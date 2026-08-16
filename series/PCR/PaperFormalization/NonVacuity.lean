import PaperFormalization.Targets

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
