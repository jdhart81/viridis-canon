# The Ecopoietic Hedge - reproducible release object

This is the proposed first release under `VRS-SUBMIT-INVARIANT-1`.

## Reproduce the Lean proof

```bash
cd lean
lake build EcopoieticHedge
```

The toolchain is Lean `v4.28.0`; Mathlib is pinned to
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

## Reproduce the numerical checks

```bash
python3 code/verification.py
```

Expected terminal summary: `RESULT: 32 PASS / 0 FAIL` and
`STATUS: NUMERICAL_GATE_PASS`. These are synthetic model checks, not field
validation.

## Scope

The paired Lean file proves the exact model claims reconciled in
`provenance/POST_ARISTOTLE_REVIEW.json`. It does not prove microbial efficacy,
site suitability, adoption, or restoration outcomes.

## Contents

- `paper.pdf`, `paper.tex` - final manuscript and source.
- `lean/` - exact theorem source and pinned build environment.
- `code/` - deterministic numerical checker and expected output.
- `provenance/` - Aristotle summary, formal audit, statement contract, and
  exact-hash post-Lean review.
- `zenodo_metadata.json` - proposed metadata; no DOI has been minted.
- `CITATION.cff`, `LICENSE.md`, `SHA256SUMS.txt` - citation, rights, and bundle
  integrity.

Justin D. Hart is the accountable human author. Aristotle and Codex are
disclosed as automated proof/research tools; they are not authors.
