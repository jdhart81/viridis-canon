"""Synthetic rule/admission regressions: no new verifier or production writes."""
from pathlib import Path
from copy import deepcopy
import tempfile,json,unittest
from unittest.mock import patch
import phase7_audit_policy as p
import phase7_claim_label_render as labels
import probe_observations as probes
import methods_digest as d
from test_phase7_audit_policy import FullAdmissionFixtureTests,raw
from test_methods_digest import Fixture as DigestFixture

class OptionalProbeTests(unittest.TestCase):
 def setUp(self):
  self.label='PHASE7_PROBE:Run-130:S01';self.source='#reduce (2, "'+self.label+'")\n';self.output='info: Challenge.lean:1:0: (2, "'+self.label+'")\ninfo: Solution.lean:1:0: (2, "'+self.label+'")'
 def test_all_resource_failure_classes_print_unclassified_nonblocking(self):
  for kind in sorted(probes.RESOURCE_FAILURES):
   with self.subTest(kind=kind):
    got=probes.optional_outcomes(self.output,self.source,self.source,[self.label],failure_kind=kind)[self.label]
    self.assertEqual(got['observed_label'],'UNCLASSIFIED');self.assertTrue(got['non_blocking']);self.assertFalse(got['certifies'])
 def test_successful_paired_ordinary_failures_are_substantive(self):self.assertEqual(probes.optional_outcomes(self.output,self.source,self.source,[self.label])[self.label]['observed_label'],'SUBSTANTIVE')
 def test_successful_downgrades_preserved(self):
  for code,name in ((0,'DEFINITIONAL'),(1,'ROUTINE')):
   with self.subTest(name=name):self.assertEqual(probes.optional_outcomes(self.output.replace('(2,',f'({code},'),self.source,self.source,[self.label])[self.label]['observed_label'],name)
 def test_missing_output_cannot_be_substantive(self):self.assertEqual(probes.optional_outcomes('',self.source,self.source,[self.label])[self.label]['observed_label'],'UNCLASSIFIED')
 def test_duplicate_marker_cannot_be_substantive(self):self.assertEqual(probes.optional_outcomes(self.output+'\n'+self.output,self.source,self.source,[self.label])[self.label]['observed_label'],'UNCLASSIFIED')
 def test_unknown_failure_kind_cannot_be_weaker_pass(self):self.assertRaises(ValueError,probes.optional_outcomes,self.output,self.source,self.source,[self.label],failure_kind='SUCCESS_DESPITE_FAILURE')
 def test_empty_labels_rejected(self):self.assertRaises(ValueError,probes.optional_outcomes,self.output,self.source,self.source,[])

class MinimalClaimRules(unittest.TestCase):
 def setUp(self):
  self.source='import Mathlib\nnamespace Example\ntheorem t (x : ℝ) (h : 0 < x) : 0 ≤ x := by linarith\nend Example\n';self.scope=[{'lean_theorem':'t','nonvacuity_obligation':None}];self.cert={'path':'/canonical/cert.json','sha256':'a'*64};self.inspection={'certified_theorems':['Example.t'],'nonvacuity':['Example.run_level_nonvacuous']}
 def call(self,run='Run-150'):return p.minimal_claim_reviews(run,self.source,self.scope,self.cert,self.inspection)[0]
 def test_missing_perclaim_witness_is_optional_but_honestly_printed(self):
  got=self.call();self.assertEqual(got['semantic_tier'],'DEPTH_NOT_ASSESSED');self.assertEqual(got['nonvacuity'],{'tier':'TIER1','status':'NOT_DEMONSTRATED'});self.assertIn('depth not yet assessed',labels.render_claim_table([got]))
 def test_run130_closed_probe_resource_hold_is_unclassified(self):
  got=self.call('Run-130');self.assertEqual(got['semantic_tier'],'UNCLASSIFIED');self.assertIn('UNCLASSIFIED (probe resource-limited)',labels.render_claim_table([got]))
 def test_runlevel_nonvacuity_is_still_required(self):self.inspection['nonvacuity']=[];self.assertRaises(ValueError,self.call)
 def test_claim_not_in_certificate_still_holds(self):self.inspection['certified_theorems']=[];self.assertRaises(ValueError,self.call)
 def test_assigned_main_witness_preserved(self):self.scope[0]['nonvacuity_obligation']='Example.run_level_nonvacuous';self.assertEqual(self.call()['nonvacuity']['certificate'],self.cert)
 def test_assigned_foreign_witness_holds(self):self.scope[0]['nonvacuity_obligation']='another_run';self.assertRaises(ValueError,self.call)
 def test_unsupported_optional_domain_is_not_a_publication_failure(self):
  with patch.object(p.tier0,'assess_candidate',side_effect=ValueError('unsupported optional domain')):self.assertEqual(self.call()['nonvacuity']['status'],'NOT_DEMONSTRATED')

