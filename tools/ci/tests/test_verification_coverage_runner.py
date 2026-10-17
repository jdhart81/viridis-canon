"""Inert runner controls only: no gate imports, Core access or network calls."""
import ast
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import verification_coverage_runner as runner


def fixtures():
    skips = sorted(runner.EXPECTED_SKIPS)
    value = {"primary": [
        ["test_first_digest_community_successor", ["inert.A"]],
        ["test_first_digest_existing_draft_recovery", ["inert.B"]],
        ["inert_remainder", ["inert.shared", "inert.shared", *skips]]],
        "secondary": [["inert_secondary", ["inert.secondary"]]]}
    binding = {"revision": "1" * 40, "source_head": "0" * 40, "run_id": 7,
               "attempt": 1, "baseline_sha256": "INERT", "runner_sha256": "INERT"}
    reports, jobs = [], []
    for index, shard in enumerate("ABC"):
        phases = []
        for phase in (["primary", "secondary"] if shard == "C" else ["primary"]):
            phases.append({"phase": phase, "success": True,
                "discovery_sha256": runner.sha(runner.encoded(value[phase])),
                "executions": [{"id": ident, "outcome": "skipped" if ident in skips else "ok"}
                               for ident in runner.expected_ids(value, phase, shard)],
                "skip_event_ids": [ident for ident in runner.expected_ids(value, phase, shard) if ident in skips]})
        reports.append({"schema": "VRS-COVERAGE-SHARD-1", "shard": shard, **binding,
                        "status": "PASS", "phases": phases, "runner_seconds": 1,
                        "commands": [{"returncode": 0, "timed_out": False, "seconds": 1,
                                      "cleanup_seconds": 0, "leader_reaped": True, "group_absent": True} for _ in phases]})
        steps = [{"name": name, "status": "completed", "conclusion": "success",
                  "started_at": "2020-01-01T00:00:00Z", "completed_at": "2020-01-01T00:00:01Z"}
                 for name in ("Runner regression controls", "Run coverage shard", "Retain shard report")]
        jobs.append({"id": index + 1, "name": "coverage-shard (" + shard + ")",
                     "run_id": 7, "run_attempt": 1, "head_sha": "0" * 40,
                     "status": "completed", "conclusion": "success",
                     "started_at": "2020-01-01T00:00:00Z", "completed_at": "2020-01-01T00:00:03Z",
                     "steps": steps})
    return value, binding, reports, {"total_count": 3, "jobs": jobs}


def mutated(reason):
    tree = ast.parse(Path(runner.__file__).read_text())
    class RemoveGuard(ast.NodeTransformer):
        count = 0
        def visit_Expr(self, node):
            call = node.value
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "need" and len(call.args) == 2
                    and isinstance(call.args[1], ast.Constant) and call.args[1].value == reason):
                self.count += 1
                return ast.copy_location(ast.Pass(), node)
            return self.generic_visit(node)
    transform = RemoveGuard()
    tree = transform.visit(tree)
    if not transform.count:
        raise AssertionError("Mutation target missing: " + reason)
    namespace = {"__name__": "INERT_RUNNER_MUTANT", "__file__": runner.__file__}
    exec(compile(ast.fix_missing_locations(tree), runner.__file__, "exec"), namespace)
    return namespace


