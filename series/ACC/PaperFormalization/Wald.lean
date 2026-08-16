import PaperFormalization.Dominance

/-!
# C4: the bounded-overshoot expected-delay corridor

This file formalizes Equations (7)–(8) of `SEALED_paper.tex`:

  `N_a = inf{ m ≥ 1 : ∑_{j=1}^m Z_j ≥ a }`,   `a/D ≤ E₁[N_a] < (a + z_max)/D`.

## Explicit assumptions

The paper says: "let post-change increments `Z_i = log Λ_i` be iid, bounded above by
finite `z_max > 0`, and have mean `D = E₁ Z_i = D(P₁‖P₀) > 0` … assume the usual Wald
integrability conditions".  The hypotheses used here are exactly:

* `hZbdd`  : the increments are bounded, `|Z_j| ≤ B` (the paper's "bounded … increments";
  boundedness is what makes `Z_j` integrable and the dominating function below finite);
* `hZmax`  : `Z_j ≤ z_max` (the paper's overshoot control);
* `hZmean` : every increment has the same mean `D`, and `hD : 0 < D`;
* `hindep` : `Z_j` is independent of the past σ-algebra `𝒢 j` (the "iid increments"
  hypothesis in exactly the form Wald's identity consumes);
* `hNstop` : `N` is a stopping time for `𝒢`;
* `hNint`  : `E[N] < ∞` — this is "the usual Wald integrability condition" that the paper
  assumes rather than derives;
* `hfirst` : `N` is a.s. the first time `m ≥ 1` at which `S_m ≥ a` (Equation 7).

Wald's identity itself (`wald_identity`) is *proved* here, not assumed.
-/

namespace Viridis.Run129.PaperFormalization

open MeasureTheory ProbabilityTheory Filter
open scoped ENNReal NNReal Topology

variable {Ω : Type*} {m0 : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]

/-- The running evidence `S_m = ∑_{j<m} Z_j` (the paper's `∑_{j=1}^m Z_j`). -/
noncomputable def evidenceSum (Z : ℕ → Ω → ℝ) (m : ℕ) (ω : Ω) : ℝ :=
  ∑ j ∈ Finset.range m, Z j ω

/-- The indicator of `{N > j}`; it is `𝒢 j`-measurable when `N` is a stopping time. -/
noncomputable def stopIndicator (N : Ω → ℕ) (j : ℕ) : Ω → ℝ :=
  Set.indicator {ω | j < N ω} 1

lemma stopIndicator_apply (N : Ω → ℕ) (j : ℕ) (ω : Ω) :
    stopIndicator N j ω = if j < N ω then (1 : ℝ) else 0 := by
  simp [stopIndicator, Set.indicator_apply]

lemma sum_stopIndicator (N : Ω → ℕ) (K : ℕ) (ω : Ω) :
    ∑ j ∈ Finset.range K, stopIndicator N j ω = ((min K (N ω) : ℕ) : ℝ) := by
  induction K with
  | zero => simp
  | succ K ih =>
    rw [Finset.sum_range_succ, ih, stopIndicator_apply]
    by_cases h : K < N ω
    · have hmin : min (K + 1) (N ω) = min K (N ω) + 1 := by omega
      rw [hmin, if_pos h]
      push_cast
      ring
    · have hmin : min (K + 1) (N ω) = min K (N ω) := by omega
      rw [hmin, if_neg h, add_zero]

lemma sum_stopIndicator_le (N : Ω → ℕ) (K : ℕ) (ω : Ω) :
    ∑ j ∈ Finset.range K, stopIndicator N j ω ≤ (N ω : ℝ) := by
  rw [sum_stopIndicator]
  exact_mod_cast Nat.min_le_right K (N ω)

lemma sum_stopIndicator_nonneg (N : Ω → ℕ) (K : ℕ) (ω : Ω) :
    0 ≤ ∑ j ∈ Finset.range K, stopIndicator N j ω := by
  rw [sum_stopIndicator]; positivity

lemma sum_stopIndicator_eq_of_le (N : Ω → ℕ) {K : ℕ} {ω : Ω} (hK : N ω ≤ K) :
    ∑ j ∈ Finset.range K, stopIndicator N j ω = (N ω : ℝ) := by
  rw [sum_stopIndicator, min_eq_right hK]

lemma sum_mul_stopIndicator_eq_of_le (Z : ℕ → Ω → ℝ) (N : Ω → ℕ) {K : ℕ} {ω : Ω}
    (hK : N ω ≤ K) :
    ∑ j ∈ Finset.range K, Z j ω * stopIndicator N j ω = evidenceSum Z (N ω) ω := by
  rw [evidenceSum]
  rw [← Finset.sum_subset (s₁ := Finset.range (N ω)) (s₂ := Finset.range K)
    (by intro x hx; simp only [Finset.mem_range] at *; omega)]
  · exact Finset.sum_congr rfl fun j hj => by
      rw [stopIndicator_apply, if_pos (Finset.mem_range.1 hj), mul_one]
  · intro j _ hj
    rw [stopIndicator_apply, if_neg (by simpa using hj), mul_zero]

/-- **Wald's identity** for a stopping time with finite mean and bounded increments that
are independent of the past: `E[∑_{j<N} Z_j] = E[Z] · E[N]`. -/
theorem wald_identity {𝒢 : Filtration ℕ m0} {Z : ℕ → Ω → ℝ} {N : Ω → ℕ} {B D : ℝ}
    (hB : 0 ≤ B)
    (hZmeas : ∀ j, Measurable (Z j))
    (hZbdd : ∀ j ω, |Z j ω| ≤ B)
    (hZmean : ∀ j, ∫ ω, Z j ω ∂μ = D)
    (hindep : ∀ j, Indep (MeasurableSpace.comap (Z j) inferInstance) (𝒢 j) μ)
    (hNstop : ∀ j, MeasurableSet[𝒢 j] {ω | N ω ≤ j})
    (hNint : Integrable (fun ω => (N ω : ℝ)) μ) :
    ∫ ω, evidenceSum Z (N ω) ω ∂μ = D * ∫ ω, (N ω : ℝ) ∂μ := by
  classical
  have hsetmeas : ∀ j, MeasurableSet[𝒢 j] {ω | j < N ω} := by
    intro j
    have hcompl : {ω | j < N ω} = {ω : Ω | N ω ≤ j}ᶜ := by
      ext ω; simp [Set.mem_setOf_eq, not_le]
    rw [hcompl]
    exact (hNstop j).compl
  have hgI𝒢 : ∀ j, Measurable[𝒢 j] (stopIndicator N j) := fun j =>
    (measurable_const : Measurable[𝒢 j] fun _ : Ω => (1 : ℝ)).indicator (hsetmeas j)
  have hgI : ∀ j, Measurable (stopIndicator N j) := fun j =>
    (hgI𝒢 j).mono (𝒢.le j) le_rfl
  have hsetmeas0 : ∀ j, MeasurableSet {ω | j < N ω} := fun j => 𝒢.le j _ (hsetmeas j)
  have hgIbdd : ∀ j ω, |stopIndicator N j ω| ≤ 1 := by
    intro j ω; rw [stopIndicator_apply]; split <;> norm_num
  have hZint : ∀ j, Integrable (Z j) μ := fun j =>
    (integrable_const B).mono' (hZmeas j).aestronglyMeasurable
      (Filter.Eventually.of_forall fun ω => by simpa [Real.norm_eq_abs] using hZbdd j ω)
  have hgIint : ∀ j, Integrable (stopIndicator N j) μ := fun j =>
    (integrable_const (1 : ℝ)).mono' (hgI j).aestronglyMeasurable
      (Filter.Eventually.of_forall fun ω => by simpa [Real.norm_eq_abs] using hgIbdd j ω)
  have hprodint : ∀ j, Integrable (fun ω => Z j ω * stopIndicator N j ω) μ := by
    intro j
    refine (integrable_const B).mono' (((hZmeas j).mul (hgI j)).aestronglyMeasurable)
      (Filter.Eventually.of_forall fun ω => ?_)
    have h1 := hZbdd j ω
    have h2 := hgIbdd j ω
    have : |Z j ω * stopIndicator N j ω| ≤ B * 1 := by
      rw [abs_mul]
      exact mul_le_mul h1 h2 (abs_nonneg _) hB
    simpa [Real.norm_eq_abs] using this
  have hgIintegral : ∀ j, ∫ ω, stopIndicator N j ω ∂μ = μ.real {ω | j < N ω} := fun j =>
    integral_indicator_one (hsetmeas0 j)
  -- the one-step independence computation
  have hkey : ∀ j, ∫ ω, Z j ω * stopIndicator N j ω ∂μ = D * μ.real {ω | j < N ω} := by
    intro j
    have hif : IndepFun (Z j) (stopIndicator N j) μ :=
      indep_of_indep_of_le_right (hindep j) ((hgI𝒢 j).comap_le)
    rw [hif.integral_fun_mul_eq_mul_integral (hZmeas j).aestronglyMeasurable
      (hgI j).aestronglyMeasurable]
    rw [show μ[Z j] = ∫ ω, Z j ω ∂μ from rfl, hZmean j,
      show μ[stopIndicator N j] = ∫ ω, stopIndicator N j ω ∂μ from rfl, hgIintegral j]
  -- partial sums
  set F : ℕ → Ω → ℝ := fun K ω => ∑ j ∈ Finset.range K, Z j ω * stopIndicator N j ω with hF
  set H : ℕ → Ω → ℝ := fun K ω => ∑ j ∈ Finset.range K, stopIndicator N j ω with hH
  have hFH : ∀ K, ∫ ω, F K ω ∂μ = D * ∫ ω, H K ω ∂μ := by
    intro K
    rw [hF, hH]
    rw [integral_finset_sum _ (fun j _ => hprodint j),
      integral_finset_sum _ (fun j _ => hgIint j), Finset.mul_sum]
    exact Finset.sum_congr rfl fun j _ => by rw [hkey j, hgIintegral j]
  have hHtendsto : Tendsto (fun K => ∫ ω, H K ω ∂μ) atTop (𝓝 (∫ ω, (N ω : ℝ) ∂μ)) := by
    refine tendsto_integral_of_dominated_convergence (fun ω => (N ω : ℝ))
      (fun K => (Finset.measurable_sum _ fun j _ => hgI j).aestronglyMeasurable)
      hNint (fun K => Filter.Eventually.of_forall fun ω => ?_)
      (Filter.Eventually.of_forall fun ω => ?_)
    · rw [Real.norm_eq_abs, abs_of_nonneg (sum_stopIndicator_nonneg N K ω)]
      exact sum_stopIndicator_le N K ω
    · exact tendsto_atTop_of_eventually_const (i₀ := N ω)
        fun K hK => sum_stopIndicator_eq_of_le N hK
  have hFtendsto : Tendsto (fun K => ∫ ω, F K ω ∂μ) atTop
      (𝓝 (∫ ω, evidenceSum Z (N ω) ω ∂μ)) := by
    refine tendsto_integral_of_dominated_convergence (fun ω => B * (N ω : ℝ))
      (fun K => (Finset.measurable_sum _ fun j _ => (hZmeas j).mul (hgI j)).aestronglyMeasurable)
      (hNint.const_mul B) (fun K => Filter.Eventually.of_forall fun ω => ?_)
      (Filter.Eventually.of_forall fun ω => ?_)
    · have h1 : |∑ j ∈ Finset.range K, Z j ω * stopIndicator N j ω|
          ≤ ∑ j ∈ Finset.range K, |Z j ω * stopIndicator N j ω| :=
        Finset.abs_sum_le_sum_abs _ _
      have h2 : ∑ j ∈ Finset.range K, |Z j ω * stopIndicator N j ω|
          ≤ ∑ j ∈ Finset.range K, B * stopIndicator N j ω := by
        refine Finset.sum_le_sum fun j _ => ?_
        rw [abs_mul, stopIndicator_apply]
        split <;> simp [hZbdd j ω]
      have h3 : ∑ j ∈ Finset.range K, B * stopIndicator N j ω ≤ B * (N ω : ℝ) := by
        rw [← Finset.mul_sum]
        exact mul_le_mul_of_nonneg_left (sum_stopIndicator_le N K ω) hB
      rw [Real.norm_eq_abs]
      exact le_trans h1 (le_trans h2 h3)
    · exact tendsto_atTop_of_eventually_const (i₀ := N ω)
        fun K hK => sum_mul_stopIndicator_eq_of_le Z N hK
  have hFtendsto' : Tendsto (fun K => ∫ ω, F K ω ∂μ) atTop (𝓝 (D * ∫ ω, (N ω : ℝ) ∂μ)) := by
    simp only [hFH]
    exact hHtendsto.const_mul D
  exact tendsto_nhds_unique hFtendsto hFtendsto'

/-- Measurability of the stopped evidence `ω ↦ S_{N ω}(ω)`. -/
lemma measurable_evidenceSum_stopped {Z : ℕ → Ω → ℝ} {N : Ω → ℕ}
    (hZmeas : ∀ j, Measurable (Z j)) (hNmeas : Measurable N) :
    Measurable (fun ω => evidenceSum Z (N ω) ω) := by
  have hstep : ∀ m, Measurable (evidenceSum Z m) := fun m =>
    Finset.measurable_sum _ fun j _ => hZmeas j
  have hpair : Measurable fun p : ℕ × Ω => evidenceSum Z p.1 p.2 :=
    measurable_from_prod_countable_right fun m => hstep m
  exact hpair.comp (hNmeas.prodMk measurable_id)

/-- A `ℕ`-valued stopping time is measurable. -/
lemma measurable_of_stopping {𝒢 : Filtration ℕ m0} {N : Ω → ℕ}
    (hNstop : ∀ j, MeasurableSet[𝒢 j] {ω | N ω ≤ j}) : Measurable N := by
  have h : ∀ j, MeasurableSet {ω : Ω | N ω ≤ j} := fun j => 𝒢.le j _ (hNstop j)
  refine measurable_to_countable' fun m => ?_
  match m with
  | 0 =>
    have hset : N ⁻¹' {0} = {ω : Ω | N ω ≤ 0} := by ext ω; simp
    rw [hset]; exact h 0
  | (m + 1) =>
    have hset : N ⁻¹' {m + 1} = {ω : Ω | N ω ≤ m + 1} \ {ω : Ω | N ω ≤ m} := by
      ext ω; simp only [Set.mem_preimage, Set.mem_singleton_iff, Set.mem_diff,
        Set.mem_setOf_eq]; omega
    rw [hset]; exact (h (m + 1)).diff (h m)

omit [IsProbabilityMeasure μ] in
/-- Integrability of the stopped evidence `ω ↦ S_{N ω}(ω)` under bounded increments and
`E[N] < ∞`. -/
lemma integrable_evidenceSum_stopped {Z : ℕ → Ω → ℝ} {N : Ω → ℕ} {B : ℝ}
    (hZmeas : ∀ j, Measurable (Z j)) (hZbdd : ∀ j ω, |Z j ω| ≤ B)
    (hNmeas : Measurable N) (hNint : Integrable (fun ω => (N ω : ℝ)) μ) :
    Integrable (fun ω => evidenceSum Z (N ω) ω) μ := by
  refine (hNint.const_mul B).mono'
    (measurable_evidenceSum_stopped hZmeas hNmeas).aestronglyMeasurable
    (Filter.Eventually.of_forall fun ω => ?_)
  rw [Real.norm_eq_abs, evidenceSum]
  calc |∑ j ∈ Finset.range (N ω), Z j ω|
      ≤ ∑ j ∈ Finset.range (N ω), |Z j ω| := Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ _j ∈ Finset.range (N ω), B := Finset.sum_le_sum fun j _ => hZbdd j ω
    _ = B * (N ω : ℝ) := by simp [mul_comm]

/-- Equation (7)–(8), pathwise: at the first crossing of the boundary `a > 0` the evidence
lies in `[a, a + z_max)`. -/
lemma evidenceSum_crossing {Z : ℕ → Ω → ℝ} {N : Ω → ℕ} {a zmax : ℝ} (ha : 0 < a)
    (hZmax : ∀ j ω, Z j ω ≤ zmax) {ω : Ω}
    (h : IsLeast {m : ℕ | 1 ≤ m ∧ a ≤ evidenceSum Z m ω} (N ω)) :
    a ≤ evidenceSum Z (N ω) ω ∧ evidenceSum Z (N ω) ω < a + zmax := by
  obtain ⟨⟨h1, h2⟩, hmin⟩ := h
  refine ⟨h2, ?_⟩
  obtain ⟨m, hm⟩ : ∃ m, N ω = m + 1 := ⟨N ω - 1, by omega⟩
  have hprev : evidenceSum Z m ω < a := by
    match m, hm with
    | 0, _ => simpa [evidenceSum] using ha
    | (k + 1), hm =>
      by_contra hcon
      push_neg at hcon
      have hle := hmin (show k + 1 ∈ {m : ℕ | 1 ≤ m ∧ a ≤ evidenceSum Z m ω} from
        ⟨by omega, hcon⟩)
      omega
  have hstep : evidenceSum Z (m + 1) ω = evidenceSum Z m ω + Z m ω :=
    Finset.sum_range_succ _ _
  rw [hm, hstep]
  have := hZmax m ω
  linarith

/-- **C4** (`bounded_overshoot_expected_delay`, Equation 8).  For bounded, correctly
specified iid post-change increments with positive mean `D`, under the Wald integrability
condition `E[N_a] < ∞`, the first-crossing time of the boundary `a > 0` satisfies the
bounded-overshoot delay corridor `a/D ≤ E₁[N_a] < (a + z_max)/D`. -/
theorem bounded_overshoot_expected_delay {𝒢 : Filtration ℕ m0} {Z : ℕ → Ω → ℝ} {N : Ω → ℕ}
    {B D zmax a : ℝ}
    (hB : 0 ≤ B)
    (hZmeas : ∀ j, Measurable (Z j))
    (hZbdd : ∀ j ω, |Z j ω| ≤ B)
    (hZmax : ∀ j ω, Z j ω ≤ zmax)
    (hZmean : ∀ j, ∫ ω, Z j ω ∂μ = D)
    (hD : 0 < D)
    (ha : 0 < a)
    (hindep : ∀ j, Indep (MeasurableSpace.comap (Z j) inferInstance) (𝒢 j) μ)
    (hNstop : ∀ j, MeasurableSet[𝒢 j] {ω | N ω ≤ j})
    (hNint : Integrable (fun ω => (N ω : ℝ)) μ)
    (hfirst : ∀ᵐ ω ∂μ, IsLeast {m : ℕ | 1 ≤ m ∧ a ≤ evidenceSum Z m ω} (N ω)) :
    a / D ≤ ∫ ω, (N ω : ℝ) ∂μ ∧ ∫ ω, (N ω : ℝ) ∂μ < (a + zmax) / D := by
  have hNmeas : Measurable N := measurable_of_stopping (𝒢 := 𝒢) hNstop
  have hSint : Integrable (fun ω => evidenceSum Z (N ω) ω) μ :=
    integrable_evidenceSum_stopped hZmeas hZbdd hNmeas hNint
  have hwald : ∫ ω, evidenceSum Z (N ω) ω ∂μ = D * ∫ ω, (N ω : ℝ) ∂μ :=
    wald_identity hB hZmeas hZbdd hZmean hindep hNstop hNint
  have hlow : a ≤ ∫ ω, evidenceSum Z (N ω) ω ∂μ := by
    have hae : ∀ᵐ ω ∂μ, a ≤ evidenceSum Z (N ω) ω := by
      filter_upwards [hfirst] with ω h using (evidenceSum_crossing ha hZmax h).1
    calc a = ∫ _ω : Ω, a ∂μ := by simp
      _ ≤ _ := integral_mono_ae (integrable_const a) hSint hae
  have hhigh : ∫ ω, evidenceSum Z (N ω) ω ∂μ < a + zmax := by
    set f : Ω → ℝ := fun ω => a + zmax - evidenceSum Z (N ω) ω with hf
    have hlt : ∀ᵐ ω ∂μ, 0 < f ω := by
      filter_upwards [hfirst] with ω h
      have := (evidenceSum_crossing ha hZmax h).2
      simp only [hf]
      linarith
    have hnn : 0 ≤ᵐ[μ] f := by filter_upwards [hlt] with ω h using h.le
    have hint2 : Integrable f μ := (integrable_const _).sub hSint
    have hsupp : μ (Function.support f) = 1 := by
      have hz : μ (Function.support f)ᶜ = 0 := by
        rw [Set.compl_def, ← ae_iff]
        filter_upwards [hlt] with ω h
        exact ne_of_gt h
      rw [← measure_univ (μ := μ)]
      exact measure_congr (ae_eq_univ.2 hz)
    have hpos : 0 < ∫ ω, f ω ∂μ := by
      rw [integral_pos_iff_support_of_nonneg_ae hnn hint2, hsupp]
      norm_num
    rw [hf, integral_sub (integrable_const _) hSint] at hpos
    simp only [integral_const, probReal_univ, smul_eq_mul, one_mul] at hpos
    linarith
  rw [hwald] at hlow hhigh
  refine ⟨?_, ?_⟩
  · rw [div_le_iff₀ hD, mul_comm]
    linarith
  · rw [lt_div_iff₀ hD, mul_comm]
    linarith

/-- **Model-dependent corollary** (Equation 9 of the paper; *not* one of the frozen formal
targets).  Under the paper's *separately declared* reversible binary-memory reset model —
formalized here as the explicit hypothesis `hW : E[W_erase] = q_L · E[N_a]` — the delay
corridor of C4 induces the Landauer-normalized erasure-work corridor
`q_L·a/D ≤ E[W_erase] < q_L·(a + z_max)/D`.

This is an accounting corollary of the declared model, not a universal lower bound on
monitor energy; the paper's exclusions (sensing, transmission, computation, leakage,
finite-time control, …) are not addressed. -/
theorem landauer_erasure_corridor {𝒢 : Filtration ℕ m0} {Z : ℕ → Ω → ℝ} {N : Ω → ℕ}
    {B D zmax a qL : ℝ} {W : Ω → ℝ}
    (hB : 0 ≤ B)
    (hZmeas : ∀ j, Measurable (Z j))
    (hZbdd : ∀ j ω, |Z j ω| ≤ B)
    (hZmax : ∀ j ω, Z j ω ≤ zmax)
    (hZmean : ∀ j, ∫ ω, Z j ω ∂μ = D)
    (hD : 0 < D)
    (ha : 0 < a)
    (hindep : ∀ j, Indep (MeasurableSpace.comap (Z j) inferInstance) (𝒢 j) μ)
    (hNstop : ∀ j, MeasurableSet[𝒢 j] {ω | N ω ≤ j})
    (hNint : Integrable (fun ω => (N ω : ℝ)) μ)
    (hfirst : ∀ᵐ ω ∂μ, IsLeast {m : ℕ | 1 ≤ m ∧ a ≤ evidenceSum Z m ω} (N ω))
    (hqL : 0 < qL)
    (hW : ∫ ω, W ω ∂μ = qL * ∫ ω, (N ω : ℝ) ∂μ) :
    qL * (a / D) ≤ ∫ ω, W ω ∂μ ∧ ∫ ω, W ω ∂μ < qL * ((a + zmax) / D) := by
  obtain ⟨hlow, hhigh⟩ := bounded_overshoot_expected_delay hB hZmeas hZbdd hZmax hZmean hD ha
    hindep hNstop hNint hfirst
  rw [hW]
  exact ⟨mul_le_mul_of_nonneg_left hlow hqL.le, mul_lt_mul_of_pos_left hhigh hqL⟩

end Viridis.Run129.PaperFormalization
