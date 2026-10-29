# P1C: pre-registration of a confirmatory wildfire test (northeast Washington), v1.4

This folder is the **public registration** of a confirmatory test. Everything listed in `FREEZE.json` was frozen before any fire-size outcome for the region was requested.

v1.4 supersedes v1.0 to v1.3. Each was frozen, timestamped and independently audited, but never published. The plan's §0 says what changed at each step and why. Their plans, code and freeze records are in `history_v1.0.tar.gz` to `history_v1.3.tar.gz`, with development files in `history_v1.1_dev.tar.gz`, `history_v1.3_dev.tar.gz` and `history_v1.4_dev.tar.gz`. The four audit reports are included verbatim: `AUDIT_1_of_v1.0.md` to `AUDIT_4_of_v1.3.md`.

## What is tested

**The claim.** Wildfires that start inside smaller compartments of mapped barriers end smaller. The barriers are vehicle roads, open water and non-burnable ground. The effect holds beyond barrier density and distance to the nearest road. The claim comes from *Trees Cannot Cut*: compartments come only from closed loops of holdable features.

**The pilot,** in Okanogan, Methow and Chelan, WA, pre-registered and frozen 2026-10-20 20:13 ET:
- β = 0.063 (95% CI 0.010–0.117), n = 2,677;
- about 16% larger fires per tenfold larger compartment.

Re-read with the methods below, the pilot's evidence is moderate (plan §1). With regional terms it holds at 5% under every error model tested on its design, though not at 2.5%. Under its own model it does not hold at 5% once compartment-level clustering is allowed.

**This test.** One confirmatory test in a new, adjacent region:
- **H2, definition B, model M2R:** SUPPORTED if β − C2 × max(two-way SE, year SE) > 0.
- **M2R** is the pilot's model plus fixed effects for 40 km regions.
- **The two-way SE** is clustered by year and 20 km block.
- **C2** is a critical value set by simulation: the maximum over a screened family of spatial error models that the pilot's residuals cannot reject (`CALIBRATION.json`) and over a stress set of structures outside it (`CRITICAL_VALUES.json`, which holds the final values).
- **The plan:** `PREREGISTRATION_P1C_NEWA_v1.4.md`.

## How to check the freeze

1. **Hashes.** `FREEZE.json` lists the SHA-256 of every frozen file, with paths as they were in the analysis folder. `SHA256SUMS.txt` covers this package.
2. **Gzipped and packed files.** Decompressed, each `.gz` file must match its entry in `FREEZE.json`:
   - `predictors_blind.csv.gz` → `predictors_blind.csv`;
   - `raw_fpafod_ignitions_blind.json.gz` → `raw/fpafod_ignitions_blind.json`;
   - `raw_mtbs_perims.json.gz` → `raw/mtbs_perims.json`;
   - `pilot_*` → `../p1/*` (pilot raw files are `../p1/raw/*`);
   - the `AUDIT_*` files → `audits/AUDIT_*`.

   `logs.tar.gz` holds `logs/`: the fetch logs, every background-command output, and the two-part record of every command and code edit with timestamps (plan §3 says what it covers, including one gap).
3. **Not shipped.** The large predictor inputs (LANDFIRE and PCL arrays, roads, NHD, ERC; about 400 MB) are not in this package. Their hashes are in `FREEZE.json`. `fetch_data.py` re-fetches them from the public services, but a re-fetch can differ if a service has changed since.
4. **The timestamp.** `FREEZE.json.ots` is an OpenTimestamps proof submitted to Bitcoin calendars. It was pending at freeze, and an upgraded proof is added once it is confirmed. Check it with `ots upgrade FREEZE.json.ots` and then `ots verify FREEZE.json.ots`.
5. **The outcome guard.** `fetch_outcomes.py` requests outcomes only after three checks:
   - the frozen files are unchanged;
   - it has itself downloaded this public copy of the plan and of `FREEZE.json` and found them byte-identical;
   - the sample shares no ignition with the pilot.

   Every record must come back, with year, date and location equal to the frozen records. Every request is logged, and the fetch record is timestamped. `run_test.py` refuses to run unless its inputs match `FREEZE.json` and the outcomes match the fetch record.

**Running the code.** The scripts expect the pilot files at `../p1/`. To put them there:

```
mkdir -p ../p1/raw
gunzip -c pilot_predictors_blind.csv.gz > ../p1/predictors_blind.csv
gunzip -c pilot_outcomes.csv.gz > ../p1/outcomes.csv
gunzip -c pilot_raw_mtbs_perims.json.gz > ../p1/raw/mtbs_perims.json
cp pilot_p1_config.json ../p1/p1_config.json
cp pilot_results.json ../p1/results.json
cp pilot_DEVIATION_2.json ../p1/DEVIATION_2.json
cp pilot_DEVIATION_3.json ../p1/DEVIATION_3.json
cp pilot_raw_requests.log ../p1/raw/requests.log
```

**Results** will be added later in a separate file. The files above will not change; any change after the freeze is reported as a numbered deviation.

## Authorship and AI use

**Author:** Justin D. Hart (Viridis LLC).

**AI use:** Claude (Anthropic) designed the analysis, wrote the code and ran it under the author's direction. The independent audits of v1.0 to v1.3 were run by separate Claude agents that had not built the study. Automated tools are not research authors.
