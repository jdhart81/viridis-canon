"""Synthetic forward-seal regressions; no manuscript payload, Lean or network."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import generation_premise_guard as guard
from test_premise_declaration import INDEPENDENT, THEOREM, CONDITIONAL

CASES = {"INDEPENDENT": (INDEPENDENT, "independent_target"),
         "THEOREM": (THEOREM, "intelligence_bound"),
         "CONDITIONAL_PL_PD": (CONDITIONAL, "product_form_fixture")}


def inputs(basis):
    source, target = CASES[basis]
    formal = guard._premise()._aligner().align_challenge(source, source, [target])[0]
    paper = r"\begin{document}\begin{abstract}Synthetic scope only.\end{abstract}\end{document}"
    return {"manifest": {"foundation_basis": basis}, "inventory": {"foundation_basis": basis},
            "formal_statement": formal, "candidate": source,
            "paper_text": guard.declare_abstract(paper, basis), "theorem_names": [target]}


class ForwardPremiseTests(unittest.TestCase):
    def test_every_allowed_actual_basis_is_declared_in_abstract_and_passes_unchanged_checker(self):
        self.assertEqual(guard.BASES, guard._premise().BASES)
        for basis in guard.BASES:
            with self.subTest(basis=basis):
                value = inputs(basis)
                result = guard.require_premise(**value)
                self.assertEqual(result["foundation_basis"], basis)
                self.assertEqual(result["status"], "PASS")
                self.assertFalse(result["certifies"])
                self.assertFalse(result["local_lean_execution"])
                self.assertNotIn("Intelligence Bound", guard.basis_sentence("INDEPENDENT"))

    def test_independent_negative_disclaimer_is_rejected_without_erasing_its_text(self):
        paper = r"\begin{document}\begin{abstract}The Intelligence Bound is not used.\end{abstract}\end{document}"
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "FORBIDDEN_PHRASE"):
            guard.declare_abstract(paper, "INDEPENDENT")
        self.assertIn("Intelligence Bound", paper)

    def test_unknown_mismatched_or_body_only_basis_is_not_accepted(self):
        value = inputs("INDEPENDENT")
        for replacement in ("UNKNOWN", "THEOREM", None):
            with self.subTest(basis=replacement), self.assertRaises(guard.GenerationPremiseHold):
                guard.require_premise(**{**value, "manifest": {"foundation_basis": replacement}})
        body_only = r"\begin{document}\begin{abstract}Synthetic result.\end{abstract}The foundation basis is INDEPENDENT.\end{document}"
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "FIRST_ABSTRACT"):
            guard.require_premise(**{**value, "paper_text": body_only})

    def test_conflicting_existing_abstract_basis_is_not_silently_rewritten(self):
        value = inputs("THEOREM")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "FIRST_ABSTRACT"):
            guard.declare_abstract(value["paper_text"], "INDEPENDENT")

    def test_quoted_multiple_or_missing_abstract_cannot_supply_basis(self):
        for paper in ("no abstract", r"\begin{document}\begin{quote}\begin{abstract}INDEPENDENT\end{abstract}",
                      r"\begin{document}\begin{abstract}a\end{abstract}\begin{abstract}b\end{abstract}"):
            with self.subTest(paper=paper), self.assertRaises(guard.GenerationPremiseHold):
                guard.declare_abstract(paper, "INDEPENDENT")

    def test_conditional_basis_requires_named_premises_in_first_abstract(self):
        value = inputs("CONDITIONAL_PL_PD")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "CONDITIONAL_ABSTRACT"):
            guard.require_premise(**{**value, "paper_text": value["paper_text"].replace("conditional on premises PL and PD", "qualified elsewhere")})

    def test_underdeclared_source_still_fails_the_unchanged_inv9_predicate(self):
        independent = inputs("INDEPENDENT"); conditional = inputs("CONDITIONAL_PL_PD")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "HOLD_PREMISE"):
            guard.require_premise(**{**conditional, "manifest": independent["manifest"],
                "inventory": independent["inventory"], "paper_text": independent["paper_text"]})

    def test_wrong_theorem_reference_and_missing_conditional_premise_still_hold(self):
        theorem = inputs("THEOREM"); independent = inputs("INDEPENDENT")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "HOLD_PREMISE"):
            guard.require_premise(**{**independent, "manifest": theorem["manifest"],
                "inventory": theorem["inventory"], "paper_text": theorem["paper_text"]})
        conditional = inputs("CONDITIONAL_PL_PD")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "HOLD_PREMISE"):
            guard.require_premise(**{**conditional, "candidate": conditional["candidate"].replace("(PL : R_obs * K ≤ P) ", "")})

    def test_required_true_is_unconditionally_forwarded_and_exemption_does_not_pass(self):
        checker = guard._premise(); actual = checker.evaluate
        with patch.object(guard, "_premise", return_value=checker), patch.object(checker, "evaluate", wraps=actual) as call:
            guard.require_premise(**inputs("INDEPENDENT"))
            self.assertIs(call.call_args.kwargs["required"], True)
        with patch.object(checker, "evaluate", return_value={"status": "EXEMPT"}), patch.object(guard, "_premise", return_value=checker):
            with self.assertRaises(guard.GenerationPremiseHold):
                guard.require_premise(**inputs("INDEPENDENT"))

    def test_declaration_is_idempotent_and_checker_hashes_are_unchanged(self):
        value = inputs("INDEPENDENT")
        self.assertEqual(guard.declare_abstract(value["paper_text"], "INDEPENDENT"), value["paper_text"])
        here = Path(guard.__file__).parent
        self.assertEqual(hashlib.sha256((here / "premise_declaration.py").read_bytes()).hexdigest(), guard.PREMISE_SHA256)
        self.assertEqual(hashlib.sha256((here / "inv9_title_basis.py").read_bytes()).hexdigest(), guard.TITLE_SHA256)

    def test_formal_basis_wording_has_the_same_explicit_actual_basis_meaning(self):
        for basis in guard.BASES:
            with self.subTest(basis=basis):
                value = inputs(basis)
                value["paper_text"] = value["paper_text"].replace("foundation basis", "Formal basis")
                self.assertEqual(guard.require_premise(**value)["status"], "PASS")

    def test_macro_quote_literal_and_conditional_examples_are_not_author_declarations(self):
        value = inputs("INDEPENDENT")
        for hidden in (r"\newcommand{\unusedbasis}{The formal basis is INDEPENDENT.}",
                       r"\begin{quote}The formal basis is INDEPENDENT.\end{quote}",
                       r"\begin{verbatim}The formal basis is INDEPENDENT.\end{verbatim}",
                       r"\iffalse The formal basis is INDEPENDENT.\fi",
                       r"\phantom{The formal basis is INDEPENDENT.}"):
            paper = r"\begin{document}\begin{abstract}" + hidden + r" Synthetic result.\end{abstract}\end{document}"
            with self.subTest(hidden=hidden), self.assertRaisesRegex(guard.GenerationPremiseHold, "VISIBLE_MAIN_ABSTRACT"):
                guard.require_premise(**{**value, "paper_text": paper})

    def test_declaration_starts_first_visible_abstract_paragraph(self):
        value = inputs("INDEPENDENT")
        layout = value["paper_text"].replace(r"\begin{abstract}", r"\begin{abstract}\sloppy\noindent")
        self.assertEqual(guard.require_premise(**{**value, "paper_text": layout})["status"], "PASS")
        delayed = value["paper_text"].replace(r"\begin{abstract}", r"\begin{abstract}A quotation follows. ")
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "FIRST_ABSTRACT"):
            guard.require_premise(**{**value, "paper_text": delayed})

    def test_approved_nested_formal_basis_formatting_is_a_visible_declaration(self):
        value = inputs("INDEPENDENT")
        paper = value["paper_text"].replace(guard.basis_sentence("INDEPENDENT"), r"\textbf{Formal basis: \texttt{INDEPENDENT}.} No framework-level bound or PL/PD premise is used.")
        self.assertEqual(guard.require_premise(**{**value, "paper_text": paper})["status"], "PASS")


class StagedBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(); self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve(); self.stage = self.root / "staged"; self.stage.mkdir()
        (self.stage / "formalization").mkdir()
        self.value = inputs("INDEPENDENT"); self.manifest = self.value["manifest"]
        rows = {"CLAIM_INVENTORY.json": json.dumps(self.value["inventory"]),
                "paper.tex": self.value["paper_text"],
                "formalization/STATEMENT_CONTRACT.json": json.dumps({"foundation_basis": "INDEPENDENT", "expected_theorem_names": self.value["theorem_names"], "nonvacuity_obligations": []}),
                "formalization/VERIFICATION_STATEMENT.lean": self.value["formal_statement"],
                "formalization/VERIFICATION_CANDIDATE.lean": self.value["candidate"]}
        for name, text in rows.items(): (self.stage / name).write_text(text)
        self.state = self.root / "state.json"; self.state.write_text('{"run": 1}\n')
        self.live = self.root / "Run-002"

    def commit(self):
        # The exact ordering proposed for seal/finalize/commit: a fresh check
        # precedes both the first sealed write and the actual rename/state write.
        guard.require_staged_premise(self.stage, self.manifest)
        (self.stage / "RUN_MANIFEST.json").write_text(json.dumps(self.manifest))
        guard.require_staged_premise(self.stage, self.manifest)
        os.replace(self.stage, self.live)
        self.state.write_text('{"run": 2}\n')

    def test_failure_precedes_sealed_write_rename_and_state_advance(self):
        before = self.state.read_bytes()
        (self.stage / "paper.tex").write_text(self.value["paper_text"].replace("Synthetic scope", "The Intelligence Bound is not used. Synthetic scope"))
        with self.assertRaises(guard.GenerationPremiseHold): self.commit()
        self.assertFalse((self.stage / "RUN_MANIFEST.json").exists())
        self.assertFalse(self.live.exists()); self.assertEqual(self.state.read_bytes(), before)

    def test_stale_pass_cannot_authorize_changed_candidate(self):
        guard.require_staged_premise(self.stage, self.manifest)
        (self.stage / "formalization/VERIFICATION_CANDIDATE.lean").write_text("axiom invented : False\n")
        with self.assertRaises(guard.GenerationPremiseHold): self.commit()
        self.assertFalse(self.live.exists()); self.assertEqual(self.state.read_text(), '{"run": 1}\n')

    def test_valid_static_premise_inputs_allow_the_synthetic_transaction_only(self):
        self.commit()
        self.assertTrue((self.live / "RUN_MANIFEST.json").is_file())
        self.assertEqual(self.state.read_text(), '{"run": 2}\n')

    def test_missing_input_or_mismatched_frozen_contract_cannot_seal(self):
        contract = self.stage / "formalization/STATEMENT_CONTRACT.json"
        data = json.loads(contract.read_text()); data["foundation_basis"] = "THEOREM"; contract.write_text(json.dumps(data))
        with self.assertRaisesRegex(guard.GenerationPremiseHold, "CONTRACT_BASIS"): self.commit()
        self.assertFalse(self.live.exists()); contract.unlink()
        with self.assertRaises(OSError): self.commit()
        self.assertFalse((self.stage / "RUN_MANIFEST.json").exists())

    def test_actual_draft_manifest_is_rechecked_after_unchanged_inv9_evaluation(self):
        path = self.stage / "DRAFT_MANIFEST.json"; path.write_text(json.dumps(self.manifest))
        self.assertEqual(guard.require_staged_manifest(self.stage, path)["status"], "PASS")
        checker = guard._premise(); actual = checker.evaluate
        def mutate(*args, **kwargs):
            result = actual(*args, **kwargs)
            path.write_text('{"foundation_basis":"THEOREM"}')
            return result
        with patch.object(guard, "_premise", return_value=checker), patch.object(checker, "evaluate", side_effect=mutate):
            with self.assertRaisesRegex(guard.GenerationPremiseHold, "MANIFEST_CHANGED"):
                guard.require_staged_manifest(self.stage, path)


if __name__ == "__main__":
    unittest.main()
