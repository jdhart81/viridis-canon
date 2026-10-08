"""Root-only approved ordinary source installation; no automatic operation.

All transport, merge and protected checks are the unchanged frozen v003 helper.
This successor preserves all35 rows during runtime nomination, then requires a
separate exact-reader registration recovery. It issues no scientific verdict.
"""
from pathlib import Path
import copy,datetime as dt,hashlib,json,os,re,sys,types
sys.dont_write_bytecode=True
LEGACY=Path('/private/tmp/phase7-public-state-runtime-installer-20261008-v003/runtime_successor.py')
LEGACY_SHA='99453df4fc6f62cab92e4604765a0ca492a0ad89903a21789a292874c417db5f'
if hashlib.sha256(LEGACY.read_bytes()).hexdigest()!=LEGACY_SHA:raise ValueError('HOLD: frozen install utility differs')
u=types.ModuleType('frozen_install_checks');u.__file__=str(LEGACY);exec(compile(LEGACY.read_bytes(),str(LEGACY),'exec'),u.__dict__)
ROOT=u.ROOT;PREFIX=u.PREFIX;Hold=u.Hold;need=u.need;raw=u.raw;sha=u.sha;digest=u.digest;encoded=u.encoded;binding=u.binding;relative=u.relative;bound=u.bound;save=u.save;immutable=u.immutable;protected=u.protected;merged=u.merged;git_blob=u.git_blob
BUILDER=u.BUILDER;BUILDER_SHA=u.BUILDER_SHA
CURRENT_RUNTIME_SHA='b712f73d8b2b0d8fc87f4ea692b8d4fa0fda8657d9591da97d8a3b246bf7da13'
POLICY_SHA='66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654'
REVIEWED={'corpus_ledger.py':'497aa58f686c48389ef5b4d62e00fa2621cdf45eff45ace4d8e79202076e94cf','registration_imports.py':'37fd17b61a869c8343d5cd035dbbf87f05ed259a9aa3ddb3a5d83da8796fc707','phase7_audit_policy.py':POLICY_SHA,'phase7_policy_versions.py':'9eb67790edfab0760601133a3994dc1dbb24f7aa60c44661804525abf330859f','phase7_runtime_update.py':'7aa7a7920f8be5bdb37e91a3efa56acda689c2a5dd7991953691ae56c9274f42'}
FLAT17=u.FLAT16|{'digest_public_state.py'};ADDED='registration_imports.py';CHANGED={'corpus_ledger.py','phase7_audit_policy.py','phase7_policy_versions.py','phase7_runtime_update.py'};P5=u.P5
ARCHIVE_NAMES={'phase7_audit_policy.py','PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','methods_digest.py','publication_gate.py'}
ARCHIVE={f'policy_versions/{POLICY_SHA}/{n}'for n in ARCHIVE_NAMES};MATERIAL_NAMES=FLAT17|{ADDED}|P5|ARCHIVE
FIELDS=u.FIELDS|{'expected_publication_projection_sha256','reviewed_five_source_freeze'}
CLOSURE_STANDARD='VRS-PHASE7-AUTHORITY-IMPORT-CURRENT-RUNTIME-CLOSURE-1'
CLOSURE_STATUS='ACTUAL_ACTIVATED_RUNTIME_FULL_SOURCE_PROTECTED22_PASS'
CLOSURE_FIELDS={'standard','status','tree_root','source_session','runtime_update','activation','policy_version_catalog','protected_readback','merged_pr','merged_commit','merged_tree','source_origin_proof','source_pins','local_import_edges','identical_own_copies','source_pin_count','historical_runtime_predecessor','consumer_sha256','certifies','zenodo_writes','clean_nights_credited'}
G='publication:methods-digest:2026-W41:23226761'
CHILD_IDS={f'publication:methods-note:2026-W41:Run-{n}'for n in(125,126,128,129,131,134,141)}
REGISTRATION_SHA='d0ece5e1f95536e75952502c6fec15cca5ddcca5e69076b860e5a3c1fb1f496d'
OLD27_PROJECTION='4b32704d10517a62a40ed980b6d524f7c471fe9a778156e6abe42f157ca48959'

