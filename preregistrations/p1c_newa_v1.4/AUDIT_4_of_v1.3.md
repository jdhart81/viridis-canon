<!-- Independent audit report, reproduced verbatim. Audited version: v1.3 (frozen 2026-10-21 05:15:30 EDT). Delivered 2026-10-21 06:42 EDT. The auditor was a separate Claude agent that had not built the study; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the auditor's scratch scripts are not shipped. -->

## Audit 4 of P1C v1.3 (frozen 05:15:30 EDT, FREEZE.json sha256 6ea1d0b8…)

**Bottom line.** The mechanics hold up. Freeze, package, timestamp, blindness and the M2R wiring all check out. Every reported calibration and pilot re-read number reproduces exactly. The claim that M2R was chosen before the pilot's M2R estimate is true.

C2 = 2.37 is adequate inside the registered family and also past its range edge: exact long-range fields out to 720 km give 4.5% false calls pooled. But C2 has no margin. I found one credible structure outside the family under which the rule over-calls at about 5.4–5.9%: anisotropic fields elongated north–south, along the valleys. Separately, S13's critical value C2_M2 = 3.74 is too small and gives about 6.0% false calls. There is no critical issue; there are two moderate issues and five minor ones.

All three protected folders are unchanged: 657/657 SHA-256 values, sizes and mtimes match, the 21 directory mtimes match, no file is newer than the audit start, and FREEZE checks 219/219. All Python ran with `-B` on copies, with no network.

### Items

| # | Result | Evidence |
|---|---|---|
| 1 M2R code | OK | **Wiring:** primary, stacked, S10, S10b, S11 (M2R without fuel group), S12 and leave-one-year-out all use `FES_R`; S13 uses M2 with `crit=C2_M2`. **Pilot functions:** the only change from the pilot's `run_test_dev1.py` is a `fes=FES` default added to `design()` and `fit()`. **Equivalence:** re-run on copies (paths patched to the copy) rebuilds the pilot table byte-identical (57118595…) and reproduces 233/233 values. **Fast path:** `simcal.Design` equals `fit_twoway`/`fit` to ≤2.6e-14 for both M2R and M2. **`verify_inputs()`:** a wrong FREEZE hash in the fetch record, a modified script, a modified CALIBRATION.json and an outcomes-hash mismatch each give VERIFY FAIL, also under `-O`; one non-SYN row with `--synthetic` is refused. A verified end-to-end run on synthetic outcomes gives model M2R, 24 regions, 75 blocks, S10/S10b/S12 n = 9,941 / 9,368 / 11,309, S13 crit 3.74, `inputs_verified` true. Trivial gaps are in m5. |
| 2 Credible set | ISSUE (minor, m2) | **Reproduction:** 23/23 retention decisions reproduce exactly from their seeds. **Fresh 1,000-replicate screens:** the holes at 0.03/45, 0.03/90, 0.03/120 and 0.045/90 are retained, and 200-replicate screens would retain them 57–84% of the time, so they are noise as the plan says. 0.03/6 is retained in 41% of 200-replicate screens, so "at 6 km no share is retained" depends on the seed. **Binding model 0.4/180 on the registered 512 km grid:** p_share = 0.044; retained in only 28% of 200-replicate screens. With exact fields it is retained in 79%. 0.3/90 is retained 5% of the time and 0.2/45 7%. **Range not closed:** exact fields are retained up to 0.70/720 km. **Inconsistent with the pilot's block ANOVA:** field-only models with share ≤ 0.09 give p ≤ 0.04 against the pilot's ANOVA block share, yet the field screen retains them. |
| 3 Calibration | ISSUE (moderate, M1/M2) | **Reproduction:** binding q95 under M2R = 2.368898064406115 exactly (k = 80, seed 13,000,000), with q90 1.9493 and M2 3.7364 / 3.2197. iid and block 0.11 also reproduce exactly. Bootstrap SE of q95 is 0.045. **Search for over-calling models:** see M1. **Regional fixed effects:** no distortion beyond what is calibrated. Four regions hold 1, 2, 14 and 17 ignitions and contribute almost nothing. Effective number of blocks is 42.3 under M2R against 43.5 under M2; under iid errors q95 is 2.04 against 2.07. The only measurable fixed-effect effect is under block effects (q95 2.26 against 2.10 at share 0.11), which is inside the calibration. |
| 4 Pilot re-read | OK | T recomputed: 2.3126 (M2) and 2.9770 (M2R), 16 regions. Three PILOT_REREAD rows reproduce exactly from their seeds; all 13 rows × 6 columns match the plan. The conclusions still hold under the new credible models: under A.15/10x120 on the pilot design, the M2 5% critical value is 2.24 and the M2R values are 2.32 / 2.67. |
| 5 Plan vs records | ISSUE (minor, m3; also M1) | **Numbers:** all match. The q95 table has 0/73 mismatches; the reference rows, power, NOT REPLICATED shares, β₃₃, sample sizes and the §0 hashes and times match too. **M2R before the estimate:** true. The decision record was written at 07:12:04Z and edited at 07:12:10Z (mtime 03:12:12). The pilot's M2R estimate was first computed at 07:12:22Z, and DEVIATION_3 is stamped 03:12:38. Neither part 1 nor the gap-era code (`run_test_before_M2R.py`) has region terms. **False or overstated statements:** see M1 and m3. |
| 6 Command record | ISSUE (minor, m1) | **What is right:** part 1 is unchanged against the v1.2 freeze. The three recovered commands are byte-identical to the third audit's tool output in its own transcript (06:39:51Z), with lengths verified. The gap is real: the session transcript starts at 06:51:15Z. Among calls that match the token filter (PAT), the extractor skips only a bare self-invocation, and none occurred. **What is wrong:** the PAT filter still drops 46 Bash calls between 06:51 and 09:15Z. |
| 7 Freeze/package | OK | FREEZE 219/219. The `.ots` has a sha256 op and the FREEZE digest at offset 33. `SHA256SUMS` passes 54/54 with no stray files. 46 plain and gz files (decompressed) match FREEZE. `logs.tar.gz` (102 members), `history_v1.3_dev` (17) and `history_v1.1_dev` (8) match FREEZE. The v1.0/v1.1/v1.2 tarballs match their own freezes (0 bad), and their FREEZE and .ots files match the v1.3 entries. |
| 8 Blindness | OK | No outcome, results, registration or fetch-record file exists under p1c or in the package; only pilot files. All 13 confirmatory-ID synthetic outcomes files are 100% 'SYN'. `fetch_outcomes.py --check` on a copy inside `unshare -n` passed G1 and stopped with "G2 FAIL: REGISTRATION.json missing" (exit 1, nothing written). |

