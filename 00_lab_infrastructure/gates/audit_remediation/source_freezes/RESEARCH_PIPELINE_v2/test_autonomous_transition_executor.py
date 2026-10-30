from __future__ import annotations

import sys
import json
import subprocess

import pytest
import autonomous_transition_executor as executor

from autonomous_transition_executor import (
    CommandResult,
    command_plan,
    drain,
    validate_command,
    ExecutorError,
)


def state(action: str | None, *, human: bool = False) -> dict:
    items = [] if action is None else [{
        "run_id": "Run-149",
        "state": "TEST",
        "next_action": action,
        "human_gate": human,
        "detail": "test",
    }]
    return {
        "items": items,
        "counts": {
            "total": len(items),
            "machine_actionable": int(bool(items) and not human),
            "human_gated": int(bool(items) and human),
            "viridisos_tracked": 0,
        },
    }


def ok(argv: list[str]) -> CommandResult:
    return CommandResult(argv, 0, "a" * 64, "b" * 64, "", "")


def test_command_plan_never_contains_irreversible_flags():
    for action in (
        "CREATE_VERSIONED_VERIFICATION_METADATA_CORRECTION",
        "CREATE_VERSIONED_CORRECTION_OVERLAY",
        "FINALIZE_REVIEWED_PACKAGE",
        "RUN_CANON_AND_PRODUCT_ROUTE",
        "BUILD_VIRIDISOS_KERNEL_PACKAGE",
        "ASSEMBLE_AUGMENT_AND_VERIFY_SUBMISSION_PACKAGE",
    ):
        for argv in command_plan(action, "Run-149", "2026-08-31"):
            validate_command(argv)


def test_validate_command_rejects_authorization_bearing_flags():
    argv = [
        sys.executable,
        command_plan("FINALIZE_REVIEWED_PACKAGE", "Run-149", "2026-08-31")[0][1],
        "--justin-authorized",
    ]
    try:
        validate_command(argv)
    except ExecutorError:
        pass
    else:
        raise AssertionError("authorization-bearing flag was accepted")


def test_apply_advances_deterministic_transition_then_stops_at_human_gate():
    snapshots = [
        state("FINALIZE_REVIEWED_PACKAGE"),
        state("WAIT_FOR_EXACT_AUTHORIZATION", human=True),
        state("WAIT_FOR_EXACT_AUTHORIZATION", human=True),
    ]
    index = 0

    def next_state() -> dict:
        nonlocal index
        value = snapshots[min(index, len(snapshots) - 1)]
        index += 1
        return value

    result = drain(
        apply=True,
        date="2026-08-31",
        max_transitions=4,
        state_builder=next_state,
        command_runner=ok,
    )
    assert result["status"] == "READY_AT_EXACT_HUMAN_GATES"
    assert result["executed"][0]["action"] == "FINALIZE_REVIEWED_PACKAGE"
    assert len(result["human_gates"]) == 1


def test_judgment_work_is_never_executed_mechanically():
    current = state("REVIEW_PRIOR_INVOCATION_DRAFT")
    called = False

    def forbidden(_: list[str]) -> CommandResult:
        nonlocal called
        called = True
        return ok([])

    result = drain(
        apply=True,
        date="2026-08-31",
        max_transitions=4,
        state_builder=lambda: current,
        command_runner=forbidden,
    )
    assert result["status"] == "AGENT_JUDGMENT_REQUIRED"
    assert called is False
    assert result["judgment_required"][0]["next_action"] == "REVIEW_PRIOR_INVOCATION_DRAFT"


def test_dry_run_does_not_execute():
    current = state("RUN_CANON_AND_PRODUCT_ROUTE")
    result = drain(
        apply=False,
        date="2026-08-31",
        max_transitions=4,
        state_builder=lambda: current,
        command_runner=lambda _: (_ for _ in ()).throw(AssertionError("executed")),
    )
    assert result["status"] == "DRY_RUN"
    assert result["planned"][0]["action"] == "RUN_CANON_AND_PRODUCT_ROUTE"
    assert result["executed"] == []


def test_kernel_package_action_uses_local_fail_closed_writer():
    argv = command_plan("BUILD_VIRIDISOS_KERNEL_PACKAGE", "Run-149", "2026-09-01")[0]
    validate_command(argv)
    assert argv[1].endswith("viridisos_kernel_packager.py")
    assert argv[2:] == ["--run", "Run-149"]



