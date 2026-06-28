/-
===============================================================================
  The Verification Phase-Transition Theorem (VPT) — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
===============================================================================

CONTEXT (nightly Run 081, verification-phase-transition; [08] Ecoservices
Platform × Symbiosis lens; 23rd IB self-application, "the Verifier").

  A monitoring AI and the ecosystem it measures form a thermodynamic mutualism.
  Every attested credit-bit costs at least the Landauer quantum

        q = k_B · T · ln 2          ( > 0 ).

  There is a minimum self-sustaining ESU (ecosystem-service-unit) price

        p_crit = (δ + r_thermo) · q · H_eff / (η · P · κ),

  with all parameters positive:
        δ        depreciation / leakage rate of attested capital,
        r_thermo endogenous thermodynamic discount rate (Run 080, the Appraiser;
                 r_thermo → ∞ at tipping points),
        H_eff    effective bits per attestation (entropy load),
        η        verifier energy efficiency,
        P        available power,
        κ        Joule-to-value conversion.

  Below p_crit the credit market cannot bootstrap (a "verification poverty
  trap"); above it the AI–ecosystem–market triad self-funds.  The crossing at
  p = p_crit is a TRANSCRITICAL bifurcation of the market-participation
  dynamics.  Writing the participation density x ≥ 0, the bootstrap normal form
  is

        dx/dt = f(x) = s·(p − p_crit)·x − β·x²,        s, β > 0,

  with equilibria  x = 0  and  x* = s(p − p_crit)/β, and linearization
  f'(x) = s(p − p_crit) − 2β x, so f'(0) = s(p − p_crit) and f'(x*) =
  − s(p − p_crit): the two equilibria exchange stability exactly at p_crit.

  Engineering levers (proved below): ZK-MRV compression c ∈ (0,1] lowers p_crit
  proportionally (a thermodynamic subsidy); alignment-matched sensing lowers it
  as 1/cos²Θ; and p_crit diverges as r_thermo → ∞ (non-market backstops needed
  near the brink).

WHAT IS PROVEN HERE (clean core — target: 0 `sorry`; axioms ⊆
{propext, Classical.choice, Quot.sound}; every named statement non-vacuous):

  1. mrv_floor_landauer                    — per-attestation Landauer floor scales
                                             the total attestation energy.
  2. verifier_throughput_IB_ceiling        — the Intelligence-Bound throughput
                                             ceiling ρ ≤ P·D/q.
  3. verification_transcritical_bifurcation— equilibria collide iff p = p_crit and
                                             exchange linear stability there.
  4. p_crit_formula_and_monotonicity       — p_crit > 0 and is monotone
                                             nondecreasing in r_thermo.
  5. zk_soundness_floor                    — ZK compression c ∈ (0,1] lowers p_crit.
  6. alignment_minimizes_pcrit             — misalignment 1/u (u = cos²Θ ≤ 1)
                                             raises p_crit; perfect alignment minimizes it.
  7. pcrit_diverges_at_tipping             — p_crit → ∞ as r_thermo → ∞.
  + vpt_nonvacuous                          — admissible parameters exist.
-/
import Mathlib

set_option autoImplicit false

namespace Viridis.Ecoservices.VerificationPhaseTransition

open scoped Real

/-- Minimum self-sustaining ESU price `p_crit`.  All physical parameters are
    intended positive; positivity is supplied as hypotheses where needed. -/
noncomputable def pcrit (δ r q H η P κ : ℝ) : ℝ := (δ + r) * q * H / (η * P * κ)

/-- Market-bootstrap participation vector field (transcritical normal form)
    `f(x) = s·(p − pc)·x − β·x²`. -/
noncomputable def bootstrap (s β p pc x : ℝ) : ℝ := s * (p - pc) * x - β * x ^ 2

/-- Linearization (x-derivative) of `bootstrap`:
    `f'(x) = s·(p − pc) − 2β·x`. -/
noncomputable def bootstrap' (s β p pc x : ℝ) : ℝ := s * (p - pc) - 2 * β * x

/-
**(1) MRV Landauer floor.**  If each attested bit costs at least the
    Landauer quantum `q = k_B T ln 2`, then attesting `B ≥ 0` bits dissipates at
    least `B · q`.  Non-vacuous: uses the per-bit Landauer bound and `q > 0`.
-/
theorem mrv_floor_landauer
    {kB T B c_bit : ℝ} (hkB : 0 < kB) (hT : 0 < T) (hB : 0 ≤ B)
    (hLandauer : kB * T * Real.log 2 ≤ c_bit) :
    B * (kB * T * Real.log 2) ≤ B * c_bit := by
  exact mul_le_mul_of_nonneg_left hLandauer hB

/-
**(2) Verifier throughput Intelligence-Bound ceiling.**  Any sustainable
    attestation rate `ρ` whose energy draw `ρ·q` is met by the available
    dissipative power budget `P·D` obeys the IB ceiling `ρ ≤ P·D/q`.
-/
theorem verifier_throughput_IB_ceiling
    {ρ q P D : ℝ} (hq : 0 < q) (hbalance : ρ * q ≤ P * D) :
    ρ ≤ P * D / q := by
  rwa [ le_div_iff₀ hq ]

/-
**(3) Verification transcritical bifurcation.**  The nontrivial market
    equilibrium `x* = s(p − pc)/β` collides with the trivial one (`x* = 0`)
    exactly at the threshold `p = pc`, and there the two equilibria exchange
    linear stability: `f'(0) = − f'(x*)`.
-/
theorem verification_transcritical_bifurcation
    {s β p pc : ℝ} (hs : 0 < s) (hβ : 0 < β) :
    (s * (p - pc) / β = 0 ↔ p = pc) ∧
    bootstrap' s β p pc 0 = - bootstrap' s β p pc (s * (p - pc) / β) := by
  unfold bootstrap';
  grind

/-
**(4) p_crit formula and monotonicity.**  With positive parameters the
    critical price is strictly positive and is monotone nondecreasing in the
    thermodynamic discount rate `r`.
-/
theorem p_crit_formula_and_monotonicity
    {δ q H η P κ r₁ r₂ : ℝ}
    (hδ : 0 < δ) (hq : 0 < q) (hH : 0 < H) (hη : 0 < η) (hP : 0 < P) (hκ : 0 < κ)
    (hr₁ : 0 ≤ r₁) (hr : r₁ ≤ r₂) :
    0 < pcrit δ r₁ q H η P κ ∧ pcrit δ r₁ q H η P κ ≤ pcrit δ r₂ q H η P κ := by
  unfold pcrit;
  exact ⟨ by positivity, by gcongr ⟩

/-
**(5) ZK soundness floor.**  A ZK-MRV compression ratio `c ∈ (0,1]` reduces
    the effective entropy load to `c·H`, lowering the critical price
    (a thermodynamic subsidy): `p_crit(c·H) ≤ p_crit(H)`.
-/
theorem zk_soundness_floor
    {δ r q H η P κ c : ℝ}
    (hδ : 0 < δ) (hr : 0 ≤ r) (hq : 0 < q) (hH : 0 < H)
    (hη : 0 < η) (hP : 0 < P) (hκ : 0 < κ) (hc0 : 0 < c) (hc1 : c ≤ 1) :
    pcrit δ r q (c * H) η P κ ≤ pcrit δ r q H η P κ := by
  exact div_le_div_of_nonneg_right ( mul_le_mul_of_nonneg_left ( mul_le_of_le_one_left hH.le hc1 ) ( by positivity ) ) ( by positivity )

/-
**(6) Alignment minimizes p_crit.**  Writing `u = cos²Θ ∈ (0,1]` for the
    alignment between sensing effort and information generation, misalignment
    inflates the effective entropy load to `H/u`.  Hence `p_crit(H) ≤
    p_crit(H/u)`, i.e. perfect alignment (`u = 1`) minimizes the critical price.
-/
theorem alignment_minimizes_pcrit
    {δ r q H η P κ u : ℝ}
    (hδ : 0 < δ) (hr : 0 ≤ r) (hq : 0 < q) (hH : 0 < H)
    (hη : 0 < η) (hP : 0 < P) (hκ : 0 < κ) (hu0 : 0 < u) (hu1 : u ≤ 1) :
    pcrit δ r q H η P κ ≤ pcrit δ r q (H / u) η P κ := by
  exact div_le_div_of_nonneg_right ( mul_le_mul_of_nonneg_left ( by nlinarith [ div_mul_cancel₀ H hu0.ne' ] ) ( by positivity ) ) ( by positivity )

/-
**(7) p_crit diverges at tipping.**  Because `r_thermo → ∞` at tipping
    points (the Appraiser, Run 080), the critical price diverges there: the
    market cannot be made to bootstrap exactly where restoration is most urgent.
-/
theorem pcrit_diverges_at_tipping
    {δ q H η P κ : ℝ}
    (hq : 0 < q) (hH : 0 < H) (hη : 0 < η) (hP : 0 < P) (hκ : 0 < κ) :
    Filter.Tendsto (fun r => pcrit δ r q H η P κ) Filter.atTop Filter.atTop := by
  convert Filter.Tendsto.atTop_div_const _ _ using 1;
  · infer_instance;
  · positivity;
  · exact Filter.Tendsto.atTop_mul_const ( by positivity ) ( Filter.Tendsto.atTop_mul_const ( by positivity ) ( tendsto_const_nhds.add_atTop Filter.tendsto_id ) )

/-
**Non-vacuity witness.**  Admissible (strictly positive) parameters exist
    with a strictly positive critical price.
-/
theorem vpt_nonvacuous :
    ∃ δ r q H η P κ : ℝ,
      0 < δ ∧ 0 < r ∧ 0 < q ∧ 0 < H ∧ 0 < η ∧ 0 < P ∧ 0 < κ ∧
      0 < pcrit δ r q H η P κ := by
  exact ⟨ 1, 1, 1, 1, 1, 1, 1, by norm_num, by norm_num, by norm_num, by norm_num, by norm_num, by norm_num, by norm_num, by unfold pcrit; norm_num ⟩

end Viridis.Ecoservices.VerificationPhaseTransition