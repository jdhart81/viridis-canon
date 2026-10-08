"""TMP-only actual copy/build regression; no fixture claims runtime admission."""
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import copy,json,types,unittest
import root_weekly_configuration as m
import test_root_weekly_configuration as fixture
class Tests(unittest.TestCase):
 save=fixture.Tests.save
 plan=fixture.Tests.plan
 def setUp(self):
  self.fixture=fixture.Tests();self.fixture.setUp()
  for k in ('tmp','root','before','files','specs','tree','pr','commit','evidence','result'):setattr(self,k,getattr(self.fixture,k))
  self.original_tmp=m.TMP;m.TMP=self.root.parent
 def tearDown(self):
  m.TMP=self.original_tmp;self.fixture.tearDown()
 def copied(self):
  receipt=m.adopt_sources(self.plan());value=m.bound(self.root,receipt);return receipt,value,value['merge_evidence']
 def test_copied_raw_four_objects_rebind_without_rewriting(self):
  original={n:m.raw(v['path'])for n,v in self.evidence.items()};receipt,v,e=self.copied();self.assertEqual(m.require_merge(e)[:2],('b'*40,'c'*40))
  for n in e:self.assertEqual(m.raw(e[n]['path']),original[n]);self.assertNotEqual(e[n]['path'],self.evidence[n]['path'])
  self.assertEqual(json.loads(m.raw(e['RESULT.json']['path']))['merged_pr'],self.evidence['MERGED_PR.json'])
 def test_build_roundtrip_reproves_real_copied_source_bytes(self):
  # Exactly three real runtime-code source fixtures complete the real CORE.
  names={'digest_metadata.py','digest_weekly_state.py','first_digest_state.py'};runtime=[]
  for name in sorted(names):
   source=Path(__file__).parent/'repo_sources/runtime'/name;dest=self.root/'runtime'/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(m.raw(source));runtime.append({'name':name,**m.binding(dest)});self.tree['tree'].append({'path':'runtime/'+name,'mode':'100644','type':'blob','sha':m.blob(m.raw(source))})
  self.save('COMPLETE_MERGED_TREE.json',self.tree);self.result['merged_tree']=self.evidence['COMPLETE_MERGED_TREE.json'];self.save('RESULT.json',self.result)
  receipt,v,e=self.copied();closure=self.root/'fixture-runtime-source-table.json';closure.write_bytes(m.encode({'source_pins':runtime}));relative={'path':closure.name,'sha256':m.sha(closure)}
  original_recipe=m.recipe
  def fixture_recipe(p):
   c=original_recipe(p);c.ROOT=self.root;return c
  with patch.object(m,'recipe',side_effect=fixture_recipe):
   inputs,proof=m.build_source_inputs(self.root,receipt,relative)
   self.assertEqual(len(proof['source_pins']),27);self.assertEqual(inputs['merged_pr'],e['MERGED_PR.json']);self.assertFalse(proof['certifies'])
   # External current-runtime/default admission remains fail-closed: it is
   # not replaced with a test marker or fixture population.
   def no_actual_admission(*args):raise ValueError('HOLD_FIXTURE_NO_REAL_RUNTIME_OR_DEFAULT_ADMISSION')
   with patch.object(m,'capture_recipe',return_value=SimpleNamespace(preflight_sources=no_actual_admission)):
    self.assertRaisesRegex(ValueError,'NO_REAL_RUNTIME',m.preflight_sources,self.root,receipt,relative)
 def test_original_hash_or_raw_body_tamper_never_passes(self):
  _,_,e=self.copied();p=Path(self.evidence['MERGED_PR.json']['path']);p.write_bytes(b'{}');self.assertRaises(ValueError,m.require_merge,e)
 def test_canonical_body_and_updated_hash_cannot_replace_original(self):
  _,_,e=self.copied();p=Path(e['MERGED_PR.json']['path']);v=json.loads(p.read_bytes());v['unreviewed']='extra';p.write_bytes(m.encode(v));e['MERGED_PR.json']=m.binding(p);self.assertRaises(ValueError,m.require_merge,e)
 def test_missing_original_result_fails_closed(self):
  _,_,e=self.copied();Path(self.evidence['RESULT.json']['path']).rename(self.root/'old-result-retained.json');self.assertRaises(ValueError,m.require_merge,e)
 def test_original_result_changed_even_when_three_objects_match(self):
  _,_,e=self.copied();Path(self.evidence['RESULT.json']['path']).write_bytes(b'{}');self.assertRaises(ValueError,m.require_merge,e)
 def test_wrong_role_basename_rejected(self):
  _,_,e=self.copied();p=Path(e['MERGED_PR.json']['path']);q=p.with_name('FOREIGN_ROLE.json');q.write_bytes(p.read_bytes());e['MERGED_PR.json']=m.binding(q);self.assertRaises(ValueError,m.require_merge,e)
 def test_original_wrong_role_rejected(self):
  _,_,e=self.copied();result=json.loads(m.raw(e['RESULT.json']['path']));result['merged_pr']=self.evidence['MERGED_COMMIT.json'];self.assertRaises(ValueError,m._exact_rebound_merge_references,e,result)
 def test_mixed_canonical_parent_rejected(self):
  _,_,e=self.copied();p=Path(e['MERGED_PR.json']['path']);q=self.root/'reports/verification-coverage/other/merge-evidence'/p.name;q.parent.mkdir(parents=True);q.write_bytes(p.read_bytes());e['MERGED_PR.json']=m.binding(q);self.assertRaises(ValueError,m.require_merge,e)
 def test_original_reference_mixed_parent_rejected(self):
  _,_,e=self.copied();p=Path(self.evidence['MERGED_PR.json']['path']);q=self.root/'other-original'/p.name;q.parent.mkdir();q.write_bytes(p.read_bytes());result=json.loads(m.raw(e['RESULT.json']['path']));result['merged_pr']=m.binding(q);self.assertRaises(ValueError,m._exact_rebound_merge_references,e,result)
 def test_dotdot_alias_rejected(self):
  _,_,e=self.copied();p=Path(e['MERGED_PR.json']['path']);e['MERGED_PR.json']['path']=str(p.parent/'..'/'merge-evidence'/p.name);self.assertRaises(ValueError,m.require_merge,e)
 def test_double_slash_alias_rejected(self):
  _,_,e=self.copied();e['MERGED_PR.json']['path']=e['MERGED_PR.json']['path'].replace('/merge-evidence/','/merge-evidence//');self.assertRaises(ValueError,m.require_merge,e)
 def test_current_symlink_rejected(self):
  _,_,e=self.copied();p=Path(e['MERGED_PR.json']['path']);q=p.with_name('saved-pr.json');p.rename(q);p.symlink_to(q);self.assertRaises(ValueError,m.require_merge,e)
 def test_original_symlink_rejected(self):
  _,_,e=self.copied();p=Path(self.evidence['MERGED_PR.json']['path']);q=p.with_name('saved-original-pr.json');p.rename(q);p.symlink_to(q);self.assertRaises(ValueError,m.require_merge,e)
 def test_original_scope_outside_tmp_is_rejected(self):
  _,_,e=self.copied();m.TMP=self.root/'different';self.assertRaises(ValueError,m.require_merge,e)
 def test_extra_key_and_wrong_type_are_rejected(self):
  _,_,e=self.copied();result=json.loads(m.raw(e['RESULT.json']['path']))
  for bad in [{**result['merged_pr'],'extra':True},{**result['merged_pr'],'sha256':123}]:
   changed=copy.deepcopy(result);changed['merged_pr']=bad;self.assertRaises(ValueError,m._exact_rebound_merge_references,e,changed)
if __name__=='__main__':unittest.main()
