import PaperFormalization.NullMartingale
import PaperFormalization.Dominance
import PaperFormalization.Wald

/-!
# Non-vacuity witnesses

Every formalized target (C1–C4) is instantiated here at an explicit model, so that none of
the theorem statements is vacuously true.

* `C3Witness`: a deterministic likelihood-ratio path for which the mixture alarm time is
  *strictly* earlier than the embedded component alarm time (`1 < 2`), so the dominance
  claim C3 is non-trivial.
* `C4Witness`: an explicit increment model, stopping time and boundary for which every
  hypothesis of C4 holds and the corridor reads `5/2 ≤ 3 < 7/2`.
* `C12Witness`: the paper's preregistered Bernoulli instance `P₀ = Bern(1/5)`,
  `P₁ = Bern(3/5)` realized as a genuinely iid sequence on `ℕ → Bool` under an infinite
  product measure.  All hypotheses of C1 and C2 hold, the mixture is not identically `1`,
  and the resulting Ville certificate is an instance of C2.
-/

namespace Viridis.Run129.PaperFormalization

open MeasureTheory ProbabilityTheory Filter
open scoped ENNReal NNReal

/-! ## C3 witness: strict dominance -/

namespace C3Witness

/-- A deterministic likelihood-ratio path with `Λ_i ≡ 3`. -/
noncomputable def Λ : ℕ → Unit → ℝ := fun _ _ => 3

lemma Λ_nonneg : ∀ n (ω : Unit), 0 ≤ Λ n ω := fun _ _ => by norm_num [Λ]

lemma component_eq (n : ℕ) : component Λ 1 n () = (1 / 2) * 3 ^ n := by
  rw [component]
  have h1 : changePrior 1 = 1 / 2 := by norm_num [changePrior]
  have h2 : ∏ _i ∈ Finset.Icc 1 n, Λ _i () = 3 ^ n := by
    simp only [Λ]
    rw [Finset.prod_const, Nat.card_Icc]
    simp
  rw [h1, h2]

lemma mixture_one : mixture Λ 1 () = 2 := by
  norm_num [mixture, mixAcc_succ, changePrior, priorTail, Λ]

lemma mixture_zero' : mixture Λ 0 () = 1 := by simp

