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
