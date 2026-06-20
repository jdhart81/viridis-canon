#!/usr/bin/env python3
"""
Submit the KSCT (K-Spectrum Collapse Theorem) Aristotle queue.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 invoke_ksct.py

The key is read from the environment ONLY. It is NEVER persisted. After the
run, unset ARISTOTLE_API_KEY in your shell.

Reads project from:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-06_aristotle_KSCT_run/

Writes the returned project_id and a poll script template to:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-06_aristotle_KSCT_run/_run_meta.json
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed.", file=sys.stderr)
    print("  Install: pip install --break-system-packages aristotlelib", file=sys.stderr)
    sys.exit(2)


HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent  # 01_MATHLIB/Aristotle-Pipeline
KSCT_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-06_aristotle_KSCT_run"

PROMPT = """
Discharge every `sorry` in the KSCT module and return a compiled,
zero-sorry Lean 4 project.

Theorem statements (4 SCPT, 1 CSD, 1 BBP-Lindblad, 1 IB spectral-gap
saturation) MUST be preserved verbatim. You may strengthen auxiliary
definitions or supporting lemmas if a target theorem is not substantively
true under the current definition; flag any such strengthening in your
output summary.

Toolchain: leanprover/lean4:v4.28.0. Mathlib commit pinned to
8f9d9cff6bd728b17a24e163c9402775d9e6a365 (canonical Viridis canon lock).

Acceptance criteria:
- 0 sorry across all KSCT files
- Axiom audit limited to {propext, Classical.choice, Quot.sound}
- All 7 named theorems compile with stated signatures
- Any structural strengthenings are noted in the output summary
"""


async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set in environment.", file=sys.stderr)
        return 1

    set_api_key(key)
    print(f"[invoke_ksct] submitting {KSCT_DIR} ...", flush=True)

    project = await Project.create_from_directory(
        prompt=PROMPT.strip(),
        project_dir=str(KSCT_DIR),
    )

    print(f"[invoke_ksct] project_id = {project.project_id}", flush=True)
    print(f"[invoke_ksct] status     = {project.status}", flush=True)

    meta = {
        "project_id": str(project.project_id),
        "status": str(project.status),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "submitted_dir": str(KSCT_DIR),
        "toolchain": "leanprover/lean4:v4.28.0",
        "mathlib_rev": "8f9d9cff6bd728b17a24e163c9402775d9e6a365",
        "target_theorems": [
            "SCPT_first_order",
            "SCPT_lemma_2",
            "SCPT_lemma_3",
            "SCPT_lemma_4",
            "CSD_critical_slowing",
            "BBP_Lindblad_correspondence",
            "IB_spectral_gap_saturation",
        ],
    }
    meta_path = KSCT_DIR / "_run_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"[invoke_ksct] wrote {meta_path}", flush=True)
    print()
    print(f"To poll: python3 {HERE}/poll_ksct.py")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
