"""Explicit root-only ordinary runtime installation and closure; no automatic action."""
from __future__ import annotations
from pathlib import Path
import contextlib,copy,datetime as dt,hashlib,importlib.abc,importlib.util,json,os,re,sys,types
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
PREFIX='RESEARCH_PIPELINE_v2/verification_coverage_gates/'
CURRENT_RUNTIME_SHA='862970c81ce31dabd87687aea6088720c37788757ce5993e548e842168741487'
FLAT16={'PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','closeout_streak.py','digest_metadata.py','inv9_dependency_scope.py','inv9_title_basis.py','methods_digest.py','methods_digest_registration.py','nonvacuity_tier0.py','phase7_audit_policy.py','phase7_claim_label_render.py','phase7_mutation_baseline.py','phase7_policy_versions.py','phase7_runtime_update.py','probe_observations.py','public_metadata_readback.py','scoped_release.py'}
CHANGED={'methods_digest_registration.py','phase7_runtime_update.py'};ADDED='digest_public_state.py';P5={'corpus_ledger.py','nightly_coverage.py','premise_declaration.py','publication_gate.py','doi_audit.py'}
CHECKS={'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}
FIELDS={'standard','canonical_root','output','expected_ssot_sha256','predecessor_runtime','source_gates','source_hashes','merged_pr','expected_head_sha','expected_merge_commit','merged_commit','merged_tree','live_protected_before','reviewed_source_proof','reviewed_driver_sha256'}
class Hold(ValueError):pass
def need(v,r):
 if not v:raise Hold('HOLD_RUNTIME_SUCCESSOR_'+r)
def encoded(v):return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n'
def digest(b):return hashlib.sha256(b).hexdigest()
def raw(p):
 p=Path(p);need(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'REGULAR_UNSYMLINKED_FILE');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'READ_RACE');return b
def sha(p):return digest(raw(p))
def binding(p):return{'path':str(Path(p).resolve(strict=True)),'sha256':sha(p)}
def relative(p):return{'path':str(Path(p).resolve(strict=True).relative_to(ROOT)),'sha256':sha(p)}
def bound(v,*,outside=False):
 need(isinstance(v,dict)and set(v)=={'path','sha256'}and isinstance(v['path'],str)and re.fullmatch('[a-f0-9]{64}',str(v['sha256']))is not None,'CLOSED_BINDING');p=Path(v['path']);p=p if p.is_absolute()else ROOT/p;need(outside or p.resolve(strict=True).is_relative_to(ROOT),'BOUND_ROOT_ESCAPE');b=raw(p);need(digest(b)==v['sha256'],'BOUND_BYTES_CHANGED');return p,b
