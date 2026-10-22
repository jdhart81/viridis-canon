# Pre-registration: confirmatory test in northeast Washington — do real fires stay smaller inside small compartments?

**Project:** P1C, the confirmatory test that follows P1 ("Trees Cannot Cut on real fires").
**Version:** 1.4. It supersedes v1.0, v1.1, v1.2 and v1.3, all frozen and timestamped but never published (§0).
**Author:** Justin D. Hart (Viridis LLC). Analysis designed and run by Claude (Anthropic) under the author's direction.

**Status at freeze**
- **Not requested:** no FPA FOD fire size, size class or containment field for any ignition in this region has been requested or stored.
- **Exception, large-fire perimeters (MTBS):** during the pilot, their full attribute records were received for part of this region. Only geometry and year were kept. See "Known limits of blindness" in §3.
- **Frozen:** the plan, code, blind predictor table, raw inputs and logs are hash-frozen in `FREEZE.json`. It has been submitted to OpenTimestamps for Bitcoin timestamping.
- **Guarded:** `fetch_outcomes.py` requests outcomes only if three guards pass, re-run immediately before the request:
  - **G1:** every frozen file is unchanged;
  - **G2:** it downloads the public copy of this file and of `FREEZE.json` and finds them byte-identical;
  - **G3:** the sample shares no ignition with the pilot.

## 0. Version history

Each version was frozen with hashes and an OpenTimestamps submission. Each was then audited by a separate agent that had not built the study. No earlier version was published. Their plans, code and freeze records are kept in `history_v1.0/` to `history_v1.3/`, and the four audit reports are shipped verbatim (`AUDIT_1_of_v1.0.md` to `AUDIT_4_of_v1.3.md`).

**v1.0**, frozen 2026-10-20 23:58:20 EDT (`FREEZE.json` sha256 `eef249f9…`). The audit's mechanical checks all passed. It found:
- **C1:** an inaccurate blindness statement about MTBS attributes.
- **M1:** a registration guard that trusted a local file.
- **M2:** the 33 years shared with the pilot were ignored.
- **M3:** unfrozen fetch evidence.
- **M4:** undisclosed post-fire map updates.
- **Minor issues.**

**v1.1**, frozen 2026-10-21 00:55:41 EDT (`efd026fd…`). It fixed those findings. It also changed the decision interval to t(0.975, G−1) × max(two-way SE, year SE), after a calibration with 20 km block-correlated errors showed the pilot's interval over-calls. Its audit confirmed the fixes and found:
- **Critical:** that calibration held only if spatial correlation stops at the 20 km block edges. The pilot's residuals stay correlated across block boundaries. Under such errors the v1.1 rule over-calls at 6–8%.
- **Moderate:**
  - the pilot's multiplicity was misdescribed (§1);
  - S10 missed part of the MTBS exposure;
  - the frozen evidence was a curated subset;
  - v1.0's text was not shipped;
  - an intermediate decision rule and the exploratory calibration run were not disclosed.
- **Minor issues.**

**v1.2**, frozen 2026-10-21 02:30:45 EDT (`d19237dd…`). It fixed those findings with a critical value C2 = 2.31, calibrated under four spatial error models fitted to the pilot's residuals. Its audit found:
- **Critical:** the fitted range of the pilot's residual correlation (11 km) is biased low, and the pilot cannot reject much longer ranges. Under fields with ranges of 22–45 km, the v1.2 rule over-calls at 6.7–9.3%.
- **Minor:**
  - the §0 table misdated v1.1's validation tolerance and misdescribed it (corrected below);
  - the fresh-seed scatter of the calibration was understated (corrected in §2);
  - the transcript extract skipped the final pre-freeze command (§3);
  - `run_test.py`'s input check could be bypassed (fixed: explicit exits, the running file is hashed, `FREEZE.json` is checked against the publicly verified copy, and results record whether verification ran).

**v1.3**, frozen 2026-10-21 05:15:30 EDT (`6ea1d0b8…`). It fixed those findings and changed the primary model:
- **Screened family.** C2 was calibrated over the models of a screened family that the pilot's residuals cannot reject, found by indirect inference on grids of 140 exponential fields and 9 block models, rather than over plug-in fits (§2).
- **Primary model M2R: the pilot's M2 plus fixed effects for 40 km regions.** The pilot cannot exclude residual correlation at long ranges. Under such fields the pilot's model M2 needs a far larger critical value (now 3.93), and its power at β₃₃ falls to 0.16 even with independent errors. Regional fixed effects absorb most of that long-range structure, while the identifying variation barely changes: the SD of log₁₀ A_enc given the other terms goes from 0.711 to 0.701.
  - The decision record (`history_v1.3_dev/DECISION_primary_model_M2R.md`) was written before the pilot's estimate under M2R was computed. The fourth audit confirmed the order from the file times and the command record.
  - The pilot's own model stays in the plan as S13, with its own critical value.

Its audit found no critical issue, and found:
- **Moderate:**
  - C2 = 2.37 had no margin. North–south elongated anisotropic fields and compartment-level clustering, both outside the family, over-called at about 5.4–5.9%. The plan's statement about fields beyond 180 km compared values from different grids and was wrong.
  - S13's critical value under-covered exact long-range fields (about 6% false calls), and S13 is exposed to differences between reporting agencies.
