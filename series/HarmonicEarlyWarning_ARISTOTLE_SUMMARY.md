# Summary of changes for run 205845a5-32b5-4396-9702-badb54dc02ad
All 11 `sorry` placeholders in `HarmonicEarlyWarning.lean` (module `HarmonicEarlyWarning`, namespace `HEWT`) are now proved. The named theorem statements and conclusions were preserved verbatim.

Results discharged:
- R1 `fdt_variance_equals_susceptibility` — `Var = Dn * chi` (algebraic identity).
- R1 `ews_variance_diverges` — `Var(eps) → +∞` as `eps → 0+` (rpow with exponent `-m < 0`, requires `m > 0`).
- R2 `detection_dissipation_floor` — `2·kB·log 2 + slack ≥ 2·kB·log 2`.
- R2 `early_warning_floor_pos` — `0 < 2·kB·log 2` (uses `Real.log_pos`, i.e. `log 2 > 0`).
- R3 `wu_wei_crossover_closed_form` — `cp(epsStar) = ca` via rpow inverse `((ca/kappa)^(1/m))^m = ca/kappa`.
- R3 `passive_dominates_below_crossover` — strict domination on `(0, epsStar)` via strict monotonicity of `eps ↦ kappa·eps^m`.
- R4 `effective_sample_collapse` and `ews_snr_degrades` — both `→ 0` as `eps → 0+` (rpow exponents `m`, `m/2 > 0`).
- R4 headline `optimal_detection_distance_interior` — `HasDerivAt (detStat) 0 (epsOpt)`: differentiated `eps^m·(eps0^m − eps^m)^2` and used the first-order condition `eps^m = eps0^m/3` at `epsOpt = eps0·3^(−1/m)` (via `Real.hasDerivAt_rpow_const`).
- R4 `optimal_detection_distance_interiority` — `0 < epsOpt < eps0` since `3^(−1/m) ∈ (0,1)`.
- R6 `detection_efficiency_cos_sq` — `0 ≤ cos²Θ ≤ 1`.

Verification: `HarmonicEarlyWarning` builds successfully; `grep` confirms no `sorry` remains in code (only in the descriptive header comment); and `#print axioms` on every named theorem reports exactly `{propext, Classical.choice, Quot.sound}`.

Note: three preserved hypotheses (`hkB` in `detection_dissipation_floor`, `hN0` in `effective_sample_collapse`, `hS0` in `ews_snr_degrades`) turn out to be logically unnecessary for their conclusions, so the build emits unused-variable lint warnings for them. I kept them because the instruction was to preserve the theorem statements verbatim; the theorems remain non-vacuous (their conclusions are genuine, non-trivial claims). No definitions were strengthened and no conclusion was collapsed to a triviality.