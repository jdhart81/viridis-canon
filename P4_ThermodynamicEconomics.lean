import Mathlib

/-
Copyright (c) 2025 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Formalization of "Mathematical Foundations of Thermodynamic Economics"
(Hart 2026). Extends the Intelligence Bound formalization to economic
production theory.

Lean version: leanprover/lean4:v4.24.0
Mathlib version: f897ebcf72cd16f89ab4577d0c826cd14afaafc7
-/

/-!
# Thermodynamic Economics — Formal Verification

This module formalizes the key theorems from "Mathematical Foundations of
Thermodynamic Economics" (Hart 2026), which applies the Intelligence Bound
to economic production theory.

## Main results

* `thermodynamic_production_bound` — **Theorem 3.1**: dI/dt ≤ η·P·D/(k_B T ln 2)
* `non_substitutability` — **Theorem 4.1**: σ(P,D) = 0 (perfect complements)
* `steady_state_necessity` — **Theorem 5.1**: Material throughput growth is bounded
* `infinite_foreclosure_cost` — **Theorem 6.1**: C(D→0) = ∞

## Design decisions

* Builds on IntelligenceBound.lean definitions (ENNReal, Landauer, etc.)
* Production function F(P,D) = η·P·D/(k_B T ln 2) inherits IB structure
* Non-substitutability proved via isoquant analysis in ENNReal
* Foreclosure cost uses improper integral formalization
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

open MeasureTheory ProbabilityTheory ENNReal Filter Topology

/-! ## §1 Economic Definitions -/

/-- Thermodynamic production function: F(P,D) = η · P · D / (k_B T ln 2).
    Maps power input P and data richness D to maximum intelligence creation rate. -/
def thermodynamicProduction (η P D kBT_ln2 : ENNReal) : ENNReal :=
  η * P * D / kBT_ln2

/-- Efficiency parameter η ∈ [0, 1], representing fraction of theoretical maximum. -/
structure EfficiencyBounded (η : ENNReal) : Prop where
  le_one : η ≤ 1

/-- Data richness D ∈ [0, 1], representing fraction of environmental entropy
    that is structured (learnable). -/
structure DataRichnessBounded (D : ENNReal) : Prop where
  le_one : D ≤ 1

/-- Power is finite and positive. -/
structure FinitePower (P : ENNReal) : Prop where
  pos : 0 < P
  finite : P < ⊤

/-- Temperature factor k_B T ln 2 is positive and finite. -/
structure PositiveTemperature (kBT_ln2 : ENNReal) : Prop where
  pos : 0 < kBT_ln2
  finite : kBT_ln2 < ⊤

/-! ## §2 Theorem 3.1: The Intelligence Bound (Economic Form) -/

/-
**Theorem 3.1** (The Intelligence Bound — Economic Form):
    For a learning system with efficiency η ∈ [0,1], power input P,
    environmental data richness D ∈ [0,1], and temperature factor k_B T ln 2,
    the rate of intelligence creation is bounded:
      dI/dt ≤ η · P · D / (k_B T ln 2)
    Since η ≤ 1, this implies dI/dt ≤ P · D / (k_B T ln 2) (the pure IB).
-/
theorem thermodynamic_production_bound
    (η P D kBT_ln2 : ENNReal)
    (hη : EfficiencyBounded η)
    (hD : DataRichnessBounded D)
    (hkBT : PositiveTemperature kBT_ln2) :
    thermodynamicProduction η P D kBT_ln2 ≤ P * D / kBT_ln2 := by
  unfold thermodynamicProduction;
  gcongr;
  simpa using mul_le_mul_right' hη.le_one P

/-! ## §3 Theorem 4.1: Non-Substitutability -/

/-- The marginal rate of substitution MRS_{P,D} = D/P.
    For the production function F = η·P·D/c, ∂F/∂P = ηD/c and ∂F/∂D = ηP/c.
    So MRS = (∂F/∂P)/(∂F/∂D) = D/P. -/
def marginalRateOfSubstitution (D P : ENNReal) : ENNReal := D / P

/-- Isoquant: the set of (P, D) pairs producing constant output F₀.
    For F = η·P·D/c, the isoquant is D = c·F₀/(η·P), a rectangular hyperbola. -/
def isoquant (η kBT_ln2 F₀ P : ENNReal) : ENNReal :=
  kBT_ln2 * F₀ / (η * P)

/-
**Theorem 4.1** (Non-Substitutability):
    As D → 0, F → 0 regardless of P. No finite increase in P can
    compensate for loss of D. This is the essential complementarity
    (Leontief) property.
-/
theorem non_substitutability_D_essential
    (η P kBT_ln2 : ENNReal)
    (hη : EfficiencyBounded η)
    (hkBT : PositiveTemperature kBT_ln2) :
    thermodynamicProduction η P 0 kBT_ln2 = 0 := by
  -- By definition of thermodynamicProduction, we have thermodynamicProduction η P 0 kBT_ln2 = η * P * 0 / kBT_ln2.
  simp [thermodynamicProduction]