def full35(ledger,expected_projection=None):
 rows=ledger.get('publication_entities');need(isinstance(rows,list)and len(rows)==35 and all(isinstance(v,dict)for v in rows)and len({v.get('id')for v in rows})==35,'EXACT_FULL35_POPULATION')
 # Route constants are checked by exact identity and actual receipt binding,
 # without assuming a display spelling for the existing source consumer.
 selected=[v for v in rows if v.get('id')in CHILD_IDS|{G}]
 need(len(selected)==8 and {v['id']for v in selected}==CHILD_IDS|{G},'EXACT_OWN8')
 need(all(isinstance(v.get('registration_receipt'),dict)and v['registration_receipt'].get('sha256')==REGISTRATION_SHA for v in selected),'OWN8_RECEIPT_CHANGED')
 old={v['id']:v for v in rows if v['id']not in CHILD_IDS|{G}}
 need(len(old)==27 and digest(encoded(old))==OLD27_PROJECTION and all(v.get('enforcement_acceptable')is True for v in old.values()),'ALL27_PREDECESSORS_EXACT')
 if expected_projection is not None:need(digest(encoded(rows))==expected_projection,'EXACT_FULL35_PROJECTION')
 return copy.deepcopy(rows)

def inventory(previous,current):
 rows=previous.get('runtime_targets');add=previous.get('additional_modules');need(isinstance(rows,list)and len(rows)==22 and len({r['path']for r in rows})==22,'TARGET22');need(isinstance(add,list)and len(add)==33 and len({r['path']for r in add})==33,'ADDITIONAL33')
 flat={Path(r['path']).name for r in add if '/policy_versions/'not in r['path']};archives=[r for r in add if '/policy_versions/'in r['path']];need(flat==FLAT17 and len(archives)==16,'EXACT_FLAT17_ARCHIVE16');need(set(current)=={r['path']for r in rows+add},'CURRENT55_FILESET')
 for r in rows+add:need(current[r['path']]==r.get('after_sha256',r.get('sha256')),'CURRENT_RUNTIME_BYTES:'+r['path'])
 return rows,add

def prove_materials(previous,current,materials,files):
 need(set(materials)==MATERIAL_NAMES,'EXACT_REVIEWED_MATERIAL_SET')
 for n,h in REVIEWED.items():need(digest(materials[n])==h,'REVIEWED_FIVE_SOURCE:'+n)
 for n in (FLAT17|P5)-CHANGED:need(digest(materials[n])==current[PREFIX+n],'UNCHANGED_EXISTING_SOURCE:'+n)
 for n in CHANGED:need(digest(materials[n])!=current[PREFIX+n],'ACTUAL_CHANGED_SOURCE:'+n)
 for n in ARCHIVE_NAMES:need(materials[f'policy_versions/{POLICY_SHA}/{n}']==materials[n],'THIRD_ARCHIVE_MATCHES_CURRENT:'+n)
 proof=u.source_proof(files,materials)
 for n in ARCHIVE|{ADDED}:need(not(ROOT/(PREFIX+n)).exists()and not(ROOT/(PREFIX+n)).is_symlink(),'ADDITIVE_NAME_COLLISION:'+n)
 return proof

