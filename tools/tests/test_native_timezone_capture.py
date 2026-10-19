"""Native DATA observer negative controls; isolated paths, no Core or network."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / 'native_timezone' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


primary = load('capture_native_timezone')
independent = load('native_timezone_path_proof')


@contextlib.contextmanager
def native_paths():
    with tempfile.TemporaryDirectory(prefix='native-tz-binding-fixture-') as folder:
        base = Path(folder).resolve()
        physical = base / 'private/var/db/timezone/tz/fixture/zoneinfo/America/New_York'
        physical.parent.mkdir(parents=True)
        physical.write_bytes(b'TZif2' + b'fixture DATA, no scientific or runtime verdict')
        logical = base / 'usr/share/zoneinfo/America/New_York'
        logical.parent.parent.parent.mkdir(parents=True)
        links = (base / 'usr/share/zoneinfo', base / 'var', base / 'private/var/db/timezone/zoneinfo')
        links[0].symlink_to(base / 'var/db/timezone/zoneinfo')
        links[1].symlink_to('private/var')
        links[2].symlink_to(physical.parent.parent)
        yield base, logical, physical, links


class NativeObserverTests(unittest.TestCase):
    def test_independent_implementations_observe_same_stable_exact_frame(self):
        with native_paths() as (_, logical, physical, links):
            first = primary.capture_frame(logical, physical, links)
            second = independent.observe(logical, physical, links, [str(logical.parent.parent)])
            self.assertEqual(first, second['frame'])

    def test_changed_logical_target_never_reuses_equal_old_bytes(self):
        with native_paths() as (base, logical, physical, links):
            replacement = base / 'new-native/America/New_York'
            replacement.parent.mkdir(parents=True)
            replacement.write_bytes(physical.read_bytes())
            links[2].unlink()
            links[2].symlink_to(replacement.parent.parent)
            with self.assertRaisesRegex(RuntimeError, 'NATIVE_RESOLUTION'):
                primary.capture_frame(logical, physical, links)

    def test_independent_lookup_must_select_declared_logical_leaf(self):
        with native_paths() as (_, logical, physical, links):
            with self.assertRaisesRegex(RuntimeError, 'NATIVE_LOOKUP'):
                independent.observe(logical, physical, links, [str(physical.parent.parent)])

    def test_physical_leaf_symlink_is_refused(self):
        with native_paths() as (base, logical, physical, links):
            replacement = base / 'replacement'
            replacement.write_bytes(physical.read_bytes())
            physical.unlink()
            physical.symlink_to(replacement)
            with self.assertRaises(RuntimeError):
                primary.capture_frame(logical, physical, links)

    def test_postopen_link_replacement_with_same_target_is_refused(self):
        with native_paths() as (_, logical, physical, links):
            real_open = os.open
            changed = []
            def open_and_replace(path, flags, *args):
                fd = real_open(path, flags, *args)
                if Path(path) == physical and not changed:
                    changed.append(True)
                    target = os.readlink(links[2])
                    links[2].unlink()
                    links[2].symlink_to(target)
                return fd
            with patch.object(primary.os, 'open', side_effect=open_and_replace):
                with self.assertRaisesRegex(RuntimeError, 'NATIVE_LINK_READ_RACE'):
                    primary.capture_frame(logical, physical, links)
            self.assertEqual(changed, [True])

    def test_oversized_native_leaf_refused_before_read(self):
        with native_paths() as (_, logical, physical, links):
            physical.write_bytes(b'TZif2' + b'x' * primary.LIMIT)
            with self.assertRaisesRegex(RuntimeError, 'REGULAR_NATIVE_DATA'):
                primary.capture_frame(logical, physical, links)

    def test_non_tzif_bytes_refused(self):
        with native_paths() as (_, logical, physical, links):
            physical.write_bytes(b'invalid DATA')
            with self.assertRaisesRegex(RuntimeError, 'NATIVE_LEAF_READ_RACE'):
                primary.capture_frame(logical, physical, links)

    def test_hash_bound_proof_rejects_symlink_or_wrong_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder).resolve()
            proof = base / 'proof.json'
            proof.write_bytes(b'{}')
            with self.assertRaisesRegex(RuntimeError, 'PROOF_HASH_OR_RACE'):
                primary.bounded_file(proof, '0' * 64)
            alias = base / 'alias.json'
            alias.symlink_to(proof)
            with self.assertRaisesRegex(RuntimeError, 'REGULAR_PROOF_FILE'):
                primary.bounded_file(alias, hashlib.sha256(b'{}').hexdigest())

    def test_capture_outputs_same_closed_source_only_schema_without_tool_exit_invention(self):
        with native_paths() as (base, logical, physical, links):
            proof = {'standard': 'VRS-INDEPENDENT-NATIVE-TIMEZONE-PATH-OBSERVATION-1',
                     'status': 'READ_ONLY_NATIVE_TIMEZONE_PATH_OBSERVED',
                     'certifies': False, 'network_requests': 0,
                     **independent.observe(logical, physical, links, [str(logical.parent.parent)])}
            proof_path = base / 'proof.json'
            proof_path.write_text(json.dumps(proof))
            failed_path = base / 'failed.log'
            failed_path.write_text('TEST FIXTURE: EXACT_NATIVE_TIMEZONE_LINK_IDENTITY')
            argv = ['capture', '--independent-proof', str(proof_path),
                    '--expected-independent-proof-sha256', hashlib.sha256(proof_path.read_bytes()).hexdigest(),
                    '--failed-preflight', str(failed_path),
                    '--expected-failed-preflight-sha256', hashlib.sha256(failed_path.read_bytes()).hexdigest()]
            with patch.object(primary, 'LOGICAL', logical), patch.object(primary, 'PHYSICAL', physical), \
                 patch.object(primary, 'LINKS', links), patch.object(sys, 'argv', argv), \
                 patch.object(primary.sysconfig, 'get_config_var', return_value=str(logical.parent.parent)), \
                 contextlib.redirect_stdout(io.StringIO()) as output:
                primary.main()
            value = json.loads(output.getvalue())
            self.assertEqual(set(value), {'actual_failed_child_path_limitation', 'actual_failed_execution',
                'after', 'before', 'certifies', 'created_at_utc', 'heavy_scientific_executions',
                'independent_platform_path_evidence', 'logical_selected_path', 'network_requests',
                'physical_path', 'root_executable', 'scope', 'source_certificate_alias_ledger_timezone_writes',
                'standard', 'status', 'stdlib_TZPATH', 'zone_key'})
            self.assertIsNone(value['actual_failed_execution']['actual_root_exec_tool_exit_code'])
            self.assertFalse(value['certifies'])
            self.assertEqual(value['before'], value['after'])
            self.assertEqual(value['network_requests'], 0)


if __name__ == '__main__':
    unittest.main()
