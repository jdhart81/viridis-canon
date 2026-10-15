#!/usr/bin/env python3
"""Idempotent Zenodo publisher for one guarded dated Viridis bundle wave.

Default mode is a local plan and performs no network call. Irreversible mode
requires both ``--publish`` and ``--go`` and is intended to run only as the
publisher argv supplied to ``weekend_canon_lockstep.py`` after Justin approves
that exact dry-run surface.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import urllib.error
import urllib.request
import urllib.parse


HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("VIRIDIS_CORE_ROOT", str(HERE.parent)))
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import release_coherence
import manuscript_pdf_gate
import rehearsal

BASE = "https://zenodo.org/api"
TOKEN_PATH = ROOT / "secrets/Zenodo_API/Zenodo_token.md"
DOI_RE = re.compile(r"^10\.5281/zenodo\.[0-9]+$")


class PublisherError(RuntimeError):
    """A safe publisher error that never includes credentials."""


def token() -> str:
    try:
        raw = TOKEN_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublisherError(f"cannot read Zenodo credential: {exc}") from exc
    candidates = re.findall(r"[A-Za-z0-9_\-]{30,}", raw.replace("\\", ""))
    if not candidates:
        raise PublisherError("Zenodo credential failed local shape validation")
    return max(candidates, key=len)


def bundles(date: str, base: Path = HERE) -> list[Path]:
    try:
        normalized = __import__("datetime").date.fromisoformat(date).isoformat()
    except ValueError as exc:
        raise PublisherError("--date must use YYYY-MM-DD") from exc
    rows = sorted(path for path in base.glob(f"{normalized}_*_standalone") if path.is_dir())
    if not rows:
        raise PublisherError(f"no {normalized}_*_standalone bundles found")
    return rows


def read_doi(path: Path) -> str | None:
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    if DOI_RE.fullmatch(value) is None:
        raise PublisherError(f"{path}: invalid DOI receipt")
    return value


def upload_files(bundle: Path) -> list[Path]:
    excluded = {
        "BUNDLE_MANIFEST.json",
        "LEDGER_BINDING.json",
        "RELEASE_BINDING.json",
        "zenodo_metadata.json",
        "PUBLISHED_DOI.txt",
        "ZENODO_DRAFT_ID.txt",
    }
    files = sorted(
        path for path in bundle.iterdir()
        if path.is_file() and path.name not in excluded and not path.name.startswith(".")
    )
    if not files:
        raise PublisherError(f"{bundle}: no upload files")
    return files



def verification_coverage_report(artifact, context, *, enforce_new_artifacts=False):
    # Default is observation; the separate enforcing flag blocks new artifacts.
    try:
        gates = ROOT / "RESEARCH_PIPELINE_v2/verification_coverage_gates"
        if str(gates) not in sys.path:
            sys.path.insert(0, str(gates))
        from production_hooks import log_publication
        return log_publication(ROOT, artifact, context, enforce_new_artifacts=enforce_new_artifacts)
    except Exception as exc:
        if enforce_new_artifacts:
            raise PublisherError("new-artifact publication gate HOLD: " + str(exc)) from exc
        print(json.dumps({"verification_coverage": {"mode": "REPORT_ONLY", "status": "HOLD",
            "label": "UNCERTIFIED", "enforcement": False,
            "reasons": [type(exc).__name__]}}), file=sys.stderr)


def metadata_payload(bundle: Path, *, enforce_new_artifacts=False) -> dict[str, Any]:
    path = bundle / "zenodo_metadata.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = payload["metadata"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise PublisherError(f"{bundle}: invalid zenodo_metadata.json") from exc
    if not isinstance(payload, dict) or not isinstance(metadata, dict):
        raise PublisherError(f"{bundle}: metadata payload must be an object")
    try:
        release_coherence.validate_bundle(bundle)
    except release_coherence.CoherenceError as exc:
        raise PublisherError(str(exc)) from exc
    verification_coverage_report(bundle, "publisher_metadata_after_coherence", enforce_new_artifacts=enforce_new_artifacts)
    try:
        manuscript_pdf_gate.require_local(bundle, upload_files(bundle))
    except manuscript_pdf_gate.ManuscriptPDFHold as exc:
        raise PublisherError("standalone manuscript PDF gate HOLD: " + str(exc)) from exc
    return payload


def validated_zenodo_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    configured = urllib.parse.urlsplit(BASE)
    if (configured.scheme != "https" or configured.hostname not in {"zenodo.org", "sandbox.zenodo.org"}
        or configured.path != "/api" or configured.query or configured.fragment
        or configured.username or configured.password or configured.port not in (None, 443)
        or parsed.scheme != "https" or parsed.hostname != configured.hostname
        or parsed.port not in (None, 443) or parsed.username or parsed.password
        or not parsed.path.startswith("/api/") or parsed.fragment
        or any(character.isspace() or ord(character) < 32 for character in url)
        or any(urllib.parse.unquote(key).lower() == "access_token" for key, _ in urllib.parse.parse_qsl(parsed.query))):
        raise PublisherError("Zenodo request destination must be the configured HTTPS API without URL credentials")
    return url


class ZenodoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validated_zenodo_url(newurl)
        credential = req.get_header("Authorization", "").removeprefix("Bearer ")
        if credential and credential in urllib.parse.unquote(newurl):
            raise PublisherError("Zenodo credential is forbidden in redirect URLs") from None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def api_call(
    credential: str,
    method: str,
    url: str,
    data: bytes | None = None,
    content_type: str | None = "application/json",
    *,
    allow_array: bool = False,
    allow_not_found: bool = False,
    accept_native: bool = False,
) -> Any:
    rehearsal.require_production()
    validated_zenodo_url(url)
    if credential and credential in urllib.parse.unquote(url):
        raise PublisherError("Zenodo credential is forbidden in request URLs") from None
    headers = {"Content-Type": content_type} if content_type else {}
    headers["Authorization"] = "Bearer " + credential
    if accept_native:
        headers["Accept"] = "application/vnd.inveniordm.v1+json"
    opener = urllib.request.build_opener(ZenodoRedirectHandler())
    raw = ""
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, method=method, data=data, headers=headers)
            with opener.open(request, timeout=rehearsal.timeout(90)) as response:
                raw = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            # Closing also prevents deferred HTTPError resource diagnostics
            # from reproducing a credential-bearing response URL/message.
            try:
                exc.close()
            except Exception:
                pass
            if allow_not_found and method == "GET" and exc.code in (404, 410):
                return None
            if method in {"GET", "PUT"} and exc.code in {429, 502, 503, 504} and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise PublisherError(
                f"Zenodo {method} failed with HTTP {exc.code}"
            ) from None
        except urllib.error.URLError as exc:
            if method in {"GET", "PUT"} and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise PublisherError(f"Zenodo {method} connection failed ({type(exc.reason).__name__})") from None
        except Exception as exc:
            detail = str(exc).replace(credential, "***") if credential else str(exc)
            raise PublisherError(f"Zenodo {method} failed ({type(exc).__name__}): {detail}") from None
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        raise PublisherError("Zenodo response was not valid JSON") from None
    if not isinstance(value, dict) and not (allow_array and isinstance(value, list)):
        raise PublisherError("Zenodo response root has an unexpected type")
    return value


def draft_id(bundle: Path) -> int | None:
    path = bundle / "ZENODO_DRAFT_ID.txt"
    if not path.is_file():
        return None
    value = path.read_text(encoding="utf-8").strip()
    if not value.isdigit():
        raise PublisherError(f"{path}: invalid draft id")
    return int(value)


def write_once(path: Path, value: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8").strip() != value.strip():
            raise PublisherError(f"refusing to overwrite conflicting receipt: {path}")
        return
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(value.strip() + "\n", encoding="utf-8")
    os.replace(temp, path)


def ensure_draft(bundle: Path, credential: str) -> dict[str, Any]:
    existing = draft_id(bundle)
    if existing is not None:
        return api_call(credential, "GET", f"{BASE}/deposit/depositions/{existing}")
    created = api_call(credential, "POST", f"{BASE}/deposit/depositions", b"{}")
    identifier = created.get("id")
    if not isinstance(identifier, int):
        raise PublisherError("Zenodo create response lacks integer deposition id")
    write_once(bundle / "ZENODO_DRAFT_ID.txt", str(identifier))
    return created


def verify_manuscript_readback(bundle: Path, credential: str, doi: str, preflight=None) -> None:
    if preflight is None:
        preflight = manuscript_pdf_gate.require_local(bundle, upload_files(bundle))
    record_id = doi.rsplit(".", 1)[1]
    record = api_call(credential, "GET", f"{BASE}/records/{record_id}")
    if str(record.get("id")) != record_id or record.get("doi") != doi:
        raise PublisherError("standalone manuscript readback record identity differs")
    try:
        receipt = manuscript_pdf_gate.require_public(record, preflight)
    except manuscript_pdf_gate.ManuscriptPDFHold as exc:
        raise PublisherError("published DOI retained; standalone manuscript PDF readback HOLD: " + str(exc)) from exc
    receipt_path = ROOT / "reports/publication-manuscript-pdf-readback" / record_id / "MANUSCRIPT_PDF_READBACK.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    write_once(receipt_path, json.dumps(receipt, sort_keys=True, indent=2))


def snapshot_uploads(bundle: Path, preflight: dict) -> dict[str, bytes]:
    """Hash stable bytes and retain those exact in-memory bytes for upload."""
    approved = preflight.get("upload_files")
    if not isinstance(approved, list) or not approved:
        raise PublisherError("complete approved upload byte inventory required")
    payloads = {}
    for row in approved:
        name = row.get("filename")
        if not isinstance(name, str) or Path(name).name != name or name in {"", ".", ".."} or name in payloads:
            raise PublisherError("unique approved top-level upload name required")
        raw = manuscript_pdf_gate._read(bundle / name)
        actual = {"sha256": hashlib.sha256(raw).hexdigest(), "md5": hashlib.md5(raw).hexdigest(), "bytes": len(raw)}
        if any(row.get(key) != value for key, value in actual.items()):
            raise PublisherError("approved upload changed before snapshot: " + name)
        payloads[name] = raw
    return payloads


def check_draft_files(credential: str, identifier: int, approved: dict, *, complete: bool) -> None:
    remote = api_call(credential, "GET", f"{BASE}/deposit/depositions/{identifier}/files", allow_array=True)
    if not isinstance(remote, list) or any(not isinstance(row, dict) for row in remote):
        raise PublisherError("draft upload inventory required")
    names = [row.get("filename") for row in remote]
    expected = {row["filename"]: row for row in approved["upload_files"]}
    if any(not isinstance(name, str) for name in names) or len(names) != len(set(names)):
        raise PublisherError("draft upload names are invalid or duplicated")
    if set(names) - set(expected):
        raise PublisherError("draft contains files outside the approved upload inventory")
    if complete:
        if set(names) != set(expected):
            raise PublisherError("draft file set differs from exact approved uploads")
        for row in remote:
            wanted = expected[row["filename"]]
            checksum = str(row.get("checksum", "")).removeprefix("md5:")
            if checksum != wanted["md5"] or row.get("filesize", row.get("size")) != wanted["bytes"]:
                raise PublisherError("draft upload checksum or size differs: " + row["filename"])


def is_published(deposition: dict) -> bool:
    # A draft may already carry its reserved DOI; that alone is not publication.
    return deposition.get("submitted") is True or deposition.get("state") == "done"


def publish_bundle(bundle: Path, credential: str, *, enforce_new_artifacts=False) -> str:
    rehearsal.require_production()
    prior = read_doi(bundle / "PUBLISHED_DOI.txt")
    if prior:
        if enforce_new_artifacts:
            verify_manuscript_readback(bundle, credential, prior)
        return prior
    if not enforce_new_artifacts:
        raise PublisherError("new-artifact publication requires --enforce-new-artifacts")
    release_metadata = metadata_payload(bundle, enforce_new_artifacts=True)
    approved = manuscript_pdf_gate.require_local(bundle, upload_files(bundle))
    payloads = snapshot_uploads(bundle, approved)
    deposition = ensure_draft(bundle, credential)
    identifier = deposition.get("id")
    if not isinstance(identifier, int):
        raise PublisherError(f"{bundle}: draft response lacks id")
    metadata = deposition.get("metadata")
    if is_published(deposition) and isinstance(metadata, dict):
        existing_doi = metadata.get("doi")
        if isinstance(existing_doi, str) and DOI_RE.fullmatch(existing_doi):
            write_once(bundle / "PUBLISHED_DOI.txt", existing_doi)
            verify_manuscript_readback(bundle, credential, existing_doi, approved)
            return existing_doi
    links = deposition.get("links")
    bucket = links.get("bucket") if isinstance(links, dict) else None
    if not isinstance(bucket, str) or not bucket:
        raise PublisherError(f"{bundle}: draft response lacks bucket")
    check_draft_files(credential, identifier, approved, complete=False)
    for name, raw in payloads.items():
        try:
            uploaded = api_call(
                credential,
                "PUT",
                f"{bucket.rstrip('/')}/{urllib.parse.quote(name, safe='')}",
                raw,
                "application/octet-stream",
            )
            if str(uploaded.get("checksum", "")).removeprefix("md5:") != hashlib.md5(raw).hexdigest():
                raise PublisherError("PUT response checksum differs from uploaded bytes")
        except PublisherError as exc:
            raise PublisherError(
                f"{bundle.name}: upload {name} failed: {exc}"
            ) from exc
    try:
        api_call(
            credential,
            "PUT",
            f"{BASE}/deposit/depositions/{identifier}",
            json.dumps(release_metadata).encode("utf-8"),
        )
    except PublisherError as exc:
        raise PublisherError(f"{bundle.name}: metadata update failed: {exc}") from exc
    verification_coverage_report(bundle, "publisher_before_publish", enforce_new_artifacts=True)
    try:
        current = manuscript_pdf_gate.require_local(bundle, upload_files(bundle))
        if current != approved:
            raise PublisherError("approved manuscript/upload inventory changed before publication")
    except manuscript_pdf_gate.ManuscriptPDFHold as exc:
        raise PublisherError("standalone manuscript PDF gate HOLD: " + str(exc)) from exc
    check_draft_files(credential, identifier, approved, complete=True)
    published = api_call(
        credential,
        "POST",
        rehearsal.publish_action_url(identifier),
    )
    published_metadata = published.get("metadata")
    doi = published_metadata.get("doi") if isinstance(published_metadata, dict) else None
    if not isinstance(doi, str) or DOI_RE.fullmatch(doi) is None:
        raise PublisherError(f"{bundle}: publish response lacks valid DOI")
    write_once(bundle / "PUBLISHED_DOI.txt", doi)
    verify_manuscript_readback(bundle, credential, doi, approved)
    return doi


@rehearsal.time_bounded
def rehearse_bundle(bundle: Path, credential: str, *, output=None):
    """Run the approved upload/metadata path on a fresh draft, then discard it."""
    rehearsal.require_production()
    # Reject a foreign DOI before even creating an evidence directory.
    read_doi(bundle / "PUBLISHED_DOI.txt")
    before = rehearsal.tree_hashes(bundle)
    release_metadata = metadata_payload(bundle, enforce_new_artifacts=True)
    approved = manuscript_pdf_gate.require_local(bundle, upload_files(bundle))
    payloads = snapshot_uploads(bundle, approved)
    out = rehearsal.output_directory(output)
    draft = None
    receipt = {"state": "REHEARSAL_STARTED", "published": False, "bundle_before": before}
    try:
        draft = api_call(credential, "POST", f"{BASE}/deposit/depositions", b"{}")
        identifier = draft.get("id")
        if type(identifier) is not int:
            raise PublisherError("rehearsal draft lacks integer id")
        receipt["draft_id"] = identifier
        check_draft_files(credential, identifier, approved, complete=False)
        for name, raw in payloads.items():
            uploaded = api_call(credential, "PUT", draft["links"]["bucket"] + "/" + urllib.parse.quote(name, safe=""), raw, "application/octet-stream")
            if str(uploaded.get("checksum", "")).removeprefix("md5:") != hashlib.md5(raw).hexdigest():
                raise PublisherError("rehearsal upload checksum differs")
        api_call(credential, "PUT", f"{BASE}/deposit/depositions/{identifier}", json.dumps(release_metadata).encode("utf-8"))
        check_draft_files(credential, identifier, approved, complete=True)
        checked = api_call(credential, "GET", f"{BASE}/deposit/depositions/{identifier}")
        native = api_call(credential, "GET", f"{BASE}/records/{identifier}/draft", accept_native=True)
        expected = release_metadata["metadata"]
        if any(checked.get("metadata", {}).get(k) != v for k, v in expected.items() if k != "copyright") or native.get("metadata", {}).get("copyright") != expected.get("copyright"):
            raise PublisherError("rehearsal metadata or copyright differs")
        if manuscript_pdf_gate.require_local(bundle, upload_files(bundle)) != approved:
            raise PublisherError("rehearsal package changed before publish boundary")
        receipt.update(state="DRAFT_READBACK_VERIFIED", draft_readback=checked, native_readback=native, approved=approved)
    finally:
        rehearsal.cleanup_window()
        if isinstance(draft, dict) and type(draft.get("id")) is int:
            # Keep the 404/410 code available while sanitizing all other failures.
            receipt["deletion"] = delete_rehearsal_draft(credential, draft["id"])
        receipt["bundle_after"] = rehearsal.tree_hashes(bundle)
        if receipt["bundle_after"] != before:
            raise PublisherError("rehearsal changed bundle bytes")
        receipt["state"] = "REHEARSED_DRAFT_DELETED" if receipt["state"] == "DRAFT_READBACK_VERIFIED" else "HOLD_REHEARSAL_DRAFT_DELETED"
        rehearsal.save(out, receipt, token=credential)
    return receipt


def delete_rehearsal_draft(credential, identifier):
    url = f"{BASE}/deposit/depositions/{identifier}"
    api_call(credential, "DELETE", url)
    result = api_call(credential, "GET", url, allow_not_found=True)
    if result is not None:
        raise PublisherError("rehearsal draft still exists after deletion")
    return {"draft_id": identifier, "deleted": True, "status": "HTTP_404_OR_410"}


def plan(date: str, base: Path = HERE) -> dict[str, Any]:
    rows = []
    for bundle in bundles(date, base):
        metadata = metadata_payload(bundle)
        title = metadata["metadata"]["title"]
        rows.append(
            {
                "bundle": str(bundle),
                "title": title,
                "files": [path.name for path in upload_files(bundle)],
                "draft_id": draft_id(bundle),
                "published_doi": read_doi(bundle / "PUBLISHED_DOI.txt"),
            }
        )
    return {"date": date, "mode": "LOCAL_PLAN", "bundles": rows, "external_mutation": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--rehearse", action="store_true")
    parser.add_argument("--go", action="store_true")
    parser.add_argument("--enforce-new-artifacts", action="store_true", help="deny new publication without a current certificate, approved manuscript binding and claim coverage")
    args = parser.parse_args()
    credential = ""
    try:
        rehearsal.require_production()
        if args.rehearse:
            if args.publish or not args.go or not args.enforce_new_artifacts:
                raise PublisherError("rehearsal requires --go --enforce-new-artifacts without --publish")
            credential = token()
            results = [rehearse_bundle(bundle, credential) for bundle in bundles(args.date)]
            print(json.dumps({"status": "REHEARSED", "results": results}, indent=2))
            return 0
        if not args.publish and not args.go:
            print(json.dumps(plan(args.date), indent=2, sort_keys=True))
            return 0
        if not (args.publish and args.go):
            raise PublisherError("irreversible publication requires both --publish and --go")
        if not args.enforce_new_artifacts:
            raise PublisherError("new-artifact publication requires --enforce-new-artifacts")
        print(json.dumps(plan(args.date), indent=2, sort_keys=True))
        credential = token()
        results = []
        for bundle in bundles(args.date):
            results.append({"bundle": str(bundle), "doi": publish_bundle(bundle, credential, enforce_new_artifacts=True)})
        print(json.dumps({"date": args.date, "status": "PUBLISHED", "results": results}, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        message = str(exc).replace(credential, "***") if credential else str(exc)
        print(json.dumps({"status": "HOLD", "error": type(exc).__name__ + ": " + message}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
