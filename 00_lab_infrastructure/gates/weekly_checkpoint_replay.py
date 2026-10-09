"""Replay genuine completed draft operations; no cached status admission.

Reconstruct metadata/main-file/PID expectations from source/creation and each
own transport ACK before invoking the unchanged full saved native/legacy
consumers. Fresh live GET/download checks still run before the next mutation.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib,json,re
from pathlib import Path
import weekly_digest_executor as e
import owned_digest_machine as machine
import digest_weekly_state as successor
import digest_metadata as metadata
import first_digest_state as original
import server_managed_fields as sm
import publication_preservation as preservation
import owned_legacy_preview_aliases as legacy_aliases
import own_record_comparison as own_rule
from weekly_digest_boundary import initial_owned_projection

def obj(root,b):return e.bound(root,b)[1]
def require_receipt(value,method,url):
    e.need(isinstance(value,dict)and value.get('environment')=='zenodo.org'and value.get('method')==method and value.get('url')==url and value.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and type(value.get('http_status'))is int and 200<=value['http_status']<300 and isinstance(value.get('response'),dict)and re.fullmatch('[0-9a-f]{64}',str(value.get('response_sha256')))is not None,'REAL_SUCCESSFUL_STEP_RECEIPT');return value['response']
def require_checkpoint(plan,state,*,root):
    root=Path(root);machine.validate(state,machine.digest(plan))
    if state['phase']=='NOT_STARTED':
        e.need(state==machine.initial(machine.digest(plan),plan['approved_inventory'],start_kind=plan['start_kind']),'EXACT_UNUSED_INITIAL_CHECKPOINT_ONLY')
        return {'status':'EXACT_ZERO_ATTEMPT_INITIAL_CHECKPOINT_REPLAYED_NOT_OWNERSHIP','steps':0,'record_id':None,'certifies':False}
    e.need(state['phase']=='OWNED_DRAFT'and not state['published'],'OWNED_NONTERMINAL_CHECKPOINT')
    prior_l=obj(root,plan['source_legacy_receipt'])['response'];prior_n=obj(root,plan['source_native_before_create'])['response'];rid=state['record_id'];base='https://zenodo.org';created=obj(root,state['creation_receipt']);first_l=obj(root,state['first_owned_legacy_draft']);first_n=obj(root,state['first_owned_draft']);require_receipt(first_l,'GET',base+'/api/deposit/depositions/'+rid);require_receipt(first_n,'GET',base+'/api/records/'+rid+'/draft');e.need(first_n.get('accept')=='application/vnd.inveniordm.v1+json','FIRST_NATIVE_REPRESENTATION')
    manifest=obj(root,plan['digest_manifest'])
    relation=successor.registered_relation_template(plan['predecessor_registration'],root=root,source_native=prior_n,source_legacy=prior_l)
    if plan['start_kind']=='NEW_VERSION':expected,wanted=initial_owned_projection(prior_l,prior_n,created,first_l,first_n)
    else:expected,wanted=deepcopy(first_n['response']),deepcopy(first_l['response']);expected['files']['entries']={};wanted['files']=[];original.refresh_totals(expected)
    payload=original.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],prior_l['metadata']));native_meta=metadata.native_metadata(manifest['public_metadata'],prior_l['metadata'],prior_l,prior_n,relation);inventory={x['name']:dict(x,size=x['bytes'])for x in plan['approved_inventory']}
    for attempt in state['attempts']:
        e.need(attempt['outcome']=='STRICT_PASS','NO_RESERVED_FAILED_UNCERTAIN_REPLAY');reservation=obj(root,attempt['reservation']);e.need(reservation.get('operation_id')==attempt['operation_id']and reservation.get('status')=='STARTED_NO_RETRY','ACTUAL_OWN_RESERVATION');intent=obj(root,reservation['receipt_binding']);own=obj(root,attempt['transport']);e.need(intent['operation_id']==attempt['operation_id']and intent['transport_receipt_path']==attempt['transport']['path']and intent['method']==own['method']and intent['url']==own['url']and intent['request_body_sha256']==own.get('request_body_sha256'),'EXACT_INTENDED_TRANSPORT');report=obj(root,attempt['validation']);e.need(report.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1'and report.get('record_id')==rid and report.get('transport')==attempt['transport']and report.get('step')==attempt['step'],'OWN_BOUND_FULL_READBACK')
        step=attempt['step'];legacy_receipt=obj(root,report['owned_legacy_get']);native_receipt=obj(root,report['owned_native_get']);legacy=require_receipt(legacy_receipt,'GET',base+'/api/deposit/depositions/'+rid);native=require_receipt(native_receipt,'GET',base+'/api/records/'+rid+'/draft');e.need(native_receipt.get('accept')=='application/vnd.inveniordm.v1+json','ACTUAL_NATIVE_GET');before=deepcopy(expected)
        if step in{'NEW_VERSION','CREATE_WEEK'}:
            e.need(step==plan['start_kind'],'EXACT_APPROVED_OWN_START_KIND');endpoint=base+'/api/deposit/depositions/'+plan['predecessor_record_id']+'/actions/newversion'if step=='NEW_VERSION'else base+'/api/deposit/depositions';ack=require_receipt(own,'POST',endpoint);body=b'{}'if step=='NEW_VERSION'else e.raw_json(payload);e.need(own==created and intent['request_body_sha256']==hashlib.sha256(body).hexdigest(),'ONE_EXACT_START')
        elif step.startswith('DROP:'):
            name=step[5:];entry=next(x for x in state['inherited_inventory']if x['filename']==name);ack=require_receipt(own,'DELETE',base+'/api/deposit/depositions/'+rid+'/files/'+entry['id']);e.need(ack=={'empty_204':True,'draft_file_removed':True}and own['http_status']==204 and intent['request_body_sha256']==hashlib.sha256(b'').hexdigest(),'EMPTY_204_OWN_DROP');expected['files']['entries'].pop(name);wanted['files']=[x for x in wanted['files']if x['filename']!=name];original.refresh_totals(expected)
        elif step=='METADATA':ack=require_receipt(own,'PUT',base+'/api/deposit/depositions/'+rid);e.need(intent['request_body_sha256']==hashlib.sha256(e.raw_json(payload)).hexdigest(),'EXACT_METADATA_BODY');expected['metadata']=deepcopy(native_meta);wanted['metadata']=deepcopy(payload['metadata'])
        elif step.startswith('UPLOAD:'):
            name=step[7:];spec=inventory[name];ack=require_receipt(own,'PUT',wanted['links']['bucket']+'/'+name);e.need(intent['request_body_sha256']==spec['sha256']and hashlib.sha256(e.raw(Path(spec['path']))).hexdigest()==spec['sha256'],'EXACT_APPROVED_UPLOAD');e.need(ack.get('key')==name and ack.get('checksum')=='md5:'+spec['md5']and type(ack.get('size'))is int and ack.get('size')==spec['size'],'OWN_UPLOAD_ACK_BYTES');row=next(x for x in legacy['files']if x['filename']==name);expected['files']['entries'][name]={**native['files']['entries'][name],'key':name,'checksum':'md5:'+spec['md5'],'size':spec['size']};wanted['files'].append(row);original.refresh_totals(expected)
        elif step=='RESERVE_DOI':
            ack=require_receipt(own,'POST',base+'/api/records/'+rid+'/draft/pids/doi');e.need(ack.get('id')==rid and ack.get('parent',{}).get('id')==state['concept_id']and ack.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+rid and intent['request_body_sha256']==hashlib.sha256(b'{}').hexdigest(),'EXACT_OWN_RESERVATION')
            expected['pids']=deepcopy(ack['pids'])
            wanted['doi']='10.5281/zenodo.'+rid
        else:raise e.ExecutionHold('HOLD_UNLISTED_COMPLETED_DRAFT_STEP')
        ownership={'creation_receipt':created,'first_native_receipt':first_n,'first_legacy_receipt':first_l,'prior_ids':[plan['predecessor_record_id'],plan['source_concept_id']]}
        own_rule.require_ownership(created,first_n,first_l,prior_ids=ownership['prior_ids'])
        sent=plan['start_kind']=='CREATE_WEEK'or any(a['step']=='METADATA'for a in state['attempts'][:state['attempts'].index(attempt)+1])
        if sent:
            native_md=own_rule.native_sent_metadata(native_meta);legacy_md=deepcopy(payload['metadata'])
        else:
            initial=own_rule.initial_projection(prior_l,prior_n,created,first_l,first_n);native_md=initial['controlled']['native_metadata'];legacy_md=initial['controlled']['legacy_metadata']
        controlled={'record_id':rid,'concept_id':state['concept_id'],'phase':'DRAFT','native_metadata':native_md,'legacy_metadata':legacy_md,'files':[{'name':name,'bytes':entry['size'],'md5':entry['checksum'][4:]}for name,entry in sorted(expected['files']['entries'].items())],'communities':deepcopy(payload['metadata'].get('communities',[])),'native_community_ids':deepcopy(prior_n.get('parent',{}).get('communities',{}).get('ids',[])),'doi_required':any(a['step']=='RESERVE_DOI'for a in state['attempts'][:state['attempts'].index(attempt)+1])}
        own_rule.require_own_readback(native,legacy,controlled=controlled,ownership=ownership)
        e.need(metadata.exact(report['expected_native'],native)and metadata.exact(report['expected_legacy'],legacy),'VALIDATION_BASELINE_NOT_OWN_GET')
        expected=deepcopy(native);wanted=deepcopy(legacy)
    last=obj(root,state['last_validation']);e.need(metadata.exact(last['expected_native'],expected)and metadata.exact(last['expected_legacy'],wanted),'LAST_CHECKPOINT_EXPECTATIONS')
    return {'status':'ALL_COMPLETED_DRAFT_OPERATIONS_REPLAYED_WITH_UNCHANGED_CONSUMERS','steps':len(state['attempts']),'record_id':rid,'certifies':False}
