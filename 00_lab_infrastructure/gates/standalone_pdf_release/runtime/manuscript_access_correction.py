"""Proposed read-only access-copy rule; requires reviewed source activation.

No science admission, HTTP transport, receipt issuance or runtime installation
is implemented. Original complete observations stay in the returned audit;
only exact declared manuscript additions are exempted from file-set equality.
No normalized response is sent to an old scientific acceptance consumer.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from io import BytesIO
import json
import re
import zipfile

STANDARD = "VRS-DIGEST-MANUSCRIPT-ACCESS-CORRECTION-1"
FIELDS = {"standard", "status", "record_id", "doi", "source_manifest_sha256",
          "source_archive_sha256", "original_files", "copies", "authority"}
FILE_FIELDS = {"filename", "sha256", "md5", "bytes"}
COPY_FIELDS = FILE_FIELDS | {"run_id", "member"}


class AccessCorrectionHold(ValueError):
    pass


def need(value, reason):
    if not value:
        raise AccessCorrectionHold("HOLD_MANUSCRIPT_ACCESS_" + reason)


def _hashes(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "md5": hashlib.md5(data).hexdigest(), "bytes": len(data)}


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def require_pair(actual_legacy, actual_native, saved_legacy, saved_native, *,
                 receipt, manifest_bytes, archive_bytes, download,
                 authority_consumer, protected_projection):
    """Check complete public observations plus exact admitted archive copies.

    The caller must first admit saved registration through its exact historical
    source and preserve genuine version-chain handling. If version flags have
    changed, this rule holds; the existing separately approved chain consumer
    must establish that transition. This function grants no flag exception.
    """
    need(isinstance(receipt, dict) and set(receipt) == FIELDS
         and receipt["standard"] == STANDARD
         and receipt["status"] == "EXACT_EXISTING_ARCHIVE_ACCESS_COPIES", "CLOSED_RECEIPT")
    rid = receipt["record_id"]; doi = receipt["doi"]
    need(isinstance(rid, str) and re.fullmatch(r"[1-9][0-9]*", rid)
         and doi == "10.5281/zenodo." + rid, "RECORD_ID")
    authority = authority_consumer(receipt["authority"])
    need(isinstance(authority, dict) and authority.get("status") == "EXACT_USER_ACCESS_COPY_AUTHORITY_PASS", "EXACT_USER_AUTHORITY")
    need(hashlib.sha256(manifest_bytes).hexdigest() == receipt["source_manifest_sha256"]
         and hashlib.sha256(archive_bytes).hexdigest() == receipt["source_archive_sha256"], "SOURCE_BYTES")
    manifest = json.loads(manifest_bytes)
    notes = manifest.get("notes")
    need(isinstance(notes, list) and notes, "NOTE_INVENTORY")
    runs = {n["run_id"] for n in notes}
    need(len(runs) == len(notes) and all(re.fullmatch(r"Run-[0-9]{3}", n) for n in runs), "UNIQUE_RUNS")
    originals = receipt["original_files"]; copies = receipt["copies"]
    need(isinstance(originals, list) and originals and isinstance(copies, list) and copies, "FILE_INVENTORY")
    need(all(isinstance(f, dict) and set(f) == FILE_FIELDS for f in originals)
         and all(isinstance(f, dict) and set(f) == COPY_FIELDS for f in copies), "CLOSED_FILES")
    original = {f["filename"]: f for f in originals}; additions = {f["filename"]: f for f in copies}
    need(len(original) == len(originals) and len(additions) == len(copies)
         and len({f["run_id"] for f in copies}) == len(copies)
         and not set(original) & set(additions), "UNIQUE_DISJOINT_FILES")
    for f in originals + copies:
        need(isinstance(f["filename"], str) and "/" not in f["filename"] and "\\" not in f["filename"]
             and type(f["bytes"]) is int and f["bytes"] > 0
             and re.fullmatch(r"[0-9a-f]{64}", f["sha256"])
             and re.fullmatch(r"[0-9a-f]{32}", f["md5"]), "FILE_BINDING")
    inventory = {f["path"]: f for f in manifest.get("archive_members", [])}
    declared = {f["filename"]: f for f in manifest.get("uploads", [])}
    need("METHODS_NOTES.zip" in declared and _hashes(archive_bytes) == {k: declared["METHODS_NOTES.zip"][k] for k in ("sha256", "md5", "bytes")}, "DECLARED_ARCHIVE")
    for name, f in declared.items():
        need(name in original and all(original[name][k] == f[k] for k in ("sha256", "md5", "bytes")), "ORIGINAL_MANIFEST_UPLOADS")
    need("DIGEST_MANIFEST.json" in original and _hashes(manifest_bytes) == {k: original["DIGEST_MANIFEST.json"][k] for k in ("sha256", "md5", "bytes")}, "ORIGINAL_MANIFEST_BYTES")
    verified = []
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        need(len({i.filename for i in archive.infolist()}) == len(archive.infolist()), "DUPLICATE_ARCHIVE_MEMBER")
        for f in copies:
            run = f["run_id"]; member = "notes/" + run + "/paper.pdf"
            need(run in runs and f["member"] == member and f["filename"].startswith(run + "-")
                 and f["filename"].endswith(".pdf") and member in inventory, "EXACT_NOTE_MANUSCRIPT")
            note = next(n for n in notes if n["run_id"] == run)
            paper_rows = [v for v in note.get("uploads", []) if v.get("filename") == "paper.pdf"]
            need(len(paper_rows) == 1 and paper_rows[0]["sha256"] == f["sha256"], "NOTE_ADMISSION_HASH")
            data = archive.read(member)
            need(data.startswith(b"%PDF-") and _hashes(data) == {k: f[k] for k in ("sha256", "md5", "bytes")}
                 and all(inventory[member][k] == f[k] for k in ("sha256", "md5", "bytes")), "EXACT_ARCHIVED_PDF")
            public = download(rid, f["filename"])
            need(isinstance(public, bytes) and public == data, "PUBLIC_PDF_BYTES")
            verified.append(deepcopy(f))
    for body in (actual_legacy, saved_legacy):
        need(str(body.get("id")) == rid and body.get("doi") == doi, "LEGACY_IDENTITY")
    for body in (actual_native, saved_native):
        need(body.get("id") == rid and body.get("pids", {}).get("doi", {}).get("identifier") == doi, "NATIVE_IDENTITY")
    saved_rows = saved_legacy.get("files")
    actual_rows = actual_legacy.get("files")
    need(isinstance(saved_rows, list) and isinstance(actual_rows, list), "LEGACY_FILES")
    saved_map = {f.get("key"): f for f in saved_rows}; actual_map = {f.get("key"): f for f in actual_rows}
    need(len(saved_map) == len(saved_rows) and len(actual_map) == len(actual_rows)
         and set(saved_map) == set(original) and set(actual_map) == set(original) | set(additions), "EXACT_ONLY_ADDITIONS")
    for name, bound in {**original, **additions}.items():
        row = actual_map[name]
        need(row.get("size") == bound["bytes"] and row.get("checksum") == "md5:" + bound["md5"], "PUBLIC_FILE_CHECKSUM")
        public = download(rid, name)
        need(isinstance(public, bytes) and _hashes(public) == {k: bound[k] for k in ("sha256", "md5", "bytes")}, "ALL_ORIGINAL_PUBLIC_BYTES")
        if name in original:
            need(saved_map[name].get("size") == bound["bytes"] and saved_map[name].get("checksum") == "md5:" + bound["md5"], "ORIGINAL_RECEIPT_BYTES")
    audits = []
    for kind, actual, saved in (("LEGACY", actual_legacy, saved_legacy), ("NATIVE", actual_native, saved_native)):
        left = protected_projection(actual, representation=kind)
        right = protected_projection(saved, representation=kind)
        if kind == "LEGACY":
            left["files"] = [f for f in left["files"] if f.get("key", f.get("filename")) in original]
        else:
            fields = left["files"]
            need(set(fields["entries"]) == set(original) | set(additions), "NATIVE_ONLY_ADDITIONS")
            for name, bound in additions.items():
                row = fields["entries"][name]
                need(row.get("key") == name and row.get("size") == bound["bytes"] and row.get("checksum") == "md5:" + bound["md5"], "NATIVE_PDF_BYTES")
            need(fields.get("count") == right["files"].get("count") + len(additions)
                 and fields.get("total_bytes") == right["files"].get("total_bytes") + sum(v["bytes"] for v in additions.values()), "NATIVE_DERIVED_TOTALS")
            fields["entries"] = {name: row for name, row in fields["entries"].items() if name in original}
            fields["count"] = right["files"]["count"]; fields["total_bytes"] = right["files"]["total_bytes"]
        need(_canonical(left) == _canonical(right), "UNCHANGED_ALL_OTHER_PROTECTED_CONTENT")
        audits.append({"representation": kind, "original_protected_sha256": hashlib.sha256(_canonical(right)).hexdigest()})
    return {"standard": STANDARD, "status": "EXACT_ARCHIVE_ACCESS_COPIES_PROTECTED_READBACK_PASS",
            "record_id": rid, "doi": doi, "added_pdfs": verified, "protected_audits": audits,
            "observed_before": {"legacy": deepcopy(saved_legacy), "native": deepcopy(saved_native)},
            "observed_after": {"legacy": deepcopy(actual_legacy), "native": deepcopy(actual_native)},
            "authority": deepcopy(receipt["authority"]), "certifies": False}
