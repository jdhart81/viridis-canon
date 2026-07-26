/-
  Symbiotic Speed Limit Theorem (SSLT) — clean analytic core
  ==========================================================
  Viridis Canon · Nightly Run-107 (2026-07-23) · [05] Thermodynamic Speed Limits × 🌿 Symbiosis
  "The Weaver" — ~49th IB self-application. First-ever [05]×🌿 pairing.

  CONTEXT.  The tempo/speed-limit family (TWT Run-060/079, DCT Run-106) treats a
  SINGLE adapting system, Σ(τ) = A/τ + Bτ, τ* = √(A/B).  SSLT opens the
  previously-untouched MUTUALISM axis: two systems A, B whose reduced
  displacements couple through a fidelity coefficient ρ ∈ (−1,1).  In reduced
  coordinates u_A = d_A/√θ_A, u_B = d_B/√θ_B the joint per-step co-adaptation
  cost is

        Σ_sym(ρ)·τ  =  (u_A² − 2ρ u_A u_B + u_B²) / (1 − ρ²).

  At ρ = 0 this recovers the independent portfolio Σ_indep·τ = u_A² + u_B².
  The coupling matrix M(ρ) = [[θ_A, ρ√(θ_Aθ_B)],[ρ√(θ_Aθ_B), θ_B]] is
  positive-definite iff |ρ| < 1 (det = θ_Aθ_B(1−ρ²)).  For cooperative motion
  (u_A u_B > 0) the optimal fidelity ρ* = min(u_A,u_B)/max(u_A,u_B) drives the
  joint cost DOWN to the LARGER partner's solo cost max(u_A²,u_B²): the smaller
  partner is carried for free.  The efficiency gain at ρ* is exactly 1 + ρ*²,
  bounded in [1,2] — the Factor-Two Symbiosis Bound.  Sustaining coupling ρ
  costs mutual information against the channel's mixing rate:
  ρ ≤ ρ_max(I) = 1 − e^{−I}.  The joint pair obeys the fidelity-weighted
  Intelligence Bound with D_mut(ρ) = D_A + D_B + ρ√(D_A D_B) — the Weaver.

  This file certifies the clean, well-posed, NON-VACUOUS analytic core of SSLT.
  Every theorem statement is to be preserved VERBATIM; every hypothesis is
  load-bearing (see per-theorem non-vacuity notes).  The keystone optimality
  theorem `sslt_optimal_is_min` reduces to the perfect square (u_A − ρ u_B)² ≥ 0.

  THEOREMS:
    T1  sslt_rho_zero_recovery        Σ_sym(0) = Σ_indep = u_A² + u_B²
    T2  sslt_coupling_det_factor      det M(ρ) = θ_Aθ_B(1 − ρ²)
    T3  sslt_posdef_iff               0 < det M(ρ)  ↔  ρ² < 1     (θ_Aθ_B > 0)
    T4  sslt_optimal_is_min           Σ_sym(ρ) ≥ max(u_A²,u_B²)   (KEYSTONE, perfect square)
    T5  sslt_optimal_cost             Σ_sym(ρ*) = u_B²             (R3 Optimal-Fidelity Law)
    T6  sslt_factor_two_bound         gain(ρ*) = 1+ρ*²  ∧  1 ≤ gain ≤ 2   (R4)
    T7  sslt_saved_dissipation        Σ_indep − Σ_sym(ρ*) = u_A² = min(u_A²,u_B²)  (R5)
    T8  sslt_landauer_ceiling         0 ≤ ρ_max(I) < 1  (I ≥ 0)   ∧ monotone   (R6)
    T9  sslt_weaver_Dmut              D_A+D_B ≤ D_mut(ρ);  D_mut(0) = D_A+D_B   (R7 the Weaver)
    T10 sslt_nonvacuous               explicit witness (u_A=1,u_B=2): Σ_sym*=4, gain=5/4, saved=1
-/

import Mathlib

open scoped BigOperators

namespace Viridis.SymbioticSpeedLimit

noncomputable section

/-- Joint symbiotic co-adaptation cost (×τ), in reduced coordinates. -/
def sigmaSymTau (uA uB rho : ℝ) : ℝ := (uA^2 - 2*rho*uA*uB + uB^2) / (1 - rho^2)

/-- Independent-portfolio cost (×τ): the ρ = 0 limit. -/
def sigmaIndepTau (uA uB : ℝ) : ℝ := uA^2 + uB^2

/-- Efficiency gain from coupling: Σ_indep / Σ_sym(ρ). -/
def gain (uA uB rho : ℝ) : ℝ := sigmaIndepTau uA uB / sigmaSymTau uA uB rho

