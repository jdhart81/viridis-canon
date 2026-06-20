#!/usr/bin/env python3
"""Poll the in-flight MissionFeasibility Aristotle run."""
import asyncio, json, os, sys
from pathlib import Path

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    sys.exit("ERROR: aristotlelib not installed.")

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent / "_pre-aristotle-drafts" / "2026-05-07_aristotle_MissionFeasibility_run"
META = RUN_DIR / "_run_meta.json"

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        sys.exit("ERROR: ARISTOTLE_API_KEY not set.")
    if not META.exists():
        sys.exit(f"ERROR: {META} missing.")
    set_api_key(key)
    pid = json.loads(META.read_text())["project_id"]
    p = await Project.from_id(pid)
    print(f"project_id = {pid}")
    print(f"status     = {p.status}")
    terminal = {"COMPLETE", "COMPLETE_WITH_ERRORS", "FAILED"}
    if str(p.status).split(".")[-1] not in terminal:
        print("not terminal yet — re-run later.")
        return 0
    out = RUN_DIR / "_aristotle_solution.tar.gz"
    await p.get_solution(destination=str(out))
    print(f"solution written to {out}")
    if hasattr(p, "output_summary"):
        try:
            print("\n--- output_summary ---")
            print(p.output_summary)
        except Exception as e:
            print(f"(could not read output_summary: {e})")
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
