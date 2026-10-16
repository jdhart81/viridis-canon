"""Real validators over declared portable trust fixtures; never production proof."""
from copy import deepcopy
from io import BytesIO
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from w42_portable_fixture import PortableFixture,pdf,ORIGINAL
import nightly_manuscript_access as access
import nightly_manuscript_checkpoint as checkpoint
import methods_digest_v2 as digest
spec=importlib.util.spec_from_file_location('w42_unchanged_recursive_pdf_gate',HERE.parents[1]/'manuscript_pdf_gate.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

class ArchivalAccessTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='w42-control-');self.addCleanup(self.temp.cleanup)
        self.f=PortableFixture(self.temp.name)
        self.scope=self.f.context();self.scope.__enter__();self.addCleanup(self.scope.__exit__,None,None,None)
        self.base=self.f.base_note()
        self.out=self.f.root/'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access/Run-191'
        self.current=access.prepare(self.f.root,self.base,self.out,self.f.authority,render=self.f.render)
    def read(self,p):return json.loads(Path(p).read_bytes())
    def change(self,p,fn):
        value=self.read(p);fn(value);Path(p).write_bytes(digest.raw_json(value))
    def require(self):return access.require_current(self.out,self.f.root,self.f.authority)
    def hold(self,reason):
        with self.assertRaisesRegex((ValueError,OSError),reason):self.require()
    def test_actual_default_base_and_access_preserve_science_and_both_pdfs(self):
        self.assertTrue(self.current['exact_publication_binding']);self.assertFalse(self.current['publication_authorized'])
        manifest=self.read(self.out/'SCOPED_RELEASE_MANIFEST.json')
        self.assertEqual(manifest['standard'],access.STANDARD)
        base_manifest=self.read(self.base/'SCOPED_RELEASE_MANIFEST.json')
        for row in base_manifest['uploads']:
            if row['filename']!='SCOPE_EVIDENCE.zip':self.assertEqual((self.base/row['filename']).read_bytes(),(self.out/row['filename']).read_bytes())
        with zipfile.ZipFile(self.base/'SCOPE_EVIDENCE.zip')as old,zipfile.ZipFile(self.out/'SCOPE_EVIDENCE.zip')as new:
            self.assertNotIn(access.HISTORICAL_PDF,old.namelist())
            self.assertEqual(set(new.namelist()),set(old.namelist())|{access.HISTORICAL_PDF})
            for name in old.namelist():self.assertEqual(old.read(name),new.read(name))
            self.assertEqual(new.read(access.HISTORICAL_PDF),(self.out/'Run-191-Historical-Paper.pdf').read_bytes())
        result=gate.require_local(self.out,[self.out/u['filename']for u in manifest['uploads']])
        self.assertEqual(result['status'],'SEPARATE_MANUSCRIPT_PDF_PREFLIGHT_PASS')
        self.assertEqual(len(result['top_level_pdfs']),2)
        self.assertEqual([m['certification']for m in manifest['manuscripts']],['EXACT_SCOPED_PREDECESSOR_ONLY','ENTIRELY_UNCERTIFIED'])
    def test_unchanged_old_default_refuses_new_archive_format(self):
        with access.frozen_sources(self.f.root)as load:
            with self.assertRaises(ValueError):load('phase7_audit_policy').require_note_publication_bound(self.out,self.f.root,self.f.authority)
    def test_changed_archival_source_holds(self):
        (self.out/access.HISTORICAL_TEX).write_bytes(ORIGINAL+b'changed')
        self.hold('archive/local access bytes differ')
    def test_wrong_historical_pdf_holds(self):
        (self.out/'Run-191-Historical-Paper.pdf').write_bytes(pdf('different original rendering'))
        self.hold('final PDF/source/cache observation mismatch|renderer PDF differs')
    def test_historical_render_input_cannot_be_corrected_r3_tex(self):
        (self.out/'historical-render/paper.tex').write_bytes(ORIGINAL+b'corrected R3 source')
        self.hold('historical render input')
    def test_header_only_pdf_cannot_become_bound_even_with_matching_observation(self):
        out=self.out.parent/'header-only-attempt'
        def header_only(tex,*,root):
            self.f.render(tex,root=root)
            raw=b'%PDF-1.4\nHEADER_ONLY_NOT_A_PDF\n'
            p=Path(tex).parent/'render-observation'
            (p/'paper.pdf').write_bytes(raw)
            self.change(p/'RENDERER_OBSERVATION.json',lambda o:o.update(rendered_pdf_sha256=digest.digest(raw)))
            return raw
        with self.assertRaisesRegex(access.AccessHold,'complete historical PDF envelope'):
            access.prepare(self.f.root,self.base,out,self.f.authority,render=header_only)
        self.assertFalse((out/'PUBLICATION_BINDING.json').exists())
    def test_wrong_source_observation_holds(self):
        self.change(self.out/'historical-render/render-observation/RENDERER_OBSERVATION.json',lambda o:o.update(source_tex_sha256='0'*64))
        self.hold('final PDF/source/cache observation mismatch')
    def test_wrong_current_binary_holds(self):
        self.f.binary.write_bytes(b'changed simulated binary')
        self.hold('current pinned renderer bytes differ')
    def test_wrong_current_cache_holds(self):
        cache=self.read(self.f.cache['path']);(Path(cache['cache_root'])/'asset-000.dat').write_bytes(b'changed')
        self.hold('bound input changed')
    def test_missing_historical_same_stem_archive_pdf_holds(self):
        with zipfile.ZipFile(self.out/'SCOPE_EVIDENCE.zip')as z:members=[(n,z.read(n))for n in z.namelist()if n!=access.HISTORICAL_PDF]
        (self.out/'SCOPE_EVIDENCE.zip').write_bytes(digest.archive_bytes(members))
        self.hold('changed copied access input')
    def test_unknown_manifest_field_holds(self):
        self.change(self.out/'SCOPED_RELEASE_MANIFEST.json',lambda o:o.update(scientific_claim='invented'))
        self.hold('closed distinct archival access manifest')
    def test_predecessor_publication_binding_drift_holds(self):
        self.change(self.base/'PUBLICATION_BINDING.json',lambda o:o.update(certifies=True))
        self.hold('EXACT_NIGHTLY_PUBLICATION_BINDING')
    def test_predecessor_source_receipt_drift_holds(self):
        self.change(self.base/'NIGHTLY_SCOPE_SOURCE.json',lambda o:o.update(selected_theorems=['foreign']))
        self.hold('UNIQUE_CERTIFICATE_LISTED_SELECTION|EXACT_CURRENT_RULE_INPUT_COVERAGE|bound input changed')
    def test_scope_or_metadata_drift_cannot_inherit_predecessor(self):
        (self.out/'metadata.json').write_bytes(digest.raw_json({'title':'new claims'}))
        self.hold('changed copied access input')
    def test_render_observation_must_not_be_future_or_naive(self):
        p=self.out/'historical-render/render-observation/RENDERER_OBSERVATION.json'
        for timestamp in ['2999-01-01T00:00:00Z','2026-01-01T00:00:00']:
            old=p.read_bytes();self.change(p,lambda o:o.update(ended_at_utc=timestamp))
            with self.assertRaisesRegex(ValueError,'PDF observation time invalid|UTC timestamp required'):self.require()
            p.write_bytes(old)
    def test_fresh_frozen_source_not_ambient_code_or_bytecode(self):
        fake=types.ModuleType('phase7_audit_policy');fake.require_note_publication_bound=lambda *a:(_ for _ in ()).throw(AssertionError('ambient code executed'))
        with patch.dict(sys.modules,{'phase7_audit_policy':fake}):self.assertTrue(self.require()['exact_publication_binding'])
        source=self.f.gates/'phase7_audit_policy.py';source.write_bytes(source.read_bytes()+b'\n# drift\n')
        self.hold('frozen source changed')
    def test_symlinked_pdf_cannot_become_access_input(self):
        p=self.out/'Run-191-Historical-Paper.pdf';other=self.f.root/'same.pdf';other.write_bytes(p.read_bytes());p.unlink();p.symlink_to(other)
        self.hold('regular unsymlinked file required')
    def test_render_input_race_holds(self):
        real=access.predecessor;calls=[]
        def trigger(*a,**kw):
            value=real(*a,**kw);calls.append(1)
            if len(calls)==1:(self.out/'historical-render/paper.tex').write_bytes(ORIGINAL+b'race')
            return value
        # Attack injection only: the real old reader executes before mutation.
        with patch.object(access,'predecessor',side_effect=trigger):self.hold('historical render input')
    def test_current_target_changed_after_reader_is_not_cached(self):
        real=access.predecessor;calls=[]
        def trigger(*a,**kw):
            value=real(*a,**kw);calls.append(1)
            if len(calls)==1:
                ledger=self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                self.change(ledger,lambda o:o['run_entities'][0].update(status='HELD'))
            return value
        with patch.object(access,'predecessor',side_effect=trigger):
            self.hold('CURRENT_PARITY_QUALIFIED_CERTIFIED_RUN')
    def test_access_binding_cannot_claim_scientific_or_publication_authority(self):
        self.change(self.out/'PUBLICATION_BINDING.json',lambda o:o.update(publication_authorized=True))
        self.hold('exact distinct access binding')
    def test_closed_manuscript_roles_cannot_swap_certification(self):
        self.change(self.out/'SCOPED_RELEASE_MANIFEST.json',lambda o:o['manuscripts'][1].update(certification='CERTIFIED'))
        self.hold('fresh exact additive access identity')
    def test_original_uncertified_labels_and_certificate_remain_exact(self):
        self.assertEqual((self.out/'LEAN_ZERO_SORRY_CERTIFICATE.json').read_bytes(),(self.base/'LEAN_ZERO_SORRY_CERTIFICATE.json').read_bytes())
        self.assertEqual((self.out/'WHOLE_PAPER_MAP.json').read_bytes(),(self.base/'WHOLE_PAPER_MAP.json').read_bytes())
        self.assertIn(b'Entirely UNCERTIFIED', (self.out/'paper.tex').read_bytes())

class FrozenInputBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name).resolve();self.gates=self.root/access.GATES;self.gates.mkdir(parents=True)
        source_root=HERE.parents[2]
        for name,h in access._FROZEN_HASHES.items():
            choices=[source_root/name,*source_root.rglob(name)]
            source=next((p for p in choices if p.is_file()and digest.sha(p)==h),None)
            self.assertIsNotNone(source,'exact public repository predecessor source '+name)
            (self.gates/name).write_bytes(source.read_bytes())
    def test_frozen_hash_boundary_rejects_source_drift_before_execution(self):
        p=self.gates/'phase7_audit_policy.py';p.write_bytes(p.read_bytes()+b'\n# drift\n')
        with self.assertRaisesRegex(access.AccessHold,'frozen source changed'):
            with access.frozen_sources(self.root):self.fail('source executed after hash drift')
    def test_frozen_hash_boundary_rejects_race_before_return(self):
        with self.assertRaisesRegex(access.AccessHold,'frozen source race'):
            with access.frozen_sources(self.root):
                p=self.gates/'phase7_audit_policy.py';p.write_bytes(p.read_bytes()+b'\n# race\n')
    def test_frozen_inputs_refuse_symlink_and_ignore_saved_bytecode(self):
        with access.frozen_sources(self.root):pass
        cache=self.gates/'__pycache__';cache.mkdir();(cache/'phase7_audit_policy.pyc').write_bytes(b'not code')
        with access.frozen_sources(self.root):pass
        p=self.gates/'phase7_audit_policy.py';other=self.root/'same.py';other.write_bytes(p.read_bytes());p.unlink();p.symlink_to(other)
        with self.assertRaisesRegex(ValueError,'regular unsymlinked'):
            with access.frozen_sources(self.root):self.fail('symlinked source accepted')

