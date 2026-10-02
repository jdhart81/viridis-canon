"""Independent review regressions; fixtures and mutations stay in temporary trees."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
GATES = REPO / '00_lab_infrastructure/gates'
sys.path.insert(0, str(GATES))
sys.path.insert(0, str(REPO / 'scripts'))
import certificate_inspection as inspection
import corpus_ledger
import claim_binding
import static_pregate
import test_track_b as track_b_tests
import test_publication_coverage_gate as publication_tests
import generate_public_index

CANONICAL = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentCoverageReview(unittest.TestCase):
    def source_certificate(self):
        cert = CANONICAL / 'RESEARCH_PIPELINE_v2/lean_certificates/Run-142/LEAN_ZERO_SORRY_CERTIFICATE.json'
        if not cert.is_file():
            self.skipTest('private issued certificate fixture unavailable')
        original = json.loads(cert.read_text())
        def resolve(value):
            if isinstance(value, dict):
                if 'path' in value and 'sha256' in value:
                    value['path'] = str(inspection.resolve_binding(value, CANONICAL))
                else:
                    for child in value.values():
                        resolve(child)
        resolve(original['bindings'])
        return original, inspection.pipeline_modules(CANONICAL)

    def test_real_receipt_cannot_certify_swapped_candidate(self):
        cert, modules = self.source_certificate()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'RESEARCH_PIPELINE_v2/lean_certificates/Run-142'
            directory.mkdir(parents=True)
            substitute = directory / 'VERIFICATION_CANDIDATE.lean'
            substitute.write_text('theorem unrelated_result (x : Nat) : x = x := rfl\n')
            cert['bindings']['candidate_proof'] = {'path': str(substitute), 'sha256': sha(substitute)}
            path = directory / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
            path.write_text(json.dumps(cert))
            with patch.object(inspection, 'pipeline_modules', return_value=modules):
                result = inspection.inspect_certificate(path, root)
            self.assertFalse(result['valid'], result)

    def test_real_receipt_cannot_certify_swapped_sealed_paper(self):
        cert, modules = self.source_certificate()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'RESEARCH_PIPELINE_v2/lean_certificates/Run-142'
            directory.mkdir(parents=True)
            substitute = directory / 'SEALED_paper.tex'
            substitute.write_text('An unrelated manuscript, not the sealed Comparator request paper.\n')
            cert['bindings']['sealed_paper_inputs']['SEALED_paper.tex'] = {'path': str(substitute), 'sha256': sha(substitute)}
            path = directory / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
            path.write_text(json.dumps(cert))
            with patch.object(inspection, 'pipeline_modules', return_value=modules):
                result = inspection.inspect_certificate(path, root)
            self.assertFalse(result['valid'], result)

    def test_real_receipt_cannot_move_certification_to_another_run(self):
        cert, modules = self.source_certificate()
        cert['run_id'] = 'Run-180'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / 'RESEARCH_PIPELINE_v2/lean_certificates/Run-180'
            directory.mkdir(parents=True)
            path = directory / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
            path.write_text(json.dumps(cert))
            with patch.object(inspection, 'pipeline_modules', return_value=modules):
                result = inspection.inspect_certificate(path, root)
            self.assertFalse(result['valid'], result)

    def test_missing_paper_root_is_unavailable_not_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            certs = root / 'certs'
            certs.mkdir()
            with self.assertRaises((ValueError, FileNotFoundError)):
                corpus_ledger.build(root, certs)

    def test_invalid_cli_input_emits_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = subprocess.run([sys.executable, str(GATES/'corpus_ledger.py'), 'build',
                '--root', str(base/'missing-root'), '--out', str(base/'ledger.json')],
                capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(json.loads(result.stdout)['status'], 'HOLD')
            self.assertFalse((base/'ledger.json').exists())

    def test_prepared_inventory_matches_claim_gate_contract(self):
        fixture = track_b_tests.TrackBPreparationTests(methodName='test_report_only_never_writes_or_generates_pdf')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.prepare(enforce=True, pdf_writer=track_b_tests.fixture_pdf)
        directory = fixture.out / 'Run-900'
        inventory = directory / 'SEALED_CLAIM_INVENTORY.json'
        inspected = {'sealed_paper_inputs': {'SEALED_CLAIM_INVENTORY.json': {'path': str(inventory), 'sha256': sha(inventory)}}}
        outcomes = [{**claim, 'status': 'PASS'} for claim in fixture.claims['claims']]
        result = claim_binding._check_inventory(inspected, {'tree_root': str(fixture.root.parent)}, outcomes, ['addition_identity','positive_witness'])
        self.assertEqual(result, [])

    def test_parenthesized_and_multiline_vacuity_fail_static(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'candidate.lean'
            for source in ('theorem vacuous : (True) := trivial\n',
                           'theorem vacuous : 0 = 0 ↔ (True) := by simp\n',
                           'theorem impossible (h : (False)) : 0 = 1 := False.elim h\n',
                           'theorem vacuous : ∃ x : Nat,\n  True := ⟨0, trivial⟩\n'):
                with self.subTest(source=source):
                    path.write_text(source)
                    self.assertFalse(static_pregate.scan(path)['static_pass'])

    def test_index_does_not_assert_current_certified_after_byte_drift(self):
        fixture = publication_tests.PublicationCoverageGateTests(methodName='test_certified_bound_claim_positive')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.candidate.write_bytes(fixture.candidate.read_bytes() + b' ')
        try:
            rendered = generate_public_index.render_index(fixture.ledger, inspector=fixture.inspected_fixture)
        except (ValueError, RuntimeError):
            return  # Entire index HOLD is a valid fail-closed response.
        descriptions = json.loads(rendered['ZENODO_DESCRIPTIONS.json'])
        self.assertNotEqual(descriptions['artifacts'][0]['proof_status'], 'CERTIFIED')
        if '| CERTIFIED | 0 | 1 |' in rendered['README.md']:
            self.assertIn('Ledger snapshot coverage', rendered['README.md'])
            self.assertIn('Current proof statuses below are re-inspected', rendered['README.md'])


if __name__ == '__main__':
    unittest.main()
