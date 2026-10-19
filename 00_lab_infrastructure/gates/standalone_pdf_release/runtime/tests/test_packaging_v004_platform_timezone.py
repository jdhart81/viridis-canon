"""One exact native timezone DATA leaf; synthetic fixtures, no live admission.

The ordinary ZoneInfo reader runs once in a fresh child over temporary links.
No ZoneInfo cache is cleared or warmed, and no original reader is replaced.
Fault injection wraps a real temporary physical read; validators stay real.
"""
import base64
import contextlib
from copy import deepcopy
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_catalog as catalog
import packaging_runtime as runtime
import test_packaging_default_routes as default_fixtures
import test_packaging_v003_data_alias as historical_fixtures

# Exact native TZif bytes from the root-reviewed NY observation. This
# is fixture DATA, never a claim that synthetic paths are actual platform paths.
TZIF_B64 = 'VFppZjIAAAAAAAAAAAAAAAAAAAAAAAAGAAAABgAAAAAAAADsAAAABgAAABSAAAAAnqYecJ+662CghgBwoZrNYKJl4nCjg+ngpGqucKU1p2CmU8rwpxWJYKgzrPCo/qXgqhOO8Kreh+Cr83DwrL5p4K3TUvCunkvgr7M08LB+LeCxnFFwsmdKYLN8M3C0RyxgtVwVcLYnDmC3O/dwuAbwYLkb2XC55tJguwT18LvGtGC85Nfwva/Q4L7EufC/j7LgwKSb8MFvlODChH3ww0924MRkX/DFL1jgxk18cMcPOuDILV5wyPhXYMoNQHDK2Dlgy4jwcNIj9HDSYPvg03Xk8NRA3eDVVcbw1iC/4Nc1qPDYAKHg2RWK8Nngg+Da/qdw28Bl4NzeiXDdqYJg3r5rcN+JZGDgnk1w4WlGYOJ+L3DjSShg5F4RcOVXLuDmRy3w5zcQ4OgnD/DpFvLg6gbx8Or21ODr5tPw7Na24O3GtfDuv9Ng76/ScPCftWDxj7Rw8n+XYPNvlnD0X3lg9U94cPY/W2D3L1pw+Ch34PkPPHD6CFng+vhY8PvoO+D82Drw/cgd4P64HPD/p//gAJf+8AGH4eACd+DwA3D+YARg/XAFUOBgBkDfcAcwwmAHjRlwCRCkYAmtlPAK8IZgC+CFcAzZouANwGdwDrmE4A+pg/AQmWbgEYll8BJ5SOATaUfwFFkq4BVJKfAWOQzgFykL8BgiKWAZCO3wGgILYBryCnAb4e1gHNHscB3Bz2Aesc5wH6GxYCB2APAhgZNgIlXi8CNqr+AkNcTwJUqR4CYVpvAnKnPgJ/7DcCkKVeAp3qVwKuo34Cu+h3As01RgLZ5pcC6zNmAvfktwMJMYYDFnZ/AycvpgM0dJ8DRS3GA1JyvwNjK+YDcHDfA4G9rgOObv8Dn7vOA6xtHwO9ue4Dyv7nA9u4DgPo/QcD+bYuBAb7JwQYR/YEJPlHBDZGFgRC92cEVEQ2BF86jwRy1f4EfTivBJDUHgSbNs8ErtI+BLnIlwTNZAYE18a3BOtiJgT1xNcFCWBGBRPC9wUnXmYFMcEXBUVchgVPvzcFY1qmBW5Q/wWB7G4FjE8fBZ/qjgWqTT8FveiuBchLXwXb5s4F5kl/Bfnk7gYE20cGGHa2BiLZZwY2dNYGQNeHBlRy9gZe1acGcnEWBnzTxwaQbzYGmtHnBq5tVga5Y68GzP8eBtdhzwbq/T4G9V/vBwj7XgcTXg8HJvl+BzFcLwdE954HT+33B2OJZgdt7BcHgYeGB4vqNwefhaYHqehXB72DxgfH5ncH24HmB+Xklwf5gAYAMBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIEBQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgEC//+6ngAA///HwAEE//+5sAAI//+5sAAI///HwAEM///HwAEQTE1UAEVEVABFU1QARVdUAEVQVAAAAAABAAEAAAABAAFUWmlmMgAAAAAAAAAAAAAAAAAAAAAAAAYAAAAGAAAAAAAAAOwAAAAGAAAAFP////9eA/CQ/////56mHnD/////n7rrYP////+ghgBw/////6GazWD/////omXicP////+jg+ng/////6RqrnD/////pTWnYP////+mU8rw/////6cViWD/////qDOs8P////+o/qXg/////6oTjvD/////qt6H4P////+r83Dw/////6y+aeD/////rdNS8P////+unkvg/////6+zNPD/////sH4t4P////+xnFFw/////7JnSmD/////s3wzcP////+0Ryxg/////7VcFXD/////ticOYP////+3O/dw/////7gG8GD/////uRvZcP////+55tJg/////7sE9fD/////u8a0YP////+85Nfw/////72v0OD/////vsS58P////+/j7Lg/////8Ckm/D/////wW+U4P/////ChH3w/////8NPduD/////xGRf8P/////FL1jg/////8ZNfHD/////xw864P/////ILV5w/////8j4V2D/////yg1AcP/////K2Dlg/////8uI8HD/////0iP0cP/////SYPvg/////9N15PD/////1EDd4P/////VVcbw/////9Ygv+D/////1zWo8P/////YAKHg/////9kVivD/////2eCD4P/////a/qdw/////9vAZeD/////3N6JcP/////dqYJg/////96+a3D/////34lkYP/////gnk1w/////+FpRmD/////4n4vcP/////jSShg/////+ReEXD/////5Vcu4P/////mRy3w/////+c3EOD/////6CcP8P/////pFvLg/////+oG8fD/////6vbU4P/////r5tPw/////+zWtuD/////7ca18P/////uv9Ng/////++v0nD/////8J+1YP/////xj7Rw//////J/l2D/////82+WcP/////0X3lg//////VPeHD/////9j9bYP/////3L1pw//////god+D/////+Q88cP/////6CFng//////r4WPD/////++g74P/////82Drw//////3IHeD//////rgc8P//////p//gAAAAAACX/vAAAAAAAYfh4AAAAAACd+DwAAAAAANw/mAAAAAABGD9cAAAAAAFUOBgAAAAAAZA33AAAAAABzDCYAAAAAAHjRlwAAAAAAkQpGAAAAAACa2U8AAAAAAK8IZgAAAAAAvghXAAAAAADNmi4AAAAAANwGdwAAAAAA65hOAAAAAAD6mD8AAAAAAQmWbgAAAAABGJZfAAAAAAEnlI4AAAAAATaUfwAAAAABRZKuAAAAAAFUkp8AAAAAAWOQzgAAAAABcpC/AAAAAAGCIpYAAAAAAZCO3wAAAAABoCC2AAAAAAGvIKcAAAAAAb4e1gAAAAABzR7HAAAAAAHcHPYAAAAAAesc5wAAAAAB+hsWAAAAAAIHYA8AAAAAAhgZNgAAAAACJV4vAAAAAAI2qv4AAAAAAkNcTwAAAAACVKkeAAAAAAJhWm8AAAAAAnKnPgAAAAACf+w3AAAAAAKQpV4AAAAAAp3qVwAAAAACrqN+AAAAAAK76HcAAAAAAs01RgAAAAAC2eaXAAAAAALrM2YAAAAAAvfktwAAAAADCTGGAAAAAAMWdn8AAAAAAycvpgAAAAADNHSfAAAAAANFLcYAAAAAA1JyvwAAAAADYyvmAAAAAANwcN8AAAAAA4G9rgAAAAADjm7/AAAAAAOfu84AAAAAA6xtHwAAAAADvbnuAAAAAAPK/ucAAAAAA9u4DgAAAAAD6P0HAAAAAAP5ti4AAAAABAb7JwAAAAAEGEf2AAAAAAQk+UcAAAAABDZGFgAAAAAEQvdnAAAAAARURDYAAAAABF86jwAAAAAEctX+AAAAAAR9OK8AAAAABJDUHgAAAAAEmzbPAAAAAASu0j4AAAAABLnIlwAAAAAEzWQGAAAAAATXxrcAAAAABOtiJgAAAAAE9cTXAAAAAAUJYEYAAAAABRPC9wAAAAAFJ15mAAAAAAUxwRcAAAAABUVchgAAAAAFT783AAAAAAVjWqYAAAAABW5Q/wAAAAAFgexuAAAAAAWMTx8AAAAABZ/qjgAAAAAFqk0/AAAAAAW96K4AAAAABchLXwAAAAAF2+bOAAAAAAXmSX8AAAAABfnk7gAAAAAGBNtHAAAAAAYYdrYAAAAABiLZZwAAAAAGNnTWAAAAAAZA14cAAAAABlRy9gAAAAAGXtWnAAAAAAZycRYAAAAABnzTxwAAAAAGkG82AAAAAAaa0ecAAAAABq5tVgAAAAAGuWOvAAAAAAbM/x4AAAAABtdhzwAAAAAG6v0+AAAAAAb1X+8AAAAABwj7XgAAAAAHE14PAAAAAAcm+X4AAAAABzFcLwAAAAAHRPeeAAAAAAdP7fcAAAAAB2OJZgAAAAAHbewXAAAAAAeBh4YAAAAAB4vqNwAAAAAHn4WmAAAAAAep6FcAAAAAB72DxgAAAAAHx+Z3AAAAAAfbgeYAAAAAB+XklwAAAAAH+YAGADAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECBAUCAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAgECAQIBAv//up4AAP//x8ABBP//ubAACP//ubAACP//x8ABDP//x8ABEExNVABFRFQARVNUAEVXVABFUFQAAAAAAQABAAAAAQABCkVTVDVFRFQsTTMuMi4wLE0xMS4xLjAK'
TZIF_SHA = 'e9ed07d7bee0c76a9d442d091ef1f01668fee7c4f26014c0a868b19fe6c18a95'


