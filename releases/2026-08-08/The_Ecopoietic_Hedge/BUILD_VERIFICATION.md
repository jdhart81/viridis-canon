# Fresh release-object verification - 2026-08-08

The exact files in this directory were checked after assembly.

## Numerical

Command: `python3 code/verification.py`

Result: `32 PASS / 0 FAIL`; exit code 0. All preregistered failure conditions
were `NOT TRIGGERED`.

## Lean

Command: `lake build EcopoieticHedge` from `lean/`

Result: successful clean dependency fetch and build, `1,903` jobs; exit code 0.
The only diagnostics were unused-variable linter warnings for existing
hypotheses. The release source scan found zero occurrences of `sorry`, `admit`,
added `axiom`, `native_decide`, `implemented_by`, `unsafe`, `extern`, or
`sorryAx`.

The post-Lean review and axiom output remain bound to the byte-identical Lean
source in `provenance/`.

No external publication action occurred.
