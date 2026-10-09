from pathlib import Path
import ast,contextlib,copy,hashlib,importlib.util,json,tempfile,types,unittest,__future__,sys
from unittest.mock import patch
D=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_runtime_scaffold',D/'runtime_successor.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ROOT=m.ROOT;LEDGER=json.loads(m.raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'));_,b=m.bound(LEDGER['enforcement_activation']);_,b=m.bound(json.loads(b)['authorized_runtime_update']);PREVIOUS=json.loads(b)
CATALOG_BYTES=(ROOT/PREVIOUS['policy_version_catalog']['path']).read_bytes()
@contextlib.contextmanager
def temporary_root():
 with tempfile.TemporaryDirectory()as t:
  root=Path(t).resolve()
  with patch.object(m,'ROOT',root),patch.object(m.u,'ROOT',root),patch.object(m.e,'ROOT',root):yield root
class Guards(unittest.TestCase):
 def test_fixture_predecessor_all77_and35_source_bytes(self):
  current={r['path']:m.sha(ROOT/r['path'])for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};m.inventory(PREVIOUS,current);self.assertEqual(m.full35(LEDGER),LEDGER['publication_entities']);self.assertEqual(len(current),77)
 def test_missing_old_archive_rejected(self):
  p=copy.deepcopy(PREVIOUS);p['additional_modules'].pop();c={r['path']:r.get('after_sha256',r.get('sha256'))for r in p['runtime_targets']+p['additional_modules']}
  with self.assertRaises(m.Hold):m.inventory(p,c)
 def test_old_archive_hash_change_rejected(self):
  c={r['path']:r.get('after_sha256',r.get('sha256'))for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};p=next(r['path']for r in PREVIOUS['additional_modules']if '/policy_versions/'in r['path']);c[p]='0'*64
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,c)
 def test_foreign_flat_rejected(self):
  p=copy.deepcopy(PREVIOUS);p['additional_modules'][0]['path']=m.PREFIX+'foreign.py';c={r['path']:r.get('after_sha256',r.get('sha256'))for r in p['runtime_targets']+p['additional_modules']}
  with self.assertRaises(m.Hold):m.inventory(p,c)
 def test_changed_one_protected_target_rejected(self):
  c={r['path']:r.get('after_sha256',r.get('sha256'))for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};c[PREVIOUS['runtime_targets'][0]['path']]='0'*64
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,c)
 def test_extra_or_missing_physical_path_rejected(self):
  c={r['path']:r.get('after_sha256',r.get('sha256'))for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']}
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,{**c,'foreign':'0'*64})
  c.pop(next(iter(c)))
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,c)
 def test_namespace_closed_exact_two_names_and_other_bodies(self):
  b=(D/'BEFORE_phase7_runtime_update.py').read_bytes();a=(D/'proposed/phase7_runtime_update.py').read_bytes();r=m.namespace_only_delta(b,a);self.assertEqual(set(r['added']),m.ADDED);self.assertEqual(m.RUNTIME_WRITE_COUNT,6);self.assertEqual(m.ADDITIONAL_COUNT,57)
 def test_foreign_or_missing_namespace_bytes_fail(self):
  for new in[(D/'proposed/phase7_runtime_update.py').read_bytes()+b' ',(D/'BEFORE_phase7_runtime_update.py').read_bytes()]:
   with self.assertRaises(m.Hold):m.namespace_only_delta((D/'BEFORE_phase7_runtime_update.py').read_bytes(),new)
 def test_literal_old35_change_rejected(self):
  v=copy.deepcopy(LEDGER);v['publication_entities'][0]['extra']='changed'
  with self.assertRaises(m.Hold):m.full35(v)
 def test_cached_acceptable_flag_does_not_admit_row(self):
  v=copy.deepcopy(LEDGER);v['publication_entities'][0]['enforcement_acceptable']=False
  with self.assertRaises(m.Hold):m.full35(v)
 def test_cutover_change_rejected(self):
  v=copy.deepcopy(LEDGER);v['premise_declaration_cutover_run']='Run-187'
  with self.assertRaises(m.Hold):m.full35(v)
 def test_bool_and_int_are_distinct(self):self.assertFalse(m.exact({'a':True},{'a':1}))
 def test_catalog_all_four_rows_exact_no_append_or_rebind(self):
  _,b=m.bound(PREVIOUS['policy_version_catalog']);v=json.loads(b);r=m.expected_catalog(v,{}, {'path':'fake','sha256':'0'*64});self.assertEqual(m.encoded(v),m.encoded(r));self.assertIsNot(v,r)
 def test_missing_duplicate_catalog_rejected(self):
  for rows in[[{'execution_consumer_sha256':'0'*64}]*4,[{'execution_consumer_sha256':str(i)*64}for i in range(3)]]:
   with self.assertRaises(m.Hold):m.expected_catalog({'versions':rows},{},{})
 def test_protected_merge_and_source_session_checks_exact_original(self):
  self.assertIs(m.protected,m.e.protected);self.assertIs(m.protected,m.u.protected);self.assertIs(m.merged,m.e.merged);self.assertEqual(m.BUILDER_SHA,'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740')
 def test_all_existing_runtimehelper_definitions_exact(self):
  old=ast.parse((D/'BEFORE_phase7_runtime_update.py').read_bytes());new=ast.parse((D/'proposed/phase7_runtime_update.py').read_bytes());a=[ast.dump(n,include_attributes=False)for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))];b=[ast.dump(n,include_attributes=False)for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))];self.assertEqual(a,b)
 def test_all_reader_function_bodies_exact_predecessor(self):
  old=ast.parse((D/'historical_2dca_prospective_catalog.py').read_bytes());new=ast.parse(m.PROSPECTIVE.read_bytes());a={n.name:ast.dump(n,include_attributes=False)for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};b={n.name:ast.dump(n,include_attributes=False)for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};self.assertEqual(a,b)
 def test_fresh35_and_other_unchanged_core_functions_exact(self):
  old=ast.parse(Path(m.PRIOR).read_bytes());new=ast.parse(Path(m.__file__).read_bytes());a={n.name:ast.dump(n,include_attributes=False)for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};b={n.name:ast.dump(n,include_attributes=False)for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  for name in ['exact','closed_relative_binding','full35','namespace_only_delta','expected_catalog','unchanged','load_builder','read_bound_closure','require_current_closure','fresh35']:self.assertEqual(a[name],b[name])
 def test_materials_are_exact_predecessor_union_two(self):self.assertEqual(m.MATERIAL_NAMES,m.e.MATERIAL_NAMES|m.ADDED);self.assertEqual(len(m.MATERIAL_NAMES),30);self.assertEqual(m.ARCHIVE,set())
 def test_relative_actual_binding_and_absolute_rejection(self):
  with temporary_root()as root:
   p=root/'receipt.json';p.write_bytes(b'{}\n');self.assertEqual(m.closed_relative_binding({'path':'receipt.json','sha256':m.sha(p)})[0],p)
   with self.assertRaises(m.Hold):m.closed_relative_binding({'path':str(p),'sha256':m.sha(p)})
 def test_parent_path_and_boolean_hash_rejected(self):
  for r in [{'path':'../x','sha256':'0'*64},{'path':'x','sha256':True}]:
   with self.assertRaises(m.Hold):m.closed_relative_binding(r)
 @contextlib.contextmanager
 def pending(self):
  with temporary_root()as root:
   out=root/'reports/install';out.mkdir(parents=True);previous=copy.deepcopy(PREVIOUS);c={'output':str(out),'reviewed_driver_sha256':'a'*64,'expected_ssot_sha256':'b'*64,'live_protected_before':{'path':'protected.json','sha256':'c'*64},'source_hashes':{}};add=copy.deepcopy(previous['additional_modules'])
   for n in sorted(m.INSTALL_NAMES):
    q=out/'after-additional'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((D/'proposed'/n).read_bytes()if (D/'proposed'/n).exists()else b'# SOURCE_ONLY_TEST_FIXTURE_NOT_ADMISSION\n');h=m.sha(q);c['source_hashes'][n]=h;row={'path':m.PREFIX+n,'sha256':h,'source':m.relative(q)};add=[row if r['path']==row['path']else r for r in add]if n in m.CHANGED else add+[row]
   q=out/'PR_MERGED_READBACK.json';q.write_text('{}\n');b=CATALOG_BYTES;cat=root/'old-catalog.json';cat.write_bytes(b);previous['policy_version_catalog']=m.relative(cat);(out/'POLICY_VERSION_CATALOG.json').write_bytes(b)
   p={'standard':'VRS-PHASE7-OWN-RECORD-RUNTIME-INSTALLED-PENDING-1','status':'INSTALLED_AWAITING_FRESH_PROTECTED_CLOSURE_NOT_PASS','installed_at_utc':'2026-10-08T00:00:00Z','predecessor_ssot_sha256':c['expected_ssot_sha256'],'predecessor_activation':LEDGER['enforcement_activation'],'publication_entities':LEDGER['publication_entities'],'cutover':'Run-188','previous_runtime_contents':previous,'runtime_targets':copy.deepcopy(previous['runtime_targets']),'additional_modules':add,'policy_version_catalog':m.relative(out/'POLICY_VERSION_CATALOG.json'),'pull_request_readback':m.relative(q),'live_protected_before':c['live_protected_before'],'driver_sha256':c['reviewed_driver_sha256'],'runtime_writes':6,'ssot_writes':0,'zenodo_writes':0,'protected_verifier_changed':False,'certifies':False};yield c,p,previous,out
 def test_pending_source_only_six_source_shape_pass(self):
  with self.pending()as args:m.require_pending(*args)
 def test_pending_wrong_target_rejected(self):
  with self.pending()as(c,p,old,out):
   p['runtime_targets'][0]['after_sha256']='0'*64
   with self.assertRaises(m.Hold):m.require_pending(c,p,old,out)
 def test_pending_changed_archive_source_rejected(self):
  with self.pending()as(c,p,old,out):
   next(r for r in p['additional_modules']if '/policy_versions/'in r['path'])['source']['sha256']='0'*64
   with self.assertRaises(m.Hold):m.require_pending(c,p,old,out)
 def test_pending_catalog_rebind_or_row_change_rejected(self):
  with self.pending()as(c,p,old,out):
   q=out/'POLICY_VERSION_CATALOG.json';v=json.loads(q.read_bytes());v['versions'][-1]['pull_request_readback']['sha256']='0'*64;q.write_bytes(m.encoded(v));p['policy_version_catalog']=m.relative(q)
   with self.assertRaises(m.Hold):m.require_pending(c,p,old,out)
 def test_pending_typed_counter_rejects_bool_float(self):
  for value in[True,6.0,'6',5]:
   with self.pending()as(c,p,old,out):
    p['runtime_writes']=value
    with self.assertRaises(m.Hold):m.require_pending(c,p,old,out)
 def test_pending_unlisted_field_rejected(self):
  with self.pending()as(c,p,old,out):
   p['cached_pass']=True
   with self.assertRaises(m.Hold):m.require_pending(c,p,old,out)
 @contextlib.contextmanager
 def materials(self):
  current={r['path']:m.sha(ROOT/r['path'])for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']}
  materials={n:(D/'proposed'/n).read_bytes()if n in m.INSTALL_NAMES and(D/'proposed'/n).exists()else (ROOT/(m.PREFIX+n)).read_bytes()if n not in m.ADDED else b'# SOURCE_ONLY_TEST_FIXTURE_NOT_ADMISSION\n'for n in m.MATERIAL_NAMES}
  for n in m.CHANGED-{'phase7_runtime_update.py'}:materials[n]+=b'\n# SOURCE_ONLY_TEST_FIXTURE_CHANGED_DISPATCH\n'
  sourcepins={n:m.digest(materials[n])for n in (m.CHANGED-{'phase7_runtime_update.py'})|m.ADDED}
  files={'00_lab_infrastructure/gates/'+n:{'sha':m.git_blob(b)}for n,b in materials.items()}
  with temporary_root()as root,patch.object(m,'REVIEWED_OWN_SOURCE_PINS',sourcepins):
   for n in m.e.MATERIAL_NAMES:
    q=root/(m.PREFIX+n);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/(m.PREFIX+n)).read_bytes())
   yield root,current,materials,files
 def test_all30_fixture_materials_and_git_blob_proof(self):
  with self.materials()as(root,current,materials,files):
   proof=m.prove_materials(current,materials,files);self.assertEqual(len(proof),30)
 def test_omitted_old_source_rejected(self):
  with self.materials()as(root,current,materials,files):
   materials.pop('publication_gate.py')
   with self.assertRaises(m.Hold):m.prove_materials(current,materials,files)
 def test_modified_unchanged_methods_rejected(self):
  with self.materials()as(root,current,materials,files):
   materials['methods_digest.py']+=b' ';files['00_lab_infrastructure/gates/methods_digest.py']['sha']=m.git_blob(materials['methods_digest.py'])
   with self.assertRaises(m.Hold):m.prove_materials(current,materials,files)
 def test_wrong_own_git_blob_rejected(self):
  with self.materials()as(root,current,materials,files):
   files['00_lab_infrastructure/gates/own_record_comparison.py']['sha']='0'*40
   with self.assertRaises(m.Hold):m.prove_materials(current,materials,files)
 def test_additive_collision_rejected_before_install(self):
  with self.materials()as(root,current,materials,files):
   (root/(m.PREFIX+'own_record_comparison.py')).write_bytes(materials['own_record_comparison.py'])
   with self.assertRaises(m.Hold):m.prove_materials(current,materials,files)
 def test_current_consumer_full_recomputation_required(self):
  with patch.object(m,'closed_relative_binding',return_value=(Path('/fake/closure'),b'bytes')),patch.object(m,'read_bound_closure',return_value={'protected_readback':{}}),patch.object(m,'current_closure',return_value={'different':True}):
   with self.assertRaises(m.Hold):m.require_current_closure({})
 def test_fresh35_calls_scanner_then_rows_and_helper(self):
  with temporary_root()as root:
   p=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';p.parent.mkdir();p.write_bytes(m.encoded(LEDGER));seen=[]
   class Corpus:
    def build(self,*args,**kwargs):seen.append(('scan',kwargs));return copy.deepcopy(LEDGER)
   class Helper:
    def validate(self,*args):seen.append(('validate',None));return {'profile':'PHASE7_SCOPED_POLICY'}
   @contextlib.contextmanager
   def scope(*args,**kwargs):seen.append(('scope',kwargs));yield {'mode':'REAL_DISK_UNWRAPPED'}
   with patch.dict(sys.modules,{'phase7_policy_versions':types.ModuleType('phase7_policy_versions')}),patch.object(m.v,'prospective_catalog_reader',scope):m.fresh35(Corpus(),LEDGER,LEDGER['publication_entities'],Helper(),{})
   self.assertEqual([x[0]for x in seen],['scope','scan','validate']);self.assertEqual(seen[1][1]['previous_ledger'],LEDGER)
 def test_fresh35_changed_row_prevents_validate(self):
  with temporary_root()as root:
   p=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';p.parent.mkdir();p.write_bytes(m.encoded(LEDGER));seen=[];changed=copy.deepcopy(LEDGER);changed['publication_entities'][0]['unexpected']='changed'
   class Corpus:
    def build(self,*args,**kwargs):seen.append('scan');return changed
   class Helper:
    def validate(self,*args):seen.append('validate');return {'profile':'PHASE7_SCOPED_POLICY'}
   @contextlib.contextmanager
   def scope(*args,**kwargs):yield {'mode':'REAL_DISK_UNWRAPPED'}
   with patch.dict(sys.modules,{'phase7_policy_versions':types.ModuleType('phase7_policy_versions')}),patch.object(m.v,'prospective_catalog_reader',scope):
    with self.assertRaises(m.Hold):m.fresh35(Corpus(),LEDGER,LEDGER['publication_entities'],Helper(),{})
   self.assertEqual(seen,['scan'])
 def test_fresh35_changed_controls_prevents_validate(self):
  with temporary_root()as root:
   p=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';p.parent.mkdir();p.write_bytes(m.encoded(LEDGER));seen=[];changed=copy.deepcopy(LEDGER);changed['enforcement_activation']={'path':'foreign','sha256':'0'*64}
   class Corpus:
    def build(self,*args,**kwargs):seen.append('scan');return changed
   class Helper:
    def validate(self,*args):seen.append('validate');return {'profile':'PHASE7_SCOPED_POLICY'}
   @contextlib.contextmanager
   def scope(*args,**kwargs):yield {'mode':'REAL_DISK_UNWRAPPED'}
   with patch.dict(sys.modules,{'phase7_policy_versions':types.ModuleType('phase7_policy_versions')}),patch.object(m.v,'prospective_catalog_reader',scope):
    with self.assertRaises(m.Hold):m.fresh35(Corpus(),LEDGER,LEDGER['publication_entities'],Helper(),{})
   self.assertEqual(seen,['scan'])
 def test_three_scans_before_and_after_CAS_exact_order(self):
  tree=ast.parse(Path(m.__file__).read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='close');calls=[]
  for n in ast.walk(f):
   if isinstance(n,ast.Call):
    name=ast.unparse(n.func)
    if name in ['fresh35','corpus.write_guarded_ledger']:calls.append((n.lineno,name,[k.arg for k in n.keywords]))
  calls.sort();self.assertEqual([n for _,n,_ in calls],['fresh35','fresh35','corpus.write_guarded_ledger','fresh35']);self.assertIn('prospective_output',calls[0][2]);self.assertIn('prospective_output',calls[1][2]);self.assertNotIn('prospective_output',calls[3][2])
 def test_physical_predecessor_never_calls_current_admission(self):
  f=next(n for n in ast.parse(Path(m.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='physical_predecessor');calls={ast.unparse(n.func)for n in ast.walk(f)if isinstance(n,ast.Call)};self.assertIn('e.read_bound_closure',calls);self.assertNotIn('e.require_current_closure',calls);self.assertNotIn('require_current_closure',calls)
 def test_preflight_dynamic_wholeSSOT_CAS_not_historical_hash(self):
  f=next(n for n in ast.parse(Path(m.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='preflight');self.assertIn("config['expected_ssot_sha256']",ast.unparse(f));self.assertNotIn('94f1',ast.unparse(f));self.assertNotIn('0d40',ast.unparse(f))
 def test_empty_future_pins_fail_closed_before_any_sourceproof(self):
  with self.materials()as(root,current,materials,files),patch.object(m,'REVIEWED_OWN_SOURCE_PINS',{}),patch.object(m.u,'source_proof')as proof:
   with self.assertRaises(m.Hold):m.prove_materials(current,materials,files)
   proof.assert_not_called()
 def test_actual_final_materials_are_exact_reviewed_source_and_blob_table(self):
  current={r['path']:m.sha(ROOT/r['path'])for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']}
  materials={n:(D/'proposed'/n).read_bytes()if n in m.INSTALL_NAMES else(ROOT/(m.PREFIX+n)).read_bytes()for n in m.MATERIAL_NAMES}
  files={'00_lab_infrastructure/gates/'+n:{'sha':m.git_blob(b)}for n,b in materials.items()}
  proof=m.prove_materials(current,materials,files);self.assertEqual(len(proof),30);self.assertEqual(set(m.REVIEWED_OWN_SOURCE_PINS),(m.CHANGED-{'phase7_runtime_update.py'})|m.ADDED)
 def test_real_current_five_function_profiles_not_fixture_hashes(self):
  with tempfile.TemporaryDirectory()as t,patch.dict(sys.modules,{}):
   gates=Path(t);modules={}
   for name,p in [('methods_digest',ROOT/(m.PREFIX+'methods_digest.py')),('phase7_policy_versions',D/'proposed/phase7_policy_versions.py'),('phase7_runtime_update',D/'proposed/phase7_runtime_update.py')]:
    q=gates/(name+'.py');b=p.read_bytes();q.write_bytes(b);x=types.ModuleType(name);x.__file__=str(q);exec(compile(b,str(q),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),x.__dict__);modules[name]=x;sys.modules[name]=x
   for name,names in [('methods_digest',['read_regular','digest']),('phase7_policy_versions',['current_catalog','implementation_for_note']),('phase7_runtime_update',['validate'])]:
    for n in names:m.v._compiled_function(modules[name],(gates/(name+'.py')).read_bytes(),n)
 def test_own_prospective_exact_final_profiles(self):
  self.assertEqual(m.v.HELPER_SHA,m.NEW_RUNTIME_HELPER_SHA);self.assertEqual(m.v.VERSION_SHA,m.REVIEWED_OWN_SOURCE_PINS['phase7_policy_versions.py']);self.assertEqual(m.v.METHODS_SHA,m.METHODS_SHA);self.assertEqual(m.v.DRIVER_SHA,'daeb140dc581104127f2e9eeacf6efb56f016ab381c0202a52ea67a97f183599')
 def test_explicit_no_automatic_entrypoint(self):self.assertIn("raise SystemExit('HOLD: root must supply",Path(m.__file__).read_text())
if __name__=='__main__':unittest.main()