/-- The mixture alarms at time `1`. -/
lemma firstAlarm_mixture : firstAlarm (fun n => mixture Λ n ()) 2 = (1 : ℕ∞) := by
  refine firstAlarm_eq_of_isLeast ⟨by simp [mixture_one], ?_⟩
  rintro k hk
  by_contra hcon
  have hk0 : k = 0 := by omega
  subst hk0
  rw [Set.mem_setOf_eq, mixture_zero'] at hk
  norm_num at hk

/-- The embedded change-time-`1` component alarms only at time `2`. -/
lemma firstAlarm_component : firstAlarm (fun n => component Λ 1 n ()) 2 = (2 : ℕ∞) := by
  refine firstAlarm_eq_of_isLeast ⟨?_, ?_⟩
  · rw [Set.mem_setOf_eq, component_eq]; norm_num
  · rintro k hk
    by_contra hcon
    interval_cases k <;>
      · rw [Set.mem_setOf_eq, component_eq] at hk
        norm_num at hk

/-- **Non-vacuity for C3**: the dominance conclusion holds and is strict here, so the
statement is not trivially satisfied. -/
theorem c3_nonvacuous :
    (∀ n (ω : Unit), component Λ 1 n ω ≤ mixture Λ n ω) ∧
      firstAlarm (fun n => mixture Λ n ()) 2 < firstAlarm (fun n => component Λ 1 n ()) 2 := by
  obtain ⟨hdom, _, _⟩ :=
    change_component_dominance_and_penalty Λ Λ_nonneg (ν := 1) le_rfl
      (α := 1 / 2) (by norm_num)
  refine ⟨hdom, ?_⟩
  rw [firstAlarm_mixture, firstAlarm_component]
  exact_mod_cast (by norm_num : (1 : ℕ) < 2)

end C3Witness

/-! ## C4 witness: an explicit delay corridor -/

namespace C4Witness

/-- Deterministic unit increments on a one-point probability space. -/
noncomputable def Z : ℕ → Unit → ℝ := fun _ _ => 1

/-- The stopping time: the boundary `a = 5/2` is first crossed at `m = 3`. -/
def N : Unit → ℕ := fun _ => 3

/-- The trivial filtration. -/
def 𝒢 : Filtration ℕ (inferInstance : MeasurableSpace Unit) where
  seq := fun _ => ⊥
  mono' := fun _ _ _ => le_rfl
  le' := fun _ => bot_le

lemma evidenceSum_eq (m : ℕ) : evidenceSum Z m () = (m : ℝ) := by
  simp [evidenceSum, Z]

/-- **Non-vacuity for C4**: all hypotheses hold at this model and the corridor is the
non-trivial statement `5/2 ≤ 3 < 7/2`. -/
theorem c4_nonvacuous :
    (5 : ℝ) / 2 / 1 ≤ ∫ ω, (N ω : ℝ) ∂(Measure.dirac ()) ∧
      ∫ ω, (N ω : ℝ) ∂(Measure.dirac ()) < ((5 : ℝ) / 2 + 1) / 1 := by
  have hbase :
      (5 : ℝ) / 2 / 1 ≤ ∫ ω, (N ω : ℝ) ∂(Measure.dirac ()) ∧
        ∫ ω, (N ω : ℝ) ∂(Measure.dirac ()) < ((5 : ℝ) / 2 + 1) / 1 := by
    refine bounded_overshoot_expected_delay (μ := Measure.dirac ()) (𝒢 := 𝒢) (Z := Z) (N := N)
      (B := 1) (D := 1) (zmax := 1) (a := 5 / 2)
      zero_le_one (fun j => measurable_const) (fun j ω => by norm_num [Z])
      (fun j ω => by norm_num [Z]) (fun j => by simp [Z]) one_pos (by norm_num)
      (fun j => ?_) (fun j => ?_)
      (by simp [N] : Integrable (fun ω : Unit => ((N ω : ℕ) : ℝ)) (Measure.dirac ())) ?_
    · exact indep_bot_right _
    · by_cases h : N () ≤ j
      · have hset : {ω : Unit | N ω ≤ j} = Set.univ := by
          ext ω; simp [show ω = () from rfl, h]
        rw [hset]; exact @MeasurableSet.univ _ (𝒢 j)
      · have hset : {ω : Unit | N ω ≤ j} = (∅ : Set Unit) := by
          ext ω; simp [show ω = () from rfl, h]
        rw [hset]; exact @MeasurableSet.empty _ (𝒢 j)
    · refine Filter.Eventually.of_forall fun ω => ?_
      constructor
      · refine ⟨by norm_num [N], ?_⟩
        rw [show ω = () from rfl, evidenceSum_eq]
        norm_num [N]
      · rintro m ⟨hm1, hm2⟩
        rw [show ω = () from rfl, evidenceSum_eq] at hm2
        have : (5 : ℝ) / 2 ≤ (m : ℝ) := hm2
        have : (3 : ℕ) ≤ m := by
          by_contra hcon
          push_neg at hcon
          interval_cases m <;> norm_num at this
        simpa [N] using this
  exact hbase

/-- The stopped mean is genuinely `3`, strictly inside the corridor. -/
lemma integral_N : ∫ ω, (N ω : ℝ) ∂(Measure.dirac ()) = 3 := by
  simp [N]

end C4Witness

/-! ## C1/C2 witness: the preregistered iid Bernoulli instance -/

namespace C12Witness

/-- The declared null `P₀ = Bernoulli(1/5)` (the paper's `p₀ = 0.2`). -/
noncomputable def bern : PMF Bool := PMF.bernoulli (1 / 5) (by simp)

/-- `P₀` as a measure on a single observation. -/
noncomputable def μ₀ : Measure Bool := bern.toMeasure

instance : IsProbabilityMeasure μ₀ := by unfold μ₀; infer_instance

/-- The likelihood ratio `dP₁/dP₀` for `P₁ = Bernoulli(3/5)` against `P₀ = Bernoulli(1/5)`:
`(3/5)/(1/5) = 3` on a detection and `(2/5)/(4/5) = 1/2` on a non-detection. -/
noncomputable def LR : Bool → ℝ := fun b => if b then 3 else 1 / 2

lemma LR_meas : Measurable LR := by fun_prop

lemma LR_nonneg (b : Bool) : 0 ≤ LR b := by cases b <;> norm_num [LR]

lemma LR_le (b : Bool) : |LR b| ≤ 3 := by cases b <;> norm_num [LR]

/-- The iid null on the whole observation stream. -/
noncomputable def μ : Measure (ℕ → Bool) := Measure.infinitePi (fun _ : ℕ => μ₀)

instance : IsProbabilityMeasure μ := by unfold μ; infer_instance

/-- The likelihood ratio process `Λ_j(ω) = dP₁/dP₀(X_j)`. -/
noncomputable def Λ : ℕ → (ℕ → Bool) → ℝ := fun j ω => LR (ω j)

lemma Λ_meas (j : ℕ) : Measurable (Λ j) := LR_meas.comp (measurable_pi_apply j)

lemma Λ_sm (j : ℕ) : StronglyMeasurable (Λ j) := (Λ_meas j).stronglyMeasurable

lemma Λ_nonneg (j : ℕ) (ω : ℕ → Bool) : 0 ≤ Λ j ω := LR_nonneg _

lemma Λ_bdd (j : ℕ) (ω : ℕ → Bool) : |Λ j ω| ≤ 3 := LR_le _

/-- The observations are genuinely iid. -/
lemma Λ_indep : iIndepFun Λ μ := by
  unfold Λ μ
  exact iIndepFun_infinitePi (X := fun _ : ℕ => LR) (fun _ => LR_meas)

/-- `E₀[Λ_j] = 1`: the likelihood ratio is mean one under the declared null. -/
lemma Λ_mean (j : ℕ) : ∫ ω, Λ j ω ∂μ = 1 := by
  have h1 : ∫ ω, Λ j ω ∂μ = ∫ b, LR b ∂(μ.map (fun ω => ω j)) := by
    rw [integral_map (measurable_pi_apply j).aemeasurable LR_meas.aestronglyMeasurable]; rfl
  rw [h1]
  have h2 : μ.map (fun ω : ℕ → Bool => ω j) = μ₀ := by
    unfold μ; exact Measure.infinitePi_map_eval _ j
  rw [h2, μ₀, PMF.integral_eq_sum]
  simp [bern, LR, PMF.bernoulli_apply]
  norm_num

/-- The natural filtration of the observation stream. -/
noncomputable def ℱ : Filtration ℕ (inferInstance : MeasurableSpace (ℕ → Bool)) :=
  Filtration.natural Λ Λ_sm

lemma Λ_adapted (j : ℕ) : StronglyMeasurable[ℱ j] (Λ j) :=
  Filtration.stronglyAdapted_natural Λ_sm j

lemma Λ_cond (n : ℕ) : μ[Λ (n + 1) | ℱ n] =ᵐ[μ] fun _ => (1 : ℝ) := by
  have h : μ[Λ (n + 1) | (Filtration.natural Λ Λ_sm) n]
      =ᵐ[μ] fun _ => ∫ ω, Λ (n + 1) ω ∂μ :=
    Λ_indep.condExp_natural_ae_eq_of_lt Λ_sm (Nat.lt_succ_self n)
  rw [Λ_mean (n + 1)] at h
  exact h

lemma Λ_int (j : ℕ) : Integrable (Λ j) μ :=
  (integrable_const (3 : ℝ)).mono' (Λ_meas j).aestronglyMeasurable
    (Filter.Eventually.of_forall fun ω => by simpa [Real.norm_eq_abs] using Λ_bdd j ω)

lemma A_int (n : ℕ) : Integrable (mixAcc Λ n) μ :=
  integrable_mixAcc_of_bounded Λ_meas (by norm_num) Λ_bdd n

/-- The mixture is not identically `1`: on the all-detections path it reaches the alarm
level `2` already at `n = 1`. -/
lemma mixture_one_true : mixture Λ 1 (fun _ => true) = 2 := by
  norm_num [mixture, mixAcc_succ, changePrior, priorTail, Λ, LR]

/-- The alarm event at threshold `1/α = 2` is not null: it contains the event
`{X₁ = 1}`, of probability `1/5`. -/
lemma alarm_not_null :
    (1 : ℝ≥0∞) / 5 ≤ μ {ω : ℕ → Bool | ∃ n, (2 : ℝ) ≤ mixture Λ n ω} := by
  have hsub : {ω : ℕ → Bool | ω 1 = true} ⊆ {ω : ℕ → Bool | ∃ n, (2 : ℝ) ≤ mixture Λ n ω} := by
    intro ω hω
    rw [Set.mem_setOf_eq] at hω
    refine ⟨1, ?_⟩
    have hΛ1 : Λ 1 ω = 3 := by simp [Λ, LR, hω]
    rw [mixture, mixAcc_succ, hΛ1]
    norm_num [changePrior, priorTail]
  have hval : μ {ω : ℕ → Bool | ω 1 = true} = 1 / 5 := by
    have h1 : {ω : ℕ → Bool | ω 1 = true} = (fun ω : ℕ → Bool => ω 1) ⁻¹' {true} := rfl
    rw [h1, ← Measure.map_apply (measurable_pi_apply 1) (measurableSet_singleton true)]
    have h2 : μ.map (fun ω : ℕ → Bool => ω 1) = μ₀ := by
      unfold μ; exact Measure.infinitePi_map_eval _ 1
    rw [h2, μ₀, PMF.toMeasure_apply_singleton _ _ (measurableSet_singleton true)]
    simp [bern, PMF.bernoulli_apply]
  rw [← hval]
  exact measure_mono hsub

/-- **Non-vacuity for C1 and C2**: at the preregistered iid Bernoulli instance the mixture
is a mean-one martingale, the anytime certificate at `α = 1/2` holds, and the alarm event
is neither empty nor null. -/
theorem c12_nonvacuous :
    Martingale (mixture Λ) ℱ μ ∧
    (∀ n, ∫ ω, mixture Λ n ω ∂μ = 1) ∧
    μ {ω : ℕ → Bool | ∃ n, (2 : ℝ) ≤ mixture Λ n ω} ≤ ENNReal.ofReal (1 / 2) ∧
    0 < μ {ω : ℕ → Bool | ∃ n, (2 : ℝ) ≤ mixture Λ n ω} := by
  obtain ⟨hmg, _, _, hmean⟩ :=
    anytime_change_mixture_martingale Λ_adapted Λ_nonneg Λ_int A_int Λ_cond
  have hville :=
    anytime_change_ville_certificate Λ_adapted Λ_nonneg Λ_int A_int Λ_cond
      (α := 1 / 2) (by norm_num)
  rw [show (1 : ℝ) / (1 / 2) = 2 by norm_num] at hville
  refine ⟨hmg, hmean, hville, ?_⟩
  refine lt_of_lt_of_le ?_ alarm_not_null
  simp

/-- Non-vacuity for the literal supremum form of Equation (4) at the same instance. -/
theorem c2_sup_nonvacuous :
    μ {ω : ℕ → Bool | ENNReal.ofReal (2 : ℝ) ≤ ⨆ n, ENNReal.ofReal (mixture Λ n ω)}
      ≤ ENNReal.ofReal (1 / 2) := by
  have h := anytime_change_ville_certificate_sup Λ_adapted Λ_nonneg Λ_int A_int Λ_cond
      (α := 1 / 2) (by norm_num)
  rwa [show (1 : ℝ) / (1 / 2) = 2 by norm_num] at h

end C12Witness

end Viridis.Run129.PaperFormalization
