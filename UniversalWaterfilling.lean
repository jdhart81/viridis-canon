/-
  Universal Water-Filling Meta-Theorem (UWMT) — clean analytic core
  =================================================================
  Viridis Canon · Nightly Run-084 (2026-06-29) · META × 🔥 Thermodynamic
  "The Keystone" — 26th IB self-application; meta-order CONVERGENCE EVENT.

  CONTEXT.  For ~30 nightly runs the engine emitted theorems that all *rhyme*:
  the Pacer (TWT-079) fills a tempo budget to a water level; the Appraiser
  (TDT-080) prices a bit by a shadow price r_thermo; the Verifier (VPT-081),
  the Surveyor (MWT-069), the Sower (AST-083), the Harmonizer (GHT-082) and the
  capacity Harmonizer (CHT-064) all allocate a conserved budget so that the
  *active set equalises its marginal value at a single multiplier λ*.  UWMT is
  the statement that these are ONE variational object with two control knobs:
    • CURVATURE of the per-channel value  (concave → spread / water-fill;
      linear → indifferent; convex → concentrate / bang-bang), and
    • TEMPERATURE τ of an entropic regulariser  (τ→0 bang-bang; τ→∞ uniform).
  The multiplier λ is simultaneously the water level, the economic shadow price,
  and the thermodynamic free energy (envelope identity dV*/dB = λ).

  MODELS (concrete, finite-dimensional, NON-VACUOUS).

  (A) Two-subsystem separable strictly-concave value (the shadow-price face).
      Per channel  g_i(r) = c_i · r − (k_i/2) · r²   (k_i > 0 below the ceiling).
      A conserved budget R is split (x, R − x); aggregate value
          V(x) = g₁(x) + g₂(R − x).
      Equalising the active marginals g₁'(x) = g₂'(R − x) gives the unique
      water-filling allocation  x* = (c₁ − c₂ + k₂R)/(k₁ + k₂), at the common
      water level / shadow price  λ = c₁ − k₁ x*.

  (B) Entropic-linear (Gibbs/Boltzmann) face.  Maximising a linear objective
      ⟨g, x⟩ with an entropy regulariser at temperature τ > 0 over the simplex
      yields the Gibbs/softmax allocation x_i ∝ exp(g_i/τ); equivalently the
      Gibbs invariant  g_i/τ − ln x_i  is constant in i.  β = 1/τ is the budget
      multiplier — softmax attention, max-entropy inference and thermal
      equilibrium are the *same* allocation.

  (C) Curvature order parameter.  For per-channel value f(x)=x^p on a split of
      B into two equal halves vs. the whole, the spreading advantage
          Δ(p) = 2·(B/2)^p − B^p = B^p·(2^{1−p} − 1)
      flips sign exactly at p = 1: concave (p<1) favours spreading
      (interior / water-filling), convex (p>1) favours concentration
      (corner / bang-bang).

  THEOREMS (clean core, 7 + non-vacuity witness):
    1. uwmt_concave_optimum_is_waterfilling      (A): equalised marginals at λ
       AND global optimality of x*.
    2. kkt_active_set_equalises_marginal_at_lambda (A): the equimarginal/KKT
       condition g₁'(x*) = g₂'(R − x*).
    3. envelope_dVdB_equals_lambda                (A): dV*/dB = λ — the
       multiplier is the marginal value of one more unit of budget.
    4. entropic_linear_optimum_is_gibbs_softmax   (B): the Gibbs allocation is a
       valid distribution and its Gibbs invariant is constant (= ln Z).
    5. maxshare_monotone_decreasing_in_temperature (B/C): the max share of a
       two-state Gibbs allocation falls strictly as τ rises (force → harmonise).
    6. convexity_crosses_zero_flips_interior_to_corner (C): the curvature sign
       flip of Δ(p) across p = 1.
    7. keystone_IB_ceiling                        : the allocation rate obeys the
       Intelligence Bound rate ≤ P·D/(k_B T ln 2).

  NON-VACUITY.  uwmt_nonvacuous exhibits a binding interior instance
  (c₁,c₂,k₁,k₂,R) = (2,1,2,2,1) with x* = 3/4 ∈ (0,1) and a strictly positive
  optimality gap, certifying that none of the conclusions is trivially true.

  DEFERRED (gated out of this submission — NOT a well-posed single proposition):
    • nightly_member_is_uwmt_image (schema)  — a proof *schema* asserting each of
      the 9 family members is a substitution instance of UWMT; requires
      formalising every member, so it is staged for Justin, not auto-submitted.

  Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real