- **Minor:**
  - the command record still filtered commands by name, and its coverage was misstated;
  - the screen's 200 replicates make boundary decisions depend on the seed;
  - several statements overstated what was covered;
  - small code points.

**v1.4 fixes them, without changing the model or the statistic.**
- **Stress set.** 90 candidate structures outside the screened family were fixed in a decision record before any of them was simulated (`history_v1.4_dev/DECISION_stress_set.md`): anisotropic fields, exact long-range fields to 720 km, and compartment random effects. 52 pass the pilot screen. The final critical values are the maxima over both sets: C2 = 2.53, C1 = 2.08, C2_M2 = 3.93 (§2).
- **The command record** has no name filter after the v1.2 extract, and its coverage is stated exactly (§3).
- **Wording and code:**
  - the plan now says what each set covers and what it does not;
  - `run_test.py` verifies the very critical-value file it loaded, and refuses cleanly when the fetch record is missing.

**How the decision rule evolved, in full.** All of this happened before any outcome from this region existed:

| When (2026-10-21 ET) | Rule | What prompted it |
|---|---|---|
| v1.0 | M2; β ± 1.96 × SE_year (the pilot's rule) | — |
| about 00:36 | M2; β ± 1.96 × max(SE₂, SE_year) | 1,000-replicate block-correlated calibration of the pilot's rule (11.7% false calls) |
| 00:41:55 | M2; t(0.975, 32) × max(SE₂, SE_year). In the same command, v1.1's validation tolerance of 0.065 | An exploratory 4,000-replicate run (`history_v1.1_dev/exploratory_bigcal.py`, seeds 30000+ and 40000+). 1.96 × max gave 5.75% iid and 6.4% block-correlated; t × max gave 4.65% and 5.6%. The code records the tolerance as "nominal 0.05 plus 1.5 points"; it lies above all four figures. |
| v1.2 | M2; C2 × max(SE₂, SE_year), C2 = 2.31 | the second audit's continuous-field finding |
| v1.3 | **M2R**; C2 × max(SE₂, SE_year), C2 = 2.37 | the third audit's range-bias finding, and the development runs below |
| v1.4 | M2R; C2 × max(SE₂, SE_year), C2 = 2.53 | the fourth audit's anisotropy and compartment findings: the stress set |

Up to v1.2, every change widened the interval on every dataset. v1.3 changed the model, so its interval is not nested in v1.2's. M2R was chosen on simulated nulls, for robustness and power, before the pilot's M2R estimate was computed and before any outcome from this region existed. v1.4 changes only the critical values, which can only rise, so its interval contains v1.3's on every dataset. The cost of the wider intervals, that NOT REPLICATED is harder to reach, is in §2.

**Development runs for v1.3** (`history_v1.3_dev/`; simulated nulls on the blind design, no outcome):
- `calibrate_v13_firstrun_T2_stopped.log`: the first v1.3 calibration, with v1.2's statistic. It was stopped after 12 models, once the retained set was seen to reach the grid's edge.
- `exploratory_multiscale.py`: adding a 40 km SE to the max barely reduces M2's sensitivity to long-range fields.
- `exploratory_regional_fe.py`: 40 km regional fixed effects remove most of it.
- `exploratory_long_range.py`: after the registered calibration, fields beyond 180 km on a 1,024 km periodic grid. The fourth audit showed that the comparison v1.3 drew from it was wrong; v1.4's stress set uses exact fields instead.
- `calibrate_v13_secondrun_stopped.log`: the second v1.3 calibration, with M2R. It was stopped after 32 models, because the plug-in block model used a single block share; a quick check (`exploratory_block_share.py`) showed the pilot cannot reject block shares of 0.045–0.13. The registered run screens block shares like fields, and extends the field grid to share 0.60.
- `exploratory_Q.py` was written and deleted before it was ever run; it is in the command record.

**Development for v1.4** (`history_v1.4_dev/`): the decision record that fixed the stress set before it was simulated. Before the registered run, the stress code was smoke-tested on one anisotropic model (200 replicates); nothing was tuned on it.

## 1. What is being replicated

**The pilot:**
- **Region and data:** Okanogan, Methow and Chelan, Washington; FPA FOD 1992–2024.
- **Freeze:** the plan was frozen at 20:13 ET on 2026-10-20, before any fire size was fetched.
- **The decisive test, H2:** compartment size predicts final fire size beyond barrier density and road distance.
- **The registered rule:** a 95% CI for each of two definitions, either one counting. The pilot's write-up later added a Bonferroni check at 0.025. That check was not registered and is post hoc.

| Pilot definition | β, log₁₀ size per log₁₀ compartment area (95% CI) | n | Verdict (registered rule) |
|---|---|---|---|
| B, mapped barriers | **0.063 (0.010, 0.117)**; cluster bootstrap (0.012, 0.120); p = 0.021 | 2,677 | SUPPORTED |
| A50, DNR control-location map (PCL > 0.5) | 0.169 (−0.012, 0.350) | 194 | not supported (underpowered) |

In words: a compartment ten times larger went with fires about 16% larger.

**The pilot re-read under this plan's approach.** This is exploratory, recorded as pilot Deviations 2 and 3 (`p1/DEVIATION_2.json`, `p1/DEVIATION_3.json`).
- **Under M2R:** the pilot's estimate is β = 0.079 (two-way SE 0.025, year SE 0.027), so T = β / max(SE₂, SE_year) = 2.98.
- **Under its own model M2:** T = 2.31.

Simulated on the pilot's own design (`pilot_reread.py` → `PILOT_REREAD.json`, 5,000 replicates each), under the reference models, the boundary of the screened family (§2: for each range, the field with the largest retained share, and the block model with the largest retained share), and every retained stress model:

| Error model | M2R: p, two-sided | M2R: 5% critical value | M2R: 2.5% critical value | M2: p, two-sided | M2: 5% critical value | M2: 2.5% critical value |
|---|---|---|---|---|---|---|
| iid (reference) | 0.005 | 1.94 | 2.28 | 0.023 | 1.91 | 2.26 |
| 20 km blocks (pilot plug-in) | 0.007 | 2.12 | 2.45 | 0.030 | 2.10 | 2.39 |
| blocks + exponential field | 0.008 | 2.10 | 2.44 | 0.031 | 2.06 | 2.42 |
| 20 km blocks, share 0.11 | 0.009 | 2.24 | 2.62 | 0.034 | 2.13 | 2.46 |
| field, share 0.09, range 11 km | 0.008 | 2.16 | 2.46 | 0.036 | 2.16 | 2.47 |
| field, share 0.11, range 16 km | 0.012 | 2.23 | 2.58 | 0.036 | 2.15 | 2.52 |
| field, share 0.13, range 22 km | 0.012 | 2.31 | 2.59 | 0.041 | 2.20 | 2.53 |
| field, share 0.13, range 30 km | 0.013 | 2.29 | 2.64 | 0.040 | 2.20 | 2.52 |
| field, share 0.2, range 45 km | 0.014 | 2.30 | 2.67 | 0.030 | 2.08 | 2.40 |
| field, share 0.2, range 60 km | 0.009 | 2.24 | 2.55 | 0.028 | 2.06 | 2.39 |
| field, share 0.3, range 90 km | 0.009 | 2.23 | 2.60 | 0.030 | 2.07 | 2.38 |
| field, share 0.3, range 120 km | 0.011 | 2.14 | 2.54 | 0.025 | 1.97 | 2.32 |
| field, share 0.4, range 180 km | 0.012 | 2.26 | 2.58 | 0.026 | 2.02 | 2.32 |

Across the 52 retained stress models on the pilot's design, the largest 5% critical value is 2.72 under M2R (compartment effects, share 0.12; at 2.5%, 3.12 at most) and 2.69 under M2 (compartment effects, share 0.12). The largest two-sided p of the pilot's T is 0.033 under M2R and 0.087 under M2.

**So the pilot's evidence is moderate, and it is stronger within regions.** Under the most conservative of these models, compartment effects at the largest share the pilot allows:
- **Under M2R, this plan's primary model:** its B result is SUPPORTED (T = 2.98 against 2.72) at 5%, and NOT SUPPORTED (T = 2.98 against 3.12) at the post hoc Bonferroni level of 2.5%.
- **Under its own model M2:** it is NOT SUPPORTED (T = 2.31 against 2.69) at 5%, and NOT SUPPORTED (T = 2.31 against 3.11) at 2.5%.

The registered pilot verdict stands as registered. This re-read is about how much weight it can bear. It is not a substitute for a test on new data.

**What was known when this plan was written.** The pilot's outcomes were known. They fix the hypothesis, the barrier definition and the model family. The pilot's M2R estimate was computed after M2R had been chosen. No outcome from this region is known.

## 2. The single confirmatory test

**H2, definition B, model M2R:** β(log₁₀ A_enc) > 0.

**Model M2R** is the pilot's M2 plus fixed effects for 40 km regions. The regions are the cells of a 40 km grid in EPSG:5070 (x // 40,000 m, y // 40,000 m), each the 2 × 2 parent of the 20 km clustering blocks. Usable B ignitions fall in 24 regions. The size was fixed beforehand as twice the clustering block, and no other size was tried.

**Decision rule.** The interval is β ± C2 × max(SE₂, SE_year), with C2 = **2.53**, where:
- **SE₂** is the CR1 standard error two-way clustered by year and 20 km block (Cameron, Gelbach & Miller 2011);
- **SE_year** is the pilot's year-clustered CR1 standard error.

The verdicts:
- **SUPPORTED** if the interval lies entirely above 0.
- **CONTRADICTED** if it lies entirely below 0.
- **NOT SUPPORTED** otherwise.
- **NOT ESTIMABLE** if n ≤ k or fewer than 2 year clusters.

This is one test, so there is no multiplicity adjustment. Two other readings are reported but do not decide: the pilot's rule (1.96 × SE_year) and v1.1's rule (t(0.975, 32) × max SE).

**How C2 was set:** first over a screened family (`calibrate_critical.py` → `CALIBRATION.json`), then over a stress set of structures outside it (`calibrate_stress.py` → `CRITICAL_VALUES.json`, which holds the final values).
- **The pilot's residual correlation:** correlation 0.080 at about 1 km, about 0.030 at 3–10 km, about 0.010 at 12–30 km and near 0 beyond 40 km. An exponential fitted to it gives a correlated share of 0.053 with range 11.2 km.
- **Why a plug-in fit is not enough:** fitted to regression residuals, the correlogram's range is biased low, so the plug-in fit (share 0.053, range 11.2 km) cannot be taken as the true model.
- **Which error models are credible.** The candidates are persistent exponential fields, with correlated share s and range r, plus independent noise. The grid has 14 shares (0.03, 0.045, 0.06, 0.075, 0.09, 0.11, 0.13, 0.16, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6) × 10 ranges (6, 11, 16, 22, 30, 45, 60, 90, 120, 180 km).
  - Each was simulated 200 times on the pilot's design, residualized on the pilot's B/M2 design, and its correlogram refitted exactly as for the real residuals.
  - A model is **retained** if the pilot's observed fitted share and range both lie inside the central 95% of its simulated fits.
  - The screen uses the pilot's M2 residuals, as v1.2 did. It asks which error processes could have produced them, whatever model is then fitted here.
  - 73 of the 140 models are retained (table below). In share, the retained set is closed within the grid: at every range, the shares above the largest retained one are rejected, and at 6 km no share was retained with the registered seeds (the fourth audit found the smallest share there retained about 4 times in 10; such a field is mild and cannot set C2). In range, the grid stops at 180 km; the stress set continues to 720 km.
  - 20 km block effects are screened the same way, against the pilot's ANOVA block share (0.062), over block shares 0.03, 0.045, 0.06, 0.075, 0.09, 0.11, 0.13, 0.16, 0.2. Shares 0.045, 0.06, 0.075, 0.09, 0.11 are retained; under them the 95th percentile of \|T\| under M2R is at most 2.26.
- **Simulating the test:** 4,000 null outcomes were simulated on this region's blind design under each retained field and block model, under the pilot's plug-in block effects (one-way ANOVA on its residuals), and under blocks plus a field (fitted jointly to cross-year pairs).
  - Over this family, the largest 95th percentile of |T| = |β| / max(SE₂, SE_year), rounded up to two decimals, is 2.37, set by the field with share 0.4 and range 180 km; at the 90th percentile it is 1.95.
- **The stress set (v1.4).** These are structures outside the screened family, fixed before any of them was simulated (`history_v1.4_dev/DECISION_stress_set.md`):
  - **S-A:** anisotropic exponential fields, elongated north–south or east–west, with (short, long) ranges of (10, 60), (10, 120), (15, 90) and (20, 180) km, and shares 0.08–0.25;
  - **S-L:** long-range isotropic fields with ranges of 180–720 km, shares 0.3–0.9;
  - **S-C:** compartment random effects, one per definition-B compartment, shares 0.02–0.15.
  - **Screens.** The fields are exact (Cholesky factors at the actual points), so long ranges are not distorted by a periodic grid. Screens run on the pilot's design with 1,000 replicates: the registered correlogram statistic for fields, and the ANOVA share between compartments (0.080 in the pilot's M2 residuals) for compartment effects. No directional screen is applied, so east–west fields are kept whenever the registered statistic keeps them.
  - 52 of the 90 candidates are retained (S-A 32, S-L 16, S-C 4). Each was simulated 4,000 times on this region's blind design.
