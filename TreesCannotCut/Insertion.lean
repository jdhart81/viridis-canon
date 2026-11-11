import Mathlib
import ViridisStatements.P1.Insertion

/-!
# Work towards `P1.Insertion` (L2)

This file proves `ViridisStatements.P1.Insertion.Statement` (`Candidate.main`, at the end).
It is assembled from the following pieces of the insertion step.

* `euler_insert_local`: `Δχ` on inserting `p` depends only on the 3×3 window around `p`.
* `C8_insert`: `C8 (insert p B) = C8 B + 1 - k`, where `k` is the number of
  8-components of `B` that contain an 8-neighbour of `p`.
* `enclosed_insert`: if `B` has finitely many enclosed components, then
  `enclosed (insert p B) = enclosed B - [old component of p is enclosed] + P`, where `P`
  counts the enclosed components of `ℤ² \ insert p B` that contain a 4-neighbour of `p`.
* `finite_enclosed`: a finite raster has finitely many enclosed components (every pixel
  outside a box around `B` has a free horizontal ray), which discharges the hypothesis.
* `invariant_insert` and `statement_of_jordan`: the pieces combined.
* `insertion_hole`: the conclusion of `Statement` in the special case where all four
  4-neighbours of `p` are barrier pixels (filling a one-pixel hole).
* `statement_of_scan`: it suffices to treat insertions in raster-scan order (every pixel of
  `B` lies in an earlier row, or earlier in the row of `p`), since the invariant of the
  empty raster is `0`.
* `invariant_insert_scan`, `statement_of_core`: in scan order the old component of `p` is
  infinite, the only new piece that can be enclosed is the one of `S = p - (0,1)`, and `Δχ`
  and `k` are explicit, except in one configuration. `Statement` follows from the single
  hypothesis `hcore` about that configuration (`S` free, `SE` and one of `W`, `SW` barrier).
* `k_core`, `statement_of_halfplane_jordan`: `hcore` is equivalent to the half-plane Jordan
  lemma `SEnc B p ↔ JoinLR B p`, so `Statement` follows from it; and
  `bridge_of_halfplane_jordan` gives the bridge equation `enc = C8 − χ` from it as well.
* `senc_of_join`: one direction of the half-plane Jordan lemma (if `W` or `SW` is
  8-connected to `SE` in `B`, the component of `S` is finite), by a crossing-parity
  argument for the closed 8-curve through `p`.
* `statement_of_enc_join`: `Statement` from the converse direction alone.
* `invariant_nonneg`, `enclosed_ge`: half of the bridge identity, `enc ≥ C8 − χ` for every
  finite raster (every scan-order insertion changes the invariant by `0` or `+1`).
* `statement_of_le`: `Statement` from the other half, `enc ≤ C8 − χ`.

* `next`, `prev`, `orbit`, `crack_step`, `crack_escape` (2026-11-09): the crack boundary of
  a finite set `C` (pairs `(c, d)` with `c ∈ C`, `c + d ∉ C`) under the (8,4) successor rule.
  `next` has the left inverse `prev`, so it permutes the finite set of cracks and every orbit
  closes. Along the orbit, the outside pixels form a 4-path in the halo of `C`.
* `join_of_senc`: the remaining direction `SEnc B p → JoinLR B p`. If `W`, `SW` are not in the
  8-component `C` of `SE`, then `p` touches `C` only at the corner `SE` and the halo of `C` is
  free. So the crack orbit leads from `S` to `E` without passing `p`, and `E` has a free ray.
* `main`: `Statement`, from `statement_of_enc_join` and `join_of_senc`.
-/

set_option linter.unusedTactic false
set_option linter.unreachableTactic false
set_option linter.unnecessarySeqFocus false

namespace Candidate
open ViridisStatements.P1.Insertion

/-- The 3×3 window around `p`. -/
def inW (p q : Pixel) : Prop := |q.1 - p.1| ≤ 1 ∧ |q.2 - p.2| ≤ 1

instance (p : Pixel) : DecidablePred (inW p) := fun _ => by unfold inW; infer_instance

/-- The part of `B` inside the 3×3 window around `p`. -/
def win (B : Finset Pixel) (p : Pixel) : Finset Pixel := B.filter (inW p)

lemma card_insert_biUnion (B : Finset Pixel) (p : Pixel) (f : Pixel → Finset (ℤ × ℤ)) :
    (((insert p B).biUnion f).card : ℤ) = ((B.biUnion f).card : ℤ) + (f p \ B.biUnion f).card := by
  rw [Finset.biUnion_insert, Finset.union_comm, ← Finset.union_sdiff_self_eq_union,
    Finset.card_union_of_disjoint Finset.disjoint_sdiff]
  push_cast; ring

/-- Locality of new cells: a cell of `f p` lies in `f q` only for `q` in the window. -/
lemma sdiff_local (B : Finset Pixel) (p : Pixel) (f : Pixel → Finset (ℤ × ℤ))
    (hf : ∀ q c, c ∈ f p → c ∈ f q → inW p q) :
    f p \ B.biUnion f = f p \ (win B p).biUnion f := by
  ext c
  simp only [Finset.mem_sdiff, Finset.mem_biUnion, win, Finset.mem_filter]
  constructor
  · rintro ⟨h1, h2⟩; exact ⟨h1, fun ⟨q, ⟨hq, _⟩, hc⟩ => h2 ⟨q, hq, hc⟩⟩
  · rintro ⟨h1, h2⟩; exact ⟨h1, fun ⟨q, hq, hc⟩ => h2 ⟨q, ⟨hq, hf q c h1 hc⟩, hc⟩⟩

lemma win_not_mem (B : Finset Pixel) (p : Pixel) (hp : p ∉ B) : p ∉ win B p := by
  simp [win, hp]

/-- `Δχ` in terms of the new cells. -/
lemma euler_insert (B : Finset Pixel) (p : Pixel) (hp : p ∉ B) :
    euler (insert p B) - euler B =
      ((corners p \ vertices B).card : ℤ)
        - (((({(p.1, p.2), (p.1, p.2 + 1)} : Finset (ℤ × ℤ)) \ hEdges B).card : ℤ)
          + (({(p.1, p.2), (p.1 + 1, p.2)} : Finset (ℤ × ℤ)) \ vEdges B).card) + 1 := by
  unfold euler vertices hEdges vEdges
  rw [card_insert_biUnion, card_insert_biUnion, card_insert_biUnion (f := fun p => {(p.1, p.2), (p.1 + 1, p.2)}),
    Finset.card_insert_of_notMem hp]
  push_cast; ring

/-- **Locality of `Δχ`.** The change of `euler` on inserting `p` depends only on the
3×3 window around `p`. -/
theorem euler_insert_local (B : Finset Pixel) (p : Pixel) (hp : p ∉ B) :
    euler (insert p B) - euler B = euler (insert p (win B p)) - euler (win B p) := by
  rw [euler_insert B p hp, euler_insert _ p (win_not_mem B p hp)]
  unfold vertices hEdges vEdges
  rw [sdiff_local B p corners, sdiff_local B p (fun p => {(p.1, p.2), (p.1, p.2 + 1)}),
    sdiff_local B p (fun p => {(p.1, p.2), (p.1 + 1, p.2)})]
  all_goals
    intro q c h1 h2
    simp only [corners, Finset.mem_insert, Finset.mem_singleton, Prod.ext_iff] at h1 h2
    unfold inW
    rw [abs_le, abs_le]
    omega


section C8

variable (B : Finset Pixel) (p : Pixel)

lemma barrier_adj_iff (B : Finset Pixel) (a b : (B : Set Pixel)) :
    (barrierGraph B).Adj a b ↔ G8.Adj a.1 b.1 := by
  exact Iff.rfl

lemma subset_insert' : (B : Set Pixel) ⊆ ((insert p B : Finset Pixel) : Set Pixel) := by
  intro x hx; simp only [Finset.coe_insert]; exact Set.mem_insert_of_mem _ hx

/-- The inclusion of `B` into `insert p B`, as a graph homomorphism. -/
def incl : barrierGraph B →g barrierGraph (insert p B) where
  toFun v := ⟨v.1, subset_insert' B p v.2⟩
  map_rel' h := by rw [barrier_adj_iff] at h ⊢; exact h

/-- The component of `v` touches `p`. -/
def Touch (v : (B : Set Pixel)) : Prop :=
  ∃ u : (B : Set Pixel), (barrierGraph B).Reachable v u ∧ G8.Adj p u.1

lemma walk_lemma (v : (B : Set Pixel)) (y : ((insert p B : Finset Pixel) : Set Pixel))
    (h : (barrierGraph (insert p B)).Reachable (incl B p v) y) :
    (∃ y0 : (B : Set Pixel), y.1 = y0.1 ∧ (barrierGraph B).Reachable v y0) ∨ Touch B p v := by
  rw [SimpleGraph.reachable_iff_reflTransGen] at h
  induction h with
  | refl => exact Or.inl ⟨v, rfl, SimpleGraph.Reachable.refl _⟩
  | @tail y z _ hyz ih =>
    rcases ih with ⟨y0, hy, hr⟩ | ht
    · rw [barrier_adj_iff] at hyz
      by_cases hz : z.1 = p
      · right
        exact ⟨y0, hr, by rw [← hz, ← hy]; exact hyz.symm⟩
      · have hzB : z.1 ∈ (B : Set Pixel) := by
          have := z.2
          simp only [Finset.coe_insert, Set.mem_insert_iff] at this
          exact this.resolve_left hz
        left
        refine ⟨⟨z.1, hzB⟩, rfl, hr.trans (SimpleGraph.Adj.reachable ?_)⟩
        rw [barrier_adj_iff]; rw [← hy]; exact hyz
    · exact Or.inr ht


/-- The component `c` of `B` touches `p`. -/
def TouchC (c : (barrierGraph B).ConnectedComponent) : Prop :=
  ∃ u : (B : Set Pixel), (barrierGraph B).connectedComponentMk u = c ∧ G8.Adj p u.1

lemma touchC_mk (v : (B : Set Pixel)) :
    TouchC B p ((barrierGraph B).connectedComponentMk v) ↔ Touch B p v := by
  constructor
  · rintro ⟨u, hu, ha⟩
    exact ⟨u, (SimpleGraph.ConnectedComponent.eq.1 hu).symm, ha⟩
  · rintro ⟨u, hu, ha⟩
    exact ⟨u, (SimpleGraph.ConnectedComponent.eq.2 hu).symm, ha⟩

/-- The inserted pixel, as a vertex of `insert p B`. -/
def pv : ((insert p B : Finset Pixel) : Set Pixel) := ⟨p, by simp⟩

lemma map_eq_p_iff (hp : p ∉ B) (c : (barrierGraph B).ConnectedComponent) :
    c.map (incl B p) = (barrierGraph (insert p B)).connectedComponentMk (pv B p) ↔ TouchC B p c := by
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h v =>
    rw [SimpleGraph.ConnectedComponent.map_mk, SimpleGraph.ConnectedComponent.eq, touchC_mk]
    constructor
    · intro h
      rcases walk_lemma B p v _ h with ⟨y0, hy, -⟩ | ht
      · exact absurd (show p ∈ B from by have := y0.2; simp only [pv] at hy; rw [hy]; exact this) hp
      · exact ht
    · rintro ⟨u, hu, ha⟩
      refine ((hu.map (incl B p))).trans (SimpleGraph.Adj.reachable ?_)
      rw [barrier_adj_iff]; exact ha.symm

lemma map_inj_of_not_touch (c1 c2 : (barrierGraph B).ConnectedComponent)
    (h : c1.map (incl B p) = c2.map (incl B p)) (h1 : ¬ TouchC B p c1) : c1 = c2 := by
  induction c1 using SimpleGraph.ConnectedComponent.ind with
  | h v1 =>
  induction c2 using SimpleGraph.ConnectedComponent.ind with
  | h v2 =>
    rw [SimpleGraph.ConnectedComponent.map_mk, SimpleGraph.ConnectedComponent.map_mk,
      SimpleGraph.ConnectedComponent.eq] at h
    rw [touchC_mk] at h1
    rcases walk_lemma B p v1 _ h with ⟨y0, hy, hr⟩ | ht
    · have : v2 = y0 := Subtype.ext hy
      subst this
      exact SimpleGraph.ConnectedComponent.eq.2 hr
    · exact absurd ht h1

lemma map_surj (c : (barrierGraph (insert p B)).ConnectedComponent) :
    c = (barrierGraph (insert p B)).connectedComponentMk (pv B p) ∨
      ∃ c0 : (barrierGraph B).ConnectedComponent, c0.map (incl B p) = c := by
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h y =>
    by_cases hy : y.1 = p
    · left
      have : y = pv B p := Subtype.ext hy
      rw [this]
    · right
      have hyB : y.1 ∈ (B : Set Pixel) := by
        have := y.2
        simp only [Finset.coe_insert, Set.mem_insert_iff] at this
        exact this.resolve_left hy
      exact ⟨(barrierGraph B).connectedComponentMk ⟨y.1, hyB⟩, rfl⟩

