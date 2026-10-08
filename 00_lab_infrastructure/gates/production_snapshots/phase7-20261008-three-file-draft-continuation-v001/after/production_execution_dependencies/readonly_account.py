"""Closed GET-only complete account discovery. No mutations or credentials storage."""
from __future__ import annotations
import hashlib,json,os,re,time,urllib.parse,urllib.request
from pathlib import Path

class AccountHold(ValueError):pass
HOST='zenodo.org'
SIZE=100
CAP=16*1024*1024

def raw_json(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def require_url(url):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https'or p.netloc!=HOST or p.path!='/api/user/records'or p.fragment or p.username or p.password:raise AccountHold('HOLD_ACCOUNT_URL')
    q=urllib.parse.parse_qs(p.query,strict_parsing=True)
    if set(q)!={'page','size'}or q['size']!=[str(SIZE)]or len(q['page'])!=1 or re.fullmatch('[1-9][0-9]*',q['page'][0])is None or p.query!='page='+q['page'][0]+'&size='+str(SIZE):raise AccountHold('HOLD_ACCOUNT_QUERY')
    return int(q['page'][0])
def immutable(path,data):
    p=Path(path)
    if p.is_symlink()or any(a.is_symlink()for a in p.parents):raise AccountHold('HOLD_ACCOUNT_SYMLINK')
    p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
def total(value):
    if type(value)is int and value>=0:return value
    if isinstance(value,dict)and set(value)=={'value','relation'}and value['relation']=='eq'and type(value['value'])is int and value['value']>=0:return value['value']
    raise AccountHold('HOLD_ACCOUNT_TOTAL_NOT_EXACT')
def identity(row):
    if not isinstance(row,dict)or re.fullmatch('[1-9][0-9]*',str(row.get('id')))is None or not isinstance(row.get('metadata'),dict)or not isinstance(row['metadata'].get('title'),str):raise AccountHold('HOLD_ACCOUNT_ROW')
    return str(row['id'])
def discovery_signature(rows):
    return [{k:r.get(k)for k in('id','metadata','parent','versions','pids','is_draft','is_published','status')}for r in rows]

class AccountDiscovery:
    def __init__(self,token,out,opener,*,pace=lambda:time.sleep(2.05)):
        if not isinstance(token,str)or len(token)<24:raise AccountHold('HOLD_ACCOUNT_TOKEN')
        self._token=token;self.out=Path(out);self.opener=opener;self.pace=pace;self.sequence=0
        if self.out.exists():raise AccountHold('HOLD_ACCOUNT_EVIDENCE_EXISTS')
        self.out.mkdir(parents=True,exist_ok=False)
    def get(self,page):
        url='https://'+HOST+'/api/user/records?page='+str(page)+'&size='+str(SIZE);require_url(url)
        self.sequence+=1;name=f'{self.sequence:03d}_ACCOUNT_GET';self.pace()
        request=urllib.request.Request(url,method='GET',headers={'Authorization':'Bearer '+self._token,'Accept':'application/vnd.inveniordm.v1+json'})
        record={'standard':'VRS-PHASE7-READONLY-ACCOUNT-GET-1','method':'GET','url':url,'status':'STARTED_GET_ONLY'}
        try:
            with self.opener.open(request,timeout=120)as response:
                if getattr(response,'url',url)!=url:raise AccountHold('HOLD_ACCOUNT_REDIRECT')
                code=response.status;raw=response.read(CAP+1)
            if len(raw)>CAP:raise AccountHold('HOLD_ACCOUNT_SIZE_CAP')
            if self._token.encode()in raw:raise AccountHold('HOLD_CREDENTIAL_IN_RESPONSE')
            immutable(self.out/(name+'.response.bin'),raw)
            record.update(http_status=code,response_sha256=sha(raw),response_bytes=len(raw),response_path=str(self.out/(name+'.response.bin')))
            if code!=200:raise AccountHold('HOLD_ACCOUNT_HTTP')
            value=json.loads(raw)
            if not isinstance(value,dict):raise AccountHold('HOLD_ACCOUNT_OBJECT')
            record['status']='RAW_ACCOUNT_GET_CAPTURED_NOT_COMPLETE'
            immutable(self.out/(name+'.json'),raw_json(record));return value
        except Exception as exc:
            record.update(status='HOLD_GET_ONLY_NOT_COMPLETE',error_type=type(exc).__name__)
            path=self.out/(name+'.json')
            if not path.exists():immutable(path,raw_json(record))
            raise AccountHold('HOLD_ACCOUNT_READBACK:'+type(exc).__name__)from None
    def pass_once(self):
        rows=[];seen=set();expected=None;page=1
        while True:
            value=self.get(page);hits=value.get('hits')
            if not isinstance(hits,dict)or not isinstance(hits.get('hits'),list):raise AccountHold('HOLD_ACCOUNT_HITS')
            n=total(hits.get('total'))
            if n>100000:raise AccountHold('HOLD_ACCOUNT_TOTAL_CAP')
            if expected is None:expected=n
            if n!=expected:raise AccountHold('HOLD_ACCOUNT_TOTAL_CHANGED')
            batch=hits['hits'];remaining=expected-len(rows)
            if len(batch)!=min(SIZE,remaining):raise AccountHold('HOLD_ACCOUNT_PAGE_INCOMPLETE')
            for row in batch:
                rid=identity(row)
                if rid in seen:raise AccountHold('HOLD_ACCOUNT_DUPLICATE')
                seen.add(rid);rows.append(row)
            if len(rows)==expected:return rows
            page+=1
    def complete(self,week,discover):
        first=self.pass_once();second=self.pass_once()
        if discovery_signature(first)!=discovery_signature(second):raise AccountHold('HOLD_ACCOUNT_MEMBERSHIP_RACE')
        matched=[r for r in first if r['metadata']['title']=='Viridis Methods Digest — '+week]
        if matched:raise AccountHold('HOLD_WEEKLY_DIGEST_ALREADY_EXISTS')
        result=discover(first,week,complete=True)
        if result.get('status')!='NO_EXISTING_WEEKLY_RECORD':raise AccountHold('HOLD_FIRST_DIGEST_ONLY')
        record={'standard':'VRS-PHASE7-COMPLETE-ACCOUNT-DISCOVERY-1','status':'COMPLETE_STABLE_ACCOUNT_NO_WEEKLY_DIGEST','release_week':week,'record_count':len(first),'double_passes':2,'records_sha256':sha(raw_json(first)),'discovery':result,'writes':0}
        immutable(self.out/'RECORDS.json',raw_json(first));immutable(self.out/'RESULT.json',raw_json(record));return record
