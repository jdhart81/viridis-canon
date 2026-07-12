import Mathlib

set_option autoImplicit false
set_option maxHeartbeats 1000000

/-!
# Kibble–Zurek Speed-Limit Theorem — R3 Integrity Re-Proof (the Quencher, Run-092)

This module corrects and machine-checks the boxed cost-ratio of Run-092 R3
("Symmetry-Breaking of the Paradox"). Generalising the Run-060 Tempo Theorem to
a critical (Kibble–Zurek) crossing with universality exponent
`α = α_KZ = D̄·ν / (1 + ν·z) ∈ (0,1)`, the finite-time crossing cost is
`C(τ) = A·τ^(−α) + B·τ`, minimised at `τ⋆ = (αA/B)^{1/(1+α)}`. Writing
`u = τ/τ⋆`, the **cost ratio** is

    ρ(u) = C(u·τ⋆)/C(τ⋆) = (u^(−α) + α·u) / (1 + α).     -- CORRECTED

The Run-092 manuscript printed the α-weight on the WRONG term,
`(α·u^(−α) + u)/(1+α)` (`rhoSwapped`). This file verifies the corrected object
and proves the two forms genuinely differ away from the optimum, so the
integrity correction is non-trivial.

All statements are intended to be TRUE and NON-VACUOUS (witness `α = 1/2`).
Sorries are placeholders for the Aristotle (Harmonic) prover; preserve every
theorem statement VERBATIM.
-/

open Real Set

namespace KZSLTReprove

/-- Corrected KZ cost ratio `ρ(u) = (u^(−α) + α·u)/(1+α)`. -/
noncomputable def rho (α u : ℝ) : ℝ := (u ^ (-α) + α * u) / (1 + α)

/-- The Run-092 manuscript's *swapped* (erroneous) ratio: α weights the power term. -/
noncomputable def rhoSwapped (α u : ℝ) : ℝ := (α * u ^ (-α) + u) / (1 + α)

