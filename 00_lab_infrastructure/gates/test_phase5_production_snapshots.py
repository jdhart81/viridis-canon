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
        path = Path(__file__).parent/'production_snapshots/phase5-20261004/after/_ZENODO_DEPOSITS'/filename
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
        base = Path(__file__).parent/'production_snapshots/phase5-20261004'
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
                    self.assertEqual(current.read_bytes(), after.read_bytes())

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
