import PaperFormalization.Cantelli
import PaperFormalization.Model
import PaperFormalization.TwoPoint

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
