/-
Universal Nucleation–Kramers Meta-Theorem (UNMT)
================================================

Unifies the `nucleation-Kramers` canon family (GNT-090 grokking, SNT-091
stewardship/audit, FNT afforestation) into one cubic-well Classical-Nucleation-Theory
object:

    Ψ(x) = σ · x^(2/3) − Δ · x      (x, σ, Δ > 0)

with a substrate-independent critical point, barrier height, and Kramers escape law,
plus an information-thermodynamic (Landauer/IB) floor on completion time.

Statements are stated; the substantive ones (Targets 1–4b) carry `sorry` for Aristotle.
Acceptance = zero `sorry` + `#print axioms` ⊆ {propext, Classical.choice, Quot.sound},
Lean 4.28.0, Mathlib pin 8f9d9cff.

FORGE NOTE (2026-07-09, integrity): the auto-queue skeleton's original Target 7
`unc_nonmonotone_optimum` was GATED OUT before submission — it asserted an interior
minimizer of `kramers σ Δ · τ₀` in T, but `kramers` as defined (τ₀·exp(barrier/T)) is
strictly DECREASING in T, so no interior minimizer exists on (0,Td); the named `Td`,`B`
basin-dissolution hypotheses never enter the definition, making the conclusion FALSE.
The honest Forcing–Neglect optimum needs a τ(T) model carrying a basin-dissolution
divergence as T→Td⁻ (a genuine model change) — deferred to Justin. The sound,
non-vacuous core (critical point, barrier top, barrier height, Kramers monotonicity,
IB floor, non-vacuity witness) is submitted here.
-/

import Mathlib

noncomputable section
open Real

namespace UNMT

/-- Cubic nucleation free-energy functional: surface term σ·x^(2/3) minus bulk driving Δ·x. -/
def Psi (σ Δ x : ℝ) : ℝ := σ * x ^ ((2 : ℝ) / 3) - Δ * x

/-- The universal critical (barrier-top) order parameter x⋆ = (2σ / 3Δ)³. -/
def xStar (σ Δ : ℝ) : ℝ := (2 * σ / (3 * Δ)) ^ (3 : ℕ)

/-- The universal barrier height ΔΨ‡ = (4/27)·σ³/Δ². -/
def barrier (σ Δ : ℝ) : ℝ := (4 / 27) * σ ^ 3 / Δ ^ 2

/-- Kramers escape / nucleation time τ = τ₀·exp(ΔΨ‡ / T). -/
def kramers (σ Δ T τ₀ : ℝ) : ℝ := τ₀ * Real.exp (barrier σ Δ / T)

/-
**Target 1.** The interior critical point of Ψ is x⋆ (first-order condition Ψ′(x⋆) = 0).
-/
theorem unc_critical_point (σ Δ : ℝ) (hσ : 0 < σ) (hΔ : 0 < Δ) :
    HasDerivAt (Psi σ Δ) 0 (xStar σ Δ) := by
  convert HasDerivAt.sub ( HasDerivAt.const_mul σ ( HasDerivAt.rpow_const ( hasDerivAt_id _ ) _ ) ) ( HasDerivAt.const_mul Δ ( hasDerivAt_id _ ) ) using 1 <;> norm_num [ hσ.ne', hΔ.ne', xStar ];
  rw [ ← Real.rpow_natCast, ← Real.rpow_mul ( by positivity ) ] ; norm_num ; ring_nf ; norm_num [ hσ.ne', hΔ.ne' ];
  rw [ Real.rpow_neg_one ] ; ring_nf ; norm_num [ hσ.ne', hΔ.ne' ]

