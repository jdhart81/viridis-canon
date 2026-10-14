from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import checkpoint_slo_hook as hook


class CheckpointHookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.base = self.root / "RESEARCH_PIPELINE_v2"
        self.checkpoint = self.base / "nightly_checkpoints/run/FINISH.json"
        self.checkpoint.parent.mkdir(parents=True)
        self.checkpoint.write_text(json.dumps({"standard": "VRS-NIGHTLY-CHECKPOINT-1",
            "invocation_id": "run", "status": "HOLD_NIGHTLY_PROGRESS"}))
        self.observer = self.base / "FOUNDRY_OBSERVER_STATUS.json"
        self.observer.write_text(json.dumps({"observed_at_utc": "2026-10-14T18:00:00Z",
            "science": {"generation": {"generated_at_utc": "2026-10-14T05:00:00Z"},
                        "certification": {"age_hours": 139, "backlog_runs": ["Run-191"]}}}))
        self.snapshot = self.base / "PIPELINE_SLO_INPUTS.json"
        self.snapshot.write_text(json.dumps({"fifo_head": {"run_id": "Run-191",
            "held_since_utc": "2026-10-09T17:00:00Z", "failing_goal": "purityLoss p = disturbanceSq p * 2"}}))

    def test_actual_checkpoint_emits_overdue_alert_without_changing_input(self):
        before = self.checkpoint.read_bytes()
        result = hook.emit(self.root, self.checkpoint, as_of="2026-10-14T23:00:00Z")
        report = json.loads((self.base / "PIPELINE_SLO_STATUS.json").read_text())
        self.assertEqual(result["status"], "REPORTED")
        self.assertEqual(report["certification_age"]["age_hours"], 144)
        self.assertEqual(report["fifo_liveness"]["status"], "ALERT")
        self.assertIn("purityLoss", report["fifo_liveness"]["failing_goal"])
        self.assertEqual(report["checkpoint"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(before, self.checkpoint.read_bytes())
        self.assertFalse(report["certifies"])

    def test_absent_coverage_snapshot_is_unavailable(self):
        self.snapshot.unlink()
        hook.emit(self.root, self.checkpoint, as_of="2026-10-14T23:00:00Z")
        report = json.loads((self.base / "PIPELINE_SLO_STATUS.json").read_text())
        for key in ("pdf_coverage", "banner_coverage", "leak_scan", "weekly_digest"):
            self.assertEqual(report[key]["status"], "UNAVAILABLE")

    def test_symlink_input_and_output_are_refused(self):
        self.snapshot.unlink()
        self.snapshot.symlink_to(self.observer)
        self.assertEqual(hook.observe(self.root, self.checkpoint)["status"], "ADVISORY_UNAVAILABLE")
        self.snapshot.unlink()
        (self.base / "PIPELINE_SLO_STATUS.json").symlink_to(self.observer)
        before = self.observer.read_bytes()
        self.assertEqual(hook.observe(self.root, self.checkpoint)["status"], "ADVISORY_UNAVAILABLE")
        self.assertEqual(self.observer.read_bytes(), before)

    def test_oversized_and_excessive_scope_cannot_run(self):
        self.snapshot.write_bytes(b"x" * (hook.MAX_INPUT_BYTES + 1))
        self.assertEqual(hook.observe(self.root, self.checkpoint)["status"], "ADVISORY_UNAVAILABLE")
        self.snapshot.write_text(json.dumps({"new_evidence": {"files": ["a"] * 196}}))
        self.assertEqual(hook.observe(self.root, self.checkpoint)["status"], "ADVISORY_UNAVAILABLE")

    def test_catch_all_never_echoes_exception_or_changes_checkpoint(self):
        before = self.checkpoint.read_bytes()
        with patch.object(hook, "emit", side_effect=RuntimeError("synthetic-sensitive-value")):
            result = hook.observe(self.root, self.checkpoint)
        self.assertNotIn("synthetic-sensitive-value", json.dumps(result))
        self.assertEqual(before, self.checkpoint.read_bytes())

    def test_ctime_only_read_change_passes_but_content_change_holds(self):
        original_read = os.read
        calls = 0
        def chmod_read(fd, count):
            nonlocal calls
            raw = original_read(fd, count)
            calls += 1
            if calls == 1:
                os.chmod(self.observer, self.observer.stat().st_mode)
            return raw
        with patch.object(os, "read", side_effect=chmod_read):
            hook.read_json(self.observer, self.root)
        original = self.observer.stat()
        calls = 0
        def tamper_read(fd, count):
            nonlocal calls
            raw = original_read(fd, count)
            calls += 1
            if calls == 1:
                self.observer.write_bytes(raw.replace(b"139", b"140"))
                os.utime(self.observer, ns=(original.st_atime_ns, original.st_mtime_ns))
            return raw
        with patch.object(os, "read", side_effect=tamper_read):
            with self.assertRaisesRegex(ValueError, "changed"):
                hook.read_json(self.observer, self.root)

    def test_monday_summary_appends_exact_ten_line_science_section(self):
        hook.emit(self.root, self.checkpoint, as_of="2026-10-14T23:00:00Z")
        report = json.loads((self.base / "PIPELINE_SLO_STATUS.json").read_text())
        original = "Adoption evidence remains unavailable.\n"
        combined = hook.monday_summary(report, original)
        self.assertTrue(combined.startswith(original.rstrip() + "\n\n"))
        self.assertEqual(len(combined.split("\n\n", 1)[1].splitlines()), 10)

    def test_input_parent_symlink_race_is_refused(self):
        original_read = os.read
        moved = self.root / "preserved"
        switched = False
        def race(fd, count):
            nonlocal switched
            raw = original_read(fd, count)
            if not switched:
                switched = True
                self.base.rename(moved)
                self.base.symlink_to(moved, target_is_directory=True)
            return raw
        with patch.object(os, "read", side_effect=race):
            with self.assertRaises(ValueError):
                hook.read_json(self.observer, self.root)

    def test_output_parent_race_cannot_redirect_write_outside_root(self):
        target = self.base / "PIPELINE_SLO_STATUS.json"
        outside = self.root / "outside"
        outside.mkdir()
        moved = self.root / "preserved"
        replace = os.replace
        def race(*args, **kwargs):
            self.base.rename(moved)
            self.base.symlink_to(outside, target_is_directory=True)
            return replace(*args, **kwargs)
        with patch.object(os, "replace", side_effect=race):
            with self.assertRaises(ValueError):
                hook.atomic_report(target, {"certifies": False}, self.root)
        self.assertFalse((outside / target.name).exists())

    def patched_checkpoint(self):
        binding = json.loads((HERE / "DESIGN/CHECKPOINT_SLO_HOOK_BINDING.json").read_text())
        source = (HERE.parents[2] / binding["source_fixture"]).read_bytes()
        installed = self.base / "nightly_checkpoint.py"
        installed.write_bytes(source)
        subprocess.run(["git", "apply", str(HERE / "DESIGN/CHECKPOINT_SLO_HOOK.patch")],
                       cwd=self.root, check=True, capture_output=True)
        namespace = {"__name__": "checkpoint_fixture", "__file__": str(installed)}
        modules = {"autonomous_pipeline_controller": types.SimpleNamespace(build_state=lambda: {}),
                   "science_foundry_continuity": types.SimpleNamespace(evaluate=lambda: {})}
        with patch.dict(sys.modules, modules):
            exec(compile(installed.read_bytes(), str(installed), "exec"), namespace)
        return namespace

    def test_isolated_child_verifies_both_sources_before_execution(self):
        namespace = self.patched_checkpoint()
        destination = self.base / "pipeline_advisory"
        destination.mkdir()
        for name in ("pipeline_slo.py", "checkpoint_slo_hook.py"):
            (destination / name).write_bytes((HERE / name).read_bytes())
        namespace["pipeline_slo_after_checkpoint"](self.checkpoint)
        report = self.base / "PIPELINE_SLO_STATUS.json"
        self.assertTrue(report.is_file())
        for name in ("pipeline_slo.py", "checkpoint_slo_hook.py"):
            with self.subTest(name=name):
                report.unlink(missing_ok=True)
                target = destination / name
                original = target.read_bytes()
                sentinel = self.root / "unreviewed-source-executed"
                target.write_text("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").touch()\n")
                namespace["pipeline_slo_after_checkpoint"](self.checkpoint)
                self.assertFalse(report.exists())
                self.assertFalse(sentinel.exists())
                target.write_bytes(original)

    def test_patch_binds_real_source_and_preserves_checkpoint_return_codes(self):
        binding = json.loads((HERE / "DESIGN/CHECKPOINT_SLO_HOOK_BINDING.json").read_text())
        repo = HERE.parents[2]
        source = (repo / binding["source_fixture"]).read_bytes()
        proposed_patch = HERE / "DESIGN/CHECKPOINT_SLO_HOOK.patch"
        self.assertEqual(hashlib.sha256(source).hexdigest(), binding["before_sha256"])
        self.assertEqual(hashlib.sha256(proposed_patch.read_bytes()).hexdigest(), binding["patch_sha256"])
        self.assertEqual(hashlib.sha256((HERE / "checkpoint_slo_hook.py").read_bytes()).hexdigest(), binding["hook_source_sha256"])
        self.assertEqual(hashlib.sha256((HERE / "pipeline_slo.py").read_bytes()).hexdigest(), binding["collector_source_sha256"])
        installed = self.base / "nightly_checkpoint.py"
        installed.write_bytes(source)
        subprocess.run(["git", "apply", str(proposed_patch)], cwd=self.root, check=True, capture_output=True)
        candidate = installed.read_bytes()
        self.assertEqual(hashlib.sha256(candidate).hexdigest(), binding["after_sha256"])
        modules = {"autonomous_pipeline_controller": types.SimpleNamespace(build_state=lambda: {}),
                   "science_foundry_continuity": types.SimpleNamespace(evaluate=lambda: {})}
        namespace = {"__name__": "checkpoint_fixture", "__file__": str(installed)}
        with patch.dict(sys.modules, modules):
            exec(compile(candidate, str(installed), "exec"), namespace)
        namespace["verification_coverage_after_checkpoint"] = lambda *a, **kw: 0
        science = {"evaluated_at_utc": "2026-10-14T23:00:00+00:00",
            "generation": {"due": False, "window": {}}, "certification": {"backlog_runs": ["Run-191"]}}
        namespace["evaluate"] = lambda: science
        with patch.object(sys, "argv", ["nightly_checkpoint.py", "--begin", "actual"]), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired("advisory", 15)), redirect_stdout(io.StringIO()):
            self.assertEqual(namespace["main"](), 0)
        start = self.base / "nightly_checkpoints/actual/START.json"
        for incidents, expected in (([], 0), (["HOLD_FIFO"], 2)):
            finish = start.parent / "FINISH.json"
            finish.unlink(missing_ok=True)
            namespace["assess"] = lambda *a, _inc=incidents: {"incidents": _inc, "invocation_id": "actual"}
            with patch.object(sys, "argv", ["nightly_checkpoint.py", "--finish", str(start)]), \
                 patch("subprocess.run", side_effect=subprocess.TimeoutExpired("advisory", 15)), redirect_stdout(io.StringIO()):
                self.assertEqual(namespace["main"](), expected)
                self.assertEqual(namespace["main"](), expected)  # real FINISH replay path


if __name__ == "__main__":
    unittest.main()
