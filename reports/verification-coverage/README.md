# Canonical coverage receipt (2026-10-01)

Report-only. No new certificate, Zenodo amendment, publication, or production gate activation.

Canonical root: `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0`
Certificate root: `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/RESEARCH_PIPELINE_v2/lean_certificates`

Receipt-era coverage: **65 / 68** (Run-116..181 excluding Run-177; 182/183 held in flight).

| Status | File entities | Paper run entities |
|---|---:|---:|
| UNSOUND | 168 | 0 |
| HAS_SORRY | 1023 | 3 |
| DEBT | 832 | 0 |
| NO_FORMALIZATION | 0 | 115 |
| CLEAN_UNCERTIFIED | 17306 | 0 |
| CERTIFIED | 751 | 65 |

The file census covers **20,080 Lean files**, including imported dependencies, archives, and repeated copies. Counts are a strict partition per table, not theorem counts. One SYNTHESIS entity is outside the 183-paper denominator; `_LATEST` is excluded.

The original T1–T3 and `00_ORIGIN/paper/Intelligence_Bound_Lean4_Proof.lean` are UNSOUND and ineligible for promotion. No source files were repaired or deleted.

Run-177: initial positivity proof failed; changed attempt-2 payload remains held by exact-hash transport review. Run-182: sealed inventory omits `paper.aux` and `paper.out`. Run-183: Comparator reports `No goals to be solved` at lines 34, 45, 48.

Publication census: **110 direct deposit directories, 64 without certificate files**. Local registry plus durable receipts identifies **98 published version DOIs**: **52 without a valid artifact proof certificate**, **46 with valid proof certificates and unresolved manuscript bindings**. Zero publication artifacts match the original sealed manuscript pair. This is a publication-binding gap, not invalidation of the 46 formal proofs.

All 115 pre-receipt runs were cross-referenced: 9 exact publication joins and 13 separate title candidates. The old registry has 9 records. Canon v8/v9 and other unresolved directories remain publication-evidence gaps; reserved/concept/citation DOIs never count as publication. No live account-wide publication census is claimed.

Full machine ledger, per-file table, DOI list, and receipt provenance remain local derived artifacts. Use the commands in the gates README to regenerate them. The PR contains consumers and fixtures, not private runtime data.
