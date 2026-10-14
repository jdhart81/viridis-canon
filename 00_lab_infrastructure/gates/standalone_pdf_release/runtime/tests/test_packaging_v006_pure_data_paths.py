"""Immutable DATA and fresh sampling fixtures; no live science or admission.

All filesystem changes are confined to resolved temporary roots. The exact
frozen V005 read/guard ASTs are used only for a synthetic before/after workload;
no original scientific module, caller source factory or real state is loaded.
"""
import ast
import cProfile
import contextlib
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
import pstats
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from common.runtime_history import historical_bytes
import packaging_runtime as runtime
import packaging_catalog as catalog
import test_packaging_v003_data_alias as aliases


def fixed_v005_function(file, name, namespace, *, method=False):
    raw = historical_bytes('v005', file)
    expected = {'packaging_runtime.py': '409cd52b97474d28d2dbcf70a9005ea73ab6d9228e30aca757931d9c2fea6910',
                'packaging_catalog.py': 'f4c292657703180eb1b34d80fd6080216744db96a872e76e83b4761479410ff7'}
    if runtime.sha(raw) != expected[file]: raise AssertionError('Frozen V005 fixture AST source changed')
    tree = ast.parse(raw)
    nodes = tree.body
    if method:
        nodes = next(node for node in nodes if isinstance(node, ast.ClassDef)
                     and node.name == 'ScientificInputData').body
    node = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'frozen_v005_synthetic_' + name, 'exec'), namespace)
    return namespace[name]


def synthetic_guard_benchmark(iterations=150):
    """Full reads/hash/link checks in both paths; timings prove fixture cost only."""
    namespace = {key: getattr(runtime, key) for key in ('Path', 'need', 'sha', 'file_identity', '_JSON_DATA')}
    old_read = fixed_v005_function('packaging_runtime.py', 'read_data_file', namespace)
    old_parse = fixed_v005_function('packaging_runtime.py', 'parse_json_data', namespace)
    def old_object(root, binding):
        path, raw = old_read(root, binding['path'], expected_sha256=binding['sha256'])
        return path, raw, old_parse(root, path, raw)
    old_runtime = SimpleNamespace(**{key: getattr(runtime, key) for key in
        ('need', 'data_alias_identity', 'require_data_alias_observation')}, object_at=old_object)
    old_guard = fixed_v005_function('packaging_catalog.py', 'alias_guard',
                                   {'runtime': old_runtime, '_HASHING': catalog._HASHING, 'Path': Path}, method=True)
    result = {'scope': 'TEMPORARY_FIXTURE_DATA_ONLY', 'runtime_admission': False,
              'original_science_imports': 0, 'network_requests': 0, 'iterations_per_trial': iterations}
    with aliases.alias_fixture() as f:
        # Expand only harmless fixture scope DATA to approximately the actual
        # descriptor size; all original closed descriptor fields are retained.
        observation = dict(f.observation)
        observation['scope'] = 'synthetic descriptor ' + 'x' * 1800
        f.receipt.write_text(json.dumps(observation, sort_keys=True))
        binding = {**f.binding, 'sha256': runtime.sha(f.receipt.read_bytes())}
        with patch.object(runtime, 'DATA_ALIAS_OBSERVATION', binding):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=binding)
            old = SimpleNamespace(root=f.root, alias_binding=binding, alias_observation=observation)
            result['descriptor_bytes'] = f.receipt.stat().st_size
            times = {'v005': [], 'v006': []}; counts = {}
            actual_read = Path.read_bytes
            for trial in range(3):
                for version in (('v005', 'v006') if trial % 2 == 0 else ('v006', 'v005')):
                    reads = []
                    def checked_read(path):
                        if path == f.receipt: reads.append(1)
                        return actual_read(path)
                    with runtime.json_data_scope(f.root), patch.object(Path, 'read_bytes', checked_read):
                        started = time.perf_counter()
                        for _ in range(iterations):
                            (old_guard(old) if version == 'v005' else data.alias_guard())
                        elapsed = time.perf_counter() - started
                    times[version].append(elapsed); counts[version] = len(reads)
            result.update(times_seconds=times, median_seconds={k: statistics.median(v) for k, v in times.items()},
                          fresh_full_descriptor_reads_per_trial=counts)
            result['median_speedup'] = result['median_seconds']['v005'] / result['median_seconds']['v006']
    return result


