/-
===============================================================================
  The Thermodynamic Discounting Theorem (TDT) — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
===============================================================================

CONTEXT (nightly Run 080, thermodynamic-discounting-theorem; [02] Thermodynamic
Economics × Thermodynamic lens; CONVERGENCE EVENT; 22nd IB self-application,
"the Appraiser").

  A degrading natural D-Capital asset has TVT value `V > 0` (Run 047), measured in
  Landauer units.  Restoring it to target by a hard horizon `T > 0` costs
  irreversible entropy on the single-system tempo cost (Run 060 / 079):

        Σ(T) = A / T + B · T,        A, B > 0,

  whose free optimum is at the critical horizon  τ* = √(A / B)  with flat cost
  Σ* = 2√(A·B).  The *deadline shadow price* is  λ = − dΣ*/dT :

        scarce   (T < τ*):  Σ*(T) = A/T + B·T,   λ(T) = A / T² − B   ( > 0 ),
        abundant (T ≥ τ*):  Σ*    = 2√(A·B)   ,   λ    = 0.

  The endogenous (thermodynamic) discount rate is the deadline shadow price per
  unit asset value:

        r_thermo(T) = λ(T) / V.

WHAT IS PROVEN HERE (clean core — target: 0 `sorry`, axioms ⊆
{propext, Classical.choice, Quot.sound}):

  1. thermo_discount_rate_eq_lambda_over_value      (R1, defining identity)
        r_thermo · V = λ.
  2. discount_rate_zero_in_abundant_time_regime     (R2, abundant / "Stern" pole)
        T ≥ τ*  ⟹  r_thermo = 0.
  3. discount_rate_diverges_at_tipping              (R3)
        as A → ∞ (critical slowing down, τ* → ∞)  r_thermo → +∞.
  4. pv_kernel_recovers_tvt_at_zero_lambda          (R4)
        λ = 0  ⟹  discount kernel ≡ 1, so the present-value integrand equals the
        undiscounted gross flux — PV recovers the TVT stock value.
  5. stern_nordhaus_regime_dichotomy_monotone_single_crossover   (R2 flagship)
        r_thermo(·) is 0 on [τ*,∞), strictly positive on (0,τ*), and strictly
        decreasing on (0,τ*): one law, two regimes, a single crossover at τ*.
  6. tdt_nonvacuous
        a concrete scarce-regime instance with r_thermo > 0, so 1–5 are NOT
        vacuous.

THE HONEST BOUNDARY (inputs, NOT formalized here):
  - that the single-system tempo cost is exactly A/T + B·T (Van Vu–Saito haste
    cost + linear neglect cost) is the physical model supplied by Run 060 / 079;
  - R6 (discounting efficiency η = cos²Θ) is an instance of the existing canon
    CSUT-017 inner-product efficiency pattern (hand-instantiated at assembly);
    R5's bare Intelligence-Bound ceiling dI/dt ≤ P·D/(k_B T ln 2) restates the
    canon P0 master bound and is not re-proved here.

NON-VACUITY: `tdt_nonvacuous` exhibits A=2, B=1, V=1, T=1 with τ*=√2 > 1, so the
scarce regime is genuinely inhabited and r_thermo = 1 > 0; the monotonicity and
positivity conclusions are therefore non-trivial.
-/
import Mathlib

set_option autoImplicit false

open Filter Topology

namespace Viridis.Economics.ThermodynamicDiscounting

/-- Critical (free-optimum) restoration horizon  τ* = √(A / B). -/
noncomputable def tcrit (A B : ℝ) : ℝ := Real.sqrt (A / B)

/-- Deadline shadow price  λ = − dΣ*/dT.  Scarce regime (`T < τ*`): `A / T² − B`;
abundant regime (`T ≥ τ*`): `0`. -/
noncomputable def lambdaShadow (A B T : ℝ) : ℝ :=
  if T < tcrit A B then A / T ^ 2 - B else 0

/-- Endogenous thermodynamic discount rate  r_thermo = λ / V. -/
noncomputable def rThermo (A B V T : ℝ) : ℝ := lambdaShadow A B T / V

/-- The discount kernel  exp(− r · t). -/
noncomputable def discountKernel (r t : ℝ) : ℝ := Real.exp (-(r * t))

/-
**R1 — Thermodynamic Discounting Theorem (defining identity).**
The thermodynamic discount rate, multiplied by the asset value, returns the
deadline shadow price:  `r_thermo · V = λ`.
-/
theorem thermo_discount_rate_eq_lambda_over_value
    (A B V T : ℝ) (hV : V ≠ 0) :
    rThermo A B V T * V = lambdaShadow A B T := by
  exact div_mul_cancel₀ _ hV

/-
**R2 (abundant pole) — zero endogenous discounting with restoration headroom.**
When the funding horizon meets or exceeds the critical horizon τ*, the tempo is
unconstrained, the shadow price vanishes, and the endogenous discount rate is
exactly zero (the "Stern" regime).
-/
theorem discount_rate_zero_in_abundant_time_regime
    (A B V T : ℝ) (hT : tcrit A B ≤ T) :
    rThermo A B V T = 0 := by
  unfold rThermo lambdaShadow;
  rw [ if_neg ( not_lt_of_ge hT ), zero_div ]

