import PaperFormalization.Cantelli
import PaperFormalization.Model
import PaperFormalization.TwoPoint
import PaperFormalization.Targets
import PaperFormalization.NonVacuity

/-!
# Run-127 paper-to-Lean formalization

Formalization of the frozen formal targets of the sealed paper
*The Precautionary Capacity Reserve: A Sharp Moment-Robust Stewardship Discount for an
Intelligence-Rate Model* (Run-127), as listed in `STATEMENT_CONTRACT.md`.

## Contents

* `PaperFormalization/Cantelli.lean` — Cantelli's one-sided (lower-tail) inequality, proved from
  Markov's inequality (it is not available in the pinned Mathlib revision).
* `PaperFormalization/Model.lean` — the model definitions and assumptions of the paper:
  `RateModel` (`P`, `k_B`, `T` positive and fixed), `RateModel.ceiling` (Eq. 1),
  `RateModel.requiredCapacity` (Eq. 2), `RateModel.violationEvent` (Eq. 3),
  `cantelliFactor`, `capacityFloor` (Eq. 4), `RateModel.certifiedRate` (Eq. 5),
  `RateModel.meanPlugInCeiling`, `coeffVar`.
* `PaperFormalization/TwoPoint.lean` — nonnegative two-point laws and the Cantelli extremal
  two-point law used by the counterexample constructions.
* `PaperFormalization/Targets.lean` — the named frozen targets:
  `cantelli_capacity_certificate` (C1), `precautionary_rate_le_violation_budget` (paper's fifth
  target), `capacity_reserve_fraction_eq` (C2),
  `positive_floor_sharp_two_point_counterexample` (C3),
  `mean_only_plugin_arbitrarily_unsafe` (C4).
* `PaperFormalization/NonVacuity.lean` — explicit non-vacuity witnesses for every target.

See `LEAN_STATEMENT_CONTRACT.md` for the exact statement contract, the assumptions used, the
non-vacuity witnesses, the documented interpretation decisions, and the recorded toolchain and
Mathlib revision.  The development contains no `sorry`, `admit`, `axiom`, `implemented_by`,
`native_decide`, `unsafe` or `extern`.
-/