class HistoricalInputTests(unittest.TestCase):
    def test_exact_self_contained_original_is_supported(self):
        self.assertEqual(access.require_self_contained_original(ORIGINAL),ORIGINAL)
    def test_unbound_file_input_graphics_dynamic_and_external_package_hold(self):
        for extra in [br'\input{other.tex}',br'\includegraphics{other.pdf}',
                      br'\bibliography{refs}',br'\csname input\endcsname{other}',
                      br'\usepackage{../../outside}',br'\documentclass{../outside}']:
            with self.subTest(extra=extra),self.assertRaisesRegex(access.AccessHold,'unbound historical|pinned-cache'):
                access.require_self_contained_original(ORIGINAL+extra)

class DigestRoleTests(unittest.TestCase):
    def test_closed_role_binding_rejects_omission_swap_extra_or_changed_hash(self):
        declared={'paper.pdf':{'sha256':'a'*64},'Run-191-Historical-Paper.pdf':{'sha256':'b'*64}}
        roles=access.manuscripts('Run-191',b'current',b'historical')
        roles[0]['sha256']='a'*64;roles[1]['sha256']='b'*64
        self.assertEqual(digest.access_manuscripts({'manuscripts':roles},declared,'Run-191'),roles)
        for value in [roles[:1],list(reversed(roles)),roles+[deepcopy(roles[0])],
                      [roles[0],{**roles[1],'certification':'CERTIFIED'}],
                      [roles[0],{**roles[1],'sha256':'0'*64}]]:
            with self.subTest(value=value),self.assertRaisesRegex(digest.DigestHold,'closed actual manuscript roles'):
                digest.access_manuscripts({'manuscripts':value},declared,'Run-191')

