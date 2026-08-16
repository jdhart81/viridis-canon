import Mathlib

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
