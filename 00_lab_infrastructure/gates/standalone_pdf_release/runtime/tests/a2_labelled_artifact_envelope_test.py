"""Genuine frozen predecessor over explicit synthetic trust DATA, no Core use.

These are artifact/source-contract tests, not real renderer or live admission
proof. The complete 20+1/130 source session is covered separately by the full
normal and negative route fixture. No predecessor/PB result is mocked here.
"""
from copy import deepcopy
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
sys.path.insert(1,str(HERE.parents[2]))  # copied public gates, required by isolated output-unit cases
from w42_portable_fixture import PortableFixture,pdf
import nightly_manuscript_access as access
import methods_digest_v2 as digest


class LabelledArtifactEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='labelled-artifact-');self.addCleanup(self.temp.cleanup)
        self.f=PortableFixture(self.temp.name)
        self.scope=self.f.context();self.scope.__enter__();self.addCleanup(self.scope.__exit__,None,None,None)
        self.base=self.f.base_note();self.before={str(p.relative_to(self.base)):p.read_bytes()for p in self.base.rglob('*')if p.is_file()}
        self.out=self.f.root/'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access/labelled'
        self.staged=access.prepare_labelled(self.f.root,self.base,self.out,self.f.authority)
    def read(self,p):return json.loads(Path(p).read_bytes())
    def change(self,p,fn):
        value=self.read(p);fn(value);Path(p).write_bytes(digest.raw_json(value))
    def review(self):return access.review_labelled(self.f.root,self.out,self.f.authority,review_invocation='TEST_ONLY_LATER_ARTIFACT_REVIEW')
    def require(self):return access.require_labelled(self.out,self.f.root,self.f.authority)
    def admitted(self):
        self.review();return self.read(self.out/'SCOPED_RELEASE_MANIFEST.json')
    def hold(self,pattern):
        with self.assertRaisesRegex((ValueError,OSError),pattern):self.require()
    def test_preparation_has_no_artifact_binding_and_later_review_is_distinct(self):
        self.assertEqual(self.staged['status'],'LABELLED_ARTIFACT_STAGED_REVIEW_REQUIRED')
        self.assertFalse((self.out/'PUBLICATION_BINDING.json').exists())
        current=self.review();self.assertTrue(current['exact_publication_binding'])
        self.assertFalse(current['certifies']);self.assertFalse(current['publication_authorized'])
        self.assertNotEqual((self.out/'PUBLICATION_BINDING.json').read_bytes(),(self.base/'PUBLICATION_BINDING.json').read_bytes())
    def test_scope_and_historical_labels_are_exact_and_predecessor_stays_unchanged(self):
        manifest=self.admitted()
        for name in ['paper.tex','historical-render/paper.tex']:
            self.assertEqual((self.out/name).read_bytes().count(access.LABEL_TEXT.encode()),1)
        self.assertEqual(self.before,{str(p.relative_to(self.base)):p.read_bytes()for p in self.base.rglob('*')if p.is_file()})
        self.assertEqual((self.out/'LEAN_ZERO_SORRY_CERTIFICATE.json').read_bytes(),self.before['LEAN_ZERO_SORRY_CERTIFICATE.json'])
        self.assertEqual(manifest['manuscripts'][0]['certification'],'ENTIRELY_UNCERTIFIED_ARTIFACT')
        self.assertEqual(manifest['manuscripts'][1]['filename'],'Run-191-Historical-Paper-UNCERTIFIED.pdf')
    def test_all_original_archive_members_preserved_and_only_labelled_pdf_added(self):
        self.admitted()
        with zipfile.ZipFile(self.base/'SCOPE_EVIDENCE.zip')as old,zipfile.ZipFile(self.out/'SCOPE_EVIDENCE.zip')as new:
            self.assertEqual(set(new.namelist()),set(old.namelist())|{access.HISTORICAL_PDF})
            for name in old.namelist():self.assertEqual(new.read(name),old.read(name))
            self.assertEqual(new.read(access.HISTORICAL_PDF),(self.out/'Run-191-Historical-Paper-UNCERTIFIED.pdf').read_bytes())
        self.assertNotIn(self.before['paper.pdf'],[(self.out/r['filename']).read_bytes()for r in self.read(self.out/'SCOPED_RELEASE_MANIFEST.json')['uploads']])
    def test_metadata_associates_each_exact_filename_with_approved_banner(self):
        self.admitted();description=self.read(self.out/'metadata.json')['description']
        self.assertIn('Run-191-Paper.pdf — '+access.LABEL_TEXT,description)
        self.assertIn('Run-191-Historical-Paper-UNCERTIFIED.pdf — '+access.LABEL_TEXT,description)
    def test_unreviewed_artifact_cannot_be_consumed(self):
        self.hold('regular unsymlinked')
    def test_old_publication_binding_cannot_clear_new_format(self):
        (self.out/'PUBLICATION_BINDING.json').write_bytes(self.before['PUBLICATION_BINDING.json'])
        self.hold('distinct labelled artifact binding')
    def test_original_review_invocation_cannot_be_reused(self):
        value=self.read(self.base/'PHASE7_RULE_EXECUTION.json')['scope_comparison']['current_invocation']
        with self.assertRaisesRegex(ValueError,'separate later artifact review'):
            access.review_labelled(self.f.root,self.out,self.f.authority,review_invocation=value)
        self.assertFalse((self.out/'PUBLICATION_BINDING.json').exists())
    def test_relabelled_main_tex_or_rehashed_manifest_cannot_clear(self):
        self.admitted();path=self.out/'paper.tex';path.write_bytes(path.read_bytes().replace(access.LABEL_TEXT.encode(),b'CERTIFIED'))
        self.change(self.out/'SCOPED_RELEASE_MANIFEST.json',lambda m:next(r for r in m['uploads']if r['filename']=='paper.tex').update(sha256=digest.sha(path)))
        self.change(self.out/'PUBLICATION_BINDING.json',lambda b:b.update(manifest=access.binding(self.out/'SCOPED_RELEASE_MANIFEST.json')))
        self.hold('fresh exact labelled artifact identity')
    def test_labelled_render_input_cannot_be_rebound_to_unlabelled_tex(self):
        self.admitted();path=self.out/'scope-render/paper.tex';path.write_bytes(self.before['paper.tex'])
        self.change(self.out/'scope-render/render-observation/RENDERER_OBSERVATION.json',lambda o:o.update(source_tex_sha256=digest.sha(path)))
        self.hold('exact labelled render source')
    def test_original_historical_source_changed_in_new_archive_holds(self):
        self.admitted();path=self.out/access.HISTORICAL_TEX;path.write_bytes(path.read_bytes()+b'changed')
        self.hold('archive/local bytes differ')
    def test_missing_historical_pdf_even_rehashed_holds(self):
        self.admitted()
        with zipfile.ZipFile(self.out/'SCOPE_EVIDENCE.zip')as z:members=[(n,z.read(n))for n in z.namelist()if n!=access.HISTORICAL_PDF]
        (self.out/'SCOPE_EVIDENCE.zip').write_bytes(digest.archive_bytes(members))
        self.hold('labelled artifact bytes differ')
    def test_changed_quoted_statement_or_certificate_still_hits_genuine_predecessor(self):
        self.admitted();path=self.base/'rendered/statement-001.txt';path.write_bytes(b'invented theorem')
        self.hold('bound input changed|display|CURRENT_RULE|ARCHIVAL|statement')
    def test_wrong_observation_source_pdf_binary_or_cache_cannot_clear(self):
        self.admitted();path=self.out/'historical-render/render-observation/RENDERER_OBSERVATION.json';raw=path.read_bytes()
        for field in ['source_tex_sha256','rendered_pdf_sha256']:
            try:
                self.change(path,lambda o:o.update({field:'0'*64}))
                self.hold('observation mismatch')
            finally:path.write_bytes(raw)
        self.f.binary.write_bytes(b'wrong binary');self.hold('current pinned renderer bytes differ')
    def test_wrong_cache_file_cannot_clear(self):
        self.admitted();cache=self.read(self.f.cache['path']);(Path(cache['cache_root'])/'asset-000.dat').write_bytes(b'changed cache')
        self.hold('bound input changed')
    def test_future_or_naive_binding_and_predated_render_hold(self):
        self.admitted();path=self.out/'PUBLICATION_BINDING.json';raw=path.read_bytes()
        for timestamp in ['2999-01-01T00:00:00Z','2026-10-14T00:00:00Z','2026-10-17T00:00:00']:
            try:
                self.change(path,lambda b:b.update(issued_at_utc=timestamp));self.hold('labelled artifact after|HOLD_UTC_TIME_REQUIRED')
            finally:path.write_bytes(raw)
    def test_changed_human_label_authority_cannot_clear(self):
        self.admitted();path=Path(self.f.label_authority['path']);self.change(path,lambda a:a.update(approved_text='CERTIFIED'))
        self.hold('bound input changed')
    def test_extra_claim_or_certified_role_cannot_clear(self):
        self.admitted();path=self.out/'SCOPED_RELEASE_MANIFEST.json'
        self.change(path,lambda m:m['manuscripts'][0].update(certification='CERTIFIED'))
        self.change(self.out/'PUBLICATION_BINDING.json',lambda b:b.update(manifest=access.binding(path)))
        self.hold('fresh exact labelled artifact identity')
    def test_binding_cannot_claim_scientific_or_publication_authority(self):
        self.admitted();path=self.out/'PUBLICATION_BINDING.json';raw=path.read_bytes()
        for key in ['certifies','publication_authorized']:
            try:
                self.change(path,lambda b:b.update({key:True}));self.hold('distinct labelled artifact binding')
            finally:path.write_bytes(raw)
    def test_display_race_after_fresh_predecessor_is_not_cached(self):
        self.admitted();real=access.predecessor;calls=[]
        def attack(*a,**kw):
            result=real(*a,**kw);calls.append(1)
            if len(calls)==1:(self.out/'scope-render/rendered/FROZEN_CONTEXT.txt').write_bytes(b'changed context')
            return result
        with patch.object(access,'predecessor',side_effect=attack):self.hold('scope display differs')
    def test_unknown_manifest_or_scientific_authority_field_holds(self):
        self.admitted();self.change(self.out/'SCOPED_RELEASE_MANIFEST.json',lambda m:m.update(certifies=True))
        self.hold('fresh exact labelled artifact identity')
    def test_symlinked_historical_pdf_holds(self):
        self.admitted();path=self.out/'Run-191-Historical-Paper-UNCERTIFIED.pdf';copy=self.f.root/'other.pdf';copy.write_bytes(path.read_bytes());path.unlink();path.symlink_to(copy)
        self.hold('regular unsymlinked')




