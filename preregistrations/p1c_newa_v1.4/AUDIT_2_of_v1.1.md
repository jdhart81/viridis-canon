<!-- Independent audit report, reproduced verbatim. Audited version: v1.1 (frozen 2026-10-21 00:55:41 EDT). Delivered 2026-10-21 01:44 EDT. The auditor was a separate Claude agent that had not built the study; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the auditor's scratch scripts are not shipped. -->

**Independent audit of P1C v1.1**

The first audit's mechanical fixes hold. The biggest new problem is the new primary rule: its "calibrated" claim only holds under an error model that the pilot's own data do not support.

Ground rules were kept. Nothing under `/home/claude/p1c`, `/home/claude/p1` or `/home/claude/p1c_registration_v1.1` changed: before/after listings and hashes are identical. I made no network requests; guard tests ran on a symlinked copy with `urlopen` blocked and the network calls stubbed. No confirmatory outcome exists anywhere on disk: all 13 confirmatory `outcomes.csv` files in the scratchpad are synthetic (every row has size class `SYN`).

**Re-runs**
- Pilot rebuild with `/home/claude/p1c/build_predictors.py`: sha256 `57118595…` ✔.
- Extra check: the confirmatory table also rebuilds byte-for-byte from the frozen raw inputs (`2229c814…`). `compartments_static.npz` rebuilds identically too, so it being unfrozen is harmless.
- `fetch_outcomes.py --check` run from `/home/claude/p1c`: G1 passes silently, then "G2 FAIL: REGISTRATION.json missing", exit 1 ✔.
- `FREEZE.json`: 126/126 hashes ✔.
- Package: `sha256sum -c` passes 39/39; the 5 `.gz` files, 7 plain copies and the v1.0 pair all match `FREEZE.json`; `logs.tar.gz` has 50/50 members matching ✔.

| Finding | Status | Evidence |
|---|---|---|
| C1 | PARTLY | Figures check out: 63 pilot perimeters reach the region (61 from 1992–2024), out of 275; 1,697 ignitions lie in the pilot compute box. `raw/mtbs_perims.json` has 262 records carrying only `year`. S10 is coded as described (keeps 9,941, drops 1,373). The claim that this region's MTBS fetch used `fields='OBJECTID'` rests in the frozen files on a bare "ok" line. Only the unfrozen session transcript shows it was one command (01:15:50Z: edit, then `fetch_data.py mtbs`; first MTBS request at 21:15:53). S10 misses part of the exposure (new issue 3). |
| M1 | FIXED | Tested with stubs: a missing registration, a failed download or a 1-byte-different public copy each stops at G2 with zero service requests. `fetch()` calls `guards()` first. 71 POSTs and 1 GET are logged. R1 (missing or duplicate records) and R2 (latitude off by 1e-6) both block `outcomes.csv`. `--check` makes no outcome request. |
| M2 | FIXED | Stacked point estimates equal the separate fits (difference ≤6e-15). The joint covariance matches my independent computation exactly: 33 merged year clusters, 109 blocks (7 shared). The difference test and GLS pooling use the joint covariance. Leave-one-year-out is correct (32 df left after dropping a year → t on 31 df). |
| M3 | PARTLY | Every listed item is frozen and every hash checks. But `logs/` is a hand-picked subset (new issue 4). |
| M4 | FIXED | The §3 disclosure is present; S11 (no fuel-group term) runs. |
| m1 | FIXED | The `.ots` file commits to FREEZE sha `efd026…` with 4 pending attestations. The README's "is a proof" slightly overstates a pending proof. |
| m2 | PARTLY | The criterion history is disclosed, but the intermediate rule and the exploratory run are not (new issue 6). The correlated-error calibration only uses errors aligned with the 20 km blocks. |
| m3 | FIXED | R1 and R2 are registered and enforced before `outcomes.csv` is written. |
| m4 | FIXED | `DEVIATION_2.json` (04:46Z, before the freeze) labels the pilot spatial check exploratory. |
| m5 | Mostly FIXED | Equivalence covers 23 outputs / 233 values with 0 mismatches (I re-ran it). Power is defined as P(SUPPORTED). H4's 10-acre rule, "lightning = Natural", the explicit lon/lat filter and OSF removal are all done. **PARTLY** on two points: the co-primary note in §1 (new issue 2), and the `run_test.py` docstring, which lists the changes but has stale numbers (new issue 10). |

