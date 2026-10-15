import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
REPO = Path(__import__("os").environ.get("VIRIDIS_LIVENESS_REPO_ROOT", str(HERE.parents[2])))
sys.path.insert(0, str(HERE))
import checkpoint_advisory as advisory


class AdvisoryCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.pipeline = self.root / "RESEARCH_PIPELINE_v2"
        self.checkpoint = self.pipeline / "nightly_checkpoints/invocation/START.json"
        self.checkpoint.parent.mkdir(parents=True)
        self.checkpoint.write_text(json.dumps({"standard": "VRS-NIGHTLY-CHECKPOINT-1", "invocation_id": "invocation",
            "science": {"certification": {"backlog_runs": ["Run-194"]}}}))
        self.playbook = self.pipeline / "LEAN_REPAIR_PLAYBOOK.json"
        self.playbook.write_text(json.dumps({"schema": "VRS-LEAN-REPAIR-PLAYBOOK-1", "rules": [
            {"id": "UNFOLD_LOCAL_ALGEBRA_DEFINITIONS"}, {"id": "RFL_ALGEBRA_REASSOCIATION"}]}))
        candidate = self.pipeline / "lean_certificates/Run-194/VERIFICATION_CANDIDATE.lean"
        candidate.parent.mkdir(parents=True)
        candidate.write_text("theorem fixture : 1 = 1 := rfl\n")
        target = self.pipeline / "pipeline_advisory"
        target.mkdir()
        for name in advisory.PINS:
            shutil.copyfile(REPO / "00_lab_infrastructure/gates/pipeline_advisory" / name, target / name)

    def test_linter_runs_and_missing_slo_inputs_write_explicit_unavailable(self):
        before = self.checkpoint.read_bytes()
        with patch.object(advisory, "PLAYBOOK_SHA256", hashlib.sha256(self.playbook.read_bytes()).hexdigest()):
            result = advisory.observe(self.root, self.checkpoint)
        lint = json.loads((self.checkpoint.parent / "LEAN_REPAIR_LINT_ADVISORY.json").read_text())
        self.assertFalse(lint["certifies"])
        self.assertEqual(lint["results"][0]["result"]["source_sha256"],
            hashlib.sha256((self.pipeline / "lean_certificates/Run-194/VERIFICATION_CANDIDATE.lean").read_bytes()).hexdigest())
        slo = json.loads((self.pipeline / "PIPELINE_SLO_STATUS.json").read_text())
        self.assertEqual(slo["status"], "ADVISORY_UNAVAILABLE")
        self.assertIsNone(slo["fifo_liveness"]["failing_goal"])
        self.assertEqual(self.checkpoint.read_bytes(), before)

    def test_advisory_source_drift_never_becomes_a_science_gate(self):
        (self.pipeline / "pipeline_advisory/lean_repair_lint.py").write_text("raise RuntimeError('untrusted changed source')")
        self.assertEqual(advisory.observe(self.root, self.checkpoint)["lint"], "ADVISORY_UNAVAILABLE")
        self.assertEqual(json.loads((self.pipeline / "PIPELINE_SLO_STATUS.json").read_text())["status"], "ADVISORY_UNAVAILABLE")

    def patched_namespace(self):
        target = self.pipeline / "nightly_checkpoint.py"
        target.write_bytes((HERE / "tests/fixtures/nightly_checkpoint.py.txt").read_bytes())
        result = subprocess.run(["git", "apply", "--unidiff-zero", str(HERE / "G2_EXISTING_CHECKPOINT.patch")],
                                cwd=self.root, capture_output=True)
        self.assertEqual(result.returncode, 0)
        tree = ast.parse(target.read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"main", "checkpoint_advisory_after_checkpoint"}]
        namespace = {"argparse": argparse, "Path": Path, "json": json, "sys": sys,
                     "HERE": self.pipeline, "re": __import__("re"), "CHECKPOINTS": self.pipeline / "nightly_checkpoints"}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "nightly_checkpoint.py", "exec"), namespace)
        return namespace

    def test_advisory_timeout_cannot_block_due_generation_checkpoint(self):
        namespace = self.patched_namespace()
        written = []
        namespace.update(evaluate=lambda: {"evaluated_at_utc": "2026-10-15T23:00:00Z",
            "generation": {"due": True, "window": "fixture"}, "certification": {"backlog_runs": []}},
            write_new=lambda *args: written.append(args))
        with patch.object(sys, "argv", ["nightly_checkpoint.py", "--begin", "new-invocation"]), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("advisory", 15)):
            self.assertEqual(namespace["main"](), 0)
        self.assertTrue(written[0][1]["science"]["generation"]["due"])

    def test_advisory_error_cannot_block_certification_or_following_authorized_action(self):
        namespace = self.patched_namespace()
        calls = []
        modules = {"checkpoint_certification_lane": SimpleNamespace(drain_checkpoint=lambda *args: calls.append("certification") or {"status": "COMPLETED"})}
        with patch.object(sys, "argv", ["nightly_checkpoint.py", "--drain-certification", str(self.checkpoint), "--certification-queue", "queue.json"]), \
             patch.dict(sys.modules, modules), patch("subprocess.run", side_effect=OSError("advisory unavailable")):
            self.assertEqual(namespace["main"](), 0)
            calls.append("following-existing-authorized-action")
        self.assertEqual(calls, ["certification", "following-existing-authorized-action"])


if __name__ == "__main__":
    unittest.main()