/-
**R3 — Tipping-point discount divergence.**
Near a tipping point, critical slowing down sends the restoration time τ* → ∞,
i.e. `A → ∞`.  For a fixed positive horizon, value and neglect cost, the
endogenous discount rate then diverges to `+∞`.
-/
theorem discount_rate_diverges_at_tipping
    (B V T : ℝ) (hB : 0 < B) (hV : 0 < V) (hT : 0 < T) :
    Tendsto (fun A : ℝ => rThermo A B V T) atTop atTop := by
  -- For A large enough, tcrit A B = sqrt(A/B) → ∞ as A → ∞, so eventually T < tcrit A B, hence lambdaShadow A B T = A/T^2 - B and rThermo A B V T = (A/T^2 - B)/V.
  have h_eventually : ∀ᶠ A in Filter.atTop, rThermo A B V T = (A / T^2 - B) / V := by
    unfold rThermo lambdaShadow;
    norm_num [ tcrit ];
    exact ⟨ T ^ 2 * B + 1, fun x hx => by rw [ if_pos ( Real.lt_sqrt_of_sq_lt ( by rw [ lt_div_iff₀ hB ] ; nlinarith ) ) ] ⟩;
  rw [ Filter.tendsto_congr' h_eventually ] ; exact Filter.Tendsto.atTop_div_const ( by positivity ) ( Filter.tendsto_atTop_add_const_right _ _ <| Filter.tendsto_id.atTop_mul_const <| by positivity ) ;

/-
**R4 — Present-value kernel recovers TVT at zero shadow price.**
With `λ = 0` the discount kernel collapses to `1`, so the discounted
present-value integrand equals the undiscounted gross-flux integrand at every
time — PV reduces to the undiscounted TVT stock value (Run 047).
-/
theorem pv_kernel_recovers_tvt_at_zero_lambda
    (A B V T : ℝ) (Vdot : ℝ → ℝ) (h : rThermo A B V T = 0) :
    ∀ t : ℝ, Vdot t * discountKernel (rThermo A B V T) t = Vdot t := by
  unfold discountKernel; aesop;

/-
**R2 — The Stern–Nordhaus regime dichotomy (monotone, single crossover).**
One physical law with two regimes separated by the single critical horizon
τ* = √(A / B):
  (i)   abundant `T ≥ τ*`:        `r_thermo = 0`  (Stern pole);
  (ii)  scarce  `0 < T < τ*`:     `r_thermo > 0`  (Nordhaus pole);
  (iii) on the scarce branch `r_thermo` is *strictly decreasing* in the horizon,
        so the two poles meet at exactly one crossover, τ*.
-/
theorem stern_nordhaus_regime_dichotomy_monotone_single_crossover
    (A B V : ℝ) (hA : 0 < A) (hB : 0 < B) (hV : 0 < V) :
    (∀ T : ℝ, tcrit A B ≤ T → rThermo A B V T = 0) ∧
    (∀ T : ℝ, 0 < T → T < tcrit A B → 0 < rThermo A B V T) ∧
    (∀ T₁ T₂ : ℝ, 0 < T₁ → T₁ < T₂ → T₂ < tcrit A B →
        rThermo A B V T₂ < rThermo A B V T₁) := by
  refine' ⟨ _, _, _ ⟩;
  · grind +locals;
  · unfold rThermo lambdaShadow tcrit;
    intro T hT₁ hT₂; rw [ if_pos hT₂ ] ; exact div_pos ( sub_pos.mpr ( by rw [ lt_div_iff₀ ( sq_pos_of_pos hT₁ ) ] ; nlinarith [ mul_div_cancel₀ A hB.ne', Real.mul_self_sqrt ( show 0 ≤ A / B by positivity ), pow_two_nonneg ( T - Real.sqrt ( A / B ) ), Real.sqrt_nonneg ( A / B ), mul_pos hT₁ hB, mul_pos hT₁ hV, mul_pos hB hV ] ) ) hV;
  · unfold rThermo lambdaShadow tcrit;
    intro T₁ T₂ h₁ h₂ h₃; rw [ if_pos h₃, if_pos ( by linarith ) ] ; gcongr;

/-
**Non-vacuity witness.**  With A = 2, B = 1, V = 1, T = 1 the critical horizon
is τ* = √2 > 1, so the horizon binds (scarce regime), λ = 2 − 1 = 1, and the
endogenous discount rate is strictly positive.
-/
theorem tdt_nonvacuous : 0 < rThermo 2 1 1 1 := by
  unfold rThermo lambdaShadow tcrit; norm_num;
  rw [ if_pos ] <;> norm_num [ Real.lt_sqrt ]

end Viridis.Economics.ThermodynamicDiscounting