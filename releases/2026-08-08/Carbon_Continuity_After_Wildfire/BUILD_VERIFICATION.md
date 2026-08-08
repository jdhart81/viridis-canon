# Fresh release-object verification - 2026-08-08

The exact files in this versioned packaging overlay were checked after
assembly.

## Numerical

Command: `python3 code/verification.py`

Result: `20 PASS / 0 FAIL`; exit code 0. The checker read the frozen source
digest from the included provenance binding and did not require any private or
absolute filesystem path.

## Lean

Command: `lake build CarbonContinuity` from `lean/`

Result: successful isolated pinned build, `866` jobs; exit code 0. The only
diagnostics were unused-variable linter warnings for existing hypotheses.

The release source scan found zero occurrences of `sorry`, `admit`, added
`axiom`, `native_decide`, `implemented_by`, `unsafe`, `extern`, or `sorryAx`.
All six theorems depend only on `propext`, `Classical.choice`, and `Quot.sound`.

The paper PDF, paper source, and Lean source are byte-identical to the earlier
scientifically passed candidate. Only the portable provenance/checker layer,
release metadata, and fresh receipts changed.

No external publication action occurred.
