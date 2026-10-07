"""Synthetic offline rule tests: no Lean, issuer, transport or genuine approvals."""
import unittest,json,tempfile,datetime as dt
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import phase7_audit_policy as p
import methods_digest as d

def raw(x):return d.raw_json(x)
def save(f,x):f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw(x));return {'path':str(f),'sha256':d.sha(f)}

class AuthorityTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.r=self.root/'reports/verification-coverage';self.r.mkdir(parents=True);section=(p.SECTION_HEADER+'\nApproved synthetic fixture; no genuine human review.\n').encode();(self.r/'GAME_PLAN.md').write_bytes(section+b'\n## Future unrelated section\nX\n');f=self.r/'authority';f.mkdir();self.pins={};bindings={}
  for name in p.PINS:
   if name=='audit_section':b=section
   elif name=='audited_packet_json':b=raw({'rows':[{'run_id':f'Run-{i:03d}'}for i in range(100,156)]})
   elif name=='audited_input_manifest':b=raw({'file_count':1,'files':[{'path':str(f/'source.txt'),'relative_path':'source.txt','sha256':d.digest(b'fixture'),'bytes':7}]})
   else:b=b'Packet fixture'
   q=f/(name+'.json'if name!='audit_section'else'SECTION.md');q.write_bytes(b);bindings[name]={'path':str(q),'sha256':d.digest(b)};self.pins[name]=d.digest(b)
  (f/'source.txt').write_bytes(b'fixture');self.authority={'standard':p.AUTH_STANDARD,'status':'APPROVED_RULE_AUTHORITY','tree_root':str(self.root),'assembly_observed_at_utc':'2020-01-01T00:00:00Z','authority_source':p.AUTHORITY_SOURCE,**bindings};self.ap=self.root/p.AUTHORITY_REL;self.binding=save(self.ap,self.authority)
  self.s=patch.multiple(p,PINS=self.pins,AUTHORITY_SHA=self.binding['sha256']);self.s.start();self.addCleanup(self.s.stop)
 def check(self):return p.require_audit_authority(self.root,self.binding)
 def update(self):self.binding=save(self.ap,self.authority);p.AUTHORITY_SHA=self.binding['sha256']
 def test_exact_actual_rules_fixture_pass(self):self.assertEqual(self.check()['status'],'APPROVED_RULE_AUTHORITY')
 def test_caller_approval_boolean_rejected(self):self.authority['approved']=True;self.update();self.assertRaises(ValueError,self.check)
 def test_wrong_authority_identity_rejected(self):self.binding['sha256']='f'*64;self.assertRaises(ValueError,self.check)
 def test_selfreview_identity_rejected(self):self.authority['authority_source']='Codex says approved';self.update();self.assertRaises(ValueError,self.check)
 def test_future_authority_rejected(self):self.authority['assembly_observed_at_utc']='2099-01-01T00:00:00Z';self.update();self.assertRaises(ValueError,self.check)
 def test_changed_gameplan_rule_rejected(self):f=self.r/'GAME_PLAN.md';f.write_bytes(f.read_bytes().replace(b'Approved',b'Changed'));self.assertRaises(ValueError,self.check)
 def test_changed_input_bytes_rejected(self):(self.r/'authority/source.txt').write_bytes(b'wrong');self.assertRaises(ValueError,self.check)
 def test_missing_audited_input_rejected(self):(self.r/'authority/source.txt').unlink();self.assertRaises(Exception,self.check)
 def test_packet_count55_rejected(self):
  q=Path(self.authority['audited_packet_json']['path']);q.write_bytes(raw({'rows':[{'run_id':f'Run-{i:03d}'}for i in range(100,155)]}));self.authority['audited_packet_json']['sha256']=d.sha(q);self.pins['audited_packet_json']=d.sha(q);self.update();self.assertRaises(ValueError,self.check)
 def test_authority_symlink_rejected(self):
  original=self.ap.with_name('orig.json');self.ap.rename(original);self.ap.symlink_to(original);self.assertRaises(ValueError,self.check)

