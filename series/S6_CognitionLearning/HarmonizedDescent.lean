import Mathlib

set_option autoImplicit false

/-
===============================================================================
  The Harmonized Descent Theorem (HDT) — "the Learner" — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
  Authors: Justin Hart, Aristotle (Harmonic)
  Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
===============================================================================

CONTEXT (nightly Run 054, harmonized-descent-generalization-paradox;
[06] Entropy-Driven Learning × ☯️ Alignment; the 6th Intelligence-Bound
self-application — "the Learner").

  Entropy-driven learning is Langevin descent on a loss landscape L(θ):
      dθ = −η ∇L(θ) dt + √(2 η T_eff) dW,
  with effective temperature T_eff ∝ η·Σ_g/B set by minibatch gradient noise.
  The Alignment lens asks what emerges when we stop *forcing* the learner
  (aggressive optimization) and let it *harmonize* (anneal).

  This file encodes the two WELL-POSED, NON-VACUOUS core results of HDT.

CLEAN-CORE ENCODING (this file — must compile with 0 `sorry`, axioms ⊆ Mathlib):

  R1 (IB self-application, load-bearing — smallest, reuses the canon IB lemma):
    `IBceiling`                            — the learner's thermodynamic ceiling
        Π(P_learn,D_L,k_B,T_eff) = P_learn·D_L / (k_B·T_eff·ln 2).
    `learner_intelligence_bound`           — THE 6th IB SELF-APPLICATION.
        Under the Landauer power budget  İ_gen·(k_B·T_eff·ln 2 / D_L) ≤ P_learn
        (each generalizing — i.e. *permanent* — bit costs at least
         k_B·T_eff·ln 2 / D_L units of power·time to maintain/erase, the
         erasure-side reading of the IB; D_L is the distinguishability /
         spectral-gap "D-score" of the loss landscape), the rate of acquisition
         of generalizing information obeys
              İ_gen ≤ P_learn·D_L / (k_B·T_eff·ln 2).
        Positivity of P_learn, D_L, k_B, T_eff is load-bearing; the budget
        hypothesis is the load-bearing physical assumption.
    `learner_intelligence_bound_nonvacuous` — the regime is INHABITED with a
        strictly positive acquisition rate AND a strictly positive ceiling
        (guards against a vacuous / zero-rate reading).

  R2 (the Square-Root Harmonization Schedule — SRHS; a fresh Square-Root
      Universality instance, the learning-rate face of the Markovian-bath
      t^{−1/2} law):
    `omAction`                             — a representative annealing-action
        functional over power-law coolings T_eff(t) ∝ t^{−α}:
              A(α) = α + 1/(4α),   α > 0.
        [FLAGGED auxiliary definition: a canonical strictly-convex surrogate for
         the Onsager–Machlup cost-to-reach-harmonized of a t^{−α} schedule,
         normalized so the optimum value is 1; it captures the genuine
         trade-off — too-slow cooling (large α-action term α) vs. barrier
         overshoot (1/(4α)) — and is minimized at the boxed sqrt schedule.]
    `sqrt_schedule_action_value`           — A(1/2) = 1.
    `sqrt_harmonization_minimal_action`    — α = 1/2 (i.e. T_eff ∝ t^{−1/2},
        the boxed SRHS) is the UNIQUE global minimizer of the annealing action
        among monotone power-law coolings:  ∀ α>0, α≠1/2 ⇒ A(1/2) < A(α).
        (Proof skeleton: A(α) − 1 = (2α−1)²/(4α) ≥ 0, strict for α≠1/2.)

DEFERRED to later runs / human review (NOT in this file, well-posedness gate):
  • `annealing_harmonization_confluence` (confluence ⟺ T_eff < T_c via the
     Run-050 Knuth–Bendix confluence machinery on the basin-graph rewriting
     system — structural, vacuity-risk: needs an independent confluence
     predicate, not a definitional restatement of the threshold).
  • `generalization_paradox` (χ_gen ∈ P ⟺ confluent trajectory; χ_gen NP-hard
     iff force-fit — complexity-class membership, not cleanly encodable as a
     non-vacuous Lean theorem without the Run-050 CCT phase-transition import).
