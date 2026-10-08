"""Root-only one-shot continuation of source-bound draft23226761.

No CREATE, metadata PUT, issuer, verifier or new acceptance rule. The reviewed
publisher helpers, transport, budget and full readback/registrar are reused.
"""
from copy import deepcopy
import datetime as dt,hashlib,json,re,time,urllib.parse,urllib.request
from pathlib import Path
import first_digest_publisher as base
import draft_reservation as reservation
from first_digest_publisher import (PublishHold,require,raw_json,sha,binding,read_regular,immutable,bound,require_module_pins,PacedOpener,Downloads,Runtime,AccountDiscovery,JournalWriter)
metadata=base.metadata;state=base.state;publisher_previews=base.publisher_previews;publisher_recovery=base.publisher_recovery
NATIVE=base.NATIVE
STANDARD='VRS-PHASE7-FIRST-METHODS-DIGEST-EXISTING-DRAFT-EXECUTION-1'

def require_recovery_plan(root,package,recovery):
    fields={'standard','status','canonical_root','package_path','original_plan','own_context','runtime_pins','record_id','expected_writes','prior_daily_attempts'}
    require(isinstance(recovery,dict)and set(recovery)==fields and recovery['standard']=='VRS-PHASE7-FIRST-DIGEST-EXISTING-DRAFT-PLAN-1'and recovery['status']=='FROZEN_READY_NOT_EXECUTED','CLOSED_OWN_DRAFT_RECOVERY_PLAN')
    require(recovery['canonical_root']==str(root)and recovery['package_path']==str(package)and recovery['record_id']==reservation.OWN_ID and recovery['expected_writes']==8 and recovery['prior_daily_attempts']==2,'EXACT_EIGHT_OWN_DRAFT_RECOVERY')
    _,original=bound(root,recovery['original_plan']);plan=deepcopy(original);plan['runtime_pins']=deepcopy(recovery['runtime_pins'])
    require_module_pins(root,plan['runtime_pins']);required={'first_digest_existing_draft.py','draft_reservation.py','first_digest_publisher.py'};require(required<={r['name']for r in plan['runtime_pins']},'COMPLETE_RECOVERY_SOURCE_CLOSURE')
    prepared=base.require_plan(root,package,plan)
    values={key:bound(root,value)[1]for key,value in recovery['own_context'].items()}
    api_path,_=bound(root,recovery['own_context']['api_metadata_payload']);api_body=read_regular(api_path)
    creation,legacy,native=reservation.require_context(recovery['own_context'],values,api_body,original,plan)
    require(read_regular(api_path)==raw_json(prepared['api_payload']),'ORIGINAL_CREATION_REQUEST_EXACT_BYTES')
    require_module_pins(root,original['runtime_pins'])
    return prepared,plan,{'creation':creation,'initial_legacy':legacy,'initial_native':native,'api_payload':values['api_metadata_payload'],'creation_receipt':recovery['own_context']['creation_receipt'],'api_metadata_payload':recovery['own_context']['api_metadata_payload'],'original_plan':recovery['original_plan']}

