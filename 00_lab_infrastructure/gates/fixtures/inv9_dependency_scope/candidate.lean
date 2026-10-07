import Mathlib

/- Engine-3 immutable source unit: Model.lean -/

/-!
# The Run-127 model: definitions and assumptions

This file fixes the definitions used to state the frozen claims of the sealed paper
*The Precautionary Capacity Reserve* (Run-127).

Paper objects formalized here:

* the fixed positive scalars `P`, `k_B`, `T` of the model premise `r ≤ C(D) = P D / (k_B T ln 2)`
  (bundled in `RateModel`);
* the model ceiling `C` (`RateModel.ceiling`), Eq. (1);
* the required capacity `d(r) = (k_B T ln 2 / P) r` (`RateModel.requiredCapacity`), Eq. (2);
* the strict violation event `𝒱(r) = {r > C(D)}` (`RateModel.violationEvent`), Eq. (3);
* the Cantelli factor `√((1-α)/α)` (`cantelliFactor`);
* the two-moment capacity floor `d_α = [μ - σ √((1-α)/α)]_+` (`capacityFloor`), Eq. (4);
* the certified rate `r_α = P d_α / (k_B T ln 2)` (`RateModel.certifiedRate`), Eq. (5);
* the mean plug-in ceiling `r_μ = P μ / (k_B T ln 2)` (`RateModel.meanPlugInCeiling`);
* the coefficient of variation `CV(D) = σ / μ` (`coeffVar`).
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

/-- The Cantelli factor `√((1-α)/α)` attached to a one-period violation budget `α`. -/
noncomputable def cantelliFactor (alpha : ℝ) : ℝ := Real.sqrt ((1 - alpha) / alpha)

/-- The positive part `[x]_+ = max 0 x` used in the paper. -/
def posPart (x : ℝ) : ℝ := max 0 x

/-- The two-moment capacity floor `d_α = [μ - σ √((1-α)/α)]_+` of Eq. (4). -/
noncomputable def capacityFloor (mu sigma alpha : ℝ) : ℝ :=
  posPart (mu - sigma * cantelliFactor alpha)

/-- The coefficient of variation `CV(D) = σ / μ`. -/
noncomputable def coeffVar (mu sigma : ℝ) : ℝ := sigma / mu

lemma cantelliFactor_nonneg (alpha : ℝ) : 0 ≤ cantelliFactor alpha := Real.sqrt_nonneg _

lemma cantelliFactor_pos {alpha : ℝ} (h0 : 0 < alpha) (h1 : alpha < 1) :
    0 < cantelliFactor alpha :=
  Real.sqrt_pos.2 (div_pos (by linarith) h0)

lemma cantelliFactor_sq {alpha : ℝ} (h0 : 0 < alpha) (h1 : alpha < 1) :
    cantelliFactor alpha ^ 2 = (1 - alpha) / alpha :=
  Real.sq_sqrt (le_of_lt (div_pos (by linarith) h0))

lemma capacityFloor_nonneg (mu sigma alpha : ℝ) : 0 ≤ capacityFloor mu sigma alpha :=
  le_max_left _ _

lemma capacityFloor_of_pos {mu sigma alpha : ℝ} (h : 0 < mu - sigma * cantelliFactor alpha) :
    capacityFloor mu sigma alpha = mu - sigma * cantelliFactor alpha :=
  max_eq_right h.le

lemma pos_of_capacityFloor_pos {mu sigma alpha : ℝ} (h : 0 < capacityFloor mu sigma alpha) :
    0 < mu - sigma * cantelliFactor alpha := by
  rcases max_cases (0 : ℝ) (mu - sigma * cantelliFactor alpha) with ⟨he, _⟩ | ⟨he, hle⟩
  · rw [capacityFloor, posPart, he] at h; exact absurd h (lt_irrefl 0)
  · rw [capacityFloor, posPart, he] at h; exact h

/-- Fixed positive scalars of the Viridis rate premise: power `P`, Boltzmann constant `kB`,
temperature `T`.  These are held fixed during the single decision that the paper models. -/
structure RateModel where
  /-- power -/
  P : ℝ
  /-- Boltzmann constant -/
  kB : ℝ
  /-- temperature -/
  T : ℝ
  /-- power is positive -/
  hP : 0 < P
  /-- Boltzmann constant is positive -/
  hkB : 0 < kB
  /-- temperature is positive -/
  hT : 0 < T

namespace RateModel

variable (M : RateModel)

/-- The Landauer cost `k_B T ln 2`, which is positive. -/
lemma erasureCost_pos : 0 < M.kB * M.T * Real.log 2 :=
  mul_pos (mul_pos M.hkB M.hT) (Real.log_pos (by norm_num))

/-- The model ceiling `C(D) = P D / (k_B T ln 2)` of Eq. (1). -/
noncomputable def ceiling (D : ℝ) : ℝ := M.P * D / (M.kB * M.T * Real.log 2)

/-- The required capacity `d(r) = (k_B T ln 2 / P) r` of Eq. (2). -/
noncomputable def requiredCapacity (r : ℝ) : ℝ := M.kB * M.T * Real.log 2 / M.P * r

