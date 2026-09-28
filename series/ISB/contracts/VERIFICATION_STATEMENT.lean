/- Engine-3 immutable source unit: Entropy.lean -/
import Mathlib.Analysis.SpecialFunctions.Log.NegMulLog
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring

/-!
# Finite Shannon entropy in bits, and the information quantities of Run-121

This file sets up the elementary machinery used to formalize the sealed paper
*Information Symbiosis Balance* (Run-121).

All random variables are modelled as functions `f : Ω → α` out of a finite sample space `Ω`
carrying a mass function `p : Ω → ℝ` (assumed nonnegative and summing to one exactly where
those assumptions are needed).  Logarithms are base 2 and `0 log 0 = 0`, matching the paper's
conventions; this is implemented through `Real.negMulLog` (which is `0` at `0`) divided by
`Real.log 2`.
-/

namespace Viridis.Run121

open Finset

variable {Ω : Type*} [Fintype Ω] {α β γ : Type*}

/-- `probOf p f a` is the probability that the finite-valued observable `f` takes the value `a`,
i.e. the push-forward mass function of `f` under `p`. -/
noncomputable def probOf [DecidableEq α] (p : Ω → ℝ) (f : Ω → α) (a : α) : ℝ :=
  ∑ ω, if f ω = a then p ω else 0

/-- Shannon entropy, in bits, of the observable `f` under the mass function `p`.
This is `H(f) = - ∑ₐ P(f = a) log₂ P(f = a)` with the convention `0 log 0 = 0`. -/
noncomputable def entropyBits [Fintype α] [DecidableEq α] (p : Ω → ℝ) (f : Ω → α) : ℝ :=
  (∑ a, Real.negMulLog (probOf p f a)) / Real.log 2

variable {p : Ω → ℝ} {f : Ω → α} {g : Ω → β} {h : Ω → γ}

/-! ### Basic properties of the push-forward mass function -/

lemma probOf_nonneg [DecidableEq α] (hp : ∀ ω, 0 ≤ p ω) (a : α) : 0 ≤ probOf p f a := by
  apply Finset.sum_nonneg
  intro ω _
  split
  · exact hp ω
  · exact le_rfl

lemma sum_probOf [Fintype α] [DecidableEq α] : ∑ a, probOf p f a = ∑ ω, p ω := by
  simp only [probOf]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun ω _ => ?_
  simp

