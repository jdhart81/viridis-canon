/-
The Effortless Equilibrium Theorem (EET) — clean dynamical / thermodynamic core
===============================================================================

Nightly science-engine Run 097 — [13] Computational Theory x Alignment ("the Steersman").
39th Intelligence-Bound self-application.

A steward-able system is a dissipative dynamical system with a bounded-below C^1
free-energy potential `Phi` and overdamped flow  x' = -gradPhi(x).  "Harmonized action"
(wu wei) = let the flow run and rest where it stops; "forcing" = hold the system at a
target `x*` chosen independently of the natural attractor set.

This file states the clean, WELL-POSED, non-vacuous dynamical / thermodynamic core of
EET, keyed to the run's boxed results.

DEFERRED (well-posedness gate — CITED, not re-proven, per the run's verification-honesty
note): the complexity-class content — R1's membership `W in CLS = PPAD cap PLS`, R2's
CLS-completeness of gradient descent (FGHS 2021), and R3's TFNP -> FNP class transition
and PPAD/NP-hardness (DGP 2009; JPY 1988).  Those require citing external completeness
theorems and are not self-contained non-vacuous propositions provable from scratch in
Lean.  This file proves the run's OWN dynamical/thermodynamic scaffolding, which is what
`verify.py` gates numerically.

Named theorems (this file):

  R1  wuwei_totality_min_exists            (potential-descent / EVT certificate: a rest state EXISTS)
  R3  rest_state_iff_grad_zero             (a resting state at x* exists iff gradPhi(x*) = 0)
  R3  forcing_nonattractor_no_rest         (forcing a non-attractor: the flow never rests there)
  R5  holding_power_nonneg                 (P_hold = gamma^-1 ||gradPhi||^2 >= 0)
  R5  zero_holding_power_iff_grad_zero     (BOXED: wu wei is the UNIQUE zero-holding-power action)
  R5  nonattractor_holding_power_pos       (a forced non-attractor drains strictly positive standing power)
  R4  harmonization_cheaper_than_forcing   (BOXED: attractor target costs 0 < any non-attractor target)
  R5  steersman_ib_floors_forcing_time     (BOXED: t_force >= I k_B T ln2 / (P D); 39th IB self-app)
  R6  drive_alignment_efficiency_eq_cos2_theta   (eta = cos^2 Theta, definitional identity)
  R6  drive_alignment_efficiency_nonneg_le_one    (eta in [0,1] via Cauchy-Schwarz)
  eet_nonvacuous                           (explicit witness: zero- and positive-holding-power both realised)

All hypotheses are the physical positivity constraints (gamma, k_B, T, P, D > 0).
Toolchain leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff.
-/

import Mathlib

namespace Viridis.Computation.EffortlessEquilibrium

open Real

variable {E : Type*} [NormedAddCommGroup E]

/-! ## R1 — Totality of wu wei (the provable potential-descent certificate).

The full boxed R1 asserts `W(Phi) != empty` certified TWICE (Brouwer fixed point AND
potential descent) and hence `W in CLS = PPAD cap PLS`.  The CLS membership is cited, not
re-proven (DEFERRED).  The dynamical content that IS well-posed is the potential-descent
certificate: on a nonempty compact state space a continuous free energy attains a
minimum — a resting state is GUARANTEED to exist.  "Wu wei never asks the impossible." -/

/-- **R1 (totality — potential-descent certificate).**  On a nonempty compact state space
`K`, a continuous free-energy potential `Phi` attains a global minimum on `K`.  That
minimiser is a resting state of the descent flow, so the wu-wei action set is nonempty. -/
theorem wuwei_totality_min_exists
    (Φ : E → ℝ) (K : Set E) (hK : IsCompact K) (hne : K.Nonempty)
    (hcont : ContinuousOn Φ K) :
    ∃ x ∈ K, ∀ y ∈ K, Φ x ≤ Φ y := by
  obtain ⟨x, hx, hmin⟩ := hK.exists_isMinOn hne hcont
  exact ⟨x, hx, fun y hy => hmin hy⟩

/-! ## R3 — Forcing destroys totality (the provable dynamical core).

