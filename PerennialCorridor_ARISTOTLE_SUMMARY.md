# Summary of changes for run 642dc458-e4bf-4d3f-9651-6c865b08c65e
All 15 `sorry` placeholders in `PerennialCorridor.lean` are now discharged; the project builds cleanly with `lake build` and contains no remaining `sorry`/`admit`.

Named theorem statements and conclusions were preserved verbatim. Proof approach per group:
- R1 factorization/ranking: `ring` and `mul_le_mul_of_nonneg_right`.
- R1' urgency facts over the fixed vector `phiPCT = ![1.30,1.44,1.55,1.63,1.67,0.13]`: `fin_cases`/`simp [phiPCT]`/`norm_num` decidable numeric checks.
- R2 band lemma: order-convexity via `le_total b p` then the up/down monotonicity hypotheses.
- R3 dividend: `sub_nonneg`.
- R4 IB floor: `div_nonneg`/`positivity` (using `Real.log_nonneg`) and `gcongr` for monotonicity in I.
- R5 holding power: `mul_pos`, `simp`, `mul_le_mul_of_nonneg_right`.
- R6 efficiency: `positivity` for nonnegativity and Cauchy–Schwarz (`abs_real_inner_le_norm`) with `div_le_one` for the ≤ 1 bound.
- Non-vacuity witness: κ = 1 at s = 4 gives index 1.67 > 0 with phiPCT 5 < phiPCT 4.

Flagged auxiliary-definition adjustments (needed only for compilation under this toolchain, no conclusion weakened):
- `ibFloor` marked `noncomputable` (depends on `Real.log`).
- `eta` uses the current Mathlib inner-product spelling `inner ℝ d a` in place of `(inner d a : ℝ)`; the mathematical meaning is unchanged.

Axiom audit: every named theorem depends only on `{propext, Classical.choice, Quot.sound}`, and each is non-vacuous (the urgency lemmas are genuine numeric facts over the fixed data; `pct_nonvacuous` exhibits an explicit positive-index, non-monotone-peak witness).