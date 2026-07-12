/-
  Kibble–Zurek Speed Limit Theorem (KZSLT) — clean analytic core
  ==============================================================
  Viridis Canon · Nightly Run-092 (2026-07-07) · [05] Thermodynamic Speed Limits × 🔥 Thermodynamic
  "The Quencher" — 34th Intelligence-Bound self-application.
  Continuous/critical (Kibble–Zurek) member of the finite-time transition taxonomy
  (continuous-confluence/054 · third-law-freeze/057 · first-order-nucleation/090,091 · critical-KZ/092).

  CONTEXT.  Driving a system across a *continuous* critical point in finite time
  (ε(t)=t/τ_Q, ε=0 the threshold) is inherently irreversible and entropy-producing.
  With static/dynamic critical exponents (ν,z) and defect codimension D̄, the
  Kibble–Zurek exponent is

      α_KZ  ≡  D̄ · ν / (1 + ν z).

  This file certifies the clean analytic core of the six boxed results.  All statements
  are encoded to be well-posed and NON-VACUOUS; proof bodies are `sorry` for the forge.

  Targets:
    R1  kzsl_product_form_equiv          — speed limit  Σ·τ^α ≥ K  ⇔  Σ ≥ K·τ^(−α)
        kzsl_criticality_cushions_haste  — criticality cushions haste: α∈(0,1) ⇒ τ^(−α) < τ^(−1) (fast regime)
    R2  critical_tempo_first_order       — the optimum τ_Q*=(αA/B)^(1/(1+α)) satisfies C'(τ*)=0
        critical_tempo_recovers_run060   — α=1 ⇒ τ_Q* = √(A/B)  (contains the Run-060 Tempo Theorem)
    R4  critical_wall_time_diverges      — t_min(ε) ∝ ε^(−νz) → ∞ as ε→0⁺  (the Critical Wall)
    R5  quencher_residual_floor          — 0 < n_ach(ε) < n_KZ  (IB-floored residual; 34th self-application)
    R6  crossing_efficiency_eq_cos2      — η = ⟨drive,mode⟩²/(‖·‖²‖·‖²) ∈ [0,1], =1 iff aligned (cos²Θ)
        kzslt_nonvacuous                 — explicit mean-field-kink witness (α_KZ=1/4∈(0,1), τ*>0)

  DEFERRED (well-posedness / rpow-convexity gate — see FORGE_STATE + note to Justin):
    R3 symmetry-breaking asymmetry inequality  (⚠ boxed ρ(u) formula in the finding has its two
        terms swapped: the correct cost ratio at the optimum is ρ(u)=(u^(−α)+α u)/(1+α), NOT
        (α u^(−α)+u)/(1+α); flagged for restatement before canon);
    full StrictConvexOn global-min uniqueness of C(τ)=A τ^(−α)+B τ (general real exponent, rpow).
-/
import Mathlib

namespace Viridis.SpeedLimits.KibbleZurekSpeedLimit

open Real

/-- Kibble–Zurek exponent  α_KZ = D̄ ν / (1 + ν z). -/
noncomputable def alphaKZ (Dbar nu z : ℝ) : ℝ := Dbar * nu / (1 + nu * z)

/-- Cost-optimal quench time  τ_Q* = (α A / B)^(1/(1+α)). -/
noncomputable def tauStar (α A B : ℝ) : ℝ := (α * A / B) ^ ((1 : ℝ) / (1 + α))

/-! ### R1 — The Kibble–Zurek Speed Limit -/

/-
**R1 (the KZSL, product-form ⇔ explicit bound).**  For any positive quench time the
    thermodynamic speed limit in canonical product form `Σ·τ^α ≥ K` is equivalent to the
    explicit power-law lower bound `Σ ≥ K·τ^(−α)`.  This is the inequality that
    renormalizes the analytic TSL exponent 1 to the universal Kibble–Zurek exponent α.
    Non-vacuous: both directions are substantive (τ^α is a genuine positive factor).
-/
theorem kzsl_product_form_equiv (τ α K Scr : ℝ) (hτ : 0 < τ) :
    K ≤ Scr * τ ^ α ↔ K * τ ^ (-α) ≤ Scr := by
  constructor <;> intro h <;> rw [ Real.rpow_neg hτ.le ] at *;
  · rwa [ ← div_eq_mul_inv, div_le_iff₀ ( Real.rpow_pos_of_pos hτ α ) ];
  · rwa [ ← div_eq_mul_inv, div_le_iff₀ ( Real.rpow_pos_of_pos hτ α ) ] at h

