#!/usr/bin/env python3
"""Bound the original coverage suites without changing their test population."""
import argparse
from collections import Counter
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASELINE = Path(__file__).with_name("verification_coverage_baseline.json")
BASELINE_SHA256 = "d16585e94635494ecd705727108a9ac3672b3aa32d677ddc28600cc668ba272d"
ACTIVE_SECONDS = 510
TERM_GRACE_SECONDS = 5
REAP_SECONDS = 1
WHOLE_JOB_SECONDS = 600
OWNERS = {
    "A": {"test_first_digest_community_successor", "test_first_digest_three_file_continuation"},
    "B": {"test_first_digest_existing_draft_recovery", "test_first_digest_uploaded_continuation"},
}
EXPECTED_SKIPS = {
    "test_coverage.CoverageTests.test_certified_real_Run142_and_tamper",
    "test_nightly_note_typography.NoteTypographyTests.test_long_identifiers_render_fully_without_overfull_lines",
    "test_review_regressions.IndependentCoverageReview.test_real_receipt_cannot_certify_swapped_candidate",
    "test_review_regressions.IndependentCoverageReview.test_real_receipt_cannot_certify_swapped_sealed_paper",
    "test_review_regressions.IndependentCoverageReview.test_real_receipt_cannot_move_certification_to_another_run",
}
STARTS = {
    "primary": ("00_lab_infrastructure/gates", "test*.py"),
    "secondary": ("00_lab_infrastructure/gates/standalone_pdf_release/tests", "test_*.py"),
}


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path, limit=2_000_000):
    path = Path(path)
    need(not path.is_symlink() and stat.S_ISREG(path.stat().st_mode), "REGULAR_JSON_REQUIRED")
    need(path.stat().st_size <= limit, "JSON_SIZE_BOUND")
    raw = path.read_bytes()
    need(len(raw) <= limit, "JSON_SIZE_BOUND")
    return json.loads(raw, object_pairs_hook=no_duplicate_keys)


def write_json(path, value):
    path = Path(path)
    need(not path.is_symlink() and not path.exists(), "EXCLUSIVE_OUTPUT_REQUIRED")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(encoded(value).decode() + "\n")


def baseline():
    need(not BASELINE.is_symlink() and stat.S_ISREG(BASELINE.stat().st_mode), "REGULAR_BASELINE")
    raw = BASELINE.read_bytes()
    need(sha(raw) == BASELINE_SHA256, "BASELINE_SHA")
    value = json.loads(raw, object_pairs_hook=no_duplicate_keys)
    need(set(value) == {"primary", "secondary"}, "BASELINE_PHASES")
    need(sum(len(ids) for _, ids in value["primary"]) == 2196, "PRIMARY_POPULATION")
    need(sum(len(ids) for _, ids in value["secondary"]) == 188, "SECONDARY_POPULATION")
    return value


def test_ids(suite):
    if isinstance(suite, unittest.TestSuite):
        return [item for child in suite for item in test_ids(child)]
    return [suite.id()]


class CoverageLoader(unittest.TestLoader):
    """Discover/import everything before selecting whole owner-module suites."""

    def __init__(self):
        super().__init__()
        self.owners = []

    def loadTestsFromModule(self, module, *args, **kwargs):
        suite = super().loadTestsFromModule(module, *args, **kwargs)
        ids = test_ids(suite)
        if ids:
            self.owners.append((module.__name__, ids, suite))
        return suite


def shard_for(owner):
    for shard, owners in OWNERS.items():
        if owner in owners:
            return shard
    return "C"


def expected_ids(value, phase, shard):
    return [ident for owner, ids in value[phase]
            if phase == "secondary" or shard_for(owner) == shard for ident in ids]