/-- At the optimal tempo the cost ratio is exactly 1. -/
theorem rho_one {α : ℝ} (hα : 0 < α) : rho α 1 = 1 := by
  unfold rho; norm_num [ hα.ne' ];
  linarith

/-- The cost ratio is strictly positive for positive tempo. -/
theorem rho_pos {α u : ℝ} (hα : 0 < α) (hu : 0 < u) : 0 < rho α u := by
  exact div_pos ( add_pos ( Real.rpow_pos_of_pos hu _ ) ( mul_pos hα hu ) ) ( by positivity )

/-- Unique interior stationary point: `ρ'(u) = α(1 − u^(−α−1))/(1+α)` vanishes iff `u = 1`. -/
theorem critical_point_unique {α u : ℝ} (hα : 0 < α) (hu : 0 < u) :
    u ^ (-α - 1) = 1 ↔ u = 1 := by
  rw [ Real.rpow_def_of_pos hu ];
  norm_num [ Real.exp_ne_zero, sub_eq_zero ];
  exact ⟨ fun h => by rcases h with ( ( rfl | rfl | rfl ) | h ) <;> linarith, fun h => Or.inl <| Or.inr <| Or.inl h ⟩

/-
Helper: `u ↦ u^(-α)` is strictly convex on `(0,∞)` for `α > 0` (negative exponent).
-/
lemma rpow_neg_strictConvexOn {α : ℝ} (hα : 0 < α) :
    StrictConvexOn ℝ (Ioi (0 : ℝ)) (fun u : ℝ => u ^ (-α)) := by
  apply strictConvexOn_of_deriv2_pos' ( convex_Ioi 0 );
  · exact continuousOn_of_forall_continuousAt fun u hu => ContinuousAt.rpow continuousAt_id continuousAt_const <| Or.inl <| ne_of_gt hu;
  · -- Let's calculate the second derivative of $f(u) = u^{-\alpha}$.
    have h_second_deriv : ∀ u : ℝ, 0 < u → deriv^[2] (fun u : ℝ => u ^ (-α)) u = (-α) * (-α - 1) * u ^ (-α - 2) := by
      have h_second_deriv : ∀ u : ℝ, 0 < u → deriv^[2] (fun u : ℝ => u ^ (-α)) u = deriv (fun u : ℝ => -α * u ^ (-α - 1)) u := by
        exact fun u hu => Filter.EventuallyEq.deriv_eq ( by filter_upwards [ lt_mem_nhds hu ] with x hx using by simp +decide [ hx.ne' ] );
      intro u hu; rw [ h_second_deriv u hu ] ; norm_num [ hu.ne' ] ; ring_nf
    exact fun u hu => h_second_deriv u hu ▸ mul_pos ( by nlinarith ) ( Real.rpow_pos_of_pos hu _ )

/-
Helper: strict tangent-line bound at `u = 1`: `u^(-α) > 1 - α(u-1)` for `u>0, u≠1`.
-/
lemma rpow_neg_tangent_lt {α u : ℝ} (hα : 0 < α) (hu : 0 < u) (hne : u ≠ 1) :
    1 - α * (u - 1) < u ^ (-α) := by
  by_cases h : u > 1 <;> simp_all +decide [ Real.rpow_def_of_pos ];
  · nlinarith [ Real.add_one_lt_exp ( show - ( Real.log u * α ) ≠ 0 by nlinarith [ Real.log_pos h ] ), Real.log_pos h, Real.log_le_sub_one_of_pos hu ];
  · have := Real.add_one_lt_exp ( show - ( Real.log u * α ) ≠ 0 by exact neg_ne_zero.mpr ( mul_ne_zero ( ne_of_lt ( Real.log_neg hu ( lt_of_le_of_ne h hne ) ) ) hα.ne' ) );
    nlinarith [ Real.log_le_sub_one_of_pos hu ]

/-
`u = 1` is the strict global minimiser: `ρ(u) > ρ(1) = 1` for every `u ≠ 1`.
-/
theorem rho_strict_min_at_one {α u : ℝ}
    (hα : 0 < α) (hα1 : α < 1) (hu : 0 < u) (hne : u ≠ 1) :
    (1 : ℝ) < rho α u := by
  unfold rho;
  rw [ lt_div_iff₀ ] <;> linarith [ rpow_neg_tangent_lt hα hu hne ]

/-
The corrected ratio is strictly convex on the positive tempo axis.
-/
theorem rho_strictConvexOn {α : ℝ} (hα : 0 < α) :
    StrictConvexOn ℝ (Ioi (0 : ℝ)) (rho α) := by
  unfold rho;
  refine' ⟨ convex_Ioi 0, _ ⟩;
  intro x hx y hy hxy a b ha hb hab;
  -- Apply the strict convexity of $u^{-\alpha}$ and the linearity of $u$.
  have h_strict_convex : (a * x + b * y) ^ (-α) < a * x ^ (-α) + b * y ^ (-α) := by
    apply_rules [ rpow_neg_strictConvexOn hα |> fun h => h.2 hx hy hxy ha hb hab ];
    exact h.2 hx hy hxy ha hb hab;
  norm_num [ ← eq_sub_iff_add_eq' ] at *;
  rw [ div_lt_iff₀ ] <;> subst hab <;> nlinarith [ mul_div_cancel₀ ( x ^ ( -α ) + α * x ) ( by linarith : ( 1 + α ) ≠ 0 ), mul_div_cancel₀ ( y ^ ( -α ) + α * y ) ( by linarith : ( 1 + α ) ≠ 0 ) ]

/-- Integrity: corrected and swapped ratios disagree away from the optimum. -/
theorem corrected_ne_swapped {α u : ℝ}
    (hα : 0 < α) (hα1 : α < 1) (hu : 0 < u) (hne : u ≠ 1) :
    rho α u ≠ rhoSwapped α u := by
  by_contra h;
  have h_eq : u^(-α) + α * u = α * u^(-α) + u := by
    unfold rho rhoSwapped at h; rw [ div_eq_div_iff ] at h <;> nlinarith;
  cases lt_or_gt_of_ne hne;
  · nlinarith [ show u ^ ( -α ) > 1 by exact lt_of_le_of_lt ( by norm_num ) ( Real.rpow_lt_rpow_of_exponent_gt hu ‹_› ( show -α < 0 by linarith ) ) ];
  · nlinarith [ show u ^ ( -α ) < 1 by simpa using Real.rpow_lt_rpow_of_exponent_lt ‹_› ( neg_lt_zero.mpr hα ) ]

/-- Symmetry-breaking sign law (from `ρ − ρ_swap = (1−α)(u^(−α) − u)/(1+α)`):
    for `α < 1` the corrected ratio lies below the swapped one exactly for
    over-slow crossings `u > 1`, and above it for over-fast `u < 1`. -/
theorem corrected_vs_swapped_sign {α u : ℝ}
    (hα : 0 < α) (hα1 : α < 1) (hu : 0 < u) (hne : u ≠ 1) :
    rho α u < rhoSwapped α u ↔ 1 < u := by
  constructor <;> intro h <;> simp_all +decide [ rho, rhoSwapped ];
  · contrapose! h;
    rw [ div_le_div_iff_of_pos_right ] <;> try linarith;
    nlinarith [ show u ^ ( -α ) ≥ 1 by exact le_trans ( by norm_num ) ( Real.rpow_le_rpow_of_exponent_ge hu h ( show -α ≤ 0 by linarith ) ) ];
  · rw [ div_lt_div_iff_of_pos_right ( by positivity ) ];
    nlinarith [ show u ^ ( -α ) < 1 by simpa using Real.rpow_lt_rpow_of_exponent_lt h ( neg_lt_zero.mpr hα ) ]

/-
Non-vacuity: the hypothesis class is inhabited and `ρ(1) = 1` holds there.
-/
theorem rho_nonvacuous : ∃ α : ℝ, 0 < α ∧ α < 1 ∧ rho α 1 = 1 := by
  exact ⟨ 1 / 2, by norm_num, by norm_num, by unfold rho; norm_num ⟩

end KZSLTReprove