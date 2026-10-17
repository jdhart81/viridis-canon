"""Prepare and conditionally apply the seven authorized Phase 5 RDM repairs.

This module has no network transport or executable mutation CLI. A caller must
provide the reviewed Bearer-header transport, its hash-bound installation
receipt, and the exact approved plan. Publication outcomes are never retried.
"""
from __future__ import annotations

import copy
from datetime import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
import re


COPYRIGHTS = {
    "21855705": "Copyright © 2026 Justin D. Hart and Viridis Research",
    "23329645": "Copyright © 2026 Justin D. Hart and Viridis Research",
    "23329732": "Copyright © 2026 Justin D. Hart and Viridis Research",
    "23329742": "Copyright © 2026 Justin D. Hart and Viridis LLC",
    "23329754": "Copyright © 2026 Justin D. Hart and Viridis Research",
    "23329771": "Copyright © 2026 Justin D. Hart and Viridis Research",
}
RDM = "https://zenodo.org/api/records/"
GATES = Path(__file__).resolve().parents[1] / "00_lab_infrastructure/gates"
if str(GATES) not in sys.path:
    sys.path.insert(0, str(GATES))
from own_record_comparison import prior_protected_projection
UNMT_ENTITY_IDS = (
    "file:_ZENODO_DEPOSITS/2026-07-12_UNMT_standalone/UniversalNucleationMetaTheorem.lean",
    "file:new leans/2026-07-10_aristotle_UNMT_forge/UniversalNucleationMetaTheorem.lean",
)
STANDARD_BANNER_SHA256 = "5832b3a98f51ce9fddf3ebf830669da328a908891452e02da1704cf8eeb31428"


class RepairHold(RuntimeError):
    pass


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def full_diff(before, after, path=""):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            escaped = key.replace("~", "~0").replace("/", "~1")
            child = path + "/" + escaped
            if key not in before or key not in after:
                result.append({"path": child, "before": before.get(key), "after": after.get(key)})
            else:
                result.extend(full_diff(before[key], after[key], child))
        return result
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def first_banner(source_record):
    description = source_record.get("metadata", {}).get("description", "")
    match = re.search(r"<p\b[^>]*>.*?</p>", description, flags=re.S)
    if not match or "UNCERTIFIED — no hash-bound Viridis Comparator certificate" not in match.group(0):
        raise RepairHold("standard source banner missing")
    return match.group(0)


def protected_diff(before, after):
    return full_diff(prior_protected_projection(before, representation="NATIVE"),
                     prior_protected_projection(after, representation="NATIVE"))


def _phase_timestamp(value):
    # RDM uses both ISO T and SQL-style space separators for edit timestamps.
    if not isinstance(value, str) or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(?:[.][0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})", value) is None:
        raise RepairHold("edit phase timestamp requires an explicit timezone")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise RepairHold("invalid edit phase timestamp") from None


