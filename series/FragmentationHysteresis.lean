/-
  FragmentationHysteresis.lean — the Fragmentation Hysteresis Theorem (FHT), "the Mender"
  Viridis Aristotle Forge · nightly Run 109 · [03] HDFM Corridors × 🔥 Thermodynamic · 2026-07-25

  CLAIM.  Habitat loss and habitat restoration are not the same path run backwards.  Destruction
  of the connective backbone requires no knowledge of where the backbone is; restoration does.
  Encode that asymmetry as a SITING EFFICIENCY  q ∈ (0,1]  — the fraction of restored area that
  lands on the connective backbone — and the degrade→restore cycle becomes irreversible:

    R1  effective-area map        a_eff(a) = a_min + q (a - a_min) ≤ a, with equality iff q = 1
                                   or a = a_min; hence the restoration branch of the order
                                   parameter never exceeds the degradation branch.
    R2  offset multiplier law     recovering a lost area ΔA requires restoring x* = ΔA / q, so the
                                   compensation multiplier is exactly m = 1/q and the restoration
                                   debt (1/q - 1)ΔA is ≥ 0, vanishing iff siting is perfect.
    R3  Second Law for landscapes the enclosed hysteresis area W(q) = ∫ (S(a) - S(a_eff a)) da is
                                   ≥ 0, is antitone in q, is 0 at q = 1, and is STRICTLY positive
                                   whenever q < 1 on a strictly monotone order parameter.
    R4  dead zone                  below a macroscopic connectivity floor a★ restoration buys
                                   nothing until x ≥ (a★ - a_min)/q — a tax scaling as 1/q.
    R5  latent heat of fragmentation  crossing the percolation threshold destroys the observable
                                   restoration TEMPLATE, collapsing q₁ → q₀, so the debt jumps by
                                   L = (1/q₀ - 1/q₁)·ΔA > 0: a first-order irreversibility riding
                                   on a continuous transition (no feedback, no alternative state).
    R6  information–area equivalence  q(I) = min(q₁, q₀·2^I): each bit halves the required area
                                   BELOW saturation, the halving law provably FAILS across the
                                   clamp, value saturates hard at I* = log₂(q₁/q₀), the marginal
                                   bit is worth ln2 × the current overbuild, and the survey-depth
                                   optimum has a closed form.
    R7  the Mender (≈51st IB self-application)  bits cost time: dI/dt ≤ P·D/(k_B T ln 2).  Racing
                                   a landscape degrading at rate δ toward its horizon a_c gives a
                                   minimum sensing power P_min that DIVERGES at the horizon.

  SCOPE / WELL-POSEDNESS GATE.  This file formalizes only self-contained, non-vacuous real
  analysis.  DEFERRED as CITED, not re-derived here: the Newman–Ziff percolation sweep and the
  numerical value a_c ≈ 0.5927 of the square-lattice site threshold, the β ≈ 5/36 exponent behind
  the restoration sweet spot, and the empirical 4.9:1 offset ratio.  The order parameter S enters
  ONLY through explicit shape hypotheses (Monotone / StrictMono / Continuous) supplied as
  arguments; nothing below depends on percolation theory being true.

  NON-VACUITY (mandatory).  `fht_nonvacuous` exhibits the paper's worked example
  (q₁ = 0.85, q₀ = 0.12, ΔA = 0.35) witnessing every hypothesis with a strictly positive latent
  heat and a strictly interior saturation depth; `fht_cycle_work_pos_witness` exhibits a concrete
  strictly monotone continuous order parameter with strictly positive hysteresis-loop area.
  A proof of a vacuously-true statement is a FAILURE of this file.
-/
import Mathlib

namespace Viridis.Mender.FragmentationHysteresis

open Real

/-! ### R1 — the effective-area map -/

/-- Restoring toward habitat fraction `a` from the post-loss floor `aMin` with siting efficiency
`q` only raises the *connective* fraction to `aEff q aMin a`. -/
noncomputable def aEff (q aMin a : ℝ) : ℝ := aMin + q * (a - aMin)

/-- The restoration branch never runs above the degradation branch. -/
theorem aEff_le_self {q aMin a : ℝ} (hq : 0 < q) (hq1 : q ≤ 1) (ha : aMin ≤ a) :
    aEff q aMin a ≤ a := by
  unfold aEff
  have hprod : 0 ≤ (1 - q) * (a - aMin) :=
    mul_nonneg (sub_nonneg.mpr hq1) (sub_nonneg.mpr ha)
  nlinarith

/-- Perfect targeting is the reversible limit: the two branches meet exactly when `q = 1` or no
area was lost. -/
theorem aEff_eq_self_iff {q aMin a : ℝ} (hq : 0 < q) (hq1 : q ≤ 1) (ha : aMin ≤ a) :
    aEff q aMin a = a ↔ q = 1 ∨ a = aMin := by
  constructor
  · intro h
    rw [aEff] at h
    have : (q - 1) * (a - aMin) = 0 := by linarith
    rcases mul_eq_zero.mp this with hq' | ha'
    · left; linarith
    · right; linarith
  · intro h
    rcases h with rfl | rfl
    · simp [aEff]
    · simp [aEff]

/-- R1 (monotone gap).  For any monotone order parameter, the up-branch is dominated by the
down-branch pointwise. -/
theorem restoration_branch_le_degradation_branch
    {S : ℝ → ℝ} (hS : Monotone S) {q aMin a : ℝ} (hq : 0 < q) (hq1 : q ≤ 1) (ha : aMin ≤ a) :
    S (aEff q aMin a) ≤ S a := by
  apply hS
  exact aEff_le_self hq hq1 ha

/-! ### R2 — the offset multiplier law and the restoration debt -/

/-- Area that must be restored to recover a connective loss `ΔA` at siting efficiency `q`. -/
noncomputable def xStar (q ΔA : ℝ) : ℝ := ΔA / q

/-- Restoration debt (overbuild): restored area in excess of the area lost. -/
noncomputable def debt (q ΔA : ℝ) : ℝ := (1 / q - 1) * ΔA