**The new primary rule**
- **(a)** `simcal.Design.stats` matches `fit_twoway`, and an independent QR implementation, to ≤5e-14. I tested 12 replicates: β of 0, 0.063 and 0.3; block variance from 0 to 4× the pilot's; heavy-tailed noise. Degrees of freedom and t are identical.
- **(b)** It is a correct one-way ANOVA method-of-moments estimator; I reproduced 0.0714 / 1.0744 independently.
  - Maximum likelihood gives 0.085.
  - Applied to OLS residuals the estimator runs about 11% low, with SD 0.022.
- **(c)** The §2 table matches `SYNTHETIC_VALIDATION.json`; re-running with the same seeds reproduces all 18 shares exactly.
- **(d)** PARTLY. The 0.065 tolerance being set after an exploratory run is disclosed. The rest of the history is not (new issue 6).
- **(e)** The change is defensible.
  - The new interval contains the v1.0 interval for every possible dataset (t = 2.037 > 1.96, and the max SE ≥ the year-only SE), so it cannot make SUPPORTED easier.
  - Downsides: it makes NOT REPLICATED harder (new issue 9), the v1.0 text is not public (new issue 5), and the calibration is not robust (new issue 1).
- **(f)** The §5 power table matches `BLIND_DESIGN.json`, is P(SUPPORTED) under the registered rule, and reproduces exactly.

**New issues**

**Critical**

1. **The calibration only works if spatial correlation lines up exactly with independent 20 km blocks.**
   - The pilot's residuals show correlation across block boundaries, between different-year pairs: 0.016 at 0–10 km and about 0.007 at 10–40 km. An exponential model fitted to the pilot's correlogram has a range of about 11–14 km.
   - Under error models consistent with that, the registered rule's false-call share on this design is above the plan's own 6.5% bar in two of the three models I tried, and at the bar in the third:
     - exponential field fitted to the correlogram: 8.1% (10,000 reps);
     - fitted block + continuous model: 7.3% and 6.4% in two runs;
     - recorded block model plus a 1% cross-block component: 6.35%.
   - False SUPPORTED runs about 3.2–4%, against 2.5% nominal.
   - The rule *is* robust to the size of the block variance: 5.2–5.3% at 2–3× the pilot's.
   - So §2's "this rule does not [over-call]" is model-dependent.
   - **Fix, before publishing:** calibrate under a spatial model fitted to the pilot. A simulated critical value of about 2.17–2.2 (instead of 2.037) restores 5%. Alternatives are Conley spatial-HAC SEs with a 30–50 km bandwidth plus year clustering (I did not test this), or at least stating the realistic α. 40 km blocks alone were not enough (7.5%).

**Moderate**

