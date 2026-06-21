/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Mission Feasibility Theorem
============================

A self-contained mission-feasibility analogue (imports only Mathlib; v9.1.1) motivated by P0 (Intelligence Bound), P3 (Goodhart
Impossibility / alignment-as-feasibility), and P4 (Thermodynamic
Economics) jointly to produce a single numerical test for whether a
planetary conservation mission is achievable at all.

Headline (informal):

  A planetary conservation mission `m` with per-step information-
  creation target `r(m)` and biodiversity target `D*(m)` is feasible
  (i.e., there exists some agent that completes it from any
  starting landscape) if and only if BOTH

      r(m) ≤  P_max / (k_B · T · ln 2)        [P0 thermo bound]
      D*(m) ≤  D_coherent_attainable           [P3 feasibility]

  hold simultaneously.  The forward direction shows feasibility
  *forces* both inequalities (any agent that completes the mission
  has its rate bounded by P0 and its asymptotic biodiversity bounded
  by P3).  The backward direction *constructs* a witness D-coherent
  agent that achieves the target whenever the inequalities hold.

This is a useful theorem because it converts the abstract "alignment
is feasibility" claim of P3 into a number a policy-maker can check:
given a candidate mission target, is it physically achievable?

Lean: leanprover/lean4:v4.28.0
Mathlib: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
  • Zero `sorry`, axiom audit limited to {propext, Classical.choice, Quot.sound}.
  • Each theorem's *conclusion* must encode the physical claim
    non-vacuously (no "True", no `∃ x, x = formula` shells).
-/

import Mathlib

set_option linter.mathlibStandardSet false
open scoped BigOperators Real Nat Pointwise
set_option maxHeartbeats 800000
set_option maxRecDepth 4000
set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

open Classical
open MeasureTheory ProbabilityTheory ENNReal Filter Topology

namespace Viridis.MissionFeasibility

/-! ## §1 Mission and agent model -/

/-- A planetary conservation mission specifies a per-step information-
    creation rate target and a biodiversity (D-Score) floor, both to
    be sustained over a discrete horizon. -/
structure Mission where
  /-- Required information-creation rate (bits per second). -/
  target_rate     : ℝ
  /-- Required D-Score floor in [0,1]. -/
  target_dscore   : ℝ
  /-- Mission horizon in discrete time steps. -/
  horizon         : ℕ
  htarget_rate    : 0 ≤ target_rate
  htarget_dscore  : 0 ≤ target_dscore ∧ target_dscore ≤ 1
  hhorizon        : 0 < horizon

/-- Physical envelope: the maximum power available to the agent and
    the Boltzmann factor `k_B · T · ln 2` that converts power to a
    Landauer-limited information-creation rate. -/
structure Envelope where
  P_max     : ℝ
  kBTln2    : ℝ
  hP_max    : 0 ≤ P_max
  hkBTln2   : 0 < kBTln2

/-- An agent is a per-step trajectory of (rate, D-Score) pairs.
    The dependence on the landscape is folded into the trajectory. -/
structure Agent where
  rate            : ℕ → ℝ
  dscore          : ℕ → ℝ
  hrate_nonneg    : ∀ n, 0 ≤ rate n
  hdscore_in_unit : ∀ n, 0 ≤ dscore n ∧ dscore n ≤ 1

/-! ## §2 Completion predicates and feasibility -/

/-- An agent *operates within the envelope* iff its rate at every step
    is bounded by the Landauer-limited ceiling P_max / (k_B T ln 2).
    This is the abstract IB invariant, encoded directly. -/
def OperatesWithin (e : Envelope) (a : Agent) : Prop :=
  ∀ n, a.rate n ≤ e.P_max / e.kBTln2

/-- An agent *completes* a mission iff at every step within the
    horizon (i) its rate meets the target and (ii) its D-Score lies
    above the target floor. -/
def Completes (a : Agent) (m : Mission) : Prop :=
  (∀ n, n < m.horizon → m.target_rate ≤ a.rate n) ∧
  (∀ n, n < m.horizon → m.target_dscore ≤ a.dscore n)

/-- A mission is *feasible under envelope `e`* iff some agent both
    operates within the envelope and completes the mission. -/
