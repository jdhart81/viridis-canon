"""Synthetic closed-runtime succession fixtures; no deployment or verification."""
import copy,datetime as dt,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import phase7_runtime_update as m

def encoded(x):return (json.dumps(x,sort_keys=True,indent=2)+'\n').encode()
def gitblob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

class Fixture:
 def __init__(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.now=dt.datetime(2026,10,7,14,tzinfo=dt.timezone.utc)
  self.paths={};self.rows=[];self.base=[];self.live={};self.prfiles=[];self.selectorfiles=[]
  for i in range(22):
   name=('corpus_ledger.py','nightly_coverage.py')[i] if i<2 else 'unchanged_%02d.py'%i
   rel=m.GATE_PREFIX+name;old=('old '+name).encode();new=('new '+name).encode() if i<2 else old
   self.write(rel,new);source='evidence/source/'+name;self.write(source,new);self.live[rel]=new
   self.base.append({'relative_path':rel,'after_sha256':hashlib.sha256(old).hexdigest()})
   self.rows.append({'path':rel,'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':m.sha(self.root/rel),'source':self.bound(source)})
   if i<2:(self.selectorfiles if i==0 else self.prfiles).append({'path':'00_lab_infrastructure/gates/'+name,'sha':gitblob(new)})
  self.write(m.GATE_PREFIX+'certificate_selection.py',b'approved selector fixture')
  self.write(m.GATE_PREFIX+'phase7_runtime_update.py',b'synthetic helper bytes not executed');self.write('evidence/source/phase7_runtime_update.py',b'synthetic helper bytes not executed')
  self.prfiles.append({'path':'00_lab_infrastructure/gates/phase7_runtime_update.py','sha':gitblob(b'synthetic helper bytes not executed')})
  self.ccraw=("INSTALLED_GUARD_SHA256 = '"+m.sha(self.root/(m.GATE_PREFIX+'nightly_coverage.py'))+"'\n").encode();self.write(m.GATE_PREFIX+'closeout_streak.py',self.ccraw);self.write('evidence/source/closeout_streak.py',self.ccraw);self.prfiles.append({'path':'00_lab_infrastructure/gates/closeout_streak.py','sha':gitblob(self.ccraw)})
  self.section=b'## Phase 7 \xe2\x80\x94 Claude audit of release packet v002 \xe2\x80\x94 2026-10-07\n\nSYNTHETIC UNIT AUTHORITY, NOT REAL REVIEW\n'
  self.write('reports/verification-coverage/GAME_PLAN.md',b'# Synthetic\n'+self.section+b'\n## Next\nLater\n');self.write('evidence/authority.md',self.section)
  self.write('evidence/baseline.json',encoded({'synthetic':True}));self.protected={'status':'LIVE_PROTECTED_HASH_READBACK_PASS','at_utc':'2026-10-07T13:45:00Z','baseline_sha256':m.sha(self.root/'evidence/baseline.json'),'remote_script_writes':0,'restarts':0,'certification_attempts':0,'checks':[{'path':'/synthetic/protected/%s'%i,'surface':'DEPLOYED_DROPLET' if i<17 else 'LOCAL','expected_sha256':hashlib.sha256(str(i).encode()).hexdigest(),'actual_sha256':hashlib.sha256(str(i).encode()).hexdigest(),'match':True}for i in range(22)]}
  self.write('evidence/original_protected.json',encoded(self.protected));self.write('evidence/current_protected.json',encoded(self.protected));self.write('evidence/original_manifest.json',encoded({'snapshots':self.base}))
  self.original={'standard':'SYNTHETIC_NOT_ACTIVATION','activated_at_utc':'2026-10-06T12:00:00Z','proofs':{'after_manifest':self.bound('evidence/original_manifest.json'),'protected_baseline':self.bound('evidence/baseline.json')},'sources':{'protected_readback':self.bound('evidence/original_protected.json')}}
  self.write('evidence/original_activation.json',encoded(self.original))
  self.pr={'state':'MERGED','baseRefName':'main','url':'https://github.com/jdhart81/viridis-canon/pull/56','number':56,'mergeCommit':{'oid':'a'*40},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in sorted(m.REQUIRED_CHECKS)],'files':self.prfiles}
  self.selector={'number':55,'state':'MERGED','baseRefName':'main','url':'https://github.com/jdhart81/viridis-canon/pull/55','mergeCommit':{'oid':'bd7746b8fe01a8ede95db27cd553978fb4733dbb'},'files':self.selectorfiles}
  self.r={'standard':m.STANDARD,'status':'INSTALLED_HASH_READBACK_PASS','profile':'RUN187_SELECTOR','tree_root':str(self.root),'installed_at_utc':'2026-10-07T13:30:00Z','original_activation':self.bound('evidence/original_activation.json'),'original_after_manifest':self.original['proofs']['after_manifest'],'audit_section':self.bound('evidence/authority.md'),'pull_request_readback':None,'selector_pull_request_readback':None,'runtime_targets':self.rows,'additional_modules':[{'path':m.GATE_PREFIX+'phase7_runtime_update.py','sha256':m.sha(self.root/(m.GATE_PREFIX+'phase7_runtime_update.py')),'source':self.bound('evidence/source/phase7_runtime_update.py')},{'path':m.GATE_PREFIX+'closeout_streak.py','sha256':m.sha(self.root/(m.GATE_PREFIX+'closeout_streak.py')),'source':self.bound('evidence/source/closeout_streak.py')}],'protected_readback':None}
  self.patches=[patch.object(m,'CORPUS_SHA256',m.sha(self.root/(m.GATE_PREFIX+'corpus_ledger.py'))),patch.object(m,'SELECTOR_SHA256',m.sha(self.root/(m.GATE_PREFIX+'certificate_selection.py'))),patch.object(m,'APPROVED_AUDIT_SECTION_SHA256',hashlib.sha256(self.section).hexdigest())]
  for p in self.patches:p.start()
  self.commit()
 def write(self,rel,data):p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 def bound(self,rel):return {'path':rel,'sha256':m.sha(self.root/rel)}
 def commit(self):
  self.write('evidence/pr.json',encoded(self.pr));self.write('evidence/selector_pr.json',encoded(self.selector));self.write('evidence/current_protected.json',encoded(self.protected))
  self.r['pull_request_readback']=self.bound('evidence/pr.json');self.r['selector_pull_request_readback']=self.bound('evidence/selector_pr.json');self.r['protected_readback']=self.bound('evidence/current_protected.json')
  self.write('evidence/update.json',encoded(self.r));self.wrapper=copy.deepcopy(self.original);self.wrapper['authorized_runtime_update']=self.bound('evidence/update.json');self.write('evidence/wrapper.json',encoded(self.wrapper));self.ledger={'enforcement_activation':self.bound('evidence/wrapper.json')};self.write('RESEARCH_PIPELINE_v2/corpus_ledger.json',encoded(self.ledger))
 def validate(self):return m.validate(self.root,self.ledger,self.original,now=self.now)
 def close(self):
  for p in reversed(self.patches):p.stop()
  self.tmp.cleanup()

class RuntimeUpdateTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def hold(self,call=None):
  with self.assertRaises((ValueError,FileNotFoundError,KeyError)): (call or self.f.validate)()
 def test_closed_selector_update_pass(self):v=self.f.validate();self.assertEqual(len(v['targets']),22);self.assertEqual(v['profile'],'RUN187_SELECTOR')
 def test_unwrap_original_byte_provenance_pass(self):self.assertEqual(m.unwrap_activation(self.f.root,self.f.wrapper,now=self.f.now),self.f.original)
 def test_now_keyword_runtime_changed_pass(self):r=self.f.rows[0];self.assertEqual(m.current_runtime_binding(self.f.root,r['path'],r['before_sha256'],self.f.original,now=self.f.now),{'path':r['path'],'sha256':r['after_sha256']})
 def test_old_unchanged_fast_binding_pass(self):r=self.f.rows[2];self.assertEqual(m.current_runtime_binding(self.f.root,r['path'],r['before_sha256'],self.f.original,now=self.f.now)['sha256'],r['before_sha256'])
 def test_altered_other20_target_holds(self):r=self.f.rows[2];self.f.write(r['path'],b'changed');self.f.write(r['source']['path'],b'changed');r['after_sha256']=m.sha(self.f.root/r['path']);r['source']=self.f.bound(r['source']['path']);self.f.commit();self.hold()
 def test_out_profile_holds(self):self.f.r['profile']='FOUNDATIONAL';self.f.commit();self.hold()
 def test_wrong_authority_holds(self):self.f.write('evidence/authority.md',b'wrong');self.f.r['audit_section']=self.f.bound('evidence/authority.md');self.f.commit();self.hold()
 def test_game_plan_current_section_changed_holds(self):self.f.write('reports/verification-coverage/GAME_PLAN.md',self.f.section+b'CHANGED');self.hold()
 def test_future_install_holds(self):self.f.r['installed_at_utc']='2026-10-08T13:30:00Z';self.f.commit();self.hold()
 def test_naive_install_holds(self):self.f.r['installed_at_utc']='2026-10-07T13:30:00';self.f.commit();self.hold()
 def test_foreign_pr_holds(self):self.f.pr['url']='https://github.com/foreign/repo/pull/56';self.f.commit();self.hold()
 def test_foreign_selector_pr_holds(self):self.f.selector['url']='https://github.com/foreign/repo/pull/55';self.f.commit();self.hold()
 def test_unmerged_pr_holds(self):self.f.pr['state']='OPEN';self.f.commit();self.hold()
 def test_check_failure_holds(self):self.f.pr['statusCheckRollup'][0]['conclusion']='FAILURE';self.f.commit();self.hold()
 def test_source_blob_not_merged_holds(self):self.f.pr['files'][0]['sha']='c'*40;self.f.commit();self.hold()
 def test_source_hash_changed_holds(self):self.f.write(self.f.rows[1]['source']['path'],b'mutated');self.hold()
 def test_missing_protected_holds(self):self.f.protected['checks'].pop();self.f.commit();self.hold()
 def test_duplicate_protected_holds(self):self.f.protected['checks'][-1]=copy.deepcopy(self.f.protected['checks'][0]);self.f.commit();self.hold()
 def test_foreign_protected_holds(self):self.f.protected['checks'][0]['path']='/foreign/path';self.f.commit();self.hold()
 def test_protected_hash_change_even_matching_holds(self):self.f.protected['checks'][0]['actual_sha256']='d'*64;self.f.protected['checks'][0]['expected_sha256']='d'*64;self.f.commit();self.hold()
 def test_preinstall_protected_readback_holds(self):self.f.protected['at_utc']='2026-10-07T13:00:00Z';self.f.commit();self.hold()
 def test_future_protected_holds(self):self.f.protected['at_utc']='2026-10-08T13:00:00Z';self.f.commit();self.hold()
 def test_protected_write_holds(self):self.f.protected['remote_script_writes']=1;self.f.commit();self.hold()
 def test_certification_attempt_holds(self):self.f.protected['certification_attempts']=1;self.f.commit();self.hold()
 def test_original_wrapper_field_changed_holds(self):self.f.wrapper['activated_at_utc']='2026-10-07T12:00:00Z';self.f.write('evidence/wrapper.json',encoded(self.f.wrapper));self.f.ledger['enforcement_activation']=self.f.bound('evidence/wrapper.json');self.hold()
 def test_original_archival_file_changed_holds(self):self.f.write('evidence/original_activation.json',encoded({'changed':True}));self.hold()
 def test_nomination_foreign_wrapper_holds(self):w=copy.deepcopy(self.f.wrapper);w['extra']='wrong';self.hold(lambda:m.unwrap_activation(self.f.root,w,now=self.f.now))
 def test_traversal_runtime_path_holds(self):self.hold(lambda:m.current_runtime_binding(self.f.root,'../escape','a'*64,self.f.original,now=self.f.now))
 def test_bound_runtime_symlink_holds(self):p=self.f.root/self.f.rows[2]['path'];p.unlink();p.symlink_to(self.f.root/self.f.rows[3]['path']);self.hold()
 def test_duplicate_pr_files_holds(self):self.f.pr['files'].append(copy.deepcopy(self.f.pr['files'][0]));self.f.commit();self.hold()
 def test_duplicate_manifest_original_holds(self):self.f.write('evidence/original_manifest.json',encoded({'snapshots':self.f.base+[self.f.base[0]]}));self.hold()
 def test_closeout_guard_pin_matches_current_22_loop(self):
  self.f.validate();raw=(self.f.root/(m.GATE_PREFIX+'closeout_streak.py')).read_text();self.assertIn(self.f.rows[1]['after_sha256'],raw);self.assertEqual({v['path']for v in self.f.r['runtime_targets']},{v['relative_path']for v in self.f.base})
 def test_closeout_old_pin_holds_even_exact_pr_blob(self):
  raw=("INSTALLED_GUARD_SHA256 = '"+self.f.rows[1]['before_sha256']+"'\n").encode();v=self.f.r['additional_modules'][1];self.f.write(v['path'],raw);self.f.write(v['source']['path'],raw);v['sha256']=m.sha(self.f.root/v['path']);v['source']=self.f.bound(v['source']['path']);self.f.pr['files'][-1]['sha']=gitblob(raw);self.f.commit();self.hold()
 def test_missing_closeout_module_holds(self):self.f.r['additional_modules'].pop();self.f.commit();self.hold()
 def test_unlisted_added_module_holds(self):self.f.r['additional_modules'].append(copy.deepcopy(self.f.r['additional_modules'][0]));self.f.commit();self.hold()

if __name__=='__main__':unittest.main()