### Critical
None.

### Moderate

**M1. C2 has no margin, and anisotropic fields elongated along the valleys over-call. The plan misstates what happens beyond 180 km.**

- **Direction.** These anisotropic exponential fields pass the plan's screen and also a directional screen I added (N–S against E–W correlogram):
  - A.15/10x120 (share 0.15; range 10 km E–W, 120 km N–S): **5.86% ± 0.33** false calls at C2 over 5,000 replicates; q95 2.46, q90 2.03 (above C1). Screen: p_share 0.07, p_range 0.45, ANOVA 0.72; retained in 75% of 200-replicate screens. Directional p = 0.13.
  - A.13/15x90: 5.35% ± 0.50; retained 100%; directional p = 0.18.
  - Neighbours give 4.1–4.9%.
  - The pilot itself shows mild N–S anisotropy: correlation at 10–25 km is 0.019 for N–S pairs against 0.003 for E–W pairs. E–W-elongated fields are rejected by the directional screen (p ≤ 0.03).
  - The plan names direction-dependent correlation as uncovered but gives no size for the risk.
- **Range.** Exact Cholesky fields that the pilot cannot reject, at shares 0.4–0.7 and ranges 180–720 km, give 4.47% ± 0.14 pooled (22,000 replicates; max single run 5.15% ± 0.49). q95 runs 2.26–2.38.
- **The plan's sentence is wrong.** §2 says q95 "stays at 2.30–2.31 there, below C2". That compares 2,000-replicate values on a 1,024 km grid against a C2 from 4,000 replicates on a 512 km grid. On the same grid, the 180 km model gave 2.29, so q95 does not fall beyond 180 km. The exact screens also retain 0.45/240 and 0.55/360, so the set does not "close" at 240 km (0.4) and 360 km (0.5).
- **Fix, before any outcome request:** either
  - add directional correlograms and anisotropic fields to the screen, use exact (or ≥2,048 km domain) fields out to about 1,000 km, recompute C2 and C1 (expect C2 ≈ 2.47) and re-freeze as v1.4; or
  - keep C2 and replace the §2 sentence with the quantified residual risk: worst case found ≈5.9% two-sided, of which the false-SUPPORTED share is ≈2.7%.

**M2. S13's critical value C2_M2 = 3.74 under-covers credible fields.**

