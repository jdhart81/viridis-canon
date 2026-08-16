import PaperFormalization.Mixture

/-!
# C1 and C2: the null martingale property and the anytime (Ville) certificate

This file formalizes the two certificate claims of `SEALED_paper.tex`, §2:

* **C1** `anytime_change_mixture_martingale`: under the declared null, `(M_n)` is a
  nonnegative martingale with `M_0 = 1` and `E₀[M_n] = 1` for all `n`.
* **C2** `anytime_change_ville_certificate` (Equation 4): `P₀(ever alarming) ≤ α`
  when the alarm threshold is `1/α`.

## Explicit assumptions and scope

The paper's null is: `X₁, X₂, …` iid `P₀`, `P₁ ≪ P₀`, and `Λ_n = dP₁/dP₀(X_n)`, from
which it records the only distributional consequence it ever uses, namely

  `E₀[Λ_n ∣ ℱ_{n-1}] = 1`.

We take exactly that consequence (`hcondΛ` below) as the hypothesis, together with
nonnegativity, adaptedness and integrability.  This is a faithful abstraction of the
paper's null: no dependence structure beyond the displayed conditional-mean-one identity
is used anywhere in §2.  `PaperFormalization.Witnesses` exhibits a genuinely iid
Bernoulli likelihood-ratio model satisfying all of these hypotheses, so nothing here is
vacuous.
-/

namespace Viridis.Run129.PaperFormalization

open MeasureTheory Filter
open scoped ENNReal NNReal Topology

variable {Ω : Type*} {m0 : MeasurableSpace Ω} {μ : Measure Ω} [IsProbabilityMeasure μ]
  {ℱ : Filtration ℕ m0} {Λ : ℕ → Ω → ℝ}

section Martingale

variable
  (hΛmeas : ∀ n, StronglyMeasurable[ℱ n] (Λ n))
  (hΛnonneg : ∀ n ω, 0 ≤ Λ n ω)
  (hΛint : ∀ n, Integrable (Λ n) μ)
  (hAint : ∀ n, Integrable (mixAcc Λ n) μ)
  (hcondΛ : ∀ n, μ[Λ (n + 1) | ℱ n] =ᵐ[μ] fun _ => (1 : ℝ))

include hΛmeas hΛint hAint hcondΛ

/-- The key one-step computation, Equation (3):
`E₀[M_n ∣ ℱ_{n-1}] = A_{n-1} + π_n + t_n = M_{n-1}`. -/
lemma condExp_mixture_succ (n : ℕ) :
    μ[mixture Λ (n + 1) | ℱ n] =ᵐ[μ] mixture Λ n := by
  have hf : StronglyMeasurable[ℱ n] (mixAcc Λ n + fun _ => changePrior (n + 1)) :=
    (stronglyMeasurable_mixAcc ℱ hΛmeas n).add stronglyMeasurable_const
  have hprod :
      (mixAcc Λ n + fun _ => changePrior (n + 1)) * Λ (n + 1) = mixAcc Λ (n + 1) := by
    funext ω
    simp [mixAcc_succ, mul_comm]
  have hfg : Integrable ((mixAcc Λ n + fun _ => changePrior (n + 1)) * Λ (n + 1)) μ := by
    rw [hprod]; exact hAint (n + 1)
  have hpull := condExp_mul_of_stronglyMeasurable_left (m := ℱ n) hf hfg (hΛint (n + 1))
  rw [hprod] at hpull
  -- `E[A_{n+1} | ℱ_n] = A_n + π_{n+1}`
  have hA : μ[mixAcc Λ (n + 1) | ℱ n] =ᵐ[μ] mixAcc Λ n + fun _ => changePrior (n + 1) := by
    filter_upwards [hpull, hcondΛ n] with ω h1 h2
    simp [h1, h2]
  -- add the (deterministic) tail term
  have hsplit : mixture Λ (n + 1) = mixAcc Λ (n + 1) + fun _ => priorTail (n + 1) := rfl
  have hadd : μ[mixture Λ (n + 1) | ℱ n]
      =ᵐ[μ] μ[mixAcc Λ (n + 1) | ℱ n] + μ[(fun _ => priorTail (n + 1) : Ω → ℝ) | ℱ n] := by
    rw [hsplit]
    exact condExp_add (hAint (n + 1)) (integrable_const _) _
  have hconst : μ[(fun _ => priorTail (n + 1) : Ω → ℝ) | ℱ n]
      =ᵐ[μ] fun _ => priorTail (n + 1) := by
    rw [condExp_const (μ := μ) (ℱ.le n)]
  filter_upwards [hadd, hA, hconst] with ω h1 h2 h3
  have := changePrior_add_priorTail n
  simp only [Pi.add_apply] at h1 h2 ⊢
  rw [h1, h2, h3]
  simp only [mixture]
  linarith

