"""Pre-network reservation writer for the actual preserving budget consumer.

Does not send HTTP. Root supplies the actual source-bound require_events and
budget consumers. No summary complete=True or empty caller list grants a slot.
"""
from __future__ import annotations
import datetime as dt,fcntl,hashlib,json,os,re
from pathlib import Path
JOURNAL='reports/verification-coverage/2026-10-07/phase7-approved-audit-execution-v001/publication/MUTATION_JOURNAL_INDEX.json'
class JournalHold(ValueError):pass
def raw_json(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p)
    if p.is_symlink()or not p.is_file()or any(a.is_symlink()for a in p.parents):raise JournalHold('HOLD_JOURNAL_UNSAFE_FILE')
    a=p.stat();b=p.read_bytes();z=p.stat()
    if (a.st_ino,a.st_mtime_ns,a.st_size)!=(z.st_ino,z.st_mtime_ns,z.st_size):raise JournalHold('HOLD_JOURNAL_READ_RACE')
    return b
def immutable(p,data):
    p=Path(p)
    if p.is_symlink()or any(a.is_symlink()for a in p.parents):raise JournalHold('HOLD_JOURNAL_SYMLINK')
    p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
def bound(root,p):
    p=Path(p)
    if not p.is_absolute()or not p.resolve().is_relative_to(Path(root).resolve(strict=True))or any(a.is_symlink()for a in(p,*p.parents)):raise JournalHold('HOLD_JOURNAL_OUTSIDE_ROOT')
    return p
class JournalWriter:
    def __init__(self,root,out,require_events,budget_consumer):
        self.root=Path(root).resolve(strict=True);self.index=self.root/JOURNAL;self.out=bound(self.root,Path(out).resolve());self.require_events=require_events;self.budget_consumer=budget_consumer;self.lock_fd=None;self.reservations=[]
    def __enter__(self):
        if not self.index.is_file():raise JournalHold('HOLD_ACTUAL_JOURNAL_MISSING')
        lock=self.index.parent/'MUTATION_JOURNAL_INDEX.lock'
        if lock.is_symlink():raise JournalHold('HOLD_JOURNAL_LOCK_SYMLINK')
        self.lock_fd=os.open(lock,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:fcntl.flock(self.lock_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:os.close(self.lock_fd);self.lock_fd=None;raise JournalHold('HOLD_CONCURRENT_EXECUTION')from None
        return self
    def __exit__(self,*args):
        if self.lock_fd is not None:fcntl.flock(self.lock_fd,fcntl.LOCK_UN);os.close(self.lock_fd);self.lock_fd=None
    def events_and_budget(self,method,at_utc,compute):
        if self.lock_fd is None:raise JournalHold('HOLD_JOURNAL_LOCK_REQUIRED')
        events=self.require_events(self.root,at_utc);actual=self.budget_consumer(self.root,method,at_utc);expected=compute(events,method,at_utc,complete=True)
        if actual!=expected:raise JournalHold('HOLD_ACTUAL_BUDGET_CHANGED')
        return events,actual
    def reserve(self,method,url,body,transport_path,at_utc,operation_id,compute):
        if self.lock_fd is None:raise JournalHold('HOLD_JOURNAL_LOCK_REQUIRED')
        if method not in {'POST','PUT'}or not isinstance(body,bytes)or re.fullmatch('[A-Za-z0-9:_-]+',operation_id)is None:raise JournalHold('HOLD_RESERVATION_OPERATION')
        # Consumer validates exact URL, not merely prefix equality.
        from urllib.parse import urlsplit
        u=urlsplit(url)
        if u.scheme!='https'or u.netloc!='zenodo.org'or u.query or u.fragment or not u.path.startswith('/api/'):raise JournalHold('HOLD_RESERVATION_URL')
        transport_path=bound(self.root,transport_path)
        if transport_path.exists():raise JournalHold('HOLD_TRANSPORT_RECEIPT_ALREADY_EXISTS')
        _,budget=self.events_and_budget(method,at_utc,compute)
        old=read(self.index);index=json.loads(old)
        if set(index)!={'standard','status','baseline','reservations','updated_at_utc'}or index['standard']!='VRS_PHASE7_MUTATION_JOURNAL_INDEX_1'or index['status']!='ACTIVE'or not isinstance(index['reservations'],list):raise JournalHold('HOLD_JOURNAL_INDEX')
        before=dt.datetime.fromisoformat(index['updated_at_utc'].replace('Z','+00:00'));now=dt.datetime.fromisoformat(at_utc.replace('Z','+00:00'))
        if before.tzinfo is None or now.tzinfo is None or now<before:raise JournalHold('HOLD_JOURNAL_TIME')
        number=len(index['reservations'])+1;folder=self.out/f'{number:04d}_{operation_id}'
        folder.mkdir(parents=True,exist_ok=False)
        request={'operation_id':operation_id,'method':method,'url':url,'request_body_sha256':sha(body),'transport_receipt_path':str(transport_path)}
        request_path=folder/'INTENDED_REQUEST.json';immutable(request_path,raw_json(request))
        reservation={'operation_id':operation_id,'method':method,'host':'zenodo.org','at_utc':at_utc,'status':'STARTED_NO_RETRY','receipt_binding':{'path':str(request_path),'sha256':sha(read(request_path))}}
        reservation_path=folder/'RESERVATION.json';immutable(reservation_path,raw_json(reservation));immutable(folder/'BEFORE_INDEX.json',old)
        index['reservations'].append({'path':str(reservation_path),'sha256':sha(read(reservation_path))});index['updated_at_utc']=at_utc
        after=raw_json(index);immutable(folder/'AFTER_INDEX.json',after)
        if read(self.index)!=old:raise JournalHold('HOLD_JOURNAL_CAS_RACE')
        temp=self.index.parent/('.'+operation_id+'.pending')
        immutable(temp,after)
        if read(self.index)!=old:raise JournalHold('HOLD_JOURNAL_CAS_RACE')
        os.replace(temp,self.index)
        fd=os.open(self.index.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        if read(self.index)!=after:raise JournalHold('HOLD_JOURNAL_READBACK')
        # Fresh admission proves this immutable request now costs one slot;
        # it is diagnostic and does not request a second (off-by-one) slot.
        events=self.require_events(self.root,at_utc)
        if not any(r.get('operation_id')==operation_id for r in events):raise JournalHold('HOLD_RESERVATION_NOT_ACCOUNTED')
        report={'status':'RESERVED_BEFORE_NETWORK_NO_RETRY','operation_id':operation_id,'reservation':{'path':str(reservation_path),'sha256':sha(read(reservation_path))},'before_index_sha256':sha(old),'after_index_sha256':sha(after),'used_before':budget['used'],'remaining_after_reservation':budget['remaining_including_next']-1,'transport_receipt_path':str(transport_path)}
        immutable(folder/'RESULT.json',raw_json(report));self.reservations.append(report);return report
