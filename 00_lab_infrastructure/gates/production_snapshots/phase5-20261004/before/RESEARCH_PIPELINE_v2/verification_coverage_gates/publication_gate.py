#!/usr/bin/env python3
"""Stage publication labels from the ledger; report-only unless --enforce is set.

This consumer cannot issue certificates or amend a published DOI. Certificate
proof status and claim publication eligibility are deliberately separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

from claim_binding import (CONJECTURE_LABEL, DISCLAIMER, check_run, find_entity,
                           inspect_entity_certificate, read_object, tree_root)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_bindings(artifact: Path, inspection: dict[str, Any]) -> list[dict[str, str]]:
    inputs = inspection.get("sealed_paper_inputs")
    if not isinstance(inputs, dict):
        raise ValueError("certificate lacks sealed paper input bindings")
    paper_bindings = {name: value for name, value in inputs.items() if name in {"SEALED_paper.pdf", "SEALED_paper.tex"}}
    if not paper_bindings:
        raise ValueError("certificate has no sealed paper to bind this artifact")
    files = [path for path in artifact.iterdir() if path.is_file() and path.suffix.lower() in {".pdf", ".tex"}]
    if not files:
        raise ValueError("artifact directory contains no certifiable paper bytes")
    checked = []
    for file in files:
        expected = [binding for name, binding in paper_bindings.items()
                    if Path(name).suffix.lower() == file.suffix.lower()]
        if not expected:
            raise ValueError(f"artifact {file.name} has no certificate binding")
        digest = sha256(file)
        matching = [value for value in expected if isinstance(value, dict) and value.get("sha256") == digest]
        if len(matching) != 1:
            raise ValueError(f"artifact bytes differ from certified sealed input: {file.name}")
        checked.append({"path": str(file.resolve()), "sha256": digest})
    return checked


def _downgrade_title(value: Any) -> str:
    title = value if isinstance(value, str) else "Untitled artifact"
    # Existing claims of proof must not survive a conjecture prefix.
    title = re.sub(r"\b(?:theorem(?:\s+stack)?|canon)\b", "candidate", title, flags=re.IGNORECASE)
    return title if title.startswith(CONJECTURE_LABEL) else f"{CONJECTURE_LABEL}: {title}"


def evaluate_publication(
    artifact: Path, ledger: dict[str, Any], *, entity_id: str | None = None,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "artifact": str(artifact.resolve()), "mode": "REPORT_ONLY", "status": "HOLD",
        "verification_status": "CONJECTURE", "label": CONJECTURE_LABEL,
        "disclaimer": DISCLAIMER, "reasons": [], "paper_bindings": [],
        "published_doi_requires_human_decision": False, "local_lean_execution": False,
    }
    metadata: dict[str, Any] = {}
    try:
        if not artifact.is_dir():
            raise ValueError("artifact must be a directory")
        metadata_path = artifact / "zenodo_metadata.json"
        if not metadata_path.exists():
            metadata_path = artifact / "metadata.json"
        if metadata_path.exists():
            metadata = read_object(metadata_path)
            if isinstance(metadata.get("metadata"), dict):
                metadata = metadata["metadata"]
        entity = find_entity(ledger, artifact, entity_id)
        result["entity_id"] = entity.get("id")
        doi = metadata.get("doi") or entity.get("doi")
        if isinstance(doi, str) and doi:
            result["doi"] = doi
            result["published_doi_requires_human_decision"] = True
        inspection = inspect_entity_certificate(entity, ledger, inspector)
        result["paper_bindings"] = _artifact_bindings(artifact, inspection)
        claims = check_run(artifact, ledger, entity_id=entity.get("id"), inspector=inspector)
        result["claim_gate"] = claims
        if claims["status"] != "PASS":
            raise ValueError("claim-binding gate held: " + "; ".join(claims["reasons"]))
        result.update(status="PASS", verification_status="CERTIFIED", label="CERTIFIED")
    except Exception as exc:
        result["reasons"].append(f"{type(exc).__name__}: {exc}")
    proposed = dict(metadata)
    if result["verification_status"] != "CERTIFIED":
        proposed["title"] = _downgrade_title(metadata.get("title"))
    proposed["verification_status"] = result["verification_status"]
    proposed["verification_banner"] = result["label"]
    proposed["model_validity_disclaimer"] = DISCLAIMER
    proposed["verification_scope"] = "Only the listed bound formal model claims; empirical claims are not validated by this certificate."
    proposed["unverified_claims"] = result.get("claim_gate", {}).get("unverified_claims", [])
    description = proposed.get("description", proposed.get("abstract", ""))
    if not isinstance(description, str):
        description = ""
    description = re.sub(r"\b(?:compiled\s+theorem\s+stack|canon(?:\s+index)?|theorem)\b", "candidate", description,
                         flags=re.IGNORECASE) if result["verification_status"] != "CERTIFIED" else description
    proposed["description"] = result["label"] + "\n\n" + DISCLAIMER + "\n\n" + description
    if proposed["unverified_claims"]:
        proposed["description"] += "\n\nNot formally verified; empirical validation is not established by the Lean certificate:\n"
        proposed["description"] += "\n".join("- " + item["english_claim"] for item in proposed["unverified_claims"])
    if "abstract" in proposed:
        proposed["abstract"] = proposed["description"]
    result["proposed_metadata"] = proposed
    result["canon_eligible"] = result["status"] == "PASS"
    return result


def stage_result(result: dict[str, Any], output_dir: Path, *, enforce: bool = False) -> list[str]:
    """Write a reviewable successor package, without touching source artifacts."""
    source = Path(result["artifact"]).resolve()
    target = output_dir.resolve()
    if target == source or target.is_relative_to(source):
        raise ValueError("output-dir must be outside the source artifact")
    target.mkdir(parents=True, exist_ok=True)
    report = dict(result)
    report["mode"] = "ENFORCING" if enforce else "REPORT_ONLY"
    report["source_artifact_modified"] = False
    paths = []
    report_path = target / "PUBLICATION_GATE_REPORT.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    paths.append(str(report_path))
    if enforce:
        # Existing published records are never changed, even with --enforce.
        # A successor proposal is reviewable; DOI amendment remains a human act.
        metadata_path = target / "metadata.json"
        metadata_path.write_text(json.dumps(result["proposed_metadata"], indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        banner_path = target / "VERIFICATION_BANNER.md"
        banner_path.write_text(result["label"] + "\n\n" + DISCLAIMER + "\n", encoding="utf-8")
        paths.extend([str(metadata_path), str(banner_path)])
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--entity-id")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--enforce", action="store_true", help="stage enforceable labels in output-dir")
    args = parser.parse_args(argv)
    if args.enforce and args.output_dir is None:
        parser.error("--enforce requires an explicit --output-dir for the successor package")
    try:
        result = evaluate_publication(args.artifact, read_object(args.ledger), entity_id=args.entity_id)
        if args.output_dir:
            result["written"] = stage_result(result, args.output_dir, enforce=args.enforce)
        result["mode"] = "ENFORCING" if args.enforce else "REPORT_ONLY"
    except Exception as exc:
        result = {"status": "HOLD", "verification_status": "CONJECTURE", "label": CONJECTURE_LABEL,
                  "disclaimer": DISCLAIMER, "reasons": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