class MinimalActualLayerTests(unittest.TestCase):
 def setUp(self):
  self.full=FullAdmissionFixtureTests();self.full.setUp();self.addCleanup(self.full.doCleanups);f=self.full;self.note=f.note;self.r=f.r
  f.rule['supplemental_manifest']=None;f.rule['supplemental_certificate']=None
  self.authority=patch.object(p,'require_minimal_authority',return_value={'synthetic':True});self.authority.start();self.addCleanup(self.authority.stop)
  reviews=p.minimal_claim_reviews('Run-141',f.f.candidate.read_text(),f.f.manifest['statement_scope'],f.f.manifest['certificate'],f.f.inspection);f.reviews=reviews
  tex=p.apply_review_labels(Path(f.source['path']).read_bytes(),reviews);f.f.tex.write_bytes(tex);f.f.rebind(f.f.tex)
  expected=p.expected_whole_paper_map(f.note,f.r,f.rule,f.auditmanifest,json.loads(Path(f.auditmanifest['path']).read_bytes()),Path(f.source['path']).read_bytes(),tex,f.f.pdf.read_bytes(),reviews,{})
  f.f.map_path.write_bytes(raw(expected));f.f.rebind(f.f.map_path,'claim_map')
  excluded={'SUPPLEMENTAL_WITNESS_CERTIFICATE.json','SUPPLEMENTAL_WITNESS_EVIDENCE.zip','SUPPLEMENTAL_WITNESS_MANIFEST.json'}
  f.f.manifest['uploads']=[v for v in f.f.manifest['uploads']if v['filename']not in excluded]
  for name in excluded:(f.note/name).unlink()
  (f.note/'CLAIM_CLASSIFICATIONS.json').write_bytes(raw({'run_id':'Run-141','claim_reviews':reviews,'status':'PROPOSAL_NOT_RULE_EXECUTION_RECEIPT','authority':f.authority,'source_statements_unchanged':True,'certifies':False}));f.f.rebind(f.note/'CLAIM_CLASSIFICATIONS.json');f.f.commit()
  result=p.evaluate_note(f.note,f.r,f.authority,rule=f.rule,inspector=f.f.inspector,_preparing=True);f.rule['inputs']=result['input_bindings'];f.rule['claim_reviews']=result['claim_reviews'];f.rule['draft_assessment']=result['identity'];f.policy.write_bytes(raw(f.rule))
 def test_missing_supplemental_files_does_not_block_fresh_minimal_admission(self):self.assertEqual(self.full.call()['status'],'APPROVED_RULES_APPLIED_NOT_PUBLICATION_BOUND')
 def test_source_changed_still_holds(self):f=self.full;f.f.tex.write_bytes(f.f.tex.read_bytes()+b'Unsupported theorem');f.f.rebind(f.f.tex);self.assertRaises(ValueError,f.call)
 def test_main_certificate_failure_still_holds(self):self.full.f.inspection['valid']=False;self.assertRaises(ValueError,self.full.call)
 def test_missing_disclaimer_still_holds(self):f=self.full;f.f.tex.write_bytes(f.f.tex.read_bytes().replace(d.DISCLAIMER.encode(),b''));f.f.rebind(f.f.tex);self.assertRaises(ValueError,f.call)
 def test_missing_binding_still_holds(self):self.assertRaises(Exception,p.require_note_publication_bound,self.note,self.r,self.full.authority)
 def test_claim_hypothesis_omission_still_holds(self):f=self.full;f.f.manifest['statement_scope'][0]['exact_source_signature']='theorem stronger : True';f.f.commit();self.assertRaises(ValueError,f.call)
 def test_main_runlevel_witness_contract_missing_still_holds(self):self.full.f.inspection['nonvacuity']=[];self.assertRaises(ValueError,self.full.call)
 def test_half_present_supplemental_evidence_rejected(self):f=self.full;f.rule['supplemental_manifest']=f.sm;self.assertRaises(ValueError,f.call)
 def test_forged_substantive_label_rejected(self):f=self.full;f.rule['claim_reviews'][0]['semantic_tier']='SUBSTANTIVE';self.assertRaises(ValueError,f.call)

