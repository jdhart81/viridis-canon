# F2g droplet deployment checkpoint — prepared, not executed

Status: WAITING_FOR_JUSTIN_GO. #43 merged at
`8b7ca7281eb76c95f7df8597771ef73ffe963ca8` after every CI job that ran passed.
Justin merged #44; the final merged release on main is
`b84f62a84bc2ee4a5c94453d4d00edf584a250b3`. The overlay archive was built locally on the Mac
from the eight exact Git blobs in that commit, not from uncommitted files.

- Archive: `f2g-overlay-b84f62a84bc2ee4a5c94453d4d00edf584a250b3.tar.gz`
- Archive SHA256: `8c850a9f2273de39eedb6b07d983095cbf5fe8057db7e42e7721b9537ce3e9fb`
- Compressed size: 12032 bytes; eight regular files, no extra members.
- All eight file SHA256 values in F2G_OVERLAY_MANIFEST.json match the commit.
- Archive readback confirms every native destination's bytes match that commit.
- Two local builds are byte-identical. Recipe: sorted native destinations,
  USTAR mode 0644, uid/gid/mtime 0 and empty owner names; gzip level 9 with
  mtime 0 and empty filename. Archive metadata is not deployment ownership.

The archive is retained on the Mac in the local evidence report folder
`reports/verification-coverage/2026-10-03/foundation-f2g-release/`.
This record PR changes documentation only; the deployed code candidate remains
that exact #44 merge commit. Justin's separate deployment go is still required.
No droplet contact, backup, installation, restart or certification submission
has been performed in preparing this checkpoint.

## Authorization and scope

Justin's deployment go must identify the final merged release and this plan.
It covers the Comparator service source overlay, one controlled Comparator-only
restart, health/readback/watch and restoring the prior source if health fails.
It does not authorize a proof submission, a v008 rerun, certificate issuance,
changing any resource limit, toolchain, project policy, wrapper, secrets,
scheduler, service unit, dependencies or unrelated service. A fresh source
mismatch stops the attempt; it does not authorize overwriting drift.

This is the native systemd Comparator, not the Fleet gateway container.
The 2026-10-03 snapshot identifies viridis-comparator.service, working directory
/opt/viridis/comparator-live, loopback port 3100 and project root
/opt/viridis/comparator-projects. These are historical coordinates to verify,
not a fresh live inspection. Do not hardcode a remembered IP or reuse a Fleet
Docker/Engine API deployment procedure.

## 1. Preflight after go, before any mutation

Resolve the intended certifier host through the existing approved connection.
Confirm hostname, service MainPID/start time, active state, ExecStart,
WorkingDirectory and resolved release layout. Read only named public source
hashes and selected nonsecret service properties; never dump the environment.
Capture loopback GET /comparator/api/health, GET /comparator/api/projects and
GET /comparator/api/metrics.prom; establish an empty queue and no running job.
If work is active or arrives before the restart, stop and wait for a quiet
window; do not cancel or resubmit it or disable a scheduler.

Record the effective MemoryMax, CPUQuota, TasksMax and process limits, plus
cgroup identity, memory.events, memory.peak, swap counters and restart count.
Snapshot effective values include MemoryMax=7864320000 and CPUQuota=400%; the
unit's 3G/180% values are overridden by control drop-ins. Confirm, do not change.
Hash the comparator/compile/collection scripts, wrapper, bootstrap, public
source modules, package/lock metadata and project manifest/toolchain. Verify
CPU ulimit 600 and toolchain/project pins. Acceptance/issuer hashes must match
the final protected baseline. No Lean, Lake, Elan or comparator job is run.

Reconcile the fresh source against deployed_snapshots/F2h-20261003, approved
#42/#43 and the merged follow-up. Preserve any already deployed reviewed
change. service-profile/service.patch binds repository main before #43, not
necessarily the deployed tree, and places shared.ts under a review-only path:
DO NOT apply that patch blindly. The real shared package target is
/opt/viridis/comparator-live/shared/shared.ts. Resolve its package mapping and
confirm it before staging. New unexplained drift is a hard stop and requires
an updated reviewed overlay, not an edit to force a gate to pass.

## 2. Backup and restore gate

Create a timestamped private source backup on the host only after go. Include
all existing destinations in the overlay allowlist, recording absent files
explicitly, plus source metadata, ownership/modes, original release pointer or
directory layout and selected nonsecret service settings. Back up bootstrap
and package/lock metadata for unchanged-byte comparison. Do not archive
credential files or raw environment values. Preserve all historical source
snapshots and immutable request/receipt/certificate artifacts.

Preserve /var/lib/viridis-lean/terminal-results and result-cache in place.
Take a consistent, access-restricted durable-store backup using the existing
approved storage procedure, with a file manifest and hashes; no new SQLite or
database format is presumed. Do not read/log proof payloads or credentials.
If no safe consistent backup procedure exists for the current live layout,
stop rather than inventing an online copy of a mutating store. Do not remove,
recreate, clear or overwrite those stores for installation or rollback.

Verify source and durable-store backup archive SHA256, copy off-host through
the existing approved channel, and compare both hashes. Backup destinations
are chosen at go; no forbidden workspace backup directory is inspected by
this preparation. Restore the source archive in an isolated scratch directory
and compare every original hash, mode and absent-file marker. Restore durable
state only into isolated scratch and verify its manifest; never into live
state. Require a fresh backup for this deployment, not a historical backup.

