#!/usr/bin/env python3
"""Propagate one verified public release as metadata; never mint a DOI or adopt code.

Default mode plans from public readbacks without writing. --apply requires the
existing CRON_SECRET in the environment and invokes the fixed metadata callback.
An interrupted callback is recovered by reading current public state first.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from deadline import Budget, DeadlineExceeded

STANDARD = "VRS-POSTPUBLICATION-METADATA-SYNC-2"
REPOSITORY = "jdhart81/viridis-canon"
CATALOG_REPOSITORY = "https://github.com/" + REPOSITORY
CATALOG_URL = "https://jdhart81.github.io/viridis-canon/data/catalog.json"
MAIN_URL = "https://api.github.com/repos/jdhart81/viridis-canon/git/ref/heads/main"
SYNC_URL = "https://viridisconservation.com/api/cron/research-knowledge"
REGISTRY_URL = "https://viridisconservation.com/api/viridisos/research-kernels"
DECISION_TREE_URL = "https://viridisconservation.com/api/viridisos/decision-tree"
CATALOG_SCHEMA = "https://jdhart81.github.io/viridis-canon/schemas/research-catalog-v1.json"
SHA40 = re.compile(r"[0-9a-f]{40}")
SHA64 = re.compile(r"[0-9a-f]{64}")
DOI = re.compile(r"10\.5281/zenodo\.(\d+)")
SSH_CALLBACK_SCRIPT = r"""const [commit,digest,countText,timeoutText]=process.argv.slice(2);
const fail=()=>{process.stdout.write(JSON.stringify({status:'hold',reason:'REMOTE_METADATA_SYNC_FAILED'}));process.exitCode=2};
(async()=>{try{
if(!/^[a-f0-9]{40}$/.test(commit)||!/^[a-f0-9]{64}$/.test(digest)||!/^\d+$/.test(countText)||!/^\d+$/.test(timeoutText)||Number(timeoutText)<1||Number(timeoutText)>120000||!process.env.CRON_SECRET)return fail();
const response=await fetch('http://127.0.0.1:3000/api/cron/research-knowledge',{method:'POST',redirect:'error',headers:{'Content-Type':'application/json',Authorization:'Bearer '+process.env.CRON_SECRET},body:JSON.stringify({expected_canon_commit:commit,expected_catalog_digest:digest,expected_record_count:Number(countText)}),signal:AbortSignal.timeout(Number(timeoutText))});
const v=await response.json();
if(response.status!==200||!['synchronized','unchanged'].includes(v.status)||!/^[a-f0-9]{64}$/.test(v.catalog_digest)||!/^[a-f0-9]{40}$/.test(v.canon_commit)||!Number.isSafeInteger(v.record_count)||v.record_count<0)return fail();
process.stdout.write(JSON.stringify({status:v.status,catalog_digest:v.catalog_digest,canon_commit:v.canon_commit,record_count:v.record_count}));
}catch{return fail()}})();
"""


class SyncHold(RuntimeError):
    """Only fixed, nonsecret reason codes may cross the command boundary."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise SyncHold(reason)


def regular(path, root):
    path = Path(path).absolute()
    root = Path(root).resolve(strict=True)
    require(not any(part.is_symlink() for part in (path, *path.parents)), "HOLD_INPUT_SYMLINK")
    require(path.is_file(), "HOLD_INPUT_MISSING")
    path = path.resolve(strict=True)
    require(path.is_relative_to(root), "HOLD_INPUT_OUTSIDE_ROOT")
    return path