class DigestAccessTests(unittest.TestCase):
    setUp = ArchivalAccessTests.setUp
    def test_default_current_digest_refuses_unscoped_self_authored_profile(self):
        import packaging_runtime as runtime
        with self.assertRaisesRegex(runtime.PackagingHold,'SOURCE_SESSION'):
            digest.current_note_consumer(self.out,self.f.root,self.f.authority)
        with self.assertRaisesRegex(runtime.PackagingHold,'SOURCE_SESSION'):
            digest.current_authority_consumer(self.f.root,self.f.authority)

    def test_partitioned_actual_consumer_digest_exact_two_roles_and_recursive_gate(self):
        # Coverage partition: genuine scientific DEFAULT admission runs inside
        # access.require_current. This does not mint/claim the separate installed
        # packaging session; the normal default HOLD is tested above.
        consumers={'consume':access.require_current,'consume_authority':access.require_authority}
        value=access.require_current(self.out,self.f.root,self.f.authority)
        self.assertEqual(value['access_standard'],access.STANDARD)
        package=self.f.root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/W42'
        manifest=digest.prepare(self.f.root,package,'2026-W42',[{'run_id':self.f.run,'path':str(self.out)}],self.f.authority,self.f.before_metadata,'2026-10-16',render=lambda p:self.f.render(p,root=self.f.root),**consumers)
        self.assertIn('Run-191-Historical-Paper.pdf',{u['filename']for u in manifest['uploads']})
        self.assertEqual(digest.require_current(package,self.f.root,**consumers),manifest)
        digest.publication_binding(package,self.f.root,**consumers)
        self.assertEqual(digest.require_publication_bound(package,self.f.root,**consumers)[0],manifest)
        names={u['filename']for u in manifest['uploads']}
        self.assertEqual(names,{'paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip','Run-191-Paper.pdf','Run-191-Historical-Paper.pdf'})
        import digest_controller_v2 as controller
        self.assertIn('Run-191-Historical-Paper.pdf',controller.approved_inventory(package,manifest))
        uploads=[package/u['filename']for u in manifest['uploads']]+[package/'DIGEST_MANIFEST.json',package/'PUBLICATION_BINDING.json']
        preflight=gate.require_local(package,uploads)
        self.assertEqual(len(preflight['top_level_pdfs']),3)
        files=[{'key':u['filename'],'checksum':'md5:'+u['md5'],'size':u['bytes']}for u in preflight['upload_files']]
        calls=[]
        def download(record,name):calls.append(name);return (package/name).read_bytes()
        public=gate.require_public({'id':123,'files':files},preflight,download=download)
        self.assertEqual(public['status'],'SEPARATE_MANUSCRIPT_PDF_PUBLIC_READBACK_PASS')
        self.assertEqual(set(calls),{p.name for p in uploads})
        historical=package/'Run-191-Historical-Paper.pdf';historical.write_bytes(pdf('wrong public bytes'))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold,'downloaded upload differs'):gate.require_public({'id':123,'files':files},preflight,download=download)
        with self.assertRaisesRegex(digest.DigestHold,'separate note manuscript differs'):digest.require_current(package,self.f.root,**consumers)

if __name__=='__main__':unittest.main(verbosity=2)
