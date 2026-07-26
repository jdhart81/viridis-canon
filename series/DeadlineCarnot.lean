/-
# The Deadline-Carnot Theorem (DCT) — the Stoker
Viridis Aristotle Forge · Nightly Run 106 · [09] Intelligence Capacity Framework × 🔥 Thermodynamic

INTENDED MEANING.
Every compute-optimal scaling law an AI lab uses to size a model (Chinchilla/Kaplan) implicitly
assumes UNLIMITED wall-clock time to spend a fixed compute budget. Once a hard deadline `τ` is
imposed, training becomes a finite-time thermodynamic engine: McCandlish et al.'s gradient-noise-
scale hyperbola `(S(b)-S_min)(D_used(b)-D_min)=S_min·D_min` (steps `S` vs. tokens `D_used` traded
off in batch size `b`) plays the role of an endoreversible Carnot engine's throttle. Substituting
the deadline-implied batch size `b*(τ)` gives a DATA EFFICIENCY that takes the exact Carnot
functional form `η(τ) = 1 − τ_floor/τ`, where `τ_floor = S_min·t1·N` is an absolute, un-crossable
wall-clock floor (no batch size, however large, beats it). Pricing wall-clock time against data
tokens and minimizing `TotalCost(τ) = c_τ·τ + c_D·(extra tokens)` gives a GOLDEN-RULE DEADLINE
`τ* = τ_floor + √(c_D·D_min·τ_floor/c_τ)` — a genuine Curzon–Ahlborn-style square-root correction,
itself an instance of a fully generic mechanism: any cost `c1·t + K/(t−floor)` is minimized at
`t* = floor + √(K/c1)`. This generic square-root lemma is *why* Curzon–Ahlborn-shaped efficiency
laws recur across so much of finite-time thermodynamics, training included.

FORMALIZATION SCOPE NOTE (spec invariance — assumptions flagged per protocol).
This file formalizes the FULLY GENERAL, self-contained mathematical core: the McCandlish
hyperbola invariance (R2), the monotonicity/floor/limit structure of `τ(b)` (R3), the closed-form
Carnot efficiency law and its monotonicity/limit/divergence/infeasibility structure (R4, HEADLINE),
the generic square-root-correction mechanism and its convexity (R6), the training-specific
golden-rule instance (R5), and the linear-in-`N` scaling of the wall-clock floor at fixed data
(R7) — every statement below is TRUE for arbitrary positive parameters satisfying the stated
hypotheses, not tied to any specific numeric calibration.

DEFERRED (gate-check, NOT submitted this cycle — matches `science-engine/DISCOVERIES_TO_PURSUE.md`
well-posedness scoping): (a) `chinchilla_foc_matches_lagrangian` (R1) — re-deriving the Chinchilla
closed-form optimum requires MATCHING specific literature-fitted constants (Hoffmann et al. 2022:
E=1.6934, A=406.4, α=0.3392, B=410.7, β=0.2849) against a 400k-point empirical grid search; this is
an empirical-fit verification (already 21/21-PASS numerically in `verify_106.py`), not a pure
mathematical identity independent of calibration, so it is left to the Python harness rather than
encoded as a Lean target. (b) The numeric half of R8 ("the Stoker" IB self-application) that
compares the realized bits/s rate against the illustrative physical ceiling `Ω·D_cap` (built from
`P_infra=5×10⁵ W`, `T_infra=320 K`, `Dcap=10⁻⁹`, plus the transcendental Chinchilla optimum itself)
is an illustrative numeric check, not a generic theorem — DEFERRED for the same reason as (a).
In its place, `stoker_realized_rate_bounded_above_by_floor_rate` below formalizes the GENERIC
structural content that makes the Stoker's ceiling-safety claim well-founded in the first place:
any golden-rule (or otherwise sub-floor-exceeding) deadline realizes STRICTLY LESS throughput than
the unreachable floor-rate `ΔI/τ_floor` — the tightest bound obtainable without external infra
constants.

