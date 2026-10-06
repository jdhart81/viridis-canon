# Protected implementation integrity log

## 2026-10-03 — FOUNDATION F2d

Justin explicitly approved: "raise the --timeout upper bound from 300 to 1800 seconds. Keep the default at 300. Keep the SSH wall clock = timeout + 60. No other change to verification logic, identity checks, kernels, axioms, hashing or receipt format."

Client SHA-256: `121debeb61ca1c456002413e57a3667e75427a24e849706805bd74568f93fa2a` → `04b51c869205a66c452241bffce76945c2b735cf90cae15c645fdbadb2f7a606`.

The runtime client was previously unversioned in the canonical pipeline. This PR imports its authoritative source with exactly two line changes: the bound and corresponding rejection message. The imported alignment and observation dependencies are byte-identical to runtime; they are not modifications or replacement verifiers. The issuer and backend remain unchanged and their current hashes are recorded in the new protected baseline. Historical baseline receipts remain immutable.

Timeout governs how long the client waits for the same remote result, not what is verified. A longer wait does not relax any proof or receipt checks. Default wait remains 300 seconds; transport allowance remains timeout + 60. Receipt schema and content are unchanged; the timeout value is recorded in the attempt log, not added to the receipt.

After merge, install only the new client bytes at the canonical runtime path, verify the new hash, then submit Run-900 v007 with timeout 1200. No droplet code, pins, issuer, aligner, backend, publication enforcement or Zenodo metadata change is authorized here.

## 2026-10-03 — FOUNDATION F2f, commit 1

Justin explicitly approved diagnostics-only client capture per F2E_DIAGNOSIS.md section 5. Client SHA-256: `04b51c869205a66c452241bffce76945c2b735cf90cae15c645fdbadb2f7a606` → `f76bcb501b252aa111a4910d54a7ac06259e543fe083ef3f8523bf436ac80ab4`. The entire `verify()` function source remains byte-identical; a transparent decorator binds its known output directory for transport diagnostics. Raw subprocess bytes are captured before equivalent text decoding. Failure evidence is private, capped at 1 MiB/stream and hash-bound, with incomplete captures identified. No stdin, key or environment is logged. Diagnostics never enter receipts or issuer evidence. Defaults and wait bounds remain unchanged.

The pre-diagnostics client and unchanged issuer are pinned test-only fixtures for source-byte, receipt and issuer-output equivalence checks; they are never production routes. Raw diagnostic directories are excluded from Git and export archives. A logging failure cannot mask the original transport decision. Historical baselines and attempts remain immutable.

## 2026-10-03 — FOUNDATION F2f, commit 2

Justin separately approved repair of the delivery wrapper per F2E_DIAGNOSIS.md section 4. `/usr/local/bin/viridis-comparator-verify` SHA-256: `b448e91bd4f5389f19358e21cb7f9c7b23e4be89d2ff79343bdb0d0ba63a09d9` → `245e5f053e5d3c5276da528ed2a82e7a07e2b0046135dc2362cfa8816bf3d4cb`. The previously unversioned authoritative wrapper is imported with delivery-only changes. One /start reserves the request, one /track enqueues, every line checks its bounded deadline, then same-ID /result polls run until terminal or the 1200-second operation deadline. Stream interval is 30 seconds and poll interval 2 seconds. Pending is not success. Disk-cache delivery is rejected; existing client identity, kernels, source hashing, observation policy and issuer acceptance are unchanged. Exactly one JSON object is emitted on stdout; delivery diagnostics go to stderr.

Deploy only after this PR merges, verify the old hash immediately before deployment and the exact new hash afterward. No service restart, service code, worker, toolchain or key changes. The client's approved 1200-second wait retains a 1260-second SSH allowance. The wrapper is the only approved remote file change.

## 2026-10-03 — FOUNDATION F2h deployed drift reconciliation approval

