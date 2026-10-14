"""Prepare and conditionally apply the seven authorized Phase 5 RDM repairs.

This module has no network transport or executable mutation CLI. A caller must
provide the reviewed Bearer-header transport, its hash-bound installation
receipt, and the exact approved plan. Publication outcomes are never retried.
"""
from __future__ import annotations

import copy
import hashlib
import json
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
SERVER_FIELDS = {"/revision_id", "/updated"}
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


def make_plan(before, record_id, field, value, *, verified_source, certificate_valid=None):
    record_id = str(record_id)
    if str(before.get("id")) != record_id or "revision_id" not in before:
        raise RepairHold("native RDM baseline and exact record identity required")
    if field == "copyright":
        if COPYRIGHTS.get(record_id) != value:
            raise RepairHold("copyright repair differs from A4 authorization")
    elif field == "description":
        if record_id != "23329823" or certificate_valid is not False:
            raise RepairHold("UNMT repair requires absence of a valid certificate")
        banner = verified_source.get("banner")
        if (not isinstance(banner, str) or hashlib.sha256(banner.encode()).hexdigest() != STANDARD_BANNER_SHA256
                or value != banner + before["metadata"]["description"]):
            raise RepairHold("description may only prepend the exact source banner")
    else:
        raise RepairHold("unapproved metadata field")
    if not verified_source.get("sha256"):
        raise RepairHold("hash-bound verified source required")
    after = copy.deepcopy(before)
    after["metadata"][field] = value
    changes = full_diff(before, after)
    if any(row["path"] != "/metadata/" + field for row in changes):
        raise RepairHold("planned full RDM diff exceeds authorized field")
    return {"state": "PREPARED_AWAITING_REVIEWED_INSTALLATION", "record_id": record_id,
            "authority": "A4", "field": field, "verified_source": verified_source,
            "certificate_valid": certificate_valid,
            "before": before, "planned_after": after, "planned_diff": changes,
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
               verify_datacite=None):
    """Use only an installed reviewed transport; retain uncertainty on failure."""
    require_installed_transport(installation_receipt, installed_transport, expected_installation_receipt_sha256)
    if canonical_hash(plan) != expected_plan_sha256 or plan.get("authority") != "A4":
        raise RepairHold("approved plan binding differs")
    try:
        reconstructed = make_plan(plan["before"], plan["record_id"], plan["field"],
                                  plan["planned_after"]["metadata"][plan["field"]],
                                  verified_source=plan["verified_source"],
                                  certificate_valid=plan.get("certificate_valid"))
    except Exception:
        raise RepairHold("plan does not satisfy the A4 record, field and value authorization") from None
    if reconstructed != plan:
        raise RepairHold("plan structure or full RDM diff exceeds the A4 authorization")
    field = plan["field"]
    allowed = {"/metadata/" + field} | SERVER_FIELDS
    record_url = RDM + plan["record_id"]
    receipt = {"state": "CHECKING_CURRENT_BASELINE", "record_id": plan["record_id"],
               "plan_sha256": expected_plan_sha256, "external_mutation": False}

    def save():
        path = Path(receipt_path)
        serialized = sanitize(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)) + "\n"
        if len(serialized.encode()) > 1024 * 1024:
            raise RepairHold("receipt exceeds one MiB limit")
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(serialized)
        temp.replace(path)

    current = client("GET", record_url, rdm=True)
    if canonical_hash(current) != plan["before_sha256"]:
        changes = full_diff(plan["planned_after"], current)
        if all(row["path"] in SERVER_FIELDS for row in changes):
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
    try:
        receipt.update(state="OPEN_EDIT_DRAFT_REQUESTED", external_mutation=True)
        save()
        draft = client("POST", record_url + "/draft", b"{}", rdm=True)
        receipt["draft_before"] = draft
        if draft.get("metadata") != current.get("metadata"):
            raise RepairHold("draft metadata differs before the authorized repair")
        payload = {"metadata": plan["planned_after"]["metadata"]}
        client("PUT", record_url + "/draft", json.dumps(payload).encode(), rdm=True)
        checked = client("GET", record_url + "/draft", rdm=True)
        receipt.update(draft_after=checked, draft_diff=full_diff(draft, checked))
        if checked.get("metadata") != payload["metadata"] or any(row["path"] not in allowed for row in receipt["draft_diff"]):
            raise RepairHold("unplanned full RDM draft change; publish blocked")
        receipt["state"] = "DRAFT_VERIFIED_PUBLISH_REQUESTED"
        save()
        client("POST", record_url + "/draft/actions/publish", b"{}", rdm=True)
        receipt["state"] = "PUBLISHED_AWAITING_PUBLIC_READBACK"
        save()
        after = client("GET", record_url, rdm=True)
        receipt.update(after=after, public_diff=full_diff(current, after))
        if after.get("metadata") != payload["metadata"] or any(row["path"] not in allowed for row in receipt["public_diff"]):
            raise RepairHold("public RDM diff exceeds the approved field; preserve the same DOI")
        if field == "copyright":
            if verify_datacite is None or verify_datacite(plan["record_id"], payload["metadata"][field]) is not True:
                raise RepairHold("RDM verified; exact DataCite InC rights readback is still required")
        receipt["state"] = "PUBLIC_REPAIR_READBACK_VERIFIED"
        save()
        return receipt
    except Exception as exc:
        receipt.update(state="HOLD_REPAIR_OUTCOME_REQUIRES_READBACK", error_type=type(exc).__name__)
        save()
        # Never surface exception messages from an injected HTTP implementation.
        raise RepairHold("repair held; inspect sanitized receipt and reconcile before any retry") from None
