"""Root-only, source-bound same-concept runtime successor. No automatic action.

The scientific consumers, original protected checks and source-session guard
are unchanged. Installation and nomination are separate explicit operations.
"""
from pathlib import Path
import ast, copy, datetime as dt, hashlib, json, os, re, sys, types
sys.dont_write_bytecode = True
PRIOR = Path('/private/tmp/phase7-authority-import-runtime-successor-20261008-v001/runtime_successor.py')
PRIOR_SHA = 'e0ebe49d167f886f0a159743f177a7963b188a233f03602225979051d3a961d6'
if hashlib.sha256(PRIOR.read_bytes()).hexdigest() != PRIOR_SHA:
    raise ValueError('HOLD: historical runtime utility differs')
e = types.ModuleType('historical_authority_import_runtime'); e.__file__ = str(PRIOR)
exec(compile(PRIOR.read_bytes(), str(PRIOR), 'exec'), e.__dict__)
u = e.u
ROOT=e.ROOT; PREFIX=e.PREFIX; Hold=e.Hold; need=e.need; raw=e.raw; sha=e.sha
digest=e.digest; encoded=e.encoded; binding=e.binding; relative=e.relative
bound=e.bound; save=e.save; immutable=e.immutable; protected=e.protected
merged=e.merged; git_blob=e.git_blob; BUILDER=e.BUILDER; BUILDER_SHA=e.BUILDER_SHA
LEGACY_PUBLIC_SHA = 'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38'
PRIOR_RUNTIME_HELPER_SHA = '7aa7a7920f8be5bdb37e91a3efa56acda689c2a5dd7991953691ae56c9274f42'
NEW_RUNTIME_HELPER_SHA = 'e37ed3d0fe05aa4ecd178c9fb0c3bbec0c49eba203c89bdfa4d2e07ee851e121'
PRIOR_RUNTIME_SHA = '1cbab65bcd3e0b8f02119920ca3390091820052525ed529af7556cf2e95f9849'
PRIOR_CLOSURE_SHA = 'e3b701f657f84050a56d5286ed8b627db65e84b9b043c99c3500dcc65589b744'
PRIOR_RECOVERY_SHA = '20a625a98f879d540b69dea95848ae3c106454ed859e3ad06dd169c200ebc2b5'
REGISTRAR_SHA = '0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9'
METHODS_SHA = '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5'
CODEC_SHA = 'cbd6aa9034e8d2e775c3b2f3226c9c41dbb39ccce1d7a59150ca52414ca8dfb2'
POLICY_SHA = '91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e'
ADDED = {'digest_public_state_legacy_b5545.py', 'digest_successor_state.py', 'first_digest_state.py'}
CHANGED = {'digest_public_state.py', 'phase7_runtime_update.py', 'phase7_audit_policy.py'}
OLD_FLAT = e.FLAT17 | {'registration_imports.py'}
FLAT = OLD_FLAT | ADDED
ARCHIVE_NAMES = e.ARCHIVE_NAMES
ARCHIVE = {f'policy_versions/{POLICY_SHA}/{n}' for n in ARCHIVE_NAMES}
INSTALL_NAMES = CHANGED | ADDED | ARCHIVE
MATERIAL_NAMES = FLAT | e.P5 | ARCHIVE
ADDITIONAL_COUNT = 42 + len(ADDED) + len(ARCHIVE)
RUNTIME_WRITE_COUNT = len(INSTALL_NAMES)
FIELDS = {'standard','canonical_root','output','expected_ssot_sha256',
          'expected_publication_projection_sha256','predecessor_runtime',
          'predecessor_closure','predecessor_registration_recovery',
          'source_gates','source_hashes','merged_pr','expected_head_sha',
          'expected_merge_commit','merged_commit','merged_tree',
          'live_protected_before','reviewed_source_proof','reviewed_driver_sha256'}
CLOSURE_STANDARD = 'VRS-PHASE7-SAME-CONCEPT-CURRENT-RUNTIME-CLOSURE-1'
CLOSURE_STATUS = 'ACTUAL_ACTIVATED_RUNTIME_FULL_SOURCE_PROTECTED22_PASS'
CLOSURE_FIELDS = e.CLOSURE_FIELDS | {'historical_runtime_closure','historical_registration_recovery'}

def exact(left, right):
    return encoded(left) == encoded(right)

def closed_relative_binding(value):
    # Fail before any candidate write if a caller supplies an absolute path.
    need(isinstance(value,dict) and set(value)=={'path','sha256'},'CLOSED_RELATIVE_BINDING')
    p=value.get('path'); h=value.get('sha256')
    need(isinstance(p,str) and bool(p) and not Path(p).is_absolute()
         and '..' not in Path(p).parts and str(Path(p))==p
         and isinstance(h,str) and re.fullmatch('[a-f0-9]{64}',h) is not None,
         'CANONICAL_RELATIVE_BINDING')
    target,b=bound(value); need(target.resolve(strict=True).is_relative_to(ROOT),'RELATIVE_ROOT_ESCAPE')
    return target,b