class HistoricalDigestCompatibilityTests(unittest.TestCase):
    def test_exact_frozen_metadata_and_wrapper_remain_readable_but_not_new_publishable(self):
        with tempfile.TemporaryDirectory(prefix='a2-historical-compatibility-')as tmp:
            f=PortableFixture(tmp)
            with f.context():
                base=f.base_note();out=f.root/'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access/old-archival'
                access.prepare(f.root,base,out,f.authority,render=f.render)
                consumers={'consume':access.require_current,'consume_authority':access.require_authority}
                package=f.root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/old-archival'
                # The producer functions are exact frozen source. The current
                # reader runs after these temporary producer-only bindings exit.
                with access.frozen_sources(f.root)as load:
                    old=load('methods_digest')
                    with patch.object(digest,'metadata_proposal',side_effect=old.metadata_proposal),patch.object(digest,'wrapper_tex',side_effect=old.wrapper_tex):
                        manifest=digest.prepare(f.root,package,'2026-W42',[{'run_id':f.run,'path':str(out)}],f.authority,f.before_metadata,'2026-10-16',render=lambda p:f.render(p,root=f.root),**consumers)
                    self.assertEqual((package/'paper.tex').read_bytes(),old.wrapper_tex('2026-W42',manifest['notes']))
                    self.assertEqual(digest.wrapper_tex('2026-W42',manifest['notes']),old.wrapper_tex('2026-W42',manifest['notes']))
                self.assertEqual(digest.require_current(package,f.root,**consumers),manifest)
                self.assertEqual(manifest['standard'],digest.STANDARD)
                with self.assertRaisesRegex(ValueError,'labelled artifact envelope'):digest.require_new_publication(manifest)


