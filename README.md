# Viridis Canon — the machine-verified Intelligence Bound

[![CI](https://github.com/jdhart81/viridis-canon/actions/workflows/ci.yml/badge.svg)](https://github.com/jdhart81/viridis-canon/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19317982.svg)](https://doi.org/10.5281/zenodo.19317982)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Lean 4](https://img.shields.io/badge/Lean-4-blue.svg)](https://leanprover.github.io/)

A **Lean 4** formalization of the **Intelligence Bound** and the theory built on it — every theorem machine-checked, zero `sorry`, with a clean axiom audit. This is the load-bearing **spine** of the Viridis research canon: the minimal set of compiled theorems someone must accept to accept the whole edifice.

> **The Intelligence Bound:** an agent's rate of heritable information acquisition is bounded by the physical power it commands — `İ(τ) ≤ min(ρB, P / (k_B T ln 2))`. The live footing is the **erasure side** (a biosphere-erasure floor + a stewardship-intelligence lower bound); the acquisition-rate framing was refuted (Wolpert 2026) and is not asserted.

## The verification guarantee

Every module in this repository:
- builds under a pinned Lean 4 toolchain (`lean-toolchain`) against [Mathlib](https://github.com/leanprover-community/mathlib4);
- contains **zero `sorry`** / `admit`;
- has each named theorem's axiom dependency **audited to `⊆ {propext, Classical.choice, Quot.sound}`** (the standard classical-logic base — no extra axioms smuggled in);
- carries **non-vacuous** statements (the hypotheses are load-bearing in the proofs).

Theorems are verified with [Aristotle (Harmonic)](https://harmonic.fun/) and re-checked in CI on every push. Verification certifies the **validity of the reasoning**, not empirical magnitudes.

## Build

```bash
# Lean 4 via elan (toolchain is pinned in lean-toolchain)
lake exe cache get      # fetch Mathlib build cache
lake build              # builds all spine modules
```

## The spine (this repo)

All 23 modules are released together under the spine concept DOI **[10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982)** (always resolves to the latest version; frozen head **v9.0.1**).

| Module | Pillar / role |
|---|---|
| `P0_IntelligenceBound_COMPILED` | **P0** — the core bound |
| `BiosphereErasureBound`, `BoundedMemoryLearning` | P0 — recovered **erasure-side** footing (post-Wolpert) |
| `P1_DScore` | **P1** — disorder/biodiversity score |
| `P2_HDFM_POC` | **P2** — high-definition forest management |
| `P3_Impossibility` | **P3** — Goodhart / alignment-as-feasibility impossibility |
| `P4_ThermodynamicEconomics` | **P4** — thermodynamic economics (D-Capital) |
| `P5_SLSPT_*` (×5) | **P5** — shadow-price / inverse-square / tower-ordering suite |
| `P7_PlasmaNFix_*` (×3) | **P7** — plasma-mediated N₂ fixation |
| `P9_AI_Safety` | **P9** — AI-safety formalization |
| `Bridge_MissionFeasibility` | bridge — mission feasibility |
| `Bridge_BiosphereProductivity` | bridge — IB ⇄ biosphere-productivity duality |
| `Bridge_EcoChainInstrument` | bridge — EcoChain instrument |
| `EcoChain_DendriticCorridor` | corridors — dendritic connectivity |
| `ConservationOperator` | asymmetric-reward conservation operator |
| `PSIT_Symplectic` | symplectic integrator theory |
| `Book_HeatAndDisorder` | "Heat and Disorder" verified appendix |

## The extended canon (thematic series & standalone records)

The spine is a curated, milestone-only release line. Everything else routes to **thematic series** (own DOI, `isDerivedFrom` the spine) or standalone branch records. Live series:

| Series | Theme | Concept DOI |
|---|---|---|
| S1 | D-Capital Valuation | [10.5281/zenodo.20705178](https://doi.org/10.5281/zenodo.20705178) |
| S2 | Monitoring — the Surveyor | [10.5281/zenodo.20704852](https://doi.org/10.5281/zenodo.20704852) |
| S3 | Gaian Thermodynamics | [10.5281/zenodo.20777225](https://doi.org/10.5281/zenodo.20777225) |
| S4 | Stewardship & Governance — ViridisOS | [10.5281/zenodo.20705182](https://doi.org/10.5281/zenodo.20705182) |
| S5 | Corridors & Spatial | [10.5281/zenodo.20777068](https://doi.org/10.5281/zenodo.20777068) |

Browse the full corpus in the [**viridis-canon** Zenodo community](https://zenodo.org/communities/viridis-canon).

## Citation

```bibtex
@software{viridis_canon,
  author  = {Hart, Justin D. and {Aristotle (Harmonic)}},
  title   = {Viridis Canon: a machine-verified Intelligence Bound},
  doi     = {10.5281/zenodo.19317982},
  url     = {https://doi.org/10.5281/zenodo.19317982},
  note    = {Concept DOI — always resolves to the latest version}
}
```

See [`CITATION.cff`](./CITATION.cff).

## Relationship to Mathlib

This package **depends on** Mathlib; it is not part of it. General, reusable lemmas discovered while building the canon are **upstreamed to Mathlib as targeted PRs** (the canon keeps the application-specific theorems; Mathlib gets the domain-agnostic pieces). See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## License

Lean sources and code: **Apache-2.0** ([`LICENSE`](./LICENSE)). Accompanying papers and documentation in the Zenodo records: **CC-BY-4.0**.

---

*Viridis LLC · Columbia Falls, Montana, USA · ORCID [0009-0008-3082-2482](https://orcid.org/0009-0008-3082-2482)*
