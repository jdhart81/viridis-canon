import Mathlib

/-!
# P1 · L2: single-pixel insertion

Adding one barrier pixel `p ∉ B` to a finite raster leaves
`enclosed − C8 + χ` unchanged, under (8,4) connectivity. There is no hypothesis
on the 3×3 neighbourhood of `p`: every one of its 256 configurations is covered,
including insertions that merge several 8-components and insertions that close
or split holes.

The definitions of `C8`, `enclosed` and their conventions are identical to those
in the `P1.Bridge` proposal (complement taken in all of `ℤ²`; enclosed means
finite). `χ` is `euler`, restated verbatim from the sealed rung L1 `P1.BitQuad`.

This is the second rung (L2) of the P1 ladder: the inductive step for L3.
-/

namespace ViridisStatements.P1.Insertion

/-! ## Definitions restated from the sealed module `P1.BitQuad`

The proposal environment does not load the sealed module `ViridisStatements.P1.BitQuad`,
so the definitions this statement needs are restated here, character for character
identical to that module (sealed rung L1). Once the module can be imported, these may
be replaced by `open ViridisStatements.P1.BitQuad` without changing any meaning. -/

/-- A pixel, named by its lower-left lattice corner. -/
abbrev Pixel := ℤ × ℤ

/-- The four lattice corners of pixel `p`. -/
def corners (p : Pixel) : Finset (ℤ × ℤ) :=
  {(p.1, p.2), (p.1 + 1, p.2), (p.1, p.2 + 1), (p.1 + 1, p.2 + 1)}

/-- Vertices of `K B`: every corner of every pixel of `B`. -/
def vertices (B : Finset Pixel) : Finset (ℤ × ℤ) :=
  B.biUnion corners

/-- Horizontal unit edges `[(i, j), (i + 1, j)]` of `K B`, named by their left
end. These are the bottom edge `(i, j)` and the top edge `(i, j + 1)` of each
pixel `(i, j)` of `B`. -/
def hEdges (B : Finset Pixel) : Finset (ℤ × ℤ) :=
  B.biUnion fun p => {(p.1, p.2), (p.1, p.2 + 1)}

/-- Vertical unit edges `[(i, j), (i, j + 1)]` of `K B`, named by their lower
end. These are the left edge `(i, j)` and the right edge `(i + 1, j)` of each
pixel `(i, j)` of `B`. -/
def vEdges (B : Finset Pixel) : Finset (ℤ × ℤ) :=
  B.biUnion fun p => {(p.1, p.2), (p.1 + 1, p.2)}

/-- The Euler characteristic `V − E + F` of `K B`. -/
def euler (B : Finset Pixel) : ℤ :=
  ((vertices B).card : ℤ) - (((hEdges B).card : ℤ) + (vEdges B).card) + B.card

/-! ## Connectivity on `ℤ²`

The adjacency relations are the usual digital-topology ones. `fromRel` symmetrises
the relation and removes loops, so no side proofs are needed. -/

/-- 4-adjacency: pixels that share an edge. -/
def G4 : SimpleGraph Pixel :=
  SimpleGraph.fromRel fun p q => |p.1 - q.1| + |p.2 - q.2| = 1

/-- 8-adjacency: distinct pixels that share an edge or a corner. -/
def G8 : SimpleGraph Pixel :=
  SimpleGraph.fromRel fun p q => |p.1 - q.1| ≤ 1 ∧ |p.2 - q.2| ≤ 1

/-- The barrier `B`, read with 8-adjacency. -/
def barrierGraph (B : Finset Pixel) : SimpleGraph (B : Set Pixel) :=
  G8.induce (B : Set Pixel)

/-- The complement `ℤ² \ B` (taken in all of `ℤ²`), read with 4-adjacency. -/
def complementGraph (B : Finset Pixel) : SimpleGraph ((B : Set Pixel)ᶜ : Set Pixel) :=
  G4.induce (B : Set Pixel)ᶜ

/-- `C8(B)`: the number of 8-components of the barrier. `B` is finite, so this
`Nat.card` is a genuine count. -/
noncomputable def C8 (B : Finset Pixel) : ℕ :=
  Nat.card (barrierGraph B).ConnectedComponent

