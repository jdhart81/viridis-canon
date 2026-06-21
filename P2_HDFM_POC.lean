import Mathlib

/-
Copyright (c) 2025 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Formalization of key graph-theoretic results from "Hierarchical Dendritic
Forest Management: Optimizing Forest Connectivity on Real Landscapes"
(Hart 2026).

Lean version: leanprover/lean4:v4.28.0
-/

/-!
# HDFM — Graph-Theoretic Foundations

This module formalizes the core graph-theoretic theorems underlying
Hierarchical Dendritic Forest Management (HDFM).

## Main results

* `dendritic_minimum_cost` — **Theorem 1**: MST minimizes total corridor cost
* `tree_edge_removal_partition` — **Theorem 2**: removing any edge of a tree
*   DISCONNECTS it (every edge is a bridge). NB the Lean conclusion is
*   `¬ Connected`, not the strictly stronger 'exactly two components'.
* `dendritic_max_info_efficiency` — **Theorem 3**: Dendritic networks maximize H_b / |E|

## Design decisions

* Uses Mathlib's `SimpleGraph` for graph structure
* Trees characterized via `IsTree` (connected + acyclic)
* MST optimality via weight minimality among spanning subgraphs
* Information efficiency as ratio of branching entropy to edge count
-/

set_option linter.mathlibStandardSet false

open scoped BigOperators Real Nat Classical Pointwise

set_option maxHeartbeats 400000
set_option maxRecDepth 4000
set_option synthInstance.maxHeartbeats 20000
set_option synthInstance.maxSize 128
set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

open Finset

/-! ## §1 Graph-Theoretic Definitions -/

/-- A weighted graph on a finite vertex type V with edge weights in ℝ≥0. -/
structure WeightedGraph (V : Type*) [Fintype V] [DecidableEq V] where
  graph : SimpleGraph V
  weight : graph.edgeSet → NNReal

/-- A spanning subgraph: same vertex set, subset of edges. -/
structure SpanningSubgraph {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) where
  subgraph : SimpleGraph V
  is_spanning : ∀ (v w : V), subgraph.Adj v w → G.Adj v w

/-- Total cost of a spanning subgraph under a weight function.
    Defined as the sum of weights of G-edges that appear in S. -/
def totalCost {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) [DecidableRel G.Adj]
    (w : G.edgeSet → NNReal) (S : SpanningSubgraph G) : NNReal :=
  ∑ e : G.edgeSet, if (e : Sym2 V) ∈ S.subgraph.edgeSet then w e else 0

/-- A spanning tree: a connected, acyclic spanning subgraph. -/
structure SpanningTree {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) extends SpanningSubgraph G where
  connected : subgraph.Connected
  acyclic : subgraph.IsAcyclic

/-! ## §2 Theorem 1: Minimum Total Resistance (MST Optimality) -/

/-
Helper: if S₁ ≤ S₂ as subgraphs, and both are spanning subgraphs of G,
    then totalCost S₁ ≤ totalCost S₂ (since all weights are non-negative).
-/
lemma totalCost_le_of_le {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) [DecidableRel G.Adj]
    (w : G.edgeSet → NNReal)
    (S₁ S₂ : SpanningSubgraph G)
    (h : S₁.subgraph ≤ S₂.subgraph) :
    totalCost G w S₁ ≤ totalCost G w S₂ := by
  refine' Finset.sum_le_sum fun e _ => _;
  by_cases h₁ : e.val ∈ S₁.subgraph.edgeSet <;> by_cases h₂ : e.val ∈ S₂.subgraph.edgeSet <;> simp_all +decide;
  contrapose! h₂;
  cases' e with e he;
  cases e ; aesop

/-
Helper: a connected graph on a finite type has a spanning tree
    (as a subgraph that is a tree).
-/
lemma connected_has_tree_subgraph {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) [DecidableRel G.Adj]
    (S : SpanningSubgraph G)
    (hS : S.subgraph.Connected) :
    ∃ T : SpanningTree G, T.subgraph ≤ S.subgraph := by
  have := hS.exists_isTree_le;
  obtain ⟨ T, hT₁, hT₂ ⟩ := this;
  constructor;
  swap;
  constructor;
  convert hT₂.1;
  rotate_left;
  rotate_left;
  exact ⟨ T, fun v w hvw => hT₁ hvw |> fun h => S.is_spanning v w h ⟩;
  exact hT₁;
  · rfl;
  · exact hT₂.2

/-
**Theorem 1** (Minimum Total Resistance):
    For a connected weighted graph G, the minimum spanning tree minimizes
    total edge weight among all connected spanning subgraphs.

    Ecological interpretation: Dendritic corridors minimize habitat
    conversion required for full landscape connectivity.
