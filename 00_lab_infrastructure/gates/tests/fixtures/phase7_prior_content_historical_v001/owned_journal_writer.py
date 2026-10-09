"""Narrow draft-only DELETE reservation extension; original writer unchanged.

POST/PUT go through the original writer exactly. DELETE is permitted solely
for the same unpublished successor's source-proven inherited file. The actual
unchanged transport performs the independent draft and parent checks again.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt, os, re
from pathlib import Path
import mutation_journal_writer as original

class OwnedJournalWriter(original.JournalWriter):
    def reserve_drop(self,*,draft_id,previous_record_id,expected_file,transport_path,
                     at_utc,operation_id,compute,creation_evidence):
        if self.lock_fd is None:raise original.JournalHold('HOLD_JOURNAL_LOCK_REQUIRED')
        canonical=lambda x:isinstance(x,str)and re.fullmatch('[1-9][0-9]*',x)is not None
        if not canonical(draft_id)or not canonical(previous_record_id)or draft_id==previous_record_id:raise original.JournalHold('HOLD_DISTINCT_OWNED_DRAFT')
        if not isinstance(expected_file,dict)or set(expected_file)!={'checksum','filename','filesize','id','links'}or not isinstance(expected_file['id'],str)or re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',expected_file['id'])is None:raise original.JournalHold('HOLD_EXACT_INHERITED_ENTRY')
        if not isinstance(creation_evidence,dict)or set(creation_evidence)!={'path','sha256'}:raise original.JournalHold('HOLD_OWN_CREATION_EVIDENCE')
        path=original.bound(self.root,creation_evidence['path']);data=original.read(path)
        if original.sha(data)!=creation_evidence['sha256']:raise original.JournalHold('HOLD_CREATION_HASH')
        record=original.json.loads(data);response=record.get('response',{})
        if record.get('method')!='POST'or record.get('url')!='https://zenodo.org/api/deposit/depositions/'+previous_record_id+'/actions/newversion'or record.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'or record.get('http_status')!=201 or str(response.get('id'))!=draft_id or response.get('state')!='unsubmitted'or response.get('submitted')is not False:raise original.JournalHold('HOLD_GENUINE_OWN_NEWVERSION')
        matches=[r for r in response.get('files',[])if isinstance(r,dict)and r.get('id')==expected_file['id']]
        if len(matches)!=1 or original.raw_json(matches[0])!=original.raw_json(expected_file):raise original.JournalHold('HOLD_FILE_NOT_IN_OWN_CREATION')
        if not isinstance(operation_id,str)or re.fullmatch('[A-Za-z0-9:_-]+',operation_id)is None:raise original.JournalHold('HOLD_OPERATION_ID')
        transport_path=original.bound(self.root,transport_path)
        if transport_path.exists():raise original.JournalHold('HOLD_TRANSPORT_RECEIPT_ALREADY_EXISTS')
        url='https://zenodo.org/api/deposit/depositions/'+draft_id+'/files/'+expected_file['id']
        _,budget=self.events_and_budget('DELETE',at_utc,compute)
        old=original.read(self.index);index=original.json.loads(old)
        if set(index)!={'standard','status','baseline','reservations','updated_at_utc'}or index['standard']!='VRS_PHASE7_MUTATION_JOURNAL_INDEX_1'or index['status']!='ACTIVE'or not isinstance(index['reservations'],list):raise original.JournalHold('HOLD_JOURNAL_INDEX')
        before=dt.datetime.fromisoformat(index['updated_at_utc'].replace('Z','+00:00'));now=dt.datetime.fromisoformat(at_utc.replace('Z','+00:00'))
        if before.tzinfo is None or now.tzinfo is None or now<before:raise original.JournalHold('HOLD_JOURNAL_TIME')
        folder=self.out/f'{len(index["reservations"])+1:04d}_{operation_id}';folder.mkdir(parents=True,exist_ok=False)
        request={'operation_id':operation_id,'method':'DELETE','url':url,'request_body_sha256':original.sha(b''),'transport_receipt_path':str(transport_path)}
        request_path=folder/'INTENDED_REQUEST.json';original.immutable(request_path,original.raw_json(request))
        reservation={'operation_id':operation_id,'method':'DELETE','host':'zenodo.org','at_utc':at_utc,'status':'STARTED_NO_RETRY','receipt_binding':{'path':str(request_path),'sha256':original.sha(original.read(request_path))}}
        reservation_path=folder/'RESERVATION.json';original.immutable(reservation_path,original.raw_json(reservation));original.immutable(folder/'BEFORE_INDEX.json',old)
        original.immutable(folder/'OWNED_DROP.json',original.raw_json({'creation_evidence':creation_evidence,'draft_id':draft_id,'previous_record_id':previous_record_id,'expected_file':deepcopy(expected_file),'public_file_deletion':False}))
        index['reservations'].append({'path':str(reservation_path),'sha256':original.sha(original.read(reservation_path))});index['updated_at_utc']=at_utc;after=original.raw_json(index);original.immutable(folder/'AFTER_INDEX.json',after)
        if original.read(self.index)!=old:raise original.JournalHold('HOLD_JOURNAL_CAS_RACE')
        temp=self.index.parent/('.'+operation_id+'.pending');original.immutable(temp,after)
        if original.read(self.index)!=old:raise original.JournalHold('HOLD_JOURNAL_CAS_RACE')
        os.replace(temp,self.index);fd=os.open(self.index.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        if original.read(self.index)!=after:raise original.JournalHold('HOLD_JOURNAL_READBACK')
        events=self.require_events(self.root,at_utc)
        if not any(r.get('operation_id')==operation_id for r in events):raise original.JournalHold('HOLD_RESERVATION_NOT_ACCOUNTED')
        report={'status':'RESERVED_BEFORE_NETWORK_NO_RETRY','operation_id':operation_id,'reservation':{'path':str(reservation_path),'sha256':original.sha(original.read(reservation_path))},'before_index_sha256':original.sha(old),'after_index_sha256':original.sha(after),'used_before':budget['used'],'remaining_after_reservation':budget['remaining_including_next']-1,'transport_receipt_path':str(transport_path)}
        original.immutable(folder/'RESULT.json',original.raw_json(report));self.reservations.append(report);return report
