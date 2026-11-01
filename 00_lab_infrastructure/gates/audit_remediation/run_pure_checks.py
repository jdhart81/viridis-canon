"""Run the finite public audit proposal in scratch; never adopt production code."""
from __future__ import annotations

import time
ACTION_STARTED = time.monotonic()

import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import sysconfig
import xml.etree.ElementTree as ET
from zoneinfo import TZPATH

HERE = Path(__file__).resolve().parent
WHOLE_SECONDS = 540
CHILD_SECONDS = 60
CLEANUP_SECONDS = 3.0
TERM_GRACE_SECONDS = 0.5
POLL_SECONDS = 0.02
# Worker processes need only interpreter search, locale and platform runtime
# settings. Provider credentials and arbitrary parent configuration never enter.
RUNTIME_ENVIRONMENT = {"PATH", "LANG", "LC_ALL", "LC_CTYPE", "LC_TIME", "LC_NUMERIC", "TZ",
                       "SYSTEMROOT", "WINDIR"}
PDF_V2_TEST = "test_v2_assembly_and_current_guard_bind_standalone_paper_bytes"
SCOPES = {
    "fixture": None,
    "controller": "RESEARCH_PIPELINE_v2/test_autonomous_pipeline_controller.py",
    "executor": "RESEARCH_PIPELINE_v2/test_autonomous_transition_executor.py",
    "kernel": "RESEARCH_PIPELINE_v2/test_viridisos_kernel_packager.py",
    "preflight": "RESEARCH_PIPELINE_v2/test_nightly_science_preflight.py",
    "assembler": "RESEARCH_PIPELINE_v2/test_assemble_saturday_candidate.py",
    "manuscript_pdf": "_ZENODO_DEPOSITS/tests/test_manuscript_pdf_gate.py",
}
MUTANTS = {
    "admission_validation_removed": (
        "autonomous_pipeline_controller.py", "admission_work = kernel_admission_work_item(path)",
        "admission_work = None",
        "test_autonomous_pipeline_controller.py::test_held_or_invalid_admission_routes_to_versioned_correction_without_writes[hold]"),
    "local_continuation_removed": (
        "autonomous_transition_executor.py",
        "result, object_local=object_local_kernel_hold(result, completed.stdout, completed.stderr)",
        "result, object_local=False",
        "test_autonomous_transition_executor.py::test_object_hold_preserves_diagnostics_continues_unrelated_run_and_never_retries"),
    "failed_identity_exclusion_removed": (
        "autonomous_transition_executor.py", 'and row.get("run_id") not in failed_runs', "and True",
        "test_autonomous_transition_executor.py::test_object_hold_preserves_diagnostics_continues_unrelated_run_and_never_retries"),
    "unknown_integrity_diagnostics_accepted": (
        "autonomous_transition_executor.py", 'and value["error"] in OBJECT_LOCAL_KERNEL_HOLDS', "and True",
        "test_autonomous_transition_executor.py::test_nonlocal_or_ambiguous_failure_stops_all_work"),
    "known_judgment_misclassified": (
        "autonomous_transition_executor.py",
        'and row.get("next_action") not in DETERMINISTIC_ACTIONS | JUDGMENT_ACTIONS',
        'and row.get("next_action") not in DETERMINISTIC_ACTIONS',
        "test_autonomous_transition_executor.py::test_new_versioned_admission_correction_is_judgment_only"),
    "stdout_diagnostic_discarded": (
        "autonomous_transition_executor.py", "stdout_tail=output_tail(completed.stdout),", 'stdout_tail="",',
        "test_autonomous_transition_executor.py::test_object_hold_preserves_diagnostics_continues_unrelated_run_and_never_retries"),
}
ORIGINAL_PREFLIGHT = (
    "00_lab_infrastructure/gates/production_snapshots/"
    "phase7-20261008-owned-weekly-source-provenance/after/"
    "production_execution_dependencies/nightly_science_preflight.py")
