# Summary of changes for run 0eb65ace-be8a-40fc-b037-a0b6ff9e32da
## Result: clean pinned build, all six targets and all seven witnesses proved, only the three permitted axioms

The frozen project was re-run exactly as delivered. No theorem, definition, proof body, namespace, witness, toolchain pin, or statement contract was altered; no file was added, edited, or removed; no Git command was run.

### Environment (verified, not assumed)
- `lean-toolchain` → `leanprover/lean4:v4.28.0`
- `.lake/packages/mathlib` HEAD → `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- `.lake/packages/mathlib/lean-toolchain` → `leanprover/lean4:v4.28.0`

### Build evidence
All `PaperFormalization*` build artifacts were deleted and regenerated from scratch, then `lake build` was run again to confirm reproducibility. Both runs:

```
✔ [8026/8031] Built PaperFormalization.Defs
✔ [8027/8031] Built PaperFormalization.Algebra
✔ [8028/8031] Built PaperFormalization.Ensemble
✔ [8029/8031] Built PaperFormalization
✔ [8030/8031] Built PaperFormalization.Witnesses
Build completed successfully (8031 jobs).
```
`lake build` exit code: `0`. Zero errors and zero warnings across all five modules.

### `#print axioms` evidence (`lake env lean AxiomCheck.lean`, exit code 0)
Each of the thirteen names reports exactly `[propext, Classical.choice, Quot.sound]`:

Six targets — `shared_channel_inverse`, `directional_gain_bounds`, `rank_deficient_unit_gain`, `worstcase_deadline`, `top_subspace_mean_cost`, `isotropic_rank_fraction`.

Seven witnesses — `witness_shared_channel_inverse`, `witness_directional_gain_aligned`, `witness_directional_gain_orthogonal`, `witness_rank_deficient_unit_gain`, `witness_worstcase_deadline`, `witness_top_subspace_mean_cost`, `witness_isotropic_rank_fraction`.

All names are in namespace `Viridis.Run125.PaperFormalization`. No `sorryAx` and no other axiom appears anywhere in the output.

### Escape-hatch scan
A regex scan over `AxiomCheck.lean`, `PaperFormalization.lean`, and `PaperFormalization/` for `sorry`, `admit`, `sorryAx`, `axiom`, `@[implemented_by]`, `native_decide`, `unsafe`, `@[extern]`, `partial`, and `set_option` returned no matches. (The only textual occurrence of the substring "admit" in the tree is the ordinary English word "admits" inside a docstring in `Ensemble.lean`, not a tactic.)

### Contract conformance
I checked the source against `EXACT_STATEMENT_CONTRACT.md` declaration by declaration. The nine model primitives in `PaperFormalization/Defs.lean`, the six target signatures in `PaperFormalization.lean`, the corollary `top_subspace_mean_cost_of_isSymm`, `exists_sorted_spectral_decomposition`, the three faithfulness bridges (`sqNorm_eq_euclideanNorm_sq`, `gain_eq_cost_ratio`, `mean_quadratic_eq_trace`), and the seven witnesses in `PaperFormalization/Witnesses.lean` all match the contract, with module names, namespace, hypotheses, and conclusions preserved.

I also read the proof bodies. They are direct mathematical arguments (projector algebra and the resolvent identity for C1–C2, a kernel vector for C3–C4, the Ky Fan combinatorial bound plus a sorted spectral decomposition for C5, and the trace-equals-rank identity for C6); none is vacuous or driven by a contradictory hypothesis. Each witness instantiates *all* hypotheses of its target with concrete `m = 2` data, so none of the six targets is vacuously true.

The live Properties table records the model definitions plus the six targets and the witness bundle, each marked proved against this build.

No novelty, empirical validation, submission eligibility, publication readiness, or reconciliation is claimed here; this return is proof execution only.