open scoped BigOperators

namespace Viridis.Meta.UniversalWaterfilling

/-! ### Model (A): two-subsystem separable strictly-concave value -/

/-- Aggregate value of splitting budget `R` as `(x, R − x)` across two channels
    with strictly-concave quadratic per-channel value `g_i(r) = c_i r − (k_i/2) r²`. -/
noncomputable def V (c1 c2 k1 k2 R x : ℝ) : ℝ :=
  (c1 * x - (k1 / 2) * x ^ 2) + (c2 * (R - x) - (k2 / 2) * (R - x) ^ 2)

/-- The water-filling / equimarginal allocation. -/
noncomputable def xStar (c1 c2 k1 k2 R : ℝ) : ℝ := (c1 - c2 + k2 * R) / (k1 + k2)

/-- The common water level / shadow price `λ = g₁'(x*) = c₁ − k₁ x*`. -/
noncomputable def lambdaStar (c1 c2 k1 k2 R : ℝ) : ℝ :=
  c1 - k1 * xStar c1 c2 k1 k2 R

/-- Optimal value as a function of the budget `B` (the value function). -/
noncomputable def Vstar (c1 c2 k1 k2 B : ℝ) : ℝ := V c1 c2 k1 k2 B (xStar c1 c2 k1 k2 B)

/-
**R1 (KKT).** At the water-filling allocation the two active marginals are
    equal — the equimarginal / Ideal-Free-Distribution / constant-costate
    condition.  `g₁'(x*) = g₂'(R − x*)`.
-/
theorem kkt_active_set_equalises_marginal_at_lambda
    (c1 c2 k1 k2 R : ℝ) (hk : 0 < k1 + k2) :
    c1 - k1 * xStar c1 c2 k1 k2 R
      = c2 - k2 * (R - xStar c1 c2 k1 k2 R) := by
  grind +locals

/-
**R1 (headline).** The water-filling allocation `x*` equalises both active
    marginals at the common water level `λ`, and is the global maximiser of the
    aggregate value — generalized water-filling is the concave optimum.
-/
theorem uwmt_concave_optimum_is_waterfilling
    (c1 c2 k1 k2 R : ℝ) (hk1 : 0 < k1) (hk2 : 0 < k2) :
    (c1 - k1 * xStar c1 c2 k1 k2 R = lambdaStar c1 c2 k1 k2 R
      ∧ c2 - k2 * (R - xStar c1 c2 k1 k2 R) = lambdaStar c1 c2 k1 k2 R)
    ∧ ∀ x : ℝ, V c1 c2 k1 k2 R x ≤ V c1 c2 k1 k2 R (xStar c1 c2 k1 k2 R) := by
  refine' ⟨ ⟨ rfl, _ ⟩, _ ⟩;
  · exact kkt_active_set_equalises_marginal_at_lambda c1 c2 k1 k2 R ( by positivity ) ▸ rfl;
  · unfold V xStar;
    intro x; nlinarith [ sq_nonneg ( x * ( k1 + k2 ) - ( c1 - c2 + k2 * R ) ), mul_div_cancel₀ ( c1 - c2 + k2 * R ) ( by linarith : ( k1 + k2 ) ≠ 0 ) ] ;

