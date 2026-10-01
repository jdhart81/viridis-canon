# Contributing to the Viridis Canon

The canon is run like a versioned codebase. A few principles keep it coherent.

## Verification standard (non-negotiable)

A module is admissible only if it:
1. **builds** under the pinned `lean-toolchain` against Mathlib (`lake build`);
2. has **zero `sorry` / `admit`**;
3. has every named theorem's axiom dependency **audited to `⊆ {propext, Classical.choice, Quot.sound}`**;
4. is **non-vacuous** — hypotheses are used; conclusions are not trivially `True`.

Protected `main` requires CI evidence for all four standards: repository
hygiene and vacuity lint, the current Lean build and axiom audit, the pinned
historical P0 build and axiom audit, and the deterministic catalog check.

## Structure (the git model)

- **Spine** (`main`, this package) = the minimal load-bearing IB skeleton. Curated, milestone-only releases under concept DOI [10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982).
- **Series S1–S6** = thematic branches, each its own Zenodo concept DOI, `isDerivedFrom` the spine.
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
4. For a Viridis publication wave, close Zenodo, exact GitHub source, DOI map,
   series index, catalog, CI, and the release receipt in the same run. A passing
   pull request does not itself authorize an irreversible Zenodo publication.

## External review and reproduction

External contributions do not need to propose new canon records. Independent
reproductions, critiques of assumptions, citation/reuse notices, and empirical
tests are especially valuable. Submit them with the
[external-validation issue template](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml).
The repository records the evidence at the level it supports; traffic and
downloads are never promoted to validation or adoption.

Automated tools may appear in provenance records and Git co-author trailers,
but they are not research authors. See
[`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md).

## License

Contributions are accepted under **Apache-2.0** (code) / **CC-BY-4.0** (docs).

## Sign your commits (DCO)

Pull requests from forks need a `Signed-off-by` line on every commit, matching the commit author's email:

    Signed-off-by: Your Name <you@example.com>

`git commit -s` adds it, and `git rebase --signoff origin/main` fixes an existing branch. Signing off
certifies the Developer Certificate of Origin 1.1 (https://developercertificate.org): you wrote the
change, or you have the right to submit it under this repository's license. The DCO check blocks
unsigned commits.

## License of contributions

Contributions are licensed under the same license as the files they change (see `LICENSE`), with no
additional terms. Don't submit work you can't license that way.

## Never commit

Credentials, API keys, private keys, `.env` files, customer or partner data, or wallet files. The secret
scan blocks known key formats. If you find a leaked secret, report it privately as described in
`SECURITY.md`.

## Names and marks

The license does not cover Viridis names, logos or certification marks. See `TRADEMARKS.md`.
