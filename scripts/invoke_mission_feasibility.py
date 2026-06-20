#!/usr/bin/env python3
"""
Submit the MissionFeasibility bridge theorem to Aristotle.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 invoke_mission_feasibility.py

Reads project from:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-07_aristotle_MissionFeasibility_run/
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
RUN_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-07_aristotle_MissionFeasibility_run"

PROMPT = """
Validate the MissionFeasibility bridge theorem module.

Critical context: This file is submitted with proof attempts ALREADY
WRITTEN — it is NOT a sorry-stub. Aristotle's job is therefore one of
(a) confirming the existing proofs compile and (b) tightening any that
fail.

Theorem signatures and conclusions must be preserved verbatim. The
forward direction (`feasibility_implies_rate_ceiling`) MUST derive its
conclusion from the structural definitions of `Feasible`, `Completes`,
and `OperatesWithin` — NOT by accepting the conclusion as a hypothesis.
The backward direction (`rate_ceiling_implies_feasible`) MUST construct
an explicit witness agent. Vacuous closures (e.g., conclusions that
are propositionally equal to a hypothesis) are NOT acceptable.

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
- 0 sorry across MissionFeasibility.lean
- Axiom audit limited to {propext, Classical.choice, Quot.sound}
- All 5 named theorems compile with stated signatures non-vacuously
- Each theorem's proof traces to definitional unfolding plus standard
  Mathlib tactics (linarith, simp, simpa, div_le_iff, etc.)
- Any structural strengthening must be flagged with rationale in the
  output summary, AND must not collapse a non-trivial conclusion to a
  trivial one
"""

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set", file=sys.stderr)
        return 1
    set_api_key(key)
    print(f"[invoke_mf] submitting {RUN_DIR} ...", flush=True)
    project = await Project.create_from_directory(
        prompt=PROMPT.strip(),
        project_dir=str(RUN_DIR),
    )
    print(f"[invoke_mf] project_id = {project.project_id}", flush=True)
    print(f"[invoke_mf] status     = {project.status}", flush=True)
    meta = {
        "project_id": str(project.project_id),
        "status": str(project.status),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_dir": str(RUN_DIR),
        "toolchain": "leanprover/lean4:v4.28.0",
        "mathlib_rev": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
        "target_theorems": [
            "feasibility_implies_rate_ceiling",
            "feasibility_implies_dscore_in_unit",
            "rate_ceiling_implies_feasible",
            "mission_feasibility",
            "minimum_feasibility_power",
        ],
    }
    (RUN_DIR / "_run_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"[invoke_mf] wrote _run_meta.json", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
