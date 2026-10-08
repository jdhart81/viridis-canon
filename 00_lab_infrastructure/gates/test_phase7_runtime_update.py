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
   if i==0:new=b"import json\nSETTING = 'UNCHANGED'\ndef certificate_lookup(ledger):\n    return ledger\ndef preserve_publication_registrations(ledger, previous):\n    return {'ledger': ledger, 'previous': previous}\n"+b"if __name__ == '__main__':\n    raise SystemExit(0)\n"
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
  self.write('evidence/baseline.json',encoded({'synthetic':True}));self.protected={'status':'LIVE_PROTECTED_HASH_READBACK_PASS','at_utc':'2026-10-07T13:00:00Z','baseline_sha256':m.sha(self.root/'evidence/baseline.json'),'remote_script_writes':0,'restarts':0,'certification_attempts':0,'checks':[{'path':'/synthetic/protected/%s'%i,'surface':'DEPLOYED_DROPLET' if i<17 else 'LOCAL','expected_sha256':hashlib.sha256(str(i).encode()).hexdigest(),'actual_sha256':hashlib.sha256(str(i).encode()).hexdigest(),'match':True}for i in range(22)]}
  self.write('evidence/original_protected.json',encoded(self.protected));self.protected['at_utc']='2026-10-07T13:50:00Z';self.write('evidence/current_protected.json',encoded(self.protected));self.write('evidence/original_manifest.json',encoded({'snapshots':self.base}))
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
 def test_readback_before_install_holds(self):self.f.protected['at_utc']='2026-10-07T13:29:00Z';self.f.commit();self.hold()
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