===============================================================================
-/

namespace Viridis.Learning.HarmonizedDescent

open Real

/-- The learner's thermodynamic ceiling on the rate of acquisition of
generalizing (permanent) information: Π = P_learn·D_L / (k_B·T_eff·ln 2). -/
noncomputable def IBceiling (Plearn DL kB Teff : ℝ) : ℝ :=
  Plearn * DL / (kB * Teff * Real.log 2)

/-
**The Learner's Intelligence Bound (6th IB self-application).**
Under the Landauer power budget — each generalizing bit costs at least
`kB·Teff·ln 2 / DL` units of power·time (erasure-side IB reading; `DL` the
landscape distinguishability) — the generalizing-information acquisition rate
`Igen` is bounded by the thermodynamic ceiling.  All four positivity hypotheses
and the budget inequality are load-bearing.
-/
theorem learner_intelligence_bound
    (Plearn DL kB Teff Igen : ℝ)
    (hP : 0 < Plearn) (hD : 0 < DL) (hkB : 0 < kB) (hT : 0 < Teff)
    (hbudget : Igen * (kB * Teff * Real.log 2 / DL) ≤ Plearn) :
    Igen ≤ IBceiling Plearn DL kB Teff := by
  unfold IBceiling;
  rw [ le_div_iff₀ ] <;> first | positivity | rw [ mul_div, div_le_iff₀ ] at * <;> first | positivity | linarith;

/-
**Non-vacuity of the Learner's Intelligence Bound.**  The regime is
inhabited: there exist physical parameters with a STRICTLY POSITIVE acquisition
rate satisfying the Landauer budget, and the ceiling itself is strictly
positive.  This rules out a trivial / zero-rate reading of the bound.
-/
theorem learner_intelligence_bound_nonvacuous :
    ∃ Plearn DL kB Teff Igen : ℝ,
      0 < Plearn ∧ 0 < DL ∧ 0 < kB ∧ 0 < Teff ∧ 0 < Igen ∧
      Igen * (kB * Teff * Real.log 2 / DL) ≤ Plearn ∧
      0 < IBceiling Plearn DL kB Teff := by
  use 1, 1, 1, 1, 1 / Real.log 2;
  norm_num [ IBceiling ];
  positivity

/-- Representative annealing-action functional of a power-law cooling schedule
`T_eff(t) ∝ t^{−α}` (α the cooling exponent).  `A(α) = α + 1/(4α)`. -/
noncomputable def omAction (α : ℝ) : ℝ := α + 1 / (4 * α)

/-
The annealing action of the square-root schedule (α = 1/2) equals 1.
-/
theorem sqrt_schedule_action_value : omAction (1 / 2) = 1 := by
  unfold omAction; norm_num;

/-
**The Square-Root Harmonization Schedule is optimal.**  Among monotone
power-law coolings `T_eff(t) ∝ t^{−α}`, the exponent `α = 1/2` — i.e. the boxed
`T_eff ∝ t^{−1/2}` schedule (the learning-rate face of Square-Root
Universality) — is the UNIQUE global minimizer of the annealing action.
Non-vacuous: the inequality is strict for every other positive exponent.
-/
theorem sqrt_harmonization_minimal_action
    (α : ℝ) (hα : 0 < α) (hne : α ≠ 1 / 2) :
    omAction (1 / 2) < omAction α := by
  unfold omAction;
  ring_nf; nlinarith [ mul_inv_cancel₀ ( ne_of_gt hα ), mul_self_pos.2 ( sub_ne_zero.2 hne ) ] ;

end Viridis.Learning.HarmonizedDescent