def full35(ledger, expected_projection=None):
    rows=e.full35(ledger, expected_projection)
    need(all(v.get('enforcement_acceptable') is True for v in rows),'ALL35_ACTUAL_ACCEPTABLE')
    need(ledger.get('premise_declaration_cutover_run')=='Run-188','CUTOVER188')
    return rows

def inventory(previous, current):
    rows=previous.get('runtime_targets'); additional=previous.get('additional_modules')
    need(isinstance(rows,list) and len(rows)==22 and len({r.get('path') for r in rows})==22,'EXACT22')
    need(isinstance(additional,list) and len(additional)==42 and len({r.get('path') for r in additional})==42,'EXACT42')
    flat={Path(r['path']).name for r in additional if '/policy_versions/' not in r['path']}
    archives=[r for r in additional if '/policy_versions/' in r['path']]
    need(flat==OLD_FLAT and len(archives)==24,'EXACT18_FLAT24_ARCHIVES')
    need(set(current)=={r['path'] for r in rows+additional},'EXACT64_PREDECESSOR_FILES')
    for r in rows+additional:
        need(current[r['path']]==r.get('after_sha256',r.get('sha256')),'PREDECESSOR_BYTES:'+r['path'])
    return rows,additional

def namespace_only_delta(before, after):
    need(digest(before)==PRIOR_RUNTIME_HELPER_SHA and digest(after)==NEW_RUNTIME_HELPER_SHA,'EXACT_RUNTIME_HELPER_PINS')
    old=ast.parse(before); new=ast.parse(after)
    def split(tree):
        rows=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POLICY_MODULE_NAMES' for t in n.targets)]
        need(len(rows)==1,'UNIQUE_NAMESPACE_ASSIGNMENT')
        n=rows[0]; need(isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='frozenset' and len(n.value.args)==1 and not n.value.keywords,'CLOSED_NAMESPACE_EXPRESSION')
        names=ast.literal_eval(n.value.args[0]); need(isinstance(names,set) and all(isinstance(x,str) for x in names),'STRING_NAMESPACE_NAMES')
        return names,[ast.dump(v,include_attributes=False) for v in tree.body if v is not n]
    oldnames,oldbody=split(old); newnames,newbody=split(new)
    need(oldnames==OLD_FLAT and newnames==oldnames|ADDED and oldbody==newbody,'NAMESPACE_ONLY_EXACT_THREE_NAMES')
    return {'status':'CLOSED_THREE_NAME_NAMESPACE_ONLY_PASS','added':sorted(ADDED),'all_original_functions_and_other_globals_identical':True}

def prove_materials(current, materials, files):
    need(set(materials)==MATERIAL_NAMES,'EXACT_SOURCE_MATERIAL_SET')
    for n in (OLD_FLAT|e.P5)-CHANGED:
        need(digest(materials[n])==current[PREFIX+n],'UNCHANGED_EXISTING_SOURCE:'+n)
    need(digest(materials['digest_public_state_legacy_b5545.py'])==LEGACY_PUBLIC_SHA
         and digest(materials['digest_public_state_legacy_b5545.py'])==current[PREFIX+'digest_public_state.py'],
         'EXACT_LEGACY_PUBLIC_BYTES')
    namespace_only_delta(raw(ROOT/(PREFIX+'phase7_runtime_update.py')),materials['phase7_runtime_update.py'])
    need(digest(materials['digest_public_state.py'])!=LEGACY_PUBLIC_SHA,'ACTUAL_DISPATCHER_SUCCESSOR')
    need(digest(materials['first_digest_state.py'])==CODEC_SHA,'EXACT_REVIEWED_CODEC')
    need(digest(materials['phase7_audit_policy.py'])==POLICY_SHA,'EXACT_REUSE_RESOLVER_POLICY')
    for n in ARCHIVE_NAMES:
        need(materials[f'policy_versions/{POLICY_SHA}/{n}']==materials[n],'EXACT_FOURTH_ARCHIVE_CURRENT:'+n)
    for n in ADDED|ARCHIVE:
        q=ROOT/(PREFIX+n);need(not q.exists() and not q.is_symlink(),'ADDITIVE_COLLISION:'+n)
    return u.source_proof(files,materials)

def expected_catalog(previous, materials, pr_binding):
    need(isinstance(previous,dict) and isinstance(previous.get('versions'),list)
         and len(previous['versions'])==3
         and len({r.get('execution_consumer_sha256') for r in previous['versions']})==3
         and all(r.get('execution_consumer_sha256')!=POLICY_SHA for r in previous['versions']),
         'EXACT_THREE_PREDECESSOR_CATALOG_ENTRIES')
    for n in ARCHIVE_NAMES:
        need(materials[f'policy_versions/{POLICY_SHA}/{n}']==materials[n],
             'FOURTH_ARCHIVE_CURRENT_BYTES:'+n)
    entry={'execution_consumer_sha256':POLICY_SHA,
           'files':[{'name':n,'binding':{'path':PREFIX+f'policy_versions/{POLICY_SHA}/{n}',
                   'sha256':digest(materials[f'policy_versions/{POLICY_SHA}/{n}'])},
                   'git_path':'00_lab_infrastructure/gates/'+f'policy_versions/{POLICY_SHA}/{n}'}
                  for n in sorted(ARCHIVE_NAMES)],'pull_request_readback':pr_binding}
    result=copy.deepcopy(previous);result['versions'].append(entry)
    need(exact(result['versions'][:-1],previous['versions']),'ALL_PREDECESSOR_CATALOG_ROWS_EXACT')
    return result

