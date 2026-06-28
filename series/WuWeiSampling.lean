import Mathlib

set_option autoImplicit false

/-
===============================================================================
  The Wu-Wei Sampling Theorem (WWST) — "the Listener" — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
===============================================================================

CONTEXT (nightly Run 078, wu-wei-sampling-theorem; [10] Monitoring Technology ×
☯️ Alignment; 20th IB self-application; temporal dual of MWT-069 the Surveyor).

  Monitoring has priced *where* (MWT, space) and *how-gently* (MIST, rate) to
  look, but never *when*.  A fixed CLOCK schedule (Riemann sampling) is the
  purest act of forcing: a uniform human time-grid imposed on a world whose
  information arrives in BURSTS.  The wu-wei alternative is EVENT-TRIGGERED
  (send-on-delta / Lebesgue) sampling: look only when the state has actually
  moved by a set increment Δ.

  Brownian baseline.  For a Wiener process with diffusion σ², the time-averaged
  zero-order-hold estimation-error variances are, at mean inter-sample interval:
      • CLOCK (periodic, interval T):           V_clock = σ²·T / 2
      • EVENT (send-on-delta, threshold Δ):     V_event = Δ² / 6
  where V_event is the Dynkin first-passage time-average
      V_event = E[∫₀^τ X² ds] / E[τ] = (Δ⁴/(6σ²)) / (Δ²/σ²) = Δ²/6,
  with E[τ] = Δ²/σ² the mean exit time of (−Δ,Δ) and the time-integrated square
  error g(x) = (Δ⁴ − x⁴)/(6σ²) the solution of the Dynkin BVP
      (σ²/2)·g''(x) = −x²,   g(±Δ) = 0      (this is what *derives* the 1/6).

CLEAN-CORE ENCODING (this file — must compile with 0 `sorry`, axioms ⊆ Mathlib).

  R1  `dynkin_solution`                          — g solves the Dynkin BVP and
        vanishes on the boundary (the genuine origin of the constant 6).
  R1  `event_variance_eq_first_passage_time_average` — V_event = g(0)/E[τ],
        i.e. the 1/6 is the time-average, not an assumption (σ,Δ > 0 load-bearing).
  R1  `wu_wei_sampling_law_factor_three`          — at EQUAL average sampling rate
        (Δ² = σ²·T, i.e. E[τ] = T):  V_clock = 3 · V_event.  The exact factor of
        three.  hrate is load-bearing (drop it and the identity is false).
  R1  `event_dominates_clock_at_equal_rate`       — strict: V_event < V_clock at
        equal rate (event-triggering is never worse, here strictly better).
  R6  `wu_wei_threshold_floor`                    — the trigger cost
        C(Δ) = a·Δ² + b/Δ² (over-monitoring b/Δ² vs illegibility a·Δ², a,b>0)
        obeys the AM–GM floor  2√(ab) ≤ C(Δ).
  R6  `wu_wei_threshold_optimum`                  — the floor is attained at the
        interior wu-wei threshold Δ* = (b/a)^{1/4}:  C(Δ*) = 2√(ab).
  R6  `wu_wei_threshold_unique_minimizer`         — and ONLY there:
        C(Δ) = 2√(ab) ⇒ Δ = Δ*  (AM–GM tightness; Δ* is the unique minimizer).
  R5  `monitoring_efficiency_le_one`              — Cauchy–Schwarz: the alignment
        efficiency ⟪effort,info⟫²/(‖effort‖²‖info‖²) is ≤ 1.
  R5  `monitoring_efficiency_eq_cos2_theta`       — that efficiency EQUALS cos²Θ,
        Θ the angle between sampling effort and information generation
        (effort, info ≠ 0 load-bearing).
  R5  `forcing_debt_eq_sin2_theta`               — the complementary forcing debt
        1 − efficiency = sin²Θ.

  Deferred to later runs / human review (NOT in this file): KKT broadcast-price
  equimarginality `broadcast_attention_price_temporal_waterfilling`,
  `attention_allocation_equimarginal` (constrained-opt machinery — gate, per the
  MWT precedent); `listener_IB_ceiling` (IB aggregation); model-dependent
  `forcing_penalty_increases_with_burstiness` (R2 regime-switch monotonicity) and
  `redundant_samples_are_nonpredictive_crypticity` (R3 68% nostalgia fraction).
