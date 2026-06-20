/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Heat and Disorder — Formal Spine of the Popular Narrative
=========================================================

This module condenses the *qualitative* claims of the trade book
"Heat and Disorder: How Thermodynamics Shapes Our Climate's Future" (Hart,
2.0) into a small set of faithful, machine-checkable theorems. The book is
written in prose for a general audience and contains no equations; the goal
here is NOT to prove the book's empirical claims (CO₂ forcing magnitudes,
the Keeling correlation, RCP projections — those are measured, not derived),
but to give the book's CONCEPTUAL backbone a verified mathematical appendix.

Three buckets were triaged from the manuscript:
  A. Formalizable theorems (this file).
  B. Physical postulates (Stefan–Boltzmann law, loop gain, entropy-production
     ≥ 0) — entered here as HYPOTHESES, never assumed derivable.
  C. Empirical/statistical claims — out of scope for a theorem prover.

Book-claim → theorem map (faithfulness, INV1):

  second_law_entropy_nondecreasing
      Preface: "entropy ... increases inexorably"; Ch.2/3: the entropy of an
      isolated system rises over time. Physics supplies the local law
      (production rate σ(t) = dS/dt ≥ 0); the THEOREM derives the global
      consequence — S is monotone non-decreasing on all of time.

  positive_feedback_diverges  /  negative_feedback_stabilizes
      Ch.1 "Feedback Loops": a POSITIVE (self-reinforcing) loop such as
      ice–albedo amplifies a perturbation without bound when the loop gain
      exceeds one; a NEGATIVE loop (gain below one) damps it back to zero.
      Modeled as the discrete orbit xₙ = gⁿ·x₀ of loop gain g.

  tipping_point_threshold  /  saddle_node_two_branches
      Introduction: "tipping points — critical thresholds where small changes
      can trigger large-scale, often irreversible, effects." Minimal
      saddle-node normal form ẋ = r + x²: equilibria are the real roots of
      x² + r = 0. There is a SHARP critical value r_c = 0 — two equilibria
      for r < 0, none for r > 0. Crossing r_c annihilates all equilibria:
      the prototypical tipping point (cf. West Antarctic Ice Sheet, Ch.1).

  energy_balance_unique_equilibrium
      Ch.1 "Basic Principles": "the balance between incoming solar radiation
      and outgoing heat determines the Earth's overall temperature." With
      absorbed flux S > 0 and grey-body emission σT⁴ (σ > 0), there is a
      UNIQUE positive equilibrium temperature.

Lean: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria (Aristotle target):
  • Zero `sorry`; axiom audit limited to {propext, Classical.choice, Quot.sound}.
  • Each theorem's conclusion encodes its claim non-vacuously — hypotheses
    must be able to fail (entropy monotonicity needs σ ≥ 0; feedback
    divergence needs g > 1; the tipping threshold is an iff; the equilibrium
    is unique only for σ, S > 0).

STATUS: PRE-ARISTOTLE DRAFT. Proof bodies are the human draft to be
discharged / repaired by Aristotle (Harmonic). Theorem STATEMENTS are the
contract and must be preserved verbatim.
-/
import Mathlib

set_option autoImplicit false

namespace HeatAndDisorder

open Filter Topology

/-! ### 1. Second law: entropy of an isolated system is non-decreasing.

Physical input (Bucket B), supplied as a hypothesis: the instantaneous
entropy-production rate is non-negative, `0 ≤ deriv S t` for all `t`.
Mathematical output: `S` is monotone — entropy never decreases. -/

theorem second_law_entropy_nondecreasing
    (S : ℝ → ℝ) (hS : Differentiable ℝ S)
    (hprod : ∀ t, 0 ≤ deriv S t) :
    Monotone S :=
  monotone_of_deriv_nonneg hS hprod

/-- Explicit two-time form of the second law: for any earlier time `t₁` and
later time `t₂`, entropy at `t₂` is at least entropy at `t₁`. -/
theorem entropy_never_decreases
    (S : ℝ → ℝ) (hS : Differentiable ℝ S)
    (hprod : ∀ t, 0 ≤ deriv S t) :
    ∀ t₁ t₂ : ℝ, t₁ ≤ t₂ → S t₁ ≤ S t₂ :=
  fun _ _ h => second_law_entropy_nondecreasing S hS hprod h

/-! ### 2. Feedback loops: positive amplifies, negative damps.

Discrete linearized orbit `xₙ = gⁿ · x₀` with loop gain `g`. -/

/-- POSITIVE feedback (`g > 1`): a positive perturbation grows without bound
(ice–albedo runaway). -/
theorem positive_feedback_diverges
    (g x₀ : ℝ) (hg : 1 < g) (hx : 0 < x₀) :
    Tendsto (fun n : ℕ => g ^ n * x₀) atTop atTop :=
  (tendsto_pow_atTop_atTop_of_one_lt hg).atTop_mul_const hx

