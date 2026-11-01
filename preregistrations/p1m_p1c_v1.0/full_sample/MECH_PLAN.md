# P1-M confirmatory test for the P1C region: do final fire perimeters run along roads?

**Status:** plan v1.0. Written and frozen before any P1-M edge statistic was computed for P1C perimeters. Prepared by Claude (Anthropic) for Justin D. Hart (Viridis LLC), 2026-10-22, after the P1C result.

**Region.** P1C, northeast Washington: eastern Okanogan, Ferry, Stevens and Pend Oreille counties. The analysis and compute boxes and the 30 m EPSG:5070 grid are those of `p1c/p1_config.json`. The primary sample excludes everything near the pilot region (§4).

## 1. Why this test, and what was already known when it was written

**In the pilot region** (Okanogan, Methow and Chelan), the pre-specified P1-M test asked whether the land just beyond final fire perimeters holds more mapped barrier than the land a little farther out. Its results (`p1mech/MECH_REPORT.md`):
- **All barriers together (its primary):** INCONCLUSIVE. E_B = 0.97 (0.87–1.05).
- **Roads (a pre-specified secondary): SUPPORTED in every pilot sample.**
  - In the primary sample, E_road = 1.45 (1.23–1.58), shift-null p = 0.001.
  - Across samples, E_road ranged from 1.30 to 1.48.
- **Post hoc:** the excess sat on highways (2.40) and local roads (1.39). Away from valley floors it shrank to 1.19 (0.61–1.42; shift-null p = 0.007).
- **Water:** CONTRADICTED. E = 0.65.
- **Non-burnable ground:** inconclusive.

**Disclosure 1: this plan departs from the pilot plan.**
- The pilot plan (`p1mech/MECH_PLAN.md` §7) said a P1C version would follow if E_B were SUPPORTED. It was INCONCLUSIVE.
- This plan instead takes as its primary hypothesis the only pilot result that was SUPPORTED: roads.
- That is a choice made after seeing the pilot results. It is legitimate only because the data are new and disjoint from the pilot (§4).

