# Addendum 1 to the P1C v1.4 pre-registration

- **Plan:** `PREREGISTRATION_P1C_NEWA_v1.4.md`, sha256 `36e6383621e3f2d228c11ef13300e15b991787d827c242b5caf3e65a61c5f57f`.
  - Frozen at 2026-10-21 08:15:51 EDT.
  - `FREEZE.json` sha256 `4efb62b83fa8f8a5bbb674739f5102dd87bb599a17bf2f0b10f813789019e042`.
- **Written:** 2026-10-21, after the fifth audit and before any outcome from this region was requested. Built at 2026-10-21 13:44:01Z and stamped with OpenTimestamps (`ADDENDUM_v1.4.md.ots`).
- **Status:** Deviation 1 under §9 of the plan.

**This addendum changes no frozen file, model, statistic, critical value or decision rule.** It adds:
- the records the fifth audit asked for;
- two reporting notes on the critical values (m2);
- corrections of wording (§3). Where §3 corrects the plan's wording, read the correction.

## 1. Why an addendum

The fifth audit (`AUDIT_5_of_v1.4.md`) was a verification audit of v1.4. It found no critical and no moderate issue. It found six minor ones, m1 to m6, and none of them changes the primary test or its critical values. Re-freezing as v1.5 would have rewritten `FREEZE.json` for records and wording only. This addendum leaves the frozen plan as it is and adds what was missing, under its own file table (§5) and timestamp. A separate review of its draft is in §6.

## 2. The six findings

### m1. The compartment labels are now hashed and shipped

The compartment models of the stress set, the pilot re-read, the validation and the power analysis read two label files. Both are now in the package:

| Package file | Copy of | labB array |
|---|---|---|
| `compartments_static.npz` | `p1c/compartments_static.npz` (this region) | 6,849 × 7,885, int32 |
| `pilot_compartments_static.npz` | `p1/compartments_static.npz` (the pilot) | 6,448 × 6,021, int32 |

- **Hashes.** The SHA-256 of the raw bytes of each labB array:
  - this region: `ee515ce845f3ee1e22ce309170cd149753f41607d26a2922918879853481c89a`;
  - the pilot: `47f992dbe50ced1fa495a9cca8e66172439930a76e3c50584a1d133a04be6bfa`.

  The file hashes are in §5. `COMPARTMENT_LABELS.json` holds both kinds, plus counts.
- **Per-ignition IDs.** These tables give the definition-B compartment of every ignition, which is the labB value at its cell:
  - `compartment_ids_blind.csv.gz`: all 14,105 ignitions of this region;
  - `pilot_compartment_ids.csv.gz`: all 4,642 pilot ignitions.

  Label 0 lies outside every compartment. No ignition in either B sample carries it (audit 5, item 2).
- **Checks.** `make_addendum_records.py` builds this addendum. It confirms that:
  - each package file is a byte copy of its source;
  - each ID table equals the label array read at the predictor table's cells;
  - the B samples hold 2,065 compartments here and 555 in the pilot, with no label 0.
- **Provenance.**
  - Audit 5 rebuilt this region's label arrays from the frozen build code and the frozen raw inputs, and found them identical.
  - The pilot's labels equal those of the builder's equivalence rebuild (audit 5, item 2). That rebuild reproduced the frozen pilot table byte for byte from the pilot's raw inputs (`EQUIVALENCE.json`), which are not in `FREEZE.json`.
  - For every point of both B samples, audit 5 found each label's area equal to the frozen `Aenc_B`.

  What was missing was a hash fixed before any outcome from this region. This addendum and its timestamp supply it.
- **Re-running from the package.** The README's "Running the code" steps put the pilot's files at `../p1/`. Several readers use the absolute path `/home/claude/p1/`:
  - the scripts `calibrate_critical.py`, `calibrate_stress.py` and `pilot_reread.py`;
  - `simcal`'s pilot functions `pilot_residuals`, `pilot_variance_components` and `PilotPlausibility`.

  So unpack the package at `/home/claude/p1c/`, follow the README's steps, and add:
  ```
  cd /home/claude/p1c && gunzip -k predictors_blind.csv.gz
  cp pilot_compartments_static.npz ../p1/compartments_static.npz
  cp CRITICAL_VALUES.json CRITICAL_VALUES.frozen.json
  python3 -B calibrate_stress.py     # rewrites CRITICAL_VALUES.json; compare it with the frozen copy (its run time, "seconds", will differ)
  ```
  `make_addendum_records.py` confirms two things. The README's steps plus these lines recreate, byte for byte, every pilot file the code reads at `../p1/`. And `predictors_blind.csv.gz` decompresses to the frozen table.
