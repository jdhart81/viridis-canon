/-
The Ecopoietic Succession-Ordering Theorem (ESOT) — combinatorial core
======================================================================

Nightly science-engine Run 095 — [15] Ecoterraforming × Thermodynamic ("the Mason").
DEDICATED COMBINATORIAL RUN. The clean analytic core (R1/R4/R5/R6) was landed
2026-07-11 in `EcopoieticSuccession.lean`. This module discharges the two pieces
that were DEFERRED there as genuine combinatorial-optimization statements:

  R2  greedy / minimax build-order optimality under monotone facilitation, and
  R3  the θ-reachable-closure FIXPOINT and the reachability wall
      (target biosphere reachable ⇔ drive budget clears the minimax bottleneck B⋆).

Model.
  Layers indexed by a finite type `L`. Layer `k` has bare barrier `Psi0 k`.
  An established set `S` lowers `k`'s barrier by `∑_{j∈S} f j k`, with `f ≥ 0`
  (MONOTONE facilitation — the load-bearing premise):
        residual Psi0 f k S = Psi0 k - ∑_{j∈S} f j k.                       (R1)
  A layer is *ignitable* under drive budget θ iff its residual barrier ≤ θ.
  θ-reachable closure = least fixpoint of "add every layer with residual ≤ θ",
  reached by iterating the extensive, monotone one-step operator `reachStep`.
  A build ORDER is a permutation of the not-yet-established layers; its makespan
  bottleneck is the largest residual barrier encountered along the build
  (`obAux`), and `Bstar = min over orders`.

Named theorems (this file):
  residual_antitone_in_established                       (R1 monotonicity)
  reachStep_extensive
  reachStep_mono_in_established                          (monotone premise, load-bearing)
  reachStep_mono_in_budget
  reachClosure_extensive
  reach_closure_is_fixpoint                              (θ-reachable-closure FIXPOINT)
  reach_closure_monotone_in_budget                      (verified numerically in the run)
  reachability_wall_is_up_set                           (R3 threshold form)
  reachability_critical_budget_eq_minimax_bottleneck    (R2⊗R3: greedy minimax = critical budget)
  reachability_iff_budget_geq_minimax_bottleneck        (R3 sharp: reachable ⇔ θ ≥ B⋆)
  esot_ordering_nonvacuous                              (explicit wall-binding witness)

Every statement is intended NON-VACUOUSLY (see `esot_ordering_nonvacuous`,
where the reachability wall strictly binds).

FORGE NOTES (deviations from the deferred stubs, flagged as required).

  (A) `obAux` base case. The deferred stub set `obAux _ [] = 0`, which silently
      injects a spurious `max (·) 0` at the END of every build order, forcing
      `obAux ≥ 0` and hence `Bstar ≥ 0` for EVERY instance. That makes the sharp
      wall FALSE whenever the true minimax bottleneck is negative (easy ignition,
      e.g. `Psi0 ≡ -5`, `f ≡ 0`, `seed = ∅`: reachable at θ = -3, yet the stub
      gives `Bstar = 0 > -3`). We STRENGTHEN the auxiliary definition to the
      faithful "largest residual actually crossed" by treating the singleton build
      `[k]` as its own base case (`obAux S [k] = residual … k S`), so no phantom
      `0` is folded in. The `[] ↦ 0` clause is retained only for totality; it is
      never reached by any genuine (nonempty) build order.

  (B) `(univ \ seed).Nonempty` hypothesis on the two wall theorems. When
      `seed = univ` the whole biosphere is ALREADY established, so `reachable`
      holds at EVERY budget θ (including arbitrarily negative θ): the reachable-
      budget set is all of `ℝ`, which has no least element and is not `[B⋆, ∞)`
      for any real `B⋆`. Thus `IsLeast … B⋆` and the sharp `reachable ↔ B⋆ ≤ θ`
      are unavoidably false in that single degenerate case for ANY real `B⋆`
      (they would require `B⋆ = -∞`). We add the minimal faithful side condition
      `(univ \ seed).Nonempty` (equivalently `seed ≠ univ`, i.e. there is at
      least one layer left to build), under which both statements hold sharply and
      NON-VACUOUSLY (the witness in `esot_ordering_nonvacuous` has `seed = ∅`,
      `univ \ ∅ = univ` nonempty). No non-trivial conclusion is collapsed.
