"""INV-9 regressions use source fixtures, never Lean/SSH/HTTP or proof issuance."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from premise_declaration import evaluate, validate_artifact, RUN902_PREMISES, CONDITIONAL_PHRASE, RUN900_SIGNATURES, RUN902_SIGNATURE, _aligner

INDEPENDENT = 'theorem independent_target (n : Nat) : n ≤ n + 1 := by\n  exact Nat.le_succ n\n'
THEOREM = RUN900_SIGNATURES['intelligence_bound']+' := by\n  exact supplied_bound\n'
CONDITIONAL = ('theorem product_form_fixture (R_obs K P D rate : ℝ)\n'
               '    (PL : R_obs * K ≤ P) (PD : rate ≤ R_obs * D) : rate ≤ P * D / K := by\n'
               '  exact supplied_bound\n')


def paper(text):
    return r'\begin{document}\begin{abstract}'+text+r'\end{abstract}\end{document}'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PremiseDeclarationTests(unittest.TestCase):
    def check(self, basis, source=None, text=None, manifest=None, inventory=None, required=True, target=None):
        defaults = {'INDEPENDENT': (INDEPENDENT, 'INDEPENDENT: a model ordering theorem.', 'independent_target'),
                    'THEOREM': (THEOREM, 'THEOREM: the certified min form / data wall.', 'intelligence_bound'),
                    'CONDITIONAL_PL_PD': (CONDITIONAL, 'The product form is '+CONDITIONAL_PHRASE+'.', 'product_form_fixture')}
        original, original_paper, original_target = defaults.get(basis, defaults['INDEPENDENT'])
        source = original if source is None else source
        target = target or original_target
        safe = source.replace('exact sorry', 'exact supplied_bound')
        targets=[target]+(['Run902_product_form_conditional'] if 'theorem Run902_product_form_conditional' in safe else [])
        formal = _aligner().align_challenge(safe, safe, targets)[0]
        return evaluate(manifest if manifest is not None else {'foundation_basis': basis},
                        inventory if inventory is not None else {'foundation_basis': basis},
                        formal_statement=formal, candidate=source, paper_text=paper(text or original_paper),
                        theorem_names=[target], required=required)

    def assert_hold(self, result, code):
        self.assertEqual(result['status'], 'HOLD', result)
        self.assertIn(code, str(result['reasons']), result)
        self.assertFalse(result['local_lean_execution']); self.assertFalse(result['certifies'])

    def test_three_explicit_basis_values_pass(self):
        for basis in ('THEOREM', 'CONDITIONAL_PL_PD', 'INDEPENDENT'):
            with self.subTest(basis=basis):
                result = self.check(basis)
                self.assertEqual(result['status'], 'PASS', result)
                self.assertEqual(result['foundation_basis'], basis)
                self.assertFalse(result['certifies']); self.assertFalse(result['local_lean_execution'])

    def test_product_form_under_theorem_holds(self):
        self.assert_hold(self.check('THEOREM', source=CONDITIONAL, target='product_form_fixture'), 'PREMISE_UNDERDECLARED')

    def test_product_form_under_independent_holds(self):
        self.assert_hold(self.check('INDEPENDENT', source=CONDITIONAL, target='product_form_fixture'), 'PREMISE_UNDERDECLARED')

    def test_removed_pl_holds(self):
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=CONDITIONAL.replace('(PL : R_obs * K ≤ P) ', '')), 'PREMISE_DROPPED')

    def test_pl_axiom_holds(self):
        source = 'axiom PL : ∀ R_obs K P : ℝ, R_obs * K ≤ P\n'+CONDITIONAL.replace('(PL : R_obs * K ≤ P) ', '')
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=source), 'PREMISE_FORBIDDEN_AXIOM_OR_ESCAPE')

    def test_unconditional_paper_product_assertion_holds(self):
        self.assert_hold(self.check('CONDITIONAL_PL_PD', text='The product form holds universally.'), 'PREMISE_BASIS_NOT_IN_MAIN_RESULT')

    def test_abstract_disclaimer_does_not_qualify_later_unconditional_use(self):
        source = CONDITIONAL; formal = _aligner().align_challenge(source, source, ['product_form_fixture'])[0]
        text = paper('The product form is '+CONDITIONAL_PHRASE+'.').replace(r'\end{document}', '\n\nThe product form always applies.\n'+r'\end{document}')
        result = evaluate({'foundation_basis': 'CONDITIONAL_PL_PD'}, {'foundation_basis': 'CONDITIONAL_PL_PD'},
                          formal_statement=formal, candidate=source, paper_text=text, theorem_names=['product_form_fixture'], required=True)
        self.assert_hold(result, 'PREMISE_UNCONDITIONAL_PAPER_CLAIM')

    def test_missing_field_new_cutover_holds(self):
        self.assert_hold(self.check('INDEPENDENT', manifest={}), 'PREMISE_DECLARATION_MISSING_OR_UNKNOWN')
        self.assert_hold(self.check('INDEPENDENT', manifest={}, inventory={}), 'PREMISE_DECLARATION_MISSING_OR_UNKNOWN')

    def test_unknown_basis_and_two_sealed_values_disagree_hold(self):
        self.assert_hold(self.check('invented'), 'PREMISE_DECLARATION_MISSING_OR_UNKNOWN')
        self.assert_hold(self.check('INDEPENDENT', inventory={'foundation_basis': 'THEOREM'}), 'PREMISE_DECLARATION_MISMATCH')

    def test_existing_canon_absent_fields_is_exempt_only_without_cutover(self):
        self.assertEqual(self.check('INDEPENDENT', manifest={}, inventory={}, required=False)['status'], 'EXEMPT')
        self.assert_hold(self.check('INDEPENDENT', manifest={}, inventory={}, required=True), 'PREMISE_DECLARATION_MISSING_OR_UNKNOWN')

    def test_declaration_checked_even_before_cutover_flag(self):
        self.assert_hold(self.check('THEOREM', source=CONDITIONAL, target='product_form_fixture', required=False), 'PREMISE_UNDERDECLARED')

    def test_whitespace_and_lean_comments_normalize_only(self):
        source = CONDITIONAL.replace('R_obs * K ≤ P)', 'R_obs /- physical premise -/ *\n K ≤ P)').replace('rate ≤ R_obs * D)', 'rate  ≤  R_obs * D)')
        self.assertEqual(self.check('CONDITIONAL_PL_PD', source=source)['status'], 'PASS')
        self.assertEqual(RUN902_PREMISES, {'PL': 'R_obs * K ≤ P', 'PD': 'rate ≤ R_obs * D'})

    def test_changed_pl_not_equivalence_guessed(self):
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=CONDITIONAL.replace('R_obs * K ≤ P)', 'R_obs * K < P)')), 'PREMISE_DROPPED')

    def test_implicit_or_renamed_pl_cannot_replace_explicit_hypothesis(self):
        for source in [CONDITIONAL.replace('(PL : R_obs * K ≤ P)', '{PL : R_obs * K ≤ P}'), CONDITIONAL.replace('(PL :', '(h_pl :')]:
            with self.subTest(source=source): self.assert_hold(self.check('CONDITIONAL_PL_PD', source=source), 'PREMISE_DROPPED')

    def test_global_section_pl_is_not_theorem_hypothesis(self):
        for prefix in ['variable (PL : R_obs * K ≤ P)\n', 'variable\n  (PL : R_obs * K ≤ P)\n']:
            self.assert_hold(self.check('CONDITIONAL_PL_PD', source=prefix+CONDITIONAL.replace('(PL : R_obs * K ≤ P) ', '')), 'PREMISE_GLOBAL_ASSUMPTION')

    def test_exact_conditional_theorem_invocation_allowed(self):
        source = RUN902_SIGNATURE+' := by\n  exact supplied_bound\n'+CONDITIONAL.replace('(PL : R_obs * K ≤ P) (PD : rate ≤ R_obs * D)', '(premises : ModelPremises)').replace('supplied_bound', 'Run902_product_form_conditional premises.PL premises.PD')
        self.assertEqual(self.check('CONDITIONAL_PL_PD', source=source)['status'], 'PASS')

    def test_comment_and_string_cannot_spoof_conditional_invocation(self):
        source = CONDITIONAL.replace('(PL : R_obs * K ≤ P) ', '').replace('supplied_bound', 'other_proof -- Run902_product_form_conditional')
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=source), 'PREMISE_DROPPED')
        source = source.replace('other_proof -- Run902_product_form_conditional', 'other_proof "Run902_product_form_conditional"')
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=source), 'PREMISE_DROPPED')

    def test_same_name_local_replacement_is_not_run902(self):
        source = 'def Run902_product_form_conditional := 0\n'+CONDITIONAL.replace('(PL : R_obs * K ≤ P) ', '').replace('supplied_bound', 'Run902_product_form_conditional')
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=source), 'PREMISE_CONDITIONAL_REFERENCE_UNRESOLVED')

    def test_independent_bound_reference_holds(self):
        self.assert_hold(self.check('INDEPENDENT', source=THEOREM, target='intelligence_bound'), 'PREMISE_UNDERDECLARED')

    def test_theorem_spelling_alone_is_not_frozen_scope(self):
        source='def data_wall (n : Nat) := n + 1\ntheorem target (n : Nat) : n ≤ data_wall n := by\n  exact Nat.le_succ n\n'
        self.assert_hold(self.check('THEOREM',source=source,target='target'),'PREMISE_THEOREM_REFERENCE_UNRESOLVED')

    def test_inventory_product_claim_also_must_name_pl_pd(self):
        result=self.check('CONDITIONAL_PL_PD',inventory={'foundation_basis':'CONDITIONAL_PL_PD','claims':[{'claim':'The product form holds universally.'}]})
        self.assert_hold(result,'PREMISE_UNCONDITIONAL_INVENTORY_CLAIM')

    def test_main_result_basis_required(self):
        self.assert_hold(self.check('INDEPENDENT', text='A mathematical ordering result.'), 'PREMISE_BASIS_NOT_IN_MAIN_RESULT')
        self.assert_hold(self.check('THEOREM', text='A mathematical ordering result.'), 'PREMISE_BASIS_NOT_IN_MAIN_RESULT')

    def test_inventory_approved_equivalent_must_name_conditional_pl_pd(self):
        phrase='Our result is conditional upon premises PL and PD'
        result=self.check('CONDITIONAL_PL_PD', text='The product form. '+phrase+'.', inventory={'foundation_basis':'CONDITIONAL_PL_PD', 'premise_declaration':{'approved_equivalents':[phrase]}})
        self.assertEqual(result['status'], 'PASS', result)
        self.assert_hold(self.check('CONDITIONAL_PL_PD', inventory={'foundation_basis':'CONDITIONAL_PL_PD', 'premise_declaration':{'approved_equivalents':['Verified under model assumptions']}}), 'PREMISE_INTAKE_ERROR')

    def test_candidate_sorry_and_parser_failure_hold(self):
        self.assert_hold(self.check('CONDITIONAL_PL_PD', source=CONDITIONAL.replace('supplied_bound','sorry')), 'PREMISE_FORBIDDEN_AXIOM_OR_ESCAPE')
        result=evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT'},formal_statement='',candidate='',paper_text='',theorem_names=[],required=True)
        self.assert_hold(result,'PREMISE_INTAKE_ERROR')


class HashBoundArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.artifact=self.root/'release';self.artifact.mkdir()
        self.manifest=self.root/'SEALED_RUN_MANIFEST.json';self.inventory=self.root/'SEALED_CLAIM_INVENTORY.json'
        self.formal=self.root/'statement.lean';self.candidate=self.root/'candidate.lean';self.certificate=self.root/'certificate.json'
        self.manifest.write_text(json.dumps({'foundation_basis':'INDEPENDENT'}));self.inventory.write_text(self.manifest.read_text())
        self.candidate.write_text(INDEPENDENT);self.formal.write_text(_aligner().align_challenge(INDEPENDENT,INDEPENDENT,['independent_target'])[0])
        (self.artifact/'paper.tex').write_text(paper('INDEPENDENT: model ordering.'))
        self.cert={'foundation_basis':'INDEPENDENT','bindings':{'sealed_paper_inputs':{'SEALED_RUN_MANIFEST.json':self.bound(self.manifest),'SEALED_CLAIM_INVENTORY.json':self.bound(self.inventory)},'formal_statement':self.bound(self.formal),'candidate_proof':self.bound(self.candidate)}}
        self.certificate.write_text(json.dumps(self.cert));self.inspection={'valid':True,'certified_theorems':['independent_target']}

    def bound(self,p):return {'path':str(p),'sha256':sha(p)}
    def check(self,required=True):return validate_artifact(self.artifact,self.inspection,self.certificate,self.root,required=required)
    def test_bound_inputs_and_final_text_pass(self): self.assertEqual(self.check()['status'],'PASS')
    def test_one_byte_sealed_input_mismatch_hold(self):
        self.manifest.write_text(self.manifest.read_text()+' ')
        self.assertIn('hash-mismatched',str(self.check()['reasons']));self.assertEqual(self.check()['status'],'HOLD')
    def test_certificate_missing_or_different_basis_hold(self):
        for basis in [None,'THEOREM']:
            obj=json.loads(json.dumps(self.cert))
            if basis is None:obj.pop('foundation_basis')
            else:obj['foundation_basis']=basis
            self.certificate.write_text(json.dumps(obj));self.assertEqual(self.check()['status'],'HOLD')
    def test_invalid_inspection_and_multiple_final_tex_hold(self):
        self.inspection['valid']=False;self.assertEqual(self.check()['status'],'HOLD')
        self.inspection['valid']=True;(self.artifact/'second.tex').write_text('second');self.assertEqual(self.check()['status'],'HOLD')
    def test_historical_absent_four_input_contract_is_exempt_only_without_flag(self):
        self.certificate.write_text('{}');self.assertEqual(self.check(required=False)['status'],'EXEMPT')
        self.assertEqual(self.check(required=True)['status'],'HOLD')


if __name__=='__main__':unittest.main()