- **Final values.** C2 is the larger of the two sets' values: **2.53**, set by the stress model "anisotropic field, north–south, share 0.2, ranges 20 × 180 km". C1 = **2.08**, set by the stress model "anisotropic field, east–west, share 0.15, ranges 10 × 120 km".
- **Checking** (`validate_synthetic.py`):
  - `CALIBRATION.json` was produced by the v1.3 code (frozen in `history_v1.3/`); the v1.4 code reproduces three of its models bit for bit, including the binding one (`check_calibration_repro.py` → `CALIBRATION_REPRO.json`);
  - the fast simulation path equals `run_test.py` to within 3e-14;
  - the rule was re-run on fresh seeds: 10,000 replicates under each binding model, 1,000 under every other model of the screened family and 500 under every other stress model, all within their limits (5% plus 3.5 Monte Carlo SE).
  - Monte Carlo error is about ±0.35 points (1 SE) at 4,000 replicates, and earlier runs moved by up to 0.9 points between seed sets, so shares near 5% are read with that in mind.

95th percentile of |T| under M2R, by retained model of the screened family ("—" marks a model the pilot rejects):

| Share | 6 km | 11 km | 16 km | 22 km | 30 km | 45 km | 60 km | 90 km | 120 km | 180 km |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.03 | — | 2.08 | 2.06 | 2.05 | 2.05 | — | 2.04 | — | — | 2.00 |
| 0.045 | — | 2.03 | 2.12 | 2.05 | 2.03 | 2.06 | 2.04 | — | 2.05 | 2.00 |
| 0.06 | — | 2.15 | 2.18 | 2.21 | 2.06 | 2.04 | 2.08 | 2.03 | 2.02 | 2.05 |
| 0.075 | — | 2.17 | 2.20 | 2.14 | 2.12 | 2.06 | 2.10 | 2.06 | 2.05 | 1.96 |
| 0.09 | — | 2.23 | 2.22 | 2.23 | 2.12 | 2.21 | 2.13 | 2.05 | 2.14 | 2.01 |
| 0.11 | — | — | 2.20 | 2.24 | 2.23 | 2.14 | 2.10 | 2.10 | 2.08 | 2.09 |
| 0.13 | — | — | — | 2.25 | 2.22 | 2.18 | 2.22 | 2.19 | 2.09 | 2.07 |
| 0.16 | — | — | — | — | — | 2.21 | 2.23 | 2.13 | 2.14 | 2.13 |
| 0.2 | — | — | — | — | — | 2.27 | 2.19 | 2.20 | 2.22 | 2.18 |
| 0.25 | — | — | — | — | — | — | — | 2.28 | 2.26 | 2.19 |
| 0.3 | — | — | — | — | — | — | — | 2.26 | 2.26 | 2.23 |
| 0.4 | — | — | — | — | — | — | — | — | — | **2.37** |
| 0.5 | — | — | — | — | — | — | — | — | — | — |
| 0.6 | — | — | — | — | — | — | — | — | — | — |