def immutable(p,b):
 p=Path(p);need(not any(x.is_symlink()for x in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.staged.txt');fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'wb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 if p.suffix=='.json':json.loads(b)
 # Keep the non-JSON sealed staging sidecar as immutable provenance.
 # No fallible cleanup can follow the terminal exclusive link.
 os.link(t,p)
def save(p,v):immutable(p,encoded(v))
def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(raw(p),str(p),'exec'),m.__dict__);return m
def full27(ledger):
 r=ledger.get('publication_entities');need(isinstance(r,list)and len(r)==27 and len({v.get('id')for v in r})==27,'FULL27_ROWS');need(all(v.get('enforcement_acceptable')is True for v in r),'OLD_PUBLIC_SCOPE_HELD');return copy.deepcopy(r)
def protected(value,prior=None,installed_at=None):
 need(value.get('status')=='LIVE_PROTECTED_HASH_READBACK_PASS','PROTECTED_STATUS');rows=value.get('checks');need(isinstance(rows,list)and len(rows)==22 and all(isinstance(r,dict)and r.get('match')is True and r.get('actual_sha256')==r.get('expected_sha256')and re.fullmatch('[a-f0-9]{64}',str(r.get('expected_sha256')))is not None for r in rows),'EXACT_PROTECTED22');identities={(r['surface'],r['path'],r['expected_sha256'])for r in rows};need(len(identities)==22,'PROTECTED_UNIQUE');need(all(type(value.get(k))is int and value[k]==0 for k in('remote_script_writes','restarts','certification_attempts')),'PROTECTED_ACTIONS')
 if prior is not None:need(identities==protected(prior)and value['baseline_sha256']==prior['baseline_sha256'],'PROTECTED_BASELINE_CHANGED')
 if installed_at is not None:
  x=dt.datetime.fromisoformat(value['at_utc'].replace('Z','+00:00'));y=dt.datetime.fromisoformat(installed_at.replace('Z','+00:00'));need(x.tzinfo is not None and y.tzinfo is not None and y<=x<=dt.datetime.now(dt.timezone.utc),'PROTECTED_POSTINSTALL_TIME')
 return identities
def merged(pr,head,merge,commit,tree):
 need(pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr.get('number'))and pr.get('headRefOid')==head and pr.get('mergeCommit',{}).get('oid')==merge,'EXACT_OWN_MERGED_PR');need(re.fullmatch('[a-f0-9]{40}',head)is not None and re.fullmatch('[a-f0-9]{40}',merge)is not None,'ACTUAL_GIT_COMMITS');checks=pr.get('statusCheckRollup');need(isinstance(checks,list)and checks and all(x.get('status')=='COMPLETED'and x.get('conclusion')in{'SUCCESS','SKIPPED'}for x in checks)and CHECKS<={x.get('name')for x in checks if x.get('conclusion')=='SUCCESS'},'EXACT_HEAD_CHECKS');need(commit.get('sha')==merge and commit.get('tree',{}).get('sha')==tree.get('sha'),'MERGE_COMMIT_TREE');need(tree.get('truncated')is False and isinstance(tree.get('tree'),list)and re.fullmatch('[a-f0-9]{40}',str(tree.get('sha')))is not None,'COMPLETE_MERGED_TREE');rows=[x for x in tree['tree']if x.get('type')=='blob'];d={x['path']:x for x in rows};need(len(d)==len(rows),'DUPLICATE_TREE_PATHS');return d
def source_proof(files,materials):
 report=[]
 for name,b in sorted(materials.items()):
  path='00_lab_infrastructure/gates/'+name;need(files.get(path,{}).get('sha')==git_blob(b),'MISSING_ACTUAL_MERGED_BLOB:'+path);report.append({'path':path,'sha':git_blob(b),'sha256':digest(b),'bytes':len(b)})
 return report
def inventory(previous,current):
 rows=previous.get('runtime_targets');add=previous.get('additional_modules');need(isinstance(rows,list)and len(rows)==22 and len({r['path']for r in rows})==22,'TARGET22');need(isinstance(add,list)and len(add)==32 and len({r['path']for r in add})==32,'ADDITIONAL32');flat={Path(r['path']).name for r in add if '/policy_versions/'not in r['path']};archive=[r for r in add if '/policy_versions/'in r['path']];need(flat==FLAT16 and len(archive)==16,'FLAT16_ARCHIVE16');need(set(current)=={r['path']for r in rows+add},'CURRENT54_FILESET')
 for r in rows+add:need(current[r['path']]==r.get('after_sha256',r.get('sha256')),'CURRENT_RUNTIME_BYTES:'+r['path'])
 return rows,add
