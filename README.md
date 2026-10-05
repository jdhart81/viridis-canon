# Viridis Canon — research sources and coverage

[![CI](https://github.com/jdhart81/viridis-canon/actions/workflows/ci.yml/badge.svg)](https://github.com/jdhart81/viridis-canon/actions/workflows/ci.yml) [![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/jdhart81/viridis-canon/badge)](https://scorecard.dev/viewer/?uri=github.com/jdhart81/viridis-canon)

**Public Lean sources, historical build records, and a coverage index for Viridis research.**

**UNCERTIFIED — the 215 legacy source records in the public catalog are not
admitted as Comparator-certified claims.** Historical compilation, an Aristotle
identifier, a zero-sorry count, and membership in `SPINE_MANIFEST.txt` do not
establish current certification. The Viridis Comparator remains the sole
verifier of record. A certified public scope requires its exact candidate,
statement, certificate, reviewed claim map, and manuscript publication binding.

Certification means **logical validity given the model, not empirical validation of its assumptions**.
Physical premises and empirical identifications remain explicit assumptions.
Read [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md) and
[`THEOREM_STATUS_TAXONOMY.md`](./THEOREM_STATUS_TAXONOMY.md) for historical claim
classifications. Integrity Release **v9.1.0** (2026-06-21) quarantined P9 and
de-escalated several overstated claims; see
[`CHANGELOG_v9.1.0.md`](./CHANGELOG_v9.1.0.md).

## Current coverage and scoped publications

The [public catalog](https://jdhart81.github.io/viridis-canon/data/catalog.json)
lists, at this 2026-10-05 labeling review, **215 legacy source records, 0
verified source records, and 0 admitted spine records**. These source counts are separate from published
release pointers and the nightly paper-run denominator. Current status comes
from `corpus_ledger.json` and the existing certificate, claim, and publication
binding consumers. A copied status or successful CI build cannot clear a HOLD.

Two publications have completed their own strict public readbacks:

- [Foundation scoped release — 10.5281/zenodo.23141592](https://doi.org/10.5281/zenodo.23141592).
- [BCAN corrected scalar scope — 10.5281/zenodo.23141980](https://doi.org/10.5281/zenodo.23141980).

These links identify the exact published releases. Their certification applies
only to their reviewed bound claims and named premises. It does not promote the
older P0, BCAN, or other repository sources, establish a broader matrix claim,
or certify the whole historical Canon collection. The
prepared [scoped-publications section](https://jdhart81.github.io/viridis-canon/#scoped-publications)
will show the receipt-bound claim scopes after the publication joins and catalog
deployment complete. See the [coverage-gate documentation](./00_lab_infrastructure/gates/README.md)
for the evidence and admission requirements. Publication joins and enforcement
remain pending the current production readback HOLD.

## Start here

Viridis is an independent research program studying conditional mathematical
connections among information, thermodynamics, learning, and living systems.
The repository is the reproducible source, not a claim that every model
assumption has been established in nature.

- **Inspect the exact claims:** [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md)
- **Reproduce current and historical builds:** [`REPRODUCE.md`](./REPRODUCE.md)
- **Find the historical collection concept:** [10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982)
- **Report a reproduction, critique, citation, or field test:** [external-validation issue](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml)
- **Understand AI use and human responsibility:** [`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md)
- **See the current validation boundary:** [`EXTERNAL_VALIDATION.md`](./EXTERNAL_VALIDATION.md)

## Weekly research release — 2026-08-08

The historical 2026-08-08 release added five research packages to the existing
module layout. Its compilation and review records are retained as provenance;
they do not supply current hash-bound certification for the deposited claims:

- **[Carbon Continuity After Wildfire](https://doi.org/10.5281/zenodo.21855690)** — weekly public feature and Natural Carbon research-pillar release.
- **[Robustness Before Performance v1](https://doi.org/10.5281/zenodo.21855705)** — Viridis Security Core Research Flagship v1.
- **[The Ecopoietic Hedge](https://doi.org/10.5281/zenodo.21855726)** — Restoration Reliability and Symbiosis working corpus.
- **[The D-Score Snapshot Alignment Theorem](https://doi.org/10.5281/zenodo.21855724)** — Biodiversity Measurement Assurance working corpus.
- **[The Scheduler Free-Energy Certificate](https://doi.org/10.5281/zenodo.21855731)** — Research Operations method; its policy proposal remains explicitly unadopted.

The archived package inventory, including papers, Lean sources, environment
pins, numerical checks, review records, provenance, licensing, and checksums, is
under [`releases/2026-08-08/`](./releases/2026-08-08/). The historical collection
version is v10.2.0; a version number does not establish certification.

## Viridis research portal

This repository now includes **Viridis Canon Core**, a standard-library Python
package that converts the checked-in research artifacts into a deterministic,
machine-readable catalog. The accompanying GitHub Pages explorer makes the
historical module layout, selected flagships, working corpus, quarantine state, caveats,
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

Coverage labeling updated: 2026-10-05. The historical 2026-08-08 release and
v10.2.0 module layout are retained below for navigation.
Lean toolchain: leanprover/lean4:v4.28.0
API: https://aristotle.harmonic.fun

---

## Historical module inventory

The table preserves earlier reported compilation and sorry counts as archive
metadata. Every legacy source below remains UNCERTIFIED for public claims; P9
is additionally quarantined. Manuscript names and mathematical declaration
counts are navigation, not a certificate or proof of physical assumptions.

| Module | File | Historical sorry count | Historical build record | Current claim status | Research topic / historical target |
|--------|------|------------------------|-------------------------|----------------------|------------------------------------|
| **P0** | `P0_IntelligenceBound_COMPILED.lean` | **0** | COMPILED under its pinned Lean 4.24 / Mathlib environment and checked by required CI | UNCERTIFIED | Intelligence Bound flagship; external-validation status is tracked separately |
| **P1** | `P1_DScore.lean` | **0** | COMPILED | UNCERTIFIED | Physical Review E (draft) |
| **P2** | `P2_HDFM_POC.lean` | **0** | COMPILED | UNCERTIFIED | HDFM resubmission |
| **P3** | `P3_Impossibility.lean` | **0** | COMPILED | UNCERTIFIED | 2nd canon paper (Goodhart impossibility / alignment-as-feasibility) |
| **P4** | `P4_ThermodynamicEconomics.lean` | **0** | COMPILED | UNCERTIFIED | Nature Sustainability |
| **P5** | `P5_SLSPT/` (5 files: IntelligenceBound, InverseSquare, ShadowPrice, ShadowPriceLevelCurves, SLSPTTowerOrdering) | **0** | COMPILED | UNCERTIFIED | Speed Limit Shadow Price Tower (24 thms; promoted from Zenodo v3 deposit 10.5281/zenodo.20006414) |
| **P7** | `P7_PlasmaNFix/` (3 files: Foundations, Energy, Integration) | **0** | COMPILED | UNCERTIFIED | Plasma-mediated N₂ fixation for forest C-sequestration (16 thms — Hart 2026; Nature Energy track) |
| ~~P9~~ | `P9_AI_Safety.lean` | 0 | ⚠ **EXPLORATORY — QUARANTINED v9.1.0** — vacuous `ai_conservation_alignment` (T₀=⊤); excluded from `defaultTargets` and public admission (see CLAIMS_MATRIX.md) | QUARANTINED | AI Safety (non-vacuous reconstruction queued) |
| **PSIT** | `PSIT_Symplectic.lean` | **0** | COMPILED | UNCERTIFIED | Symplectic-conjugation theorem — Nature Physics (Hart 2026, Run-035; 8 thms) |
| **BMD** | `BoundedMemoryDissipation.lean` | **0** | COMPILED (Aristotle `6483ae65`, 2026-06-21) | UNCERTIFIED | **v9.1.0 INV-4 fix** — honest bounded-memory dissipation floor (`hmem` load-bearing); replaces P0's dead-`h_mem` `finite_memory_dissipation` (→ `landauer_dissipation_bound`) |
| **EcoChain** | `EcoChain_DendriticCorridor.lean` | **0** | COMPILED | UNCERTIFIED | Dendritic corridor formation — *Methods in Ecology & Evolution* (4 thms + 3 lemmas; Aristotle c23eab22, 2026-05-30) |
| **Book** | `Book_HeatAndDisorder.lean` | **0** | COMPILED | UNCERTIFIED | Model collection for *Heat and Disorder* book — 12 thms. Foundation (7): entropy monotonicity, feedback dichotomy, saddle-node tipping threshold, energy-balance uniqueness. Conditional model layer (5): strict Clausius production + gap-monotonicity, Planck climate sensitivity (Stefan–Boltzmann), **Intelligence-Bound restoration speed limit** (dI/dt ≤ P/(k_B T ln2)) + time lower bound. Aristotle a9312b60, 2026-05-31 |
| **MRAB** | `MRAB.lean` | **0** | COMPILED — **IB core-extension, included in the historical v10 layout** | UNCERTIFIED | Multi-Ring Alignment Bound (Thm 1; the Polymath Paradox + wu-wei saturation + UAIB reduction). 10 thms; Aristotle `65347d17`, 2026-06-21. Published standalone on Zenodo 2026-06-22; queued for a future curated v10 release (historical layout frozen at v9). |
| **SIB** | `SymbioticIntelligenceBound.lean` | **0** | COMPILED — **IB core-extension, included in the historical v10 layout** | UNCERTIFIED | Symbiotic Intelligence Bound (two-body generalization of the IB; Good-Regulator rate law). 5 thms; Aristotle `a0660ac8`. Standalone DOI 10.5281/zenodo.20764638; included in the historical v10 layout. |
| **UWMT** | `UniversalWaterfilling.lean` | **0** | COMPILED — **historical layout v10.1.0 ("the Keystone")** | UNCERTIFIED | Universal Water-Filling Meta-Theorem — unifies the 9-member shadow-price/water-filling family into one variational object (curvature + temperature control knobs; lambda = water level = shadow price = free energy). 8 thms; Aristotle `da92404c`, Run-084. |
| **GST** | `GeodesicSaturation.lean` | **0** | COMPILED — **historical layout v10.1.0 ("the Sage")** | UNCERTIFIED | Geodesic Saturation Theorem — the IB's own equality/saturation condition: dI/dt=(P-F)c, saturates iff F=0 (constant-speed Fisher-Rao geodesic). 6 thms; Aristotle `f864600a`, Run-086. |
| **EET** | `EffortlessEquilibrium.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Steersman")** | UNCERTIFIED | Effortless Equilibrium Theorem — wu-wei rest states exist, rest iff grad(Phi)=0, and holding power P_hold=gamma^-1\|\|grad(Phi)\|\|^2 is minimized (zero) exactly at rest; harmonization is strictly cheaper than forcing. 11 thms; Aristotle `65ae007a`, Run-097. |
| **PCT** | `PerennialCorridor.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Gardener")** | UNCERTIFIED | Perennial Corridor Theorem — Whittle-index corridor urgency ranking, band-convexity of the unimodal superlevel set, stewardship-dividend nonnegativity, and the IB floor on maintenance holding power. 15 thms; Run-098. |
| **DST** | `DecoherentSelection.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Chooser")** | UNCERTIFIED | Decoherent Selection Theorem — decision cost vanishes iff the pointer-basis eigenstate is selected, is bounded by ln N, and the einselected basis is the unique zero-waste choice; IB throughput speed limit on collapse. 12 thms; Run-099. |
| **MAT** | `MutualisticAttestation.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Attester")** | UNCERTIFIED | Mutualistic Attestation Theorem — attestation cost = kBT·ln2·(residual entropy); certification feedback has fold bistability (trap/mutualism stable states); optimal confidence is interior. 19 thms; Run-100 (100th nightly-run milestone). |
| **TAT** | `ThermodynamicAttention.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Attuner")** | UNCERTIFIED | Thermodynamic Attention Theorem — the rational-inattention shadow price equals the Landauer quantum kBT; attention water-fills the einselected slow basis per KKT; Inattention Trap below a resolvability threshold C_crit. 12 thms; Run-101. |
| **SST** | `StewardshipSetpoint.lean` | **0** | COMPILED — **historical layout v10.2.0 ("the Steward")** | UNCERTIFIED | Stewardship Setpoint Theorem — golden-rule sustainable ceiling for a living renewable stock (dD/dt=g(D)-phi*H); Tragedy collapse for phi*Omega>rho; act-budget twin of TAT. 13 thms; Run-102. |

The protected `main` branch requires the repository hygiene check, the current
Lean build and axiom audit, the pinned historical P0 build and audit, and the
deterministic catalog check. P9 remains **EXPLORATORY — quarantined** and is not
included in the current default compilation targets or admitted as a certified source.

### Historical bridge modules

| Module | File | Historical sorry count | Historical build record | Current claim status | Historical headline |
|--------|------|------------------------|-------------------------|----------------------|------------------------------------|
| **B1** | `Bridge_MissionFeasibility.lean` | **0** | COMPILED | UNCERTIFIED | `Feasible e m ↔ target_rate ≤ P_max / (k_B T ln 2)` — a **self-contained mission-feasibility analogue** motivated by P0/P1/P3/P4 (imports only Mathlib; the rate ceiling and D-range are built into its local predicates — see CLAIMS_MATRIX.md). Aristotle 054d616c. |

---

## Directory Structure

```
Aristotle-Pipeline/
├── P0_IntelligenceBound_COMPILED.lean   # Historical P0 model source
├── P1_DScore.lean                        # D-Score biodiversity metric
├── P2_HDFM_POC.lean                      # HDFM graph models
├── P3_Impossibility.lean                 # Conditional feasibility model
├── P4_ThermodynamicEconomics.lean        # Thermodynamic economics models
├── P7_PlasmaNFix/                        # Plasma N₂ fixation models
├── P9_AI_Safety.lean                     # Quarantined; excluded from defaultTargets
├── lakefile.toml                         # Current compilation targets
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

## Historical dependency sketch

```
P0 (Intelligence Bound) ──┬──> P2 (HDFM)
                           ├──> P4 (Thermodynamic Economics)
                           ├──> P1 (D-Score)
                           ├──> P5 (SLSPT — shadow-price tower)
                           └──> P9 (AI Safety) [EXPLORATORY — quarantined v9.1.0, not built]
```

This is a historical conceptual sketch. Consult each file's imports for actual
Lean dependencies. Shared definitions, matching names, and this diagram do not
establish physical premises or bind a published claim to a certified statement.

---

## Build audits and Comparator certification

The permitted certificate axiom set is exactly:

- `propext` — propositional extensionality
- `Classical.choice` — axiom of choice
- `Quot.sound` — quotient soundness

`AxiomAudit.lean` and `P0AxiomAudit.lean` inspect their declared build
environments and fail on an axiom outside this set or on `sorryAx`. GitHub
Actions runs `verify`, `lean-build-current`, `lean-build-p0`, `deposit-verify`,
and `verify-catalog`, as defined in [the build workflow](./.github/workflows/ci.yml)
and [the catalog workflow](./.github/workflows/research-portal.yml). Required
checks must pass before merge. Their compilation, hygiene, and catalog results
are build evidence; they neither issue Comparator certificates nor establish
that every repository claim has a non-vacuity witness.

Comparator certification uses the pinned Lean 4.28.0 / Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365` environment. Historical P0
reproduction keeps its separately declared Lean 4.24 environment. Reproduction
instructions remain in [`REPRODUCE.md`](./REPRODUCE.md). A missing or invalid
certificate, unsupported axiom, trivial bound claim, failed witness, drift, or
missing manuscript binding leaves the public claim UNCERTIFIED or HOLD.

---

## Workflow: Adding New Aristotle Outputs

1. Preserve the exact Aristotle output and project identifier.
2. Reconcile the paper to the final proof and separate formal, numeric, assumed,
   and empirical claims.
3. Preserve the historical admission review, and apply the current static,
   trivial-theorem, premise, witness, and claim-binding gates. Obtain an exact
   hash-bound certificate through the approved Comparator pipeline; a build or
   Aristotle response cannot substitute for it. Complete the reviewed
   `PUBLICATION_BINDING` before publication.
4. Open a pull request containing the Lean source, Aristotle summary, DOI map,
   series index, and regenerated catalog.
5. Merge only after the protected checks pass. Zenodo publication remains a
   separate explicit human decision and must close in the same release receipt.

---

## Historical research scope and quarantine

The historical research program connects these model families:

**Landauer premises → information-theoretic models → Intelligence Bound models
(P0) → D-Score models (P1) → HDFM graph models (P2) → thermodynamic economics
models (P4).**

This is a research outline, not a certificate for the chain or a derivation of
physical assumptions. P9 remains EXPLORATORY and quarantined.

P9 note (corrected v9.1.0): `ai_conservation_alignment` is **vacuous** — it is proved with the existential witness T₀ = ⊤, so the hypothesis `T > T₀` can never hold and the ∀ is empty. This is not an "edge case"; the theorem establishes nothing. Two further P9 results are also weaker than their names: `deception_power_cost` proves only `0 < ΔI·kBT_ln2` (no deceptive-power term), and `complete_alignment_framework` proves only `a ≤ b`. P9 is therefore **quarantined as EXPLORATORY** pending a non-vacuous reconstruction. The historical discussion points to P0 `conditional_conservation` (NNReal). That reference does not certify its public conservation claims; current certificate, premise, witness, and claim-binding evidence is still required. See CLAIMS_MATRIX.md → P9.

---

## Cross-References

- **Formal Invariant Structure:** `Viridis_Formal_Invariant_Structure_v1.0.docx` (workspace root)
- **Zenodo DOI:** 10.5281/zenodo.19317983 (P0 formalization)
- **Historical submission record:** NJP-119954 (current venue status is not inferred here)
- **Obsidian Log:** Inbox/Intelligence Bound/2026-04-05_Viridis-Formal-Invariant-Structure-v10-Day-One.md