-/
theorem dendritic_minimum_cost
    {V : Type*} [Fintype V] [DecidableEq V]
    (G : SimpleGraph V) [DecidableRel G.Adj]
    (hG : G.Connected)
    (w : G.edgeSet → NNReal)
    (T_mst : SpanningTree G)
    (h_mst : ∀ T' : SpanningTree G, totalCost G w T_mst.toSpanningSubgraph ≤
      totalCost G w T'.toSpanningSubgraph) :
    ∀ S : SpanningSubgraph G, S.subgraph.Connected →
    totalCost G w T_mst.toSpanningSubgraph ≤ totalCost G w S := by
  intro S hS;
  -- By connected_has_tree_subgraph, there exists a spanning tree T' with T'.subgraph ≤ S.subgraph.
  obtain ⟨T', hT'⟩ : ∃ T' : SpanningTree G, T'.subgraph ≤ S.subgraph := by
    exact connected_has_tree_subgraph G S hS;
  exact le_trans ( h_mst T' ) ( totalCost_le_of_le G w _ _ hT' )

/-! ## §3 Theorem 2: Deterministic Vulnerability (Tree Partition) -/

/-
**Theorem 2** (Deterministic Vulnerability Quantification):
    For a tree T, removing any edge e disconnects it: the Lean conclusion is
    `¬ (T.deleteEdges {e}).Connected` (every edge is a bridge). The strictly
    stronger 'exactly two components' is TRUE for trees but is NOT what this
    theorem proves — see CLAIMS_MATRIX.md.

    This is a fundamental property of trees: every edge is a bridge.
    Ecological interpretation: enables precise quantification of edge
    criticality for protection prioritization.
-/
theorem tree_edge_removal_partition
    {V : Type*} [Fintype V] [DecidableEq V]
    (T : SimpleGraph V) [DecidableRel T.Adj]
    (hT_connected : T.Connected)
    (hT_acyclic : T.IsAcyclic)
    (v w : V) (h_adj : T.Adj v w) :
    ¬ ((T.deleteEdges {s(v, w)}).Connected) := by
  contrapose! hT_acyclic with hT_not_acyclic;
  rw [ SimpleGraph.isAcyclic_iff_forall_adj_isBridge ];
  simp_all +decide [ SimpleGraph.isBridge_iff ];
  exact ⟨ v, w, h_adj, hT_not_acyclic v w ⟩

/-
Every edge in a tree is a bridge (its removal disconnects the graph).
-/
theorem tree_every_edge_is_bridge
    {V : Type*} [Fintype V] [DecidableEq V]
    (T : SimpleGraph V) [DecidableRel T.Adj]
    (hT_connected : T.Connected)
    (hT_acyclic : T.IsAcyclic) :
    ∀ e ∈ T.edgeSet, T.IsBridge e := by
  intro e he;
  contrapose! hT_acyclic with hT_not_acyclic;
  simp_all +decide [ SimpleGraph.isAcyclic_iff_forall_adj_isBridge ];
  rcases e with ⟨ x, y ⟩ ; use x, y; aesop;

/-! ## §4 Tree Edge Count -/

/-
A tree on n vertices has exactly n - 1 edges.
-/
theorem tree_edge_count
    {V : Type*} [Fintype V] [DecidableEq V]
    (T : SimpleGraph V) [DecidableRel T.Adj]
    (hT_connected : T.Connected)
    (hT_acyclic : T.IsAcyclic) :
    T.edgeFinset.card = Fintype.card V - 1 := by
  -- Since T is a tree, it is connected and acyclic.
  have h_tree : T.IsTree := by
    constructor <;> assumption;
  have := h_tree.card_edgeFinset;
  exact eq_tsub_of_add_eq this

/-! ## §5 Theorem 3: Maximum Information Efficiency -/

/-- Information efficiency: branching entropy per edge.
    I_eff = H_b(T) / |E|
    For a tree: I_eff = H_b / (n-1)
    For a cyclic graph: I_eff = H_b / |E| where |E| > n-1
    Trees maximize this ratio. -/
def informationEfficiency (H_b : NNReal) (edge_count : ℕ) : NNReal :=
  if edge_count = 0 then 0 else H_b / edge_count

/-
**Theorem 3** (Maximum Information Efficiency):
    For networks with equal vertex count, dendritic (tree) networks
    maximize information efficiency H_b / |E|, because they achieve
    connectivity with the minimum number of edges (n-1).

    Key insight: any cyclic network has |E| > n-1, so for the same
    branching entropy H_b, the tree has higher I_eff.
-/
theorem dendritic_max_info_efficiency
    (H_b : NNReal) (n : ℕ) (hn : 1 < n)
    (edge_count_cyclic : ℕ) (h_cyclic : n ≤ edge_count_cyclic) :
    informationEfficiency H_b (n - 1) ≥ informationEfficiency H_b edge_count_cyclic := by
  rcases n with ( _ | _ | n ) <;> simp_all +decide [ informationEfficiency ];
  rw [ if_neg ( by linarith ) ] ; gcongr ; norm_cast;
  bv_omega

/-! ## §6 Strahler Order and Corridor Width -/

/-- Corridor width prescription: W(e) = W_min · α^(S(e) - 1)
    where S(e) is the Strahler order. Width grows geometrically with order. -/
def corridorWidth (W_min α : NNReal) (strahler_order : ℕ) : NNReal :=
  W_min * α ^ (strahler_order - 1)

/-
Higher Strahler order implies wider corridors.
-/
theorem strahler_monotone_width
    (W_min α : NNReal) (hα : 1 ≤ α) (hW : 0 < W_min) :
    ∀ s₁ s₂ : ℕ, s₁ ≤ s₂ →
    corridorWidth W_min α s₁ ≤ corridorWidth W_min α s₂ := by
  intro s₁ s₂ hs
  unfold corridorWidth
  gcongr
  exact hα

end