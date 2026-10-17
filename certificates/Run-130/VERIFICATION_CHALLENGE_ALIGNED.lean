/- Engine-3 immutable source unit: Hall.lean -/
import Mathlib

/-!
# A capacitated Hall / Gale supply–demand theorem

This file develops, from scratch, the network-flow ingredient that the sealed paper
(`SEALED_paper.tex`, Run-130, "The Seed-Source Bottleneck Certificate") invokes as
"max-flow/min-cut" in its proof sketch of Proposition 1.

Mathlib (revision recorded in `TOOLCHAIN.md`) contains Hall's marriage theorem but no
max-flow/min-cut theorem and no capacitated Hall condition, so the required statement is
proved here directly, by induction on the total size of the bipartite ground sets.

Everything in this file is stated for arbitrary `Finset`s `A` of sites and `B` of sources
so that the induction can shrink both sides; the paper-level statements in
`PaperFormalization/Certificate.lean` are the special case `A = univ`, `B = univ`.
-/

namespace Viridis.Run130.Hall

open Finset

variable {σ τ : Type*} [DecidableEq σ] [DecidableEq τ]

/-- `nbhdOn B E U` is the eligible neighbourhood `N(U) = {j ∈ B : ∃ i ∈ U, (j,i) ∈ E}`. -/
def nbhdOn (B : Finset τ) (E : τ → σ → Bool) (U : Finset σ) : Finset τ :=
  B.filter (fun j => ∃ i ∈ U, E j i)

/-- `dem d U = D(U) = ∑_{i ∈ U} d i`. -/
def dem (d : σ → ℝ) (U : Finset σ) : ℝ := ∑ i ∈ U, d i

/-- `cap s C = S(C) = ∑_{j ∈ C} s j`. -/
def cap (s : τ → ℝ) (C : Finset τ) : ℝ := ∑ j ∈ C, s j

omit [DecidableEq σ] [DecidableEq τ] in
@[simp] lemma mem_nbhdOn {B : Finset τ} {E : τ → σ → Bool} {U : Finset σ} {j : τ} :
    j ∈ nbhdOn B E U ↔ j ∈ B ∧ ∃ i ∈ U, E j i := by
  simp [nbhdOn]

omit [DecidableEq σ] [DecidableEq τ] in
lemma nbhdOn_subset (B : Finset τ) (E : τ → σ → Bool) (U : Finset σ) :
    nbhdOn B E U ⊆ B := filter_subset _ _

omit [DecidableEq σ] [DecidableEq τ] in
lemma nbhdOn_mono_sites {B : Finset τ} {E : τ → σ → Bool} {U V : Finset σ} (h : U ⊆ V) :
    nbhdOn B E U ⊆ nbhdOn B E V := by
  intro j hj
  obtain ⟨hjB, i, hi, hEi⟩ := mem_nbhdOn.1 hj
  exact mem_nbhdOn.2 ⟨hjB, i, h hi, hEi⟩

omit [DecidableEq σ] [DecidableEq τ] in
lemma nbhdOn_mono_edges {B : Finset τ} {E F : τ → σ → Bool} (hEF : ∀ j i, E j i → F j i)
    (U : Finset σ) : nbhdOn B E U ⊆ nbhdOn B F U := by
  intro j hj
  obtain ⟨hjB, i, hi, hEi⟩ := mem_nbhdOn.1 hj
  exact mem_nbhdOn.2 ⟨hjB, i, hi, hEF j i hEi⟩

