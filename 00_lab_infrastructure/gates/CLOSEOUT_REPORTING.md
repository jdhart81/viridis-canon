# Completion evidence and nightly closeout reporting

The approved `GAME_PLAN.md` close-out decisions dated 2026-10-06 require durable
completion evidence, seven genuine consecutive clean nightly windows, and quiet
reporting between failures, the weekly ledger report, and 7/7.

`completion_links.py` rejects a completion report unless every rendered evidence
link resolves to a regular file inside the canonical Cowork tree, including
after symlink resolution. Historical temporary evidence must first be copied
byte-for-byte into that tree and hash-checked before report links are rewritten.

`closeout_streak.py` is a receipt consumer. It imports the exact installed
`nightly_coverage.py` with SHA-256
`d25e051fe9d2d4e6da04d46cd16d18a101ac4ae2fee49f38596ab2ce04926ea9`.
Every clean window uses that unchanged guard's checkpoint and science gates.
An explicit HOLD can only be anchored to its immutable START/FINISH, activation
and coverage bindings as a dated failure. It receives no clean credit; later
consecutive clean windows can recover. Unknown or damaged enforcing evidence
remains fail-closed. A day with both clean and failed reports is failed.

The consumer scans all saved cycle reports, preserves original streak receipts,
and writes separately named `CLOSEOUT_STREAK_REPORT.json` receipts. `--weekly`
uses an authentic current-week checkpoint and pinned ledger to produce the
existing immutable weekly report. A weekly snapshot is not nightly clean credit.
The consumer neither executes Lean nor issues certificates nor publishes.

Install this reporting consumer alongside the existing canonical guard after
this PR's checks pass. The 22 runtime authority targets and their activation
receipt remain unchanged. Update the existing scheduler's reporting instructions
only: no duplicate generator or checkpoint, no quiet-window user message, one
failure message per newly failed closed nightly window, and one weekly report.
At 7/7 regenerate the completion report using durable canonical links; the
separate final Claude audit must actually pass before declaring completion.

Validation: the repository's gate suite includes 39 completion-link containment
tests and 36 closeout tests. These cover genuine recovery after a failed window,
missing dates, duplicate/open windows, negative-only HOLD anchoring, tampered
receipt chains, substituted guards and unknown enforcement evidence.