def causal_mutant(kind):
    """Prospective inert controls; neither mutation admits real shard reports."""
    tree = ast.parse(Path(runner.__file__).read_text())
    class AlterOneProducer(ast.NodeTransformer):
        count = 0

        def visit_FunctionDef(self, node):
            if kind == "POST_KILL_ABSENCE_QUERY_BYPASS" and node.name == "cleanup_group":
                matches = [index for index, item in enumerate(node.body)
                           if isinstance(item, ast.Assign) and any(
                               isinstance(target, ast.Name) and target.id == "post_kill_deadline"
                               for target in item.targets)]
                if len(matches) != 1 or matches[0] + 1 != len(node.body) - 1:
                    raise AssertionError("Post-KILL mutation shape drift")
                loop = node.body[-1]
                if not isinstance(loop, ast.While) or not any(
                        isinstance(item, ast.Constant)
                        and item.value == "PROCESS_GROUP_STILL_PRESENT_AFTER_KILL"
                        for item in ast.walk(loop)):
                    raise AssertionError("Post-KILL proof loop missing")
                # Bypass exactly the bounded post-KILL proof, leaving TERM,
                # KILL and the ordinary pre-KILL group query unchanged.
                node.body[-1] = ast.copy_location(ast.Return(value=ast.BinOp(
                    left=ast.Call(func=ast.Attribute(value=ast.Name(id="time", ctx=ast.Load()),
                                                    attr="monotonic", ctx=ast.Load()), args=[], keywords=[]),
                    op=ast.Sub(), right=ast.Name(id="started", ctx=ast.Load()))), loop)
                self.count += 1
                return node
            return self.generic_visit(node)

        def visit_ClassDef(self, node):
            if kind == "RAW_SKIP_LEDGER_APPEND_REMOVAL" and node.name == "RecordingResult":
                for method in node.body:
                    if not isinstance(method, ast.FunctionDef) or method.name != "addSkip":
                        continue
                    for index, item in enumerate(method.body):
                        if (isinstance(item, ast.Expr) and isinstance(item.value, ast.Call)
                                and isinstance(item.value.func, ast.Attribute)
                                and item.value.func.attr == "append"
                                and isinstance(item.value.func.value, ast.Attribute)
                                and item.value.func.value.attr == "skip_event_ids"
                                and isinstance(item.value.func.value.value, ast.Name)
                                and item.value.func.value.value.id == "self"):
                            method.body[index] = ast.copy_location(ast.Pass(), item)
                            self.count += 1
                return node
            return self.generic_visit(node)
    transform = AlterOneProducer()
    tree = transform.visit(tree)
    if transform.count != 1:
        raise AssertionError("Mutation must change exactly one producer: " + kind)
    namespace = {"__name__": "INERT_RUNNER_MUTANT", "__file__": runner.__file__}
    exec(compile(ast.fix_missing_locations(tree), runner.__file__, "exec"), namespace)
    return namespace


def isolated_function(function, **overrides):
    """Copy only function globals; never patch shared modules or the real clock."""
    namespace = dict(function.__globals__)
    namespace.update(overrides)
    return types.FunctionType(function.__code__, namespace, function.__name__,
                              function.__defaults__, function.__closure__)


class LoaderControls(unittest.TestCase):
    def make_loader(self):
        class Shared(unittest.TestCase):
            def test_one(self):
                pass
        Shared.__module__, Shared.__qualname__ = "inert_shared", "Shared"
        class Derived(Shared):
            def test_extra(self):
                pass
        Derived.__module__, Derived.__qualname__ = "inert_derived", "Derived"
        Generated = type("Generated", (unittest.TestCase,), {"test_dynamic": lambda self: None})
        Generated.__module__ = "inert_generated"
        first = types.ModuleType("test_first_digest_community_successor")
        first.Shared = Shared
        rest = types.ModuleType("inert_remainder")
        rest.Derived, rest.Shared = Derived, Shared
        def load_tests(loader, ordinary, pattern):
            return unittest.TestSuite([ordinary, loader.loadTestsFromTestCase(Generated)])
        rest.load_tests = load_tests
        loader = runner.CoverageLoader()
        loader.loadTestsFromModule(first)
        loader.loadTestsFromModule(rest)
        expected = {"primary": [
            [first.__name__, ["inert_shared.Shared.test_one"]],
            [rest.__name__, ["inert_derived.Derived.test_extra", "inert_derived.Derived.test_one",
                            "inert_shared.Shared.test_one", "inert_generated.Generated.test_dynamic"]]],
            "secondary": []}
        return loader, expected

    def test_duplicate_import_inheritance_generation_and_load_tests_retained(self):
        loader, expected = self.make_loader()
        selected = runner.select_shard(loader, expected, "primary", "C")
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=runner.RecordingResult).run(selected)
        self.assertTrue(result.wasSuccessful())
        self.assertEqual([r["id"] for r in result.executions], expected["primary"][1][1])
        self.assertEqual([x[:2] for x in loader.owners], [tuple(x) for x in expected["primary"]])

    def test_full_discovery_required_even_when_selected_shard_unchanged(self):
        loader, expected = self.make_loader()
        expected["primary"][1][1].append("inert.NEW")
        with self.assertRaisesRegex(ValueError, "DISCOVERY"):
            runner.select_shard(loader, expected, "primary", "A")

    def test_committed_manifest_preserves_original_multiplicity(self):
        value = runner.baseline()
        primary = [ident for _, ids in value["primary"] for ident in ids]
        secondary = [ident for _, ids in value["secondary"] for ident in ids]
        self.assertEqual((len(primary), len(set(primary)), len(secondary)), (2196, 2164, 188))
        self.assertFalse(set(primary) & set(secondary))
        self.assertEqual(len(set(primary) & runner.EXPECTED_SKIPS), 5)


