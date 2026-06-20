/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Conservation Operator — Asymmetric-Reward Operator Architecture
================================================================

The architectural framework for asymmetric-reward systems: management
operators that produce strictly positive expected value on stochastic
input regardless of input quality, with yield concentrated in the upper
tail and with marginal returns to operator-efficiency dominating
marginal returns to input-power at sufficient scale.

Headline (informal):

  In a value-extracting system applied to a stochastic input process,
  the architecture of the management operator X determines a strictly
  larger fraction of long-run realized value than the architecture of
  the input-selection operator E, whenever (i) X bounds losses and has
  a dominant-mass win region (Theorem 1), (ii) the yield concentrates
  in the upper tail (Theorem 2), and (iii) at sufficient scale the
  marginal return-on-cost of operator efficiency D dominates that of
  input power P (Theorem 3).

Three core theorems, all derived against pinned Mathlib:

  positive_EV               — strictly positive expectation under
                              loss-bounded, win-dominated structure
  yield_concentration       — for non-negative integrable X, the upper
                              tail {X > T} captures at least E[X] - T
                              of the total integral mass
  architecture_dominance    — D-investment marginal return-on-cost
                              strictly exceeds P-investment marginal
                              return-on-cost when D·cost_D < P·cost_P

Connection to existing Canon (cited but not re-proved here):
  P0  IntelligenceBound.cap        — used implicitly: cap = P·D/C is
                                     the capability function whose
                                     partials drive Theorem 3
  P5  ShadowPrice / SLSPT-Tower    — quadratic-divergence is the
                                     mechanism that produces the
                                     heavy-tail premise of Theorem 2

Lean: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
  • Zero `sorry`, axiom audit limited to {propext, Classical.choice, Quot.sound}.
  • Each theorem's *conclusion* must encode the architectural claim
    non-vacuously (no `True`, no `∃ x, x = formula` shells).
  • Theorem 3 conclusion must be a strict inequality with a non-trivial
    hypothesis that can fail (e.g., when D·cost_D ≥ P·cost_P the
    conclusion is independent — verifying non-vacuity).
-/

import Mathlib

set_option linter.mathlibStandardSet false
open scoped BigOperators Real Nat
set_option maxHeartbeats 800000
set_option maxRecDepth 4000
set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

open Classical
open MeasureTheory Filter Topology

namespace Viridis.ConservationOperator

/-! ## §1 Capability function (carried over from IntelligenceBound)

The capability function `cap P D C = P · D / C` is the same function
used in the P0 Intelligence Bound module.  We restate it here for
self-containment.  In the live Canon library this would be imported. -/

/-- Capability function: P = power available, D = operator efficiency,
    C = thermodynamic / Landauer cost factor. -/
def cap (P D C : ℝ) : ℝ := P * D / C

/-- Capability is non-negative on the physical domain. -/
theorem cap_nonneg (P D C : ℝ) (hP : 0 ≤ P) (hD : 0 ≤ D) (hC : 0 < C) :
    0 ≤ cap P D C := by
  unfold cap
  exact div_nonneg (mul_nonneg hP hD) hC.le

/-- Capability is strictly monotone in D (operator efficiency). -/
theorem cap_strictMono_D (P D₁ D₂ C : ℝ) (hP : 0 < P) (hD : D₁ < D₂) (hC : 0 < C) :
    cap P D₁ C < cap P D₂ C := by
  unfold cap
  exact div_lt_div_of_pos_right (by nlinarith) hC

/-- Capability is strictly monotone in P (input power). -/
theorem cap_strictMono_P (P₁ P₂ D C : ℝ) (hP : P₁ < P₂) (hD : 0 < D) (hC : 0 < C) :
    cap P₁ D C < cap P₂ D C := by
  unfold cap
  exact div_lt_div_of_pos_right (by nlinarith) hC

/-! ## §2 Theorem 1 — positive expected value under asymmetric reward

The asymmetric-reward property has three components:
  (a) Loss boundedness:  ∃ L ≥ 0, ∀ ω, X(ω) ≥ -L
  (b) Win region:        ∃ V > 0, ∃ A measurable, μ(A) > 0, ∀ ω∈A, X(ω) ≥ V
  (c) Win dominance:     V · μ(A) > L · μ(Aᶜ)

Under (a)+(b)+(c), the expectation is strictly positive.  This is the
central architectural claim: a sufficiently asymmetric operator extracts
positive value even from random input.

