<!-- Independent review, reproduced verbatim below this comment. Reviewed: the dry-run build of Addendum 1 to plan P1C v1.4 (ADDENDUM_v1.4.md as filled at 13:00:28Z, its template and make_addendum_records.py). Delivered 2026-10-21T13:30:13Z. The reviewer was a separate Claude agent that had not written the addendum; it worked on copies, made no network requests and requested no outcome. Paths refer to the analysis machine; the reviewer's scratch scripts are not shipped. Its findings are answered in the final ADDENDUM_v1.4.md (see its section 6). This report is not covered by FREEZE.json. -->

## Review of Addendum 1 to P1C v1.4 (dry run of 13:00:28Z)

**Bottom line.** There is no critical issue. The addendum's numbers, times and quotations match audit 5 and the plan. The labels verify independently. On scratch copies, the build reproduces the dry-run records, COMPARTMENT_LABELS.json and ADDENDUM byte for byte, and a full run with a fake offline `ots` gives a correct package. Two moderate problems should be fixed before the final run: the home-folder regex rewrites text that is not the author's path, and the "no gap for C2" claim is not supported by audit 5's own between-grid numbers. Several descriptions are inaccurate: the second TaskStop, the pilot label rebuild, "no code changed between the tests and the run", and "all 10 statistics".

**Protected folders.** 774 of 775 file hashes and 798 of 799 path/size/mtime/mode lines are unchanged, and FREEZE still matches 236/236. The one change is `/home/claude/p1c/CODEX_P1C_REGISTRATION_TEMPLATE.md` (2,285 → 2,716 bytes, mtime 13:01:33Z). The main session's Bash call at 13:01:31.043Z wrote it, 20 s after my snapshot began. It is not in FREEZE and not in the package. All my work was on copies, with `-B` and no network.

