/-
Copyright (c) 2025 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Formalization of "The Intelligence Bound: Thermodynamic Limits on
Learning Rate and Implications for Biosphere Information".

Lean version: leanprover/lean4:v4.24.0
Mathlib version: f897ebcf72cd16f89ab4577d0c826cd14afaafc7

Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
-/

import Mathlib

/-! ## v8 FRAMING CORRECTION (2026-06-16) — read the thermodynamic branch on the
ERASURE / MAINTENANCE side, not the acquisition side. k_B T ln 2 is NOT a floor on
*acquiring* a bit (no Landauer floor on acquisition — Wolpert); it IS the floor on
*maintaining/erasing* information. The operative cost here is the maintenance &
erasure of predictive/heritable information — see Lemma 3 (`landauer_dissipation_bound`,
the bounded-memory ⇒ dissipation core), and modules `BoundedMemoryLearning` and
`BiosphereErasureBound`, and `IB_FOOTING_CORRECTION_2026-06-16.md`. All theorem
statements below are UNCHANGED; only the physical reading is corrected. -/

/-!
# The Intelligence Bound

This module formalizes the key definitions, theorems, and predictions from
"The Intelligence Bound: Thermodynamic Limits on Learning Rate and
Implications for Biosphere Information" (Hart 2025).

## Main results

* `intelligence_bound` — **Theorem 1**: İ(τ) ≤ min(ρB, P/(k_B T ln 2))
* `data_bound_lemma_conditional` — **Lemma 1**: İ ≤ ρ · B
* `thermodynamic_bound_lemma` — **Lemma 2**: İ ≤ P/(k_B T ln 2)
* `landauer_dissipation_bound` — **Lemma 3** (renamed v9.1.0): Landauer floor ⟹ power dissipation
*   (honest bounded-memory floor: module `BoundedMemoryDissipation`)
* `learning_dissipation_link` — **Proposition 2**: Learning–dissipation link
* `conditional_conservation` — **Proposition 7**: Rational long-horizon agents preserve biosphere
* `phase_transition_regimes` — **Prediction 2**: Power-limited ↔ data-limited phase transition
* `data_wall` — **Data Wall**: Low ρ imposes hard ceiling regardless of power

## Design decisions

* All quantities live in `ENNReal` (extended non-negative reals) to handle
  potentially infinite values without partial functions.
* `SatisfiesLandauerLimit` is a predicate (hypothesis), not a derived fact,
  cleanly separating the physical assumption from its mathematical consequences.
