"""Private descriptive W42 index; no legacy queue or executable admission.

The current legacy consumers deliberately HOLD these uncertified artifacts.
This additive index retains that HOLD and separately scoped predecessor evidence.
"""
from __future__ import annotations
import copy
from pathlib import Path
import root_scope
import postpublication_sync as sync
import w42_receipt as receipt
from deadline import Budget

STANDARD = "VOS-UNCERTIFIED-DESCRIPTIVE-PUBLICATION-INDEX-1"


def read_index(root, index_binding):
    value = receipt.object_at(root, index_binding)
    receipt.need(value.get("standard") == STANDARD and value.get("certifies") is False
        and "certificate" in value and value["certificate"] is None and value.get("runtime_admission") is False
        and value.get("automatic_adoption") is False and value.get("private_evidence_only") is True
        and value.get("legacy_consumer_status") == "HOLD_UNCERTIFIED_ARTIFACT", "HOLD_DESCRIPTIVE_OS_AUTHORITY")
    rows = value.get("records")
    receipt.need(isinstance(rows, list) and rows, "HOLD_DESCRIPTIVE_OS_RECORDS")
    seen = set()
    for row in rows:
        receipt.need(isinstance(row, dict) and isinstance(row.get("run_id"), str) and row["run_id"] not in seen
            and row.get("status") == "UNCERTIFIED" and row.get("certificate_valid") is False
            and row.get("certifies") is False and "certificate" in row and row["certificate"] is None
            and "certificate_sha256" in row and row["certificate_sha256"] is None
            and row.get("runtime_admission") is False and row.get("artifact_label") == receipt.ARTIFACT_LABEL,
            "HOLD_DESCRIPTIVE_OS_CURRENT_ARTIFACT_TRUTH")
        seen.add(row["run_id"])
        evidence = row.get("statement_certificate_evidence")
        receipt.need(isinstance(evidence, dict) and evidence.get("scope") == receipt.STATEMENT_SCOPE
            and evidence.get("certifies_current_artifact") is False and evidence.get("certificate_valid") is True,
            "HOLD_DESCRIPTIVE_OS_SEPARATE_STATEMENT_SCOPE")
    return value


def reconcile(root, canon_receipt, publication_receipt, route_binding, *, budget=None):
    budget = budget or Budget(); budget.require_remaining()
    root = Path(root).resolve(strict=True)
    route_path = sync.regular(route_binding, root)
    route = sync.object_file(route_path)
    scope = root_scope.load(root, route.get("owner_approval"), require_canon=True)
    publication = receipt.binding(root, publication_receipt)
    receipt.need(route.get("publication_receipt") == publication, "HOLD_DESCRIPTIVE_OS_PUBLICATION_BINDING")
    manifest = receipt.object_at(root, route.get("canon_payload_manifest"))
    intake = root_scope.validate_w42_mapping(root, scope, manifest)
    receipt.need(intake["publication"] == publication, "HOLD_DESCRIPTIVE_OS_INTAKE_BINDING")
    canon_binding = receipt.binding(root, canon_receipt)
    kind, dois = sync.publication_dois(receipt.object_at(root, canon_binding))
    receipt.need(kind == "lockstep" and dois == {intake["doi"]}, "HOLD_DESCRIPTIVE_OS_CANON_CLOSURE")
    by_run = {row["run_id"]: row for row in manifest["publication_mappings"][0]["children"]}
    rows = []
    for actual in intake["children"]:
        row = copy.deepcopy(actual)
        mapping = by_run[actual["run_id"]]
        row.update(canon_record_id=mapping["canon_record_id"], backing_doi=mapping["backing_doi"],
                   mapped_source={"path": mapping["source_path"], "sha256": mapping["source_sha256"]})
        rows.append(row)
    value = {"standard": STANDARD, "certifies": False, "certificate": None, "runtime_admission": False,
        "automatic_adoption": False, "private_evidence_only": True,
        "legacy_consumer_status": "HOLD_UNCERTIFIED_ARTIFACT", "publication": publication,
        "canon_receipt": canon_binding, "route_binding": receipt.binding(root, route_path),
        "source_exit": intake["source_exit"], "intake_sha256": receipt.digest(receipt.encoded(intake)), "records": rows}
    identity = route["publication_receipt"]["sha256"] + "-" + sync.file_hash(route_path)
    path = root / "ViridisOS/data/approved_release_sync" / (identity + ".json")
    # Current code is deliberately unactivatable. A separate installed genuine
    # host integration must replace this reviewed interlock before any write.
    root_scope.require_mutation_authority(scope)
    budget.require_remaining()
    from w42_after_source_session import immutable_json
    immutable_json(path, value)
    index_binding = receipt.binding(root, path)
    observed = read_index(root, index_binding)
    receipt.need(observed == value, "HOLD_DESCRIPTIVE_OS_EXACT_READBACK")
    budget.require_remaining()
    return {"status": "DESCRIPTIVE_OS_INDEX_READBACK_VERIFIED", "certifies": False, "runtime_admission": False,
        "automatic_adoption": False, "certificate": None, "readback_verified": True,
        "legacy_consumer_status": "HOLD_UNCERTIFIED_ARTIFACT", "record_count": len(rows),
        "reader_proof": {"reader": "descriptive_os.read_index", "source_sha256": sync.file_hash(Path(__file__)),
                         "artifact_sha256": index_binding["sha256"], "index": index_binding}}
