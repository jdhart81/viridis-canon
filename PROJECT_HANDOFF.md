# Information-weighted stewardship handoff

## Current decision

Ready for review as a local research candidate. **The requested complete milestone
is NOT signed off:** the supplied continuation ZIP, its internal manifest,
LEAN_FORMALIZATION_SPEC.md and original executable sources were not located.
Their authenticity/spec compliance and reported 24-test run remain unverified.
The next action is to provide the local path of the original ZIP, then run
`python3 stewardship/verify_package.py /actual/path/viridis_stewardship_example.zip`
before source inspection and the original package reproduction.

## Repository and authority

Repository: https://github.com/jdhart81/viridis-canon . This is a fresh local
clone of that existing repository at baseline
`85505cfe7f2f8d3977a96e18ea6d27a6ae8dd692`, on local branch
`research/information-weighted-stewardship`. The clone began clean.
The working diff is deliberately uncommitted for review. No remote push, PR,
merge, release, deployment, admission or paid proof job occurred. Unrelated
applications and production services were not edited.

The local workspace alias with two spaces before “2.0” resolves to the directory
with one space. The default executor rejected the symlinked writable root before
execution; approved local commands were used. No approval was bypassed.

## Completed science and implementation

`InformationWeightedStewardship.lean` assembles `global_certificate` from
`InformationWeightedStewardship/{Algebra,Trajectory,Lifetime,Equality,Raw}.lean`.
It is a full locally absolutely continuous infinite-horizon theorem, not a C1
substitute or algebra-only result. Admissibility contains stock bounds, measurable
control, local AC and the a.e. ODE; no accounting/regret/dominance hypothesis.
The finite identity, objective/potential integrability, terminal limit, exact
regret, feasible stationary integral and both equality directions compile.
The q=1 square-regret comparison and arbitrary-initial-state upper bound compile.
The enforcing audit checks all six candidate modules and 67 declarations against
{propext, Classical.choice, Quot.sound}; no proof holes or extra axioms.

The defensible claim: under the declared deterministic fluid model, fresh-bit
channel quality q(d)=d/K, positive parameters, 0<r<2α, feasible holding
Ω≥(α+r)/(3φ), and D(0)=K(2α−r)/(3α), stationary stewardship maximizes the actual
discounted lifetime objective over every already-admissible AC policy. Equality
requires constant stock everywhere and held effort a.e. No general initial-state
optimal controller, stochastic-event transfer, ecological validation, universal
information-energy price, or novelty is established.

The probability-space channel model and general controlled-ODE existence/invariance
are analytical, not new Lean theorems. The formal comparison quantifies over
already-admissible trajectories and proves that the stationary class is nonempty.
For random stock, scalar I(X;O|D)=E[D]/K; the statewise value is I(X;O|D=d)=d/K.

`stewardship/model.py`, `test_model.py`, and `run.py` are an independent implementation,
not reconstructed or authenticated copies of missing package code. It includes
independent DOP853 objective integration, exact constant-duty trajectories, separate
quadrature/regret calculation, infinite tails, seeded alternatives, channel trials,
normalization, capacity and out-of-scope checks. One near-capacity rounding defect
was found, retained in a failing log, and fixed with exact decimal feasibility.

## Observed final verification

Exact one-command execution, from this repository:

```sh
python3 stewardship/verify_local.py --output stewardship/evidence/final-verification-2
```

Every step passed. Exact commands, exit codes, versions and source hashes:
`stewardship/evidence/final-verification-2/verification.json`.

- New independent tests: 25 passed, seven symbolic identities.
- Existing repository tests: 65 passed.
- Current Lean spine/AxiomAudit: passed; historical P0 (Lean 4.24/f897): passed.
- New family/enforcing audit: passed; DepositAudit: passed.
- Hygiene, candidate vacuity, deposit wiring, catalog and whitespace: passed.
- All 42 existing function manifests validate after the two scoped binding repairs.
- Proposed GitHub CI was edited but not executed remotely.

New numerical results: J*=0.7199999999999999; forcing
0.2407207380857683; raw-target comparator 0.5844503257509175; ratio
2.99101774830661; crossover 4.0359697061540984.
The analytical conservative bound is J*/J_force≥2.2, not the numerical ratio.
DOP853 vs infinite quadrature differs by about 4.20e−14; at T=300 the analytic
omitted-tail bound evaluated in float is 9.357622968840175e−13.
384 seeded schedules (128 per m=0,1,2), 12 stages plus infinite tails, maximum
observed regret-identity residual 1.1657341758564144e−15. These are diagnostics,
not rigorous interval enclosures. The 400,000 channel trials reproduce the q=.1
Wilson interval miss with seed 1000; it remains in results without reseeding.

## Traceability and integration

Both loose supplied files remain unchanged and are hashed in
`stewardship/evidence/input-provenance.json`. Historical Git and current baseline
SST/TAT sources were identical. The public Zenodo v10.2.0 ZIP checksum matches
its metadata and the two relevant source files match the comparison commit;
see `stewardship/evidence/zenodo-comparison.json`. No broader deposit/tree
equivalence is claimed and no historical deposit was changed.

Historical positivity, drift, capacity and attention-price claims are corrected
in current source comments and claim documentation; legacy names are deprecated
aliases. Correct sustained output is g(D*)/φ. The existing φ=1 uStar definition
is retained and explicitly scoped. `stewardship/ERRATA.md` records all corrections.

The two affected source-binding manifests were reviewed byte-for-byte at their
bound declarations; proof statements/bodies differ only in the stewardship
canonical name. Runtime expressions and admission tiers are unchanged. Its
returned theorem string changes to `potential_derivative_points_toward_Dstar`
(manifest 1.1.0); attention metadata version is 1.0.1. No admission ledger was
modified. Initial source-hash failures remain in final-verification-1 evidence.

The generated catalog labels the new theorem “working / not-canon-admitted” and
excludes the audit infrastructure. The root and P0 toolchains/Mathlib pins are
unchanged; the generated P0 lockfile records its existing pinned environment.
The Bash hygiene portability repair preserves all gates and manifest inputs.

## Review materials and remaining gates

- `stewardship/INVARIANTS.md`: pre-implementation invariant map.
- `stewardship/MATHEMATICAL_CERTIFICATE.md`: full human proof and primary-source comparison.
- `stewardship/CLAIMS.md`: exact theorem/test/evidence scope map.
- `stewardship/EMPIRICAL_PROTOCOL.md`: falsifiable controlled-sensing protocol; no data invented.
- `stewardship/REPRODUCE.md`: fresh-output commands and missing-package procedure.
- `stewardship/RELEASE_CANDIDATE.md`: open review/publication gates.
- `stewardship/PR_DESCRIPTION.md`: prepared text, not a created PR.

No proof gap remains in the advertised deterministic AC lifetime comparison.
Remaining milestone requirements are supplied-archive authentication, specification
reconciliation and original-package reproduction. Independent review and remote CI
are still pending; release/admission/publication require Justin's approval.

Raw compiler/command captures are archived byte-for-byte in
`stewardship/evidence/execution-logs.zip` with a per-member hash manifest. They
remain on disk, including all failed attempts. Compiler whitespace is preserved;
logs are not treated as editable source. Extract the archive as described in the
reproduction guide when reviewing a fresh checkout.
