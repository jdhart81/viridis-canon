# Aristotle-Pipeline — Viridis Formal Canon

**The canonical compiled Lean 4 artifacts underlying all Viridis science, methods, and publications.**

> **What "verified" means here.** These modules are **Lean-checked conditional mathematics**: each theorem's *type* is machine-verified, but a Lean-checked theorem is not automatically a verified statement about physics, economics, or ecology. Every headline result is graded by formal strength in [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md) using the labels in [`THEOREM_STATUS_TAXONOMY.md`](./THEOREM_STATUS_TAXONOMY.md). Read the matrix before citing any result as established. Integrity Release **v9.1.0** (2026-06-21) quarantined P9 and de-escalated several overstated claims; see [`CHANGELOG_v9.1.0.md`](./CHANGELOG_v9.1.0.md).

## Start here

Viridis is an independent research program studying conditional mathematical
connections among information, thermodynamics, learning, and living systems.
The repository is the reproducible source, not a claim that every model
assumption has been established in nature.

- **Inspect the exact claims:** [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md)
- **Reproduce current and historical builds:** [`REPRODUCE.md`](./REPRODUCE.md)
- **Cite the stable concept:** [10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982)
- **Report a reproduction, critique, citation, or field test:** [external-validation issue](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml)
- **Understand AI use and human responsibility:** [`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md)
- **See the current validation boundary:** [`EXTERNAL_VALIDATION.md`](./EXTERNAL_VALIDATION.md)

## Viridis research portal

This repository now includes **Viridis Canon Core**, a standard-library Python
package that converts the checked-in research artifacts into a deterministic,
machine-readable catalog. The accompanying GitHub Pages explorer makes the
formal spine, selected flagships, working corpus, quarantine state, caveats,
source hashes, and record hashes inspectable without reading the repository
tree by hand. Every public record includes a readable abstract and a full-paper
or full-source action, and the research map exposes tier, import, and topic
relationships as an interactive graph.

- Public explorer: `https://jdhart81.github.io/viridis-canon/`
- Machine interface: `https://jdhart81.github.io/viridis-canon/data/catalog.json`
- Build and architecture: [`RESEARCH_PORTAL.md`](./RESEARCH_PORTAL.md)
- Public/private product boundary: [`OPEN_SOURCE_BOUNDARY.md`](./OPEN_SOURCE_BOUNDARY.md)

The portal never publishes a result automatically. GitHub submission and pull
request templates collect the evidence; canon admission and Zenodo publication
remain explicit human decisions.

After a successful catalog build on `main`, the `sync-canon-cloud` workflow can
also update a private Canon Cloud reader. It is dormant unless
`CANON_CLOUD_URL` and the `CANON_CLOUD_SYNC_SECRET` Actions secret are
configured. Synchronization only imports the deterministic catalog; it does not
approve records or publish research.

Last updated: 2026-07-26 (v10.2.0 "The Equilibrium Wave"; historical P0
reproducibility repaired without changing declaration statements, the public
catalog regenerated, and protected-branch checks made blocking)
Lean toolchain: leanprover/lean4:v4.28.0
API: https://aristotle.harmonic.fun

---

## Module Status

| Module | File | Sorry | Status | Paper Target |
|--------|------|-------|--------|-------------|
| **P0** | `P0_IntelligenceBound_COMPILED.lean` | **0** | COMPILED under its pinned Lean 4.24 / Mathlib environment and checked by required CI | Intelligence Bound flagship; external-validation status is tracked separately |
| **P1** | `P1_DScore.lean` | **0** | COMPILED | Physical Review E (draft) |
| **P2** | `P2_HDFM_POC.lean` | **0** | COMPILED | HDFM resubmission |
| **P3** | `P3_Impossibility.lean` | **0** | COMPILED | 2nd canon paper (Goodhart impossibility / alignment-as-feasibility) |
| **P4** | `P4_ThermodynamicEconomics.lean` | **0** | COMPILED | Nature Sustainability |
| **P5** | `P5_SLSPT/` (5 files: IntelligenceBound, InverseSquare, ShadowPrice, ShadowPriceLevelCurves, SLSPTTowerOrdering) | **0** | COMPILED | Speed Limit Shadow Price Tower (24 thms; promoted from Zenodo v3 deposit 10.5281/zenodo.20006414) |
| **P7** | `P7_PlasmaNFix/` (3 files: Foundations, Energy, Integration) | **0** | COMPILED | Plasma-mediated N₂ fixation for forest C-sequestration (16 thms — Hart 2026; Nature Energy track) |
| ~~P9~~ | `P9_AI_Safety.lean` | 0 | ⚠ **EXPLORATORY — QUARANTINED v9.1.0** — vacuous `ai_conservation_alignment` (T₀=⊤); removed from `defaultTargets` and the verified guarantee (see CLAIMS_MATRIX.md) | AI Safety (non-vacuous reconstruction queued) |
| **PSIT** | `PSIT_Symplectic.lean` | **0** | COMPILED | Symplectic-conjugation theorem — Nature Physics (Hart 2026, Run-035; 8 thms) |
| **BMD** | `BoundedMemoryDissipation.lean` | **0** | COMPILED (Aristotle `6483ae65`, 2026-06-21) | **v9.1.0 INV-4 fix** — honest bounded-memory dissipation floor (`hmem` load-bearing); replaces P0's dead-`h_mem` `finite_memory_dissipation` (→ `landauer_dissipation_bound`) |
| **EcoChain** | `EcoChain_DendriticCorridor.lean` | **0** | COMPILED | Dendritic corridor formation — *Methods in Ecology & Evolution* (4 thms + 3 lemmas; Aristotle c23eab22, 2026-05-30) |
| **Book** | `Book_HeatAndDisorder.lean` | **0** | COMPILED | Formal spine of *Heat and Disorder* book — 12 thms. Foundation (7): entropy monotonicity, feedback dichotomy, saddle-node tipping threshold, energy-balance uniqueness. First-principles layer (5): strict Clausius production + gap-monotonicity, Planck climate sensitivity (Stefan–Boltzmann), **Intelligence-Bound restoration speed limit** (dI/dt ≤ P/(k_B T ln2)) + time lower bound. Aristotle a9312b60, 2026-05-31 |
| **MRAB** | `MRAB.lean` | **0** | COMPILED — **IB core-extension, promoted into the spine at v10** | Multi-Ring Alignment Bound (Thm 1; the Polymath Paradox + wu-wei saturation + UAIB reduction). 10 thms; Aristotle `65347d17`, 2026-06-21. Published standalone on Zenodo 2026-06-22; queued for a future curated spine v10 wave (spine frozen at v9). |
| **SIB** | `SymbioticIntelligenceBound.lean` | **0** | COMPILED — **IB core-extension, promoted into the spine at v10** | Symbiotic Intelligence Bound (two-body generalization of the IB; Good-Regulator rate law). 5 thms; Aristotle `a0660ac8`. Standalone DOI 10.5281/zenodo.20764638; folded into spine v10. |
| **UWMT** | `UniversalWaterfilling.lean` | **0** | COMPILED — **spine v10.1.0 ("the Keystone")** | Universal Water-Filling Meta-Theorem — unifies the 9-member shadow-price/water-filling family into one variational object (curvature + temperature control knobs; lambda = water level = shadow price = free energy). 8 thms; Aristotle `da92404c`, Run-084. |
| **GST** | `GeodesicSaturation.lean` | **0** | COMPILED — **spine v10.1.0 ("the Sage")** | Geodesic Saturation Theorem — the IB's own equality/saturation condition: dI/dt=(P-F)c, saturates iff F=0 (constant-speed Fisher-Rao geodesic). 6 thms; Aristotle `f864600a`, Run-086. |
| **EET** | `EffortlessEquilibrium.lean` | **0** | COMPILED — **spine v10.2.0 ("the Steersman")** | Effortless Equilibrium Theorem — wu-wei rest states exist, rest iff grad(Phi)=0, and holding power P_hold=gamma^-1||grad(Phi)||^2 is minimized (zero) exactly at rest; harmonization is strictly cheaper than forcing. 11 thms; Aristotle `65ae007a`, Run-097. |
| **PCT** | `PerennialCorridor.lean` | **0** | COMPILED — **spine v10.2.0 ("the Gardener")** | Perennial Corridor Theorem — Whittle-index corridor urgency ranking, band-convexity of the unimodal superlevel set, stewardship-dividend nonnegativity, and the IB floor on maintenance holding power. 15 thms; Run-098. |
| **DST** | `DecoherentSelection.lean` | **0** | COMPILED — **spine v10.2.0 ("the Chooser")** | Decoherent Selection Theorem — decision cost vanishes iff the pointer-basis eigenstate is selected, is bounded by ln N, and the einselected basis is the unique zero-waste choice; IB throughput speed limit on collapse. 12 thms; Run-099. |
| **MAT** | `MutualisticAttestation.lean` | **0** | COMPILED — **spine v10.2.0 ("the Attester")** | Mutualistic Attestation Theorem — attestation cost = kBT·ln2·(residual entropy); certification feedback has fold bistability (trap/mutualism stable states); optimal confidence is interior. 19 thms; Run-100 (100th nightly-run milestone). |
| **TAT** | `ThermodynamicAttention.lean` | **0** | COMPILED — **spine v10.2.0 ("the Attuner")** | Thermodynamic Attention Theorem — the rational-inattention shadow price equals the Landauer quantum kBT; attention water-fills the einselected slow basis per KKT; Inattention Trap below a resolvability threshold C_crit. 12 thms; Run-101. |
| **SST** | `StewardshipSetpoint.lean` | **0** | COMPILED — **spine v10.2.0 ("the Steward")** | Stewardship Setpoint Theorem — golden-rule sustainable ceiling for a living renewable stock (dD/dt=g(D)-phi*H); Tragedy collapse for phi*Omega>rho; act-budget twin of TAT. 13 thms; Run-102. |

The protected `main` branch requires the repository hygiene check, the current
Lean build and axiom audit, the pinned historical P0 build and audit, and the
deterministic catalog check. P9 remains **EXPLORATORY — quarantined** and is not
part of the verified spine.

### Bridge Theorems (cross-canon results)

| Module | File | Sorry | Status | Headline |
|--------|------|-------|--------|----------|
| **B1** | `Bridge_MissionFeasibility.lean` | **0** | COMPILED | `Feasible e m ↔ target_rate ≤ P_max / (k_B T ln 2)` — a **self-contained mission-feasibility analogue** motivated by P0/P1/P3/P4 (imports only Mathlib; the rate ceiling and D-range are built into its local predicates — see CLAIMS_MATRIX.md). Aristotle 054d616c. |

---

## Directory Structure

```
Aristotle-Pipeline/
├── P0_IntelligenceBound_COMPILED.lean   # THE FOUNDATION — 604 lines, zero sorry
├── P1_DScore.lean                        # D-Score biodiversity metric
├── P2_HDFM_POC.lean                      # HDFM graph-theoretic foundations (zero sorry)
├── P3_Impossibility.lean                 # Planetary-conservation impossibility (zero sorry)
├── P4_ThermodynamicEconomics.lean        # Thermodynamic economics (zero sorry)
├── P7_PlasmaNFix/                        # Plasma N₂ fixation (3 files, 16 thms, zero sorry)
├── P9_AI_Safety.lean                     # AI Safety — COMPILED, zero sorry
├── lakefile.toml                         # Unified build config (all modules)
├── lean-toolchain                        # v4.28.0
├── lake-manifest.json                    # Mathlib dependency lock
├── README.md                             # This file
└── _pre-aristotle-drafts/                # Archive of sorry versions + Aristotle summaries
    ├── P2_HDFM_POC_sorry.lean
    ├── P4_ThermodynamicEconomics_sorry.lean
    ├── ARISTOTLE_SUMMARY_P2.md
    └── ARISTOTLE_SUMMARY_P4.md
```

---

## Dependency Graph

```
P0 (Intelligence Bound) ──┬──> P2 (HDFM)
                           ├──> P4 (Thermodynamic Economics)
                           ├──> P1 (D-Score)
                           ├──> P5 (SLSPT — shadow-price tower)
                           └──> P9 (AI Safety) [EXPLORATORY — quarantined v9.1.0, not built]
```

P0 is the root. All downstream modules share its definitions (ENNReal, Landauer, mutual information). P2 and P4 are independent of each other.

---

## Axiom Audit

All compiled modules depend only on:
- `propext` — propositional extensionality
- `Classical.choice` — axiom of choice
- `Quot.sound` — quotient soundness

**Enforcement.** This allowlist is no longer a claim in prose — it is enforced.
`AxiomAudit.lean` and `P0AxiomAudit.lean` walk the relevant environments and
fail on any axiom outside the three above or on `sorryAx`. Protected `main`
requires four GitHub Actions checks: `verify`, `lean-build-current`,
`lean-build-p0`, and `verify-catalog`. The checks cover spine hygiene,
non-vacuity, both current and historical Lean builds, both axiom audits, and the
deterministic public catalog. See `.github/workflows/ci.yml` and
`.github/workflows/research-portal.yml`.

No sorry, no native_decide on nontrivial terms, no escape hatches.

---

## Workflow: Adding New Aristotle Outputs

1. Preserve the exact Aristotle output and project identifier.
2. Reconcile the paper to the final proof and separate formal, numeric, assumed,
   and empirical claims.
3. Route the result through the five-gate Spine Admission Test; the default
   destination is a thematic series or standalone record.
4. Open a pull request containing the Lean source, Aristotle summary, DOI map,
   series index, and regenerated catalog.
5. Merge only after the protected checks pass. Zenodo publication remains a
   separate explicit human decision and must close in the same release receipt.

---

## Stack Complete

All five modules compile with zero sorry. The full Viridis theorem stack covers:

**Physics (Landauer) → Information Theory (Shannon, KL) → Intelligence Bound (P0) → D-Score (P1) → HDFM Graph Optimality (P2) → Thermodynamic Economics (P4)**  
_(AI-safety module P9 is EXPLORATORY — quarantined v9.1.0, not in the verified stack.)_

P9 note (corrected v9.1.0): `ai_conservation_alignment` is **vacuous** — it is proved with the existential witness T₀ = ⊤, so the hypothesis `T > T₀` can never hold and the ∀ is empty. This is not an "edge case"; the theorem establishes nothing. Two further P9 results are also weaker than their names: `deception_power_cost` proves only `0 < ΔI·kBT_ln2` (no deceptive-power term), and `complete_alignment_framework` proves only `a ≤ b`. P9 is therefore **quarantined as EXPLORATORY** pending a non-vacuous reconstruction. The substantive long-horizon conservation result is P0 `conditional_conservation` (NNReal, non-vacuous). See CLAIMS_MATRIX.md → P9.

---

## Cross-References

- **Formal Invariant Structure:** `Viridis_Formal_Invariant_Structure_v1.0.docx` (workspace root)
- **Zenodo DOI:** 10.5281/zenodo.19317983 (P0 formalization)
- **Historical submission record:** NJP-119954 (current venue status is not inferred here)
- **Obsidian Log:** Inbox/Intelligence Bound/2026-04-05_Viridis-Formal-Invariant-Structure-v10-Day-One.md
