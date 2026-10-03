"""Explicitly authorized sandbox-only transaction regression, never production.

No production credential, endpoint or publisher is used. A configured sandbox
credential is consumed only in memory and is never written to receipts.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from zenodo_write_plan import amendment,deposition_projection

ORIGIN='https://sandbox.zenodo.org'


def checked_url(url):
    parsed=urlsplit(url)
    if (parsed.scheme!='https' or parsed.netloc!='sandbox.zenodo.org'
            or not parsed.path.startswith('/api/') or parsed.query or parsed.fragment
            or parsed.username or parsed.password):
        raise ValueError('refused non-sandbox or unbound API endpoint')
    return url


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('API redirect refused')


class SandboxClient:
    def __init__(self):
        token=os.environ.get('ZENODO_SANDBOX_ACCESS_TOKEN')
        if not token:raise ValueError('sandbox-specific credential unavailable')
        self._token=token;self.opener=urllib.request.build_opener(NoRedirect());self.calls=[]
    def request(self,method,url,payload=None,data=None):
        checked_url(url)
        if method not in ('GET','POST','PUT'):raise ValueError('unsupported sandbox method')
        headers={'Authorization':'Bearer '+self._token,'User-Agent':'Viridis-sandbox-preservation-regression/1.0'}
        body=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else data
        if payload is not None:headers['Content-Type']='application/json'
        request=urllib.request.Request(url,data=body,headers=headers,method=method)
        try:
            with self.opener.open(request,timeout=40) as response:
                content=response.read();status=response.status
        except urllib.error.HTTPError as exc:
            # Do not dump response bodies, headers, token or exception URLs.
            self.calls.append({'method':method,'url':url,'status':exc.code});raise ValueError('sandbox HTTP error '+str(exc.code)) from None
        self.calls.append({'method':method,'url':url,'status':status,'body_sha256':hashlib.sha256(content).hexdigest()})
        return json.loads(content) if content else {}


def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n')


def assert_amendment_readback(before,after,description,keywords):
    for k,v in before['metadata'].items():
        if k not in ('description','keywords') and after['metadata'].get(k)!=v:
            raise ValueError('sandbox protected metadata changed: '+k)
    if after['metadata']['description']!=description or after['metadata']['keywords']!=keywords:
        raise ValueError('sandbox description/keyword readback mismatch')
    if before['files']!=after['files']:
        # Stable identity checks below ignore version timestamps/links only.
        stable=lambda r:[(f.get('key'),f.get('checksum'),f.get('size')) for f in r['files']]
        if stable(before)!=stable(after):raise ValueError('sandbox file identity changed')


def run(before_path,out,confirm):
    if confirm!='sandbox.zenodo.org':raise ValueError('explicit sandbox confirmation required')
    out.mkdir(parents=True,exist_ok=False);receipt={'status':'HOLD','production_writes':0,'sandbox_writes':0,'tests_executed':False,'calls':[]};client=None
    try:
        client=SandboxClient();production=json.loads(before_path.read_text());seed=copy.deepcopy(production);seed.pop('doi',None);seed.pop('relations',None)
        projected,changes,holds=deposition_projection(seed)
        if holds:raise ValueError('fixture contains unresolved deposition mapping')
        # Community requests are not silently dropped or redirected to production.
        seed_payload=projected
        write(out/'seed_payload.json',seed_payload)
        draft=client.request('POST',ORIGIN+'/api/deposit/depositions',payload={});rid=str(draft['id']);receipt['initial_deposition_id']=rid;write(out/'created_identity.json',{'id':draft['id'],'conceptrecid':draft.get('conceptrecid')})
        bucket=checked_url(draft['links']['bucket']);content=b'Viridis sandbox-only metadata preservation test. No research certification or production release.\n'
        client.request('PUT',bucket+'/SANDBOX_TEST_ONLY.txt',data=content)
        client.request('PUT',ORIGIN+'/api/deposit/depositions/'+rid,payload=seed_payload)
        client.request('POST',ORIGIN+'/api/deposit/depositions/'+rid+'/actions/publish',payload={})
        before=client.request('GET',ORIGIN+'/api/records/'+rid);write(out/'before_amendment_record.json',before)
        if before['metadata']['title']!=production['title']:raise ValueError('fixture title differs')
        if not before['metadata']['doi'].startswith('10.5072/'):raise ValueError('test DOI not sandbox assigned')
        # Preserve the actual authenticated deposition schema: change two fields only.
        desired=amendment(before['metadata']);dep=client.request('GET',ORIGIN+'/api/deposit/depositions/'+rid);actual=copy.deepcopy(dep['metadata']);actual['description']=desired['description'];actual['keywords']=desired['keywords'];payload={'metadata':actual};write(out/'amendment_payload.json',payload)
        client.request('POST',ORIGIN+'/api/deposit/depositions/'+rid+'/actions/edit',payload={})
        client.request('PUT',ORIGIN+'/api/deposit/depositions/'+rid,payload=payload)
        client.request('POST',ORIGIN+'/api/deposit/depositions/'+rid+'/actions/publish',payload={})
        amended=client.request('GET',ORIGIN+'/api/records/'+rid);write(out/'amendment_readback.json',amended);assert_amendment_readback(before,amended,desired['description'],desired['keywords'])
        response=client.request('POST',ORIGIN+'/api/deposit/depositions/'+rid+'/actions/newversion',payload={});newurl=checked_url(response['links']['latest_draft']);new=client.request('GET',newurl);newid=str(new['id']);receipt['new_version_deposition_id']=newid
        if newid==rid:raise ValueError('new-version identity was not advanced')
        newmetadata=copy.deepcopy(new['metadata']);newmetadata['title']=production['title'];newpayload={'metadata':newmetadata};write(out/'newversion_payload.json',newpayload)
        client.request('PUT',ORIGIN+'/api/deposit/depositions/'+newid,payload=newpayload)
        client.request('POST',ORIGIN+'/api/deposit/depositions/'+newid+'/actions/publish',payload={})
        newer=client.request('GET',ORIGIN+'/api/records/'+newid);write(out/'newversion_readback.json',newer);original=client.request('GET',ORIGIN+'/api/records/'+rid);write(out/'original_after_newversion.json',original)
        if newer['metadata']['title']!=production['title'] or original['metadata']['title']!=production['title']:raise ValueError('new-version title changed')
        if original['metadata']['doi']!=before['metadata']['doi']:raise ValueError('original DOI changed')
        if newer['metadata']['doi']==original['metadata']['doi'] or not newer['metadata']['doi'].startswith('10.5072/'):raise ValueError('new-version DOI identity failed')
        if newer['conceptrecid']!=original['conceptrecid']:raise ValueError('concept lineage changed')
        if newer['metadata'].get('related_identifiers')!=amended['metadata'].get('related_identifiers'):raise ValueError('bibliographic relations changed')
        if not newer['metadata'].get('relations',{}).get('version'):raise ValueError('version graph missing')
        receipt.update(status='PASS_SANDBOX_ONLY',tests_executed=True,title_preserved=True,amendment_doi_preserved=True,amendment_all_public_fields_preserved=True,new_version_doi_distinct=True,concept_lineage_preserved=True,related_identifiers_preserved=True,initial_doi=original['metadata']['doi'],new_version_doi=newer['metadata']['doi'])
    except Exception as exc:
        receipt['reason']=str(exc) if isinstance(exc,ValueError) else 'Sandbox operation failed; stop and reconcile exact recorded IDs without retry.'
    finally:
        if client:
            receipt['calls']=client.calls;receipt['sandbox_writes']=sum(c['method']!='GET' for c in client.calls)
        receipt['payload_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*payload.json')}
        write(out/'RECEIPT.json',receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--confirm-sandbox',required=True);a=p.parse_args();r=run(a.before,a.out,a.confirm_sandbox);print(json.dumps({k:r.get(k) for k in ('status','reason','production_writes','sandbox_writes')}));return 0 if r['status']=='PASS_SANDBOX_ONLY' else 1
if __name__=='__main__':raise SystemExit(main())
