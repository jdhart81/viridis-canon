# Auto-intake: proven engine results become live kernels

**Owner decision (2026-11-17, Justin Hart):** when the science engine proves a statement that is
a spin-off function or service for Viridis Conservation, it is entered into this canon and goes
live automatically, with no human merge, once every check passes. `os/auto_intake.json` holds
that decision as two switches (`enabled`, `go_live`) and `os/core.json`
`authority.automatic_kernel_activation` mirrors `go_live`.

## The path

```
viridis-engine nightly (one job)            jdhart81/viridis-research
  run certified ───────────────────────────► index/certified.json  (PROVEN, sealed hash, proof hash, DOI)
  auto-intake step (tools/auto_intake/engine_step.sh)
    1 plan        python3 -m canon_core auto-intake plan        every statement: CANDIDATE / WAIT / SKIP + reason
    2 draft       engine Claude, docs/auto_intake/DRAFTING.md   one candidate per night: package, or decide C/RECERT
    3 verify      ... auto-intake verify                        every gate below; any error = stop
    4 apply       ... auto-intake apply                         family, research intake, ledger, regenerated indexes
    5 go-live     ... auto-intake go-live                       os/core.json + os/admissions.json + tier admitted
    6 gates       validate-functions, build-os, unit tests, generated-index checks
    7 PR          branch auto-intake/<statement>, PR, wait for canon CI, merge only when green
  jdhart81/viridisos
    8 refresh     tools/refresh_from_canon.py → runtime/canon_auto_kernels.json, GET /auto-kernels; PR, merge when green
  jdhart81/viridis-canon release
    9 release     when main's live-kernel files differ from the newest canon-v release: publish canon-vYYYY.MM.DD;
                  the os-bundle workflow builds the bundle from that tag and attaches it with its DIGEST
  viridis-conservation-app (viridisconservation.com)
   10 site        once that release carries its DIGEST: the app's scripts/sync-canon-bundle.sh moves the pinned
                  bundle on branch auto-intake/site-<tag>; PR; merge when the app's checks pass
  owner note      python3 -m canon_core auto-intake note --since <last run>   (folded into the kernel-flag email)
```

The product (viridis-conservation-app) vendors the canon `os-bundle` and pins its digest. Steps 9
and 10 carry a new live kernel there: a kernel merged one night is released that night, and the
site takes the released bundle on the next run once its DIGEST is attached. The site moves only
through its own `scripts/sync-canon-bundle.sh` (which must verify the bundle against the release
DIGEST with `canon_core verify-os` and support `--check <tag>`), only on a branch with a PR, and
only when the app's own checks pass. Without that script the site stays pinned and the step says so.

## Three phases, so the write token never meets drafted code

The step is three workflow steps in the engine's nightly job, each a `PHASE` of
`engine_step.sh`:

| Phase | Credentials | Runs | Does |
|---|---|---|---|
| `fetch` | `AUTO_INTAKE_TOKEN`, as the runner user | only `gh` and `git` | sweeps open auto-intake PRs (merge green, alert on red, missing or stalled checks), publishes the canon release, downloads the newest released bundle into `$AI_IN` |
| `build` | none; a separate unprivileged user under `env -i`, on copies of the checkouts | the drafter, the package's `runner.py`, every gate, ViridisOS tests, the site's sync script and tests | steps 1–6, 8 and 10 above; writes each change to `$AI_OUT/<canon\|viridisos\|site>/` as `branch`, `patch`, `body` |
| `publish` | `AUTO_INTAKE_TOKEN`, as the runner user | only `gh` and `git`, in a fresh clone with hooks off | refuses any patch outside its allowed paths, applies it, commits with a fixed message, pushes the branch, opens the PR |

Allowed paths, checked before a patch is applied (`check_patch`):

- canon: one `research/<id>/`, `tests/test_os_auto_<id>.py`, `os/research_statements.json`,
  `os/families.json`, `os/research_intake.json`, `os/core.json`, `os/admissions.json`,
  `formalization.yaml`, `README.md`, `docs/overview/index.html`; a decline only the ledger;
  no deletions
- viridisos: `runtime/canon_auto_kernels.json` only
- site: `os-bundle/` only

Any rename, mode change, symlink, submodule, quoted, absolute or `..` path refuses the whole
change. Run without `PHASE`, the step only sweeps and releases, and says so.

Every problem is an `ALERT` line; the engine collects them, and any failed phase, into one open
issue in viridis-engine ("Auto-intake needs attention"), which emails the owner.