Isolated rejections among the smallest shares reflect Monte Carlo noise in the 200-replicate screen; those models are milder than their retained neighbours and cannot set C2. Taking the maximum over many models, each with Monte Carlo error, errs on the conservative side.

The reference models, and the screened family's binding model:

| Error model | Parameters | 95th pct of \|T\|, M2R | False calls: pilot's rule | v1.1 rule | **this rule** (fresh seeds) |
|---|---|---|---|---|---|
| iid (reference) | — | 2.039 | 6.9% | 5.1% | **1.9%** (1,000 replicates) |
| 20 km blocks (pilot plug-in) | block share 0.062 | 2.173 | 10.0% | 6.6% | **1.7%** (1,000 replicates) |
| blocks + exponential field | block share 0.028; field share 0.021, range 15.3 km | 2.091 | 8.1% | 5.5% | **2.3%** (1,000 replicates) |
| field, share 0.4, range 180 km (binding in the screened family for C2 and C1) | field share 0.400, range 180.0 km | 2.369 | 13.0% | 8.6% | **4.0%** (1,000 replicates) |

The stress models with the largest 95th percentiles under M2R:

| Stress model | 95th pct of \|T\|, M2R | 95th pct of \|T\|, M2 | False calls at C2 = 2.53: calibration / fresh seeds |
|---|---|---|---|
| anisotropic field, north–south, share 0.2, ranges 20 × 180 km (binding) | 2.528 | 2.525 | 5.0% / 4.3% (10,000 fresh) |
| compartment effects, share 0.12 | 2.471 | 2.543 | 4.6% / 5.6% (500 fresh) |
| compartment effects, share 0.1 | 2.456 | 2.555 | 4.5% / 5.8% (500 fresh) |
| anisotropic field, east–west, share 0.15, ranges 10 × 120 km | 2.426 | 3.119 | 4.1% / 4.6% (500 fresh) |
| anisotropic field, east–west, share 0.2, ranges 20 × 180 km | 2.419 | 3.466 | 4.1% / 3.4% (500 fresh) |
| anisotropic field, north–south, share 0.15, ranges 10 × 120 km | 2.417 | 2.486 | 4.0% / 3.8% (500 fresh) |
| compartment effects, share 0.08 | 2.411 | 2.476 | 3.9% / 2.8% (500 fresh) |
| anisotropic field, north–south, share 0.15, ranges 15 × 90 km | 2.390 | 2.596 | 3.9% / 3.4% (500 fresh) |

