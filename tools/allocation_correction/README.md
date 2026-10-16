# Closed approved allocation correction

The original Run-177 and Run-183 proposals both reserve row 147. Justin's exact
linked correction approves Run-183 at 148 while preserving Run-177 at 147. The
installed router, candidate assembler and publication reconciler read only the
original proposals. This review bundle adds one shared effective projection
and three inactive patches so those consumers agree without replacing either
original or changing scientific evidence.

`PATCH_MANIFEST.json` binds the exact current predecessor, patch and resulting
source hashes. The `before/*.txt` files are immutable review snapshots. The
builder reproduces only repository patch artifacts; it has no CORE installation
or execution mode. All three resulting consumers load the same exact resolver
bytes from their sibling `effective_allocation.py`, verify the hash before
execution, reject linked paths and ignore ambient module imports and caches.

Normal installed calls need no allocation flags. The three patched consumers
use their CORE-root-relative `RESEARCH_PIPELINE_v2/finalized_runs/Run-183/`
`APPROVED_ALLOCATION_CORRECTION_20261016.json` at its compiled-in approved hash,
and capture a fresh root-ledger CAS before constructing the shared view. They
never search directories, read an environment override or infer authorization
from an unpinned file. The pure resolver still requires an explicit binding;
any Run-183 original without that binding HOLDs even if Run-177 disappears or
stops being READY. A missing or altered fixed overlay HOLDs normal calls.

For an explicitly pinned diagnostic invocation, all three options remain
available together (partial options HOLD):

```
--allocation-correction <exact Run-183 correction path>
--allocation-correction-sha256 <exact approved overlay hash>
--expected-ledger-sha256 <fresh exact root-ledger hash>
```

The resolver accepts only the approved 183 147→148 correction and the exact
planned local-binding companion, with their two authority bindings, original
177/183 proposal hashes and all six 183 scientific hashes. Unknown fields,
boolean rows, changed authority, science, identity, bytes or file frames,
symlink ancestry and reservation-set races HOLD. Row 148 must be absent or the
unique exact MCSL/Run-183 identity. Historical lower ledger rows remain intact;
ordinary global public/proposal reservation duplicates remain errors. Every
occupied effective proposal row must match its exact nightly Run and
abbreviation; unpublished rows also require the full title. Historical
published rows may retain their existing shortened title only with the exact
abbreviation, Run identity, published status and valid Zenodo DOI. Their bytes
are preserved. All numeric ledger rows contribute to the allocation maximum.

| Consumer | Result | Retained authority boundary |
| --- | --- | --- |
| Router | Reserves effective 148 and allocates the next free row | Existing independent science, non-spine and runtime classification gates |
| Assembler | Records original 147 and effective 148 with exact proof bindings | Rights and authoritative ledger row stay unassigned until separate existing binding authorization |
| Publication reconciler | Selects effective 148 for a separately verified publication receipt | Existing verified main receipt and authoritative ledger authorization still required |

Each consumer freezes JSON-safe receipts and serializes all output receipts
before its first local write. Real argparse `Path` arguments become strings in
the projection. The router removes only its exact owned route afterimage if
its second CAS fails; the assembler prepares all artifact and manifest bytes
before creating a directory and removes its own temporary tree on failure.
Late allocation failures use each consumer's normal HOLD type, so a racing
assembly records one per-run HOLD and the scan continues.

A staged bundle's source hashes bind only its scientific/package inputs.
Its separately recorded stable allocation receipt binds that same Run's
original proposal hash, effective row and relevant correction/authority facts;
its diagnostic global allocation input map remains separate. Unrelated ledger
edits or new proposals do not change this identity. Replays revalidate the new
global snapshot and compare the Run's allocation as well as its source hashes.
Unaffected legacy bundles can replay when the original proposal hash, license
and effective row match; an old Run-183 row147 cannot masquerade as148.

Each consumer revalidates its captured inputs before writing new local output.
The reconciler derives its ledger calculation from the captured bytes. Its
existing two separate writes remain separate: after an owned ledger write it
checks that exact afterimage and all other captured inputs before writing the
intake. A later HOLD requires reconciliation of any completed first write; it
does not imply rollback or a completed transaction. The resolver itself writes
nothing and grants no license, publication, promotion or scientific verdict.

The portable tests use synthetic science and authority bytes with explicitly
substituted test-local hashes, plus assertions of the unchanged production
pins. They apply every patch to temporary copies of the exact predecessor
snapshots and verify all resulting hashes. They never execute CORE source,
Lean, a publisher or a transport. Mutation tests refresh source pins and patch
hashes so stale admission hashes are not credited as behavioral kills; only
named assertion failures with zero unittest/infrastructure errors qualify.

Private ENGINE evidence preserves the historical prospective G-plan replay.
Round2 evidence also evaluates the actual current approved overlay, local
companion, both authorities, original proposals and scientific pins with this
owned pure read-only resolver. It confirms current ledger row148 has the
required nine-cell MCSL/nightly Run-183 identity and next allocation149. No
installed consumer is imported or executed, and this does not prove activated
consumer behavior or grant installation authority.

This code stays inactive until exact-head independent review, Justin's merge,
and a separate S4 installation with a fresh whole-workspace fence and CAS.
The installation must bind the merged resolver and all three resulting source
blobs to this manifest; it must not apply a patch to different predecessor
bytes. This PR does not install code, seal routes, publish, execute successors or merge main.
