"""Render a separate digest pointer population through the unchanged registrar.

This adapter supplies no proof or acceptance rule. Every group is consumed by
the default receipt-backed registrar before its exact current SSOT rows and
bound note scopes are projected. A collection never enters Canon entries.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

from canon_core.methods_digests import DISCLAIMER, validate_methods_digests

GROUP_ROUTE = "METHODS_DIGEST_GROUP_V1"
NOTE_ROUTE = "METHODS_DIGEST_NOTE_V1"
ROUTES = {GROUP_ROUTE, NOTE_ROUTE}


def _registrar(root: Path):
    module = importlib.import_module("methods_digest_registration")
    expected = Path(__file__).resolve().parents[1] / "00_lab_infrastructure/gates/methods_digest_registration.py"
    actual = Path(module.__file__).resolve()
    installed = root.resolve(strict=True) / "RESEARCH_PIPELINE_v2/verification_coverage_gates/methods_digest_registration.py"
    if actual not in {expected, installed} or actual.read_bytes() != expected.read_bytes():
        raise ValueError("Methods Digest registrar came from a different checkout")
    return module


def _title(root: Path, note: dict) -> str:
    folder = Path(note["path"]).resolve(strict=True)
    binding = note["metadata_binding"]
    name = binding["filename"]
    if Path(name).name != name or not folder.is_relative_to(root.resolve(strict=True)):
        raise ValueError("foreign Methods Note metadata")
    path = folder / name
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Methods Note metadata is a symlink")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != binding["sha256"]:
        raise ValueError("Methods Note metadata changed during rendering")
    value = json.loads(raw); metadata = value.get("metadata", value)
    title = metadata["title"]
    if not isinstance(title, str) or not title.strip():
        raise ValueError("bound Methods Note title required")
    return title


def registered_digest_pointers(root: Path, ledger: dict) -> tuple[list[dict], dict[str, list[str]]]:
    """Freshly consume whole cohorts; failures retain a held diagnostic per row."""
    selected = [row for row in ledger.get("publication_entities", []) if row.get("registration_route") in ROUTES]
    if not selected:
        return [], {}
    registrar = _registrar(root)
    pointers, failures, used = [], {}, set()
    for group in selected:
        if group["registration_route"] != GROUP_ROUTE:
            continue
        binding = group.get("registration_receipt")
        cohort = [row for row in selected if row.get("registration_receipt") == binding]
        try:
            # Default consumer rechecks proofs, parity, current scope, binding,
            # native/legacy readback and all six public bytes. No cached PASS.
            current = registrar.require_registration(root, binding, ledger)
            expected = registrar.entity_rows(root, binding, ledger, consume=lambda *_: current)
            actual = {row["id"]: row for row in cohort}
            if len(actual) != len(cohort) or len(expected) != len(cohort) or actual != {row["id"]: row for row in expected}:
                raise ValueError("Methods Digest current SSOT cohort differs from fresh registration")
            receipt, manifest = current["receipt"], current["manifest"]
            notes = {note["run_id"]: note for note in manifest["notes"]}
            children = []
            for child in receipt["children"]:
                note = notes[child["run_id"]]
                # Preserve every printed claim field, including exact Lean
                # binders, ambient premises and model-fidelity tags.
                scope = json.dumps(note["statement_scope"], indent=2, ensure_ascii=False, sort_keys=True)
                children.append({"entity_id": child["id"], "run_id": child["run_id"],
                    "title": _title(root, note), "claim_scope": scope,
                    "foundation_basis": note["foundation_basis"],
                    "certifies": "LISTED_NOTE_SCOPE_ONLY", "disclaimer": DISCLAIMER,
                    "certificate_sha256": child["certificate"]["sha256"],
                    "publication_binding_sha256": child["publication_binding"]["sha256"],
                    "semantic_labels": deepcopy(note["claim_table"])})
            pointer = {"entity_id": group["id"], "record_id": receipt["record_id"], "doi": receipt["doi"],
                "release_week": receipt["release_week"], "title": current["public_legacy"]["metadata"]["title"],
                "certifies": False, "disclaimer": DISCLAIMER,
                "registration_receipt_sha256": binding["sha256"],
                "public_readback_sha256": receipt["public_evidence"]["sha256"],
                "publication_binding_sha256": receipt["digest_publication_binding"]["sha256"], "notes": children}
            validate_methods_digests([pointer])
            pointers.append(pointer)
        except Exception as exc:
            for row in cohort:
                failures[row["id"]] = [type(exc).__name__ + ": " + str(exc)]
        used.update(row["id"] for row in cohort)
    for row in selected:
        if row["id"] not in used:
            failures[row["id"]] = ["orphaned Methods Digest note registration"]
    validate_methods_digests(pointers)
    return pointers, failures