def preflight(config):
 need(isinstance(config,dict)and set(config)==FIELDS and config['standard']=='VRS-PHASE7-PUBLIC-STATE-RUNTIME-SUCCESSOR-CONFIG-1'and config['canonical_root']==str(ROOT),'CLOSED_CONFIG');need(sha(__file__)==config['reviewed_driver_sha256'],'REVIEWED_DRIVER');out=Path(config['output']);need(out.is_absolute()and out.resolve().is_relative_to(ROOT/'reports/verification-coverage')and not out.exists()and not any(x.is_symlink()for x in(out,*out.parents)),'UNUSED_CANONICAL_OUTPUT');ssot=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before_raw=raw(ssot);need(digest(before_raw)==config['expected_ssot_sha256'],'SSOT_CAS');ledger=json.loads(before_raw);rows=full27(ledger);need(ledger['premise_declaration_cutover_run']=='Run-188','CUTOVER188');ap,ab=bound(ledger['enforcement_activation']);activation=json.loads(ab);rp,rb=bound(config['predecessor_runtime']);need(config['predecessor_runtime']==activation['authorized_runtime_update']and digest(rb)==CURRENT_RUNTIME_SHA,'CURRENT_EXACT_POLICY_PREDECESSOR');previous=json.loads(rb);op,ob=bound(previous['original_activation']);original=json.loads(ob);need({k:v for k,v in activation.items()if k!='authorized_runtime_update'}==original,'ORIGINAL_ACTIVATION_CONTENT');current={r['path']:sha(ROOT/r['path'])for r in previous['runtime_targets']+previous['additional_modules']};inventory(previous,current)
 for r in previous['runtime_targets']+previous['additional_modules']:
  _,b=bound(r['source']);need(b==raw(ROOT/r['path']),'CURRENT_SOURCE_AUTHORITY')
 _,prraw=bound(config['merged_pr'],outside=True);_,comraw=bound(config['merged_commit'],outside=True);_,treeraw=bound(config['merged_tree'],outside=True);pr=json.loads(prraw);commit=json.loads(comraw);tree=json.loads(treeraw);files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],commit,tree);g=Path(config['source_gates']);expected_names=FLAT16|{ADDED}|P5;need(set(config['source_hashes'])==expected_names,'CLOSED_MERGED_SOURCE_NAMES');materials={n:raw(g/n)for n in expected_names}
 for n,b in materials.items():need(re.fullmatch('[a-f0-9]{64}',str(config['source_hashes'][n]))is not None and digest(b)==config['source_hashes'][n],'ACTUAL_REVIEWED_SOURCE_SHA:'+n)
 for n in FLAT16-CHANGED:need(digest(materials[n])==current[PREFIX+n],'UNCHANGED_FLAT:'+n)
 for n in P5:need(digest(materials[n])==current[PREFIX+n],'UNCHANGED_CURRENT_TARGET:'+n)
 need(all(digest(materials[n])!=current[PREFIX+n]for n in CHANGED),'EXACT_TWO_CHANGED_FLAT');need(not(ROOT/(PREFIX+ADDED)).exists(),'ADDITIVE_NAME_COLLISION');proof=source_proof(files,materials);_,sr=bound(config['reviewed_source_proof'],outside=True);review=json.loads(sr);need(review.get('status')=='REVIEWED_EXACT_SOURCE_ONLY_PUBLIC_STATE_CHANGE_PASS'and review.get('source_hashes')=={n:config['source_hashes'][n]for n in CHANGED|{ADDED}}and review.get('protected_verifier_changed')is False and review.get('allowlist_changed')is False,'INDEPENDENT_SOURCE_CHANGE_REVIEW')
 _,pb=bound(config['live_protected_before']);before_protected=json.loads(pb);protected(before_protected);need(raw(ssot)==before_raw,'SSOT_CHANGED_DURING_PREFLIGHT');normalized=copy.deepcopy(pr);normalized['files']=[{'path':x['path'],'sha':x['sha']}for x in proof]
 return {'config':copy.deepcopy(config),'out':out,'before_raw':before_raw,'ledger':ledger,'rows':rows,'activation':activation,'previous':previous,'current':current,'materials':materials,'prraw':prraw,'comraw':comraw,'treeraw':treeraw,'normalized_pr':normalized,'source_origin_proof':proof,'before_protected':before_protected,'review':review}
def unchanged(p):
 need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==p['before_raw'],'SSOT_CHANGED');need(all(sha(ROOT/path)==h for path,h in p['current'].items()),'PREDECESSOR_RUNTIME_CHANGED');need(all(raw(Path(p['config']['source_gates'])/n)==b for n,b in p['materials'].items()),'MERGED_SOURCE_CHANGED')
