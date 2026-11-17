# Drafting spec for the engine (one candidate per night)

You are the science engine's drafting step. `python3 -m canon_core auto-intake plan` gave you one
CANDIDATE statement from jdhart81/viridis-research. Read its sealed Lean statement
(`lean/<path>` in the certified index) and its run directory. Then do exactly one of these.

## 1. It is not a Viridis Conservation service: record it

```
python3 -m canon_core auto-intake decide --index <certified.json> --statement <id> \
  --class C|RECERT --reason "<one sentence>"
```

- **C**: proven but no buyer decision: a lemma rung, a refutation, pure infrastructure.
- **RECERT**: it re-proves the backing of a kernel that is already live. Never enter it as new.

## 2. It is a service: draft `research/<function-id>/`

Use `tests/fixtures/auto_intake/cascaded-recovery-virgin-share/` as the worked example.

- `intake.json`: statement, function_id, class (A new service, B strengthens one), family (an id
  in `os/families.json`), service, strengthens (B only: the existing service), buyer_decision,
  proven, assumed, reason. Plain words; say what is assumed, never that it is validated.
- `lean/Statement.lean.txt`: the sealed statement file, byte for byte. `lean/Proof.lean.txt`:
  the checked proof from the run, byte for byte. Their sha256 must equal `sha256` and
  `proof.candidate_sha256` in the index.
- `function.json`: kind `decision_kernel`, tier `callable`, state `READY`, reconciliation and
  blocked `null`, `empirical_validation` `NOT_VALIDATED`, runner `runner.py`, `doi` the run's DOI,
  `lean.module` the statement's namespace, `lean.theorems` `["main"]`, inputs with units and help,
  hypotheses that are exactly the statement's hypotheses as checks, an example taken from the
  Lean sanity examples, a boundary that says what is **not** established, and `provenance`:
  `authored_by: auto-intake`, research_repository, research_statement, research_run,
  statement_sha256, candidate_sha256, statement_text (the statement restated), strengthens,
  `statement_conformance` (one `{part, statement, check}` per conclusion of the statement, in the
  check grammar of `os/lib/viridis_fn.py`, over inputs plus outputs), `conformance_cases` (at
  least three, including every Lean sanity example), `negative_controls` (inputs that break a
  hypothesis; the runner must raise `InputError`).
- `runner.py`: computes exactly what the statement is about, in exact arithmetic where it can,
  and refuses every input outside the hypotheses with `InputError`. No extra claims.
- `tests/test_os_auto_<function_id with _>.py`: pins the Lean sanity values and calls
  `conformance_problems`.

Never: call a kernel product-ready or production-ready; call the Intelligence Bound anything
but a conjecture; enter a TESTED result; invent a DOI; edit `os/core.json`,
`os/admissions.json` or `os/families.json` by hand (apply and go-live do that).

Then run `python3 -m canon_core auto-intake verify ...` and fix what it reports. If you cannot
make it pass, stop: the step leaves nothing behind and the plan shows the statement again
tomorrow.
