# F2g resource and termination overlay — review only

This PR changes the **server launch policy and diagnostics only**. It does not
install anything, change the droplet, restart the service or submit a Comparator
job. Resource limits change the budget available for verification, not what is
verified. Review/merge is not deployment or permission to rerun v008.

## Server policy

The selector hashes the actual wire `challenge` and `solution` strings and
requires the fixed `viridis-lean-4.28` project plus the exact ordered export list.
`PROJECT_POLICY` binds the approved Run-900 bytes, toolchain and Mathlib policy.
The worker additionally reads/hashes the server-selected project
`lean-toolchain` and `lake-manifest.json`; their captured approved hashes must
match. Missing or drifted project files receive no elevated allowance. Neither
the project root nor these observations comes from the request.
The ordered wire list includes the three repeated witness entries emitted by
the unchanged client; the existing theorem selector still deduplicates them.
Changing a byte, project, order or export chooses the unchanged default profile.
Request `timeout`, `profile`, caller-supplied hashes or resource values are never
used for selection. There is no new API field granting a larger budget.

| Setting | Nightly/default | Approved Run-900 foundation |
|---|---:|---:|
| Policy client wait / default promise | 300 s | Explicit 1200 s |
| Comparator phase wall guard | 285 s | 600 s |
| Compile guard, each concurrent build | 285 s | 285 s |
| Theorem collection guard | 285 s | 285 s |
| Comparator CPU ulimit | 600 CPU-seconds | 600 CPU-seconds |
| Existing service MemoryMax | 7,864,320,000 bytes | Same |
| Existing delivery wrapper operation deadline | 1200 s | 1200 s |
| Toolchain | Lean 4.28.0 | Same |

Only foundation adds an operation-budget clamp: a phase gets the lesser of its
configured guard and remaining time from worker entry to 1185 seconds. The
existing wrapper ends delivery at 1200 seconds, leaving 15 seconds for cleanup
and delivery; a late/pending result remains HOLD. The default profile does not
add an aggregate timer or change existing stage guards. The protected client
still defaults to 300; its already-approved extended-wait API is unchanged.
The rewritten `test_five_minute_slo_rejects_longer_client_timeout` now tests that
300-second default promise, exact allowlist and explicit foundation limit
instead of treating any requested wait as server authority.

## Terminal diagnostics

`terminationDiagnostics` is an optional terminal-result extension under
`VRS-COMPARATOR-TERMINATION-1`. Each completed launcher close records phase,
requestId, UTC start/end, monotonic elapsed milliseconds, numeric exitCode or
null, actual signal or null, guard_fired, reason/guard reason, group/fallback
kill target, selected profile and limits. Both successful and failed stages are
recorded; failure before spawn has null code/signal and a distinct reason. The
existing combined process output cap and collection stdout callback are kept.

CPU and max RSS are **unavailable**, with null values and explicit reasons:
Node's ChildProcess exposes no per-child wait4/rusage accounting. Exporter,
nanoda are subprocesses internal to the comparator; Lean replay runs in the
comparator process. Their individual CPU/RSS values
cannot be inferred from parent, service or wall-time counters. No parent
`process.resourceUsage()` is substituted. No accounting service is enabled.
Profile CPU/MemoryMax fields describe the unchanged approved launcher/service
configuration, not measured CPU/RSS or a new cgroup write.

A failed/signaled/guard-fired phase rejects. The terminal decorator also refuses
verification-ok if any recorded phase failed, or diagnostic capture failed.
A guard-fired fake exit 0 cannot pass. Diagnostics never contain command
arguments, request bodies, environment, output payloads or raw error messages.
Capture failure fails closed without hiding a child failure. Terminal consumers
keep the extension in provider_response; the acceptance/issuer code is unchanged
and never treats a diagnostic field as kernel acceptance.

The existing scientific result, exports, axioms, observations, toolchain,
source/hash checks and certificate conditions are unchanged. Successful results
only gain optional diagnostics. Existing delivery/cache provenance rules are
unchanged; diagnostics do not authorize cache reuse or another request's result.
Completed phase records are distinguished from phases never reached. For a
compile failure, another already-running compile may close after the initial
failure result; missing records are not claimed as observed success.

## Reviewable application recipe (not executed on the droplet)

`service.patch` targets only `server/src/exec.ts` and `server/src/worker.ts`.
`BASELINE.json` binds both captured live inputs and candidate outputs. A future
separately approved application must verify the exact input hashes first, then
apply the context-free patch with `git apply --unidiff-zero` at the Comparator
source root and copy the four `.mjs`/`.d.mts`
source files from `src/` into `server/src/`. Do not apply against drifted source.
The comparator/compile/collection scripts, systemd unit, project/toolchain,
wrapper, client and issuer are not patched. No automatic apply/deploy script is
provided. The operator must preserve the existing server project policy/pins;
this PR is not a migration to another project.

## Validation

- Node fake-process regressions: exit 0, nonzero, SIGXCPU, SIGKILL, group kill and
  fallback, guard-fired exit 0, spawn failure, unchanged output cap, unavailable
  accounting, logging failure, exact binding and budget isolation.
- Python gates: scientific rejection fixtures, byte-identical acceptance and
  issuer hashes, killed terminal → HOLD → no certificate, unchanged success
  checks, and wrapper extension/cache/request identity compatibility.
- Local patch application and full server TypeScript check against the captured
  source and existing dependencies; no Lean/toolchain execution.

The public CI runs fixtures only. Local overlay/typecheck evidence and exact
source/input checks are recorded in the accompanying F2g implementation report.
A real resource test requires a separate future certification authorization.
