import Mathlib.Analysis.Calculus.Deriv.Basic
import Mathlib.Analysis.Calculus.Deriv.Add
import Mathlib.Analysis.Calculus.Deriv.Mul
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Finset.Lattice.Fold
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace Viridis.Run124.PaperFormalization

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

def ind (b : Bool) : ℝ := if b then 1 else 0

def plug (e : ι) (σ : {f : ι // f ≠ e} → Bool) (b : Bool) : ι → Bool :=
  fun f => if h : f = e then b else σ ⟨f, h⟩

def weight (p : ι → ℝ) (ω : ι → Bool) : ℝ :=
  ∏ f, (if ω f then p f else 1 - p f)

def coWeight (e : ι) (p : ι → ℝ) (σ : {f : ι // f ≠ e} → Bool) : ℝ :=
  ∏ f : {f : ι // f ≠ e}, (if σ f then p (f : ι) else 1 - p (f : ι))

def reliability (φ : (ι → Bool) → Bool) (p : ι → ℝ) : ℝ :=
  ∑ ω, weight p ω * ind (φ ω)

def pivotalProb (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) : ℝ :=
  ∑ σ : {f : ι // f ≠ e} → Bool,
    coWeight e p σ * ind (φ (plug e σ true) && !(φ (plug e σ false)))

theorem reliability_derivative_eq_pivotal_probability
    (φ : (ι → Bool) → Bool) (hφ : Monotone φ) (p : ι → ℝ) (e : ι) :
    (∀ t : ℝ, reliability φ (Function.update p e t)
        = reliability φ (Function.update p e 0) + t * pivotalProb φ p e)
      ∧ HasDerivAt (fun t : ℝ => reliability φ (Function.update p e t))
          (pivotalProb φ p e) (p e) := by
  sorry

theorem pivotal_probability_independent_of_own_probability
    (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) (t : ℝ) :
    pivotalProb φ (Function.update p e t) e = pivotalProb φ p e := by
  sorry

def firstOrderGain (φ : (ι → Bool) → Bool) (p : ι → ℝ) (d : ι → ℝ) : ℝ :=
  ∑ f, pivotalProb φ p f * d f

def feasibleGains (φ : (ι → Bool) → Bool) (p : ι → ℝ) (c : ι → ℝ) (B : ℝ) : Set ℝ :=
  {g | ∃ d : ι → ℝ, (∀ f, 0 ≤ d f) ∧ ∑ f, c f * d f ≤ B ∧ g = firstOrderGain φ p d}

noncomputable def bestRatio [Nonempty ι]
    (φ : (ι → Bool) → Bool) (p : ι → ℝ) (c : ι → ℝ) : ℝ :=
  (univ : Finset ι).sup' Finset.univ_nonempty (fun f => pivotalProb φ p f / c f)

theorem local_linear_budget_gain_le_best_ratio [Nonempty ι]
    (φ : (ι → Bool) → Bool) (p : ι → ℝ) (hp : ∀ f, 0 ≤ p f ∧ p f ≤ 1)
    (c : ι → ℝ) (hc : ∀ f, 0 < c f) (B : ℝ) (hB : 0 ≤ B) :
    IsGreatest (feasibleGains φ p c B) (B * bestRatio φ p c) := by
  sorry

def mixedDifference (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e₁ e₂ : ι) : ℝ :=
  reliability φ (Function.update (Function.update p e₁ 1) e₂ 1)
    - reliability φ (Function.update (Function.update p e₁ 1) e₂ 0)
    - reliability φ (Function.update (Function.update p e₁ 0) e₂ 1)
    + reliability φ (Function.update (Function.update p e₁ 0) e₂ 0)

theorem series_parallel_mixed_difference_signs
    (e₁ e₂ : ι) (h12 : e₁ ≠ e₂)
    (ψ : (ι → Bool) → Bool)
    (hψ₁ : ∀ (ω : ι → Bool) (b : Bool), ψ (Function.update ω e₁ b) = ψ ω)
    (hψ₂ : ∀ (ω : ι → Bool) (b : Bool), ψ (Function.update ω e₂ b) = ψ ω)
    (p : ι → ℝ) (hp : ∀ f, 0 < p f ∧ p f < 1)
    (ω₀ : ι → Bool) (hω₀ : ψ ω₀ = true)
    (φser φpar : (ι → Bool) → Bool)
    (hser : ∀ ω : ι → Bool, φser ω = (ω e₁ && ω e₂ && ψ ω))
    (hpar : ∀ ω : ι → Bool, φpar ω = ((ω e₁ || ω e₂) && ψ ω)) :
    0 < mixedDifference φser p e₁ e₂ ∧ mixedDifference φpar p e₁ e₂ < 0 := by
  sorry

def series2 : (Fin 2 → Bool) → Bool := fun ω => ω 0 && ω 1

def parallel2 : (Fin 2 → Bool) → Bool := fun ω => ω 0 || ω 1

def IsProbDist (μ : (ι → Bool) → ℝ) : Prop :=
  (∀ ω, 0 ≤ μ ω) ∧ ∑ ω, μ ω = 1

def edgeMarginal (μ : (ι → Bool) → ℝ) (e : ι) : ℝ :=
  ∑ ω, μ ω * ind (ω e)

def jointReliability (φ : (ι → Bool) → Bool) (μ : (ι → Bool) → ℝ) : ℝ :=
  ∑ ω, μ ω * ind (φ ω)

theorem equal_marginals_do_not_identify_reliability :
    ∃ (φ : (Fin 2 → Bool) → Bool) (p : Fin 2 → ℝ) (μ₁ μ₂ : (Fin 2 → Bool) → ℝ),
      Monotone φ ∧ IsProbDist μ₁ ∧ IsProbDist μ₂ ∧
      μ₁ = weight p ∧
      (∀ e, edgeMarginal μ₁ e = p e) ∧
      (∀ e, edgeMarginal μ₁ e = edgeMarginal μ₂ e) ∧
      jointReliability φ μ₁ ≠ jointReliability φ μ₂ := by
  sorry

noncomputable def pEx (i : Fin 2) : ℝ := if i = 0 then 1 / 2 else 1 / 3

noncomputable def cEx (i : Fin 2) : ℝ := if i = 0 then 1 else 2

theorem witness_C1 :
    HasDerivAt (fun t : ℝ => reliability series2 (Function.update pEx 0 t)) (1 / 3) (pEx 0)
      ∧ pivotalProb series2 pEx 0 ≠ 0 := by
  sorry

theorem witness_C2 (t : ℝ) :
    pivotalProb series2 (Function.update pEx 0 t) 0 = 1 / 3 := by
  sorry

theorem witness_C3 :
    IsGreatest (feasibleGains series2 pEx cEx 1) (1 / 3) := by
  sorry

theorem witness_C4 :
    0 < mixedDifference series2 pEx 0 1 ∧
      mixedDifference parallel2 pEx 0 1 < 0 := by
  sorry

end Viridis.Run124.PaperFormalization
