"""Apply actual bound patch, verify hashes, then execute both production paths."""
import ast
from collections import namedtuple
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parents[1]
REPO = Path(os.environ.get("VIRIDIS_LIVENESS_REPO_ROOT", str(HERE.parents[2])))
sys.path.insert(0, str(HERE))
from scheduler_liveness import paper_review_pending, writer_hold_code


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ActualWiringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        pipeline = self.root / "RESEARCH_PIPELINE_v2"
        pipeline.mkdir()
        controller = REPO / "00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/autonomous_pipeline_controller.py"
        executor = HERE / "tests/fixtures/autonomous_transition_executor.py.txt"
        self.binding = json.loads((HERE / "INTEGRATION_BINDING.json").read_text())
        sources = {"autonomous_pipeline_controller.py": controller, "autonomous_transition_executor.py": executor}
        for row in self.binding["files"]:
            path = Path(row["path"])
            if path.name not in sources:
                continue
            self.assertEqual(sha(sources[path.name]), row["before_sha256"])
            (self.root / path).write_bytes(sources[path.name].read_bytes())
        command = subprocess.run(["git", "apply", "--unidiff-zero", str(HERE / "G1_CONTROLLER_EXECUTOR.patch")],
                                 cwd=self.root, capture_output=True, text=True)
        self.assertEqual(command.returncode, 0, "the actual installation patch must apply")
        for row in self.binding["files"]:
            if Path(row["path"]).name in sources:
                self.assertEqual(sha(self.root / row["path"]), row["after_sha256"])

    def function(self, filename, name, namespace):
        tree = ast.parse((self.root / "RESEARCH_PIPELINE_v2" / filename).read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        exec(compile(ast.Module(body=[function], type_ignores=[]), filename, "exec"), namespace)
        return namespace[name]

    def test_actual_executor_wiring_exposes_stdout_hold_with_no_prose(self):
        fields = "argv returncode stdout_sha256 stderr_sha256 stdout_tail stderr_tail"
        namespace = {"CommandResult": namedtuple("CommandResult", fields), "hashlib": hashlib,
            "validate_command": lambda argv: None, "CONTROL_ROOT": self.root,
            "output_tail": lambda value: value[-2000:], "writer_hold_code": writer_hold_code,
            "ExecutorError": RuntimeError,
            "subprocess": SimpleNamespace(run=lambda *args, **kwargs: SimpleNamespace(returncode=2,
                stdout=json.dumps({"status": "HOLD", "error": "HOLD_REVIEW_STATUS_CONTRADICTION: excluded prose"}), stderr=""))}
        run = self.function("autonomous_transition_executor.py", "run_command", namespace)
        with self.assertRaises(RuntimeError) as failure:
            run([sys.executable, "writer.py"])
        self.assertIn("HOLD_REVIEW_STATUS_CONTRADICTION", str(failure.exception))
        self.assertNotIn("excluded prose", str(failure.exception))
        self.assertIn("stdout_sha256=", str(failure.exception))

    def test_actual_controller_wiring_routes_pending_paper_without_rewriting(self):
        root = self.root / "Run-170"
        root.mkdir()
        for name in ("CURATOR_DRAFT_READY.json", "FINALIZED_PACKAGE.json", "CANON_PRODUCT_ROUTE.json", "KERNEL_ADMISSION_REVIEW.json"):
            (root / name).write_text("{}")
        (root / "PAPER_PACKAGE_MANIFEST.json").write_text(json.dumps({"artifacts": {"paper_source": "paper.tex"}}))
        paper = root / "paper.tex"
        paper.write_text("Independent manuscript review remains pending.")
        before = paper.read_bytes()
        fields = "run_id state next_action human_gate detail"
        namespace = {"Path": Path, "WorkItem": namedtuple("WorkItem", fields),
            "finalized_lean_hashes": lambda path: set(), "review_passes": lambda path: True,
            "certificate_clean": lambda *args: True, "read_json": lambda path: json.loads(path.read_text()),
            "certified_metadata_contradictions": lambda value: [], "review_hold": lambda path: None,
            "paper_review_pending": paper_review_pending, "complete_kernel_package": lambda *args: False}
        inspect = self.function("autonomous_pipeline_controller.py", "inspect_run", namespace)
        result = inspect(root, self.root, set(), set(), self.root, True, self.root)
        self.assertEqual(result.next_action, "REVIEW_FINALIZED_PACKAGE_BINDINGS")
        self.assertFalse(result.human_gate)
        self.assertEqual(before, paper.read_bytes())


if __name__ == "__main__":
    unittest.main()