- **§8.** The frozen-file list does not include the label files. This addendum's file table and timestamp cover them instead.

### m2. Between grid points, the critical values are approximate

- **What audit 5 found.** Each final value is a maximum over a grid of models. Between grid points, the region the pilot cannot reject extends slightly beyond the simulated models. Audit 5 simulated models between grid points, near the screen's boundary, with 4,000 fresh null replicates each:

  | Model | Screen | q95 of \|T\| | False calls at the frozen value |
  |---|---|---|---|
  | long-range field, share 0.65, 480 km | rejected by 0.0011 | M2: 4.05 | 5.6% ± 0.4 at 3.93 |
  | long-range field, share 0.75, 720 km | rejected by 0.0025 | M2: 4.09 | 6.4% ± 0.4 at 3.93 |
  | long-range field, share 0.65, 500 km (fourth audit) | retained | M2: 4.07 | — |
  | north–south field, 20 × 180 km, share 0.21 | rejected by 0.0040 | M2R: 2.61 | 5.6% ± 0.4 at 2.53 |
  | north–south field, 20 × 180 km, share 0.22 | rejected by 0.0082 | M2R: 2.53 | 5.0% ± 0.3 at 2.53 |

- **The C2 neighbours.** C2's binding model, the north–south field at share 0.20, is retained by 0.0034. Audit 5 read its two neighbours as clean because the screen rejects them. The review in §6 pointed out that the same reasoning would also clear S13's neighbours, which are rejected by narrower margins.
- **The reading.** Between grid points, a retained model could set a critical value above the frozen one:
  - for C2, by up to about 0.08 (2.53 against 2.61), where the Monte Carlo SE of these q95 values is about 0.04;
  - for S13's C2_M2, by up to about 0.16 (3.93 against 4.09).

  This is a residual risk, and neither frozen value changes. C1 and C1_M2 were not checked between grid points.
- **Two reporting notes, fixed here before any outcome.** With T = β / max(SE₂, SE_year), each verdict is reported under its frozen rule, unchanged. In addition:
  - **The primary test.** If 2.53 < T ≤ 2.61, the verdict SUPPORTED is labelled borderline.
  - **S13.** T is also stated against 4.10. If 3.93 < T ≤ 4.10, S13's verdict is labelled borderline.

  2.61 and 4.10 are the largest q95 values above, 2.606 and 4.091, rounded up to two decimals as the frozen values were. Neither note changes a decision, and S13 carries no decision weight.
- **§2.** "At every share the pilot cannot reject" holds at the grids' shares. Between them, see this item.

### m3. The command record

- **§3's scope.** "Every call", in both bullets on part 2, means every Bash, Edit and Write call: the tools that run commands or write files on the analysis machine.
  - Audit 5 found all 213 such calls from 06:51:29Z to the freeze command in part 2, in order and identical.
  - Other tools that act are in the first new record below: shell commands on the author's computer, TaskStop, Agent and Projects writes.
- **Two new records**, from the same session transcript:
  - `addendum_transcript_other_tools.jsonl`: every call of any other tool, from the transcript's start (06:51Z) up to this addendum's build. That is 33 calls (Read 9, shell on the author's computer 5, Projects 4, TaskCreate 4, Agent 3, SendUserMessage 3, TaskStop 2, ReadNotifications 1, TaskUpdate 1, folder listing on the author's computer 1), 20 of them before the freeze command. They include:
    - two TaskStop calls. At 07:09:26Z one stopped the first disclosed v1.3 run. At 07:43:24Z the other stopped a wait loop on the second run, which a `pkill` at 07:43:14.932Z (a Bash call, in part 2) had already ended;
    - four shell commands on the author's computer at 09:17Z: two listings, and two moves of the unpublished v1.0 package and its Codex packet into `superseded/` in his mirror folder.
  - `addendum_transcript_post_freeze.jsonl`: every Bash, Edit and Write call after the freeze command (12:15:47.486Z) up to this addendum's build. That is 74 calls, from 2026-10-21T12:16:00.175Z to 2026-10-21T13:43:30.706Z. One of them deleted `p1c/__pycache__` (m6).
  - Calls of other tools before 06:51Z (02:51 ET) are in no record. The session transcript before then was lost when the session was compacted (plan §3).
