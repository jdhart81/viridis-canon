#!/usr/bin/env python3
"""
Poll the in-flight KSCT Aristotle run and pull the solution tarball when ready.

Reads project_id from:
    01_MATHLIB/Aristotle-Pipeline/_pre-aristotle-drafts/2026-05-06_aristotle_KSCT_run/_run_meta.json

On COMPLETE / COMPLETE_WITH_ERRORS:
    Writes solution to: <KSCT_DIR>/_aristotle_solution.tar.gz

NB: COMPLETE_WITH_ERRORS does NOT mean failed proofs — it can mean Aristotle
made structural improvements to definitions. Always read output_summary
before judging.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed.", file=sys.stderr)
    sys.exit(2)


HERE = Path(__file__).resolve().parent
KSCT_DIR = HERE.parent / "_pre-aristotle-drafts" / "2026-05-06_aristotle_KSCT_run"
META = KSCT_DIR / "_run_meta.json"


async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set.", file=sys.stderr)
        return 1
    if not META.exists():
        print(f"ERROR: {META} missing — invoke_ksct.py first.", file=sys.stderr)
        return 1
    set_api_key(key)

    pid = json.loads(META.read_text())["project_id"]
    p = await Project.from_id(pid)
    print(f"project_id = {pid}")
    print(f"status     = {p.status}")

    terminal = {"COMPLETE", "COMPLETE_WITH_ERRORS", "FAILED"}
    if str(p.status) not in terminal:
        print("not terminal yet — re-run poll_ksct.py later.")
        return 0

    # Pull the solution
    out = KSCT_DIR / "_aristotle_solution.tar.gz"
    await p.get_solution(destination=str(out))
    print(f"solution written to {out}")

    # Summary
    if hasattr(p, "output_summary"):
        try:
            print("\n--- output_summary ---")
            print(p.output_summary)
        except Exception as e:
            print(f"(could not read output_summary: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
