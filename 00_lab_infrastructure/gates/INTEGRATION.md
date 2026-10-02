# Verification coverage integration review

Read-only inspection of `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0`.
The initial PR installed no production hooks. The follow-up installs local REPORT_ONLY observers from hash-bound snapshots; it performs no verifier call, Lean execution, publication or scheduler-root mutation.

## Current receipt-era gaps

The exact machine extract is `integration-evidence.json` alongside this note.

* Run-177 attempt 1 is HOLD: Comparator reports `Solution.lean:24:2: failed to prove positivity/nonnegativity/nonzeroness`. The canonical certificate directory contains no certificate. Its attempt-2 candidate is frozen at SHA256 `5ac65b6b04f434190542cd186500258d21bc3163c47d91af2a39eea2b6bf7c30`; immutable transport-security receipt says the modified bytes are outside exact-payload authorization and the review rejected transport. Preserve this hold.
* Run-182 remains in-flight with an intake hold. Its canonical `RUN_MANIFEST.json` declares 25 artifacts while the actual sealed directory contains 27 excluding the manifest. `paper.aux` and `paper.out` are undeclared; all 25 declared hashes match, and none are absent. `stage_comparator_inputs.freeze` rejects exactly this condition at lines 28–31. No `lean_certificates/Run-182` directory exists.
* Run-183 remains in-flight with a failed verification receipt: `Solution.lean:34:4`, `45:6`, and `48:4` each report `No goals to be solved`. Candidate hash is `39e9e149072700e629ced7dba884a0f445313285ae12caecfa3d1d8b49d88a3e`. No certificate is issued.
* Latest closed checkpoint inspected: `RESEARCH_PIPELINE_v2/nightly_checkpoints/viridis-nightly-science-generator-20261001T230209Z/FINISH.json`, completed `2026-10-01T23:05:48.442976+00:00`; remaining debt is `[Run-177, Run-182, Run-183]`, status `HOLD_NIGHTLY_PROGRESS`.

## Existing pipeline APIs and locations

* `RESEARCH_PIPELINE_v2/stage_comparator_inputs.py:17` exposes `freeze(run_value, *, source_root, mirror_root, certificate_root)`. It is nightly-specific: find exactly one source/mirror `Run-NNN_slug`, compare the complete inventory and manifest, require canonical absolute output bindings, freeze original proof bytes, derive alignment, and publish the request last. Do not use it as an unrestricted foundational-object wrapper.
* `RESEARCH_PIPELINE_v2/install_sealed_intake_manifest.py:22` intentionally defaults `SOURCE_ROOT` to `/Users/justinhart/Desktop/science ` while `MIRROR_ROOT` points into Cowork `science-engine/`. Justin's v4 decision retains Desktop as the untrusted generator laboratory and Cowork as the mirror/certification authority. Source reads are restricted to INV-8 parity comparisons; all certificate bindings must stay inside Cowork. The scheduler root remains unchanged.
* `RESEARCH_PIPELINE_v2/engine3_align_challenge.py:104` exposes `align_challenge(sealed_statement, candidate, expected_names) -> (challenge, signature_sha256s)`. It rejects proof holes/escapes, missing or duplicate targets, assignments that do not use `:= by`, target-signature drift, and non-proof context drift. All definitions/imports/context remain exact bytes. For a clean standalone candidate, `align_challenge(candidate, candidate, explicit_names)` derives the challenge using the unchanged helper; its output then becomes the frozen statement/challenge envelope. This is text preparation, never verifier authority.
* Stale-tree `comparator-deploy/bind_formalization_overlay.py` copies existing source/mirror formalization into an existing `CURATOR_INPUT.json` overlay after parity checks. `prepare_comparator_reconciled_overlay.py` has a reviewed run-specific prose replacement map and requires an already certified Comparator overlay. Neither is a general foundational-envelope synthesizer.
* `RESEARCH_PIPELINE_v2/comparator_cloud_lean_verifier.py:133` exposes `verify(*, request_path, formal_statement_path, candidate_path, output_path, host, key, timeout, transport)` and performs the sole private Comparator transport. `issue_lean_zero_sorry_certificate.py:122` exposes `issue(*, request_path, cloud_receipt_path, output_path, audit_path=None)`. Both remain unchanged. The issuer refuses an existing certificate, requires numbered source_run, complete four sealed-input names, exact receipt bindings, dual-kernel checks, allowed axioms, and named raw witness exports.
* `science-engine/07_nightly_engine/viridis-science-agent/nightly/paper_generator.py` only compiles LaTeX; its only template is `templates/viridis-journal.cls`. Scientific generation is agent-authored under `RESEARCH_PIPELINE_v2/automation_prompts/nightly_science_generator.md` and `CODEX_NIGHTLY_SCIENCE_GENERATION_STANDARD.md`, not a Python theorem generator.
* `RESEARCH_PIPELINE_v2/autonomous_transition_executor.py` classifies `CERTIFY_COMPARATOR_FIFO` as judgment work. Its deterministic action map does not perform Comparator transport. Keep a new coverage scan report-only and do not claim an executor hook transports proof debt.

## Smallest integration

1. Keep gates in `viridis-canon/00_lab_infrastructure/gates/` with explicit canonical tree/cert roots. Run report-only before future transport and publisher planning, recording deterministic reports. Enforcing mode is a separate flag.
2. For opt-in Track B, require CLEAN_UNCERTIFIED triage, explicit claim/model-fidelity bindings, explicit theorem/witness names, a unique reserved Run-900..999, and a new immutable target directory. Use unchanged `align_challenge` for challenge creation. Create Methods Note and exact four sealed-input names; keep DEBT/PENDING until unchanged Comparator and issuer succeed. Never generate an envelope for UNSOUND/HAS_SORRY input.
3. Publication insertion point is `_ZENODO_DEPOSITS/publish_dated_bundles.py:89` `metadata_payload(bundle)`, immediately after `release_coherence.validate_bundle(bundle)`. Both `plan()` and `publish_bundle()` consume this function. The Canon mirror/recovery path discovers bundles and calls the same coherence validation in `weekend_canon_lockstep.py:452`; gate there too.
4. Those production scripts and the active automation are outside `viridis-canon`. If the PR contains only gates and adapters/patches, state clearly whether production hooks are still pending. A CLI helper or integration proposal is not an installed live publication gate.
5. Claim-binding templates belong beside new run `CLAIM_INVENTORY.json` / `formalization` data in the generation contract. Preserve sealed runs; generated current labels and proposed metadata derive from the corpus ledger. Published DOI changes remain a separate human decision.

## Test targets

* Run-177 receipt failure and distinct attempt-2 transport hold survive classification.
* Run-182 incomplete artifact inventory remains DEBT/in-flight, never CERTIFIED.
* Run-183 failed cloud receipt cannot be counted merely because candidate text is clean.
* Track-B helper preserves every non-proof byte and rejects the unsound Origin paper before writing an envelope.
* Report-only publisher adapter emits a conjecture proposal without changing metadata/PDF/source bytes; enforcement operates only on a new unpublished artifact copy.
* Missing claim-binding/model-fidelity data and a missing witness export fail closed.
