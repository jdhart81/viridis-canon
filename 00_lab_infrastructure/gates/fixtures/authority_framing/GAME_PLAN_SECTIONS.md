## Phase 7 — Claude audit of release packet v002 — 2026-10-07

Packet: `2026-10-06/phase-7-science-catchup-v001/release-packet-v002/RELEASE_PACKET.md`. The packet is accurate and appropriately conservative: no overclaiming was found, and the disclaimer ("logical validity given the model, not empirical validation") is present. The 48 HOLDs are an evidence gap, not a science failure. Resolutions below; after these, publication proceeds without another Claude stop unless a hard-stop condition occurs.

### 1. Per-claim nonvacuity witnesses (blocks 47 packages; 297 null witnesses)
Claude's count: 132 of the 297 claims have **no hypotheses beyond type binders** over nonempty types (ℝ, ℕ, ℤ, ℚ, function types into ℝ).
- **Tier 0, no hypotheses:** nonvacuity is discharged by rule. A universally quantified statement over a nonempty domain with no premises cannot be vacuous. Record `witness = NO_HYPOTHESES (domain nonempty: <type>)`. Custom types need a recorded `Inhabited`/`Nonempty` instance or an explicit term.
- **Tier 1, hypotheses present (about 165):**
  1. Pre-screen candidate substitutions (start with the run's existing `*_nonvacuous` values) using **exact rational arithmetic** (sympy `Rational`, no floats). Use rigorous interval arithmetic for `sqrt`, `exp` or `log`.
  2. For each claim with a passing substitution, emit a Lean witness lemma `example : <every hypothesis at the substituted values> := by norm_num [defs]` (or `positivity`/`nlinarith`).
  3. **Bundle all witness lemmas for a run into one Comparator job on the droplet**, under the standard dual-kernel and axiom rules. A certified bundle sets `selected_reviewed_witness` for those claims.
  4. Claims with no certified witness stay in the paper only under the label **"certified; nonvacuity not demonstrated"**, and do not count toward the note's certified-result headline.
- The exact-arithmetic pre-screen is a selection aid only; the Comparator remains the sole verifier of record.

### 2. Semantic triviality tiers (replaces open "semantic review required")
In the same Comparator bundle, add downgrade-only probes per claim: try closing each theorem with `rfl`, then `simp only [<defs>]`, then `ring`/`ring_nf`/`norm_num`/`linarith`/`nlinarith`/`field_simp; ring` after unfolding definitions. Label each claim:
- `DEFINITIONAL` (closes by `rfl`/defs-only `simp`);
- `ROUTINE` (closes by one standard tactic after unfolding; e.g. Run-140 `option_value_identity` is a `ring` identity under `optionValue`'s definition);
- `SUBSTANTIVE` (no probe closes it).

Labels print in the claim table. A note whose claims are all DEFINITIONAL is published only inside the Methods Digest appendix, never as a headline note. Probes can only downgrade a label; they never certify.

### 3. Run-127: product-form underdeclaration
Narrow the paper. Every product-form statement moves to a labeled "Conjectural context" section that cites foundation 10.5281/zenodo.23141592 and the Run-902 conditional. The certified scope keeps only theorems whose statements and definitions do not encode the product form. If a certified theorem itself encodes the product form without PL/PD hypotheses, that theorem leaves the certified scope and Run-127 goes on the re-proof candidate list. Rerun INV-9 on the narrowed paper.

### 4. Run-147: INV-9 title false positive
Keep the historical title. Add one sentence to the abstract: "This note does not depend on the product-form Intelligence Bound conjecture; its results are independent of premises PL and PD." Amend the INV-9 checker so a phrase-only title match **with zero product-form formula matches and an explicit basis sentence in the abstract** passes. Add must-fail tests: a formula match still fails; the title match without the sentence still fails.

### 5. Run-187 discovery debt
Install the merged corrected selector through the standard PR/protected-hash path. Then confirm via SSOT that Run-187 reads CERTIFIED.

### 6. Release flow after 1–5
Packages that pass all gates go to publication in the weekly Methods Digest: exact bindings at publish time, ≤10 Zenodo writes per day, strict readback. Wave C draft passes (125, 126, 128–131, 134, 141) may go first once their witnesses are complete (each has 0 null witnesses already). No further Claude stop is required. Claude audits the first published digest by readback.

---

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
