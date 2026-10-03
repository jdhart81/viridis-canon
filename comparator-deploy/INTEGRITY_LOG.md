# Protected implementation integrity log

## 2026-10-03 — FOUNDATION F2d

Justin explicitly approved: "raise the --timeout upper bound from 300 to 1800 seconds. Keep the default at 300. Keep the SSH wall clock = timeout + 60. No other change to verification logic, identity checks, kernels, axioms, hashing or receipt format."

Client SHA-256: `121debeb61ca1c456002413e57a3667e75427a24e849706805bd74568f93fa2a` → `04b51c869205a66c452241bffce76945c2b735cf90cae15c645fdbadb2f7a606`.

The runtime client was previously unversioned in the canonical pipeline. This PR imports its authoritative source with exactly two line changes: the bound and corresponding rejection message. The imported alignment and observation dependencies are byte-identical to runtime; they are not modifications or replacement verifiers. The issuer and backend remain unchanged and their current hashes are recorded in the new protected baseline. Historical baseline receipts remain immutable.

Timeout governs how long the client waits for the same remote result, not what is verified. A longer wait does not relax any proof or receipt checks. Default wait remains 300 seconds; transport allowance remains timeout + 60. Receipt schema and content are unchanged; the timeout value is recorded in the attempt log, not added to the receipt.

After merge, install only the new client bytes at the canonical runtime path, verify the new hash, then submit Run-900 v007 with timeout 1200. No droplet code, pins, issuer, aligner, backend, publication enforcement or Zenodo metadata change is authorized here.
