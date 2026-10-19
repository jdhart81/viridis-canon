#!/usr/bin/env python3
"""Drain deterministic, reversible Viridis research-pipeline transitions.

The autonomous controller is the authority for *what* should happen next.
This executor supplies the missing mechanical layer for transitions that
already have deterministic local writers. It deliberately does not perform
scientific authorship, independent review, Comparator transmission, rights or
ledger assignment, publication, Git push, Canon-spine mutation, or deployment.

An agent invocation consumes ``judgment_required`` work, then reruns this
executor. Exact human gates remain visible and fail closed.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable
from zoneinfo import ZoneInfo

from autonomous_pipeline_controller import build_state


HERE = Path(__file__).resolve().parent
CONTROL_ROOT = HERE.parent
DEFAULT_RECEIPT = HERE / "AUTONOMOUS_TRANSITION_EXECUTOR_STATUS.json"

# These transitions are deterministic, local, reversible, and already
# implemented by fail-closed stage writers. Anything absent from this map is
# intentionally left to an agent or to an exact human authorization surface.
DETERMINISTIC_ACTIONS = {
    "CREATE_VERSIONED_VERIFICATION_METADATA_CORRECTION",
    "CREATE_VERSIONED_CORRECTION_OVERLAY",
    "FINALIZE_REVIEWED_PACKAGE",
    "RUN_CANON_AND_PRODUCT_ROUTE",
    "BUILD_VIRIDISOS_KERNEL_PACKAGE",
    "ASSEMBLE_AUGMENT_AND_VERIFY_SUBMISSION_PACKAGE",
}

JUDGMENT_ACTIONS = {
    "CERTIFY_COMPARATOR_FIFO",
    "CREATE_VERSIONED_PRE_CURATOR_PAPER_CORRECTION",
    "CURATE_PROOF_RECONCILED_DRAFT",
    "REVIEW_PRIOR_INVOCATION_DRAFT",
    "REVIEW_KERNEL_ADMISSION",
    "PREPARE_VERSIONED_KERNEL_ADMISSION_CORRECTION",
    "REVIEW_EXISTING_KERNEL_PACKAGE_BINDINGS",
    "SEAL_EXISTING_DOI_GIT_IDENTITY",
    "PREPARE_LICENSE_LEDGER_AND_HASH_SURFACE",
    "VERIFY_WRAPPER_OR_EXPLICIT_BACKLOG",
}

BANNED_ARGUMENTS = {
    "--go",
    "--publish",
    "--justin-authorized",
    "--bind-ledger",
    "--promote-ledger-cleared",
}


class ExecutorError(RuntimeError):
    """A fail-closed executor error safe to surface."""


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    returncode: int
    stdout_sha256: str
    stderr_sha256: str
    stdout_tail: str
    stderr_tail: str


class WriterFailure(ExecutorError):
    """Retain exact command diagnostics and a narrowly established hold scope."""

    def __init__(self, result: CommandResult, *, object_local: bool = False):
        self.result = result
        self.object_local = object_local
        super().__init__(
            f"local writer failed ({result.returncode}): {' '.join(result.argv[1:])}; "
            f"stdout={result.stdout_tail!r}; stderr={result.stderr_tail!r}"
        )


# These exact kernel-packager refusals occur before any package write. Unknown
# diagnostics (including hash, authority, path, immutable-write and process
# failures) remain global stops. No other writer gains continuation semantics.
OBJECT_LOCAL_KERNEL_HOLDS = {
    "HOLD_REVIEW_STATUS_CONTRADICTION: finalized manuscript still says "
    "its independent review is pending; preserve the sealed package and "
    "prepare a corrected successor with a later independent review",
    "all scientific probes must be recorded and resolved",
    "unresolved empirical dependency must remain HOLD, not NO_RUNTIME_KERNEL",
    "product no-runtime route requires a matching admission verdict",
    "runtime role is unresolved; missing wrapper requires review, not NO_RUNTIME_KERNEL",
}


def object_local_kernel_hold(result: CommandResult, stdout: str, stderr: str) -> bool:
    argv = result.argv
    if (result.returncode != 2 or stderr or len(argv) != 4
            or argv[:3] != [sys.executable, str(HERE / "viridisos_kernel_packager.py"), "--run"]
            or re.fullmatch(r"Run-\d{3,}", argv[3]) is None):
        return False
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate diagnostic key")
            value[key] = item
        return value
    try:
        value = json.loads(stdout, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        return False
    return (isinstance(value, dict)
            and set(value) == {"status", "error", "external_mutation"}
            and value["status"] == "HOLD" and value["external_mutation"] is False
            and isinstance(value["error"], str) and value["error"] in OBJECT_LOCAL_KERNEL_HOLDS)


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def persist_receipt(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Preserve a stable checkpoint; command attempts remain distinct events."""
    # Compare only after drain has rebuilt current state. Do not reuse old
    # controller results or suppress the record of an executed/failed writer.
    if path.is_file() and not result.get("executed") and not result.get("holds"):
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict):
            raise ExecutorError("existing executor receipt must be a JSON object")
        ignored = {"started_at_utc", "completed_at_utc"}
        if (
            {key: value for key, value in existing.items() if key not in ignored}
            == {key: value for key, value in result.items() if key not in ignored}
        ):
            return existing
    write_json_atomic(path, result)
    return result


