# ARISTOTLE FORGE — Landing Summary

**Item:** The Deadline-Carnot Theorem (DCT / *the Stoker*)
**Nightly source:** Run 106 — `[09] Intelligence Capacity Framework × 🔥 Thermodynamic`
**Module:** `DeadlineCarnot.lean` — namespace `Viridis.Stoker.DeadlineCarnot`
**Toolchain / Mathlib:** leanprover/lean4:v4.28.0 / Mathlib pin 8f9d9cff
**Aristotle project_id:** `5b1b42ae-daf1-47cb-8a74-753e70793196`
**Aristotle run_id:** `685443b9-9b9e-4f07-8980-b7adbe81e08a`
**Submitted:** 2026-07-22T12:08:45Z · **Landed:** 2026-07-22T18:0xZ
**Status:** VERIFIED CLEAN

## Verification (independent re-check at landing)
- 0 `sorry` outside comments (code-only scan). 0 `admit`.
- 17 named theorems compile: 16 R-mapped headline/structural results + `dct_nonvacuous` concrete witness.
- Aristotle axiom audit reports exactly the permitted set: {propext, Classical.choice, Quot.sound} — no new axioms, no `implemented_by`.
- Named theorem statements and conclusions preserved verbatim; no auxiliary definition strengthened.

## Theorems landed
- R2 mccandlish_hyperbola_batch_invariant
- R3 tau_of_b_monotone_decreasing, tau_of_b_gt_tau_floor, tau_floor_is_b_to_infinity_limit, deadline_infeasible_below_floor
- R4 (headline — Deadline-Carnot efficiency law) dused_of_tau_matches_bstar_substitution, deadline_carnot_efficiency_eq_one_minus_floor_over_tau, eta_strictly_increasing_in_tau, eta_tendsto_one_atTop, d_used_diverges_at_floor
- R6 sqrt_correction_generic_near_critical_floor, totalcost_convex_on_feasible_domain
- R5 golden_rule_tau_star_closed_form, golden_rule_eta_star_equals_x_over_one_plus_x
- R7 tau_floor_linear_in_N_at_fixed_data
- R8 (generic structural substitute) stoker_realized_rate_bounded_above_by_floor_rate
- Non-vacuity witness dct_nonvacuous

## Deferred (gate-check, NOT submitted — empirical-fit, not calibration-independent Lean identities)
- R1 Chinchilla FOC matching external literature-fitted constants.
- R8 numeric-ceiling half — external literature-calibrated Chinchilla optimum + illustrative infra constants. Both already verified in verify_106.py (21/21 PASS); a generic structural R8 substitute was formalized instead.

## Downstream (human-gated — NOT done by the forge)
- Added to ZENODO_SUBMISSION_LEDGER.md -> AWAITING JUSTIN OK (no publication hold applies; GCT hold unrelated, G-TURYSHEV lifted).
- NOT promoted into 01_MATHLIB/Aristotle-Pipeline/, canon lakefile untouched, no Zenodo deposit. Those are the viridis-canon-submission task + --publish, gated on Justin's ledger OK.