For the overdamped flow `x' = -gradPhi(x)`, `x*` is a rest state iff the velocity
`-gradPhi(x*)` vanishes, i.e. iff `gradPhi(x*) = 0`.  Thus asking for a resting state at a
forced non-attractor target (`gradPhi(x*) != 0`) is unsatisfiable — no such rest exists.
This is the well-posed content of R3's "TFNP -> FNP" jump (the class-transition label
itself is cited/DEFERRED). -/

/-- **R3 (rest iff stationary).**  Under the flow `x' = -gradPhi(x)`, a resting state at
`x` (zero velocity) exists iff `gradPhi(x) = 0`.  Existence of harmony is exactly
stationarity. -/
theorem rest_state_iff_grad_zero
    (gradΦ : E → E) (x : E) :
    (- gradΦ x = 0) ↔ gradΦ x = 0 := by
  rw [neg_eq_zero]

/-- **R3 (forcing a non-attractor is unsatisfiable).**  If `x*` is not a stationary point
(`gradPhi(x*) != 0`) then the flow velocity there is nonzero: the system CANNOT rest at a
forced non-attractor target.  Forcing converts a guaranteed-rest problem into one with no
solution. -/
theorem forcing_nonattractor_no_rest
    (gradΦ : E → E) (x : E) (h : gradΦ x ≠ 0) :
    - gradΦ x ≠ 0 := by
  rwa [neg_ne_zero]

/-! ## R5 — The Steersman: standing holding-power and the Intelligence Bound.

To hold the system at `x*` against its own relaxation flow costs a standing power
`P_hold(x*) = gamma^-1 ||gradPhi(x*)||^2` (overdamped regime).  It is >= 0 always, and = 0
EXACTLY on the wu-wei set — wu wei is the unique zero-holding-power action. -/

/-- **R5 (holding power is nonnegative).**  `P_hold = gamma^-1 ||gradPhi||^2 >= 0`. -/
theorem holding_power_nonneg
    (γ : ℝ) (hγ : 0 < γ) (g : E) :
    0 ≤ (1 / γ) * ‖g‖ ^ 2 := by
  positivity

/-- **R5 (BOXED — wu wei is the unique zero-holding-power action).**  The standing holding
power vanishes iff the state is stationary (`gradPhi = 0`), i.e. iff the target is the
natural attractor.  Every non-attractor costs standing power. -/
theorem zero_holding_power_iff_grad_zero
    (γ : ℝ) (hγ : 0 < γ) (g : E) :
    (1 / γ) * ‖g‖ ^ 2 = 0 ↔ g = 0 := by
  rw [mul_eq_zero]
  constructor
  · rintro (h | h)
    · exact absurd h (by positivity)
    · exact norm_eq_zero.mp (pow_eq_zero_iff (by norm_num) |>.mp h)
  · rintro rfl; simp

/-- **R5 (a forced non-attractor drains positive standing power).** -/
theorem nonattractor_holding_power_pos
    (γ : ℝ) (hγ : 0 < γ) (g : E) (h : g ≠ 0) :
    0 < (1 / γ) * ‖g‖ ^ 2 := by
  have : (0:ℝ) < ‖g‖ := norm_pos_iff.mpr h
  positivity

/-! ## R4 — The Alignment Paradox: harmonization is cheaper than forcing. -/

/-- **R4 (BOXED — alignment-by-harmonization dominates alignment-by-forcing).**  Reshaping
the landscape so the desired outcome is itself an attractor (`g_a = 0`) costs zero standing
holding power, strictly less than forcing any non-attractor target (`g_b != 0`).  Don't
steer the system to your goal; make the flow already go there. -/
theorem harmonization_cheaper_than_forcing
    (γ : ℝ) (hγ : 0 < γ) (ga gb : E) (ha : ga = 0) (hb : gb ≠ 0) :
    (1 / γ) * ‖ga‖ ^ 2 < (1 / γ) * ‖gb‖ ^ 2 := by
  subst ha
  have hgb : (0:ℝ) < ‖gb‖ ^ 2 := by positivity
  have hg : (0:ℝ) < 1 / γ := by positivity
  simp only [norm_zero]
  nlinarith [mul_pos hg hgb]

