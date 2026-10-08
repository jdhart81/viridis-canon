"""Read-only source-bound production mutation accounting; never transport.

Every actual mutation receipt is counted. Identical receipt bytes at distinct
paths are conservatively distinct attempts unless a separately proven origin
relationship is adopted. No SHA-only or uncertain-attempt deduplication occurs. A missing capture, disappearing receipt or racing scan
is HOLD; complete=True supplied by a caller is not evidence.
"""
from __future__ import annotations
import datetime as dt,hashlib,json,re,os
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

STANDARD='VRS_PHASE7_SOURCE_BOUND_MUTATION_BASELINE_1'
INDEX_STANDARD='VRS_PHASE7_MUTATION_JOURNAL_INDEX_1'
JOURNAL='reports/verification-coverage/2026-10-07/phase7-approved-audit-execution-v001/publication/MUTATION_JOURNAL_INDEX.json'
STATUSES={'STARTED_NO_RETRY','HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'}
METHODS={'POST','PUT','DELETE'}
sha=lambda b:hashlib.sha256(b).hexdigest()

def utc(value):
    parsed=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('timezone required')
    return parsed.astimezone(dt.timezone.utc)

def read(path):
    p=Path(path)
    if p.is_symlink()or not p.is_file()or any(a.is_symlink()for a in p.parents):raise ValueError('regular unsymlinked evidence required')
    before=p.stat();b=p.read_bytes();after=p.stat()
    state=lambda st:(st.st_ino,st.st_size,st.st_mtime_ns)
    if state(before)!=state(after):raise ValueError('mutation evidence changed during read')
    return b,{'bytes':len(b),'sha256':sha(b),'mtime_ns':after.st_mtime_ns,'inode':after.st_ino}

def bound(root,value):
    if not isinstance(value,dict)or set(value)!={'path','sha256'}or not isinstance(value['path'],str)or not re.fullmatch('[a-f0-9]{64}',str(value['sha256'])):raise ValueError('closed path/hash binding required')
    p=Path(value['path']);p=p if p.is_absolute()else Path(root)/p
    if not p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True)):raise ValueError('evidence outside canonical root')
    raw,stat=read(p)
    if stat['sha256']!=value['sha256']:raise ValueError('mutation binding changed')
    return p.resolve(),raw

def _paths(root):
    base=Path(root)/'reports/verification-coverage'
    if not base.is_dir()or base.is_symlink():raise ValueError('canonical report family missing')
    result=[]
    for folder,dirs,files in os.walk(base,followlinks=False):
        if any((Path(folder)/d).is_symlink()for d in dirs):raise ValueError('report source directory symlink')
        for name in files:
            if name.endswith('.json'):
                p=Path(folder)/name
                if p.is_symlink():raise ValueError('JSON evidence symlink')
                result.append(p.resolve())
    return sorted(result)

def _receipt(value):
    if not isinstance(value,dict)or value.get('environment')!='zenodo.org'or value.get('method')not in METHODS:return False
    parsed=urlsplit(str(value.get('url','')))
    if parsed.scheme!='https'or parsed.hostname!='zenodo.org'or parsed.username or parsed.password or parsed.port not in(None,443)or parsed.query or parsed.fragment:raise ValueError('mutation own-host URL malformed')
    if value.get('status')not in STATUSES or not re.fullmatch('[a-f0-9]{64}',str(value.get('request_body_sha256'))):raise ValueError('unclassified production mutation receipt')
    if value['status']=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and not re.fullmatch('[a-f0-9]{64}',str(value.get('response_sha256'))):raise ValueError('successful receipt missing raw-response hash')
    return True

