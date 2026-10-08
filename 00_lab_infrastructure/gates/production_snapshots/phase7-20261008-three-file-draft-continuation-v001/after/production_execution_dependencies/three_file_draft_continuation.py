"""Closed source-bound continuation of exactly three uploaded own files.

Saved observations do not grant acceptance: the unchanged full native/private
consumers and exact downloaded bytes are rerun. The uncertain PUT stays charged
and is never represented as HTTP success. No HTTP or new allow-list is here.
"""
from copy import deepcopy
import hashlib,json,re,urllib.parse
from pathlib import Path
import draft_reservation as previous
import legacy_preview_aliases as aliases
from digest_metadata import check,exact
from first_digest_publisher import bound,read_regular
OWN_ID=previous.OWN_ID
THREE_CONTEXT_PINS={'metadata_upload_receipt': '5f323966431c6ebc4e9a88bd97ce3a88ebbccde99090d5bc49849ee00b005a24', 'metadata_legacy_receipt': '02c738b6e8bad7b2b551a6576b871c423774802391e4de8ce313ca875af5d22b', 'metadata_native_receipt': '4e53ada3018a118eede41b7c375b360744282455032ac9b3e8e09d25498c8120', 'uncertain_archive_receipt': '784d73f3c876fe8a84ca8bb7360b0e48208b6a9cabbc2e9a92ed35516942e904', 'terminal_hold': 'cfe832914ed73cd83baadf6413e7e7a1b298d2076b98cb3845f5a22cf5585caa', 'absence_legacy_receipt': '02c738b6e8bad7b2b551a6576b871c423774802391e4de8ce313ca875af5d22b', 'absence_native_receipt': '4e53ada3018a118eede41b7c375b360744282455032ac9b3e8e09d25498c8120', 'adjudication_result': 'ed7ca424ff339686af2b729c12873642ea34baa7e07391cc52342b712e20fe80', 'adjudication_diff': '32a31e031a7d332cd88c015e2d761ee5dd6cf2a09157ec4261a6d27e3fdbe625'}
THREE_CONTEXT_PATHS={'metadata_upload_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-methods-digest-publication-v005/transport/007_PUT.json', 'metadata_legacy_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-methods-digest-publication-v005/transport/012_GET.json', 'metadata_native_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-methods-digest-publication-v005/transport/013_GET.json', 'uncertain_archive_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-methods-digest-publication-v005/transport/014_PUT.json', 'terminal_hold': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-methods-digest-publication-v005/RESULT.json', 'absence_legacy_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-digest-v005-archive-readonly-adjudication-v001/transport/001_GET.json', 'absence_native_receipt': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-digest-v005-archive-readonly-adjudication-v001/transport/002_GET.json', 'adjudication_result': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-digest-v005-archive-readonly-adjudication-v001/RESULT.json', 'adjudication_diff': 'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-digest-v005-archive-readonly-adjudication-v001/FULL_PAIR_DIFF.json'}
ADJUDICATOR_SHA256='cd8f8457b72a633126831e4be0fe367af59c2801d48b9e668e3f3f3f7d8e35fa'
KNOWN=('paper.tex','paper.pdf','metadata.json')
REMAINING=('METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json')
INVENTORY_SHA256='598c35f86bb1a17104230d940f70814aca8743ea62f97210dccf112af2c23e26'
PRIOR_PLAN_SHA256='2f67aa3c0d7e4d606ef4c01513dc827b13acb528533810c377919ed1fb43bcac'

def require_three_file_context(root,context,values,before,legacy_before,prepared,sm,preservation,approved_inventory_evidence,lineage_evidence):
 check(isinstance(context,dict)and set(context)==set(THREE_CONTEXT_PINS)and set(values)==set(context),'EXACT_THREE_FILE_SOURCE_CONTEXT')
 for key,digest in THREE_CONTEXT_PINS.items():
  check(isinstance(context[key],dict)and set(context[key])=={'path','sha256'}and context[key]['sha256']==digest,'APPROVED_THREE_FILE_CONTEXT_HASH:'+key)
  check(context[key]['path']==str(root/THREE_CONTEXT_PATHS[key]),'EXACT_POSTFAILURE_SOURCE_PATH:'+key)
  check(exact(bound(root,context[key])[1],values[key]),'BOUND_CONTEXT_VALUE:'+key)
 check(approved_inventory_evidence['sha256']==INVENTORY_SHA256,'ORIGINAL_SIX_FILE_INVENTORY')
 inventory,_=sm._preview_inventory(approved_inventory_evidence)
 check(set(inventory)==set(KNOWN+REMAINING),'EXACT_SIX_FROZEN_FILES')
 check(before.get('id')==OWN_ID and set(before['files']['entries'])==set(KNOWN[:2])and {f['filename']for f in legacy_before['files']}==set(KNOWN[:2]),'EXACT_TWO_FILE_PREDECESSOR')
 rid=OWN_ID;bucket=legacy_before['links']['bucket'];target=inventory['metadata.json'];receipt=values['metadata_upload_receipt']
 check(set(receipt)=={'method','url','request_body_sha256','environment','accept','status','http_status','response_sha256','response'}and receipt.get('method')=='PUT'and receipt.get('url')==bucket+'/metadata.json'and receipt.get('environment')=='zenodo.org'and receipt.get('accept')=='application/json'and receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and type(receipt.get('http_status'))is int and receipt['http_status']==201 and receipt.get('request_body_sha256')==target['sha256']and re.fullmatch('[a-f0-9]{64}',receipt.get('response_sha256',''))is not None,'GENUINE_SAVED_METADATA_201')
 legacy=previous.transport_response(values['metadata_legacy_receipt'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid,accept='application/json')
 native=previous.transport_response(values['metadata_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=previous.NATIVE)
 matches=[f for f in legacy['files']if f['filename']=='metadata.json'];check(len(matches)==1,'ONE_GENUINE_METADATA_ROW')
 expected=deepcopy(before);expected['files']['entries']['metadata.json']=previous.state.file_from_upload(matches[0],receipt['response'],{'name':'metadata.json','size':target['size'],'md5':target['checksum'][4:]},rid);previous.state.refresh_totals(expected);wanted=deepcopy(legacy_before);wanted['files'].append(matches[0])
 def ev(binding):return {'receipt_path':binding['path'],'receipt_sha256':binding['sha256'],'transport_contract_sha256':sm.transport_contract_sha256()}
 preview={'own_record_id':rid,'approved_inventory_evidence':approved_inventory_evidence,'lineage_evidence':ev(lineage_evidence),'source_readback_evidence':[ev(context[k])for k in('metadata_legacy_receipt','metadata_native_receipt','absence_legacy_receipt','absence_native_receipt')],'delete_evidence':[],'upload_evidence':[ev(context['metadata_upload_receipt'])],'publish_evidence':None}
 # Preserve original paper upload evidence for PDF preview provenance. These
 # are explicit source-bound descendants of the frozen prior plan, never ACKs.
 _,prior=bound(root,prepared['three_file_prior_uploaded_plan'])
 for key in('tex_upload_receipt','pdf_upload_receipt'):
  item=prior['uploaded_context'][key];bound(root,item);preview['upload_evidence'].append(ev(item))
 for key in('tex_legacy_receipt','tex_native_receipt','pdf_legacy_receipt','pdf_native_receipt'):
  item=prior['uploaded_context'][key];bound(root,item);preview['source_readback_evidence'].append(ev(item))
 audits=[]
 def validate(actual,private,predicted,private_wanted,label):
  check(set(actual['files']['entries'])==set(KNOWN)and len(private['files'])==3 and {f['filename']for f in private['files']}==set(KNOWN),'EXACT_THREE_NO_ARCHIVE_OR_OTHER_MAIN_FILES')
  audit=sm.validate_new_version(actual,predicted,host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=predicted,own_operation_record_id=rid,derived_preview_context=preview,existing_communities=prepared['manifest']['public_metadata'].get('communities'),public_communities=prepared['manifest']['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
  projected=aliases.project(actual,private_wanted,audit,sm);previous.state.require_private_source(private,projected,actual,sm,preservation);audits.append({'stage':label,'native_audit':audit,'private_guard_pass':True})
 validate(native,legacy,expected,wanted,'SAVED_METADATA_201')
 hold=values['terminal_hold'];check(hold.get('status')=='HOLD'and hold.get('phase')=='UPLOAD_METHODS_NOTES.zip'and type(hold.get('writes'))is int and hold['writes']==2 and type(hold.get('continuation_attempts'))is int and hold['continuation_attempts']==2 and hold.get('record_id')==rid and hold.get('doi')is None and hold.get('automatic_retry')is False and hold.get('failure')=='TransportHold: HOLD_TRANSPORT_UNCERTAIN_NO_RETRY:URLError','OWN_METADATA_THEN_UNCERTAIN_ARCHIVE_HOLD')
 uncertain=values['uncertain_archive_receipt'];check(set(uncertain)=={'method','url','request_body_sha256','environment','accept','status','error_type'}and uncertain['method']=='PUT'and uncertain['url']==bucket+'/METHODS_NOTES.zip'and uncertain['request_body_sha256']==inventory['METHODS_NOTES.zip']['sha256']and uncertain['environment']=='zenodo.org'and uncertain['accept']=='application/json'and uncertain['status']=='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'and uncertain['error_type']=='URLError','UNCERTAIN_ARCHIVE_IS_NOT_201')
 absent_legacy=previous.transport_response(values['absence_legacy_receipt'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid,accept='application/json')
 absent_native=previous.transport_response(values['absence_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=previous.NATIVE)
 check(exact(absent_legacy,legacy)and exact(absent_native,native),'ACTUAL_ABSENCE_PAIR_IDENTICAL_TO_LAST_SUCCESSFUL_STATE')
 validate(absent_native,absent_legacy,native,legacy,'ACTUAL_ABSENCE_PAIR')
 diff=values['adjudication_diff'];check(diff=={'standard':'READ_ONLY_PATH_DIFFERENCES_NOT_ACCEPTANCE_1','certifies':False,'legacy':[],'native':[]},'ZERO_ACTUAL_ABSENCE_PATH_DIFFERENCES')
 result=values['adjudication_result'];check(set(result)=={'standard','status','record_id','published','mutations','acceptance_evidence','certifies','archive_observation','present_files','absent_files','downloads','driver_sha256','credentials_recorded','automatic_retry'}and result['standard']=='VRS_PHASE7_UNCERTAIN_UPLOAD_READ_ONLY_OBSERVATIONS_1'and result['status']=='READ_ONLY_OBSERVATIONS_NOT_ACCEPTANCE'and result['record_id']==rid and result['driver_sha256']==ADJUDICATOR_SHA256 and result['published']is False and type(result['mutations'])is int and result['mutations']==0 and result['acceptance_evidence']is False and result['certifies']is False and result['credentials_recorded']is False and result['automatic_retry']is False and result['archive_observation']=='ABSENT_FROM_BOTH_INVENTORIES_OBSERVED_ONLY'and result['present_files']==list(KNOWN)and result['absent_files']==list(REMAINING),'ACTUAL_READONLY_ABSENT_ADJUDICATION')
 check(isinstance(result['downloads'],list)and len(result['downloads'])==3 and [r.get('filename')for r in result['downloads']]==list(KNOWN),'ALL_THREE_DOWNLOAD_RECEIPTS')
 for row in result['downloads']:
  check(set(row)=={'filename','download','get_receipt','md5','size'},'CLOSED_DOWNLOADED_ROW');name=row['filename'];check(isinstance(row['download'],dict)and set(row['download'])=={'path','sha256'},'CLOSED_DOWNLOAD_BINDING');file_path=Path(row['download']['path']);check(file_path.is_absolute()and file_path.resolve(strict=True).is_relative_to(root),'DOWNLOAD_CONTAINMENT');receipt_path,get=bound(root,row['get_receipt']);data=read_regular(file_path);target=inventory[name]
  check(row['download']['sha256']==target['sha256']and hashlib.sha256(data).hexdigest()==target['sha256']and type(row['size'])is int and len(data)==row['size']==target['size']and hashlib.md5(data).hexdigest()==row['md5']==target['checksum'][4:],'ACTUAL_ALL_THREE_DOWNLOADED_BYTES')
  check(get=={'standard':'VRS-PHASE7-EXACT-FILE-GET-1','status':'EXACT_BYTES_PASS','authenticated':True,'method':'GET','url':'https://zenodo.org/api/records/'+rid+'/draft/files/'+urllib.parse.quote(name,safe='')+'/content','filename':name,'bytes':len(data),'sha256':target['sha256'],'md5':row['md5'],'path':str(file_path)},'GENUINE_OWN_DOWNLOADED_GET')
 return deepcopy(absent_native),deepcopy(absent_legacy),audits

def operation_id(manifest_sha,week,rid,stage,body,context):
 previous.own_doi(rid);check(stage=='PUBLISH'or stage in{'UPLOAD_METHODS_NOTES.zip','UPLOAD_DIGEST_MANIFEST.json','UPLOAD_PUBLICATION_BINDING.json'},'ONLY_THREE_REMAINING_UPLOADS_OR_PUBLISH')
 check(isinstance(body,bytes)and re.fullmatch('[a-f0-9]{64}',manifest_sha)is not None and set(context)==set(THREE_CONTEXT_PINS),'SOURCE_BOUND_THREE_FILE_OPERATION')
 for key,value in context.items():check(value['sha256']==THREE_CONTEXT_PINS[key],'SOURCE_BOUND_NONCE_CONTEXT:'+key)
 material={'manifest_sha256':manifest_sha,'context':context,'stage':stage,'body_sha256':hashlib.sha256(body).hexdigest()}
 nonce=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return 'phase7-digest-three-file-continuation:'+week+':'+rid+':'+nonce


def require_archive_retry_history(root,events,context,*,new_archive_attempts=0):
 """Count actual source-bound same-archive attempts, never a summary's flag."""
 check(type(new_archive_attempts)is int and new_archive_attempts in{0,1},'CLOSED_SINGLE_SCOPED_RETRY_STAGE')
 _,old=bound(root,context['uncertain_archive_receipt']);matched=[]
 for event in events:
  _,receipt=bound(root,event['receipt_binding'])
  if receipt.get('method')=='PUT'and receipt.get('url')==old['url']and receipt.get('request_body_sha256')==old['request_body_sha256']:
   matched.append(event['receipt_binding'])
 check(context['uncertain_archive_receipt']in matched and len(matched)==1+new_archive_attempts,'ONLY_ORIGINAL_UNCERTAINTY_PLUS_ONE_SCOPED_RETRY')
 # Reserved request leaves also count if a transport hasn't completed. No
 # fourth attempt can ever be admitted by this immutable first-retry route.
 return {'status':'SOURCE_BOUND_ARCHIVE_RETRY_COUNT_PASS','attempts':len(matched),'retry_budget_maximum':2,'automatic_retry':False}