def synthetic_complete_input_benchmark(files=160, trials=3):
    """Exact old additive DATA class vs new class, temporary full row replay."""
    namespace = {key: getattr(runtime, key) for key in ('Path', 'need', 'sha', 'file_identity', '_JSON_DATA', 're', 'json')}
    for name in ('read_data_file', 'parse_json_data', 'read', 'object_at', 'json_file'):
        fixed_v005_function('packaging_runtime.py', name, namespace)
    class OldRuntime:
        def __getattr__(self, name): return namespace[name] if name in namespace else getattr(runtime, name)
    raw = historical_bytes('v005', 'packaging_catalog.py')
    if runtime.sha(raw) != 'f4c292657703180eb1b34d80fd6080216744db96a872e76e83b4761479410ff7':
        raise AssertionError('Frozen V005 DATA source changed')
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == 'ScientificInputData')
    old_namespace = {'runtime': OldRuntime(), '_HASHING': catalog._HASHING,
                     'os': os, 'Path': Path, 'json': json, '_SCIENCE': catalog._SCIENCE,
                     '_READ_CAPTURE': catalog._READ_CAPTURE}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'frozen_v005_fixture_DATA_class', 'exec'), old_namespace)
    old_class = old_namespace['ScientificInputData']
    result = {'scope': 'TEMPORARY_FULL_INPUT_AND_INVENTORY_FIXTURE_ONLY', 'files': files,
              'original_science_imports': 0, 'network_requests': 0, 'runtime_admission': False}
    with aliases.alias_fixture() as f:
        paths = []
        for number in range(files):
            path = f.root / 'temporary/deep/input/tree' / ('file-' + str(number) + '.lean')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((('synthetic input ' + str(number) + '\n') * 450).encode())
            paths.append(path)
        certificate = f.root / 'RESEARCH_PIPELINE_v2/lean_certificates'
        ledger = f.root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        ledger.write_text(json.dumps({'publication_entities': [],
                                     'file_entities': [{'path': str(p), 'hashes': {'fixture': number}}
                                                       for number, p in enumerate(paths)]}))
        corpus = SimpleNamespace(GENERATION_ROOT=str(f.base / 'generation'),
                                 discover=lambda root: (sorted(root.rglob('*.lean')), [], []))
        times, profiles = {'v005': [], 'v006': []}, {}
        for trial in range(trials):
            for version in (('v005', 'v006') if trial % 2 == 0 else ('v006', 'v005')):
                with runtime.json_data_scope(f.root):
                    data = (old_class if version == 'v005' else catalog.ScientificInputData)(
                        f.root, f.context, data_alias_observation=f.binding)
                    data.capture_inventory(corpus, certificate)
                    for path in paths: data.record(path)
                    timer = time.perf_counter(); data.assert_current(); times[version].append(time.perf_counter() - timer)
                    if trial == 0:
                        profiler = cProfile.Profile(); profiler.runcall(data.assert_current)
                        stats = pstats.Stats(profiler)
                        profiles[version] = sorted(({'function': ':'.join(map(str, key)), 'calls': row[1],
                                                     'self_seconds': row[2], 'cumulative_seconds': row[3]}
                                                    for key, row in stats.stats.items()),
                                                   key=lambda r: r['self_seconds'], reverse=True)[:15]
                    if len(data.inputs) != files: raise AssertionError('Fixture full population changed')
        result.update(times_seconds=times, median_seconds={k: statistics.median(v) for k, v in times.items()},
                      fixture_profile_top_self_seconds=profiles)
        result['median_speedup'] = result['median_seconds']['v005'] / result['median_seconds']['v006']
    return result


