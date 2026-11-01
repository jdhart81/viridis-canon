# P1-M: do fire perimeters run along mapped barriers? A mechanism test on the pilot region

- **Plan written:** 2026-10-21, before any perimeter was compared with any barrier on real data. It is frozen with the code by hash (`MECH_FREEZE.json`) and stamped with OpenTimestamps before the real run.
- **Author:** Justin D. Hart, Viridis LLC. Claude (Anthropic) designed the analysis, wrote the code and runs it under the author's direction.
- **Status:** exploratory and pre-specified. It is not part of the P1C confirmatory test, and it uses no P1C (northeast Washington) data. The P1C region's MTBS perimeters stay untouched until the P1C test has run.

## 1. Question and prediction

*Trees Cannot Cut* (TCC) says fires end where closed loops of holdable features stop them. The P1 pilot found the predicted correlation: ignitions in smaller compartments of mapped barriers ended smaller (β = 0.063 log₁₀ size per log₁₀ compartment area). A correlation can arise without barriers stopping anything, for example if small compartments are simply places where suppression arrives fast.

**The mechanism prediction.** If barriers stop fires, final fire perimeters lie against barriers. The land just beyond a perimeter should then hold more barrier cells than the land a little farther out.

## 2. Data (pilot region only)

| Input | What it is |
|---|---|
| `p1/compartments_static.npz` | The pilot's definition-B barrier rasters on the 30 m EPSG:5070 grid: `road` (TIGER vehicle roads), `water` (NHD river areas, lakes and reservoirs) and `nonburn` (LANDFIRE 2024 non-burnable). |
| `p1/raw/mtbs_perims.json` | MTBS burned-area perimeters in the pilot compute box: 275 features, 1984–2024, with geometry and year only. |
| `p1/raw/fpafod_ignitions_blind.json` | The pilot's blind FPA FOD ignition table: locations and years only. |
| `p1/p1_config.json`, `p1/build_predictors.py` | The grid, plus the builder's own polygon reading and rasterization (cell-centre rule). |

Before writing this plan I looked at three things: the MTBS file's structure, its feature count by year, and the FPA FOD file's fields. Before the freeze I also ran the sample-construction step alone, without reading the barrier map (`SAMPLE_QA.json`). It covers rasterization, inclusion, wildfire matching and clustering, and it found:
- 190 of the 275 perimeters included; the other 85 lie outside the analysis box;
- a primary sample of 102 matched wildfires (1992–2023) in 24 clusters, the largest holding 51 fires;
- all perimeters together: 190 fires in 44 clusters.

No perimeter was compared with any barrier.

## 3. Samples

- **A fire.** One MTBS perimeter feature. It is included if:
  - its polygon intersects the pilot analysis box;
  - its zone (burned cells plus 600 m) lies on the compute grid;
  - it has at least 20 burned cells.
- **Primary sample: matched wildfires.** Perimeters of 1992–2024 that contain, or lie within 300 m of, at least one FPA FOD ignition of the same year.
  - MTBS also maps prescribed burns, whose edges are planned along roads.
  - FPA FOD lists only wildfires, so the match removes the prescribed burns.
- **Secondary samples:**
  - all perimeters, of any year;
  - the primary sample split at 2010.
- **Clusters.** Fires whose zones share a cell, directly or through other fires, form one cluster. Reburns and neighbours share landscape, so clusters are the independent units.

## 4. Statistic, inference and decision

**The edge ratio.** For each barrier type t (B = any of road, water, non-burnable; road; water; non-burnable), pooled over fires:

E_t = (share of barrier-t cells among unburned cells 0–90 m beyond the perimeter) ÷ (the same share 150–600 m beyond it)

- Distances are Euclidean distance transforms, measured between cell centres on the 30 m grid.
- E = 1 when perimeters ignore barriers.

**Inference.**
- **Bootstrap.** A 95% percentile interval from 2,000 bootstrap resamples of clusters (seed 1).
- **Shift null.** Each cluster's masks, with all their bands, are moved rigidly by one random whole-cell vector, and E is recomputed from the barrier map at the new place.
  - The vector is drawn from the shifts that keep the cluster's zones on the grid, with length uniform on 2–6 km and direction uniform.
  - 1,000 replicates (seed 2), with clusters shifted independently.
  - p_shift = (1 + #{E_null ≥ E_obs}) / 1,001.

**Decision**, for the primary statistic E_B on the primary sample:
- **SUPPORTED** if the interval lies above 1 and p_shift < 0.025.
- **CONTRADICTED** if the interval lies below 1 and the lower-tail p < 0.025.
- **INCONCLUSIVE** otherwise.

The same rule is reported for every type and sample. Those results are secondary.

**Secondary descriptions:**
- the inside ratio C_t: the barrier share among burned cells 150–600 m inside the perimeter, divided by the outside reference share;
- the profile of barrier share by signed distance, in 30 m bins from −600 to +600 m, with the shift null's 95% band;
- the cell counts in each band.

## 5. Validation before the real run (`SYNTHETIC_CHECK.json`)

The code was run on synthetic 60 × 60 km landscapes with random roads, lakes and non-burnable patches, 40 fires each, using 500 bootstrap and 300 shift replicates.

- **Mechanism worlds:** fires grew by random spread that barriers stop. Primary decision for B: 5 of 5 SUPPORTED.
- **Null worlds:** fires grew the same way but ignored barriers.
  - Primary decision for B: 1 of 60 SUPPORTED and 0 CONTRADICTED.
  - Mean E_B under the null: 1.009.
- No real data was read.

## 6. Limitations stated in advance

- **Modern maps.** Roads, water and fuels are mapped now: TIGER, NHD and LANDFIRE 2024. Older fires therefore meet roads built after them. That pushes E toward 1, unless roads were later built along old fire lines, which pushes it up. The 2010 split checks this.
- **LANDFIRE 2024 and recent burns.** It may map some recently burned ground as non-burnable. If that ground is slightly misregistered against MTBS edges, it could raise the non-burnable edge share. The road result is immune to this.
- **How MTBS draws edges.** Perimeters are mapped from burn severity, and a road can be where burned and unburned pixels meet. That is part of what "stopped at a road" looks like, and it cannot be separated here.
- **Passive and active stopping.** A perimeter at a road may come from a burnout lit from the road rather than from the road itself. TCC counts both, because holdable features are where suppression holds. This test does not tell them apart.
- **Spatial dependence.** Clusters handle overlapping fires. Dependence between clusters that do not overlap is not modelled.
- **Few independent units.** One cluster holds half of the primary sample, the reburns of the Methow and Chelan valleys. The bootstrap therefore rests on 24 units, and its interval will be wide if that cluster differs from the rest.
- **The barrier types differ in how much they can show.** Water and non-burnable ground are fuel breaks by definition. Roads are the most informative type for TCC's claim about holdable features.

## 7. What happens next

- **Reporting.** The results are reported whatever they are: `MECH_RESULTS.json`, the profile figure and a short report.
- **If SUPPORTED.** A confirmatory version for the P1C region will be pre-registered only after the P1C test has run, never before, using this code unchanged.
- **Deviations.** Any change after the freeze is reported as a numbered deviation.