def enumerate_sources(root,now):
    root=Path(root).resolve(strict=True);now=utc(now)if isinstance(now,str)else now.astimezone(dt.timezone.utc)
    paths=_paths(root);inventory=[];receipts=[]
    for p in paths:
        raw,stat=read(p)
        try:obj=json.loads(raw)
        except Exception as exc:raise ValueError('unreadable JSON source: '+str(p))from exc
        is_receipt=_receipt(obj)
        # The two accounting records are excluded only from recursive source
        # inventory, never from transport classification.
        excluded=p.name=='MUTATION_JOURNAL_INDEX.json'or(p.name.startswith('MUTATION_BASELINE')and p.parent==root/Path(JOURNAL).parent)
        if excluded and is_receipt:raise ValueError('transport receipt hidden under accounting filename')
        if not excluded:inventory.append({'path':str(p),**stat,'is_transport_receipt':is_receipt})
        if is_receipt:receipts.append({'path':str(p),'stat':stat,'receipt':obj})
    if paths!=_paths(root):raise ValueError('report source inventory changed during scan')
    for row in inventory:
        _,stat=read(row['path'])
        if stat!={k:row[k]for k in('bytes','sha256','mtime_ns','inode')}:raise ValueError('report source bytes/stat raced')
    return {'source_inventory':inventory,'transport_receipts':receipts}

def capture(root,at_utc):
    """Return immutable capture bytes to root; this module never writes."""
    now=utc(at_utc);scan=enumerate_sources(root,now)
    return {'standard':STANDARD,'status':'SOURCE_BOUND_CAPTURE','tree_root':str(Path(root).resolve(strict=True)),'captured_at_utc':now.isoformat(),'source_inventory':scan['source_inventory'],'transport_receipts':scan['transport_receipts']}

def _receipt_events(receipts,now):
    events=[];now=utc(now)if isinstance(now,str)else now
    for row in receipts:
        r=row['receipt'];stat=row['stat']
        if not _receipt(r):raise ValueError('captured mutation changed shape')
        modified=r.get('response',{}).get('modified')if isinstance(r.get('response'),dict)else None
        when=None
        if r['status']=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and isinstance(modified,str):
            try:when=utc(modified)
            except Exception:when=None
        if when is None:
            try:when=dt.datetime.fromtimestamp(stat['mtime_ns']/1_000_000_000,dt.timezone.utc)
            except Exception:when=now
        if when>now:when=now  # Ambiguous/future filesystem timestamp costs today's slot.
        identity=sha((row['path']+'\0'+stat['sha256']).encode())
        events.append({'operation_id':'transport:'+identity,'method':r['method'],'host':'zenodo.org','at_utc':when.isoformat(),'status':r['status'],'receipt_binding':{'path':row['path'],'sha256':stat['sha256']}})
    return events

