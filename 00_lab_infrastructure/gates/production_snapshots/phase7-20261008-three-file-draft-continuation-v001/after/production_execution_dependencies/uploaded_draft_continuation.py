"""Source-bound continuation after two exact own manuscript uploads.

No HTTP, re-upload, CREATE, reserve, metadata PUT or new allow-list.
Full native validation precedes only the exact legacy thumbnail projection.
"""
from copy import deepcopy
import hashlib,re,urllib.parse
import draft_reservation as previous
import legacy_preview_aliases as aliases
from digest_metadata import check,exact
OWN_ID=previous.OWN_ID
UPLOADED_CONTEXT_PINS={'tex_upload_receipt': 'e246005e6ac1cb9321d23b8dc9c2bb1a0cfd9e079d604d5202f455f375dabc08', 'tex_legacy_receipt': '7b9c8d7e4ce595dd4efa525c7e0bd543b202034af77d50703391fcb9bab886f7', 'tex_native_receipt': 'c7b6bdf0a0f4b0ce3fa7a4adf089d16f60019b7c8f44ac2bfe51909bd07f0c25', 'pdf_upload_receipt': '6ea9b01ec11180505741fae0dad6d88e98c50c19593809b673629c60d2ff6fce', 'pdf_legacy_receipt': 'e77c056b5ca47ae5bb98687f5ccae5b23564858f88b4364ac3436d8d1beba978', 'pdf_native_receipt': 'eb7b8e06b71492b70c6a2d465589c0df283c862ef9a6c3499fef363425fab789', 'terminal_hold': '793bb411e52501c927e8be770b4abc8d678f95fe447bc0104d9b0c2805149059'}

def require_uploaded_context(context,values,before,legacy_before,prepared,sm,preservation,approved_inventory_evidence,lineage_evidence):
 check(isinstance(context,dict)and set(context)==set(UPLOADED_CONTEXT_PINS),'EXACT_UPLOADED_OWN_CONTEXT')
 for key,digest in UPLOADED_CONTEXT_PINS.items():check(context[key]['sha256']==digest,'APPROVED_UPLOADED_CONTEXT_HASH:'+key)
 inventory,inventory_log=sm._preview_inventory(approved_inventory_evidence);check(set(inventory)=={'paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'},'EXACT_SIX_APPROVED_UPLOADED_INVENTORY')
 rid=OWN_ID;check(before.get('id')==rid and before.get('files',{}).get('entries')=={}and legacy_before.get('files')==[],'SAVED_OWN_RESERVED_EMPTY_BASELINE')
 hold=values['terminal_hold'];check(hold.get('status')=='HOLD'and hold.get('phase')=='UPLOAD_paper.pdf'and type(hold.get('writes'))is int and hold['writes']==2 and type(hold.get('continuation_attempts'))is int and hold['continuation_attempts']==2 and hold.get('record_id')==rid and hold.get('doi')is None and hold.get('automatic_retry')is False,'OWN_TWO_UPLOAD_ATTEMPT_HOLD')
 def ev(binding):return {'receipt_path':binding['path'],'receipt_sha256':binding['sha256'],'transport_contract_sha256':sm.transport_contract_sha256()}
 reads=[];uploads=[];current=deepcopy(before);wanted=deepcopy(legacy_before);audits=[]
 for prefix,name in(('tex','paper.tex'),('pdf','paper.pdf')):
  target=inventory[name];receipt=values[prefix+'_upload_receipt'];bucket=legacy_before['links']['bucket']
  # Body is already immutable and hash-bound; no new upload is performed.
  check(receipt.get('request_body_sha256')==target['sha256'],'SAVED_EXACT_OWN_UPLOAD_BODY_HASH')
  check(set(receipt)=={'method','url','request_body_sha256','environment','accept','status','http_status','response_sha256','response'}and receipt['method']=='PUT'and receipt['url']==bucket+'/'+urllib.parse.quote(name,safe='')and receipt['environment']=='zenodo.org'and receipt['accept']=='application/json'and receipt['status']=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and receipt['http_status']==201 and re.fullmatch('[a-f0-9]{64}',receipt['response_sha256'])is not None,'SAVED_SUCCESSFUL_OWN_UPLOAD')
  response=deepcopy(receipt['response']);legacy=previous.transport_response(values[prefix+'_legacy_receipt'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid,accept='application/json');native=previous.transport_response(values[prefix+'_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=previous.NATIVE)
  rows=legacy.get('files');check(isinstance(rows,list),'SAVED_UPLOADED_LEGACY_FILES');matches=[row for row in rows if row.get('filename')==name];check(len(matches)==1,'EXACT_SAVED_UPLOADED_FILE_ROW')
  approved={'name':name,'size':target['size'],'md5':target['checksum'][4:]};expected=deepcopy(current);expected['files']['entries'][name]=previous.state.file_from_upload(matches[0],response,approved,rid);previous.state.refresh_totals(expected);predicted=deepcopy(wanted);predicted['files'].append(matches[0])
  reads.extend([ev(context[prefix+'_legacy_receipt']),ev(context[prefix+'_native_receipt'])]);uploads.append(ev(context[prefix+'_upload_receipt']))
  preview={'own_record_id':rid,'approved_inventory_evidence':approved_inventory_evidence,'lineage_evidence':ev(lineage_evidence),'source_readback_evidence':reads,'delete_evidence':[],'upload_evidence':uploads,'publish_evidence':None}
  audit=sm.validate_new_version(native,expected,host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=expected,own_operation_record_id=rid,derived_preview_context=preview,existing_communities=prepared['manifest']['public_metadata'].get('communities'),public_communities=prepared['manifest']['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
  projected=aliases.project(native,predicted,audit,sm);previous.state.require_private_source(legacy,projected,native,sm,preservation)
  current,wanted=deepcopy(native),deepcopy(legacy);audits.append({'file':name,'native_audit':audit,'private_guard_pass':True,'upload_receipt':context[prefix+'_upload_receipt']})
 check(set(current['files']['entries'])=={'paper.tex','paper.pdf'}and len(wanted['files'])==2,'ONLY_SAVED_TWO_MANUSCRIPT_FILES')
 return current,wanted,audits

def operation_id(manifest_sha,week,rid,stage,body):
 previous.own_doi(rid);check(isinstance(body,bytes)and re.fullmatch('[a-f0-9]{64}',manifest_sha)is not None and isinstance(stage,str)and re.fullmatch('[A-Za-z0-9_.-]+',stage)is not None,'CLOSED_UPLOADED_CONTINUATION_OPERATION_ID')
 check(stage=='PUBLISH'or stage in{'UPLOAD_metadata.json','UPLOAD_METHODS_NOTES.zip','UPLOAD_DIGEST_MANIFEST.json','UPLOAD_PUBLICATION_BINDING.json'},'REMAINING_EVIDENCE_UPLOAD_OR_PUBLISH_ONLY')
 return 'phase7-digest-uploaded-continuation:'+week+':'+rid+':'+manifest_sha+':'+stage.encode().hex()+':'+hashlib.sha256(body).hexdigest()