- **Format.** As in part 2, `input` is each call's input as the session transcript stores it. The transcript drops a leading `cd <dir> &&` from a command when `<dir>` is the working directory, so each new row also gives `cwd`, the working directory of the call.
- **Redaction.**
  - The plan's two hashed tokens are redacted as in part 2.
  - In the new records, one more token is redacted the same way: the author's account name on his computer, which is his name in lower case (sha256 `46711eb1a331c17ea8bfeadc8f2b22195b1c690b0c210d02fe7c0ebeffb0d8c3`). It occurs in paths and in the privacy checks of this addendum's build.
  - Affected rows are flagged `redacted`. The build fails if any token, or any part of a token, still hashes to one of the three, or if any e-mail address remains.
- **What is left out.**
  - Of the calls up to the build, only the build's own invocation is in neither record. The build refuses to run unless that invocation is exactly `cd /home/claude/p1c/addendum_v1.4 && python3 -B make_addendum_records.py`.
  - What the build does is fixed by `make_addendum_records.py`, whose code is in the package: it fills this file's counts and table, stamps it, copies the files into the package and rewrites `SHA256SUMS.txt`.
  - Later calls only copy the finished package for publication, and they are in no record.
- **Not included.** The auditors' and the reviewer's own calls ran in separate agents (plan §8).

### m4. The smoke tests, in full

§0's sentence on the smoke test is incomplete. In full:
- **10:49:28Z, unit test.** It ran in the same command that added the stress code to `simcal.py`, on 300 random points with one coincident pair:
  - max |LLᵀ − C| was 2.1e-15 with jitter 1e-6;
  - the compartment within-group correlation was 0.300 (target 0.3);
  - the field check used two pairs whose model correlation is about 0 (empirical 0.008 and −0.017), so it checked little.
- **10:50:43Z, one smoke-test command:**
  - imported `calibrate_stress.py` (90 candidates; pilot compartment share 0.080);
  - computed the screen statistics on 100 pilot-design replicates of `aniso_NS_s0.150_10x60` and `comp_s0.080` (medians printed; no retention decision);
  - timed the exact Cholesky factor of `aniso_NS_s0.150_10x60` on this region's design;
  - ran 200 null replicates of that model (seed 999), which printed q95 |T| under M2R = 2.402.
- **10:51:09Z, the registered run.**
  - No code changed between the smoke test and the run (audit 5, item 1).
  - Between the unit test and the smoke test, `calibrate_stress.py` was written (10:50:06Z) and `run_test.py` edited (10:50:31Z). `simcal.py`, which the unit test exercised, did not change after it.
  - Nothing was tuned on the tests.

### m5. What v1.4 fixed, exactly

§0's "v1.4 fixes them" overstates. Here is the status of each of the fourth audit's findings, as audit 5 assessed them (item 6):

| Fourth audit | Status |
|---|---|
| M1: C2 had no margin | fixed; between grid points, see m2 above |
| M2: S13 under long-range fields | mostly fixed; v1.4 neither fixed nor disclosed the gap between grid points, which m2 above now discloses |
| m1: command record | fixed; its tool scope is stated in m3 above |
| m2: 200-replicate screens | disclosed as residual risk (§2) |
| m3: overstated coverage | fixed; the new overstatements are corrected in this addendum |
| m4: compartment clustering | fixed by the compartment models (max q95 2.471 < 2.53); combinations disclosed as not covered |
| m5: code points | label loading, the missing fetch record and the S9 label are fixed; a missing `outcomes.csv` still gives a traceback (m6), and the local trust in `OUTCOME_FETCH.json` remains (below) |

**Disclosure for §8: the fetch record.** `run_test.py` checks three things about the fetch record:
- that `OUTCOME_FETCH.json` exists;
- that `FREEZE.json` equals the public copy whose hash the record holds;
- that `outcomes.csv` is the file whose hash the record holds.

Beyond that it trusts the record. It checks neither the record's OpenTimestamps proof nor the public registration. `fetch_outcomes.py` checks the registration before it requests any outcome (G2). The results will be published with:
- `OUTCOME_FETCH.json`;
- its proof, `OUTCOME_FETCH.json.ots`;
- `OUTCOME_FETCH_STAMP.json`;
- `outcomes.csv`.