2. **The pilot's multiplicity is misdescribed in §1.**
   - The registered pilot rule was a 95% CI for each definition, with either one counting (see the pilot plan and `run_test_dev1.py`'s "SUPPORTED BY"). The Bonferroni split was added afterwards.
   - At the 0.025 level that §1 cites, the pilot under v1.1's rule is (−0.0011, 0.1274), p = 0.027: **NOT SUPPORTED**.
   - On its own design, the pilot's rule over-calls at about 8.5%.
   - **Fix:** state the registered pilot rule, label the Bonferroni check post hoc, and report the pilot under the stricter rule at both 0.05 and 0.025.
3. **S10 does not cover the whole MTBS exposure.**
   - 11 of the 63 pilot-received perimeters reach into the analysis box beyond the pilot compute box, up to 34.6 km east.
   - **Fix:** add an S10b that also drops ignitions inside the bounding rectangle of those perimeters. That removes about 1,500 more ignitions (3,195 in the rectangle, 1,503 outside the pilot box). Otherwise, disclose the gap.
4. **The frozen evidence is a curated subset.**
   - At least 7 command outputs from the fetch window are unfrozen, in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/tasks/`:
     - `bp7lrz87f`, `b42g58hf7`, `b6r4qh8vv`, `bd0vydszc`, `bc90e5oj2`, `b639iume7`;
     - `bgqo0etnv`, a retry loop that overlapped the MTBS edit;
     - `b056yjxxo`, the pilot's first MTBS fetch, which crashed at 19:55.
   - The transcript commands for the fetches are unfrozen.
   - So are `/home/claude/p1/raw/mtbs_perims.json` and `/home/claude/p1/raw/requests.log`, which are the basis of the 63/61/275 counts and the 19:53/20:06 times.
   - None of these contradicts the provenance.
   - **Fix:** freeze them plus a transcript excerpt, or stop claiming "every log".
5. **v1.0's plan and code are not in the public package**; only its freeze record and timestamp are. The `history_v1.0` files match the v1.0 hashes. **Fix:** ship them, so readers can see what changed.
6. **The rule went through an undisclosed intermediate version, and the exploratory run is unrecorded.**
   - Around 00:36 the decision rule was coded as 1.96 × max SE (run_test version `76a75c58`, docstring "about 6%"), then changed to t × max at 00:41.
   - The tolerance was written at 00:50. It falls between that intermediate rule's 6.6% and the chosen rule's 5.8%.
   - The exploratory figures (4.7 / 5.6 / 6.7 / 12.0%) are not the first 4,000 of the recorded seeds, which give 4.8 / 6.0 / 6.5 / 13.1%.
   - **Fix:** disclose the sequence, and preserve the scratch `synth_v11/` and `synth_v11b/` copies of `run_test.py` plus the exploratory seeds and output.

**Minor**

7. **G2's "anonymous" download can be fooled.** It goes through `HTTPS_PROXY`, and a credential-injecting proxy could let a private repo pass. GitHub commits can also be deleted later. **Fix:** use Zenodo (already planned), or check that the GitHub API reports `private: false`; record the downloaded hashes.
8. **`run_test.py` never checks its inputs** against `FREEZE.json`, or `outcomes.csv` against `OUTCOME_FETCH.json`. A failed `ots stamp` is silently ignored, and the metadata GET is logged only after it completes. **Fix:** add assertions.
9. **The new rule makes NOT REPLICATED harder, undisclosed.** Under a true null, P(NOT REPLICATED) drops from 86.5% to 85.3% (iid) and from 78.6% to 74.3% (block-correlated). **Fix:** disclose it.
10. **Stale text in frozen code.**
    - `run_test.py` docstring says "7% / 12% / 5–6%"; the record says 5.9 / 12.6 / 4.3 / 5.8%.
    - A comment in `main()` still says "1.96 × max".
    - The `fit_twoway` docstring still calls itself "stricter than the registered rule".
    - `Z95` is unused.
    - `run_chain.sh` is the v1.0 chain and calls `equivalence_model.py`, which no longer exists.
11. **Possible duplicates across the boundary.** 5 confirmatory ignitions have a pilot ignition with the same discovery day within 5 km (1 within 2 km), and the pilot outcomes are known. **Fix:** list them now and drop them in a sensitivity analysis.
12. **README and provenance wording.**
    - The setup steps omit `DEVIATION_2.json`.
    - "Re-fetches" is not byte-reproducible from live services.
    - `requests.log` lists only successful requests.
    - "Only counts per year looked at" is not quite true, since the 63/61 intersection counts were computed.

My scripts are in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit2_p1c/scripts/`. The main ones are `calib_sens.py`, `grf_fit.py`, `joint_fit.py`, `crit_value.py`, `guard_harness.py`, `check_simcal_exact.py`, `check_stacked.py` and `c1_geometry.py`.