def preflight(config):
    need(isinstance(config,dict) and set(config)==FIELDS and config['standard']=='VRS-PHASE7-SAME-CONCEPT-RUNTIME-SUCCESSOR-CONFIG-1' and config['canonical_root']==str(ROOT),'CLOSED_CONFIG')
    need(sha(__file__)==config['reviewed_driver_sha256'],'REVIEWED_DRIVER')
    out=Path(config['output']); need(out.is_absolute() and out.resolve().is_relative_to(ROOT/'reports/verification-coverage') and not out.exists() and not any(q.is_symlink() for q in(out,*out.parents)),'UNUSED_CANONICAL_OUTPUT')
    ssot=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'; before=raw(ssot)
    need(digest(before)==config['expected_ssot_sha256'],'SSOT_CAS'); ledger=json.loads(before)
    rows=full35(ledger,config['expected_publication_projection_sha256'])
    _,b=closed_relative_binding(ledger['enforcement_activation']);activation=json.loads(b)
    _,b=closed_relative_binding(config['predecessor_runtime']);previous=json.loads(b)
    need(config['predecessor_runtime']==activation['authorized_runtime_update'] and digest(b)==PRIOR_RUNTIME_SHA,'EXACT_PREDECESSOR_RUNTIME')
    _,b=closed_relative_binding(previous['original_activation']);original=json.loads(b)
    need(exact({k:v for k,v in activation.items() if k!='authorized_runtime_update'},original),'ORIGINAL_ACTIVATION_EXACT')
    _,b=closed_relative_binding(config['predecessor_closure']);need(digest(b)==PRIOR_CLOSURE_SHA,'EXACT_HISTORICAL_CLOSURE')
    historical=e.require_current_closure(config['predecessor_closure'])
    need(historical['activation']==ledger['enforcement_activation'] and historical['runtime_update']==config['predecessor_runtime'],'CURRENT_ACTIVATED_PREDECESSOR')
    _,b=closed_relative_binding(config['predecessor_registration_recovery']);recovery=json.loads(b)
    need(digest(b)==PRIOR_RECOVERY_SHA and recovery.get('status')=='EXPLICIT_DEFAULT_READER8_FRESH35_CAS_READBACK_PASS' and recovery.get('after_ssot_sha256')==digest(before) and recovery.get('unchanged_registrar_sha256')==REGISTRAR_SHA and recovery.get('all35_fresh_scan_and_replay_acceptable') is True,'GENUINE_CURRENT35_RECOVERY')
    current={r['path']:sha(ROOT/r['path']) for r in previous['runtime_targets']+previous['additional_modules']};inventory(previous,current)
    for r in previous['runtime_targets']+previous['additional_modules']:
        _,b=closed_relative_binding(r['source']);need(b==raw(ROOT/r['path']),'CURRENT_SOURCE_AUTHORITY')
    _,b=closed_relative_binding(previous['policy_version_catalog']);catalog=json.loads(b)
    need(len(catalog.get('versions',[]))==3,'EXACT_THREE_ARCHIVES')
    _,prraw=bound(config['merged_pr'],outside=True);_,comraw=bound(config['merged_commit'],outside=True);_,treeraw=bound(config['merged_tree'],outside=True)
    pr=json.loads(prraw);files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],json.loads(comraw),json.loads(treeraw))
    need(set(config['source_hashes'])==MATERIAL_NAMES,'CLOSED_SOURCE_HASH_TABLE')
    materials={n:raw(Path(config['source_gates'])/n) for n in MATERIAL_NAMES}
    for n,b in materials.items():need(digest(b)==config['source_hashes'][n],'CONFIG_SOURCE_HASH:'+n)
    proof=prove_materials(current,materials,files)
    _,b=bound(config['reviewed_source_proof'],outside=True);review=json.loads(b)
    changes={n:config['source_hashes'][n] for n in CHANGED|ADDED}
    need(review.get('status')=='REVIEWED_CLOSED_SAME_CONCEPT_RUNTIME_SOURCE_ONLY_PASS' and exact(review.get('source_hashes'),changes) and review.get('protected_verifier_changed') is False and review.get('scientific_acceptance_changed') is False and review.get('legacy_public_state_sha256')==LEGACY_PUBLIC_SHA,'INDEPENDENT_REVIEW')
    _,b=closed_relative_binding(config['live_protected_before']);pb=json.loads(b);protected(pb)
    need(raw(ssot)==before,'SSOT_CHANGED_DURING_PREFLIGHT')
    normalized=copy.deepcopy(pr);normalized['files']=[{'path':r['path'],'sha':r['sha']} for r in proof]
    return {'config':copy.deepcopy(config),'out':out,'before_raw':before,'ledger':ledger,'rows':rows,'activation':activation,'original':original,'previous':previous,'current':current,'materials':materials,'proof':proof,'prraw':prraw,'comraw':comraw,'treeraw':treeraw,'normalized_pr':normalized,'protected_before':pb}

