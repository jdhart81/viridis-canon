<!-- Independent audit report, reproduced verbatim. Audited version: v1.2 (frozen 2026-10-21 02:30:45 EDT). Delivered 2026-10-21 02:48 EDT. The auditor was a separate Claude agent that had not built the study; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the auditor's scratch scripts are not shipped. -->

## Audit of P1C plan v1.2 (third audit, scoped to what changed in v1.2)

**Bottom line:** the mechanics, blindness and new lists are clean, and the arithmetic producing C2 = 2.31 / C1 = 1.91 is exact. But C2 depends on a fitted field range that the pilot data barely constrain, and the fit is biased low. A same-family error model that the pilot cannot reject needs C2 of about 2.5–2.7, and under it the registered rule over-calls at 6.7–9.3%. That is one critical issue; I found no moderate issues and four minor ones.

Nothing under `/home/claude/p1c`, `/home/claude/p1` or `/home/claude/p1c_registration_v1.2` was modified. All 169 hashes still match after my work, no files are newer than the audit start, and I ran Python with `-B` on scratch copies.

### Item table

| Item | Result | Evidence |
|---|---|---|
| 1a `Field` | OK | Variance is 1.002 on the grid and 1.01 at design points. Correlation at d = 1/5/10/20/30 km is 0.920/0.645/0.414/0.174/0.070 against exp(−d/11.17) = 0.914/0.639/0.408/0.167/0.068. No eigenvalues clipped, and no wrap-around (point span 200×171 km, under half the 512 km grid). |
| 1b Fits | Reproduced, but biased as an estimator | The correlogram is identical to the stored one, and the fits match: 0.0534/11.17; 0.0496/11.71; 0.0277 + 0.0208/15.29; block share 0.0623. The range estimate is biased low (Critical issue). |
| 1c `null_t` / `sim_stats` / `D.stats` | OK | `D.stats` equals `run_test.fit_twoway` and `fit` to ≤ 6e-15 on two draws with field plus block errors. `null_t` reproduces a hand-built draw. The outcome is 0.5·ERC + iid noise + block effect + √vf·field, as the plan describes. |
| 1d Quantiles, max, rounding | OK | Rerunning exp_cross on the calibration seeds reproduces q95 = 2.303227639516545 and q90 = 1.90178 exactly, so ceil gives 2.31 and 1.91. The code hashes stored in CALIBRATION.json match the frozen files. The first run differs from the final one only in `seconds` and the run_test.py hash. |
| 1e Plausible alternative model | **ISSUE (critical)** | Doubled range (22.3 km): q95\|T\| = 2.48 and 6.7% false calls at C2. Ranges of 30–45 km: q95 = 2.71 and 8.7–9.3%. Doubled share: q95 = 2.41, but the pilot rejects it (P = 0.01). |
| 1f Pilot re-read (§1) | OK | Matches `pilot_reread` exactly: T = 2.3126, 5% critical value 2.088, 2.5% critical value 2.384, p = 0.024–0.028. It also holds under the larger-range models (pilot-design 5% critical values 2.02–2.10). |
| 2 S10b / S12 | OK | Independent recomputation with my own ring parsing: 63/61 perimeters; 1,888 / 703 / 1,697 / 2,400 ignitions; identical ID sets. S12's 5 IDs are identical. In run_test.py, S10 has n = 9,941, S10b 9,368 and S12 11,309. (Two further pairs within 5 km at ±1 day fall outside the stated rule; immaterial.) |
| 3 `verify_inputs()` | OK, minor gaps | FREEZE keys and `OUTCOME_FETCH['outcomes_sha256']` match what the code looks up. `--synthetic` is used only by `validate_synthetic.py`. Gaps in m4. |
| 4 Plan text §0–§5 | Mostly OK | Every number checked in §1, §2, §5, the small-telescopes figures, the sample counts and the §0 hashes and times matches the JSON records. Two statements are false (m1, m2) and one completeness claim is false (m3). |
| 5 Freeze / OTS / package | OK | 169/169 hashes match. The `.ots` digest equals sha256(FREEZE.json) (`d19237dd…`, sha256 op). `sha256sum -c` passes (46 entries). 129 package members (plain, gz, tar) match FREEZE.json with 0 mismatches. The history tarballs match their own v1.0/v1.1 freezes. 40 large raw inputs are frozen but not shipped, as in v1.1. |
| 6 Blindness | OK | No outcome, results, registration or fetch files exist under p1c. All 12 confirmatory-ID `outcomes.csv` files in the scratchpad are 100% class 'SYN'; the other copies hold pilot IDs only. The pre-freeze `fetch_outcomes.py --check` stopped at G2 (no REGISTRATION.json). |

### Critical

**C1. C2 = 2.31 rests on plug-in field parameters from a correlogram fit that is strongly biased toward short ranges.**