def synthetic_source_and_projection_benchmark(tree_rows=3545, file_rows=21924):
    """Complete shaped Git proof and ledger DATA, with every fresh file check.

    This measures the named source/JSON components, not the complete original
    runtime helper chain. No original module is executed to obtain a timing.
    """
    result = {'scope': 'TEMPORARY_SOURCE_PROOF_AND_LEDGER_DATA_COMPONENTS_ONLY',
              'tree_rows': tree_rows, 'file_rows': file_rows, 'runtime_admission': False,
              'original_science_imports': 0, 'network_requests': 0}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        modules, rows = [], []
        for name in sorted(runtime.MODULE_NAMES):
            path = root / 'synthetic' / name; path.parent.mkdir(exist_ok=True)
            raw = b'# synthetic source proof bytes only\n'; path.write_bytes(raw)
            row = {'name': name, 'path': str(path), 'sha256': runtime.sha(raw), 'git_path': runtime.GIT_PREFIX + name}
            modules.append(row); rows.append({'path': row['git_path'], 'type': 'blob', 'mode': '100644',
                'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()})
        rows.extend({'path': 'synthetic/unused-' + str(number), 'type': 'blob', 'mode': '100644', 'sha': 'c' * 40}
                    for number in range(tree_rows - len(rows)))
        def put(name, value):
            path = root / name; path.write_text(json.dumps(value))
            return {'path': str(path), 'sha256': runtime.sha(path.read_bytes())}
        origin = {'pull_request': put('pr.json', {'state': 'MERGED', 'baseRefName': 'main', 'number': 999,
            'url': 'https://github.com/jdhart81/viridis-canon/pull/999', 'mergeCommit': {'oid': 'a' * 40},
            'statusCheckRollup': [{'name': name, 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}
                                 for name in runtime.REQUIRED_CHECKS]}),
            'merge_commit': put('commit.json', {'sha': 'a' * 40, 'tree': {'sha': 'b' * 40}}),
            'tree': put('tree.json', {'sha': 'b' * 40, 'truncated': False, 'tree': rows})}
        namespace = {key: getattr(runtime, key) for key in
                     ('Path', 'need', 'sha', 'file_identity', '_JSON_DATA', 're', 'json', 'hashlib', 'REQUIRED_CHECKS')}
        for name in ('read_data_file', 'parse_json_data', 'read', 'object_at', 'source_proof'):
            fixed_v005_function('packaging_runtime.py', name, namespace)
        old_proof = namespace['source_proof']; times = {'v005': [], 'v006': []}
        for trial in range(3):
            for version, function in (('v005', old_proof), ('v006', runtime.source_proof)):
                with runtime.json_data_scope(root):
                    function(root, origin, modules)  # cold parses remain real
                    start = time.perf_counter()
                    for _ in range(5): function(root, origin, modules)
                    times[version].append(time.perf_counter() - start)
        result['source_proof_five_replays_times_seconds'] = times
        result['source_proof_median_speedup'] = statistics.median(times['v005']) / statistics.median(times['v006'])
        path = root / 'ledger.json'
        value = {'publication_entities': [{'path': 'paper-' + str(i), 'status': 'DEBT'} for i in range(92)],
                 'file_entities': [{'path': 'source-' + str(i), 'sha256': '0' * 64,
                                    'nested': {'fixture': 'unchanged synthetic data ' * 20}} for i in range(file_rows)]}
        path.write_text(json.dumps(value)); result['ledger_bytes'] = path.stat().st_size
        times = {'whole_mutable_export': [], 'publication_branch_export': []}
        with runtime.json_data_scope(root):
            runtime.json_file(root, path)  # complete cold syntax parse
            for trial in range(3):
                for key in times:
                    start = time.perf_counter()
                    if key == 'whole_mutable_export': actual = runtime.json_file(root, path)[2]['publication_entities']
                    else: actual = runtime.json_file_field(root, path, 'publication_entities', [])[2]
                    times[key].append(time.perf_counter() - start)
                    if actual != value['publication_entities']: raise AssertionError('Actual branch changed')
        result['ledger_projection_times_seconds'] = times
        result['ledger_projection_median_speedup'] = (statistics.median(times['whole_mutable_export']) /
                                                       statistics.median(times['publication_branch_export']))
    return result


def synthetic_repeated_observed_cohort_benchmark(files=112, notes=6):
    """Repeated policy-shaped opens through the genuine unchanged observer.

    Counts repeated read events, not just unique rows. The two complete passes
    model audited-input admission plus _finish; actual input sizes/counts and
    real policy predicates are not substituted or executed by this workload.
    """
    namespace = {key: getattr(runtime, key) for key in ('Path', 'need', 'sha', 'file_identity', '_JSON_DATA', 're', 'json')}
    for name in ('read_data_file', 'parse_json_data', 'read', 'object_at', 'json_file'):
        fixed_v005_function('packaging_runtime.py', name, namespace)
    class OldRuntime:
        def __getattr__(self, name): return namespace[name] if name in namespace else getattr(runtime, name)
    raw = historical_bytes('v005', 'packaging_catalog.py')
    if runtime.sha(raw) != 'f4c292657703180eb1b34d80fd6080216744db96a872e76e83b4761479410ff7':
        raise AssertionError('Frozen V005 DATA source changed')
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == 'ScientificInputData')
    old_namespace = {'runtime': OldRuntime(), '_HASHING': catalog._HASHING,
                     'os': os, 'Path': Path, 'json': json, '_SCIENCE': catalog._SCIENCE,
                     '_READ_CAPTURE': catalog._READ_CAPTURE}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'frozen_v005_fixture_observed_DATA', 'exec'), old_namespace)
    old_class = old_namespace['ScientificInputData']
    result = {'scope': 'TEMPORARY_REPEATED_AUDITED_COHORT_OPEN_OBSERVER_ONLY',
              'runtime_admission': False, 'original_science_imports': 0, 'network_requests': 0,
              'unique_fixture_inputs': files, 'note_repeats': notes, 'passes_per_note': 2,
              'actual_audit_cohort_substituted': False}
    with aliases.alias_fixture() as f:
        paths = []
        for i in range(files):
            size = 1048576 if i % 28 == 0 else 65536 if i % 7 == 0 else 8192
            path = f.root / 'reports/verification-coverage/synthetic-audited-cohort/inputs/deep' / ('input-' + str(i))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((str(i) + '\n').encode().ljust(size, b'x')); paths.append(path)
        result['bytes_per_cohort'] = sum(p.stat().st_size for p in paths)
        times = {'v005': [], 'v006': []}; observed = {}
        for trial in range(3):
            for version in (('v005', 'v006') if trial % 2 == 0 else ('v006', 'v005')):
                with runtime.json_data_scope(f.root):
                    data = (old_class if version == 'v005' else catalog.ScientificInputData)(
                        f.root, f.context, data_alias_observation=f.binding)
                    count = [0]; record = data.record
                    def counted(path): count[0] += 1; return record(path)
                    data.record = counted
                    token = catalog._READ_CAPTURE.set(data)
                    try:
                        start = time.perf_counter()
                        for _ in range(notes):
                            for _ in range(2):
                                for path in paths:
                                    if len(path.read_bytes()) < 8192: raise AssertionError('Fixture bytes changed')
                        times[version].append(time.perf_counter() - start)
                    finally: catalog._READ_CAPTURE.reset(token)
                    observed[version] = {'observed_original_opens': count[0], 'retained_unique_rows': len(data.inputs)}
                    if count[0] != files * notes * 2 or len(data.inputs) != files:
                        raise AssertionError('Repeated open or full input coverage changed')
        result.update(times_seconds=times, median_seconds={k: statistics.median(v) for k, v in times.items()},
                      observed_open_and_unique_row_counts=observed)
        result['median_speedup'] = result['median_seconds']['v005'] / result['median_seconds']['v006']
        result['data_read_events_per_trial'] = files * notes * 2
    return result


