# The D-Score Snapshot Alignment Theorem - reproducible release object

This package is the Run-118 release under `VRS-SUBMIT-INVARIANT-1`.

## Reproduce the numerical checks

```bash
python3 code/verification.py
```

Expected summary: `21 PASS / 0 FAIL` and `NUMERICAL_GATE_PASS`.
These are analytic and synthetic model checks, not empirical biodiversity
validation.

## Reproduce the Lean proof

```bash
cd lean
lake build SnapshotAlignment
lake env lean AxiomAudit.lean
```

The toolchain is Lean `v4.28.0`; Mathlib and all transitive dependencies are
pinned by `lake-manifest.json`.

## Scope

The six Lean theorems verify the exact common-mode alignment identity,
unit-interval result, delay-variance bound, sufficient band budget, and two
controls stated in the paper. They do not prove that real biodiversity
channels share the modeled signal, that delays are known, that the sufficient
budget is necessary, or that any monitoring program is empirically valid.

The paper enters the standalone Viridis working research corpus. It is not an
Intelligence Bound spine addition.

Justin D. Hart is the accountable human author. Aristotle and Codex are
disclosed research/proof tools and are not authors.