Justin explicitly approved the foundation-only resource profile, diagnostic receipt fields and deployed-script snapshots. Every deployed launcher, delivery wrapper, source component and service fragment/drop-in was snapshotted with SHA-256 before change; see F2H_DRIFT_RECONCILIATION.md and the protected baseline `deployed_pre_f2h_sha256`. Deployed bytes are the pre-change operational authority. No droplet changes in this commit.

## FOUNDATION F2h — foundational resource profile

Approved by Justin: only Run-900–999 may select a 600-second comparator wall allowance. Nightly/default, compile/collection guards remain 285 seconds; deployed launchers and service limits remain byte-identical. Source-run routing is derived from the frozen request outside the byte-identical client verify() function; the server schema and worker both reject a nightly foundational selection. In-flight routing is partitioned by run/profile. Old hashes are in deployed_pre_f2h_sha256 and the previous commit; new hashes are in protected_remote_implementation_sha256. The profile is recorded in provider receipts as non-acceptance metadata.

## FOUNDATION F2h — subprocess receipt diagnostics

Approved by Justin: preserve actual close-event exit code/signal, reached phase and elapsed seconds for pass and fail, with deadline-fired attribution. Diagnostic metadata is never evidence of acceptance. Core worker verification and client verify() remain byte-identical; the original spawnPromise nonzero rejection is unchanged. Queue failures report unavailable/null comparator accounting. Old→new source hashes are bound by the deployed snapshot and protected remote baseline. No launcher, kernel, issuer, aligner, backend or service configuration change. Deployment requires merged review and before/after hash readback.

### F2h exact protected hash transitions

| Component | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `/usr/local/bin/viridis-comparator-verify` | `245e5f053e5d3c5276da528ed2a82e7a07e2b0046135dc2362cfa8816bf3d4cb` | `9e7a384df16c4c80170ff117f63e90cae09b7f923dbf3296ed36158bd1126f02` |
| `/opt/viridis/comparator-live/server/src/exec.ts` | `1d87221a644df128b73011e45bc28391558d802d7ca7645a3919a9adcbfed607` | `c6282bc7ee10a9d8717c22892beb24d239e7129331df47cc7c07379c19cb9941` |
| `/opt/viridis/comparator-live/server/src/worker.ts` | `2d288baedf40cc718f42417c99c3a1dc3788f36c6fead05a150837bd84e41cdc` | `6ed027bef98e254ba181587c156bff9e5ce9ab0d29f66a265f2c6561b3862448` |
| `/opt/viridis/comparator-live/shared/shared.ts` | `93e84d5060d34724ca79a2512a18d97903c3ee26bbe35249ddd811621a6fa055` | `70922cfc75b6cc24d2d8bb102dcb405aaed9baf57fd14261d86482f99dc3808a` |
| `/opt/viridis/comparator-live/server/src/resource-profile.mjs` | `ABSENT (new operational module)` | `a399885225e15ddb896294ab135d777a8d56727d31fa5fb3976b1f1e02cc88fc` |
| `/opt/viridis/comparator-live/server/src/app.ts` | `a6ed0b0712154b0ce94f241ee445f6428c94ca8d90769ef05701acb34a857ae2` | `9a11661de61ab1c2d0941b5c32d2b5e179d6cb17c48440f823dae5b6f8c536ed` |
| Client | `f76bcb501b252aa111a4910d54a7ac06259e543fe083ef3f8523bf436ac80ab4` | `b745e90ad147a0d5bd6787e20049e9bbb49a694837172851c77958b271718202` |

Client verify() acceptance-function SHA-256: `4ede83be9b0a083c1b5107ceb7ac33a4cc0616fe7bf9cc5069d4bb472390ad43`, unchanged.

## 2026-10-04 — INV-9 protected issuer intake approval