/-- NEGATIVE feedback (`0 ≤ g < 1`): any perturbation decays back to
equilibrium (the stabilizing loop of Ch.1). -/
theorem negative_feedback_stabilizes
    (g x₀ : ℝ) (hg0 : 0 ≤ g) (hg1 : g < 1) :
    Tendsto (fun n : ℕ => g ^ n * x₀) atTop (𝓝 0) := by
  have h : Tendsto (fun n : ℕ => g ^ n) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one hg0 hg1
  simpa using h.mul_const x₀

/-! ### 3. Tipping points: the saddle-node threshold `r_c = 0`.

Equilibria of `ẋ = r + x²` are the real roots of `x² + r = 0`. -/

/-- An equilibrium exists iff the control parameter is at or below the
critical value `r_c = 0`. Crossing it (small change `r : 0⁻ → 0⁺`) destroys
every equilibrium — the tipping point. -/
theorem tipping_point_threshold (r : ℝ) :
    (∃ x : ℝ, x ^ 2 + r = 0) ↔ r ≤ 0 := by
  constructor
  · rintro ⟨x, hx⟩
    nlinarith [sq_nonneg x]
  · intro hr
    refine ⟨Real.sqrt (-r), ?_⟩
    have hsq : Real.sqrt (-r) ^ 2 = -r := Real.sq_sqrt (by linarith)
    rw [hsq]; ring

/-- Below the threshold (`r < 0`) there are exactly two distinct equilibria;
together with `tipping_point_threshold` (none for `r > 0`) this is a genuine
saddle-node bifurcation: two branches collide and annihilate at `r_c = 0`. -/
theorem saddle_node_two_branches (r : ℝ) (hr : r < 0) :
    Real.sqrt (-r) ≠ -Real.sqrt (-r)
    ∧ (Real.sqrt (-r)) ^ 2 + r = 0
    ∧ (-Real.sqrt (-r)) ^ 2 + r = 0 := by
  have hpos : 0 < Real.sqrt (-r) := Real.sqrt_pos.mpr (by linarith)
  have hsq : Real.sqrt (-r) ^ 2 = -r := Real.sq_sqrt (by linarith)
  refine ⟨by linarith, by rw [hsq]; ring, ?_⟩
  have hneg : (-Real.sqrt (-r)) ^ 2 = Real.sqrt (-r) ^ 2 := by ring
  rw [hneg, hsq]; ring

/-! ### 4. Energy balance: a unique equilibrium temperature.

Absorbed solar flux `Sflux > 0` balanced against grey-body emission
`σ · T⁴` (`σ > 0`). -/

