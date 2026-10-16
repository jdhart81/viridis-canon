"""Behavioral B4 regressions on the actual patched controller and executor.

Every fixture is a disposable mini repository. Private imports are inert local
stubs; no live pipeline, provider, credential, or Lean process is accessed.
"""
from collections import namedtuple
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import test_g1_integration as wiring


class AuditG1Tests(unittest.TestCase):
    # Borrow only the actual patch/hash setup, never the parent's test methods.
    setUp = wiring.ActualWiringTests.setUp
    function = wiring.ActualWiringTests.function

    def prepare_cli_fixture(self):
        self.pipeline = self.root / "RESEARCH_PIPELINE_v2"
        (self.pipeline / "nightly_checkpoint.py").write_bytes(
            (wiring.HERE / "tests/fixtures/nightly_checkpoint.py.txt").read_bytes())
        (self.pipeline / "scheduler_liveness.py").write_bytes(
            (wiring.HERE / "scheduler_liveness.py").read_bytes())
        stubs = {
            "verification_state_metadata.py":
                "def certified_metadata_contradictions(value):\n    return []\n",
            "comparator_data_egress_authorization.py":
                "def validate_authorization(*args):\n    return {'status': 'AUTHORIZED'}\n",
            "viridisos_kernel_packager.py":
                "class KernelPackageError(Exception):\n    pass\n"
                "def validate_existing_kernel_package(*args, **kwargs):\n"
                "    raise KernelPackageError('no fixture package')\n",
            "science_foundry_continuity.py":
                "import datetime as dt\n"
                "def evaluate():\n"
                "    return {'evaluated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),\n"
                "        'generation': {'ready': True, 'due': False, 'fresh': True, 'window': 'fixture'},\n"
                "        'certification': {'backlog_runs': [], 'certified_runs': [],\n"
                "            'ready': True, 'recent': True, 'backlog_critical': 9}}\n",
        }
        for name, text in stubs.items():
            (self.pipeline / name).write_text(text)
        self.bad_run = self.make_finalized_run("Run-170")
        self.make_finalized_run("Run-171")

    def make_finalized_run(self, run_id):
        root = self.pipeline / "finalized_runs" / run_id
        root.mkdir(parents=True)
        for name in ("FINALIZED_PACKAGE", "CURATOR_DRAFT_READY", "CANON_PRODUCT_ROUTE",
                     "KERNEL_ADMISSION_REVIEW"):
            (root / (name + ".json")).write_text("{}")
        (root / "POST_ARISTOTLE_REVIEW.json").write_text(json.dumps({
            "schema_version": 2, "verdict": "pass", "reviewer_system": "fixture",
            "reviewer_model": "fixture", "checks": {"exact_scope": True}}))
        (root / "PAPER_PACKAGE_MANIFEST.json").write_text(json.dumps({
            "artifacts": {"paper_source": "paper.tex"}}))
        (root / "paper.tex").write_text("The final paper has completed its review.")
        return root

    def cli(self, *arguments):
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        environment.pop("PYTHONPYCACHEPREFIX", None)
        result = subprocess.run([sys.executable, "-B", *map(str, arguments)],
            cwd=self.pipeline, env=environment, capture_output=True, text=True, timeout=15)
        self.assertIn(result.returncode, (0, 2), result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def assert_contained_run_and_real_receipts(self):
        before = {p.name: p.read_bytes() for p in self.bad_run.iterdir() if p.is_file()}
        controller_receipt = self.pipeline / "CONTROLLER.json"
        self.cli("autonomous_pipeline_controller.py", "--write-receipt", "--output",
                 controller_receipt)
        state = json.loads(controller_receipt.read_text())
        rows = {row["run_id"]: row for row in state["items"]}
        self.assertEqual(rows["Run-170"]["next_action"], "REVIEW_FINALIZED_PACKAGE_BINDINGS")
        self.assertEqual(rows["Run-170"]["state"], "FINALIZED_PACKAGE_RECONCILIATION_REQUIRED")
        self.assertFalse(rows["Run-170"]["human_gate"])
        self.assertEqual(rows["Run-171"]["next_action"], "BUILD_VIRIDISOS_KERNEL_PACKAGE")

        evaluated = dt.datetime.now(dt.timezone.utc).isoformat()
        start = self.pipeline / "nightly_checkpoints/fixture/START.json"
        start.parent.mkdir(parents=True)
        start.write_text(json.dumps({"standard": "VRS-NIGHTLY-CHECKPOINT-1",
            "invocation_id": "fixture", "started_at_utc": evaluated,
            "science": {"evaluated_at_utc": evaluated,
                "generation": {"ready": True, "due": False, "fresh": True, "window": "fixture"},
                "certification": {"backlog_runs": [], "certified_runs": [],
                    "ready": True, "recent": True, "backlog_critical": 9}}}))
        self.cli("nightly_checkpoint.py", "--finish", start)
        finish = json.loads(start.with_name("FINISH.json").read_text())
        self.assertEqual(finish["status"], "HOLD_NIGHTLY_PROGRESS")
        self.assertIn("HOLD_REVERSIBLE_PACKAGE_WORK_REMAINS", finish["incidents"])
        self.assertEqual(finish["start_receipt_sha256"], hashlib.sha256(start.read_bytes()).hexdigest())

        executor_receipt = self.pipeline / "EXECUTOR.json"
        self.cli("autonomous_transition_executor.py", "--output", executor_receipt,
                 "--date", "2026-10-16")
        executed = json.loads(executor_receipt.read_text())
        self.assertEqual(executed["mode"], "DRY_RUN")
        self.assertFalse(executed["external_mutation"])
        self.assertEqual(executed["executed"], [])
        self.assertTrue(any(row["run_id"] == "Run-170"
                            and row["next_action"] == "REVIEW_FINALIZED_PACKAGE_BINDINGS"
                            for row in executed["judgment_required"]))
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.bad_run.iterdir()
                                  if p.is_file()})

    def malformed_case(self, case):
        self.prepare_cli_fixture()
        manifest = self.bad_run / "PAPER_PACKAGE_MANIFEST.json"
        if case == "absent":
            manifest.unlink()
        elif case == "artifacts_null":
            manifest.write_text('{"artifacts": null}')
        elif case == "missing_source":
            (self.bad_run / "paper.tex").unlink()
        elif case == "malformed_json":
            manifest.write_text('{"artifacts":')
        elif case == "invalid_manifest_utf8":
            manifest.write_bytes(b"\xff\xfe")
        elif case == "invalid_paper_utf8":
            (self.bad_run / "paper.tex").write_bytes(b"\xff\xfe")
        elif case == "escaping_source":
            manifest.write_text(json.dumps({"artifacts": {"paper_source": "../../outside.tex"}}))
            outside = self.pipeline / "outside.tex"
            outside.write_text("A complete reviewed fixture paper.")
        else:
            self.fail("unknown malformed fixture case")
        self.assert_contained_run_and_real_receipts()

    def test_absent_manifest_keeps_finish_and_executor_receipts(self):
        self.malformed_case("absent")

    def test_artifacts_null_keeps_finish_and_executor_receipts(self):
        self.malformed_case("artifacts_null")

    def test_missing_paper_source_keeps_finish_and_executor_receipts(self):
        self.malformed_case("missing_source")

    def test_malformed_json_is_a_per_run_hold(self):
        self.malformed_case("malformed_json")

    def test_invalid_manifest_encoding_is_a_per_run_hold(self):
        self.malformed_case("invalid_manifest_utf8")

    def test_invalid_paper_encoding_is_a_per_run_hold(self):
        self.malformed_case("invalid_paper_utf8")

    def test_escaping_paper_source_is_a_per_run_hold(self):
        self.malformed_case("escaping_source")

    def test_existing_reviewed_text_checker_is_used(self):
        self.prepare_cli_fixture()
        (self.bad_run / "paper.tex").write_text("fixture shared reviewer contradiction")
        path = self.pipeline / "verification_state_metadata.py"
        path.write_text(path.read_text() +
            "def reviewed_text_contradictions(text):\n"
            "    return ['fixture contradiction'] if 'shared reviewer contradiction' in text else []\n")
        self.assert_contained_run_and_real_receipts()

    def test_actual_executor_retains_safe_stderr_and_redacts_credential_shapes(self):
        bearer = "fixture" + "Q7w4R9t2P6v8N3m5L1z0"
        opaque = "".join(("A9z_", "Q4w+", "E7r/", "T2y=", "U5i-", "O8p.", "S3d_", "F6g+"))
        url = "https://example.invalid/fixture?access_token=" + bearer
        safe = "The draft metadata is missing a required field."
        stderr = safe + "\nAuthorization: Bearer " + bearer + "\n" + url + "\n" + opaque
        stdout = json.dumps({"status": "HOLD", "error": "HOLD_REVIEW_STATUS_CONTRADICTION: excluded stdout prose"})
        writer = self.root / "RESEARCH_PIPELINE_v2" / "fixture_writer.py"
        writer.write_text("import sys\nsys.stdout.write(" + repr(stdout) + ")\n"
                          "sys.stderr.write(" + repr(stderr) + ")\nsys.exit(2)\n")
        fields = "argv returncode stdout_sha256 stderr_sha256 stdout_tail stderr_tail"
        namespace = {"CommandResult": namedtuple("CommandResult", fields), "hashlib": hashlib,
            "validate_command": lambda argv: None, "CONTROL_ROOT": writer.parent,
            "output_tail": lambda value: value[-2000:], "writer_hold_code": wiring.writer_hold_code,
            "redacted_stderr_tail": wiring.redacted_stderr_tail, "ExecutorError": RuntimeError,
            "subprocess": subprocess}
        run = self.function("autonomous_transition_executor.py", "run_command", namespace)
        with self.assertRaises(RuntimeError) as failure:
            run([sys.executable, "-B", str(writer)])
        message = str(failure.exception)
        self.assertIn(safe, message)
        self.assertIn("HOLD_REVIEW_STATUS_CONTRADICTION", message)
        self.assertIn("[REDACTED]", message)
        self.assertIn(hashlib.sha256(stderr.encode()).hexdigest(), message)
        self.assertNotIn(bearer, message)
        self.assertNotIn(url, message)
        self.assertNotIn(opaque, message)
        self.assertNotIn("excluded stdout prose", message)


if __name__ == "__main__":
    unittest.main()
