/-
# Historical Stewardship Setpoint algebra, with claim corrections (2026-09-26)
Justin Hart / Viridis. Original proof provenance: Aristotle, Run 102.
Lean 4.28 / Mathlib 8f9d9cff. Historical deposits are unchanged.

This module proves algebra, positivity, derivative signs and a potential maximum.
It does NOT compare lifetime policy integrals or prove trajectory limits.
The general sustainable held rate is g(D*)/phi, feasible iff
Omega >= (rho+r)/(2*phi), for 0<r<rho. Omega*D* is an instantaneous
capacity ceiling. Legacy uStar assumes phi=1 and is retained for compatibility.
Omega is an operating coefficient; a Landauer identification needs independent
architecture and energy assumptions. D*/K is a stock ratio, not a sustainable
throughput ratio. No scientific-priority or universal alignment claim is made.
See stewardship/ERRATA.md and InformationWeightedStewardship for corrected work.
-/
import Mathlib

open Real

namespace Viridis.Stewardship.StewardshipSetpoint

/-- Logistic regeneration of the disequilibrium stock: `g(D) = ρ·D·(1 − D/K)`. -/
noncomputable def g (rho K D : ℝ) : ℝ := rho * D * (1 - D / K)

/-- Marginal regeneration `g'(D) = ρ·(1 − 2D/K)` (the derivative of `g` in `D`). -/
noncomputable def gPrime (rho K D : ℝ) : ℝ := rho * (1 - 2 * D / K)

/-- The Stewardship Setpoint (golden-rule steady capacity)
    `D⋆ = (K/2)·(1 − r/ρ)`. -/
noncomputable def Dstar (rho K r : ℝ) : ℝ := (K / 2) * (1 - r / rho)

/-- Legacy name: instantaneous capacity at the raw setpoint, not sustained output. -/
noncomputable def sustCeiling (Omega rho K r : ℝ) : ℝ := Omega * Dstar rho K r

/-- Discounted regeneration net of the opportunity cost of tied-up capacity:
    `Φ(D) = g(D) − r·D`. Its strict concavity and unique maximizer at `D⋆` are the
    model-free (O-R-A-R) stewardship content. -/
noncomputable def Phi (rho K r D : ℝ) : ℝ := g rho K D - r * D

/-- Legacy phi=1 duty formula only. General duty is (rho+r)/(2*phi*Omega). -/
noncomputable def uStar (Omega rho r : ℝ) : ℝ := (rho + r) / (2 * Omega)

/-! ### R1 — Endogenous-D bound: the instantaneous capacity is `Ω·D⋆ < Ω·K`. -/

/-- Instantaneous capacity at the raw setpoint is below capacity at K; no sustained-rate claim. -/
theorem capacity_at_raw_setpoint_lt_full_stock_capacity
    (Omega rho K r : ℝ) (hOmega : 0 < Omega) (hK : 0 < K)
    (hrho : 0 < rho) (hr0 : 0 ≤ r) (hr : r < rho) :
    sustCeiling Omega rho K r = Omega * Dstar rho K r ∧
      Omega * Dstar rho K r < Omega * K := by
  exact ⟨ rfl, mul_lt_mul_of_pos_left ( by unfold Dstar; nlinarith [ mul_div_cancel₀ r hrho.ne' ] ) hOmega ⟩

/-! ### R2 — Stewardship Setpoint (canon candidate). -/

/-- **R2 (canon candidate).** The modified golden rule: marginal regeneration at the
    setpoint equals the discount rate, `g'(D⋆) = r`. Stated as a genuine derivative:
    `g(rho,K,·)` has derivative `r` at `D⋆`. -/
theorem golden_rule_gprime_eq_r
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) :
    HasDerivAt (fun D => g rho K D) r (Dstar rho K r) := by
  convert HasDerivAt.mul ( HasDerivAt.mul ( hasDerivAt_const _ _ ) ( hasDerivAt_id ( K / 2 * ( 1 - r / rho ) ) ) ) ( HasDerivAt.sub ( hasDerivAt_const _ _ ) ( HasDerivAt.div_const ( hasDerivAt_id ( K / 2 * ( 1 - r / rho ) ) ) _ ) ) using 1 ; ring;
  norm_num [ hrho.ne', hK.ne' ] ; ring;
  -- Combine like terms and simplify the expression.
  field_simp
  ring

/-- **R2 (canon candidate).** Closed form of the setpoint: the interior root of the
    golden rule is `D⋆ = (K/2)(1 − r/ρ)`, and it is interior: `0 < D⋆ < K/2 < K`. -/
theorem Dstar_eq_half_K_one_minus_r_over_rho
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr0 : 0 ≤ r) (hr : r < rho) :
    Dstar rho K r = (K / 2) * (1 - r / rho) ∧ 0 < Dstar rho K r ∧
      Dstar rho K r ≤ K / 2 := by
  exact ⟨ rfl, by unfold Dstar; exact mul_pos ( by positivity ) ( sub_pos_of_lt ( by rw [ div_lt_iff₀ hrho ] ; linarith ) ), by unfold Dstar; exact mul_le_of_le_one_right ( by positivity ) ( sub_le_self _ ( by positivity ) ) ⟩

