# Phase 7 runtime integrity log

2026-10-07: Justin approved GAME_PLAN Phase 7 audit item 5. Install the exact selector merged in PR #55. The runtime guard consumes a closed two-target update with actual merged PR Git blobs, 20 unchanged runtime hashes and fresh 22-target protected closure. Original activation evidence is preserved. No verifier, issuer, aligner, backend, pin or droplet change.

- RESEARCH_PIPELINE_v2/verification_coverage_gates/corpus_ledger.py: d9d68fbb90605c975a006c070a448c3b843efb05a52b164c816d232dd6e583d9 → bfd2ec16c1e9c39ebcd39fdb45ccf9683b6864a95d3496109df49f9a7639a173
- RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py: d25e051fe9d2d4e6da04d46cd16d18a101ac4ae2fee49f38596ab2ce04926ea9 → fd9a4fe406445f3181391ca83f462c4889fb3392c4c93d5ac0d54838c223484f

Runtime-update module SHA-256: b74da7279148fd279f22116b728e25786b51d27007d9959756f1e6f643ace403

Reporting-only closeout pin: b8b21f1d8a6df3b53f3f1b18f2dfd5a087169d8bc2ce4060bc72dbad86f5fd17 → 9663c006df997e368373f64e0f10e324661893d7b9246ea92a6c8dfec0b7ec3b (guard literal only).

Fresh protected readback must follow the actual installation timestamp; a pre-install readback cannot clear the successor.

2026-10-07 evening: Justin approved the source-bound probe/witness separation, closed Run-130 probe HOLD and the appended weekly-push simplification. Per-claim witnesses/depth are optional background evidence; the existing main certificate and issuer run-level nonvacuity, exact claim scope, INV-9, disclaimer, publication binding and strict readback remain required. No protected implementation changes or droplet deployment.

The mechanical integration preserves the actual 22-target installed predecessor from PR57, including the original publication_binding (1fb3d5bc1d0df57445b8d7fed8a034e7bab7f1aeb0314db21e3cedd5e237df2e). The older prepared scoped binding (80e5e44e5f331cc50685cce2a9cedbc4d2a4f8a95928c8d6313dd69300327522) remains a distinct source-only proposal. Four further runtime consumers change; all 17 targets outside the five reviewed names remain unchanged. Original snapshots and the INV-9 fixture are byte-bound; assertions are retained.

- phase7_audit_policy.py: 053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7
- phase7_runtime_update.py: 0dbd20d6232287a9bfd15bf0ebbf0ab665829c15b7b9ff82db57b078d393729a
- methods_digest_registration.py: 66cc830f4814ee943c616d754d61cff9be5a65607e0a26ec4f91acd23ce630d7
- methods_digest.py: 5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5
- scoped_release.py: a6e5fe9b1213d91987a5cf125d1f591e643e3e68eb5bac05492196b77e7e3ea8
- phase7_claim_label_render.py: b80b1c7c32bddbf176f08fd5250a7a4c1e610a4848de075397397d7106786141
- probe_observations.py: ebbe0ffff1570acec84bcaf18570e69c9a66938cee932999d9a6729208abb4de

Authority section SHA-256: decoupling ba56d7254744843b9e7512b61f0d80161cf33b366f076d516aa451ba21c8325a; simplification 483fddbd90eb1782911db43de477c161d35214fd033061a83a87b9dec503652a. The immutable runtime-snapshot closure is fafa0a9b4c1675701dcb3f9d972c8e22e565afc2059a5d6d6c39d2b30378721a. Source-only first-digest executor freeze: f4468f5380fae88304c31c61494f43f97551fc279484a7756966a7e91c819c4b. Actual install follows the merged exact head and fresh protected hash closure.

2026-10-07: PR58 merged at 30b11d7783bcee2c0938cfed2dd4975bc518b269 after all required checks passed on 2e35099412abed7472715ef96f3a12fc730037e2. Its installation retained every protected implementation hash (22/22 before and after). The first runtime closure failed before the SSOT compare-and-swap: the section extractor included the newly appended literal Markdown separator after the unchanged old approval. The failed installation and partial closure are retained immutably; there was no Zenodo write or registration change.

The ordinary runtime section extractor now applies the same closed authority-boundary rule as the approved policy. It removes exactly the added separator only when the preceding approval still has its original SHA-256 and both subsequent, uniquely ordered approved appendices have their exact hashes. Changed approval text, changed or missing appendices, duplicate headings and arbitrary padding fail. The runtime validation body, target inventory, source checks, catalog checks and all other function bodies/defaults remain identical. This is a mechanical integration correction under item 5 of the approved decoupling resolution. Protected verifier, issuer, aligner, backend, kernel, toolchain and receipt acceptance code remain unchanged.

phase7_runtime_update.py SHA-256: 0dbd20d6232287a9bfd15bf0ebbf0ab665829c15b7b9ff82db57b078d393729a → e718bfc61a4da1885df282339371707b17139f4eb5f5857cd19540c7cc7a1e90. Installation requires its own passing exact-head PR and merged-source hash closure; a prior readback or failed closure is not acceptance evidence.

2026-10-07 independent source review: the prepared runtime helper `0dbd20d6232287a9bfd15bf0ebbf0ab665829c15b7b9ff82db57b078d393729a` above is preserved as historical proposal evidence. Its chronological guard admitted a protected readback older than the actual runtime installation. The source-only correction is `58d66f6910c5255d83914586fd11bb13a5768fe1913e8ab9efa243f18fe7acd7`; it restores `activated_at <= installed_at <= protected_readback_at <= now` for both selector and policy profiles. No prior log entry, activation receipt, immutable snapshot, or frozen policy artifact is rewritten.

The two added regression checks reject protected readback before selector/policy installation. They both fail against the pre-correction helper and pass against the corrected source. Synthetic current-readback fixtures are explicitly after installation; their original historical receipt remains separately preserved. Focused validation: 136 runtime-update tests and two platform-temporary-directory tests pass. Full report-only gate suite: 1,474 tests pass with the pinned pypdf 6.10.0 dependency; no local Lean or external publication runs.

This correction has not been installed or deployed. Any later runtime installation must use a new source/hash-bound successor receipt for the exact merged helper, its own installation timestamp, and fresh protected readback after that timestamp. Existing digest/executor freezes under the historical helper are not upgraded by this source repair; their current gate admission and applicable source-bound installation evidence must be revalidated before execution.

The parser proposal above was not installed. PR60 now retains the separately merged PR59 post-install freshness correction in full. The combined runtime helper SHA-256 is ae9af64d0940ce2a764a2dd9be61951211b2bf668b957aedf88563301d704194. Relative to PR59 source 58d66f6910c5255d83914586fd11bb13a5768fe1913e8ab9efa243f18fe7acd7, only the exact authority separator parser and the two immutable appendix pins differ. The new immutable closure successor must prove both changes, all original target/source rows, the unchanged original activation and all 27 registration statuses, with its own post-install protected readback. No protected verification logic is changed.
