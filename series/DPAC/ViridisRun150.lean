import Mathlib

noncomputable section

namespace Viridis.ThermodynamicEconomics.DualPriceAlignment

def valuation (price quantity cost : ℝ) : ℝ := price * quantity - cost

theorem valuation_gap_identity (p s q c : ℝ) :
    valuation p q c - valuation s q c = (p - s) * q := by
  unfold valuation
  ring

theorem valuation_gap_abs (p s q c : ℝ) (hq : 0 ≤ q) :
    |valuation p q c - valuation s q c| = |p - s| * q := by
  rw [valuation_gap_identity]
  rw [abs_mul, abs_of_nonneg hq]

theorem dual_acceptance_iff_corridor (p s q c : ℝ) :
    (0 ≤ valuation p q c ∧ 0 ≤ valuation s q c) ↔
      c ≤ min (p * q) (s * q) := by
  unfold valuation
  constructor
  · intro h
    apply le_min
    · linarith [h.1]
    · linarith [h.2]
  · intro h
    have hp : c ≤ p * q := le_trans h (min_le_left _ _)
    have hs : c ≤ s * q := le_trans h (min_le_right _ _)
    constructor <;> linarith

theorem two_project_gap_identity (p s qOne qTwo cOne cTwo : ℝ) :
    (valuation p qOne cOne + valuation p qTwo cTwo) -
      (valuation s qOne cOne + valuation s qTwo cTwo) =
        (p - s) * (qOne + qTwo) := by
  unfold valuation
  ring

theorem dual_price_positive_witness :
    (0 : ℝ) < 2 ∧ (0 : ℝ) < 3 ∧ (0 : ℝ) < 4 ∧ (0 : ℝ) < 7 ∧
      valuation 2 4 7 = 1 ∧ valuation 3 4 7 = 5 ∧
      (0 : ℝ) < valuation 2 4 7 ∧ (0 : ℝ) < valuation 3 4 7 := by
  norm_num [valuation]

theorem dual_price_mismatch_witness :
    valuation 1 2 4 = -2 ∧ valuation 3 2 4 = 2 ∧
      valuation 1 2 4 < 0 ∧ (0 : ℝ) < valuation 3 2 4 := by
  norm_num [valuation]

end Viridis.ThermodynamicEconomics.DualPriceAlignment