def object_file(path):
    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=unique_object)
    except (OSError, ValueError, TypeError):
        raise SyncHold("HOLD_INPUT_JSON") from None
    require(isinstance(value, dict), "HOLD_INPUT_OBJECT")
    return value


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "HOLD_DUPLICATE_JSON_KEY")
        value[key] = item
    return value


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _http_json(method, url, *, body=None, secret=None, budget, approved_scope=None):
    """Fixed destinations only; bearer requests never follow a redirect."""
    budget.require_remaining()
    allowed = url in (CATALOG_URL, MAIN_URL, SYNC_URL, REGISTRY_URL, DECISION_TREE_URL) or re.fullmatch(
        r"https://zenodo\.org/api/records/\d+", url
    ) or re.fullmatch(r"https://raw\.githubusercontent\.com/jdhart81/viridis-canon/[0-9a-f]{40}/docs/data/catalog\.json", url)
    require(allowed and method in {"GET", "POST"}, "HOLD_HTTP_DESTINATION")
    require((method == "POST") == (url == SYNC_URL), "HOLD_HTTP_METHOD")
    if method == "POST":
        require_mutation_authority(approved_scope)
    headers = {"User-Agent": "Viridis-Release-Sync/1", "Cache-Control": "no-cache", "Accept": "application/json"}
    if secret is not None:
        require(method == "POST" and url == SYNC_URL, "HOLD_SECRET_DESTINATION")
        headers["Authorization"] = "Bearer " + secret
    data = None if body is None else canonical(body).encode()
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=budget.remaining_cap(30)) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
            require(len(raw) <= 16 * 1024 * 1024, "HOLD_REMOTE_SIZE")
            value = json.loads(raw, object_pairs_hook=unique_object)
            require(isinstance(value, dict), "HOLD_REMOTE_OBJECT")
            return response.status, value
    except SyncHold:
        raise
    except urllib.error.HTTPError as error:
        return error.code, {}
    except Exception:
        raise SyncHold("HOLD_REMOTE_UNAVAILABLE") from None


def http_json(method, url, *, body=None, secret=None, budget, approved_scope=None):
    return budget.call(_http_json, method, url, body=body, secret=secret, budget=budget, approved_scope=approved_scope)


def get(http, url, *, budget):
    try:
        status, value = budget.call(http, "GET", url, budget=budget)
    except DeadlineExceeded:
        raise SyncHold("HOLD_SHARED_DEADLINE") from None
    except Exception:
        raise SyncHold("HOLD_REMOTE_UNAVAILABLE") from None
    require(status == 200 and isinstance(value, dict), "HOLD_PUBLIC_READBACK")
    return value


def expected_label(row):
    metadata = row.get("metadata")
    coverage = metadata.get("verification_coverage") if isinstance(metadata, dict) else None
    certified = (isinstance(coverage, dict) and coverage.get("status") == "PASS"
                 and coverage.get("canon_eligible") is True)
    return "VERIFIED" if certified and row.get("status") == "verified" and row.get("integrity") == "gate-passed" else "UNCERTIFIED"


def publication_dois(value):
    """Recognize only final supported publisher receipts, never a reserved DOI."""
    standard = value.get("standard")
    if standard == "VRS-ZENODO-SUCCESSOR-PUBLICATION-1":
        require(value.get("state") == "ZENODO_SUCCESSOR_WAVE_PUBLISHED", "HOLD_SUCCESSOR_PUBLICATION_PENDING")
        rows = value.get("results")
        require(isinstance(rows, list) and rows, "HOLD_SUCCESSOR_PUBLICATION_ROWS")
        kind = "successor-wave"
    elif standard == "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2":
        require(value.get("status") == "PUBLISHED_STRICT_READBACK_PASS" and value.get("published") is True
                and value.get("source_session_exit_succeeded") is True and value.get("certifies") is False,
                "HOLD_DIGEST_PUBLICATION_PENDING")
        rows, kind = [value], "methods-digest"
    elif (value.get("status") == "verified" and value.get("repository") == REPOSITORY
          and value.get("branch") == "main" and value.get("spine_changed") is False):
        rows, kind = value.get("bundles"), "lockstep"
        require(isinstance(rows, list) and rows, "HOLD_LOCKSTEP_PUBLICATION_ROWS")
    else:
        raise SyncHold("HOLD_UNSUPPORTED_PUBLICATION_RECEIPT")
    dois = set()
    for row in rows:
        require(isinstance(row, dict), "HOLD_PUBLICATION_DOI_ROW")
        doi = row.get("doi")
        require(isinstance(doi, str) and DOI.fullmatch(doi) and doi not in dois, "HOLD_PUBLICATION_DOI")
        if "record_id" in row:
            require(str(row["record_id"]) == DOI.fullmatch(doi).group(1), "HOLD_PUBLICATION_RECORD_ID")
        dois.add(doi)
    return kind, dois