def install(config,*,reviewed_driver_sha256):
 need(sha(__file__)==reviewed_driver_sha256==config['reviewed_driver_sha256'],'REVIEWED_INSTALL_DRIVER');p=preflight(config);out=p['out'];out.mkdir(parents=True,exist_ok=False);save(out/'CONFIG.json',config);immutable(out/'BEFORE_LEDGER.json',p['before_raw']);save(out/'BEFORE_FULL27_PUBLICATIONS.json',p['rows']);save(out/'BEFORE_ACTIVATION.json',p['activation']);immutable(out/'RAW_PR_MERGED_READBACK.json',p['prraw']);immutable(out/'MERGED_COMMIT.json',p['comraw']);immutable(out/'COMPLETE_MERGED_TREE.json',p['treeraw']);save(out/'PR_MERGED_READBACK.json',p['normalized_pr']);save(out/'SOURCE_ORIGIN_PROOF.json',{'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':p['source_origin_proof'],'unchanged_original_targets':'ORIGINAL_BOUND_SOURCE_AUTHORITY_PRESERVED'})
 save(out/'INSTALL_INTENT_NOT_PASS.json',{'status':'INSTALLING_OWN_REVIEWED_ORDINARY_SOURCES_NOT_ADMISSION','runtime_writes_planned':3,'ssot_writes':0,'zenodo_writes':0,'certifies':False})
 try:
  for path in p['current']:immutable(out/'before'/path,raw(ROOT/path))
  for n,b in p['materials'].items():immutable(out/'reviewed-source'/n,b)
  unchanged(p)
  expected_live=copy.deepcopy(p['current'])
  for n in sorted(CHANGED|{ADDED}):
   live=ROOT/(PREFIX+n)
   need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==p['before_raw'],'SSOT_CHANGED_BEFORE_EACH_RUNTIME_WRITE')
   need(all(sha(ROOT/path)==h for path,h in expected_live.items()),'CURRENT_RUNTIME_CHANGED_BEFORE_EACH_WRITE')
   need(n in CHANGED or(not live.exists()and not live.is_symlink()),'ADDITIVE_COLLISION_BEFORE_WRITE')
   candidate=live.with_name('.'+live.name+'.phase7-public-state-pending');immutable(candidate,p['materials'][n]);os.chmod(candidate,live.stat().st_mode&0o777 if live.exists()else 0o644)
   need(raw(candidate)==p['materials'][n],'CANDIDATE_CHANGED_BEFORE_REPLACE')
   if n in CHANGED:need(sha(live)==expected_live[PREFIX+n],'OLD_RUNTIME_CHANGED_BEFORE_REPLACE')
   else:need(not live.exists()and not live.is_symlink(),'ADDITIVE_COLLISION_BEFORE_REPLACE')
   os.replace(candidate,live);need(raw(live)==p['materials'][n],'INSTALLED_SOURCE_READBACK');expected_live[PREFIX+n]=digest(p['materials'][n])
  installed=dt.datetime.now(dt.timezone.utc).isoformat();newadd=copy.deepcopy(p['previous']['additional_modules'])
  for n in CHANGED|{ADDED}:
   q=out/'after-additional'/n;immutable(q,raw(ROOT/(PREFIX+n)));row={'path':PREFIX+n,'sha256':sha(q),'source':relative(q)}
   if n in CHANGED:newadd=[row if x['path']==row['path']else x for x in newadd]
   else:newadd.append(row)
  need(len(newadd)==33,'NEW_ADDITIONAL33');need(all(sha(ROOT/r['path'])==r['after_sha256']for r in p['previous']['runtime_targets']),'UNCHANGED22_AFTER_INSTALL');need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==p['before_raw'],'SSOT_UNCHANGED_DURING_INSTALL');pending={'standard':'VRS-PHASE7-PUBLIC-STATE-RUNTIME-INSTALLED-PENDING-1','status':'INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS','installed_at_utc':installed,'predecessor_ssot_sha256':digest(p['before_raw']),'predecessor_activation':p['ledger']['enforcement_activation'],'publication_entities':p['rows'],'cutover':'Run-188','previous_runtime_contents':p['previous'],'runtime_targets':p['previous']['runtime_targets'],'additional_modules':newadd,'pull_request_readback':relative(out/'PR_MERGED_READBACK.json'),'live_protected_before':config['live_protected_before'],'driver_sha256':reviewed_driver_sha256,'source_hashes':config['source_hashes'],'runtime_writes':3,'ssot_writes':0,'zenodo_writes':0,'protected_verifier_changed':False,'certifies':False};save(out/'INSTALLED_AWAITING_CLOSURE.json',pending);return pending
 except Exception as exc:
  save(out/'INSTALL_HOLD.json',{'status':'HOLD_PARTIAL_INSTALL_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')!=p['before_raw'],'no_automatic_retry':True,'certifies':False});raise

