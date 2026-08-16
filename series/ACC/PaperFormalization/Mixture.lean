import PaperFormalization.Prior

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
