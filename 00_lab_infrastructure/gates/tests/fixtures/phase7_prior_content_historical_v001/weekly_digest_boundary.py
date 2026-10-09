"""Source/draft/public readback under the approved own-record control policy.

Own server housekeeping is logged; controlled payloads, file bytes, DOI/concept
identity and every prior record are independently checked. This module
is ordinary integration code, never a Lean verifier or issuer.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib,json,re
import time
from pathlib import Path
import weekly_digest_executor as engine
import digest_weekly_state as successor
import digest_metadata as metadata
import first_digest_state as original
import digest_public_state as public_state
import publisher_previews
import server_managed_fields as sm
import publication_preservation as preservation
import methods_digest as digest
import owned_legacy_preview_aliases as legacy_aliases
import own_record_comparison as own_rule
import own_prior_record
from owned_prior_legacy import require_prior_legacy
from first_digest_publisher import Downloads, PacedOpener

NATIVE='application/vnd.inveniordm.v1+json'
BASE='https://zenodo.org'
def inherited_rows(created):
    fields={'id','filename','filesize','checksum','links'}
    rows=created.get('files');engine.need(isinstance(rows,list),'OWN_INHERITED_ROWS')
    return [{k:deepcopy(row[k])for k in fields}for row in rows]

def initial_owned_projection(source_legacy,source_native,creation_receipt,first_legacy_receipt,first_native_receipt):
    projection=own_rule.initial_projection(source_legacy,source_native,creation_receipt,first_legacy_receipt,first_native_receipt)
    controlled=projection['controlled'];expected=deepcopy(projection['native'])
    created={r['filename']:r for r in inherited_rows(creation_receipt['response'])}
    engine.need(set(created)=={r['name']for r in controlled['files']},'OWN_CREATION_INHERITED_MAIN_SET')
    for row in controlled['files']:
        ack=created[row['name']];engine.need(type(ack['filesize'])is int and ack['filesize']==row['bytes']and ack['checksum']==row['md5'],'OWN_CREATION_INHERITED_MAIN_BYTES')
        expected['files']['entries'][row['name']].update(key=row['name'],size=row['bytes'],checksum='md5:'+row['md5'])
    original.refresh_totals(expected)
    return expected,deepcopy(projection['legacy'])

class WeeklyDigestBoundary:
    def __init__(self,plan,package,transport,out,opener,token):
        self.plan=plan;self.package=Path(package);self.root=Path(plan['canonical_root']);self.t=transport;self.out=Path(out);self.sequence=0;self.sources=[];self.current_state=None;self.opener=opener;self.token=token;self.discovery_count=0;self.pending_evidence=None
        self.downloads=Downloads(token,opener,self.out/'downloads');self.creating=None
        _,self.manifest=engine.bound(self.root,plan['digest_manifest'])
        _,self.saved_legacy=engine.bound(self.root,plan['source_legacy_receipt']);_,self.saved_native=engine.bound(self.root,plan['source_native_before_create']);self.saved_legacy=self.saved_legacy['response'];self.saved_native=self.saved_native['response']
        source=deepcopy(self.saved_legacy['metadata']);self.relation=successor.registered_relation_template(plan['predecessor_registration'],root=self.root,source_native=self.saved_native,source_legacy=self.saved_legacy)
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
        if self.plan['start_kind']=='CREATE_WEEK':return None
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
    def source_inventory_plan(self):
        # FIRST_WEEK uses the earlier digest solely as a metadata/bytes source.
        # Reconsume its real default registration; the own new-week scope stays
        # unchanged and is never passed off as a same-week predecessor.
        if self.plan['start_kind']=='NEW_VERSION':return self.plan
        import methods_digest_registration as registrar
        admitted=registrar.require_registration(self.root,self.plan['predecessor_registration'])
        engine.need(admitted['receipt']['record_id']==self.plan['predecessor_record_id']and admitted['receipt']['release_week']!=self.plan['release_week'],'ACTUAL_OTHER_WEEK_METADATA_SOURCE_INVENTORY')
        return dict(self.plan,release_week=admitted['receipt']['release_week'])
    def prior(self,state,own=None,expected=None,boundary='CREATE',operation=None,before=None):
        legacy,lb=self.get(self.plan['predecessor_record_id'],True);native,nb=self.get(self.plan['predecessor_record_id'],True,True)
        # Every prior field is exact; only the existing receipt-bound chain
        # flags may transition. No own revision/ui/link is a prior baseline.
        created=engine.bound(self.root,state['creation_receipt'])[1]if state['record_id']is not None and self.plan['start_kind']=='NEW_VERSION'else None
        published=engine.bound(self.root,operation)[1]if boundary=='PUBLISH'and operation is not None else None
        own_prior_record.require_pair(legacy,native,self.saved_legacy,self.saved_native,creation=created,publish=published,preservation=preservation)
        # Download all six immutable predecessor bytes; their independent
        # hash inventory was admitted by the default predecessor registrar.
        prior_files=successor.predecessor_inventory(self.source_inventory_plan(),root=self.root)
        engine.need({r['name']for r in prior_files}=={f['key']for f in legacy['files']},'PRIOR_EXACT_MAIN_SET')
        for row in prior_files:self.downloads.get(row['name'],self.plan['predecessor_record_id'],dict(row,size=row['bytes']),published=True,published_url=BASE+'/api/records/'+self.plan['predecessor_record_id']+'/files/'+row['name']+'/content')
        return legacy,native,lb,nb
    def baseline(self,state):
        _,report=engine.bound(self.root,state['last_validation']);engine.need(report.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1'and report.get('record_id')==state['record_id'],'OWN_VERIFIED_BASELINE');return report['expected_native'],report['expected_legacy']
    def ownership(self,state):
        _,created=engine.bound(self.root,state['creation_receipt']);_,first_n=engine.bound(self.root,state['first_owned_draft']);_,first_l=engine.bound(self.root,state['first_owned_legacy_draft'])
        ownership={'creation_receipt':created,'first_native_receipt':first_n,'first_legacy_receipt':first_l,'prior_ids':[self.plan['predecessor_record_id'],self.plan['source_concept_id']]}
        own_rule.require_ownership(created,first_n,first_l,prior_ids=ownership['prior_ids'])
        return ownership
    def controlled(self,state,expected,wanted,*,phase='DRAFT'):
        sent=self.plan['start_kind']=='CREATE_WEEK'or'METADATA'in state['completed']
        if sent:
            native_md=own_rule.native_sent_metadata(self.native_metadata)
            legacy_md=own_rule.legacy_sent_metadata(self.manifest['public_metadata'])if phase=='PUBLISHED'else deepcopy(self.payload['metadata'])
        else:
            owned=self.ownership(state)
            initial=own_rule.initial_projection(self.saved_legacy,self.saved_native,owned['creation_receipt'],owned['first_legacy_receipt'],owned['first_native_receipt'])
            native_md=initial['controlled']['native_metadata'];legacy_md=initial['controlled']['legacy_metadata']
        return {'record_id':state['record_id'],'concept_id':state['concept_id'],'phase':phase,'native_metadata':native_md,'legacy_metadata':legacy_md,'files':[{'name':name,'bytes':entry['size'],'md5':entry['checksum'][4:]}for name,entry in sorted(expected['files']['entries'].items())],'communities':deepcopy(self.payload['metadata'].get('communities',[])),'native_community_ids':deepcopy(self.saved_native.get('parent',{}).get('communities',{}).get('ids',[])),'doi_required':'RESERVE_DOI'in state['completed']or phase=='PUBLISHED'}
    def initial_projection(self,created,first_legacy_receipt,first_native_receipt):
        return initial_owned_projection(self.saved_legacy,self.saved_native,created,first_legacy_receipt,first_native_receipt)
    def full_draft(self,state,expected,wanted,legacy,native,*,chain,operation=None):
        self.staged_expected=expected
        controlled=self.controlled(state,expected,wanted)
        checked=own_rule.require_own_readback(native,legacy,controlled=controlled,ownership=self.ownership(state))
        self.last_draft_audit=checked;self.last_server_context={'operation':'NEW_VERSION','phase':'DRAFT','own_record_controlled':deepcopy(controlled)}
        entries=native.get('files',{}).get('entries');engine.need(isinstance(entries,dict)and set(entries)=={f['filename']for f in wanted['files']},'DRAFT_EXACT_FILE_SET')
        created={f['filename']:f for f in state['inherited_inventory']}
        for name,entry in entries.items():
            uploaded='UPLOAD:'+name in state['completed'];spec=self.inventory[name]if uploaded else successor.inherited_download_spec(name,created[name],self.plan,root=self.root)
            self.downloads.get(name,state['record_id'],dict(spec,size=spec.get('bytes',spec.get('size'))),published=False)
        return {'native':native,'legacy':legacy}
    def readmit_creation(self,*,old_plan_binding,old_hold_binding,original_creation,first_legacy,first_native):
        # GET/download-only explicit recovery. Old HOLD remains immutable.
        from owned_creation_recovery import STANDARD as recovery_standard
        _,old_hold=engine.bound(self.root,old_hold_binding);attempt=old_hold['attempts'][0];_,created=engine.bound(self.root,original_creation);rid=str(created['response']['id']);parent=str(created['response']['conceptrecid'])
        legacy,lb=self.get(rid,False);native,nb=self.get(rid,False,True);expected,wanted=self.initial_projection(created,engine.bound(self.root,first_legacy)[1],engine.bound(self.root,first_native)[1])
        import owned_digest_machine as machine
        temp=machine.initial(machine.digest(self.plan),self.plan['approved_inventory'],start_kind='NEW_VERSION')
        temp.update(record_id=rid,concept_id=parent,creation_receipt=original_creation,first_owned_draft=first_native,first_owned_legacy_draft=first_legacy,inherited_inventory=inherited_rows(created['response']))
        self.prior(temp,native,expected);self.full_draft(temp,expected,wanted,legacy,native,chain=None,operation=original_creation)
        report={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'CURRENT_OWN_RECORD_CREATION_READMISSION_NO_WRITE','record_id':rid,'step':'NEW_VERSION','transport':original_creation,'owned_native_get':nb,'owned_legacy_get':lb,'expected_native':deepcopy(native),'expected_legacy':deepcopy(legacy),'server_context':deepcopy(self.last_server_context),'native_audit':deepcopy(self.last_draft_audit),'source_chain_native_gets':deepcopy(self.sources),'explicit_creation_recovery':{'standard':recovery_standard,'status':'CURRENT_OWN_RECORD_RULE_READMISSION_ONLY','old_plan':old_plan_binding,'old_hold':old_hold_binding,'authority':self.plan['authority'],'original_reservation':attempt['reservation'],'original_operation_id':attempt['operation_id'],'no_network_write':True},'scientific_acceptance':'UNCHANGED_EXISTING_GATE_ONLY','certifies':False}
        return self.emit('validated/EXPLICIT_CREATION_READMISSION.json',report)
    def before(self,state):
        self.current_state=state;self.pending_evidence=None
        if state['record_id']is not None and self.plan['start_kind']=='CREATE_WEEK':
            import weekly_pending_discovery
            self.discovery_count+=1
            pending=weekly_pending_discovery.capture(self.root,self.plan,state,self.token,self.out/'fresh-account'/f'{self.discovery_count:03d}',self.opener)
            self.pending_evidence=pending
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
        elif step=='CREATE_WEEK':url=BASE+'/api/deposit/depositions';body=engine.raw_json(self.payload)
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
        if step in{'NEW_VERSION','CREATE_WEEK'}:
            engine.need(step==self.plan['start_kind'],'EXACT_APPROVED_OWN_START_KIND')
            endpoint=BASE+'/api/deposit/depositions/'+self.plan['predecessor_record_id']+'/actions/newversion'if step=='NEW_VERSION'else BASE+'/api/deposit/depositions'
            engine.need(own.get('http_status')==201 and own.get('url')==endpoint,'OWN_GENUINE_START_ROUNDTRIP')
            rid=str(response.get('id'));parent=str(response.get('conceptrecid'));engine.need(re.fullmatch('[1-9][0-9]*',rid)is not None and re.fullmatch('[1-9][0-9]*',parent)is not None,'OWN_CHILD_IDENTITY')
            if step=='NEW_VERSION':engine.need(parent==self.plan['expected_concept_id'],'OWN_EXISTING_CONCEPT')
            else:engine.need(parent!=self.plan['source_concept_id']and rid not in{parent,self.plan['predecessor_record_id']},'GENUINE_NEW_WEEK_CONCEPT_ONLY')
            legacy,lb=self.get(rid,False);native,nb=self.get(rid,False,True)
            if step=='NEW_VERSION':expected,wanted=self.initial_projection(own,engine.bound(self.root,lb)[1],engine.bound(self.root,nb)[1])
            else:expected,wanted=deepcopy(native),deepcopy(legacy);expected['files']['entries']={};wanted['files']=[];original.refresh_totals(expected)
            temp=deepcopy(state);temp.update(record_id=rid,concept_id=parent,creation_receipt=operation,first_owned_draft=nb,first_owned_legacy_draft=lb,inherited_inventory=inherited_rows(response))
            prior_l,prior_n,_,_=self.prior(temp,native,expected);chain=self.chain(temp,prior_n,native,expected)
            # Own versions are logged by the own-record policy; prior() guards the source.
            self.full_draft(temp,expected,wanted,legacy,native,chain=chain,operation=operation)
            ownership={'record_id':rid,'concept_id':parent,'first_owned_draft':nb,'first_owned_legacy_draft':lb,'inherited_inventory':inherited_rows(response)}
        elif step=='PUBLISH':return self.published(state,response,operation)
        else:
            ownership=None;expected=deepcopy(self.before_expected);wanted=deepcopy(self.before_legacy)
            if step.startswith('DROP:'):
                name=step[5:];engine.need(response=={'empty_204':True,'draft_file_removed':True},'EMPTY_204_DROP_ACK');expected['files']['entries'].pop(name);wanted['files']=[x for x in wanted['files']if x['filename']!=name];original.refresh_totals(expected)
            elif step=='METADATA':expected['metadata']=deepcopy(self.native_metadata);wanted['metadata']=deepcopy(self.payload['metadata'])
            elif step=='RESERVE_DOI':
                engine.need(response.get('id')==state['record_id']and response.get('parent',{}).get('id')==state['concept_id']and response.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+state['record_id'],'OWN_DOI_RESERVATION')
                expected['pids']=deepcopy(response['pids'])
                wanted['doi']='10.5281/zenodo.'+state['record_id']
            legacy,lb=self.get(state['record_id'],False);native,nb=self.get(state['record_id'],False,True)
            if step.startswith('UPLOAD:'):
                name=step[7:];row=next(x for x in legacy['files']if x['filename']==name);engine.need(response.get('key')==name and response.get('checksum')=='md5:'+self.inventory[name]['md5']and type(response.get('size'))is int and response.get('size')==self.inventory[name]['bytes'],'OWN_UPLOAD_ACK_BYTES');entry=deepcopy(native['files']['entries'][name]);entry.update(key=name,checksum='md5:'+self.inventory[name]['md5'],size=self.inventory[name]['bytes']);expected['files']['entries'][name]=entry;wanted['files'].append(row);original.refresh_totals(expected)
            temp=deepcopy(state)
            # Include the actual in-flight upload/drop in byte/preview checks;
            # this is provenance only, not a terminal machine completion.
            temp['completed']=temp['completed']+[step];temp['attempts'][-1]=dict(temp['attempts'][-1],transport=operation,outcome='STRICT_PASS')
            prior_l,prior_n,_,_=self.prior(temp,native,expected);chain=self.chain(temp,prior_n,native,expected);self.full_draft(temp,expected,wanted,legacy,native,chain=chain,operation=operation)
        report={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'STRICT_DRAFT_SOURCE_NATIVE_LEGACY_FILES_PIDS_PASS','record_id':rid if step in{'NEW_VERSION','CREATE_WEEK'}else state['record_id'],'step':step,'transport':operation,'prewrite_pending_account':getattr(self,'pending_evidence',None),'owned_native_get':nb,'owned_legacy_get':lb,'expected_native':deepcopy(native),'expected_legacy':deepcopy(legacy),'server_context':deepcopy(self.last_server_context),'native_audit':deepcopy(self.last_draft_audit),'source_chain_native_gets':deepcopy(self.sources),'scientific_acceptance':'UNCHANGED_EXISTING_GATE_ONLY','certifies':False}
        # Audit-admitted complete native server representations become the
        # next temporal baseline. Main data has already matched independent
        # source/payload/upload expectations, never the after body itself.
        self.sequence+=1;return self.emit('validated/'+f'{self.sequence:03d}.json',report),ownership
    def published(self,state,response,operation):
        rid=state['record_id'];doi='10.5281/zenodo.'+rid
        engine.need(str(response.get('id'))==rid and response.get('doi')==doi and str(response.get('conceptrecid'))==state['concept_id'],'OWN_PUBLISH_PID_IDENTITIES')
        post=Path(operation['path']);before_path=post.parent/f'{int(post.name[:3])-1:03d}_GET.json'
        before_obj=json.loads(engine.raw(before_path));engine.need(before_obj.get('url')==BASE+'/api/records/'+rid+'/draft'and before_obj.get('accept')==NATIVE and before_obj.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','FINAL_REAL_PREPUBLISH_GET')
        before_binding=engine.binding(before_path)
        reserve=next(a['transport']for a in state['attempts']if a['step']=='RESERVE_DOI'and a['outcome']=='STRICT_PASS')
        metadata_sent=next((a['transport']for a in state['attempts']if a['step']=='METADATA'and a['outcome']=='STRICT_PASS'),state['creation_receipt']if self.plan['start_kind']=='CREATE_WEEK'else None)
        engine.need(metadata_sent is not None,'REAL_EXPLICIT_METADATA_PAYLOAD_OPERATION')
        native,nb=self.get(rid,True,True);legacy,lb=self.get(rid,True)
        # Final main controls are all six approved package bytes, not a server
        # projection. Previews/media/revisions/flags are logged without polling.
        controlled=self.controlled(state,self.before_expected,self.before_legacy,phase='PUBLISHED')
        controlled['files']=[{'name':name,'bytes':row['bytes'],'md5':row['md5']}for name,row in sorted(self.inventory.items())]
        ownership=self.ownership(state);audit=own_rule.require_own_readback(native,legacy,controlled=controlled,ownership=ownership)
        expected,legacy_expected=own_rule.public_projection(controlled)
        legacy_expected['metadata']=deepcopy(self.manifest['public_metadata'])
        prior_l,prior_n,prior_lb,prior_nb=self.prior(state,native,expected,'PUBLISH',operation,before_obj['response'])
        relation=self.emit('RELATION_TEMPLATE.json',self.relation);payload=self.emit('CONTROLLED_METADATA_PAYLOAD.json',self.payload)
        roles={'authority':self.plan['authority'],'digest_manifest':self.plan['digest_manifest'],'source_legacy_receipt':self.plan['source_legacy_receipt'],'source_native_receipt':self.plan['source_native_receipt'],'creation_receipt':state['creation_receipt'],'first_own_native_draft':state['first_owned_draft'],'first_own_legacy_draft':state['first_owned_legacy_draft'],'metadata_payload':payload,'metadata_put_receipt':metadata_sent,'relation_template':relation,'reservation_receipt':reserve,'before_publish_native_receipt':before_binding,'publish_receipt':operation,'prior_after_native_receipt':prior_nb,'prior_after_legacy_receipt':prior_lb}
        context=own_rule.assemble_context(record_id=rid,source_bindings=roles);context_binding=self.emit('PUBLIC_STATE_CONTEXT.json',context)
        prediction=own_rule.consume_context(context,load=lambda b:engine.bound(self.root,b)[1],public=self.manifest['public_metadata'],evidence_sources={'source_legacy_receipt':self.plan['source_legacy_receipt'],'source_native_receipt':self.plan['source_native_receipt'],'own_publish_receipt':operation})
        engine.need(metadata.exact(expected,prediction['native'])and metadata.exact(legacy_expected,prediction['legacy']),'CONTROLLED_PUBLIC_EXPECTATIONS_MATCH_CURRENT_CONTEXT')
        own=json.loads(engine.raw(Path(operation['path'])));own=dict(own,record_id=rid,doi=doi)
        def download(entry,record_id):
            return self.downloads.get(entry['key'],record_id,self.inventory[entry['key']],published=True,published_url=BASE+'/api/records/'+rid+'/files/'+entry['key']+'/content')
        def check_metadata(actual,expected_record,own_receipt):
            own_rule.require_own_readback(native,actual,controlled=controlled,ownership=ownership)
        strict=digest.strict_readback(self.package,self.root,legacy,own,download,expected_record=legacy_expected,metadata_consumer=check_metadata)
        nbinding=self.emit('EXPECTED_PUBLIC_NATIVE.json',expected);lbinding=self.emit('EXPECTED_PUBLIC_LEGACY.json',legacy_expected)
        server={'operation':'NEW_VERSION','phase':'PUBLISHED'};sbinding=self.emit('SERVER_CONTEXT.json',server);strictbinding=self.emit('STRICT_DIGEST_READBACK.json',strict)
        import methods_digest_registration as registrar
        downloads=[{'filename':x['filename'],'binding':{'path':x['path'],'sha256':x['sha256']},'url':x['url']}for x in self.downloads.public if x['url'].startswith(BASE+'/api/records/'+rid+'/')]
        evidence=registrar.assemble_evidence(record_id=rid,public_legacy_receipt=lb,public_native_receipt=nb,own_publish_receipt=operation,expected_legacy=lbinding,expected_native=nbinding,source_legacy_receipt=self.plan['source_legacy_receipt'],source_native_receipt=self.plan['source_native_receipt'],relation_template=relation,server_context=sbinding,downloads=downloads,strict_readback_result=strictbinding,public_state_context=context_binding)
        ebinding=self.emit('METHODS_DIGEST_PUBLIC_EVIDENCE.json',evidence)
        registration=registrar.prepare_registration(self.root,self.package,ebinding);rbinding=self.emit('METHODS_DIGEST_REGISTRATION_RECEIPT.json',registration);registrar.require_registration(self.root,rbinding)
        report={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'PUBLISHED_OWN_CONTROLLED_NATIVE_LEGACY_SIX_FILES_PID_DEFAULT_REGISTRAR_PASS','record_id':rid,'step':'PUBLISH','transport':operation,'owned_native_get':nb,'owned_legacy_get':lb,'expected_native':expected,'expected_legacy':legacy_expected,'native_audit':audit,'strict_digest_readback':strictbinding,'registration_receipt':rbinding,'public_evidence':ebinding,'preview_polls':[],'certifies':False}
        return self.emit('validated/PUBLISHED.json',report),None
