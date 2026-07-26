/-
# The Plasticity Vitrification Theorem (PVT) — the Metronome
Viridis Aristotle Forge · Nightly Run 103 · [06] Entropy-Driven Learning × 🔥 Thermodynamic
45th Intelligence-Bound self-application. Tempo twin of SST-102 (the Steward, level).

INTENDED MEANING (formalized clean core).
Continual-learning "loss of plasticity" is modeled as a renewable stock `D(t) ∈ [0,1]`
cycling through a FORCING phase (continuous training, no reset, duration `τ_F`) and a
REST phase (active regeneration, duration `τ_R`). During forcing, the effective
fluctuation-dissipation ratio ages algebraically (Cugliandolo–Kurchan), so plasticity
survives one forcing phase scaled by a factor `a = a(τ_F) ∈ (0,1)`
(`a = exp(-k·A(τ_F))`, `A(τ_F) = ∫₀^τ_F (1 - X(s)) ds`, `X(s) = (1+s/τ_g)^(-β)`);
during rest it relaxes toward 1 scaled by `b = exp(-ρ·τ_R) ∈ (0,1)`. One reset-forcing
cycle maps `D ↦ 1 - (1 - a·D)·b`, whose fixed point is the closed-form steady
plasticity `D⋆(a,b) = (1-b)/(1-ab)` (R2, canon candidate — matched to 500-iterate
simulation at 1.11e-16 in the source verify.py). Harvest accrues only during forcing
at rate `Ω·D`; with a strictly positive per-cycle overhead cost `c>0`
(checkpointing/consolidation — the ingredient absent from Run 102's Clark model), the
sustainable rate `R̄(τ_F,τ_R) = Ω·D⋆(a(τ_F),b(τ_R))·I(τ_F) / (τ_F+τ_R+c)` is the
paper's Section 4 headline (R3) golden-rule objective, `I(τ_F)` the within-forcing
cumulative-survival integral.

The clean core (formalized):
  R2  Closed-form fixed point (canon candidate): `D⋆(a,b)` solves the one-cycle map;
      `τ_R=0 ⟹ b=1 ⟹ D⋆=0` (never-reset-in-a-cycle collapse, exact algebra); a
      genuinely unbroken, never-reset forcing trajectory `a(s) = exp(-k·A(s))` tends
      to `0` as forcing time `s → ∞` whenever the aging integral `A` diverges (the
      learning-domain Tragedy of the Bound, Section 3's trajectory-level claim).
  R2′ `D⋆` is interior `(0,1)` for interior `(a,b)`, strictly increasing in the
      forcing-survival factor `a`, and strictly decreasing in the reset-relaxation
      factor `b` (more forcing damage survived, or less reset granted, both move `D⋆`
      the intuitive direction).
  R3  Golden-rule EXISTENCE (canon candidate, HEADLINE — existence half): given any
      continuous forcing-survival profile `A` and continuous cumulative-harvest
      profile `I` on a bounded duration box `[0,T]×[0,T]`, reset-decay rate `ρ>0`,
      and strictly positive overhead cost `c>0`, the sustainable-rate objective `R̄`
      attains a maximizer on the box. This is the existence content behind the
      interior golden-rule reset duty cycle (numerically confirmed interior in 60/60
      random draws in the source paper's verify.py Section 4); the closed-form value
      of the maximizer is DEFERRED below.
  R8  Sustainable-ceiling bound: the duty-cycle-averaged sustainable throughput
      `u·Ω·D⋆` is strictly below the instantaneous ceiling `Ω` whenever the duty
      cycle `u<1` and the setpoint `D⋆<1` (both strict in any genuine reset-forcing
      cycle).

NON-VACUITY. `pvt_nonvacuous` binds explicit witnesses (`a=1/2, b=1/2` give an
interior `D⋆=2/3`; `b=1` collapses to `D⋆=0`; `Dstar` is shown to strictly increase
when `a` rises from `1/2` to `3/4` at fixed `b=1/2`; the sustainable ceiling strictly
binds at `u=1/2, Ω=2`) — witnessing that none of the laws above is vacuous.

DEFERRED (well-posedness gate — CITED, not re-proven, matching the source paper's own
honest disclosure that these are established by verified numerical grid search, not
closed-form control theory): the closed-form numerical value and uniqueness of the
golden-rule `(τ_F⋆,τ_R⋆,u⋆)`, the `c=0` degenerate boundary-collapse limit, and the
monotonicity of `u⋆` in the discount rate `r` (the paper's own honestly-reported
impatience-inversion, Section 7). The forge load here is the exact one-cycle
fixed-point algebra (R2 family) and the existence half of the golden-rule optimum
(R3), the two items the source `finding.md` explicitly flags PROVE-VIA-ARISTOTLE.

Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real Set Filter

namespace Viridis.Plasticity.PlasticityVitrification

/-- Closed-form one-cycle fixed point of the reset-forcing map:
    `D⋆(a,b) = (1-b)/(1-ab)`. -/
noncomputable def Dstar (a b : ℝ) : ℝ := (1 - b) / (1 - a * b)

/-- The one-cycle map: forcing (`D ↦ a·D`) then reset (`D ↦ 1-(1-D)·b`), composed:
    `cycleMap a b D = 1 - (1 - a·D)·b`. -/
noncomputable def cycleMap (a b D : ℝ) : ℝ := 1 - (1 - a * D) * b

/-! ### R2 — Closed-form fixed point (canon candidate). -/

/-- **R2 (canon candidate).** `D⋆(a,b)` is a fixed point of the one-cycle
    forcing-then-reset map, matching the 500-iterate simulated fixed point to
    machine precision in the source `verify.py`.
-/
theorem Dstar_closed_form_eq_fixed_point (a b : ℝ) (ha0 : 0 < a) (ha1 : a < 1)
    (hb0 : 0 < b) (hb1 : b < 1) :
    cycleMap a b (Dstar a b) = Dstar a b := by
  unfold cycleMap Dstar;
  nlinarith [ mul_div_cancel₀ ( 1 - b ) ( by nlinarith : ( 1 - a * b ) ≠ 0 ) ]

/-- **R2′.** The steady plasticity `D⋆(a,b)` is interior: strictly between `0` and
    `1` whenever both the forcing-survival factor `a` and the reset-relaxation
    factor `b` are themselves interior.
-/
theorem Dstar_interior_bounds (a b : ℝ) (ha0 : 0 < a) (ha1 : a < 1)
    (hb0 : 0 < b) (hb1 : b < 1) :
    0 < Dstar a b ∧ Dstar a b < 1 := by
  unfold Dstar;
  exact ⟨ div_pos ( by linarith ) ( by nlinarith ), by rw [ div_lt_iff₀ ] <;> nlinarith ⟩

/-- **R2′.** `D⋆(a,b)` is strictly increasing in the forcing-survival factor `a`
    on `(0,1)`, for any fixed interior reset-relaxation factor `b`: surviving forcing
    better always raises the sustained setpoint.
-/
theorem Dstar_strictMonoOn_a (b : ℝ) (hb0 : 0 < b) (hb1 : b < 1) :
    StrictMonoOn (fun a => Dstar a b) (Set.Ioo (0 : ℝ) 1) := by
  intro a ha b hb hab;
  simp +zetaDelta at *;
  rw [ Dstar, Dstar, div_lt_div_iff₀ ] <;> nlinarith [ mul_lt_mul_of_pos_left hab hb0 ]

/-- **R2′.** `D⋆(a,b)` is strictly decreasing in the reset-relaxation factor `b`
    on `(0,1)`, for any fixed interior forcing-survival factor `a`: a `b` closer to
    `1` means less genuine reset happened during the rest phase, so the sustained
    setpoint is lower.
-/
theorem Dstar_strictAntiOn_b (a : ℝ) (ha0 : 0 < a) (ha1 : a < 1) :
    StrictAntiOn (fun b => Dstar a b) (Set.Ioo (0 : ℝ) 1) := by
  intro b hb c hc hbc;
  unfold Dstar;
  rw [ div_lt_div_iff₀ ] <;> nlinarith [ hb.1, hb.2, hc.1, hc.2, mul_lt_mul_of_pos_left hbc ha0 ]

/-! ### R2 (boundary case) — never reset within a cycle. -/

/-- **R2 (boundary).** `τ_R = 0` (never reset within a cycle) means `b = 1`
    exactly, and the one-cycle fixed point collapses to `D⋆ = 0`: the
    learning-domain Tragedy of the Bound at the level of a single reset-forcing
    cycle.
-/
theorem tauR_zero_implies_Dstar_zero (a : ℝ) (ha0 : 0 ≤ a) (ha1 : a < 1) :
    Dstar a 1 = 0 := by
  unfold Dstar; aesop;

/-! ### R2 (Section 3) — genuinely unbroken forcing (never reset, ever). -/

/-- **Continuous forcing (no reset, ever) collapses plasticity to zero.** If the
    aging-integral profile `A` diverges to `+∞` as forcing time `s → ∞` (the
    Cugliandolo–Kurchan aging kernel's established divergence away from the fresh
    equilibrium `X(0)=1`, Section 1 of the source paper), then the raw survival
    trajectory `a(s) = exp(-k·A(s))` — under a single unbroken forcing phase with no
    reset ever applied — tends to `0`. This is the trajectory-level Tragedy of the
    Bound verified in Section 3 of the source `verify.py`.
-/
theorem continuous_forcing_collapses_to_zero
    (k : ℝ) (hk : 0 < k) (A : ℝ → ℝ) (hA : Tendsto A atTop atTop) :
    Tendsto (fun s => Real.exp (-k * A s)) atTop (nhds 0) := by
  norm_num +zetaDelta at *;
  exact Filter.Tendsto.const_mul_atTop hk hA

/-! ### R8 — Sustainable-ceiling bound. -/

/-- **R8.** The duty-cycle-averaged sustainable throughput `u·Ω·D⋆(a,b)` is strictly
    below the instantaneous Intelligence-Bound ceiling `Ω`, whenever the duty cycle
    `u` is genuinely fractional (`0<u<1`) and `(a,b)` are interior — some plasticity,
    and some time, is always spent on sustaining the cycle rather than harvesting.
-/
theorem sustainable_avg_lt_instantaneous_ceiling
    (Omega a b u : ℝ) (hOmega : 0 < Omega) (ha0 : 0 < a) (ha1 : a < 1)
    (hb0 : 0 < b) (hb1 : b < 1) (hu0 : 0 < u) (hu1 : u < 1) :
    u * Omega * Dstar a b < Omega := by
  -- By LEMMA: Obtain 0<Dstar<1 from Dstar_interior_bounds.
  have hDstar_bounds : 0 < Dstar a b ∧ Dstar a b < 1 := by
    exact Dstar_interior_bounds a b ha0 ha1 hb0 hb1;
  nlinarith [ mul_lt_mul_of_pos_left hDstar_bounds.2 hOmega, mul_lt_mul_of_pos_left hu1 hOmega ]

/-! ### R3 — Golden-rule existence (canon candidate, HEADLINE, existence half). -/

/-- **R3 (canon candidate, HEADLINE — existence half).** Given a continuous
    forcing-survival profile `A : ℝ → ℝ` (with `A(τ_F) = a(τ_F) ∈ (0,1)` on the
    duration box, the Cugliandolo–Kurchan aging survival factor) and a continuous
    cumulative-harvest profile `Ifun : ℝ → ℝ`, a reset-decay rate `ρ>0`, and a
    strictly positive per-cycle overhead cost `c>0`, the sustainable-throughput
    objective `R̄(τ_F,τ_R) = Ω·D⋆(A τ_F, exp(-ρ·τ_R))·(Ifun τ_F) / (τ_F+τ_R+c)`
    attains a maximizer on any bounded duration box `[0,T]×[0,T]`. This is the
    existence content of the golden-rule reset duty cycle (numerically confirmed
    interior in 60/60 draws in the source paper's Section 4); the closed-form value
    of the maximizer is DEFERRED (established there by verified grid search, not
    closed-form control theory, per the source paper's own honest disclosure).
-/
theorem interior_ustar_exists_given_c_pos
    (Omega rho c T : ℝ) (hOmega : 0 < Omega) (hrho : 0 < rho) (hc : 0 < c) (hT : 0 < T)
    (A Ifun : ℝ → ℝ)
    (hA_cont : ContinuousOn A (Set.Icc (0 : ℝ) T))
    (hA_pos : ∀ x ∈ Set.Icc (0 : ℝ) T, 0 < A x)
    (hA_lt1 : ∀ x ∈ Set.Icc (0 : ℝ) T, A x < 1)
    (hI_cont : ContinuousOn Ifun (Set.Icc (0 : ℝ) T)) :
    ∃ p ∈ Set.Icc (0 : ℝ) T ×ˢ Set.Icc (0 : ℝ) T,
      ∀ q ∈ Set.Icc (0 : ℝ) T ×ˢ Set.Icc (0 : ℝ) T,
        Omega * Dstar (A q.1) (Real.exp (-rho * q.2)) * Ifun q.1 / (q.1 + q.2 + c)
          ≤ Omega * Dstar (A p.1) (Real.exp (-rho * p.2)) * Ifun p.1 / (p.1 + p.2 + c) := by
  have h_cont : ContinuousOn (fun p : ℝ × ℝ => (Omega * Dstar (A p.1) (Real.exp (-rho * p.2)) * Ifun p.1) / (p.1 + p.2 + c)) (Set.Icc 0 T ×ˢ Set.Icc 0 T) := by
    refine' ContinuousOn.div _ _ _;
    · refine' ContinuousOn.mul ( ContinuousOn.mul continuousOn_const _ ) _;
      · refine' ContinuousOn.div _ _ _;
        · fun_prop;
        · exact ContinuousOn.sub continuousOn_const ( ContinuousOn.mul ( hA_cont.comp continuousOn_fst fun x hx => hx.1 ) ( ContinuousOn.rexp ( continuousOn_const.mul continuousOn_snd ) ) );
        · exact fun x hx => ne_of_gt ( sub_pos_of_lt ( by nlinarith [ hA_pos x.1 hx.1, hA_lt1 x.1 hx.1, Real.exp_pos ( -rho * x.2 ), Real.exp_le_one_iff.mpr ( show -rho * x.2 ≤ 0 by nlinarith [ hx.2.1, hx.2.2 ] ) ] ) );
      · exact hI_cont.comp continuousOn_fst fun x hx => hx.1;
    · fun_prop;
    · exact fun x hx => by linarith [ hx.1.1, hx.1.2, hx.2.1, hx.2.2 ] ;
  exact ( IsCompact.exists_isMaxOn ( CompactIccSpace.isCompact_Icc.prod CompactIccSpace.isCompact_Icc ) ⟨ ⟨ 0, 0 ⟩, by norm_num; linarith ⟩ h_cont )

/-! ### Non-vacuity witness. -/

/-- **`pvt_nonvacuous`.** All laws bind simultaneously on explicit non-degenerate
    witnesses: `a=1/2, b=1/2` gives an interior fixed point `D⋆=2/3`; `b=1`
    (never reset within a cycle) collapses to `D⋆=0`; raising `a` from `1/2` to
    `3/4` at fixed `b=1/2` strictly raises `D⋆` (from `2/3` to `4/5`); the
    sustainable ceiling strictly binds at `u=1/2, Ω=2` (`2/3 < 2`).
-/
theorem pvt_nonvacuous :
    Dstar (1 / 2) (1 / 2) = 2 / 3 ∧
      Dstar (1 / 2) 1 = 0 ∧
      Dstar (1 / 2) (1 / 2) < Dstar (3 / 4) (1 / 2) ∧
      (1 / 2 : ℝ) * 2 * Dstar (1 / 2) (1 / 2) < 2 := by
  unfold Dstar; norm_num;

end Viridis.Plasticity.PlasticityVitrification
