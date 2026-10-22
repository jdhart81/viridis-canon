<!-- Independent audit report, reproduced verbatim. Audited version: v1.0 (frozen 2026-10-20 23:58:20 EDT). Delivered 2026-10-21 00:20 EDT. The auditor was a separate Claude agent that had not built the study; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the auditor's scratch scripts are not shipped. -->

## P1C independent audit: report

**Bottom line:** all 8 mechanical checks pass. The freeze is intact, the predictor files contain no outcomes, the samples are disjoint, the code matches the pilot exactly and every number in the plan reproduces. But one blindness claim in the frozen plan, about MTBS fire perimeters, is wrong for part of the region. It should be corrected before the plan is published.

I changed nothing in p1, p1c or p1c_registration: a before/after listing of names, sizes and modification times is identical. I never requested outcomes and made no network calls. My work is in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit_p1c`.

### Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Freeze integrity | PASS | All 20 frozen files match their hashes. `ots info` shows `eef249f9…`, which equals `sha256sum FREEZE.json`. All 4 attestations are still *Pending* (calendar times 03:58:21–23Z), none confirmed on Bitcoin yet. |
| 2a | No outcome files | PASS | No outcomes.csv, results.json or REGISTRATION.json anywhere under p1c. |
| 2b | Predictor columns | PASS | The 43 columns include no fire_size, cont_\*, mtbs_\*, complex_name or ics_209\*. |
| 2c | Raw ignition fields | PASS | 14,105 records; the keys are exactly the 12 allow-listed fields; geometry has only x and y. |
| 2d | MTBS file | PASS | 262 features, each with only a `year` attribute. (Caveat: see issue C1.) |
| 2e | `fire_size` grep | PASS | 11 files hit, all code or prose. No data file under p1c or raw/ contains it. |
| 3 | Disjoint and complete | PASS | 0 fod_ids shared with the pilot table, the pilot outcomes or the pilot raw records. fod_id is unique. 14,105 raw records in the box equals 14,105 table rows, and the id sets are equal. |
| 4 | Outcome guard | PASS (with caveat M1) | `--check` exits 1 with "G2 FAIL: REGISTRATION.json missing". There is no fetch path when a guard fails or `--check` is passed. In a sandbox copy, a REGISTRATION.json with a wrong SHA-256 or MD5 was rejected. |
| 5 | Plan vs code | PASS (nits in m5) | Single primary is B, M2. Decision: β ± 1.96·SE with CR1 by year; lower bound > 0 is SUPPORTED, upper bound < 0 is CONTRADICTED. BETA33 = 0.04152513098030266, equal to the formula. The diff against the pilot's `run_test_dev1.py` shows exactly the 5 changes the plan lists, and the model functions are untouched. |
| 6 | Numbers | PASS | Every number in §§3–5 matches the JSON files and the config. sigma (1.0797, using n−k), the iid SE and deff (1.0640) recompute from pilot data. sd_res is 0.71106 with n = 11,314. Recomputed SE: 0.015189 (base) and 0.024625 (pessimistic). Recomputed power: 0.9861 / 0.7805 / 0.5476 (base) and 0.7276 / 0.3923 / 0.2497 (pessimistic). All match the plan. |
| 7a | Build equivalence | PASS | Rebuilt table sha256 is `57118595…`, byte-identical to the frozen pilot table. 49 s, 2.8 GB peak memory. |
| 7b | Model equivalence | PASS | B, M2 gives β 0.06317647448409425 and SE 0.027318251774805232 exactly. A50, M2 is identical to the pilot results. In fact all 24 pilot outputs reproduce exactly (bootstrap CIs, H3, H4, every sensitivity), not just the 6 that `EQUIVALENCE.json` compared. |
| 8 | Package | PASS | `sha256sum -c` passes for all 24 files. Both gunzipped CSVs match their frozen hashes. All 18 other frozen files are present and byte-identical. |

The cached bytecode in `p1c/__pycache__` is byte-identical to fresh compiles of the frozen sources, so no stale code ran.

### Issues

**Critical: fix before publishing the plan**

**C1. The MTBS blindness statement is inaccurate for part of the region.**
- **What the plan says:** "requested as geometry only… no size attribute was ever received" (line 90). Also line 7, "no fire size… for any ignition in this region has been requested", and line 60, "fixed before any data from it were fetched".
- **What the pilot did:** the frozen pilot `fetch_data.py` (line 168, sha256 `927e911d…`) requested MTBS with `fields='*'`, at 19:53 and again at 20:06. That means all attributes; MTBS boundary records normally include burned acreage.
- **Overlap with this region:** the pilot's download area covers 1,697 of the 14,105 confirmatory ignitions. 63 of the pilot's 275 perimeters (61 of them from 1992–2024) reach into the confirmatory region. All of this happened before the region was chosen (config written at 20:33).
- **The confirmatory MTBS fetch can't be verified.** It ran at 21:15–21:17 using a version of `fetch_data.py` that wasn't kept:
  - the copy saved at 21:05 (`scratchpad/dry/p1c/fetch_data.py`) uses `fields='*'`;
  - the frozen file was last changed at 21:34, after the fetch;
  - `requests.log` doesn't record the request bodies, so the fields actually requested aren't logged.
- **The polygons encode size anyway:** the stored perimeter shapes give the burned area of every fire of 1,000 acres or more.
- **What I did not find:** any evidence that a size value was stored or looked at. The stored files keep only `year`. The same caveat applies to the pilot's line "frozen… before any fire size was fetched".
- **Fix:** before publishing, re-freeze as v1.1 with a corrected disclosure. Keep v1.0 and its timestamp as history. Optionally pre-register a sensitivity analysis that drops the 1,697 ignitions inside the pilot's download area.

**Moderate**

**M1. The registration guard (G2) can be satisfied by a hand-written file.** It checks a local REGISTRATION.json and never contacts Zenodo or GitHub. In the sandbox, a file with the correct local hashes and an invented DOI (`10.5281/zenodo.1`) or a fake repo passed every guard (exit 0). Also, `fetch()` doesn't call `guards()` itself.
- **Fix:** do the anonymous download-and-hash check inside `fetch_outcomes.py` right before fetching, and call `guards()` from `fetch()`. Log every outcome request with its body, and timestamp outcomes.csv and that log immediately after fetching.

**M2. Both studies use the same 33 years, which are the units of inference.** The pilot and the replication both cover 1992–2024 and cluster by year. Adjacent regions share fire seasons, so year-specific effects can push both estimates the same way. The difference test and the pooled estimate assume the two are independent, and this isn't disclosed in §7.
- **Fix:** pre-register a stacked model (both regions, separate slopes, CR1 by year) to estimate the covariance for the difference test and pooled estimate. Add a leave-one-year-out check. Disclose it.

**M3. The blindness evidence isn't frozen or published.** None of these are in FREEZE.json or the package: `raw/fpafod_ignitions_blind.json`, `raw/mtbs_perims.json`, `requests.log`, the fetch and chain logs. The log keeps only the URL (cut at 300 characters), not request bodies. Outcome fetches aren't logged in either study. The frozen `fetch_data.py` post-dates both the ignition fetch (20:56) and the MTBS fetch, and the line numbers in the 20:50 and 20:55 tracebacks show it was being edited during the fetches.
- **Fix:** add these files to the v1.1 freeze and deposit them, and say which code version did each fetch.

**M4. Some predictors post-date the fires (inherited from the pilot).** LANDFIRE 2024 fuels are updated after recent fires. So for roughly 2014–2023 ignitions, the fuel group at the ignition cell partly reflects that fire's own aftermath. The 2024 roads (TIGER) may also include roads built after fires. The planned anachronism check, S8 (2010 and later), concentrates on exactly those fires rather than avoiding them.
- **Fix:** disclose this. Add a sensitivity analysis using the nearest earlier LANDFIRE version, or one without the fuel-group term.

**Minor**

- **m1. Timestamp not yet confirmed.** The plan says it is "timestamped on the Bitcoin blockchain", but the proof is only submitted to calendars so far. Run `ots upgrade` and ship the upgraded `.ots`, or reword.
- **m2. Synthetic-validation criterion and calibration.** The pass criterion changed after run 1 failed. This is disclosed, but nothing independent shows the 3.2–6.8% band was fixed in advance. The calibration also uses independent errors only, so "the rule is calibrated" doesn't cover year- or space-correlated errors, where CR1 with 33 clusters and 1.96 can over-reject. Reword, or add a correlated-error calibration.
- **m3. Outcome fetch is unchecked.** It queries the live "CurrentEdition" service without checking the edition, how many records came back, or whether year, date and location still match the frozen records. `run_test.py` silently drops ignitions with no outcome. The plan defines neither a minimum retrieval rate nor the NOT ESTIMABLE outcome. Request the blind fields alongside fire_size and assert they match; assert that every id is returned.
- **m4. S9 (two-way clustering) is not a stricter test.** On the pilot its SE (0.0234) is smaller than the year-only SE (0.0273), so "do not explain it away" overstates it. The fallback rule isn't in the prose. The pilot plan required any spatial-block check to be a labelled deviation, and there is no such record. Use max(two-way, year-only) or report both.
- **m5. Small prose and code mismatches.**
  - §4 says "every pilot estimate" reproduces, but `EQUIVALENCE.json` covers only 6 models. The claim is true; I checked all 24.
  - The `run_test.py` docstring lists 3 changes; the plan lists 5.
  - BETA33 uses 1.959964 while the CI uses 1.96 (difference about 1e-5).
  - "Power" includes wrong-sign rejections (at most 0.0006).
  - The H4 restriction to fires of 10+ acres and "lightning" meaning cause = Natural are implicit only.
  - The README says "Everything here was frozen", but README.md and PREREG_TEMPLATE.md are not in FREEZE.json, and it points to `AI_USE_AND_AUTHORSHIP.md`, which isn't in the package.
  - G2 accepts OSF DOIs, but `verify_registration.py` has no OSF mode.
  - Disjointness relies on the lon/lat server query: the box `build_predictors.py` filters on contains 1,000 pilot ignitions. Pilot record fod 60886, at exactly −119.4, sits on the boundary.
  - §1 omits that the pilot had two co-primary definitions (B: p = 0.021 against a Bonferroni threshold of 0.025).

Files are in /tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit_p1c:
- rebuild_pilot/predictors_blind.csv
- model/check7b.py
- model/check6.py
- guardtest/
- diff_runtest_dev1_vs_p1c.txt
- baseline_listing.txt
- after_listing.txt