/-- The certified precautionary rate `r_α = P d_α / (k_B T ln 2)` of Eq. (5). -/
noncomputable def certifiedRate (mu sigma alpha : ℝ) : ℝ :=
  M.ceiling (capacityFloor mu sigma alpha)

/-- The mean plug-in ceiling `r_μ = P μ / (k_B T ln 2)`. -/
noncomputable def meanPlugInCeiling (mu : ℝ) : ℝ := M.ceiling mu

/-- The strict violation event `𝒱(r) = {r > C(D)}` of Eq. (3). -/
def violationEvent {Ω : Type*} (D : Ω → ℝ) (r : ℝ) : Set Ω := {ω | r > M.ceiling (D ω)}

variable {M}

lemma ceiling_lt_ceiling_iff {x y : ℝ} : M.ceiling x < M.ceiling y ↔ x < y := by
  unfold ceiling
  rw [div_lt_div_iff_of_pos_right M.erasureCost_pos, mul_lt_mul_iff_of_pos_left M.hP]

lemma ceiling_smul (c x : ℝ) : c * M.ceiling x = M.ceiling (c * x) := by
  unfold ceiling; ring

lemma requiredCapacity_ceiling (x : ℝ) : M.requiredCapacity (M.ceiling x) = x := by
  have hc : M.kB * M.T * Real.log 2 ≠ 0 := M.erasureCost_pos.ne'
  have hP : M.P ≠ 0 := M.hP.ne'
  unfold requiredCapacity ceiling
  field_simp
  exact mul_div_cancel_left₀ x (mul_pos M.hkB M.hT).ne'

/-- Eq. (3) at the certified rate: the violation event is exactly `{D < d_α}`. -/
lemma violationEvent_certifiedRate {Ω : Type*} (D : Ω → ℝ) (mu sigma alpha : ℝ) :
    M.violationEvent D (M.certifiedRate mu sigma alpha)
      = {ω | D ω < capacityFloor mu sigma alpha} := by
  ext ω
  simp only [violationEvent, certifiedRate, Set.mem_setOf_eq, gt_iff_lt]
  exact ceiling_lt_ceiling_iff

end RateModel

end Viridis.Run127.PaperFormalization

/- Engine-3 immutable source unit: Cantelli.lean -/

/-!
# Cantelli's one-sided inequality (lower tail)

The paper's Theorem 1 is a specialization of the classical Cantelli inequality.  Mathlib (at the
revision pinned by this project) contains Chebyshev's inequality but not Cantelli's one-sided
inequality, so we prove the version we need here.
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

