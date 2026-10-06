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


class PremiseBindingTests(BindingTests):
    def declare(self):
        from premise_declaration import _aligner
        from publication_binding import draft_binding,sha
        f=self.f
        f.paper.write_text(r'\begin{document}\begin{abstract}INDEPENDENT: model successor ordering.\end{abstract}\end{document}')
        f.expected_paper_hash=sha(f.paper)
        f.candidate.write_text(f.candidate.read_text().replace(':= Nat.le_succ x',':= by\n  exact Nat.le_succ x').replace(':= ⟨0, Nat.le_succ 0⟩',':= by\n  exact ⟨0, Nat.le_succ 0⟩'))
        f.expected_candidate_hash=sha(f.candidate)
        formal=f.root/'formal.lean';formal.write_text(_aligner().align_challenge(f.candidate.read_text(),f.candidate.read_text(),['meaningful','meaningful_witness'])[0])
        manifest=f.root/'SEALED_RUN_MANIFEST.json';manifest.write_text(json.dumps({'foundation_basis':'INDEPENDENT'}))
        inventory=json.loads(f.inventory.read_text());inventory['foundation_basis']='INDEPENDENT';f.inventory.write_text(json.dumps(inventory))
        bound=lambda p:{'path':str(p),'sha256':sha(p)}
        sealed={p.name:bound(p) for p in [f.paper,f.pdf,f.inventory,manifest]}
        cert={'issued_at_utc':'2026-01-01T00:00:00Z','foundation_basis':'INDEPENDENT',
              'bindings':{'sealed_paper_inputs':sealed,'formal_statement':bound(formal),'candidate_proof':bound(f.candidate)}}
        f.cert.write_text(json.dumps(cert))
        receipt=draft_binding(f.run,f.inspected_fixture(f.cert,f.root),f.cert,f.root)
        review={k:receipt[k] for k in ('certificate','final_manuscript','allowed_diff_sha256')}
        review.update(status='APPROVED_PUBLICATION_BINDING',pdf_correspondence_reviewed=True,scope='VERIFICATION_STATUS_TEXT_ONLY',reviewer={'identity':'independent test reviewer'},reviewed_at_utc='2026-01-02T00:00:00Z')
        f.review.write_text(json.dumps(review));f.entry['approved_publication_binding_reviews']=[sha(f.review)]
        receipt.update(status='PUBLICATION_BOUND',issued_at_utc='2026-01-03T00:00:00Z',review={'path':str(f.review),'sha256':sha(f.review)})
        (f.run/'PUBLICATION_BINDING.json').write_text(json.dumps(receipt))
        return receipt

    def test_basis_in_new_binding_and_gate_result(self):
        receipt=self.declare();self.assertEqual(receipt['foundation_basis'],'INDEPENDENT')
        result=self.result();self.assertEqual(result['status'],'PASS',result)
        self.assertEqual(result['foundation_basis'],'INDEPENDENT')

    def test_omitted_or_changed_binding_basis_holds(self):
        for value in [None,'THEOREM']:
            receipt=self.declare()
            if value is None:receipt.pop('foundation_basis')
            else:receipt['foundation_basis']=value
            (self.f.run/'PUBLICATION_BINDING.json').write_text(json.dumps(receipt))
            self.assertEqual(self.result()['status'],'HOLD')

    def test_declared_sealed_basis_without_certificate_basis_holds(self):
        self.declare();cert=json.loads(self.f.cert.read_text());cert.pop('foundation_basis');self.f.cert.write_text(json.dumps(cert))
        self.assertEqual(self.result()['status'],'HOLD')