class AggregateControls(unittest.TestCase):
    def setUp(self):
        self.value, self.binding, self.reports, self.api = fixtures()

    def check(self):
        return runner.aggregate(self.reports, self.value, self.binding, self.api, "success")

    def test_complete_inert_multiset_is_required_including_repeats_and_skips(self):
        self.assertEqual(self.check()["executions"], 10)
        self.assertEqual(self.check()["skips"], 5)

    def test_missing_extra_and_duplicate_shards_refused(self):
        for reports in ([], self.reports[:2], self.reports + [self.reports[0]],
                        [self.reports[0], self.reports[0], self.reports[2]]):
            with self.subTest(length=len(reports)), self.assertRaises(ValueError):
                runner.aggregate(reports, self.value, self.binding, self.api, "success")

    def test_actual_execution_drop_extra_or_reorder_refused(self):
        for edit in ("drop", "extra", "order"):
            reports = copy.deepcopy(self.reports)
            rows = reports[2]["phases"][0]["executions"]
            if edit == "drop":
                rows.pop()
            elif edit == "extra":
                rows.append(dict(rows[0]))
            else:
                rows[0], rows[-1] = rows[-1], rows[0]
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                runner.aggregate(reports, self.value, self.binding, self.api, "success")

    def test_wrong_source_attempt_baseline_runner_or_discovery_refused(self):
        for key, wrong in (("revision", "2" * 40), ("attempt", 2),
                           ("baseline_sha256", "WRONG"), ("runner_sha256", "WRONG")):
            reports = copy.deepcopy(self.reports)
            reports[0][key] = wrong
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "SOURCE_OR_ATTEMPT"):
                runner.aggregate(reports, self.value, self.binding, self.api, "success")
        self.reports[0]["phases"][0]["discovery_sha256"] = "WRONG"
        with self.assertRaisesRegex(ValueError, "DISCOVERY"):
            self.check()

    def test_missing_expected_skip_extra_skip_and_unittest_failure_refused(self):
        for edit in ("missing", "extra", "failure"):
            reports = copy.deepcopy(self.reports)
            rows = reports[2]["phases"][0]["executions"]
            if edit == "missing":
                rows[-1]["outcome"] = "ok"
            elif edit == "extra":
                rows[0]["outcome"] = "skipped"
            else:
                rows[0]["outcome"] = "failure"
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                runner.aggregate(reports, self.value, self.binding, self.api, "success")

    def test_missing_secondary_failed_matrix_and_cancelled_job_refused(self):
        self.reports[2]["phases"].pop()
        with self.assertRaisesRegex(ValueError, "PHASE_OR_COMMAND"):
            self.check()
        self.value, self.binding, self.reports, self.api = fixtures()
        with self.assertRaisesRegex(ValueError, "MATRIX"):
            runner.aggregate(self.reports, self.value, self.binding, self.api, "cancelled")
        self.api["jobs"][0]["conclusion"] = "cancelled"
        with self.assertRaisesRegex(ValueError, "UNSUCCESSFUL_SHARD"):
            self.check()

    def test_actual_whole602_or_step602_and_missing_timing_refused(self):
        for field in ("whole", "step", "missing"):
            api = copy.deepcopy(self.api)
            target = api["jobs"][0] if field != "step" else api["jobs"][0]["steps"][0]
            target["completed_at"] = None if field == "missing" else "2020-01-01T00:10:02Z"
            with self.subTest(field=field), self.assertRaises(ValueError):
                runner.aggregate(self.reports, self.value, self.binding, api, "success")

    def test_leader_reap_without_group_absence_is_refused(self):
        self.reports[0]["commands"][0]["group_absent"] = False
        with self.assertRaisesRegex(ValueError, "FAILED_COMMAND"):
            self.check()
        self.reports[0]["commands"][0].pop("group_absent")
        with self.assertRaisesRegex(ValueError, "COMMAND_SCHEMA"):
            self.check()

    def test_nonfinite_negative_boolean_and_truncated_api_refused(self):
        for value in (float("nan"), float("inf"), -1, True, 602):
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                runner.seconds(value)
        self.api["total_count"] = 4
        with self.assertRaisesRegex(ValueError, "TRUNCATED"):
            self.check()

    def test_eight_causal_guard_mutants_are_killed_by_negative_oracles(self):
        checks = []
        # Each original rejection below is a regression oracle. Removing only
        # its named guard admits the same inert bad input, proving causality.
        phase = copy.deepcopy(self.reports[0]["phases"][0])
        phase["executions"].append(dict(phase["executions"][0]))
        checks.append(("ACTUAL_EXECUTION_ORDER_OR_MULTIPLICITY", "validate_phase",
                       (phase, self.value, "primary", "A")))
        phase = copy.deepcopy(self.reports[0]["phases"][0])
        phase["discovery_sha256"] = "WRONG"
        checks.append(("FULL_DISCOVERY_BINDING", "validate_phase", (phase, self.value, "primary", "A")))
        reports = copy.deepcopy(self.reports)
        reports[0]["commands"][0]["unrecognized"] = True
        checks.append(("COMMAND_SCHEMA", "aggregate",
                       (reports, self.value, self.binding, self.api, "success")))
        phase = copy.deepcopy(self.reports[0]["phases"][0])
        phase["success"] = False
        checks.append(("UNSUCCESSFUL_PHASE", "validate_phase", (phase, self.value, "primary", "A")))
        checks.append(("INVALID_OR_OVER_CAP_TIME", "seconds", (602,)))
        api = copy.deepcopy(self.api)
        api["jobs"][0]["conclusion"] = "cancelled"
        checks.append(("UNSUCCESSFUL_SHARD_JOB", "validate_jobs", (api, self.binding)))
        reports = copy.deepcopy(self.reports)
        reports[0]["revision"] = "2" * 40
        checks.append(("REPORT_SOURCE_OR_ATTEMPT", "aggregate",
                       (reports, self.value, self.binding, self.api, "success")))
        checks.append(("MISSING_OR_FAILED_MATRIX", "aggregate",
                       (self.reports, self.value, self.binding, self.api, "cancelled")))
        for reason, function, args in checks:
            with self.subTest(mutant=reason):
                with self.assertRaisesRegex(ValueError, reason):
                    getattr(runner, function)(*args)
                mutated(reason)[function](*args)
        print(json.dumps({"inert_causal_runner_mutants": len(checks), "killed": len(checks)}))



