"""Synthetic byte/transport-seam tests only; no certificates, Lean or writes."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,tempfile,unittest,zipfile,io,stat
import methods_digest as m
from zenodo_transport import TransportHold

def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(m.raw_json(v))

class Fixture:
 def __init__(self):
  self.tmp=tempfile.TemporaryDirectory(dir='/private/tmp');self.root=Path(self.tmp.name).resolve();self.out=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/2026-W41/attempt-v001'
  self.authority=self.root/'SYNTHETIC_AUDIT_AUTHORITY.json';save(self.authority,{'standard':'UNIT_NOT_ACTUAL_AUDIT','model':None,'review_timestamp':None});self.authority_binding=m.binding(self.authority);self.records={};self.specs=[]
  for rid in ('Run-125','Run-126'):
   p=self.root/'notes'/rid;p.mkdir(parents=True);cert=self.root/'certs'/rid/'cert.json';save(cert,{'run_id':rid,'status':'SYNTHETIC_NOT_CERTIFICATION'})
   files={'paper.tex':b'SYNTHETIC NOTE TEX','paper.pdf':b'%PDF-SYNTHETIC NOT RENDERED','candidate.lean':b'SYNTHETIC NEVER ELABORATED','statement.lean':b'SYNTHETIC FROZEN TYPE','claim_map.json':b'{}','foundation_basis.json':b'{}','statement_inventory.json':b'{}','certificate.json':cert.read_bytes()}
   for n,b in files.items():(p/n).write_bytes(b)
   metadata={'title':'Original '+rid,'description':'SYNTHETIC CANONICAL METADATA','creators':[{'name':'Synthetic fixture'}],'license':{'id':'cc-by-4.0'},'access_right':'open','language':'eng'};save(p/'metadata.json',metadata)
   save(p/'SCOPED_RELEASE_MANIFEST.json',{'run_id':rid,'status':'SYNTHETIC'});save(p/'PUBLICATION_BINDING.json',{'run_id':rid,'status':'SYNTHETIC'});save(p/'RULE_EXECUTION.json',{'run_id':rid,'status':'SYNTHETIC_RULE_EXECUTION_NOT_REVIEW'})
   scope=[{'lean_theorem':'conditional_target','nonvacuity_obligation':'fixture_witness'}]
   self.records[rid]={'status':'PUBLICATION_BOUND','exact_publication_binding':True,'run_id':rid,'certificate':m.binding(cert),'candidate':m.binding(p/'candidate.lean'),'formal_statement':m.binding(p/'statement.lean'),'foundation_basis':'INDEPENDENT','statement_scope':scope,'claim_reviews':[{'lean_theorem':'conditional_target','semantic_tier':'SUBSTANTIVE','nonvacuity':{'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':'fixture_witness','certificate':m.binding(cert)}}],'uploads':[{'filename':n,'sha256':m.sha(p/n)}for n in(*files,'metadata.json')],'policy_receipt':m.binding(p/'RULE_EXECUTION.json'),'public_metadata':metadata,'metadata_binding':{'filename':'metadata.json','sha256':m.sha(p/'metadata.json')},'prior_dois':['10.5281/zenodo.'+str(1000+int(rid[4:]))]}
   self.specs.append({'run_id':rid,'path':str(p)})
  self.source=m.binding(self.root/'notes/Run-125/metadata.json');self.consume_calls=0
 def consume(self,p,*args):self.consume_calls+=1;return deepcopy(self.records[p.name])
 def authority_consumer(self,*args):return {'status':'APPROVED_RULE_AUTHORITY','actual_authority':'SYNTHETIC_UNIT_STUB_ONLY'}
 def kw(self):return {'consume':self.consume,'consume_authority':self.authority_consumer}
 def prepare(self,**extra):return m.prepare(self.root,self.out,'2026-W41',self.specs,self.authority_binding,self.source,'2026-10-07',render=lambda p:b'%PDF-SYNTHETIC WRAPPER TEST ONLY',**self.kw(),**extra)
 def bound(self):self.prepare();return m.publication_binding(self.out,self.root,'2026-10-07T12:00:00+00:00',**self.kw())
 def close(self):self.tmp.cleanup()
 def record(self):
  manifest=json.loads((self.out/'DIGEST_MANIFEST.json').read_text());names=[u['filename']for u in manifest['uploads']]+['DIGEST_MANIFEST.json','PUBLICATION_BINDING.json']
  return {'id':77,'doi':'10.5281/zenodo.77','metadata':manifest['public_metadata'],'pids':{'doi':{'identifier':'10.5281/zenodo.77','provider':'datacite'}},'files':[{'key':n,'checksum':'md5:'+hashlib.md5((self.out/n).read_bytes()).hexdigest(),'size':(self.out/n).stat().st_size}for n in names]}
 def own(self):return {'record_id':'77','doi':'10.5281/zenodo.77','method':'POST','url':'https://zenodo.org/api/deposit/depositions/77/actions/publish','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'}
 def readback(self,record=None,own=None,download=None,expected=None):
  r=record or self.record();return m.strict_readback(self.out,self.root,r,own or self.own(),download or (lambda f,rid:(self.out/f['key']).read_bytes()),expected_record=expected or self.record(),**self.kw())

class DigestTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def hold(self,fn):
  with self.assertRaises((m.DigestHold,TransportHold,ValueError,FileNotFoundError)):fn()
 def test_legacy_type_fields_preserved_exactly_when_present(self):
  path=Path(self.f.source['path']);source=json.loads(path.read_bytes());source.update(upload_type='publication',publication_type='preprint');save(path,source);self.f.source=m.binding(path)
  self.f.records['Run-125']['public_metadata']=source;self.f.records['Run-125']['metadata_binding']['sha256']=m.sha(path)
  for u in self.f.records['Run-125']['uploads']:
   if u['filename']=='metadata.json':u['sha256']=m.sha(path)
  result=self.f.prepare();self.assertEqual(result['public_metadata']['upload_type'],'publication');self.assertEqual(result['public_metadata']['publication_type'],'preprint')
 def test_absent_legacy_type_fields_never_invented(self):
  result=self.f.prepare();self.assertNotIn('upload_type',result['public_metadata']);self.assertNotIn('publication_type',result['public_metadata'])
 def test_native_type_shape_preserved_without_translation(self):
  path=Path(self.f.source['path']);source=json.loads(path.read_bytes());source['resource_type']={'type':'publication','subtype':'preprint','title':'Preprint'};save(path,source);self.f.source=m.binding(path)
  self.f.records['Run-125']['public_metadata']=source;self.f.records['Run-125']['metadata_binding']['sha256']=m.sha(path)
  for u in self.f.records['Run-125']['uploads']:
   if u['filename']=='metadata.json':u['sha256']=m.sha(path)
  result=self.f.prepare();self.assertEqual(result['public_metadata']['resource_type'],source['resource_type']);self.assertNotIn('publication_type',result['public_metadata'])
 def test_prepare_not_certification_or_publication(self):
  result=self.f.prepare();self.assertFalse(result['certifies']);self.assertFalse(result['local_lean_execution']);self.assertEqual(result['zenodo_writes'],0);self.assertEqual(result['status'],'ASSEMBLED_NOT_PUBLICATION_BOUND');self.assertFalse(result['review_pdf_is_publication']);self.assertEqual(len(result['notes']),2);self.assertIn(m.DISCLAIMER,(self.f.out/'paper.tex').read_text())
 def repin_upload(self,name,data):
  self.f.out.joinpath(name).write_bytes(data);p=self.f.out/'DIGEST_MANIFEST.json';manifest=json.loads(p.read_text())
  for u in manifest['uploads']:
   if u['filename']==name:u.update(sha256=m.digest(data),md5=hashlib.md5(data).hexdigest(),bytes=len(data))
  if name=='metadata.json':manifest['public_metadata']=json.loads(data)
  save(p,manifest)
 def test_rehashed_broader_aggregate_metadata_holds(self):
  self.f.prepare();v=json.loads((self.f.out/'metadata.json').read_text());v['description']='<p>Every historical claim is verified.</p>';self.repin_upload('metadata.json',m.raw_json(v));self.hold(lambda:m.publication_binding(self.f.out,self.f.root,**self.f.kw()))
 def test_rehashed_broader_wrapper_holds(self):
  self.f.prepare();self.repin_upload('paper.tex',b'All historical claims verified');self.hold(lambda:m.publication_binding(self.f.out,self.f.root,**self.f.kw()))
 def test_aggregate_title_cannot_change(self):
  self.f.prepare();v=json.loads((self.f.out/'metadata.json').read_text());v['title']='All Science Certified';self.repin_upload('metadata.json',m.raw_json(v));self.hold(lambda:m.publication_binding(self.f.out,self.f.root,**self.f.kw()))
 def test_manifest_cannot_claim_certification(self):
  self.f.prepare();p=self.f.out/'DIGEST_MANIFEST.json';v=json.loads(p.read_text());v['certifies']=True;save(p,v);self.hold(lambda:m.require_current(self.f.out,self.f.root,**self.f.kw()))
 def test_binding_cannot_fabricate_reviewer(self):
  self.f.bound();p=self.f.out/'PUBLICATION_BINDING.json';v=json.loads(p.read_text());v['reviewer']='Claude';save(p,v);self.hold(lambda:m.require_publication_bound(self.f.out,self.f.root,**self.f.kw()))
 def test_candidate_absent_from_archive_holds(self):
  r=self.f.records['Run-125'];r['uploads']=[u for u in r['uploads']if u['filename']!='candidate.lean'];self.hold(self.f.prepare)
 def test_certificate_absent_from_archive_holds(self):
  r=self.f.records['Run-125'];r['uploads']=[u for u in r['uploads']if u['filename']!='certificate.json'];self.hold(self.f.prepare)
 def test_frozen_statement_absent_from_archive_holds(self):
  r=self.f.records['Run-125'];r['uploads']=[u for u in r['uploads']if u['filename']!='statement.lean'];self.hold(self.f.prepare)
 def test_expected_readback_cannot_substitute_broader_payload(self):
  self.f.bound();r=self.f.record();r['metadata']['description']='Every historical claim certified';self.hold(lambda:self.f.readback(r,expected=deepcopy(r)))
 def test_consumption_current_source_metadata_overlap_pass(self):self.f.bound();self.assertEqual(m.require_current(self.f.out,self.f.root,**self.f.kw())['release_week'],'2026-W41')
 def test_publication_binding_is_mechanical_not_fake_claude(self):
  b=self.f.bound();self.assertIn('no new Claude identity',b['review_provenance']);self.assertNotIn('reviewer',b);self.assertFalse(b['certifies']);before=(self.f.out/'PUBLICATION_BINDING.json').read_bytes();m.publication_binding(self.f.out,self.f.root,**self.f.kw());self.assertEqual(before,(self.f.out/'PUBLICATION_BINDING.json').read_bytes())
 def test_existing_immutable_output_never_overwritten(self):self.f.prepare();before=(self.f.out/'paper.tex').read_bytes();self.hold(self.f.prepare);self.assertEqual(before,(self.f.out/'paper.tex').read_bytes())
 def test_main_file_change_holds(self):self.f.bound();(self.f.out/'paper.pdf').write_bytes(b'%PDF-CHANGED');self.hold(lambda:m.require_publication_bound(self.f.out,self.f.root,**self.f.kw()))
 def test_missing_binding_prewrite_holds(self):self.f.prepare();self.hold(lambda:m.prewrite(self.f.out,self.f.root,'POST','2026-10-07T13:00:00Z',[],complete_journal=True,**self.f.kw()))
 def test_changed_binding_holds(self):self.f.bound();save(self.f.out/'PUBLICATION_BINDING.json',{'status':'PUBLICATION_BOUND'});self.hold(lambda:m.require_publication_bound(self.f.out,self.f.root,**self.f.kw()))
 def test_changed_note_source_holds(self):self.f.bound();p=Path(self.f.specs[0]['path'])/'paper.tex';p.write_bytes(b'CHANGED');self.hold(lambda:m.require_current(self.f.out,self.f.root,**self.f.kw()))
 def test_note_hold_never_admitted(self):self.f.records['Run-125']['status']='HOLD';self.hold(self.f.prepare);self.assertFalse(self.f.out.exists())
 def test_foreign_certificate_run_holds(self):
  r=self.f.records['Run-125'];p=Path(r['certificate']['path']);save(p,{'run_id':'Run-999'});r['certificate']=m.binding(p);self.hold(self.f.prepare)
 def test_foreign_note_result_run_holds(self):self.f.records['Run-125']['run_id']='Run-126';self.hold(self.f.prepare)
 def test_duplicate_note_holds(self):self.f.specs.append(deepcopy(self.f.specs[0]));self.hold(self.f.prepare)
 def test_unknown_basis_holds(self):self.f.records['Run-125']['foundation_basis']='CONJECTURE';self.hold(self.f.prepare)
 def test_unreviewed_metadata_holds(self):self.f.records['Run-125'].pop('metadata_binding');self.hold(self.f.prepare)
 def test_changed_metadata_holds(self):save(Path(self.f.specs[0]['path'])/'metadata.json',{'title':'CHANGED'});self.hold(self.f.prepare)
 def test_all_definitional_note_only_appendix(self):
  self.f.records['Run-125']['claim_reviews'][0]['semantic_tier']='DEFINITIONAL';mft=self.f.prepare();n=mft['notes'][0];self.assertEqual(n['section'],'DEFINITIONAL_OR_NONVACUITY_PENDING_APPENDIX');self.assertFalse(n['claim_table'][0]['headline_eligible'])
 def test_tier0_nonempty_domains_printed(self):
  self.f.records['Run-125']['claim_reviews'][0]['nonvacuity']={'tier':'TIER0','status':'NO_HYPOTHESES','domains':['Real']};mft=self.f.prepare();self.assertEqual(mft['notes'][0]['claim_table'][0]['nonvacuity_label'],'NO_HYPOTHESES (domain nonempty: Real)')
 def test_missing_tier0_domain_holds(self):self.f.records['Run-125']['claim_reviews'][0]['nonvacuity']={'tier':'TIER0','status':'NO_HYPOTHESES','domains':[]};self.hold(self.f.prepare)
 def test_tier1_not_demonstrated_never_headline(self):
  self.f.records['Run-125']['claim_reviews'][0]['nonvacuity']={'tier':'TIER1','status':'NOT_DEMONSTRATED'};mft=self.f.prepare();n=mft['notes'][0];self.assertFalse(n['claim_table'][0]['headline_eligible']);self.assertEqual(n['claim_table'][0]['nonvacuity_label'],'certified; nonvacuity not demonstrated')
 def test_tier1_no_certificate_holds(self):self.f.records['Run-125']['claim_reviews'][0]['nonvacuity'].pop('certificate');self.hold(self.f.prepare)
 def test_unknown_semantic_label_holds(self):self.f.records['Run-125']['claim_reviews'][0]['semantic_tier']='UNCERTAIN';self.hold(self.f.prepare)
 def test_foreign_claim_review_holds(self):self.f.records['Run-125']['claim_reviews'][0]['lean_theorem']='other';self.hold(self.f.prepare)
 def test_authority_changed_holds(self):self.f.authority.write_bytes(b'CHANGED');self.hold(self.f.prepare)
 def test_false_authority_holds(self):self.f.authority_consumer=lambda *a:{'status':'HOLD'};self.hold(self.f.prepare)
 def test_wrong_publication_week_holds(self):self.hold(lambda:m.metadata_proposal({'creators':[],'license':'cc-by'},'2026-W41',[],'2026-10-14'))
 def test_creator_license_shape_preserved(self):
  mft=self.f.prepare();source=json.loads(Path(self.f.source['path']).read_text());self.assertEqual(mft['public_metadata']['license'],source['license']);self.assertEqual(mft['public_metadata']['creators'],source['creators']);self.assertNotIn('doi',mft['public_metadata']);self.assertEqual(mft['public_metadata']['title'],'Viridis Methods Digest — 2026-W41')
 def test_review_pdf_cannot_replace_wrapper(self):self.f.bound();p=self.f.out/'DIGEST_MANIFEST.json';v=json.loads(p.read_text());v['review_pdf_is_publication']=True;save(p,v);self.hold(lambda:m.require_current(self.f.out,self.f.root,**self.f.kw()))
 def test_strict_own_readback_pass(self):self.f.bound();self.assertEqual(self.f.readback()['status'],'STRICT_OWN_PUBLIC_READBACK_PASS')
 def test_foreign_record_readback_holds(self):self.f.bound();r=self.f.record();r['id']=78;self.hold(lambda:self.f.readback(record=r))
 def test_foreign_publish_receipt_holds(self):self.f.bound();r=self.f.own();r['record_id']='78';self.hold(lambda:self.f.readback(own=r))
 def test_changed_readback_description_holds(self):self.f.bound();r=self.f.record();r['metadata']['description']='BROADER';self.hold(lambda:self.f.readback(record=r))
 def test_missing_public_file_holds(self):self.f.bound();r=self.f.record();r['files'].pop();self.hold(lambda:self.f.readback(record=r))
 def test_duplicate_public_filename_holds(self):self.f.bound();r=self.f.record();r['files'].append(deepcopy(r['files'][0]));self.hold(lambda:self.f.readback(record=r))
 def test_public_checksum_change_holds(self):self.f.bound();r=self.f.record();r['files'][0]['checksum']='md5:'+'0'*32;self.hold(lambda:self.f.readback(record=r))
 def test_download_bytes_changed_holds(self):self.f.bound();self.hold(lambda:self.f.readback(download=lambda f,rid:b'CHANGED'))
 def test_public_PID_changed_holds(self):self.f.bound();r=self.f.record();r['pids']['doi']['identifier']='10.5281/zenodo.78';self.hold(lambda:self.f.readback(record=r))
 def test_public_file_order_ignored_by_filename(self):self.f.bound();r=self.f.record();r['files'].reverse();self.assertEqual(self.f.readback(record=r)['status'],'STRICT_OWN_PUBLIC_READBACK_PASS')
 def test_spoof_empty_journal_cannot_prewrite(self):self.f.bound();self.hold(lambda:m.prewrite(self.f.out,self.f.root,'POST','2026-10-07T13:00:00Z',[],complete_journal=True,**self.f.kw()))
 def test_prewrite_requires_fresh_actual_budget_consumer(self):
  self.f.bound();at='2026-10-07T13:00:00Z';r=m.prewrite(self.f.out,self.f.root,'POST',at,[],complete_journal=True,budget_consumer=lambda *args:m.require_write_budget([],'POST',at,complete=True),**self.f.kw());self.assertEqual(r['used'],0)

class ArchiveTests(unittest.TestCase):
 def setUp(self):self.members=[('notes/Run-125/a.lean',b'UNCHANGED'),('notes/Run-125/b.json',b'{}')];self.inventory=m.member_inventory(self.members)
 def test_deterministic_bytes(self):self.assertEqual(m.archive_bytes(self.members),m.archive_bytes(reversed(self.members)));self.assertEqual(m.require_archive(m.archive_bytes(self.members),self.inventory)['members'],2)
 def test_missing_member_holds(self):
  with self.assertRaises(m.DigestHold):m.require_archive(m.archive_bytes(self.members[:1]),self.inventory)
 def test_changed_member_holds(self):
  with self.assertRaises(m.DigestHold):m.require_archive(m.archive_bytes([('notes/Run-125/a.lean',b'CHANGED'),self.members[1]]),self.inventory)
 def test_extra_member_holds(self):
  with self.assertRaises(m.DigestHold):m.require_archive(m.archive_bytes(self.members+[('extra',b'X')]),self.inventory)
 def test_duplicate_member_holds(self):
  with self.assertRaises(m.DigestHold):m.archive_bytes(self.members+[self.members[0]])
 def test_traversal_absolute_dot_backslash_holds(self):
  for name in ('../secret','/secret','notes/../secret','notes//file','notes/./file','notes\\file'):
   with self.subTest(name=name),self.assertRaises(m.DigestHold):m.archive_bytes([(name,b'X')])
 def test_forged_zip_symlink_holds(self):
  b=io.BytesIO()
  with zipfile.ZipFile(b,'w')as z:
   i=zipfile.ZipInfo(self.members[0][0]);i.create_system=3;i.external_attr=(stat.S_IFLNK|0o600)<<16;z.writestr(i,b'UNCHANGED')
  with self.assertRaises(m.DigestHold):m.require_archive(b.getvalue(),self.inventory)
 def test_duplicate_inventory_holds(self):
  with self.assertRaises(m.DigestHold):m.require_archive(m.archive_bytes(self.members),self.inventory+[self.inventory[0]])

class DiscoveryBudgetTests(unittest.TestCase):
 def test_incomplete_discovery_holds(self):
  with self.assertRaises(m.DigestHold):m.discover_weekly_record([],'2026-W41')
 def test_complete_no_existing_is_only_discovery(self):self.assertEqual(m.discover_weekly_record([],'2026-W41',complete=True)['status'],'NO_EXISTING_WEEKLY_RECORD')
 def test_existing_weekly_chain_discovery(self):
  records=[{'id':77,'conceptrecid':70,'doi':'10.5281/zenodo.77','versions':{'is_latest':True},'metadata':{'title':m.week_title('2026-W41')}}];self.assertEqual(m.discover_weekly_record(records,'2026-W41',complete=True)['record_id'],'77')
 def test_two_weekly_concepts_holds(self):
  records=[{'id':i,'conceptrecid':i,'doi':'10.5281/zenodo.'+str(i),'versions':{'is_latest':True},'metadata':{'title':m.week_title('2026-W41')}}for i in(77,78)]
  with self.assertRaises(m.DigestHold):m.discover_weekly_record(records,'2026-W41',complete=True)
 def events(self,n):return [{'operation_id':str(i),'method':'PUT','host':'zenodo.org','at_utc':'2026-10-07T12:00:00Z','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY','receipt_binding':{'path':'SYNTHETIC','sha256':'a'*64}}for i in range(n)]
 def test_nine_writes_permits_tenth(self):self.assertEqual(m.require_write_budget(self.events(9),'POST','2026-10-07T13:00:00Z',complete=True)['used'],9)
 def test_ten_writes_blocks_even_if_all_uncertain(self):
  with self.assertRaises(m.DigestHold):m.require_write_budget(self.events(10),'POST','2026-10-07T13:00:00Z',complete=True)
 def test_incomplete_budget_holds(self):
  with self.assertRaises(m.DigestHold):m.require_write_budget([],'POST','2026-10-07T13:00:00Z')
 def test_duplicate_operation_holds(self):
  events=self.events(1)*2
  with self.assertRaises(m.DigestHold):m.require_write_budget(events,'POST','2026-10-07T13:00:00Z',complete=True)
 def test_future_operation_holds(self):
  events=self.events(1);events[0]['at_utc']='2026-10-08T13:00:00Z'
  with self.assertRaises(m.DigestHold):m.require_write_budget(events,'POST','2026-10-07T13:00:00Z',complete=True)
 def test_new_york_day_boundary(self):
  events=self.events(10)
  for event in events:event['at_utc']='2026-10-07T02:00:00Z'
  self.assertEqual(m.require_write_budget(events,'POST','2026-10-07T13:00:00Z',complete=True)['used'],0)

if __name__=='__main__':unittest.main(verbosity=2)