Anyone can then check the record against the public registration and its timestamp.

**Disclosure for §8: this addendum in the public record.** G2 checks only the plan and `FREEZE.json`. No outcome will be requested until the public record also holds this file and its proof. After `verify_registration.py`, the script `verify_addendum_public.py`:
- downloads both files anonymously;
- compares them byte for byte with the local copies;
- writes `ADDENDUM_REGISTRATION.json`, but only on a match.

The frozen `fetch_outcomes.py` cannot enforce this step. The command record will show that it came first.

### m6. Small code points

- **Read order in `main()`.** `run_test.py` reads `outcomes.csv` before `verify_inputs()`. Three cases therefore give a Python traceback rather than a clean VERIFY FAIL: a missing `outcomes.csv`, a missing frozen input, or a missing `FREEZE.json` key. In every case the run exits with status 1 and writes no result. The frozen code stays as it is.
- **The `check_calibration_repro.py` docstring.** It says "every statistic". The script compares only q90 and q95 of |T|, under M2R and M2, for its three models. Audit 5 checked more (item 3):
  - it re-ran the stress set's C2 binding model and found all 10 recorded statistics identical;
  - it found the C1 and C2_M2/C1_M2 binding values identical;
  - it re-ran `check_calibration_repro.py`, which wrote a byte-identical `CALIBRATION_REPRO.json`.
- **`p1c/__pycache__`.** It held unfrozen bytecode and was deleted before this addendum was built. The confirmatory run will use `python3 -B` with no `__pycache__` present. `run_test.py`, run as the main script, never used it.

## 3. Corrections to the plan's wording

| § | Frozen text | Read as |
|---|---|---|
| 0 | "v1.4 fixes them, without changing the model or the statistic." | "v1.4 fixes most of them, without changing the model or the statistic; Addendum 1 (m5) gives the status of each." |
| 0 | "Before the registered run, the stress code was smoke-tested on one anisotropic model (200 replicates); nothing was tuned on it." | "Before the registered run, the stress code was unit-tested on 300 random points. One smoke-test command then computed screen statistics on 100 pilot-design replicates of one anisotropic and one compartment model, and ran 200 null replicates of the anisotropic one (seed 999; q95 2.402). Nothing was tuned on them (Addendum 1, m4)." |
| 2 | "… at every share the pilot cannot reject." | "… at every grid share the pilot cannot reject. Between grid points a retained model could set a higher value, by up to about 0.08 for C2 and 0.16 for C2_M2. The report labels verdicts in those bands borderline (Addendum 1, m2)." |
| 3 | "every call from 02:09:28 to 02:31:57 ET"; "every call from 02:51 ET onward" | "every Bash, Edit and Write call from 02:09:28 to 02:31:57 ET"; "every Bash, Edit and Write call from 02:51 ET up to and including the freeze command". Addendum 1 (m3) holds the other tools from 02:51 ET and the Bash, Edit and Write calls after the freeze. Calls of other tools before 02:51 ET are not recorded. |
| 6 | "S13: … with its own calibrated critical value C2_M2 = 3.93." | "S13: … with its own calibrated critical value C2_M2 = 3.93, approximate between grid points. T is also stated against 4.10, and a verdict with 3.93 < T ≤ 4.10 is labelled borderline (Addendum 1, m2)." |
| 8 | the list of frozen files | add: "The compartment label files and the per-ignition compartment IDs are not in `FREEZE.json`. Addendum 1 hashes them, and its timestamp covers them." |
| 8 | the description of `OUTCOME_FETCH.json` | add the two disclosures in m5 above. |

## 4. What stays the same, and how to check it

- **`FREEZE.json` and every file it lists.** `make_addendum_records.py` hashes all 236 entries before it writes anything and again at the end. It stops with an error if any of them differs, or if an outcome file exists.
- **The package.**
  - The 61 files listed in the v1.4 `SHA256SUMS.txt` keep their hashes.
  - The addendum's 13 files are added.
  - `SHA256SUMS.txt` is rewritten over all 74, as `make_package.py` writes it.

  If a check fails after the copy, the build removes the copies and restores the v1.4 `SHA256SUMS.txt`.
