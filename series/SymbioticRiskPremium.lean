/-
  Symbiotic Risk-Premium Theorem (SRPT) — clean analytic core
  ===========================================================
  Viridis Canon · Nightly Run-093 (2026-07-08) · [02] Thermodynamic Economics × 🌿 Symbiosis
  "The Mutualist" — 35th Intelligence-Bound self-application.
  Second-moment (variance / risk) sibling of the D-Capital valuation canon
  (SVT-067 value-coupling · SIB-072 rate-coupling · TDT-080 time-axis / discount rate).

  CONTEXT.  The valuation canon prices EXPECTED D-Capital flows (first moment) and their
  timing, importing the risk premium — the price of variance — as an exogenous constant, as
  CAPM does.  SRPT derives it from thermodynamics.  The Thermodynamic Uncertainty Relation
  (TUR) supplies the physics of variance (precision costs dissipation:
  Var(J)/⟨J⟩² ≥ 2 k_B/Σ), and the ecological portfolio effect supplies the statistics of
  aggregate stability (joint variance governed by covariance).  SRPT joins them: the risk
  premium is the price of dissipation-limited variance, and symbiotic coupling is
  thermodynamic diversification whose power is bounded by the same TUR that prices the risk.

  This file certifies the CLEAN ANALYTIC CORE of the boxed results.  All statements are
  encoded to be well-posed and NON-VACUOUS; proof bodies are `sorry` for the forge.

  Targets (named — PRESERVE VERBATIM):
    R1  risk_premium_tur_floor
          — π ≥ ρ k_B/Σ : no riskless D-Capital asset at finite dissipation.
    R2  mutualistic_iff_covariance_negative
          — joint variance sub-additive (diversifying) iff Cov < 0.
    R3  diversification_wall_residual_positive
          — TUR floors a strictly positive undiversifiable residual premium π_min = ρ k_B/Σ_tot.
        markowitz_zero_variance_requires_perfect_anticorrelation
          — classical (equal-variance) zero-variance hedge exists iff ρ_c = −1 (which physical
            coupling |ρ_c|<1 forbids).
    R5  contagion_mutualism_transition_at_zero_covariance
          — excess variance = 2 Cov ⇒ mutualistic/contagious phase transition exactly at Cov=0.
    R6  mutualist_ib_ceiling
          — hedging is Intelligence-Bound: ceiling P·D/(k_B T ln2) rises in P and D, falls in T.
        mutualist_ib_learnable_fraction_lt_one
          — regime shift faster than the ceiling ⇒ learnable covariance fraction < 1 (forced
            mis-hedging is a physical bound, not merely a behavioral bias).
    R7  hedging_efficiency_eq_cos2_theta
          — η = ⟪w,w*⟫²/(‖w‖²‖w*‖²) ∈ [0,1]  (Cauchy–Schwarz; CSUT-017 cos²Θ closer).
        srpt_nonvacuous — explicit positive-data witness (R1/R3/R6).

  DEFERRED (well-posedness / limit-divergence gate — see FORGE_STATE + note to Justin):
    R4 risk_premium_diverges_at_spectral_gap_closure  (π → ∞ as the spectral gap ε → 0⁺; a
        Tendsto/atTop limit statement — staged separately, not in this clean-core submission);
    the FULL-GENERALITY finiteness of Σ_tot for arbitrary physical coupling and the
    general-correlation (V_A ≠ V_B) Markowitz optimum — the finding itself flags these as
    verified on a concrete model rather than in full generality.
-/
import Mathlib

namespace Viridis.ThermoEconomics.SymbioticRiskPremium

open Real
open RealInnerProductSpace

/-! ## Definitions -/

/-- Relative risk premium of a return current in the mean-variance / small-risk (CRRA)
    expansion:  π = (ρ/2)·Var(R)/⟨R⟩². -/
noncomputable def riskPremium (rho varR meanSq : ℝ) : ℝ := rho / 2 * (varR / meanSq)

/-- Joint variance of two coupled D-Capital currents via their variances and covariance:
    Var(A+B) = V_A + V_B + 2·Cov. -/
def jointVariance (VA VB Cov : ℝ) : ℝ := VA + VB + 2 * Cov

/-- Excess (non-additive) part of the joint variance = 2·Cov.  Its sign is the
    mutualism (<0) vs. contagion (>0) order parameter. -/
def excessVariance (VA VB Cov : ℝ) : ℝ := jointVariance VA VB Cov - (VA + VB)

/-- Equal-variance two-asset minimum-variance portfolio variance as a function of the
    correlation ρ_c (equal weights are optimal when V_A = V_B):  (V/2)(1 + ρ_c). -/
noncomputable def eqMinVariance (V rhoc : ℝ) : ℝ := V / 2 * (1 + rhoc)