**Disclosure 2: P1C results seen before this plan was written.**
- P1C (compartment size and final fire size; registered 2026-10-22 as viridis-canon PR #138) was SUPPORTED: β = 0.053 (registered interval 0.023–0.084).
- Its sensitivity checks (no decision weight) showed:
  - no effect in lightning-caused fires (S6a: −0.015, −0.062 to 0.033);
  - a smaller effect without regional terms (S13: β = 0.033, NOT SUPPORTED against 3.93).
- Those results used ignition points, fire sizes and compartments, not perimeter edge profiles. No P1-M edge statistic (E, profile or shift null) has been computed for any P1C perimeter.

**The question.** Does the pilot's road edge excess replicate in a new, disjoint region? If it does, does it survive away from valley floors? The pilot could not settle the second question.

## 2. Code (frozen, run unchanged)

- **`p1mech/mech_test.py`**, sha256 `85d4f45f4a6b0e2009e5fd0783040655c13a4487f15f221371219863d2760893`.
  - Frozen for the pilot in `p1mech/MECH_FREEZE.json` (sha256 `c54863a7…`), confirmed in Bitcoin block 972546.
- **`p1mech/posthoc_roads.py`**, sha256 `d61013e972208721d3fbe08fab129ff79f3f1892daf148b5c6040bfb00adcfff`.
  - These are the pilot's post hoc road checks. They were hash-recorded in `p1mech/POSTHOC_ROADS.json` but not frozen before their pilot run.
  - Here they are pre-specified, and they are run unchanged.
  - They were never checked on synthetic data, which is a limit (§8).
- **`run_p1c_mech.py`** (this folder) runs both on the P1C inputs.
  - It checks both hashes, then sets the code's input folder, input table and output folder.
  - It replaces or edits no function. For the robustness subsets it calls the frozen `analyse()` on subsets of the fires that the frozen `build_pilot_fires()` produced.
  - It adds fields under new names: the correct region label, this plan's primary, the variant and the subset sizes. It overwrites none of the frozen code's fields.
- **`make_disjoint_perims.py`** builds the primary perimeter input (§4).

Copies of the frozen code, of the pilot freeze record and of both its proofs are in `frozen_pilot_code/` for public checking.

**Calibration** (`p1mech/SYNTHETIC_CHECK.json`):
- **Planted mechanisms:** 5 of 5 were called SUPPORTED, for B and for roads.
- **60 null-world tests:** B was falsely called SUPPORTED once. Roads were falsely called SUPPORTED once and CONTRADICTED once.

This calibrates the rule; it does not show power for realistic effects.

## 3. Inputs (all hashed in the freeze record)

- **`p1c/compartments_static.npz`:** the road, water and non-burnable rasters (definition B).
  - Pinned by the publicly registered P1C package's `SHA256SUMS.txt` (sha256 `d6fd8cb7…`; PR #138). `p1c/FREEZE.json` does not list it.
- **`p1c/raw/mtbs_perims.json`:** all MTBS perimeters fetched for P1C. Pinned in `p1c/FREEZE.json`.
- **`mtbs_perims_disjoint.json`** (this folder): the same file without perimeters near the pilot (§4). This is the primary perimeter input.
- **`p1c/raw/fpafod_ignitions_blind.json`:** FPA FOD ignition locations and years, for wildfire matching. Pinned in `p1c/FREEZE.json`.
- **`p1c/p1_config.json` and `p1c/build_predictors.py`:** the grid and the rasterizing functions. Pinned in `p1c/FREEZE.json`.
- **`p1c/raw/roads_primary.json`, `p1c/raw/roads_secondary.json`, `p1c/raw/roads_local.json`:** TIGER roads with MTFCC classes. Pinned in `p1c/FREEZE.json`.

## 4. Samples

**Disjoint from the pilot.** `make_disjoint_perims.py` drops every P1C perimeter that intersects the pilot compute box (`p1/p1_config.json`), widened by 600 m. It reads perimeter geometry only.
- **Why that guarantees disjointness:** pilot perimeters lie at least 660 m inside that box, because the frozen code kept a fire only if its zone fit on the grid. So kept fires share no fire and no zone cell with the pilot sample.
- **Count:** 137 of 262 perimeter features are dropped (`DISJOINT_FILTER.json`).

**As implemented in the frozen code:**
- **Inclusion:** perimeters that intersect the P1C analysis box, rasterized on the 30 m grid, with at least 20 burned cells and their ±600 m zone on the grid.
- **Primary sample:** disjoint perimeters of 1992–2024 matched to an FPA FOD wildfire of the same year, meaning an ignition inside the perimeter or within 300 m of it.
  - Matching to a recorded wildfire largely excludes prescribed burns. It does not exclude them strictly.
- **Clusters:** fires that share any zone cell (cells within 600 m of a perimeter on either side), joined by union-find. This is the code's rule; the pilot report's Deviation 1 recorded that the pilot plan's wording differed.

**Sample sizes, recorded before the freeze without reading the barrier map** (`SAMPLE_QA.json`):

| Sample | Fires | Clusters | Largest cluster |
|---|---|---|---|
| **Primary, disjoint, 1992–2024** | **47** | **30** | 6 |
| Before 2010 | 13 | 12 | 2 |
| 2010 on | 34 | 25 | 3 |
| All disjoint perimeters | 82 | 37 | 11 |
| **Full sample** (secondary; all P1C perimeters, including those near the pilot) | 91 | 35 | 39 |

The full sample is recorded in `full_sample/SAMPLE_QA.json`.

## 5. Statistic and inference (the frozen code)

- **Statistic.** E_t is the share of barrier type t in the 0–90 m band beyond the perimeter, divided by its share in the 150–600 m band beyond it.
- **Interval.** A 95% cluster bootstrap: 2,000 replicates, seed 1.
- **Null.** A rigid-shift null: 1,000 replicates, seed 2. Each cluster moves by 2–6 km to feasible positions (lattice-weighted exact sampling).

## 6. Hypotheses, decisions and readings

**H1, primary: roads.** E_road > 1 in the primary (disjoint) sample. The frozen rule:
- **SUPPORTED** if the 95% interval lies above 1 and the shift-null upper p < 0.025;
- **CONTRADICTED** if the interval lies below 1 and the lower p < 0.025;
- **INCONCLUSIVE** otherwise.

**Reading of H1:**
- SUPPORTED: **REPLICATED**. SUPPORTED tests the direction, not the pilot's magnitude; the report states whether the interval contains the pilot's 1.45.
- INCONCLUSIVE: **NOT REPLICATED** (inconclusive).
- CONTRADICTED: **CONTRADICTED**.

**H2, tested confirmatorily only if H1 is SUPPORTED (a fixed sequence).** E_road away from valley floors: only cells with no water and no non-burnable cell within 300 m count, in both bands. The frozen `posthoc_roads.py` runs this on the primary sample.
- **SUPPORTED** if its 95% interval lies above 1 and its shift-null upper p < 0.025; **NOT SUPPORTED** otherwise.
- There is no CONTRADICTED category, because that code gives no lower-tail p.
- An interval that is not finite counts as NOT SUPPORTED.

**Joint reading:**

| H1 | H2 | Reading |
|---|---|---|
| SUPPORTED | SUPPORTED | The road edge excess replicates, and it holds away from valley floors. |
| SUPPORTED | NOT SUPPORTED, interval upper bound < 1.10 | It replicates, but valley floors account for it: there is no excess of 10% or more away from them. |
| SUPPORTED | NOT SUPPORTED otherwise | It replicates; away from valley floors is undetermined. Low power and a valley-floor effect cannot be told apart. |
| not SUPPORTED | (any) | H2 is reported descriptively, with no reading. |

**Descriptive results.** These are reported in full, carry no confirmatory weight, and use the same rules:
- **Road classes on the primary sample:**
  - highways (S1100, S1200);
  - local roads (S1400);
  - other vehicle roads (S1630, S1640, S1730, S1740, S1780).

  The classes reproduce the frozen road raster exactly (`UNION_CHECK.json`, before the freeze).
- **Barrier types:** B, water and non-burnable, in every sample of the frozen code.
- **Two subsets of the primary sample, run with the frozen `analyse()`:**
  - **without the largest cluster:** 41 fires;
  - **without fires whose zone reaches north of 49°N:** 45 fires. There are no TIGER roads in Canada, so a reference band that reaches into Canada while the edge band does not would inflate E_road.
- **The full sample:** 91 fires, including those near the pilot. Its results are not independent of the pilot.

**Edge cases fixed in advance:**
- A sample with fewer than 5 fires is not analysed. This is the frozen rule.
- If a cluster has no room for a shift, the frozen code stops. Every cluster had room in the sample check.
- If the road-class union failed at run time, the classes and H2 would be reported as not computed. The union check before the freeze passed with the library versions recorded.

**Multiplicity.** H1 is the confirmatory test. H2 is confirmatory only through the fixed sequence.

## 7. Order of operations

1. Steps before the freeze, all done without reading the barrier map together with any perimeter:
   - `make_disjoint_perims.py`;
   - `run_p1c_mech.py sample primary`;
   - `run_p1c_mech.py sample full`;
   - `run_p1c_mech.py union`, which reads the barrier map but no perimeter.
2. An independent review by an agent that did not write the plan. Its findings are addressed here.
3. **Freeze.** `freeze_p1c_mech.py` writes `MECH_FREEZE.json` and an OpenTimestamps proof.
   - The record holds hashes of this plan, the scripts, the disjoint input, the sample and union checks, the frozen code, the pilot freeze record and every input.
   - The freeze refuses to run if any result file exists.
   - A later upgraded proof is kept in `ots_upgraded/`, never in place, because the registration check compares the stamped file.
   - If the freeze fails, for example because the proof cannot be written, its partial record is deleted and the freeze is re-run. That is safe because no result exists.
4. **Public registration**, authorized by Justin. `verify_p1m_registration.py` downloads every frozen file in this folder anonymously from the registered commit, and writes `REGISTRATION_P1M.json` only if all of them match.
5. **Run.** The runner refuses to run until steps 3 and 4 are complete. Each result is stamped with OpenTimestamps as soon as it is written.
   - `run_p1c_mech.py real primary`
   - `run_p1c_mech.py roads`
   - `run_p1c_mech.py robust`
   - `run_p1c_mech.py real full`
   - `run_p1c_mech.py decide`
6. **Report** every number in the result files, whatever they show, in a separate results folder.

Any departure from this plan after the freeze is reported as a numbered deviation.

## 8. Limits

- **Observational.** A road at a final perimeter may:
  - have stopped the fire;
  - have been the line crews held or burned out from;
  - mark a fuel or valley-floor transition;
  - be where the perimeter was drawn.

  H2 addresses the transition. The rest are not separable here.
- **Roads are mapped now.** Later roads built on fire lines would inflate E_road; roads placed without regard to fires would dilute it.
- **Canada.** Perimeters that reach past 49°N bias E_road in either direction, depending on which band crosses the border. A descriptive subset addresses this (§6).
- **Smaller sample than the pilot.** The disjoint sample has 47 fires in 30 clusters, against the pilot's 102 in 24. Its zones hold 1.93 million cells, against the pilot's 7.01 million. Power was not computed formally, and an INCONCLUSIVE result may reflect low power rather than the absence of an edge excess.
- **Unchecked code.** The H2 and road-class code was never checked on synthetic data.
