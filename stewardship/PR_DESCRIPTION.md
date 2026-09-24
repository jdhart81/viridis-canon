# Information-weighted stewardship: AC lifetime certificate and claim corrections

The historical stewardship theorem named `setpoint_J_beats_forcing_J` proved
only positivity of g(Dstar)/r; its description discarded forcing's early output.
This change adds an actual locally absolutely continuous infinite-horizon
comparison, derived from the physical-model ODE, including terminal limits,
exact polynomial regret, feasibility, equality cases, and the q=1 counterpart.
It reuses the existing logistic growth and raw setpoint definitions.

Misleading legacy theorem names remain as deprecated aliases. Documentation
separates sustained g(D*)/φ from instantaneous ΩD*, restores φ in the general
duty formula, limits drift statements to what they prove, and classifies the
attention-price derivative as a consequence of an assumed linear cost.
Published deposits and both historical/current proof pins are preserved.

Validation: the full candidate compiled under Lean 4.28 / Mathlib 8f9d9cff;
an enforcing audit covers 67 candidate declarations with the existing three-axiom
allowlist. The independent numerical implementation recovers the benchmark,
passes 25 adversarial tests, checks seven symbolic identities, runs 384 schedules
with infinite tails, and preserves all four seeded channel confidence intervals.
Current/P0/deposit/corpus regression results and exact command receipts are in
`stewardship/evidence/final-verification-2/verification.json`.

This is a local research candidate, not spine admission. The supplied ZIP and
its formalization specification were unavailable: its SHA/internal manifest and
original 24-test run remain unverified. Matching independent results do not
remove that gate. The constructed channel is analytically derived and numerically
checked, but not represented as a probability-space theorem in Lean. No empirical,
novelty, physical energy-price or universal alignment claim is introduced.


Two existing source-binding manifests are updated after an exact declaration/proof
comparison. The stewardship theorem-name string changes to the corrected name
(manifest 1.1.0); runtime formulas and admission tiers are unchanged. The attention
manifest's source hash and explanatory summary are updated (1.0.1). All original
integration failures are retained alongside the repair evidence.
