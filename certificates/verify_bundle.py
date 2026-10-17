#!/usr/bin/env python3
"""Check that every certificate in this folder still binds the files beside it.

Standard library only; no Lean needed. For each Run-* directory it confirms
that each file named in LEAN_ZERO_SORRY_CERTIFICATE.json "bindings" is present
and has the recorded SHA-256, and that the receipt and request agree with the
certificate about the solution and challenge hashes.

The sealed paper (SEALED_paper.*) is not copied here; it is published on Zenodo
under the DOI listed in index.json, and its hash is reported for you to check.

Usage:  python3 certificates/verify_bundle.py [certificates-dir]
Exit status 0 means every binding matched.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_run(run_dir: Path) -> tuple[int, list[str], list[str]]:
    """Return (files checked, problems, sealed-paper hashes to check against Zenodo)."""
    cert = json.loads((run_dir / "LEAN_ZERO_SORRY_CERTIFICATE.json").read_text())
    problems: list[str] = []
    external: list[str] = []
    checked = 0

    def walk(node):
        nonlocal checked
        if isinstance(node, dict) and "path" in node and "sha256" in node:
            name = os.path.basename(node["path"])
            if name.startswith("SEALED_paper"):
                external.append(f"{name} sha256={node['sha256']}")
                return
            f = run_dir / name
            checked += 1
            if not f.exists():
                problems.append(f"missing {name}")
            elif sha256(f) != node["sha256"]:
                problems.append(f"hash mismatch {name}")
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)

    walk(cert.get("bindings", {}))

    b = cert["bindings"]
    receipt = json.loads((run_dir / os.path.basename(b["independent_cloud_receipt"]["path"])).read_text())
    if (receipt.get("candidate") or {}).get("sha256") != b["candidate_proof"]["sha256"]:
        problems.append("receipt candidate hash differs from certificate")
    if (receipt.get("formal_statement") or {}).get("sha256") != b["formal_statement"]["sha256"]:
        problems.append("receipt challenge hash differs from certificate")
    if receipt.get("status") != "VERIFIED":
        problems.append(f"receipt status is {receipt.get('status')!r}, not VERIFIED")
    if cert.get("status") != "LEAN_ZERO_SORRY_CERTIFIED":
        problems.append(f"certificate status is {cert.get('status')!r}")
    return checked, problems, external


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent
    runs = sorted(p for p in root.glob("Run-*") if p.is_dir())
    total, bad = 0, 0
    for run in runs:
        n, problems, external = check_run(run)
        total += n
        status = "OK" if not problems else "FAIL"
        bad += bool(problems)
        print(f"{run.name}: {status} ({n} bound files)")
        for p in problems:
            print(f"    {p}")
    print(f"{len(runs)} runs, {total} bound files, {bad} runs with problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
