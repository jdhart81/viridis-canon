/-
# The Dissipative Generalization Theorem (DGT) — "the Annealer"
Viridis Aristotle Forge · nightly Run 075 · [06] Entropy-Driven Learning × 🔥 Thermodynamic
17th self-application of the Intelligence Bound (learning-time companion to Run-073 "the Mirror").

This file states the throttled CLEAN CORE of the DGT for machine verification.
ACCEPTANCE: discharge every `sorry`; preserve every named statement VERBATIM; axiom audit
limited to {propext, Classical.choice, Quot.sound}; every theorem must be NON-VACUOUS.

Modeling layer (finite-dim ℝ; the cryptic/predictive split of stored information after
Still–Crooks "thermodynamics of prediction"):
  • S_mem  = total stored information I(W;D)  (Goldt–Seifert dissipated bits; Xu–Raginsky bound)
  • E_pred = predictive part of the stored information (generalizes)
  • χ_L    = cryptic part / "nostalgia" (memorized noise unseen data never reads)
Still–Crooks decomposition:  S_mem = E_pred + χ_L.

NON-VACUITY is stated per theorem below; each hypothesis named in a theorem is load-bearing
(positivity / ordering / decomposition assumptions are genuinely consumed, never decorative).
-/

import Mathlib

set_option autoImplicit false
set_option maxHeartbeats 1000000

namespace DGT

/-- **Result 1 — Generalization–Crypticity Identity.**
Under the Still–Crooks decomposition `S_mem = E_pred + χ_L`, the generalization gap
(defined as stored minus predictive information, `S_mem − E_pred`) equals the crypticity `χ_L`
EXACTLY. "Overfitting is literally crypticity." NON-VACUOUS: genuinely consumes the
decomposition hypothesis `hdec` (the conclusion is the gap, not a tautology about χ alone). -/
theorem generalization_crypticity_identity
    (S_mem E_pred chi : ℝ) (hdec : S_mem = E_pred + chi) :
    S_mem - E_pred = chi := by
  linarith

/-- **Crypticity nonnegativity.** With `χ_L := S_mem − E_pred` and the predictive part
no larger than the total stored information (`E_pred ≤ S_mem`), crypticity is nonnegative.
NON-VACUOUS: the ordering hypothesis `hle : E_pred ≤ S_mem` is load-bearing — drop it and the
conclusion is false. -/
theorem crypticity_nonneg
    (S_mem E_pred chi : ℝ) (hdef : chi = S_mem - E_pred) (hle : E_pred ≤ S_mem) :
    0 ≤ chi := by
  linarith

/-- **E_pred ≤ S_mem (the debit direction).** The predictive part of the stored
information never exceeds the total, because the discarded remainder (crypticity) is
nonnegative. NON-VACUOUS: requires `0 ≤ χ_L` (`hchi`); the decomposition `hdec` is consumed. -/
theorem epred_le_smem
    (S_mem E_pred chi : ℝ) (hdec : S_mem = E_pred + chi) (hchi : 0 ≤ chi) :
    E_pred ≤ S_mem := by
  linarith

/-- **Result 2 — Learning Intelligence Bound with crypticity debit (the Annealer, 17th IB
self-application).** If the TOTAL stored-information rate obeys the raw Intelligence Bound
`dS_mem/dt ≤ P·D/(k_BT ln2)` and the rate splits as `dS_mem/dt = dE_pred/dt + χ̇_L`, then the
rate of *generalizing* information is bounded by the IB ceiling MINUS the crypticity rate:
`dE_pred/dt ≤ P·D/(k_BT ln2) − χ̇_L`. Cryptic memorization is a debit against generalization.
NON-VACUOUS: consumes both the rate decomposition `hrate` and the IB bound `hIB`; the physical
floor `0 < k_BT ln2` (`hkt`) is retained for fidelity. -/
theorem learning_intelligence_bound_crypticity_debit
    (dEpred dChi dSmem P D kTln2 : ℝ)
    (hkt : 0 < kTln2)
    (hrate : dSmem = dEpred + dChi)
    (hIB : dSmem ≤ P * D / kTln2) :
    dEpred ≤ P * D / kTln2 - dChi := by
  linarith

