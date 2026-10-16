from __future__ import annotations

import datetime as dt
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

GATES = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GATES))
from terminal_certification import terminal_hold as gate


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


class TerminalFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="terminal-hold-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.pipeline = self.root / "RESEARCH_PIPELINE_v2"
        self.package = self.pipeline / "nightly_packages/Run-194"
        self.folder = self.pipeline / "lean_certificates/Run-194"
        self.package.mkdir(parents=True)
        self.folder.mkdir(parents=True)
        self.manifest = {"run_id": "Run-194", "foundation_basis": "DERIVED"}
        self.documents = {
            "SEALED_RUN_MANIFEST.json": encoded(self.manifest),
            "SEALED_CLAIM_INVENTORY.json": encoded({"foundation_basis": "DERIVED"}),
            "SEALED_paper.tex": b"\\begin{abstract}Conditional note.\\end{abstract}\n",
            "VERIFICATION_STATEMENT.lean": b"theorem target : True\n",
            "VERIFICATION_CANDIDATE.lean": b"theorem target : True := by trivial\n",
        }
        self.request = {"source_run": "Run-194", "local_lean_execution": False,
                        "expected_theorem_names": ["target", "witness"],
                        "nonvacuity_obligations": ["witness"],
                        "input_sha256": {name: gate._sha(data) for name, data in self.documents.items()}}
        self.documents["ENGINE3_VERIFICATION_REQUEST.json"] = encoded(self.request)
        for name, data in self.documents.items():
            (self.folder / name).write_bytes(data)
        (self.package / "PAPER_PACKAGE_MANIFEST.json").write_bytes(self.documents["SEALED_RUN_MANIFEST.json"])
        self.receipt = {
            "schema_version": "VRS-CERTIFICATION-PREMISE-HOLD-1", "run_id": "Run-194",
            "status": "HOLD_PREMISE_DECLARATION", "terminal_for_sealed_object": True,
            "transport_performed_this_checkpoint": False, "certificate_issued": False,
            "reason": "PREMISE_DECLARATION_MISSING_OR_UNKNOWN",
            "bindings": {key: gate._sha(self.documents[name]) for key, name in gate.BOUND_FILES.items()},
            "checker_result": {"standard": "VRS-PREMISE-DECLARATION-1", "status": "HOLD",
                               "foundation_basis": None, "reasons": ["PREMISE_DECLARATION_MISSING_OR_UNKNOWN"],
                               "findings": [], "local_lean_execution": False, "certifies": False},
        }
        self.receipt["bindings"]["premise_checker_sha256"] = gate.CHECKER_SHA256
        self.receipt_path = self.folder / "PREMISE_DECLARATION_HOLD_ENGINE_20261015.json"
        self.trusted = {}
        self.trust_current_receipt()
        self.allowlist = patch.object(gate, "TRUSTED_RECEIPTS", self.trusted)
        self.allowlist.start()
        self.addCleanup(self.allowlist.stop)

    def trust_current_receipt(self):
        self.receipt_path.write_bytes(encoded(self.receipt))
        self.trusted["Run-194"] = (self.receipt_path.name, gate._sha(self.receipt_path.read_bytes()))

    def check(self):
        return gate.terminal_hold(self.package, self.folder.parent)

    def rebind_document(self, filename, data):
        (self.folder / filename).write_bytes(data)
        self.documents[filename] = data
        for key, name in gate.BOUND_FILES.items():
            if name == filename:
                self.receipt["bindings"][key] = gate._sha(data)
        if filename != "ENGINE3_VERIFICATION_REQUEST.json":
            self.request["input_sha256"][filename] = gate._sha(data)
            self.rebind_document("ENGINE3_VERIFICATION_REQUEST.json", encoded(self.request))
        self.trust_current_receipt()