class Loader(importlib.abc.Loader):
 def __init__(self,p,h):self.p=p;self.h=h
 def create_module(self,s):return None
 def exec_module(self,m):need(sha(self.p)==self.h,'FRESH_SOURCE_IMPORT');m.__file__=str(self.p);exec(compile(raw(self.p),str(self.p),'exec'),m.__dict__);need(sha(self.p)==self.h,'SOURCE_CHANGED_DURING_IMPORT')
class Finder(importlib.abc.MetaPathFinder):
 def __init__(self,paths):self.paths=paths
 def find_spec(self,name,path=None,target=None):
  if name in self.paths:p,h=self.paths[name];return importlib.util.spec_from_loader(name,Loader(p,h),origin=str(p))
BUILDER = Path('/private/tmp/phase7-first-seven-plan-builder-20261007-v003/prepare_first_seven_plan.py')
BUILDER_SHA = 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'
CLOSURE_STANDARD = 'VRS-PHASE7-PUBLIC-STATE-CURRENT-RUNTIME-CLOSURE-1'
CLOSURE_STATUS = 'ACTUAL_ACTIVATED_RUNTIME_FULL_SOURCE_PROTECTED22_PASS'
@contextlib.contextmanager
def fresh_gates():
 gates=ROOT/PREFIX;paths={q.stem:(q,sha(q))for q in gates.glob('*.py')};finder=Finder(paths)
 old={n:sys.modules.get(n)for n in paths}
 for n in paths:sys.modules.pop(n,None)
 sys.path.insert(0,str(gates));sys.meta_path.insert(0,finder)
 try:yield paths
 finally:
  sys.meta_path.remove(finder);sys.path.remove(str(gates))
  for n,m in old.items():
   sys.modules.pop(n,None)
   if m is not None:sys.modules[n]=m

def pin_table(builder):
 before,update,original,seeds=builder.runtime_inputs(ROOT)
 gates=ROOT/PREFIX;pipeline=ROOT/'RESEARCH_PIPELINE_v2'
 seeds.extend(p for p in gates.glob('*.py')if not p.name.startswith('test_'))
 seeds.append(pipeline/'nightly_proof_track.py')
 extras=[x[0]for x in builder.APPROVED_HELPERS.values()];seeds.extend(extras)
 required={'digest_public_state.py','methods_digest_registration.py','corpus_ledger.py','phase7_runtime_update.py','phase7_policy_versions.py','mirror_parity.py','publication_gate.py','certificate_inspection.py','publication_preservation.py'}
 pins,edges,duplicates=builder.collect_closure(ROOT,seeds,[gates,pipeline,ROOT/'_ZENODO_DEPOSITS'],extra_sources=extras,required=required)
 _,raw_catalog=bound(update['policy_version_catalog']);catalog=json.loads(raw_catalog)
 for entry in catalog['versions']:
  for row in entry['files']:
   p,_=bound(row['binding'])
   if p.suffix=='.py':pins.append({'name':'archive_'+entry['execution_consumer_sha256']+'_'+p.name,'path':str(p),'sha256':sha(p)})
 need(len({r['name']for r in pins})==len(pins),'UNIQUE_PIN_NAMES')
 return before,update,original,pins,edges,duplicates

