import Mathlib

noncomputable section

namespace Viridis.Afforestation.SharedFacilitation

def pooledMargin (demandOne demandTwo supportOne supportTwo : ℝ) : ℝ :=
  (supportOne + supportTwo) - (demandOne + demandTwo)

theorem pooled_margin_identity
    (demandOne demandTwo supportOne supportTwo : ℝ) :
    pooledMargin demandOne demandTwo supportOne supportTwo =
      (supportOne - demandOne) + (supportTwo - demandTwo) := by
  sorry

theorem pooled_feasible_iff_margin_nonnegative
    (demandOne demandTwo supportOne supportTwo : ℝ) :
    demandOne + demandTwo ≤ supportOne + supportTwo ↔
      0 ≤ pooledMargin demandOne demandTwo supportOne supportTwo := by
  sorry

theorem isolated_feasible_implies_pooled
    (demandOne demandTwo supportOne supportTwo : ℝ)
    (hOne : demandOne ≤ supportOne) (hTwo : demandTwo ≤ supportTwo) :
    demandOne + demandTwo ≤ supportOne + supportTwo := by
  sorry

theorem transfer_conserves_pooled_margin
    (demandOne demandTwo supportOne supportTwo transfer : ℝ) :
    pooledMargin demandOne demandTwo (supportOne - transfer) (supportTwo + transfer) =
      pooledMargin demandOne demandTwo supportOne supportTwo := by
  sorry

theorem full_pool_double_count_identity
    (supportOne supportTwo : ℝ) :
    2 * (supportOne + supportTwo) - (supportOne + supportTwo) =
      supportOne + supportTwo := by
  sorry

theorem shared_facilitation_nonvacuous_witness :
    (0 : ℝ) < 3 ∧ (0 : ℝ) < 1 ∧ (0 : ℝ) < 2 ∧
      (3 : ℝ) + 1 ≤ 2 + 2 ∧ ¬ ((3 : ℝ) ≤ 2) ∧
      pooledMargin 3 1 2 2 = 0 := by
  sorry

end Viridis.Afforestation.SharedFacilitation