class EvidenceTests(TerminalFixture):
    def test_authentic_receipt_and_fresh_checker_hold_exclude_only_dispatch(self):
        result = self.check()
        self.assertEqual(result["status"], "TERMINAL_PREMISE_HOLD")
        self.assertFalse(result["certifies"])
        self.assertFalse(result["clears_certification_debt"])
        self.assertFalse(result["publication_admitted"])

    def test_missing_or_unreviewed_receipt_retains_fifo(self):
        self.receipt_path.unlink()
        self.assertIsNone(self.check())
        self.trust_current_receipt()
        self.trusted.clear()
        self.assertIsNone(self.check())

    def test_assertion_only_or_changed_receipt_retains_fifo(self):
        self.receipt["detail"] = "self asserted skip"
        self.receipt_path.write_bytes(encoded(self.receipt))
        self.assertIsNone(self.check())

    def test_every_frozen_byte_binding_is_required(self):
        for filename, original in self.documents.items():
            with self.subTest(filename=filename):
                (self.folder / filename).write_bytes(original + b" ")
                self.assertIsNone(self.check())
                (self.folder / filename).write_bytes(original)

    def test_changed_selected_package_is_not_held_object(self):
        (self.package / "PAPER_PACKAGE_MANIFEST.json").write_bytes(encoded({**self.manifest, "revision": 2}))
        self.assertIsNone(self.check())

    def test_different_run_is_not_inherited_from_old_receipt(self):
        other = self.package.with_name("Run-195")
        shutil.copytree(self.package, other)
        self.assertIsNone(gate.terminal_hold(other, self.folder.parent))

    def test_terminal_and_no_certificate_no_transport_flags_are_literal(self):
        for key, value in (("terminal_for_sealed_object", False), ("certificate_issued", True),
                           ("transport_performed_this_checkpoint", True), ("run_id", "Run-195")):
            with self.subTest(key=key):
                original = self.receipt[key]
                self.receipt[key] = value
                self.trust_current_receipt()
                self.assertIsNone(self.check())
                self.receipt[key] = original
                self.trust_current_receipt()

    def test_request_local_lean_and_run_identity_cannot_be_waived(self):
        for key, value in (("source_run", "Run-195"), ("local_lean_execution", True)):
            with self.subTest(key=key):
                original = self.request[key]
                self.request[key] = value
                self.rebind_document("ENGINE3_VERIFICATION_REQUEST.json", encoded(self.request))
                self.assertIsNone(self.check())
                self.request[key] = original
                self.rebind_document("ENGINE3_VERIFICATION_REQUEST.json", encoded(self.request))

    def test_checker_hash_and_loaded_source_are_pinned(self):
        self.receipt["bindings"]["premise_checker_sha256"] = "0" * 64
        self.trust_current_receipt()
        self.assertIsNone(self.check())
        self.receipt["bindings"]["premise_checker_sha256"] = gate.CHECKER_SHA256
        self.trust_current_receipt()
        with patch.object(gate, "TITLE_SHA256", "0" * 64):
            self.assertIsNone(self.check())
        with patch.object(gate, "ALIGNER_SHA256", "0" * 64):
            self.assertIsNone(self.check())

    def test_fresh_checker_pass_or_intake_error_never_excludes(self):
        for result in ({**self.receipt["checker_result"], "status": "PASS"},
                       {**self.receipt["checker_result"], "reasons": ["PREMISE_INTAKE_ERROR: invalid"]}):
            with self.subTest(result=result), patch.object(gate, "_pure_check", return_value=result):
                self.assertIsNone(self.check())

    def test_fresh_checker_recomputes_from_bound_sealed_documents(self):
        self.rebind_document("SEALED_RUN_MANIFEST.json", encoded({**self.manifest, "foundation_basis": "INDEPENDENT"}))
        self.rebind_document("SEALED_CLAIM_INVENTORY.json", encoded({"foundation_basis": "INDEPENDENT"}))
        (self.package / "PAPER_PACKAGE_MANIFEST.json").write_bytes(self.documents["SEALED_RUN_MANIFEST.json"])
        self.assertIsNone(self.check())

    def test_recorded_checker_result_must_equal_fresh_result(self):
        self.receipt["checker_result"]["findings"] = [{"asserted": "terminal"}]
        self.trust_current_receipt()
        self.assertIsNone(self.check())

    def test_symlinks_and_malformed_json_retain_fifo(self):
        original = self.receipt_path.read_bytes()
        target = self.root / "receipt.json"
        target.write_bytes(original)
        self.receipt_path.unlink()
        self.receipt_path.symlink_to(target)
        self.assertIsNone(self.check())
        self.receipt_path.unlink()
        self.receipt_path.write_bytes(b'{"run_id":"Run-194","run_id":"Run-194"}')
        self.trusted["Run-194"] = (self.receipt_path.name, gate._sha(self.receipt_path.read_bytes()))
        self.assertIsNone(self.check())

    def test_drift_during_check_retains_fifo(self):
        original = gate._pure_check
        def drift(*args):
            result = original(*args)
            (self.folder / "VERIFICATION_CANDIDATE.lean").write_text("changed after check")
            return result
        with patch.object(gate, "_pure_check", side_effect=drift):
            self.assertIsNone(self.check())