/-- **R2.** The setpoint capacity is strictly decreasing in the discount rate:
    a more impatient steward holds a smaller stock. -/
theorem Dstar_decreasing_in_discount
    (rho K r₁ r₂ : ℝ) (hK : 0 < K) (hrho : 0 < rho)
    (hr₁ : 0 ≤ r₁) (hr₂ : r₂ < rho) (hlt : r₁ < r₂) :
    Dstar rho K r₂ < Dstar rho K r₁ := by
  unfold Dstar; nlinarith [ mul_div_cancel₀ r₁ hrho.ne', mul_div_cancel₀ r₂ hrho.ne' ] ;

/-! ### R3 — Tragedy of the Bound (HEADLINE canon candidate). -/

/-- Negative instantaneous drift at positive stock; not a trajectory-limit theorem. -/
theorem forcing_drift_negative_when_phiOmega_gt_rho
    (rho K phi Omega D : ℝ) (hK : 0 < K) (hrho : 0 < rho)
    (hphi : 0 < phi) (hOmega : 0 < Omega) (hD : 0 < D)
    (hforce : rho < phi * Omega) :
    g rho K D - phi * Omega * D < 0 := by
  simp_all +decide [ g, mul_assoc ];
  nlinarith [ mul_pos hrho hD, mul_pos hrho hK, mul_pos hD hK, mul_div_cancel₀ D hK.ne' ]

/-- Positivity of g(Dstar)/r. This omits phi and is not a comparison of objectives. -/
theorem raw_setpoint_regeneration_discount_positive
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr : 0 < r) (hrlt : r < rho) :
    (0 : ℝ) < g rho K (Dstar rho K r) / r := by
  refine' div_pos _ hr;
  convert mul_pos ( mul_pos hrho ( show 0 < Dstar rho K r from ?_ ) ) ( show 0 < 1 - Dstar rho K r / K from ?_ ) using 1;
  · exact Dstar_eq_half_K_one_minus_r_over_rho rho K r hK hrho hr.le hrlt |>.2.1;
  · rw [ sub_pos, div_lt_iff₀ ] <;> nlinarith [ Dstar_eq_half_K_one_minus_r_over_rho rho K r hK hrho hr.le hrlt, mul_div_cancel₀ r hrho.ne' ]

/-! ### R4 — Clark collapse threshold. -/

/-- **R4.** The interior setpoint exists only for a patient-enough steward: the
    collapse threshold is `r ≥ g'(0) = ρ`. Equivalently, `g'(0) = ρ`, and once
    `ρ ≤ r` the golden-rule capacity is non-positive (no interior optimum). -/
theorem clark_collapse_threshold_r_ge_rho
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr0 : 0 ≤ r) :
    gPrime rho K 0 = rho ∧ (rho ≤ r → Dstar rho K r ≤ 0) := by
  unfold gPrime Dstar;
  exact ⟨ by ring, fun h => mul_nonpos_of_nonneg_of_nonpos ( by positivity ) ( sub_nonpos_of_le ( by rw [ le_div_iff₀ hrho ] ; linarith ) ) ⟩

/-! ### R5 — O-R-A-R model-free extremum seeking. -/