* Mutual information is defined via `klDiv` of the joint vs. product of marginals.
  The equivalence `I(X;Y) = 0 ↔ IndepFun X Y μ` is proven using Mathlib's
  `klDiv_eq_zero_iff` (Gibbs' inequality) and `indepFun_iff_map_prod_eq_prod_map_map`.
* The conservation result (Proposition 7) uses `ENNReal` throughout and proves
  linear growth eventually dominates bounded exponential growth.

## References

* [C. Shannon, *A Mathematical Theory of Communication*][shannon1948]
* [T. Cover, J. Thomas, *Elements of Information Theory*][cover2006]
* [R. Landauer, *Irreversibility and Heat Generation in the Computing Process*][landauer1961]
* [J. Kaplan et al., *Scaling Laws for Neural Language Models*][kaplan2020]
* [J. Hoffmann et al., *Training Compute-Optimal Large Language Models*][hoffmann2022]
-/

set_option linter.mathlibStandardSet false

open scoped BigOperators Real Nat Classical Pointwise

set_option maxHeartbeats 400000
set_option maxRecDepth 4000
set_option synthInstance.maxHeartbeats 20000
set_option synthInstance.maxSize 128

set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

/-! ## §1 Information-Theoretic Definitions -/

open MeasureTheory ProbabilityTheory ENNReal InformationTheory Filter Topology

/-- Mutual information between random variables X and Y under measure μ.
    Defined as the KL divergence D_KL(P_{X,Y} ‖ P_X ⊗ P_Y). -/
def mutualInformation {Ω A B : Type*} [MeasurableSpace Ω] [MeasurableSpace A]
    [MeasurableSpace B] (μ : Measure Ω) (X : Ω → A) (Y : Ω → B) : ENNReal :=
  klDiv (μ.map (fun ω => (X ω, Y ω))) ((μ.map X).prod (μ.map Y))

/-- Shannon entropy of X under μ, defined as I(X; X). -/
def shannonEntropy {Ω A : Type*} [MeasurableSpace Ω] [MeasurableSpace A]
    (μ : Measure Ω) (X : Ω → A) : ENNReal :=
  mutualInformation μ X X

/-! ## §2 Stochastic Processes and Trajectories -/

/-- A stochastic process: sample space → time → state. -/
def Process (Ω State : Type) : Type := Ω → NNReal → State

/-- Trajectory of process X restricted to [0, t]. -/
def trajectory {Ω State : Type} (X : Process Ω State) (t : NNReal) :
    Ω → (Set.Icc (0 : NNReal) t → State) :=
  fun ω => (fun (s : Set.Icc (0 : NNReal) t) => X ω s)

instance {t : NNReal} {State : Type} [MeasurableSpace State] :
    MeasurableSpace (Set.Icc (0 : NNReal) t → State) :=
  MeasurableSpace.pi

/-- Cumulative predictive information I_t(τ) = I(X_{[0,t+τ]}; O_{[0,t]}). -/
def cumulativePredictiveInformation {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (t τ : NNReal) : ENNReal :=
  mutualInformation μ (trajectory X (t + τ)) (trajectory O t)

/-! ## §3 Core Rates and Richness -/

/-- Intelligence creation rate İ(τ) := limsup_{t→∞} I_t(τ)/t. -/
def intelligenceCreationRate {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (τ : NNReal) : ENNReal :=
  Filter.limsup (fun t : NNReal =>
    cumulativePredictiveInformation μ X O t τ / t) Filter.atTop

/-- Observation entropy H(O_{[0,t]}). -/
def observationEntropy {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (O : Process Ω State)
    (t : NNReal) : ENNReal :=
  shannonEntropy μ (trajectory O t)

/-- Observation bandwidth B := limsup_{t→∞} H(O_{[0,t]})/t. -/
def observationBandwidth {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (O : Process Ω State) : ENNReal :=
  Filter.limsup (fun t : NNReal => observationEntropy μ O t / t) Filter.atTop

/-- Predictive richness ρ(τ) := limsup_{t→∞} I_t(τ)/H(O_{[0,t]}). -/
def predictiveRichness {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (τ : NNReal) : ENNReal :=
  Filter.limsup (fun t : NNReal =>
    cumulativePredictiveInformation μ X O t τ /
    observationEntropy μ O t) Filter.atTop

/-- Finite-time predictive richness estimator ρ_t(τ) (Eq. 7). -/
def finiteTimePredictiveRichness {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (t τ : NNReal) : ENNReal :=
  cumulativePredictiveInformation μ X O t τ / observationEntropy μ O t

/-! ## §4 Landauer Limit and Thermodynamic Bound -/

/-- Proposition 2 (predicate form): P ≥ İ · k_B T ln 2. -/
def SatisfiesLandauerLimit {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (τ : NNReal) (P T kB : NNReal) : Prop :=
  (P : ENNReal) ≥ intelligenceCreationRate μ X O τ *
    ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2)

/-- Lemma 2: İ ≤ P/(k_B T ln 2). -/
theorem thermodynamic_bound_lemma {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (O : Process Ω State) (τ : NNReal) (P T kB : NNReal)
    (h_kB_pos : 0 < kB) (h_T_pos : 0 < T)
    (h_landauer : SatisfiesLandauerLimit μ X O τ P T kB) :
    intelligenceCreationRate μ X O τ ≤
      ENNReal.ofReal ((P : ℝ) / ((kB : ℝ) * (T : ℝ) * Real.log 2)) := by
  rw [ENNReal.le_ofReal_iff_toReal_le]
  · rw [le_div_iff₀ (by positivity)]
    convert ENNReal.toReal_mono _ h_landauer using 1
    · rw [ENNReal.toReal_mul, ENNReal.toReal_ofReal (by positivity)]
    · exact ENNReal.coe_ne_top
  · contrapose! h_landauer
    unfold SatisfiesLandauerLimit
    rw [h_landauer, ENNReal.top_mul]; norm_num
    exact ne_of_gt (ENNReal.ofReal_pos.mpr (mul_pos (mul_pos
      (NNReal.coe_pos.mpr h_kB_pos) (NNReal.coe_pos.mpr h_T_pos))
      (Real.log_pos one_lt_two)))
  · positivity

/-! ## §5 Bounded Memory and Dissipation -/

/-- Bounded memory: the learner's state entropy is uniformly bounded by C. -/
def BoundedMemory {Ω State : Type} [MeasurableSpace Ω] [MeasurableSpace State]
    (μ : Measure Ω) (Y : Process Ω State) (C : NNReal) : Prop :=
  ∀ t, shannonEntropy μ (fun ω => Y ω t) ≤ C

/-- **Landauer dissipation bound** (v9.1.0 — renamed from `finite_memory_dissipation`).
    Given a Landauer floor on the erasure rate and `erasureRate ≥ İ`, power
    dissipation is at least `İ · k_B T ln 2`. The former name and its unused
    `BoundedMemory` hypothesis (`h_mem`/`C`) were withdrawn: the bounded-memory →
    erasure mechanism is NOT used here. The HONEST, non-vacuous bounded-memory
    dissipation floor — with bounded memory load-bearing — is
    `Viridis.P0BoundedMemoryDissipation.bounded_memory_dissipation_floor`
    (module `BoundedMemoryDissipation`, Aristotle-verified 2026-06-21). See
    CLAIMS_MATRIX.md → P0. -/
theorem landauer_dissipation_bound {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (Y : Process Ω State) (τ : NNReal) (P T kB : NNReal)
    (erasureRate : ENNReal)
    (h_landauer : P ≥ erasureRate *
      ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2))
    (h_erasure_needed : erasureRate ≥ intelligenceCreationRate μ X Y τ) :
    (P : ENNReal) ≥ intelligenceCreationRate μ X Y τ *
      ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2) := by
  exact le_trans (mul_le_mul_right' h_erasure_needed _) h_landauer

/-- Proposition 2: Learning–dissipation link. Bounded memory + Landauer ⟹
    the system satisfies the Landauer limit predicate. -/
theorem learning_dissipation_link {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (X : Process Ω State)
    (Y : Process Ω State) (τ : NNReal) (P T kB : NNReal)
    (erasureRate : ENNReal)
    (h_landauer : P ≥ erasureRate *
      ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2))
    (h_erasure_needed : erasureRate ≥ intelligenceCreationRate μ X Y τ) :
    SatisfiesLandauerLimit μ X Y τ P T kB := by
  exact le_trans (mul_le_mul_right' h_erasure_needed _) h_landauer

/-! ## §6 Mutual Information and Independence

The key equivalence `I(X;Y) = 0 ↔ IndepFun X Y μ` is proven via:
* Forward: `klDiv_eq_zero_iff` (Gibbs' inequality) gives measure equality,
  then `indepFun_iff_map_prod_eq_prod_map_map` converts to independence.
* Reverse: Independence → joint = product → `klDiv_self`.
-/

/-- If Y is independent of itself under a probability measure, then X and Y
    are independent. (Self-independence implies Y is a.s. constant.) -/
lemma indep_self_implies_indep_any {Ω A B : Type*} [MeasurableSpace Ω]
    [MeasurableSpace A] [MeasurableSpace B] (μ : Measure Ω)
    [IsProbabilityMeasure μ] (X : Ω → A) (Y : Ω → B)
    (hY : IndepFun Y Y μ) : IndepFun X Y μ := by
  rw [ProbabilityTheory.indepFun_iff_measure_inter_preimage_eq_mul] at hY ⊢
  have hY_const : ∀ s : Set B, MeasurableSet s →
      μ (Y ⁻¹' s) = 0 ∨ μ (Y ⁻¹' s) = 1 := by
    intro s hs
    have h_eq : μ (Y ⁻¹' s) = μ (Y ⁻¹' s) * μ (Y ⁻¹' s) := by
      simpa using hY s s hs hs
    have hfin : μ (Y ⁻¹' s) ≠ ⊤ := MeasureTheory.measure_ne_top μ _
    by_cases hzero : μ (Y ⁻¹' s) = 0
    · exact Or.inl hzero
    · right
      have hreal_pos : 0 < (μ (Y ⁻¹' s)).toReal :=
        ENNReal.toReal_pos hzero hfin
      have hreal_eq := congrArg ENNReal.toReal h_eq
      simp only [ENNReal.toReal_mul] at hreal_eq
      apply (ENNReal.toReal_eq_toReal hfin ENNReal.one_ne_top).mp
      simp only [ENNReal.toReal_one]
      nlinarith
  intro s t hs ht
  rcases hY_const t ht with ht0 | ht1
  · rw [ht0, mul_zero]
    exact MeasureTheory.measure_mono_null Set.inter_subset_right ht0
  · rw [ht1, mul_one]
    apply MeasureTheory.measure_congr
    rw [MeasureTheory.ae_eq_set]
    constructor
    · rw [show (X ⁻¹' s ∩ Y ⁻¹' t) \ X ⁻¹' s = ∅ by ext x; simp; tauto]
      exact MeasureTheory.measure_empty
    · have htcompl : μ (Y ⁻¹' tᶜ) = 0 := by
        have h := hY t tᶜ ht ht.compl
        rw [show Y ⁻¹' t ∩ Y ⁻¹' tᶜ = ∅ by ext; simp,
          MeasureTheory.measure_empty, ht1, one_mul] at h
        exact h.symm
      exact MeasureTheory.measure_mono_null (by intro x hx; simp_all) htcompl

/-- Mutual information is zero iff X and Y are independent.
    Forward direction uses Mathlib's `klDiv_eq_zero_iff` (Gibbs' inequality)
    to derive joint = product of marginals from D_KL = 0.
    Reverse direction follows from independence → joint = product → klDiv_self. -/
lemma mutualInformation_eq_zero_iff_indep {Ω A B : Type*}
    [MeasurableSpace Ω] [MeasurableSpace A] [MeasurableSpace B]
    (μ : Measure Ω) [IsFiniteMeasure μ] (X : Ω → A) (Y : Ω → B)
    (hX : AEMeasurable X μ) (hY : AEMeasurable Y μ) :
    mutualInformation μ X Y = 0 ↔ IndepFun X Y μ := by
  unfold mutualInformation
  rw [InformationTheory.klDiv_eq_zero_iff,
    ProbabilityTheory.indepFun_iff_map_prod_eq_prod_map_map hX hY]

/-- Entropy is zero iff the variable is independent of itself. -/
lemma entropy_eq_zero_iff_indep_self {Ω A : Type*} [MeasurableSpace Ω]
    [MeasurableSpace A] (μ : Measure Ω) [IsFiniteMeasure μ] (X : Ω → A)
    (hX : AEMeasurable X μ) :
    shannonEntropy μ X = 0 ↔ IndepFun X X μ := by
  apply mutualInformation_eq_zero_iff_indep μ X X hX hX

/-- If H(Y) = 0 then I(X; Y) = 0 (probability measure version). -/
lemma entropy_eq_zero_implies_mutualInformation_eq_zero {Ω A B : Type*}
    [MeasurableSpace Ω] [MeasurableSpace A] [MeasurableSpace B]
    (μ : Measure Ω) [IsProbabilityMeasure μ] (X : Ω → A) (Y : Ω → B)
    (hX : AEMeasurable X μ) (hY : AEMeasurable Y μ)
    (hH : shannonEntropy μ Y = 0) :
    mutualInformation μ X Y = 0 := by
  have := entropy_eq_zero_iff_indep_self μ Y hY
  exact mutualInformation_eq_zero_iff_indep μ X Y hX hY |>.2
    (indep_self_implies_indep_any μ X Y (this.mp hH))

/-- If H(Y) = 0 then I(X; Y) = 0 (general version handling non-measurable cases). -/
lemma mutualInformation_eq_zero_of_entropy_eq_zero {Ω A B : Type*}
    [MeasurableSpace Ω] [MeasurableSpace A] [MeasurableSpace B]
    (μ : Measure Ω) [IsProbabilityMeasure μ] (X : Ω → A) (Y : Ω → B)
    (hH : shannonEntropy μ Y = 0) :
    mutualInformation μ X Y = 0 := by
  by_cases hY : AEMeasurable Y μ
  · by_cases hX : AEMeasurable X μ
    · exact entropy_eq_zero_implies_mutualInformation_eq_zero μ X Y hX hY hH
    · unfold mutualInformation
      rw [MeasureTheory.Measure.map_of_not_aemeasurable hX]
      rw [Measure.map_of_not_aemeasurable]
      · simp +decide [klDiv]
      · exact fun h => hX <| h.fst
  · unfold mutualInformation
    rw [MeasureTheory.Measure.map_of_not_aemeasurable]
    · rw [MeasureTheory.Measure.map_of_not_aemeasurable hY]; norm_num
    · exact fun h => hY <| h.snd

/-! ## §7 Data-Processing Bound (Lemma 1) -/

/-- Finite bandwidth implies observation entropy is eventually finite. -/
lemma eventually_finite_entropy {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) (O : Process Ω State)
    (hB : observationBandwidth μ O ≠ ⊤) :
    ∀ᶠ t in Filter.atTop, observationEntropy μ O t ≠ ⊤ := by
  contrapose! hB
  refine' le_antisymm _ _ <;> simp_all +decide [observationBandwidth]
  refine' le_antisymm _ _ <;> simp_all +decide [Filter.limsup_eq]
  intro b x hx; obtain ⟨y, hy₁, hy₂⟩ := hB x; specialize hx y hy₁; aesop

/-- ENNReal division identity: a/c = (a/b) · (b/c) when b ∈ (0, ∞). -/
lemma ennreal_div_eq_div_mul_div (a b c : ENNReal)
    (hb0 : b ≠ 0) (hbt : b ≠ ⊤) :
    a / c = (a / b) * (b / c) := by
  simp_all +decide [div_eq_mul_inv, mul_assoc]
  simp_all +decide [← mul_assoc, ENNReal.inv_mul_cancel]

/-- Pointwise decomposition: I_t/t = (I_t/H_t) · (H_t/t) when H_t < ∞. -/
lemma decomposition_lemma_pointwise {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Process Ω State) (O : Process Ω State) (t τ : NNReal)
    (h_finite : observationEntropy μ O t ≠ ⊤) :
    cumulativePredictiveInformation μ X O t τ / t =
    (cumulativePredictiveInformation μ X O t τ / observationEntropy μ O t) *
    (observationEntropy μ O t / t) := by
  by_cases h : observationEntropy μ O t = 0 <;>
    simp_all +decide [div_mul_div_cancel₀]
  · apply mutualInformation_eq_zero_of_entropy_eq_zero; assumption
  · exact ennreal_div_eq_div_mul_div _ _ _ h h_finite

/-- The decomposition holds eventually (for all sufficiently large t). -/
lemma intelligence_rate_eq_product_eventually {Ω State : Type}
    [MeasurableSpace Ω] [MeasurableSpace State] (μ : Measure Ω)
    [IsProbabilityMeasure μ] (X : Process Ω State) (O : Process Ω State)
    (τ : NNReal) (hB : observationBandwidth μ O ≠ ⊤) :
    ∀ᶠ t in Filter.atTop,
      cumulativePredictiveInformation μ X O t τ / t =
      (cumulativePredictiveInformation μ X O t τ /
        observationEntropy μ O t) *
      (observationEntropy μ O t / t) := by
  have := eventually_finite_entropy μ O hB
  filter_upwards [this] with t ht using decomposition_lemma_pointwise μ X O t τ ht

/-- Limsup decomposition of intelligence rate. -/
lemma limsup_decomposition {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Process Ω State) (O : Process Ω State) (τ : NNReal)
    (hB : observationBandwidth μ O ≠ ⊤) :
    intelligenceCreationRate μ X O τ =
    Filter.limsup (fun t : NNReal =>
      (cumulativePredictiveInformation μ X O t τ /
        observationEntropy μ O t) *
      (observationEntropy μ O t / t)) Filter.atTop := by
  convert Filter.limsup_congr
    (intelligence_rate_eq_product_eventually μ X O τ hB) using 1

/-- Lemma 1 (data-processing bound): İ ≤ ρ · B.
    Requires ρ ≠ ⊤ (satisfied when ρ ∈ [0, 1]). -/
theorem data_bound_lemma_conditional {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Process Ω State) (O : Process Ω State) (τ : NNReal)
    (hB : observationBandwidth μ O ≠ ⊤)
    (hRho : predictiveRichness μ X O τ ≠ ⊤) :
    intelligenceCreationRate μ X O τ ≤
      predictiveRichness μ X O τ * observationBandwidth μ O := by
  convert limsup_decomposition μ X O τ hB |> fun h => h.trans_le (?_)
  apply_rules [ENNReal.limsup_mul_le']
  · contrapose! hB; aesop
  · exact Or.inl hRho

/-! ## §8 The Intelligence Bound (Theorem 1) -/

/-- **Theorem 1**: The Intelligence Bound.
    İ(τ) ≤ min(ρB, P/(k_B T ln 2)). -/
theorem intelligence_bound {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Process Ω State) (O : Process Ω State) (τ : NNReal)
    (P T kB : NNReal) (h_kB_pos : 0 < kB) (h_T_pos : 0 < T)
    (h_landauer : SatisfiesLandauerLimit μ X O τ P T kB)
    (hB : observationBandwidth μ O ≠ ⊤)
    (hRho_le_one : predictiveRichness μ X O τ ≤ 1) :
    intelligenceCreationRate μ X O τ ≤
      min (predictiveRichness μ X O τ * observationBandwidth μ O)
        (ENNReal.ofReal ((P : ℝ) / ((kB : ℝ) * (T : ℝ) * Real.log 2))) := by
  refine' le_min _ _
  · apply_rules [data_bound_lemma_conditional]
    exact ne_of_lt (lt_of_le_of_lt hRho_le_one ENNReal.one_lt_top)
  · exact thermodynamic_bound_lemma μ X O τ P T kB h_kB_pos h_T_pos h_landauer

/-! ## §9 Phase Transitions (Prediction 2) -/

/-- Thermodynamic factor K = k_B · T · ln 2. -/
def thermodynamicFactor (T kB : NNReal) : ENNReal :=
  ENNReal.ofReal ((kB : ℝ) * (T : ℝ) * Real.log 2)

/-- Critical power P* = ρ · B · K (phase boundary). -/
def criticalPower (ρ B : ENNReal) (T kB : NNReal) : ENNReal :=
  ρ * B * thermodynamicFactor T kB

/-- K is positive and finite given positive temperature and Boltzmann constant. -/
lemma thermodynamic_factor_pos_finite (T kB : NNReal)
    (h_kB_pos : 0 < kB) (h_T_pos : 0 < T) :
    0 < thermodynamicFactor T kB ∧ thermodynamicFactor T kB ≠ ⊤ := by
  constructor
  · rw [thermodynamicFactor]
    exact ENNReal.ofReal_pos.mpr (mul_pos
      (mul_pos (NNReal.coe_pos.mpr h_kB_pos) (NNReal.coe_pos.mpr h_T_pos))
      (Real.log_pos one_lt_two))
  · rw [thermodynamicFactor]
    exact ENNReal.ofReal_ne_top

/-- Phase transition algebra: min(a, b/k) resolves by comparing b to a·k. -/
theorem phase_transition_algebra (ρB P_enn K : ENNReal)
    (hK0 : K ≠ 0) (hKt : K ≠ ⊤) :
    (P_enn < ρB * K → min ρB (P_enn / K) = P_enn / K) ∧
    (P_enn ≥ ρB * K → min ρB (P_enn / K) = ρB) := by
  constructor
  · intro h
    apply min_eq_right
    exact (ENNReal.div_le_iff_le_mul (Or.inl hK0) (Or.inl hKt)).2 (le_of_lt h)
  · intro h
    apply min_eq_left
    exact (ENNReal.le_div_iff_mul_le (Or.inl hK0) (Or.inl hKt)).2 h

/-- Data-limited regime: P ≥ P*. -/
def IsDataLimited (ρ B : ENNReal) (P T kB : NNReal) : Prop :=
  (P : ENNReal) ≥ criticalPower ρ B T kB

/-- Power-limited regime: P < P*. -/
def IsPowerLimited (ρ B : ENNReal) (P T kB : NNReal) : Prop :=
  (P : ENNReal) < criticalPower ρ B T kB

/-- **Prediction 2**: Phase transition between power-limited and data-limited regimes.
    Below P*: bound = P/K (power-limited). Above P*: bound = ρB (data-limited). -/
theorem phase_transition_regimes (ρ B : ENNReal) (P T kB : NNReal)
    (h_kB_pos : 0 < kB) (h_T_pos : 0 < T) :
    ((P : ENNReal) < criticalPower ρ B T kB →
      min (ρ * B) ((P : ENNReal) / thermodynamicFactor T kB) =
        (P : ENNReal) / thermodynamicFactor T kB) ∧
    ((P : ENNReal) ≥ criticalPower ρ B T kB →
      min (ρ * B) ((P : ENNReal) / thermodynamicFactor T kB) = ρ * B) := by
  let K := thermodynamicFactor T kB
  have hK_pos_finite := thermodynamic_factor_pos_finite T kB h_kB_pos h_T_pos
  have hK0 : K ≠ 0 := ne_of_gt hK_pos_finite.1
  have hKt : K ≠ ⊤ := hK_pos_finite.2
  have h_alg := phase_transition_algebra (ρ * B) P K hK0 hKt
  simp [criticalPower] at *
  exact h_alg

/-! ## §10 ρ-Dependence (Prediction 1) and Data Wall -/

/-- **Prediction 1**: In the data-limited regime, the bound = ρ · B. -/
theorem prediction1_rho_dependence (ρ B : ENNReal) (P T kB : NNReal)
    (h_kB_pos : 0 < kB) (h_T_pos : 0 < T)
    (h_data_limited : IsDataLimited ρ B P T kB) :
    min (ρ * B) (ENNReal.ofReal ((P : ℝ) /
      ((kB : ℝ) * (T : ℝ) * Real.log 2))) = ρ * B := by
  let K_real := (kB : ℝ) * (T : ℝ) * Real.log 2
  let K := thermodynamicFactor T kB
  have hK_real_pos : 0 < K_real :=
    mul_pos (mul_pos (NNReal.coe_pos.mpr h_kB_pos) (NNReal.coe_pos.mpr h_T_pos))
      (Real.log_pos one_lt_two)
  have h_div_eq : (P : ENNReal) / K =
      ENNReal.ofReal ((P : ℝ) / K_real) := by
    rw [show K = ENNReal.ofReal K_real from rfl]
    rw [ENNReal.ofReal_div_of_pos hK_real_pos, ENNReal.ofReal_coe_nnreal]
  have h_phase := phase_transition_regimes ρ B P T kB h_kB_pos h_T_pos
  rw [IsDataLimited, criticalPower] at h_data_limited
  rw [← h_div_eq]
  exact h_phase.2 h_data_limited

/-- **Data Wall Theorem**: Low ρ imposes a hard ceiling on İ regardless of power.
    If ρ ≤ ρ_max, then İ ≤ ρ_max · B. -/
theorem data_wall {Ω State : Type} [MeasurableSpace Ω]
    [MeasurableSpace State] (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Process Ω State) (O : Process Ω State) (τ : NNReal)
    (P T kB : NNReal) (ρ_max : ENNReal)
    (h_kB_pos : 0 < kB) (h_T_pos : 0 < T)
    (h_landauer : SatisfiesLandauerLimit μ X O τ P T kB)
    (hB : observationBandwidth μ O ≠ ⊤)
    (hRho_le_one : predictiveRichness μ X O τ ≤ 1)
    (h_rho_bound : predictiveRichness μ X O τ ≤ ρ_max)
    (h_data_limited : IsDataLimited (predictiveRichness μ X O τ)
      (observationBandwidth μ O) P T kB) :
    intelligenceCreationRate μ X O τ ≤ ρ_max * observationBandwidth μ O := by
  have h_bound := intelligence_bound μ X O τ P T kB h_kB_pos h_T_pos
    h_landauer hB hRho_le_one
  refine' le_trans h_bound (min_le_iff.mpr _)
  exact Or.inl (mul_le_mul_right' h_rho_bound _)

/-! ## §11 Conditional Conservation (Proposition 7) -/

/-- Parameters for the biosphere conservation scenario. -/
structure BiosphereScenario where
  (T : NNReal)
  (degradationRate : NNReal)
  (initialPotential : NNReal)
  (exploitationRate : NNReal)
  (preservationRate : NNReal)
  (hT : T > 1 / degradationRate)
  (h_deg_pos : degradationRate > 0)
  (h_init_pos : initialPotential > 0)
  (h_exploit_high : exploitationRate > preservationRate)
  (h_preserve_pos : preservationRate > 0)

/-- Utility under preservation: r_P · Φ₀ · T (linear growth). -/
def utilityPreservation (params : BiosphereScenario) : ENNReal :=
  params.preservationRate * params.initialPotential * params.T

/-- Utility under exploitation: r_E · Φ₀ · (1 − e^{−λT})/λ (bounded growth). -/
def utilityExploitation (params : BiosphereScenario) : ENNReal :=
  ENNReal.ofReal (
    (params.exploitationRate : ℝ) * (params.initialPotential : ℝ) *
    ((1 - Real.exp (-(params.degradationRate : ℝ) * (params.T : ℝ))) /
      (params.degradationRate : ℝ)))

/-- Core inequality: ∃ T₀ such that for T > T₀, linear preservation utility
    exceeds bounded exploitation utility. -/
theorem conditional_conservation_core
    (degRate initialPot r_E r_P : NNReal)
    (h_deg_pos : degRate > 0) (h_init_pos : initialPot > 0)
    (h_exploit_high : r_E > r_P) (h_preserve_pos : r_P > 0) :
    ∃ T₀ : NNReal, ∀ T : NNReal, T > T₀ →
      (r_P * initialPot * T : ENNReal) >
      ENNReal.ofReal ((r_E : ℝ) * (initialPot : ℝ) *
        ((1 - Real.exp (-(degRate : ℝ) * (T : ℝ))) / (degRate : ℝ))) := by
  let T₀ : NNReal := r_E / (r_P * degRate) + 1
  refine ⟨T₀, fun T hT => ?_⟩
  have hdeg : (0 : ℝ) < degRate := NNReal.coe_pos.mpr h_deg_pos
  have hinit : (0 : ℝ) < initialPot := NNReal.coe_pos.mpr h_init_pos
  have hrp : (0 : ℝ) < r_P := NNReal.coe_pos.mpr h_preserve_pos
  have hlinear : (r_E : ℝ) * initialPot / degRate <
      (r_P : ℝ) * initialPot * T := by
    have hTreal : (r_E : ℝ) / ((r_P : ℝ) * degRate) + 1 < T := by
      exact_mod_cast hT
    have hden : 0 < (r_P : ℝ) * degRate := mul_pos hrp hdeg
    have hprod : (r_E : ℝ) < (r_P : ℝ) * degRate * T := by
      have := (div_lt_iff₀ hden).mp (lt_trans (lt_add_one _) hTreal)
      nlinarith
    apply (div_lt_iff₀ hdeg).2
    nlinarith
  have hre : (0 : ℝ) ≤ r_E := NNReal.coe_nonneg r_E
  have hexp : 0 ≤ Real.exp (-(degRate : ℝ) * (T : ℝ)) :=
    (Real.exp_pos _).le
  have hn : (r_E : ℝ) * initialPot *
      (1 - Real.exp (-(degRate : ℝ) * (T : ℝ))) ≤
      (r_E : ℝ) * initialPot := by
    nlinarith [mul_nonneg hre (le_of_lt hinit)]
  have hexploit : (r_E : ℝ) * initialPot *
      ((1 - Real.exp (-(degRate : ℝ) * (T : ℝ))) / degRate) ≤
      (r_E : ℝ) * initialPot / degRate := by
    calc
      _ = ((r_E : ℝ) * initialPot *
          (1 - Real.exp (-(degRate : ℝ) * (T : ℝ)))) / degRate := by ring
      _ ≤ ((r_E : ℝ) * initialPot) / degRate :=
        (div_le_div_iff_of_pos_right hdeg).2 hn
      _ = _ := by ring
  have hupper_nonneg : 0 ≤ (r_E : ℝ) * initialPot / degRate := by positivity
  refine lt_of_le_of_lt (ENNReal.ofReal_le_ofReal hexploit) ?_
  change ENNReal.ofReal ((r_E : ℝ) * initialPot / degRate) <
    ((↑(r_P * initialPot * T) : ENNReal))
  rw [ENNReal.ofReal_lt_coe_iff hupper_nonneg]
  exact_mod_cast hlinear

/-- Helper to construct a `BiosphereScenario`. -/
def makeScenario (degRate initialPot r_E r_P : NNReal)
    (h_deg_pos : degRate > 0) (h_init_pos : initialPot > 0)
    (h_exploit_high : r_E > r_P) (h_preserve_pos : r_P > 0)
    (T : NNReal) (hT : T > 1 / degRate) : BiosphereScenario :=
  { T := T, degradationRate := degRate, initialPotential := initialPot,
    exploitationRate := r_E, preservationRate := r_P,
    hT := hT, h_deg_pos := h_deg_pos, h_init_pos := h_init_pos,
    h_exploit_high := h_exploit_high, h_preserve_pos := h_preserve_pos }

/-- **Proposition 7**: Conditional Conservation.
    For any valid parameters, ∃ T₀ such that ∀ T > T₀,
    preservation utility > exploitation utility. -/
theorem conditional_conservation
    (degRate initialPot r_E r_P : NNReal)
    (h_deg_pos : degRate > 0) (h_init_pos : initialPot > 0)
    (h_exploit_high : r_E > r_P) (h_preserve_pos : r_P > 0) :
    ∃ T₀ : NNReal, ∀ T : NNReal, T > T₀ →
      ∃ (hT : T > 1 / degRate),
        utilityPreservation (makeScenario degRate initialPot r_E r_P
          h_deg_pos h_init_pos h_exploit_high h_preserve_pos T hT) >
        utilityExploitation (makeScenario degRate initialPot r_E r_P
          h_deg_pos h_init_pos h_exploit_high h_preserve_pos T hT) := by
  obtain ⟨T₁, hT₁⟩ := conditional_conservation_core degRate initialPot
    r_E r_P h_deg_pos h_init_pos h_exploit_high h_preserve_pos
  exact ⟨Max.max T₁ (1 / degRate), fun T hT =>
    ⟨lt_of_le_of_lt (le_max_right _ _) hT,
     hT₁ _ (lt_of_le_of_lt (le_max_left _ _) hT)⟩⟩

/-! ## §12 Empirical Hypotheses (Definitions Only)

These are empirically testable claims from the paper, stated as predicates
rather than theorems. They require experimental data to validate. -/

/-- Proposition 5: Biosphere ρ-richness hypothesis.
    Biosphere data has higher predictive richness than text corpora. -/
def BiosphereRichnessHypothesis (ρ_bio ρ_text : ENNReal) : Prop :=
  ρ_bio > ρ_text

/-- Prediction 3: Biosphere integrity hypothesis.
    Intact ecosystems have higher ρ than degraded ones. -/
def BiosphereIntegrityHypothesis (ρ_intact ρ_degraded : ENNReal) : Prop :=
  ρ_intact > ρ_degraded

/-- Gaia-Intelligence Proposition: Earth's biosphere is the highest-ρ source. -/
def GaiaIntelligenceProposition (ρ_biosphere : ENNReal)
    (ρ_other_sources : Set ENNReal) : Prop :=
  ∀ ρ ∈ ρ_other_sources, ρ_biosphere ≥ ρ

/-- Biosphere information potential Φ_bio(t) = ρ(t) · B(t). -/
def biosphereInformationPotential (ρ B : NNReal → ENNReal)
    (t : NNReal) : ENNReal :=
  ρ t * B t

end -- noncomputable section