/-
**R1 (criticality cushions haste).**  Because α_KZ < 1 for standard universality
    classes, the KZ speed-limit lower bound `τ^(−α)` is strictly gentler than the
    analytic (Run-060 / Nagayama–Ito smooth-protocol) exponent-1 bound `τ^(−1)` in the
    fast-crossing regime τ<1: critical slowing down partially protects the system from
    its own hurry.  Non-vacuous strict inequality.
-/
theorem kzsl_criticality_cushions_haste (τ α : ℝ)
    (hτ0 : 0 < τ) (hτ1 : τ < 1) (hα0 : 0 < α) (hα1 : α < 1) :
    τ ^ (-α) < τ ^ (-(1 : ℝ)) := by
  exact Real.rpow_lt_rpow_of_exponent_gt hτ0 hτ1 ( by linarith )

/-! ### R2 — The Critical Tempo Theorem (generalizes Run 060) -/

/-
**R2 (first-order optimality).**  The crossing cost `C(τ) = A·τ^(−α) + B·τ` (haste +
    neglect) is stationary at the closed-form optimum `τ_Q* = (αA/B)^(1/(1+α))`: the
    optimum equalizes the marginal defect-reduction `α·A·τ^(−(α+1))` and the marginal
    neglect drift `B`, i.e. C'(τ*)=0.  Non-vacuous: the identity pins τ* uniquely.
-/
theorem critical_tempo_first_order (α A B : ℝ)
    (hα : 0 < α) (hA : 0 < A) (hB : 0 < B) :
    α * A * (tauStar α A B) ^ (-(α + 1)) = B := by
  unfold tauStar;
  rw [ ← Real.rpow_mul ] <;> norm_num <;> try positivity;
  rw [ show ( 1 + α ) ⁻¹ * ( -1 + -α ) = -1 by nlinarith [ mul_inv_cancel₀ ( by linarith : ( 1 + α ) ≠ 0 ) ], Real.rpow_neg_one, inv_div ] ; ring_nf ;
  grind

/-
**R2 (containment of Run-060).**  At the analytic exponent α=1 (no criticality) the
    optimal quench time reduces exactly to `τ_Q* = √(A/B)` — the Run-060 Haste–Neglect
    Tempo optimum.  KZSLT is thus a strict generalization of prior canon; criticality is a
    universal renormalization of its exponent.  Non-vacuous identity.
-/
theorem critical_tempo_recovers_run060 (A B : ℝ) (hA : 0 < A) (hB : 0 < B) :
    tauStar 1 A B = Real.sqrt (A / B) := by
  unfold tauStar; norm_num [ Real.sqrt_eq_rpow ] ;

/-! ### R4 — The Critical Wall -/

/-
**R4 (the Critical Wall).**  To make a fixed finite move at reduced distance ε the
    mobility vanishes as μ(ε) ∝ ε^(νz), so the TSL minimum move-time
    `t_min(ε) ∝ ε^(−νz)` diverges as ε→0⁺: the critical point is an infinite-time wall
    for finite-dissipation moves — the speed-limit face of critical slowing down, and the
    physics under Run-080's discount-rate blow-up and Run-071's ignition divergence.
    Non-vacuous genuine divergence (exponent q = νz > 0).
-/
theorem critical_wall_time_diverges (K q : ℝ) (hK : 0 < K) (hq : 0 < q) :
    Filter.Tendsto (fun ε : ℝ => K * ε ^ (-q))
      (nhdsWithin 0 (Set.Ioi 0)) Filter.atTop := by
  have h_exp : Filter.Tendsto (fun ε : ℝ => ε ^ (-q)) (nhdsWithin 0 (Set.Ioi 0)) Filter.atTop := by
    have := Real.tendsto_log_nhdsGT_zero;
    have : Filter.Tendsto (fun ε : ℝ => Real.exp (q * (-Real.log ε))) (nhdsWithin 0 (Set.Ioi 0)) Filter.atTop := by
      exact Real.tendsto_exp_atTop.comp <| Filter.Tendsto.const_mul_atTop hq <| Filter.tendsto_neg_atBot_atTop.comp this;
    exact this.congr' ( Filter.eventuallyEq_of_mem self_mem_nhdsWithin fun x hx => by rw [ Real.rpow_def_of_pos hx ] ; ring );
  exact h_exp.const_mul_atTop hK

/-! ### R5 — The Quencher (34th Intelligence-Bound self-application) -/

/-- Counterdiabatic control demand rate `R_demand(ε) = c·ε^(−p)` (diverges at criticality). -/
noncomputable def Rdemand (c p ε : ℝ) : ℝ := c * ε ^ (-p)

/-- Achievable defect density under finite-power control:
    `n_ach(ε) = n_KZ · exp(−R_ctrl / R_demand(ε))`. -/
noncomputable def nAch (nKZ Rctrl c p ε : ℝ) : ℝ :=
  nKZ * Real.exp (-Rctrl / Rdemand c p ε)

