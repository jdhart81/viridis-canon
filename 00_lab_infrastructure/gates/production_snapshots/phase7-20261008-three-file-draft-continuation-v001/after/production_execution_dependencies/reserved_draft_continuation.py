"""Closed prediction for the already-reserved own draft23226761.

No HTTP, reserve action, returned-field adoption or new server allow-list.
All DOI projections derive from frozen own CREATE preregistration and the
successful same-ID native reservation; unchanged strict guards check them.
"""
from copy import deepcopy
import hashlib,re,urllib.parse
import draft_reservation as previous
from digest_metadata import check,exact
OWN_ID=previous.OWN_ID
RESERVED_CONTEXT_PINS={
 'reservation_receipt':'cb93e955ec397b48b779854af02fe2f21de8ad64774381beb7e17ee0ccf486ef',
 'reserved_legacy_receipt':'8360fd179d653446830349c4f268edb68a5431f70727bb9f187ad61458bcb18d',
 'reserved_native_receipt':'d92f1fd105e944f0141a54a71b3ffbd59c50de44d6ca7d5d6efb810bf418383d',
 'terminal_hold':'26a5021f4a87c3d56cfc2c0f857a5a84483aa67eccae78df4b8a3c78dc52ad00',
}
def predicted_reserved_pair(before,legacy_before,rid,receipt):
 response,expected,wanted=previous.require_reservation_receipt(receipt,before,legacy_before,rid)
 doi=previous.own_doi(rid);url='https://doi.org/'+doi
 check(not any(k in legacy_before for k in('doi','doi_url'))and 'doi'not in legacy_before['metadata']and 'doi'not in legacy_before['links'],'FROZEN_UNRESERVED_LEGACY_DOI_PROJECTIONS')
 wanted.update(doi=doi,doi_url=url);wanted['metadata']['doi']=doi;wanted['links']['doi']=url
 check('badge'in legacy_before['links'],'FROZEN_INITIAL_BADGE_REQUIRED')
 wanted['links']['badge']='https://zenodo.org/badge/doi/'+urllib.parse.quote(doi,safe='')+'.svg'
 return response,expected,wanted

def require_reserved_context(context,values,before,legacy_before,prepared,sm,preservation):
 check(isinstance(context,dict)and set(context)==set(RESERVED_CONTEXT_PINS),'EXACT_RESERVED_OWN_CONTEXT')
 for key,digest in RESERVED_CONTEXT_PINS.items():check(context[key]['sha256']==digest,'APPROVED_RESERVED_CONTEXT_HASH:'+key)
 rid=OWN_ID;response,expected,wanted=predicted_reserved_pair(before,legacy_before,rid,values['reservation_receipt'])
 legacy=previous.transport_response(values['reserved_legacy_receipt'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid,accept='application/json')
 native=previous.transport_response(values['reserved_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=previous.NATIVE)
 hold=values['terminal_hold'];check(hold.get('status')=='HOLD'and hold.get('phase')=='RESERVE_DOI'and hold.get('writes')==1 and hold.get('recovery_attempts')==1 and hold.get('record_id')==rid and hold.get('doi')is None and hold.get('automatic_retry')is False,'OWN_RESERVED_ONE_ATTEMPT_HOLD')
 kwargs=dict(host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=before,own_operation_record_id=rid,existing_communities=prepared['manifest']['public_metadata'].get('communities'),public_communities=prepared['manifest']['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
 # The same full validator checks native ACK and subsequent saved draft.
 # A response is never substituted into the expected prediction.
 sm.validate_new_version(response,expected,**kwargs)
 sm.validate_new_version(native,expected,**kwargs)
 previous.state.require_private_source(legacy,wanted,native,sm,preservation)
 check(native.get('pids')==expected['pids']and native.get('parent',{}).get('pids')==before['parent']['pids']and native.get('files',{}).get('entries')=={}and native.get('media_files',{}).get('entries')=={},'EXACT_RESERVED_EMPTY_FILES_AND_PIDS')
 return expected,wanted,native,legacy

def operation_id(manifest_sha,week,rid,stage,body):
 previous.own_doi(rid);check(isinstance(body,bytes)and re.fullmatch('[a-f0-9]{64}',manifest_sha)is not None and isinstance(stage,str)and re.fullmatch('[A-Za-z0-9_.-]+',stage)is not None,'CLOSED_RESERVED_CONTINUATION_OPERATION_ID')
 check(stage=='PUBLISH'or stage.startswith('UPLOAD_'),'UPLOAD_OR_PUBLISH_STAGE_ONLY')
 return 'phase7-digest-reserved-continuation:'+week+':'+rid+':'+manifest_sha+':'+stage.encode().hex()+':'+hashlib.sha256(body).hexdigest()