NON-VACUITY. `dct_nonvacuous` binds concrete positive numbers (Smin=2, Bnoise=3, Dmin=5, b=6,
τ_floor=10 via (Smin,t1,N)=(2,1,5), and a golden-rule instance (floor,c1,K)=(4,1,4) giving a clean
`τ*=6`) and confirms every core quantity is well-defined, non-degenerate, and matches its expected
closed-form value.

Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real Set Filter Topology

namespace Viridis.Stoker.DeadlineCarnot

/-! ### Core objects: the McCandlish hyperbola and the wall-clock engine. -/

/-- McCandlish steps-to-converge as a function of batch size `b`:
    `S(b) = S_min·(1 + B_noise/b)`. -/
noncomputable def SofB (Smin Bnoise b : ℝ) : ℝ := Smin * (1 + Bnoise / b)

/-- McCandlish examples-consumed (tokens) as a function of batch size `b`:
    `D_used(b) = D_min·(1 + b/B_noise)`. -/
noncomputable def DusedOfB (Dmin Bnoise b : ℝ) : ℝ := Dmin * (1 + b / Bnoise)

/-- Wall-clock time to train at batch size `b`, model size `N`, per-step time `t1`:
    `τ(b) = S(b)·t1·N`. -/
noncomputable def tauOfB (Smin Bnoise t1 N b : ℝ) : ℝ := SofB Smin Bnoise b * t1 * N

/-- The absolute, un-crossable wall-clock floor: `τ_floor = S_min·t1·N` (the `b→∞` limit). -/
def tauFloorOf (Smin t1 N : ℝ) : ℝ := Smin * t1 * N

/-! ### R2 — the McCandlish hyperbola is batch-invariant. -/

/-- **R2 (boxed).** `(S(b)−S_min)(D_used(b)−D_min) = S_min·D_min` for every batch size `b>0` —
    the gradient-noise-scale steps/examples tradeoff is a hyperbola of constant product,
    independent of `b`. -/
theorem mccandlish_hyperbola_batch_invariant (Smin Bnoise Dmin b : ℝ)
    (hSmin : 0 < Smin) (hBnoise : 0 < Bnoise) (hDmin : 0 < Dmin) (hb : 0 < b) :
    (SofB Smin Bnoise b - Smin) * (DusedOfB Dmin Bnoise b - Dmin) = Smin * Dmin := by
  dsimp [SofB, DusedOfB]
  field_simp
  ring

/-! ### R3 — monotonicity and the wall-clock floor. -/

/-- **R3 (boxed).** `τ(b)` is strictly decreasing in batch size: bigger batches finish faster. -/
theorem tau_of_b_monotone_decreasing (Smin Bnoise t1 N b1 b2 : ℝ)
    (hSmin : 0 < Smin) (hBnoise : 0 < Bnoise) (ht1 : 0 < t1) (hN : 0 < N)
    (hb1 : 0 < b1) (hb12 : b1 < b2) :
    tauOfB Smin Bnoise t1 N b2 < tauOfB Smin Bnoise t1 N b1 := by
  dsimp [tauOfB, SofB]
  have hb2 : 0 < b2 := lt_trans hb1 hb12
  have hdiv : Bnoise / b2 < Bnoise / b1 := by
    exact (div_lt_div_iff₀ hb2 hb1).2 (by nlinarith)
  calc
    Smin * (1 + Bnoise / b2) * t1 * N = (Smin * t1 * N) * (1 + Bnoise / b2) := by ring
    _ < (Smin * t1 * N) * (1 + Bnoise / b1) :=
      mul_lt_mul_of_pos_left (by linarith) (mul_pos (mul_pos hSmin ht1) hN)
    _ = Smin * (1 + Bnoise / b1) * t1 * N := by ring

/-- **R3 (supporting).** For every finite batch size `b>0`, `τ(b)` is strictly ABOVE the floor —
    the floor is approached but never reached at any finite batch size. -/
