"""Closed current archival-access source contracts over isolated temp DATA.

These source/installer/worker fixtures supply no scientific or publication
admission. The real default-policy access tests live in their separate suite.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime
import install_packaging_runtime as installer
import owner_content_worker as owner
import scientific_registration_worker as science
import guard_methods_digest_release as guard
import test_packaging_v002_cold_scope as cold_tests
import test_packaging_runtime as runtime_tests
from test_packaging_runtime import put
import test_packaging_v007_worker_sources as worker_tests
import test_digest_route_scope as route_tests
import test_outer_digest_guard as guard_tests
from test_owner_content_worker import fixture as owner_fixture
import test_scientific_registration_worker as science_tests


class ArchivalProfileTests(unittest.TestCase):
    def test_current20_does_not_admit_prior18_or_successor_in_either_slot(self):
        helper = route_tests.DigestRouteScopeTests()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            rows = helper.rows(root, runtime.MODULE_NAMES, runtime.GIT_PREFIX)
            self.assertEqual(len(runtime.module_table(root, rows)), 20)
            old = [r for r in rows if r['name'] in runtime.PRIOR_DIGEST_MODULE_NAMES]
            self.assertEqual(len(old), 18)
            with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                runtime.module_table(root, old)
            successor = helper.rows(root, {'publish_successor_wave_guarded.py'}, runtime.GIT_PREFIX)[0]
            for omitted in ('nightly_manuscript_access.py', 'nightly_manuscript_checkpoint.py'):
                with self.subTest(omitted=omitted), self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                    runtime.module_table(root, [r for r in rows if r['name'] != omitted] + [successor])

    def test_profile_wrong_missing_reordered_or_old_nomination_holds_before_authority(self):
        helper = runtime_tests.RuntimeTrustTests()
        for change in ('missing', 'wrong_module', 'reordered', 'old_profile'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                root = Path(folder).resolve()
                value, _, _ = helper.fixture(root)
                if change == 'missing': del value['note_preparation']
                elif change == 'wrong_module': value['note_preparation'] = {**runtime.NOTE_PREPARATION, 'module':'packaging_nightly.py'}
                elif change == 'reordered': value['note_preparation'] = {**runtime.NOTE_PREPARATION, 'entrypoints':list(reversed(runtime.NOTE_PREPARATION['entrypoints']))}
                else: value['standard'] = 'VRS-DIGEST-ONLY-PDF-PACKAGING-PROFILE-1'
                profile = put(root, runtime.PROFILE_PATH, value)
                real = runtime.object_at
                def object_at(r, binding):
                    self.assertEqual(binding, profile, 'authority read before closed current profile')
                    return real(r, binding)
                with patch.object(runtime, 'require_nomination', return_value={}), patch.object(runtime, 'object_at', side_effect=object_at):
                    with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_INSTALLED_PROFILE'):
                        runtime.validate(root, profile)

    def test_installer_altered_note_preparation_holds_before_source_proof_or_writes(self):
        helper = runtime_tests.InstallerPreflightTests()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            plan, finish, _, _, _ = helper.fixture(root)
            plan['note_preparation'] = {**runtime.NOTE_PREPARATION, 'module':'packaging_nightly.py'}
            bound = finish()
            with patch.object(installer, 'ROOT', root), patch.object(runtime, 'module_table', side_effect=AssertionError('source table entered before facade nomination')):
                with self.assertRaisesRegex(runtime.PackagingHold, 'EXACT_NOTE_PREPARATION_NOMINATION'):
                    installer.preflight(root, bound)
            self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

    def test_outer_guard_altered_note_preparation_holds_before_real_child(self):
        helper = guard_tests.OuterDigestGuardTests()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            stack, config, digest, log = helper.fixture(root)
            with stack:
                self.assertIn('invoke_digest_v2.py', guard.context(config, digest)['sources'])
                profile = json.loads(guard.PROFILE.read_bytes())
                profile['note_preparation']['module'] = 'packaging_nightly.py'
                guard.PROFILE.write_text(json.dumps(profile))
                binding = {'path':str(guard.PROFILE), 'sha256':hashlib.sha256(guard.PROFILE.read_bytes()).hexdigest()}
                nomination = json.loads(guard.NOMINATION.read_bytes()); nomination['profile'] = binding
                guard.NOMINATION.write_text(json.dumps(nomination))
                config.write_text(json.dumps({'canonical_root':str(root), 'packaging_profile':binding}))
                with self.assertRaisesRegex(guard.GuardHold, 'exact installed successor profile'):
                    guard.context(config, hashlib.sha256(config.read_bytes()).hexdigest())
                self.assertFalse(log.exists())

    def test_owner_bootstrap_rejects_altered_facade_manifest(self):
        with owner_fixture() as f, patch.object(owner, 'FIXED_CANONICAL_ROOT', f.root):
            self.assertEqual(owner.bootstrap_sources(f.manifest), f.root)
            value = deepcopy(f.manifest); value['note_preparation']['module'] = 'packaging_nightly.py'
            with self.assertRaisesRegex(owner.TransportHold, 'NOMINATED_BOOTSTRAP_NOTE_PREPARATION'):
                owner.bootstrap_sources(value)

    def test_science_bootstrap_rejects_altered_facade_manifest_before_runtime(self):
        helper = science_tests.ScienceTransportTests()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); directory, config = helper.bootstrap_fixture(root)
            config_value = json.loads(config.read_bytes()); manifest_path = Path(config_value['source_manifest']['path'])
            manifest = json.loads(manifest_path.read_bytes()); manifest['note_preparation']['module'] = 'packaging_nightly.py'
            manifest_path.write_bytes(science.raw(manifest)); config_value['source_manifest'] = science.binding(manifest_path)
            config.write_bytes(science.raw(config_value))
            argv = ['synthetic-worker','--config',str(config),'--expected-config-sha256',science.binding(config)['sha256']]
            with patch.object(science, 'BOOTSTRAP_ROOT', root), patch.object(science, '__file__', str(directory/'scientific_registration_worker.py')), patch.object(sys, 'argv', argv):
                with self.assertRaisesRegex(ValueError, 'WORKER_BOOTSTRAP_NOTE_PREPARATION_BINDING'):
                    science._bootstrap()

    def test_manifest_proof_binds_facade_and_new_module_count(self):
        helper = worker_tests.WorkerSourceTests()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve(); binding, _ = helper.fixture(root)
            with helper.source_fixture(root), runtime.readonly_worker_scope():
                manifest = runtime.build_worker_source_manifest(root, binding)
                proof = runtime.verify_worker_source_manifest(root, binding, manifest)
                self.assertEqual(proof['source_modules'], 20)
                self.assertEqual(proof['note_preparation'], runtime.NOTE_PREPARATION)
                owner.source_proof_valid(proof, manifest)
                bad = deepcopy(proof); bad['note_preparation']['module'] = 'packaging_nightly.py'
                with self.assertRaisesRegex(owner.TransportHold, 'CURRENT_WORKER_SOURCE_PROOF'):
                    owner.source_proof_valid(bad, manifest)

    def test_new_module_alternate_import_artifacts_hold_in_all_current_bootstraps(self):
        checks = [runtime.current_import_artifact_guard, owner.reject_import_artifacts, science._bootstrap_artifacts]
        for check in checks:
            for name in ('nightly_manuscript_access', 'nightly_manuscript_checkpoint'):
                for suffix in ('', '.pyc', '.pyo'):
                    with self.subTest(check=check.__name__, name=name, suffix=suffix), tempfile.TemporaryDirectory() as folder:
                        root = Path(folder).resolve(); check(root)
                        path = root / (name+suffix)
                        if suffix: path.write_bytes(b'not executable source')
                        else: path.mkdir()
                        with self.assertRaisesRegex(ValueError, 'IMPORT_ARTIFACT'):
                            check(root)

    def test_preparation_route_uses_pinned_facade_in_genuine_source_session(self):
        with cold_tests.synthetic_validation_case() as (root, checked, binding, base, modules, events):
            profile = json.loads(Path(binding['path']).read_bytes())
            row = next(r for r in modules if r['name'] == 'nightly_manuscript_checkpoint.py')
            source = ("import sys\nfrom pathlib import Path\nimport packaging_runtime as canonical_runtime\n"
                      "def stage_checkpoint(root, value, *, mode):\n"
                      "    p=Path(root)/canonical_runtime.PROFILE_PATH\n"
                      "    canonical_runtime.require_source_session(root,{'path':str(p),'sha256':canonical_runtime.sha(p.read_bytes())})\n"
                      "    assert any(type(f).__name__ == 'SourceFinder' for f in sys.meta_path), 'facade outside genuine source session'\n"
                      "    return {'root':str(root),'value':value,'mode':mode,'source':str(Path(__file__))}\n").encode()
            Path(row['path']).write_bytes(source); row['sha256'] = checked.sha(source)
            profile['modules'] = modules
            all_rows = [*modules, *profile['shared_dependencies']]
            profile['source_origin'] = cold_tests.origin(root, 'route-additive-proof', all_rows, checked)
            review = json.loads(Path(profile['source_review']['path']).read_bytes())
            review['source_hashes'] = {r['name']:r['sha256'] for r in all_rows}
            profile['source_review'] = cold_tests.put(root, 'route-review.json', review)
            binding = cold_tests.put(root, checked.PROFILE_PATH, profile)
            cold_tests.put(root, checked.NOMINATION_PATH, {'profile':binding})
            before = tuple(sys.meta_path)
            try:
                result = checked.note_preparation(root, 'stage_checkpoint', 'synthetic argument', mode='SOURCE_ONLY')
            except ValueError as error:
                self.fail('genuine private/canonical preparation source scope rejected: '+str(error))
            canonical = sys.modules['packaging_runtime']
            self.assertIsNot(canonical, checked)
            with self.assertRaisesRegex(ValueError, 'ACTIVE_COMPLETE_SOURCE_SESSION_REQUIRED'):
                canonical.require_source_session(root, binding)
            self.assertEqual(result, {'root':str(root),'value':'synthetic argument','mode':'SOURCE_ONLY','source':row['path']})
            self.assertEqual(tuple(sys.meta_path), before)
            self.assertGreaterEqual(events.count('proved-original'), 3)
            self.assertGreaterEqual(events.count('proved-additive'), 3)
            self.assertGreaterEqual(events.count('root-plan-checked'), 3)

    def test_preparation_route_rejects_unreviewed_operation_before_nomination(self):
        for entrypoint in ('execute', '__dict__', 'publish_successor_wave_guarded.py', lambda:None):
            with self.subTest(entrypoint=repr(entrypoint)), patch.object(runtime, 'nominated_binding', side_effect=AssertionError('unreviewed entrypoint reached nomination')):
                with self.assertRaisesRegex(runtime.PackagingHold, 'FIXED_NOTE_PREPARATION_ENTRYPOINT'):
                    runtime.note_preparation('/nonexistent-source-only-fixture', entrypoint)

    def test_active_source_scope_requires_exact_profile_and_revokes_after_exception(self):
        with cold_tests.synthetic_validation_case() as (root, checked, binding, *_):
            with self.assertRaisesRegex(checked.PackagingHold, 'ACTIVE_COMPLETE_SOURCE_SESSION_REQUIRED'):
                checked.require_source_session(root, binding)
            with self.assertRaisesRegex(RuntimeError, 'synthetic operation failure'):
                with checked.session(root, binding):
                    checked.require_source_session(root, binding)
                    other = cold_tests.put(root, 'same-bytes-profile.json', Path(binding['path']).read_bytes())
                    with self.assertRaisesRegex(checked.PackagingHold, 'ACTIVE_EXACT_NOMINATED_SOURCE_SESSION'):
                        checked.require_source_session(root, other)
                    raise RuntimeError('synthetic operation failure')
            with self.assertRaisesRegex(checked.PackagingHold, 'ACTIVE_COMPLETE_SOURCE_SESSION_REQUIRED'):
                checked.require_source_session(root, binding)

    def test_current_review_schema_requires_archival_flags_and_every_new_source_hash(self):
        hashes = {name:'a'*64 for name in runtime.MODULE_NAMES | {runtime.SHARED_INPUT_NAME}}
        # Build the full closed review without borrowing an admission result.
        review = {'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-13',
            'status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS','reviewer':'synthetic source-contract fixture',
            'source_hashes':hashes,'legacy_closure':runtime.LEGACY_CLOSURE,
            'review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,
            'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK', **runtime.CURRENT_SOURCE_REVIEW_CHANGE_FLAGS}
        runtime.require_source_review(review, hashes, runtime.LEGACY_CLOSURE)
        for name in ('nightly_manuscript_access.py','nightly_manuscript_checkpoint.py'):
            bad = deepcopy(review); del bad['source_hashes'][name]
            with self.assertRaisesRegex(runtime.PackagingHold, 'EXACT_INDEPENDENT_SOURCE_REVIEW'):
                runtime.require_source_review(bad, hashes, runtime.LEGACY_CLOSURE)
        bad = deepcopy(review); del bad['archival_manuscript_access_packaging_changed']
        with self.assertRaises(runtime.PackagingHold): runtime.require_source_review(bad, hashes, runtime.LEGACY_CLOSURE)
        bad = deepcopy(review); bad['standard'] = 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-12'
        with self.assertRaises(runtime.PackagingHold): runtime.require_source_review(bad, hashes, runtime.LEGACY_CLOSURE)


if __name__ == '__main__': unittest.main()