include hΛnonneg in
/-- **C1** (`anytime_change_mixture_martingale`).  Under the declared null the
change-time mixture `M_n = A_n + t_n` of Equation (2) is a nonnegative martingale with
`M_0 = 1`, hence a mean-one test martingale: `E₀[M_n] = 1` for every `n`. -/
theorem anytime_change_mixture_martingale :
    Martingale (mixture Λ) ℱ μ ∧ (∀ n ω, 0 ≤ mixture Λ n ω) ∧
      mixture Λ 0 = (fun _ => (1 : ℝ)) ∧ (∀ n, ∫ ω, mixture Λ n ω ∂μ = 1) := by
  have hmg : Martingale (mixture Λ) ℱ μ := by
    refine martingale_nat (stronglyAdapted_mixture ℱ hΛmeas)
      (fun n => (hAint n).add (integrable_const _)) (fun n => ?_)
    exact (condExp_mixture_succ hΛmeas hΛint hAint hcondΛ n).symm
  refine ⟨hmg, mixture_nonneg hΛnonneg, mixture_zero Λ, fun n => ?_⟩
  have h0 : mixture Λ 0 =ᵐ[μ] μ[mixture Λ n | ℱ 0] := (hmg.2 0 n (Nat.zero_le n)).symm
  have hint : ∫ ω, mixture Λ 0 ω ∂μ = ∫ ω, (μ[mixture Λ n | ℱ 0]) ω ∂μ :=
    integral_congr_ae h0
  rw [integral_condExp (ℱ.le 0)] at hint
  rw [← hint]
  simp

end Martingale

section Ville

/-- **Ville's inequality** for a nonnegative martingale indexed by `ℕ`: the probability of
*ever* reaching the level `c > 0` is at most `E[M₀]/c`.

