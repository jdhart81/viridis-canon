"""Complete real source/default route over explicitly simulated trust DATA.

No production renderer/provider/authority, source activation or publication is
claimed. The complete original source validators and default consumers execute;
this test never supplies an alternate admission consumer or saved PASS result.
"""
from pathlib import Path
import json
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from w42_full_session_fixture import FullSessionFixture
from w42_portable_fixture import pdf
import manuscript_pdf_gate as gate


class CompleteDefaultRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Share immutable trust/source DATA, while each operation still performs
        # every real fresh source validation. Negative mutations are restored.
        cls.temp=tempfile.TemporaryDirectory(prefix='w42-complete-source-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.full=FullSessionFixture(Path(cls.temp.name).resolve())
        cls.f=cls.full.science_fixture
        cls.completed=[]
        cls.canonical_runtime=None
        cls.context=cls.full.context();cls.context.__enter__()
        cls.addClassCleanup(cls.context.__exit__,None,None,None)

    @classmethod
    def tearDownClass(cls):
        proof=cls.full.source_receipt()
        assert proof['legacy_source_pins']==130 and proof['current_modules']==20 and proof['shared_helpers']==1
        assert proof['all_function_class_asts_equal']and proof['all_non_data_control_flow_equal']
        assert proof['core_open_attempts']==[]and proof['mocked_validate_or_current_closure']is False
        assert proof['context_mints']==0 and proof['module_aliases']==0
        print('VRS_COMPLETE_SOURCE_ROUTE_PROOF='+json.dumps({
            k:proof[k]for k in ('legacy_source_pins','current_modules','shared_helpers',
                'loader_executions','all_function_class_asts_equal',
                'all_non_data_control_flow_equal','core_open_attempts',
                'mocked_validate_or_current_closure','context_mints','module_aliases')
        }|{'completed_actual_facade_operations':cls.completed},sort_keys=True),flush=True)

    def invoke(self,entrypoint,*args,**kwargs):
        if 'render' in kwargs:
            render=kwargs['render']
            def capture_active_canonical(*render_args,**render_kwargs):
                # The original SourceFinder has created this exact canonical
                # module inside the active genuine session. Retain its object
                # only for a later revocation probe; never import or alias it.
                canonical=sys.modules['packaging_runtime']
                expected=self.full.root/'_ZENODO_DEPOSITS/standalone_pdf_runtime/packaging_runtime.py'
                self.assertEqual(Path(canonical.__file__).resolve(),expected)
                canonical.require_source_session(self.full.root,self.full.binding)
                type(self).canonical_runtime=canonical
                return render(*render_args,**render_kwargs)
            kwargs['render']=capture_active_canonical
        result=self.full.runtime.note_preparation(self.full.root,entrypoint,*args,**kwargs)
        self.completed.append(entrypoint)
        return result

    def prepare_base(self):
        source=self.invoke('source_for_cycle',self.f.run,self.f.cycle,
            self.f.before_metadata,self.full.source_pins130,
            selection_invocation='TEST_ONLY_COMPLETE_SOURCE_SELECTION',
            selected_theorems=['bounded'],selection_at_utc='2026-10-14T00:00:00Z')
        self.assertFalse(source['certifies'])
        self.assertEqual(source['status'],'STAGED_SOURCE_NOT_REVIEW_OR_PUBLICATION_BOUND')
        base=self.full.root/'RESEARCH_PIPELINE_v2/science_release_queue/complete-base'/self.f.run
        staged=self.invoke('stage_checkpoint',base,self.f.run,self.f.cycle,
            self.f.before_metadata,self.full.source_pins130,
            selection_invocation='TEST_ONLY_COMPLETE_STAGE',render=self.f.render,
            selected_theorems=['bounded'])
        self.assertEqual(staged['status'],'EXACT_NIGHTLY_SCOPE_SOURCE_AND_PDF_STAGED_NOT_ADMITTED')
        self.assertFalse((base/'PUBLICATION_BINDING.json').exists())
        reviewed=self.invoke('review_checkpoint',base,self.f.authority,
            review_invocation='TEST_ONLY_SEPARATE_LATER_CURRENT_REVIEW')
        self.assertEqual(reviewed['status'],'ACTUAL_DEFAULT_NIGHTLY_MINIMAL_SCOPE_BINDING_PASS')
        self.assertEqual(json.loads((base/'PUBLICATION_BINDING.json').read_bytes())['status'],'PUBLICATION_BOUND')
        return base

    def assert_revoked(self):
        with self.assertRaisesRegex(ValueError,'SOURCE_SESSION'):
            self.full.runtime.require_source_session(self.full.root,self.full.binding)
        # Inspect only the genuine canonical object, if one was created. A
        # fresh unscoped import here would introduce foreign checkout code into
        # the next original SourceFinder validation and spoil this cold fixture.
        canonical=type(self).canonical_runtime
        if canonical is not None:
            expected=self.full.root/'_ZENODO_DEPOSITS/standalone_pdf_runtime/packaging_runtime.py'
            self.assertEqual(Path(canonical.__file__).resolve(),expected)
            with self.assertRaisesRegex(ValueError,'SOURCE_SESSION'):
                canonical.require_source_session(self.full.root,self.full.binding)

    def test_complete_normal_default_source_review_access_digest_and_pdf_readbacks(self):
        base=self.prepare_base()
        out=self.full.root/'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access'/self.f.run
        current=self.invoke('prepare_access',base,out,self.f.authority,render=self.f.render)
        self.assertTrue(current['exact_publication_binding'])
        self.assertFalse(current['publication_authorized'])
        discovery=self.f.account_discovery()
        specs,observed=self.invoke('new_note_specs',[out],self.f.authority,
            week='2026-W42',account_discovery=discovery)
        self.assertEqual(specs,[{'run_id':self.f.run,'path':str(out)}])
        self.assertEqual(observed['status'],'NO_EXISTING_WEEKLY_RECORD')
        package=self.full.root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/complete-W42'
        staged=self.invoke('stage_weekly_package',package,'2026-W42',[out],
            self.f.authority,self.f.before_metadata,'2026-10-16',
            account_discovery=discovery,render=lambda p:self.f.render(p,root=self.full.root))
        self.assertEqual(staged['status'],'ACTUAL_DEFAULT_NOTE_COHORT_AND_METHODS_PACKAGE_STAGED_NOT_PUBLISHED')
        self.assertTrue(staged['full_pdf_review_and_publication_authority_still_required'])
        manifest=json.loads((package/'DIGEST_MANIFEST.json').read_bytes())
        names={u['filename']for u in manifest['uploads']}
        self.assertEqual(names,{'paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip',
            'Run-191-Paper.pdf','Run-191-Historical-Paper.pdf'})
        uploads=[package/u['filename']for u in manifest['uploads']]+[package/'DIGEST_MANIFEST.json']
        preflight=gate.require_local(package,uploads)
        self.assertEqual(preflight['status'],'SEPARATE_MANUSCRIPT_PDF_PREFLIGHT_PASS')
        self.assertEqual(len(preflight['top_level_pdfs']),3)
        files=[{'key':u['filename'],'checksum':'md5:'+u['md5'],'size':u['bytes']}for u in preflight['upload_files']]
        calls=[]
        def download(record,name):
            calls.append(name);return(package/name).read_bytes()
        public=gate.require_public({'id':123,'files':files},preflight,download=download)
        self.assertEqual(public['status'],'SEPARATE_MANUSCRIPT_PDF_PUBLIC_READBACK_PASS')
        self.assertEqual(set(calls),{p.name for p in uploads})
        historical=package/'Run-191-Historical-Paper.pdf'
        original=historical.read_bytes()
        try:
            historical.write_bytes(pdf('DIFFERENT SIMULATED PUBLIC PDF'))
            with self.assertRaisesRegex(ValueError,'downloaded upload differs'):
                gate.require_public({'id':123,'files':files},preflight,download=download)
        finally:historical.write_bytes(original)
        self.assertEqual(self.completed,['source_for_cycle','stage_checkpoint','review_checkpoint',
            'prepare_access','new_note_specs','stage_weekly_package'])
        self.assert_revoked()

    def test_real_facade_exception_revokes_all_session_capabilities(self):
        with self.assertRaisesRegex(ValueError,'regular unsymlinked file required'):
            self.invoke('review_checkpoint',self.full.root/'missing-note',self.f.authority,
                review_invocation='TEST_ONLY_MISSING_NOTE')
        self.assert_revoked()

    def test_changed_required_source_holds_before_any_note_write(self):
        row=next(r for r in self.full.source_pins130 if r['name']=='nightly_minimal_policy.py')
        path=Path(row['path']);raw=path.read_bytes();path.write_bytes(raw+b'\n# TEST ONLY SOURCE DRIFT\n')
        out=self.full.root/'RESEARCH_PIPELINE_v2/science_release_queue/never-created'/self.f.run
        try:
            with self.assertRaises(ValueError):
                self.invoke('stage_checkpoint',out,self.f.run,self.f.cycle,
                    self.f.before_metadata,self.full.source_pins130,
                    selection_invocation='TEST_ONLY_DRIFT',render=self.f.render)
            self.assertFalse(out.exists())
        finally:path.write_bytes(raw)
        self.assert_revoked()

    def test_genuine_capability_cannot_authorize_another_root_or_profile_path(self):
        profile=Path(self.full.binding['path'])
        if not profile.is_absolute():profile=self.full.root/profile
        alternate=self.f.put('synthetic-trust/FOREIGN_PROFILE.json',
            profile.read_bytes())
        foreign=self.full.root/'foreign-root';foreign.mkdir()
        with self.full.runtime.session(self.full.root,self.full.binding):
            type(self).canonical_runtime=sys.modules['packaging_runtime']
            self.full.runtime.require_source_session(self.full.root,self.full.binding)
            self.canonical_runtime.require_source_session(self.full.root,self.full.binding)
            with self.assertRaisesRegex(ValueError,'ACTIVE_EXACT_NOMINATED_SOURCE_SESSION'):
                self.full.runtime.require_source_session(self.full.root,alternate)
            with self.assertRaises(ValueError):
                self.full.runtime.require_source_session(foreign,self.full.binding)
        self.assert_revoked()


if __name__=='__main__':unittest.main()
