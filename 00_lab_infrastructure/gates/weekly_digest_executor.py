"""Root-invoked, source-bound <=4-attempt continuation. No automatic entry point.

This ordinary engine cannot grant scientific/native readback admission. The
reviewed actual boundary module must rerun all unchanged complete consumers;
every post-mutation checkpoint binds its real transport and strict evidence.
"""
from __future__ import annotations
import datetime as dt, hashlib, json, os, re
from pathlib import Path
from zoneinfo import ZoneInfo
import owned_digest_machine as machine
from owned_journal_writer import OwnedJournalWriter

STANDARD='VRS-METHODS-DIGEST-GENERIC-WEEKLY-EXECUTION-1'
MAX_ATTEMPTS=4
class ExecutionHold(ValueError):pass
def need(v,r):
    if not v:raise ExecutionHold('HOLD_'+r)
def raw_json(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n'
def raw(path):
    p=Path(path);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'REGULAR_SOURCE');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_mtime_ns,a.st_size)==(z.st_ino,z.st_mtime_ns,z.st_size),'SOURCE_READ_RACE');return b
def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def binding(path):return {'path':str(Path(path).resolve(strict=True)),'sha256':sha(Path(path).resolve(strict=True))}
def source(root,value):
    machine.binding(value);p=Path(value['path']);need(p.resolve(strict=True).is_relative_to(root),'CANONICAL_BOUND_SOURCE');data=raw(p);need(hashlib.sha256(data).hexdigest()==value['sha256'],'SOURCE_HASH');return p,data
def bound(root,value):
    p,data=source(root,value);return p,json.loads(data)
