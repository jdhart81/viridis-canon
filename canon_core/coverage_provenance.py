"""Describe historical assessment provenance; never admit proof or a public claim.

The publication/claim gates and full catalog-preservation consumer remain the
sole admission checks. This header records which ledger supplied each cohort.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import re

STANDARD = "CATALOG_COVERAGE_PROVENANCE_1"
FIELDS = {"standard", "historical_snapshot", "current_snapshots", "source_prefix",
          "historical_record_ids", "historical_publication_entity_ids",
          "current_entities", "certifies"}
SNAPSHOT_FIELDS = {"name", "sha256"}
ENTITY_FIELDS = {"entity_id", "entity_type", "row_sha256", "snapshot_sha256"}
SHA = re.compile(r"[0-9a-f]{64}")


def require(condition, reason):
    if not condition:
        raise ValueError("HOLD_CATALOG_PROVENANCE_" + reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def equal(left, right):
    return encoded(left) == encoded(right)


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def _ids(rows, field):
    require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows), "ROW_TABLE")
    ids = [row.get(field) for row in rows]
    require(all(isinstance(value, str) and value for value in ids) and
            len(ids) == len(set(ids)), "UNIQUE_NONEMPTY_IDS")
    return sorted(ids)


def _new_entities(document):
    groups = document.get("methods_digests", [])
    require(isinstance(groups, list), "GROUP_TABLE")
    entities = []
    for group in groups:
        require(isinstance(group, dict) and group.get("certifies") is False, "NO_AGGREGATE_CERTIFICATION")
        entities.append({"entity_id": group.get("entity_id"), "entity_type": "METHODS_DIGEST_GROUP"})
        notes = group.get("notes")
        require(isinstance(notes, list) and notes, "NONEMPTY_NOTE_TABLE")
        for note in notes:
            require(isinstance(note, dict) and note.get("certifies") == "LISTED_NOTE_SCOPE_ONLY", "LISTED_SCOPES_ONLY")
            entities.append({"entity_id": note.get("entity_id"), "entity_type": "METHODS_DIGEST_NOTE"})
    _ids(entities, "entity_id")
    return sorted(entities, key=lambda row: row["entity_id"])


def validate_provenance(document, header, *, current_ledger_raw=None):
    """Validate the closed header, census and exact optionally supplied SSOT bytes.

    Without private SSOT input this is a public metadata consistency check only.
    A caller applying the update must also reconsume the default registrar and
    provide current_ledger_raw; a header is never a certificate or gate verdict.
    """
    require(isinstance(document, dict) and isinstance(header, dict) and set(header) == FIELDS, "CLOSED_HEADER")
    require(header["standard"] == STANDARD and header["certifies"] is False, "NONCERTIFYING_HEADER")
    require(isinstance(header["current_snapshots"], list) and header["current_snapshots"], "CURRENT_SNAPSHOT_TABLE")
    snapshots = [header["historical_snapshot"], *header["current_snapshots"]]
    for snapshot in snapshots:
        require(isinstance(snapshot, dict) and set(snapshot) == SNAPSHOT_FIELDS and
                isinstance(snapshot["name"], str) and snapshot["name"] and
                not any(token in snapshot["name"] for token in ("/", "\\", ":")) and
                isinstance(snapshot["sha256"], str) and SHA.fullmatch(snapshot["sha256"]) is not None,
                "CLOSED_NAMED_SNAPSHOT")
    current_by_sha = {snapshot["sha256"]: snapshot for snapshot in header["current_snapshots"]}
    require(len(current_by_sha) == len(header["current_snapshots"]) and
            len({snapshot["name"] for snapshot in header["current_snapshots"]}) == len(header["current_snapshots"]),
            "UNIQUE_CURRENT_SNAPSHOTS")
    require(header["source_prefix"] == "viridis-canon", "EXACT_SOURCE_PREFIX")
    records = document.get("records")
    publications = document.get("publications")
    require(equal(header["historical_record_ids"], _ids(records, "record_id")), "HISTORICAL_RECORD_MEMBERSHIP")
    require(equal(header["historical_publication_entity_ids"], _ids(publications, "entity_id")), "HISTORICAL_JOIN_MEMBERSHIP")
    require(all(isinstance(row.get("metadata"), dict) and
                isinstance(row["metadata"].get("verification_coverage"), dict) and
                row["metadata"]["verification_coverage"].get("ledger_sha256") == header["historical_snapshot"]["sha256"]
                for row in records), "HISTORICAL_RECORDED_HASH_CHANGED")
    expected = _new_entities(document)
    rows = header["current_entities"]
    require(isinstance(rows, list) and all(isinstance(row, dict) and set(row) == ENTITY_FIELDS and
                isinstance(row["row_sha256"], str) and SHA.fullmatch(row["row_sha256"]) is not None and
                isinstance(row["snapshot_sha256"], str) and row["snapshot_sha256"] in current_by_sha for row in rows),
            "CLOSED_CURRENT_ENTITIES")
    _ids(rows, "entity_id")
    require(equal(sorted([{k: row[k] for k in ("entity_id", "entity_type")} for row in rows], key=lambda row: row["entity_id"]), expected), "EXACT_CURRENT_COHORT")
    require(not (set(header["historical_publication_entity_ids"]) & {row["entity_id"] for row in rows}), "DISJOINT_COHORTS")
    if current_ledger_raw is not None:
        require(type(current_ledger_raw) is bytes and
                hashlib.sha256(current_ledger_raw).hexdigest() == header["current_snapshots"][-1]["sha256"], "CURRENT_SSOT_HASH_CHANGED")
        ledger = json.loads(current_ledger_raw)
        table = ledger.get("publication_entities")
        _ids(table, "id")
        index = {row["id"]: row for row in table}
        for row in rows:
            if row["snapshot_sha256"] != header["current_snapshots"][-1]["sha256"]:
                continue  # Earlier cohorts retain recorded historical assessment provenance.
            actual = index.get(row["entity_id"])
            require(isinstance(actual, dict) and actual.get("entity_type") == row["entity_type"] and
                    fingerprint(actual) == row["row_sha256"], "CURRENT_ROW_CHANGED:" + row["entity_id"])
            require(actual.get("publication_registration_status") == "PASS" and actual.get("registration_revalidated") is True and
                    actual.get("publication_binding_status") == "PUBLICATION_BOUND" and actual.get("enforcement_acceptable") is True and
                    equal(actual.get("reasons"), []) and equal(actual.get("publication_registration_reasons"), []),
                    "CURRENT_REGISTRATION_HOLD:" + row["entity_id"])
            if row["entity_type"] == "METHODS_DIGEST_GROUP":
                require(actual.get("status") == "SCOPED_DIGEST" and actual.get("certifies") is False and
                        actual.get("certificate_valid") is False, "CURRENT_AGGREGATE_CERTIFICATION")
            else:
                require(actual.get("status") == "CERTIFIED" and actual.get("certifies") == "LISTED_NOTE_SCOPE_ONLY" and
                        actual.get("certificate_valid") is True, "CURRENT_NOTE_SCOPE_HOLD")
    return deepcopy(header)


def require_append_only(prior, successor):
    require(isinstance(prior, dict) and isinstance(successor, dict) and set(prior) == set(successor) == FIELDS,
            "CLOSED_PRIOR_AND_SUCCESSOR")
    for field in FIELDS - {"current_snapshots", "current_entities"}:
        require(equal(prior[field], successor[field]), "PRIOR_FIELD_REWRITTEN:" + field)
    for field in ("current_snapshots", "current_entities"):
        require(isinstance(prior[field], list) and isinstance(successor[field], list) and
                len(successor[field]) >= len(prior[field]) and equal(prior[field], successor[field][:len(prior[field])]),
                "PRIOR_PROVENANCE_REWRITTEN:" + field)
    return True


def construct_provenance(document, current_ledger_raw, *, historical_name, current_name, prior_header=None):
    """Fresh new cohorts append provenance; earlier cohorts are never relabeled."""
    historical_hashes = {row.get("metadata", {}).get("verification_coverage", {}).get("ledger_sha256")
                         for row in document.get("records", [])}
    require(len(historical_hashes) == 1, "ONE_HISTORICAL_SNAPSHOT")
    ledger = json.loads(current_ledger_raw)
    rows = ledger.get("publication_entities")
    _ids(rows, "id")
    index = {row["id"]: row for row in rows}
    current_sha = hashlib.sha256(current_ledger_raw).hexdigest()
    expected = _new_entities(document)
    if prior_header is None:
        header = {"standard": STANDARD,
                  "historical_snapshot": {"name": historical_name, "sha256": next(iter(historical_hashes))},
                  "current_snapshots": [], "source_prefix": "viridis-canon",
                  "historical_record_ids": _ids(document["records"], "record_id"),
                  "historical_publication_entity_ids": _ids(document["publications"], "entity_id"),
                  "current_entities": [], "certifies": False}
    else:
        header = deepcopy(prior_header)
    old = {row["entity_id"]: row for row in header["current_entities"]}
    additions = [row for row in expected if row["entity_id"] not in old]
    require(set(old) <= {row["entity_id"] for row in expected}, "PRIOR_COHORT_REMOVED")
    if additions or prior_header is None:
        if current_sha not in {snapshot["sha256"] for snapshot in header["current_snapshots"]}:
            header["current_snapshots"].append({"name": current_name, "sha256": current_sha})
        require(header["current_snapshots"][-1]["sha256"] == current_sha, "NEW_COHORT_NOT_CURRENT_SNAPSHOT")
        for row in additions:
            require(row["entity_id"] in index, "CURRENT_ENTITY_MISSING")
            row["snapshot_sha256"] = current_sha
            row["row_sha256"] = fingerprint(index[row["entity_id"]])
        header["current_entities"].extend(additions)
    if prior_header is not None:
        require_append_only(prior_header, header)
    return validate_provenance(document, header, current_ledger_raw=current_ledger_raw)


def checked_historical_projection(document, expected_header, *, current_ledger_raw, prior_header=None):
    """Validate exactly one additive field, then call the old whole guard.

    No other field is removed or normalized; the complete historical rows and
    all unknown metadata remain visible to the unchanged preservation consumer.
    """
    require("coverage_provenance" in document and equal(document["coverage_provenance"], expected_header), "EXPECTED_HEADER_CHANGED")
    validate_provenance(document, expected_header, current_ledger_raw=current_ledger_raw)
    result = deepcopy(document)
    if prior_header is None:
        del result["coverage_provenance"]
    else:
        require_append_only(prior_header, expected_header)
        result["coverage_provenance"] = deepcopy(prior_header)
    return result


def audit_additive_update(before, after, expected_header, current_ledger_raw, whole_guard):
    """Type-exact preservation followed by the unchanged original whole guard."""
    projected = checked_historical_projection(after, expected_header, current_ledger_raw=current_ledger_raw,
                                             prior_header=before.get("coverage_provenance"))
    prior_groups = before.get("methods_digests", [])
    require(equal(prior_groups, after.get("methods_digests", [])[:len(prior_groups)]), "PRIOR_DIGEST_CONTENT_REWRITTEN")
    legacy_before = {k: v for k, v in before.items() if k not in {"catalog_digest", "methods_digests"}}
    legacy_after = {k: v for k, v in projected.items() if k not in {"catalog_digest", "methods_digests"}}
    require(equal(legacy_before, legacy_after), "EXISTING_FIELD_CHANGED")
    return whole_guard(before, projected, after["methods_digests"])
