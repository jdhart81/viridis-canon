#!/usr/bin/env python3
"""
poll_p3.py — Standalone Aristotle follow-up poller for P3 Impossibility run.

Runs the full new-leans workflow when project a55260c8 completes:
  - Pulls the compiled artifact into `new leans/P3_2026-04-25/`
  - Verifies zero `sorry` and that all 4 named theorems remain
  - Promotes to Aristotle-Pipeline/P3_Impossibility.lean
  - Updates lakefile.toml, README.md
  - Logs a milestone entry

Usage
-----
    # Set the key in your shell first (rotate after any chat exposure):
    export ARISTOTLE_API_KEY=arstl_...

    # Then either poll once and exit:
    python3 poll_p3.py

    # ...or run in a loop until the project completes (every 30 min):
    python3 poll_p3.py --watch

This script is intentionally standalone — no Cowork dependencies. Run from
any terminal with Python 3.10+ and aristotlelib installed
(`pip install aristotlelib`).
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ID = "a55260c8-fe1b-4a69-ad96-22d3ae1a5495"
WORKSPACE = Path("/Users/justinhart/Desktop/Cowork /Viridis Core docs  2.0")
PIPELINE_DIR = WORKSPACE / "01_MATHLIB" / "Aristotle-Pipeline"
PRE_DRAFTS = PIPELINE_DIR / "_pre-aristotle-drafts"
NEW_LEANS = WORKSPACE / "new leans"
LOG_FILE = PRE_DRAFTS / "P3_FOLLOWUP_LOG.md"
TIGHTENED_SKELETON = PRE_DRAFTS / "P3_Impossibility_sorry_v2_tightened.lean"

REQUIRED_THEOREMS = [
    "proxy_misalignment_implies_dscore_loss",
    "goodhart_inevitable",
    "alignment_is_feasibility",
    "corrigibility_under_IB",
]


def log(msg: str) -> None:
    """Append a timestamped line to the follow-up log."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    line = f"- [{ts}] {msg}\n"
    print(line, end="")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def get_key() -> str:
    key = os.environ.get("ARISTOTLE_API_KEY", "").strip()
    if not key:
        sys.exit("ERROR: ARISTOTLE_API_KEY env var not set. Export it first.")
    return key


async def fetch_project():
    from aristotlelib import set_api_key, Project
    set_api_key(get_key())
    return await Project.from_id(PROJECT_ID)


async def pull_solution(p, dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    return await p.get_solution(destination=str(dest))


def verify_compiled(lean_path: Path) -> tuple[bool, list[str]]:
    """Return (ok, issues) where ok=True means promotion is safe."""
    issues = []
    text = lean_path.read_text(encoding="utf-8")
    n_sorry = text.count("sorry")
    if n_sorry > 0:
        issues.append(f"found {n_sorry} `sorry` token(s) — expected zero")
    for thm in REQUIRED_THEOREMS:
        if thm not in text:
            issues.append(f"missing theorem `{thm}`")
    return (len(issues) == 0, issues)


def promote(compiled_path: Path, summary: str) -> None:
    """Move the compiled file into the canonical Aristotle-Pipeline location."""
    archive_dir = PRE_DRAFTS / "2026-04-25_aristotle_P3_run"
    archive_dir.mkdir(parents=True, exist_ok=True)

    if TIGHTENED_SKELETON.exists():
        shutil.copy2(TIGHTENED_SKELETON, archive_dir / TIGHTENED_SKELETON.name)

    summary_file = archive_dir / "ARISTOTLE_SUMMARY_P3.md"
    summary_file.write_text(summary or "(no output_summary returned)\n", encoding="utf-8")

    target = PIPELINE_DIR / "P3_Impossibility.lean"
    shutil.copy2(compiled_path, target)
    log(f"PROMOTED → {target.relative_to(WORKSPACE)}")
    log(f"ARCHIVED → {archive_dir.relative_to(WORKSPACE)}")

    # Update lakefile.toml
    lakefile = PIPELINE_DIR / "lakefile.toml"
    text = lakefile.read_text(encoding="utf-8")
    if "P3_Impossibility" not in text:
        text = text.replace(
            'defaultTargets = ["P0_IntelligenceBound_COMPILED", "P1_DScore", "P2_HDFM_POC", "P4_ThermodynamicEconomics", "P9_AI_Safety"]',
            'defaultTargets = ["P0_IntelligenceBound_COMPILED", "P1_DScore", "P2_HDFM_POC", "P3_Impossibility", "P4_ThermodynamicEconomics", "P9_AI_Safety"]',
        )
        text += '\n[[lean_lib]]\nname = "P3_Impossibility"\nglobs = ["P3_Impossibility"]\n'
        lakefile.write_text(text, encoding="utf-8")
        log("UPDATED lakefile.toml (added P3_Impossibility)")

    # Update README status table
    readme = PIPELINE_DIR / "README.md"
    rtxt = readme.read_text(encoding="utf-8")
    if "**P3**" not in rtxt:
        rtxt = rtxt.replace(
            "| **P2** | `P2_HDFM_POC.lean` | **0** | COMPILED | HDFM resubmission |",
            "| **P2** | `P2_HDFM_POC.lean` | **0** | COMPILED | HDFM resubmission |\n"
            "| **P3** | `P3_Impossibility.lean` | **0** | COMPILED | 2nd canon paper (Impossibility) |",
        )
        readme.write_text(rtxt, encoding="utf-8")
        log("UPDATED README.md status table (added P3 row)")


async def run_once() -> str:
    """One poll cycle. Returns the project status as a string."""
    p = await fetch_project()
    status = str(p.status).rsplit(".", 1)[-1]
    pct = p.percent_complete
    log(f"status={status} percent={pct}")

    if status in {"NOT_STARTED", "QUEUED", "IN_PROGRESS"}:
        return status

    if status in {"FAILED", "CANCELED", "OUT_OF_BUDGET"}:
        log(f"TERMINAL FAILURE — output_summary: {(p.output_summary or '')[:500]}")
        return status

    # COMPLETE or COMPLETE_WITH_ERRORS — pull artifact
    pull_dest = NEW_LEANS / "P3_2026-04-25"
    pulled = await pull_solution(p, pull_dest)
    log(f"PULLED → {pull_dest.relative_to(WORKSPACE)} (returned: {pulled})")

    # Find the .lean file inside
    lean_files = list(pull_dest.rglob("P3_Impossibility.lean"))
    if not lean_files:
        log("ERROR: no P3_Impossibility.lean found in pulled archive — manual review needed")
        return status

    compiled = lean_files[0]
    ok, issues = verify_compiled(compiled)

    if not ok or status == "COMPLETE_WITH_ERRORS":
        log("VERIFICATION FAILED or PARTIAL — not promoting")
        for i in issues:
            log(f"  · {i}")
        return status

    promote(compiled, p.output_summary or "")
    log("✅ P3 PROMOTED — 6/9 canon now compiled")
    return status


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="Loop every 30 min until terminal status.")
    args = ap.parse_args()

    if not args.watch:
        await run_once()
        return 0

    while True:
        status = await run_once()
        if status not in {"NOT_STARTED", "QUEUED", "IN_PROGRESS"}:
            log("WATCH LOOP EXITING — terminal status reached")
            return 0
        time.sleep(1800)  # 30 minutes


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
