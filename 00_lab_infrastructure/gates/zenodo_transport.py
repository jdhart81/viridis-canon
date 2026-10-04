"""Hash-guarded Zenodo transport; credentials stay in Keychain and process memory.

No CLI, automatic retry, deletion, acceptance decision or implicit production authorization.
The caller must supply an independently recorded exact body hash before each mutation.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.parse
import urllib.request


class TransportHold(RuntimeError): pass


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

    def request(self, method, url, body=None, expected_sha256=None, content_type='application/json', authorized=False):
        parsed=urllib.parse.urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname!=self.host or parsed.port not in (None,443) or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise TransportHold('HOLD_URL_BOUNDARY')
        if method not in ('GET','POST','PUT'):raise TransportHold('HOLD_METHOD')
        if method=='GET':
            if body is not None:raise TransportHold('HOLD_GET_BODY')
        else:
            if authorized is not True:raise TransportHold('HOLD_NOT_AUTHORIZED')
            if not isinstance(body,bytes) or hashlib.sha256(body).hexdigest()!=expected_sha256:
                raise TransportHold('HOLD_BODY_HASH')
        self.sequence+=1
        receipt={'method':method,'url':url,'request_body_sha256':expected_sha256,'environment':self.host,'status':'STARTED_NO_RETRY'}
        path=self.out/f'{self.sequence:03d}_{method}.json'
        path.write_text(json.dumps(receipt,indent=2)+'\n')
        req=urllib.request.Request(url,data=body,method=method,headers={'Authorization':'Bearer '+self._token,'Accept':'application/json',**({'Content-Type':content_type} if body is not None else {})})
        try:
            with self.opener.open(req,timeout=120) as response:
                code=response.status;raw=response.read()
            if not 200<=code<300:raise TransportHold('HOLD_HTTP_STATUS_'+str(code))
            value=json.loads(raw)
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
