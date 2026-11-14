# Boundary essentiality in the product-form Intelligence Bound

`Non_Substitutability_Complete.lean` is the corrected form of the Lean file deposited in May 2026 at
[doi:10.5281/zenodo.20010754](https://doi.org/10.5281/zenodo.20010754) as "Formal Verification of the
Non-Substitutability Theorem".

## What is proved

This file formalizes the product-form bound F(P, D) = P·D/(k_B·T·ln 2). It proves:

- boundary essentiality: F(P, 0) = 0;
- continuity of F as D → 0;
- the compensation formula: a finite ΔP offsets any partial loss of D;
- the isoquant P·D = constant.

It does **not** prove that biodiversity is non-substitutable. Under the product form, power and D
substitute at unit elasticity. The canon's certified non-substitution result is the min-form data wall
(`data_wall`; see [`CLAIMS_MATRIX.md`](../../CLAIMS_MATRIX.md)). Machine-checked means logically valid
given the model, not empirically validated.

## What changed from the deposited file

| Change | Why |
|---|---|
| Two docstrings that ended with `--` now end with the block-comment terminator | In the deposited file everything after the first of them was inside a comment, so `D_vanishes_at_extinction`, `D_positive_of_species_positive` and `extinction_irreversible` were never checked |
| `no_finite_compensation` → `compensation_formula` | The theorem proves that a finite ΔP = P·ΔD/(D−ΔD) restores the bound |
| `economic_non_substitutability` → `isoquant_is_hyperbola` | The theorem characterises the isoquant P·D = r·E_L |
| `extinction_irreversible` → `bound_zero_at_zero_species` | The theorem proves the bound is zero at zero species; it says nothing about reversibility |
| Comments and the file header | They now state what each theorem proves; the header names Justin D. Hart as author and the AI tools as tools |

The old names remain as deprecated aliases. No statement or proof was changed.

## How it is checked

The canon compile census (`tools/compile_census.py`, workflow `compile-census`) compiles this file on its
own at the repository pins and audits every declaration's axioms. Its status is in
`reports/compile_census/`. No comparator certificate covers this file. The file is excluded from the
public catalog (`catalog/config.json`) until it is admitted through the coverage ledger.
