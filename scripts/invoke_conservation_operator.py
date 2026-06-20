#!/usr/bin/env python3
"""
Submit the ConservationOperator canon-candidate module to Aristotle.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 invoke_conservation_operator.py

Reads project from:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-09_aristotle_ConservationOperator_run/
Writes _run_meta.json with project_id.
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
RUN_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-09_aristotle_ConservationOperator_run"

PROMPT = """
Validate the ConservationOperator canon-candidate module.

Critical context: This file is submitted with proof attempts ALREADY
WRITTEN — it is NOT a sorry-stub. Aristotle's job is therefore one of
(a) confirming the existing proofs compile and (b) tightening any that
fail without altering theorem signatures.

Theorem signatures and conclusions must be preserved verbatim. The
four headline theorems are:

  positive_EV
  yield_concentration
  architecture_dominance
  architecture_dominance_under_asymmetric_reward (corollary)

Plus three structural restatements of the IntelligenceBound `cap`
function:

  cap_nonneg
  cap_strictMono_D
  cap_strictMono_P

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
- 0 sorry across ConservationOperator.lean
- Axiom audit limited to {propext, Classical.choice, Quot.sound}
- All 7 named theorems compile with stated signatures non-vacuously
- Each theorem's proof traces to definitional unfolding plus standard
  Mathlib tactics (linarith, nlinarith, setIntegral_mono_on,
  integral_add_compl, div_lt_div_iff, etc.)
- Any structural strengthening must be flagged with rationale in the
  output summary, AND must not collapse a non-trivial conclusion to a
  trivial one.

Non-vacuity guarantees to preserve:
- positive_EV: the conclusion `0 < ∫ X dμ` is a strict positivity claim
  on the integral, NOT propositional equality with a hypothesis.
- yield_concentration: the conclusion `(∫ X) - T ≤ ∫ X over {X > T}`
  is a substantive truncation bound. Verify by checking that with
  X = constant c > 0 and T = 0 the conclusion gives c - 0 ≤ c
  (trivially true but non-vacuous), and with X = c and T = c the
  conclusion gives 0 ≤ 0 (boundary, non-trivially true).
- architecture_dominance: the hypothesis `D · cost_D < P · cost_P` can
  fail, in which case the conclusion is not derivable. Verify that
  the proof actually uses the hypothesis (it must, or the conclusion
  would be false in counter-examples).

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
    print(f"[invoke_co] submitting {RUN_DIR} ...", flush=True)
    project = await Project.create_from_directory(
        prompt=PROMPT.strip(),
        project_dir=str(RUN_DIR),
    )
    print(f"[invoke_co] project_id = {project.project_id}", flush=True)
    print(f"[invoke_co] status     = {project.status}", flush=True)
    meta = {
        "project_id": str(project.project_id),
        "status": str(project.status),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_dir": str(RUN_DIR),
        "toolchain": "leanprover/lean4:v4.28.0",
        "mathlib_rev": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
        "target_theorems": [
            "cap_nonneg",
            "cap_strictMono_D",
            "cap_strictMono_P",
            "positive_EV",
            "yield_concentration",
            "architecture_dominance",
            "architecture_dominance_under_asymmetric_reward",
        ],
    }
    (RUN_DIR / "_run_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[invoke_co] wrote _run_meta.json", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