def durable_dois(path):
    if path.name == "PUBLISHED_DOI.txt":
        value = path.read_text().strip()
        require(DOI.fullmatch(value), "HOLD_DOI_RECEIPT")
        return {value}
    require(path.name in {"SUCCESSOR_PUBLICATION_RECEIPT.json", "TERMINAL_RESULT.json"}, "HOLD_DOI_RECEIPT_NAME")
    kind, dois = publication_dois(object_file(path))
    require(kind in {"successor-wave", "methods-digest"}, "HOLD_DOI_RECEIPT_FORMAT")
    return dois


def catalog_rows(catalog):
    require(catalog.get("schema") == CATALOG_SCHEMA and catalog.get("repository") == CATALOG_REPOSITORY,
            "HOLD_CATALOG_IDENTITY")
    require(catalog.get("publication_scope") == "public" and catalog.get("human_publish_gate") is True,
            "HOLD_CATALOG_PUBLICATION")
    require(SHA64.fullmatch(str(catalog.get("catalog_digest", ""))) is not None, "HOLD_CATALOG_DIGEST")
    require(digest({key: value for key, value in catalog.items() if key != "catalog_digest"}) == catalog["catalog_digest"],
            "HOLD_CATALOG_DIGEST")
    rows = catalog.get("records")
    require(isinstance(rows, list) and rows, "HOLD_CATALOG_RECORDS")
    by_id, paths = {}, set()
    for row in rows:
        require(isinstance(row, dict), "HOLD_CATALOG_RECORD")
        identity = row.get("record_id")
        require(isinstance(identity, str) and identity and identity not in by_id, "HOLD_CATALOG_RECORD_ID")
        require(isinstance(row.get("title"), str) and bool(row["title"])
                and isinstance(row.get("path"), str) and bool(row["path"]) and row["path"] not in paths,
                "HOLD_CATALOG_RECORD_CONTENT")
        paths.add(row["path"])
        require(SHA64.fullmatch(str(row.get("source_sha256", ""))) is not None, "HOLD_CATALOG_SOURCE_HASH")
        require(isinstance(row.get("doi", ""), str), "HOLD_CATALOG_DOI")
        by_id[identity] = row
    return by_id


def verify_canon_source(http, expected_commit, expected_digest, *, budget):
    """An unrelated later main commit may preserve this exact catalog release."""
    main = get(http, MAIN_URL, budget=budget)
    require(isinstance(main.get("object"), dict), "HOLD_PUBLIC_MAIN_IDENTITY")
    current = main["object"].get("sha")
    require(isinstance(current, str) and SHA40.fullmatch(current), "HOLD_PUBLIC_MAIN_IDENTITY")
    for commit in sorted({expected_commit, current}):
        pinned = get(http, "https://raw.githubusercontent.com/" + REPOSITORY + "/" + commit + "/docs/data/catalog.json", budget=budget)
        catalog_rows(pinned)
        require(pinned["catalog_digest"] == expected_digest,
                "HOLD_CURRENT_CANON_CATALOG_DRIFT" if commit == current else "HOLD_RECEIPT_COMMIT_CATALOG_MISMATCH")
    return current


