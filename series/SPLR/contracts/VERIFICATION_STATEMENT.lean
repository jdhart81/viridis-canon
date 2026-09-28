import Mathlib

namespace Viridis.GaianSystems.SinglePartnerLossReserve

def retainedAfterLoss (a b c lost : ℝ) : ℝ := a + b + c - lost

theorem loss_budget_guarantee
    (a b c q budget lost : ℝ)
    (hreserve : q + budget ≤ a + b + c)
    (hloss : lost ≤ budget) :
    q ≤ retainedAfterLoss a b c lost := by
  sorry

theorem loss_of_a (a b c q : ℝ) (h : q ≤ b + c) :
    q ≤ retainedAfterLoss a b c a := by
  sorry

theorem loss_of_b (a b c q : ℝ) (h : q ≤ a + c) :
    q ≤ retainedAfterLoss a b c b := by
  sorry

theorem loss_of_c (a b c q : ℝ) (h : q ≤ a + b) :
    q ≤ retainedAfterLoss a b c c := by
  sorry

theorem three_partner_single_loss_guarantee
    (a b c q : ℝ)
    (hab : q ≤ a + b) (hac : q ≤ a + c) (hbc : q ≤ b + c) :
    q ≤ retainedAfterLoss a b c a ∧
    q ≤ retainedAfterLoss a b c b ∧
    q ≤ retainedAfterLoss a b c c := by
  sorry

theorem reserve_monotone_new_partner
    (a b c d q budget : ℝ)
    (h : q + budget ≤ a + b + c) (hd : 0 ≤ d) :
    q + budget ≤ a + b + c + d := by
  sorry

theorem single_partner_loss_witness :
    retainedAfterLoss 2 3 5 5 = 5 ∧
    retainedAfterLoss 2 3 5 3 = 7 ∧
    retainedAfterLoss 2 3 5 2 = 8 := by
  sorry

theorem concentrated_total_counterexample :
    retainedAfterLoss 5 5 0 5 = 5 ∧
    retainedAfterLoss 4 3 3 4 = 6 := by
  sorry

end Viridis.GaianSystems.SinglePartnerLossReserve