def preflight(config):
 need(isinstance(config,dict)and set(config)==FIELDS and config['standard']=='VRS-PHASE7-AUTHORITY-IMPORT-RUNTIME-SUCCESSOR-CONFIG-1'and config['canonical_root']==str(ROOT),'CLOSED_CONFIG');need(sha(__file__)==config['reviewed_driver_sha256'],'REVIEWED_DRIVER')
 out=Path(config['output']);need(out.is_absolute()and out.resolve().is_relative_to(ROOT/'reports/verification-coverage')and not out.exists()and not any(q.is_symlink()for q in(out,*out.parents)),'UNUSED_CANONICAL_OUTPUT')
 ssot=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before=raw(ssot);need(digest(before)==config['expected_ssot_sha256'],'SSOT_CAS');ledger=json.loads(before);rows=full35(ledger,config['expected_publication_projection_sha256']);need(ledger['premise_declaration_cutover_run']=='Run-188','CUTOVER188')
 _,b=bound(ledger['enforcement_activation']);activation=json.loads(b);_,b=bound(config['predecessor_runtime']);need(config['predecessor_runtime']==activation['authorized_runtime_update']and digest(b)==CURRENT_RUNTIME_SHA,'EXACT_CURRENT_PREDECESSOR');previous=json.loads(b);_,b=bound(previous['original_activation']);original=json.loads(b);need({k:v for k,v in activation.items()if k!='authorized_runtime_update'}==original,'ORIGINAL_ACTIVATION_FIELDS')
 current={r['path']:sha(ROOT/r['path'])for r in previous['runtime_targets']+previous['additional_modules']};inventory(previous,current)
 for r in previous['runtime_targets']+previous['additional_modules']:_,b=bound(r['source']);need(b==raw(ROOT/r['path']),'CURRENT_SOURCE_AUTHORITY')
 _,prraw=bound(config['merged_pr'],outside=True);_,comraw=bound(config['merged_commit'],outside=True);_,treeraw=bound(config['merged_tree'],outside=True);pr=json.loads(prraw);files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],json.loads(comraw),json.loads(treeraw))
 need(set(config['source_hashes'])==MATERIAL_NAMES,'CLOSED_SOURCE_HASH_TABLE');materials={n:raw(Path(config['source_gates'])/n)for n in MATERIAL_NAMES}
 for n,b in materials.items():need(digest(b)==config['source_hashes'][n],'CONFIG_SOURCE_HASH:'+n)
 proof=prove_materials(previous,current,materials,files)
 _,f=bound(config['reviewed_five_source_freeze'],outside=True);freeze=json.loads(f);frows=freeze.get('files');need(isinstance(frows,dict),'CLOSED_FIVE_SOURCE_FREEZE')
 for n,h in REVIEWED.items():need(frows.get(n,{}).get('sha256')==h,'FIVE_SOURCE_REVIEW_FREEZE:'+n)
 _,reviewraw=bound(config['reviewed_source_proof'],outside=True);review=json.loads(reviewraw);need(review.get('status')=='REVIEWED_APPROVED_AUTHORITY_IMPORT_SOURCE_ONLY_PASS'and review.get('source_hashes')==REVIEWED and review.get('protected_verifier_changed')is False and review.get('scientific_acceptance_changed')is False,'INDEPENDENT_ORDINARY_SOURCE_REVIEW')
 _,b=bound(config['live_protected_before']);protected_before=json.loads(b);protected(protected_before);need(raw(ssot)==before,'SSOT_CHANGED_DURING_PREFLIGHT');normalized=copy.deepcopy(pr);normalized['files']=[{'path':r['path'],'sha':r['sha']}for r in proof]
 return {'config':copy.deepcopy(config),'out':out,'before_raw':before,'ledger':ledger,'rows':rows,'activation':activation,'previous':previous,'original':original,'current':current,'materials':materials,'prraw':prraw,'comraw':comraw,'treeraw':treeraw,'normalized_pr':normalized,'proof':proof,'protected_before':protected_before}

def unchanged(p,current=None):
 need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==p['before_raw'],'SSOT_CHANGED')
 for path,h in (current or p['current']).items():need(sha(ROOT/path)==h,'LIVE_RUNTIME_CHANGED:'+path)
 for n,b in p['materials'].items():need(raw(Path(p['config']['source_gates'])/n)==b,'MERGED_SOURCE_CHANGED:'+n)