ORIGINAL_PREFLIGHT_SHA256 = "a41945368e682012cdc41d8a206d6a8a0c66e12baddb082326bf755d626e2f83"
PREFLIGHT_CAUSAL = ("test_nightly_science_preflight.py::VersionedCertificateDiscoveryTests::"
                    "test_versioned_r1_and_r2_certificates_count_without_integrity_hold")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def source_inventory(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


class LifecycleStop(BaseException):
    """A handled signal or original whole deadline stops further admission."""


def identity_probe(pid: int, *, group: bool) -> dict:
    """Only an actual ESRCH probe proves absence; other errors are uncertain."""
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return {"state": "ABSENT", "evidence": "ESRCH"}
    except OSError as exc:
        return {"state": "UNKNOWN", "error": type(exc).__name__ + ": " + str(exc)}
    return {"state": "PRESENT"}


def runtime_environment(fixture: Path | None, output: Path) -> dict:
    environment = {key: value for key, value in os.environ.items() if key in RUNTIME_ENVIRONMENT}
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", TMPDIR=str(output))
    paths = [p for p in sys.path if p and p.endswith(("site-packages", "dist-packages"))]
    if fixture is not None:
        environment["VIRIDIS_CORE_ROOT"] = str(fixture)
        paths[:0] = [str(fixture / "RESEARCH_PIPELINE_v2"),
                     str(fixture / "RESEARCH_PIPELINE_v2/verification_coverage_gates"),
                     str(fixture / "_ZENODO_DEPOSITS")]
    environment["PYTHONPATH"] = os.pathsep.join(paths)
    return environment


class OwnedProcesses:
    """Own exact returned Popen objects and prove quiet on every exit path."""

    def __init__(self, deadline: float):
        if not isinstance(deadline, (int, float)) or not math.isfinite(deadline):
            raise ValueError("finite original monotonic deadline required")
        self.deadline = deadline
        self.active = {}
        self.records = []
        self.aborted = None
        self.cleaning = False
        self.signals = (signal.SIGTERM, signal.SIGINT, signal.SIGALRM)

    def checkpoint(self):
        if self.aborted or time.monotonic() >= self.deadline - CLEANUP_SECONDS:
            raise LifecycleStop(self.aborted or "original whole deadline reserve reached")

    def _signal(self, signum, frame):
        self.aborted = "runner received " + signal.Signals(signum).name
        if not self.cleaning:
            raise LifecycleStop(self.aborted)

    def __enter__(self):
        self.previous_handlers = {sig: signal.getsignal(sig) for sig in self.signals}
        self.previous_alarm = signal.getitimer(signal.ITIMER_REAL)
        for sig in self.signals:
            signal.signal(sig, self._signal)
        signal.setitimer(signal.ITIMER_REAL, max(0.001, self.deadline - time.monotonic()))
        try:
            self.checkpoint()
        except BaseException:
            signal.setitimer(signal.ITIMER_REAL, 0)
            for sig, handler in self.previous_handlers.items():
                signal.signal(sig, handler)
            raise
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.cleaning = True
        try:
            for owner in list(self.active.values()):
                self._teardown(owner, normal=False)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            for sig, handler in self.previous_handlers.items():
                signal.signal(sig, handler)
            # This harness is a standalone action, not an alarm-extending nested
            # scheduler. A pre-existing alarm is never postponed by restoration.
            if self.previous_alarm[0]:
                signal.setitimer(signal.ITIMER_REAL, 0.001)
        return False

    def _teardown(self, owner, *, normal):
        if "cleanup" in owner:
            return owner["cleanup"]
        process = owner["process"]
        previous_cleaning, self.cleaning = self.cleaning, True
        started = time.monotonic()
        deadline = started + CLEANUP_SECONDS
        record = {"pid": process.pid, "pgid": owner.get("pgid"),
                  "sid": owner.get("sid"), "signals": [], "errors": [], "probes": [],
                  "normal_return_residue": False, "direct_child_reaped": False,
                  "quiet": False, "status": "HOLD"}
        def sample():
            value = {"elapsed": time.monotonic() - started,
                     "pid": identity_probe(process.pid, group=False),
                     "group": identity_probe(process.pid, group=True)}
            record["probes"].append(value)
            return value
        def send(sig):
            try:
                if owner.get("verified_group"):
                    os.killpg(process.pid, sig)
                else:
                    # Never guess a process group when its actual ownership is
                    # uncertain. The exact returned direct child is still ours.
                    process.send_signal(sig)
                record["signals"].append(signal.Signals(sig).name)
            except ProcessLookupError:
                record["signals"].append(signal.Signals(sig).name + ":ESRCH")
            except BaseException as exc:
                record["errors"].append(type(exc).__name__ + ": " + str(exc))
        try:
            initial = sample()
            record["normal_return_residue"] = normal and any(
                initial[key]["state"] != "ABSENT" for key in ("pid", "group"))
            if any(initial[key]["state"] != "ABSENT" for key in ("pid", "group")):
                send(signal.SIGTERM)
                grace = min(deadline, time.monotonic() + TERM_GRACE_SECONDS)
                while time.monotonic() < grace:
                    try:
                        process.poll()  # reaps the exact direct child when terminal
                    except BaseException as exc:
                        record["errors"].append("poll: " + type(exc).__name__ + ": " + str(exc))
                        break
                    current = sample()
                    if all(current[key]["state"] == "ABSENT" for key in ("pid", "group")):
                        break
                    time.sleep(min(POLL_SECONDS, max(0, grace - time.monotonic())))
                current = sample()
                if any(current[key]["state"] != "ABSENT" for key in ("pid", "group")):
                    send(signal.SIGKILL)
            try:
                process.wait(timeout=max(0.001, deadline - time.monotonic()))
                record["direct_child_reaped"] = process.returncode is not None
            except BaseException as exc:
                record["errors"].append("reap: " + type(exc).__name__ + ": " + str(exc))
            while time.monotonic() < deadline:
                current = sample()
                if all(current[key]["state"] == "ABSENT" for key in ("pid", "group")):
                    record["quiet"] = True
                    break
                if any(current[key]["state"] == "UNKNOWN" for key in ("pid", "group")):
                    break
                time.sleep(min(POLL_SECONDS, max(0, deadline - time.monotonic())))
            record["final_probe"] = sample()
            record["quiet"] = record["quiet"] and all(
                record["final_probe"][key]["state"] == "ABSENT" for key in ("pid", "group"))
            if (owner.get("verified_group") and record["quiet"]
                    and record["direct_child_reaped"] and not record["errors"]
                    and not record["normal_return_residue"]):
                record["status"] = "REAPED_PID_AND_GROUP_QUIET"
        except BaseException as exc:
            record["errors"].append("cleanup: " + type(exc).__name__ + ": " + str(exc))
        finally:
            record["seconds"] = time.monotonic() - started
            record["returncode"] = process.returncode
            owner["cleanup"] = record
            if record["quiet"] and record["direct_child_reaped"]:
                self.active.pop(process.pid, None)
            self.cleaning = previous_cleaning
        return record

    def execute(self, argv, *, cwd, environment, output, child_seconds=CHILD_SECONDS, waiter=None):
        self.checkpoint()
        deadline = min(self.deadline - CLEANUP_SECONDS, time.monotonic() + child_seconds)
        record = {"argv": argv, "status": "HOLD", "deadline": deadline,
                  "whole_deadline": self.deadline, "timed_out": False,
                  "ownership": "CONSTRUCTOR_NOT_RETURNED", "error": None}
        owner = None
        started = time.monotonic()
        try:
            with (output / "stdout.txt").open("xb") as stdout, (output / "stderr.txt").open("xb") as stderr:
                old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, self.signals)
                try:
                    process = subprocess.Popen(argv, cwd=cwd, env=environment,
                                               stdout=stdout, stderr=stderr, start_new_session=True)
                    # Register the actual returned object before any unshielded
                    # operation or further inspection can be interrupted.
                    owner = {"process": process, "verified_group": False}
                    self.active[process.pid] = owner
                    record.update(pid=process.pid, ownership="ACTUAL_POPEN_REGISTERED")
                    owner["pgid"], owner["sid"] = os.getpgid(process.pid), os.getsid(process.pid)
                    owner["verified_group"] = owner["pgid"] == process.pid == owner["sid"]
                    record.update(pgid=owner["pgid"], sid=owner["sid"])
                    if not owner["verified_group"]:
                        raise RuntimeError("actual child group/session ownership differs")
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
                if waiter is None:
                    process.wait(timeout=max(0.001, deadline - time.monotonic()))
                else:
                    waiter(process, deadline)
                record["returncode"] = process.returncode
        except subprocess.TimeoutExpired as exc:
            record.update(timed_out=True, error=type(exc).__name__ + ": " + str(exc))
        except BaseException as exc:
            record["error"] = type(exc).__name__ + ": " + str(exc)
        finally:
            if owner is not None:
                record["cleanup"] = self._teardown(owner, normal=record["error"] is None)
                record["returncode"] = owner["process"].returncode
            if (record["error"] is None and isinstance(record.get("returncode"), int)
                    and record["returncode"] >= 0
                    and record.get("cleanup", {}).get("status")
                    == "REAPED_PID_AND_GROUP_QUIET" and not self.aborted):
                record["status"] = "OWNED_PROCESS_COMPLETE"
            else:
                self.aborted = self.aborted or "owned child lifecycle HOLD"
            record["seconds"] = time.monotonic() - started
            self.records.append(record)
            write_json(output / "LIFECYCLE.json", record)
        return record