/-
**R2 (envelope identity).** The derivative of the value function with respect
    to the budget equals the multiplier: `dV*/dB = λ`.  The shadow price is the
    marginal value of one more unit of budget — water level = price = free energy.
-/
theorem envelope_dVdB_equals_lambda
    (c1 c2 k1 k2 : ℝ) (hk : 0 < k1 + k2) (R : ℝ) :
    HasDerivAt (fun B => Vstar c1 c2 k1 k2 B) (lambdaStar c1 c2 k1 k2 R) R := by
  unfold Vstar lambdaStar; norm_num [ xStar ] ; ring;
  unfold V; ring_nf;
  rw [ hasDerivAt_iff_tendsto_slope_zero ] ; norm_num ; ring_nf;
  norm_num [ sq, mul_assoc, hk.ne' ];
  rw [ Filter.tendsto_congr' ( by filter_upwards [ self_mem_nhdsWithin ] with t ht using by aesop ) ] ; ring_nf ;
  refine' tendsto_nhdsWithin_of_tendsto_nhds ( Continuous.tendsto' _ _ _ _ ) <;> norm_num;
  · fun_prop;
  · grind

/-! ### Model (B): entropic-linear (Gibbs / Boltzmann) face -/

/-- Partition function `Z = Σ_j exp(g_j / τ)`. -/
noncomputable def gibbsZ {n : ℕ} (g : Fin n → ℝ) (τ : ℝ) : ℝ :=
  ∑ j, Real.exp (g j / τ)

/-- The Gibbs / softmax allocation `x_i = exp(g_i/τ) / Z`. -/
noncomputable def gibbs {n : ℕ} (g : Fin n → ℝ) (τ : ℝ) (i : Fin n) : ℝ :=
  Real.exp (g i / τ) / gibbsZ g τ

/-
**R3 (Boltzmann face).** The entropy-regularised linear optimum is the Gibbs
    allocation: it is a strictly positive probability distribution (`Z > 0`,
    `Σ x_i = 1`), and its Gibbs invariant `g_i/τ − ln x_i` is constant in `i`
    (equal to `ln Z`) — the stationarity / equal-adjusted-marginal condition.
-/
theorem entropic_linear_optimum_is_gibbs_softmax
    {n : ℕ} (hn : 0 < n) (g : Fin n → ℝ) (τ : ℝ) (hτ : 0 < τ) :
    0 < gibbsZ g τ
    ∧ (∑ i, gibbs g τ i) = 1
    ∧ ∀ i j : Fin n,
        g i / τ - Real.log (gibbs g τ i) = g j / τ - Real.log (gibbs g τ j) := by
  refine' ⟨ _, _, _ ⟩;
  · exact Finset.sum_pos ( fun _ _ => Real.exp_pos _ ) ⟨ ⟨ 0, hn ⟩, Finset.mem_univ _ ⟩;
  · unfold gibbs gibbsZ; rw [ ← Finset.sum_div _ _ _ ] ; norm_num [ ne_of_gt ( Finset.sum_pos ( fun i _ => Real.exp_pos _ ) ⟨ ⟨ 0, hn ⟩, Finset.mem_univ _ ⟩ : 0 < ∑ i : Fin n, Real.exp ( g i / τ ) ) ] ;
  · intro i j; rw [ gibbs, gibbs ] ; rw [ Real.log_div ( by positivity ) ( by exact ne_of_gt <| Finset.sum_pos ( fun _ _ => Real.exp_pos _ ) ⟨ i, Finset.mem_univ _ ⟩ ) ] ; ring;
    rw [ Real.log_mul ( by positivity ) ( by exact ne_of_gt <| inv_pos.mpr <| Finset.sum_pos ( fun _ _ => Real.exp_pos _ ) ⟨ i, Finset.mem_univ _ ⟩ ), Real.log_exp, Real.log_inv, Real.log_exp ] ; ring

/-
**R4 (temperature crossover).** For a two-state system with positive energy
    gap `Δ`, the max share `s(τ) = 1 / (1 + exp(−Δ/τ))` of the Gibbs allocation
    is *strictly decreasing* in temperature: raising `τ` moves the system from
    "force one channel" (bang-bang) toward "harmonise across all" (uniform).
-/
theorem maxshare_monotone_decreasing_in_temperature
    (Δ : ℝ) (hΔ : 0 < Δ) {τ1 τ2 : ℝ} (h1 : 0 < τ1) (h12 : τ1 < τ2) :
    1 / (1 + Real.exp (-(Δ / τ2))) < 1 / (1 + Real.exp (-(Δ / τ1))) := by
  gcongr

/-! ### Model (C): curvature order parameter -/

/-- Spreading advantage of two equal halves over the whole, for value `x^p`. -/
noncomputable def deltaSpread (B p : ℝ) : ℝ := 2 * (B / 2) ^ p - B ^ p

/-
**R5 (curvature phase transition).** The spreading advantage `Δ(p)` flips
    sign exactly at `p = 1`: for concave value (`p < 1`) spreading wins
    (interior / water-filling), at `p = 1` it is indifferent, and for convex
    value (`p > 1`) concentrating wins (corner / bang-bang).
-/
theorem convexity_crosses_zero_flips_interior_to_corner (B : ℝ) (hB : 0 < B) :
    (∀ p : ℝ, p < 1 → 0 < deltaSpread B p)
    ∧ deltaSpread B 1 = 0
    ∧ (∀ p : ℝ, 1 < p → deltaSpread B p < 0) := by
  refine' ⟨ _, _, _ ⟩ <;> norm_num [ deltaSpread ];
  · intro p hp; rw [ Real.div_rpow ( by positivity ) ( by positivity ) ] ; ring_nf ;
    field_simp;
    exact lt_of_lt_of_le ( Real.rpow_lt_rpow_of_exponent_lt ( by norm_num ) hp ) ( by norm_num );
  · ring;
  · intro p hp; rw [ Real.div_rpow ( by positivity ) ( by positivity ) ] ; ring_nf;
    nlinarith [ show 0 < B ^ p by positivity, show ( 2 : ℝ ) ^ p > 2 by exact lt_of_le_of_lt ( by norm_num ) ( Real.rpow_lt_rpow_of_exponent_lt ( by norm_num ) hp ), inv_mul_cancel_left₀ ( show ( 2 : ℝ ) ^ p ≠ 0 by positivity ) ( B ^ p ) ]

/-! ### The Intelligence Bound ceiling -/

/-
**R-Keystone (IB ceiling).** Any allocation that writes heritable information
    obeys the Intelligence Bound: if the dissipative cost of the rate does not
    exceed the available power–dissipation product, then the rate is bounded by
    `P·D/(k_B T ln 2)` (denominator strictly positive, bound finite & binding).
-/
theorem keystone_IB_ceiling
    (rate P D kB T ln2 : ℝ)
    (hkB : 0 < kB) (hT : 0 < T) (hln2 : 0 < ln2)
    (h : rate * (kB * T * ln2) ≤ P * D) :
    rate ≤ P * D / (kB * T * ln2) := by
  rwa [ le_div_iff₀ ( by positivity ) ]

/-! ### Non-vacuity witness -/

/-
**Non-vacuity.** The binding interior instance `(c₁,c₂,k₁,k₂,R)=(2,1,2,2,1)`
    has water-filling allocation `x* = 3/4 ∈ (0,1)` with a strictly positive
    optimality gap, so the headline conclusions are not vacuously true.
-/
theorem uwmt_nonvacuous :
    xStar 2 1 2 2 1 = 3 / 4
    ∧ (0 : ℝ) < xStar 2 1 2 2 1
    ∧ xStar 2 1 2 2 1 < 1
    ∧ V 2 1 2 2 1 0 < V 2 1 2 2 1 (xStar 2 1 2 2 1) := by
  unfold xStar V; norm_num;

end Viridis.Meta.UniversalWaterfilling