def install(config,*,reviewed_driver_sha256):
 need(sha(__file__)==reviewed_driver_sha256==config['reviewed_driver_sha256'],'REVIEWED_INSTALL_DRIVER');p=preflight(config);out=p['out'];out.mkdir(parents=True,exist_ok=False)
 save(out/'CONFIG.json',config);immutable(out/'BEFORE_LEDGER.json',p['before_raw']);save(out/'BEFORE_FULL35_PUBLICATIONS.json',p['rows']);save(out/'BEFORE_ACTIVATION.json',p['activation']);immutable(out/'RAW_PR_MERGED_READBACK.json',p['prraw']);immutable(out/'MERGED_COMMIT.json',p['comraw']);immutable(out/'COMPLETE_MERGED_TREE.json',p['treeraw']);save(out/'PR_MERGED_READBACK.json',p['normalized_pr']);save(out/'SOURCE_ORIGIN_PROOF.json',{'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':p['proof']})
 save(out/'INSTALL_INTENT_NOT_PASS.json',{'status':'INSTALLING_APPROVED_ORDINARY_SOURCES_NOT_ADMISSION','runtime_writes_planned':13,'publication_rows':'ALL35_EXACT_INCLUDING_EXISTING_HOLDS','ssot_writes':0,'zenodo_writes':0,'certifies':False})
 try:
  for path in p['current']:immutable(out/'before'/path,raw(ROOT/path))
  for n,b in p['materials'].items():immutable(out/'reviewed-source'/n,b)
  expected=copy.deepcopy(p['current']);unchanged(p)
  for n in sorted(CHANGED|{ADDED}|ARCHIVE):
   unchanged(p,expected);live=ROOT/(PREFIX+n);new=n not in CHANGED;need(not new or(not live.exists()and not live.is_symlink()),'ADDITIVE_COLLISION_BEFORE_WRITE');live.parent.mkdir(parents=True,exist_ok=True);candidate=live.with_name('.'+live.name+'.phase7-authority-import-pending');immutable(candidate,p['materials'][n]);os.chmod(candidate,live.stat().st_mode&0o777 if live.exists()else 0o644);need(raw(candidate)==p['materials'][n],'CANDIDATE_SOURCE_READBACK');unchanged(p,expected);need(not new or not live.exists(),'ADDITIVE_COLLISION_BEFORE_REPLACE');os.replace(candidate,live);need(raw(live)==p['materials'][n],'INSTALLED_SOURCE_READBACK');expected[PREFIX+n]=digest(p['materials'][n])
  installed=dt.datetime.now(dt.timezone.utc).isoformat();targets=copy.deepcopy(p['previous']['runtime_targets']);additional=copy.deepcopy(p['previous']['additional_modules'])
  for n in sorted(CHANGED|{ADDED}|ARCHIVE):
   q=out/'after'/n;immutable(q,raw(ROOT/(PREFIX+n)))
   if n=='corpus_ledger.py':targets=[{**r,'after_sha256':sha(q),'source':relative(q)}if r['path']==PREFIX+n else r for r in targets]
   else:
    row={'path':PREFIX+n,'sha256':sha(q),'source':relative(q)}
    additional=[row if r['path']==row['path']else r for r in additional]if n in CHANGED else additional+[row]
  need(len(targets)==22 and len(additional)==42,'ACTUAL22_ADDITIONAL42');unchanged(p,expected)
  _,b=bound(p['previous']['policy_version_catalog']);catalog=json.loads(b);need(len(catalog['versions'])==2 and all(r['execution_consumer_sha256']!=POLICY_SHA for r in catalog['versions']),'TWO_UNCHANGED_ARCHIVES')
  entry={'execution_consumer_sha256':POLICY_SHA,'files':[{'name':n,'binding':{'path':PREFIX+f'policy_versions/{POLICY_SHA}/{n}','sha256':digest(p['materials'][f'policy_versions/{POLICY_SHA}/{n}'])},'git_path':'00_lab_infrastructure/gates/'+f'policy_versions/{POLICY_SHA}/{n}'}for n in sorted(ARCHIVE_NAMES)],'pull_request_readback':relative(out/'PR_MERGED_READBACK.json')};newcatalog=copy.deepcopy(catalog);newcatalog['versions'].append(entry);save(out/'POLICY_VERSION_CATALOG.json',newcatalog)
  pending={'standard':'VRS-PHASE7-AUTHORITY-IMPORT-RUNTIME-INSTALLED-PENDING-1','status':'INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS','installed_at_utc':installed,'predecessor_ssot_sha256':digest(p['before_raw']),'predecessor_activation':p['ledger']['enforcement_activation'],'publication_entities':p['rows'],'cutover':'Run-188','previous_runtime_contents':p['previous'],'runtime_targets':targets,'additional_modules':additional,'policy_version_catalog':relative(out/'POLICY_VERSION_CATALOG.json'),'pull_request_readback':relative(out/'PR_MERGED_READBACK.json'),'live_protected_before':config['live_protected_before'],'driver_sha256':reviewed_driver_sha256,'runtime_writes':13,'ssot_writes':0,'zenodo_writes':0,'protected_verifier_changed':False,'certifies':False};save(out/'INSTALLED_AWAITING_CLOSURE.json',pending);return pending
 except Exception as exc:
  save(out/'INSTALL_HOLD.json',{'status':'HOLD_PARTIAL_INSTALL_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')!=p['before_raw'],'no_automatic_retry':True,'certifies':False});raise

