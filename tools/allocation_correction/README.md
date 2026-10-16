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

The caller must provide all three options explicitly:

```
--allocation-correction <exact Run-183 correction path>
--allocation-correction-sha256 <exact approved overlay hash>
--expected-ledger-sha256 <fresh exact root-ledger hash>
```

No environment variable or discovered overlay authorizes the projection. With
no explicit binding, the duplicate original 147 reservation continues to HOLD.
The resolver accepts only the approved 183 147→148 correction and the exact
planned local-binding companion, with their two authority bindings, original
177/183 proposal hashes and all six 183 scientific hashes. Unknown fields,
boolean rows, changed authority, science, identity, bytes or file frames,
symlink ancestry and reservation-set races HOLD. Row 148 must be absent or the
unique exact MCSL/Run-183 identity. Historical lower ledger rows remain intact;
ordinary global public/proposal reservation duplicates remain errors.

| Consumer | Result | Retained authority boundary |
| --- | --- | --- |
| Router | Reserves effective 148 and allocates the next free row | Existing independent science, non-spine and runtime classification gates |
| Assembler | Records original 147 and effective 148 with exact proof bindings | Rights and authoritative ledger row stay unassigned until separate existing binding authorization |
| Publication reconciler | Selects effective 148 for a separately verified publication receipt | Existing verified main receipt and authoritative ledger authorization still required |

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

A separate private ENGINE receipt evaluates the exact frozen G-plan bytes,
both real authorities, all 30 real scientific bindings and the actual current
three source hashes. Only the three prospective files (correction, local
companion and root-ledger afterimage) are supplied from that plan. This is a
prospective read-only result, not proof that those files are installed.

This code stays inactive until exact-head independent review, Justin's merge,
and a separate S4 installation with a fresh whole-workspace fence and CAS.
The installation must bind the merged resolver and all three resulting source
blobs to this manifest; it must not apply a patch to different predecessor
bytes. This PR does not install code, seal routes, publish, execute successors or merge main.
