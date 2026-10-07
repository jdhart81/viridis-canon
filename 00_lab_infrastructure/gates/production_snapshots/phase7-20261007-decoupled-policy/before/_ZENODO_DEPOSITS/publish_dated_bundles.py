#!/usr/bin/env python3
"""Idempotent Zenodo publisher for one guarded dated Viridis bundle wave.

Default mode is a local plan and performs no network call. Irreversible mode
requires both ``--publish`` and ``--go`` and is intended to run only as the
publisher argv supplied to ``weekend_canon_lockstep.py`` after Justin approves
that exact dry-run surface.
"""

from __future__ import annotations

import argparse
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
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import release_coherence

BASE = "https://zenodo.org/api"
TOKEN_PATH = ROOT / "secrets/Zenodo_API/Zenodo_token.md"
DOI_RE = re.compile(r"10\.\d{4,9}/zenodo\.\d+")


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
            "reasons": [type(exc).__name__ + ": " + str(exc)]}}), file=sys.stderr)


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
    return payload


def validated_zenodo_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname != "zenodo.org"
        or parsed.port not in (None, 443) or parsed.username or parsed.password
        or not parsed.path.startswith("/api/") or parsed.fragment
        or any(key.lower() == "access_token" for key, _ in urllib.parse.parse_qsl(parsed.query))):
        raise PublisherError("Zenodo request destination must be the configured HTTPS API without URL credentials")
    return url


class ZenodoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validated_zenodo_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def api_call(
    credential: str,
    method: str,
    url: str,
    data: bytes | None = None,
    content_type: str | None = "application/json",
    *,
    allow_array: bool = False,
) -> Any:
    validated_zenodo_url(url)
    headers = {"Content-Type": content_type} if content_type else {}
    headers["Authorization"] = "Bearer " + credential
    opener = urllib.request.build_opener(ZenodoRedirectHandler())
    raw = ""
    for attempt in range(4):
        request = urllib.request.Request(
            url,
            method=method,
            data=data,
            headers=headers,
        )
        try:
            with opener.open(request, timeout=90) as response:
                raw = response.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 502, 503, 504} and attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise PublisherError(
                f"Zenodo {method} failed with HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            if attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            raise PublisherError(f"Zenodo {method} connection failed ({type(exc.reason).__name__})") from exc
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PublisherError("Zenodo response was not valid JSON") from exc
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


def publish_bundle(bundle: Path, credential: str, *, enforce_new_artifacts=False) -> str:
    prior = read_doi(bundle / "PUBLISHED_DOI.txt")
    if prior:
        return prior
    if not enforce_new_artifacts:
        raise PublisherError("new-artifact publication requires --enforce-new-artifacts")
    release_metadata = metadata_payload(bundle, enforce_new_artifacts=True)
    deposition = ensure_draft(bundle, credential)
    identifier = deposition.get("id")
    if not isinstance(identifier, int):
        raise PublisherError(f"{bundle}: draft response lacks id")
    metadata = deposition.get("metadata")
    if isinstance(metadata, dict):
        existing_doi = metadata.get("doi")
        if isinstance(existing_doi, str) and DOI_RE.fullmatch(existing_doi):
            write_once(bundle / "PUBLISHED_DOI.txt", existing_doi)
            return existing_doi
    links = deposition.get("links")
    bucket = links.get("bucket") if isinstance(links, dict) else None
    if not isinstance(bucket, str) or not bucket:
        raise PublisherError(f"{bundle}: draft response lacks bucket")
    for path in upload_files(bundle):
        try:
            api_call(
                credential,
                "PUT",
                f"{bucket}/{path.name}",
                path.read_bytes(),
                "application/octet-stream",
            )
        except PublisherError as exc:
            raise PublisherError(
                f"{bundle.name}: upload {path.name} failed: {exc}"
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
    published = api_call(
        credential,
        "POST",
        f"{BASE}/deposit/depositions/{identifier}/actions/publish",
    )
    published_metadata = published.get("metadata")
    doi = published_metadata.get("doi") if isinstance(published_metadata, dict) else None
    if not isinstance(doi, str) or DOI_RE.fullmatch(doi) is None:
        raise PublisherError(f"{bundle}: publish response lacks valid DOI")
    write_once(bundle / "PUBLISHED_DOI.txt", doi)
    return doi


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
    parser.add_argument("--go", action="store_true")
    parser.add_argument("--enforce-new-artifacts", action="store_true", help="deny new publication without a current certificate, approved manuscript binding and claim coverage")
    args = parser.parse_args()
    try:
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
    except (PublisherError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
