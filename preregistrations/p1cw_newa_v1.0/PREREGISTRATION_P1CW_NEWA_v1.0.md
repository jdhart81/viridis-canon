# P1C-W: preregistration of a wind-modification test of the compartment effect

Nov 11, 2026 · Version 1.0, frozen 11 Nov 2026 with Justin Hart's approval. Content identical to draft v0.2 apart from these status lines. Committed to viridis-canon as preregistrations/p1cw\_newa\_v1.0.

**Project:** P1C-W, a pre-specified effect-modification analysis of P1C (viridis-canon, preregistrations/p1c\_newa\_v1.4, registered 2026-10-22 as PR #138). **Author:** Justin D. Hart (Viridis LLC). Drafted by Claude (Anthropic) under the author's direction.

## 0. Decisions taken and what is left

Both design choices were settled on 11 Nov 2026 (Justin: "your call"): Stage 1 plus a blind Stage 2 in west-side Oregon, and the continuous wind interaction γ as the one confirmatory test, with the low-wind versus high-wind tercile contrast secondary (R4).

Status at freeze:

1. **Freeze Stage 1.** Approved by Justin on 11 Nov 2026 and done: plan, code, wind table and calibration are hashed in FREEZE.json, timestamped and committed to viridis-canon. Only now may wind and fire size be joined (§9).
2. **Stage 2 data run.** The Oregon blind fetch cannot run from the drafting environment, which cannot reach the LANDFIRE, TIGER, NHD or USFS servers. It runs from Justin's Mac after the Stage 1 freeze (§11).
3. **Outside review.** Whether to send the plan to Meg Krawchuk or Chris Dunn before the Stage 2 freeze is still open. No contact has been made.

## 1. Source of the hypothesis

P1C found that fires starting in smaller compartments of mapped barriers (TIGER vehicle roads, NHD water, LANDFIRE FBFM40 non-burnable 91, 92, 93, 98, 99; 30 m grid; 4-connected burnable patches; edge-touching compartments censored) end smaller: β = 0.0531 log₁₀ acres per log₁₀ compartment area under M2R (registered interval 0.0228 to 0.0835, T = 4.42, SUPPORTED), about 13% larger fires per tenfold larger compartment. M2R has no wind term.

Matt Betts (OSU, email of 10 Nov 2026) wrote that west-side fire response is heavily weather dependent: in high wind nothing holds (he cited the Holiday Farm fire), in low wind roads can work, and at the Lookout Fire the road network did nothing once winds rose around 25 August. That is an expert's field observation, not a measured result; this plan turns it into a test.

**Mechanistic reading (interpretation, not tested directly).** A compartment boundary constrains final size only when it holds. Let p\_hold(w) be the probability that a barrier segment stops spread at wind speed w. Wind tilts the flame, raises convective and radiative flux across the barrier and lengthens spotting distance, so the effective breach length scale ℓ(w) grows with w. When ℓ(w) exceeds barrier width, the boundary stops acting as a constraint on the spread process and compartment area carries no information about final size. The observable slope is then approximately β(w) ≈ β₀ · p\_hold(w), which falls with w. A suppression-access mechanism (crews reach small compartments faster) predicts the same sign, because high wind also defeats initial attack. A negative interaction therefore supports "barriers matter less in wind" but does not by itself separate fuel-break physics from access (§10).

## 2. What is already known (disclosure)

- P1C outcomes for all 14,105 ignitions were fetched on 2026-10-22 and are public in p1c\_newa\_v1.4\_results. The primary β, and the sensitivities S6a (lightning only, M2: −0.015, −0.062 to 0.033), S6b (human only, M2: 0.054, 0.031 to 0.076), S13 (no regional terms: 0.033, NOT SUPPORTED) and S5 (burn scars as barriers: 0.020) are known.
- ERA5 hourly wind for Dec 1991 to Jan 2025 was fetched on 11 Nov 2026, and the wind table was built from discovery dates and locations only. No statistic joining wind to fire size has been computed. The northeast Washington outcomes file was never loaded in this work; the calibration code asserts it is absent.
- This plan is therefore registered **before the wind join, not before the outcomes**. Its blindness is procedural: freeze plan, code and the wind predictor table, then join. Its evidential weight is below P1C's, which is why Stage 2 exists.
- The cause interactions in M2R-W (§5) were chosen after S6a and S6b were seen.
- The Stage 2 region was chosen around fires Betts named. Holiday Farm, Beachie Creek and Lookout are publicly known large, wind-driven fires inside the Stage 2 box, so some Stage 2 outcomes are known to the authors. R13 (§8) repeats the Stage 2 test without them.
- The date-effect stress screen (§7) used residuals from the pilot region (Okanogan, Methow, Chelan), whose outcomes were public before P1C. No wind entered that screen.

## 3. Invariants (must hold for the run to count)

- **I1 Sample.** Identical to P1C v1.4 definition B: 11,314 usable ignitions, same barrier rasters, censoring and exclusions. The only new exclusion is missing wind, counted and reported.
- **I2 Exposure window.** Defined from discovery date alone. No containment date or any outcome-linked field enters the wind variable.
- **I3 Critical value.** C\_W ≥ 2.53 (the P1C C2). Recalibration can only raise it.
- **I4 Order.** No statistic combining wind and fire size is computed before the freeze record is hashed and timestamped.
- **I5 One primary estimand.** γ, defined in §5. Everything else is reported but carries no decision weight.

## 4. Wind data and exposure

| Source | Resolution | Years | Use |
| --- | --- | --- | --- |
| ERA5 hourly 10 m u and v (ECMWF reanalysis, public NSF NCAR mirror, dataset ds633.0) | 0.25° (about 28 km), hourly | 1940 to present | **Primary, both stages.** Fetched 11 Nov 2026 for 49.5 to 43.25 N, 123.0 to 116.5 W; every request logged with URL and time. |
| gridMET vs (daily mean 10 m wind) | about 4 km, daily | 1979 to present | Primary in v0.1. Its server is unreachable from the drafting environment, so v0.2 uses ERA5 in both stages for one consistent exposure. |
| ERA5-Land 10 m u and v | about 9 km, hourly | 1950 to present | Not on the public mirror used; dropped. |
| RAWS station records | point | variable | Rejected: sparse in this region, gaps, station-to-ignition distance error. |
| HRRR | 3 km, hourly | 2014 on | Rejected: covers about a third of the years. |

**Exposure.** W3 = maximum hourly 10 m wind speed (m/s), interpolated bilinearly to the ignition point, over the discovery day and the two following days (d0 to d2). Days are local standard days (UTC−8, 08:00 to 07:00 UTC); d0 is the FPA FOD discovery date. Rationale: initial attack and the first burning periods decide whether a fire is held at a compartment boundary. Secondary windows: W1 (d0 only) and W7 (d0 to d6, closer to Betts's Lookout example, where wind rose days into the fire).

**Scaling.** z\_w = (W3 − mean) / SD, with mean and SD computed on the blind predictor table (no outcomes): 4.13 m/s and 1.26 m/s over the 11,314 usable ignitions. Absolute speed is primary because the holding mechanism is physical; the per-point percentile of W3 among all 1992–2024 three-day windows is robustness R1.

**Known limitation.** A 28 km grid smooths ridge-top gusts and terrain channelling more than gridMET's 4 km would. It measures the synoptic wind regime, not fire-scale wind. The hourly maximum partly offsets this by keeping afternoon peaks that a daily mean loses. The remaining error is classical in the exposure and biases γ toward zero, against the hypothesis.

ERC (fuel model G) has no wind term, so wind is not already absorbed by the ERC control.

## 5. Model

Let L = log₁₀ A\_enc, centred at the blind-sample median (3.63).

**M2R-W:** M2R + z\_w + L × z\_w + L × cause + z\_w × cause.

- M2R is unchanged: L, ERC percentile, fuel group, cause, month, year, log₁₀(barrier density + 0.001), log₁₀(road distance + 30 m), and 40 km region fixed effects.
- **Primary estimand γ:** the coefficient on L × z\_w, the change in the compartment slope per +1 SD of wind, within cause.
- **Why the cause interactions:** lightning fires show no slope (S6a), and lightning days may differ in wind. Without L × cause, the cause mix would load onto γ and could manufacture an apparent wind effect.
- **Directional prediction, stated before data:** γ < 0. Descriptively, the low-wind tercile slope exceeds 0.053 and the high-wind tercile slope is near zero and below the low-wind slope.

**Tercile display (pre-specified, descriptive):** cut points of z\_w fixed on the blind table; M2R fitted within each tercile; β\_low, β\_mid, β\_high reported with the registered interval.

## 6. Human and lightning fires

The primary model pools causes with the interactions above. Pre-specified secondaries:

- **Human only** (n ≈ 6,915 under M2 in S6b): M2R + z\_w + L × z\_w. Predicted γ\_human < 0. This is where the effect lives, so it is the most informative subset.
- **Lightning only** (n ≈ 4,226): reported, no directional prediction, because there is no main slope to attenuate.
- Missing cause is handled exactly as in v1.4.

## 7. Inference and decision rule

- **Standard errors:** as v1.4. SE₂ two-way clustered by year and 20 km block; SE\_year clustered by year. T\_W = γ / max(SE₂, SE\_year).
- **Critical values:** C\_W is the 95th percentile of |T\_W|, maximised over a family of error models simulated under the null (γ = 0) on this design with the frozen wind variable attached, 4,000 replicates each, before any join. C\_W = max(2.53, that value, rounded up to 0.01). C1\_W is the same with the 90th percentile and a floor of 2.08. The family is:
  - the 81 models of the P1C screened family (iid, block, block plus field, retained blocks and fields);
  - the 52 retained P1C stress models (anisotropic fields, long-range exact fields, compartment effects);
  - new S-D: random effects shared by all ignitions discovered on the same date, at each share a pilot screen retains (wind is near-constant within a date, so this is the error structure most likely to fake γ);
  - new S-H: noise whose SD rises with wind (a = 0.25 and 0.5), unscreened.
- **Verdicts:**
  - **SUPPORTED** (attenuation) if γ ± C\_W × max SE lies entirely below 0.
  - **CONTRADICTED** (amplification) if it lies entirely above 0.
  - **WIND-INVARIANT** if γ ± C1\_W × max SE lies entirely inside ±γ\_min, with γ\_min = 0.0265 per SD (the slope halving for +1 SD of wind).
  - **INCONCLUSIVE** otherwise.
- **Falsification.** The wind-holding mechanism, as operationalised here, is falsified in this region by CONTRADICTED or WIND-INVARIANT.

**Calibration result (11 Nov 2026): both floors bind, so C\_W = 2.53 and C1\_W = 2.08.** The run used all 140 error models at 4,000 null replicates each on the blind design (n = 11,314, 83 columns). The largest 95th percentile of |T\_W| was 2.22 (anisotropic north-south field, share 0.20, 20 × 180 km, the same model that bound P1C's C2). The largest 90th percentile was 1.86 (field share 0.40, range 180 km). The date-effect screen retained shares 0.01 to 0.08 against a pilot share of 0.006; none of the five came near the binding value, nor did S-H. Monte Carlo error on a 95th percentile at 4,000 replicates is about ±0.03, well inside the 0.31 gap to the floor. False-call rate at the 2.53 rule across all models: 1.2% to 3.0%.

**Power and recovery** (2,000 simulated datasets per cell, true β = 0.053 planted, share of runs giving each verdict):

| True γ per SD | SUPPORTED, iid errors | SUPPORTED, binding error model | WIND-INVARIANT, binding model |
| --- | --- | --- | --- |
| 0 | 0.6% | 1.1% | 13% |
| −0.02 | 17% | 22% | 5% |
| −0.03 | 45% | 48% | 1% |
| −0.04 | 73% | 74% | 0.3% |
| −0.053 (full attenuation at +1 SD) | 95% | 95% | 0% |

The estimator is unbiased (mean γ̂ within 0.0004 of the planted value in every cell) with SD(γ̂) of 0.012 to 0.014, close to SE(β), as v0.1 assumed. CONTRADICTED never occurred under a negative γ. Reading: Stage 1 detects strong attenuation (73% power at −0.04) but is a coin flip for moderate attenuation, and WIND-INVARIANT will rarely be reached even if wind truly does nothing (13%). A null Stage 1 result will most likely read INCONCLUSIVE, which is why Stage 2 matters.

## 8. Robustness (all reported, none decisive)

- **R1** per-point wind percentile (W3\_pct) instead of absolute speed.
- **R2** W3mean: the maximum over d0 to d2 of the daily mean speed, the closest analogue of a gridMET daily mean.
- **R3** windows W1 and W7.
- **R4** tercile contrast β\_low − β\_high with its interval.
- **R5 placebo:** W3 computed for d0−30 to d0−28 (P3). Predicted γ\_placebo ≈ 0. A non-null placebo means the wind variable is proxying place or season.
- **R6** add L × ERC percentile, to separate wind from fuel dryness.
- **R7** add L × month, to exclude seasonality in both wind and suppression.
- **R8** S10 and S10b exclusions (pilot box, pilot-fetched MTBS perimeters).
- **R9** M2-W without regional terms (the S13 analogue).
- **R10** fires of at least 10 acres (escaped fires, H3 analogue), where perimeter holding is most relevant.
- **R11** leave-one-year-out; any year whose removal changes the verdict is named.
- **R12** stacked with the pilot region (Okanogan, Methow, Chelan) under M2R-W, descriptive only.
- **R13** (Stage 2 only) drop ignitions discovered 15 Aug to 15 Sep 2020 and 1 to 31 Aug 2023, the windows of the publicly known Beachie Creek, Holiday Farm and Lookout fires.

## 9. Freeze procedure

1. Fetch ERA5 hourly 10 m u and v for Dec 1991 to Jan 2025 over 49.5 to 43.25 N, 123.0 to 116.5 W, logging every request. **Done 11 Nov 2026:** 398 months, 796 logged requests, none failed.
2. Build wind\_blind\_newa.csv (fod\_id, W1, W3, W7, W3mean, P3, W3\_pct) with no outcome column read (asserted in code). **Done:** 14,105 rows, no missing values. SHA-256 6c90bd47…1148.
3. Run the C\_W calibration and power simulation on the blind design. **Done:** CALIBRATION\_WIND.json, SHA-256 6fb08c33…56dc16; results in §7.
4. Synthetic check: planted γ from 0 to −0.053 recovered without bias; false calls 0.6% to 2.5% at γ = 0. **Done** (§7).
5. Hash this plan, the code, the wind table and the calibration in FREEZE.json, add an OpenTimestamps proof, and commit to viridis-canon as preregistrations/p1cw\_newa\_v1.0. **Approved 11 Nov 2026; done in the commit that adds this file.**
6. Only then join outcomes and run once.

All files are in the project folder p1cw (scripts, wind table, calibration, request log, raw ERA5 months). FREEZE.json in the committed folder holds the SHA-256 of every frozen file and of the P1C files this test reads.

## 10. Known threats

- **Outcomes already seen** (§2). The plan's structure was chosen after P1C's results, including the cause interaction.
- **Wind and suppression resources are confounded.** High-wind days bring multiple starts and resource draw-down. A SUPPORTED verdict shows the compartment effect fades in wind; it does not show whether that runs through barrier physics or crew availability.
- **Exposure scale.** ERA5 at 0.25° is coarse in complex terrain (§4).
- **Barrier maps from 2024** applied to 1992–2024 fires, as in P1C.
- **Observational design.** No causal claim beyond effect modification.

## 11. Stage 2: blind west-side confirmation (decided 11 Nov 2026)

Stage 2 asks two questions where large fires are weather-driven: does the compartment effect exist at all, and does wind remove it? It runs with the P1C machinery, and no Stage 2 outcome is requested until its own freeze.

- **Region.** Western Oregon Cascades, forested Willamette basin: 122.8 to 121.9 W, 43.5 to 45.0 N. The EPSG:5070 analysis and compute boxes and the 30 m grid (4,822 × 7,013 cells) are fixed in stage2\_oregon\_p1\_config.json, written before any fire record for the box was requested. The box contains the Holiday Farm, Beachie Creek and Lookout fires (§2).
- **Data.** Same sources and code as P1C: FPA FOD predictor fields only, TIGER vehicle roads, NHD water, LANDFIRE FBFM40, gridMET ERC. Wind comes from the ERA5 table already fetched, whose box covers Oregon. Washington DNR land data do not cover Oregon, so barrier definitions A50 and A25 are dropped and B is primary.
- **Two confirmatory tests,** each with its own critical values calibrated on the Oregon blind design: (1) β under M2R with P1C's decision rule; (2) γ under M2R-W with the rules of §7. Fire regime and cause mix will differ from northeast Washington; that is part of the test, not a nuisance.
- **Power gate, fixed now.** If the blind Oregon design gives under 50% power for SUPPORTED at γ = −0.04, Stage 2's γ test is reported as descriptive only. That is decided from the blind simulation, before outcomes.
- **Order.** Stage 1 freeze, then the Oregon blind fetch and calibration from Justin's Mac, then the Stage 2 freeze, then one outcome fetch and one run.
- **Running it.** One copy-paste Cowork prompt, drafted after the Stage 1 freeze, runs the blind fetch, builds the predictor and wind tables, runs both calibrations and returns file hashes. It never calls fetch\_outcomes.py.

Betts suggested Meg Krawchuk and Chris Dunn as people to bring these findings to. They are candidate external reviewers before the Stage 2 freeze; no contact has been made.

## 12. Assumptions (defaults taken)

- **A1** Wind source ERA5 hourly 10 m wind at 0.25°, in both stages. gridMET was the v0.1 default but cannot be fetched from the drafting environment.
- **A2** Window W3 (d0 to d2). Alternatives W1 and W7 are robustness.
- **A3** Absolute speed, standardised. Per-point percentile is robustness.
- **A4** γ\_min = 0.0265 per SD for the invariance reading. This is a judgement about the smallest attenuation worth caring about.
- **A5** Pooled-cause primary with cause interactions. Alternative: human-only primary (more direct, but chosen after seeing S6b).
- **A6** Continuous primary, tercile contrast secondary (decided).
- **A7** Wind direction relative to compartment geometry is left out; it is a richer test but needs perimeter-scale data and belongs in a later plan.
- **A8** Gust is not used. ERA5 gust files are too large to read from the drafting environment, and gust adds little over the hourly maximum at 28 km.
