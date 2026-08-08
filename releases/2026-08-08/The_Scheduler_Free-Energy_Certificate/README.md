# The Scheduler Free-Energy Certificate - reproducible release object

This package is the Run-119 release under `VRS-SUBMIT-INVARIANT-1`.

## Reproduce the numerical checks

```bash
cd code
python3 verification.py
```

Expected summary: `22 PASS / 0 FAIL` and `FINAL_NO_DRIFT_AUDIT_PASS`.
The policy and state files are exact local copies whose recorded digests match
the immutable inputs. The included policy proposal is not adopted.

## Reproduce the Lean proof

```bash
cd lean
lake build
lake env lean AxiomAudit.lean
```

The toolchain is Lean `v4.28.0`; Mathlib and all transitive dependencies are
pinned by `lake-manifest.json`.

## Scope

The six Lean theorems verify the frozen one-step, equal-cost scheduling model.
They do not establish a long-run scheduler, scientific productivity, empirical
benefit, policy adoption, execution authority, or literature priority.

The paper enters the standalone Viridis Research Operations methods corpus. It
is not an Intelligence Bound spine addition or a customer-facing business
flagship.
