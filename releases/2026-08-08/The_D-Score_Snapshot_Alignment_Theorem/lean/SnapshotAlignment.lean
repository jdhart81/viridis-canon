import Mathlib.Analysis.Complex.Basic
import Mathlib.Analysis.Complex.Exponential
import Mathlib.Analysis.Complex.Trigonometric
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Bounds

set_option autoImplicit false

open scoped BigOperators ComplexConjugate

namespace Viridis.SnapshotAlignment

noncomputable section

/-- Weighted delay phasor for a locally common harmonic mode. -/
def phasor {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω : ℝ) : ℂ :=
  ∑ i, (w i : ℂ) * Complex.exp (-(ω * τ i : ℂ) * Complex.I)

/-- Common-mode output-to-input energy ratio. -/
def alignment {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω : ℝ) : ℝ :=
  Complex.normSq (phasor w τ ω)

/-- Weighted mean channel delay. -/
def weightedMean {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) : ℝ :=
  ∑ i, w i * τ i

/-- Weighted delay variance about the weighted mean. -/
def delayVariance {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) : ℝ :=
  ∑ i, w i * (τ i - weightedMean w τ) ^ 2

section Helpers

variable {ι : Type*} [Fintype ι]

/-- Real part of the weighted phasor. -/
lemma phasor_re (w τ : ι → ℝ) (ω : ℝ) :
    (phasor w τ ω).re = ∑ i, w i * Real.cos (ω * τ i) := by
  simp [phasor]
  simp [Complex.exp_re]

/-- Imaginary part of the weighted phasor. -/
lemma phasor_im (w τ : ι → ℝ) (ω : ℝ) :
    (phasor w τ ω).im = -∑ i, w i * Real.sin (ω * τ i) := by
  simp [phasor]
  simp [Complex.exp_im]

/-- Alignment as the squared modulus in cosine/sine coordinates. -/
lemma alignment_eq_sq_add_sq (w τ : ι → ℝ) (ω : ℝ) :
    alignment w τ ω =
      (∑ i, w i * Real.cos (ω * τ i)) ^ 2 + (∑ i, w i * Real.sin (ω * τ i)) ^ 2 := by
  rw [alignment, Complex.normSq_apply, phasor_re, phasor_im]
  ring

end Helpers

