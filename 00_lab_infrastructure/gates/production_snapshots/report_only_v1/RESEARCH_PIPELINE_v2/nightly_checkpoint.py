"""Record and enforce a scheduled invocation's actual foundry progress.

This local guard never submits a proof, generates a paper, or publishes.
The immutable start receipt makes a no-progress invocation observable even
when the controller has no deterministic transition to execute.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from autonomous_pipeline_controller import build_state
from science_foundry_continuity import evaluate


HERE = Path(__file__).resolve().parent
CHECKPOINTS = HERE / "nightly_checkpoints"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(start: dict, current: dict, pipeline: dict) -> dict:
    before = start["science"]
    before_debt = before["certification"]["backlog_runs"]
    after_debt = current["certification"]["backlog_runs"]
    cleared = [run for run in before_debt
               if run in current["certification"]["certified_runs"]]
    target = min(2, len(before_debt))
    target_runs = before_debt[:target]
    package_work = [item for item in pipeline['items']
                    if not item.get('human_gate')
                    and item.get('state') not in {'VIRIDISOS_TRACKED', 'CERTIFICATE_REQUIRED'}]
    incidents = []
    generation = current["generation"]
    if not generation["ready"]:
        incidents.append("HOLD_GENERATION_PREFLIGHT")
    if generation["due"]:
        incidents.append("HOLD_DUE_NIGHTLY_PAPER_NOT_SEALED")
    if not generation["fresh"]:
        incidents.append("HOLD_GENERATION_STALE")
    certification = current["certification"]
    if not certification["ready"]:
        incidents.append("HOLD_CERTIFIER_UNAVAILABLE")
    if not certification["recent"]:
        incidents.append("HOLD_CERTIFICATION_OVERDUE")
    if any(run not in cleared for run in target_runs):
        incidents.append("HOLD_FIFO_CERTIFICATION_TARGET_NOT_MET")
    if len(after_debt) > certification["backlog_critical"]:
        incidents.append("HOLD_CERTIFICATION_BACKLOG_CRITICAL")
    if package_work:
        incidents.append('HOLD_REVERSIBLE_PACKAGE_WORK_REMAINS')
    return {
        "standard": "VRS-NIGHTLY-CHECKPOINT-1",
        "invocation_id": start["invocation_id"],
        "started_at_utc": start["started_at_utc"],
        "completed_at_utc": current["evaluated_at_utc"],
        "status": "HOLD_NIGHTLY_PROGRESS" if incidents else "NIGHTLY_PROGRESS_PASS",
        "incidents": incidents,
        "generation": generation,
        "certification": {
            "target": target,
            "target_runs": target_runs,
            "cleared_prior_debt": cleared,
            "remaining_debt": after_debt,
            "recent": certification["recent"],
            "ready": certification["ready"],
        },
        "submission_ready_packages": pipeline["counts"]["submission_ready_packages"],
        "unresolved_package_work": package_work,
        "agent_owned_actions": [item for item in pipeline["items"]
                                if not item.get("human_gate")
                                and item.get("state") != "VIRIDISOS_TRACKED"],
        "truth_boundary": "Progress is measured from current validated certificates and sealed runs; a receipt refresh or executor exit zero is not progress.",
        "external_mutation": False,
    }


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # A crash must not leave a partially written canonical receipt. Link a
    # complete same-filesystem temporary file exclusively; never replace history.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(value, indent=2, sort_keys=True) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_start(path: Path) -> dict:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError('checkpoint symlink refused')
    start = json.loads(path.read_text(encoding='utf-8'))
    if start.get('standard') != 'VRS-NIGHTLY-CHECKPOINT-1' or start.get('invocation_id') != path.parent.name:
        raise ValueError('checkpoint identity mismatch')
    started = dt.datetime.fromisoformat(start['started_at_utc'])
    if started.tzinfo is None:
        raise ValueError('checkpoint timestamp is invalid')
    return start



def verification_coverage_after_checkpoint(output):
    # Observe after the immutable checkpoint has been written, including replay.
    try:
        import subprocess
        command = [sys.executable, str(HERE / "verification_coverage_gates/run_flow.py"),
                   "--root", str(HERE.parent), "--checkpoint", str(output), "--report-only"]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=300)
        print(json.dumps({"verification_coverage_hook": {"mode": "REPORT_ONLY",
            "status": "REPORTED" if completed.returncode == 0 else "HOLD",
            "returncode": completed.returncode, "report": completed.stdout.strip(),
            "errors": completed.stderr.strip(), "enforcement": False}}), file=sys.stderr)
    except Exception as exc:
        print(json.dumps({"verification_coverage_hook": {"mode": "REPORT_ONLY", "status": "HOLD",
            "enforcement": False, "error": type(exc).__name__ + ": " + str(exc)}}), file=sys.stderr)


def return_existing_finish(path: Path, start: dict) -> int:
    output = path.parent / 'FINISH.json'
    if output.is_symlink():
        raise ValueError('checkpoint finish symlink refused')
    result = json.loads(output.read_text(encoding='utf-8'))
    if (result.get('invocation_id') != start['invocation_id']
            or result.get('start_receipt_sha256') != digest(path)):
        raise ValueError('finished checkpoint does not bind original start')
    verification_coverage_after_checkpoint(output)
    print(json.dumps({**result, 'finish_receipt': str(output), 'replayed': True}, indent=2, sort_keys=True))
    return 2 if result['incidents'] else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--begin", metavar="INVOCATION_ID")
    group.add_argument("--finish", type=Path, metavar="START_RECEIPT")
    args = parser.parse_args()
    try:
        if args.begin:
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", args.begin):
                raise ValueError("invalid invocation id")
            path = CHECKPOINTS / args.begin / "START.json"
            if path.exists():
                start = read_start(path)
                if (path.parent / 'FINISH.json').exists():
                    return return_existing_finish(path, start)
                print(json.dumps({'status': 'CHECKPOINT_RESUMED', 'start_receipt': str(path),
                                  'started_at_utc': start['started_at_utc'],
                                  'generation_due': start['science']['generation']['due'],
                                  'fifo_debt': start['science']['certification']['backlog_runs'],
                                  'next_action': 'recheck live state before work; original baseline retained'}, indent=2))
                return 0
            current = evaluate()
            start = {
                "standard": "VRS-NIGHTLY-CHECKPOINT-1",
                "invocation_id": args.begin,
                "started_at_utc": current["evaluated_at_utc"],
                "science": current,
                "external_mutation": False,
            }
            write_new(path, start)
            print(json.dumps({"status": "CHECKPOINT_STARTED", "start_receipt": str(path),
                              "generation_due": current["generation"]["due"],
                              "generation_window": current["generation"]["window"],
                              "fifo_debt": current["certification"]["backlog_runs"]}, indent=2))
            return 0
        path = args.finish.resolve()
        if not path.is_relative_to(CHECKPOINTS.resolve()) or path.name != "START.json":
            raise ValueError("start receipt must be inside the canonical checkpoint directory")
        start = read_start(path)
        if (path.parent / 'FINISH.json').exists():
            return return_existing_finish(path, start)
        current = evaluate()
        started = dt.datetime.fromisoformat(start["started_at_utc"])
        observed = dt.datetime.fromisoformat(current["evaluated_at_utc"])
        if started.tzinfo is None or observed < started:
            raise ValueError("checkpoint timestamp is invalid")
        result = assess(start, current, build_state())
        result["start_receipt_sha256"] = digest(path)
        output = path.parent / "FINISH.json"
        write_new(output, result)
        verification_coverage_after_checkpoint(output)
        print(json.dumps({**result, "finish_receipt": str(output)}, indent=2, sort_keys=True))
        return 2 if result["incidents"] else 0
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD_NIGHTLY_CHECKPOINT", "error": str(exc), "external_mutation": False}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