def arm_worker_deadline(whole_deadline: float, child_deadline: float):
    """Install an OS-default hard alarm before pytest or candidate imports."""
    if (not isinstance(whole_deadline, (int, float)) or not isinstance(child_deadline, (int, float))
            or not math.isfinite(whole_deadline) or not math.isfinite(child_deadline)
            or child_deadline > whole_deadline or whole_deadline > ACTION_STARTED + WHOLE_SECONDS
            or child_deadline > ACTION_STARTED + CHILD_SECONDS):
        raise ValueError("bounded original whole and worker deadlines required")
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGALRM):
        signal.signal(sig, signal.SIG_DFL)
    # Popen is deliberately created while the supervisor masks its handled
    # signals. Clear that inherited mask before any candidate import or alarm.
    signal.pthread_sigmask(signal.SIG_UNBLOCK, (signal.SIGTERM, signal.SIGINT, signal.SIGALRM))
    remaining = min(whole_deadline, child_deadline) - time.monotonic()
    if remaining <= 0:
        raise LifecycleStop("worker original deadline already expired")
    signal.setitimer(signal.ITIMER_REAL, remaining)


def _worker_guard(repo: Path, fixture: Path, output: Path) -> None:
    """Reject ambient data, network, native tools and production writer dispatch."""
    writable = output.resolve()
    libraries = {Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve(),
                 Path(sysconfig.get_path("stdlib")).resolve()}
    libraries.update(Path(p).resolve() for p in sys.path if p and
                     (p.endswith("site-packages") or p.endswith("dist-packages")))
    readable = {repo.resolve(), fixture.resolve(), writable, *libraries,
                *(Path(p).resolve() for p in TZPATH)}
    packager = (fixture / "RESEARCH_PIPELINE_v2/viridisos_kernel_packager.py").resolve()
    actual_popen = subprocess.Popen

    def guarded_popen(*args, **kwargs):
        if (kwargs.get("start_new_session") or kwargs.get("process_group") is not None
                or kwargs.get("preexec_fn") is not None):
            raise RuntimeError("pure audit child must remain in its owned worker group")
        command = args[0] if args else kwargs.get("args")
        if not (isinstance(command, (list, tuple)) and len(command) == 9
                and Path(command[0]).resolve() == Path(sys.executable).resolve()
                and Path(command[1]).resolve() == packager
                and list(command[2:5]) == ["--run", "200", "--finalized-root"]
                and command[6] == "--output-root" and command[8] == "--validate-only"
                and inside(command[5], {writable}) and inside(command[7], {writable})):
            raise RuntimeError("pure audit fixture permits only its exact validate-only child")
        supplied_cwd = kwargs.get("cwd")
        if supplied_cwd is not None and Path(supplied_cwd).resolve() != fixture.resolve():
            raise RuntimeError("pure audit child cwd differs from its inherited fixture")
        # The worker already inherits this directory. Make it explicit so the
        # reviewed CPython3.12/3.14 Popen path uses fork_exec and the raw native
        # posix_spawn denial remains intact on Linux CLOSEFROM builds.
        kwargs["cwd"] = str(fixture.resolve())
        return actual_popen(*args, **kwargs)

    def no_detach(*args, **kwargs):
        raise RuntimeError("pure audit fixture forbids detached process creation")

    subprocess.Popen = guarded_popen
    os.setsid = no_detach
    os.setpgid = no_detach

    def descriptor_path(fd):
        if sys.platform == "darwin":
            raw = fcntl.fcntl(fd, getattr(fcntl, "F_GETPATH", 50), b"\0" * 1024)
            return Path(os.fsdecode(raw.split(b"\0", 1)[0])).resolve()
        if sys.platform.startswith("linux"):
            raw = os.readlink("/proc/self/fd/" + str(fd))
            if not Path(raw).is_absolute():
                raise ValueError("descriptor is not a filesystem object")
            return Path(raw.removesuffix(" (deleted)")).resolve()
        raise ValueError("descriptor containment requires a supported platform")

    def resolved(value, dir_fd=-1, *, follow_final=True):
        if isinstance(value, int):
            return descriptor_path(value)
        path = Path(os.fsdecode(value))
        if not path.is_absolute() and dir_fd not in (None, -1):
            path = descriptor_path(dir_fd) / path
        return path.resolve() if follow_final else path.parent.resolve() / path.name

    def inside(value, roots):
        try:
            path = resolved(value)
        except (OSError, TypeError, ValueError):
            return False
        return any(path == root or path.is_relative_to(root) for root in roots)

    def write_path(value, dir_fd=-1, *, follow_final=True):
        try:
            path = resolved(value, dir_fd, follow_final=follow_final)
            return path == writable or path.is_relative_to(writable)
        except (OSError, TypeError, ValueError):
            return False

    def audit(event, args):
        if event.startswith("socket.") or event in {"os.system", "os.posix_spawn", "os.exec",
                                                    "os.fork", "os.forkpty"}:
            raise RuntimeError("pure audit fixture forbids network/native dispatch: " + event)
        if event == "open":
            name, mode, flags = args
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            if name == os.devnull and not writing:
                return
            if isinstance(name, int) and name in (0, 1, 2):
                # Only inherited standard streams are exempt from pathname
                # containment; arbitrary descriptors must resolve below.
                return
            if isinstance(name, int) and not writing and stat.S_ISFIFO(os.fstat(name).st_mode):
                # subprocess capture_output wraps its anonymous read pipes
                # before the Popen audit event. Regular descriptors still need
                # actual filesystem containment.
                return
            if not inside(name, {writable} if writing else readable):
                raise RuntimeError("pure audit fixture forbids ambient file access")
        if event in {"os.listdir", "os.scandir"}:
            if not inside(args[0] if args[0] is not None else os.curdir, readable):
                raise RuntimeError("pure audit fixture forbids ambient directory access")
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime"}:
            fd_index = {"os.remove": 1, "os.rmdir": 1, "os.mkdir": 2,
                        "os.chmod": 2, "os.utime": 3}[event]
            follow_final = event not in {"os.remove", "os.rmdir", "os.mkdir"}
            if not write_path(args[0], args[fd_index], follow_final=follow_final):
                raise RuntimeError("pure audit fixture forbids writes outside scratch")
        if event == "os.rename":
            if not write_path(args[0], args[2], follow_final=False) or not write_path(
                    args[1], args[3], follow_final=False):
                raise RuntimeError("pure audit fixture forbids rename outside scratch")
        if event == "os.symlink":
            try:
                destination = resolved(args[1], args[2], follow_final=False)
                target = Path(os.fsdecode(args[0]))
                if not target.is_absolute():
                    target = destination.parent / target
                allowed = inside(target, readable) and write_path(
                    args[1], args[2], follow_final=False)
            except (OSError, TypeError, ValueError):
                allowed = False
            if not allowed:
                raise RuntimeError("pure audit fixture forbids links outside scratch")
        if event == "os.link":
            if not write_path(args[0], args[2]) or not write_path(
                    args[1], args[3], follow_final=False):
                raise RuntimeError("pure audit fixture forbids links outside scratch")
        if event == "subprocess.Popen":
            executable, argv, cwd, environment = args
            allowed = (isinstance(argv, (list, tuple)) and len(argv) == 9
                       and Path(executable).resolve() == Path(sys.executable).resolve()
                       and Path(argv[1]).resolve() == packager
                       and list(argv[2:5]) == ["--run", "200", "--finalized-root"]
                       and argv[6] == "--output-root" and argv[8] == "--validate-only"
                       and inside(argv[5], {writable}) and inside(argv[7], {writable})
                       and cwd == str(fixture.resolve())
                       and isinstance(environment, dict)
                       and environment.get("PYTHONDONTWRITEBYTECODE") == "1")
            if not allowed:
                raise RuntimeError("pure audit fixture forbids subprocess writers and native tools")

    sys.addaudithook(audit)


