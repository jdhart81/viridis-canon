"""Exact manuscript-access joins; these confer no scientific admission."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import quote

ACCESS_FIELDS = {"pdf_url", "pdf_access"}
LINKED = "LINKED_FROM_HASH_BOUND_PUBLIC_READBACK"
HOLD = "HOLD_UNRESOLVED_MAPPING"
HEX = re.compile(r"[a-f0-9]{64}")


def validate_access_fields(row: dict, record_id: str, run_id: str = "") -> None:
    present = ACCESS_FIELDS.intersection(row)
    if not present:
        return
    if present != ACCESS_FIELDS:
        raise ValueError("PDF URL and its access evidence must appear together")
    access = row["pdf_access"]
    if not isinstance(access, dict) or access.get("certifies") is not False:
        raise ValueError("PDF access cannot certify scientific claims")
    if access.get("status") == HOLD:
        if set(access) != {"status", "certifies", "reason"} or row["pdf_url"] is not None or not access["reason"]:
            raise ValueError("unresolved manuscript access must remain an explicit HOLD")
        return
    required = {"status", "certifies", "filename", "sha256", "md5", "bytes", "index_row_sha256", "verification_receipt_sha256"}
    if set(access) != required or access["status"] != LINKED:
        raise ValueError("closed manuscript access evidence required")
    filename = access["filename"]
    if not isinstance(filename, str) or Path(filename).name != filename or not filename.lower().endswith(".pdf"):
        raise ValueError("direct top-level manuscript PDF required")
    expected = "https://zenodo.org/records/" + record_id + "/files/" + quote(filename, safe="")
    if row["pdf_url"] != expected:
        raise ValueError("PDF URL differs from the exact publication record and filename")
    if any(not isinstance(access[key], str) or HEX.fullmatch(access[key]) is None for key in ("sha256", "index_row_sha256")):
        raise ValueError("manuscript and index-row SHA-256 required")
    if not isinstance(access["md5"], str) or re.fullmatch(r"[a-f0-9]{32}", access["md5"]) is None or type(access["bytes"]) is not int or access["bytes"] <= 0:
        raise ValueError("manuscript MD5 and positive byte size required")
    receipts = access["verification_receipt_sha256"]
    if not isinstance(receipts, list) or not receipts or any(not isinstance(value, str) or HEX.fullmatch(value) is None for value in receipts):
        raise ValueError("public verification receipt hashes required")


def load_mapping(root: Path, config: dict) -> tuple[dict | None, str]:
    binding = config.get("manuscript_access")
    if binding is None:
        return None, ""
    if not isinstance(binding, dict) or set(binding) != {"path", "sha256"}:
        raise ValueError("exact manuscript access path and SHA-256 required")
    relative = Path(binding["path"])
    root = root.resolve()
    path = root / relative
    if relative.is_absolute() or ".." in relative.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("manuscript mapping must be a regular repository file")
    path = path.resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("manuscript mapping outside repository")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != binding["sha256"]:
        raise ValueError("manuscript mapping SHA-256 differs")
    mapping = json.loads(raw)
    if (not isinstance(mapping, dict) or mapping.get("schema") != "VRS-MANUSCRIPT-ACCESS-MAPPING-1"
            or mapping.get("certifies") is not False
            or any(not isinstance(mapping.get(key), str) or HEX.fullmatch(mapping[key]) is None
                   for key in ("source_index_sha256", "correction_overlay_sha256"))
            or not isinstance(mapping.get("bindings"), list) or not isinstance(mapping.get("unresolved"), list)):
        raise ValueError("hash-bound access-only manuscript mapping required")
    return mapping, digest


def project_access(publications: list[dict], digests: list[dict], mapping: dict, mapping_sha256: str):
    """Join explicit paper identities only; never attach access to Lean records."""
    publications, digests = copy.deepcopy(publications), copy.deepcopy(digests)
    by_entity = {}
    for binding in mapping["bindings"]:
        entity = binding["entity_id"]
        if entity in by_entity:
            raise ValueError("ambiguous manuscript access binding")
        by_entity[entity] = binding
    joined = 0; unresolved = copy.deepcopy(mapping["unresolved"]); consumed = set()

    def attach(row, record_id, run_id=""):
        nonlocal joined
        entity = row["entity_id"]
        binding = by_entity.get(entity)
        if binding is None:
            row.update(pdf_url=None, pdf_access={"status": HOLD, "certifies": False,
                       "reason": "no exact entity/record/Run manuscript binding"})
            unresolved.append({"entity_id": entity, "record_id": record_id, "run_id": run_id, "status": HOLD})
            return
        if binding["record_id"] != record_id or binding.get("run_id", "") != run_id or binding["doi"] != "10.5281/zenodo." + record_id:
            raise ValueError("manuscript mapping entity/record/Run identity differs")
        if run_id and (binding.get("archive_member") != "notes/" + run_id + "/paper.pdf"
                       or binding.get("selection_basis") != "EXACT_DIGEST_RUN_ARCHIVE_MEMBER"):
            raise ValueError("Methods Note requires its own exact Run/archive-member binding")
        if not run_id and binding.get("selection_basis") != "EXPLICIT_STANDALONE_PUBLICATION_RECORD":
            raise ValueError("standalone publication needs an explicit paper-record mapping")
        row.update(pdf_url=binding["pdf_url"], pdf_access={"status": LINKED, "certifies": False,
                   **{key: binding[key] for key in ("filename", "sha256", "md5", "bytes", "index_row_sha256", "verification_receipt_sha256")}})
        validate_access_fields(row, record_id, run_id)
        joined += 1; consumed.add(entity)

    for publication in publications:
        attach(publication, publication["record_id"])
    for digest in digests:
        for note in digest["notes"]:
            attach(note, digest["record_id"], note["run_id"])
    if consumed != set(by_entity):
        raise ValueError("manuscript mapping contains unknown or source-only entities")
    report = {"status": "HOLD_UNRESOLVED_MANUSCRIPTS" if unresolved else "MAPPED_PUBLIC_PAPER_ENTRIES",
              "certifies": False, "mapping_sha256": mapping_sha256,
              "source_index_sha256": mapping["source_index_sha256"],
              "correction_overlay_sha256": mapping["correction_overlay_sha256"],
              "linked_paper_entries": joined, "unresolved": unresolved,
              "scope": "explicit_publications_and_individual_methods_notes_only"}
    return publications, digests, report