- With exact fields, the binding model's q95 under M2 is 3.89. The retained long-range models give 3.78–4.07, and pooled false calls at 3.74 are **6.0% ± 0.16** (22,000 replicates).
- The frozen `exploratory_long_range.json` already shows 3.84 and 3.81, but the plan does not mention it.
- Cause: the grid stops at 180 km, and the 512 km periodic grid clips about 1% of the spectrum at 180 km. The builder computed that clipped share at 06:59Z; the command is not in the record.
- S13 is also exposed to reporting-agency composition on this design. The pilot's M2R residuals show strong agency effects (F = 23.6). Applying the pilot's agency effects to this design implies a bias of −1.7 SD for M2 against −0.05 SD for M2R.
- **Fix:** recalibrate C2_M2 (≈4.1) over the extended set using exact fields, or label S13's interval as approximate. Note the agency exposure in §7.

### Minor

- **m1. Command record (§3).** "Only a bare invocation of the extractor is skipped now" is false. The PAT text filter drops 46 Bash calls between 06:51 and 09:15Z, including:
  - `python3 pilot_reread.py`, which wrote the frozen PILOT_REREAD.json;
  - the v1.3 re-run of `check_predictors.py`;
  - the clipped-spectrum check on the 512 km grid.

  The rest are read-only monitors. Part 1 used the same filter, so "every command … touching these files" is overstated there too. The gap paragraph omits two things: the first v1.3 calibration was launched at about 02:51, and two third-audit logs were added to `history_v1.2/` at 02:49. Those two files are covered by no FREEZE, only by SHA256SUMS. `exploratory_Q.py` was written at 07:09Z and deleted unrun at 07:18Z; it is in the record but not in the §0 list. **Fix:** add an addendum listing every Bash call since 06:51Z, and reword §3.
- **m2. Screen design.** The screen has four weaknesses:
  - 200 replicates estimate each 2.5% tail from about 5 draws, so boundary decisions depend on the seed;
  - a box of two marginal 95% intervals rejects a true model up to about 10% of the time;
  - fields and blocks are screened on different statistics, never jointly;
  - long-range verdicts depend on the field embedding.

  As a result, C2 is set by a model that a precise screen on the registered grid would drop, which would give C2 = 2.28 and under-cover the long-range boundary. **Fix:** use ≥1,000 replicates, a joint statistic (correlogram + ANOVA + directional) and exact fields.
- **m3. Wording.**
  - "Every error model that the pilot's residuals cannot reject" (§0) is overstated: the set covers grid exponential fields and 20 km blocks only.
  - "Up to 180 km" understates the range; the pilot cannot exclude 720 km.
  - "Closed within the grid" holds only in the share direction.
  - The README's "holds up at 5% under every credible error model" covers 13 boundary models.
  - "v1.3 fixes all of them" is only partly true for m3 of the third audit.
- **m4. Compartment-level effects are outside the family.**
  - **Pilot evidence:** residuals cluster by labB compartment. ANOVA share is 0.080 under M2 (p = 5e-8) and 0.037 under M2R (p = 0.005).
  - **Exposure:** the regressor is constant within a compartment. Σ_c(Σh)²/Σh² is 14.4, against 4.97 for blocks, and 32% of Σh² sits in 272 compartments that span more than one block.
  - **Effect:** false calls are 4.6% at share 0.05 and 5.6% ± 0.4 at 0.08. Combined with blocks or fields they give 5.3–5.4%, but the plan's correlogram rule rejects those combinations because the fitted range is too short.
  - **Fix:** add the compartment ANOVA to the screen, or use clusters merged across compartments.
- **m5. Trivial code points.** CALIBRATION.json is loaded from the script's directory but verified in the working directory. A missing OUTCOME_FETCH.json raises a traceback rather than a clean refusal. OUTCOME_FETCH.json itself is trusted locally. S9 (A50, M2) uses C2, the M2R value.

### Also tested (no over-call)
None of these exceeds 5%:
- Gaussian-covariance smooth fields: 2.7–3.8%.
- Skewed, heteroskedastic noise resampled from pilot residuals: 1.9–2.3% alone; 4.2% with the binding field.
- Agency random effects at share 0.052: 4.7%.
- Block + field and two-scale combinations at the retained boundaries: all rejected by the pilot (p_share ≤ 0.03); modest retained versions give 2.8–4.5%.

Scripts and outputs are in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit4_p1c/` (`scripts/`, `out/jobA–J*.json`, `equiv_run/`, `vtest_SYNTHETIC/`).

Worth remembering: P1C v1.3 audit 4 found no critical issue. Moderate: anisotropic N–S fields over-call at about 5.9%, and S13's C2_M2 = 3.74 under-covers (about 6%).
