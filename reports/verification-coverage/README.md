# Coverage and report-only production hooks (2026-10-02)

The hooks are installed in REPORT_ONLY mode. Enforcement is OFF; Zenodo writes: 0. The source/scheduler root remains the Desktop laboratory, and certificate assessment remains Cowork only. Production scripts are preserved before and after installation with SHA-256 hashes under `00_lab_infrastructure/gates/production_snapshots/`.

[Cycle report](2026-10-02/NIGHTLY_CYCLE_REPORT.md) · [DOI triage](2026-10-02/DOI_TRIAGE.md) · [Evidence manifest](2026-10-02/EVIDENCE_MANIFEST.json).

The checkpoint-bound observation cycle finished **HOLD**: certification overdue, FIFO targets unmet, and reversible package work remains. Run-184 already satisfies this nightly generation window; no second paper was generated. The production publisher and Canon mirror each exercised six live hook calls in default local-only plans.

Receipt-era coverage is **65/69** (runs 116–184). Runs 177, 182, 183 and 184 remain uncertified. INV-8 finds **MIRROR_DRIFT** in Run-102 (extra mirror `.DS_Store`), Run-112 (edited paper plus backup) and Run-113 (edited paper/README plus backups). Those runs cannot count as eligible or certified. No drift was repaired.

File counts are a strict partition of 20,085 `.lean` files: UNSOUND 168, HAS_SORRY 1,026, DEBT 834, CLEAN_UNCERTIFIED 17,306, CERTIFIED 751 (exact content copies/dependencies included; this is not 751 distinct proofs). Paper-run counts: MIRROR_DRIFT 3, HAS_SORRY 4, NO_FORMALIZATION 112, CERTIFIED 65. One synthesis is outside paper counts; `_LATEST` is excluded. All foundational quarantine fixtures remain UNSOUND.

DOI triage: CURABLE_BY_JOIN **0**; TRUE_CONJECTURE **52**; COSMETIC **0**; SUBSTANTIVE **46**. TRUE_CONJECTURE includes unavailable joins and mismatched evidence; it does not assert falsity. SUBSTANTIVE includes changed certification assertions in manuscript bodies, even when mathematics is unchanged. The diffs distinguish provenance/status edits from removed hypotheses or changed numerical counts. SAC removes explicit nonempty-family/nonnegative-coefficient conditions; DSWC removes its formalization-correction account; SRA changes 27,131 tests to 26,691.

Anonymous public GET readback succeeds for all **98** DOI records. Every one lacks the gate's required conjecture banner. All **46** proof-certified artifacts' deposited PDF and TeX pairs match published file checksums. Current public metadata and exact diffs are preserved in the cycle evidence; no account-wide private census is claimed.

59 consumer regressions pass, including a one-byte source/mirror divergence, exclusion from certified coverage, missing/extra/symlink inventories, certificate binding refusal outside Cowork, metadata immutability and manuscript-number/hypothesis changes. Production scripts compile as Python; no Lean, Lake, Elan, Comparator transport or issuer was executed.

Full per-file ledger tables remain local at `RESEARCH_PIPELINE_v2/corpus_ledger.json` and the dated production report directory. Review the cycle before any separate enforcement decision.