class PolicyFixture(Fixture):
 def __init__(self):
  super().__init__()
  # A synthetic original22 actually contains premise_declaration, as production does.
  row=self.rows[2];oldrel=row['path'];name='premise_declaration.py';rel=m.GATE_PREFIX+name;old=b'old premise checker fixture'
  self.write(rel,old);self.write('evidence/source/'+name,old)
  self.base[2]={'relative_path':rel,'after_sha256':hashlib.sha256(old).hexdigest()}
  self.rows[2]={'path':rel,'before_sha256':hashlib.sha256(old).hexdigest(),'after_sha256':hashlib.sha256(old).hexdigest(),'source':self.bound('evidence/source/'+name)}
  self.pub_original=b"import json\ndef sha256(raw):\n    return raw\ndef evaluate_publication(artifact, ledger):\n    return {'kind': 'ordinary'}\n"
  self.pub_scoped=self.pub_original.replace(b"'ordinary'",b"'scoped'")
  self.doi_original=b"def build_audit(root, cert_root):\n    return {'root': root, 'cert_root': cert_root}\n"
  self.reader_original=b"def read_record(row):\n    return {'row': row}\ndef readback(rows):\n    return rows\n"
  for i,name,raw in ((3,'publication_gate.py',self.pub_original),(4,'doi_audit.py',self.doi_original)):
   rel=m.GATE_PREFIX+name;source='evidence/source/'+name;self.write(rel,raw);self.write(source,raw);self.base[i]={'relative_path':rel,'after_sha256':hashlib.sha256(raw).hexdigest()};self.rows[i]={'path':rel,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(raw).hexdigest(),'source':self.bound(source)}
  self.write('evidence/publication_scoped_baseline.py',self.pub_scoped);self.write('evidence/public_reader_baseline.py',self.reader_original)
  self.write('evidence/original_manifest.json',encoded({'snapshots':self.base}));self.original['proofs']['after_manifest']=self.bound('evidence/original_manifest.json');self.write('evidence/original_activation.json',encoded(self.original));self.r['original_activation']=self.bound('evidence/original_activation.json');self.r['original_after_manifest']=self.original['proofs']['after_manifest']
  self.pr.update(number=57,url='https://github.com/jdhart81/viridis-canon/pull/57',mergeCommit={'oid':m.PREVIOUS_SELECTOR_MERGE_COMMIT})
  baseline_patches=[patch.object(m,'PUBLICATION_ORIGINAL_SHA256',hashlib.sha256(self.pub_original).hexdigest()),patch.object(m,'PUBLICATION_SCOPED_SHA256',hashlib.sha256(self.pub_scoped).hexdigest()),patch.object(m,'DOI_AUDIT_SHA256',hashlib.sha256(self.doi_original).hexdigest()),patch.object(m,'PUBLIC_READER_SHA256',hashlib.sha256(self.reader_original).hexdigest())]
  self.patches.extend(baseline_patches)
  for p in baseline_patches:p.start()
  self.commit();previous=copy.deepcopy(self.r)
  # Prior source copies are immutable separate archival files.
  for v in previous['runtime_targets']+previous['additional_modules']:
   archived='evidence/prior/'+Path(v['source']['path']).name;self.write(archived,(self.root/v['source']['path']).read_bytes());v['source']=self.bound(archived)
  self.write('evidence/pr57.json',encoded(self.pr));previous['pull_request_readback']=self.bound('evidence/pr57.json')
  self.write('evidence/prior/protected_readback.json',(self.root/previous['protected_readback']['path']).read_bytes());previous['protected_readback']=self.bound('evidence/prior/protected_readback.json')
  self.write('evidence/prior_update.json',encoded(previous));self.previous=previous
  self.patches.extend([patch.object(m,'PREVIOUS_SELECTOR_RECEIPT_SHA256',m.sha(self.root/'evidence/prior_update.json')),patch.object(m,'GUARD_SHA256',m.sha(self.root/(m.GATE_PREFIX+'nightly_coverage.py'))),patch.object(m,'CLOSEOUT_SHA256',m.sha(self.root/(m.GATE_PREFIX+'closeout_streak.py')))])
  for p in self.patches[-3:]:p.start()
  self.r['profile']='PHASE7_SCOPED_POLICY';self.r['previous_runtime_update']=self.bound('evidence/prior_update.json');self.r['installed_at_utc']='2026-10-07T13:45:00Z'
  self.r['publication_gate_scoped_baseline']=self.bound('evidence/publication_scoped_baseline.py');self.r['public_metadata_readback_baseline']=self.bound('evidence/public_reader_baseline.py')
  rel=m.GATE_PREFIX+'premise_declaration.py';name='premise_declaration.py';new=b'new approved premise checker fixture';self.write(rel,new);self.write('evidence/source/'+name,new);self.rows[2]['after_sha256']=m.sha(self.root/rel);self.rows[2]['source']=self.bound('evidence/source/'+name)
  self.pr={'number':58,'state':'MERGED','baseRefName':'main','url':'https://github.com/jdhart81/viridis-canon/pull/58','mergeCommit':{'oid':'b'*40},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in sorted(m.REQUIRED_CHECKS)],'files':[{'path':'00_lab_infrastructure/gates/premise_declaration.py','sha':gitblob(new)}]}
  old_corpus=(self.root/(m.GATE_PREFIX+'corpus_ledger.py')).read_bytes()
  guard=b"if __name__ == '__main__':\n    raise SystemExit(0)\n"
  self.asserted_original_corpus_cli=old_corpus.endswith(guard)
  if not self.asserted_original_corpus_cli:raise ValueError('synthetic original CLI fixture changed')
  wrapper=b'\ndef preserve_publication_registrations(ledger, previous):\n    return methods_digest_registration.preserve(ledger, previous, legacy=_preserve_publication_registrations_legacy)\n'
  new_corpus=old_corpus[:-len(guard)].replace(b'def preserve_publication_registrations(',b'def _preserve_publication_registrations_legacy(')+wrapper+guard
  cr=self.rows[0];self.write(cr['path'],new_corpus);self.write('evidence/policy_sources/corpus_ledger.py',new_corpus);cr['after_sha256']=m.sha(self.root/cr['path']);cr['source']=self.bound('evidence/policy_sources/corpus_ledger.py');self.pr['files'].append({'path':'00_lab_infrastructure/gates/corpus_ledger.py','sha':gitblob(new_corpus)})
  original_eval=self.pub_original[self.pub_original.index(b'def evaluate_publication'):]
  self.pub_new=self.pub_scoped.replace(b'def evaluate_publication(',b'def _evaluate_publication_scoped_legacy(')+b'\n'+original_eval.replace(b'def evaluate_publication(',b'def _evaluate_publication_original_legacy(')+b'\ndef evaluate_publication(artifact, ledger):\n    return methods_digest_registration.evaluate_publication(artifact, ledger, legacy=_evaluate_publication_original_legacy, scoped_legacy=_evaluate_publication_scoped_legacy)\n'
  self.doi_new=self.doi_original.replace(b'def build_audit(',b'def _build_audit_legacy(')+b'\ndef build_audit(root, cert_root):\n    return methods_digest_registration.augment_audit(root, cert_root, legacy=_build_audit_legacy)\n'
  self.reader_new=self.reader_original.replace(b'def read_record(',b'def _read_record_legacy(').replace(b'def readback(',b'def _readback_legacy(')+b'\ndef read_record(row):\n    return methods_digest_registration.public_label_read_record(row, legacy=_read_record_legacy)\ndef readback(rows):\n    return methods_digest_registration.public_label_readback(rows, legacy=_readback_legacy)\n'
  for i,name,raw in ((3,'publication_gate.py',self.pub_new),(4,'doi_audit.py',self.doi_new)):
   row=self.rows[i];source='evidence/policy_sources/'+name;self.write(row['path'],raw);self.write(source,raw);row['after_sha256']=m.sha(self.root/row['path']);row['source']=self.bound(source);self.pr['files'].append({'path':'00_lab_infrastructure/gates/'+name,'sha':gitblob(raw)})
  self.r['additional_modules']=[]
  for n in sorted(m.POLICY_MODULE_NAMES):
   raw=self.ccraw if n=='closeout_streak.py' else (self.reader_new if n=='public_metadata_readback.py' else ('new approved policy fixture '+n).encode())
   if n=='phase7_audit_policy.py': raw=("CONTRACT_SHA='"+hashlib.sha256(b'new approved policy fixture PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json').hexdigest()+"'\n").encode()
   p=m.GATE_PREFIX+n;s='evidence/policy_sources/'+n;self.write(p,raw);self.write(s,raw)
   self.r['additional_modules'].append({'path':p,'sha256':m.sha(self.root/p),'source':self.bound(s)})
   if n!='closeout_streak.py':self.pr['files'].append({'path':'00_lab_infrastructure/gates/'+n,'sha':gitblob(raw)})
  version=m.sha(self.root/(m.GATE_PREFIX+'phase7_audit_policy.py'));self.version=version;version_rows=[]
  for name in sorted(m.POLICY_VERSION_NAMES):
   raw=(self.root/(m.GATE_PREFIX+name)).read_bytes();rel=m.GATE_PREFIX+'policy_versions/'+version+'/'+name;source='evidence/version_sources/'+version+'/'+name;self.write(rel,raw);self.write(source,raw)
   self.r['additional_modules'].append({'path':rel,'sha256':m.sha(self.root/rel),'source':self.bound(source)})
   git_path='00_lab_infrastructure/gates/policy_versions/'+version+'/'+name;self.pr['files'].append({'path':git_path,'sha':gitblob(raw)});version_rows.append({'name':name,'binding':self.bound(rel),'git_path':git_path})
  self.write('evidence/archive_pr.json',encoded(self.pr));self.catalog={'standard':'VRS-PHASE7-POLICY-VERSIONS-1','status':'MERGED_SOURCE_CATALOG','tree_root':str(self.root),'versions':[{'execution_consumer_sha256':version,'files':version_rows,'pull_request_readback':self.bound('evidence/archive_pr.json')}]}
  self.write('evidence/policy_catalog.json',encoded(self.catalog));self.r['policy_version_catalog']=self.bound('evidence/policy_catalog.json')
  self.commit()