def unchanged(p, current=None):
    need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==p['before_raw'],'SSOT_CHANGED')
    for path,h in (current or p['current']).items():need(sha(ROOT/path)==h,'RUNTIME_BYTES_CHANGED:'+path)
    for n,b in p['materials'].items():need(raw(Path(p['config']['source_gates'])/n)==b,'MERGED_SOURCE_CHANGED:'+n)

def install(config, *, reviewed_driver_sha256):
    need(sha(__file__)==reviewed_driver_sha256==config['reviewed_driver_sha256'],'REVIEWED_INSTALL_DRIVER')
    p=preflight(config);out=p['out'];out.mkdir(parents=True,exist_ok=False)
    save(out/'CONFIG.json',config);immutable(out/'BEFORE_LEDGER.json',p['before_raw']);save(out/'BEFORE_FULL35_PUBLICATIONS.json',p['rows']);save(out/'BEFORE_ACTIVATION.json',p['activation'])
    immutable(out/'RAW_PR_MERGED_READBACK.json',p['prraw']);immutable(out/'MERGED_COMMIT.json',p['comraw']);immutable(out/'COMPLETE_MERGED_TREE.json',p['treeraw']);save(out/'PR_MERGED_READBACK.json',p['normalized_pr']);save(out/'SOURCE_ORIGIN_PROOF.json',{'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':p['proof']})
    save(out/'INSTALL_INTENT_NOT_PASS.json',{'status':'INSTALLING_CLOSED_ORDINARY_SOURCES_NOT_ADMISSION','runtime_writes_planned':RUNTIME_WRITE_COUNT,'all35_rows':'EXACT_CURRENT_PASS_ROWS_PRESERVED','ssot_writes':0,'zenodo_writes':0,'certifies':False})
    try:
        for path in p['current']:immutable(out/'before'/path,raw(ROOT/path))
        for n,b in p['materials'].items():immutable(out/'reviewed-source'/n,b)
        expected=copy.deepcopy(p['current'])
        for n in sorted(INSTALL_NAMES):
            unchanged(p,expected);live=ROOT/(PREFIX+n);new=n not in CHANGED
            need(not new or(not live.exists() and not live.is_symlink()),'ADDITIVE_COLLISION_BEFORE_WRITE')
            live.parent.mkdir(parents=True,exist_ok=True)
            candidate=live.with_name('.'+live.name+'.phase7-same-concept-pending')
            immutable(candidate,p['materials'][n]);os.chmod(candidate,live.stat().st_mode&0o777 if live.exists() else 0o644)
            need(raw(candidate)==p['materials'][n],'CANDIDATE_CHANGED');unchanged(p,expected)
            need(not new or(not live.exists() and not live.is_symlink()),'ADDITIVE_COLLISION_BEFORE_REPLACE')
            os.replace(candidate,live);need(raw(live)==p['materials'][n],'INSTALLED_SOURCE_READBACK');expected[PREFIX+n]=digest(p['materials'][n])
        installed=dt.datetime.now(dt.timezone.utc).isoformat();additional=copy.deepcopy(p['previous']['additional_modules'])
        for n in sorted(INSTALL_NAMES):
            q=out/'after-additional'/n;immutable(q,raw(ROOT/(PREFIX+n)));row={'path':PREFIX+n,'sha256':sha(q),'source':relative(q)}
            additional=[row if r['path']==row['path'] else r for r in additional] if n in CHANGED else additional+[row]
        need(len(additional)==ADDITIONAL_COUNT,'ACTUAL_ADDITIONAL_SUCCESSOR');unchanged(p,expected)
        _,old_catalog_bytes=closed_relative_binding(p['previous']['policy_version_catalog'])
        old_catalog=json.loads(old_catalog_bytes)
        catalog=expected_catalog(old_catalog,p['materials'],relative(out/'PR_MERGED_READBACK.json'))
        save(out/'POLICY_VERSION_CATALOG.json',catalog)
        pending={'standard':'VRS-PHASE7-SAME-CONCEPT-RUNTIME-INSTALLED-PENDING-1','status':'INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS','installed_at_utc':installed,'predecessor_ssot_sha256':digest(p['before_raw']),'predecessor_activation':p['ledger']['enforcement_activation'],'publication_entities':p['rows'],'cutover':'Run-188','previous_runtime_contents':p['previous'],'runtime_targets':copy.deepcopy(p['previous']['runtime_targets']),'additional_modules':additional,'policy_version_catalog':relative(out/'POLICY_VERSION_CATALOG.json'),'pull_request_readback':relative(out/'PR_MERGED_READBACK.json'),'live_protected_before':config['live_protected_before'],'driver_sha256':reviewed_driver_sha256,'runtime_writes':RUNTIME_WRITE_COUNT,'ssot_writes':0,'zenodo_writes':0,'protected_verifier_changed':False,'certifies':False}
        save(out/'INSTALLED_AWAITING_CLOSURE.json',pending);return pending
    except Exception as exc:
        save(out/'INSTALL_HOLD.json',{'status':'HOLD_PARTIAL_INSTALL_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')!=p['before_raw'],'no_automatic_retry':True,'certifies':False});raise

