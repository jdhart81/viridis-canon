"""Operational wiring fixtures: genuine CAS code, no live science admission."""
import ast
from copy import deepcopy
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(1,str(HERE.parent))
GATES=HERE.parents[2]/'RESEARCH_PIPELINE_v2/verification_coverage_gates'
if not GATES.is_dir():GATES=HERE.parents[1]
sys.path.insert(2,str(GATES))
import packaging_catalog as catalog
import packaging_runtime as runtime
import packaging_nightly_coverage as coverage
import nightly_checkpoint_guarded as checkpoint
import packaging_nightly as nightly
import methods_digest_registration_v3 as reg
import test_digest_registration_v3 as reg_fixtures


def real_cas():
    source=(GATES/'corpus_ledger.py').read_bytes();tree=ast.parse(source)
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='write_guarded_ledger')
    env=dict(Path=Path,os=os,tempfile=tempfile,hashlib=hashlib,json=json)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(GATES/'corpus_ledger.py'),'exec'),env)
    return env['write_guarded_ledger']


class DefaultRouteIntegration(unittest.TestCase):
    def fixture(self,root):
        empty,v3,consume=reg_fixtures.RegistrationV3Tests().scoped_rows(root)
        original=[{'id':f'publication:original:{i}','path':f'original/{i}','run_id':f'Run-{i+1:03d}',
            'certificate':f'certificates/{i}.json','certificate_sha256':'1'*64,
            'approved_publication_binding_reviews':['2'*64],'publication_registration_status':'PASS',
            'enforcement_acceptable':True,'scientific_scope':'original fixture predicate'}for i in range(35)]
        file=root/'v1.json';file.write_text(json.dumps({'standard':'VRS-METHODS-DIGEST-REGISTRATION-2'}))
        v1={'id':'publication:original-v1-group','path':'old-digest','registration_route':reg.GROUP_ROUTE,
            'registration_receipt':{'path':str(file),'sha256':runtime.sha(file.read_bytes())},
            'doi':'10.5281/zenodo.20000001','scientific_scope':'unchanged v1 fixture predicate',
            'publication_registration_status':'PASS','enforcement_acceptable':True,'certifies':False}
        previous={**empty,'publication_entities':[*deepcopy(original),v1,*v3],
            'enforcement_activation':{'path':'original-activation.json','sha256':'3'*64},'premise_declaration_cutover_run':'Run-188'}
        records=[]
        def original_preserve(ledger,old):
            records.append(('original',deepcopy(old['publication_entities'])))
            return {**deepcopy(ledger),'publication_entities':deepcopy(old['publication_entities'])}
        def old_preserve(ledger,old,*,legacy,consume):
            result=legacy(ledger,old)
            for row in old['publication_entities']:consume(root,row['registration_receipt'],result)
            result['publication_entities']+=deepcopy(old['publication_entities']);return result
        def old_audit(root,ledger,audit,*,consume):
            out=deepcopy(audit);out['methods_digest_groups']=[{'doi':v1['doi'],'deposit_paths':['old-digest'],
                'methods_digest_registration':{'tree_root':str(root),'receipt':v1['registration_receipt']}}]
            return out
        def read(root_,binding,*a,**kw):
            records.append(('consume',deepcopy(binding)))
            if binding==v3[0]['registration_receipt']:return consume(root_,binding,*a,**kw)
            return {'receipt':{'record_id':'20000001'}}
        labels=[]
        ctx=SimpleNamespace(require_registration=read)
        ctx.public_label_read_record=lambda row,legacy:(labels.append(deepcopy(row))or{'doi':row['doi'],'status':'READ','proposed_label_disagrees':False,'local_manuscript_public_checksum_matches':[]})
        corp=SimpleNamespace(discover=lambda r:([],[],[]),GENERATION_ROOT=root/'mirror',build=lambda root,cert,previous_ledger:original_preserve(previous_ledger,previous_ledger),
            preserve_publication_registrations=original_preserve,write_guarded_ledger=real_cas(),validate_uncertified_readback=lambda r,e:None)
        doi=SimpleNamespace(build_audit=lambda r,l:{'published_records':[],'counts':{}})
        old=SimpleNamespace(preserve=old_preserve,augment_audit=old_audit)
        original_import=catalog.importlib.import_module
        def imports(name,*a,**kw):
            if name=='corpus_ledger':return corp
            if name=='doi_audit':return doi
            if name=='public_metadata_readback':return SimpleNamespace(_read_record_legacy=lambda row:None)
            return original_import(name,*a,**kw)
        return previous,original,ctx,records,labels,old,imports

    def scope(self,root,ctx,old,imports):
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(runtime,'session',side_effect=lambda *a,**kw:contextlib.nullcontext()))
        stack.enter_context(patch.object(catalog,'checked_context',return_value=ctx))
        stack.enter_context(patch.object(catalog.importlib,'import_module',side_effect=imports))
        stack.enter_context(patch.object(reg,'_original_registrar',return_value=old))
        population=SimpleNamespace(baseline_rows=lambda r:[],preserving_population=lambda previous,baseline,fresh:None)
        stack.enter_context(patch.object(runtime,'load',return_value=population))
        # The copied coverage still imports the genuine corpus for its unchanged
        # banner policy. Its preserving consumer is the additive explicit seam.
        actual_corpus=SimpleNamespace(validate_uncertified_readback=lambda r,e:None,
            preserve_publication_registrations=lambda *a:(_ for _ in ()).throw(AssertionError('old convenience route bypass')))
        stack.enter_context(patch.dict(sys.modules,corpus_ledger=actual_corpus))
        stack.enter_context(catalog.operation_scope(root,{'fixture_profile':True},ctx))
        return stack

    def test_new_v3_canonical_cas_then_next_coverage_doi_and_labels_keep_entire_population(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();previous,original,ctx,calls,labels,old,imports=self.fixture(root)
            canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';canonical.parent.mkdir();canonical.write_text(json.dumps(previous))
            before=runtime.sha(canonical.read_bytes())
            with self.scope(root,ctx,old,imports):
                proposal=catalog.refresh_canonical(root,{'fixture_profile':True},registry_context=ctx,expected_sha256=before)
                self.assertEqual(proposal['publication_entities'],previous['publication_entities'])
                self.assertEqual(json.loads(canonical.read_bytes()),proposal)
                fresh=coverage._registrations(root,proposal,{'publication_entities':original[:27]})
                self.assertEqual(fresh['publication_entities'],previous['publication_entities'])
                audit=catalog.augment_audit(root,fresh,{'fixture_profile':True},registry_context=ctx)
                public=catalog.public_label_readback(root,audit,{'fixture_profile':True},registry_context=ctx)
            self.assertEqual(len(fresh['publication_entities']),38)
            self.assertEqual(audit['counts']['methods_digest_groups'],2)
            self.assertEqual(public['counts']['records'],2)
            self.assertEqual({r['doi']for r in labels},{'10.5281/zenodo.20000001','10.5281/zenodo.24000001'})
            self.assertTrue(all(len(rows)==35 for kind,rows in calls if kind=='original'))
            self.assertEqual(fresh['enforcement_activation'],previous['enforcement_activation'])
            self.assertEqual(fresh['premise_declaration_cutover_run'],'Run-188')
            self.assertIs(fresh['publication_entities'][-2]['certifies'],False)
            self.assertEqual(fresh['publication_entities'][-1]['certifies'],'LISTED_NOTE_SCOPE_ONLY')

    def test_changed_original_registration_or_v3_child_remains_visible_and_holds(self):
        for mode in ('original','v3-child'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();previous,original,ctx,calls,labels,old,imports=self.fixture(root)
                if mode=='original':previous['publication_entities'][0]['certificate_sha256']='0'*64
                else:previous['publication_entities'][-1]['certificate_sha256']='0'*64
                with self.scope(root,ctx,old,imports),self.assertRaises(ValueError):
                    coverage._registrations(root,previous,{'publication_entities':original[:27]})

    def test_canonical_predecessor_drift_cannot_write_fresh_proposal(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();previous,original,ctx,calls,labels,old,imports=self.fixture(root)
            canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';canonical.parent.mkdir();canonical.write_text(json.dumps(previous))
            before=canonical.read_bytes()
            with self.scope(root,ctx,old,imports),self.assertRaisesRegex(runtime.PackagingHold,'CANONICAL_EXACT_PREDECESSOR'):
                catalog.refresh_canonical(root,{'fixture_profile':True},registry_context=ctx,expected_sha256='0'*64)
            self.assertEqual(canonical.read_bytes(),before)

    def test_existing_cycle_report_cannot_return_cached_pass_when_current_labels_disagree(self):
        import packaging_run_flow as flow
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();previous,original,ctx,calls,labels,old,imports=self.fixture(root)
            ctx.observation_timing=lambda:{'fixture':True}
            ctx.public_label_read_record=lambda row,legacy:{'doi':row['doi'],'status':'READ',
                'proposed_label_disagrees':True,'local_manuscript_public_checksum_matches':[]}
            canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';canonical.parent.mkdir();canonical.write_text(json.dumps(previous))
            finish=root/'RESEARCH_PIPELINE_v2/nightly_checkpoints/fixture/FINISH.json';finish.parent.mkdir(parents=True)
            finish.write_text(json.dumps({'invocation_id':'fixture'}))
            output=root/'reports/verification-coverage/fixture';output.mkdir(parents=True)
            report=output/'NIGHTLY_CYCLE_REPORT.json';report.write_text(json.dumps({'enforcement':False,
                'checkpoint':flow.binding(finish),'status':'ENFORCING_PASS'}));before=report.read_bytes()
            fake_corpus=SimpleNamespace(render_markdown=lambda v:'fixture')
            fake_doi=SimpleNamespace(render_markdown=lambda v:'fixture')
            fake_triage=SimpleNamespace(build_triage=lambda *a:None,markdown=lambda v:'fixture')
            with self.scope(root,ctx,old,imports),patch.dict(sys.modules,corpus_ledger=fake_corpus,doi_audit=fake_doi,doi_triage=fake_triage):
                result=flow.cycle_report(root,finish,output)
            self.assertEqual(result['status'],'HOLD')
            self.assertEqual(report.read_bytes(),before)
            self.assertIn('current_default_replay',result)
            self.assertEqual(result['public_metadata_readback']['label_disagreements'],2)

    def test_no_operational_context_cannot_bypass_default_admission(self):
        with tempfile.TemporaryDirectory()as tmp:
            with self.assertRaisesRegex(runtime.PackagingHold,'EXPLICIT_DEFAULT_OPERATION_SCOPE_REQUIRED'):
                catalog.operation(Path(tmp).resolve())

    def test_checkpoint_uses_explicit_additive_cycle_with_explicit_bounded_timeout_and_holds_failures(self):
        import subprocess
        calls=[]
        def completed(command,**kwargs):
            calls.append((command,kwargs));return SimpleNamespace(returncode=2,stdout='HOLD fixture',stderr='')
        with patch.object(subprocess,'run',side_effect=completed):
            self.assertEqual(checkpoint.verification_coverage_after_checkpoint(Path('/fixture/FINISH.json'),enforce_new_artifacts=True),2)
        self.assertIn('packaging_nightly.py',calls[0][0][1]);self.assertEqual(calls[0][0][2],'cycle')
        self.assertIn('--enforce-new-artifacts',calls[0][0]);self.assertIn('--intake-reviewed-nightly',calls[0][0])
        self.assertEqual(calls[0][1]['timeout'],3000)
        with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('fixture',3000)):
            self.assertEqual(checkpoint.verification_coverage_after_checkpoint(Path('/fixture/FINISH.json'),enforce_new_artifacts=True),2)



class HealthFinalBoundaryTests(unittest.TestCase):
    def test_health_summary_is_emitted_only_after_operation_and_source_exit(self):
        for fail_at in (None,'observation-exit','source-exit'):
            with self.subTest(fail_at=fail_at),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                canonical.parent.mkdir();canonical.write_text(json.dumps({'enforcement_activation':None,'premise_declaration_cutover_run':None}))
                events=[];ctx=SimpleNamespace(observation_timing=lambda:{'fixture_only':True})
                @contextlib.contextmanager
                def scoped(name):
                    events.append(name+'-entry')
                    try:yield {'status':'SOURCE_ONLY_FIXTURE','transient_source_readback':{'transient_source_writes':2,'recovery_intent':{'fixture':True}}}if name=='source'else None
                    finally:
                        events.append(name+'-exit')
                        if fail_at==name+'-exit':raise RuntimeError(name+'-exit fixture')
                def owner(*args):
                    args[-1].mkdir(parents=True);return ctx
                fake_catalog=SimpleNamespace(owner_context=owner,operation_scope=lambda *a:scoped('observation'),
                    build=lambda *a,**kw:{'enforcement_activation':None,'premise_declaration_cutover_run':None,'publication_registration_enforcement_acceptable':True},
                    augment_audit=lambda *a,**kw:{'fixture':True},
                    public_label_readback=lambda *a,**kw:{'counts':{'unavailable':0,'label_disagreements':0}},observation_guard=lambda *a:None)
                imports={'packaging_catalog':fake_catalog,'publish_dated_bundles_guarded':SimpleNamespace(token=lambda:'explicit-fixture-secret'),
                         'packaging_nightly_coverage':SimpleNamespace(load_enforcement_activation=lambda *a:{'binding':None})}
                stdout=io.StringIO()
                with patch.object(nightly,'ROOT',root),patch.object(runtime,'nominated_binding',return_value={'fixture':True}),\
                     patch.object(runtime,'session',side_effect=lambda *a:scoped('source')),\
                     patch.object(nightly.importlib,'import_module',side_effect=imports.__getitem__),contextlib.redirect_stdout(stdout):
                    if fail_at:
                        with self.assertRaisesRegex(RuntimeError,fail_at+' fixture'):nightly.main(['health'])
                    else:self.assertEqual(nightly.main(['health']),0)
                self.assertEqual(events,['source-entry','observation-entry','observation-exit','source-exit'])
                if fail_at:self.assertEqual(stdout.getvalue(),'')
                else:
                    self.assertEqual(json.loads(stdout.getvalue())['status'],'FRESH_DEFAULT_FULL_POPULATION_READBACK_PASS')
                    self.assertEqual(json.loads(stdout.getvalue())['startup_transient_source_writes'],2)
                    body=json.loads(next((root/'reports/verification-coverage').rglob('DEFAULT_HEALTH_READBACK.json')).read_bytes())
                    self.assertEqual(body['startup_source_admission']['transient_source_readback']['transient_source_writes'],2)


class ObservationReplayTests(unittest.TestCase):
    def setup_context(self,root,folder='operation-1',clock=None,after_json=None,after_binary=None,begin=True):
        import urllib.request
        calls=[];now=[0]if clock is None else clock
        class Response:
            status=200
            def __init__(self,url):self.url=url
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def geturl(self):return self.url
            def read(self):
                calls.append(('binary',self.url))
                if after_binary is not None:after_binary()
                return b'%PDF-1.7\nactual fixture body'
        class Opener:
            def open(self,request,**kwargs):return Response(request.full_url)
        class Paced:
            def __init__(self,opener):self.opener=opener;self.deadline=None
            def open(self,*args,**kwargs):return self.opener.open(*args,**kwargs)
        class Transport:
            def __init__(self,host,token,out,opener=None):self.out=out;self.out.mkdir(parents=True);self.sequence=0
            def request(self,method,url,accept=None):
                calls.append(('json',url,accept));self.sequence+=1
                body={'id':'24000001','unknown_protected_field':{'kept':True},'accept':accept}
                (self.out/f'{self.sequence:03d}_GET.json').write_text(json.dumps({'method':'GET','url':url,'accept':accept,'response':body}))
                if after_json is not None:after_json()
                return body
        def context(root,binding,**kwargs):return SimpleNamespace(**kwargs)
        registry=SimpleNamespace(RegistryContext=context,CONTEXT={'authentication':'OWNER','owner_id':'1591505',
            'legacy_accept':'application/json','native_accept':'application/vnd.inveniordm.v1+json'})
        def imports(name):
            return {'zenodo_transport':SimpleNamespace(NoRedirect=urllib.request.HTTPRedirectHandler,ZenodoTransport=Transport),
                'manuscript_access_registry':registry,'first_digest_publisher':SimpleNamespace(PacedOpener=Paced)}[name]
        output=root/'reports/verification-coverage'/folder
        stack=contextlib.ExitStack();stack.enter_context(patch.object(runtime,'validate',return_value={'access_registry':{'fixture':True}}))
        stack.enter_context(patch.object(catalog.importlib,'import_module',side_effect=imports))
        stack.enter_context(patch.object(urllib.request,'build_opener',return_value=Opener()))
        stack.enter_context(patch.object(catalog.time,'monotonic',side_effect=lambda:now[0]))
        ctx=catalog.owner_context(root,{'fixture':True},'fixture-memory-secret-24-characters',output)
        stack.enter_context(patch.object(catalog,'checked_context',return_value=ctx))
        if begin:
            ctx.begin_observation_operation()
            stack.callback(ctx.end_observation_operation,failed=True)
        return stack,ctx,calls,now,output

    def test_actual_observations_are_once_per_key_and_rechecked_each_use(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
            with stack:
                body=ctx.owner_getter('24000001','application/json');body['unknown_protected_field']['kept']=False
                self.assertTrue(ctx.owner_getter('24000001','application/json')['unknown_protected_field']['kept'])
                first=ctx.download('24000001','Run-191-Paper.pdf')
                self.assertEqual(first,ctx.download('24000001','Run-191-Paper.pdf'))
                self.assertEqual(len(calls),2)
                info=json.loads(next(output.rglob('OBSERVATION.json')).read_bytes())
                self.assertIs(info['admission_cached'],False)
                self.assertIn('observed_at_utc',info)
                self.assertEqual(info['reuse_scope'],'THIS_BOUND_900_SECOND_OPERATION_ONLY')

    def test_any_tampered_body_receipt_stamp_or_file_holds(self):
        for target in ('ACTUAL_BODY.json','001_GET.json','OBSERVATION.json','Run-191-Paper.pdf','GET.json'):
            with self.subTest(target=target),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
                with stack:
                    ctx.owner_getter('24000001','application/json');ctx.download('24000001','Run-191-Paper.pdf')
                    path=next(output.rglob(target));path.write_bytes(b'tampered actual input')
                    with self.assertRaisesRegex(runtime.PackagingHold,'ACTUAL_OBSERVATION_INPUT_CHANGED'):
                        if target in ('Run-191-Paper.pdf','GET.json'):ctx.download('24000001','Run-191-Paper.pdf')
                        else:ctx.owner_getter('24000001','application/json')

    def test_expired_operation_holds_instead_of_returning_old_observation(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
            with stack:
                ctx.owner_getter('24000001','application/json');ctx.download('24000001','Run-191-Paper.pdf')
                clock[0]=catalog.OBSERVATION_SECONDS+1
                for call in (lambda:ctx.owner_getter('24000001','application/json'),lambda:ctx.download('24000001','Run-191-Paper.pdf')):
                    with self.assertRaisesRegex(runtime.PackagingHold,'BOUNDED_OBSERVATION_OPERATION_EXPIRED'):call()

    def test_separate_operation_does_not_reuse_prior_body_or_admission(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
            with stack:ctx.owner_getter('24000001','application/json');ctx.download('24000001','Run-191-Paper.pdf')
            second,c2,calls2,_,out2=self.setup_context(root,'operation-2')
            with second:c2.owner_getter('24000001','application/json');c2.download('24000001','Run-191-Paper.pdf')
            self.assertEqual(len(calls),2);self.assertEqual(len(calls2),2)
            self.assertNotEqual(output,out2)

    def test_inflight_expiry_after_actual_get_or_byte_response_holds(self):
        for mode in ('json','binary'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();clock=[0]
                def expire():clock[0]=catalog.OBSERVATION_SECONDS+1
                stack,ctx,calls,_,output=self.setup_context(root,clock=clock,
                    after_json=expire if mode=='json'else None,after_binary=expire if mode=='binary'else None)
                with stack,self.assertRaisesRegex(runtime.PackagingHold,'BOUNDED_OBSERVATION_OPERATION_EXPIRED'):
                    if mode=='json':ctx.owner_getter('24000001','application/json')
                    else:ctx.download('24000001','Run-191-Paper.pdf')
                self.assertEqual(len(calls),1)

    def test_long_scientific_phase_starts_fresh_900_second_clock_at_first_get(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
            with stack,self.assertRaisesRegex(runtime.PackagingHold,'BOUNDED_OBSERVATION_OPERATION_EXPIRED'):
                with catalog.operation_scope(root,{'fixture':True},ctx):
                    clock[0]=catalog.OBSERVATION_SECONDS+1000
                    ctx.owner_getter('1','application/json')
                    self.assertEqual(ctx.observation_timing()['clock_start'],'FIRST_ACTUAL_GET')
                    self.assertEqual(ctx.observation_timing()['observation_elapsed_seconds'],0)
                    clock[0]+=catalog.OBSERVATION_SECONDS+1
                    ctx.owner_getter('2','application/json')
            self.assertEqual(len(calls),1)

    def test_generic_label_spacing_and_response_expiry_prevent_later_requests(self):
        for mode in ('spacing','response'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
                requests=[]
                def anonymous(row):
                    requests.append(row['doi'])
                    if mode=='response':clock[0]=catalog.OBSERVATION_SECONDS+1
                    return {'status':'READ','local_manuscript_public_checksum_matches':[]}
                def sleep(seconds):
                    if mode=='spacing':clock[0]+=seconds
                with stack:
                    ctx.owner_getter('24000001','application/json')
                    if mode=='spacing':clock[0]=catalog.OBSERVATION_SECONDS-1
                    ctx.public_label_read_record=lambda row,legacy:legacy(row)
                    with patch.object(runtime,'session',side_effect=lambda *a:contextlib.nullcontext()),\
                         patch.object(catalog.importlib,'import_module',return_value=SimpleNamespace(_read_record_legacy=anonymous)),\
                         patch.object(catalog.time,'sleep',side_effect=sleep):
                        with self.assertRaisesRegex(runtime.PackagingHold,'BOUNDED_OBSERVATION_OPERATION_EXPIRED'):
                            with catalog.operation_scope(root,{'fixture':True},ctx):
                                catalog.scientific_data(root).scan_data={'explicit_fixture':True}
                                catalog.public_label_readback(root,{'published_records':[{'doi':'first'},{'doi':'second'}]},
                                                              {},registry_context=ctx)
                    self.assertEqual(requests,[]if mode=='spacing'else['first'])

    def test_outer_scope_is_single_use_and_nested_scopes_share_same_observations(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root)
            with stack:
                ctx.owner_getter('24000001','application/json')
                with catalog.operation_scope(root,{'fixture':True},ctx):
                    ctx.owner_getter('24000001','application/json')
                ctx.owner_getter('24000001','application/json')
                self.assertEqual(len(calls),1)
            with self.assertRaisesRegex(runtime.PackagingHold,'OBSERVATION_OPERATION_ALREADY_CLOSED'):
                with catalog.operation_scope(root,{'fixture':True},ctx):pass
            with self.assertRaisesRegex(runtime.PackagingHold,'ONE_ACTIVE_OBSERVATION_OPERATION_REQUIRED'):
                ctx.owner_getter('24000001','application/json')

    def test_final_rehash_or_manifest_failure_still_closes_context_and_restores_all_tokens(self):
        for mode in ('rehash','manifest'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();stack,ctx,calls,clock,output=self.setup_context(root,begin=False)
                with stack:
                    with self.assertRaisesRegex(RuntimeError,'final '+mode+' fixture'):
                        with catalog.operation_scope(root,{'fixture':True},ctx):
                            ctx.owner_getter('24000001','application/json')
                            data=catalog.scientific_data(root)
                            if mode=='rehash':
                                # The operation guard succeeds; the independent
                                # final science rehash fails at retention.
                                def retain(failed):
                                    with patch.object(data,'assert_current',side_effect=RuntimeError('final rehash fixture')):
                                        catalog.ScientificInputData.retain_final(data,failed)
                                data.retain_final=retain
                            else:
                                (output/'SCIENTIFIC_INPUT_DATA_FINAL.json').mkdir()
                                def retain(failed):
                                    try:catalog.ScientificInputData.retain_final(data,failed)
                                    except OSError as exc:raise RuntimeError('final manifest fixture')from exc
                                data.retain_final=retain
                    self.assertIsNone(catalog._OPERATION.get());self.assertIsNone(catalog._SCIENCE.get())
                    self.assertIsNone(catalog._READ_CAPTURE.get())
                    with self.assertRaisesRegex(runtime.PackagingHold,'OBSERVATION_OPERATION_ALREADY_CLOSED'):
                        with catalog.operation_scope(root,{'fixture':True},ctx):pass
                    with self.assertRaisesRegex(runtime.PackagingHold,'ONE_ACTIVE_OBSERVATION_OPERATION_REQUIRED'):
                        ctx.owner_getter('24000001','application/json')

if __name__=='__main__':unittest.main()