def validate_registry(registry, expected, rows, allowed_commits=None):
    require(registry.get("standard") == "VOS-CANON-KERNEL-REGISTRY-3", "HOLD_APP_REGISTRY_SCHEMA")
    require(registry.get("catalog_digest") == expected["expected_catalog_digest"], "HOLD_APP_CATALOG_DIGEST")
    require(isinstance(registry.get("canon_commit"), str) and registry["canon_commit"] in
            (allowed_commits or {expected["expected_canon_commit"]}), "HOLD_APP_CANON_COMMIT")
    require(type(registry.get("record_count")) is int and registry["record_count"] == expected["expected_record_count"], "HOLD_APP_RECORD_COUNT")
    public = registry.get("records")
    require(isinstance(public, list) and len(public) == len(rows), "HOLD_APP_RECORDS")
    indexed = {}
    for row in public:
        require(isinstance(row, dict), "HOLD_APP_RECORD")
        identity = row.get("record_id")
        require(isinstance(identity, str) and identity in rows and identity not in indexed, "HOLD_APP_RECORD_ID")
        indexed[identity] = row
    require(set(indexed) == set(rows), "HOLD_APP_RECORDS")
    for identity, source in rows.items():
        row = indexed[identity]
        for source_key, public_key in (("title", "title"), ("path", "path"), ("lean_module", "lean_module"),
                                       ("doi", "doi"), ("status", "canon_status"),
                                       ("integrity", "canon_integrity"), ("source_sha256", "source_sha256")):
            require(row.get(public_key, "") == source.get(source_key, ""), "HOLD_APP_RECORD_MISMATCH")
        require(row.get("certification_label") == expected_label(source), "HOLD_APP_CERTIFICATION_LABEL")
        metadata = source.get("metadata")
        coverage = metadata.get("verification_coverage") if isinstance(metadata, dict) else None
        coverage = coverage if isinstance(coverage, dict) else None
        require(row.get("verification_coverage") == coverage, "HOLD_APP_COVERAGE_LABEL")
        require(row.get("certification_detail") == (coverage.get("label") if coverage and coverage.get("label") is not None
                else "No current hash-bound certification coverage is recorded."), "HOLD_APP_COVERAGE_LABEL")
        require(row.get("caveat", "") == (source.get("caveat") or ""), "HOLD_APP_RECORD_MISMATCH")
        require(row.get("certification_authority") is False, "HOLD_APP_CERTIFICATION_AUTHORITY")
        require(row.get("certification_scope") == "Current public Canon classification; not an empirical or production certificate",
                "HOLD_APP_CERTIFICATION_SCOPE")
        for key in ("function_ids", "decision_tree_paths"):
            values = row.get(key)
            require(isinstance(values, list) and all(isinstance(item, str) for item in values)
                    and len(values) == len(set(values)), "HOLD_APP_RUNTIME_PROVENANCE")
        quarantine = source.get("status") == "quarantined"
        verified = expected_label(source) == "VERIFIED"
        require(row.get("kernel_state") == ("QUARANTINED" if quarantine else "KERNEL_CANDIDATE" if verified else "NOT_ELIGIBLE")
                and row.get("research_state") == ("QUARANTINED" if quarantine else "ZERO_SORRY_RESEARCH" if verified else "CANON_WORKING"),
                "HOLD_APP_CLASSIFICATION")
        if not verified:
            require(row.get("os_tier") == "reference" and row.get("disposition") == ("QUARANTINED" if quarantine else "REFERENCE_ONLY"),
                    "HOLD_APP_CURRENT_AUTHORITY")
    policy = registry.get("policy")
    require(isinstance(policy, dict) and all(policy.get(key) is False for key in
            ("automatic_certification_authority", "automatic_decision_tree_activation", "automatic_module_activation")),
            "HOLD_APP_AUTOMATIC_AUTHORITY")
    runtime_source = registry.get("runtime_source")
    require(isinstance(runtime_source, dict) and runtime_source.get("metadata_is_runtime_activation") is False,
            "HOLD_APP_RUNTIME_AUTHORITY")
    stats = registry.get("stats")
    require(isinstance(stats, dict) and type(stats.get("records")) is int and stats["records"] == len(rows)
            and type(stats.get("kernel_candidates")) is int
            and stats["kernel_candidates"] == sum(expected_label(row) == "VERIFIED" for row in rows.values()),
            "HOLD_APP_REGISTRY_STATS")
    return digest(public)


