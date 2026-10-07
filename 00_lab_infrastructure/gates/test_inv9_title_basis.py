import unittest
import importlib.util
from pathlib import Path
from inv9_title_basis import BASIS_SENTENCE,approved_title_only_view

class TitleBasisTests(unittest.TestCase):
    def paper(self,sentence=BASIS_SENTENCE,body='',title='A note for the Intelligence Bound'):
        return '\\documentclass{article}\n\\hypersetup{pdftitle={'+title+'}}\n\\title{\\textbf{'+title+'}}\n\\begin{document}\n\\begin{abstract}\nINDEPENDENT.\n'+sentence+'\n\\end{abstract}\n'+body+'\n\\end{document}'
    def test_phrase_only_title_with_exact_abstract_sentence_passes(self):
        v=approved_title_only_view(self.paper());self.assertIsNotNone(v)
        self.assertNotIn(BASIS_SENTENCE,v['product_view']);self.assertNotIn('Intelligence Bound',v['bound_view'])
    def test_title_without_sentence_fails(self):self.assertIsNone(approved_title_only_view(self.paper('')))
    def test_formula_matches_still_fail(self):
        for formula in (r'$\frac{PD}{K}$',r'$\frac{P D}{K}$',r'$P*D/K$',r'$P \cdot D / K$',r'$P D/K$',r'$PD/K$',r'$\dfrac{P\,D}{K}$'):
            with self.subTest(formula=formula):self.assertIsNone(approved_title_only_view(self.paper(body=formula)))
    def test_body_bound_phrase_fails(self):
        self.assertIsNone(approved_title_only_view(self.paper(body='The Intelligence Bound is derived.')))
    def test_sentence_only_in_body_or_later_abstract_fails(self):
        for body in (BASIS_SENTENCE,r'\begin{abstract}'+BASIS_SENTENCE+r'\end{abstract}'):
            self.assertIsNone(approved_title_only_view(self.paper('',body)))
    def test_sentence_in_archived_quote_comment_or_footnote_fails(self):
        self.assertIsNone(approved_title_only_view(self.paper('% '+BASIS_SENTENCE)))
        self.assertIsNone(approved_title_only_view(self.paper(r'\footnote{'+BASIS_SENTENCE+'}')))
        x=self.paper();x=x.replace(r'\begin{abstract}',r'\begin{quote}\begin{abstract}',1)
        self.assertIsNone(approved_title_only_view(x))
    def test_changed_or_duplicate_sentence_fails(self):
        self.assertIsNone(approved_title_only_view(self.paper(BASIS_SENTENCE[:-1])))
        self.assertIsNone(approved_title_only_view(self.paper(body=BASIS_SENTENCE)))
    def test_non_title_other_option_not_excluded(self):
        self.assertIsNone(approved_title_only_view(self.paper().replace('pdftitle=', 'pdfsubject=')))
    def test_malformed_or_multiple_titles_fail(self):
        self.assertIsNone(approved_title_only_view(self.paper()+r'\title{Intelligence Bound}'))
        self.assertIsNone(approved_title_only_view(self.paper().replace('\\title{\\textbf{','\\title{\\textbf{extra{')))

class IntegratedPremiseTests(TitleBasisTests):
    def setUp(self):
        import premise_declaration as canonical
        proposed=Path(__file__).with_name('proposed_premise_declaration.py')
        if proposed.exists():
            spec=importlib.util.spec_from_file_location('oct7_proposed_premise',proposed)
            self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
            self.module._aligner=canonical._aligner
        else:self.module=canonical
    def evaluate(self,paper,candidate='import Mathlib\ntheorem example_math (x : ℝ) : x = x := rfl\n'):
        return self.module.evaluate({'foundation_basis':'INDEPENDENT'},
            {'foundation_basis':'INDEPENDENT'},formal_statement=candidate,
            candidate=candidate,paper_text=paper,theorem_names=['example_math'],required=True)
    def test_integration_exact_title_exception_pass(self):
        self.assertEqual('PASS',self.evaluate(self.paper())['status'])
    def test_integration_missing_abstract_sentence_holds(self):
        self.assertEqual('HOLD',self.evaluate(self.paper(''))['status'])
    def test_integration_paper_formula_holds(self):
        self.assertEqual('HOLD',self.evaluate(self.paper(body=r'$\frac{PD}{K}$'))['status'])
    def test_integration_formula_in_frozen_candidate_holds(self):
        source='import Mathlib\ndef product_form (P D K : ℝ) := P * D / K\ntheorem example_math : True := True.intro\n'
        self.assertEqual('HOLD',self.evaluate(self.paper(),source)['status'])
    def test_integration_other_source_bound_dependency_holds(self):
        source='import Mathlib\ndef intelligenceCreationRate : ℝ := 0\ntheorem example_math : True := True.intro\n'
        self.assertEqual('HOLD',self.evaluate(self.paper(),source)['status'])

if __name__=='__main__':unittest.main()