Justin explicitly approved new-nightly premise-declaration intake in GAME_PLAN.md, section “Premise-declaration gate (INV-9) — 2026-10-04”. The authoritative unversioned production issuer was imported first with SHA-256 `789cb903c972a9c10731360769ccff56055b3257de9491a75b92c0d549b5c438`; the approved intake revision is `96c5c70d7d9de31c537ac4dc4a405d5f2c38a7ba03389c93dac1efb28cfc5ebe`. The new explicit `--require-premise-declaration` flag checks the four already hash-bound sealed inputs and records `foundation_basis` plus its static intake report in the certificate. Default remains off for historical callers; the entire existing proof/receipt/kernel/axiom/alignment/hash acceptance block and witness-evidence helper remain byte-identical. Tests compare historical certificate output byte-for-byte and preserve all prior proof rejections. No verifier, kernel, permitted-axiom list, alignment implementation, proof source or existing certificate changes. Runtime installation is deferred to the merged, hash-checked Phase 5 closure.

## 2026-10-04 — already deployed F2G overlay baseline reconciliation

The protected remote baseline still listed pre-overlay hashes. This entry reconciles it to previously merged release `b84f62a84bc2ee4a5c94453d4d00edf584a250b3`, not a new deployment or protected-code change. Authority: `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/2026-10-03/foundation-f2g-cold-retry-20261004T001801Z/evidence/DEPLOYMENT_STATUS.json` (SHA-256 `cfd4068c2e31f2d7b65c40942ca57947ee1c81424ce489782d2406446f80bbd1`) and `checkpoints/F2G_OVERLAY_MANIFEST.json` (SHA-256 `534582acd73e893d14aa70413e24da907e39109e8ced91619d880e43e7abd3de`). Every local overlay source matches its previously recorded release hash. A fresh read-only deployed hash probe is recorded separately by the parent task.

| Deployed component | Prior baseline SHA-256 | Already deployed SHA-256 |
| --- | --- | --- |
| `/opt/viridis/comparator-live/server/src/app.ts` | `9a11661de61ab1c2d0941b5c32d2b5e179d6cb17c48440f823dae5b6f8c536ed` | `b8bdfe6cee8f334f13be3f8315533d08eda3a59161cd0e51dfc14daec3340701` |
| `/opt/viridis/comparator-live/server/src/exec.ts` | `c6282bc7ee10a9d8717c22892beb24d239e7129331df47cc7c07379c19cb9941` | `d3cef70035b949f13a811013530a3e6e22d3434b5699b11f844591081fa853d2` |
| `/opt/viridis/comparator-live/server/src/worker.ts` | `6ed027bef98e254ba181587c156bff9e5ce9ab0d29f66a265f2c6561b3862448` | `d370bf959992234c92d35540149be1dfda74d9d825006076fd0ba8ac0514a305` |
| `/opt/viridis/comparator-live/server/src/resource-profile.mjs` | `a399885225e15ddb896294ab135d777a8d56727d31fa5fb3976b1f1e02cc88fc` | `a506ea2f0b5edf1dce5b0e526804b285e261db8c296d593b4725523ed78e3c88` |
| `/opt/viridis/comparator-live/server/src/resource-profile.d.mts` | `ABSENT` | `bb22f5f88f7d8c2d16541bb01889f7b0d5f822ed4db55c64339f632e2aad5ef4` |
| `/opt/viridis/comparator-live/server/src/guarded-process.mjs` | `ABSENT` | `544ac5bfb3ca631e7cb3fb5aef531efca4d83a9cbb98c818125b10dbffe83015` |
| `/opt/viridis/comparator-live/server/src/guarded-process.d.mts` | `ABSENT` | `9e83fd6a1728ad6907b734960d0cec3b80cdba39f952ef5a48e60155ec06cfed` |
| `/opt/viridis/comparator-live/shared/shared.ts` | `70922cfc75b6cc24d2d8bb102dcb405aaed9baf57fd14261d86482f99dc3808a` | `a3fe5a7596e0fd546dd53bc6b6bbc504ea21463605ffbff2efd5f9a12f3f6dc7` |
