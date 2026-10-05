"""Local bookkeeping tests use recorded-evidence fixtures; no Lean/SSH/HTTP."""
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import nightly_publication_intake as intake
import test_publication_coverage_gate as fixtures


class NightlyPublicationIntakeTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.PublicationCoverageGateTests(methodName='test_certified_bound_claim_positive')
        self.f.setUp(); self.addCleanup(self.f.doCleanups)
        self.root = self.f.root
        self.artifact = self.root/'RESEARCH_PIPELINE_v2/finalized_runs/Run-142'
        shutil.copytree(self.f.run, self.artifact)
        self.ledger_path = self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        self.ledger_path.write_text(json.dumps(self.f.ledger))
        self.output = self.root/'RESEARCH_PIPELINE_v2/publication_releases/Run-142/attempt-1'
        self.review_path = self.artifact/'POST_ARISTOTLE_REVIEW.json'
        self.review = {'verdict': 'pass', 'reviewer_system': 'fixture reviewer', 'reviewer_model': 'fixture model',
                       'reviewed_at_utc': '2026-01-04T00:00:00Z',
                       'independent_checks': {'review_complete': True, 'rendering_defects': 0},
                       'reviewed_evidence_sha256': {'LEAN_ZERO_SORRY_CERTIFICATE.json': intake.sha(self.f.cert),
                                                   'claim_binding.json': intake.sha(self.artifact/'claim_binding.json'),
                                                   'paper.tex': intake.sha(self.artifact/'SEALED_paper.tex')}}
        self.review_path.write_text(json.dumps(self.review))

    def inspected(self, path, root):
        result = self.f.inspected_fixture(path, root)
        result.update(run_id='Run-142', candidate_sha256=intake.sha(self.f.candidate))
        return result

    def prepare(self):
        return intake.prepare(self.root, 'Run-142', self.artifact, inspector=self.inspected, review_validator=lambda *args: None)

    def apply(self, expected=None):
        with patch('corpus_ledger.inspect_certificate', side_effect=self.inspected):
            return intake.apply(self.root, 'Run-142', self.artifact, self.output,
                                expected_ledger_sha256=expected or intake.sha(self.ledger_path),
                                inspector=self.inspected, review_validator=lambda *args: None)

    def test_read_only_plan_requires_exact_pass_and_changes_nothing(self):
        before = self.ledger_path.read_bytes()
        result = self.prepare()
        self.assertEqual(result['status'], 'READY_FOR_AUTHORIZED_REGISTRATION')
        self.assertEqual(self.ledger_path.read_bytes(), before); self.assertFalse(self.output.exists())
        self.assertFalse(result['certificate_issued']); self.assertFalse(result['local_lean_execution'])

    def test_explicit_registration_issues_consumable_binding_and_ssot_entry(self):
        result = self.apply()
        self.assertEqual(result['status'], 'PUBLICATION_BOUND_REGISTERED')
        self.assertEqual(result['publication_gate']['status'], 'PASS')
        ledger = json.loads(self.ledger_path.read_text()); entry = ledger['publication_entities'][0]
        self.assertEqual(entry['publication_binding_status'], 'PUBLICATION_BOUND')
        self.assertTrue((self.output/'PUBLICATION_BINDING.json').is_file())
        self.assertTrue((self.output/'registration_audit/corpus_ledger_before.json').is_file())
        self.assertFalse(result['zenodo_writes'])

    def test_held_review_cannot_issue_or_register(self):
        self.review['verdict'] = 'hold'; self.review_path.write_text(json.dumps(self.review))
        before = self.ledger_path.read_bytes(); result = self.apply()
        self.assertEqual(result['status'], 'HOLD'); self.assertFalse(self.output.exists())
        self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_missing_or_unreviewed_scope_map_is_hold(self):
        del self.review['reviewed_evidence_sha256']['claim_binding.json']
        self.review_path.write_text(json.dumps(self.review))
        self.assertIn('does not bind the explicit claim map', str(self.prepare()['reasons']))

    def test_one_byte_claim_map_change_is_hold(self):
        path = self.artifact/'claim_binding.json'; path.write_text(path.read_text()+' ')
        self.assertIn('does not bind the explicit claim map', str(self.prepare()['reasons']))

    def test_stale_certificate_review_is_hold(self):
        self.review['reviewed_evidence_sha256']['LEAN_ZERO_SORRY_CERTIFICATE.json'] = '0'*64
        self.review_path.write_text(json.dumps(self.review))
        self.assertIn('does not bind the current certificate', str(self.prepare()['reasons']))

    def test_missing_pdf_correspondence_is_hold(self):
        self.review['independent_checks']['review_complete'] = False
        self.review_path.write_text(json.dumps(self.review))
        self.assertIn('PDF correspondence review is incomplete', str(self.prepare()['reasons']))

    def test_model_assignment_is_not_inferred_from_theorem_name(self):
        path = self.artifact/'claim_binding.json'; obj = json.loads(path.read_text())
        obj['claims'][0]['model_fidelity'] = {'defined': [], 'empirically_identified': []}
        path.write_text(json.dumps(obj)); self.review['reviewed_evidence_sha256']['claim_binding.json'] = intake.sha(path)
        self.review_path.write_text(json.dumps(self.review))
        self.assertIn('must identify at least one model symbol', str(self.prepare()['reasons']))

    def test_unknown_sealed_class_is_not_silently_reclassified(self):
        obj = json.loads(self.f.inventory.read_text()); obj['claims'].append({'id': 'C2', 'claim': 'A model assumption.', 'evidence_class': 'ASSUMED'})
        self.f.inventory.write_text(json.dumps(obj))
        self.assertIn('unknown sealed inventory evidence_class', str(self.prepare()['reasons']))

    def test_expected_ledger_hash_prevents_racing_registration(self):
        before = self.ledger_path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'ledger changed before registration'):
            self.apply(expected='0'*64)
        self.assertFalse(self.output.exists()); self.assertEqual(self.ledger_path.read_bytes(), before)

    def test_existing_output_is_immutable(self):
        self.output.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, 'new immutable'):
            self.apply()


