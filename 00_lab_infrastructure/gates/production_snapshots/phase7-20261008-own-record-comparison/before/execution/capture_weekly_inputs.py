"""Explicit root-only GET capture. No token retrieval or mutation entry point.

Run preflight_sources before root obtains its existing approved memory token.
The capture repeats source/runtime checks and refuses every non-GET request.
"""
from pathlib import Path
import hashlib,json,types,urllib.request,re
import prepare_weekly_configuration as c

class GetOnlyOpener:
    def __init__(self,inner,record_id):self.inner=inner;self.record_id=record_id
    def open(self,request,timeout=120):
        c.need(request.get_method()=='GET'and request.data is None,'GET_ONLY_CAPTURE')
        url=request.full_url
        if url!='https://zenodo.org/api/records/'+self.record_id:
            from readonly_account import require_url
            require_url(url)
        return self.inner.open(request,timeout=timeout)

def load(root,binding,name):
    p,b=c.bound_raw(root,binding);m=types.ModuleType(name);m.__file__=str(p);exec(compile(b,str(p),'exec'),m.__dict__);c.need(hashlib.sha256(c.raw(p)).hexdigest()==binding['sha256'],'BOUND_SOURCE_EXEC_RACE');return m

def preflight_sources(root,source_inputs):
    root=Path(root).resolve(strict=True);pins,origin=c.source_materials(root,source_inputs)
    pr=c.bound(root,source_inputs['merged_pr'])[1];checks=pr.get('statusCheckRollup');required={'gitleaks','report-only-consumers','verify-catalog','verify','verify-functions','lean-build-current','lean-build-p0','deposit-verify'}
    c.need(isinstance(checks,list)and required<={x.get('name')for x in checks if x.get('status')=='COMPLETED'and x.get('conclusion')=='SUCCESS'}and all(x.get('status')=='COMPLETED'and x.get('conclusion')in{'SUCCESS','SKIPPED'}for x in checks),'ALL_REAL_EXACT_HEAD_CHECKS')
    builder=load(root,source_inputs['source_session_consumer'],'_root_exact_sources');builder.verify_loaded(pins,root)
    with builder.source_session(root,pins):
        from runtime_closure_view import require_current
        consumer=load(root,source_inputs['runtime_consumer'],'_root_current_runtime')
        closure=require_current(consumer,source_inputs['current_runtime_closure'],root=root,purpose_pins=pins)
        c.need(all(row in pins for row in closure['source_pins']),'CURRENT_RUNTIME_SUBSET')
        # Complete default preserving consumer, no derived-status repair.
        import corpus_ledger
        ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before=c.raw(ledger_path);ledger=json.loads(before)
        scanned=corpus_ledger.build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=ledger)
        c.need(scanned.get('publication_entities')==ledger.get('publication_entities')and all(x.get('enforcement_acceptable')is True for x in scanned['publication_entities']),'FRESH_DEFAULT_POPULATION_BEFORE_CREDENTIAL')
        builder.verify_loaded(pins,root);c.need(c.raw(ledger_path)==before,'SSOT_CHANGED_DURING_SOURCE_PREFLIGHT')
    return {'purpose_source_pins':pins,'source_origin':origin,'before_ssot_sha256':hashlib.sha256(before).hexdigest(),'status':'ACTUAL_SOURCE_RUNTIME_DEFAULT_PREFLIGHT_NOT_PUBLICATION_CLEARANCE','certifies':False,'zenodo_writes':0}

def capture_inputs(root,source_inputs,week,record_id,token,output,*,source_registration):
    root=Path(root).resolve(strict=True);c.need(root==c.ROOT.resolve(strict=True)and re.fullmatch('[1-9][0-9]*',str(record_id))is not None and isinstance(token,str)and len(token)>=24,'ROOT_EXPLICIT_MEMORY_CAPTURE')
    proof=preflight_sources(root,source_inputs);pins=proof['purpose_source_pins'];out=Path(output);c.need(out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists(),'NEW_OWNED_GET_OUTPUT');out.mkdir(parents=True,exist_ok=False)
    builder=load(root,source_inputs['source_session_consumer'],'_root_exact_get_source_session')
    with builder.source_session(root,pins):
        import zenodo_transport as t
        import owned_weekly_discovery as q
        from first_digest_publisher import PacedOpener
        opener=GetOnlyOpener(PacedOpener(urllib.request.build_opener(t.NoRedirect())),str(record_id));transport=t.ZenodoTransport('zenodo.org',token,out/'transport',opener=opener)
        url='https://zenodo.org/api/records/'+str(record_id)
        transport.request('GET',url,accept='application/json');legacy=c.binding(transport.out/'001_GET.json')
        transport.request('GET',url,accept='application/vnd.inveniordm.v1+json');native=c.binding(transport.out/'002_GET.json')
        account=q.capture(root,week,token,out/'account-discovery',opener)
        _,discovery=c.bound(root,account)
        import methods_digest_registration as registrar
        import weekly_digest_executor as engine
        source=registrar.require_registration(root,source_registration)
        c.need(source['receipt']['record_id']==str(record_id),'ACTUAL_DEFAULT_METADATA_SOURCE')
        if discovery['start_kind']=='NEW_VERSION':c.need(discovery['record_id']==str(record_id)and source['receipt']['release_week']==week,'LATEST_SAME_WEEKLY_SOURCE_ONLY')
        else:c.need(discovery['start_kind']=='CREATE_WEEK'and discovery['record_id']is None and discovery['concept_id']is None and source['receipt']['release_week']!=week,'ACTUAL_NEW_WEEK_METADATA_SOURCE_ONLY')
        _,native_value=c.bound(root,native)
        engine.require_prestart_source(root,{'predecessor_record_id':str(record_id),'source_concept_id':native_value['response']['parent']['id'],'source_native_receipt':native,'source_native_before_create':native})
        result={'standard':'VRS-OWNED-DIGEST-ROOT-GET-INPUTS-1','status':'GETS_CAPTURED_NOT_PUBLICATION_CLEARANCE','source_legacy_receipt':legacy,'source_native_receipt':native,'source_native_before_create':native,'account_discovery':account,'preflight_ssot_sha256':proof['before_ssot_sha256'],'certifies':False,'zenodo_writes':0}
        builder.verify_loaded(pins,root)
    encoded=c.encode(result);c.need(token.encode()not in encoded,'NO_CREDENTIAL_IN_CAPTURE');p=out/'RESULT.json';c.immutable(p,encoded);return c.binding(p)
if __name__=='__main__':raise SystemExit('HOLD: explicit root preflight; memory-only credential; GET-only capture')