The hypothesis (c) is non-trivial — it can fail (e.g., V tiny relative
to L, or A negligible).  When it holds, it makes the conclusion strict.
The proof splits the integral over A and Aᶜ, lower-bounds each piece,
and combines via `linarith`.
-/

variable {Ω : Type*} [MeasurableSpace Ω]

/-- **Theorem 1** (`positive_EV`).  An asymmetric-reward operator with
    bounded loss `L`, win region `A` of value `V`, and strict
    win-dominance `L · μ(Aᶜ) < V · μ(A)` produces strictly positive
    expected value under any probability measure. -/
theorem positive_EV
    (X : Ω → ℝ) (μ : Measure Ω) [IsProbabilityMeasure μ]
    (hX_int : Integrable X μ)
    (L : ℝ) (hL : 0 ≤ L) (h_loss : ∀ ω, -L ≤ X ω)
    (V : ℝ) (A : Set Ω) (hA : MeasurableSet A)
    (h_win : ∀ ω ∈ A, V ≤ X ω)
    (h_dom : L * (μ Aᶜ).toReal < V * (μ A).toReal) :
    0 < ∫ ω, X ω ∂μ := by
      have h_integral_split : ∫ ω, X ω ∂μ = (∫ ω in A, X ω ∂μ) + (∫ ω in Aᶜ, X ω ∂μ) := by
        exact (integral_add_compl hA hX_int).symm;
      -- By the properties of integrals, we can bound the integrals over $A$ and $A^c$.
      have h_integral_bound : (∫ ω in A, X ω ∂μ) ≥ V * (μ A).toReal ∧ (∫ ω in Aᶜ, X ω ∂μ) ≥ -L * (μ Aᶜ).toReal := by
        constructor;
        · refine' le_trans _ ( MeasureTheory.setIntegral_mono_on _ _ hA h_win );
          · simp +decide [ mul_comm ];
            rfl;
          · norm_num;
          · exact hX_int.integrableOn;
        · refine' le_trans _ ( MeasureTheory.setIntegral_mono_on _ _ _ fun ω hω => h_loss ω ) <;> norm_num [ mul_comm ];
          · rfl;
          · exact hX_int.integrableOn;
          · exact hA;
      linarith

/-! ## §3 Theorem 2 — yield concentration in the upper tail

For a non-negative integrable X on a probability space, for any
threshold T ≥ 0:

    ∫ X dμ - T  ≤  ∫_{X > T} X dμ.

Equivalently, the upper tail `{X > T}` carries at least `E[X] - T` of
the integral mass.  When T is small relative to E[X] this implies the
tail captures most of the mass.

This is the formal underpinning for "value concentrates in the upper
tail" — an architectural claim that, applied to operator design, means
that the design effort should focus on capturing tail wins rather than
suppressing modal-region noise.
-/

/-- **Theorem 2** (`yield_concentration`).  For non-negative
    integrable `X` on a probability space and any threshold `T ≥ 0`,
    the upper tail `{X > T}` captures at least `E[X] - T` of the
    integral mass. -/
theorem yield_concentration
    (X : Ω → ℝ) (μ : Measure Ω) [IsProbabilityMeasure μ]
    (hX_meas : Measurable X) (hX_int : Integrable X μ)
    (hX_nonneg : ∀ ω, 0 ≤ X ω)
    (T : ℝ) (hT : 0 ≤ T) :
    (∫ ω, X ω ∂μ) - T ≤ ∫ ω in {ω | T < X ω}, X ω ∂μ := by
      -- Let $A = \{ \omega \mid T < X(\omega) \}$. This is measurable since $X$ is measurable.
      set A : Set Ω := {ω | T < X ω} with hA_def;
      -- Split the integral into the part over $A$ and the part over $A^c$.
      have h_split : ∫ ω, X ω ∂μ = (∫ ω in A, X ω ∂μ) + (∫ ω in Aᶜ, X ω ∂μ) := by
        rw [ MeasureTheory.integral_add_compl ];
        · exact measurableSet_lt measurable_const hX_meas;
        · exact hX_int;
      -- On $A^c = \{X \leq T\}$, bound $\int_{A^c} X \leq T \cdot \mu(A^c)$.
      have h_bound : ∫ ω in Aᶜ, X ω ∂μ ≤ T * (μ Aᶜ).toReal := by
        have h_bound : ∫ ω in Aᶜ, X ω ∂μ ≤ ∫ ω in Aᶜ, T ∂μ := by
          refine' MeasureTheory.setIntegral_mono_on _ _ _ _ <;> norm_num;
          · exact hX_int.integrableOn;
          · exact measurableSet_lt measurable_const hX_meas;
          · exact fun ω hω => le_of_not_gt hω;
        simpa [ mul_comm ] using h_bound;
      nlinarith [ show ( μ Aᶜ ).toReal ≤ 1 by exact ENNReal.toReal_le_of_le_ofReal zero_le_one <| by exact le_trans ( MeasureTheory.measure_mono <| Set.subset_univ _ ) <| by simp +decide ]