def normalized_edit_draft(before, draft):
    """Project one same-record published edit onto its public protected baseline.

    Only the observed edit-phase signature and closed, identity-derived URLs
    obtain these transformations. Unknown fields and unknown links stay exact.
    This function never supplies an update payload or changes public comparison.
    """
    if (not isinstance(before, dict) or not isinstance(draft, dict)
            or any(not isinstance(row.get("parent"), dict) or not isinstance(row.get("pids"), dict)
                   or not isinstance(row["pids"].get("doi"), dict) for row in (before, draft))):
        raise RepairHold("native published and edit identity objects required")
    record_id = before.get("id")
    parent_id = before["parent"].get("id")
    if (not isinstance(record_id, str) or re.fullmatch(r"[1-9][0-9]*", record_id) is None
            or not isinstance(parent_id, str) or re.fullmatch(r"[1-9][0-9]*", parent_id) is None
            or draft.get("id") != record_id or draft.get("parent", {}).get("id") != parent_id
            or before.get("status") != "published" or before.get("is_draft") is not False
            or before.get("is_published") is not True or draft.get("status") != "published"
            or draft.get("is_draft") is not True or draft.get("is_published") is not True
            or before.get("pids", {}).get("doi", {}).get("identifier") != "10.5281/zenodo." + record_id
            or draft.get("pids") != before.get("pids")):
        raise RepairHold("same published record edit phase and PID identity required")
    public_url = RDM + record_id
    public_html = "https://zenodo.org/records/" + record_id
    original_links, draft_links = before.get("links"), draft.get("links")
    if (not isinstance(original_links, dict) or not isinstance(draft_links, dict)
            or original_links.get("self") != public_url
            or original_links.get("self_html") != public_html
            or draft_links.get("self") != public_url + "/draft"
            or draft_links.get("self_html") != "https://zenodo.org/uploads/" + record_id):
        raise RepairHold("same record edit navigation identity required")
    value = copy.deepcopy(draft)
    value["is_draft"] = False
    links = value["links"]
    links["self"], links["self_html"] = public_url, public_html
    # Public-only navigation can be omitted by an edit representation. A
    # different URL or an unrecognized link is never discarded or reconstructed.
    public_only = {"draft": public_url + "/draft", "latest": public_url + "/versions/latest",
                   "latest_html": public_html + "/latest", "parent": RDM + parent_id,
                   "parent_html": "https://zenodo.org/records/" + parent_id,
                   "self_doi_html": "https://zenodo.org/doi/10.5281/zenodo." + record_id}
    for key, expected in public_only.items():
        if original_links.get(key) == expected and key not in links:
            links[key] = expected
    draft_only = {"publish": public_url + "/draft/actions/publish", "record": public_url,
                  "record_html": public_html, "review": public_url + "/draft/review"}
    for key, expected in draft_only.items():
        if key not in original_links and links.get(key) == expected:
            links.pop(key)
    if (original_links.get("files") == public_url + "/files"
            and links.get("files") == public_url + "/draft/files"):
        links["files"] = original_links["files"]
    created, updated = _phase_timestamp(draft.get("created")), _phase_timestamp(draft.get("updated"))
    old_created, old_updated = _phase_timestamp(before.get("created")), _phase_timestamp(before.get("updated"))
    if not old_created <= old_updated <= created <= updated:
        raise RepairHold("edit creation timestamp is outside the public-to-draft observation order")
    value["created"] = before["created"]
    if "expires_at" not in before and "expires_at" in value:
        if _phase_timestamp(value["expires_at"]) < old_created:
            raise RepairHold("edit expiry precedes the published record")
        value.pop("expires_at")
    if (before.get("deletion_status") == {"is_deleted": False, "status": "P"}
            and "deletion_status" not in value):
        value["deletion_status"] = copy.deepcopy(before["deletion_status"])
    original_versions, versions = before.get("versions", {}), value.get("versions", {})
    if (isinstance(original_versions, dict) and isinstance(versions, dict)
            and versions.get("is_latest_draft") is True
            and original_versions.get("is_latest_draft", False) is False):
        if "is_latest_draft" in original_versions:
            versions["is_latest_draft"] = original_versions["is_latest_draft"]
        else:
            versions.pop("is_latest_draft")
    original_entries = before.get("files", {}).get("entries", {})
    entries = value.get("files", {}).get("entries", {})
    if isinstance(original_entries, dict) and isinstance(entries, dict):
        from urllib.parse import quote
        for name, row in entries.items():
            if not isinstance(row, dict) or not isinstance(original_entries.get(name), dict):
                continue
            old_links = original_entries[name].get("links")
            file_url = public_url + "/files/" + quote(name, safe="")
            expected_links = {"self": file_url, "content": file_url + "/content",
                              "container": file_url + "/container"}
            if (not isinstance(old_links, dict) or "self" not in old_links
                    or any(key not in expected_links or expected_links[key] != url for key, url in old_links.items())):
                continue
            if "links" not in row:
                row["links"] = copy.deepcopy(old_links)
                continue
            file_links = row["links"]
            if not isinstance(file_links, dict):
                continue
            draft_file_url = public_url + "/draft/files/" + quote(name, safe="")
            if ("commit" not in old_links and file_links.get("self") == draft_file_url
                    and file_links.get("commit") == draft_file_url + "/commit"):
                file_links.pop("commit")
            for key, original in old_links.items():
                if file_links.get(key) == original.replace(public_url + "/files/", public_url + "/draft/files/", 1):
                    file_links[key] = original
    return value


def draft_against_public(before, draft):
    return protected_diff(before, normalized_edit_draft(before, draft))


def unmt_ledger(expected_sha256):
    root = os.environ.get("VIRIDIS_CORE_ROOT")
    if not root or re.fullmatch(r"[0-9a-f]{64}", str(expected_sha256)) is None:
        raise RepairHold("UNMT ledger root and expected sha256 required")
    path = Path(root) / "RESEARCH_PIPELINE_v2/corpus_ledger.json"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RepairHold("UNMT corpus ledger hash differs")
    ledger = json.loads(raw)
    rows = [row for row in ledger.get("file_entities", []) if row.get("id") in UNMT_ENTITY_IDS]
    if sorted(row["id"] for row in rows) != sorted(UNMT_ENTITY_IDS):
        raise RepairHold("UNMT exact ledger entities missing or duplicated")
    if any(row.get("certificate_valid") is not False or row.get("certificate") is not None for row in rows):
        raise RepairHold("UNMT ledger has a certificate or ambiguous certificate status")
    return {"sha256": expected_sha256, "selected_rows": rows}


