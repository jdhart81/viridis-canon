# Viridis Foundation & Canon — Completion Game Plan

**Owner:** Justin Hart · **Executor:** Codex · **Reviewer:** Claude
**Purpose:** finish the foundation, the canon audit and the public record in one continuous run, with human
stops only at the three gates below. Supersedes piecemeal F-prompts; all prior reports remain evidence.

## Standing decisions (do not re-ask)

1. **Invariant.** The Intelligence Bound THEOREM is the certified min form
   `İ ≤ min(ρ·B, P/(k_B T ln 2))` under the named premises in Run-900's PREMISE_LIST. The data-wall corollary
   (P → ∞ ⇒ İ ≤ ρB) is the proven non-substitutability result. `dI/dt ≤ P·D/(k_B T ln 2)` is **THE INTELLIGENCE
   BOUND CONJECTURE (product form)** — never called a theorem.
2. **Dual-root design** stands: Desktop `science ` = generation; Cowork = mirror + certification. Gates scan Cowork.
3. **Gate code** lives in `jdhart81/viridis-canon`. Every change via PR with tests; merge when all checks pass.
4. **Public label wording** (exact, once, titles never modified):
   "UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. Lean sources may
   compile but have not been independently certified. Results are conditional on the stated model assumptions."
5. **DOI handling:** metadata amendments in place for uncertified records; new versions only for papers that can be
   published as fully verified (certificate + PUBLICATION_BINDING). No interim unverified reissues.
6. **Pre-approved protected changes:** the F2h items only (foundational 600 s comparator profile restricted to
   Run-900–999; exit/signal/phase/elapsed in receipts; deployed-script drift snapshot). Anything else protected = Gate 2.

## Invariants (must hold at every step)

- Verifier acceptance logic, issuer and align_challenge stay byte-identical (tests prove it).
- No certificate from recovered, cached or out-of-band results; every certificate has its own receipt round trip.
- Immutable attempts: never overwrite a prior attempt; new attempt directory every time.
- Logical validity is never presented as empirical validation.
- Zero production Zenodo writes before Gate 1. Sandbox (sandbox.zenodo.org) is allowed anytime.
- Fail closed: anything ambiguous is HOLD/UNCERTIFIED, never upgraded.

## Retry policy (to avoid back-and-forth)

- **Infrastructure failure** (transport, timeout, resource kill, droplet hiccup): diagnose read-only, apply only
  pre-approved fixes, retry the same frozen bytes. Max **2 retries** per object; then Gate 3.
- **Proof failure** (identity mismatch from source, kernel rejection, sorry, bad axiom): fix in a new immutable attempt
  if the fix is mechanical (naming, API port, instance names). If the fix would change a theorem statement or premise,
  Gate 3.

## Phases (run continuously; produce one dated report per phase)

### Phase 1 — Certify the foundation
1. F2h: PR (foundational profile, receipt diagnostics, deployed-script drift snapshot + reconciliation); deploy with
   hash readback.
2. Run-900 v009 on frozen v005 bytes (foundational profile, --timeout 1200). Expect CERTIFIED.
3. Run-901: formalize the positive-learning witness (fair-Bernoulli product, rate log 2 > 0, all premises) as an exported
   Lean theorem; add honest successor statements for the h_mem lemmas (`erasure_dominates_learning_transfers_power_bound`),
   originals preserved. Certify via the same pipeline.
**Exit:** Run-900 and Run-901 certificates exist, or Gate 3.

### Phase 2 — Restate and re-anchor the canon
1. Corrected origin manuscript (min-form theorem + premises; data-wall corollary; product form as explicit conjecture with
   its two required premises; no unsupported "derived"), bound to Run-900/901 via PUBLICATION_BINDING.
2. Classify every canon result citing the bound: THEOREM-DEPENDENT vs CONJECTURE-DEPENDENT. Replace
   `axiom intelligence_bound` (Gaia) with an import of the certified theorem where valid; mark the rest conditional.
3. Quarantine p_vs_np and all UNSOUND_ENVIRONMENT files from every index (already ledgered; enforce in indices).
4. Entropy submission: determine from local records whether it is under review; if so, draft (do not send) a correction
   letter to the editor describing the unused inconsistent axiom, the assumed premises, and the corrected statement.
**Exit:** classification table with counts; drafts ready.

### Phase 3 — Clean the canon
1. Run-177 (proof failure): repair mechanically if possible, else document as failed with cause. Runs 182–184: complete
   through the normal nightly pipeline.
2. Trivial certified claims (5 whole, 4 mixed across 9 runs): relabel CERTIFIED_TRIVIAL; split mixed rows.
3. PUBLICATION_BINDING receipts for the 27 VERIFICATION_STATUS_ONLY papers.
4. CONTENT_CHANGED (19): BCAN corrected-version proposal limited to certified scope; SAC bridge text; SRA record the
   26,691 correction; remaining 16 bind or flag individually.
5. The 16 reissues (9 chains): prepare as **verified** new versions (certified candidate + statement + certificate +
   binding). Prepare only.
**Exit:** every published DOI has a final intended status and a prepared action.

### Phase 4 — Prepare the public release (single packet)
1. Fix the write-plan generator: titles untouched (test after.title == before.title); exact label wording above;
   per-field preservation table (doi, resource_type, relations, license) restored or justified.
2. Run the full sequence on sandbox.zenodo.org (amendment and new-version flows) with readback proving title, DOI and
   version chain survive.
3. Assemble **RELEASE_PACKET.md**: every planned production write (36 UNCERTIFIED amendments, 9 verified reissue chains,
   BCAN correction, corrected Intelligence Bound paper as new version of its concept), each with before/after metadata,
   SHA-256 of the exact payload, rollback note, and sandbox evidence. Include the Entropy letter draft if applicable.
**→ GATE 1. Stop.**

