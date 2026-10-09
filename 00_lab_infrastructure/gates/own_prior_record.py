"""Prior protected content with genuine flags and complete processing logs.

The approved Oct9 rule logs asynchronous processing on any record. Genuine
own chain receipts still exclusively authorize version-state flag changes.
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
    import own_record_comparison as own
    native_audit=own.require_prior_semantics(native,expected_n,representation='NATIVE')
    legacy_audit=own.require_prior_semantics(legacy,expected_l,representation='LEGACY')
    preservation.require_public_metadata(legacy.get('metadata',{}),expected_l.get('metadata',{}))
    # Run the unchanged file guard on protected filename-keyed rows. Full
    # original bodies and ordering remain logged in the two audits.
    preservation.require_file_preservation(own.prior_protected_projection(legacy,representation='LEGACY').get('files'),own.prior_protected_projection(expected_l,representation='LEGACY').get('files'))
    return {'status':'PRIOR_RECORD_PROTECTED_EXCEPT_APPROVED_VERSION_CHAIN_FLAGS','record_id':src,'chain_state':phase,'native_audit':native_audit,'legacy_audit':legacy_audit,'observed_before':{'native':deepcopy(saved_native),'legacy':deepcopy(saved_legacy)},'observed_after':{'native':deepcopy(native),'legacy':deepcopy(legacy)},'certifies':False}
