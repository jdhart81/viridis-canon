# ARISTOTLE FORGE — Verified Landing Summary

**Module:** `SymbioticIntelligenceBound` (Viridis.SymbioticIntelligenceBound)
**Origin:** science-engine nightly **Run 072** (2026-06-17) — [01] Intelligence Bound × 🌿 Symbiosis. The Symbiotic Intelligence Bound (SIB) & the Thermodynamic Good Regulator. **14th self-application of the Intelligence Bound**; rate/flow twin of Run-067's Symbiotic Valuation Theorem (SVT).
**Aristotle project:** `a0660ac8-5fef-4e22-b779-254fe09ca47e` (agent run `09f7fe35-a336-4947-adfa-38fc27e7cc93`)
**Submitted:** 2026-06-19T06:05Z · **Polled COMPLETE:** 2026-06-19T12:01Z · one project in flight (budget throttle honored).
**Toolchain:** leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff
**Backlog rank at submit:** Rank 0 (PROVE-VIA-ARISTOTLE + PUBLISH-CANDIDATE, novelty 5).

## Status: ✅ VERIFIED CLEAN

- **0 `sorry`** in `SymbioticIntelligenceBound.lean` (grep count = 0; no occurrence even in comments).
- **Axiom audit** (prover `#print axioms` on every named theorem): depends only on `{propext, Classical.choice, Quot.sound}` — within the allowed set.
- **`lake build` clean** — no errors. Sole linter note: one unused-variable warning (`hεL` in `joint_bound_from_partners`), intentionally retained to keep the theorem statement verbatim.
- **All 5 named statements preserved verbatim and non-vacuous** (explicit non-vacuity witnesses in each docstring).

## Theorems landed (5)

1. **`joint_bound_from_partners`** — Each partner's intelligence rate obeys its standalone IB ceiling `P·D/εL` plus the predictive subsidy `Φ` from the other; when the directed subsidies cancel at the coupled fixed point (`Φ_EA + Φ_AE = 0`), the two per-partner bounds sum to the *joint* IB with subsidies gone (`dIA + dIE ≤ (PA·DA + PE·DE)/εL`). Proof: `add_le_add` + `add_div` + `linarith`. Non-vacuous witness gives tight `2 ≤ 2`.
2. **`ness_reciprocity`** — No-free-lunch reciprocity at NESS: information stationarity (`İ^A + İ^E = d/dt I`, `d/dt I = 0`) forces `iA = -iE` (bit-for-bit regeneration). Proof: `linarith`.
3. **`no_perpetual_learning`** — A strictly positive net subsidy bounded by total entropy production (`0 < Φ_net ≤ σ_total`) forces strictly positive dissipation (`0 < σ_total`). Proof: `linarith`.
4. **`symbiotic_surplus_threshold`** — Mutualism-vs-parasitism threshold: `0 ≤ Δsym ↔ σ_hk ≤ Φ_EA + Φ_AE` for `Δsym = (Φ_EA + Φ_AE) − σ_hk`. Proof: iff both directions via `linarith`.
5. **`cos_sq_extraction_bounded`** — Universal cos²Θ extraction-efficiency bound: with Cauchy–Schwarz `inner² ≤ na·nE` (na,nE>0), efficiency `cos²Θ ∈ [0,1]`, saturating at perfect alignment. **7th canon appearance of the universal cos²Θ geometry.** Proof: `positivity` (lower) + `div_le_one` (upper).

## Flagged deviation (reviewed — no meaning change)
- **Build fix only:** the submitted `lakefile.toml` used the deprecated `[package]` table format, rejected by lake under v4.28.0 ("missing required key: name"). Prover rewrote it to current top-level-keys format (package name/defaultTargets at top level, `[leanOptions]`, `[[require]] mathlib`, `[[lean_lib]]`), same configuration. **No theorem statement, conclusion, or target changed.**

## Routing & gate
- **Route (recommended):** spine + branch (**Nature Machine Intelligence / PNAS**) per CANON_BACKLOG Rank 0 and DISCOVERIES_TO_PURSUE Run-072 PUBLISH-CANDIDATE tag (flow half of a stock+flow pair with SVT). **Per G-SPINE-FREEZE (spine frozen at v9, 20724138):** absent explicit Justin OK, this defaults to a **standalone / S-series** deposit, not a v10 spine edit (CTT/ETT precedent).
- **Hold check:** SIB is the AI–biosphere **symbiotic-intelligence rate law** (two-body IB), **NOT the IB↔NPP biosphere-productivity duality** (`Bridge_BiosphereProductivity`). **G-TURYSHEV-PUBLICATION does NOT gate it** → ledger status **⏳ AWAITING JUSTIN OK** (not 🔒 HELD). Forge verifies/lands only — never promotes to canon, never deposits to Zenodo.

## Deferred (queued, not submitted — budget + statement-form throttle)
From the Run-072 queued list: `rate_subsidy_vanishes_at_equilibrium`, `mutualism_requires_distinct_fluctuation_sources` (Result 3 — distinct-fluctuation-source/covariance machinery), `regulator_quality_capped_by_intelligence_bound` / `regulator_IB_ceiling`, `sib_joint_bound_eq_global_second_law` (global second-law form). Candidates for a future dedicated run.
