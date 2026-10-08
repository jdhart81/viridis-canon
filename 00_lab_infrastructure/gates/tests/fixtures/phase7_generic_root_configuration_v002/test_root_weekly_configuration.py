"""TMP-only fixture merge/source proof; never an installed/public PASS."""
from pathlib import Path
import copy,hashlib,json,tempfile,unittest
import root_weekly_configuration as m
SOURCE=Path(__file__).parent/'repo_sources/production'
OLD=Path(__file__).parent/'repo_sources/original'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.before=m.ROOT;m.ROOT=self.root;self.files=[]
  sources={n:SOURCE/n for n in m.PRODUCTION};sources.update({n:OLD/n for n in m.ORIGINAL});sources['prepare_first_seven_plan.py']=Path(__file__).parent/'repo_sources/original/prepare_first_seven_plan.py';sources['runtime_successor.py']=Path(__file__).parent/'repo_sources/original/runtime_successor.py'
  self.specs=[{'name':n,'source':str(p),'git_path':'00_lab_infrastructure/gates/'+n,'destination':n}for n,p in sources.items()];self.tree={'sha':'a'*40,'truncated':False,'tree':[{'path':r['git_path'],'mode':'100644','type':'blob','sha':m.blob(m.raw(r['source']))}for r in self.specs]};head='b'*40;merge='c'*40;self.pr={'number':73,'url':'https://github.com/jdhart81/viridis-canon/pull/73','state':'MERGED','baseRefName':'main','headRefOid':head,'mergeCommit':{'oid':merge},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in m.CHECKS]};self.commit={'sha':merge,'tree':{'sha':self.tree['sha']}};self.evidence={}
  for n,v in [('MERGED_PR.json',self.pr),('MERGED_COMMIT.json',self.commit),('COMPLETE_MERGED_TREE.json',self.tree)]:self.save(n,v)
  self.result={'status':'EXACT_HEAD_ORDINARY_SOURCE_PR_MERGED_ALL_CHECKS_PASS','head':head,'merge_commit':merge,'merged_pr':self.evidence['MERGED_PR.json'],'merged_commit':self.evidence['MERGED_COMMIT.json'],'merged_tree':self.evidence['COMPLETE_MERGED_TREE.json']};self.save('RESULT.json',self.result)
 def tearDown(self):m.ROOT=self.before;self.tmp.cleanup()
 def save(self,n,v):p=self.root/n;p.write_bytes(m.encode(v));self.evidence[n]=m.binding(p)
 def plan(self):return m.adoption_plan(self.root,self.evidence,self.specs,self.root/'reports/verification-coverage/source')
 def test_all_frozen_generic24_source_blobs_proven_no_adoption(self):
  p=self.plan();self.assertEqual(len(p['sources']),24);self.assertFalse(Path(p['output']).exists());self.assertEqual(p['zenodo_writes'],0);self.assertFalse(p['certifies']);self.assertIn('actual_generic_runtime_closure',p['unresolved'])
 def test_explicit_tmp_adoption_retains_exact_sources_and_no_admission(self):
  plan=self.plan();receipt=m.adopt_sources(plan);v=m.bound(self.root,receipt);self.assertEqual(v['ssot_writes'],0);self.assertEqual(len(v['sources']),24);self.assertEqual(v['status'],'ACTUAL_OWN_MERGED_SOURCE_ADOPTED_NOT_RUNTIME_OR_PUBLICATION_CLEARANCE')
  for r in v['sources']:self.assertEqual(m.sha(r['binding']['path']),r['sha256'])
 def test_unmerged_or_prospective_head_check_holds_before_copy(self):
  for key,value in [('state','OPEN'),('headRefOid',None),('baseRefName','other'),('number',71),('statusCheckRollup',[])]:
   with self.subTest(key=key):v=copy.deepcopy(self.pr);v[key]=value;self.save('MERGED_PR.json',v);self.assertRaises(ValueError,self.plan);self.assertFalse((self.root/'reports').exists());self.save('MERGED_PR.json',self.pr)
 def test_pending_required_check_is_not_pass(self):
  v=copy.deepcopy(self.pr);v['statusCheckRollup'][0]['status']='IN_PROGRESS';self.save('MERGED_PR.json',v);self.assertRaises(ValueError,self.plan)
 def test_raw_merge_binding_changed_holds(self):
  (self.root/'MERGED_PR.json').write_bytes(b'{}');self.assertRaises(ValueError,self.plan)
 def test_incomplete_or_duplicate_git_tree_holds(self):
  for key,value in [('truncated',True),('tree',self.tree['tree']+self.tree['tree'][:1])]:
   v=copy.deepcopy(self.tree);v[key]=value;self.save('COMPLETE_MERGED_TREE.json',v);self.assertRaises(ValueError,self.plan);self.save('COMPLETE_MERGED_TREE.json',self.tree)
 def test_wrong_blob_mode_or_source_byte_holds(self):
  for key,value in [('sha','0'*40),('mode','120000')]:
   v=copy.deepcopy(self.tree);v['tree'][0][key]=value;self.assertRaises(ValueError,m.exact_sources,v,self.specs)
 def test_duplicate_destination_missing_core_or_escape_holds(self):
  cases=[self.specs[:-1],copy.deepcopy(self.specs),copy.deepcopy(self.specs)];cases[1][1]['destination']=cases[1][0]['destination'];cases[2][0]['destination']='../escape'
  for v in cases:self.assertRaises(ValueError,m.exact_sources,self.tree,v)
 def test_modified_plan_head_or_source_proof_never_adopts(self):
  for key,value in [('head','d'*40),('status','PASS')]:
   p=self.plan();p[key]=value;self.assertRaises(ValueError,m.adopt_sources,p);self.assertFalse(Path(p['output']).exists())
 def test_unavailable_future_closure_not_replaced_by_historical_table(self):
  p=self.plan();receipt=m.adopt_sources(p);self.assertRaises(Exception,m.build_source_inputs,self.root,receipt,{'path':'missing.json','sha256':'0'*64})
 def test_module_guard_refuses_changed_recipe(self):
  p=self.root/'fake.py';p.write_bytes(b'pass\n');self.assertRaises(ValueError,m.recipe,p)
 def checkout_fixture(self):
  checkout=self.root/'checkout';tree=copy.deepcopy(self.tree);base='00_lab_infrastructure/gates/'
  for spec,node in zip(self.specs,tree['tree']):
   name=spec['name'];gp=base+name if name in m.PRODUCTION else base+'production_snapshots/fixture/after/'+name;node['path']=gp;p=checkout/gp;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(m.raw(spec['source']))
  return checkout,tree
 def test_real_checkout_selector_resolves_exact24_source_blobs(self):
  checkout,tree=self.checkout_fixture();runtime=checkout/'00_lab_infrastructure/gates/production_snapshots/fixture/after/runtime_successor.py';specs=m.source_specs(checkout,tree,runtime_consumer=runtime);rows=m.exact_sources(tree,specs);self.assertEqual(len(rows),24);self.assertEqual({r['name']for r in rows},set(m.PRODUCTION)|set(m.ORIGINAL)|{'prepare_first_seven_plan.py','runtime_successor.py'});self.assertFalse((self.root/'reports').exists())
 def test_checkout_substitution_or_missing_snapshot_is_not_invented(self):
  checkout,tree=self.checkout_fixture();runtime=checkout/'00_lab_infrastructure/gates/production_snapshots/fixture/after/runtime_successor.py';p=checkout/'00_lab_infrastructure/gates/weekly_digest_executor.py';p.write_bytes(b'changed source\n');self.assertRaises(ValueError,m.source_specs,checkout,tree,runtime_consumer=runtime)
if __name__=='__main__':unittest.main()
