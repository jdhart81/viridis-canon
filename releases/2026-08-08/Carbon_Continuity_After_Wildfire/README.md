# Carbon Continuity After Wildfire - reproducible release object

This is the proposed Carbon Continuity release under
`VRS-SUBMIT-INVARIANT-1`. The finished paper and reviewed zero-sorry Lean
artifact pass the scientific submission invariant.

## Verified formal component

```bash
cd lean
lake build CarbonContinuity
```

The toolchain is Lean `v4.28.0`; Mathlib is pinned to
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

## Reproduce the numerical checks

```bash
python3 code/verification.py
```

Expected terminal summary: `SUMMARY: 20 PASS / 0 FAIL` and
`STATUS: NUMERICAL_GATE_PASS`. These are exact algebra and stylized model
checks, not empirical calibration or a causal field claim.

## Provenance repair

The original checker used a private absolute path solely to hash a concept
outline that the source ledger classifies as not scientific evidence. The
versioned packaging overlay binds the same digest through the included
`provenance/SOURCE_BINDING.json`; the model and all scientific artifacts are
unchanged. See `PACKAGING_OVERLAY.md` and the fresh post-overlay review.

## Scope

The formal core verifies the stated two-pool coupling threshold. It does not
verify ecological response, treatment efficacy, market implications, carbon
credits, empirical coefficients, or real-world truth.

No DOI was minted during assembly. The package was subsequently published to
Zenodo on 2026-08-08 as DOI 10.5281/zenodo.21855690 (version 0.2.0-formal,
concept DOI 10.5281/zenodo.21855689).