-/

namespace Viridis.Monitoring.WuWeiSampling

open Real
open scoped RealInnerProductSpace

/-- CLOCK (periodic / Riemann) time-averaged estimation-error variance of a
Wiener process with diffusion `σ²` at mean inter-sample interval `T`:  σ²·T/2. -/
noncomputable def Vclock (σ T : ℝ) : ℝ := σ ^ 2 * T / 2

/-- EVENT-triggered (send-on-delta / Lebesgue) time-averaged estimation-error
variance at trigger threshold `Δ`:  Δ²/6. -/
noncomputable def Vevent (Δ : ℝ) : ℝ := Δ ^ 2 / 6

/-- Dynkin time-integrated square error `g(x) = (Δ⁴ − x⁴)/(6σ²)` for Brownian
motion exiting `(−Δ, Δ)`. -/
noncomputable def gD (σ Δ x : ℝ) : ℝ := (Δ ^ 4 - x ^ 4) / (6 * σ ^ 2)

/-- Mean first-passage (exit) time of the Wiener process to `±Δ` (Dynkin):
`E[τ] = Δ²/σ²`. -/
noncomputable def Etau (σ Δ : ℝ) : ℝ := Δ ^ 2 / σ ^ 2

/-- Trigger-design cost: over-monitoring `b/Δ²` plus illegibility `a·Δ²`. -/
noncomputable def Cost (a b Δ : ℝ) : ℝ := a * Δ ^ 2 + b / Δ ^ 2

/-- The wu-wei threshold `Δ* = (b/a)^{1/4} = √(√(b/a))`. -/
noncomputable def Dstar (a b : ℝ) : ℝ := Real.sqrt (Real.sqrt (b / a))

