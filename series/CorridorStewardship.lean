/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Corridor Stewardship Theorem (CST) — Clean Cores
================================================

Nightly science-engine Run 074 (2026-06-19), [03] HDFM Corridors x Stewardship —
the "Weaver", 16th IB self-application; the edge-dual of the Monitoring
Water-Filling Theorem (MWT, Run 069). CONVERGENCE EVENT: it fuses the
corridor-design thread (Runs 022/036/055/058) with the broadcast-shadow-price
stewardship-allocation family (Runs 064/065/068/069) into a single variational
object, by recognizing that McRae's resistance distance (Circuitscape), Ghosh-
Boyd's convex edge-weight allocation, and the canon's broadcast shadow price
are the same optimization seen by three non-citing communities.

This file pins the CLEAN, WELL-POSED, NON-VACUOUS cores of CST as Lean 4
theorem statements for machine verification by Aristotle. The harder
matrix-calculus form of the global marginal-current law (dR_eff/dr_e = i_e^2
via the pseudoinverse Laplacian L^+ / Thomson's variational principle) and the
graph-connectivity items (two_edge_connected_iff_bridgeless,
kirchhoff_gradient_eq_current_flow_betweenness, efficiency_resilience_paradox)
are DEFERRED to a follow-up forge run pending an L^+/envelope-theorem
formalization; they are gate-checked out of this bundle to bound Aristotle
budget and keep every statement here crisply non-vacuous.

Toolchain leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff.
-/
import Mathlib

set_option autoImplicit false
set_option maxHeartbeats 1000000

namespace CorridorStewardship

open scoped RealInnerProductSpace BigOperators

/--
**Marginal-Current Law (L1/I1)** — exact on the simplest non-trivial
landscape resistor network: two parallel corridors of resistance `r1`, `r2`
under a unit s-t current injection. The effective resistance is
`R_eff(r1,r2) = r1*r2/(r1+r2)`, and the current carried by corridor 1 is
`i1 = r2/(r1+r2)`. The marginal value of restoring corridor 1 (lowering its
resistance) equals the **squared biotic current** it carries:
`dR_eff/dr1 = i1^2`. Centrality is not a heuristic proxy for restoration
priority — it *is* the gradient.
-/
theorem cst_marginal_current_law_parallel
    (r₂ : ℝ) (hr₂ : 0 < r₂) (r₁ : ℝ) (hr₁ : 0 < r₁) :
    deriv (fun r => r * r₂ / (r + r₂)) r₁ = (r₂ / (r₁ + r₂)) ^ 2 := by
  have h : r₁ + r₂ ≠ 0 := by positivity
  norm_num [h]
  rw [div_pow]
  ring

/--
**Corridor Water-Filling Optimum (I3/L2)** — uniqueness of the broadcast
connectivity shadow price. Given strictly positive current-flow betweenness
`κ`, unit cost `c`, decay rate `δ`, and shadow price `lam = λ_corr`, the
stationarity / equimarginal condition `κ /(c*δ*g^2) = lam` has a UNIQUE positive
solution `g`.
-/
theorem cst_corridor_waterfilling_optimum
    (κ c δ lam : ℝ) (hκ : 0 < κ) (hc : 0 < c) (hδ : 0 < δ) (hlam : 0 < lam) :
    ∃! g : ℝ, 0 < g ∧ κ / (c * δ * g ^ 2) = lam := by
  refine' ⟨ Real.sqrt ( κ / ( c * δ * lam ) ), _, _ ⟩ <;> norm_num;
  · exact ⟨ by positivity, by rw [ Real.sq_sqrt ( by positivity ), div_eq_iff ( by positivity ) ] ; nlinarith [ mul_div_cancel₀ κ ( by positivity : ( c * δ * lam ) ≠ 0 ) ] ⟩;
  · intro y hy h; rw [ ← h, eq_comm, Real.sqrt_eq_iff_mul_self_eq ] <;> try positivity;
    field_simp

/--
**Broadcast-price formula** — the unique positive solution of the corridor
water-filling stationarity condition is the closed-form optimum
`g_e* = sqrt( κ_e /(λ_corr * c_e * δ_e) )`.
-/
theorem cst_waterfilling_value
    (κ c δ lam : ℝ) (hκ : 0 < κ) (hc : 0 < c) (hδ : 0 < δ) (hlam : 0 < lam)
    (g : ℝ) (hg : 0 < g) (hopt : κ / (c * δ * g ^ 2) = lam) :
    g = Real.sqrt (κ / (lam * c * δ)) := by
  rw [ ← hopt ];
  field_simp;
  rw [ Real.sqrt_sq hg.le ]

/--
**Convexity (I2)**, per-corridor building block. The corridor resistance
`r_e = 1/g_e` is *strictly convex* in the conductance `g_e` on `(0,∞)`; hence
the series effective resistance `R_tot(g) = Σ_e 1/g_e` is strictly convex on the
positive orthant, so the budgeted stewardship optimum is **unique**. (Honest
diagonal/series instance of the general matrix-fractional convexity of
`R_tot = Δᵀ L^+ Δ`.)
-/
theorem cst_reff_strictConvexOn_inv :
    StrictConvexOn ℝ (Set.Ioi (0 : ℝ)) (fun g : ℝ => 1 / g) := by
  refine' strictConvexOn_of_deriv2_pos' ( convex_Ioi 0 ) _ _ <;> norm_num;
  · exact ContinuousOn.inv₀ continuousOn_id fun x hx => ne_of_gt hx;
  · exact fun x hx => pow_pos hx 3

/--
**Restoration Efficiency = cos²Θ (L6)** — the canon's universal cos²Θ
geometry (8th instance, CSUT-017). For nonzero steward spend `s` and nonzero
current-flow-betweenness `κ`, the realized connectivity gain as a fraction of
the theoretical maximum, `η = ⟪s,κ⟫² /(‖s‖²*‖κ‖²)`, lies in `[0,1]`, attaining
`η = 1` **iff** the spend is parallel to the betweenness. A deployable
misallocation meter.
-/
theorem cst_restoration_efficiency_cos2theta
    {n : ℕ} (s κ : EuclideanSpace ℝ (Fin n)) (hs : s ≠ 0) (hκ : κ ≠ 0) :
    0 ≤ (⟪s, κ⟫) ^ 2 / (‖s‖ ^ 2 * ‖κ‖ ^ 2)
      ∧ (⟪s, κ⟫) ^ 2 / (‖s‖ ^ 2 * ‖κ‖ ^ 2) ≤ 1
      ∧ ((⟪s, κ⟫) ^ 2 / (‖s‖ ^ 2 * ‖κ‖ ^ 2) = 1 ↔ ∃ c : ℝ, s = c • κ) := by
  refine' ⟨ div_nonneg ( sq_nonneg _ ) ( mul_nonneg ( sq_nonneg _ ) ( sq_nonneg _ ) ), _, _ ⟩;
  · exact div_le_one_of_le₀ ( by nlinarith [ abs_le.mp ( abs_real_inner_le_norm s κ ) ] ) ( by positivity );
  · constructor;
    · intro h
      have h_eq : ‖s - (⟪s, κ⟫ / ‖κ‖^2) • κ‖^2 = 0 := by
        rw [ @norm_sub_sq ℝ ] ; norm_num [ inner_smul_right, inner_smul_left ] ; ring_nf;
        simp_all +decide [ norm_smul, mul_pow ];
        grind;
      exact ⟨ _, sub_eq_zero.mp <| norm_eq_zero.mp <| sq_eq_zero_iff.mp h_eq ⟩;
    · rintro ⟨ c, rfl ⟩ ; simp +decide [ norm_smul, inner_smul_left, inner_self_eq_norm_sq_to_K ] ; ring_nf ; aesop;

/--
**Bridge Lemma (I4)** — a bridge carries the full throughput. Let `f e` be
the signed current carried by corridor `e` across an s-t cut, with total injected
throughput `T = ∑ e, f e` (flow conservation). If corridor `e₀` is a **bridge** —
the unique corridor crossing the cut (every other crossing current vanishes) —
then it carries the entire throughput: `f e₀ = T`. Under unit injection `T = 1`
the bridge carries the full unit current and its removal disconnects the
landscape.
-/
theorem cst_bridge_carries_full_unit_current
    {m : ℕ} (f : Fin m → ℝ) (T : ℝ) (hflow : ∑ e, f e = T)
    (e₀ : Fin m) (hbridge : ∀ e, e ≠ e₀ → f e = 0) :
    f e₀ = T := by
  rw [ ← hflow, Finset.sum_eq_single e₀ ] <;> aesop

end CorridorStewardship