lemma probOf_comp_injective [DecidableEq α] {α' : Type*} [DecidableEq α'] {e : α → α'}
    (he : Function.Injective e) (a : α) : probOf p (fun ω => e (f ω)) (e a) = probOf p f a := by
  simp [probOf, he.eq_iff]

lemma probOf_comp_not_mem [DecidableEq α] {α' : Type*} [DecidableEq α'] {e : α → α'} {a' : α'}
    (ha : ∀ a, e a ≠ a') : probOf p (fun ω => e (f ω)) a' = 0 := by
  simp [probOf, ha]

/-- Entropy is invariant under an injective relabelling of the observable's values. -/
lemma entropyBits_comp_injective [Fintype α] [DecidableEq α] {α' : Type*} [Fintype α']
    [DecidableEq α'] {e : α → α'} (he : Function.Injective e) :
    entropyBits p (fun ω => e (f ω)) = entropyBits p f := by
  have h1 : ∑ a' : α', Real.negMulLog (probOf p (fun ω => e (f ω)) a')
      = ∑ a' ∈ Finset.image e Finset.univ,
          Real.negMulLog (probOf p (fun ω => e (f ω)) a') := by
    refine (Finset.sum_subset (Finset.subset_univ _) ?_).symm
    intro a' _ ha'
    have hne : ∀ a, e a ≠ a' := fun a hEq =>
      ha' (Finset.mem_image.2 ⟨a, Finset.mem_univ _, hEq⟩)
    rw [probOf_comp_not_mem (p := p) (f := f) hne]
    simp
  simp only [entropyBits, h1, Finset.sum_image he.injOn]
  simp only [probOf_comp_injective (p := p) (f := f) he]

/-- Entropy is invariant under a bijective relabelling of the observable's values. -/
lemma entropyBits_equiv [Fintype α] [DecidableEq α] {α' : Type*} [Fintype α'] [DecidableEq α']
    (e : α ≃ α') : entropyBits p (fun ω => e (f ω)) = entropyBits p f :=
  entropyBits_comp_injective e.injective

/-! ### Marginalization -/

lemma probOf_pair_swap [DecidableEq α] [DecidableEq β] (a : α) (b : β) :
    probOf p (fun ω => (f ω, g ω)) (a, b) = probOf p (fun ω => (g ω, f ω)) (b, a) := by
  simp only [probOf, Prod.ext_iff]
  exact Finset.sum_congr rfl fun ω _ => by
    by_cases h1 : f ω = a <;> by_cases h2 : g ω = b <;> simp [h1, h2]

lemma probOf_pair_assoc [DecidableEq α] [DecidableEq β] [DecidableEq γ] (a : α) (b : β) (c : γ) :
    probOf p (fun ω => ((f ω, g ω), h ω)) ((a, b), c)
      = probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) := by
  simp only [probOf, Prod.ext_iff]
  exact Finset.sum_congr rfl fun ω _ => by
    by_cases h1 : f ω = a <;> by_cases h2 : g ω = b <;> by_cases h3 : h ω = c <;>
      simp [h1, h2, h3]

/-- Summing the joint mass function over the second component recovers the first marginal. -/
lemma sum_probOf_pair_right [DecidableEq α] [Fintype β] [DecidableEq β] (a : α) :
    ∑ b, probOf p (fun ω => (f ω, g ω)) (a, b) = probOf p f a := by
  simp only [probOf, Prod.ext_iff]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun ω _ => ?_
  by_cases h1 : f ω = a
  · simp [h1]
  · simp [h1]

/-- Summing the joint mass function over the first component recovers the second marginal. -/
lemma sum_probOf_pair_left [Fintype α] [DecidableEq α] [DecidableEq β] (b : β) :
    ∑ a, probOf p (fun ω => (f ω, g ω)) (a, b) = probOf p g b := by
  simp only [probOf_pair_swap (p := p) (f := f) (g := g)]
  exact sum_probOf_pair_right (p := p) (f := g) (g := f) b

lemma probOf_le_probOf_fst [DecidableEq α] [Fintype β] [DecidableEq β]
    (hp : ∀ ω, 0 ≤ p ω) (a : α) (b : β) :
    probOf p (fun ω => (f ω, g ω)) (a, b) ≤ probOf p f a := by
  rw [← sum_probOf_pair_right (p := p) (f := f) (g := g) a]
  exact Finset.single_le_sum
    (f := fun b => probOf p (fun ω => (f ω, g ω)) (a, b))
    (fun b _ => probOf_nonneg hp _) (Finset.mem_univ b)

lemma probOf_le_probOf_snd [Fintype α] [DecidableEq α] [DecidableEq β]
    (hp : ∀ ω, 0 ≤ p ω) (a : α) (b : β) :
    probOf p (fun ω => (f ω, g ω)) (a, b) ≤ probOf p g b := by
  rw [← sum_probOf_pair_left (p := p) (f := f) (g := g) b]
  exact Finset.single_le_sum
    (f := fun a => probOf p (fun ω => (f ω, g ω)) (a, b))
    (fun a _ => probOf_nonneg hp _) (Finset.mem_univ a)

end Viridis.Run121

/- Engine-3 immutable source unit: Info.lean -/

/-!
# Mutual information, conditional mutual information and the symbiosis balance

Definitions follow the sealed paper exactly:

* `I(A;B) = H(A) + H(B) - H(A,B)`                              (paper Eq. (1))
* `I(A;B ∣ C) = H(A,C) + H(B,C) - H(C) - H(A,B,C)`             (paper Eq. (2))
* `B(Y;X₁,X₂) = I(Y;X₁,X₂) - I(Y;X₁) - I(Y;X₂)`                (paper Eq. (3))

The main result of this file is the chain-rule identity (paper Proposition 1).
-/

namespace Viridis.Run121

open Finset

variable {Ω : Type*} [Fintype Ω] {α β γ : Type*}
  [Fintype α] [DecidableEq α] [Fintype β] [DecidableEq β] [Fintype γ] [DecidableEq γ]

/-- Mutual information in bits, `I(A;B) = H(A) + H(B) - H(A,B)` (paper Eq. (1)). -/
noncomputable def mutualInfoBits (p : Ω → ℝ) (f : Ω → α) (g : Ω → β) : ℝ :=
  entropyBits p f + entropyBits p g - entropyBits p (fun ω => (f ω, g ω))

/-- Conditional mutual information in bits,
`I(A;B ∣ C) = H(A,C) + H(B,C) - H(C) - H(A,B,C)` (paper Eq. (2)). -/
noncomputable def condMutualInfoBits (p : Ω → ℝ) (f : Ω → α) (g : Ω → β) (h : Ω → γ) : ℝ :=
  entropyBits p (fun ω => (f ω, h ω)) + entropyBits p (fun ω => (g ω, h ω))
    - entropyBits p h - entropyBits p (fun ω => (f ω, g ω, h ω))

/-- The raw information-symbiosis balance
`B(Y;X₁,X₂) = I(Y;X₁,X₂) - I(Y;X₁) - I(Y;X₂)` (paper Eq. (3)). -/
noncomputable def balanceBits (p : Ω → ℝ) (Y : Ω → γ) (X1 : Ω → α) (X2 : Ω → β) : ℝ :=
  mutualInfoBits p Y (fun ω => (X1 ω, X2 ω)) - mutualInfoBits p Y X1 - mutualInfoBits p Y X2

/-- The cost-adjusted balance `B_c = B - c` of the paper's Section 2. -/
noncomputable def netBalanceBits (p : Ω → ℝ) (Y : Ω → γ) (X1 : Ω → α) (X2 : Ω → β) (c : ℝ) : ℝ :=
  balanceBits p Y X1 X2 - c

/-- The relabelling `(x₁, x₂, y) ↦ (y, x₁, x₂)`, used to identify the entropies of two
groupings of the same triple of observables. -/
def tripleRotate : α × β × γ ≃ γ × α × β where
  toFun x := (x.2.2, x.1, x.2.1)
  invFun x := (x.2.1, x.2.2, x.1)
  left_inv := by rintro ⟨a, b, c⟩; rfl
  right_inv := by rintro ⟨a, b, c⟩; rfl

variable {p : Ω → ℝ} {Y : Ω → γ} {X1 : Ω → α} {X2 : Ω → β}

lemma entropyBits_pair_comm (f : Ω → α) (g : Ω → β) :
    entropyBits p (fun ω => (f ω, g ω)) = entropyBits p (fun ω => (g ω, f ω)) := by
  simpa using entropyBits_equiv (p := p) (f := fun ω => (g ω, f ω)) (Equiv.prodComm β α)

lemma entropyBits_triple_rotate (f : Ω → α) (g : Ω → β) (k : Ω → γ) :
    entropyBits p (fun ω => (k ω, f ω, g ω)) = entropyBits p (fun ω => (f ω, g ω, k ω)) := by
  simpa [tripleRotate] using
    entropyBits_equiv (p := p) (f := fun ω => (f ω, g ω, k ω)) (tripleRotate (α := α) (β := β))

/-- **Paper Proposition 1 (information-symbiosis chain rule).**
For every finite joint distribution,
`B(Y;X₁,X₂) = I(X₁;X₂ ∣ Y) - I(X₁;X₂)`.

No hypothesis on `p` is required: with the paper's entropy-based definitions of `I` and
`I(· ; · ∣ ·)` the identity is an exact algebraic consequence of the fact that entropy does not
depend on how the observables are grouped or ordered. -/
theorem information_symbiosis_chain_rule (p : Ω → ℝ) (Y : Ω → γ) (X1 : Ω → α) (X2 : Ω → β) :
    balanceBits p Y X1 X2 = condMutualInfoBits p X1 X2 Y - mutualInfoBits p X1 X2 := by
  sorry

end Viridis.Run121

/- Engine-3 immutable source unit: Nonneg.lean -/

/-!
# Nonnegativity of mutual information

Gibbs' inequality for finite mass functions, and the consequence
`0 ≤ I(X₁;X₂)`, which is what turns the paper's Corollary 1 identity
`B = -I(X₁;X₂)` into the sign statement `B ≤ 0`.
-/

namespace Viridis.Run121

open Finset

/-- Gibbs' inequality in the form needed here: for a nonnegative family `r` and a nonnegative
reference family `s` whose total mass is at most that of `r`, and with `s i = 0 → r i = 0`,
one has `∑ r log s ≤ ∑ r log r`. -/
lemma gibbs {ι : Type*} [Fintype ι] (r s : ι → ℝ) (hr : ∀ i, 0 ≤ r i) (hs : ∀ i, 0 ≤ s i)
    (h0 : ∀ i, s i = 0 → r i = 0) (hle : ∑ i, s i ≤ ∑ i, r i) :
    ∑ i, r i * Real.log (s i) ≤ ∑ i, r i * Real.log (r i) := by
  have key : ∀ i, r i * Real.log (s i) - r i * Real.log (r i) ≤ s i - r i := by
    intro i
    rcases eq_or_lt_of_le (hr i) with hri | hri
    · simp [← hri, hs i]
    · have hsi : 0 < s i := lt_of_le_of_ne (hs i) (fun hE => absurd (h0 i hE.symm) (ne_of_gt hri))
      have hlog : Real.log (s i / r i) ≤ s i / r i - 1 :=
        Real.log_le_sub_one_of_pos (div_pos hsi hri)
      have hmul := mul_le_mul_of_nonneg_left hlog (le_of_lt hri)
      rw [Real.log_div (ne_of_gt hsi) (ne_of_gt hri)] at hmul
      calc r i * Real.log (s i) - r i * Real.log (r i)
          = r i * (Real.log (s i) - Real.log (r i)) := by ring
        _ ≤ r i * (s i / r i - 1) := hmul
        _ = s i - r i := by field_simp
  have hsum : ∑ i, (r i * Real.log (s i) - r i * Real.log (r i)) ≤ ∑ i, (s i - r i) :=
    Finset.sum_le_sum (fun i _ => key i)
  rw [Finset.sum_sub_distrib, Finset.sum_sub_distrib] at hsum
  linarith

lemma sum_negMulLog_eq {ι : Type*} [Fintype ι] (q : ι → ℝ) :
    ∑ i, Real.negMulLog (q i) = -∑ i, q i * Real.log (q i) := by
  rw [← Finset.sum_neg_distrib]
  exact Finset.sum_congr rfl fun i _ => by simp [Real.negMulLog]

variable {Ω : Type*} [Fintype Ω] {α β : Type*}
  [Fintype α] [DecidableEq α] [Fintype β] [DecidableEq β]

/-- Mutual information (in bits) of two finite observables is nonnegative. -/
theorem mutualInfoBits_nonneg {p : Ω → ℝ} (hp : ∀ ω, 0 ≤ p ω) (hsum : ∑ ω, p ω = 1)
    (f : Ω → α) (g : Ω → β) : 0 ≤ mutualInfoBits p f g := by
  set q1 := probOf p f with hq1
  set q2 := probOf p g with hq2
  set pj := probOf p (fun ω => (f ω, g ω)) with hpj
  have hm1 : ∀ a, ∑ b, pj (a, b) = q1 a := fun a =>
    sum_probOf_pair_right (p := p) (f := f) (g := g) a
  have hm2 : ∀ b, ∑ a, pj (a, b) = q2 b := fun b =>
    sum_probOf_pair_left (p := p) (f := f) (g := g) b
  have hpjnn : ∀ x : α × β, 0 ≤ pj x := fun x => probOf_nonneg hp x
  have hq1nn : ∀ a, 0 ≤ q1 a := fun a => probOf_nonneg hp a
  have hq2nn : ∀ b, 0 ≤ q2 b := fun b => probOf_nonneg hp b
  have hA : ∑ a, q1 a * Real.log (q1 a) = ∑ x : α × β, pj x * Real.log (q1 x.1) := by
    rw [Fintype.sum_prod_type]
    refine Finset.sum_congr rfl fun a _ => ?_
    rw [← hm1 a, Finset.sum_mul]
    simp [hm1]
  have hB : ∑ b, q2 b * Real.log (q2 b) = ∑ x : α × β, pj x * Real.log (q2 x.2) := by
    rw [Fintype.sum_prod_type, Finset.sum_comm]
    refine Finset.sum_congr rfl fun b _ => ?_
    rw [← hm2 b, Finset.sum_mul]
    simp [hm2]
  have hprod : ∀ x : α × β, pj x * Real.log (q1 x.1 * q2 x.2)
      = pj x * Real.log (q1 x.1) + pj x * Real.log (q2 x.2) := by
    rintro ⟨a, b⟩
    rcases eq_or_lt_of_le (hpjnn (a, b)) with h0 | hpos
    · simp [← h0]
    · have h1 : 0 < q1 a := lt_of_lt_of_le hpos (probOf_le_probOf_fst hp a b)
      have h2 : 0 < q2 b := lt_of_lt_of_le hpos (probOf_le_probOf_snd hp a b)
      rw [Real.log_mul (ne_of_gt h1) (ne_of_gt h2)]; ring
  have hsprod : ∑ x : α × β, q1 x.1 * q2 x.2 = 1 := by
    rw [Fintype.sum_prod_type]
    simp only [← Finset.mul_sum]
    rw [← Finset.sum_mul, hq1, hq2, sum_probOf, sum_probOf, hsum]
    ring
  have hpjsum : ∑ x : α × β, pj x = 1 := by rw [hpj, sum_probOf, hsum]
  have hgibbs := gibbs (ι := α × β) pj (fun x => q1 x.1 * q2 x.2) hpjnn
    (fun x => mul_nonneg (hq1nn x.1) (hq2nn x.2))
    (by
      rintro ⟨a, b⟩ hzero
      rcases mul_eq_zero.1 hzero with h1 | h2
      · exact le_antisymm (h1 ▸ probOf_le_probOf_fst hp a b) (hpjnn (a, b))
      · exact le_antisymm (h2 ▸ probOf_le_probOf_snd hp a b) (hpjnn (a, b)))
    (by rw [hsprod, hpjsum])
  simp only [hprod, Finset.sum_add_distrib] at hgibbs
  rw [← hA, ← hB] at hgibbs
  have hnum : 0 ≤ (∑ a, Real.negMulLog (q1 a)) + (∑ b, Real.negMulLog (q2 b))
      - ∑ x : α × β, Real.negMulLog (pj x) := by
    rw [sum_negMulLog_eq, sum_negMulLog_eq, sum_negMulLog_eq]
    linarith
  simp only [mutualInfoBits, entropyBits, ← sub_div, ← add_div]
  exact div_nonneg hnum (le_of_lt (Real.log_pos one_lt_two))

end Viridis.Run121

/- Engine-3 immutable source unit: CondIndep.lean -/

/-!
# Conditional independence and vanishing conditional mutual information

`CondIndepGiven p f g h` is the (division-free) statement that `f` and `g` are conditionally
independent given `h`:  `P(h = c) · P(f = a, g = b, h = c) = P(f = a, h = c) · P(g = b, h = c)`.

The main result is `condMutualInfoBits_eq_zero_of_condIndep`, which is the analytic content of
the paper's Corollary 1.
-/

namespace Viridis.Run121

open Finset

variable {Ω : Type*} [Fintype Ω] {α β γ : Type*}
  [Fintype α] [DecidableEq α] [Fintype β] [DecidableEq β] [Fintype γ] [DecidableEq γ]
variable {p : Ω → ℝ} {f : Ω → α} {g : Ω → β} {h : Ω → γ}

/-- Conditional independence of the observables `f` and `g` given `h`, written multiplicatively
so that no division and no positivity assumption on `P(h = c)` is needed. -/
def CondIndepGiven (p : Ω → ℝ) (f : Ω → α) (g : Ω → β) (h : Ω → γ) : Prop :=
  ∀ a b c, probOf p h c * probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
    = probOf p (fun ω => (f ω, h ω)) (a, c) * probOf p (fun ω => (g ω, h ω)) (b, c)

/-! ### Relabelings and marginals of a triple -/

/-- `((a,c),b) ↦ (a,b,c)`. -/
def tripleToFH : (α × γ) × β ≃ α × β × γ where
  toFun x := (x.1.1, x.2, x.1.2)
  invFun x := ((x.1, x.2.2), x.2.1)
  left_inv := by rintro ⟨⟨a, c⟩, b⟩; rfl
  right_inv := by rintro ⟨a, b, c⟩; rfl

/-- `((b,c),a) ↦ (a,b,c)`. -/
def tripleToGH : (β × γ) × α ≃ α × β × γ where
  toFun x := (x.2, x.1.1, x.1.2)
  invFun x := ((x.2.1, x.2.2), x.1)
  left_inv := by rintro ⟨⟨b, c⟩, a⟩; rfl
  right_inv := by rintro ⟨a, b, c⟩; rfl

/-- `(c,(a,b)) ↦ (a,b,c)`. -/
def tripleToH : γ × (α × β) ≃ α × β × γ where
  toFun x := (x.2.1, x.2.2, x.1)
  invFun x := (x.2.2, x.1, x.2.1)
  left_inv := by rintro ⟨c, a, b⟩; rfl
  right_inv := by rintro ⟨a, b, c⟩; rfl

omit [Fintype α] [Fintype β] [Fintype γ] in
lemma probOf_triple_fh (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      = probOf p (fun ω => ((f ω, h ω), g ω)) ((a, c), b) := by
  have := probOf_comp_injective (p := p) (f := fun ω => ((f ω, h ω), g ω))
    (e := (tripleToFH : (α × γ) × β ≃ α × β × γ)) (Equiv.injective _) ((a, c), b)
  simpa [tripleToFH] using this

omit [Fintype α] [Fintype β] [Fintype γ] in
lemma probOf_triple_gh (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      = probOf p (fun ω => ((g ω, h ω), f ω)) ((b, c), a) := by
  have := probOf_comp_injective (p := p) (f := fun ω => ((g ω, h ω), f ω))
    (e := (tripleToGH : (β × γ) × α ≃ α × β × γ)) (Equiv.injective _) ((b, c), a)
  simpa [tripleToGH] using this

omit [Fintype α] [Fintype β] [Fintype γ] in
lemma probOf_triple_h (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      = probOf p (fun ω => (h ω, f ω, g ω)) (c, a, b) := by
  have := probOf_comp_injective (p := p) (f := fun ω => (h ω, (f ω, g ω)))
    (e := (tripleToH : γ × (α × β) ≃ α × β × γ)) (Equiv.injective _) (c, (a, b))
  simpa [tripleToH] using this

omit [Fintype α] [Fintype γ] in
lemma sum_probOf_triple_mid (a : α) (c : γ) :
    ∑ b, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      = probOf p (fun ω => (f ω, h ω)) (a, c) := by
  simp only [probOf_triple_fh]
  exact sum_probOf_pair_right (p := p) (f := fun ω => (f ω, h ω)) (g := g) (a, c)

omit [Fintype β] [Fintype γ] in
lemma sum_probOf_triple_first (b : β) (c : γ) :
    ∑ a, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      = probOf p (fun ω => (g ω, h ω)) (b, c) := by
  simp only [probOf_triple_gh]
  exact sum_probOf_pair_right (p := p) (f := fun ω => (g ω, h ω)) (g := f) (b, c)

omit [Fintype γ] in
lemma sum_probOf_triple_pair (c : γ) :
    ∑ a, ∑ b, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) = probOf p h c := by
  have h1 : ∑ x : α × β, probOf p (fun ω => (h ω, f ω, g ω)) (c, x) = probOf p h c :=
    sum_probOf_pair_right (p := p) (f := h) (g := fun ω => (f ω, g ω)) c
  rw [Fintype.sum_prod_type] at h1
  rw [← h1]
  exact Finset.sum_congr rfl fun a _ => Finset.sum_congr rfl fun b _ => probOf_triple_h a b c

/-! ### Collapsing sums over the triple -/

lemma sum_triple_collapse_fh (F : α × γ → ℝ) :
    ∑ x : α × β × γ, probOf p (fun ω => (f ω, g ω, h ω)) x * F (x.1, x.2.2)
      = ∑ y : α × γ, probOf p (fun ω => (f ω, h ω)) y * F y := by
  simp only [Fintype.sum_prod_type]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun c _ => ?_
  rw [← Finset.sum_mul, sum_probOf_triple_mid]

lemma sum_triple_collapse_gh (G : β × γ → ℝ) :
    ∑ x : α × β × γ, probOf p (fun ω => (f ω, g ω, h ω)) x * G (x.2.1, x.2.2)
      = ∑ y : β × γ, probOf p (fun ω => (g ω, h ω)) y * G y := by
  simp only [Fintype.sum_prod_type]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun b _ => ?_
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun c _ => ?_
  rw [← Finset.sum_mul, sum_probOf_triple_first]

lemma sum_triple_collapse_h (K : γ → ℝ) :
    ∑ x : α × β × γ, probOf p (fun ω => (f ω, g ω, h ω)) x * K x.2.2
      = ∑ c, probOf p h c * K c := by
  simp only [Fintype.sum_prod_type]
  calc ∑ a, ∑ b, ∑ c, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) * K c
      = ∑ a, ∑ c, ∑ b, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) * K c :=
        Finset.sum_congr rfl fun a _ => Finset.sum_comm
    _ = ∑ c, ∑ a, ∑ b, probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) * K c :=
        Finset.sum_comm
    _ = ∑ c, probOf p h c * K c := by
        refine Finset.sum_congr rfl fun c _ => ?_
        rw [← sum_probOf_triple_pair (p := p) (f := f) (g := g) (h := h) c, Finset.sum_mul]
        exact Finset.sum_congr rfl fun a _ => (Finset.sum_mul _ _ _).symm

/-! ### Domination bounds -/

omit [Fintype α] [Fintype γ] in
lemma probOf_triple_le_fh (hp : ∀ ω, 0 ≤ p ω) (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) ≤ probOf p (fun ω => (f ω, h ω)) (a, c) := by
  rw [← sum_probOf_triple_mid (p := p) (f := f) (g := g) (h := h) a c]
  exact Finset.single_le_sum
    (f := fun b => probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c))
    (fun b _ => probOf_nonneg hp _) (Finset.mem_univ b)

omit [Fintype β] [Fintype γ] in
lemma probOf_triple_le_gh (hp : ∀ ω, 0 ≤ p ω) (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) ≤ probOf p (fun ω => (g ω, h ω)) (b, c) := by
  rw [← sum_probOf_triple_first (p := p) (f := f) (g := g) (h := h) b c]
  exact Finset.single_le_sum
    (f := fun a => probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c))
    (fun a _ => probOf_nonneg hp _) (Finset.mem_univ a)

omit [Fintype γ] in
lemma probOf_triple_le_h (hp : ∀ ω, 0 ≤ p ω) (a : α) (b : β) (c : γ) :
    probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c) ≤ probOf p h c := by
  rw [← sum_probOf_triple_pair (p := p) (f := f) (g := g) (h := h) c]
  have inner : probOf p (fun ω => (f ω, g ω, h ω)) (a, b, c)
      ≤ ∑ b', probOf p (fun ω => (f ω, g ω, h ω)) (a, b', c) :=
    Finset.single_le_sum
      (f := fun b' => probOf p (fun ω => (f ω, g ω, h ω)) (a, b', c))
      (fun b' _ => probOf_nonneg hp _) (Finset.mem_univ b)
  refine inner.trans (Finset.single_le_sum
    (f := fun a' => ∑ b', probOf p (fun ω => (f ω, g ω, h ω)) (a', b', c))
    (fun a' _ => Finset.sum_nonneg fun b' _ => probOf_nonneg hp _) (Finset.mem_univ a))

/-! ### Vanishing conditional mutual information -/

/-- If `f` and `g` are conditionally independent given `h`, the conditional mutual information
`I(f;g ∣ h)` vanishes. -/
theorem condMutualInfoBits_eq_zero_of_condIndep (hp : ∀ ω, 0 ≤ p ω)
    (hci : CondIndepGiven p f g h) : condMutualInfoBits p f g h = 0 := by
  set p3 := probOf p (fun ω => (f ω, g ω, h ω)) with hp3
  set pfh := probOf p (fun ω => (f ω, h ω)) with hpfh
  set pgh := probOf p (fun ω => (g ω, h ω)) with hpgh
  set ph := probOf p h with hph
  have hlog : ∀ x : α × β × γ, p3 x * Real.log (p3 x)
      = p3 x * Real.log (pfh (x.1, x.2.2)) + p3 x * Real.log (pgh (x.2.1, x.2.2))
        - p3 x * Real.log (ph x.2.2) := by
    rintro ⟨a, b, c⟩
    rcases eq_or_lt_of_le (probOf_nonneg (f := fun ω => (f ω, g ω, h ω)) hp (a, b, c)) with
      h0 | hpos
    · simp [hp3, ← h0]
    · have h1 : 0 < pfh (a, c) := lt_of_lt_of_le hpos (probOf_triple_le_fh hp a b c)
      have h2 : 0 < pgh (b, c) := lt_of_lt_of_le hpos (probOf_triple_le_gh hp a b c)
      have h3 : 0 < ph c := lt_of_lt_of_le hpos (probOf_triple_le_h hp a b c)
      have hmul : Real.log (ph c) + Real.log (p3 (a, b, c))
          = Real.log (pfh (a, c)) + Real.log (pgh (b, c)) := by
        rw [← Real.log_mul (ne_of_gt h3) (ne_of_gt hpos), ← Real.log_mul (ne_of_gt h1) (ne_of_gt h2),
          hci a b c]
      have : Real.log (p3 (a, b, c))
          = Real.log (pfh (a, c)) + Real.log (pgh (b, c)) - Real.log (ph c) := by linarith
      rw [this]; ring
  have hsplit : ∑ x : α × β × γ, p3 x * Real.log (p3 x)
      = (∑ y : α × γ, pfh y * Real.log (pfh y)) + (∑ y : β × γ, pgh y * Real.log (pgh y))
        - ∑ c, ph c * Real.log (ph c) := by
    have e1 := sum_triple_collapse_fh (p := p) (f := f) (g := g) (h := h)
      (fun y => Real.log (pfh y))
    have e2 := sum_triple_collapse_gh (p := p) (f := f) (g := g) (h := h)
      (fun y => Real.log (pgh y))
    have e3 := sum_triple_collapse_h (p := p) (f := f) (g := g) (h := h)
      (fun c => Real.log (ph c))
    calc ∑ x : α × β × γ, p3 x * Real.log (p3 x)
        = ∑ x : α × β × γ, (p3 x * Real.log (pfh (x.1, x.2.2))
            + p3 x * Real.log (pgh (x.2.1, x.2.2)) - p3 x * Real.log (ph x.2.2)) :=
          Finset.sum_congr rfl fun x _ => hlog x
      _ = (∑ x : α × β × γ, p3 x * Real.log (pfh (x.1, x.2.2)))
            + (∑ x : α × β × γ, p3 x * Real.log (pgh (x.2.1, x.2.2)))
            - ∑ x : α × β × γ, p3 x * Real.log (ph x.2.2) := by
          rw [Finset.sum_sub_distrib, Finset.sum_add_distrib]
      _ = (∑ y : α × γ, pfh y * Real.log (pfh y)) + (∑ y : β × γ, pgh y * Real.log (pgh y))
            - ∑ c, ph c * Real.log (ph c) := by rw [e1, e2, e3]
  have hnum : (∑ y : α × γ, Real.negMulLog (pfh y)) + (∑ y : β × γ, Real.negMulLog (pgh y))
      - (∑ c, Real.negMulLog (ph c)) - ∑ x : α × β × γ, Real.negMulLog (p3 x) = 0 := by
    rw [sum_negMulLog_eq, sum_negMulLog_eq, sum_negMulLog_eq, sum_negMulLog_eq, hsplit]
    ring
  simp only [condMutualInfoBits, entropyBits, ← sub_div, ← add_div]
  rw [hnum, zero_div]

end Viridis.Run121

/- Engine-3 immutable source unit: Controls.lean -/

/-!
# The three deterministic controls of the paper's control table

* exact duplication `X₁ = X₂ = Y`, fair binary `Y`:            balance `-1` bit
* `Y = X₁ ⊕ X₂` with independent fair input bits:              balance `+1` bit
* `Y = (X₁, X₂)` with independent fair bits:                   balance `0` bit
-/

namespace Viridis.Run121

open Finset

/-! ### Numerical helpers -/

lemma negMulLog_half : Real.negMulLog ((1 : ℝ) / 2) = (1 / 2) * Real.log 2 := by
  rw [Real.negMulLog, show ((1 : ℝ) / 2) = (2 : ℝ)⁻¹ by norm_num, Real.log_inv]; ring

lemma negMulLog_quarter : Real.negMulLog ((1 : ℝ) / 4) = (1 / 2) * Real.log 2 := by
  rw [Real.negMulLog, show ((1 : ℝ) / 4) = ((2 : ℝ) ^ 2)⁻¹ by norm_num, Real.log_inv, Real.log_pow]
  push_cast; ring

/-! ### The fair binary sample space (duplication control) -/

/-- A fair bit: the uniform mass function on `Bool`. -/
noncomputable def pdup : Bool → ℝ := fun _ => 1 / 2

lemma pdup_nonneg : ∀ ω, 0 ≤ pdup ω := by intro ω; norm_num [pdup]

lemma pdup_sum : ∑ ω, pdup ω = 1 := by norm_num [pdup]

lemma entropy_pdup_single : entropyBits pdup (fun ω => ω) = 1 := by
  have hq : ∀ a : Bool, probOf pdup (fun ω => ω) a = 1 / 2 := by
    intro a; cases a <;> norm_num [probOf, pdup]
  simp only [entropyBits, hq, Fintype.sum_bool, negMulLog_half]
  field_simp
  norm_num

lemma entropy_pdup_pair : entropyBits pdup (fun ω => (ω, ω)) = 1 := by
  have hq : ∀ x : Bool × Bool, probOf pdup (fun ω => (ω, ω)) x =
      if x.1 = x.2 then 1 / 2 else 0 := by
    rintro ⟨a, b⟩; cases a <;> cases b <;> norm_num [probOf, pdup]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_half]
  field_simp
  norm_num