## 3. Candidate overlay and offline checks

Build the source archive on the Mac from the final merged release; no droplet
build, package install, dependency upgrade or toolchain execution. Preserve
all untouched runtime/dependency/bootstrap bytes from the confirmed release.
The allowlist contains eight source/type files only:

| Repository candidate | Native release destination |
|---|---|
| remote_service/app.ts | server/src/app.ts |
| remote_service/exec.ts | server/src/exec.ts |
| remote_service/worker.ts | server/src/worker.ts |
| remote_service/resource-profile.mjs | server/src/resource-profile.mjs |
| remote_service/resource-profile.d.mts | server/src/resource-profile.d.mts |
| remote_service/guarded-process.mjs | server/src/guarded-process.mjs |
| remote_service/guarded-process.d.mts | server/src/guarded-process.d.mts |
| remote_service/shared.ts | shared/shared.ts |

Stage a sibling candidate release with the same ownership/modes and unchanged
bootstrap/dependency linkage; verify all eight overlay hashes and all protected
unchanged hashes. Do not edit the live tree in place. Confirm every import
resolves, including the shared schema and existing job-attestation modules.
Run the fixture regressions, full server typecheck and import/schema checks
locally against this exact assembled tree. Any scratch boot must use isolated
scratch state, mock work, loopback and no network access; it must not attach to
the production queue or compile/check a proof. Record the assembled archive
hash and the prior release hash as candidate/rollback identities.

Confirm default/nightly comparator guard 285s and client promise 300s;
compile/collection 285s; only exact approved source bytes, ordered exports and
server project pins select foundation comparator 600s. Caller labels/timeouts
cannot elevate it. Foundation remains within the existing 1200s wrapper.
CPU ulimit 600, MemoryMax, CPUQuota, toolchain and acceptance remain unchanged.
The error-without-pid-and-without-close fixture must reject immediately,
cancel its guard and emit one spawn_failed record with null code/signal.

## 4. Controlled activation, only after deployment go

Recheck the queue is idle and the backup gate is complete. Keep the prior
release intact. If the live path is a symlink, atomically switch its target to
the verified sibling release. If it is a directory, stop the Comparator alone,
rename the intact original to the recorded prior path and place the candidate
at the original path before starting it. Do not improvise a layout migration;
record the selected reversible procedure during preflight. No unit/drop-in,
wrapper, environment or cgroup setting changes. No daemon-reload is needed.
Restart/start viridis-comparator.service once and record its new PID/start time.
Do not restart anything else. No POST to a verification/admission endpoint.

## 5. Readback and health acceptance

Require active service, fresh PID, no restart loop and clean startup journal
(no raw payload capture). Rehash the eight destinations, unchanged scripts,
wrapper/bootstrap, project/toolchain and effective resource settings. Require
health HTTP 200, the same supported project inventory and idle queue.
Existing v005 and v008 terminal files must still resolve at their recorded
paths with unchanged hashes; where the existing result GET exposes them,
require the historical response still resolves. Never create a new request to
check an old terminal record, and never relabel the failed v008 result.

Watch 15 minutes with GET-only health/metrics and journal checks. Record health
at start, periodic intervals and end, restart count, memory/swap and cgroup
identity/counters. Cgroup counters may reset on restart; do not compare counts
across different cgroup identities as a lifetime delta. Other service identities
and start times stay unchanged. This proves installation/readiness only, not
successful foundational verification or receipt issuance in a live proof run.
Live subprocess diagnostics and the new allowance remain unexercised until a
separate certification/rerun authorization.

## 6. Rollback and final checkpoint

Any failed import, hash, health, unexpected resource/unit drift, missing
historical terminal, or restart loop triggers Comparator-only source rollback.
Restore the recorded prior release pointer/directory, retain the candidate for
diagnosis and restart only the Comparator. Preserve both source archives and
all terminal/results/cache state; never restore old durable state over live
state or delete new receipts. Confirm prior hashes, health, project inventory,
historical terminal resolution and unchanged settings. Stop with exact failure
evidence if rollback cannot restore health. No automatic retry or proof run.

After a healthy 15-minute watch, report candidate and rollback identities,
backup SHA256 on both hosts, overlay/unchanged hash readbacks, service health,
watch evidence and explicit zero proof submissions / zero v008 reruns. Stop
for Justin's separate go on any certification attempt. Today remains
WAITING_FOR_JUSTIN_GO: all actions above are a checkpoint plan, not execution.

## #43 CI exceptions (verified from the final PR check results)

The final #43 head was 442ab5e66189df99d96683053ba1acf800617cd7.
Nine reported checks succeeded; these three jobs were skipped by workflow
conditions rather than executed:

| Job | Workflow | Reason |
|---|---|---|
| dco | DCO | Only fork contributions run this job; #43 came from a branch in jdhart81/viridis-canon. Condition: head repository must differ from github.repository. |
| deploy-pages | research-catalog-and-pages | Requires a non-PR event on refs/heads/main; #43 was a pull_request event. |
| release-bundle | viridis-os-bundle | Requires a refs/tags/v tag or release event; #43 was neither. |

No final #43 check was pending, cancelled, failed or otherwise unexecuted
besides those three skips. This describes the PR head checks, not a claim
that Pages publication or release publication occurred. Workflow conditions
are recorded in .github/workflows/dco.yml, research-portal.yml and os-bundle.yml.
