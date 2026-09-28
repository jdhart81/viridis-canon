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

/- Engine-3 migration note: Codex adopted this zero-sorry proof text from the
historical Run-124 repair artifact as untrusted source material. No provider
status is carried forward; the exact bytes below require fresh Comparator
nanoda and Lean-default-kernel verification before certification. -/

/-!
# Run-124 — "Pivotal corridor stewardship": Lean formalization of the frozen paper claims

This file formalizes the frozen `FORMAL_TARGET` claims C1, C2, C3, C4, C6 of
`STATEMENT_CONTRACT.md` under explicit definitions and explicit assumptions.

All probabilistic notions are finite and elementary:

* the *edge set* is an arbitrary finite type `ι`;
* a *state* is a function `ω : ι → Bool` (`true` = edge up / surviving);
* a *structure function* is a map `φ : (ι → Bool) → Bool`; coherence is the explicit
  hypothesis `Monotone φ`;
* two-terminal (s–t) connectivity is realized as a concrete monotone structure function
  in the section `TwoTerminal`, so that "two-terminal reliability" is not merely an
  abstract placeholder;
* "independent edge states" is realized by the product weight `weight p`;
* correlated failures (needed for C6) are realized by arbitrary finitely-supported
  probability weights `μ : (ι → Bool) → ℝ`.

Interpretation notes and named blockers are recorded in `FORMALIZATION_NOTES.md`.
-/

namespace Viridis.Run124.PaperFormalization

open Finset

/-! ## 1. Basic definitions -/

section Defs

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- Real-valued indicator of a boolean. -/
def ind (b : Bool) : ℝ := if b then 1 else 0

@[simp] lemma ind_true : ind true = 1 := rfl

@[simp] lemma ind_false : ind false = 0 := rfl

lemma ind_nonneg (b : Bool) : 0 ≤ ind b := by cases b <;> simp