/-
**R5 (the Quencher — IB-floored residual).**  A finite-power controller (finite
    R_ctrl) can suppress crossing defects strictly below the Kibble–Zurek floor but never
    to zero: `0 < n_ach(ε) < n_KZ`.  Since the Intelligence Bound caps the control-info
    supply `dI/dt ≤ P·D/(k_BT ln2)` while the counterdiabatic demand diverges at the
    threshold, zero-defect crossing is thermodynamically-information forbidden.
    Non-vacuous strict two-sided bound; the 34th IB self-application.
-/
theorem quencher_residual_floor (nKZ Rctrl c p ε : ℝ)
    (hn : 0 < nKZ) (hR : 0 < Rctrl) (hc : 0 < c) (hp : 0 < p) (hε : 0 < ε) :
    0 < nAch nKZ Rctrl c p ε ∧ nAch nKZ Rctrl c p ε < nKZ := by
  unfold nAch Rdemand; norm_num [ hn, hR, hc, hp, hε ] ;
  exact ⟨ Real.exp_pos _, div_neg_of_neg_of_pos ( neg_neg_of_pos hR ) ( by positivity ) ⟩

/-! ### R6 — Crossing efficiency = cos²Θ  (recurring canon signature) -/

open RealInnerProductSpace in
/-- **R6 (crossing efficiency = cos²Θ).**  The control-alignment efficiency of a crossing
    protocol, `η = ⟨drive, soft-mode⟩² / (‖drive‖²‖mode‖²)`, lies in [0,1] and saturates
    (η=1, adiabatic-efficient) iff the drive is exactly collinear with the critical soft
    mode; misaligned drive spills into transverse modes as defects.  Nth instance of the
    canon's efficiency-as-squared-cosine law.  Non-vacuous (Cauchy–Schwarz, with genuine
    equality case). -/
theorem crossing_efficiency_eq_cos2
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (d m : E) (hd : d ≠ 0) (hm : m ≠ 0) :
    0 ≤ (inner ℝ d m : ℝ) ^ 2 / (‖d‖ ^ 2 * ‖m‖ ^ 2)
      ∧ (inner ℝ d m : ℝ) ^ 2 / (‖d‖ ^ 2 * ‖m‖ ^ 2) ≤ 1
      ∧ ((inner ℝ d m : ℝ) ^ 2 / (‖d‖ ^ 2 * ‖m‖ ^ 2) = 1 ↔ ∃ c : ℝ, m = c • d) := by
  refine' ⟨ by positivity, _, ⟨ fun h => _, fun h => _ ⟩ ⟩;
  · exact div_le_one_of_le₀ ( by nlinarith [ abs_le.mp ( abs_real_inner_le_norm d m ) ] ) ( by positivity );
  · -- By the equality case of Cauchy-Schwarz, we have that $m$ is a scalar multiple of $d$.
    have h_eq : ‖m - (⟪d, m⟫ / ‖d‖ ^ 2) • d‖ = 0 := by
      have h_eq : ‖m - (⟪d, m⟫ / ‖d‖ ^ 2) • d‖ ^ 2 = ‖m‖ ^ 2 - (⟪d, m⟫ ^ 2 / ‖d‖ ^ 2) := by
        rw [ @norm_sub_sq ℝ ] ; simp +decide [ real_inner_comm, inner_smul_right ] ; ring;
        simp +decide [ norm_smul, mul_pow ] ; ring;
        grind;
      grind +splitIndPred;
    exact ⟨ _, sub_eq_zero.mp ( norm_eq_zero.mp h_eq ) ⟩;
  · rcases h with ⟨ c, rfl ⟩ ; simp +decide [ inner_smul_right, norm_smul ] ; ring_nf ;
    simp_all +decide

/-! ### Non-vacuity witness -/

/-
**Explicit non-vacuity witness.**  Mean-field kink universality (ν=1/2, z=2, D̄=1)
    gives α_KZ = 1/4 ∈ (0,1) — so criticality genuinely cushions haste (R1) and the
    haste–neglect symmetry genuinely breaks — and with A=B=1 the optimal quench time
    τ_Q* = (1/4)^(4/5) is a positive interior optimum.  Certifies the core is non-vacuous.
-/
theorem kzslt_nonvacuous :
    alphaKZ 1 (1 / 2) 2 = 1 / 4
      ∧ (0 : ℝ) < 1 / 4 ∧ (1 / 4 : ℝ) < 1
      ∧ 0 < tauStar (1 / 4) 1 1 := by
  exact ⟨ by unfold alphaKZ; norm_num, by norm_num, by norm_num, by unfold tauStar; positivity ⟩

end Viridis.SpeedLimits.KibbleZurekSpeedLimit