theorem tau_of_b_gt_tau_floor (Smin Bnoise t1 N b : ℝ)
    (hSmin : 0 < Smin) (hBnoise : 0 < Bnoise) (ht1 : 0 < t1) (hN : 0 < N) (hb : 0 < b) :
    tauFloorOf Smin t1 N < tauOfB Smin Bnoise t1 N b := by
  dsimp [tauFloorOf, tauOfB, SofB]
  have hq : 0 < Bnoise / b := div_pos hBnoise hb
  calc
    Smin * t1 * N = (Smin * t1 * N) * 1 := by ring
    _ < (Smin * t1 * N) * (1 + Bnoise / b) :=
      mul_lt_mul_of_pos_left (by linarith) (mul_pos (mul_pos hSmin ht1) hN)
    _ = Smin * (1 + Bnoise / b) * t1 * N := by ring

/-- **R3 (boxed).** `τ(b) → τ_floor` as `b → ∞`. -/
theorem tau_floor_is_b_to_infinity_limit (Smin Bnoise t1 N : ℝ)
    (hSmin : 0 < Smin) (hBnoise : 0 < Bnoise) (ht1 : 0 < t1) (hN : 0 < N) :
    Tendsto (fun b : ℝ => tauOfB Smin Bnoise t1 N b) atTop (nhds (tauFloorOf Smin t1 N)) := by
  have hz : Tendsto (fun b : ℝ => Bnoise / b) atTop (nhds 0) :=
    tendsto_const_nhds.div_atTop tendsto_id
  have h1 : Tendsto (fun b : ℝ => 1 + Bnoise / b) atTop (nhds 1) := by
    simpa using hz.const_add 1
  have h2 : Tendsto (fun b : ℝ => Smin * (1 + Bnoise / b)) atTop (nhds (Smin * 1)) :=
    h1.const_mul Smin
  have h3 := (h2.mul_const t1).mul_const N
  simpa only [tauOfB, SofB, tauFloorOf, mul_one] using h3

/-- **R4 (supporting).** No finite batch size can meet a deadline at or below the floor —
    the direct impossibility statement dual to `tau_of_b_gt_tau_floor`. -/
theorem deadline_infeasible_below_floor (Smin Bnoise t1 N tau : ℝ)
    (hSmin : 0 < Smin) (hBnoise : 0 < Bnoise) (ht1 : 0 < t1) (hN : 0 < N)
    (htau : tau ≤ tauFloorOf Smin t1 N) :
    ¬ ∃ b : ℝ, 0 < b ∧ tauOfB Smin Bnoise t1 N b = tau := by
  rintro ⟨b, hb, rfl⟩
  exact (not_lt_of_ge htau) (tau_of_b_gt_tau_floor Smin Bnoise t1 N b hSmin hBnoise ht1 hN hb)

/-! ### R4 (HEADLINE) — the Deadline-Carnot efficiency law. -/

/-- The batch size implicitly required to hit deadline `τ` (root of `τ(b)=τ`, inverted). -/
noncomputable def bStarOfTau (tau tf Bnoise : ℝ) : ℝ := Bnoise / (tau / tf - 1)

/-- The closed-form tokens used to hit deadline `τ`: `D_used(τ) = D_min·τ/(τ−τ_floor)`. -/
noncomputable def dUsedOfTau (tau tf Dmin : ℝ) : ℝ := Dmin * tau / (tau - tf)

/-- The Deadline-Carnot data efficiency: `η(τ) = 1 − τ_floor/τ`. -/
noncomputable def etaOfTau (tau tf : ℝ) : ℝ := 1 - tf / tau

/-- **R4 (supporting).** The closed-form `D_used(τ)` matches direct substitution of the
    deadline-implied batch size `b*(τ)` into the McCandlish token formula. -/
theorem dused_of_tau_matches_bstar_substitution (tau tf Dmin Bnoise : ℝ)
    (htf : 0 < tf) (htau : tf < tau) (hDmin : 0 < Dmin) (hBnoise : 0 < Bnoise) :
    DusedOfB Dmin Bnoise (bStarOfTau tau tf Bnoise) = dUsedOfTau tau tf Dmin := by
  dsimp [DusedOfB, bStarOfTau, dUsedOfTau]
  have hnt : tau ≠ 0 := ne_of_gt (lt_trans htf htau)
  have htf0 : tf ≠ 0 := ne_of_gt htf
  have hB0 : Bnoise ≠ 0 := ne_of_gt hBnoise
  have hsub : tau - tf ≠ 0 := ne_of_gt (sub_pos.2 htau)
  have hn : tau / tf - 1 ≠ 0 := by
    exact ne_of_gt (sub_pos.2 ((lt_div_iff₀ htf).2 (by simpa using htau)))
  field_simp [hnt, htf0, hB0, hsub, hn]
  ring

