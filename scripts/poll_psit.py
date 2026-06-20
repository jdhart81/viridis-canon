#!/usr/bin/env python3
"""
Poll the PSIT_Symplectic Aristotle run and pull the solution when ready.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 poll_psit.py            # reads project_id from _run_meta.json
    python3 poll_psit.py <id>       # or pass an explicit project_id
"""
import asyncio, json, sys
from pathlib import Path

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed.", file=sys.stderr)
    sys.exit(2)

import os
HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent / "_pre-aristotle-drafts" / "2026-05-20_aristotle_PSIT_run"
META = RUN_DIR / "_run_meta.json"

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set", file=sys.stderr)
        return 1
    set_api_key(key)
    pid = sys.argv[1] if len(sys.argv) > 1 else json.loads(META.read_text())["project_id"]
    p = await Project.from_id(pid)
    print(f"[poll_psit] project {pid} status = {p.status}", flush=True)
    if str(p.status).upper().startswith(("COMPLETE", "DONE", "FINISHED")):
        out = RUN_DIR / "psit_solution.tar.gz"
        await p.get_solution(destination=str(out))
        print(f"[poll_psit] solution written to {out}", flush=True)
        summary = getattr(p, "output_summary", None)
        if summary:
            print("---- output_summary ----")
            print(summary)
    else:
        print("[poll_psit] not ready yet — re-run later.", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
