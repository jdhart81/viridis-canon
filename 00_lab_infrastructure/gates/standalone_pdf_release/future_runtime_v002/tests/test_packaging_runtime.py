"""Trust boundary regressions. Synthetic receipts never certify live source."""
from copy import deepcopy
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import packaging_runtime as runtime
import install_packaging_runtime as installer


def put(root,name,value):
    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(installer.encoded(value))
    return {'path':str(path),'sha256':runtime.sha(path.read_bytes())}


class RuntimeTrustTests(unittest.TestCase):
    def fixture(self, root):
        provider=put(root,'provider.json',{'standard':'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1',
            'provider_tool':'mcp__codex_app__read_thread','thread_id':'01a12d47-02a3-78f3-beb4-6b8e1a079dd2',
            'user_messages':[{'type':'userMessage','id':'01a132f6-4708-7440-a9ba-ebf03deeb906',
                'content':[{'type':'text','text':runtime.USER_DIRECTIVE+'\n'}]}]})
        authority=put(root,'authority.json',{'standard':'VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1',
            'source':'Current user message in this Codex chat','user_text':runtime.USER_DIRECTIVE,
            'captured_at_utc':'2020-01-01T00:00:00Z','scientific_scope_changes':False,'provider_instruction':provider})
        fields={k:None for k in runtime.PROFILE_FIELDS}
        fields.update(standard=runtime.STANDARD,status=runtime.STATUS,canonical_root=str(root),
            installed_at_utc='2020-01-02T00:00:00Z',user_authority=authority,default_routes=runtime.DEFAULT_ROUTES)
        profile=put(root,runtime.PROFILE_PATH,fields)
        dummy=put(root,'review.json',{'fixture':True})
        nomination=put(root,runtime.NOMINATION_PATH,{'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-2',
            'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING','profile':profile,
            'installer_source':dummy,'merged_source_commit':'a'*40,'root_review_receipt':dummy})
        return fields,profile,provider

    def test_caller_profile_has_no_default_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();outside=put(root,'arbitrary.json',{})
            with self.assertRaisesRegex(runtime.PackagingHold,'CANONICAL_INSTALLED_PROFILE_PATH'):
                runtime.require_nomination(root,outside)

    def test_missing_nomination_cannot_be_replaced_by_cli_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();profile=put(root,runtime.PROFILE_PATH,{})
            with self.assertRaisesRegex(runtime.PackagingHold,'CANONICAL_INSTALLATION_NOMINATION'):
                runtime.require_nomination(root,profile)

    def test_crafted_exec_consumer_never_runs_before_anchor_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();fields,profile,provider=self.fixture(root)
            path=root/'crafted.py';marker=root/'EXECUTED'
            path.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("ran")\n')
            fields['legacy_consumer']={'path':str(path),'sha256':runtime.sha(path.read_bytes())}
            profile=put(root,runtime.PROFILE_PATH,fields)
            n=root/runtime.NOMINATION_PATH;nom=json.loads(n.read_bytes());nom['profile']=profile;n.write_bytes(installer.encoded(nom))
            with patch.object(runtime,'require_nomination',return_value={}),patch.object(runtime,'PROVIDER_SHA',provider['sha256']),patch.object(runtime,'same_binding',return_value=False),patch.object(runtime,'load',side_effect=AssertionError('no executable load')):
                with self.assertRaisesRegex(runtime.PackagingHold,'UNCHANGED_PREEXEC_ANCHOR'):
                    runtime.validate(root,profile)
            self.assertFalse(marker.exists())

    def test_future_install_time_holds_before_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();fields,profile,provider=self.fixture(root)
            fields['installed_at_utc']='2999-01-01T00:00:00Z';profile=put(root,runtime.PROFILE_PATH,fields)
            with patch.object(runtime,'require_nomination',return_value={}),patch.object(runtime,'load',side_effect=AssertionError('no exec')):
                with self.assertRaisesRegex(runtime.PackagingHold,'INSTALLATION_TIME'):runtime.validate(root,profile)

    def test_authority_from_after_install_holds_before_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();fields,profile,provider=self.fixture(root)
            ap=Path(fields['user_authority']['path']);a=json.loads(ap.read_bytes());a['captured_at_utc']='2021-01-01T00:00:00Z'
            fields['user_authority']=put(root,'authority.json',a);profile=put(root,runtime.PROFILE_PATH,fields)
            with patch.object(runtime,'require_nomination',return_value={}),patch.object(runtime,'PROVIDER_SHA',provider['sha256']),patch.object(runtime,'load',side_effect=AssertionError('no exec')):
                with self.assertRaisesRegex(runtime.PackagingHold,'AUTHORITY_TIME'):runtime.validate(root,profile)

    def source_origin(self,root):
        path=root/'source.py';path.write_bytes(b'# synthetic packaging fixture\n')
        blob=hashlib.sha1(b'blob '+str(len(path.read_bytes())).encode()+b'\0'+path.read_bytes()).hexdigest()
        row={'name':'source.py','path':str(path),'sha256':runtime.sha(path.read_bytes()),'git_path':'fixture/source.py'}
        oid='a'*40;tree='b'*40
        pr=put(root,'pr.json',{'state':'MERGED','baseRefName':'main','number':999,'url':'https://github.com/jdhart81/viridis-canon/pull/999',
            'mergeCommit':{'oid':oid},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in runtime.REQUIRED_CHECKS]})
        commit=put(root,'commit.json',{'sha':oid,'tree':{'sha':tree}})
        git=put(root,'tree.json',{'sha':tree,'truncated':False,'tree':[{'path':row['git_path'],'type':'blob','mode':'100644','sha':blob}]})
        return {'pull_request':pr,'merge_commit':commit,'tree':git},row

    def test_complete_exact_git_blob_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();origin,row=self.source_origin(root)
            self.assertEqual(runtime.source_proof(root,origin,[row])['proofs'][0]['sha256'],row['sha256'])
            tree=json.loads(Path(origin['tree']['path']).read_bytes());tree['tree'][0]['sha']='c'*40;origin['tree']=put(root,'tree.json',tree)
            with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_MERGED_BLOB'):runtime.source_proof(root,origin,[row])

    def test_truncated_tree_and_skipped_required_ci_do_not_establish_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();origin,row=self.source_origin(root)
            tree=json.loads(Path(origin['tree']['path']).read_bytes());tree['truncated']=True;origin['tree']=put(root,'tree.json',tree)
            with self.assertRaisesRegex(runtime.PackagingHold,'GENUINE_COMPLETE_MERGED_SOURCE'):runtime.source_proof(root,origin,[row])
            tree['truncated']=False;origin['tree']=put(root,'tree.json',tree)
            pr=json.loads(Path(origin['pull_request']['path']).read_bytes());pr['statusCheckRollup'][0]['conclusion']='SKIPPED';origin['pull_request']=put(root,'pr.json',pr)
            with self.assertRaisesRegex(runtime.PackagingHold,'REQUIRED_SOURCE_CI'):runtime.source_proof(root,origin,[row])

    def test_closed_module_inventory_rejects_omissions_duplicates_and_extras(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();rows=[]
            for name in runtime.MODULE_NAMES:
                p=root/name;p.write_text('# fixture\n');rows.append({'name':name,'path':str(p),'sha256':runtime.sha(p.read_bytes()),'git_path':runtime.GIT_PREFIX+name})
            self.assertEqual(len(runtime.module_table(root,rows)),17)
            for bad in (rows[:-1],[*rows,deepcopy(rows[0])],[{**r,'name':'other.py'}if i==0 else r for i,r in enumerate(rows)]):
                with self.assertRaisesRegex(runtime.PackagingHold,'CLOSED_ADDITIVE_MODULES'):runtime.module_table(root,bad)

    def test_install_nomination_is_bindings_only_not_runtime_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();_,profile,_=self.fixture(root)
            self.assertEqual(runtime.require_nomination(root,profile)['status'],'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING')
            p=root/runtime.NOMINATION_PATH;n=json.loads(p.read_bytes());n['status']='ACTUAL_INSTALLED_SOURCE_AND_DEFAULT_ROUTES_READBACK_PASS';p.write_bytes(installer.encoded(n))
            with self.assertRaisesRegex(runtime.PackagingHold,'ROOT_REVIEWED_INSTALLED_NOMINATION'):runtime.require_nomination(root,profile)



class InstallerPreflightTests(unittest.TestCase):
    def fixture(self,root):
        original=root/'old.py';original.write_bytes(b'# old fixture\n')
        publisher=root/'_ZENODO_DEPOSITS/publish_dated_bundles.py';publisher.parent.mkdir();publisher.write_bytes(b'# old fixture\n')
        original_sha=runtime.sha(original.read_bytes());before_sha=runtime.sha(publisher.read_bytes())
        anchor=put(root,'anchor.json',{'fixture':True})
        scope=put(root,'scope.json',{'source_origin':{'merged_pr':anchor,'merged_commit':anchor,'merged_tree':anchor,
            'source_rows':[{'name':'publish_dated_bundles.py'if i==0 else str(i)+'.py','path':'original-'+str(i),
                'sha256':'1'*64,'git_path':'fixture/'+str(i)}for i in range(130)]}})
        provider=put(root,'provider.json',{'synthetic':True})
        authority=put(root,'authority.json',{'standard':'VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1',
            'source':'Current user message in this Codex chat','user_text':runtime.USER_DIRECTIVE,
            'captured_at_utc':'2020-01-01T00:00:00Z','scientific_scope_changes':False,'provider_instruction':provider})
        file=Path(installer.__file__).resolve();row={'name':file.name,'path':str(file),'sha256':runtime.sha(file.read_bytes()),'git_path':runtime.GIT_PREFIX+file.name}
        hashes={row['name']:row['sha256']}
        source_review=put(root,'source-review.json',{'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-2',
            'status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS','reviewer':'explicit synthetic test fixture','source_hashes':hashes,
            'legacy_closure':anchor,'scientific_admission_changed':False,'historical_sources_changed':False,
            'review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,
            'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK'})
        plan={'standard':'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-2','status':'ROOT_REVIEWED_READY_NOT_INSTALLED',
            'canonical_root':str(root),'source_modules':[row],'source_origin':{'synthetic':True},'source_review':source_review,
            'user_authority':authority,'access_registry':anchor,'historical_publisher':{'path':str(publisher),'sha256':original_sha},
            'installed_at_utc':'2020-01-02T00:00:00Z','root_review':None,
            'predecessor_installation':runtime.PREDECESSOR_INSTALLATION,'transient_rehydration':runtime.TRANSIENT_REHYDRATION_POLICY}
        def finish():
            review={'standard':'VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-2','status':'EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS',
                'reviewer':'synthetic test reviewer','plan_projection_sha256':runtime.sha(installer.encoded({k:v for k,v in plan.items()if k!='root_review'})),
                'merged_source_commit':'a'*40,'source_hashes':hashes,'historical_publisher_sha256':original_sha,'scientific_or_authority_changes':False}
            plan['root_review']=put(root,'root-review.json',review)
            return put(root,'plan.json',plan)
        patches=[patch.object(installer,'ROOT',root),patch.object(installer,'ORIGINAL_PUBLISHER_SHA',original_sha),
            patch.object(runtime,'HISTORICAL_PUBLISHER',{'path':str(publisher),'sha256':before_sha}),
            patch.object(runtime,'predecessor_installation',return_value={'source_only_fixture':True}),
            patch.object(runtime,'legacy_transient_precheck',return_value={'transient_source_writes':0,'synthetic_fixture':True}),patch.object(runtime,'LEGACY_SCOPE',scope),
            patch.object(runtime,'LEGACY_CLOSURE',anchor),patch.object(runtime,'LEGACY_CONSUMER',anchor),
            patch.object(runtime,'SESSION_CONSUMER',anchor),patch.object(runtime,'PROVIDER_SHA',provider['sha256']),
            patch.object(runtime,'module_table',return_value=[row]),
            patch.object(runtime,'source_proof',return_value={'merge_commit':'a'*40})]
        return plan,finish,patches,publisher,before_sha

    def run_fixture(self,root,plan,finish,patches,*,go=False):
        import contextlib
        with contextlib.ExitStack()as stack:
            mocks=[stack.enter_context(p)for p in patches]
            value=installer.install(root,finish(),go=go)
            calls=mocks[-1].call_args_list
            self.assertEqual(len(calls[-1].args[2]),130)
            return value

    def test_exact_bootstrap_preflight_is_read_only(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root)
            value=self.run_fixture(root,p,f,ps)
            self.assertEqual(value['writes'],0)
            self.assertEqual(runtime.sha(publisher.read_bytes()),before)
            self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

    def test_changed_executed_installer_holds_before_install(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root)
            p['source_modules'][0]['sha256']='0'*64
            with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_EXECUTED_INSTALLER_SOURCE'):
                self.run_fixture(root,p,f,ps,go=True)
            self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

    def test_invalid_future_or_naive_install_time_never_mutates(self):
        for value in ('not-a-time','2999-01-01T00:00:00Z','2020-01-02T00:00:00','2019-12-31T00:00:00Z'):
            with self.subTest(value=value),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root);p['installed_at_utc']=value
                with self.assertRaises(ValueError):self.run_fixture(root,p,f,ps,go=True)
                self.assertEqual(runtime.sha(publisher.read_bytes()),before)
                self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

    def test_duplicate_or_partial_install_is_not_blindly_replaced(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root)
            target=(root/runtime.PROFILE_PATH).parent;target.mkdir();(target/'INSTALL_HOLD.json').write_text('partial fixture')
            with self.assertRaisesRegex(runtime.PackagingHold,'NO_REPLACE_OR_DUPLICATE_INSTALL'):
                self.run_fixture(root,p,f,ps,go=True)
            self.assertEqual((target/'INSTALL_HOLD.json').read_text(),'partial fixture')
            self.assertEqual(runtime.sha(publisher.read_bytes()),before)

    def test_unknown_current_publisher_cannot_be_restored(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root);publisher.write_bytes(b'# unknown actual edit\n')
            with self.assertRaisesRegex(runtime.PackagingHold,'SOURCE_HASH_OR_RACE'):
                self.run_fixture(root,p,f,ps,go=True)
            self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

    def test_source_review_cannot_claim_unperformed_runtime_admission(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p,f,ps,publisher,before=self.fixture(root)
            review=json.loads(Path(p['source_review']['path']).read_bytes());review['actual_live_runtime_admission']=True
            p['source_review']=put(root,'source-review.json',review)
            with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_INSTALL_SOURCE_REVIEW'):
                self.run_fixture(root,p,f,ps,go=True)
            self.assertFalse((root/runtime.PROFILE_PATH).parent.exists())

class InstalledPlanBindingTests(unittest.TestCase):
    def fixture(self,root):
        prototype=root/'reviewed-source';prototype.mkdir()
        installed=root/Path(runtime.PROFILE_PATH).parent;installed.mkdir(parents=True)
        rows=[];current=[]
        for name in runtime.MODULE_NAMES:
            raw=b'# source-binding fixture\n';p=prototype/name;p.write_bytes(raw);(installed/name).write_bytes(raw)
            row={'name':name,'path':str(p),'sha256':runtime.sha(raw),'git_path':runtime.GIT_PREFIX+name}
            rows.append(row);current.append({**row,'path':str(installed/name)})
        authority=put(root,'authority.json',{'synthetic':True})
        publisher=root/'_ZENODO_DEPOSITS/publish_dated_bundles.py';publisher.write_bytes(b'# pointer-only fixture\n')
        publisher_binding={'path':str(publisher),'sha256':runtime.sha(publisher.read_bytes())}
        profile={k:authority for k in ('source_origin','source_review','user_authority','access_registry')}
        profile.update(installed_at_utc='2020-01-01T00:00:00Z',modules=current,
            predecessor_installation=runtime.PREDECESSOR_INSTALLATION,transient_rehydration=runtime.TRANSIENT_REHYDRATION_POLICY)
        plan={'standard':'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-2','status':'ROOT_REVIEWED_READY_NOT_INSTALLED',
            'canonical_root':str(root),'source_modules':rows,'historical_publisher':publisher_binding,'root_review':None,
            'predecessor_installation':runtime.PREDECESSOR_INSTALLATION,'transient_rehydration':runtime.TRANSIENT_REHYDRATION_POLICY,
            **{k:profile[k]for k in ('source_origin','source_review','user_authority','access_registry','installed_at_utc')}}
        review={'standard':'VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-2','status':'EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS',
            'reviewer':'synthetic fixture reviewer','plan_projection_sha256':runtime.sha(installer.encoded({k:v for k,v in plan.items()if k!='root_review'})),
            'merged_source_commit':'a'*40,'source_hashes':{r['name']:r['sha256']for r in rows},
            'historical_publisher_sha256':installer.ORIGINAL_PUBLISHER_SHA,'scientific_or_authority_changes':False}
        plan['root_review']=put(root,'root-review.json',review)
        (installed/'INSTALL_PLAN.json').write_bytes(installer.encoded(plan))
        row=next(r for r in rows if r['name']=='install_packaging_runtime.py')
        nomination={'installer_source':{k:row[k]for k in ('path','sha256')},'root_review_receipt':plan['root_review'],'merged_source_commit':'a'*40}
        return profile,nomination,publisher_binding

    def test_installed_source_and_root_review_bind_the_same_exclusive_plan(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();profile,nom,publisher=self.fixture(root)
            with patch.object(runtime,'HISTORICAL_PUBLISHER',publisher):runtime.require_installed_plan(root,profile,nom,{'merge_commit':'a'*40})
            wrong=put(root,'unrelated-review.json',{'reviewer':'unrelated'})
            with self.assertRaisesRegex(runtime.PackagingHold,'NOMINATED_ACTUAL_ROOT_REVIEW'):
                runtime.require_installed_plan(root,profile,{**nom,'root_review_receipt':wrong},{'merge_commit':'a'*40})

    def test_nomination_cannot_self_record_an_unrelated_installer(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();profile,nom,publisher=self.fixture(root)
            original=nom['installer_source'];other=root/'other-install.py';other.write_bytes(Path(original['path']).read_bytes())
            with self.assertRaisesRegex(runtime.PackagingHold,'NOMINATED_PROVED_EXECUTED_INSTALLER'):
                runtime.require_installed_plan(root,profile,{**nom,'installer_source':{'path':str(other),'sha256':original['sha256']}},{'merge_commit':'a'*40})

if __name__=='__main__':unittest.main()
