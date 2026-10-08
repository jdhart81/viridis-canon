"""Closed continuation of one source-bound own draft; no HTTP or allow-list.

The existing strict server validator remains authoritative. This module
predicts the missing, previously sandbox-proven native DOI reservation stage.
It does not admit an omitted public/pre-existing PID or adopt returned fields.
"""
from copy import deepcopy
import datetime as dt,hashlib,json,re
from zoneinfo import ZoneInfo
import first_digest_state as state
from digest_metadata import check,exact

OWN_ID='23226761'
NATIVE='application/vnd.inveniordm.v1+json'
EMPTY_BODY=b'{}'
CONTEXT_PINS={
 'creation_receipt':'42cd70a797b9b1deb10f96e131e5b4ffbb19b3681fefb6a21a206543f485ab1f',
 'initial_legacy_receipt':'d74f1e88801fceab4fdb232cdbb0dca9aed1a52e0ead9421173d503e16eb1a29',
 'initial_native_receipt':'1ee2ddcb4f8750562093a7bf7dc8d05263f909de43b68446dc3745b58eccb36b',
 'terminal_hold':'ebb585667a4202752fd80d8746db8f75f05a2d5beddab43bd7d7fe21c7d95267',
 'api_metadata_payload':('7de637798416a70c21da3823fb428c19a' + '37c068d64f3e0bd75b43d99cb1c87dc'),
}
def own_doi(rid):
 check(state.identifier(rid)==OWN_ID,'APPROVED_OWN_DRAFT_ONLY')
 return '10.5281/zenodo.'+rid