def current_closure(out,protected_binding):
 need(sha(BUILDER)==BUILDER_SHA,'UNCHANGED_REVIEWED_SOURCE_SESSION')
 config=json.loads(raw(out/'CONFIG.json'));pr=json.loads(raw(out/'RAW_PR_MERGED_READBACK.json'));commit=json.loads(raw(out/'MERGED_COMMIT.json'));tree=json.loads(raw(out/'COMPLETE_MERGED_TREE.json'))
 files=merged(pr,config['expected_head_sha'],config['expected_merge_commit'],commit,tree)
 materials={n:raw(ROOT/(PREFIX+n))for n in FLAT16|{ADDED}|P5}
 for n,b in materials.items():need(digest(b)==config['source_hashes'][n],'CURRENT_MERGED_MATERIAL_CHANGED')
 proof=source_proof(files,materials);saved_proof=json.loads(raw(out/'SOURCE_ORIGIN_PROOF.json'));need(saved_proof=={'status':'FULL_ACTUAL_MERGED_TREE_SOURCE_PROOF_NOT_INSTALLATION','files':proof,'unchanged_original_targets':'ORIGINAL_BOUND_SOURCE_AUTHORITY_PRESERVED'},'CURRENT_SOURCE_ORIGIN_PROOF_CHANGED')
 normalized=copy.deepcopy(pr);normalized['files']=[{'path':x['path'],'sha':x['sha']}for x in proof];need(json.loads(raw(out/'PR_MERGED_READBACK.json'))==normalized,'NORMALIZED_PR_NOT_ACTUAL_TREE_PROJECTION')
 builder=module(BUILDER,'phase7_current_runtime_closure_builder')
 before,update,original,pins,edges,duplicates=pin_table(builder)
 with fresh_gates(),builder.source_session(ROOT,pins):
  import phase7_runtime_update as helper,nightly_coverage as nightly
  actual=helper.validate(ROOT,before,original)
  need(actual.get('profile')=='PHASE7_SCOPED_POLICY','CURRENT_REAL_HELPER_PASS')
  nightly.load_enforcement_activation(ROOT)
 need(len(update['runtime_targets'])==22 and len(update['additional_modules'])==33,'CURRENT22_33')
 _,raw_protected=bound(protected_binding);protected(json.loads(raw_protected),installed_at=update['installed_at_utc'])
 for row in pins:need(sha(row['path'])==row['sha256'],'CURRENT_PIN_READBACK')
 return {'standard':CLOSURE_STANDARD,'status':CLOSURE_STATUS,'tree_root':str(ROOT),'source_session':binding(BUILDER),'runtime_update':json.loads(raw(ROOT/before['enforcement_activation']['path']))['authorized_runtime_update'],'activation':before['enforcement_activation'],'policy_version_catalog':update['policy_version_catalog'],'protected_readback':protected_binding,'merged_pr':relative(out/'RAW_PR_MERGED_READBACK.json'),'merged_commit':relative(out/'MERGED_COMMIT.json'),'merged_tree':relative(out/'COMPLETE_MERGED_TREE.json'),'source_origin_proof':relative(out/'SOURCE_ORIGIN_PROOF.json'),'source_pins':pins,'local_import_edges':edges,'identical_own_copies':duplicates,'source_pin_count':len(pins),'historical_runtime_predecessor':json.loads(raw(out/'CONFIG.json'))['predecessor_runtime'],'certifies':False,'zenodo_writes':0,'clean_nights_credited':0}

