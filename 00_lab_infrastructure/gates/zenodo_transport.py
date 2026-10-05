"""Hash-guarded Zenodo transport; credentials stay in Keychain and process memory.

No CLI, automatic retry, record deletion, acceptance decision or implicit production authorization.
The caller must supply an independently recorded exact body hash before each mutation.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request


class TransportHold(RuntimeError): pass


def _canonical_decimal_id(value):
    if type(value) not in (str,int):return None
    try:value=str(value)
    except ValueError:return None
    if not value or value[0] not in '123456789' or any(c not in '0123456789' for c in value):return None
    return value


def _valid_filename(value):
    return (isinstance(value,str) and bool(value) and value not in ('.','..')
            and '/' not in value and '\\' not in value
            and all(ord(c)>=32 and ord(c)!=127 for c in value))


def _valid_file_id(value):
    return isinstance(value,str) and re.fullmatch(r'[0-9a-f]+(?:-[0-9a-f]+)*',value) is not None


def _file_entry_json(entry):
    def valid(value):
        if type(value) in (str,int,float,bool,type(None)):return True
        if type(value) is list:return all(valid(v) for v in value)
        if type(value) is dict:return all(type(k) is str and valid(v) for k,v in value.items())
        return False
    try:
        if not valid(entry):raise ValueError('not JSON fields')
        return json.dumps(entry,sort_keys=True,separators=(',',':'),allow_nan=False)
    except (TypeError,ValueError,OverflowError,RecursionError):
        raise TransportHold('HOLD_INHERITED_FILE_JSON') from None


def _valid_file_entry(entry, *, published=False):
    if not isinstance(entry,dict):return False
    name='key' if published else 'filename';size='size' if published else 'filesize'
    checksum=entry.get('checksum')
    if published:
        if not isinstance(checksum,str) or not checksum.startswith('md5:'):return False
        checksum=checksum[4:]
    if not (_valid_filename(entry.get(name)) and _valid_file_id(entry.get('id'))
            and type(entry.get(size)) is int and entry[size]>=0
            and isinstance(checksum,str) and re.fullmatch(r'[0-9a-f]{32}',checksum) is not None):return False
    try:_file_entry_json(entry)
    except TransportHold:return False
    return True


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise TransportHold('HOLD_REDIRECT_REFUSED')


def keychain_token(service, account):
    result=subprocess.run(['security','find-generic-password','-s',service,'-a',account,'-w'],capture_output=True)
    if result.returncode or len(result.stdout.strip())<24:
        raise TransportHold('HOLD_KEYCHAIN_CREDENTIAL_UNAVAILABLE')
    return result.stdout.decode().strip()


class ZenodoTransport:
    def __init__(self, host, token, evidence_dir, opener=None):
        if host not in ('sandbox.zenodo.org','zenodo.org'):raise TransportHold('HOLD_HOST')
        if not token:raise TransportHold('HOLD_CREDENTIAL')
        self.host=host;self._token=token;self.out=Path(evidence_dir)
        self.out.mkdir(parents=True,exist_ok=True)
        self.opener=opener or urllib.request.build_opener(NoRedirect())
        self.sequence=0

    def request(self, method, url, body=None, expected_sha256=None, content_type='application/json', authorized=False, accept='application/json'):
        if method not in ('GET','POST','PUT'):raise TransportHold('HOLD_METHOD')
        return self._send(method,url,body,expected_sha256,content_type,authorized,accept)

    def remove_inherited_draft_file(self, draft_id, previous_record_id, expected_file, *, expected_sha256, authorized=False):
        """Remove one exact inherited entry from a distinct unpublished successor.

        Every call freshly proves the draft boundary and exact original entry.
        The public request API continues to reject DELETE; no record deletion is exposed.
        """
        if authorized is not True:raise TransportHold('HOLD_NOT_AUTHORIZED')
        if expected_sha256 != hashlib.sha256(b'').hexdigest():raise TransportHold('HOLD_BODY_HASH')
        draft_id=_canonical_decimal_id(draft_id);previous_record_id=_canonical_decimal_id(previous_record_id)
        if draft_id is None or previous_record_id is None or draft_id==previous_record_id:
            raise TransportHold('HOLD_DISTINCT_SUCCESSOR_IDS')
        if not _valid_file_entry(expected_file):
            raise TransportHold('HOLD_INHERITED_FILE_INPUT')
        file_id=expected_file['id']
        base='https://'+self.host
        previous=self.request('GET',base+'/api/records/'+previous_record_id)
        if not isinstance(previous,dict):raise TransportHold('HOLD_PUBLISHED_PARENT_SHAPE')
        if _canonical_decimal_id(previous.get('id'))!=previous_record_id:raise TransportHold('HOLD_PUBLISHED_PARENT_IDENTITY')
        originals=previous.get('files')
        if not isinstance(originals,list) or any(not _valid_file_entry(f,published=True) for f in originals):
            raise TransportHold('HOLD_PUBLISHED_PARENT_FILES')
        draft_url=base+'/api/deposit/depositions/'+draft_id
        draft=self.request('GET',draft_url)
        if not isinstance(draft,dict):raise TransportHold('HOLD_SUCCESSOR_DRAFT_SHAPE')
        if _canonical_decimal_id(draft.get('id'))!=draft_id or draft.get('state')!='unsubmitted' or draft.get('submitted') is not False:
            raise TransportHold('HOLD_UNPUBLISHED_SUCCESSOR_REQUIRED')
        concept_id=_canonical_decimal_id(previous.get('conceptrecid'))
        if not isinstance(previous.get('doi'),str) or not previous['doi'] or concept_id is None or _canonical_decimal_id(draft.get('conceptrecid'))!=concept_id:
            raise TransportHold('HOLD_SUCCESSOR_CONCEPT')
        entries=draft.get('files')
        if not isinstance(entries,list) or any(not _valid_file_entry(f) for f in entries):raise TransportHold('HOLD_DRAFT_FILES')
        matches=[f for f in entries if f.get('id')==file_id]
        if len(matches)!=1 or _file_entry_json(matches[0])!=_file_entry_json(expected_file):raise TransportHold('READBACK_MISMATCH_INHERITED_FILE')
        # A new successor must inherit this identity from the stated published parent.
        inherited=[f for f in originals if f.get('id')==file_id]
        if len(inherited)!=1 or inherited[0].get('key')!=expected_file['filename'] or inherited[0].get('checksum')!=('md5:'+expected_file['checksum']) or inherited[0].get('size')!=expected_file['filesize']:
            raise TransportHold('HOLD_NOT_INHERITED_FROM_PARENT')
        return self._send('DELETE',draft_url+'/files/'+file_id,b'',expected_sha256,'application/json',True,'application/json',empty_response=True)

    def _send(self, method, url, body, expected_sha256, content_type, authorized, accept, empty_response=False):
        if accept not in ('application/json','application/vnd.inveniordm.v1+json'):raise TransportHold('HOLD_ACCEPT_MEDIA_TYPE')
        parsed=urllib.parse.urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname!=self.host or parsed.port not in (None,443) or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise TransportHold('HOLD_URL_BOUNDARY')
        if method not in ('GET','POST','PUT') and not (method=='DELETE' and empty_response):raise TransportHold('HOLD_METHOD')
        if method=='GET':
            if body is not None:raise TransportHold('HOLD_GET_BODY')
        else:
            if authorized is not True:raise TransportHold('HOLD_NOT_AUTHORIZED')
            if not isinstance(body,bytes) or hashlib.sha256(body).hexdigest()!=expected_sha256:
                raise TransportHold('HOLD_BODY_HASH')
        self.sequence+=1
        receipt={'method':method,'url':url,'request_body_sha256':expected_sha256,'environment':self.host,'accept':accept,'status':'STARTED_NO_RETRY'}
        path=self.out/f'{self.sequence:03d}_{method}.json'
        path.write_text(json.dumps(receipt,indent=2)+'\n')
        req=urllib.request.Request(url,data=body,method=method,headers={'Authorization':'Bearer '+self._token,'Accept':accept,**({'Content-Type':content_type} if body is not None else {})})
        try:
            with self.opener.open(req,timeout=120) as response:
                code=response.status;raw=response.read()
            if not 200<=code<300:raise TransportHold('HOLD_HTTP_STATUS_'+str(code))
            if empty_response:
                if code!=204 or raw!=b'':raise TransportHold('HOLD_EXPECTED_EMPTY_204')
                value={'empty_204':True,'draft_file_removed':True}
            else:value=json.loads(raw)
            if not isinstance(value,(dict,list)):raise TransportHold('HOLD_RESPONSE_SHAPE')
            safe=json.dumps(value,ensure_ascii=False).replace(self._token,'[REDACTED_CREDENTIAL]')
            receipt.update(status='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE',http_status=code,response_sha256=hashlib.sha256(raw).hexdigest(),response=json.loads(safe))
            path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
            return value
        except Exception as exc:
            receipt.update(status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY',error_type=type(exc).__name__)
            if isinstance(exc,urllib.error.HTTPError):
                receipt['http_status']=exc.code
                try:
                    detail=json.loads(exc.read(65536))
                    receipt['error_response']=json.loads(json.dumps(detail).replace(self._token,'[REDACTED_CREDENTIAL]'))
                except Exception:receipt['error_response']='UNAVAILABLE_OR_NON_JSON'
            path.write_text(json.dumps(receipt,indent=2)+'\n')
            raise TransportHold('HOLD_TRANSPORT_UNCERTAIN_NO_RETRY:'+type(exc).__name__) from None


def require_metadata(actual, expected):
    if actual!=expected:
        fields=sorted(k for k in actual.keys()|expected.keys() if actual.get(k)!=expected.get(k))
        raise TransportHold('READBACK_MISMATCH:'+','.join(fields))