def load_builder():
    need(sha(BUILDER)==BUILDER_SHA,'UNCHANGED_SOURCE_SESSION');return u.module(BUILDER,'same_concept_unchanged_source_session')

def pin_table(builder, ledger=None):
    ledger=json.loads(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')) if ledger is None else ledger
    _,b=closed_relative_binding(ledger['enforcement_activation']);activation=json.loads(b)
    _,b=closed_relative_binding(activation['authorized_runtime_update']);update=json.loads(b)
    _,b=closed_relative_binding(update['original_activation']);original=json.loads(b)
    need(update['profile']=='PHASE7_SCOPED_POLICY' and len(update['runtime_targets'])==22 and len(update['additional_modules'])==ADDITIONAL_COUNT,'MEASURED22_ADDITIONAL_SUCCESSOR')
    gates=ROOT/PREFIX;pipeline=ROOT/'RESEARCH_PIPELINE_v2';seeds=[]
    for r in update['runtime_targets']+update['additional_modules']:
        p,_=closed_relative_binding({'path':r['path'],'sha256':r.get('after_sha256',r.get('sha256'))})
        if p.suffix=='.py' and '/policy_versions/' not in str(p):seeds.append(p)
    seeds.extend(p for p in gates.glob('*.py') if not p.name.startswith('test_'));seeds.append(pipeline/'nightly_proof_track.py')
    extras=[p for p,h in builder.APPROVED_HELPERS.values()];seeds.extend(extras)
    required={'registration_imports.py','digest_public_state.py','digest_public_state_legacy_b5545.py','digest_successor_state.py','first_digest_state.py','methods_digest_registration.py','corpus_ledger.py','phase7_runtime_update.py','phase7_policy_versions.py','mirror_parity.py','publication_gate.py','certificate_inspection.py','publication_preservation.py'}
    pins,edges,duplicates=builder.collect_closure(ROOT,seeds,[gates,pipeline,ROOT/'_ZENODO_DEPOSITS'],extra_sources=extras,required=required)
    _,b=closed_relative_binding(update['policy_version_catalog']);catalog=json.loads(b);need(len(catalog['versions'])==4,'FOUR_ARCHIVES_CLOSED')
    for entry in catalog['versions']:
        for row in entry['files']:
            p,_=closed_relative_binding(row['binding'])
            if p.suffix=='.py':pins.append({'name':'archive_'+entry['execution_consumer_sha256']+'_'+p.name,'path':str(p),'sha256':sha(p)})
    need(len({r['name'] for r in pins})==len(pins),'UNIQUE_SOURCE_PINS')
    return ledger,update,original,pins,edges,duplicates

def current_closure(output, protected_binding):
    output=Path(output).resolve(strict=True);config=json.loads(raw(output/'CONFIG.json'))
    for key,h in (('predecessor_runtime',PRIOR_RUNTIME_SHA),('predecessor_closure',PRIOR_CLOSURE_SHA),('predecessor_registration_recovery',PRIOR_RECOVERY_SHA)):
        _,b=closed_relative_binding(config[key]);need(digest(b)==h,'HISTORICAL_BOUND_INPUT_CHANGED:'+key)
    pr=json.loads(raw(output/'RAW_PR_MERGED_READBACK.json'));files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],json.loads(raw(output/'MERGED_COMMIT.json')),json.loads(raw(output/'COMPLETE_MERGED_TREE.json')))
    materials={n:raw(ROOT/(PREFIX+n)) for n in MATERIAL_NAMES}
    for n,b in materials.items():need(digest(b)==config['source_hashes'][n],'CURRENT_SOURCE_DIFFERS_FROM_MERGE:'+n)
    proof=u.source_proof(files,materials);need(exact(json.loads(raw(output/'SOURCE_ORIGIN_PROOF.json')),{'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':proof}),'SOURCE_PROOF_CHANGED')
    normalized=copy.deepcopy(pr);normalized['files']=[{'path':r['path'],'sha':r['sha']} for r in proof]
    need(exact(json.loads(raw(output/'PR_MERGED_READBACK.json')),normalized),'ACTUAL_FULL_TREE_PROJECTION')
    _,prior_bytes=closed_relative_binding(config['predecessor_runtime']);previous=json.loads(prior_bytes)
    _,old_catalog_bytes=closed_relative_binding(previous['policy_version_catalog'])
    need(exact(json.loads(raw(output/'POLICY_VERSION_CATALOG.json')),expected_catalog(json.loads(old_catalog_bytes),materials,relative(output/'PR_MERGED_READBACK.json'))),'CURRENT_CATALOG_SUCCESSOR_CHANGED')
    builder=load_builder();ledger,update,original,pins,edges,duplicates=pin_table(builder)
    with builder.source_session(ROOT,pins):
        import phase7_runtime_update as helper
        actual=helper.validate(ROOT,ledger,original);need(actual['profile']=='PHASE7_SCOPED_POLICY','ACTUAL_CURRENT_HELPER_PASS');builder.verify_loaded(pins,ROOT)
    _,b=closed_relative_binding(protected_binding);protected(json.loads(b),installed_at=update['installed_at_utc']);need(update['protected_readback']==protected_binding,'NOMINATED_PROTECTED_BINDING')
    return {'standard':CLOSURE_STANDARD,'status':CLOSURE_STATUS,'tree_root':str(ROOT),'source_session':binding(BUILDER),'runtime_update':json.loads(raw(ROOT/ledger['enforcement_activation']['path']))['authorized_runtime_update'],'activation':ledger['enforcement_activation'],'policy_version_catalog':update['policy_version_catalog'],'protected_readback':protected_binding,'merged_pr':relative(output/'RAW_PR_MERGED_READBACK.json'),'merged_commit':relative(output/'MERGED_COMMIT.json'),'merged_tree':relative(output/'COMPLETE_MERGED_TREE.json'),'source_origin_proof':relative(output/'SOURCE_ORIGIN_PROOF.json'),'source_pins':pins,'local_import_edges':edges,'identical_own_copies':duplicates,'source_pin_count':len(pins),'historical_runtime_predecessor':config['predecessor_runtime'],'historical_runtime_closure':config['predecessor_closure'],'historical_registration_recovery':config['predecessor_registration_recovery'],'consumer_sha256':sha(__file__),'certifies':False,'zenodo_writes':0,'clean_nights_credited':0}