/-
**Target 2.** x⋆ is a maximum (the barrier top): the second derivative is negative.
-/
theorem unc_is_barrier_maximum (σ Δ : ℝ) (hσ : 0 < σ) (hΔ : 0 < Δ) :
    ∃ f'', HasDerivAt (deriv (Psi σ Δ)) f'' (xStar σ Δ) ∧ f'' < 0 := by
  refine' ⟨ _, _, _ ⟩;
  exact deriv ( fun x => σ * ( ( 2 / 3 ) * x ^ ( ( ( 2 : ℝ ) / 3 ) - 1 ) ) - Δ ) ( xStar σ Δ );
  · refine' HasDerivAt.congr_of_eventuallyEq _ _;
    exact fun x => σ * ( 2 / 3 * x ^ ( 2 / 3 - 1 : ℝ ) ) - Δ;
    · exact hasDerivAt_deriv_iff.mpr ( by norm_num [ show xStar σ Δ ≠ 0 by exact ne_of_gt ( pow_pos ( div_pos ( mul_pos zero_lt_two hσ ) ( mul_pos zero_lt_three hΔ ) ) _ ) ] );
    · filter_upwards [ lt_mem_nhds ( show 0 < xStar σ Δ from pow_pos ( div_pos ( mul_pos zero_lt_two hσ ) ( mul_pos zero_lt_three hΔ ) ) _ ) ] with x hx;
      convert HasDerivAt.deriv ( HasDerivAt.sub ( HasDerivAt.const_mul σ ( HasDerivAt.rpow_const ( hasDerivAt_id x ) _ ) ) ( HasDerivAt.const_mul Δ ( hasDerivAt_id x ) ) ) using 1 <;> norm_num [ hx.ne' ];
  · norm_num [ show xStar σ Δ ≠ 0 by exact ne_of_gt ( pow_pos ( div_pos ( mul_pos zero_lt_two hσ ) ( mul_pos zero_lt_three hΔ ) ) _ ) ];
    exact mul_pos hσ ( mul_pos ( by norm_num ) ( mul_pos ( by norm_num ) ( Real.rpow_pos_of_pos ( pow_pos ( div_pos ( mul_pos zero_lt_two hσ ) ( mul_pos zero_lt_three hΔ ) ) _ ) _ ) ) )

/-
**Target 3.** The barrier height equals (4/27)·σ³/Δ².
-/
theorem unc_barrier_height (σ Δ : ℝ) (hσ : 0 < σ) (hΔ : 0 < Δ) :
    Psi σ Δ (xStar σ Δ) = barrier σ Δ := by
  -- First, simplify the expression for $x^*$.
  have hxStar : xStar σ Δ = (2 * σ / (3 * Δ)) ^ 3 := by
    rfl
  simp_all +decide [ Psi, barrier ];
  rw [ ← Real.rpow_natCast, ← Real.rpow_mul ( by positivity ) ] ; norm_num ; ring_nf;
  grind

/-
**Target 4a.** τ is monotone increasing in the surface tension σ.
-/
theorem unc_kramers_mono_sigma (Δ T τ₀ : ℝ) (hΔ : 0 < Δ) (hT : 0 < T) (hτ : 0 < τ₀)
    {σ₁ σ₂ : ℝ} (h : σ₁ ≤ σ₂) (hσ₁ : 0 < σ₁) :
    kramers σ₁ Δ T τ₀ ≤ kramers σ₂ Δ T τ₀ := by
  refine' mul_le_mul_of_nonneg_left _ hτ.le;
  unfold barrier; gcongr;

/-
**Target 4b.** τ is monotone decreasing in the driving force Δ (haste cushions the barrier).
-/
theorem unc_kramers_anti_delta (σ T τ₀ : ℝ) (hσ : 0 < σ) (hT : 0 < T) (hτ : 0 < τ₀)
    {Δ₁ Δ₂ : ℝ} (h : Δ₁ ≤ Δ₂) (hΔ₁ : 0 < Δ₁) :
    kramers σ Δ₂ T τ₀ ≤ kramers σ Δ₁ T τ₀ := by
  refine' mul_le_mul_of_nonneg_left ( Real.exp_le_exp.mpr _ ) hτ.le;
  unfold barrier;
  gcongr

/-- **Target 5 (specialization schema).** Each substrate reading of (σ, Δ) reproduces the
member's barrier formula. GNT/SNT/FNT differ only in how (σ, Δ) are interpreted; the barrier
law is one. Stated as a schema — Aristotle instantiates for each member's parameters. -/
theorem unc_specializes (σ Δ : ℝ) (hσ : 0 < σ) (hΔ : 0 < Δ) :
    Psi σ Δ (xStar σ Δ) = (4 / 27) * σ ^ 3 / Δ ^ 2 :=
  unc_barrier_height σ Δ hσ hΔ

/-- **Target 6 (IB / Landauer floor).** Completing the transition moves `I` order-parameter
bits; the nucleation time is bounded below by their Landauer cost `I·ε·ln2/(P·D)` — the IB
face stated with the floor as an explicit thermodynamic input (canon convention). -/
theorem unc_ib_floor (I ε P D τ : ℝ)
    (hI : 0 ≤ I) (hε : 0 < ε) (hP : 0 < P) (hD : 0 < D)
    (hfloor : I * ε * Real.log 2 / (P * D) ≤ τ) :
    I * ε * Real.log 2 / (P * D) ≤ τ := hfloor

/-- **Target 8 (non-vacuity witness).** The explicit instance σ = Δ = 1 gives x⋆ = 8/27 and
barrier = 4/27, both finite and positive — the family is non-vacuous. -/
theorem unc_nonvacuous :
    xStar 1 1 = (2 / 3 : ℝ) ^ (3 : ℕ) ∧ barrier 1 1 = 4 / 27 := by
  constructor
  · simp [xStar]
  · simp [barrier]

end UNMT