# Contributing to the Viridis Canon

The canon is run like a versioned codebase. A few principles keep it coherent.

## Verification standard (non-negotiable)

A module is admissible only if it:
1. **builds** under the pinned `lean-toolchain` against Mathlib (`lake build`);
2. has **zero `sorry` / `admit`**;
3. has every named theorem's axiom dependency **audited to `⊆ {propext, Classical.choice, Quot.sound}`**;
4. is **non-vacuous** — hypotheses are used; conclusions are not trivially `True`.

CI enforces (1) and (2) on every push; (3)–(4) are checked at proof time.

## Structure (the git model)

- **Spine** (`main`, this package) = the minimal load-bearing IB skeleton. Curated, milestone-only releases under concept DOI [10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982).
- **Series S1–S5** = thematic branches, each its own Zenodo concept DOI, `isDerivedFrom` the spine.
- A result is admitted to the spine only if it is foundational, irreducible, domain-defining, milestone-coherent, and stable (the 5-gate Spine Admission Test). Everything else routes to a series or a standalone record. The bar for the spine is deliberately high.

## Relationship to Mathlib — we upstream, we don't fork

This package **depends on** Mathlib. It is **not** a candidate for inclusion *into* Mathlib: Mathlib accepts only general, reusable mathematics, not application-specific theorems (D-Scores, corridors, biosphere productivity).

The right contribution path:
- **Keep** the domain-specific theorems here, in the canon.
- **Upstream** the genuinely general lemmas discovered while building proofs as **targeted Mathlib PRs** (e.g. arithmetic/analysis lemmas with no Viridis-specific content).

Prior upstream contributions: Mathlib PR [#37954](https://github.com/leanprover-community/mathlib4/pull/37954) (`div_mul_div_cancel`), among others. Discussion happens on the [Lean Zulip](https://leanprover.zulipchat.com/).

## Adding a module

1. Verify it (Aristotle or local), confirm the four standards above.
2. Add the `.lean` file and register it in `lakefile.toml` (`lean_lib` + `defaultTargets`).
3. Open a PR; CI must be green.
4. Deposit the corresponding Zenodo record (series or standalone) and link it in the README.

## License

Contributions are accepted under **Apache-2.0** (code) / **CC-BY-4.0** (docs).
