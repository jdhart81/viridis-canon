"""Packaging/dispatch regressions only; fixture PASS is not science authority."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))
gates = HERE.parents[2] / 'RESEARCH_PIPELINE_v2/verification_coverage_gates'
sys.path.insert(2, str(gates if gates.is_dir() else HERE.parents[1]))
import methods_digest_registration_v3 as reg


class RegistrationV3Tests(unittest.TestCase):
    def evidence(self):
        binding = {'path': 'source.json', 'sha256': '1' * 64}
        manifest = {'standard': reg.d.STANDARD, 'uploads': [
            {'filename': n} for n in ['paper.pdf', 'paper.tex', 'metadata.json', 'METHODS_NOTES.zip',
                                     'Run-189-Paper.pdf', 'Run-190-Paper.pdf']]}
        downloads = [{'filename': n, 'binding': deepcopy(binding),
                      'url': 'https://zenodo.org/api/records/23308138/files/' + n + '/content'}
                     for n in [*[v['filename'] for v in manifest['uploads']],
                               'DIGEST_MANIFEST.json', 'PUBLICATION_BINDING.json']]
        fields = reg.EVIDENCE_FIELDS - {'standard', 'status', 'record_id', 'doi', 'downloads'}
        return {'record_id': '23308138', 'manifest': manifest, 'downloads': downloads,
                **{k: deepcopy(binding) for k in fields}}

    def test_two_note_v2_requires_all_eight_exact_downloads(self):
        value = reg.assemble_evidence(**self.evidence())
        self.assertEqual(value['standard'], reg.EVIDENCE_STANDARD)
        self.assertEqual(len(value['downloads']), 8)
        self.assertEqual(set(value), reg.EVIDENCE_FIELDS)

    def test_old_six_file_shape_cannot_omit_separate_papers(self):
        args = self.evidence()
        args['downloads'] = [v for v in args['downloads'] if not v['filename'].startswith('Run-')]
        with self.assertRaisesRegex(reg.RegistrationHold, 'dynamic public download'):
            reg.assemble_evidence(**args)

    def test_equal_count_unapproved_extra_cannot_replace_a_paper(self):
        args = self.evidence()
        args['downloads'][0]['filename'] = 'unapproved-summary.pdf'
        with self.assertRaisesRegex(reg.RegistrationHold, 'unapproved public download'):
            reg.assemble_evidence(**args)

    def test_duplicate_download_cannot_satisfy_dynamic_count(self):
        args = self.evidence()
        args['downloads'][-1] = deepcopy(args['downloads'][0])
        with self.assertRaisesRegex(reg.RegistrationHold, 'duplicate'):
            reg.assemble_evidence(**args)

    def test_old_manifest_does_not_become_v2_by_adding_pdf_names(self):
        args = self.evidence()
        args['manifest']['standard'] = 'VRS-METHODS-DIGEST-1'
        with self.assertRaisesRegex(reg.RegistrationHold, 'v2 manifest'):
            reg.assemble_evidence(**args)

    def test_historical_receipt_uses_original_scientific_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            receipt = root / 'original.json'
            receipt.write_text(json.dumps({'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2'}))
            binding = {'path': str(receipt), 'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}
            calls = []
            def original(*args, **kwargs):
                calls.append((args, kwargs))
                return {'science': 'original fixture result'}
            fake = SimpleNamespace(require_registration=original)
            with patch.object(reg, '_original_registrar', return_value=fake):
                value = reg.require_registration(root, binding, {'tree_root': str(root)}, views=None)
            self.assertEqual(value, {'science': 'original fixture result'})
            self.assertNotIn('digest_consumer', calls[0][1])
            self.assertNotIn('strict_consumer', calls[0][1])

    def test_original_source_hash_is_required_before_delegation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'wrong_original.py'
            source.write_text('not the admitted source')
            with patch('importlib.import_module', return_value=SimpleNamespace(__file__=str(source))):
                with self.assertRaisesRegex(reg.RegistrationHold, 'exact original installed'):
                    reg._original_registrar()


    def scoped_rows(self, root):
        package = root / 'digest'
        package.mkdir()
        note = root / 'note'
        note.mkdir()
        certificate = root / 'certificate.json'
        certificate.write_text('{}')
        path = root / 'v3.json'
        path.write_text(json.dumps({'standard': reg.STANDARD}))
        binding = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
        receipt = {'record_id': '24000001', 'doi': '10.5281/zenodo.24000001', 'release_week': '2026-W42',
                   'package_path': 'digest', 'children': [{'id': 'publication:note:Run-191', 'run_id': 'Run-191',
                      'path': 'note', 'certificate': {'path': str(certificate), 'sha256': hashlib.sha256(certificate.read_bytes()).hexdigest()},
                      'publication_binding': {'path': 'fixture.json', 'sha256': '1' * 64}}]}
        def consume(*args, **kwargs):
            return {'receipt': deepcopy(receipt)}
        ledger = {'tree_root': str(root), 'file_entities': [], 'run_entities': [], 'publication_entities': [],
                  'publication_holds': []}
        rows = reg.entity_rows(root, binding, ledger, consume=consume)
        return ledger, rows, consume

    def test_preserve_replays_only_v3_on_explicit_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            ledger, rows, consume = self.scoped_rows(root)
            oldfile = root / 'v1.json'
            oldfile.write_text(json.dumps({'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2'}))
            v1 = {'id': 'original-v1', 'path': 'old', 'registration_route': reg.GROUP_ROUTE,
                  'registration_receipt': {'path': str(oldfile), 'sha256': hashlib.sha256(oldfile.read_bytes()).hexdigest()},
                  'scientific_scope': 'original', 'publication_registration_status': 'PASS', 'enforcement_acceptable': True}
            previous = {**ledger, 'publication_entities': [v1, *rows]}
            delegated = []
            def legacy(current, ordinary):
                delegated.extend(ordinary['publication_entities'])
                return {**deepcopy(current), 'publication_entities': deepcopy(ordinary['publication_entities'])}
            result = reg.preserve(ledger, previous, legacy=legacy, consume=consume)
            self.assertEqual(delegated, [v1])
            self.assertEqual(result['publication_entities'], [v1, *rows])
            self.assertFalse(rows[0]['certifies'])
            self.assertEqual(rows[1]['certifies'], 'LISTED_NOTE_SCOPE_ONLY')

    def test_failed_v3_replay_holds_group_and_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            ledger, rows, _ = self.scoped_rows(root)
            def fail(*args, **kwargs):
                raise reg.RegistrationHold('exact paper omitted')
            result = reg.preserve(ledger, {**ledger, 'publication_entities': rows}, legacy=lambda current, old: current, consume=fail)
            self.assertTrue(all(r['publication_registration_status'] == 'HOLD' and r['enforcement_acceptable'] is False for r in result['publication_entities']))
            self.assertEqual(len(result['publication_holds']), 2)

    def test_augment_cannot_duplicate_an_existing_digest_doi(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            ledger, rows, consume = self.scoped_rows(root)
            ledger['publication_entities'] = rows
            original = {'published_records': [], 'methods_digest_groups': [{'doi': rows[0]['doi'], 'certifies': False}], 'counts': {}}
            with self.assertRaisesRegex(reg.RegistrationHold, 'collides'):
                reg.augment_audit(root, ledger, original, consume=consume)
            self.assertEqual(len(original['methods_digest_groups']), 1)

    def test_evaluate_v3_uses_explicit_consumer_and_preserves_scope(self):
        import claim_binding
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            ledger, rows, consume = self.scoped_rows(root)
            ledger['publication_entities'] = rows
            def forbidden(*args, **kwargs):
                raise AssertionError('v3 must not use legacy verdict')
            with patch.object(claim_binding, 'find_entity', return_value=rows[0]):
                result = reg.evaluate_publication(root / 'digest', ledger, legacy=forbidden, consume=consume, enforce=True)
            self.assertEqual(result['status'], 'PASS')
            self.assertFalse(result['certifies'])
            self.assertEqual(result['verification_status'], 'SCOPED_DIGEST')
            def fail(*args, **kwargs):
                raise reg.RegistrationHold('wrong bytes')
            with patch.object(claim_binding, 'find_entity', return_value=rows[1]):
                result = reg.evaluate_publication(root / 'note', ledger, legacy=forbidden, consume=fail, enforce=True)
            self.assertEqual(result['status'], 'HOLD')
            self.assertTrue(result['blocking'])


if __name__ == '__main__':
    unittest.main()
