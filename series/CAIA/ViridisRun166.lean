import Mathlib

namespace Viridis.Computation.CheckerAgreement

theorem disagreement_exposes_error (truth left right : Bool) (h : left ≠ right) :
    left ≠ truth ∨ right ≠ truth := by
  cases truth <;> cases left <;> cases right <;> simp_all

theorem agreement_with_left_soundness (truth left right : Bool)
    (hAgree : left = right) (hLeft : left = truth) : right = truth := by
  calc
    right = left := hAgree.symm
    _ = truth := hLeft

theorem agreement_with_right_soundness (truth left right : Bool)
    (hAgree : left = right) (hRight : right = truth) : left = truth := by
  calc
    left = right := hAgree
    _ = truth := hRight

theorem shared_wrong_agreement_witness :
    ∃ truth left right : Bool, left = right ∧ left ≠ truth ∧ right ≠ truth := by
  exact ⟨false, true, true, rfl, by simp, by simp⟩

end Viridis.Computation.CheckerAgreement
