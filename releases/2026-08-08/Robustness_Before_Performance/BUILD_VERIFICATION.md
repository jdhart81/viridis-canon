# Fresh release verification

Verified at: `2026-08-08T22:26:17Z`

- Python reference suite: `35 passed` under Python 3.14.3 and pytest 9.1.1.
- Lean build: `Build completed successfully (922 jobs).`
- Zero-sorry/escape scan: no occurrences of `sorry`, `admit`, `axiom`, or
  `unsafe` in the kernel, review checks, or audit files.
- Axiom audits: only `propext`, `Classical.choice`, and `Quot.sound`; several
  concrete witness checks require no axioms.

The fresh job count reflects the release package's two declared library
targets. The sealed provider receipt is retained separately and reports its
original 930-job audit with 19 review checks.

