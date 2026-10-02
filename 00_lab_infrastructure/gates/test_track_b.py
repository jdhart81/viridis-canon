"""Track-B preparation tests; no proof transport or Lean execution."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import static_pregate
import track_b


CLEAN = """import Mathlib

theorem addition_identity (x : Nat) : x + 0 = x := by
  simpa

theorem positive_witness : ∃ x : Nat, x > 0 := by
  use 1
  decide
"""


def fixture_pdf(_lines):
    # A controlled byte fixture, never presented as an actual Methods Note.
    return b"%PDF-1.4\n% unit-test fixture only\n%%EOF\n"


class TrackBPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "canonical"
        pipeline = self.root / "RESEARCH_PIPELINE_v2"
        pipeline.mkdir(parents=True)
        helper = Path(__file__).parent / "fixtures/track_b_engine3_align_challenge.py"
        shutil.copyfile(helper, pipeline / "engine3_align_challenge.py")
        for name in ("comparator_cloud_lean_verifier.py", "issue_lean_zero_sorry_certificate.py"):
            (pipeline / name).write_text("# command-plan path fixture; never imported or executed\n")
        self.source = self.root / "foundation.lean"
        self.source.write_text(CLEAN)
        self.binding = self.root / "claim_binding.json"
        self.claims = {"claims": [{"english_claim": "Adding zero leaves a natural number unchanged.",
                                   "lean_theorem": "addition_identity", "nonvacuity_obligation": "positive_witness",
                                   "model_fidelity": {"defined": ["Nat", "addition"], "empirically_identified": []},
                                   "disclaimer": track_b.DISCLAIMER}]}
        self.binding.write_text(json.dumps(self.claims))
        self.out = self.base / "envelopes"

    def prepare(self, **extra):
        arguments = {"source": self.source, "claim_binding": self.binding, "run_id": "Run-900",
                     "root": self.root, "out": self.out}
        arguments.update(extra)
        return track_b.prepare(**arguments)

    def test_report_only_never_writes_or_generates_pdf(self):
        def unavailable_pdf(_lines):
            raise AssertionError("report-only should not invoke the PDF writer")
        report = self.prepare(pdf_writer=unavailable_pdf)
        self.assertEqual(report["mode"], "REPORT_ONLY")
        self.assertEqual(report["status"], "DEBT")
        self.assertFalse(report["certified"])
        self.assertFalse(report["transport_performed"])
        self.assertFalse(self.out.exists())
        self.assertEqual(report["command_plan"][0][1], str(self.root / "RESEARCH_PIPELINE_v2/comparator_cloud_lean_verifier.py"))
        self.assertEqual(report, self.prepare(pdf_writer=unavailable_pdf))

    def test_envelope_reuses_alignment_and_exact_sealed_inputs_without_certifying(self):
        original = self.source.read_bytes()
        report = self.prepare(enforce=True, pdf_writer=fixture_pdf)
        directory = self.out / "Run-900"
        request = json.loads((directory / "ENGINE3_VERIFICATION_REQUEST.json").read_text())
        self.assertEqual(report["status"], "DEBT")
        self.assertFalse(report["certified"])
        self.assertEqual(report["preparation_status"], "FROZEN_PENDING_COMPARATOR")
        self.assertTrue(track_b.SEALED_NAMES.issubset(request["input_sha256"]))
        for name, expected in request["input_sha256"].items():
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected)
        self.assertEqual((directory / "VERIFICATION_CANDIDATE.lean").read_bytes(), original)
        self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(request["nonvacuity_obligations"], ["positive_witness"])
        self.assertEqual(request["expected_theorem_names"], ["addition_identity", "positive_witness"])
        self.assertEqual(request["permitted_axioms"], track_b.PERMITTED_AXIOMS)
        self.assertFalse(request["local_lean_fallback_authorized"])
        align, _ = track_b.load_alignment_helper(self.root)
        challenge, _ = align((directory / "VERIFICATION_STATEMENT.lean").read_text(),
                             (directory / "VERIFICATION_CANDIDATE.lean").read_text(), request["expected_theorem_names"])
        self.assertEqual(challenge, (directory / "VERIFICATION_CHALLENGE_ALIGNED.lean").read_text())
        self.assertIn(track_b.DISCLAIMER, (directory / "SEALED_paper.tex").read_text())
        self.assertIn(track_b.CONJECTURE, (directory / "SEALED_paper.tex").read_text())
        inventory = json.loads((directory / "SEALED_CLAIM_INVENTORY.json").read_text())
        self.assertEqual(inventory["claims"][0]["evidence_class"], "FORMAL_TARGET")
        self.assertEqual(inventory["claims"][0]["empirical_content"]["evidence_class"], "DEFERRED")
        self.assertFalse((directory / "LEAN_ZERO_SORRY_CERTIFICATE.json").exists())

    def test_existing_envelope_is_preserved(self):
        self.prepare(enforce=True, pdf_writer=fixture_pdf)
        before = {p.name: p.read_bytes() for p in (self.out / "Run-900").iterdir()}
        with self.assertRaisesRegex(track_b.PreparationError, "immutable destination"):
            self.prepare(enforce=True, pdf_writer=fixture_pdf)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.out / "Run-900").iterdir()})

    def test_unsound_and_hole_bearing_sources_are_quarantined_before_pdf(self):
        for addition in ("axiom forbidden : False\n", "theorem hole : 0 = 0 := by\n  sorry\n",
                         "theorem vacuous : True := by\n  trivial\n"):
            with self.subTest(addition=addition):
                self.source.write_text(CLEAN + addition)
                with self.assertRaisesRegex(track_b.PreparationError, "static failure"):
                    self.prepare(enforce=True, pdf_writer=lambda _: self.fail("PDF cannot precede quarantine"))
                self.assertFalse(self.out.exists())

    def test_reserved_ids_are_exact(self):
        for value in ("Run-899", "Run-1000", "900", "Run-900-extra", "Run-9١١"):
            with self.subTest(value=value), self.assertRaisesRegex(track_b.PreparationError, "reserved ID"):
                self.prepare(run_id=value)

    def test_missing_witness_fidelity_and_disclaimer_hold(self):
        for key in ("nonvacuity_obligation", "model_fidelity", "disclaimer"):
            modified = json.loads(json.dumps(self.claims))
            del modified["claims"][0][key]
            self.binding.write_text(json.dumps(modified))
            with self.subTest(key=key), self.assertRaises(track_b.PreparationError):
                self.prepare()
        self.assertFalse(self.out.exists())

    def test_missing_or_multiple_declarations_do_not_invent_witnesses(self):
        modified = json.loads(json.dumps(self.claims))
        modified["claims"][0]["nonvacuity_obligation"] = "missing_witness"
        self.binding.write_text(json.dumps(modified))
        with self.assertRaisesRegex(track_b.PreparationError, "one source declaration"):
            self.prepare()

    def test_source_hash_change_fails_before_output(self):
        def mutate_after_scan(path):
            scanned = static_pregate.scan(path)
            path.write_text(CLEAN + "\n-- changed after scan\n")
            return scanned
        with self.assertRaisesRegex(track_b.PreparationError, "changed before freezing"):
            self.prepare(enforce=True, pdf_writer=fixture_pdf, scanner=mutate_after_scan)
        self.assertFalse(self.out.exists())

    def test_missing_pdf_dependency_is_hold_without_partial_envelope(self):
        def missing(_lines):
            raise track_b.PreparationError("reportlab unavailable")
        with self.assertRaisesRegex(track_b.PreparationError, "reportlab unavailable"):
            self.prepare(enforce=True, pdf_writer=missing)
        self.assertFalse(self.out.exists())

    def test_source_outside_root_and_symlink_are_refused(self):
        outside = self.base / "outside.lean"
        outside.write_text(CLEAN)
        with self.assertRaisesRegex(track_b.PreparationError, "canonical root"):
            self.prepare(source=outside)
        link = self.root / "link.lean"
        link.symlink_to(self.source)
        with self.assertRaisesRegex(track_b.PreparationError, "symlink"):
            self.prepare(source=link)

    def test_recorded_certificate_and_reserved_run_collision_are_not_promoted(self):
        store = self.root / "RESEARCH_PIPELINE_v2/lean_certificates/Run-116"
        store.mkdir(parents=True)
        (store / "LEAN_ZERO_SORRY_CERTIFICATE.json").write_text(json.dumps({
            "bindings": {"candidate_proof": {"sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}}}))
        with self.assertRaisesRegex(track_b.PreparationError, "recorded certificate"):
            self.prepare()
        shutil.rmtree(store)
        (store.parent / "Run-900").mkdir()
        with self.assertRaisesRegex(track_b.PreparationError, "reserved run ID already exists"):
            self.prepare()

    def test_term_proof_not_supported_by_existing_helper_fails_closed(self):
        self.source.write_text(CLEAN.replace("  simpa", "  simpa").replace("x + 0 = x := by\n  simpa", "x + 0 = x := Nat.add_zero x"))
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