/-- Intelligence-Bound learning ceiling  dI/dt ≤ P·D /(k_B T ln 2). -/
noncomputable def ibCeiling (P D kB T : ℝ) : ℝ := P * D / (kB * T * Real.log 2)

/-! ### R1 — Thermodynamic Risk-Premium Floor -/

/-
**R1 (boxed).**  A mean-variance / CRRA valuer feeding the asset's own entropy production
    Σ through the TUR (Var/⟨R⟩² ≥ 2 k_B/Σ) prices a relative risk premium bounded below by
    ρ k_B/Σ.  There is **no riskless D-Capital asset at finite dissipation** — a zero-variance
    asset would need infinite Σ.  Non-vacuous: the floor is exactly attained at TUR saturation.
-/
theorem risk_premium_tur_floor
    (rho kB Sigma varR meanSq : ℝ)
    (hrho : 0 < rho) (hkB : 0 < kB) (hSig : 0 < Sigma) (hmeanSq : 0 < meanSq)
    (hTUR : 2 * kB / Sigma ≤ varR / meanSq) :
    rho * kB / Sigma ≤ riskPremium rho varR meanSq := by
  convert mul_le_mul_of_nonneg_left hTUR ( show 0 ≤ rho / 2 by positivity ) using 1 ; ring!

/-! ### R2 — Symbiotic Diversification = the Thermodynamic Portfolio Effect -/

/-
**R2 (boxed).**  For two coupled D-Capital currents the joint variance
    V_A + V_B + 2·Cov is strictly sub-additive — genuine diversification lowering the joint
    risk premium — **iff** the coupling covariance is negative (complementary niches / distinct
    fluctuation sources).  Ecological mutualism and Markowitz diversification are one law.
    Non-vacuous iff.
-/
theorem mutualistic_iff_covariance_negative (VA VB Cov : ℝ) :
    jointVariance VA VB Cov < VA + VB ↔ Cov < 0 := by
  unfold jointVariance; constructor <;> intro h <;> linarith;

/-! ### R3 — The Diversification Wall -/

/-
**R3 (boxed — the genuinely new result).**  Two *physically coupled* dissipative currents
    share a reservoir and hence share fluctuations; the TUR floors the optimally-hedged joint
    precision ratio at 2 k_B/Σ_tot.  Therefore a **strictly positive undiversifiable residual
    risk premium** π_min = ρ k_B/Σ_tot survives ANY hedge — the thermodynamic content of
    systematic risk, and a refutation of the classical riskless coupled hedge.  Non-vacuous:
    strictly positive at every finite Σ_tot and dominated by the achieved premium.
-/
theorem diversification_wall_residual_positive
    (rho kB Sigma_tot ratioStar : ℝ)
    (hrho : 0 < rho) (hkB : 0 < kB) (hSig : 0 < Sigma_tot)
    (hTUR : 2 * kB / Sigma_tot ≤ ratioStar) :
    0 < rho * kB / Sigma_tot ∧ rho * kB / Sigma_tot ≤ rho / 2 * ratioStar := by
  exact ⟨ by positivity, by ring_nf at *; nlinarith ⟩

/-
**R3 (classical contrast).**  In the equal-variance two-asset model the (equal-weight
    optimal) minimum-variance portfolio has variance (V/2)(1 + ρ_c); with V>0 it vanishes
    **iff** ρ_c = −1.  Classical Markowitz permits the riskless coupled hedge exactly at
    perfect anticorrelation — precisely the point physical coupling (|ρ_c|<1) forbids, whence
    the Wall.  Non-vacuous iff.
-/
theorem markowitz_zero_variance_requires_perfect_anticorrelation
    (V rhoc : ℝ) (hV : 0 < V) :
    eqMinVariance V rhoc = 0 ↔ rhoc = -1 := by
  unfold eqMinVariance; constructor <;> intro h <;> nlinarith;

/-! ### R5 — Contagion vs. Mutualism Phase Transition -/

/-
**R5 (boxed).**  The sign of the coupling covariance decides everything.  The excess
    (non-additive) variance equals 2·Cov, so the pair is **mutualistic** (excess<0, portfolio
    effect) iff Cov<0, **contagious** (excess>0, synchronized/systemic collapse) iff Cov>0,
    with the phase boundary exactly at Cov=0 — a second-moment degree of freedom orthogonal to
    the SVT-067 value transition.  Non-vacuous three-way sign dichotomy.
-/
theorem contagion_mutualism_transition_at_zero_covariance (VA VB Cov : ℝ) :
    (excessVariance VA VB Cov < 0 ↔ Cov < 0) ∧
    (excessVariance VA VB Cov > 0 ↔ Cov > 0) ∧
    (excessVariance VA VB Cov = 0 ↔ Cov = 0) := by
  unfold excessVariance;
  unfold jointVariance; ring_nf; norm_num;
  constructor <;> intro h <;> linarith