/-- Restoring `xStar q ΔA` hectares recovers exactly the lost connective area `ΔA`. -/
theorem connective_gain_of_xStar {q ΔA : ℝ} (hq : 0 < q) : q * xStar q ΔA = ΔA := by
  simp [xStar, mul_div_cancel₀ _ hq.ne']

/-- **R2 — Offset Multiplier Law.**  The physically required compensation ratio is exactly `1/q`:
an *information* premium, not a risk premium. -/
theorem multiplier_eq_one_over_q {q ΔA : ℝ} (hq : 0 < q) (hΔA : 0 < ΔA) :
    xStar q ΔA / ΔA = 1 / q := by
  unfold xStar
  field_simp

/-- The restoration debt is nonnegative, and vanishes exactly under perfect siting. -/
theorem debt_nonneg_and_zero_iff_perfect {q ΔA : ℝ} (hq : 0 < q) (hq1 : q ≤ 1) (hΔA : 0 < ΔA) :
    0 ≤ debt q ΔA ∧ (debt q ΔA = 0 ↔ q = 1) := by
  have h1q : 1 / q ≥ 1 := by
    have : q ≤ 1 := hq1
    rw [ge_iff_le, le_div_iff₀ hq]
    linarith
  constructor
  · unfold debt; nlinarith
  · constructor
    · intro h
      rw [debt] at h
      have h2 : 1 / q - 1 = 0 := by nlinarith
      rw [sub_eq_zero] at h2
      rw [div_eq_iff hq.ne'] at h2
      linarith
    · intro h
      rw [debt, h]
      simp

/-- The debt is strictly antitone in siting efficiency: better targeting always costs less area. -/
theorem debt_strictAntiOn_q {ΔA : ℝ} (hΔA : 0 < ΔA) :
    StrictAntiOn (fun q => debt q ΔA) (Set.Ioi (0 : ℝ)) := by
  intro x hx y hy hxy
  unfold debt
  have hr : 1 / y < 1 / x := one_div_lt_one_div_of_lt hx hxy
  nlinarith

/-! ### R3 — the hysteresis loop area is dissipated connectivity work -/

/-- Enclosed area of the degrade→restore cycle between the post-loss floor `aMin` and the
pre-loss state `a0`: the connectivity work dissipated per cycle. -/
noncomputable def cycleWork (S : ℝ → ℝ) (q aMin a0 : ℝ) : ℝ :=
  ∫ a in aMin..a0, (S a - S (aEff q aMin a))

/-- **R3 (Second Law form).**  The hysteresis loop area is nonnegative for every imperfect siting
efficiency. -/
theorem cycle_work_nonneg {S : ℝ → ℝ} (hSm : Monotone S) (hSc : Continuous S)
    {q aMin a0 : ℝ} (hq : 0 < q) (hq1 : q ≤ 1) (h0 : aMin ≤ a0) :
    0 ≤ cycleWork S q aMin a0 := by
  rw [cycleWork]
  apply intervalIntegral.integral_nonneg h0
  intro x hx
  exact sub_nonneg_of_le (hSm (aEff_le_self hq hq1 hx.1))

/-- Perfect siting is the reversible limit: zero dissipated connectivity work. -/
theorem cycle_work_zero_of_q_eq_one {S : ℝ → ℝ} {aMin a0 : ℝ} :
    cycleWork S 1 aMin a0 = 0 := by
  unfold cycleWork
  simp only [aEff]
  simp [mul_one, add_sub_cancel]

/-- **R3 (strict irreversibility).**  On a strictly monotone continuous order parameter every
imperfectly targeted cycle dissipates a strictly positive amount of connectivity work — so
`cycleWork = 0` characterises `q = 1`. -/
theorem cycle_work_pos_of_q_lt_one {S : ℝ → ℝ} (hSm : StrictMono S) (hSc : Continuous S)
    {q aMin a0 : ℝ} (hq : 0 < q) (hq1 : q < 1) (h0 : aMin < a0) :
    0 < cycleWork S q aMin a0 := by
  unfold cycleWork
  apply intervalIntegral.integral_pos h0
  · exact (hSc.sub (hSc.comp
      (continuous_const.add (continuous_const.mul (continuous_id.sub continuous_const))))).continuousOn
  · intro x hx
    apply sub_nonneg.mpr
    apply hSm.monotone
    unfold aEff
    have hp : 0 ≤ (1 - q) * (x - aMin) :=
      mul_nonneg (sub_nonneg.mpr (le_of_lt hq1)) (sub_nonneg.mpr (le_of_lt hx.1))
    nlinarith
  · refine ⟨a0, ⟨le_of_lt h0, le_rfl⟩, ?_⟩
    apply sub_pos.mpr
    apply hSm
    unfold aEff
    have hp : 0 < (1 - q) * (a0 - aMin) :=
      mul_pos (sub_pos.mpr hq1) (sub_pos.mpr h0)
    nlinarith

/-- The loop area shrinks monotonically as siting improves. -/
theorem cycle_work_antitone_in_q {S : ℝ → ℝ} (hSm : Monotone S) (hSc : Continuous S)
    {q q' aMin a0 : ℝ} (hq : 0 < q) (hqq : q ≤ q') (hq1 : q' ≤ 1) (h0 : aMin ≤ a0) :
    cycleWork S q' aMin a0 ≤ cycleWork S q aMin a0 := by
  unfold cycleWork
  apply intervalIntegral.integral_mono_on
  · exact h0
  · exact (hSc.sub (hSc.comp (continuous_const.add (continuous_const.mul (continuous_id.sub continuous_const))))).intervalIntegrable _ _
  · exact (hSc.sub (hSc.comp (continuous_const.add (continuous_const.mul (continuous_id.sub continuous_const))))).intervalIntegrable _ _
  · intro a ha
    rw [sub_le_sub_iff_left]
    apply hSm
    unfold aEff
    have : aMin ≤ a := ha.1
    have h1 : a - aMin ≥ 0 := sub_nonneg_of_le this
    nlinarith

/-! ### R4 — the dead zone and the reconnection tax -/

/-- Restoration needed to lift the *connective* fraction back to a macroscopic floor `aStar`. -/
noncomputable def deadZone (q aMin aStar : ℝ) : ℝ := (aStar - aMin) / q

/-- **R4.**  Below the floor, restoration buys exactly zero macroscopic connectivity: any
restored amount short of `deadZone` leaves the order parameter at zero. -/
theorem dead_zone_buys_nothing {S : ℝ → ℝ} {aStar : ℝ} (hS : ∀ a, a < aStar → S a = 0)
    {q aMin x : ℝ} (hq : 0 < q) (hx : x < deadZone q aMin aStar) :
    S (aMin + q * x) = 0 := by
  rw [deadZone] at hx
  have h : aMin + q * x < aStar := by
    have hx' : q * x < aStar - aMin := by
      calc q * x < q * ((aStar - aMin) / q) := by nlinarith
        _ = aStar - aMin := by field_simp
    linarith
  exact hS _ h

/-- The reconnection tax scales as `1/q`: imperfect targeting amplifies the dead zone. -/
theorem dead_zone_scales_as_one_over_q {q aMin aStar : ℝ} (hq : 0 < q) :
    deadZone q aMin aStar = (1 / q) * (aStar - aMin) := by
  rw [deadZone]
  ring

/-- The dead zone is strictly antitone in siting efficiency (given a nondegenerate floor). -/
theorem dead_zone_strictAntiOn_q {aMin aStar : ℝ} (h : aMin < aStar) :
    StrictAntiOn (fun q => deadZone q aMin aStar) (Set.Ioi (0 : ℝ)) := by
  intro q hq q' hq' hqq'
  unfold deadZone
  exact div_lt_div_of_pos_left (by linarith : 0 < aStar - aMin) hq hqq'

/-! ### R5 — template collapse and the latent heat of fragmentation (headline) -/

/-- Latent heat of fragmentation: the discontinuous jump in restoration debt incurred when the
percolation threshold destroys the observable restoration template and siting collapses
`q₁ → q₀`. -/
noncomputable def latentHeat (q0 q1 ΔA : ℝ) : ℝ := (1 / q0 - 1 / q1) * ΔA

/-- The latent heat is exactly the difference of the two debts. -/
theorem latent_heat_eq_debt_gap {q0 q1 ΔA : ℝ} :
    latentHeat q0 q1 ΔA = debt q0 ΔA - debt q1 ΔA := by
  unfold latentHeat debt
  ring

/-- **R5.**  The latent heat is strictly positive exactly when the template is genuinely lost
(`q₀ < q₁`), and vanishes exactly when it is not.  Non-vacuous: both directions are asserted. -/
theorem latent_heat_pos_iff_template_loss {q0 q1 ΔA : ℝ} (h0 : 0 < q0) (h1 : 0 < q1)
    (hΔA : 0 < ΔA) :
    (0 < latentHeat q0 q1 ΔA ↔ q0 < q1) ∧ (latentHeat q0 q1 ΔA = 0 ↔ q0 = q1) := by
  unfold latentHeat
  have key : 1 / q0 - 1 / q1 = (q1 - q0) / (q0 * q1) := by field_simp
  rw [key]
  have hqq : 0 < q0 * q1 := mul_pos h0 h1
  rw [div_mul_eq_mul_div]
  constructor
  · constructor
    · intro h
      have := div_pos_iff.mp h
      rcases this with ⟨hnum, hdenom⟩ | ⟨hnum, hdenom⟩
      · by_contra hc
        push_neg at hc
        have : q1 - q0 ≤ 0 := by linarith
        have : (q1 - q0) * ΔA ≤ 0 := mul_nonpos_of_nonpos_of_nonneg this (le_of_lt hΔA)
        exact hnum.not_ge this
      · linarith
    · intro h
      apply div_pos
      · exact mul_pos (by linarith : 0 < q1 - q0) hΔA
      · exact hqq
  · constructor
    · intro h
      have := div_eq_zero_iff.mp h
      rcases this with hq | hqq'
      · have : q1 - q0 = 0 ∨ ΔA = 0 := mul_eq_zero.mp hq
        rcases this with heq | hΔA0
        · linarith
        · exact absurd hΔA0 hΔA.ne'
      · linarith
    · intro h
      rw [h]
      simp

/-- Siting efficiency as a function of the habitat fraction: informed above the fragmentation
horizon `ac`, uninformed below it. -/
noncomputable def qOf (q0 q1 ac a : ℝ) : ℝ := if a < ac then q0 else q1

/-- **R5 (discontinuity at the horizon).**  Restoration debt is discontinuous at the fragmentation
horizon whenever the template is genuinely lost — a first-order jump on an otherwise continuous
transition. -/
theorem debt_discontinuous_at_horizon {q0 q1 ac ΔA : ℝ} (h0 : 0 < q0) (h01 : q0 < q1)
    (hΔA : 0 < ΔA) :
    ¬ ContinuousAt (fun a => debt (qOf q0 q1 ac a) ΔA) ac := by
  simp only [qOf]
  intro hcont
  -- Define a sequence approaching ac from the left
  let x : ℕ → ℝ := fun n => ac - 1 / (n + 1)
  have hx_lt : ∀ n, x n < ac := fun n => sub_lt_self ac (by positivity)
  have hx_tends : Filter.Tendsto x Filter.atTop (nhds ac) := by
    simp_rw [x]
    have h1 : Filter.Tendsto (fun n : ℕ => (1 : ℝ) / (n + 1)) Filter.atTop (nhds 0) :=
      tendsto_one_div_add_atTop_nhds_zero_nat
    convert tendsto_const_nhds.sub h1 using 1
    ring_nf
  -- The function is constant on the sequence x n (all less than ac)
  have hf_x : ∀ n, debt (if x n < ac then q0 else q1) ΔA = debt q0 ΔA := by
    intro n
    simp [hx_lt n]
  -- So the composition is constant
  have hcomp : Filter.Tendsto (fun n => debt (if x n < ac then q0 else q1) ΔA) Filter.atTop (nhds (debt q0 ΔA)) := by
    simp_rw [hf_x]
    exact tendsto_const_nhds
  -- But continuity requires it to tend to f(ac)
  have hcont_app := hcont.tendsto.comp hx_tends
  -- f(ac) = debt q1 ΔA since ac < ac is false
  have hf_ac : debt (if ac < ac then q0 else q1) ΔA = debt q1 ΔA := by simp
  rw [hf_ac] at hcont_app
  -- These two limits must be equal
  have heq := tendsto_nhds_unique hcomp hcont_app
  -- But debt q0 ΔA ≠ debt q1 ΔA since q0 < q1 and ΔA > 0
  unfold debt at heq
  have : (1 / q0 - 1) = (1 / q1 - 1) := by
    have := mul_right_cancel₀ hΔA.ne' heq
    linarith
  have : 1 / q0 = 1 / q1 := by linarith
  have : q0 = q1 := by
    rw [one_div, one_div, inv_inj] at this
    exact this
  linarith

/-! ### R6 — information–area equivalence -/

/-- Siting efficiency purchased with `I` bits of survey information: each bit halves the candidate
siting set, clamped at the informed ceiling `q₁`. -/
noncomputable def qOfBits (q0 q1 I : ℝ) : ℝ := min q1 (q0 * (2 : ℝ) ^ I)

/-- Required restoration area (overbuild) at survey depth `I`. -/
noncomputable def overshoot (q0 q1 ΔA I : ℝ) : ℝ := ΔA / qOfBits q0 q1 I

/-- Hard saturation depth: the number of bits beyond which further survey is worthless. -/
noncomputable def iStar (q0 q1 : ℝ) : ℝ := logb 2 (q1 / q0)

/-- **R6 (saturation).**  Survey information reaches the informed ceiling exactly at
`I* = log₂(q₁/q₀)` and never before. -/
theorem istar_eq_log2_q1_over_q0 {q0 q1 I : ℝ} (h0 : 0 < q0) (h01 : q0 ≤ q1) :
    qOfBits q0 q1 I = q1 ↔ iStar q0 q1 ≤ I := by
  unfold qOfBits iStar
  rw [min_eq_left_iff]
  constructor
  · intro h
    rw [Real.logb_le_iff_le_rpow (by norm_num : (1 : ℝ) < 2) (div_pos (by linarith : 0 < q1) h0)]
    rw [div_le_iff₀ h0]; linarith
  · intro h
    rw [Real.logb_le_iff_le_rpow (by norm_num : (1 : ℝ) < 2) (div_pos (by linarith : 0 < q1) h0)] at h
    rw [div_le_iff₀ h0] at h; linarith

/-- **R6 (bit-halving law).**  Strictly below saturation, each additional bit of correctly
targeted survey information halves the required restoration area. -/
theorem bit_halves_overshoot_below_saturation {q0 q1 ΔA I : ℝ} (h0 : 0 < q0) (h01 : q0 ≤ q1)
    (hΔA : 0 < ΔA) (hI : I + 1 ≤ iStar q0 q1) :
    overshoot q0 q1 ΔA (I + 1) = overshoot q0 q1 ΔA I / 2 := by
  unfold overshoot qOfBits iStar at *
  -- From hI: I + 1 ≤ logb 2 (q1 / q0), we need q0 * 2^(I+1) ≤ q1
  have hpos : (0 : ℝ) < q1 := by linarith
  have hratio : 0 < q1 / q0 := by positivity
  rw [Real.le_logb_iff_rpow_le (by norm_num : (1 : ℝ) < 2) hratio] at hI
  -- hI : q1 / q0 ≥ 2^(I+1), so q1 ≥ q0 * 2^(I+1)
  have hq1_ge : q1 ≥ q0 * (2 : ℝ) ^ (I + 1) := by
    calc q1 = q0 * (q1 / q0) := by field_simp
      _ ≥ q0 * (2 : ℝ) ^ (I + 1) := by nlinarith
  have hq1_ge_I : q1 ≥ q0 * (2 : ℝ) ^ I := by
    calc q1 ≥ q0 * (2 : ℝ) ^ (I + 1) := hq1_ge
      _ = q0 * (2 : ℝ) ^ I * 2 := by rw [Real.rpow_add (by norm_num : (2 : ℝ) > 0), Real.rpow_one]; ring
      _ ≥ q0 * (2 : ℝ) ^ I := by nlinarith [Real.rpow_pos_of_pos (by norm_num : (2 : ℝ) > 0) I]
  -- Now q0 * 2^(I+1) ≤ q1 and q0 * 2^I ≤ q1
  have hmin_I : min q1 (q0 * (2 : ℝ) ^ I) = q0 * (2 : ℝ) ^ I := min_eq_right hq1_ge_I
  have hmin_I1 : min q1 (q0 * (2 : ℝ) ^ (I + 1)) = q0 * (2 : ℝ) ^ (I + 1) := min_eq_right hq1_ge
  rw [hmin_I, hmin_I1]
  -- Now show ΔA / (q0 * 2^(I+1)) = (ΔA / (q0 * 2^I)) / 2
  rw [Real.rpow_add (by norm_num : (2 : ℝ) > 0), Real.rpow_one]
  rw [div_div]
  congr 1
  conv_rhs => rw [mul_assoc]

/-- **R6 (honest failure across the clamp).**  The halving law is exact ONLY below saturation: a
bit straddling the saturation depth strictly under-delivers.  This theorem asserts the
*failure* of the naive law and must not be provable in the halving range. -/
theorem bit_halving_fails_across_saturation {q0 q1 ΔA I : ℝ} (h0 : 0 < q0) (h01 : q0 < q1)
    (hΔA : 0 < ΔA) (hlo : I < iStar q0 q1) (hhi : iStar q0 q1 < I + 1) :
    overshoot q0 q1 ΔA I / 2 < overshoot q0 q1 ΔA (I + 1) := by
  -- From I < iStar, we get q0 * 2^I < q1, so qOfBits q0 q1 I = q0 * 2^I
  have hqOB_I : qOfBits q0 q1 I = q0 * (2 : ℝ) ^ I := by
    rw [qOfBits]
    apply min_eq_right
    have hIlt : I < logb 2 (q1 / q0) := hlo
    have hpos : 0 < q1 / q0 := div_pos (by linarith) h0
    have hrpow : (2 : ℝ) ^ I < q1 / q0 := by
      have := Real.rpow_lt_rpow_of_exponent_lt (by norm_num : (1 : ℝ) < 2) hIlt
      rw [Real.rpow_logb (by norm_num : (0 : ℝ) < 2) (by norm_num) hpos] at this
      exact this
    have h1 := mul_lt_mul_of_pos_left hrpow h0
    rw [mul_div_assoc', mul_div_cancel_left₀ _ h0.ne'] at h1
    exact le_of_lt h1
  -- From iStar < I + 1, we get q1 < q0 * 2^(I+1), so qOfBits q0 q1 (I+1) = q1
  have hqOB_I1 : qOfBits q0 q1 (I + 1) = q1 := by
    rw [qOfBits]
    apply min_eq_left
    have hI1gt : logb 2 (q1 / q0) < I + 1 := hhi
    have hpos : 0 < q1 / q0 := div_pos (by linarith) h0
    have hrpow : q1 / q0 < (2 : ℝ) ^ (I + 1) := by
      have := Real.rpow_lt_rpow_of_exponent_lt (by norm_num : (1 : ℝ) < 2) hI1gt
      rw [Real.rpow_logb (by norm_num : (0 : ℝ) < 2) (by norm_num) hpos] at this
      exact this
    have h1 := mul_lt_mul_of_pos_left hrpow h0
    rw [mul_div_assoc', mul_div_cancel_left₀ _ h0.ne'] at h1
    exact le_of_lt h1
  -- Now finish: overshoot I / 2 < overshoot (I+1)
  rw [overshoot, overshoot, hqOB_I, hqOB_I1]
  -- Goal: ΔA / (q0 * 2^I) / 2 < ΔA / q1
  -- Need: q1 < q0 * 2^(I+1)
  have hI1gt : logb 2 (q1 / q0) < I + 1 := hhi
  have hpos : 0 < q1 / q0 := div_pos (by linarith) h0
  have hrpow : q1 / q0 < (2 : ℝ) ^ (I + 1) := by
    have := Real.rpow_lt_rpow_of_exponent_lt (by norm_num : (1 : ℝ) < 2) hI1gt
    rw [Real.rpow_logb (by norm_num : (0 : ℝ) < 2) (by norm_num) hpos] at this
    exact this
  have hq1_lt : q1 < q0 * (2 : ℝ) ^ (I + 1) := by
    have h1 := mul_lt_mul_of_pos_left hrpow h0
    rw [mul_div_assoc', mul_div_cancel_left₀ _ h0.ne'] at h1
    exact h1
  have hq0_2I_pos : 0 < q0 * (2 : ℝ) ^ I := mul_pos h0 (Real.rpow_pos_of_pos (by norm_num) _)
  have hq1_pos : 0 < q1 := by linarith
  rw [div_div, mul_comm (q0 * 2 ^ I) 2]
  apply div_lt_div_of_pos_left hΔA (by positivity)
  convert hq1_lt using 1
  rw [Real.rpow_add (by norm_num : (2 : ℝ) > 0), Real.rpow_one]
  ring

/-- **R6 (marginal value of a bit).**  Below saturation the marginal bit is worth exactly `ln 2 ×`
the current overbuild area. -/
theorem marginal_bit_eq_ln2_times_overshoot {q0 ΔA I : ℝ} (h0 : 0 < q0) :
    HasDerivAt (fun J : ℝ => ΔA / (q0 * (2 : ℝ) ^ J))
      (-(Real.log 2) * (ΔA / (q0 * (2 : ℝ) ^ I))) I := by
  have h2pos : (0 : ℝ) < 2 := by norm_num
  have hrpow : HasDerivAt (fun J : ℝ => (2 : ℝ) ^ J) ((2 : ℝ) ^ I * Real.log 2) I := by
    have h2pos' : (0 : ℝ) < 2 := by norm_num
    have h : (fun J : ℝ => (2 : ℝ) ^ J) = fun J => Real.exp (J * Real.log 2) := by
      ext J
      rw [Real.rpow_def_of_pos h2pos']
      ring_nf
    rw [h]
    have := Real.hasDerivAt_exp (I * Real.log 2)
    have hchain := this.comp I (hasDerivAt_mul_const (Real.log 2))
    simp at hchain
    rw [Real.rpow_def_of_pos h2pos']
    convert hchain using 2 <;> ring_nf
  -- Now we need to differentiate ΔA / (q0 * 2^J)
  have h2ne : (2 : ℝ) ^ I ≠ 0 := by positivity
  have hq0ne : q0 ≠ 0 := h0.ne'
  have hprod_ne : q0 * (2 : ℝ) ^ I ≠ 0 := mul_ne_zero hq0ne h2ne
  -- Rewrite as (ΔA / q0) * (2^J)⁻¹
  have heq : (fun J : ℝ => ΔA / (q0 * (2 : ℝ) ^ J)) = (fun J => (ΔA / q0) * ((2 : ℝ) ^ J)⁻¹) := by
    ext J
    field_simp
  rw [heq]
  -- Use HasDerivAt.const_mul and the chain rule for (2^J)⁻¹
  -- First, get the derivative of (2^J)⁻¹
  have hrpow_inv : HasDerivAt (fun J : ℝ => ((2 : ℝ) ^ J)⁻¹) (-((2 : ℝ) ^ I * Real.log 2) / ((2 : ℝ) ^ I) ^ 2) I := by
    have := hrpow.inv h2ne
    simp at this
    convert this using 1
  -- Now multiply by the constant ΔA / q0
  have hconst_mul := hrpow_inv.const_mul (ΔA / q0)
  simp at hconst_mul
  convert hconst_mul using 1
  field_simp

/-- Total programme cost at survey depth `I`: restoration area at `c_A` per unit area plus survey
at `c_I` per bit. -/
noncomputable def totalCost (q0 ΔA cA cI I : ℝ) : ℝ := cA * (ΔA / (q0 * (2 : ℝ) ^ I)) + cI * I

/-- Closed-form unconstrained survey depth. -/
noncomputable def iFree (q0 ΔA cA cI : ℝ) : ℝ := logb 2 (Real.log 2 * ΔA * cA / (cI * q0))

/-- **R6 (stopping rule).**  The closed-form survey depth is a global minimiser of programme cost:
an explicit rule for when to stop surveying. -/
theorem iopt_closed_form_is_global_min {q0 ΔA cA cI : ℝ} (h0 : 0 < q0) (hΔA : 0 < ΔA)
    (hA : 0 < cA) (hI : 0 < cI) :
    ∀ I : ℝ, totalCost q0 ΔA cA cI (iFree q0 ΔA cA cI) ≤ totalCost q0 ΔA cA cI I := by
  intro I
  unfold totalCost iFree
  -- Let r = ln(2) * ΔA * cA / (cI * q0), then iFree = logb 2 r and 2^iFree = r
  set r := Real.log 2 * ΔA * cA / (cI * q0) with hr_def
  have hr_pos : 0 < r := by positivity
  have h2r : (2 : ℝ) ^ logb 2 r = r := by
    apply Real.rpow_logb
    · norm_num
    · norm_num
    · exact hr_pos
  rw [h2r]
  -- Simplify cA * (ΔA / (q0 * r)) = cI / ln 2
  have hcA_delta : cA * (ΔA / (q0 * r)) = cI / Real.log 2 := by
    rw [hr_def]
    field_simp
  rw [hcA_delta]
  -- Rewrite cA * (ΔA / (q0 * 2^I)) using r
  have hcost_term : cA * (ΔA / (q0 * 2 ^ I)) = cI * r / (Real.log 2 * 2 ^ I) := by
    rw [hr_def]
    field_simp
  rw [hcost_term]
  -- Factor out cI and use substitution x = 2^I
  have hx_pos : (0 : ℝ) < 2 ^ I := by positivity
  set x := (2 : ℝ) ^ I with hx_def
  have hI_eq : I = logb 2 x := by
    rw [hx_def]
    rw [Real.logb_rpow (by norm_num : (0 : ℝ) < 2) (by norm_num : (2 : ℝ) ≠ 1)]
  rw [hI_eq]
  -- The inequality becomes: cI/ln2 + cI*logb2(r) ≤ cI*r/(ln2*x) + cI*logb2(x)
  -- Divide by cI > 0: 1/ln2 + logb2(r) ≤ r/(ln2*x) + logb2(x)
  -- Multiply by ln2: 1 + ln(r) ≤ r/x + ln(x)
  -- Rearrange: 1 + ln(r/x) ≤ r/x
  -- Let y = r/x: 1 + ln(y) ≤ y, which is ln(y) ≤ y - 1
  have hcI_pos : 0 < cI := hI
  have hln2_pos : 0 < Real.log 2 := Real.log_pos (by norm_num : (1 : ℝ) < 2)
  have hgoal : 1 + Real.log r ≤ r / x + Real.log x := by
    have key : ∀ y : ℝ, 0 < y → Real.log y ≤ y - 1 := fun y hy => Real.log_le_sub_one_of_pos hy
    have hy_pos : 0 < r / x := div_pos hr_pos hx_pos
    have h_ineq : Real.log (r / x) ≤ r / x - 1 := key (r / x) hy_pos
    rw [Real.log_div (ne_of_gt hr_pos) (ne_of_gt hx_pos)] at h_ineq
    linarith
  -- Convert logb to log / log 2 and use hgoal
  simp only [Real.logb]
  -- Goal: cI / log 2 + cI * (log r / log 2) ≤ cI * r / (log 2 * x) + cI * (log x / log 2)
  -- Factor: cI / log 2 * (1 + log r) ≤ cI / log 2 * (r / x + log x)
  have factored : cI / Real.log 2 + cI * (Real.log r / Real.log 2) = cI / Real.log 2 * (1 + Real.log r) := by ring
  have factored_rhs : cI * r / (Real.log 2 * x) + cI * (Real.log x / Real.log 2) = cI / Real.log 2 * (r / x + Real.log x) := by
    field_simp
  rw [factored, factored_rhs]
  exact mul_le_mul_of_nonneg_left hgoal (div_nonneg (le_of_lt hcI_pos) (le_of_lt hln2_pos))

/-- Programme cost is convex in survey depth, so clipping the closed-form optimum to the feasible
band `[0, I*]` still minimises. -/
theorem totalCost_convexOn {q0 ΔA cA cI : ℝ} (h0 : 0 < q0) (hΔA : 0 < ΔA) (hA : 0 < cA) :
    ConvexOn ℝ Set.univ (totalCost q0 ΔA cA cI) := by
  unfold totalCost
  have hA' : 0 < cA * ΔA / q0 := by positivity
  set A := cA * ΔA / q0 with hA_def
  refine ⟨convex_univ, ?_⟩
  intro x _ y _ a b ha hb hab
  simp only [smul_eq_mul]
  -- Rewrite as: A * 2^(-ax-by) + cI*(ax+by) ≤ A*(a*2^(-x) + b*2^(-y)) + cI*(ax+by)
  -- where A = cA * ΔA / q0 > 0
  -- This reduces to showing: 2^(-ax-by) ≤ a * 2^(-x) + b * 2^(-y)
  -- which is Jensen's inequality for the convex function t ↦ 2^(-t)
  have key : (2 : ℝ) ^ (- (a * x + b * y)) ≤ a * (2 : ℝ) ^ (-x) + b * (2 : ℝ) ^ (-y) := by
    -- 2^t = exp(t * log 2), and exp is convex
    simp only [Real.rpow_def_of_pos (by norm_num : (0 : ℝ) < 2)]
    -- Goal: exp(log 2 * -(a * x + b * y)) ≤ a * exp(log 2 * -x) + b * exp(log 2 * -y)
    -- Let c = log 2 > 0
    -- This is: exp(-c * (a * x + b * y)) ≤ a * exp(-c * x) + b * exp(-c * y)
    -- Let f(t) = exp(-c * t), which is convex
    have hconv : ConvexOn ℝ Set.univ Real.exp := by
      exact convexOn_exp
    -- Rewrite: log 2 * -(a * x + b * y) = a * (log 2 * -x) + b * (log 2 * -y)
    have eq1 : log 2 * -(a * x + b * y) = a * (log 2 * -x) + b * (log 2 * -y) := by ring
    rw [eq1]
    exact hconv.2 (Set.mem_univ _) (Set.mem_univ _) ha hb hab
  -- Now use key to prove the main goal
  -- Rewrite using: ΔA / (q0 * 2^I) = (ΔA/q0) * 2^(-I)
  have eq_simp : ∀ I : ℝ, ΔA / (q0 * (2 : ℝ) ^ I) = (ΔA / q0) * (2 : ℝ) ^ (-I) := by
    intro I
    rw [Real.rpow_neg (by norm_num : (0 : ℝ) ≤ 2)]
    field_simp
  -- Rewrite the goal using eq_simp
  simp_rw [eq_simp]
  -- Now goal is: cA * (ΔA/q0 * 2^-(ax+by)) + cI*(ax+by) ≤ a*(cA*(ΔA/q0 * 2^-x) + cI*x) + b*(cA*(ΔA/q0 * 2^-y) + cI*y)
  -- Expand RHS
  ring_nf
  -- The cI terms cancel; we need: hA' * 2^(-(ax) - by) ≤ hA' * (a * 2^(-x) + b * 2^(-y))
  -- Note: -(ax) - by = -(a*x + b*y)
  have eq2 : -(a * x) - b * y = -(a * x + b * y) := by ring
  rw [eq2]
  have h1 : cA * ΔA * q0⁻¹ = A := by rw [hA_def]; field_simp
  rw [h1]
  nlinarith [key]

/-- **R6 (clipped stopping rule).**  `I_opt = clip(iFree, 0, I*)` minimises cost on the feasible
band. -/
theorem iopt_clipped_min_on_Icc {q0 q1 ΔA cA cI : ℝ} (h0 : 0 < q0) (h01 : q0 < q1)
    (hΔA : 0 < ΔA) (hA : 0 < cA) (hI : 0 < cI) :
    ∀ I ∈ Set.Icc (0 : ℝ) (iStar q0 q1),
      totalCost q0 ΔA cA cI (max 0 (min (iStar q0 q1) (iFree q0 ΔA cA cI)))
        ≤ totalCost q0 ΔA cA cI I := by
  intro I hI_mem
  -- Let's define the clipped optimum
  set I_star := iStar q0 q1 with hI_star
  set I_free := iFree q0 ΔA cA cI with hI_free
  set I_opt := max 0 (min I_star I_free) with hI_opt
  -- iStar q0 q1 = logb 2 (q1 / q0) ≥ 0 since q0 < q1 implies q1/q0 > 1
  have hiStar_nonneg : 0 ≤ iStar q0 q1 := by
    unfold iStar
    apply Real.logb_nonneg (by norm_num : (1 : ℝ) < 2)
    rw [one_le_div h0]
    linarith
  -- The clipped optimum is in [0, I_star]
  have hI_opt_mem : I_opt ∈ Set.Icc 0 I_star := by
    simp only [Set.mem_Icc, hI_opt]
    exact ⟨le_max_left _ _, max_le hiStar_nonneg (min_le_left _ _)⟩
  -- Consider three cases: I_free < 0, I_free > I_star, or I_free ∈ [0, I_star]
  by_cases hI_free_neg : I_free < 0
  · -- Case: I_free < 0, so I_opt = 0
    have hI_opt_eq : I_opt = 0 := by
      apply max_eq_left
      linarith [min_le_right I_star I_free]
    rw [hI_opt_eq]
    -- Since totalCost is convex and has minimum at I_free < 0, it's monotone increasing on [0, I_star]
    have hconv := totalCost_convexOn h0 hΔA hA (cI := cI)
    -- Use the three-point property of convex functions
    by_cases hI_eq_zero : I = 0
    · simp [hI_eq_zero]
    · have hI_pos : 0 < I := lt_of_le_of_ne hI_mem.1 (Ne.symm hI_eq_zero)
      -- Express 0 as convex combination: 0 = (1-t)*I_free + t*I where t = -I_free / (I - I_free)
      set t := -I_free / (I - I_free) with ht_def
      have hI_sub_I_free_pos : 0 < I - I_free := by linarith
      have ht_pos : 0 < t := div_pos (by linarith : 0 < -I_free) hI_sub_I_free_pos
      have ht_le_one : t ≤ 1 := by
        rw [div_le_one hI_sub_I_free_pos]
        linarith
      have h1mt_nonneg : 0 ≤ 1 - t := by linarith
      -- By convexity: f(0) ≤ (1-t)*f(I_free) + t*f(I)
      have h0_eq_comb : (0 : ℝ) = (1 - t) * I_free + t * I := by
        rw [ht_def]
        field_simp
        ring
      have hconv_ineq := hconv.2 (Set.mem_univ I_free) (Set.mem_univ I)
        h1mt_nonneg (le_of_lt ht_pos) (by linarith : (1 - t) + t = 1)
      have h0_eq_comb' : (1 - t) • I_free + t • I = 0 := by simp [h0_eq_comb]
      rw [h0_eq_comb'] at hconv_ineq
      simp only [smul_eq_mul] at hconv_ineq
      -- f(I_free) ≤ f(0) since I_free is global min
      have hglob := iopt_closed_form_is_global_min h0 hΔA hA hI 0
      nlinarith [mul_nonneg h1mt_nonneg (le_of_lt ht_pos)]
  · by_cases hI_free_gt : I_free > I_star
    · -- Case: I_free > I_star, so I_opt = I_star
      have hI_opt_eq : I_opt = I_star := by
        show max 0 (min I_star I_free) = I_star
        rw [min_eq_left (by linarith : I_star ≤ I_free), max_eq_right hiStar_nonneg]
      rw [hI_opt_eq]
      -- Since totalCost is convex and has minimum at I_free > I_star, it's monotone decreasing on [0, I_star]
      have hconv := totalCost_convexOn h0 hΔA hA (cI := cI)
      -- Express I_star as convex combination: I_star = (1-t)*I + t*I_free where t = (I_star - I) / (I_free - I)
      set t := (I_star - I) / (I_free - I) with ht_def
      have hI_free_sub_I_pos : 0 < I_free - I := by linarith [hI_mem.2]
      have hI_le_I_star : I ≤ I_star := hI_mem.2
      -- Handle case I = I_star trivially
      by_cases hI_eq_I_star : I = I_star
      · simp [hI_eq_I_star]
      · have hI_lt_I_star' : I < I_star := lt_of_le_of_ne hI_le_I_star hI_eq_I_star
        have ht_pos : 0 < t := div_pos (by linarith) hI_free_sub_I_pos
        have ht_lt_one : t < 1 := by
          rw [div_lt_one hI_free_sub_I_pos]
          linarith
        have h1mt_pos : 0 < 1 - t := by linarith
        -- By convexity: f(I_star) ≤ (1-t)*f(I) + t*f(I_free)
        have hI_star_eq_comb : (I_star : ℝ) = (1 - t) * I + t * I_free := by
          rw [ht_def]
          field_simp
          ring
        have hconv_ineq := hconv.2 (Set.mem_univ I) (Set.mem_univ I_free)
          (le_of_lt h1mt_pos) (le_of_lt ht_pos) (by linarith : (1 - t) + t = 1)
        have hI_star_eq_comb' : (1 - t) • I + t • I_free = I_star := by simp [hI_star_eq_comb]
        rw [hI_star_eq_comb'] at hconv_ineq
        simp only [smul_eq_mul] at hconv_ineq
        -- f(I_free) ≤ f(I_star) since I_free is global min
        have hglob := iopt_closed_form_is_global_min h0 hΔA hA hI I_star
        nlinarith [mul_pos h1mt_pos ht_pos]
    · -- Case: I_free ∈ [0, I_star], so I_opt = I_free
      have hI_free_in_Icc : I_free ∈ Set.Icc 0 I_star := by
        constructor <;> linarith
      have hI_opt_eq : I_opt = I_free := by
        show max 0 (min I_star I_free) = I_free
        rw [min_eq_right hI_free_in_Icc.2, max_eq_right hI_free_in_Icc.1]
      rw [hI_opt_eq]
      -- I_free is the global minimum
      exact iopt_closed_form_is_global_min h0 hΔA hA hI I

/-! ### R7 — the Mender: the survey race condition against the Intelligence Bound -/

/-- Minimum sensing power required to acquire the saturating survey depth before a landscape
degrading at rate `δ` reaches its fragmentation horizon. -/
noncomputable def pMin (kB T D δ q0 q1 aNow ac : ℝ) : ℝ :=
  kB * T * Real.log 2 * δ * iStar q0 q1 / (D * (aNow - ac))

/-- **R7 (survey race condition).**  If an Intelligence-Bound-limited survey programme
(`dI/dt ≤ P·D/(k_B T ln 2)`) acquires the saturating depth `I*` before the horizon arrives at
`t_h = (aNow - ac)/δ`, then its sensing power was at least `P_min`. -/
theorem survey_race_requires_pMin {kB T D δ P dIdt q0 q1 aNow ac : ℝ}
    (hkB : 0 < kB) (hT : 0 < T) (hD : 0 < D) (hδ : 0 < δ) (hgap : ac < aNow)
    (hIB : dIdt ≤ P * D / (kB * T * Real.log 2))
    (hrate : 0 ≤ dIdt)
    (hreach : iStar q0 q1 ≤ dIdt * ((aNow - ac) / δ)) :
    pMin kB T D δ q0 q1 aNow ac ≤ P := by
  unfold pMin
  have hlog : Real.log 2 > 0 := Real.log_pos (by norm_num : (1 : ℝ) < 2)
  have hkB_T_log : kB * T * Real.log 2 > 0 := by positivity
  have hD_pos : D * (aNow - ac) > 0 := by nlinarith
  have h_ne : aNow - ac ≠ 0 := by linarith
  have hr_ne : δ ≠ 0 := hδ.ne'
  have hrate_pos : 0 ≤ (aNow - ac) / δ := div_nonneg (by linarith : 0 ≤ aNow - ac) (le_of_lt hδ)
  have hkey : iStar q0 q1 ≤ P * D / (kB * T * Real.log 2) * ((aNow - ac) / δ) := by
    calc iStar q0 q1 ≤ dIdt * ((aNow - ac) / δ) := hreach
      _ ≤ (P * D / (kB * T * Real.log 2)) * ((aNow - ac) / δ) := by
        gcongr
  calc kB * T * Real.log 2 * δ * iStar q0 q1 / (D * (aNow - ac))
      ≤ kB * T * Real.log 2 * δ * (P * D / (kB * T * Real.log 2) * ((aNow - ac) / δ)) / (D * (aNow - ac)) := by
        gcongr
    _ = P := by field_simp [h_ne, hr_ne]

/-- **R7 (achievability / non-vacuity of the race).**  Conversely, a programme running at the
Intelligence-Bound-saturating rate with `P ≥ P_min` does acquire the full `I*` before the
horizon — so `P_min` is tight, not merely necessary. -/
theorem pMin_sufficient_at_IB_rate {kB T D δ P q0 q1 aNow ac : ℝ}
    (hkB : 0 < kB) (hT : 0 < T) (hD : 0 < D) (hδ : 0 < δ) (hgap : ac < aNow)
    (hP : pMin kB T D δ q0 q1 aNow ac ≤ P) :
    iStar q0 q1 ≤ (P * D / (kB * T * Real.log 2)) * ((aNow - ac) / δ) := by
  unfold pMin at hP
  have hlog : Real.log 2 > 0 := Real.log_pos (by norm_num : (1 : ℝ) < 2)
  have hkB_T_log : kB * T * Real.log 2 > 0 := by positivity
  have hD_pos : D * (aNow - ac) > 0 := by nlinarith
  have h_ne : aNow - ac ≠ 0 := by linarith
  have hr_ne : δ ≠ 0 := hδ.ne'
  have hdenom_pos : kB * T * Real.log 2 * δ > 0 := by positivity
  -- From hP: kB * T * log 2 * δ * iStar / (D * (aNow - ac)) ≤ P
  -- Multiply both sides by (D * (aNow - ac)) to get:
  -- kB * T * log 2 * δ * iStar ≤ P * (D * (aNow - ac))
  have h1 : kB * T * Real.log 2 * δ * iStar q0 q1 ≤ P * (D * (aNow - ac)) := by
    have := mul_le_mul_of_nonneg_right hP (le_of_lt hD_pos)
    rwa [div_mul_cancel₀ _ (ne_of_gt hD_pos)] at this
  -- Divide both sides by (kB * T * log 2 * δ) to get:
  -- iStar ≤ P * (D * (aNow - ac)) / (kB * T * log 2 * δ)
  have h2 : iStar q0 q1 ≤ P * (D * (aNow - ac)) / (kB * T * Real.log 2 * δ) := by
    rw [le_div_iff₀' hdenom_pos]
    linarith
  convert h2 using 1
  field_simp

/-- **R7 (divergence at the horizon).**  The minimum sensing power diverges as the landscape
approaches its fragmentation horizon: a monitoring programme that starts too late can never win. -/
theorem pMin_diverges_at_horizon {kB T D δ q0 q1 ac : ℝ}
    (hkB : 0 < kB) (hT : 0 < T) (hD : 0 < D) (hδ : 0 < δ) (h0 : 0 < q0) (h01 : q0 < q1) :
    Filter.Tendsto (fun aNow => pMin kB T D δ q0 q1 aNow ac) (nhdsWithin ac (Set.Ioi ac))
      Filter.atTop := by
  unfold pMin
  have hi : 0 < iStar q0 q1 := by
    unfold iStar
    exact logb_pos (by norm_num : (1 : ℝ) < 2) (by rw [lt_div_iff₀ h0]; linarith)
  have hlog2 : 0 < log 2 := Real.log_pos (by norm_num)
  have hnum : 0 < kB * T * log 2 * δ * iStar q0 q1 := by
    apply mul_pos
    · apply mul_pos
      · apply mul_pos
        · apply mul_pos hkB hT
        · exact hlog2
      · exact hδ
    · exact hi
  have hdenom_tendsto : Filter.Tendsto (fun aNow => D * (aNow - ac)) (nhdsWithin ac (Set.Ioi ac)) (nhdsWithin 0 (Set.Ioi 0)) := by
    apply tendsto_nhdsWithin_of_tendsto_nhds_of_eventually_within
    · show Filter.Tendsto (fun aNow => D * (aNow - ac)) _ _
      have h1 : Filter.Tendsto (fun aNow : ℝ => aNow - ac) (nhds ac) (nhds 0) := by
        convert Filter.tendsto_id.sub_const ac using 1
        norm_num
      exact Filter.Tendsto.const_mul D (h1.mono_left nhdsWithin_le_nhds) |> fun h => h.trans (by simp)
    · filter_upwards [self_mem_nhdsWithin] with x hx using Set.mem_Ioi.mpr (by nlinarith [Set.mem_Ioi.mp hx])
  have h_div : Filter.Tendsto (fun aNow => kB * T * log 2 * δ * iStar q0 q1 / (D * (aNow - ac)))
      (nhdsWithin ac (Set.Ioi ac)) Filter.atTop := by
    apply Filter.Tendsto.const_mul_atTop hnum
    have hinv : Filter.Tendsto (fun x : ℝ => x⁻¹) (nhdsWithin 0 (Set.Ioi 0)) Filter.atTop :=
      tendsto_inv_nhdsGT_zero
    exact hinv.comp hdenom_tendsto
  exact h_div

/-- **R7 (the ceiling is never violated).**  No survey programme acquires information faster than
the Intelligence Bound allows over any horizon window. -/
theorem mender_ib_ceiling_never_violated {kB T D δ P dIdt aNow ac : ℝ}
    (hkB : 0 < kB) (hT : 0 < T) (hδ : 0 < δ) (hgap : ac < aNow)
    (hIB : dIdt ≤ P * D / (kB * T * Real.log 2)) :
    dIdt * ((aNow - ac) / δ) ≤ (P * D / (kB * T * Real.log 2)) * ((aNow - ac) / δ) := by
  apply mul_le_mul_of_nonneg_right hIB
  exact div_nonneg (sub_nonneg.mpr (le_of_lt hgap)) (le_of_lt hδ)

/-! ### Non-vacuity witnesses (mandatory — a vacuous proof of this file is a failure) -/

/-- The paper's worked example: `q₁ = 0.85` informed, `q₀ = 0.12` uninformed, `ΔA = 0.35`.
Witnesses every hypothesis with a strictly positive latent heat, an informed multiplier below
`1.2 : 1`, an uninformed multiplier above `8 : 1`, and a strictly interior saturation depth of
under three bits. -/
theorem fht_nonvacuous :
    (0 : ℝ) < 0.12 ∧ (0.12 : ℝ) < 0.85 ∧ (0.85 : ℝ) ≤ 1 ∧ (0 : ℝ) < 0.35 ∧
      0 < latentHeat 0.12 0.85 0.35 ∧
      xStar 0.85 0.35 / 0.35 < 1.2 ∧
      (8 : ℝ) < xStar 0.12 0.35 / 0.35 ∧
      2 < iStar 0.12 0.85 ∧ iStar 0.12 0.85 < 3 := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, ?_, ?_, ?_, ?_, ?_⟩
  · -- 0 < latentHeat 0.12 0.85 0.35
    simp [latentHeat]
    norm_num
  · -- xStar 0.85 0.35 / 0.35 < 1.2
    simp [xStar]
    norm_num
  · -- 8 < xStar 0.12 0.35 / 0.35
    simp [xStar]
    norm_num
  · -- 2 < iStar 0.12 0.85
    simp [iStar]
    rw [Real.lt_logb_iff_rpow_lt (by norm_num : (1 : ℝ) < 2) (by norm_num : (0 : ℝ) < 0.85 / 0.12)]
    norm_num
  · -- iStar 0.12 0.85 < 3
    simp [iStar]
    rw [Real.logb_lt_iff_lt_rpow (by norm_num : (1 : ℝ) < 2) (by norm_num : (0 : ℝ) < 0.85 / 0.12)]
    norm_num

/-- A concrete strictly monotone continuous order parameter with a strictly positive hysteresis
loop area: the Second Law statement above is not vacuous. -/
theorem fht_cycle_work_pos_witness :
    0 < cycleWork (fun a => a) (1 / 2) 0 1 := by
  exact cycle_work_pos_of_q_lt_one strictMono_id continuous_id (by norm_num) (by norm_num)
    (by norm_num)

end Viridis.Mender.FragmentationHysteresis
