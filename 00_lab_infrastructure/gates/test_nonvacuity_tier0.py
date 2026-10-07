import hashlib
import unittest
import nonvacuity_tier0 as t

class Tier0Tests(unittest.TestCase):
    def classify(self,s,ambient=(),**kw):
        return t.assess_declaration(s,list(ambient),**kw)
    def test_builtin_nonempty_domains(self):
        for typ in ('ℝ','Real','ℕ','Nat','ℤ','Int','ℚ','Rat','Bool','Unit','PUnit','NNReal','ENNReal','Fin 3','Finset Nat','Finset ℝ'):
            with self.subTest(type=typ):
                r=self.classify('theorem test (x : '+typ+') : x = x')
                self.assertEqual('NO_HYPOTHESES',r['status']);self.assertEqual(typ,r['domains'][0]['type'])
                self.assertTrue(r['domains'][0]['term']);self.assertFalse(r['certifies'])
    def test_closed_claim(self):
        self.assertIn('Unit',self.classify('theorem test : (1 : Nat) = 1')['witness'])
    def test_constant_functions_do_not_require_nonempty_input(self):
        for typ in ('Fin 0 → ℝ','Empty -> Real','α → ℝ','Fin 3 -> Real'):
            self.assertEqual('NO_HYPOTHESES',self.classify('theorem test (f : '+typ+') : f = f')['status'])
    def test_type_parameter_and_function_coherent(self):
        self.assertEqual('NO_HYPOTHESES',self.classify('theorem test (α : Type) (f : α → ℝ) : f = f')['status'])
    def test_unknown_empty_or_prop_domains_fail(self):
        for typ in ('Empty','PEmpty','Fin 0','Fin n','α','Prop','False','True','0 < x','RobustFeasible 0 1 0','RateModel','HiddenFalse','x = 0','Nonempty α','Inhabited α'):
            with self.subTest(type=typ):self.assertEqual('HOLD',self.classify('theorem test (x : '+typ+') : True')['status'])
    def test_instance_binders_fail(self):
        self.assertEqual('HOLD',self.classify('theorem test [IsProbabilityMeasure P] : True')['status'])
    def test_builtin_shadowing_and_local_notation_fail(self):
        for source in ('abbrev Real := Empty\n','def Nat : Type := Empty\n','local notation "ℝ" => Empty\n'):
            self.assertEqual('HOLD',self.classify('theorem test (x : ℝ) : x = x',source=source)['status'])
    def test_ambient_hypothesis_and_unknown_domain_fail(self):
        for text in ('variable (h : False)','variable {α : Type} (x : α)','variable [Nonempty α]'):
            self.assertEqual('HOLD',self.classify('theorem test : True',[{'line':1,'source_text':text}])['status'])
    def test_ambient_real_parameters_documented(self):
        r=self.classify('theorem test : a = a',[{'line':1,'source_text':'variable (a : ℝ)'}])
        self.assertEqual('NO_HYPOTHESES',r['status']);self.assertEqual(['a'],r['domains'][0]['binders'])
    def test_post_colon_implication_fail(self):
        for conclusion in ('False → 1 = 0','p -> p','∀ x : Empty, True','forall x : Empty, True'):
            self.assertEqual('HOLD',self.classify('theorem test : '+conclusion)['status'])
    def test_custom_closed_term_bound_to_source(self):
        source='structure Custom where\n  x : Nat\ndef specimen : Custom := ⟨0⟩\ntheorem test (x : Custom) : x = x := rfl\n'
        e={'Custom':{'kind':'CERTIFICATE_BOUND_CLOSED_EXPLICIT_TERM','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'term_declaration':'def specimen : Custom := ⟨0⟩','term':'specimen'}}
        self.assertEqual('NO_HYPOTHESES',self.classify('theorem test (x : Custom) : x = x',source=source,custom_domains=e)['status'])
        self.assertEqual('HOLD',self.classify('theorem test (x : Custom) : x = x',source=source+' ',custom_domains=e)['status'])
        e['Custom']['term']='invented';self.assertEqual('HOLD',self.classify('theorem test (x : Custom) : x = x',source=source,custom_domains=e)['status'])
    def test_custom_term_with_hidden_assumption_fails(self):
        source='variable (h : False)\ndef specimen : Custom := False.elim h\n'
        e={'Custom':{'kind':'CERTIFICATE_BOUND_CLOSED_EXPLICIT_TERM','source_sha256':hashlib.sha256(source.encode()).hexdigest(),'term_declaration':'def specimen : Custom := False.elim h','term':'specimen'}}
        self.assertEqual('HOLD',self.classify('theorem test (x : Custom) : x = x',source=source,custom_domains=e)['status'])
    def test_default_value_untyped_and_unparsed_context_fail(self):
        for signature in ('theorem test (x := 1) : x = x','theorem test x : True','not a declaration'):
            self.assertEqual('HOLD',self.classify(signature)['status'])
        self.assertEqual('HOLD',self.classify('theorem test : True',[{'line':1,'source_text':'open Nat'}])['status'])

if __name__=='__main__': unittest.main()
