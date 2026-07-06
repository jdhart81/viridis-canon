/-
  StewardshipRevisit.lean — The Stewardship Revisit Theorem (SRT), "the Tender"
  Viridis Nightly Science Engine, Run 087 — [04] D-Score Science × 🎯 Stewardship.

  The temporal completion of the monitoring calculus: when should a steward
  re-observe a *drifting* ecosystem?  Site i's true certified slack drifts as an
  Ornstein–Uhlenbeck process; a D-Score certificate pins the estimate, after which
  the steward's conditional uncertainty grows as
        V(t) = (s^2 / (2θ)) · (1 − e^{−2θ t}),   V∞ = s^2/(2θ).

  This file states the CLEAN, WELL-POSED, NON-VACUOUS core of SRT as deterministic
  claims about the conditional-variance curve V, the amortized renewal cost rate,
  and the Whittle scheduling index.  Each theorem below has a genuinely non-trivial
  conclusion (see `srt_nonvacuous` for a concrete binding instance):

    1. certificate_halflife_eq_ln2_over_2theta
         at t½ = ln2/(2θ) the conditional variance is exactly half its stationary
         value.  Cadence tracks turnover θ, not the calendar.
    2. ou_conditional_variance_growth_monotone
         V is strictly increasing in age (a certificate is a decaying asset).
    3. sqrt_cadence_minimizes_amortized_cost
         in the diffusion regime the amortized cost rate
         C(τ) = c/τ + ½ κ s² τ is globally minimized at τ* = √(2c/(κ s²)) (EOQ/AM–GM).
    4. whittle_index_form_eq_stakes_times_variance_rate
         the scheduling index W(t) = κ·V(t) (the accrued staleness-penalty rate)
         equals stakes × conditional variance and is strictly increasing in age
         (indexability of the restless bandit).
    5. broadcast_clock_price_equalizes_marginal_penalty
         a single broadcast monitoring-clock price ν ∈ (0, κV∞) sets a UNIQUE
         service time at which each site's index reaches ν — one number equalizes
         the marginal staleness penalty across the portfolio (temporal water level).

  NON-VACUITY: `srt_nonvacuous` exhibits θ=s=κ=1, c=1, ν=1/4 for which τ*=√2>0,
  V∞=1/2, and the broadcast band (0,1/2) is nonempty and contains ν — so every
  hypothesis is jointly satisfiable and every conclusion is a strict statement.
-/
import Mathlib

namespace Viridis.Monitoring.StewardshipRevisit

open Real

/-- OU conditional variance of the certified slack, `t` after the last observation. -/
noncomputable def V (s θ t : ℝ) : ℝ := (s ^ 2 / (2 * θ)) * (1 - Real.exp (-(2 * θ * t)))

/-- Stationary conditional variance `V∞ = s²/(2θ)`. -/
noncomputable def Vinf (s θ : ℝ) : ℝ := s ^ 2 / (2 * θ)

/-- Certificate half-life `t½ = ln2/(2θ)`. -/
noncomputable def thalf (θ : ℝ) : ℝ := Real.log 2 / (2 * θ)

/-- Diffusion-regime amortized renewal cost rate `C(τ) = c/τ + ½ κ s² τ`. -/
noncomputable def C (c κ s τ : ℝ) : ℝ := c / τ + (1 / 2) * κ * s ^ 2 * τ

/-- Square-root cadence `τ* = √(2c/(κ s²))`. -/
noncomputable def taustar (c κ s : ℝ) : ℝ := Real.sqrt (2 * c / (κ * s ^ 2))

/-- Whittle scheduling index `W(t) = κ·V(t)`, the accrued staleness-penalty rate. -/
noncomputable def W (κ s θ t : ℝ) : ℝ := κ * V s θ t

/-
**Result 1 — Certificate half-life.** At `t½ = ln2/(2θ)` the conditional
    variance equals exactly half the stationary value `V∞`.