/-- Exact pairwise cosine representation of the squared weighted phasor. -/
theorem phasor_energy_pairwise_identity
    {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω : ℝ) :
    alignment w τ ω =
      ∑ i, ∑ j, w i * w j * Real.cos (ω * (τ i - τ j)) := by
  rw [alignment_eq_sq_add_sq]
  simp only [sq]
  rw [Finset.sum_mul_sum, Finset.sum_mul_sum, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun j _ => ?_
  rw [mul_sub, Real.cos_sub (ω * τ i) (ω * τ j)]
  ring

section Helpers2

variable {ι : Type*} [Fintype ι]

/-- Recentring the delays by a constant does not change the alignment energy. -/
lemma alignment_eq_sq_add_sq_shift (w τ : ι → ℝ) (ω c : ℝ) :
    alignment w τ ω =
      (∑ i, w i * Real.cos (ω * (τ i - c))) ^ 2
        + (∑ i, w i * Real.sin (ω * (τ i - c))) ^ 2 := by
  have hshift : alignment w τ ω = alignment w (fun i => τ i - c) ω := by
    simp only [alignment]
    have hp : phasor w τ ω = Complex.exp (-(ω * c : ℂ) * Complex.I) * phasor w (fun i => τ i - c) ω := by
      simp [phasor]
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro i _
      rw [mul_left_comm, ← Complex.exp_add]
      congr 1
      ring
    rw [hp, Complex.normSq_mul]
    have heq : Complex.exp (-(↑ω * ↑c) * Complex.I) = Complex.exp ((-(ω * c) : ℝ) * Complex.I) := by
      congr 1; simp
    rw [heq]
    have h1 : Complex.normSq (Complex.exp ((-(ω * c) : ℝ) * Complex.I)) = 1 := by
      simp [Complex.normSq, Complex.exp_re, Complex.exp_im]
      ring_nf
      rw [Real.cos_sq_add_sin_sq]
    rw [h1, one_mul]
  rw [hshift, alignment_eq_sq_add_sq w (fun i => τ i - c) ω]

/-- The squared in-phase component lower bounds the alignment energy. -/
lemma sq_cos_le_alignment (w τ : ι → ℝ) (ω c : ℝ) :
    (∑ i, w i * Real.cos (ω * (τ i - c))) ^ 2 ≤ alignment w τ ω := by
  rw [alignment_eq_sq_add_sq_shift w τ ω c]
  exact le_add_of_nonneg_right (sq_nonneg _)

/-- Nonnegativity of the weighted delay variance. -/
lemma delayVariance_nonneg (w τ : ι → ℝ) (hw : ∀ i, 0 ≤ w i) :
    0 ≤ delayVariance w τ := by
  exact Finset.sum_nonneg fun i _ => mul_nonneg (hw i) (sq_nonneg _)

/-- Quadratic lower bound on the recentred in-phase component. -/
lemma cos_sum_lower_bound (w τ : ι → ℝ) (ω : ℝ)
    (hw : ∀ i, 0 ≤ w i) (hsum : ∑ i, w i = 1) :
    1 - ω ^ 2 * delayVariance w τ / 2
      ≤ ∑ i, w i * Real.cos (ω * (τ i - weightedMean w τ)) := by
  have h1 : ∀ x : ℝ, 1 - x ^ 2 / 2 ≤ Real.cos x := fun _ => Real.one_sub_sq_div_two_le_cos
  have h2 : ∀ i, w i * (1 - (ω * (τ i - weightedMean w τ)) ^ 2 / 2)
      ≤ w i * Real.cos (ω * (τ i - weightedMean w τ)) := fun i =>
    mul_le_mul_of_nonneg_left (h1 _) (hw i)
  calc 1 - ω ^ 2 * delayVariance w τ / 2
      = (∑ i, w i) - ω ^ 2 * delayVariance w τ / 2 := by rw [hsum]
    _ = ∑ i, w i * (1 - (ω * (τ i - weightedMean w τ)) ^ 2 / 2) := by
        rw [delayVariance, weightedMean, Finset.mul_sum]
        rw [show (∑ i, w i) = ∑ i, w i * 1 by simp]
        rw [show (∑ i, ω ^ 2 * (w i * (τ i - ∑ i, w i * τ i) ^ 2)) / 2 =
                ∑ i, ω ^ 2 * (w i * (τ i - ∑ i, w i * τ i) ^ 2) / 2 by
          rw [div_eq_iff (by norm_num : (2:ℝ) ≠ 0), Finset.sum_mul]
          exact Finset.sum_congr rfl fun i _ => by ring]
        rw [← Finset.sum_sub_distrib]
        exact Finset.sum_congr rfl fun i _ => by ring
    _ ≤ ∑ i, w i * Real.cos (ω * (τ i - weightedMean w τ)) :=
        Finset.sum_le_sum fun i _ => h2 i

end Helpers2

/-- Normalized nonnegative weights keep modeled alignment in the unit interval. -/
theorem alignment_efficiency_unit_interval
    {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω : ℝ)
    (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i, w i = 1) :
    0 ≤ alignment w τ ω ∧ alignment w τ ω ≤ 1 := by
  refine ⟨Complex.normSq_nonneg _, ?_⟩
  rw [phasor_energy_pairwise_identity w τ ω]
  calc ∑ i, ∑ j, w i * w j * Real.cos (ω * (τ i - τ j))
      ≤ ∑ i, ∑ j, w i * w j * 1 :=
        Finset.sum_le_sum fun i _ => Finset.sum_le_sum fun j _ =>
          mul_le_mul_of_nonneg_left (Real.cos_le_one _) (mul_nonneg (hw i) (hw j))
    _ = (∑ i, w i) * (∑ j, w j) := by
        rw [Finset.sum_mul]
        exact Finset.sum_congr rfl fun i _ => by rw [Finset.mul_sum]; simp
    _ = 1 := by rw [hsum]; ring

/-- Alignment loss is bounded by angular frequency squared times weighted delay variance. -/
theorem delay_variance_bounds_alignment_loss
    {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω : ℝ)
    (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i, w i = 1) :
    1 - alignment w τ ω ≤ ω ^ 2 * delayVariance w τ := by
  have h1 := cos_sum_lower_bound w τ ω hw hsum
  have h2 := sq_cos_le_alignment w τ ω (weightedMean w τ)
  have h3 := alignment_efficiency_unit_interval w τ ω hw hsum
  by_cases h : 1 - ω ^ 2 * delayVariance w τ / 2 ≤ 0
  · linarith [h3.1]
  · have hpos : 0 < 1 - ω ^ 2 * delayVariance w τ / 2 := not_le.mp h
    have hsq : (1 - ω ^ 2 * delayVariance w τ / 2) ^ 2
        ≤ (∑ i, w i * Real.cos (ω * (τ i - weightedMean w τ))) ^ 2 := by gcongr
    nlinarith [le_trans hsq h2]

/-- The declared delay-variance budget is sufficient throughout a bounded frequency band. -/
theorem alignment_budget_sufficient_for_band
    {ι : Type*} [Fintype ι]
    (w τ : ι → ℝ) (ω Ω q : ℝ)
    (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i, w i = 1)
    (hΩ : 0 < Ω)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hband : |ω| ≤ Ω)
    (hbudget : delayVariance w τ ≤ (1 - q) / Ω ^ 2) :
    q ≤ alignment w τ ω := by
  have h1 : 1 - alignment w τ ω ≤ ω ^ 2 * delayVariance w τ :=
    delay_variance_bounds_alignment_loss w τ ω hw hsum
  have h2 : ω ^ 2 ≤ Ω ^ 2 := by
    have := abs_le.mp hband
    nlinarith
  have h3 : ω ^ 2 * delayVariance w τ ≤ ω ^ 2 * ((1 - q) / Ω ^ 2) := by
    apply mul_le_mul_of_nonneg_left hbudget
    positivity
  have h4 : ω ^ 2 * ((1 - q) / Ω ^ 2) ≤ 1 - q := by
    have hdiv : ω ^ 2 / Ω ^ 2 ≤ 1 := div_le_one_of_le₀ h2 (sq_nonneg Ω)
    calc ω ^ 2 * ((1 - q) / Ω ^ 2) = (ω ^ 2 / Ω ^ 2) * (1 - q) := by ring
      _ ≤ 1 * (1 - q) := by apply mul_le_mul_of_nonneg_right hdiv; linarith
      _ = 1 - q := by ring
  linarith

