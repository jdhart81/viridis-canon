"""One no-retry first Methods Digest executor, explicitly invoked by root only.

No credential lookup, local Lean, certificate issuance, ordinary batch replay,
or permissive server-field rule is implemented. All actual HTTP mutations use
the unchanged hash-pinned ZenodoTransport. No CLI accepts a token or auto-runs.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt,hashlib,json,os,re,sys,time,urllib.parse,urllib.request,importlib.abc,importlib.machinery,importlib.util
from pathlib import Path
from readonly_account import AccountDiscovery
from mutation_journal_writer import JournalWriter
import digest_metadata as metadata
import first_digest_state as state
import publisher_previews
import publisher_recovery

NATIVE='application/vnd.inveniordm.v1+json'
FIRST8=('Run-125','Run-126','Run-128','Run-129','Run-130','Run-131','Run-134','Run-141')
STANDARD='VRS-PHASE7-FIRST-METHODS-DIGEST-EXECUTION-1'
class PublishHold(ValueError):pass
def require(v,c):
    if not v:raise PublishHold('HOLD_'+c)
def raw_json(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def read_regular(p):
    p=Path(p);require(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'REGULAR_UNSYMLINKED_FILE');a=p.stat();b=p.read_bytes();z=p.stat();require((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'FILE_READ_RACE');return b
def immutable(p,b):
    p=Path(p);require(not any(x.is_symlink()for x in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
def bound(root,value):
    require(isinstance(value,dict)and set(value)=={'path','sha256'},'CLOSED_EVIDENCE_BINDING');p=Path(value['path']);require(p.is_absolute()and p.resolve(strict=True).is_relative_to(root),'EVIDENCE_CONTAINMENT');raw=read_regular(p);require(hashlib.sha256(raw).hexdigest()==value['sha256'],'EVIDENCE_HASH');return p,json.loads(raw)
def load_source(path,name):
    # Root pins the complete own repository module closure; no stale bytecode.
    module=type(sys)(name);module.__file__=str(path);sys.modules[name]=module;exec(compile(read_regular(path),str(path),'exec'),module.__dict__);return module
def require_module_pins(root,pins):
    require(isinstance(pins,list)and pins,'RUNTIME_MODULE_PINS_REQUIRED');names=set();paths=[]
    for row in pins:
        require(isinstance(row,dict)and set(row)=={'name','path','sha256'}and row['name'].endswith('.py')and row['name']not in names,'MODULE_CLOSURE_ROW');names.add(row['name']);p=Path(row['path']);require(p.name==row['name']and p.is_absolute()and p.resolve(strict=True).is_relative_to(root),'MODULE_SOURCE_CONTAINMENT');require(sha(p)==row['sha256'],'RUNTIME_MODULE_CHANGED:'+row['name']);read_regular(p);paths.append(p)
    required={'methods_digest.py','phase7_audit_policy.py','phase7_mutation_baseline.py','zenodo_transport.py','server_managed_fields.py','publication_preservation.py','file_byte_metadata.py','scoped_release.py','certificate_inspection.py','nonvacuity_tier0.py','probe_observations.py','phase7_claim_label_render.py','digest_metadata.py','first_digest_state.py','readonly_account.py','mutation_journal_writer.py','publisher_previews.py','publisher_recovery.py','phase7_policy_versions.py','methods_digest_registration.py','mirror_parity.py'}
    require(required<=names,'ACTUAL_COMPLETE_CONSUMER_CLOSURE_REQUIRED');return paths
def require_plan(root,package,plan):
    fields={'standard','status','canonical_root','package_path','digest_manifest','digest_publication_binding','source_before_metadata','source_legacy','source_native','relation_vocabulary_source','community_mirror_proof','runtime_pins','expected_writes','first_notes'}
    require(isinstance(plan,dict)and set(plan)==fields and plan['standard']=='VRS-PHASE7-FIRST-DIGEST-PUBLISH-PLAN-1'and plan['status']=='FROZEN_READY_NOT_EXECUTED','CLOSED_FROZEN_PLAN_REQUIRED')
    require(plan['canonical_root']==str(root)and plan['package_path']==str(package),'PLAN_ROOT_PACKAGE');require(plan['expected_writes']==9 and plan['first_notes']in [list(FIRST8),[r for r in FIRST8 if r!='Run-130']],'EXACT_CLEARED_FIRST_COHORT_NINE_WRITES')
    _,manifest=bound(root,plan['digest_manifest']);bound(root,plan['digest_publication_binding']);require(Path(plan['digest_manifest']['path'])==package/'DIGEST_MANIFEST.json'and Path(plan['digest_publication_binding']['path'])==package/'PUBLICATION_BINDING.json','OWN_PACKAGE_BINDINGS')
    before_path,before=bound(root,plan['source_before_metadata']);_,source_legacy=bound(root,plan['source_legacy']);_,source_native=bound(root,plan['source_native']);_,vocab=bound(root,plan['relation_vocabulary_source']);_,mirror=bound(root,plan['community_mirror_proof'])
    require(mirror.get('status')=='SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN'and mirror.get('public_post_publish_exact_preservation')is True,'ACTUAL_APPROVED_COMMUNITY_FIXTURE_REQUIRED')
    require(manifest.get('source_metadata',{}).get('path')==str(before_path)and manifest['source_metadata']['sha256']==sha(before_path),'SOURCE_IS_AUDITED_DIGEST_INPUT')
    require([n['run_id']for n in manifest['notes']]==plan['first_notes'],'EXACT_NOTE_COHORT')
    require(manifest['release_week']=='2026-W41'and manifest['public_metadata']['title']=='Viridis Methods Digest — 2026-W41','APPROVED_WEEKLY_TITLE')
    source_id=state.identifier(source_legacy['id']);require(source_legacy.get('doi')==before.get('doi')and source_native.get('id')==source_id,'AUDITED_SOURCE_PAIR_IDENTITY')
    templates=[r['relation_type']for r in vocab.get('metadata',{}).get('related_identifiers',[])if r.get('relation_type',{}).get('id')=='issupplementto'];require(templates and all(metadata.exact(t,templates[0])for t in templates),'SOURCE_BOUND_RELATION_VOCABULARY')
    api=state.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],before));predicted=metadata.native_metadata(manifest['public_metadata'],before,source_legacy,source_native,templates[0]);from methods_digest_registration import source_custom_fields
    source_custom_fields(manifest['public_metadata'],source_legacy,source_native);require_module_pins(root,plan['runtime_pins'])
    return {'manifest':manifest,'before_metadata':before,'source_legacy':source_legacy,'source_native':source_native,'source_id':source_id,'relation_template':templates[0],'api_payload':api,'native_metadata':predicted,'mirror':mirror}

class PacedOpener:
    def __init__(self,opener):self.opener=opener;self.last=0;self.deadline=None
    def open(self,*args,**kwargs):
        wait=2.05-(time.monotonic()-self.last)
        if wait>0:time.sleep(wait)
        self.last=time.monotonic()
        if self.deadline is not None:
            remaining=self.deadline-time.monotonic();require(remaining>0,'PREVIEW_TEN_MINUTE_DEADLINE');kwargs['timeout']=min(kwargs.get('timeout',120),remaining)
        return self.opener.open(*args,**kwargs)
class Downloads:
    def __init__(self,token,opener,out):self._token=token;self.opener=opener;self.out=Path(out);self.sequence=0;self.public=[]
    def get(self,name,rid,expected,*,published,published_url=None):
        require(re.fullmatch('[A-Za-z0-9_.-]+',name)is not None and state.identifier(rid)==rid,'DOWNLOAD_IDENTITY')
        require(type(expected['size'])is int and 0<=expected['size']<=2*1024*1024*1024,'DOWNLOAD_EXPECTED_SIZE')
        url='https://zenodo.org/api/records/'+rid+('/files/'if published else'/draft/files/')+name+'/content'
        if published:
            require(isinstance(published_url,str)and published_url==url,'ACTUAL_OWN_PUBLIC_FILE_URL_REQUIRED');url=published_url
        else:require(published_url is None,'DRAFT_DOWNLOAD_HAS_PUBLIC_URL')
        self.sequence+=1
        folder=self.out/('public'if published else'draft')/f'{self.sequence:03d}';folder.mkdir(parents=True,exist_ok=True)
        headers={}if published else{'Authorization':'Bearer '+self._token};req=urllib.request.Request(url,method='GET',headers=headers)
        with self.opener.open(req,timeout=120)as response:
            require(response.status==200 and getattr(response,'url',url)==url,'OWN_FILE_PUBLIC_GET');data=response.read(expected['size']+1)
        require(len(data)==expected['size']and hashlib.sha256(data).hexdigest()==expected['sha256']and hashlib.md5(data).hexdigest()==expected['md5'],'DOWNLOADED_EXACT_OWN_BYTES')
        require(self._token.encode()not in data,'CREDENTIAL_IN_DOWNLOAD');path=folder/name;immutable(path,data)
        row={'filename':name,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest(),'bytes':len(data),'path':str(path),'authenticated':not published};immutable(folder/(name+'.GET.json'),raw_json({'standard':'VRS-PHASE7-EXACT-FILE-GET-1','method':'GET','status':'EXACT_BYTES_PASS',**row}))
        if published:
            self.public=[r for r in self.public if r['filename']!=name];self.public.append({k:v for k,v in row.items()if k!='authenticated'})
        return data

class PinnedLoader(importlib.abc.Loader):
    def __init__(self,path,expected):self.path=path;self.expected=expected
    def create_module(self,spec):return None
    def exec_module(self,module):
        raw=read_regular(self.path);require(hashlib.sha256(raw).hexdigest()==self.expected,'PINNED_IMPORT_CHANGED')
        module.__file__=str(self.path);exec(compile(raw,str(self.path),'exec'),module.__dict__)
        require(sha(self.path)==self.expected,'PINNED_IMPORT_CHANGED_DURING_EXECUTION')
class PinnedFinder(importlib.abc.MetaPathFinder):
    def __init__(self,root,pins):self.root=root;self.paths={p['name'][:-3]:(Path(p['path']),p['sha256'])for p in pins}
    def find_spec(self,fullname,path=None,target=None):
        if fullname in self.paths:
            source,expected=self.paths[fullname];return importlib.util.spec_from_loader(fullname,PinnedLoader(source,expected),origin=str(source))
        spec=importlib.machinery.PathFinder.find_spec(fullname,path)
        source=getattr(spec,'origin',None)
        if source and source not in {'built-in','frozen'}and Path(source).resolve().is_relative_to(self.root):raise PublishHold('HOLD_UNPINNED_OWN_SOURCE_IMPORT')
        return None
class Runtime:
    def __init__(self,root,plan):
        paths=require_module_pins(root,plan['runtime_pins']);self.root=root;self.plan=plan;self.finder=None
        for p in paths:
            if str(p.parent)not in sys.path:sys.path.insert(0,str(p.parent))
        for name,module in list(sys.modules.items()):
            source=getattr(module,'__file__',None)
            if name in {p.stem for p in paths}or(source and Path(source).resolve().is_relative_to(root)):sys.modules.pop(name,None)
        self.finder=PinnedFinder(root,plan['runtime_pins']);sys.meta_path.insert(0,self.finder)
        try:
            import importlib
            self.d=importlib.import_module('methods_digest');self.policy=importlib.import_module('phase7_audit_policy');self.mut=importlib.import_module('phase7_mutation_baseline');self.transport=importlib.import_module('zenodo_transport');self.sm=importlib.import_module('server_managed_fields');self.preservation=importlib.import_module('publication_preservation');self.registration=importlib.import_module('methods_digest_registration')
            # Executor helper code is also compiled from its reviewed source.
            self.metadata=importlib.import_module('digest_metadata');self.state=importlib.import_module('first_digest_state');self.account=importlib.import_module('readonly_account');self.journal=importlib.import_module('mutation_journal_writer');self.previews=importlib.import_module('publisher_previews');self.recovery=importlib.import_module('publisher_recovery')
        except Exception:self.close();raise
    def fresh(self,package,plan):
        require_module_pins(self.root,plan['runtime_pins']);return self.d.require_publication_bound(package,self.root)
    def close(self):
        if self.finder in sys.meta_path:sys.meta_path.remove(self.finder)


def _execute(root,package,plan,output,token,runtime,*,account_factory=AccountDiscovery,transport_factory=None,download_factory=Downloads,clock=lambda:dt.datetime.now(dt.timezone.utc).isoformat(),monotonic=time.monotonic,sleep=time.sleep):
    prepared=require_plan(root,package,plan);manifest=prepared['manifest'];require(not output.exists()and output.resolve().is_relative_to(root/'reports/verification-coverage'),'IMMUTABLE_CANONICAL_EXECUTION_ONLY');output.mkdir(parents=True,exist_ok=False);immutable(output/'PLAN.json',raw_json(plan));immutable(output/'API_METADATA_PAYLOAD.json',raw_json(prepared['api_payload']));immutable(output/'EXPECTED_NATIVE_METADATA.json',raw_json(prepared['native_metadata']))
    d,policy,mut,sm,preserve=runtime.d,runtime.policy,runtime.mut,runtime.sm,runtime.preservation
    opener=PacedOpener(urllib.request.build_opener(runtime.transport.NoRedirect()));factory=transport_factory or runtime.transport.ZenodoTransport;t=factory('zenodo.org',token,output/'transport',opener=opener);downloads=download_factory(token,opener,output/'downloads')
    uploads=[dict(name=u['filename'],path=str(package/u['filename']),size=u['bytes'],sha256=u['sha256'],md5=u['md5'])for u in manifest['uploads']]
    for name in('DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
        data=read_regular(package/name);uploads.append({'name':name,'path':str(package/name),'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest()})
    require(len(uploads)==6 and len({u['name']for u in uploads})==6,'EXACT_SIX_UPLOADS');immutable(output/'APPROVED_SIX_FILES.json',raw_json({'files':uploads}))
    result={'standard':STANDARD,'status':'HOLD','release_week':manifest['release_week'],'notes':plan['first_notes'],'writes':0,'record_id':None,'doi':None,'phase':'PRECHECK','failure':None,'automatic_retry':False,'main_certificates_replaced':False,'certifies':False};created_path=None;source_paths=[];upload_paths=[];current=None;legacy_expected=None;published=False;publish_path=None;creation=None;rid=None;checkpoint_number=0;last_reservation=None;last_transport=None;fresh_source_receipts=None
    def emit(name,value):
        data=raw_json(value);require(token.encode()not in data,'CREDENTIAL_IN_EXECUTION_EVIDENCE');immutable(output/name,data);return output/name
    def checkpoint(label):
        nonlocal checkpoint_number
        checkpoint_number+=1;emit('checkpoints/'+f'{checkpoint_number:03d}_'+label+'.json',publisher_recovery.checkpoint(result,plan_binding=binding(output/'PLAN.json'),inventory_binding=binding(output/'APPROVED_SIX_FILES.json'),reservation=last_reservation,transport_receipt=last_transport))
    def saved(method):return t.out/f'{t.sequence:03d}_{method}.json'
    def ev(path):return {'receipt_path':str(path),'receipt_sha256':sha(path),'transport_contract_sha256':sm.transport_contract_sha256()}
    def preview_context():return {'own_record_id':rid,'approved_inventory_evidence':binding(output/'APPROVED_SIX_FILES.json'),'lineage_evidence':ev(created_path),'source_readback_evidence':[ev(p)for p in source_paths],'delete_evidence':[],'upload_evidence':[ev(p)for p in upload_paths],'publish_evidence':ev(publish_path)if publish_path else None}
    def read_source():
        nonlocal fresh_source_receipts
        url='https://zenodo.org/api/records/'+prepared['source_id'];legacy=t.request('GET',url);native=t.request('GET',url,accept=NATIVE);fresh_source_receipts=(t.out/f'{t.sequence-1:03d}_GET.json',saved('GET'));predicted=metadata.native_metadata(manifest['public_metadata'],prepared['before_metadata'],legacy,native,prepared['relation_template'])
        require(metadata.exact(predicted,prepared['native_metadata']),'FRESH_SOURCE_VOCABULARY_CHANGED')
        require(legacy['metadata'].get('title')==prepared['source_legacy']['metadata'].get('title')==prepared['before_metadata'].get('title'),'FRESH_SOURCE_TITLE_CHANGED')
        require(metadata.exact(native.get('custom_fields',{}).get('legacy:communities'),prepared['source_native'].get('custom_fields',{}).get('legacy:communities'))and metadata.exact(native.get('parent',{}).get('access',{}).get('owned_by'),prepared['source_native'].get('parent',{}).get('access',{}).get('owned_by')),'FRESH_SOURCE_COMMUNITY_OR_OWNER_CHANGED')
        return legacy,native
    def own_pair():
        legacy=t.request('GET','https://zenodo.org/api/deposit/depositions/'+rid);native=t.request('GET','https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE);source_paths.extend([t.out/f'{t.sequence-1:03d}_GET.json',saved('GET')]);return legacy,native
    def draft_guard(legacy,native,expected,wanted,*,label):
        state.require_private_source(legacy,wanted,native,sm,preserve)
        audit=sm.validate_new_version(native,expected,host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=expected,own_operation_record_id=rid,derived_preview_context=preview_context(),existing_communities=manifest['public_metadata'].get('communities'),public_communities=manifest['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
        # Main uploaded bytes are checked independently of previews/metadata.
        selected={x['name']:x for x in uploads};native_names=set(native['files']['entries']);require(native_names=={x['filename']for x in wanted['files']},'DRAFT_MAIN_FILE_SET')
        for name in sorted(native_names):downloads.get(name,rid,selected[name],published=False)
        emit(label+'.json',{'status':'STRICT_DRAFT_READBACK_PASS','native_audit':audit,'files_downloaded_exact':sorted(native_names)})
        return deepcopy(native),deepcopy(legacy)
    def fresh():
        runtime.fresh(package,plan);read_source()
        if current is not None:
            legacy,native=own_pair();draft_guard(legacy,native,current,legacy_expected,label=f'PREWRITE_{t.sequence:03d}')
    def mutation(writer,method,url,body,purpose,content_type='application/json'):
        nonlocal result,last_reservation,last_transport
        require(result['writes']<9 and not published,'NO_DUPLICATE_OR_POSTPUBLISH_MUTATION');fresh();at=clock();events,budget=writer.events_and_budget(method,at,d.require_write_budget);d.prewrite(package,root,method,at,events,complete_journal=True,budget_consumer=policy.require_write_budget)
        operation_id='phase7-digest:'+manifest['release_week']+':'+hashlib.sha256(read_regular(package/'DIGEST_MANIFEST.json')).hexdigest()[:16]+':'+hashlib.sha256(body).hexdigest()+':'+str(result['writes']+1)
        reservation=writer.reserve(method,url,body,t.out/f'{t.sequence+1:03d}_{method}.json',at,operation_id,d.require_write_budget)
        emit(f'WRITE_{result["writes"]+1:02d}_PRECHECK.json',{'status':'RESERVED_PREWRITE_PASS','purpose':purpose,'reservation':reservation,'package_binding':binding(package/'PUBLICATION_BINDING.json'),'body_sha256':hashlib.sha256(body).hexdigest()})
        result['writes']+=1 # Every attempted mutation costs its slot, including uncertainty.
        last_reservation=reservation['reservation'];last_transport=None;checkpoint('RESERVED_BEFORE_NETWORK')
        try:
            response=t.request(method,url,body,hashlib.sha256(body).hexdigest(),content_type,authorized=True)
        finally:
            path=t.out/f'{t.sequence:03d}_{method}.json'
            if path.exists():last_transport=binding(path)
            checkpoint('ATTEMPT_FINISHED_OR_UNCERTAIN')
        return response
    try:
        runtime.fresh(package,plan);checkpoint('PRECHECK')
        with JournalWriter(root,output/'reservations',mut.require_events,policy.require_write_budget)as writer:
            account=account_factory(token,output/'account-discovery',opener,pace=lambda:None);account.complete(manifest['release_week'],d.discover_weekly_record)
            _,budget=writer.events_and_budget('POST',clock(),d.require_write_budget);require(budget['remaining_including_next']>=9,'NINE_DAILY_SLOTS_REQUIRED_BEFORE_CREATION')
            result['phase']='CREATE';creation=mutation(writer,'POST','https://zenodo.org/api/deposit/depositions',read_regular(output/'API_METADATA_PAYLOAD.json'),'Create exactly one approved weekly Methods Digest');created_path=saved('POST');rid=state.identifier(creation['id']);result['record_id']=rid;emit('OWN_CREATION_RECEIPT.json',{'standard':'SOURCE_BOUND_TRANSPORT_REFERENCE_1','status':'REFERENCE_ONLY_NOT_ANOTHER_MUTATION','receipt':binding(created_path)})
            legacy,native=own_pair();expected,wanted=state.initial_expected(creation,native,prepared['native_metadata'],prepared['source_native'],prepared['api_payload'],sm,preserve,source_legacy=prepared['source_legacy']);current,legacy_expected=draft_guard(legacy,native,expected,wanted,label='CREATE_STRICT_READBACK')
            bucket=creation.get('links',{}).get('bucket');require(isinstance(bucket,str)and re.fullmatch('https://zenodo[.]org/api/files/[0-9a-f-]{36}',bucket)is not None,'OWN_CREATION_BUCKET')
            result['phase']='METADATA';mutation(writer,'PUT','https://zenodo.org/api/deposit/depositions/'+rid,read_regular(output/'API_METADATA_PAYLOAD.json'),'Exact approved legacy API encoding; public/native semantics unchanged');legacy,native=own_pair();current,legacy_expected=draft_guard(legacy,native,current,legacy_expected,label='METADATA_STRICT_READBACK')
            for number,row in enumerate(uploads,1):
                result['phase']='UPLOAD_'+row['name'];data=read_regular(row['path']);require(hashlib.sha256(data).hexdigest()==row['sha256']and len(data)==row['size'],'FROZEN_UPLOAD_BYTES');response=mutation(writer,'PUT',bucket+'/'+urllib.parse.quote(row['name'],safe=''),data,'Exact digest upload '+row['name'],'application/octet-stream');upload_paths.append(saved('PUT'));legacy,native=own_pair();matches=[f for f in legacy.get('files',[])if f.get('filename')==row['name']];require(len(matches)==1,'OWN_UPLOADED_ENTRY');expected=deepcopy(current);expected['files']['entries'][row['name']]=state.file_from_upload(matches[0],response,row,rid);state.refresh_totals(expected);wanted=deepcopy(legacy_expected);wanted['files'].append(matches[0]);current,legacy_expected=draft_guard(legacy,native,expected,wanted,label=f'UPLOAD_{number:02d}_STRICT_READBACK')
            require(set(current['files']['entries'])=={x['name']for x in uploads}and result['writes']==8,'EXACT_SIX_FILES_BEFORE_PUBLICATION');emit('BEFORE_PUBLISH_NATIVE.json',current);emit('BEFORE_PUBLISH_LEGACY.json',legacy_expected)
            result['phase']='PUBLISH';response=mutation(writer,'POST','https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish',b'{}','Publish one exact bound digest after all eight source checks');publish_path=saved('POST');published=True;publish_receipt=json.loads(read_regular(publish_path));emit('OWN_PUBLISH_RECEIPT.json',{'standard':'SOURCE_BOUND_TRANSPORT_REFERENCE_1','status':'REFERENCE_ONLY_NOT_ANOTHER_MUTATION','receipt':binding(publish_path)});expected_native,doi,concept=state.public_projection(current,response,rid);result['doi']=doi;emit('EXPECTED_NATIVE_PUBLIC.json',expected_native)
            # This is the FIRST authenticated native public GET after own POST.
            url='https://zenodo.org/api/records/'+rid;public_native=t.request('GET',url,accept=NATIVE);native_get=saved('GET');source_paths.append(native_get);emit('AFTER_PUBLIC_NATIVE.json',public_native)
            public_legacy=t.request('GET',url);legacy_get=saved('GET');emit('AFTER_PUBLIC_LEGACY.json',public_legacy)
            server_context={'operation':'NEW_VERSION','host':'zenodo.org','record_id':rid,'phase':'PUBLISHED','same_operation_response':response,'existing_concept_doi':concept,'previous_latest_index':0,'chain_parent_id':current['parent']['id'],'temporal_baseline':current,'own_publish_response':publish_receipt,'same_operation_reservation_id':rid,'revision_evidence':{'receipt_directory':str(t.out),'publish_receipt_name':publish_path.name,'first_native_get_receipt_name':native_get.name,'transport_contract_sha256':sm.transport_contract_sha256()},'own_operation_record_id':rid,'existing_communities':manifest['public_metadata'].get('communities'),'public_communities':public_legacy.get('metadata',{}).get('communities'),'mirror_proof':prepared['mirror'],'derived_preview_context':preview_context()};emit('SERVER_CONTEXT.json',server_context)
            # Only the decided missing-thumbnail transition may wait. Every
            # unmodified readback must eventually pass the original full rules.
            deadline=monotonic()+600;opener.deadline=time.monotonic()+600;polls=[]
            while True:
                kwargs=dict(server_context);kwargs.pop('operation')
                try:audit=sm.validate_new_version(public_native,expected_native,**kwargs);break
                except Exception as exc:
                    if not publisher_previews.preview_pending_only(sm,public_native,expected_native,server_context,exc):raise
                    remaining=deadline-monotonic();require(remaining>0,'PREVIEW_TEN_MINUTE_DEADLINE')
                    polls.append({'native_get':binding(native_get),'status':'KNOWN_PREVIEW_PENDING_NO_ACCEPTANCE','report':getattr(exc,'report',None)})
                    emit('preview-polls/'+f'{len(polls):03d}.json',polls[-1])
                    sleep(min(5,remaining));require(monotonic()<deadline,'PREVIEW_TEN_MINUTE_DEADLINE')
                    public_native=t.request('GET',url,accept=NATIVE);native_get=saved('GET');source_paths.append(native_get)
                    public_legacy=t.request('GET',url);legacy_get=saved('GET')
                    server_context['public_communities']=public_legacy.get('metadata',{}).get('communities');server_context['derived_preview_context']=preview_context()
            opener.deadline=None
            emit('PREVIEW_POLL_INDEX.json',{'status':'FULL_STRICT_PASS','polls':polls,'max_wait_seconds':600,'mutation_retries':0})
            if polls:
                emit('FINAL_AFTER_PUBLIC_NATIVE.json',public_native);emit('FINAL_AFTER_PUBLIC_LEGACY.json',public_legacy);emit('FINAL_SERVER_CONTEXT.json',server_context)
            emit('STRICT_NATIVE_READBACK.json',audit)
            expected_legacy=state.public_legacy_projection(prepared['source_legacy'],public_native,manifest['public_metadata'],doi,concept);emit('EXPECTED_PUBLIC_LEGACY.json',expected_legacy);legacy_audit=state.require_public_legacy(public_legacy,expected_legacy,public_native,sm,preserve);emit('STRICT_LEGACY_READBACK.json',legacy_audit)
            own_publish=deepcopy(publish_receipt);own_publish.update(record_id=rid,doi=doi)
            byname={r['name']:r for r in uploads}
            def download(entry,record_id):return downloads.get(entry['key'],record_id,byname[entry['key']],published=True,published_url=entry.get('links',{}).get('self'))
            def metadata_guard(actual,wanted,receipt):state.require_public_legacy(actual,wanted,public_native,sm,preserve)
            strict=d.strict_readback(package,root,public_legacy,own_publish,download,expected_record=expected_legacy,metadata_consumer=metadata_guard);emit('STRICT_DIGEST_READBACK.json',strict);emit('PUBLIC_DOWNLOADS.json',downloads.public)
            require(result['writes']==9,'EXACT_NINE_WRITES_CLOSED')
            envelope={'standard':'VRS_PHASE7_DIGEST_PUBLIC_READBACK_ENVELOPE_1','status':'STRICT_PUBLIC_READBACK_PASS','record_id':rid,'doi':doi,'release_week':manifest['release_week'],'digest_path':str(package),'digest_manifest':binding(package/'DIGEST_MANIFEST.json'),'digest_publication_binding':binding(package/'PUBLICATION_BINDING.json'),'source_before_metadata':plan['source_before_metadata'],'source_legacy':plan['source_legacy'],'source_native':plan['source_native'],'relation_vocabulary_source':plan['relation_vocabulary_source'],'community_mirror_proof':plan['community_mirror_proof'],'own_publish_receipt':binding(publish_path),'native_public_get_receipt':binding(native_get),'legacy_public_get_receipt':binding(legacy_get),'before_publish_native':binding(output/'BEFORE_PUBLISH_NATIVE.json'),'expected_native_public':binding(output/'EXPECTED_NATIVE_PUBLIC.json'),'expected_public_legacy':binding(output/'EXPECTED_PUBLIC_LEGACY.json'),'after_public_native':binding(output/('FINAL_AFTER_PUBLIC_NATIVE.json'if polls else'AFTER_PUBLIC_NATIVE.json')),'after_public_legacy':binding(output/('FINAL_AFTER_PUBLIC_LEGACY.json'if polls else'AFTER_PUBLIC_LEGACY.json')),'server_context':binding(output/('FINAL_SERVER_CONTEXT.json'if polls else'SERVER_CONTEXT.json')),'strict_native_readback':binding(output/'STRICT_NATIVE_READBACK.json'),'strict_legacy_readback':binding(output/'STRICT_LEGACY_READBACK.json'),'strict_digest_readback':binding(output/'STRICT_DIGEST_READBACK.json'),'public_downloads':downloads.public,'runtime_pins':plan['runtime_pins'],'notes':[{k:n[k]for k in('run_id','certificate','publication_binding','policy_receipt')}for n in manifest['notes']],'mutations':9,'automatic_retry':False,'certifies':False};emit('FINAL_READBACK_ENVELOPE.json',envelope)
            # This is an input adapter, never a cached acceptance summary. The
            # actual current registrar repeats the bound gate and readback.
            require(fresh_source_receipts is not None,'FRESH_ORIGINAL_SOURCE_PAIR_RECEIPTS')
            relation_path=emit('RELATION_TEMPLATE.json',prepared['relation_template'])
            evidence=runtime.registration.assemble_evidence(record_id=rid,
                public_legacy_receipt=binding(legacy_get),public_native_receipt=binding(native_get),
                own_publish_receipt=binding(publish_path),
                expected_legacy=binding(output/'EXPECTED_PUBLIC_LEGACY.json'),expected_native=binding(output/'EXPECTED_NATIVE_PUBLIC.json'),
                source_legacy_receipt=binding(fresh_source_receipts[0]),source_native_receipt=binding(fresh_source_receipts[1]),
                relation_template=binding(relation_path),
                server_context=binding(output/('FINAL_SERVER_CONTEXT.json'if polls else'SERVER_CONTEXT.json')),
                downloads=[{'filename':r['filename'],'binding':{'path':r['path'],'sha256':r['sha256']},'url':r['url']}for r in downloads.public],
                strict_readback_result=binding(output/'STRICT_DIGEST_READBACK.json'))
            evidence_path=emit('REGISTRATION_EVIDENCE.json',evidence)
            registration=runtime.registration.prepare_registration(root,package,binding(evidence_path))
            registration_path=emit('REGISTRATION_RECEIPT.json',registration)
            runtime.registration.require_registration(root,binding(registration_path))
            rows=runtime.registration.entity_rows(root,binding(registration_path),json.loads(read_regular(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json')))
            rows_path=emit('REGISTRATION_ROWS.json',{'standard':'VRS-METHODS-DIGEST-REGISTRATION-ROWS-PROPOSAL-1','status':'FRESH_CONSUMER_PASS_NOT_SSOT_WRITTEN','registration':binding(registration_path),'rows':rows,'certifies':False})
            result.update(status='PUBLISHED_STRICT_READBACK_PASS',phase='COMPLETE',final_readback_envelope=binding(output/'FINAL_READBACK_ENVELOPE.json'),registration_status='FRESH_CONSUMER_PASS_NOT_SSOT_WRITTEN',registration_receipt=binding(registration_path),registration_rows=binding(rows_path))
    except Exception as exc:
        result.update(status='HOLD_AFTER_PUBLISH'if published else'HOLD',failure=type(exc).__name__+': '+str(exc).replace(token,'[REDACTED_CREDENTIAL]'),next_action='Read-only diagnosis; do not replay any attempted mutation.')
        if hasattr(exc,'report'):emit('FAILED_SERVER_MANAGED_READBACK.json',exc.report)
    checkpoint('FINAL');emit('RESULT.json',result);return result

def execute(root,package,plan_binding,output,token,*,reviewed_driver_sha256):
    """Root-only explicit invocation; token provided in memory from its existing helper."""
    require(sha(__file__)==reviewed_driver_sha256,'REVIEWED_DRIVER_HASH');root=Path(root).resolve(strict=True);package=Path(package).resolve(strict=True);output=Path(output)
    require(str(root)=='/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0','CANONICAL_ROOT_ONLY');require(package.is_relative_to(root)and not any(p.is_symlink()for p in(package,*package.parents)),'OWN_CANONICAL_PACKAGE');_,plan=bound(root,plan_binding);runtime=Runtime(root,plan)
    globals().update(metadata=runtime.metadata,state=runtime.state,AccountDiscovery=runtime.account.AccountDiscovery,JournalWriter=runtime.journal.JournalWriter,publisher_previews=runtime.previews,publisher_recovery=runtime.recovery)
    try:return _execute(root,package,plan,output,token,runtime,account_factory=runtime.account.AccountDiscovery)
    finally:runtime.close()

if __name__=='__main__':raise SystemExit('HOLD: root must explicitly supply exact frozen plan, reviewed driver hash and existing in-memory token; no CLI credential or automatic execution.')
