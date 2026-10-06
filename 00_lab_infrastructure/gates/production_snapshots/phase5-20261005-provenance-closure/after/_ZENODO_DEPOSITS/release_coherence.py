#!/usr/bin/env python3
"""Fail-closed rights, metadata, and receipt coherence for Viridis releases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


UNASSIGNED_LICENSES = {"", "unassigned", "none", "pending"}
LOCAL_RECEIPTS = {
    "BUNDLE_MANIFEST.json",
    "LEDGER_BINDING.json",
    "RELEASE_BINDING.json",
    "PUBLISHED_DOI.txt",
    "ZENODO_DRAFT_ID.txt",
}
STALE_RIGHTS_MARKERS = (
    "hold_unassigned",
    "no license is granted",
    "becomes operative only if",
)


class CoherenceError(RuntimeError):
    """A release contains mutually contradictory rights or status claims."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in LOCAL_RECEIPTS
    }


def normalize_license(value: object) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def license_gate(license_id: str) -> str:
    if license_id == "cc-by-4.0":
        return "ASSIGNED_CC_BY_4_0"
    return "ASSIGNED_" + re.sub(r"[^A-Z0-9]+", "_", license_id.upper()).strip("_")


def assigned_rights_notice(title: str, license_id: str) -> str:
    if normalize_license(license_id) != "cc-by-4.0":
        raise CoherenceError(f"unsupported Viridis paper license: {license_id!r}")
    return f'''# Rights and license status

**Work:** {title}

**Current gate:** `ASSIGNED_CC_BY_4_0`

Justin D. Hart authorized this release under the Creative Commons Attribution
4.0 International license (`CC-BY-4.0`). The license applies to this deposited
release package. Attribution should cite the corresponding Zenodo record and
identify later modifications.

License text: https://creativecommons.org/licenses/by/4.0/
'''


def unassigned_rights_notice(title: str) -> str:
    return f'''# Rights and license status

**Work:** {title}

**Current gate:** `HOLD_UNASSIGNED`

No license is granted by this local staging file. The proposed release license
is Creative Commons Attribution 4.0 International (`CC-BY-4.0`). It becomes
operative only through Justin D. Hart's exact release authorization.
'''


def publication_description(existing: object) -> str:
    text = str(existing or "").strip()
    subject = text.split(";", 1)[0].rstrip(" .")
    if not subject:
        subject = "Proof-reconciled generated exploration"
    return (
        subject
        + ". This public working-corpus release includes the reviewed manuscript "
        "and paired Lean evidence. It is not peer reviewed or empirically validated; "
        "significance and novelty have not been independently established."
    )


def publication_notes() -> str:
    return (
        "The paired Lean proof is audited verified and checks the stated mathematics "
        "under declared assumptions. This standalone working-corpus record is licensed "
        "CC BY 4.0. It is not an Intelligence Bound Canon spine admission, and no "
        "empirical, ecological, causal, adoption, commercial, procurement, or legal "
        "outcome is inferred."
    )


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CoherenceError(f"{path}: invalid {label}") from exc
    if not isinstance(value, dict):
        raise CoherenceError(f"{path}: {label} must be an object")
    return value


def validate_bundle(bundle: Path, *, allow_unassigned: bool = False) -> dict[str, Any]:
    metadata_payload = _read_object(bundle / "zenodo_metadata.json", "Zenodo metadata")
    metadata = metadata_payload.get("metadata")
    if not isinstance(metadata, dict):
        raise CoherenceError(f"{bundle}: Zenodo metadata object is missing")
    license_id = normalize_license(metadata.get("license"))
    if license_id in UNASSIGNED_LICENSES:
        if allow_unassigned:
            return {"license": license_id or "unassigned", "state": "HOLD_UNASSIGNED"}
        raise CoherenceError(f"{bundle}: exact rights/license value is required")

    rights_path = bundle / "RIGHTS_AND_LICENSE.md"
    try:
        rights = rights_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoherenceError(f"{rights_path}: positive rights notice is required") from exc
    rights_lower = rights.lower()
    if any(marker in rights_lower for marker in STALE_RIGHTS_MARKERS):
        raise CoherenceError(
            f"{rights_path}: assigned metadata conflicts with unassigned rights notice"
        )
    required_gate = license_gate(license_id)
    if required_gate.lower() not in rights_lower or license_id not in rights_lower:
        raise CoherenceError(f"{rights_path}: does not affirm {license_id}")

    manifest = _read_object(bundle / "BUNDLE_MANIFEST.json", "bundle manifest")
    completeness = manifest.get("package_completeness")
    if not isinstance(completeness, dict):
        raise CoherenceError(f"{bundle}: package_completeness is required")
    if completeness.get("license_gate") != required_gate:
        raise CoherenceError(f"{bundle}: manifest license gate does not match {license_id}")
    if completeness.get("status") != "READY_FOR_PUBLICATION":
        raise CoherenceError(f"{bundle}: package is not marked READY_FOR_PUBLICATION")

    release_binding = _read_object(bundle / "RELEASE_BINDING.json", "release binding")
    if normalize_license(release_binding.get("license")) != license_id:
        raise CoherenceError(f"{bundle}: release binding license mismatch")
    if release_binding.get("approved_by") != "Justin D. Hart":
        raise CoherenceError(f"{bundle}: exact release authorization is missing")
    if release_binding.get("final_artifact_sha256") != tree_hashes(bundle):
        raise CoherenceError(f"{bundle}: release-bound artifact hashes drifted")

    combined = " ".join(
        str(metadata.get(key, "")).lower() for key in ("description", "notes")
    )
    stale_status = (
        "rights-cleared",
        "ledger-approved",
        "no empirical, adoption, commercial, rights, ledger",
        "no empirical, procurement, commercial, rights, ledger",
        "no empirical, legal, causal, adoption, revenue, rights, ledger",
    )
    if any(marker in combined for marker in stale_status):
        raise CoherenceError(f"{bundle}: release metadata retains pre-authorization status")
    if (bundle / "PUBLISHED_DOI.txt").is_file() and (
        re.search(r"\bnot\b[^.]{0,100}\bpublished\b", combined)
        or "no publication evidence" in combined
    ):
        raise CoherenceError(f"{bundle}: published record claims it is unpublished")

    return {"license": license_id, "state": "COHERENT", "license_gate": required_gate}
