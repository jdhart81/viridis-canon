"""Closed Methods Digest pointers, separate from source or aggregate admission.

The publication renderer derives these from the existing fresh registrar. This
catalog loader validates the pointer projection only; hashes are not proof.
One shared DOI contains independently scoped notes and certifies no aggregate.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

DISCLAIMER = "logical validity given the model, not empirical validation of its assumptions"
STANDARD = "PUBLIC_METHODS_DIGEST_POINTERS_1"
GROUP_FIELDS = {"entity_id", "record_id", "doi", "release_week", "title", "certifies",
                "disclaimer", "registration_receipt_sha256", "public_readback_sha256",
                "publication_binding_sha256", "notes"}
NOTE_FIELDS = {"entity_id", "run_id", "title", "claim_scope", "foundation_basis", "certifies",
               "disclaimer", "certificate_sha256", "publication_binding_sha256", "semantic_labels"}
LABEL_FIELDS = {"lean_theorem", "semantic_tier", "nonvacuity_label", "headline_eligible"}
TIERS = {"DEFINITIONAL", "ROUTINE", "SUBSTANTIVE", "UNCLASSIFIED", "DEPTH_NOT_ASSESSED"}
TIER_PRINT = {"UNCLASSIFIED": "UNCLASSIFIED (probe resource-limited)", "DEPTH_NOT_ASSESSED": "depth not yet assessed"}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_methods_digests(rows: list[dict]) -> list[dict]:
    """Reject admission labels, ambiguous identities and expanded note scope."""
    if not isinstance(rows, list):
        raise ValueError("Methods Digest pointer list required")
    seen_groups, seen_records, seen_notes = set(), set(), set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != GROUP_FIELDS or row["certifies"] is not False:
            raise ValueError("Methods Digest aggregate must be closed and uncertified")
        rid, week = row["record_id"], row["release_week"]
        if (not isinstance(rid, str) or re.fullmatch(r"[1-9][0-9]*", rid) is None
                or not isinstance(week, str) or re.fullmatch(r"[0-9]{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3])", week) is None
                or row["doi"] != "10.5281/zenodo." + rid
                or row["entity_id"] != "publication:methods-digest:" + week + ":" + rid):
            raise ValueError("Methods Digest DOI/week/group identity differs")
        if row["entity_id"] in seen_groups or rid in seen_records:
            raise ValueError("duplicate Methods Digest group or record")
        seen_groups.add(row["entity_id"]); seen_records.add(rid)
        if not _text(row["title"]) or row["disclaimer"] != DISCLAIMER:
            raise ValueError("Methods Digest title/disclaimer required")
        for key in ("registration_receipt_sha256", "public_readback_sha256", "publication_binding_sha256"):
            if not isinstance(row[key], str) or re.fullmatch(r"[0-9a-f]{64}", row[key]) is None:
                raise ValueError("Methods Digest evidence SHA-256 required")
        notes, runs = row["notes"], set()
        if not isinstance(notes, list) or not notes:
            raise ValueError("Methods Digest must list its individually scoped notes")
        for note in notes:
            if (not isinstance(note, dict) or set(note) != NOTE_FIELDS
                    or note["certifies"] != "LISTED_NOTE_SCOPE_ONLY"):
                raise ValueError("Methods Note cannot carry aggregate/source admission labels")
            run = note["run_id"]
            if (not isinstance(run, str) or re.fullmatch(r"Run-[0-9]{3,}", run) is None
                    or note["entity_id"] != "publication:methods-note:" + week + ":" + run
                    or run in runs or note["entity_id"] in seen_notes):
                raise ValueError("duplicate or foreign Methods Note identity")
            runs.add(run); seen_notes.add(note["entity_id"])
            if (not all(_text(note[key]) for key in ("title", "claim_scope"))
                    or note["disclaimer"] != DISCLAIMER
                    or note["foundation_basis"] not in {"INDEPENDENT", "THEOREM", "CONDITIONAL_PL_PD"}):
                raise ValueError("exact Methods Note scope/basis/disclaimer required")
            for key in ("certificate_sha256", "publication_binding_sha256"):
                if not isinstance(note[key], str) or re.fullmatch(r"[0-9a-f]{64}", note[key]) is None:
                    raise ValueError("Methods Note evidence SHA-256 required")
            labels, declarations = note["semantic_labels"], set()
            if not isinstance(labels, list) or not labels:
                raise ValueError("Methods Note semantic/nonvacuity labels required")
            for label in labels:
                if (not isinstance(label, dict) or set(label) != LABEL_FIELDS
                        or not all(_text(label[key]) for key in ("lean_theorem", "nonvacuity_label"))
                        or label["semantic_tier"] not in TIERS
                        or type(label["headline_eligible"]) is not bool
                        or label["lean_theorem"] in declarations):
                    raise ValueError("closed unique Methods Note claim labels required")
                if label["semantic_tier"] == "DEFINITIONAL" and label["headline_eligible"]:
                    raise ValueError("definitional Methods Note claim cannot be headline eligible")
                if label["nonvacuity_label"] == "certified; nonvacuity not demonstrated" and label["headline_eligible"]:
                    raise ValueError("undemonstrated nonvacuity cannot be headline eligible")
                declarations.add(label["lean_theorem"])
    return rows


def require_disjoint_publications(publications: list[dict], digests: list[dict]) -> None:
    """Shared note DOIs belong to one digest group, never generic joins."""
    ids = {row["entity_id"] for row in publications}
    digest_ids = {row["entity_id"] for row in digests}
    digest_ids.update(note["entity_id"] for row in digests for note in row["notes"])
    if ids & digest_ids or {row["record_id"] for row in publications} & {row["record_id"] for row in digests}:
        raise ValueError("Methods Digest shared DOI/identity cannot also be a generic publication pointer")


def load_methods_digest_joins(root: Path, config: dict) -> list[dict]:
    source = config.get("methods_digest_joins")
    if source is None:
        return []
    if not isinstance(source, dict) or set(source) != {"path", "sha256"} or not _text(source["path"]):
        raise ValueError("exact Methods Digest join path and SHA-256 required")
    relative = Path(source["path"]); root = root.resolve()
    path = root / relative
    if (relative.is_absolute() or ".." in relative.parts
            or any(p.is_symlink() for p in (path, *path.parents))):
        raise ValueError("Methods Digest join must be a non-symlink repository file")
    path = path.resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("Methods Digest join outside repository")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source["sha256"]:
        raise ValueError("Methods Digest join source SHA-256 mismatch")
    packet = json.loads(raw)
    if not isinstance(packet, dict) or set(packet) != {"standard", "methods_digests"} or packet["standard"] != STANDARD:
        raise ValueError("unsupported Methods Digest pointer schema")
    return validate_methods_digests(packet["methods_digests"])
