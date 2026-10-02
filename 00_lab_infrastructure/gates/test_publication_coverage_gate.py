"""Consumer tests use recorded-evidence fixtures and never invoke Lean or SSH."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "00_lab_infrastructure" / "gates"))
sys.path.insert(0, str(REPO / "gates"))
sys.path.insert(0, str(REPO / "scripts"))
from claim_binding import DISCLAIMER, CONJECTURE_LABEL, check_bindings, check_run
from publication_gate import evaluate_publication, stage_result
from generate_public_index import generate, render_index


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PublicationCoverageGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "canonical tree"
        self.root.mkdir()
        self.run = self.root / "Run-142"
        self.run.mkdir()
        self.candidate = self.root / "VERIFICATION_CANDIDATE.lean"
        self.candidate.write_text("theorem meaningful (x : Nat) : x ≤ x := le_rfl\n"
                                  "theorem meaningful_witness : ∃ x : Nat, x ≤ x := ⟨0, le_rfl⟩\n")
        self.paper = self.run / "SEALED_paper.tex"
        self.paper.write_text("A sealed Methods Note, not a fabricated research paper.")
        self.cert = self.root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        self.cert.write_text("{}")
        self.expected_candidate_hash = digest(self.candidate)
        self.expected_paper_hash = digest(self.paper)
        self.entry = {"id": "Run-142", "kind": "PAPER", "path": "Run-142", "status": "CERTIFIED",
                      "certificate_valid": True, "certificate": self.cert.name,
                      "certified_theorems": ["meaningful"], "nonvacuity": ["meaningful_witness"]}
        self.ledger = {"tree_root": str(self.root), "file_entities": [], "run_entities": [self.entry]}
        self.binding = {"claims": [{"english_claim": "The model relation is reflexive.",
                         "lean_theorem": "meaningful", "nonvacuity_obligation": "meaningful_witness",
                         "model_fidelity": {"defined": ["model_relation"], "empirically_identified": []},
                         "disclaimer": DISCLAIMER}]}
        self.inventory = self.root / "SEALED_CLAIM_INVENTORY.json"
        self.inventory.write_text(json.dumps({"claims": [{"id": "C1", "claim": "The model relation is reflexive.",
            "evidence_class": "FORMAL_TARGET", "aristotle_target": "meaningful"}]}))
        (self.run / "claim_binding.json").write_text(json.dumps(self.binding))
        (self.run / "metadata.json").write_text(json.dumps({"title": "Theorem relation", "description": "Theorem in Canon"}))

    def inspected_fixture(self, path, root):
        # Deliberately an injected evidence consumer fixture, never a verifier.
        return {"valid": digest(self.candidate) == self.expected_candidate_hash,
                "reasons": [], "candidate_path": str(self.candidate), "source_run": "Run-142",
                "certified_theorems": ["meaningful"], "nonvacuity": ["meaningful_witness"],
                "sealed_paper_inputs": {"SEALED_paper.tex": {"path": str(self.paper), "sha256": self.expected_paper_hash},
                    "SEALED_CLAIM_INVENTORY.json": {"path": str(self.inventory), "sha256": digest(self.inventory)}}}

    def test_certified_bound_claim_positive(self):
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["canon_eligible"])
        self.assertEqual(result["verification_status"], "CERTIFIED")
        self.assertIn(DISCLAIMER, result["proposed_metadata"]["description"])

    def test_no_certificate_downgrades_title_abstract_and_metadata(self):
        self.entry.update(status="DEBT", certificate_valid=False, certificate=None)
        result = evaluate_publication(self.run, self.ledger, inspector=self.inspected_fixture)
        self.assertEqual(result["verification_status"], "CONJECTURE")
        self.assertTrue(result["proposed_metadata"]["title"].startswith(CONJECTURE_LABEL))
        self.assertNotIn("Theorem", result["proposed_metadata"]["title"])
        self.assertNotIn("Canon", result["proposed_metadata"]["description"])
        self.assertFalse(result["canon_eligible"])

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
