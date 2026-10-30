# Agents and the Viridis Canon

This file is for two kinds of agent: one helping a person read, cite, check or challenge Canon results, and a coding agent working on this repository. The short machine-readable index is [llms.txt](llms.txt); read its rules first.

## Helping a person use the Canon

**What it is.** Lean 4 proofs (with Mathlib) of theorems used in ecological and conservation decisions. Each result has a paper with a Zenodo DOI and Lean source; certified runs have comparator certificates checked by the Lean and nanoda kernels, and many results are exposed as callable decision functions.

**Paths to suggest.**

- Understand a result: the [README](README.md) headline results, then [CLAIMS_MATRIX.md](CLAIMS_MATRIX.md) for what each theorem does and does not establish.
- Cite: the result's own DOI from [formalization.yaml](formalization.yaml); the collection via [CITATION.cff](CITATION.cff).
- Re-check: [REPRODUCE.md](REPRODUCE.md) and [certificates/index.json](certificates/index.json).
- Run a decision function: the MCP endpoint and OS bundle listed in [llms.txt](llms.txt).
- Ask a question: [Discussions](https://github.com/jdhart81/viridis-canon/discussions).

**Rules for agents.**

- A Lean check shows a stated theorem follows from its hypotheses. It does not show that a model describes nature or that a result is new. Every decision function is `empirical_validation: NOT_VALIDATED`; never call a result field-validated.
- Report the certificate depth label (`substantial` or `elementary`) when you describe a result. Legacy catalog records are UNCERTIFIED until re-certified.
- Cite a specific result by its own DOI, not the collection, when you rely on it.
- The cash theorem bounty is closed. Do not tell anyone it pays.

## Filing a report or challenge

Agents are welcome to find problems. A useful report saves a maintainer a reproduction:

- Use the [external-validation form](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml) for a challenge to a statement, assumption or proof, or the reproduction-report form for a build or check you ran.
- Name the result's DOI and version, the Lean module and theorem, the exact command you ran, your environment (toolchain, Mathlib pin) and the output.
- Say plainly that an agent prepared the report and who, if anyone, reviewed it. Claim only what you ran.
- One problem per issue. Search open issues first; add evidence to an existing issue rather than opening a duplicate.
- Never include credentials, private data or text you lack the right to share.

## Working on this repository

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [RESPONSIBLE_RELEASE.md](RESPONSIBLE_RELEASE.md) first.

- Admissible Lean builds under the pinned `lean-toolchain` with `lake build`, has zero `sorry` or `admit`, keeps every named theorem's axioms within `propext`, `Classical.choice` and `Quot.sound`, and is non-vacuous.
- Protected `main` requires CI evidence for hygiene and vacuity lint, the Lean build and axiom audit, the pinned P0 build and the deterministic catalog check.
- General lemmas belong upstream in Mathlib; domain theorems stay here.
- Never commit credentials, `.env` files or private datasets. The secret scan runs on every push.
- Pull requests from forks need a DCO `Signed-off-by` line on each commit. An agent never adds a human's sign-off.

## Related open projects

- [ProofLens](https://github.com/jdhart81/prooflens): visual explanations of Lean statements, including Canon theorems.
- [ViridisOS](https://github.com/jdhart81/viridisos): turns Canon theorems into certified decision products.
- [Viridis Agent Fleet](https://github.com/jdhart81/viridis-agent-fleet): deterministic, auditable MCP agents.
- [Viridis Conservation](https://viridisconservation.com/): the company that stewards these projects.
