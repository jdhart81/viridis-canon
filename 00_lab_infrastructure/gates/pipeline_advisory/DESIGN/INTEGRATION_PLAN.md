# Advisory integration proposal

The prepared linter and SLO collector run only on explicitly supplied files.
Neither changes the scheduler, issues certificates, sends proof requests,
decides generation.due, publishes, deploys, or alters FIFO predicates. Their
outputs say `certifies: false`. These files are not installed.

The Lean linter strips nested comments and strings, identifies ordinary local
definitions and simple theorem proof blocks, then flags pure algebraic tactics
that have not unfolded referenced local definitions. It also flags the Run-191
`rfl` reassociation pattern. It is a text heuristic with possible false positives
and incomplete Lean syntax coverage. Complex tactic syntax, explicit simp sets,
and unsupported proof structures remain UNASSESSED. A pass supplies preparation
guidance only; the Comparator remains the execution authority.

The SLO collector consumes a foundry-observer snapshot plus an explicit status
snapshot and as-of time. It reports source age and unavailable data, never
replaces a missing denominator or count with zero, and distinguishes a scoped
zero-hit token scan from unscanned files. New evidence is measured from a bounded
explicit file list; it performs no tree scan. The optional ten-line summary is
ready for a later reviewed hook in the existing Monday adoption snapshot.

No checkpoint or Monday hook is installed in this preparation.
`CHECKPOINT_SLO_HOOK.patch` binds the exact existing nightly source with before,
after and patch hashes. It observes freshly written START and FINISH receipts,
including FINISH replay, without changing the existing return codes. Its child
has a 15-second timeout; failure is advisory and controller output is discarded.
The hook reads at most five fixed source/data inputs plus 195 explicit footprint paths,
uses ctime-free stable reads, and writes only the derived
`RESEARCH_PIPELINE_v2/PIPELINE_SLO_STATUS.json` (at most 1 MiB). It does not edit
checkpoint receipts or scientific state. Missing supplied coverage, weekly or
leak results remain UNAVAILABLE. Production installation requires independent
merge, green CI, and refreshed source closure for the checkpoint and both hook
modules. Its isolated child hashes both exact source files before compiling
either; local module replacement prevents execution. Directory descriptors and
fresh ancestry checks prevent parent-link races from redirecting report writes.
The exact-source fixture test exercises BEGIN, FINISH and replay with
an advisory timeout and preserves both successful and held return codes.

`monday_summary` appends exactly ten science lines to an existing adoption
snapshot without changing its contents. The actual Monday owner/call site has
not been identified, so that integration remains HOLD; no automation is changed.
The linter's
weekly first-attempt rate uses America/New_York ISO weeks and exposes incomplete
attempt records separately from its known terminal-attempt denominator.

The CODEOWNERS and authorship files are reviewable patches. The ruleset proposal
is intentionally not an executable API update: A8 is unchecked, the current
ruleset must first be fetched, and unrelated rules and bypass settings must be
preserved. Proposed review fields follow the
[GitHub ruleset API](https://docs.github.com/en/rest/repos/rules). Existing owner
`jdhart81` is retained; no reviewer identity or permission is invented.