lemma entropy_pdup_triple : entropyBits pdup (fun ω => (ω, ω, ω)) = 1 := by
  have hq : ∀ x : Bool × Bool × Bool, probOf pdup (fun ω => (ω, ω, ω)) x =
      if x.1 = x.2.1 ∧ x.1 = x.2.2 then 1 / 2 else 0 := by
    rintro ⟨a, b, c⟩; cases a <;> cases b <;> cases c <;> norm_num [probOf, pdup]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_half]
  field_simp
  norm_num

/-- **Duplication control.** With `Y = X₁ = X₂` a fair bit, the balance is `-1` bit. -/
theorem balance_duplicate : balanceBits pdup (fun ω => ω) (fun ω => ω) (fun ω => ω) = -1 := by
  simp only [balanceBits, mutualInfoBits, entropy_pdup_single, entropy_pdup_pair,
    entropy_pdup_triple]
  norm_num

/-! ### Two independent fair bits (XOR and unique-bit controls) -/

/-- Two independent fair bits: the uniform mass function on `Bool × Bool`. -/
noncomputable def pfour : Bool × Bool → ℝ := fun _ => 1 / 4

lemma pfour_nonneg : ∀ ω, 0 ≤ pfour ω := by intro ω; norm_num [pfour]

lemma pfour_sum : ∑ ω, pfour ω = 1 := by
  norm_num [pfour, Fintype.sum_prod_type]