class PolicyUpdateTests(unittest.TestCase):
 def setUp(self):self.f=PolicyFixture()
 def tearDown(self):self.f.close()
 def hold(self,call=None):
  with self.assertRaises((ValueError,FileNotFoundError,KeyError)): (call or self.f.validate)()
 def module(self,name):return next(v for v in self.f.r['additional_modules'] if Path(v['path']).name==name)
 def test_approved_policy_update_pass(self):v=self.f.validate();self.assertEqual(v['profile'],'PHASE7_SCOPED_POLICY');self.assertEqual(len(v['targets']),22)
 def test_own_changed_premise_binding_pass(self):r=self.f.rows[2];self.assertEqual(m.current_runtime_binding(self.f.root,r['path'],r['before_sha256'],self.f.original,now=self.f.now)['sha256'],r['after_sha256'])
 def test_policy_unwrap_preserves_original_pass(self):self.assertEqual(m.unwrap_activation(self.f.root,self.f.wrapper,now=self.f.now),self.f.original)
 def test_prior_receipt_missing_holds(self):self.f.r.pop('previous_runtime_update');self.f.commit();self.hold()
 def test_prior_receipt_rehashed_change_holds(self):self.f.previous['installed_at_utc']='2026-10-07T13:29:00Z';self.f.write('evidence/prior_update.json',encoded(self.f.previous));self.f.r['previous_runtime_update']=self.f.bound('evidence/prior_update.json');self.f.commit();self.hold()
 def test_prior_receipt_source_mutation_holds(self):self.f.write(self.f.previous['additional_modules'][0]['source']['path'],b'mutated old source');self.hold()
 def test_prior_guard_origin_not_own_new_pr_pass(self):self.assertNotIn('00_lab_infrastructure/gates/nightly_coverage.py',{v['path'] for v in self.f.pr['files']});self.f.validate()
 def test_prior_closeout_origin_not_own_new_pr_pass(self):self.assertNotIn('00_lab_infrastructure/gates/closeout_streak.py',{v['path'] for v in self.f.pr['files']});self.f.validate()
 def test_unchanged18_targets_preserved(self):v=self.f.validate();self.assertEqual(sum(x['before_sha256']==x['after_sha256'] for x in self.f.rows),17);self.assertEqual(set(v['targets']),{x['relative_path'] for x in self.f.base})
 def test_foreign_new_module_holds(self):self.module('methods_digest.py')['path']=m.GATE_PREFIX+'unapproved.py';self.f.commit();self.hold()
 def test_missing_policy_module_holds(self):self.f.r['additional_modules'].pop();self.f.commit();self.hold()
 def test_duplicate_policy_module_holds(self):self.f.r['additional_modules'][0]=copy.deepcopy(self.f.r['additional_modules'][1]);self.f.commit();self.hold()
 def test_changed_guard_even_merged_holds(self):
  r=self.f.rows[1];raw=b'changed guard fixture';self.f.write(r['path'],raw);self.f.write(r['source']['path'],raw);r['after_sha256']=m.sha(self.f.root/r['path']);r['source']=self.f.bound(r['source']['path']);self.f.pr['files'].append({'path':'00_lab_infrastructure/gates/nightly_coverage.py','sha':gitblob(raw)});self.f.commit();self.hold()
 def test_changed_closeout_even_merged_holds(self):
  v=self.module('closeout_streak.py');raw=self.f.ccraw+b'changed=1\n';self.f.write(v['path'],raw);self.f.write(v['source']['path'],raw);v['sha256']=m.sha(self.f.root/v['path']);v['source']=self.f.bound(v['source']['path']);self.f.pr['files'].append({'path':'00_lab_infrastructure/gates/closeout_streak.py','sha':gitblob(raw)});self.f.commit();self.hold()
 def test_unlisted_original_target_holds(self):r=self.f.rows[3];raw=b'extra original change';self.f.write(r['path'],raw);self.f.write(r['source']['path'],raw);r['after_sha256']=m.sha(self.f.root/r['path']);r['source']=self.f.bound(r['source']['path']);self.f.pr['files'].append({'path':'00_lab_infrastructure/gates/'+Path(r['path']).name,'sha':gitblob(raw)});self.f.commit();self.hold()
 def test_new_pr_reuses_selector_pr_holds(self):self.f.pr.update(number=57,url='https://github.com/jdhart81/viridis-canon/pull/57',mergeCommit={'oid':m.PREVIOUS_SELECTOR_MERGE_COMMIT});self.f.commit();self.hold()
 def test_policy_before_prior_install_holds(self):self.f.r['installed_at_utc']='2026-10-07T13:20:00Z';self.f.commit();self.hold()
 def test_policy_future_install_holds(self):self.f.r['installed_at_utc']='2026-10-08T13:20:00Z';self.f.commit();self.hold()
 def test_policy_readback_before_install_holds(self):self.f.protected['at_utc']='2026-10-07T13:44:00Z';self.f.commit();self.hold()
 def test_new_module_source_wrong_blob_holds(self):next(v for v in self.f.pr['files'] if v['path'].endswith('methods_digest.py'))['sha']='c'*40;self.f.commit();self.hold()
 def test_premise_wrong_merged_blob_holds(self):self.f.pr['files'][0]['sha']='c'*40;self.f.commit();self.hold()
 def test_data_contract_wrong_merged_blob_holds(self):next(v for v in self.f.pr['files'] if v['path'].endswith('.json'))['sha']='c'*40;self.f.commit();self.hold()
 def test_data_contract_changed_holds(self):self.f.write(self.module('PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json')['path'],b'changed json');self.hold()
 def test_metadata_unlisted_receipt_field_holds(self):self.f.r['permit_extra']=True;self.f.commit();self.hold()
 def test_wrong_current_audit_holds(self):self.f.write('reports/verification-coverage/GAME_PLAN.md',self.f.section+b'changed');self.hold()
 def test_wrong_protected_hash_holds(self):self.f.protected['checks'][0]['actual_sha256']='c'*64;self.f.commit();self.hold()
 def test_missing_protected_holds(self):self.f.protected['checks'].pop();self.f.commit();self.hold()
 def test_attempt_diagnostic_never_acceptance_holds(self):self.f.protected['certification_attempts']=1;self.f.commit();self.hold()
 def test_original_activation_mutation_holds(self):self.f.write('evidence/original_activation.json',encoded({'foreign':True}));self.hold()
 def test_new_module_source_traversal_holds(self):self.module('methods_digest.py')['source']['path']='../evil';self.f.commit();self.hold()
 def test_new_module_symlink_holds(self):v=self.module('methods_digest.py');p=self.f.root/v['path'];p.unlink();p.symlink_to(self.f.root/self.module('scoped_release.py')['path']);self.hold()