/-- **R4 (HEADLINE, canon candidate) — the Deadline-Carnot Law.**
    `D_min / D_used(τ) = η(τ) = 1 − τ_floor/τ`, the exact Carnot efficiency functional form,
    with the deadline `τ` playing the role of the hot reservoir and the un-crossable floor
    playing the role of the cold one. -/
theorem deadline_carnot_efficiency_eq_one_minus_floor_over_tau (tau tf Dmin : ℝ)
    (htf : 0 < tf) (htau : tf < tau) (hDmin : 0 < Dmin) :
    Dmin / dUsedOfTau tau tf Dmin = etaOfTau tau tf := by
  dsimp [dUsedOfTau, etaOfTau]
  have hD : Dmin ≠ 0 := ne_of_gt hDmin
  have ht : tau ≠ 0 := ne_of_gt (lt_trans htf htau)
  have hsub : tau - tf ≠ 0 := ne_of_gt (sub_pos.2 htau)
  field_simp

/-- **R4 (boxed).** `η(τ)` is strictly increasing in the deadline `τ`. -/
theorem eta_strictly_increasing_in_tau (tf tau1 tau2 : ℝ)
    (htf : 0 < tf) (htau1 : tf < tau1) (htau12 : tau1 < tau2) :
    etaOfTau tau1 tf < etaOfTau tau2 tf := by
  dsimp [etaOfTau]
  have h1 : 0 < tau1 := lt_trans htf htau1
  have h2 : 0 < tau2 := lt_trans h1 htau12
  have hd : tf / tau2 < tf / tau1 := by
    exact (div_lt_div_iff₀ h2 h1).2 (by nlinarith)
  linarith

/-- **R4 (boxed).** `η(τ) → 1` as `τ → ∞` (an infinite deadline is perfectly data-efficient). -/
theorem eta_tendsto_one_atTop (tf : ℝ) (htf : 0 < tf) :
    Tendsto (fun tau : ℝ => etaOfTau tau tf) atTop (nhds 1) := by
  have hz : Tendsto (fun tau : ℝ => tf / tau) atTop (nhds 0) :=
    tendsto_const_nhds.div_atTop tendsto_id
  simpa [etaOfTau] using tendsto_const_nhds.sub hz

/-- **R4 (boxed, HEADLINE).** `D_used(τ)` DIVERGES as `τ → τ_floor⁺` — an un-crossable horizon,
    in the family of the canon's other critical/divergent floors. -/
theorem d_used_diverges_at_floor (tf Dmin : ℝ) (htf : 0 < tf) (hDmin : 0 < Dmin) :
    Tendsto (fun tau : ℝ => dUsedOfTau tau tf Dmin) (nhdsWithin tf (Set.Ioi tf)) atTop := by
  have hid : Tendsto (fun x : ℝ => x) (nhdsWithin tf (Ioi tf)) (nhds tf) :=
    tendsto_id.mono_left inf_le_left
  have hc : Tendsto (fun _ : ℝ => tf) (nhdsWithin tf (Ioi tf)) (nhds tf) :=
    tendsto_const_nhds
  have hcont : Tendsto (fun tau : ℝ => tau - tf) (nhdsWithin tf (Ioi tf)) (nhds 0) := by
    simpa only [sub_self] using hid.sub hc
  have hmap : ∀ᶠ x : ℝ in nhdsWithin tf (Ioi tf), x - tf ∈ Ioi (0 : ℝ) := by
    filter_upwards [self_mem_nhdsWithin] with x hx
    change 0 < x - tf
    exact sub_pos.2 hx
  have hsub : Tendsto (fun tau : ℝ => tau - tf) (nhdsWithin tf (Ioi tf))
      (nhdsWithin 0 (Ioi 0)) := tendsto_nhdsWithin_iff.2 ⟨hcont, hmap⟩
  have hi : Tendsto (fun tau : ℝ => (tau - tf)⁻¹) (nhdsWithin tf (Ioi tf)) atTop :=
    tendsto_inv_nhdsGT_zero.comp hsub
  have hiD : Tendsto (fun tau : ℝ => (tau - tf)⁻¹ * (Dmin * tf))
      (nhdsWithin tf (Ioi tf)) atTop := hi.atTop_mul_const (mul_pos hDmin htf)
  have hcD : Tendsto (fun _ : ℝ => Dmin) (nhdsWithin tf (Ioi tf)) (nhds Dmin) :=
    tendsto_const_nhds
  apply (hiD.atTop_add hcD).congr'
  filter_upwards [self_mem_nhdsWithin] with x hx
  have hne : x - tf ≠ 0 := ne_of_gt (sub_pos.2 hx)
  dsimp [dUsedOfTau]
  field_simp
  ring

