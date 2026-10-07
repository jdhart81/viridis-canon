"""Focused unit regression of the Phase7 draft gate; synthetic certificate authority only.

No certificate is issued or considered genuine: tests inject an inspector stub.
Frozen real Run141 source bytes exercise existing syntax/intake consumers. All
files are temporary; no canonical, Git, network, transport or publication writes.
"""
from pathlib import Path
from copy import deepcopy
import datetime as dt,hashlib,importlib.util,json,os,sys,tempfile,unittest
G=Path(__file__).resolve().parent
sys.path.insert(0,str(G))
TARGET=G/'scoped_release.py'
spec=importlib.util.spec_from_file_location('reviewed_scoped_release',TARGET);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import theorem_coverage as tc
from scoped_statement_text import inline_unicode_escape, signature_parts, binder_documentation
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def read(p):return json.loads(Path(p).read_bytes())

class Fixture:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.bundle=self.root/'release';self.bundle.mkdir();self.run_id='Run-141';self.now=dt.datetime(2026,10,6,23,0,tzinfo=dt.timezone.utc)
        self.stage=Path(__file__).resolve().parent/'fixtures/scoped_release';contract=read(self.stage/'CONTRACT.json')
        self.candidate=self.root/'CANDIDATE.lean';self.candidate.write_bytes((self.stage/'CANDIDATE.lean').read_bytes())
        self.formal=self.root/'STATEMENT.lean';self.formal.write_bytes((self.stage/'STATEMENT.lean').read_bytes())
        self.certificate=self.root/'SYNTHETIC_CERTIFICATE_FIXTURE.json';self.cert={'status':'SYNTHETIC_TEST_ONLY_NOT_VERIFIED','issued_at_utc':contract['issued_at_utc'],'run_id':self.run_id,'bindings':{'candidate_proof':{'path':str(self.candidate),'sha256':sha(self.candidate)},'formal_statement':{'path':str(self.formal),'sha256':sha(self.formal)}}};save(self.certificate,self.cert)
        self.inspection={'valid':True,'run_id':self.run_id,'candidate_path':str(self.candidate),'candidate_sha256':sha(self.candidate),'sha256':sha(self.certificate),'certified_theorems':contract['certified_theorems'],'nonvacuity':contract['nonvacuity']}
        self.tex=self.bundle/'paper.tex';self.tex.write_bytes((self.stage/'paper.tex').read_bytes());self.pdf=self.bundle/'paper.pdf';self.pdf.write_bytes(b'%PDF-1.4\nSYNTHETIC_UNRENDERED_TEST_FIXTURE_ONLY\n')
        self.mapping=read(self.stage/'claim_map.json');self.inventory=read(self.stage/'statement_inventory.json');self.basis=read(self.stage/'foundation_basis.json')
        self.map_path=self.bundle/'claim_map.json';self.inventory_path=self.bundle/'statement_inventory.json';self.basis_path=self.bundle/'foundation_basis.json'
        self.statements=[]
        for d,c in zip(self.inventory['declarations'],self.mapping['claims']):
            self.statements.append({**d,**c,'evidence_class':'FORMALLY_VERIFIED'})
        self.mapping['claims']=deepcopy(self.statements)
        save(self.map_path,self.mapping);save(self.inventory_path,self.inventory);save(self.basis_path,self.basis)
        self.raw_uploads=[]
        for src,name in ((self.certificate,'CERTIFICATE_UPLOAD.json'),(self.candidate,'CANDIDATE_UPLOAD.lean'),(self.formal,'STATEMENT_UPLOAD.lean')):
            p=self.bundle/name;p.write_bytes(src.read_bytes());self.raw_uploads.append((src,p))
        self.manifest_path=self.bundle/'SCOPED_RELEASE_MANIFEST.json';self.manifest={'standard':m.STANDARD,'scope':m.REVIEW_SCOPE,'run_id':self.run_id,'certificate':{'path':str(self.certificate),'sha256':sha(self.certificate)},'candidate':{'path':str(self.candidate),'sha256':sha(self.candidate)},'formal_statement':{'path':str(self.formal),'sha256':sha(self.formal)},'claim_map':self.local(self.map_path),'statement_inventory':self.local(self.inventory_path),'foundation_basis':self.local(self.basis_path),'uploads':[self.local(p)for p in(self.tex,self.pdf,self.map_path,self.inventory_path,self.basis_path,*[p for _,p in self.raw_uploads])],'final_tex_sha256':sha(self.tex),'final_pdf_sha256':sha(self.pdf),'statement_scope':deepcopy(self.statements)}
        self.commit()
    def local(self,p):return {'filename':Path(p).name,'sha256':sha(p)}
    def commit(self):save(self.manifest_path,self.manifest)
    def inspector(self,certificate,root):return deepcopy(self.inspection)
    def assess(self):return m.assess(self.bundle,self.root,inspector=self.inspector)
    def rebind(self,p,key=None):
        p=Path(p)
        if key:self.manifest[key]=self.local(p)
        for v in self.manifest['uploads']:
            if v['filename']==p.name:v['sha256']=sha(p)
        if p==self.tex:self.manifest['final_tex_sha256']=sha(p)
        if p==self.pdf:self.manifest['final_pdf_sha256']=sha(p)
        self.commit()
    def review(self,changes=None):
        current=self.assess()
        if current['status']!='DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND':raise AssertionError('fixture baseline HOLD '+str(current['reasons']))
        o={k:deepcopy(current[k])for k in('manifest_sha256','certificate','candidate','formal_statement','claim_map_sha256','statement_inventory_sha256','foundation_basis_sha256','uploads','final_tex_sha256','final_pdf_sha256','statement_scope','foundation_basis','inv9_projection_sha256','archival_exclusion_review_required')}
        o.update(standard=m.REVIEW_STANDARD,scope=m.REVIEW_SCOPE,status='APPROVED',reviewer={'identity':'Claude independent fixture reviewer','model':'claude-opus-synthetic-test-only'},reviewed_at_utc='2026-10-06T22:00:00+00:00',checks={k:True for k in m.REVIEW_CHECKS})
        if changes:o.update(changes)
        p=self.bundle/'SCOPED_RELEASE_REVIEW.json';save(p,o);return p,o
    def validate_review(self,p,approved=None):return m.validate_review(self.bundle,self.root,[sha(p)]if approved is None else approved,inspector=self.inspector,now=self.now)
    def close(self):self.tmp.cleanup()
    def sync_raw_uploads(self):
        for source,path in self.raw_uploads:
            path.write_bytes(source.read_bytes());self.rebind(path)

class FocusedTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def hold(self):self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_baseline_draft_is_only_draft_never_publication(self):
        r=self.f.assess();self.assertEqual(r['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND');self.assertFalse(r['certifies']);self.assertFalse(r['zenodo_writes'])
        with self.assertRaises(ValueError):m.require_publication_bound(r)
    def test_exact_independent_fixture_review_requires_binding(self):
        p,_=self.f.review();r=self.f.validate_review(p);self.assertEqual(r['status'],'AUDITED_SCOPE_READY_FOR_PUBLICATION_TIME_BINDING');self.assertFalse(r['publication_authorized'])
        with self.assertRaises(ValueError):m.require_publication_bound(r)
    def test_manifest_hypothesis_drop(self):
        self.f.manifest['statement_scope'][0]['exact_source_signature']=self.f.manifest['statement_scope'][0]['exact_source_signature'].replace('(hr : r = slowRate a b k)','');self.f.commit();self.hold()
    def test_manifest_context_drop(self):
        self.f.manifest['statement_scope'][0]['ambient_source_context']=[{'line':1,'source_text':'invented'}];self.f.commit();self.hold()
    def test_wrong_run(self):self.f.manifest['run_id']='Run-140';self.f.commit();self.hold()
    def test_rejected_certificate(self):self.f.inspection['valid']=False;self.hold()
    def test_wrong_candidate_identity(self):self.f.manifest['candidate']['sha256']='0'*64;self.f.commit();self.hold()
    def test_wrong_formal_identity(self):self.f.manifest['formal_statement']['sha256']='0'*64;self.f.commit();self.hold()
    def test_stale_certificate_sha(self):self.f.manifest['certificate']['sha256']='0'*64;self.f.commit();self.hold()
    def test_stale_pdf_upload_sha(self):self.f.pdf.write_bytes(self.f.pdf.read_bytes()+b'changed');self.hold()
    def test_stale_final_pdf_sha(self):self.f.manifest['final_pdf_sha256']='0'*64;self.f.commit();self.hold()
    def test_stale_final_tex_sha(self):self.f.manifest['final_tex_sha256']='0'*64;self.f.commit();self.hold()
    def test_missing_pdf(self):self.f.pdf.unlink();self.hold()
    def test_duplicate_upload(self):self.f.manifest['uploads'].append(deepcopy(self.f.manifest['uploads'][0]));self.f.commit();self.hold()
    def test_missing_disclaimer(self):self.f.tex.write_text(self.f.tex.read_text().replace(m.DISCLAIMER,''));self.f.rebind(self.f.tex);self.hold()
    def test_empirical_symbols(self):self.f.manifest['statement_scope'][0]['model_fidelity']['empirically_identified']=['measured real rate'];self.f.commit();self.hold()
    def test_duplicate_theorem(self):self.f.manifest['statement_scope'].append(deepcopy(self.f.manifest['statement_scope'][0]));self.f.commit();self.hold()
    def test_foreign_witness(self):self.f.manifest['statement_scope'][0]['nonvacuity_obligation']='other_run_witness';self.f.commit();self.hold()
    def test_trivial_formal_evidence(self):
        name=self.f.manifest['statement_scope'][0]['lean_theorem'];coverage=m.triviality(self.f.candidate.read_text());coverage[name]['classification']='CERTIFIED_TRIVIAL'
        from unittest.mock import patch
        with patch.object(m,'triviality',return_value=coverage):self.hold()
    def test_unresolved_triviality(self):
        name=self.f.manifest['statement_scope'][0]['lean_theorem'];coverage=m.triviality(self.f.candidate.read_text());coverage[name]['classification']='TRIVIALITY_UNRESOLVED'
        from unittest.mock import patch
        with patch.object(m,'triviality',return_value=coverage):self.hold()
    def test_future_review(self):
        p,_=self.f.review({'reviewed_at_utc':'2027-01-01T00:00:00+00:00'})
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_review_before_certificate(self):
        p,_=self.f.review({'reviewed_at_utc':'2026-01-01T00:00:00+00:00'})
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_review_missing_timezone(self):
        p,_=self.f.review({'reviewed_at_utc':'2026-10-06T22:00:00'})
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_review_not_approved_in_ledger(self):
        p,_=self.f.review()
        with self.assertRaises(ValueError):self.f.validate_review(p,[])
    def test_review_changed_after_approval(self):
        p,o=self.f.review();old=sha(p);o['reviewer']['identity']='different';save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p,[old])
    def test_codex_self_review(self):
        p,_=self.f.review({'reviewer':{'identity':'Codex','model':'gpt-6'}})
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_review_missing_required_check(self):
        p,o=self.f.review();o['checks']['no_statement_stronger_than_certified']=False;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_review_wrong_final_pdf_identity(self):
        p,o=self.f.review();o['final_pdf_sha256']='0'*64;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_no_binding_prewrite(self):
        with self.assertRaises(ValueError):m.require_publication_bound({'status':'AUDITED_SCOPE_READY_FOR_PUBLICATION_TIME_BINDING','exact_publication_binding':False})
    def test_source_product_not_erased_by_projection(self):
        marker='\nnoncomputable def product_form_fixture : ℝ := 1\n';self.f.candidate.write_text(self.f.candidate.read_text()+marker);self.f.formal.write_text(self.f.formal.read_text()+marker)
        self.f.cert['bindings']['candidate_proof']['sha256']=sha(self.f.candidate);self.f.cert['bindings']['formal_statement']['sha256']=sha(self.f.formal);save(self.f.certificate,self.f.cert)
        self.f.inspection['candidate_sha256']=sha(self.f.candidate);self.f.inspection['sha256']=sha(self.f.certificate)
        self.f.manifest['certificate']['sha256']=sha(self.f.certificate);self.f.manifest['candidate']['sha256']=sha(self.f.candidate);self.f.manifest['formal_statement']['sha256']=sha(self.f.formal)
        p=self.f.bundle/'inv9_projection.json';save(p,{'final_tex_sha256':sha(self.f.tex),'rule':'AUDITED_UNCERTIFIED_ARCHIVE_EXCLUSION','paper_text':r'\begin{abstract}INDEPENDENT mathematical scope.\end{abstract}'})
        self.f.manifest['inv9_projection']=self.f.local(p);self.f.commit();self.hold()
    # Must-fail adversarial inputs exposing structural gaps in the initial draft.
    def test_forged_binding_boolean_cannot_authorize_write(self):
        with self.assertRaises(ValueError):m.require_publication_bound({'status':'PUBLICATION_BOUND','exact_publication_binding':True})
    def test_gpt_self_alias_is_not_claude_review(self):
        p,_=self.f.review({'reviewer':{'identity':'implementation-agent','model':'gpt-6'}})
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_missing_english_claim(self):
        del self.f.manifest['statement_scope'][0]['english_claim'];self.f.commit();self.hold()
    def test_duplicate_english_claim(self):
        self.f.manifest['statement_scope'][1]['english_claim']=self.f.manifest['statement_scope'][0]['english_claim'];self.f.commit();self.hold()
    def test_claim_map_wrong_run(self):
        self.f.mapping['run_id']='Run-126';save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_claim_map_stronger_english_than_manifest(self):
        self.f.mapping['claims'][0]['english_claim']='This is the measured smaller eigenvalue with no assumptions.';save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_statement_inventory_hypothesis_drop(self):
        self.f.inventory['declarations'][0]['exact_source_signature']=self.f.inventory['declarations'][0]['exact_source_signature'].replace('(ha : 0 < a)','');save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_statement_inventory_not_json(self):
        self.f.inventory_path.write_text('not JSON');self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_claim_map_missing_scoped_claim(self):
        self.f.mapping['claims'].pop();save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_paper_printed_hypothesis_omission(self):
        self.f.tex.write_text(self.f.tex.read_text().replace('(hr : r = slowRate a b k)','',1));self.f.rebind(self.f.tex);self.hold()


class ExtendedTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def hold(self):self.assertEqual(self.f.assess()['status'],'HOLD')
    def null_witness(self):
        for c in self.f.manifest['statement_scope']:c['nonvacuity_obligation']=None
        for c in self.f.mapping['claims']:c['nonvacuity_obligation']=None
        save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map')
    def assignments(self):
        return {c['lean_theorem']:self.f.inspection['nonvacuity'][0] for c in self.f.manifest['statement_scope']}
    def review_with_assignments(self,assignments=None):
        assignments=self.assignments() if assignments is None else assignments
        current=m.assess(self.f.bundle,self.f.root,inspector=self.f.inspector,reviewed_witness_assignments=assignments)
        self.assertEqual(current['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND',current['reasons'])
        keys=('manifest_sha256','certificate','candidate','formal_statement','claim_map_sha256','statement_inventory_sha256','foundation_basis_sha256','uploads','final_tex_sha256','final_pdf_sha256','statement_scope','foundation_basis','inv9_projection_sha256','archival_exclusion_review_required')
        review={k:deepcopy(current[k])for k in keys}
        review.update(standard=m.REVIEW_STANDARD,scope=m.REVIEW_SCOPE,status='APPROVED',reviewer={'identity':'Claude independent synthetic fixture','model':'claude-opus-synthetic-test-only'},reviewed_at_utc='2026-10-06T22:00:00+00:00',checks={k:True for k in m.REVIEW_CHECKS},nonvacuity_assignments=assignments)
        p=self.f.bundle/'SCOPED_RELEASE_REVIEW.json';save(p,review);return p,review
    def binding(self):
        p,_=self.f.review();current=self.f.validate_review(p)
        keys=('manifest_sha256','certificate','candidate','formal_statement','claim_map_sha256','statement_inventory_sha256','foundation_basis_sha256','uploads','final_tex_sha256','final_pdf_sha256','statement_scope','foundation_basis','review')
        o={k:deepcopy(current[k])for k in keys};o.update(standard='VRS-SCOPED-PUBLICATION-BINDING-1',status='PUBLICATION_BOUND',issued_at_utc='2026-10-06T22:30:00+00:00')
        bp=self.f.bundle/'PUBLICATION_BINDING.json';save(bp,o);return p,bp,o
    def bound(self,p):return m.require_publication_bound(self.f.bundle,self.f.root,[sha(p)],inspector=self.f.inspector,now=self.f.now)
    def test_null_witness_no_review_hold(self):self.null_witness();self.hold()
    def test_null_witness_review_approved_exact_assignment_pass(self):
        self.null_witness();p,_=self.review_with_assignments();self.assertEqual(self.f.validate_review(p)['status'],'AUDITED_SCOPE_READY_FOR_PUBLICATION_TIME_BINDING');self.hold()
    def test_null_witness_missing_assignment_hold(self):
        self.null_witness();p,o=self.review_with_assignments();o['nonvacuity_assignments'].pop(next(iter(o['nonvacuity_assignments'])));save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_null_witness_invented_assignment_hold(self):
        self.null_witness();p,o=self.review_with_assignments();o['nonvacuity_assignments'][next(iter(o['nonvacuity_assignments']))]='invented_not_in_certificate';save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_null_witness_multiple_names_hold(self):
        self.null_witness();p,o=self.review_with_assignments();o['nonvacuity_assignments'][next(iter(o['nonvacuity_assignments']))]=[self.f.inspection['nonvacuity'][0]]*2;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_null_witness_unapproved_assignment_hold(self):
        self.null_witness();p,o=self.review_with_assignments()
        with self.assertRaises(ValueError):self.f.validate_review(p,[])
    def test_null_witness_unreviewed_semantics_hold(self):
        self.null_witness();p,o=self.review_with_assignments();o['checks']['nonvacuity_correspondence_reviewed']=False;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_claim_map_foreign_witness_conflict_hold(self):
        self.f.mapping['claims'][0]['nonvacuity_obligation']='foreign_not_certified';save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_claim_map_empirical_fidelity_conflict_hold(self):
        self.f.mapping['claims'][0]['model_fidelity']['empirically_identified']=['physically measured rate'];save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_claim_map_evidence_class_conflict_hold(self):
        self.f.mapping['claims'][0]['evidence_class']='UNREVIEWED';save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map');self.hold()
    def test_inventory_ambient_context_conflict_hold(self):
        self.f.inventory['declarations'][0]['ambient_source_context']=[{'line':1,'source_text':'variable (h_false : False)'}];save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_inventory_binders_conflict_hold(self):
        self.f.inventory['declarations'][0]['explicit_binders_and_hypotheses']='(a b k r : ℝ)';save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_inventory_conclusion_conflict_hold(self):
        self.f.inventory['declarations'][0]['conclusion']='r = 0';save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_inventory_foreign_witness_conflict_hold(self):
        self.f.inventory['declarations'][0]['nonvacuity_obligation']='invented_not_certified';save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_inventory_unsupported_extra_theorem_hold(self):
        d=deepcopy(self.f.inventory['declarations'][0]);d['lean_theorem']='invented_not_certified';self.f.inventory['declarations'].append(d);save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_inspection_candidate_snapshot_mismatch_hold(self):
        anticipated=self.f.candidate.read_bytes()+b'\n';import hashlib
        self.f.manifest['candidate']['sha256']=hashlib.sha256(anticipated).hexdigest();self.f.commit()
        def mutate_inspector(c,r):
            out=self.f.inspector(c,r);self.f.candidate.write_bytes(anticipated);return out
        self.assertEqual(m.assess(self.f.bundle,self.f.root,inspector=mutate_inspector)['status'],'HOLD')
    def test_inspection_certificate_snapshot_mismatch_hold(self):
        def mutate_inspector(c,r):
            out=self.f.inspector(c,r);v=read(c);v['post_inspection_ignored_field']='changed bytes';save(c,v);return out
        self.assertEqual(m.assess(self.f.bundle,self.f.root,inspector=mutate_inspector)['status'],'HOLD')
    def test_exact_binding_fixture_pass(self):
        p,bp,o=self.binding();r=self.bound(p);self.assertEqual(r['status'],'PUBLICATION_BOUND');self.assertFalse(r['certifies']);self.assertFalse(r['zenodo_writes'])
    def test_exact_binding_missing_file_hold(self):
        p,bp,o=self.binding();bp.unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):self.bound(p)
    def test_exact_binding_wrong_review_hold(self):
        p,bp,o=self.binding();o['review']['sha256']='0'*64;save(bp,o)
        with self.assertRaises(ValueError):self.bound(p)
    def test_exact_binding_stale_pdf_hold(self):
        p,bp,o=self.binding();self.f.pdf.write_bytes(self.f.pdf.read_bytes()+b'changed')
        with self.assertRaises(ValueError):self.bound(p)
    def test_exact_binding_future_hold(self):
        p,bp,o=self.binding();o['issued_at_utc']='2027-01-01T00:00:00+00:00';save(bp,o)
        with self.assertRaises(ValueError):self.bound(p)
    def test_exact_binding_before_review_hold(self):
        p,bp,o=self.binding();o['issued_at_utc']='2026-10-06T21:00:00+00:00';save(bp,o)
        with self.assertRaises(ValueError):self.bound(p)
    def test_exact_binding_draft_status_hold(self):
        p,bp,o=self.binding();o['status']='READY';save(bp,o)
        with self.assertRaises(ValueError):self.bound(p)

class ContextAndUploadTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def hold(self):self.assertEqual(self.f.assess()['status'],'HOLD')
    def context_fixture(self):
        marker='variable (h_ambient : 0 < (1 : ℝ))\n\n'
        for p in (self.f.candidate,self.f.formal):p.write_text(p.read_text().replace('theorem slow_rate_characterization',marker+'theorem slow_rate_characterization',1))
        self.f.cert['bindings']['candidate_proof']['sha256']=sha(self.f.candidate);self.f.cert['bindings']['formal_statement']['sha256']=sha(self.f.formal);save(self.f.certificate,self.f.cert)
        self.f.inspection['candidate_sha256']=sha(self.f.candidate);self.f.inspection['sha256']=sha(self.f.certificate)
        self.f.manifest['certificate']['sha256']=sha(self.f.certificate);self.f.manifest['candidate']['sha256']=sha(self.f.candidate);self.f.manifest['formal_statement']['sha256']=sha(self.f.formal)
        coverage=m.triviality(self.f.candidate.read_text())
        for c in self.f.manifest['statement_scope']:c['ambient_source_context']=m.ambient_context(self.f.candidate.read_text(),coverage[c['lean_theorem']]['line'])
        for c in self.f.inventory['declarations']:c['ambient_source_context']=m.ambient_context(self.f.candidate.read_text(),coverage[c['lean_theorem']]['line'])
        save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory')
        context=self.f.manifest['statement_scope'][0]['ambient_source_context'][0]['source_text']
        self.f.tex.write_text(self.f.tex.read_text()+'\n\\begin{verbatim}\n'+inline_unicode_escape(context)+'\n\\end{verbatim}\n');self.f.rebind(self.f.tex);self.f.sync_raw_uploads();self.f.commit();return context
    def context_display(self):
        import science_release_stage
        p=self.f.bundle/'FROZEN_CONTEXT.txt';p.write_text(science_release_stage.ascii_render(self.f.formal.read_text()))
        self.f.tex.write_text(self.f.tex.read_text()+'\n\\VerbatimInput{FROZEN_CONTEXT.txt}\n');self.f.rebind(self.f.tex)
        for c in self.f.manifest['statement_scope']:c['context_display_file']={'relative_path':p.name,'sha256':sha(p)}
        self.f.commit();return p
    def test_inline_ambient_context_visible_pass(self):
        self.context_fixture();self.assertEqual(self.f.assess()['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND')
    def test_inline_ambient_context_dropped_hold(self):
        context=self.context_fixture();self.f.tex.write_text(self.f.tex.read_text().replace(inline_unicode_escape(context),''));self.f.rebind(self.f.tex);self.hold()
    def test_inline_ambient_context_edited_hold(self):
        context=self.context_fixture();self.f.tex.write_text(self.f.tex.read_text().replace(inline_unicode_escape(context),'variable (h_ambient : True)'));self.f.rebind(self.f.tex);self.hold()
    def test_bound_full_context_display_pass_existing_render(self):
        context=self.context_fixture();self.f.tex.write_text(self.f.tex.read_text().replace(inline_unicode_escape(context),''));self.f.rebind(self.f.tex);self.context_display();self.assertEqual(self.f.assess()['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND')
    def test_bound_full_context_wrong_recomputed_render_hold(self):
        self.context_fixture();p=self.context_display();p.write_text(p.read_text().replace('variable (h_ambient : 0 < (1 : Real))','variable (h_ambient : True)'))
        for c in self.f.manifest['statement_scope']:c['context_display_file']['sha256']=sha(p)
        self.f.commit();self.hold()
    def test_bound_full_context_missing_include_hold(self):
        self.context_fixture();self.context_display();self.f.tex.write_text(self.f.tex.read_text().replace('\\VerbatimInput{FROZEN_CONTEXT.txt}',''));self.f.rebind(self.f.tex);self.hold()
    def test_bound_full_context_stale_hash_hold(self):
        self.context_fixture();p=self.context_display();p.write_bytes(p.read_bytes()+b'changed');self.hold()
    def test_dropped_candidate_upload_hold(self):
        self.f.manifest['uploads']=[v for v in self.f.manifest['uploads']if v['filename']!='CANDIDATE_UPLOAD.lean'];self.f.commit();self.hold()
    def test_dropped_statement_upload_hold(self):
        self.f.manifest['uploads']=[v for v in self.f.manifest['uploads']if v['filename']!='STATEMENT_UPLOAD.lean'];self.f.commit();self.hold()
    def test_dropped_certificate_upload_hold(self):
        self.f.manifest['uploads']=[v for v in self.f.manifest['uploads']if v['filename']!='CERTIFICATE_UPLOAD.json'];self.f.commit();self.hold()
    def test_corrupt_candidate_upload_rebound_hold(self):
        p=self.f.bundle/'CANDIDATE_UPLOAD.lean';p.write_bytes(p.read_bytes()+b'\nchanged');self.f.rebind(p);self.hold()
    def test_corrupt_statement_upload_rebound_hold(self):
        p=self.f.bundle/'STATEMENT_UPLOAD.lean';p.write_bytes(p.read_bytes()+b'\nchanged');self.f.rebind(p);self.hold()
    def test_corrupt_certificate_upload_rebound_hold(self):
        p=self.f.bundle/'CERTIFICATE_UPLOAD.json';p.write_bytes(p.read_bytes()+b'\nchanged');self.f.rebind(p);self.hold()
    def test_no_raw_uploads_hold(self):
        self.f.manifest['uploads']=[v for v in self.f.manifest['uploads']if 'UPLOAD'not in v['filename']];self.f.commit();self.hold()
    def test_unicode_escaping_nonbmp_and_literal_escape_are_distinct(self):
        self.assertEqual(inline_unicode_escape('𝒢'),r'\U0001d4a2');self.assertNotEqual(inline_unicode_escape('ℝ'),inline_unicode_escape(r'\u211d'))
    def test_signature_parser_preserves_nested_colons_and_binders(self):
        s='theorem foo {Ω : Type*} (f : Ω → ℝ) (h : ∀ x, 0 ≤ f x) : ∃ x, f x = 0'
        a,c=signature_parts(s);self.assertEqual(a,'{Ω : Type*} (f : Ω → ℝ) (h : ∀ x, 0 ≤ f x)');self.assertEqual(c,'∃ x, f x = 0');self.assertEqual(binder_documentation(s)['conclusion_utf8'],c)
    def mutation_after_inv9(self,path):
        from unittest.mock import patch
        import premise_declaration
        original=premise_declaration.evaluate
        def mutate(*a,**k):
            result=original(*a,**k);path.write_bytes(path.read_bytes()+b'\n');return result
        with patch.object(premise_declaration,'evaluate',side_effect=mutate):
            r=self.f.assess();self.assertEqual(r['status'],'HOLD');self.assertTrue(any('evidence changed during assessment' in x for x in r['reasons']),r)
    def test_candidate_changed_after_inv9_hold(self):self.mutation_after_inv9(self.f.candidate)
    def test_certificate_changed_after_inv9_hold(self):self.mutation_after_inv9(self.f.certificate)
    def test_formal_changed_after_inv9_hold(self):self.mutation_after_inv9(self.f.formal)
    def test_pdf_changed_after_inv9_hold(self):self.mutation_after_inv9(self.f.pdf)
    def test_claim_map_changed_after_inv9_hold(self):self.mutation_after_inv9(self.f.map_path)
    def test_source_product_bypass_still_hold_after_exact_proof_uploads(self):
        marker='\nnoncomputable def product_form_fixture : ℝ := 1\n'
        self.f.candidate.write_text(self.f.candidate.read_text()+marker);self.f.formal.write_text(self.f.formal.read_text()+marker)
        self.f.cert['bindings']['candidate_proof']['sha256']=sha(self.f.candidate);self.f.cert['bindings']['formal_statement']['sha256']=sha(self.f.formal);save(self.f.certificate,self.f.cert)
        self.f.inspection['candidate_sha256']=sha(self.f.candidate);self.f.inspection['sha256']=sha(self.f.certificate)
        self.f.manifest['certificate']['sha256']=sha(self.f.certificate);self.f.manifest['candidate']['sha256']=sha(self.f.candidate);self.f.manifest['formal_statement']['sha256']=sha(self.f.formal)
        p=self.f.bundle/'inv9_projection.json';save(p,{'final_tex_sha256':sha(self.f.tex),'rule':'AUDITED_UNCERTIFIED_ARCHIVE_EXCLUSION','paper_text':r'\begin{abstract}INDEPENDENT mathematical scope.\end{abstract}'})
        self.f.manifest['inv9_projection']=self.f.local(p);self.f.sync_raw_uploads();self.f.commit();r=self.f.assess();self.assertEqual(r['status'],'HOLD');self.assertTrue(any('INV-9' in x for x in r['reasons']),r)

class ClosedAssignmentTests(ExtendedTests):
    # Do not inherit old cases twice: only these new explicit test definitions
    # are enumerated by load_tests below.
    def test_unknown_assignment_target_hold(self):
        self.null_witness();p,o=self.review_with_assignments();o['nonvacuity_assignments']['invented_target']='symbiotic_equalization_nonvacuous';save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_missing_map_witness_field_hold(self):
        self.null_witness();self.f.mapping['claims'][0].pop('nonvacuity_obligation');save(self.f.map_path,self.f.mapping);self.f.rebind(self.f.map_path,'claim_map')
        self.hold()
    def test_missing_inventory_witness_field_hold(self):
        self.f.inventory['declarations'][0].pop('nonvacuity_obligation');save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold()
    def test_review_changed_during_assessment_hold(self):
        p,o=self.f.review();approved=sha(p)
        def change_review(c,r):
            result=self.f.inspector(c,r);p.write_bytes(p.read_bytes()+b'\n');return result
        with self.assertRaises(ValueError):m.validate_review(self.f.bundle,self.f.root,[approved],inspector=change_review,now=self.f.now)


def load_tests(loader, tests, pattern):
    suite=unittest.TestSuite()
    for cls in (FocusedTests, ExtendedTests, ContextAndUploadTests):suite.addTests(loader.loadTestsFromTestCase(cls))
    for name in sorted(ClosedAssignmentTests.__dict__):
        if name.startswith('test_'):suite.addTest(ClosedAssignmentTests(name))
    return suite

class PublicScopeEvidenceTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def omit(self,key):
        name=self.f.manifest[key]['filename'];self.f.manifest['uploads']=[u for u in self.f.manifest['uploads']if u['filename']!=name];self.f.commit();self.assertEqual(self.f.assess()['status'],'HOLD')
    def metadata(self,name='zenodo_metadata.json',upload=True):
        p=self.f.bundle/name;save(p,{'title':'Exact original title','description':'Historical vector and empirical claims','abstract':'Historical abstract','keywords':['historical']})
        if upload:self.f.manifest['uploads'].append(self.f.local(p))
        self.f.commit();return p
    def test_missing_public_claim_map_holds(self):self.omit('claim_map')
    def test_missing_public_statement_inventory_holds(self):self.omit('statement_inventory')
    def test_missing_public_foundation_basis_holds(self):self.omit('foundation_basis')
    def test_claim_map_upload_hash_mutation_holds(self):
        self.f.map_path.write_bytes(self.f.map_path.read_bytes()+b' ');self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_statement_inventory_upload_hash_mutation_holds(self):
        self.f.inventory_path.write_bytes(self.f.inventory_path.read_bytes()+b' ');self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_foundation_basis_upload_hash_mutation_holds(self):
        self.f.basis_path.write_bytes(self.f.basis_path.read_bytes()+b' ');self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_equal_byte_alias_is_not_exact_evidence_filename(self):
        src=self.f.map_path;other=self.f.bundle/'alias.json';other.write_bytes(src.read_bytes());self.f.manifest['uploads']=[u for u in self.f.manifest['uploads']if u['filename']!=src.name];self.f.manifest['uploads'].append(self.f.local(other));self.f.commit();self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_bound_public_metadata_passes_only_pending_review(self):
        p=self.metadata();r=self.f.assess();self.assertEqual(r['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND');self.assertEqual(r['metadata_binding'],self.f.local(p));review,_=self.f.review();ready=self.f.validate_review(review);self.assertTrue(ready['metadata_claim_completeness']);self.assertFalse(ready['publication_authorized'])
    def test_bound_generic_metadata_filename_passes(self):
        p=self.metadata('metadata.json');self.assertEqual(self.f.assess()['metadata_binding'],self.f.local(p))
    def test_added_unbound_metadata_holds(self):self.metadata(upload=False);self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_metadata_changed_after_binding_holds(self):
        p=self.metadata();p.write_bytes(p.read_bytes()+b' ');self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_both_metadata_filenames_holds(self):self.metadata();self.metadata('metadata.json');self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_metadata_symlink_holds(self):
        p=self.metadata();p.unlink();p.symlink_to(self.f.map_path);self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_missing_bound_metadata_holds(self):self.metadata().unlink();self.assertEqual(self.f.assess()['status'],'HOLD')
    def test_metadata_review_completeness_false_holds(self):
        self.metadata();p,o=self.f.review();o['checks']['metadata_claim_completeness']=False;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_metadata_review_completeness_missing_holds(self):
        self.metadata();p,o=self.f.review();o['checks'].pop('metadata_claim_completeness');save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_broader_metadata_without_independent_review_holds(self):
        self.metadata();p,o=self.f.review();o['checks']['metadata_claim_completeness']=False;save(p,o)
        with self.assertRaises(ValueError):self.f.validate_review(p)
    def test_metadata_mutation_after_approved_review_holds(self):
        p=self.metadata();review,_=self.f.review();approved=[sha(review)];save(p,{'title':'Exact original title','description':'Stronger new empirical claim'})
        with self.assertRaises(ValueError):self.f.validate_review(review,approved)
    def test_freshly_rebound_metadata_still_invalidates_old_review_identity(self):
        p=self.metadata();review,_=self.f.review();save(p,{'title':'Exact original title','description':'Changed public claims'});self.f.rebind(p)
        with self.assertRaises(ValueError):self.f.validate_review(review)

if __name__=='__main__':
    print('SYNTHETIC_UNIT_TEST_ONLY',str(TARGET),'SHA256',sha(TARGET))
    unittest.main(verbosity=2)
