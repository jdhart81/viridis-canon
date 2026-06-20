#!/usr/bin/env python3
"""
Poll Aristotle for ConservationOperator project status and download
results when ready.

Usage:
    export ARISTOTLE_API_KEY="arstl_..."
    python3 poll_conservation_operator.py
"""
import asyncio, json, os, sys
from pathlib import Path

try:
    from aristotlelib import set_api_key, Project
except ImportError:
    print("ERROR: aristotlelib not installed.", file=sys.stderr)
    sys.exit(2)

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RUN_DIR = PIPELINE / "_pre-aristotle-drafts" / "2026-05-09_aristotle_ConservationOperator_run"
META = RUN_DIR / "_run_meta.json"

OUT_DIR = PIPELINE.parent.parent / "new leans" / "2026-05-09_aristotle_ConservationOperator_run_aristotle"

async def main() -> int:
    key = os.environ.get("ARISTOTLE_API_KEY")
    if not key:
        print("ERROR: ARISTOTLE_API_KEY not set", file=sys.stderr)
        return 1
    if not META.exists():
        print(f"ERROR: missing {META} — run invoke first", file=sys.stderr)
        return 1
    set_api_key(key)
    meta = json.loads(META.read_text())
    project_id = meta["project_id"]
    print(f"[poll_co] project_id = {project_id}", flush=True)
    project = await Project.from_id(project_id)
    print(f"[poll_co] status     = {project.status}", flush=True)
    if str(project.status).lower() in ("completed", "succeeded", "done"):
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        await project.download_to_directory(str(OUT_DIR))
        print(f"[poll_co] downloaded to {OUT_DIR}", flush=True)
        meta["downloaded_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        meta["download_dir"] = str(OUT_DIR)
        META.write_text(json.dumps(meta, indent=2))
    elif str(project.status).lower() in ("failed", "error"):
        print(f"[poll_co] FAILED: see project page", flush=True)
        return 2
    else:
        print(f"[poll_co] still running — poll again later", flush=True)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
