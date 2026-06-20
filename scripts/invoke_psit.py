#!/usr/bin/env python3
"""
Submit the PSIT_Symplectic verification target to Aristotle.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 invoke_psit.py

Reads project from:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-20_aristotle_PSIT_run/
Writes _run_meta.json with project_id.
"""
import asyncio, json, os, sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed "
          "(pip install --break-system-packages aristotlelib).", file=sys.stderr)
    sys.exit(2)

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RUN_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-20_aristotle_PSIT_run"

PROMPT = """
Discharge every `sorry` in PSIT_Symplectic.lean.

Critical context: this file is a SORRY-STUB. Proof bodies are NOT written;
each of the 8 named theorems ends in `:= by sorry`. Your task is to supply
correct proofs. All 8 theorem statements (names, hypotheses, conclusions)
must be preserved VERBATIM.

This module formalizes the linear-algebraic core of Theorem 1 (symplectic
conjugation) and Corollary 1 (no-solo-saturation) of "Symplectic structure
on the slack of an information-rate bound" (Hart 2026, PSIT).

The 8 target theorems:

  omega_skew                 -- omegaᵀ = -omega
  omega_block_nondegenerate  -- omega4.det = 1
  omega_radical_decoh        -- ker(omega) = decoh axis
  conjugate_pairs            -- the (geom,meas) and (rank,mut) pairings
  psit_uniqueness            -- linear Darboux: any nondegenerate alternating
                                4x4 real form is GL-congruent to omega4
  ham_preserves_self         -- omegaForm (hamVF i) (hamVF i) = 0
  ham_moves_conjugate        -- |omegaForm (hamVF i) (hamVF (conj i))| = 1
  no_solo_saturation         -- the conjugate coordinate leaves 0 under flow

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
- 0 `sorry` across PSIT_Symplectic.lean
- Axiom audit limited to {propext, Classical.choice, Quot.sound}
- All 8 named theorems compile with their stated signatures, non-vacuously
- Theorems 1-4, 6-8 are concrete finite computations over an explicit
  5x5 (resp. 4x4) real matrix: `decide`-style evaluation, `Fin` case
  splits, `Matrix.det` unfolding, `norm_num`, `Finset.sum` over `Fin`,
  and `simp` with `omega`/`omega4`/`e`/`omegaForm`/`hamVF`/`conj`/`hamFlow`
  unfolded should close them.

Latitude on `psit_uniqueness` (the one non-elementary theorem):
- You MAY use any Mathlib API for symplectic bases / nondegenerate
  alternating forms, OR construct the change-of-basis matrix M explicitly
  via a symplectic Gram-Schmidt argument.
- You MAY add auxiliary lemmas and definitions, but MUST NOT weaken the
  conclusion (`∃ M, M.det ≠ 0 ∧ Mᵀ * A * M = omega4`) or alter the
  hypotheses (`Aᵀ = -A`, `A.det ≠ 0`).
- If `psit_uniqueness` cannot be closed under these constraints, return the
  file with that ONE proof clearly marked as unresolved and a diagnostic
  explanation, but still discharge the other 7. Do NOT block the other 7.

Non-vacuity guarantees to preserve:
- omega_block_nondegenerate: the conclusion is `det = 1`, a strict
  numerical identity, not `det ≠ 0` weakened to a triviality.
- omega_radical_decoh: this is an iff; both directions must be proved. The
  reverse direction shows the decoh axis IS in the radical; the forward
  direction shows NOTHING ELSE is.
- ham_moves_conjugate: the conclusion `|...| = 1` is a strict identity; the
  hypothesis `i ≠ 4` is used (for i = 4 it would be false).
- no_solo_saturation: the hypothesis `p (conj i) = 0` is satisfiable and the
  conclusion `≠ 0` is substantive; verify the proof genuinely uses the
  unit-rate fact from ham_moves_conjugate.

If you strengthen any auxiliary definition, flag it with rationale in the
output summary; do not collapse any non-trivial conclusion to a trivial one.
""".strip()

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set", file=sys.stderr)
        return 1
    set_api_key(key)
    print(f"[invoke_psit] submitting {RUN_DIR} ...", flush=True)
    project = await Project.create_from_directory(
        prompt=PROMPT,
        project_dir=str(RUN_DIR),
    )
    print(f"[invoke_psit] project_id = {project.project_id}", flush=True)
    print(f"[invoke_psit] status     = {project.status}", flush=True)
    meta = {
        "project_id": str(project.project_id),
        "status": str(project.status),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_dir": str(RUN_DIR),
        "toolchain": "leanprover/lean4:v4.28.0",
        "mathlib_rev": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
        "target_theorems": [
            "omega_skew",
            "omega_block_nondegenerate",
            "omega_radical_decoh",
            "conjugate_pairs",
            "psit_uniqueness",
            "ham_preserves_self",
            "ham_moves_conjugate",
            "no_solo_saturation",
        ],
    }
    (RUN_DIR / "_run_meta.json").write_text(json.dumps(meta, indent=2))
    print("[invoke_psit] wrote _run_meta.json", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