| # | Result | Evidence |
|---|---|---|
| 1 Faithful to audit 5 | ISSUE (minor) | **Matches:** the m2 table (4.05 / 4.09 / 4.07; 5.6% / 6.4% ± 0.4; margins 0.0011 / 0.0025, which I recomputed from audit 5's between_grid.json), the 0.21 / 0.22 check (q025 0.057 / 0.062 against 0.053), the 213 calls (Edit count in the window is 0, so "Bash/Write" equals "Bash, Edit and Write"), and the item numbers. **Overstated attributions:** the pilot label rebuild (item 2 says "the builder's equivalence rebuild"); "no code changed between the tests" (item 1 covers only the time after the smoke test); "all 10 statistics of the binding models" (item 3 says this of one model); and the m5 M2 row "disclosed" (item 6 says "neither fixed nor disclosed"). The m5 row also leaves out the outcomes.csv traceback. |
| 2 Facts from records | ISSUE (minor) | **m4 matches the tool inputs and outputs.** 10:49:28Z: 300 points, x[5]=x[6], max error 2.109e-15, jitter 1e-06. 10:50:43Z: 90 candidates, share 0.08, CAND[3]=aniso_NS_s0.150_10x60, CAND[-4]=comp_s0.080, 100 replicates, Cholesky 11.9 s, 200 replicates from seed 999, q95 2.402. Registered run at 10:51:09Z. **TaskStop:** the 07:09:26Z call stopped the first v1.3 run (task b5xdfb0uc). The 07:43:24Z call stopped a wait loop (bfd2oy646, `until grep -q "^exit=" calibrate.log…`). The second run (bblsn32aj) had been killed by `pkill -f "python3 calibrate_critical.py"` at 07:43:14.932Z. **09:17Z:** two listings (:32, :35) and two moves (:48, :51) — correct. |
| 3 Plan's text | OK, with 2 corrections wrong | All six quotations occur verbatim, once each. The third audit's printout (its command at 06:39:49Z) filtered Bash/Edit/Write, so the new §3 wording is right. Wrong: the §2 row's "found no gap for C2" (Moderate 2) and the §3 row's "Other tools … are in Addendum 1" (true only from 02:51 ET). |
| 4 Build script | ISSUE | **Re-run on copies,** with the transcript cut at the 13:00:22Z dry-run call so the last-call check passes unmodified: identical outputs. **Full run with a fake offline `ots`:** ADDENDUM OK, the 61 old hashes kept, 72 files listed, SHA256SUMS identical to `make_package.py`'s logic, table matches the package, digest at offset 33. **My own recomputation:** 44 post-freeze calls (12:16:00.175Z → 13:00:11.423Z) and 30 other-tool calls (20 before the freeze). Only one call has the freeze timestamp. Redaction is identical to extract_transcript.py's (same REDACT, same TOKEN, input only, same flag). **Writes and checks:** it writes only to addendum_v1.4/ and the package, and no FREEZE key lies under either, so it cannot change a frozen file. The `ots` checks (return code, digest present) are sound. **Problems:** the home-folder regex (Moderate 1); a docstring overclaim; a print-only e-mail check; a last-call check that accepts any command naming the script; publication steps after the build. |
| 5 Labels (m1) | OK | **Files:** npz d6fd8cb7…/8fabe8e3… equal their sources. labB bytes ee515ce8…/47f992db… (C-contiguous int32, 6849×7885 and 6448×6021). **ID tables:** 14,105 and 4,642 rows, fod_id order equal to the predictor tables, compartment_B = labB[row,col] everywhere. **B samples (my own filter):** 11,314 / 2,677 points, 2,065 / 555 compartments, none on label 0. labB==0 is exactly road∪water∪nonburn. **Recipe:** the three .gz files decompress to the frozen hashes. calibrate_stress, pilot_reread and simcal read only HERE/{run_test.py, simcal.py, CALIBRATION.json, CRITICAL_VALUES.json, predictors_blind.csv, compartments_static.npz} and /home/claude/p1/{predictors_blind.csv, outcomes.csv, compartments_static.npz}. After the recipe all of them are byte-identical. |
| 6 Privacy | ISSUE (doubtful items) | No e-mail address, no e-mail fragment (as a token or a substring), no remaining /Users/ path, no credential or URL. "Justin" appears 3 times. **Doubtful:** (a) the bare macOS account name (the author's name in lower case without the space) appears 11 times in 4 rows (12:45:17, 12:47:08, 12:47:20, 12:47:29Z); (b) the two REDACT hashes are published and easy to guess (already public in extract_transcript.py); (c) the session UUID. The final run's new rows are published without review. |
| 7 Soundness | ISSUE | **Defensible:** the addendum leaves FREEZE untouched, comes before any outcome, is timestamped, is Deviation 1, and has no effect on the primary test. **Problems:** the C2 / S13 asymmetry (Moderate 2); "borderline" should accompany S13's frozen verdict, not replace it; the precedence clause is too broad; G2 checks only the plan and FREEZE.json, not the addendum. |
| 8 Wording | ISSUE | See the minor list. |

### Critical
None.

### Moderate

**1. The home-folder regex over-matches, so the final record will contradict m3.**

`HOME = r'/Users/[^/\s"\'\\]+'` replaces any `/Users/x`.
- **In the dry run**, it rewrote text that is not the author's path:
  - the regex literal in the recorded Write of make_addendum_records.py (12:57:53Z). The recorded source now reads `HOME = re.compile(r'~/\s"\'\\]+')`;
  - the same literal twice in the 13:00:11Z edit;
  - the docstring `/Users/<name>` (12:58:48Z);
  - the code strings at 12:45:17Z and 12:47:29Z, which now read `s.replace('~', '~')`.
- **In a simulated final run** (the current transcript plus a synthetic last call), it also alters this review's prompt (Agent call, 13:01:00Z): "touches only \`~ path prefixes", "no \`~ path", and it swallows a backtick.
- **Meanwhile the bare account name is not hidden:** it stays in the 4 rows listed in item 6.

Fix: replace only the author's account path, matched by hash.
```python
ACCT = '46711eb1a331c17ea8bfeadc8f2b22195b1c690b0c210d02fe7c0ebeffb0d8c3'  # sha256 of the lower-case account name
HOME = re.compile(r'/Users/([A-Za-z0-9._-]+)')
def _home(m): return '~' if sha_bytes(m.group(1).lower().encode()) == ACCT else m.group(0)
# shorten_home: new = HOME.sub(_home, o); the post-check fails only on account-matching paths
```
Then reword m3: "The author's macOS account path (`/Users/<account>`) is shortened to `~`, and each affected row is flagged `home_folder_shortened`. The account name itself, which is his name, still appears in four privacy-check commands (12:45–12:48Z)." Alternatively, redact tokens that hash to ACCT and say so.

**2. "No gap for C2" (m2 and the §3 row for §2) is not supported by the evidence.**

Audit 5's own between-grid output:
- North–south 20×180 at share 0.21: q95 under M2R 2.606, and 5.6% ± 0.4 false calls at 2.53. This is the same over-call as S13's 0.65/480. At 0.22: 2.530 and 5.0%.
- Both the C2 and the S13 neighbours are rejected by the screen. The margins differ: 0.0040 / 0.0082 for C2 against 0.0011 / 0.0025 for S13.
- Share 0.20 is retained by 0.0034. The boundary therefore sits near 0.205, where the interpolated q95 is about 2.56, roughly one Monte Carlo SE (≈0.04) above 2.53. For S13 the gap is about 0.1–0.13.
- The addendum's reason ("rejected by the screen") would dismiss S13's gap just as well.

Replace "The primary value. The same check found no gap … against the pilot's 0.053." with: "**The primary value.** For C2, the binding model's next shares are rejected by the screen by wider margins. North–south 20 × 180 km fields at shares 0.21 and 0.22 have simulated share q025 of 0.057 and 0.062, against the pilot's 0.053 (rejected by 0.004 and 0.008; share 0.20 is retained by 0.003). Their q95 of \|T\| under M2R are 2.61 and 2.53 (5.6% and 5.0% false calls at 2.53). Any retained field between shares 0.20 and 0.21 is therefore within about one Monte Carlo SE of C2. This is a residual risk, not a change to C2."

In the §3 row for §2, replace the second sentence with: "Between grid points, the fifth audit found a gap for S13's C2_M2 and, for C2, only a gap within Monte Carlo error (Addendum 1, m2)."

### Minor (fix → replacement)

1. **m1 "No new information" misattributes the pilot rebuild.** Audit 5 rebuilt only this region. The pilot's file matched the builder's equivalence rebuild, which used p1/raw; FREEZE holds only that folder's mtbs_perims.json and requests.log. Replace with: "Audit 5 rebuilt this region's label file from the frozen build code and frozen raw inputs and found it byte-identical. The pilot's label file is byte-identical to the builder's equivalence rebuild, which also reproduced the frozen pilot table byte for byte; the pilot's raw inputs are not in FREEZE.json. For every point of both B samples, audit 5 found each label's area equal to the frozen Aenc_B. What was missing was a hash fixed before any outcome from this region."
2. **m3 TaskStop.** Replace with: "the two TaskStop calls: at 07:09:26Z it stopped the first disclosed v1.3 run; at 07:43:24Z it stopped a wait loop on the second run, which a `pkill` at 07:43:14.932Z (a Bash call, in part 2) had already ended;"
3. **m4.** Replace the last bullet with: "**10:51:09Z, the registered run.** No code changed between the 10:50:43Z smoke test and the run (audit 5, item 1). After the unit test, calibrate_stress.py was written (10:50:06Z) and run_test.py edited (10:50:31Z); simcal.py, which the unit test exercised, did not change. Nothing was tuned on the tests." Two more changes in m4:
   - "the simulated field and compartment correlations matched the model" → "the compartment within-group correlation was 0.300 (target 0.3); the field check used two pairs whose model correlation is about 0 (0.008 and −0.017)";
   - "ran 100-replicate pilot screens of" → "computed the screen statistics on 100 pilot-design replicates of … (medians printed; no retention decision)".
4. **m6.** Replace with: "Audit 5 re-ran the stress set's C2 binding model and found all 10 recorded statistics identical. It also found the C1 and C2_M2/C1_M2 binding values identical, and re-ran check_calibration_repro.py to a byte-identical CALIBRATION_REPRO.json (item 3)." Also: "A missing outcomes.csv, frozen input or FREEZE.json key therefore gives" → "A missing outcomes.csv (read before verify_inputs()), a missing frozen input or a missing FREEZE.json key gives".
5. **§1.** "none of them touches the primary test or its critical values" → "none of them changes the primary test or its critical values". m1's labels feed S-C, which came within 0.06 of setting C2.
6. **m3 "What is left out".** Publishing will need calls after the build, as at 12:17Z (copies to outputs and the Mac). Replace with: "Of the calls up to the build, only the build's own invocation is in neither record. What it does — fill this file's counts and table, stamp it, copy the files into the package and rewrite SHA256SUMS.txt — is fixed by make_addendum_records.py, whose code is in the package. Calls after the build, which only copy the finished package for publication, are in no record." Also make the last-call check exact, so nothing can ride along unrecorded: `re.fullmatch(r'(cd /home/claude/p1c/addendum_v1\.4 && )?python3 -B make_addendum_records\.py', cmd)`.
7. **Privacy hardening.** The final rows are published without review. Make the e-mail check fatal and widen it to `[\w.+-]+@(\[redacted\]|[\w-]+)\.[A-Za-z]{2,}`. Fail if any substring of any token hashes into REDACT: the address's local part is not itself a REDACT token. Print the rows added since the last dry run.
8. **Docstring** "any failure stops … before the package is touched" is false for the checks made after copying (I5) and for the final I1 check. A failure there leaves copied files with the old SHA256SUMS.txt, and a re-run then fails. Either stage the copy and rename it, or add "except the checks after copying (I5) and the final I1 check". Also "No outcome is read" → "No confirmatory outcome is read; the pilot outcome table is only hashed."
9. **Header.** "Where the plan's wording and this addendum differ, read the addendum." → "Where §3 corrects the plan's wording, read the correction. Nothing here changes a model, statistic, critical value or decision rule."
10. **S13 note.** Replace with: "S13's verdict under its frozen rule (C2_M2 = 3.93) is reported unchanged, with \|T\| also stated against 4.10, the largest of these values (4.09) rounded up to one decimal. If 3.93 < \|T\| ≤ 4.10, that verdict is labelled borderline."
11. **m5 table.**
    - M2 row → "mostly fixed; v1.4 neither fixed nor disclosed the gap between grid points (disclosed now in m2 above)".
    - m5 row: add "a missing outcomes.csv still gives a traceback (m6)".
    - Disclosure: "run_test.py checks three things:" → "Of the fetch record, run_test.py checks three things:"; and "(G1, G2)" → "(G2)".
12. **m3 scope.** "These are the calls that run commands or write files." → "These are the tools that run commands or write files on the analysis machine. Other tools that act — shell commands on the author's computer, TaskStop, Agent, Projects writes — are in the new record below." In the §3 row: "Other tools, and the calls after the freeze, are in Addendum 1 (m3)." → "Other tools from 02:51 ET, and the Bash, Edit and Write calls after the freeze, are in Addendum 1 (m3); calls of other tools before 02:51 ET are not recorded."
13. **m1 recipe.**
    - Add `cp CRITICAL_VALUES.json CRITICAL_VALUES.frozen.json` before the run, and change the comment to "compare every field except `seconds`": the run overwrites the frozen copy, and `seconds` differs.
    - Add `cp pilot_p1_config.json /home/claude/p1/p1_config.json`, which run_test.py, blind_design.py and validate_synthetic.py need.
    - Also list calibrate_critical.py and simcal.pilot_residuals / pilot_variance_components among the readers of /home/claude/p1/.
14. **README step 2** will flag 4 addendum files (AUDIT_5, both ID .gz files, pilot_compartments_static.npz). Add to §4: "README step 2 covers the 61 v1.4 files only; the 11 addendum files are checked against §5's table and SHA256SUMS.txt, not FREEZE.json."
15. **m2 table.** The lead-in should read "Long-range fields between grid points, near the screen's boundary:". The third row's Screen cell should read "retained (fourth audit's 600-replicate screen)".
16. **Pre-outcome proof.** G2 checks only the plan and FREEZE.json. Add: "Outcomes will not be requested until the public record holds this addendum and its proof."
17. **Records use the stored inputs**, which drop a leading `cd <dir> &&` in 180 of 297 calls (28 post-freeze rows). This is part 2's convention; the harness keeps the full form in `wireToolInputs`. Disclose this in m3.
18. **Nits.**
    - AUDIT_5's file says "reproduced verbatim" but carries an added header comment.
    - The `.ots` check could require offset 33 after op 0x08.
    - Fail on `isSidechain` rows and on any non-`tool_use` tool blocks.

My scratch work is in `/tmp/claude-0/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3/scratchpad/review_addendum/`:
- `scripts/recompute_records.py` and `scripts/check_labels.py`;
- `exercise/`: the redirected script copies, the cut transcripts and the full-run package, with the fake `ots` in `bin/`;
- `hashes_before.txt`, `hashes_after.txt` and the matching stat files.

Worth remembering: the review of P1C v1.4 Addendum 1 (2026-10-21) found no critical issue. The two moderate ones were the over-broad home-folder regex in make_addendum_records.py and the unsupported "no gap for C2" claim (the 0.21 neighbour over-calls at 5.6%, as S13's does).
