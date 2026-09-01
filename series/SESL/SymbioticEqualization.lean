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
  have hs := sq_sqrt_disc a b k
  rw [hr, slowRate]
  nlinarith [hs]

theorem slow_rate_lower_min
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) :
    min a b ≤ slowRate a b k := by
  have hnn : 0 ≤ Real.sqrt ((a - b)^2 + 4 * k^2) := Real.sqrt_nonneg _
  have hs := sq_sqrt_disc a b k
  rcases le_total a b with hab | hab
  · rw [min_eq_left hab, slowRate]
    -- need `2 * a ≤ a + b + 2k - s`, i.e. `s ≤ b - a + 2k`
    have key : Real.sqrt ((a - b)^2 + 4 * k^2) ≤ b - a + 2 * k := by
      nlinarith [hs, hnn]
    linarith
  · rw [min_eq_right hab, slowRate]
    have key : Real.sqrt ((a - b)^2 + 4 * k^2) ≤ a - b + 2 * k := by
      nlinarith [hs, hnn]
    linarith

theorem slow_rate_upper_mean
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) :
    slowRate a b k ≤ (a + b) / 2 := by
  have h := two_k_le_sqrt_disc a b k hk
  rw [slowRate]
  linarith

theorem slow_rate_monotone
    (a b k₁ k₂ : ℝ) (ha : 0 < a) (hb : 0 < b)
    (hk₁ : 0 ≤ k₁) (hord : k₁ ≤ k₂) :
    slowRate a b k₁ ≤ slowRate a b k₂ := by
  have hk₂ : 0 ≤ k₂ := le_trans hk₁ hord
  have h1 := sq_sqrt_disc a b k₁
  have h2 := sq_sqrt_disc a b k₂
  have hn1 : 0 ≤ Real.sqrt ((a - b)^2 + 4 * k₁^2) := Real.sqrt_nonneg _
  have hn2 : 0 ≤ Real.sqrt ((a - b)^2 + 4 * k₂^2) := Real.sqrt_nonneg _
  have hlow : 2 * k₁ ≤ Real.sqrt ((a - b)^2 + 4 * k₁^2) := two_k_le_sqrt_disc a b k₁ hk₁
  have key : Real.sqrt ((a - b)^2 + 4 * k₂^2)
      ≤ Real.sqrt ((a - b)^2 + 4 * k₁^2) + 2 * (k₂ - k₁) := by
    nlinarith [h1, h2, hn1, hn2, hlow, sq_nonneg (k₂ - k₁)]
  rw [slowRate, slowRate]
  linarith

theorem equal_rates_no_gain
    (a k : ℝ) (ha : 0 < a) (hk : 0 ≤ k) :
    slowRate a a k = a := by
  rw [slowRate]
  have h : (a - a)^2 + 4 * k^2 = (2 * k)^2 := by ring
  rw [h, Real.sqrt_sq (by linarith : (0:ℝ) ≤ 2 * k)]
  ring

theorem finite_asymmetry_strict_mean
    (a b k : ℝ) (ha : 0 < a) (hb : 0 < b) (hk : 0 ≤ k) (hab : a ≠ b) :
    slowRate a b k < (a + b) / 2 := by
  have hne : (0:ℝ) < (a - b)^2 := by
    have : a - b ≠ 0 := sub_ne_zero.mpr hab
    positivity
  have hs := sq_sqrt_disc a b k
  have hnn : 0 ≤ Real.sqrt ((a - b)^2 + 4 * k^2) := Real.sqrt_nonneg _
  have key : 2 * k < Real.sqrt ((a - b)^2 + 4 * k^2) := by
    nlinarith [hs, hnn]
  rw [slowRate]
  linarith

theorem symbiotic_equalization_nonvacuous :
    1 < slowRate 1 4 1 ∧ slowRate 1 4 1 < (1 + 4) / 2 := by
  have hval : slowRate 1 4 1 = (7 - Real.sqrt 13) / 2 := by
    rw [slowRate]
    norm_num
  have hnn : 0 ≤ Real.sqrt 13 := Real.sqrt_nonneg _
  have hsq : Real.sqrt 13 ^ 2 = 13 := Real.sq_sqrt (by norm_num)
  constructor
  · rw [hval]
    nlinarith [hsq, hnn]
  · rw [hval]
    nlinarith [hsq, hnn]

end Viridis.ThermodynamicSpeedLimits.SymbioticEqualization
