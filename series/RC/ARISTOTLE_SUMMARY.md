# Summary of changes for run 7790b6b3-fe3c-4011-93b2-2a435b022c7b
Re-ran the frozen Run-128 project exactly as delivered. No file was modified, added, or removed (working tree unchanged, 0 differences); no Git write operation, no theorem, definition, proof body, namespace, witness, statement, or toolchain change.

TOOLCHAIN (as pinned in the project, unmodified)
- Lean: `leanprover/lean4:v4.28.0` (`lean-toolchain`)
- Mathlib: revision `8f9d9cff6bd728b17a24e163c9402775d9e6a365` (verified in `.lake/packages/mathlib`)

BUILD EVIDENCE
- `lake build PaperFormalization`: `Build completed successfully (8027 jobs).`, 0 errors.
- `lake build` (all default targets): `Build completed successfully (8027 jobs).`, 0 errors.
- Only warnings emitted are the four pre-existing `unused variable` linter notices (`hy`, `hvY`, `hcX` at `PaperFormalization.lean:83-84`, `hvY` at `:132`), i.e. the paper's standing positivity hypotheses retained verbatim. No linter is disabled.
- `lake env lean AxiomCheck.lean`: elaborates with 0 errors and emits the 13 `#print axioms` lines below.

AXIOM EVIDENCE — every named target in `AxiomCheck.lean` reports exactly `[propext, Classical.choice, Quot.sound]`:
1. `Viridis.Run128.PaperFormalization.bilateral_benefit_iff_reciprocity_corridor`
2. `...strict_corridor_nonempty_iff_product_condition`
3. `...share_coordinate_corridor_equivalence`
4. `...nash_midpoint_unique_maximizer`
5. `...bandwidth_scaling_cannot_restore_feasibility`
6. `...witness_feasible_product_condition`
7. `...witness_infeasible_product_condition`
8. `...witness_C1_benefit`
9. `...witness_C1_no_benefit`
10. `...witness_C2_corridor_nonempty`
11. `...witness_C2_corridor_empty`
12. `...witness_C3`
13. `...witness_C4`

Additionally checked (outside the project tree, no project file touched) the three supporting lemmas `ratio_interval_nonempty_iff_product_condition`, `share_payoff_identities`, `qL_lt_qU_iff_product_condition`: each also depends only on `[propext, Classical.choice, Quot.sound]`. The in-file `#print axioms` block of `PaperFormalization.lean` reproduces the same output for the four frozen targets and the sealed claim-inventory auxiliary target during the build.

HYGIENE SCAN
A repository-wide search over all Lean sources found no `sorry`, `admit`, `sorryAx`, `axiom`, `implemented_by`, `native_decide`, `unsafe`, `extern`, or `set_option` occurrence. The only textual matches for those tokens anywhere in the project are inside prose/JSON documentation files (`ARISTOTLE_PROMPT.md`, `EXACT_STATEMENT_CONTRACT.md`, `FORMALIZATION_AUDIT.json`, `FORMALIZATION_SUMMARY.md`, `REPAIR_RECEIPT.json`) and one descriptive comment line in `PaperFormalization.lean`; none is a Lean construct.

The Properties table lists the four frozen targets, the sealed claim-inventory auxiliary target, and the eight non-vacuity witnesses, all marked proved against this build, together with the model and share-coordinate definitions the statements are phrased in terms of.

Scope: this is proof execution only. No claim of novelty, empirical validation, submission eligibility, publication readiness, or reconciliation is made; the paper and significance gates remain separately held.