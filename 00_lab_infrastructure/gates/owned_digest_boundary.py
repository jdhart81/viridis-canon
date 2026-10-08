"""Complete source/draft/public readback boundary; no weaker pass path.

The successor state adapter proposes source-derived expectations; only the
unchanged complete server/file/metadata/PID consumers admit them. This module
is ordinary integration code, never a Lean verifier or issuer.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib,json,re
import time
from pathlib import Path
import owned_digest_executor as engine
import digest_successor_state as successor
import digest_metadata as metadata
import first_digest_state as original
import digest_public_state as public_state
import publisher_previews
import server_managed_fields as sm
import publication_preservation as preservation
import methods_digest as digest
import owned_legacy_preview_aliases as legacy_aliases
from owned_prior_legacy import require_prior_legacy
from first_digest_publisher import Downloads, PacedOpener

NATIVE='application/vnd.inveniordm.v1+json'
BASE='https://zenodo.org'
class OwnedDigestBoundary:
    def __init__(self,plan,package,transport,out,opener,token):
        self.plan=plan;self.package=Path(package);self.root=Path(plan['canonical_root']);self.t=transport;self.out=Path(out);self.sequence=0;self.sources=[];self.current_state=None;self.opener=opener;self.token=token;self.discovery_count=0
        self.downloads=Downloads(token,opener,self.out/'downloads');self.creating=None
        _,self.manifest=engine.bound(self.root,plan['digest_manifest'])
        _,self.saved_legacy=engine.bound(self.root,plan['source_legacy_receipt']);_,self.saved_native=engine.bound(self.root,plan['source_native_before_create']);self.saved_legacy=self.saved_legacy['response'];self.saved_native=self.saved_native['response']
        source=deepcopy(self.saved_legacy['metadata']);templates=[x['relation_type']for x in self.saved_native['metadata'].get('related_identifiers',[])if x.get('relation_type',{}).get('id')=='issupplementto']
        engine.need(templates and all(metadata.exact(x,templates[0])for x in templates),'SOURCE_RELATION_VOCABULARY');self.relation=templates[0]
        self.payload=original.encode_api_communities(metadata.closed_payload(self.manifest['public_metadata'],source));self.native_metadata=metadata.native_metadata(self.manifest['public_metadata'],source,self.saved_legacy,self.saved_native,self.relation)
        self.inventory={x['name']:dict(x,size=x['bytes'])for x in plan['approved_inventory']}
        self.approved=self.emit('APPROVED_SIX_FILES.json',{'files':[dict(x,size=x['bytes'])for x in plan['approved_inventory']]})
        _,self.mirror=engine.bound(self.root,plan['community_mirror_proof']);self.preview_number=0
    def emit(self,name,value):
        p=self.out/name;engine.immutable(p,engine.raw_json(value));return engine.binding(p)
    def saved(self,method):return engine.binding(self.t.out/f'{self.t.sequence:03d}_{method}.json')
    def evidence(self,binding):return {'receipt_path':binding['path'],'receipt_sha256':binding['sha256'],'transport_contract_sha256':sm.transport_contract_sha256()}
    def get(self,rid,published,native=False):
        url=BASE+'/api/records/'+rid if published else(BASE+'/api/records/'+rid+'/draft'if native else BASE+'/api/deposit/depositions/'+rid)
        value=self.t.request('GET',url,accept=NATIVE if native else'application/json');b=self.saved('GET');self.sources.append(b);return value,b
    def chain(self,state,prior,own,expected,*,boundary='CREATE',operation=None,before=None):
        return {'boundary':boundary,'prior_record_id':self.plan['predecessor_record_id'],'successor_record_id':state['record_id'],'chain_parent_id':state['concept_id'],'prior_before_create':self.saved_native,'prior_actual':prior,'successor_actual':own,'successor_expected':expected,'creation_evidence':self.evidence(state['creation_receipt']),'operation_evidence':self.evidence(operation)if operation else None,'successor_before_boundary':before,'successor_absence_evidence':None}
    def preview(self,state,publish=None):
        drops=[self.evidence(a['transport'])for a in state['attempts']if a['step'].startswith('DROP:')and a['outcome']=='STRICT_PASS'];uploads=[self.evidence(a['transport'])for a in state['attempts']if a['step'].startswith('UPLOAD:')and a['outcome']=='STRICT_PASS']
        # A private stage has the exact predecessor-derived inherited files or
        # exact acknowledged approved uploads. These are never the final
        # publication inventory; PUBLISH separately requires the exact target.
        self.preview_number+=1;stage=[]
        entries=self.staged_expected['files']['entries']
        for name,x in entries.items():
            row={'key':name,'size':x['size'],'checksum':x['checksum'],'id':x['id']}
            if x['checksum']=='md5:'+self.inventory[name]['md5']:row['sha256']=self.inventory[name]['sha256']
            else:
                old=next(r for r in successor.predecessor_inventory(self.plan,root=self.root)if r['name']==name);engine.need(x['checksum']=='md5:'+old['md5']and x['size']==old['bytes'],'PRIVATE_INHERITED_SOURCE_BYTES');row['sha256']=old['sha256']
            stage.append(row)
        stage_binding=self.emit('preview-inventories/'+f'{self.preview_number:04d}.json',{'files':stage or[{**self.inventory[n],'size':self.inventory[n]['bytes']}for n in sorted(self.inventory)],'purpose':'EXACT_PRIVATE_STAGE_ONLY_NOT_PUBLICATION_ADMISSION','final_target_inventory':self.approved})
        removal=self.emit('preview-removals/'+f'{self.preview_number:04d}.json',{'drop':[{**x,'size':x['filesize']}for x in state['inherited_inventory']]})
        own_reads=[]
        for value in self.sources:
            _,receipt=engine.bound(self.root,value)
            if receipt.get('method')=='GET'and str(receipt.get('response',{}).get('id'))==state['record_id']:own_reads.append(self.evidence(value))
        return {'own_record_id':state['record_id'],'approved_inventory_evidence':stage_binding,'approved_removal_inventory_evidence':removal,'lineage_evidence':self.evidence(state['creation_receipt']),'source_readback_evidence':own_reads,'delete_evidence':drops,'upload_evidence':uploads,'publish_evidence':self.evidence(publish)if publish else None}
    def prior(self,state,own=None,expected=None,boundary='CREATE',operation=None,before=None):
        legacy,lb=self.get(self.plan['predecessor_record_id'],True);native,nb=self.get(self.plan['predecessor_record_id'],True,True)
        # All scientific metadata/files/PIDs are exact. Only the already
        # approved versions state machine sees the genuine own newversion.
        if state['record_id']is None:require_prior_legacy(legacy,self.saved_legacy,native,self.saved_native,sm=sm,preservation=preservation)
        else:
            context=self.chain(state,native,own,expected,boundary=boundary,operation=operation,before=before)
            sm.require_version_chain_state(host='zenodo.org',**context)
            require_prior_legacy(legacy,self.saved_legacy,native,self.saved_native,sm=sm,preservation=preservation,chain=context)
        # Download all six immutable predecessor bytes; their independent
        # hash inventory was admitted by the default predecessor registrar.
        prior_files=successor.predecessor_inventory(self.plan,root=self.root)
        engine.need({r['name']for r in prior_files}=={f['key']for f in legacy['files']},'PRIOR_EXACT_MAIN_SET')
        for row in prior_files:self.downloads.get(row['name'],self.plan['predecessor_record_id'],dict(row,size=row['bytes']),published=True,published_url=BASE+'/api/records/'+self.plan['predecessor_record_id']+'/files/'+row['name']+'/content')
        return legacy,native,lb,nb
    def baseline(self,state):
        _,report=engine.bound(self.root,state['last_validation']);engine.need(report.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1'and report.get('record_id')==state['record_id'],'OWN_VERIFIED_BASELINE');return report['expected_native'],report['expected_legacy']
    def full_draft(self,state,expected,wanted,legacy,native,*,chain,operation=None):
        self.staged_expected=expected
        context={'phase':'DRAFT','temporal_baseline':expected,'own_operation_record_id':state['record_id'],'version_chain_context':chain,'derived_preview_context':self.preview(state),'same_operation_response':json.loads(engine.raw(operation['path']))['response']if operation else None,'existing_communities':self.manifest['public_metadata'].get('communities'),'public_communities':self.manifest['public_metadata'].get('communities'),'mirror_proof':self.mirror}
        self.last_draft_audit=sm.validate_new_version(native,expected,host='zenodo.org',record_id=state['record_id'],**context);self.last_server_context=deepcopy(context)
        projected=legacy_aliases.project(native,wanted,self.last_draft_audit,sm,record_id=state['record_id']);original.require_private_source(legacy,projected,native,sm,preservation)
        entries=native.get('files',{}).get('entries');engine.need(isinstance(entries,dict)and set(entries)=={f['filename']for f in wanted['files']},'DRAFT_EXACT_FILE_SET')
        created={f['filename']:f for f in state['inherited_inventory']}
        for name,entry in entries.items():
            uploaded='UPLOAD:'+name in state['completed'];spec=self.inventory[name]if uploaded else successor.inherited_download_spec(name,created[name],self.plan,root=self.root)
            self.downloads.get(name,state['record_id'],dict(spec,size=spec.get('bytes',spec.get('size'))),published=False)
        return {'native':native,'legacy':legacy}
    def before(self,state):
        self.current_state=state
        if state['record_id']is None:
            # Complete account discovery is reconsumed by runtime admission;
            # only the actual latest owned weekly source may start once.
            import owned_weekly_discovery
            self.discovery_count+=1
            fresh=owned_weekly_discovery.capture(self.root,self.plan['release_week'],self.token,self.out/'fresh-account'/f'{self.discovery_count:03d}',self.opener)
            _,discovered=engine.bound(self.root,fresh)
            engine.need(discovered['start_kind']==self.plan['start_kind']and discovered['record_id']==(self.plan['predecessor_record_id']if self.plan['start_kind']=='NEW_VERSION'else None)and discovered['concept_id']==self.plan['expected_concept_id'],'FRESH_START_ACCOUNT_OWN_CHAIN')
            self.prior(state);return
        known={(v['path'],v['sha256'])for v in self.sources}
        for attempt in state['attempts']:
            _,past=engine.bound(self.root,attempt['validation'])
            for value in past['source_chain_native_gets']:
                engine.bound(self.root,value)
                if (value['path'],value['sha256'])not in known:self.sources.append(value);known.add((value['path'],value['sha256']))
        expected,wanted=self.baseline(state);legacy,lb=self.get(state['record_id'],False);native,nb=self.get(state['record_id'],False,True);prior_l,prior_n,_,_=self.prior(state,native,expected);chain=self.chain(state,prior_n,native,expected);self.full_draft(state,expected,wanted,legacy,native,chain=chain)
        self.before_expected=deepcopy(expected);self.before_legacy=deepcopy(wanted)
        self.before_actual_legacy=deepcopy(legacy);self.before_chain=chain
        _,created=engine.bound(self.root,state['creation_receipt']);_,first=engine.bound(self.root,state['first_owned_legacy_draft']);self.opener.arm(state['record_id'],self.plan['predecessor_record_id'],created,first,self.inventory['METHODS_NOTES.zip'])
    def command(self,state,step):
        rid=state['record_id'];method='POST';body=b'{}';kind='application/json';delete=None
        if step=='NEW_VERSION':url=BASE+'/api/deposit/depositions/'+self.plan['predecessor_record_id']+'/actions/newversion'
        elif step.startswith('DROP:'):
            method='DELETE';body=b'';delete=next(x for x in state['inherited_inventory']if x['filename']==step[5:]);url=BASE+'/api/deposit/depositions/'+rid+'/files/'+delete['id']
        elif step=='METADATA':method='PUT';url=BASE+'/api/deposit/depositions/'+rid;body=engine.raw_json(self.payload)
        elif step.startswith('UPLOAD:'):
            method='PUT';name=step[7:];row=self.inventory[name];body=engine.raw(Path(row['path']));engine.need(hashlib.sha256(body).hexdigest()==row['sha256'],'UPLOAD_EXACT_APPROVED_BYTES');url=self.before_legacy['links']['bucket']+'/'+name;kind='application/octet-stream'
        elif step=='RESERVE_DOI':url=BASE+'/api/records/'+rid+'/draft/pids/doi'
        elif step=='PUBLISH':
            engine.need(set(self.before_expected['files']['entries'])==set(self.inventory),'PREPUBLISH_EXACT_MAIN_SET')
            for name,x in self.before_expected['files']['entries'].items():engine.need(x['checksum']=='md5:'+self.inventory[name]['md5']and x['size']==self.inventory[name]['bytes'],'PREPUBLISH_EXACT_BYTES')
            final_native,_=self.get(rid,False,True)
            self.full_draft(state,self.before_expected,self.before_legacy,self.before_actual_legacy,final_native,chain=self.before_chain)
            url=BASE+'/api/deposit/depositions/'+rid+'/actions/publish'
        else:raise engine.ExecutionHold('HOLD_UNLISTED_STEP')
        return {'method':method,'url':url,'body':body,'content_type':kind,'delete_file':delete}
    def after(self,state,step,response,operation):
        own=json.loads(engine.raw(Path(operation['path'])));engine.need(own.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','GENUINE_SUCCESSFUL_ROUNDTRIP')
        if step=='NEW_VERSION':
            endpoint=BASE+'/api/deposit/depositions/'+self.plan['predecessor_record_id']+'/actions/newversion'
            engine.need(own.get('http_status')==201 and own.get('url')==endpoint,'OWN_GENUINE_START_ROUNDTRIP')
            rid=str(response.get('id'));parent=str(response.get('conceptrecid'));engine.need(re.fullmatch('[1-9][0-9]*',rid)is not None and re.fullmatch('[1-9][0-9]*',parent)is not None,'OWN_CHILD_IDENTITY')
            engine.need(parent==self.plan['expected_concept_id'],'OWN_EXISTING_CONCEPT')
            legacy,lb=self.get(rid,False);native,nb=self.get(rid,False,True)
            expected,wanted=successor.initial_newversion_projection(self.saved_legacy,self.saved_native,own,legacy,native)
            temp=deepcopy(state);temp.update(record_id=rid,concept_id=parent,creation_receipt=operation,first_owned_draft=nb,first_owned_legacy_draft=lb,inherited_inventory=deepcopy(response['files']))
            prior_l,prior_n,_,_=self.prior(temp,native,expected);chain=self.chain(temp,prior_n,native,expected)
            if chain is not None:sm.require_version_chain_state(host='zenodo.org',**chain)
            self.full_draft(temp,expected,wanted,legacy,native,chain=chain,operation=operation)
            ownership={'record_id':rid,'concept_id':parent,'first_owned_draft':nb,'first_owned_legacy_draft':lb,'inherited_inventory':deepcopy(response['files'])}
        elif step=='PUBLISH':return self.published(state,response,operation)
        else:
            ownership=None;expected=deepcopy(self.before_expected);wanted=deepcopy(self.before_legacy)
            if step.startswith('DROP:'):
                name=step[5:];engine.need(response=={'empty_204':True,'draft_file_removed':True},'EMPTY_204_DROP_ACK');expected['files']['entries'].pop(name);wanted['files']=[x for x in wanted['files']if x['filename']!=name];original.refresh_totals(expected)
            elif step=='METADATA':expected['metadata']=deepcopy(self.native_metadata);wanted['metadata']=successor.private_metadata_projection(self.payload,response,self.native_metadata)
            elif step=='RESERVE_DOI':engine.need(response.get('id')==state['record_id']and response.get('parent',{}).get('id')==state['concept_id']and response.get('pids',{}).get('doi')=={'identifier':'10.5281/zenodo.'+state['record_id'],'provider':'datacite','client':'datacite'},'OWN_DOI_RESERVATION')
            legacy,lb=self.get(state['record_id'],False);native,nb=self.get(state['record_id'],False,True)
            if step.startswith('UPLOAD:'):
                name=step[7:];row=next(x for x in legacy['files']if x['filename']==name);entry=original.file_from_upload(row,response,dict(self.inventory[name],size=self.inventory[name]['bytes']),state['record_id']);expected['files']['entries'][name]=entry;wanted['files'].append(row);original.refresh_totals(expected)
            temp=deepcopy(state)
            # Include the actual in-flight upload/drop in byte/preview checks;
            # this is provenance only, not a terminal machine completion.
            temp['completed']=temp['completed']+[step];temp['attempts'][-1]=dict(temp['attempts'][-1],transport=operation,outcome='STRICT_PASS')
            prior_l,prior_n,_,_=self.prior(temp,native,expected);chain=self.chain(temp,prior_n,native,expected);self.full_draft(temp,expected,wanted,legacy,native,chain=chain,operation=operation)
        report={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'STRICT_DRAFT_SOURCE_NATIVE_LEGACY_FILES_PIDS_PASS','record_id':rid if step=='NEW_VERSION'else state['record_id'],'step':step,'transport':operation,'owned_native_get':nb,'owned_legacy_get':lb,'expected_native':deepcopy(native),'expected_legacy':deepcopy(legacy),'server_context':deepcopy(self.last_server_context),'native_audit':deepcopy(self.last_draft_audit),'source_chain_native_gets':deepcopy(self.sources),'scientific_acceptance':'UNCHANGED_EXISTING_GATE_ONLY','certifies':False}
        # Audit-admitted complete native server representations become the
        # next temporal baseline. Main data has already matched independent
        # source/payload/upload expectations, never the after body itself.
        self.sequence+=1;return self.emit('validated/'+f'{self.sequence:03d}.json',report),ownership
    def published(self,state,response,operation):
        rid=state['record_id'];engine.need(str(response.get('id'))==rid and response.get('submitted')is True and response.get('state')=='done'and response.get('doi')=='10.5281/zenodo.'+rid and str(response.get('conceptrecid'))==state['concept_id'],'OWN_TERMINAL_PUBLISH')
        # A final own GET must be the immediately preceding receipt in this
        # same transport directory, never an invented/stale before body.
        post=Path(operation['path']);before_path=post.parent/f'{int(post.name[:3])-1:03d}_GET.json'
        before_obj=json.loads(engine.raw(before_path));engine.need(before_obj.get('url')==BASE+'/api/records/'+rid+'/draft'and before_obj.get('accept')==NATIVE and before_obj.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','FINAL_REAL_PREPUBLISH_GET')
        before_binding=engine.binding(before_path)
        first_native=state['first_owned_draft']
        first_legacy=state['first_owned_legacy_draft']
        reserve=next(a['transport']for a in state['attempts']if a['step']=='RESERVE_DOI'and a['outcome']=='STRICT_PASS')
        context=successor.assemble_context(record_id=rid,source_legacy_receipt=self.plan['source_legacy_receipt'],source_native_receipt=self.plan['source_native_receipt'],source_native_before_create=self.plan['source_native_before_create'],first_own_native_draft=first_native,first_own_legacy_draft=first_legacy,predecessor_registration=self.plan['predecessor_registration'],successor_digest_manifest=self.plan['digest_manifest'],before_publish_native_receipt=before_binding,creation_receipt=state['creation_receipt'],reservation_receipt=reserve,publish_receipt=operation,mirror_proof=self.plan['community_mirror_proof'])
        context_binding=self.emit('PUBLIC_STATE_CONTEXT.json',context)
        load=lambda b:engine.bound(self.root,b)[1]
        prediction=successor.consume_context(context,load=load,public=self.manifest['public_metadata'],evidence_sources={'source_legacy_receipt':self.plan['source_legacy_receipt'],'source_native_receipt':self.plan['source_native_receipt'],'own_publish_receipt':operation},root=self.root)
        expected=prediction['native'];self.staged_expected=expected
        native,nb=self.get(rid,True,True);first_public_native=nb;legacy,lb=self.get(rid,True)
        prior_l,prior_n,_,_=self.prior(state,native,expected,'PUBLISH',operation,before_obj['response']);chain=self.chain(state,prior_n,native,expected,boundary='PUBLISH',operation=operation,before=before_obj['response'])
        own=json.loads(engine.raw(Path(operation['path'])))
        server={'operation':'NEW_VERSION','phase':'PUBLISHED','same_operation_response':response,'existing_concept_doi':'10.5281/zenodo.'+state['concept_id'],'previous_latest_index':self.saved_native['versions']['index'],'chain_parent_id':state['concept_id'],'temporal_baseline':before_obj['response'],'own_publish_response':own,'same_operation_reservation_id':rid,'revision_evidence':{'receipt_directory':str(post.parent),'publish_receipt_name':post.name,'first_native_get_receipt_name':Path(first_public_native['path']).name,'transport_contract_sha256':sm.transport_contract_sha256()},'own_operation_record_id':rid,'existing_communities':self.manifest['public_metadata'].get('communities'),'public_communities':legacy['metadata'].get('communities'),'mirror_proof':self.mirror,'version_chain_context':chain,'derived_preview_context':self.preview(state,operation)}
        deadline=time.monotonic()+600;polls=[];self.opener.deadline=deadline
        try:
            while True:
                try:
                    audit=sm.audit_readback(native,expected,host='zenodo.org',record_id=rid,**server);public_state.require_native_audit(audit,record_id=rid,sm=sm);break
                except Exception as exc:
                    if not publisher_previews.preview_pending_only(sm,native,expected,server,exc):raise
                    remaining=deadline-time.monotonic();engine.need(remaining>0,'PREVIEW_TEN_MINUTE_DEADLINE');polls.append(nb);time.sleep(min(5,remaining));engine.need(time.monotonic()<deadline,'PREVIEW_TEN_MINUTE_DEADLINE');native,nb=self.get(rid,True,True);legacy,lb=self.get(rid,True);server['public_communities']=legacy['metadata'].get('communities');server['derived_preview_context']=self.preview(state,operation)
        finally:self.opener.deadline=None
        legacy_expected=public_state.predict_legacy(self.saved_legacy,native,self.manifest['public_metadata']);legacy_expected['metadata']['relations']=prediction['legacy_relation']
        public_state.require_legacy(legacy,legacy_expected,native,source_legacy=self.saved_legacy,source_native=self.saved_native,sm=sm,preservation=preservation,native_expected=expected,server_context=server)
        own=dict(own,record_id=rid,doi='10.5281/zenodo.'+rid)
        def download(entry,record_id):return self.downloads.get(entry['key'],record_id,self.inventory[entry['key']],published=True,published_url=entry['links']['self'])
        strict=digest.strict_readback(self.package,self.root,legacy,own,download,expected_record=legacy_expected,metadata_consumer=lambda a,e,o:preservation.require_public_metadata(a['metadata'],e['metadata']))
        nbinding=self.emit('EXPECTED_PUBLIC_NATIVE.json',expected);lbinding=self.emit('EXPECTED_PUBLIC_LEGACY.json',legacy_expected);sbinding=self.emit('SERVER_CONTEXT.json',server);strictbinding=self.emit('STRICT_DIGEST_READBACK.json',strict);relation=self.emit('RELATION_TEMPLATE.json',self.relation)
        import methods_digest_registration as registrar
        downloads=[{'filename':x['filename'],'binding':{'path':x['path'],'sha256':x['sha256']},'url':x['url']}for x in self.downloads.public if x['url'].startswith(BASE+'/api/records/'+rid+'/')]
        evidence=registrar.assemble_evidence(record_id=rid,public_legacy_receipt=lb,public_native_receipt=nb,own_publish_receipt=operation,expected_legacy=lbinding,expected_native=nbinding,source_legacy_receipt=self.plan['source_legacy_receipt'],source_native_receipt=self.plan['source_native_receipt'],relation_template=relation,server_context=sbinding,downloads=downloads,strict_readback_result=strictbinding,public_state_context=context_binding)
        ebinding=self.emit('METHODS_DIGEST_PUBLIC_EVIDENCE.json',evidence)
        registration=registrar.prepare_registration(self.root,self.package,ebinding) # unchanged default consumers
        rbinding=self.emit('METHODS_DIGEST_REGISTRATION_RECEIPT.json',registration);registrar.require_registration(self.root,rbinding)
        report={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'PUBLISHED_NATIVE_LEGACY_SIX_FILES_PID_DEFAULT_REGISTRAR_PASS','record_id':rid,'step':'PUBLISH','transport':operation,'owned_native_get':nb,'owned_legacy_get':lb,'expected_native':expected,'expected_legacy':legacy_expected,'native_audit':audit,'strict_digest_readback':strictbinding,'registration_receipt':rbinding,'public_evidence':ebinding,'preview_polls':polls,'certifies':False}
        return self.emit('validated/PUBLISHED.json',report),None
