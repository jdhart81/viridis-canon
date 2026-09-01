/- Engine-3 immutable source unit: Model.lean -/
import Mathlib.Data.Finset.Card
import Mathlib.Data.Finset.Lattice.Lemmas
import Mathlib.Data.Matrix.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Order.Filter.Basic
import Mathlib.Topology.Instances.Real.Lemmas
import Mathlib.Tactic.Ext
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

/-!
# Run-120 "Conjunctive Audit Stewardship": the model

This file fixes the model of Section 3 of the sealed paper
(`SEALED_paper.tex`, Run-120, *The Conjunctive Audit Stewardship Theorem*).

Paper text being formalized:

* `E = {1,…,n}` is a set of evidence components.  Here `E` is an arbitrary
  type `ι` of components (all statements only ever refer to finitely many of
  them, through `Finset`s), so no loss of generality is incurred.
* Component `i` has a modeled current validity probability `p i ∈ (0,1]`.
  This is carried as explicit hypotheses `0 < p i` and `p i ≤ 1` on each
  theorem that needs it, rather than as a bundled subtype.
* Components are independent, and a perfect audit of `i` resets its
  probability to `1` and changes nothing else.  These two modeling
  assumptions are *not* extra Lean hypotheses: they are exactly what is
  encoded by the definition of `claimValue` below, which is equation (1) of
  the paper, `r_C(S) = ∏_{i ∈ C \ S} p i`.
* A claim `C ⊆ E` is conjunctive with post-audit credibility `r_C(S)`.
* A finite claim family `𝒞` with nonnegative weights `w_C` has portfolio
  value `F(S) = ∑_{C ∈ 𝒞} w_C r_C(S)` (equation (2)).  We index the family
  by a `Finset` of an index type so that repeated claims are allowed.
* Audits have equal cost, so a budget of `k` audits means `|S| ≤ k`.  Equal
  costs are again encoded in the statements (a cardinality constraint on the
  audited set) rather than as a hypothesis.
-/

namespace Viridis.Run120

open Finset

variable {ι : Type*} [DecidableEq ι]

/-- Equation (1) of the paper: the modeled credibility of the conjunctive
claim `C` after the set `S` of components has been (perfectly) audited,
`r_C(S) = ∏_{i ∈ C \ S} p i`. -/
def claimValue (p : ι → ℝ) (C S : Finset ι) : ℝ := ∏ i ∈ C \ S, p i

/-- Equation (2) of the paper: the value of a nonnegatively weighted
portfolio of conjunctive claims after auditing `S`,
`F(S) = ∑_{C ∈ 𝒞} w_C r_C(S)`.  The claim family is indexed by the finite
index set `𝒞 : Finset κ`, with `C c` the component set and `w c` the
decision weight of claim `c`. -/
def portfolioValue {κ : Type*} (p : ι → ℝ) (𝒞 : Finset κ) (C : κ → Finset ι)
    (w : κ → ℝ) (S : Finset ι) : ℝ :=
  ∑ c ∈ 𝒞, w c * claimValue p (C c) S

/-- The marginal audit value `Δ_i(S) = F(S ∪ {i}) - F(S)` of the paper. -/
def marginal {κ : Type*} (p : ι → ℝ) (𝒞 : Finset κ) (C : κ → Finset ι)
    (w : κ → ℝ) (S : Finset ι) (i : ι) : ℝ :=
  portfolioValue p 𝒞 C w (insert i S) - portfolioValue p 𝒞 C w S

@[simp] lemma claimValue_empty (p : ι → ℝ) (C : Finset ι) :
    claimValue p C ∅ = ∏ i ∈ C, p i := by
  simp [claimValue]