class ExactScopeTests(unittest.TestCase):
 def setUp(self):
  self.original=[{'lean_theorem':'t','exact_source_signature':'theorem t (h : P) : Q','ambient_source_context':[{'line':1,'source_text':'variable (h₂ : R)'}],'english_claim':'Under all printed premises Q holds','nonvacuity_obligation':None,'model_fidelity':{'defined':['P','Q','R'],'empirically_identified':[]},'evidence_class':'FORMALLY_VERIFIED'}];self.reviews=[{'lean_theorem':'t','semantic_tier':'ROUTINE','nonvacuity':{'tier':'TIER0','status':'NO_HYPOTHESES','domains':['Unit']}}]
 def test_exact_scope_pass(self):self.assertEqual(p._scope_derivative(deepcopy(self.original),self.original,self.reviews,'Run-150'),self.original)
 def test_hypothesis_drop_rejected(self):v=deepcopy(self.original);v[0]['exact_source_signature']='theorem t : Q';self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_ambient_drop_rejected(self):v=deepcopy(self.original);v[0]['ambient_source_context']=[];self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_witness_null_cannot_be_mutated(self):v=deepcopy(self.original);v[0]['nonvacuity_obligation']='fabricated';self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_stronger_english_rejected(self):v=deepcopy(self.original);v[0]['english_claim']='Q without hypotheses';self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_defined_to_empirical_rejected(self):v=deepcopy(self.original);v[0]['model_fidelity']['empirically_identified']=['P'];self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_only_defs_demotion_permitted(self):v=deepcopy(self.original);v[0]['evidence_class']='CERTIFIED_TRIVIAL';r=deepcopy(self.reviews);r[0]['semantic_tier']='DEFINITIONAL';self.assertEqual(p._scope_derivative(v,self.original,r,'Run-150'),v)
 def test_routine_cannot_change_class(self):v=deepcopy(self.original);v[0]['evidence_class']='CERTIFIED_TRIVIAL';self.assertRaises(ValueError,p._scope_derivative,v,self.original,self.reviews,'Run-150')
 def test_certified_trivial_no_upgrade(self):old=deepcopy(self.original);old[0]['evidence_class']='CERTIFIED_TRIVIAL';self.assertRaises(ValueError,p._scope_derivative,self.original,old,self.reviews,'Run-150')

class SupplementalTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.r=Path(self.t.name).resolve();self.run='Run-150';self.source='import Mathlib\nnamespace Fixture\ntheorem t (x : ℝ) : x = x := by rfl\nend Fixture\n';self.candidate=self.source+'\n#reduce (0, "PHASE7_PROBE:Run-150:S01")\n';self.formal=self.candidate
  from theorem_coverage import triviality
  self.sig=triviality(self.source)['t']['signature'];self.main={'path':str(self.r/'main.json'),'sha256':'a'*64};self.scope=[{'lean_theorem':'t','nonvacuity_obligation':None}]
  self.sm={'run_id':self.run,'main_certificate':self.main,'original_source_prefix':{'binding':{'path':str(self.r/'main.lean'),'sha256':d.digest(self.source.encode())},'byte_length':len(self.source.encode())},'claims':[{'theorem':'t','tier':'TIER0','exact_signature_sha256':d.digest(self.sig.encode()),'source_context':[],'probe':{'print_label':'PHASE7_PROBE:Run-150:S01'}}]};self.mb=save(self.r/'SUPPLEMENTAL_MANIFEST.json',self.sm);self.cb=save(self.r/'candidate.lean',{'x':1});(self.r/'candidate.lean').write_bytes(self.candidate.encode());self.cb={'path':str(self.r/'candidate.lean'),'sha256':d.sha(self.r/'candidate.lean')};(self.r/'formal.lean').write_bytes(self.formal.encode());self.fb={'path':str(self.r/'formal.lean'),'sha256':d.sha(self.r/'formal.lean')}
  self.request={'source_run':self.run,'supplemental_only':True,'issuer_output_must_not_replace_main_certificate':True,'expected_theorem_names':['phase7_probe_S01_range'],'nonvacuity_obligations':['phase7_bundle_domain_inhabited'],'input_sha256':{'SUPPLEMENTAL_MANIFEST.json':self.mb['sha256']}};self.rb=save(self.r/'request.json',self.request)
  self.requestid='12345678-1234-1234-1234-123456789abc';pos=p.probes.observation_positions(self.candidate)['PHASE7_PROBE:Run-150:S01']['line'];out=f'info: Challenge.lean:{pos}:0: (0, "PHASE7_PROBE:Run-150:S01")\ninfo: Solution.lean:{pos}:0: (0, "PHASE7_PROBE:Run-150:S01")'
  self.response={'type':'verification-ok','project':'viridis-lean-4.28','requestId':self.requestid,'theoremNames':['phase7_probe_S01_range','phase7_bundle_domain_inhabited'],'output':out,'executionEvidence':{'executionId':self.requestid,'delivery':{'mode':'FRESH_EXECUTION','servedForRequestId':self.requestid}}}
  self.cloud={'provider_response':self.response,'provider_response_sha256':d.digest((json.dumps(self.response,sort_keys=True,separators=(',',':'))+'\n').encode()),'request':self.rb,'candidate':self.cb,'formal_statement':self.fb};self.cloudb=save(self.r/'cloud.json',self.cloud);self.cert={'bindings':{'request':self.rb,'candidate_proof':self.cb,'formal_statement':self.fb,'independent_cloud_receipt':self.cloudb}};self.sb=save(self.r/'certificate.json',self.cert)
  self.inspection={'valid':True,'run_id':self.run,'sha256':self.sb['sha256'],'candidate_sha256':self.cb['sha256'],'certified_theorems':['phase7_probe_S01_range','phase7_bundle_domain_inhabited'],'nonvacuity':['phase7_bundle_domain_inhabited']}
  self.contract={'runs':{self.run:{'manifest':deepcopy(self.sm),'request_sha256':self.rb['sha256'],'candidate_sha256':self.cb['sha256'],'formal_statement_sha256':self.fb['sha256'],'expected_theorem_names':self.request['expected_theorem_names'],'nonvacuity_obligations':self.request['nonvacuity_obligations']}}};self.cr=raw(self.contract);self.actualread=d.read_regular
  def rd(path):return self.cr if Path(path).name=='PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json'else self.actualread(path)
  self.rpatch=patch.object(d,'read_regular',side_effect=rd);self.rpatch.start();self.addCleanup(self.rpatch.stop);self.cpatch=patch.object(p,'CONTRACT_SHA',d.digest(self.cr));self.cpatch.start();self.addCleanup(self.cpatch.stop)
  self.pipeline=patch('certificate_inspection.pipeline_modules',return_value=(None,type('IssuerFixture',(),{'assess_job_observation':staticmethod(lambda *args:{'status':'OBSERVATION_MATCH_PARTIAL'})})()));self.pipeline.start();self.addCleanup(self.pipeline.stop)
 def inspect(self,*args):return deepcopy(self.inspection)
 def call(self):return p._supplemental(self.r,self.run,self.main,self.source,self.scope,self.mb,self.sb,self.inspect,{})
 def changed_response(self):
  self.cloud['provider_response']=self.response;self.cloud['provider_response_sha256']=d.digest((json.dumps(self.response,sort_keys=True,separators=(',',':'))+'\n').encode());self.cloudb=save(self.r/'cloud.json',self.cloud);self.cert['bindings']['independent_cloud_receipt']=self.cloudb;self.sb=save(self.r/'certificate.json',self.cert);self.inspection['sha256']=self.sb['sha256']
 def test_rehashed_other_request_field_hold(self):
  self.request['candidate_id']='unapproved-new-identity';self.rb=save(self.r/'request.json',self.request);self.cert['bindings']['request']=self.rb;self.cloud['request']=self.rb;self.cloudb=save(self.r/'cloud.json',self.cloud);self.cert['bindings']['independent_cloud_receipt']=self.cloudb;self.sb=save(self.r/'certificate.json',self.cert);self.inspection['sha256']=self.sb['sha256'];self.assertRaises(ValueError,self.call)
 def test_same_job_tags_tier0_pass(self):r,_=self.call();self.assertEqual(r[0]['semantic_tier'],'DEFINITIONAL');self.assertEqual(r[0]['nonvacuity']['status'],'NO_HYPOTHESES')
 def test_missing_tags_hold_never_substantive(self):self.response['output']='';self.changed_response();self.assertRaises(ValueError,self.call)
 def test_conflicting_tags_hold(self):self.response['output']=self.response['output'].replace('Solution.lean:'+str(p.probes.observation_positions(self.candidate)['PHASE7_PROBE:Run-150:S01']['line'])+':0: (0,','Solution.lean:'+str(p.probes.observation_positions(self.candidate)['PHASE7_PROBE:Run-150:S01']['line'])+':0: (1,');self.changed_response();self.assertRaises(ValueError,self.call)
 def test_duplicate_tags_hold(self):self.response['output']+='\n'+self.response['output'];self.changed_response();self.assertRaises(ValueError,self.call)
 def test_recovered_other_job_receipt_hold(self):self.response['recoveredFromTerminalJournal']=True;self.response['executionEvidence']['executionId']='other-job';self.changed_response();self.assertRaises(ValueError,self.call)
 def test_same_own_fresh_terminal_retrieval_allowed(self):self.response['recoveredFromTerminalJournal']=True;self.changed_response();self.assertEqual(self.call()[0][0]['semantic_tier'],'DEFINITIONAL')
 def test_disk_cache_terminal_not_allowed(self):self.response['recoveredFromDiskCache']=True;self.changed_response();self.assertRaises(ValueError,self.call)
 def test_inflight_reuse_hold(self):self.response['executionEvidence']['delivery']['mode']='IN_FLIGHT_REUSE';self.changed_response();self.assertRaises(ValueError,self.call)
 def test_own_id_mismatch_hold(self):self.response['executionEvidence']['executionId']='other';self.changed_response();self.assertRaises(ValueError,self.call)
 def test_source_contract_changed_hold(self):(self.r/'candidate.lean').write_text(self.candidate+'--different');self.assertRaises(ValueError,self.call)
 def test_wrong_run_cert_hold(self):self.inspection['run_id']='Run-151';self.assertRaises(ValueError,self.call)
 def test_cert_inspector_rejected_hold(self):self.inspection['valid']=False;self.assertRaises(ValueError,self.call)
 def test_missing_range_export_hold(self):self.inspection['certified_theorems']=[];self.assertRaises(ValueError,self.call)
 def test_missing_witness_export_hold(self):self.inspection['nonvacuity']=[];self.assertRaises(ValueError,self.call)
 def test_manifest_dropped_context_hold(self):self.sm['claims'][0]['source_context']=[{'line':1,'source_text':'variable (h : False)'}];self.mb=save(self.r/'SUPPLEMENTAL_MANIFEST.json',self.sm);self.assertRaises(ValueError,self.call)
 def test_response_hash_corrupted_hold(self):self.cloud['provider_response_sha256']='b'*64;self.cloudb=save(self.r/'cloud.json',self.cloud);self.cert['bindings']['independent_cloud_receipt']=self.cloudb;self.sb=save(self.r/'certificate.json',self.cert);self.inspection['sha256']=self.sb['sha256'];self.assertRaises(ValueError,self.call)