def worker(args) -> int:
    arm_worker_deadline(args.whole_deadline, args.child_deadline)
    repo, fixture, output = args.repo.resolve(), args.fixture.resolve(), args.output.resolve()
    _worker_guard(repo, fixture, output)
    sys.path[:0] = [str(fixture / "RESEARCH_PIPELINE_v2"),
                    str(fixture / "RESEARCH_PIPELINE_v2/verification_coverage_gates"),
                    str(fixture / "_ZENODO_DEPOSITS"), str(HERE)]
    import pytest
    write_json(output / "interpreter.json", {"version": sys.version, "executable": sys.executable,
                                            "pytest_version": pytest.__version__, "pytest_file": pytest.__file__})
    if args.scope in SCOPES:
        target = HERE / "test_public_fixture.py" if args.scope == "fixture" else fixture / SCOPES[args.scope]
    elif args.scope in MUTANTS:
        target = str(fixture / "RESEARCH_PIPELINE_v2") + "/" + MUTANTS[args.scope][3]
    elif args.scope == "preflight_original_discovery":
        target = str(fixture / "RESEARCH_PIPELINE_v2") + "/" + PREFLIGHT_CAUSAL
    else:
        raise ValueError("unknown pure test scope")
    return pytest.main(["-c", os.devnull, "--rootdir=" + str(fixture),
                        "--confcutdir=" + str(HERE if args.scope == "fixture" else fixture), "-p", "no:cacheprovider",
                        "--basetemp=" + str(output / "pytest-fixtures"),
                        "--log-file=" + str(output / "pytest.log"),
                        "--junitxml=" + str(output / "tests.xml"), "-vv", "-rA", str(target)])


