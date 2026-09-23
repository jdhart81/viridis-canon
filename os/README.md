# Viridis OS — the canon compiled into callable functions (WS-20)

**The repository is the research, the bundle is the OS, the site is its interface.**

Every result in this repository is available to the product at three tiers, all
generated from files in this repository:

| Tier | What it means | Where it comes from |
|---|---|---|
| `reference` | Searchable, linked, citable. | Every record in `docs/data/catalog.json` (203 at v10.2.0). |
| `callable` | Runs in the workspace, the Viridis Guide and the MCP/agent API as an **unsigned preview** with a receipt. | A valid `function.json` + runner beside the Lean source. |
| `admitted` | May appear in a reviewed analysis. | A human-authored entry in `os/admissions.json` (CODEOWNERS: @jdhart81). The compiler reads it and never writes it. |

## Layout

```
function.json + runner.py      beside the Lean in a package dir (series/SBB/, P5_SLSPT/, …)
os/functions/<id>/function.json for single-file records and results without a package dir
os/lib/viridis_fn.py            runner runtime: JavaScript-number semantics (fdlibm ports of V8 12.4
                                exp/expm1/log/cosh/pow, toFixed, toLocaleString), the product's input
                                validator, and the checkable-condition grammar
os/lib/theorem_runner.py        generic runner for theorem functions
os/lib/run.py                   bundle dispatcher (stdin JSON → result; --self-test)
os/core.json                    operating tree, held proposals, service boundaries, kernel order (human)
os/families.json                the four decision families and their membership (human)
os/research_intake.json         engine research-intake records carried from the app
os/admissions.json              the admission ledger (human only)
os/parity/                      the product's own outputs at viridis-conservation-app@398b177 (I2)
os/migrations/                  the one-time WS-20 extraction script (provenance)
docs/schemas/function-v1.json   manifest schema
```

## Build

```
python3 -m canon_core validate-functions          # every manifest, strict
python3 -m canon_core build-os --out os-bundle    # examples, parity replay, bundle, self-test
python3 -m canon_core verify-os os-bundle --expect-digest <sha256>
```

The bundle is `functions.json`, `reference.json`, `runners/`, `run.py`,
`SHA256SUMS` and `DIGEST` (= SHA-256 of `SHA256SUMS`). The `viridis-os-bundle`
workflow builds it on every push and attaches `os-bundle-<tag>.tar.gz` plus the
digest to each release tag. The product vendors a bundle and pins its digest.

## Invariants

- **I1 Single source.** Function definitions, examples, units, summaries and
  boundaries live here. The product loads the bundle and nothing else.
- **I2 Parity.** The 17 runners reproduce the product's TypeScript runners
  bit-for-bit: 187,051 fuzz and published cases (outputs *and* error messages)
  with zero mismatches before retirement; 1,717 of them are replayed on every
  build from `os/parity/`. The five `/research/recompute` hashes are untouched.
- **I3 No automatic authority.** `admitted` requires the ledger; the compiler
  cannot promote and writes nothing in the repository (tested). Mutualist stays
  `BLOCKED` with no runner.
- **I4 Honest labels.** Every function carries its Lean module, sources + hashes,
  theorem names, DOI, tier and `empirical_validation: NOT_VALIDATED`.
- **I5 Determinism.** Same commit ⇒ same `DIGEST` (tested; CI rebuilds twice).
- **I6 Engine unlimited.** Engine-authored manifests are additive. A defective
  one never blocks a build: it is recorded under `rejected_functions` in the
  bundle and its record stays in the reference tier.

## Status at WS-20 (v10.2.0 catalog)

- 18 decision kernels migrated from the app: **9 admitted** (restoration,
  afforestation, harmonization, carbon-continuity, shadow-price-capacity,
  multi-ring-alignment-capacity, symbiotic-surplus, decision-information-capacity,
  thermodynamic-economic-allocation), **7 callable with an open canon
  classification reconciliation** (shared-channel-coverage, invariance-capacity,
  precautionary-capacity, reciprocity-corridor, anytime-change,
  seed-source-bottleneck, switching-hysteresis), **tempo callable with an open
  canon record reconciliation** (its StewardshipTempo Lean source is not in this
  repository), **mutualist reference + BLOCKED**.
- **14 theorem functions** promoted to `callable` from the 18 verified spine
  records not already bound to a kernel (see below). Each is property-tested:
  over thousands of hypothesis-satisfying samples the conclusion check never
  fails, and a flipped-conclusion negative control is caught.

### Verified records promoted to callable theorem functions

| Function | Record | Theorem |
|---|---|---|
| biosphere-erasure-floor | BiosphereErasureBound.lean | `biosphere_erasure_floor` |
| bounded-memory-erasure-floor | BoundedMemoryLearning.lean | `erasure_dissipation_floor` |
| mission-feasibility-corrigibility | P3_Impossibility.lean | `corrigibility_under_IB` |
| decoherent-selection-ambiguity-cost | DecoherentSelection.lean | `ambiguity_cost_le_lnN` |
| effortless-equilibrium-forcing-time | EffortlessEquilibrium.lean | `steersman_ib_floors_forcing_time` |
| geodesic-saturation-forcing-decomposition | GeodesicSaturation.lean | `forcing_decomposition_nonneg` |
| plasma-nfix-information-rate | P7_PlasmaNFix/Integration.lean | `theorem10_info_bound_structure` |
| mutualistic-attestation-throughput | MutualisticAttestation.lean | `attester_ib_throughput_speed_limit` |
| hdfm-strahler-corridor-width | P2_HDFM_POC.lean | `strahler_monotone_width` |
| perennial-corridor-holding-power | PerennialCorridor.lean | `holding_power_mono_in_decay` |
| stewardship-setpoint-direction | StewardshipSetpoint.lean | `orar_extremum_seeking_converges_to_Dstar` |
| thermodynamic-attention-waterfill | ThermodynamicAttention.lean | `slow_modes_filled_first` |
| thermodynamic-economics-production-bound | P4_ThermodynamicEconomics.lean | `thermodynamic_production_bound` |
| universal-waterfilling-optimum | UniversalWaterfilling.lean | `uwmt_concave_optimum_is_waterfilling` |

These spine records have no standalone deposit DOI; their manifests cite the
canon concept DOI (10.5281/zenodo.19317982) and say so in `provenance.doi_scope`.

### Verified records not promoted, and why

| Record | Why not (v1 grammar) |
|---|---|
| P1_DScore.lean | Statements are about entropy and mutual information of random variables under a probability measure. A finite-pmf specialisation is sound but needs a dedicated runner that reproduces Mathlib's measure-theoretic definitions; not a condition over supplied values. |
| P7_PlasmaNFix/Energy.lean | Closed numerical facts about fixed design constants (no free variables). Citable, nothing to call. |
| P7_PlasmaNFix/Foundations.lean | Constants and one definitional identity; nothing to check beyond the definition. |
| PSIT_Symplectic.lean | Structural statements about a fixed symplectic form, matrix congruence (∃ M …) and Hamiltonian flows; existential and matrix-level conclusions are not checks on supplied values. |

The 8 remaining verified records are already bound to decision kernels
(P5_SLSPT ×5 → shadow-price-capacity, MRAB, SymbioticIntelligenceBound,
P0_IntelligenceBound_COMPILED). The 176 `working` and 1 `quarantined` records
stay in the reference tier until an author (or the engine's package template)
writes a manifest; `tools/scaffold_function.py` fills the mechanical fields.
