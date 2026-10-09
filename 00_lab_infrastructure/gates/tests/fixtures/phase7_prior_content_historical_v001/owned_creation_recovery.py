"""Explicit approved recovery of one successful, held NEW_VERSION creation.

This module never sends a request, creates a version, edits a prior checkpoint,
or grants scientific admission.  The candidate constructor records provenance;
the actual entry then replays the source-bound runtime and every completed
operation before returning a seed for a DISTINCT plan/execution directory.
"""
from copy import deepcopy
import hashlib, json
from pathlib import Path
import owned_digest_machine as machine

STANDARD='VRS-METHODS-DIGEST-EXPLICIT-OWN-CREATION-RECOVERY-1'
APPROVED_OWN_RECORD='23246368'
APPROVED_PREDECESSOR='23226761'
APPROVED_CONCEPT='23226760'
class RecoveryHold(ValueError): pass
def need(value,reason):
    if not value: raise RecoveryHold('HOLD_'+reason)
def exact(left,right):
    return machine.encode(left)==machine.encode(right)
def _receipt(value,method,url,*,native=False,status=200):
    need(isinstance(value,dict) and value.get('environment')=='zenodo.org' and value.get('method')==method and value.get('url')==url and value.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE' and value.get('http_status')==status and isinstance(value.get('response'),dict),'GENUINE_OWN_RECEIPT')
    if native: need(value.get('accept')=='application/vnd.inveniordm.v1+json','GENUINE_NATIVE_REPRESENTATION')
    return value['response']

def candidate_seed(old_plan,new_plan,old_hold,*,sources,creation_receipt,first_legacy_receipt,first_native_receipt,readmission):
    """Produce an UNADMITTED candidate.  Call recover() for actual admission.

    The old attempt is neither retried nor rewritten.  Its original reservation
    and transport remain in the new explicitly authorized lineage, consuming
    their existing daily slot.  Scientific/package admission is independent.
    """
    roles={'old_plan','new_plan','old_hold','first_legacy','first_native','readmission','authority'}
    need(isinstance(sources,dict) and set(sources)==roles,'EXACT_RECOVERY_SOURCE_ROLES')
    for value in sources.values():machine.binding(value)
    machine.validate(old_hold,machine.digest(old_plan))
    need(old_hold['phase']=='HOLD' and old_hold['published'] is False and old_hold['record_id'] is None and old_hold['creation_receipt'] is None and old_hold['completed']==[] and len(old_hold['attempts'])==1,'ONE_HELD_SUCCESSFUL_CREATION_ONLY')
    attempted=old_hold['attempts'][0]
    need(attempted['step']=='NEW_VERSION' and attempted['outcome']=='HOLD' and attempted['transport'] is not None and attempted['validation'] is None and old_hold['start_kind']=='NEW_VERSION','EXPLICIT_HELD_START_ONLY')
    need(old_hold['failure']=='inherited creation metadata changed','EXACT_APPROVED_DATE_HOLD')
    need(old_plan['start_kind']==new_plan['start_kind']=='NEW_VERSION','NEVER_CREATE_ANOTHER_VERSION')
    for field in ('canonical_root','release_week','predecessor_record_id','expected_concept_id','source_concept_id','prior_run_ids','new_run_ids','predecessor_registration','registration_recovery','source_legacy_receipt','source_native_receipt','source_native_before_create','community_mirror_proof'):
        need(exact(old_plan[field],new_plan[field]),'EXACT_RECOVERY_IDENTITY_SCOPE:'+field)
    need(old_plan['execution_directory']!=new_plan['execution_directory'] and machine.digest(old_plan)!=machine.digest(new_plan),'DISTINCT_IMMUTABLE_PLAN_HISTORY')
    need(old_plan['authority']!=new_plan['authority'] and sources['authority']==new_plan['authority'],'NEW_APPROVED_AUTHORITY_BOUND')
    need(old_hold['approved_inventory']==old_plan['approved_inventory'],'OLD_APPROVED_INVENTORY_EXACT')
    machine.inventory(new_plan['approved_inventory'])
    original_path=Path(attempted['transport']['path'])
    try: ordinal=int(original_path.name.split('_',1)[0])
    except (TypeError,ValueError):raise RecoveryHold('HOLD_ORIGINAL_TRANSPORT_SEQUENCE')
    need(original_path.name==f'{ordinal:03d}_POST.json' and sources['first_legacy']['path']==str(original_path.parent/f'{ordinal+1:03d}_GET.json') and sources['first_native']['path']==str(original_path.parent/f'{ordinal+2:03d}_GET.json'),'GENUINE_ORIGINAL_FIRST_PAIR_SEQUENCE')
    src=new_plan['predecessor_record_id'];parent=new_plan['expected_concept_id'];base='https://zenodo.org'
    created=_receipt(creation_receipt,'POST',base+'/api/deposit/depositions/'+src+'/actions/newversion',status=201)
    need(creation_receipt.get('request_body_sha256')==hashlib.sha256(b'{}').hexdigest(),'EXACT_ORIGINAL_START_BODY')
    rid=str(created.get('id'))
    need(rid not in{src,parent} and rid.isdecimal() and str(int(rid))==rid and str(created.get('conceptrecid'))==parent and created.get('state')=='unsubmitted' and created.get('submitted') is False,'EXISTING_OWN_DRAFT_ONLY')
    need((rid,src,parent,new_plan['release_week'])==(APPROVED_OWN_RECORD,APPROVED_PREDECESSOR,APPROVED_CONCEPT,'2026-W41'),'EXACT_EXPLICITLY_APPROVED_RECOVERY_RECORD')
    first_l=_receipt(first_legacy_receipt,'GET',base+'/api/deposit/depositions/'+rid)
    first_n=_receipt(first_native_receipt,'GET',base+'/api/records/'+rid+'/draft',native=True)
    need(str(first_l.get('id'))==rid and str(first_l.get('conceptrecid'))==parent and first_n.get('id')==rid and first_n.get('parent',{}).get('id')==parent,'GENUINE_FIRST_PAIR_IDENTITY')
    need(isinstance(readmission,dict) and readmission.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1' and readmission.get('record_id')==rid and readmission.get('step')=='NEW_VERSION' and readmission.get('transport')==attempted['transport'],'NEW_STRICT_BOUND_READMISSION')
    recovery=readmission.get('explicit_creation_recovery')
    need(isinstance(recovery,dict) and set(recovery)=={'standard','status','old_plan','old_hold','authority','original_reservation','original_operation_id','no_network_write'} and recovery['standard']==STANDARD and recovery['status']=='CURRENT_OWN_RECORD_RULE_READMISSION_ONLY' and recovery['old_plan']==sources['old_plan'] and recovery['old_hold']==sources['old_hold'] and recovery['authority']==sources['authority'] and recovery['original_reservation']==attempted['reservation'] and recovery['original_operation_id']==attempted['operation_id'] and recovery['no_network_write'] is True,'EXPLICIT_IMMUTABLE_RECOVERY_LINEAGE')
    need(readmission.get('owned_legacy_get') is not None and readmission.get('owned_native_get') is not None,'FRESH_READMISSION_PAIR_REQUIRED')
    rows=created.get('files');need(isinstance(rows,list),'REAL_INHERITED_CREATION_ROWS');inherited=[{k:deepcopy(row[k])for k in ('id','filename','filesize','checksum','links')}for row in rows]
    ownership={'record_id':rid,'concept_id':parent,'first_owned_draft':deepcopy(sources['first_native']),'first_owned_legacy_draft':deepcopy(sources['first_legacy']),'inherited_inventory':inherited}
    state=machine.initial(machine.digest(new_plan),new_plan['approved_inventory'],start_kind='NEW_VERSION')
    state=machine.reserve(state,'NEW_VERSION',attempted['reservation'],attempted['operation_id'])
    state=machine.finish(state,attempted['transport'],sources['readmission'],ownership=ownership)
    need(machine.next_step(state).startswith('DROP:'),'RECOVERY_NEVER_RESUBMITS_NEW_VERSION')
    receipt={'standard':STANDARD,'status':'SOURCE_BOUND_RECOVERY_CANDIDATE_NOT_ADMITTED','record_id':rid,'concept_id':parent,'source_bindings':deepcopy(sources),'original_creation_transport':deepcopy(attempted['transport']),'original_reservation':deepcopy(attempted['reservation']),'original_operation_id':attempted['operation_id'],'old_hold_retained':True,'original_attempt_still_charged':True,'network_writes':0,'new_versions_created':0,'certifies':False}
    return state,receipt

def recover(root,*,old_plan_binding,new_plan_binding,old_hold_binding,first_legacy_binding,first_native_binding,readmission_binding):
    """Re-admit through the current exact source session; no output/write here."""
    import weekly_digest_executor as engine
    import weekly_digest_runtime as runtime
    root=Path(root).resolve(strict=True)
    _,old_plan=engine.bound(root,old_plan_binding);_,new_plan=engine.bound(root,new_plan_binding);_,old_hold=engine.bound(root,old_hold_binding)
    actual=runtime.ActualRuntime(root,new_plan);package=engine.require_plan(root,new_plan);actual.admission(new_plan,package)
    row=next((p for p in new_plan['purpose_source_pins']if p['name']=='owned_creation_recovery.py'),None)
    need(row is not None and row['path']==str(Path(__file__).resolve()) and engine.sha(Path(__file__).resolve())==row['sha256'],'RECOVERY_HAS_CURRENT_MERGED_PURPOSE_ORIGIN')
    original=old_hold['attempts'][0]['transport'];_,created=engine.bound(root,original);_,first_l=engine.bound(root,first_legacy_binding);_,first_n=engine.bound(root,first_native_binding);_,readmission=engine.bound(root,readmission_binding)
    sources={'old_plan':old_plan_binding,'new_plan':new_plan_binding,'old_hold':old_hold_binding,'first_legacy':first_legacy_binding,'first_native':first_native_binding,'readmission':readmission_binding,'authority':new_plan['authority']}
    state,receipt=candidate_seed(old_plan,new_plan,old_hold,sources=sources,creation_receipt=created,first_legacy_receipt=first_l,first_native_receipt=first_n,readmission=readmission)
    # A hand-written readmission status cannot grant admission: source-bound
    # replay consumes its actual reservation/intents, receipts and own policy.
    actual.replay_checkpoint(new_plan,state);actual.admission(new_plan,package)
    need(engine.bound(root,old_hold_binding)[1]==old_hold,'OLD_HOLD_CHANGED_DURING_RECOVERY')
    receipt['status']='CURRENT_SOURCE_RUNTIME_FULL_REPLAY_RECOVERY_ADMITTED_NO_WRITE'
    return state,receipt

if __name__=='__main__':raise SystemExit('HOLD: explicit root call in the exact current source session only')
