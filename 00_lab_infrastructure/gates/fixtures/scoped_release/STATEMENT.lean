import Mathlib

noncomputable section

namespace Viridis.ThermodynamicSpeedLimits.SymbioticEqualization

def slowRate (a b k : ℝ) : ℝ :=
  (a + b + 2 * k - Real.sqrt ((a - b)^2 + 4 * k^2)) / 2

/-- The discriminant `(a - b)^2 + 4 * k^2` is nonnegative. -/
private lemma disc_nonneg (a b k : ℝ) : 0 ≤ (a - b)^2 + 4 * k^2 := by
  have h1 : 0 ≤ (a - b)^2 := sq_nonneg _
  have h2 : 0 ≤ 4 * k^2 := by positivity
  linarith

/-- The square of the discriminant's square root. -/
private lemma sq_sqrt_disc (a b k : ℝ) :
    Real.sqrt ((a - b)^2 + 4 * k^2) ^ 2 = (a - b)^2 + 4 * k^2 :=
  Real.sq_sqrt (disc_nonneg a b k)

/-- `2 * k` is at most the square root of the discriminant, when `0 ≤ k`. -/
private lemma two_k_le_sqrt_disc (a b k : ℝ) (hk : 0 ≤ k) :
    2 * k ≤ Real.sqrt ((a - b)^2 + 4 * k^2) := by
  have h : Real.sqrt ((2 * k)^2) ≤ Real.sqrt ((a - b)^2 + 4 * k^2) := by
    apply Real.sqrt_le_sqrt
    nlinarith [sq_nonneg (a - b)]
  rwa [Real.sqrt_sq (by linarith : (0:ℝ) ≤ 2 * k)] at h

theorem slow_rate_characterization
    (a b k r : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k)
    (hr : r = slowRate a b k) :
    r^2 - (a + b + 2*k) * r + a*b + k*(a+b) = 0 := by
  sorry

theorem slow_rate_lower_min
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) :
    min a b ≤ slowRate a b k := by
  sorry

theorem slow_rate_upper_mean
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) :
    slowRate a b k ≤ (a + b) / 2 := by
  sorry

theorem slow_rate_monotone
    (a b k₁ k₂ : ℝ) (ha : 0 < a) (hb : 0 < b)
    (hk₁ : 0 ≤ k₁) (hord : k₁ ≤ k₂) :
    slowRate a b k₁ ≤ slowRate a b k₂ := by
  sorry

theorem equal_rates_no_gain
    (a k : ℝ) (ha : 0 < a) (hk : 0 ≤ k) :
    slowRate a a k = a := by
  sorry

theorem finite_asymmetry_strict_mean
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) (hab : a ≠ b) :
    slowRate a b k < (a + b) / 2 := by
  sorry

theorem symbiotic_equalization_nonvacuous :
    1 < slowRate 1 4 1 ∧ slowRate 1 4 1 < (1 + 4) / 2 := by
  sorry

end Viridis.ThermodynamicSpeedLimits.SymbioticEqualization
