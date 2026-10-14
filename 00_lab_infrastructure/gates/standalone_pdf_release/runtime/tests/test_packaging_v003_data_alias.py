"""Narrow historical DATA alias fixtures; no production/runtime admission.

All writable paths are temporary. The observation/alias constants alone are
redirected to the synthetic descriptor; no alias validator or scientific
predicate is replaced. The one read-race case injects a filesystem change after
a real temporary-file read, rather than returning a mocked read or verdict.
"""
import ast
import contextlib
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_catalog as catalog
import packaging_runtime as runtime
import test_packaging_default_routes as default_fixtures


@contextlib.contextmanager
def alias_fixture():
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary).resolve()
        root = base / 'canonical'
        root.mkdir()
        alias = base / 'canonical  '
        alias.symlink_to(root.name)
        names = {
            'candidate_proof': 'VERIFICATION_CANDIDATE.lean',
            'formal_statement': 'VERIFICATION_STATEMENT_V2.lean',
            'independent_cloud_receipt': 'COMPARATOR_VERIFICATION_RECEIPT_V2.json',
            'request': 'ENGINE3_FROZEN_REQUEST_V2.json',
            'sealed:SEALED_CLAIM_INVENTORY.json': 'SEALED_CLAIM_INVENTORY.json',
            'sealed:SEALED_RUN_MANIFEST.json': 'SEALED_RUN_MANIFEST.json',
            'sealed:SEALED_paper.pdf': 'SEALED_paper.pdf',
            'sealed:SEALED_paper.tex': 'SEALED_paper.tex',
        }
        rows = []
        for key, name in names.items():
            relative = Path('RESEARCH_PIPELINE_v2/engine3_verification/Run-117') / name
            physical = root / relative
            physical.parent.mkdir(parents=True, exist_ok=True)
            raw = ('exact synthetic original bytes: ' + key).encode()
            physical.write_bytes(raw)
            rows.append({'binding_name': key, 'bytes': len(raw),
                         'logical_path': str(alias / relative),
                         'physical_path': str(physical), 'sha256': runtime.sha(raw)})
        certificate = root / 'RESEARCH_PIPELINE_v2/lean_certificates/Run-117/certificate.json'
        certificate.parent.mkdir(parents=True)
        certificate.write_text(json.dumps({'synthetic_original_binding_rows': rows}))
        observation = {
            'standard': 'VRS-HISTORICAL-CONTROLPLANE-DATA-ALIAS-OBSERVATION-1',
            'status': 'ACTUAL_EXISTING_HISTORICAL_ALIAS_AND_ORIGINAL_CERTIFICATE_BYTES_VERIFIED_NOT_RUNTIME_ADMISSION',
            'alias_path': str(alias), 'canonical_root': str(root),
            'physical_target': str(root), 'identity': runtime.data_alias_identity(alias),
            'observed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'original_binding_readbacks': rows,
            'representative_original_certificate': {
                'path': str(certificate.relative_to(root)),
                'sha256': runtime.sha(certificate.read_bytes())},
            'scope': 'Synthetic fixture; one exact historical DATA ancestor only.',
            'alias_writes': 0, 'certificate_writes': 0, 'source_or_ssot_writes': 0,
            'network_requests': 0, 'certifies': False,
        }
        receipt = root / 'reports/synthetic_alias_observation.json'
        receipt.parent.mkdir()
        receipt.write_text(json.dumps(observation, sort_keys=True))
        binding = {'path': str(receipt.relative_to(root)),
                   'sha256': runtime.sha(receipt.read_bytes())}
        physical = root / 'inputs/scientific.lean'
        physical.parent.mkdir()
        physical.write_bytes(b'exact synthetic scientific DATA')
        output = root / 'reports/owner_fixture'
        output.mkdir()
        context = SimpleNamespace(owner_evidence_directory=output)
        with patch.object(runtime, 'SCIENTIFIC_ALIAS_PATH', alias), \
             patch.object(runtime, 'SCIENTIFIC_ALIAS_READLINK', root.name), \
             patch.object(runtime, 'DATA_ALIAS_OBSERVATION', binding):
            yield SimpleNamespace(base=base, root=root, alias=alias,
                                  observation=observation, receipt=receipt,
                                  binding=binding, rows=rows, physical=physical,
                                  logical=alias / physical.relative_to(root),
                                  context=context, output=output)