class OptionalDigestLabels(unittest.TestCase):
 def setUp(self):self.f=DigestFixture();self.addCleanup(self.f.close)
 def test_unassessed_depth_keeps_note_publishable(self):
  self.f.records['Run-125']['claim_reviews'][0]['semantic_tier']='DEPTH_NOT_ASSESSED';self.f.records['Run-125']['claim_reviews'][0]['nonvacuity']={'tier':'TIER1','status':'NOT_DEMONSTRATED'};got=self.f.prepare();self.assertEqual(len(got['notes']),2);self.assertIn('depth not yet assessed',got['public_metadata']['description'])
 def test_resource_limited_probe_label_printed_without_blocking_digest(self):
  self.f.records['Run-125']['claim_reviews'][0]['semantic_tier']='UNCLASSIFIED';got=self.f.prepare();self.assertIn('UNCLASSIFIED (probe resource-limited)',got['public_metadata']['description']);self.assertIn('UNCLASSIFIED (probe resource-limited)',(self.f.out/'paper.tex').read_text())

if __name__=='__main__':unittest.main()

class ExactAppendedAuthorityTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.path=self.root/p.MINIMAL_AUTHORITY_REL;self.path.parent.mkdir(parents=True);self.plan=self.root/'reports/verification-coverage/GAME_PLAN.md';self.pins=[];sections=[];bodies=[]
  for name,header,pin in p.MINIMAL_SECTIONS:
   body=(header+'\nSynthetic offline rule fixture.\n\n').encode();(self.path.parent/name).write_bytes(body);h=d.digest(body);self.pins.append((name,header,h));sections.append({'path':name,'sha256':h});bodies.append(body.decode())
  self.plan.write_text('\n'.join(bodies));self.original=self.path.parent/'PRIOR.md';self.original.write_bytes(b'Synthetic prior approval');self.prior=d.digest(self.original.read_bytes());self.authority={'standard':'VRS-PHASE7-APPROVED-DECOUPLING-1','approved_by':'Justin','new_review_fabricated':False,'local_lean_execution':False,'captured_at_utc':'2020-01-01T00:00:00Z','original_audit_section':{'path':str(self.original),'sha256':self.prior},'sections':sections};self.path.write_bytes(raw(self.authority));self.q=patch.multiple(p,MINIMAL_AUTHORITY_SHA=d.sha(self.path),MINIMAL_SECTIONS=tuple(self.pins),PINS={**p.PINS,'audit_section':self.prior});self.q.start();self.addCleanup(self.q.stop)
 def call(self):return p.require_minimal_authority(self.root,{})
 def test_exact_section_pin_is_required(self):self.assertEqual(self.call()['approved_by'],'Justin')
 def test_changed_appended_instruction_holds(self):self.plan.write_text(self.plan.read_text().replace('Synthetic','Changed',1));self.assertRaises(ValueError,self.call)
 def test_future_capture_holds(self):self.authority['captured_at_utc']='2099-01-01T00:00:00Z';self.path.write_bytes(raw(self.authority));p.MINIMAL_AUTHORITY_SHA=d.sha(self.path);self.assertRaises(ValueError,self.call)
 def test_missing_section_holds(self):(self.path.parent/self.pins[0][0]).unlink();self.assertRaises(Exception,self.call)
 def test_original_audit_byte_changed_holds(self):self.original.write_bytes(b'Changed');self.assertRaises(ValueError,self.call)
 def test_duplicate_rule_section_holds(self):self.plan.write_text(self.plan.read_text()+self.pins[0][1]+'\nSynthetic offline rule fixture.\n\n');self.assertRaises(ValueError,self.call)
 def test_fabricated_review_holds(self):self.authority['new_review_fabricated']=True;self.path.write_bytes(raw(self.authority));p.MINIMAL_AUTHORITY_SHA=d.sha(self.path);self.assertRaises(ValueError,self.call)