/-- A common delay rotates the phasor but preserves its unit energy. -/
theorem equal_delay_perfect_alignment
    {ι : Type*} [Fintype ι] [Nonempty ι]
    (w τ : ι → ℝ) (ω τ₀ : ℝ)
    (hsum : ∑ i, w i = 1)
    (hτ : ∀ i, τ i = τ₀) :
    alignment w τ ω = 1 := by
  simp [alignment, phasor, hτ]
  rw [← Finset.sum_mul, ← Complex.ofReal_sum, hsum]
  simp
  rw [Complex.normSq_eq_norm_sq]
  have h : -(↑ω * (τ₀ : ℂ) * Complex.I) = ((-ω * τ₀ : ℝ) : ℂ) * Complex.I := by simp
  rw [h, Complex.norm_exp_ofReal_mul_I]
  simp

/-- Two equally weighted channels separated by an odd half-cycle cancel exactly. -/
theorem two_channel_half_period_cancellation
    (ω T : ℝ)
    (hphase : Complex.exp (-(ω * T : ℂ) * Complex.I) = -1) :
    alignment
      (fun _ : Fin 2 => (1 : ℝ) / 2)
      (fun i : Fin 2 => if i = 0 then 0 else T)
      ω = 0 := by
  simp [alignment, phasor]
  simp only [neg_mul] at hphase ⊢
  rw [hphase]
  norm_num

end

end Viridis.SnapshotAlignment