/-- **R5.** `Φ(D) = g(D) − rD` is strictly concave on `ℝ`. -/
theorem phi_concave_unique_max
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) :
    StrictConcaveOn ℝ Set.univ (fun D => Phi rho K r D) ∧
      ∀ D, D ≠ Dstar rho K r → Phi rho K r D < Phi rho K r (Dstar rho K r) := by
  refine' ⟨ ⟨ convex_univ, _ ⟩, _ ⟩;
  · unfold Phi g; intro x _ y _ hxy a b ha hb hab; simp_all +decide [ ← eq_sub_iff_add_eq' ] ; ring_nf;
    nlinarith [ mul_pos ha ( mul_pos hrho ( sq_pos_of_ne_zero ( sub_ne_zero.mpr hxy ) ) ), mul_pos ha ( mul_pos hrho ( inv_pos.mpr hK ) ), mul_pos ( sub_pos.mpr hb ) ( mul_pos hrho ( sq_pos_of_ne_zero ( sub_ne_zero.mpr hxy ) ) ), mul_pos ( sub_pos.mpr hb ) ( mul_pos hrho ( inv_pos.mpr hK ) ) ];
  · unfold Phi Dstar g;
    field_simp;
    intro D hD; rw [ Ne.eq_def, eq_div_iff ] at hD <;> nlinarith [ mul_self_pos.mpr ( sub_ne_zero.mpr hD ), mul_pos hrho hK ] ;

/-- The potential derivative has opposite signs on either side; no convergence result. -/
theorem potential_derivative_points_toward_Dstar
    (rho K r D : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr0 : 0 ≤ r) (hr : r < rho) :
    (D < Dstar rho K r → 0 < gPrime rho K D - r) ∧
      (Dstar rho K r < D → gPrime rho K D - r < 0) := by
  unfold Dstar gPrime at *;
  field_simp;
  grind

/-! ### R6 — the Steward (44th IB self-application). -/

/-- The raw setpoint stock fraction is at most one half; not a sustained-output ratio. -/
theorem raw_stock_ratio_le_one_half
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr0 : 0 ≤ r) (hr : r < rho) :
    Dstar rho K r / K ≤ 1 / 2 := by
  rw [ div_le_iff₀ ] <;> norm_num [ Dstar ] ; nlinarith [ mul_div_cancel₀ r hrho.ne' ] ;
  positivity

/-- **R6 (44th IB self-application, the Steward).** Exact form and the equality case:
    the stock ratio equals `½(1 − r/ρ)`, and it saturates the one-half ceiling
    exactly when the steward is perfectly patient (`r = 0`). -/
theorem steward_ib_self_application
    (rho K r : ℝ) (hK : 0 < K) (hrho : 0 < rho) (hr0 : 0 ≤ r) (hr : r < rho) :
    Dstar rho K r / K = (1 / 2) * (1 - r / rho) ∧
      (Dstar rho K r / K = 1 / 2 ↔ r = 0) := by
  unfold Dstar; ring_nf; norm_num [ hK.ne', hrho.ne' ] ;
  grind

/-! ### R7 — Max-power correspondence. -/

/-- **R7.** The phi=1 duty cycle is strictly interior and structurally capped:
    `0 < u⋆ < ρ/Ω < 1`, and it is non-decreasing in impatience (myopia pushes harder
    on a smaller stock). Requires the structural throughput cap `ρ < Ω`. -/
theorem duty_cycle_lt_one
    (Omega rho r : ℝ) (hOmega : 0 < Omega) (hrho : 0 < rho)
    (hr0 : 0 ≤ r) (hr : r < rho) (hcap : rho < Omega) :
    0 < uStar Omega rho r ∧ uStar Omega rho r < rho / Omega ∧ rho / Omega < 1 ∧
      ∀ r', r < r' → r' < rho → uStar Omega rho r < uStar Omega rho r' := by
  unfold uStar;
  exact ⟨ by positivity, by rw [ div_lt_div_iff₀ ] <;> nlinarith, by rw [ div_lt_iff₀ ] <;> linarith, fun r' hr₁ hr₂ => by gcongr ⟩

/-! ### Non-vacuity witness. -/

/-- **`sst_nonvacuous`.** All laws bind simultaneously on an explicit non-degenerate
    witness `ρ = 1, K = 4, Ω = 2, r = 1/2` (so `0 ≤ r < ρ < Ω`). Then the setpoint is
    interior `D⋆ = 1 = K/4`, the instantaneous capacity `Ω·D⋆ = 2 < Ω·K = 8`, the
    throughput ratio `D⋆/K = 1/4 < 1/2`, and the duty cycle `u⋆ = 3/8` lies strictly
    in `(0, ρ/Ω) = (0, 1/2)` — witnessing that none of the laws is vacuous. -/
theorem sst_nonvacuous :
    Dstar 1 4 (1/2) = 1 ∧
      sustCeiling 2 1 4 (1/2) < 2 * 4 ∧
      Dstar 1 4 (1/2) / 4 < 1 / 2 ∧
      0 < uStar 2 1 (1/2) ∧ uStar 2 1 (1/2) < (1 : ℝ) / 2 := by
  unfold Dstar; unfold sustCeiling; unfold uStar; norm_num;
  unfold Dstar; norm_num;

@[deprecated capacity_at_raw_setpoint_lt_full_stock_capacity (since := "2026-09-26")]
alias sustainable_ceiling_eq_omega_Dstar := capacity_at_raw_setpoint_lt_full_stock_capacity
@[deprecated forcing_drift_negative_when_phiOmega_gt_rho (since := "2026-09-26")]
alias forcing_collapses_capacity_when_phiOmega_gt_rho := forcing_drift_negative_when_phiOmega_gt_rho
@[deprecated raw_setpoint_regeneration_discount_positive (since := "2026-09-26")]
alias setpoint_J_beats_forcing_J := raw_setpoint_regeneration_discount_positive
@[deprecated potential_derivative_points_toward_Dstar (since := "2026-09-26")]
alias orar_extremum_seeking_converges_to_Dstar := potential_derivative_points_toward_Dstar
@[deprecated raw_stock_ratio_le_one_half (since := "2026-09-26")]
alias sustainable_ratio_le_one_half := raw_stock_ratio_le_one_half

end Viridis.Stewardship.StewardshipSetpoint