**What the critical values cover, and what they do not.**
- **Covered:** the screened family (isotropic exponential fields to 180 km, 20 km block effects, and one fitted combination of the two) and the stress set (anisotropic fields, exact isotropic fields to 720 km, and compartment effects), at every share the pilot cannot reject.
- **Limits of the screens** (fourth audit): a box of two marginal 95% intervals; separate statistics for fields, blocks and compartments; and, in the screened family, 200 replicates per model.
- **Not covered:** structures outside both sets, for example correlation that changes from year to year, several structures combined at their limits, or shapes other than exponential. These remain a residual risk.
- The models were fitted to the pilot and not to this region, whose outcomes are unknown.

**Pre-specified reading.** These readings never change the decision.

| Reading | Condition |
|---|---|
| **REPLICATED** | SUPPORTED |
| **NOT REPLICATED** | NOT SUPPORTED, and the one-sided bound β + C1 × max(SE₂, SE_year), with C1 = **2.08**, is below β₃₃ = 0.0415 |
| **INCONCLUSIVE** | NOT SUPPORTED, otherwise |
| **CONTRADICTED** | CONTRADICTED |

**β₃₃** is the effect the pilot had 33% power to detect with its own registered rule: the small-telescopes benchmark (Simonsohn 2015, *Psychological Science* 26:559–569). The wider intervals make NOT REPLICATED harder to reach than under the pilot's rule. For a true null effect, simulated on this design: iid (reference): 0.76 under this plan's reading against 0.86 under the pilot's rule; 20 km blocks (pilot plug-in): 0.71 under this plan's reading against 0.82 under the pilot's rule; blocks + exponential field: 0.72 under this plan's reading against 0.83 under the pilot's rule; anisotropic field, north–south, share 0.2, ranges 20 × 180 km: 0.68 under this plan's reading against 0.75 under the pilot's rule; anisotropic field, east–west, share 0.15, ranges 10 × 120 km: 0.63 under this plan's reading against 0.74 under the pilot's rule.