class FullAdmissionFixtureTests(unittest.TestCase):
 """Synthetic authority/inspector injection; genuine consumers are never bypassed in production."""
 def setUp(self):
  import shutil
  try:import proposed_scoped_release
  except ModuleNotFoundError:import scoped_release as proposed_scoped_release
  from test_scoped_release import Fixture
  real_assess=proposed_scoped_release.assess
  self.f=Fixture();self.addCleanup(self.f.close);self.r=self.f.root;self.note=self.f.bundle;self.audited=self.r/'audited';shutil.copytree(self.note,self.audited)
  aw=json.loads((self.audited/'claim_map.json').read_bytes());aw['formal_section_spans']=[];aw['successor_regions']=[];aw['uncertified_remark_spans']=[];(self.audited/'claim_map.json').write_bytes(raw(aw))
  self.auditmanifest={'path':str(self.audited/'SCOPED_RELEASE_MANIFEST.json'),'sha256':d.sha(self.audited/'SCOPED_RELEASE_MANIFEST.json')};self.source={'path':str(self.audited/'paper.tex'),'sha256':d.sha(self.audited/'paper.tex')};self.before=save(self.r/'before.json',{'title':'Exact original title','keywords':['original'],'description':'Historical source; conditional assertions retained only in archive.'})
  self.authority=save(self.r/'AUTHORITY.json',{'synthetic':True});self.row={'run_id':'Run-141','evidence':{'release_manifest':self.auditmanifest,'paper_tex':self.source,'basis':{'path':str(self.audited/'foundation_basis.json'),'sha256':d.sha(self.audited/'foundation_basis.json')},'metadata_before':self.before},'existing_dois':['10.5281/zenodo.22236496']}
  self.reviews=[{'lean_theorem':v['lean_theorem'],'semantic_tier':'ROUTINE','nonvacuity':{'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':v['nonvacuity_obligation'],'certificate':self.f.manifest['certificate']}}for v in self.f.manifest['statement_scope']]
  oldtex=self.f.tex.read_bytes();final=p.apply_review_labels(oldtex,self.reviews);self.f.tex.write_bytes(final);self.f.rebind(self.f.tex)
  from phase7_claim_label_render import shift_whole_paper_map
  whole=shift_whole_paper_map(json.loads((self.audited/'claim_map.json').read_bytes()),oldtex,final,p.render_claim_table(self.reviews));whole['paper']={'path':str(self.f.tex),'sha256':d.sha(self.f.tex)};whole['final_pdf']={'path':str(self.f.pdf),'sha256':d.sha(self.f.pdf)};self.f.map_path.write_bytes(raw(whole));self.f.rebind(self.f.map_path,'claim_map')
  from publication_gate import scoped_metadata_proposal
  metadata=scoped_metadata_proposal(json.loads((self.r/'before.json').read_bytes()),{'statement_scope':self.f.manifest['statement_scope'],'foundation_basis':self.f.basis['foundation_basis']});self.metadata=self.note/'metadata.json';self.metadata.write_bytes(raw(metadata));self.f.manifest['uploads'].append({'filename':self.metadata.name,'sha256':d.sha(self.metadata)});self.f.commit()
  self.sm=save(self.r/'SUPPLEMENTAL_MANIFEST.json',{'synthetic':True})
  required=('candidate_proof','formal_statement','request','independent_cloud_receipt','sealed_statement_contract','statement_alignment_receipt');self.scert={'bindings':{key:save(self.r/(key+'.json'),{'fixture':key})for key in required}};self.scert['bindings']['sealed_paper_inputs']={key:save(self.r/key,{'fixture':key})for key in('SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json','SEALED_paper.pdf','SEALED_paper.tex')};self.sc=save(self.r/'SUPPLEMENTAL_CERTIFICATE.json',self.scert)
  family=[('LEAN_ZERO_SORRY_CERTIFICATE.json',d.read_regular(self.r/'SUPPLEMENTAL_CERTIFICATE.json'))]
  for key in sorted(required):b=self.scert['bindings'][key];f=Path(b['path']);family.append((key+'/'+f.name,f.read_bytes()))
  for key,b in sorted(self.scert['bindings']['sealed_paper_inputs'].items()):family.append(('sealed_paper_inputs/'+key,Path(b['path']).read_bytes()))
  descriptor={'standard':'VRS-SUPPLEMENTAL-EVIDENCE-FAMILY-1','certificate':self.sc,'run_id':'Run-141','members':d.member_inventory(family),'certifies':False,'diagnostics_capture_included':False};family.append(('SUPPLEMENTAL_EVIDENCE_MANIFEST.json',raw(descriptor)))
  for name,b in(('SUPPLEMENTAL_WITNESS_CERTIFICATE.json',d.read_regular(self.r/'SUPPLEMENTAL_CERTIFICATE.json')),('SUPPLEMENTAL_WITNESS_EVIDENCE.zip',d.archive_bytes(family))):q=self.note/name;q.write_bytes(b);self.f.manifest['uploads'].append({'filename':name,'sha256':d.sha(q)})
  base_files=[(str(q.relative_to(self.audited)),q.read_bytes())for q in sorted(self.audited.rglob('*'))if q.is_file()]
  for name,obj in(('AUDITED_BASE_MANIFEST.json',{'base':str(self.audited),'members':d.member_inventory(base_files),'source_unchanged':True}),('CLAIM_CLASSIFICATIONS.json',{'run_id':'Run-141','claim_reviews':self.reviews,'status':'PROPOSAL_NOT_RULE_EXECUTION_RECEIPT','authority':self.authority,'source_statements_unchanged':True,'certifies':False}),('SUPPLEMENTAL_WITNESS_MANIFEST.json',descriptor)):
   q=self.note/name;q.write_bytes(raw(obj));self.f.manifest['uploads'].append({'filename':name,'sha256':d.sha(q)})
  q=self.note/'AUDITED_BASE.zip';q.write_bytes(d.archive_bytes(base_files));self.f.manifest['uploads'].append({'filename':q.name,'sha256':d.sha(q)})
  self.f.commit();self.rule={'standard':p.RULE_STANDARD,'status':'APPLIED_APPROVED_RULES','run_id':'Run-141','authority':self.authority,'audited_release_manifest':self.auditmanifest,'source_base_tex':self.source,'before_metadata':self.before,'supplemental_manifest':self.sm,'supplemental_certificate':self.sc,'issued_at_utc':'2020-01-01T00:00:00Z','inputs':{},'claim_reviews':self.reviews,'draft_assessment':{},'execution_consumer_sha256':d.sha(p.__file__)}
  def authority(*args):return {'status':'APPROVED_RULE_AUTHORITY','audited_rows':[self.row],'input_bindings':{}}
  def supplement(root,run,main,source,scope,mb,cb,inspector,snapshots):
   for binding in(mb,cb):p._read_bound(root,binding,snapshots)
   return deepcopy(self.reviews),{'observations':{'synthetic':True},'certificate':self.scert}
  self.patches=[patch.object(p,'require_pdf_provenance',return_value={'synthetic':True}),patch.object(p,'require_audit_authority',side_effect=authority),patch.object(p,'_supplemental',side_effect=supplement),patch.object(p.scoped,'assess',side_effect=lambda *args,**kw:real_assess(*args,**kw))]
  for q in self.patches:q.start();self.addCleanup(q.stop)
  self.result=p.evaluate_note(self.note,self.r,self.authority,rule=self.rule,inspector=self.f.inspector,_preparing=True);self.rule['inputs']=self.result['input_bindings'];self.rule['draft_assessment']=self.result['identity'];self.policy=self.note/'PHASE7_RULE_EXECUTION.json';self.policy.write_bytes(raw(self.rule))
 def call(self):return p.evaluate_note(self.note,self.r,self.authority,rule=self.rule,inspector=self.f.inspector)
 def test_all_exact_synthetic_gate_layers_pass_only_prebinding(self):self.assertEqual(self.call()['status'],'APPROVED_RULES_APPLIED_NOT_PUBLICATION_BOUND')
 def test_unbound_note_no_publication_pass(self):self.assertRaises(Exception,p.require_note_publication_bound,self.note,self.r,self.authority)
 def test_self_review_checklist_cannot_substitute(self):self.rule['checks']={'all':True};self.assertRaises(ValueError,self.call)
 def test_metadata_title_mutation_hold(self):v=json.loads(self.metadata.read_bytes());v['title']='Altered title';self.metadata.write_bytes(raw(v));self.f.rebind(self.metadata);self.assertRaises(ValueError,self.call)
 def test_metadata_scientific_sentence_hold(self):v=json.loads(self.metadata.read_bytes());v['description']+=' Certified empirical validation.';self.metadata.write_bytes(raw(v));self.f.rebind(self.metadata);self.assertRaises(ValueError,self.call)
 def test_main_paper_stronger_text_hold(self):self.f.tex.write_bytes(self.f.tex.read_bytes().replace(b'\\end{document}',b'Unconditional stronger claim.\\end{document}'));self.f.rebind(self.f.tex);self.assertRaises(ValueError,self.call)
 def test_stale_pdf_hash_hold(self):self.f.pdf.write_bytes(self.f.pdf.read_bytes()+b'changed');self.assertRaises(ValueError,self.call)
 def test_dropped_certificate_upload_hold(self):self.f.manifest['uploads']=[v for v in self.f.manifest['uploads']if v['filename']!='CERTIFICATE_UPLOAD.json'];self.f.commit();self.assertRaises(ValueError,self.call)
 def test_dropped_supplemental_archive_hold(self):q=self.note/'SUPPLEMENTAL_WITNESS_EVIDENCE.zip';q.unlink();self.assertRaises(Exception,self.call)
 def test_missing_input_binding_hold(self):self.rule['inputs'].pop(next(iter(self.rule['inputs'])));self.assertRaises(ValueError,self.call)
 def test_extra_arbitrary_input_hold(self):self.rule['inputs']['arbitrary']='a'*64;self.assertRaises(ValueError,self.call)
 def test_wrong_consumer_hash_hold(self):self.rule['execution_consumer_sha256']='f'*64;self.assertRaises(ValueError,self.call)
 def test_wrong_claim_review_hold(self):self.rule['claim_reviews'][0]['semantic_tier']='SUBSTANTIVE';self.assertRaises(ValueError,self.call)
 def test_unreviewed_extra_file_hold(self):
  q=self.note/'new_scientific_claim.md';q.write_bytes(b'Unreviewed stronger science');self.f.manifest['uploads'].append({'filename':q.name,'sha256':d.sha(q)});self.f.commit();self.assertRaises(ValueError,self.call)
 def test_rehashed_extra_science_in_audited_archive_hold(self):
  q=self.note/'AUDITED_BASE.zip';q.write_bytes(d.archive_bytes([('rogue.md',b'New unsupported claim')]));self.f.rebind(q);self.assertRaises(ValueError,self.call)
 def test_rehashed_audited_descriptor_extra_field_hold(self):
  q=self.note/'AUDITED_BASE_MANIFEST.json';v=json.loads(q.read_bytes());v['claim']='Unreviewed science';q.write_bytes(raw(v));self.f.rebind(q);self.assertRaises(ValueError,self.call)
 def test_rehashed_claim_map_extra_science_field_hold(self):
  q=self.f.map_path;v=json.loads(q.read_bytes());v['extra_scientific_claim']='Unreviewed universal result';q.write_bytes(raw(v));self.f.rebind(q,'claim_map');self.assertRaises(ValueError,self.call)
 def test_rehashed_inventory_extra_science_field_hold(self):
  q=self.f.inventory_path;v=json.loads(q.read_bytes());v['extra_scientific_claim']='Unreviewed empirical validation';q.write_bytes(raw(v));self.f.rebind(q,'statement_inventory');self.assertRaises(ValueError,self.call)
 def test_wrong_draft_identity_hold(self):self.rule['draft_assessment']['final_pdf_sha256']='c'*64;self.assertRaises(ValueError,self.call)
 def test_forged_manifest_context_hold(self):self.f.manifest['statement_scope'][0]['ambient_source_context']=[{'line':1,'source_text':'variable (h : False)'}];self.f.commit();self.assertRaises(ValueError,self.call)

