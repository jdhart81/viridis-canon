<!-- Independent audit report, reproduced verbatim. Audited version: v1.4 (frozen 2026-10-21 08:15:51 EDT). Delivered 2026-10-21T12:43:38.560Z. The auditor was a separate Claude agent that had not built the study; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the auditor's scratch scripts are not shipped. This report is not covered by FREEZE.json; see ADDENDUM_v1.4.md. -->

## Audit 5 of P1C v1.4 (frozen 08:15:51 EDT, FREEZE.json sha256 4efb62b8…)

**Bottom line.** v1.4 does what it says. The stress set follows its decision record, and that record was written before any stress model was simulated. The new exact machinery is exact, and the binding values and boundary screens reproduce bit for bit. The final values equal the max rule and are the ones every script uses. Freeze, package and blindness check out. There is no critical and no moderate issue, and there are six minor ones:
- the compartment-label files that the compartment models depend on are not frozen or shipped;
- S13's critical value C2_M2 has no margin at the edge of the share grid;
- some wording overstates.

All three protected folders are unchanged: 767/767 SHA-256 values and 791/791 path, size, mtime and mode lines match, including directories, and no file is newer than the audit start. All Python ran with `-B` on copies, with no network.

| # | Result | Evidence |
|---|---|---|
| 1 Stress set vs decision record | OK (disclosure: m4) | **Candidates:** 90 = 48 S-A (N–S and E–W; four range pairs × six shares) + 35 S-L (180–720 km × 0.3–0.9) + 7 S-C (0.02–0.15), equal to the record; names match `CRITICAL_VALUES.json`. **Screens:** all 1,000 replicates on the pilot design, with the record's rules; the observed fit (0.0534, 11.17 km) and compartment share (0.0800) reproduce exactly. **Simulation:** 52 retained (32/16/4), all at 4,000 replicates for both statistics, jitter 1e-6 throughout. **Max rule:** holds; see item 4. **Order:** the decision record was written at 10:48:26.865Z (content identical to the file, mtime 10:48:26.891Z). Then the stress code (10:49:28Z), `calibrate_stress.py` (10:50:06Z), the `run_test.py` edit (10:50:31Z), the smoke test (10:50:43–10:51:04Z) and the registered run (10:51:09Z, 2,123 s). The transcript from 09:00Z to 10:48Z shows no stress simulation. **Nothing tuned:** all code mtimes precede the smoke test, and the code hashes in `CRITICAL_VALUES.json` equal the frozen files. |
| 2 Exactness | OK | **Cholesky:** on this region's design (n = 11,314, binding model), max\|LLᵀ − (C + 1e-6 I)\| is 2.2e-15 on a 1,500-point subsample and 8.3e-15 on 6 full rows; C was built independently and the upper triangle is exactly 0. **Draws:** 20,000 draws on the pilot design. Field: slope of empirical on theoretical covariance 0.999; N–S/E–W correlation at 10–40 km 0.1542/0.0589 against 0.1541/0.0589. Compartment 0.12: slope 1.004; within-compartment covariance 0.1376 against 0.1371. **Labels:** for all 2,677 pilot and 11,314 confirmatory points, the labB area at (row, col) equals the frozen Aenc_B (≤3e-16), with no zero label; the code arrays match mine (555 and 2,065 compartments). Rebuilding this region from frozen code and raw inputs gives a byte-identical table (2229c814…) and identical label arrays; the pilot's labels match the builder's equivalence rebuild. **Hand check:** `fit_twoway` T equals `null_t_pair_stress` to ≤1.1e-12 for the binding field (replicates 0 and 1234) and comp 0.12 (0 and 333), under both M2R and M2. |
| 3 Reproduction | OK | **Binding model** (k = 15, seed 21,500,000): q95 under M2R = 2.527546606809679 exactly; all 10 recorded statistics are identical. The C1 binding (q90 2.0709732561882737) and the C2_M2/C1_M2 binding (3.9266074617609363 / 3.388271992246296) are also identical. **Screens:** bit-identical for the binding model and the nearest boundary cases: aniso N–S 0.15, 10×120 (retained by 0.0009); long 0.5/240 (rejected by 0.0011); aniso E–W 0.2, 20×180. **`CALIBRATION_REPRO.json`:** re-run on a copy gives a byte-identical file. The v1.3 code hashes equal `CALIBRATION.json`'s. The simcal diff is additions only, and the `run_test.py` changes are outside the calibration path. |
| 4 Final values and their use | OK (code points: m6) | **Values:** C2 = max(2.37, 2.53); C1 = max(1.95, 2.08); C2_M2 = max(3.74, 3.93); C1_M2 = max(3.22, 3.39). Binding labels are correct. **Use:** nothing is hard-coded. `freeze.py`, `validate_synthetic.py` and `blind_design.py` assert equality with `CRITICAL_VALUES.json`, and their records hold 2.53/2.08/3.93. `pilot_reread.py` takes its stress models from `CRITICAL_VALUES.json`. **`verify_inputs()`:** 15 scenarios, identical with and without `-O`. A missing fetch record, `FREEZE.json` or critical-value file gives a clean VERIFY FAIL; so does a modified loaded file (script folder ≠ working folder), a modified working-folder file, outcomes, script, `CALIBRATION.json`, or a `FREEZE.json` that differs from the public copy. A non-SYN row with `--synthetic` is REFUSED. **End-to-end:** a verified run on synthetic outcomes gives `inputs_verified` true, M2R, n 11,314, 24 regions, 75 blocks, C2 2.53, S13 crit 3.93, and S10/S10b/S12 n = 9,941 / 9,368 / 11,309. |
| 5 Plan vs records | ISSUE (minor: m3, m4, m5) | **Numbers:** all match. §1 table 13×6 and the summary (2.72/3.12/2.69/3.11; p 0.033/0.087); §2 q95 table (73 values + 67 dashes), blocks, 2.37/1.95, reference rows, the 8×3 stress table, the NOT REPLICATED shares; §5 power 5×4 and S13 (0.16/0.44/0.64/0.73), SE, SDs and n's; §0 freeze times and hashes; §6 3.93. **Coverage:** 213/213 Bash/Write calls from the transcript start (06:51:29Z) to the freeze command (12:15:47.486Z) are present, in order and identical. No bare extractor call falls in the window, and the 6 recovered rows equal the third audit's view. **Spot checks:** `pilot_reread.py` at 08:36Z and 11:26Z, `check_predictors.py` at 07:30Z, and `exploratory_Q`. **Redaction:** 7 flagged rows and 19 tokens, all matching the two hashes. Applying the redaction to the transcript reproduces every row exactly, so nothing else changed. **Wording:** see m3–m5. |
| 6 Audit 4 findings | see right | **M1:** fixed. Audit 4's A.15/10×120 and A.13/15×90 give 4.0% and 3.9% at 2.53; exact fields to 720 km; the wrong §2 sentence is gone. **M2:** mostly fixed (C2_M2 = 3.93; agency exposure in §7). The boundary gap is neither fixed nor disclosed (m2). **m1:** fixed; wording in m3. **m2:** disclosed as residual risk in §2. **m3:** fixed, but new overstatements appear (m5). **m4:** fixed by S-C (max q95 2.471 < 2.53); combinations disclosed as not covered. **m5:** label loading and the missing fetch record are fixed; S9 is relabelled. OUTCOME_FETCH.json is still trusted locally, neither fixed nor disclosed; a missing outcomes.csv still gives a traceback. |
| 7 Freeze and package | OK | FREEZE 236/236. The `.ots` has a sha256 op and the FREEZE digest at offset 33 (3 pending calendars); the v1.0–v1.3 `.ots` digests match. SHA256SUMS 61/61, nothing stray. 6 gz and 45 plain files match FREEZE. `logs.tar.gz` holds exactly the 109 frozen logs; the dev tarballs (8/17/1) match. The v1.0–v1.3 tarballs match their own freezes (18/23/27/29 members, 0 bad), and their FREEZE and `.ots` equal the v1.4 entries, v1.3's included. |
| 8 Blindness | OK | No outcome, results, registration or fetch-record file in p1c or the package; `pilot_outcomes.csv.gz` holds 4,642 pilot IDs and 0 confirmatory ones. All 18 confirmatory-ID synthetic outcome files are 100% 'SYN'. `fetch_outcomes.py --check` on a copy under `unshare -n -r`: G1 passed, then "G2 FAIL: REGISTRATION.json missing" (exit 1), nothing written. |

