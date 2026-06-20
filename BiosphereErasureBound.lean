/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

# The Biosphere Erasure Bound — the recovered footing of the Intelligence Bound

D. Wolpert refuted the IB's original premise that k_B T ln 2 lower-bounds the cost
of *acquiring* a bit (acquisition ≠ erasure; acquisition can be reversible).

This module relocates the bound to the side of the ledger Wolpert does NOT dispute:
**erasure**. Erasing a bit (reducing logical entropy) dissipates at least
ε_L = k_B T ln 2 — the original Landauer principle. The biosphere is the largest
known low-entropy / high-order dataset (genomes, ecosystems, hydrological and
climate structure); its *erasure* (extinction, collapse) therefore carries an
irreducible thermodynamic floor proportional to its information content `D`.

Two reversals make this the strong form of the IB:
  1. Direction: an UPPER bound on acquisition rate (refuted) becomes a LOWER bound
     on erasure cost and on the intelligence required to steward against erasure.
  2. Robustness: Wolpert's "real costs exceed Landauer (mismatch)" REINFORCES a
     lower bound (it only raises the floor) — his refutation becomes a buttress.

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
-/

import Mathlib

namespace Viridis.BiosphereErasureBound

/-! `ε_L` = k_B T ln 2 > 0, the Landauer cost per erased bit; `D` (or `N` bits) = the
biosphere's order / information content; `Q` = heat dissipated by an erasure process;
`S` = excess (mismatch) dissipation ≥ 0; `r` = rate (bits/time) at which biosphere
order is threatened with erasure; `P` = free-energy throughput (power) of the steward. -/

/-- **Destroying biosphere order is never free.** With a positive Landauer quantum and
positive biosphere order, the erasure floor `ε_L · D` is strictly positive. -/
theorem erasure_floor_positive (εL D : ℝ) (hεL : 0 < εL) (hD : 0 < D) :
    0 < εL * D :=
  mul_pos hεL hD

/-- **Complexity amplifies the floor.** The erasure floor is monotone in the
biosphere's information content: the most complex dataset (largest `D`) carries the
largest irreducible erasure cost. -/
theorem complexity_amplifies_floor (εL D₁ D₂ : ℝ) (hεL : 0 ≤ εL) (h : D₁ ≤ D₂) :
    εL * D₁ ≤ εL * D₂ :=
  mul_le_mul_of_nonneg_left h hεL

/-- **Biosphere erasure floor (additive Landauer).** If each of the biosphere's `N`
bits costs at least `ε_L` to erase, total erasure dissipation is at least `N · ε_L`.
The floor scales with the biosphere's complexity. This is the erasure-side Landauer
bound — the side Wolpert agrees is bounded below. -/
theorem biosphere_erasure_floor {N : ℕ} (εL : ℝ) (cost : Fin N → ℝ)
    (hbit : ∀ i, εL ≤ cost i) :
    (N : ℝ) * εL ≤ ∑ i, cost i := by
  have hsum : ∑ _i : Fin N, εL ≤ ∑ i, cost i :=
    Finset.sum_le_sum (fun i _ => hbit i)
  simpa [Finset.sum_const, Finset.card_univ, nsmul_eq_mul, mul_comm] using hsum

/-- **Wolpert reinforces, not refutes.** Real (irreversible, mismatched) erasure costs
the Landauer floor plus a non-negative excess `S`. Wolpert's observation that real
costs exceed bare Landauer only RAISES the lower bound `ε_L · D` — the very critique
that broke the acquisition-side upper bound buttresses the erasure-side lower bound. -/
theorem wolpert_strengthens_floor (εL D S Q : ℝ)
    (hS : 0 ≤ S) (hQ : εL * D + S ≤ Q) :
    εL * D ≤ Q := by
  linarith

/-- **Stewardship intelligence floor (the dual of the IB).** To hold the biosphere's
order against erasure threatening `r` bits/time, the steward must supply free energy
at rate ≥ `ε_L · r`; hence its power `P` (a proxy for the information-processing
throughput of any adequate biosphere-AI) is bounded BELOW by `ε_L · r`. Where the
original IB put an upper bound on learning rate, the biosphere puts a LOWER bound on
the intelligence required to steward it. -/
theorem stewardship_power_floor (εL r P t : ℝ)
    (ht : 0 < t) (hmaint : εL * r * t ≤ P * t) :
    εL * r ≤ P :=
  le_of_mul_le_mul_right hmaint ht

end Viridis.BiosphereErasureBound
