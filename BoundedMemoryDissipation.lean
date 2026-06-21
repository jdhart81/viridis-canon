/-
# P0 Bounded-Memory Dissipation Floor — INTEGRITY FIX (INV-4)
Viridis Aristotle Forge · 2026-06-21 · Integrity Release v9.1.0 follow-on
Authors: Justin Hart, Aristotle (Harmonic)

PURPOSE. The canonical P0 `finite_memory_dissipation` carried an UNUSED bounded-
memory hypothesis `h_mem` (external audit, 2026-06-21): its proof rode on
`Landauer ∧ erasure ≥ creation` alone, so the named bounded-memory mechanism was
decorative. This target supplies the honest, NON-VACUOUS replacement in the same
real-ledger abstraction as the verified `BoundedMemoryLearning` engine, in which
bounded memory is LOAD-BEARING: deleting `hmem` breaks the proof, and that fact is
itself machine-checked below.

ACCEPTANCE. Discharge every `sorry`; preserve every named statement VERBATIM;
axiom audit ⊆ {propext, Classical.choice, Quot.sound}; every theorem NON-VACUOUS;
every named hypothesis genuinely consumed.

LEDGER. A = acquired predictive bits; M = memory capacity (bits); E = bits erased;
Q = total dissipation; ε = per-erasure dissipation floor (a STATED regime
parameter, NOT a universal constant — Wolpert-robust). Bounded memory = retained
information `A − E ≤ M`.

Toolchain: leanprover/lean4:v4.28.0
-/
import Mathlib

set_option autoImplicit false

namespace Viridis.P0BoundedMemoryDissipation

/-- **Bounded memory forces erasure** (verbatim from `BoundedMemoryLearning`).
If retained information `A − E` does not exceed capacity `M`, at least `A − M`
bits were erased. -/
theorem bounded_memory_forces_erasure (A M E : ℝ) (hret : A - E ≤ M) :
    A - M ≤ E := by
  linarith

/-- **Erasure dissipation floor** (verbatim from `BoundedMemoryLearning`).
With per-erasure floor `ε > 0`, dissipation `ε·E ≤ Q`, and at least `A − M`
erasures, total dissipation is at least `ε·(A − M)`. -/
theorem erasure_dissipation_floor (A M E Q ε : ℝ)
    (hε : 0 < ε) (hQ : ε * E ≤ Q) (hE : A - M ≤ E) :
    ε * (A - M) ≤ Q := by
  have h := mul_le_mul_of_nonneg_left hE hε.le
  linarith

/-- **HEADLINE — Bounded-Memory Dissipation Floor (P0 INV-4 replacement).**
A bounded-memory learner (retained information `A − E ≤ M`) in a regime with
per-erasure dissipation floor `ε > 0` and dissipation budget `ε·E ≤ Q` dissipates
at least `ε·(A − M)`. The bounded-memory hypothesis `hmem` is LOAD-BEARING: it is
exactly what forces `A − M ≤ E` (via `bounded_memory_forces_erasure`); without it
`E` is unconstrained and no floor follows. This is the honest replacement for the
canonical `finite_memory_dissipation`, whose `h_mem` was unused. -/
theorem bounded_memory_dissipation_floor (A M E Q ε : ℝ)
    (hε : 0 < ε) (hQ : ε * E ≤ Q) (hmem : A - E ≤ M) :
    ε * (A - M) ≤ Q := by
  have hE : A - M ≤ E := bounded_memory_forces_erasure A M E hmem
  exact erasure_dissipation_floor A M E Q ε hε hQ hE

/-- **Non-vacuity witness.** The antecedents are jointly satisfiable in the regime
where the floor bites (`M < A`), so the theorem is not vacuously about an empty
hypothesis set. Witness: A=2, M=1, E=1, Q=1, ε=1. -/
theorem bounded_memory_dissipation_floor_nonvacuous :
    ∃ A M E Q ε : ℝ,
      0 < ε ∧ ε * E ≤ Q ∧ A - E ≤ M ∧ A - M ≤ E ∧ M < A := by
  refine ⟨2, 1, 1, 1, 1, ?_, ?_, ?_, ?_, ?_⟩ <;> norm_num

/-- **Load-bearing witness (the contrast).** WITHOUT bounded memory the floor can
fail: there is an assignment satisfying `0 < ε` and `ε·E ≤ Q` but NOT
`ε·(A − M) ≤ Q`. Hence `hmem` genuinely cannot be dropped from the headline.
Witness: A=10, M=0, E=0, Q=0, ε=1 — here `ε·E = 0 ≤ 0 = Q` yet
`ε·(A − M) = 10 > 0 = Q` (and indeed `A − E = 10 ≰ 0 = M`, i.e. `hmem` is violated). -/
theorem bounded_memory_is_load_bearing :
    ∃ A M E Q ε : ℝ, 0 < ε ∧ ε * E ≤ Q ∧ ¬ (ε * (A - M) ≤ Q) := by
  refine ⟨10, 0, 0, 0, 1, ?_, ?_, ?_⟩ <;> norm_num

end Viridis.P0BoundedMemoryDissipation