lemma entropy_pfour_fst : entropyBits pfour (fun ω => ω.1) = 1 := by
  have hq : ∀ a : Bool, probOf pfour (fun ω => ω.1) a = 1 / 2 := by
    intro a; cases a <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_bool, negMulLog_half]
  field_simp
  norm_num

lemma entropy_pfour_snd : entropyBits pfour (fun ω => ω.2) = 1 := by
  have hq : ∀ a : Bool, probOf pfour (fun ω => ω.2) a = 1 / 2 := by
    intro a; cases a <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_bool, negMulLog_half]
  field_simp
  norm_num

lemma entropy_pfour_pair : entropyBits pfour (fun ω => (ω.1, ω.2)) = 2 := by
  have hq : ∀ x : Bool × Bool, probOf pfour (fun ω => (ω.1, ω.2)) x = 1 / 4 := by
    rintro ⟨a, b⟩; cases a <;> cases b <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool, negMulLog_quarter]
  field_simp
  norm_num

lemma entropy_pfour_xor : entropyBits pfour (fun ω => xor ω.1 ω.2) = 1 := by
  have hq : ∀ a : Bool, probOf pfour (fun ω => xor ω.1 ω.2) a = 1 / 2 := by
    intro a; cases a <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_bool, negMulLog_half]
  field_simp
  norm_num

