# Forge spec — make `h_mem` load-bearing in P0 `finite_memory_dissipation` (INV-4)

**Status:** queued for a fresh Aristotle pass. This is a proof-content change; per
the Aristotle-first gate it is NOT asserted verified in v9.1.0.

## The defect

`P0_IntelligenceBound_COMPILED.lean`:

```lean
theorem finite_memory_dissipation … (h_mem : BoundedMemory μ Y C)
    (h_landauer : P ≥ erasureRate * ENNReal.ofReal (kB*T*Real.log 2))
    (h_erasure_needed : erasureRate ≥ intelligenceCreationRate μ X Y τ) :
    (P : ENNReal) ≥ intelligenceCreationRate μ X Y τ * ENNReal.ofReal (kB*T*Real.log 2) := by
  exact le_trans (mul_le_mul_right' h_erasure_needed _) h_landauer
```

The proof uses only `h_landauer` and `h_erasure_needed`. **`h_mem` is never
used.** The theorem's name and docstring claim "bounded memory ⟹ dissipation,"
but bounded memory plays no role: the result is just transitivity of
`Landauer ∧ erasure ≥ creation`. A critic running `#print axioms` won't catch
this, but reading the proof term will.

## Invariant the fix must satisfy

> **INV-4.** In any spine theorem named for a mechanism, the hypothesis encoding
> that mechanism must be load-bearing: deleting it must break the proof.

## Option A (recommended) — derive the erasure rate FROM bounded memory

Bind P0 to the module that already does the real work,
`BoundedMemoryLearning.bounded_memory_forces_erasure`
(`A − E ≤ M ⟹ E ≥ A − M`). The intended causal chain is:

```
bounded memory (capacity C)  ⟹  erasureRate ≥ creationRate − C    (forces erasure)
                              ⟹  P ≥ (creationRate − C) · kBT ln2  (Landauer on erasure)
```

Concretely:

```lean
import BoundedMemoryLearning   -- add to P0 imports

theorem finite_memory_dissipation … (h_mem : BoundedMemory μ Y C)
    (h_landauer_erasure : ∀ r, P ≥ r * ENNReal.ofReal (kB*T*Real.log 2) → …)
    … :
    (P : ENNReal) ≥ (intelligenceCreationRate μ X Y τ - (C : ENNReal))
                      * ENNReal.ofReal (kB*T*Real.log 2) := by
  -- 1. from h_mem, obtain erasureRate ≥ creationRate − C
  --    (instantiate bounded_memory_forces_erasure with A := creationRate, M := C)
  -- 2. apply the Landauer floor to that erasure rate
  …
```

The conclusion weakens from `creationRate` to `creationRate − C` — which is the
**honest** finite-memory statement (a system with capacity `C` need only erase
the excess above `C`). `h_mem` is now essential: remove it and step 1 fails.

## Option B (minimal) — admit the result is Landauer-only and rename

If the `creationRate − C` refinement is not wanted now, delete `h_mem` and rename:

```lean
theorem landauer_dissipation_bound …    -- no BoundedMemory hypothesis
    (h_landauer …) (h_erasure_needed …) : … := by
  exact le_trans (mul_le_mul_right' h_erasure_needed _) h_landauer
```

This is fully honest (the proof is exactly this) and removes the false
implication that bounded memory was used. Pairs with a CLAIMS_MATRIX status of
**Definition-expansion / Conditional**.

## Recommendation

Ship **Option A** — it makes the bounded-memory mechanism real, unifies P0 with
the post-Wolpert `BoundedMemoryLearning` engine (closing the gap the reviewer
flagged), and yields the correct `creationRate − C` floor. Keep Option B as the
fallback if the Aristotle pass on A stalls.

## Acceptance check (add to AxiomAudit/CI once landed)

A lightweight "unused-hypothesis" guard: for each spine theorem, assert that
every explicitly-named hypothesis appears in the proof term. (Lean's
`linter.unusedVariables` covers term-mode binders; enable it for the spine and
treat warnings as errors for `h_*` hypotheses.)