def make_plan(before, record_id, field, value, *, verified_source, certificate_valid=None,
              expected_ledger_sha256=None):
    record_id = str(record_id)
    if str(before.get("id")) != record_id or "revision_id" not in before:
        raise RepairHold("native RDM baseline and exact record identity required")
    ledger_binding = None
    if field == "copyright":
        if COPYRIGHTS.get(record_id) != value:
            raise RepairHold("copyright repair differs from A4 authorization")
        if before.get("metadata", {}).get("copyright") not in (None, "", value):
            raise RepairHold("existing copyright differs from authorized source")
    elif field == "description":
        if record_id != "23329823" or certificate_valid is True:
            raise RepairHold("UNMT repair requires absence of a valid certificate")
        ledger_binding = unmt_ledger(expected_ledger_sha256)
        banner = verified_source.get("banner")
        if (not isinstance(banner, str) or hashlib.sha256(banner.encode()).hexdigest() != STANDARD_BANNER_SHA256
                or value != banner + before["metadata"]["description"]):
            raise RepairHold("description may only prepend the exact source banner")
    else:
        raise RepairHold("unapproved metadata field")
    if re.fullmatch(r"[0-9a-f]{64}", str(verified_source.get("sha256"))) is None:
        raise RepairHold("hash-bound verified source required")
    after = copy.deepcopy(before)
    after["metadata"][field] = value
    changes = protected_diff(before, after)
    if [row["path"] for row in changes] != ["/metadata/" + field]:
        raise RepairHold("planned protected RDM diff must be exactly the authorized field")
    return {"state": "PREPARED_AWAITING_REVIEWED_INSTALLATION", "record_id": record_id,
            "authority": "A4", "field": field, "verified_source": copy.deepcopy(verified_source),
            "certificate_valid": certificate_valid, "ledger_binding": ledger_binding,
            "before": copy.deepcopy(before), "planned_after": after, "planned_diff": changes,
            "before_sha256": canonical_hash(before), "planned_after_sha256": canonical_hash(after),
            "external_mutation": False}


def require_installed_transport(receipt, installed_path, expected_receipt_sha256):
    raw = Path(receipt).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_receipt_sha256:
        raise RepairHold("installation receipt hash mismatch")
    value = json.loads(raw)
    required = value.get("independent_review_merged") is True and value.get("ci_green") is True
    source_hash = value.get("merged_blob_sha256")
    actual_hash = hashlib.sha256(Path(installed_path).read_bytes()).hexdigest()
    if not required or source_hash != actual_hash or value.get("installed_sha256") != actual_hash:
        raise RepairHold("reviewed Phase 2 transport installation is not proven")
    if re.fullmatch(r"[0-9a-f]{40}", value.get("merged_commit", "")) is None:
        raise RepairHold("merged source commit missing")


