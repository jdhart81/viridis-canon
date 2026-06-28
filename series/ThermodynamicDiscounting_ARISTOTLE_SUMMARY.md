# ARISTOTLE FORGE — Landing Summary

**Module:** `ThermodynamicDiscounting.lean`
**Namespace:** `Viridis.Economics.ThermodynamicDiscounting`
**Theorem name:** Thermodynamic Discounting Theorem (TDT) — *the Appraiser*
**Source nightly:** Run 080 — [02] Thermodynamic Economics × discounting / value-of-time
**Aristotle project_id:** `7952aa91-08ad-4f6d-8ef9-f2265eccf93d`
**Aristotle agent_task_id:** `29ec9160-5b23-4c04-a7be-735a287732d9`
**Submitted:** 2026-06-26T12:08Z · **Completed:** 2026-06-26T12:21Z (~13 min)
**Toolchain:** leanprover/lean4:v4.28.0 · **Mathlib pin:** 8f9d9cff6bd728b17a24e163c9402775d9e6a365
**Status:** VERIFIED CLEAN

## Verdict
Agent task COMPLETE (100%). All six `sorry`s discharged with no change to any
theorem statement or conclusion. No auxiliary definition strengthened, no conclusion
weakened.

## Gates (forge verification)
- 0 sorry / 0 admit outside comments — sole textual `sorry` is the doc-comment on line 28.
- No `axiom` declarations, no `native_decide`.
- Axiom audit (prover `#print axioms` on every named theorem): subset of {propext, Classical.choice, Quot.sound}.
- Full `lake build` succeeds.
- Non-vacuity: confirmed per theorem (positivity hypotheses load-bearing; `tdt_nonvacuous`
  is a genuine strictly-positive witness `0 < rThermo 2 1 1 1`, not a collapsed tautology).

## Named theorems (statements preserved verbatim)
1. `thermo_discount_rate_eq_lambda_over_value` (R1) — `r_thermo * V = lambda` (shadow-price/value identity; consumes `V != 0`).
2. `discount_rate_zero_in_abundant_time_regime` (R2 pole) — `tcrit A B <= T => r_thermo = 0` (Stern pole; restoration headroom => zero endogenous discounting).
3. `discount_rate_diverges_at_tipping` (R3) — `Tendsto (fun A => rThermo A B V T) atTop atTop`; critical slowing-down tau*->inf drives the rate to +inf.
4. `pv_kernel_recovers_tvt_at_zero_lambda` (R4) — zero shadow price collapses the discount kernel to 1 (PV reduces to undiscounted TVT, Run 047).
5. `stern_nordhaus_regime_dichotomy_monotone_single_crossover` (R5 flagship) — one law, two regimes about the single critical horizon tau* = sqrt(A/B): zero on [tau*,inf), strictly positive on (0,tau*), strictly decreasing on the scarce branch => single crossover.
6. `tdt_nonvacuous` — witness `0 < rThermo 2 1 1 1` (scarce regime: tau*=sqrt 2 > 1, lambda = 1).

## Provenance / pipeline
- Landed from forge tarball member `forge_project_aristotle/`.
- Raw prover summary preserved alongside as `ARISTOTLE_SUMMARY_raw.md`.
- NOT promoted to canon, NOT deposited to Zenodo (both Justin-gated).
- Recorded on `ZENODO_SUBMISSION_LEDGER.md` AWAITING JUSTIN OK.

## Hold check
TDT is the thermodynamic-economics discount-rate law (value-of-time / Stern-Nordhaus
reconciliation), NOT the IB<->NPP duality. G-TURYSHEV-PUBLICATION does not gate it (and was
lifted 2026-06-20). No active publication hold applies => AWAITING JUSTIN OK (not HELD).