### Phase 5 — Execute and harden (after Gate 1 approval)
1. Execute exactly the approved payload hashes; read back each record; abort on any mismatch.
2. Flip publication_gate to **enforcing** for all new artifacts (nightly papers cannot carry DOI/"Theorem" language
   without certificate + binding).
3. Make PUBLICATION_BINDING mandatory in the nightly flow; trivial-theorem rule active; parity + drift checks nightly.
4. Weekly coverage report generated automatically from the ledger.
**Exit:** Definition of Done below.

### Phase 6 — First contact with reality (planning)
Write PREREGISTRATION.md for the experiment that discriminates min form vs product form (power-limited regime: product
predicts İ ∝ D, min predicts no D-dependence). Computational first. Cost, timeline, falsification criteria.

## Gates (the only reasons to stop)

- **Gate 1 — Public release.** One packet, one approval (by payload hashes). Nothing public before it.
- **Gate 2 — New protected change** not in the pre-approved list.
- **Gate 3 — Scientific surprise or exhausted retries:** a theorem fails for non-mechanical reasons, a premise must
  change, the conjecture-dependent share of the canon exceeds 50%, or 2 infrastructure retries fail.

## Definition of Done

- Run-900 and Run-901 certified; foundation paper restated and bound.
- 100% of published DOIs carry an accurate status; every "verified" claim = certificate + PUBLICATION_BINDING.
- 0 unsound or vacuous files in any canon/public index.
- Every canon result classified THEOREM- or CONJECTURE-DEPENDENT.
- Deployed verifier scripts == protected baseline.
- Enforcement ON; 7 consecutive clean nightly reports (no drift, no unbound publications, coverage reported).
- Preregistration written.

---

## Gate 3 resolution — 2026-10-03 (decided; do not re-ask)

- **Run-900 CERTIFIED** (VRS-COMPARATOR-DUAL-KERNEL-1, issued 2026-10-03T20:44:26Z); all ten bindings independently
  re-hashed and matched; receipt VERIFIED with both kernels.
- **Denominator** for conjecture dependence = the bound-citing population (55 logical entries). Result: ≥33/55 (60%)
  CONJECTURE_DEPENDENT in physical interpretation; 22 UNRESOLVED.
- **Decision: continue the plan.** The 50% trigger is retired as a stop condition; the share is now a reported metric.
  Conjecture-dependent results are labeled "conditional on the product-form premises (PL, PD)"; their algebra under
  stated hypotheses remains valid.
- **Added to Phase 2:**
  1. **Run-902 — Product-Form Conditional Theorem.** Certify: given PL (Landauer cost per raw observation bit:
     R_obs·K ≤ P) and PD (useful information is fraction D of observations: rate ≤ R_obs·D), then rate ≤ P·D/K.
     Both premises named in the statement; non-vacuity witness; same pipeline. Downstream files should import this
     certified conditional instead of ad hoc `hcap`/product hypotheses (propose the re-anchoring; apply via PR).
  2. Classify the 22 UNRESOLVED entries (statement/premise/import review). No entry counts as THEOREM-DEPENDENT
     without evidence.
- **Phase 6 elevated** to top science priority: the preregistered experiment must specifically test **PL** (does
  thermodynamic cost scale with raw observations or only with useful information) and discriminate min vs product form.

---

## Gate 1 decisions & full-completion authorization — 2026-10-04 (Justin; do not re-ask)

Justin directs Codex to complete ALL remaining work. Human review gates are replaced by the deterministic rules below;
anything a rule cannot decide is HELD (left in its current state and listed), never published on judgment.
Claude reviewed the Gate 1 packet: 7 certificates (900–902, 177, 182–184) re-hashed OK; 36 amendment payloads
title-preserving, single exact banner, description/keywords only; corrected foundation paper scope accurate.

### Decisions
1. **Placement:** corrected Intelligence Bound paper = NEW standalone record (own concept DOI). related_identifiers:
   isSupplementTo the Canon hub concept 10.5281/zenodo.19317982; references Run-900/901/902 certificates. Then publish a
   next Canon hub version citing it as spine (isSupplementedBy). Never version the paper inside the hub chain.
2. **Entropy:** no journal correspondence found in Justin's email; treat as never submitted. Archive the letter draft; do not send.
3. **Sandbox credential:** if Justin's existing sign-in lets you reach sandbox.zenodo.org, create a personal token with only
   `deposit:write`+`deposit:actions`, store it in the keychain, never print/log it. If a new login, password or 2FA is required,
   STOP and ask Justin (Gate 2-style credential stop).

### Deterministic review rules (replace "independent review")
- **27 status-only bindings:** issue PUBLICATION_BINDING iff the structure-aware diff is confined to verification-status
  sentences and section titles AND protected math/number/theorem-statement sets are identical. Else HOLD.
- **9 reissue chains:** every claim marked FORMALLY_VERIFIED must map to a certified, non-trivial (trivial-theorem rule)
  theorem in that chain's certificate; all other claims must read DEFERRED/conditional in the manuscript. Else HOLD that chain.
- **BCAN:** certify the scalar-only corrected manuscript; if CERTIFIED, prepare its corrected version under the same rule. Else HOLD.
- **Run-182:** prove the frozen statement derives byte-for-byte from its sealed source via unchanged align_challenge. If not
  provable, mark Run-182 HOLD (do not count in coverage).
- **2 legacy-field amendments (20400274, 20422179):** find a field-preserving API route proven on sandbox; else HOLD.

### Execution authorization (production)
Production writes are AUTHORIZED, without further approval, only when ALL hold for the item: (a) authenticated sandbox
legacy-API sequence passed with the identical transport code; (b) the item's exact payload SHA-256 equals the reviewed hash
(for the 34 amendments, the Gate 1 packet hashes; for newly generated payloads, hashes recorded before execution in
EXECUTION_LEDGER.md); (c) its rule above passed. Execute in this order, with strict public readback after EACH write and
immediate halt + report on any mismatch:
1. 34 UNCERTIFIED amendments → 2. corrected foundation paper (new record) → 3. BCAN corrected version (if certified)
→ 4. passing reissue chains as verified new versions → 5. next Canon hub version citing the foundation paper.
No deletions ever. Rollback = a new exact edit, logged.