def apply_plan(client, plan, receipt_path, *, installation_receipt, installed_transport,
               expected_installation_receipt_sha256, expected_plan_sha256, sanitize,
               verify_datacite=None, rehearse=False):
    """Use only an installed reviewed transport; retain uncertainty on failure."""
    require_installed_transport(installation_receipt, installed_transport, expected_installation_receipt_sha256)
    if canonical_hash(plan) != expected_plan_sha256 or plan.get("authority") != "A4":
        raise RepairHold("approved plan binding differs")
    try:
        reconstructed = make_plan(plan["before"], plan["record_id"], plan["field"],
                                  plan["planned_after"]["metadata"][plan["field"]],
                                  verified_source=plan["verified_source"],
                                  certificate_valid=plan.get("certificate_valid"),
                                  expected_ledger_sha256=(plan.get("ledger_binding") or {}).get("sha256"))
    except Exception:
        raise RepairHold("plan does not satisfy the A4 record, field and value authorization") from None
    if reconstructed != plan:
        raise RepairHold("plan structure or full RDM diff exceeds the A4 authorization")
    field = plan["field"]
    allowed_path = "/metadata/" + field
    if rehearse:
        engine = os.environ.get("VIRIDIS_ENGINE_ROOT")
        if not engine or not Path(receipt_path).resolve().is_relative_to(Path(engine).resolve(strict=True) / "rehearsals"):
            raise RepairHold("repair rehearsal receipts must remain in ENGINE/rehearsals/<UTC>")
    try:
        with Path(receipt_path).open("x", encoding="utf-8") as stream:
            stream.write('{"state":"REPAIR_ATTEMPT_RESERVED"}\n')
    except FileExistsError:
        raise RepairHold("exclusive new receipt path required") from None
    record_url = RDM + plan["record_id"]
    receipt = {"state": "CHECKING_CURRENT_BASELINE", "record_id": plan["record_id"],
               "plan_sha256": expected_plan_sha256, "external_mutation": False}

    def save():
        path = Path(receipt_path)
        serialized = sanitize(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)) + "\n"
        if len(serialized.encode()) > 1024 * 1024:
            raise RepairHold("receipt exceeds one MiB limit")
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(serialized, encoding="utf-8")
        temp.replace(path)

    current = client("GET", record_url, rdm=True)
    if protected_diff(plan["before"], current):
        changes = protected_diff(plan["planned_after"], current)
        if not changes:
            receipt.update(state="ALREADY_APPLIED_PENDING_REQUIRED_READBACK", after=current)
            save()
            if field == "copyright":
                try:
                    confirmed = verify_datacite is not None and verify_datacite(plan["record_id"], current["metadata"][field]) is True
                except Exception:
                    confirmed = False
                if not confirmed:
                    receipt["state"] = "HOLD_ALREADY_APPLIED_DATACITE_READBACK_REQUIRED"
                    save()
                    raise RepairHold("existing RDM repair still requires exact DataCite InC rights readback")
            receipt["state"] = "ALREADY_APPLIED_NO_MUTATION"
            save()
            return receipt
        raise RepairHold("current RDM baseline drifted; rebuild and review the plan")
    receipt.update(state="BEFORE_OPENING_EDIT_DRAFT", before=current)
    save()
    draft_opened = False
    publish_requested = False
    try:
        if plan.get("ledger_binding") is not None and unmt_ledger(plan["ledger_binding"]["sha256"]) != plan["ledger_binding"]:
            raise RepairHold("UNMT selected ledger rows drifted before opening draft")
        receipt.update(state="OPEN_EDIT_DRAFT_REQUESTED", external_mutation=True)
        save()
        draft = client("POST", record_url + "/draft", b"{}", rdm=True)
        draft_opened = True
        receipt["draft_before"] = draft
        if draft_against_public(current, draft):
            raise RepairHold("draft protected content differs before the authorized repair")
        payload = copy.deepcopy(draft)
        payload["metadata"][field] = plan["planned_after"]["metadata"][field]
        client("PUT", record_url + "/draft", json.dumps(payload).encode(), rdm=True)
        checked = client("GET", record_url + "/draft", rdm=True)
        # Retain the full native readback even if phase validation cold-holds.
        receipt["draft_after"] = checked
        receipt.update(draft_diff=protected_diff(
                           normalized_edit_draft(current, draft), normalized_edit_draft(current, checked)),
                       draft_public_diff=draft_against_public(current, checked))
        if (checked.get("created") != draft.get("created")
                or checked.get("metadata") != payload["metadata"]
                or [row["path"] for row in receipt["draft_diff"]] != [allowed_path]
                or [row["path"] for row in receipt["draft_public_diff"]] != [allowed_path]):
            raise RepairHold("unplanned full RDM draft change; publish blocked")
        if rehearse:
            client("DELETE", record_url + "/draft", rdm=True)
            draft_opened = False
            try:
                client("GET", record_url + "/draft", rdm=True)
            except Exception as exc:
                if getattr(exc, "code", None) not in (404, 410):
                    raise RepairHold("rehearsal deletion requires 404 or 410") from None
            else:
                raise RepairHold("rehearsal edit draft still exists")
            after = client("GET", record_url, rdm=True)
            if protected_diff(current, after):
                raise RepairHold("rehearsal changed published protected content")
            receipt.update(state="REHEARSED_DRAFT_DELETED", after=after, published=False)
            save()
            return receipt
        receipt["state"] = "DRAFT_VERIFIED_PUBLISH_REQUESTED"
        save()
        publish_requested = True
        client("POST", record_url + "/draft/actions/publish", b"{}", rdm=True)
        receipt["state"] = "PUBLISHED_AWAITING_PUBLIC_READBACK"
        save()
        after = client("GET", record_url, rdm=True)
        receipt.update(after=after, public_diff=protected_diff(current, after))
        if after.get("metadata") != payload["metadata"] or [row["path"] for row in receipt["public_diff"]] != [allowed_path]:
            raise RepairHold("public RDM diff exceeds the approved field; preserve the same DOI")
        if field == "copyright":
            if verify_datacite is None or verify_datacite(plan["record_id"], payload["metadata"][field]) is not True:
                raise RepairHold("RDM verified; exact DataCite InC rights readback is still required")
        receipt["state"] = "PUBLIC_REPAIR_READBACK_VERIFIED"
        save()
        return receipt
    except Exception as exc:
        if draft_opened and not publish_requested:
            try:
                client("DELETE", record_url + "/draft", rdm=True)
                receipt["held_draft_deleted"] = True
            except Exception:
                receipt["held_draft_deleted"] = False
        receipt.update(state="HOLD_REPAIR_OUTCOME_REQUIRES_READBACK", error_type=type(exc).__name__)
        if isinstance(exc, RepairHold):
            receipt["hold_reason"] = str(exc)
        save()
        # Never surface exception messages from an injected HTTP implementation.
        raise RepairHold("repair held; inspect sanitized receipt and reconcile before any retry") from None
