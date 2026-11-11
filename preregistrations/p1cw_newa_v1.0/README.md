# P1C-W: pre-registration of a wind-modification test of the P1C compartment effect (Stage 1, northeast Washington), v1.0

This folder is the **public registration** of Stage 1 of P1C-W. Everything listed in `FREEZE.json` was frozen before wind and fire size were joined for any ignition in the region.

## What is tested

P1C (`../p1c_newa_v1.4`, registered as PR #138) found that wildfires starting in smaller compartments of mapped barriers end smaller: β = 0.053 under M2R, definition B, 11,314 ignitions. P1C-W asks whether that effect fades as wind rises.

- **Primary estimand:** γ, the coefficient on Lc × z\_w in M2R-W = M2R + z\_w + Lc·z\_w + Lc·cause + z\_w·cause, with Lc = log10 A\_enc − 3.63 and z\_w the standardised W3 (maximum hourly ERA5 10 m wind over the discovery day and the next two local days, bilinear at the ignition).
- **Prediction:** γ < 0 (attenuation in wind).
- **Decision rule:** in `FREEZE.json` and plan §7. C\_W = 2.53 and C1\_W = 2.08 (both P1C floors bind); γ\_min = 0.0265 per SD.
- **The plan:** `PREREGISTRATION_P1CW_NEWA_v1.0.md`. Its content is identical to draft v0.2 apart from the status lines.

Stage 2, a blind confirmation in the western Oregon Cascades, is defined in plan §11. Its region and grid are fixed in `stage2_oregon_p1_config.json`. It gets its own freeze before any Oregon outcome is requested.

## Files

| File | What it is |
| --- | --- |
| `PREREGISTRATION_P1CW_NEWA_v1.0.md` | The plan |
| `fetch_era5_wind.py` | Fetches ERA5 hourly 10 m u and v (NSF NCAR mirror, ds633.0) for 49.5–43.25 N, 123.0–116.5 W, Dec 1991 to Jan 2025; logs every request |
| `raw_era5_requests.log` | That log: 796 requests, none failed |
| `RAW_ERA5_SHA256SUMS.txt` | SHA-256 of the 398 monthly `raw/era5/era5_wind_YYYYMM.npz` files (1.1 GB, not shipped) |
| `build_wind.py` | Builds the blind wind table; asserts no outcome column is read |
| `wind_blind_newa.csv` | fod\_id, W1, W3, W7, P3 (placebo), W3mean, W3\_pct for the P1C ignitions |
| `calibrate_wind.py` | Null calibration of C\_W and C1\_W over 140 error models, plus power; asserts no outcomes file is present |
| `CALIBRATION_WIND.json`, `calibrate_wind.out` | Its result and console output |
| `stage2_oregon_p1_config.json` | Stage 2 region, boxes and grid |
| `freeze_w.py` | Checks invariants W1–W6, writes `FREEZE.json`, verifies (`--verify`) and stamps (`--stamp`) |
| `FREEZE.json`, `FREEZE.json.ots` | The freeze record and its OpenTimestamps proof |
| `FREEZE_superseded_1.json` | The first freeze record (commit 5989c46), replaced the same day before any outcome join because `fetch_era5_wind.py` omitted January 2025 from its schedule and did not create `raw/era5`; no data, table or calibration changed |

## How to check the freeze

1. **Hashes.** From this folder in a viridis-canon checkout: `python3 freeze_w.py --verify`. It re-runs the invariant checks and recomputes every hash, including the P1C files this test reads (taken from `../p1c_newa_v1.4`, gzipped files decompressed), which must equal the P1C v1.4 freeze.
2. **The timestamp.** `ots upgrade FREEZE.json.ots`, then `ots verify FREEZE.json.ots`.
3. **Raw wind.** `python3 fetch_era5_wind.py` re-fetches the months into `raw/era5/`; compare with `sha256sum -c RAW_ERA5_SHA256SUMS.txt`.

## Reproducing the calibration

`calibrate_wind.py` was run (and is frozen) with this layout, which is how it finds P1C's code and the public pilot:

```
work/
  calibrate_wind.py
  p1c/   ../p1c_newa_v1.4 without fetch_outcomes.py, with predictors_blind.csv decompressed; no outcomes.csv
  p1/    predictors_blind.csv and outcomes.csv from ../p1c_newa_v1.4/pilot_*.csv.gz (the pilot, already public)
```

Then `python3 calibrate_wind.py wind_blind_newa.csv CALIBRATION_WIND.json 6`. Full settings took 30 minutes on 6 cores. Monte Carlo error on a 95th percentile at 4,000 replicates is about ±0.03.

## What comes next

1. Join P1C's outcomes to the wind table and run M2R-W once (plan §9 step 6).
2. Stage 2: the Oregon blind fetch, predictor and wind tables, and both calibrations, run from a machine that can reach LANDFIRE, TIGER, NHD, USFS and gridMET. No Oregon outcome is requested until the Stage 2 freeze.