/-! ### R6 — The Mutualist (35th IB self-application) -/

/-
**R6 (boxed IB ceiling).**  To hedge, the valuer must *learn* the covariance structure;
    acquiring correlation bits is Intelligence-Bound: dI/dt ≤ ibCeiling = P·D/(k_B T ln2).  The
    ceiling **rises** in power P and dissipation-structure D and **falls** in temperature T
    (myopia under heat).  Non-vacuous strict monotonicities.
-/
theorem mutualist_ib_ceiling
    (P1 P2 D1 D2 T1 T2 kB : ℝ)
    (hkB : 0 < kB)
    (hP1 : 0 < P1) (hPlt : P1 < P2)
    (hD1 : 0 < D1) (hDlt : D1 < D2)
    (hT1 : 0 < T1) (hTlt : T1 < T2) :
    ibCeiling P1 D1 kB T1 < ibCeiling P2 D1 kB T1 ∧
    ibCeiling P1 D1 kB T1 < ibCeiling P1 D2 kB T1 ∧
    ibCeiling P1 D1 kB T2 < ibCeiling P1 D1 kB T1 := by
  refine' ⟨ _, _, _ ⟩;
  · exact div_lt_div_of_pos_right ( mul_lt_mul_of_pos_right hPlt hD1 ) ( by positivity );
  · unfold ibCeiling;
    gcongr;
  · exact div_lt_div_of_pos_left ( by positivity ) ( by positivity ) ( by nlinarith [ mul_lt_mul_of_pos_left hTlt hkB, mul_lt_mul_of_pos_left hTlt hP1, mul_lt_mul_of_pos_left hTlt hD1, Real.log_pos one_lt_two ] )

/-
**R6 (corollary — forced mis-hedging).**  When the covariance regime shifts faster than the
    Landauer-limited update rate (regime speed v exceeds the IB ceiling), the learnable fraction
    of the covariance structure, ceiling/v, is strictly < 1.  Under-diversification in crises is
    therefore a physical bound, not merely a behavioral bias — the normative content of
    "correlations go to one exactly when you need diversification".  Non-vacuous.
-/
theorem mutualist_ib_learnable_fraction_lt_one
    (ceiling v : ℝ) (hc : 0 < ceiling) (hv : ceiling < v) :
    ceiling / v < 1 := by
  rwa [ div_lt_one ( by linarith ) ]

/-! ### R7 — Hedging efficiency = cos²Θ (CSUT-017) -/

/-
**R7.**  With chosen portfolio weights `w` and minimum-variance weights `wstar`, the hedging
    efficiency η = ⟪w,w*⟫²/(‖w‖²‖w*‖²) lies in [0,1] by Cauchy–Schwarz; the complement
    sin²Θ = 1 − η is the forcing debt.  Non-vacuous [0,1] bound.
-/
theorem hedging_efficiency_eq_cos2_theta
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (w wstar : E) (hw : w ≠ 0) (hws : wstar ≠ 0) :
    0 ≤ (⟪w, wstar⟫) ^ 2 / (‖w‖ ^ 2 * ‖wstar‖ ^ 2) ∧
    (⟪w, wstar⟫) ^ 2 / (‖w‖ ^ 2 * ‖wstar‖ ^ 2) ≤ 1 := by
  refine' ⟨ div_nonneg ( sq_nonneg _ ) ( mul_nonneg ( sq_nonneg _ ) ( sq_nonneg _ ) ), div_le_one_of_le₀ _ ( mul_nonneg ( sq_nonneg _ ) ( sq_nonneg _ ) ) ⟩;
  nlinarith [ abs_le.mp ( abs_real_inner_le_norm w wstar ) ]

/-! ### Non-vacuity witness -/

/-
**Non-vacuity witness.**  Explicit positive data instantiating the core: ρ=2, Var=1,
    ⟨R⟩²=1 ⇒ risk premium 1; equal-variance V=2 at ρ_c=−1 ⇒ classical zero-variance hedge;
    P=2,D=3,k_B=1,T=1 ⇒ strictly positive IB ceiling 6/ln2.  Certifies the statements are not
    vacuously satisfiable.
-/
theorem srpt_nonvacuous :
    riskPremium 2 1 1 = 1 ∧ eqMinVariance 2 (-1) = 0 ∧ 0 < ibCeiling 2 3 1 1 := by
  unfold riskPremium eqMinVariance ibCeiling; norm_num;
  positivity

end Viridis.ThermoEconomics.SymbioticRiskPremium