/-- Determinant of the coupling matrix M(ρ) = [[θ_A, ρ√(θ_Aθ_B)],[ρ√(θ_Aθ_B), θ_B]]. -/
def couplingDet (thetaA thetaB rho : ℝ) : ℝ := thetaA*thetaB - (rho * Real.sqrt (thetaA*thetaB))^2

/-- Landauer coupling ceiling ρ_max(I) = 1 − e^{−I}. -/
def rhoMax (I : ℝ) : ℝ := 1 - Real.exp (-I)

/-- Fidelity-weighted joint dissipation capacity D_mut(ρ) = D_A + D_B + ρ√(D_A D_B). -/
def Dmut (DA DB rho : ℝ) : ℝ := DA + DB + rho * Real.sqrt (DA*DB)

/-- **T1 — ρ = 0 recovery (R1).** At zero coupling the joint cost is the
    independent-portfolio sum. Non-vacuous: LHS involves the full quotient. -/
theorem sslt_rho_zero_recovery (uA uB : ℝ) :
    sigmaSymTau uA uB 0 = sigmaIndepTau uA uB := by
  simp [sigmaSymTau, sigmaIndepTau]

/-- **T2 — coupling determinant factorisation (R1).** Requires θ_Aθ_B ≥ 0 so
    that (√(θ_Aθ_B))² = θ_Aθ_B; then det M(ρ) = θ_Aθ_B(1 − ρ²). -/
theorem sslt_coupling_det_factor (thetaA thetaB rho : ℝ)
    (hpos : 0 ≤ thetaA * thetaB) :
    couplingDet thetaA thetaB rho = thetaA * thetaB * (1 - rho^2) := by
  unfold couplingDet
  rw [mul_pow, Real.sq_sqrt hpos]
  ring

/-- **T3 — positive-definiteness boundary (R1).** For θ_Aθ_B > 0, M(ρ) is
    positive-definite (det > 0) exactly when |ρ| < 1. Non-vacuous: both
    directions bind (ρ² < 1 is neither always-true nor always-false). -/
theorem sslt_posdef_iff (thetaA thetaB rho : ℝ)
    (hpos : 0 < thetaA * thetaB) :
    0 < couplingDet thetaA thetaB rho ↔ rho^2 < 1 := by
  rw [sslt_coupling_det_factor thetaA thetaB rho hpos.le]
  rw [mul_pos_iff_of_pos_left hpos, sub_pos]

/-- **T4 — KEYSTONE optimality (R3 core).** For cooperative partners
    0 < u_A ≤ u_B and any feasible coupling ρ² < 1, the joint cost is bounded
    below by the larger partner's solo cost u_B² = max(u_A²,u_B²). The proof
    reduces to the perfect square (u_A − ρ u_B)² ≥ 0. Non-vacuous: equality is
    attained at ρ = u_A/u_B (see T5). -/
theorem sslt_optimal_is_min (uA uB rho : ℝ)
    (huA : 0 < uA) (hle : uA ≤ uB) (hrho : rho^2 < 1) :
    uB^2 ≤ sigmaSymTau uA uB rho := by
  have hden : 0 < 1 - rho^2 := by linarith
  rw [sigmaSymTau, le_div_iff₀ hden]
  nlinarith [sq_nonneg (uA - rho*uB), huA, hle]

/-- **T5 — Optimal-Fidelity Law (R3, HEADLINE).** For 0 < u_A < u_B, the
    optimal coupling ρ* = u_A/u_B collapses the joint cost to the larger
    partner's solo cost u_B²: the smaller partner is carried for free.
    Strict u_A < u_B keeps ρ* < 1 (feasible) and the quotient well-defined. -/
theorem sslt_optimal_cost (uA uB : ℝ)
    (huA : 0 < uA) (hlt : uA < uB) :
    sigmaSymTau uA uB (uA / uB) = uB^2 := by
  have hB : 0 < uB := lt_trans huA hlt
  have hBne : uB ≠ 0 := ne_of_gt hB
  have hdenom : 1 - (uA/uB)^2 ≠ 0 := by
    have : 1 - (uA/uB)^2 = (uB^2 - uA^2)/uB^2 := by field_simp
    rw [this]
    have hnum : (0:ℝ) < uB^2 - uA^2 := by nlinarith
    exact div_ne_zero (ne_of_gt hnum) (by positivity)
  rw [sigmaSymTau, div_eq_iff hdenom]
  field_simp
  ring

/-- **T6 — Factor-Two Symbiosis Bound (R4).** At ρ*, the efficiency gain is
    exactly 1 + ρ*² and lies in [1,2]. Non-vacuous: the upper bound 2 is the
    equal-partner limit, the lower bound 1 the maximally-unequal limit. -/