def test_unchanged_checkpoint_retains_exact_receipt_bytes_and_time(tmp_path):
    from copy import deepcopy
    from autonomous_transition_executor import persist_receipt

    result = drain(apply=True, date="2026-09-08", max_transitions=1,
                   state_builder=lambda: state("CERTIFY_COMPARATOR_FIFO"), command_runner=ok)
    path = tmp_path / "executor.json"
    original = persist_receipt(path, result)
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    later = deepcopy(result)
    later.update(started_at_utc="2026-09-08T15:00:00+00:00",
                 completed_at_utc="2026-09-08T15:00:01+00:00")
    assert persist_receipt(path, later) == original
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_changed_checkpoint_gets_new_receipt(tmp_path):
    from copy import deepcopy
    from autonomous_transition_executor import persist_receipt

    result = drain(apply=True, date="2026-09-08", max_transitions=1,
                   state_builder=lambda: state("CERTIFY_COMPARATOR_FIFO"), command_runner=ok)
    path = tmp_path / "executor.json"
    persist_receipt(path, result)
    later = deepcopy(result)
    later["judgment_required"][0]["next_action"] = "REVIEW_KERNEL_ADMISSION"
    later["completed_at_utc"] = "2026-09-08T15:00:01+00:00"
    assert persist_receipt(path, later) == later
    assert path.read_text().find("REVIEW_KERNEL_ADMISSION") >= 0


def test_repeated_command_and_hold_attempts_are_fresh_events(tmp_path):
    from copy import deepcopy
    from autonomous_transition_executor import persist_receipt

    for field in ("executed", "holds"):
        result = drain(apply=True, date="2026-09-08", max_transitions=1,
                       state_builder=lambda: state(None), command_runner=ok)
        result[field] = [{"run_id": "Run-149", "action": "fixture attempt"}]
        path = tmp_path / (field + ".json")
        persist_receipt(path, result)
        later = deepcopy(result)
        later["completed_at_utc"] = "2026-09-08T15:00:01+00:00"
        assert persist_receipt(path, later) == later
        assert later["completed_at_utc"] in path.read_text()


def test_executor_main_still_recomputes_each_checkpoint(tmp_path, monkeypatch, capsys):
    from copy import deepcopy
    import autonomous_transition_executor as executor

    calls = []
    result = drain(apply=False, date="2026-09-08", max_transitions=1,
                   state_builder=lambda: state("CERTIFY_COMPARATOR_FIFO"), command_runner=ok)

    def fresh_drain(**kwargs):
        calls.append(kwargs)
        fresh = deepcopy(result)
        fresh["completed_at_utc"] = f"2026-09-08T15:00:0{len(calls)}+00:00"
        return fresh

    path = tmp_path / "executor.json"
    monkeypatch.setattr(executor, "drain", fresh_drain)
    monkeypatch.setattr(sys, "argv", ["executor", "--output", str(path), "--date", "2026-09-08"])
    assert executor.main() == 0
    before = (path.read_bytes(), path.stat().st_mtime_ns)
    assert executor.main() == 0
    assert len(calls) == 2
    assert all(call["apply"] is False for call in calls)
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before
    capsys.readouterr()


def kernel_hold_json(error="all scientific probes must be recorded and resolved", **changes):
    return json.dumps({"status": "HOLD", "error": error, "external_mutation": False, **changes})


def test_object_hold_preserves_diagnostics_continues_unrelated_run_and_never_retries(monkeypatch):
    calls = []
    finished = False
    failed = False

    def current():
        first = {"run_id": "Run-170", "state": "TEST", "human_gate": False,
                 "next_action": "FINALIZE_REVIEWED_PACKAGE" if failed else "BUILD_VIRIDISOS_KERNEL_PACKAGE"}
        second = {"run_id": "Run-179", "state": "TEST", "human_gate": finished,
                  "next_action": "WAIT_FOR_EXACT_AUTHORIZATION" if finished else "FINALIZE_REVIEWED_PACKAGE"}
        return {"items": [first, second], "counts": {}}

    def process(argv, **kwargs):
        nonlocal failed, finished
        calls.append(argv)
        if argv[-1] == "Run-170":
            failed = True
            return subprocess.CompletedProcess(argv, 2, kernel_hold_json(), "")
        finished = True
        return subprocess.CompletedProcess(argv, 0, "independent object completed", "")

    monkeypatch.setattr(executor.subprocess, "run", process)
    result = drain(apply=True, date="2026-10-18", max_transitions=5,
                   state_builder=current, command_runner=executor.run_command)
    assert [argv[-1] for argv in calls] == ["Run-170", "Run-179"]
    assert [row["run_id"] for row in result["executed"]] == ["Run-179"]
    assert result["status"] == "HOLD_EXECUTOR_ERROR"
    assert len(result["holds"]) == 1 and result["holds"][0]["scope"] == "OBJECT"
    assert "all scientific probes" in result["holds"][0]["failed_command"]["stdout_tail"]
    assert result["holds"][0]["failed_command"]["stdout_sha256"]
    assert [row["run_id"] for row in result["deterministic_remaining"]] == ["Run-170"]


