#!/usr/bin/env python3
"""Build certificates/index.json and per-run comparator configs.

Standard library only. Deterministic: the same inputs always produce the same
bytes (no timestamps of its own, sorted output).

Usage:
    python3 tools/build_certificates_index.py          # write outputs
    python3 tools/build_certificates_index.py --check  # exit 1 if outputs are stale

What it reads (all inside this repository):
    certificates/Run-*/LEAN_ZERO_SORRY_CERTIFICATE.json   the issued certificate
    certificates/Run-*/<files the certificate binds>      byte-exact copies
    **/function.json                                       OS function manifests

What it writes:
    certificates/index.json                    one entry per certified run
    certificates/Run-*/comparator.config.json  input for leanprover/comparator

The depth label is a size indicator computed from the Lean source, not a
judgement of novelty or mathematical importance. Its rule is stated in
DEPTH_RULE below and repeated in the index.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = ROOT / "certificates"

DEPTH_RULE = (
    "substantial if the certified candidate has at least 200 non-blank lines "
    "and the median proof length of its listed theorems is at least 6 lines; "
    "otherwise elementary. Size indicator only: it does not measure novelty, "
    "difficulty or scientific value."
)
# Proofs that close with a single basic tactic or term are reported separately.
ONE_STEP = re.compile(
    r"^(by\s+)?(rfl|ring|ring_nf|linarith|nlinarith|norm_num|simp|omega|decide|"
    r"positivity|trivial|exact\s+\S+|exact\s+\S+\s+\S+\s+\S+|field_simp)\s*$"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def basename(p: str) -> str:
    return os.path.basename(p)


def theorem_proofs(src: str, names: list[str]) -> dict[str, list[str]]:
    """Return proof lines (blank and comment lines dropped) for each listed theorem."""
    stop = r"\n(?:theorem|lemma|def|noncomputable|structure|instance|abbrev|end|namespace|section|/--|@\[|example|open|variable)\b"
    out: dict[str, list[str]] = {}
    for name in names:
        m = re.search(r"\n(?:theorem|lemma)\s+" + re.escape(name) + r"\b(.*?)(?=" + stop + r"|\Z)", src, re.S)
        if not m:
            continue
        body = m.group(1)
        proof = body.split(":=", 1)[1] if ":=" in body else ""
        lines = [l.strip() for l in proof.strip().splitlines()]
        out[name] = [l for l in lines if l and not l.startswith("--")]
    return out


def load_functions() -> list[dict]:
    rows = []
    for path in sorted(ROOT.glob("**/function.json")):
        if ".lake" in path.parts or "certificates" in path.parts:
            continue
        j = json.loads(path.read_text())
        lean = j.get("lean") or {}
        rows.append({
            "id": j.get("id"),
            "name": j.get("name"),
            "kind": j.get("kind"),
            "tier": j.get("tier"),
            "doi": j.get("doi"),
            "summary": j.get("summary"),
            "empirical_validation": j.get("empirical_validation"),
            "manifest": str(path.relative_to(ROOT)),
            "receipt": lean.get("verification_receipt_id"),
        })
    return rows


def build() -> tuple[dict, dict[Path, str]]:
    functions = load_functions()
    runs = []
    configs: dict[Path, str] = {}
    for run_dir in sorted(CERT_DIR.glob("Run-*")):
        cert_path = run_dir / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        cert = json.loads(cert_path.read_text())
        b = cert["bindings"]
        candidate = basename(b["candidate_proof"]["path"])
        challenge = basename(b["formal_statement"]["path"])
        receipt_name = basename(b["independent_cloud_receipt"]["path"])
        request_name = basename(b["request"]["path"])
        request = json.loads((run_dir / request_name).read_text())
        receipt = json.loads((run_dir / receipt_name).read_text())

        expected = list(request.get("expected_theorem_names") or [])
        obligations = list(request.get("nonvacuity_obligations") or [])
        namespace = request.get("namespace") or ""
        resp_names = list(((receipt.get("provider_response") or {}).get("theoremNames")) or [])
        if resp_names:
            qualified = resp_names
        else:
            qualified = [f"{namespace}.{n}" if namespace else n for n in expected + obligations]

        cand_src = (run_dir / candidate).read_text(encoding="utf-8")
        proofs = theorem_proofs(cand_src, expected)
        lengths = [len(v) for v in proofs.values()]
        nonblank = sum(1 for l in cand_src.splitlines() if l.strip())
        median = statistics.median(lengths) if lengths else 0
        one_step = sorted(n for n, v in proofs.items() if len(v) <= 2 and ONE_STEP.match(" ".join(v)))
        depth = "substantial" if nonblank >= 200 and median >= 6 else "elementary"

        cand_sha = sha256(run_dir / candidate)
        chal_sha = sha256(run_dir / challenge)

        linked = [
            {k: f[k] for k in ("id", "name", "kind", "tier", "doi", "summary", "empirical_validation", "manifest")}
            for f in functions
            if f["receipt"] and (f["receipt"] == cert.get("candidate_id") or f["receipt"].startswith(run_dir.name + "-"))
        ]

        config = {
            "challenge_module": "Challenge",
            "solution_module": "Solution",
            "theorem_names": qualified,
            "permitted_axioms": list(request.get("permitted_axioms") or []),
        }
        configs[run_dir / "comparator.config.json"] = json.dumps(config, indent=2, ensure_ascii=False) + "\n"

        runs.append({
            "run": run_dir.name,
            "certificate_status": cert.get("status"),
            "certificate_standard": cert.get("standard"),
            "verification_standard": cert.get("verification_standard"),
            "issued_at_utc": cert.get("issued_at_utc"),
            "candidate_id": cert.get("candidate_id"),
            "gates": cert.get("gates"),
            "scope": cert.get("scope"),
            "toolchain": request.get("toolchain"),
            "mathlib_rev": request.get("mathlib_rev"),
            "namespace": namespace,
            "files": {
                "solution": {"file": candidate, "sha256": cand_sha},
                "challenge": {"file": challenge, "sha256": chal_sha},
                "receipt": receipt_name,
                "request": request_name,
                "claim_inventory": "SEALED_CLAIM_INVENTORY.json" if (run_dir / "SEALED_CLAIM_INVENTORY.json").exists() else None,
                "comparator_config": "comparator.config.json",
            },
            "challenge_identical_to_solution": cand_sha == chal_sha,
            "theorems": expected,
            "nonvacuity_obligations": obligations,
            "comparator_theorem_names": qualified,
            "permitted_axioms": config["permitted_axioms"],
            "receipt_status": receipt.get("status"),
            "receipt_checks": receipt.get("checks"),
            "depth": {
                "label": depth,
                "candidate_nonblank_lines": nonblank,
                "proof_lines": {n: len(v) for n, v in sorted(proofs.items())},
                "median_proof_lines": median,
                "one_step_proofs": one_step,
            },
            "os_functions": linked,
        })

    index = {
        "schema": "viridis-certificates-index/1",
        "description": (
            "Comparator certificates for Viridis Canon results. Each run directory provides the listed "
            "certificate evidence. This export omits sealed manuscripts. A linked Zenodo DOI is a "
            "manuscript-access link, not a representation that its public PDF is byte-identical to the "
            "sealed manuscript. Each certificate covers only its hash-bound artifacts and stated formal "
            "theorem scope; a different public manuscript requires its own reviewed publication-binding "
            "evidence."
        ),
        "what_a_certificate_establishes": (
            "The listed Lean theorems are proved in the solution file, their statements match the challenge "
            "file, they use only the permitted axioms, and the Lean kernel and the nanoda kernel accept them. "
            "It does not establish that the formal statement captures the paper's prose claim, that the model "
            "describes nature, that the result is new, or that any decision built on it is correct."
        ),
        "depth_rule": DEPTH_RULE,
        "counts": {
            "runs": len(runs),
            "theorems": sum(len(r["theorems"]) for r in runs),
            "substantial": sum(1 for r in runs if r["depth"]["label"] == "substantial"),
            "elementary": sum(1 for r in runs if r["depth"]["label"] == "elementary"),
            "challenge_identical_to_solution": sum(1 for r in runs if r["challenge_identical_to_solution"]),
        },
        "runs": runs,
    }
    return index, configs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if checked-in outputs are stale")
    args = ap.parse_args()
    index, configs = build()
    outputs = dict(configs)
    outputs[CERT_DIR / "index.json"] = json.dumps(index, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    stale = [p for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
    if args.check:
        for p in stale:
            print(f"STALE: {p.relative_to(ROOT)}")
        print("certificates index:", "STALE" if stale else "up to date")
        return 1 if stale else 0
    for p, text in outputs.items():
        p.write_text(text, encoding="utf-8")
    c = index["counts"]
    print(f"wrote certificates/index.json: {c['runs']} runs, {c['theorems']} theorems, "
          f"{c['substantial']} substantial, {c['elementary']} elementary, "
          f"{c['challenge_identical_to_solution']} with challenge identical to solution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