lemma nbhdOn_union {B : Finset τ} {E : τ → σ → Bool} (U V : Finset σ) :
    nbhdOn B E (U ∪ V) = nbhdOn B E U ∪ nbhdOn B E V := by
  ext j
  constructor
  · intro hj
    obtain ⟨hjB, i, hi, hEi⟩ := mem_nbhdOn.1 hj
    rcases Finset.mem_union.1 hi with h' | h'
    · exact Finset.mem_union_left _ (mem_nbhdOn.2 ⟨hjB, i, h', hEi⟩)
    · exact Finset.mem_union_right _ (mem_nbhdOn.2 ⟨hjB, i, h', hEi⟩)
  · intro hj
    rcases Finset.mem_union.1 hj with h' | h' <;>
      · obtain ⟨hjB, i, hi, hEi⟩ := mem_nbhdOn.1 h'
        exact mem_nbhdOn.2 ⟨hjB, i, by simp [hi], hEi⟩

omit [DecidableEq σ] [DecidableEq τ] in
@[simp] lemma nbhdOn_empty (B : Finset τ) (E : τ → σ → Bool) :
    nbhdOn B E (∅ : Finset σ) = ∅ := by
  ext j; simp

omit [DecidableEq σ] in
@[simp] lemma dem_empty (d : σ → ℝ) : dem d (∅ : Finset σ) = 0 := by simp [dem]

omit [DecidableEq τ] in
@[simp] lemma cap_empty (s : τ → ℝ) : cap s (∅ : Finset τ) = 0 := by simp [cap]

omit [DecidableEq σ] in
lemma dem_nonneg {d : σ → ℝ} {U : Finset σ} (h : ∀ i ∈ U, 0 ≤ d i) : 0 ≤ dem d U :=
  Finset.sum_nonneg h

omit [DecidableEq τ] in
lemma cap_nonneg {s : τ → ℝ} {C : Finset τ} (h : ∀ j ∈ C, 0 ≤ s j) : 0 ≤ cap s C :=
  Finset.sum_nonneg h

omit [DecidableEq τ] in
lemma cap_mono {s : τ → ℝ} {C D : Finset τ} (hCD : C ⊆ D) (h : ∀ j ∈ D, 0 ≤ s j) :
    cap s C ≤ cap s D :=
  Finset.sum_le_sum_of_subset_of_nonneg hCD (fun j hj _ => h j hj)

/-- Splitting off a union: `S(C ∪ D) = S(C) + S(D \ C)`. -/
lemma cap_union_sdiff (s : τ → ℝ) (C D : Finset τ) :
    cap s (C ∪ D) = cap s C + cap s (D \ C) := by
  have h : C ∪ D = C ∪ (D \ C) := by ext j; by_cases h : j ∈ C <;> simp [h]
  rw [h, cap, cap, cap, Finset.sum_union Finset.disjoint_sdiff]

/-- Effect on a finite sum of decreasing one coordinate by `c`. -/
lemma sum_update_sub {α : Type*} [DecidableEq α] (f : α → ℝ) (a : α) (c : ℝ) (U : Finset α) :
    ∑ x ∈ U, Function.update f a (f a - c) x
      = (∑ x ∈ U, f x) - (if a ∈ U then c else 0) := by
  by_cases h : a ∈ U
  · rw [if_pos h, ← Finset.add_sum_erase _ _ h, ← Finset.add_sum_erase _ f h]
    have hcongr : ∑ x ∈ U.erase a, Function.update f a (f a - c) x = ∑ x ∈ U.erase a, f x :=
      Finset.sum_congr rfl fun x hx => Function.update_of_ne (Finset.ne_of_mem_erase hx) _ _
    rw [hcongr, Function.update_self]
    ring
  · rw [if_neg h, sub_zero]
    exact Finset.sum_congr rfl fun x hx =>
      Function.update_of_ne (by rintro rfl; exact h hx) _ _

omit [DecidableEq τ] in
lemma dem_update_sub (d : σ → ℝ) (i₀ : σ) (c : ℝ) (U : Finset σ) :
    dem (Function.update d i₀ (d i₀ - c)) U = dem d U - (if i₀ ∈ U then c else 0) :=
  sum_update_sub d i₀ c U

omit [DecidableEq σ] in
lemma cap_update_sub (s : τ → ℝ) (j₀ : τ) (c : ℝ) (C : Finset τ) :
    cap (Function.update s j₀ (s j₀ - c)) C = cap s C - (if j₀ ∈ C then c else 0) :=
  sum_update_sub s j₀ c C

/-- A routing (feasible transportation plan) on the bipartite pair `(A, B)`:
nonnegative, supported on eligible pairs inside `B × A`, meeting every site demand exactly
and respecting every source capacity. -/
structure IsRoutingOn (A : Finset σ) (B : Finset τ) (E : τ → σ → Bool)
    (d : σ → ℝ) (s : τ → ℝ) (x : τ → σ → ℝ) : Prop where
  nonneg : ∀ j i, 0 ≤ x j i
  support : ∀ j i, ¬ (j ∈ B ∧ i ∈ A ∧ E j i) → x j i = 0
  rows : ∀ i ∈ A, ∑ j ∈ B, x j i = d i
  cols : ∀ j ∈ B, ∑ i ∈ A, x j i ≤ s j

namespace IsRoutingOn

variable {A : Finset σ} {B : Finset τ} {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ}
  {x : τ → σ → ℝ} {i₀ : σ} {j₀ : τ}

omit [DecidableEq σ] [DecidableEq τ] in
lemma row_zero_of_notMem (h : IsRoutingOn A B E d s x) {i : σ} (hi : i ∉ A) (j : τ) :
    x j i = 0 := h.support j i (by tauto)

omit [DecidableEq σ] [DecidableEq τ] in
lemma col_zero_of_notMem (h : IsRoutingOn A B E d s x) {j : τ} (hj : j ∉ B) (i : σ) :
    x j i = 0 := h.support j i (by tauto)

omit [DecidableEq τ] in
/-- A routing on `A.erase i₀` is a routing on `A` as soon as `d i₀ = 0`. -/
lemma extend_site (h : IsRoutingOn (A.erase i₀) B E d s x) (hi₀ : d i₀ = 0) :
    IsRoutingOn A B E d s x := by
  have hzero : ∀ j, x j i₀ = 0 := h.row_zero_of_notMem (Finset.notMem_erase _ _)
  refine ⟨h.nonneg, ?_, ?_, ?_⟩
  · intro j i hji
    refine h.support j i ?_
    rintro ⟨hjB, hiA, hE⟩
    exact hji ⟨hjB, Finset.mem_of_mem_erase hiA, hE⟩
  · intro i hi
    by_cases hii : i = i₀
    · subst hii
      rw [hi₀]
      exact Finset.sum_eq_zero fun j _ => hzero j
    · exact h.rows i (Finset.mem_erase.2 ⟨hii, hi⟩)
  · intro j hj
    have hsplit : ∑ i ∈ A, x j i = ∑ i ∈ A.erase i₀, x j i := by
      refine (Finset.sum_subset (Finset.erase_subset _ _) ?_).symm
      intro i hiA hi
      have : i = i₀ := by
        by_contra hne
        exact hi (Finset.mem_erase.2 ⟨hne, hiA⟩)
      subst this
      exact hzero j
    rw [hsplit]
    exact h.cols j hj

omit [DecidableEq σ] in
/-- A routing on `B.erase j₀` is a routing on `B` as soon as `0 ≤ s j₀`. -/
lemma extend_source (h : IsRoutingOn A (B.erase j₀) E d s x) (hj₀ : 0 ≤ s j₀) :
    IsRoutingOn A B E d s x := by
  have hzero : ∀ i, x j₀ i = 0 := h.col_zero_of_notMem (Finset.notMem_erase _ _)
  refine ⟨h.nonneg, ?_, ?_, ?_⟩
  · intro j i hji
    refine h.support j i ?_
    rintro ⟨hjB, hiA, hE⟩
    exact hji ⟨Finset.mem_of_mem_erase hjB, hiA, hE⟩
  · intro i hi
    have hsplit : ∑ j ∈ B, x j i = ∑ j ∈ B.erase j₀, x j i := by
      refine (Finset.sum_subset (Finset.erase_subset _ _) ?_).symm
      intro j hjB hj
      have : j = j₀ := by
        by_contra hne
        exact hj (Finset.mem_erase.2 ⟨hne, hjB⟩)
      subst this
      exact hzero i
    rw [hsplit]
    exact h.rows i hi
  · intro j hj
    by_cases hjj : j = j₀
    · subst hjj
      have : ∑ i ∈ A, x j i = 0 := Finset.sum_eq_zero fun i _ => hzero i
      rw [this]
      exact hj₀
    · exact h.cols j (Finset.mem_erase.2 ⟨hjj, hj⟩)

end IsRoutingOn

/-- Adding back `ε` units on a single eligible pair `(j₀, i₀)` turns a routing for the
demands/capacities reduced by `ε` at `(i₀, j₀)` into a routing for the original data. -/
lemma routing_bump {A : Finset σ} {B : Finset τ} {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ}
    {i₀ : σ} {j₀ : τ} {ε : ℝ} {x y : τ → σ → ℝ}
    (hi₀ : i₀ ∈ A) (hj₀ : j₀ ∈ B) (hE : E j₀ i₀) (hε : 0 ≤ ε)
    (hy : ∀ j i, y j i = x j i + if j = j₀ ∧ i = i₀ then ε else 0)
    (h : IsRoutingOn A B E (Function.update d i₀ (d i₀ - ε))
          (Function.update s j₀ (s j₀ - ε)) x) :
    IsRoutingOn A B E d s y := by
  have hrow : ∀ i, ∑ j ∈ B, y j i = (∑ j ∈ B, x j i) + (if i = i₀ then ε else 0) := by
    intro i
    have hpt : ∀ j ∈ B, y j i = x j i + (if j = j₀ then (if i = i₀ then ε else 0) else 0) := by
      intro j _
      rw [hy]
      by_cases h1 : j = j₀ <;> by_cases h2 : i = i₀ <;> simp [h1, h2]
    rw [Finset.sum_congr rfl hpt, Finset.sum_add_distrib]
    congr 1
    rw [Finset.sum_ite_eq' B j₀ (fun _ => if i = i₀ then ε else 0), if_pos hj₀]
  have hcol : ∀ j, ∑ i ∈ A, y j i = (∑ i ∈ A, x j i) + (if j = j₀ then ε else 0) := by
    intro j
    have hpt : ∀ i ∈ A, y j i = x j i + (if i = i₀ then (if j = j₀ then ε else 0) else 0) := by
      intro i _
      rw [hy]
      by_cases h1 : j = j₀ <;> by_cases h2 : i = i₀ <;> simp [h1, h2]
    rw [Finset.sum_congr rfl hpt, Finset.sum_add_distrib]
    congr 1
    rw [Finset.sum_ite_eq' A i₀ (fun _ => if j = j₀ then ε else 0), if_pos hi₀]
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro j i
    have h1 := h.nonneg j i
    rw [hy]
    by_cases hc : j = j₀ ∧ i = i₀
    · rw [if_pos hc]; linarith
    · rw [if_neg hc]; linarith
  · intro j i hji
    have hx : x j i = 0 := h.support j i hji
    have hc : ¬ (j = j₀ ∧ i = i₀) := by
      rintro ⟨rfl, rfl⟩; exact hji ⟨hj₀, hi₀, hE⟩
    rw [hy, hx, if_neg hc, add_zero]
  · intro i hi
    have hr := h.rows i hi
    rw [hrow i, hr]
    by_cases hii : i = i₀
    · subst hii
      rw [Function.update_self, if_pos rfl]
      ring
    · rw [Function.update_of_ne hii, if_neg hii, add_zero]
  · intro j hj
    have hc := h.cols j hj
    rw [hcol j]
    by_cases hjj : j = j₀
    · subst hjj
      rw [Function.update_self] at hc
      rw [if_pos rfl]
      linarith
    · rw [Function.update_of_ne hjj] at hc
      rw [if_neg hjj, add_zero]
      exact hc

/-- **Capacitated Hall theorem** (the "max-flow/min-cut" ingredient of Proposition 1 of the
sealed paper), in the form needed here: if every set of sites has an eligible neighbourhood
with at least as much capacity as its demand, then all demands can be met exactly. -/
theorem exists_routing_of_hall_aux :
    ∀ (n : ℕ) (A : Finset σ) (B : Finset τ) (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ),
      A.card + B.card ≤ n →
      (∀ i ∈ A, 0 ≤ d i) → (∀ j ∈ B, 0 ≤ s j) →
      (∀ U ⊆ A, dem d U ≤ cap s (nbhdOn B E U)) →
      ∃ x, IsRoutingOn A B E d s x := by
  intro n
  induction n with
  | zero =>
    intro A B E d s hcard _ hs _
    have hA : A = ∅ := card_eq_zero.1 (Nat.le_zero.1 (le_trans (Nat.le_add_right _ _) hcard))
    have hB : B = ∅ := card_eq_zero.1 (Nat.le_zero.1 (le_trans (Nat.le_add_left _ _) hcard))
    subst hA; subst hB
    exact ⟨fun _ _ => 0, ⟨fun _ _ => le_rfl, fun _ _ _ => rfl, by simp, by simp⟩⟩
  | succ n IH =>
    intro A B E d s hcard hd hs hall
    -- The "critical set" split, available for every choice of demands/capacities on `(A,B)`.
    have key : ∀ (d' : σ → ℝ) (s' : τ → ℝ) (U : Finset σ), U ⊆ A → U.Nonempty → U ≠ A →
        (∀ i ∈ A, 0 ≤ d' i) → (∀ j ∈ B, 0 ≤ s' j) →
        (∀ W ⊆ A, dem d' W ≤ cap s' (nbhdOn B E W)) →
        dem d' U = cap s' (nbhdOn B E U) →
        ∃ x, IsRoutingOn A B E d' s' x := by
      intro d' s' U hUA hUne hUA' hd' hs' hall' hcrit
      have hCB : nbhdOn B E U ⊆ B := nbhdOn_subset _ _ _
      have hUcard : U.card < A.card := card_lt_card (lt_of_le_of_ne hUA hUA')
      -- first subproblem: sites `U`, sources `N(U)`
      have h1card : U.card + (nbhdOn B E U).card ≤ n := by
        have : (nbhdOn B E U).card ≤ B.card := card_le_card hCB
        omega
      have hnb : ∀ W ⊆ U, nbhdOn (nbhdOn B E U) E W = nbhdOn B E W := by
        intro W hW
        ext j
        constructor
        · intro hj
          obtain ⟨hjC, i, hi, hEi⟩ := mem_nbhdOn.1 hj
          exact mem_nbhdOn.2 ⟨hCB hjC, i, hi, hEi⟩
        · intro hj
          obtain ⟨hjB, i, hi, hEi⟩ := mem_nbhdOn.1 hj
          exact mem_nbhdOn.2 ⟨mem_nbhdOn.2 ⟨hjB, i, hW hi, hEi⟩, i, hi, hEi⟩
      obtain ⟨x₁, hx₁⟩ := IH U (nbhdOn B E U) E d' s' h1card (fun i hi => hd' i (hUA hi))
        (fun j hj => hs' j (hCB hj))
        (by
          intro W hW
          rw [hnb W hW]
          exact hall' W (hW.trans hUA))
      -- second subproblem: sites `A \ U`, sources `B \ N(U)`
      have h2card : (A \ U).card + (B \ nbhdOn B E U).card ≤ n := by
        have h1 : (A \ U).card < A.card := by
          refine Finset.card_lt_card ⟨sdiff_subset, ?_⟩
          intro hsub
          obtain ⟨a, ha⟩ := hUne
          exact (Finset.mem_sdiff.1 (hsub (hUA ha))).2 ha
        have h2 : (B \ nbhdOn B E U).card ≤ B.card := card_le_card sdiff_subset
        omega
      have hnb2 : ∀ W : Finset σ,
          nbhdOn (B \ nbhdOn B E U) E W = nbhdOn B E W \ nbhdOn B E U := by
        intro W
        ext j
        simp only [mem_nbhdOn, Finset.mem_sdiff, mem_nbhdOn]
        tauto
      obtain ⟨x₂, hx₂⟩ := IH (A \ U) (B \ nbhdOn B E U) E d' s' h2card
        (fun i hi => hd' i (Finset.mem_sdiff.1 hi).1)
        (fun j hj => hs' j (Finset.mem_sdiff.1 hj).1)
        (by
          intro W hW
          rw [hnb2 W]
          have hWA : W ⊆ A := hW.trans sdiff_subset
          have hbig := hall' (W ∪ U) (union_subset hWA hUA)
          have hdemW : dem d' (W ∪ U) = dem d' W + dem d' U := by
            refine Finset.sum_union ?_
            refine Finset.disjoint_left.2 ?_
            intro a haW haU
            exact (Finset.mem_sdiff.1 (hW haW)).2 haU
          rw [hdemW, nbhdOn_union, Finset.union_comm, cap_union_sdiff, hcrit] at hbig
          linarith)
      refine ⟨fun j i => x₁ j i + x₂ j i, ⟨?_, ?_, ?_, ?_⟩⟩
      · intro j i
        have h1 := hx₁.nonneg j i
        have h2 := hx₂.nonneg j i
        linarith
      · intro j i hji
        have h1 : x₁ j i = 0 := by
          refine hx₁.support j i ?_
          rintro ⟨hjC, hiU, hE⟩
          exact hji ⟨hCB hjC, hUA hiU, hE⟩
        have h2 : x₂ j i = 0 := by
          refine hx₂.support j i ?_
          rintro ⟨hjB, hiA, hE⟩
          exact hji ⟨(Finset.mem_sdiff.1 hjB).1, (Finset.mem_sdiff.1 hiA).1, hE⟩
        simp [h1, h2]
      · intro i hi
        rw [Finset.sum_add_distrib]
        by_cases hiU : i ∈ U
        · have e1 : ∑ j ∈ B, x₁ j i = ∑ j ∈ nbhdOn B E U, x₁ j i := by
            refine (Finset.sum_subset hCB ?_).symm
            intro j _ hj
            exact hx₁.col_zero_of_notMem hj i
          have e2 : ∑ j ∈ B, x₂ j i = 0 :=
            Finset.sum_eq_zero fun j _ =>
              hx₂.row_zero_of_notMem (by simp [hiU]) j
          rw [e1, e2, hx₁.rows i hiU, add_zero]
        · have hiAU : i ∈ A \ U := Finset.mem_sdiff.2 ⟨hi, hiU⟩
          have e1 : ∑ j ∈ B, x₁ j i = 0 :=
            Finset.sum_eq_zero fun j _ => hx₁.row_zero_of_notMem hiU j
          have e2 : ∑ j ∈ B, x₂ j i = ∑ j ∈ B \ nbhdOn B E U, x₂ j i := by
            refine (Finset.sum_subset sdiff_subset ?_).symm
            intro j _ hj
            exact hx₂.col_zero_of_notMem hj i
          rw [e1, e2, hx₂.rows i hiAU, zero_add]
      · intro j hj
        rw [Finset.sum_add_distrib]
        by_cases hjC : j ∈ nbhdOn B E U
        · have e1 : ∑ i ∈ A, x₁ j i = ∑ i ∈ U, x₁ j i := by
            refine (Finset.sum_subset hUA ?_).symm
            intro i _ hi
            exact hx₁.row_zero_of_notMem hi j
          have e2 : ∑ i ∈ A, x₂ j i = 0 :=
            Finset.sum_eq_zero fun i _ =>
              hx₂.col_zero_of_notMem (by simp [hjC]) i
          rw [e1, e2, add_zero]
          exact hx₁.cols j hjC
        · have e1 : ∑ i ∈ A, x₁ j i = 0 :=
            Finset.sum_eq_zero fun i _ => hx₁.col_zero_of_notMem hjC i
          have e2 : ∑ i ∈ A, x₂ j i = ∑ i ∈ A \ U, x₂ j i := by
            refine (Finset.sum_subset sdiff_subset ?_).symm
            intro i _ hi
            exact hx₂.row_zero_of_notMem hi j
          rw [e1, e2, zero_add]
          exact hx₂.cols j (Finset.mem_sdiff.2 ⟨hj, hjC⟩)
    -- Main dispatch.
    by_cases hzero : ∀ i ∈ A, d i = 0
    · refine ⟨fun _ _ => 0, ⟨fun _ _ => le_rfl, fun _ _ _ => rfl, ?_, ?_⟩⟩
      · intro i hi; simp [hzero i hi]
      · intro j hj; simpa using hs j hj
    push_neg at hzero
    obtain ⟨i₀, hi₀A, hi₀⟩ := hzero
    have hd0 : 0 < d i₀ := lt_of_le_of_ne (hd i₀ hi₀A) (Ne.symm hi₀)
    by_cases hcrit : ∃ U ⊆ A, U.Nonempty ∧ U ≠ A ∧ dem d U = cap s (nbhdOn B E U)
    · obtain ⟨U, hUA, hUne, hUA', hU⟩ := hcrit
      exact key d s U hUA hUne hUA' hd hs hall hU
    push_neg at hcrit
    have hstrict : ∀ U ⊆ A, U.Nonempty → U ≠ A → dem d U < cap s (nbhdOn B E U) :=
      fun U hUA hUne hUA' => lt_of_le_of_ne (hall U hUA) (hcrit U hUA hUne hUA')
    -- pick an eligible source with positive capacity for `i₀`
    have hsing : d i₀ ≤ cap s (nbhdOn B E {i₀}) := by
      have h := hall {i₀} (by simpa using hi₀A)
      simpa [dem] using h
    have hj₀ex : ∃ j₀ ∈ nbhdOn B E {i₀}, 0 < s j₀ := by
      by_contra hcon
      push_neg at hcon
      have : cap s (nbhdOn B E {i₀}) ≤ 0 := Finset.sum_nonpos hcon
      linarith
    obtain ⟨j₀, hj₀mem, hj₀pos⟩ := hj₀ex
    have hj₀B : j₀ ∈ B := (mem_nbhdOn.1 hj₀mem).1
    have hEj₀ : E j₀ i₀ := by
      obtain ⟨_, i, hi, hE⟩ := mem_nbhdOn.1 hj₀mem
      rw [Finset.mem_singleton.1 hi] at hE
      exact hE
    have hj₀nb : ∀ U : Finset σ, i₀ ∈ U → j₀ ∈ nbhdOn B E U :=
      fun U hU => mem_nbhdOn.2 ⟨hj₀B, i₀, hU, hEj₀⟩
    -- the perturbation size
    obtain ⟨slacks, hslacks⟩ : ∃ T : Finset ℝ, T =
        ((A.powerset.filter (fun U => U.Nonempty ∧ i₀ ∉ U ∧ j₀ ∈ nbhdOn B E U)).image
          (fun U => cap s (nbhdOn B E U) - dem d U)) := ⟨_, rfl⟩
    obtain ⟨cands, hcands⟩ : ∃ T : Finset ℝ, T = insert (d i₀) (insert (s j₀) slacks) :=
      ⟨_, rfl⟩
    have hcandsne : cands.Nonempty := ⟨d i₀, by rw [hcands]; exact mem_insert_self _ _⟩
    obtain ⟨ε, hε⟩ : ∃ r : ℝ, r = cands.min' hcandsne := ⟨_, rfl⟩
    have hεpos : 0 < ε := by
      rw [hε, Finset.lt_min'_iff]
      intro b hb
      rw [hcands] at hb
      rcases mem_insert.1 hb with rfl | hb
      · exact hd0
      rcases mem_insert.1 hb with rfl | hb
      · exact hj₀pos
      rw [hslacks] at hb
      obtain ⟨U, hU, rfl⟩ := mem_image.1 hb
      rw [mem_filter, mem_powerset] at hU
      obtain ⟨hUA, hUne, hi₀U, -⟩ := hU
      have hUA' : U ≠ A := by rintro rfl; exact hi₀U hi₀A
      have := hstrict U hUA hUne hUA'
      linarith
    have hεd : ε ≤ d i₀ := by
      rw [hε]; exact Finset.min'_le _ _ (by rw [hcands]; exact mem_insert_self _ _)
    have hεs : ε ≤ s j₀ := by
      rw [hε]
      exact Finset.min'_le _ _
        (by rw [hcands]; exact mem_insert_of_mem (mem_insert_self _ _))
    have hεU : ∀ U ⊆ A, U.Nonempty → i₀ ∉ U → j₀ ∈ nbhdOn B E U →
        ε ≤ cap s (nbhdOn B E U) - dem d U := by
      intro U hUA hUne hi₀U hj₀U
      rw [hε]
      refine Finset.min'_le _ _ ?_
      rw [hcands]
      refine mem_insert_of_mem (mem_insert_of_mem ?_)
      rw [hslacks]
      refine mem_image.2 ⟨U, ?_, rfl⟩
      rw [mem_filter, mem_powerset]
      exact ⟨hUA, hUne, hi₀U, hj₀U⟩
    obtain ⟨d', hd'def⟩ : ∃ f : σ → ℝ, f = Function.update d i₀ (d i₀ - ε) := ⟨_, rfl⟩
    obtain ⟨s', hs'def⟩ : ∃ f : τ → ℝ, f = Function.update s j₀ (s j₀ - ε) := ⟨_, rfl⟩
    have hd'nonneg : ∀ i ∈ A, 0 ≤ d' i := by
      intro i hi
      rw [hd'def]
      by_cases h : i = i₀
      · subst h; rw [Function.update_self]; linarith
      · rw [Function.update_of_ne h]; exact hd i hi
    have hs'nonneg : ∀ j ∈ B, 0 ≤ s' j := by
      intro j hj
      rw [hs'def]
      by_cases h : j = j₀
      · subst h; rw [Function.update_self]; linarith
      · rw [Function.update_of_ne h]; exact hs j hj
    have hall' : ∀ U ⊆ A, dem d' U ≤ cap s' (nbhdOn B E U) := by
      intro U hUA
      have e1 : dem d' U = dem d U - (if i₀ ∈ U then ε else 0) := by
        rw [hd'def]; exact dem_update_sub d i₀ ε U
      have e2 : cap s' (nbhdOn B E U)
          = cap s (nbhdOn B E U) - (if j₀ ∈ nbhdOn B E U then ε else 0) := by
        rw [hs'def]; exact cap_update_sub s j₀ ε _
      rw [e1, e2]
      by_cases hiU : i₀ ∈ U
      · rw [if_pos hiU, if_pos (hj₀nb U hiU)]
        have := hall U hUA
        linarith
      · rw [if_neg hiU, sub_zero]
        by_cases hjU : j₀ ∈ nbhdOn B E U
        · rw [if_pos hjU]
          rcases U.eq_empty_or_nonempty with rfl | hUne
          · simp at hjU
          · have := hεU U hUA hUne hiU hjU
            linarith
        · rw [if_neg hjU, sub_zero]
          exact hall U hUA
    -- solve the perturbed problem, then add `ε` back on the pair `(j₀, i₀)`
    have hperturbed : ∃ x, IsRoutingOn A B E d' s' x := by
      have hmem : ε ∈ cands := by rw [hε]; exact Finset.min'_mem _ _
      rw [hcands] at hmem
      rcases mem_insert.1 hmem with hcase | hmem
      · -- ε = d i₀ : the site `i₀` drops out
        have hd'0 : d' i₀ = 0 := by
          rw [hd'def, Function.update_self, ← hcase]; ring
        have hcard' : (A.erase i₀).card + B.card ≤ n := by
          have h1 : (A.erase i₀).card = A.card - 1 := card_erase_of_mem hi₀A
          have h2 : 1 ≤ A.card := card_pos.2 ⟨i₀, hi₀A⟩
          omega
        obtain ⟨x, hx⟩ := IH (A.erase i₀) B E d' s' hcard'
          (fun i hi => hd'nonneg i (Finset.mem_of_mem_erase hi)) hs'nonneg
          (fun W hW => hall' W (hW.trans (Finset.erase_subset _ _)))
        exact ⟨x, hx.extend_site hd'0⟩
      rcases mem_insert.1 hmem with hcase | hmem
      · -- ε = s j₀ : the source `j₀` drops out
        have hs'0 : s' j₀ = 0 := by
          rw [hs'def, Function.update_self, ← hcase]; ring
        have hcard' : A.card + (B.erase j₀).card ≤ n := by
          have h1 : (B.erase j₀).card = B.card - 1 := card_erase_of_mem hj₀B
          have h2 : 1 ≤ B.card := card_pos.2 ⟨j₀, hj₀B⟩
          omega
        obtain ⟨x, hx⟩ := IH A (B.erase j₀) E d' s' hcard' hd'nonneg
          (fun j hj => hs'nonneg j (Finset.mem_of_mem_erase hj))
          (by
            intro W hW
            have hnb : nbhdOn (B.erase j₀) E W = (nbhdOn B E W).erase j₀ := by
              ext j
              simp only [mem_nbhdOn, Finset.mem_erase, mem_nbhdOn]
              tauto
            rw [hnb]
            by_cases hjW : j₀ ∈ nbhdOn B E W
            · have hEq : cap s' ((nbhdOn B E W).erase j₀) = cap s' (nbhdOn B E W) := by
                rw [cap, cap, ← Finset.add_sum_erase _ s' hjW, hs'0, zero_add]
              rw [hEq]
              exact hall' W hW
            · rw [Finset.erase_eq_of_notMem hjW]
              exact hall' W hW)
        exact ⟨x, hx.extend_source (le_of_eq hs'0.symm)⟩
      · -- ε is the slack of some `U*`, which becomes critical after the perturbation
        rw [hslacks] at hmem
        obtain ⟨U, hU, hUeq⟩ := mem_image.1 hmem
        rw [mem_filter, mem_powerset] at hU
        obtain ⟨hUA, hUne, hi₀U, hj₀U⟩ := hU
        have hUA' : U ≠ A := by rintro rfl; exact hi₀U hi₀A
        have hcritU : dem d' U = cap s' (nbhdOn B E U) := by
          have e1 : dem d' U = dem d U - (if i₀ ∈ U then ε else 0) := by
            rw [hd'def]; exact dem_update_sub d i₀ ε U
          have e2 : cap s' (nbhdOn B E U)
              = cap s (nbhdOn B E U) - (if j₀ ∈ nbhdOn B E U then ε else 0) := by
            rw [hs'def]; exact cap_update_sub s j₀ ε _
          rw [e1, e2, if_neg hi₀U, if_pos hj₀U, sub_zero]
          linarith [hUeq]
        exact key d' s' U hUA hUne hUA' hd'nonneg hs'nonneg hall' hcritU
    obtain ⟨x, hx⟩ := hperturbed
    refine ⟨fun j i => x j i + if j = j₀ ∧ i = i₀ then ε else 0, ?_⟩
    refine routing_bump hi₀A hj₀B hEj₀ (le_of_lt hεpos) (fun j i => rfl) ?_
    rw [← hd'def, ← hs'def]
    exact hx

/-- The capacitated Hall theorem, packaged without the induction parameter. -/
theorem exists_routing_of_hall (A : Finset σ) (B : Finset τ) (E : τ → σ → Bool)
    (d : σ → ℝ) (s : τ → ℝ)
    (hd : ∀ i ∈ A, 0 ≤ d i) (hs : ∀ j ∈ B, 0 ≤ s j)
    (hall : ∀ U ⊆ A, dem d U ≤ cap s (nbhdOn B E U)) :
    ∃ x, IsRoutingOn A B E d s x :=
  exists_routing_of_hall_aux (A.card + B.card) A B E d s le_rfl hd hs hall

end Viridis.Run130.Hall

/- Engine-3 immutable source unit: Certificate.lean -/

/-!
# The Seed-Source Bottleneck Certificate — formal statements of the frozen targets

This file formalizes the preregistered model of `SEALED_paper.tex` (Run-130) and the four
frozen formal targets listed in `STATEMENT_CONTRACT.md`:

* `C1` : `seed_routing_common_fraction_eq_min_cut_ratio`
* `C2` : `seed_routing_feasible_iff_cut_conditions`
* `C3` : `capacity_outside_active_bottleneck_irrelevant`
* `C4` : `scenario_intersection_certificate_le_each_scenario`

## The preregistered model (paper, Section 2)

`σ` is the finite set `I` of restoration sites, `τ` is the finite set `J` of seed sources,
`d : σ → ℝ` are the site demands (the paper assumes `d i > 0`), `s : τ → ℝ` are the source
capacities (the paper assumes `s j ≥ 0`), and `E : τ → σ → Bool` is the frozen eligibility
graph `E ⊆ J × I` (`E j i = true` means the transfer `(j, i)` is eligible).

A routing `x : τ → σ → ℝ` is admissible for the common fulfillment fraction `lam` when it is
nonnegative, supported on `E`, satisfies the supply constraints (paper eq. 1) and the demand
constraints (paper eq. 2). This is `IsFeasibleFraction`.

`certificate E d s` is the right-hand side of the boxed equation (3) of the paper,
`min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`, realized as the minimum of the finite set of reals
`{1} ∪ {S(N(U))/D(U) : ∅ ≠ U ⊆ I}`.

Non-vacuity witnesses for all four targets are in `PaperFormalization/Witnesses.lean`.
-/

namespace Viridis.Run130

open Finset Viridis.Run130.Hall

variable {σ τ : Type*} [Fintype σ] [Fintype τ]

/-! ## Model definitions -/

/-- The eligible neighbourhood `N(U) = {j ∈ J : ∃ i ∈ U, (j,i) ∈ E}` of a set of sites. -/
abbrev nbhd (E : τ → σ → Bool) (U : Finset σ) : Finset τ := nbhdOn Finset.univ E U

/-- `D(U) = ∑_{i ∈ U} d i`. -/
abbrev demand (d : σ → ℝ) (U : Finset σ) : ℝ := dem d U

/-- `S(C) = ∑_{j ∈ C} s j`. -/
abbrev supply (s : τ → ℝ) (C : Finset τ) : ℝ := cap s C

/-- Paper equations (1) and (2): a common fulfillment fraction `lam` is *feasible* when some
nonnegative routing supported on the eligibility graph respects every source capacity and
delivers at least `lam * d i` to every site `i`. -/
def IsFeasibleFraction (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) (lam : ℝ) : Prop :=
  ∃ x : τ → σ → ℝ,
    (∀ j i, 0 ≤ x j i) ∧
    (∀ j i, ¬ E j i → x j i = 0) ∧
    (∀ j, ∑ i, x j i ≤ s j) ∧
    (∀ i, lam * d i ≤ ∑ j, x j i)

/-- The finite set of reals `{1} ∪ {S(N(U))/D(U) : ∅ ≠ U ⊆ I}`. -/
noncomputable def cutRatios (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) : Finset ℝ :=
  insert 1 ((Finset.univ.filter (fun U : Finset σ => U.Nonempty)).image
    (fun U => supply s (nbhd E U) / demand d U))

lemma cutRatios_nonempty (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) :
    (cutRatios E d s).Nonempty := ⟨1, Finset.mem_insert_self _ _⟩

/-- The cut certificate of the paper, boxed equation (3):
`λ* = min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`. -/
noncomputable def certificate (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) : ℝ :=
  (cutRatios E d s).min' (cutRatios_nonempty E d s)

/-! ## Elementary properties of the certificate -/

variable {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ}

lemma ratio_mem_cutRatios {U : Finset σ} (hU : U.Nonempty) :
    supply s (nbhd E U) / demand d U ∈ cutRatios E d s :=
  Finset.mem_insert_of_mem (Finset.mem_image_of_mem _ (by simp [hU]))

lemma certificate_le_one : certificate E d s ≤ 1 :=
  Finset.min'_le _ _ (Finset.mem_insert_self _ _)

lemma certificate_le_ratio {U : Finset σ} (hU : U.Nonempty) :
    certificate E d s ≤ supply s (nbhd E U) / demand d U :=
  Finset.min'_le _ _ (ratio_mem_cutRatios hU)

lemma le_certificate {t : ℝ} (h1 : t ≤ 1)
    (h2 : ∀ U : Finset σ, U.Nonempty → t ≤ supply s (nbhd E U) / demand d U) :
    t ≤ certificate E d s := by
  refine Finset.le_min' _ _ _ ?_
  intro y hy
  rcases Finset.mem_insert.1 hy with rfl | hy
  · exact h1
  · obtain ⟨U, hU, rfl⟩ := Finset.mem_image.1 hy
    exact h2 U (by simpa using hU)

omit [Fintype σ] in
lemma demand_pos {U : Finset σ} (hd : ∀ i, 0 < d i) (hU : U.Nonempty) : 0 < demand d U :=
  Finset.sum_pos (fun i _ => hd i) hU

lemma certificate_nonneg (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    0 ≤ certificate E d s := by
  refine le_certificate zero_le_one ?_
  intro U hU
  exact div_nonneg (cap_nonneg fun j _ => hs j) (demand_pos hd hU).le

/-- `λ* D(U) ≤ S(N(U))` for every nonempty `U`: the certificate satisfies every cut. -/
lemma certificate_mul_demand_le (hd : ∀ i, 0 < d i) {U : Finset σ} (hU : U.Nonempty) :
    certificate E d s * demand d U ≤ supply s (nbhd E U) :=
  (le_div_iff₀ (demand_pos hd hU)).1 (certificate_le_ratio hU)

/-- A convenient way to evaluate the certificate: if `U₀` is nonempty, its ratio is at most
`1`, and its ratio is minimal, then the certificate equals that ratio. -/
lemma certificate_eq_ratio_of_min {U₀ : Finset σ} (hU₀ : U₀.Nonempty)
    (h1 : supply s (nbhd E U₀) / demand d U₀ ≤ 1)
    (hmin : ∀ U : Finset σ, U.Nonempty →
      supply s (nbhd E U₀) / demand d U₀ ≤ supply s (nbhd E U) / demand d U) :
    certificate E d s = supply s (nbhd E U₀) / demand d U₀ :=
  le_antisymm (certificate_le_ratio hU₀) (le_certificate h1 hmin)

/-! ## The two directions of the cut equivalence -/

/-- Any feasible common fraction satisfies every cut condition: `lam D(U) ≤ S(N(U))`.
This is the easy ("min-cut is an upper bound") half of Proposition 1. -/
lemma cut_le_of_feasible {lam : ℝ} (h : IsFeasibleFraction E d s lam) (U : Finset σ) :
    lam * demand d U ≤ supply s (nbhd E U) := by
  obtain ⟨x, hx0, hxsupp, hxcol, hxrow⟩ := h
  have step1 : lam * demand d U ≤ ∑ i ∈ U, ∑ j, x j i := by
    have hms : lam * demand d U = ∑ i ∈ U, lam * d i := Finset.mul_sum ..
    rw [hms]
    exact Finset.sum_le_sum fun i _ => hxrow i
  have step2 : ∑ i ∈ U, ∑ j, x j i = ∑ j, ∑ i ∈ U, x j i := Finset.sum_comm
  have step3 : ∑ j, ∑ i ∈ U, x j i = ∑ j ∈ nbhd E U, ∑ i ∈ U, x j i := by
    refine (Finset.sum_subset (Finset.subset_univ _) ?_).symm
    intro j _ hj
    refine Finset.sum_eq_zero fun i hi => ?_
    refine hxsupp j i ?_
    intro hE
    exact hj (mem_nbhdOn.2 ⟨Finset.mem_univ _, i, hi, hE⟩)
  have step4 : ∑ j ∈ nbhd E U, ∑ i ∈ U, x j i ≤ supply s (nbhd E U) := by
    refine Finset.sum_le_sum fun j _ => ?_
    refine le_trans ?_ (hxcol j)
    exact Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _)
      (fun i _ _ => hx0 j i)
  linarith [step1, step2 ▸ step1, step3 ▸ step2 ▸ step1]

/-- If every cut condition holds for `lam` then `lam` is feasible.  This is the hard
("max-flow attains the min cut") half of Proposition 1; it rests on the capacitated Hall
theorem proved in `PaperFormalization/Hall.lean`. -/
lemma feasible_of_cut_le [DecidableEq σ] [DecidableEq τ] {lam : ℝ} (hlam : 0 ≤ lam) (hd : ∀ i, 0 ≤ d i) (hs : ∀ j, 0 ≤ s j)
    (hcut : ∀ U : Finset σ, U.Nonempty → lam * demand d U ≤ supply s (nbhd E U)) :
    IsFeasibleFraction E d s lam := by
  obtain ⟨x, hx⟩ := exists_routing_of_hall (Finset.univ : Finset σ) (Finset.univ : Finset τ)
    E (fun i => lam * d i) s
    (fun i _ => mul_nonneg hlam (hd i)) (fun j _ => hs j)
    (by
      intro U _
      rcases U.eq_empty_or_nonempty with rfl | hU
      · simp
      · have hmul : dem (fun i => lam * d i) U = lam * demand d U :=
          (Finset.mul_sum ..).symm
        rw [hmul]
        exact hcut U hU)
  refine ⟨x, hx.nonneg, ?_, ?_, ?_⟩
  · intro j i hE
    exact hx.support j i (by tauto)
  · intro j
    exact hx.cols j (Finset.mem_univ _)
  · intro i
    exact le_of_eq (hx.rows i (Finset.mem_univ _)).symm

/-! ## C1 — the cut certificate -/

/-- **C1** (`seed_routing_common_fraction_eq_min_cut_ratio`, paper Proposition 1, boxed
equation (3)).  Under the preregistered continuous one-period model, the maximum common
fulfillment fraction exists and equals
`min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`. -/
theorem seed_routing_common_fraction_eq_min_cut_ratio [DecidableEq σ] [DecidableEq τ]
    (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction E d s lam}
      (certificate E d s) := by
  sorry

/-! ## C2 — the capacitated Hall condition -/

/-- **C2** (`seed_routing_feasible_iff_cut_conditions`, paper equation (4)).  Full demand
(`lam = 1`) is feasible exactly when every nonempty set of sites passes the capacitated Hall
condition `D(U) ≤ S(N(U))`. -/
theorem seed_routing_feasible_iff_cut_conditions [DecidableEq σ] [DecidableEq τ] (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsFeasibleFraction E d s 1 ↔
      ∀ U : Finset σ, U.Nonempty → demand d U ≤ supply s (nbhd E U) := by
  sorry

/-! ## Monotonicity of the certificate -/

/-- Adding capacity cannot decrease the certificate. -/
lemma certificate_mono_capacity {s' : τ → ℝ} (hd : ∀ i, 0 < d i)
    (hss' : ∀ j, s j ≤ s' j) : certificate E d s ≤ certificate E d s' := by
  refine le_certificate certificate_le_one ?_
  intro U hU
  refine le_trans (certificate_le_ratio hU) ?_
  have hden : 0 < demand d U := demand_pos hd hU
  have hnum : supply s (nbhd E U) ≤ supply s' (nbhd E U) :=
    Finset.sum_le_sum fun j _ => hss' j
  gcongr

/-- Adding eligibility edges cannot decrease the certificate. -/
lemma certificate_mono_edges {F : τ → σ → Bool} (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j)
    (hEF : ∀ j i, E j i → F j i) : certificate E d s ≤ certificate F d s := by
  refine le_certificate certificate_le_one ?_
  intro U hU
  refine le_trans (certificate_le_ratio hU) ?_
  have hden : 0 < demand d U := demand_pos hd hU
  have hnum : supply s (nbhd E U) ≤ supply s (nbhd F U) :=
    cap_mono (nbhdOn_mono_edges hEF U) (fun j _ => hs j)
  gcongr

/-! ## C3 — capacity outside an active bottleneck is irrelevant -/

/-- **C3** (`capacity_outside_active_bottleneck_irrelevant`, paper Corollary 1).
Let `U` be a nonempty set of sites attaining the certificate (an *active* minimizing subset)
with `λ* < 1`.  Increasing the capacity of a single source `j₀ ∉ N(U)` cannot improve the
certificate.

Remarks on the hypotheses, kept exactly as the paper states them:
`hlt` (`λ* < 1`) and `hincr` (the perturbation *increases* the capacity) are recorded because
the paper's Corollary 1 states them, but the proof does not use either: for *any* change of
capacity at a single source outside `N(U)` the certificate cannot rise above its old value.
Together with `certificate_mono_capacity`, `hincr` upgrades this to the equality
`capacity_outside_active_bottleneck_eq` below. -/
theorem capacity_outside_active_bottleneck_irrelevant {s' : τ → ℝ} {U : Finset σ} {j₀ : τ}
    (hU : U.Nonempty)
    (hactive : certificate E d s = supply s (nbhd E U) / demand d U)
    (hlt : certificate E d s < 1)
    (hj₀ : j₀ ∉ nbhd E U)
    (hoff : ∀ j, j ≠ j₀ → s' j = s j)
    (hincr : s j₀ ≤ s' j₀) :
    certificate E d s' ≤ certificate E d s := by
  sorry

/-- The equality form of **C3**: adding capacity at a source outside the neighbourhood of an
active minimizing subset leaves the certificate exactly unchanged. -/
theorem capacity_outside_active_bottleneck_eq {s' : τ → ℝ} {U : Finset σ} {j₀ : τ}
    (hd : ∀ i, 0 < d i)
    (hU : U.Nonempty)
    (hactive : certificate E d s = supply s (nbhd E U) / demand d U)
    (hlt : certificate E d s < 1)
    (hj₀ : j₀ ∉ nbhd E U)
    (hoff : ∀ j, j ≠ j₀ → s' j = s j)
    (hincr : s j₀ ≤ s' j₀) :
    certificate E d s' = certificate E d s := by
  refine le_antisymm
    (capacity_outside_active_bottleneck_irrelevant hU hactive hlt hj₀ hoff hincr) ?_
  refine certificate_mono_capacity hd ?_
  intro j
  by_cases h : j = j₀
  · subst h; exact hincr
  · exact le_of_eq (hoff j h).symm

/-! ## C4 — scenario robustness -/

/-- The intersection `E_∩ = ⋂_k E_k` of a finite family of scenario eligibility graphs. -/
def scenarioIntersection {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) : τ → σ → Bool :=
  fun j i => decide (∀ k, Es k j i)

/-- The union `E_∪ = ⋃_k E_k` of a finite family of scenario eligibility graphs. -/
def scenarioUnion {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) : τ → σ → Bool :=
  fun j i => decide (∃ k, Es k j i)

omit [Fintype σ] [Fintype τ] in
lemma scenarioIntersection_subset {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) (k : κ) :
    ∀ j i, scenarioIntersection Es j i → Es k j i := by
  intro j i h
  simpa using (of_decide_eq_true h) k

omit [Fintype σ] [Fintype τ] in
lemma subset_scenarioUnion {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) (k : κ) :
    ∀ j i, Es k j i → scenarioUnion Es j i := by
  intro j i h
  exact decide_eq_true ⟨k, h⟩

/-- **C4** (`scenario_intersection_certificate_le_each_scenario`, paper equation (5)).
The certificate of the intersection of the scenario eligibility graphs cannot exceed the
certificate of any individual scenario. -/
theorem scenario_intersection_certificate_le_each_scenario {κ : Type*} [Fintype κ]
    (Es : κ → τ → σ → Bool) (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) (k : κ) :
    certificate (scenarioIntersection Es) d s ≤ certificate (Es k) d s := by
  sorry

/-- Companion to C4: every scenario certificate is at most the certificate of the union,
which is the precise sense in which the union "can be falsely reassuring". -/
theorem scenario_certificate_le_union {κ : Type*} [Fintype κ]
    (Es : κ → τ → σ → Bool) (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) (k : κ) :
    certificate (Es k) d s ≤ certificate (scenarioUnion Es) d s :=
  certificate_mono_edges hd hs (subset_scenarioUnion Es k)

end Viridis.Run130

/- Engine-3 immutable source unit: Witnesses.lean -/

/-!
# Non-vacuity witnesses

Explicit instances showing that the hypotheses of each frozen target `C1`–`C4` are
satisfiable and that the conclusions are non-trivial.

All witnesses use the paper's own negative control (Section 3.1 of `SEALED_paper.tex`):
two unit-demand sites, two sources with capacities `(1/10, 19/10)`, and the "private"
eligibility graph in which source `j` may serve site `i` only if `j = i`.  Total inventory
equals total demand, yet the certified common fulfillment fraction is `1/10`.
-/

namespace Viridis.Run130.Witnesses

open Finset Viridis.Run130 Viridis.Run130.Hall

/-- Two restoration sites, each with unit demand. -/
noncomputable def d2 : Fin 2 → ℝ := fun _ => 1

/-- Two seed sources with capacities `0.1` and `1.9`; total inventory `2` equals total
demand `2`. -/
noncomputable def s2 : Fin 2 → ℝ := fun j => if j = 0 then 1 / 10 else 19 / 10

/-- The "private" eligibility graph: source `j` is eligible for site `i` iff `j = i`. -/
def Epriv : Fin 2 → Fin 2 → Bool := fun j i => decide (j = i)

/-- The complete eligibility graph: every source is eligible for every site. -/
def Efull : Fin 2 → Fin 2 → Bool := fun _ _ => true

/-- A capacity vector that adds a large amount of capacity at source `1`. -/
noncomputable def s2' : Fin 2 → ℝ := fun j => if j = 0 then 1 / 10 else 100

lemma d2_pos : ∀ i, 0 < d2 i := by
  intro i; norm_num [d2]

lemma s2_nonneg : ∀ j, 0 ≤ s2 j := by
  intro j; by_cases h : j = 0 <;> norm_num [s2, h]

lemma s2'_nonneg : ∀ j, 0 ≤ s2' j := by
  intro j; by_cases h : j = 0 <;> norm_num [s2', h]

lemma nbhd_Epriv (U : Finset (Fin 2)) : nbhd Epriv U = U := by
  ext j; simp [Epriv]

lemma nbhd_Efull {U : Finset (Fin 2)} (hU : U.Nonempty) :
    nbhd Efull U = (Finset.univ : Finset (Fin 2)) := by
  obtain ⟨i, hi⟩ := hU
  ext j
  simp only [mem_nbhdOn, Finset.mem_univ, true_and, iff_true]
  exact ⟨i, hi, rfl⟩

/-- The three nonempty subsets of a two-element site set. -/
lemma sites_cases (U : Finset (Fin 2)) (hU : U.Nonempty) :
    U = {0} ∨ U = {1} ∨ U = {0, 1} := by
  revert hU
  revert U
  decide

/-! ## The negative control: adequate total inventory, ten-percent common fulfillment -/

lemma total_supply_eq_total_demand :
    supply s2 (Finset.univ : Finset (Fin 2)) = demand d2 (Finset.univ : Finset (Fin 2)) := by
  simp [cap, dem, s2, d2, Fin.sum_univ_two]
  norm_num

lemma ratio_priv_singleton_zero :
    supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = 1 / 10 := by
  rw [nbhd_Epriv]
  norm_num [cap, dem, s2, d2]

/-- The certificate of the paper's negative control is exactly `1/10`. -/
theorem certificate_priv : certificate Epriv d2 s2 = 1 / 10 := by
  rw [show (1 / 10 : ℝ) = supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) from
    ratio_priv_singleton_zero.symm]
  refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
  · rw [ratio_priv_singleton_zero]; norm_num
  · intro U hU
    rw [ratio_priv_singleton_zero, nbhd_Epriv]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2, d2]
    · norm_num [cap, dem, s2, d2]
    · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl]
      norm_num [cap, dem, s2, d2, Fin.sum_univ_two]

/-- **Non-vacuity for C1.** The hypotheses of `seed_routing_common_fraction_eq_min_cut_ratio`
are satisfiable, and in the paper's negative control the maximum common fulfillment fraction
is genuinely `1/10` — even though total inventory equals total demand. -/
theorem C1_witness :
    IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction Epriv d2 s2 lam} (1 / 10) := by
  have h := seed_routing_common_fraction_eq_min_cut_ratio (E := Epriv) (d := d2) (s := s2)
    d2_pos s2_nonneg
  rwa [certificate_priv] at h

/-- The maximum common fraction of the negative control is strictly below `1`, so `C1_witness`
is not the trivial instance. -/
theorem C1_witness_nontrivial : (1 : ℝ) / 10 < 1 := by norm_num

/-! ## C2 witnesses: both sides of the equivalence are realized -/

/-- **Non-vacuity for C2, negative side.** Full demand is *not* routable in the negative
control, and correspondingly the capacitated Hall condition fails for `U = {0}`. -/
theorem C2_witness_infeasible :
    ¬ IsFeasibleFraction Epriv d2 s2 1 ∧
      ¬ (∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Epriv U)) := by
  have hfail : ¬ (∀ U : Finset (Fin 2), U.Nonempty →
      demand d2 U ≤ supply s2 (nbhd Epriv U)) := by
    intro h
    have h0 := h {0} ⟨0, by simp⟩
    rw [nbhd_Epriv] at h0
    norm_num [cap, dem, s2, d2] at h0
  refine ⟨?_, hfail⟩
  intro hfeas
  exact hfail ((seed_routing_feasible_iff_cut_conditions d2_pos s2_nonneg).1 hfeas)

/-- **Non-vacuity for C2, positive side.** With the same demands and the same total
inventory, but a complete eligibility graph, full demand *is* routable. -/
theorem C2_witness_feasible :
    IsFeasibleFraction Efull d2 s2 1 ∧
      (∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Efull U)) := by
  have hhall : ∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Efull U) := by
    intro U hU
    rw [nbhd_Efull hU]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  exact ⟨(seed_routing_feasible_iff_cut_conditions d2_pos s2_nonneg).2 hhall, hhall⟩

/-! ## C3 witness -/

/-- The certificate is unchanged by adding a large amount of capacity at source `1`, which
lies outside the eligible neighbourhood of the active bottleneck `U = {0}`. -/
theorem certificate_priv' : certificate Epriv d2 s2' = 1 / 10 := by
  have hratio : supply s2' (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = 1 / 10 := by
    rw [nbhd_Epriv]
    norm_num [cap, dem, s2', d2]
  rw [show (1 / 10 : ℝ) = supply s2' (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) from
    hratio.symm]
  refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
  · rw [hratio]; norm_num
  · intro U hU
    rw [hratio, nbhd_Epriv]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2', d2]
    · norm_num [cap, dem, s2', d2]
    · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl]
      norm_num [cap, dem, s2', d2, Fin.sum_univ_two]

/-- **Non-vacuity for C3.** All hypotheses of
`capacity_outside_active_bottleneck_irrelevant` are satisfied by the negative control with
active bottleneck `U = {0}` and the outside source `j₀ = 1`; the conclusion is realized as
the equality `1/10 = 1/10`, i.e. adding `98.1` units of capacity at source `1` provably does
not help. -/
theorem C3_witness :
    ({0} : Finset (Fin 2)).Nonempty ∧
    certificate Epriv d2 s2 = supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) ∧
    certificate Epriv d2 s2 < 1 ∧
    (1 : Fin 2) ∉ nbhd Epriv {0} ∧
    (∀ j, j ≠ 1 → s2' j = s2 j) ∧
    s2 1 ≤ s2' 1 ∧
    certificate Epriv d2 s2' = certificate Epriv d2 s2 := by
  refine ⟨⟨0, by simp⟩, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [certificate_priv, ratio_priv_singleton_zero]
  · rw [certificate_priv]; norm_num
  · rw [nbhd_Epriv]; decide
  · intro j hj
    have hj0 : j = 0 := by revert hj; revert j; decide
    subst hj0
    norm_num [s2, s2']
  · norm_num [s2, s2']
  · rw [certificate_priv, certificate_priv']

/-! ## The negative control in general form (paper claim C130-06)

"Adequate total seed inventory can coexist with an arbitrarily small common fulfillment
fraction when eligibility neighborhoods are imbalanced." -/

/-- Capacities `(e, 2 - e)` for a parameter `e`; total inventory is always `2`, which equals
total demand for `d2`. -/
noncomputable def sEps (e : ℝ) : Fin 2 → ℝ := fun j => if j = 0 then e else 2 - e

lemma sEps_nonneg {e : ℝ} (he0 : 0 < e) (he1 : e ≤ 1) : ∀ j, 0 ≤ sEps e j := by
  intro j
  by_cases h : j = 0 <;> simp only [sEps, h, if_true, if_false] <;> linarith

lemma sEps_total {e : ℝ} :
    supply (sEps e) (Finset.univ : Finset (Fin 2))
      = demand d2 (Finset.univ : Finset (Fin 2)) := by
  simp [cap, dem, sEps, d2, Fin.sum_univ_two]

/-- **Arbitrarily severe negative control.**  For every `0 < e ≤ 1` the two-site, two-source
instance with private eligibility and capacities `(e, 2 - e)` has total inventory equal to
total demand, yet its maximum common fulfillment fraction is exactly `e`. -/
theorem negative_control_arbitrarily_severe {e : ℝ} (he0 : 0 < e) (he1 : e ≤ 1) :
    supply (sEps e) (Finset.univ : Finset (Fin 2))
        = demand d2 (Finset.univ : Finset (Fin 2)) ∧
      IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction Epriv d2 (sEps e) lam} e := by
  have hratio : supply (sEps e) (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = e := by
    rw [nbhd_Epriv]
    norm_num [cap, dem, sEps, d2]
  have hcert : certificate Epriv d2 (sEps e) = e := by
    have h0 : certificate Epriv d2 (sEps e)
        = supply (sEps e) (nbhd Epriv ({0} : Finset (Fin 2)))
            / demand d2 ({0} : Finset (Fin 2)) := by
      refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
      · rw [hratio]; exact he1
      · intro U hU
        rw [hratio, nbhd_Epriv]
        rcases sites_cases U hU with rfl | rfl | rfl
        · norm_num [cap, dem, sEps, d2]
        · rw [show supply (sEps e) ({1} : Finset (Fin 2))
              / demand d2 ({1} : Finset (Fin 2)) = 2 - e by norm_num [cap, dem, sEps, d2]]
          linarith
        · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl,
            show supply (sEps e) (Finset.univ : Finset (Fin 2))
              / demand d2 (Finset.univ : Finset (Fin 2)) = 1 by
                norm_num [cap, dem, sEps, d2, Fin.sum_univ_two]]
          exact he1
    rw [h0, hratio]
  refine ⟨sEps_total, ?_⟩
  have h := seed_routing_common_fraction_eq_min_cut_ratio (E := Epriv) (d := d2)
    (s := sEps e) d2_pos (sEps_nonneg he0 he1)
  rwa [hcert] at h

/-! ## C4 witnesses -/

/-- Two scenarios: the complete eligibility graph and the "private" one. -/
def Es2 : Fin 2 → Fin 2 → Fin 2 → Bool := fun k => if k = 0 then Efull else Epriv

lemma scenarioIntersection_Es2 : scenarioIntersection Es2 = Epriv := by decide

lemma scenarioUnion_Es2 : scenarioUnion Es2 = Efull := by decide

theorem certificate_full : certificate Efull d2 s2 = 1 := by
  refine le_antisymm certificate_le_one (le_certificate le_rfl ?_)
  intro U hU
  rw [nbhd_Efull hU]
  rcases sites_cases U hU with rfl | rfl | rfl
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]

/-- **Non-vacuity for C4.** For the two-scenario family `Es2`, the intersection certificate
is `1/10`, strictly below the certificate `1` of scenario `0`, and equal to the certificate
of scenario `1`.  Moreover the *union* certificate is `1`: the union is falsely reassuring,
exactly as the paper's scenario-robustness section asserts. -/
theorem C4_witness :
    certificate (scenarioIntersection Es2) d2 s2 = 1 / 10 ∧
    certificate (Es2 0) d2 s2 = 1 ∧
    certificate (Es2 1) d2 s2 = 1 / 10 ∧
    certificate (scenarioUnion Es2) d2 s2 = 1 ∧
    certificate (scenarioIntersection Es2) d2 s2 < certificate (Es2 0) d2 s2 := by
  have h0 : Es2 0 = Efull := by decide
  have h1 : Es2 1 = Epriv := by decide
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [scenarioIntersection_Es2, certificate_priv]
  · rw [h0, certificate_full]
  · rw [h1, certificate_priv]
  · rw [scenarioUnion_Es2, certificate_full]
  · rw [scenarioIntersection_Es2, h0, certificate_priv, certificate_full]
    norm_num

end Viridis.Run130.Witnesses
