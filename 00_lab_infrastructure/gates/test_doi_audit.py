import json
import tempfile
import unittest
from pathlib import Path

import doi_audit as audit


class DOIAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = self.root / 'science-engine/09_zenodo/ZENODO_RECORDS.json'
        self.registry.parent.mkdir(parents=True)
        self.registry.write_text(json.dumps({'last_reviewed': '2026-06-01', 'records': []}))
        self.deposits = self.root / '_ZENODO_DEPOSITS'
        self.deposits.mkdir()
        self.runs = self.root / 'science-engine/07_nightly_engine/compound research papers'
        self.runs.mkdir(parents=True)
        self.ledger = {'certificates': [], 'run_entities': []}

    def deposit(self, name='2026-09-01_test', published=True, certified=False):
        p = self.deposits / name
        p.mkdir(parents=True)
        (p / 'zenodo_metadata.json').write_text(json.dumps({'metadata': {'title': 'A Defined Model Result', 'prereserve_doi': {'doi': '10.5281/zenodo.9000'}}}))
        if published:
            (p / 'PUBLISHED_DOI.txt').write_text('10.5281/zenodo.9001\n')
        if certified:
            candidate = p / 'VERIFICATION_CANDIDATE.lean'
            statement = p / 'VERIFICATION_STATEMENT.lean'
            candidate.write_text('theorem model_result : 1 = 1 := rfl\n')
            statement.write_text('theorem model_result : 1 = 1 := by sorry\n')
            (p / 'paper.tex').write_text('\\title{A Defined Model Result}\n')
            (p / 'paper.pdf').write_bytes(b'%PDF fixture\n')
            bindings = {'candidate_proof': {'sha256': audit.sha256(candidate)},
                        'formal_statement': {'sha256': audit.sha256(statement)},
                        'sealed_paper_inputs': {'SEALED_paper.tex': {'sha256': audit.sha256(p / 'paper.tex')},
                                                'SEALED_paper.pdf': {'sha256': audit.sha256(p / 'paper.pdf')}}}
            cert = p / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
            cert.write_text(json.dumps({'run_id': 'Run-178', 'bindings': bindings}))
            store = self.root / 'certs/Run-178/LEAN_ZERO_SORRY_CERTIFICATE.json'
            store.parent.mkdir(parents=True)
            store.write_bytes(cert.read_bytes())
            self.ledger['certificates'].append({'path': str(store), 'valid': True, 'run_id': 'Run-178'})
        return p

    def build(self):
        return audit.build_audit(self.root, self.ledger, certificate_assessor=lambda p, r: {'valid': False, 'reasons': ['test consumer rejected']})

    def test_versions_exclude_concepts_and_citations(self):
        values, excluded = audit.published_dois('Concept DOI: 10.5281/zenodo.12\n  v1: 10.5281/zenodo.13\n  v2: 10.5281/zenodo.14\nisDerivedFrom: 10.5281/zenodo.15\n')
        self.assertEqual(values, ['10.5281/zenodo.13', '10.5281/zenodo.14'])
        self.assertEqual(excluded, ['10.5281/zenodo.12', '10.5281/zenodo.15'])

    def test_reserved_draft_is_not_publication(self):
        self.deposit(published=False)
        self.assertEqual(self.build()['counts']['published_dois'], 0)

    def test_exact_artifact_binding_passes(self):
        self.deposit(certified=True)
        result = self.build()
        self.assertEqual(result['counts']['published_artifact_hash_bound'], 1)
        self.assertTrue(result['published_records'][0]['proof_certificate_present_valid'])

    def test_tampered_proof_is_hold(self):
        p = self.deposit(certified=True)
        with (p / 'VERIFICATION_CANDIDATE.lean').open('a') as stream:
            stream.write(' ')
        result = self.build()['published_records'][0]
        self.assertFalse(result['proof_certificate_present_valid'])
        self.assertFalse(result['publication_artifact_bound'])

    def test_manuscript_drift_keeps_separate_proof_status(self):
        p = self.deposit(certified=True)
        with (p / 'paper.tex').open('a') as stream:
            stream.write('edited publication disclaimer\n')
        result = self.build()['published_records'][0]
        self.assertTrue(result['proof_certificate_present_valid'])
        self.assertFalse(result['publication_artifact_bound'])
        self.assertEqual(result['status'], 'PROOF_CERTIFIED_PUBLICATION_BINDING_UNRESOLVED')

    def test_title_join_cannot_transfer_certificate(self):
        self.deposit(certified=True)
        self.registry.write_text(json.dumps({'records': [{'doi': '10.5281/zenodo.9002', 'title': 'A Defined Model Result', 'status': 'preprint'}]}))
        result = {row['doi']: row for row in self.build()['published_records']}
        self.assertFalse(result['10.5281/zenodo.9002']['certificate_valid'])
        self.assertTrue(result['10.5281/zenodo.9001']['certificate_valid'])

    def test_receipt_consumer_error_is_hold(self):
        p = self.deposit(certified=True)
        self.ledger['certificates'] = []
        def broken(path, root):
            raise TimeoutError('receipt inspection unavailable')
        result = audit.build_audit(self.root, self.ledger, certificate_assessor=broken)['published_records'][0]
        self.assertFalse(result['certificate_valid'])
        self.assertIn('failed closed', result['reasons'][0])

    def test_nested_repair_version_receipt_included(self):
        self.deposit(name='REPAIR_STAGING/amended/Result')
        result = self.build()
        self.assertEqual(result['counts']['published_dois'], 1)
        self.assertEqual(result['counts']['nested_publication_receipt_directories'], 1)

    def test_papertitle_join_and_repeat_are_deterministic(self):
        self.deposit()
        run = self.runs / 'Run-034_model_result'
        run.mkdir()
        (run / 'paper.tex').write_text('\\papertitle{A Defined Model Result}\n')
        first, second = self.build(), self.build()
        self.assertEqual(first, second)
        self.assertEqual(first['prereceipt_run_entities'][0]['published_dois'], ['10.5281/zenodo.9001'])


if __name__ == '__main__':
    unittest.main()
