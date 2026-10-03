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