**Also reported (descriptive):** the difference from the pilot and the pooled estimate, both under M2R.
- **From a stacked model:** both samples in one block-diagonal regression, clustered across both regions by year and two-way.
- **Under independence:** for reference, against the pilot's M2R estimate in §1.

**Retrieval rules, registered.** Every requested fod_id must come back exactly once. Each record's fire_year, discovery_date, latitude and longitude must equal the frozen blind record. Otherwise outcomes.csv is not written, and the failure is resolved as a numbered deviation before any analysis. `run_test.py` refuses to run unless its inputs match `FREEZE.json` and outcomes.csv matches the hash recorded at fetch time.

## 3. Region, data and sample

**Region**
- **Analysis box:** lon −119.4 to −117.0, lat 47.75 to 49.0. It covers eastern Okanogan, Ferry, Stevens and Pend Oreille counties, the northern edges of Lincoln and Spokane counties, and a strip about 3 km wide of the Idaho panhandle at the east edge.
- **Compute box:** the analysis box plus 15 km, 7,885 × 6,849 cells at 30 m in EPSG:5070 (`p1_config.json`).
- **Why this region:** it adjoins the pilot to the east and has similar fuels and fire regimes. It was fixed before any data from it were fetched. It was also expected to be covered by the DNR PCL raster, but §5 shows large gaps.

**Data.** The sources are the pilot's.
- **Ignitions:** FPA FOD 7th edition (FPA_FOD_20260615; 1992–2024), USFS EDW `EDW_FireOccurrenceCurrentEdition_01`, layer 0. Only the allow-listed fields are requested: id, year, discovery date and day, cause, location, owner and agency.
- **Roads:** TIGER, vehicle MTFCC classes only.
- **Water:** NHD large-scale Area (FTYPE 460, 431) and Waterbody (390, 436, 378). The waterbodies were requested by FTYPE because the USGS server timed out on the full layer. The features used are the same.
- **Fuels:** LANDFIRE LF2024 FBFM40; non-burnable 91, 92, 93, 98, 99.
- **Control locations:** Washington DNR PCL raster.
- **Burn scars:** MTBS perimeters, geometry only, for B+.
- **Weather:** gridMET ERC-G as a per-cell percentile over 1992–2024.

**The record of the work.** `FETCH_PROVENANCE.md` records which code version fetched each input. The command record has two parts:
- **`logs/transcript_tool_calls_p1c.jsonl`,** frozen with v1.2 and unchanged. It holds the commands and code edits from 20:33 to 02:09:27 ET whose text names a P1C file or script; the name filter is in `extract_transcript.py`.
  - Read-only monitors, and runs that named no P1C file, are not in it.
  - v1.2's extractor also skipped any command that mentioned the extractor.
- **`logs/transcript_tool_calls_p1c_part2.jsonl`,** with no name filter:
  - every call from 02:09:28 to 02:31:57 ET, recovered from the third audit's printout of the session transcript (`logs/transcript_view_by_third_audit_0232ET.txt`), with each command's length checked;
  - every call from 02:51 ET onward, from the session transcript. Only a bare invocation of the extractor is skipped.
  - Two personal identifiers that occur in a few commands, only as tokens of a privacy filter, are replaced by "[redacted]". The extractor matches them by hash and flags each affected row.
- **A gap, 02:32 to 02:51 ET.** The session transcript was compacted at about 02:51 ET, and the commands in between cannot be recovered. In that window:
  - v1.2 was archived to `history_v1.2/`, with two logs of the third audit added to it at 02:49 (frozen from v1.4 on);
  - `simcal.py`, `run_test.py` and `calibrate_critical.py` were edited;
  - the first v1.3 calibration was launched, at about 02:51 (its log is in `history_v1.3_dev/`).

  The v1.2 and later versions of the edited files are all in this package, so every change is visible as a diff. No outcome was requested then or at any other time.

**Sample.** The sample is every FPA FOD record inside the closed lon/lat box above, judged by its own coordinates: 14,105 records. Any record also in the pilot table is removed by fod_id. No record needed removing: the two boxes meet only along the meridian at −119.4, and no record lies on it in both. The check runs anyway, in the build and in every guard. That leaves 14,105 ignitions:

| Cause | Ignitions |
|---|---|
| Natural | 4,779 |
| Human | 9,080 |
| Missing | 246 |

ERC is available for 100.0% of them.

**Possible cross-boundary duplicates.** 5 ignitions here have a pilot ignition on the same discovery date within 5 km (`EXPOSURE_LISTS.json`). If any is a duplicate report of the same fire, the pilot's outcomes would reveal its size. S12 drops them. Two more pairs lie within 5 km but a day apart; they fall outside the rule and are kept.

**Blindness, checked before the freeze** (`check_predictors.py`, all PASS):
- **P1:** no outcome field in the predictor table or the raw ignition records.
- **P2:** diagonal lines split 4-connected fuel.
- **P3:** edge-touching compartments are censored.
- **P4:** every layer is on the compute grid.
- **P5:** no pilot ignition is present, and the exclusion list is the frozen pilot table (sha256 `57118595…`).
- **P6:** the table equals the raw records inside the lon/lat box minus the pilot records.

