# Summary of changes for run 02c218c8-3443-4f11-84df-d06bc57e2ae5
Run-141 `LEAN_PROOF` job is COMPLETE. All seven frozen named targets in module `SymbioticEqualization`, namespace `Viridis.ThermodynamicSpeedLimits.SymbioticEqualization`, are proved with zero `sorry`.

**Statement integrity.** `slowRate`, all theorem statements, hypotheses, namespace, module name, `lean-toolchain`, `lakefile.toml` Mathlib pin, `lake-manifest.json`, and `STATEMENT_CONTRACT.json` are unchanged. The only additions to `SymbioticEqualization.lean` are the proof bodies plus three `private` auxiliary lemmas inside the same namespace (`disc_nonneg`, `sq_sqrt_disc`, `two_k_le_sqrt_disc`). No Git command was run that mutates anything; nothing was committed, pushed, or published.

**Execution environment (resolved).**
- Toolchain: `leanprover/lean4:v4.28.0` — reported as `Lean (version 4.28.0, x86_64-unknown-linux-gnu, commit 7e01a1bf5c70fc6167d49c345d3bf80596e9a79b, Release)`.
- Mathlib requested (attempt 3): `8f9d9cff6bd728b17a24e163c9402775d9e6a365`. Lakefile pin, `lake-manifest.json` `rev`, and the resolved dependency checkout HEAD all equal that commit exactly. Lake prints a benign "manifest out of date" notice only because the manifest records `inputRev` `v4.28.0` alongside the explicit pinned rev; no `lake update` was run, so the pin and manifest stay frozen.
- Build: `lake build` → SUCCESS, 8027 jobs, 0 errors. The only warnings are unused-variable linter notices for frozen hypotheses (`ha`/`hb`/`hk`) that the finished proofs do not require; they are retained verbatim as the contract mandates.
- A scan for `sorry`, `admit`, `sorryAx`, `axiom`, `implemented_by`, `native_decide`, `unsafe`, `extern` in the source returns no matches.

**Per-declaration `#print axioms` (via `lake env lean AxiomCheck.lean`)** — each of `slow_rate_characterization`, `slow_rate_lower_min`, `slow_rate_upper_mean`, `slow_rate_monotone`, `equal_rates_no_gain`, `finite_asymmetry_strict_mean`, `symbiotic_equalization_nonvacuous` depends on exactly `[propext, Classical.choice, Quot.sound]`, i.e. strictly within the allowed set.

**Mathematical content.** Writing `s = √((a−b)² + 4k²)`: the characterization follows from `s² = (a+b+2k)² − 4(ab + k(a+b))`; the lower bound from `s ≤ |a−b| + 2k`; the mean bound from `2k ≤ s`; monotonicity in `k` from `√(d+4k₂²) ≤ √(d+4k₁²) + 2(k₂−k₁)`, which reduces to `√(d+4k₁²) ≥ 2k₁`; `slowRate a a k = a` since `s = 2k` there; strictness under `a ≠ b` since then `2k < s`. The non-vacuity witness evaluates to `slowRate 1 4 1 = (7 − √13)/2 ≈ 1.697`, strictly between `1` and `5/2`.

Evidence is recorded in `PROVIDER_BUILD_RECEIPT_ATTEMPT3.json` alongside the proved source in `SymbioticEqualization.lean` and the checker `AxiomCheck.lean`.