def immutable(path,data):
    p=Path(path);need(not any(q.is_symlink()for q in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())

def require_prestart_source(root,plan):
    """Frozen PRECREATE GETs must show the exact latest eligible source.

    This runs inside require_plan before any output, transport or reservation.
    A owned continuation retains this pre-create evidence; live source-chain
    transitions are audited separately against that owned draft on every step.
    """
    values=[];bodies=[]
    for key in ('source_native_receipt','source_native_before_create'):
        _,receipt=bound(root,plan[key])
        need(receipt.get('method')=='GET'and receipt.get('url')=='https://zenodo.org/api/records/'+plan['predecessor_record_id']and receipt.get('environment')=='zenodo.org'and receipt.get('http_status')==200 and receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and receipt.get('accept')=='application/vnd.inveniordm.v1+json','ACTUAL_NATIVE_PRECREATE_GET')
        body=receipt.get('response');need(isinstance(body,dict)and body.get('id')==plan['predecessor_record_id']and body.get('parent',{}).get('id')==plan['source_concept_id'],'NATIVE_PRECREATE_SOURCE_IDENTITY')
        versions=body.get('versions');need(isinstance(versions,dict)and type(versions.get('index'))is int and versions['index']>0 and versions.get('is_latest')is True and versions.get('is_latest_draft')is True,'LATEST_SOURCE_BEFORE_NEWVERSION')
        values.append(versions['index']);bodies.append(body)
    need(values[0]==values[1],'SAME_PRECREATE_SOURCE_ORDINAL')
    need(raw_json(bodies[0])==raw_json(bodies[1]),'EXACT_PRECREATE_NATIVE_SOURCE_BODY')

def require_plan(root,plan):
    fields={'standard','status','canonical_root','package','digest_manifest','publication_binding','current_runtime_closure','registration_recovery','before_ssot_sha256','predecessor_registration','source_legacy_receipt','source_native_receipt','source_native_before_create','source_origin','purpose_source_pins','approved_inventory','release_week','predecessor_record_id','expected_concept_id','source_concept_id','prior_run_ids','new_run_ids','boundary_module','authority','community_mirror_proof','runtime_consumer','recovery_consumer','source_session_consumer','ordinary_cohort_consumer','account_discovery','start_kind','execution_directory'}
    need(isinstance(plan,dict)and set(plan)==fields and plan['standard']=='VRS-METHODS-DIGEST-GENERIC-WEEKLY-PLAN-1'and plan['status']=='ACTUAL_CURRENT_SOURCE_BOUND_NOT_EXECUTED','EXACT_ACTUAL_PLAN')
    need(plan['canonical_root']==str(root),'CANONICAL_ROOT');history=Path(plan['execution_directory']);need(history.is_absolute()and history.resolve().is_relative_to(root/'reports/verification-coverage')and not any(q.is_symlink()for q in(history,*history.parents)),'OWN_EXECUTION_HISTORY');package=Path(plan['package']);need(package.is_absolute()and package.resolve(strict=True).is_relative_to(root),'OWN_PACKAGE')
    for key in('digest_manifest','publication_binding','registration_recovery','predecessor_registration','source_legacy_receipt','source_native_receipt','source_native_before_create','source_origin','authority','community_mirror_proof','runtime_consumer','recovery_consumer','source_session_consumer','ordinary_cohort_consumer','account_discovery'):source(root,plan[key])
    closure=plan['current_runtime_closure'];need(isinstance(closure,dict)and set(closure)=={'path','sha256'}and isinstance(closure['path'],str)and not Path(closure['path']).is_absolute()and '..'not in Path(closure['path']).parts and re.fullmatch('[0-9a-f]{64}',str(closure['sha256']))is not None,'CANONICAL_RELATIVE_MEASURED_RUNTIME');cp=root/closure['path'];need(cp.resolve(strict=True).is_relative_to(root)and sha(cp)==closure['sha256'],'EXACT_MEASURED_RUNTIME_RECEIPT')
    need(plan['digest_manifest']['path']==str(package/'DIGEST_MANIFEST.json')and plan['publication_binding']['path']==str(package/'PUBLICATION_BINDING.json'),'OWN_EXACT_PACKAGE')
    machine.inventory(plan['approved_inventory'])
    for row in plan['approved_inventory']:
        p=Path(row['path']);need(p==package/row['name'],'OWN_APPROVED_FILE');b=raw(p);need(len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']and hashlib.md5(b).hexdigest()==row['md5'],'APPROVED_BYTES')
    need(re.fullmatch('[0-9]{4}-W[0-9]{2}',str(plan['release_week']))is not None,'WEEK');need(isinstance(plan['new_run_ids'],list)and plan['new_run_ids']and len(plan['new_run_ids'])==len(set(plan['new_run_ids']))and isinstance(plan['prior_run_ids'],list)and len(plan['prior_run_ids'])==len(set(plan['prior_run_ids']))and not set(plan['new_run_ids'])&set(plan['prior_run_ids']),'DISJOINT_NEW_NOTE_IDS')
    need(plan['start_kind']in{'NEW_VERSION','CREATE_WEEK'},'CLOSED_OWNED_WEEKLY_OPERATION')
    for key in('predecessor_record_id','source_concept_id'):need(isinstance(plan[key],str)and re.fullmatch('[1-9][0-9]*',plan[key])is not None,'REAL_PREDECESSOR_CONCEPT')
    if plan['start_kind']=='NEW_VERSION':need(plan['expected_concept_id']==plan['source_concept_id'],'OWN_EXISTING_CONCEPT_ONLY')
    else:need(plan['expected_concept_id']is None and plan['release_week']!='2026-W41','NO_INVENTED_FIRST_CONCEPT_OR_DUPLICATE_W41')
    need(plan['predecessor_record_id']!=plan['source_concept_id'],'DISTINCT_PUBLIC_PARENT')
    _,manifest=bound(root,plan['digest_manifest']);need(manifest['release_week']==plan['release_week']and [n['run_id']for n in manifest['notes']]==plan['new_run_ids'],'ACTUAL_NEW_COHORT')
    _,legacy_source=bound(root,plan['source_legacy_receipt']);_,native=bound(root,plan['source_native_receipt'])
    for receipt in(legacy_source,native):need(receipt.get('method')=='GET'and receipt.get('url')=='https://zenodo.org/api/records/'+plan['predecessor_record_id']and receipt.get('environment')=='zenodo.org'and receipt.get('http_status')==200 and receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','ACTUAL_PUBLIC_SOURCE_RECEIPT')
    need(native.get('accept')=='application/vnd.inveniordm.v1+json'and native['response'].get('id')==plan['predecessor_record_id']and native['response'].get('parent',{}).get('id')==plan['source_concept_id'],'REAL_PUBLIC_SOURCE_PAIR')
    need(str(legacy_source['response'].get('id'))==plan['predecessor_record_id']and str(legacy_source['response'].get('conceptrecid'))==plan['source_concept_id'],'SOURCE_IDENTITY')
    require_prestart_source(root,plan)
    if plan['start_kind']=='NEW_VERSION':need(legacy_source['response'].get('metadata',{}).get('title')==manifest['public_metadata']['title'],'PRESERVED_WEEKLY_TITLE')
    else:need(manifest['public_metadata']['title']=='Viridis Methods Digest — '+plan['release_week'],'EXACT_FIRST_WEEK_TITLE')
    pins=plan['purpose_source_pins'];need(isinstance(pins,list)and pins and len({x.get('name')for x in pins if isinstance(x,dict)})==len(pins),'CLOSED_PURPOSE_SOURCE_TABLE')
    for row in pins:
        need(isinstance(row,dict)and set(row)=={'name','path','sha256'},'CLOSED_PURPOSE_PIN')
        p=Path(row['path']);archive=re.fullmatch('archive_([0-9a-f]{64})_(.+[.]py)',row['name'])
        named=(p.name==row['name'])if archive is None else(p.name==archive[2]and p.parent.name==archive[1]and p.parent.parent.name=='policy_versions')
        need(named and p.resolve(strict=True).is_relative_to(root)and sha(p)==row['sha256'],'ACTUAL_PURPOSE_SOURCE')
    need({'methods_digest_registration_legacy_0fc739.py','owned_creation_recovery.py','own_prior_record.py','own_record_comparison.py','weekly_digest_executor.py','weekly_digest_boundary.py','weekly_digest_runtime.py','weekly_checkpoint_replay.py','prepare_weekly_digest_plan.py','invoke_weekly_digest.py','weekly_archive_wait.py','weekly_digest_queue.py','weekly_pending_discovery.py','owned_digest_machine.py','owned_journal_writer.py','digest_weekly_state.py','methods_digest.py','methods_digest_registration.py','server_managed_fields.py','zenodo_transport.py','phase7_mutation_baseline.py','mutation_journal_writer.py'}<={r['name']for r in pins},'FULL_PURPOSE_CLOSURE')
    need(plan['boundary_module']=='weekly_digest_boundary.py','ONE_CLOSED_BOUNDARY')
    return package

def publication_day(root,plan,now):
    _,manifest=bound(root,plan['digest_manifest']);value=manifest['public_metadata'].get('publication_date')
    need(isinstance(value,str)and re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}',value)is not None,'EXPLICIT_BOUND_PUBLICATION_DATE')
    intended=dt.date.fromisoformat(value)
    instant=dt.datetime.fromisoformat(now.replace('Z','+00:00'))
    need(instant.tzinfo is not None,'AWARE_PUBLICATION_CLOCK')
    actual=instant.astimezone(ZoneInfo('America/New_York')).date()
    return {'intended':intended.isoformat(),'actual':actual.isoformat(),'ready':intended==actual,'wait_status':'WAIT_PLANNED_NEW_YORK_PUBLISH_DAY'if actual<intended else'WAIT_IMMUTABLE_PUBLICATION_DATE_REBINDING'}

def require_command(root,plan,state,step,command):
    need(isinstance(command,dict)and set(command)=={'method','url','body','content_type','delete_file'}and isinstance(command['body'],bytes),'CLOSED_SOURCE_BOUND_COMMAND')
    base='https://zenodo.org';rid=state['record_id'];method='POST';body=b'{}';kind='application/json';delete=None
    if step=='NEW_VERSION':need(plan['start_kind']=='NEW_VERSION','EXACT_APPROVED_SAME_WEEK_STEP');url=base+'/api/deposit/depositions/'+plan['predecessor_record_id']+'/actions/newversion'
    elif step=='CREATE_WEEK':
        need(plan['start_kind']=='CREATE_WEEK','EXACT_APPROVED_FIRST_WEEK_STEP');url=base+'/api/deposit/depositions'
        from digest_metadata import closed_payload
        from first_digest_state import encode_api_communities
        _,manifest=bound(root,plan['digest_manifest']);_,prior=bound(root,plan['source_legacy_receipt'])
        body=raw_json(encode_api_communities(closed_payload(manifest['public_metadata'],prior['response']['metadata'])))
    elif step.startswith('DROP:'):
        delete=next(x for x in state['inherited_inventory']if x['filename']==step[5:]);method='DELETE';body=b'';url=base+'/api/deposit/depositions/'+rid+'/files/'+delete['id']
    elif step=='METADATA':
        method='PUT';url=base+'/api/deposit/depositions/'+rid
        from digest_metadata import closed_payload
        from first_digest_state import encode_api_communities
        _,manifest=bound(root,plan['digest_manifest']);_,prior=bound(root,plan['source_legacy_receipt'])
        body=raw_json(encode_api_communities(closed_payload(manifest['public_metadata'],prior['response']['metadata'])))
    elif step.startswith('UPLOAD:'):
        row=next(x for x in plan['approved_inventory']if x['name']==step[7:]);_,previous=bound(root,state['last_validation']);bucket=previous['expected_legacy']['links']['bucket'];need(isinstance(bucket,str)and re.fullmatch('https://zenodo.org/api/files/[0-9a-f-]{36}',bucket)is not None,'OWN_REAL_BUCKET');url=bucket+'/'+row['name'];method='PUT';body=raw(Path(row['path']));kind='application/octet-stream';need(hashlib.sha256(body).hexdigest()==row['sha256'],'EXACT_UPLOAD_COMMAND_BYTES')
    elif step=='RESERVE_DOI':url=base+'/api/records/'+rid+'/draft/pids/doi'
    elif step=='PUBLISH':url=base+'/api/deposit/depositions/'+rid+'/actions/publish'
    else:raise ExecutionHold('HOLD_UNLISTED_COMMAND_STEP')
    need(command=={'method':method,'url':url,'body':body,'content_type':kind,'delete_file':delete},'EXACT_OWN_NEXT_COMMAND')
    return command

def execute(root,plan_binding,output,token,runtime,*,checkpoint=None,reviewed_driver_sha256,
            clock=lambda:dt.datetime.now(dt.timezone.utc).isoformat()):
    """Run up to four actual mutation attempts and return an immutable checkpoint.

    runtime is the reviewed purpose-bound loader, not a caller's PASS summary.
    Its admission() verifies real merge blobs, activated runtime, current
    default registrations, complete own source closure and frozen package.
    boundary.before()/after() rerun complete source/native/legacy/file/PID rules.
    """
    root=Path(root).resolve(strict=True);out=Path(output)
    need(sha(Path(__file__).resolve())==reviewed_driver_sha256,'REVIEWED_EXACT_EXECUTOR')
    _,plan=bound(root,plan_binding);package=require_plan(root,plan);ph=machine.digest(plan)
    need(out.is_absolute()and out.parent==Path(plan['execution_directory'])and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists()and not any(q.is_symlink()for q in(out,*out.parents)),'EXCLUSIVE_CANONICAL_OUTPUT')
    need(isinstance(token,str)and len(token)>=24,'MEMORY_CREDENTIAL')
    runtime.admission(plan,package) # independently replays all actual consumers
    if checkpoint is None:current=machine.initial(ph,plan['approved_inventory'],start_kind=plan['start_kind'])
    else:
        _,current=bound(root,checkpoint);machine.validate(current,ph)
        runtime.replay_checkpoint(plan,current) # every bound reservation/receipt/readback
    need(current['published']is False,'CONSUMED_PUBLISHED_CHAIN')
    need(current['start_kind']==plan['start_kind'],'FROZEN_OPERATION_KIND')
    machine.next_step(current) # refuses any uncertain/reserved/HOLD/consumed state
    out.mkdir(parents=True,exist_ok=False)
    def emit(name,value):
        data=raw_json(value);need(token.encode()not in data,'NO_CREDENTIAL_IN_EVIDENCE');p=out/name;immutable(p,data);return binding(p)
    emit('PLAN.json',plan);emit('BEFORE_CHECKPOINT.json',current)
    transport=runtime.transport(token,out/'transport')
    boundary=runtime.boundary(plan,package,transport,out)
    attempted=0;serial=0;stop='SAFE_NONTERMINAL'
    def save(label):
        nonlocal serial
        serial+=1;return emit('checkpoints/'+f'{serial:03d}_'+label+'.json',current)
    with OwnedJournalWriter(root,out/'reservations',runtime.require_events,runtime.require_budget)as writer:
        while attempted<MAX_ATTEMPTS:
            step=machine.next_step(current)
            if step is None:stop='PUBLISHED_STRICT_READBACK_PASS';break
            if step=='PUBLISH':
                day=publication_day(root,plan,clock())
                if not day['ready']:stop=day['wait_status'];break
            runtime.admission(plan,package);boundary.before(current) # fresh GET/readback, no write
            command=boundary.command(current,step)
            require_command(root,plan,current,step,command)
            at=clock()
            if step=='PUBLISH':
                # This second check runs after complete admission and fresh
                # GET/downloads, with the exact immutable attempt timestamp.
                # A midnight crossing consumes neither reservation nor write.
                day=publication_day(root,plan,at)
                if not day['ready']:stop=day['wait_status'];break
            try:
                events,budget=writer.events_and_budget(command['method'],at,runtime.d.require_write_budget)
            except runtime.d.DigestHold as exc:
                if str(exc)!='daily 10-write cap reached; no write/retry':raise
                stop='WAIT_NEXT_NEW_YORK_DAY';break
            need(budget['used']<10 and budget['remaining_including_next']>0,'ACTUAL_DAILY_SLOT')
            runtime.d.prewrite(package,root,command['method'],at,events,complete_journal=True,budget_consumer=runtime.require_budget)
            if step=='PUBLISH':
                # Publication-bound package checks may cross midnight. Refresh
                # the actual reservation timestamp after all fallible prewrite
                # work; an expired day consumes no charge and sends no request.
                at=clock();day=publication_day(root,plan,at)
                if not day['ready']:stop=day['wait_status'];break
            op='phase7-owned:'+ph[:16]+':'+hashlib.sha256(step.encode()).hexdigest()[:16]
            need(not any(event.get('operation_id')==op for event in events),'RESERVED_OPERATION_ALREADY_CONSUMED_NO_RETRY')
            if command['method']=='DELETE':
                need(step.startswith('DROP:')and command['body']==b''and command['delete_file']is not None,'DRAFT_ONLY_DELETE')
                # unchanged narrow transport performs two GETs before DELETE
                predicted=transport.out/f'{transport.sequence+3:03d}_DELETE.json'
                reserved=writer.reserve_drop(draft_id=current['record_id'],previous_record_id=plan['predecessor_record_id'],expected_file=command['delete_file'],transport_path=predicted,at_utc=at,operation_id=op,compute=runtime.d.require_write_budget,creation_evidence=current['creation_receipt'])
            else:
                need(command['delete_file']is None,'NO_GENERIC_DELETE');predicted=transport.out/f'{transport.sequence+1:03d}_{command["method"]}.json'
                reserved=writer.reserve(command['method'],command['url'],command['body'],predicted,at,op,runtime.d.require_write_budget)
            current=machine.reserve(current,step,reserved['reservation'],op);attempted+=1;save('RESERVED_BEFORE_NETWORK')
            publish_day_blocked_before_network=False
            try:
                if step=='PUBLISH':
                    # A reservation itself may cross midnight. Preserve the
                    # charged attempt as known-unsent HOLD; never send a stale
                    # publication-date request or silently refund its slot.
                    day=publication_day(root,plan,clock())
                    if not day['ready']:
                        publish_day_blocked_before_network=True
                        raise ExecutionHold('HOLD_PUBLISH_DAY_CHANGED_AFTER_RESERVATION:'+day['intended']+':'+day['actual'])
                if command['method']=='DELETE':response=transport.remove_inherited_draft_file(current['record_id'],plan['predecessor_record_id'],command['delete_file'],expected_sha256=hashlib.sha256(b'').hexdigest(),authorized=True)
                else:response=transport.request(command['method'],command['url'],command['body'],hashlib.sha256(command['body']).hexdigest(),command['content_type'],authorized=True,accept='application/vnd.inveniordm.v1+json'if step=='RESERVE_DOI'else'application/json')
                need(predicted.exists(),'OWN_EXPECTED_TRANSPORT_RECEIPT');own=binding(predicted)
                # after() must read and verify actual receipts; raw HTTP success
                # and marker dictionaries cannot produce a strict completion.
                checked,ownership=boundary.after(current,step,response,own)
                bound(root,checked);current=machine.finish(current,own,checked,ownership=ownership);save('STRICT_READBACK_COMPLETE')
            except Exception as exc:
                own=binding(predicted)if predicted.exists()else None
                uncertain=not publish_day_blocked_before_network and(own is None or json.loads(raw(predicted)).get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE')
                current=machine.fail(current,own,str(exc),uncertain=uncertain);save('HARD_HOLD_NO_RETRY');stop=current['phase'];break
            runtime.admission(plan,package)
            if current['published']:stop='PUBLISHED_STRICT_READBACK_PASS';break
    final=emit('CHECKPOINT.json',current)
    result={'standard':STANDARD,'status':stop,'release_week':plan['release_week'],'plan':plan_binding,'checkpoint':final,'writes_attempted_this_invocation':attempted,'max_attempts_per_invocation':MAX_ATTEMPTS,'daily_limit':10,'record_id':current['record_id'],'concept_id':current['concept_id'],'published':current['published'],'automatic_retry':False,'certifies':False,'ssot_writes':0}
    emit('RESULT.json',result);return result

if __name__=='__main__':raise SystemExit('HOLD: only an explicit reviewed root call with actual merged sources, installed closure and genuine receipts is executable')
