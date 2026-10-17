#!/usr/bin/env python3
"""Publish one sealed Zenodo successor-version wave safely and resumably.

The default mode is a local plan. Irreversible publication requires both
``--publish`` and ``--go`` plus the exact SHA-256 of ``WAVE_MANIFEST.json``.
Existing versions are never edited or deleted. Draft and DOI receipts are
written immediately, and completed candidates are skipped on a retry.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


if not os.environ.get("VIRIDIS_CORE_ROOT"):
    raise RuntimeError("HOLD_CORE_ROOT_REQUIRED: set VIRIDIS_CORE_ROOT explicitly")
ROOT = Path(os.environ["VIRIDIS_CORE_ROOT"])
HERE = ROOT / '_ZENODO_DEPOSITS'
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import functools
import importlib
import packaging_runtime as packaging


def guarded(function):
    @functools.wraps(function)
    def checked(*args, **kwargs):
        with packaging.session(ROOT, packaging.nominated_binding(ROOT)):
            globals()['manuscript_pdf_gate'] = importlib.import_module('manuscript_pdf_gate')
            globals()['release_coherence'] = importlib.import_module('release_coherence')
            return function(*args, **kwargs)
    return checked


BASE = "https://zenodo.org/api"
TOKEN_PATH = ROOT / "secrets/Zenodo_API/Zenodo_token.md"
DOI_RE = re.compile(r"^10\.5281/zenodo\.([0-9]+)$")


class SuccessorPublisherError(RuntimeError):
    """A fail-closed error whose message never contains a credential."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def credential() -> str:
    try:
        raw = TOKEN_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise SuccessorPublisherError(f"cannot read Zenodo credential: {exc}") from exc
    candidates = re.findall(r"[A-Za-z0-9_\-]{30,}", raw.replace("\\", ""))
    if not candidates:
        raise SuccessorPublisherError("Zenodo credential failed local shape validation")
    return max(candidates, key=len)


def write_once(path: Path, value: str, *, token: str = "") -> None:
    normalized = redact(value, token).strip()
    if path.exists():
        if path.read_text(encoding="utf-8").strip() != normalized:
            raise SuccessorPublisherError(f"refusing conflicting receipt: {path}")
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(normalized + "\n", encoding="utf-8")
    os.replace(temporary, path)



def json_write_atomic(path: Path, value: object, *, token: str = "") -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        redact(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False), token) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)



def api_call(
    token: str,
    method: str,
    url: str,
    data: bytes | None = None,
    content_type: str | None = "application/json",
    *,
    allow_not_found: bool = False,
    not_found_status: list[int] | None = None,
    rdm: bool = False,
) -> dict[str, Any] | None:
    if "VIRIDIS_ZENODO_API_BASE" in os.environ:
        raise SuccessorPublisherError("VIRIDIS_ZENODO_API_BASE is forbidden")
    validated_zenodo_url(url)
    if token and token in urllib.parse.unquote(url):
        raise SuccessorPublisherError("Zenodo credential is forbidden in request URLs")
    headers = {"Content-Type": content_type} if content_type else {}
    headers["Authorization"] = "Bearer " + token
    headers["Accept"] = (
        "application/vnd.inveniordm.v1+json"
        if rdm
        else "application/json"
    )
    opener = urllib.request.build_opener(ZenodoRedirectHandler())
    raw = ""
    for attempt in range(4):
        try:
            if method.upper() != "GET":
                packaging.validate(ROOT, packaging.nominated_binding(ROOT))
            request = urllib.request.Request(url, method=method, data=data, headers=headers)
            with opener.open(request, timeout=120) as response:
                raw = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            try:
                body = redact(exc.read().decode("utf-8", errors="replace"), token)[:500]
            except Exception:
                body = ""
            finally:
                try:
                    exc.close()
                except Exception:
                    pass
            if allow_not_found and method in {"GET", "DELETE"} and exc.code in (404, 410):
                if not_found_status is not None:
                    not_found_status.append(exc.code)
                return None
            if method != "POST" and exc.code in {429, 502, 503, 504} and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            detail = f": {body}" if body.strip() else ""
            raise SuccessorPublisherError(
                f"Zenodo {method} failed with HTTP {exc.code}{detail}"
            ) from None
        except urllib.error.URLError as exc:
            if method != "POST" and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SuccessorPublisherError(
                f"Zenodo {method} connection failed ({type(exc.reason).__name__})"
            ) from None
        except Exception as exc:
            raise SuccessorPublisherError(
                f"Zenodo {method} failed ({type(exc).__name__}): " + redact(str(exc), token)
            ) from None
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise SuccessorPublisherError("Zenodo response was not valid JSON") from None
    if not isinstance(value, dict):
        raise SuccessorPublisherError("Zenodo response root was not an object")
    return value



