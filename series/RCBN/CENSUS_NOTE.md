# Census note (2026-11-13)

The compile census of 2026-11-13 compiled every Lean file in this folder at the project's declared pins
(Lean 4.28.0, Mathlib `8f9d9cff`).

`CheckpointBalance.lean`, the only Lean file deposited here, closes all six theorems with `sorry`.

`COMPARATOR_SUMMARY.md` reports a zero-sorry certificate from a private verifier, with no local Lean run.
The candidate that verifier checked is not in this repository, so that certificate cannot be reproduced
from here.

`CheckpointBalanceProofs.lean` now proves every deposited statement with no `sorry`, over the same definitions, and checks each
proved statement's type against the deposited statement file. The deposited files are unchanged.

What this establishes: the stated mathematics, at the pins above, from the three standard axioms. It does
not establish novelty or any empirical claim.
