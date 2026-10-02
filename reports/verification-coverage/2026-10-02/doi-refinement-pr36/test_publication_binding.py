"""Regression checks for a report-only exact manuscript binding consumer."""
import json
import shutil
import unittest
from pathlib import Path
from manuscript_structure import classify
from publication_gate import evaluate_publication
import test_publication_coverage_gate as fixtures

class BindingTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.PublicationCoverageGateTests(methodName='test_certified_bound_claim_positive');self.f.setUp();self.addCleanup(self.f.doCleanups)
    def result(self):
        shutil.copytree(self.f.run,self.f.source,dirs_exist_ok=True)
        return evaluate_publication(self.f.run,self.f.ledger,inspector=self.f.inspected_fixture)
    def test_missing_receipt_even_identical_paper_holds(self):
        (self.f.run/'PUBLICATION_BINDING.json').unlink();(self.f.source/'PUBLICATION_BINDING.json').unlink()
        self.assertEqual(self.result()['status'],'HOLD')
    def test_self_authored_review_has_no_authority(self):
        self.f.entry['approved_publication_binding_reviews']=[]
        self.assertEqual(self.result()['status'],'HOLD')
    def test_review_mutation_holds(self):
        self.f.review.write_text(self.f.review.read_text()+' ')
        self.assertEqual(self.result()['status'],'HOLD')
    def test_pdf_one_byte_mutation_holds_even_tex_unchanged(self):
        self.f.pdf.write_bytes(self.f.pdf.read_bytes()+b' ')
        self.assertEqual(self.result()['status'],'HOLD')
    def test_receipt_before_certification_holds(self):
        p=self.f.run/'PUBLICATION_BINDING.json';r=json.loads(p.read_text());r['issued_at_utc']='2025-01-01T00:00:00Z';p.write_text(json.dumps(r))
        self.assertEqual(self.result()['status'],'HOLD')

class StructureTests(unittest.TestCase):
    def paper(self,text):return r'\begin{document}'+text+r'\end{document}'
    def test_status_only_preserves_science(self):
        a=self.paper('The rate is $r=2$.\n\nFormal status remains uncertified until Comparator accepts the exact bytes.')
        b=self.paper('The rate is $r=2$.\n\nComparator certified the exact frozen Lean statements.')
        self.assertEqual(classify(a,b)['classification'],'VERIFICATION_STATUS_ONLY')
    def test_equation_inside_certification_sentence_never_masked(self):
        a=self.paper('Comparator has not certified $r=2$.');b=self.paper('Comparator certified $r=3$.')
        self.assertEqual(classify(a,b)['classification'],'CONTENT_CHANGED')
    def test_added_model_premise_cannot_be_status_only(self):
        a=self.paper('Formal status remains uncertified.');b=self.paper('Comparator certification assumes nonnegative time and feasible workloads.')
        self.assertEqual(classify(a,b)['classification'],'CONTENT_CHANGED')
    def test_scientific_sentence_mixed_with_lean_remains_protected(self):
        a=self.paper('The result is a bound on capacity; Lean certification remains unassessed.')
        b=self.paper('The result is an equality of capacity; Lean certification is complete.')
        self.assertEqual(classify(a,b)['classification'],'CONTENT_CHANGED')
    def test_malformed_tex_holds(self):
        self.assertEqual(classify('no boundaries',self.paper('Formal status is certified.'))['status'],'HOLD')

class RepairProvenanceTests(unittest.TestCase):
    def test_repair_join_hash_bound_and_one_byte_divergence_holds(self):
        import tempfile
        from doi_refinement import repair_join, sha
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();original=root/'original';repair=root/'repair';original.mkdir();repair.mkdir()
            (original/'proof.lean').write_text('frozen old proof');shutil.copy2(original/'proof.lean',repair/'proof.lean');digest=sha(original/'proof.lean')
            manifest={'source_bundle':str(original),'predecessor_doi':'10.5281/zenodo.1','science_changed':False,'protected_unchanged_files':['proof.lean'],'original_sha256':{'proof.lean':digest},'candidate_sha256':{'proof.lean':digest}}
            (repair/'CORRECTION_MANIFEST.json').write_text(json.dumps(manifest))
            item={'deposit_paths':[str(repair)]};records={'10.5281/zenodo.1':{'deposit_paths':[str(original)],'run_ids':['Run-126']}}
            self.assertEqual(repair_join(item,records,root)[0],['Run-126'])
            (repair/'proof.lean').write_bytes((repair/'proof.lean').read_bytes()+b' ')
            with self.assertRaises(ValueError):repair_join(item,records,root)

if __name__=='__main__':unittest.main()
