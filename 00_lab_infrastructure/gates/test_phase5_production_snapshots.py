"""Production adapters deny new publication before network access on gate failure."""
import importlib.util
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


class PreparedProductionAdaptersTests(unittest.TestCase):
    def load(self, filename):
        path = Path(__file__).parent/'production_snapshots/phase5-20261005-oai-cutover/after/_ZENODO_DEPOSITS'/filename
        module_name = 'prepared_' + filename.removesuffix('.py')
        stub = types.ModuleType('release_coherence')
        stub.CoherenceError = type('CoherenceError', (ValueError,), {})
        stub.validate_bundle = lambda bundle: None
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'release_coherence': stub, module_name: module}):
            spec.loader.exec_module(module)
        return module

    def setUp(self):
        self.publisher = self.load('publish_dated_bundles.py')
        self.lockstep = self.load('weekend_canon_lockstep.py')
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.bundle = Path(self.tmp.name)
        self.payload = {'metadata': {'title': 'Original', 'description': 'Unchanged'}}
        (self.bundle/'zenodo_metadata.json').write_text(json.dumps(self.payload))

    def test_all_prepared_snapshot_hashes_match_manifest(self):
        base = Path(__file__).parent/'production_snapshots/phase7-20261006-scoped-consumers'
        manifest = json.loads((base/'AFTER_MANIFEST.json').read_text())
        self.assertEqual(len(manifest['snapshots']), 22)
        for row in manifest['snapshots']:
            with self.subTest(file=row['relative_path']):
                after = base/row['after_path']
                self.assertEqual(hashlib.sha256(after.read_bytes()).hexdigest(), row['after_sha256'])
                if row['before_path'] is not None:
                    self.assertEqual(hashlib.sha256((base/row['before_path']).read_bytes()).hexdigest(), row['before_sha256'])
                else:
                    self.assertFalse(row['before_exists'])
                if '/verification_coverage_gates/' in row['relative_path']:
                    current = Path(__file__).parent/Path(row['relative_path']).name
                    successor = Path(__file__).parent/'production_snapshots/phase7-20261007-decoupled-policy'
                    update = json.loads((successor/'AFTER_MANIFEST.json').read_text())
                    target = next(v for v in update['snapshots'] if v['relative_path'] == row['relative_path'])
                    after = successor/target['after_path']
                    self.assertEqual(hashlib.sha256(after.read_bytes()).hexdigest(), target['after_sha256'])
                    if current.name == 'corpus_ledger.py':
                        # The historical frozen bytes remain proven above.
                        # Its registry alias and every selector/legacy body
                        # are retained under the exact approved new caller.
                        from phase7_runtime_update import corpus_preservation, _preserved_functions
                        baseline=(Path(__file__).parent/'fixtures/registration_baselines/corpus_ledger.py').read_bytes()
                        proof=corpus_preservation(baseline,current.read_bytes())
                        self.assertEqual(proof['registry_import_caller']['status'],'EXACT_ORIGINAL_ALIAS_AND_APPROVED_NAMESPACE_WRAPPER')
                        *_,functions=_preserved_functions(after.read_bytes(),current.read_bytes(),{'preserve_publication_registrations':'_preserve_publication_registrations_source_original'})
                        self.assertEqual(len(functions),len([n for n in __import__('ast').parse(after.read_bytes()).body if isinstance(n,__import__('ast').FunctionDef)]))
                    elif current.name == 'publication_binding.py':
                        self.assertEqual(current.read_bytes(), (base/row['after_path']).read_bytes())
                        self.assertEqual(target['before_sha256'],target['after_sha256'])
                    else:
                        self.assertEqual(current.read_bytes(), after.read_bytes())

    def test_decoupled_successor_closes_exact_22_targets_and_preserves_every_prior_snapshot(self):
        root=Path(__file__).parent/'production_snapshots'
        old=root/'phase7-20261006-scoped-consumers'
        selector=root/'phase7-20261007-run187-selector'
        new=root/'phase7-20261007-decoupled-policy'
        old_raw=(old/'AFTER_MANIFEST.json').read_bytes()
        selector_raw=(selector/'MANIFEST.json').read_bytes()
        self.assertEqual((new/'PREDECESSOR_AFTER_MANIFEST.json').read_bytes(),old_raw)
        self.assertEqual((new/'SELECTOR_MANIFEST.json').read_bytes(),selector_raw)
        prior={r['relative_path']:r for r in json.loads(old_raw)['snapshots']}
        runtime_raw=(new/'SELECTOR_RUNTIME_RECEIPT.json').read_bytes()
        self.assertEqual(hashlib.sha256(runtime_raw).hexdigest(),'02957fbd6ea67e02e7e6979a06f0d07d4e3d46be6dbe8b783b847fb9ba9192b9')
        approved={r['path']:r for r in json.loads(runtime_raw)['runtime_targets']}
        self.assertEqual(len(approved),22)
        manifest=json.loads((new/'AFTER_MANIFEST.json').read_bytes())
        rows=manifest['snapshots'];self.assertEqual(len(rows),22)
        from install_phase5_hooks import TARGETS
        self.assertEqual({r['relative_path']for r in rows},TARGETS)
        reviewed={'corpus_ledger.py','nightly_coverage.py','premise_declaration.py','publication_gate.py','doi_audit.py'}
        self.assertEqual(set(manifest['reviewed_consumer_names']),reviewed)
        self.assertFalse(manifest['protected_verifier_issuer_changed'])
        changed=[]
        for row in rows:
            rel=row['relative_path'];previous=prior[rel]
            expected_before=approved[rel]['after_sha256']
            self.assertEqual(row['before_sha256'],expected_before)
            self.assertEqual(hashlib.sha256((new/row['before_path']).read_bytes()).hexdigest(),expected_before)
            self.assertEqual(hashlib.sha256((new/row['after_path']).read_bytes()).hexdigest(),row['after_sha256'])
            self.assertEqual(hashlib.sha256((old/previous['after_path']).read_bytes()).hexdigest(),previous['after_sha256'])
            if row['before_sha256']!=row['after_sha256']:changed.append(Path(rel).name)
            if Path(rel).name not in reviewed:
                self.assertEqual(row['before_sha256'],row['after_sha256'])
                self.assertEqual((new/row['before_path']).read_bytes(),(new/row['after_path']).read_bytes())
        self.assertEqual(sorted(changed),['corpus_ledger.py','doi_audit.py','premise_declaration.py','publication_gate.py'])
        self.assertEqual(manifest['unchanged_outside_reviewed_targets'],17)

    def test_phase7_successor_preserves_frozen_predecessor_and_only_three_consumers_change(self):
        root=Path(__file__).parent/'production_snapshots'
        old=root/'phase5-20261005-provenance-closure';new=root/'phase7-20261006-scoped-consumers'
        self.assertEqual((new/'PREDECESSOR_AFTER_MANIFEST.json').read_bytes(),(old/'AFTER_MANIFEST.json').read_bytes())
        before={r['relative_path']:r for r in json.loads((old/'AFTER_MANIFEST.json').read_text())['snapshots']}
        manifest=json.loads((new/'AFTER_MANIFEST.json').read_text())
        after={r['relative_path']:r for r in manifest['snapshots']}
        from install_phase5_hooks import TARGETS
        self.assertEqual(set(before),TARGETS);self.assertEqual(set(after),TARGETS)
        changed=[p for p in sorted(TARGETS) if before[p]['after_sha256']!=after[p]['after_sha256']]
        self.assertEqual([Path(p).name for p in changed],['corpus_ledger.py','publication_binding.py','publication_gate.py'])
        self.assertFalse(manifest['protected_verifier_issuer_changed'])
        for p in TARGETS-set(changed):self.assertEqual(before[p],after[p])
        for p in changed:
            self.assertEqual(after[p]['before_sha256'],before[p]['after_sha256'])
            self.assertEqual((new/after[p]['before_path']).read_bytes(),(old/before[p]['after_path']).read_bytes())

    def test_provenance_successor_preserves_original_and_other_21_targets(self):
        root = Path(__file__).parent/'production_snapshots'
        original = root/'phase5-20261005-oai-cutover'
        successor = root/'phase5-20261005-provenance-closure'
        original_raw = (original/'AFTER_MANIFEST.json').read_bytes()
        self.assertEqual(hashlib.sha256(original_raw).hexdigest(),
                         '8abfd4f5264c7c6f9c61b0a79c810a7a725d74ce7100b4d209fabaa9d6b1b677')
        self.assertEqual((successor/'AFTER_MANIFEST_PRE_PROVENANCE_20261005.json').read_bytes(), original_raw)
        self.assertEqual((successor/'BEFORE_MANIFEST.json').read_bytes(),
                         (original/'BEFORE_MANIFEST.json').read_bytes())
        before = {row['relative_path']: row for row in json.loads(original_raw)['snapshots']}
        after = {row['relative_path']: row for row in json.loads((successor/'AFTER_MANIFEST.json').read_bytes())['snapshots']}
        from install_phase5_hooks import TARGETS
        self.assertEqual(set(before), TARGETS)
        self.assertEqual(set(after), TARGETS)
        guard = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
        self.assertEqual([path for path in sorted(TARGETS)
                          if before[path]['after_sha256'] != after[path]['after_sha256']], [guard])
        for path in TARGETS - {guard}:
            with self.subTest(path=path):
                self.assertEqual(after[path], before[path])
        self.assertEqual(after[guard]['before_sha256'], before[guard]['after_sha256'])
        self.assertEqual((successor/after[guard]['before_path']).read_bytes(),
                         (original/before[guard]['after_path']).read_bytes())

    def test_historical_22_target_manifest_and_original_before_bytes_remain_exact(self):
        root=Path(__file__).parent/'production_snapshots'
        original=root/'phase5-20261004';current=root/'phase5-20261005-oai-cutover'
        old_after='a881ae2973421db2401fd7b768893365f5bff2d476ad6e4b8a93722a0188d427'
        old_before='60d7133b8a10da2a051f1bc83a8351dcd0c57c1eefd9456c77d532d01776edf1'
        digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(digest(original/'AFTER_MANIFEST.json'),old_after)
        self.assertEqual(digest(current/'AFTER_MANIFEST_PRE_CUTOVER_20261005.json'),old_after)
        self.assertEqual(digest(original/'BEFORE_MANIFEST.json'),old_before)
        self.assertEqual((original/'BEFORE_MANIFEST.json').read_bytes(),(current/'BEFORE_MANIFEST.json').read_bytes())
        old=json.loads((original/'AFTER_MANIFEST.json').read_text());new=json.loads((current/'AFTER_MANIFEST.json').read_text())
        from install_phase5_hooks import TARGETS
        self.assertEqual(len(old['snapshots']),22);self.assertEqual(len(new['snapshots']),22)
        self.assertEqual({e['relative_path'] for e in old['snapshots']},TARGETS)
        self.assertEqual({e['relative_path'] for e in new['snapshots']},TARGETS)
        self.assertEqual(new['preserved_pre_cutover_manifest'],{'path':'AFTER_MANIFEST_PRE_CUTOVER_20261005.json','sha256':old_after})
        old_rows={e['relative_path']:e for e in old['snapshots']};changed=[]
        for row in new['snapshots']:
            previous=old_rows[row['relative_path']]
            with self.subTest(file=row['relative_path']):
                self.assertEqual(digest(original/previous['after_path']),previous['after_sha256'])
                self.assertEqual(row['before_path'],previous['before_path'])
                self.assertEqual(row['before_sha256'],previous['before_sha256'])
                if row['before_path'] is not None:
                    self.assertEqual((original/previous['before_path']).read_bytes(),(current/row['before_path']).read_bytes())
                    self.assertEqual(digest(original/previous['before_path']),previous['before_sha256'])
                if row['after_sha256']!=previous['after_sha256']:
                    changed.append(Path(row['relative_path']).name)
                else:
                    self.assertEqual((original/previous['after_path']).read_bytes(),(current/row['after_path']).read_bytes())
        self.assertEqual(sorted(changed),['corpus_ledger.py','nightly_coverage.py','run_flow.py'])

    def test_attempt_local_raw_diagnostics_never_enter_upload_inventory(self):
        (self.bundle/'paper.pdf').write_bytes(b'%PDF fixture')
        diagnostics=self.bundle/'transport-diagnostics'/'fixture';diagnostics.mkdir(parents=True)
        for name in ('stdout.bin','stderr.bin','manifest.json'):
            (diagnostics/name).write_bytes(b'PRIVATE_DIAGNOSTIC_FIXTURE')
        files=self.publisher.upload_files(self.bundle)
        self.assertEqual([p.name for p in files],['paper.pdf'])
        self.assertTrue(all(not p.is_relative_to(diagnostics.parent) for p in files))

    def test_new_publisher_without_explicit_flag_never_opens_draft(self):
        with patch.object(self.publisher, 'ensure_draft') as draft, patch.object(self.publisher, 'api_call') as api:
            with self.assertRaisesRegex(self.publisher.PublisherError, 'requires --enforce-new-artifacts'):
                self.publisher.publish_bundle(self.bundle, 'test-only-placeholder')
            draft.assert_not_called(); api.assert_not_called()

    def test_existing_doi_is_read_only_and_not_republished(self):
        (self.bundle/'PUBLISHED_DOI.txt').write_text('10.5281/zenodo.1234')
        with patch.object(self.publisher, 'api_call') as api:
            self.assertEqual(self.publisher.publish_bundle(self.bundle, 'test-only-placeholder'), '10.5281/zenodo.1234')
            api.assert_not_called()

    def test_coherence_precedes_gate_and_metadata_bytes_preserved(self):
        sequence = []
        with patch.object(self.publisher.release_coherence, 'validate_bundle', side_effect=lambda _: sequence.append('coherence')), \
                patch.object(self.publisher, 'verification_coverage_report', side_effect=lambda *a, **k: sequence.append(('gate', k))):
            before = (self.bundle/'zenodo_metadata.json').read_bytes()
            self.assertEqual(self.publisher.metadata_payload(self.bundle, enforce_new_artifacts=True), self.payload)
            self.assertEqual(sequence, ['coherence', ('gate', {'enforce_new_artifacts': True})])
            self.assertEqual((self.bundle/'zenodo_metadata.json').read_bytes(), before)

    def test_publisher_gate_hold_denies_draft_and_upload(self):
        with patch.object(self.publisher, 'verification_coverage_report', side_effect=self.publisher.PublisherError('HOLD')), \
                patch.object(self.publisher, 'ensure_draft') as draft, patch.object(self.publisher, 'api_call') as api:
            with self.assertRaises(self.publisher.PublisherError):
                self.publisher.publish_bundle(self.bundle, 'test-only-placeholder', enforce_new_artifacts=True)
            draft.assert_not_called(); api.assert_not_called()

    def test_lockstep_without_flag_denies_git_and_publisher(self):
        with patch.object(self.lockstep, 'discover_bundles', return_value=[]), patch.object(self.lockstep, 'print_plan'), \
                patch.object(self.lockstep, 'read_github_token') as credential:
            with self.assertRaisesRegex(self.lockstep.LockstepError, 'requires --enforce-new-artifacts'):
                self.lockstep.main(['--date', '2026-10-04', '--go'])
            credential.assert_not_called()

    def test_lockstep_publisher_must_also_enforce(self):
        with patch.object(self.lockstep, 'discover_bundles', return_value=[]), patch.object(self.lockstep, 'print_plan'), \
                patch.object(self.lockstep, 'read_github_token') as credential:
            with self.assertRaisesRegex(self.lockstep.LockstepError, 'publisher argv must enforce'):
                self.lockstep.main(['--date', '2026-10-04', '--go', '--enforce-new-artifacts', '--', 'publisher', '--publish', '--go'])
            credential.assert_not_called()

    def test_default_lockstep_plan_remains_local(self):
        with patch.object(self.lockstep, 'discover_bundles', return_value=[]), patch.object(self.lockstep, 'print_plan'), \
                patch.object(self.lockstep, 'read_github_token') as credential, patch('builtins.print'):
            self.assertEqual(self.lockstep.main(['--date', '2026-10-04']), 0)
            credential.assert_not_called()

    def test_hook_failures_raise_only_in_explicit_enforcing_mode(self):
        for module, error in [(self.publisher, self.publisher.PublisherError), (self.lockstep, self.lockstep.LockstepError)]:
            with self.subTest(adapter=module.__name__), patch('production_hooks.log_publication', side_effect=ValueError('missing receipt')), patch('builtins.print'):
                with self.assertRaises(error):
                    module.verification_coverage_report(self.bundle, 'test', enforce_new_artifacts=True)
                self.assertIsNone(module.verification_coverage_report(self.bundle, 'test'))


if __name__ == '__main__': unittest.main()
