"""Pure, closed next-step machine. No HTTP, credentials, scientific admission.

A step only advances after its own successful transport and full strict
readback. Uncertainty consumes an attempt and freezes the chain; it never
permits another start. Each invocation has at most four mutation attempts.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib, json, re

STANDARD = 'VRS-METHODS-DIGEST-OWNED-SUCCESSOR-CHECKPOINT-1'
FIELDS = {'standard','plan_sha256','phase','record_id','concept_id','creation_receipt',
          'first_owned_draft','first_owned_legacy_draft','approved_inventory','inherited_inventory','completed',
          'attempts','last_validation','published','failure','start_kind'}
NAMES = {'paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip',
         'DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'}
class MachineHold(ValueError): pass
def need(value,reason):
    if not value: raise MachineHold('HOLD_'+reason)
def encode(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def digest(value): return hashlib.sha256(encode(value)).hexdigest()
def binding(value):
    need(isinstance(value,dict) and set(value)=={'path','sha256'} and isinstance(value['path'],str) and value['path'].startswith('/') and isinstance(value['sha256'],str) and re.fullmatch('[0-9a-f]{64}',str(value['sha256'])) is not None,'CLOSED_REAL_BINDING')
    return value
def inventory(rows):
    need(isinstance(rows,list) and len(rows)==6 and {r.get('name') for r in rows if isinstance(r,dict)}==NAMES,'EXACT_SIX_MAIN_FILES')
    for r in rows:
        need(set(r)=={'name','path','bytes','sha256','md5'} and isinstance(r['path'],str) and r['path'].startswith('/') and type(r['bytes'])is int and r['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',str(r['sha256'])) is not None and re.fullmatch('[0-9a-f]{32}',str(r['md5'])) is not None,'CLOSED_MAIN_FILE_BYTES')
    return rows
def initial(plan_sha,approved,*,start_kind='NEW_VERSION'):
    need(re.fullmatch('[0-9a-f]{64}',str(plan_sha)) is not None,'PLAN_HASH')
    inventory(approved);need(start_kind in{'NEW_VERSION','CREATE_WEEK'},'CLOSED_START_KIND')
    return {'standard':STANDARD,'plan_sha256':plan_sha,'phase':'NOT_STARTED','record_id':None,'concept_id':None,'creation_receipt':None,'first_owned_draft':None,'first_owned_legacy_draft':None,'approved_inventory':deepcopy(approved),'inherited_inventory':None,'completed':[],'attempts':[],'last_validation':None,'published':False,'failure':None,'start_kind':start_kind}
def step_order(start_kind):
    need(start_kind in{'NEW_VERSION','CREATE_WEEK'},'CLOSED_START_KIND')
    start=[start_kind]
    if start_kind=='NEW_VERSION':start += ['DROP:'+n for n in sorted(NAMES)]+['METADATA']
    return start+['UPLOAD:'+n for n in sorted(NAMES)]+['RESERVE_DOI','PUBLISH']
def validate(state,plan_sha):
    need(isinstance(state,dict) and set(state)==FIELDS and state['standard']==STANDARD and state['plan_sha256']==plan_sha,'EXACT_CHECKPOINT')
    inventory(state['approved_inventory']); need(state['start_kind']in{'NEW_VERSION','CREATE_WEEK'}and isinstance(state['completed'],list) and len(state['completed'])==len(set(state['completed'])) and isinstance(state['attempts'],list),'CHECKPOINT_STEP_LIST')
    need(type(state['published'])is bool and state['phase']in{'NOT_STARTED','OWNED_DRAFT','PUBLISHED','UNCERTAIN','HOLD'},'CHECKPOINT_PHASE')
    ids=[a.get('operation_id') for a in state['attempts'] if isinstance(a,dict)]
    need(len(ids)==len(state['attempts']) and len(set(ids))==len(ids),'UNIQUE_ATTEMPTS')
    for a in state['attempts']:
        need(set(a)=={'operation_id','step','reservation','transport','validation','outcome'} and a['outcome']in{'RESERVED','STRICT_PASS','UNCERTAIN','HOLD'},'CLOSED_ATTEMPT')
        binding(a['reservation'])
        if a['transport']is not None: binding(a['transport'])
        if a['validation']is not None: binding(a['validation'])
        need((a['outcome']=='STRICT_PASS')==(a['step']in state['completed']),'ATTEMPT_COMPLETION')
    need(sum(a['outcome']=='STRICT_PASS' for a in state['attempts'])==len(state['completed']),'ONE_PASS_PER_STEP')
    order=step_order(state['start_kind'])
    need(state['completed']==order[:len(state['completed'])]and [a['step']for a in state['attempts']]==order[:len(state['attempts'])]and len(state['attempts'])<=len(order),'EXACT_ORDERED_OPERATION_PREFIX')
    need(all(a['outcome']=='STRICT_PASS'for a in state['attempts'][:-1])and len(state['attempts'])-len(state['completed'])in{0,1},'ONLY_LAST_ATTEMPT_UNFINISHED')
    if state['phase']in{'HOLD','UNCERTAIN'}:need(state['attempts']and state['attempts'][-1]['outcome']==state['phase']and isinstance(state['failure'],str),'FAILURE_STATE_HAS_REAL_ATTEMPT')
    else:need(state['failure']is None,'NO_HIDDEN_FAILURE')
    if state['phase']=='PUBLISHED':need(state['published']is True,'NO_FAKE_PUBLISHED_PHASE')
    if state['phase']=='NOT_STARTED':need(state['record_id']is None and state['concept_id']is None and not state['completed'] and state['creation_receipt']is None,'NO_INVENTED_ID')
    if state['record_id']is not None:
        need(isinstance(state['record_id'],str) and re.fullmatch('[1-9][0-9]*',state['record_id']) is not None and isinstance(state['concept_id'],str) and re.fullmatch('[1-9][0-9]*',state['concept_id']) is not None and state['record_id']!=state['concept_id'],'OWNED_IDENTITIES')
        binding(state['creation_receipt']);binding(state['first_owned_draft']);binding(state['first_owned_legacy_draft']);need(state['start_kind']in state['completed'],'OWNED_START_PASS')
        wanted_count=6 if state['start_kind']=='NEW_VERSION'else 0
        need(isinstance(state['inherited_inventory'],list) and len(state['inherited_inventory'])==wanted_count and ({x.get('filename')for x in state['inherited_inventory']}==NAMES if wanted_count else state['inherited_inventory']==[]),'EXACT_INHERITED_FILES')
        need(all(isinstance(r,dict)and set(r)=={'checksum','filename','filesize','id','links'}and isinstance(r['id'],str)and type(r['filesize'])is int and r['filesize']>=0 and re.fullmatch('[0-9a-f]{32}',str(r['checksum'])) is not None for r in state['inherited_inventory']),'CLOSED_INHERITED_FILES')
    if state['published']:need(state['phase']=='PUBLISHED' and state['completed'][-1]=='PUBLISH' and state['last_validation']is not None,'NO_FAKE_TERMINAL')
    if state['last_validation']is not None:binding(state['last_validation'])
    return state
def next_step(state):
    validate(state,state['plan_sha256'])
    need(state['phase']not in{'UNCERTAIN','HOLD'},'NO_AUTOMATIC_RETRY')
    need(all(a['outcome']=='STRICT_PASS'for a in state['attempts']),'NO_RESERVED_STEP_REPLAY')
    if state['published']: return None
    if state['record_id']is None:
        need(not state['attempts'],'START_ONCE');return state['start_kind']
    for r in sorted(state['inherited_inventory'],key=lambda x:x['filename']):
        step='DROP:'+r['filename']
        if step not in state['completed']:return step
    if state['start_kind']=='NEW_VERSION'and 'METADATA'not in state['completed']:return 'METADATA'
    for row in sorted(state['approved_inventory'],key=lambda x:x['name']):
        step='UPLOAD:'+row['name']
        if step not in state['completed']:return step
    if 'RESERVE_DOI'not in state['completed']:return 'RESERVE_DOI'
    return 'PUBLISH'
def reserve(state,step,reservation,operation_id):
    need(next_step(state)==step,'EXACT_NEXT_STEP');binding(reservation)
    need(isinstance(operation_id,str)and re.fullmatch('[A-Za-z0-9:_-]+',operation_id)is not None and all(a['operation_id']!=operation_id for a in state['attempts']),'NEW_OPERATION_ID')
    out=deepcopy(state);out['attempts'].append({'operation_id':operation_id,'step':step,'reservation':deepcopy(reservation),'transport':None,'validation':None,'outcome':'RESERVED'});return out
def finish(state,transport,validation,*,ownership=None):
    binding(transport);binding(validation);out=deepcopy(state);need(out['attempts']and out['attempts'][-1]['outcome']=='RESERVED','OWN_RESERVED_OPERATION')
    a=out['attempts'][-1];step=a['step'];a.update(transport=deepcopy(transport),validation=deepcopy(validation),outcome='STRICT_PASS');out['completed'].append(step);out['last_validation']=deepcopy(validation)
    if step in{'NEW_VERSION','CREATE_WEEK'}:
        need(isinstance(ownership,dict)and set(ownership)=={'record_id','concept_id','first_owned_draft','first_owned_legacy_draft','inherited_inventory'},'REAL_CREATION_OWNERSHIP')
        out.update(deepcopy(ownership));out['creation_receipt']=deepcopy(transport);out['phase']='OWNED_DRAFT'
    else:need(ownership is None,'NO_LATE_ID_OVERRIDE')
    if step=='PUBLISH':out['published']=True;out['phase']='PUBLISHED'
    return validate(out,out['plan_sha256'])
def fail(state,transport,reason,*,uncertain):
    out=deepcopy(state);need(out['attempts']and out['attempts'][-1]['outcome']=='RESERVED','OWN_FAILED_ATTEMPT')
    if transport is not None:binding(transport)
    a=out['attempts'][-1];a['transport']=deepcopy(transport);a['outcome']='UNCERTAIN'if uncertain else'HOLD';out['phase']=a['outcome'];out['failure']=str(reason);return validate(out,out['plan_sha256'])