def _execute(root,package,plan,output,token,runtime,*,account_factory=AccountDiscovery,transport_factory=None,download_factory=Downloads,clock=lambda:dt.datetime.now(dt.timezone.utc).isoformat(),monotonic=time.monotonic,sleep=time.sleep):
    recovery_plan=plan;prepared,plan,context=require_recovery_plan(root,package,recovery_plan);manifest=prepared['manifest'];require(not output.exists()and output.resolve().is_relative_to(root/'reports/verification-coverage'),'IMMUTABLE_CANONICAL_EXECUTION_ONLY');output.mkdir(parents=True,exist_ok=False);immutable(output/'PLAN.json',raw_json(plan));immutable(output/'RECOVERY_PLAN.json',raw_json(recovery_plan));immutable(output/'API_METADATA_PAYLOAD.json',raw_json(prepared['api_payload']));immutable(output/'EXPECTED_NATIVE_METADATA.json',raw_json(prepared['native_metadata']))
    d,policy,mut,sm,preserve=runtime.d,runtime.policy,runtime.mut,runtime.sm,runtime.preservation
    opener=PacedOpener(urllib.request.build_opener(runtime.transport.NoRedirect()));factory=transport_factory or runtime.transport.ZenodoTransport;t=factory('zenodo.org',token,output/'transport',opener=opener);downloads=download_factory(token,opener,output/'downloads')
    uploads=[dict(name=u['filename'],path=str(package/u['filename']),size=u['bytes'],sha256=u['sha256'],md5=u['md5'])for u in manifest['uploads']]
    for name in('DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
        data=read_regular(package/name);uploads.append({'name':name,'path':str(package/name),'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest()})
    require(len(uploads)==6 and len({u['name']for u in uploads})==6,'EXACT_SIX_UPLOADS');immutable(output/'APPROVED_SIX_FILES.json',raw_json({'files':uploads}))
    result={'recovery_attempts':0,'prior_own_create_attempts':1,'prior_other_daily_attempts':1,'standard':STANDARD,'status':'HOLD','release_week':manifest['release_week'],'notes':plan['first_notes'],'writes':0,'record_id':reservation.OWN_ID,'doi':None,'phase':'PRECHECK','failure':None,'automatic_retry':False,'main_certificates_replaced':False,'certifies':False};created_path=Path(context['creation_receipt']['path']);source_paths=[];upload_paths=[];current=None;legacy_expected=None;published=False;publish_path=None;creation=context['creation'];rid=reservation.OWN_ID;checkpoint_number=0;last_reservation=None;last_transport=None;fresh_source_receipts=None;initial_budget=None
    def emit(name,value):
        data=raw_json(value);require(token.encode()not in data,'CREDENTIAL_IN_EXECUTION_EVIDENCE');immutable(output/name,data);return output/name
    def checkpoint(label):
        nonlocal checkpoint_number
        checkpoint_number+=1;emit('checkpoints/'+f'{checkpoint_number:03d}_'+label+'.json',publisher_recovery.checkpoint(result,plan_binding=binding(output/'PLAN.json'),inventory_binding=binding(output/'APPROVED_SIX_FILES.json'),reservation=last_reservation,transport_receipt=last_transport))
    def saved(method):return t.out/f'{t.sequence:03d}_{method}.json'
    def ev(path):return {'receipt_path':str(path),'receipt_sha256':sha(path),'transport_contract_sha256':sm.transport_contract_sha256()}
    def preview_context():return {'own_record_id':rid,'approved_inventory_evidence':binding(output/'APPROVED_SIX_FILES.json'),'lineage_evidence':ev(created_path),'source_readback_evidence':[ev(p)for p in source_paths],'delete_evidence':[],'upload_evidence':[ev(p)for p in upload_paths],'publish_evidence':ev(publish_path)if publish_path else None}
    def read_source():
        nonlocal fresh_source_receipts
        url='https://zenodo.org/api/records/'+prepared['source_id'];legacy=t.request('GET',url);native=t.request('GET',url,accept=NATIVE);fresh_source_receipts=(t.out/f'{t.sequence-1:03d}_GET.json',saved('GET'));predicted=metadata.native_metadata(manifest['public_metadata'],prepared['before_metadata'],legacy,native,prepared['relation_template'])
        require(metadata.exact(predicted,prepared['native_metadata']),'FRESH_SOURCE_VOCABULARY_CHANGED')
        require(legacy['metadata'].get('title')==prepared['source_legacy']['metadata'].get('title')==prepared['before_metadata'].get('title'),'FRESH_SOURCE_TITLE_CHANGED')
        require(metadata.exact(native.get('custom_fields',{}).get('legacy:communities'),prepared['source_native'].get('custom_fields',{}).get('legacy:communities'))and metadata.exact(native.get('parent',{}).get('access',{}).get('owned_by'),prepared['source_native'].get('parent',{}).get('access',{}).get('owned_by')),'FRESH_SOURCE_COMMUNITY_OR_OWNER_CHANGED')
        return legacy,native
    def own_pair():
        legacy=t.request('GET','https://zenodo.org/api/deposit/depositions/'+rid);native=t.request('GET','https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE);source_paths.extend([t.out/f'{t.sequence-1:03d}_GET.json',saved('GET')]);return legacy,native
    def draft_guard(legacy,native,expected,wanted,*,label):
        state.require_private_source(legacy,wanted,native,sm,preserve)
        audit=sm.validate_new_version(native,expected,host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=expected,own_operation_record_id=rid,derived_preview_context=preview_context(),existing_communities=manifest['public_metadata'].get('communities'),public_communities=manifest['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
        # Main uploaded bytes are checked independently of previews/metadata.
        selected={x['name']:x for x in uploads};native_names=set(native['files']['entries']);require(native_names=={x['filename']for x in wanted['files']},'DRAFT_MAIN_FILE_SET')
        for name in sorted(native_names):downloads.get(name,rid,selected[name],published=False)
        emit(label+'.json',{'status':'STRICT_DRAFT_READBACK_PASS','native_audit':audit,'files_downloaded_exact':sorted(native_names)})
        return deepcopy(native),deepcopy(legacy)
    def fresh():
        runtime.fresh(package,plan);read_source()
        if current is not None:
            legacy,native=own_pair();draft_guard(legacy,native,current,legacy_expected,label=f'PREWRITE_{t.sequence:03d}')
    def mutation(writer,method,url,body,purpose,content_type='application/json',accept='application/json'):
        nonlocal result,last_reservation,last_transport
        require(result['writes']<8 and not published,'NO_DUPLICATE_OR_POSTPUBLISH_MUTATION');fresh();at=clock();events,budget=writer.events_and_budget(method,at,d.require_write_budget);require(initial_budget is not None and budget['date_new_york']==initial_budget['date_new_york']and budget['used']==initial_budget['used']+result['writes'],'SOURCE_BOUND_DAY_OR_ATTEMPT_COUNT_CHANGED');d.prewrite(package,root,method,at,events,complete_journal=True,budget_consumer=policy.require_write_budget)
        operation_id=reservation.operation_id(sha(package/'DIGEST_MANIFEST.json'),manifest['release_week'],rid,result['phase'],body)
        reservation.require_unspent_operation(events,operation_id)
        reserved=writer.reserve(method,url,body,t.out/f'{t.sequence+1:03d}_{method}.json',at,operation_id,d.require_write_budget)
        emit(f'WRITE_{result["writes"]+1:02d}_PRECHECK.json',{'status':'RESERVED_PREWRITE_PASS','purpose':purpose,'reservation':reserved,'package_binding':binding(package/'PUBLICATION_BINDING.json'),'body_sha256':hashlib.sha256(body).hexdigest()})
        result['writes']+=1;result['recovery_attempts']=result['writes'] # Every attempted mutation costs its slot, including uncertainty.
        last_reservation=reserved['reservation'];last_transport=None;checkpoint('RESERVED_BEFORE_NETWORK')
        try:
            response=t.request(method,url,body,hashlib.sha256(body).hexdigest(),content_type,authorized=True,accept=accept)
        finally:
            path=t.out/f'{t.sequence:03d}_{method}.json'
            if path.exists():last_transport=binding(path)
            checkpoint('ATTEMPT_FINISHED_OR_UNCERTAIN')
        return response
    try:
        runtime.fresh(package,plan);checkpoint('PRECHECK')
        with JournalWriter(root,output/'reservations',mut.require_events,policy.require_write_budget)as writer:
            account=account_factory(token,output/'account-discovery',opener,pace=lambda:None)
            reservation.complete_account(account,manifest['release_week'],creation,context['initial_native'])
            budget_at=clock();events,budget=writer.events_and_budget('POST',budget_at,d.require_write_budget);require(budget['remaining_including_next']>=8 and budget['used']==2,'EIGHT_DAILY_SLOTS_REQUIRED_FOR_OWN_DRAFT_RECOVERY');initial_budget=deepcopy(budget);emit('INITIAL_DAILY_BUDGET.json',{'standard':'VRS_SOURCE_BOUND_OWN_DRAFT_RECOVERY_BUDGET_1','at_utc':budget_at,'budget':budget,'event_bindings':[e['receipt_binding']for e in events],'prior_own_create':context['creation_receipt'],'journal_index':binding(writer.index),'diagnostics_only':True})
            result['phase']='EXISTING_DRAFT_PRECHECK';legacy,native=own_pair()
            expected,wanted=reservation.initial_expected(creation,context['initial_native'],prepared,sm,preserve)
            current,legacy_expected=draft_guard(legacy,native,expected,wanted,label='EXISTING_DRAFT_STRICT_READBACK')
            require(metadata.exact(prepared['api_payload'],context['api_payload']),'ORIGINAL_CREATION_API_PAYLOAD_UNCHANGED')
            emit('METADATA_ALREADY_EXACT.json',{'status':'EXACT_EXISTING_OWN_METADATA_NO_PUT_REQUIRED','creation_receipt':context['creation_receipt'],'original_api_payload':context['api_metadata_payload'],'original_plan':context['original_plan'],'legacy_readback':binding(source_paths[-2]),'native_readback':binding(source_paths[-1]),'metadata_changed':False,'metadata_puts':0})
            emit('OWN_CREATION_RECEIPT.json',{'standard':'SOURCE_BOUND_TRANSPORT_REFERENCE_1','status':'REFERENCE_ONLY_NOT_ANOTHER_MUTATION','receipt':context['creation_receipt']})
            bucket=creation.get('links',{}).get('bucket');require(isinstance(bucket,str)and re.fullmatch('https://zenodo[.]org/api/files/[0-9a-f-]{36}',bucket)is not None,'OWN_CREATION_BUCKET')
            result['phase']='RESERVE_DOI';before_reserve=deepcopy(current);legacy_before_reserve=deepcopy(legacy_expected)
            response=mutation(writer,'POST','https://zenodo.org/api/records/'+rid+'/draft/pids/doi',b'{}','Reserve exact own legacy preregistration via proven native route',accept=NATIVE)
            reserve_path=saved('POST');native_ack,expected,wanted=reservation.require_reservation_receipt(json.loads(read_regular(reserve_path)),before_reserve,legacy_before_reserve,rid)
            # Validate the full native ACK under the original closed validator;
            # its body is never adopted as the expected draft.
            sm.validate_new_version(native_ack,expected,host='zenodo.org',record_id=rid,phase='DRAFT',temporal_baseline=before_reserve,own_operation_record_id=rid,derived_preview_context=preview_context(),existing_communities=manifest['public_metadata'].get('communities'),public_communities=manifest['public_metadata'].get('communities'),mirror_proof=prepared['mirror'])
            legacy,native=own_pair();current,legacy_expected=draft_guard(legacy,native,expected,wanted,label='RESERVE_DOI_STRICT_READBACK')
            emit('OWN_RESERVATION_RECEIPT.json',{'standard':'SOURCE_BOUND_TRANSPORT_REFERENCE_1','status':'REFERENCE_ONLY_NOT_ANOTHER_MUTATION','receipt':binding(reserve_path),'managed_doi':current['pids']['doi']['identifier'],'legacy_preregistration_exact':True})
            for number,row in enumerate(uploads,1):
                result['phase']='UPLOAD_'+row['name'];data=read_regular(row['path']);require(hashlib.sha256(data).hexdigest()==row['sha256']and len(data)==row['size'],'FROZEN_UPLOAD_BYTES');response=mutation(writer,'PUT',bucket+'/'+urllib.parse.quote(row['name'],safe=''),data,'Exact digest upload '+row['name'],'application/octet-stream');upload_paths.append(saved('PUT'));legacy,native=own_pair();matches=[f for f in legacy.get('files',[])if f.get('filename')==row['name']];require(len(matches)==1,'OWN_UPLOADED_ENTRY');expected=deepcopy(current);expected['files']['entries'][row['name']]=state.file_from_upload(matches[0],response,row,rid);state.refresh_totals(expected);wanted=deepcopy(legacy_expected);wanted['files'].append(matches[0]);current,legacy_expected=draft_guard(legacy,native,expected,wanted,label=f'UPLOAD_{number:02d}_STRICT_READBACK')
            require(set(current['files']['entries'])=={x['name']for x in uploads}and result['writes']==7,'EXACT_SIX_FILES_BEFORE_PUBLICATION');emit('BEFORE_PUBLISH_NATIVE.json',current);emit('BEFORE_PUBLISH_LEGACY.json',legacy_expected)
            result['phase']='PUBLISH';response=mutation(writer,'POST','https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish',b'{}','Publish one exact bound digest after reservation and six exact uploads');publish_path=saved('POST');published=True;publish_receipt=json.loads(read_regular(publish_path));emit('OWN_PUBLISH_RECEIPT.json',{'standard':'SOURCE_BOUND_TRANSPORT_REFERENCE_1','status':'REFERENCE_ONLY_NOT_ANOTHER_MUTATION','receipt':binding(publish_path)});expected_native,doi,concept=state.public_projection(current,response,rid);result['doi']=doi;emit('EXPECTED_NATIVE_PUBLIC.json',expected_native)
            # This is the FIRST authenticated native public GET after own POST.
            url='https://zenodo.org/api/records/'+rid;public_native=t.request('GET',url,accept=NATIVE);native_get=saved('GET');source_paths.append(native_get);emit('AFTER_PUBLIC_NATIVE.json',public_native)
            public_legacy=t.request('GET',url);legacy_get=saved('GET');emit('AFTER_PUBLIC_LEGACY.json',public_legacy)
            server_context={'operation':'NEW_VERSION','host':'zenodo.org','record_id':rid,'phase':'PUBLISHED','same_operation_response':response,'existing_concept_doi':concept,'previous_latest_index':0,'chain_parent_id':current['parent']['id'],'temporal_baseline':current,'own_publish_response':publish_receipt,'same_operation_reservation_id':rid,'revision_evidence':{'receipt_directory':str(t.out),'publish_receipt_name':publish_path.name,'first_native_get_receipt_name':native_get.name,'transport_contract_sha256':sm.transport_contract_sha256()},'own_operation_record_id':rid,'existing_communities':manifest['public_metadata'].get('communities'),'public_communities':public_legacy.get('metadata',{}).get('communities'),'mirror_proof':prepared['mirror'],'derived_preview_context':preview_context()};emit('SERVER_CONTEXT.json',server_context)
            # Only the decided missing-thumbnail transition may wait. Every
            # unmodified readback must eventually pass the original full rules.
            deadline=monotonic()+600;opener.deadline=time.monotonic()+600;polls=[]
            while True:
                kwargs=dict(server_context);kwargs.pop('operation')
                try:audit=sm.validate_new_version(public_native,expected_native,**kwargs);break
                except Exception as exc:
                    if not publisher_previews.preview_pending_only(sm,public_native,expected_native,server_context,exc):raise
                    remaining=deadline-monotonic();require(remaining>0,'PREVIEW_TEN_MINUTE_DEADLINE')
                    polls.append({'native_get':binding(native_get),'status':'KNOWN_PREVIEW_PENDING_NO_ACCEPTANCE','report':getattr(exc,'report',None)})
                    emit('preview-polls/'+f'{len(polls):03d}.json',polls[-1])
                    sleep(min(5,remaining));require(monotonic()<deadline,'PREVIEW_TEN_MINUTE_DEADLINE')
                    public_native=t.request('GET',url,accept=NATIVE);native_get=saved('GET');source_paths.append(native_get)
                    public_legacy=t.request('GET',url);legacy_get=saved('GET')
                    server_context['public_communities']=public_legacy.get('metadata',{}).get('communities');server_context['derived_preview_context']=preview_context()
            opener.deadline=None
            emit('PREVIEW_POLL_INDEX.json',{'status':'FULL_STRICT_PASS','polls':polls,'max_wait_seconds':600,'mutation_retries':0})
            if polls:
                emit('FINAL_AFTER_PUBLIC_NATIVE.json',public_native);emit('FINAL_AFTER_PUBLIC_LEGACY.json',public_legacy);emit('FINAL_SERVER_CONTEXT.json',server_context)
            emit('STRICT_NATIVE_READBACK.json',audit)
            expected_legacy=state.public_legacy_projection(prepared['source_legacy'],public_native,manifest['public_metadata'],doi,concept);emit('EXPECTED_PUBLIC_LEGACY.json',expected_legacy);legacy_audit=state.require_public_legacy(public_legacy,expected_legacy,public_native,sm,preserve);emit('STRICT_LEGACY_READBACK.json',legacy_audit)
            own_publish=deepcopy(publish_receipt);own_publish.update(record_id=rid,doi=doi)
            byname={r['name']:r for r in uploads}
            def download(entry,record_id):return downloads.get(entry['key'],record_id,byname[entry['key']],published=True,published_url=entry.get('links',{}).get('self'))
            def metadata_guard(actual,wanted,receipt):state.require_public_legacy(actual,wanted,public_native,sm,preserve)
            strict=d.strict_readback(package,root,public_legacy,own_publish,download,expected_record=expected_legacy,metadata_consumer=metadata_guard);emit('STRICT_DIGEST_READBACK.json',strict);emit('PUBLIC_DOWNLOADS.json',downloads.public)
            require(result['writes']==8,'EXACT_EIGHT_RECOVERY_WRITES_CLOSED');final_at=clock();final_events=mut.require_events(root,final_at);final_daily=reservation.daily_diagnostics(final_events,final_at);require(final_daily['date_new_york']==initial_budget['date_new_york']and final_daily['used']==initial_budget['used']+8,'FINAL_SOURCE_BOUND_DAILY_COUNT');emit('FINAL_DAILY_BUDGET.json',{'standard':'VRS_SOURCE_BOUND_OWN_DRAFT_RECOVERY_BUDGET_1','at_utc':final_at,'daily':final_daily,'event_bindings':[e['receipt_binding']for e in final_events],'journal_index':binding(writer.index),'diagnostics_only':True})
            envelope={'standard':'VRS_PHASE7_DIGEST_PUBLIC_READBACK_ENVELOPE_1','status':'STRICT_PUBLIC_READBACK_PASS','record_id':rid,'doi':doi,'release_week':manifest['release_week'],'digest_path':str(package),'digest_manifest':binding(package/'DIGEST_MANIFEST.json'),'digest_publication_binding':binding(package/'PUBLICATION_BINDING.json'),'source_before_metadata':plan['source_before_metadata'],'source_legacy':plan['source_legacy'],'source_native':plan['source_native'],'relation_vocabulary_source':plan['relation_vocabulary_source'],'community_mirror_proof':plan['community_mirror_proof'],'own_publish_receipt':binding(publish_path),'native_public_get_receipt':binding(native_get),'legacy_public_get_receipt':binding(legacy_get),'before_publish_native':binding(output/'BEFORE_PUBLISH_NATIVE.json'),'expected_native_public':binding(output/'EXPECTED_NATIVE_PUBLIC.json'),'expected_public_legacy':binding(output/'EXPECTED_PUBLIC_LEGACY.json'),'after_public_native':binding(output/('FINAL_AFTER_PUBLIC_NATIVE.json'if polls else'AFTER_PUBLIC_NATIVE.json')),'after_public_legacy':binding(output/('FINAL_AFTER_PUBLIC_LEGACY.json'if polls else'AFTER_PUBLIC_LEGACY.json')),'server_context':binding(output/('FINAL_SERVER_CONTEXT.json'if polls else'SERVER_CONTEXT.json')),'strict_native_readback':binding(output/'STRICT_NATIVE_READBACK.json'),'strict_legacy_readback':binding(output/'STRICT_LEGACY_READBACK.json'),'strict_digest_readback':binding(output/'STRICT_DIGEST_READBACK.json'),'public_downloads':downloads.public,'runtime_pins':plan['runtime_pins'],'notes':[{k:n[k]for k in('run_id','certificate','publication_binding','policy_receipt')}for n in manifest['notes']],'mutations':9,'recovery_mutations':8,'prior_own_creation_mutations':1,'daily_total_including_prior_failed_create':final_daily['used'],'daily_date_new_york':final_daily['date_new_york'],'prior_own_creation_receipt':context['creation_receipt'],'recovery_plan':binding(output/'RECOVERY_PLAN.json'),'metadata_already_exact':binding(output/'METADATA_ALREADY_EXACT.json'),'initial_daily_budget':binding(output/'INITIAL_DAILY_BUDGET.json'),'final_daily_budget':binding(output/'FINAL_DAILY_BUDGET.json'),'automatic_retry':False,'certifies':False};emit('FINAL_READBACK_ENVELOPE.json',envelope)
            # This is an input adapter, never a cached acceptance summary. The
            # actual current registrar repeats the bound gate and readback.
            require(fresh_source_receipts is not None,'FRESH_ORIGINAL_SOURCE_PAIR_RECEIPTS')
            relation_path=emit('RELATION_TEMPLATE.json',prepared['relation_template'])
            evidence=runtime.registration.assemble_evidence(record_id=rid,
                public_legacy_receipt=binding(legacy_get),public_native_receipt=binding(native_get),
                own_publish_receipt=binding(publish_path),
                expected_legacy=binding(output/'EXPECTED_PUBLIC_LEGACY.json'),expected_native=binding(output/'EXPECTED_NATIVE_PUBLIC.json'),
                source_legacy_receipt=binding(fresh_source_receipts[0]),source_native_receipt=binding(fresh_source_receipts[1]),
                relation_template=binding(relation_path),
                server_context=binding(output/('FINAL_SERVER_CONTEXT.json'if polls else'SERVER_CONTEXT.json')),
                downloads=[{'filename':r['filename'],'binding':{'path':r['path'],'sha256':r['sha256']},'url':r['url']}for r in downloads.public],
                strict_readback_result=binding(output/'STRICT_DIGEST_READBACK.json'))
            evidence_path=emit('REGISTRATION_EVIDENCE.json',evidence)
            registration=runtime.registration.prepare_registration(root,package,binding(evidence_path))
            registration_path=emit('REGISTRATION_RECEIPT.json',registration)
            runtime.registration.require_registration(root,binding(registration_path))
            rows=runtime.registration.entity_rows(root,binding(registration_path),json.loads(read_regular(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json')))
            rows_path=emit('REGISTRATION_ROWS.json',{'standard':'VRS-METHODS-DIGEST-REGISTRATION-ROWS-PROPOSAL-1','status':'FRESH_CONSUMER_PASS_NOT_SSOT_WRITTEN','registration':binding(registration_path),'rows':rows,'certifies':False})
            result.update(status='PUBLISHED_STRICT_READBACK_PASS',phase='COMPLETE',final_readback_envelope=binding(output/'FINAL_READBACK_ENVELOPE.json'),registration_status='FRESH_CONSUMER_PASS_NOT_SSOT_WRITTEN',registration_receipt=binding(registration_path),registration_rows=binding(rows_path))
    except Exception as exc:
        result.update(status='HOLD_AFTER_PUBLISH'if published else'HOLD',failure=type(exc).__name__+': '+str(exc).replace(token,'[REDACTED_CREDENTIAL]'),next_action='Read-only diagnosis; do not replay any attempted mutation.')
        if hasattr(exc,'report'):emit('FAILED_SERVER_MANAGED_READBACK.json',exc.report)
    checkpoint('FINAL');emit('RESULT.json',result);return result

def execute(root,package,plan_binding,output,token,*,reviewed_driver_sha256):
    """Explicit root invocation, immutable attempt; no credential lookup or CLI."""
    require(sha(__file__)==reviewed_driver_sha256,'REVIEWED_RECOVERY_DRIVER_HASH');root=Path(root).resolve(strict=True);package=Path(package).resolve(strict=True);output=Path(output)
    require(str(root)=='/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0','CANONICAL_ROOT_ONLY');require(package.is_relative_to(root)and not any(p.is_symlink()for p in(package,*package.parents)),'OWN_CANONICAL_PACKAGE')
    _,recovery=bound(root,plan_binding);prepared,plan,context=require_recovery_plan(root,package,recovery);runtime=Runtime(root,plan)
    try:
        pinned={r['name']:r for r in plan['runtime_pins']};rp=pinned['draft_reservation.py'];require(sha(reservation.__file__)==rp['sha256']and Path(reservation.__file__).resolve()==Path(rp['path']).resolve(),'PINNED_RESERVATION_MODULE')
        own=pinned['first_digest_existing_draft.py'];require(own['sha256']==reviewed_driver_sha256 and Path(own['path']).resolve()==Path(__file__).resolve(),'OWN_RECOVERY_DRIVER_SOURCE_CLOSURE')
        globals().update(metadata=runtime.metadata,state=runtime.state,AccountDiscovery=runtime.account.AccountDiscovery,JournalWriter=runtime.journal.JournalWriter,publisher_previews=runtime.previews,publisher_recovery=runtime.recovery)
        return _execute(root,package,recovery,output,token,runtime,account_factory=runtime.account.AccountDiscovery)
    finally:runtime.close()

if __name__=='__main__':raise SystemExit('HOLD: root-only explicit frozen own-draft recovery; no credential lookup, CREATE, retry or CLI execution.')