theorem sslt_factor_two_bound (uA uB : ℝ)
    (huA : 0 < uA) (hlt : uA < uB) :
    gain uA uB (uA / uB) = 1 + (uA / uB)^2 ∧
      1 ≤ gain uA uB (uA / uB) ∧ gain uA uB (uA / uB) ≤ 2 := by
  have hB : 0 < uB := lt_trans huA hlt
  have hBne : uB ≠ 0 := ne_of_gt hB
  have hcost : sigmaSymTau uA uB (uA / uB) = uB^2 := sslt_optimal_cost uA uB huA hlt
  have hg : gain uA uB (uA / uB) = 1 + (uA / uB)^2 := by
    rw [gain, hcost, sigmaIndepTau]
    field_simp
    ring
  refine ⟨hg, ?_, ?_⟩
  · rw [hg]; nlinarith [sq_nonneg (uA/uB)]
  · rw [hg]
    have hrho : (uA/uB)^2 ≤ 1 := by
      rw [div_pow, div_le_one (by positivity)]
      nlinarith
    linarith

/-- **T7 — Value of the mutual-information current (R5).** The dissipation saved
    by optimal coupling equals the carried (smaller) partner's entire solo cost
    u_A² = min(u_A²,u_B²). -/
theorem sslt_saved_dissipation (uA uB : ℝ)
    (huA : 0 < uA) (hlt : uA < uB) :
    sigmaIndepTau uA uB - sigmaSymTau uA uB (uA / uB) = uA^2 := by
  rw [sslt_optimal_cost uA uB huA hlt, sigmaIndepTau]
  ring

/-- **T8 — Landauer coupling ceiling (R6).** ρ_max(I) = 1 − e^{−I} is a valid
    fidelity (in [0,1)) for every nonnegative information budget I, and is
    monotone increasing in I. Non-vacuous: strict ρ_max < 1 forbids perfect
    coupling at finite information. -/
theorem sslt_landauer_ceiling (I₁ I₂ : ℝ) (hI₁ : 0 ≤ I₁) (hmono : I₁ ≤ I₂) :
    (0 ≤ rhoMax I₁ ∧ rhoMax I₁ < 1) ∧ rhoMax I₁ ≤ rhoMax I₂ := by
  refine ⟨⟨?_, ?_⟩, ?_⟩
  · rw [rhoMax, sub_nonneg]
    calc Real.exp (-I₁) ≤ Real.exp 0 := by
          apply Real.exp_le_exp.mpr; linarith
      _ = 1 := Real.exp_zero
  · rw [rhoMax, sub_lt_self_iff]
    exact Real.exp_pos _
  · rw [rhoMax, rhoMax, sub_le_sub_iff_left]
    apply Real.exp_le_exp.mpr; linarith

/-- **T9 — the Weaver: fidelity-weighted joint capacity (R7).** Cooperative
    coupling (ρ ≥ 0) can only raise the joint dissipation capacity that gates
    the pair's Intelligence Bound dI_joint/dt ≤ P·D_mut(ρ)/(k_BT ln2); at ρ = 0
    it degenerates to the additive uncoupled capacity. -/
theorem sslt_weaver_Dmut (DA DB rho : ℝ)
    (hDA : 0 ≤ DA) (hDB : 0 ≤ DB) (hrho : 0 ≤ rho) :
    DA + DB ≤ Dmut DA DB rho ∧ Dmut DA DB 0 = DA + DB := by
  constructor
  · rw [Dmut, le_add_iff_nonneg_right]
    exact mul_nonneg hrho (Real.sqrt_nonneg _)
  · rw [Dmut]; ring

/-- **T10 — explicit non-vacuity witness.** Unequal cooperative partners
    (u_A = 1, u_B = 2, ρ* = 1/2): the joint cost collapses to 4 = u_B², the
    independent cost is 5, the gain is 5/4 = 1 + ρ*², and the saved dissipation
    is exactly 1 = u_A². Certifies the whole cluster is instantiable with all
    hypotheses satisfied and every conclusion strictly non-trivial. -/
theorem sslt_nonvacuous :
    sigmaSymTau 1 2 (1/2) = 4 ∧
    sigmaIndepTau 1 2 = 5 ∧
    gain 1 2 (1/2) = 5/4 ∧
    sigmaIndepTau 1 2 - sigmaSymTau 1 2 (1/2) = 1 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;>
    simp only [sigmaSymTau, sigmaIndepTau, gain] <;> norm_num

end

end Viridis.SymbioticSpeedLimit