- **README step 2** covers the v1.4 files only. The addendum's files are checked against §5's table and `SHA256SUMS.txt`, not against `FREEZE.json`.
- **The test.** The model M2R, the statistic, C2 = 2.53, C1 = 2.08, C2_M2 = 3.93, C1_M2 = 3.39, and every reading in §2 stay as frozen.
- **Outcomes.** No outcome from this region has been requested, and none exists on the analysis machine.

## 5. Files added to the package

<!-- FILES -->
| File | Bytes | SHA-256 | What it is |
|---|---|---|---|
| `AUDIT_5_of_v1.4.md` | 11,300 | `58f06f3bf338eddebd28ef02018ba34c15cf0489c932107695b9bd0063750572` | the fifth audit, verbatim below a header comment |
| `REVIEW_of_ADDENDUM_v1.4.md` | 17,149 | `20b67403d7436e2e4585c857dc45fec4da278ce746bef60ba5cf61fb9ff33cbb` | the independent review of this addendum's draft, verbatim below a header comment (§6) |
| `COMPARTMENT_LABELS.json` | 3,397 | `71cbad50efb343dc9509205abb9dc9077721caa0f470a68c7cc4f025f979bbac` | hashes and counts of the compartment labels (m1) |
| `compartments_static.npz` | 15,199,539 | `d6fd8cb7590dc9cc70ec84bb6e5179d69212295a871c7586ae7fe571d960d996` | this region's compartment label arrays (copy of p1c/compartments_static.npz) |
| `pilot_compartments_static.npz` | 12,161,473 | `8fabe8e39cfb0cfee37d2b60d0bc63f42b1ebecb100d582deabca3c156c06ef5` | the pilot's compartment label arrays (copy of p1/compartments_static.npz) |
| `compartment_ids_blind.csv.gz` | 63,310 | `10d63f095a49a3fd14e4eda05fee72f07ea7b0563ff2ca30b8895f883808d833` | definition-B compartment of each of the 14,105 ignitions of this region |
| `pilot_compartment_ids.csv.gz` | 18,874 | `988ef53130ba7857ad65cbb3a3a4ac33efa7dc704571e001f5a14007e392dd69` | definition-B compartment of each of the 4,642 pilot ignitions |
| `addendum_transcript_post_freeze.jsonl` | 175,134 | `585f56b07de239aa33fc3e28ab18cdcb4458872540daf7c1d70140885e742168` | Bash, Edit and Write calls after the freeze command (m3) |
| `addendum_transcript_other_tools.jsonl` | 29,377 | `0542cb8e9ede0e2ed391d6182d382edafdcff16d0141cc9d3ae545fb2dbd97f7` | calls of all other tools from 06:51Z (m3) |
| `make_addendum_records.py` | 22,487 | `f4b0847c0a9e0813188c926042bba484199b4b4b878e46dd4a0cad0675503e11` | this build script |
| `verify_addendum_public.py` | 3,364 | `5419d4023ea1db27089426ab0118138295fdd3918cba8eba2d1eec0105e37254` | checks the public record for this addendum before any outcome (m5) |
<!-- /FILES -->

This file itself, `ADDENDUM_v1.4.md`, is listed in `SHA256SUMS.txt`. Its OpenTimestamps proof, `ADDENDUM_v1.4.md.ots`, was submitted to the calendars when it was built; Bitcoin confirmation was then pending.

## 6. Independent review of this addendum

A separate agent that had not written this addendum reviewed its dry-run build. Its report is `REVIEW_of_ADDENDUM_v1.4.md`, verbatim below a header comment. It found no critical issue and two moderate ones, both fixed here:
- **Home-folder rule.** The build's home-folder rule also rewrote code and text that were not the author's path. The hashed-token redaction in m3 replaces it.
- **"No gap for C2".** This was not supported by audit 5's own between-grid numbers. m2 now treats C2 and C2_M2 alike.

Its minor points are applied here:
- in m1 (provenance, re-run recipe), m2 (table, notes), m3 (TaskStop, scope, format, what is left out), m4, m5, m6, §3 and §4;
- in the build script: an exact last-call check, fatal privacy checks, rollback after a failed copy, the timestamp digest checked at its offset, and a refusal of agent rows in the transcript.

One suggestion was not taken. It concerned the replicate count of the fourth audit's screen of the 0.65, 500 km field. That count is not stated, because this addendum did not verify it.
