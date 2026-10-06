#!/usr/bin/env python3
"""Generate reviewable public text from the coverage ledger, without publishing."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "00_lab_infrastructure" / "gates"))
# Support the isolated component staging tree as well as the repository layout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gates"))
from claim_binding import CONJECTURE_LABEL, DISCLAIMER, ledger_entities, read_object, tree_root, inspect_entity_certificate
from publication_gate import evaluate_publication
from mirror_parity import GENERATION_ROOT

STATUSES = ("MIRROR_DRIFT", "UNSOUND_ENVIRONMENT", "UNSOUND", "HAS_SORRY", "DEBT", "NO_FORMALIZATION", "CLEAN_UNCERTIFIED", "CERTIFIED")


def _quarantined(entry: dict[str, Any]) -> bool:
    from claim_binding import _static_vacuity
    return entry.get("status") in {"UNSOUND", "UNSOUND_ENVIRONMENT"} or _static_vacuity({}, entry)


def escape_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _safe_entities(ledger: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ledger_entities(ledger)
    files, runs = ledger["file_entities"], ledger["run_entities"]
    for values, table in ((files, "file"), (runs, "run")):
        ids = [entity.get("id") for entity in values]
        if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
            raise ValueError(f"{table} entity identities are missing or ambiguous")
        for entity in values:
            if entity.get("status") not in STATUSES:
                raise ValueError(f"unpartitioned ledger status for {entity['id']}")
    return files, runs


def _public_strings(value: Any, root: Path) -> Any:
    """Keep diagnostics and claim scope while hiding local roots in public text.

    This rendering projection never touches ledger or gate evidence. Replace
    only the two known roots, retaining relative filenames and every reason.
    """
    prefixes = ((str(root.resolve()), "[canonical mirror]"),
                (str(root), "[canonical mirror]"),
                (str(Path(GENERATION_ROOT).resolve()), "[generation root]"),
                (str(GENERATION_ROOT), "[generation root]"))
    if isinstance(value, str):
        for prefix, label in prefixes:
            value = value.replace(prefix, label)
        return value
    if isinstance(value, list):
        return [_public_strings(item, root) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            public_key = _public_strings(key, root)
            if public_key in result:
                raise ValueError("public diagnostic root projection collides")
            result[public_key] = _public_strings(item, root)
        return result
    return value


def render_index(
    ledger: dict[str, Any], *, inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, str]:
    root = tree_root(ledger)
    files, runs = _safe_entities(ledger)
    files = [entry for entry in files if "_LATEST" not in Path(str(entry.get("path", ""))).parts]
    runs = [entry for entry in runs if "_LATEST" not in Path(str(entry.get("path", ""))).parts]
    papers = [entry for entry in runs if entry.get("kind") == "PAPER"]
    syntheses = [entry for entry in runs if entry.get("kind") == "SYNTHESIS"]
    if any(entry.get("kind") not in {"PAPER", "SYNTHESIS"} for entry in runs):
        raise ValueError("run entity kind must be PAPER or SYNTHESIS")
    public = []
    canon = []
    for entry in sorted(papers, key=lambda value: value["id"]):
        artifact = root / str(entry.get("path", ""))
        current_proof_status = entry["status"]
        if current_proof_status == "CERTIFIED":
            try:
                inspect_entity_certificate(entry, ledger, inspector)
            except Exception:
                current_proof_status = "DEBT"
        result = evaluate_publication(artifact, ledger, entity_id=entry["id"], inspector=inspector)
        item = {"id": entry["id"], "path": entry.get("path"), "proof_status": current_proof_status, "ledger_snapshot_status": entry["status"],
                "verification_status": result["verification_status"], "label": result["label"],
                "disclaimer": DISCLAIMER, "doi": entry.get("doi"), "gate_reasons": result["reasons"],
                "proposed_description": result["proposed_metadata"]["description"],
                "published_doi_requires_human_decision": result["published_doi_requires_human_decision"]}
        public.append(item)
        if result["canon_eligible"] and not _quarantined(entry):
            canon.append({**item, "claims": result["claim_gate"]["claims"]})
    lines = ["# Verification coverage and public index", "", "Scanned tree: canonical certification mirror.", "",
             "This file is generated from corpus_ledger.json. Source changes belong in that ledger.", "",
             DISCLAIMER, "", "## Ledger snapshot coverage", "",
             "Snapshot counts record the ledger at scan time. Current proof statuses below are re-inspected before rendering.", "", "| Status | Lean files | Paper runs |", "|---|---:|---:|"]
    fcounts, rcounts = Counter(entry["status"] for entry in files), Counter(entry["status"] for entry in papers)
    for status in STATUSES:
        lines.append(f"| {status} | {fcounts[status]} | {rcounts[status]} |")
    lines.extend(["", "Proof certificate status and public claim eligibility are separate. A historical certificate remains recorded even when the claim publication gate holds.",
                  "", "## Eligible model results", ""])
    if canon:
        for item in canon:
            lines.append(f"- {item['id']}: CERTIFIED. {DISCLAIMER}")
            for claim in item["claims"]:
                lines.append(f"  - {claim['english_claim']} (bound declaration: `{claim['lean_theorem']}`; witness: `{claim['nonvacuity_obligation']}`).")
    else:
        lines.append("No paper-run artifact currently passes the certificate, paper-byte, and public claim gates.")
    lines.extend(["", "## Paper publication labels", "", "| Entity | Proof status | Public label |", "|---|---|---|"])
    for item in public:
        lines.append(f"| {escape_cell(item['id'])} | {item['proof_status']} | {item['label']} |")
    lines.extend(["", "## Explicit publication registrations", "",
                  "Publication registrations are separate from the paper-run denominator. Only the exact registered artifact and current claim gate can qualify a published scope.", "",
                  "| Publication | DOI | Claim status |", "|---|---|---|"])
    registrations = []
    for entry in sorted(ledger.get("publication_entities", []), key=lambda value: value["id"]):
        gate = evaluate_publication(root / entry["path"], ledger, entity_id=entry["id"], inspector=inspector)
        passed = (entry.get("registration_revalidated") is True
                  and entry.get("publication_registration_status") == "PASS"
                  and gate.get("status") == "PASS"
                  and gate.get("exact_publication_binding") is True
                  and isinstance(entry.get("doi"), str) and bool(entry["doi"])
                  and gate.get("doi") == entry["doi"] and not _quarantined(entry))
        status = "CERTIFIED_SCOPED_CLAIMS" if passed else "UNCERTIFIED"
        item = {"id": entry["id"], "doi": entry.get("doi"), "label": status,
                "disclaimer": DISCLAIMER, "gate_reasons": gate.get("reasons", [])}
        registrations.append(item)
        lines.append(f"| {escape_cell(entry['id'])} | {escape_cell(entry.get('doi') or 'unpublished')} | {status} |")
        if passed:
            canon.append({**item, "claims": gate["claim_gate"]["claims"]})
    lines.extend(["", "## Quarantined source files", ""])
    quarantined = sorted((entry for entry in files if _quarantined(entry)), key=lambda entry: entry["id"])
    lines.extend(f"- `{escape_cell(entry['path'])}` — {escape_cell(entry['status'])}; unsound or vacuous source promotion is prohibited." for entry in quarantined)
    if not quarantined:
        lines.append("None recorded.")
    lines.extend(["", "## Synthesis artifacts", ""])
    lines.extend(f"- `{escape_cell(entry['path'])}` — SYNTHESIS; excluded from paper coverage." for entry in syntheses)
    if not syntheses:
        lines.append("None recorded.")
    lines.extend(["", "Published DOI amendments require a separate human decision. These outputs are successor proposals only.", ""])
    public_root = Path(ledger["tree_root"])
    public = _public_strings(public, public_root)
    registrations = _public_strings(registrations, public_root)
    canon = _public_strings(canon, public_root)
    return {"README.md": _public_strings("\n".join(lines), public_root),
            "ZENODO_DESCRIPTIONS.json": json.dumps({"generated_from": "corpus_ledger.json", "publication_mode": "REPORT_ONLY",
                "disclaimer": DISCLAIMER, "artifacts": public, "publication_registrations": registrations}, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            "CANON_INDEX.json": json.dumps({"generated_from": "corpus_ledger.json", "disclaimer": DISCLAIMER,
                "entries": canon, "quarantined": [entry["id"] for entry in quarantined]}, indent=2, ensure_ascii=False, sort_keys=True) + "\n"}


def generate(ledger_path: Path, output_dir: Path, *, enforce: bool = False,
             inspector: Callable[[Path, Path], dict[str, Any]] | None = None) -> dict[str, Any]:
    ledger = read_object(ledger_path)
    root = tree_root(ledger)
    target = output_dir.resolve()
    if target == root or target.is_relative_to(root):
        if not enforce:
            raise ValueError("report-only output-dir must be outside the scanned tree")
    outputs = render_index(ledger, inspector=inspector)
    target.mkdir(parents=True, exist_ok=True)
    receipt = {"mode": "ENFORCING" if enforce else "REPORT_ONLY", "tree_root": str(root),
               "ledger_sha256": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
               "remote_publication_performed": False, "outputs": {}}
    for name, content in outputs.items():
        path = target / name
        path.write_text(content, encoding="utf-8")
        receipt["outputs"][name] = {"path": str(path), "sha256": hashlib.sha256(content.encode()).hexdigest()}
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--enforce", action="store_true", help="permit local generated outputs in the scanned tree")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(generate(args.ledger, args.output_dir, enforce=args.enforce), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "HOLD", "reasons": [f"{type(exc).__name__}: {exc}"]}, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