class PureDataFreshPathTests(unittest.TestCase):
    def test_ordinary_mutable_json_exports_preserve_non_alphabetic_input_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); path = root / 'ordered.json'
            raw = b'{"z":1,"a":2,"publication_entities":[{"z":3,"a":4}]}'
            path.write_bytes(raw); binding = {'path': str(path), 'sha256': runtime.sha(raw)}
            with runtime.json_data_scope(root):
                for reader in (lambda: runtime.object_at(root, binding)[2],
                               lambda: runtime.json_file(root, path)[2]):
                    self.assertEqual(list(reader()), ['z', 'a', 'publication_entities'])
                rows = runtime.json_file_field(root, path, 'publication_entities', [])[2]
                self.assertEqual(list(rows[0]), ['z', 'a'])
    def test_alias_snapshot_export_mutation_and_holder_replacement_cannot_change_guard(self):
        with aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            exported = data.alias_observation
            exported['identity']['inode'] = -1
            exported['original_binding_readbacks'].clear()
            exported_binding = data.alias_binding; exported_binding['sha256'] = '0' * 64
            for field, value in (('alias_observation', exported), ('alias_binding', exported_binding),
                                 ('_alias_material', runtime.immutable_json_object(exported)),
                                 ('_alias_binding_material', runtime.immutable_json_object(exported_binding))):
                with self.subTest(field=field), self.assertRaises(AttributeError): setattr(data, field, value)
            with self.assertRaises(AttributeError): data._alias_material._value = ('scalar', False)
            with self.assertRaises(AttributeError): del data._alias_material._value
            self.assertEqual(data._alias_material, f.observation)
            for field in ('_alias_material', '_alias_binding_material'):
                with self.subTest(delete=field), self.assertRaises(AttributeError): delattr(data, field)
            # A mutable ordinary DATA dictionary cannot shadow the slot-backed
            # snapshot; this is an actual public cache-holder attack surface.
            data.__dict__['_alias_material'] = runtime.immutable_json_object(exported)
            data.__dict__['_alias_binding_material'] = runtime.immutable_json_object(exported_binding)
            data.alias_guard()
            self.assertEqual(data.alias_observation, f.observation)
            data.alias_guard(complete=True)

    def test_fast_alias_guard_has_full_comparison_fresh_bytes_and_zero_full_descriptor_exports(self):
        with aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            actual_read, actual_thaw = Path.read_bytes, runtime._thaw_json
            reads, exports = [], []
            def read(path):
                if path == f.receipt: reads.append(1)
                return actual_read(path)
            def thaw(value):
                if value[0] == 'object' and len(value[1]) == 15: exports.append(1)
                return actual_thaw(value)
            with patch.object(Path, 'read_bytes', read), patch.object(runtime, '_thaw_json', thaw):
                data.record(f.physical)
                self.assertEqual(reads, [])  # canonical no-link DATA needs no alias permission
                data.record(f.logical)
            self.assertEqual(len(reads), 2)  # before and after the actual historical-alias read
            self.assertEqual(exports, [])
            self.assertEqual(data.inputs[str(f.logical)]['historical_alias_identity'], f.observation['identity'])
            self.assertEqual(data.alias_observation, f.observation)

    def test_alias_descriptor_bytes_identity_unknown_parent_and_link_changes_hold(self):
        for change in ('descriptor-bytes', 'descriptor-recreated', 'alias-recreated', 'alias-retarget', 'parent-link'):
            with self.subTest(change=change), aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
                data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
                if change == 'descriptor-bytes': f.receipt.write_bytes(f.receipt.read_bytes() + b' ')
                elif change == 'descriptor-recreated':
                    replacement = f.receipt.with_name('replacement'); replacement.write_bytes(f.receipt.read_bytes())
                    # Ordinary parser DATA may reparse a changed identity, but
                    # already observed scientific input identity must reject it.
                    data.record(f.receipt); os.replace(replacement, f.receipt)
                elif change == 'alias-recreated':
                    target = os.readlink(f.alias); f.alias.unlink(); f.alias.symlink_to(target)
                elif change == 'alias-retarget':
                    foreign = f.base / 'foreign'; foreign.mkdir(); f.alias.unlink(); f.alias.symlink_to(foreign)
                else:
                    parent = f.physical.parent; moved = parent.with_name('original-inputs')
                    parent.rename(moved); parent.symlink_to(moved)
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                    data.assert_current() if change == 'descriptor-recreated' else data.record(f.logical)

    def test_fixed_lexical_alias_missing_or_replaced_by_directory_never_becomes_canonical(self):
        for mode in ('missing', 'ordinary-directory', 'descriptor-absent'):
            with self.subTest(mode=mode), aliases.alias_fixture() as f:
                data = catalog.ScientificInputData(f.root, f.context,
                    data_alias_observation=None if mode == 'descriptor-absent' else f.binding)
                if mode != 'descriptor-absent':
                    f.alias.unlink()
                    if mode == 'ordinary-directory':
                        f.logical.parent.mkdir(parents=True)
                        f.logical.write_bytes(f.physical.read_bytes())
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)): data.record(f.logical)
                self.assertNotIn(str(f.logical), data.inputs)

    def test_classifier_is_signed_snapshot_not_mutable_module_constant_or_dictionary_shadow(self):
        with aliases.alias_fixture() as f:
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            original_parts = data._alias_path_parts
            foreign = f.base / 'foreign-alias'; foreign.mkdir()
            for field in ('_alias_path_parts',):
                with self.assertRaises(AttributeError): setattr(data, field, foreign.parts)
                with self.assertRaises(AttributeError): delattr(data, field)
            data.__dict__['_alias_path_parts'] = foreign.parts
            self.assertEqual(data._alias_path_parts, original_parts)
            f.alias.unlink(); f.logical.parent.mkdir(parents=True)
            f.logical.write_bytes(f.physical.read_bytes())
            reads = []; original_read = Path.read_bytes
            def read(path):
                if path == f.logical: reads.append('unapproved historical acquisition')
                return original_read(path)
            with patch.object(runtime, 'SCIENTIFIC_ALIAS_PATH', foreign), patch.object(Path, 'read_bytes', read):
                with self.assertRaises(runtime.PackagingHold): data.record(f.logical)
            self.assertEqual(reads, []); self.assertNotIn(str(f.logical), data.inputs)

    def test_canonical_no_link_read_does_not_use_alias_authority_but_global_guard_rejects_drift(self):
        with aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            f.receipt.write_bytes(f.receipt.read_bytes() + b' ')
            data.record(f.physical)
            self.assertIn(str(f.physical), data.inputs)
            with self.assertRaises(runtime.PackagingHold): data.assert_current()
            with self.assertRaises(runtime.PackagingHold): data.record(f.logical)

    def test_alias_descriptor_drift_during_last_canonical_replay_holds_before_boundary_returns(self):
        with aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            data.record(f.physical); original = Path.read_bytes; changed = []
            def read(path):
                raw = original(path)
                if path == f.physical and not changed:
                    f.receipt.write_bytes(original(f.receipt) + b' '); changed.append(True)
                return raw
            with patch.object(Path, 'read_bytes', read):
                with self.assertRaises(runtime.PackagingHold): data.assert_current()
            self.assertTrue(changed)
            self.assertIsNone(data.manifest); self.assertEqual(data.cas_events, [])

    def test_canonical_unknown_parent_link_inserted_during_actual_read_holds_before_row_commit(self):
        with aliases.alias_fixture() as f:
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            original = Path.read_bytes; changed = []
            def read(path):
                raw = original(path)
                if path == f.physical and not changed:
                    parent = f.physical.parent; retained = parent.with_name('retained-inputs')
                    parent.rename(retained); parent.symlink_to(retained); changed.append(True)
                return raw
            with patch.object(Path, 'read_bytes', read):
                with self.assertRaises(runtime.PackagingHold): data.record(f.physical)
            self.assertTrue(changed); self.assertNotIn(str(f.physical), data.inputs)

    def test_complete_alias_guard_still_rehashes_each_original_binding_and_certificate(self):
        with aliases.alias_fixture() as f, runtime.json_data_scope(f.root):
            data = catalog.ScientificInputData(f.root, f.context, data_alias_observation=f.binding)
            actual = Path.read_bytes; reads = []
            def read(path): reads.append(str(path)); return actual(path)
            with patch.object(Path, 'read_bytes', read): data.alias_guard(complete=True)
            self.assertTrue({r['physical_path'] for r in f.rows} <= set(reads))
            certificate = f.root / f.observation['representative_original_certificate']['path']
            self.assertIn(str(certificate), reads)

    def test_source_read_retains_distinct_root_pre_post_and_final_sampling_positions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); path = root / 'file.json'; path.write_bytes(b'{}')
            frames, directories = [], []
            actual, directory = runtime.strict_regular_source_frame, runtime.strict_directory_frame
            def sampled(*args): frames.append(args[2]); return actual(*args)
            def sampled_root(*args): directories.append(args[1]); return directory(*args)
            with runtime.json_data_scope(root), patch.object(runtime, 'strict_regular_source_frame', sampled), \
                    patch.object(runtime, 'strict_directory_frame', sampled_root):
                runtime.object_at(root, {'path': str(path), 'sha256': runtime.sha(b'{}')})
            self.assertEqual(frames, ['REGULAR_CONTAINED_SOURCE'] * 2 + ['SOURCE_HASH_OR_RACE'] * 3)
            self.assertEqual(directories, ['REGULAR_CONTAINED_SOURCE', 'ONE_ACTIVE_JSON_DATA_OPERATION_REQUIRED'])

    def test_each_distinct_sampling_subposition_rejects_external_parent_alias_with_same_inode_leaf(self):
        # The external leaf is a hardlink: same bytes and all six identities.
        # File-only checks would pass, so each distinct fresh ancestry stage is
        # required to reject the temporary outside-root path substitution.
        for stage in range(1, 6):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve(); root = base / 'canonical'; folder = root / 'source'; folder.mkdir(parents=True)
                path = folder / 'material.json'; path.write_bytes(b'{"bound":true}')
                foreign = base / 'external'; foreign.mkdir(); os.link(path, foreign / path.name)
                self.assertEqual(runtime.file_identity(path.stat()), runtime.file_identity((foreign / path.name).stat()))
                real = runtime.strict_regular_source_frame; calls = []
                def sample(*args):
                    calls.append(1)
                    if len(calls) == stage:
                        folder.rename(root / 'retained-source'); folder.symlink_to(foreign)
                    return real(*args)
                with runtime.json_data_scope(root), patch.object(runtime, 'strict_regular_source_frame', sample):
                    with self.assertRaises(runtime.PackagingHold):
                        runtime.read(root, {'path': str(path), 'sha256': runtime.sha(path.read_bytes())})
                self.assertEqual(len(calls), stage)

    def test_lexical_tuple_reuse_is_not_a_filesystem_pass_and_missing_source_is_typed_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); folder = root / 'source'; folder.mkdir(); path = folder / 'file.json'
            path.write_bytes(b'{}'); binding = {'path': str(path), 'sha256': runtime.sha(b'{}')}
            geometry = runtime.lexical_ancestors(path)
            self.assertIs(geometry, runtime.lexical_ancestors(path))
            runtime.read(root, binding)
            path.unlink()
            with self.assertRaisesRegex(runtime.PackagingHold, 'REGULAR_CONTAINED_SOURCE'): runtime.read(root, binding)
            path.write_bytes(b'{}'); moved = root / 'actual-source'; folder.rename(moved); folder.symlink_to(moved)
            with self.assertRaisesRegex(runtime.PackagingHold, 'REGULAR_CONTAINED_SOURCE'): runtime.read(root, binding)
            self.assertIs(geometry, runtime.lexical_ancestors(path))

    def test_projection_checks_whole_json_and_full_bytes_but_only_exports_requested_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); path = root / 'ledger.json'
            value = {'publication_entities': [{'path': 'actual-paper', 'proof': {'status': 'DEBT'}}],
                     'file_entities': [{'irrelevant_to_inventory': n} for n in range(200)]}
            path.write_text(json.dumps(value))
            actual_read, actual_thaw = Path.read_bytes, runtime._thaw_json; reads, full_exports = [], []
            def read(p):
                if p == path: reads.append(1)
                return actual_read(p)
            def thaw(v):
                if v[0] == 'object' and {k for k, _ in v[1]} == set(value): full_exports.append(1)
                return actual_thaw(v)
            with runtime.json_data_scope(root), patch.object(Path, 'read_bytes', read), patch.object(runtime, '_thaw_json', thaw):
                first = runtime.json_file_field(root, path, 'publication_entities', [])[2]
                first[0]['proof']['status'] = 'CALLER_ONLY'
                second = runtime.json_file_field(root, path, 'publication_entities', [])[2]
                self.assertEqual(second, value['publication_entities'])
                self.assertEqual(len(reads), 2); self.assertEqual(full_exports, [])
                path.write_bytes(b'{"publication_entities":[],"unrequested":{malformed}')
                with self.assertRaises(json.JSONDecodeError): runtime.json_file_field(root, path, 'publication_entities', [])

    def test_projection_material_is_operation_scoped_and_changed_unrequested_bytes_are_reparsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); path = root / 'ledger.json'
            first = b'{"publication_entities":[1],"other":true}'; path.write_bytes(first)
            with runtime.json_data_scope(root) as view:
                self.assertEqual(runtime.json_file_field(root, path, 'publication_entities', [])[2], [1])
                path.write_bytes(b'{"publication_entities":[1],"other":false}')
                self.assertEqual(runtime.json_file_field(root, path, 'publication_entities', [])[2], [1])
                self.assertEqual(view['parses'], 2)
            with runtime.json_data_scope(root) as view:
                runtime.json_file_field(root, path, 'publication_entities', [])
                self.assertEqual(view['parses'], 1); self.assertEqual(view['parse_reuses'], 0)

    def test_synthetic_combined_guard_workload_retains_equal_full_read_counts(self):
        result = synthetic_guard_benchmark(iterations=20)
        self.assertEqual(result['fresh_full_descriptor_reads_per_trial'], {'v005': 20, 'v006': 20})
        self.assertGreater(result['median_seconds']['v005'], 0)
        self.assertGreater(result['median_seconds']['v006'], 0)
        # Timing is diagnostic, not an acceptance threshold or live fit proof.


if __name__ == '__main__': unittest.main()