lemma claimValue_pos {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (C S : Finset ι) :
    0 < claimValue p C S :=
  Finset.prod_pos fun i _ => hp0 i

lemma claimValue_le_one {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1)
    (C S : Finset ι) : claimValue p C S ≤ 1 :=
  Finset.prod_le_one (fun i _ => (hp0 i).le) (fun i _ => hp1 i)

/-- Equation (3) of the paper: for `S ⊆ C`, `r_C(S) = r_C(∅) / ∏_{i ∈ S} p i`. -/
lemma claimValue_eq_div {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) {C S : Finset ι}
    (hSC : S ⊆ C) :
    claimValue p C S = (∏ i ∈ C, p i) / ∏ i ∈ S, p i := by
  have hprod : claimValue p C S * ∏ i ∈ S, p i = ∏ i ∈ C, p i :=
    Finset.prod_sdiff hSC
  have hSpos : (0:ℝ) < ∏ i ∈ S, p i := Finset.prod_pos fun i _ => hp0 i
  rw [eq_div_iff hSpos.ne']
  exact hprod

end Viridis.Run120

/- Engine-3 immutable source unit: WeakestFirst.lean -/

/-!
# Theorem 1 of the sealed paper: the conjunctive weakest-first rule

Frozen paper statement (Theorem 1, `SEALED_paper.tex`):

> **Theorem 1 (conjunctive weakest-first rule; formal target).**
> For one claim `C` and an equal-cost budget `k ≤ |C|`, any set containing the
> `k` smallest `p_i` maximizes `r_C(S)` among `|S| = k`.  If the cutoff is
> strict, the optimum is unique.

Formalization decisions (all recorded explicitly, none of them weakening the
claim):

* "a set containing the `k` smallest `p_i`" is rendered as: `S ⊆ C`,
  `|S| = k`, and every audited component is at most as reliable as every
  unaudited component of the claim, i.e.
  `∀ i ∈ S, ∀ j ∈ C \ S, p i ≤ p j`.  This is exactly the cutoff condition
  used in the paper's exchange argument, and it is satisfiable for every
  `k ≤ |C|` (`exists_weakest_selection` below), which is the non-vacuity
  witness for the hypothesis.
* "maximizes among `|S| = k`" is rendered in two forms: the literal one
  (`conjunctive_chain_weakest_first`, competitors are the subsets of `C` of
  size exactly `k`) and a strictly stronger budget form
  (`conjunctive_chain_weakest_first_budget`, competitors are *all* audit sets
  of size at most `k`, including sets that audit components outside `C`).
* "if the cutoff is strict, the optimum is unique" is
  `conjunctive_chain_weakest_first_unique`.
-/

namespace Viridis.Run120

open Finset

variable {ι : Type*} [DecidableEq ι]

/-! ### Product comparison lemmas -/

/-- Enlarging the index set cannot increase a product of factors in `(0,1]`. -/
lemma prod_le_prod_subset_of_le_one {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1)
    {A B : Finset ι} (h : A ⊆ B) : ∏ i ∈ B, p i ≤ ∏ i ∈ A, p i := by
  have hsplit : (∏ i ∈ B \ A, p i) * ∏ i ∈ A, p i = ∏ i ∈ B, p i := Finset.prod_sdiff h
  have h1 : ∏ i ∈ B \ A, p i ≤ 1 :=
    Finset.prod_le_one (fun i _ => (hp0 i).le) fun i _ => hp1 i
  have hA0 : (0:ℝ) ≤ ∏ i ∈ A, p i := (Finset.prod_pos fun i _ => hp0 i).le
  calc ∏ i ∈ B, p i = (∏ i ∈ B \ A, p i) * ∏ i ∈ A, p i := hsplit.symm
    _ ≤ 1 * ∏ i ∈ A, p i := mul_le_mul_of_nonneg_right h1 hA0
    _ = ∏ i ∈ A, p i := one_mul _

omit [DecidableEq ι] in
/-- If every element of `A` has a `p`-value at most that of every element of
`B`, and `A` and `B` have the same size, then `∏_A p ≤ ∏_B p`. -/
lemma prod_le_prod_of_pointwise_le_of_card_eq {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {A B : Finset ι} (hcard : A.card = B.card)
    (h : ∀ i ∈ A, ∀ j ∈ B, p i ≤ p j) :
    ∏ i ∈ A, p i ≤ ∏ j ∈ B, p j := by
  rcases A.eq_empty_or_nonempty with rfl | hA
  · have hB : B = ∅ := Finset.card_eq_zero.mp (by simpa using hcard.symm)
    simp [hB]
  · have hB : B.Nonempty := Finset.card_pos.mp (by rw [← hcard]; exact Finset.card_pos.mpr hA)
    set c := B.inf' hB p with hc
    have h1 : ∀ i ∈ A, p i ≤ c := fun i hi => Finset.le_inf' hB p fun j hj => h i hi j hj
    have h2 : ∀ j ∈ B, c ≤ p j := fun j hj => Finset.inf'_le p hj
    calc ∏ i ∈ A, p i ≤ ∏ _i ∈ A, c :=
          Finset.prod_le_prod (fun i _ => (hp0 i).le) h1
      _ = c ^ B.card := by rw [Finset.prod_const, hcard]
      _ = ∏ _j ∈ B, c := by rw [Finset.prod_const]
      _ ≤ ∏ j ∈ B, p j := by
          refine Finset.prod_le_prod (fun j _ => ?_) h2
          exact Finset.le_inf' hB p fun j _ => (hp0 j).le

omit [DecidableEq ι] in
/-- Strict version of `prod_le_prod_of_pointwise_le_of_card_eq`. -/
lemma prod_lt_prod_of_pointwise_lt_of_card_eq {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {A B : Finset ι} (hA : A.Nonempty) (hcard : A.card = B.card)
    (h : ∀ i ∈ A, ∀ j ∈ B, p i < p j) :
    ∏ i ∈ A, p i < ∏ j ∈ B, p j := by
  have hB : B.Nonempty := Finset.card_pos.mp (by rw [← hcard]; exact Finset.card_pos.mpr hA)
  set M := A.sup' hA p with hM
  set c := B.inf' hB p with hc
  have hMc : M < c := by
    refine Finset.sup'_lt_iff hA |>.mpr fun i hi => ?_
    exact (Finset.lt_inf'_iff hB).mpr fun j hj => h i hi j hj
  have hM0 : 0 ≤ M := le_trans (hp0 hA.choose).le (Finset.le_sup' p hA.choose_spec)
  have h1 : ∀ i ∈ A, p i ≤ M := fun i hi => Finset.le_sup' p hi
  have h2 : ∀ j ∈ B, c ≤ p j := fun j hj => Finset.inf'_le p hj
  have step1 : ∏ i ∈ A, p i ≤ M ^ A.card := by
    calc ∏ i ∈ A, p i ≤ ∏ _i ∈ A, M := Finset.prod_le_prod (fun i _ => (hp0 i).le) h1
      _ = M ^ A.card := Finset.prod_const M
  have step2 : c ^ B.card ≤ ∏ j ∈ B, p j := by
    calc c ^ B.card = ∏ _j ∈ B, c := (Finset.prod_const c).symm
      _ ≤ ∏ j ∈ B, p j := by
          refine Finset.prod_le_prod (fun j hj => ?_) h2
          exact le_trans hM0 hMc.le
  have step3 : M ^ A.card < c ^ B.card := by
    rw [hcard]
    exact pow_lt_pow_left₀ hMc hM0 (by
      have : 0 < B.card := Finset.card_pos.mpr hB
      omega)
  exact lt_of_le_of_lt step1 (lt_of_lt_of_le step3 step2)

/-! ### The audited product is minimized by a weakest-first selection -/

/-- If `S` collects the `k` weakest components of `C` and `T` is any other
`k`-subset of `C`, then `∏_{i ∈ S} p i ≤ ∏_{i ∈ T} p i`. -/
lemma prod_audited_le_of_weakest {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {C S T : Finset ι} (hTC : T ⊆ C) (hcard : S.card = T.card)
    (hmin : ∀ i ∈ S, ∀ j ∈ C \ S, p i ≤ p j) :
    ∏ i ∈ S, p i ≤ ∏ i ∈ T, p i := by
  have hSdiff : (S \ T).card = (T \ S).card := Finset.card_sdiff_comm hcard
  have key : ∏ i ∈ S \ T, p i ≤ ∏ i ∈ T \ S, p i := by
    refine prod_le_prod_of_pointwise_le_of_card_eq hp0 hSdiff fun i hi j hj => ?_
    have hiS : i ∈ S := (Finset.mem_sdiff.mp hi).1
    have hjT : j ∈ T := (Finset.mem_sdiff.mp hj).1
    have hjS : j ∉ S := (Finset.mem_sdiff.mp hj).2
    exact hmin i hiS j (Finset.mem_sdiff.mpr ⟨hTC hjT, hjS⟩)
  have hS : (∏ i ∈ S \ T, p i) * ∏ i ∈ S ∩ T, p i = ∏ i ∈ S, p i := by
    have := Finset.prod_sdiff (f := p) (Finset.inter_subset_left (s₁ := S) (s₂ := T))
    rwa [Finset.sdiff_inter_self_left] at this
  have hT : (∏ i ∈ T \ S, p i) * ∏ i ∈ T ∩ S, p i = ∏ i ∈ T, p i := by
    have := Finset.prod_sdiff (f := p) (Finset.inter_subset_left (s₁ := T) (s₂ := S))
    rwa [Finset.sdiff_inter_self_left] at this
  have hinter : ∏ i ∈ S ∩ T, p i = ∏ i ∈ T ∩ S, p i := by rw [Finset.inter_comm]
  rw [← hS, ← hT, hinter]
  exact mul_le_mul_of_nonneg_right key (Finset.prod_pos fun i _ => hp0 i).le

/-- Strict version: with a strict cutoff, any different `k`-subset audits a
strictly larger product. -/
lemma prod_audited_lt_of_weakest_strict {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {C S T : Finset ι} (hTC : T ⊆ C) (hcard : S.card = T.card) (hne : T ≠ S)
    (hmin : ∀ i ∈ S, ∀ j ∈ C \ S, p i < p j) :
    ∏ i ∈ S, p i < ∏ i ∈ T, p i := by
  have hSdiff : (S \ T).card = (T \ S).card := Finset.card_sdiff_comm hcard
  have hSTne : (S \ T).Nonempty := by
    by_contra hcon
    rw [Finset.not_nonempty_iff_eq_empty, Finset.sdiff_eq_empty_iff_subset] at hcon
    exact hne (Finset.eq_of_subset_of_card_le hcon hcard.ge).symm
  have key : ∏ i ∈ S \ T, p i < ∏ i ∈ T \ S, p i := by
    refine prod_lt_prod_of_pointwise_lt_of_card_eq hp0 hSTne hSdiff fun i hi j hj => ?_
    have hiS : i ∈ S := (Finset.mem_sdiff.mp hi).1
    have hjT : j ∈ T := (Finset.mem_sdiff.mp hj).1
    have hjS : j ∉ S := (Finset.mem_sdiff.mp hj).2
    exact hmin i hiS j (Finset.mem_sdiff.mpr ⟨hTC hjT, hjS⟩)
  have hS : (∏ i ∈ S \ T, p i) * ∏ i ∈ S ∩ T, p i = ∏ i ∈ S, p i := by
    have := Finset.prod_sdiff (f := p) (Finset.inter_subset_left (s₁ := S) (s₂ := T))
    rwa [Finset.sdiff_inter_self_left] at this
  have hT : (∏ i ∈ T \ S, p i) * ∏ i ∈ T ∩ S, p i = ∏ i ∈ T, p i := by
    have := Finset.prod_sdiff (f := p) (Finset.inter_subset_left (s₁ := T) (s₂ := S))
    rwa [Finset.sdiff_inter_self_left] at this
  have hinter : ∏ i ∈ S ∩ T, p i = ∏ i ∈ T ∩ S, p i := by rw [Finset.inter_comm]
  rw [← hS, ← hT, hinter]
  exact mul_lt_mul_of_pos_right key (Finset.prod_pos fun i _ => hp0 i)

/-! ### Theorem 1 -/

/-- **Theorem 1 (conjunctive weakest-first rule).**  For one conjunctive claim
`C`, equal-cost perfect audits, and a budget of `k ≤ |C|` audits, an audit set
`S ⊆ C` of size `k` consisting of `k` weakest components (every audited
component at most as reliable as every unaudited component of the claim)
maximizes the post-audit claim credibility `r_C(·)` among all `k`-subsets of
the claim. -/
theorem conjunctive_chain_weakest_first {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {C S : Finset ι} {k : ℕ} (hSC : S ⊆ C) (hScard : S.card = k)
    (hmin : ∀ i ∈ S, ∀ j ∈ C \ S, p i ≤ p j)
    {T : Finset ι} (hTC : T ⊆ C) (hTcard : T.card = k) :
    claimValue p C T ≤ claimValue p C S := by
  sorry

/-- **Theorem 1, uniqueness under a strict cutoff.**  If every audited
component is *strictly* less reliable than every unaudited component of the
claim, then the weakest-first audit set is the unique maximizer among the
`k`-subsets of the claim. -/
theorem conjunctive_chain_weakest_first_unique {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    {C S : Finset ι} {k : ℕ} (hSC : S ⊆ C) (hScard : S.card = k)
    (hmin : ∀ i ∈ S, ∀ j ∈ C \ S, p i < p j)
    {T : Finset ι} (hTC : T ⊆ C) (hTcard : T.card = k) (hne : T ≠ S) :
    claimValue p C T < claimValue p C S := by
  sorry

/-- Auditing outside a claim is worthless: only `S ∩ C` matters for `r_C`. -/
lemma claimValue_inter (p : ι → ℝ) (C S : Finset ι) :
    claimValue p C (S ∩ C) = claimValue p C S := by
  unfold claimValue
  congr 1
  ext x
  simp only [Finset.mem_sdiff, Finset.mem_inter]
  tauto

/-- Monotonicity of a single claim's credibility in the audited set (uses
`p i ≤ 1`). -/
lemma claimValue_mono {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1) (C : Finset ι)
    {S T : Finset ι} (hST : S ⊆ T) :
    claimValue p C S ≤ claimValue p C T :=
  prod_le_prod_subset_of_le_one hp0 hp1 (Finset.sdiff_subset_sdiff (le_refl C) hST)

/-- **Theorem 1, budget form (strictly stronger than the literal statement).**
The weakest-first set of size `k` beats *every* audit set of size at most `k`,
including sets that spend audits on components outside the claim. -/
theorem conjunctive_chain_weakest_first_budget {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    (hp1 : ∀ i, p i ≤ 1) {C S : Finset ι} {k : ℕ} (hSC : S ⊆ C) (hScard : S.card = k)
    (hmin : ∀ i ∈ S, ∀ j ∈ C \ S, p i ≤ p j)
    {T : Finset ι} (hTcard : T.card ≤ k) :
    claimValue p C T ≤ claimValue p C S := by
  sorry

/-! ### Non-vacuity of the hypothesis: weakest-first sets always exist -/

/-- For every budget `k ≤ |C|` there is a set of `k` weakest components of
`C`, so the hypothesis of Theorem 1 is never vacuous. -/
theorem exists_weakest_selection (p : ι → ℝ) (C : Finset ι) {k : ℕ} (hk : k ≤ C.card) :
    ∃ S ⊆ C, S.card = k ∧ ∀ i ∈ S, ∀ j ∈ C \ S, p i ≤ p j := by
  induction k generalizing C with
  | zero => exact ⟨∅, Finset.empty_subset C, rfl, by simp⟩
  | succ n ih =>
    have hC : C.Nonempty := Finset.card_pos.mp (by omega)
    obtain ⟨m, hmC, hm⟩ := Finset.exists_min_image C p hC
    have hcard : n ≤ (C.erase m).card := by
      rw [Finset.card_erase_of_mem hmC]; omega
    obtain ⟨S', hS'sub, hS'card, hS'min⟩ := ih (C.erase m) hcard
    have hmS' : m ∉ S' := fun h => (Finset.mem_erase.mp (hS'sub h)).1 rfl
    refine ⟨insert m S', ?_, ?_, ?_⟩
    · intro x hx
      rcases Finset.mem_insert.mp hx with rfl | hx
      · exact hmC
      · exact Finset.mem_of_mem_erase (hS'sub hx)
    · rw [Finset.card_insert_of_notMem hmS', hS'card]
    · intro i hi j hj
      have hjC : j ∈ C := (Finset.mem_sdiff.mp hj).1
      have hjni : j ∉ insert m S' := (Finset.mem_sdiff.mp hj).2
      have hjm : j ≠ m := fun h => hjni (by simp [h])
      have hjerase : j ∈ (C.erase m) \ S' :=
        Finset.mem_sdiff.mpr ⟨Finset.mem_erase.mpr ⟨hjm, hjC⟩,
          fun h => hjni (Finset.mem_insert_of_mem h)⟩
      rcases Finset.mem_insert.mp hi with rfl | hi
      · exact hm j hjC
      · exact hS'min i hi j hjerase

end Viridis.Run120

/- Engine-3 immutable source unit: Portfolio.lean -/

/-!
# Theorem 2 of the sealed paper: monotone supermodularity of the portfolio

Frozen paper statement (Theorem 2, `SEALED_paper.tex`):

> **Theorem 2 (monotone supermodularity; formal targets).**
> Under the stated assumptions, `F` is monotone.  Moreover, for `S ⊆ T` and
> `i ∉ T`, `Δ_i(S) ≤ Δ_i(T)`.

"The stated assumptions" (Section 3 and claim `C9` of the sealed inventory)
are: independence of the components, conjunctive claims, perfect equal-cost
audits, `p i ∈ (0,1]`, and nonnegative claim weights `w_C ≥ 0`.  These appear
below as `hp0 : 0 < p i`, `hp1 : p i ≤ 1`, `hw : 0 ≤ w c`, plus the
definitions `claimValue` / `portfolioValue` themselves.

The two frozen target names are `conjunctive_portfolio_monotone` and
`conjunctive_portfolio_supermodular`.  We also record the paper's marginal
formula (its equation (4)) as `marginal_eq`, since the proof sketch uses it.
-/

namespace Viridis.Run120

open Finset

variable {ι : Type*} [DecidableEq ι] {κ : Type*}

/-! ### Monotonicity -/

/-- **Theorem 2, monotonicity part.**  With component validities in `(0,1]`
and nonnegative claim weights, the portfolio value `F` is monotone in the
audited set. -/
theorem conjunctive_portfolio_monotone {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1)
    {𝒞 : Finset κ} {C : κ → Finset ι} {w : κ → ℝ} (hw : ∀ c ∈ 𝒞, 0 ≤ w c)
    {S T : Finset ι} (hST : S ⊆ T) :
    portfolioValue p 𝒞 C w S ≤ portfolioValue p 𝒞 C w T := by
  sorry

/-! ### The marginal audit value -/

/-- The single-claim marginal: auditing `i ∉ S` gains `(1 - p i)` times the
product of the remaining unaudited components of the claim if `i` belongs to
the claim, and nothing otherwise.  This is the per-claim form of equation (4)
of the paper. -/
lemma claimValue_marginal {p : ι → ℝ} (C S : Finset ι) {i : ι} (hiS : i ∉ S) :
    claimValue p C (insert i S) - claimValue p C S =
      if i ∈ C then (1 - p i) * ∏ j ∈ C \ insert i S, p j else 0 := by
  by_cases hiC : i ∈ C
  · have hmem : i ∈ C \ S := Finset.mem_sdiff.mpr ⟨hiC, hiS⟩
    have hsplit : C \ S = insert i (C \ insert i S) := by
      ext x
      simp only [Finset.mem_sdiff, Finset.mem_insert]
      constructor
      · rintro ⟨hxC, hxS⟩
        by_cases hxi : x = i
        · exact Or.inl hxi
        · exact Or.inr ⟨hxC, by simp [hxi, hxS]⟩
      · rintro (rfl | ⟨hxC, hxS⟩)
        · exact ⟨hiC, hiS⟩
        · exact ⟨hxC, fun h => hxS (Or.inr h)⟩
    have hnot : i ∉ C \ insert i S := by simp
    have h1 : claimValue p C S = p i * ∏ j ∈ C \ insert i S, p j := by
      unfold claimValue
      rw [hsplit, Finset.prod_insert hnot]
    simp only [claimValue, hiC, if_true] at *
    rw [h1]
    ring
  · have : C \ insert i S = C \ S := by
      ext x
      simp only [Finset.mem_sdiff, Finset.mem_insert]
      constructor
      · rintro ⟨hxC, hx⟩; exact ⟨hxC, fun h => hx (Or.inr h)⟩
      · rintro ⟨hxC, hxS⟩
        refine ⟨hxC, ?_⟩
        rintro (rfl | h)
        · exact hiC hxC
        · exact hxS h
    simp [claimValue, this, hiC]

/-- **Equation (4) of the paper.**  `Δ_i(S) = ∑_{C ∋ i} w_C (1 - p_i)
∏_{j ∈ C \ (S ∪ {i})} p_j`. -/
lemma marginal_eq {p : ι → ℝ} {𝒞 : Finset κ} {C : κ → Finset ι} {w : κ → ℝ}
    {S : Finset ι} {i : ι} (hiS : i ∉ S) :
    marginal p 𝒞 C w S i =
      ∑ c ∈ 𝒞.filter (fun c => i ∈ C c), w c * ((1 - p i) * ∏ j ∈ C c \ insert i S, p j) := by
  unfold marginal portfolioValue
  rw [← Finset.sum_sub_distrib]
  rw [Finset.sum_filter]
  refine Finset.sum_congr rfl fun c _ => ?_
  rw [← mul_sub, claimValue_marginal (C c) S hiS]
  by_cases h : i ∈ C c <;> simp [h]

/-! ### Supermodularity -/

/-- Per-claim supermodularity: the marginal gain from auditing `i` is larger
when more complementary components have already been audited. -/
lemma claimValue_marginal_mono {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1)
    (Cc : Finset ι) {S T : Finset ι} {i : ι} (hST : S ⊆ T) (hiT : i ∉ T) :
    claimValue p Cc (insert i S) - claimValue p Cc S
      ≤ claimValue p Cc (insert i T) - claimValue p Cc T := by
  have hiS : i ∉ S := fun h => hiT (hST h)
  rw [claimValue_marginal Cc S hiS, claimValue_marginal Cc T hiT]
  by_cases hiC : i ∈ Cc
  · simp only [hiC, if_true]
    have hsub : Cc \ insert i T ⊆ Cc \ insert i S :=
      Finset.sdiff_subset_sdiff (le_refl Cc) (Finset.insert_subset_insert i hST)
    have hprod : ∏ j ∈ Cc \ insert i S, p j ≤ ∏ j ∈ Cc \ insert i T, p j :=
      prod_le_prod_subset_of_le_one hp0 hp1 hsub
    exact mul_le_mul_of_nonneg_left hprod (by linarith [hp1 i])
  · simp [hiC]

/-- **Theorem 2, supermodularity part.**  For `S ⊆ T` and `i ∉ T`, the
marginal audit value satisfies `Δ_i(S) ≤ Δ_i(T)`: the portfolio value is
supermodular (increasing marginals) in the audited set. -/
theorem conjunctive_portfolio_supermodular {p : ι → ℝ} (hp0 : ∀ i, 0 < p i) (hp1 : ∀ i, p i ≤ 1)
    {𝒞 : Finset κ} {C : κ → Finset ι} {w : κ → ℝ} (hw : ∀ c ∈ 𝒞, 0 ≤ w c)
    {S T : Finset ι} {i : ι} (hST : S ⊆ T) (hiT : i ∉ T) :
    marginal p 𝒞 C w S i ≤ marginal p 𝒞 C w T i := by
  sorry

/-- Equivalent lattice form of supermodularity:
`F(S) + F(T) ≤ F(S ∪ T) + F(S ∩ T)` is implied for the two-set case obtained
from increasing marginals along a chain; here we record the direct
consequence used in the paper, `F(S ∪ {i}) - F(S) ≤ F(T ∪ {i}) - F(T)`,
restated without the `marginal` abbreviation. -/
theorem conjunctive_portfolio_increasing_marginals {p : ι → ℝ} (hp0 : ∀ i, 0 < p i)
    (hp1 : ∀ i, p i ≤ 1) {𝒞 : Finset κ} {C : κ → Finset ι} {w : κ → ℝ}
    (hw : ∀ c ∈ 𝒞, 0 ≤ w c) {S T : Finset ι} {i : ι} (hST : S ⊆ T) (hiT : i ∉ T) :
    portfolioValue p 𝒞 C w (insert i S) - portfolioValue p 𝒞 C w S
      ≤ portfolioValue p 𝒞 C w (insert i T) - portfolioValue p 𝒞 C w T := by
  sorry

end Viridis.Run120

/- Engine-3 immutable source unit: GreedyFailure.lean -/

/-!
# Theorem 3 of the sealed paper: a family defeating marginal greedy

Frozen paper statement (Theorem 3, `SEALED_paper.tex`):

> **Theorem 3 (greedy failure family; formal target).**
> For every `0 < ε < 1/3`, consider three components with `p_a = p_b = ε` and
> `p_c = 1/2`.  There are two claims: `{a,b}` of weight one and `{c}` of
> weight `4ε`.  With two audits, marginal greedy's improvement ratio is
> `ρ(ε) = (3ε - ε²)/(1 - ε²) → 0`.

Formalization decisions:

* The three components are `0, 1, 2 : Fin 3` (`a = 0`, `b = 1`, `c = 2`) and
  the two claims are indexed by `Fin 2`.  The instance is the exact one of
  the paper: `p = ![ε, ε, 1/2]`, claims `![{0,1}, {2}]`, weights `![1, 4ε]`.
* "marginal greedy" with a budget of two audits is formalized as the
  predicate `GreedyRun2 e x y`: the first audit `x` maximizes the marginal
  value at `∅`, and the second audit `y ≠ x` maximizes the marginal value at
  `{x}`.  The predicate leaves tie-breaking free, so the results below hold
  for *every* marginal-greedy execution, not just one chosen tie-break.
* "improvement ratio" is
  `(F(greedy) - F(∅)) / (F(optimum) - F(∅))`, the improvement over the
  unaudited baseline, exactly as computed in the paper's proof sketch.
* "`→ 0`" is a limit as `ε → 0⁺`.
-/

namespace Viridis.Run120

open Finset

/-! ### The explicit three-component instance -/

/-- Component validity probabilities `p_a = p_b = ε`, `p_c = 1/2`. -/
noncomputable def greedyP (e : ℝ) : Fin 3 → ℝ := ![e, e, 1/2]

/-- The two claims: `{a,b} = {0,1}` and `{c} = {2}`. -/
def greedyClaims : Fin 2 → Finset (Fin 3) := ![{0, 1}, {2}]

/-- The two claim weights: `1` and `4ε`. -/
noncomputable def greedyW (e : ℝ) : Fin 2 → ℝ := ![1, 4 * e]

/-- The portfolio value `F` of the counterexample family. -/
noncomputable def greedyF (e : ℝ) (S : Finset (Fin 3)) : ℝ :=
  portfolioValue (greedyP e) Finset.univ greedyClaims (greedyW e) S

/-- The marginal audit value `Δ_i(S)` of the counterexample family. -/
noncomputable def greedyMarg (e : ℝ) (S : Finset (Fin 3)) (i : Fin 3) : ℝ :=
  marginal (greedyP e) Finset.univ greedyClaims (greedyW e) S i

lemma greedyMarg_eq (e : ℝ) (S : Finset (Fin 3)) (i : Fin 3) :
    greedyMarg e S i = greedyF e (insert i S) - greedyF e S := rfl

lemma greedyF_eq (e : ℝ) (S : Finset (Fin 3)) :
    greedyF e S = (∏ i ∈ ({0, 1} : Finset (Fin 3)) \ S, greedyP e i)
      + 4 * e * ∏ i ∈ ({2} : Finset (Fin 3)) \ S, greedyP e i := by
  simp [greedyF, portfolioValue, claimValue, greedyClaims, greedyW, Fin.sum_univ_succ]

/-- The instance satisfies the model assumptions: `p i ∈ (0,1]`. -/
lemma greedyP_pos {e : ℝ} (he : 0 < e) : ∀ i, 0 < greedyP e i := by
  intro i; fin_cases i <;> simp [greedyP] <;> norm_num [he]

lemma greedyP_le_one {e : ℝ} (he : e < 1/3) : ∀ i, greedyP e i ≤ 1 := by
  intro i
  fin_cases i <;> simp [greedyP] <;> linarith

/-- The claim weights are nonnegative. -/
lemma greedyW_nonneg {e : ℝ} (he : 0 < e) : ∀ c ∈ (Finset.univ : Finset (Fin 2)), 0 ≤ greedyW e c := by
  intro c _
  fin_cases c <;> simp [greedyW]
  linarith

/-! ### The eight portfolio values -/

lemma greedyF_empty (e : ℝ) : greedyF e ∅ = e ^ 2 + 2 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ ∅ = {0, 1} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ ∅ = {2} := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_a (e : ℝ) : greedyF e {0} = 3 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {0} = {1} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {0} = {2} := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_b (e : ℝ) : greedyF e {1} = 3 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {1} = {0} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {1} = {2} := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_c (e : ℝ) : greedyF e {2} = e ^ 2 + 4 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {2} = {0, 1} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {2} = ∅ := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_ab (e : ℝ) : greedyF e {0, 1} = 1 + 2 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {0, 1} = ∅ := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {0, 1} = {2} := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_ac (e : ℝ) : greedyF e {0, 2} = 5 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {0, 2} = {1} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {0, 2} = ∅ := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

lemma greedyF_bc (e : ℝ) : greedyF e {1, 2} = 5 * e := by
  rw [greedyF_eq]
  have h1 : ({0, 1} : Finset (Fin 3)) \ {1, 2} = {0} := by decide
  have h2 : ({2} : Finset (Fin 3)) \ {1, 2} = ∅ := by decide
  rw [h1, h2]
  simp [greedyP]
  ring

/-! ### Marginal values -/

lemma fin3_cases (x : Fin 3) : x = 0 ∨ x = 1 ∨ x = 2 := by revert x; decide

lemma greedyMarg_empty_a (e : ℝ) : greedyMarg e ∅ 0 = e - e ^ 2 := by
  rw [greedyMarg_eq]
  have : insert (0 : Fin 3) (∅ : Finset (Fin 3)) = {0} := by decide
  rw [this, greedyF_a, greedyF_empty]; ring

lemma greedyMarg_empty_b (e : ℝ) : greedyMarg e ∅ 1 = e - e ^ 2 := by
  rw [greedyMarg_eq]
  have : insert (1 : Fin 3) (∅ : Finset (Fin 3)) = {1} := by decide
  rw [this, greedyF_b, greedyF_empty]; ring

lemma greedyMarg_empty_c (e : ℝ) : greedyMarg e ∅ 2 = 2 * e := by
  rw [greedyMarg_eq]
  have : insert (2 : Fin 3) (∅ : Finset (Fin 3)) = {2} := by decide
  rw [this, greedyF_c, greedyF_empty]; ring

lemma greedyMarg_c_a (e : ℝ) : greedyMarg e {2} 0 = e - e ^ 2 := by
  rw [greedyMarg_eq]
  have : insert (0 : Fin 3) ({2} : Finset (Fin 3)) = {0, 2} := by decide
  rw [this, greedyF_ac, greedyF_c]; ring

lemma greedyMarg_c_b (e : ℝ) : greedyMarg e {2} 1 = e - e ^ 2 := by
  rw [greedyMarg_eq]
  have : insert (1 : Fin 3) ({2} : Finset (Fin 3)) = {1, 2} := by decide
  rw [this, greedyF_bc, greedyF_c]; ring

/-! ### Marginal greedy with a budget of two audits -/

/-- A marginal-greedy execution with budget two: `x` is a marginal-value
maximizer at the empty audit set, and `y ≠ x` is a marginal-value maximizer
after `x` has been audited.  Tie-breaking is left free. -/
def GreedyRun2 (e : ℝ) (x y : Fin 3) : Prop :=
  (∀ z : Fin 3, greedyMarg e ∅ z ≤ greedyMarg e ∅ x) ∧ y ≠ x ∧
    (∀ z : Fin 3, z ≠ x → greedyMarg e {x} z ≤ greedyMarg e {x} y)

/-- Non-vacuity: for every `0 < ε < 1/3` a marginal-greedy execution exists,
namely "audit the distractor `c = 2`, then `a = 0`". -/
theorem greedyRun2_exists {e : ℝ} (he0 : 0 < e) : GreedyRun2 e 2 0 := by
  refine ⟨fun z => ?_, by decide, fun z hz => ?_⟩
  · rw [greedyMarg_empty_c]
    rcases fin3_cases z with rfl | rfl | rfl
    · rw [greedyMarg_empty_a]; nlinarith
    · rw [greedyMarg_empty_b]; nlinarith
    · rw [greedyMarg_empty_c]
  · rw [greedyMarg_c_a]
    rcases fin3_cases z with rfl | rfl | rfl
    · rw [greedyMarg_c_a]
    · rw [greedyMarg_c_b]
    · exact absurd rfl hz

/-- **Greedy picks the distractor first.**  In every marginal-greedy
execution the first audit is the component `c = 2`, the claim `{c}` of weight
`4ε`, and not a member of the load-bearing pair. -/
theorem greedy_first_pick_is_distractor {e : ℝ} (he0 : 0 < e) {x y : Fin 3}
    (h : GreedyRun2 e x y) : x = 2 := by
  sorry

/-- **The greedy improvement.**  Every marginal-greedy execution with budget
two gains exactly `3ε - ε²` over the unaudited baseline. -/
theorem greedy_improvement {e : ℝ} (he0 : 0 < e) {x y : Fin 3} (h : GreedyRun2 e x y) :
    greedyF e {x, y} - greedyF e ∅ = 3 * e - e ^ 2 := by
  sorry

/-- **The optimum with budget two is `{a,b}`** for `0 < ε < 1/3`. -/
theorem greedy_family_optimum {e : ℝ} (he : e < 1/3)
    {S : Finset (Fin 3)} (hS : S.card = 2) :
    greedyF e S ≤ greedyF e {0, 1} := by
  sorry

/-- **Budget form of optimality**: `{a,b}` is optimal among all audit sets of
size at most two, not just among those of size exactly two. -/
theorem greedy_family_optimum_budget {e : ℝ} (he0 : 0 < e) (he : e < 1/3)
    {S : Finset (Fin 3)} (hS : S.card ≤ 2) :
    greedyF e S ≤ greedyF e {0, 1} := by
  sorry

/-- The optimal improvement over the unaudited baseline is `1 - ε²`. -/
theorem greedy_family_optimal_improvement (e : ℝ) :
    greedyF e {0, 1} - greedyF e ∅ = 1 - e ^ 2 := by
  sorry

/-- The improvement ratio of any marginal-greedy execution is
`ρ(ε) = (3ε - ε²)/(1 - ε²)`. -/
theorem greedy_improvement_ratio {e : ℝ} (he0 : 0 < e) {x y : Fin 3} (h : GreedyRun2 e x y) :
    (greedyF e {x, y} - greedyF e ∅) / (greedyF e {0, 1} - greedyF e ∅)
      = (3 * e - e ^ 2) / (1 - e ^ 2) := by
  sorry

/-- `ρ(ε) = (3ε - ε²)/(1 - ε²) → 0` as `ε → 0⁺`. -/
theorem greedy_ratio_tendsto_zero :
    Filter.Tendsto (fun e : ℝ => (3 * e - e ^ 2) / (1 - e ^ 2))
      (nhdsWithin 0 (Set.Ioi 0)) (nhds 0) := by
  sorry

/-! ### Theorem 3 -/

/-- **Theorem 3 (greedy failure family).**  For the explicit three-component
family `p = ![ε, ε, 1/2]` with claims `{0,1}` of weight `1` and `{2}` of
weight `4ε`, for every `0 < ε < 1/3`:

* the instance satisfies the model assumptions (`p i ∈ (0,1]`, weights `≥ 0`);
* a marginal-greedy execution with budget two exists;
* every such execution audits the distractor `2` first and improves the
  portfolio value by exactly `3ε - ε²`;
* the best two-audit set is `{0,1}`, improving by `1 - ε²`;
* hence the marginal-greedy improvement ratio equals `ρ(ε) = (3ε - ε²)/(1 - ε²)`,

and `ρ(ε) → 0` as `ε → 0⁺`, so marginal greedy has no positive worst-case
improvement guarantee in this model. -/
theorem marginal_greedy_counterexample_family :
    (∀ e : ℝ, 0 < e → e < 1/3 →
        (∀ i, 0 < greedyP e i) ∧ (∀ i, greedyP e i ≤ 1) ∧
        (∀ c ∈ (Finset.univ : Finset (Fin 2)), 0 ≤ greedyW e c) ∧
        GreedyRun2 e 2 0 ∧
        (∀ x y : Fin 3, GreedyRun2 e x y →
          x = 2 ∧ greedyF e {x, y} - greedyF e ∅ = 3 * e - e ^ 2) ∧
        (∀ S : Finset (Fin 3), S.card = 2 → greedyF e S ≤ greedyF e {0, 1}) ∧
        greedyF e {0, 1} - greedyF e ∅ = 1 - e ^ 2 ∧
        (∀ x y : Fin 3, GreedyRun2 e x y →
          (greedyF e {x, y} - greedyF e ∅) / (greedyF e {0, 1} - greedyF e ∅)
            = (3 * e - e ^ 2) / (1 - e ^ 2)))
      ∧ Filter.Tendsto (fun e : ℝ => (3 * e - e ^ 2) / (1 - e ^ 2))
          (nhdsWithin 0 (Set.Ioi 0)) (nhds 0) := by
  sorry

end Viridis.Run120

/- Engine-3 immutable source unit: NonVacuity.lean -/

/-!
# Explicit non-vacuity witnesses

For each formalized target we exhibit a concrete instance in which every
hypothesis of the theorem is satisfied *and* the conclusion has strict
content (a strict inequality, not an equality forced by degeneracy).

* Theorem 1: `weakest_first_witness` (plus `exists_weakest_selection`, which
  shows the "`k` weakest components" hypothesis is satisfiable for every
  budget `k ≤ |C|` in every instance).
* Theorem 2: `portfolio_witness` — a portfolio that is *strictly* increasing
  and has *strictly* increasing marginals.
* Theorem 3: `greedyRun2_exists` (a marginal-greedy execution exists) together
  with `greedy_family_ratio_pos_lt_one` — the greedy improvement is strictly
  positive and strictly below the optimum, so the failure ratio is a genuine
  ratio in `(0,1)`.
-/

namespace Viridis.Run120

open Finset

/-! ### A three-component chain for Theorem 1 -/

/-- Component validities `1/2, 1/3, 1/4`. -/
noncomputable def wfP : Fin 3 → ℝ := ![1/2, 1/3, 1/4]

/-- The single conjunctive claim `{0,1,2}`. -/
def wfC : Finset (Fin 3) := {0, 1, 2}

@[simp] lemma wfP_zero : wfP 0 = 1/2 := rfl
@[simp] lemma wfP_one : wfP 1 = 1/3 := rfl
@[simp] lemma wfP_two : wfP 2 = 1/4 := rfl

lemma wfP_pos : ∀ i, 0 < wfP i := by
  intro i
  fin_cases i <;> simp [wfP]

lemma wfP_le_one : ∀ i, wfP i ≤ 1 := by
  intro i
  fin_cases i <;> simp [wfP] <;> norm_num

/-- **Non-vacuity for Theorem 1.**  With `p = (1/2, 1/3, 1/4)`, the claim
`C = {0,1,2}` and budget `k = 1`, the audit set `{2}` satisfies every
hypothesis of `conjunctive_chain_weakest_first`, and it strictly beats the
competing audit set `{0}`; so the theorem's conclusion is not vacuous. -/
theorem weakest_first_witness :
    (∀ i, 0 < wfP i) ∧ (∀ i, wfP i ≤ 1) ∧
      ({2} : Finset (Fin 3)) ⊆ wfC ∧ ({2} : Finset (Fin 3)).card = 1 ∧
      (∀ i ∈ ({2} : Finset (Fin 3)), ∀ j ∈ wfC \ {2}, wfP i ≤ wfP j) ∧
      claimValue wfP wfC {0} < claimValue wfP wfC {2} := by
  refine ⟨wfP_pos, wfP_le_one, by decide, rfl, ?_, ?_⟩
  · intro i hi j hj
    have hi2 : i = 2 := Finset.mem_singleton.mp hi
    have hjset : wfC \ {2} = ({0, 1} : Finset (Fin 3)) := by decide
    rw [hjset] at hj
    subst hi2
    rcases Finset.mem_insert.mp hj with rfl | hj
    · simp [wfP]; norm_num
    · rw [Finset.mem_singleton] at hj
      subst hj
      simp [wfP]; norm_num
  · have h1 : wfC \ {0} = ({1, 2} : Finset (Fin 3)) := by decide
    have h2 : wfC \ {2} = ({0, 1} : Finset (Fin 3)) := by decide
    simp only [claimValue, h1, h2]
    simp [wfP]
    norm_num

/-- The conclusion of Theorem 1 applied to the witness instance. -/
theorem weakest_first_witness_conclusion
    {T : Finset (Fin 3)} (hTC : T ⊆ wfC) (hT : T.card = 1) :
    claimValue wfP wfC T ≤ claimValue wfP wfC {2} := by
  obtain ⟨-, -, hsub, hcard, hmin, -⟩ := weakest_first_witness
  exact conjunctive_chain_weakest_first wfP_pos hsub hcard hmin hTC hT

/-! ### A portfolio for Theorem 2 -/

/-- A one-claim portfolio: the conjunctive claim `{0,1}` with weight `1`. -/
def pfC : Fin 1 → Finset (Fin 3) := ![{0, 1}]

/-- The weight vector of the witness portfolio. -/
noncomputable def pfW : Fin 1 → ℝ := ![1]

lemma pfW_nonneg : ∀ c ∈ (Finset.univ : Finset (Fin 1)), 0 ≤ pfW c := by
  intro c _
  fin_cases c
  norm_num [pfW]

lemma pfF_eq (S : Finset (Fin 3)) :
    portfolioValue wfP Finset.univ pfC pfW S = ∏ i ∈ ({0, 1} : Finset (Fin 3)) \ S, wfP i := by
  simp [portfolioValue, claimValue, pfC, pfW]

/-- **Non-vacuity for Theorem 2.**  The one-claim portfolio `{0,1}` with
`p = (1/2, 1/3, 1/4)` satisfies the assumptions, is *strictly* increasing
(`F(∅) < F({0})`), and has *strictly* increasing marginals
(`Δ_0(∅) < Δ_0({1})`); so neither conclusion of Theorem 2 is vacuous. -/
theorem portfolio_witness :
    (∀ i, 0 < wfP i) ∧ (∀ i, wfP i ≤ 1) ∧
      (∀ c ∈ (Finset.univ : Finset (Fin 1)), 0 ≤ pfW c) ∧
      portfolioValue wfP Finset.univ pfC pfW ∅
        < portfolioValue wfP Finset.univ pfC pfW {0} ∧
      marginal wfP Finset.univ pfC pfW ∅ 0
        < marginal wfP Finset.univ pfC pfW {1} 0 := by
  have e0 : portfolioValue wfP Finset.univ pfC pfW ∅ = 1/6 := by
    rw [pfF_eq]
    have h : ({0, 1} : Finset (Fin 3)) \ ∅ = ({0, 1} : Finset (Fin 3)) := by decide
    rw [h]; simp [wfP]; norm_num
  have e1 : portfolioValue wfP Finset.univ pfC pfW {0} = 1/3 := by
    rw [pfF_eq]
    have h : ({0, 1} : Finset (Fin 3)) \ {0} = ({1} : Finset (Fin 3)) := by decide
    rw [h]; simp [wfP]
  have e2 : portfolioValue wfP Finset.univ pfC pfW {1} = 1/2 := by
    rw [pfF_eq]
    have h : ({0, 1} : Finset (Fin 3)) \ {1} = ({0} : Finset (Fin 3)) := by decide
    rw [h]; simp [wfP]
  have e3 : portfolioValue wfP Finset.univ pfC pfW {0, 1} = 1 := by
    rw [pfF_eq]
    have h : ({0, 1} : Finset (Fin 3)) \ {0, 1} = (∅ : Finset (Fin 3)) := by decide
    rw [h]; norm_num
  refine ⟨wfP_pos, wfP_le_one, pfW_nonneg, by rw [e0, e1]; norm_num, ?_⟩
  have ins0 : insert (0 : Fin 3) (∅ : Finset (Fin 3)) = {0} := by decide
  have ins1 : insert (0 : Fin 3) ({1} : Finset (Fin 3)) = {0, 1} := by decide
  unfold marginal
  rw [ins0, ins1, e0, e1, e2, e3]
  norm_num

/-! ### Non-triviality of the greedy failure ratio -/

/-- For every `0 < ε < 1/3` the marginal-greedy improvement is strictly
positive and strictly smaller than the optimal improvement, so the ratio
`ρ(ε)` of Theorem 3 lies strictly between `0` and `1`. -/
theorem greedy_family_ratio_pos_lt_one {e : ℝ} (he0 : 0 < e) (he : e < 1/3) :
    0 < (3 * e - e ^ 2) / (1 - e ^ 2) ∧ (3 * e - e ^ 2) / (1 - e ^ 2) < 1 := by
  have hden : 0 < 1 - e ^ 2 := by nlinarith
  constructor
  · apply div_pos _ hden
    nlinarith
  · rw [div_lt_one hden]
    nlinarith

end Viridis.Run120
