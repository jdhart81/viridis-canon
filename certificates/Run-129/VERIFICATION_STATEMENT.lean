import Mathlib

/- Engine-3 immutable source unit: Prior.lean -/

/-!
# The heavy-tailed change-time prior of Run-129

This file formalizes Equation (1) of the sealed paper `SEALED_paper.tex`:

  `π_k = 1 / (k (k+1))`,  `t_n = ∑_{k > n} π_k = 1 / (n+1)`.

`changePrior` is `π` and `priorTail` is `t`.  Both are defined for every natural index;
the paper only uses `k ≥ 1` for `π` (and `changePrior 0 = 0` in Lean, which is harmless
since the index `0` never occurs in the recursion).

The two facts that the rest of the development needs are

* `changePrior_add_priorTail`: `π_{n+1} + t_{n+1} = t_n` (the identity `π_n + t_n = t_{n-1}`
  used in the martingale computation), and
* `hasSum_changePrior_tail`: `t_n` really is the tail mass `∑_{k > n} π_k` of the prior,
  so in particular (`hasSum_changePrior`) `π` is a probability distribution on `{1, 2, …}`.
-/

namespace Viridis.Run129.PaperFormalization

open scoped Topology
open Filter

/-- The heavy-tailed change-time prior `π_k = 1 / (k (k+1))` of Equation (1). -/
noncomputable def changePrior (k : ℕ) : ℝ := 1 / ((k : ℝ) * (k + 1))

/-- The prior tail mass `t_n = ∑_{k>n} π_k = 1 / (n+1)` of Equation (1). -/
noncomputable def priorTail (n : ℕ) : ℝ := 1 / ((n : ℝ) + 1)

@[simp] lemma priorTail_zero : priorTail 0 = 1 := by norm_num [priorTail]

lemma priorTail_pos (n : ℕ) : 0 < priorTail n := by
  have : (0 : ℝ) < (n : ℝ) + 1 := by positivity
  simpa [priorTail] using this

lemma changePrior_nonneg (k : ℕ) : 0 ≤ changePrior k := by
  unfold changePrior
  positivity

lemma changePrior_pos {k : ℕ} (hk : 1 ≤ k) : 0 < changePrior k := by
  have hk' : (1 : ℝ) ≤ (k : ℝ) := by exact_mod_cast hk
  have h : (0 : ℝ) < (k : ℝ) * ((k : ℝ) + 1) := by nlinarith
  exact div_pos one_pos h

/-- `π_k = 1/k - 1/(k+1)` for `k ≥ 1`; stated in the shifted form used for telescoping. -/
lemma changePrior_succ_eq_sub (k : ℕ) :
    changePrior (k + 1) = 1 / ((k : ℝ) + 1) - 1 / ((k : ℝ) + 2) := by
  have h1 : ((k : ℝ) + 1) ≠ 0 := by positivity
  have h2 : ((k : ℝ) + 2) ≠ 0 := by positivity
  unfold changePrior
  push_cast
  field_simp
  ring

/-- Equation (1): `π_{n+1} + t_{n+1} = t_n`, i.e. `π_n + t_n = t_{n-1}`. -/
lemma changePrior_add_priorTail (n : ℕ) :
    changePrior (n + 1) + priorTail (n + 1) = priorTail n := by
  have h := changePrior_succ_eq_sub n
  have h2 : priorTail (n + 1) = 1 / ((n : ℝ) + 2) := by
    simp [priorTail]; ring_nf
  rw [h, h2]
  simp [priorTail]