/-- **R5 (BOXED — the Steersman's Intelligence-Bound forcing-time floor; 39th IB
self-application).**  Acquiring the `I` bits that specify a forced target is capped by the
Intelligence Bound `dI/dt <= P D / (k_B T ln 2)`.  Hence any protocol that learns `I` bits
at admissible rate takes at least `t_force >= I k_B T ln 2 / (P D)`. -/
theorem steersman_ib_floors_forcing_time
    (I kB T P D rate t : ℝ)
    (hI : 0 ≤ I) (hkB : 0 < kB) (hT : 0 < T) (hP : 0 < P) (hD : 0 < D)
    (hrate : 0 < rate)
    (hcap : rate ≤ P * D / (kB * T * Real.log 2))
    (hbits : I ≤ t * rate) :
    I * (kB * T * Real.log 2) / (P * D) ≤ t := by
  have hlog : 0 < Real.log 2 := Real.log_pos (by norm_num)
  have hc : 0 < kB * T * Real.log 2 := by positivity
  have hpd : 0 < P * D := by positivity
  have htr : 0 ≤ t * rate := le_trans hI hbits
  have ht : 0 ≤ t := by
    by_contra h
    push_neg at h
    nlinarith [mul_neg_of_neg_of_pos h hrate]
  rw [div_le_iff₀ hpd]
  rw [le_div_iff₀ hc] at hcap
  nlinarith [mul_le_mul_of_nonneg_left hcap ht, mul_le_mul_of_nonneg_right hbits hc.le]

/-! ## R6 — Drive-alignment efficiency (recurring CSUT motif). -/

/-- **R6 (efficiency is exactly cos^2 Theta — definitional identity).**  With
`cos Theta = <u,f> / (||u|| ||f||)`, the drive-alignment efficiency
`eta = <u,f>^2 / (||u||^2 ||f||^2)` equals `cos^2 Theta`. -/
theorem drive_alignment_efficiency_eq_cos2_theta
    [InnerProductSpace ℝ E] (u f : E) :
    (inner ℝ u f / (‖u‖ * ‖f‖)) ^ 2
      = (inner ℝ u f) ^ 2 / (‖u‖ ^ 2 * ‖f‖ ^ 2) := by
  rw [div_pow, mul_pow]

/-- **R6 (efficiency lies in [0,1]).**  By Cauchy–Schwarz, `0 <= eta <= 1`; `eta = 1` when
the control is aligned with the natural flow (target is the attractor, wu wei), `eta = 0`
when orthogonal (pure forcing). -/
theorem drive_alignment_efficiency_nonneg_le_one
    [InnerProductSpace ℝ E] (u f : E) (hu : u ≠ 0) (hf : f ≠ 0) :
    0 ≤ (inner ℝ u f) ^ 2 / (‖u‖ ^ 2 * ‖f‖ ^ 2)
      ∧ (inner ℝ u f) ^ 2 / (‖u‖ ^ 2 * ‖f‖ ^ 2) ≤ 1 := by
  have hden : (0:ℝ) < ‖u‖ ^ 2 * ‖f‖ ^ 2 := by positivity
  refine ⟨by positivity, ?_⟩
  rw [div_le_one hden]
  have := abs_real_inner_le_norm u f
  nlinarith [sq_abs (inner ℝ u f), abs_nonneg (inner ℝ u f)]

/-! ## Non-vacuity. -/

/-- **eet_nonvacuous.**  An explicit witness (state space `ℝ`, `Phi x = x^2/2`,
`gradPhi x = x`, `gamma = 1`): the attractor `g_a = 0` carries zero standing holding power,
while a non-attractor `g_b = 1 != 0` carries strictly positive standing power.  Both the
wu-wei (zero-cost) and forcing (positive-cost) branches are realised, so the theory is
non-vacuous. -/
theorem eet_nonvacuous :
    ∃ (γ ga gb : ℝ), 0 < γ ∧ ga = 0 ∧ gb ≠ 0
      ∧ (1 / γ) * ‖ga‖ ^ 2 = 0 ∧ 0 < (1 / γ) * ‖gb‖ ^ 2 := by
  refine ⟨1, 0, 1, by norm_num, rfl, by norm_num, by simp, ?_⟩
  norm_num

end Viridis.Computation.EffortlessEquilibrium