@contextlib.contextmanager
def native_fixture():
    with historical_fixtures.alias_fixture() as old:
        base = old.base
        physical = base / 'private/var/db/timezone/tz/fixture-version/zoneinfo/America/New_York'
        physical.parent.mkdir(parents=True)
        raw = base64.b64decode(TZIF_B64)
        if runtime.sha(raw) != TZIF_SHA or len(raw) != 3552:
            raise AssertionError('Exact original native fixture bytes changed')
        physical.write_bytes(raw)
        logical = base / 'usr/share/zoneinfo/America/New_York'
        logical.parent.parent.parent.mkdir(parents=True)
        links = (base / 'usr/share/zoneinfo', base / 'var',
                 base / 'private/var/db/timezone/zoneinfo')
        links[0].symlink_to(str(base / 'var/db/timezone/zoneinfo'))
        links[1].symlink_to('private/var')
        links[2].symlink_to(str(base / 'var/db/timezone/tz/fixture-version/zoneinfo'))
        frame = {'TZif_header_hex': raw[:5].hex(), 'bytes': len(raw),
                 'sha256': runtime.sha(raw),
                 'physical_file_identity': runtime.platform_file_identity(physical),
                 'physical_regular_parent_chain': [
                     {'path': str(p), 'identity': runtime.platform_file_identity(p)}
                     for p in reversed(physical.parents)],
                 'resolution_symlink_chain': [
                     {'path': str(p), 'identity': runtime.data_alias_identity(p),
                      'resolved_target': str(p.resolve(strict=True))} for p in links]}
        observation = {
            'standard': 'VRS-ROOT-EXACT-PLATFORM-TIMEZONE-DATA-READBACK-1',
            'status': 'EXACT_CURRENT_NATIVE_DATA_PATH_VERIFIED_NOT_RUNTIME_ADMISSION',
            'zone_key': 'America/New_York', 'logical_selected_path': str(logical),
            'physical_path': str(physical), 'root_executable': sys.executable,
            'stdlib_TZPATH': [str(logical.parent.parent)],
            'before': deepcopy(frame), 'after': deepcopy(frame),
            'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'actual_failed_child_path_limitation': 'Synthetic shape only; no actual child claimed.',
            'actual_failed_execution': {'path': 'synthetic-only', 'sha256': '0' * 64,
                                       'actual_child_exit_code': 1,
                                       'actual_root_exec_tool_exit_code': 1},
            'independent_platform_path_evidence': {'path': 'synthetic-only', 'sha256': '0' * 64},
            'scope': 'One temporary NY DATA leaf and exact three temporary links.',
            'heavy_scientific_executions': 0, 'network_requests': 0,
            'source_certificate_alias_ledger_timezone_writes': 0, 'certifies': False}
        receipt = old.root / 'reports/synthetic_native_timezone.json'
        receipt.write_text(json.dumps(observation, sort_keys=True))
        binding = {'path': str(receipt.relative_to(old.root)),
                   'sha256': runtime.sha(receipt.read_bytes())}
        with contextlib.ExitStack() as stack:
            for key, value in {'CURRENT_PLATFORM_TIMEZONE_OBSERVATION': binding,
                               'PLATFORM_TZ_LOGICAL': logical,
                               'PLATFORM_TZ_PHYSICAL': physical,
                               'PLATFORM_TZ_LINK_PATHS': links}.items():
                stack.enter_context(patch.object(runtime, key, value))
            stack.enter_context(patch.dict(os.environ, {'PYTHONTZPATH': str(logical.parent.parent)}))
            yield SimpleNamespace(root=old.root, base=base, old=old,
                                  context=old.context, output=old.output,
                                  logical=logical, physical=physical, links=links,
                                  frame=frame, observation=observation,
                                  receipt=receipt, binding=binding)


