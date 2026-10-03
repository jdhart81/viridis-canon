# FOUNDATION F2g — profile and terminal diagnostics PR

The approved Run-900 wire request alone receives a server-selected 600-second
comparator wall guard. Project ID, exact Challenge/Solution hashes and ordered
wire exports must match the allowlist; the server-selected project manifest and
toolchain file hashes must also match the captured approved policy. Caller
profile/timeout/hash fields cannot grant this allowance. Default/nightly client
wait remains 300 seconds and its existing stage guards remain 285 seconds;
foundation has the explicit 1200-second wait and 600-second comparator guard.
Compile/collection guards, CPU ulimit 600, MemoryMax, toolchain, wrapper, client
acceptance and issuer source are unchanged. The foundation operation clamp
reserves delivery time inside the existing 1200-second wrapper.

The terminal extension records phase/request identity, timing, actual code and
signal, guard reason, selected policy/limits and accounting availability. CPU and
RSS are explicitly unavailable; parent/service aggregates are never presented
as per-process measurements. Signal termination retains exitCode null. Failure
or guard-fired execution cannot produce verification-ok or a certificate,
even with forged kernel markers or fake exit zero. No arguments, payloads,
environment or raw error messages enter the new diagnostics.

Implementation: the canonical candidate is comparator-deploy/remote_service.
This PR is rebased onto main 7b08c5a418a27372ca3539574e989d8175dccd81,
which includes concurrently merged #42. It replaces caller-selected Run-900–999
budget elevation with the authorized exact-input/server-project allowlist.
The existing doUncachedWork scientific acceptance body stays byte-identical;
only its launcher and enclosing diagnostic wrapper change. Shared terminal
schemas register the new extension; queue failure reports unavailable metadata.
BASELINE.json and service.patch bind the merged source, not the live droplet.
No automatic remote application is included.

Validation: 157 local Python gate tests; 14 fake-process tests; full server
TypeScript check (scratch paths resolve the candidate shared package); local
patch replay; offline exact approved-input/project-observation match and
changed-byte refusal; strict diagnostic schema; zero secret findings.
The named five-minute test is retained and rewritten as expressly authorized.

Merged #42 operational test expectations updated for the authorized rule:
- Run-900–999 plus caller resourceProfile -> foundation: now default unless
  actual approved bytes, ordered exports and trusted server pins match. Caller
  labels never authorize elevated limits; unrelated labels are ignored.
- Old spawnPromise source-string assertions -> guarded launcher delegation,
  unchanged compile/collection/default guards, and unchanged script bytes.
- Reconstructed old/new launcher comparison -> the exact current guarded
  launcher, with distinct 0/nonzero/SIGXCPU/SIGKILL, guard-fired fake zero,
  group/fallback kill, unavailable accounting and capture-failure regressions.
These tighten operational tests. Scientific acceptance and issuer assertions,
including the unchanged doUncachedWork body assertion, remain intact.
The new full-client hash regression pins the rebased main b745e90a baseline;
its acceptance-function hash remains the original 5588b110 baseline. #42's
client metadata changes are in main, not authored by this PR.

The client verify() acceptance source is byte-identical, and its entire file
hash is unchanged. The issuer fixture exactly matches the protected canonical
issuer hash. Existing missing-marker/export/witness, wrong project/hash,
forbidden construct/axiom, observation, sealed-paper drift and issuance gates
remain fail-closed. Optional diagnostics preserve scientific success checks and
same-request/cache delivery rules.

No droplet contact, write, restart, resource resize, certification submission,
v008 rerun, certificate promotion, merge or deployment. STOP for Justin review.