**Known limits of blindness, disclosed:**
- **MTBS during the pilot.** The pilot fetched MTBS perimeters at 19:53 and 20:06, before this region was chosen at about 20:33. It requested all attributes, which include burned acreage, over the pilot's compute box. 63 of those 275 perimeters (61 from 1992–2024) reach into this region. The pilot code kept only geometry and year, and no attribute value was stored, printed or looked at.
  - **S10** drops the 1,697 ignitions inside the pilot's compute box.
  - **S10b** also drops those inside, or within 1 km of, any of the 63 perimeters: 1,888 ignitions, 703 of them outside the pilot box, so 2,400 dropped in all.
  - This region's own MTBS fetch requested geometry only (`fields='OBJECTID'`). The evidence is the command log `logs/tasks/bdqn7r65m.output` and the transcript record of that command.
- **MTBS geometry.** The perimeter polygons on disk encode the burned area of every large fire (≥ 1,000 acres). They were used only as barriers in B+, and never linked to ignitions or measured for that purpose. Beyond the count per year, the only computations on them were the 63/61 intersection counts and the S10b zone above.
- **The PCL raster.** It is a model product that may have been trained on fire perimeters that include this region. That is one reason A50 and A25 are secondary here. The other is power.
- **Post-fire map updates.** The maps are from 2024 and are applied to 1992–2024 fires.
  - **Fuels:** LANDFIRE updates fuels after disturbances, so for recent large fires the fuel group at the ignition cell partly reflects that fire's own aftermath. S11 drops the fuel-group term.
  - **Roads:** roads built after a fire, such as salvage roads, would make compartments around large past fires smaller. That works against the hypothesis.

## 4. Models and code

**Outcome:** Y = log₁₀(fire_size, acres).

**Models:**
- **M1:** Y ~ log₁₀ A_enc + ERC_pct + fuel group + cause + month + year (fixed effects).
- **M2:** M1 + log₁₀(ρ + 0.001) + log₁₀(road distance + 30 m).
- **M2R (the confirmatory primary):** M2 + 40 km region (fixed effects). M1 and M2 are exactly as in the pilot.

**Estimation.** OLS. The decision interval is defined in §2. The year-clustered CR1 interval and a 2,000-replicate cluster bootstrap by year are reported alongside.

**Sample rules.** Records need fire_size > 0, ERC and month. Ignitions on holdable cells and censored compartments are excluded, per definition.

**Definitions:**
- **B (primary):** roads, water and non-burnable ground.
- **A50:** PCL > 0.5. **A25:** PCL > 0.25.
- **B+:** B plus MTBS scars from the 10 prior years.

All are exactly as in the pilot.

**Code identity, verified before the freeze** (`equivalence.py` → `EQUIVALENCE.json`):
- **`build_predictors.py`:** rebuilt the frozen pilot predictor table byte-for-byte (sha256 `57118595…`).
- **`run_test.py`:** replaying the pilot's call sequence with it reproduces all 233 numbers in the pilot's 23 reported outputs exactly. Its changes from the pilot code are listed in its header; M2R and S13 are additions, and the pilot's functions with default arguments are untouched.

**Synthetic validation,** in a scratch directory with no real outcome present (`SYNTHETIC_VALIDATION.json`):
- **Planted effect:** β = 0.30 on B was recovered as 0.288 (interval 0.257–0.319) and called SUPPORTED.
- **One null draw** (seed 202) was recovered as −0.036 (interval −0.076 to 0.004) and called NOT SUPPORTED. One draw cannot measure an error rate; the calibration can.
- **Exactness and null check:** as in §2.
- **Pass criterion:** the planted effect is SUPPORTED; the fast path is exact for M2R and M2; and every fresh-seed false-call share, for this rule and for S13's, is within 5% plus 3.5 Monte Carlo SE (0.058 at 10,000 replicates, 0.074 at 1,000, 0.084 at 500). It passed.

## 5. Blind sample sizes and power

| Definition | Usable ignitions | Compartment area, log₁₀ acres (10th / 50th / 90th percentile) |
|---|---|---|
| B, mapped barriers (primary) | 11,314 | 2.41 / 3.63 / 4.46 |
| A50, PCL > 0.5 | 102 | −0.33 / 1.51 / 4.94 |
| A25, PCL > 0.25 | 712 | 1.00 / 3.26 / 4.40 |
| B+, B plus prior scars | 11,105 | 2.39 / 3.59 / 4.43 |

"Usable" counts records that pass every predictor-based rule. The one outcome-based rule, fire_size > 0, removed no record in the pilot.

S10 keeps 9,941 usable B ignitions. S10b keeps 9,368.

The DNR PCL raster has no-data gaps across much of this region, so almost every A50 and A25 compartment touches no-data and is censored. Those two definitions are reported, but they carry little information here. Definition B does not depend on PCL.

**Power of the registered rule.** This is P(SUPPORTED) under M2R, simulated on this region's blind design with 4,000 replicates per cell (`BLIND_DESIGN.json`).

| Error model | β = 0.079 (pilot, M2R) | β = 0.063 (pilot, M2) | β = 0.0415 (β₃₃) | β = 0.032 (half the pilot) |
|---|---|---|---|---|
| iid (reference) | 1.00 | 0.95 | 0.60 | 0.36 |
| 20 km blocks (pilot plug-in) | 0.99 | 0.93 | 0.56 | 0.35 |
| blocks + exponential field | 0.99 | 0.93 | 0.57 | 0.35 |
| anisotropic field, north–south, share 0.2, ranges 20 × 180 km | 0.98 | 0.90 | 0.58 | 0.38 |
| anisotropic field, east–west, share 0.15, ranges 10 × 120 km | 0.96 | 0.86 | 0.52 | 0.31 |