def read_bound_closure(value):
    """Read a closed pin table for scope composition; not current admission.

    The caller must still invoke require_current_closure, which recomputes the
    actual nominated helper, merged source and protected closure independently.
    """
    p,b=closed_relative_binding(value);v=json.loads(b)
    need(set(v)==CLOSURE_FIELDS and v['standard']==CLOSURE_STANDARD and v['status']==CLOSURE_STATUS and v['tree_root']==str(ROOT) and v['consumer_sha256']==sha(__file__) and v['certifies'] is False and type(v['zenodo_writes']) is int and v['zenodo_writes']==0 and type(v['clean_nights_credited']) is int and v['clean_nights_credited']==0,'CLOSED_ACTUAL_CURRENT_CLOSURE')
    rows=v['source_pins'];need(isinstance(rows,list) and type(v['source_pin_count']) is int
         and v['source_pin_count']==len(rows) and rows
         and all(isinstance(r,dict) and set(r)=={'name','path','sha256'} and isinstance(r['name'],str)
                 and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*[.]py',r['name']) is not None
                 and isinstance(r['path'],str) and Path(r['path']).is_absolute()
                 and isinstance(r['sha256'],str) and re.fullmatch('[a-f0-9]{64}',r['sha256']) is not None for r in rows)
         and len({r['name'] for r in rows})==len(rows),'CLOSED_MEASURED_SOURCE_PIN_TABLE')
    need(raw(p)==b,'BOUND_CLOSURE_READ_RACE');return v

def require_current_closure(value):
    p,b=closed_relative_binding(value);v=read_bound_closure(value)
    need(exact(current_closure(p.parent,v['protected_readback']),v),'ACTUAL_CURRENT_CLOSURE_CHANGED');need(raw(p)==b,'CLOSURE_READ_RACE');return v

def fresh35(corpus, ledger, rows, helper, original):
    scanned=corpus.build(ROOT,ROOT/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=ledger)
    need(exact(full35(scanned),rows),'FRESH_ALL35_CHANGED')
    need(exact({k:scanned.get(k) for k in('enforcement_activation','premise_declaration_cutover_run')},{k:ledger.get(k) for k in('enforcement_activation','premise_declaration_cutover_run')}),'FRESH_CONTROLS_CHANGED')
    need(helper.validate(ROOT,scanned,original)['profile']=='PHASE7_SCOPED_POLICY','FRESH_ACTUAL_RUNTIME_VALIDATION');return scanned