class CorpusPreservationTests(unittest.TestCase):
 def setUp(self):self.f=PolicyFixture();self.old=(self.f.root/'evidence/prior/corpus_ledger.py').read_bytes();self.new=(self.f.root/(m.GATE_PREFIX+'corpus_ledger.py')).read_bytes()
 def tearDown(self):self.f.close()
 def hold(self,raw):
  with self.assertRaises((ValueError,SyntaxError)):m.corpus_preservation(self.old,raw)
 def test_preserved_all_original_bodies(self):v=m.corpus_preservation(self.old,self.new);self.assertEqual(v['status'],'ORIGINAL_SELECTOR_AND_LEGACY_BODIES_IDENTICAL');self.assertEqual({r['name']for r in v['functions']},{'certificate_lookup','preserve_publication_registrations'})
 def test_changed_selector_body(self):self.hold(self.new.replace(b'return ledger',b'return None'))
 def test_changed_legacy_body(self):self.hold(self.new.replace(b"{'ledger': ledger, 'previous': previous}",b'{}'))
 def test_legacy_signature_changed(self):self.hold(self.new.replace(b'_preserve_publication_registrations_legacy(ledger, previous)',b'_preserve_publication_registrations_legacy(ledger)'))
 def test_original_constant_changed(self):self.hold(self.new.replace(b"SETTING = 'UNCHANGED'",b"SETTING = 'MUTATED'"))
 def test_original_import_removed(self):self.hold(self.new.replace(b'import json\n',b''))
 def test_selector_overwritten_assignment(self):self.hold(self.new+b'\ncertificate_lookup = None\n')
 def test_foreign_top_level_import(self):self.hold(self.new+b'\nfrom foreign_registry import dispatch\n')
 def test_named_top_level_registry_import_pass(self):m.corpus_preservation(self.old,self.new+b'\nfrom methods_digest_registration import preserve_methods_digest_registrations\n')
 def test_shadowing_registry_import(self):self.hold(self.new+b'\nfrom methods_digest_registration import dispatch as json\n')
 def test_wildcard_registry_import(self):self.hold(self.new+b'\nfrom methods_digest_registration import *\n')
 def test_duplicate_callable(self):self.hold(self.new+b'\ndef certificate_lookup(ledger):\n    return ledger\n')
 def test_extra_unapproved_callable(self):self.hold(self.new+b'\ndef other(ledger):\n    return ledger\n')
 def test_legacy_body_missing(self):self.hold(self.new.replace(b'def _preserve_publication_registrations_legacy(',b'def wrong_legacy('))
 def test_wrapper_signature_changed(self):self.hold(self.new.replace(b'def preserve_publication_registrations(ledger, previous)',b'def preserve_publication_registrations(ledger)'))
 def test_decorator_changed(self):self.hold(self.new.replace(b'def certificate_lookup',b'@unknown\ndef certificate_lookup'))
 def test_wrong_baseline(self):
  with self.assertRaises(ValueError):m.corpus_preservation(self.old+b'changed',self.new)


