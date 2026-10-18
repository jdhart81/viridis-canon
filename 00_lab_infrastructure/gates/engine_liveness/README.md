# Engine liveness: reviewed installation candidate

Run-170's writer exits 2 because its sealed manuscript says independent review
is pending while its package has a passing review. The writer correctly holds.
The executor previously discarded the writer's stdout JSON and showed empty
stderr. `G1_CONTROLLER_EXECUTOR.patch` makes that HOLD identifier visible
with a bounded, credential-redacted stderr tail, and sends the sealed-paper conflict
to agent judgment for a versioned successor and later review. It never changes
the sealed paper, certificate or existing kernel package.

The installed-source hashes in `INTEGRATION_BINDING.json` bind the patch to the
diagnosed controller and executor. Apply only after this PR is independently
reviewed, merged by Justin and green. Install `scheduler_liveness.py` beside
those two files after the exact reviewed #109 installation. The controller
before hash is #109's `86f1691f...`; its context-bearing G1 diff cannot be applied
to the original `58e9c939...` controller. `install_integration.py --pipeline PATH`
plans both patches and checks all before/source/helper hashes. Its explicit
`--apply` mode requires hash-bound merged-review evidence and a fresh receipt
path; it installs the helpers first, retains per-file rollback bytes and checks
every after hash. It never activates policy. A mismatch holds before any write. Record the installation
and exact rollback in the engine receipt. Rollback restores both before files
from the recorded snapshot and removes only the newly installed helper.

`SchedulerLane` implements the S8 policy as a library for the existing nightly
scheduler. It is not installed or active. No new schedule, transport, issuer or
publisher exists here. The scheduler must retain its current egress authority,
proof checks, named checkpoint targets and publication gates.

1. During the existing checkpoint, acquire `lane.checkpoint()` under the
   scheduler's existing writer lock. Pass eligible debt and authenticated
   terminal holds to `eligible_dispatches`, in oldest-first order. At most two
   unresolved hash-bound reservations can exist. Persist each reservation
   **before** using the existing Comparator transport; a reservation returned
   with `dispatch: false` never permits another send.
2. On transport uncertainty, retain the reservation. Reconcile the exact
   original provider request; never retry or free the slot on a timeout alone.
   `record_rejection` reads the actual terminal provider receipt, verifies its
   hash and every exact identity, then requires the same provider request ID in
   the response, fresh delivery and recorded termination diagnostics, with a
   nonzero exited phase. Failure responses carry delivery-only execution
   evidence; success-path phase observations remain a certificate gate and
   are not required for a rejection. The row retains a bounded goal excerpt
   and SHA-256 of the complete output.
   It preserves the request and never authorizes a new attempt.
3. The adapter reconciles every original reservation before dispatch: authenticated
   terminal rejection frees capacity; ambiguity retains it. A reviewed new request
   for the same Run has a new identity and never retries the rejected identity.
   Inactive rollback uses `--reconcile-certification`, with no transport or canonical
   promotion. On acceptance, use the existing issuer and its complete certificate
   validator, then call `accept` with the exact identity, artifact hashes and
   genuine kernel/premise/non-vacuity results. The supplied validator must
   validate the real certificate, proof and provider receipt; a boolean claimed
   by the caller is insufficient production evidence. Results are exclusive,
   immutable holding-area records and do not grant checkpoint target credit.
4. Real issuer certificates stay under `parallel_certification/verified-results/`
   until the nonterminal certification order has a contiguous verified prefix. The adapter
   promotes only exact bytes of that prefix to canonical paths; an out-of-order
   accepted certificate cannot become a current certified ledger row. This
   visibility step grants no publication authority. Pass only release objects that cleared **every** existing science, review,
   packaging and authority gate to `publication_prefix`. It returns the
   contiguous admitted prefix of the caller's authoritative release order.
   A terminal original can be omitted from release membership only by the
   existing reviewed successor or held-Run policy, never by this library.
5. The actual checkpoint patch adds explicit drain and rollback-reconcile actions.
   The scheduler performs its existing due-generation action before drain, and
   always reaches its existing finish path after a certification HOLD.
   `scheduler_checkpoint` is a library model used by A6; the production call
   site is the source-bound `nightly_checkpoint.py` patch. No cadence, model,
   budget or extra checkpoint changes.

The concrete inactive checkpoint adapter, exact source patch, queue/policy
schema, supported prompt amendment and rollback are in
`EXISTING_SCHEDULER_INTEGRATION.md`. Activation requires their reviewed merged
installation and a production checkpoint confirming ownership, request
reconciliation and ordered admission. Tests of this library alone do
not establish DoD-9/DoD-10. Rollback disables new reservations, reconciles every
in-flight request through its original identity, and retains all results and
scientific/publication history.

The seven acceptance tests are named A1–A7 in `tests/test_scheduler_liveness.py`.
Run `python3 -m unittest discover -s 00_lab_infrastructure/gates/engine_liveness/tests -v`.

Invariants touched: I-3 credential hygiene, I-8 certification liveness,
I-12 independent merge, I-14 evidence before action, I-15 reversible changes,
I-17 liveness with ordered publication and I-18 single writer. This patch
does not weaken the original checkpoint's two named oldest certificate targets.

The exact #109 terminal helper is the single terminal-object classifier used
by the controller, continuity reader and S8 queue adapter. Queue flags cannot
create another terminal policy. While S8 policy is present and active, both
controller certification call sites name `DRAIN_SCHEDULER_CERTIFICATION_LANE`;
the existing checkpoint drain is its only transport route. Per-run nonterminal
premise failures remain visible HOLDs and do not abort other eligible work.

Round-2 reproduction (no network or Lean):

```
python3 -B -m unittest discover -s 00_lab_infrastructure/gates/engine_liveness/tests -v
python3 -B 00_lab_infrastructure/gates/engine_liveness/run_mutations.py
python3 -B 00_lab_infrastructure/gates/engine_liveness/run_precheck_mutations.py
python3 -B -m unittest discover -s 00_lab_infrastructure/gates/terminal_certification/tests -v
```

`test_round2_rejections.py` passes all three sanitized historical Run-191
failure envelopes through the real Comparator client with inert injected
transport. It checks slot release, successor dispatch, B1 evidence, every
termination/authentication guard, long output, rollback after FINISH and
continued dispatch past a younger premise HOLD. `test_round2_stack.py` applies
#109 then #108, loads both actual controllers, checks review routing and shared
terminal policy, and exercises the real installer CLI's mismatch, plan and
apply/readback/rollback paths. The historical source receipts are only read;
fixture provenance lists their original hashes and the sanitization rule.
The advisory refreshes even when history exceeds its 200-reservation or
20-HOLD input budget, reporting the explicit bounded-history limitation.

The fresh source precheck found two issues on retained head `35d6c5a`:
unchecked Python bytecode could execute after a helper source hash check, and
authenticated terminal originals still blocked younger certificate visibility.
The installer now uses only standard-library utilities and executes captured,
checked terminal-helper source bytes in a fresh module and rechecks its complete input closure before writes. Review evidence
also binds `INTEGRATION_BINDING.json`. Canonical certificate visibility omits
only freshly reauthenticated #109 terminal-original entries; pending and rejected
requests still block it. Original checkpoint targets/debt and the general
publication-prefix API remain unchanged. Named cache substitution, source-CAS,
real-drain visibility and terminal-recheck tests accompany these fixes.

`run_precheck_mutations.py` isolates six cause-specific named tests. Each baseline passes and its semantic mutant must fail by assertion with zero errors; broad-suite errors are retained separately and never constitute a kill.
