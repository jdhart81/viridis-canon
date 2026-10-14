"""Actual-shaped synthetic predecessor provenance; no production admission."""
from copy import deepcopy
import hashlib,json
from pathlib import Path
import sys,tempfile,unittest,contextlib
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import packaging_runtime as runtime


def put(root,name,value):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_bytes((json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
 return {'path':str(p),'sha256':runtime.sha(p.read_bytes())}


class FrozenV004PredecessorTests(unittest.TestCase):
 def fixture(self,root):
  prototype=root/'candidate';installed=root/'installed';prototype.mkdir();installed.mkdir()
  rows=[];current=[];git=[]
  for name in sorted(runtime.MODULE_NAMES):
   raw=('# reviewed synthetic predecessor '+name+'\n').encode()
   for directory in(prototype,installed):(directory/name).write_bytes(raw)
   row={'name':name,'path':str(prototype/name),'sha256':runtime.sha(raw),'git_path':'00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v004/'+name}
   rows.append(row);current.append({**row,'path':str(installed/name)})
   git.append({'path':row['git_path'],'type':'blob','mode':'100644','sha':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()})
  pr=put(root,'pr.json',{'state':'MERGED','baseRefName':'main','number':999,'url':'https://github.com/jdhart81/viridis-canon/pull/999','mergeCommit':{'oid':'a'*40},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in runtime.REQUIRED_CHECKS]})
  commit=put(root,'commit.json',{'sha':'a'*40,'tree':{'sha':'b'*40}})
  tree=put(root,'tree.json',{'sha':'b'*40,'truncated':False,'tree':git})
  anchor=put(root,'anchor.json',{'synthetic_only':True})
  alias=put(root,'alias-observation.json',{'synthetic_only':True,'writes':0})
  review=put(root,'review.json',{'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-4','review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK','source_hashes':{r['name']:r['sha256']for r in rows}})
  shared={'source_origin':{'pull_request':pr,'merge_commit':commit,'tree':tree},'source_review':review,'user_authority':anchor,'access_registry':anchor,'installed_at_utc':'2020-01-01T00:00:00Z','transient_rehydration':runtime.TRANSIENT_REHYDRATION_POLICY,'predecessor_installation':{'v001':runtime.V001_INSTALLATION,'v002':runtime.V002_INSTALLATION,'v003':runtime.V003_INSTALLATION},'data_alias_observation':alias,'platform_timezone_observation':alias}
  profile=put(root,'profile.json',{'standard':'VRS-STANDALONE-PDF-PACKAGING-PROFILE-4','canonical_root':str(root),'modules':current,**shared})
  plan=put(root,'plan.json',{'standard':'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-4','source_modules':rows,'root_review':anchor,**shared})
  nomination=put(root,'nomination.json',{'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-4','status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING','profile':profile,'merged_source_commit':'a'*40,'root_review_receipt':anchor,'installer_source':{k:next(r for r in rows if r['name']=='install_packaging_runtime.py')[k]for k in('path','sha256')}})
  publisher=root/'publisher.py';publisher.write_bytes(b'# unchanged historical publisher\n')
  bindings={'V004_PROFILE':profile,'V004_PLAN':plan,'V004_NOMINATION':nomination,'DATA_ALIAS_OBSERVATION':alias,'PLATFORM_TIMEZONE_OBSERVATION':alias,'HISTORICAL_PUBLISHER':{'path':str(publisher),'sha256':runtime.sha(publisher.read_bytes())}}
  return bindings,rows,current,publisher
 def consume(self,root,bindings):
  with contextlib.ExitStack()as stack:
   for key,value in bindings.items():stack.enter_context(patch.object(runtime,key,value))
   stack.enter_context(patch.object(runtime,'v003_predecessor_installation',return_value={'prior_fixtures':'tested separately, no live verdict'}))
   return runtime.v004_predecessor_installation(root)
 def test_all17_installed_and_source_git_bindings_preserve_failed_v004_without_execution(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp).resolve();bindings,rows,current,publisher=self.fixture(root)
   before={str(p):p.read_bytes()for p in root.rglob('*')if p.is_file()}
   with patch.object(runtime,'load',side_effect=AssertionError('no executable predecessor load')):
    value=self.consume(root,bindings)
   self.assertFalse(value['actual_runtime_admission']);self.assertFalse(value['certifies'])
   self.assertEqual(before,{str(p):p.read_bytes()for p in root.rglob('*')if p.is_file()})
   self.assertEqual(len(value['v004']['merged_source']['proofs']),17)
 def test_changed_v004_module_or_fixed_metadata_holds_without_overwrite(self):
  for field in('source','installed','profile','plan','nomination'):
   with self.subTest(field=field),tempfile.TemporaryDirectory()as tmp:
    root=Path(tmp).resolve();bindings,rows,current,publisher=self.fixture(root)
    path=Path(rows[0]['path']if field=='source'else current[0]['path']if field=='installed'else bindings['V004_'+field.upper()]['path'])
    changed=path.read_bytes()+b'changed';path.write_bytes(changed)
    with self.assertRaises(runtime.PackagingHold):self.consume(root,bindings)
    self.assertEqual(path.read_bytes(),changed)
 def test_rebound_wrong_prior_review_or_profile_relation_cannot_claim_runtime_success(self):
  with tempfile.TemporaryDirectory()as tmp:
   root=Path(tmp).resolve();bindings,rows,current,publisher=self.fixture(root)
   n=json.loads(Path(bindings['V004_NOMINATION']['path']).read_bytes());n['status']='FRESH_DEFAULT_FULL_POPULATION_READBACK_PASS'
   bindings['V004_NOMINATION']=put(root,'nomination.json',n)
   with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_FROZEN_V004_INSTALLATION'):self.consume(root,bindings)
   n['status']='EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING';n['root_review_receipt']=put(root,'unrelated.json',{})
   bindings['V004_NOMINATION']=put(root,'nomination.json',n)
   with self.assertRaisesRegex(runtime.PackagingHold,'FROZEN_V004_SOURCE_AND_NOMINATION'):self.consume(root,bindings)

if __name__=='__main__':unittest.main()
