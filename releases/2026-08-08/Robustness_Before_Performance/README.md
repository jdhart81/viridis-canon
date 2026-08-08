# Robustness Before Performance v1 - reproducible release object

This is the formally reconciled research release under
`VRS-SUBMIT-INVARIANT-1`.

## Reproduce the reference implementation checks

From `code/` with Python 3.11 or newer and the declared `jsonschema`
dependency installed:

```bash
python3 -m pytest tests/test_engine.py
```

Expected result: `35 passed`. The included examples are synthetic decision
fixtures, not empirical evidence or authorized recommendations.

## Reproduce the Lean proof and review checks

```bash
cd lean
lake build
lake env lean AxiomAudit.lean
lake env lean ReviewChecksAxiomAudit.lean
```

The toolchain is Lean `v4.28.0`; Mathlib and transitive dependencies are pinned
by `lake-manifest.json`. The formal package contains 27 named theorems plus 19
non-degeneracy review checks and has zero unresolved proof holes.

## Scope

The paper defines a governed robustness decision kernel covering dependency
independence, authority separation, epistemic states, lineage recall,
interval classification, robust dominance, trajectory stress, and distinct
release-state witnesses. Formal proof establishes only the declared
mathematical models. It does not establish empirical input truth, threat-model
completeness, authority, deployment benefit, security certification, adoption,
or revenue.

The included production receipt supports a separate historical internal
software/deployment statement; it is not a Lean theorem or scientific outcome.

This paper routes to the standalone Robustness Engineering and Governance
branch. It is not an Intelligence Bound spine addition.