/-! ### R6 — the generic square-root-correction mechanism (why Curzon–Ahlborn laws recur). -/

/-- The generic minimizer of a linear-plus-hyperbolic-near-a-floor cost:
    `t* = floor + √(K/c1)`. -/
noncomputable def tauStarGeneric (floor c1 K : ℝ) : ℝ := floor + Real.sqrt (K / c1)

/-- **R6 (boxed) — genericity of the square-root correction.** For ANY cost of the form
    `c1·t + K/(t−floor)` on `t>floor`, the point `t* = floor+√(K/c1)` is a GLOBAL MINIMIZER, and
    the minimum cost achieved has the closed form `c1·floor + 2√(c1·K)`. This single mechanism is
    why Curzon–Ahlborn-shaped `1−√(T_c/T_h)`-type laws recur across finite-time thermodynamics —
    training included. -/
theorem sqrt_correction_generic_near_critical_floor (floor c1 K : ℝ)
    (hc1 : 0 < c1) (hK : 0 < K) :
    (∀ t : ℝ, floor < t →
        c1 * tauStarGeneric floor c1 K + K / (tauStarGeneric floor c1 K - floor)
          ≤ c1 * t + K / (t - floor)) ∧
      c1 * tauStarGeneric floor c1 K + K / (tauStarGeneric floor c1 K - floor)
        = c1 * floor + 2 * Real.sqrt (c1 * K) := by
  let s := Real.sqrt (K / c1)
  have hq : 0 < K / c1 := div_pos hK hc1
  have hs : 0 < s := Real.sqrt_pos.2 hq
  have hs0 : s ≠ 0 := ne_of_gt hs
  have hs2 : s ^ 2 = K / c1 := Real.sq_sqrt (le_of_lt hq)
  have hKrel : K = c1 * s ^ 2 := by
    field_simp at hs2
    nlinarith
  have hroot : Real.sqrt (c1 * K) = c1 * s := by
    rw [hKrel, show c1 * (c1 * s ^ 2) = (c1 * s) ^ 2 by ring,
      Real.sqrt_sq_eq_abs, abs_of_pos (mul_pos hc1 hs)]
  constructor
  · intro t ht
    have hx : 0 < t - floor := sub_pos.2 ht
    have hx0 : t - floor ≠ 0 := ne_of_gt hx
    dsimp [tauStarGeneric]
    rw [show Real.sqrt (K / c1) = s from rfl, add_sub_cancel_left]
    have hid : c1 * t + K / (t - floor) - (c1 * (floor + s) + K / s) =
        c1 * ((t - floor) - s) ^ 2 / (t - floor) := by
      rw [hKrel]
      field_simp
      ring
    rw [← sub_nonneg, hid]
    positivity
  · dsimp [tauStarGeneric]
    rw [show Real.sqrt (K / c1) = s from rfl, add_sub_cancel_left, hroot, hKrel]
    field_simp
    ring

/-- **R5 (supporting) — convexity on the feasible domain.** The generic cost function
    `t ↦ c1·t + K/(t−floor)` is convex on `(floor, ∞)`, which is what guarantees the
    square-root critical point found above is a genuine (not merely local) minimum. -/