def select_shard(loader, value, phase, shard):
    need(shard in {"A", "B", "C"}, "UNKNOWN_SHARD")
    observed = [[owner, ids] for owner, ids, _ in loader.owners]
    need(not loader.errors and observed == value[phase], "DISCOVERY_ORDER_OR_POPULATION_DRIFT")
    selected = [suite for owner, _, suite in loader.owners
                if phase == "secondary" or shard_for(owner) == shard]
    need(selected and (phase != "secondary" or shard == "C"), "EMPTY_OR_WRONG_PHASE")
    return unittest.TestSuite(selected)


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executions = []
        self.skip_event_ids = []
        self.active = None

    def startTest(self, test):
        super().startTest(test)
        self.executions.append({"id": test.id(), "outcome": "started"})
        self.active = len(self.executions) - 1

    def outcome(self, value):
        if self.active is not None:
            self.executions[self.active]["outcome"] = value

    def addSuccess(self, test):
        super().addSuccess(test)
        self.outcome("ok")

    def addSkip(self, test, reason):
        self.skip_event_ids.append(test.id())
        super().addSkip(test, reason)
        self.outcome("skipped")

    def addError(self, test, err):
        super().addError(test, err)
        self.outcome("error")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.outcome("failure")

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.outcome("expected_failure")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.outcome("unexpected_success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.outcome("failure")

    def stopTest(self, test):
        super().stopTest(test)
        self.active = None


def validate_phase(report, value, phase, shard):
    need(set(report) == {"phase", "discovery_sha256", "success", "executions", "skip_event_ids"}, "PHASE_SCHEMA")
    need(report["phase"] == phase and report["success"] is True, "UNSUCCESSFUL_PHASE")
    need(report["discovery_sha256"] == sha(encoded(value[phase])), "FULL_DISCOVERY_BINDING")
    rows = report["executions"]
    need(isinstance(rows, list) and all(set(r) == {"id", "outcome"} for r in rows), "EXECUTION_SCHEMA")
    expected = expected_ids(value, phase, shard)
    need([r["id"] for r in rows] == expected, "ACTUAL_EXECUTION_ORDER_OR_MULTIPLICITY")
    need(all(r["outcome"] in {"ok", "skipped"} for r in rows), "UNSUCCESSFUL_EXECUTION")
    skips = Counter(r["id"] for r in rows if r["outcome"] == "skipped")
    wanted = Counter(ident for ident in expected if ident in EXPECTED_SKIPS)
    need(skips == wanted, "UNEXPECTED_OR_MISSING_SKIP")
    raw_skips = report["skip_event_ids"]
    need(isinstance(raw_skips, list) and all(isinstance(ident, str) for ident in raw_skips), "RAW_SKIP_SCHEMA")
    need(Counter(raw_skips) == wanted, "RAW_SKIP_EVENT_MULTISET")
    need(Counter(raw_skips) == skips, "OUTCOME_SKIP_CROSSCHECK")
    return rows


def seconds(value, cap=WHOLE_JOB_SECONDS):
    need(type(value) in {int, float} and math.isfinite(value) and 0 <= value <= cap, "INVALID_OR_OVER_CAP_TIME")
    return value


def group_exists(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def signal_group(pid, sig):
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


def cleanup_group(process, grace=TERM_GRACE_SECONDS):
    started = time.monotonic()
    signal_group(process.pid, signal.SIGTERM)
    term_deadline = started + grace
    while True:
        process.poll()  # Reap our own exited leader BEFORE the independent query.
        if not group_exists(process.pid):  # EPERM always propagates as a failure.
            need(process.poll() is not None, "LEADER_ESCAPED_OR_UNREAPED")
            return time.monotonic() - started
        if time.monotonic() >= term_deadline:
            break
        time.sleep(min(0.01, max(0, term_deadline - time.monotonic())))
    signal_group(process.pid, signal.SIGKILL)
    post_kill_deadline = time.monotonic() + REAP_SECONDS
    while True:
        process.poll()
        if not group_exists(process.pid):
            need(process.poll() is not None, "LEADER_ESCAPED_OR_UNREAPED")
            return time.monotonic() - started
        need(time.monotonic() < post_kill_deadline, "PROCESS_GROUP_STILL_PRESENT_AFTER_KILL")
        time.sleep(min(0.01, max(0, post_kill_deadline - time.monotonic())))


def run_bounded_command(argv, cwd, deadline, grace=TERM_GRACE_SECONDS):
    """One absolute active deadline shared across every phase; never per-child reset."""
    remaining = deadline - time.monotonic()
    need(remaining > 0, "ACTIVE_BUDGET_EXHAUSTED")
    started = time.monotonic()
    process = subprocess.Popen(argv, cwd=cwd, start_new_session=True)
    timed_out = False
    try:
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = None
    finally:
        cleanup_seconds = cleanup_group(process, grace)
    return {"returncode": returncode, "timed_out": timed_out,
            "seconds": time.monotonic() - started, "cleanup_seconds": cleanup_seconds,
            "leader_reaped": process.poll() is not None, "group_absent": True}


def context(revision, source_head):
    need(len(revision) == 40 and all(c in "0123456789abcdef" for c in revision), "REVISION")
    need(len(source_head) == 40 and all(c in "0123456789abcdef" for c in source_head), "SOURCE_HEAD")
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, timeout=5).strip()
    need(actual == revision, "ACTUAL_CHECKOUT")
    run_id, attempt = os.environ.get("GITHUB_RUN_ID", ""), os.environ.get("GITHUB_RUN_ATTEMPT", "")
    need(run_id.isdigit() and attempt.isdigit() and int(attempt) >= 1, "ACTUAL_RUN_CONTEXT")
    return {"revision": revision, "source_head": source_head, "run_id": int(run_id),
            "attempt": int(attempt), "baseline_sha256": BASELINE_SHA256,
            "runner_sha256": sha(Path(__file__).read_bytes())}


def execute(phase, shard, output):
    value = baseline()
    start, pattern = STARTS[phase]
    sys.path[0] = str(ROOT)  # Match python -m unittest before default discovery.
    loader = CoverageLoader()
    loader.discover(str(ROOT / start), pattern=pattern)
    suite = select_shard(loader, value, phase, shard)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
    report = {"phase": phase, "discovery_sha256": sha(encoded(value[phase])),
              "success": result.wasSuccessful(), "executions": result.executions,
              "skip_event_ids": result.skip_event_ids}
    write_json(output, report)
    validate_phase(report, value, phase, shard)


def run_shard(shard, output, revision, source_head):
    value = baseline()
    binding = context(revision, source_head)
    need(not output.exists() and all(not output.with_name(shard + "-" + p + ".json").exists() for p in ("primary", "secondary")), "NO_AUTOMATIC_REPLAY")
    write_json(output.with_suffix(".claim.json"), {"schema": "VRS-COVERAGE-SHARD-ATTEMPT-1", "shard": shard, **binding})
    started = time.monotonic()
    deadline = started + ACTIVE_SECONDS
    report = {"schema": "VRS-COVERAGE-SHARD-1", "shard": shard, **binding,
              "status": "FAIL", "phases": [], "commands": []}
    try:
        for phase in (["primary", "secondary"] if shard == "C" else ["primary"]):
            phase_output = output.with_name(shard + "-" + phase + ".json")
            command = [sys.executable, str(Path(__file__).resolve()), "execute",
                       "--phase", phase, "--shard", shard, "--output", str(phase_output)]
            timing = run_bounded_command(command, ROOT, deadline)
            report["commands"].append(timing)
            need(timing["returncode"] == 0 and not timing["timed_out"] and timing["leader_reaped"], "CHILD_FAILURE_OR_TIMEOUT")
            phase_report = read_json(phase_output)
            validate_phase(phase_report, value, phase, shard)
            report["phases"].append(phase_report)
        report["status"] = "PASS"
    finally:
        report["runner_seconds"] = time.monotonic() - started
        write_json(output, report)


def elapsed(start, end):
    need(isinstance(start, str) and isinstance(end, str), "MISSING_API_TIME")
    before, after = (dt.datetime.fromisoformat(x.replace("Z", "+00:00")) for x in (start, end))
    need(before.tzinfo is not None and after.tzinfo is not None, "NAIVE_API_TIME")
    return seconds((after - before).total_seconds())


def validate_jobs(api, binding):
    need(type(api.get("total_count")) is int and api["total_count"] == len(api.get("jobs", [])), "TRUNCATED_JOB_API")
    timings = {}
    for shard in ("A", "B", "C"):
        name = "coverage-shard (" + shard + ")"
        rows = [j for j in api["jobs"] if j["name"] == name]
        need(len(rows) == 1, "MISSING_OR_DUPLICATE_SHARD_JOB")
        job = rows[0]
        need(job["run_id"] == binding["run_id"] and job["run_attempt"] == binding["attempt"]
             and job["head_sha"] == binding["source_head"], "JOB_SOURCE_OR_ATTEMPT")
        need(job["status"] == "completed" and job["conclusion"] == "success", "UNSUCCESSFUL_SHARD_JOB")
        whole = elapsed(job.get("started_at"), job.get("completed_at"))
        steps = job.get("steps", [])
        required = {"Runner regression controls", "Run coverage shard", "Retain shard report"}
        need(all(sum(s["name"] == n and s["conclusion"] == "success" for s in steps) == 1 for n in required), "REQUIRED_STEP_MISSING")
        for step in steps:
            need(step["status"] == "completed" and step["conclusion"] in {"success", "skipped"}, "UNSUCCESSFUL_STEP")
            if step["conclusion"] != "skipped":
                elapsed(step.get("started_at"), step.get("completed_at"))
        timings[shard] = {"job_id": job["id"], "whole_job_seconds": whole}
    return timings


def aggregate(reports, value, binding, api, matrix_status):
    need(matrix_status == "success" and len(reports) == 3, "MISSING_OR_FAILED_MATRIX")
    need(Counter(r["shard"] for r in reports) == Counter({"A": 1, "B": 1, "C": 1}), "SHARD_SET")
    executions = []
    for report in reports:
        need(set(report) == {"schema", "shard", *binding, "status", "phases", "commands", "runner_seconds"}, "REPORT_SCHEMA")
        need(report["schema"] == "VRS-COVERAGE-SHARD-1" and report["status"] == "PASS", "FAILED_REPORT")
        need(all(report[k] == v for k, v in binding.items()), "REPORT_SOURCE_OR_ATTEMPT")
        shard = report["shard"]
        phases = ["primary", "secondary"] if shard == "C" else ["primary"]
        need(len(report["phases"]) == len(phases) == len(report["commands"]), "PHASE_OR_COMMAND_SET")
        seconds(report["runner_seconds"], ACTIVE_SECONDS + TERM_GRACE_SECONDS + REAP_SECONDS)
        for phase, phase_report, command in zip(phases, report["phases"], report["commands"]):
            need(set(command) == {"returncode", "timed_out", "seconds", "cleanup_seconds", "leader_reaped", "group_absent"}, "COMMAND_SCHEMA")
            need(type(command["returncode"]) is int and command["returncode"] == 0 and command["timed_out"] is False and command["leader_reaped"] is True and command["group_absent"] is True, "FAILED_COMMAND")
            seconds(command["seconds"], ACTIVE_SECONDS + TERM_GRACE_SECONDS + REAP_SECONDS)
            seconds(command["cleanup_seconds"], TERM_GRACE_SECONDS + REAP_SECONDS + 0.25)
            rows = validate_phase(phase_report, value, phase, shard)
            executions.extend((phase, r["id"]) for r in rows)
    expected = Counter((phase, ident) for phase in ("primary", "secondary")
                       for _, ids in value[phase] for ident in ids)
    need(Counter(executions) == expected, "INCOMPLETE_EXECUTION_MULTISET")
    return {"status": "PASS", "executions": len(executions),
            "skips": len(EXPECTED_SKIPS), "jobs": validate_jobs(api, binding)}


def report_path(path):
    path = Path(path).absolute()
    directory = ROOT / ".ci-coverage"
    need(path.is_relative_to(directory) and ".." not in path.parts, "CI_OUTPUT_SCOPE")
    for parent in [directory, *path.parents]:
        if parent.exists():
            need(not parent.is_symlink(), "OUTPUT_PARENT_SYMLINK")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("execute", "run-shard"):
        arg = sub.add_parser(name)
        arg.add_argument("--shard", choices=("A", "B", "C"), required=True)
        arg.add_argument("--output", type=Path, required=True)
        if name == "execute":
            arg.add_argument("--phase", choices=("primary", "secondary"), required=True)
        else:
            arg.add_argument("--revision", required=True)
            arg.add_argument("--source-head", required=True)
    arg = sub.add_parser("aggregate")
    arg.add_argument("--reports", type=Path, required=True)
    arg.add_argument("--api-jobs", type=Path, required=True)
    arg.add_argument("--revision", required=True)
    arg.add_argument("--source-head", required=True)
    arg.add_argument("--matrix-status", required=True)
    args = parser.parse_args()
    if args.command == "execute":
        execute(args.phase, args.shard, report_path(args.output))
    elif args.command == "run-shard":
        run_shard(args.shard, report_path(args.output), args.revision, args.source_head)
    else:
        reports_directory = report_path(args.reports)
        api_path = report_path(args.api_jobs)
        paths = sorted(reports_directory.iterdir())
        need([p.name for p in paths] == ["report-A.json", "report-B.json", "report-C.json"], "ARTIFACT_SET")
        result = aggregate([read_json(p) for p in paths], baseline(),
                           context(args.revision, args.source_head), read_json(api_path),
                           args.matrix_status)
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    def interrupted(signum, frame):
        raise InterruptedError("WORKFLOW_INTERRUPTED")
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    main()
