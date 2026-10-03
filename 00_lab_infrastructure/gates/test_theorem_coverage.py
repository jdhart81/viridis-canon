import unittest
from theorem_coverage import triviality, declarations
from claim_binding import check_bindings
import test_publication_coverage_gate as fixture_tests

class TrivialTests(unittest.TestCase):
    def test_reflexivity_and_definition_only_label(self):
        for proof in ('rfl','by rfl','by reflexivity','Eq.refl p','by simp only [identity]','by unfold identity; rfl'):
            source='def identity (p : Nat) := p\ntheorem copied (p : Nat) : identity p = p := '+proof+'\n'
            self.assertEqual(triviality(source)['copied']['classification'],'CERTIFIED_TRIVIAL',proof)
    def test_internal_rfl_in_nontrivial_proof_not_whole_proof(self):
        source='theorem real_result (n : Nat) : n ≤ n+1 := by\n  have h : n=n := rfl\n  exact Nat.le_succ n\n'
        self.assertEqual(triviality(source)['real_result']['classification'],'NO_SYNTACTIC_TRIVIAL_PATTERN')
    def test_alias_cannot_launder_trivial(self):
        x=triviality('theorem copied (p : Nat) : p=p := rfl\ntheorem alias (p : Nat) : p=p := copied p\n')
        self.assertEqual(x['alias']['classification'],'CERTIFIED_TRIVIAL')
    def test_namespaces_do_not_confuse_same_short_name(self):
        x=declarations('namespace A\ntheorem same (p : Nat) : p=p := rfl\nend A\nnamespace B\ntheorem same (p : Nat) : p≤p+1 := Nat.le_succ p\nend B\n')
        self.assertNotIn('same',x);self.assertIn('A.same',x);self.assertIn('B.same',x)
    def test_library_lemma_not_definition_only(self):
        x=triviality('theorem bound (n : Nat) : n ≤ n+1 := by simp only [Nat.le_succ]\n')
        self.assertNotEqual(x['bound']['classification'],'CERTIFIED_TRIVIAL')
    def test_formally_verified_binding_rejected_for_trivial(self):
        f=fixture_tests.PublicationCoverageGateTests(methodName='test_certified_bound_claim_positive');f.setUp();self.addCleanup(f.doCleanups)
        f.candidate.write_text('theorem meaningful (p : Nat) : p=p := rfl\ntheorem meaningful_witness : ∃ p : Nat, p=p := ⟨0,rfl⟩\n');f.expected_candidate_hash=fixture_tests.digest(f.candidate)
        result=check_bindings(f.binding,f.entry,f.ledger,inspector=f.inspected_fixture)
        self.assertEqual(result['status'],'HOLD');self.assertEqual(result['claims'][0]['verification_status'],'CERTIFIED_TRIVIAL')
if __name__=='__main__':unittest.main()
