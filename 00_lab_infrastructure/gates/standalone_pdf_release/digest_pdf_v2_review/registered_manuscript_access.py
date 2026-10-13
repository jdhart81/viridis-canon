"""Additive registrar adapter proposal; original admission stays authoritative.

Install only through a genuine reviewed source closure. This module does not
rewrite the pinned registrar, fabricate GETs, grant a scientific verdict or
accept a cached access-copy PASS. All actual before/after views remain logged.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import manuscript_access_correction as access


def bound(root, value):
    access.need(isinstance(value, dict) and set(value) == {"path", "sha256"}
                and isinstance(value["path"], str) and re.fullmatch(r"[0-9a-f]{64}", str(value["sha256"])), "BOUND_SOURCE")
    p = Path(value["path"]); p = p if p.is_absolute() else Path(root) / p
    access.need(p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True))
                and not any(q.is_symlink() for q in (p, *p.parents)), "CONTAINED_REGULAR_SOURCE")
    before = p.stat(); raw = p.read_bytes(); after = p.stat()
    access.need((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns)
                and hashlib.sha256(raw).hexdigest() == value["sha256"], "SOURCE_HASH")
    return raw


def require_registration(root, registration_binding, ledger=None, *, views=None,
                         access_binding=None, archive_binding=None,
                         original_consumer, authority_consumer,
                         protected_projection, download):
    """Original saved scientific admission first; exact fresh copies second.

    A deployment must nominate the correction binding in a source-bound access
    registry. Missing nomination never enables permissive auto-discovery. No
    real public addition is hidden from the resulting audit or source closure.
    """
    admitted = original_consumer(root, registration_binding, ledger, views=None)
    if views is None:
        return admitted
    if access_binding is None:
        return original_consumer(root, registration_binding, ledger, views=views)
    access.need(isinstance(views, (tuple, list)) and len(views) == 2
                and all(isinstance(v, dict) for v in views), "ACTUAL_FRESH_PAIR")
    access.need(archive_binding is not None, "ORIGINAL_ARCHIVE_SOURCE")
    correction_raw = bound(root, access_binding); correction = json.loads(correction_raw)
    receipt = admitted["receipt"]
    access.need(correction["record_id"] == receipt["record_id"] and correction["doi"] == receipt["doi"], "REGISTERED_IDENTITY")
    manifest_binding = receipt["digest_manifest"]
    manifest = bound(root, manifest_binding); archive = bound(root, archive_binding)
    expected_archive = next(u for u in admitted["manifest"]["uploads"] if u["filename"] == "METHODS_NOTES.zip")
    access.need(archive_binding["sha256"] == expected_archive["sha256"], "ADMITTED_ARCHIVE_HASH")
    checked = access.require_pair(views[0], views[1], admitted["public_legacy"], admitted["public_native"],
        receipt=correction, manifest_bytes=manifest, archive_bytes=archive, download=download,
        authority_consumer=authority_consumer, protected_projection=protected_projection)
    access.need(bound(root, access_binding) == correction_raw
                and bound(root, manifest_binding) == manifest and bound(root, archive_binding) == archive, "FINAL_SOURCE_RACE")
    return {**admitted, "public_legacy": deepcopy(views[0]), "public_native": deepcopy(views[1]),
        "registered_public_views": {"legacy": deepcopy(admitted["public_legacy"]), "native": deepcopy(admitted["public_native"])},
        "prior_processing_audit": {"route": "EXACT_RECEIPT_BOUND_MANUSCRIPT_ACCESS_COPIES", "access_correction": checked,
                                   "correction_binding": deepcopy(access_binding)}}
