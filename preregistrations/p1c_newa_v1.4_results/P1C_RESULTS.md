# P1C results: the confirmatory replication is SUPPORTED (reading: REPLICATED)

**Test.** P1C v1.4, the pre-registered confirmatory replication in northeast Washington. Do wildfires that start inside smaller compartments of mapped barriers end smaller?

**Registered.** Pull request [jdhart81/viridis-canon#138](https://github.com/jdhart81/viridis-canon/pull/138), commit `9e79127d9ba9b17812f8fb567bef5ec858693a8d`, folder `preregistrations/p1c_newa_v1.4/`.

**Order of events, 2026-10-22 (UTC):**

| Time | Event |
|---|---|
| 11:30:09 | `REGISTRATION.json` written. The plan and `FREEZE.json` were downloaded anonymously from the commit and matched byte for byte. |
| 11:30:17 | `ADDENDUM_REGISTRATION.json` written (Addendum 1 and its `.ots` matched). |
| 11:30:56 | `fetch_outcomes.py` repeated the anonymous download itself (guard G2). |
| by 11:34:43 | All outcomes fetched: 14,105 of 14,105, none missing, no overlap with the pilot. |
| 11:34:46 | `OUTCOME_FETCH.json` stamped with OpenTimestamps. |

After that, `run_test.py` ran once. Its input check passed: every input matched `FREEZE.json`, and the outcomes matched the fetch record.

Not peer reviewed. The frozen files are unchanged, and there are no deviations from the plan.

## Primary result (H2, definition B, model M2R)

| Quantity | Value |
|---|---|
| Ignitions in the primary sample | 11,314 (33 year clusters, 75 20-km blocks, 24 40-km regions) |
| β, log10 final fire size per log10 compartment area | **0.0531** |
| SE, two-way (year × 20 km block) / year-clustered / max | 0.0120 / 0.0097 / 0.0120 |
| Registered interval, β ± 2.53 × max SE | **0.0228 to 0.0835** |
| T = β / max SE | **4.42** (C2 = 2.53) |
| **Decision** | **SUPPORTED** |
| **Reading** | **REPLICATED** |
| Fire size per tenfold larger compartment | × 1.13, about 13% larger (pilot: × 1.16) |

- **Addendum 1 note.** T is not in the borderline band (2.53, 2.61], so the verdict is not borderline.
- **Other intervals (reported, not decisive):**
  - the v1.1-rule interval (t × max SE): 0.0287 to 0.0776, SUPPORTED;
  - the pilot-rule reading: SUPPORTED;
  - the year-clustered 95% CI: 0.0342 to 0.0721;
  - the year cluster bootstrap: 0.0350 to 0.0721.
- **Small telescopes.** β₃₃ = 0.0415 and the 90% upper bound is 0.078, so an effect as large as the one the pilot could detect is not rejected.

## Pre-specified checks

**S13: the pilot's own model M2, no regional terms, critical value C2_M2 = 3.93. No decision weight.**
- β = 0.0330, max SE 0.0142, T = 2.33. The interval is −0.023 to 0.089: **NOT SUPPORTED** against 3.93, and against 4.10, so it is not borderline.
- Its year-clustered 95% CI is 0.005 to 0.061, and the v1.1-rule reading is SUPPORTED.
- **The effect is smaller without the 40 km regional terms.**

**Leave-one-year-out.** β ranges from 0.049 to 0.057 over the 33 years. No year's removal changes the decision.

**Stacked with the pilot (M2R).**
- The pilot's β is 0.079, so the difference is −0.026 (z = −0.98, p = 0.33 with two-way SEs).
- Pooled (GLS, two-way): **0.057** (0.036 to 0.079).

**Sensitivities, definition B.**

| Check | Model | n | β (95% CI) | Registered rule |
|---|---|---|---|---|
| S10 outside the pilot's compute box | M2R | 9,941 | 0.043 (0.016–0.069) | SUPPORTED (0.009–0.077) |
| S10b also excluding pilot-fetched MTBS perimeters | M2R | 9,368 | 0.042 (0.012–0.072) | SUPPORTED (0.003–0.081) |
| S11 no fuel-group term | M2R | 11,314 | 0.051 (0.027–0.075) | SUPPORTED (0.020–0.082) |
| S12 without possible cross-boundary duplicates | M2R | 11,309 | 0.052 (0.029–0.076) | SUPPORTED (0.022–0.083) |
| S1 snap ignitions on holdable cells | M2 | 13,707 | 0.057 (0.039–0.075) | n/a |
| S2 include censored compartments | M2 | 11,585 | 0.031 (0.012–0.050) | n/a |
| S3 drop coarse coordinates | M2 | 11,297 | 0.033 (0.014–0.052) | n/a |
| S5 B+ (prior 10-year burn scars as barriers) | M2 | 11,105 | 0.020 (0.001–0.039) | n/a |
| S6a lightning-caused only | M2 | 4,226 | **−0.015 (−0.062 to 0.033)** | n/a |
| S6b human-caused only | M2 | 6,915 | 0.054 (0.031–0.076) | n/a |
| S8 years 2010 on | M2 | 4,865 | 0.049 (0.025–0.073) | n/a |

**Secondary models (not confirmatory).**

| Definition | Model | n | β (95% CI) |
|---|---|---|---|
| B | M1 | 11,314 | 0.063 (0.042–0.085) |
| A50, DNR control-location map with PCL > 0.5 | M1 | 102 | 0.553 (0.361–0.746) |
| A50 | M2 | 102 | 0.527 (0.366–0.689) |
| A25, PCL > 0.25 | M1 | 712 | 0.158 (0.087–0.228) |
| A25 | M2 | 712 | 0.140 (0.071–0.209) |

PCL has large no-data gaps in this region, so the A50 sample is small (n = 102).

**H3, escaped fires (B, M2, n = 802).** β = 0.091 (0.001–0.181).

**H4, containment (B, n = 802).** Observed share 0.946 against a null mean of 0.929, one-sided p = 0.0002.

## What this does and does not show

- **It does show:** under the rule frozen and timestamped before any outcome was requested, the compartment effect found in the Okanogan, Methow and Chelan pilot replicates in the adjoining northeast Washington region.
  - The effect is slightly smaller than the pilot's: about 13% larger final fires per tenfold larger compartment of mapped roads, water and non-burnable ground, after fire weather, fuel, cause, month, year, barrier density, road distance and 40 km regions are accounted for.
- **It does not show:**
  - that barriers stop fires;
  - how much of the effect runs through suppression access rather than fuel discontinuity.

  The study is observational.
- **Three pre-specified checks bound the result:**
  - Without the regional terms (S13, M2) the estimate is 0.033, and it does not pass S13's stricter critical value.
  - Fires caused by lightning show no effect (S6a); the effect is in human-caused fires (S6b).
  - Counting recent burn scars as barriers shrinks the estimate to 0.020 (S5).

## Files

These are published next to the registration, in `preregistrations/p1c_newa_v1.4_results/`:
- this report;
- `results.json`, `run_test_registered.log`;
- `outcomes.csv`, `OUTCOME_FETCH.json` and its `.ots`, `OUTCOME_FETCH_STAMP.json`, `outcome_requests.log`, `fetch_outcomes_run.log`;
- `REGISTRATION.json`, `ADDENDUM_REGISTRATION.json`.

The registered folder is not touched.

**Authorship.** Justin D. Hart (Viridis LLC) is the accountable author. Claude (Anthropic) designed the analysis and wrote and ran the code under his direction. Automated tools are not research authors.