class PDFObservationTests(unittest.TestCase):
 def setUp(self):
  self.tex=b'Exact final TeX';self.pdf=b'%PDF-synthetic';self.o={'source_tex_sha256':d.digest(self.tex),'rendered_pdf_sha256':d.digest(self.pdf),'command':['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs','--outdir','/private/tmp/test','paper.tex'],'renderer_binary':{'invoked_path':'/opt/homebrew/bin/tectonic','resolved_path':'/pinned/tectonic','sha256':p.RENDERER_SHA},'cache_manifest':{'path':'/canonical/cache.json','sha256':p.RENDERER_CACHE_SHA,'bytes':42},'cache_file_count':556,'cache_and_binary_exact_after':True,'started_at_utc':'2020-01-01T00:00:00Z','ended_at_utc':'2020-01-01T00:01:00Z','returncode':0,'network_resource_fetch_disabled':True,'no_env_or_stdin_or_credentials_captured':True,'local_lean_execution':False}
 def check(self):return p.check_pdf_observation(self.o,self.tex,self.pdf)
 def test_exact_observation_pass_only_provenance(self):self.assertEqual(self.check()['status'],'SOURCE_BOUND_RENDER_OBSERVATION_MATCH_NOT_SEMANTIC_VERIFICATION')
 def test_rebound_stale_pdf_not_matching_renderer_hold(self):self.pdf+=b'changed';self.assertRaises(ValueError,self.check)
 def test_rebound_stale_source_hold(self):self.tex+=b'changed';self.assertRaises(ValueError,self.check)
 def test_foreign_executable_hold(self):self.o['command'][0]='/tmp/fake';self.assertRaises(ValueError,self.check)
 def test_non_cached_renderer_hold(self):self.o['command'][1]='--fetch';self.assertRaises(ValueError,self.check)
 def test_wrong_binary_hold(self):self.o['renderer_binary']['sha256']='a'*64;self.assertRaises(ValueError,self.check)
 def test_cache_change_hold(self):self.o['cache_and_binary_exact_after']=False;self.assertRaises(ValueError,self.check)
 def test_renderer_failure_hold(self):self.o['returncode']=1;self.assertRaises(ValueError,self.check)
 def test_future_renderer_hold(self):self.o['ended_at_utc']='2099-01-01T00:00:00Z';self.assertRaises(ValueError,self.check)
 def test_local_lean_mustfail(self):self.o['local_lean_execution']=True;self.assertRaises(ValueError,self.check)
 def test_undocumented_render_field_hold(self):self.o['verified']=True;self.assertRaises(ValueError,self.check)

class PublicationBindingTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.r=Path(self.t.name).resolve();self.note=self.r/'note';self.note.mkdir();self.authority={'path':str(self.r/'actual_authority.json'),'sha256':'a'*64};self.policy=self.note/'PHASE7_RULE_EXECUTION.json';self.policy.write_bytes(raw({'issued_at_utc':'2020-01-01T00:00:00Z','execution_consumer_sha256':d.sha(p.__file__)}));self.result={'run_id':'Run-125','identity':{'main_candidate_sha':'c'*64},'claim_reviews':[]};self.bp=self.note/'PUBLICATION_BINDING.json';self.v={'standard':p.BINDING_STANDARD,'status':'PUBLICATION_BOUND','run_id':'Run-125','authority':self.authority,'policy_receipt':p._binding(self.policy),'identity':self.result['identity'],'issued_at_utc':'2020-01-01T00:00:01Z','execution_consumer_sha256':d.sha(p.__file__)};self.bp.write_bytes(raw(self.v));self.q=patch.object(p,'evaluate_note',return_value=self.result);self.q.start();self.addCleanup(self.q.stop)
 def call(self):return p.require_note_publication_bound(self.note,self.r,self.authority)
 def change(self,k,v):self.v[k]=v;self.bp.write_bytes(raw(self.v))
 def test_fresh_exact_binding_pass(self):self.assertTrue(self.call()['exact_publication_binding'])
 def test_missing_binding_hold(self):self.bp.unlink();self.assertRaises(Exception,self.call)
 def test_wrong_run_hold(self):self.change('run_id','Run-126');self.assertRaises(ValueError,self.call)
 def test_wrong_main_identity_hold(self):self.change('identity',{'main_candidate_sha':'d'*64});self.assertRaises(ValueError,self.call)
 def test_foreign_authority_hold(self):self.change('authority',{'path':'/fake','sha256':'b'*64});self.assertRaises(ValueError,self.call)
 def test_policy_receipt_changed_hold(self):self.policy.write_bytes(raw({'issued_at_utc':'2020-01-01T00:00:00Z','changed':True}));self.assertRaises(ValueError,self.call)
 def test_future_publish_time_hold(self):self.change('issued_at_utc','2099-01-01T00:00:00Z');self.assertRaises(ValueError,self.call)
 def test_publish_precedes_rule_hold(self):self.change('issued_at_utc','2019-01-01T00:00:00Z');self.assertRaises(ValueError,self.call)
 def test_unclassified_binding_field_hold(self):self.change('reviewer',{'identity':'Codex self'});self.assertRaises(ValueError,self.call)
 def test_wrong_consumer_hold(self):self.change('execution_consumer_sha256','a'*64);self.assertRaises(ValueError,self.call)

if __name__=='__main__':unittest.main()