@pytest.mark.parametrize("stdout,stderr,code", [
    (kernel_hold_json("reviewed_artifact_sha256.paper_manifest does not match PAPER_PACKAGE_MANIFEST.json"), "", 2),
    (kernel_hold_json("HOLD_EFFECTIVE_ALLOCATION_REGULAR_INPUT"), "", 2),
    (kernel_hold_json("HOLD_AUTHORIZATION"), "", 2),
    (kernel_hold_json("unknown refusal"), "", 2),
    (kernel_hold_json(external_mutation=True), "", 2),
    (kernel_hold_json(), "unexpected process diagnostic", 2),
    (kernel_hold_json(), "", 1),
    ("not JSON", "", 2),
    ('{"status":"PASS","status":"HOLD","error":"all scientific probes must be recorded and resolved","external_mutation":false}', "", 2),
    (kernel_hold_json(extra_authority="unknown"), "", 2),
])
def test_nonlocal_or_ambiguous_failure_stops_all_work(monkeypatch, stdout, stderr, code):
    calls = []
    current = {"items": [
        {"run_id": "Run-170", "state": "TEST", "human_gate": False,
         "next_action": "BUILD_VIRIDISOS_KERNEL_PACKAGE"},
        {"run_id": "Run-179", "state": "TEST", "human_gate": False,
         "next_action": "FINALIZE_REVIEWED_PACKAGE"},
    ], "counts": {}}
    def process(argv, **kwargs):
        calls.append(argv)
        return subprocess.CompletedProcess(argv, code, stdout, stderr)
    monkeypatch.setattr(executor.subprocess, "run", process)
    result = drain(apply=True, date="2026-10-18", max_transitions=5,
                   state_builder=lambda: current, command_runner=executor.run_command)
    assert len(calls) == 1
    assert result["status"] == "HOLD_EXECUTOR_ERROR"
    assert result["holds"][0]["scope"] == "GLOBAL"
    assert result["holds"][0]["failed_command"]["stdout_tail"] == stdout[-2000:]
    assert result["executed"] == []


def test_semantic_hold_from_another_writer_is_a_global_stop(monkeypatch):
    argv = command_plan("FINALIZE_REVIEWED_PACKAGE", "Run-170", "2026-10-18")[0]
    monkeypatch.setattr(executor.subprocess, "run",
                        lambda *args, **kwargs: subprocess.CompletedProcess(argv, 2, kernel_hold_json(), ""))
    with pytest.raises(executor.WriterFailure) as failure:
        executor.run_command(argv)
    assert failure.value.object_local is False
    assert "all scientific probes" in str(failure.value)


def test_new_versioned_admission_correction_is_judgment_only():
    called = []
    result = drain(apply=True, date="2026-10-18", max_transitions=5,
                   state_builder=lambda: state("PREPARE_VERSIONED_KERNEL_ADMISSION_CORRECTION"),
                   command_runner=lambda argv: called.append(argv))
    assert result["status"] == "AGENT_JUDGMENT_REQUIRED"
    assert called == []


def test_unknown_machine_action_stops_before_any_known_writer():
    current = {"items": [
        {"run_id": "Run-170", "human_gate": False, "next_action": "UNKNOWN_NEW_ACTION"},
        {"run_id": "Run-179", "human_gate": False, "next_action": "FINALIZE_REVIEWED_PACKAGE"},
    ], "counts": {}}
    called = []
    result = drain(apply=True, date="2026-10-18", max_transitions=5,
                   state_builder=lambda: current, command_runner=lambda argv: called.append(argv))
    assert result["status"] == "HOLD_EXECUTOR_ERROR"
    assert result["holds"][0]["scope"] == "GLOBAL"
    assert called == []


@pytest.mark.parametrize("failure", [OSError("process unavailable"), subprocess.TimeoutExpired("writer", 300)])
def test_process_and_timeout_errors_never_continue(failure):
    called = []
    def runner(argv):
        called.append(argv)
        raise failure
    result = drain(apply=True, date="2026-10-18", max_transitions=5,
                   state_builder=lambda: state("BUILD_VIRIDISOS_KERNEL_PACKAGE"), command_runner=runner)
    assert result["status"] == "HOLD_EXECUTOR_ERROR"
    assert result["holds"][0]["scope"] == "GLOBAL"
    assert len(called) == 1