/-
**R1 (Dynkin BVP).** The time-integrated square error `g` solves the
stationary Dynkin equation `(σ²/2)·g'' = −x²` and vanishes on the boundary
`g(±Δ) = 0`.  This BVP is what *derives* the constant `6` in `V_event`.
-/
theorem dynkin_solution (σ Δ : ℝ) (hσ : 0 < σ) :
    (∀ x : ℝ, (σ ^ 2 / 2) * deriv (deriv (fun y => gD σ Δ y)) x = - x ^ 2)
      ∧ gD σ Δ Δ = 0 ∧ gD σ Δ (-Δ) = 0 := by
  unfold gD; norm_num; ring_nf; norm_num [ hσ.ne' ] ;
  exact fun x => by nlinarith [ mul_inv_cancel_left₀ ( pow_ne_zero 2 hσ.ne' ) ( x ^ 2 ) ] ;

/-
**R1 (first-passage time-average).** `V_event = g(0) / E[τ]`: the `1/6` is the
Dynkin time-average of the square error, not an assumed constant.
-/
theorem event_variance_eq_first_passage_time_average (σ Δ : ℝ)
    (hσ : 0 < σ) (hΔ : 0 < Δ) :
    Vevent Δ = gD σ Δ 0 / Etau σ Δ := by
  unfold Vevent gD Etau; ring_nf; norm_num [ hσ.ne', hΔ.ne' ] ;
  field_simp

/-
**R1 — Wu-Wei Sampling Law (factor three).** At equal average sampling rate
(`Δ² = σ²·T`, i.e. the event mean interval equals the clock interval `T`),
clock monitoring carries exactly three times the error of event-triggered
monitoring:  `V_clock = 3 · V_event`.  `hrate` is load-bearing.
-/
theorem wu_wei_sampling_law_factor_three (σ T Δ : ℝ)
    (hσ : 0 < σ) (hT : 0 < T) (hΔ : 0 < Δ) (hrate : Δ ^ 2 = σ ^ 2 * T) :
    Vclock σ T = 3 * Vevent Δ := by
  unfold Vclock Vevent;
  grind

/-
**R1 (strict domination).** At equal average rate, event-triggered sampling
strictly dominates clock sampling:  `V_event < V_clock`.
-/
theorem event_dominates_clock_at_equal_rate (σ T Δ : ℝ)
    (hσ : 0 < σ) (hT : 0 < T) (hΔ : 0 < Δ) (hrate : Δ ^ 2 = σ ^ 2 * T) :
    Vevent Δ < Vclock σ T := by
  convert wu_wei_sampling_law_factor_three σ T Δ hσ hT hΔ hrate ▸ lt_mul_of_one_lt_left _ _ using 1 <;> norm_num [ Vclock, Vevent ] ; nlinarith [ mul_pos hσ hT ] ;

/-
**R6 (AM–GM floor).** The trigger cost is bounded below by `2√(ab)`.
-/
theorem wu_wei_threshold_floor (a b Δ : ℝ)
    (ha : 0 < a) (hb : 0 < b) (hΔ : 0 < Δ) :
    2 * Real.sqrt (a * b) ≤ Cost a b Δ := by
  unfold Cost;
  rw [ add_div', le_div_iff₀ ] <;> try positivity;
  nlinarith [ sq_nonneg ( a * Δ ^ 2 - Real.sqrt ( a * b ) ), Real.mul_self_sqrt ( mul_nonneg ha.le hb.le ) ]

/-
**R6 (interior optimum).** The floor `2√(ab)` is attained at the wu-wei
threshold `Δ* = (b/a)^{1/4}`.
-/
theorem wu_wei_threshold_optimum (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    Cost a b (Dstar a b) = 2 * Real.sqrt (a * b) := by
  unfold Cost Dstar;
  rw [ Real.sq_sqrt ( by positivity ), Real.sqrt_div ( by positivity ) ];
  field_simp;
  rw [ Real.sqrt_mul ] <;> nlinarith [ Real.mul_self_sqrt ha.le, Real.mul_self_sqrt hb.le ]

/-
**R6 (unique minimizer).** The cost attains its floor only at `Δ*`:
`C(Δ) = 2√(ab) ⇒ Δ = Δ*`.
-/
theorem wu_wei_threshold_unique_minimizer (a b Δ : ℝ)
    (ha : 0 < a) (hb : 0 < b) (hΔ : 0 < Δ)
    (hmin : Cost a b Δ = 2 * Real.sqrt (a * b)) :
    Δ = Dstar a b := by
  unfold Cost Dstar at *;
  field_simp at hmin;
  rw [ eq_comm, Real.sqrt_eq_iff_mul_self_eq ];
  · rw [ Real.sqrt_eq_iff_mul_self_eq ] <;> try positivity;
    rw [ div_eq_iff ] <;> nlinarith [ show 0 < Δ ^ 2 * Real.sqrt ( a * b ) by positivity, Real.mul_self_sqrt ( show 0 ≤ a * b by positivity ) ];
  · positivity;
  · positivity

/-
**R5 (Cauchy–Schwarz / efficiency ≤ 1).** The squared alignment between
sampling effort and information generation is bounded by the product of norms.
-/
theorem monitoring_efficiency_le_one {V : Type*}
    [NormedAddCommGroup V] [InnerProductSpace ℝ V] (u v : V) :
    ⟪u, v⟫ ^ 2 ≤ ‖u‖ ^ 2 * ‖v‖ ^ 2 := by
  nlinarith [ abs_le.mp ( abs_real_inner_le_norm u v ) ]

/-
**R5 — efficiency = cos²Θ.** Monitoring efficiency, the squared cosine of the
angle `Θ` between sampling effort `u` and information generation `v`.
-/
theorem monitoring_efficiency_eq_cos2_theta {V : Type*}
    [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (u v : V) (hu : u ≠ 0) (hv : v ≠ 0) :
    ⟪u, v⟫ ^ 2 / (‖u‖ ^ 2 * ‖v‖ ^ 2)
      = Real.cos (InnerProductGeometry.angle u v) ^ 2 := by
  rw [ InnerProductGeometry.cos_angle ] ; ring

/-
**R5 — forcing debt = sin²Θ.** The complementary forcing debt is the squared
sine of the same angle:  `1 − efficiency = sin²Θ`.
-/
theorem forcing_debt_eq_sin2_theta {V : Type*}
    [NormedAddCommGroup V] [InnerProductSpace ℝ V]
    (u v : V) (hu : u ≠ 0) (hv : v ≠ 0) :
    1 - ⟪u, v⟫ ^ 2 / (‖u‖ ^ 2 * ‖v‖ ^ 2)
      = Real.sin (InnerProductGeometry.angle u v) ^ 2 := by
  rw [ Real.sin_sq, InnerProductGeometry.cos_angle ];
  ring

end Viridis.Monitoring.WuWeiSampling