# ARISTOTLE FORGE — SRPT (Symbiotic Risk-Premium Theorem) — VERIFIED CLEAN

- **Item:** SRPT — The Symbiotic Risk-Premium Theorem ("the Mutualist"), clean analytic core
- **Source:** nightly **Run-093** — [02] Thermodynamic Economics × 🌿 Symbiosis; 35th IB self-application; PUBLISH-CANDIDATE + PROVE-VIA-ARISTOTLE (novelty 4/5)
- **Module / namespace:** `SymbioticRiskPremium` (`SymbioticRiskPremium.lean`)
- **Aristotle project:** `a5815165-a7af-4fc5-9416-6e9b29c120a8`
- **Agent task:** `14deb694-2788-45ce-bbea-cf5e7b2ddaf9`
- **Toolchain / pin:** leanprover/lean4 v4.28.0 · Mathlib pin 8f9d9cff
- **Submitted:** 2026-07-09T12:07Z · **Landed:** 2026-07-09 (this run)
- **Aristotle status:** `COMPLETE_WITH_ERRORS` @ 100% (ProjectStatus.IDLE + has_files=True). The "errors" are unused-variable linter warnings only — they fall on hypotheses that are part of the named theorem signatures, kept verbatim to honor the preservation requirement. No statement weakened, no auxiliary definition strengthened, no conclusion collapsed to a trivial one.

## Verification (forge contract)
- **0 `sorry`** — confirmed: zero bare `sorry` tokens outside comments (the only textual match is inside the file's doc comment).
- **Axiom audit CLEAN** — every one of the nine named theorems depends only on `{propext, Classical.choice, Quot.sound}` per the Aristotle output summary.
- **Non-vacuous** — `srpt_nonvacuous` supplies an explicit positive-data witness satisfying every hypothesis; `verify.py` is 20/20 numeric PASS on concrete parameters.

## Significance Gate (RESEARCH_PIPELINE_v2) — PASS (6/6)
INV-SIG-1 NON-VACUOUS OK · INV-SIG-2 NON-TRIVIAL OK · INV-SIG-3 NOVEL OK · INV-SIG-4 FALSIFIABLE OK · INV-SIG-5 AXIOM-CLEAN OK · INV-SIG-6 HONEST-SCOPE OK. Eligible to enter the Zenodo ledger as AWAITING JUSTIN OK.

## Nine named results (PRESERVED VERBATIM)
- **R1** `risk_premium_tur_floor` — π ≥ ρ k_B/Σ: no riskless D-Capital asset at finite dissipation (TUR floor).
- **R2** `mutualistic_iff_covariance_negative` — a pair is mutualistic in risk iff covariance < 0.
- **R3** `diversification_wall_residual_positive` — strictly positive undiversifiable residual π_min ≥ ρ k_B/Σ_tot survives any hedge (the Diversification Wall).
- **R3** `markowitz_zero_variance_requires_perfect_anticorrelation` — zero-variance hedge requires perfect anticorrelation (which the TUR forbids at finite Σ_tot).
- **R5** `contagion_mutualism_transition_at_zero_covariance` — contagion/mutualism sign transition sits at zero covariance.
- **R6** `mutualist_ib_ceiling` — IB ceiling on symbiotic variance cancellation.
- **R6** `mutualist_ib_learnable_fraction_lt_one` — learnable fraction < 1.
- **R7** `hedging_efficiency_eq_cos2_theta` — hedging efficiency = cos²Θ (Cauchy–Schwarz).
- `srpt_nonvacuous` — explicit positive-data non-vacuity witness.

## Falsifiable prediction carried (P1)
Across managed ecological portfolios (salmon stock complexes, mixed-species stands), achievable diversification variance-reduction saturates at a floor π_min ≥ ρ k_B/Σ_tot set by shared energy throughput; **refuted if** a managed coupled portfolio drives risk below that floor at finite shared dissipation.

## Deferred (well-posedness gate — staged separately, NOT in this landing)
- **R4** `risk_premium_diverges_at_spectral_gap_closure` — Tendsto/atTop limit divergence (concrete-model-only per the finding).
- Full-generality Σ_tot finiteness and general-correlation (V_A ≠ V_B) Markowitz optimum.

## Disposition
LANDED VERIFIED CLEAN in `new leans/2026-07-09_aristotle_SRPT_forge/`. CANON_BACKLOG row updated to VERIFIED. Ledger row **48** appended to `ZENODO_SUBMISSION_LEDGER.md` as **AWAITING JUSTIN OK**, route **spine + branch** (Run-093 is PUBLISH-CANDIDATE). No publication hold applies (G-TURYSHEV lifted 2026-06-20; SRPT is a risk-premium/asset-pricing result unrelated to the IB↔NPP duality). NOT promoted to canon, NOT deposited to Zenodo — those remain Justin-gated.
