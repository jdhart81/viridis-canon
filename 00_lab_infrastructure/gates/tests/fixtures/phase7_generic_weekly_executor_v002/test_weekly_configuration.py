"""TMP-only source/blob construction tests; fake merge is never clearance."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import prepare_weekly_configuration as c
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.patch=patch.object(c,'ROOT',self.root);self.patch.start()
  def put(name,value):
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(c.encode(value));return c.binding(p)
  self.pins=[]
  for name in sorted(c.CORE|{'prepare_first_seven_plan.py','runtime_successor.py','recover.py','cohort.py'}):
   p=self.root/'sources'/name;p.parent.mkdir(exist_ok=True);p.write_bytes((Path(__file__).parent/'test_fixtures/prepare_first_seven_plan.py').read_bytes()if name=='prepare_first_seven_plan.py'else b'# fixture ordinary source; not executable admission\n');self.pins.append(dict(name=name,**c.binding(p)))
  by={p['name']:p for p in self.pins};closure=put('closure.json',{'source_pins':self.pins[:3]});closure['path']='closure.json';tree={'sha':'b'*40,'truncated':False,'tree':[{'path':'ordinary/'+p['name'],'type':'blob','mode':'100644','sha':c.blob_sha(Path(p['path']).read_bytes())}for p in self.pins]};self.tree=put('tree.json',tree);self.pr=put('pr.json',{'state':'MERGED','baseRefName':'main','url':'https://github.com/jdhart81/viridis-canon/pull/71','number':71,'headRefOid':'d'*40,'mergeCommit':{'oid':'a'*40}});commit=put('commit.json',{'sha':'a'*40,'tree':{'sha':'b'*40}});shared=put('shared.json',{'fixture':'no clearance'})
  self.inputs={k:shared for k in c.ROLES-{'canonical_root','package','current_runtime_closure','start_kind'}};self.inputs.update(standard='VRS-OWNED-DIGEST-CONFIG-CONSTRUCTION-1',canonical_root=str(self.root),package=str(self.root/'package'),current_runtime_closure=closure,start_kind='NEW_VERSION',extra_purpose_sources=self.pins[3:],git_path_by_name={p['name']:'ordinary/'+p['name']for p in self.pins},merged_pr=self.pr,merged_commit=commit,merged_tree=self.tree)
  for role,name in [('runtime_consumer','runtime_successor.py'),('recovery_consumer','recover.py'),('ordinary_cohort_consumer','cohort.py'),('source_session_consumer','prepare_first_seven_plan.py')]:self.inputs[role]={k:by[name][k]for k in('path','sha256')}
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def call(self):return c.construct(self.root,self.inputs)
 def tree_mutate(self,fn):
  p=Path(self.tree['path']);v=json.loads(p.read_bytes());fn(v);p.write_bytes(c.encode(v));self.tree.update(c.binding(p))
 def test_all_exact_blobs_and_python_consumer_bytes_pass_construction_only(self):
  value,origin=self.call();self.assertEqual(len(value['purpose_source_pins']),len(self.pins));self.assertEqual(origin['status'],'EXACT_MERGED_BLOBS_NOT_PUBLICATION_CLEARANCE');self.assertEqual(value['start_kind'],'NEW_VERSION')
 def test_no_write_construction(self):
  before={str(p):p.read_bytes()for p in self.root.rglob('*')if p.is_file()};self.call();self.assertEqual(before,{str(p):p.read_bytes()for p in self.root.rglob('*')if p.is_file()})
 def test_changed_source_byte_fails(self):Path(self.pins[0]['path']).write_bytes(b'changed');self.assertRaises(ValueError,self.call)
 def test_changed_git_blob_fails(self):self.tree_mutate(lambda v:v['tree'][0].update(sha='c'*40));self.assertRaises(ValueError,self.call)
 def test_missing_git_blob_fails(self):self.tree_mutate(lambda v:v['tree'].pop());self.assertRaises(ValueError,self.call)
 def test_truncated_tree_fails(self):self.tree_mutate(lambda v:v.update(truncated=True));self.assertRaises(ValueError,self.call)
 def test_duplicate_tree_path_fails(self):self.tree_mutate(lambda v:v['tree'].append(dict(v['tree'][0])));self.assertRaises(ValueError,self.call)
 def test_foreign_alias_fails(self):self.inputs['extra_purpose_sources'][0]['name']='fake_alias.py';self.assertRaises(ValueError,self.call)
 def test_missing_exact_namespace_member_fails(self):self.inputs['extra_purpose_sources'].pop(0);self.assertRaises(ValueError,self.call)
 def test_missing_full_git_mapping_fails(self):self.inputs['git_path_by_name'].pop(next(iter(self.inputs['git_path_by_name'])));self.assertRaises(ValueError,self.call)
 def test_relative_actual_input_rejected(self):self.inputs['authority']['path']='shared.json';self.assertRaises(ValueError,self.call)
 def test_absolute_runtime_binding_rejected(self):self.inputs['current_runtime_closure']['path']=str(self.root/'closure.json');self.assertRaises(ValueError,self.call)
 def test_future_unmerged_pr_rejected(self):p=Path(self.pr['path']);v=json.loads(p.read_bytes());v['state']='OPEN';p.write_bytes(c.encode(v));self.pr.update(c.binding(p));self.assertRaises(ValueError,self.call)
 def test_first_week_input_construction_pass_not_admission(self):self.inputs['start_kind']='CREATE_WEEK';value,_=self.call();self.assertEqual(value['start_kind'],'CREATE_WEEK')
 def test_unknown_start_kind_fails(self):self.inputs['start_kind']='CREATE';self.assertRaises(ValueError,self.call)
 def test_unknown_configuration_field_fails(self):self.inputs['force']=True;self.assertRaises(ValueError,self.call)
 def test_exact_duplicate_pin_deduplicates(self):self.inputs['extra_purpose_sources'].append(dict(self.pins[0]));value,_=self.call();self.assertEqual(len(value['purpose_source_pins']),len(self.pins))
 def test_existing_different_path_same_name_fails(self):row=dict(self.pins[0]);p=self.root/'other'/row['name'];p.parent.mkdir();p.write_bytes(Path(row['path']).read_bytes());row['path']=str(p);self.inputs['extra_purpose_sources'].append(row);self.assertRaises(ValueError,self.call)
 def test_real_unchanged_collector_preserves_primary_rows_and_import_edges(self):
  publisher=next(r for r in self.pins if r['name']=='first_digest_publisher.py');Path(publisher['path']).write_bytes(b'import publisher_recovery\n');publisher.update(c.binding(publisher['path']));closure=self.root/'closure.json';closure.write_bytes(c.encode({'source_pins':self.pins[:3]}));self.inputs['current_runtime_closure']['sha256']=c.binding(closure)['sha256'];extras,edges,duplicates=c.collect_extra_sources(self.root,self.inputs['current_runtime_closure'],self.inputs['source_session_consumer'],[r['path']for r in self.pins]);self.assertIn('publisher_recovery.py',edges['first_digest_publisher.py']);self.assertEqual({r['name']for r in extras},{r['name']for r in self.pins[3:]})
 def test_real_collector_missing_recovery_fails(self):
  paths=[r['path']for r in self.pins if r['name']!='publisher_recovery.py'];self.assertRaises(ValueError,c.collect_extra_sources,self.root,self.inputs['current_runtime_closure'],self.inputs['source_session_consumer'],paths)
 def test_real_blob_mapping_suggestion_is_exact(self):self.assertEqual(c.suggest_git_paths(self.root,self.pins,self.tree,self.inputs['git_path_by_name']),self.inputs['git_path_by_name'])
 def test_preferred_nonexistent_blob_fails(self):self.assertRaises(ValueError,c.suggest_git_paths,self.root,self.pins,self.tree,{self.pins[0]['name']:'invented.py'})
 def test_suggest_missing_blob_fails(self):self.tree_mutate(lambda v:v.update(tree=[x for x in v['tree']if x['path']!='ordinary/prepare_first_seven_plan.py']));self.assertRaises(ValueError,c.suggest_git_paths,self.root,self.pins,self.tree)
 def test_source_materials_needs_no_credential_or_future_gets(self):
  source={k:self.inputs[k]for k in c.SOURCE_FIELDS};pins,origin=c.source_materials(self.root,source);self.assertEqual(len(pins),len(self.pins));self.assertEqual(len(origin['source_rows']),len(pins))
 def test_explicit_output_immutable_and_exclusive(self):
  out=self.root/'reports/verification-coverage/inputs';result=c.emit_inputs(self.root,self.inputs,out);self.assertEqual(Path(result['path']),out/'ACTUAL_INPUTS.json');self.assertRaises(ValueError,c.emit_inputs,self.root,self.inputs,out)
if __name__=='__main__':unittest.main()