def junit(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    return [{"classname": case.get("classname"), "name": case.get("name"),
             "seconds": case.get("time"),
             "failures": [(node.text or "") + " " + node.get("message", "") for node in case.findall("failure")],
             "errors": [(node.text or "") + " " + node.get("message", "") for node in case.findall("error")],
             "skips": [node.get("message", "") for node in case.findall("skipped")]}
            for case in root.iter("testcase")]


def run_child(repo, fixture, output, scope, processes):
    output.mkdir()
    processes.checkpoint()
    child_deadline = min(processes.deadline - CLEANUP_SECONDS,
                         time.monotonic() + CHILD_SECONDS)
    argv = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", "--repo", str(repo),
            "--fixture", str(fixture), "--output", str(output), "--scope", scope,
            "--whole-deadline", str(processes.deadline), "--child-deadline", str(child_deadline)]
    started = time.monotonic()
    lifecycle = processes.execute(argv, cwd=fixture, environment=runtime_environment(fixture, output),
                                  output=output, child_seconds=child_deadline - time.monotonic())
    code, timed_out = lifecycle.get("returncode"), lifecycle["timed_out"]
    tests = junit(output / "tests.xml") if (output / "tests.xml").is_file() else []
    failures = [failure for row in tests for failure in row["failures"]]
    errors = [error for row in tests for error in row["errors"]]
    skipped = [skip for row in tests for skip in row["skips"]]
    mutant = scope in MUTANTS or scope == "preflight_original_discovery"
    successful = (lifecycle["status"] == "OWNED_PROCESS_COMPLETE"
                  and not timed_out and bool(tests) and not errors and not skipped and
                  ((code == 1 and bool(failures) and all("AssertionError" in f for f in failures))
                   if mutant else (code == 0 and not failures)))
    if scope == "manuscript_pdf" and not any(row["name"] == PDF_V2_TEST for row in tests):
        successful = False
    result = {"scope": scope, "argv": argv, "returncode": code, "timed_out": timed_out,
              "seconds": time.monotonic() - started, "test_count": len(tests), "tests": tests,
              "lifecycle": lifecycle,
              "status": ("MUTANT_KILLED_BY_ASSERTION" if mutant else "PURE_SCOPE_PASS") if successful else "HOLD",
              "stdout_sha256": sha(output / "stdout.txt"), "stderr_sha256": sha(output / "stderr.txt")}
    write_json(output / "RESULT.json", result)
    return result


