"""Purpose-only owned FIRST continuation guard over complete raw account pages.

The original initial absence producer/selector remains unchanged. Only the
exact draft already owned by a fully replayed genuine CREATE may be projected
out of a continuation's account listing; this never issues public evidence.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib,re
import weekly_digest_executor as e
import owned_digest_machine as machine
import owned_weekly_discovery as original

STANDARD='VRS-METHODS-DIGEST-OWNED-PENDING-ACCOUNT-CONTINUATION-1'
FIELDS={'standard','release_week','plan_sha256','record_id','concept_id','creation_receipt','first_owned_draft','first_owned_legacy_draft','last_validation','passes','records','record_count','own_pending_count','producer_sha256','writes','status'}
def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def typed(a,b):return e.raw_json(a)==e.raw_json(b)
def owned_projection(root,plan,state):
    machine.validate(state,machine.digest(plan))
    e.need(plan['start_kind']=='CREATE_WEEK'and state['start_kind']=='CREATE_WEEK'and state['phase']=='OWNED_DRAFT'and state['published']is False and state['attempts']and all(a['outcome']=='STRICT_PASS'for a in state['attempts']),'EXACT_OWNED_PENDING_FIRST_CHECKPOINT')
    import weekly_checkpoint_replay
    weekly_checkpoint_replay.require_checkpoint(plan,state,root=root)
    rid=state['record_id'];parent=state['concept_id'];_,created=e.bound(root,state['creation_receipt']);_,first_native=e.bound(root,state['first_owned_draft']);_,first_legacy=e.bound(root,state['first_owned_legacy_draft']);_,last=e.bound(root,state['last_validation'])
    e.need(created.get('environment')=='zenodo.org'and created.get('method')=='POST'and created.get('url')=='https://zenodo.org/api/deposit/depositions'and created.get('http_status')==201 and created.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','GENUINE_OWN_CREATE_FOR_ACCOUNT_CONTINUATION')
    ack=created.get('response');e.need(isinstance(ack,dict)and str(ack.get('id'))==rid and str(ack.get('conceptrecid'))==parent and ack.get('submitted')is False and ack.get('state')=='unsubmitted'and ack.get('files')==[] and ack.get('links',{}).get('latest_draft')=='https://zenodo.org/api/deposit/depositions/'+rid,'EXACT_OWN_CREATE_IDENTITY')
    for receipt,native in((first_native,True),(first_legacy,False)):
        e.need(receipt.get('environment')=='zenodo.org'and receipt.get('method')=='GET'and receipt.get('http_status')==200 and receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and receipt.get('url')==('https://zenodo.org/api/records/'+rid+'/draft'if native else'https://zenodo.org/api/deposit/depositions/'+rid),'GENUINE_FIRST_OWN_PENDING_GET')
        body=receipt.get('response');e.need(isinstance(body,dict)and str(body.get('id'))==rid and (body.get('parent',{}).get('id')if native else str(body.get('conceptrecid')))==parent,'FIRST_OWN_PENDING_GET_IDENTITY')
        if native:e.need(receipt.get('accept')=='application/vnd.inveniordm.v1+json','FIRST_OWN_NATIVE_PENDING_REPRESENTATION')
    e.need(last.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1'and last.get('record_id')==rid and last.get('status')=='STRICT_DRAFT_SOURCE_NATIVE_LEGACY_FILES_PIDS_PASS','ACTUAL_LAST_OWN_PENDING_READBACK')
    _,current=e.bound(root,last['owned_native_get']);body=current.get('response')
    e.need(current.get('method')=='GET'and current.get('url')=='https://zenodo.org/api/records/'+rid+'/draft'and current.get('environment')=='zenodo.org'and current.get('http_status')==200 and current.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and current.get('accept')=='application/vnd.inveniordm.v1+json'and typed(body,last.get('expected_native')),'REPLAYED_OWN_PENDING_NATIVE_BASELINE')
    e.need(body.get('id')==rid and body.get('parent',{}).get('id')==parent and body.get('is_draft')is True and body.get('is_published')is False and body.get('status')=='draft'and body.get('metadata',{}).get('title')=='Viridis Methods Digest — '+plan['release_week'],'EXACT_OWN_WEEK_PENDING_NATIVE')
    return body

def require_pending(value,*,root,plan,state):
    root=Path(root).resolve(strict=True);body=owned_projection(root,plan,state)
    e.need(isinstance(value,dict)and set(value)==FIELDS and value['standard']==STANDARD and value['status']=='COMPLETE_OWN_PENDING_ACCOUNT_CONTINUATION_NOT_PUBLICATION_CLEARANCE'and value['producer_sha256']==source_sha()and type(value['writes'])is int and value['writes']==0 and value['plan_sha256']==machine.digest(plan)and value['release_week']==plan['release_week'],'EXACT_PENDING_ACCOUNT_PROOF')
    for key in('record_id','concept_id','creation_receipt','first_owned_draft','first_owned_legacy_draft','last_validation'):e.need(typed(value[key],state[key]),'EXACT_PENDING_ACCOUNT_OWN_STATE:'+key)
    e.need(isinstance(value['passes'],list)and len(value['passes'])==2,'REAL_PENDING_DOUBLE_PASS')
    first,second=[original.decode_pass(root,rows)for rows in value['passes']]
    e.need(typed(original.discovery_signature(first),original.discovery_signature(second)),'PENDING_ACCOUNT_RACE')
    _,records=e.bound(root,value['records']);e.need(typed(records,{'records':first})and type(value['record_count'])is int and value['record_count']==len(first),'EXACT_PENDING_ACCOUNT_RECORDS')
    rest=[];owned=[]
    for row in first:
        if original.identity(row)!=state['record_id']:rest.append(row);continue
        e.need(row.get('is_draft')is True and row.get('is_published')is False and row.get('status')=='draft','ONLY_GENUINE_OWN_UNPUBLISHED_ACCOUNT_ROW')
        for field in('metadata','parent','versions','pids'):e.need(typed(row.get(field),body.get(field)),'EXACT_PENDING_OWN_ACCOUNT_FIELD:'+field)
        owned.append(row)
    e.need(len(owned)<=1 and type(value['own_pending_count'])is int and value['own_pending_count']==len(owned),'ONLY_ONE_EXACT_OWN_PENDING_ROW')
    # Account endpoints may omit private drafts. Independent complete own
    # native/legacy readback remains required before the next mutation.
    result=original.discover(rest,plan['release_week'])
    e.need(result.get('status')=='NO_EXISTING_WEEKLY_RECORD','NO_FOREIGN_PENDING_OR_PUBLISHED_WEEKLY_RECORD')
    return {'status':'EXACT_OWN_PENDING_OR_ACCOUNT_OMITTED_DRAFT_NO_OTHER_WEEK','record_id':state['record_id'],'own_pending_count':len(owned),'writes':0,'certifies':False}

def capture(root,plan,state,token,output,opener):
    root=Path(root).resolve(strict=True);body=owned_projection(root,plan,state);out=Path(output)
    e.need(out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists(),'NEW_PENDING_ACCOUNT_OUTPUT')
    account=original.AccountDiscovery(token,out/'account',opener);first=account.pass_once();split=account.sequence;second=account.pass_once();e.need(typed(original.discovery_signature(first),original.discovery_signature(second)),'PENDING_ACCOUNT_RACE')
    records=out/'RECORDS.json';e.immutable(records,e.raw_json({'records':first}));paths=sorted((out/'account').glob('*_ACCOUNT_GET.json'));e.need(len(paths)==account.sequence,'ALL_PENDING_REAL_PAGE_RECEIPTS')
    value={key:deepcopy(state[key])for key in('record_id','concept_id','creation_receipt','first_owned_draft','first_owned_legacy_draft','last_validation')};value.update(standard=STANDARD,status='COMPLETE_OWN_PENDING_ACCOUNT_CONTINUATION_NOT_PUBLICATION_CLEARANCE',release_week=plan['release_week'],plan_sha256=machine.digest(plan),passes=[[e.binding(p)for p in paths[:split]],[e.binding(p)for p in paths[split:]]],records=e.binding(records),record_count=len(first),own_pending_count=sum(original.identity(r)==state['record_id']for r in first),producer_sha256=source_sha(),writes=0)
    require_pending(value,root=root,plan=plan,state=state);data=e.raw_json(value);e.need(token.encode()not in data,'NO_CREDENTIAL_IN_PENDING_PROOF');p=out/'RESULT.json';e.immutable(p,data);return e.binding(p)
if __name__=='__main__':raise SystemExit('HOLD: explicit purpose-bound owned checkpoint call only')