-/

import Mathlib

open Finset
open scoped BigOperators
open Classical

namespace Viridis.Ecoterraforming.EcopoieticOrdering

/-! ### Generic finite-lattice iterate machinery -/

section Generic
variable {α : Type*} [DecidableEq α] [Fintype α]

omit [DecidableEq α] [Fintype α] in
/-- One iterate of an extensive operator only grows the set. -/
theorem iterate_subset_succ (g : Finset α → Finset α) (hext : ∀ S, S ⊆ g S)
    (S : Finset α) (n : ℕ) : g^[n] S ⊆ g^[n + 1] S := by
  rw [Function.iterate_succ_apply']
  exact hext _

omit [DecidableEq α] [Fintype α] in
/-- Iterating an extensive operator is extensive. -/
theorem iterate_extensive_gen (g : Finset α → Finset α) (hext : ∀ S, S ⊆ g S)
    (S : Finset α) (n : ℕ) : S ⊆ g^[n] S := by
  induction n with
  | zero => simp
  | succ k ih => exact ih.trans (iterate_subset_succ g hext S k)

omit [DecidableEq α] [Fintype α] in
/-- Comparing iterates of two operators `g ≤ h` (pointwise), with `h` monotone. -/
theorem iterate_compare_gen (g h : Finset α → Finset α) (hmono : Monotone h)
    (hgh : ∀ S, g S ⊆ h S) (seed : Finset α) (n : ℕ) :
    g^[n] seed ⊆ h^[n] seed := by
  induction n with
  | zero => simp
  | succ k ih =>
    rw [Function.iterate_succ_apply', Function.iterate_succ_apply']
    exact (hgh _).trans (hmono ih)

/-
**Finite-lattice fixpoint.** An extensive, monotone operator on a finite
powerset reaches a genuine fixpoint after `Fintype.card α + 1` iterations from any
seed: the increasing chain of finite sets must stabilize within `card α + 1` steps
(pigeonhole on cardinalities), and once it stabilizes it stays fixed.
-/
theorem exists_iterate_fixpoint (g : Finset α → Finset α) (hext : ∀ S, S ⊆ g S)
    (seed : Finset α) :
    g (g^[Fintype.card α + 1] seed) = g^[Fintype.card α + 1] seed := by
  -- By the pigeonhole principle, since there are only `Fintype.card α + 1` possible sizes for subsets of `α`, and we are iterating `g` for `Fintype.card α + 1` times, there must be some `m ≤ Fintype.card α` such that `g^[m] seed = g^[m+1] seed`.
  obtain ⟨m, hm⟩ : ∃ m ≤ Fintype.card α, g^[m] seed = g^[m+1] seed := by
    by_contra h_no_m;
    -- Since $g$ is extensive and monotone, the sequence of iterates $g^[n] seed$ is strictly increasing in terms of cardinality.
    have h_card_increasing : ∀ n ≤ Fintype.card α, (g^[n] seed).card < (g^[n + 1] seed).card := by
      intro n hn; exact Finset.card_lt_card ( lt_of_le_of_ne ( by simpa only [ Function.iterate_succ_apply' ] using hext _ ) fun h => h_no_m ⟨ n, hn, h ⟩ ) ;
    -- By induction, we can show that the cardinality of $g^[n] seed$ is at least $n$.
    have h_card_ge_n : ∀ n ≤ Fintype.card α + 1, (g^[n] seed).card ≥ n := by
      intro n hn; induction' n with n ih <;> simp_all +decide [ Function.iterate_succ_apply' ] ;
      linarith [ ih ( Nat.le_succ_of_le hn ), h_card_increasing n hn ];
    exact absurd ( h_card_ge_n ( Fintype.card α + 1 ) le_rfl ) ( by exact not_le_of_gt ( lt_of_le_of_lt ( Finset.card_le_univ _ ) ( by simp +decide ) ) );
  -- By induction on $n$, we can show that $g^[n] seed = g^[m] seed$ for all $n \geq m$.
  have h_ind : ∀ n ≥ m, g^[n] seed = g^[m] seed := by
    intro n hn;
    induction hn <;> simp_all +singlePass [ Function.iterate_succ_apply' ];
  rw [ h_ind _ ( by linarith ), ← Function.iterate_succ_apply' g m seed, ← hm.2 ]

end Generic

/-! ### The ESOT model -/

variable {L : Type*} [Fintype L] [DecidableEq L]

/-- Residual nucleation barrier of layer `k` given established set `S`, with
facilitation coupling `f`. -/
def residual (Psi0 : L → ℝ) (f : L → L → ℝ) (k : L) (S : Finset L) : ℝ :=
  Psi0 k - ∑ j ∈ S, f j k

/-
**R1 — Monotone facilitation ⇒ residual barrier is antitone in the established set.**
Enlarging `S ⊆ S'` never raises a downstream residual barrier when `f ≥ 0`.
This is the premise that makes the greedy sweep optimal and the closure well defined.
-/
omit [Fintype L] [DecidableEq L] in
theorem residual_antitone_in_established
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k)
    (k : L) {S S' : Finset L} (hSS : S ⊆ S') :
    residual Psi0 f k S' ≤ residual Psi0 f k S := by
  exact sub_le_sub_left ( Finset.sum_le_sum_of_subset_of_nonneg hSS fun _ _ _ => hf _ _ ) _

/-- One-step reachability operator: keep everything already established and add
every layer whose current residual barrier is at or below the drive budget `θ`. -/
noncomputable def reachStep (Psi0 : L → ℝ) (f : L → L → ℝ) (θ : ℝ) (S : Finset L) : Finset L := by
  classical
  exact S ∪ univ.filter (fun k => residual Psi0 f k S ≤ θ)

/-
The step operator is EXTENSIVE: nothing already built is lost.
-/
theorem reachStep_extensive (Psi0 : L → ℝ) (f : L → L → ℝ) (θ : ℝ) (S : Finset L) :
    S ⊆ reachStep Psi0 f θ S := by
  exact Finset.subset_union_left

/-
**Monotone premise, load-bearing.** With `f ≥ 0` the step operator is monotone
in the established set: growing the built set can only enlarge what becomes ignitable.
-/
theorem reachStep_mono_in_established
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (θ : ℝ)
    {S S' : Finset L} (hSS : S ⊆ S') :
    reachStep Psi0 f θ S ⊆ reachStep Psi0 f θ S' := by
  intro k hk
  simp [reachStep] at hk ⊢;
  exact Or.imp ( fun hk => hSS hk ) ( fun hk => le_trans ( residual_antitone_in_established Psi0 f hf k hSS ) hk ) hk

/-- Packaged monotonicity of the step operator in the established set. -/
theorem reachStep_monotone (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (θ : ℝ) :
    Monotone (reachStep Psi0 f θ) :=
  fun _ _ h => reachStep_mono_in_established Psi0 f hf θ h

/-
The step operator is monotone in the drive budget: a larger budget ignites at
least as much.
-/
theorem reachStep_mono_in_budget
    (Psi0 : L → ℝ) (f : L → L → ℝ) {θ θ' : ℝ} (hθ : θ ≤ θ') (S : Finset L) :
    reachStep Psi0 f θ S ⊆ reachStep Psi0 f θ' S := by
  -- Take k in S ∪ filter(residual · S ≤ θ). If k ∈ S, done. Otherwise residual Psi0 f k S ≤ θ ≤ θ', so k is in filter for θ'.
  simp [reachStep, Finset.subset_iff];
  exact fun x hx => Or.imp id ( fun hx' => le_trans hx' hθ ) hx

/-- θ-reachable closure: iterate the step operator `card L + 1` times from the seed,
which is enough for the extensive, monotone operator to reach its least fixpoint. -/
noncomputable def reachClosure
    (Psi0 : L → ℝ) (f : L → L → ℝ) (θ : ℝ) (seed : Finset L) : Finset L :=
  (reachStep Psi0 f θ)^[Fintype.card L + 1] seed

/-
The seed is contained in its reachable closure.
-/
theorem reachClosure_extensive
    (Psi0 : L → ℝ) (f : L → L → ℝ) (θ : ℝ) (seed : Finset L) :
    seed ⊆ reachClosure Psi0 f θ seed := by
  convert iterate_extensive_gen ( reachStep Psi0 f θ ) ( reachStep_extensive Psi0 f θ ) seed ( Fintype.card L + 1 )

/-
**R3 — the θ-reachable-closure FIXPOINT.** Under monotone facilitation the closure
is a genuine fixed point of the step operator: no further layer can be ignited at
budget `θ` once the closure is reached.

(The `hf : f ≥ 0` premise is kept verbatim as stated; the fixpoint in fact follows
from EXTENSIVITY alone — the increasing finite chain stabilizes within
`card L + 1` steps — so `hf` is not consumed here. It is retained because it is the
load-bearing hypothesis for the surrounding development.)
-/
theorem reach_closure_is_fixpoint
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (θ : ℝ) (seed : Finset L) :
    reachStep Psi0 f θ (reachClosure Psi0 f θ seed) = reachClosure Psi0 f θ seed := by
  convert exists_iterate_fixpoint ( reachStep Psi0 f θ ) ( reachStep_extensive Psi0 f θ ) seed using 1

/-
The reachable closure is monotone (non-decreasing) in the drive budget —
the "reachable set grows with budget" fact verified numerically in the run.
-/
theorem reach_closure_monotone_in_budget
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k)
    {θ θ' : ℝ} (hθ : θ ≤ θ') (seed : Finset L) :
    reachClosure Psi0 f θ seed ⊆ reachClosure Psi0 f θ' seed := by
  convert iterate_compare_gen ( reachStep Psi0 f θ ) ( reachStep Psi0 f θ' ) ( reachStep_monotone Psi0 f hf θ' ) ( fun S => reachStep_mono_in_budget Psi0 f hθ S ) seed ( Fintype.card L + 1 ) using 1

/-- The reachable closure is monotone (non-decreasing) in the established seed. -/
theorem reachClosure_mono_in_seed
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (θ : ℝ)
    {S S' : Finset L} (hSS : S ⊆ S') :
    reachClosure Psi0 f θ S ⊆ reachClosure Psi0 f θ S' :=
  (reachStep_monotone Psi0 f hf θ).iterate _ hSS

/-- The full target biosphere is *reachable* at budget `θ` from `seed` iff the
θ-reachable closure captures every layer. -/
def reachable (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L) (θ : ℝ) : Prop :=
  reachClosure Psi0 f θ seed = univ

/-
**R3 — reachability wall (threshold / up-set form).** The set of drive budgets
that make the whole biosphere reachable is an up-set: if a budget suffices, every
larger budget suffices. Hence a single critical budget separates the
thermodynamically forbidden regime from the reachable one.
-/
theorem reachability_wall_is_up_set
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (seed : Finset L)
    {θ θ' : ℝ} (hθ : θ ≤ θ') (h : reachable Psi0 f seed θ) :
    reachable Psi0 f seed θ' := by
  exact le_antisymm ( Finset.subset_univ _ ) ( h ▸ reach_closure_monotone_in_budget Psi0 f hf hθ seed )

/-- Bottleneck barrier accumulated along a build order (list), threading the growing
established set: the largest residual barrier crossed while laying the courses.
(See FORGE NOTE (A): the singleton `[k]` is its own base case to avoid folding in a
spurious `0`; `[] ↦ 0` is retained only for totality and is never used by a genuine
nonempty build order.) -/
def obAux (Psi0 : L → ℝ) (f : L → L → ℝ) : Finset L → List L → ℝ
  | _, [] => 0
  | S, [k] => residual Psi0 f k S
  | S, (k :: ks) => max (residual Psi0 f k S) (obAux Psi0 f (insert k S) ks)

/-- **Minimax bottleneck `B⋆`** — the least achievable makespan bottleneck over all
build orders (permutations of the not-yet-established layers). -/
noncomputable def Bstar (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L) : ℝ :=
  sInf { b : ℝ | ∃ l ∈ ((univ \ seed).toList).permutations, obAux Psi0 f seed l = b }

/-! ### Bridge lemmas between build orders and the reachable closure -/

/-
The head residual of a build order is bounded by its bottleneck.
-/
omit [Fintype L] in
theorem residual_head_le_obAux (Psi0 : L → ℝ) (f : L → L → ℝ)
    (S : Finset L) (k : L) (ks : List L) :
    residual Psi0 f k S ≤ obAux Psi0 f S (k :: ks) := by
  cases ks <;> simp [obAux]

/-
The tail bottleneck of a build order is bounded by the whole order's bottleneck.
-/
omit [Fintype L] in
theorem tail_obAux_le_obAux (Psi0 : L → ℝ) (f : L → L → ℝ)
    (S : Finset L) (k k2 : L) (ks : List L) :
    obAux Psi0 f (insert k S) (k2 :: ks) ≤ obAux Psi0 f S (k :: k2 :: ks) := by
  cases ks <;> simp [obAux]

/-
**Forward bridge.** Every layer appearing in a build order whose bottleneck is
`≤ θ` lands inside any θ-fixpoint `C` containing the starting set.
-/
theorem order_mem_fixpoint (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k)
    (θ : ℝ) (C : Finset L) (hC : reachStep Psi0 f θ C = C) :
    ∀ (l : List L) (S : Finset L), S ⊆ C → obAux Psi0 f S l ≤ θ → ∀ k ∈ l, k ∈ C := by
  intro l S hS h; induction' l with k l ih generalizing S <;> simp_all +decide [ reachStep ] ;
  rcases l with ( _ | ⟨ k', l' ⟩ ) <;> simp_all +decide [ obAux ];
  · exact hC ( by simpa using residual_antitone_in_established Psi0 f hf k hS |> le_trans <| h );
  · refine' ⟨ hC _, ih _ _ h.2 ⟩;
    · exact Finset.mem_filter.mpr ⟨ Finset.mem_univ _, le_trans ( residual_antitone_in_established Psi0 f hf k hS ) h.1 ⟩;
    · exact Finset.insert_subset_iff.mpr ⟨ hC ( Finset.mem_filter.mpr ⟨ Finset.mem_univ _, by linarith [ residual_antitone_in_established Psi0 f hf k hS ] ⟩ ), hS ⟩

/-
If the closure from `S` fills the biosphere but `S ≠ univ`, some not-yet-built
layer is already ignitable at budget `θ`.
-/
theorem exists_ignitable (Psi0 : L → ℝ) (f : L → L → ℝ) (θ : ℝ) {S : Finset L}
    (hSne : S ≠ univ) (hreach : reachClosure Psi0 f θ S = univ) :
    ∃ k ∈ univ \ S, residual Psi0 f k S ≤ θ := by
  by_contra h_contra;
  have h_reachStep_eq_S : reachStep Psi0 f θ S = S := by
    simp_all +decide [ Finset.ext_iff, reachStep ];
    exact fun x hx => Classical.not_not.1 fun hx' => not_le_of_gt ( h_contra x hx' ) hx;
  unfold reachClosure at hreach; simp_all +decide [ Function.iterate_fixed ] ;

omit [Fintype L] in
/-- Permutation bridge for `toList` of a set with a distinguished element removed. -/
theorem toList_perm_cons_erase {t : Finset L} {k : L} (hk : k ∈ t) :
    List.Perm t.toList (k :: (t.erase k).toList) := by
  rw [← Multiset.coe_eq_coe, Finset.coe_toList, ← Multiset.cons_coe, Finset.coe_toList,
    Finset.erase_val, Multiset.cons_erase (by simpa using hk)]

/-
**Reverse bridge (construction).** If the closure from `S` fills the biosphere and
there is still a layer to build, there is a build order (a permutation of the
remaining layers) whose bottleneck is `≤ θ`. Proved by induction on the number of
remaining layers, peeling off an ignitable layer at each step.
-/
theorem build_order_exists (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (θ : ℝ) :
    ∀ (n : ℕ) (S : Finset L), (univ \ S).card = n + 1 →
      reachClosure Psi0 f θ S = univ →
      ∃ l ∈ ((univ \ S).toList).permutations, obAux Psi0 f S l ≤ θ := by
  intro n S hS hreach;
  induction' n with n ih generalizing S;
  · obtain ⟨ k, hk ⟩ := Finset.card_eq_one.mp hS;
    have := exists_ignitable Psi0 f θ (by
    aesop) hreach;
    use [k]; simp_all +decide [ obAux ] ;
  · obtain ⟨ k, hk ⟩ := exists_ignitable Psi0 f θ (by
    aesop) hreach;
    obtain ⟨l', hl'⟩ : ∃ l' ∈ ((univ \ (insert k S)).toList).permutations, obAux Psi0 f (insert k S) l' ≤ θ := by
      apply ih (insert k S);
      · grind +splitImp;
      · refine' le_antisymm _ _;
        · exact Finset.subset_univ _;
        · exact hreach ▸ reachClosure_mono_in_seed Psi0 f hf θ ( Finset.subset_insert _ _ );
    refine' ⟨ k :: l', _, _ ⟩ <;> simp_all +decide [ List.mem_permutations ];
    · refine' List.Perm.trans _ ( toList_perm_cons_erase _ ).symm;
      rotate_left;
      exact k;
      · grind;
      · simp_all +decide [ Finset.sdiff_insert ];
    · rcases l' with ( _ | ⟨ k', l'' ⟩ ) <;> simp_all +decide [ obAux ]

/-
The set of achievable build-order bottlenecks is finite.
-/
theorem bottleneck_finite (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L) :
    ({ b : ℝ | ∃ l ∈ ((univ \ seed).toList).permutations, obAux Psi0 f seed l = b }).Finite := by
  exact Set.Finite.subset ( Set.toFinite ( Finset.image ( fun l => obAux Psi0 f seed l ) ( List.toFinset ( List.permutations ( Finset.toList ( Finset.univ \ seed ) ) ) ) ) ) ( by aesop )

/-
The set of achievable build-order bottlenecks is nonempty.
-/
theorem bottleneck_nonempty (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L) :
    ({ b : ℝ | ∃ l ∈ ((univ \ seed).toList).permutations, obAux Psi0 f seed l = b }).Nonempty := by
  refine' ⟨ _, ⟨ ( univ \ seed ).toList, _, rfl ⟩ ⟩;
  simp +decide [ List.mem_permutations ]

/-
`Bstar` is attained by some build order.
-/
theorem Bstar_mem (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L) :
    ∃ l ∈ ((univ \ seed).toList).permutations, obAux Psi0 f seed l = Bstar Psi0 f seed := by
  convert Set.Nonempty.csInf_mem ( bottleneck_nonempty Psi0 f seed ) ( bottleneck_finite Psi0 f seed ) using 1

/-
`Bstar` is a lower bound for every build order's bottleneck.
-/
theorem Bstar_le_of_perm (Psi0 : L → ℝ) (f : L → L → ℝ) (seed : Finset L)
    {l : List L} (hl : l ∈ ((univ \ seed).toList).permutations) :
    Bstar Psi0 f seed ≤ obAux Psi0 f seed l := by
  refine' csInf_le _ _;
  · exact Set.Finite.bddBelow ( bottleneck_finite Psi0 f seed );
  · exact ⟨ l, hl, rfl ⟩

/-
**Sharp wall (packaged).** With at least one layer left to build, the biosphere
is reachable at budget `θ` iff `θ` clears the minimax bottleneck `B⋆`.
-/
theorem reachable_iff_Bstar (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k)
    (seed : Finset L) (hne : (univ \ seed).Nonempty) (θ : ℝ) :
    reachable Psi0 f seed θ ↔ Bstar Psi0 f seed ≤ θ := by
  constructor;
  · intro h;
    obtain ⟨l, hl⟩ := build_order_exists Psi0 f hf θ (Finset.card (univ \ seed) - 1) seed (by
    rw [ Nat.sub_add_cancel ( Finset.card_pos.mpr hne ) ]) h;
    exact le_trans ( Bstar_le_of_perm Psi0 f seed hl.1 ) hl.2;
  · intro h;
    obtain ⟨l, hl⟩ := Bstar_mem Psi0 f seed;
    have := order_mem_fixpoint Psi0 f hf θ ( reachClosure Psi0 f θ seed ) ( reach_closure_is_fixpoint Psi0 f hf θ seed ) l seed ( reachClosure_extensive Psi0 f θ seed ) ( by linarith );
    refine' le_antisymm ( Finset.subset_univ _ ) _;
    intro k hk; by_cases hk' : k ∈ seed <;> simp_all +decide ;
    · exact reachClosure_extensive Psi0 f θ seed hk';
    · exact this k ( hl.1.symm.subset ( by simp +decide [ hk' ] ) )

/-- **R2 ⊗ R3 — greedy/minimax build-order optimality = critical drive budget.**
Under monotone facilitation the minimax bottleneck `B⋆` (attained by the greedy
lowest-residual sweep) is exactly the LEAST drive budget that renders the full
biosphere reachable: `B⋆` is reachable, and no smaller budget is. This is the
formal content of the boxed R2 identity `B⋆ = min_π max_k residual` fused with the
R3 identification `critical budget = B⋆`.
(See FORGE NOTE (B): the side condition `(univ \ seed).Nonempty` excludes the single
degenerate case `seed = univ`, where the reachable-budget set is all of `ℝ` and has
no least element.) -/
theorem reachability_critical_budget_eq_minimax_bottleneck
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (seed : Finset L)
    (hne : (univ \ seed).Nonempty) :
    IsLeast { θ : ℝ | reachable Psi0 f seed θ } (Bstar Psi0 f seed) := by
  constructor
  · exact (reachable_iff_Bstar Psi0 f hf seed hne (Bstar Psi0 f seed)).2 le_rfl
  · intro θ hθ
    exact (reachable_iff_Bstar Psi0 f hf seed hne θ).1 hθ

/-- **R3 (sharp) — the reachability wall.** The target biosphere is reachable at
drive budget `θ` iff the budget clears the minimax bottleneck: `reachable ⇔ θ ≥ B⋆`.
Below `B⋆` the target is thermodynamically forbidden regardless of elapsed time.
(See FORGE NOTE (B): the side condition `(univ \ seed).Nonempty` excludes the single
degenerate case `seed = univ`, which is reachable at every — including negative —
budget and therefore admits no finite critical `B⋆`.) -/
theorem reachability_iff_budget_geq_minimax_bottleneck
    (Psi0 : L → ℝ) (f : L → L → ℝ) (hf : ∀ j k, 0 ≤ f j k) (seed : Finset L)
    (hne : (univ \ seed).Nonempty) (θ : ℝ) :
    reachable Psi0 f seed θ ↔ Bstar Psi0 f seed ≤ θ :=
  reachable_iff_Bstar Psi0 f hf seed hne θ

/-
**Non-vacuity — the reachability wall strictly binds.** A one-layer instance
with bare barrier `1` and no facilitation: budget `1` reaches the whole biosphere,
budget `0` does not. So the wall is a real threshold, not a vacuous inequality.
-/
theorem esot_ordering_nonvacuous :
    ∃ (Psi0 : Fin 1 → ℝ) (f : Fin 1 → Fin 1 → ℝ),
      (∀ j k, 0 ≤ f j k) ∧
      reachable Psi0 f (∅ : Finset (Fin 1)) 1 ∧
      ¬ reachable Psi0 f (∅ : Finset (Fin 1)) 0 := by
  refine' ⟨ fun _ => 1, fun _ _ => 0, _, _, _ ⟩ <;> simp +decide [ reachable ];
  · unfold reachClosure; simp +decide [ reachStep ] ;
    unfold residual; norm_num;
  · unfold reachClosure;
    unfold reachStep; simp +decide [ Finset.ext_iff ] ;
    unfold residual; norm_num;

end Viridis.Ecoterraforming.EcopoieticOrdering