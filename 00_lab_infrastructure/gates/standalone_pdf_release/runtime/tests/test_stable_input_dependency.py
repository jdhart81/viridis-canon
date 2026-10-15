"""Prospective shared-source attestation; temporary files only, no admission."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import packaging_runtime as runtime
import owner_content_worker as owner
import scientific_registration_worker as science


class StableDependencyTests(unittest.TestCase):
    def test_loader_uses_exact_fresh_source_and_restores_private_module_context(self):
        ambient=types.ModuleType('stable_input_identity')
        ambient.read_stable=lambda *a,**k: (_ for _ in ()).throw(AssertionError('ambient code ran'))
        before=set(sys.modules)
        with mock.patch.dict(sys.modules,{'stable_input_identity':ambient}):
            module=runtime.load_stable_input_dependency()
            with tempfile.TemporaryDirectory()as temp:
                path=Path(temp).resolve()/'input';path.write_bytes(b'fixture')
                self.assertEqual(module.read_stable(path).identity[0],hashlib.sha256(b'fixture').hexdigest())
        self.assertFalse(any(name.startswith('_viridis_exact_stable_input_')for name in set(sys.modules)-before))
        self.assertIsNone(runtime._SHARED_SOURCE_READ.get())

    def test_changed_helper_cannot_execute_even_with_correct_basename(self):
        with tempfile.TemporaryDirectory()as temp:
            path=Path(temp).resolve()/runtime.SHARED_INPUT_NAME
            marker=Path(temp).resolve()/'RAN';path.write_text('raise AssertionError("unattested helper executed")\n')
            with mock.patch.object(runtime,'_stable_dependency_path',return_value=path):
                with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_SHARED_INPUT_DEPENDENCY_BYTES'):
                    runtime.load_stable_input_dependency()
            self.assertFalse(marker.exists());self.assertIsNone(runtime._SHARED_SOURCE_READ.get())

    def test_one_exact_dependency_row_is_required_and_source_checked(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();path=root/runtime.SHARED_INPUT_NAME
            path.write_bytes((HERE.parent/'common'/runtime.SHARED_INPUT_NAME).read_bytes())
            row={'name':runtime.SHARED_INPUT_NAME,'path':str(path),'sha256':runtime.SHARED_INPUT_SHA256,
                 'git_path':runtime.SHARED_INPUT_GIT_PATH}
            self.assertEqual(len(runtime.shared_dependency_table(root,[row])),1)
            for change in ('missing','duplicate','hash','git_path','name'):
                with self.subTest(change=change):
                    values=[dict(row)]
                    if change=='missing':values=[]
                    elif change=='duplicate':values.append(dict(row))
                    else:values[0][{'hash':'sha256'}.get(change,change)]='unreviewed'
                    with self.assertRaises(runtime.PackagingHold):runtime.shared_dependency_table(root,values)

    def test_both_bootstrap_readers_ignore_only_status_change_time(self):
        with tempfile.TemporaryDirectory()as temp:
            path=Path(temp).resolve()/'source.py';path.write_bytes(b'# exact source\n')
            expected=hashlib.sha256(path.read_bytes()).hexdigest();frame=owner._identity(path.stat(),path.read_bytes())
            self.assertNotIn('ctime_ns',frame)
            path.chmod(path.stat().st_mode)
            self.assertEqual(owner._strict_source_read(path,expected,frame),b'# exact source\n')
            self.assertEqual(science._bootstrap_read(path,expected,frame),b'# exact source\n')
            before=path.stat();path.write_bytes(b'# other source\n')
            os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
            for read in (owner._strict_source_read,science._bootstrap_read):
                with self.subTest(reader=read.__name__),self.assertRaises(ValueError):read(path,expected,frame)

    def test_full_bootstrap_manifest_refuses_missing_or_changed_shared_source(self):
        import test_owner_content_worker as fixtures
        for change in ('missing','bytes','hash','profile'):
            with self.subTest(change=change),fixtures.fixture()as fixture:
                value=deepcopy(fixture.manifest)
                if change=='missing':value['shared_dependencies']=[]
                elif change=='bytes':Path(value['shared_dependencies'][0]['path']).write_bytes(b'# changed')
                elif change=='hash':value['shared_dependencies'][0]['sha256']='0'*64
                else:
                    row=next(r for r in value['metadata']if r['role']=='profile')
                    path=Path(row['path']);path.write_bytes(b'{}')
                    row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest();row['identity']=owner._identity(path.stat(),path.read_bytes())
                    value['profile_binding']['sha256']=row['sha256']
                with mock.patch.object(owner,'FIXED_CANONICAL_ROOT',fixture.root):
                    with self.assertRaises(owner.TransportHold):owner.bootstrap_sources(value)


if __name__=='__main__':unittest.main()
