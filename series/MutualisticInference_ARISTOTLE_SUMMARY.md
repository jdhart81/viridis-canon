# ARISTOTLE_SUMMARY — MINT (Run 085, the Mutualist)

**Theorem:** Mutualistic Inference Network Theorem (MINT) — *the Mutualist*; 27th IB self-application; nightly Run 085 CONVERGENCE EVENT, [14] Cognitive Modeling × 🌿 Symbiosis. Lifts SIT (062) dyad → N-agent network.
**Module:** `MutualisticInference.lean` — namespace `Viridis.MutualisticInference`
**Aristotle project:** `71b77385-316c-460d-8255-c87713250db8` · agent task `a592bd11-fb71-4bb6-b4ea-15a4819432f8`
**Status:** TaskStatus.COMPLETE @100% (submitted 2026-07-02T00:05:27Z → completed 2026-07-02T00:13:04Z, ~8 min) · ProjectStatus.IDLE + has_files=True
**Landed:** 2026-07-02T (this forge run)

## Verification (independent re-check)
- sorry: 0 (raw 0, 0 after comment-strip); admit: 0; native_decide: 0; axiom decls: 0
- Axiom audit per Aristotle output_summary: every theorem ⊆ {propext, Classical.choice, Quot.sound}
- All 6 named statements verbatim; no auxiliary definition strengthened; no conclusion collapsed to trivial (Aristotle self-report + statement inspection)

## Named theorems (6, all non-vacuous)
1. `mint_network_ledger_no_penalty` (T1) — edge-subsidy ledger: (∑Inon) − (∑E Ipred) − sHigher ≤ ∑Inon (predictive commons never penalizes). `Finset.sum_nonneg` + `linarith`.
2. `mint_dyad_recovers_sit` (T2) — N=2 floor = 2 − 1/2 − 0 = 3/2, exactly the SIT dyad floor (1.500). `norm_num`. Pins the network limit to the prior certified SIT result; witnesses non-vacuity (strictly-below-solo value attained).
3. `mint_pid_subsidy_nonneg_le_total` (T3) — PID atoms ≥0 ⇒ 0 ≤ S ≤ I_total (synergistic subsidy well-defined; measure-robust sum identity; R/S split NOT asserted). `linarith` on sum identity. All four non-negativity hyps + identity load-bearing.
4. `mint_group_markov_blanket_ceiling` (T4) — additive group ceiling: ceil j ≤ ∑ ceil i (each ceiling >0). `Finset.single_le_sum`.
5. `mint_efficiency_eq_cos2_theta` (T5) — η = (∑a·b)²/((∑a²)(∑b²)) ∈ [0,1]; η=1 ⇔ proportional allocations (Fisher angle Θ=0). Discrete Cauchy–Schwarz (`Finset.sum_mul_sq_le_sq_mul_sq`) + `div_nonneg`/`div_le_one`. ha,hb load-bearing (non-zero denominator).
6. `mint_mutualist_IB_ceiling` (T6) — the 27th IB self-application: ∑ dI_i ≤ ∑ ceil_i ∧ (∑ceil − subsidy) < ∑ceil for subsidy>0. `Finset.sum_le_sum` + `linarith`. hsub load-bearing for the STRICT commons discount; open science / mutual prediction = thermodynamic optimum.

## Deferred / gate-check (NOT submitted)
- `legibility_percolation_threshold`, `per_agent_cost_sublinear`, `synergy_vanishes` — ER mean-field / measure-dependent.
- Water-fill + envelope machinery inherited from UWMT-084 (per-agent shadow price).

**Tier:** spine + branch (PUBLISH-CANDIDATE per DISCOVERIES_TO_PURSUE.md). Publication venues (rec.): Phys. Rev. X / Phys. Rev. E primary; Nature Sustainability + NeurIPS/ICML secondary. No publication hold (G-TURYSHEV lifted 2026-06-20; MINT is not IB↔NPP duality).
