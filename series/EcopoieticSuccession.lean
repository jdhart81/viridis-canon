/-
The Ecopoietic Succession-Ordering Theorem (ESOT) — "the Mason"
==============================================================

Nightly science-engine Run 095 — [15] Ecoterraforming × Thermodynamic.
37th Intelligence-Bound self-application. Prices the ORDER in which biosphere
"courses" (functional layers) are laid: a target biosphere is a coupled cascade
of metastable->viable nucleation events, each barrier renormalized DOWN by the
layers already present. This module encodes the CLEAN ANALYTIC CORE of the run.

Model.
  Layers indexed by a finite type; layer k has a bare nucleation barrier DPsi0_k = Psi0 k.
  An established set S facilitates k, lowering its barrier by sum_{j in S} f j k, f ≥ 0:
        DPsi_k(S) = Psi0 k - sum_{j in S} f j k.                             (R1)
  Layer k is *ignitable* under drive budget B iff DPsi_k(S) ≤ B.
  EPR-generated facilitation: f j k = (g k) * (dsig j), dsig j ≥ 0. Then
        DPsi_k(S) = Psi0 k - (g k) * sigma(S),  sigma(S) = sum_{j in S} dsig j. (R4)

Clean-core theorems (this file):
  R1  facilitation_barrier_renormalization_monotone
  R4a residual_linear_in_accumulated_epr
  R4b layer_ignites_at_critical_epr_threshold
  R4c barrier_slope_linear_in_epr
  R4d epr_trajectory_monotone_along_build
  R3  critical_budget_equals_bottleneck
  R5a mason_ib_floors_ordering_learning_time
  R5b ordering_regret_nonneg
  R5c ordering_regret_decreasing_in_knowledge
  R6  drive_alignment_efficiency_eq_cos2_theta
  esot_nonvacuous

DEFERRED (dedicated combinatorial run, NOT in this file):
  R2 greedy-minimax build-order optimality vs all N! orders (widest-path),
  R3 full theta-reachable-closure fixpoint.

Every statement is intended NON-VACUOUSLY (see esot_nonvacuous). `sorry`
placeholders are for the Aristotle forge to discharge; preserve statements verbatim.
-/

import Mathlib

open Real Finset
open scoped BigOperators

namespace Viridis.Ecoterraforming.EcopoieticSuccession

/-- **R1 - Facilitation barrier renormalization is monotone.**
Adding facilitators (enlarging the established set `S ⊆ S'`) never raises the
residual barrier of a downstream layer `k`, when all facilitation couplings are
nonnegative. -/
theorem facilitation_barrier_renormalization_monotone
    {iota : Type*} [DecidableEq iota] (Psi0 : iota → Real) (f : iota → iota → Real)
    (hf : ∀ j k, 0 ≤ f j k) (k : iota) {S S' : Finset iota} (hSS : S ⊆ S') :
    Psi0 k - ∑ j ∈ S', f j k ≤ Psi0 k - ∑ j ∈ S, f j k := by
  have := Finset.sum_le_sum_of_subset_of_nonneg hSS (fun j _ _ => hf j k)
  linarith

/-- **R4a - Residual barrier is exactly linear in accumulated entropy production.** -/
theorem residual_linear_in_accumulated_epr
    {iota : Type*} (Psi0 g dsig : iota → Real) (k : iota) (S : Finset iota) :
    Psi0 k - ∑ j ∈ S, (g k * dsig j) = Psi0 k - g k * (∑ j ∈ S, dsig j) := by
  rw [Finset.mul_sum]

/-- **R4b - Each layer ignites at a critical EPR threshold `sigma*_k=(Psi0-B)/g`.** -/
theorem layer_ignites_at_critical_epr_threshold
    (Psi0k gk B sigma : Real) (hg : 0 < gk) :
    Psi0k - gk * sigma ≤ B ↔ (Psi0k - B) / gk ≤ sigma := by
  rw [div_le_iff₀ hg]; constructor <;> intro h <;> nlinarith

/-- **R4c - Barrier falls linearly in sigma with slope `-g_k`.** -/
theorem barrier_slope_linear_in_epr (Psi0k gk s1 s2 : Real) :
    (Psi0k - gk * s2) - (Psi0k - gk * s1) = - gk * (s2 - s1) := by
  ring