def require_pending(config, pending, previous, output):
    fields={'standard','status','installed_at_utc','predecessor_ssot_sha256',
            'predecessor_activation','publication_entities','cutover',
            'previous_runtime_contents','runtime_targets','additional_modules',
            'policy_version_catalog','pull_request_readback','live_protected_before',
            'driver_sha256','runtime_writes','ssot_writes','zenodo_writes',
            'protected_verifier_changed','certifies'}
    need(isinstance(pending,dict) and set(pending)==fields and
         pending['standard']=='VRS-PHASE7-SAME-CONCEPT-RUNTIME-INSTALLED-PENDING-1',
         'CLOSED_PENDING_SCHEMA')
    need(exact(pending['previous_runtime_contents'],previous) and
         exact(pending['runtime_targets'],previous['runtime_targets']),
         'UNCHANGED22_AND_PREDECESSOR')
    need(pending['driver_sha256']==config['reviewed_driver_sha256'] and
         pending['predecessor_ssot_sha256']==config['expected_ssot_sha256'] and
         pending['live_protected_before']==config['live_protected_before'] and
         pending['protected_verifier_changed'] is False and pending['certifies'] is False,
         'PENDING_AUTHORITY')
    for key,value in (('runtime_writes',RUNTIME_WRITE_COUNT),('ssot_writes',0),('zenodo_writes',0)):
        need(type(pending[key]) is int and pending[key]==value,'PENDING_COUNTER:'+key)
    prior={r['path']:r for r in previous['additional_modules']}
    added=pending['additional_modules'];need(isinstance(added,list) and len(added)==ADDITIONAL_COUNT
         and all(isinstance(r,dict) and set(r)=={'path','sha256','source'} for r in added),
         'CLOSED_ADDITIONAL_SUCCESSOR')
    actual={r['path']:r for r in added};need(len(actual)==ADDITIONAL_COUNT and set(actual)==set(prior)|{PREFIX+n for n in ADDED|ARCHIVE},'EXACT_ADDITIONAL_SUCCESSOR')
    for path,row in prior.items():
        if path not in {PREFIX+n for n in CHANGED}:
            need(exact(actual[path],row),'UNCHANGED_ADDITIONAL_SOURCE:'+path)
    original_output=Path(config['output'])
    for n in INSTALL_NAMES:
        q=original_output/'after-additional'/n
        _,b=closed_relative_binding(actual[PREFIX+n]['source'])
        need(actual[PREFIX+n]['source']==relative(q) and digest(b)==config['source_hashes'][n]
             and actual[PREFIX+n]['sha256']==config['source_hashes'][n],
             'EXACT_INSTALLED_REVIEWED_SOURCE:'+n)
    _,old_catalog_bytes=closed_relative_binding(previous['policy_version_catalog'])
    _,new_catalog_bytes=closed_relative_binding(pending['policy_version_catalog'])
    need(pending['policy_version_catalog']==relative(original_output/'POLICY_VERSION_CATALOG.json'),'OWN_SUCCESSOR_CATALOG_BINDING')
    materials={n:raw(ROOT/actual[PREFIX+n]['source']['path']) for n in INSTALL_NAMES}
    prior_sources={r['path']:r for r in previous['runtime_targets']+previous['additional_modules']}
    for n in ARCHIVE_NAMES-{ 'phase7_audit_policy.py' }:
        _,materials[n]=closed_relative_binding(prior_sources[PREFIX+n]['source'])
    need(exact(json.loads(new_catalog_bytes),expected_catalog(json.loads(old_catalog_bytes),materials,pending['pull_request_readback'])),'APPEND_ONLY_EXACT_FOURTH_CATALOG')
    _,b=closed_relative_binding(pending['pull_request_readback'])
    need(b==raw(Path(output)/'PR_MERGED_READBACK.json'),'PENDING_OWN_MERGED_PROJECTION')
    return pending