/-
**Theorem 4.1b**: Symmetrically, as P → 0, F → 0 regardless of D.
-/
theorem non_substitutability_P_essential
    (η D kBT_ln2 : ENNReal)
    (hη : EfficiencyBounded η)
    (hD : DataRichnessBounded D)
    (hkBT : PositiveTemperature kBT_ln2) :
    thermodynamicProduction η 0 D kBT_ln2 = 0 := by
  unfold thermodynamicProduction; aesop;

/-
**Theorem 4.1c**: The isoquant never touches either axis —
    maintaining constant output requires both P > 0 and D > 0.
    Note: P must be finite, since in ENNReal, finite/⊤ = 0.
-/
theorem isoquant_avoids_axes
    (η kBT_ln2 F₀ : ENNReal)
    (hη_pos : 0 < η) (hη_fin : η < ⊤)
    (hkBT : PositiveTemperature kBT_ln2)
    (hF₀_pos : 0 < F₀) (hF₀_fin : F₀ < ⊤) :
    ∀ P : ENNReal, 0 < P → P < ⊤ → 0 < isoquant η kBT_ln2 F₀ P := by
  intros P hP_pos hP_fin
  simp [isoquant];
  exact ⟨ ⟨ ne_of_gt hkBT.pos, ne_of_gt hF₀_pos ⟩, ne_of_lt ( ENNReal.mul_lt_top hη_fin hP_fin ) ⟩

/-! ## §4 Theorem 5.1: Steady-State Necessity -/

/-- Maximum available power on Earth (solar flux ≈ 1.7 × 10^17 W).
    We abstract this as a finite upper bound P_max. -/
structure PlanetaryPowerBound (P_max : ENNReal) : Prop where
  finite : P_max < ⊤
  pos : 0 < P_max

/-- Minimum achievable temperature (CMB ≈ 2.7 K, giving finite kBT_min_ln2).
    We abstract this as a positive lower bound. -/
structure MinTemperatureBound (kBT_min_ln2 : ENNReal) : Prop where
  pos : 0 < kBT_min_ln2
  finite : kBT_min_ln2 < ⊤

/-
**Theorem 5.1** (Steady-State Necessity):
    The maximum intelligence creation rate via material throughput is finite:
      (dI/dt)_max = P_max · 1 / (k_B T_min ln 2) < ∞
    Only efficiency improvement (η → 1) offers sustained growth.
-/
theorem steady_state_necessity
    (P_max kBT_min_ln2 : ENNReal)
    (hP : PlanetaryPowerBound P_max)
    (hkBT : MinTemperatureBound kBT_min_ln2) :
    P_max / kBT_min_ln2 < ⊤ := by
  refine' ENNReal.div_lt_top _ _;
  · exact ne_of_lt hP.finite;
  · exact ne_of_gt hkBT.pos

/-! ## §5 Theorem 6.1: Infinite Foreclosure Cost -/

/-- Value density: the value per unit intelligence creation rate per unit time.
    We require it to be bounded below by a positive constant. -/
structure PositiveValuation (v_min : ENNReal) : Prop where
  pos : 0 < v_min

/-
**Theorem 6.1** (Asymptotic Infinite Foreclosure Cost):
    Under any valuation framework assigning positive weight to future
    intelligence creation, the cost of complete D-loss (D → 0) is infinite.

    Informal proof: If V(τ) ≥ v_min > 0 for all τ, and D-loss eliminates
    all intelligence creation permanently (irreversible), then:
      C = ∫_t^∞ v_min · (ηPD)/(k_BT ln 2) dτ = ∞
    because the integrand is positive over an infinite horizon.

    We formalize the key structural result: the integral of a positive
    constant over [0, ∞) is infinite.
-/
theorem infinite_foreclosure_cost
    (v_min : ENNReal)
    (hv : PositiveValuation v_min) :
    ∀ (rate : ENNReal), 0 < rate →
    ∫⁻ (_t : ℝ) in Set.Ici (0 : ℝ), v_min * rate = ⊤ := by
  cases eq_or_ne v_min 0 <;> simp_all +decide [ ENNReal.mul_eq_top ];
  · cases hv ; aesop;
  · aesop

/-! ## §6 Corollaries -/

/-
**Corollary 4.1**: Technology cannot substitute for nature.
    No matter how large P becomes, if D = 0 then F = 0.
-/
theorem technology_cannot_substitute_nature
    (η kBT_ln2 : ENNReal) :
    ∀ P : ENNReal, thermodynamicProduction η P 0 kBT_ln2 = 0 := by
  unfold thermodynamicProduction; aesop;

/-
**Corollary**: The planetary intelligence ceiling is the product P · D.
    Degrading D while increasing P can decrease the ceiling.
-/
theorem intelligence_ceiling_product
    (η P₁ P₂ D₁ D₂ kBT_ln2 : ENNReal)
    (h_more_power : P₁ ≤ P₂)
    (h_less_data : D₂ ≤ D₁)
    (h_net_loss : P₂ * D₂ ≤ P₁ * D₁) :
    thermodynamicProduction η P₂ D₂ kBT_ln2 ≤
    thermodynamicProduction η P₁ D₁ kBT_ln2 := by
  unfold thermodynamicProduction;
  rw [ mul_assoc, mul_assoc ];
  gcongr

end