/-! ## §4 Theorem 3 — architecture-D dominance over input-P

The capability function `cap P D C = P · D / C` has partial derivatives
∂cap/∂D = P/C and ∂cap/∂P = D/C.  The marginal return-on-cost for
investment in operator efficiency D is therefore P/(C · cost_D), and
the marginal return-on-cost for investment in input power P is
D/(C · cost_P).

D-investment dominates iff:
    P / (C · cost_D)  >  D / (C · cost_P)
which (since C > 0) is equivalent to:
    P · cost_P  >  D · cost_D.

This is the architectural-dominance threshold: at any operating point
where the cost-weighted input is below the cost-weighted operator,
investing in operator efficiency strictly outperforms investing in
input power.

CORRECTION FROM v0.0:  The v0.0 outline stated the threshold as
`P · cost_P > cost_D / D`, which is dimensionally inconsistent and
admits counter-examples.  The corrected threshold `D · cost_D <
P · cost_P` is the cost-weighted dominance condition derived directly
from the partials of `cap`.
-/

/-- **Theorem 3** (`architecture_dominance`).  When the cost-weighted
    operator-efficiency `D · cost_D` falls below the cost-weighted
    input-power `P · cost_P`, the marginal return-on-cost of investing
    in operator efficiency strictly exceeds the marginal
    return-on-cost of investing in input power. -/
theorem architecture_dominance
    (P D C cost_P cost_D : ℝ)
    (hP : 0 < P) (hD : 0 < D) (hC : 0 < C)
    (hcP : 0 < cost_P) (hcD : 0 < cost_D)
    (h_threshold : D * cost_D < P * cost_P) :
    D / (C * cost_P) < P / (C * cost_D) := by
      rw [ div_lt_div_iff₀ ] <;> nlinarith [ mul_pos hC hcP, mul_pos hC hcD ]

/-! ## §5 Architectural corollary — the unified dominance statement

Combining Theorems 1 and 3: at an operating point satisfying the
asymmetric-reward conditions of Theorem 1 AND the cost-weighted
dominance condition of Theorem 3, the marginal dollar of investment
flows to operator efficiency (D) rather than input power (P).
-/

/-- **Corollary** (`architecture_dominance_under_asymmetric_reward`).
    If the operator already produces positive expected value under
    asymmetric reward (Theorem 1 hypotheses) AND the cost-weighted
    dominance condition holds (Theorem 3 hypothesis), then both
    conclusions hold simultaneously: the system has positive EV AND
    marginal D-investment dominates marginal P-investment. -/
theorem architecture_dominance_under_asymmetric_reward
    (X : Ω → ℝ) (μ : Measure Ω) [IsProbabilityMeasure μ]
    (hX_int : Integrable X μ)
    (L : ℝ) (hL : 0 ≤ L) (h_loss : ∀ ω, -L ≤ X ω)
    (V : ℝ) (A : Set Ω) (hA : MeasurableSet A)
    (h_win : ∀ ω ∈ A, V ≤ X ω)
    (h_dom : L * (μ Aᶜ).toReal < V * (μ A).toReal)
    (P D C cost_P cost_D : ℝ)
    (hP : 0 < P) (hD : 0 < D) (hC : 0 < C)
    (hcP : 0 < cost_P) (hcD : 0 < cost_D)
    (h_threshold : D * cost_D < P * cost_P) :
    (0 < ∫ ω, X ω ∂μ) ∧ (D / (C * cost_P) < P / (C * cost_D)) := by
  refine ⟨?_, ?_⟩
  · exact positive_EV X μ hX_int L hL h_loss V A hA h_win h_dom
  · exact architecture_dominance P D C cost_P cost_D hP hD hC hcP hcD h_threshold

end Viridis.ConservationOperator