def close(output, protected_after_binding, *, reviewed_driver_sha256):
    need(sha(__file__)==reviewed_driver_sha256,'REVIEWED_CLOSE_DRIVER')
    closed_relative_binding(protected_after_binding)
    output=Path(output).resolve(strict=True);need(output.is_relative_to(ROOT/'reports/verification-coverage'),'OWN_CANONICAL_OUTPUT')
    ledgerpath=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';oldraw=raw(ledgerpath)
    try:
        pending=json.loads(raw(output/'INSTALLED_AWAITING_CLOSURE.json'))
        need(pending.get('status')=='INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS' and pending.get('driver_sha256')==reviewed_driver_sha256,'OWN_PENDING_NOT_PASS')
        need(not any((output/n).exists() for n in('RUNTIME_UPDATE_RECEIPT.json','INSTALL_RECEIPT.json','candidate-validation')),'NO_CLOSE_REPLAY')
        need(digest(oldraw)==pending['predecessor_ssot_sha256'],'CLOSURE_SSOT_CAS');old=json.loads(oldraw)
        need(exact(full35(old),pending['publication_entities']) and old['enforcement_activation']==pending['predecessor_activation'] and old['premise_declaration_cutover_run']==pending['cutover'],'FULL35_AND_CONTROLS_EXACT')
        _,b=closed_relative_binding(pending['live_protected_before']);before=json.loads(b)
        _,b=closed_relative_binding(protected_after_binding);protected(json.loads(b),before,pending['installed_at_utc'])
        config=json.loads(raw(output/'CONFIG.json'));_,b=closed_relative_binding(config['predecessor_runtime'])
        need(digest(b)==PRIOR_RUNTIME_SHA,'EXACT_CLOSE_PREDECESSOR_RUNTIME')
        previous=json.loads(b);require_pending(config,pending,previous,output)
        _,b=closed_relative_binding(previous['original_activation']);original=json.loads(b)
        for r in pending['runtime_targets']+pending['additional_modules']:need(sha(ROOT/r['path'])==r.get('after_sha256',r.get('sha256')),'INSTALLED_CLOSURE_BYTES')
        with u.fresh_gates() as paths:
            import phase7_runtime_update as helper, corpus_ledger as corpus
            receipt={**previous,'installed_at_utc':pending['installed_at_utc'],'pull_request_readback':pending['pull_request_readback'],'runtime_targets':pending['runtime_targets'],'additional_modules':pending['additional_modules'],'policy_version_catalog':pending['policy_version_catalog'],'protected_readback':protected_after_binding}
            need(receipt['policy_version_catalog']==pending['policy_version_catalog'],'OWN_FOURTH_ARCHIVE_CATALOG')
            candidate=output/'candidate-validation';candidate.mkdir(exist_ok=False)
            save(candidate/'RUNTIME_UPDATE_RECEIPT.json',receipt);save(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',{**original,'authorized_runtime_update':relative(candidate/'RUNTIME_UPDATE_RECEIPT.json')})
            save(candidate/'CANDIDATE_NOT_ACTIVATED.json',{'status':'UNNOMINATED_CANDIDATE_INPUTS_NOT_ADMISSION','certifies':False,'ssot_writes':0})
            proposed={**old,'enforcement_activation':relative(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')}
            actual=helper.validate(ROOT,proposed,original);need(actual['profile']=='PHASE7_SCOPED_POLICY','ACTUAL_NEW_RUNTIME_VALIDATION')
            scanned=fresh35(corpus,proposed,pending['publication_entities'],helper,original)
            for q,h in paths.values():need(sha(q)==h,'SOURCE_CHANGED_BEFORE_FINAL_RECEIPT')
            need(raw(ledgerpath)==oldraw,'SSOT_CHANGED_BEFORE_FINAL_RECEIPT')
            save(output/'CANDIDATE_VALIDATION.json',{'status':'REAL_NEW_HELPER_FRESH35_AND_PROTECTED22_PASS_NOT_ACTIVATED','all35_rows_exact':True,'certifies':False,'ssot_writes':0})
            save(output/'RUNTIME_UPDATE_RECEIPT.json',receipt);save(output/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',{**original,'authorized_runtime_update':relative(output/'RUNTIME_UPDATE_RECEIPT.json')})
            nomination={**old,'enforcement_activation':relative(output/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')}
            fresh35(corpus,nomination,pending['publication_entities'],helper,original)
            for q,h in paths.values():need(sha(q)==h,'SOURCE_CHANGED_BEFORE_NOMINATION_CAS')
            need(raw(ledgerpath)==oldraw,'SSOT_CHANGED_BEFORE_NOMINATION_CAS')
            newsha=corpus.write_guarded_ledger(ledgerpath,nomination,pending['predecessor_ssot_sha256'])
            need(sha(ledgerpath)==newsha and exact(json.loads(raw(ledgerpath)),nomination),'NOMINATION_STRICT_READBACK')
            replay=fresh35(corpus,json.loads(raw(ledgerpath)),pending['publication_entities'],helper,original)
            immutable(output/'AFTER_RUNTIME_NOMINATION_LEDGER.json',raw(ledgerpath));save(output/'POST_CAS_FRESH35_REPLAY.json',replay)
        closure=current_closure(output,protected_after_binding);save(output/'CURRENT_RUNTIME_CLOSURE.json',closure);require_current_closure(relative(output/'CURRENT_RUNTIME_CLOSURE.json'))
        result={'standard':'VRS-PHASE7-SAME-CONCEPT-RUNTIME-SUCCESSOR-INSTALL-1','status':'INSTALLED_ACTUAL_SOURCE_VALIDATOR_FRESH35_PROTECTED22_PASS','current_runtime_closure':relative(output/'CURRENT_RUNTIME_CLOSURE.json'),'runtime_update':relative(output/'RUNTIME_UPDATE_RECEIPT.json'),'activation':nomination['enforcement_activation'],'before_ssot_sha256':pending['predecessor_ssot_sha256'],'after_ssot_sha256':newsha,'all35_rows_unchanged':True,'original_controls_unchanged':True,'cutover':'Run-188','runtime_targets':22,'additional_modules':ADDITIONAL_COUNT,'runtime_writes':RUNTIME_WRITE_COUNT,'ssot_writes':1,'zenodo_writes':0,'certificates_issued':0,'clean_nights_credited':0,'certifies':False}
        save(output/'INSTALL_RECEIPT.json',result);return result
    except Exception as exc:
        if not(output/'CLOSURE_HOLD.json').exists():save(output/'CLOSURE_HOLD.json',{'status':'HOLD_CLOSURE_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ledgerpath)!=oldraw,'no_automatic_retry':True,'certifies':False})
        raise

if __name__=='__main__':
    raise SystemExit('HOLD: root must supply exact reviewed merged-source configuration and fresh protected readbacks; no automatic operation')