lemma entropy_pfour_xor_fst : entropyBits pfour (fun ω => (xor ω.1 ω.2, ω.1)) = 2 := by
  have hq : ∀ x : Bool × Bool, probOf pfour (fun ω => (xor ω.1 ω.2, ω.1)) x = 1 / 4 := by
    rintro ⟨y, a⟩; cases y <;> cases a <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool, negMulLog_quarter]
  field_simp
  norm_num

lemma entropy_pfour_xor_snd : entropyBits pfour (fun ω => (xor ω.1 ω.2, ω.2)) = 2 := by
  have hq : ∀ x : Bool × Bool, probOf pfour (fun ω => (xor ω.1 ω.2, ω.2)) x = 1 / 4 := by
    rintro ⟨y, b⟩; cases y <;> cases b <;> norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool, negMulLog_quarter]
  field_simp
  norm_num

lemma entropy_pfour_xor_triple : entropyBits pfour (fun ω => (xor ω.1 ω.2, ω.1, ω.2)) = 2 := by
  have hq : ∀ x : Bool × Bool × Bool, probOf pfour (fun ω => (xor ω.1 ω.2, ω.1, ω.2)) x =
      if x.1 = xor x.2.1 x.2.2 then 1 / 4 else 0 := by
    rintro ⟨y, a, b⟩; cases y <;> cases a <;> cases b <;>
      norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_quarter]
  field_simp
  norm_num

