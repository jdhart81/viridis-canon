import Mathlib

/-!
# MIST — Measurement-Induced Symbiosis Theorem (Run 076, "the Witness")

18th IB self-application. Forge-encoded clean, well-posed, NON-VACUOUS core of Run 076 (MIST).
Source: science-engine/07_nightly_engine/.../Run-076_measurement-induced-symbiosis/finding.md.

## Modeling notes (forge-flagged assumptions; named CONCLUSIONS preserved from the finding)
* Legibility (saturating information gain):  `Leg γ p = p / (p + γ)`,  γ > 0.
  (The finding's honest course-corrected form Λ(p)=p/(p+γ).)
* Retained adaptive capacity (linear collapse to zero at criticality):
  `Cap pc p = pc - p` on `[0, pc]`,  pc > 0.  This explicit decreasing form is a forge
  modeling choice; the named conclusions (Σ unimodal; interior optimum p* ≤ p_c) are the
  finding's R2 claims and are preserved verbatim.
* Symbiotic surplus:  `Surplus γ pc p = Leg γ p * Cap pc p`  (finding R2, Σ = Λ·A).
* Cooperative back-action (finding R5, verbatim closed form):
  `Dtot γ L K = K·γ·((1-L)^(-1/K) - 1)`,  γ>0, L∈(0,1).
* Witness efficiency (finding R6, cos²Θ geometry):
  `η_W(Θ) = cos²Θ / (cos²Θ + sin²Θ) = cos²Θ`.

## Non-vacuity
`pStar γ pc = √(γ² + γ·pc) − γ` is the positive root of `p² + 2γp − γ·pc`; it lies strictly in
`(0, pc)` and is the STRICT global maximizer of `Surplus` on `[0, pc]` (so p* ≤ p_c is non-trivial,
strict, and interior — the edge-of-collapse). `Dtot` is STRICTLY decreasing in K with finite
positive asymptote `γ·log(1/(1-L))`. `η_W` is a genuine ratio identity with range `[0,1]`.
None collapses to a trivially-true statement.
-/

namespace MIST

open Real

/-- Legibility (saturating information gain), `γ > 0`. -/
noncomputable def Leg (γ p : ℝ) : ℝ := p / (p + γ)

/-- Retained adaptive capacity (linear collapse), critical monitoring rate `pc`. -/
noncomputable def Cap (pc p : ℝ) : ℝ := pc - p

/-- Symbiotic surplus `Σ(p) = Leg(p) · Cap(p)`. -/
noncomputable def Surplus (γ pc p : ℝ) : ℝ := Leg γ p * Cap pc p

/-- Edge-of-collapse optimum (closed form): positive root of `p² + 2γp − γ·pc`. -/
noncomputable def pStar (γ pc : ℝ) : ℝ := Real.sqrt (γ ^ 2 + γ * pc) - γ

/-- Cooperative total back-action of `K` shared-outcome witnesses (finding R5). -/
noncomputable def Dtot (γ L K : ℝ) : ℝ := K * γ * (Real.rpow (1 - L) (-(1 / K)) - 1)

/-
**R2 (boxed) — Edge-of-Collapse Optimum.** The symbiotic-surplus maximizer `pStar`
is strictly positive, strictly below the critical monitoring rate `pc`, and is the global
maximizer of `Surplus` on `[0, pc]`. Hence the mutualistic optimum sits *just below*
criticality: `p* ≤ p_c`.
-/
theorem edge_of_collapse_optimum_below_critical
    (γ pc : ℝ) (hγ : 0 < γ) (hpc : 0 < pc) :
    0 < pStar γ pc ∧ pStar γ pc < pc ∧
      ∀ p ∈ Set.Icc (0 : ℝ) pc, Surplus γ pc p ≤ Surplus γ pc (pStar γ pc) := by
  unfold pStar Surplus Leg Cap;
  norm_num +zetaDelta at *;
  refine' ⟨ Real.lt_sqrt_of_sq_lt ( by nlinarith ), _, _ ⟩;
  · rw [ sub_lt_iff_lt_add', Real.sqrt_lt' ] <;> nlinarith;
  · intro p hp₁ hp₂;
    field_simp;
    nlinarith [ sq_nonneg ( p - ( Real.sqrt ( γ * ( γ + pc ) ) - γ ) ), Real.sqrt_nonneg ( γ * ( γ + pc ) ), Real.mul_self_sqrt ( show 0 ≤ γ * ( γ + pc ) by positivity ) ]

/-
**R2 — Symbiotic Surplus is Unimodal.** `Surplus` is strictly increasing on `[0, pStar]`
and strictly decreasing on `[pStar, pc]`: over-monitoring is a phase, not a quantity.
-/
theorem symbiotic_surplus_unimodal
    (γ pc : ℝ) (hγ : 0 < γ) (hpc : 0 < pc) :
    StrictMonoOn (Surplus γ pc) (Set.Icc (0 : ℝ) (pStar γ pc)) ∧
      StrictAntiOn (Surplus γ pc) (Set.Icc (pStar γ pc) pc) := by
  constructor <;> intro x hx y hy hxy;
  · unfold Surplus Leg Cap pStar at *;
    simp +zetaDelta at *;
    rw [ div_mul_eq_mul_div, div_mul_eq_mul_div, div_lt_div_iff₀ ] <;> try nlinarith;
    nlinarith [ mul_pos hγ ( sub_pos.mpr hxy ), mul_le_mul_of_nonneg_left hx.2 hγ.le, mul_le_mul_of_nonneg_left hy.2 hγ.le, mul_le_mul_of_nonneg_left hx.2 ( sub_nonneg.mpr hxy.le ), mul_le_mul_of_nonneg_left hy.2 ( sub_nonneg.mpr hxy.le ), Real.mul_self_sqrt ( show 0 ≤ γ ^ 2 + γ * pc by positivity ) ];
  · -- By definition of $pStar$, we know that $x$ and $y$ are in the interval $[pStar, pc]$.
    have h_pos : 0 < x + γ ∧ 0 < y + γ := by
      constructor <;> nlinarith [ hx.1, hy.1, show 0 ≤ pStar γ pc from sub_nonneg_of_le <| Real.le_sqrt_of_sq_le <| by nlinarith ];
    -- By definition of $pStar$, we know that $x$ and $y$ are in the interval $[pStar, pc]$, so we can apply the properties of the surplus function.
    have h_surplus : (y * (pc - y)) / (y + γ) < (x * (pc - x)) / (x + γ) := by
      -- By definition of $pStar$, we know that $x$ and $y$ are in the interval $[pStar, pc]$, so we can apply the properties of the surplus function to get the inequality.
      have h_surplus : (y - x) * (y * x + γ * (x + y) - γ * pc) > 0 := by
        exact mul_pos ( sub_pos.mpr hxy ) ( by nlinarith [ hx.1, hy.1, show pStar γ pc = Real.sqrt ( γ ^ 2 + γ * pc ) - γ from rfl, Real.sqrt_nonneg ( γ ^ 2 + γ * pc ), Real.mul_self_sqrt ( show 0 ≤ γ ^ 2 + γ * pc by positivity ) ] );
      rw [ div_lt_div_iff₀ ] <;> nlinarith;
    convert h_surplus using 1 <;> unfold Surplus Leg Cap <;> ring

/-
**R5 — Cooperative-Witness Advantage.** Total back-action to reach a fixed target
legibility is strictly decreasing in the number `K` of shared-outcome witnesses: cooperative
mutualistic monitoring certifies below the solitary collapse threshold.
-/
theorem cooperative_witness_total_backaction_decreasing_in_K
    (γ L : ℝ) (hγ : 0 < γ) (hL0 : 0 < L) (hL1 : L < 1) :
    StrictAntiOn (Dtot γ L) (Set.Ici (1 : ℝ)) := by
  intro K1 hK1 K2 hK2 hKL; simp_all +decide;
  -- Let $c = -\log(1-L)$, so $c > 0$.
  set c : ℝ := -Real.log (1 - L)
  have hc_pos : 0 < c := by
    exact neg_pos_of_neg ( Real.log_neg ( by linarith ) ( by linarith ) );
  -- We need to show that $g(K) = K * (\exp(c/K) - 1)$ is strictly decreasing on $[1, \infty)$.
  have hg_decreasing : StrictAntiOn (fun K : ℝ => K * (Real.exp (c / K) - 1)) (Set.Ici 1) := by
    -- We need to show that the derivative of $g(K)$ is negative for $K \geq 1$.
    have hg_deriv_neg : ∀ K ≥ 1, deriv (fun K => K * (Real.exp (c / K) - 1)) K < 0 := by
      intro K hK; norm_num [ div_eq_mul_inv, differentiableAt_inv, show K ≠ 0 by linarith ] ; ring_nf ;
      norm_num [ sq, mul_assoc, ne_of_gt ( zero_lt_one.trans_le hK ) ];
      nlinarith [ Real.exp_pos ( c * K⁻¹ ), Real.exp_neg ( c * K⁻¹ ), mul_inv_cancel₀ ( ne_of_gt ( Real.exp_pos ( c * K⁻¹ ) ) ), Real.add_one_lt_exp ( show c * K⁻¹ ≠ 0 by positivity ), Real.add_one_lt_exp ( show - ( c * K⁻¹ ) ≠ 0 by exact neg_ne_zero.mpr ( mul_ne_zero hc_pos.ne' ( inv_ne_zero ( by linarith ) ) ) ) ];
    intros K1 hK1 K2 hK2 hKL;
    have := exists_deriv_eq_slope ( fun K => K * ( Real.exp ( c / K ) - 1 ) ) hKL;
    contrapose! this;
    exact ⟨ continuousOn_of_forall_continuousAt fun x hx => by exact ContinuousAt.mul continuousAt_id <| ContinuousAt.sub ( Real.continuous_exp.continuousAt.comp <| ContinuousAt.div continuousAt_const continuousAt_id <| by linarith [ hx.1, Set.mem_Ici.mp hK1 ] ) continuousAt_const, fun x hx => DifferentiableAt.differentiableWithinAt <| by exact DifferentiableAt.mul differentiableAt_id <| DifferentiableAt.sub ( DifferentiableAt.exp <| DifferentiableAt.div ( differentiableAt_const _ ) differentiableAt_id <| by linarith [ hx.1, Set.mem_Ici.mp hK1 ] ) <| differentiableAt_const _, fun x hx => by rw [ ne_eq, eq_div_iff ] <;> nlinarith [ hg_deriv_neg x <| by linarith [ hx.1, Set.mem_Ici.mp hK1 ] ] ⟩;
  convert mul_lt_mul_of_pos_left ( hg_decreasing ( show 1 ≤ K1 by linarith ) ( show 1 ≤ K2 by linarith ) hKL ) hγ using 1 <;> norm_num [ Dtot ] ; ring;
  · rw [ Real.rpow_def_of_pos ( by linarith ) ] ; ring;
    grind;
  · rw [ Real.rpow_def_of_pos ( by linarith ) ] ; ring;
    grind

/-
**R5 (asymptote) — Cooperative back-action saturates** at the finite floor
`γ·log(1/(1-L))` as the witness count `K → ∞`.
-/
theorem cooperative_witness_backaction_limit
    (γ L : ℝ) (hγ : 0 < γ) (hL0 : 0 < L) (hL1 : L < 1) :
    Filter.Tendsto (Dtot γ L) Filter.atTop (nhds (γ * Real.log (1 / (1 - L)))) := by
  unfold Dtot;
  -- Let $t = \frac{1}{K}$, so we can rewrite the limit as $t \to 0^+$.
  suffices h_lim : Filter.Tendsto (fun t : ℝ => (1 / t) * ((1 - L) ^ (-t) - 1)) (Filter.map (fun K => 1 / K) Filter.atTop) (nhds (Real.log (1 / (1 - L)))) by
    convert h_lim.const_mul γ |> Filter.Tendsto.comp <| Filter.tendsto_map using 2 ; norm_num ; ring!;
  simpa [ div_eq_inv_mul, Real.rpow_def_of_pos ( sub_pos.mpr hL1 ) ] using HasDerivAt.tendsto_slope_zero_right ( HasDerivAt.sub ( HasDerivAt.exp ( HasDerivAt.const_mul ( -Real.log ( 1 - L ) ) ( hasDerivAt_id 0 ) ) ) ( hasDerivAt_const 0 1 ) )

/-
**R6 — Witness efficiency is the cos²Θ universal geometry.** `η_W = extracted /
(extracted + back-action) = cos²Θ`, and lies in `[0, 1]`.
-/
theorem witness_efficiency_eq_cos2_theta (Θ : ℝ) :
    (Real.cos Θ ^ 2) / (Real.cos Θ ^ 2 + Real.sin Θ ^ 2) = Real.cos Θ ^ 2
      ∧ 0 ≤ Real.cos Θ ^ 2 ∧ Real.cos Θ ^ 2 ≤ 1 := by
  exact ⟨ by rw [ Real.cos_sq_add_sin_sq, div_one ], sq_nonneg _, Real.cos_sq_le_one _ ⟩

end MIST