#!/usr/bin/env python3
"""
Submit the Bridge_EcoChainInstrument canon-to-application module to Aristotle.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 invoke_bridge_ecochain.py
"""
import asyncio, json, os, sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed.", file=sys.stderr)
    sys.exit(2)

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RUN_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-09_aristotle_BridgeEcoChain_run"

PROMPT = """
Validate the Bridge_EcoChainInstrument canon-to-application module.

Critical context: This file is submitted with proof attempts ALREADY
WRITTEN — it is NOT a sorry-stub. Aristotle's job is therefore one of
(a) confirming the existing proofs compile and (b) tightening any that
fail without altering theorem signatures.

Theorem signatures and conclusions must be preserved verbatim. The
four headline theorems are:

  economic_dominance
  agent_architecture_dominance
  enrolled_parcel_positive_EV
  composite_feasibility (corollary)

All four are pure algebraic inequalities over ℝ, derivable from
linarith / nlinarith plus div_lt_div_iff₀ for Theorem 2. The proofs
mirror the parent Conservation Operator module's structure exactly.

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
- 0 sorry across Bridge_EcoChainInstrument.lean
- Axiom audit limited to {propext, Classical.choice, Quot.sound}
- All 4 named theorems compile with stated signatures non-vacuously
- Each theorem's proof traces to definitional unfolding plus standard
  Mathlib tactics (linarith, nlinarith, div_lt_div_iff₀)
- Any structural strengthening must be flagged with rationale in the
  output summary, AND must not collapse a non-trivial conclusion to a
  trivial one.

Non-vacuity guarantees to preserve:
- economic_dominance: the conclusion `development_gain - legal_damages
  < FMV + payment_premium + ECR` is a strict inequality. With
  development_gain = 0 and FMV, payment_premium, ECR, legal_damages
  all positive, conclusion is trivially true; with development_gain
  approaching the threshold, conclusion approaches equality but
  remains strict by `0 < payment_premium`.
- agent_architecture_dominance: identical structural form to
  Conservation Operator's `architecture_dominance`; preserve the
  div_lt_div_iff₀ + nlinarith close.
- enrolled_parcel_positive_EV: direct linarith from h_dom hypothesis.
- composite_feasibility: corollary delegates to the three lemmas via
  refine ⟨_, _, _⟩ pattern. Must NOT collapse to a single Iff.rfl.

If any proof attempt cannot be closed under these constraints, return
the file with the failing proof clearly marked and a diagnostic
explanation, but do NOT alter theorem signatures.
"""

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set", file=sys.stderr)
        return 1
    set_api_key(key)
    print(f"[invoke_be] submitting {RUN_DIR} ...", flush=True)
    project = await Project.create_from_directory(
        prompt=PROMPT.strip(),
        project_dir=str(RUN_DIR),
    )
    print(f"[invoke_be] project_id = {project.project_id}", flush=True)
    print(f"[invoke_be] status     = {project.status}", flush=True)
    meta = {
        "project_id": str(project.project_id),
        "status": str(project.status),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_dir": str(RUN_DIR),
        "toolchain": "leanprover/lean4:v4.28.0",
        "mathlib_rev": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
        "target_theorems": [
            "economic_dominance",
            "agent_architecture_dominance",
            "enrolled_parcel_positive_EV",
            "composite_feasibility",
        ],
    }
    (RUN_DIR / "_run_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[invoke_be] wrote _run_meta.json", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
