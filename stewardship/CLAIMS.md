# Claim → theorem → executed test map

**Policy class:** already-admissible locally absolutely continuous D on [0,∞),
0≤D≤K, measurable H, 0≤H≤ΩD a.e., D′=αD(1−D/K)−φH a.e.
Functions in Lean are defined on R and interpreted on nonnegative time; ODE
and control claims hold a.e. there. The singleton zero has no effect on the
objective. The information-weighted optimum requires D(0)=D*, positive
α,K,φ,Ω,r, r<2α and Ω≥(α+r)/(3φ). No C1 restriction replaces AC.

All names below are in `Viridis.InformationWeightedStewardship`.
The family is built with Lean 4.28, Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`. The enforcing audit passed for
67 candidate declarations (including definitions/structure declarations, NOT
67 named theorems), using only propext, Classical.choice and Quot.sound.
Local proof development used Codex and Mathlib. No new Aristotle project ID,
external review, admission, release or Zenodo publication is claimed.

| Claim | Lean declaration / exact scope | Independent test/evidence | Status |
|---|---|---|---|
| Model and nonempty class | `Admissible`, `stationary_admissible`, `explicit_nonvacuity` | normalized and nonunit witnesses | Compiled conditional mathematics |
| Factorization and unique potential maximum | `factorization`, `potential_gap_nonneg`, `potential_gap_eq_zero_iff` | seven symbolic checks | Compiled algebra; symbolic run distinct |
| Sustainable held rate and feasible duty | `held_rate_balance`, `held_rate_at_star`, `held_rate_feasible`, `duty_feasible` | cap equality, insufficient cap, nonunit φ/K | Compiled; numerical guard interprets declared decimals exactly |
| Finite AC physical-model accounting | `discounted_primitive_derivative`, `finite_accounting` | terminal-term regression, short-horizon reversal | Compiled from ODE and AC FTC, not an assumed identity |
| Integrability and infinite bridge | `objective_integrable`, `discounted_stock_integrable`, `terminal_vanishes`, `infinite_accounting` | independent DOP853 objective and analytic tail bound | Compiled; finite numerics are separate |
| Full global comparison | `lifetime_regret`, `lifetime_optimal`, `stationary_objective`, `global_certificate` | matched forcing/raw-target/schedule values | Compiled actual lifetime integrals |
| Equality | `equality_iff_stock`, `held_stock_control`, `held_control_stock`, `equality_iff_control` | stationary equality regression | Compiled: stock equal at every nonnegative time, controls equal a.e. |
| Arbitrary initial condition | `arbitrary_initial_upper_bound` | four off-setpoint states with transitions | Compiled upper bound only; no optimal transition controller claimed |
| q=1 counterpart | `raw_finite_accounting`, `raw_infinite_accounting`, `raw_lifetime_regret`, `raw_stationary_admissible`, `raw_lifetime_optimal`, `raw_stationary_objective` | K=2,D0=.8, value 2.4 vs forcing 1.138236… | Compiled; Ω≥(α+r)/(2φ), 0<r<α |
| Fresh-bit channel q(d)=d/K | Human entropy/log-loss derivation in mathematical certificate | joint-distribution enumeration; 400,000 seeded trials; duplicate target refusal | Analytical + executed numerical; channel probability space not formalized in Lean |
| Explicit forcing solution and ≥2.2 ratio | Human differentiation and exponential bound | exact solution vs DOP853; independent quadrature | Analytical, not a Lean forcing-solution theorem |
| Approximately 2.991 ratio/crossover | No claim of exact symbolic decimal values | fresh `results.json` | Numerical observation with error estimates |
| All bounded measurable u produce invariant trajectories | Separate analytical Carathéodory/comparison argument | numerical boundary/overshoot tests | Not a Lean existence/invariance theorem; full certificate instead quantifies over already-admissible trajectories |
| φ=0 | Pointwise dominance reasoning, separate dynamics | zero-damage ablation | Analytical + numerical; excluded from positive-φ theorem |
| m=0,1,2 schedule experiments | General-m analytical candidate/maximum derivation; Lean covers m=0,1 | 128 per exponent, 384 total, 12 stages plus infinite tail | Analytical/numerical extension, not general-m Lean theorem |
| Attention price, energy bridge | Defined linear cost; assumed ε_op and power law | No physical experiment | Definition-expansion / physical hypothesis |
| Ecological validity, scientific priority, universal alignment | None | No supporting evidence | Not established |
| Supplied ZIP and original 24 tests | Missing archive/spec/code/manifest | Loose files hashed only | Unverified provenance; NOT reproduced |

The failed near-capacity regression in `independent-tests-2.log` is retained;
`independent-tests-3.log` records the correction. The synthetic q=.1 Wilson
interval misses .1 with the unchanged seed, as in the supplied loose results;
this is reported rather than reseeded. Pointwise 95% intervals are not a joint
coverage guarantee or physical evidence.

A mathematical coefficient in an analytic tail bound evaluated in floating
point is not an outward-rounded rigorous numerical enclosure. Solver tolerances
and quadrature error estimates remain numerical diagnostics.