### Then Phase 5 and 6 as written
Enforcement ON for new artifacts; PUBLICATION_BINDING mandatory nightly; trivial-theorem, parity and drift checks nightly;
weekly ledger report. Run 7 consecutive enforcing nightly cycles and report each. Write PREREGISTRATION.md (Phase 6:
PL test, min vs product).

### Stops (only)
Credential needing Justin; any readback mismatch; a proof failure needing a statement/premise change; verifier/issuer change
outside the pre-approved list. Final deliverable: COMPLETION_REPORT.md mapping every Definition-of-Done item to evidence.

---

## Readback-mismatch resolution — 2026-10-04 (Justin; do not re-ask)

Mismatch: opening the first production amendment for edit added `custom_fields.legacy:communities` to the draft. Nothing
was published. Root cause of the miss: the sandbox fixture omitted community membership.

1. **Discard the open production edit draft now** (actions/discard on the draft only; the published record is untouched).
   Read back the public record and confirm it is byte-identical to the before snapshot.
2. **Sandbox proof with a community-member fixture:** create a sandbox community, a record in it, and repeat the exact
   edit → PUT → publish sequence with the production transport code. Determine whether `legacy:communities` is a
   server-generated mirror of existing membership.
3. **Allowed resolution (preserving only):** server-generated draft-internal fields are acceptable ONLY if they equal the
   record's existing values and the **public readback after publish** shows communities and every other field unchanged
   except description and keywords. Encode this as an explicit, tested allow-rule (field name + equality-to-existing
   condition), not a blanket ignore. The decisive acceptance check remains the public post-publish readback.
4. If the sandbox shows membership would change or the field cannot be proven a pure mirror, HOLD all community-member
   records and continue with the rest; report.
5. Payload hashes for the 34 amendments are unchanged by this (the allow-rule governs readback validation, not payload
   bytes). If any payload byte must change, record the new hash in EXECUTION_LEDGER.md before execution.
Then resume Phase 5 in the authorized order, still halting on any other mismatch. Preregistration (Phase 6) may run in
parallel now.

---

## File-order mismatch resolution — 2026-10-04 (Justin; do not re-ask)

Observed: after the first live amendment (10.5281/zenodo.20008839) Zenodo reordered the file list; all 7 entries and
downloaded checksums unchanged. Claude independently read back the public record: title exact, single banner, keyword
`uncertified` added, community `viridis-canon` preserved, 7 files.

1. **Approved rule:** compare file lists as a set keyed by filename, requiring (a) filenames unique within the record,
   (b) identical set of filenames, and (c) every per-file field identical (checksum, size, file id/key, mimetype, any other
   returned field). Order is ignored; nothing else is. If filenames are not unique in a record, fall back to strict
   ordered comparison for that record (HOLD on reorder).
2. **Before resuming production:** prove the rule on a sandbox multi-file record (≥5 files) through edit → PUT → publish,
   including a forced reorder case and a negative test where one checksum differs (must fail). Add these as regression tests.
3. Resume Phase 5 in the authorized order; halt on any other mismatch.
4. **Deferred follow-up (do not do now):** after all amendments land, propose one batched keyword-cleanup pass removing
   verification-asserting keywords (e.g. "machine-checked proof") from UNCERTIFIED records, as its own reviewed payload set.

---

## Inherited-file resolution — 2026-10-04 (Justin; do not re-ask)

Status verified by Claude on public records: 34 amendments live (spot-checked 5: one banner, titles exact); corrected
foundation paper live as standalone 10.5281/zenodo.23141592 (concept 23141591), isSupplementTo 10.5281/zenodo.19317982,
with Run-900/901/902 certificates, binding and review files attached.

1. **Approved inventory is authoritative for every new version** (BCAN and all 9 reissue chains). In the new-version draft,
   remove inherited files not in the approved inventory; if an inherited file shares a name with an approved file but
   differs in checksum, replace it. Before publish, the draft file set must equal the approved inventory exactly
   (filename-keyed, every per-file field incl. checksum). Earlier published versions are never modified.
2. **Report before publishing each chain:** list every inherited file being dropped (name, size, checksum) in
   EXECUTION_LEDGER.md. Files intended to persist (e.g. LICENSE, CITATION) must be in the inventory explicitly.
3. **Sandbox first:** prove on a sandbox record whose prior version has ≥10 files: new version → drop/replace →
   exact-set check → publish → readback; include a must-fail case (an unapproved inherited file left in place).
4. **No record left behind:** any reissue chain or BCAN that ends HOLD must instead receive the standard UNCERTIFIED
   metadata amendment (title-preserving, same rules as the 34), so no uncertified record keeps implying verification.
5. **Optional, low priority:** add the foundation record 23141592 to the `viridis-canon` community if that can be done
   without other field changes; verify by readback.
Resume Phase 5: BCAN → reissue chains → Canon hub successor citing the foundation. Halt on any new mismatch.

---

## Server-managed field allow-list — 2026-10-04 (Justin; do not re-ask)

Trigger: sandbox new-version publish added `pids.oai`; managed DOI and files exact. Approved, and generalized to a closed
allow-list so routine server-managed fields stop halting the run. Each entry is allowed ONLY under its exact rule; any field
not listed here, or listed but failing its rule, still HALTS.

