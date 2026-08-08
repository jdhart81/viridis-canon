# Run 118 Snapshot Alignment — Aristotle verification summary (attempt 2)

## Result

The project builds and every frozen declaration kernel-checks with no proof
holes and no non-standard axioms.

- `lake build` → `Build completed successfully (2155 jobs)`, exit code 0.
- `sorry` / `admit` / `sorryAx` occurrences: 0 (raw and comment-stripped).
- `axiom`, `unsafe`, `native_decide`, `@[implemented_by]`, `@[extern]`,
  `partial`, `opaque`: 0 occurrences.
- No statement, definition, hypothesis, or conclusion was modified. The module
  `SnapshotAlignment.lean` is byte-identical to the attempt-1 source
  (`git status` reports no change to the file).

## Pinned toolchain and manifest repair

- Toolchain: `leanprover/lean4:v4.28.0` (`lean-toolchain`, unchanged).
- Mathlib revision: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`, confirmed by
  `git rev-parse HEAD` in `.lake/packages/mathlib`; its `lean-toolchain` is
  `leanprover/lean4:v4.28.0`, matching the project.
- The attempt-1 failure was a one-package `lake-manifest.json` that omitted
  Mathlib's transitive dependencies, so Lake aborted on the missing package
  `plausible`. The manifest carried into this attempt lists the complete nine
  packages — `mathlib`, `plausible`, `LeanSearchClient`, `importGraph`,
  `proofwidgets`, `aesop`, `Qq`, `batteries`, `Cli` — all resolved against the
  same pinned Mathlib revision. No dependency was updated, added, or removed
  during this verification, and no Git remote was contacted.

## Verified theorem set

All six declarations live in namespace `Viridis.SnapshotAlignment` and are
stated over an arbitrary `Fintype` index `ι`, on top of the four frozen
definitions `phasor`, `alignment`, `weightedMean`, `delayVariance`.

1. **`phasor_energy_pairwise_identity`** — the exact double-sum identity
   `alignment w τ ω = ∑ i, ∑ j, w i * w j * cos (ω * (τ i - τ j))`, with no
   hypotheses on `w` or `τ`.
2. **`alignment_efficiency_unit_interval`** — for nonnegative weights summing
   to `1`, `0 ≤ alignment w τ ω ∧ alignment w τ ω ≤ 1`.
3. **`delay_variance_bounds_alignment_loss`** — under the same weight
   normalization, `1 - alignment w τ ω ≤ ω ^ 2 * delayVariance w τ`.
4. **`alignment_budget_sufficient_for_band`** — a model-scoped *sufficient*
   condition only: if `|ω| ≤ Ω`, `0 ≤ q ≤ 1` and
   `delayVariance w τ ≤ (1 - q) / Ω ^ 2`, then `q ≤ alignment w τ ω`. It is not
   claimed as necessary and is not an empirical guarantee.
5. **`equal_delay_perfect_alignment`** — if all delays equal a common `τ₀` and
   the weights sum to `1`, then `alignment w τ ω = 1`.
6. **`two_channel_half_period_cancellation`** — for two equally weighted
   channels with delays `0` and `T`, if `exp (-(ω T) i) = -1` then
   `alignment ... ω = 0`.

## Proof strategy

The chain is elementary and fully constructive over Mathlib's complex
exponential and trigonometric API.

- `phasor_re` / `phasor_im` expand the complex weighted phasor into its
  real cosine and sine components via `Complex.exp_re` / `Complex.exp_im`,
  giving `alignment_eq_sq_add_sq`: the energy is `(∑ w cos)² + (∑ w sin)²`.
- Theorem 1 expands both squares as double sums (`Finset.sum_mul_sum`) and
  recombines them term-by-term with the cosine subtraction formula
  `Real.cos_sub`, yielding the diagonal-plus-off-diagonal pairwise form.
- Theorem 2 bounds each cosine in that identity by `1` (weights being
  nonnegative) and collapses the double sum to `(∑ w)(∑ w) = 1`; the lower
  bound is `Complex.normSq_nonneg`.
- `alignment_eq_sq_add_sq_shift` shows recentring the delays by any constant
  `c` multiplies the phasor by a unit-modulus factor and so leaves the energy
  unchanged; dropping the sine term gives `sq_cos_le_alignment`.
- `cos_sum_lower_bound` applies the quadratic cosine bound
  `Real.one_sub_sq_div_two_le_cos` pointwise at `c = weightedMean w τ` and sums,
  producing `1 - ω² · delayVariance / 2 ≤ ∑ w cos`. Squaring that (when the
  left side is positive) and combining with `sq_cos_le_alignment` via `nlinarith`
  gives theorem 3; the degenerate case follows from `0 ≤ alignment`.
- Theorem 4 chains theorem 3 with `ω² ≤ Ω²` from `|ω| ≤ Ω` and the budget
  hypothesis, using `ω²/Ω² ≤ 1`.
- Theorem 5 factors the common phase out of the sum, uses `∑ w = 1`, and
  computes the modulus with `Complex.norm_exp_ofReal_mul_I`.
- Theorem 6 evaluates the two-term sum explicitly and substitutes the
  half-cycle hypothesis `exp(-(ωT)i) = -1`, giving `½ + ½·(-1) = 0`.

## Axiom result

`#print axioms` on each of the six theorems (elaborated against the built
module) reports exactly:

```
[propext, Classical.choice, Quot.sound]
```

for all six. No `sorryAx`, no user-declared axiom, no unexpected axiom.

## Zero-hole result

The module contains no `sorry`, `admit`, or any other proof hole, raw or after
stripping comments, and the build emits no errors. The only diagnostics are
non-fatal: an informational `ring`/`ring_nf` suggestion inside a helper lemma
whose proof nonetheless closes, and two unused-variable warnings for `hΩ` and
`hq0` in `alignment_budget_sufficient_for_band`. Those two hypotheses are part
of the frozen statement contract and were deliberately left in place rather
than removed.

## Non-vacuity witnesses

Checked locally against the built module (scratch checks, not added to the
frozen source, which may not be altered):

- `alignment (fun _ : Fin 2 => 1/2) (fun i => if i = 0 then 0 else 1) π = 0`
  — instantiates theorem 6 with `T = 1`, `ω = π`, discharging the hypothesis
  `exp(-(π·1)i) = -1` from `Complex.exp_pi_mul_I`. The half-period hypothesis
  is therefore satisfiable and the destructive-interference conclusion is
  realized.
- `alignment (fun _ : Fin 2 => 1/2) (fun _ => 3) 7 = 1` — instantiates
  theorem 5, showing the perfect-alignment conclusion is attained.
- `1/2 ≤ alignment (fun _ : Fin 2 => 1/2) (fun _ => 0) 1` — instantiates
  theorem 4 with `Ω = 1`, `q = 1/2`, all hypotheses satisfied simultaneously,
  so the budget theorem is not vacuous.

Theorems 1–3 carry either no hypotheses or only the satisfiable weight
normalization `0 ≤ w i`, `∑ w = 1` (witnessed above), so none is vacuous.

## Scope note

Consistent with `SOURCE_BINDING.json` and `STATEMENT_CONTRACT.md`: these are
model-scoped mathematical statements about the defined phasor model. Nothing
here is an empirical claim, and the novelty note about the timestamp-delay
phasor identity and weighted delay-variance budget is a novelty reference, not
a priority claim.