def local_date() -> str:
    return datetime.now(ZoneInfo("America/Denver")).date().isoformat()


def command_plan(action: str, run_id: str, date: str) -> list[list[str]]:
    python = sys.executable
    if action == "CREATE_VERSIONED_VERIFICATION_METADATA_CORRECTION":
        return [[python, str(HERE / "post_aristotle_curator.py"), "--correct-verification-metadata", run_id]]
    if action == "CREATE_VERSIONED_CORRECTION_OVERLAY":
        return [[python, str(HERE / "post_aristotle_curator.py"), "--repair-hold", run_id]]
    if action == "FINALIZE_REVIEWED_PACKAGE":
        return [[python, str(HERE / "post_aristotle_curator.py"), "--finalize", run_id]]
    if action == "RUN_CANON_AND_PRODUCT_ROUTE":
        return [[python, str(HERE / "canon_product_router.py"), "--run", run_id]]
    if action == "BUILD_VIRIDISOS_KERNEL_PACKAGE":
        return [[python, str(HERE / "viridisos_kernel_packager.py"), "--run", run_id],
                [python, str(HERE / "conservation_app_intake.py"), "--run", run_id]]
    if action == "ASSEMBLE_AUGMENT_AND_VERIFY_SUBMISSION_PACKAGE":
        return [
            [python, str(HERE / "assemble_saturday_candidate.py"), "--run", run_id, "--date", date],
            [python, str(HERE / "augment_release_candidate.py"), "--run", run_id, "--date", date],
        ]
    raise ExecutorError(f"no deterministic writer is registered for {action}")


def validate_command(argv: list[str]) -> None:
    if not argv or Path(argv[0]).resolve() != Path(sys.executable).resolve():
        raise ExecutorError("executor commands must use the current Python interpreter")
    if len(argv) < 2:
        raise ExecutorError("executor command is missing its script")
    script = Path(argv[1]).resolve()
    try:
        script.relative_to(HERE.resolve())
    except ValueError as exc:
        raise ExecutorError(f"executor script escapes the pipeline root: {script}") from exc
    forbidden = sorted(BANNED_ARGUMENTS.intersection(argv))
    if forbidden:
        raise ExecutorError("irreversible or authorization-bearing arguments are forbidden: " + ", ".join(forbidden))


def output_tail(value: str, limit: int = 2000) -> str:
    return value[-limit:]


