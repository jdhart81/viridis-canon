# One selected runtime source, immutable history

The selected source is `future_runtime_v012/`. Its V012 semantic labels,
canonical Git namespace, nineteen source modules, outer guard, installed-path
requirements and existing failed-health provenance are unchanged. The retained
historical directory name is intentional: renaming it would change the exact
merged-source namespace required by its admission gates.

This is source consolidation, not installation or runtime admission. The
existing v2 digest controller/helper remains inside the selected source with
its original science, certificate, source-review, journal and public-readback
requirements. The independent reviewed installation and bounded sandbox
rehearsal gates remain required. No V013 behavior is promoted or repaired.

`RUNTIME_HISTORY.json` preserves all 505 original v001–v012 merge/tree/blob
rows and adds the 59 exact v013 rows at their existing merge. The unselected
v001–v011 and v013 directories live in Git history. Planned v001–v012 tag names
are proposals; this change does not create tags. V013 remains an unselected
historical successor, including its original tests and diagnostics.

`common/runtime_history.py` supplies exact local Git bytes to the retained
predecessor tests. It checks the version tree, commit path, regular blob mode
and blob identity. It never extracts an old runtime, imports historical source
as a module, starts network traffic or supplies an admission result. Existing
tests may still execute their original scoped AST fixtures in their original
synthetic contexts. Only their storage lookup changed; the expected hashes and
functional assertions remain intact.

The selected runtime retains its 387 existing tests. CI runs that functional
suite once per Python version and separately checks all 564 historical blob
bindings. It does not re-run thirteen largely duplicated runtime trees. The
source consolidation does not claim that unselected V013 behavior passed, or
that source tests establish a successful production health check.

No active production module is moved into `common/`: the selected source has
no byte-identical duplicate among the outer modules, and forced extraction
would change its pinned source bytes. Future shared code requires its own
reviewed source change. The common folder currently contains the narrowly
shared test-source provider.

Installed Core directories and bulk session evidence remain untouched. Their
later archival requires genuine shared-writer/source exit and verified
reference migration, followed by the authorized archive verification and
targeted removal transaction.
