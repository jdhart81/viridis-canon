# Summary of changes for run dc20d215-1890-45d9-84f4-1cc6283b50a6
Re-ran the frozen Run-130 project exactly as supplied. No file, theorem, definition, proof body, namespace, witness, toolchain, or contract text was altered, and no Git operation was performed.

**Toolchain evidence (matches the contract)**
- `lean-toolchain`: `leanprover/lean4:v4.28.0`; `lake --version` → `Lake version 5.0.0-src+7e01a1b (Lean version 4.28.0)`.
- Mathlib package HEAD: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

**Build evidence**
- `lake build PaperFormalization` → exit code `0`, `Build completed successfully (8031 jobs)`, `0` errors. All project modules built: `PaperFormalization.Defs`, `PaperFormalization.Hall`, `PaperFormalization.Certificate`, `PaperFormalization.Witnesses`, `PaperFormalization`. The only diagnostic is a non-fatal linter warning `Certificate.lean:250:5: unused variable 'hlt'`, which is the disclosed blocker B2 (hypothesis retained because the paper states it) and was deliberately left unchanged.
- `lake env lean AxiomCheck.lean` → exit code `0`, all twelve `#print axioms` lines emitted, no errors.

**Axiom output — all twelve named targets depend on `[propext, Classical.choice, Quot.sound]` and nothing else:**
- `Viridis.Run130.PaperFormalization.seed_routing_common_fraction_eq_min_cut_ratio` (C1)
- `Viridis.Run130.PaperFormalization.seed_routing_feasible_iff_cut_conditions` (C2)
- `Viridis.Run130.PaperFormalization.capacity_outside_active_bottleneck_irrelevant` (C3)
- `Viridis.Run130.PaperFormalization.scenario_intersection_certificate_le_each_scenario` (C4)
- `Viridis.Run130.Hall.exists_routing_of_hall` (capacitated Hall support theorem)
- `Viridis.Run130.Witnesses.C1_witness`, `C1_witness_nontrivial`, `C2_witness_infeasible`, `C2_witness_feasible`, `C3_witness`, `C4_witness`, `negative_control_arbitrarily_severe`

**Escape-hatch scan**
A search across every `.lean` file for `sorry`, `admit`, `sorryAx`, `native_decide`, `unsafe`, `extern`, `implemented_by`, and top-level `axiom` returns exactly one hit: the descriptive prose line `PaperFormalization.lean:21`, inside the module docstring. There is no such construct in any declaration, and the absence of `sorryAx` from every axiom listing above confirms this at the kernel level.

**Statement-contract check**
The four frozen target signatures at the project root, the model definitions (`IsFeasibleFraction`, `cutRatios`, `certificate`, `scenarioIntersection`, `nbhd`, `demand`, `supply`), the Hall support theorem signature, and the witness names all match `EXACT_STATEMENT_CONTRACT.md` as given. The Properties table has been populated with the four targets, the Hall support theorem, the seven named witnesses, and the definitions the statements are phrased in terms of, each marked from the verified build.

No claim of novelty, empirical validation, submission eligibility, publication readiness, or reconciliation is made; this is proof-execution evidence only.