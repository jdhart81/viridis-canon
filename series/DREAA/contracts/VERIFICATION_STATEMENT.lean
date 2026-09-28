import Mathlib

noncomputable section

namespace Viridis.Applications.DeferenceReserveEqualization

def reviewBenefit (rateOne rateTwo timeOne timeTwo : ℝ) : ℝ :=
  rateOne * timeOne + rateTwo * timeTwo

def residualLoss (baseLoss rateOne rateTwo timeOne timeTwo : ℝ) : ℝ :=
  baseLoss - reviewBenefit rateOne rateTwo timeOne timeTwo

theorem residual_loss_decomposition
    (baseLoss rateOne rateTwo timeOne timeTwo : ℝ) :
    residualLoss baseLoss rateOne rateTwo timeOne timeTwo +
      reviewBenefit rateOne rateTwo timeOne timeTwo = baseLoss := by
  sorry

theorem exchange_gain_identity
    (rateOne rateTwo timeOne timeTwo delta : ℝ) :
    reviewBenefit rateOne rateTwo (timeOne + delta) (timeTwo - delta) -
      reviewBenefit rateOne rateTwo timeOne timeTwo =
        delta * (rateOne - rateTwo) := by
  sorry

theorem exchange_preserves_capacity
    (timeOne timeTwo delta : ℝ) :
    (timeOne + delta) + (timeTwo - delta) = timeOne + timeTwo := by
  sorry

theorem ordered_exchange_not_worse
    (rateOne rateTwo timeOne timeTwo delta : ℝ)
    (hrate : rateTwo ≤ rateOne) (hdelta : 0 ≤ delta) :
    reviewBenefit rateOne rateTwo timeOne timeTwo ≤
      reviewBenefit rateOne rateTwo (timeOne + delta) (timeTwo - delta) := by
  sorry

theorem ordered_exchange_reduces_loss
    (baseLoss rateOne rateTwo timeOne timeTwo delta : ℝ)
    (hrate : rateTwo ≤ rateOne) (hdelta : 0 ≤ delta) :
    residualLoss baseLoss rateOne rateTwo (timeOne + delta) (timeTwo - delta) ≤
      residualLoss baseLoss rateOne rateTwo timeOne timeTwo := by
  sorry

theorem full_first_dominates_split
    (rateOne rateTwo budget timeOne timeTwo : ℝ)
    (hrate : rateTwo ≤ rateOne) (hsum : timeOne + timeTwo = budget)
    (htwo : 0 ≤ timeTwo) :
    reviewBenefit rateOne rateTwo timeOne timeTwo ≤ rateOne * budget := by
  sorry

theorem equal_rate_allocation_invariant
    (rate budget timeOne timeTwo : ℝ)
    (hsum : timeOne + timeTwo = budget) :
    reviewBenefit rate rate timeOne timeTwo = rate * budget := by
  sorry

theorem deference_reserve_positive_witness :
    reviewBenefit 4 2 3 0 = 12 ∧ residualLoss 20 4 2 3 0 = 8 := by
  sorry

theorem wrong_priority_negative_control :
    reviewBenefit 2 4 3 0 < reviewBenefit 2 4 0 3 := by
  sorry

end Viridis.Applications.DeferenceReserveEqualization
