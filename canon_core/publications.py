"""Explicit public DOI joins, separate from admission of repository sources.

These are publication pointers. They cannot confer verified/spine eligibility on
the older repository modules or replace current certificate/claim gates.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def load_publication_joins(root: Path, config: dict) -> list[dict]:
    value = config.get("publication_joins")
    if value is None:
        return []
    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise ValueError("exact publication join path and SHA-256 required")
    relative = Path(value["path"])
    root = root.resolve()
    path = root / relative
    if relative.is_absolute() or ".." in relative.parts or path.is_symlink():
        raise ValueError("publication join must be a non-symlink repository file")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise ValueError("publication join outside repository")
    raw = resolved.read_bytes()
    if hashlib.sha256(raw).hexdigest() != value["sha256"]:
        raise ValueError("publication join source SHA-256 mismatch")
    packet = json.loads(raw)
    if not isinstance(packet, dict) or set(packet) != {"standard", "publications"} or packet["standard"] != "PUBLIC_SCOPED_PUBLICATION_POINTERS_1":
        raise ValueError("unsupported publication pointer schema")
    rows = packet["publications"]
    if not isinstance(rows, list):
        raise ValueError("publication pointer list required")
    required = {"entity_id", "record_id", "doi", "title", "claim_scope", "disclaimer", "public_readback_sha256", "publication_binding_sha256", "certificate_sha256"}
    identities = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != required:
            raise ValueError("publication pointers cannot carry source admission labels")
        if any(not isinstance(row[k], str) or not row[k] for k in required):
            raise ValueError("complete explicit publication pointer required")
        rid = row["record_id"]
        if re.fullmatch(r"[1-9][0-9]*", rid) is None or row["doi"] != "10.5281/zenodo." + rid:
            raise ValueError("publication DOI/record identity mismatch")
        if row["entity_id"] in identities or rid in identities:
            raise ValueError("duplicate publication identity")
        identities.update({row["entity_id"], rid})
        for key in ("public_readback_sha256", "publication_binding_sha256", "certificate_sha256"):
            if re.fullmatch(r"[0-9a-f]{64}", row[key]) is None:
                raise ValueError("publication evidence SHA-256 required")
        if row["disclaimer"] != "logical validity given the model, not empirical validation of its assumptions":
            raise ValueError("publication scope disclaimer differs")
    return rows
