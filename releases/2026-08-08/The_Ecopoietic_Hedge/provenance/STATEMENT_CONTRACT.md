# Run 117 frozen statement contract

Candidate: `Run-117-EcopoieticHedge-attempt-1`

Source: corrected pre-Aristotle overlay `Run-117_ecopoietic-hedge-theorem-r1`

Namespace: `Viridis.EcopoieticHedge`

Module: `EcopoieticHedge`

The following five load-bearing theorem declarations are frozen exactly as
written in `EcopoieticHedge.lean`:

1. `reciprocal_two_regime_maximin_equal_split`
2. `reciprocal_diversification_gain`
3. `target_probability_dose_saving`
4. `uniform_dominance_implies_monoculture_optimal`
5. `identical_strains_zero_diversification_gain`

The auxiliary theorem `ecopoietic_hedge_nonvacuous` is also required. It is a
concrete witness that the reciprocal assumptions can hold and that the mixed
allocation strictly improves the worst-case exponent.

Contract rules:

- Preserve every definition and theorem type exactly.
- Replace every `sorry` with a kernel-checkable Lean proof.
- Do not add axioms, `admit`, `sorryAx`, unsafe declarations, or proof escapes.
- Do not weaken hypotheses, conclusions, strictness, uniqueness, or the
  pointwise dominance conclusion.
- The final module must build with Lean `v4.28.0` and mathlib `v4.28.0`.