def validate_decision_tree(value, registry):
    require(value.get("schema_version") == 3, "HOLD_APP_DECISION_TREE_SCHEMA")
    for key in ("catalog_digest", "canon_commit", "record_count", "runtime_source"):
        require(value.get(key) == registry.get(key), "HOLD_APP_DECISION_TREE_IDENTITY")
    authority = value.get("authority")
    require(isinstance(authority, dict) and authority.get("automatic_kernel_activation") is False,
            "HOLD_APP_DECISION_TREE_AUTHORITY")
    stats = value.get("stats")
    require(isinstance(stats, dict) and stats.get("canon_records") == registry["record_count"]
            and stats.get("kernel_candidate_records") == registry["stats"]["kernel_candidates"],
            "HOLD_APP_DECISION_TREE_STATS")
    public = value.get("corpus_records")
    require(isinstance(public, list) and len(public) == len(registry["records"]), "HOLD_APP_DECISION_TREE_RECORDS")
    records = {row["record_id"]: row for row in registry["records"]}
    seen = set()
    extras = {"module_ids", "decision_family_ids", "runtime_disposition"}
    for row in public:
        require(isinstance(row, dict) and set(row) >= extras, "HOLD_APP_DECISION_TREE_RECORD")
        identity = row.get("record_id")
        require(isinstance(identity, str) and identity in records and identity not in seen, "HOLD_APP_DECISION_TREE_RECORD_ID")
        seen.add(identity)
        require({key: item for key, item in row.items() if key not in extras} == records[identity],
                "HOLD_APP_DECISION_TREE_FULL_ROW_MISMATCH")
        require(row["decision_family_ids"] == row["decision_tree_paths"]
                and row["runtime_disposition"] == row["disposition"], "HOLD_APP_DECISION_TREE_PROVENANCE")
        require(isinstance(row["module_ids"], list) and all(isinstance(item, str) for item in row["module_ids"])
                and len(row["module_ids"]) == len(set(row["module_ids"]))
                and set(row["module_ids"]) <= set(row["function_ids"]), "HOLD_APP_DECISION_TREE_PROVENANCE")
    require(seen == set(records), "HOLD_APP_DECISION_TREE_RECORDS")
    return digest(public)


def app_state(http, expected, rows, allowed_commits, *, budget):
    registry = get(http, REGISTRY_URL, budget=budget)
    registry_digest = validate_registry(registry, expected, rows, allowed_commits)
    decision_tree = get(http, DECISION_TREE_URL, budget=budget)
    map_digest = validate_decision_tree(decision_tree, registry)
    return registry, registry_digest, map_digest


def require_mutation_authority(approved_scope):
    import root_scope
    root_scope.require_mutation_authority(approved_scope)


