# EET — Effortless Equilibrium Theorem (the Steersman) — ARISTOTLE FORGE LANDING

**Status:** VERIFIED CLEAN
**Landed:** 2026-07-13 (forge MODE P, ~00:0x UTC 2026-07-14 poll cycle)
**Aristotle project_id:** `65ae007a-5c0f-4605-9027-0402c42ca0c6`
**Aristotle internal run:** `402b0489-6a7d-4930-8440-b27df095a552`
**Source:** nightly Run 097 — [13] Computational Theory x Alignment, 39th IB self-application; PROVE-VIA-ARISTOTLE + PUBLISH-CANDIDATE, novelty 4/5.
**Module:** `EffortlessEquilibrium` · namespace `Viridis.Computation.EffortlessEquilibrium`
**Toolchain:** leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff (MCET Lake template).

## Verification result
- 11 named theorems, 11 `sorry` discharged -> 0 `sorry` (grep-confirmed outside comments).
- Axiom audit: `#print axioms` on every one of the 11 named theorems reports dependence only on `[propext, Classical.choice, Quot.sound]`. Within the permitted set.
- Non-vacuity: hypotheses are the stated physical positivity constraints; `eet_nonvacuous` exhibits an explicit witness (gamma=1, g_a=0 zero-cost attractor vs g_b=1 positive-cost non-attractor) that binds both branches.
- Statements preserved verbatim — no auxiliary definition strengthened, no conclusion weakened. Only cleanup: `[InnerProductSpace R E]` narrowed from the shared `variable` line onto the two R6 drive-alignment lemmas that need it (removes unused-section-variable linter warnings; no statement altered).

## The 11 named theorems
1. `wuwei_totality_min_exists` (R1) — a rest state EXISTS on nonempty compact X (EVT via `IsCompact.exists_isMinOn`).
2. `rest_state_iff_grad_zero` (R3) — rest iff grad Phi = 0.
3. `forcing_nonattractor_no_rest` (R3) — forced non-attractor is unsatisfiable.
4. `holding_power_nonneg` (R5) — P_hold = gamma^-1 ||grad Phi||^2 >= 0.
5. `zero_holding_power_iff_grad_zero` (R5, BOXED) — wu wei = the unique zero-holding-power action.
6. `nonattractor_holding_power_pos` (R5) — forced non-attractor drains P_hold > 0.
7. `harmonization_cheaper_than_forcing` (R4, BOXED) — attractor target 0-cost < any non-attractor.
8. `steersman_ib_floors_forcing_time` (R5, BOXED) — IB floor t >= I·k_BT·ln2/(P·D); 39th IB self-application.
9. `drive_alignment_efficiency_eq_cos2_theta` (R6) — eta = cos^2 Theta identity.
10. `drive_alignment_efficiency_nonneg_le_one` (R6) — eta in [0,1] via Cauchy-Schwarz.
11. `eet_nonvacuous` — explicit binding witness.

## DEFERRED (well-posedness gate — cited, NOT re-proven)
External completeness theorems, not self-contained non-vacuous propositions; deliberately NOT submitted:
- R1 `W in CLS = PPAD cap PLS`
- R2 CLS-completeness of gradient descent (FGHS 2021)
- R3 TFNP->FNP class transition + PPAD/NP-hardness (DGP 2009; JPY 1988)

## Provenance / next stage
Landed to `new leans/` only. NOT promoted to canon, NOT deposited to Zenodo. Ledger row added AWAITING JUSTIN OK (Tier: spine + branch, per PUBLISH-CANDIDATE). Canon promotion + Zenodo deposit are the separate human-gated `viridis-canon-submission` stage, gated on Justin's ledger OK.
