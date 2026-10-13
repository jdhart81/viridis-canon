"""One-operation scan DATA and actual-byte guards; no production admission."""
from copy import deepcopy
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import packaging_catalog as catalog
import packaging_runtime as runtime
import test_packaging_default_routes as default_fixtures

class ScientificDataGuardTests(unittest.TestCase):
    def inputs(self,base):
        root=base/'canonical';root.mkdir();mirror=base/'science';mirror.mkdir()
        certs=root/'certificates';certs.mkdir();papers=root/'science-engine/07_nightly_engine/compound research papers';papers.mkdir(parents=True)
        paths=[root/'proof.lean',certs/'certificate.json',papers/'Run-001/paper.pdf',root/'review.json',mirror/'nightly_reviews/review.json',
               mirror/'07_nightly_engine/compound research papers/Run-001/paper.pdf']
        for i,p in enumerate(paths):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(('input-'+str(i)).encode())
        ctx=SimpleNamespace()
        corpus=SimpleNamespace(discover=lambda r:(sorted(r.rglob('*.lean')),[],[]),GENERATION_ROOT=mirror)
        return root,mirror,certs,papers,paths,ctx,corpus
    def scope(self,root,ctx):
        stack=contextlib.ExitStack();stack.enter_context(patch.object(catalog,'checked_context',return_value=ctx))
        stack.enter_context(catalog.operation_scope(root,{'explicit_fixture':True},ctx));return stack
    def test_every_actual_lean_certificate_paper_review_and_sibling_mirror_byte_is_guarded(self):
        for changed in range(6):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory()as tmp:
                root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
                with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_CHANGED'):
                    with self.scope(root,ctx):
                        data=catalog.scientific_data(root);data.capture_inventory(corpus,certs)
                        for p in paths:p.read_bytes()
                        self.assertEqual(set(data.inputs),{str(p)for p in paths})
                        paths[changed].write_bytes(b'changed actual input')
                        catalog.observation_guard(ctx)
                self.assertIsNone(catalog._READ_CAPTURE.get());self.assertIsNone(catalog._SCIENCE.get())
    def test_lean_cert_paper_and_sibling_inventory_additions_hold_without_hiding_new_inputs(self):
        for kind in ('lean','certificate','paper','mirror-review','mirror-run'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory()as tmp:
                root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
                with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                    with self.scope(root,ctx):
                        data=catalog.scientific_data(root);data.capture_inventory(corpus,certs)
                        target={'lean':root/'new.lean','certificate':certs/'new.json','paper':papers/'Run-999/paper.pdf',
                                'mirror-review':mirror/'nightly_reviews/new.json','mirror-run':mirror/'07_nightly_engine/compound research papers/Run-999/paper.pdf'}[kind]
                        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'new real input')
                        catalog.observation_guard(ctx)
    def test_added_file_empty_directory_or_symlink_inside_existing_actual_run_holds(self):
        for side in ('canonical','source'):
            for kind in ('paper','empty-directory','symlink'):
                with self.subTest(side=side,kind=kind),tempfile.TemporaryDirectory()as tmp:
                    root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
                    run=(papers if side=='canonical'else mirror/'07_nightly_engine/compound research papers')/'Run-001'
                    with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                        with self.scope(root,ctx):
                            data=catalog.scientific_data(root);data.capture_inventory(corpus,certs)
                            for p in paths:p.read_bytes()
                            target=run/'new-entry'
                            if kind=='paper':target.write_bytes(b'new actual paper')
                            elif kind=='empty-directory':target.mkdir()
                            else:target.symlink_to(run/'paper.pdf')
                            catalog.observation_guard(ctx)
    def test_existing_registered_non_run_artifact_membership_includes_absent_optional_claims(self):
        for name in ('claim_binding.json','SCOPED_RELEASE_MANIFEST.json','second-paper.pdf','second-paper.tex'):
            with self.subTest(name=name),tempfile.TemporaryDirectory()as tmp:
                root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
                artifact=root/'reports/reviewed-release/22236409';artifact.mkdir(parents=True);(artifact/'paper.pdf').write_bytes(b'original paper')
                canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';canonical.parent.mkdir()
                canonical.write_text(json.dumps({'publication_entities':[{'path':str(artifact.relative_to(root))}]}))
                with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                    with self.scope(root,ctx):
                        data=catalog.scientific_data(root);data.capture_inventory(corpus,certs,{'publication_entities':[]})
                        (artifact/'paper.pdf').read_bytes();(artifact/name).write_bytes(b'new actual optional scientific input')
                        catalog.observation_guard(ctx)
    def test_new_intake_artifact_is_guarded_without_replacing_the_old_scientific_predecessor(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();fixture=default_fixtures.DefaultRouteIntegration();previous,original,ctx,calls,labels,old,imports=fixture.fixture(root)
            release=root/'reports/intake-new-release';release.mkdir(parents=True)
            (release/'paper.pdf').write_bytes(b'exact new copied manuscript')
            audit=release/'registration_audit';audit.mkdir();(audit/'corpus_ledger_before.json').write_text(json.dumps(previous))
            proposed={**deepcopy(previous),'publication_entities':[*previous['publication_entities'],{'path':str(release.relative_to(root))}]}
            with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                with fixture.scope(root,ctx,old,imports):
                    classified=catalog.build(root,root/'certs',previous,{},registry_context=ctx,inventory_publications=proposed)
                    self.assertEqual(classified['publication_entities'],previous['publication_entities'])
                    catalog.observation_guard(ctx)
                    (release/'second-paper.pdf').write_bytes(b'unapproved new manuscript after scan')
                    catalog.observation_guard(ctx)
    def test_identical_bytes_behind_replaced_inode_or_symlink_do_not_reuse_old_data(self):
        for mode in ('replace','symlink'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory()as tmp:
                root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve());p=paths[0]
                with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT'):
                    with self.scope(root,ctx):
                        p.read_bytes();raw=p.read_bytes();p.unlink()
                        if mode=='replace':p.write_bytes(raw)
                        else:
                            other=root/'other.lean';other.write_bytes(raw);p.symlink_to(other)
                        catalog.observation_guard(ctx)
    def test_observer_is_inert_after_failure_and_a_new_scope_has_new_input_data(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
            with self.assertRaisesRegex(RuntimeError,'fixture failure'):
                with self.scope(root,ctx):
                    paths[0].read_bytes();old=catalog.scientific_data(root);raise RuntimeError('fixture failure')
            paths[1].read_bytes();self.assertNotIn(str(paths[1]),old.inputs)
            self.assertIsNone(catalog._READ_CAPTURE.get());self.assertIsNone(catalog._SCIENCE.get())
            with self.scope(root,ctx):
                fresh=catalog.scientific_data(root);self.assertIsNot(fresh,old);self.assertEqual(fresh.inputs,{})
    def test_read_descriptor_requires_the_actual_preceding_path_open_in_this_scope(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
            with self.scope(root,ctx):
                fd=os.open(paths[0],os.O_RDONLY)
                with os.fdopen(fd,'rb')as stream:self.assertEqual(stream.read(),b'input-0')
            inherited=os.open(paths[1],os.O_RDONLY)
            try:
                with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_UNBOUND_READ_DESCRIPTOR'):
                    with self.scope(root,ctx):
                        os.fdopen(inherited,'rb',closefd=False)
            finally:os.close(inherited)
    def test_doi_or_labels_cannot_substitute_a_saved_scan_for_current_operation(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
            with self.scope(root,ctx),patch.object(runtime,'session',side_effect=lambda *a,**kw:contextlib.nullcontext()):
                for action in (lambda:catalog.augment_audit(root,{'file_entities':'saved'}, {},registry_context=ctx),
                               lambda:catalog.public_label_readback(root,{'published_records':[]}, {},registry_context=ctx)):
                    with self.assertRaisesRegex(runtime.PackagingHold,'FRESH_COMPLETE_OPERATIONAL_SCAN_REQUIRED'):action()
    def test_only_verified_canonical_cas_can_rebind_one_input_and_other_changes_hold(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,mirror,certs,papers,paths,ctx,corpus=self.inputs(Path(tmp).resolve())
            canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';canonical.parent.mkdir();canonical.write_text('{"before":true}')
            with self.scope(root,ctx):
                data=catalog.scientific_data(root);data.capture_inventory(corpus,certs);canonical.read_bytes();paths[0].read_bytes()
                data.scan_data={'explicit_classification_fixture':True};before=runtime.sha(canonical.read_bytes());new={'after':True}
                catalog.authorize_canonical_write(canonical,new,before);default_fixtures.real_cas()(canonical,new,before);catalog.finish_canonical_write(root)
                self.assertEqual(json.loads(canonical.read_bytes()),new);self.assertEqual(len(data.cas_events),1);catalog.observation_guard(ctx)
            with self.assertRaisesRegex(runtime.PackagingHold,'SCIENTIFIC_INPUT_CHANGED'):
                with self.scope(root,ctx):
                    paths[0].read_bytes();paths[0].write_text('unapproved mutation');catalog.observation_guard(ctx)
    def test_one_original_complete_scan_data_reuse_replays_all_92_rows_and_fresh_registrations(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();fixture=default_fixtures.DefaultRouteIntegration();previous,original,ctx,calls,labels,old,imports=fixture.fixture(root)
            more=[{**deepcopy(original[0]),'id':'publication:additional:'+str(i),'path':'extra/'+str(i)}for i in range(54)]
            previous['publication_entities']=[*original,*more,*previous['publication_entities'][35:]]
            self.assertEqual(len(previous['publication_entities']),92)
            proof=root/'source.lean';proof.write_bytes(b'constant guarded source')
            corp=imports('corpus_ledger');original_build=corp.build;count=[]
            def scan(*a,**kw):count.append('complete-original-scan');proof.read_bytes();return original_build(*a,**kw)
            corp.build=scan
            with fixture.scope(root,ctx,old,imports):
                first=catalog.build(root,root/'certs',previous,{},registry_context=ctx)
                second=catalog.build(root,root/'certs',previous,{},registry_context=ctx)
                self.assertEqual(first['publication_entities'],previous['publication_entities'])
                self.assertEqual(second['publication_entities'],previous['publication_entities'])
                self.assertEqual(count,['complete-original-scan'])
                self.assertEqual(sum(1 for kind,row in calls if kind=='consume'),4)
                self.assertEqual(catalog.scientific_data(root).inputs[str(proof)]['sha256'],runtime.sha(proof.read_bytes()))
            self.assertIsNone(catalog._READ_CAPTURE.get())

if __name__=='__main__':unittest.main()
