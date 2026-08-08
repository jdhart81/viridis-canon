# Versioned post-Lean packaging overlay

The immutable pre-Aristotle paper is preserved under its original SHA-256:

- `paper.pdf`: `5d520ccde5f24ff4f3ba48b47b23d44d2e58d0760ba46052537b5550371f4bdd`
- `paper.tex`: `914ee219d6ece78d01c8d494b996a51edd69cdbfffa9d82ee539b285dd2c8428`

This release overlay changes only the manuscript's formal-status, disclosure,
stage, and route wording after the successful frozen-statement Aristotle audit.
No mathematical statement, scheduler model, numerical input, policy diagnosis,
policy proposal, or adoption state was changed.

For portability, `verification.py` now reads the included byte-identical policy
file rather than an absolute Desktop path. The policy digest remains
`fdee0f1dff1a92ebe42ef7413a98b39b771b8759ad385ba3fb037898935cd09e`,
and the fresh 22-check output exactly matches the sealed output.
