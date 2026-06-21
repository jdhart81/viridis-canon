# CHANGELOG — v9.1.1 (Enforcement Release, 2026-06-21)

Narrowly scoped follow-up to v9.1.0, addressing the second external review. v9.1.0
fixed *intellectual honesty*; v9.1.1 fixes *enforcement and integration*.

## The real CI build failure — fixed
The v9.1.0 CI `lean-build` job failed at `lake build` with `expected glob` on every
P5/P7 stanza: the `lean_lib` globs used slash paths (`P5_SLSPT/IntelligenceBound`),
but Lake on the pinned `leanprover/lean4:v4.28.0` expects **dot-separated module
globs** (`P5_SLSPT.IntelligenceBound`). All eight P5/P7 globs corrected. This was
almost certainly the original "CI red at the build step" cause.

## P5 and P7 now under the integrity gates
Previously the hygiene/vacuity gates scanned only root-level `.lean` files and
`AxiomAudit.lean` enumerated only root modules, so the five P5_SLSPT and three
P7_PlasmaNFix default-target modules escaped the audit. Now:
- New canonical **`SPINE_MANIFEST.txt`** — the single source of truth listing every
  verified-spine module (default targets minus quarantined P9).
- `tools/check_spine_hygiene.sh` and the CI vacuity step are **driven by the
  manifest**, so they cover P5/P7 (and anything added later) automatically.
- `AxiomAudit.lean` imports the P5/P7 modules and adds them to its spine list.
- Verified locally: hygiene + vacuity pass on all 23 modules (0 sorry, 0 homemade
  axioms, 0 vacuity).

## CI honesty (claim corrected)
README and the v9.1.0 changelog had said "all checks blocking" while the workflow
sets `continue-on-error: true` on the Lean build. Corrected: **the textual gates
(hygiene, vacuity, integrity-docs presence) are blocking; the full Lean build and
axiom audit are provisional** until validated on GitHub Actions, after which
`continue-on-error` is removed and both jobs required via branch protection.

## Documentation accuracy
- `Bridge_MissionFeasibility` is now described — in both the README table and the
  file docstring — as a **self-contained mission-feasibility analogue motivated by
  P0/P1/P3/P4** (it imports only Mathlib; the rate ceiling and D-range are built into
  its local predicates), not a cross-canon bridge. Real-import rewrite remains queued.
- `CITATION.cff` title → **"Viridis Canon: Lean-Checked Conditional Mathematics for
  the Intelligence Bound"** (was "a machine-verified Intelligence Bound").
- `THEOREM_STATUS_TAXONOMY.md` now uses **two fields — Formal status × Interpretive
  status** — so a result can be Derived mathematically yet Empirical-hypothesis
  interpretively.

## Still queued (proof-content, separate forge passes)
- P4 precise names as deprecated aliases: `boundary_essentiality_D`,
  `finite_planetary_rate_ceiling`, `undiscounted_constant_flow_diverges`.
- `Bridge_MissionFeasibility` real `import` of the pillar modules.
- P9 non-vacuous reconstruction.
- Validate `AxiomAudit.lean` on the pinned toolchain, then drop `continue-on-error`
  and require both CI jobs on `main`.