/-- **XOR control.** With independent fair inputs and `Y = X₁ ⊕ X₂`, the balance is `+1` bit. -/
theorem balance_xor :
    balanceBits pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1) (fun ω => ω.2) = 1 := by
  simp only [balanceBits, mutualInfoBits, entropy_pfour_fst, entropy_pfour_snd,
    entropy_pfour_pair, entropy_pfour_xor, entropy_pfour_xor_fst, entropy_pfour_xor_snd,
    entropy_pfour_xor_triple]
  norm_num

lemma entropy_pfour_id_fst : entropyBits pfour (fun ω => (ω, ω.1)) = 2 := by
  have hq : ∀ x : (Bool × Bool) × Bool, probOf pfour (fun ω => (ω, ω.1)) x =
      if x.1.1 = x.2 then 1 / 4 else 0 := by
    rintro ⟨⟨a, b⟩, c⟩; cases a <;> cases b <;> cases c <;>
      norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_quarter]
  field_simp
  norm_num

lemma entropy_pfour_id_snd : entropyBits pfour (fun ω => (ω, ω.2)) = 2 := by
  have hq : ∀ x : (Bool × Bool) × Bool, probOf pfour (fun ω => (ω, ω.2)) x =
      if x.1.2 = x.2 then 1 / 4 else 0 := by
    rintro ⟨⟨a, b⟩, c⟩; cases a <;> cases b <;> cases c <;>
      norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_quarter]
  field_simp
  norm_num

