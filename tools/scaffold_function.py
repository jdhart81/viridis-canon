#!/usr/bin/env python3
"""Scaffold a function.json beside a Lean source (WS-20; used by the engine package template).

Fills only the mechanical fields — id, Lean module, source path + SHA-256, the
theorem name (checked to exist), DOI from catalog/config.json — and writes a
``tier: "reference"`` theorem-function skeleton. It never writes ``callable`` or
``admitted``. To make it callable an author adds inputs, hypotheses, derived
values, the conclusion check and a satisfying example, sets ``tier: "callable"``
and ``runner: "theorem"``, and runs ``python3 -m canon_core validate-functions``.

    python3 tools/scaffold_function.py series/ABC/ViridisRun200.lean \\
        --theorem main_theorem --id abc-main-theorem [--out series/ABC/function.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_URL = "https://jdhart81.github.io/viridis-canon/schemas/function-v1.json"


def main(argv=None) -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("lean", help="Lean source path relative to the canon root")
    cli.add_argument("--theorem", required=True)
    cli.add_argument("--id", required=True)
    cli.add_argument("--name", default="")
    cli.add_argument("--out", default="")
    cli.add_argument("--root", default=str(ROOT))
    args = cli.parse_args(argv)
    root = Path(args.root).resolve()
    source = root / args.lean
    if not source.is_file():
        print(f"ERROR: {args.lean} does not exist", file=sys.stderr)
        return 1
    text = source.read_text(encoding="utf-8", errors="replace")
    if not re.search(rf"^\s*(?:private\s+|protected\s+)?(?:theorem|lemma)\s+(?:[A-Za-z0-9_'.]+\.)?{re.escape(args.theorem)}\b", text, re.M):
        print(f"ERROR: theorem {args.theorem} is not declared in {args.lean}", file=sys.stderr)
        return 1
    namespace = re.search(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\s*$", text, re.M)
    config = json.loads((root / "catalog" / "config.json").read_text(encoding="utf-8"))
    doi = config.get("doi_by_path", {}).get(args.lean) or config.get("concept_doi", "")
    manifest = {
        "$schema": SCHEMA_URL,
        "schema_version": 1,
        "id": args.id,
        "kind": "theorem_function",
        "name": args.name or f"{args.theorem.replace('_', ' ')}",
        "version": "0.1.0",
        "summary": "TODO(author): one plain-language sentence saying what question this theorem answers.",
        "decision_family": None,
        "tier": "reference",
        "state": "READY",
        "reconciliation": None,
        "blocked": None,
        "doi": doi,
        "lean": {
            "module": namespace.group(1) if namespace else source.stem,
            "sources": [{"path": args.lean, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}],
            "theorems": [args.theorem],
            "verification_provider": None,
            "verification_receipt_id": None,
        },
        "inputs": [],
        "outputs": [],
        "hypotheses": [],
        "example": None,
        "scope": "Theorem function: the Lean hypotheses and conclusion restated as checks over supplied real values.",
        "boundary": "Conditional mathematics about the supplied values only; not empirical validity, a real-world magnitude, Viridis review, certification, a credit, or a registry determination.",
        "empirical_validation": "NOT_VALIDATED",
        "runner": None,
        "provenance": {"scaffolded_by": "tools/scaffold_function.py"},
    }
    out = Path(args.out) if args.out else source.parent / "function.json"
    if not out.is_absolute():
        out = root / out
    if out.exists():
        print(f"ERROR: {out} exists; the scaffold never overwrites a manifest", file=sys.stderr)
        return 1
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(root)} (tier reference)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
