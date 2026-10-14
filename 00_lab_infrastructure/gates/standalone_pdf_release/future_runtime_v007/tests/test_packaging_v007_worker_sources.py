"""Current worker DATA/source refusal tests; no original science or network."""
import contextlib
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import packaging_runtime as runtime


def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    path.write_bytes(raw)
    return {'path':str(path),'sha256':runtime.sha(raw)}


class WorkerSourceTests(unittest.TestCase):
    def test_current_import_artifacts_are_rejected_without_deletion(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(sys,'pycache_prefix','/synthetic/external-cache'):
            with self.assertRaisesRegex(runtime.PackagingHold,'CURRENT_EXTERNAL_IMPORT_CACHE_PREFIX'):
                runtime.current_import_artifact_guard(Path(tmp))
        for artifact in ('__pycache__','packaging_runtime','packaging_runtime.pyc',
                         'packaging_runtime.pyo',
                         'packaging_runtime'+runtime.importlib.machinery.EXTENSION_SUFFIXES[0]):
            with self.subTest(artifact=artifact),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp).resolve()
                runtime.current_import_artifact_guard(directory)
                path=directory/artifact
                if artifact in ('__pycache__','packaging_runtime'):path.mkdir()
                else:path.write_bytes(b'inert alternate-code fixture')
                with self.assertRaisesRegex(runtime.PackagingHold,'CURRENT_IMPORT_ARTIFACT'):
                    runtime.current_import_artifact_guard(directory)
                self.assertTrue(path.exists())
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp).resolve();path=directory/'packaging_runtime.pyc'
            path.symlink_to(directory/'missing')
            with self.assertRaises(runtime.PackagingHold):runtime.current_import_artifact_guard(directory)
            self.assertTrue(path.is_symlink())

    def review(self):
        return {'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-7',
            'status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS','reviewer':'synthetic isolated test',
            'source_hashes':{},'legacy_closure':runtime.LEGACY_CLOSURE,
            'review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,
            'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK',
            **runtime.SOURCE_REVIEW_CHANGE_FLAGS}

    def test_each_change_flag_is_required_with_exact_boolean_and_old_schema_refused(self):
        review=self.review()
        runtime.require_source_review(review,{},runtime.LEGACY_CLOSURE)
        for key,correct in runtime.SOURCE_REVIEW_CHANGE_FLAGS.items():
            for bad in (not correct,int(correct),'true',None):
                value={**review,key:bad}
                with self.subTest(key=key,bad=bad),self.assertRaises(runtime.PackagingHold):
                    runtime.require_source_review(value,{},runtime.LEGACY_CLOSURE)
            value=deepcopy(review);del value[key]
            with self.assertRaises(runtime.PackagingHold):
                runtime.require_source_review(value,{},runtime.LEGACY_CLOSURE)
        old={**review,'scientific_admission_changed':False}
        with self.assertRaises(runtime.PackagingHold):
            runtime.require_source_review(old,{},runtime.LEGACY_CLOSURE)

    def test_current19_and_fixed_historical17_tables_cannot_be_mixed_or_rebound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();rows=[]
            for name in sorted(runtime.MODULE_NAMES):
                file=root/name;file.write_bytes(b'# source fixture\n')
                rows.append({'name':name,'path':str(file),'sha256':runtime.sha(file.read_bytes()),
                             'git_path':runtime.GIT_PREFIX+name})
            self.assertEqual(len(runtime.module_table(root,rows)),19)
            for prefix in runtime.FROZEN_GIT_PREFIXES:
                old=[{**row,'git_path':prefix+row['name']} for row in rows if row['name'] in runtime.FROZEN_MODULE_NAMES]
                self.assertEqual(len(runtime.module_table(root,old,git_prefix=prefix)),17)
                with self.assertRaises(runtime.PackagingHold):
                    runtime.module_table(root,[{**row,'git_path':prefix+row['name']} for row in rows],git_prefix=prefix)
                with self.assertRaises(runtime.PackagingHold):runtime.module_table(root,old)
            with self.assertRaisesRegex(runtime.PackagingHold,'FIXED_MODULE_TABLE_NAMESPACE'):
                runtime.module_table(root,rows,git_prefix='operator-selected/')

    def test_readonly_authority_propagates_through_nested_source_sessions_and_finalizers(self):
        calls=[]
        def validate(*args,**kwargs):
            calls.append(runtime._RESTORE_TRANSIENTS.get())
            return {'source_pins':[]}
        @contextlib.contextmanager
        def source_session(*args,**kwargs):yield
        builder=types.SimpleNamespace(source_session=source_session)
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'validate',side_effect=validate),\
             patch.object(runtime,'object_at',return_value=(None,b'{}',{'source_session_consumer':{}})),\
             patch.object(runtime,'load',return_value=builder):
            with runtime.readonly_worker_scope():
                with runtime.session(tmp,{}):
                    with runtime.session(tmp,{}):pass
                with self.assertRaisesRegex(RuntimeError,'fixture failure'):
                    with runtime.session(tmp,{}):raise RuntimeError('fixture failure')
            self.assertEqual(calls,[False]*9)
            calls.clear()
            with runtime.session(tmp,{}):pass
            self.assertEqual(calls,[True]*3)

    def fixture(self,root):
        installed=root/Path(runtime.PROFILE_PATH).parent;installed.mkdir(parents=True)
        review=put(root/'review.json',{'explicit_synthetic_test':True})
        modules=[]
        for name in sorted(runtime.MODULE_NAMES):
            file=installed/name;file.write_bytes(('# synthetic '+name+'\n').encode())
            modules.append({'name':name,'path':str(file),'sha256':runtime.sha(file.read_bytes()),
                            'git_path':runtime.GIT_PREFIX+name})
        profile=put(root/runtime.PROFILE_PATH,{'modules':modules,'source_origin':{'synthetic_only':True},
                  'legacy_closure':runtime.LEGACY_CLOSURE})
        installer=next(row for row in modules if row['name']=='install_packaging_runtime.py')
        put(root/runtime.NOMINATION_PATH,{'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-7',
            'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
            'profile':profile,'installer_source':{k:installer[k] for k in ('path','sha256')},
            'merged_source_commit':'a'*40,'root_review_receipt':review})
        put(installed/'INSTALL_PLAN.json',{'synthetic_only':True})
        return profile,modules

    @contextlib.contextmanager
    def source_fixture(self,root):
        # Only source-authority is a named test stub. Physical source/data
        # reads, closed tables, fixed paths and all identities execute for real.
        with patch.object(runtime,'validate',return_value={'synthetic_source_only':True}),\
             patch.object(runtime,'SCIENTIFIC_ALIAS_PATH',root.with_name('historical-alias')) ,\
             patch.object(runtime,'SCIENTIFIC_ALIAS_READLINK',root.name):yield

    def test_complete_source_manifest_requires_readonly_and_rechecks_actual_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();profile,modules=self.fixture(root)
            with self.source_fixture(root):
                manifest=runtime.build_worker_source_manifest(root,profile)
                self.assertEqual(len(manifest['modules']),19);self.assertEqual(len(manifest['metadata']),3)
                with self.assertRaisesRegex(runtime.PackagingHold,'READONLY_WORKER'):
                    runtime.verify_worker_source_manifest(root,profile,manifest)
                with runtime.readonly_worker_scope():
                    proof=runtime.verify_worker_source_manifest(root,profile,manifest)
                    self.assertFalse(proof['scientific_population_admitted'])
                    row=modules[0];path=Path(row['path']);raw=path.read_bytes()
                    replacement=path.with_name('replacement');replacement.write_bytes(raw);replacement.replace(path)
                    with self.assertRaisesRegex(runtime.PackagingHold,'SOURCE_MANIFEST_CHANGED'):
                        runtime.verify_worker_source_manifest(root,profile,manifest)

    def test_worker_manifest_rejects_changed_source_or_rebound_metadata_and_unknown_fields(self):
        for change in ('bytes','profile_identity','missing_module','extra_field'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();profile,modules=self.fixture(root)
                with self.source_fixture(root):
                    manifest=runtime.build_worker_source_manifest(root,profile)
                    if change=='bytes':Path(modules[0]['path']).write_bytes(b'changed')
                    elif change=='profile_identity':
                        path=Path(profile['path']);replacement=path.with_name('new-profile')
                        replacement.write_bytes(path.read_bytes());replacement.replace(path)
                    elif change=='missing_module':manifest['modules']=manifest['modules'][:-1]
                    else:manifest['source_review_waiver']=True
                    with runtime.readonly_worker_scope(),self.assertRaises(runtime.PackagingHold):
                        runtime.verify_worker_source_manifest(root,profile,manifest)

    def test_parent_data_refresh_does_not_claim_or_replace_child_source_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();profile,_=self.fixture(root)
            with self.source_fixture(root):
                manifest=runtime.build_worker_source_manifest(root,profile)
                with patch.object(runtime,'validate',side_effect=runtime.PackagingHold('old source drift')):
                    # Current19+3 DATA is still exact, but full child authority
                    # refuses the changed original/predecessor closure.
                    current=runtime.refresh_worker_source_manifest_data(root,manifest)
                    self.assertEqual(current,manifest)
                    self.assertNotIn('status',current)
                    with runtime.readonly_worker_scope(),self.assertRaisesRegex(runtime.PackagingHold,'old source drift'):
                        runtime.verify_worker_source_manifest(root,profile,manifest)

    def test_parent_data_refresh_rejects_source_hash_identity_path_flags_and_unknown_metadata_drift(self):
        for change in ('hash','identity','path','table','flags','metadata_bytes','unknown_profile_bytes'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();profile,_=self.fixture(root)
                with self.source_fixture(root):
                    manifest=runtime.build_worker_source_manifest(root,profile)
                    if change=='hash':manifest['modules'][0]['sha256']='0'*64
                    elif change=='identity':manifest['modules'][0]['identity']['inode']+=1
                    elif change=='path':manifest['modules'][0]['path']=str(root/'other.py')
                    elif change=='table':manifest['modules'].pop()
                    elif change=='flags':manifest['source_review_change_flags']['admission_implementation_changed']=False
                    elif change=='metadata_bytes':Path(manifest['metadata'][2]['path']).write_bytes(b'changed')
                    else:
                        path=Path(profile['path']);value=json.loads(path.read_bytes())
                        value['unknown_field_changed']=True;path.write_text(json.dumps(value))
                    with self.assertRaises(runtime.PackagingHold):
                        runtime.refresh_worker_source_manifest_data(root,manifest)


if __name__=='__main__':unittest.main()