def run(args) -> int:
    repo, output = args.repo.resolve(), args.output.resolve()
    if output.exists() or output.is_relative_to(repo):
        raise ValueError("fresh output outside the public repository required")
    output.mkdir(parents=True)
    started = ACTION_STARTED
    deadline = started + WHOLE_SECONDS
    processes = OwnedProcesses(deadline)
    result = {"standard": "VRS-PUBLIC-AUDIT-REMEDIATION-PURE-CHECKS-1", "status": "HOLD",
              "qualification": "isolated public source tests only; no production adoption or independent review",
              "whole_cap_seconds": WHOLE_SECONDS, "child_cap_seconds": CHILD_SECONDS, "cases": [],
              "runner_sha256": sha(Path(__file__).resolve()), "production_mutations": 0}
    try:
        with processes:
            from lifecycle_controls import run_controls
            result["lifecycle_controls"] = run_controls(processes, repo, output / "lifecycle-controls")
            processes.checkpoint()
            from public_fixture import materialize
            base = materialize(repo, output / "baseline")
            fixture = Path(base["root"])
            write_json(output / "MATERIALIZATION.json", base)
            before = source_inventory(fixture)
            for scope in SCOPES:
                case = run_child(repo, fixture, output / ("test-" + scope), scope, processes)
                result["cases"].append(case)
                if case["status"] != "PURE_SCOPE_PASS":
                    raise RuntimeError("pure scope failed: " + scope)
            if source_inventory(fixture) != before:
                raise RuntimeError("baseline tests changed the materialized source closure")
            for scope in [*MUTANTS, "preflight_original_discovery"]:
                processes.checkpoint()
                materialized = materialize(repo, output / ("fixture-" + scope))
                target_root = Path(materialized["root"])
                if scope in MUTANTS:
                    filename, old, new, _ = MUTANTS[scope]
                    target = target_root / "RESEARCH_PIPELINE_v2" / filename
                    original = target.read_bytes()
                    text = original.decode("utf-8")
                    if text.count(old) != 1:
                        raise ValueError("causal mutation anchor is not unique: " + scope)
                    target.write_text(text.replace(old, new), encoding="utf-8")
                else:
                    original_source = repo / ORIGINAL_PREFLIGHT
                    if original_source.is_symlink() or sha(original_source) != ORIGINAL_PREFLIGHT_SHA256:
                        raise ValueError("original public preflight source pin differs")
                    target = target_root / "RESEARCH_PIPELINE_v2/nightly_science_preflight.py"
                    original = target.read_bytes()
                    target.write_bytes(original_source.read_bytes())
                expected = source_inventory(target_root)
                write_json(output / ("MUTATION_" + scope + ".json"), {
                    "fixture": materialized, "target": str(target.relative_to(target_root)),
                    "before_sha256": hashlib.sha256(original).hexdigest(), "after_sha256": sha(target)})
                case = run_child(repo, target_root, output / ("test-" + scope), scope, processes)
                result["cases"].append(case)
                if case["status"] != "MUTANT_KILLED_BY_ASSERTION" or source_inventory(target_root) != expected:
                    raise RuntimeError("causal check survived, failed by infrastructure, or changed sources: " + scope)
            processes.checkpoint()
            result["status"] = "PUBLIC_PURE_SOURCE_CHECKS_PASS_NOT_ADOPTED"
    except BaseException as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
    finally:
        result["owned_processes"] = processes.records
        result["unresolved_owned_pids"] = sorted(processes.active)
        if processes.aborted or processes.active:
            result["status"] = "HOLD"
            result["lifecycle_stop"] = processes.aborted
        result["whole_seconds"] = time.monotonic() - started
        result["artifact_files"] = sum(p.is_file() for p in output.rglob("*"))
        result["artifact_bytes"] = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
        write_json(output / "RESULT.json", result)
    print(json.dumps({"status": result["status"], "output": str(output),
                      "whole_seconds": result["whole_seconds"], "case_count": len(result["cases"])}))
    return 0 if result["status"] == "PUBLIC_PURE_SOURCE_CHECKS_PASS_NOT_ADOPTED" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[2])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--fixture", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--scope", help=argparse.SUPPRESS)
    parser.add_argument("--whole-deadline", type=float, help=argparse.SUPPRESS)
    parser.add_argument("--child-deadline", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    return worker(args) if args.worker else run(args)


if __name__ == "__main__":
    raise SystemExit(main())
