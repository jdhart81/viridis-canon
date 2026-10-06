"""Offline proposal tests. TEST_ONLY fixtures never establish activation."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import nightly_coverage as nc

def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');return p
def bind(root,p):return {'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

class HistoricalProvenanceCases(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();self.base=self.root/'reports/verification-coverage/TEST_ONLY'
  self.counterpart=self.root/'RESEARCH_PIPELINE_v2/lean_certificates/Run-119/SEALED_paper.tex';self.counterpart.parent.mkdir(parents=True);self.counterpart.write_bytes(b'TEST_ONLY exact frozen paper bytes\n')
  self.literal=str(self.root.parent/'TEST_ONLY_EXTERNAL_DO_NOT_READ/Run-119/SEALED_paper.tex');self.original={'path':self.literal,'sha256':hashlib.sha256(self.counterpart.read_bytes()).hexdigest()}
  old={'tree_root':str(self.root),'certificates':[{'sealed_paper_inputs':{'SEALED_paper.tex':self.original}}],'run_entities':[{'certificate_artifacts':{'SEALED_paper.tex':self.original}}]}
  self.archive=write(self.base/'immutable-predecessor.json',old);self.current=write(self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json',{'TEST_ONLY':'different live current authority'})
  self.plan=write(self.base/'original-plan.json',{'tree_root':str(self.root),'precondition_current_ledger':{'path':str(self.current),'sha256':bind(self.root,self.archive)['sha256']},'publication_entities':[{'id':'TEST_ONLY-'+str(i)}for i in range(27)]})
  snapshot=copy.deepcopy(old);snapshot['premise_declaration_cutover_run']='Run-188';self.snapshot=write(self.base/'fresh-ledger-snapshot.json',snapshot)
  policies=[{'kind':'SEALED_INPUT_LOCATION','literal_path':self.literal,'expected_sha256':self.original['sha256'],'canonical_path':str(self.counterpart.relative_to(self.root))},{'kind':'HISTORICAL_PRECONDITION','literal_path':str(self.current),'expected_sha256':bind(self.root,self.archive)['sha256'],'canonical_path':str(self.archive.relative_to(self.root))}]
  docs={'registration_plan':bind(self.root,self.plan),'registration_ledger':bind(self.root,self.snapshot),'historical_precondition_ledger':bind(self.root,self.archive)};mappings=[]
  for role in ('registration_ledger','historical_precondition_ledger'):
   for pointer in ('/certificates/0/sealed_paper_inputs/SEALED_paper.tex','/run_entities/0/certificate_artifacts/SEALED_paper.tex'):
    mappings.append({'kind':'SEALED_INPUT_LOCATION','document_role':role,'source_document':docs[role],'json_pointer':pointer,'literal_path':self.literal,'expected_sha256':self.original['sha256'],'canonical_binding':bind(self.root,self.counterpart)})
  mappings.append({'kind':'HISTORICAL_PRECONDITION','document_role':'registration_plan','source_document':docs['registration_plan'],'json_pointer':'/precondition_current_ledger','literal_path':str(self.current),'expected_sha256':bind(self.root,self.archive)['sha256'],'canonical_binding':bind(self.root,self.archive)})
  self.capsule={'standard':'VRS-ACTIVATION-HISTORICAL-PROVENANCE-1','status':'EXACT_SOURCE_BOUND_CANONICAL_RELOCATION','tree_root':str(self.root),'policy':policies,'documents':docs,'mappings':mappings}
  self.receipt={'premise_declaration_cutover_run':'Run-188','sources':{'registration_ledger':docs['registration_ledger']},'proofs':{'registration_plan':docs['registration_plan']}}
  self.cpath=self.base/'HISTORICAL_PROVENANCE.json';self.save()
  for name,value in [('HISTORICAL_PROVENANCE_POLICY_SHA256',nc._policy_sha(policies)),('APPROVED_REGISTRATION_PLAN_SHA256',bind(self.root,self.plan)['sha256'])]:
   patcher=patch.object(nc,name,value);patcher.start();self.addCleanup(patcher.stop)
 def save(self):write(self.cpath,self.capsule);self.receipt['proofs']['historical_provenance']=bind(self.root,self.cpath)
 def resolver(self):self.save();return nc._HistoricalProvenance(self.root,self.receipt)
 def close(self):
  resolver=self.resolver();nc._nested_sources(self.root,self.receipt,provenance=resolver);resolver.require_complete();return resolver
 def test_exact_own_source_and_archive_with_all_children_pass(self):
  before=self.current.read_bytes();r=self.close();self.assertEqual(len(r.used),5);self.assertEqual(self.current.read_bytes(),before)
 def test_no_external_file_is_opened_or_statted(self):
  original_read=Path.read_bytes;original_exists=Path.exists;original_symlink=Path.is_symlink
  def guard(fn,p,*args,**kwargs):
   if not p.is_relative_to(self.root):raise AssertionError('No external-path IO permitted')
   return fn(p,*args,**kwargs)
  with patch.object(Path,'read_bytes',lambda p:guard(original_read,p)),patch.object(Path,'exists',lambda p:guard(original_exists,p)),patch.object(Path,'is_symlink',lambda p:guard(original_symlink,p)):self.close()
 def test_without_capsule_original_guard_holds(self):
  no=copy.deepcopy(self.receipt);no['proofs'].pop('historical_provenance')
  with self.assertRaises(ValueError):nc._nested_sources(self.root,no)
 def test_missing_map_unlisted_external_pointer_holds(self):
  self.capsule['mappings'].pop(0)
  with self.assertRaises(ValueError):self.close()
 def test_unknown_literal_sha_or_counterpart_policy_holds(self):
  for key,value in [('literal_path',self.literal+'-foreign'),('expected_sha256','0'*64),('canonical_binding',{'path':str(self.counterpart.relative_to(self.root)),'sha256':'0'*64})]:
   old=copy.deepcopy(self.capsule);self.capsule['mappings'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.close()
   self.capsule=old
 def test_changed_source_binding_document_or_pointer_holds(self):
  for key,value in [('source_document',{'path':self.capsule['documents']['registration_ledger']['path'],'sha256':'0'*64}),('document_role','registration_plan'),('json_pointer','/run_entities/01/certificate_artifacts/SEALED_paper.tex')]:
   old=copy.deepcopy(self.capsule);self.capsule['mappings'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.close()
   self.capsule=old
 def test_mapping_cannot_touch_current_claim_certificate_or_public_receipt(self):
  for pointer in ('/publication_entities/0/certificate','/public_publication_readback','/sources/installation','/proofs/protected_baseline'):
   old=self.capsule['mappings'][0]['json_pointer'];self.capsule['mappings'][0]['json_pointer']=pointer
   with self.subTest(pointer=pointer),self.assertRaises(ValueError):self.close()
   self.capsule['mappings'][0]['json_pointer']=old
 def test_top_current_binding_never_resolved_by_historical_mapping(self):
  resolver=self.resolver();self.assertIsNone(resolver.mapped(None,'/precondition_current_ledger',self.original))
  with self.assertRaises(ValueError):nc._nested_sources(self.root,self.original,provenance=resolver)
 def test_altered_counterpart_bytes_and_missing_file_hold(self):
  original=self.counterpart.read_bytes();self.counterpart.write_bytes(original+b'changed')
  with self.assertRaises(ValueError):self.close()
  self.counterpart.unlink()
  with self.assertRaises(FileNotFoundError):self.close()
 def test_symlink_counterpart_or_source_or_capsule_hold(self):
  for choice in ('counterpart','snapshot','cpath'):
   p=getattr(self,choice);raw=p.read_bytes();target=p.with_name(p.name+'.saved');target.write_bytes(raw);p.unlink();p.symlink_to(target)
   with self.subTest(choice=choice),self.assertRaises(ValueError):nc._HistoricalProvenance(self.root,self.receipt)
   p.unlink();p.write_bytes(raw);target.unlink()
 def test_external_or_traversal_canonical_target_never_allowed(self):
  for target in ('../escape','/tmp/outside'):
   old=copy.deepcopy(self.capsule);self.capsule['mappings'][0]['canonical_binding']['path']=target
   with self.subTest(target=target),self.assertRaises(ValueError):self.close()
   self.capsule=old
 def test_changed_policy_extra_keys_duplicate_rows_hold(self):
  for change in ('hash','capsule_key','row_key','duplicate'):
   old=copy.deepcopy(self.capsule)
   if change=='hash':self.capsule['policy'][0]['expected_sha256']='0'*64
   elif change=='capsule_key':self.capsule['skip_recursive_checks']=True
   elif change=='row_key':self.capsule['mappings'][0]['ignore_hash']=True
   else:self.capsule['mappings'].append(copy.deepcopy(self.capsule['mappings'][0]))
   with self.subTest(change=change),self.assertRaises(ValueError):self.close()
   self.capsule=old
 def test_source_bytes_changed_after_capsule_or_at_mapped_pointer_hold(self):
  raw=self.snapshot.read_bytes();self.snapshot.write_bytes(raw+b' ')
  with self.assertRaises(ValueError):nc._HistoricalProvenance(self.root,self.receipt)
  self.snapshot.write_bytes(raw);r=self.close();doc=self.capsule['documents']['registration_ledger']
  with self.assertRaises(ValueError):r.mapped(doc,'/run_entities/0/certificate_artifacts/SEALED_paper.tex',{'path':self.literal,'sha256':'0'*64})
 def test_predecessor_mapping_cannot_use_fresh_live_ledger_or_another_archive(self):
  self.capsule['documents']['historical_precondition_ledger']=bind(self.root,self.current)
  with self.assertRaises(ValueError):self.close()
 def test_source_role_root_cutover_wrong_document_hold(self):
  for key,value in [('tree_root','/wrong/root'),('premise_declaration_cutover_run','Run-189')]:
   old=json.loads(self.snapshot.read_text());changed=copy.deepcopy(old);changed[key]=value;write(self.snapshot,changed);new=bind(self.root,self.snapshot);self.capsule['documents']['registration_ledger']=new;self.receipt['sources']['registration_ledger']=new
   for row in self.capsule['mappings']:
    if row['document_role']=='registration_ledger':row['source_document']=new
   with self.subTest(key=key),self.assertRaises(ValueError):self.close()
   write(self.snapshot,old);new=bind(self.root,self.snapshot);self.capsule['documents']['registration_ledger']=new;self.receipt['sources']['registration_ledger']=new
   for row in self.capsule['mappings']:
    if row['document_role']=='registration_ledger':row['source_document']=new
 def test_unused_mapping_cannot_be_silently_accepted(self):
  r=self.resolver()
  with self.assertRaises(ValueError):r.require_complete()
 def test_relocated_json_children_are_not_skipped(self):
  value=json.loads(self.archive.read_text());value['unclassified']={'path':self.literal+'-unknown','sha256':'0'*64};write(self.archive,value)
  rebound=bind(self.root,self.archive);self.capsule['documents']['historical_precondition_ledger']=rebound
  self.capsule['policy'][1]['expected_sha256']=rebound['sha256']
  for row in self.capsule['mappings']:
   if row['document_role']=='historical_precondition_ledger':row['source_document']=rebound
   if row['kind']=='HISTORICAL_PRECONDITION':row['expected_sha256']=rebound['sha256'];row['canonical_binding']=rebound
  plan=json.loads(self.plan.read_text());plan['precondition_current_ledger']['sha256']=rebound['sha256'];write(self.plan,plan);pb=bind(self.root,self.plan)
  self.capsule['documents']['registration_plan']=pb;self.receipt['proofs']['registration_plan']=pb
  self.capsule['mappings'][-1]['source_document']=pb
  with patch.object(nc,'HISTORICAL_PROVENANCE_POLICY_SHA256',nc._policy_sha(self.capsule['policy'])),patch.object(nc,'APPROVED_REGISTRATION_PLAN_SHA256',pb['sha256']):
   with self.assertRaisesRegex(ValueError,'outside canonical'):self.close()
 def test_duplicate_capsule_json_key_is_not_reinterpreted(self):
  self.save();raw=self.cpath.read_bytes();self.cpath.write_bytes(raw.replace(b'"standard":',b'"status":"wrong","standard":',1));self.receipt['proofs']['historical_provenance']=bind(self.root,self.cpath)
  with self.assertRaises(ValueError):nc._HistoricalProvenance(self.root,self.receipt)
 def test_no_capsule_map_can_waive_current_authority_source_hash(self):
  r=self.resolver();proof=copy.deepcopy(self.receipt);proof['sources']['registration_ledger']['sha256']='0'*64
  with self.assertRaises(ValueError):nc._nested_sources(self.root,proof,provenance=r)


class GateSuccessorCases(unittest.TestCase):
 def setUp(self):
  from test_activation_guard import ActivationFixture
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.f=ActivationFixture(self,self.root)
  self.guard='RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py';self.old_manifest=json.loads(self.f.paths['after_manifest'].read_text());self.f.put('original_after_manifest',self.old_manifest)
  oldhash=next(r['after_sha256']for r in self.old_manifest['snapshots']if r['relative_path']==self.guard)
  for name,value in [('ORIGINAL_ACTIVATION_GUARD_SHA256',oldhash),('APPROVED_ORIGINAL_AFTER_MANIFEST_SHA256',self.f.bound('original_after_manifest')['sha256']),('APPROVED_ORIGINAL_TRACKED_SNAPSHOT_FILES',( ('BEFORE_MANIFEST.json',self.f.bound('original_after_manifest')['sha256']),('AFTER_MANIFEST.json',self.f.bound('original_after_manifest')['sha256']) ))]:
   p=patch.object(nc,name,value);p.start();self.addCleanup(p.stop)
  (self.root/self.guard).write_bytes(b'TEST_ONLY exact gate successor')
  newhash=hashlib.sha256((self.root/self.guard).read_bytes()).hexdigest()
  self.f.change('after_manifest',lambda m:next(r for r in m['snapshots']if r['relative_path']==self.guard).update(after_sha256=newhash))
  self.f.change('installation',lambda m:(m.update(release_commit='f'*40,manifest_sha256=self.f.bound('after_manifest')['sha256']),next(r for r in m['installed']if r['path']==self.guard).update(after_sha256=newhash)))
  plan=json.loads(self.f.paths['registration_plan'].read_text());ledger=json.loads(self.f.paths['registration_ledger'].read_text())
  paper=self.f.base/'frozen-paper.tex';paper.write_bytes(b'TEST_ONLY unchanged sealed paper')
  literal=str(self.root.parent/'TEST_ONLY_DO_NOT_READ/frozen-paper.tex');original={'path':literal,'sha256':hashlib.sha256(paper.read_bytes()).hexdigest()}
  archive=write(self.f.base/'archive.json',{'tree_root':str(self.root),'certificates':[{'sealed_paper_inputs':{'SEALED_paper.tex':original}}]})
  plan['precondition_current_ledger']={'path':str(self.f.canonical),'sha256':bind(self.root,archive)['sha256']};self.f.put('registration_plan',plan);self.f.receipt['proofs']['registration_plan']=self.f.bound('registration_plan')
  p=patch.object(nc,'APPROVED_REGISTRATION_PLAN_SHA256',self.f.bound('registration_plan')['sha256']);p.start();self.addCleanup(p.stop)
  ledger['certificates']=[{'sealed_paper_inputs':{'SEALED_paper.tex':original}}];self.f.put('registration_ledger',ledger);self.f.receipt['sources']['registration_ledger']=self.f.bound('registration_ledger')
  policy=[{'kind':'SEALED_INPUT_LOCATION','literal_path':literal,'expected_sha256':original['sha256'],'canonical_path':str(paper.relative_to(self.root))},{'kind':'HISTORICAL_PRECONDITION','literal_path':str(self.f.canonical),'expected_sha256':bind(self.root,archive)['sha256'],'canonical_path':str(archive.relative_to(self.root))}]
  p=patch.object(nc,'HISTORICAL_PROVENANCE_POLICY_SHA256',nc._policy_sha(policy));p.start();self.addCleanup(p.stop)
  docs={'registration_plan':self.f.bound('registration_plan'),'registration_ledger':self.f.bound('registration_ledger'),'historical_precondition_ledger':bind(self.root,archive)}
  maps=[{'kind':'SEALED_INPUT_LOCATION','document_role':role,'source_document':docs[role],'json_pointer':'/certificates/0/sealed_paper_inputs/SEALED_paper.tex','literal_path':literal,'expected_sha256':original['sha256'],'canonical_binding':bind(self.root,paper)}for role in('registration_ledger','historical_precondition_ledger')]
  maps.append({'kind':'HISTORICAL_PRECONDITION','document_role':'registration_plan','source_document':docs['registration_plan'],'json_pointer':'/precondition_current_ledger','literal_path':str(self.f.canonical),'expected_sha256':bind(self.root,archive)['sha256'],'canonical_binding':bind(self.root,archive)})
  self.pr={'number':51,'state':'MERGED','mergeCommit':{'oid':'f'*40},'headRefOid':'c'*40,'baseRefName':'main','url':'https://github.com/jdhart81/viridis-canon/pull/51'}
  self.checks=[{'name':'TEST_ONLY required','bucket':'pass','state':'SUCCESS','link':'https://github.com/jdhart81/viridis-canon/actions/runs/123/job/456'}]
  self.extra_runs=[]
  self.run={'id':123,'head_sha':'c'*40,'status':'completed','conclusion':'success'}
  self.git={'standard':'VRS-PHASE5-GATE-SUCCESSOR-GIT-READBACK-1','repository':'jdhart81/viridis-canon','original_release_commit':'d'*40,'release_commit':'f'*40,'head_commit':'c'*40,'ancestry':{'argv':['git','merge-base','--is-ancestor','d'*40,'f'*40],'exit_code':0,'stdout':'','stderr':''},'changed_files':[]}
  prefix='00_lab_infrastructure/gates/production_snapshots/phase5-20261005-provenance-closure/'
  sources={ '00_lab_infrastructure/gates/nightly_coverage.py':(self.root/self.guard,'M',oldhash),'00_lab_infrastructure/gates/test_activation_historical_provenance.py':(write(self.f.base/'test_source.json',{'TEST_ONLY':'new tests'}),'A',None),prefix+'BEFORE_MANIFEST.json':(self.f.paths['original_after_manifest'],'A',None),prefix+'AFTER_MANIFEST.json':(self.f.paths['after_manifest'],'A',None),prefix+'AFTER_MANIFEST_PRE_PROVENANCE_20261005.json':(self.f.paths['original_after_manifest'],'A',None),prefix+'CURRENT_BEFORE_OBSERVATION.json':(write(self.f.base/'observation.json',{'TEST_ONLY':'actual before operation'}),'A',None),prefix+'provenance_before/'+self.guard:(write(self.f.base/'guard_old_source.json',{'TEST_ONLY':'old guard'}),'A',None),prefix+'provenance_after/'+self.guard:(self.root/self.guard,'A',None)}
  # Bind the old snapshot to fixture bytes, no claimed real SHA or operation.
  old_path=self.f.base/'guard_old';old_path.write_text('TEST_ONLY installed '+self.guard);sources[prefix+'provenance_before/'+self.guard]=(old_path,'A',None)
  for path,(src,status,before)in sources.items():self.git['changed_files'].append({'path':path,'status':status,'before_sha256':before,'after_sha256':bind(self.root,src)['sha256'],'after_source':bind(self.root,src)})
  self.pr['files']=[{'path':p}for p in sources]
  self.f.put('successor_pr',self.pr);self.f.put('successor_checks',self.checks);self.f.put('successor_run',self.run);self.f.put('successor_git',self.git)
  self.successor={'standard':'VRS-PHASE5-GATE-SUCCESSOR-MERGE-1','status':'MERGED_REQUIRED_CHECKS_PASS','tree_root':str(self.root),'repository':'jdhart81/viridis-canon','original_merge_review':self.f.bound('merge_review'),'original_after_manifest':self.f.bound('original_after_manifest'),'after_manifest':self.f.bound('after_manifest'),'release_commit':'f'*40,'observed_at_utc':self.f.time(-8.5),'pull_request_readback':self.f.bound('successor_pr'),'checks_readback':self.f.bound('successor_checks'),'action_run_readbacks':[self.f.bound('successor_run')],'git_readback':self.f.bound('successor_git')}
  self.f.put('successor',self.successor)
  self.capsule={'standard':'VRS-ACTIVATION-HISTORICAL-PROVENANCE-1','status':'EXACT_SOURCE_BOUND_CANONICAL_RELOCATION','tree_root':str(self.root),'policy':policy,'documents':docs,'mappings':maps,'gate_successor':self.f.bound('successor')}
  self.save()
 def save(self):
  for name,value in [('successor_pr',self.pr),('successor_checks',self.checks),('successor_run',self.run),('successor_git',self.git)]:self.f.put(name,value)
  for key,name in [('pull_request_readback','successor_pr'),('checks_readback','successor_checks'),('git_readback','successor_git')]:self.successor[key]=self.f.bound(name)
  self.successor['action_run_readbacks']=[self.f.bound('successor_run')]
  for i,run in enumerate(self.extra_runs):self.f.put('successor_extra_run_'+str(i),run);self.successor['action_run_readbacks'].append(self.f.bound('successor_extra_run_'+str(i)))
  self.f.put('successor',self.successor)
  self.capsule['gate_successor']=self.f.bound('successor');self.f.put('historical_provenance',self.capsule);self.f.receipt['proofs']['historical_provenance']=self.f.bound('historical_provenance');self.f.save_activation()
 def validate(self):self.save();return nc.validate_activation_receipt(self.root,self.f.receipt,now=self.f.now)
 def test_full_successor_keeps_original50_and27_registration_authorities(self):
  result=self.validate();self.assertEqual(result['premise_declaration_cutover_run'],'Run-188');self.assertEqual(len(result['registration_plan']['publication_entities']),27)
 def test_missing_successor_original50_cannot_cover_newinstalledrelease(self):
  self.capsule.pop('gate_successor');self.f.put('historical_provenance',self.capsule);self.f.receipt['proofs']['historical_provenance']=self.f.bound('historical_provenance')
  with self.assertRaises(ValueError):nc.validate_activation_receipt(self.root,self.f.receipt,now=self.f.now)
 def test_wrong_pending_failed_head_release_pr_or_ci_hold(self):
  cases=[('pr','number',50),('pr','headRefOid','1'*40),('pr','baseRefName','other'),('run','head_sha','a'*40),('run','status','in_progress'),('run','conclusion','failure'),('successor','release_commit','e'*40)]
  for name,key,value in cases:
   obj=getattr(self,name);old=obj[key];obj[key]=value
   with self.subTest(name=name,key=key),self.assertRaises(ValueError):self.validate()
   obj[key]=old
  old=self.checks;self.checks=[]
  with self.assertRaises(ValueError):self.validate()
  self.checks=old;old=self.checks[0]['bucket'];self.checks[0]['bucket']='fail'
  with self.assertRaises(ValueError):self.validate()
  self.checks[0]['bucket']=old
 def test_original50_is_still_mandatory_actual_merge_evidence(self):
  self.f.change('pr',lambda o:o.update(number=49));self.f.change('merge_review',lambda o:o.update(pull_request_readback=self.f.bound('pr')));self.successor['original_merge_review']=self.f.bound('merge_review')
  with self.assertRaises(ValueError):self.validate()
 def test_github_diff_omission_foreign_file_deletedfile_and_blob_change_hold(self):
  for change in ('omit','foreign','deleted','blob','guard_before','copied'):
   old=copy.deepcopy(self.git);oldpr=copy.deepcopy(self.pr)
   row=self.git['changed_files'][0]
   if change=='omit':self.pr['files'].pop()
   elif change=='foreign':row['path']='comparator-deploy/comparator_cloud_lean_verifier.py';self.pr['files'][0]['path']=row['path']
   elif change=='deleted':row['status']='D'
   elif change=='blob':row['after_sha256']='a'*64
   elif change=='guard_before':row['before_sha256']='a'*64
   else:self.git['changed_files'][2]['after_sha256']='a'*64
   with self.subTest(change=change),self.assertRaises(ValueError):self.validate()
   self.git=old;self.pr=oldpr
 def test_wrong_ancestry_manifest_and_merge_chronology_hold(self):
  for change in ('ancestor','oldmanifest','newmanifest','chronology'):
   old=copy.deepcopy(self.successor);oldgit=copy.deepcopy(self.git)
   if change=='ancestor':self.git['ancestry']['exit_code']=1
   elif change=='oldmanifest':self.successor['original_after_manifest']['sha256']='a'*64
   elif change=='newmanifest':self.successor['after_manifest']['sha256']='a'*64
   else:self.successor['observed_at_utc']=self.f.time(-20)
   with self.subTest(change=change),self.assertRaises(ValueError):self.validate()
   self.successor=old;self.git=oldgit
 def test_capsule_cannot_waive_scheduler_protected_current_source_or_registration(self):
  for choice in ('scheduler','protected','registration','source'):
   names={'scheduler':'scheduler_readback','protected':'protected_readback','registration':'registration_ledger','source':'source_observation'};name=names[choice];old=json.loads(self.f.paths[name].read_text())
   if choice=='scheduler':
    raw=json.loads(self.f.paths['scheduler_raw'].read_text());raw['cwds']=['/wrong/generation'];self.f.put('scheduler_raw',raw);self.f.change(name,lambda o:o.update(automation=raw,raw_configuration=self.f.bound('scheduler_raw')))
   elif choice=='protected':self.f.change(name,lambda o:o['checks'][0].update(actual_sha256='0'*64))
   elif choice=='registration':self.f.change(name,lambda o:o['publication_entities'][0].update(certificate_sha256='0'*64))
   else:self.f.change(name,lambda o:o.update(next_run='Run-189'))
   with self.subTest(choice=choice),self.assertRaises(ValueError):self.validate()
   self.f.put(name,old);self.f.receipt['sources'][name]=self.f.bound(name)

 def test_duplicate_required_check_names_require_both_distinct_currenthead_runs(self):
  original=json.loads(self.f.paths['checks'].read_text());original.append(copy.deepcopy(original[0]));self.f.put('checks',original)
  self.f.change('merge_review',lambda o:o.update(checks_readback=self.f.bound('checks')));self.successor['original_merge_review']=self.f.bound('merge_review')
  with self.assertRaises(ValueError):self.validate()
  second=copy.deepcopy(self.checks[0]);second['link']='https://github.com/jdhart81/viridis-canon/actions/runs/123/job/457';self.checks.append(second)
  with self.assertRaises(ValueError):self.validate()
  self.checks[-1]['link']='https://github.com/jdhart81/viridis-canon/actions/runs/124/job/457';run=copy.deepcopy(self.run);run['id']=124;self.extra_runs=[run]
  self.validate()
  self.extra_runs[0]['head_sha']='1'*40
  with self.assertRaises(ValueError):self.validate()

 def test_unexpected_generated_bytecode_in_successor_gitdiff_holds(self):
  row=copy.deepcopy(self.git['changed_files'][1]);row['path']='00_lab_infrastructure/gates/production_snapshots/phase5-20261005-provenance-closure/after/__pycache__/unexpected.pyc';self.git['changed_files'].append(row);self.pr['files'].append({'path':row['path']})
  with self.assertRaisesRegex(ValueError,'closed gate/test/snapshot scope'):self.validate()

class FrozenHistoricalOwnerCases(unittest.TestCase):
 save = HistoricalProvenanceCases.save
 resolver = HistoricalProvenanceCases.resolver
 close = HistoricalProvenanceCases.close
 def setUp(self):
  HistoricalProvenanceCases.setUp(self)
  self.owner=write(self.base/'frozen-comparator-receipt.json',{'candidate':self.original,'status':'TEST_ONLY_UNCHANGED_VERIFICATION_VERDICT'})
  self.fixed_source=bind(self.root,self.owner)
  pol={'kind':'FROZEN_HISTORICAL_LOCATION','literal_path':self.literal,'expected_sha256':self.original['sha256'],'canonical_path':str(self.counterpart.relative_to(self.root)),'source_document':self.fixed_source,'json_pointer':'/candidate'}
  self.capsule['policy'].append(pol);self.capsule['mappings'].append({'kind':pol['kind'],'document_role':'frozen_historical_source','source_document':self.fixed_source,'json_pointer':'/candidate','literal_path':self.literal,'expected_sha256':self.original['sha256'],'canonical_binding':bind(self.root,self.counterpart)})
  snap=json.loads(self.snapshot.read_text());snap['historical_receipt']=self.fixed_source;write(self.snapshot,snap);new=bind(self.root,self.snapshot);self.capsule['documents']['registration_ledger']=new;self.receipt['sources']['registration_ledger']=new
  for row in self.capsule['mappings']:
   if row['document_role']=='registration_ledger':row['source_document']=new
  p=patch.object(nc,'HISTORICAL_PROVENANCE_POLICY_SHA256',nc._policy_sha(self.capsule['policy']));p.start();self.addCleanup(p.stop)
 def test_frozen_receipt_source_and_own_pointer_pass_without_verdict_change(self):
  raw=self.owner.read_bytes();r=self.close();self.assertEqual(len(r.used),6);self.assertEqual(self.owner.read_bytes(),raw)
 def test_fixed_owner_cannot_move_to_other_document_pointer_or_sha(self):
  for field,value in [('source_document',self.capsule['documents']['historical_precondition_ledger']),('json_pointer','/conclusion'),('document_role','registration_ledger')]:
   old=copy.deepcopy(self.capsule);self.capsule['mappings'][-1][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.close()
   self.capsule=old
 def test_fixed_owner_source_altered_bytes_holds(self):
  self.owner.write_bytes(self.owner.read_bytes()+b' ')
  with self.assertRaises(ValueError):self.close()
 def test_even_policy_test_rebinding_cannot_target_a_direct_current_authority(self):
  source=self.capsule['documents']['registration_ledger'];self.capsule['policy'][-1]['source_document']=source;self.capsule['policy'][-1]['json_pointer']='/certificates/0/sealed_paper_inputs/SEALED_paper.tex'
  with patch.object(nc,'HISTORICAL_PROVENANCE_POLICY_SHA256',nc._policy_sha(self.capsule['policy'])):
   with self.assertRaisesRegex(ValueError,'direct current authority'):self.close()
 def test_fixed_owner_no_mapping_still_fails_closed(self):
  self.capsule['mappings'].pop()
  with self.assertRaises(ValueError):self.close()

 def test_frozen_owner_never_reads_an_external_literal(self):
  HistoricalProvenanceCases.test_no_external_file_is_opened_or_statted(self)

if __name__=='__main__':unittest.main()
