#!/usr/bin/env python3
"""Keep human-facing package metadata consistent with formal certification.

This module is intentionally narrow. It never upgrades scientific state; it
only detects and repairs prose that contradicts an already-bound, clean
Comparator certificate.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any


CERTIFIED_STATUS = "LEAN_ZERO_SORRY_CERTIFIED"
STALE_PATTERNS = (
    re.compile(r"\bno\s+(?:formally\s+)?(?:verified|certified)\s+result\s+exists\b", re.I),
    re.compile(r"\bnot\b[^.;\n]{0,80}\bformally\s+(?:verified|certified)\b", re.I),
    re.compile(r"\bformally\s+unverified\b", re.I),
    re.compile(
        r"\bformal(?:ly)?\s+(?:verification|certification)\b"
        r"[^.;\n]{0,100}\b(?:remain(?:s)?\s+)?unassessed\b",
        re.I,
    ),
)
RELEASE_TEXT_FIELDS = ("description", "notes", "spine_reason")


def comparator_certified(manifest: dict[str, Any]) -> bool:
    formal = manifest.get("formal_verification")
    return bool(
        isinstance(formal, dict)
        and formal.get("provider") == "COMPARATOR_CLOUD"
        and formal.get("status") == CERTIFIED_STATUS
        and formal.get("aristotle_required") is False
    )


def certified_metadata_contradictions(manifest: dict[str, Any]) -> list[str]:
    """Return release-metadata fields that deny a bound Comparator certificate."""
    if not comparator_certified(manifest):
        return []
    metadata = manifest.get("release_metadata")
    if not isinstance(metadata, dict):
        return ["release_metadata"]
    contradictions: list[str] = []
    for field in RELEASE_TEXT_FIELDS:
        value = metadata.get(field)
        if isinstance(value, str) and any(pattern.search(value) for pattern in STALE_PATTERNS):
            contradictions.append(f"release_metadata.{field}")
    return contradictions


def certified_text_contradictions(text: str) -> list[str]:
    """Return stable identifiers for prose that denies formal certification."""
    return [
        f"stale_verification_text_pattern_{index}"
        for index, pattern in enumerate(STALE_PATTERNS, start=1)
        if pattern.search(text)
    ]


def corrected_certified_metadata(manifest: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a copy with conservative, certification-consistent draft metadata."""
    if not comparator_certified(manifest):
        raise ValueError("manifest is not bound to a clean Comparator certificate")
    result = deepcopy(manifest)
    metadata = result.setdefault("release_metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("release_metadata must be an object")
    replacements = {
        "description": (
            "Comparator-certified working-corpus methods note; formally certified for its "
            "declared Lean statements, but not yet independently paper-reviewed, empirically "
            "validated, licensed, ledger-bound, published, or deployed."
        ),
        "notes": (
            "Comparator-certified local draft; independent paper review, license, ledger row, "
            "DOI, Git Canon publication, ViridisOS activation, and deployment remain separate gates."
        ),
        "spine_reason": (
            "The declared Lean statements are Comparator-certified. Certification alone does "
            "not satisfy the five-gate Intelligence Bound Canon doctrine; no spine admission is implied."
        ),
    }
    changes: list[str] = []
    for field, value in replacements.items():
        if metadata.get(field) != value:
            metadata[field] = value
            changes.append(f"release_metadata.{field}")
    if metadata.get("spine_admitted") is not False:
        metadata["spine_admitted"] = False
        changes.append("release_metadata.spine_admitted")
    if metadata.get("version") == "0.1.0-certified-draft":
        metadata["version"] = "0.1.1-certified-draft"
        changes.append("release_metadata.version")
    pending = {
        "status": "pending",
        "path": None,
        "evidence": "Comparator certificate is bound; a separate provider-attributed paper correspondence review is pending.",
    }
    if result.get("post_lean_review") != pending:
        result["post_lean_review"] = pending
        changes.append("post_lean_review")
    legacy_pending = {
        "status": "pending",
        "path": None,
        "evidence": "Legacy compatibility field; the independent post-Lean review is pending.",
    }
    if result.get("post_aristotle_review") != legacy_pending:
        result["post_aristotle_review"] = legacy_pending
        changes.append("post_aristotle_review")
    return result, changes


def reviewed_text_contradictions(text: str) -> list[str]:
    """Detect manuscript status incompatible with a passing internal review.

    External peer review and empirical validation remain separate gates.
    """
    patterns = (
        r"\bindependent\s+(?:paper|manuscript)\s+review\s+remains?\s+pending\b",
        r"\bmanuscript\s+remains?\s+subject\s+to\s+later\s+independent\s+review\b",
    )
    return [f"pending_manuscript_review_pattern_{index}"
            for index, pattern in enumerate(patterns, start=1)
            if re.search(pattern, text, re.I)]
