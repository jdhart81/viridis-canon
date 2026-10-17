"""A traceback word cannot erase counted behavioral assertion failures."""
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("feature_mutations", Path(__file__).parents[1] / "mutate_gate_features.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class MutationClassificationTests(unittest.TestCase):
    def test_behavioral_failures_with_optional_codec_error_are_killed(self):
        counts = {"tests_run":42,"failures":7,"errors":1,"infrastructure_errors":1}
        self.assertEqual(M.classify_test_run(1, counts), {"result":"KILLED",**counts})

    def test_import_only_or_unstarted_suite_is_not_a_kill(self):
        for counts in ({"tests_run":1,"failures":0,"errors":1,"infrastructure_errors":1}, None):
            self.assertEqual(M.classify_test_run(1, counts)["result"], "INVALID_TEST_ERROR")

    def test_baseline_failure_and_survival_remain_distinct(self):
        counts={"tests_run":2,"failures":1,"errors":0,"infrastructure_errors":0}
        self.assertEqual(M.classify_test_run(1, counts, baseline=True)["result"], "BASELINE_FAILURE")
        self.assertEqual(M.classify_test_run(0, {**counts,"failures":0})["result"], "SURVIVED")

    def test_actual_runner_keeps_seven_failures_when_optional_codec_is_missing(self):
        import json,os,subprocess,sys,tempfile
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'tests').mkdir()
            source="import unittest\nclass Behavior(unittest.TestCase):\n"
            for number in range(7):
                source+=f" def test_behavior_{number}(self):self.fail('missing gate')\n"
            source+=" def test_optional_codec(self):raise ModuleNotFoundError('optional codec')\n"
            (root/'tests/test_gate_hardening.py').write_text(source)
            result=subprocess.run([sys.executable,'-c',M.TEST_RUNNER],cwd=root,capture_output=True,text=True,
                                  env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=10)
        metrics=[line.split(':',1)[1] for line in result.stdout.splitlines() if line.startswith('VRS_MUTATION_TEST_COUNTS:')]
        self.assertEqual(len(metrics),1);counts=json.loads(metrics[0])
        self.assertEqual(counts,{'tests_run':8,'failures':7,'errors':1,'infrastructure_errors':1})
        self.assertEqual(M.classify_test_run(result.returncode,counts)['result'],'KILLED')

    def test_behavioral_type_error_is_a_kill(self):
        counts={"tests_run":2,"failures":0,"errors":1,"infrastructure_errors":0}
        self.assertEqual(M.classify_test_run(1, counts)["result"], "KILLED")
