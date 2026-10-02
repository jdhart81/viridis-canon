import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from corpus_ledger import PRIORITY, build, discover, partition_status, file_status
from static_pregate import scan
from certificate_inspection import resolve_binding, inspect_certificate


class CoverageTests(unittest.TestCase):
    def test_status_partition_priority(self):
        self.assertEqual(partition_status(*PRIORITY), 'UNSOUND')
        self.assertEqual(partition_status('HAS_SORRY','DEBT'), 'HAS_SORRY')
        self.assertEqual(partition_status('NO_FORMALIZATION','DEBT'), 'DEBT')
        self.assertEqual(partition_status('CERTIFIED','CLEAN_UNCERTIFIED'), 'CLEAN_UNCERTIFIED')

    def test_pointer_exclusion_and_synthesis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'certs').mkdir()
            papers=root/'science-engine/07_nightly_engine/compound research papers'
            for name in ('Run-001_test', 'Run-META-001_canon-synthesis','_LATEST'):
                (papers/name).mkdir(parents=True)
            (papers/'_LATEST/stale.lean').write_text('axiom wrong : False')
            ledger=build(root,root/'certs')
            self.assertEqual(ledger['file_entities'],[])
            self.assertEqual(ledger['run_counts']['NO_FORMALIZATION'],1)
            self.assertEqual(ledger['synthesis_count'],1)
            self.assertEqual(next(r for r in ledger['run_entities'] if r['kind']=='SYNTHESIS')['id'],'Run-META-001_canon-synthesis')

    def test_hash_and_relative_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            proof=root/'RESEARCH_PIPELINE_v2/lean_certificates/Run-142/candidate.lean'
            proof.parent.mkdir(parents=True)
            proof.write_text('theorem x : 1 = 1 := rfl')
            binding={'path':'lean_certificates/Run-142/candidate.lean', 'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}
            self.assertEqual(resolve_binding(binding,root),proof.resolve())
            proof.write_bytes(proof.read_bytes()+b' ')
            with self.assertRaises(ValueError): resolve_binding(binding,root)

    def test_comments_and_missing_inputs_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'candidate.lean'
            self.assertTrue(scan(path)['errors'])
            path.write_text('/- axiom sorry /- admit -/ -/\n-- sorry\ndef s := "sorry"\ntheorem x : 1 = 1 := by rfl')
            self.assertTrue(scan(path)['static_pass'])
            path.write_text('axiom bad : False\ntheorem x : True := by sorry')
            self.assertEqual(file_status(scan(path)), 'UNSOUND')
            path.write_text('theorem witness : True := by sorry')
            self.assertEqual(file_status(scan(path)), 'HAS_SORRY')

    def test_timeout_inspection_never_certifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'cert.json';path.write_text('{}')
            with patch('certificate_inspection.pipeline_modules',side_effect=TimeoutError('simulated timeout')):
                result=inspect_certificate(path,Path(tmp))
            self.assertFalse(result['valid'])
            self.assertIn('TimeoutError',result['reasons'][0])

    def test_real_regression_files(self):
        root=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
        if not root.exists():
            fixtures=Path(__file__).parent/'fixtures'
            for name in ('intelligence_bound.lean.txt','gaia.lean.txt','p_vs_np.lean.txt'):
                self.assertEqual(file_status(scan(fixtures/name)), 'UNSOUND')
            clean=[p for p in fixtures.glob('*.lean.txt') if p.name not in ('intelligence_bound.lean.txt','gaia.lean.txt','p_vs_np.lean.txt')]
            self.assertEqual(len(clean),7)
            for path in clean: self.assertTrue(scan(path)['static_pass'])
            return
        paths=[root/'00_ORIGIN/paper/Intelligence_Bound_Lean4_Proof.lean',root/'science-engine/01_foundation/intelligence_bound/Intelligence_Bound_Lean4_Proof.lean',root/'science-engine/01_foundation/intelligence_bound_full/ai_alignment_paper/proofs/Gaia_Intelligence_Theorem.lean',next((root/'science-engine/04_advanced/computation/p_vs_np').glob('*output.lean'))]
        for path in paths: self.assertEqual(file_status(scan(path)), 'UNSOUND',str(path))
        nucleus=root/'science-engine/07_nightly_engine/compound research papers/aristotle_proofs'
        self.assertEqual(len(list(nucleus.glob('*.lean'))),7)
        for path in nucleus.glob('*.lean'): self.assertTrue(scan(path)['static_pass'],str(path))


    def test_certified_real_Run142_and_tamper(self):
        root=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
        if not root.exists(): self.skipTest('private issued receipt fixture unavailable')
        path=root/'RESEARCH_PIPELINE_v2/lean_certificates/Run-142/LEAN_ZERO_SORRY_CERTIFICATE.json'
        self.assertTrue(inspect_certificate(path,root)['valid'])
        with patch('certificate_inspection.resolve_binding', side_effect=ValueError('one-byte binding mismatch')):
            self.assertFalse(inspect_certificate(path,root)['valid'])


if __name__=='__main__': unittest.main()
