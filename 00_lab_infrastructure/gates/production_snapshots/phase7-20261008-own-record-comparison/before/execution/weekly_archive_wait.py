"""Approved600s sender-only wait for one exact owned successor ZIP PUT.

Transport69bc, acceptance, receipts and every other120s request stay unchanged.
No retry, body/header diagnostic, credential retrieval or record mutation.
"""
import hashlib,re
from digest_metadata import check,exact
class WeeklyArchiveWait:
    def __init__(self,opener):self.opener=opener;self.profile=None
    @property
    def deadline(self):return self.opener.deadline
    @deadline.setter
    def deadline(self,value):self.opener.deadline=value
    def arm(self,record_id,source_id,creation_receipt,first_legacy_receipt,archive):
        check(isinstance(record_id,str)and re.fullmatch('[1-9][0-9]*',record_id)is not None and isinstance(source_id,str)and source_id!=record_id,'OWN_DISTINCT_SUCCESSOR_RECORD')
        created=creation_receipt.get('response',{});first=first_legacy_receipt.get('response',{})
        check(creation_receipt.get('method')=='POST'and creation_receipt.get('url')in{'https://zenodo.org/api/deposit/depositions/'+source_id+'/actions/newversion','https://zenodo.org/api/deposit/depositions'}and creation_receipt.get('http_status')==201 and creation_receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and str(created.get('id'))==record_id and created.get('state')=='unsubmitted'and created.get('submitted')is False,'GENUINE_OWN_NEWVERSION_WAIT_SCOPE')
        if creation_receipt.get('url')=='https://zenodo.org/api/deposit/depositions':check(created.get('files')==[],'EMPTY_OWN_FIRST_WEEK_DRAFT')
        check(first_legacy_receipt.get('method')=='GET'and first_legacy_receipt.get('url')=='https://zenodo.org/api/deposit/depositions/'+record_id and first_legacy_receipt.get('http_status')==200 and first_legacy_receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and str(first.get('id'))==record_id and first.get('state')=='unsubmitted'and first.get('submitted')is False,'GENUINE_FIRST_OWN_DRAFT_WAIT_SCOPE')
        bucket=created.get('links',{}).get('bucket');check(isinstance(bucket,str)and re.fullmatch('https://zenodo.org/api/files/[0-9a-f-]{36}',bucket)is not None and first.get('links',{}).get('bucket')==bucket,'OWN_INVARIANT_ARCHIVE_BUCKET')
        check(isinstance(archive,dict)and archive.get('name')=='METHODS_NOTES.zip'and type(archive.get('bytes'))is int and archive['bytes']>0 and re.fullmatch('[0-9a-f]{64}',str(archive.get('sha256')))is not None,'EXACT_REVIEWED_ZIP_INVENTORY')
        wanted={'record_id':record_id,'url':bucket+'/METHODS_NOTES.zip','sha256':archive['sha256'],'bytes':archive['bytes']}
        check(self.profile is None or exact(self.profile,wanted),'NO_ARCHIVE_SCOPE_REASSIGNMENT');self.profile=wanted
    def open(self,request,timeout=120):
        check(type(timeout)is int and timeout==120,'UNCHANGED_TRANSPORT_WAIT_DEFAULT')
        method=request.get_method();url=request.full_url
        if method=='PUT'and url.rsplit('/',1)[-1]=='METHODS_NOTES.zip':
            p=self.profile;check(p is not None and url==p['url']and isinstance(request.data,bytes)and len(request.data)==p['bytes']and hashlib.sha256(request.data).hexdigest()==p['sha256'],'EXACT_OWN_SUCCESSOR_FROZEN_ARCHIVE_ONLY')
            return self.opener.open(request,timeout=600)
        return self.opener.open(request,timeout=timeout)
