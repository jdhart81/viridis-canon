"""Synthetic Git-shaped recovery fixtures; never touch actual legacy targets.

Every source, target, predecessor and journal lives in a resolved platform
TemporaryDirectory. These fixtures prove file/trust boundaries only; they
provide no live source, scientific or installation authority.
"""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (
        json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    path.write_bytes(raw)
    return {'path': str(path), 'sha256': runtime.sha(raw)}


def git_origin(root, rows):
    """Actual-shape observations, explicitly synthetic and entirely local."""
    commit_sha, tree_sha = 'a' * 40, 'b' * 40
    blobs = []
    for row in rows:
        raw = Path(row['path']).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        blobs.append({'path': row['git_path'], 'type': 'blob', 'mode': '100644', 'sha': blob})
    pr = put(root, 'git-fixtures/pr.json', {
        'state': 'MERGED', 'baseRefName': 'main', 'number': 999,
        'url': 'https://github.com/jdhart81/viridis-canon/pull/999',
        'mergeCommit': {'oid': commit_sha},
        'statusCheckRollup': [
            {'name': name, 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}
            for name in sorted(runtime.REQUIRED_CHECKS)]})
    commit = put(root, 'git-fixtures/commit.json', {'sha': commit_sha, 'tree': {'sha': tree_sha}})
    tree = put(root, 'git-fixtures/tree.json', {'sha': tree_sha, 'truncated': False, 'tree': blobs})
    return {'pull_request': pr, 'merge_commit': commit, 'tree': tree}


@contextmanager
def fixture():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        targets = root / 'fixture-transient-targets'
        rows = []
        for number, production in enumerate(runtime.LEGACY_TRANSIENT_SOURCES):
            raw = ('# synthetic recovery input: ' + production['name'] + '\n').encode()
            source = put(root, f'durable-sources/{number}/{Path(production["target"]).name}', raw)
            rows.append({'name': production['name'],
                         'target': str(targets / str(number) / Path(production['target']).name),
                         'source': source, 'git_path': 'fixture/original/' + str(number) + '/' + Path(production['target']).name})
        proof_rows = [{'name': row['name'], 'path': row['source']['path'],
                       'sha256': row['source']['sha256'], 'git_path': row['git_path']} for row in rows]
        origin = git_origin(root, proof_rows)
        sentinel = put(root, '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/frozen-source.py', b'# frozen v001 fixture\n')
        publisher = put(root, '_ZENODO_DEPOSITS/publish_dated_bundles.py', b'# preserved publisher fixture\n')
        with patch.object(runtime, 'LEGACY_TRANSIENT_ROOT', targets), \
                patch.object(runtime, 'LEGACY_TRANSIENT_SOURCES', tuple(rows)), \
                patch('socket.create_connection', side_effect=AssertionError('fixture must not use network')):
            yield root, rows, origin, [sentinel, publisher]


class ExactTransientRecoveryTests(unittest.TestCase):
    def assert_no_targets_or_journal(self, root, rows):
        self.assertTrue(all(not Path(row['target']).exists() for row in rows))
        self.assertFalse((root / 'reports/verification-coverage').exists())

    def test_all_eight_absent_restore_exact_bytes_with_durable_intent_and_readback(self):
        with fixture() as (root, rows, origin, preserved):
            original_open = runtime.os.open
            target_paths = {row['target'] for row in rows}
            order = []
            def checked_open(path, *args, **kwargs):
                current = Path(path)
                if str(current) in target_paths:
                    intents = list((root / 'reports/verification-coverage').rglob('RECOVERY_INTENT.json'))
                    self.assertEqual(len(intents), 1)
                    self.assertEqual(json.loads(intents[0].read_bytes())['status'],
                                     'SOURCE_PROVED_EXCLUSIVE_REHYDRATION_INTENT_NOT_COMPLETION')
                    order.append('target')
                elif current.name == 'RECOVERY_INTENT.json':
                    order.append('intent')
                elif current.name == 'RECOVERY_READBACK.json':
                    self.assertTrue(all(Path(row['target']).read_bytes() == Path(row['source']['path']).read_bytes() for row in rows))
                    order.append('readback')
                return original_open(path, *args, **kwargs)
            with patch.object(runtime.os, 'open', side_effect=checked_open):
                result = runtime.legacy_transient_precheck(root, origin, restore=True)
            self.assertEqual(order, ['intent', *(['target'] * 8), 'readback'])
            self.assertEqual(result['status'], 'EXACT_ORIGINAL_GIT_BOUND_TRANSIENT_SOURCE_READBACK')
            self.assertEqual(result['transient_source_writes'], 8)
            self.assertEqual(set(result['restored_targets']), {row['target'] for row in rows})
            self.assertEqual(len(result['targets']), 8)
            for row in rows:
                self.assertEqual(Path(row['target']).read_bytes(), Path(row['source']['path']).read_bytes())
            intent_binding, readback_binding = result['recovery_intent'], result['recovery_receipt']
            for binding in (intent_binding, readback_binding):
                self.assertEqual(runtime.sha(Path(binding['path']).read_bytes()), binding['sha256'])
            intent = json.loads(Path(intent_binding['path']).read_bytes())
            readback = json.loads(Path(readback_binding['path']).read_bytes())
            self.assertEqual(intent['absent_targets'], [row['target'] for row in rows])
            self.assertEqual(intent['allowed_sources'], rows)
            self.assertEqual(readback['restored_targets'], result['restored_targets'])
            self.assertEqual(readback['recovery_intent'], intent_binding)
            for name in ('network_requests', 'installed_source_writes', 'ssot_writes', 'zenodo_writes'):
                self.assertEqual(result[name], 0)
            self.assertFalse(result['certifies'])
            for binding in preserved:
                self.assertEqual(runtime.sha(Path(binding['path']).read_bytes()), binding['sha256'])

    def test_existing_exact_inputs_are_noop_without_counterfeit_recovery_journal(self):
        with fixture() as (root, rows, origin, _):
            for row in rows:
                target = Path(row['target']); target.parent.mkdir(parents=True)
                target.write_bytes(Path(row['source']['path']).read_bytes())
            result = runtime.legacy_transient_precheck(root, origin, restore=True)
            self.assertEqual(result['transient_source_writes'], 0)
            self.assertEqual(result['restored_targets'], [])
            self.assertNotIn('recovery_intent', result)
            self.assertNotIn('recovery_receipt', result)
            self.assertFalse((root / 'reports/verification-coverage').exists())

    def test_partial_exclusive_create_failure_retains_exact_bytes_and_durable_hold(self):
        with fixture() as (root, rows, origin, preserved):
            original_open = runtime.os.open
            target_attempts = []

            def fail_second_target(path, flags, *args, **kwargs):
                current = str(Path(path))
                if current in {row['target'] for row in rows}:
                    self.assertTrue(flags & runtime.os.O_EXCL)
                    target_attempts.append(current)
                    if current == rows[1]['target']:
                        self.assertEqual(Path(rows[0]['target']).read_bytes(),
                                         Path(rows[0]['source']['path']).read_bytes())
                        raise FileExistsError('synthetic exclusive-create collision')
                return original_open(path, flags, *args, **kwargs)

            with patch.object(runtime.os, 'open', side_effect=fail_second_target):
                with self.assertRaisesRegex(FileExistsError, 'synthetic exclusive-create collision'):
                    runtime.legacy_transient_precheck(root, origin, restore=True)

            self.assertEqual(target_attempts, [row['target'] for row in rows[:2]])
            self.assertEqual(Path(rows[0]['target']).read_bytes(),
                             Path(rows[0]['source']['path']).read_bytes())
            self.assertTrue(all(not Path(row['target']).exists() for row in rows[1:]))
            journals = root / 'reports/verification-coverage'
            intents = list(journals.rglob('RECOVERY_INTENT.json'))
            holds = list(journals.rglob('RECOVERY_HOLD.json'))
            self.assertEqual(len(intents), 1)
            self.assertEqual(len(holds), 1)
            self.assertEqual(intents[0].parent, holds[0].parent)
            self.assertFalse(list(journals.rglob('RECOVERY_READBACK.json')))
            intent = json.loads(intents[0].read_bytes())
            hold = json.loads(holds[0].read_bytes())
            self.assertEqual(intent['allowed_sources'], rows)
            self.assertEqual(intent['absent_targets'], [row['target'] for row in rows])
            self.assertEqual(hold['status'], 'HOLD_TRANSIENT_RECOVERY_NOT_ADMISSION')
            self.assertEqual(hold['intent'], {'path': str(intents[0]),
                                            'sha256': runtime.sha(intents[0].read_bytes())})
            self.assertEqual(hold['restored_targets'], [rows[0]['target']])
            self.assertEqual(hold['error_type'], 'FileExistsError')
            self.assertFalse(hold['automatic_mismatch_overwrite'])
            for name in ('ssot_writes', 'zenodo_writes'):
                self.assertEqual(hold[name], 0)
            self.assertFalse(hold['certifies'])
            for binding in preserved:
                self.assertEqual(runtime.sha(Path(binding['path']).read_bytes()), binding['sha256'])

    def test_source_git_or_observation_mismatch_holds_before_any_write(self):
        for mode in ('source-bytes', 'source-hash', 'git-blob', 'unmerged-pr', 'commit', 'truncated-tree', 'required-ci', 'cached-pass'):
            with self.subTest(mode=mode), fixture() as (root, rows, origin, _):
                if mode == 'source-bytes':
                    Path(rows[-1]['source']['path']).write_bytes(b'# changed source\n')
                elif mode == 'source-hash':
                    rows[-1]['source']['sha256'] = '0' * 64
                elif mode in {'git-blob', 'truncated-tree'}:
                    value = json.loads(Path(origin['tree']['path']).read_bytes())
                    if mode == 'git-blob':value['tree'][-1]['sha'] = 'c' * 40
                    else:value['truncated'] = True
                    origin['tree'] = put(root, 'git-fixtures/tree.json', value)
                elif mode == 'commit':
                    value = json.loads(Path(origin['merge_commit']['path']).read_bytes()); value['sha'] = 'c' * 40
                    origin['merge_commit'] = put(root, 'git-fixtures/commit.json', value)
                elif mode == 'cached-pass':
                    origin['pull_request'] = put(root, 'git-fixtures/pr.json', {'status': 'PASS'})
                else:
                    value = json.loads(Path(origin['pull_request']['path']).read_bytes())
                    if mode == 'unmerged-pr':value['state'] = 'OPEN'
                    else:
                        check = next(row for row in value['statusCheckRollup'] if row['name'] != 'standalone-manuscript-pdf')
                        check['conclusion'] = 'SKIPPED'
                    origin['pull_request'] = put(root, 'git-fixtures/pr.json', value)
                with self.assertRaises(runtime.PackagingHold):
                    runtime.legacy_transient_precheck(root, origin, restore=True)
                self.assert_no_targets_or_journal(root, rows)

    def test_existing_mismatch_or_directory_is_never_overwritten_or_partially_recovered(self):
        for mode in ('different-bytes', 'directory'):
            with self.subTest(mode=mode), fixture() as (root, rows, origin, _):
                target = Path(rows[-1]['target']); target.parent.mkdir(parents=True)
                if mode == 'different-bytes':target.write_bytes(b'# unrelated existing object\n')
                else:target.mkdir()
                with self.assertRaisesRegex(runtime.PackagingHold, 'EXISTING_MISMATCH'):
                    runtime.legacy_transient_precheck(root, origin, restore=True)
                if mode == 'different-bytes':self.assertEqual(target.read_bytes(), b'# unrelated existing object\n')
                else:self.assertTrue(target.is_dir())
                self.assertTrue(all(not Path(row['target']).exists() for row in rows[:-1]))
                self.assertFalse((root / 'reports/verification-coverage').exists())

    def test_source_target_and_target_parent_symlinks_hold_before_writes(self):
        for mode in ('source', 'target', 'parent'):
            with self.subTest(mode=mode), fixture() as (root, rows, origin, _):
                row = rows[-1]; target = Path(row['target']); source = Path(row['source']['path'])
                if mode == 'source':
                    actual = source.with_name('actual-input.py'); source.rename(actual); source.symlink_to(actual)
                elif mode == 'target':
                    target.parent.mkdir(parents=True); target.symlink_to(source)
                else:
                    real = root / 'actual-target-parent'; real.mkdir()
                    target.parent.parent.mkdir(parents=True); target.parent.symlink_to(real, target_is_directory=True)
                with self.assertRaises(runtime.PackagingHold):
                    runtime.legacy_transient_precheck(root, origin, restore=True)
                self.assertTrue(all(not Path(item['target']).exists() for item in rows[:-1]))
                self.assertFalse((root / 'reports/verification-coverage').exists())
                self.assertEqual(source.read_bytes(), ('# synthetic recovery input: ' + row['name'] + '\n').encode())

    def test_readonly_absent_preflight_and_require_present_never_write(self):
        with fixture() as (root, rows, origin, _):
            result = runtime.legacy_transient_precheck(root, origin, restore=False, require_present=False)
            self.assertEqual(result['status'], 'SOURCE_PROVED_TRANSIENTS_ABSENT_NOT_REHYDRATED')
            self.assertEqual(result['missing_targets'], [row['target'] for row in rows])
            self.assertEqual(result['transient_source_writes'], 0)
            self.assert_no_targets_or_journal(root, rows)
            with self.assertRaisesRegex(runtime.PackagingHold, 'LEGACY_TRANSIENT_ABSENT'):
                runtime.legacy_transient_precheck(root, origin, restore=False, require_present=True)
            self.assert_no_targets_or_journal(root, rows)

    def test_closed_eight_target_inventory_includes_the_original_builder(self):
        production = runtime.LEGACY_TRANSIENT_SOURCES
        self.assertEqual(len(production), 8)
        builders = [row for row in production if row['name'] == 'legacy_builder.py']
        self.assertEqual(len(builders), 1)
        self.assertEqual(Path(builders[0]['target']).name, 'prepare_first_seven_plan.py')
        self.assertEqual(builders[0]['source']['sha256'], runtime.SESSION_CONSUMER['sha256'])
        for mode in ('omit-eighth', 'duplicate-target'):
            with self.subTest(mode=mode), fixture() as (root, rows, origin, _):
                invalid = deepcopy(rows)
                if mode == 'omit-eighth':invalid.pop()
                else:invalid[-1]['target'] = invalid[0]['target']
                with patch.object(runtime, 'LEGACY_TRANSIENT_SOURCES', tuple(invalid)):
                    with self.assertRaisesRegex(runtime.PackagingHold, 'EXACT_EIGHT_LEGACY_TRANSIENTS'):
                        runtime.legacy_transient_precheck(root, origin, restore=True)
                self.assert_no_targets_or_journal(root, rows)

    def test_frozen_predecessor_exact_bindings_and_publisher_are_readonly(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); modules = []
            for name in sorted(runtime.MODULE_NAMES):
                binding = put(root, 'frozen-v001/' + name, ('# synthetic v001 module: ' + name + '\n').encode())
                modules.append({'name': name, **binding, 'git_path': runtime.PREDECESSOR_GIT_PREFIX + name})
            origin = git_origin(root, modules)
            review = put(root, 'predecessor/source-review.json', {
                'review_scope': 'SOURCE_ONLY', 'actual_live_runtime_admission': False,
                'actual_seven_record_admission': 'PENDING_POST_INSTALL_FRESH_READBACK',
                'source_hashes': {row['name']: row['sha256'] for row in modules}})
            common = {'source_origin': origin, 'source_review': review,
                      'user_authority': put(root, 'predecessor/user.json', {'synthetic_fixture': True}),
                      'access_registry': put(root, 'predecessor/registry.json', {'synthetic_fixture': True}),
                      'installed_at_utc': '2020-01-01T00:00:00Z'}
            profile = put(root, 'predecessor/profile.json', {
                'standard': 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-1', 'canonical_root': str(root),
                'modules': modules, **common})
            nomination_value = {'profile': profile,
                'status': 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
                'merged_source_commit': 'a' * 40}
            nomination = put(root, 'predecessor/nomination.json', nomination_value)
            plan = put(root, 'predecessor/plan.json', {
                'standard': 'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-1', 'source_modules': modules,
                'root_review': put(root, 'predecessor/root-review.json', {'synthetic_fixture': True}), **common})
            publisher = put(root, '_ZENODO_DEPOSITS/publish_dated_bundles.py', b'# frozen publisher fixture\n')
            snapshots = {str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}
            with ExitStack() as stack:
                for name, binding in [('PREDECESSOR_PROFILE', profile), ('PREDECESSOR_NOMINATION', nomination),
                                      ('PREDECESSOR_PLAN', plan), ('HISTORICAL_PUBLISHER', publisher)]:
                    stack.enter_context(patch.object(runtime, name, binding))
                result = runtime.predecessor_installation(root)
                self.assertFalse(result['actual_runtime_admission'])
                self.assertFalse(result['certifies'])
                self.assertEqual({str(path): path.read_bytes() for path in root.rglob('*') if path.is_file()}, snapshots)
                Path(publisher['path']).write_bytes(b'# changed publisher\n')
                with self.assertRaisesRegex(runtime.PackagingHold, 'SOURCE_HASH_OR_RACE'):
                    runtime.predecessor_installation(root)
                Path(publisher['path']).write_bytes(snapshots[publisher['path']])
                with patch.object(runtime, 'PREDECESSOR_PROFILE', {**profile, 'sha256': '0' * 64}):
                    with self.assertRaisesRegex(runtime.PackagingHold, 'SOURCE_HASH_OR_RACE'):
                        runtime.predecessor_installation(root)
                nomination_value['status'] = 'ACTUAL_INSTALLED_RUNTIME_PASS'
                replacement = put(root, 'predecessor/nomination.json', nomination_value)
                with patch.object(runtime, 'PREDECESSOR_NOMINATION', replacement):
                    with self.assertRaisesRegex(runtime.PackagingHold, 'EXACT_FROZEN_V001_INSTALLATION'):
                        runtime.predecessor_installation(root)


if __name__ == '__main__':
    unittest.main()