/-- **`ΔC8 = 1 − k`**, where `k` counts the 8-components of `B` that touch `p`. -/
theorem C8_insert (hp : p ∉ B) :
    (C8 (insert p B) : ℤ) = C8 B + 1 - Nat.card {c // TouchC B p c} := by
  classical
  let f : Option {c // ¬ TouchC B p c} → (barrierGraph (insert p B)).ConnectedComponent :=
    fun o => match o with
    | none => (barrierGraph (insert p B)).connectedComponentMk (pv B p)
    | some c => c.1.map (incl B p)
  have hf : Function.Bijective f := by
    constructor
    · rintro (_ | ⟨c1, h1⟩) (_ | ⟨c2, h2⟩) h
      · rfl
      · exact absurd ((map_eq_p_iff B p hp c2).1 h.symm) h2
      · exact absurd ((map_eq_p_iff B p hp c1).1 h) h1
      · exact congrArg some (Subtype.ext (map_inj_of_not_touch B p c1 c2 h h1))
    · intro c
      rcases map_surj B p c with h | ⟨c0, h⟩
      · exact ⟨none, h.symm⟩
      · by_cases ht : TouchC B p c0
        · refine ⟨none, ?_⟩
          rw [← h]; exact ((map_eq_p_iff B p hp c0).2 ht).symm
        · exact ⟨some ⟨c0, ht⟩, h⟩
  have e1 : C8 (insert p B) = Nat.card {c // ¬ TouchC B p c} + 1 := by
    rw [C8, ← Nat.card_congr (Equiv.ofBijective f hf), Finite.card_option]
  have e2 : C8 B = Nat.card {c // TouchC B p c} + Nat.card {c // ¬ TouchC B p c} := by
    rw [C8, ← Nat.card_sum, Nat.card_congr (Equiv.sumCompl _)]
  rw [e1, e2]; push_cast; ring

end C8


section Enc

variable (B : Finset Pixel) (p : Pixel)

lemma compl_adj_iff (B : Finset Pixel) (a b : ((B : Set Pixel)ᶜ : Set Pixel)) :
    (complementGraph B).Adj a b ↔ G4.Adj a.1 b.1 := Iff.rfl

lemma compl_subset : (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel) ⊆ (B : Set Pixel)ᶜ := by
  intro x hx; simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or] at hx
  exact hx.2

/-- The inclusion of `ℤ² \ insert p B` into `ℤ² \ B`, as a graph homomorphism. -/
def jincl : complementGraph (insert p B) →g complementGraph B where
  toFun v := ⟨v.1, compl_subset B p v.2⟩
  map_rel' h := by rw [compl_adj_iff] at h ⊢; exact h

lemma jincl_inj : Function.Injective (jincl B p) := by
  intro a b h
  have h2 := congrArg (fun v : ((B : Set Pixel)ᶜ : Set Pixel) => v.1) h
  exact Subtype.ext h2

/-- The component of `x` in `ℤ² \ insert p B` contains a 4-neighbour of `p`. -/
def TouchP (x : (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel)) : Prop :=
  ∃ u, (complementGraph (insert p B)).Reachable x u ∧ G4.Adj p u.1

lemma walk_lemma' (x : (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel))
    (y : ((B : Set Pixel)ᶜ : Set Pixel))
    (h : (complementGraph B).Reachable (jincl B p x) y) :
    (∃ y0, y.1 = (y0 : (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel)).1 ∧
      (complementGraph (insert p B)).Reachable x y0) ∨ TouchP B p x := by
  rw [SimpleGraph.reachable_iff_reflTransGen] at h
  induction h with
  | refl => exact Or.inl ⟨x, rfl, SimpleGraph.Reachable.refl _⟩
  | @tail y z _ hyz ih =>
    rcases ih with ⟨y0, hy, hr⟩ | ht
    · rw [compl_adj_iff] at hyz
      by_cases hz : z.1 = p
      · right
        refine ⟨y0, hr, ?_⟩
        have := hyz.symm; rw [hz, hy] at this; exact this
      · have hzB : z.1 ∈ (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel) := by
          have := z.2
          simp only [Set.mem_compl_iff, Finset.mem_coe] at this
          simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or,
            Finset.mem_coe]
          exact ⟨hz, this⟩
        left
        refine ⟨⟨z.1, hzB⟩, rfl, hr.trans (SimpleGraph.Adj.reachable ?_)⟩
        rw [compl_adj_iff]; rw [← hy]; exact hyz
    · exact Or.inr ht

/-- The component `c` of `ℤ² \ insert p B` contains a 4-neighbour of `p`. -/
def TouchPC (c : (complementGraph (insert p B)).ConnectedComponent) : Prop :=
  ∃ u, (complementGraph (insert p B)).connectedComponentMk u = c ∧ G4.Adj p u.1

lemma touchPC_mk (v) :
    TouchPC B p ((complementGraph (insert p B)).connectedComponentMk v) ↔ TouchP B p v := by
  constructor
  · rintro ⟨u, hu, ha⟩
    exact ⟨u, (SimpleGraph.ConnectedComponent.eq.1 hu).symm, ha⟩
  · rintro ⟨u, hu, ha⟩
    exact ⟨u, (SimpleGraph.ConnectedComponent.eq.2 hu).symm, ha⟩

/-- The inserted pixel, as a vertex of `ℤ² \ B`. -/
def qv (hp : p ∉ B) : ((B : Set Pixel)ᶜ : Set Pixel) := ⟨p, by simpa using hp⟩

/-- The old component of `p`. -/
def cp (hp : p ∉ B) : (complementGraph B).ConnectedComponent :=
  (complementGraph B).connectedComponentMk (qv B p hp)

lemma map_eq_cp_iff (hp : p ∉ B) (c : (complementGraph (insert p B)).ConnectedComponent) :
    c.map (jincl B p) = cp B p hp ↔ TouchPC B p c := by
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h v =>
    rw [SimpleGraph.ConnectedComponent.map_mk, cp, SimpleGraph.ConnectedComponent.eq, touchPC_mk]
    constructor
    · intro h
      rcases walk_lemma' B p v _ h with ⟨y0, hy, -⟩ | ht
      · exfalso
        have := y0.2
        simp only [qv] at hy
        rw [← hy] at this
        simp at this
      · exact ht
    · rintro ⟨u, hu, ha⟩
      refine ((hu.map (jincl B p))).trans (SimpleGraph.Adj.reachable ?_)
      rw [compl_adj_iff]; exact ha.symm

lemma map_inj_of_not_touch' (c1 c2 : (complementGraph (insert p B)).ConnectedComponent)
    (h : c1.map (jincl B p) = c2.map (jincl B p)) (h1 : ¬ TouchPC B p c1) : c1 = c2 := by
  induction c1 using SimpleGraph.ConnectedComponent.ind with
  | h v1 =>
  induction c2 using SimpleGraph.ConnectedComponent.ind with
  | h v2 =>
    rw [SimpleGraph.ConnectedComponent.map_mk, SimpleGraph.ConnectedComponent.map_mk,
      SimpleGraph.ConnectedComponent.eq] at h
    rw [touchPC_mk] at h1
    rcases walk_lemma' B p v1 _ h with ⟨y0, hy, hr⟩ | ht
    · have : v2 = y0 := Subtype.ext hy
      subst this
      exact SimpleGraph.ConnectedComponent.eq.2 hr
    · exact absurd ht h1

lemma map_surj' (hp : p ∉ B) (c : (complementGraph B).ConnectedComponent) (hc : c ≠ cp B p hp) :
    ∃ c0 : (complementGraph (insert p B)).ConnectedComponent, c0.map (jincl B p) = c := by
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h y =>
    have hy : y.1 ≠ p := by
      rintro hy; apply hc; rw [cp]; congr 1; exact Subtype.ext hy
    have hyB : y.1 ∈ (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel) := by
      have := y.2
      simp only [Set.mem_compl_iff, Finset.mem_coe] at this
      simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or, Finset.mem_coe]
      exact ⟨hy, this⟩
    exact ⟨(complementGraph (insert p B)).connectedComponentMk ⟨y.1, hyB⟩, rfl⟩

/-- Away from `p`, components keep their support, so finiteness is preserved. -/
lemma enclosed_map_iff (c : (complementGraph (insert p B)).ConnectedComponent)
    (h1 : ¬ TouchPC B p c) : IsEnclosed (c.map (jincl B p)) ↔ IsEnclosed c := by
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h x =>
    rw [touchPC_mk] at h1
    unfold IsEnclosed
    have hsub : ((complementGraph B).connectedComponentMk (jincl B p x)).supp ⊆
        (jincl B p) '' ((complementGraph (insert p B)).connectedComponentMk x).supp := by
      intro y hy
      rw [SimpleGraph.ConnectedComponent.mem_supp_iff, SimpleGraph.ConnectedComponent.eq] at hy
      rcases walk_lemma' B p x y hy.symm with ⟨y0, hy0, hr⟩ | ht
      · refine ⟨y0, ?_, Subtype.ext hy0.symm⟩
        rw [SimpleGraph.ConnectedComponent.mem_supp_iff, SimpleGraph.ConnectedComponent.eq]
        exact hr.symm
      · exact absurd ht h1
    have hsub2 : ((complementGraph (insert p B)).connectedComponentMk x).supp ⊆
        (jincl B p) ⁻¹' ((complementGraph B).connectedComponentMk (jincl B p x)).supp := by
      intro y hy
      rw [SimpleGraph.ConnectedComponent.mem_supp_iff, SimpleGraph.ConnectedComponent.eq] at hy
      simp only [Set.mem_preimage, SimpleGraph.ConnectedComponent.mem_supp_iff,
        SimpleGraph.ConnectedComponent.eq]
      exact hy.map (jincl B p)
    rw [SimpleGraph.ConnectedComponent.map_mk]
    constructor
    · intro hf
      exact (hf.preimage (jincl_inj B p).injOn).subset hsub2
    · intro hf
      exact (hf.image _).subset hsub


lemma finite_G4_nbrs : Finite {u : Pixel // G4.Adj p u} := by
  have : {u : Pixel | G4.Adj p u} ⊆
      ((Finset.Icc (p.1 - 1) (p.1 + 1) ×ˢ Finset.Icc (p.2 - 1) (p.2 + 1) : Finset Pixel) : Set Pixel) := by
    intro u hu
    simp only [Set.mem_setOf_eq, G4, SimpleGraph.fromRel_adj] at hu
    simp only [Finset.coe_product, Finset.coe_Icc, Set.mem_prod, Set.mem_Icc]
    obtain ⟨-, h | h⟩ := hu
    · have := abs_nonneg (p.1 - u.1); have := abs_nonneg (p.2 - u.2)
      have := le_abs_self (p.1 - u.1); have := neg_abs_le (p.1 - u.1)
      have := le_abs_self (p.2 - u.2); have := neg_abs_le (p.2 - u.2)
      omega
    · have := abs_nonneg (u.1 - p.1); have := abs_nonneg (u.2 - p.2)
      have := le_abs_self (u.1 - p.1); have := neg_abs_le (u.1 - p.1)
      have := le_abs_self (u.2 - p.2); have := neg_abs_le (u.2 - p.2)
      omega
  exact ((Finset.finite_toSet _).subset this).to_subtype

lemma finite_touch : Finite {c // TouchPC B p c} := by
  haveI := finite_G4_nbrs p
  classical
  refine Finite.of_injective (β := {u : Pixel // G4.Adj p u})
    (fun t => ⟨(Classical.choose t.2).1, (Classical.choose_spec t.2).2⟩) ?_
  intro t1 t2 h
  simp only [Subtype.mk.injEq] at h
  have e1 := (Classical.choose_spec t1.2).1
  have e2 := (Classical.choose_spec t2.2).1
  have : Classical.choose t1.2 = Classical.choose t2.2 := Subtype.ext h
  apply Subtype.ext
  rw [← e1, ← e2, this]

open Classical in
/-- **`Δenclosed`, reduced to the pieces of the old component of `p`.** Assuming `B` has
finitely many enclosed components, inserting `p` removes the old component of `p` (counted
if it was enclosed) and adds the enclosed components of `ℤ² \ insert p B` that contain a
4-neighbour of `p`; every other component is unchanged. -/
theorem enclosed_insert (hp : p ∉ B)
    (hfin : Finite {c : (complementGraph B).ConnectedComponent // IsEnclosed c}) :
    (enclosed (insert p B) : ℤ) = enclosed B - (if IsEnclosed (cp B p hp) then 1 else 0)
      + Nat.card {x : {c : (complementGraph (insert p B)).ConnectedComponent // IsEnclosed c} //
          TouchPC B p x.1} := by
  classical
  haveI := finite_touch B p
  let E' := {c : (complementGraph (insert p B)).ConnectedComponent // IsEnclosed c}
  let E := {c : (complementGraph B).ConnectedComponent // IsEnclosed c}
  let f : {x : E' // ¬ TouchPC B p x.1} → {y : E // y.1 ≠ cp B p hp} := fun x =>
    ⟨⟨x.1.1.map (jincl B p), (enclosed_map_iff B p x.1.1 x.2).2 x.1.2⟩,
      fun h => x.2 ((map_eq_cp_iff B p hp x.1.1).1 h)⟩
  have hf : Function.Bijective f := by
    constructor
    · intro x1 x2 h
      have h' : x1.1.1.map (jincl B p) = x2.1.1.map (jincl B p) :=
        congrArg (fun y : {y : E // y.1 ≠ cp B p hp} => y.1.1) h
      exact Subtype.ext (Subtype.ext (map_inj_of_not_touch' B p _ _ h' x1.2))
    · intro y
      obtain ⟨c0, hc0⟩ := map_surj' B p hp y.1.1 y.2
      have ht : ¬ TouchPC B p c0 := fun ht => y.2 (hc0 ▸ (map_eq_cp_iff B p hp c0).2 ht)
      have he : IsEnclosed c0 := (enclosed_map_iff B p c0 ht).1 (hc0 ▸ y.1.2)
      exact ⟨⟨⟨c0, he⟩, ht⟩, Subtype.ext (Subtype.ext hc0)⟩
  haveI : Finite {x : E' // ¬ TouchPC B p x.1} := Finite.of_injective f hf.1
  haveI : Finite {x : E' // TouchPC B p x.1} :=
    Finite.of_injective (β := {c // TouchPC B p c}) (fun x => ⟨x.1.1, x.2⟩)
      (fun x1 x2 h => by
        have h2 := congrArg (fun v : {c // TouchPC B p c} => v.1) h
        exact Subtype.ext (Subtype.ext h2))
  have e1 : enclosed (insert p B) = Nat.card {x : E' // TouchPC B p x.1} +
      Nat.card {x : E' // ¬ TouchPC B p x.1} := by
    rw [enclosed, ← Nat.card_sum, Nat.card_congr (Equiv.sumCompl _)]
  have e2 : enclosed B = Nat.card {y : E // y.1 ≠ cp B p hp} +
      Nat.card {y : E // ¬ y.1 ≠ cp B p hp} := by
    rw [enclosed, ← Nat.card_sum, Nat.card_congr (Equiv.sumCompl _)]
  have e3 : Nat.card {y : E // ¬ y.1 ≠ cp B p hp} = if IsEnclosed (cp B p hp) then 1 else 0 := by
    split_ifs with h
    · rw [Nat.card_eq_one_iff_unique]
      refine ⟨⟨fun a b => ?_⟩, ⟨⟨⟨cp B p hp, h⟩, fun h' => h' rfl⟩⟩⟩
      apply Subtype.ext; apply Subtype.ext
      have ha := a.2; have hb := b.2
      push_neg at ha hb
      rw [ha, hb]
    · rw [Nat.card_eq_zero]
      left
      constructor
      intro a
      have ha := a.2
      push_neg at ha
      exact h (ha ▸ a.1.2)
  rw [e1, e2, e3, Nat.card_congr (Equiv.ofBijective f hf)]
  split_ifs <;> push_cast <;> ring

end Enc


lemma exists_bound (B : Finset Pixel) : ∃ M : ℤ, ∀ b ∈ B, |b.1| < M ∧ |b.2| < M := by
  refine ⟨1 + ∑ b ∈ B, (|b.1| + |b.2|), fun b hb => ?_⟩
  have h := Finset.single_le_sum (f := fun b : Pixel => |b.1| + |b.2|)
    (fun i _ => add_nonneg (abs_nonneg i.1) (abs_nonneg i.2)) hb
  have := abs_nonneg b.1; have := abs_nonneg b.2
  simp only at h
  constructor <;> linarith

/-- Every pixel of an enclosed component lies in a box around `B`. -/
lemma enclosed_in_box (B : Finset Pixel) (M : ℤ) (hM : ∀ b ∈ B, |b.1| < M ∧ |b.2| < M)
    (v : ((B : Set Pixel)ᶜ : Set Pixel))
    (hv : IsEnclosed ((complementGraph B).connectedComponentMk v)) :
    |v.1.1| < M ∧ |v.1.2| < M := by
  have hvB : v.1 ∉ B := by
    have := v.2; simp only [Set.mem_compl_iff, Finset.mem_coe] at this; exact this
  have key : ¬ IsEnclosed ((complementGraph B).connectedComponentMk ⟨v.1, hvB⟩) →
      ¬ IsEnclosed ((complementGraph B).connectedComponentMk v) := fun h => h
  by_contra hc
  apply key _ hv
  rcases le_or_gt M v.1.1 with h1 | h1
  · refine Controls.infinite_of_ray _ _ _ 1 (Or.inl rfl) (Controls.ray_right _ _ ?_)
    intro b hb _
    have := (hM b hb).1
    rw [abs_lt] at this; omega
  rcases le_or_gt v.1.1 (-M) with h2 | h2
  · refine Controls.infinite_of_ray _ _ _ (-1) (Or.inr rfl) (Controls.ray_left _ _ ?_)
    intro b hb _
    have := (hM b hb).1
    rw [abs_lt] at this; omega
  · refine Controls.infinite_of_ray _ _ _ 1 (Or.inl rfl) (Controls.ray_right _ _ ?_)
    intro b hb hb2
    exfalso
    apply hc
    have := (hM b hb).2
    rw [abs_lt] at this ⊢
    rw [abs_lt]
    omega

/-- **Finiteness (F).** A finite raster has finitely many enclosed components. -/
theorem finite_enclosed (B : Finset Pixel) :
    Finite {c : (complementGraph B).ConnectedComponent // IsEnclosed c} := by
  classical
  obtain ⟨M, hM⟩ := exists_bound B
  let box : Finset Pixel := Finset.Icc (-M) M ×ˢ Finset.Icc (-M) M
  let rep : {c : (complementGraph B).ConnectedComponent // IsEnclosed c} →
      ((B : Set Pixel)ᶜ : Set Pixel) := fun c => Classical.choose (Quot.exists_rep c.1)
  have hrep : ∀ c, (complementGraph B).connectedComponentMk (rep c) = c.1 :=
    fun c => Classical.choose_spec (Quot.exists_rep c.1)
  have hbox : ∀ c, (rep c).1 ∈ box := by
    intro c
    have h := enclosed_in_box B M hM (rep c) (by rw [hrep c]; exact c.2)
    rw [abs_lt, abs_lt] at h
    simp only [box, Finset.mem_product, Finset.mem_Icc]
    omega
  refine Finite.of_injective (β := box) (fun c => ⟨(rep c).1, hbox c⟩) ?_
  intro c1 c2 h
  have h' : rep c1 = rep c2 := Subtype.ext (congrArg (fun x : box => x.1) h)
  apply Subtype.ext
  rw [← hrep c1, ← hrep c2, h']


open Classical in
/-- **Reduction of L2.** The change of the invariant equals
`P - [cp enclosed] - (1 - k) + Δχ(window)`. `Statement` therefore follows from the
Jordan-type identity that this quantity is `0`. -/
theorem invariant_insert (B : Finset Pixel) (p : Pixel) (hp : p ∉ B)
    :
    invariant (insert p B) - invariant B =
      ((Nat.card {x : {c : (complementGraph (insert p B)).ConnectedComponent // IsEnclosed c} //
          TouchPC B p x.1} : ℤ) - (if IsEnclosed (cp B p hp) then 1 else 0))
      - (1 - (Nat.card {c // TouchC B p c} : ℤ))
      + (euler (insert p (win B p)) - euler (win B p)) := by
  have h1 := enclosed_insert B p hp (finite_enclosed B)
  have h2 := C8_insert B p hp
  have h3 := euler_insert_local B p hp
  unfold invariant
  rw [h1, h2]
  linarith

/-- The reduction in "hypothesis form": `Statement` follows from the Jordan-type
identity for every insertion. -/
theorem statement_of_jordan
    (hjordan : ∀ (B : Finset Pixel) (p : Pixel) (hp : p ∉ B),
      ((Nat.card {x : {c : (complementGraph (insert p B)).ConnectedComponent // IsEnclosed c} //
          TouchPC B p x.1} : ℤ) - (open Classical in if IsEnclosed (cp B p hp) then 1 else 0))
      - (1 - (Nat.card {c // TouchC B p c} : ℤ))
      + (euler (insert p (win B p)) - euler (win B p)) = 0) :
    Statement := by
  intro B p hp
  have := invariant_insert B p hp
  rw [hjordan B p hp] at this
  linarith

section Hole

variable (B : Finset Pixel) (p : Pixel)

lemma g8_adj_iff (a b : Pixel) : G8.Adj a b ↔ a ≠ b ∧
    (-1 ≤ a.1 - b.1 ∧ a.1 - b.1 ≤ 1) ∧ (-1 ≤ a.2 - b.2 ∧ a.2 - b.2 ≤ 1) := by
  simp only [G8, SimpleGraph.fromRel_adj, abs_le]
  constructor
  · rintro ⟨h, h1 | h1⟩ <;> refine ⟨h, ?_⟩ <;> omega
  · rintro ⟨h, h1⟩; exact ⟨h, Or.inl h1⟩

lemma g4_adj_iff (a b : Pixel) : G4.Adj a b → |a.1 - b.1| + |a.2 - b.2| = 1 := by
  simp only [G4, SimpleGraph.fromRel_adj]
  rintro ⟨-, h | h⟩
  · exact h
  · rw [abs_sub_comm a.1, abs_sub_comm a.2]; exact h

lemma reach (a b : (B : Set Pixel)) (h : a.1 ≠ b.1 ∧
    (-1 ≤ a.1.1 - b.1.1 ∧ a.1.1 - b.1.1 ≤ 1) ∧ (-1 ≤ a.1.2 - b.1.2 ∧ a.1.2 - b.1.2 ≤ 1)) :
    (barrierGraph B).Reachable a b :=
  SimpleGraph.Adj.reachable ((barrier_adj_iff B a b).2 ((g8_adj_iff _ _).2 h))

/-- In the hole case, every 8-component of `B` touching `p` is the component of `N`. -/
lemma touch_eq_N (hn : ∀ u : Pixel, |p.1 - u.1| + |p.2 - u.2| = 1 → u ∈ B)
    (u : (B : Set Pixel)) (hu : G8.Adj p u.1) :
    (barrierGraph B).Reachable u ⟨(p.1, p.2 + 1), hn _ (by simp)⟩ := by
  have hS : (p.1, p.2 - 1) ∈ (B : Set Pixel) := hn _ (by simp)
  have hE : (p.1 + 1, p.2) ∈ (B : Set Pixel) := hn _ (by simp)
  rw [g8_adj_iff] at hu
  obtain ⟨hne, h1, h2⟩ := hu
  have hne' : ¬ (u.1.1 = p.1 ∧ u.1.2 = p.2) := fun h => hne (Prod.ext h.1.symm h.2.symm)
  have SE : (barrierGraph B).Reachable ⟨_, hS⟩ ⟨_, hE⟩ := reach B _ _ (by simp)
  have EN : (barrierGraph B).Reachable ⟨_, hE⟩ ⟨(p.1, p.2 + 1), hn _ (by simp)⟩ :=
    reach B _ _ (by simp)
  by_cases hN : u.1 = (p.1, p.2 + 1)
  · have : u = ⟨(p.1, p.2 + 1), hn _ (by simp)⟩ := Subtype.ext hN
    rw [this]
  by_cases hup : p.2 ≤ u.1.2
  · refine reach B _ _ ⟨hN, ?_, ?_⟩ <;> simp only <;> omega
  by_cases hSu : u.1 = (p.1, p.2 - 1)
  · have : u = ⟨_, hS⟩ := Subtype.ext hSu
    rw [this]; exact SE.trans EN
  · refine (reach B u ⟨_, hS⟩ ⟨hSu, ?_, ?_⟩).trans (SE.trans EN) <;> simp only <;> omega

/-- **L2 in the hole case.** If all four 4-neighbours of `p` are barrier pixels, inserting
`p` leaves the invariant unchanged. -/
theorem insertion_hole (hp : p ∉ B)
    (hn : ∀ u : Pixel, |p.1 - u.1| + |p.2 - u.2| = 1 → u ∈ B) :
    invariant (insert p B) = invariant B := by
  have key := invariant_insert B p hp
  -- no new component touches `p`
  have hP : Nat.card {x : {c : (complementGraph (insert p B)).ConnectedComponent //
      IsEnclosed c} // TouchPC B p x.1} = 0 := by
    rw [Nat.card_eq_zero]; left; constructor
    rintro ⟨x, u, -, hu⟩
    have := u.2
    simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or,
      Finset.mem_coe] at this
    exact this.2 (hn _ (g4_adj_iff _ _ hu))
  -- the old component of `p` is `{p}`, which is enclosed
  have hcp : IsEnclosed (cp B p hp) := Controls.isolated B p hp hn
  -- exactly one 8-component touches `p`
  have hk : Nat.card {c // TouchC B p c} = 1 := by
    have hN : (p.1, p.2 + 1) ∈ (B : Set Pixel) := hn _ (by simp)
    rw [Nat.card_eq_one_iff_unique]
    refine ⟨⟨fun a b => ?_⟩, ⟨⟨_, ⟨_, hN⟩, rfl, (g8_adj_iff _ _).2 (by simp [Prod.ext_iff])⟩⟩⟩
    have key : ∀ x : {c // TouchC B p c}, x.1 = (barrierGraph B).connectedComponentMk ⟨_, hN⟩ := by
      rintro ⟨c, u, rfl, hu⟩
      exact SimpleGraph.ConnectedComponent.eq.2 (touch_eq_N B p hn u hu)
    exact Subtype.ext ((key a).trans (key b).symm)
  -- `Δχ = 1`: every corner and edge of `p` is already present
  have hchi : euler (insert p B) - euler B = 1 := by
    rw [euler_insert B p hp]
    have hS := hn (p.1, p.2 - 1) (by simp)
    have hW := hn (p.1 - 1, p.2) (by simp)
    have hE := hn (p.1 + 1, p.2) (by simp)
    have hN := hn (p.1, p.2 + 1) (by simp)
    have e1 : corners p \ vertices B = ∅ := by
      rw [Finset.sdiff_eq_empty_iff_subset]
      intro c hc
      simp only [vertices, Finset.mem_biUnion]
      simp only [corners, Finset.mem_insert, Finset.mem_singleton] at hc
      rcases hc with rfl | rfl | rfl | rfl
      · exact ⟨_, hS, by simp [corners]⟩
      · exact ⟨_, hS, by simp [corners]⟩
      · exact ⟨_, hN, by simp [corners]⟩
      · exact ⟨_, hN, by simp [corners]⟩
    have e2 : ({(p.1, p.2), (p.1, p.2 + 1)} : Finset (ℤ × ℤ)) \ hEdges B = ∅ := by
      rw [Finset.sdiff_eq_empty_iff_subset]
      intro c hc
      simp only [hEdges, Finset.mem_biUnion]
      simp only [Finset.mem_insert, Finset.mem_singleton] at hc
      rcases hc with rfl | rfl
      · exact ⟨_, hS, by simp⟩
      · exact ⟨_, hN, by simp⟩
    have e3 : ({(p.1, p.2), (p.1 + 1, p.2)} : Finset (ℤ × ℤ)) \ vEdges B = ∅ := by
      rw [Finset.sdiff_eq_empty_iff_subset]
      intro c hc
      simp only [vEdges, Finset.mem_biUnion]
      simp only [Finset.mem_insert, Finset.mem_singleton] at hc
      rcases hc with rfl | rfl
      · exact ⟨_, hW, by simp⟩
      · exact ⟨_, hE, by simp⟩
    rw [e1, e2, e3]; simp
  rw [hP, if_pos hcp, hk, ← euler_insert_local B p hp, hchi] at key
  push_cast at key
  linarith

end Hole

/-- Every pixel of `B` comes before `p` in raster-scan order (row by row, left to right). -/
def Before (B : Finset Pixel) (p : Pixel) : Prop :=
  ∀ q ∈ B, q.2 < p.2 ∨ (q.2 = p.2 ∧ q.1 < p.1)

lemma euler_empty : euler ∅ = 0 := by simp [euler, vertices, hEdges, vEdges]

lemma invariant_empty : invariant ∅ = 0 := by
  rw [invariant, Controls.enclosed_empty, Controls.C8_empty_eq, euler_empty]; simp

/-- The bridge identity from insertions in raster-scan order alone. -/
theorem invariant_zero_of_scan
    (h : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      invariant (insert p B) = invariant B) (B : Finset Pixel) : invariant B = 0 := by
  induction B using Finset.induction_on_max_value (fun q : Pixel => toLex (q.2, q.1)) with
  | h0 => exact invariant_empty
  | step a s ha hmax ih =>
    rw [h s a ha ?_, ih]
    intro q hq
    have h1 := hmax q hq
    have hne : q ≠ a := fun e => ha (e ▸ hq)
    rw [Prod.Lex.toLex_le_toLex] at h1
    rcases h1 with h1 | ⟨h1, h2⟩
    · exact Or.inl h1
    · refine Or.inr ⟨h1, lt_of_le_of_ne h2 fun e => hne (Prod.ext e h1)⟩

/-- `Statement` from insertions in raster-scan order alone. -/
theorem statement_of_scan
    (h : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      invariant (insert p B) = invariant B) : Statement := by
  intro B p _
  rw [invariant_zero_of_scan h, invariant_zero_of_scan h]


section ScanPieces

variable (B : Finset Pixel) (p : Pixel)

lemma cp_not_enclosed (hp : p ∉ B) (hb : Before B p) : ¬ IsEnclosed (cp B p hp) :=
  Controls.infinite_of_ray B p hp 1 (Or.inl rfl) (Controls.ray_right B p fun b hb' h2 => by
    rcases hb b hb' with h | ⟨_, h⟩ <;> omega)

lemma mem_compl_insert {v : Pixel} (h1 : v ≠ p) (h2 : v ∉ B) :
    v ∈ (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel) := by
  simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or, Finset.mem_coe]
  exact ⟨h1, h2⟩

/-- In scan order, a pixel strictly above `p`, or to its right in its row, has a free ray to
the right in `ℤ² \ insert p B`. -/
lemma not_enclosed_above (hb : Before B p) (v : Pixel)
    (hv : p.2 < v.2 ∨ (v.2 = p.2 ∧ p.1 < v.1)) (hv' : v ∉ insert p B) :
    ¬ IsEnclosed ((complementGraph (insert p B)).connectedComponentMk ⟨v, by simpa using hv'⟩) :=
  Controls.infinite_of_ray (insert p B) v hv' 1 (Or.inl rfl)
    (Controls.ray_right (insert p B) v fun b hb' h2 => by
      rw [Finset.mem_insert] at hb'
      rcases hb' with rfl | hb'
      · omega
      · rcases hb b hb' with h | ⟨_, h⟩ <;> omega)

lemma not_mem_above (hb : Before B p) (v : Pixel)
    (hv : p.2 < v.2 ∨ (v.2 = p.2 ∧ p.1 < v.1)) : v ∉ insert p B := by
  intro h
  rw [Finset.mem_insert] at h
  rcases h with rfl | h
  · omega
  · rcases hb v h with h' | h' <;> omega

/-- In scan order, the only new piece around `p` that can be enclosed is the one of `S`. -/
lemma touch_enclosed_eq_S (hb : Before B p)
    (c : (complementGraph (insert p B)).ConnectedComponent) (hc : IsEnclosed c)
    (ht : TouchPC B p c) :
    ∃ hS : (p.1, p.2 - 1) ∉ B,
      c = (complementGraph (insert p B)).connectedComponentMk
        ⟨(p.1, p.2 - 1), mem_compl_insert B p (by simp [Prod.ext_iff]) hS⟩ := by
  obtain ⟨u, rfl, hu⟩ := ht
  have h4 := g4_adj_iff _ _ hu
  have hu' := u.2
  simp only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or,
    Finset.mem_coe] at hu'
  obtain ⟨u1, u2⟩ := u
  obtain ⟨a, b⟩ := u1
  simp only at h4 hu'
  rcases abs_cases (p.1 - a) with ⟨ha, _⟩ | ⟨ha, _⟩ <;>
    rcases abs_cases (p.2 - b) with ⟨hb', _⟩ | ⟨hb', _⟩ <;> rw [ha, hb'] at h4
  · by_cases hab : a = p.1
    · -- `u` is `S`
      have hb2 : b = p.2 - 1 := by omega
      subst hab hb2
      exact ⟨hu'.2, rfl⟩
    · -- `u` is `W`: joined to `NW`, which has a free ray
      exfalso
      have hab : a = p.1 - 1 := by omega
      have hb2 : b = p.2 := by omega
      subst hab hb2
      have hNW := not_mem_above B p hb (p.1 - 1, p.2 + 1) (by simp only; omega)
      apply not_enclosed_above B p hb (p.1 - 1, p.2 + 1) (by simp only; omega) hNW
      have : (complementGraph (insert p B)).connectedComponentMk ⟨(p.1 - 1, p.2 + 1), by simpa using hNW⟩ =
          (complementGraph (insert p B)).connectedComponentMk ⟨(p.1 - 1, p.2), u2⟩ := by
        refine SimpleGraph.ConnectedComponent.eq.2 (SimpleGraph.Adj.reachable ?_)
        rw [compl_adj_iff]
        simp only [G4, SimpleGraph.fromRel_adj, ne_eq, Prod.mk.injEq]
        refine ⟨by omega, Or.inl ?_⟩
        simp
      rw [this]; exact hc
  · -- `u` is `N`
    exfalso
    exact not_enclosed_above B p hb (a, b) (by simp only; omega) (by
      simpa only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or, Finset.mem_coe,
        Finset.mem_insert] using u2) hc
  · -- `u` is `E`
    exfalso
    exact not_enclosed_above B p hb (a, b) (by simp only; omega) (by
      simpa only [Finset.coe_insert, Set.mem_compl_iff, Set.mem_insert_iff, not_or, Finset.mem_coe,
        Finset.mem_insert] using u2) hc
  · exfalso; omega

end ScanPieces


section ScanCount

variable (B : Finset Pixel) (p : Pixel)

/-- `S` is not a barrier pixel and its component in `ℤ² \ insert p B` is enclosed. -/
def SEnc : Prop :=
  ∃ hS : (p.1, p.2 - 1) ∉ B, IsEnclosed ((complementGraph (insert p B)).connectedComponentMk
    ⟨(p.1, p.2 - 1), mem_compl_insert B p (by simp [Prod.ext_iff]) hS⟩)

open Classical in
lemma P_scan (hb : Before B p) :
    Nat.card {x : {c : (complementGraph (insert p B)).ConnectedComponent // IsEnclosed c} //
      TouchPC B p x.1} = if SEnc B p then 1 else 0 := by
  split_ifs with h
  · obtain ⟨hS, he⟩ := h
    rw [Nat.card_eq_one_iff_unique]
    refine ⟨⟨fun a b => ?_⟩, ⟨⟨⟨_, he⟩, ⟨_, rfl, ?_⟩⟩⟩⟩
    · obtain ⟨_, ha⟩ := touch_enclosed_eq_S B p hb a.1.1 a.1.2 a.2
      obtain ⟨_, hb'⟩ := touch_enclosed_eq_S B p hb b.1.1 b.1.2 b.2
      exact Subtype.ext (Subtype.ext (ha.trans hb'.symm))
    · simp only [G4, SimpleGraph.fromRel_adj, ne_eq, Prod.ext_iff]
      refine ⟨by omega, Or.inl ?_⟩
      simp
  · rw [Nat.card_eq_zero]; left; constructor
    intro x
    obtain ⟨hS, hx⟩ := touch_enclosed_eq_S B p hb x.1.1 x.1.2 x.2
    exact h ⟨hS, hx ▸ x.1.2⟩

lemma card_sdiff_eq_sum (s t : Finset (ℤ × ℤ)) :
    ((s \ t).card : ℤ) = ∑ c ∈ s, if c ∈ t then 0 else 1 := by
  rw [Finset.sdiff_eq_filter, Finset.card_filter]; push_cast
  refine Finset.sum_congr rfl fun c _ => ?_
  split_ifs <;> simp_all

lemma mem_vertices (c : ℤ × ℤ) : c ∈ vertices B ↔ ∃ q ∈ B,
    (c.1 = q.1 ∨ c.1 = q.1 + 1) ∧ (c.2 = q.2 ∨ c.2 = q.2 + 1) := by
  simp only [vertices, corners, Finset.mem_biUnion, Finset.mem_insert, Finset.mem_singleton,
    Prod.ext_iff]
  constructor
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩

lemma mem_hEdges (c : ℤ × ℤ) : c ∈ hEdges B ↔ ∃ q ∈ B, c.1 = q.1 ∧ (c.2 = q.2 ∨ c.2 = q.2 + 1) := by
  simp only [hEdges, Finset.mem_biUnion, Finset.mem_insert, Finset.mem_singleton, Prod.ext_iff]
  constructor
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩

lemma mem_vEdges (c : ℤ × ℤ) : c ∈ vEdges B ↔ ∃ q ∈ B, (c.1 = q.1 ∨ c.1 = q.1 + 1) ∧ c.2 = q.2 := by
  simp only [vEdges, Finset.mem_biUnion, Finset.mem_insert, Finset.mem_singleton, Prod.ext_iff]
  constructor
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩
  · rintro ⟨q, hq, h⟩; exact ⟨q, hq, by omega⟩

/-- **`Δχ` in raster-scan order**, with `W, SW, S, SE` the only possible barrier
neighbours of `p`. -/
theorem euler_scan (hp : p ∉ B) (hb : Before B p) :
    euler (insert p B) - euler B =
      (if (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B then 0 else 1)
      + (if (p.1, p.2 - 1) ∈ B ∨ (p.1 + 1, p.2 - 1) ∈ B then 0 else 1)
      - (if (p.1, p.2 - 1) ∈ B then 0 else 1) := by
  rw [euler_insert B p hp, card_sdiff_eq_sum, card_sdiff_eq_sum, card_sdiff_eq_sum]
  have m1 : (p.1, p.2) ∈ vertices B ↔
      (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B := by
    rw [mem_vertices]
    constructor
    · rintro ⟨⟨a, b⟩, hq, h⟩
      have h' := hb _ hq
      simp only at h h'
      have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
      rcases h with ⟨h1 | h1, h2 | h2⟩
      · exact absurd ⟨h1.symm, h2.symm⟩ this
      · have e1 : a = p.1 := by omega
        have e2 : b = p.2 - 1 := by omega
        subst e1 e2; exact Or.inr (Or.inl hq)
      · have e1 : a = p.1 - 1 := by omega
        have e2 : b = p.2 := by omega
        subst e1 e2; exact Or.inl hq
      · have e1 : a = p.1 - 1 := by omega
        have e2 : b = p.2 - 1 := by omega
        subst e1 e2; exact Or.inr (Or.inr hq)
    · rintro (h | h | h) <;> exact ⟨_, h, by simp⟩
  have m2 : (p.1 + 1, p.2) ∈ vertices B ↔ (p.1, p.2 - 1) ∈ B ∨ (p.1 + 1, p.2 - 1) ∈ B := by
    rw [mem_vertices]
    constructor
    · rintro ⟨⟨a, b⟩, hq, h⟩
      have h' := hb _ hq
      have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
      simp only at h h'
      rcases h with ⟨h1 | h1, h2 | h2⟩
      · exfalso; omega
      · have e1 : a = p.1 + 1 := by omega
        have e2 : b = p.2 - 1 := by omega
        subst e1 e2; exact Or.inr hq
      · exfalso; omega
      · have e1 : a = p.1 := by omega
        have e2 : b = p.2 - 1 := by omega
        subst e1 e2; exact Or.inl hq
    · rintro (h | h) <;> exact ⟨_, h, by simp⟩
  have m3 : (p.1, p.2 + 1) ∈ vertices B ↔ (p.1 - 1, p.2) ∈ B := by
    rw [mem_vertices]
    constructor
    · rintro ⟨⟨a, b⟩, hq, h⟩
      have h' := hb _ hq
      have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
      simp only at h h'
      have e1 : a = p.1 - 1 := by omega
      have e2 : b = p.2 := by omega
      subst e1 e2; exact hq
    · intro h; exact ⟨_, h, by simp⟩
  have m4 : (p.1 + 1, p.2 + 1) ∉ vertices B := by
    rw [mem_vertices]
    rintro ⟨⟨a, b⟩, hq, h⟩
    have h' := hb _ hq
    have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
    simp only at h h'
    omega
  have h1 : (p.1, p.2) ∈ hEdges B ↔ (p.1, p.2 - 1) ∈ B := by
    rw [mem_hEdges]
    constructor
    · rintro ⟨⟨a, b⟩, hq, h⟩
      have h' := hb _ hq
      have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
      simp only at h h'
      have e1 : a = p.1 := by omega
      have e2 : b = p.2 - 1 := by omega
      subst e1 e2; exact hq
    · intro h; exact ⟨_, h, by simp⟩
  have h2 : (p.1, p.2 + 1) ∉ hEdges B := by
    rw [mem_hEdges]
    rintro ⟨⟨a, b⟩, hq, h⟩
    have h' := hb _ hq
    have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
    simp only at h h'
    omega
  have v1 : (p.1, p.2) ∈ vEdges B ↔ (p.1 - 1, p.2) ∈ B := by
    rw [mem_vEdges]
    constructor
    · rintro ⟨⟨a, b⟩, hq, h⟩
      have h' := hb _ hq
      have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
      simp only at h h'
      have e1 : a = p.1 - 1 := by omega
      have e2 : b = p.2 := by omega
      subst e1 e2; exact hq
    · intro h; exact ⟨_, h, by simp⟩
  have v2 : (p.1 + 1, p.2) ∉ vEdges B := by
    rw [mem_vEdges]
    rintro ⟨⟨a, b⟩, hq, h⟩
    have h' := hb _ hq
    have : ¬ (a = p.1 ∧ b = p.2) := fun ⟨e1, e2⟩ => hp (by rw [show p = (a, b) from Prod.ext e1.symm e2.symm]; exact hq)
    simp only at h h'
    omega
  rw [corners, Finset.sum_insert (by simp [Prod.ext_iff]), Finset.sum_insert (by simp [Prod.ext_iff]), Finset.sum_insert (by simp [Prod.ext_iff]),
    Finset.sum_singleton, Finset.sum_insert (by simp [Prod.ext_iff]), Finset.sum_singleton,
    Finset.sum_insert (by simp [Prod.ext_iff]), Finset.sum_singleton]
  simp only [m1, m2, m3, m4, h1, h2, v1, v2, if_false]
  split_ifs <;> simp_all

end ScanCount


section ScanFinal

variable (B : Finset Pixel) (p : Pixel)

lemma touch_nbrs (hb : Before B p) (u : (B : Set Pixel)) (hu : G8.Adj p u.1) :
    u.1 = (p.1 - 1, p.2) ∨ u.1 = (p.1 - 1, p.2 - 1) ∨ u.1 = (p.1, p.2 - 1) ∨
      u.1 = (p.1 + 1, p.2 - 1) := by
  rw [g8_adj_iff] at hu
  have h' := hb u.1 u.2
  obtain ⟨hne, h1, h2⟩ := hu
  have hne' : ¬ (u.1.1 = p.1 ∧ u.1.2 = p.2) := fun h => hne (Prod.ext h.1.symm h.2.symm)
  simp only [Prod.ext_iff]
  omega

lemma k_eq_zero (h : ∀ u : (B : Set Pixel), ¬ G8.Adj p u.1) : Nat.card {c // TouchC B p c} = 0 := by
  rw [Nat.card_eq_zero]; left; constructor
  rintro ⟨c, u, -, hu⟩; exact h u hu

lemma k_eq_one (u0 : (B : Set Pixel)) (h0 : G8.Adj p u0.1)
    (h : ∀ u : (B : Set Pixel), G8.Adj p u.1 → (barrierGraph B).Reachable u u0) :
    Nat.card {c // TouchC B p c} = 1 := by
  rw [Nat.card_eq_one_iff_unique]
  refine ⟨⟨fun a b => ?_⟩, ⟨⟨_, u0, rfl, h0⟩⟩⟩
  have key : ∀ x : {c // TouchC B p c}, x.1 = (barrierGraph B).connectedComponentMk u0 := by
    rintro ⟨c, u, rfl, hu⟩
    exact SimpleGraph.ConnectedComponent.eq.2 (h u hu)
  exact Subtype.ext ((key a).trans (key b).symm)

lemma creach {a b : Pixel} (ha : a ∈ (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel))
    (hb : b ∈ (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel))
    (h : |a.1 - b.1| + |a.2 - b.2| = 1) :
    (complementGraph (insert p B)).Reachable ⟨a, ha⟩ ⟨b, hb⟩ := by
  refine SimpleGraph.Adj.reachable ?_
  rw [compl_adj_iff]
  simp only [G4, SimpleGraph.fromRel_adj]
  refine ⟨fun e => ?_, Or.inl h⟩
  rw [e] at h; simp at h

lemma not_SEnc_of_S (hS : (p.1, p.2 - 1) ∈ B) : ¬ SEnc B p := fun ⟨h, _⟩ => h hS

/-- If `S` and `SE` are free, `S` reaches `E`, which has a free ray. -/
lemma not_SEnc_right (hb : Before B p) (hSE : (p.1 + 1, p.2 - 1) ∉ B) : ¬ SEnc B p := by
  rintro ⟨hS, he⟩
  have hE := not_mem_above B p hb (p.1 + 1, p.2) (Or.inr ⟨rfl, by simp⟩)
  have hSE' := mem_compl_insert B p (v := (p.1 + 1, p.2 - 1)) (by simp [Prod.ext_iff]) hSE
  apply not_enclosed_above B p hb (p.1 + 1, p.2) (Or.inr ⟨rfl, by simp⟩) hE
  have : (complementGraph (insert p B)).connectedComponentMk ⟨(p.1 + 1, p.2), by simpa using hE⟩ =
      (complementGraph (insert p B)).connectedComponentMk
        ⟨(p.1, p.2 - 1), mem_compl_insert B p (by simp [Prod.ext_iff]) hS⟩ := by
    refine SimpleGraph.ConnectedComponent.eq.2 ?_
    refine (creach B p _ hSE' (by simp)).trans (creach B p _ _ (by simp))
  rw [this]; exact he

/-- If `S`, `SW` and `W` are free, `S` reaches `NW`, which has a free ray. -/
lemma not_SEnc_left (hb : Before B p) (hW : (p.1 - 1, p.2) ∉ B) (hSW : (p.1 - 1, p.2 - 1) ∉ B) :
    ¬ SEnc B p := by
  rintro ⟨hS, he⟩
  have hNW := not_mem_above B p hb (p.1 - 1, p.2 + 1) (Or.inl (by simp))
  have hW' := mem_compl_insert B p (v := (p.1 - 1, p.2)) (by simp [Prod.ext_iff]) hW
  have hSW' := mem_compl_insert B p (v := (p.1 - 1, p.2 - 1)) (by simp [Prod.ext_iff]) hSW
  apply not_enclosed_above B p hb (p.1 - 1, p.2 + 1) (Or.inl (by simp)) hNW
  have : (complementGraph (insert p B)).connectedComponentMk ⟨(p.1 - 1, p.2 + 1), by simpa using hNW⟩ =
      (complementGraph (insert p B)).connectedComponentMk
        ⟨(p.1, p.2 - 1), mem_compl_insert B p (by simp [Prod.ext_iff]) hS⟩ := by
    refine SimpleGraph.ConnectedComponent.eq.2 ?_
    refine (creach B p _ hW' (by simp)).trans ((creach B p _ hSW' (by simp)).trans
      (creach B p _ _ (by simp)))
  rw [this]; exact he

open Classical in
/-- **The insertion step in raster-scan order, reduced to its Jordan core.** -/
theorem invariant_insert_scan (hp : p ∉ B) (hb : Before B p) :
    invariant (insert p B) - invariant B =
      (if SEnc B p then 1 else 0) + Nat.card {c // TouchC B p c} - 1
      + ((if (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B then 0 else 1)
      + (if (p.1, p.2 - 1) ∈ B ∨ (p.1 + 1, p.2 - 1) ∈ B then 0 else 1)
      - (if (p.1, p.2 - 1) ∈ B then 0 else 1)) := by
  have key := invariant_insert B p hp
  rw [← euler_insert_local B p hp, euler_scan B p hp hb, P_scan B p hb,
    if_neg (cp_not_enclosed B p hp hb)] at key
  rw [key]
  split_ifs <;> push_cast <;> ring

open Classical in
/-- **`Statement` from the Jordan core.** The only remaining case is the one where `S` is
free, `SE` is a barrier pixel, and `W` or `SW` is a barrier pixel: then the enclosed piece
count `[SEnc]` and the number `k` of touching 8-components must add up to `2`. -/
theorem statement_of_core
    (hcore : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      (p.1, p.2 - 1) ∉ B → (p.1 + 1, p.2 - 1) ∈ B →
      ((p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B) →
      (if SEnc B p then 1 else 0) + Nat.card {c // TouchC B p c} = 2) :
    Statement := by
  apply statement_of_scan
  intro B p hp hb
  have key := invariant_insert_scan B p hp hb
  have mem : ∀ v : Pixel, v ∈ B → v ∈ (B : Set Pixel) := fun v h => h
  by_cases hS : (p.1, p.2 - 1) ∈ B
  · -- `S` is a barrier pixel: every touching neighbour is joined to `S`
    have hk : Nat.card {c // TouchC B p c} = 1 := by
      refine k_eq_one B p ⟨_, mem _ hS⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
      intro u hu
      rcases touch_nbrs B p hb u hu with h | h | h | h
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
      · have : u = ⟨_, mem _ hS⟩ := Subtype.ext h
        rw [this]
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
    rw [if_neg (not_SEnc_of_S B p hS), hk, if_pos (Or.inr (Or.inl hS)), if_pos (Or.inl hS),
      if_pos hS] at key
    push_cast at key
    linarith
  by_cases hSE : (p.1 + 1, p.2 - 1) ∈ B
  · by_cases hL : (p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B
    · -- the Jordan core
      have hc := hcore B p hp hb hS hSE hL
      have hL' : (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B := by tauto
      rw [if_pos hL', if_pos (Or.inr hSE), if_neg hS] at key
      have hc' : ((if SEnc B p then 1 else 0 : ℕ) : ℤ) + (Nat.card {c // TouchC B p c} : ℤ) = 2 := by
        exact_mod_cast hc
      split_ifs at key hc' <;> push_cast at hc' <;> linarith
    · -- only `SE` touches
      push_neg at hL
      have hk : Nat.card {c // TouchC B p c} = 1 := by
        refine k_eq_one B p ⟨_, mem _ hSE⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
        intro u hu
        rcases touch_nbrs B p hb u hu with h | h | h | h
        · exact absurd (h ▸ u.2) hL.1
        · exact absurd (h ▸ u.2) hL.2
        · exact absurd (h ▸ u.2) hS
        · have : u = ⟨_, mem _ hSE⟩ := Subtype.ext h
          rw [this]
      rw [if_neg (not_SEnc_left B p hb hL.1 hL.2), hk, if_neg (not_or.2 ⟨hL.1, not_or.2 ⟨hS, hL.2⟩⟩),
        if_pos (Or.inr hSE), if_neg hS] at key
      push_cast at key
      linarith
  · rw [if_neg (not_SEnc_right B p hb hSE)] at key
    by_cases hL : (p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B
    · -- only `W` and `SW` can touch, and they are 8-adjacent
      have hk : Nat.card {c // TouchC B p c} = 1 := by
        rcases hL with hW | hSW
        · refine k_eq_one B p ⟨_, mem _ hW⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
          intro u hu
          rcases touch_nbrs B p hb u hu with h | h | h | h
          · have : u = ⟨_, mem _ hW⟩ := Subtype.ext h
            rw [this]
          · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
          · exact absurd (h ▸ u.2) hS
          · exact absurd (h ▸ u.2) hSE
        · refine k_eq_one B p ⟨_, mem _ hSW⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
          intro u hu
          rcases touch_nbrs B p hb u hu with h | h | h | h
          · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
          · have : u = ⟨_, mem _ hSW⟩ := Subtype.ext h
            rw [this]
          · exact absurd (h ▸ u.2) hS
          · exact absurd (h ▸ u.2) hSE
      have hL' : (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B := by tauto
      rw [hk, if_pos hL', if_neg (not_or.2 ⟨hS, hSE⟩), if_neg hS] at key
      push_cast at key
      linarith
    · -- nothing touches
      push_neg at hL
      have hk : Nat.card {c // TouchC B p c} = 0 := by
        refine k_eq_zero B p fun u hu => ?_
        rcases touch_nbrs B p hb u hu with h | h | h | h
        · exact hL.1 (h ▸ u.2)
        · exact hL.2 (h ▸ u.2)
        · exact hS (h ▸ u.2)
        · exact hSE (h ▸ u.2)
      rw [hk, if_neg (not_or.2 ⟨hL.1, not_or.2 ⟨hS, hL.2⟩⟩), if_neg (not_or.2 ⟨hS, hSE⟩),
        if_neg hS] at key
      push_cast at key
      linarith

/-- In raster-scan order, an insertion either preserves the invariant or is in the
Jordan-core configuration. -/
lemma scan_step_eq_or_core (B : Finset Pixel) (p : Pixel) (hp : p ∉ B) (hb : Before B p) :
    invariant (insert p B) = invariant B ∨
      ((p.1, p.2 - 1) ∉ B ∧ (p.1 + 1, p.2 - 1) ∈ B ∧
        ((p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B)) := by
  have key := invariant_insert_scan B p hp hb
  have mem : ∀ v : Pixel, v ∈ B → v ∈ (B : Set Pixel) := fun v h => h
  by_cases hS : (p.1, p.2 - 1) ∈ B
  · -- `S` is a barrier pixel: every touching neighbour is joined to `S`
    have hk : Nat.card {c // TouchC B p c} = 1 := by
      refine k_eq_one B p ⟨_, mem _ hS⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
      intro u hu
      rcases touch_nbrs B p hb u hu with h | h | h | h
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
      · have : u = ⟨_, mem _ hS⟩ := Subtype.ext h
        rw [this]
      · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
    rw [if_neg (not_SEnc_of_S B p hS), hk, if_pos (Or.inr (Or.inl hS)), if_pos (Or.inl hS),
      if_pos hS] at key
    push_cast at key
    exact Or.inl (by linarith)
  by_cases hSE : (p.1 + 1, p.2 - 1) ∈ B
  · by_cases hL : (p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B
    · -- the Jordan core
      exact Or.inr ⟨hS, hSE, hL⟩
    · -- only `SE` touches
      push_neg at hL
      have hk : Nat.card {c // TouchC B p c} = 1 := by
        refine k_eq_one B p ⟨_, mem _ hSE⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
        intro u hu
        rcases touch_nbrs B p hb u hu with h | h | h | h
        · exact absurd (h ▸ u.2) hL.1
        · exact absurd (h ▸ u.2) hL.2
        · exact absurd (h ▸ u.2) hS
        · have : u = ⟨_, mem _ hSE⟩ := Subtype.ext h
          rw [this]
      rw [if_neg (not_SEnc_left B p hb hL.1 hL.2), hk, if_neg (not_or.2 ⟨hL.1, not_or.2 ⟨hS, hL.2⟩⟩),
        if_pos (Or.inr hSE), if_neg hS] at key
      push_cast at key
      exact Or.inl (by linarith)
  · rw [if_neg (not_SEnc_right B p hb hSE)] at key
    by_cases hL : (p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B
    · -- only `W` and `SW` can touch, and they are 8-adjacent
      have hk : Nat.card {c // TouchC B p c} = 1 := by
        rcases hL with hW | hSW
        · refine k_eq_one B p ⟨_, mem _ hW⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
          intro u hu
          rcases touch_nbrs B p hb u hu with h | h | h | h
          · have : u = ⟨_, mem _ hW⟩ := Subtype.ext h
            rw [this]
          · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
          · exact absurd (h ▸ u.2) hS
          · exact absurd (h ▸ u.2) hSE
        · refine k_eq_one B p ⟨_, mem _ hSW⟩ ((g8_adj_iff _ _).2 (by simp [Prod.ext_iff] <;> omega)) ?_
          intro u hu
          rcases touch_nbrs B p hb u hu with h | h | h | h
          · exact reach B _ _ ⟨by rw [h]; simp [Prod.ext_iff] <;> omega, by rw [h]; simp, by rw [h]; simp⟩
          · have : u = ⟨_, mem _ hSW⟩ := Subtype.ext h
            rw [this]
          · exact absurd (h ▸ u.2) hS
          · exact absurd (h ▸ u.2) hSE
      have hL' : (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B := by tauto
      rw [hk, if_pos hL', if_neg (not_or.2 ⟨hS, hSE⟩), if_neg hS] at key
      push_cast at key
      exact Or.inl (by linarith)
    · -- nothing touches
      push_neg at hL
      have hk : Nat.card {c // TouchC B p c} = 0 := by
        refine k_eq_zero B p fun u hu => ?_
        rcases touch_nbrs B p hb u hu with h | h | h | h
        · exact hL.1 (h ▸ u.2)
        · exact hL.2 (h ▸ u.2)
        · exact hS (h ▸ u.2)
        · exact hSE (h ▸ u.2)
      rw [hk, if_neg (not_or.2 ⟨hL.1, not_or.2 ⟨hS, hL.2⟩⟩), if_neg (not_or.2 ⟨hS, hSE⟩),
        if_neg hS] at key
      push_cast at key
      exact Or.inl (by linarith)


end ScanFinal


section Core

variable (B : Finset Pixel) (p : Pixel)

/-- The left neighbour (`W` or `SW`) and `SE` lie in the same 8-component of `B`. -/
def JoinLR : Prop :=
  ∃ u v : (B : Set Pixel), (u.1 = (p.1 - 1, p.2) ∨ u.1 = (p.1 - 1, p.2 - 1)) ∧
    v.1 = (p.1 + 1, p.2 - 1) ∧ (barrierGraph B).Reachable u v

lemma reach_left (u v : (B : Set Pixel)) (hu : u.1 = (p.1 - 1, p.2) ∨ u.1 = (p.1 - 1, p.2 - 1))
    (hv : v.1 = (p.1 - 1, p.2) ∨ v.1 = (p.1 - 1, p.2 - 1)) : (barrierGraph B).Reachable u v := by
  by_cases e : u = v
  · rw [e]
  · have e' : u.1 ≠ v.1 := fun h => e (Subtype.ext h)
    refine reach B u v ⟨e', ?_, ?_⟩ <;> rcases hu with hu | hu <;> rcases hv with hv | hv <;>
      rw [hu, hv] <;> simp

open Classical in
lemma k_core (hb : Before B p) (hS : (p.1, p.2 - 1) ∉ B) (hSE : (p.1 + 1, p.2 - 1) ∈ B)
    (hL : (p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B) :
    Nat.card {c // TouchC B p c} = if JoinLR B p then 1 else 2 := by
  have mem : ∀ v : Pixel, v ∈ B → v ∈ (B : Set Pixel) := fun v h => h
  let se : (B : Set Pixel) := ⟨_, mem _ hSE⟩
  have hse : G8.Adj p se.1 := (g8_adj_iff _ _).2 (by simp [se, Prod.ext_iff])
  obtain ⟨l0, hl0⟩ : ∃ l0 : (B : Set Pixel), l0.1 = (p.1 - 1, p.2) ∨ l0.1 = (p.1 - 1, p.2 - 1) := by
    rcases hL with h | h
    · exact ⟨⟨_, mem _ h⟩, Or.inl rfl⟩
    · exact ⟨⟨_, mem _ h⟩, Or.inr rfl⟩
  have hl0adj : G8.Adj p l0.1 := by
    rw [g8_adj_iff]; rcases hl0 with h | h <;> rw [h] <;> simp [Prod.ext_iff] <;> omega
  split_ifs with hJ
  · obtain ⟨u, v, hu, hv, huv⟩ := hJ
    have hv' : v = se := Subtype.ext hv
    subst hv'
    refine k_eq_one B p se hse fun w hw => ?_
    rcases touch_nbrs B p hb w hw with h | h | h | h
    · exact (reach_left B p w u (Or.inl h) hu).trans huv
    · exact (reach_left B p w u (Or.inr h) hu).trans huv
    · exact absurd (h ▸ w.2) hS
    · have : w = se := Subtype.ext h
      rw [this]
  · have hne : (barrierGraph B).connectedComponentMk l0 ≠ (barrierGraph B).connectedComponentMk se :=
      fun h => hJ ⟨l0, se, hl0, rfl, SimpleGraph.ConnectedComponent.eq.1 h⟩
    have e : {c // TouchC B p c} ≃
        (({(barrierGraph B).connectedComponentMk l0, (barrierGraph B).connectedComponentMk se} :
          Set (barrierGraph B).ConnectedComponent)) := by
      refine Equiv.subtypeEquivRight fun c => ?_
      simp only [Set.mem_insert_iff, Set.mem_singleton_iff]
      constructor
      · rintro ⟨w, rfl, hw⟩
        rcases touch_nbrs B p hb w hw with h | h | h | h
        · exact Or.inl (SimpleGraph.ConnectedComponent.eq.2 (reach_left B p w l0 (Or.inl h) hl0))
        · exact Or.inl (SimpleGraph.ConnectedComponent.eq.2 (reach_left B p w l0 (Or.inr h) hl0))
        · exact absurd (h ▸ w.2) hS
        · exact Or.inr (by rw [show w = se from Subtype.ext h])
      · rintro (rfl | rfl)
        · exact ⟨l0, rfl, hl0adj⟩
        · exact ⟨se, rfl, hse⟩
    rw [Nat.card_congr e, Nat.card_coe_set_eq, Set.ncard_pair hne]

open Classical in
/-- **`Statement` from a half-plane digital Jordan lemma.** Suppose that, in raster-scan
order, whenever `S` is free, `SE` is a barrier pixel and `W` or `SW` is a barrier pixel,
the component of `S` in `ℤ² \ insert p B` is finite exactly when the left neighbour and `SE`
are 8-connected in `B`. Then `Statement` holds. -/
theorem statement_of_halfplane_jordan
    (hJ : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      (p.1, p.2 - 1) ∉ B → (p.1 + 1, p.2 - 1) ∈ B →
      ((p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B) →
      (SEnc B p ↔ JoinLR B p)) :
    Statement := by
  apply statement_of_core
  intro B p hp hb hS hSE hL
  rw [k_core B p hb hS hSE hL]
  have := hJ B p hp hb hS hSE hL
  by_cases h : SEnc B p
  · rw [if_pos h, if_pos (this.1 h)]
  · rw [if_neg h, if_neg (fun h' => h (this.2 h'))]

end Core


open Classical in
/-- Under the half-plane Jordan lemma, the bridge identity `enc = C8 − χ` holds for every
finite raster (the equation of `P1.Bridge`). -/
theorem bridge_of_halfplane_jordan
    (hJ : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      (p.1, p.2 - 1) ∉ B → (p.1 + 1, p.2 - 1) ∈ B →
      ((p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B) →
      (SEnc B p ↔ JoinLR B p))
    (B : Finset Pixel) : (enclosed B : ℤ) = C8 B - euler B := by
  have h := invariant_zero_of_scan (fun B p hp _ => statement_of_halfplane_jordan hJ B p hp) B
  unfold invariant at h
  linarith


section Parity

variable (B : Finset Pixel) (p : Pixel)

/-- Sum of `F` over the steps of a walk in the barrier graph. -/
def dsum (F : Pixel → Pixel → ℤ) {a b : (B : Set Pixel)} (w : (barrierGraph B).Walk a b) : ℤ :=
  (w.darts.map fun d => F d.fst.1 d.snd.1).sum

lemma dsum_parity (F : Pixel → Pixel → ℤ) (χ : Pixel → ℤ)
    (h : ∀ a b : Pixel, a ∈ B → b ∈ B → G8.Adj a b → (F a b - χ a - χ b) % 2 = 0)
    {a b : (B : Set Pixel)} (w : (barrierGraph B).Walk a b) :
    (dsum B F w - χ a.1 - χ b.1) % 2 = 0 := by
  induction w with
  | nil => simp [dsum]; omega
  | @cons a c b hac q ih =>
    have h1 := h a.1 c.1 a.2 c.2 ((barrier_adj_iff B a c).1 hac)
    have e : dsum B F (SimpleGraph.Walk.cons hac q) = F a.1 c.1 + dsum B F q := by
      simp [dsum, SimpleGraph.Walk.darts_cons]
    rw [e]; omega

/-- Crossing indicator: the step `a → b` crosses the vertical line between columns `v.1`
and `v.1 + 1`, and its endpoint in column `v.1` lies above `v`. -/
def cross (v a b : Pixel) : ℤ :=
  if (a.1 = v.1 ∧ b.1 = v.1 + 1 ∧ v.2 < a.2) ∨ (b.1 = v.1 ∧ a.1 = v.1 + 1 ∧ v.2 < b.2) then 1 else 0

lemma g8_coords {a b : Pixel} (h : G8.Adj a b) :
    -1 ≤ a.1 - b.1 ∧ a.1 - b.1 ≤ 1 ∧ -1 ≤ a.2 - b.2 ∧ a.2 - b.2 ≤ 1 := by
  rw [g8_adj_iff] at h; omega

/-- Horizontal step `v → v + (1,0)` between free pixels. -/
lemma cross_horiz (v a b : Pixel) (hadj : G8.Adj a b)
    (ha1 : ¬ (a.1 = v.1 ∧ a.2 = v.2)) (ha2 : ¬ (a.1 = v.1 + 1 ∧ a.2 = v.2))
    (hb1 : ¬ (b.1 = v.1 ∧ b.2 = v.2)) (hb2 : ¬ (b.1 = v.1 + 1 ∧ b.2 = v.2)) :
    (cross v a b + cross (v.1 + 1, v.2) a b
      - (if a.1 = v.1 + 1 ∧ v.2 < a.2 then 1 else 0) - (if b.1 = v.1 + 1 ∧ v.2 < b.2 then 1 else 0))
      % 2 = 0 := by
  have := g8_coords hadj
  unfold cross
  simp only
  split_ifs <;> omega

/-- Vertical step `v → v + (0,1)` between free pixels. -/
lemma cross_vert (v a b : Pixel) (hadj : G8.Adj a b)
    (ha : ¬ (a.1 = v.1 ∧ a.2 = v.2 + 1)) (hb : ¬ (b.1 = v.1 ∧ b.2 = v.2 + 1)) :
    (cross v a b - cross (v.1, v.2 + 1) a b - 0 - 0) % 2 = 0 := by
  have := g8_coords hadj
  unfold cross
  simp only
  split_ifs <;> omega

/-- Below everything: the count is the number of crossings of a full line. -/
lemma cross_below (v a b : Pixel) (hadj : G8.Adj a b) (ha : v.2 < a.2) (hb : v.2 < b.2) :
    (cross v a b - (if a.1 ≤ v.1 then 1 else 0) - (if b.1 ≤ v.1 then 1 else 0)) % 2 = 0 := by
  have := g8_coords hadj
  unfold cross
  split_ifs <;> omega

end Parity


section JoinToEnc

variable (B : Finset Pixel) (p : Pixel)

lemma dsum_add (F G : Pixel → Pixel → ℤ) {a b : (B : Set Pixel)} (w : (barrierGraph B).Walk a b) :
    dsum B (fun x y => F x y + G x y) w = dsum B F w + dsum B G w := by
  simp [dsum, List.sum_map_add]

/-- Parity over the closed curve `p → u → ⋯ → v' → p`. -/
lemma cycle_parity {u v' : (B : Set Pixel)} (w : (barrierGraph B).Walk u v')
    (hpu : G8.Adj p u.1) (hvp : G8.Adj v'.1 p) (F : Pixel → Pixel → ℤ) (χ : Pixel → ℤ)
    (h : ∀ a b : Pixel, a ∈ insert p B → b ∈ insert p B → G8.Adj a b →
      (F a b - χ a - χ b) % 2 = 0) :
    (F p u.1 + dsum B F w + F v'.1 p) % 2 = 0 := by
  have h1 := dsum_parity B F χ (fun a b ha hb hab =>
    h a b (Finset.mem_insert_of_mem ha) (Finset.mem_insert_of_mem hb) hab) w
  have h2 := h p u.1 (Finset.mem_insert_self _ _) (Finset.mem_insert_of_mem u.2) hpu
  have h3 := h v'.1 p (Finset.mem_insert_of_mem v'.2) (Finset.mem_insert_self _ _) hvp
  omega

lemma row_le (hb : Before B p) (a : Pixel) (ha : a ∈ insert p B) :
    a.2 < p.2 ∨ (a.2 = p.2 ∧ a.1 ≤ p.1) := by
  rw [Finset.mem_insert] at ha
  rcases ha with rfl | ha
  · right; exact ⟨rfl, le_rfl⟩
  · rcases hb a ha with h | h
    · left; exact h
    · right; exact ⟨h.1, h.2.le⟩

lemma free_ne {v a : Pixel} (hv : v ∉ insert p B) (ha : a ∈ insert p B) :
    ¬ (a.1 = v.1 ∧ a.2 = v.2) := fun h => hv (by rw [show v = a from Prod.ext h.1.symm h.2.symm]; exact ha)

/-- **One direction of the half-plane Jordan lemma.** If the left neighbour and `SE` are
8-connected in `B`, the component of `S` in `ℤ² \ insert p B` is finite. The proof is a
crossing-parity argument for the closed 8-curve formed by the connecting path and `p`. -/
theorem senc_of_join (hb : Before B p) (hS : (p.1, p.2 - 1) ∉ B) (hJ : JoinLR B p) :
    SEnc B p := by
  obtain ⟨u, v', hu, hv', huv⟩ := hJ
  obtain ⟨w⟩ := huv
  have hpu : G8.Adj p u.1 := by
    rw [g8_adj_iff]; rcases hu with h | h <;> rw [h] <;> simp [Prod.ext_iff] <;> omega
  have hvp : G8.Adj v'.1 p := by
    rw [g8_adj_iff, hv']; simp [Prod.ext_iff]
  let N : Pixel → ℤ := fun v => cross v p u.1 + dsum B (cross v) w + cross v v'.1 p
  -- horizontal steps
  have hstep : ∀ v : Pixel, v ∉ insert p B → (v.1 + 1, v.2) ∉ insert p B →
      (N v + N (v.1 + 1, v.2)) % 2 = 0 := by
    intro v hv hv2
    have := cycle_parity B p w hpu hvp (fun a b => cross v a b + cross (v.1 + 1, v.2) a b)
      (fun a => if a.1 = v.1 + 1 ∧ v.2 < a.2 then 1 else 0)
      (fun a b ha hb hab => cross_horiz v a b hab (free_ne B p hv ha) (free_ne B p hv2 ha)
        (free_ne B p hv hb) (free_ne B p hv2 hb))
    rw [dsum_add] at this
    beta_reduce at this
    simp only [N]; omega
  -- vertical steps
  have vstep : ∀ v : Pixel, v ∉ insert p B → (v.1, v.2 + 1) ∉ insert p B →
      (N v + N (v.1, v.2 + 1)) % 2 = 0 := by
    intro v hv hv2
    have := cycle_parity B p w hpu hvp (fun a b => cross v a b + cross (v.1, v.2 + 1) a b)
      (fun _ => 0)
      (fun a b ha hb hab => by
        have := cross_vert v a b hab (free_ne B p hv2 ha) (free_ne B p hv2 hb)
        beta_reduce
        omega)
    rw [dsum_add] at this
    beta_reduce at this
    simp only [N]; omega
  -- parity is constant along free 4-paths
  have step : ∀ x y : (((insert p B : Finset Pixel) : Set Pixel)ᶜ : Set Pixel),
      (complementGraph (insert p B)).Adj x y → (N x.1 - N y.1) % 2 = 0 := by
    intro x y hxy
    rw [compl_adj_iff] at hxy
    have h4 := g4_adj_iff _ _ hxy
    have hx : x.1 ∉ insert p B := by simpa using x.2
    have hy : y.1 ∉ insert p B := by simpa using y.2
    obtain ⟨⟨x1, x2⟩, _⟩ := x
    obtain ⟨⟨y1, y2⟩, _⟩ := y
    simp only at h4 hx hy ⊢
    rcases abs_cases (x1 - y1) with ⟨ha, _⟩ | ⟨ha, _⟩ <;>
      rcases abs_cases (x2 - y2) with ⟨hb', _⟩ | ⟨hb', _⟩ <;> rw [ha, hb'] at h4
    · by_cases e : x1 = y1
      · have e2 : x2 = y2 + 1 := by omega
        subst e e2
        have := vstep (x1, y2) hy hx
        simp only at this; omega
      · have e2 : x1 = y1 + 1 := by omega
        have e3 : x2 = y2 := by omega
        subst e2 e3
        have := hstep (y1, x2) hy hx
        simp only at this; omega
    · have e1 : x1 = y1 := by omega
      have e2 : y2 = x2 + 1 := by omega
      subst e1 e2
      have := vstep (x1, x2) hx hy
      simp only at this; omega
    · have e1 : y1 = x1 + 1 := by omega
      have e2 : x2 = y2 := by omega
      subst e1 e2
      have := hstep (x1, x2) hx hy
      simp only at this; omega
    · exfalso; omega
  -- the count at `S` is odd
  have hSodd : N (p.1, p.2 - 1) % 2 = 1 := by
    have h0 := dsum_parity B (cross (p.1, p.2 - 1)) (fun _ => 0) (fun a b ha' hb' hab => by
      have h1 := hb a ha'
      have h2 := hb b hb'
      unfold cross
      simp only
      split_ifs <;> omega) w
    have e1 : cross (p.1, p.2 - 1) p u.1 = 0 := by
      unfold cross; rcases hu with h | h <;> rw [h] <;> simp <;> omega
    have e2 : cross (p.1, p.2 - 1) v'.1 p = 1 := by
      unfold cross; rw [hv']; simp
    simp only [N]; rw [e1, e2]; omega
  -- every pixel of the component of `S` has odd count
  have hS' := mem_compl_insert B p (v := (p.1, p.2 - 1)) (by simp [Prod.ext_iff]) hS
  have hodd : ∀ y, (complementGraph (insert p B)).Reachable ⟨_, hS'⟩ y → N y.1 % 2 = 1 := by
    intro y hy
    rw [SimpleGraph.reachable_iff_reflTransGen] at hy
    induction hy with
    | refl => exact hSodd
    | tail _ hyz ih =>
      have := step _ _ hyz
      omega
  -- pixels with odd count lie in a finite box
  obtain ⟨M, hM⟩ := exists_bound (insert p B)
  have hbox : ∀ v : Pixel, N v % 2 = 1 → -M - 1 < v.1 ∧ v.1 < M ∧ -M < v.2 ∧ v.2 < p.2 := by
    intro v hv
    by_contra hc
    apply absurd hv
    have zero : (∀ a b : Pixel, a ∈ insert p B → b ∈ insert p B → G8.Adj a b →
        cross v a b = 0) → N v % 2 = 0 := by
      intro hz
      have := cycle_parity B p w hpu hvp (cross v) (fun _ => 0)
        (fun a b ha hb hab => by rw [hz a b ha hb hab]; rfl)
      simpa [N] using this
    rcases not_and_or.1 hc with h | h
    · rw [zero]; · omega
      intro a b ha _ _
      have := hM a ha; simp only [abs_lt] at this
      unfold cross; split_ifs <;> omega
    rcases not_and_or.1 h with h | h
    · rw [zero]; · omega
      intro a b _ hb' _
      have h1 := hM b hb'; simp only [abs_lt] at h1
      unfold cross; split_ifs <;> omega
    rcases not_and_or.1 h with h | h
    · -- below everything
      have := cycle_parity B p w hpu hvp (cross v) (fun a => if a.1 ≤ v.1 then 1 else 0)
        (fun a b ha hb hab => by
          have h1 := hM a ha; have h2 := hM b hb; simp only [abs_lt] at h1 h2
          exact cross_below v a b hab (by omega) (by omega))
      simp only [N]; omega
    · -- above the row of `p`
      rw [zero]; · omega
      intro a b ha hb' _
      have h1 := row_le B p hb a ha; have h2 := row_le B p hb b hb'
      unfold cross; split_ifs <;> omega
  refine ⟨hS, ?_⟩
  unfold IsEnclosed
  let box : Finset Pixel := Finset.Icc (-M - 1) M ×ˢ Finset.Icc (-M) p.2
  refine ((Finset.finite_toSet box).preimage Subtype.val_injective.injOn).subset ?_
  intro y hy
  rw [SimpleGraph.ConnectedComponent.mem_supp_iff, SimpleGraph.ConnectedComponent.eq] at hy
  have := hbox y.1 (hodd y hy.symm)
  simp only [Set.mem_preimage, Finset.coe_product, Finset.coe_Icc, Set.mem_prod, Set.mem_Icc, box]
  omega

end JoinToEnc


/-- **`Statement` from the remaining direction of the half-plane Jordan lemma.** The
direction `JoinLR → SEnc` is `senc_of_join`; only `SEnc → JoinLR` is assumed. -/
theorem statement_of_enc_join
    (hJ : ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → Before B p →
      (p.1, p.2 - 1) ∉ B → (p.1 + 1, p.2 - 1) ∈ B →
      ((p.1 - 1, p.2) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B) →
      SEnc B p → JoinLR B p) :
    Statement :=
  statement_of_halfplane_jordan fun B p hp hb hS hSE hL =>
    ⟨hJ B p hp hb hS hSE hL, senc_of_join B p hb hS⟩


/-- In raster-scan order, an insertion never decreases the invariant. -/
lemma scan_step_mono (B : Finset Pixel) (p : Pixel) (hp : p ∉ B) (hb : Before B p) :
    invariant B ≤ invariant (insert p B) := by
  classical
  rcases scan_step_eq_or_core B p hp hb with h | ⟨hS, hSE, hL⟩
  · rw [h]
  have key := invariant_insert_scan B p hp hb
  have hL' : (p.1 - 1, p.2) ∈ B ∨ (p.1, p.2 - 1) ∈ B ∨ (p.1 - 1, p.2 - 1) ∈ B := by tauto
  rw [k_core B p hb hS hSE hL, if_pos hL', if_pos (Or.inr hSE), if_neg hS] at key
  by_cases hJ : JoinLR B p
  · rw [if_pos hJ, if_pos (senc_of_join B p hb hS hJ)] at key
    push_cast at key
    linarith
  · rw [if_neg hJ] at key
    split_ifs at key <;> push_cast at key <;> linarith

/-- **Half of the bridge identity.** For every finite raster, `enc ≥ C8 − χ`. -/
theorem invariant_nonneg (B : Finset Pixel) : 0 ≤ invariant B := by
  induction B using Finset.induction_on_max_value (fun q : Pixel => toLex (q.2, q.1)) with
  | h0 => rw [invariant_empty]
  | step a s ha hmax ih =>
    refine ih.trans (scan_step_mono s a ha ?_)
    intro q hq
    have h1 := hmax q hq
    have hne : q ≠ a := fun e => ha (e ▸ hq)
    rw [Prod.Lex.toLex_le_toLex] at h1
    rcases h1 with h1 | ⟨h1, h2⟩
    · exact Or.inl h1
    · refine Or.inr ⟨h1, lt_of_le_of_ne h2 fun e => hne (Prod.ext e h1)⟩

/-- The same, in the form `enc ≥ C8 − χ`. -/
theorem enclosed_ge (B : Finset Pixel) : (C8 B : ℤ) - euler B ≤ enclosed B := by
  have := invariant_nonneg B
  unfold invariant at this
  linarith

/-- `Statement` follows from the other half of the bridge identity, `enc ≤ C8 − χ`. -/
theorem statement_of_le
    (h : ∀ B : Finset Pixel, (enclosed B : ℤ) ≤ C8 B - euler B) : Statement := by
  have hz : ∀ B : Finset Pixel, invariant B = 0 := fun B => by
    have h1 := invariant_nonneg B
    have h2 := h B
    unfold invariant at h1 ⊢
    linarith
  intro B p _
  rw [hz, hz]




/-- Successor of a crack `(c, d)` (`c ∈ C`, `c + d ∉ C`) along the boundary, (8,4) rule. -/
def next (C : Finset Pixel) (x : Pixel × Pixel) : Pixel × Pixel :=
  if (x.1.1 + x.2.1 - x.2.2, x.1.2 + x.2.2 + x.2.1) ∈ C then
    ((x.1.1 + x.2.1 - x.2.2, x.1.2 + x.2.2 + x.2.1), (x.2.2, -x.2.1))
  else if (x.1.1 - x.2.2, x.1.2 + x.2.1) ∈ C then ((x.1.1 - x.2.2, x.1.2 + x.2.1), x.2)
  else (x.1, (-x.2.2, x.2.1))

def prev (C : Finset Pixel) (y : Pixel × Pixel) : Pixel × Pixel :=
  if (y.1.1 + y.2.1 + y.2.2, y.1.2 + y.2.2 - y.2.1) ∈ C then
    ((y.1.1 + y.2.1 + y.2.2, y.1.2 + y.2.2 - y.2.1), (-y.2.2, y.2.1))
  else if (y.1.1 + y.2.2, y.1.2 - y.2.1) ∈ C then ((y.1.1 + y.2.2, y.1.2 - y.2.1), y.2)
  else (y.1, (y.2.2, -y.2.1))

def dirs : Finset Pixel := {(1, 0), (0, 1), (-1, 0), (0, -1)}

def cracks (C : Finset Pixel) : Finset (Pixel × Pixel) :=
  (C ×ˢ dirs).filter fun x => (x.1.1 + x.2.1, x.1.2 + x.2.2) ∉ C

lemma mem_cracks (C : Finset Pixel) (x : Pixel × Pixel) : x ∈ cracks C ↔
    x.1 ∈ C ∧ x.2 ∈ dirs ∧ (x.1.1 + x.2.1, x.1.2 + x.2.2) ∉ C := by
  simp [cracks, and_assoc]

lemma mc {C : Finset Pixel} {a b a' b' : ℤ} (h : (a, b) ∈ C) (ha : a = a') (hb : b = b') :
    (a', b') ∈ C := ha ▸ hb ▸ h

lemma next_mem (C : Finset Pixel) (x : Pixel × Pixel) (hx : x ∈ cracks C) : next C x ∈ cracks C := by
  rw [mem_cracks] at hx ⊢
  obtain ⟨⟨c1, c2⟩, ⟨d1, d2⟩⟩ := x
  obtain ⟨h1, h2, h3⟩ := hx
  dsimp only at h1 h2 h3
  simp only [dirs, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq] at h2
  simp only [next]
  split_ifs with g1 g2
  · refine ⟨g1, ?_, fun h => h3 (mc h (by ring) (by ring))⟩
    simp only [dirs, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq]; omega
  · refine ⟨g2, by simpa [dirs] using h2, fun h => g1 (mc h (by ring) (by ring))⟩
  · refine ⟨h1, ?_, fun h => g2 (mc h (by ring) (by ring))⟩
    simp only [dirs, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq]; omega

lemma prev_next (C : Finset Pixel) (x : Pixel × Pixel) (hx : x ∈ cracks C) : prev C (next C x) = x := by
  rw [mem_cracks] at hx
  obtain ⟨⟨c1, c2⟩, ⟨d1, d2⟩⟩ := x
  obtain ⟨h1, -, h3⟩ := hx
  dsimp only at h1 h3
  simp only [next]
  split_ifs with g1 g2
  · simp only [prev]
    rw [if_pos (mc h1 (by ring) (by ring))]
    ext <;> simp <;> ring
  · simp only [prev]
    rw [if_neg (fun h => h3 (mc h (by ring) (by ring))), if_pos (mc h1 (by ring) (by ring))]
    ext <;> simp <;> ring
  · simp only [prev]
    rw [if_neg (fun h => g1 (mc h (by ring) (by ring))),
      if_neg (fun h => h3 (mc h (by ring) (by ring)))]
    simp

/-- A self-map of a finite set with a left inverse on it: the orbit of `x0` returns. -/
lemma orbit {α : Type*} (f g : α → α) (s : Finset α) (hs : ∀ x ∈ s, f x ∈ s)
    (hg : ∀ x ∈ s, g (f x) = x) (x0 : α) (h0 : x0 ∈ s) :
    ∃ n, 0 < n ∧ f^[n] x0 = x0 ∧ ∀ k, 0 < k → k < n → f^[k] x0 ≠ x0 := by
  have hmem : ∀ k, f^[k] x0 ∈ s := by
    intro k; induction k with
    | zero => exact h0
    | succ k ih => rw [Function.iterate_succ_apply']; exact hs _ ih
  have hex : ∃ n, 0 < n ∧ f^[n] x0 = x0 := by
    obtain ⟨i, j, hij, he⟩ := Finite.exists_ne_map_eq_of_infinite
      (fun k : ℕ => (⟨f^[k] x0, hmem k⟩ : s))
    simp only [Subtype.mk.injEq] at he
    -- cancel the common prefix
    have cancel : ∀ m a b, f^[a + m] x0 = f^[b + m] x0 → f^[a] x0 = f^[b] x0 := by
      intro m; induction m with
      | zero => intro a b h; simpa using h
      | succ m ih =>
        intro a b h
        apply ih a b
        have := congrArg g h
        rwa [show a + (m + 1) = (a + m) + 1 by omega, show b + (m + 1) = (b + m) + 1 by omega,
          Function.iterate_succ_apply', Function.iterate_succ_apply', hg _ (hmem _),
          hg _ (hmem _)] at this
    rcases Nat.lt_or_gt_of_ne hij with h | h
    · refine ⟨j - i, by omega, ?_⟩
      have := cancel i (j - i) 0 (by rw [show j - i + i = j by omega]; simpa using he.symm)
      simpa using this
    · refine ⟨i - j, by omega, ?_⟩
      have := cancel j (i - j) 0 (by rw [show i - j + j = i by omega]; simpa using he)
      simpa using this
  classical
  refine ⟨Nat.find hex, (Nat.find_spec hex).1, (Nat.find_spec hex).2, fun k hk hkn e => ?_⟩
  exact Nat.find_min hex hkn ⟨hk, e⟩


section Escape

variable (B : Finset Pixel) (p : Pixel)

/-- `a` and `b` are free and joined by a 4-path in `ℤ² \ insert p B`. -/
def FR (a b : Pixel) : Prop :=
  ∃ (ha : a ∉ insert p B) (hb : b ∉ insert p B),
    (complementGraph (insert p B)).Reachable ⟨a, by simpa using ha⟩ ⟨b, by simpa using hb⟩

lemma FR_refl {a : Pixel} (ha : a ∉ insert p B) : FR B p a a := ⟨ha, ha, by rfl⟩

lemma FR_trans {a b c : Pixel} (h1 : FR B p a b) (h2 : FR B p b c) : FR B p a c := by
  obtain ⟨ha, hb, r1⟩ := h1
  obtain ⟨_, hc, r2⟩ := h2
  exact ⟨ha, hc, r1.trans r2⟩

lemma FR_step {a b : Pixel} (ha : a ∉ insert p B) (hb : b ∉ insert p B)
    (h : (a.1 - b.1 = 0 ∧ (a.2 - b.2 = 1 ∨ a.2 - b.2 = -1)) ∨
      ((a.1 - b.1 = 1 ∨ a.1 - b.1 = -1) ∧ a.2 - b.2 = 0)) : FR B p a b := by
  refine ⟨ha, hb, creach B p _ _ ?_⟩
  rcases h with ⟨h1, h2 | h2⟩ | ⟨h1 | h1, h2⟩ <;> rw [h1, h2] <;> simp

/-- Chebyshev distance at most one. -/
def Near (q c : Pixel) : Prop := -1 ≤ q.1 - c.1 ∧ q.1 - c.1 ≤ 1 ∧ -1 ≤ q.2 - c.2 ∧ q.2 - c.2 ≤ 1

/-- The outside pixel of a crack. -/
def out (x : Pixel × Pixel) : Pixel := (x.1.1 + x.2.1, x.1.2 + x.2.2)

variable (C : Finset Pixel) (c0 : Pixel)

/-- One step along the crack boundary of `C` moves along a free 4-path, except the step
that turns around the corner `p`. -/
lemma crack_step
    (hfree : ∀ c ∈ C, ∀ q : Pixel, q ∉ C → Near q c → q ≠ p → q ∉ B)
    (hp : p = (c0.1 - 1, c0.2 + 1))
    (hpC : ∀ c ∈ C, Near p c → c = c0)
    (x : Pixel × Pixel) (hx : x ∈ cracks C) (hxE : x ≠ (c0, (0, 1))) :
    FR B p (out x) (out (next C x)) := by
  have fr : ∀ c ∈ C, ∀ q : Pixel, q ∉ C → Near q c → q ≠ p → q ∉ insert p B := by
    intro c hc q hq hn hne h
    rw [Finset.mem_insert] at h
    rcases h with h | h
    · exact hne h
    · exact hfree c hc q hq hn hne h
  rw [mem_cracks] at hx
  obtain ⟨⟨c1, c2⟩, ⟨d1, d2⟩⟩ := x
  obtain ⟨h1, h2, h3⟩ := hx
  dsimp only at h1 h2 h3
  simp only [dirs, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq] at h2
  have hxE' : ¬ (c1 = c0.1 ∧ c2 = c0.2 ∧ d1 = 0 ∧ d2 = 1) := by
    rintro ⟨e1, e2, e3, e4⟩; subst e1 e2 e3 e4; exact hxE rfl
  -- `p` is not 4-adjacent to any pixel of `C`, and is diagonal only to `c0`
  have np : ∀ c ∈ C, Near p c → c = c0 := hpC
  obtain ⟨a0, b0⟩ := c0
  obtain ⟨p1, p2⟩ := p
  simp only [Prod.mk.injEq] at hp
  obtain ⟨rfl, rfl⟩ := hp
  simp only [next, out]
  split_ifs with g1 g2
  · -- the boundary turns outward to the diagonal pixel; the outside pixel is unchanged
    have e : ((c1 + d1 - d2 + (d2, -d1).1, c2 + d2 + d1 + (d2, -d1).2) : Pixel) =
        (c1 + d1, c2 + d2) := by ext <;> simp <;> ring
    rw [e]
    refine FR_refl B _ (fr _ h1 _ h3 (by simp only [Near]; omega) fun h => ?_)
    simp only [Prod.mk.injEq] at h
    have := np _ h1 (by simp only [Near]; omega)
    simp only [Prod.mk.injEq] at this
    omega
  · -- straight on
    have e : ((c1 - d2 + (d1, d2).1, c2 + d1 + (d1, d2).2) : Pixel) =
        (c1 + d1 - d2, c2 + d2 + d1) := by ext <;> simp <;> ring
    rw [e]
    have hg : (c1 + d1 - d2, c2 + d2 + d1) ≠ ((a0 - 1, b0 + 1) : Pixel) := fun h => by
      simp only [Prod.mk.injEq] at h
      have := np _ g2 (by simp only [Near]; omega)
      simp only [Prod.mk.injEq] at this
      omega
    have hf : (c1 + d1, c2 + d2) ≠ ((a0 - 1, b0 + 1) : Pixel) := fun h => by
      simp only [Prod.mk.injEq] at h
      have := np _ h1 (by simp only [Near]; omega)
      simp only [Prod.mk.injEq] at this
      omega
    exact FR_step B _ (fr _ h1 _ h3 (by simp only [Near]; omega) hf)
      (fr _ g2 _ g1 (by simp only [Near]; omega) hg) (by simp only; omega)
  · -- the boundary turns inward around `c`: go through the diagonal pixel
    have hg : (c1 + d1 - d2, c2 + d2 + d1) ≠ ((a0 - 1, b0 + 1) : Pixel) := fun h => by
      simp only [Prod.mk.injEq] at h
      have := np _ h1 (by simp only [Near]; omega)
      simp only [Prod.mk.injEq] at this
      omega
    have hf : (c1 + d1, c2 + d2) ≠ ((a0 - 1, b0 + 1) : Pixel) := fun h => by
      simp only [Prod.mk.injEq] at h
      have := np _ h1 (by simp only [Near]; omega)
      simp only [Prod.mk.injEq] at this
      omega
    have ht : ((c1, c2).1 + (-d2, d1).1, (c1, c2).2 + (-d2, d1).2) ≠
        ((a0 - 1, b0 + 1) : Pixel) := fun h => by
      simp only [Prod.mk.injEq] at h
      have := np _ h1 (by simp only [Near]; omega)
      simp only [Prod.mk.injEq] at this
      omega
    have ht' : ((c1, c2).1 + (-d2, d1).1, (c1, c2).2 + (-d2, d1).2) ∉ C := by
      intro h; apply g2; exact mc h (by simp <;> ring) (by simp <;> ring)
    exact FR_trans B _ (FR_step B _ (fr _ h1 _ h3 (by simp only [Near]; omega) hf)
      (fr _ h1 _ g1 (by simp only [Near]; omega) hg) (by simp only; omega))
      (FR_step B _ (fr _ h1 _ g1 (by simp only [Near]; omega) hg)
      (fr _ h1 _ ht' (by simp only [Near]; omega) ht) (by simp only; omega))

lemma iter_mem (x : Pixel × Pixel) (hx : x ∈ cracks C) (k : ℕ) : (next C)^[k] x ∈ cracks C := by
  induction k with
  | zero => exact hx
  | succ k ih => rw [Function.iterate_succ_apply']; exact next_mem C _ ih

/-- **Escape along the crack boundary.** If `p` touches `C` only at the corner `c0`, and every
non-`C` pixel near `C` other than `p` is free, then the pixel left of `c0` reaches the pixel
above `c0` by a free 4-path. -/
theorem crack_escape (hc0 : c0 ∈ C)
    (hfree : ∀ c ∈ C, ∀ q : Pixel, q ∉ C → Near q c → q ≠ p → q ∉ B)
    (hp : p = (c0.1 - 1, c0.2 + 1))
    (hpC : ∀ c ∈ C, Near p c → c = c0)
    (hS : (c0.1 - 1, c0.2) ∉ C) (hE : (c0.1, c0.2 + 1) ∉ C) :
    FR B p (c0.1 - 1, c0.2) (c0.1, c0.2 + 1) := by
  have hxS : (c0, ((-1 : ℤ), (0 : ℤ))) ∈ cracks C := by
    rw [mem_cracks]; refine ⟨hc0, by simp [dirs], ?_⟩
    simpa [sub_eq_add_neg] using hS
  have hxE : (c0, ((0 : ℤ), (1 : ℤ))) ∈ cracks C := by
    rw [mem_cracks]; refine ⟨hc0, by simp [dirs], ?_⟩
    simpa using hE
  have hpn : p ∉ C := fun h => by
    have := hpC p h (by simp only [Near]; omega)
    rw [this] at hp; simp [Prod.ext_iff] at hp
  have hnE : next C (c0, ((0 : ℤ), (1 : ℤ))) = (c0, ((-1 : ℤ), (0 : ℤ))) := by
    simp only [next]
    rw [if_neg (fun h => hpn (hp ▸ mc h (by ring) (by ring))),
      if_neg (fun h => hS (mc h (by ring) (by ring)))]
  obtain ⟨n, hn0, hnx, hmin⟩ := orbit (next C) (prev C) (cracks C) (next_mem C) (prev_next C) _ hxS
  have hlast : (next C)^[n - 1] (c0, ((-1 : ℤ), (0 : ℤ))) = (c0, ((0 : ℤ), (1 : ℤ))) := by
    have h1 : next C ((next C)^[n - 1] (c0, ((-1 : ℤ), (0 : ℤ)))) = next C (c0, ((0 : ℤ), (1 : ℤ))) := by
      rw [hnE, ← Function.iterate_succ_apply' (next C), show (n - 1).succ = n by omega, hnx]
    have := congrArg (prev C) h1
    rwa [prev_next _ _ (iter_mem C _ hxS _), prev_next _ _ hxE] at this
  have hne : ∀ k, k < n - 1 → (next C)^[k] (c0, ((-1 : ℤ), (0 : ℤ))) ≠ (c0, ((0 : ℤ), (1 : ℤ))) := by
    intro k hk e
    apply hmin (k + 1) (by omega) (by omega)
    rw [Function.iterate_succ_apply', e, hnE]
  have hS0 : out (c0, ((-1 : ℤ), (0 : ℤ))) ∉ insert p B := by
    intro h; rw [Finset.mem_insert] at h
    rcases h with h | h
    · rw [hp] at h; simp [out, Prod.ext_iff] at h
    · exact hfree c0 hc0 _ (by simpa [out, sub_eq_add_neg] using hS)
        (by simp only [Near, out]; omega) (by rw [hp]; simp [out, Prod.ext_iff]) h
  have hreach : ∀ k, k ≤ n - 1 →
      FR B p (out (c0, ((-1 : ℤ), (0 : ℤ)))) (out ((next C)^[k] (c0, ((-1 : ℤ), (0 : ℤ))))) := by
    intro k
    induction k with
    | zero => intro _; exact FR_refl B p hS0
    | succ k ih =>
      intro hk
      rw [Function.iterate_succ_apply']
      exact FR_trans B p (ih (by omega))
        (crack_step B p C c0 hfree hp hpC _ (iter_mem C _ hxS k) (hne k (by omega)))
  have := hreach (n - 1) le_rfl
  rw [hlast] at this
  simpa [out, sub_eq_add_neg] using this

end Escape

section Final

variable (B : Finset Pixel) (p : Pixel)

/-- **The remaining direction of the half-plane Jordan lemma.** If the component of `S` is
finite, the left neighbour and `SE` are 8-connected in `B`. Proof: otherwise, follow the crack
boundary of the 8-component of `SE` from `S` to `E` without passing `p`. -/
theorem join_of_senc (hp : p ∉ B) (hb : Before B p) (hS : (p.1, p.2 - 1) ∉ B)
    (hSE : (p.1 + 1, p.2 - 1) ∈ B) (hs : SEnc B p) : JoinLR B p := by
  classical
  by_contra hJ
  let se : (B : Set Pixel) := ⟨_, hSE⟩
  let C : Finset Pixel := B.filter fun b => ∃ hb : b ∈ B, (barrierGraph B).Reachable se ⟨b, hb⟩
  have memC : ∀ b, b ∈ C ↔ ∃ hb : b ∈ B, (barrierGraph B).Reachable se ⟨b, hb⟩ := by
    intro b; simp only [C, Finset.mem_filter]
    exact ⟨fun h => h.2, fun h => ⟨h.1, h⟩⟩
  have hc0 : (p.1 + 1, p.2 - 1) ∈ C := (memC _).2 ⟨hSE, by rfl⟩
  have hfree : ∀ c ∈ C, ∀ q : Pixel, q ∉ C → Near q c → q ≠ p → q ∉ B := by
    intro c hc q hq hn _ hqB
    obtain ⟨hcB, hr⟩ := (memC c).1 hc
    apply hq
    refine (memC q).2 ⟨hqB, hr.trans (reach B ⟨c, hcB⟩ ⟨q, hqB⟩ ⟨fun e => hq (by simp only at e; rw [← e]; exact hc), ?_⟩)⟩
    simp only [Near] at hn
    simp only; omega
  have hpC : ∀ c ∈ C, Near p c → c = (p.1 + 1, p.2 - 1) := by
    intro c hc hn
    obtain ⟨hcB, hr⟩ := (memC c).1 hc
    have hcp : c ≠ p := fun e => hp (e ▸ hcB)
    obtain ⟨c1, c2⟩ := c
    simp only [Near] at hn
    have hbc := hb _ hcB
    simp only at hbc
    have hne : ¬ (c1 = p.1 ∧ c2 = p.2) := fun ⟨e1, e2⟩ => hcp (by rw [e1, e2])
    by_cases hW : c1 = p.1 - 1
    · exfalso
      apply hJ
      refine ⟨⟨_, hcB⟩, se, ?_, rfl, hr.symm⟩
      simp only [Prod.mk.injEq]; omega
    by_cases hS' : c1 = p.1
    · exfalso; apply hS
      have : c2 = p.2 - 1 := by omega
      rw [hS', this] at hcB; exact hcB
    simp only [Prod.mk.injEq]; omega
  have hE : (p.1 + 1, p.2) ∉ B := fun h => by
    rcases hb _ h with h' | h' <;> simp only at h' <;> omega
  have hS2 : (((p.1 + 1, p.2 - 1) : Pixel).1 - 1, ((p.1 + 1, p.2 - 1) : Pixel).2) =
      ((p.1, p.2 - 1) : Pixel) := by ext <;> simp
  have hE2 : (((p.1 + 1, p.2 - 1) : Pixel).1, ((p.1 + 1, p.2 - 1) : Pixel).2 + 1) =
      ((p.1 + 1, p.2) : Pixel) := by ext <;> simp
  have hesc := crack_escape B p C (p.1 + 1, p.2 - 1) hc0 hfree
    (by ext <;> simp) hpC
    (by rw [hS2]; exact fun h => hS ((memC _).1 h).1)
    (by rw [hE2]; exact fun h => hE ((memC _).1 h).1)
  rw [hS2, hE2] at hesc
  obtain ⟨hS0, hE0, hr⟩ := hesc
  obtain ⟨hS1, henc⟩ := hs
  apply not_enclosed_above B p hb (p.1 + 1, p.2) (Or.inr ⟨rfl, by simp⟩) hE0
  have e2 : (complementGraph (insert p B)).connectedComponentMk
      ⟨(p.1 + 1, p.2), by simpa using hE0⟩ =
      (complementGraph (insert p B)).connectedComponentMk
      ⟨(p.1, p.2 - 1), mem_compl_insert B p (by simp [Prod.ext_iff]) hS1⟩ :=
    SimpleGraph.ConnectedComponent.eq.2 hr.symm
  rw [e2]; exact henc

end Final

/-- The bridge equation `enc = C8 − χ` for every finite raster (the equation of `P1.Bridge`). -/
theorem bridge_eq (B : Finset Pixel) : (enclosed B : ℤ) = C8 B - euler B :=
  bridge_of_halfplane_jordan (fun B p _ hb hS hSE _ =>
    ⟨fun hs => join_of_senc B p ‹_› hb hS hSE hs, senc_of_join B p hb hS⟩) B

/-- **`P1.Insertion`.** -/
theorem main : ViridisStatements.P1.Insertion.Statement :=
  statement_of_enc_join fun B p hp hb hS hSE _ hs => join_of_senc B p hp hb hS hSE hs

end Candidate
