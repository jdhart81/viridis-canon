# Existing scheduler integration, inactive candidate

This integration adds two explicit actions on the existing `nightly_checkpoint.py`
entry point. `G2_EXISTING_CHECKPOINT.patch` adds
`--drain-certification START.json --certification-queue QUEUE.json` and
`--reconcile-certification START.json --certification-queue QUEUE.json`. It neither
creates a checkpoint nor runs generation. Existing `--begin`, `--finish`,
original START debt, enforcing coverage and source-exit semantics remain intact.
The scheduler performs the due-generation step first and always reaches its
existing finish path after any lane HOLD. Terminal originals stay sealed and
retain their original checkpoint target obligations.

After independent exact-head review, Justin's merge and green CI:

1. Apply both zero-context patches to the exact before hashes in
   `INTEGRATION_BINDING.json`; install the helper and adapter alongside the
   existing checkpoint. The bundled `job_observation_policy.py` is an exact,
   hash-bound copy of the unchanged installed pure validator, included for
   reproducible tests. Keep the already installed validator bytes unchanged.
2. Create a reviewed installation receipt inside the existing pipeline root.
   It records `merged_by: "Justin"`, `ci: "PASS"`, `independent_review: "PASS"`
   and the actual `installed_source_sha256` map. Its evidence must bind the
   real merged blobs, independent verdict, CI, installation and rollback.
3. Create `PARALLEL_CERTIFICATION_POLICY.json` beside the existing checkpoint
   with `standard: "VRS-PARALLEL-CERTIFY-ORDERED-PUBLISH-1"`, `active: true`,
   `max_in_flight: 2`, `scheduler_id: "viridis-nightly-science-generator"`,
   `reviewed_installation: {path, sha256}`, and the same actual
   `installed_source_sha256`. The source map must contain exactly:
   `nightly_checkpoint.py`, `checkpoint_certification_lane.py`,
   `scheduler_liveness.py`, `job_observation_policy.py`,
   `comparator_cloud_lean_verifier.py`, `issue_lean_zero_sorry_certificate.py`,
   `verification_coverage_gates/premise_declaration.py`, `checkpoint_advisory.py`,
   `pipeline_advisory/checkpoint_slo_hook.py`, `pipeline_advisory/pipeline_slo.py`
   and `pipeline_advisory/lean_repair_lint.py`.
4. Using the supported automation-update tool, insert the following operating
   paragraph into the existing generator prompt. Preserve every other field
   and all existing source-exit, ownership, generation and publication gates.
   The original prompt and other-field digests are bound in
   `INTEGRATION_BINDING.json`; refresh the proposal if those inputs drift.

> S8 PARALLEL CERTIFICATION, ORDERED PUBLICATION — After the existing due-generation
> step and the normal source-parity, authorization, scope and premise checks,
> prepare QUEUE.json inside this invocation's canonical checkpoint directory.
> Bind its exact original START SHA-256 and list every original START debt in
> its original order. For each debt, use the current reviewed immutable request,
> formal statement and candidate bindings and unused canonical receipt and
> certificate output paths. Bind any terminal premise HOLD by exact path/hash;
> it skips certification dispatch only, never original target credit or release
> admission. Run the same existing checkpoint entry point with
> `--drain-certification <original START.json> --certification-queue <QUEUE.json>`.
> Use no additional scheduler or transport. On an ambiguous reservation, reconcile
> its exact original request and never send again. A terminal rejection releases
> capacity only through `record_rejection`'s real receipt hash, unchanged source
> observation validator, exact identity, terminal process evidence and bound
> failing goal. Preserve rejected objects; no automatic repair attempt follows.
> Existing publication admission remains oldest-first and drains only the
> contiguous eligible prefix after every science, review, packaging and authority
> gate. Never count a younger acceptance toward either original named oldest
> target. Regardless of lane HOLD, finish the original checkpoint and its existing
> coverage flow, retaining exact incidents. Due generation remains independent.

`QUEUE.json` has `standard: "VRS-SCHEDULER-CERTIFICATION-QUEUE-1"`,
`start_sha256`, and `entries`. Each entry has `run_id`, the three exact
`{path, sha256}` objects `request`, `formal_statement`, `candidate`, absolute
`receipt_output` and `certificate_output` paths in that request's directory,
and optional `terminal_hold: {path, sha256}`. A terminal HOLD uses the existing
`VRS-CERTIFICATION-PREMISE-HOLD-1` form and binds that same request, statement
and candidate, the exact pure premise-checker source digest, and a fresh
non-certifying, no-local-Lean HOLD from that same pure checker. Manifest omission, reordering, path escape, existing fresh
outputs, identity drift, authority drift, source drift and premise failure
all HOLD before transport.

The adapter revalidates the unchanged egress authority and INV-9 preflight,
durably reserves at most two unresolved identities before calls to the unchanged
verifier. The private verifier/issuer calls run serially because those APIs do
not promise thread safety. It issues
only through the unchanged issuer with `require_premise_declaration=True`.
Acceptance writes the real issuer certificate only under
`parallel_certification/verified-results/<identity-key>/certificate.json`; its
immutable result binds the certificate, proof and cloud-receipt digests. Before
new transport, every accepted artifact is revalidated and compared with that
record. The adapter calls the ordered-prefix policy and exclusively links
only its contiguous verified prefix to canonical certificate paths. A younger
certificate remains invisible to the existing current-certificate ledger and
`nightly_release_checkpoint.source_for_cycle` until the oldest gap closes.
All later publication admission gates remain required. Resume reconciles the
original context and receipt without sending a reservation again; authenticated
terminal rejection releases a slot, ambiguity retains it, and a reviewed successor
request for the same Run has a distinct key. Every blocked queue entry has a HOLD.
Publication is never performed by the adapter. The original finish computes
its original target credit from actual current certificates.

The same source-bound checkpoint patch invokes `checkpoint_advisory.py` after
START/FINISH writes and their legitimate resumes, and after lane reconciliation/drain. This
isolated child has a 15-second maximum; stdout/stderr and exceptions never alter
the checkpoint's generation, certification, coverage or authorization result.
Install the three already reviewed PR106 advisory modules under the existing
pipeline's `pipeline_advisory/` directory and preserve the exact existing
`LEAN_REPAIR_PLAYBOOK.json` bytes pinned by the helper. It runs the advisory
Lean text linter on at most two explicitly named START/FINISH proof debts,
writes a derived per-checkpoint lint report, and invokes the bounded SLO
collector. Missing inputs or advisory errors produce explicit unavailable
status in `PIPELINE_SLO_STATUS.json`; unavailable values never become zero.
The FIFO report derives the named oldest debt from its hash-bound reservation
or recorded premise HOLD when no SLO input producer exists. It always includes
run_id, held_since_utc, failing_goal, candidate_sha256 and provider_receipt, with
explicit UNAVAILABLE values. It alerts at exactly 86,400 elapsed seconds; rounded
display hours cannot trigger an early alert. No Lean process, proof dispatch, publication,
schedule, model or budget is controlled by the advisory hook.

Rollback sets the policy active field to false first, then invokes the same
checkpoint entry point with `--reconcile-certification <original START.json>
--certification-queue <QUEUE.json>`. This validates the reviewed installed closure
and reconciles every reserved provider request through its original identity,
without transport, new reservation or canonical promotion. Preserve that closure
until reconciliation is complete; only then restore the before-source bytes. Keep all requests, accepted
results, rejection receipts and certificates. Restore checkpoint/controller/
executor before bytes from the installation snapshot and restore only the
generator prompt field through its supported update tool. No schedule, model,
budget, source seal, existing DOI or scientific bytes change.
