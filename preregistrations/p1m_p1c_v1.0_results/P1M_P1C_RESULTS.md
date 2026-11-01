# P1-M on the P1C region: the road edge excess REPLICATED, and it holds away from valley floors

**Test.** Do final wildfire perimeters run along roads more than the land just beyond them? This is the confirmatory P1-M test in the P1C region (northeast Washington), in a sample disjoint from the pilot.

**Registered.** Plan v1.0 is [viridis-canon PR #139](https://github.com/jdhart81/viridis-canon/pull/139), commit `5e9a9f72ffd86e101cfc555d07148cc958eaf9bb`, folder `preregistrations/p1m_p1c_v1.0/`.

**Order of events, 2026-10-22 (UTC):**

| Time | Event |
|---|---|
| 12:33:07 | Freeze (`MECH_FREEZE.json`, sha256 `b5c55616…`), timestamped with OpenTimestamps. No result file existed. |
| 20:53:50 | Registration verified: all 19 frozen files downloaded anonymously from the commit matched byte for byte (`REGISTRATION_P1M.json`). |
| 20:54–21:00 | The runner ran each step once, in the plan's order, and stamped every output as soon as it was written. |

**Process.** The frozen pilot code ran unchanged: `mech_test.py` (85d4f45f…), `posthoc_roads.py` (d61013e9…). There are no deviations from the plan. Not peer reviewed.

## Confirmatory results (disjoint sample: 47 matched wildfires, 1992–2024, 30 clusters)

| Hypothesis | E (95% CI) | Shift null p (upper) | Decision | Reading |
|---|---|---|---|---|
| **H1: roads** | **1.277 (1.174–1.410)** | 0.001 | **SUPPORTED** | **REPLICATED** |
| **H2: roads away from valley floors** (no water or non-burnable cell within 300 m; tested because H1 is SUPPORTED) | **1.226 (1.110–1.355)** | 0.001 | **SUPPORTED** | **the road edge excess holds away from valley floors** |

- **Size of the effect.** The 0–90 m band beyond final perimeters holds about 28% more road than the land 150–600 m out.
  - The pilot's 1.45 lies **outside** this interval, so the excess is smaller here than in the pilot.
  - Away from valley floors the excess is 23%. In the pilot that check was post hoc and uncertain (1.19, 0.61–1.42).
- **H2's sample.** It keeps cells where 46% of the grid has no water or non-burnable cell within 300 m.

## Descriptive results (no confirmatory weight)

**Road classes, disjoint sample** (the class rasters reproduce the frozen road raster exactly):

| Class | E (95% CI) | p (upper) | Rule |
|---|---|---|---|
| Local roads (S1400) | 1.279 (1.177–1.421) | 0.001 | SUPPORTED |
| Highways (S1100, S1200) | 0.930 (0.262–1.735) | 0.50 | NOT SUPPORTED |
| Other vehicle roads (S1630–S1780) | 1.458 (0.768–2.343) | 0.018 | NOT SUPPORTED |

**Barrier types, disjoint sample:**

| Type | E (95% CI) | Decision |
|---|---|---|
| B (any barrier) | 0.935 (0.839–1.099) | INCONCLUSIVE |
| Water | 0.603 (0.328–0.697) | CONTRADICTED |
| Non-burnable | 0.770 (0.679–0.939) | CONTRADICTED |

**E_road by sample and subset:**

| Sample | Fires | E_road (95% CI) | Decision |
|---|---|---|---|
| All disjoint perimeters | 82 | 1.369 (1.201–1.573) | SUPPORTED |
| Disjoint, before 2010 | 13 | 1.532 (1.114–1.953) | SUPPORTED |
| Disjoint, 2010 on | 34 | 1.231 (1.140–1.344) | SUPPORTED |
| Without the largest cluster | 41 | 1.292 (1.163–1.436) | SUPPORTED |
| Without zones reaching north of 49°N | 45 | 1.286 (1.174–1.423) | SUPPORTED |
| Full sample (not independent of the pilot) | 91 | 1.379 (1.172–1.461) | SUPPORTED |

In every sample and subset, water and non-burnable ground are at or below 1 at the perimeter, and B is INCONCLUSIVE.

## What this does and does not show

- **It does show:** in a second region, with fires disjoint from the pilot's and under a rule frozen and registered before any edge statistic was computed, final fire perimeters run along roads more than the land just beyond them.
  - The excess is concentrated on local roads.
  - It holds away from valley floors, which counts against the leading alternative explanation from the pilot: that roads only mark the transition from burned slopes to valley floors.
  - Water and non-burnable ground show the reverse: perimeters tend to end short of them.
- **It does not show** why perimeters lie along roads. The alternatives are:
  - roads stop fire passively;
  - crews hold or burn out from roads;
  - perimeters are drawn along roads;
  - roads built later along old fire lines.

  The pilot's era split and this region's before-2010 subset show no sign that later roads inflate the effect, but they cannot rule it out.
- **One reading** is that roads act mainly through suppression access. P1C found no compartment-size effect in lightning-caused fires, and in the Flathead simulations roads did not help as passive walls at fixed corridor area. It is a hypothesis that the next test should separate, for example by comparing human-caused with lightning-caused fires, and road edges with and without crew access.

## Files

These are published next to the registration, in `preregistrations/p1m_p1c_v1.0_results/`. The registered folder is not touched.
- this report;
- `P1M_P1C_DECISIONS.json`;
- `MECH_RESULTS.json` and `mech_profile.png`;
- `ROADS_CHECKS.json` and `POSTHOC_ROADS.json`;
- `ROBUST.json`;
- `full_sample/MECH_RESULTS.json` and `full_sample/mech_profile.png`;
- every output's `.ots` proof, `REGISTRATION_P1M.json` and the run logs.

**Authorship.** Justin D. Hart (Viridis LLC) is the accountable author. Claude (Anthropic) designed the analysis and wrote and ran the code under his direction. Automated tools are not research authors.
