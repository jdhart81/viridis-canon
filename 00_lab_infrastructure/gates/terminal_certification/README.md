# Inactive terminal premise HOLD selection

This narrow S8 component excludes one exact, reviewed terminal-held frozen
Comparator object from certification dispatch. It does not implement parallel
transport, issue certificates, clear prior certification debt, create a
successor, or change publication admission. Those gates remain separate.

The only reviewed receipt is Run-194's existing
`VRS-CERTIFICATION-PREMISE-HOLD-1` record with SHA-256
`0c03ddd7ff286fb114d19354616b04006529c3bf650bf21936ed6e695737c065`.
Its hash is an explicit source-reviewed allowlist entry, not a signature or a
self-authenticating assertion. A new receipt requires a new reviewed update.
No private receipt, manuscript, credential, or proof source is included here.

Before excluding dispatch the classifier checks the receipt's literal terminal,
no-transport and no-certificate flags, all six frozen byte bindings, the selected
package's exact manifest, the request's identity/input hashes and false local
Lean flag. It verifies the unchanged checker, title helper and aligner source
hashes, runs that pure static checker with `required=True`, requires exact
equality with the recorded non-certifying HOLD result, then re-reads all inputs.
The allowed reason is the recorded missing/unknown premise declaration; a
checker error, PASS, EXEMPT, substituted result or source drift never excludes
work. Missing, malformed, unreviewed or changed evidence preserves ordinary
FIFO dispatch eligibility. No Lean, Comparator transport or credential lookup
is performed by this classifier.

`EXISTING_SELECTION.patch` is an inactive patch against the two unchanged
production source snapshots identified in `INTEGRATION_BINDING.json`.
It makes both actual controller inspection paths expose the held object as a
human-held item and permits the next machine action. Continuity exposes a
separate `dispatch_fifo_runs` list, while retaining the complete `backlog_runs`,
`certified_runs`, certificate age and debt counts. The existing checkpoint's
oldest-debt target and certificate credit logic are byte-for-byte unchanged.
A younger certificate cannot satisfy the older held object's debt target.
Publication states, metadata, admission and ordering are untouched.

Tests apply the bound patch to disposable mini-repository copies, load the
actual patched controller/continuity and retain an exact checkpoint source
fixture for its original debt-credit behavior. Private runtime imports are
stubbed; no installed runtime, scheduler, CORE writer, transport, publisher or
successor is invoked.

Activation remains prohibited until Justin merges the PR, independent source
review and the applicable full S8 acceptance gates pass, and the existing
single-writer installation protocol records exact before/after bytes and a
rollback. Install the reviewed helper under
`RESEARCH_PIPELINE_v2/verification_coverage_gates/terminal_certification/` and
verify the existing checker/title/aligner pins before atomically applying the
two call-site changes. Never apply this patch to PR108-modified controller
bytes: a later combination requires a fresh exact-source patch and review.
Rollback restores both bound original source bytes and removes only the new
helper after preserving receipts; historical scientific objects stay sealed.

Run the local tests with `python3 -m unittest discover -s
00_lab_infrastructure/gates/terminal_certification/tests -v` and the behavioral
mutants with `python3 00_lab_infrastructure/gates/terminal_certification/run_mutations.py
--output <receipt.json>`. The inherited manuscript gate matrices remain required.