def require_events(root,at_utc):
    root=Path(root).resolve(strict=True);now=utc(at_utc)
    ip=root/JOURNAL;index_raw,_=read(ip);index=json.loads(index_raw)
    if set(index)!={'standard','status','baseline','reservations','updated_at_utc'}or index['standard']!=INDEX_STANDARD or index['status']!='ACTIVE'or utc(index['updated_at_utc'])>now:raise ValueError('closed current mutation index required')
    _,baseline_raw=bound(root,index['baseline']);baseline=json.loads(baseline_raw)
    if set(baseline)!={'standard','status','tree_root','captured_at_utc','source_inventory','transport_receipts'}or baseline['standard']!=STANDARD or baseline['status']!='SOURCE_BOUND_CAPTURE'or baseline['tree_root']!=str(root)or utc(baseline['captured_at_utc'])>now:raise ValueError('actual pre-mutation source capture required')
    fresh=enumerate_sources(root,now);current={r['path']:r for r in fresh['source_inventory']}
    baseline_paths=set()
    for row in baseline['source_inventory']:
        if not isinstance(row,dict)or set(row)!={'path','bytes','sha256','mtime_ns','inode','is_transport_receipt'}or row['path']in baseline_paths:raise ValueError('invalid/duplicate baseline source inventory')
        baseline_paths.add(row['path'])
        if row['path']not in current:raise ValueError('baseline source disappeared')
        if row['is_transport_receipt']and row!=current[row['path']]:raise ValueError('previous transport receipt changed; budget HOLD')
    captured=utc(baseline['captured_at_utc'])
    if not baseline_paths:raise ValueError('empty baseline is not a complete source capture')
    for path,row in current.items():
        if path not in baseline_paths and dt.datetime.fromtimestamp(row['mtime_ns']/1e9,dt.timezone.utc)<=captured:
            raise ValueError('baseline omitted an earlier source file')
    # Baseline transport rows must equal their exact full source inventory and
    # are re-read from disk; a summary's complete flag cannot supply coverage.
    expected={r['path']for r in baseline['source_inventory']if r['is_transport_receipt']}
    if {r['path']for r in baseline['transport_receipts']}!=expected:raise ValueError('baseline transport coverage incomplete')
    for row in baseline['transport_receipts']:
        data,stat=read(row['path'])
        if stat!=row['stat']or json.loads(data)!=row['receipt']:raise ValueError('baseline transport bytes changed')
    events=_receipt_events(fresh['transport_receipts'],now)
    if not isinstance(index['reservations'],list):raise ValueError('ordered reservation bindings required')
    seen=set();claimed_actual=set();previous=captured;snapshots={}
    for value in index['reservations']:
        rp,raw=bound(root,value);snapshots[str(rp)]=sha(raw);r=json.loads(raw)
        fields={'operation_id','method','host','at_utc','status','receipt_binding'}
        if set(r)!=fields or not isinstance(r['operation_id'],str)or not r['operation_id']or r['operation_id']in seen or r['method']not in METHODS or r['host']!='zenodo.org'or r['status']!='STARTED_NO_RETRY':raise ValueError('closed unique mutation reservation required')
        seen.add(r['operation_id']);t=utc(r['at_utc'])
        if t<previous or t>now:raise ValueError('reservation order/time invalid')
        previous=t
        receipt_path,rr=bound(root,r['receipt_binding']);receipt=json.loads(rr)
        snapshots[str(receipt_path)]=sha(rr)
        # A reservation can bind an immutable intended transport request before
        # the actual attempt. Its identity is exact URL+body; a completed actual
        # receipt subsumes exactly one reservation. Uncertain attempts stay.
        if not isinstance(receipt,dict)or set(receipt)!={'operation_id','method','url','request_body_sha256','transport_receipt_path'}or receipt['operation_id']!=r['operation_id']or receipt['method']!=r['method']or not re.fullmatch('[a-f0-9]{64}',str(receipt['request_body_sha256'])):raise ValueError('reservation request binding invalid')
        parsed=urlsplit(receipt['url'])
        if parsed.scheme!='https'or parsed.hostname!='zenodo.org'or parsed.port not in(None,443)or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('reservation own-host boundary')
        target=Path(receipt['transport_receipt_path'])
        if not target.is_absolute() or not target.resolve().is_relative_to(root) or any(x.is_symlink()for x in(target,*target.parents)):
            raise ValueError('reservation exact transport path outside canonical root or symlink')
        matching=[]
        for v in fresh['transport_receipts']:
            vr=v['receipt']
            if v['path']!=receipt['transport_receipt_path'] or vr['method']!=receipt['method']or vr['url']!=receipt['url']or vr['request_body_sha256']!=receipt['request_body_sha256']:continue
            actual_event=_receipt_events([v],now)[0]
            if utc(actual_event['at_utc'])>=t and actual_event['operation_id']not in claimed_actual:matching.append(actual_event)
        if matching:claimed_actual.add(matching[0]['operation_id'])
        else:events.append(r)
    if read(ip)[0]!=index_raw or bound(root,index['baseline'])[1]!=baseline_raw:raise ValueError('baseline/index changed during admission')
    for path,h in snapshots.items():
        if sha(read(path)[0])!=h:raise ValueError('reservation/request changed during admission')
    return events