def run_command(argv: list[str], timeout_seconds: int = 300) -> CommandResult:
    validate_command(argv)
    completed = subprocess.run(
        argv,
        cwd=CONTROL_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )
    result = CommandResult(
        argv=argv,
        returncode=completed.returncode,
        stdout_sha256=hashlib.sha256(completed.stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(completed.stderr.encode()).hexdigest(),
        stdout_tail=output_tail(completed.stdout),
        stderr_tail=output_tail(completed.stderr),
    )
    if completed.returncode != 0:
        raise WriterFailure(
            result, object_local=object_local_kernel_hold(result, completed.stdout, completed.stderr),
        )
    return result


def item_for(state: dict[str, Any], run_id: str) -> dict[str, Any] | None:
    return next(
        (row for row in state.get("items", []) if isinstance(row, dict) and row.get("run_id") == run_id),
        None,
    )


def classify_remaining(state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    judgment: list[dict[str, Any]] = []
    human: list[dict[str, Any]] = []
    for row in state.get("items", []):
        if not isinstance(row, dict) or row.get("state") == "VIRIDISOS_TRACKED":
            continue
        if row.get("human_gate") is True:
            human.append(row)
        elif row.get("next_action") not in DETERMINISTIC_ACTIONS:
            judgment.append(row)
    return judgment, human


def drain(
    *,
    apply: bool,
    date: str,
    max_transitions: int,
    state_builder: Callable[[], dict[str, Any]] = build_state,
    command_runner: Callable[[list[str]], CommandResult] = run_command,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    executed: list[dict[str, Any]] = []
    planned: list[dict[str, Any]] = []
    holds: list[dict[str, Any]] = []
    failed_runs: set[str] = set()

    for _ in range(max_transitions):
        before = state_builder()
        unknown = next((row for row in before.get("items", [])
                        if isinstance(row, dict) and row.get("human_gate") is False
                        and row.get("next_action") not in DETERMINISTIC_ACTIONS | JUDGMENT_ACTIONS), None)
        if unknown is not None:
            holds.append({"run_id": unknown.get("run_id"), "action": unknown.get("next_action"),
                          "error": "unknown machine action semantics; entire invocation stopped",
                          "scope": "GLOBAL"})
            break
        candidate = next(
            (
                row for row in before.get("items", [])
                if isinstance(row, dict)
                and row.get("human_gate") is False
                and row.get("next_action") in DETERMINISTIC_ACTIONS
                and row.get("run_id") not in failed_runs
            ),
            None,
        )
        if candidate is None:
            break
        run_id = str(candidate["run_id"])
        action = str(candidate["next_action"])
        commands = command_plan(action, run_id, date)
        planned.append({"run_id": run_id, "action": action, "commands": commands})
        if not apply:
            # A dry run lists the next eligible deterministic action without
            # looping forever on unchanged state.
            break

        results: list[CommandResult] = []
        try:
            for argv in commands:
                results.append(command_runner(argv))
        except WriterFailure as exc:
            holds.append({"run_id": run_id, "action": action, "error": str(exc),
                          "scope": "OBJECT" if exc.object_local else "GLOBAL",
                          "completed_commands": [asdict(result) for result in results],
                          "failed_command": asdict(exc.result)})
            if not exc.object_local:
                break
            # Do not retry this object or any later stage for it during this
            # invocation. Rebuild controller truth before unrelated work.
            failed_runs.add(run_id)
            continue
        except (ExecutorError, OSError, subprocess.SubprocessError) as exc:
            holds.append({"run_id": run_id, "action": action, "error": str(exc), "scope": "GLOBAL",
                          "completed_commands": [asdict(result) for result in results]})
            break

        after = state_builder()
        next_item = item_for(after, run_id)
        next_action = next_item.get("next_action") if next_item else None
        executed.append(
            {
                "run_id": run_id,
                "action": action,
                "commands": [asdict(result) for result in results],
                "next_action": next_action,
            }
        )
        if next_action == action:
            holds.append(
                {
                    "run_id": run_id,
                    "action": action,
                    "error": "writer returned success but controller state did not advance",
                }
            )
            break

    final_state = state_builder()
    judgment, human = classify_remaining(final_state)
    deterministic_remaining = [
        row for row in final_state.get("items", [])
        if isinstance(row, dict)
        and row.get("human_gate") is False
        and row.get("next_action") in DETERMINISTIC_ACTIONS
    ]
    if holds:
        status = "HOLD_EXECUTOR_ERROR"
    elif not apply:
        status = "DRY_RUN"
    elif deterministic_remaining:
        status = "LOCAL_TRANSITION_LIMIT_REACHED"
    elif judgment:
        status = "AGENT_JUDGMENT_REQUIRED"
    elif human:
        status = "READY_AT_EXACT_HUMAN_GATES"
    else:
        status = "LOCAL_REVERSIBLE_QUEUE_DRAINED"
    return {
        "schema_version": 1,
        "standard": "VRS-AUTONOMOUS-TRANSITION-EXECUTOR-1",
        "status": status,
        "started_at_utc": started,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "date": date,
        "mode": "APPLY_LOCAL_REVERSIBLE" if apply else "DRY_RUN",
        "planned": planned,
        "executed": executed,
        "holds": holds,
        "deterministic_remaining": deterministic_remaining,
        "judgment_required": judgment,
        "human_gates": human,
        "controller_counts": final_state.get("counts", {}),
        "external_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="execute only registered local reversible writers")
    parser.add_argument("--date", default=local_date())
    parser.add_argument("--max-transitions", type=int, default=32)
    parser.add_argument("--output", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    if args.max_transitions <= 0:
        parser.error("--max-transitions must be positive")
    result = drain(apply=args.apply, date=args.date, max_transitions=args.max_transitions)
    result = persist_receipt(args.output, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 2 if result["status"] == "HOLD_EXECUTOR_ERROR" else 0


if __name__ == "__main__":
    raise SystemExit(main())
