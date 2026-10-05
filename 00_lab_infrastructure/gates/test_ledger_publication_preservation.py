"""Approved release registrations survive fresh scans without trust inheritance."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from corpus_ledger import (build, preserve_publication_registrations,
                           validate_uncertified_readback, write_guarded_ledger)
from publication_gate import evaluate_publication
from release_packet import LABEL
import test_publication_coverage_gate as fixtures

digest = fixtures.digest


class LedgerPublicationPreservationTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.PublicationCoverageGateTests(methodName='test_certified_bound_claim_positive')
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.root = self.f.root
        self.release = self.root / 'reviewed release'
        shutil.copytree(self.f.run, self.release)
        self.entry = {**self.f.entry, 'id':'publication:reviewed', 'kind':'PUBLICATION', 'entity_type':'PUBLICATION',
                      'run_id':'Run-142', 'path':'reviewed release', 'certificate_sha256':digest(self.f.cert)}
        self.previous = {**self.f.ledger, 'publication_entities':[self.entry]}
        self.fresh = copy.deepcopy(self.f.ledger)
        self.cert_root = self.root / 'cert-store'
        fresh_cert = self.cert_root / 'Run-142/LEAN_ZERO_SORRY_CERTIFICATE.json'
        fresh_cert.parent.mkdir(parents=True)
        fresh_cert.write_bytes(self.f.cert.read_bytes())

    def inspected(self, path, root):
        result = self.f.inspected_fixture(path, root)
        result.update(path=str(path), run_id='Run-142', candidate_sha256=digest(self.f.candidate))
        return result

    def preserve(self, previous=None):
        with patch('corpus_ledger.inspect_certificate', side_effect=self.inspected):
            return preserve_publication_registrations(copy.deepcopy(self.fresh), self.previous if previous is None else previous)

    def test_exact_approval_and_binding_are_revalidated_and_preserved(self):
        ledger = self.preserve()
        entry = ledger['publication_entities'][0]
        self.assertEqual(entry['approved_publication_binding_reviews'], self.entry['approved_publication_binding_reviews'])
        self.assertEqual(entry['status'], 'CERTIFIED')
        self.assertEqual(entry['publication_binding_status'], 'PUBLICATION_BOUND')
        self.assertTrue(entry['registration_revalidated'])
        self.assertEqual(entry['publication_registration_status'], 'PASS')
        self.assertTrue(entry['enforcement_acceptable'])
        self.assertEqual(len(ledger['run_entities']), 1)

    def test_build_reads_ssot_and_keeps_publication_entities_in_separate_denominator(self):
        authoritative = self.root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        authoritative.parent.mkdir()
        authoritative.write_text(json.dumps(self.previous))
        with patch('corpus_ledger.inspect_certificate', side_effect=self.inspected), patch('corpus_ledger.flow', return_value={'state':'CERTIFIED'}):
            ledger = build(self.root, self.cert_root, self.f.generation_root)
        self.assertEqual(len(ledger['publication_entities']), 1)
        self.assertEqual(ledger['publication_entities'][0]['publication_binding_status'], 'PUBLICATION_BOUND')
        self.assertEqual(sum(ledger['run_counts'].values()), 1)
        self.assertEqual(ledger['receipt_era']['total'], 1)
        self.assertEqual(json.loads(authoritative.read_text()), self.previous)

    def test_no_registration_is_inferred_from_existing_certificate_and_receipt(self):
        previous = {**self.previous, 'publication_entities':[]}
        self.assertEqual(self.preserve(previous)['publication_entities'], [])

    def test_premise_cutover_is_retained_without_rewriting_historical_registrations(self):
        self.previous['premise_declaration_cutover_run'] = 'Run-187'
        ledger = self.preserve()
        self.assertEqual(ledger['premise_declaration_cutover_run'], 'Run-187')
        self.assertEqual(ledger['publication_entities'][0]['publication_registration_status'], 'PASS')

    def test_invalid_premise_cutover_is_not_silently_dropped_on_rebuild(self):
        for cutover in ('Run-0187', 'Run-0', 'Run-900', 187, True):
            with self.subTest(cutover=cutover):
                previous = {**self.previous, 'premise_declaration_cutover_run':cutover}
                with self.assertRaisesRegex(ValueError, 'cutover'):
                    self.preserve(previous)

    def test_missing_approved_hash_holds_instead_of_copying_run_approval(self):
        previous = copy.deepcopy(self.previous)
        del previous['publication_entities'][0]['approved_publication_binding_reviews']
        entry = self.preserve(previous)['publication_entities'][0]
        self.assertEqual(entry['status'], 'DEBT')
        self.assertFalse(entry['certificate_valid'])
        self.assertNotIn('approved_publication_binding_reviews', entry)

    def test_one_byte_final_manuscript_change_keeps_registration_visible_as_hold(self):
        (self.release / 'SEALED_paper.tex').write_text(self.f.paper.read_text() + ' ')
        ledger = self.preserve()
        entry = ledger['publication_entities'][0]
        self.assertEqual(entry['status'], 'DEBT')
        self.assertEqual(entry['publication_binding_status'], 'HOLD')
        self.assertEqual(entry['approved_publication_binding_reviews'], self.entry['approved_publication_binding_reviews'])
        self.assertEqual(ledger['publication_holds'][0]['id'], self.entry['id'])

    def test_certificate_hash_change_is_not_a_valid_run_join_substitute(self):
        self.f.cert.write_text(self.f.cert.read_text() + ' ')
        entry = self.preserve()['publication_entities'][0]
        self.assertEqual(entry['status'], 'DEBT')
        self.assertIn('SHA-256', str(entry['reasons']))

    def test_other_review_hash_does_not_self_approve_receipt(self):
        previous = copy.deepcopy(self.previous)
        previous['publication_entities'][0]['approved_publication_binding_reviews'] = ['0' * 64]
        entry = self.preserve(previous)['publication_entities'][0]
        self.assertEqual(entry['status'], 'DEBT')
        self.assertIn('ledger approval', str(entry['reasons']))

    def test_run_join_drift_holds_the_release(self):
        previous = copy.deepcopy(self.previous)
        previous['publication_entities'][0]['run_id'] = 'Run-900'
        self.assertEqual(self.preserve(previous)['publication_entities'][0]['status'], 'DEBT')

    def test_previously_held_registration_never_auto_upgrades(self):
        previous = copy.deepcopy(self.previous)
        previous['publication_entities'][0].update(status='DEBT', certificate_valid=False)
        self.assertEqual(self.preserve(previous)['publication_entities'][0]['status'], 'DEBT')

    def test_malformed_table_duplicate_identity_and_wrong_root_fail_closed(self):
        cases = [{**self.previous, 'publication_entities':{}},
                 {**self.previous, 'publication_entities':[self.entry, self.entry]},
                 {**self.previous, 'tree_root':str(self.root.parent)}]
        for previous in cases:
            with self.subTest(previous=previous.get('tree_root')):
                with self.assertRaises(ValueError):
                    self.preserve(previous)

    def banner_proof(self, *, description=None):
        rid = '22236409'
        self.previous['publication_entities'][0]['doi'] = '10.5281/zenodo.' + rid
        path = self.root / 'reports/public-readback.json'
        path.parent.mkdir(exist_ok=True)
        receipt = {'method':'GET', 'url':'https://zenodo.org/api/records/' + rid,
                   'environment':'zenodo.org', 'http_status':200,
                   'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'response_sha256':'a' * 64,
                   'response':{'id':rid, 'is_published':True,
                               'metadata':{'description':description if description is not None else '<p><strong>' + LABEL + '</strong></p><p>Historical description</p>'}}}
        path.write_text(json.dumps(receipt))
        proof = {'authenticated':True, 'record_id':rid, 'receipt_path':str(path.relative_to(self.root)),
                 'receipt_sha256':digest(path), 'response_sha256':receipt['response_sha256']}
        self.previous['publication_entities'][0]['public_uncertified_readback'] = proof
        return path, receipt, proof

    def test_no_claim_map_is_explicit_hold_and_not_whole_verified(self):
        (self.release / 'claim_binding.json').unlink()
        ledger = self.preserve()
        entry = ledger['publication_entities'][0]
        self.assertEqual(entry['status'], 'CERTIFIED')  # Proof qualification only.
        self.assertEqual(entry['publication_registration_status'], 'HOLD_NO_CLAIM_MAP')
        self.assertFalse(entry['enforcement_acceptable'])
        self.assertFalse(ledger['publication_registration_enforcement_acceptable'])
        with patch('corpus_ledger.inspect_certificate', side_effect=self.inspected):
            result = evaluate_publication(self.release, ledger, entity_id=entry['id'], inspector=self.inspected)
        self.assertEqual(result['status'], 'HOLD')
        self.assertEqual(result['verification_status'], 'UNCERTIFIED')

    def test_no_claim_map_with_exact_authenticated_public_banner_is_acceptable_hold(self):
        (self.release / 'claim_binding.json').unlink()
        self.banner_proof()
        ledger = self.preserve()
        entry = ledger['publication_entities'][0]
        self.assertEqual(entry['publication_registration_status'], 'HOLD_NO_CLAIM_MAP')
        self.assertTrue(entry['enforcement_acceptable'])
        self.assertTrue(ledger['publication_registration_enforcement_acceptable'])
        self.assertEqual(entry['public_uncertified_banner']['status'], 'PUBLIC_UNCERTIFIED_BANNER_READBACK_PASS')
        self.assertEqual(ledger['publication_registration_defects'], [])

    def test_no_claim_map_registration_survives_fresh_scan_without_invented_map(self):
        (self.release / 'claim_binding.json').unlink()
        self.banner_proof()
        first = self.preserve()
        with patch('corpus_ledger.inspect_certificate', side_effect=self.inspected), patch('corpus_ledger.flow', return_value={'state':'CERTIFIED'}):
            second = build(self.root, self.cert_root, self.f.generation_root, previous_ledger=first)
        entry = second['publication_entities'][0]
        self.assertEqual(entry['publication_registration_status'], 'HOLD_NO_CLAIM_MAP')
        self.assertTrue(entry['enforcement_acceptable'])
        self.assertEqual(entry['public_uncertified_readback'], first['publication_entities'][0]['public_uncertified_readback'])
        self.assertFalse((self.release / 'claim_binding.json').exists())

    def test_absent_historical_duplicated_or_wrong_banner_is_not_acceptable(self):
        (self.release / 'claim_binding.json').unlink()
        for text in ('Certified mathematics', '<p>Historical description</p><p>' + LABEL + '</p>', LABEL + LABEL,
                     LABEL.replace('UNCERTIFIED', 'CONJECTURE')):
            with self.subTest(description=text):
                self.banner_proof(description=text)
                entry = self.preserve()['publication_entities'][0]
                self.assertEqual(entry['publication_registration_status'], 'HOLD_NO_CLAIM_MAP')
                self.assertFalse(entry['enforcement_acceptable'])

    def test_public_receipt_hash_identity_and_authenticated_boundary_are_required(self):
        (self.release / 'claim_binding.json').unlink()
        for change in ('receipt_hash', 'response_hash', 'record_id', 'authenticated', 'method', 'published', 'endpoint'):
            with self.subTest(change=change):
                path, receipt, proof = self.banner_proof()
                if change == 'receipt_hash':proof['receipt_sha256'] = '0' * 64
                elif change == 'response_hash':proof['response_sha256'] = '0' * 64
                elif change == 'record_id':receipt['response']['id'] = '22236410'
                elif change == 'authenticated':proof['authenticated'] = False
                elif change == 'method':receipt['method'] = 'POST'
                elif change == 'published':receipt['response']['is_published'] = False
                else:receipt['url'] = 'https://zenodo.org/api/records/22236409/draft'
                if change in ('record_id', 'method', 'published', 'endpoint'):
                    path.write_text(json.dumps(receipt));proof['receipt_sha256'] = digest(path)
                entry = self.preserve()['publication_entities'][0]
                self.assertFalse(entry['enforcement_acceptable'])

    def test_malformed_claim_map_is_not_no_claim_map_or_acceptable(self):
        (self.release / 'claim_binding.json').write_text('not JSON')
        self.banner_proof()
        entry = self.preserve()['publication_entities'][0]
        self.assertEqual(entry['publication_registration_status'], 'HOLD')
        self.assertFalse(entry['enforcement_acceptable'])

    def test_guarded_writer_replaces_exact_predecessor_and_reads_back(self):
        path = self.root / 'ledger.json';path.write_text('{"before":true}\n')
        before = digest(path)
        after = write_guarded_ledger(path, {'after':True}, before)
        self.assertEqual(after, digest(path))
        self.assertEqual(json.loads(path.read_text()), {'after':True})
        self.assertEqual(list(self.root.glob('.ledger.json.*')), [])

    def test_guarded_writer_refuses_changed_predecessor_and_symlink(self):
        path = self.root / 'ledger.json';path.write_text('{"before":true}\n')
        before = digest(path);path.write_text('{"concurrent":true}\n')
        with self.assertRaisesRegex(ValueError, 'concurrent'):
            write_guarded_ledger(path, {'after':True}, before)
        self.assertEqual(json.loads(path.read_text()), {'concurrent':True})
        link = self.root / 'ledger-link.json';link.symlink_to(path)
        with self.assertRaises(ValueError):write_guarded_ledger(link, {'after':True}, digest(path))

    def test_guarded_writer_refuses_concurrent_change_before_replace(self):
        path = self.root / 'ledger.json';path.write_text('{"before":true}\n')
        before = digest(path)
        with patch('corpus_ledger.os.fsync', side_effect=lambda fd:path.write_text('{"concurrent":true}\n')):
            with self.assertRaisesRegex(ValueError, 'concurrent'):
                write_guarded_ledger(path, {'after':True}, before)
        self.assertEqual(json.loads(path.read_text()), {'concurrent':True})
        self.assertEqual(list(self.root.glob('.ledger.json.*')), [])


if __name__ == '__main__':
    unittest.main()