theorem energy_balance_unique_equilibrium
    (σ Sflux : ℝ) (hσ : 0 < σ) (hS : 0 < Sflux) :
    ∃! T : ℝ, 0 < T ∧ σ * T ^ 4 = Sflux := by
      use ( Sflux / σ ) ^ ( 1/4 : ℝ );
      refine' ⟨ ⟨ Real.rpow_pos_of_pos ( by positivity ) _, _ ⟩, _ ⟩;
      · rw [ ← Real.rpow_natCast, ← Real.rpow_mul ( by positivity ) ] ; norm_num [ mul_div_cancel₀ _ hσ.ne' ];
      · intro y hy; rw [ ← hy.2, mul_div_cancel_left₀ _ hσ.ne' ] ; rw [ ← Real.rpow_natCast, ← Real.rpow_mul hy.1.le ] ; norm_num;

/-! ### 5. First-principles layer (paper anchors).

Three results that give the module deductive teeth, each derived from physics
rather than a fitted model: a *strict* second law for irreversible heat flow,
the Planck climate sensitivity from Stefan–Boltzmann, and the
Intelligence-Bound speed limit on ecological restoration — the uniquely
Viridis first principle. -/

/-- Strict Clausius inequality. Heat `Q > 0` flowing across a finite
temperature gap `Tc < Th` produces strictly positive total entropy
`Q·(1/Tc − 1/Th)`. Strengthens `second_law_entropy_nondecreasing` from
"non-decreasing" to strictly positive production whenever a real gradient
exists — the book's thesis that gradients and interference raise entropy. -/
theorem clausius_entropy_production_pos
    (Q Tc Th : ℝ) (hQ : 0 < Q) (hTc : 0 < Tc) (hgap : Tc < Th) :
    0 < Q * (1 / Tc - 1 / Th) := by
  have hinv : 1 / Th < 1 / Tc := one_div_lt_one_div_of_lt hTc hgap
  exact mul_pos hQ (by linarith)

/-- Entropy production is strictly monotone in the temperature gap: widening
the gradient (larger `Th` at fixed `Tc`) strictly increases entropy produced.
The more we drive the system from equilibrium, the more disorder we make. -/
theorem entropy_production_mono_in_gap
    (Q Tc Th₁ Th₂ : ℝ) (hQ : 0 < Q) (hTc : 0 < Tc)
    (h1 : Tc < Th₁) (h2 : Th₁ < Th₂) :
    Q * (1 / Tc - 1 / Th₁) < Q * (1 / Tc - 1 / Th₂) := by
  have hTh1 : 0 < Th₁ := lt_trans hTc h1
  have hinv : 1 / Th₂ < 1 / Th₁ := one_div_lt_one_div_of_lt hTh1 h2
  apply mul_lt_mul_of_pos_left _ hQ
  linarith

/-- Planck climate sensitivity (Stefan–Boltzmann, first principles).
The equilibrium temperature `T(F) = ((Q+F)/σ)^{1/4}`, set by balancing
absorbed-plus-forcing flux `Q+F` against grey-body emission `σT⁴`, is
STRICTLY increasing in the radiative forcing `F`: more forcing ⟹ strictly
more warming. The deductive backbone under "RCP scenarios imply warming". -/
theorem planck_sensitivity_strictMono
    (σ Q : ℝ) (hσ : 0 < σ) (hQ : 0 < Q) :
    StrictMonoOn (fun F : ℝ => ((Q + F) / σ) ^ ((1 : ℝ) / 4)) (Set.Ici 0) := by
  intro a ha b _ hab
  have ha0 : (0 : ℝ) ≤ a := Set.mem_Ici.mp ha
  have hbase : (0 : ℝ) ≤ (Q + a) / σ := by positivity
  have hnum : Q + a < Q + b := by linarith
  have hlt : (Q + a) / σ < (Q + b) / σ := (div_lt_div_iff_of_pos_right hσ).mpr hnum
  exact Real.rpow_lt_rpow hbase hlt (by norm_num)

/-
Intelligence-Bound restoration speed limit (the Viridis first principle).
A controller raising the climate-order metric `I` is subject to the Landauer
rate bound `dI/dt ≤ P/(k_B T ln 2)` — the Intelligence Bound applied to the
work of creating order. Then the order gained over any interval `[0,τ]`
cannot exceed `(P/(k_B T ln 2))·τ`: ordering has a finite maximum rate.
-/
theorem restoration_rate_bound
    (I : ℝ → ℝ) (P kB T : ℝ)
    (hI : Differentiable ℝ I) (hP : 0 < P) (hkB : 0 < kB) (hT : 0 < T)
    (hrate : ∀ t, deriv I t ≤ P / (kB * T * Real.log 2)) :
    ∀ τ : ℝ, 0 ≤ τ → I τ - I 0 ≤ (P / (kB * T * Real.log 2)) * τ := by
  -- By the Mean Value Theorem, there exists some $c \in (0, \tau)$ such that $I'(\tau) = \frac{I(\tau) - I(0)}{\tau}$.
  have h_mvt : ∀ τ > 0, ∃ c ∈ Set.Ioo 0 τ, deriv I c = (I τ - I 0) / τ := by
    intro τ hτ; have := exists_deriv_eq_slope I hτ; simp_all +decide [ div_eq_inv_mul ] ;
    exact this ( hI.continuous.continuousOn ) ( hI.differentiableOn );
  intro τ hτ; cases lt_or_eq_of_le hτ <;> [ obtain ⟨ c, hc₁, hc₂ ⟩ := h_mvt τ ‹_› ; aesop ] ; nlinarith [ hrate c, mul_div_cancel₀ ( I τ - I 0 ) ( ne_of_gt ‹_› ) ] ;

/-
Equivalent "speed limit" form: achieving a strictly positive target order
gain `ΔI` requires at least time `ΔI · k_B T ln 2 / P`. You cannot restore
order — cannot restore Gaia — faster than the Intelligence Bound permits.
-/
theorem restoration_time_lower_bound
    (I : ℝ → ℝ) (P kB T τ ΔI : ℝ)
    (hI : Differentiable ℝ I) (hP : 0 < P) (hkB : 0 < kB) (hT : 0 < T)
    (hlog : 0 < Real.log 2)
    (hrate : ∀ t, deriv I t ≤ P / (kB * T * Real.log 2))
    (hτ : 0 ≤ τ) (hgain : I τ - I 0 = ΔI) :
    ΔI * (kB * T * Real.log 2) / P ≤ τ := by
  have := restoration_rate_bound I P kB T hI hP hkB hT hrate τ hτ;
  rw [ div_le_iff₀ ] <;> first | positivity | rw [ ← hgain ] ; rw [ div_mul_eq_mul_div, le_div_iff₀ ] at this <;> first | positivity | linarith;

end HeatAndDisorder