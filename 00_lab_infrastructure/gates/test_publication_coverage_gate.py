"""Consumer tests use recorded-evidence fixtures and never invoke Lean or SSH."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "00_lab_infrastructure" / "gates"))
sys.path.insert(0, str(REPO / "gates"))
sys.path.insert(0, str(REPO / "scripts"))
from claim_binding import DISCLAIMER, CONJECTURE_LABEL, check_bindings, check_run
from publication_gate import (evaluate_publication, stage_result, UNCERTIFIED_LABEL,
                              require_new_artifact_publication, PublicationGateHold,
                              _premise_required)
from generate_public_index import generate, render_index


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicationCoverageGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "canonical tree"
        self.root.mkdir()
        self.run = self.root / "science-engine/07_nightly_engine/compound research papers/Run-142"
        self.run.mkdir(parents=True)
        self.candidate = self.root / "VERIFICATION_CANDIDATE.lean"
        self.candidate.write_text("theorem meaningful (x : Nat) : x ≤ x + 1 := Nat.le_succ x\n"
                                  "theorem meaningful_witness : ∃ x : Nat, x ≤ x + 1 := ⟨0, Nat.le_succ 0⟩\n")
        self.paper = self.run / "SEALED_paper.tex"
        self.paper.write_text(r"\begin{document}A sealed Methods Note.\end{document}")
        self.pdf = self.run / "SEALED_paper.pdf"
        self.pdf.write_bytes(b"%PDF-test fixture")
        self.cert = self.root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        self.cert.write_text(json.dumps({"issued_at_utc":"2026-01-01T00:00:00Z"}))
        self.expected_candidate_hash = digest(self.candidate)
        self.expected_paper_hash = digest(self.paper)
        self.entry = {"id": "Run-142", "kind": "PAPER", "path": "science-engine/07_nightly_engine/compound research papers/Run-142", "status": "CERTIFIED",
                      "certificate_valid": True, "certificate": self.cert.name,
                      "certified_theorems": ["meaningful"], "nonvacuity": ["meaningful_witness"]}
        self.ledger = {"tree_root": str(self.root), "file_entities": [], "run_entities": [self.entry]}
        self.binding = {"claims": [{"english_claim": "The model successor dominates its input.",
                         "lean_theorem": "meaningful", "nonvacuity_obligation": "meaningful_witness",
                         "model_fidelity": {"defined": ["model_relation"], "empirically_identified": []},
                         "disclaimer": DISCLAIMER}]}
        self.inventory = self.root / "SEALED_CLAIM_INVENTORY.json"
        self.inventory.write_text(json.dumps({"claims": [{"id": "C1", "claim": "The model successor dominates its input.",
            "evidence_class": "FORMAL_TARGET", "aristotle_target": "meaningful"}]}))
        (self.run / "claim_binding.json").write_text(json.dumps(self.binding))
        (self.run / "metadata.json").write_text(json.dumps({"title": "Theorem relation", "description": "Theorem in Canon"}))
        from publication_binding import draft_binding
        receipt = draft_binding(self.run, self.inspected_fixture(self.cert, self.root), self.cert, self.root)
        review = {k:receipt[k] for k in ('certificate','final_manuscript','allowed_diff_sha256')}
        review.update(status='APPROVED_PUBLICATION_BINDING', pdf_correspondence_reviewed=True, scope='VERIFICATION_STATUS_TEXT_ONLY', reviewer={'identity':'independent test reviewer'}, reviewed_at_utc='2026-01-02T00:00:00Z')
        self.review = self.root / 'independent-review.json'
        self.review.write_text(json.dumps(review))
        self.entry['approved_publication_binding_reviews']=[digest(self.review)]
        receipt.update(status='PUBLICATION_BOUND', issued_at_utc='2026-01-03T00:00:00Z', review={'path':str(self.review),'sha256':digest(self.review)})
        (self.run/'PUBLICATION_BINDING.json').write_text(json.dumps(receipt))
        import shutil
        self.generation_root = Path(self.tmp.name)/'author lab'
        self.source = self.generation_root/'07_nightly_engine/compound research papers/Run-142'
        shutil.copytree(self.run, self.source)
        self.ledger['generation_root_parity_only'] = str(self.generation_root)

    def inspected_fixture(self, path, root):
        # Deliberately an injected evidence consumer fixture, never a verifier.
        return {"valid": digest(self.candidate) == self.expected_candidate_hash,
                "reasons": [], "candidate_path": str(self.candidate), "source_run": "Run-142",
                "certified_theorems": ["meaningful"], "nonvacuity": ["meaningful_witness"],
                "sealed_paper_inputs": {"SEALED_paper.pdf": {"path":str(self.pdf), "sha256":digest(self.pdf)}, "SEALED_paper.tex": {"path": str(self.paper), "sha256": self.expected_paper_hash},
                    "SEALED_CLAIM_INVENTORY.json": {"path": str(self.inventory), "sha256": digest(self.inventory)}}}

    def test_certified_bound_claim_positive(self):
        import shutil
        shutil.copytree(self.run, self.source, dirs_exist_ok=True)
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["canon_eligible"])
        self.assertEqual(result["verification_status"], "CERTIFIED")
        self.assertIn(DISCLAIMER, result["proposed_metadata"]["description"])

    def test_premise_cutover_exempts_historical_and_foundational_runs(self):
        self.ledger['premise_declaration_cutover_run'] = 'Run-187'
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['premise_declaration_required'])
        self.assertEqual(result['premise_declaration']['status'], 'EXEMPT')
        for rid, required in [('Run-186', False), ('Run-187', True), ('Run-188', True),
                              ('Run-899', True), ('Run-900', False), ('Run-903', False)]:
            with self.subTest(run=rid):
                self.assertIs(_premise_required(self.ledger, {'run_id':rid}, False), required)

    def test_premise_cutover_holds_a_new_nightly_without_declaration(self):
        self.ledger['premise_declaration_cutover_run'] = 'Run-142'
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture, enforce=True)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(result['premise_declaration_required'])
        self.assertIn('required sealed premise input missing', str(result['reasons']))
        self.assertFalse(result['release_eligible'])
        with self.assertRaises(PublicationGateHold):require_new_artifact_publication(result)

    def test_explicit_premise_requirement_cannot_be_exempted(self):
        with patch('premise_declaration.validate_artifact', return_value={'status':'EXEMPT', 'reasons':[]}) as intake:
            result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture,
                                          require_premise_declaration=True)
        self.assertEqual(result['status'], 'HOLD')
        self.assertTrue(result['premise_declaration_required'])
        self.assertTrue(intake.call_args.kwargs['required'])

    def test_declared_premise_mismatch_is_not_a_historical_exemption(self):
        with patch('premise_declaration.validate_artifact', return_value={
                'status':'HOLD', 'foundation_basis':'THEOREM', 'reasons':['PREMISE_UNDERDECLARED']}):
            result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result['status'], 'HOLD')
        self.assertIn('PREMISE_UNDERDECLARED', str(result['reasons']))

    def test_passing_premise_basis_propagates_without_bypassing_claim_binding(self):
        premise = {'status':'PASS', 'foundation_basis':'CONDITIONAL_PL_PD', 'reasons':[]}
        with patch('premise_declaration.validate_artifact', return_value=premise):
            result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture,
                                          require_premise_declaration=True)
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(result['foundation_basis'], 'CONDITIONAL_PL_PD')
            (self.run/'claim_binding.json').unlink()
            (self.source/'claim_binding.json').unlink()
            result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture,
                                          require_premise_declaration=True)
        self.assertEqual(result['status'], 'HOLD')
        self.assertIn('claim-binding gate', str(result['reasons']))

    def test_malformed_premise_cutover_and_nonboolean_flag_fail_closed(self):
        for cutover in ('Run-0187', 'Run-0', 'Run-900', 187, True, '187'):
            with self.subTest(cutover=cutover):
                self.ledger['premise_declaration_cutover_run'] = cutover
                result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
                self.assertEqual(result['status'], 'HOLD')
                self.assertIn('cutover', str(result['reasons']))
        self.ledger.pop('premise_declaration_cutover_run')
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture,
                                      require_premise_declaration=1)
        self.assertEqual(result['status'], 'HOLD')
        self.assertIn('boolean', str(result['reasons']))

    def test_no_certificate_labels_metadata_but_preserves_title_and_historical_claims(self):
        self.entry.update(status="DEBT", certificate_valid=False, certificate=None)
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["verification_status"], "UNCERTIFIED")
        self.assertEqual(result["proposed_metadata"]["title"], "Theorem relation")
        self.assertIn("Theorem in Canon", result["proposed_metadata"]["description"])
        self.assertEqual(result["proposed_metadata"]["description"].count(UNCERTIFIED_LABEL), 1)
        self.assertIn("Historical description", result["proposed_metadata"]["description"])
        self.assertNotIn(DISCLAIMER, result["proposed_metadata"]["description"])
        self.assertIsNone(result["disclaimer"])
        self.assertEqual(result["proposed_metadata"]["keywords"], ["uncertified"])
        self.assertFalse(result["canon_eligible"])

    def test_report_only_pass_does_not_authorize_new_artifact_release(self):
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["mode"], "REPORT_ONLY")
        self.assertFalse(result["enforcement"])
        self.assertFalse(result["blocking"])
        with self.assertRaises(PublicationGateHold):
            require_new_artifact_publication(result)

    def test_explicit_enforcement_passes_only_current_certificate_binding_and_claims(self):
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture, enforce=True)
        self.assertEqual(result["mode"], "ENFORCING")
        require_new_artifact_publication(result)
        (self.run / "PUBLICATION_BINDING.json").unlink()
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture, enforce=True)
        self.assertTrue(result["blocking"])
        with self.assertRaises(PublicationGateHold):
            require_new_artifact_publication(result)

    def test_held_banner_is_idempotent_and_removes_only_old_leading_gate_text(self):
        self.entry.update(status="DEBT", certificate_valid=False)
        meta = {"title":"Viridis Compiled Theorem Stack — Canon v5", "description":CONJECTURE_LABEL + "\n\n" + DISCLAIMER + "\n\nHistorical scientific claim. Theorem x = y.", "keywords":["conjecture", "model"]}
        (self.run / "metadata.json").write_text(json.dumps(meta))
        first = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        after = first["proposed_metadata"]
        self.assertEqual(after["title"], meta["title"])
        self.assertNotIn(CONJECTURE_LABEL, after["description"])
        self.assertNotIn(DISCLAIMER, after["description"])
        self.assertIn("Theorem x = y.", after["description"])
        (self.run / "metadata.json").write_text(json.dumps(after))
        second = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(after["description"], second["proposed_metadata"]["description"])
        self.assertEqual(after["keywords"], ["model", "uncertified"])

    def test_publication_entity_lookup_does_not_inherit_a_run_approval(self):
        import shutil
        artifact = self.root / "new release"
        shutil.copytree(self.run, artifact)
        entry = {**self.entry, "id":"publication:one", "kind":"PUBLICATION", "run_id":"Run-142", "path":"new release"}
        del entry["approved_publication_binding_reviews"]
        self.ledger["publication_entities"] = [entry]
        result = evaluate_publication(artifact, self.ledger, entity_id=entry["id"], inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("ledger approval", str(result["reasons"]))
        entry["approved_publication_binding_reviews"] = [digest(self.review)]
        result = evaluate_publication(artifact, self.ledger, entity_id=entry["id"], inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "PASS")

    def test_explicit_entity_id_cannot_grant_approval_to_an_unregistered_copy(self):
        import shutil
        artifact = self.root / "unregistered release"
        shutil.copytree(self.run, artifact)
        result = evaluate_publication(artifact, self.ledger, entity_id=self.entry["id"], inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("exactly one ledger entity", str(result["reasons"]))

    def test_publication_entity_run_join_must_equal_its_certificate(self):
        import shutil
        artifact = self.root / "new release"
        shutil.copytree(self.run, artifact)
        entry = {**self.entry, "id":"publication:one", "kind":"PUBLICATION", "run_id":"Run-900", "path":"new release"}
        self.ledger["publication_entities"] = [entry]
        result = evaluate_publication(artifact, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("different run", str(result["reasons"]))

    def test_static_clean_is_insufficient_and_unsound_never_promotes(self):
        for status in ("CLEAN_UNCERTIFIED", "UNSOUND", "HAS_SORRY"):
            self.entry["status"] = status
            result = check_run(self.run, self.ledger, inspector=self.inspected_fixture)
            self.assertEqual(result["status"], "HOLD")

    def test_missing_binding_or_fidelity_downgrades(self):
        (self.run / "claim_binding.json").unlink()
        self.assertEqual(check_run(self.run, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")
        del self.binding["claims"][0]["model_fidelity"]
        self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_exactly_one_theorem_and_certified_witness_required(self):
        for key, value in (("lean_theorem", ["meaningful", "other"]), ("lean_theorem", "other"),
                           ("nonvacuity_obligation", "unproved_witness")):
            original = self.binding["claims"][0][key]
            self.binding["claims"][0][key] = value
            self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")
            self.binding["claims"][0][key] = original

    def test_duplicate_public_claim_rejected(self):
        self.binding["claims"].append(dict(self.binding["claims"][0]))
        self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_missing_or_omitted_sealed_formal_claim_holds(self):
        def missing_inventory(path, root):
            result = self.inspected_fixture(path, root)
            del result["sealed_paper_inputs"]["SEALED_CLAIM_INVENTORY.json"]
            return result
        self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=missing_inventory)["status"], "HOLD")
        inventory = json.loads(self.inventory.read_text())
        inventory["claims"].append({"id": "C2", "claim": "Another public formal claim.",
                                      "evidence_class": "FORMALLY_VERIFIED", "lean_theorem": "meaningful"})
        self.inventory.write_text(json.dumps(inventory))
        self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_empirical_content_is_separate_and_never_empirically_certified(self):
        inventory = json.loads(self.inventory.read_text())
        inventory["claims"].append({"id": "C2", "claim": "An observed empirical trend.", "evidence_class": "NUMERIC"})
        self.inventory.write_text(json.dumps(inventory))
        import shutil
        shutil.copytree(self.run, self.source, dirs_exist_ok=True)
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "PASS")
        item = result["proposed_metadata"]["unverified_claims"][0]
        self.assertEqual(item["verification_status"], "NOT_FORMALLY_VERIFIED")
        self.assertEqual(item["empirical_validation"], "NOT_ESTABLISHED_BY_LEAN_CERTIFICATE")
        self.assertIn("Not formally verified", result["proposed_metadata"]["description"])

    def test_exact_disclaimer_required(self):
        self.binding["claims"][0]["disclaimer"] = "A weaker paraphrase"
        self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_nonvacuity_sorry_and_true_conclusion_rejected(self):
        for source in ("theorem meaningful : True := trivial\n",
                       "theorem meaningful_witness : ∃ x : Nat, x ≤ x := by sorry\n",
                       "theorem meaningful : ∃ x : Nat, True := ⟨0, trivial⟩\n"):
            self.candidate.write_text(source)
            self.expected_candidate_hash = digest(self.candidate)
            self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_obvious_unsatisfiable_hypotheses_rejected(self):
        for source in ("theorem meaningful (h : False) : 0 = 1 := False.elim h\n",
                       "theorem meaningful (x : Nat) (h : x < x) : x = x := rfl\n"):
            self.candidate.write_text(source)
            self.expected_candidate_hash = digest(self.candidate)
            self.assertEqual(check_bindings(self.binding, self.entry, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_timeout_and_missing_inspector_fail_closed(self):
        def timeout(*args):
            raise TimeoutError("receipt unavailable")
        result = check_run(self.run, self.ledger, inspector=timeout)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["verification_status"], "CONJECTURE")

    def test_one_byte_candidate_and_paper_tamper_fail_closed(self):
        self.candidate.write_text(self.candidate.read_text() + " ")
        self.assertEqual(evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")
        self.expected_candidate_hash = digest(self.candidate)
        self.paper.write_text(self.paper.read_text() + " ")
        self.assertEqual(evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)["status"], "HOLD")

    def test_report_and_enforcement_never_change_published_doi(self):
        self.entry["doi"] = "10.5281/zenodo.123"
        before = {p.name: p.read_bytes() for p in self.run.iterdir() if p.is_file()}
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        preview = Path(self.tmp.name) / "preview"
        stage_result(result, preview)
        self.assertFalse((preview / "metadata.json").exists())
        stage_result(result, preview, enforce=True)
        after = {p.name: p.read_bytes() for p in self.run.iterdir() if p.is_file()}
        self.assertEqual(before, after)
        self.assertTrue(result["published_doi_requires_human_decision"])

    def test_ledger_generated_index_reverts_manual_change(self):
        self.ledger["file_entities"] = [{"id": "origin", "path": "00_ORIGIN/paper/proof.lean", "status": "UNSOUND"}]
        self.ledger["run_entities"].append({"id": "Run-META-001", "path": "Run-META-001_canon-synthesis", "kind": "SYNTHESIS", "status": "NO_FORMALIZATION"})
        ledger_path = Path(self.tmp.name) / "corpus_ledger.json"
        ledger_path.write_text(json.dumps(self.ledger))
        output = Path(self.tmp.name) / "public"
        generate(ledger_path, output, inspector=self.inspected_fixture)
        first = (output / "README.md").read_bytes()
        (output / "README.md").write_text("A manually asserted membership that bypasses the ledger")
        generate(ledger_path, output, inspector=self.inspected_fixture)
        self.assertEqual((output / "README.md").read_bytes(), first)
        canon = json.loads((output / "CANON_INDEX.json").read_text())
        self.assertEqual([item["id"] for item in canon["entries"]], ["Run-142"])
        self.assertEqual(canon["quarantined"], ["origin"])
        self.assertNotIn("Run-META-001", [item["id"] for item in canon["entries"]])

    def test_report_only_generation_cannot_write_scanned_tree(self):
        path = Path(self.tmp.name) / "ledger.json"
        path.write_text(json.dumps(self.ledger))
        with self.assertRaises(ValueError):
            generate(path, self.root, inspector=self.inspected_fixture)

    def test_invalid_status_partition_holds_before_generation(self):
        self.entry["status"] = ["CERTIFIED", "DEBT"]
        with self.assertRaises((ValueError, TypeError)):
            render_index(self.ledger, inspector=self.inspected_fixture)


if __name__ == "__main__":
    unittest.main()