class FullProfilePreservationTests(unittest.TestCase):
 def setUp(self):self.f=PolicyFixture()
 def tearDown(self):self.f.close()
 def hold(self,call=None):
  with self.assertRaises((ValueError,FileNotFoundError,KeyError,SyntaxError)): (call or self.f.validate)()
 def test_exact_five_deltas_and_fifteen_modules_pass(self):v=self.f.validate();self.assertEqual({x['path']for x in self.f.rows if x['before_sha256']!=x['after_sha256']},m.POLICY_TARGETS);self.assertEqual(len(self.f.r['additional_modules']),len(m.POLICY_MODULE_NAMES)+len(m.POLICY_VERSION_NAMES));self.assertEqual(set(v['corpus_preservation']),{'corpus','publication','doi_audit','public_reader'})
 def test_original_publication_eval_changed(self):self.hold(lambda:m.publication_preservation(self.f.pub_original,self.f.pub_scoped,self.f.pub_new.replace(b"'ordinary'",b"'unsafe'")))
 def test_scoped_publication_eval_changed(self):self.hold(lambda:m.publication_preservation(self.f.pub_original,self.f.pub_scoped,self.f.pub_new.replace(b"'scoped'",b"'unsafe'")))
 def test_publication_original_other_body_changed(self):self.hold(lambda:m.publication_preservation(self.f.pub_original,self.f.pub_scoped,self.f.pub_new.replace(b'return raw',b'return None')))
 def test_publication_scoped_baseline_mutated(self):self.f.write('evidence/publication_scoped_baseline.py',b'mutated');self.f.r['publication_gate_scoped_baseline']=self.f.bound('evidence/publication_scoped_baseline.py');self.f.commit();self.hold()
 def test_public_reader_baseline_mutated(self):self.f.write('evidence/public_reader_baseline.py',b'mutated');self.f.r['public_metadata_readback_baseline']=self.f.bound('evidence/public_reader_baseline.py');self.f.commit();self.hold()
 def test_missing_publication_baseline(self):self.f.r.pop('publication_gate_scoped_baseline');self.f.commit();self.hold()
 def test_missing_public_reader_baseline(self):self.f.r.pop('public_metadata_readback_baseline');self.f.commit();self.hold()
 def test_doi_audit_legacy_body_changed(self):self.hold(lambda:m.module_preservation(self.f.doi_original,self.f.doi_new.replace(b"{'root': root, 'cert_root': cert_root}",b'{}'),m.DOI_AUDIT_SHA256,{'build_audit':'_build_audit_legacy'},{'build_audit'}))
 def test_reader_legacy_body_changed(self):self.hold(lambda:m.module_preservation(self.f.reader_original,self.f.reader_new.replace(b"{'row': row}",b'{}'),m.PUBLIC_READER_SHA256,{'read_record':'_read_record_legacy','readback':'_readback_legacy'},{'read_record','readback'}))
 def test_new_reader_must_be_own_blob(self):next(v for v in self.f.pr['files']if v['path'].endswith('public_metadata_readback.py'))['sha']='c'*40;self.f.commit();self.hold()
 def test_new_registry_must_be_own_blob(self):next(v for v in self.f.pr['files']if v['path'].endswith('methods_digest_registration.py'))['sha']='c'*40;self.f.commit();self.hold()
 def test_new_digest_metadata_must_be_own_blob(self):next(v for v in self.f.pr['files']if v['path'].endswith('digest_metadata.py'))['sha']='c'*40;self.f.commit();self.hold()
 def test_original17_other_target_mutation(self):row=self.f.rows[5];self.f.write(row['path'],b'changed extra');self.hold()