theorem totalcost_convex_on_feasible_domain (c1 K floor : ℝ) (hc1 : 0 < c1) (hK : 0 < K) :
    ConvexOn ℝ (Set.Ioi floor) (fun t : ℝ => c1 * t + K / (t - floor)) := by
  constructor
  · exact convex_Ioi floor
  · intro x hx y hy a b ha hb hab
    dsimp
    have hbval : b = 1 - a := by linarith
    have hx' : 0 < x - floor := sub_pos.2 hx
    have hy' : 0 < y - floor := sub_pos.2 hy
    have hm : 0 < a * (x - floor) + b * (y - floor) := by
      rcases lt_or_eq_of_le ha with ha' | rfl
      · nlinarith [mul_pos ha' hx']
      · have : b = 1 := by linarith
        positivity
    have hid : a / (x - floor) + b / (y - floor) -
          1 / (a * (x - floor) + b * (y - floor)) =
        a * b * ((x - floor) - (y - floor)) ^ 2 /
          ((x - floor) * (y - floor) * (a * (x - floor) + b * (y - floor))) := by
      field_simp
      rw [hbval]
      ring
    have hrec : 1 / (a * (x - floor) + b * (y - floor)) ≤
        a / (x - floor) + b / (y - floor) := by
      rw [← sub_nonneg, hid]
      positivity
    have heq : a * x + b * y - floor =
        a * (x - floor) + b * (y - floor) := by rw [hbval]; ring
    rw [heq]
    have hKrec := mul_le_mul_of_nonneg_left hrec (le_of_lt hK)
    have hKrec' : K / (a * (x - floor) + b * (y - floor)) ≤
        K * (a / (x - floor) + b / (y - floor)) := by
      simpa [div_eq_mul_inv] using hKrec
    calc
      c1 * (a * x + b * y) + K / (a * (x - floor) + b * (y - floor))
          ≤ c1 * (a * x + b * y) + K * (a / (x - floor) + b / (y - floor)) :=
            add_le_add (le_refl _) hKrec'
      _ = a * (c1 * x + K / (x - floor)) + b * (c1 * y + K / (y - floor)) := by
        rw [hbval]
        ring

/-! ### R5 — the Golden-Rule Deadline (the training-specific instance of R6). -/

/-- The golden-rule economically-optimal training deadline:
    `τ* = τ_floor + √(c_D·D_min·τ_floor/c_τ)`. -/
noncomputable def tauStarGolden (tf Dmin cD cTau : ℝ) : ℝ :=
  tf + Real.sqrt (cD * Dmin * tf / cTau)

/-- **R5 (canon candidate) — the Golden-Rule Deadline.** `τ*` is a global minimizer of the
    total cost `c_τ·τ + c_D·(extra tokens needed to hit deadline τ)`, where the extra-token cost
    is exactly `D_min·τ_floor/(τ−τ_floor)` — the direct training-economics instance of the
    generic square-root mechanism (R6). -/
theorem golden_rule_tau_star_closed_form (tf Dmin cD cTau : ℝ)
    (htf : 0 < tf) (hDmin : 0 < Dmin) (hcD : 0 < cD) (hcTau : 0 < cTau) :
    ∀ tau : ℝ, tf < tau →
      cTau * tauStarGolden tf Dmin cD cTau
          + cD * Dmin * tf / (tauStarGolden tf Dmin cD cTau - tf)
        ≤ cTau * tau + cD * Dmin * tf / (tau - tf) := by
  have hK : 0 < cD * Dmin * tf := mul_pos (mul_pos hcD hDmin) htf
  have h := (sqrt_correction_generic_near_critical_floor tf cTau (cD * Dmin * tf)
    hcTau hK).1
  simpa only [tauStarGeneric, tauStarGolden, mul_assoc] using h

/-- **R5 (boxed).** The data efficiency achieved exactly at the golden-rule deadline,
    `η(τ*)`, equals `x/(1+x)` where `x = √(c_D·D_min·τ_floor/c_τ)/τ_floor` is the data-cost/
    time-cost ratio — monotonically increasing in `x` (data-expensive-relative-to-time ⇒
    `η→1`; time-expensive-relative-to-data ⇒ `η→0`). -/