class ExactNativeTimezoneTests(unittest.TestCase):
    def data(self, f):
        return catalog.ScientificInputData(f.root, f.context,
                                          platform_timezone_observation=f.binding)

    def test_cold_unchanged_zoneinfo_reader_uses_exact_three_links_and_preserves_new_york_offsets(self):
        with native_fixture() as f:
            config = {'root': str(f.root), 'binding': f.binding,
                      'logical': str(f.logical), 'physical': str(f.physical),
                      'links': [str(p) for p in f.links]}
            code = '''import sys,json,datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo
sys.path.insert(0,sys.argv[1])
import packaging_catalog as catalog
import packaging_runtime as runtime
value=json.loads(sys.argv[2]);root=Path(value['root'])
runtime.CURRENT_PLATFORM_TIMEZONE_OBSERVATION=value['binding']
runtime.PLATFORM_TZ_LOGICAL=Path(value['logical'])
runtime.PLATFORM_TZ_PHYSICAL=Path(value['physical'])
runtime.PLATFORM_TZ_LINK_PATHS=tuple(Path(p)for p in value['links'])
data=catalog.ScientificInputData(root,SimpleNamespace(),platform_timezone_observation=value['binding'])
token=catalog._READ_CAPTURE.set(data)
try:
    zone=ZoneInfo('America/New_York')
finally:
    catalog._READ_CAPTURE.reset(token)
data.assert_current()
data.require_platform_read()
row=data.inputs[value['logical']]
print(json.dumps({'key':zone.key,'winter_seconds':datetime.datetime(2026,1,15,tzinfo=zone).utcoffset().total_seconds(),
                 'summer_seconds':datetime.datetime(2026,7,15,tzinfo=zone).utcoffset().total_seconds(),
                 'row':row,'capture_reset':catalog._READ_CAPTURE.get()is None}))
'''
            # Fresh process and ordinary standard-library configuration; no
            # ZoneInfo object exists before the actual captured native open.
            child = subprocess.run([sys.executable, '-B', '-c', code, str(HERE), json.dumps(config)],
                                   env=dict(os.environ), capture_output=True, text=True, timeout=30)
            self.assertEqual(child.returncode, 0, child.stderr)
            value = json.loads(child.stdout)
            self.assertEqual((value['key'], value['winter_seconds'], value['summer_seconds']),
                             ('America/New_York', -18000, -14400))
            self.assertTrue(value['capture_reset'])
            row = value['row']
            self.assertEqual(row['physical_path'], str(f.physical))
            self.assertEqual(row['sha256'], TZIF_SHA)
            self.assertEqual(row['native_timezone_identity'], f.frame['physical_file_identity'])
            self.assertEqual(row['native_timezone_link_chain'], f.frame['resolution_symlink_chain'])

    def test_native_logical_or_physical_leaf_is_never_a_source_binding(self):
        with native_fixture() as f:
            self.data(f).record(f.logical)
            for path in (f.logical, f.physical):
                with self.subTest(path=path), self.assertRaisesRegex(runtime.PackagingHold, 'REGULAR_CONTAINED_SOURCE'):
                    runtime.read(f.root, {'path': str(path), 'sha256': TZIF_SHA})

    def test_no_descriptor_wrong_binding_or_extra_whitelist_never_admits_native_alias(self):
        with native_fixture() as f:
            with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_REGULAR_PATH'):
                catalog.ScientificInputData(f.root, f.context).record(f.logical)
            with self.assertRaises(runtime.PackagingHold):
                catalog.ScientificInputData(f.root, f.context,
                                           platform_timezone_observation={**f.binding, 'sha256': '0' * 64})
            changed = deepcopy(f.observation)
            changed['allowed_timezones'] = ['America/New_York', 'any-other-leaf']
            f.receipt.write_text(json.dumps(changed, sort_keys=True))
            replacement = {**f.binding, 'sha256': runtime.sha(f.receipt.read_bytes())}
            with patch.object(runtime, 'CURRENT_PLATFORM_TIMEZONE_OBSERVATION', replacement):
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_NATIVE_PLATFORM_TIMEZONE_OBSERVATION'):
                    catalog.ScientificInputData(f.root, f.context, platform_timezone_observation=replacement)

    def test_each_native_link_recreated_retargeted_or_removed_holds(self):
        for index in range(3):
            for mode in ('recreated', 'retargeted', 'removed'):
                with self.subTest(index=index, mode=mode), native_fixture() as f:
                    data = self.data(f)
                    link = f.links[index]
                    target = os.readlink(link)
                    link.unlink()
                    if mode == 'recreated':
                        link.symlink_to(target)
                    elif mode == 'retargeted':
                        link.symlink_to(f.root)
                    with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                        data.assert_current()

    def test_same_target_link_metadata_change_is_not_reused(self):
        with native_fixture() as f:
            data = self.data(f)
            p = f.links[1]
            s = p.lstat()
            os.utime(p, ns=(s.st_atime_ns, s.st_mtime_ns + 1000000), follow_symlinks=False)
            with self.assertRaises(runtime.PackagingHold):
                data.record(f.logical)

    def test_unknown_alias_sibling_leaf_or_physical_child_link_holds(self):
        for mode in ('unknown-alias', 'sibling-leaf', 'physical-parent-link', 'logical-parent-link'):
            with self.subTest(mode=mode), native_fixture() as f:
                data = self.data(f)
                if mode == 'unknown-alias':
                    p = f.root / 'unknown-zoneinfo'
                    p.symlink_to(f.logical.parent.parent)
                    path = p / 'America/New_York'
                elif mode == 'sibling-leaf':
                    (f.physical.parent / 'Unapproved').write_bytes(f.physical.read_bytes())
                    path = f.logical.parent / 'Unapproved'
                elif mode == 'physical-parent-link':
                    moved = f.physical.parent.with_name('original-America')
                    f.physical.parent.rename(moved)
                    f.physical.parent.symlink_to(moved.name)
                    path = f.logical
                else:
                    # All three known link objects and native leaf identities
                    # stay exact, but a previously regular logical ancestor
                    # acquires an unapproved additional symlink.
                    parent = f.links[0].parent
                    moved = parent.with_name('original-share')
                    parent.rename(moved)
                    parent.symlink_to(moved.name)
                    path = f.logical
                    self.assertEqual(runtime.data_alias_identity(f.links[0]),
                                     f.frame['resolution_symlink_chain'][0]['identity'])
                    self.assertEqual(runtime.platform_file_identity(f.physical),
                                     f.frame['physical_file_identity'])
                with self.assertRaises(runtime.PackagingHold):
                    data.record(path)

    def test_changed_replaced_absent_directory_or_leaf_symlink_timezone_holds(self):
        for mode in ('bytes', 'replacement', 'absent', 'directory', 'leaf-symlink'):
            with self.subTest(mode=mode), native_fixture() as f:
                data = self.data(f)
                raw = f.physical.read_bytes()
                if mode == 'bytes':
                    f.physical.write_bytes(raw[:-1] + bytes([raw[-1] ^ 255]))
                elif mode == 'replacement':
                    other = f.root / 'replacement'
                    other.write_bytes(raw)
                    os.replace(other, f.physical)
                else:
                    f.physical.unlink()
                    if mode == 'directory':
                        f.physical.mkdir()
                    elif mode == 'leaf-symlink':
                        other = f.root / 'replacement'
                        other.write_bytes(raw)
                        f.physical.symlink_to(other)
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                    data.record(f.logical)

    def test_post_read_native_link_leaf_or_parent_change_rejects_before_row_commit(self):
        for mode in ('link', 'leaf', 'parent', 'logical-parent'):
            with self.subTest(mode=mode), native_fixture() as f:
                data = self.data(f)
                original_read = Path.read_bytes
                injected = []
                def read_then_change(path):
                    raw = original_read(path)
                    if path == f.physical and not injected:
                        injected.append(True)
                        if mode == 'link':
                            p = f.links[2]
                            target = os.readlink(p)
                            p.unlink()
                            p.symlink_to(target)
                        elif mode == 'leaf':
                            other = f.root / 'replacement'
                            other.write_bytes(raw)
                            os.replace(other, f.physical)
                        elif mode == 'parent':
                            moved = f.physical.parent.with_name('original-America')
                            f.physical.parent.rename(moved)
                            f.physical.parent.symlink_to(moved.name)
                        else:
                            parent = f.links[0].parent
                            moved = parent.with_name('original-share')
                            parent.rename(moved)
                            parent.symlink_to(moved.name)
                            self.assertEqual(runtime.data_alias_identity(f.links[0]),
                                             f.frame['resolution_symlink_chain'][0]['identity'])
                            self.assertEqual(runtime.platform_file_identity(f.physical),
                                             f.frame['physical_file_identity'])
                    return raw
                with patch.object(Path, 'read_bytes', read_then_change):
                    with self.assertRaises(runtime.PackagingHold):
                        data.record(f.logical)
                self.assertEqual(injected, [True])
                self.assertNotIn(str(f.logical), data.inputs)
                self.assertFalse(catalog._HASHING.get())

    def test_changed_native_lookup_configuration_holds_without_rebaselining(self):
        with native_fixture() as f:
            data = self.data(f)
            with patch.dict(os.environ, {'PYTHONTZPATH': str(f.physical.parent.parent)}):
                with self.assertRaisesRegex(runtime.PackagingHold, 'ACTUAL_NATIVE_NEW_YORK_LOOKUP'):
                    data.assert_current()

    def test_nominal_validation_or_physical_read_cannot_replace_actual_logical_timezone_observation(self):
        with native_fixture() as f:
            data = self.data(f)
            # Constructor/frame validation has read the bytes but has not
            # recorded an original pending open of the logical native leaf.
            with self.assertRaisesRegex(runtime.PackagingHold, 'ACTUAL_CURRENT_OPERATION_NEW_YORK_TZ_DATA_READ_REQUIRED'):
                data.require_platform_read()
            token = catalog._READ_CAPTURE.set(data)
            try:
                f.physical.read_bytes()
            finally:
                catalog._READ_CAPTURE.reset(token)
            self.assertIn(str(f.physical), data.inputs)
            self.assertNotIn(str(f.logical), data.inputs)
            data.scan_data = {'explicit_synthetic_DATA_only': True}
            with self.assertRaisesRegex(runtime.PackagingHold, 'ACTUAL_CURRENT_OPERATION_NEW_YORK_TZ_DATA_READ_REQUIRED'):
                data.assert_current()

    def test_full_native_guard_is_used_for_target_and_boundaries_not_every_unrelated_read(self):
        with native_fixture() as f:
            data = self.data(f)
            unrelated = f.root / 'unrelated-scientific-data.lean'
            unrelated.write_bytes(b'exact synthetic ordinary DATA')
            # Call instrumentation preserves the real instance guard and its
            # validation. It neither mocks the native frame nor a verdict.
            with patch.object(data, 'platform_guard', wraps=data.platform_guard) as guard:
                data.record(unrelated)
                self.assertEqual(guard.call_count, 0)
                data.record(f.logical)
                self.assertGreaterEqual(guard.call_count, 2)
                guard.reset_mock()
                data.scan_data = {'explicit_synthetic_DATA_only': True}
                data.assert_current()
                self.assertGreaterEqual(guard.call_count, 1)
                guard.reset_mock()
                data.record(unrelated)
                self.assertEqual(guard.call_count, 0)

    def test_directory_stats_are_observed_while_parent_structure_and_leaf_stay_pinned(self):
        with native_fixture() as f:
            data = self.data(f)
            before = deepcopy(data.platform_initial_frame)
            (f.physical.parent / 'unrelated-empty-directory').mkdir()
            data.assert_current()
            self.assertNotEqual(before['physical_regular_parent_chain'],
                                data.platform_latest_frame['physical_regular_parent_chain'])
            self.assertEqual(before['physical_file_identity'], data.platform_latest_frame['physical_file_identity'])
            self.assertEqual(before['resolution_symlink_chain'], data.platform_latest_frame['resolution_symlink_chain'])

    def test_native_changes_hold_before_and_after_canonical_cas(self):
        for phase in ('before', 'after'):
            with self.subTest(phase=phase), native_fixture() as f:
                data = self.data(f)
                path = f.root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                path.write_bytes(b'{"before":true}')
                before = runtime.sha(path.read_bytes())
                after = b'{"after":true}'
                data.record(path)
                if phase == 'after':
                    data.authorize_cas(path, before, runtime.sha(after))
                    path.write_bytes(after)
                target = os.readlink(f.links[0])
                f.links[0].unlink()
                f.links[0].symlink_to(target)
                with self.assertRaises(runtime.PackagingHold):
                    if phase == 'before':
                        data.authorize_cas(path, before, runtime.sha(after))
                    else:
                        data.finish_cas()
                if phase == 'before':
                    self.assertEqual(data.cas_events, [])
                    self.assertEqual(path.read_bytes(), b'{"before":true}')
                else:
                    # The authorized bytes really changed before the final
                    # guard failed. Retain that actual transition accounting;
                    # it is not a successful operation/admission verdict.
                    self.assertEqual(data.cas_events, [{'path': str(path),
                                                       'before': before,
                                                       'after': runtime.sha(after)}])
                    self.assertEqual(path.read_bytes(), after)
                with self.assertRaises(runtime.PackagingHold):
                    data.retain_final(False)
                self.assertFalse((f.output / 'SCIENTIFIC_INPUT_DATA_FINAL.json').exists())

    def test_complete_final_manifest_keeps_native_frame_and_changed_native_exit_holds(self):
        with native_fixture() as f:
            data = self.data(f)
            data.record(f.logical)
            data.retain_manifest()
            data.retain_final(False)
            value = json.loads((f.output / 'SCIENTIFIC_INPUT_DATA_FINAL.json').read_bytes())
            self.assertEqual(value['status'], 'COMPLETE_REHASHED_OPERATION_INPUT_DATA')
            self.assertFalse(value['admission_cached'])
            self.assertEqual(value['platform_timezone_observation'], f.binding)
            self.assertEqual(value['native_timezone_initial_frame']['physical_file_identity'], f.frame['physical_file_identity'])
            self.assertEqual(value['native_timezone_latest_frame']['resolution_symlink_chain'], f.frame['resolution_symlink_chain'])
        with native_fixture() as f:
            data = self.data(f)
            data.record(f.logical)
            f.physical.write_bytes(b'changed timezone')
            with self.assertRaises(runtime.PackagingHold):
                data.retain_final(False)
            self.assertFalse((f.output / 'SCIENTIFIC_INPUT_DATA_FINAL.json').exists())

    def test_missing_native_constructor_closes_genuine_observation_factory_and_restores_tokens(self):
        with native_fixture() as f:
            replay = default_fixtures.ObservationReplayTests()
            stack, context, requests, clock, output = replay.setup_context(
                f.root, folder='native-constructor-failure', begin=False)
            with stack:
                f.links[2].unlink()
                entered = []
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                    with catalog.operation_scope(f.root, {'synthetic_profile': True}, context):
                        entered.append(True)
                self.assertEqual(entered, [])
                with self.assertRaisesRegex(runtime.PackagingHold, 'OBSERVATION_OPERATION_ALREADY_CLOSED'):
                    context.begin_observation_operation()
                self.assertEqual(requests, [])
                self.assertIsNone(catalog._SCIENCE.get())
                self.assertIsNone(catalog._READ_CAPTURE.get())
                self.assertIsNone(catalog._OPERATION.get())
                self.assertFalse(list(output.rglob('SCIENTIFIC_INPUT_DATA*.json')))


if __name__ == '__main__':
    unittest.main()