if __name__ == '__main__': unittest.main()


class PremiseNightlyIntakeTests(NightlyPublicationIntakeTests):
    def declare(self):
        from premise_declaration import _aligner
        f=self.f
        f.paper.write_text(r'\begin{document}\begin{abstract}INDEPENDENT: model successor ordering.\end{abstract}\end{document}')
        f.expected_paper_hash=intake.sha(f.paper)
        (self.artifact/'SEALED_paper.tex').write_bytes(f.paper.read_bytes())
        f.candidate.write_text(f.candidate.read_text().replace(':= Nat.le_succ x',':= by\n  exact Nat.le_succ x').replace(':= ⟨0, Nat.le_succ 0⟩',':= by\n  exact ⟨0, Nat.le_succ 0⟩'))
        f.expected_candidate_hash=intake.sha(f.candidate)
        formal=f.root/'formal.lean';formal.write_text(_aligner().align_challenge(f.candidate.read_text(),f.candidate.read_text(),['meaningful','meaningful_witness'])[0])
        manifest=f.root/'SEALED_RUN_MANIFEST.json';manifest.write_text(json.dumps({'foundation_basis':'INDEPENDENT'}))
        inventory=json.loads(f.inventory.read_text());inventory['foundation_basis']='INDEPENDENT';f.inventory.write_text(json.dumps(inventory))
        bound=lambda p:{'path':str(p),'sha256':intake.sha(p)}
        cert={'issued_at_utc':'2026-01-01T00:00:00Z','foundation_basis':'INDEPENDENT',
              'bindings':{'sealed_paper_inputs':{p.name:bound(p) for p in [f.paper,f.pdf,f.inventory,manifest]},'formal_statement':bound(formal),'candidate_proof':bound(f.candidate)}}
        f.cert.write_text(json.dumps(cert))
        self.review['reviewed_evidence_sha256']['LEAN_ZERO_SORRY_CERTIFICATE.json']=intake.sha(f.cert)
        self.review['reviewed_evidence_sha256']['paper.tex']=intake.sha(self.artifact/'SEALED_paper.tex')
        self.review_path.write_text(json.dumps(self.review))
        shutil.copytree(f.run,f.source,dirs_exist_ok=True)

    def test_cutover_missing_basis_holds_before_output_or_ledger_write(self):
        ledger=json.loads(self.ledger_path.read_text());ledger['premise_declaration_cutover_run']='Run-142'
        self.ledger_path.write_text(json.dumps(ledger));before=self.ledger_path.read_bytes()
        result=self.apply()
        self.assertEqual(result['status'],'HOLD');self.assertIn('INV-9 HOLD',str(result['reasons']))
        self.assertFalse(self.output.exists());self.assertEqual(self.ledger_path.read_bytes(),before)
        ledger['premise_declaration_cutover_run']='Run-143';self.ledger_path.write_text(json.dumps(ledger))
        self.assertEqual(self.prepare()['status'],'READY_FOR_AUTHORIZED_REGISTRATION')

    def test_required_new_intake_missing_fields_holds(self):
        result=intake.prepare(self.root,'Run-142',self.artifact,inspector=self.inspected,review_validator=lambda *args:None,require_premise_declaration=True)
        self.assertEqual(result['status'],'HOLD');self.assertIn('INV-9 HOLD',str(result['reasons']))

    def test_future_intake_issues_binding_and_entry_with_exact_basis(self):
        self.declare()
        with patch('corpus_ledger.inspect_certificate',side_effect=self.inspected):
            result=intake.apply(self.root,'Run-142',self.artifact,self.output,expected_ledger_sha256=intake.sha(self.ledger_path),inspector=self.inspected,review_validator=lambda *args:None,require_premise_declaration=True)
        self.assertEqual(result['status'],'PUBLICATION_BOUND_REGISTERED',result)
        self.assertEqual(result['foundation_basis'],'INDEPENDENT')
        self.assertEqual(json.loads((self.output/'PUBLICATION_BINDING.json').read_text())['foundation_basis'],'INDEPENDENT')
        self.assertEqual(json.loads(self.ledger_path.read_text())['publication_entities'][0]['foundation_basis'],'INDEPENDENT')
