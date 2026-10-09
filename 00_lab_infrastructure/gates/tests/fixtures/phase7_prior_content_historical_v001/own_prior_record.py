"""Prior-record equality, with only approved genuine version-chain flags.

Own housekeeping is irrelevant here.  Existing records remain exact; the
genuine own creation/publish receipts permit only the established flag state.
The latest own-record authority requires complete prior equality, including
ordered file arrays; the earlier own-file reorder rule is not used on priors.
"""
from copy import deepcopy
import hashlib, json

class PriorHold(ValueError):pass
def need(value,reason):
    if not value:raise PriorHold('HOLD_PRIOR_'+reason)
def exact(a,b):return json.dumps(a,sort_keys=True,allow_nan=False,separators=(',',':'))==json.dumps(b,sort_keys=True,allow_nan=False,separators=(',',':'))
def receipt(value,method,url):
    need(isinstance(value,dict)and value.get('environment')=='zenodo.org'and value.get('method')==method and value.get('url')==url and value.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and type(value.get('http_status'))is int and 200<=value['http_status']<300 and isinstance(value.get('response'),dict),'GENUINE_OWN_CHAIN_RECEIPT')
    return value['response']
def require_pair(legacy,native,saved_legacy,saved_native,*,creation=None,publish=None,preservation):
    src=saved_native.get('id');parent=saved_native.get('parent',{}).get('id')
    need(isinstance(src,str)and str(saved_legacy.get('id'))==src and str(saved_legacy.get('conceptrecid'))==parent and native.get('id')==src and native.get('parent',{}).get('id')==parent,'IDENTITY')
    expected_n=deepcopy(saved_native);expected_l=deepcopy(saved_legacy);phase='UNCHANGED'
    if creation is not None:
        ack=receipt(creation,'POST','https://zenodo.org/api/deposit/depositions/'+src+'/actions/newversion')
        rid=str(ack.get('id'));need(rid not in{src,parent}and str(ack.get('conceptrecid'))==parent and creation.get('http_status')==201 and creation.get('request_body_sha256')==hashlib.sha256(b'{}').hexdigest(),'OWN_DISTINCT_SAME_PARENT_CREATION')
        versions=expected_n.get('versions');need(isinstance(versions,dict)and versions.get('is_latest')is True and versions.get('is_latest_draft')is True and type(versions.get('index'))is int,'INITIAL_LATEST_FLAGS')
        versions['is_latest_draft']=False;phase='OWN_CREATED'
        if publish is not None:
            ack=receipt(publish,'POST','https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish')
            need(str(ack.get('id'))==rid and str(ack.get('conceptrecid'))==parent and ack.get('doi')=='10.5281/zenodo.'+rid,'OWN_TERMINAL_PUBLISH')
            versions['is_latest']=False;phase='OWN_PUBLISHED'
            rows=expected_l.get('metadata',{}).get('relations',{}).get('version')
            need(isinstance(rows,list)and len(rows)==1 and rows[0].get('is_last')is True,'INITIAL_LEGACY_LAST_FLAG')
            rows[0]['is_last']=False
    else:need(publish is None,'NO_PUBLISH_WITHOUT_OWN_CREATION')
    need(exact(native,expected_n),'NATIVE_BYTES_OUTSIDE_APPROVED_FLAGS_CHANGED')
    preservation.require_public_metadata(legacy.get('metadata',{}),expected_l.get('metadata',{}))
    preservation.require_file_preservation(legacy.get('files'),expected_l.get('files'))
    need(exact(legacy,expected_l),'LEGACY_BYTES_OUTSIDE_APPROVED_FLAGS_CHANGED')
    return {'status':'PRIOR_RECORD_EXACT_EXCEPT_APPROVED_VERSION_CHAIN_FLAGS','record_id':src,'chain_state':phase,'certifies':False}
