# Aristotle-Pipeline — Viridis Formal Canon

**The canonical compiled Lean 4 artifacts underlying all Viridis science, methods, and publications.**

> **What "verified" means here.** These modules are **Lean-checked conditional mathematics**: each theorem's *type* is machine-verified, but a Lean-checked theorem is not automatically a verified statement about physics, economics, or ecology. Every headline result is graded by formal strength in [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md) using the labels in [`THEOREM_STATUS_TAXONOMY.md`](./THEOREM_STATUS_TAXONOMY.md). Read the matrix before citing any result as established. Integrity Release **v9.1.0** (2026-06-21) quarantined P9 and de-escalated several overstated claims; see [`CHANGELOG_v9.1.0.md`](./CHANGELOG_v9.1.0.md).

Last updated: 2026-05-31 (Book_HeatAndDisorder v2 promoted; 12 theorems verified via Aristotle a9312b60 — "Heat and Disorder" formal spine + first-principles layer incl. the Intelligence-Bound restoration speed limit)
Lean toolchain: leanprover/lean4:v4.28.0
API: https://aristotle.harmonic.fun

---

## Module Status

| Module | File | Sorry | Status | Paper Target |
|--------|------|-------|--------|-------------|
| **P0** | `P0_IntelligenceBound_COMPILED.lean` | **0** | COMPILED | NJP-119954 (submitted 2026-04-05) |
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

**ALL MODULES ZERO SORRY. 8/9 canon + PSIT + EcoChain_DendriticCorridor + Book_HeatAndDisorder (12 thms) compiled. Full stack: physics → information theory → intelligence bound → biodiversity metric → graph optimality → planetary-conservation impossibility → thermodynamic economics → plasma N₂ fixation.** _(The AI-safety module P9 is **EXPLORATORY — quarantined in v9.1.0** and is NOT part of the verified stack.)_

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

**Enforcement (v9.1.0).** This allowlist is no longer a claim in prose — it is enforced. `AxiomAudit.lean` is a build target that walks the environment, collects the axioms of every verified-spine declaration, and **throws (fails `lake build`)** on any axiom outside the three above or on `sorryAx`. CI additionally runs `tools/check_spine_hygiene.sh` (no `sorry`/`admit`/homemade axioms) and `tools/vacuity_lint.py` (no ⊤-witness / `absurd … not_top_lt` vacuity). **CI status (v9.1.1):** the textual integrity gates — `check_spine_hygiene.sh` (no `sorry`/`admit`/homemade axioms), `vacuity_lint.py`, and integrity-docs presence, all driven by `SPINE_MANIFEST.txt` across **every** default-target module incl. P5/P7 — are **BLOCKING** (the `verify` job). The full Lean build + `AxiomAudit` are **PROVISIONAL** (`continue-on-error`) until validated on GitHub Actions, then made blocking. See `.github/workflows/ci.yml`, `CHANGELOG_v9.1.0.md`, `CHANGELOG_v9.1.1.md`.

No sorry, no native_decide on nontrivial terms, no escape hatches.

---

## Workflow: Adding New Aristotle Outputs

1. Justin drops new Aristotle output folders into `new leans/` in the workspace root
2. Claude reviews: diff against current versions, verify zero sorry, check axiom set
3. Archive the old sorry version into `_pre-aristotle-drafts/`
4. Promote the new compiled .lean file into this directory
5. Copy the Aristotle summary into `_pre-aristotle-drafts/` for provenance
6. Update this README's status table
7. Update the Formal Invariant Structure document (v1.0+) if new theorems added

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
- **NJP Submission:** Manuscript ID NJP-119954 (Intelligence Bound paper)
- **Obsidian Log:** Inbox/Intelligence Bound/2026-04-05_Viridis-Formal-Invariant-Structure-v10-Day-One.md