## Invariants (tests/test_os_auto_intake.py)

| | Invariant | Where it is enforced |
|---|---|---|
| AI-1 | Only a statement PROVEN in the certified index, with a proof, not closed by a single tactic, labelled PROVEN and non-trivial in its run's certification.json, and classified **A** (new service) or **B** (strengthens one) enters. TESTED results never become kernels; SEALED_UNPROVEN and every other status never enter. Text naming the Intelligence Bound must call it a conjecture and never proven; no kernel is called product-ready. | `eligibility`, `verify` |
| AI-2 | A statement already in `os/research_statements.json`, or already backing a function, is skipped; applying twice writes once. | `plan`, `verify`, `apply` |
| AI-3 | The package is `research/<function id>/` with `function.json` (decision_kernel, callable, READY, NOT_VALIDATED, inputs with units, the run's DOI, a boundary that says what is not established), `runner.py`, `intake.json`, verbatim copies of the sealed statement and the checked proof pinned by the index hashes, and `tests/test_os_auto_<id>.py`. Every statement part is a machine check replayed on the example, at least three cases and the negative controls. | `verify`, `conformance_problems` |
| AI-4 | `verify` lists every problem and exits non-zero; the engine step merges only when verify, validate-functions, build-os, the unit tests and canon CI are green, and otherwise leaves the PR open with the reason. | CLI, `engine_step.sh` |
| AI-5 | ViridisOS's auto-kernel list refreshes from the merged canon and refuses to disagree with the canon's live list. | viridisos `tools/refresh_from_canon.py` |
| AI-6 | Go-live is one switch. With `go_live` false nothing is written to `os/core.json` or `os/admissions.json`. Each live kernel's admission entry names the owner decision and its rollback. Rollback is one command (or one revert) and a rolled-back kernel never comes back by itself. | `go_live`, `rollback` |
| AI-7 | Every entry, go-live, rollback and decline is a ledger entry with statement, run, class and reason; `plan` gives every skip a reason; `note` gives the owner one line per kernel. | `os/research_statements.json`, `note` |
| AI-8 | One kernel per night (`max_new_kernels_per_run`), inside the existing nightly job; no new schedule. Canon and ViridisOS are public, so their CI costs nothing against the Actions cap. | `os/auto_intake.json`, `engine_step.sh` |
| AI-9 | The write token is never in reach of code a drafter wrote or a merged kernel ships: `build` refuses to start with any credential in its environment, in a checkout's git config or remote URL, or in gh's login; `publish` runs only gh and git and applies only patches inside the allowed paths. | `engine_step.sh` phases, `check_patch` |
| AI-10 | Nothing fails quietly: red, missing or stalled (`STALL_HOURS`, default 12) checks, a release without its DIGEST after 3 hours, a refused patch, a failed gate and any failed phase raise an alert that reaches the owner as an issue. | `alert`, engine report step |

## Classes

- **A**: a new decision service a Viridis Conservation buyer would use.
- **B**: strengthens an existing service; `strengthens` names it.
- **C**: proven, but no buyer decision (a lemma rung, a refutation, pure infrastructure). Logged, never entered.
- **RECERT**: re-proves the backing of a kernel that is already live. Handled by the re-certification path, never entered as a new kernel.

## Roll back a live kernel

```
python3 -m canon_core auto-intake rollback --function <id>
python3 tools/build_certificates_index.py && python3 tools/build_formalization_yaml.py   # rollback already runs these
```

Commit, open a PR and merge it; or simply revert the PR that brought the kernel in. Rollback takes
the kernel out of `os/core.json` and `os/admissions.json`, sets its tier back to callable (so the
OS build leaves it out of the live bundle and records why), and marks the ledger ROLLED_BACK. The
next run publishes a canon release without it and moves the site to that release. To take it off
the site at once, pin the site to the release before the kernel arrived:
`scripts/sync-canon-bundle.sh <previous canon-v tag>` in the app, then merge that PR. The
statement is not screened again. To stop new kernels going live, set `go_live` to false in
`os/auto_intake.json` and `automatic_kernel_activation` to false in `os/core.json`; to stop
intake entirely, set `enabled` to false.

## Why the Lean files are `.lean.txt`

The proof is compiled and axiom-audited by the engine in viridis-research, against that repo's
lake environment. The canon keeps a verbatim copy pinned by the index hashes so the manifest can
bind to it; the `.txt` suffix keeps the canon's compile census and catalog from trying to build a
file that imports `ViridisStatements` outside its environment.