class RawSkipControls(unittest.TestCase):
    def exercise(self, kind, resultclass=runner.RecordingResult):
        name = "inert_raw_skip_" + kind
        module = types.ModuleType(name)
        def skipped(*args):
            raise unittest.SkipTest("inert control")
        def subtest(self):
            with self.subTest(part="inert"):
                self.skipTest("inert subtest skip")
        attrs = {"__module__": name, "test_one": subtest if kind == "subtest" else lambda self: None}
        if kind == "class":
            attrs["setUpClass"] = classmethod(skipped)
        module.Case = type("Case", (unittest.TestCase,), attrs)
        if kind == "module":
            module.setUpModule = skipped
        sys.modules[name] = module
        try:
            loader = runner.CoverageLoader()
            suite = loader.loadTestsFromModule(module)
            value = {"primary": [[name, runner.test_ids(suite)]], "secondary": []}
            result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=resultclass).run(suite)
            report = {"phase": "primary", "success": result.wasSuccessful(),
                      "discovery_sha256": runner.sha(runner.encoded(value["primary"])),
                      "executions": result.executions, "skip_event_ids": result.skip_event_ids}
            self.assertTrue(result.wasSuccessful())  # Ordinary unittest permits these skips.
            self.assertEqual(result.skip_event_ids, [test.id() for test, _ in result.skipped],
                             "RAW_SKIP_LEDGER_EVENT_LOST")
            self.assertEqual(len(result.skip_event_ids), 1)
            with self.assertRaises(ValueError):
                runner.validate_phase(report, value, "primary", "C")
            return report
        finally:
            sys.modules.pop(name)

    def test_subtest_skip_remains_visible_independent_of_parent_outcome(self):
        report = self.exercise("subtest")
        self.assertEqual(len(report["executions"]), 1)
        self.assertNotEqual(report["skip_event_ids"][0], report["executions"][0]["id"])
        # A skipped subTest need not be followed by parent addSuccess. The
        # real skip event must survive either parent outcome.
        parent_ok = copy.deepcopy(report)
        parent_ok["executions"][0]["outcome"] = "ok"
        value = {"primary": [["inert_raw_skip_subtest", [report["executions"][0]["id"]]]],
                 "secondary": []}
        with self.assertRaisesRegex(ValueError, "RAW_SKIP_EVENT_MULTISET"):
            runner.validate_phase(parent_ok, value, "primary", "C")

    def test_class_skiptest_does_not_fake_started_test_executions(self):
        report = self.exercise("class")
        self.assertEqual(report["executions"], [])
        self.assertIn("setUpClass", report["skip_event_ids"][0])

    def test_module_skiptest_does_not_fake_started_test_executions(self):
        report = self.exercise("module")
        self.assertEqual(report["executions"], [])
        self.assertIn("setUpModule", report["skip_event_ids"][0])

    def test_raw_skip_append_removal_mutant_is_killed_by_subtest_ledger_oracle(self):
        self.exercise("subtest")
        mutant = causal_mutant("RAW_SKIP_LEDGER_APPEND_REMOVAL")
        with self.assertRaisesRegex(self.failureException, "RAW_SKIP_LEDGER_EVENT_LOST"):
            self.exercise("subtest", resultclass=mutant["RecordingResult"])
        print(json.dumps({"inert_raw_skip_ledger_mutants": 1, "killed": 1,
                          "oracle": "test_subtest_skip_remains_visible_independent_of_parent_outcome"}))


