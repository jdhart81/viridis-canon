# Retained V012 adoption: source preparation, execution HOLD

The I9 patch is prospective. It changes no installed file, old seal, certificate,
scientific predicate, FIFO order or scheduler. The ordinary installer still
refuses an existing destination; no executable replacement mode is supplied.

The planning inventory is `adoption/EXPECTED_INSTALLED_V012_20261014.json`
(SHA-256 `5a84030f03d279896753568d85c2ad8e470b2bd389be9a4c43f48c5e3c1031d6`).
It binds the old 19 modules and three metadata files individually. Two additional
regular files (`INSTALL_RESULT_PENDING_READBACK.json` and
`PUBLISHER_UNCHANGED_BEFORE_INSTALL.py`) must also be archived. The shared helper
is currently absent. This read-only snapshot grants no source ownership.

A reviewed opt-in adoption mode must implement these exact transitions:

1. Require a new independently merged commit, successful required CI, its complete
   Git tree/blob proof for the 19 modules plus the fixed common helper, independent
   source/root review, a new exact installation plan, and a freshly approved
   publication configuration binding the new profile. Old configuration bytes
   stay immutable and cannot nominate the new profile accidentally.
2. Acquire the existing scheduler's acknowledged source handoff and exclusive
   whole-Cowork writer exclusion; prove all owned children are reaped. Compare the
   complete old directory inventory, every old22 hash/size/mode, both extra-file
   hashes, exact outer-guard bytes and shared-helper absence to the reviewed
   inventory. Unexpected files, links, changes or ownership uncertainty HOLD.
3. Before replacement, create one immutable archive outside the active directory
   containing all 24 old files. Retain an index mapping original paths to member
   names, SHA-256, size and mode. Reopen the archive, inspect its exact member set,
   hash every member and then hash the archive. Preserve old seals/receipts as
   bytes. No old runtime directory becomes another active version.
4. Stage the new reviewed 19 modules, exact common helper and newly encoded
   profile/plan/nomination at a private sibling path on the same filesystem. Bind
   metadata to final canonical paths; verify staged bytes against the merged
   blobs and reviewed plan without importing staged modules. Fsync files and
   parent directories. Record an exclusive transition journal binding old, new,
   archive and outer-guard hashes; no credential enters it.
5. A reviewed, platform-tested atomic directory-exchange adapter must swap the
   stage and retained V012 path while exclusion remains held. Ordinary two-rename
   replacement leaves a crash gap and is insufficient for an atomic claim. The
   outer default guard requires its own exact reviewed CAS. Do not enable
   dispatch until source-only readback verifies every new byte/profile relation.
6. On any post-exchange failure, exchange the retained old directory back and
   restore the exact old outer guard before releasing exclusion; verify all old
   hashes and retain the failed new tree as private evidence. Ambiguous crash
   journals HOLD for reconciliation; never infer success or retry a publication.
   No source-only adoption receipt establishes scientific or publication PASS.

Implementation remains HOLD because atomic exchange/recovery, archival proof and
an opt-in closed adoption-plan schema are not implemented or independently
reviewed. A second source issue precedes the requested small health path:
`runtime.session()` still reads 216 current/predecessor module paths plus 130
original source paths (at least 346 before metadata/data). Phase6's Git storage
consolidation does not remove that live dependency. A reviewed archive/Git-backed
predecessor proof must retain exact historical authority without opening every
old installed module before a <=200-file digest closure can be truthful. The
current full-population health is not an acceptable replacement.

Sandbox rehearsal also remains HOLD. The controller, catalog, journal validation
and DOI joins still require production host/namespace values. A reviewed config
base URL must select only production or sandbox, keep credentials/journals/SSOT
separate, reject cross-host redirects, and prevent 10.5072 sandbox DOIs from
entering real ledger/announcement state. The sandbox token is absent; no rehearsal,
production publication or live health was run.
