## Phase 7 Gate 3 resolution: decouple probes from witnesses — 2026-10-07 (evening)

Evidence: `2026-10-07/phase7-approved-audit-execution-v001/PHASE7_REPORT.md`. Run-130 failed on the generated **triviality probe** `phase7_probe_S04` (whnf heartbeat timeout), not on a witness, theorem or premise. The root cause is my audit spec, which put downgrade-only probes in the same Comparator job as the publication-required witnesses, so one expensive probe can sink the evidence that publication needs. Correction:

1. **Two separate objects per run.**
   - **Witness bundle:** publication-required. Contains only the nonvacuity witness lemmas. Normal retry policy (max 2 retries, then Gate 3).
   - **Probe bundle:** informational, never blocks publication. Contains only the triviality probes. Each probe is its own declaration with its own `maxHeartbeats` budget.
2. **Probe outcome labels (honest, downgrade-only):**
   - A probe that closes the goal → `DEFINITIONAL` / `ROUTINE`.
   - An ordinary tactic failure on every probe → `SUBSTANTIVE`.
   - Any resource, timeout, depth, interruption or internal error → **`UNCLASSIFIED (probe resource-limited)`**. This is printed in the claim table. It never becomes SUBSTANTIVE, and it never blocks the note.
3. **Run-130.** The current probe object stays closed as HOLD under the retry policy, with no fourth attempt on it. Its claims are labeled `UNCLASSIFIED (probe resource-limited)` unless a later probe-only bundle under rule 2 resolves them. Run-130 gets a **new witness-only bundle**, a new object with its own normal budget. If that certifies, Run-130 proceeds to publication like the others. Codex's resource-aware refactor may be used for future probe bundles.
4. **The six certified Wave C bundles** (125/126 per report, 128, 129, 131, 134, 141) keep their certificates. Their probe labels stand.
5. **Integration fixes are mechanical and pre-authorized:**
   - Fix the 5 failing branch tests by adopting the new immutable snapshot closure and the INV-9 fixture. No assertion may be weakened.
   - Integrate the EVIDENCE_FIELDS adapter.
   - Resolve the empty-`custom_fields` conflict using the existing approved `legacy:communities` equality-to-existing rule.
   - Then go through PR → exact-head checks → merge → hash closure.
6. **Resume:** submit the 48 remaining runs as witness-only bundles. Probe bundles run in parallel or afterwards and are non-blocking. Publish the first Methods Digest as soon as its notes clear every publication gate.

---

## SIMPLIFICATION — weekly push restored — 2026-10-07 (Justin directive; supersedes conflicting Phase 7 items)

Justin's direction: the engine must keep its weekly publication cadence. The Phase 7 additions (per-claim witnesses, triviality probes, Gate 3 stops on optional evidence) turned an enrichment layer into a publication blocker. Claude accepts responsibility for that over-scoping.

### Minimal publication gate (the only blocking checks)
A note publishes in the weekly push iff:
1. **Certificate:** a valid existing Comparator certificate, including the issuer contract's own run-level `nonvacuity_obligations`.
2. **Scope:** the paper claims no more than the certified statements. Uncertified material sits in a labeled conjecture/remarks section (the narrowed v00x manuscripts already staged).
3. **INV-9:** foundation basis declared and passing.
4. **Binding:** PUBLICATION_BINDING at publish time; strict readback; the existing Zenodo field rules.
5. **Disclaimer:** "logical validity given the model, not empirical validation of its assumptions."

Nothing else blocks publication.

### Demoted to non-blocking enrichment
- Per-claim witnesses, triviality/depth probes and DEFINITIONAL/ROUTINE/SUBSTANTIVE labels run as a background track, never as a release gate.
- Labels already obtained are printed. Claims without one print "depth not yet assessed".
- Results are added later as a new record version when convenient.
- Background-track failures never cause a Gate 3 stop.

### Weekly cadence
- Every week, a Methods Digest of all notes passing the minimal gate. Full papers stay standalone.
- Backlog first: all staged packages that pass the minimal gate go in the next digests, at ≤10 writes/day, until the backlog is clear.
- Hard stops only for: a certificate mismatch, a scope violation (paper claims beyond the certificate), an INV-9 failure, a content/file/PID mismatch on readback, or a Zenodo field class not covered by existing rules (batch-reported).

---

## First Methods Digest audit + catalog provenance decision — 2026-10-08

**Digest 10.5281/zenodo.23226761: Claude audit PASS.** Independent public readback on 2026-10-08:
- Contains 7 notes (Runs 125, 126, 128, 129, 131, 134, 141), all INDEPENDENT basis.
- Every listed claim carries a certified witness and a depth label (mostly SUBSTANTIVE; Runs 131 and 134 partly or wholly ROUTINE, honestly labeled).
- The disclaimer is present, and so is "no aggregate theorem claimed".
- isSupplementTo links go to the 12 predecessor DOIs. Community: viridis-canon.
- SHA-256 of the public paper.pdf, paper.tex, DIGEST_MANIFEST.json (88102cd5…) and METHODS_NOTES.zip all match PUBLICATION_BINDING.json.

**Catalog provenance: APPROVED.**
- Existing catalog records keep their recorded coverage provenance. Reuse historical ledger snapshot `15350393…` and the original build inputs for them, because provenance is a historical fact about when each record was assessed.
- New records get current-SSOT provenance.
- The catalog header names both snapshots and their hashes.
- Current SSOT and all guards stay as they are.

**Standing rule:** additive catalog updates that preserve every existing field byte-for-byte and pass the unchanged guard are pre-authorized. Never stop for them again.

**Reminder:** the 2026-10-07 SIMPLIFICATION section governs all remaining backlog publication.

---

## Own-record comparison principle (ends Zenodo field stops) — 2026-10-08 (evening)

Trigger: new-version draft 23246368's `publication_date` went from 2026-10-07 to 2026-10-08. Zenodo resets the date on a new draft. **APPROVED:** the draft's date comes from its own authenticated creation timestamp. Recover 23246368 in place; do not create another version.

Root cause of the repeated stops: the readback compares Zenodo's own housekeeping on the **new** record against expectations it can't know in advance. Permanent rule from now on:

1. **Own new record or draft (the thing we are publishing).** Compare only what **we send or control**, and require it to equal our payload exactly:
   - metadata we PUT, including an explicit `publication_date` that we set ourselves on every PUT, equal to the publish date (America/New_York);
   - files: names, sizes, checksums;
   - DOI and concept identity;
   - related identifiers, communities, banner/description text.
   Everything else Zenodo sets on the own record (dates, revisions, flags, ui, links, stats, previews, PIDs it mints) is logged, not gated. Sole exception: a server value that **contradicts** something we sent is a hard stop.
2. **Every pre-existing record** (prior versions, untouched records): byte-exact as before, except the already-approved version-chain flags.
3. With rule 1, a server-managed field on the own record is **never** a new mismatch class. Escalate only content, file, PID-identity or prior-record changes.

Resume: recover 23246368 (explicit publication_date in the PUT), then publish the 49 staged backlog notes through the weekly digest, ≤10 writes/day.