lemma entropy_pfour_id_triple : entropyBits pfour (fun ω => (ω, ω.1, ω.2)) = 2 := by
  have hq : ∀ x : (Bool × Bool) × Bool × Bool, probOf pfour (fun ω => (ω, ω.1, ω.2)) x =
      if x.1.1 = x.2.1 ∧ x.1.2 = x.2.2 then 1 / 4 else 0 := by
    rintro ⟨⟨a, b⟩, c, d⟩; cases a <;> cases b <;> cases c <;> cases d <;>
      norm_num [probOf, pfour, Fintype.sum_prod_type]
  simp only [entropyBits, hq, Fintype.sum_prod_type, Fintype.sum_bool]
  norm_num [negMulLog_quarter]
  field_simp
  norm_num

/-- **Complementary unique-bit control.** With independent fair bits and `Y = (X₁, X₂)`,
the balance is `0` bit. -/
theorem balance_unique_bits :
    balanceBits pfour (fun ω => ω) (fun ω => ω.1) (fun ω => ω.2) = 0 := by
  simp only [balanceBits, mutualInfoBits, entropy_pfour_fst, entropy_pfour_snd,
    entropy_pfour_pair, entropy_pfour_id_fst, entropy_pfour_id_snd,
    entropy_pfour_id_triple]
  norm_num

end Viridis.Run121

/- Engine-3 immutable source unit: Targets.lean -/

/-!
# The four frozen formal targets of Run-121

* `information_symbiosis_chain_rule`            (C1, paper Proposition 1) — proved in `Info.lean`
* `conditional_independence_no_positive_balance` (C2, paper Corollary 1)
* `net_symbiosis_cost_criterion`                 (C3, paper Corollary 2)
* `duplicate_and_xor_extremes`                   (C4, paper control table)

Each target is followed by an explicit non-vacuity witness: a concrete finite joint
distribution satisfying every hypothesis, for which the conclusion is not degenerate.
-/

namespace Viridis.Run121

open Finset

variable {Ω : Type*} [Fintype Ω] {α β γ : Type*}
  [Fintype α] [DecidableEq α] [Fintype β] [DecidableEq β] [Fintype γ] [DecidableEq γ]

/-! ## C2 — common-cause no-positive-balance (paper Corollary 1) -/

/-- **Paper Corollary 1.**  If `X₁ ⟂ X₂ ∣ Y`, then `B = -I(X₁;X₂) ≤ 0`.

