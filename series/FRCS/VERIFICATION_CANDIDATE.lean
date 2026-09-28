import Mathlib

noncomputable section

namespace Viridis.Monitoring.FreshnessReserve

def requiredRate (records horizon : ℝ) : ℝ := records / horizon

theorem freshness_capacity_equiv
    (records capacity horizon : ℝ) (hh : 0 < horizon) :
    records ≤ capacity * horizon ↔ requiredRate records horizon ≤ capacity := by
  unfold requiredRate
  constructor
  · intro h
    exact (div_le_iff₀ hh).2 h
  · intro h
    exact (div_le_iff₀ hh).1 h

theorem nominal_capacity_exact
    (records horizon : ℝ) (hh : 0 < horizon) :
    (requiredRate records horizon) * horizon = records := by
  unfold requiredRate
  exact div_mul_cancel₀ records (ne_of_gt hh)

theorem reserve_capacity_sufficient
    (records horizon reserve : ℝ) (hr : 0 ≤ records)
    (hh : 0 < horizon) (hreserve : 1 ≤ reserve) :
    records ≤ (reserve * requiredRate records horizon) * horizon := by
  rw [mul_assoc, nominal_capacity_exact records horizon hh]
  nlinarith

theorem reserve_headroom_identity
    (records horizon reserve : ℝ) (hh : 0 < horizon) :
    (reserve * requiredRate records horizon) * horizon - records =
      (reserve - 1) * records := by
  rw [mul_assoc, nominal_capacity_exact records horizon hh]
  ring

theorem capacity_shortfall_positive
    (records capacity horizon : ℝ) (hh : 0 < horizon)
    (hshort : capacity < requiredRate records horizon) :
    0 < records - capacity * horizon := by
  have hscaled : capacity * horizon < records := by
    exact (lt_div_iff₀ hh).1 hshort
  linarith

theorem freshness_reserve_sharp_witness :
    0 < (4 : ℝ) ∧ requiredRate 12 4 = 3 ∧
      (12 : ℝ) = 3 * 4 ∧
      (2 * requiredRate 12 4) * 4 - 12 = (2 - 1) * 12 := by
  norm_num [requiredRate]

end Viridis.Monitoring.FreshnessReserve
