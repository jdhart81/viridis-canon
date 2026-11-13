# Compile census

`tools/compile_census.py` compiles every Lean file in this repository on its own, at the pins its project
declares, and audits every declaration the file contributes against the three standard axioms
(`propext`, `Classical.choice`, `Quot.sound`). The `compile-census` workflow runs it weekly and on every
change to a Lean file, and fails if a file is missing from the ledger or is newly not clean.

`ci.yml` builds chosen targets (the spine, the historical P0 module, the deposits in `DEPOSIT_MANIFEST.txt`).
The census leaves no `.lean` file out.

## First census, 2026-11-13

278 Lean files; 6,947 declarations (4,966 theorems) audited.

| Result | Files | Meaning |
|---|---|---|
| CLEAN | 188 | compiles; every declaration rests on the standard axioms only |
| NO_DECLARATIONS | 19 | compiles; an axiom-audit script or an import hub that adds no declaration |
| NONSTANDARD_AXIOM | 68 | compiles; at least one declaration depends on `sorryAx` |
| COMPILE_FAILED | 3 | does not compile at its declared pins |

- The verified spine (`SPINE_MANIFEST.txt`, 36 files) is CLEAN throughout, and so is the historical
  Intelligence Bound module `P0_IntelligenceBound_COMPILED.lean` at Lean 4.24.
- 61 of the 68 files with `sorryAx` are statement or challenge files. They state claims with `sorry` on
  purpose, and a file beside each compiles clean. The census does not check that the clean file proves
  those statements. 2 more are gate test fixtures.
- `P9_AI_Safety.lean` is quarantined and does not parse.

### Gaps found, and closed the same day

| Project | What the census found | Closed by |
|---|---|---|
| `series/BCAN` (DOI 10.5281/zenodo.22236387) | The only Lean file closes every theorem with `sorry`. | `CorridorAlignmentProofs.lean` |
| `series/RCBN` (DOI 10.5281/zenodo.22236441) | The only Lean file closes every theorem with `sorry`. | `CheckpointBalanceProofs.lean` |
| `series/SBRN` (DOI 10.5281/zenodo.22236458) | The only Lean file closes every theorem with `sorry`. | `StewardshipBottleneckReserveProofs.lean` |
| `series/ACCN` (DOI 10.5281/zenodo.22236361) | The candidate proof does not compile (type mismatch, line 35). | `VERIFICATION_PROOFS.lean` |
| `series/DCAE` | The candidate proof does not compile (unsolved goals, line 12). | `VERIFICATION_PROOFS.lean` |

Each proof file proves every deposited statement with no `sorry` and checks, by `type_of%`, that each proved
statement is the deposited one. The deposited files are unchanged, so the two candidate files still do not
compile and are recorded as `superseded`. Each folder has a `CENSUS_NOTE.md`. The proof files are listed in
`catalog/config.json` `exclude` for now: admitting a new record to the public catalog needs the private
coverage ledger, which is a separate step.

The first four folders carry a `COMPARATOR_SUMMARY.md` that reports a zero-sorry certificate from a private
verifier with no local Lean run. The candidate that verifier checked is not in this repository. The census
measures only what is here.

## What CLEAN does not mean

That a theorem says what its paper claims, that its hypotheses can be satisfied, or that the result is new.
CLEAN means the file compiles at its declared pins and rests on the standard axioms.

## Files

- `known_gaps.json`: every file that is not clean, with its status, kind and reason. Closing a gap means
  fixing the file and removing its entry.
- `ledger-<date>.json`: a dated snapshot of one census. The live ledger is the `compile-census-ledger`
  artifact of the latest workflow run.
