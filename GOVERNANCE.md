# Viridis Research community governance

## Purpose

The community can reproduce, challenge, extend, and apply Viridis research
without collapsing distinct evidence gates. Open contribution does not imply
Canon admission, empirical validation, publication, or ViridisOS deployment.

## Roles

- **Contributors** propose evidence, code, formalizations, reviews, data, and
  documentation through issues and pull requests.
- **Reviewers** evaluate scope, reproducibility, proof artifacts, citations,
  rights, safety, and product interfaces. A reviewer does not approve their own
  contribution.
- **Viridis Research Curator** classifies verified results, maintains dependency
  and DOI links, and recommends Working Corpus, Series, or Canon routing.
- **Release owner — Justin D. Hart** authorizes exact rights, Zenodo publication,
  Canon-spine mutations, and production ViridisOS deployment.

Maintainer access is earned through sustained, accurate review and can be
removed for security, conduct, provenance, or evidence-integrity failures.

## Contribution lifecycle

```text
proposal or reproduction
        ↓
scope, rights, provenance, and prior-work review
        ↓
tests plus Lean/formal review where the claim is mathematical
        ↓
Harmonic Aristotle verification for release-bound proof claims
        ↓
Working Corpus or Series recommendation
        ↓
exact Zenodo → Git release authorization
        ↓
optional ViridisOS adapter review and deployment authorization
```

Every public research release must preserve an immutable evidence trail. A
published Zenodo version is never silently rewritten; corrections use a new
version with a changelog and predecessor link.

## Canon-spine admission

A clean Lean build is necessary for applicable formal claims but is not enough
for the Intelligence Bound Canon spine. A candidate must pass all five gates in
`CANON_SPINE_DOCTRINE.md`:

1. foundational;
2. irreducible;
3. domain-defining;
4. milestone-coherent; and
5. stable.

Failure of any gate routes the work to the Working Corpus or a Series. That is
the normal maturation path, not a rejection. Canon-spine releases require an
explicit, exact decision by the release owner.

## ViridisOS integration

A research result reaches ViridisOS only through a separately reviewed adapter
that declares:

- the exact Zenodo DOI and Git source commit;
- typed inputs, units, assumptions, and missing-data behavior;
- outputs, uncertainty, refusal conditions, and human-review triggers;
- tests connecting the adapter to the formal or numerical evidence; and
- field-validation status and known limitations.

No adapter may present formal verification as proof of empirical, ecological,
causal, legal, commercial, or safety outcomes.

## Decisions and appeals

Routine changes are accepted through reviewed pull requests. Maintainers record
the reason for a hold or rejection against the relevant gate. A contributor may
appeal by supplying new evidence in the same issue or pull request. Rights,
publication, Canon-spine, and production-deployment decisions remain with the
release owner and cannot be inferred from votes, reactions, or passing CI.

Material governance changes use a public pull request with at least seven days
for comment. Emergency security or legal holds may be immediate and must be
documented when disclosure is safe.