/-- A 4-component of `ℤ² \ B` is enclosed when it is finite. -/
def IsEnclosed {B : Finset Pixel} (c : (complementGraph B).ConnectedComponent) : Prop :=
  c.supp.Finite

/-- The number of enclosed 4-components of `ℤ² \ B`. (`Nat.card` would read 0 on an
infinite type; `P1.Bridge` therefore also asserts that there are finitely many
enclosed components.) -/
noncomputable def enclosed (B : Finset Pixel) : ℕ :=
  Nat.card {c : (complementGraph B).ConnectedComponent // IsEnclosed c}

/-- The quantity that L2 says is invariant, and that L3 says is zero. -/
noncomputable def invariant (B : Finset Pixel) : ℤ :=
  (enclosed B : ℤ) - C8 B + euler B

/-- **Proposed target `P1.Insertion`.** Inserting any non-barrier pixel into any
finite raster leaves `enclosed − C8 + χ` unchanged. -/
def Statement : Prop :=
  ∀ (B : Finset Pixel) (p : Pixel), p ∉ B → invariant (insert p B) = invariant B

/-! ## A computable bounded-box model (test oracle only)

`Statement` does not mention anything in this section. The definitions below
recompute `C8` and the enclosed count inside a bounding box with a one-pixel
margin, by flood fill, so that the controls can be checked by `decide`. That the
box model agrees with the definitions above on every finite raster is a lemma
for the proving task. It is not claimed here. The control values are also proved
for the semantic definitions themselves at the end of this file. -/

/-- Decidable 4-adjacency (same relation as `G4`). -/
def adj4 (p q : Pixel) : Prop := |p.1 - q.1| + |p.2 - q.2| = 1

/-- Decidable 8-adjacency (same relation as `G8`). -/
def adj8 (p q : Pixel) : Prop := p ≠ q ∧ |p.1 - q.1| ≤ 1 ∧ |p.2 - q.2| ≤ 1

instance : DecidableRel adj4 := fun _ _ => by unfold adj4; infer_instance
instance : DecidableRel adj8 := fun _ _ => by unfold adj8; infer_instance

/-- Lexicographic order on pixels, used to pick one representative per component. -/
def lexLe (p q : Pixel) : Prop := p.1 < q.1 ∨ (p.1 = q.1 ∧ p.2 ≤ q.2)

instance : DecidableRel lexLe := fun _ _ => by unfold lexLe; infer_instance

/-- One flood-fill step inside `A`. -/
def grow (r : Pixel → Pixel → Prop) [DecidableRel r] (A S : Finset Pixel) : Finset Pixel :=
  S ∪ A.filter fun q => ∃ s ∈ S, r s q

/-- Everything in `A` reachable from `S` through `A`; `|A|` steps suffice. -/
def reach (r : Pixel → Pixel → Prop) [DecidableRel r] (A S : Finset Pixel) : Finset Pixel :=
  (grow r A)^[A.card] S

/-- The number of `r`-components of `A`: count the lexicographically least pixel
of each component. -/
def numComponents (r : Pixel → Pixel → Prop) [DecidableRel r] (A : Finset Pixel) : ℕ :=
  (A.filter fun q => ∀ s ∈ reach r A {q}, lexLe q s).card

/-- Bounding box of `B ∪ {(0, 0)}`, with a margin of one pixel on every side. -/
def xlo (B : Finset Pixel) : ℤ := B.fold min 0 (·.1) - 1
def xhi (B : Finset Pixel) : ℤ := B.fold max 0 (·.1) + 1
def ylo (B : Finset Pixel) : ℤ := B.fold min 0 (·.2) - 1
def yhi (B : Finset Pixel) : ℤ := B.fold max 0 (·.2) + 1
def box (B : Finset Pixel) : Finset Pixel :=
  Finset.Icc (xlo B) (xhi B) ×ˢ Finset.Icc (ylo B) (yhi B)

/-- Non-barrier pixels of the box that reach the box corner, which lies in the
unbounded component. -/
def exterior (B : Finset Pixel) : Finset Pixel :=
  reach adj4 (box B \ B) {(xlo B, ylo B)}

/-- Non-barrier pixels of the box that do not reach the corner. -/
def holes (B : Finset Pixel) : Finset Pixel := (box B \ B) \ exterior B

/-- Box-model count of enclosed 4-components. -/
def boxEnclosed (B : Finset Pixel) : ℕ := numComponents adj4 (holes B)

/-- Box-model count of 8-components of the barrier. -/
def boxC8 (B : Finset Pixel) : ℕ := numComponents adj8 B

/-! ## Control rasters -/

/-- Witness: the 3×3 ring, eight pixels around the empty centre `(1, 1)`. -/
def ring : Finset Pixel := {(0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)}

/-- Negative control 1: the solid 2×2 block. Its 8-adjacency graph is `K₄`. -/
def block : Finset Pixel := {(0, 0), (1, 0), (0, 1), (1, 1)}

/-- Negative control 2: the four pixels N, S, E, W of the empty centre `(1, 1)`.
Their 4-adjacency graph has no edges, but under (8,4) they enclose the centre. -/
def diamond : Finset Pixel := {(1, 0), (0, 1), (2, 1), (1, 2)}

/-- Box-model version of `invariant`, computable. -/
def boxInvariant (B : Finset Pixel) : ℤ :=
  (boxEnclosed B : ℤ) - boxC8 B + euler B

/-! ## Sanity checks by `decide` (box model)

The controls of the ladder, and insertions that exercise the non-local cases. -/

set_option maxRecDepth 100000 in
/-- Witness: the 3×3 ring has `C8 = 1`, `χ = 0` and one enclosed component. -/
example : boxC8 ring = 1 ∧ euler ring = 0 ∧ boxEnclosed ring = 1 := by decide

set_option maxRecDepth 100000 in
/-- Negative control 1: the 2×2 block has `C8 = 1`, `χ = 1` and encloses nothing. -/
example : boxC8 block = 1 ∧ euler block = 1 ∧ boxEnclosed block = 0 := by decide

set_option maxRecDepth 100000 in
/-- Negative control 2: the diamond has `C8 = 1`, `χ = 0` and one enclosed
component under (8,4). -/
example : boxC8 diamond = 1 ∧ euler diamond = 0 ∧ boxEnclosed diamond = 1 := by decide

set_option maxRecDepth 100000 in
/-- Closing a hole: inserting `(1, 2)` into the ring with its top middle removed
keeps `C8 = 1`, drops `χ` from 1 to 0 and creates one enclosed component. -/
example : boxInvariant (ring.erase (1, 2)) = 0 ∧ boxInvariant ring = 0 ∧
    boxEnclosed (ring.erase (1, 2)) = 0 ∧ euler (ring.erase (1, 2)) = 1 := by decide

set_option maxRecDepth 100000 in
/-- Merging: the left and right columns of the ring are two 8-components
(`χ = 2`). Inserting `(1, 0)` merges them (`C8 = 1`, `χ = 1`, nothing enclosed). -/
example : boxC8 ({(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)} : Finset Pixel) = 2 ∧
    euler ({(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)} : Finset Pixel) = 2 ∧
    boxInvariant ({(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)} : Finset Pixel) = 0 ∧
    boxInvariant ({(1, 0), (0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)} : Finset Pixel) = 0 := by
  decide

set_option maxRecDepth 100000 in
/-- Corner-only merging: inserting the last pixel of the diamond joins three
corner-touching pixels into a cycle and encloses the centre. -/
example : boxInvariant (diamond.erase (1, 2)) = 0 ∧ boxEnclosed (diamond.erase (1, 2)) = 0 ∧
    euler (diamond.erase (1, 2)) = 1 ∧ boxInvariant diamond = 0 := by decide

set_option maxRecDepth 100000 in
/-- Filling a hole: inserting the centre `(1, 1)` into the ring removes the enclosed
component and raises `χ` from 0 to 1, giving the solid 3×3 block. -/
example : boxInvariant (insert (1, 1) ring) = 0 ∧ boxEnclosed (insert (1, 1) ring) = 0 ∧
    euler (insert (1, 1) ring) = 1 := by decide


/-! ## Every configuration of the 3×3 neighbourhood, by `decide` (bitmask model)

`Statement` does not mention anything in this section. It is a second, independent
test oracle, written with natural-number bit operations so that the kernel can check
all 256 configurations of the eight neighbours of an inserted pixel in seconds.

The model lives in a 7×7 box: pixel `(x, y)` with `0 ≤ x, y < 7` is bit `7 * y + x`.
Barrier pixels are confined to the inner 5×5, so the box border is non-barrier and
4-connected, and its 4-component is the unbounded one. `chi` counts `V − E + F` with
the same naming of vertices and edges as `euler` (lower-left corner, left end,
lower end). As with the box model, agreement with the semantic definitions is not
proved here. -/

namespace Mask

/-- All 49 bits of the box. -/
def full : ℕ := 2 ^ 49 - 1

/-- The box without column 0. -/
def notCol0 : ℕ := full - (List.range 7).foldl (fun a y => a + 2 ^ (7 * y)) 0

/-- The box without column 6. -/
def notCol6 : ℕ := full - (List.range 7).foldl (fun a y => a + 2 ^ (7 * y + 6)) 0

/-- Left and right neighbours of a set of pixels (no wrap-around). -/
def horiz (S : ℕ) : ℕ := ((S &&& notCol6) <<< 1) ||| ((S &&& notCol0) >>> 1)

/-- Lower and upper neighbours of a set of pixels, inside the box. -/
def vert (S : ℕ) : ℕ := ((S <<< 7) ||| (S >>> 7)) &&& full

/-- `S` together with its 4-neighbours. -/
def nbr4 (S : ℕ) : ℕ := S ||| horiz S ||| vert S

/-- `S` together with its 8-neighbours. -/
def nbr8 (S : ℕ) : ℕ := let H := S ||| horiz S; H ||| vert H

/-- Flood fill from `S` inside `A`, with fuel. -/
def fill (nb : ℕ → ℕ) (A S : ℕ) : ℕ → ℕ
  | 0 => S
  | n + 1 => let S' := nb S &&& A; if S' = S then S else fill nb A S' n

/-- The lowest set bit of `A`. -/
def lowBit (A : ℕ) : ℕ := A - (A &&& (A - 1))

/-- The number of components of `A`: peel off the component of the lowest bit. -/
def countComp (nb : ℕ → ℕ) : ℕ → ℕ → ℕ
  | 0, _ => 0
  | n + 1, A => if A = 0 then 0 else 1 + countComp nb n (A ^^^ fill nb A (lowBit A) 49)

/-- The number of set bits among the lowest `n`. -/
def popcount : ℕ → ℕ → ℕ
  | 0, _ => 0
  | n + 1, m => m % 2 + popcount n (m / 2)

/-- 8-components of the barrier. -/
def c8 (B : ℕ) : ℕ := countComp nbr8 49 B

/-- 4-components of the non-barrier pixels that do not reach the box corner. -/
def enc (B : ℕ) : ℕ :=
  let C := full ^^^ B
  countComp nbr4 49 (C ^^^ fill nbr4 C 1 49)

/-- `V − E + F`. Vertices are the lower-left corners of the pixels at offsets
(0,0), (1,0), (0,1), (1,1) from a barrier pixel; horizontal edges those at offsets
(0,0), (0,1); vertical edges those at offsets (0,0), (1,0). -/
def chi (B : ℕ) : ℤ :=
  (popcount 64 (B ||| (B <<< 1) ||| (B <<< 7) ||| (B <<< 8)) : ℤ)
    - ((popcount 64 (B ||| (B <<< 7)) : ℤ) + popcount 64 (B ||| (B <<< 1)))
    + popcount 64 B

/-- The model's `enclosed − C8 + χ`. -/
def inv (B : ℕ) : ℤ := (enc B : ℤ) - c8 B + chi B

/-- The inserted pixel `p`, at the centre `(3, 3)` of the box. -/
def centre : ℕ := 2 ^ 24

/-- The bits of the eight neighbours of `p`, in the order SW, S, SE, W, E, NW, N, NE. -/
def nbIdx : List ℕ := [16, 17, 18, 23, 25, 30, 31, 32]

/-- Neighbourhood configuration `m < 256`, as a set of barrier pixels around `p`. -/
def spread (m : ℕ) : ℕ :=
  (List.range 8).foldl (fun a i => if m.testBit i then a ||| 2 ^ (nbIdx.getD i 0) else a) 0

/-- The 16 pixels at Chebyshev distance 2 from `p`. As a context, it 8-connects every
barrier neighbour of `p` to every other one, outside the 3×3 window. -/
def ring5 : ℕ := (List.range 49).foldl (fun a i =>
  let x := i % 7; let y := i / 7
  if (x = 1 ∨ x = 5) ∧ 1 ≤ y ∧ y ≤ 5 ∨ (y = 1 ∨ y = 5) ∧ 1 ≤ x ∧ x ≤ 5 then a ||| 2 ^ i
  else a) 0

/-- For every configuration `m < n` of the eight neighbours, placed in context `ctx`:
the invariant is `0` before and after inserting `p`, so it is unchanged. -/
def allConfigs (ctx : ℕ) : ℕ → Bool
  | 0 => true
  | n + 1 =>
    let B := ctx ||| spread n
    (inv (B ||| centre) == inv B && inv B == 0) && allConfigs ctx n

/-- Witness in the bitmask model: the eight neighbours of `p` form the 3×3 ring. -/
example : enc (spread 255) = 1 ∧ c8 (spread 255) = 1 ∧ chi (spread 255) = 0 := by decide

/-- Negative control 1 in the bitmask model: the 2×2 block `{p, W, S, SW}`. -/
example : enc (centre ||| spread 0b1011) = 0 ∧ c8 (centre ||| spread 0b1011) = 1 ∧
    chi (centre ||| spread 0b1011) = 1 := by decide

/-- Negative control 2 in the bitmask model: the diamond `{S, W, E, N}` encloses `p`. -/
example : enc (spread 0b01011010) = 1 ∧ c8 (spread 0b01011010) = 1 ∧
    chi (spread 0b01011010) = 0 ∧ countComp nbr4 49 (spread 0b01011010) = 4 := by decide

set_option maxRecDepth 100000 in
/-- **All 256 configurations, alone.** For every subset `N` of the eight neighbours of
`p`, inserting `p` into `N` leaves `enclosed − C8 + χ` unchanged (and equal to `0`).
This covers all 512 subsets of the 3×3 window. -/
example : allConfigs 0 256 = true := by decide

set_option maxRecDepth 100000 in
/-- **All 256 configurations, inside a closed ring.** The same, with the 5×5 ring `ring5`
added as context. Now all barrier neighbours of `p` are already 8-connected through
the ring, so inserting `p` never merges 8-components, and every non-barrier run around
`p` lies in a finite region. -/
example : allConfigs ring5 256 = true := by decide

end Mask

/-! ## The controls for the semantic definitions

The checks above use the box model. The lemmas below prove the same control
values for `C8` and `enclosed` themselves (the definitions that `Statement`
uses), with no appeal to the box model: a horizontal ray of non-barrier pixels
makes a component infinite, and a non-barrier pixel whose four 4-neighbours are
barrier is a finite component on its own. -/

namespace Controls

/-- A horizontal ray of non-barrier pixels makes a component infinite. -/
theorem infinite_of_ray (B : Finset Pixel) (v : Pixel) (hv : v ∉ B) (d : ℤ) (hd : d = 1 ∨ d = -1)
    (hray : ∀ n : ℕ, (v.1 + d * n, v.2) ∉ B) :
    ¬ IsEnclosed ((complementGraph B).connectedComponentMk ⟨v, hv⟩) := by
  intro hfin
  have hreach : ∀ n : ℕ, (complementGraph B).Reachable ⟨v, hv⟩ ⟨(v.1 + d * n, v.2), hray n⟩ := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
      refine ih.trans (SimpleGraph.Adj.reachable ?_)
      simp only [complementGraph, SimpleGraph.comap_adj, SimpleGraph.induce, G4,
        SimpleGraph.fromRel_adj, Function.Embedding.coe_subtype, ne_eq, Prod.mk.injEq]
      push_cast
      rcases hd with rfl | rfl <;> refine ⟨by omega, Or.inl ?_⟩ <;> simp
  apply Set.infinite_of_injective_forall_mem (f := fun n : ℕ => (⟨(v.1 + d * n, v.2), hray n⟩ :
    ((B : Set Pixel)ᶜ : Set Pixel)))
  · intro m n h
    simp only [Subtype.mk.injEq, Prod.mk.injEq] at h
    rcases hd with rfl | rfl <;> omega
  · intro n
    exact (SimpleGraph.ConnectedComponent.mem_supp_iff _ _).2
      (SimpleGraph.ConnectedComponent.eq.2 (hreach n).symm)
  · exact hfin


theorem ray_right (B : Finset Pixel) (v : Pixel) (h : ∀ b ∈ B, b.2 = v.2 → b.1 < v.1) :
    ∀ n : ℕ, (v.1 + 1 * n, v.2) ∉ B := by
  intro n hb
  have := h _ hb rfl
  simp at this; omega

theorem ray_left (B : Finset Pixel) (v : Pixel) (h : ∀ b ∈ B, b.2 = v.2 → v.1 < b.1) :
    ∀ n : ℕ, (v.1 + (-1) * n, v.2) ∉ B := by
  intro n hb
  have := h _ hb rfl
  simp at this; omega

/-- A pixel whose four 4-neighbours are all barrier is a finite component on its own. -/
theorem isolated (B : Finset Pixel) (h : Pixel) (hh : h ∉ B)
    (hn : ∀ u : Pixel, |h.1 - u.1| + |h.2 - u.2| = 1 → u ∈ B) :
    IsEnclosed ((complementGraph B).connectedComponentMk ⟨h, hh⟩) := by
  apply (Set.finite_singleton (⟨h, hh⟩ : ((B : Set Pixel)ᶜ : Set Pixel))).subset
  intro w hw
  rw [SimpleGraph.ConnectedComponent.mem_supp_iff, SimpleGraph.ConnectedComponent.eq] at hw
  obtain ⟨p⟩ := hw.symm
  cases p with
  | nil => rfl
  | @cons _ u _ hadj _ =>
    exfalso
    simp only [complementGraph, SimpleGraph.comap_adj, SimpleGraph.induce, G4,
      SimpleGraph.fromRel_adj, Function.Embedding.coe_subtype] at hadj
    obtain ⟨-, hr | hr⟩ := hadj
    · exact u.2 (hn _ hr)
    · exact u.2 (hn _ (by rw [abs_sub_comm h.1, abs_sub_comm h.2]; exact hr))

theorem enclosed_eq_zero (B : Finset Pixel)
    (h : ∀ v (hv : v ∉ B), ¬ IsEnclosed ((complementGraph B).connectedComponentMk ⟨v, hv⟩)) :
    enclosed B = 0 := by
  rw [enclosed, Nat.card_eq_zero]
  left
  constructor
  rintro ⟨c, hc⟩
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h v => exact h v.1 v.2 hc

theorem enclosed_eq_one (B : Finset Pixel) (h : Pixel) (hh : h ∉ B)
    (hiso : IsEnclosed ((complementGraph B).connectedComponentMk ⟨h, hh⟩))
    (hrest : ∀ v (hv : v ∉ B), v ≠ h →
      ¬ IsEnclosed ((complementGraph B).connectedComponentMk ⟨v, hv⟩)) :
    enclosed B = 1 := by
  rw [enclosed, Nat.card_eq_one_iff_unique]
  refine ⟨⟨?_⟩, ⟨⟨_, hiso⟩⟩⟩
  have key : ∀ x : {c : (complementGraph B).ConnectedComponent // IsEnclosed c},
      x.1 = (complementGraph B).connectedComponentMk ⟨h, hh⟩ := by
    rintro ⟨c, hc⟩
    induction c using SimpleGraph.ConnectedComponent.ind with
    | h v =>
      by_cases hvh : v.1 = h
      · obtain ⟨v, hv⟩ := v; subst hvh; rfl
      · exact absurd hc (hrest v.1 v.2 hvh)
  intro x y
  exact Subtype.ext ((key x).trans (key y).symm)

theorem enclosed_ring : enclosed ring = 1 := by
  refine enclosed_eq_one ring (1, 1) (by decide) (isolated _ _ _ ?_) ?_
  · rintro ⟨x, y⟩ h
    have h' : |1 - x| + |1 - y| = 1 := h
    simp only [ring, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq]
    rcases abs_cases (1 - x) with ⟨h1, h1'⟩ | ⟨h1, h1'⟩ <;>
    rcases abs_cases (1 - y) with ⟨h2, h2'⟩ | ⟨h2, h2'⟩ <;> omega
  · rintro ⟨x, y⟩ hv hne
    simp only [ring, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq, not_or] at hv
    simp only [ne_eq, Prod.mk.injEq] at hne
    by_cases hr : 2 < x ∨ y < 0 ∨ 2 < y
    · refine infinite_of_ray _ _ _ 1 (Or.inl rfl) (ray_right _ _ ?_)
      simp only [ring, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
      omega
    · refine infinite_of_ray _ _ _ (-1) (Or.inr rfl) (ray_left _ _ ?_)
      simp only [ring, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
      omega

theorem enclosed_block : enclosed block = 0 := by
  refine enclosed_eq_zero block ?_
  rintro ⟨x, y⟩ hv
  simp only [block, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq, not_or] at hv
  by_cases hr : 1 < x ∨ y < 0 ∨ 1 < y
  · refine infinite_of_ray _ _ _ 1 (Or.inl rfl) (ray_right _ _ ?_)
    simp only [block, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
    omega
  · refine infinite_of_ray _ _ _ (-1) (Or.inr rfl) (ray_left _ _ ?_)
    simp only [block, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
    omega

theorem enclosed_diamond : enclosed diamond = 1 := by
  refine enclosed_eq_one diamond (1, 1) (by decide) (isolated _ _ _ ?_) ?_
  · rintro ⟨x, y⟩ h
    have h' : |1 - x| + |1 - y| = 1 := h
    simp only [diamond, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq]
    rcases abs_cases (1 - x) with ⟨h1, h1'⟩ | ⟨h1, h1'⟩ <;>
    rcases abs_cases (1 - y) with ⟨h2, h2'⟩ | ⟨h2, h2'⟩ <;> omega
  · rintro ⟨x, y⟩ hv hne
    simp only [diamond, Finset.mem_insert, Finset.mem_singleton, Prod.mk.injEq, not_or] at hv
    simp only [ne_eq, Prod.mk.injEq] at hne
    by_cases hr : 1 < x ∨ (x = 1 ∧ (y < 0 ∨ 2 < y))
    · refine infinite_of_ray _ _ _ 1 (Or.inl rfl) (ray_right _ _ ?_)
      simp only [diamond, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
      omega
    · refine infinite_of_ray _ _ _ (-1) (Or.inr rfl) (ray_left _ _ ?_)
      simp only [diamond, Finset.mem_insert, Finset.mem_singleton, forall_eq_or_imp, forall_eq]
      omega


theorem barrier_adj (B : Finset Pixel) (a b : Pixel) (ha : a ∈ B) (hb : b ∈ B)
    (h : a ≠ b ∧ |a.1 - b.1| ≤ 1 ∧ |a.2 - b.2| ≤ 1) :
    (barrierGraph B).Reachable ⟨a, ha⟩ ⟨b, hb⟩ := by
  refine SimpleGraph.Adj.reachable ?_
  simp only [barrierGraph, SimpleGraph.comap_adj, SimpleGraph.induce, G8,
    SimpleGraph.fromRel_adj, Function.Embedding.coe_subtype]
  exact ⟨h.1, Or.inl h.2⟩

theorem C8_eq_one (B : Finset Pixel) (b₀ : Pixel) (h₀ : b₀ ∈ B)
    (hr : ∀ b (hb : b ∈ B), (barrierGraph B).Reachable ⟨b₀, h₀⟩ ⟨b, hb⟩) : C8 B = 1 := by
  rw [C8, Nat.card_eq_one_iff_unique]
  refine ⟨⟨fun x y => ?_⟩, ⟨(barrierGraph B).connectedComponentMk ⟨b₀, h₀⟩⟩⟩
  induction x using SimpleGraph.ConnectedComponent.ind with
  | h v =>
  induction y using SimpleGraph.ConnectedComponent.ind with
  | h w =>
    exact SimpleGraph.ConnectedComponent.eq.2 ((hr v.1 v.2).symm.trans (hr w.1 w.2))

theorem C8_empty_eq : C8 ∅ = 0 := by
  rw [C8, Nat.card_eq_zero]
  left
  constructor
  intro c
  induction c using SimpleGraph.ConnectedComponent.ind with
  | h v => simpa using v.2

theorem enclosed_empty : enclosed ∅ = 0 :=
  enclosed_eq_zero ∅ fun v _ => infinite_of_ray _ _ _ 1 (Or.inl rfl) (ray_right _ _ (by simp))

theorem C8_block : C8 block = 1 := by
  refine C8_eq_one block (0, 0) (by decide) ?_
  intro b hb
  simp only [block, Finset.mem_insert, Finset.mem_singleton] at hb
  rcases hb with rfl | rfl | rfl | rfl
  · rfl
  all_goals exact barrier_adj _ _ _ _ _ (by decide)

theorem C8_diamond : C8 diamond = 1 := by
  refine C8_eq_one diamond (1, 0) (by decide) ?_
  intro b hb
  simp only [diamond, Finset.mem_insert, Finset.mem_singleton] at hb
  rcases hb with rfl | rfl | rfl | rfl
  · rfl
  · exact barrier_adj _ _ _ _ _ (by decide)
  · exact barrier_adj _ _ _ _ _ (by decide)
  · exact (barrier_adj _ (1, 0) (0, 1) (by decide) (by decide) (by decide)).trans
      (barrier_adj _ _ _ _ _ (by decide))

theorem C8_ring : C8 ring = 1 := by
  refine C8_eq_one ring (1, 0) (by decide) ?_
  have h01 : (0, 1) ∈ ring := by decide
  have h21 : (2, 1) ∈ ring := by decide
  intro b hb
  simp only [ring, Finset.mem_insert, Finset.mem_singleton] at hb
  rcases hb with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl
  · exact barrier_adj _ _ _ _ _ (by decide)
  · rfl
  · exact barrier_adj _ _ _ _ _ (by decide)
  · exact barrier_adj _ _ _ _ _ (by decide)
  · exact barrier_adj _ _ _ _ _ (by decide)
  · exact (barrier_adj _ (1, 0) (0, 1) (by decide) h01 (by decide)).trans
      (barrier_adj _ _ _ _ _ (by decide))
  · exact (barrier_adj _ (1, 0) (0, 1) (by decide) h01 (by decide)).trans
      (barrier_adj _ _ _ _ _ (by decide))
  · exact (barrier_adj _ (1, 0) (2, 1) (by decide) h21 (by decide)).trans
      (barrier_adj _ _ _ _ _ (by decide))

end Controls

open Controls in
/-- Witness, semantic: the ring has one enclosed component, and the identity
`enclosed = C8 − χ` holds for it (`1 = 1 − 0`). -/
example : enclosed ring = 1 ∧ C8 ring = 1 ∧ (enclosed ring : ℤ) = C8 ring - euler ring := by
  refine ⟨enclosed_ring, C8_ring, ?_⟩
  rw [enclosed_ring, C8_ring]
  decide

open Controls in
/-- Negative control 1, semantic: the block encloses nothing (`0 = 1 − 1`). -/
example : enclosed block = 0 ∧ C8 block = 1 ∧ (enclosed block : ℤ) = C8 block - euler block := by
  refine ⟨enclosed_block, C8_block, ?_⟩
  rw [enclosed_block, C8_block]
  decide

open Controls in
/-- Negative control 2, semantic: the diamond encloses its centre (`1 = 1 − 0`). -/
example : enclosed diamond = 1 ∧ C8 diamond = 1 ∧
    (enclosed diamond : ℤ) = C8 diamond - euler diamond := by
  refine ⟨enclosed_diamond, C8_diamond, ?_⟩
  rw [enclosed_diamond, C8_diamond]
  decide

open Controls in
/-- Empty raster, semantic: `C8 = 0`, `χ = 0`, nothing enclosed. -/
example : enclosed ∅ = 0 ∧ C8 ∅ = 0 ∧ euler ∅ = 0 :=
  ⟨enclosed_empty, C8_empty_eq, by decide⟩

end ViridisStatements.P1.Insertion