class DeadlineControls(unittest.TestCase):
    def persistent_group_rejection_oracle(self, cleanup):
        # Negative-only causal fixture: the group is ALWAYS reported present.
        # It proves fail-closed deadline logic, never actual OS group absence.
        class Clock:
            now = 0.0
            def monotonic(self):
                return self.now
            def sleep(self, delay):
                if not 0 <= delay <= 0.01:
                    raise AssertionError("Unbounded inert wait")
                self.now += max(delay, 0.000001)
        clock, signals, queries = Clock(), [], []
        process = types.SimpleNamespace(pid=4242, poll=lambda: 0)
        def signal_group(pid, sig):
            signals.append((pid, sig))
        def group_exists(pid):
            queries.append((pid, len(signals), clock.now))
            return True
        command = isolated_function(cleanup, time=clock, signal_group=signal_group,
                                    group_exists=group_exists)
        with self.assertRaisesRegex(ValueError, "PROCESS_GROUP_STILL_PRESENT_AFTER_KILL"):
            command(process, grace=0.02)
        self.assertEqual(signals, [(4242, runner.signal.SIGTERM), (4242, runner.signal.SIGKILL)])
        self.assertTrue(any(phase == 2 for _, phase, _ in queries))
        self.assertGreaterEqual(clock.now, 0.02 + runner.REAP_SECONDS)
        self.assertLess(clock.now, 0.03 + runner.REAP_SECONDS)

    def test_post_kill_persistent_group_is_rejected_by_bounded_absence_query(self):
        self.persistent_group_rejection_oracle(runner.cleanup_group)

    def test_post_kill_absence_query_bypass_mutant_is_killed_by_named_oracle(self):
        self.persistent_group_rejection_oracle(runner.cleanup_group)
        mutant = causal_mutant("POST_KILL_ABSENCE_QUERY_BYPASS")
        with self.assertRaisesRegex(self.failureException, "ValueError not raised"):
            self.persistent_group_rejection_oracle(mutant["cleanup_group"])
        print(json.dumps({"inert_post_kill_absence_mutants": 1, "killed": 1,
                          "oracle": "test_post_kill_persistent_group_is_rejected_by_bounded_absence_query"}))

    def test_timeout_kills_process_group_and_reaps_child(self):
        with tempfile.TemporaryDirectory() as directory:
            started = time.monotonic()
            result = runner.run_bounded_command([sys.executable, "-c", "import time;time.sleep(60)"],
                                                directory, started + 0.05, grace=0.05)
            self.assertTrue(result["timed_out"])
            self.assertTrue(result["leader_reaped"])
            self.assertTrue(result["group_absent"])
            self.assertLess(time.monotonic() - started, 2)


    def test_term_ignoring_leader_and_descendant_are_killed_and_group_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            child = ("import os,signal,time;from pathlib import Path;"
                     "signal.signal(signal.SIGTERM,lambda *_:Path('child-term').write_text('TERM'));"
                     "Path('child-pid').write_text(str(os.getpid()));"
                     "Path('child-ready').write_text('ready');"
                     "deadline=time.monotonic()+10;exec('while time.monotonic()<deadline: time.sleep(.01)')")
            leader = ("import signal,time,subprocess,sys;from pathlib import Path;"
                      "signal.signal(signal.SIGTERM,lambda *_:Path('leader-term').write_text('TERM'));"
                      "subprocess.Popen([sys.executable,'-c'," + repr(child) + "]);"
                      "deadline=time.monotonic()+10;exec('while time.monotonic()<deadline: time.sleep(.01)')")
            observed = []
            def observed_popen(*args, **kwargs):
                self.assertIs(kwargs["start_new_session"], True)
                process = runner.subprocess.Popen(*args, **kwargs)
                observed.append(process)
                return process
            # A transparent wrapper captures the genuine Popen PID. The
            # command, cleanup, actual signals and real clock remain intact.
            command = isolated_function(runner.run_bounded_command,
                subprocess=types.SimpleNamespace(Popen=observed_popen,
                                                 TimeoutExpired=runner.subprocess.TimeoutExpired))
            started = time.monotonic()
            result = command([sys.executable, "-c", leader], directory, started + 5, grace=0.25)
            self.assertEqual(len(observed), 1)
            leader_pid = observed[0].pid
            child_pid = int((Path(directory) / "child-pid").read_text())
            self.assertNotEqual(child_pid, leader_pid)
            # Independent OS observations, never the helper's returned flag.
            # EPERM propagates as failure rather than being treated as absence.
            with self.assertRaises(ProcessLookupError):
                os.killpg(leader_pid, 0)
            for pid in (leader_pid, child_pid):
                with self.subTest(pid=pid), self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
            self.assertTrue(result["timed_out"])
            self.assertTrue(result["leader_reaped"])
            self.assertTrue(result["group_absent"])
            self.assertEqual((Path(directory) / "child-ready").read_text(), "ready")
            self.assertEqual((Path(directory) / "child-term").read_text(), "TERM")
            self.assertEqual((Path(directory) / "leader-term").read_text(), "TERM")
            self.assertGreaterEqual(result["cleanup_seconds"], 0.25)
            self.assertLess(time.monotonic() - started, 7)

    def test_second_command_uses_remaining_absolute_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            started = time.monotonic()
            deadline = started + 0.3
            first = runner.run_bounded_command([sys.executable, "-c", "import time;time.sleep(.05)"],
                                               directory, deadline, grace=0.02)
            self.assertEqual(first["returncode"], 0)
            second = runner.run_bounded_command([sys.executable, "-c", "import time;time.sleep(60)"],
                                                directory, deadline, grace=0.02)
            self.assertTrue(second["timed_out"])
            self.assertLess(time.monotonic() - started, 1)
            with self.assertRaisesRegex(ValueError, "BUDGET_EXHAUSTED"):
                runner.run_bounded_command([sys.executable, "-c", "raise SystemExit(99)"],
                                           directory, deadline, grace=0.02)


if __name__ == "__main__":
    unittest.main()