def extract_doi(value: dict[str, Any]) -> str | None:
    metadata = value.get("metadata")
    if isinstance(metadata, dict):
        doi = metadata.get("doi")
        if isinstance(doi, str) and DOI_RE.fullmatch(doi):
            return doi
    pids = value.get("pids")
    if isinstance(pids, dict):
        doi_pid = pids.get("doi")
        if isinstance(doi_pid, dict):
            identifier = doi_pid.get("identifier")
            if isinstance(identifier, str) and DOI_RE.fullmatch(identifier):
                return identifier
    return None


def record_id(value: dict[str, Any], context: str) -> str:
    identifier = value.get("id")
    normalized = str(identifier) if isinstance(identifier, (str, int)) else ""
    if not normalized.isdigit():
        raise SuccessorPublisherError(f"{context}: response lacks a numeric record id")
    return normalized


def read_receipt(path: Path, pattern: re.Pattern[str], label: str) -> str | None:
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    if pattern.fullmatch(value) is None:
        raise SuccessorPublisherError(f"{path}: invalid {label} receipt")
    return value


@guarded
def load_and_validate_wave(wave_root: Path, expected_sha256: str) -> list[dict[str, Any]]:
    manifest_path = wave_root / "WAVE_MANIFEST.json"
    if sha256(manifest_path) != expected_sha256:
        raise SuccessorPublisherError("successor-wave manifest SHA-256 mismatch")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SuccessorPublisherError("invalid successor-wave manifest") from exc
    if manifest.get("standard") != "VRS-ZENODO-SUCCESSOR-WAVE-1":
        raise SuccessorPublisherError("unexpected successor-wave standard")
    if manifest.get("candidate_count") != 7 or manifest.get("science_changed") is not False:
        raise SuccessorPublisherError("successor wave count or science boundary mismatch")
    candidates = manifest.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 7:
        raise SuccessorPublisherError("successor wave must contain exactly seven candidates")

    validated: list[dict[str, Any]] = []
    for row in candidates:
        if not isinstance(row, dict):
            raise SuccessorPublisherError("successor-wave candidate must be an object")
        abbreviation = row.get("abbreviation")
        if not isinstance(abbreviation, str) or not re.fullmatch(r"[A-Z]{2,5}", abbreviation):
            raise SuccessorPublisherError("invalid successor-wave abbreviation")
        bundle = wave_root / abbreviation
        correction_path = wave_root / str(row.get("manifest", ""))
        if correction_path != bundle / "CORRECTION_MANIFEST.json":
            raise SuccessorPublisherError(f"{abbreviation}: correction manifest path mismatch")
        if sha256(correction_path) != row.get("manifest_sha256"):
            raise SuccessorPublisherError(f"{abbreviation}: correction manifest SHA-256 mismatch")
        try:
            correction = json.loads(correction_path.read_text(encoding="utf-8"))
            release_metadata = json.loads(
                (bundle / "zenodo_metadata.json").read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise SuccessorPublisherError(f"{abbreviation}: invalid candidate JSON") from exc
        if correction.get("abbreviation") != abbreviation:
            raise SuccessorPublisherError(f"{abbreviation}: correction abbreviation mismatch")
        if correction.get("predecessor_doi") != row.get("predecessor_doi"):
            raise SuccessorPublisherError(f"{abbreviation}: predecessor DOI mismatch")
        if correction.get("new_version") != row.get("new_version"):
            raise SuccessorPublisherError(f"{abbreviation}: successor version mismatch")
        if correction.get("science_changed") is not False:
            raise SuccessorPublisherError(f"{abbreviation}: science_changed must be false")
        candidate_hashes = correction.get("candidate_sha256")
        if not isinstance(candidate_hashes, dict) or not candidate_hashes:
            raise SuccessorPublisherError(f"{abbreviation}: missing candidate hash map")
        for name, expected in candidate_hashes.items():
            path = bundle / str(name)
            if not path.is_file() or sha256(path) != expected:
                raise SuccessorPublisherError(f"{abbreviation}: candidate hash mismatch for {name}")
        protected = correction.get("protected_unchanged_files")
        original_hashes = correction.get("original_sha256")
        if not isinstance(protected, list) or not isinstance(original_hashes, dict):
            raise SuccessorPublisherError(f"{abbreviation}: invalid protected-artifact declaration")
        for name in protected:
            if candidate_hashes.get(name) != original_hashes.get(name):
                raise SuccessorPublisherError(f"{abbreviation}: protected artifact changed: {name}")
        metadata = release_metadata.get("metadata")
        if not isinstance(metadata, dict):
            raise SuccessorPublisherError(f"{abbreviation}: missing metadata object")
        if metadata.get("version") != row.get("new_version"):
            raise SuccessorPublisherError(f"{abbreviation}: metadata version mismatch")
        if metadata.get("license") != "cc-by-4.0" or metadata.get("access_right") != "open":
            raise SuccessorPublisherError(f"{abbreviation}: open CC BY 4.0 metadata required")
        if sha256(bundle / "zenodo_metadata.json") != correction.get("zenodo_metadata_sha256"):
            raise SuccessorPublisherError(f"{abbreviation}: metadata SHA-256 mismatch")
        upload_names = sorted(
            name for name in candidate_hashes if name != "zenodo_metadata.json"
        ) + ["CORRECTION_MANIFEST.json"]
        try:
            preflight = manuscript_pdf_gate.require_local(bundle, [bundle / name for name in upload_names])
        except manuscript_pdf_gate.ManuscriptPDFHold as exc:
            raise SuccessorPublisherError("standalone manuscript PDF gate HOLD: " + str(exc)) from exc
        expected_upload_hashes = {name: candidate_hashes[name] for name in upload_names if name != "CORRECTION_MANIFEST.json"}
        expected_upload_hashes["CORRECTION_MANIFEST.json"] = row["manifest_sha256"]
        if {item["filename"]: item["sha256"] for item in preflight["upload_files"]} != expected_upload_hashes:
            raise SuccessorPublisherError("approved upload bytes differ from the sealed successor-wave manifest")
        validated.append(
            {
                "abbreviation": abbreviation,
                "bundle": bundle,
                "predecessor_doi": row["predecessor_doi"],
                "new_version": row["new_version"],
                "metadata": release_metadata,
                "upload_names": tuple(sorted(upload_names)),
                "approved_preflight_json": json.dumps(preflight, sort_keys=True, separators=(",", ":")),
            }
        )
    return validated


@guarded
def ensure_draft(candidate: dict[str, Any], token: str) -> str:
    bundle = candidate["bundle"]
    draft_receipt = bundle / "ZENODO_DRAFT_ID.txt"
    existing = read_receipt(draft_receipt, re.compile(r"\d+"), "draft id")
    if existing:
        return existing
    predecessor = DOI_RE.fullmatch(candidate["predecessor_doi"])
    assert predecessor is not None
    parent_id = predecessor.group(1)
    adopted = api_call(
        token,
        "GET",
        f"{BASE}/records/{parent_id}/draft",
        allow_not_found=True,
    )
    if adopted is None:
        adopted = api_call(token, "POST", f"{BASE}/records/{parent_id}/versions", b"{}")
    assert adopted is not None
    identifier = record_id(adopted, candidate["abbreviation"])
    write_once(draft_receipt, identifier, token=token)
    return identifier



def approved_preflight(candidate: dict[str, Any]) -> dict:
    """Decode the frozen planning result; never approve replacement local bytes."""
    serialized = candidate.get("approved_preflight_json")
    if not isinstance(serialized, str):
        raise SuccessorPublisherError("immutable planning preflight required")
    approved = json.loads(serialized)
    rows = approved.get("upload_files") if isinstance(approved, dict) else None
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise SuccessorPublisherError("complete approved upload byte inventory required")
    names = [row.get("filename") for row in rows]
    if (any(not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."} for name in names)
            or len(names) != len(set(names)) or set(names) != set(candidate["upload_names"])):
        raise SuccessorPublisherError("unique exact approved top-level upload inventory required")
    return approved


def snapshot_uploads(bundle: Path, approved: dict) -> dict[str, bytes]:
    """Retain exactly the bytes approved in the wave's planning preflight."""
    payloads = {}
    for row in approved["upload_files"]:
        name = row["filename"]
        raw = manuscript_pdf_gate._read(bundle / name)
        actual = {"sha256": hashlib.sha256(raw).hexdigest(), "md5": hashlib.md5(raw).hexdigest(), "bytes": len(raw)}
        if any(row.get(key) != value for key, value in actual.items()):
            raise SuccessorPublisherError("approved upload changed before snapshot: " + name)
        payloads[name] = raw
    return payloads


def check_draft_files(deposition: dict, approved: dict) -> None:
    files = deposition.get("files")
    if not isinstance(files, list) or any(not isinstance(row, dict) for row in files):
        raise SuccessorPublisherError("draft upload inventory required")
    names = [row.get("filename") for row in files]
    expected = {row["filename"]: row for row in approved["upload_files"]}
    if any(not isinstance(name, str) for name in names) or len(names) != len(set(names)):
        raise SuccessorPublisherError("draft upload names are invalid or duplicated")
    if set(names) != set(expected):
        raise SuccessorPublisherError("draft file set differs from exact approved uploads")
    for row in files:
        wanted = expected[row["filename"]]
        checksum = str(row.get("checksum", "")).removeprefix("md5:")
        if checksum != wanted["md5"] or row.get("filesize", row.get("size")) != wanted["bytes"]:
            raise SuccessorPublisherError("draft upload checksum or size differs: " + row["filename"])



@guarded
def verify_manuscript_readback(candidate: dict[str, Any], token: str, doi: str, preflight=None) -> None:
    bundle = candidate["bundle"]
    if preflight is None:
        preflight = approved_preflight(candidate)
    if "expected_copyright" not in candidate:
        inherit_predecessor_copyright(candidate, token)
    record_id = DOI_RE.fullmatch(doi).group(1)
    record = api_call(token, "GET", f"{BASE}/records/{record_id}")
    if not isinstance(record, dict) or str(record.get("id")) != record_id or extract_doi(record) != doi:
        raise SuccessorPublisherError("standalone manuscript readback record identity differs")
    if candidate["expected_copyright"] is not None:
        rdm_record = api_call(token, "GET", f"{BASE}/records/{record_id}", rdm=True)
        if not isinstance(rdm_record, dict) or rdm_record.get("metadata", {}).get("copyright") != candidate["expected_copyright"]:
            raise SuccessorPublisherError("published DOI retained; predecessor copyright readback differs")
    try:
        receipt = manuscript_pdf_gate.require_public(record, preflight)
    except manuscript_pdf_gate.ManuscriptPDFHold as exc:
        raise SuccessorPublisherError("published DOI retained; standalone manuscript PDF readback HOLD: " + str(exc)) from exc
    receipt_path = ROOT / "reports/publication-manuscript-pdf-readback" / record_id / "MANUSCRIPT_PDF_READBACK.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_once(receipt_path, json.dumps(receipt, sort_keys=True, indent=2), token=token)



@guarded
def publish_candidate(candidate: dict[str, Any], token: str) -> dict[str, Any]:
    if "VIRIDIS_ZENODO_API_BASE" in os.environ:
        raise SuccessorPublisherError("VIRIDIS_ZENODO_API_BASE is forbidden")
    bundle: Path = candidate["bundle"]
    read_receipt(bundle / "PUBLISHED_DOI.txt", DOI_RE, "DOI")
    approved = approved_preflight(candidate)
    # This receipt fixes the original approval across retries and partial DOI
    # outcomes. A later invocation cannot silently approve replacement bytes.
    write_once(bundle / "APPROVED_UPLOAD_PREFLIGHT.json", json.dumps(approved, sort_keys=True, indent=2), token=token)
    doi_receipt = bundle / "PUBLISHED_DOI.txt"
    existing_doi = read_receipt(doi_receipt, DOI_RE, "DOI")
    if existing_doi:
        verify_manuscript_readback(candidate, token, existing_doi, approved)
        return {"abbreviation": candidate["abbreviation"], "doi": existing_doi, "reused": True}

    try:
        current = manuscript_pdf_gate.require_local(bundle, [bundle / name for name in candidate["upload_names"]])
        if current != approved:
            raise SuccessorPublisherError("approved manuscript/upload inventory changed before network activity")
    except manuscript_pdf_gate.ManuscriptPDFHold as exc:
        raise SuccessorPublisherError("standalone manuscript PDF gate HOLD: " + str(exc)) from exc
    payloads = snapshot_uploads(bundle, approved)
    inherit_predecessor_copyright(candidate, token)
    draft = ensure_draft(candidate, token)
    publish_requested = False
    doi_observed = False
    try:
        public_record = api_call(
            token,
            "GET",
            f"{BASE}/records/{draft}",
            allow_not_found=True,
        )
        if public_record is not None:
            doi_observed = True
            published_doi = extract_doi(public_record)
            if published_doi is None:
                raise SuccessorPublisherError("existing published record lacks a production DOI; preserve it")
            if published_doi:
                doi_observed = True
                write_once(doi_receipt, published_doi, token=token)
                verify_manuscript_readback(candidate, token, published_doi, approved)
                return {
                    "abbreviation": candidate["abbreviation"],
                    "doi": published_doi,
                    "recovered": True,
                }

        deposition = api_call(token, "GET", f"{BASE}/deposit/depositions/{draft}")
        assert deposition is not None
        already_published = extract_doi(deposition)
        if deposition.get("submitted") is True:
            doi_observed = True
            if already_published is None:
                raise SuccessorPublisherError("submitted deposition lacks a production DOI; preserve it")
            doi_observed = True
            write_once(doi_receipt, already_published, token=token)
            verify_manuscript_readback(candidate, token, already_published, approved)
            return {
                "abbreviation": candidate["abbreviation"],
                "doi": already_published,
                "recovered": True,
            }
        files = deposition.get("files")
        if not isinstance(files, list):
            raise SuccessorPublisherError(f"{candidate['abbreviation']}: draft file list missing")
        for item in files:
            if not isinstance(item, dict):
                raise SuccessorPublisherError(f"{candidate['abbreviation']}: invalid draft file entry")
            file_id = item.get("id")
            if not isinstance(file_id, str) or not file_id:
                raise SuccessorPublisherError(f"{candidate['abbreviation']}: inherited file lacks id")
            api_call(token, "DELETE", f"{BASE}/deposit/depositions/{draft}/files/{file_id}")

        links = deposition.get("links")
        bucket = links.get("bucket") if isinstance(links, dict) else None
        if not isinstance(bucket, str) or not bucket:
            raise SuccessorPublisherError(f"{candidate['abbreviation']}: draft bucket missing")
        for name, raw in payloads.items():
            uploaded = api_call(
                token,
                "PUT",
                f"{bucket}/{urllib.parse.quote(name, safe='')}",
                raw,
                "application/octet-stream",
            )
            if not isinstance(uploaded, dict) or str(uploaded.get("checksum", "")).removeprefix("md5:") != hashlib.md5(raw).hexdigest():
                raise SuccessorPublisherError("PUT response checksum differs from uploaded bytes")

        snapshot_native_successor(candidate, token, draft)
        metadata_payload = copy.deepcopy(candidate["metadata"])
        if candidate["expected_copyright"] is not None:
            metadata_payload["metadata"]["copyright"] = candidate["expected_copyright"]
        api_call(
            token,
            "PUT",
            f"{BASE}/deposit/depositions/{draft}",
            json.dumps(metadata_payload).encode("utf-8"),
        )
        preserve_draft_copyright(candidate, token, draft)
        verify_native_successor(candidate, token, draft)
        verified = api_call(token, "GET", f"{BASE}/deposit/depositions/{draft}")
        assert verified is not None
        check_draft_files(verified, approved)
        try:
            current = manuscript_pdf_gate.require_local(bundle, [bundle / name for name in candidate["upload_names"]])
            if current != approved:
                raise SuccessorPublisherError("approved manuscript/upload inventory changed before publication")
        except manuscript_pdf_gate.ManuscriptPDFHold as exc:
            raise SuccessorPublisherError("standalone manuscript PDF gate HOLD: " + str(exc)) from exc
        publish_requested = True
        published = api_call(
            token,
            "POST",
            f"{BASE}/deposit/depositions/{draft}/actions/publish",
        )
        assert published is not None
        doi = extract_doi(published)
        if doi is None:
            raise SuccessorPublisherError(f"{candidate['abbreviation']}: publish response lacks DOI")
        write_once(doi_receipt, doi, token=token)
        verify_manuscript_readback(candidate, token, doi, approved)
        return {"abbreviation": candidate["abbreviation"], "doi": doi, "record_id": draft}
    except Exception:
        if not publish_requested and not doi_observed:
            try:
                api_call(token, "DELETE", f"{BASE}/records/{draft}/draft", rdm=True, allow_not_found=True)
            except Exception:
                raise SuccessorPublisherError("prepublication HOLD; draft cleanup requires exact readback") from None
        raise



@guarded
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wave-root", type=Path, required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--go", action="store_true")
    args = parser.parse_args()
    token = ""
    try:
        wave_root = args.wave_root.resolve()
        candidates = load_and_validate_wave(wave_root, args.expected_manifest_sha256)
        plan = {
            "state": "LOCAL_PLAN",
            "wave_manifest_sha256": args.expected_manifest_sha256,
            "candidate_count": len(candidates),
            "candidates": [
                {
                    "abbreviation": row["abbreviation"],
                    "predecessor_doi": row["predecessor_doi"],
                    "new_version": row["new_version"],
                    "file_count": len(row["upload_names"]),
                    "draft_id": read_receipt(
                        row["bundle"] / "ZENODO_DRAFT_ID.txt",
                        re.compile(r"\d+"),
                        "draft id",
                    ),
                    "published_doi": read_receipt(
                        row["bundle"] / "PUBLISHED_DOI.txt", DOI_RE, "DOI"
                    ),
                }
                for row in candidates
            ],
            "external_mutation": False,
        }
        if not args.publish and not args.go:
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 0
        if not (args.publish and args.go):
            raise SuccessorPublisherError(
                "irreversible successor publication requires both --publish and --go"
            )
        token = credential()
        results: list[dict[str, Any]] = []
        for row in candidates:
            result = publish_candidate(row, token)
            results.append(result)
            json_write_atomic(
                wave_root / "SUCCESSOR_PUBLICATION_RECEIPT.json",
                {
                    "schema_version": 1,
                    "standard": "VRS-ZENODO-SUCCESSOR-PUBLICATION-1",
                    "state": "ZENODO_SUCCESSOR_WAVE_IN_PROGRESS",
                    "wave_manifest_sha256": args.expected_manifest_sha256,
                    "results": results,
                    "external_mutation": True,
                },
                token=token,
            )
        receipt = {
            "schema_version": 1,
            "standard": "VRS-ZENODO-SUCCESSOR-PUBLICATION-1",
            "state": "ZENODO_SUCCESSOR_WAVE_PUBLISHED",
            "wave_manifest_sha256": args.expected_manifest_sha256,
            "results": results,
            "external_mutation": True,
        }
        json_write_atomic(wave_root / "SUCCESSOR_PUBLICATION_RECEIPT.json", receipt, token=token)
        print(redact(json.dumps(receipt, indent=2, sort_keys=True), token))
        return 0
    except Exception as exc:
        print(json.dumps({"state": "HOLD", "error_type": type(exc).__name__,
                          "error": redact(str(exc), token)}, indent=2), file=sys.stderr)
        return 2



def redact(value: str, token: str) -> str:
    """Sanitize credentials before exception output or receipt serialization."""
    return value.replace(token, "***") if token else value


def validated_zenodo_url(url: str) -> str:
    """Keep credentials on the configured approved HTTPS Zenodo origin."""
    try:
        parsed = urllib.parse.urlsplit(url)
        configured = urllib.parse.urlsplit(BASE)
        query_keys = [key for key, _ in urllib.parse.parse_qsl(parsed.query)]
        if (
            configured.scheme != "https"
            or configured.hostname not in {"zenodo.org", "sandbox.zenodo.org"}
            or configured.port not in (None, 443)
            or configured.username or configured.password
            or configured.path != "/api" or configured.query or configured.fragment
            or any(character.isspace() or ord(character) < 32 for character in BASE)
            or parsed.scheme != "https" or parsed.hostname != configured.hostname
            or parsed.port not in (None, 443)
            or parsed.username or parsed.password
            or not parsed.path.startswith("/api/") or parsed.fragment
            or any(character.isspace() or ord(character) < 32 for character in url)
            or any(urllib.parse.unquote(key).lower() == "access_token" for key in query_keys)
        ):
            raise ValueError
    except (TypeError, ValueError):
        raise SuccessorPublisherError(
            "Zenodo request destination must be the configured HTTPS API without URL credentials"
        ) from None
    return url


class ZenodoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validated_zenodo_url(newurl)
        authorization = req.get_header("Authorization", "")
        token = authorization.removeprefix("Bearer ")
        if token and token in urllib.parse.unquote(newurl):
            raise SuccessorPublisherError("Zenodo credential is forbidden in redirect URLs")
        source = urllib.parse.urlsplit(req.full_url)
        target = urllib.parse.urlsplit(newurl)
        if source.hostname != target.hostname:
            raise SuccessorPublisherError("Zenodo redirect crosses the credential origin")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@guarded
def inherit_predecessor_copyright(candidate: dict[str, Any], token: str) -> str | None:
    predecessor = DOI_RE.fullmatch(candidate["predecessor_doi"])
    if predecessor is None:
        raise SuccessorPublisherError("invalid predecessor DOI")
    record = api_call(token, "GET", f"{BASE}/records/{predecessor.group(1)}", rdm=True)
    metadata = record.get("metadata") if isinstance(record, dict) else None
    if not isinstance(metadata, dict):
        raise SuccessorPublisherError("predecessor metadata unavailable for copyright inheritance")
    copyright_value = metadata.get("copyright")
    if copyright_value is not None and not isinstance(copyright_value, str):
        raise SuccessorPublisherError("predecessor copyright has an invalid type")
    candidate["expected_copyright"] = copyright_value
    candidate["predecessor_native"] = copy.deepcopy(record)
    return copyright_value


@guarded
def native_projection(value):
    """Execute only the unchanged, hash-bound reviewed native projection source."""
    installed = ROOT / "RESEARCH_PIPELINE_v2/verification_coverage_gates/own_record_comparison.py"
    # Repository test/review execution has the same immutable source next to
    # this gate directory. Installed execution has no such repository fallback.
    repository = next((parent / "own_record_comparison.py" for parent in Path(__file__).absolute().parents
                       if (parent / "own_record_comparison.py").is_file()), None)
    path = installed if installed.exists() or installed.is_symlink() else repository
    if path is None or any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise SuccessorPublisherError("reviewed native protected projection source required")
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    if (hashlib.sha256(raw).hexdigest() != "55e9e4a070cd6d3ac0f0ceb5398d163b1f64c2463b41810bf82b63be537003bf"
            or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
        raise SuccessorPublisherError("reviewed native protected projection source differs")
    namespace = {"__file__": str(path), "__name__": "_bound_successor_native_projection"}
    exec(compile(raw, str(path), "exec"), namespace)
    result = namespace["prior_protected_projection"](value, representation="NATIVE")
    if path.read_bytes() != raw:
        raise SuccessorPublisherError("reviewed native protected projection source changed")
    return result


@guarded
def snapshot_native_successor(candidate, token, draft):
    """Retain the complete native draft before the lossy legacy round trip."""
    before = api_call(token, "GET", f"{BASE}/records/{draft}/draft", rdm=True)
    if not isinstance(before, dict) or str(before.get("id")) != str(draft):
        raise SuccessorPublisherError("native successor draft identity differs")
    # Record identity, phase, generated links/PIDs and the explicitly replaced
    # files belong to the new version. Every other native field is inherited.
    operation_fields = {"id", "created", "expires_at", "status", "is_draft", "is_published", "versions", "pids", "links", "files"}
    planned_fields = {"version", "publication_date", "related_identifiers"}
    def inherited(value):
        projected = native_projection(value)
        for key in operation_fields:
            projected.pop(key, None)
        metadata = projected.get("metadata")
        if not isinstance(metadata, dict):
            raise SuccessorPublisherError("native successor metadata required")
        for key in planned_fields:
            metadata.pop(key, None)
        return projected
    if inherited(before) != inherited(candidate["predecessor_native"]):
        raise SuccessorPublisherError("native successor creation changed protected predecessor content")
    candidate["native_before_metadata"] = copy.deepcopy(before)
    return before


@guarded
def verify_native_successor(candidate, token, draft):
    """Require the full native projection plus only the approved metadata edits."""
    expected = copy.deepcopy(candidate["native_before_metadata"])
    planned = candidate["metadata"]["metadata"]
    for key in ("version", "publication_date", "related_identifiers"):
        if key in planned:
            expected["metadata"][key] = copy.deepcopy(planned[key])
    if candidate["expected_copyright"] is not None:
        expected["metadata"]["copyright"] = candidate["expected_copyright"]
    actual = api_call(token, "GET", f"{BASE}/records/{draft}/draft", rdm=True)
    matched = native_projection(expected) == native_projection(actual)
    receipt = {"state": "NATIVE_SUCCESSOR_READBACK_VERIFIED" if matched else "HOLD_NATIVE_SUCCESSOR_PROTECTED_DIFF",
               "draft_id": str(draft), "predecessor": candidate["predecessor_native"],
               "before_legacy_put": candidate["native_before_metadata"], "planned_after": expected, "after": actual}
    json_write_atomic(candidate.get("receipt_root", candidate["bundle"]) / "NATIVE_SUCCESSOR_READBACK.json", receipt, token=token)
    if not matched:
        raise SuccessorPublisherError("native successor protected content differs before publication")
    return actual



@guarded
def preserve_draft_copyright(candidate: dict[str, Any], token: str, draft: str) -> None:
    """Use RDM when the legacy metadata round trip drops predecessor rights."""
    expected = candidate["expected_copyright"]
    if expected is None:
        return
    url = f"{BASE}/records/{draft}/draft"
    current = api_call(token, "GET", url, rdm=True)
    metadata = current.get("metadata") if isinstance(current, dict) else None
    if not isinstance(metadata, dict):
        raise SuccessorPublisherError("RDM draft metadata missing for copyright preservation")
    if metadata.get("copyright") == expected:
        return
    corrected = copy.deepcopy(current)
    corrected["metadata"]["copyright"] = expected
    receipt_path = candidate.get("receipt_root", candidate["bundle"]) / "COPYRIGHT_INHERITANCE_RECEIPT.json"
    receipt = {"state": "BEFORE_COPYRIGHT_ONLY_RDM_UPDATE", "draft_id": draft,
               "predecessor_doi": candidate["predecessor_doi"],
               "before": current, "planned_copyright": expected}
    json_write_atomic(receipt_path, receipt, token=token)
    try:
        api_call(token, "PUT", url, json.dumps(corrected).encode("utf-8"), rdm=True)
        readback = api_call(token, "GET", url, rdm=True)
        # Reconsume the same exact reviewed projection without ambient imports.
        matched = native_projection(corrected) == native_projection(readback)
        receipt.update(state="COPYRIGHT_INHERITED" if matched else "HOLD_UNPLANNED_RDM_DIFF", after=readback)
        json_write_atomic(receipt_path, receipt, token=token)
        if not matched:
            raise SuccessorPublisherError("copyright-only RDM draft readback differs; publication held")
    except Exception:
        try:
            api_call(token, "DELETE", url, rdm=True, allow_not_found=True)
        except Exception:
            raise SuccessorPublisherError("copyright repair held and draft cleanup requires readback") from None
        raise




if __name__ == "__main__":
    try:
        exit_code = main()
    except Exception as exc:
        # Session admission wraps main; its failures must also remain private.
        print(json.dumps({"state": "HOLD", "error_type": type(exc).__name__,
                          "error": "guarded packaging entry point refused execution"}), file=sys.stderr)
        exit_code = 2
    raise SystemExit(exit_code)