def load_builder():
 need(sha(BUILDER)==BUILDER_SHA,'UNCHANGED_REVIEWED_SOURCE_SESSION');return u.module(BUILDER,'unchanged_phase7_source_session')

def pin_table(builder):
 ledger=json.loads(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'));_,b=bound(ledger['enforcement_activation']);wrapper=json.loads(b);_,b=bound(wrapper['authorized_runtime_update']);update=json.loads(b);_,b=bound(update['original_activation']);original=json.loads(b)
 need(update['profile']=='PHASE7_SCOPED_POLICY'and len(update['runtime_targets'])==22 and len(update['additional_modules'])==42,'CURRENT_MEASURED22_42');gates=ROOT/PREFIX;pipeline=ROOT/'RESEARCH_PIPELINE_v2';seeds=[]
 for r in update['runtime_targets']+update['additional_modules']:
  p,_=bound({'path':r['path'],'sha256':r.get('after_sha256',r.get('sha256'))})
  if p.suffix=='.py'and '/policy_versions/'not in str(p):seeds.append(p)
 seeds.extend(p for p in gates.glob('*.py')if not p.name.startswith('test_'));seeds.append(pipeline/'nightly_proof_track.py');extras=[p for p,h in builder.APPROVED_HELPERS.values()];seeds.extend(extras)
 required={'registration_imports.py','digest_public_state.py','methods_digest_registration.py','corpus_ledger.py','phase7_runtime_update.py','phase7_policy_versions.py','mirror_parity.py','publication_gate.py','certificate_inspection.py','publication_preservation.py'}
 pins,edges,duplicates=builder.collect_closure(ROOT,seeds,[gates,pipeline,ROOT/'_ZENODO_DEPOSITS'],extra_sources=extras,required=required);_,b=bound(update['policy_version_catalog']);catalog=json.loads(b)
 for entry in catalog['versions']:
  for row in entry['files']:
   p,_=bound(row['binding'])
   if p.suffix=='.py':pins.append({'name':'archive_'+entry['execution_consumer_sha256']+'_'+p.name,'path':str(p),'sha256':sha(p)})
 need(len({r['name']for r in pins})==len(pins),'UNIQUE_SOURCE_PINS');return ledger,update,original,pins,edges,duplicates

def current_closure(out,protected_binding):
 out=Path(out).resolve(strict=True);config=json.loads(raw(out/'CONFIG.json'));pr=json.loads(raw(out/'RAW_PR_MERGED_READBACK.json'));files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],json.loads(raw(out/'MERGED_COMMIT.json')),json.loads(raw(out/'COMPLETE_MERGED_TREE.json')));materials={n:raw(ROOT/(PREFIX+n))for n in MATERIAL_NAMES}
 for n,b in materials.items():need(digest(b)==config['source_hashes'][n],'CURRENT_SOURCE_DIFFERS_FROM_MERGE:'+n)
 proof=u.source_proof(files,materials);need(json.loads(raw(out/'SOURCE_ORIGIN_PROOF.json'))=={'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':proof},'ACTUAL_SOURCE_PROOF_CHANGED');builder=load_builder();ledger,update,original,pins,edges,duplicates=pin_table(builder)
 with builder.source_session(ROOT,pins):
  import phase7_runtime_update as helper
  actual=helper.validate(ROOT,ledger,original);need(actual['profile']=='PHASE7_SCOPED_POLICY','ACTUAL_NOMINATED_HELPER_PASS');builder.verify_loaded(pins,ROOT)
 _,b=bound(protected_binding);protected(json.loads(b),installed_at=update['installed_at_utc']);need(update['protected_readback']==protected_binding,'NOMINATED_PROTECTED_BINDING')
 return {'standard':CLOSURE_STANDARD,'status':CLOSURE_STATUS,'tree_root':str(ROOT),'source_session':binding(BUILDER),'runtime_update':json.loads(raw(ROOT/ledger['enforcement_activation']['path']))['authorized_runtime_update'],'activation':ledger['enforcement_activation'],'policy_version_catalog':update['policy_version_catalog'],'protected_readback':protected_binding,'merged_pr':relative(out/'RAW_PR_MERGED_READBACK.json'),'merged_commit':relative(out/'MERGED_COMMIT.json'),'merged_tree':relative(out/'COMPLETE_MERGED_TREE.json'),'source_origin_proof':relative(out/'SOURCE_ORIGIN_PROOF.json'),'source_pins':pins,'local_import_edges':edges,'identical_own_copies':duplicates,'source_pin_count':len(pins),'historical_runtime_predecessor':config['predecessor_runtime'],'consumer_sha256':sha(__file__),'certifies':False,'zenodo_writes':0,'clean_nights_credited':0}