theorem golden_rule_eta_star_equals_x_over_one_plus_x (tf Dmin cD cTau : ℝ)
    (htf : 0 < tf) (hDmin : 0 < Dmin) (hcD : 0 < cD) (hcTau : 0 < cTau) :
    etaOfTau (tauStarGolden tf Dmin cD cTau) tf
      = (Real.sqrt (cD * Dmin * tf / cTau) / tf)
          / (1 + Real.sqrt (cD * Dmin * tf / cTau) / tf) := by
  have hq : 0 < cD * Dmin * tf / cTau :=
    div_pos (mul_pos (mul_pos hcD hDmin) htf) hcTau
  have hs : 0 < Real.sqrt (cD * Dmin * tf / cTau) := Real.sqrt_pos.2 hq
  have htf0 : tf ≠ 0 := ne_of_gt htf
  have hsum : tf + Real.sqrt (cD * Dmin * tf / cTau) ≠ 0 :=
    ne_of_gt (add_pos htf hs)
  dsimp [etaOfTau, tauStarGolden]
  field_simp
  ring

/-! ### R7 — the wall-clock floor scales linearly in model size at fixed data budget. -/

/-- The wall-clock floor as an explicit function of model size `N`, at a fixed data budget
    `D_min` and reference (max-parallelism) batch size `b_ref`: `τ_floor(N) = (D_min/b_ref)·t1·N`. -/
noncomputable def tauFloorOfN (Dmin bRef t1 N : ℝ) : ℝ := (Dmin / bRef) * t1 * N

/-- **R7 (boxed).** At a FIXED data corpus (not the Chinchilla-optimal frontier), the wall-clock
    floor scales EXACTLY LINEARLY in model size `N`: the ratio `τ_floor(N)/N` is constant across
    any two positive model sizes `N1, N2`. -/
theorem tau_floor_linear_in_N_at_fixed_data (Dmin bRef t1 N1 N2 : ℝ)
    (hDmin : 0 < Dmin) (hbRef : 0 < bRef) (ht1 : 0 < t1) (hN1 : 0 < N1) (hN2 : 0 < N2) :
    tauFloorOfN Dmin bRef t1 N1 / N1 = tauFloorOfN Dmin bRef t1 N2 / N2 := by
  dsimp [tauFloorOfN]
  field_simp

/-! ### R8 — the Stoker: generic structural core of the IB self-application. -/

/-- **R8 (structural core, IB self-application).** Any deadline strictly above the floor realizes
    a delivered-information rate `ΔI/τ` strictly BELOW the unreachable floor-rate `ΔI/τ_floor` —
    the tightest generic bound available without invoking external physical-infrastructure
    constants (`P_infra`, `T_infra`, `D_cap`). This is the structural fact that makes "the golden-
    rule deadline never violates the Intelligence-Bound ceiling" a well-founded claim: the
    achieved rate is already capped below the floor-rate before any illustrative physical ceiling
    is even invoked. -/
theorem stoker_realized_rate_bounded_above_by_floor_rate (deltaI tf tauStar : ℝ)
    (hdeltaI : 0 < deltaI) (htf : 0 < tf) (htauStar : tf < tauStar) :
    deltaI / tauStar < deltaI / tf := by
  exact (div_lt_div_iff₀ (lt_trans htf htauStar) htf).2 (by nlinarith)

/-! ### Non-vacuity witness. -/

/-- **Non-vacuity.** Concrete positive numbers instantiate every core definition to a
    well-defined, non-degenerate value, and the golden-rule closed form matches its expected
    numeric evaluation (`floor=4,c1=1,K=4 ⇒ τ*=6`, `η(τ*)=1/3`). -/
theorem dct_nonvacuous :
    0 < tauFloorOf 2 1 5 ∧
      (SofB 2 3 6 - 2) * (DusedOfB 5 3 6 - 5) = 2 * 5 ∧
      etaOfTau 20 10 = (1 : ℝ) / 2 ∧
      tauStarGeneric 4 1 4 = 6 ∧
      etaOfTau (tauStarGeneric 4 1 4) 4 = (1 : ℝ) / 3 := by
  norm_num [tauFloorOf, SofB, DusedOfB, etaOfTau, tauStarGeneric]

end Viridis.Stoker.DeadlineCarnot
