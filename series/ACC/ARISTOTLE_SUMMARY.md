# Summary of changes for run 3d415726-308e-4cec-85cf-c62b2c46c994
## Run-129 anytime change certificate — verified LEAN_PROOF return

The complete `PaperFormalization` project was built and verified as received. **No Lean source, contract, inventory, receipt or configuration file was modified**: every `.lean` file, `EXACT_STATEMENT_CONTRACT.md`, `AxiomCheck.lean`, `SEALED_CLAIM_INVENTORY.json`, `SOURCE_BINDING.json`, `FORMALIZATION_AUDIT.json`, `FORMALIZATION_SUMMARY.md`, `PROOF_STAGING_RECEIPT.json`, `lakefile.toml` and `lean-toolchain` hash exactly as recorded in `input_sha256` of `ARISTOTLE_FORGE_REQUEST.json`. No definition, statement, target name or non-vacuity obligation was weakened, renamed, reinterpreted or changed.

### Environment (matches the required pins exactly)
- Lean `4.28.0` (`leanprover/lean4:v4.28.0`; binary commit `7e01a1bf5c70fc6167d49c345d3bf80596e9a79b`), Lake `5.0.0-src+7e01a1b`
- Mathlib checkout at revision `8f9d9cff6bd728b17a24e163c9402775d9e6a365`, toolchain `v4.28.0`

### Build evidence
`lake build PaperFormalization` completes successfully (8033 jobs, exit 0), compiling `Prior`, `Mixture`, `Dominance`, `NullMartingale`, `Wald`, `Witnesses` and the root module. In addition, each of the six modules was re-elaborated from source directly with the compiler: all six exit 0 and emit **no output at all** — no errors, no warnings, no `sorry` diagnostics.

### `#print axioms` output (as requested by `AxiomCheck.lean`)
`lake env lean AxiomCheck.lean` exits 0 and reports, for all eight requested declarations — the four frozen targets `anytime_change_mixture_martingale`, `anytime_change_ville_certificate`, `change_component_dominance_and_penalty`, `bounded_overshoot_expected_delay`, and the four non-vacuity obligations `C12Witness.c12_nonvacuous`, `C12Witness.c2_sup_nonvacuous`, `C3Witness.c3_nonvacuous`, `C4Witness.c4_nonvacuous` — dependence on exactly `[propext, Classical.choice, Quot.sound]` and nothing else. The verbatim output is stored in `AXIOM_CHECK_OUTPUT.txt`.

Going beyond the eight names, an environment-wide axiom sweep over the built library reports `checked 116 declarations; disallowed-axiom users: []`, i.e. every public declaration under `Viridis.Run129.PaperFormalization` depends only on the three allowed axioms. No `sorryAx` appears anywhere.

### Proof-escape scan
A source scan of `PaperFormalization.lean`, `PaperFormalization/*.lean` and `AxiomCheck.lean` for `sorry`, `admit`, `sorryAx`, `axiom`, `implemented_by`, `native_decide`, `unsafe`, `extern`, `macro_rules` and `set_option` returns **no occurrence at all**.

### Contract conformance
All four frozen targets are present under their contract names in namespace `Viridis.Run129.PaperFormalization` and are proved, along with the literal supremum form `anytime_change_ville_certificate_sup`, the supporting results `hasSum_changePrior_tail` / `hasSum_changePrior`, `component_le_mixture`, `ville_inequality` / `ville_inequality_sup`, `component_crossing_iff_evidence`, the two late-change-penalty asymptotics theorems, `wald_identity` (proved in-project, not assumed), and the explicitly model-dependent corollary `landauer_erasure_corridor`. All four non-vacuity obligations are proved at their explicit witness models.

### Files added
Only two evidence files: `BUILD_EVIDENCE.md` (full provider build evidence, environment table, escape scan, contract conformance table, input-hash table) and `AXIOM_CHECK_OUTPUT.txt`.

One recorded deviation, in a non-Lean file: `lake-manifest.json` differs from the hash in the request. It was already in that state on receipt — it is the build environment's local manifest, whose dependency entries are `path` entries pointing at pre-materialized `.lake/packages/*` checkouts rather than remote git entries. It records the same package set, and the Mathlib checkout it points at is verified to be exactly `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. This is documented in §7 of `BUILD_EVIDENCE.md`.

### Scope
As instructed, no Git command was run and no branch, commit, tag or push was created; no remote or other external system was contacted or mutated. The returned project directory is the deliverable. This return is a proof-and-build verification only: it makes no claim of empirical validation, reconciliation, ledger or canon admission, publication readiness, or publication authority. The separate classification state `HOLD_SIGNIFICANCE_NOT_INDEPENDENTLY_CLEARED` is untouched and is not cleared by this job.