class ActualSelectionTests(TerminalFixture):
    def load_patched_sources(self):
        binding = json.loads((GATES / "terminal_certification/INTEGRATION_BINDING.json").read_text())
        self.assertFalse(binding["active"])
        self.assertEqual(gate._sha((GATES / "terminal_certification/terminal_hold.py").read_bytes()),
                         binding["terminal_helper_sha256"])
        for row in binding["files"]:
            source = GATES.parent.parent / row["snapshot"]
            self.assertEqual(gate._sha(source.read_bytes()), row["before_sha256"])
            target = self.root / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        patch_path = GATES / "terminal_certification/EXISTING_SELECTION.patch"
        self.assertEqual(gate._sha(patch_path.read_bytes()), binding["patch_sha256"])
        applied = subprocess.run(["patch", "--batch", "-p1", "-i", str(patch_path)],
                                 cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
        for row in binding["files"]:
            self.assertEqual(gate._sha((self.root / row["path"]).read_bytes()), row["after_sha256"])
        namespace = types.ModuleType("verification_coverage_gates")
        namespace.__path__ = [str(GATES)]
        terminal = types.ModuleType("verification_coverage_gates.terminal_certification")
        terminal.__path__ = [str(GATES / "terminal_certification")]
        metadata = types.ModuleType("verification_state_metadata")
        metadata.certified_metadata_contradictions = lambda _: []
        auth = types.ModuleType("comparator_data_egress_authorization")
        auth.validate_authorization = lambda *_: {"status": "AUTHORIZED"}
        packager = types.ModuleType("viridisos_kernel_packager")
        packager.KernelPackageError = RuntimeError
        def no_package(*args, **kwargs):
            raise RuntimeError("no kernel package in selection fixture")
        packager.validate_existing_kernel_package = no_package
        preflight = types.ModuleType("nightly_science_preflight")
        preflight.SCIENCE_ROOT = self.root / "science"
        preflight.RUNS_REL = Path("runs")
        preflight._latest_run = lambda _: (195, self.root / "latest")
        preflight.preflight = lambda *_: {"status": "READY"}
        paths = types.ModuleType("viridis_paths")
        paths.CONTROL_ROOT = self.root
        window = types.ModuleType("nightly_generation_window")
        window.generation_window = lambda *_: {"overdue": False, "generation_due": False}
        modules = {"verification_coverage_gates": namespace,
                   "verification_coverage_gates.terminal_certification": terminal,
                   "verification_coverage_gates.terminal_certification.terminal_hold": gate,
                   "verification_state_metadata": metadata, "comparator_data_egress_authorization": auth,
                   "viridisos_kernel_packager": packager, "nightly_science_preflight": preflight,
                   "viridis_paths": paths, "nightly_generation_window": window}
        context = patch.dict(sys.modules, modules)
        context.start()
        self.addCleanup(context.stop)
        def load(name):
            spec = importlib.util.spec_from_file_location(name, self.pipeline / (name + ".py"))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            self.addCleanup(sys.modules.pop, name, None)
            spec.loader.exec_module(module)
            return module
        controller = load("autonomous_pipeline_controller")
        controller.certificate_clean = lambda *_: False
        continuity = load("science_foundry_continuity")
        continuity.verifier_readiness = lambda *_: {"ready": True}
        return controller, continuity

    def test_actual_controller_advances_dispatch_without_certifying_or_publishing_younger(self):
        controller, _ = self.load_patched_sources()
        younger = self.package.with_name("Run-195")
        younger.mkdir()
        state = controller.build_state(finalized_root=self.pipeline / "finalized_runs",
                                       certificate_root=self.folder.parent,
                                       intake_path=self.root / "absent-intake.json",
                                       submission_map_path=self.root / "absent-map.json",
                                       nightly_packages_root=self.package.parent)
        self.assertEqual(state["items"][0]["state"], "TERMINAL_PREMISE_HOLD")
        self.assertTrue(state["items"][0]["human_gate"])
        self.assertEqual(state["first_action"]["run_id"], "Run-195")
        self.assertEqual(state["first_action"]["next_action"], "CERTIFY_COMPARATOR_FIFO")
        self.assertEqual(state["counts"]["submission_ready_packages"], 0)
        self.assertFalse(list(self.root.rglob("LEAN_ZERO_SORRY_CERTIFICATE*.json")))

    def test_unreviewed_hold_remains_actual_oldest_dispatch(self):
        controller, _ = self.load_patched_sources()
        self.receipt_path.unlink()
        item = controller.inspect_open_run(self.package, self.folder.parent, True)
        self.assertEqual(item.next_action, "CERTIFY_COMPARATOR_FIFO")

    def test_continuity_keeps_oldest_debt_and_separate_eligible_fifo(self):
        _, continuity = self.load_patched_sources()
        self.package.with_name("Run-195").mkdir()
        (self.root / "latest").mkdir()
        now = dt.datetime(2026, 10, 16, 12, tzinfo=dt.timezone.utc)
        (self.root / "latest/RUN_MANIFEST.json").write_bytes(encoded({"generated_at_utc": now.isoformat()}))
        result = continuity.evaluate(science_root=self.root / "science", control_root=self.root, now=now)
        certification = result["certification"]
        self.assertEqual(certification["backlog_runs"], ["Run-194", "Run-195"])
        self.assertEqual(certification["dispatch_fifo_runs"], ["Run-195"])
        self.assertEqual(certification["certified_runs"], [])
        self.assertFalse(certification["recent"])
        self.assertEqual(certification["backlog_count"], 2)
        self.assertIn("Run-195", result["next_action"])

    def test_actual_checkpoint_never_credits_younger_certificate_as_oldest_debt(self):
        fixture = GATES / "terminal_certification/tests/fixtures/nightly_checkpoint.py.txt"
        binding = json.loads((GATES / "terminal_certification/INTEGRATION_BINDING.json").read_text())
        self.assertEqual(gate._sha(fixture.read_bytes()), binding["unchanged_checkpoint_sha256"])
        source = ast.parse(fixture.read_text())
        assess = next(node for node in source.body if isinstance(node, ast.FunctionDef) and node.name == "assess")
        namespace = {}
        exec(compile(ast.Module(body=[assess], type_ignores=[]), str(fixture), "exec"), namespace)
        certification = {"backlog_runs": ["Run-194", "Run-195"], "certified_runs": [],
                         "ready": True, "recent": True, "backlog_critical": 7}
        start = {"science": {"certification": certification}, "invocation_id": "fixture",
                 "started_at_utc": "2026-10-16T12:00:00Z"}
        current = {"certification": {**certification, "backlog_runs": ["Run-194"],
                                      "certified_runs": ["Run-195"]},
                   "generation": {"ready": True, "due": False, "fresh": True},
                   "evaluated_at_utc": "2026-10-16T12:01:00Z"}
        result = namespace["assess"](start, current, {"items": [], "counts": {"submission_ready_packages": 0}})
        self.assertEqual(result["certification"]["target_runs"], ["Run-194", "Run-195"])
        self.assertEqual(result["certification"]["cleared_prior_debt"], ["Run-195"])
        self.assertIn("HOLD_FIFO_CERTIFICATION_TARGET_NOT_MET", result["incidents"])


if __name__ == "__main__":
    unittest.main()