*Bias check.* I simulated the fitted field on the pilot design, residualized on B/M2, recomputed the correlogram and refit it exactly as `simcal` does (150 replicates each):
- **True range 11.2 km:** the median fitted range is 6.6 km (q90 9.2). The pilot's own 11.17 km sits at the 97th percentile of its own model.
- **True range 22.3 km:** median fitted range 8.7 km; the fit comes out ≤ 11.17 km 85% of the time.
- **Share 0.060, range 30 km:** fit ≤ 11.17 km 71% of the time.
- **Share 0.065, range 45 km:** fit ≤ 11.17 km 62% of the time.

The plan reads the pilot correlogram as near 0 beyond 40 km, but that does not exclude these ranges. Residualization plus pair-count weighting pushes the tail to zero or below; the pilot's −0.006/−0.009 at 45–55 km is what these longer-range models produce.

*Effect on the confirmatory blind design* (fresh seeds):

| Error model | q95\|T\| | q90\|T\| | False calls at C2 = 2.31 | Reps |
|---|---|---|---|---|
| Range 22.3 km | 2.48 | 2.04 | 6.7% (above the plan's own 0.058 limit) | 3,000 |
| Share 0.06, range 30 km | 2.71 | — | 8.7% | 2,000 |
| Share 0.065, range 45 km | 2.71 | — | 9.3% | 2,000 |

*Fix, before any outcome request:* re-derive the field parameters with a bias-aware method. Either use indirect inference (choose the share and range whose simulated fits match the observed 0.053 / 11.2 km), or take C2 as the maximum q95 over the share/range set the pilot cannot reject. On this evidence that gives C2 ≈ 2.7 and C1 ≈ 2.3. Alternatively, switch to an SE robust to long-range correlation (blocks of 50 km or more, or Conley SEs with a long bandwidth) and recalibrate that. Then redo the power and small-telescopes numbers (power at β₃₃ will fall), update §2 and §5, and re-freeze as v1.3.

### Moderate
None found.

### Minor

**m1. §0 table, "00:50 … between those figures", is false on both counts.**
- The frozen transcript shows the 0.065 tolerance was set at 00:41:55, in the same command as the t × max switch.
- Frozen `history_v1.1/validate_synthetic.py` gives the rationale as "nominal 0.05 plus 1.5 points".
- 0.065 lies above all four figures (4.65 / 5.75 / 5.6 / 6.4%), not between them.
- *Fix:* correct the time and the rationale. The 11.7% figure (00:32 run, seeds 20000–20999) and the exploratory 5.75 / 6.4 / 4.65 / 5.6% figures do check out.

**m2. §2's "fresh-seed shares scatter by about ±0.4 points" is understated.**
- The registered rule under exp_all moved +0.72 points (4.53% → 5.25%). The v1.1-rule column moved +0.91 (exp_all) and +0.89 (block_exp).
- A third seed set (my 6,000 replicates) gives 5.37% and q95 = 2.353 under exp_all, so the table's 2.250 is a low draw. The pooled false-call share under exp_all at C2 is about 5.0–5.3%.
- *Fix:* say "up to about ±0.9 points" and report pooled values.

**m3. §3's claim that the transcript holds every command and code edit from 20:33 ET onward is not quite true.**
- The final pre-freeze command (02:30:42 ET) is missing from the frozen transcript because `extract_transcript.py` drops any command that contains its own name.
- That command edited `PREREG_TEMPLATE.md`, adding the "Checking" sentence (including the ±0.4 claim) and the `history_v1.1_dev` freeze line. It then ran `fill_prereg`, `extract_transcript`, `freeze`, the timestamp stamp and `fetch_outcomes --check`.
- *Fix:* record that command in a post-freeze addendum, and make the extractor skip only a bare self-invocation.

**m4. `verify_inputs()` can be bypassed silently.**
- It relies on `assert`, which `python -O` or `PYTHONOPTIMIZE` strips without warning. That also removes the pilot-disjointness assert.
- It hashes `run_test.py` in the working directory rather than the script actually executing.
- It trusts the local FREEZE.json.
- results.json does not record whether verification ran or `--synthetic` was passed.
- *Fix:* replace the asserts with explicit exits; hash `__file__`; check FREEZE.json against `OUTCOME_FETCH['g2_downloads']['FREEZE.json']['sha256']`; write `inputs_verified` into results.json; refuse `--synthetic` unless every `fire_size_class` is 'SYN'.

### Files
All audit scripts and logs are in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit3_p1c/`. The C1 evidence is in `jobD_plaus.py`, `jobE_match.py`, `jobC_alt.py`, `jobF.py` and `jobC.log`; the exact reproduction of C2/C1 is `jobB_exact.py` with `jobB.log`.
