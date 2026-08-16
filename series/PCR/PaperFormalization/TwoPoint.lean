import Mathlib

/-!
# Two-point laws on `ℝ`

The counterexample constructions of the paper (Theorem 2 and Proposition 1) use two-point
nonnegative laws.  This file provides the measure `twoPointLaw l h q = q δ_l + (1-q) δ_h`
together with its basic integral, mean, variance and tail-mass computations.
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

/-- The two-point law putting mass `q` at `l` and mass `1 - q` at `h`. -/
noncomputable def twoPointLaw (l h q : ℝ) : Measure ℝ :=
  ENNReal.ofReal q • Measure.dirac l + ENNReal.ofReal (1 - q) • Measure.dirac h

variable {l h q : ℝ}

lemma twoPointLaw_apply {s : Set ℝ} (hs : MeasurableSet s) :
    twoPointLaw l h q s =
      ENNReal.ofReal q * s.indicator 1 l + ENNReal.ofReal (1 - q) * s.indicator 1 h := by
  simp [twoPointLaw, Measure.coe_add, Measure.coe_smul, Measure.dirac_apply' _ hs]

lemma twoPointLaw_isProbabilityMeasure (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    IsProbabilityMeasure (twoPointLaw l h q) := by
  constructor
  rw [twoPointLaw_apply MeasurableSet.univ]
  simp only [Set.indicator_univ, Pi.one_apply, mul_one]
  rw [← ENNReal.ofReal_add hq0 (by linarith)]
  simp

/-- Every real-valued function is integrable for a two-point law. -/
lemma twoPointLaw_integrable (f : ℝ → ℝ) : Integrable f (twoPointLaw l h q) := by
  rw [twoPointLaw]
  exact ((integrable_dirac (f := f) (by simp [enorm_lt_top])).smul_measure (by simp)).add_measure
    ((integrable_dirac (f := f) (by simp [enorm_lt_top])).smul_measure (by simp))

lemma twoPointLaw_integral (f : ℝ → ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    ∫ x, f x ∂(twoPointLaw l h q) = q * f l + (1 - q) * f h := by
  rw [twoPointLaw, integral_add_measure
    ((integrable_dirac (f := f) (by simp [enorm_lt_top])).smul_measure (by simp))
    ((integrable_dirac (f := f) (by simp [enorm_lt_top])).smul_measure (by simp)),
    integral_smul_measure, integral_smul_measure, integral_dirac, integral_dirac,
    ENNReal.toReal_ofReal hq0, ENNReal.toReal_ofReal (by linarith), smul_eq_mul, smul_eq_mul]

lemma twoPointLaw_mean (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    ∫ x, x ∂(twoPointLaw l h q) = q * l + (1 - q) * h :=
  twoPointLaw_integral (fun x => x) hq0 hq1

lemma twoPointLaw_variance (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    Var[fun x => x; twoPointLaw l h q]
      = q * (l - (q * l + (1 - q) * h)) ^ 2 + (1 - q) * (h - (q * l + (1 - q) * h)) ^ 2 := by
  haveI := twoPointLaw_isProbabilityMeasure (l := l) (h := h) hq0 hq1
  rw [variance_eq_integral (by fun_prop), twoPointLaw_mean hq0 hq1,
    twoPointLaw_integral (fun x => (x - (q * l + (1 - q) * h)) ^ 2) hq0 hq1]

/-- `MemLp` for the identity under a two-point law: all moments are finite. -/
lemma twoPointLaw_memLp :
    MemLp (fun x : ℝ => x) 2 (twoPointLaw l h q) := by
  refine (memLp_two_iff_integrable_sq (by fun_prop)).2 ?_
  exact twoPointLaw_integrable _

/-- Mass of a lower tail `{x | x < d}` under a two-point law with `l < d ≤ h`. -/
lemma twoPointLaw_lower_tail (hq0 : 0 ≤ q) {d : ℝ} (hl : l < d) (hh : d ≤ h) :
    (twoPointLaw l h q {x : ℝ | x < d}).toReal = q := by
  rw [twoPointLaw_apply (s := {x : ℝ | x < d}) (measurableSet_Iio (a := d))]
  have hlmem : l ∈ {x : ℝ | x < d} := hl
  have hhmem : h ∉ {x : ℝ | x < d} := by simpa using hh
  rw [Set.indicator_of_mem hlmem, Set.indicator_of_notMem hhmem]
  simp [ENNReal.toReal_ofReal hq0]

/-- Lower bound for the mass of a lower tail `{x | x < d}` under a two-point law with `l < d`. -/
lemma twoPointLaw_le_lower_tail (hq0 : 0 ≤ q) (hq1 : q ≤ 1) {d : ℝ} (hl : l < d) :
    q ≤ (twoPointLaw l h q {x : ℝ | x < d}).toReal := by
  rcases lt_or_ge h d with hh | hh
  · rw [twoPointLaw_apply (s := {x : ℝ | x < d}) (measurableSet_Iio (a := d)),
      Set.indicator_of_mem (show l ∈ {x : ℝ | x < d} from hl),
      Set.indicator_of_mem (show h ∈ {x : ℝ | x < d} from hh)]
    simp only [Pi.one_apply, mul_one]
    rw [← ENNReal.ofReal_add hq0 (by linarith)]
    simp [hq1]
  · rw [twoPointLaw_lower_tail hq0 hl hh]

/-- The two-point law is supported on the nonnegative reals when both atoms are nonnegative. -/
lemma twoPointLaw_nonneg_support (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hl : 0 ≤ l) (hh : 0 ≤ h) :
    twoPointLaw l h q {x : ℝ | 0 ≤ x} = 1 := by
  rw [twoPointLaw_apply (s := {x : ℝ | 0 ≤ x}) (measurableSet_Ici (a := (0 : ℝ)))]
  rw [Set.indicator_of_mem (show l ∈ {x : ℝ | 0 ≤ x} from hl),
    Set.indicator_of_mem (show h ∈ {x : ℝ | 0 ≤ x} from hh)]
  simp only [Pi.one_apply, mul_one]
  rw [← ENNReal.ofReal_add hq0 (by linarith)]
  simp

/-- The identity is almost surely nonnegative for a two-point law with nonnegative atoms. -/
lemma twoPointLaw_ae_nonneg (hl : 0 ≤ l) (hh : 0 ≤ h) :
    0 ≤ᵐ[twoPointLaw l h q] fun x : ℝ => x := by
  have key : ∀ᵐ x ∂(twoPointLaw l h q), (0 : ℝ) ≤ x := by
    rw [ae_iff]
    have hset : {x : ℝ | ¬ (0 : ℝ) ≤ x} = {x : ℝ | x < 0} := by ext x; simp
    rw [hset, twoPointLaw_apply (s := {x : ℝ | x < 0}) (measurableSet_Iio (a := (0 : ℝ))),
      Set.indicator_of_notMem (by simpa using hl), Set.indicator_of_notMem (by simpa using hh)]
    simp
  exact key

/-! ### The Cantelli extremal two-point law -/

/-- The Cantelli two-point law: mass `q = σ²/(σ²+a²)` at `μ - a` and mass `1 - q` at
`μ + σ²/a`.  It has mean `μ` and variance `σ²`. -/
noncomputable def cantelliTwoPoint (mu sigma a : ℝ) : Measure ℝ :=
  twoPointLaw (mu - a) (mu + sigma ^ 2 / a) (sigma ^ 2 / (sigma ^ 2 + a ^ 2))

variable {mu sigma a : ℝ}

lemma cantelliTwoPoint_q_pos (hsigma : 0 < sigma) (ha : 0 < a) :
    0 < sigma ^ 2 / (sigma ^ 2 + a ^ 2) := div_pos (by positivity) (by positivity)

lemma cantelliTwoPoint_q_lt_one (hsigma : 0 < sigma) (ha : 0 < a) :
    sigma ^ 2 / (sigma ^ 2 + a ^ 2) < 1 := by
  rw [div_lt_one (by positivity)]
  nlinarith

lemma cantelliTwoPoint_mean (hsigma : 0 < sigma) (ha : 0 < a) :
    ∫ x, x ∂(cantelliTwoPoint mu sigma a) = mu := by
  rw [cantelliTwoPoint, twoPointLaw_mean (cantelliTwoPoint_q_pos hsigma ha).le
    (cantelliTwoPoint_q_lt_one hsigma ha).le]
  have h1 : sigma ^ 2 + a ^ 2 ≠ 0 := by positivity
  field_simp
  ring

lemma cantelliTwoPoint_variance (hsigma : 0 < sigma) (ha : 0 < a) :
    Var[fun x : ℝ => x; cantelliTwoPoint mu sigma a] = sigma ^ 2 := by
  have hq0 := (cantelliTwoPoint_q_pos hsigma ha).le
  have hq1 := (cantelliTwoPoint_q_lt_one hsigma ha).le
  have hmean : sigma ^ 2 / (sigma ^ 2 + a ^ 2) * (mu - a)
      + (1 - sigma ^ 2 / (sigma ^ 2 + a ^ 2)) * (mu + sigma ^ 2 / a) = mu := by
    have h1 : sigma ^ 2 + a ^ 2 ≠ 0 := by positivity
    field_simp
    ring
  rw [cantelliTwoPoint, twoPointLaw_variance hq0 hq1, hmean]
  have h1 : sigma ^ 2 + a ^ 2 ≠ 0 := by positivity
  have h2 : a ≠ 0 := ha.ne'
  field_simp
  ring

end Viridis.Run127.PaperFormalization
