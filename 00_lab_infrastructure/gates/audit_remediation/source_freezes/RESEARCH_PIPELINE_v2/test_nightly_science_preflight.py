import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from nightly_science_preflight import preflight, REQUIRED_CONTROL, _request_runs


class NightlySciencePreflightTests(unittest.TestCase):
    def test_engine3_atomic_cutover_rejects_legacy_only_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            control = Path(tmp)
            legacy = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/example/ARISTOTLE_FORGE_REQUEST.json"
            legacy.parent.mkdir(parents=True)
            payload = {"source_run": "Run-148", "input_sha256": {"x": "y"}, "statement_contract_sha256": "z"}
            legacy.write_text(json.dumps(payload), encoding="utf-8")
            self.assertNotIn(148, _request_runs(control))

            engine3 = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-148/ENGINE3_VERIFICATION_REQUEST.json"
            engine3.parent.mkdir(parents=True)
            payload.update({"request_kind": "LEAN_PROOF", "primary_verifier": "COMPARATOR_CLOUD", "aristotle_required": False})
            engine3.write_text(json.dumps(payload), encoding="utf-8")
            self.assertIn(148, _request_runs(control))

    def add_certificate(self, control, run_number, request):
        audit = control / f"audit-{run_number}.json"
        cloud = control / f"cloud-{run_number}.json"
        audit.write_text("{}", encoding="utf-8")
        cloud.write_text("{}", encoding="utf-8")
        sealed = control / f"sealed-paper-{run_number}.pdf"
        sealed.write_bytes(b"paper")
        def binding(path):
            return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        certificate = control / f"RESEARCH_PIPELINE_v2/lean_certificates/Run-{run_number:03d}/LEAN_ZERO_SORRY_CERTIFICATE.json"
        certificate.parent.mkdir(parents=True)
        certificate.write_text(json.dumps({
            "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "run_id": f"Run-{run_number:03d}",
            "bindings": {
                "request": binding(request),
                "aristotle_audit": binding(audit),
                "independent_cloud_receipt": binding(cloud),
                "sealed_paper_inputs": {"SEALED_paper.pdf": binding(sealed)},
            },
        }), encoding="utf-8")

    def add_comparator_certificate(self, control, run_number, request):
        cloud = control / f"comparator-cloud-{run_number}.json"
        statement = control / f"statement-{run_number}.lean"
        candidate = control / f"candidate-{run_number}.lean"
        sealed = control / f"sealed-comparator-paper-{run_number}.pdf"
        for path, value in ((cloud, b"{}"), (statement, b"theorem x : True := by sorry"),
                            (candidate, b"theorem x : True := by trivial"), (sealed, b"paper")):
            path.write_bytes(value)
        def binding(path):
            return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        certificate = control / f"RESEARCH_PIPELINE_v2/lean_certificates/Run-{run_number:03d}/LEAN_ZERO_SORRY_CERTIFICATE.json"
        certificate.parent.mkdir(parents=True)
        certificate.write_text(json.dumps({
            "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "run_id": f"Run-{run_number:03d}",
            "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
            "bindings": {
                "request": binding(request),
                "independent_cloud_receipt": binding(cloud),
                "formal_statement": binding(statement),
                "candidate_proof": binding(candidate),
                "sealed_paper_inputs": {"SEALED_paper.pdf": binding(sealed)},
            },
        }), encoding="utf-8")

    def test_pipeline_relative_certificate_bindings_are_current(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        pipeline = control / "RESEARCH_PIPELINE_v2"
        files = {
            "request": (pipeline / "lean_certificates/Run-116/request.json", b"{}"),
            "cloud": (pipeline / "lean_certificates/Run-116/cloud.json", b"{}"),
            "statement": (pipeline / "lean_certificates/Run-116/statement.lean", b"theorem x : True := by sorry"),
            "candidate": (pipeline / "lean_certificates/Run-116/candidate.lean", b"theorem x : True := by trivial"),
            "sealed": (pipeline / "lean_certificates/Run-116/SEALED_paper.pdf", b"paper"),
        }
        for path, value in files.values():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        def binding(path):
            return {
                "path": str(path.relative_to(pipeline)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        certificate = pipeline / "lean_certificates/Run-116/LEAN_ZERO_SORRY_CERTIFICATE.json"
        certificate.write_text(json.dumps({
            "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "run_id": "Run-116",
            "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
            "bindings": {
                "request": binding(files["request"][0]),
                "independent_cloud_receipt": binding(files["cloud"][0]),
                "formal_statement": binding(files["statement"][0]),
                "candidate_proof": binding(files["candidate"][0]),
                "sealed_paper_inputs": {"SEALED_paper.pdf": binding(files["sealed"][0])},
            },
        }), encoding="utf-8")
        result = preflight(science, control, 117)
        self.assertNotIn(116, result["proof_obligations"]["missing_certificate"])

    def fixture(self):
        temp = tempfile.TemporaryDirectory()
        base = Path(temp.name)
        science = base / "science "
        control = base / "control"
        runs = science / "07_nightly_engine/compound research papers"
        state_dir = science / "07_nightly_engine/viridis-science-agent/nightly"
        runs.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        (runs / "Run-116_example").mkdir()
        (state_dir / "NIGHTLY_STATE.md").write_text("### Run 116\n", encoding="utf-8")
        state = {
            "current_run": 116,
            "selection_policy_id": "VRS-NIGHTLY-SELECTION-2",
            "sum_staleness": 1,
            "areas": [{"staleness": 1}],
            "locked_directives": [{"run": 117, "area_id": "15"}],
        }
        (state_dir / "NIGHTLY_STATE.json").write_text(json.dumps(state), encoding="utf-8")
        for rel in REQUIRED_CONTROL:
            path = control / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x", encoding="utf-8")
        (control / "RESEARCH_PIPELINE_v2/NIGHTLY_SELECTION_POLICY_v1.json").write_text(
            json.dumps({"policy_id": "VRS-NIGHTLY-SELECTION-2", "generator_exit_state": "DISPOSITION_ASSIGNED"}),
            encoding="utf-8",
        )
        (control / "new leans").mkdir()
        return temp, science, control

    def test_ready(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        self.assertEqual(preflight(science, control, 117)["status"], "READY")

    def test_duplicate_next_run_fails_closed(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        (science / "07_nightly_engine/compound research papers/Run-117_duplicate").mkdir()
        result = preflight(science, control, 117)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("already exists" in item for item in result["failures"]))

    def test_receipt_era_formal_target_requires_mirror_and_request_before_next_run(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        runs = science / "07_nightly_engine/compound research papers"
        (runs / "Run-116_example").rename(runs / "Run-117_example")
        run = runs / "Run-117_example"
        (run / "CLAIM_INVENTORY.json").write_text(
            json.dumps({"claims": [{"evidence_class": "FORMAL_TARGET"}]}),
            encoding="utf-8",
        )
        state_path = science / "07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"current_run": 117, "locked_directives": [{"run": 118, "area_id": "15"}]})
        state_path.write_text(json.dumps(state), encoding="utf-8")

        held = preflight(science, control, 118)
        self.assertEqual(held["status"], "HOLD")
        self.assertEqual(held["proof_obligations"]["missing_mirror"], [117])
        self.assertEqual(held["proof_obligations"]["missing_request"], [117])

        receipt = control / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts/Run-117.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({"status": "MIRRORED"}), encoding="utf-8")
        request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-117-proof/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
        request.parent.mkdir(parents=True)
        request.write_text(
            json.dumps({
                "source_run": "Run-117",
                "input_sha256": {"Target.lean": "a" * 64},
                "statement_contract_sha256": "b" * 64,
            }),
            encoding="utf-8",
        )
        rolling_debt = preflight(science, control, 118)
        self.assertEqual(rolling_debt["status"], "READY")
        self.assertFalse(rolling_debt["generation_blocked_by_certificate_debt"])
        self.assertEqual(rolling_debt["proof_obligations"]["missing_certificate"], [117])
        self.add_certificate(control, 117, request)
        self.assertEqual(preflight(science, control, 118)["status"], "READY")
        (control / "sealed-paper-117.pdf").write_bytes(b"changed")
        drifted = preflight(science, control, 118)
        self.assertEqual(drifted["status"], "READY")
        self.assertEqual(drifted["proof_obligations"]["missing_certificate"], [117])

    def test_receipt_era_paper_without_formal_target_is_not_exempt(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        runs = science / "07_nightly_engine/compound research papers"
        (runs / "Run-116_example").rename(runs / "Run-117_empirical_note")
        state_path = science / "07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"current_run": 117, "locked_directives": [{"run": 118, "area_id": "15"}]})
        state_path.write_text(json.dumps(state), encoding="utf-8")

        result = preflight(science, control, 118)

        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["proof_obligations"]["missing_mirror"], [117])
        self.assertEqual(result["proof_obligations"]["missing_request"], [117])
        self.assertEqual(result["proof_obligations"]["missing_certificate"], [117])

    def test_comparator_certificate_counts_without_aristotle_audit(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        request = control / "request-117.json"
        request.write_text("{}", encoding="utf-8")
        self.add_comparator_certificate(control, 117, request)
        from nightly_science_preflight import _has_current_certificate
        self.assertTrue(_has_current_certificate(control, 117))

    def test_control_root_relative_comparator_bindings_are_current(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        cert_dir = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-117"
        cert_dir.mkdir(parents=True)
        files = {
            "request": cert_dir / "ENGINE3_VERIFICATION_REQUEST.json",
            "independent_cloud_receipt": cert_dir / "COMPARATOR_CLOUD_RECEIPT.json",
            "formal_statement": cert_dir / "VERIFICATION_STATEMENT.lean",
            "candidate_proof": cert_dir / "VERIFICATION_CANDIDATE.lean",
            "SEALED_paper.pdf": cert_dir / "SEALED_paper.pdf",
        }
        for path in files.values():
            path.write_bytes(path.name.encode("utf-8"))

        def relative_binding(path):
            return {
                "path": str(path.relative_to(control)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }

        certificate = cert_dir / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        certificate.write_text(json.dumps({
            "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "run_id": "Run-117",
            "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
            "bindings": {
                name: relative_binding(path)
                for name, path in files.items()
                if name != "SEALED_paper.pdf"
            } | {
                "sealed_paper_inputs": {
                    "SEALED_paper.pdf": relative_binding(files["SEALED_paper.pdf"]),
                }
            },
        }), encoding="utf-8")

        from nightly_science_preflight import _has_current_certificate
        self.assertTrue(_has_current_certificate(control, 117))

    def test_legacy_absolute_control_root_spelling_resolves_by_safe_suffix(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        cert_dir = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-117"
        cert_dir.mkdir(parents=True)
        artifact = cert_dir / "VERIFICATION_CANDIDATE.lean"
        artifact.write_text("theorem t : True := by trivial\n", encoding="utf-8")
        from nightly_science_preflight import _binding_is_current
        binding = {
            "path": "/stale/Viridis Core docs  2.0/RESEARCH_PIPELINE_v2/lean_certificates/Run-117/VERIFICATION_CANDIDATE.lean",
            "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        }
        self.assertTrue(_binding_is_current(binding, control))

    def test_engine3_comparator_request_counts_without_aristotle_request(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        runs = science / "07_nightly_engine/compound research papers"
        (runs / "Run-116_example").rename(runs / "Run-117_engine3")
        state_path = science / "07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"current_run": 117, "locked_directives": [{"run": 118, "area_id": "15"}]})
        state_path.write_text(json.dumps(state), encoding="utf-8")
        receipt = control / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts/Run-117.json"
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps({"status": "MIRRORED"}), encoding="utf-8")
        request = control / "science-engine/07_nightly_engine/compound research papers/Run-117_engine3/formalization/ENGINE3_VERIFICATION_REQUEST.json"
        request.parent.mkdir(parents=True)
        request.write_text(json.dumps({
            "source_run": "Run-117",
            "request_kind": "LEAN_PROOF",
            "primary_verifier": "COMPARATOR_CLOUD",
            "aristotle_required": False,
            "input_sha256": {"VERIFICATION_STATEMENT.lean": "a" * 64},
            "statement_contract_sha256": "b" * 64,
        }), encoding="utf-8")

        result = preflight(science, control, 118)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["proof_obligations"]["missing_request"], [])

    def test_finalized_reviewed_run_still_requires_certificate(self):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        runs = science / "07_nightly_engine/compound research papers"
        (runs / "Run-116_example").rename(runs / "Run-117_example")
        run = runs / "Run-117_example"
        (run / "CLAIM_INVENTORY.json").write_text(
            json.dumps({"claims": [{"evidence_class": "FORMAL_TARGET"}]}),
            encoding="utf-8",
        )
        state_path = science / "07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"current_run": 117, "locked_directives": [{"run": 118, "area_id": "15"}]})
        state_path.write_text(json.dumps(state), encoding="utf-8")
        finalized = control / "RESEARCH_PIPELINE_v2/finalized_runs/Run-117/FINALIZED_PACKAGE.json"
        finalized.parent.mkdir(parents=True)
        finalized.write_text(
            json.dumps({"status": "FINALIZED", "run_id": "Run-117"}),
            encoding="utf-8",
        )

        result = preflight(science, control, 118)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["proof_obligations"]["missing_certificate"], [117])


class VersionedCertificateDiscoveryTests(unittest.TestCase):
    """Certificate discovery must agree without weakening the byte bindings."""

    fixture = NightlySciencePreflightTests.fixture
    add_comparator_certificate = NightlySciencePreflightTests.add_comparator_certificate

    def certificate_fixture(self, suffix="DECLARATION_R2", issued="2026-10-18T13:39:05+00:00"):
        temp, science, control = self.fixture()
        self.addCleanup(temp.cleanup)
        request = control / "request-117.json"
        request.write_text("{}", encoding="utf-8")
        self.add_comparator_certificate(control, 117, request)
        root = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-117"
        original = root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        certificate = root / f"LEAN_ZERO_SORRY_CERTIFICATE_{suffix}.json"
        payload = json.loads(original.read_text(encoding="utf-8"))
        payload["issued_at_utc"] = issued
        original.unlink()
        certificate.write_text(json.dumps(payload), encoding="utf-8")
        return control, certificate, payload

    def current(self, control):
        from nightly_science_preflight import _has_current_certificate
        return _has_current_certificate(control, 117)

    def test_versioned_r1_and_r2_certificates_count_without_integrity_hold(self):
        for suffix in ("ALIGNMENT_R1", "DECLARATION_R2"):
            with self.subTest(suffix=suffix):
                control, certificate, payload = self.certificate_fixture(suffix)
                self.assertFalse((certificate.parent / "CERTIFICATION_INTEGRITY_HOLD.json").exists())
                self.assertTrue(self.current(control))

    def test_versioned_certificate_rejects_each_drifted_required_binding(self):
        for name in ("request", "independent_cloud_receipt", "formal_statement", "candidate_proof", "SEALED_paper.pdf"):
            with self.subTest(binding=name):
                control, certificate, payload = self.certificate_fixture()
                bindings = payload["bindings"]
                binding = bindings["sealed_paper_inputs"][name] if name == "SEALED_paper.pdf" else bindings[name]
                Path(binding["path"]).write_bytes(b"drifted")
                self.assertFalse(self.current(control))

    def test_versioned_certificate_rejects_wrong_identity_standard_and_status(self):
        for name, invalid in (("run_id", "Run-118"), ("standard", "UNSUPPORTED"), ("status", "HOLD")):
            with self.subTest(field=name):
                control, certificate, payload = self.certificate_fixture()
                payload[name] = invalid
                certificate.write_text(json.dumps(payload), encoding="utf-8")
                self.assertFalse(self.current(control))

    def test_versioned_certificate_rejects_missing_or_malformed_bindings(self):
        for bindings in (None, [], {}, {"sealed_paper_inputs": {}}):
            with self.subTest(bindings=bindings):
                control, certificate, payload = self.certificate_fixture()
                payload["bindings"] = bindings
                certificate.write_text(json.dumps(payload), encoding="utf-8")
                self.assertFalse(self.current(control))

    def test_malformed_versioned_receipt_does_not_count(self):
        for invalid in ("{not-json", "[]", "null"):
            with self.subTest(receipt=invalid):
                control, certificate, payload = self.certificate_fixture()
                certificate.write_text(invalid, encoding="utf-8")
                self.assertFalse(self.current(control))

    def test_integrity_hold_requires_current_evidence_and_remains_untouched(self):
        control, certificate, payload = self.certificate_fixture()
        hold = certificate.parent / "CERTIFICATION_INTEGRITY_HOLD.json"
        hold_bytes = b'{"status":"HOLD","reason":"historical evidence retained"}\n'
        hold.write_bytes(hold_bytes)
        self.assertTrue(self.current(control))
        Path(payload["bindings"]["candidate_proof"]["path"]).write_bytes(b"drifted")
        self.assertFalse(self.current(control))
        certificate.unlink()
        self.assertFalse(self.current(control))
        self.assertEqual(hold.read_bytes(), hold_bytes)

    def test_valid_predecessor_remains_evidence_when_newer_receipt_is_invalid(self):
        control, certificate, payload = self.certificate_fixture()
        later = certificate.parent / "LEAN_ZERO_SORRY_CERTIFICATE_DECLARATION_R3.json"
        invalid = dict(payload, issued_at_utc="2026-10-18T14:00:00+00:00", run_id="Run-118")
        later.write_text(json.dumps(invalid), encoding="utf-8")
        self.assertTrue(self.current(control))



if __name__ == "__main__":
    unittest.main()