class ApprovedDelimiterTests(unittest.TestCase):
 def setUp(self):
  from test_phase7_audit_policy import AuthorityTests
  self.f=AuthorityTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.plan=self.f.r/'GAME_PLAN.md'
 def test_exact_new_delimiter_requires_bound_new_authority(self):
  self.plan.write_bytes(self.plan.read_bytes().replace(b'\n## Future',b'\n---\n\n## Future'))
  with patch.object(p,'require_minimal_authority',return_value={'synthetic':True})as new:self.assertEqual(self.f.check()['status'],'APPROVED_RULE_AUTHORITY');self.assertEqual(new.call_count,1)
 def test_delimiter_without_approved_new_authority_holds(self):
  self.plan.write_bytes(self.plan.read_bytes().replace(b'\n## Future',b'\n---\n\n## Future'))
  with patch.object(p,'require_minimal_authority',side_effect=ValueError('missing new approval')):self.assertRaises(ValueError,self.f.check)
 def test_new_scientific_sentence_is_not_a_delimiter(self):
  self.plan.write_bytes(self.plan.read_bytes().replace(b'\n## Future',b'\nUnsupported stronger theorem.\n---\n\n## Future'))
  with patch.object(p,'require_minimal_authority',return_value={'synthetic':True}):self.assertRaises(ValueError,self.f.check)

class ActualMainAbstractOnlyTests(unittest.TestCase):
 def setUp(self):self.prior=b'\\documentclass{article}\n\\title{Historical Intelligence Bound}\n\\begin{document}\n\\begin{abstract}\nExact reviewed scope.\n\n\\end{abstract}\n\\section*{Main results}\nExact frozen theorem.\n\\section*{Claims excluded from formal scope}\n\\begin{verbatim}\n\\begin{abstract}\nUncertified historical claim.\n\\end{abstract}\n\\end{verbatim}\n\\end{document}\n'
 def test_quoted_historical_abstract_is_untouched(self):
  got=p.run147_approved_base(self.prior);self.assertEqual(got.count(p.SENTENCE147.encode()),1);self.assertEqual(got.split(b'\\section*{Claims excluded from formal scope}',1)[1],self.prior.split(b'\\section*{Claims excluded from formal scope}',1)[1]);self.assertIn(p.SENTENCE147.encode(),got.split(b'\\end{abstract}',1)[0])
 def test_duplicate_live_main_abstract_is_rejected(self):prior=self.prior.replace(b'\\section*{Main results}',b'\\begin{abstract}\nSecond active abstract.\n\\end{abstract}\n\\section*{Main results}');self.assertRaises(ValueError,p.run147_approved_base,prior)
 def test_missing_archive_boundary_rejected(self):self.assertRaises(ValueError,p.run147_approved_base,self.prior.replace(b'\\section*{Claims excluded from formal scope}',b''))
 def test_absent_live_abstract_is_rejected(self):self.assertRaises(ValueError,p.run147_approved_base,self.prior.replace(b'\\begin{abstract}',b'\\begin{wrong}',1))
 def test_transformed_map_rejects_additional_scientific_sentence(self):
  base=p.run147_approved_base(self.prior);reviews=[{'lean_theorem':'t','semantic_tier':'DEPTH_NOT_ASSESSED','nonvacuity':{'tier':'TIER1','status':'NOT_DEMONSTRATED'}}];wrong=base.replace(b'Exact frozen theorem.',b'Unconditional stronger theorem.');final=p.apply_review_labels(wrong,reviews);binding=lambda b:{'path':'/synthetic','sha256':d.digest(b)}
  self.assertRaises(ValueError,p.transformed_whole_paper_map,'Run-147',audit_manifest=binding(b'{}'),original_map_binding=binding(b'{}'),prior_tex_binding=binding(self.prior),base_tex_binding=binding(wrong),prior_tex=self.prior,base_tex=wrong,final_tex=final,final_pdf_binding=binding(b'%PDF-synthetic'),final_tex_binding=binding(final),statement_scope=[{'lean_theorem':'t'}],reviews=reviews)