class PolicyVersionClosureTests(unittest.TestCase):
 def setUp(self):self.f=PolicyFixture()
 def tearDown(self):self.f.close()
 def refresh(self):
  self.f.write('evidence/policy_catalog.json',encoded(self.f.catalog));self.f.r['policy_version_catalog']=self.f.bound('evidence/policy_catalog.json');self.f.commit()
 def hold(self,call=None):
  with self.assertRaises((ValueError,FileNotFoundError,KeyError,SyntaxError)): (call or self.f.validate)()
 def entry(self):return self.f.catalog['versions'][0]
 def row(self,name):return next(v for v in self.entry()['files']if v['name']==name)
 def archive_pr(self,mutate):
  pr=json.loads((self.f.root/'evidence/archive_pr.json').read_bytes());mutate(pr);self.f.write('evidence/archive_pr.json',encoded(pr));self.entry()['pull_request_readback']=self.f.bound('evidence/archive_pr.json');self.refresh()
 def test_current_version_exact_eight_files_pass(self):
  v=self.f.validate();self.assertEqual(v['policy_version_catalog']['versions'],[self.f.version]);self.assertEqual(len(self.entry()['files']),8)
 def test_missing_catalog_holds(self):self.f.r.pop('policy_version_catalog');self.f.commit();self.hold()
 def test_catalog_mutation_holds(self):self.f.write('evidence/policy_catalog.json',b'changed');self.hold()
 def test_unlisted_catalog_field_holds(self):self.f.catalog['approved']=True;self.refresh();self.hold()
 def test_foreign_catalog_tree_holds(self):self.f.catalog['tree_root']='/foreign';self.refresh();self.hold()
 def test_unmerged_catalog_status_holds(self):self.f.catalog['status']='PROPOSED';self.refresh();self.hold()
 def test_empty_catalog_holds(self):self.f.catalog['versions']=[];self.refresh();self.hold()
 def test_duplicate_version_holds(self):self.f.catalog['versions'].append(copy.deepcopy(self.entry()));self.refresh();self.hold()
 def test_unknown_current_version_holds(self):self.entry()['execution_consumer_sha256']='e'*64;self.refresh();self.hold()
 def test_foreign_version_field_holds(self):self.entry()['approved']=True;self.refresh();self.hold()
 def test_missing_archive_member_holds(self):self.entry()['files'].pop();self.refresh();self.hold()
 def test_duplicate_archive_member_holds(self):self.entry()['files'][-1]=copy.deepcopy(self.entry()['files'][0]);self.refresh();self.hold()
 def test_foreign_archive_member_holds(self):self.entry()['files'][0]['name']='unknown.py';self.refresh();self.hold()
 def test_archive_member_field_holds(self):self.entry()['files'][0]['approved']=True;self.refresh();self.hold()
 def test_archive_binding_traversal_holds(self):self.entry()['files'][0]['binding']['path']='../escape';self.refresh();self.hold()
 def test_archive_copied_other_directory_holds(self):
  row=self.entry()['files'][0];self.f.write('evidence/wrong/'+row['name'],(self.f.root/row['binding']['path']).read_bytes());row['binding']=self.f.bound('evidence/wrong/'+row['name']);self.refresh();self.hold()
 def test_archive_wrong_git_path_holds(self):self.entry()['files'][0]['git_path']='00_lab_infrastructure/gates/foreign.py';self.refresh();self.hold()
 def test_archive_source_mutation_holds(self):self.f.write(self.entry()['files'][0]['binding']['path'],b'changed');self.hold()
 def test_archive_implementation_rehashed_changed_holds(self):
  row=self.row('phase7_audit_policy.py');self.f.write(row['binding']['path'],b'changed');row['binding']=self.f.bound(row['binding']['path']);self.refresh();self.hold()
 def test_archive_source_symlink_holds(self):
  row=self.entry()['files'][0];p=self.f.root/row['binding']['path'];p.unlink();p.symlink_to(self.f.root/(m.GATE_PREFIX+row['name']));self.hold()
 def test_archive_source_missing_holds(self):(self.f.root/self.entry()['files'][0]['binding']['path']).unlink();self.hold()
 def test_archive_pr_unmerged_holds(self):self.archive_pr(lambda x:x.update(state='OPEN'));self.hold()
 def test_archive_pr_foreign_holds(self):self.archive_pr(lambda x:x.update(url='https://github.com/foreign/repo/pull/58'));self.hold()
 def test_archive_pr_failed_checks_holds(self):self.archive_pr(lambda x:x['statusCheckRollup'][0].update(conclusion='FAILURE'));self.hold()
 def test_archive_pr_missing_checks_holds(self):self.archive_pr(lambda x:x['statusCheckRollup'].pop());self.hold()
 def test_archive_pr_duplicate_file_holds(self):self.archive_pr(lambda x:x['files'].append(copy.deepcopy(x['files'][0])));self.hold()
 def test_archive_pr_wrong_blob_holds(self):self.archive_pr(lambda x:next(v for v in x['files']if '/policy_versions/'in v['path']).update(sha='c'*40));self.hold()
 def test_archive_additional_module_missing_holds(self):self.f.r['additional_modules'].pop();self.f.commit();self.hold()
 def test_archive_additional_extra_holds(self):self.f.r['additional_modules'].append(copy.deepcopy(self.f.r['additional_modules'][-1]));self.f.commit();self.hold()
 def test_archive_additional_catalog_mismatch_holds(self):
  v=self.f.r['additional_modules'][-1];raw=b'changed';self.f.write(v['path'],raw);self.f.write(v['source']['path'],raw);v['sha256']=m.sha(self.f.root/v['path']);v['source']=self.f.bound(v['source']['path']);self.f.commit();self.hold()
 def test_archive_changed_capture_holds(self):self.f.write(self.f.r['additional_modules'][-1]['source']['path'],b'changed');self.hold()
 def test_added_uncatalogued_hash_directory_holds(self):
  v=copy.deepcopy(self.f.r['additional_modules'][-1]);v['path']=m.GATE_PREFIX+'policy_versions/'+('e'*64)+'/publication_gate.py';self.f.r['additional_modules'].append(v);self.f.commit();self.hold()
 def test_contract_pin_wrong_holds(self):
  row=self.row('PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json');self.f.write(row['binding']['path'],b'changed contract');row['binding']=self.f.bound(row['binding']['path']);self.archive_pr(lambda x:next(v for v in x['files']if v['path']==row['git_path']).update(sha=gitblob(b'changed contract')));self.hold()
 def test_catalog_closure_return_binds_exact_members(self):
  v=m.policy_catalog_closure(self.f.root,self.f.r['policy_version_catalog'],self.f.version);self.assertEqual(set(v['pinned']),{row['binding']['path']for row in self.entry()['files']});self.assertEqual(set(v['origins']),set(v['pinned']))
 def test_second_old_version_requires_own_archive_and_merge(self):
  contract=b'{"synthetic":"old immutable"}';policy=("CONTRACT_SHA='"+hashlib.sha256(contract).hexdigest()+"'\n").encode();version=hashlib.sha256(policy).hexdigest();rows=[]
  pr=copy.deepcopy(self.f.pr);pr.update(number=59,url='https://github.com/jdhart81/viridis-canon/pull/59',mergeCommit={'oid':'c'*40});pr['files']=[]
  for name in sorted(m.POLICY_VERSION_NAMES):
   raw=policy if name=='phase7_audit_policy.py'else(contract if name=='PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json'else('old reviewed '+name).encode());rel=m.GATE_PREFIX+'policy_versions/'+version+'/'+name;source='evidence/old_version/'+name;self.f.write(rel,raw);self.f.write(source,raw);git_path='00_lab_infrastructure/gates/policy_versions/'+version+'/'+name;pr['files'].append({'path':git_path,'sha':gitblob(raw)});rows.append({'name':name,'binding':self.f.bound(rel),'git_path':git_path});self.f.r['additional_modules'].append({'path':rel,'sha256':m.sha(self.f.root/rel),'source':self.f.bound(source)})
  self.f.write('evidence/old_version_pr.json',encoded(pr));self.f.catalog['versions'].append({'execution_consumer_sha256':version,'files':rows,'pull_request_readback':self.f.bound('evidence/old_version_pr.json')});self.refresh();v=self.f.validate();self.assertEqual(len(v['policy_version_catalog']['versions']),2)