### Critical
None.

### Moderate
None.

### Minor
- **m1. The compartment labels are not frozen or shipped.**
  - `p1c/compartments_static.npz` and `p1/compartments_static.npz` feed S-C, the pilot re-read, validation and power. S-C comes close to binding (2.471 against 2.528) and sets the re-read's 2.72/3.12.
  - Neither file is in FREEZE or in any code_sha256 record. `calibrate_stress.py` and `pilot_reread.py` also hard-code `/home/claude/p1/`, so the stress set cannot be re-run from the package.
  - The labels can be rebuilt exactly from frozen code and inputs (shown above).
  - **Fix:** freeze both files or a hash of their labB arrays; ship a per-ignition compartment ID; use `../p1/` paths; amend §8.
- **m2. S13's C2_M2 has no margin at the grid boundary.**
  - Fresh-seed long-range fields between grid points sit just outside the screen. 0.65/480 is rejected by 0.0011 and 0.75/720 by 0.0025. Under M2 they give q95 of 4.05 and 4.09, i.e. 5.6% ± 0.4 and 6.4% ± 0.4 false calls at 3.93.
  - Audit 4's retained 0.65/500 gave 4.07.
  - The same check for C2 is clean: N–S 20×180 at 0.21 and 0.22 is rejected (q025 0.057 and 0.062 against 0.053).
  - §2's "at every share the pilot cannot reject" is true only at grid points.
  - **Fix:** refine the S-L shares to steps of 0.05 near the boundary and recompute (expect about 4.05–4.1), or label 3.93 as approximate in §6. Reword §2 to "at the grid's shares".