# Exact AST bodies selected from unchanged original nightly_proof_track.py
# b63c3866db0e3538f6462ca32f0bbf916a6e80081d1bdf74514b1fa6c7dc2b06.
# Keeping the SHA-selected bodies here makes the synthetic test portable; when
# the complete original source is present, both it and this selection must match.
ORIGINAL_BINDING_BODIES = '''def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def binding_is_current(binding: object, control_root: Path) -> bool:
    """Resolve immutable bindings exactly as the foundry continuity gate does."""
    if not isinstance(binding, dict):
        return False
    path_value = binding.get('path')
    digest = binding.get('sha256')
    if not isinstance(path_value, str) or not isinstance(digest, str):
        return False
    path = Path(path_value)
    candidates = [path]
    if not path.is_absolute():
        candidates = [control_root / path, control_root / 'RESEARCH_PIPELINE_v2' / path]
    for candidate in candidates:
        try:
            if candidate.is_file() and sha256_file(candidate) == digest:
                return True
        except OSError:
            continue
    return False
'''


def original_binding_is_current():
    """Execute exact unchanged original function ASTs on temporary inputs only."""
    expected_body = '98042582fac4c874dc3c3f2a6ce32438d0f4ac49d1b92a523d3d63359c75176c'
    if runtime.sha(ORIGINAL_BINDING_BODIES.encode()) != expected_body:
        raise RuntimeError('Original binding reader AST selection changed')
    source = HERE.parents[2] / 'RESEARCH_PIPELINE_v2/nightly_proof_track.py'
    if source.is_file():
        raw = source.read_bytes()
        expected = 'b63c3866db0e3538f6462ca32f0bbf916a6e80081d1bdf74514b1fa6c7dc2b06'
        if runtime.sha(raw) != expected:
            raise RuntimeError('Original binding reader source changed')
        functions = [node for node in ast.parse(raw).body
                     if isinstance(node, ast.FunctionDef)
                     and node.name in ('sha256_file', 'binding_is_current')]
        selection = ast.unparse(ast.Module(body=functions, type_ignores=[])) + '\n'
        if selection != ORIGINAL_BINDING_BODIES:
            raise RuntimeError('Original binding reader AST selection mismatched')
    namespace = {'Path': Path, 'hashlib': hashlib}
    exec(compile(ORIGINAL_BINDING_BODIES, 'unchanged_original_binding_reader_ast', 'exec'), namespace)
    return namespace['binding_is_current']


