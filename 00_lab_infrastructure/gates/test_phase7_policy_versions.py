"""Synthetic version/provenance fixtures, no real proof or approval is claimed."""
import hashlib,json,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
import methods_digest as d
import phase7_policy_versions as v

def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d.raw_json(obj));return {'path':str(p),'sha256':d.sha(p)}

class VersionTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.r=Path(self.t.name).resolve();self.note=self.r/'note';self.note.mkdir();self.cur=self.r/'new_default.py';self.cur.write_bytes(b'# current version is different\n');self.current=types.SimpleNamespace(__file__=str(self.cur))
  contract=b'{"closed": "old exact contract"}\n';h=d.digest(contract)
  source=("CONTRACT_SHA='"+h+"'\nimport json\nfrom pathlib import Path\nimport methods_digest as d\nfrom certificate_inspection import inspect_certificate\ndef require_note_publication_bound(note,root,authority):\n rule=json.loads((Path(note)/'PHASE7_RULE_EXECUTION.json').read_bytes())\n if d.sha(Path(note)/'CURRENT_INPUT')!=rule['input_sha']:raise ValueError('changed input')\n seen=inspect_certificate(Path(note)/'certificate.json',Path(root))\n if seen.get('valid')is not True:raise ValueError('fresh current inspector held')\n return {'status':'PUBLICATION_BOUND','exact_publication_binding':True,'execution_consumer_sha256':d.sha(__file__)}\ndef prepare_publication_binding(note,root,authority,*,at_utc=None):\n return require_note_publication_bound(note,root,authority)\n").encode();self.sha=d.digest(source);self.base=self.r/'policy_versions'/self.sha;self.base.mkdir(parents=True);self.files=[]
  for name in sorted(v.NAMES):
   p=self.base/name
   raw=source if name=='phase7_audit_policy.py'else contract if name=='PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json'else b"from pathlib import Path\nimport hashlib\ndef sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"if name=='methods_digest.py'else b'# exact synthetic helper\n'
   p.write_bytes(raw);self.files.append({'name':name,'binding':{'path':str(p),'sha256':d.sha(p)},'git_path':'00_lab_infrastructure/gates/policy_versions/'+self.sha+'/'+name})
  self.pr={'state':'MERGED','baseRefName':'main','number':999,'url':'https://github.com/jdhart81/viridis-canon/pull/999','mergeCommit':{'oid':'a'*40},'statusCheckRollup':[{'name':name,'status':'COMPLETED','conclusion':'SUCCESS'}for name in v.CHECKS],'files':[{'path':row['git_path'],'sha':hashlib.sha1(b'blob '+str((self.base/row['name']).stat().st_size).encode()+b'\0'+(self.base/row['name']).read_bytes()).hexdigest()}for row in self.files]};self.pr_binding=save(self.r/'pr.json',self.pr);self.entry={'execution_consumer_sha256':self.sha,'files':self.files,'pull_request_readback':self.pr_binding};self.catalog={'standard':v.STANDARD,'status':'MERGED_SOURCE_CATALOG','tree_root':str(self.r),'versions':[self.entry]}
  (self.note/'CURRENT_INPUT').write_bytes(b'exact original source');save(self.note/'certificate.json',{'fixture':True});self.rule={'execution_consumer_sha256':self.sha,'input_sha':d.sha(self.note/'CURRENT_INPUT')};save(self.note/'PHASE7_RULE_EXECUTION.json',self.rule);self.calls=[]
 def catalog_consumer(self,root,seen):return deepcopy(self.catalog)
 def select(self):return v.implementation_for_note(self.note,self.r,self.current,catalog_consumer=self.catalog_consumer)
 def fake_inspector(self,*args):self.calls.append(args);return {'valid':True,'synthetic_fixture_only':True}
 def invoke(self):
  with patch('certificate_inspection.inspect_certificate',side_effect=self.fake_inspector):
   module=self.select();result=module.require_note_publication_bound(self.note,self.r,{})
   v._finish(module._phase7_version_source_inputs);return result
 def test_old_issued_note_survives_new_default_with_fresh_current_inspector(self):
  self.assertTrue(self.invoke()['exact_publication_binding']);self.cur.write_bytes(b'# third current version\n');self.assertTrue(self.invoke()['exact_publication_binding']);self.assertEqual(len(self.calls),2)
 def test_old_changed_input_still_holds_after_default_change(self):
  self.invoke();(self.note/'CURRENT_INPUT').write_bytes(b'changed theorem premise');self.assertRaises(ValueError,self.invoke)
 def test_fresh_inspector_hold_not_cached_old_pass(self):
  self.invoke()
  with patch('certificate_inspection.inspect_certificate',return_value={'valid':False}):self.assertRaises(ValueError,lambda:self.select().require_note_publication_bound(self.note,self.r,{}))
 def test_unknown_consumer_hold(self):self.rule['execution_consumer_sha256']='f'*64;save(self.note/'PHASE7_RULE_EXECUTION.json',self.rule);self.assertRaises(ValueError,self.select)
 def test_missing_consumer_not_default_pass(self):del self.rule['execution_consumer_sha256'];save(self.note/'PHASE7_RULE_EXECUTION.json',self.rule);self.assertRaises(ValueError,self.select)
 def test_modified_archived_policy_hold(self):(self.base/'phase7_audit_policy.py').write_bytes(b'# forged pass');self.assertRaises(ValueError,self.select)
 def test_modified_contract_hold(self):(self.base/'PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json').write_bytes(b'{}');self.assertRaises(ValueError,self.select)
 def test_missing_label_renderer_hold(self):(self.base/'phase7_claim_label_render.py').unlink();self.assertRaises(Exception,self.select)
 def test_unmerged_source_hold(self):self.pr['state']='OPEN';self.entry['pull_request_readback']=save(self.r/'pr.json',self.pr);self.assertRaises(ValueError,self.select)
 def test_repository_checks_fail_closed(self):self.pr['statusCheckRollup'][0]['conclusion']='FAILURE';self.entry['pull_request_readback']=save(self.r/'pr.json',self.pr);self.assertRaises(ValueError,self.select)
 def test_wrong_merged_git_blob_hold(self):self.pr['files'][0]['sha']='a'*40;self.entry['pull_request_readback']=save(self.r/'pr.json',self.pr);self.assertRaises(ValueError,self.select)
 def test_duplicate_version_hold(self):self.catalog['versions'].append(deepcopy(self.entry));self.assertRaises(ValueError,self.select)
 def test_missing_version_dependency_hold(self):self.entry['files'].pop();self.assertRaises(ValueError,self.select)
 def test_arbitrary_extra_version_file_hold(self):self.entry['files'].append(self.entry['files'][0]);self.assertRaises(ValueError,self.select)
 def test_foreign_note_hold(self):self.assertRaises(ValueError,v.implementation_for_note,self.r.parent,self.r,self.current,catalog_consumer=self.catalog_consumer)
 def test_same_actual_current_default_preserves_existing_behavior(self):self.cur.write_bytes((self.base/'phase7_audit_policy.py').read_bytes());self.assertIs(v.implementation_for_note(self.note,self.r,self.current),self.current)
 def test_runtime_catalog_is_source_bound_not_a_caller_flag(self):
  c=save(self.r/'catalog.json',self.catalog);original=save(self.r/'original.json',{'fixture':True});runtime=save(self.r/'runtime.json',{'original_activation':original,'standard':'VRS-PHASE7-AUTHORIZED-RUNTIME-UPDATE-1','status':'INSTALLED_HASH_READBACK_PASS','profile':'PHASE7_SCOPED_POLICY','tree_root':str(self.r),'policy_version_catalog':c});a=save(self.r/'activation.json',{'authorized_runtime_update':runtime});save(self.r/'RESEARCH_PIPELINE_v2/corpus_ledger.json',{'enforcement_activation':a});seen={}
  with patch('phase7_runtime_update.validate',return_value={'profile':'PHASE7_SCOPED_POLICY','binding':runtime})as validator:
   self.assertEqual(v.current_catalog(self.r,seen)['versions'],self.catalog['versions']);self.assertEqual(validator.call_count,1);self.assertIn(str(self.r/'RESEARCH_PIPELINE_v2/corpus_ledger.json'),seen);(self.r/'catalog.json').write_bytes(b'{}');self.assertRaises(ValueError,v.current_catalog,self.r,{})
 def test_bad_unselected_catalog_version_is_not_silently_ignored(self):
  other=deepcopy(self.entry);other['execution_consumer_sha256']='b'*64;self.catalog['versions'].append(other);self.assertRaises(ValueError,self.select)
 def test_no_catalog_before_runtime_install_is_hold(self):self.assertRaises(Exception,v.current_catalog,self.r,{})

if __name__=='__main__':unittest.main()
