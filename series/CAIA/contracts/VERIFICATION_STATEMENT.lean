import Mathlib

namespace Viridis.Computation.CheckerAgreement

theorem disagreement_exposes_error (truth left right : Bool) (h : left ≠ right) :
    left ≠ truth ∨ right ≠ truth := by
  sorry

theorem agreement_with_left_soundness (truth left right : Bool)
    (hAgree : left = right) (hLeft : left = truth) : right = truth := by
  sorry

theorem agreement_with_right_soundness (truth left right : Bool)
    (hAgree : left = right) (hRight : right = truth) : left = truth := by
  sorry

theorem shared_wrong_agreement_witness :
    ∃ truth left right : Bool, left = right ∧ left ≠ truth ∧ right ≠ truth := by
  sorry

end Viridis.Computation.CheckerAgreement