class HistoricalDataAliasTests(unittest.TestCase):
    def data(self, fixture):
        return catalog.ScientificInputData(fixture.root, fixture.context,
                                          data_alias_observation=fixture.binding)

    @contextlib.contextmanager
    def actual_read_capture(self, data):
        token = catalog._READ_CAPTURE.set(data)
        try:
            yield
        finally:
            catalog._READ_CAPTURE.reset(token)

    def test_exact_alias_supports_unchanged_original_reader_and_retains_both_identities(self):
        original_reader = original_binding_is_current()
        with alias_fixture() as fixture:
            data = self.data(fixture)
            logical_binding = {'path': str(fixture.logical),
                               'sha256': runtime.sha(fixture.physical.read_bytes())}
            with self.actual_read_capture(data):
                self.assertTrue(original_reader(logical_binding, fixture.root))
            row = data.inputs[str(fixture.logical)]
            stat = fixture.physical.stat()
            self.assertEqual(row['physical_path'], str(fixture.physical))
            self.assertEqual(row['sha256'], logical_binding['sha256'])
            self.assertEqual(row['historical_alias_identity'], fixture.observation['identity'])
            self.assertEqual((row['device'], row['inode'], row['mode'], row['bytes'],
                              row['mtime_ns'], row['ctime_ns']),
                             (stat.st_dev, stat.st_ino, stat.st_mode, stat.st_size,
                              stat.st_mtime_ns, stat.st_ctime_ns))
            # Matching bytes are still insufficient for an incorrect original hash.
            with self.actual_read_capture(data):
                self.assertFalse(original_reader({**logical_binding, 'sha256': '0' * 64}, fixture.root))
            data.assert_current()
            self.assertIsNone(catalog._READ_CAPTURE.get())

    def test_alias_is_never_an_accepted_source_binding(self):
        with alias_fixture() as fixture:
            self.data(fixture).record(fixture.logical)
            binding = {'path': str(fixture.logical),
                       'sha256': runtime.sha(fixture.physical.read_bytes())}
            with self.assertRaisesRegex(runtime.PackagingHold, 'REGULAR_CONTAINED_SOURCE'):
                runtime.read(fixture.root, binding)
            self.assertEqual(runtime.read(fixture.root, {
                **binding, 'path': str(fixture.physical)})[1], fixture.physical.read_bytes())

    def test_missing_or_wrong_fixed_observation_never_admits_an_alias(self):
        with alias_fixture() as fixture:
            strict = catalog.ScientificInputData(fixture.root, fixture.context)
            with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_REGULAR_PATH'):
                strict.record(fixture.logical)
            with self.assertRaisesRegex(runtime.PackagingHold,
                                        'FIXED_HISTORICAL_DATA_ALIAS_OBSERVATION|SOURCE_HASH_OR_RACE'):
                catalog.ScientificInputData(fixture.root, fixture.context,
                                           data_alias_observation={**fixture.binding, 'sha256': '0' * 64})

    def test_modified_observation_or_representative_original_bytes_hold(self):
        for target in ('observation', 'original-binding', 'original-certificate'):
            with self.subTest(target=target), alias_fixture() as fixture:
                data = self.data(fixture)
                if target == 'observation':
                    fixture.receipt.write_bytes(fixture.receipt.read_bytes() + b' ')
                elif target == 'original-binding':
                    Path(fixture.rows[0]['physical_path']).write_bytes(b'different original evidence')
                else:
                    Path(fixture.root / fixture.observation['representative_original_certificate']['path']).write_bytes(b'changed certificate')
                with self.assertRaises(runtime.PackagingHold):
                    if target == 'observation':
                        data.alias_guard()
                    else:
                        # The full original-byte helper is used at startup and
                        # source/operation boundaries. Fast per-read alias
                        # identity checks are not scientific input admission.
                        data.assert_current()

    def test_hash_bound_receipt_cannot_add_a_second_alias_whitelist(self):
        with alias_fixture() as fixture:
            value = dict(fixture.observation)
            value['allowed_aliases'] = [str(fixture.alias), str(fixture.base / 'another')]
            fixture.receipt.write_text(json.dumps(value, sort_keys=True))
            changed = {**fixture.binding, 'sha256': runtime.sha(fixture.receipt.read_bytes())}
            with patch.object(runtime, 'DATA_ALIAS_OBSERVATION', changed):
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_HISTORICAL_DATA_ALIAS_OBSERVATION'):
                    catalog.ScientificInputData(fixture.root, fixture.context,
                                               data_alias_observation=changed)

    def test_unknown_alias_and_alias_leaf_or_child_are_rejected(self):
        for target in ('other-root-alias', 'alias-child', 'alias-leaf', 'physical-child'):
            with self.subTest(target=target), alias_fixture() as fixture:
                data = self.data(fixture)
                if target == 'other-root-alias':
                    other = fixture.base / 'unapproved-root'
                    other.symlink_to(fixture.root)
                    path = other / fixture.physical.relative_to(fixture.root)
                elif target == 'alias-child':
                    (fixture.root / 'linked-inputs').symlink_to(fixture.root / 'inputs')
                    path = fixture.alias / 'linked-inputs/scientific.lean'
                elif target == 'alias-leaf':
                    (fixture.root / 'linked.lean').symlink_to(fixture.physical)
                    path = fixture.alias / 'linked.lean'
                else:
                    (fixture.root / 'linked-inputs').symlink_to(fixture.root / 'inputs')
                    path = fixture.root / 'linked-inputs/scientific.lean'
                with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_REGULAR_PATH'):
                    data.record(path)

    def test_recreated_retargeted_removed_or_directory_alias_holds_before_read(self):
        for mode in ('recreated', 'retargeted', 'removed', 'directory'):
            with self.subTest(mode=mode), alias_fixture() as fixture:
                data = self.data(fixture)
                data.record(fixture.logical)
                fixture.alias.unlink()
                if mode == 'recreated':
                    fixture.alias.symlink_to(fixture.root.name)
                elif mode == 'retargeted':
                    other = fixture.base / 'other'
                    other.mkdir()
                    (other / 'inputs').mkdir()
                    (other / 'inputs/scientific.lean').write_bytes(fixture.physical.read_bytes())
                    fixture.alias.symlink_to(other.name)
                elif mode == 'directory':
                    (fixture.alias / 'inputs').mkdir(parents=True)
                    (fixture.alias / 'inputs/scientific.lean').write_bytes(fixture.physical.read_bytes())
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                    data.record(fixture.logical)

    def test_alias_metadata_change_cannot_reuse_the_same_link_target(self):
        with alias_fixture() as fixture:
            data = self.data(fixture)
            data.record(fixture.logical)
            stat = fixture.alias.lstat()
            os.utime(fixture.alias, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000), follow_symlinks=False)
            with self.assertRaisesRegex(runtime.PackagingHold, 'HISTORICAL_DATA_ALIAS'):
                data.assert_current()

    def test_identity_change_after_actual_physical_read_holds_without_committing_a_row(self):
        for mode in ('alias-recreated', 'physical-replaced', 'physical-parent-symlink'):
            with self.subTest(mode=mode), alias_fixture() as fixture:
                data = self.data(fixture)
                original_read = Path.read_bytes
                injected = []

                def read_then_change(path):
                    raw = original_read(path)
                    if path == fixture.physical and not injected:
                        injected.append(True)
                        if mode == 'alias-recreated':
                            fixture.alias.unlink()
                            fixture.alias.symlink_to(fixture.root.name)
                        elif mode == 'physical-replaced':
                            replacement = fixture.root / 'replacement.lean'
                            replacement.write_bytes(raw)
                            os.replace(replacement, fixture.physical)
                        else:
                            # The file inode/bytes/timestamps remain exact, but
                            # the previously regular parent becomes a link.
                            # A file-stat-only race check must not admit it.
                            moved = fixture.root / 'original-inputs'
                            fixture.physical.parent.rename(moved)
                            fixture.physical.parent.symlink_to(moved.name)
                    return raw

                with patch.object(Path, 'read_bytes', read_then_change):
                    with self.assertRaisesRegex(runtime.PackagingHold,
                                                'HISTORICAL.*ALIAS|SCIENTIFIC_INPUT_READ_RACE|SCIENTIFIC_INPUT_REGULAR_PATH'):
                        data.record(fixture.logical)
                self.assertEqual(injected, [True])
                self.assertNotIn(str(fixture.logical), data.inputs)
                self.assertFalse(catalog._HASHING.get())

    def test_alias_read_cannot_reuse_changed_bytes_or_replaced_physical_identity(self):
        for mode in ('bytes', 'inode', 'physical-symlink'):
            with self.subTest(mode=mode), alias_fixture() as fixture:
                data = self.data(fixture)
                data.record(fixture.logical)
                raw = fixture.physical.read_bytes()
                if mode == 'bytes':
                    fixture.physical.write_bytes(b'changed actual scientific DATA')
                else:
                    replacement = fixture.root / 'replacement.lean'
                    replacement.write_bytes(raw)
                    if mode == 'inode':
                        os.replace(replacement, fixture.physical)
                    else:
                        fixture.physical.unlink()
                        fixture.physical.symlink_to(replacement)
                with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT'):
                    data.assert_current()

    def test_observed_absence_through_exact_alias_is_not_rebaselined(self):
        with alias_fixture() as fixture:
            data = self.data(fixture)
            logical = fixture.alias / 'inputs/absent.json'
            data.record(logical)
            row = data.inputs[str(logical)]
            self.assertFalse(row['exists'])
            self.assertEqual(row['physical_path'], str(fixture.root / 'inputs/absent.json'))
            self.assertEqual(row['historical_alias_identity'], fixture.observation['identity'])
            (fixture.root / 'inputs/absent.json').write_bytes(b'new unapproved input')
            with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_CHANGED'):
                data.assert_current()

    def test_absent_path_appearing_during_post_path_guard_cannot_escape_original_read_observation(self):
        with alias_fixture() as fixture:
            data = self.data(fixture)
            physical = fixture.root / 'inputs/absent.json'
            logical = fixture.alias / 'inputs/absent.json'
            original_read = Path.read_bytes
            receipt_reads = []

            def read_then_create(path):
                raw = original_read(path)
                if path == fixture.receipt:
                    receipt_reads.append(True)
                    if len(receipt_reads) == 2:
                        # This is the real descriptor read in the post-path
                        # guard, after the leaf was observed absent. The
                        # original pending open would otherwise read these
                        # new bytes while its captured row still says absent.
                        physical.write_bytes(b'new temporary bytes not observed by the original open')
                return raw

            with patch.object(Path, 'read_bytes', read_then_create), self.actual_read_capture(data):
                with self.assertRaisesRegex(runtime.PackagingHold,
                                            'SCIENTIFIC_INPUT.*RACE|SCIENTIFIC_INPUT_CHANGED'):
                    logical.read_bytes()
            self.assertEqual(len(receipt_reads), 2)
            self.assertTrue(physical.is_file())
            self.assertNotIn(str(logical), data.inputs)
            self.assertIsNone(catalog._READ_CAPTURE.get())
            self.assertFalse(catalog._HASHING.get())

    def test_new_actual_run_inventory_entry_still_holds_after_alias_read(self):
        with alias_fixture() as fixture:
            data = self.data(fixture)
            mirror = fixture.base / 'science'
            mirror.mkdir()
            papers = fixture.root / 'science-engine/07_nightly_engine/compound research papers'
            run = papers / 'Run-117'
            run.mkdir(parents=True)
            (run / 'paper.pdf').write_bytes(b'original synthetic paper')
            certs = fixture.root / 'RESEARCH_PIPELINE_v2/lean_certificates'
            corpus = SimpleNamespace(GENERATION_ROOT=mirror,
                                     discover=lambda root: (sorted(root.rglob('*.lean')), [], []))
            data.capture_inventory(corpus, certs)
            data.record(fixture.logical)
            (run / 'new-optional-paper.pdf').write_bytes(b'unapproved added input')
            with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                data.assert_current()

    def test_alias_identity_is_rechecked_before_and_after_canonical_cas(self):
        for phase in ('before', 'after'):
            with self.subTest(phase=phase), alias_fixture() as fixture:
                data = self.data(fixture)
                canonical = fixture.root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                canonical.write_bytes(b'{"before":true}')
                before = runtime.sha(canonical.read_bytes())
                after_bytes = b'{"after":true}'
                data.record(canonical)
                data.record(fixture.logical)
                if phase == 'after':
                    data.authorize_cas(canonical, before, runtime.sha(after_bytes))
                    canonical.write_bytes(after_bytes)
                fixture.alias.unlink()
                fixture.alias.symlink_to(fixture.root.name)
                with self.assertRaisesRegex(runtime.PackagingHold, 'HISTORICAL.*ALIAS'):
                    if phase == 'before':
                        data.authorize_cas(canonical, before, runtime.sha(after_bytes))
                    else:
                        data.finish_cas()
                self.assertEqual(canonical.read_bytes(), b'{"before":true}' if phase == 'before' else after_bytes)
                # V006 canonical DATA uses no historical-alias permission.
                # An AFTER failure retains the exact already-completed CAS,
                # then the global authority guard rejects final admission.
                expected = [] if phase == 'before' else [{'path': str(canonical),
                    'before': before, 'after': runtime.sha(after_bytes)}]
                self.assertEqual(data.cas_events, expected)

    def test_normal_final_manifest_keeps_alias_and_input_identity_and_rejects_change(self):
        with alias_fixture() as fixture:
            data = self.data(fixture)
            data.record(fixture.logical)
            data.retain_manifest()
            data.retain_final(False)
            manifest = json.loads((fixture.output / 'SCIENTIFIC_INPUT_DATA_FINAL.json').read_bytes())
            self.assertEqual(manifest['status'], 'COMPLETE_REHASHED_OPERATION_INPUT_DATA')
            self.assertFalse(manifest['admission_cached'])
            self.assertEqual(manifest['historical_alias'], fixture.observation)
            self.assertEqual(manifest['data_alias_observation'], fixture.binding)
            self.assertEqual(manifest['inputs'][0]['path'], str(fixture.logical))
        with alias_fixture() as fixture:
            data = self.data(fixture)
            data.record(fixture.logical)
            fixture.alias.unlink()
            fixture.alias.symlink_to(fixture.root.name)
            with self.assertRaisesRegex(runtime.PackagingHold, 'HISTORICAL_DATA_ALIAS'):
                data.retain_final(False)
            self.assertFalse((fixture.output / 'SCIENTIFIC_INPUT_DATA_FINAL.json').exists())

    def test_constructor_failure_closes_real_observation_factory_without_tokens_or_fake_manifest(self):
        for mode in ('missing', 'stale'):
            with self.subTest(mode=mode), alias_fixture() as fixture:
                replay = default_fixtures.ObservationReplayTests()
                stack, context, requests, clock, output = replay.setup_context(
                    fixture.root, folder='constructor-failure-' + mode, begin=False)
                with stack:
                    fixture.alias.unlink()
                    if mode == 'stale':
                        fixture.alias.symlink_to(fixture.root.name)
                    entered = []
                    with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                        with catalog.operation_scope(fixture.root, {'synthetic_profile': True}, context):
                            entered.append(True)
                    self.assertEqual(entered, [])
                    with self.assertRaisesRegex(runtime.PackagingHold, 'OBSERVATION_OPERATION_ALREADY_CLOSED'):
                        context.begin_observation_operation()
                    with self.assertRaisesRegex(runtime.PackagingHold, 'ONE_ACTIVE_OBSERVATION_OPERATION_REQUIRED'):
                        context.owner_getter('24000001', 'application/json')
                    self.assertEqual(requests, [])
                    self.assertIsNone(catalog._SCIENCE.get())
                    self.assertIsNone(catalog._READ_CAPTURE.get())
                    self.assertIsNone(catalog._OPERATION.get())
                    self.assertFalse(list(output.rglob('SCIENTIFIC_INPUT_DATA*.json')))


if __name__ == '__main__':
    unittest.main()