/-- Equation (1): the tail mass identity `∑_{k>n} π_k = t_n`. -/
theorem hasSum_changePrior_tail (n : ℕ) :
    HasSum (fun j : ℕ => changePrior (n + 1 + j)) (priorTail n) := by
  set f : ℕ → ℝ := fun j => 1 / ((n : ℝ) + 1 + j) with hf
  have hterm : ∀ j : ℕ, changePrior (n + 1 + j) = f j - f (j + 1) := by
    intro j
    have := changePrior_succ_eq_sub (n + j)
    have hcast : ((n + 1 + j : ℕ) : ℝ) = ((n + j : ℕ) : ℝ) + 1 := by push_cast; ring
    have h1 : changePrior (n + 1 + j) = changePrior ((n + j) + 1) := by
      congr 1; omega
    rw [h1, this]
    simp only [hf]
    push_cast
    ring_nf
  have hpartial : ∀ m : ℕ, ∑ j ∈ Finset.range m, changePrior (n + 1 + j)
      = priorTail n - f m := by
    intro m
    simp only [hterm]
    rw [Finset.sum_range_sub' f m]
    simp [hf, priorTail]
  have hsummable : Summable (fun j : ℕ => changePrior (n + 1 + j)) := by
    refine summable_of_sum_range_le (c := priorTail n) (fun j => changePrior_nonneg _) (fun m => ?_)
    rw [hpartial m]
    have : 0 ≤ f m := by
      simp only [hf]
      positivity
    linarith
  rw [hsummable.hasSum_iff_tendsto_nat]
  have hlim : Tendsto f atTop (𝓝 0) := by
    simp only [hf]
    have : Tendsto (fun m : ℕ => ((n : ℝ) + 1 + m)) atTop atTop := by
      apply Filter.tendsto_atTop_add_const_left
      exact tendsto_natCast_atTop_atTop
    exact this.inv_tendsto_atTop.congr (fun m => by simp [one_div])
  have := (tendsto_const_nhds (x := priorTail n) (f := atTop (α := ℕ))).sub hlim
  simpa [hpartial, sub_zero] using this

/-- The prior `π` is a probability distribution on the change times `{1, 2, …}`. -/
theorem hasSum_changePrior : HasSum (fun j : ℕ => changePrior (j + 1)) 1 := by
  have h := hasSum_changePrior_tail 0
  simpa [add_comm] using h

end Viridis.Run129.PaperFormalization

/- Engine-3 immutable source unit: Mixture.lean -/

/-!
# The change-time mixture `M_n` of Run-129

This file formalizes the recursion of Equation (2) in `SEALED_paper.tex`:

  `A_0 = 0`,  `A_n = Λ_n (A_{n-1} + π_n)`,  `M_n = A_n + t_n`.

Everything in this file is *pathwise* (no measure theory): the accumulator `mixAcc`,
the mixture `mixture`, nonnegativity, `M_0 = 1`, adaptedness, and the component
dominance bound `M_n ≥ π_ν ∏_{i=ν}^{n} Λ_i` of Equation (5).

`Λ` is the sequence of likelihood ratios `Λ_n = dP₁/dP₀(X_n)`; it is an arbitrary
sequence of functions here, and all distributional assumptions are made where needed.
-/

namespace Viridis.Run129.PaperFormalization

open MeasureTheory

variable {Ω : Type*}

/-- The accumulator `A_n` of Equation (2): `A_0 = 0` and `A_n = Λ_n (A_{n-1} + π_n)`. -/
noncomputable def mixAcc (Λ : ℕ → Ω → ℝ) : ℕ → Ω → ℝ
  | 0 => fun _ => 0
  | n + 1 => fun ω => Λ (n + 1) ω * (mixAcc Λ n ω + changePrior (n + 1))

@[simp] lemma mixAcc_zero (Λ : ℕ → Ω → ℝ) : mixAcc Λ 0 = fun _ => 0 := rfl

lemma mixAcc_succ (Λ : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    mixAcc Λ (n + 1) ω = Λ (n + 1) ω * (mixAcc Λ n ω + changePrior (n + 1)) := rfl

/-- The change-time mixture `M_n = A_n + t_n` of Equation (2). -/
noncomputable def mixture (Λ : ℕ → Ω → ℝ) (n : ℕ) : Ω → ℝ :=
  fun ω => mixAcc Λ n ω + priorTail n

lemma mixture_apply (Λ : ℕ → Ω → ℝ) (n : ℕ) (ω : Ω) :
    mixture Λ n ω = mixAcc Λ n ω + priorTail n := rfl

/-- `M_0 = 1`. -/
@[simp] lemma mixture_zero (Λ : ℕ → Ω → ℝ) : mixture Λ 0 = fun _ => (1 : ℝ) := by
  funext ω; simp [mixture]

section Nonneg

variable {Λ : ℕ → Ω → ℝ} (hΛ : ∀ n ω, 0 ≤ Λ n ω)
include hΛ

lemma mixAcc_nonneg : ∀ (n : ℕ) (ω : Ω), 0 ≤ mixAcc Λ n ω := by
  intro n
  induction n with
  | zero => intro ω; simp
  | succ n ih =>
    intro ω
    rw [mixAcc_succ]
    exact mul_nonneg (hΛ _ _) (by have := ih ω; have := changePrior_nonneg (n + 1); linarith)

lemma mixture_nonneg (n : ℕ) (ω : Ω) : 0 ≤ mixture Λ n ω := by
  have h1 := mixAcc_nonneg hΛ n ω
  have h2 := (priorTail_pos n).le
  simpa [mixture] using add_nonneg h1 h2

lemma priorTail_le_mixture (n : ℕ) (ω : Ω) : priorTail n ≤ mixture Λ n ω := by
  have := mixAcc_nonneg hΛ n ω
  simpa [mixture] using this

end Nonneg

section Dominance

variable {Λ : ℕ → Ω → ℝ} (hΛ : ∀ n ω, 0 ≤ Λ n ω)
include hΛ

/-- The accumulator dominates the single change-time-`ν` component, for `n ≥ ν ≥ 1`. -/
lemma component_le_mixAcc {ν : ℕ} (hν : 1 ≤ ν) :
    ∀ {n : ℕ}, ν ≤ n → ∀ ω : Ω,
      changePrior ν * ∏ i ∈ Finset.Icc ν n, Λ i ω ≤ mixAcc Λ n ω := by
  intro n hn
  induction n, hn using Nat.le_induction with
  | base =>
    intro ω
    obtain ⟨m, rfl⟩ : ∃ m, ν = m + 1 := ⟨ν - 1, by omega⟩
    rw [Finset.Icc_self, Finset.prod_singleton, mixAcc_succ]
    have h1 : 0 ≤ mixAcc Λ m ω := mixAcc_nonneg hΛ m ω
    have h2 : 0 ≤ Λ (m + 1) ω := hΛ _ _
    nlinarith
  | succ n hn ih =>
    intro ω
    rw [Finset.prod_Icc_succ_top (by omega), mixAcc_succ]
    have h1 := ih ω
    have h2 : 0 ≤ Λ (n + 1) ω := hΛ _ _
    have h3 : 0 ≤ changePrior (n + 1) := changePrior_nonneg _
    nlinarith

/-- **Equation (5)**, in the form valid for every `n` (not only `n ≥ ν`):
`M_n ≥ π_ν ∏_{i=ν}^{n} Λ_i`.  For `n < ν` the empty product is `1` and the bound is
the tail term `t_n ≥ π_ν`. -/
theorem component_le_mixture {ν : ℕ} (hν : 1 ≤ ν) (n : ℕ) (ω : Ω) :
    changePrior ν * ∏ i ∈ Finset.Icc ν n, Λ i ω ≤ mixture Λ n ω := by
  rcases le_or_gt ν n with h | h
  · have := component_le_mixAcc hΛ hν h ω
    have h2 := (priorTail_pos n).le
    simp only [mixture]
    linarith
  · have hempty : Finset.Icc ν n = ∅ := by
      rw [Finset.Icc_eq_empty_iff]
      omega
    rw [hempty, Finset.prod_empty, mul_one]
    have hle : changePrior ν ≤ priorTail n := by
      have hν' : (1 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
      have hn' : ((n : ℝ) + 1) ≤ (ν : ℝ) := by
        have : (n : ℝ) + 1 ≤ (ν : ℝ) := by exact_mod_cast (by omega : n + 1 ≤ ν)
        exact this
      have hpos : (0 : ℝ) < (n : ℝ) + 1 := by positivity
      have hden : ((n : ℝ) + 1) ≤ (ν : ℝ) * ((ν : ℝ) + 1) := by nlinarith
      unfold changePrior priorTail
      exact one_div_le_one_div_of_le hpos hden
    have := priorTail_le_mixture hΛ n ω
    linarith

end Dominance

section Adapted

variable {m0 : MeasurableSpace Ω} {Λ : ℕ → Ω → ℝ}

/-- If each `Λ_n` is `ℱ_n`-measurable then each `A_n` is `ℱ_n`-measurable. -/
lemma stronglyMeasurable_mixAcc (ℱ : Filtration ℕ m0)
    (hΛ : ∀ n, StronglyMeasurable[ℱ n] (Λ n)) :
    ∀ n, StronglyMeasurable[ℱ n] (mixAcc Λ n) := by
  intro n
  induction n with
  | zero => simpa using stronglyMeasurable_const
  | succ n ih =>
    have h1 : StronglyMeasurable[ℱ (n + 1)] (mixAcc Λ n) :=
      ih.mono (ℱ.mono (Nat.le_succ n))
    exact (hΛ (n + 1)).mul (h1.add stronglyMeasurable_const)

lemma stronglyMeasurable_mixture (ℱ : Filtration ℕ m0)
    (hΛ : ∀ n, StronglyMeasurable[ℱ n] (Λ n)) :
    ∀ n, StronglyMeasurable[ℱ n] (mixture Λ n) := fun n =>
  (stronglyMeasurable_mixAcc ℱ hΛ n).add stronglyMeasurable_const

lemma stronglyAdapted_mixture (ℱ : Filtration ℕ m0)
    (hΛ : ∀ n, StronglyMeasurable[ℱ n] (Λ n)) :
    StronglyAdapted ℱ (mixture Λ) := stronglyMeasurable_mixture ℱ hΛ

lemma measurable_mixAcc {Λ : ℕ → Ω → ℝ} (hΛ : ∀ n, Measurable (Λ n)) :
    ∀ n, Measurable (mixAcc Λ n) := by
  intro n
  induction n with
  | zero => exact measurable_const
  | succ n ih => exact (hΛ (n + 1)).mul (ih.add measurable_const)

end Adapted

section Integrability

variable {m0 : MeasurableSpace Ω} {μ : Measure Ω} {Λ : ℕ → Ω → ℝ}

/-- If the likelihood ratios are uniformly bounded, so is each accumulator `A_n`. -/
lemma exists_bound_mixAcc {K : ℝ} (hK0 : 0 ≤ K) (hK : ∀ n ω, |Λ n ω| ≤ K) (n : ℕ) :
    ∃ C : ℝ, 0 ≤ C ∧ ∀ ω, |mixAcc Λ n ω| ≤ C := by
  induction n with
  | zero => exact ⟨0, le_rfl, by simp⟩
  | succ n ih =>
    obtain ⟨C, hC0, hC⟩ := ih
    have hπ : 0 ≤ changePrior (n + 1) := changePrior_nonneg _
    refine ⟨K * (C + changePrior (n + 1)), mul_nonneg hK0 (by linarith), fun ω => ?_⟩
    rw [mixAcc_succ, abs_mul]
    have h2 : |mixAcc Λ n ω + changePrior (n + 1)| ≤ C + changePrior (n + 1) := by
      calc |mixAcc Λ n ω + changePrior (n + 1)|
          ≤ |mixAcc Λ n ω| + |changePrior (n + 1)| := abs_add_le _ _
        _ ≤ C + changePrior (n + 1) := by
            rw [abs_of_nonneg hπ]; linarith [hC ω]
    exact mul_le_mul (hK _ _) h2 (abs_nonneg _) hK0

/-- Uniformly bounded, measurable likelihood ratios give integrable accumulators. -/
lemma integrable_mixAcc_of_bounded [IsProbabilityMeasure μ] (hmeas : ∀ n, Measurable (Λ n))
    {K : ℝ} (hK0 : 0 ≤ K) (hK : ∀ n ω, |Λ n ω| ≤ K) (n : ℕ) :
    Integrable (mixAcc Λ n) μ := by
  obtain ⟨C, _, hC⟩ := exists_bound_mixAcc hK0 hK n
  refine (integrable_const C).mono' (measurable_mixAcc hmeas n).aestronglyMeasurable
    (Filter.Eventually.of_forall fun ω => ?_)
  simpa [Real.norm_eq_abs] using hC ω

end Integrability

end Viridis.Run129.PaperFormalization

/- Engine-3 immutable source unit: NullMartingale.lean -/

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
  sorry

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
  sorry

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

/- Engine-3 immutable source unit: Dominance.lean -/

/-!
# C3: component dominance and the late-change evidence penalty

This file formalizes Equations (5)–(6) of `SEALED_paper.tex`:

* `M_n ≥ π_ν ∏_{i=ν}^{n} Λ_i` (Equation 5), hence the mixture alarm time is never later
  than the alarm time of the embedded change-time-`ν` component;
* `a_ν = log(1/(α π_ν)) = log(1/α) + log[ν(ν+1)]` (Equation 6), whose late-change part
  `log[ν(ν+1)]` is asymptotically `2 log ν`.

The alarm time is formalized by `firstAlarm f c`, the first index at which the path `f`
reaches the level `c`, valued in `ℕ∞` so that "never alarms" is represented by `⊤`.
-/

namespace Viridis.Run129.PaperFormalization

open Filter
open scoped Topology

variable {Ω : Type*}

/-- The first index at which the path `f` reaches level `c`, or `⊤` if it never does. -/
noncomputable def firstAlarm (f : ℕ → ℝ) (c : ℝ) : ℕ∞ :=
  sInf ((fun n : ℕ => (n : ℕ∞)) '' {n : ℕ | c ≤ f n})

lemma firstAlarm_le_of_le {f : ℕ → ℝ} {c : ℝ} {n : ℕ} (h : c ≤ f n) :
    firstAlarm f c ≤ (n : ℕ∞) :=
  sInf_le ⟨n, h, rfl⟩

lemma firstAlarm_eq_top_iff {f : ℕ → ℝ} {c : ℝ} :
    firstAlarm f c = ⊤ ↔ ∀ n, ¬ (c ≤ f n) := by
  constructor
  · intro h n hn
    have h2 := firstAlarm_le_of_le (f := f) (c := c) hn
    rw [h] at h2
    simp at h2
  · intro h
    have : ((fun n : ℕ => (n : ℕ∞)) '' {n : ℕ | c ≤ f n}) = ∅ := by
      ext x; simp only [Set.mem_image, Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
      rintro ⟨n, hn, rfl⟩; exact h n hn
    simp [firstAlarm, this]

/-- `firstAlarm` computes the least crossing index. -/
lemma firstAlarm_eq_of_isLeast {f : ℕ → ℝ} {c : ℝ} {m : ℕ}
    (h : IsLeast {n : ℕ | c ≤ f n} m) : firstAlarm f c = (m : ℕ∞) := by
  refine le_antisymm (sInf_le ⟨m, h.1, rfl⟩) (le_sInf ?_)
  rintro x ⟨k, hk, rfl⟩
  simp only
  exact_mod_cast h.2 hk

/-- A path that dominates another alarms no later than it. -/
lemma firstAlarm_mono {f g : ℕ → ℝ} (h : ∀ n, g n ≤ f n) (c : ℝ) :
    firstAlarm f c ≤ firstAlarm g c := by
  refine sInf_le_sInf ?_
  rintro x ⟨n, hn, rfl⟩
  exact ⟨n, (hn.trans (h n) : c ≤ f n), rfl⟩

/-- The embedded change-time-`ν` likelihood-ratio component `π_ν ∏_{i=ν}^{n} Λ_i`. -/
noncomputable def component (Λ : ℕ → Ω → ℝ) (ν : ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  changePrior ν * ∏ i ∈ Finset.Icc ν n, Λ i ω

/-- The evidence boundary `a_ν = log(1/(α π_ν))` of Equation (6). -/
noncomputable def evidenceBoundary (α : ℝ) (ν : ℕ) : ℝ := Real.log (1 / (α * changePrior ν))

/-- **C3** (`change_component_dominance_and_penalty`, Equations 5–6).

1. Equation (5): the mixture dominates the embedded change-time-`ν` component pathwise.
2. Consequently the mixture alarm time at threshold `1/α` is never later than the alarm
   time of that component ("the mixture stops no later than the embedded true-change
   component").
3. Equation (6): the evidence the component must accumulate is
   `a_ν = log(1/α) + log[ν(ν+1)]`, exhibiting the late-change penalty `log[ν(ν+1)]`. -/
theorem change_component_dominance_and_penalty (Λ : ℕ → Ω → ℝ) (hΛ : ∀ n ω, 0 ≤ Λ n ω)
    {ν : ℕ} (hν : 1 ≤ ν) {α : ℝ} (hα : 0 < α) :
    (∀ n ω, component Λ ν n ω ≤ mixture Λ n ω) ∧
    (∀ ω, firstAlarm (fun n => mixture Λ n ω) (1 / α)
        ≤ firstAlarm (fun n => component Λ ν n ω) (1 / α)) ∧
    evidenceBoundary α ν = Real.log (1 / α) + Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) := by
  sorry

/-- Equation (6) read as an evidence threshold: for a strictly positive likelihood-ratio
path, the change-time-`ν` component reaches the alarm level `1/α` exactly when the
post-change log-likelihood sum reaches the boundary `a_ν`. -/
lemma component_crossing_iff_evidence (Λ : ℕ → Ω → ℝ) {ν : ℕ} (hν : 1 ≤ ν) {α : ℝ}
    (hα : 0 < α) (ω : Ω) (hpos : ∀ i, 0 < Λ i ω) (n : ℕ) :
    (1 / α ≤ component Λ ν n ω) ↔
      evidenceBoundary α ν ≤ ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) := by
  have hprodpos : 0 < ∏ i ∈ Finset.Icc ν n, Λ i ω :=
    Finset.prod_pos (fun i _ => hpos i)
  have hπpos : 0 < changePrior ν := changePrior_pos hν
  have hcomp : 0 < component Λ ν n ω := mul_pos hπpos hprodpos
  have hlogprod : Real.log (∏ i ∈ Finset.Icc ν n, Λ i ω)
      = ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) :=
    Real.log_prod (fun i _ => ne_of_gt (hpos i))
  have hcompl : Real.log (component Λ ν n ω)
      = Real.log (changePrior ν) + ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) := by
    rw [component, Real.log_mul (ne_of_gt hπpos) (ne_of_gt hprodpos), hlogprod]
  have hb : evidenceBoundary α ν = Real.log (1 / α) - Real.log (changePrior ν) := by
    rw [evidenceBoundary, one_div, Real.log_inv, Real.log_mul (ne_of_gt hα)
      (ne_of_gt hπpos), one_div, Real.log_inv]
    ring
  constructor
  · intro h
    have := Real.log_le_log (by positivity) h
    rw [hcompl] at this
    rw [hb]
    have h2 : Real.log (1 / α) ≤ Real.log (component Λ ν n ω) := by
      rw [hcompl]; exact this
    rw [hcompl] at h2
    linarith
  · intro h
    rw [hb] at h
    have h2 : Real.log (1 / α) ≤ Real.log (component Λ ν n ω) := by
      rw [hcompl]; linarith
    have := Real.exp_le_exp.2 h2
    rwa [Real.exp_log (by positivity), Real.exp_log hcomp] at this

/-- The late-change penalty `log[ν(ν+1)]` is asymptotically `2 log ν` (difference form). -/
theorem late_change_penalty_sub_tendsto_zero :
    Tendsto (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν)
      atTop (𝓝 0) := by
  have hev : (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν)
      =ᶠ[atTop] (fun ν : ℕ => Real.log (1 + 1 / (ν : ℝ))) := by
    filter_upwards [eventually_ge_atTop 1] with ν hν
    have hνR : (1 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
    have hpos : (0 : ℝ) < (ν : ℝ) := by linarith
    have h1 : Real.log ((ν : ℝ) * ((ν : ℝ) + 1))
        = Real.log ν + Real.log ((ν : ℝ) + 1) :=
      Real.log_mul (ne_of_gt hpos) (by positivity)
    have h2 : (1 : ℝ) + 1 / (ν : ℝ) = ((ν : ℝ) + 1) / (ν : ℝ) := by
      field_simp
    rw [h1, h2, Real.log_div (by positivity) (ne_of_gt hpos)]
    ring
  refine Tendsto.congr' hev.symm ?_
  have h1 : Tendsto (fun ν : ℕ => 1 + 1 / (ν : ℝ)) atTop (𝓝 1) := by
    have h0 : Tendsto (fun n : ℕ => 1 / (n : ℝ)) atTop (𝓝 0) :=
      tendsto_one_div_atTop_nhds_zero_nat
    simpa using (tendsto_const_nhds (x := (1 : ℝ)) (f := (atTop : Filter ℕ))).add h0
  have := (Real.continuousAt_log (by norm_num : (1 : ℝ) ≠ 0)).tendsto.comp h1
  simpa using this

/-- The late-change penalty `log[ν(ν+1)]` is asymptotically `2 log ν` (ratio form). -/
theorem late_change_penalty_ratio_tendsto_one :
    Tendsto (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) / (2 * Real.log ν))
      atTop (𝓝 1) := by
  have hlog : Tendsto (fun ν : ℕ => 2 * Real.log ν) atTop atTop := by
    have h : Tendsto (fun ν : ℕ => Real.log ν) atTop atTop :=
      Real.tendsto_log_atTop.comp (tendsto_natCast_atTop_atTop (R := ℝ))
    exact Filter.Tendsto.const_mul_atTop (by norm_num : (0:ℝ) < 2) h
  have hquot : Tendsto
      (fun ν : ℕ => (Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν) / (2 * Real.log ν))
      atTop (𝓝 0) := late_change_penalty_sub_tendsto_zero.div_atTop hlog
  have hev : ∀ᶠ ν : ℕ in atTop,
      1 + (Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν) / (2 * Real.log ν)
        = Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) / (2 * Real.log ν) := by
    filter_upwards [eventually_ge_atTop 2] with ν hν
    have hνR : (2 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
    have hlogpos : 0 < Real.log ν := Real.log_pos (by linarith)
    field_simp
    ring
  refine Tendsto.congr' hev ?_
  simpa using (tendsto_const_nhds (x := (1 : ℝ)) (f := (atTop : Filter ℕ))).add hquot

end Viridis.Run129.PaperFormalization

/- Engine-3 immutable source unit: Wald.lean -/

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
  sorry

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

/- Engine-3 immutable source unit: Witnesses.lean -/

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