def transport_response(receipt,*,method,url,accept,body=None,http_status=200):
 check(isinstance(receipt,dict)and set(receipt)=={'method','url','request_body_sha256','environment','accept','status','http_status','response_sha256','response'},'CLOSED_TRANSPORT_RECEIPT')
 check(receipt['environment']=='zenodo.org'and receipt['method']==method and receipt['url']==url and receipt['accept']==accept and receipt['http_status']==http_status and receipt['status']=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','OWN_SUCCESSFUL_TRANSPORT')
 check(receipt['request_body_sha256']==(hashlib.sha256(body).hexdigest()if body is not None else None),'ACTUAL_REQUEST_BODY_HASH')
 check(isinstance(receipt['response_sha256'],str)and re.fullmatch('[a-f0-9]{64}',receipt['response_sha256'])is not None and isinstance(receipt['response'],dict),'RAW_RESPONSE_HASH_REQUIRED')
 return deepcopy(receipt['response'])
def require_context(context,values,api_body,original_plan,execution_plan):
 check(isinstance(context,dict)and set(context)==set(CONTEXT_PINS),'EXACT_OWN_CREATION_CONTEXT')
 for key,sha in CONTEXT_PINS.items():check(context[key]['sha256']==sha,'APPROVED_CONTEXT_HASH:'+key)
 check(exact({k:v for k,v in execution_plan.items()if k!='runtime_pins'},{k:v for k,v in original_plan.items()if k!='runtime_pins'}),'ORIGINAL_PLAN_SCIENCE_AND_PAYLOAD_UNCHANGED')
 check(hashlib.sha256(api_body).hexdigest()==context['api_metadata_payload']['sha256'],'ORIGINAL_API_BYTES')
 creation=transport_response(values['creation_receipt'],method='POST',url='https://zenodo.org/api/deposit/depositions',accept='application/json',body=api_body,http_status=201)
 rid=state.identifier(creation.get('id'));own_doi(rid)
 legacy=transport_response(values['initial_legacy_receipt'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid,accept='application/json')
 native=transport_response(values['initial_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE)
 check(exact(creation,legacy),'ORIGINAL_CREATION_PAIR_UNCHANGED')
 check(native.get('id')==rid and native.get('pids')=={}and native.get('parent',{}).get('pids')=={}and native.get('files',{}).get('entries')=={}and native.get('media_files',{}).get('entries')=={},'OWN_FRESH_EMPTY_PID_AND_FILES')
 hold=values['terminal_hold']
 check(hold.get('status')=='HOLD'and hold.get('phase')=='CREATE'and hold.get('writes')==1 and hold.get('record_id')==rid and hold.get('doi')is None and hold.get('automatic_retry')is False,'ORIGINAL_UNPUBLISHED_CREATE_HOLD')
 return creation,legacy,native
def initial_expected(creation,actual,prepared,sm,preservation):
 check(actual.get('pids')=={}and actual.get('parent',{}).get('pids')=={},'NO_PREEXISTING_NATIVE_PID')
 rid=state.identifier(creation.get('id'));doi=own_doi(rid)
 check(creation.get('metadata',{}).get('prereserve_doi')=={'doi':doi,'recid':int(rid)},'EXACT_OWN_LEGACY_PREREGISTRATION')
 expected,wanted=state.initial_expected(creation,actual,prepared['native_metadata'],prepared['source_native'],prepared['api_payload'],sm,preservation,source_legacy=prepared['source_legacy'])
 # Exact lifecycle prediction, restricted to the frozen own CREATE context.
 # No existing PID is removed; before native reservation this set is empty.
 expected['pids']={}
 return expected,wanted
def reserved_expected(before,legacy_before,rid,body=EMPTY_BODY):
 doi=own_doi(rid)
 check(body==EMPTY_BODY,'EXACT_EMPTY_NATIVE_RESERVATION_BODY')
 check(before.get('id')==rid and before.get('pids')=={}and before.get('parent',{}).get('pids')=={}and before.get('status')=='draft'and before.get('is_draft')is True and before.get('is_published')is False,'OWN_EMPTY_UNPUBLISHED_RESERVATION_BOUNDARY')
 check(legacy_before.get('metadata',{}).get('prereserve_doi')=={'doi':doi,'recid':int(rid)},'RESERVATION_EQUALS_LEGACY_PREREGISTRATION')
 expected=deepcopy(before);expected['pids']={'doi':{'identifier':doi,'provider':'datacite','client':'datacite'}}
 wanted=deepcopy(legacy_before)
 # Private legacy badge is a deterministic own-DOI URL after native reserve.
 if 'badge'in wanted.get('links',{}):
  check(wanted['links']['badge']=='https://zenodo.org/badge/doi/.svg','FROZEN_BEFORE_RESERVE_BADGE')
  wanted['links']['badge']='https://zenodo.org/badge/doi/'+doi+'.svg'
 return expected,wanted
def require_reservation_receipt(receipt,before,legacy_before,rid,body=EMPTY_BODY):
 expected,wanted=reserved_expected(before,legacy_before,rid,body)
 response=transport_response(receipt,method='POST',url='https://zenodo.org/api/records/'+rid+'/draft/pids/doi',accept=NATIVE,body=body,http_status=201)
 check(response.get('id')==rid and exact(response.get('pids'),expected['pids'])and response.get('parent',{}).get('id')==before['parent']['id']and exact(response.get('parent',{}).get('pids'),before['parent']['pids']),'EXACT_SAME_DRAFT_MANAGED_DOI_MINT')
 return response,expected,wanted
def require_account_rows(first,second,week,creation,native):
 from readonly_account import identity,discovery_signature
 check(isinstance(first,list)and isinstance(second,list)and discovery_signature(first)==discovery_signature(second),'COMPLETE_STABLE_ACCOUNT_REQUIRED')
 ids=[identity(row)for row in first];check(len(set(ids))==len(ids),'UNIQUE_ACCOUNT_IDENTITIES')
 rid=state.identifier(creation.get('id'));own_doi(rid)
 matched=[r for r in first if r['metadata']['title']=='Viridis Methods Digest — '+week]
 check(len(matched)==1 and identity(matched[0])==rid,'EXACT_ANCHORED_WEEKLY_DRAFT_ONLY')
 own=matched[0]
 check(exact(discovery_signature([own]),discovery_signature([native]))and own.get('is_draft')is True and own.get('is_published')is False and own.get('status')=='draft','OWN_ACCOUNT_DRAFT_PROJECTION_UNCHANGED')
 return {'status':'COMPLETE_STABLE_ACCOUNT_EXACT_ANCHORED_DRAFT','record_count':len(first),'record_id':rid,'double_passes':2,'writes':0}
def complete_account(account,week,creation,native):
 first=account.pass_once();second=account.pass_once();result=require_account_rows(first,second,week,creation,native)
 from readonly_account import immutable,raw_json
 immutable(account.out/'RECORDS.json',raw_json(first));immutable(account.out/'RESULT.json',raw_json(result));return result
def operation_id(manifest_sha,week,rid,stage,body):
 own_doi(rid);check(isinstance(body,bytes)and re.fullmatch('[a-f0-9]{64}',manifest_sha)is not None and isinstance(stage,str)and re.fullmatch('[A-Za-z0-9_.-]+',stage)is not None,'CLOSED_RECOVERY_OPERATION_ID')
 return 'phase7-digest-recovery:'+week+':'+rid+':'+manifest_sha+':'+stage.encode().hex()+':'+hashlib.sha256(body).hexdigest()
def daily_diagnostics(events,at_utc):
 """Count already source-validated events for reporting, never grant a slot."""
 now=dt.datetime.fromisoformat(at_utc.replace('Z','+00:00'));check(now.tzinfo is not None,'DIAGNOSTIC_TIMEZONE')
 day=now.astimezone(ZoneInfo('America/New_York')).date()
 return {'date_new_york':str(day),'used':sum(dt.datetime.fromisoformat(e['at_utc'].replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York')).date()==day for e in events)}
def require_unspent_operation(events,operation):
 check(not any(e.get('operation_id')==operation for e in events),'RECOVERY_OPERATION_ALREADY_SPENT')