def atomic_receipt(path, value):
    require(not any(p.is_symlink() for p in (path, *path.parents)), "HOLD_RECEIPT_SYMLINK")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and object_file(path) == value:
        return False
    fd, name = tempfile.mkstemp(prefix=".postpublication-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def metadata_callback(expected, *, transport, secret, http, budget, runner=subprocess.run, approved_scope=None):
    budget.require_remaining()
    require_mutation_authority(approved_scope)
    require(transport in {"environment", "existing-app-ssh"}, "HOLD_CALLBACK_TRANSPORT")
    if transport == "environment":
        try:
            return budget.call(http, "POST", SYNC_URL, body=expected, secret=secret, budget=budget, approved_scope=approved_scope)
        except DeadlineExceeded:
            raise SyncHold("HOLD_SHARED_DEADLINE") from None
        except Exception:
            raise SyncHold("HOLD_METADATA_CALLBACK_UNCERTAIN") from None
    commit, catalog, count = (expected["expected_canon_commit"], expected["expected_catalog_digest"], expected["expected_record_count"])
    require(SHA40.fullmatch(commit) and SHA64.fullmatch(catalog) and type(count) is int and 0 < count < 1000000,
            "HOLD_SSH_CALLBACK_ARGUMENTS")
    timeout_ms = int(budget.remaining_cap(120) * 1000)
    require(timeout_ms >= 1, "HOLD_SHARED_DEADLINE")
    command = "docker exec -i viridis-app node - " + commit + " " + catalog + " " + str(count) + " " + str(timeout_ms)
    try:
        completed = budget.call(runner, ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10",
                            "root@192.241.131.123", command], input=SSH_CALLBACK_SCRIPT, text=True, capture_output=True,
                            timeout=budget.remaining_cap(150), check=False)
        require(completed.returncode == 0, "HOLD_SSH_CALLBACK")
        value = json.loads(completed.stdout)
        require(isinstance(value, dict) and set(value) == {"status", "catalog_digest", "canon_commit", "record_count"}, "HOLD_SSH_CALLBACK_OUTPUT")
        return 200, value
    except SyncHold:
        raise
    except DeadlineExceeded:
        raise SyncHold("HOLD_SHARED_DEADLINE") from None
    except Exception:
        raise SyncHold("HOLD_SSH_CALLBACK_OUTPUT") from None
    return True


