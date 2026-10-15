# Engine liveness: reviewed installation candidate

Run-170's writer exits 2 because its sealed manuscript says independent review
is pending while its package has a passing review. The writer correctly holds.
The executor previously discarded the writer's stdout JSON and showed empty
stderr. `G1_CONTROLLER_EXECUTOR.patch` makes that HOLD identifier visible
without copying untrusted diagnostic prose, and sends the sealed-paper conflict
to agent judgment for a versioned successor and later review. It never changes
the sealed paper, certificate or existing kernel package.

The installed-source hashes in `INTEGRATION_BINDING.json` bind the patch to the
diagnosed controller and executor. Apply only after this PR is independently
reviewed, merged by Justin and green. Install `scheduler_liveness.py` beside
those two files, apply the zero-context patch with `git apply --unidiff-zero`,
and verify the expected after hashes. Record the installation
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
   hash and every exact identity, recomputes the unchanged source-observation
   validator and requires terminal process evidence plus the real failing goal.
   It preserves the request and never authorizes a new attempt.
3. On acceptance, use the existing issuer and its complete certificate
   validator, then call `accept` with the exact identity, artifact hashes and
   genuine kernel/premise/non-vacuity results. The supplied validator must
   validate the real certificate, proof and provider receipt; a boolean claimed
   by the caller is insufficient production evidence. Results are exclusive,
   immutable holding-area records and do not grant checkpoint target credit.
4. Pass only release objects that cleared **every** existing science, review,
   packaging and authority gate to `publication_prefix`. It returns the
   contiguous admitted prefix of the caller's authoritative release order.
   A terminal original can be omitted from release membership only by the
   existing reviewed successor or held-Run policy, never by this library.
5. Use `scheduler_checkpoint` at the existing scheduler call site so generation
   runs once when `generation.due` is true before certification HOLD handling.
   It adds no generation cadence, model, budget or additional checkpoint.

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