def require_current_closure(value):
 p,b=bound(value);v=json.loads(b)
 fields={'standard','status','tree_root','source_session','runtime_update','activation','policy_version_catalog','protected_readback','merged_pr','merged_commit','merged_tree','source_origin_proof','source_pins','local_import_edges','identical_own_copies','source_pin_count','historical_runtime_predecessor','certifies','zenodo_writes','clean_nights_credited'}
 need(set(v)==fields and v['standard']==CLOSURE_STANDARD and v['status']==CLOSURE_STATUS and v['tree_root']==str(ROOT)and v['certifies']is False and type(v['zenodo_writes'])is int and v['zenodo_writes']==0 and type(v['clean_nights_credited'])is int and v['clean_nights_credited']==0,'CLOSED_CURRENT_RUNTIME_CLOSURE')
 out=p.parent;fresh=current_closure(out,v['protected_readback']);need(fresh==v,'CURRENT_FULL_RUNTIME_CLOSURE_CHANGED');need(raw(p)==b,'CLOSURE_CHANGED_DURING_CONSUMPTION')
 return v

def close(output,protected_after_binding,*,reviewed_driver_sha256):
 need(sha(__file__)==reviewed_driver_sha256,'REVIEWED_CLOSE_DRIVER')
 out=Path(output).resolve(strict=True);need(out.is_relative_to(ROOT/'reports/verification-coverage'),'OWN_CLOSURE_OUTPUT')
 ledgerpath=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';oldraw=raw(ledgerpath)
 try:
  p=json.loads(raw(out/'INSTALLED_AWAITING_CLOSURE.json'))
  need(p.get('status')=='INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS'and p['driver_sha256']==reviewed_driver_sha256,'OWN_PENDING_NOT_PASS')
  need(not any((out/n).exists()for n in('RUNTIME_UPDATE_RECEIPT.json','INSTALL_RECEIPT.json','candidate-validation')),'NO_CLOSE_REPLAY')
  need(digest(oldraw)==p['predecessor_ssot_sha256'],'CLOSURE_SSOT_CAS');old=json.loads(oldraw)
  need(full27(old)==p['publication_entities']and old['enforcement_activation']==p['predecessor_activation']and old['premise_declaration_cutover_run']==p['cutover'],'BEFORE_FULL27_CONTROL')
  _,b=bound(p['live_protected_before']);before=json.loads(b);_,b=bound(protected_after_binding);after=json.loads(b);protected(after,before,p['installed_at_utc'])
  previous=p['previous_runtime_contents'];_,b=bound(previous['original_activation']);original=json.loads(b)
  for r in p['runtime_targets']+p['additional_modules']:need(sha(ROOT/r['path'])==r.get('after_sha256',r.get('sha256')),'INSTALLED_CLOSURE_SOURCE')
  with fresh_gates()as paths:
   import phase7_runtime_update as helper,corpus_ledger as corpus,nightly_coverage as nightly
   receipt={**previous,'installed_at_utc':p['installed_at_utc'],'pull_request_readback':p['pull_request_readback'],'runtime_targets':p['runtime_targets'],'additional_modules':p['additional_modules'],'protected_readback':protected_after_binding}
   candidate=out/'candidate-validation';candidate.mkdir(exist_ok=False)
   # These closed candidate inputs carry the fixed validator's internal receipt
   # status. They are not nominated in SSOT and never serve as final admission.
   save(candidate/'RUNTIME_UPDATE_RECEIPT.json',receipt)
   candidate_wrapper={**original,'authorized_runtime_update':relative(candidate/'RUNTIME_UPDATE_RECEIPT.json')}
   save(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',candidate_wrapper)
   save(candidate/'CANDIDATE_NOT_ACTIVATED.json',{'status':'UNNOMINATED_CANDIDATE_INPUTS_NOT_ADMISSION','certifies':False,'ssot_writes':0})
   proposed={**old,'enforcement_activation':relative(candidate/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')}
   need({k:v for k,v in candidate_wrapper.items()if k!='authorized_runtime_update'}==original,'ORIGINAL_ACTIVATION_UNCHANGED')
   actual=helper.validate(ROOT,proposed,original);need(actual.get('profile')=='PHASE7_SCOPED_POLICY','ACTUAL_NEW_RUNTIME_VALIDATION')
   candidate_fresh=corpus.build(ROOT,ROOT/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=proposed)
   need(full27(candidate_fresh)==p['publication_entities']and candidate_fresh['premise_declaration_cutover_run']==p['cutover']and candidate_fresh['enforcement_activation']==proposed['enforcement_activation'],'FRESH_FULL27_CONTROL')
   helper.validate(ROOT,candidate_fresh,original)
   for q,h in paths.values():need(sha(q)==h,'SOURCE_CHANGED_BEFORE_FINAL_RECEIPT')
   need(raw(ledgerpath)==oldraw,'LEDGER_CHANGED_BEFORE_FINAL_RECEIPT')
   save(out/'CANDIDATE_VALIDATION.json',{'status':'REAL_NEW_HELPER_AND_FRESH27_SCAN_PASS_NOT_ACTIVATED','protected_readback':protected_after_binding,'candidate_activation':proposed['enforcement_activation'],'certifies':False,'ssot_writes':0})
   # Final receipts are created only after the real validator, fresh scan, and
   # fresh protected readback have passed. Activation still requires the CAS.
   save(out/'RUNTIME_UPDATE_RECEIPT.json',receipt)
   wrapper={**original,'authorized_runtime_update':relative(out/'RUNTIME_UPDATE_RECEIPT.json')}
   save(out/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json',wrapper)
   fresh={**candidate_fresh,'enforcement_activation':relative(out/'ENFORCEMENT_ACTIVATION_RUNTIME_SUCCESSOR.json')}
   helper.validate(ROOT,fresh,original)
   for q,h in paths.values():need(sha(q)==h,'SOURCE_CHANGED_BEFORE_CAS')
   need(raw(ledgerpath)==oldraw,'LEDGER_CHANGED_BEFORE_CAS')
   newsha=corpus.write_guarded_ledger(ledgerpath,fresh,p['predecessor_ssot_sha256'])
   nightly.load_enforcement_activation(ROOT);need(sha(ledgerpath)==newsha,'SSOT_AFTER_READBACK')
   immutable(out/'AFTER_LEDGER.json',raw(ledgerpath));immutable(out/'LEDGER.md',corpus.render_markdown(fresh).encode())
  closure=current_closure(out,protected_after_binding);save(out/'CURRENT_RUNTIME_CLOSURE.json',closure)
  require_current_closure(relative(out/'CURRENT_RUNTIME_CLOSURE.json'))
  result={'standard':'VRS-PHASE7-PUBLIC-STATE-RUNTIME-SUCCESSOR-INSTALL-1','status':'INSTALLED_REAL_RUNTIME_VALIDATION_PROTECTED22_PRESERVING_SSOT_PASS','current_runtime_closure':relative(out/'CURRENT_RUNTIME_CLOSURE.json'),'runtime_update':relative(out/'RUNTIME_UPDATE_RECEIPT.json'),'activation':fresh['enforcement_activation'],'before_ssot_sha256':p['predecessor_ssot_sha256'],'after_ssot_sha256':newsha,'protected_readback':protected_after_binding,'full27_rows_unchanged':True,'cutover':'Run-188','runtime_targets':22,'additional_modules':33,'runtime_writes':3,'ssot_writes':1,'zenodo_writes':0,'certificates_issued':0,'clean_nights_credited':0,'certifies':False}
  save(out/'INSTALL_RECEIPT.json',result);return result
 except Exception as exc:
  if not(out/'CLOSURE_HOLD.json').exists():save(out/'CLOSURE_HOLD.json',{'status':'HOLD_CLOSURE_NOT_ADMISSION','failure_class':type(exc).__name__,'failure':str(exc),'ssot_changed':raw(ledgerpath)!=oldraw,'no_automatic_retry':True,'certifies':False})
  raise
if __name__=='__main__':raise SystemExit('HOLD: explicit root-reviewed config/driver and actual merge/protected closure are required. No automatic operation.')
