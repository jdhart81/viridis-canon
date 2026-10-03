# Mirror drift diagnosis

Report-only; neither source nor mirror corrected. Source reads are parity evidence only.

| Run | Differing files | Supported changed side/time | Cause |
|---|---|---|---|
| Run-102 | .DS_Store | 2026-07-19T17:59:38.721881+00:00 UTC; mirror | No scientific drift; extra hidden OS metadata causes strict INV-8 hold. |
| Run-112 | paper.tex, paper.tex.bak_2026-08-01_corr | 2026-08-01T18:17:40.653999+00:00; 2026-07-28T13:39:08.215155+00:00 UTC; mirror | Mirror corrected boxed ghost-floor inequality to monotone bounds; source and both PDFs retain prior bytes. |
| Run-113 | README.md, README.md.bak_2026-08-01_corr, paper.tex, paper.tex.bak_2026-08-01_corr | 2026-08-01T18:17:40.655383+00:00; 2026-07-29T07:23:24.266656+00:00; 2026-08-01T18:17:40.654683+00:00; 2026-07-29T07:21:16.935570+00:00 UTC; mirror | Mirror corrected equality locus to Tc in (0,Ta] and Landauer saturation, including README; source and both PDFs retain prior bytes. |

Filesystem timestamps plus byte-identical backups establish supported side/time attribution; no actor audit trail available.

Run-112/113 mirror correction backups exactly match current Desktop originals. Both source/mirror PDFs match each other and are identified as stale by the contemporaneous rebuild note. Run-102 holds because strict parity includes hidden extra files; do not suppress it without an approved invariant change.

Corroborating note: [PDF_REBUILD_REQUIRED_2026-08-01.md](/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/RESEARCH_PIPELINE_v2/PDF_REBUILD_REQUIRED_2026-08-01.md). Exact full hashes, birth/mtime observations and classified side evidence are in [MIRROR_DRIFT_DIAGNOSIS.json](MIRROR_DRIFT_DIAGNOSIS.json).
