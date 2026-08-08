# Fresh release verification

Verified at: `2026-08-08T22:47:52Z`

- Numerical gate: `22 PASS / 0 FAIL`; fresh portable execution exactly matches
  the sealed captured output.
- Lean build: `Build completed successfully (1895 jobs).`
- Zero-sorry/escape scan: no occurrences of `sorry`, `admit`, `axiom`, or
  `unsafe` in `SchedulerFreeEnergy.lean` or `AxiomAudit.lean`.
- Axiom audit: only `propext`, `Classical.choice`, and `Quot.sound`.
- PDF review: all four pages rendered and visually passed.

The numerical verifier's final interpretation correctly says that its finite
checks are not formal proof. Formal support is supplied separately by the
pinned, audited Lean artifact.