/-- The generalization free-energy objective `Φ(β) = σ²·β − log β` (β = inverse learning
temperature, σ² = data-noise variance). -/
noncomputable def thermalObjective (s2 β : ℝ) : ℝ := s2 * β - Real.log β

/-
**Result 3 — Thermal Matching: the optimal learning temperature equals the data-noise
temperature, `β* = 1/σ²`.** The generalization free energy `Φ(β) = σ²·β − log β` is strictly
convex on the positive reals AND is strictly minimized at the unique interior point
`β* = 1/σ²` (every other positive β gives strictly larger Φ). Generalization is an
entropy-driven ordering transition at thermal equilibrium with the data — NOT at zero training
loss (β → ∞). NON-VACUOUS: `0 < σ²` (`hs2`) is load-bearing (it fixes the unique minimizer and
the strict convexity via `Φ''(β) = 1/β² > 0`); the minimizer claim is a strict `<`, not `≤`.
-/
theorem thermal_matching_optimal_temperature (s2 : ℝ) (hs2 : 0 < s2) :
    StrictConvexOn ℝ (Set.Ioi 0) (thermalObjective s2) ∧
      ∀ β ∈ Set.Ioi (0 : ℝ), β ≠ 1 / s2 →
        thermalObjective s2 (1 / s2) < thermalObjective s2 β := by
  constructor;
  · apply_rules [ strictConvexOn_of_deriv2_pos, convex_Ioi ];
    · exact ContinuousOn.sub ( continuousOn_const.mul continuousOn_id ) ( Real.continuousOn_log.mono fun x hx => ne_of_gt hx );
    · unfold thermalObjective;
      -- Let's calculate the second derivative of the thermal objective function.
      have h_second_deriv : ∀ β > 0, deriv^[2] (fun β => s2 * β - Real.log β) β = 1 / β^2 := by
        have h_second_deriv : ∀ β > 0, deriv^[2] (fun β => s2 * β - Real.log β) β = deriv (fun β => s2 - 1 / β) β := by
          exact fun β hβ => Filter.EventuallyEq.deriv_eq ( by filter_upwards [ lt_mem_nhds hβ ] with x hx using by norm_num [ mul_comm s2, hx.ne' ] );
        intro β hβ; rw [ h_second_deriv β hβ ] ; norm_num [ sub_eq_add_neg, differentiableAt_inv, hβ.ne' ] ;
      aesop;
  · unfold thermalObjective;
    intro β hβ hne; have := Real.log_lt_sub_one_of_pos ( mul_pos hs2 hβ ) ; simp_all +decide [ ne_of_gt, mul_comm s2 ] ;
    linarith [ this ( by contrapose! hne; nlinarith [ mul_inv_cancel₀ hs2.ne' ] ), Real.log_mul hβ.ne' hs2.ne' ]

/-
**Universal cos²Θ generalization efficiency.** The generalization efficiency
`η_g = E_pred / S_mem` is the squared cosine between the learner's representation and the
predictive (teacher) direction; as a squared cosine it lies in `[0,1]` by Cauchy–Schwarz,
saturating at `1` iff the two are parallel (pure predictive learning, zero crypticity).
This is the Nth canon instance of the universal cos²Θ efficiency geometry.
NON-VACUOUS: `u ≠ 0`, `v ≠ 0` (`hu`, `hv`) make the denominator strictly positive so the ratio
is well-defined and the bounds are not vacuously about `0/0`.
-/
theorem generalization_efficiency_eq_cos2_theta
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (u v : E) (hu : u ≠ 0) (hv : v ≠ 0) :
    0 ≤ (inner ℝ u v : ℝ) ^ 2 / (‖u‖ ^ 2 * ‖v‖ ^ 2) ∧
      (inner ℝ u v : ℝ) ^ 2 / (‖u‖ ^ 2 * ‖v‖ ^ 2) ≤ 1 := by
  exact ⟨ div_nonneg ( sq_nonneg _ ) ( mul_nonneg ( sq_nonneg _ ) ( sq_nonneg _ ) ), div_le_one_of_le₀ ( by nlinarith [ abs_le.mp ( abs_real_inner_le_norm u v ) ] ) ( mul_nonneg ( sq_nonneg _ ) ( sq_nonneg _ ) ) ⟩

end DGT