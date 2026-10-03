from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comparator-deploy"))
from comparator_cloud_lean_verifier import VerificationError, verify
from engine3_align_challenge import align_challenge


class ComparatorVerifierTests(unittest.TestCase):
    def fixture(self, root: Path, candidate: str) -> tuple[Path, Path, Path, Path, Path]:
        request = root / "request.json"
        formal = root / "statement.lean"
        solution = root / "candidate.lean"
        output = root / "receipt.json"
        key = root / "key"
        formal.write_text(
            "theorem main_result : True := by sorry\n"
            "theorem witness : True := by sorry\n"
        )
        solution.write_text(candidate)
        request.write_text(
            json.dumps(
                {
                    "request_kind": "LEAN_PROOF",
                    "source_run": "Run-144",
                    "candidate_id": "run144-v1",
                    "toolchain": "leanprover/lean4:v4.28.0",
                    "expected_theorem_names": ["main_result"],
                    "nonvacuity_obligations": ["witness"],
                    "statement_contract_sha256": hashlib.sha256(formal.read_bytes()).hexdigest(),
                    "input_sha256": {
                        formal.name: hashlib.sha256(formal.read_bytes()).hexdigest(),
                        solution.name: hashlib.sha256(solution.read_bytes()).hexdigest(),
                    },
                }
            )
        )
        key.write_text("test-only")
        return request, formal, solution, output, key

    def test_dual_kernel_acceptance_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(
                Path(directory),
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n",
            )

            def accepted(payload, host, key, timeout):
                self.assertEqual(payload["theoremNames"], ["main_result", "witness"])
                return 0, {
                    "type": "verification-ok",
                    "project": "viridis-lean-4.28",
                    "theoremNames": ["V.main_result", "V.witness"],
                    "output": (
                        "Nanoda kernel accepts the solution\n"
                        "Lean default kernel accepts the solution.\n"
                        "Your solution is okay!\n"
                    ),
                }

            receipt = verify(
                request_path=paths[0],
                formal_statement_path=paths[1],
                candidate_path=paths[2],
                output_path=paths[3],
                key=paths[4],
                transport=accepted,
            )
            self.assertEqual(receipt["status"], "VERIFIED")
            self.assertTrue(receipt["checks"]["nanoda_kernel_accepted"])
            self.assertTrue(receipt["checks"]["lean_kernel_accepted"])

    def test_missing_second_kernel_marker_holds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(
                Path(directory),
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n",
            )

            def incomplete(payload, host, key, timeout):
                return 0, {
                    "type": "verification-ok",
                    "project": "viridis-lean-4.28",
                    "output": "Lean default kernel accepts the solution.\nYour solution is okay!\n",
                }

            receipt = verify(
                request_path=paths[0],
                formal_statement_path=paths[1],
                candidate_path=paths[2],
                output_path=paths[3],
                key=paths[4],
                transport=incomplete,
            )
            self.assertEqual(receipt["status"], "HOLD")

    def test_candidate_sorry_fails_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(
                Path(directory),
                "theorem main_result : True := by sorry\n"
                "theorem witness : True := by trivial\n",
            )
            with self.assertRaises(VerificationError):
                verify(
                    request_path=paths[0],
                    formal_statement_path=paths[1],
                    candidate_path=paths[2],
                    output_path=paths[3],
                    key=paths[4],
                )

    def test_five_minute_slo_rejects_longer_client_timeout(self) -> None:
        # The client wait alone is not server admission. Keep the default 300s
        # promise and require the exact server allowlist for foundation's limit.
        import subprocess
        profile_module = Path(__file__).resolve().parents[2] / "comparator-deploy/service-profile/src/resource-profile.mjs"
        script = """
import {DEFAULT_PROFILE, FOUNDATION_PROFILE, PROJECT_POLICY, resolveObservedPolicy, selectResourceProfile}
  from 'MODULE_URI';
const approved = resolveObservedPolicy(PROJECT_POLICY.project, PROJECT_POLICY);
const spoofed = selectResourceProfile({project:PROJECT_POLICY.project,
  challenge:'nightly-fixture',solution:'nightly-fixture',timeout:1200,
  profile:FOUNDATION_PROFILE.name,theoremNames:PROJECT_POLICY.theorem_names});
console.log(JSON.stringify({default:DEFAULT_PROFILE,approved,spoofed}));
""".replace("MODULE_URI", profile_module.as_uri())
        policy = json.loads(subprocess.check_output(["node", "--input-type=module", "-e", script], text=True))
        self.assertEqual(policy["default"]["client_wait_seconds"], 300)
        self.assertEqual(policy["default"]["comparator_wall_ms"], 285000)
        self.assertEqual(policy["spoofed"], policy["default"])
        self.assertEqual(policy["approved"]["client_wait_seconds"], 1200)
        self.assertEqual(policy["approved"]["comparator_wall_ms"], 600000)
        for key in ("compile_wall_ms", "collection_wall_ms", "comparator_cpu_seconds", "memory_max_bytes", "toolchain"):
            self.assertEqual(policy["approved"][key], policy["default"][key])
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(Path(directory),
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n")
            calls = []
            def rejected(payload, host, key, timeout):
                calls.append(timeout)
                return 2, {"type":"verification-failed", "project":"viridis-lean-4.28", "output":"phase wall limit"}
            receipt = verify(request_path=paths[0], formal_statement_path=paths[1],
                candidate_path=paths[2], output_path=paths[3], key=paths[4], transport=rejected)
            self.assertEqual(calls, [300])
            self.assertEqual(receipt["status"], "HOLD")

    def test_unbound_candidate_fails_before_transport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(
                Path(directory),
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n",
            )
            paths[2].write_text(paths[2].read_text() + "\n", encoding="utf-8")
            with self.assertRaisesRegex(VerificationError, "exact request-bound input"):
                verify(
                    request_path=paths[0],
                    formal_statement_path=paths[1],
                    candidate_path=paths[2],
                    output_path=paths[3],
                    key=paths[4],
                )

    def test_hash_bound_aligned_challenge_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = self.fixture(
                root,
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n",
            )
            sealed = root / "SEALED_STATEMENT.lean"
            sealed.write_text(paths[1].read_text(encoding="utf-8"), encoding="utf-8")
            paths[1].write_text(align_challenge(
                sealed.read_text(), paths[2].read_text(), ["main_result", "witness"]
            )[0])
            receipt = root / "ALIGNMENT.json"
            receipt.write_text(json.dumps({
                "standard": "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1",
                "status": "FROZEN",
                "sealed_statement": {"sha256": hashlib.sha256(sealed.read_bytes()).hexdigest()},
                "aligned_challenge": {"sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest()},
                "candidate": {"sha256": hashlib.sha256(paths[2].read_bytes()).hexdigest()},
                "expected_theorem_names": ["main_result"],
                "target_signatures_match_sealed_statement": True,
                "candidate_forbidden_constructs_empty": True,
            }), encoding="utf-8")
            request_value = json.loads(paths[0].read_text(encoding="utf-8"))
            request_value["statement_contract_sha256"] = hashlib.sha256(sealed.read_bytes()).hexdigest()
            request_value["input_sha256"][paths[1].name] = hashlib.sha256(paths[1].read_bytes()).hexdigest()
            request_value["statement_alignment"] = {
                "standard": "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1",
                "sealed_statement": {"filename": sealed.name, "sha256": hashlib.sha256(sealed.read_bytes()).hexdigest()},
                "receipt": {"filename": receipt.name, "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()},
            }
            paths[0].write_text(json.dumps(request_value), encoding="utf-8")

            def accepted(payload, host, key, timeout):
                return 0, {
                    "type": "verification-ok",
                    "project": "viridis-lean-4.28",
                    "theoremNames": ["V.main_result", "V.witness"],
                    "output": (
                        "Nanoda kernel accepts the solution\n"
                        "Lean default kernel accepts the solution.\n"
                        "Your solution is okay!\n"
                    ),
                }

            result = verify(
                request_path=paths[0], formal_statement_path=paths[1], candidate_path=paths[2],
                output_path=paths[3], key=paths[4], transport=accepted,
            )
            self.assertTrue(result["checks"]["sealed_statement_signature_alignment"])
            self.assertIn("statement_alignment", result)


    def test_malformed_or_empty_nonvacuity_never_reaches_transport(self) -> None:
        for obligations in (None, [], "witness", {}, [""], ["needs a witness"],
                            ["witness", 7], ["witness", "witness"], ["V..witness"]):
            with self.subTest(obligations=obligations), tempfile.TemporaryDirectory() as directory:
                paths = self.fixture(Path(directory),
                    "theorem main_result : True := by trivial\n"
                    "theorem witness : True := by trivial\n")
                value = json.loads(paths[0].read_text())
                value["nonvacuity_obligations"] = obligations
                paths[0].write_text(json.dumps(value))
                def must_not_send(*args):
                    self.fail("invalid witness contract reached network transport")
                with self.assertRaisesRegex(VerificationError, "nonvacuity_obligations"):
                    verify(request_path=paths[0], formal_statement_path=paths[1],
                           candidate_path=paths[2], output_path=paths[3], key=paths[4],
                           transport=must_not_send)
                self.assertFalse(paths[3].exists())

    def test_missing_witness_export_cannot_report_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(Path(directory),
                "theorem main_result : True := by trivial\n"
                "theorem witness : True := by trivial\n")
            def omitted(payload, host, key, timeout):
                return 0, {"type": "verification-ok", "project": "viridis-lean-4.28",
                    "theoremNames": ["V.main_result"],
                    "output": "Nanoda kernel accepts the solution\nLean default kernel accepts the solution\nYour solution is okay!"}
            result = verify(request_path=paths[0], formal_statement_path=paths[1],
                            candidate_path=paths[2], output_path=paths[3], key=paths[4], transport=omitted)
            self.assertEqual(result["status"], "HOLD")
            self.assertFalse(result["checks"]["targeted_export_complete"])


    def test_forged_pass_alignment_cannot_change_scientific_context(self):
        for sealed_prefix, candidate_prefix in (
            ("def admissible : Prop := False\n", "def admissible : Prop := True\n"),
            ("variable (h : False)\n", "variable (h : True)\n"),
            ("import Mathlib.Data.Nat.Basic\n", "import Mathlib\n"),
        ):
            with self.subTest(prefix=sealed_prefix), tempfile.TemporaryDirectory() as directory:
                paths = self.fixture(Path(directory), candidate_prefix +
                    "theorem main_result : True := by trivial\n"
                    "theorem witness : True := by trivial\n")
                paths[1].write_text(candidate_prefix + paths[1].read_text())
                if sealed_prefix.startswith("def admissible"):
                    for source in (paths[1], paths[2]):
                        source.write_text(source.read_text().replace("theorem main_result : True", "theorem main_result : admissible"))
                sealed = Path(directory) / "sealed.lean"
                sealed.write_text(paths[1].read_text().replace(candidate_prefix, sealed_prefix, 1))
                receipt = Path(directory) / "alignment.json"
                receipt.write_text(json.dumps({
                    "status": "FROZEN", "standard": "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1",
                    "sealed_statement": {"sha256": hashlib.sha256(sealed.read_bytes()).hexdigest()},
                    "aligned_challenge": {"sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest()},
                    "candidate": {"sha256": hashlib.sha256(paths[2].read_bytes()).hexdigest()},
                    "expected_theorem_names": ["main_result"],
                    "target_signatures_match_sealed_statement": True,
                    "candidate_forbidden_constructs_empty": True,
                }))
                value = json.loads(paths[0].read_text())
                value["input_sha256"][paths[1].name] = hashlib.sha256(paths[1].read_bytes()).hexdigest()
                value["input_sha256"][paths[2].name] = hashlib.sha256(paths[2].read_bytes()).hexdigest()
                value["statement_contract_sha256"] = hashlib.sha256(sealed.read_bytes()).hexdigest()
                value["statement_alignment"] = {
                    "standard": "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1",
                    "sealed_statement": {"filename": sealed.name, "sha256": hashlib.sha256(sealed.read_bytes()).hexdigest()},
                    "receipt": {"filename": receipt.name, "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()},
                }
                paths[0].write_text(json.dumps(value))
                def must_not_send(*args):
                    self.fail("forged context PASS reached remote transport")
                with self.assertRaisesRegex(VerificationError, "frozen-context comparison failed"):
                    verify(request_path=paths[0], formal_statement_path=paths[1], candidate_path=paths[2],
                           output_path=paths[3], key=paths[4], transport=must_not_send)
                self.assertFalse(paths[3].exists())


    def test_contradictory_runtime_observation_preserves_raw_hold_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = self.fixture(Path(directory), "theorem main_result : True := by trivial\ntheorem witness : True := by trivial\n")
            def accepted_with_bad_observations(payload, host, key, timeout):
                return 0, {"type": "verification-ok", "project": "viridis-lean-4.28", "requestId": "fixture-job",
                    "theoremNames": ["V.main_result", "V.witness"],
                    "output": "Nanoda kernel accepts the solution\nLean default kernel accepts the solution\nYour solution is okay!",
                    "executionEvidence": {"standard": "forged", "status": "OBSERVED_PARTIAL"}}
            result = verify(request_path=paths[0], formal_statement_path=paths[1], candidate_path=paths[2],
                output_path=paths[3], key=paths[4], transport=accepted_with_bad_observations)
            self.assertEqual(result["status"], "HOLD")
            self.assertEqual(result["runtime_observation_assessment"]["status"], "INVALID_OBSERVATION")
            self.assertIn("executionEvidence", result["provider_response"])


if __name__ == "__main__":
    unittest.main()
