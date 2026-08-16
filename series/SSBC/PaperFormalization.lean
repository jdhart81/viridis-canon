import PaperFormalization.Hall
import PaperFormalization.Certificate
import PaperFormalization.Witnesses

/-!
# Run-130 — "The Seed-Source Bottleneck Certificate": Lean formalization

This is the root module of the returned project.  It collects the formalization of the four
frozen formal targets of `STATEMENT_CONTRACT.md` (paper source: `SEALED_paper.tex`).

* `PaperFormalization/Hall.lean` — the network-flow ingredient (capacitated Hall / Gale
  supply–demand theorem), proved from scratch: Mathlib has no max-flow/min-cut theorem.
* `PaperFormalization/Certificate.lean` — the preregistered model, the cut certificate, and
  the four targets `C1`–`C4`.
* `PaperFormalization/Witnesses.lean` — explicit non-vacuity witnesses.

Toolchain actually used is recorded in `TOOLCHAIN.md`; the exact Lean statement contract,
including the assumptions carried by each target and the documented scope blockers, is in
`LEAN_STATEMENT_CONTRACT.md`.

No `sorry`, `admit`, new `axiom`, `implemented_by`, `native_decide`, `unsafe` or `extern`
occurs anywhere in this project.
-/

namespace Viridis.Run130.PaperFormalization

open Viridis.Run130

/-! ## The four frozen targets, restated for reference at the project root.

Each of the following is a direct alias of the corresponding theorem, so that the frozen
target names of `STATEMENT_CONTRACT.md` appear verbatim in a single place. -/

/-- **C1** — "The maximum common fulfillment fraction equals the minimum eligible-neighborhood
capacity-to-demand ratio, capped at one." (paper: *The cut certificate*). -/
theorem seed_routing_common_fraction_eq_min_cut_ratio
    {σ τ : Type*} [Fintype σ] [Fintype τ] [DecidableEq σ] [DecidableEq τ]
    {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ} (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction E d s lam}
      (certificate E d s) :=
  Viridis.Run130.seed_routing_common_fraction_eq_min_cut_ratio hd hs

/-- **C2** — "Full demand is feasible exactly when every site subset passes the capacitated
Hall condition." (paper: *Equation 4*). -/
theorem seed_routing_feasible_iff_cut_conditions
    {σ τ : Type*} [Fintype σ] [Fintype τ] [DecidableEq σ] [DecidableEq τ]
    {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ} (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsFeasibleFraction E d s 1 ↔
      ∀ U : Finset σ, U.Nonempty → demand d U ≤ supply s (nbhd E U) :=
  Viridis.Run130.seed_routing_feasible_iff_cut_conditions hd hs

/-- **C3** — "Capacity outside an active minimizing subset's neighborhood cannot improve the
certificate." (paper: *Bottleneck-targeted expansion*, Corollary 1). -/
theorem capacity_outside_active_bottleneck_irrelevant
    {σ τ : Type*} [Fintype σ] [Fintype τ]
    {E : τ → σ → Bool} {d : σ → ℝ} {s s' : τ → ℝ} {U : Finset σ} {j₀ : τ}
    (hU : U.Nonempty)
    (hactive : certificate E d s = supply s (nbhd E U) / demand d U)
    (hlt : certificate E d s < 1)
    (hj₀ : j₀ ∉ nbhd E U)
    (hoff : ∀ j, j ≠ j₀ → s' j = s j)
    (hincr : s j₀ ≤ s' j₀) :
    certificate E d s' ≤ certificate E d s :=
  Viridis.Run130.capacity_outside_active_bottleneck_irrelevant hU hactive hlt hj₀ hoff hincr

/-- **C4** — "The intersection-graph certificate cannot exceed any scenario-specific
certificate." (paper: *Scenario robustness*, equation 5). -/
theorem scenario_intersection_certificate_le_each_scenario
    {σ τ κ : Type*} [Fintype σ] [Fintype τ] [Fintype κ]
    {d : σ → ℝ} {s : τ → ℝ} (Es : κ → τ → σ → Bool)
    (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) (k : κ) :
    certificate (scenarioIntersection Es) d s ≤ certificate (Es k) d s :=
  Viridis.Run130.scenario_intersection_certificate_le_each_scenario Es hd hs k

end Viridis.Run130.PaperFormalization

/-! ## Axiom audit

Each frozen target depends only on Lean's three standard axioms
(`propext`, `Classical.choice`, `Quot.sound`). -/

#print axioms Viridis.Run130.PaperFormalization.seed_routing_common_fraction_eq_min_cut_ratio
#print axioms Viridis.Run130.PaperFormalization.seed_routing_feasible_iff_cut_conditions
#print axioms Viridis.Run130.PaperFormalization.capacity_outside_active_bottleneck_irrelevant
#print axioms Viridis.Run130.PaperFormalization.scenario_intersection_certificate_le_each_scenario
#print axioms Viridis.Run130.Witnesses.C1_witness
#print axioms Viridis.Run130.Witnesses.C2_witness_infeasible
#print axioms Viridis.Run130.Witnesses.C2_witness_feasible
#print axioms Viridis.Run130.Witnesses.C3_witness
#print axioms Viridis.Run130.Witnesses.C4_witness
#print axioms Viridis.Run130.Witnesses.negative_control_arbitrarily_severe
#print axioms Viridis.Run130.Hall.exists_routing_of_hall