class MalformedVersionClosureTests(unittest.TestCase):
 setUp=PolicyVersionClosureTests.setUp
 tearDown=PolicyVersionClosureTests.tearDown
 entry=PolicyVersionClosureTests.entry
 row=PolicyVersionClosureTests.row
 refresh=PolicyVersionClosureTests.refresh
 hold=PolicyVersionClosureTests.hold
 def test_unhashable_version_identity_holds(self):self.entry()['execution_consumer_sha256']=[];self.refresh();self.hold()
 def test_missing_version_binding_holds(self):self.entry()['files'][0]['binding']=None;self.refresh();self.hold()
 def test_version_binding_extra_field_holds(self):self.entry()['files'][0]['binding']['bytes']=123;self.refresh();self.hold()
 def test_catalog_source_mutates_before_return_holds(self):
  real=m.sha;target=self.f.root/self.row('methods_digest.py')['binding']['path'];seen={'changed':False}
  def changing(path):
   if Path(path)==target and not seen['changed']:
    # First call is _bound; mutate after returning that hash so read() rejects.
    old=real(path);target.write_bytes(b'mutated during validation');seen['changed']=True;return old
   return real(path)
  with patch.object(m,'sha',side_effect=changing):self.hold()

if __name__=='__main__':unittest.main()