This is proved from Doob's finite-horizon maximal inequality by monotone convergence of
the crossing events. -/
theorem ville_inequality {M : ℕ → Ω → ℝ} (hM : Martingale M ℱ μ) (hnonneg : ∀ n ω, 0 ≤ M n ω)
    {c : ℝ} (hc : 0 < c) :
    μ {ω | ∃ n, c ≤ M n ω} ≤ ENNReal.ofReal ((∫ ω, M 0 ω ∂μ) / c) := by
  classical
  set I : ℝ := ∫ ω, M 0 ω ∂μ with hI
  have hI0 : 0 ≤ I := integral_nonneg (fun ω => hnonneg 0 ω)
  set ε : ℝ≥0 := c.toNNReal with hε
  have hεc : (ε : ℝ) = c := Real.coe_toNNReal c hc.le
  set E : ℕ → Set Ω := fun N =>
    {ω | (ε : ℝ) ≤ (Finset.range (N + 1)).sup' Finset.nonempty_range_add_one fun k => M k ω}
    with hE
  -- each `E N` has measure at most `I / c`
  have hstep : ∀ N, μ (E N) ≤ ENNReal.ofReal (I / c) := by
    intro N
    have hmax := maximal_ineq hM.submartingale (fun n ω => hnonneg n ω) (ε := ε) N
    have hsub : ∫ ω in E N, M N ω ∂μ ≤ I := by
      have h1 : ∫ ω in E N, M N ω ∂μ ≤ ∫ ω, M N ω ∂μ :=
        setIntegral_le_integral (hM.integrable N) (Filter.Eventually.of_forall (hnonneg N))
      have h2 : ∫ ω, M N ω ∂μ = I := by
        have h0 : M 0 =ᵐ[μ] μ[M N | ℱ 0] := (hM.2 0 N (Nat.zero_le N)).symm
        have := integral_congr_ae h0
        rw [integral_condExp (ℱ.le 0)] at this
        rw [hI, this]
      linarith
    have hmax' : (ε : ℝ≥0∞) * μ (E N) ≤ ENNReal.ofReal I := by
      refine le_trans ?_ (ENNReal.ofReal_le_ofReal hsub)
      simpa [hE, smul_eq_mul] using hmax
    have hεpos : (ε : ℝ≥0∞) ≠ 0 := by
      simp only [ne_eq, ENNReal.coe_eq_zero, hε]
      exact ne_of_gt (Real.toNNReal_pos.mpr hc)
    have : μ (E N) ≤ ENNReal.ofReal I / (ε : ℝ≥0∞) :=
      ENNReal.le_div_iff_mul_le (Or.inl hεpos) (Or.inl (by simp)) |>.2 (by rwa [mul_comm] at hmax')
    refine this.trans (le_of_eq ?_)
    rw [ENNReal.ofReal_div_of_pos hc, ← hεc, ENNReal.ofReal_coe_nnreal]
  -- the alarm event is the increasing union of the `E N`
  have hunion : {ω | ∃ n, c ≤ M n ω} = ⋃ N, E N := by
    ext ω
    constructor
    · rintro ⟨n, hn⟩
      refine Set.mem_iUnion.2 ⟨n, ?_⟩
      simp only [hE, Set.mem_setOf_eq, hεc]
      exact hn.trans (Finset.le_sup' (f := fun k => M k ω) (by simp))
    · rintro h
      obtain ⟨N, hN⟩ := Set.mem_iUnion.1 h
      simp only [hE, Set.mem_setOf_eq, hεc] at hN
      obtain ⟨j, _, hj⟩ : ∃ j ∈ Finset.range (N + 1), c ≤ M j ω := by
        by_contra hcon
        push_neg at hcon
        have : ((Finset.range (N + 1)).sup' Finset.nonempty_range_add_one fun k => M k ω) < c :=
          Finset.sup'_lt_iff _ |>.2 (fun i hi => hcon i hi)
        linarith
      exact ⟨j, hj⟩
  have hmono : Monotone E := by
    intro a b hab ω hω
    simp only [hE, Set.mem_setOf_eq] at hω ⊢
    refine hω.trans (Finset.sup'_mono (f := fun k => M k ω)
      (s₁ := Finset.range (a + 1)) (s₂ := Finset.range (b + 1))
      (by intro x hx; simp only [Finset.mem_range] at hx ⊢; omega)
      Finset.nonempty_range_add_one)
  rw [hunion]
  rw [hmono.measure_iUnion]
  exact iSup_le hstep

/-- **Ville's inequality, supremum form.**  This is the literal form of Equation (4):
`P(sup_n M_n ≥ c) ≤ E[M₀]/c`.  The supremum is taken in `ℝ≥0∞` so that it is always
defined; it is a strengthening of `ville_inequality`, whose event is `∃ n, c ≤ M n`. -/
theorem ville_inequality_sup {M : ℕ → Ω → ℝ} (hM : Martingale M ℱ μ)
    (hnonneg : ∀ n ω, 0 ≤ M n ω) {c : ℝ} (hc : 0 < c) :
    μ {ω | ENNReal.ofReal c ≤ ⨆ n, ENNReal.ofReal (M n ω)}
      ≤ ENNReal.ofReal ((∫ ω, M 0 ω ∂μ) / c) := by
  set I : ℝ := ∫ ω, M 0 ω ∂μ with hI
  set t : ℕ → ℝ := fun k => ((k : ℝ) + 1) / ((k : ℝ) + 2) with ht
  have htpos : ∀ k, 0 < t k := by
    intro k
    have h1 : (0 : ℝ) < (k : ℝ) + 1 := by positivity
    have h2 : (0 : ℝ) < (k : ℝ) + 2 := by positivity
    exact div_pos h1 h2
  have htlt : ∀ k, t k < 1 := by
    intro k
    have h2 : (0 : ℝ) < (k : ℝ) + 2 := by positivity
    rw [ht, div_lt_one h2]
    linarith
  -- for each `k`, compare with the strictly smaller level `t k * c`
  have hstep : ∀ k, μ {ω | ENNReal.ofReal c ≤ ⨆ n, ENNReal.ofReal (M n ω)}
      ≤ ENNReal.ofReal (I / (t k * c)) := by
    intro k
    have hck : 0 < t k * c := mul_pos (htpos k) hc
    have hsub : {ω | ENNReal.ofReal c ≤ ⨆ n, ENNReal.ofReal (M n ω)}
        ⊆ {ω | ∃ n, t k * c ≤ M n ω} := by
      intro ω hω
      by_contra hcon
      simp only [Set.mem_setOf_eq, not_exists, not_le] at hcon
      have hle : (⨆ n, ENNReal.ofReal (M n ω)) ≤ ENNReal.ofReal (t k * c) :=
        iSup_le fun n => ENNReal.ofReal_le_ofReal (hcon n).le
      have := le_trans hω hle
      rw [ENNReal.ofReal_le_ofReal_iff hck.le] at this
      nlinarith [htlt k, hc]
    refine le_trans (measure_mono hsub) ?_
    exact ville_inequality hM hnonneg hck
  -- let `t k → 1`
  have htend : Tendsto (fun k : ℕ => ENNReal.ofReal (I / (t k * c))) atTop
      (𝓝 (ENNReal.ofReal (I / c))) := by
    have h0 : Tendsto (fun k : ℕ => 1 / ((k : ℝ) + 2)) atTop (𝓝 0) := by
      have h := tendsto_one_div_add_atTop_nhds_zero_nat (𝕜 := ℝ)
      have := h.comp (Filter.tendsto_add_atTop_nat 1)
      refine this.congr fun k => ?_
      simp only [Function.comp_apply]
      congr 1
      push_cast
      ring
    have h1 : Tendsto t atTop (𝓝 1) := by
      have hev : ∀ k : ℕ, t k = 1 - 1 / ((k : ℝ) + 2) := by
        intro k
        have h2 : ((k : ℝ) + 2) ≠ 0 := by positivity
        simp only [ht]
        field_simp
        ring
      refine Tendsto.congr (fun k => (hev k).symm) ?_
      simpa using (tendsto_const_nhds (x := (1 : ℝ)) (f := (atTop : Filter ℕ))).sub h0
    have h2 : Tendsto (fun k : ℕ => I / (t k * c)) atTop (𝓝 (I / c)) := by
      have hmul : Tendsto (fun k : ℕ => t k * c) atTop (𝓝 c) := by
        simpa using h1.mul (tendsto_const_nhds (x := c) (f := (atTop : Filter ℕ)))
      exact (tendsto_const_nhds (x := I) (f := (atTop : Filter ℕ))).div hmul (ne_of_gt hc)
    exact (ENNReal.continuous_ofReal.tendsto _).comp h2
  exact ge_of_tendsto htend (Filter.Eventually.of_forall hstep)

variable
  (hΛmeas : ∀ n, StronglyMeasurable[ℱ n] (Λ n))
  (hΛnonneg : ∀ n ω, 0 ≤ Λ n ω)
  (hΛint : ∀ n, Integrable (Λ n) μ)
  (hAint : ∀ n, Integrable (mixAcc Λ n) μ)
  (hcondΛ : ∀ n, μ[Λ (n + 1) | ℱ n] =ᵐ[μ] fun _ => (1 : ℝ))

include hΛmeas hΛnonneg hΛint hAint hcondΛ

/-- **C2** (`anytime_change_ville_certificate`, Equation 4).  Under the declared null, the
probability that the monitor *ever* alarms at the single threshold `1/α` is at most `α`. -/
theorem anytime_change_ville_certificate {α : ℝ} (hα : 0 < α) :
    μ {ω | ∃ n, 1 / α ≤ mixture Λ n ω} ≤ ENNReal.ofReal α := by
  obtain ⟨hmg, hnn, h0, hmean⟩ :=
    anytime_change_mixture_martingale hΛmeas hΛnonneg hΛint hAint hcondΛ
  have hc : (0 : ℝ) < 1 / α := by positivity
  have := ville_inequality hmg hnn hc
  rw [hmean 0] at this
  simpa [one_div_one_div] using this

/-- **C2, supremum form** (the literal Equation 4): `P₀(sup_{n≥0} M_n ≥ 1/α) ≤ α`.
This strengthens `anytime_change_ville_certificate`. -/
theorem anytime_change_ville_certificate_sup {α : ℝ} (hα : 0 < α) :
    μ {ω | ENNReal.ofReal (1 / α) ≤ ⨆ n, ENNReal.ofReal (mixture Λ n ω)}
      ≤ ENNReal.ofReal α := by
  obtain ⟨hmg, hnn, h0, hmean⟩ :=
    anytime_change_mixture_martingale hΛmeas hΛnonneg hΛint hAint hcondΛ
  have hc : (0 : ℝ) < 1 / α := by positivity
  have h := ville_inequality_sup hmg hnn hc
  rw [hmean 0] at h
  simpa [one_div_one_div] using h

end Ville

end Viridis.Run129.PaperFormalization