| Field | Allowed only when |
|---|---|
| `pids.oai` (new versions) | identifier == `oai:<host>:<this record's own new ID>` where host = zenodo.org in production (the sandbox's own host in sandbox); provider == `oai`; every pre-existing PID (doi, concept DOI, other) byte-identical |
| `pids.doi` / concept DOI (new versions) | new-version DOI is the one Zenodo minted for this record (read from the same operation's response); concept DOI equals the chain's existing concept DOI |
| `custom_fields.legacy:communities` | already approved: equal to existing membership; public communities unchanged |
| `created`, `updated`, `revision_id` | monotonic/timestamp changes only; no other field derived from them |
| `versions.index`, `versions.is_latest`, `parent.id` | new version: index = previous latest + 1, is_latest true, parent == chain parent; previous version now is_latest false, everything else on it unchanged |
| `links.*`, `stats.*` | URLs reference this record's own ID / counters only; ignored for content comparison |
| file entry ordering | already approved filename-keyed rule |

Encode as a single tested allow-list module (one test per row, plus a must-fail test per row with a wrong value) and use it
for all remaining Phase 5 writes. Resume: BCAN → reissue chains (no-record-left-behind rule applies) → Canon hub successor.

---

## Server-managed allow-list amendment — 2026-10-04 (supersedes the conflicting rows only)

Evidence: `2026-10-04/game-plan-completion/server-managed-allowlist-v001/SERVER_MANAGED_ALLOWLIST_STOP.md`. Codex's proposed predicates are APPROVED with the tightenings below. Every other row of the 2026-10-04 allow-list stands unchanged; every field not listed remains exact-match HOLD.

All rows below are **phase-scoped**: they apply only to the record created by *this operation's own* publish response (record ID equal to the same-operation DOI reservation ID), never to the prior version, the concept record, or any record not touched by this operation.

| Field | Rule (PASS iff) | Must-fail tests |
|---|---|---|
| `pids.oai.identifier` | equals `oai:zenodo.org:<own new record ID>` in **both** sandbox and production (Zenodo's OAI namespace is the literal string `zenodo.org` on both hosts); provider `oai`; every pre-existing PID byte-identical | `oai:sandbox.zenodo.org:<id>`; correct namespace with a different ID; provider ≠ `oai`; any pre-existing PID changed |
| `revision_id` | Two phases. Draft phase: nondecreasing across draft readbacks. Published phase: own-record publish response returns a positive integer *r₀*; every later public readback is ≥ *r₀* and nondecreasing. A draft→published reset (e.g. 31→3) is allowed only at the own publish boundary. Prior version: revision may increase only alongside the `is_latest` flip, with its content/metadata/files byte-identical | reset without an own publish response; non-positive *r₀*; decrease between public readbacks; prior-version revision change with any content change |
| `deletion_status` | absent → exactly `{"is_deleted": false, "status": "P"}` on own new record after publish; byte-identical on every other record | `is_deleted: true`; any status ≠ `P`; any change on a pre-existing record |
| `expires_at` | non-null on draft → `null` after own publish | stays non-null after publish; a published record gaining a non-null value; any change on a pre-existing record |
| `swh` | absent → `{}` on own new record after publish. Any later non-empty value is **ignored for content comparison but logged** (Software Heritage archiving is asynchronous and changes nothing we certify) | `swh` appearing or changing on a pre-existing record within this operation's readback window |
| `ui.is_draft` | `true` → `false` on own new record after publish; `false` unchanged elsewhere | stays `true` after publish; `false` → `true` anywhere |

Invariants unaffected (restated): metadata, custom fields, titles, descriptions, banner text, related identifiers, file names, sizes and checksums remain exact; no rule here can ever turn a content or certificate mismatch into PASS.

### Resume authorization

1. Add the passing and must-fail tests above to the closed module; record the new module SHA-256 in the ledger.
2. Re-run the strict validator against the **existing** sandbox evidence (record 613107). Do not create another sandbox version if that evidence fully passes; if any other path fails, apply the GAME_PLAN retry/stop rules.
3. On sandbox PASS, resume Phase 5 production in the authorized order: BCAN successor (use existing draft 23141980; discard-and-recreate only if its inherited-file state cannot be corrected under the inventory rule) → 9 reissue chains → for every chain ending HOLD, execute its prepared fallback UNCERTIFIED amendments (no record left behind) → Canon hub successor (proposal must become an exact hashed payload first; preserve 21444226's title; link foundation 23141592).
4. Recover the 27 SSOT publication registrations through the preserving consumer before enabling enforcement; 0 registrations in the authoritative table is a blocking defect for Phase 5 hardening, not a cosmetic one.
5. Stop only on a new mismatch class. A recurrence of any class already decided in this GAME_PLAN is handled by its rule, not escalated.

---

## Premise-declaration gate (INV-9) — 2026-10-04

Purpose: the engine must never publish a claim stronger than what was proven. Every run declares what it rests on, and the gate enforces it mechanically.

### Invariant
**INV-9 `PREMISE_DECLARATION`.** Every new run's `SEALED_RUN_MANIFEST.json` and `SEALED_CLAIM_INVENTORY.json` carry a `foundation_basis` field with exactly one value:

| Value | Meaning | Required Lean form |
|---|---|---|
| `THEOREM` | Uses only the certified min form / data wall (Run-900/901) | Imports or restates the Run-900 statement; no PL/PD hypotheses needed |
| `CONDITIONAL_PL_PD` | Uses the product form dI/dt ≤ P·D/(k_B T ln 2) | Every theorem using it takes PL and PD as **explicit hypotheses** (matching Run-902's premise statements byte-for-byte after normalization), or invokes the Run-902 conditional theorem; no axiom, `sorry`, or global assumption may stand in for them |
| `INDEPENDENT` | Does not rely on the intelligence bound | No reference to the bound or its constants |

### Gate rules (HOLD on any violation)
1. Missing or unknown `foundation_basis` → HOLD.
2. Declared `THEOREM` or `INDEPENDENT`, but the Lean statement or proof references the product form, or the paper text asserts it unconditionally → HOLD (`PREMISE_UNDERDECLARED`).
3. Declared `CONDITIONAL_PL_PD`, but a certified theorem's statement lacks PL/PD hypotheses → HOLD (`PREMISE_DROPPED`).
4. Paper text must state the basis in the abstract or main-result statement: a `CONDITIONAL_PL_PD` paper must contain the phrase "conditional on premises PL and PD" (or the inventory-approved equivalent) near each use of the product form. Checked by the claim-inventory scan; missing → HOLD.
5. `foundation_basis` is included in the certificate and the PUBLICATION_BINDING receipt, so the public record shows the status.

### Tests
- Passing fixture for each of the three values.
- Must-fail fixtures: product form used under `THEOREM`; PL hypothesis removed from a `CONDITIONAL_PL_PD` statement; PL supplied as an `axiom`; paper asserts the product form unconditionally; field missing.

### Upgrade path
If Phase 6 confirms PL and PD, upgrading is a ledger event that re-labels `CONDITIONAL_PL_PD` results. No re-proof is needed, because the hypotheses are discharged by the new result. If Phase 6 refutes either premise, the ledger lists exactly the affected runs.

### Scope
INV-9 applies to new runs from the next nightly onward and joins the nightly enforcement set (so it counts toward the 7 clean nights). Existing canon is already covered by the 55-entry classification (3 THEOREM / 52 conjecture) and needs no rerun. This changes gate/issuer intake only, as a protected change explicitly approved by Justin 2026-10-04; it does not change the verifier, kernels or axiom allow-list.

---

## Revision-evidence and expiry-representation resolution — 2026-10-04 (evening)

Evidence: `2026-10-04/game-plan-completion/server-managed-allowlist-v002/SERVER_MANAGED_ALLOWLIST_AMENDMENT_STOP.md`.

### 1. `revision_id` r₀ source (replaces "from the own publish response")
The legacy deposition publish endpoint returns HTTP 202 without a revision, so requiring r₀ in that response was my specification error. **Do not run the proposed native-publish-link sandbox operation**: it would change transport between sandbox and production and create another sandbox version for no evidentiary gain.

r₀ is defined as the `revision_id` in the **first authenticated native GET of the own new record after a saved, hash-bound own publish response**. PASS iff all of the following hold:
- The own publish response is HTTP 2xx, its raw bytes SHA-256 is in the receipt, and its record ID equals the same-operation reservation ID.
- That first GET's record ID is the same, and its `revision_id` is a positive integer r₀.
- Every later readback is ≥ r₀ and nondecreasing.

Must-fail tests: no saved own publish response; publish response non-2xx; record-ID mismatch; r₀ ≤ 0; a later readback < r₀; r₀ taken from a GET that precedes the publish response.

### 2. `expires_at` representation
On the **own new record after own publish only**, an absent `expires_at` is equivalent to JSON `null`. Must-fail tests: non-null after publish; absent or null on the draft (the draft must carry its expiry); any presence change on a pre-existing record.

### 3. Standing representation rule (to end this class of stop)
For fields **already on the server-managed allow-list**, and on the own new record only, the following are representational, not new mismatch classes, and need no escalation:
- absent ≡ JSON `null`;
- a legacy-envelope response that omits a server-assigned value, which is then taken from the first authenticated readback after the hash-bound own operation, as in rule 1.

This never applies to unlisted fields, pre-existing records, metadata, custom fields, files or certificates.

### 4. SSOT registrations
Restore all 27 registrations through the preserving consumer now. They do not depend on the sandbox PASS. Then:
- The 2 complete ones (foundation, BCAN) are registered PASS.
- The 25 without claim maps are registered with the explicit status `HOLD_NO_CLAIM_MAP`. That is acceptable for enforcement **iff** the public record carries the UNCERTIFIED banner (verified by readback). Any of the 25 that claims certification without a banner is a defect, fixed by a banner amendment under existing rules.
- Prove a fresh scan retains all 27 before enabling enforcement.

### Resume
Encode the rules above with tests, then revalidate the existing record 613107 without any new sandbox write. On PASS, run the authorized Phase 5 sequence, INV-9, SSOT recovery, enforcement ON, and start the streak.

---

## Derived `ui.*` display fields — 2026-10-04 (night)

Trigger: the edit draft of record 22236409 changed `ui.updated_date_l10n_long` from a September 1 date to October 4, 2026, with no other unexplained difference. APPROVED, and generalized so the `ui.*` namespace stops producing stops one field at a time.

Rationale: `ui.*` is Zenodo's rendering layer. Every value there is derived from source fields that are already compared exactly (metadata, custom fields, files) or governed by the allow-list (`created`, `updated`, `publication_date`, version and status flags). A `ui.*` difference therefore cannot hide a content change; the source comparison catches any real change.

Rules (own record of the operation only; pre-existing untouched records must remain byte-identical):

| `ui.*` field class | PASS iff | Must-fail |
|---|---|---|
| `ui.*date*` (e.g. `updated_date_l10n_long`, `created_date_l10n_long`, `publication_date_l10n_*`) | Calendar date equals the date of its own record's corresponding source timestamp (`updated` → updated, `created` → created, `metadata.publication_date` → publication) in UTC or the locale's display day (±1 day for timezone rendering) | Date matching no corresponding source timestamp; change on an untouched record |
| `ui.is_draft` | Existing rule (true → false at own publish; true on drafts) | Unchanged |
| All other `ui.*` | Excluded from comparison, but logged in the diff appendix; the source-field comparison is authoritative | Any change to a source field the `ui` value derives from, which already fails under the existing exact rules |

Standing rule: a future difference **only** within `ui.*` on the own record is not a new mismatch class. Log it and continue.

---

## Version-chain flag state machine (`versions.*`) — 2026-10-04 (late)

Trigger: prior BCAN record 22236387 has `versions.is_latest_draft` true → false after own successor draft 23141980 was created (creation receipt `bcan-publication-execution-v001/transport/002_POST.json`, SHA-256 `2451b9d4…`). Codex's proposed rule is APPROVED, with all of its listed tests, and **generalized into a complete state machine**, so that no `versions.*` flag on a chain we operate on can raise a new class at any lifecycle boundary.

Scope: only the prior version P and own successor S of a chain this operation acts on, with the transition tied to a saved, hash-bound own operation receipt naming P, S and the parent. Every other record and chain stays exact. Metadata, custom fields, files, checksums, PIDs, media files and `ui.*` (except under its own rule) stay exact on P.

| Boundary (own receipt required) | P (prior published) | S (own successor) |
|---|---|---|
| **Create new version** | `is_latest_draft` true→false; `is_latest` stays true; `index` unchanged | draft; `is_latest_draft` true; `is_latest` false; `index` = P.index+1 (or null/absent on the draft ≡ rule 3 representational) |
| **Publish S** | `is_latest` true→false; `is_latest_draft` stays false; `index` unchanged | `is_latest` true; `is_latest_draft` true (or absent ≡ false/true as Zenodo renders; logged); `index` = P.index+1 |
| **Discard S (draft only)** | `is_latest_draft` false→true; all else restored to pre-create values | gone (404) |
| **Edit published record (no new version)** | no `versions.*` change permitted | n/a |

Must-fail (in addition to Codex's list): any flag transition without the matching own receipt; transition in the wrong direction or at the wrong boundary; two records in one chain with `is_latest=true` after publish; an index gap or reuse; any `versions.*` change on an unrelated chain.

Standing rule: a `versions.*` difference on P/S that matches this table is not a new mismatch class. Log it and continue. A difference that does not match is a hard stop.

Revalidate the already-saved BCAN evidence (no new draft), then resume.

---

## Source-bound derived-preview policy + remaining execution authorization — 2026-10-04 (21:30)

Evidence: `2026-10-04/game-plan-completion/late-version-chain-consolidated-review-v004/CONSOLIDATED_READBACK_REVIEW.md`. Codex's batched review, including the predicted-risk table, is the right practice; this section resolves both the observed thumbnail class and the four predicted classes in one decision.

### A. Derived-preview policy (approved)
Zenodo builds previews (thumbnails, IIIF image endpoints, image-tile media, archive container listings) asynchronously **from file bytes we already pin by checksum**. They carry no claim content. On the **own record of the operation only**, the following may appear, disappear or regenerate:

| Derived field | PASS iff |
|---|---|
| `links.thumbnails` | Every URL is on the allowed host and names the own record and a file key **currently in, or removed under a saved hash-bound own DELETE from**, the approved inventory. Disappearance is allowed only after such a DELETE of the source file (Codex's proposed exception, with all its listed tests). (Re)appearance is allowed after an approved upload/publish of the source file. |
| `files.entries.<key>.links.{iiif_api,iiif_base,iiif_canvas,iiif_info}` | Same own-record/own-file-key binding; file key in the approved inventory; that entry's checksum, size and key remain exact. |
| `media_files.entries.*` (e.g. `<key>.ptif`, `image-tiles`) and `media_files` aggregates | `processor.source_file_id` resolves to a file in the own record's approved main inventory. Media entries **never** count toward, substitute for, or satisfy the main-file inventory. |
| `files.entries.<zip>.links.container` | Own-record/own-file-key binding; the archive's checksum is exact. |

Must-fail tests: Codex's thumbnail list, plus a derived link or media entry pointing to a foreign record, foreign file or unapproved file; a media entry whose source file isn't in the inventory; any derived-field change on a pre-existing untouched record or the prior version; any change to a main-file checksum, size or key.

Standing rule: own-record derived-preview differences matching this table are logged, not escalated.

### B. Execution authorization (no further approval needed for these)
1. **Complete BCAN:** finish the approved draft inventory on 23141980, publish, and read back strictly. If the published PDF's previews are not yet generated at readback, poll up to 10 minutes; their absence alone is not a HOLD.
2. **9 chains:** all remain HOLD on real scientific gaps (statement-scope gaps in 129/131/134/141; incomplete whole-paper claims in 125–128/130). Correct: do not reissue them. Execute the 16 prepared fallback UNCERTIFIED amendments (aggregate plan `bc7762cd…`).
3. **25 missing-banner defects:** the 25 `HOLD_NO_CLAIM_MAP` registrations whose public records lack the UNCERTIFIED banner get banner amendments through the same exact-payload/strict-readback pipeline (the same template as the 34 already live). This is required before enforcement acceptance.
4. **Canon hub successor:** execute the v003 exact payload (metadata SHA `48091fb7…`, manifest `9f191afc…`) after steps 1–3.
5. **Public index:** add the explicit foundation 23141592 and BCAN publication joins; deploy the prepared catalog/index (0 unsafe labels).
6. **Activation:** merge PR 50 after its gates pass, install INV-9 and the runtime/hooks (22-target installer), close the post-install protected hash check, enable enforcement, and start the 7-night streak.

Content, metadata, certificate or main-file mismatches remain immediate hard stops. New unclassified server-managed classes still follow the batch-report rule.

---

## Byte-derivable file metadata principle — 2026-10-05

Evidence: `2026-10-04/game-plan-completion/source-bound-preview-consolidated-review-v001/` (`PROPOSED_PDF_DIMENSION_RULE.md`, `BCAN_PDF_GEOMETRY.json`). Codex's proposed own-PDF geometry rule is APPROVED with all its must-fail tests, and generalized as a principle so that the next byte-derived field does not stop the run again.

**Principle.** On the own record of the operation, a server-added per-file field `files.entries.<key>.metadata.*` (e.g. `width`, `height`, page count, MIME/format details) is PASS iff **Codex independently computes the same value from the hash-pinned approved bytes** of that same file (own upload receipt → native readback → UUID/checksum/size exact), using a deterministic parser recorded in the receipt (parser name, version and output). Mismatch, non-computable values, wrong type, or any such field on a prior or untouched record → HOLD.

- Recomputation is the acceptance test, so this principle never trusts the server's value; it verifies it against our own bytes.
- PDF geometry: width/height must equal page-1 MediaBox (or CropBox if they differ, recorded) in PDF points, with rotation applied; Codex's unsupported-geometry cases remain must-fail.
- A server field that cannot be recomputed from bytes is not covered and follows the batch-report rule.
- Main-file key, checksum, size and UUID stay exact. Metadata on the record itself (title, description, creators, etc.) is never covered.

Resume BCAN from its current state (19 removals done, 2 manuscripts uploaded, 7 evidence files pending); do **not** rerun the frozen after-17 driver. Then continue the authorized order without further approval.

---

## Amendment-draft OAI PID restoration — 2026-10-05 (evening)

Evidence: `2026-10-05/game-plan-completion/amendment-oai-consolidated-review-v001/CONSOLIDATED_READBACK_REVIEW.md`. The sandbox-first exact restoration workflow is APPROVED, including all 20 proposed cases, with these specifics:

1. **Invariant (unchanged and absolute):** after publish, the **public** `pids` object of every amended record is byte-identical to its pre-edit public value. A transient omission of `pids.oai` is allowed only on the own unpublished edit draft, after a saved own legacy PUT receipt, and only for the OAI object.
2. **The sandbox proof decides the route.** Build a sandbox amendment on the same legacy transport (create → publish → edit → identical legacy PUT) and record the transient loss. Then test, in this order:
   - **Route A, publish-regenerates:** publish the edit as is. If the public `pids.oai` comes back byte-identical, Route A is the production route and no native PID write is needed.
   - **Route B, native exact restore:** if Route A fails in sandbox, test the prepared body `PROPOSED_EXACT_NATIVE_PID_RESTORE.json` (SHA `418eaedb…`) before publish, then publish and read back.
   Use whichever route the sandbox proves. If neither proves exact, HOLD.
3. **Retroactive check (required before resuming):** with read-only GETs, confirm that the public `pids` object of all 34 previously published amendments and foundation 23141592 equals its pre-amendment value. Any public OAI loss there is a hard stop: report it, do not repair.
4. **Standing rule:** once a route is sandbox-proven, applying it to every remaining amendment (16 fallbacks, 25 banners, the hub) is the approved procedure, not a new class. Pre-check each draft, and require exact public PIDs after publish.
5. **Streak-collector cutover guard:** approved as mechanical work under the existing genuine-future-window rule. Implement it with its 36 regression cases before activation.

---

## Close-out decisions — 2026-10-06

Status accepted: enforcement ON (cutover Run-188), PR 50 + PR 52 merged, 75 amendments receipt-confirmed, hub successor 23174891 live with isSupplementedBy 23141592 (independently confirmed by public API read 2026-10-06), BCAN 23141980 live, 22/22 protected hashes. Remaining items are resolved as follows. **None requires another human decision.**

1. **Evidence durability (do first).** COMPLETION_REPORT cites evidence under `/private/tmp/...` (`UNIQUE_AMENDMENT_TARGETS.json`, `DOD_EVIDENCE.json`, `catalog.json`). macOS purges `/private/tmp`. Copy every cited `/private/tmp` file into `reports/verification-coverage/2026-10-05/game-plan-completion/evidence-durable/`, verify SHA-256 equality, and rewrite the report links. Add a gate test: COMPLETION_REPORT links must resolve inside the Cowork root.
2. **Legacy banner HOLDs 20400274, 20422179.** No record left behind still applies. Attempt the banner amendment with the proven edit/PID route. If the legacy fields make an in-place edit impossible under the strict rules, publish a **banner-only new version** instead: same files byte-identical, description with the standard UNCERTIFIED banner, everything else exact, strict readback. Never delete.
3. **"0 unsound/vacuous files" criterion: clarified, not lowered.** Deleting or hiding historical public sources would destroy provenance. The criterion is met iff every unsound/vacuous source in any public index is (a) explicitly labeled QUARANTINED, (b) never admitted to the verified/spine sets or any verified count, and (c) excluded from all certification claims. The current catalog (1 quarantined, 0 verified/spine admissions) satisfies this once readback confirms the label is rendered publicly. Mark it EVIDENCED with that readback.
4. **Streak.** Seven genuine consecutive clean enforcing windows starting 2026-10-06. A failing night resets to 0. Codex reports only on a failing night or on reaching 7/7; no daily check-ins needed. A weekly ledger report is still produced.
5. **Final audit.** At 7/7, Codex regenerates COMPLETION_REPORT. Claude then audits it against the Definition of Done before the program is declared complete.

---

## Publication-binding timing fix — 2026-10-06 (evening)

Evidence: `2026-10-06/viridis-nightly-science-generator-20261006T110349Z-enforcing/NIGHTLY_CYCLE_REPORT.json`.

Diagnosis (verified by Claude):
- Run-188 is a working run of the engine. It is certified (`LEAN_ZERO_SORRY_CERTIFIED`, issued 05:14Z), carries the Methods-Note disposition, and has `foundation_basis = INDEPENDENT`. INV-9 PASSED on its first live run.
- The night failed only because the gate demands `PUBLICATION_BINDING.json` for a run that has **not been published**. A binding links a public DOI to a certificate, so it cannot exist before publication. As written, every certified-but-unpublished night fails, and the streak could never start.

Rule (gate correction, approved):
1. **The binding is required at publish time, not at certification.** A certified run with no DOI or deposition is `CERTIFIED_UNPUBLISHED`, which is clean for the nightly window.
2. **The publish gate is the enforcement point.** No Zenodo create/publish for a run may execute unless its `PUBLICATION_BINDING.json` exists and validates against the certificate and the exact upload hashes. The nightly check is also a backstop: any run that has a DOI (in the ledger, deposition receipts or a Zenodo readback) but no valid binding → HOLD.
3. Must-fail tests: published run without binding; binding whose hashes mismatch the public files; publish attempted without binding (blocked pre-write); certified unpublished run wrongly marked HOLD (regression for this bug).
4. **Stale disposition label:** `finalized_runs/Run-188/DISPOSITION.json` says `FROZEN_CANDIDATE_UNCERTIFIED`. It was written at 05:06Z, before the 05:14Z certificate. Reconcile the disposition `formal_status` with the certificate after issuance (an append-only correction record, not an overwrite). Add a consistency check: a certified run cannot carry an uncertified label, and vice versa.
5. **Legacy label-mapping noise:** ~42 legacy DOIs report "artifact must match exactly one ledger entity, found 0". Resolve these through the receipt-confirmed amendment registry (75 targets plus 2 legacy) instead of ledger entities, so each one maps to its already-published banner status. Confirm they are non-blocking, and that the nightly report shows zero unexplained label disagreements.
6. **Streak honesty:** windows that already failed stay failed. The streak counts from the first closed window after this fix is deployed and its protected hashes are recorded. No retroactive passes.

---

## Phase 7 — Science catch-up wave — 2026-10-06 (approved by Justin)

Goal: bring every nightly run up to date. Each one is either published with an exact certified scope or honestly labeled. No backlog is left behind.

### Inventory (Claude, from corpus_ledger + finalized_runs, 2026-10-06)
- Runs 140–188: all 48 have `LEAN_ZERO_SORRY_CERTIFIED` certificates (Run-182 is absent from finalized_runs; locate it or record its status).
- **21 published:** 140, 143, 144, 146–150, 152, 157, 159, 164–166, 169, 171, 173–176, 178. Most are `HOLD_NO_CLAIM_MAP` and carry UNCERTIFIED banners.
- **~27 certified but never published:** 141, 142, 145, 151, 153–156, 158, 160–163, 167, 168, 170, 172, 177, 179–188. Codex confirms the exact list.
- **9 scientific HOLD chains** (125–131, 134, 141) with statement-scope or claim-completeness gaps.

### Wave A — Stage the unpublished certified runs
For each run, build a release package that passes every gate:
1. **Whole-paper claim map:** every claim in paper.tex maps to a certified Lean statement, or is explicitly marked uncertified in the text.
2. **Scope rule (the core rule of this phase):** the paper may not claim more than the certificate. Default repair: **narrow the paper text** to the certified scope, and move unproven claims into a labeled "Conjectures / uncertified remarks" section. Never strengthen claims without a new certificate.
3. Triviality and nonvacuity check. CERTIFIED_TRIVIAL results are labeled as such.
4. INV-9 `foundation_basis` declared. Runs before Run-188 get the declaration from the 55-entry classification, or a fresh classification for runs outside it.
5. DISPOSITION/certificate consistency (fixes the stale `FROZEN_CANDIDATE_UNCERTIFIED` labels on 164, 167–169, 173, 174, 187, 188 with append-only correction records).
6. PUBLICATION_BINDING generated at publish time against the exact upload hashes.

### Wave B — Upgrade the published HOLD_NO_CLAIM_MAP records
Build the missing claim maps.
- If every paper claim is certified or explicitly scoped: publish a new version with a binding, and replace the UNCERTIFIED banner with a **scoped CERTIFIED statement** naming exactly what is certified.
- Otherwise: keep the banner. Never remove a banner without a validating binding.

### Wave C — The 9 scientific HOLD chains
Default: narrow the paper to the certified statements (Wave A rule 2) and reissue scoped. **Re-proof** (strengthening the Lean statement through the Comparator) only for results whose claims are central to Viridis products. Codex lists the top candidates with one line on the business or research value each; Justin picks.

### Publication format
- Full papers: standalone DOIs.
- **Methods Notes: published in a weekly "Viridis Methods Digest" record** (one DOI per week, each note with its own certificate, binding and scope inside). This keeps volume visible without diluting the canon with dozens of tiny standalone records. Justin may override to standalone.

### Execution rules
- Staging is autonomous. A consolidated release packet lists every run with its claim map, scope diff (original vs narrowed text), basis, triviality and binding plan.
- Publication is autonomous for packages that pass **every** gate, through the same pipeline as the 75 amendments: exact payload hashes, PID/version rules, strict readback, and at most 10 Zenodo publications per day.
- Claude spot-audits the release packet before the first publication batch: Codex stops once after staging for that audit, then runs to completion.
- Content, certificate or scope mismatches are hard stops. Server-managed classes follow the existing batch-report rule.
- Ongoing: each new nightly run that certifies goes through the same package path automatically, so the backlog cannot rebuild.

---

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

---

## Prior-record rule narrowed to content we control — 2026-10-09

Trigger: the PDF-preview processing status on prior digest 23226761 went `init` → `finished`. Its files, metadata and PIDs are exact. **APPROVED.**

Rule 2 of the own-record principle is restated so that Zenodo's background processing can never stop the run:

**Pre-existing records stay byte-exact on everything we control or that carries meaning:**
- metadata (title, description/banner, creators, dates we set, keywords, license, related identifiers, communities, resource type);
- files (names, sizes, checksums, count);
- DOI, concept DOI and every PID value;
- version-chain identity (index, parent; `is_latest` flips per the approved state machine).

**Zenodo's asynchronous processing state is logged, never gated, on any record:** preview/IIIF/thumbnail status and links, `media_files`, stats/counters, `ui.*`, `swh`, revision counters, `updated` timestamps, and indexing/processing status fields.

A change in the protected list on a pre-existing record remains a hard stop. Nothing in the processing list ever is.

Resume immediately: publish draft 23246368, then the 49 bound notes through the weekly digest, ≤10 writes/day.
