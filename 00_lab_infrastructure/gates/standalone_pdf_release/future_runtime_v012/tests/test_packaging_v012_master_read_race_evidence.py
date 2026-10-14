"""Private synthetic filesystem tests; no runtime/original module import.

Only the hash-bound proposal's DATA record/path/diagnostic AST bodies are used.
The runtime error/lexical-path seam is an explicit fixture, never admission.
"""
import ast
import contextvars
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))
from common.runtime_history import historical_bytes
HASHING = contextvars.ContextVar('synthetic_internal_hash_read', default=False)
READ_CAPTURE = contextvars.ContextVar('synthetic_capture_marker', default=None)

class FixtureHold(ValueError):
    pass

def need(ok, reason):
    if not ok:
        raise FixtureHold('SYNTHETIC_RUNTIME_' + reason)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def links(path):
    """All fresh fixture components; no authority/verdict/filesystem cache."""
    result = []
    for component in (path, *path.parents):
        try:
            value = os.lstat(component)
        except OSError as exc:
            if exc.errno not in (errno.ENOENT, errno.ENOTDIR):
                raise
            continue
        if stat.S_ISLNK(value.st_mode):
            result.append(component)
    return result

def load_data_class(path):
    source = path.decode('utf-8') if isinstance(path, bytes) else path.read_text()
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ScientificInputData')
    wanted = {'record', 'data_path', '_commit_checked_row', '_raise_input_read_race', '_retain_input_read_race'}
    selected = copy.deepcopy([n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in wanted])
    model = ast.ClassDef(name='FixtureData', bases=[], keywords=[], body=selected, decorator_list=[])
    namespace = {'Path': Path, 'runtime': types.SimpleNamespace(need=need, sha=sha, PackagingHold=FixtureHold,
                   fresh_symlink_components=links), '_HASHING': HASHING, 'deepcopy': copy.deepcopy,
                 'os': os, 'time': time, 'json': json}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[model], type_ignores=[])),
                 '<hash-bound-synthetic-data-methods-only>', 'exec'), namespace)
    return namespace['FixtureData']

def identity(sample):
    return dict(zip(('device', 'inode', 'mode', 'bytes', 'mtime_ns', 'ctime_ns'),
                    (sample.st_dev, sample.st_ino, sample.st_mode, sample.st_size,
                     sample.st_mtime_ns, sample.st_ctime_ns)))

class ReadRaceEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate_path = HERE.parent / 'packaging_catalog.py'
        assert sha(cls.candidate_path.read_bytes()) == '708442313d8ae717fc1b6152bfdfceaac46ff7726a1d1742701b7f5c67db0803'
        original = historical_bytes('v011', 'packaging_catalog.py')
        assert sha(original) == '6816ea4868dd4d1262084348023e0132a0aa638843bf6dc9cfb025d05c086346'
        cls.proposal_class = load_data_class(cls.candidate_path)
        cls.original_class = load_data_class(original)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.owner = self.root / 'evidence'
        self.owner.mkdir()
        self.input = self.root / 'ORIGINAL_FUNCTION_RESULT.json'
        self.input.write_bytes(b'{"synthetic":true}\n')
        self.before_raw = self.input.read_bytes()
        self.data = self.make_data(self.proposal_class)
        self.capture_token = READ_CAPTURE.set('fixture-parent-capture')

    def tearDown(self):
        self.assertFalse(HASHING.get())
        self.assertEqual(READ_CAPTURE.get(), 'fixture-parent-capture')
        READ_CAPTURE.reset(self.capture_token)
        self.temp.cleanup()

    def make_data(self, cls):
        data = cls()
        data.root = self.root
        data.context = types.SimpleNamespace(owner_evidence_directory=self.owner)
        data.inputs = {}
        data.pending_cas = None
        data.platform_observation = None
        data._alias_path_parts = ('/', '__synthetic_nonexistent_historical_alias__')
        data._alias_material = None
        return data

    def evidence(self):
        rows = list(self.owner.glob('SCIENTIFIC_INPUT_READ_RACE_*.json'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(stat.S_IMODE(rows[0].stat().st_mode), 0o600)
        return rows[0], json.loads(rows[0].read_bytes())

    def changed_after_body(self, data=None):
        data = self.data if data is None else data
        read = Path.read_bytes
        def after(path):
            raw = read(path)
            if path == self.input:
                path.write_bytes(raw + b'ACTUAL_SYNTHETIC_CHANGE\n')
            return raw
        with mock.patch.object(Path, 'read_bytes', after):
            with self.assertRaises(FixtureHold) as caught:
                data.record(self.input)
        return caught.exception

    def changed_at_final_path(self, data=None):
        data = self.data if data is None else data
        method = data.data_path
        count = 0
        def second(path):
            nonlocal count
            value = method(path)
            count += 1
            if count == 2:
                path.write_bytes(self.before_raw + b'FINAL_INTERVAL_CHANGE\n')
            return value
        with mock.patch.object(data, 'data_path', second):
            with self.assertRaises(FixtureHold) as caught:
                data.record(self.input)
        self.assertEqual(count, 2)
        return caught.exception

    def test_unchanged_success_has_no_diagnostic_or_changed_row(self):
        self.data.record(self.input)
        self.assertEqual(self.data.inputs[str(self.input)]['sha256'], sha(self.before_raw))
        self.assertEqual(list(self.owner.iterdir()), [])
        self.assertFalse(hasattr(self.data, 'read_race_diagnostic'))

    def test_real_first_last_change_keeps_exact_primary_hold_and_samples(self):
        first = self.input.stat()
        caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        path, value = self.evidence()
        self.assertEqual(value['phase'], 'BODY_FIRST_LAST')
        self.assertEqual(value['first'], identity(first))
        self.assertEqual(value['last'], identity(self.input.stat()))
        self.assertIsNone(value['final'])
        self.assertNotEqual(value['first'], value['last'])
        self.assertEqual(value['acquired_raw_sha256'], sha(self.before_raw))
        self.assertEqual(value['acquired_raw_bytes'], len(self.before_raw))
        self.assertEqual(value['logical_path'], str(self.input))
        self.assertEqual(value['physical_path'], str(self.input))
        self.assertEqual(self.data.inputs, {})
        self.assertEqual(self.data.read_race_diagnostic['sha256'], sha(path.read_bytes()))

    def test_real_final_change_stores_single_actual_sample_same_as_gate(self):
        first = self.input.stat()
        stat_call = Path.stat
        samples = []
        direct_samples = []
        def observed(path, *args, **kwargs):
            result = stat_call(path, *args, **kwargs)
            if path == self.input:
                samples.append(identity(result))
                caller = sys._getframe(1).f_code
                if (caller.co_name == 'record'
                        and caller.co_filename == '<hash-bound-synthetic-data-methods-only>'):
                    direct_samples.append(identity(result))
            return result
        with mock.patch.object(Path, 'stat', observed):
            caught = self.changed_at_final_path()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        _, value = self.evidence()
        self.assertEqual(value['phase'], 'FINAL_LEAF_AFTER_PATH')
        self.assertEqual(value['first'], identity(first))
        self.assertEqual(value['first'], value['last'])
        self.assertNotEqual(value['final'], value['last'])
        self.assertEqual(value['final'], samples[-1])
        # Count the source method's three explicit samples independently of
        # pathlib's version-dependent exists/is_file probes. The next test
        # separately requires equal total target observations in old and new.
        self.assertEqual(len(direct_samples), 3)
        self.assertEqual(value['final'], direct_samples[-1])
        self.assertEqual(self.data.inputs, {})

    def test_old_and_new_real_failures_have_same_hold_and_target_sample_count(self):
        stat_call = Path.stat
        def run(cls):
            self.input.write_bytes(self.before_raw)
            samples = []
            def observed(path, *args, **kwargs):
                value = stat_call(path, *args, **kwargs)
                if path == self.input:
                    samples.append(identity(value))
                return value
            with mock.patch.object(Path, 'stat', observed):
                caught = self.changed_at_final_path(self.make_data(cls))
            return str(caught), len(samples)
        self.assertEqual(run(self.original_class), run(self.proposal_class))

    def test_causal_joins_explicitly_unavailable_no_caller_context_api(self):
        self.data.context.read_race_diagnostic_context = {'operation': 'IMPOSTOR_NOT_ACCEPTED'}
        self.changed_after_body()
        _, value = self.evidence()
        self.assertTrue(all(v is None for v in value['causal_joins'].values()))
        self.assertEqual(value['causal_join_availability'], 'UNAVAILABLE_CURRENT_CONTEXT_HAS_NO_CAUSAL_PRODUCER')
        self.assertTrue(value['causal_joins_are_data_only'])
        self.assertFalse(value['actual_runtime_admission'])
        self.assertFalse(value['source_finally_claimed'])
        self.assertFalse(value['original_call_claimed'])

    def test_retention_denied_preserves_primary_and_context(self):
        opened = os.open
        def denied(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith('SCIENTIFIC_INPUT_READ_RACE_'):
                raise PermissionError('synthetic private diagnostic failure')
            return opened(path, *args, **kwargs)
        with mock.patch.object(os, 'open', denied):
            caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        self.assertTrue(any('PermissionError' in n for n in caught.__notes__))
        self.assertEqual(list(self.owner.iterdir()), [])
        self.assertEqual(self.data.inputs, {})

    def test_existing_diagnostic_never_overwritten(self):
        existing = self.owner / ('SCIENTIFIC_INPUT_READ_RACE_' + str(os.getpid()) + '_1234.json')
        existing.write_bytes(b'SYNTHETIC_SENTINEL_UNCHANGED')
        with mock.patch.object(time, 'monotonic_ns', return_value=1234):
            caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        self.assertTrue(any('FileExistsError' in n for n in caught.__notes__))
        self.assertEqual(existing.read_bytes(), b'SYNTHETIC_SENTINEL_UNCHANGED')

    def test_symlink_evidence_root_never_writes_external_leaf(self):
        target = self.root / 'unowned'
        target.mkdir()
        self.owner.rmdir()
        self.owner.symlink_to(target, target_is_directory=True)
        caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        self.assertEqual(list(target.iterdir()), [])
        self.assertTrue(any('FixtureHold' in n for n in caught.__notes__))

    def test_diagnostic_readback_suppresses_recursive_capture(self):
        read = Path.read_bytes
        flags = []
        def observed(path):
            if path.name.startswith('SCIENTIFIC_INPUT_READ_RACE_'):
                flags.append(HASHING.get())
            return read(path)
        with mock.patch.object(Path, 'read_bytes', observed):
            self.changed_at_final_path()
        self.assertEqual(flags, [True])
        self.assertFalse(HASHING.get())

    def test_close_fault_still_closes_every_owned_fd_and_keeps_primary(self):
        opened, closed = os.open, os.close
        allocated, attempts = [], []
        def tracked(*args, **kwargs):
            fd = opened(*args, **kwargs)
            allocated.append(fd)
            return fd
        def fail_once(fd):
            attempts.append(fd)
            closed(fd)
            if len(attempts) == 1:
                raise OSError('synthetic post-close failure')
        with mock.patch.object(os, 'open', tracked), mock.patch.object(os, 'close', fail_once):
            caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        self.assertCountEqual(attempts, allocated)
        for fd in allocated:
            with self.assertRaises(OSError): os.fstat(fd)
        self.assertTrue(any('OSError' in n for n in caught.__notes__))

    def test_credential_pattern_failure_retains_no_secret_but_same_hold(self):
        self.input.rename(self.root / 'Bearer synthetic-secret')
        self.input = self.root / 'Bearer synthetic-secret'
        caught = self.changed_after_body()
        self.assertEqual(str(caught), 'SYNTHETIC_RUNTIME_SCIENTIFIC_INPUT_READ_RACE')
        self.assertEqual(list(self.owner.iterdir()), [])
        self.assertTrue(any('FixtureHold' in n for n in caught.__notes__))

if __name__ == '__main__':
    unittest.main(verbosity=2)
