/-
  CognitiveThroughput.lean — Viridis Aristotle Forge
  Nightly Run 039 — The Cognitive Throughput Theorem (CTT)
  The first first-principles cognitive-throughput envelope: under simultaneous
  Pierra–Censor–Elfving Bregman multiprojection onto Csense ∩ Cmodel ∩ Cmotor,
  the maximum certified information rate per observation obeys an inverse
  square-root law in the number of observations N,

      dI_cog/dt |max (N) = K_cog · N^(−1/2),

  with throughput constant K_cog = √( 2·W_attn·Φ_eco / (k_B T ln 2) ), and
  Φ_eco ∈ (0,1] the ecological coupling factor (cosine of the angle between the
  motor jump operator and the environmental affordance basis).

  This module discharges the named canon target `Viridis.Cognition.CTT.
  SquareRootScaling` and its load-bearing corollaries (throughput invariant,
  strict antitone "attentional iris", and the Symbiotic-AI inference bound:
  a fully decoupled agent Φ_eco = 0 saturates at ZERO throughput, while any
  ecological coupling Φ_eco > 0 yields strictly positive K_cog).

  We model the envelope as  R K N := K / √N  (N = N_obs > 0). The square-root
  scaling content is the homogeneity law R(c·N) = R(N)/√c, equivalently the
  throughput invariant R(N)·√N = K.

  DEFERRED to a dedicated run (NOT in this project):
    • Viridis.Cognition.CTT.OMPathEquivalence — the Onsager–Machlup ↔ Koopman
      path-equivalence; the finding gives no closed-form Lean-ready proposition
      (statement-form risk) → staged as a gate-check, not auto-submitted.

  ACCEPTANCE: 0 sorry; axiom audit ⊆ {propext, Classical.choice, Quot.sound};
  every named theorem compiles NON-VACUOUSLY (no conclusion collapsed to a
  trivially-true statement). Preserve all named statements VERBATIM. If a lemma
  was renamed under Mathlib pin 8f9d9cff, swap the proof term but DO NOT weaken
  any conclusion. Toolchain leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real

namespace Viridis.Cognition.CTT

/-- The maximum certified cognitive-throughput envelope as a function of the
    number of observations `N`, for throughput constant `K`:  `R K N = K / √N`. -/
noncomputable def R (K N : ℝ) : ℝ := K / Real.sqrt N

/-- The ecological throughput constant
    `K_cog = √( 2 · W_attn · Φ_eco / (k_B T ln 2) )`. -/
noncomputable def Kcog (Wattn Phi_eco kT : ℝ) : ℝ :=
  Real.sqrt (2 * Wattn * Phi_eco / (kT * Real.log 2))

/-! ### (CTT main) Inverse square-root scaling of the throughput envelope.

NON-VACUITY: the identity is the defining homogeneity of an `N^(−1/2)` law and
genuinely consumes `0 < c`, `0 < N` (it determines the exponent −1/2 uniquely:
no other power law satisfies `R(c·N) = R(N)/√c` for all `c`). -/
theorem SquareRootScaling (K c N : ℝ) (hc : 0 < c) (hN : 0 < N) :
    R K (c * N) = R K N / Real.sqrt c := by
  unfold R
  rw [Real.sqrt_mul hc.le]
  field_simp

/-- The cognitive throughput–budget invariant: `R(N)·√N = K` for every
    `N > 0` (the conserved attention budget across observation counts).
    NON-VACUITY: consumes `0 < N` (else `√N = 0` and the product is `0 ≠ K`). -/
theorem throughput_invariant (K N : ℝ) (hN : 0 < N) :
    R K N * Real.sqrt N = K := by
  unfold R
  have h : Real.sqrt N ≠ 0 := by positivity
  field_simp

/-- Attentional Iris (Cor 2): the envelope is STRICTLY decreasing in the
    observation count for a positive throughput constant — more divided
    attention ⇒ strictly lower certified rate per observation.
    NON-VACUITY: requires `0 < K`; with `K = 0` the envelope is constantly `0`
    and the strict inequality is false. -/
theorem envelope_strictAntitone (K N₁ N₂ : ℝ)
    (hK : 0 < K) (hN₁ : 0 < N₁) (hlt : N₁ < N₂) :
    R K N₂ < R K N₁ := by
  unfold R
  have h1 : 0 < Real.sqrt N₁ := Real.sqrt_pos.mpr hN₁
  have h2 : Real.sqrt N₁ < Real.sqrt N₂ :=
    Real.sqrt_lt_sqrt hN₁.le hlt
  apply div_lt_div_of_pos_left hK h1 h2

/-! ### Symbiotic-AI inference bound (Cor, finding §applications).

A fully decoupled agent (`Φ_eco = 0`) has ZERO throughput constant; any
ecological coupling (`Φ_eco > 0`, with positive attention power and temperature)
yields a STRICTLY POSITIVE `K_cog`. This is the cognitive face of the
Intelligence Bound: throughput is gated by physical/ecological coupling. -/

/-- Decoupled AI saturates at zero throughput: `Φ_eco = 0 ⇒ K_cog = 0`. -/
theorem decoupled_AI_zero_throughput (Wattn kT : ℝ) :
    Kcog Wattn 0 kT = 0 := by
  unfold Kcog
  simp

/-- Ecology-coupled AI has strictly positive throughput:
    `0 < W_attn → 0 < kT → 0 < Φ_eco → 0 < K_cog`.
    NON-VACUITY: genuinely consumes all three positivity hypotheses and
    `0 < log 2` (so the radicand is positive and `√` is positive). -/
theorem coupled_AI_positive_throughput (Wattn Phi_eco kT : ℝ)
    (hW : 0 < Wattn) (hkT : 0 < kT) (hPhi : 0 < Phi_eco) :
    0 < Kcog Wattn Phi_eco kT := by
  unfold Kcog
  apply Real.sqrt_pos.mpr
  have hlog : 0 < Real.log 2 := Real.log_pos (by norm_num)
  positivity

end Viridis.Cognition.CTT
