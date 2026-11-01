# Summary of changes
## Formal Verification of Hart (2026) — Plasma-Mediated N₂ Fixation

I formalized and fully proved the paper's theorems, lemmas, corollaries, and invariants in Lean 4 with Mathlib. The project builds with **zero `sorry` statements** and only standard axioms (`propext`, `Classical.choice`, `Quot.sound`).

### File Structure

- **`RequestProject/Foundations.lean`** — Sections 0–2: Physical constants, thermodynamic foundations, and plasma chemistry
- **`RequestProject/Energy.lean`** — Sections 3–4: Photovoltaic energy conversion and ecological stoichiometry  
- **`RequestProject/Integration.lean`** — Sections 5–8: System integration, thermodynamic economics, ecological safety, and system invariants

### Verified Results (all proved, no sorry)

| Paper Statement | Lean Theorem | Result |
|---|---|---|
| **T1** (Min energy for N-fixation) | `theorem1_min_energy_lower/upper` | E_min ∈ (6.17, 6.19) MJ/kg N |
| **C1** (Thermodynamic efficiency) | `corollary1_haber_bosch/plasma`, `corollary1_plasma_at_T4_cost` | H-B: 20.6% (at 30 MJ/kg N); Plasma: 24.72% at 25 MJ/kg N, 17.66% at the 35 MJ/kg N used in T4 |
| **L1** (Solar info bound) | `lemma1_solar_info_bound` | Structural identity |
| **L3** (Quenching rate) | `lemma3_quenching_rate` | β_min = 30,000 K/s |
| **T2** (Vibrational enhancement) | `theorem2_enhancement_exponent_*` | Exponent ∈ (10.02, 10.04) |
| **T3** (Solar wing power) | `theorem3a/theorem3b` | P_gross = 9,900 W, P_plasma = 6,200 W |
| **T4** (N production rate, corrected) | `theorem4_denom`, `theorem4_rate/hourly/daily/annual_bounds`, `theorem4_energy_closure`, `theorem4_v1_erratum_factor` | 0.177 g/s, 0.638 kg/hr, 5.10 kg/day, 1,020 kg/yr (v1: 0.638 g/s, 2.30 kg/hr, 18.4 kg/day, 3,680 kg/yr) |
| **T5** (Stoichiometric bound) | `theorem5_stoichiometric_bound` | α_ag,max = 20.5 kg C/kg N |
| **T6** (Decomposition amplifier) | `theorem6_decomp_amplifier` | α_decomp = 300 kg C/kg N |
| **T7** (Annual C sequestration, corrected) | `theorem7_carbon/co2_bounds` | 35,712 kg C/yr, 130,944 kg CO₂/yr (v1: 128,563 / 471,398) |
| **T8** (Fleet scaling) | `theorem8_linearity` | Linear in fleet size |
| **T9** (Energy invested) | `theorem9_energy_GJ` | 57.024 GJ/yr |
| **T10** (Info bound) | `theorem10_info_bound_structure` | rate × k_BT ln2 ≤ P |
| **T12** (Saturation safety) | `theorem12_safe_range_*` | 10–37 kg N/ha/yr |
| **T13** (Net GHG balance) | `theorem13_*` | Penalty ≈ 4.29, net ≈ 124.0, fraction ≈ 3.3% |
| **I1–I5, I7** (Invariants) | `invariant_I*_check` | All verified |

### Erratum (unit conversion in Theorem 4) — corrected in v1.1

The v1 formalization reproduced the paper's Theorem 4 denominator
`35 × 10⁶ / 3600 = 9,722` and described the result as a "minor" inconsistency.
It is not minor. 9,722 is 35 MJ/kg N expressed in **Wh/kg**
(35 × 10⁶ J/kg ÷ 3600 J/Wh); the rate formula N_dot = P / E needs E in **J/g**
(W·s/g), which is 35 × 10⁶ J/kg ÷ 1000 g/kg = **35,000 J/g**. Using the Wh/kg
number as J/g drops a factor 3600/1000 = 3.6, so every Theorem 4 and Theorem 7
output in v1 was 3.6× too high. (The v1 text compared 3,673 with 3,680 — that
agreement is between two numbers carrying the same error.)

Corrected values (same inputs, P_plasma = 6,200 W, 8 h/day, 200 days/yr):

| Quantity | v1 (wrong) | Corrected |
|---|---|---|
| E_plasma denominator | 9,722 "W·s/g" | 35,000 J/g |
| N production rate | 0.638 g/s | 0.177 g/s |
| Hourly | 2.30 kg/hr | 0.638 kg/hr |
| Daily | 18.4 kg/day | 5.10 kg/day |
| Annual | 3,673–3,680 kg N/yr | 1,020 kg N/yr |
| Area served at 20 kg N/ha/yr | 184 ha | 51.0 ha |
| Carbon | 128,563–128,800 kg C/yr | 35,712 kg C/yr |
| CO₂ | 471,398–472,300 kg CO₂/yr | 130,944 kg CO₂/yr |

`theorem4_energy_closure` now checks the units: annual plasma energy divided by
annual N returns exactly 35 MJ/kg N.

**Status of the 35 MJ/kg N input.** It is an assumed design target (0.49 MJ/mol
N), not a measurement. It is below the 0.72 MJ/mol N theoretical minimum for
thermal plasmas and about 4–6× better than the best reproducible measurements
(≈ 1.8–2.8 MJ/mol N) reported by Rouwenhorst et al. 2021 (Energy Environ. Sci.
14, 2520, doi:10.1039/d0ee03763j, and its 2023 correction) and Tsonev et al. 2024
(Sustainable Energy Fuels 8, 2191, doi:10.1039/d3se01615c). All T4/T7 magnitudes
scale as 1/E_plasma; at 2.4 MJ/mol N (≈ 171 MJ/kg N) annual output would be
≈ 208 kg N/yr.
