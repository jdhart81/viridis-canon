/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

# Power-Limited Sustained Learning (corrected thermodynamic branch of the Intelligence Bound)

Context: D. Wolpert (Santa Fe Institute) refuted the original premise of the IB's
thermodynamic branch — that k_B T ln 2 is a *lower bound on the cost of acquiring
a bit*. He is right: (i) acquisition ≠ erasure (Landauer's floor is for ERASING a
bit; acquiring/measuring carries no such floor — Bennett; Sagawa–Ueda); and
(ii) even logically-irreversible operations can be run thermodynamically
reversibly with zero entropy production (Wolpert, arXiv:1508.05319), so there is
no *universal* per-bit floor.

This module rebuilds the bound on a defensible footing. The cost is grounded NOT
in acquisition but in the ERASURE that *bounded memory* forces: a learner with
finite capacity that keeps acquiring must overwrite, and erasure in any
finite-time / dissipative (non-reversible) regime has a strictly positive
per-erasure dissipation floor `ε`. `ε` is a STATED regime parameter (= k_B T ln 2
in the standard quasistatic non-reversible case), NOT a universal constant — and
when `ε = 0` (the reversible idealization Wolpert invokes) the bound correctly
vacates. The result is a CONDITIONAL, regime-restricted bound, not a universal law.

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
-/

import Mathlib

namespace Viridis.BoundedMemoryLearning

/-! `A` = cumulative acquired predictive information (bits); `M` = memory capacity
(bits); `E` = bits erased; `Q` = total dissipation; `ε` = per-ERASURE dissipation
floor in the operating regime; `P` = power; `τ` = horizon. -/

/-- **Bounded memory forces erasure.** If the information retained at the end
(`A - E`, acquired minus erased) does not exceed capacity `M`, then at least
`A - M` bits were erased. -/
theorem bounded_memory_forces_erasure (A M E : ℝ) (hret : A - E ≤ M) :
    A - M ≤ E := by
  linarith

/-- **Erasure dissipation floor.** With a per-erasure dissipation floor `ε > 0`,
total dissipation `Q ≥ ε·E`, and at least `A - M` erasures, the dissipation is at
least `ε·(A - M)`. -/
theorem erasure_dissipation_floor (A M E Q ε : ℝ)
    (hε : 0 < ε) (hQ : ε * E ≤ Q) (hE : A - M ≤ E) :
    ε * (A - M) ≤ Q := by
  have h := mul_le_mul_of_nonneg_left hE hε.le
  linarith

/-- **Power-limited sustained learning (headline).** Grounding the cost in the
erasure that bounded memory forces — NOT in acquisition — with an energy budget
`ε·(A - M) ≤ P·τ`, sustained acquisition obeys `ε·A ≤ P·τ + ε·M`. Equivalently the
average rate `A/τ ≤ P/ε + M/τ → P/ε`. The floor `ε` is the operating-regime
per-erasure dissipation (a stated physical assumption), NOT a universal
`k_B T ln 2`. -/
theorem sustained_learning_bound (A M P ε τ : ℝ)
    (hbudget : ε * (A - M) ≤ P * τ) :
    ε * A ≤ P * τ + ε * M := by
  nlinarith [hbudget]

/-- **Honesty clause — the reversible loophole, encoded.** If the regime admits
reversible erasure, `ε = 0`, the energy-budget constraint `0·(A - M) ≤ P·τ` holds
for *every* `A` (given non-negative power and horizon): there is NO upper bound on
acquisition. The bound has bite exactly when the regime has a strictly positive
per-erasure dissipation floor. This is Wolpert's point (arXiv:1508.05319) made
explicit inside the formalism. -/
theorem reversible_regime_imposes_no_bound (A M P τ : ℝ)
    (hP : 0 ≤ P) (hτ : 0 ≤ τ) :
    (0 : ℝ) * (A - M) ≤ P * τ := by
  have : (0 : ℝ) ≤ P * τ := mul_nonneg hP hτ
  simpa using this

end Viridis.BoundedMemoryLearning