`p` is assumed to be a mass function (nonnegative, total mass one); conditional independence is
`CondIndepGiven p X₁ X₂ Y`, i.e.
`P(Y=y)·P(X₁=x₁,X₂=x₂,Y=y) = P(X₁=x₁,Y=y)·P(X₂=x₂,Y=y)` for all values. -/
theorem conditional_independence_no_positive_balance {p : Ω → ℝ} (hp : ∀ ω, 0 ≤ p ω)
    (hsum : ∑ ω, p ω = 1) (Y : Ω → γ) (X1 : Ω → α) (X2 : Ω → β)
    (hci : CondIndepGiven p X1 X2 Y) :
    balanceBits p Y X1 X2 = -mutualInfoBits p X1 X2 ∧ balanceBits p Y X1 X2 ≤ 0 := by
  sorry

/-! ## C3 — cost-aware criterion (paper Corollary 2) -/

/-- **Paper Corollary 2.**  For a bit-equivalent coordination cost `c ≥ 0`,
`B_c = B - c > 0` holds exactly when `I(X₁;X₂ ∣ Y) > I(X₁;X₂) + c`.

The hypothesis `0 ≤ c` is the paper's standing assumption on the cost; it is retained here
even though the equivalence in fact holds for every real `c`. -/
theorem net_symbiosis_cost_criterion (p : Ω → ℝ) (Y : Ω → γ) (X1 : Ω → α) (X2 : Ω → β)
    (c : ℝ) (hc : 0 ≤ c) :
    0 < netBalanceBits p Y X1 X2 c ↔
      mutualInfoBits p X1 X2 + c < condMutualInfoBits p X1 X2 Y := by
  sorry

/-! ## C4 — the extremes of the control table -/

/-- **Paper control table.**  Fair-binary duplication, XOR and complementary unique bits have
balances `-1`, `+1` and `0` bit respectively. -/
theorem duplicate_and_xor_extremes :
    balanceBits pdup (fun ω => ω) (fun ω => ω) (fun ω => ω) = -1
      ∧ balanceBits pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1) (fun ω => ω.2) = 1
      ∧ balanceBits pfour (fun ω => ω) (fun ω => ω.1) (fun ω => ω.2) = 0 := by
  sorry

/-! ## Non-vacuity witnesses -/

/-- The uniform mass functions used by the controls really are mass functions. -/
theorem control_distributions_are_mass_functions :
    (∀ ω, 0 ≤ pdup ω) ∧ (∑ ω, pdup ω = 1) ∧ (∀ ω, 0 ≤ pfour ω) ∧ (∑ ω, pfour ω = 1) :=
  ⟨pdup_nonneg, pdup_sum, pfour_nonneg, pfour_sum⟩

/-- **Non-vacuity for C1.**  On the fair XOR control the chain rule relates two quantities that
are both nonzero: the balance equals `+1` bit and so does `I(X₁;X₂ ∣ Y) - I(X₁;X₂)`. -/
theorem chain_rule_nonvacuous :
    balanceBits pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1) (fun ω => ω.2) = 1
      ∧ condMutualInfoBits pfour (fun ω => ω.1) (fun ω => ω.2) (fun ω => xor ω.1 ω.2)
          - mutualInfoBits pfour (fun ω => ω.1) (fun ω => ω.2) = 1 := by
  refine ⟨balance_xor, ?_⟩
  rw [← information_symbiosis_chain_rule pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1)
    (fun ω => ω.2)]
  exact balance_xor

/-- In the duplication control the two sources are conditionally independent given the target
(trivially: each of them is the target).  This is the hypothesis of C2. -/
theorem condIndep_duplicate :
    CondIndepGiven pdup (fun ω => ω) (fun ω => ω) (fun ω => ω) := by
  intro a b c
  cases a <;> cases b <;> cases c <;> norm_num [probOf, pdup]

/-- The mutual information between the two (identical) sources of the duplication control
is one bit. -/
theorem mutualInfo_duplicate : mutualInfoBits pdup (fun ω => ω) (fun ω => ω) = 1 := by
  simp only [mutualInfoBits, entropy_pdup_single, entropy_pdup_pair]
  norm_num

/-- **Non-vacuity for C2.**  The duplication control satisfies every hypothesis of C2
(mass function, conditional independence) and its conclusion is strict: the balance equals
`-I(X₁;X₂) = -1 < 0`, so the corollary is not vacuous and not merely `B ≤ 0` by triviality. -/
theorem conditional_independence_nonvacuous :
    CondIndepGiven pdup (fun ω => ω) (fun ω => ω) (fun ω => ω)
      ∧ balanceBits pdup (fun ω => ω) (fun ω => ω) (fun ω => ω)
          = -mutualInfoBits pdup (fun ω => ω) (fun ω => ω)
      ∧ balanceBits pdup (fun ω => ω) (fun ω => ω) (fun ω => ω) < 0 := by
  refine ⟨condIndep_duplicate, ?_, ?_⟩
  · exact (conditional_independence_no_positive_balance pdup_nonneg pdup_sum
      (fun ω => ω) (fun ω => ω) (fun ω => ω) condIndep_duplicate).1
  · rw [balance_duplicate]; norm_num

/-- **Non-vacuity for C3.**  On the fair XOR control (balance `+1` bit) both directions of the
cost criterion are realized: a cost of `1/2` bit leaves a strictly positive net balance, while a
cost of `2` bits does not. -/
theorem net_symbiosis_cost_nonvacuous :
    0 < netBalanceBits pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1) (fun ω => ω.2) (1 / 2)
      ∧ ¬ (0 < netBalanceBits pfour (fun ω => xor ω.1 ω.2) (fun ω => ω.1) (fun ω => ω.2) 2) := by
  constructor
  · rw [netBalanceBits, balance_xor]; norm_num
  · rw [netBalanceBits, balance_xor]; norm_num

/-- **Non-vacuity for C4.**  The three control balances are pairwise distinct, so the control
table separates redundancy, additivity and joint-only information. -/
theorem control_balances_distinct :
    (-1 : ℝ) ≠ 1 ∧ (-1 : ℝ) ≠ 0 ∧ (1 : ℝ) ≠ 0 := by
  norm_num

end Viridis.Run121
