"""GET-only double-pass weekly-chain discovery and its full raw consumer.

AccountDiscovery's unchanged pass_once/get methods capture the complete
bounded response pages. The original first-only complete() is not modified.
"""
from __future__ import annotations
import hashlib,json,os,re
from copy import deepcopy
from pathlib import Path
from readonly_account import AccountDiscovery,total,identity,discovery_signature,require_url,raw_json
import methods_digest as d


class DiscoveryHold(ValueError):pass
def need(value,reason):
    if not value:raise DiscoveryHold('HOLD_'+reason)
def raw(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'REGULAR_BOUND_SOURCE');a=p.stat();value=p.read_bytes();z=p.stat();need((a.st_ino,a.st_mtime_ns,a.st_size)==(z.st_ino,z.st_mtime_ns,z.st_size),'SOURCE_READ_RACE');return value
def binding(path):
    p=Path(path).resolve(strict=True);return {'path':str(p),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def bound(root,value):
    need(isinstance(value,dict)and set(value)=={'path','sha256'}and isinstance(value['path'],str)and re.fullmatch('[0-9a-f]{64}',str(value['sha256']))is not None,'CLOSED_SOURCE_BINDING');p=Path(value['path']);data=raw(p);need(p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True))and hashlib.sha256(data).hexdigest()==value['sha256'],'CURRENT_CANONICAL_SOURCE');return p,json.loads(data)
def immutable(path,data):
    p=Path(path);need(not any(q.is_symlink()for q in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())

FIELDS={'standard','release_week','record_id','concept_id','passes','records','record_count','producer_sha256','writes','start_kind'}
def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def decode_pass(root,rows):
    need(isinstance(rows,list)and rows,'EXACT_ACCOUNT_PAGES');out=[];expected=None;ids=set()
    for page,row in enumerate(rows,1):
        _,receipt=bound(root,row);need(receipt.get('standard')=='VRS-PHASE7-READONLY-ACCOUNT-GET-1'and receipt.get('method')=='GET'and receipt.get('status')=='RAW_ACCOUNT_GET_CAPTURED_NOT_COMPLETE'and receipt.get('http_status')==200 and require_url(receipt.get('url'))==page,'GENUINE_ACCOUNT_PAGE')
        p=Path(receipt.get('response_path'));data_bytes=raw(p);need(p.resolve(strict=True).is_relative_to(root)and hashlib.sha256(data_bytes).hexdigest()==receipt.get('response_sha256')and len(data_bytes)==receipt.get('response_bytes')and len(data_bytes)<=16*1024*1024,'ACCOUNT_RAW_BINDING')
        data=json.loads(data_bytes);hits=data.get('hits');need(isinstance(hits,dict)and isinstance(hits.get('hits'),list),'ACCOUNT_NATIVE_HITS');count=total(hits.get('total'));need(count<=100000,'BOUNDED_ACCOUNT_TOTAL')
        if expected is None:expected=count
        need(count==expected and len(hits['hits'])==min(100,expected-len(out)),'COMPLETE_EXACT_ACCOUNT_PAGE')
        for record in hits['hits']:
            rid=identity(record);need(rid not in ids,'UNIQUE_ACCOUNT_ID');ids.add(rid);out.append(record)
        need(len(out)<=expected,'ACCOUNT_OVERFLOW')
        if len(out)==expected:need(page==len(rows),'NO_EXTRA_ACCOUNT_PAGE')
    need(len(out)==expected,'ACCOUNT_INCOMPLETE');return out
def discover(rows,week):
    # The unchanged selector expects a legacy doi scalar. Native account
    # rows expose that exact own identifier under pids.doi; the projection
    # adds no claim/title/identity and never chooses another record's PID.
    projected=deepcopy(rows)
    for row in projected:
        rid=identity(row);doi=row.get('pids',{}).get('doi',{}).get('identifier')
        if 'doi'in row:need(doi is None or row['doi']==doi,'ACCOUNT_DOI_REPRESENTATION_CONFLICT')
        elif doi is not None:need(doi=='10.5281/zenodo.'+rid,'ACCOUNT_OWN_DOI');row['doi']=doi
    result=d.discover_weekly_record(projected,week,complete=True)
    if result['status']=='EXISTING_WEEKLY_RECORD':
        own=next(r for r in rows if identity(r)==result['record_id'])
        need(own.get('is_published')is True and own.get('is_draft')is False and own.get('status')=='published'and result['doi']=='10.5281/zenodo.'+result['record_id'],'GENUINE_PUBLISHED_WEEKLY_SOURCE')
    return result
def require_discovery(v,*,root):
    need(isinstance(v,dict)and set(v)==FIELDS and v['standard']=='VRS-OWNED-WEEKLY-DISCOVERY-1'and v['producer_sha256']==source_sha()and type(v['writes'])is int and v['writes']==0,'CURRENT_CLOSED_WEEKLY_DISCOVERY');need(isinstance(v['passes'],list)and len(v['passes'])==2,'REAL_DOUBLE_PASS')
    first,second=[decode_pass(root,rows)for rows in v['passes']];need(discovery_signature(first)==discovery_signature(second),'ACCOUNT_RACE');_,saved=bound(root,v['records']);need(saved=={'records':first}and type(v['record_count'])is int and v['record_count']==len(first),'EXACT_RECORDED_ACCOUNT')
    result=discover(first,v['release_week'])
    need(v['start_kind']in{'NEW_VERSION','CREATE_WEEK'},'CLOSED_DISCOVERY_OPERATION')
    if v['start_kind']=='NEW_VERSION':need(result['status']=='EXISTING_WEEKLY_RECORD'and result['record_id']==v['record_id']and result['concept_id']==v['concept_id'],'ONE_EXISTING_WEEKLY_CONCEPT')
    else:need(result['status']=='NO_EXISTING_WEEKLY_RECORD'and v['record_id']is None and v['concept_id']is None and v['release_week']!='2026-W41','NO_DUPLICATE_FIRST_WEEK_CONCEPT')
    return result
def capture(root,week,token,output,opener):
    out=Path(output);account=AccountDiscovery(token,out/'account',opener);first=account.pass_once();split=account.sequence;second=account.pass_once();need(discovery_signature(first)==discovery_signature(second),'ACCOUNT_RACE');result=discover(first,week);need(result['status']in{'EXISTING_WEEKLY_RECORD','NO_EXISTING_WEEKLY_RECORD'},'CLOSED_ACCOUNT_WEEK_STATE');need(result['status']!='NO_EXISTING_WEEKLY_RECORD'or week!='2026-W41','NO_INDEPENDENT_DUPLICATE_W41')
    records=out/'RECORDS.json';immutable(records,raw_json({'records':first}));paths=sorted((out/'account').glob('*_ACCOUNT_GET.json'));need(len(paths)==account.sequence,'ALL_REAL_PAGE_RECEIPTS')
    v={'standard':'VRS-OWNED-WEEKLY-DISCOVERY-1','release_week':week,'record_id':result.get('record_id'),'concept_id':result.get('concept_id'),'passes':[[binding(p)for p in paths[:split]],[binding(p)for p in paths[split:]]],'records':binding(records),'record_count':len(first),'producer_sha256':source_sha(),'writes':0,'start_kind':'NEW_VERSION'if result['status']=='EXISTING_WEEKLY_RECORD'else'CREATE_WEEK'};require_discovery(v,root=Path(root));p=out/'RESULT.json';immutable(p,raw_json(v));return binding(p)
