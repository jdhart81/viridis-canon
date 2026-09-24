# Reproduce the review candidate

From the repository root, with Python 3.14 and the existing elan toolchains:

```sh
python3 stewardship/verify_local.py --output stewardship/evidence/my-fresh-run
```

The output directory must not already exist. This installs only the pinned
numerical requirements into `.venv-stewardship`, runs all 25 new tests and the
benchmark, existing repository tests, hygiene/vacuity/deposit wiring, current
Lean and its audit, the candidate and its separate enforcing audit, DepositAudit,
the historical P0 with its original Lean 4.24/Mathlib f897 pin, and the catalog
check. It records exact commands, working directories, exit codes, versions,
source hashes and evidence classes in `verification.json`. Failures are retained;
a successful run does not mark the missing-package milestone complete.

The candidate is an explicit Lake target and a required CI step in the proposed
diff, not an admitted/default spine target. Existing default targets and checks
are preserved. Fresh network dependency acquisition can take several minutes.
Do not update the repository's toolchains to bypass a failure.

To run only the new checks in an already prepared environment:

```sh
.venv-stewardship/bin/python -m unittest discover -s stewardship -p test_model.py -v
.venv-stewardship/bin/python stewardship/run.py --output stewardship/evidence/my-fresh-benchmark
lake build InformationWeightedStewardship InformationWeightedStewardshipAudit
```

The independent implementation computes its outputs; saved numbers are only
regression references. There are seven symbolic checks; 384 schedules total
(128 per m=0,1,2), 12 stages and an infinite tail each; 400,000 channel trials.
Forcing's independent ODE check uses T=300 and omitted objective bound
ΩK exp(−rT)/r≈9.3576e−13. Quadrature estimates are not rigorous enclosures.

## Supplied continuation package: blocked, not silently replaced

Only `/Users/justinhart/Desktop/theorem_and_proof.md` and
`/Users/justinhart/Desktop/results.json` were located. Their observed hashes are
in `evidence/input-provenance.json`; neither was changed. Searches covered the
workspace/science trees and Desktop/Downloads. No archive, internal manifest,
LEAN_FORMALIZATION_SPEC.md, AlgebraCertificates.lean, example.py or test_example.py
was available. The reported 24 tests are therefore not an observed original-package
run. The independent 25 tests are different tests.

When the original ZIP is located, first run the read-only verifier:

```sh
python3 stewardship/verify_package.py /actual/path/viridis_stewardship_example.zip
```

It requires SHA-256
`6af21f66207ed9e20dfc11ef2b991d3cac077de066e9dde7b13f329c20021a9e`
and verifies every internal SHA256SUMS entry, with no regeneration. It refuses
unsafe/duplicate members, missing or unlisted files and checksum discrepancies.
Preserve the ZIP and its manifest. Then inspect every source/spec for side
effects and scope, extract to a separate input directory, and execute its original
commands in a separate environment, directing output to a fresh results directory:

```sh
python -m pip install -r requirements.txt
python -m unittest -v test_example.py
python example.py --output /new/results/directory
```

Compare the new formalization against the original specification and record any
mismatch explicitly. Do not infer archive authenticity from matching benchmark
numbers or create a replacement manifest for supplied data.

## Preserved execution logs

The original success and failure logs are stored byte-for-byte in
`evidence/execution-logs.zip`, with per-member SHA-256 in
`evidence/execution-logs-manifest.json`. Raw `.log` files remain locally but are
not individually included in Git; compiler-generated whitespace has not been
rewritten to satisfy source formatting checks. To inspect logs in a fresh clone:

```sh
python3 -m zipfile -e stewardship/evidence/execution-logs.zip stewardship/evidence
```

No proof, axiom, numerical or source-integrity gate is disabled by this packaging.
