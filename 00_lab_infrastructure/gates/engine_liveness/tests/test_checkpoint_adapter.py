import argparse
import ast
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import checkpoint_certification_lane as adapter
from scheduler_liveness import LivenessHold, file_digest


class CheckpointAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.pipeline = Path(self.temporary.name) / "RESEARCH_PIPELINE_v2"
        self.start = self.pipeline / "nightly_checkpoints/invocation/START.json"
        self.start.parent.mkdir(parents=True)
        self.start.write_text(json.dumps({"science": {"certification": {"backlog_runs": ["Run-194", "Run-195"]}}}))
        self.queue = self.start.parent / "QUEUE.json"
        self.entries = []
        for number in (194, 195):
            folder = self.pipeline / "lean_certificates" / f"Run-{number}"
            folder.mkdir(parents=True)
            statement, candidate = folder / "statement.lean", folder / "candidate.lean"
            statement.write_text("frozen statement"); candidate.write_text("frozen candidate")
            request = folder / "request.json"
            request.write_text(json.dumps({"source_run": f"Run-{number}", "toolchain": "leanprover/lean4:v4.28.0",
                "mathlib_rev": "b" * 40, "local_lean_execution": False,
                "input_sha256": {statement.name: file_digest(statement), candidate.name: file_digest(candidate)}}))
            self.entries.append({"run_id": f"Run-{number}",
                **{name: {"path": str(path), "sha256": file_digest(path)} for name, path in
                   [("request", request), ("formal_statement", statement), ("candidate", candidate)]},
                "receipt_output": str(folder / "fresh-receipt.json"), "certificate_output": str(folder / "fresh-certificate.json")})
        self.write_queue()
        checker = self.pipeline / "verification_coverage_gates/premise_declaration.py"
        checker.parent.mkdir()
        checker.write_text('def validate_envelope(*args, **kwargs):\n return {"status":"PASS", "historical_exemption":False}\n')
        self.modules = {
            "comparator_data_egress_authorization": SimpleNamespace(validate_authorization=lambda *args: {"status": "AUTHORIZED"}),
            "nightly_checkpoint": SimpleNamespace(read_start=lambda path: json.loads(path.read_text()))}

    def write_queue(self):
        self.queue.write_text(json.dumps({"standard": "VRS-SCHEDULER-CERTIFICATION-QUEUE-1",
            "start_sha256": file_digest(self.start), "entries": self.entries}))

    def verifier(self, identity, entry, paths):
        Path(entry["receipt_output"]).write_text("fresh receipt from mocked protected verifier")
        certificate = {"run_id": identity.run_id, "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "bindings": {"request": {"sha256": identity.request_sha256}, "formal_statement": {"sha256": identity.statement_sha256},
                "candidate_proof": {"sha256": identity.candidate_sha256},
                "independent_cloud_receipt": {"sha256": file_digest(Path(entry["receipt_output"]))}},
            "gates": {name: True for name in ("comparator_nanoda_kernel", "comparator_lean_kernel", "zero_sorries_or_admits",
                "nonvacuity_witnesses", "premise_declaration", "allowed_axioms_only", "independent_cloud_kernel_verification",
                "frozen_statement_and_candidate_hash_bound", "sealed_statement_signature_alignment")}}
        certificate["gates"]["local_lean_execution"] = False
        Path(entry["certificate_output"]).write_text(json.dumps(certificate))
        return {"status": "VERIFIED"}, certificate

    def drain(self, verifier=None):
        with patch.dict(sys.modules, self.modules), patch.object(adapter, "validate_policy", return_value={}), \
             patch.object(adapter, "_verify_one", side_effect=verifier or self.verifier):
            return adapter.drain_checkpoint(self.start, self.queue, pipeline=self.pipeline)

    def test_existing_checkpoint_dispatches_and_resume_never_sends_again(self):
        sent = []
        def verifier(*args):
            sent.append(args[0].run_id)
            return self.verifier(*args)
        first = self.drain(verifier)
        second = self.drain(lambda *args: self.fail("duplicate provider send"))
        self.assertEqual(sorted(sent), ["Run-194", "Run-195"])
        self.assertEqual(first, second)
        self.assertEqual(first["accepted"], ["Run-194", "Run-195"])

    def test_transport_ambiguity_remains_reserved_on_resume(self):
        def ambiguous(*args): raise TimeoutError("provider state unknown")
        first = self.drain(ambiguous)
        second = self.drain(lambda *args: self.fail("ambiguous request resent"))
        self.assertEqual(first, second)
        self.assertEqual(len(second["holds"]), 2)

    def test_resume_rejects_certificate_byte_drift_from_holding_area(self):
        self.drain()
        path = Path(self.entries[0]["certificate_output"])
        certificate = json.loads(path.read_text()); certificate["scope"] = "edited after acceptance"
        path.write_text(json.dumps(certificate))
        with self.assertRaisesRegex(LivenessHold, "RESULT_ARTIFACT_DRIFT"):
            self.drain(lambda *args: self.fail("accepted request resent"))

    def test_resume_rejects_cloud_and_certificate_rebinding(self):
        self.drain()
        cloud = Path(self.entries[0]["receipt_output"]); cloud.write_text("different receipt bytes")
        path = Path(self.entries[0]["certificate_output"])
        certificate = json.loads(path.read_text())
        certificate["bindings"]["independent_cloud_receipt"]["sha256"] = file_digest(cloud)
        path.write_text(json.dumps(certificate))
        with self.assertRaisesRegex(LivenessHold, "RESULT_ARTIFACT_DRIFT"):
            self.drain(lambda *args: self.fail("accepted request resent"))

    def test_manifest_cannot_omit_named_oldest_start_debt(self):
        self.entries.pop(0); self.write_queue()
        with self.assertRaisesRegex(LivenessHold, "QUEUE_BASELINE"):
            self.drain(lambda *args: self.fail("invalid baseline reached transport"))

    def test_premise_preflight_fails_before_reservation_or_transport(self):
        checker = self.pipeline / "verification_coverage_gates/premise_declaration.py"
        checker.write_text('def validate_envelope(*args, **kwargs):\n return {"status":"HOLD"}\n')
        with self.assertRaisesRegex(LivenessHold, "PREMISE_PREFLIGHT"):
            self.drain(lambda *args: self.fail("premise hold reached transport"))
        self.assertFalse((self.pipeline / "parallel_certification/requests").exists())

    def test_protected_verifier_and_issuer_are_the_only_execution_route(self):
        identity, paths = adapter.identity_for(self.entries[0], self.pipeline)
        calls = []
        modules = {"comparator_cloud_lean_verifier": SimpleNamespace(verify=lambda **kwargs: calls.append(("verify", kwargs)) or {"status": "VERIFIED"}),
            "issue_lean_zero_sorry_certificate": SimpleNamespace(issue=lambda **kwargs: calls.append(("issue", kwargs)) or {})}
        with patch.dict(sys.modules, modules):
            adapter._verify_one(identity, self.entries[0], paths)
        self.assertEqual([name for name, _ in calls], ["verify", "issue"])
        self.assertTrue(calls[1][1]["require_premise_declaration"])
        self.assertNotIn("host", calls[0][1])
        self.assertNotIn("transport", calls[0][1])

    def test_actual_checkpoint_patch_hashes_and_drains_original_start(self):
        fixture = HERE / "tests/fixtures/nightly_checkpoint.py.txt"
        binding = next(row for row in json.loads((HERE / "INTEGRATION_BINDING.json").read_text())["files"] if row["path"].endswith("/nightly_checkpoint.py"))
        self.assertEqual(file_digest(fixture), binding["before_sha256"])
        target = self.pipeline / "nightly_checkpoint.py"; target.write_bytes(fixture.read_bytes())
        result = subprocess.run(["git", "apply", "--unidiff-zero", str(HERE / "G2_EXISTING_CHECKPOINT.patch")], cwd=self.pipeline.parent, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(file_digest(target), binding["after_sha256"])
        tree = ast.parse(target.read_text()); main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        namespace = {"argparse": argparse, "Path": Path, "json": json,
                     "checkpoint_advisory_after_checkpoint": lambda path: None}
        exec(compile(ast.Module(body=[main], type_ignores=[]), "nightly_checkpoint.py", "exec"), namespace)
        calls = []
        modules = {"checkpoint_certification_lane": SimpleNamespace(drain_checkpoint=lambda *args: calls.append(args) or {"status": "COMPLETED"})}
        with patch.dict(sys.modules, modules), patch.object(sys, "argv", ["nightly_checkpoint.py", "--drain-certification", str(self.start), "--certification-queue", str(self.queue)]):
            self.assertEqual(namespace["main"](), 0)
        self.assertEqual(calls, [(self.start, self.queue)])


if __name__ == "__main__":
    unittest.main()