def synchronize(receipt_path, doi_receipt_paths, *, root, apply=False, http=http_json, environ=None,
                transport="environment", runner=subprocess.run, budget, approved_scope=None):
    """Recover metadata only from a verified release, with injectable public HTTP."""
    budget.require_remaining()
    if apply:
        require_mutation_authority(approved_scope)
    root = Path(root).resolve(strict=True)
    receipt_path = regular(receipt_path, root)
    receipt_sha = file_hash(receipt_path)
    release = object_file(receipt_path)
    require(release.get("status") == "verified" and release.get("repository") == REPOSITORY
            and release.get("branch") == "main" and release.get("spine_changed") is False,
            "HOLD_UNVERIFIED_RELEASE")
    commit = release.get("commit_sha")
    require(isinstance(commit, str) and SHA40.fullmatch(commit), "HOLD_RELEASE_COMMIT")
    require(release.get("public_catalog_url") == CATALOG_URL, "HOLD_RELEASE_CATALOG_URL")
    require(SHA64.fullmatch(str(release.get("catalog_digest", ""))), "HOLD_RELEASE_DIGEST")
    bundles = release.get("bundles")
    require(isinstance(bundles, list) and bundles, "HOLD_RELEASE_BUNDLES")
    bundle_dois = set()
    for bundle in bundles:
        require(isinstance(bundle, dict) and DOI.fullmatch(str(bundle.get("doi", ""))), "HOLD_RELEASE_DOI")
        require(bundle["doi"] not in bundle_dois, "HOLD_RELEASE_DUPLICATE_DOI")
        bundle_dois.add(bundle["doi"])
    durable = {}
    for path in doi_receipt_paths:
        path = regular(path, root)
        for value in durable_dois(path):
            require(value not in durable, "HOLD_DOI_RECEIPT")
            durable[value] = {"path": str(path.relative_to(root)), "sha256": file_hash(path)}
    require(set(durable) == bundle_dois, "HOLD_DOI_RECEIPT_COVERAGE")
    secret = (os.environ if environ is None else environ).get("CRON_SECRET", "") if apply and transport == "environment" else ""
    require(transport in {"environment", "existing-app-ssh"}, "HOLD_CALLBACK_TRANSPORT")
    if apply and transport == "environment":
        require(isinstance(secret, str) and bool(secret) and "\n" not in secret and "\r" not in secret, "HOLD_CRON_AUTH_MISSING")
    catalog = get(http, CATALOG_URL, budget=budget)
    rows = catalog_rows(catalog)
    require(catalog["catalog_digest"] == release["catalog_digest"], "HOLD_RELEASE_CATALOG_DRIFT")
    current_main = verify_canon_source(http, commit, release["catalog_digest"], budget=budget)
    require(bundle_dois.issubset({row.get("doi") for row in rows.values()}), "HOLD_RELEASE_DOI_NOT_IN_CATALOG")
    zenodo = []
    for doi in sorted(bundle_dois):
        identifier = DOI.fullmatch(doi).group(1)
        record = get(http, "https://zenodo.org/api/records/" + identifier, budget=budget)
        metadata = record.get("metadata")
        actual = record.get("doi") or (metadata.get("doi") if isinstance(metadata, dict) else None)
        require(str(record.get("id")) == identifier and actual == doi, "HOLD_ZENODO_DOI_MISMATCH")
        require(record.get("is_published") is not False and record.get("submitted") is not False
                and record.get("draft") is not True, "HOLD_ZENODO_NOT_PUBLISHED")
        zenodo.append({"doi": doi, "record_id": identifier, "durable_receipt": durable[doi]})
    expected = {"expected_catalog_digest": catalog["catalog_digest"], "expected_canon_commit": commit,
                "expected_record_count": len(rows)}
    identity = digest({"release_sha256": receipt_sha, "expected": expected, "zenodo": zenodo})
    output = root / "reports/approved-release-sync/postpublication-sync" / (identity + ".json")
    summary = {"standard": STANDARD, "release_identity": identity, "release_receipt": str(receipt_path.relative_to(root)),
               "release_receipt_sha256": receipt_sha, "expected": expected, "zenodo": zenodo,
               "metadata_only": True, "runtime_adoption": False, "zenodo_mutations": 0,
               "registry_url": REGISTRY_URL, "decision_tree_url": DECISION_TREE_URL}
    try:
        registry, registry_digest, map_digest = app_state(http, expected, rows, {commit, current_main}, budget=budget)
        current = True
    except SyncHold as error:
        if str(error) == "HOLD_SHARED_DEADLINE":
            raise
        current = False
        registry_digest = map_digest = None
    if not apply:
        return {**summary, "status": "ALREADY_SYNCHRONIZED" if current else "READY_FOR_METADATA_SYNC",
                "registry_records_digest": registry_digest, "decision_tree_records_digest": map_digest,
                "writes_performed": False, "callback_attempted": False}
    callback_attempted = False
    try:
        if not current:
            callback_attempted = True
            require_mutation_authority(approved_scope)
            # Keep the historical receipt identity, but refresh using the latest
            # independently proven commit with the exact same public catalog.
            current_main = verify_canon_source(http, commit, expected["expected_catalog_digest"], budget=budget)
            callback_expected = {**expected, "expected_canon_commit": current_main}
            status, callback = metadata_callback(callback_expected, transport=transport, secret=secret, http=http, runner=runner,
                                                 budget=budget, approved_scope=approved_scope)
            require(status == 200 and isinstance(callback, dict), "HOLD_METADATA_CALLBACK")
            require(isinstance(callback.get("status"), str) and callback["status"] in {"synchronized", "unchanged"}, "HOLD_METADATA_CALLBACK_STATUS")
            for request_key, reply_key in (("expected_catalog_digest", "catalog_digest"),
                                           ("expected_canon_commit", "canon_commit"),
                                           ("expected_record_count", "record_count")):
                require(callback.get(reply_key) == callback_expected[request_key], "HOLD_METADATA_CALLBACK_MISMATCH")
            require(type(callback.get("record_count")) is int, "HOLD_METADATA_CALLBACK_MISMATCH")
            current_main = verify_canon_source(http, commit, expected["expected_catalog_digest"], budget=budget)
            registry, registry_digest, map_digest = app_state(http, expected, rows, {commit, current_main}, budget=budget)
        require(file_hash(receipt_path) == receipt_sha, "HOLD_RELEASE_RECEIPT_CHANGED")
        for doi, evidence in durable.items():
            require(file_hash(regular(root / evidence["path"], root)) == evidence["sha256"], "HOLD_DOI_RECEIPT_CHANGED")
        # Re-read both public authority pins after sync to reject concurrent releases.
        final_catalog = get(http, CATALOG_URL, budget=budget)
        catalog_rows(final_catalog)
        require(final_catalog["catalog_digest"] == expected["expected_catalog_digest"], "HOLD_RELEASE_CATALOG_DRIFT")
        current_main = verify_canon_source(http, commit, expected["expected_catalog_digest"], budget=budget)
        registry, registry_digest, map_digest = app_state(http, expected, rows, {commit, current_main}, budget=budget)
        budget.require_remaining()
        result = {**summary, "status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED", "registry_records_digest": registry_digest,
                  "decision_tree_records_digest": map_digest,
                  "publication_scope": "DOI_CANON_AND_DESCRIPTIVE_APP_METADATA", "runtime_execution_verified": False,
                  "metadata_source_commit": registry["canon_commit"],
                  "recovery": "Replay this receipt and DOI files; never invoke a Zenodo publisher."}
        if output.exists():
            previous = object_file(output)
            if previous.get("status") == result["status"]:
                stable_before = {k: v for k, v in previous.items() if k not in {"verified_at_utc", "metadata_source_commit"}}
                stable_after = {k: v for k, v in result.items() if k != "metadata_source_commit"}
                require(stable_before == stable_after, "HOLD_RECOVERY_RECEIPT_CONFLICT")
                return previous if previous.get("metadata_source_commit") == registry["canon_commit"] else {
                    **previous, "current_metadata_source_commit": registry["canon_commit"], "verified_receipt_preserved": True}
        result["verified_at_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        budget.cleanup_remaining_cap(30)
        atomic_receipt(output, result)
        return result
    except (SyncHold, DeadlineExceeded) as error:
        partial = {**summary, "status": "CANON_PUBLISHED_APP_METADATA_PENDING",
                   "reason": "HOLD_SHARED_DEADLINE" if isinstance(error, DeadlineExceeded) else str(error),
                   "callback_attempted": callback_attempted,
                   "recovery": "Replay this receipt and DOI files; public readback determines whether another metadata callback is needed."}
        if output.exists() and object_file(output).get("status") == "PRODUCTION_METADATA_PROPAGATION_VERIFIED":
            partial["existing_verified_receipt_sha256"] = file_hash(output)
            output = output.with_name(identity + "-hold-" + digest(partial) + ".json")
        budget.cleanup_remaining_cap(30)
        atomic_receipt(output, partial)
        return partial


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--doi-receipt", type=Path, action="append", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--transport", choices=("environment", "existing-app-ssh"), default="environment")
    args = parser.parse_args(argv)
    try:
        result = synchronize(args.receipt, args.doi_receipt, root=args.root, apply=args.apply, transport=args.transport, budget=Budget())
    except SyncHold as error:
        result = {"standard": STANDARD, "status": "HOLD_POSTPUBLICATION_SYNC", "reason": str(error), "zenodo_mutations": 0}
    except Exception:
        result = {"standard": STANDARD, "status": "HOLD_POSTPUBLICATION_SYNC", "reason": "HOLD_INPUT_OR_TRANSPORT", "zenodo_mutations": 0}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"ALREADY_SYNCHRONIZED", "READY_FOR_METADATA_SYNC", "PRODUCTION_METADATA_PROPAGATION_VERIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