/-- **R4d - The EPR trajectory is monotone non-decreasing along any admissible build.** -/
theorem epr_trajectory_monotone_along_build
    {iota : Type*} [DecidableEq iota] (dsig : iota → Real) (hd : ∀ j, 0 ≤ dsig j)
    {S S' : Finset iota} (hSS : S ⊆ S') :
    ∑ j ∈ S, dsig j ≤ ∑ j ∈ S', dsig j :=
  Finset.sum_le_sum_of_subset_of_nonneg hSS (fun j _ _ => hd j)

/-- **R3 (clean scalar form) - the critical budget equals the bottleneck.**
Every course ignitable (`b k ≤ B` for all k) iff the worst residual (bottleneck
`sup_k b k`) is `≤ B`; hence the critical drive budget equals the bottleneck. -/
theorem critical_budget_equals_bottleneck
    {iota : Type*} [Fintype iota] [Nonempty iota] (b : iota → Real) (B : Real) :
    (∀ k, b k ≤ B) ↔ (Finset.univ.sup' Finset.univ_nonempty b) ≤ B := by
  rw [Finset.sup'_le_iff]
  constructor
  · intro h k _; exact h k
  · intro h k; exact h k (Finset.mem_univ k)

/-- **R5a - the Mason's Intelligence-Bound floor on ordering-discovery time.**
Under `dI/dt ≤ P*D/(kB*T*ln2)`, acquiring `Igraph` bits by time `t`
(`Igraph ≤ rate*t`) forces `t ≥ Igraph*kB*T*ln2/(P*D)`. -/
theorem mason_ib_floors_ordering_learning_time
    (Igraph kB T ln2 P D t : Real)
    (hkB : 0 < kB) (hT : 0 < T) (hln2 : 0 < ln2) (hP : 0 < P) (hD : 0 < D)
    (hrate : Igraph ≤ (P * D) / (kB * T * ln2) * t) :
    Igraph * (kB * T * ln2) / (P * D) ≤ t := by
  rw [div_le_iff₀ (by positivity)]
  have hPD : 0 < P * D := by positivity
  have hden : 0 < kB * T * ln2 := by positivity
  rw [div_mul_eq_mul_div, le_div_iff₀ hden] at hrate
  nlinarith

/-- **R5b - Ordering regret is nonnegative** (chosen order vs minimal-makespan optimum). -/
theorem ordering_regret_nonneg
    {iota : Type*} [Fintype iota] [Nonempty iota] (mk : iota → Real) (pihat : iota) :
    0 ≤ mk pihat - (Finset.univ.inf' Finset.univ_nonempty mk) := by
  have := Finset.inf'_le mk (Finset.mem_univ pihat)
  linarith

/-- **R5c - Ordering regret decreases in knowledge and vanishes at full knowledge.** -/
theorem ordering_regret_decreasing_in_knowledge
    (r : Real → Real) (hr : Antitone r) (hr1 : r 1 = 0)
    {ka1 ka2 : Real} (h12 : ka1 ≤ ka2) (h2 : ka2 ≤ 1) :
    r ka2 ≤ r ka1 ∧ 0 ≤ r ka2 := by
  refine ⟨hr h12, ?_⟩
  have := hr h2; rw [hr1] at this; exact this

/-- **R6 - Drive-alignment efficiency `eta = cos^2 Theta in [0,1]`, aligned (Theta=0) => eta=1.** -/
theorem drive_alignment_efficiency_eq_cos2_theta (Theta : Real) :
    0 ≤ Real.cos Theta ^ 2 ∧ Real.cos Theta ^ 2 ≤ 1 ∧ Real.cos 0 ^ 2 = 1 := by
  refine ⟨sq_nonneg _, ?_, ?_⟩
  · nlinarith [Real.neg_one_le_cos Theta, Real.cos_le_one Theta]
  · rw [Real.cos_zero]; norm_num

/-- **Non-vacuity witness** (`Psi0=2, g=1, B=1`, `sigma*=1`): forbidden at sigma=0,
ignites exactly at sigma*. -/
theorem esot_nonvacuous :
    ∃ (Psi0 gk B : Real), 0 < gk ∧
      (B < Psi0 - gk * 0) ∧ (Psi0 - gk * ((Psi0 - B) / gk) = B) := by
  refine ⟨2, 1, 1, by norm_num, by norm_num, by norm_num⟩

end Viridis.Ecoterraforming.EcopoieticSuccession