/-- **Cantelli's inequality, lower tail.**  For a square-integrable real random variable `X` with
mean `𝔼[X]` and variance `Var[X]`, and for `a > 0`,
`ℙ(X ≤ 𝔼[X] - a) ≤ Var[X] / (Var[X] + a ^ 2)`. -/
theorem cantelli_lower_tail {Ω : Type*} [MeasurableSpace Ω] {P : Measure Ω}
    [IsProbabilityMeasure P] {X : Ω → ℝ} (hX : MemLp X 2 P) {a : ℝ} (ha : 0 < a) :
    (P {ω | X ω ≤ P[X] - a}).toReal ≤ Var[X; P] / (Var[X; P] + a ^ 2) := by
  set m : ℝ := P[X] with hm
  set v : ℝ := Var[X; P] with hv
  have hv0 : 0 ≤ v := variance_nonneg _ _
  set t : ℝ := v / a with ht
  have ht0 : 0 ≤ t := div_nonneg hv0 ha.le
  have hat : 0 < a + t := by positivity
  -- the shifted square
  set f : Ω → ℝ := fun ω => (X ω - m - t) ^ 2 with hf
  have hXm : MemLp (fun ω => X ω - m - t) 2 P := (hX.sub (memLp_const _)).sub (memLp_const _)
  have hfint : Integrable f P := hXm.integrable_sq
  have hfnn : 0 ≤ᵐ[P] f := Filter.Eventually.of_forall fun ω => sq_nonneg _
  -- the integral of the shifted square
  have hXsq : Integrable (fun ω => (X ω - m) ^ 2) P := (hX.sub (memLp_const _)).integrable_sq
  have hXint : Integrable X P := hX.integrable (by norm_num)
  have hvar : ∫ ω, (X ω - m) ^ 2 ∂P = v := (variance_eq_integral hX.1.aemeasurable).symm
  have hcent : ∫ ω, (X ω - m) ∂P = 0 := by
    rw [integral_sub hXint (integrable_const _)]
    simp [hm]
  have hlin : Integrable (fun ω => (-(2 * t)) * (X ω - m)) P :=
    (hXint.sub (integrable_const _)).const_mul _
  have hfval : ∫ ω, f ω ∂P = v + t ^ 2 := by
    have hexp : (fun ω => f ω)
        = fun ω => ((X ω - m) ^ 2 + (-(2 * t)) * (X ω - m)) + t ^ 2 := by
      funext ω; simp only [hf]; ring
    calc ∫ ω, f ω ∂P
        = ∫ ω, ((X ω - m) ^ 2 + (-(2 * t)) * (X ω - m)) + t ^ 2 ∂P := by rw [hexp]
      _ = (∫ ω, ((X ω - m) ^ 2 + (-(2 * t)) * (X ω - m)) ∂P) + ∫ _ω : Ω, t ^ 2 ∂P :=
          integral_add (hXsq.add hlin) (integrable_const _)
      _ = ((∫ ω, (X ω - m) ^ 2 ∂P) + ∫ ω, (-(2 * t)) * (X ω - m) ∂P) + t ^ 2 := by
          rw [integral_add hXsq hlin]; simp
      _ = v + t ^ 2 := by rw [hvar, integral_const_mul, hcent]; ring
  -- Markov's inequality applied to `f`
  have hmarkov : (a + t) ^ 2 * P.real {ω | (a + t) ^ 2 ≤ f ω} ≤ ∫ ω, f ω ∂P :=
    mul_meas_ge_le_integral_of_nonneg hfnn hfint _
  have hsub : {ω | X ω ≤ m - a} ⊆ {ω | (a + t) ^ 2 ≤ f ω} := by
    intro ω hω
    simp only [Set.mem_setOf_eq, hf] at hω ⊢
    nlinarith [hω, ht0, ha.le]
  have hmono : P.real {ω | X ω ≤ m - a} ≤ P.real {ω | (a + t) ^ 2 ≤ f ω} :=
    measureReal_mono hsub (measure_ne_top _ _)
  have hkey : (a + t) ^ 2 * P.real {ω | X ω ≤ m - a} ≤ v + t ^ 2 :=
    calc (a + t) ^ 2 * P.real {ω | X ω ≤ m - a}
        ≤ (a + t) ^ 2 * P.real {ω | (a + t) ^ 2 ≤ f ω} :=
          mul_le_mul_of_nonneg_left hmono (sq_nonneg _)
      _ ≤ ∫ ω, f ω ∂P := hmarkov
      _ = v + t ^ 2 := hfval
  -- conclude
  have hden : 0 < v + a ^ 2 := by positivity
  have hta : t * a = v := by rw [ht, div_mul_cancel₀ _ ha.ne']
  rw [← measureReal_def, le_div_iff₀ hden]
  set p : ℝ := P.real {ω | X ω ≤ m - a} with hp
  have hp0 : 0 ≤ p := measureReal_nonneg
  have h1 : ((a + t) * a) ^ 2 * p ≤ (v + t ^ 2) * a ^ 2 := by nlinarith [hkey, sq_nonneg a]
  have h2 : (a + t) * a = a ^ 2 + v := by rw [add_mul, hta]; ring
  have h3 : (v + t ^ 2) * a ^ 2 = v * (a ^ 2 + v) := by nlinarith [hta]
  rw [h2, h3] at h1
  have h4 : (a ^ 2 + v) * ((a ^ 2 + v) * p) ≤ (a ^ 2 + v) * v := by nlinarith [h1]
  have h5 : (a ^ 2 + v) * p ≤ v := le_of_mul_le_mul_left h4 (by linarith)
  linarith

end Viridis.Run127.PaperFormalization

/- Engine-3 immutable source unit: TwoPoint.lean -/

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

/- Engine-3 immutable source unit: Targets.lean -/

/-!
# The frozen formal targets of Run-127

This file states and proves the named Lean targets of `STATEMENT_CONTRACT.md`:

* `cantelli_capacity_certificate`            (C1, paper Theorem 1);
* `precautionary_rate_le_violation_budget`   (extra target listed in the paper, Theorem 1
   restated through the required-capacity map of Eq. (2));
* `capacity_reserve_fraction_eq`             (C2, paper Corollary 1);
* `positive_floor_sharp_two_point_counterexample` (C3, paper Theorem 2);
* `mean_only_plugin_arbitrarily_unsafe`      (C4, paper Proposition 1).
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

section Certificate

variable {Omega : Type*} [MeasurableSpace Omega] {P : Measure Omega} [IsProbabilityMeasure P]

/-- Core capacity-level form of Theorem 1: under the two-moment ambiguity class, the probability
that the capacity falls strictly below the floor `d_α` is at most `α`. -/
theorem capacityFloor_violation_prob_le {D : Omega → ℝ} (hD0 : 0 ≤ᵐ[P] D) (hD2 : MemLp D 2 P)
    {mu sigma alpha : ℝ} (ha0 : 0 < alpha) (ha1 : alpha < 1) (hmu : mu = P[D])
    (hsigma : sigma = Real.sqrt (Var[D; P])) :
    (P {omega | D omega < capacityFloor mu sigma alpha}).toReal ≤ alpha := by
  have hv0 : (0 : ℝ) ≤ Var[D; P] := variance_nonneg _ _
  have hs0 : 0 ≤ sigma := hsigma ▸ Real.sqrt_nonneg _
  have hs2 : sigma ^ 2 = Var[D; P] := by rw [hsigma]; exact Real.sq_sqrt hv0
  set k : ℝ := cantelliFactor alpha with hk
  rcases le_or_gt (mu - sigma * k) 0 with hfl | hfl
  · -- clipped floor: the violation event is `{D < 0}`, which is null
    have hzero : capacityFloor mu sigma alpha = 0 := max_eq_left hfl
    rw [hzero]
    have hnull : P {omega | D omega < 0} = 0 := by
      refine measure_mono_null (fun omega homega => ?_) (ae_iff.1 hD0)
      exact not_le.2 homega
    rw [hnull]
    simpa using ha0.le
  · have hfloor : capacityFloor mu sigma alpha = mu - sigma * k := capacityFloor_of_pos hfl
    rw [hfloor]
    rcases eq_or_lt_of_le hs0 with hs | hs
    · -- degenerate case `σ = 0`: `D = μ` almost surely
      have hvar0 : Var[D; P] = 0 := by rw [← hs2, ← hs]; ring
      have hevar : evariance D P = 0 := by
        have hne : evariance D P ≠ ⊤ := hD2.evariance_ne_top
        have : (evariance D P).toReal = 0 := hvar0
        simpa [ENNReal.toReal_eq_zero_iff, hne] using this
      have hae : D =ᵐ[P] fun _ => P[D] := (evariance_eq_zero_iff hD2.1.aemeasurable).1 hevar
      have hnull : P {omega | D omega < mu - sigma * k} = 0 := by
        refine measure_mono_null (fun omega homega => ?_) (ae_iff.1 hae)
        simp only [Set.mem_setOf_eq] at homega ⊢
        rw [← hs, zero_mul, sub_zero] at homega
        rw [← hmu]
        exact ne_of_lt homega
      rw [hnull]
      simpa using ha0.le
    · -- main case: Cantelli's inequality
      have hkpos : 0 < k := cantelliFactor_pos ha0 ha1
      have hapos : 0 < sigma * k := mul_pos hs hkpos
      have hsub : {omega | D omega < mu - sigma * k} ⊆ {omega | D omega ≤ P[D] - sigma * k} := by
        intro omega homega
        simp only [Set.mem_setOf_eq] at homega ⊢
        rw [← hmu]
        exact homega.le
      have hstep : (P {omega | D omega < mu - sigma * k}).toReal
          ≤ (P {omega | D omega ≤ P[D] - sigma * k}).toReal :=
        ENNReal.toReal_mono (measure_ne_top _ _) (measure_mono hsub)
      have hcant := cantelli_lower_tail hD2 hapos
      have hval : Var[D; P] / (Var[D; P] + (sigma * k) ^ 2) = alpha := by
        have hksq : k ^ 2 = (1 - alpha) / alpha := cantelliFactor_sq ha0 ha1
        rw [← hs2, mul_pow, hksq]
        field_simp
        ring
      linarith [hstep, hcant, hval.le, hval.ge]

/-- **C1 — `cantelli_capacity_certificate` (paper Theorem 1).**
Let `D ≥ 0` be a square-integrable capacity with population mean `μ = 𝔼[D]` and standard
deviation `σ = √Var[D]`, and let `0 < α < 1` be the one-period violation budget.  Then the
certified rate `r_α = P d_α / (k_B T ln 2)` built from the two-moment capacity floor
`d_α = [μ - σ√((1-α)/α)]_+` has strict violation probability `ℙ[𝒱(r_α)] ≤ α`. -/
theorem cantelli_capacity_certificate (M : RateModel) {D : Omega → ℝ}
    (hD0 : 0 ≤ᵐ[P] D) (hD2 : MemLp D 2 P) {mu sigma alpha : ℝ}
    (ha0 : 0 < alpha) (ha1 : alpha < 1) (hmu : mu = P[D])
    (hsigma : sigma = Real.sqrt (Var[D; P])) :
    (P (M.violationEvent D (M.certifiedRate mu sigma alpha))).toReal ≤ alpha := by
  rw [RateModel.violationEvent_certifiedRate]
  exact capacityFloor_violation_prob_le hD0 hD2 ha0 ha1 hmu hsigma

/-- **Extra target listed in the paper — `precautionary_rate_le_violation_budget`.**
The same statement expressed through the required-capacity map of Eq. (2): the capacity required
by the certified rate is exactly the floor `d_α`, and the probability that the realized capacity
falls short of it is at most the violation budget `α`. -/
theorem precautionary_rate_le_violation_budget (M : RateModel) {D : Omega → ℝ}
    (hD0 : 0 ≤ᵐ[P] D) (hD2 : MemLp D 2 P) {mu sigma alpha : ℝ}
    (ha0 : 0 < alpha) (ha1 : alpha < 1) (hmu : mu = P[D])
    (hsigma : sigma = Real.sqrt (Var[D; P])) :
    M.requiredCapacity (M.certifiedRate mu sigma alpha) = capacityFloor mu sigma alpha ∧
      (P {omega | D omega < M.requiredCapacity (M.certifiedRate mu sigma alpha)}).toReal
        ≤ alpha := by
  have hreq : M.requiredCapacity (M.certifiedRate mu sigma alpha) = capacityFloor mu sigma alpha :=
    RateModel.requiredCapacity_ceiling _
  refine ⟨hreq, ?_⟩
  rw [hreq]
  exact capacityFloor_violation_prob_le hD0 hD2 ha0 ha1 hmu hsigma

end Certificate

/-- **C2 — `capacity_reserve_fraction_eq` (paper Corollary 1).**
For `μ > 0` the certified rate is the fraction `[1 - CV(D)√((1-α)/α)]_+` of the mean plug-in
ceiling `r_μ = Pμ/(k_B T ln 2)`. -/
theorem capacity_reserve_fraction_eq (M : RateModel) {mu sigma alpha : ℝ} (hmu : 0 < mu) :
    M.certifiedRate mu sigma alpha / M.meanPlugInCeiling mu
      = posPart (1 - coeffVar mu sigma * cantelliFactor alpha) := by
  have hc : (0 : ℝ) < M.kB * M.T * Real.log 2 := M.erasureCost_pos
  have hratio : ∀ x : ℝ, M.ceiling x / M.ceiling mu = x / mu := by
    intro x
    have hc' : M.kB * M.T * Real.log 2 ≠ 0 := hc.ne'
    have hP' : M.P ≠ 0 := M.hP.ne'
    have hkB' : M.kB ≠ 0 := M.hkB.ne'
    have hT' : M.T ≠ 0 := M.hT.ne'
    have hmu' : mu ≠ 0 := hmu.ne'
    unfold RateModel.ceiling
    field_simp
  unfold RateModel.certifiedRate RateModel.meanPlugInCeiling capacityFloor coeffVar posPart
  rw [hratio]
  rcases le_or_gt (mu - sigma * cantelliFactor alpha) 0 with hfl | hfl
  · rw [max_eq_left hfl, max_eq_left]
    · simp
    · rw [div_mul_eq_mul_div, sub_nonpos, le_div_iff₀ hmu, one_mul]
      linarith
  · rw [max_eq_right hfl.le, max_eq_right]
    · field_simp
    · rw [div_mul_eq_mul_div, sub_nonneg, div_le_one hmu]
      linarith

/-- **C3 — `positive_floor_sharp_two_point_counterexample` (paper Theorem 2).**
In the positive-floor regime (`σ > 0` and `d_α > 0`), every strictly larger threshold `d > d_α`
admits a nonnegative two-point law with the *same* mean `μ` and variance `σ²` whose probability of
falling strictly below `d` exceeds `α`.  Hence no uniformly valid threshold above `d_α` exists. -/
theorem positive_floor_sharp_two_point_counterexample {mu sigma alpha : ℝ}
    (ha0 : 0 < alpha) (ha1 : alpha < 1) (hsigma : 0 < sigma)
    (hfloor : 0 < capacityFloor mu sigma alpha) {d : ℝ} (hd : capacityFloor mu sigma alpha < d) :
    ∃ l h q : ℝ, 0 ≤ l ∧ 0 ≤ h ∧ 0 < q ∧ q < 1 ∧
      IsProbabilityMeasure (twoPointLaw l h q) ∧
      twoPointLaw l h q {x : ℝ | 0 ≤ x} = 1 ∧
      ∫ x, x ∂(twoPointLaw l h q) = mu ∧
      Var[fun x : ℝ => x; twoPointLaw l h q] = sigma ^ 2 ∧
      alpha < (twoPointLaw l h q {x : ℝ | x < d}).toReal := by
  set k : ℝ := cantelliFactor alpha with hk
  have hkpos : 0 < k := cantelliFactor_pos ha0 ha1
  have hksq : k ^ 2 = (1 - alpha) / alpha := cantelliFactor_sq ha0 ha1
  have hpos : 0 < mu - sigma * k := pos_of_capacityFloor_pos hfloor
  have hfl : capacityFloor mu sigma alpha = mu - sigma * k := capacityFloor_of_pos hpos
  have hapos : 0 < sigma * k := mul_pos hsigma hkpos
  have hmu : 0 < mu := by linarith
  -- choose the lower atom strictly between the floor and `min d μ`
  set l : ℝ := (mu - sigma * k + min d mu) / 2 with hl
  have hlt : mu - sigma * k < min d mu := lt_min (hfl ▸ hd) (by linarith)
  have hl1 : mu - sigma * k < l := by rw [hl]; linarith
  have hl2 : l < min d mu := by rw [hl]; linarith
  have hld : l < d := lt_of_lt_of_le hl2 (min_le_left _ _)
  have hlmu : l < mu := lt_of_lt_of_le hl2 (min_le_right _ _)
  have hl0 : 0 ≤ l := by linarith
  obtain ⟨a, ha0', haa, hla⟩ : ∃ a : ℝ, 0 < a ∧ a < sigma * k ∧ l = mu - a :=
    ⟨mu - l, by linarith, by linarith, by ring⟩
  have hq0 : 0 < sigma ^ 2 / (sigma ^ 2 + a ^ 2) := cantelliTwoPoint_q_pos hsigma ha0'
  have hq1 : sigma ^ 2 / (sigma ^ 2 + a ^ 2) < 1 := cantelliTwoPoint_q_lt_one hsigma ha0'
  have hhi0 : 0 ≤ mu + sigma ^ 2 / a := by
    have : 0 < sigma ^ 2 / a := div_pos (by positivity) ha0'
    linarith
  have hl0' : 0 ≤ mu - a := by rw [← hla]; exact hl0
  refine ⟨mu - a, mu + sigma ^ 2 / a, sigma ^ 2 / (sigma ^ 2 + a ^ 2), hl0', hhi0, hq0, hq1,
    twoPointLaw_isProbabilityMeasure hq0.le hq1.le,
    twoPointLaw_nonneg_support hq0.le hq1.le hl0' hhi0,
    cantelliTwoPoint_mean hsigma ha0', cantelliTwoPoint_variance hsigma ha0', ?_⟩
  have hqa : alpha < sigma ^ 2 / (sigma ^ 2 + a ^ 2) := by
    have halpha : alpha = sigma ^ 2 / (sigma ^ 2 + (sigma * k) ^ 2) := by
      rw [mul_pow, hksq]
      field_simp
      ring
    rw [halpha]
    apply div_lt_div_of_pos_left (by positivity) (by positivity)
    nlinarith [ha0', haa, hapos]
  exact lt_of_lt_of_le hqa
    (twoPointLaw_le_lower_tail hq0.le hq1.le (by rw [← hla]; exact hld))

/-- **C4 — `mean_only_plugin_arbitrarily_unsafe` (paper Proposition 1).**
Mean information alone gives no nontrivial chance guarantee: for any positive fraction `theta` of
the mean plug-in ceiling and any target level `beta < 1`, there is a nonnegative two-point law
with mean exactly `μ` whose violation probability at the scheduled rate `theta * r_μ` exceeds
`beta`.  Thus the failure probability can be pushed arbitrarily close to one. -/
theorem mean_only_plugin_arbitrarily_unsafe (M : RateModel) {mu : ℝ} (hmu : 0 < mu)
    {theta : ℝ} (htheta : 0 < theta) {beta : ℝ} (hbeta : beta < 1) :
    ∃ l h q : ℝ, 0 ≤ l ∧ 0 ≤ h ∧ 0 < q ∧ q < 1 ∧
      IsProbabilityMeasure (twoPointLaw l h q) ∧
      twoPointLaw l h q {x : ℝ | 0 ≤ x} = 1 ∧
      ∫ x, x ∂(twoPointLaw l h q) = mu ∧
      beta < (twoPointLaw l h q
        (M.violationEvent (fun x : ℝ => x) (theta * M.meanPlugInCeiling mu))).toReal := by
  set eps : ℝ := min (1 / 2) ((1 - beta) / 2) with heps
  have heps0 : 0 < eps := lt_min (by norm_num) (by linarith)
  have heps1 : eps ≤ 1 / 2 := min_le_left _ _
  have hepsb : beta < 1 - eps := by
    have : eps ≤ (1 - beta) / 2 := min_le_right _ _
    linarith
  refine ⟨0, mu / eps, 1 - eps, le_refl _, (div_pos hmu heps0).le, by linarith, by linarith,
    twoPointLaw_isProbabilityMeasure (by linarith) (by linarith),
    twoPointLaw_nonneg_support (by linarith) (by linarith) le_rfl (div_pos hmu heps0).le, ?_, ?_⟩
  · rw [twoPointLaw_mean (by linarith) (by linarith)]
    field_simp
    ring
  · have hset : M.violationEvent (fun x : ℝ => x) (theta * M.meanPlugInCeiling mu)
        = {x : ℝ | x < theta * mu} := by
      ext x
      simp only [RateModel.violationEvent, RateModel.meanPlugInCeiling, Set.mem_setOf_eq,
        gt_iff_lt, RateModel.ceiling_smul]
      exact RateModel.ceiling_lt_ceiling_iff
    rw [hset]
    exact lt_of_lt_of_le hepsb
      (twoPointLaw_le_lower_tail (by linarith) (by linarith) (by positivity))

end Viridis.Run127.PaperFormalization

/- Engine-3 immutable source unit: NonVacuity.lean -/

/-!
# Explicit non-vacuity witnesses

For each frozen target we exhibit a concrete instance in which *all* hypotheses hold and the
conclusion is not degenerate:

* `cantelli_capacity_certificate_nonvacuous` / `precautionary_rate_le_violation_budget_nonvacuous`:
  a nonnegative law with `σ > 0`, a strictly positive capacity floor, and a violation event of
  strictly positive probability (`4/13`), so the certificate bound `≤ α = 1/2` is a genuine,
  non-trivial bound on a nonempty event;
* `capacity_reserve_fraction_eq_nonvacuous`: both branches of the positive part are realized
  (a strictly positive certified fraction `1/2` and a clipped fraction `0`);
* `positive_floor_sharp_two_point_counterexample_nonvacuous`: the positive-floor hypotheses are
  satisfiable, and the produced counterexample is exhibited;
* `mean_only_plugin_arbitrarily_unsafe_nonvacuous`: a law whose violation probability exceeds
  `999/1000` at the full mean plug-in rate.
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

/-- Witness model with `P = k_B = T = 1`. -/
def witnessModel : RateModel := ⟨1, 1, 1, one_pos, one_pos, one_pos⟩

/-- Witness capacity law: mass `4/13` at `1/4` and mass `9/13` at `4/3`.
It is nonnegative and has mean `1` and variance `1/4`. -/
noncomputable def witnessLaw : Measure ℝ := twoPointLaw (1 / 4) (4 / 3) (4 / 13)

lemma witnessLaw_isProbabilityMeasure : IsProbabilityMeasure witnessLaw :=
  twoPointLaw_isProbabilityMeasure (by norm_num) (by norm_num)

lemma witnessLaw_ae_nonneg : 0 ≤ᵐ[witnessLaw] fun x : ℝ => x :=
  twoPointLaw_ae_nonneg (by norm_num) (by norm_num)

lemma witnessLaw_memLp : MemLp (fun x : ℝ => x) 2 witnessLaw := twoPointLaw_memLp

lemma witnessLaw_mean : ∫ x, x ∂witnessLaw = 1 := by
  rw [witnessLaw, twoPointLaw_mean (by norm_num) (by norm_num)]
  norm_num

lemma witnessLaw_variance : Var[fun x : ℝ => x; witnessLaw] = 1 / 4 := by
  rw [witnessLaw, twoPointLaw_variance (by norm_num) (by norm_num)]
  norm_num

lemma witnessLaw_sigma : (1 : ℝ) / 2 = Real.sqrt (Var[fun x : ℝ => x; witnessLaw]) := by
  rw [witnessLaw_variance, show (1 : ℝ) / 4 = (1 / 2) ^ 2 by norm_num,
    Real.sqrt_sq (by norm_num)]

lemma cantelliFactor_half : cantelliFactor (1 / 2) = 1 := by
  unfold cantelliFactor
  norm_num

lemma capacityFloor_witness : capacityFloor 1 (1 / 2) (1 / 2) = 1 / 2 := by
  rw [capacityFloor, cantelliFactor_half, posPart]
  norm_num

lemma witnessLaw_violation_mass :
    (witnessLaw {x : ℝ | x < capacityFloor 1 (1 / 2) (1 / 2)}).toReal = 4 / 13 := by
  rw [capacityFloor_witness, witnessLaw]
  exact twoPointLaw_lower_tail (by norm_num) (by norm_num) (by norm_num)

/-- **Non-vacuity witness for C1 (`cantelli_capacity_certificate`).**
All hypotheses hold for a nonnegative law with strictly positive standard deviation and a
strictly positive capacity floor, and the certified violation event has strictly positive
probability `4/13`, which the certificate bounds by `α = 1/2`. -/
theorem cantelli_capacity_certificate_nonvacuous :
    (0 ≤ᵐ[witnessLaw] fun x : ℝ => x) ∧
    MemLp (fun x : ℝ => x) 2 witnessLaw ∧
    (0 : ℝ) < 1 / 2 ∧ (1 / 2 : ℝ) < 1 ∧
    (1 : ℝ) = ∫ x, x ∂witnessLaw ∧
    (1 / 2 : ℝ) = Real.sqrt (Var[fun x : ℝ => x; witnessLaw]) ∧
    (0 : ℝ) < 1 / 2 ∧
    0 < capacityFloor 1 (1 / 2) (1 / 2) ∧
    (witnessLaw (witnessModel.violationEvent (fun x : ℝ => x)
        (witnessModel.certifiedRate 1 (1 / 2) (1 / 2)))).toReal = 4 / 13 ∧
    (0 : ℝ) < (witnessLaw (witnessModel.violationEvent (fun x : ℝ => x)
        (witnessModel.certifiedRate 1 (1 / 2) (1 / 2)))).toReal ∧
    (witnessLaw (witnessModel.violationEvent (fun x : ℝ => x)
        (witnessModel.certifiedRate 1 (1 / 2) (1 / 2)))).toReal ≤ 1 / 2 := by
  haveI := witnessLaw_isProbabilityMeasure
  have hmass : (witnessLaw (witnessModel.violationEvent (fun x : ℝ => x)
      (witnessModel.certifiedRate 1 (1 / 2) (1 / 2)))).toReal = 4 / 13 := by
    rw [RateModel.violationEvent_certifiedRate]
    exact witnessLaw_violation_mass
  refine ⟨witnessLaw_ae_nonneg, witnessLaw_memLp, by norm_num, by norm_num,
    witnessLaw_mean.symm, witnessLaw_sigma, by norm_num, ?_, hmass, by rw [hmass]; norm_num, ?_⟩
  · rw [capacityFloor_witness]; norm_num
  · exact cantelli_capacity_certificate witnessModel witnessLaw_ae_nonneg witnessLaw_memLp
      (by norm_num) (by norm_num) witnessLaw_mean.symm witnessLaw_sigma

/-- **Non-vacuity witness for the extra paper target
(`precautionary_rate_le_violation_budget`).** -/
theorem precautionary_rate_le_violation_budget_nonvacuous :
    witnessModel.requiredCapacity (witnessModel.certifiedRate 1 (1 / 2) (1 / 2)) = 1 / 2 ∧
    (witnessLaw {x : ℝ |
        x < witnessModel.requiredCapacity (witnessModel.certifiedRate 1 (1 / 2) (1 / 2))}).toReal
      = 4 / 13 ∧
    (witnessLaw {x : ℝ |
        x < witnessModel.requiredCapacity (witnessModel.certifiedRate 1 (1 / 2) (1 / 2))}).toReal
      ≤ 1 / 2 := by
  haveI := witnessLaw_isProbabilityMeasure
  obtain ⟨hreq, hle⟩ := precautionary_rate_le_violation_budget witnessModel (alpha := 1 / 2)
    witnessLaw_ae_nonneg witnessLaw_memLp (by norm_num) (by norm_num) witnessLaw_mean.symm
    witnessLaw_sigma
  have hreq' : witnessModel.requiredCapacity (witnessModel.certifiedRate 1 (1 / 2) (1 / 2))
      = 1 / 2 := by rw [hreq, capacityFloor_witness]
  refine ⟨hreq', ?_, hle⟩
  rw [hreq, witnessLaw_violation_mass]

/-- **Non-vacuity witness for C2 (`capacity_reserve_fraction_eq`).**
Both branches of the positive part occur: a strictly positive certified fraction `1/2` at
`CV = 1/2, α = 1/2`, and a clipped fraction `0` at `CV = 2, α = 1/2`. -/
theorem capacity_reserve_fraction_eq_nonvacuous :
    witnessModel.certifiedRate 1 (1 / 2) (1 / 2) / witnessModel.meanPlugInCeiling 1 = 1 / 2 ∧
    posPart (1 - coeffVar 1 (1 / 2) * cantelliFactor (1 / 2)) = 1 / 2 ∧
    witnessModel.certifiedRate 1 2 (1 / 2) / witnessModel.meanPlugInCeiling 1 = 0 ∧
    posPart (1 - coeffVar 1 2 * cantelliFactor (1 / 2)) = 0 := by
  have h1 : posPart (1 - coeffVar 1 (1 / 2) * cantelliFactor (1 / 2)) = 1 / 2 := by
    rw [posPart, coeffVar, cantelliFactor_half]; norm_num
  have h2 : posPart (1 - coeffVar 1 2 * cantelliFactor (1 / 2)) = 0 := by
    rw [posPart, coeffVar, cantelliFactor_half]
    norm_num
  refine ⟨?_, h1, ?_, h2⟩
  · rw [capacity_reserve_fraction_eq witnessModel one_pos, h1]
  · rw [capacity_reserve_fraction_eq witnessModel one_pos, h2]

/-- **Non-vacuity witness for C3 (`positive_floor_sharp_two_point_counterexample`).**
The positive-floor hypotheses are satisfiable (`μ = 1`, `σ = 1/2`, `α = 1/2`, floor `= 1/2`) and
`d = 3/4 > 1/2` yields an explicit nonnegative two-point counterexample with mean `1`,
variance `1/4`, and violation probability strictly above `α = 1/2`. -/
theorem positive_floor_sharp_two_point_counterexample_nonvacuous :
    0 < capacityFloor 1 (1 / 2) (1 / 2) ∧ capacityFloor 1 (1 / 2) (1 / 2) < 3 / 4 ∧
    ∃ l h q : ℝ, 0 ≤ l ∧ 0 ≤ h ∧ 0 < q ∧ q < 1 ∧
      IsProbabilityMeasure (twoPointLaw l h q) ∧
      twoPointLaw l h q {x : ℝ | 0 ≤ x} = 1 ∧
      ∫ x, x ∂(twoPointLaw l h q) = 1 ∧
      Var[fun x : ℝ => x; twoPointLaw l h q] = (1 / 2 : ℝ) ^ 2 ∧
      (1 / 2 : ℝ) < (twoPointLaw l h q {x : ℝ | x < 3 / 4}).toReal := by
  have hfloor : 0 < capacityFloor 1 (1 / 2) (1 / 2) := by rw [capacityFloor_witness]; norm_num
  have hlt : capacityFloor 1 (1 / 2) (1 / 2) < 3 / 4 := by rw [capacityFloor_witness]; norm_num
  exact ⟨hfloor, hlt, positive_floor_sharp_two_point_counterexample (mu := 1) (sigma := 1 / 2)
    (alpha := 1 / 2) (by norm_num) (by norm_num) (by norm_num) hfloor hlt⟩

/-- **Non-vacuity witness for C4 (`mean_only_plugin_arbitrarily_unsafe`).**
Scheduling the *whole* mean plug-in ceiling (`θ = 1`) at mean `μ = 1` admits a nonnegative law
with mean `1` whose violation probability exceeds `999/1000`. -/
theorem mean_only_plugin_arbitrarily_unsafe_nonvacuous :
    ∃ l h q : ℝ, 0 ≤ l ∧ 0 ≤ h ∧ 0 < q ∧ q < 1 ∧
      IsProbabilityMeasure (twoPointLaw l h q) ∧
      twoPointLaw l h q {x : ℝ | 0 ≤ x} = 1 ∧
      ∫ x, x ∂(twoPointLaw l h q) = 1 ∧
      (999 / 1000 : ℝ) < (twoPointLaw l h q
        (witnessModel.violationEvent (fun x : ℝ => x)
          (1 * witnessModel.meanPlugInCeiling 1))).toReal :=
  mean_only_plugin_arbitrarily_unsafe witnessModel one_pos one_pos (by norm_num)

end Viridis.Run127.PaperFormalization
