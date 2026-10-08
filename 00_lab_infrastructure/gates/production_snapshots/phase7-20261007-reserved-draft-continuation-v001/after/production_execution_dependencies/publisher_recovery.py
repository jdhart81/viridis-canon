"""Append-only root recovery checkpoints; no network or retry authority.

Recovery is diagnostic. Only the original actual journal consumer determines
available mutation budget; incomplete reservation evidence remains HOLD.
"""
import hashlib,json,re
from pathlib import Path
STANDARD='VRS-PHASE7-DIGEST-RECOVERY-CHECKPOINT-1'

def checkpoint(result,*,plan_binding,inventory_binding,reservation=None,transport_receipt=None):
    return {'standard':STANDARD,'status':'READ_ONLY_RECOVERY_REQUIRED'if result['status'].startswith('HOLD')else'OPERATION_CHECKPOINT_ONLY',
        'phase':result['phase'],'attempted_mutations':result['writes'],'own_record_id':result['record_id'],'own_doi':result['doi'],
        'plan':plan_binding,'approved_six_files':inventory_binding,'reservation':reservation,'transport_receipt':transport_receipt,
        'automatic_retry':False,'replay_authorized':False,'certifies':False}

def inspect_checkpoints(directory,read_regular):
    """Retain all spent/uncertain slots, including a crash before a checkpoint."""
    directory=Path(directory).resolve(strict=True)
    def owned(path):
        p=Path(path)
        if not p.is_absolute()or p.is_symlink()or any(a.is_symlink()for a in p.parents)or not p.resolve().is_relative_to(directory):raise ValueError('HOLD_RECOVERY_FOREIGN_OR_UNSAFE_PATH')
        return p
    def bound(binding):
        if not isinstance(binding,dict)or set(binding)!={'path','sha256'}or re.fullmatch('[a-f0-9]{64}',str(binding['sha256']))is None:raise ValueError('HOLD_RECOVERY_BINDING_SCHEMA')
        p=owned(binding['path']);raw=read_regular(p)
        if hashlib.sha256(raw).hexdigest()!=binding['sha256']:raise ValueError('HOLD_RECOVERY_BOUND_SOURCE_CHANGED')
        return p,raw
    paths=sorted((directory/'checkpoints').glob('*.json'))
    if not paths:raise ValueError('HOLD_NO_RECOVERY_CHECKPOINT_NO_ZERO_ASSUMPTION')
    rows=[];previous=0;identity=None;plan=None;inventory=None
    for path in paths:
        if re.fullmatch('[0-9]{3}_[A-Z_]+[.]json',path.name)is None:raise ValueError('HOLD_FOREIGN_RECOVERY_FILE')
        raw=read_regular(owned(path));row=json.loads(raw)
        fields={'standard','status','phase','attempted_mutations','own_record_id','own_doi','plan','approved_six_files','reservation','transport_receipt','automatic_retry','replay_authorized','certifies'}
        if set(row)!=fields or row['standard']!=STANDARD or row['status']not in{'READ_ONLY_RECOVERY_REQUIRED','OPERATION_CHECKPOINT_ONLY'}or type(row['attempted_mutations'])is not int or not previous<=row['attempted_mutations']<=10 or any(row[k]is not False for k in('automatic_retry','replay_authorized','certifies')):raise ValueError('HOLD_RECOVERY_SCHEMA_OR_ATTEMPT_COUNT')
        if plan is None:plan=row['plan'];inventory=row['approved_six_files']
        if row['plan']!=plan or row['approved_six_files']!=inventory:raise ValueError('HOLD_RECOVERY_INPUTS_CHANGED')
        if bound(plan)[0]!=directory/'PLAN.json'or bound(inventory)[0]!=directory/'APPROVED_SIX_FILES.json':raise ValueError('HOLD_RECOVERY_INPUT_PATHS')
        for optional,folder in(('reservation','reservations'),('transport_receipt','transport')):
            if row[optional]is not None and not bound(row[optional])[0].is_relative_to(directory/folder):raise ValueError('HOLD_RECOVERY_OPTIONAL_BINDING_PATH')
        rid=row['own_record_id']
        if rid is not None:
            if not isinstance(rid,str)or re.fullmatch('[1-9][0-9]*',rid)is None or identity is not None and rid!=identity:raise ValueError('HOLD_RECOVERY_FOREIGN_RECORD')
            identity=rid
        if row['own_doi']is not None and row['own_doi']!='10.5281/zenodo.'+str(rid):raise ValueError('HOLD_RECOVERY_FOREIGN_DOI')
        previous=row['attempted_mutations'];rows.append({'binding':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()},'checkpoint':row})
    reservations=[];seen=set()
    for path in sorted((directory/'reservations').glob('*/RESERVATION.json')):
        raw=read_regular(owned(path));r=json.loads(raw)
        if set(r)!={'operation_id','method','host','at_utc','status','receipt_binding'}or r['operation_id']in seen or not isinstance(r['operation_id'],str)or not r['operation_id']or r['method']not in{'POST','PUT'}or r['host']!='zenodo.org'or r['status']!='STARTED_NO_RETRY':raise ValueError('HOLD_RECOVERY_RESERVATION_SCHEMA')
        seen.add(r['operation_id']);ip,ir=bound(r['receipt_binding']);intended=json.loads(ir)
        if ip!=path.parent/'INTENDED_REQUEST.json'or set(intended)!={'operation_id','method','url','request_body_sha256','transport_receipt_path'}or intended['operation_id']!=r['operation_id']or intended['method']!=r['method']or re.fullmatch('[a-f0-9]{64}',str(intended['request_body_sha256']))is None:raise ValueError('HOLD_RECOVERY_INTENDED_REQUEST')
        tp=owned(intended['transport_receipt_path'])
        if not tp.is_relative_to(directory/'transport'):raise ValueError('HOLD_RECOVERY_TRANSPORT_PATH')
        reservations.append({'binding':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()},'transport_receipt_path':str(tp),'receipt_present':tp.is_file()})
    if len(reservations)>10:raise ValueError('HOLD_RECOVERY_TOO_MANY_RESERVATIONS')
    if identity is not None:
        ref=json.loads(read_regular(owned(directory/'OWN_CREATION_RECEIPT.json')))
        if set(ref)!={'standard','status','receipt'}or ref['standard']!='SOURCE_BOUND_TRANSPORT_REFERENCE_1'or ref['status']!='REFERENCE_ONLY_NOT_ANOTHER_MUTATION':raise ValueError('HOLD_RECOVERY_OWN_CREATION_REFERENCE')
        cp,cr=bound(ref['receipt']);creation=json.loads(cr)
        if not cp.is_relative_to(directory/'transport')or creation.get('method')!='POST'or creation.get('url')!='https://zenodo.org/api/deposit/depositions'or creation.get('environment')!='zenodo.org'or creation.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'or str(creation.get('response',{}).get('id'))!=identity:raise ValueError('HOLD_RECOVERY_UNANCHORED_OWN_RECORD')
    return {'status':'READ_ONLY_RECOVERY_INVENTORY','last_checkpoint':rows[-1],'attempted_mutations_at_least':max(previous,len(reservations)),'own_record_id':identity,'reservation_evidence':reservations,
        'next_action':'Fresh original journal validation and own saved receipts plus GET only. Never replay an uncertain request or create another weekly record.',
        'automatic_retry':False,'replay_authorized':False,'certifies':False}