- **m3. §3 says "every call", but only Bash, Edit and Write calls are recorded.**
  - 20 other calls in the window are absent: 2 TaskStop (the two disclosed stopped v1.3 runs), 4 shell commands on the author's computer that moved files, 6 Read, and the rest are listing, agent, project and message calls.
  - **Fix:** state the tool scope and list the TaskStop and remote-shell calls.
- **m4. The smoke-test disclosure in §0 is incomplete.**
  - The same command also ran 100-replicate pilot screens of aniso N–S 0.15, 10×60 and of comp 0.08. A unit test on 300 random points ran just before it. The 200-replicate run (seed 999) printed q95 2.402.
  - Nothing was tuned on any of it.
  - **Fix:** describe all three in one sentence.
- **m5. "v1.4 fixes them" (§0) is overstated.** Audit 4's m2 is disclosed, not fixed, and m5's local trust in OUTCOME_FETCH.json remains.
  - **Fix:** reword, and either disclose in §8 that `run_test.py` trusts the local fetch record, or verify its timestamp.
- **m6. Small code points.**
  - `main()` reads outcomes.csv before `verify_inputs()`, so a missing file gives a traceback. A missing frozen input or FREEZE key does the same. All of these still exit 1 without writing results.
  - The `check_calibration_repro.py` docstring says "every statistic", but it compares only q90 and q95.
  - `p1c/__pycache__` (06:51, unfrozen) would be used when helper scripts import `run_test` or `simcal`. `run_test.py` run as the main script is unaffected.
  - **Fix:** call `verify_inputs()` first and add existence checks; reword the docstring; delete `__pycache__` before freezing.

Scripts and outputs are in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/audit5_p1c/`: `scripts/`, `out/` (job A, job B, between-grid and package checks), `vt/` (the `verify_inputs` scenarios and the end-to-end run) and `rebuild/`.

Worth remembering: P1C v1.4 audit 5 found no critical or moderate issue. The main minor findings are the unfrozen compartment labels and S13's C2_M2 having no margin at the grid boundary (5.6–6.4% just outside the screen).