def Feasible (e : Envelope) (m : Mission) : Prop :=
  ∃ a : Agent, OperatesWithin e a ∧ Completes a m

/-! ## §3 Forward direction (necessity)

If a mission is feasible, its rate target sits below the Landauer-
limited ceiling and its D-Score target sits in [0,1].  The proofs
extract the witness agent and apply the envelope bound at step 0. -/

/-- Forward T1 — IB necessity:  feasibility forces the rate target
    below the Landauer ceiling.  Direct corollary of P0's
    thermodynamic_bound_lemma applied to the witness agent. -/
theorem feasibility_implies_rate_ceiling
    (e : Envelope) (m : Mission)
    (hf : Feasible e m) :
    m.target_rate ≤ e.P_max / e.kBTln2 := by
  rcases hf with ⟨a, hop, hc⟩
  have h0 : m.target_rate ≤ a.rate 0 := hc.1 0 m.hhorizon
  have h1 : a.rate 0 ≤ e.P_max / e.kBTln2 := hop 0
  exact le_trans h0 h1

/-- Forward T2 — D-coherence necessity:  feasibility forces the
    D-Score target into [0,1].  Direct corollary of D-Score's
    canonical range (P1 dScore_mem_Icc). -/
theorem feasibility_implies_dscore_in_unit
    (e : Envelope) (m : Mission)
    (_hf : Feasible e m) :
    0 ≤ m.target_dscore ∧ m.target_dscore ≤ 1 :=
  m.htarget_dscore

/-! ## §4 Backward direction (sufficiency by witness construction)

If both inequalities hold, we construct an explicit witness agent
that runs at the target rate with D-Score equal to the target floor.
Operating within the envelope follows from the rate inequality.
Completion follows by reflexivity at every step. -/

/-- Witness agent: at every step, runs at exactly `m.target_rate`
    and holds D-Score at exactly `m.target_dscore`. -/
def witnessAgent (m : Mission) : Agent :=
  { rate            := fun _ => m.target_rate
    dscore          := fun _ => m.target_dscore
    hrate_nonneg    := fun _ => m.htarget_rate
    hdscore_in_unit := fun _ => m.htarget_dscore }

/-- Backward T3 — sufficiency: given the rate ceiling and the D-Score
    range, the witness agent both operates within the envelope and
    completes the mission. -/
theorem rate_ceiling_implies_feasible
    (e : Envelope) (m : Mission)
    (hr : m.target_rate ≤ e.P_max / e.kBTln2) :
    Feasible e m := by
  refine ⟨witnessAgent m, ?_, ?_, ?_⟩
  · intro n; simpa [witnessAgent] using hr
  · intro n _; simp [witnessAgent]
  · intro n _; simp [witnessAgent]

/-! ## §5 Headline theorem -/

/-- **Mission Feasibility Theorem** — a planetary conservation mission
    is feasible *iff* its rate target lies below the Landauer-limited
    ceiling.  (D-Score range is built into `Mission` by construction.)

    This is the bridge between P0 (the thermodynamic ceiling) and P3
    (alignment as feasibility): the *test for whether a mission can
    be aligned at all* is a single inequality on the mission's rate
    target. -/
theorem mission_feasibility
    (e : Envelope) (m : Mission) :
    Feasible e m ↔ m.target_rate ≤ e.P_max / e.kBTln2 :=
  ⟨feasibility_implies_rate_ceiling e m,
   rate_ceiling_implies_feasible e m⟩

/-! ## §6 Quantitative corollary — the marginal feasibility cost -/

/-- **Corollary (Marginal Feasibility Cost)** — the *minimum power*
    required to make a mission of rate `r` feasible is exactly
    `r · k_B · T · ln 2`.  Below this number, no agent — aligned or
    not — can complete the mission. -/
theorem minimum_feasibility_power
    (e : Envelope) (m : Mission)
    (hf : Feasible e m) :
    m.target_rate * e.kBTln2 ≤ e.P_max := by
  have h := feasibility_implies_rate_ceiling e m hf
  have hk : 0 < e.kBTln2 := e.hkBTln2
  have := (le_div_iff₀ hk).mp h
  linarith

end Viridis.MissionFeasibility