class LabelledRegistrationOutputTests(unittest.TestCase):
    """Output transformations over synthetic DATA, never an admission proof.

    No forged default consumer/PB/science PASS is supplied. The explicit test
    consumer only makes shape DATA available to pure presentation functions;
    the separate complete-source fixture executes genuine default admission.
    """
    def setUp(self):
        import methods_digest_registration_v3 as registration
        self.reg=registration
        self.temp=tempfile.TemporaryDirectory(prefix='a2-registration-output-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.note=self.root/'note';self.note.mkdir();(self.root/'digest').mkdir()
        self.certificate=self.root/'certificate.json';self.certificate.write_bytes(b'{"fixture":"NOT_A_CERTIFICATE"}')
        def bound(path):return {'path':str(path),'sha256':digest.sha(path)}
        self.cert=bound(self.certificate)
        self.statement={'path':'TEST_ONLY_STATEMENT.lean','sha256':'2'*64}
        self.predecessor={'path':str(self.root/'sealed'),'manifest':{'path':'TEST_ONLY_SEALED_MANIFEST.json','sha256':'3'*64},'publication_binding':{'path':'TEST_ONLY_SEALED_BINDING.json','sha256':'4'*64}}
        self.manifest={'standard':digest.LABELLED_STANDARD,'release_week':'2026-W42','notes':[{
            'path':str(self.note),'run_id':'Run-191','certificate':self.cert,
            'candidate':{'path':'TEST_ONLY_CANDIDATE.lean','sha256':'5'*64},'formal_statement':self.statement,
            'statement_scope':[{'lean_theorem':'TEST_ONLY_QUOTED_STATEMENT'}],'scientific_predecessor':self.predecessor,
            'publication_binding':{'path':'TEST_ONLY_LABELLED_BINDING.json','sha256':'6'*64}}]}
        receipt_path=self.root/'REGISTRATION.json';receipt_path.write_bytes(digest.raw_json({'standard':registration.STANDARD,'fixture':'OUTPUT_ONLY_NOT_ADMISSION'}))
        self.binding=bound(receipt_path)
        self.receipt={'record_id':'24000001','doi':'10.5281/zenodo.24000001','release_week':'2026-W42','package_path':'digest','children':registration._children(self.root,self.root/'digest',self.manifest)}
        self.ledger={'tree_root':str(self.root),'file_entities':[],'run_entities':[],'publication_entities':[],'publication_holds':[]}
        self.calls=[]
        self.rows=registration.entity_rows(self.root,self.binding,self.ledger,consume=self.output_only_consumer)
        self.ledger['publication_entities']=deepcopy(self.rows)
    def output_only_consumer(self,*args,**kwargs):
        self.calls.append(kwargs)
        return {'receipt':deepcopy(self.receipt),'manifest':deepcopy(self.manifest)}
    def evaluate(self,row,consume=None):
        import claim_binding
        def forbidden(*args,**kwargs):raise AssertionError('new explicit registration route used legacy classification')
        with patch.object(claim_binding,'find_entity',return_value=row):
            return self.reg.evaluate_publication(self.root/row['path'],self.ledger,legacy=forbidden,enforce=True,consume=consume or self.output_only_consumer)
    def test_child_receipt_keeps_issuer_only_under_exact_statement_evidence(self):
        child=self.receipt['children'][0];evidence=child['statement_certificate_evidence']
        self.assertIsNone(child['certificate']);self.assertEqual(child['artifact_label'],digest.ARTIFACT_LABEL)
        self.assertEqual(evidence['certificate'],self.cert);self.assertEqual(evidence['formal_statement'],self.statement)
        self.assertEqual(evidence['scientific_predecessor'],self.predecessor)
        self.assertEqual(evidence['scope'],'EXACT_SEALED_PREDECESSOR_AND_QUOTED_FORMAL_STATEMENTS_ONLY')
        self.assertTrue(evidence['certificate_valid']);self.assertFalse(evidence['certifies_current_artifact'])
    def test_current_artifact_rows_are_never_certified_or_bare_certificate_bound(self):
        for row in self.rows:
            self.assertEqual(row['status'],'UNCERTIFIED');self.assertFalse(row['certificate_valid']);self.assertFalse(row['certifies'])
            self.assertEqual(row['artifact_label'],digest.ARTIFACT_LABEL)
        child=self.rows[1];self.assertIsNone(child['certificate']);self.assertIsNone(child['certificate_sha256'])
        self.assertEqual(child['statement_certificate_evidence'],self.receipt['children'][0]['statement_certificate_evidence'])
    def test_delivery_integrity_pass_never_promotes_group_or_note_pdf(self):
        for row in self.rows:
            result=self.evaluate(row)
            self.assertEqual(result['status'],'PASS');self.assertTrue(result['release_eligible'])
            self.assertEqual(result['verification_status'],'UNCERTIFIED');self.assertFalse(result['certificate_valid']);self.assertFalse(result['certifies'])
            self.assertEqual(result['label'],digest.ARTIFACT_LABEL)
            self.assertEqual(result['statement_certificate_evidence'],row['statement_certificate_evidence'])
    def test_generic_certificate_or_certified_status_promotion_is_held(self):
        for change in [{'certificate':str(self.certificate.relative_to(self.root))},{'certificate_sha256':self.cert['sha256']},{'status':'CERTIFIED'},{'certificate_valid':True},{'certifies':'LISTED_NOTE_SCOPE_ONLY'}]:
            row={**deepcopy(self.rows[1]),**change};result=self.evaluate(row)
            self.assertEqual(result['status'],'HOLD');self.assertFalse(result['release_eligible']);self.assertFalse(result['canon_eligible'])
    def test_statement_evidence_drift_is_held_by_preserve_and_evaluate(self):
        previous=deepcopy(self.ledger);previous['publication_entities'][1]['statement_certificate_evidence']['certificate']['sha256']='0'*64
        result=self.reg.preserve({**self.ledger,'publication_entities':[]},previous,legacy=lambda current,old:deepcopy(current),consume=self.output_only_consumer)
        self.assertTrue(all(row['publication_registration_status']=='HOLD'for row in result['publication_entities']))
        self.assertEqual(self.evaluate(previous['publication_entities'][1])['status'],'HOLD')
    def test_fresh_registration_failure_is_not_replaced_by_output_classification(self):
        def fail(*args,**kwargs):raise self.reg.RegistrationHold('TEST_ONLY_FRESH_INPUT_DRIFT')
        result=self.evaluate(self.rows[1],consume=fail)
        self.assertEqual(result['status'],'HOLD');self.assertFalse(result['exact_publication_binding'])
    def test_audit_group_has_no_certified_pdf_count_or_unscoped_issuer(self):
        audit=self.reg.augment_audit(self.root,self.ledger,{'published_records':[],'counts':{}},consume=self.output_only_consumer)
        self.assertEqual(audit['published_records'],[]);self.assertEqual(audit['counts'],{'methods_digest_groups':1})
        row=audit['methods_digest_groups'][0];self.assertEqual(row['verification_status'],'UNCERTIFIED');self.assertFalse(row['certificate_valid']);self.assertFalse(row['certifies'])
        self.assertEqual(row['run_ids'],[]);self.assertEqual(row['note_run_ids'],['Run-191'])
    def test_public_label_output_names_uncertified_artifact_and_keeps_scoped_evidence(self):
        row={'doi':self.receipt['doi'],'deposit_paths':[str(self.root/'digest')],'methods_digest_registration':{'tree_root':str(self.root),'receipt':self.binding}}
        body={'metadata':{'title':'TEST_ONLY_TITLE','description':digest.ARTIFACT_LABEL},'files':[]}
        result=self.reg._public_label_read_record_pre_prior_processing(row,legacy=lambda row:None,getter=lambda rid,accept:(body,'7'*64),consume=self.output_only_consumer)
        self.assertEqual(result['status'],'READ');self.assertEqual(result['proposed_label'],digest.ARTIFACT_LABEL)
        self.assertEqual(result['public_verification_status'],'UNCERTIFIED');self.assertFalse(result['certificate_valid']);self.assertFalse(result['certifies'])
        self.assertEqual(result['statement_certificate_evidence'],self.rows[0]['statement_certificate_evidence'])

if __name__=='__main__':unittest.main()