/-- `plug e σ b` is the state that assigns `b` to the edge `e` and follows `σ` elsewhere. -/
def plug (e : ι) (σ : {f : ι // f ≠ e} → Bool) (b : Bool) : ι → Bool :=
  fun f => if h : f = e then b else σ ⟨f, h⟩

omit [Fintype ι] in
@[simp] lemma plug_self (e : ι) (σ : {f : ι // f ≠ e} → Bool) (b : Bool) :
    plug e σ b e = b := by simp [plug]

omit [Fintype ι] in
lemma plug_of_ne {e f : ι} (h : f ≠ e) (σ : {f : ι // f ≠ e} → Bool) (b : Bool) :
    plug e σ b f = σ ⟨f, h⟩ := by simp [plug, h]

/-- The independent-edge (product) probability weight of a state. -/
def weight (p : ι → ℝ) (ω : ι → Bool) : ℝ := ∏ f, (if ω f then p f else 1 - p f)

/-- The product weight of the *other* edges, i.e. of a state of `ι \ {e}`. -/
def coWeight (e : ι) (p : ι → ℝ) (σ : {f : ι // f ≠ e} → Bool) : ℝ :=
  ∏ f : {f : ι // f ≠ e}, (if σ f then p (f : ι) else 1 - p (f : ι))

/-- System reliability under independent edge states with survival probabilities `p`.
For the two-terminal structure function of `TwoTerminal` below this is exactly the
two-terminal reliability of the network. -/
def reliability (φ : (ι → Bool) → Bool) (p : ι → ℝ) : ℝ := ∑ ω, weight p ω * ind (φ ω)

/-- The pivotal probability of edge `e`: the probability that the remaining edges are in a
state for which `e` is critical (the system works iff `e` works). -/
def pivotalProb (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) : ℝ :=
  ∑ σ : {f : ι // f ≠ e} → Bool,
    coWeight e p σ * ind (φ (plug e σ true) && !(φ (plug e σ false)))

end Defs

/-! ## 2. Elementary computational lemmas -/

section Basic

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

lemma sum_split (e : ι) {M : Type*} [AddCommMonoid M] (F : (ι → Bool) → M) :
    ∑ ω, F ω = ∑ σ : {f : ι // f ≠ e} → Bool, ∑ b : Bool, F (plug e σ b) := by
  rw [← Equiv.sum_comp (Equiv.piSplitAt e (fun _ => Bool)).symm F, Fintype.sum_prod_type,
    Finset.sum_comm]
  refine Finset.sum_congr rfl (fun σ _ => Finset.sum_congr rfl (fun b _ => ?_))
  congr 1
  funext f
  simp only [Equiv.piSplitAt, plug, Equiv.coe_fn_symm_mk]
  split <;> simp_all

lemma prod_split (e : ι) (g : ι → ℝ) : ∏ f, g f = g e * ∏ f : {f : ι // f ≠ e}, g (f : ι) := by
  rw [Fintype.prod_eq_mul_prod_compl e g]
  congr 1
  exact Finset.prod_subtype _ (by simp) g

lemma weight_plug (e : ι) (p : ι → ℝ) (σ : {f : ι // f ≠ e} → Bool) (b : Bool) :
    weight p (plug e σ b) = (if b then p e else 1 - p e) * coWeight e p σ := by
  rw [weight, prod_split e]
  simp only [plug_self, coWeight]
  congr 1
  exact Finset.prod_congr rfl fun f _ => by rw [plug_of_ne f.2]

lemma coWeight_update (e : ι) (p : ι → ℝ) (t : ℝ) (σ : {f : ι // f ≠ e} → Bool) :
    coWeight e (Function.update p e t) σ = coWeight e p σ :=
  Finset.prod_congr rfl fun f _ => by rw [Function.update_of_ne f.2]

lemma coWeight_nonneg {e : ι} {p : ι → ℝ} (hp : ∀ f, 0 ≤ p f ∧ p f ≤ 1)
    (σ : {f : ι // f ≠ e} → Bool) : 0 ≤ coWeight e p σ := by
  refine Finset.prod_nonneg fun f _ => ?_
  rcases hp (f : ι) with ⟨h0, h1⟩
  by_cases h : σ f <;> simp [h] <;> linarith

/-- Conditioning the reliability on the state of a single edge `e`. -/
lemma reliability_condition (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) :
    reliability φ p =
      ∑ σ : {f : ι // f ≠ e} → Bool,
        coWeight e p σ * (p e * ind (φ (plug e σ true)) + (1 - p e) * ind (φ (plug e σ false))) := by
  rw [reliability, sum_split e]
  refine Finset.sum_congr rfl fun σ _ => ?_
  rw [Fintype.sum_bool]
  simp only [weight_plug, Bool.false_eq_true, if_true, if_false]
  ring

end Basic

/-! ## 3. C1 — Theorem 1: affineness and the pivotal derivative -/

section C1

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

omit [Fintype ι] in
/-- For a coherent (monotone) structure function, the one-edge difference of indicators is
the pivotality indicator. -/
lemma ind_sub_ind_eq_pivotal {φ : (ι → Bool) → Bool} (hφ : Monotone φ) (e : ι)
    (σ : {f : ι // f ≠ e} → Bool) :
    ind (φ (plug e σ true)) - ind (φ (plug e σ false))
      = ind (φ (plug e σ true) && !(φ (plug e σ false))) := by
  have hle : φ (plug e σ false) ≤ φ (plug e σ true) := by
    refine hφ ?_
    intro f
    by_cases h : f = e
    · subst h; simp
    · simp [plug_of_ne h]
  cases hT : φ (plug e σ true) <;> cases hF : φ (plug e σ false) <;> simp_all
  exact absurd hle (by decide)

/-- **C1 (Theorem 1).** For independent edge states and a coherent (monotone) structure
function, the reliability is an affine function of each single edge survival probability,
and its partial derivative with respect to that probability equals the pivotal probability
of that edge. -/
theorem reliability_derivative_eq_pivotal_probability
    (φ : (ι → Bool) → Bool) (hφ : Monotone φ) (p : ι → ℝ) (e : ι) :
    (∀ t : ℝ, reliability φ (Function.update p e t)
        = reliability φ (Function.update p e 0) + t * pivotalProb φ p e)
      ∧ HasDerivAt (fun t : ℝ => reliability φ (Function.update p e t))
          (pivotalProb φ p e) (p e) := by
  have key : ∀ t : ℝ, reliability φ (Function.update p e t)
      = reliability φ (Function.update p e 0) + t * pivotalProb φ p e := by
    intro t
    rw [reliability_condition φ _ e, reliability_condition φ _ e, pivotalProb,
      Finset.mul_sum, ← Finset.sum_add_distrib]
    refine Finset.sum_congr rfl fun σ _ => ?_
    rw [coWeight_update, coWeight_update, Function.update_self, Function.update_self,
      ← ind_sub_ind_eq_pivotal hφ e σ]
    ring
  refine ⟨key, ?_⟩
  have hfun : (fun t : ℝ => reliability φ (Function.update p e t))
      = fun t : ℝ => reliability φ (Function.update p e 0) + t * pivotalProb φ p e :=
    funext key
  rw [hfun]
  simpa using ((hasDerivAt_id (p e)).mul_const (pivotalProb φ p e)).const_add
    (reliability φ (Function.update p e 0))

/-- The pivotal probability is exactly the difference of the reliabilities obtained by
forcing the edge up and forcing it down. -/
lemma pivotalProb_eq_reliability_diff
    (φ : (ι → Bool) → Bool) (hφ : Monotone φ) (p : ι → ℝ) (e : ι) :
    pivotalProb φ p e
      = reliability φ (Function.update p e 1) - reliability φ (Function.update p e 0) := by
  have h := (reliability_derivative_eq_pivotal_probability φ hφ p e).1 1
  linarith

lemma pivotalProb_nonneg (φ : (ι → Bool) → Bool) {p : ι → ℝ}
    (hp : ∀ f, 0 ≤ p f ∧ p f ≤ 1) (e : ι) : 0 ≤ pivotalProb φ p e :=
  Finset.sum_nonneg fun σ _ =>
    mul_nonneg (coWeight_nonneg hp σ) (ind_nonneg _)

end C1

/-! ## 4. C2 — Corollary 1: the pivotal derivative does not depend on the edge's own probability -/

section C2

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- **C2 (Corollary 1).** The pivotal probability of an edge — i.e. the partial derivative
of the reliability with respect to that edge's survival probability — does not depend on
the edge's own survival probability. -/
theorem pivotal_probability_independent_of_own_probability
    (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) (t : ℝ) :
    pivotalProb φ (Function.update p e t) e = pivotalProb φ p e := by
  refine Finset.sum_congr rfl fun σ _ => ?_
  rw [coWeight_update]

end C2

/-! ## 5. C3 — Corollary 2: the infinitesimal linear-budget gain -/

section C3

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- The first-order gain of an infinitesimal upgrade direction `d`. -/
def firstOrderGain (φ : (ι → Bool) → Bool) (p : ι → ℝ) (d : ι → ℝ) : ℝ :=
  ∑ f, pivotalProb φ p f * d f

/-- The set of first-order gains achievable by nonnegative upgrade directions obeying the
linear budget `∑ c f * d f ≤ B`. -/
def feasibleGains (φ : (ι → Bool) → Bool) (p : ι → ℝ) (c : ι → ℝ) (B : ℝ) : Set ℝ :=
  {g | ∃ d : ι → ℝ, (∀ f, 0 ≤ d f) ∧ ∑ f, c f * d f ≤ B ∧ g = firstOrderGain φ p d}

/-- The best pivotality-to-cost ratio over all edges. -/
noncomputable def bestRatio [Nonempty ι] (φ : (ι → Bool) → Bool) (p : ι → ℝ) (c : ι → ℝ) : ℝ :=
  (univ : Finset ι).sup' Finset.univ_nonempty (fun f => pivotalProb φ p f / c f)

/-- **C3 (Corollary 2).** Under an infinitesimal linear budget `B` with positive edge costs,
the maximum achievable first-order gain equals `B` times the maximum pivotality-to-cost
ratio; in particular every feasible gain is at most that value, and the value is attained. -/
theorem local_linear_budget_gain_le_best_ratio [Nonempty ι]
    (φ : (ι → Bool) → Bool) (p : ι → ℝ) (hp : ∀ f, 0 ≤ p f ∧ p f ≤ 1)
    (c : ι → ℝ) (hc : ∀ f, 0 < c f) (B : ℝ) (hB : 0 ≤ B) :
    IsGreatest (feasibleGains φ p c B) (B * bestRatio φ p c) := by
  obtain ⟨f₀, -, hf₀⟩ := Finset.exists_mem_eq_sup' (Finset.univ_nonempty (α := ι))
    (fun f => pivotalProb φ p f / c f)
  have hratio_nonneg : 0 ≤ bestRatio φ p c := by
    rw [bestRatio, hf₀]
    exact div_nonneg (pivotalProb_nonneg φ hp f₀) (hc f₀).le
  constructor
  · -- attainment: spend the whole budget on a best-ratio edge
    refine ⟨Function.update (fun _ : ι => (0 : ℝ)) f₀ (B / c f₀), ?_, ?_, ?_⟩
    · intro f
      by_cases h : f = f₀
      · rw [h, Function.update_self]; exact div_nonneg hB (hc f₀).le
      · simp [Function.update_of_ne h]
    · rw [Finset.sum_eq_single f₀ (fun f _ hf => by simp [Function.update_of_ne hf])
        (fun h => absurd (Finset.mem_univ f₀) h), Function.update_self, mul_comm,
        div_mul_cancel₀ _ (hc f₀).ne']
    · rw [firstOrderGain, Finset.sum_eq_single f₀ (fun f _ hf => by
        simp [Function.update_of_ne hf]) (fun h => absurd (Finset.mem_univ f₀) h),
        Function.update_self, bestRatio, hf₀]
      field_simp
  · rintro g ⟨d, hd, hbudget, rfl⟩
    have hstep : ∀ f : ι, pivotalProb φ p f * d f ≤ bestRatio φ p c * (c f * d f) := by
      intro f
      have h1 : pivotalProb φ p f / c f ≤ bestRatio φ p c :=
        Finset.le_sup' (fun f => pivotalProb φ p f / c f) (Finset.mem_univ f)
      have h2 : pivotalProb φ p f ≤ bestRatio φ p c * c f := by
        rw [div_le_iff₀ (hc f)] at h1; linarith
      have := mul_le_mul_of_nonneg_right h2 (hd f)
      calc pivotalProb φ p f * d f ≤ bestRatio φ p c * c f * d f := this
        _ = bestRatio φ p c * (c f * d f) := by ring
    calc firstOrderGain φ p d ≤ ∑ f, bestRatio φ p c * (c f * d f) :=
          Finset.sum_le_sum fun f _ => hstep f
      _ = bestRatio φ p c * ∑ f, c f * d f := by rw [Finset.mul_sum]
      _ ≤ bestRatio φ p c * B := by
          exact mul_le_mul_of_nonneg_left hbudget hratio_nonneg
      _ = B * bestRatio φ p c := by ring

end C3

/-! ## 6. C4 — Proposition 1: signs of the mixed interaction for series and parallel pairs -/

section C4

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- The mixed second difference of the reliability in the two edges `e₁`, `e₂`. -/
def mixedDifference (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e₁ e₂ : ι) : ℝ :=
  reliability φ (Function.update (Function.update p e₁ 1) e₂ 1)
    - reliability φ (Function.update (Function.update p e₁ 1) e₂ 0)
    - reliability φ (Function.update (Function.update p e₁ 0) e₂ 1)
    + reliability φ (Function.update (Function.update p e₁ 0) e₂ 0)

lemma reliability_update_boolean (φ : (ι → Bool) → Bool) (p : ι → ℝ) (e : ι) (b : Bool) :
    reliability φ (Function.update p e (if b then 1 else 0))
      = reliability (fun ω => φ (Function.update ω e b)) p := by
  rw [reliability_condition φ _ e, reliability_condition _ p e]
  refine Finset.sum_congr rfl fun σ _ => ?_
  rw [coWeight_update, Function.update_self]
  have hT : Function.update (plug e σ true) e b = plug e σ b := by
    funext f
    by_cases h : f = e
    · subst h; simp
    · simp [Function.update_of_ne h, plug_of_ne h]
  have hF : Function.update (plug e σ false) e b = plug e σ b := by
    funext f
    by_cases h : f = e
    · subst h; simp
    · simp [Function.update_of_ne h, plug_of_ne h]
  simp only [hT, hF]
  cases b <;> simp only [if_true, if_false, Bool.false_eq_true] <;> ring

/-- The reliability of a structure function which is positive on some state is positive,
provided every edge probability is strictly between `0` and `1`. -/
lemma reliability_pos {ψ : (ι → Bool) → Bool} {p : ι → ℝ} (hp : ∀ f, 0 < p f ∧ p f < 1)
    {ω₀ : ι → Bool} (hω₀ : ψ ω₀ = true) : 0 < reliability ψ p := by
  have hw : ∀ ω : ι → Bool, 0 < weight p ω := by
    intro ω
    refine Finset.prod_pos fun f _ => ?_
    rcases hp f with ⟨h0, h1⟩
    by_cases h : ω f <;> simp [h] <;> linarith
  have h1 : weight p ω₀ * ind (ψ ω₀) ≤ reliability ψ p :=
    Finset.single_le_sum (f := fun ω => weight p ω * ind (ψ ω))
      (fun ω _ => mul_nonneg (hw ω).le (ind_nonneg _)) (Finset.mem_univ ω₀)
  have h2 : 0 < weight p ω₀ * ind (ψ ω₀) := by
    rw [hω₀, ind_true, mul_one]; exact hw ω₀
  linarith

/-- **C4 (Proposition 1).** If two edges `e₁ ≠ e₂` are *in series* (both are required, on top
of a residual structure `ψ` not involving them), their mixed interaction is strictly
positive; if they are *in parallel* (either one suffices, on top of the same residual
structure `ψ`), their mixed interaction is strictly negative. -/
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
  have hRψ : 0 < reliability ψ p := reliability_pos hp hω₀
  have hfalse : reliability (fun _ : ι → Bool => false) p = 0 := by simp [reliability]
  have hstate : ∀ (ω : ι → Bool) (a b : Bool),
      (Function.update (Function.update ω e₁ a) e₂ b) e₁ = a ∧
        (Function.update (Function.update ω e₁ a) e₂ b) e₂ = b ∧
        ψ (Function.update (Function.update ω e₁ a) e₂ b) = ψ ω := by
    intro ω a b
    refine ⟨?_, ?_, ?_⟩
    · rw [Function.update_of_ne h12, Function.update_self]
    · rw [Function.update_self]
    · rw [hψ₂, hψ₁]
  have key : ∀ (φ : (ι → Bool) → Bool) (a b : Bool),
      reliability φ (Function.update (Function.update p e₁ (if a then 1 else 0)) e₂
          (if b then 1 else 0))
        = reliability (fun ω => φ (Function.update (Function.update ω e₁ a) e₂ b)) p := by
    intro φ a b
    rw [reliability_update_boolean φ _ e₂ b, reliability_update_boolean _ p e₁ a]
  constructor
  · have h11 := key φser true true
    have h10 := key φser true false
    have h01 := key φser false true
    have h00 := key φser false false
    simp only [if_true, if_false, Bool.false_eq_true] at h11 h10 h01 h00
    have e11 : (fun ω => φser (Function.update (Function.update ω e₁ true) e₂ true)) = ψ := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω true true
      rw [hser, ha, hb, hc]; simp
    have e10 : (fun ω => φser (Function.update (Function.update ω e₁ true) e₂ false))
        = fun _ => false := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω true false
      rw [hser, ha, hb, hc]; simp
    have e01 : (fun ω => φser (Function.update (Function.update ω e₁ false) e₂ true))
        = fun _ => false := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω false true
      rw [hser, ha, hb, hc]; simp
    have e00 : (fun ω => φser (Function.update (Function.update ω e₁ false) e₂ false))
        = fun _ => false := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω false false
      rw [hser, ha, hb, hc]; simp
    rw [e11] at h11; rw [e10] at h10; rw [e01] at h01; rw [e00] at h00
    rw [mixedDifference, h11, h10, h01, h00, hfalse]
    linarith
  · have h11 := key φpar true true
    have h10 := key φpar true false
    have h01 := key φpar false true
    have h00 := key φpar false false
    simp only [if_true, if_false, Bool.false_eq_true] at h11 h10 h01 h00
    have e11 : (fun ω => φpar (Function.update (Function.update ω e₁ true) e₂ true)) = ψ := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω true true
      rw [hpar, ha, hb, hc]; simp
    have e10 : (fun ω => φpar (Function.update (Function.update ω e₁ true) e₂ false)) = ψ := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω true false
      rw [hpar, ha, hb, hc]; simp
    have e01 : (fun ω => φpar (Function.update (Function.update ω e₁ false) e₂ true)) = ψ := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω false true
      rw [hpar, ha, hb, hc]; simp
    have e00 : (fun ω => φpar (Function.update (Function.update ω e₁ false) e₂ false))
        = fun _ => false := by
      funext ω
      obtain ⟨ha, hb, hc⟩ := hstate ω false false
      rw [hpar, ha, hb, hc]; simp
    rw [e11] at h11; rw [e10] at h10; rw [e01] at h01; rw [e00] at h00
    rw [mixedDifference, h11, h10, h01, h00, hfalse]
    linarith

end C4

/-! ## 7. The two-edge toolkit on `Fin 2`

Explicit computations used for the non-vacuity witnesses and for the negative control. -/

section TwoEdge

open Finset

lemma sum_fin2 (F : (Fin 2 → Bool) → ℝ) :
    ∑ ω, F ω = F ![false, false] + F ![false, true] + F ![true, false] + F ![true, true] := by
  have hc : ∀ a b : Bool, (Fin.cons a (Fin.cons b finZeroElim) : Fin 2 → Bool) = ![a, b] := by
    intro a b; funext i; fin_cases i <;> rfl
  rw [← Equiv.sum_comp (piFinTwoEquiv (fun _ => Bool)).symm F, Fintype.sum_prod_type]
  simp only [piFinTwoEquiv, Equiv.coe_fn_symm_mk, Fintype.sum_bool, hc]
  ring

/-- The two-edge series structure function: both edges are required. -/
def series2 : (Fin 2 → Bool) → Bool := fun ω => ω 0 && ω 1

/-- The two-edge parallel structure function: either edge suffices. -/
def parallel2 : (Fin 2 → Bool) → Bool := fun ω => ω 0 || ω 1

lemma series2_monotone : Monotone series2 := by
  intro ω ω' h
  have h0 := h 0
  have h1 := h 1
  simp only [series2]
  revert h0 h1
  cases ω 0 <;> cases ω 1 <;> cases ω' 0 <;> cases ω' 1 <;> simp

lemma parallel2_monotone : Monotone parallel2 := by
  intro ω ω' h
  have h0 := h 0
  have h1 := h 1
  simp only [parallel2]
  revert h0 h1
  cases ω 0 <;> cases ω 1 <;> cases ω' 0 <;> cases ω' 1 <;> simp

lemma reliability_fin2 (φ : (Fin 2 → Bool) → Bool) (q : Fin 2 → ℝ) :
    reliability φ q =
      (1 - q 0) * (1 - q 1) * ind (φ ![false, false])
        + (1 - q 0) * q 1 * ind (φ ![false, true])
        + q 0 * (1 - q 1) * ind (φ ![true, false])
        + q 0 * q 1 * ind (φ ![true, true]) := by
  rw [reliability, sum_fin2]
  simp only [weight, Fin.prod_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one,
    if_true, if_false, Bool.false_eq_true]

end TwoEdge

/-! ## 8. C6 — Negative control: equal marginals do not identify reliability -/

section C6

open Finset

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

/-- A (possibly correlated) joint distribution of edge states. -/
def IsProbDist (μ : (ι → Bool) → ℝ) : Prop := (∀ ω, 0 ≤ μ ω) ∧ ∑ ω, μ ω = 1

/-- The marginal survival probability of edge `e` under a joint distribution. -/
def edgeMarginal (μ : (ι → Bool) → ℝ) (e : ι) : ℝ := ∑ ω, μ ω * ind (ω e)

/-- Terminal reliability under a (possibly correlated) joint distribution. -/
def jointReliability (φ : (ι → Bool) → Bool) (μ : (ι → Bool) → ℝ) : ℝ :=
  ∑ ω, μ ω * ind (φ ω)

/-- The independent (product) model with survival probabilities `p`, viewed as a joint
distribution. -/
lemma jointReliability_weight (φ : (ι → Bool) → Bool) (p : ι → ℝ) :
    jointReliability φ (weight p) = reliability φ p := rfl

/-- The independent fair-coin distribution on two edges. -/
noncomputable def indepHalf : (Fin 2 → Bool) → ℝ := fun _ => 1 / 4

/-- The perfectly correlated distribution on two edges: both edges are up, or both are
down, with probability `1/2` each. -/
noncomputable def comonotoneHalf : (Fin 2 → Bool) → ℝ := fun ω => if ω 0 = ω 1 then 1 / 2 else 0

lemma indepHalf_eq_weight : indepHalf = weight (fun _ : Fin 2 => (1 : ℝ) / 2) := by
  funext ω
  simp only [indepHalf, weight, Fin.prod_univ_two]
  cases ω 0 <;> cases ω 1 <;> norm_num

/-- **C6 (negative control).** There are two joint distributions of edge states with
identical edge marginals but different terminal reliabilities for one and the same
coherent structure function; moreover one of the two is the independent product model
with those very marginals. Hence marginal edge survival probabilities do not identify
terminal reliability once failures may be correlated. -/
theorem equal_marginals_do_not_identify_reliability :
    ∃ (φ : (Fin 2 → Bool) → Bool) (p : Fin 2 → ℝ) (μ₁ μ₂ : (Fin 2 → Bool) → ℝ),
      Monotone φ ∧ IsProbDist μ₁ ∧ IsProbDist μ₂ ∧
      μ₁ = weight p ∧
      (∀ e, edgeMarginal μ₁ e = p e) ∧
      (∀ e, edgeMarginal μ₁ e = edgeMarginal μ₂ e) ∧
      jointReliability φ μ₁ ≠ jointReliability φ μ₂ := by
  refine ⟨series2, fun _ => 1 / 2, indepHalf, comonotoneHalf, series2_monotone, ⟨?_, ?_⟩,
    ⟨?_, ?_⟩, indepHalf_eq_weight, ?_, ?_, ?_⟩
  · intro ω; norm_num [indepHalf]
  · rw [sum_fin2]; norm_num [indepHalf]
  · intro ω; unfold comonotoneHalf; split <;> norm_num
  · rw [sum_fin2]; norm_num [comonotoneHalf]
  · intro e
    fin_cases e <;>
      · rw [edgeMarginal, sum_fin2]; norm_num [indepHalf, ind]
  · intro e
    fin_cases e <;>
      · rw [edgeMarginal, edgeMarginal, sum_fin2, sum_fin2]
        norm_num [indepHalf, comonotoneHalf, ind]
  · rw [jointReliability, jointReliability, sum_fin2, sum_fin2]
    norm_num [indepHalf, comonotoneHalf, series2, ind]

end C6

/-! ## 10. Non-vacuity witnesses

Every formalized target is instantiated on an explicit example with a nondegenerate
conclusion. -/

section Witnesses

open Finset

/-- Edge survival probabilities of the running example: `p 0 = 1/2`, `p 1 = 1/3`. -/
noncomputable def pEx (i : Fin 2) : ℝ := if i = 0 then 1 / 2 else 1 / 3

lemma pEx_mem_Icc : ∀ f, 0 ≤ pEx f ∧ pEx f ≤ 1 := by
  intro f; fin_cases f <;> norm_num [pEx]

lemma pEx_mem_Ioo : ∀ f, 0 < pEx f ∧ pEx f < 1 := by
  intro f; fin_cases f <;> norm_num [pEx]

/-- The reliability of the two-edge series system in the running example is `1/6`. -/
lemma reliability_series2_pEx : reliability series2 pEx = 1 / 6 := by
  rw [reliability_fin2]
  norm_num [pEx, series2, ind]

/-- Non-vacuity for **C1**: the pivotal probability of edge `0` is `1/3 ≠ 0`, so the
derivative statement has nondegenerate content. -/
lemma pivotalProb_series2_pEx_zero : pivotalProb series2 pEx 0 = 1 / 3 := by
  rw [pivotalProb_eq_reliability_diff series2 series2_monotone pEx 0,
    reliability_fin2, reliability_fin2]
  norm_num [pEx, series2, ind, Function.update_apply, Fin.ext_iff]

/-- Non-vacuity for **C1**: the pivotal probability of edge `1` is `1/2 ≠ 0`. -/
lemma pivotalProb_series2_pEx_one : pivotalProb series2 pEx 1 = 1 / 2 := by
  rw [pivotalProb_eq_reliability_diff series2 series2_monotone pEx 1,
    reliability_fin2, reliability_fin2]
  norm_num [pEx, series2, ind, Function.update_apply, Fin.ext_iff]

/-- **Witness for C1.** The derivative of the two-edge series reliability with respect to
`p 0`, at `p = (1/2, 1/3)`, exists and equals the (nonzero) pivotal probability `1/3`. -/
theorem witness_C1 :
    HasDerivAt (fun t : ℝ => reliability series2 (Function.update pEx 0 t)) (1 / 3) (pEx 0)
      ∧ pivotalProb series2 pEx 0 ≠ 0 := by
  refine ⟨?_, by rw [pivotalProb_series2_pEx_zero]; norm_num⟩
  have := (reliability_derivative_eq_pivotal_probability series2 series2_monotone pEx 0).2
  rwa [pivotalProb_series2_pEx_zero] at this

/-- **Witness for C2.** The pivotal probability of edge `0` stays equal to `1/3` however
the survival probability of edge `0` itself is changed. -/
theorem witness_C2 (t : ℝ) : pivotalProb series2 (Function.update pEx 0 t) 0 = 1 / 3 := by
  rw [pivotal_probability_independent_of_own_probability, pivotalProb_series2_pEx_zero]

/-- Upgrade costs of the running example: cost `1` for edge `0`, cost `2` for edge `1`. -/
noncomputable def cEx (i : Fin 2) : ℝ := if i = 0 then 1 else 2

lemma cEx_pos : ∀ f, 0 < cEx f := by
  intro f; fin_cases f <;> norm_num [cEx]

lemma bestRatio_series2_pEx : bestRatio series2 pEx cEx = 1 / 3 := by
  rw [bestRatio]
  refine le_antisymm (Finset.sup'_le _ _ (fun f _ => ?_)) ?_
  · have hf : f = 0 ∨ f = 1 := by fin_cases f <;> simp
    rcases hf with rfl | rfl
    · rw [pivotalProb_series2_pEx_zero]; norm_num [cEx]
    · rw [pivotalProb_series2_pEx_one]; norm_num [cEx]
  · have h0 := Finset.le_sup' (fun f : Fin 2 => pivotalProb series2 pEx f / cEx f)
      (Finset.mem_univ 0)
    rw [pivotalProb_series2_pEx_zero] at h0
    have hc0 : cEx 0 = 1 := by norm_num [cEx]
    rwa [hc0, div_one] at h0

/-- **Witness for C3.** With budget `B = 1`, costs `(1, 2)` and `p = (1/2, 1/3)`, the
maximum first-order gain is exactly `1/3 > 0`, attained by spending the whole budget on
edge `0`. -/
theorem witness_C3 :
    IsGreatest (feasibleGains series2 pEx cEx 1) (1 / 3) := by
  have h := local_linear_budget_gain_le_best_ratio series2 pEx pEx_mem_Icc cEx cEx_pos 1
    (by norm_num)
  rwa [bestRatio_series2_pEx, one_mul] at h

/-- **Witness for C4.** Two edges in series have strictly positive mixed interaction and
two edges in parallel have strictly negative mixed interaction, on the explicit two-edge
example with `p = (1/2, 1/3)`. -/
theorem witness_C4 :
    0 < mixedDifference series2 pEx 0 1 ∧ mixedDifference parallel2 pEx 0 1 < 0 := by
  refine series_parallel_mixed_difference_signs 0 1 (by decide) (fun _ => true)
    (fun _ _ => rfl) (fun _ _ => rfl) pEx pEx_mem_Ioo (fun _ => true) rfl series2 parallel2
    (fun ω => by simp [series2]) (fun ω => by simp [parallel2])

end Witnesses

end Viridis.Run124.PaperFormalization
