"""Explicit root-only composition of existing publication consumers.

No credential, HTTP, certificate, runtime, scheduler, or catalog deployment.
register_once is a preserving SSOT CAS, explicitly invoked only after publish.
Catalog preparation is a proposal; unchanged ordinary rebuild is required
after root installs the exact data/config and before deployment.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib, json, os, re, sys, types
from pathlib import Path

ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
CHECKS = {'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}
CONFIG_FIELDS = {'standard','canonical_root','plan','publication_result','expected_ssot_sha256','invoker','merged_pr','merged_commit','merged_tree','git_path'}
STANDARD = 'VRS-GENERIC-DIGEST-PRESERVING-POSTPUBLICATION-1'

def need(value, reason):
    if not value: raise ValueError('HOLD_POSTPUBLICATION_' + reason)

def encoded(value):
    return json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n'

def exact(left,right): return encoded(left)==encoded(right)
def digest(data): return hashlib.sha256(data).hexdigest()
def raw(path):
    p=Path(path);need(p.is_absolute() and p.is_file() and not any(q.is_symlink() for q in (p,*p.parents)),'REGULAR_INPUT')
    a=p.stat();data=p.read_bytes();z=p.stat();need((a.st_ino,a.st_mtime_ns,a.st_size)==(z.st_ino,z.st_mtime_ns,z.st_size),'READ_RACE');return data

def binding(path): return {'path':str(Path(path).resolve(strict=True)),'sha256':digest(raw(path))}
def bound(root,value):
    need(isinstance(value,dict) and set(value)=={'path','sha256'} and isinstance(value['path'],str) and re.fullmatch('[0-9a-f]{64}',str(value['sha256'])) is not None,'CLOSED_BINDING')
    p=Path(value['path']);p=p if p.is_absolute() else root/p
    need('..' not in p.parts and p.resolve(strict=True).is_relative_to(root),'OWN_INPUT')
    data=raw(p);need(digest(data)==value['sha256'],'BOUND_HASH');return p,data

def object_value(root,value):
    p,data=bound(root,value);return p,json.loads(data)

def load(root,value,name):
    p,data=bound(root,value);m=types.ModuleType(name);m.__file__=str(p);exec(compile(data,str(p),'exec'),m.__dict__);need(raw(p)==data,'LOAD_RACE');return m

def immutable(path,data):
    p=Path(path);need(not p.exists() and not any(q.is_symlink() for q in (p,*p.parents)),'EXCLUSIVE_OUTPUT');p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
    need(raw(p)==data,'OUTPUT_READBACK')

def row_index(rows):
    need(isinstance(rows,list) and all(isinstance(v,dict) for v in rows),'ROW_TABLE')
    result={v.get('id'):v for v in rows};need(len(result)==len(rows) and all(isinstance(k,str) and k for k in result),'UNIQUE_ROWS');return result

def preserve_controls(before,after):
    for key in ('enforcement_activation','premise_declaration_cutover_run'):
        need(exact(before.get(key),after.get(key)),'CONTROL_CHANGED:'+key)

def append_rows(root,before,rows,receipt):
    """Only append rows returned by the actual default registrar."""
    old=row_index(before.get('publication_entities'));new=row_index(rows)
    need(old and new and not set(old)&set(new),'NEW_ID_COLLISION')
    all_rows=[r for key in ('file_entities','run_entities','publication_entities') for r in before.get(key,[])]
    need(not {v['id'] for v in all_rows}&set(new),'CORPUS_ID_COLLISION')
    old_paths={(root/r['path']).resolve() for r in all_rows};new_paths=[]
    for r in rows:
        path=Path(r['path']);need(not path.is_absolute() and '..' not in path.parts and (root/path).resolve(strict=True).is_relative_to(root),'NEW_PATH')
        new_paths.append((root/path).resolve(strict=True))
        need(exact(r.get('registration_receipt'),receipt) and r.get('enforcement_acceptable') is True and r.get('registration_revalidated') is True and r.get('publication_registration_status')=='PASS','DEFAULT_NEW_ROW_HOLD')
    need(len(set(new_paths))==len(new_paths) and not old_paths&set(new_paths),'PATH_COLLISION')
    groups=[r for r in rows if r.get('entity_type')=='METHODS_DIGEST_GROUP'];notes=[r for r in rows if r.get('entity_type')=='METHODS_DIGEST_NOTE']
    need(len(groups)==1 and len(notes)+1==len(rows) and notes,'ONE_GROUP_NONEMPTY_NOTES')
    g=groups[0];need(g.get('certifies') is False and g.get('certificate_valid') is False and g.get('note_ids')==[r['id'] for r in notes],'NO_AGGREGATE_CERTIFICATE')
    need(all(r.get('group_id')==g['id'] and r.get('certifies')=='LISTED_NOTE_SCOPE_ONLY' for r in notes),'EXACT_CHILD_SCOPE')
    result=deepcopy(before);result['publication_entities'].extend(deepcopy(rows));preserve_controls(before,result);return result

def check_scan(before,rows,scanned):
    old=row_index(before['publication_entities']);new=row_index(rows);actual=row_index(scanned.get('publication_entities'))
    need(set(actual)==set(old)|set(new),'COMPLETE_SCAN_MEMBERSHIP')
    need(all(exact(actual[k],v) for k,v in old.items()),'PRIOR_FULL_ROW_CHANGED')
    need(all(exact(actual[k],v) for k,v in new.items()),'NEW_FULL_ROW_CHANGED')
    need(all(v.get('enforcement_acceptable') is True for v in actual.values()),'CURRENT_REGISTRATION_HOLD');preserve_controls(before,scanned)
    return {'old_rows':len(old),'new_rows':len(new),'total_rows':len(actual),'old_full_projection_sha256':digest(encoded(old)),'new_full_projection_sha256':digest(encoded(new))}

def verify_config(root,config):
    need(root==ROOT.resolve(strict=True) and isinstance(config,dict) and set(config)==CONFIG_FIELDS and config['standard']==STANDARD and config['canonical_root']==str(root),'CLOSED_ACTUAL_CONFIG')
    need(config['invoker']==binding(__file__),'EXACT_INVOKER')
    _,pr=object_value(root,config['merged_pr']);_,commit=object_value(root,config['merged_commit']);_,tree=object_value(root,config['merged_tree'])
    need(pr.get('state')=='MERGED' and pr.get('baseRefName')=='main' and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr.get('number')) and pr.get('mergeCommit',{}).get('oid')==commit.get('sha') and commit.get('tree',{}).get('sha')==tree.get('sha') and tree.get('truncated') is False,'OWN_COMPLETE_MERGE')
    checks=pr.get('statusCheckRollup');need(isinstance(checks,list) and CHECKS<={v.get('name') for v in checks if v.get('status')=='COMPLETED' and v.get('conclusion')=='SUCCESS'} and all(v.get('status')=='COMPLETED' and v.get('conclusion') in {'SUCCESS','SKIPPED'} for v in checks),'EXACT_HEAD_CHECKS')
    nodes=tree.get('tree');need(isinstance(nodes,list) and len({v.get('path') for v in nodes})==len(nodes),'UNIQUE_TREE')
    node=next((v for v in nodes if v.get('path')==config['git_path']),{})
    data=raw(__file__);blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    need(node.get('sha')==blob and node.get('type')=='blob' and node.get('mode') in {'100644','100755'},'OWN_MERGED_COMPOSITION_SOURCE')

def require_current_in_source_session(root,plan,current,invoke):
    """Use the existing exact runtime view inside the measured purpose session."""
    pins=[r for r in plan['purpose_source_pins'] if r['name']=='runtime_closure_view.py']
    need(len(pins)==1,'UNIQUE_RUNTIME_VIEW_SOURCE')
    with invoke.session(root,plan):
        view=load(root,{k:pins[0][k] for k in ('path','sha256')},'_exact_postpublish_runtime_view')
        return view.require_current(current,plan['current_runtime_closure'],root=root,purpose_pins=plan['purpose_source_pins'])

def register_once(config,output):
    """Explicit preserving CAS. Never calls a Zenodo write or a verifier."""
    root=ROOT.resolve(strict=True);verify_config(root,config);out=Path(output)
    need(out.is_absolute() and out.resolve().is_relative_to(root/'reports/verification-coverage') and not out.exists(),'NEW_OWN_ATTEMPT')
    _,plan=object_value(root,config['plan']);_,result=object_value(root,config['publication_result'])
    need(result.get('status')=='PUBLISHED_STRICT_READBACK_PASS' and result.get('published') is True and result.get('ssot_writes')==0 and result.get('plan')==config['plan'],'ACTUAL_POSTPUBLISH_RESULT')
    invoke_pin=next(v for v in plan['purpose_source_pins'] if v['name']=='invoke_weekly_digest.py');invoke=load(root,{k:invoke_pin[k] for k in ('path','sha256')},'_exact_postpublish_source_session')
    current=load(root,plan['runtime_consumer'],'_exact_postpublish_current_runtime');require_current_in_source_session(root,plan,current,invoke)
    ssot=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before_raw=raw(ssot);need(digest(before_raw)==config['expected_ssot_sha256'],'FRESH_SSOT_CAS');before=json.loads(before_raw)
    input_bytes={str(bound(root,config[k])[0]):bound(root,config[k])[1] for k in ('plan','publication_result','merged_pr','merged_commit','merged_tree')}
    out.mkdir(parents=True,exist_ok=False);immutable(out/'BEFORE_LEDGER.json',before_raw)
    with invoke.session(root,plan):
        import weekly_digest_executor as engine,owned_digest_machine as machine,methods_digest_registration as registrar,corpus_ledger as corpus,weekly_digest_runtime as live
        live.require_origin(root,plan['source_origin'],plan['purpose_source_pins']);engine.require_plan(root,plan)
        _,state=engine.bound(root,result['checkpoint']);machine.validate(state,machine.digest(plan));need(state['phase']=='PUBLISHED' and state['published'] is True and state['record_id']==result['record_id'] and state['concept_id']==result['concept_id'],'ACTUAL_TERMINAL_STATE')
        _,report=engine.bound(root,state['last_validation']);need(report.get('step')=='PUBLISH' and report.get('record_id')==state['record_id'] and report.get('transport')==state['attempts'][-1]['transport'] and state['attempts'][-1]['validation']==state['last_validation'],'OWN_PUBLISH_EVIDENCE')
        receipt=report['registration_receipt'];registered=registrar.require_registration(root,receipt,before);rows=registrar.entity_rows(root,receipt,before)
        need(registered['receipt']['record_id']==state['record_id'] and registered['receipt']['package_path']==str(Path(plan['package']).relative_to(root)) and [v['run_id'] for v in registered['receipt']['children']]==plan['new_run_ids'],'EXACT_PUBLISHED_COHORT')
        # Use the original registrar's own material snapshot/check helpers;
        # do not grant acceptance from our proposal/counts. The SSOT itself
        # has a separate explicit hash CAS and changes exactly once.
        materials={};registrar._object(root,receipt,materials)
        package=Path(plan['package']);manifest,pub=registrar.current_digest(package,root)
        registrar._snapshot_digest(root,package,manifest,pub,materials)
        _,evidence=registrar._object(root,registered['receipt']['public_evidence'],materials)
        registrar._check_public(package,root,manifest,evidence,materials,digest_consumer=registrar.current_digest,strict_consumer=registrar.d.strict_readback)
        materials.pop(str(ssot),None)
        for key in (result['checkpoint'],state['last_validation']):
            path,data=bound(root,key);input_bytes[str(path)]=data
        staged=append_rows(root,before,rows,receipt);fresh=corpus.build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=staged);projection=check_scan(before,rows,fresh)
        need(raw(ssot)==before_raw,'PREWRITE_SSOT_RACE');verify_config(root,config)
        for p,data in input_bytes.items():need(raw(p)==data,'PREWRITE_INPUT_RACE')
        registrar._finish(materials)
        live.require_origin(root,plan['source_origin'],plan['purpose_source_pins'])
        immutable(out/'FRESH_ROWS.json',encoded(rows));immutable(out/'PREWRITE_PROJECTION.json',encoded(projection))
        newsha=corpus.write_guarded_ledger(ssot,fresh,config['expected_ssot_sha256']);after_raw=raw(ssot);need(digest(after_raw)==newsha,'CAS_READBACK');immutable(out/'AFTER_LEDGER.json',after_raw)
        after=json.loads(after_raw);rescanned=corpus.build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=after);projection=check_scan(before,rows,rescanned);registrar.require_registration(root,receipt,after);registrar._finish(materials);live.require_origin(root,plan['source_origin'],plan['purpose_source_pins'])
    # Full default re-read and clean source-session exit precede terminal seal.
    require_current_in_source_session(root,plan,current,invoke);verify_config(root,config)
    for p,data in input_bytes.items():need(raw(p)==data,'FINAL_INPUT_RACE')
    registrar._finish(materials)
    need(raw(ssot)==after_raw,'FINAL_SSOT_RACE')
    report={'standard':STANDARD,'status':'PRESERVING_REGISTRATION_FRESH_RESCAN_PASS','before_sha256':config['expected_ssot_sha256'],'after_sha256':newsha,'projection':projection,'registration_receipt':receipt,'publication_result':config['publication_result'],'current_runtime_closure':plan['current_runtime_closure'],'old_control_unchanged':True,'ssot_writes':1,'zenodo_writes':0,'certificates_issued':0,'clean_nights_credited':0,'certifies':False}
    immutable(out/'RESULT.json',encoded(report));return report

def whole_catalog_guard(before,after,groups):
    """Preserve every prior non-digest field and the exact prior digest prefix."""
    left={k:v for k,v in before.items() if k not in {'catalog_digest','methods_digests'}};right={k:v for k,v in after.items() if k not in {'catalog_digest','methods_digests'}}
    need(exact(left,right),'PRIOR_CATALOG_FIELD_CHANGED');old=before.get('methods_digests',[])
    need(exact(after.get('methods_digests'),groups) and exact(groups[:len(old)],old) and len(groups)>len(old),'EXACT_ADDITIVE_DIGEST_PREFIX')
    return {'prior_groups':len(old),'new_groups':len(groups)-len(old),'prior_record_count':len(before['records']),'prior_publication_count':len(before['publications']),'prior_non_digest_fields_exact':True,'prior_digest_prefix_exact':True,'certifies':False}

def catalog_projection(before,groups,ledger_raw,provenance,*,snapshot_name):
    """Proposal only; groups must come from fresh registered_digest_pointers."""
    need(before.get('catalog_digest')==provenance.fingerprint({k:v for k,v in before.items() if k!='catalog_digest'}),'PRIOR_CATALOG_DIGEST')
    candidate=deepcopy(before);candidate['methods_digests']=deepcopy(groups)
    prior=before.get('coverage_provenance');need(isinstance(prior,dict),'EXISTING_CATALOG_PROVENANCE')
    header=provenance.construct_provenance(candidate,ledger_raw,historical_name=prior['historical_snapshot']['name'],current_name=snapshot_name,prior_header=prior)
    candidate['coverage_provenance']=header;candidate['catalog_digest']=provenance.fingerprint({k:v for k,v in candidate.items() if k!='catalog_digest'})
    audit=provenance.audit_additive_update(before,candidate,header,ledger_raw,whole_catalog_guard)
    return candidate,audit

def checkout_materials(root,checkout,tree_binding):
    """Close ordinary renderer/consumer source bytes to the actual merged tree."""
    checkout=Path(checkout).resolve(strict=True);_,tree=object_value(root,tree_binding)
    mapping={v['path']:v for v in tree['tree']};need(len(mapping)==len(tree['tree']) and tree.get('truncated') is False,'COMPLETE_CATALOG_SOURCE_TREE')
    names={'scripts/generate_public_index.py','scripts/methods_digest_index.py'}
    for directory in ('canon_core','00_lab_infrastructure/gates'):
        names.update(p.relative_to(checkout).as_posix() for p in (checkout/directory).iterdir() if p.is_file() and p.suffix=='.py' and not p.name.startswith('test_'))
    table={}
    for name in sorted(names):
        data=raw(checkout/name);node=mapping.get(name,{})
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        need(node.get('type')=='blob' and node.get('mode') in {'100644','100755'} and node.get('sha')==blob,'OWN_CATALOG_SOURCE_BLOB:'+name)
        table[name]=digest(data)
    return table

def checkout_baselines(root,checkout,tree_binding):
    """Exact before data/config/joins, separate from unchanged code materials."""
    checkout=Path(checkout).resolve(strict=True);_,tree=object_value(root,tree_binding)
    nodes=tree.get('tree');need(isinstance(nodes,list) and tree.get('truncated') is False,'COMPLETE_PRIOR_CATALOG_TREE')
    mapping={v['path']:v for v in nodes};need(len(mapping)==len(nodes),'UNIQUE_PRIOR_CATALOG_TREE')
    names={'catalog/config.json','docs/data/catalog.json'};config=json.loads(raw(checkout/'catalog/config.json'))
    for field in ('publication_joins','methods_digest_joins'):
        source=config.get(field)
        if source is None:continue
        need(isinstance(source,dict) and set(source)=={'path','sha256'},'EXACT_PRIOR_CATALOG_JOIN:'+field)
        relative=Path(source['path']);need(not relative.is_absolute() and '..' not in relative.parts,'OWN_PRIOR_CATALOG_JOIN:'+field)
        need(digest(raw(checkout/relative))==source['sha256'],'BOUND_PRIOR_CATALOG_JOIN:'+field);names.add(relative.as_posix())
    proof={}
    for name in sorted(names):
        data=raw(checkout/name);node=mapping.get(name,{})
        blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        need(node.get('type')=='blob' and node.get('mode') in {'100644','100755'} and node.get('sha')==blob,'OWN_PRIOR_CATALOG_DATA_BLOB:'+name)
        proof[name]={'sha256':digest(data),'git_blob_sha':blob}
    return proof

def verify_checkout_loaded(checkout,table):
    for name,module in tuple(sys.modules.items()):
        if not (name=='canon_core' or name.startswith('canon_core.') or name in {'scripts.methods_digest_index','scripts.generate_public_index'}):continue
        origin=getattr(module,'__file__',None);need(isinstance(origin,str),'DECLARED_CATALOG_MODULE:'+name)
        path=Path(origin);need(path.is_absolute() and path.resolve(strict=True).is_relative_to(checkout),'FOREIGN_CATALOG_MODULE:'+name)
        relative=path.relative_to(checkout).as_posix();need(relative in table and digest(raw(path))==table[relative],'CATALOG_SOURCE_CHANGED:'+name)

def prepare_catalog(config,checkout,output):
    """Fresh real default pointer projection, TMP candidates only; no deploy."""
    root=ROOT.resolve(strict=True);verify_config(root,config);checkout=Path(checkout).resolve(strict=True);out=Path(output)
    need(out.is_absolute() and out.resolve().is_relative_to(Path('/private/tmp')) and not out.exists(),'NEW_TMP_CATALOG_OUTPUT')
    _,plan=object_value(root,config['plan'])
    invoke_pin=next(r for r in plan['purpose_source_pins'] if r['name']=='invoke_weekly_digest.py');invoke=load(root,{k:invoke_pin[k] for k in ('path','sha256')},'_exact_catalog_source_session')
    current=load(root,plan['runtime_consumer'],'_exact_current_catalog_runtime');require_current_in_source_session(root,plan,current,invoke)
    ssot=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_raw=raw(ssot);need(digest(ledger_raw)==config['expected_ssot_sha256'],'CURRENT_CATALOG_SSOT_HASH');ledger=json.loads(ledger_raw)
    before_path=checkout/'docs/data/catalog.json';config_path=checkout/'catalog/config.json';before_raw=raw(before_path);config_raw=raw(config_path);before=json.loads(before_raw);original_config=json.loads(config_raw)
    materials=checkout_materials(root,checkout,config['merged_tree'])
    baselines=checkout_baselines(root,checkout,config['merged_tree'])
    need(digest(before_raw)==baselines['docs/data/catalog.json']['sha256'] and digest(config_raw)==baselines['catalog/config.json']['sha256'],'EXACT_PRIOR_DATA_CONFIG_READS')
    old_path=sys.path[:]
    try:
        sys.path.insert(0,str(checkout))
        with invoke.session(root,plan):
            import weekly_digest_executor as engine,weekly_digest_runtime as live
            live.require_origin(root,plan['source_origin'],plan['purpose_source_pins'])
            engine.require_plan(root,plan)
            pointers=importlib.import_module('scripts.methods_digest_index');provenance=importlib.import_module('canon_core.coverage_provenance')
            verify_checkout_loaded(checkout,materials)
            groups,failures=pointers.registered_digest_pointers(root,ledger);need(not failures,'CURRENT_DEFAULT_DIGEST_POINTER_HOLD')
            candidate,audit=catalog_projection(before,groups,ledger_raw,provenance,snapshot_name='corpus-ledger-current-'+digest(ledger_raw))
            second,second_failures=pointers.registered_digest_pointers(root,ledger);need(not second_failures and exact(groups,second),'CURRENT_CATALOG_COHORT_CHANGED')
            verify_checkout_loaded(checkout,materials)
    finally:sys.path[:]=old_path
    require_current_in_source_session(root,plan,current,invoke);verify_config(root,config)
    need(raw(ssot)==ledger_raw and raw(before_path)==before_raw and raw(config_path)==config_raw,'CATALOG_INPUT_RACE')
    need(checkout_materials(root,checkout,config['merged_tree'])==materials,'CATALOG_SOURCE_RACE')
    need(checkout_baselines(root,checkout,config['merged_tree'])==baselines,'PRIOR_CATALOG_DATA_CONFIG_RACE')
    original_config['coverage_provenance']=candidate['coverage_provenance']
    # Root chooses a new repository-relative join filename and binds this exact
    # packet in config before the unchanged ordinary rebuild. Existing packets
    # and their evidence stay immutable; no checkout file is written here.
    packet={'standard':'PUBLIC_METHODS_DIGEST_POINTERS_1','methods_digests':groups}
    out.mkdir(parents=True,exist_ok=False)
    immutable(out/'PROPOSED_CATALOG.json',encoded(candidate));immutable(out/'METHODS_DIGESTS.json',encoded(packet));immutable(out/'CONFIG_WITH_APPENDED_PROVENANCE.json',encoded(original_config))
    report={'standard':'VRS-GENERIC-DIGEST-CATALOG-PROPOSAL-1','status':'FRESH_DEFAULT_COHORT_PROPOSAL_NOT_REBUILT_OR_DEPLOYED','before_catalog_sha256':digest(before_raw),'before_config_sha256':digest(config_raw),'current_ssot_sha256':digest(ledger_raw),'current_runtime_closure':plan['current_runtime_closure'],'materials':materials,'before_data_config_proof':baselines,'preservation':audit,'proposed_catalog':binding(out/'PROPOSED_CATALOG.json'),'digest_packet':binding(out/'METHODS_DIGESTS.json'),'provenance_config':binding(out/'CONFIG_WITH_APPENDED_PROVENANCE.json'),'required_next':['exact join packet/config root install','unchanged ordinary full rebuild and validators','exact-head reviewed data PR merge','public strict catalog readback'],'checkout_writes':0,'ssot_writes':0,'zenodo_writes':0,'certifies':False}
    immutable(out/'RESULT.json',encoded(report));return report

def require_catalog_rebuild(candidate,checkout,historical_ledger,config_path,catalog,*,materials):
    """Root calls after exact local data/config install, before public deploy."""
    checkout=Path(checkout).resolve(strict=True)
    need(isinstance(materials,dict) and 'canon_core/catalog.py' in materials,'ACTUAL_PREPARED_CATALOG_SOURCE_TABLE')
    need(Path(catalog.__file__).resolve(strict=True)==checkout/'canon_core/catalog.py' and digest(raw(catalog.__file__))==materials['canon_core/catalog.py'],'EXACT_ORDINARY_CATALOG_CONSUMER')
    for name,expected in materials.items():
        if Path(name).suffix=='.py':need(digest(raw(checkout/name))==expected,'ORDINARY_CATALOG_CODE_CHANGED:'+name)
    verify_checkout_loaded(checkout,materials)
    historical_sha=digest(raw(historical_ledger));need(historical_sha=='153503930e19c3971e346f9319bb1eaf109dd8486deda1b9ed5efee7689975db','EXACT_HISTORICAL_CATALOG_BASIS')
    rebuilt=catalog.build_catalog(checkout,config_path=config_path,ledger_path=historical_ledger,source_prefix='viridis-canon',enforce_coverage=False)
    need(exact(rebuilt,candidate),'UNCHANGED_DETERMINISTIC_CATALOG_REBUILD')
    need(catalog.validate_catalog(candidate,root=checkout,config_path=config_path,ledger_path=historical_ledger,source_prefix='viridis-canon')==[],'UNCHANGED_CATALOG_VALIDATOR')
    need(catalog.validate_catalog_sources(candidate,checkout,config_path)==[],'UNCHANGED_COMPLETE_CATALOG_SOURCE_VALIDATOR')
    for name,expected in materials.items():
        if Path(name).suffix=='.py':need(digest(raw(checkout/name))==expected,'ORDINARY_CATALOG_CODE_CHANGED_AFTER_REBUILD:'+name)
    verify_checkout_loaded(checkout,materials)
    return {'status':'UNCHANGED_COMPLETE_CATALOG_REBUILD_PASS','catalog_sha256':digest(encoded(candidate)),'historical_ledger_sha256':historical_sha,'certifies':False}

if __name__=='__main__': raise SystemExit('Explicit reviewed root operation only; no automatic action.')
