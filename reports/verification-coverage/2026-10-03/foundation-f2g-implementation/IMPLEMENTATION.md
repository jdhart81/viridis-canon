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

Implementation: comparator-deploy/service-profile/README.md describes the
hash-bound review overlay. Only exec.ts/worker.ts are patched; four module/type
files are registered for a future separately approved application. No automatic
remote application is included. Exact source hashes and validation results are
in VERIFICATION.json and service-profile/BASELINE.json.

Validation: 149 local Python gate tests; 14 fake-process tests; full server
TypeScript check; patch application against the captured source; offline exact
approved-input/project-observation match and changed-byte refusal; strict
termination schema; zero secret findings. No existing assertion was modified
except the explicitly requested limit test, retained under its original name in
the PR's acceptance suite. It now checks the unchanged nightly/default promise,
explicit foundation limit, phase-budget isolation and forged-profile rejection. The
local authoritative test/runtime files are not installed from this PR.

The client verify() acceptance source is byte-identical, and its entire file
hash is unchanged. The issuer fixture exactly matches the protected canonical
issuer hash. Existing missing-marker/export/witness, wrong project/hash,
forbidden construct/axiom, observation, sealed-paper drift and issuance gates
remain fail-closed. Optional diagnostics preserve scientific success checks and
same-request/cache delivery rules.

No droplet contact, write, restart, resource resize, certification submission,
v008 rerun, certificate promotion, merge or deployment. STOP for Justin review.
