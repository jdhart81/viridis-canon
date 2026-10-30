"""Finite disposable lifecycle probes. Never import scientific candidate code."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import run_pure_checks as harness


CASES = ("normal", "timeout", "wait_baseexception", "term", "int", "spawn_interruption", "whole_expiry",
         "worker_watchdog", "normal_linger", "constructor_unknown", "group_unknown", "quiet_unknown")
MODES = ("quick", "sleep", "ignore_term", "leak", "watchdog", "marker")


class InjectedWaitFailure(BaseException):
    pass


def ready(path: Path, deadline: float):
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("finite disposable readiness deadline exceeded")
        time.sleep(0.01)


def leaf(mode: str, output: Path, whole_deadline: float) -> int:
    # Even an unexpectedly orphaned disposable leaf has a short independent OS
    # bound. This is a fixture bound, not evidence that cleanup actually worked.
    signal.setitimer(signal.ITIMER_REAL, min(3.0, max(0.001, whole_deadline - time.monotonic())))
    if mode == "ignore_term":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    harness.write_json(output / ("descendant.json" if mode == "ignore_term" else "leaf.json"),
                       {"pid": os.getpid(), "pgid": os.getpgrp(), "sid": os.getsid(0)})
    if mode == "marker":
        (output / "NEXT_SCOPE_WAS_ADMITTED").write_text("unexpected\n")
        return 0
    if mode == "watchdog":
        harness.arm_worker_deadline(whole_deadline, min(whole_deadline, time.monotonic() + 0.15))
    if mode == "leak":
        child = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                                  "--mode", "ignore_term", "--output", str(output),
                                  "--whole-deadline", str(whole_deadline)],
                                 env=harness.runtime_environment(None, output))
        # Deliberately leave this same-group child alive on normal leader exit.
        # Readiness proves TERM was ignored before the leader exits.
        ready(output / "descendant.json", min(whole_deadline, time.monotonic() + 0.8))
        assert child.poll() is None
        return 0
    time.sleep(0.03 if mode == "quick" else 2.0)
    return 0


def probe(case: str, output: Path, whole_deadline: float) -> int:
    output.mkdir(exist_ok=False)
    local_deadline = min(whole_deadline, time.monotonic() + 7.0)
    owned = harness.OwnedProcesses(local_deadline)
    mode = "quick" if case == "normal" else "leak" if case == "normal_linger" else (
        "watchdog" if case == "worker_watchdog" else "sleep")
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--mode", mode,
            "--output", str(output), "--whole-deadline", str(whole_deadline)]
    original_popen, original_getpgid, original_probe = subprocess.Popen, os.getpgid, harness.identity_probe
    result = {"case": case, "status": "HOLD", "next_scope_blocked": False}

    def waiter(process, deadline):
        ready(output / "leaf.json", min(deadline, time.monotonic() + 0.8))
        if case == "wait_baseexception":
            raise InjectedWaitFailure("finite injected failure after actual Popen registration")
        if case in {"term", "int"}:
            os.kill(os.getpid(), signal.SIGTERM if case == "term" else signal.SIGINT)
        if case == "whole_expiry":
            # Shorten this disposable probe's clock while the actual child is
            # active. Never extend the real action's original whole deadline.
            owned.deadline = min(owned.deadline, time.monotonic() + 0.1)
            signal.setitimer(signal.ITIMER_REAL, owned.deadline - time.monotonic())
        process.wait(timeout=max(0.001, deadline - time.monotonic()))

    def constructor_unknown(*args, **kwargs):
        raise OSError("finite constructor uncertainty before any child is returned")

    def spawn_interruption(*args, **kwargs):
        assert signal.SIGTERM in signal.pthread_sigmask(signal.SIG_BLOCK, ())
        process = original_popen(*args, **kwargs)
        # The actual object has returned from Popen, but the wrapper has not
        # returned it to execute yet. TERM must remain pending until execute
        # registers and verifies that exact object's ownership.
        os.kill(os.getpid(), signal.SIGTERM)
        return process

    def group_unknown(pid):
        raise PermissionError("finite injected actual-group lookup uncertainty")

    def quiet_unknown(pid, *, group):
        return {"state": "UNKNOWN", "error": "finite injected liveness probe uncertainty"}

    try:
        with owned:
            if case == "constructor_unknown":
                subprocess.Popen = constructor_unknown
            if case == "spawn_interruption":
                subprocess.Popen = spawn_interruption
            if case == "group_unknown":
                os.getpgid = group_unknown
            if case == "quiet_unknown":
                harness.identity_probe = quiet_unknown
            record = owned.execute(argv, cwd=output, environment=harness.runtime_environment(None, output),
                                   output=output, child_seconds=0.15 if case == "timeout" else 3.5,
                                   waiter=waiter if case in {"wait_baseexception", "term", "int", "whole_expiry"}
                                   else None)
            subprocess.Popen, os.getpgid, harness.identity_probe = original_popen, original_getpgid, original_probe
            result["owned_record"] = record
            if case != "normal":
                next_output = output / "next-scope"
                next_output.mkdir()
                try:
                    owned.execute([sys.executable, "-B", str(Path(__file__).resolve()), "--mode", "marker",
                                   "--output", str(output), "--whole-deadline", str(whole_deadline)],
                                  cwd=output, environment=harness.runtime_environment(None, output),
                                  output=next_output, child_seconds=0.2)
                except harness.LifecycleStop:
                    result["next_scope_blocked"] = True
            assert not (output / "NEXT_SCOPE_WAS_ADMITTED").exists()
            if case == "normal":
                assert record["status"] == "OWNED_PROCESS_COMPLETE" and record["returncode"] == 0
            else:
                assert record["status"] == "HOLD" and result["next_scope_blocked"]
            if case == "timeout":
                assert record["timed_out"]
            if case == "wait_baseexception":
                assert record["error"].startswith("InjectedWaitFailure:")
            if case in {"term", "int", "whole_expiry"}:
                expected = {"term": "SIGTERM", "int": "SIGINT", "whole_expiry": "SIGALRM"}[case]
                assert "runner received " + expected in record["error"]
            if case == "spawn_interruption":
                assert record["ownership"] == "ACTUAL_POPEN_REGISTERED"
                assert record["pid"] == record["pgid"] == record["sid"]
                assert "runner received SIGTERM" in record["error"]
            if case == "worker_watchdog":
                assert record["returncode"] == -signal.SIGALRM
            if case == "normal_linger":
                assert record["returncode"] == 0 and record["cleanup"]["normal_return_residue"]
                assert "SIGKILL" in record["cleanup"]["signals"]
            if case == "constructor_unknown":
                assert record["ownership"] == "CONSTRUCTOR_NOT_RETURNED" and "cleanup" not in record
            elif case == "group_unknown":
                assert record["ownership"] == "ACTUAL_POPEN_REGISTERED"
                assert not record["cleanup"]["status"] == "REAPED_PID_AND_GROUP_QUIET"
            elif case == "quiet_unknown":
                assert not record["cleanup"]["quiet"]
            else:
                assert record["cleanup"]["direct_child_reaped"] and record["cleanup"]["quiet"]
            # These are fresh OS probes after teardown, independent of cleanup
            # JSON or an exited leader. The parent repeats them independently.
            result["independent_probes"] = []
            for name in ("leaf.json", "descendant.json"):
                if (output / name).exists():
                    identity = json.loads((output / name).read_bytes())
                    proof = {"identity": identity, "pid": original_probe(identity["pid"], group=False),
                             "group": original_probe(identity["pgid"], group=True)}
                    result["independent_probes"].append(proof)
                    assert proof["pid"]["state"] == proof["group"]["state"] == "ABSENT"
            if case != "constructor_unknown":
                assert original_probe(record["pid"], group=False)["state"] == "ABSENT"
                assert original_probe(record["pid"], group=True)["state"] == "ABSENT"
            result["status"] = "DISPOSABLE_LIFECYCLE_CONTROL_PASS"
    except BaseException as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        subprocess.Popen, os.getpgid, harness.identity_probe = original_popen, original_getpgid, original_probe
        result["owned_records"] = owned.records
        harness.write_json(output / "CONTROL_RESULT.json", result)
    return 0 if result["status"] == "DISPOSABLE_LIFECYCLE_CONTROL_PASS" else 2


def main() -> int:
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
        signal.signal(sig, signal.SIG_DFL)
    signal.pthread_sigmask(signal.SIG_UNBLOCK, (signal.SIGTERM, signal.SIGINT, signal.SIGALRM))
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--probe", choices=CASES)
    group.add_argument("--mode", choices=MODES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--whole-deadline", type=float, required=True)
    args = parser.parse_args()
    if (not args.output.is_absolute() or not math.isfinite(args.whole_deadline)
            or args.whole_deadline > harness.ACTION_STARTED + harness.WHOLE_SECONDS
            or args.whole_deadline <= time.monotonic()):
        raise ValueError("absolute disposable output and original bounded deadline required")
    return probe(args.probe, args.output, args.whole_deadline) if args.probe else leaf(
        args.mode, args.output, args.whole_deadline)


if __name__ == "__main__":
    raise SystemExit(main())