-/
theorem certificate_halflife_eq_ln2_over_2theta (s θ : ℝ) (hθ : 0 < θ) :
    V s θ (thalf θ) = (1 / 2) * Vinf s θ := by
  unfold V Vinf thalf; ring_nf; norm_num [ hθ.ne' ] ;
  norm_num [ Real.exp_neg, Real.exp_log ] ; ring

/-
**Result 2 — Certificate decay.** The OU conditional variance is strictly
    increasing in age: a past observation certifies strictly less as time passes.
-/
theorem ou_conditional_variance_growth_monotone (s θ : ℝ) (hs : 0 < s) (hθ : 0 < θ) :
    StrictMono (fun t => V s θ t) := by
  refine' fun a b hab => mul_lt_mul_of_pos_left ( sub_lt_sub_left ( Real.exp_lt_exp.mpr ( neg_lt_neg <| mul_lt_mul_of_pos_left hab <| by positivity ) ) _ ) ( by positivity )

/-
**Result 2b — Non-negativity/positivity of accrued variance** (auxiliary,
    strengthens non-vacuity of the index band).
-/
theorem ou_variance_pos_of_pos_age (s θ t : ℝ) (hs : 0 < s) (hθ : 0 < θ) (ht : 0 < t) :
    0 < V s θ t := by
  exact mul_pos ( by positivity ) ( by exact sub_pos.mpr ( Real.exp_lt_one_iff.mpr ( by nlinarith ) ) )

/-
**Result 3 — The square-root cadence law.** In the diffusion regime the
    amortized cost rate `C(τ) = c/τ + ½ κ s² τ` is globally minimized over positive
    revisit intervals at `τ* = √(2c/(κ s²))` (EOQ / AM–GM stationary point).
-/
theorem sqrt_cadence_minimizes_amortized_cost
    (c κ s : ℝ) (hc : 0 < c) (hκ : 0 < κ) (hs : 0 < s) :
    ∀ τ : ℝ, 0 < τ → C c κ s (taustar c κ s) ≤ C c κ s τ := by
  unfold C taustar;
  intro τ hτ;
  field_simp;
  rw [ Real.sq_sqrt ( by positivity ) ];
  rw [ mul_div_cancel₀ _ ( by positivity ) ];
  -- Squaring both sides to remove the square root.
  suffices h_sq : (c * 2 + c * 2) ^ 2 * τ ^ 2 ≤ (c * 2 / (κ * s ^ 2)) * (c * 2 + κ * s ^ 2 * τ ^ 2) ^ 2 by
    nlinarith [ show 0 ≤ Real.sqrt ( c * 2 / ( κ * s ^ 2 ) ) * ( c * 2 + κ * s ^ 2 * τ ^ 2 ) by positivity, Real.mul_self_sqrt ( show 0 ≤ c * 2 / ( κ * s ^ 2 ) by positivity ) ];
  rw [ div_mul_eq_mul_div, le_div_iff₀ ] <;> nlinarith [ sq_nonneg ( c * 2 - κ * s ^ 2 * τ ^ 2 ), show 0 < κ * s ^ 2 by positivity ]

/-
**Result 3b — The minimized cost value** `C(τ*) = √(2 c κ s²)` (the EOQ value;
    ensures the minimizer is not a trivial/degenerate point).
-/
theorem sqrt_cadence_optimal_value (c κ s : ℝ) (hc : 0 < c) (hκ : 0 < κ) (hs : 0 < s) :
    C c κ s (taustar c κ s) = Real.sqrt (2 * c * κ * s ^ 2) := by
  unfold C taustar; ring_nf
  field_simp
  ring_nf
  rw [ Real.sq_sqrt ( by positivity ) ] ; rw [ ← Real.sqrt_mul <| by positivity ] ; ring_nf; norm_num [ hc.le, hκ.le, hs.le, hc.ne', hκ.ne', hs.ne' ] ; ring_nf;
  field_simp
  ring

/-
**Result 4 — Whittle index form & indexability.** The scheduling index equals
    stakes times the conditional variance, `W(t) = κ·V(t)`, and is strictly
    increasing in age — the restless-bandit arms are indexable.
-/
theorem whittle_index_form_eq_stakes_times_variance_rate
    (κ s θ : ℝ) (hκ : 0 < κ) (hs : 0 < s) (hθ : 0 < θ) :
    (∀ t, W κ s θ t = κ * V s θ t) ∧ StrictMono (fun t => W κ s θ t) := by
  refine' ⟨ fun t => rfl, _ ⟩;
  refine' fun t1 t2 h => mul_lt_mul_of_pos_left _ hκ;
  exact ( ou_conditional_variance_growth_monotone s θ hs hθ ) h

/-
**Result 5 — Broadcast clock price equalizes the marginal penalty.** For a
    single broadcast monitoring-clock price `ν` in the attainable band `(0, κ·V∞)`,
    there is a UNIQUE positive service time at which the site's staleness-penalty
    index reaches `ν`.  One number `ν`, announced to the whole fleet, sets each
    site's threshold — a temporal water level equalizing the marginal penalty.
-/
theorem broadcast_clock_price_equalizes_marginal_penalty
    (κ s θ ν : ℝ) (hκ : 0 < κ) (hs : 0 < s) (hθ : 0 < θ)
    (hν : 0 < ν) (hνmax : ν < κ * Vinf s θ) :
    ∃! τ : ℝ, 0 < τ ∧ W κ s θ τ = ν := by
  obtain ⟨τ, hτ⟩ : ∃ τ : ℝ, 0 < τ ∧ W κ s θ τ = ν := by
    -- By definition of $W$, we know that $W(τ) = κ * V(τ)$.
    unfold W Vinf at *;
    unfold V;
    refine' ⟨ Real.log ( 1 - ν / ( κ * ( s ^ 2 / ( 2 * θ ) ) ) ) / ( - ( 2 * θ ) ), _, _ ⟩ <;> norm_num [ hκ.ne', hs.ne', hθ.ne', hν.ne', hνmax.ne', Real.exp_log, div_neg ];
    · exact div_neg_of_neg_of_pos ( Real.log_neg ( sub_pos.mpr <| by rw [ div_lt_iff₀ <| by positivity ] ; linarith ) <| sub_lt_self _ <| by positivity ) <| by positivity;
    · rw [ mul_div_cancel₀ _ ( by positivity ), Real.exp_log ] <;> nlinarith [ mul_div_cancel₀ ν ( by positivity : ( κ * ( s ^ 2 / ( 2 * θ ) ) ) ≠ 0 ) ];
  exact ⟨ τ, hτ, fun x hx => StrictMono.injective ( show StrictMono ( fun t => W κ s θ t ) from ( whittle_index_form_eq_stakes_times_variance_rate κ s θ hκ hs hθ ) |>.2 ) ( hx.2.trans hτ.2.symm ) ⟩

/-
**Non-vacuity witness.** With `θ = s = κ = 1`, `c = 1`, `ν = 1/4`:
    the square-root cadence is `√2 > 0`, the stationary variance is `1/2`, and the
    broadcast band `(0, 1/2)` is nonempty and contains `ν = 1/4`.  Hence every
    hypothesis of Results 1–5 is jointly satisfiable with strict, non-degenerate
    conclusions.
-/
theorem srt_nonvacuous :
    taustar 1 1 1 = Real.sqrt 2 ∧ 0 < taustar 1 1 1 ∧
      Vinf 1 1 = (1 / 2 : ℝ) ∧ (0 : ℝ) < 1 * Vinf 1 1 ∧
      (1 / 4 : ℝ) < 1 * Vinf 1 1 := by
  unfold taustar Vinf; norm_num;

end Viridis.Monitoring.StewardshipRevisit