def require_current_closure(value):
 p,b=bound(value);v=json.loads(b);need(set(v)==CLOSURE_FIELDS and v['standard']==CLOSURE_STANDARD and v['status']==CLOSURE_STATUS and v['tree_root']==str(ROOT)and v['consumer_sha256']==sha(__file__)and v['certifies']is False and type(v['zenodo_writes'])is int and v['zenodo_writes']==0 and type(v['clean_nights_credited'])is int and v['clean_nights_credited']==0,'CLOSED_ACTUAL_CURRENT_CLOSURE');need(current_closure(p.parent,v['protected_readback'])==v,'ACTUAL_CURRENT_CLOSURE_CHANGED');need(raw(p)==b,'CLOSURE_READ_RACE');return v

def close(output,protected_after_binding,*,reviewed_driver_sha256):
 need(sha(__file__)==reviewed_driver_sha256,'REVIEWED_CLOSE_DRIVER');out=Path(output).resolve(strict=True);need(out.is_relative_to(ROOT/'reports/verification-coverage'),'OWN_CLOSURE_OUTPUT');ledgerpath=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';oldraw=raw(ledgerpath)
 try:
  p=json.loads(raw(out/'INSTALLED_AWAITING_CLOSURE.json'));need(p.get('status')=='INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS'and p['driver_sha256']==reviewed_driver_sha256,'OWN_PENDING_NOT_PASS');need(not any((out/n).exists()for n in('RUNTIME_UPDATE_RECEIPT.json','INSTALL_RECEIPT.json','candidate-validation')),'NO_CLOSE_REPLAY');need(digest(oldraw)==p['predecessor_ssot_sha256'],'CLOSURE_SSOT_CAS');old=json.loads(oldraw);need(full35(old)==p['publication_entities']and old['enforcement_activation']==p['predecessor_activation']and old['premise_declaration_cutover_run']==p['cutover'],'ALL35_AND_CONTROLS_EXACT')
  _,b=bound(p['live_protected_before']);before=json.loads(b);_,b=bound(protected_after_binding);protected(json.loads(b),before,p['installed_at_utc']);previous=p['previous_runtime_contents'];_,b=bound(previous['original_activation']);original=json.loads(b)
  for r in p['runtime_targets']+p['additional_modules']:need(sha(ROOT/r['path'])==r.get('after_sha256',r.get('sha256')),'INSTALLED_CLOSURE_SOURCE')
  with u.fresh_gates()as paths:
   import phase7_runtime_update as helper,corpus_ledger as corpus
   receipt={**previous,'installed_at_utc':p['installed_at_utc'],'pull_request_readback':p['pull_request_readback'],'runtime_targets':p['runtime_targets'],'additional_modules':p['additional_modules'],'policy_version_catalog':p['policy_version_catalog'],'protected_readback':protected_after_binding}
   candidate=out/'candidate-validation';candidate.mkdir(exist_ok=False);save(candidate/'RUNTIME_UPDATE_RECEIPT.json',receipt);cw={**original,'authorized_runtime_update':relative(candidate/'RUNTIME_UPDATE_RECEIPT.json')};save(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',cw);save(candidate/'CANDIDATE_NOT_ACTIVATED.json',{'status':'REAL_MEASURED_CANDIDATE_INPUTS_NOT_ADMISSION','certifies':False,'ssot_writes':0});proposed={**old,'enforcement_activation':relative(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')}
   actual=helper.validate(ROOT,proposed,original);need(actual['profile']=='PHASE7_SCOPED_POLICY','ACTUAL_NEW_RUNTIME_VALIDATION');need(full35(proposed)==p['publication_entities'],'ALL35_PRESERVED_DURING_CANDIDATE_VALIDATION');need(raw(ledgerpath)==oldraw,'SSOT_CHANGED_BEFORE_FINAL_RECEIPT')
   for q,h in paths.values():need(sha(q)==h,'LIVE_SOURCE_CHANGED_BEFORE_FINAL_RECEIPT')
   save(out/'CANDIDATE_VALIDATION.json',{'status':'REAL_NEW_HELPER_PROTECTED22_PASS_NOT_ACTIVATED','actual_helper_result':actual,'all35_rows_exact':True,'publication_registration_recovery':'PENDING_EXPLICIT_DEFAULT_CONSUMER','certifies':False,'ssot_writes':0})
   save(out/'RUNTIME_UPDATE_RECEIPT.json',receipt);wrapper={**original,'authorized_runtime_update':relative(out/'RUNTIME_UPDATE_RECEIPT.json')};save(out/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',wrapper);nomination={**old,'enforcement_activation':relative(out/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')};helper.validate(ROOT,nomination,original);need(full35(nomination)==p['publication_entities'],'NO_MANUAL_STATUS_RECOVERY')
   for q,h in paths.values():need(sha(q)==h,'LIVE_SOURCE_CHANGED_BEFORE_NOMINATION_CAS')
   need(raw(ledgerpath)==oldraw,'SSOT_CHANGED_BEFORE_NOMINATION_CAS');newsha=corpus.write_guarded_ledger(ledgerpath,nomination,p['predecessor_ssot_sha256']);need(sha(ledgerpath)==newsha and full35(json.loads(raw(ledgerpath)))==p['publication_entities'],'NOMINATION_STRICT_READBACK');immutable(out/'AFTER_RUNTIME_NOMINATION_LEDGER.json',raw(ledgerpath))
  closure=current_closure(out,protected_after_binding);save(out/'CURRENT_RUNTIME_CLOSURE.json',closure);require_current_closure(relative(out/'CURRENT_RUNTIME_CLOSURE.json'))
  result={'standard':'VRS-PHASE7-AUTHORITY-IMPORT-RUNTIME-SUCCESSOR-INSTALL-1','status':'INSTALLED_ACTUAL_SOURCE_VALIDATOR_PROTECTED22_PASS_PUBLICATION_RECOVERY_PENDING','current_runtime_closure':relative(out/'CURRENT_RUNTIME_CLOSURE.json'),'runtime_update':relative(out/'RUNTIME_UPDATE_RECEIPT.json'),'activation':nomination['enforcement_activation'],'before_ssot_sha256':p['predecessor_ssot_sha256'],'after_ssot_sha256':newsha,'all35_rows_unchanged':True,'cutover':'Run-188','runtime_targets':22,'additional_modules':42,'runtime_writes':13,'ssot_writes':1,'zenodo_writes':0,'certificates_issued':0,'clean_nights_credited':0,'certifies':False};save(out/'INSTALL_RECEIPT.json',result);return result
 except Exception as exc:
  if not(out/'CLOSURE_HOLD.json').exists():save(out/'CLOSURE_HOLD.json',{'status':'HOLD_CLOSURE_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ledgerpath)!=oldraw,'no_automatic_retry':True,'certifies':False})
  raise
if __name__=='__main__':raise SystemExit('HOLD: explicit root-reviewed configuration and fresh actual merged/protected evidence are required; no automatic operation')
