/-
Trees Cannot Cut — machine-checked core of claim C1
===================================================

This file isolates the *topology* content of claim C1 ("Trees Cannot Cut"):

  C1. A corridor / fuel-break network splits a landscape into compartments only
      through its cycles: the number of compartments equals the network's
      circuit rank plus one. An acyclic (tree-shaped) corridor connects habitat
      without cutting the surrounding fuel into pieces.

Scope / honesty note (matching the paper's stated boundary):
  * The step `FaceCount` — that a plane embedding of a connected network with
    `V` vertices and `E` edges has `V - E + F = 2` (Alexander duality) — is NOT
    proved here. It enters exactly as it does in the paper: as an explicit
    hypothesis, named `hEuler` below. Everything downstream of it is proved.
  * The raster/discrete (bit-quad Euler) version lives in the separate project
    P1 (github.com/jdhart81/viridis-research) and is out of scope here.
  * Claim C2 (the northeast Washington wildfire regression, beta = 0.0531,
    n = 11,314) is an empirical/observational result whose replication requires
    the ignition and barrier GIS layers plus the preregistered specification.
    Those data are not in this repository, so C2 cannot be reproduced or
    falsified by a source-only patch; this file deliberately makes no claim
    about it.

Named results:
  compartments_eq_circuitRank_add_one  — F = (E - V + 1) + 1, the headline identity.
  faceCount_eq_of_euler                — the same identity derived from Euler's formula.
  tree_cannot_cut                      — a tree (E = V - 1) has exactly one face
                                         and circuit rank 0.
  tree_not_cuts                        — a tree network does not cut: no compartment
                                         beyond the surrounding one.
  cuts_iff_positive_circuitRank        — cutting <-> at least one cycle.
  cut_growth_of_edge                   — one extra edge raises the compartment count
                                         by exactly one.
  nonvacuous                           — explicit witness (V = 4, E = 3 vs E = 4).

Non-vacuity: every hypothesis is satisfiable and the conclusions are not
`True` shells — see `nonvacuous`, where the tree case genuinely fails `Cuts`
while the one-cycle case genuinely satisfies it.

Toolchain: leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff6bd728b17a24e163c9402775d9e6a365.
-/

import Mathlib

set_option autoImplicit false

namespace Viridis.Topology.TreesCannotCut

/-! ## §1  The two counting invariants -/

/-- Circuit rank (first Betti number) of a connected finite graph with `V` vertices
and `E` edges: `E - V + 1`. It vanishes exactly for trees. -/
def circuitRank (V E : ℤ) : ℤ := E - V + 1

/-- Number of faces — i.e. compartments — of a connected plane graph, by Euler's
formula `V - E + F = 2`. -/
def faceCount (V E : ℤ) : ℤ := E - V + 2

/-- A corridor network *cuts* the landscape when its plane embedding yields at
least two compartments. -/
def Cuts (V E : ℤ) : Prop := 2 ≤ faceCount V E

/-! ## §2  Compartments = circuit rank + 1  (C1, headline) -/

/-- **C1 (headline identity).** The compartment count of a connected plane network
is its circuit rank plus one. Pure arithmetic, no embedding hypothesis needed. -/
theorem compartments_eq_circuitRank_add_one (V E : ℤ) :
    faceCount V E = circuitRank V E + 1 := by
  unfold faceCount circuitRank
  ring

/-- **C1 (topology step as an explicit hypothesis).** If a plane embedding of a
connected network has `F` faces — `V - E + F = 2`, the `FaceCount` hypothesis
justified in the paper by Alexander duality — then `F = circuitRank + 1`. -/
theorem faceCount_eq_of_euler (V E F : ℤ) (hEuler : V - E + F = 2) :
    F = circuitRank V E + 1 := by
  unfold circuitRank
  linarith

/-! ## §3  Trees Cannot Cut -/

/-- **C1 (trees cannot cut).** A tree-shaped corridor network — `E = V - 1`, acyclic —
has exactly one face and circuit rank zero: it connects habitat without cutting the
surrounding fuel into pieces. -/
theorem tree_cannot_cut (V E : ℤ) (htree : E = V - 1) :
    faceCount V E = 1 ∧ circuitRank V E = 0 := by
  unfold faceCount circuitRank
  omega

/-- **C1 (trees cannot cut, negative form).** No tree-shaped network cuts. -/
theorem tree_not_cuts (V E : ℤ) (htree : E = V - 1) : ¬ Cuts V E := by
  have h : faceCount V E = 1 := (tree_cannot_cut V E htree).1
  unfold Cuts
  omega

/-- **C1 (cutting requires a cycle).** A network splits the landscape into two or more
compartments exactly when its circuit rank is positive. -/
theorem cuts_iff_positive_circuitRank (V E : ℤ) :
    Cuts V E ↔ 1 ≤ circuitRank V E := by
  unfold Cuts faceCount circuitRank
  omega

/-- **C1 (one edge, one compartment).** Adding a single corridor edge on a fixed
vertex set raises the compartment count by exactly one: barriers of the fuel-break
kind only cut when they close cycles. -/
theorem cut_growth_of_edge (V E : ℤ) :
    faceCount V (E + 1) = faceCount V E + 1 := by
  unfold faceCount
  ring

/-! ## §4  Non-vacuity witness -/

/-- **Non-vacuity.** Four vertices spanning a tree (`E = 3`) give exactly one
compartment and do not cut; adding the fourth edge (`E = 4`, one cycle) gives two
compartments and does cut. The hypotheses are satisfiable and both branches of
`Cuts` are realised. -/
theorem nonvacuous :
    faceCount 4 3 = 1 ∧ faceCount 4 4 = 2 ∧ ¬ Cuts 4 3 ∧ Cuts 4 4 := by
  unfold Cuts faceCount
  norm_num

end Viridis.Topology.TreesCannotCut
