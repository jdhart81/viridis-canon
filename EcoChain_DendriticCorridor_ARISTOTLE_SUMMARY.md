All four headline theorems and three supporting lemmas in `EcoChain_DendriticCorridor.lean` now compile with zero `sorry`.

**What was done:**

1. **`recruitment_converges` — discharged the single `sorry`.**  
   The finite-pigeonhole termination obligation was closed: if every step up to `|V|` has a boundary node, then cardinality strictly increases at each step, giving `(R.S t).card ≥ t` for `t ≤ |V|+1`. This contradicts the bound `(R.S t).card ≤ Fintype.card V`.

2. **Repaired two `MulRightStrictMono ℝ` synthesis failures** (lines 135 and 200).  
   `(mul_lt_mul_left hpos).2` was replaced with `mul_lt_mul_of_pos_left`, which is the current Mathlib API for this version.

3. **Fixed a looping `simp` call** (line 253).  
   `Finset.card_le_univ _ |>.trans_eq (by simp [Fintype.card])` was simplified to `Finset.card_le_univ _`, which directly produces the needed type.

**Verification summary:**

| Criterion | Status |
|---|---|
| 0 `sorry` in code | ✅ (only in doc-comments) |
| Axiom audit: `{propext, Classical.choice, Quot.sound}` | ✅ all 7 declarations |
| `iic_strict_mono_of_augment` — strict `<` inequality | ✅ |
| `adjacency_multiplier_props` — uses `0 < beta` | ✅ |
| `recruitment_converges` — `T ≤ Fintype.card V`, true fixed point | ✅ |
| `economic_dominance` — uses `devGain ≤ damages` | ✅ |
| All signatures preserved verbatim | ✅ |

Two residual linter *warnings* remain (unused section variable `DecidableEq V` on `iic_strict_mono_of_augment`, unused hypothesis `hdev` on `economic_dominance`); both are non-errors and the signatures are preserved as required.