**For comparison, S13** (the pilot's model M2 with C2_M2 = 3.93): P(SUPPORTED) at β₃₃ is 0.16 with independent errors and 0.44 under its binding model (the stress model "exact field, share 0.7, range 720 km"); at β = 0.063 it is 0.64 and 0.73.

**For reference:**
- the analytic iid SE on this design is 0.0145 (n = 11,314);
- the residual SD of log₁₀ A_enc given the other M2R terms is 0.701 (M2: 0.711; pilot under M2: 0.813).

The pilot estimate cleared p < 0.05, so the winner's curse applies, and its value is probably inflated. The β₃₃ and half-pilot columns are the honest planning numbers.

## 6. Secondary analyses (reported in full, not confirmatory)

**As in the pilot**, with the pilot's models and rule:
- **H1:** M1 for B and A50.
- **A50 under M2**, with the bootstrap.
- **A25** under M1 and M2.
- **H3:** M2 on fires of at least 10 acres, for A50 and B.
- **H4:** among fires of at least 10 acres, the share with final size ≤ A_enc, against 10,000 permutations within year × fuel-group strata, for A50 and B.
- **Sensitivity, for A50 and B:**
  - S1: snap on-holdable ignitions;
  - S2: include censored compartments;
  - S3: drop coarse coordinates;
  - S6a: lightning, meaning NWCG cause "Natural";
  - S6b: human;
  - S8: 2010 and later.
- **S5:** B+.

**New in the confirmatory plan.** Each of these is reported with the registered interval; all but S9 and S13 use M2R.
- **S9:** the two-way clustered interval for A50 under M2, shown with C2 for reference only (C2 is calibrated for B under M2R).
- **S10:** without the pilot's compute box.
- **S10b:** also without the 63 pilot-fetched perimeters.
- **S11:** no fuel-group term.
- **S12:** without the possible duplicates.
- **S13:** the pilot's exact model M2 on this region, with its own calibrated critical value C2_M2 = 3.93.
- **Leave-one-year-out:** the primary estimate and decision with each year removed in turn. Any year whose removal changes the decision will be named.
- **Stacked model** with the pilot (§2).

## 7. Known threats

**Same as the pilot:**
- **Suppression access:** handled by road distance, density and the lightning-only analysis.
- **Anachronism and post-fire map updates:** see §3, S8 and S11.
- **Location precision:** see S3.

**New here:**
- **Spatial correlation.** It is handled by the regional fixed effects, the two-way SE and the critical values set over the screened family and the stress set (§2). Structures outside both remain a residual risk.
- **What the regional terms remove.** M2R compares compartments within 40 km regions. An effect that operated only between regions would not be detected by the primary test; S13 reports the pilot's model for that.
- **The 33 shared years.** The stacked model handles them for the comparison with the pilot. The replication's own test does not depend on them.
- **Landscape overlap with the pilot.** 208 of 11,314 usable B ignitions share a compartment with a pilot ignition. They are disjoint by ignition, but not entirely by landscape.
- **More wildland–urban interface near Spokane.** M2R's road and density controls and regional terms apply, and S6 splits by cause.
- **Reporting agencies.** Agency is not in the model, as in the pilot. The regional terms absorb differences between areas for the primary test. S13, the pilot's model without them, is exposed: the fourth audit estimates that the pilot's agency effects, applied to this region's mix of agencies, would bias M2 by about 1.7 standard errors, against 0.05 for M2R.

## 8. Freeze, timestamp and registration

**Frozen files:** everything listed in `FREEZE.json`:
- this file, its template and the README;
- all code;
- the blind predictor table and the configuration;
- every raw input and the request log. `raw/requests.log` lists only completed requests.
- every fetch, retry and chain log, and the command log of every background job that built this plan (`logs/tasks/`; the auditors' own jobs are not included);
- both parts of the command record, and the third audit's printout it draws on;
- the critical-value records (`CALIBRATION.json`, `CRITICAL_VALUES.json`, `CALIBRATION_REPRO.json`), and the pilot re-read, exposure, equivalence, design, validation and check records;
- the four audit reports;
- the pilot files this test reads or cites: its predictor table, outcomes, configuration, results, Deviations 2 and 3, MTBS perimeters and request log;
- the v1.0 to v1.3 freeze records, and the development files of v1.1, v1.3 and v1.4.

**Timestamp.** `FREEZE.json` was submitted to OpenTimestamps calendars, with Bitcoin confirmation pending at freeze. The upgraded proof will be added once it is confirmed.

**Public registration.** This folder will be published under the author's account. Zenodo is preferred: G2's GitHub check runs through the environment's HTTPS proxy, and GitHub commits can later be deleted. `fetch_outcomes.py` verifies the public copy itself before requesting any outcome. Afterwards it writes `OUTCOME_FETCH.json` and stamps it with OpenTimestamps. That record holds:
- the downloaded hashes;
- the counts;
- the service metadata;
- the outcome and log hashes.

## 9. Deviations

Any change after the freeze is reported as a numbered deviation, with its date and reason.
