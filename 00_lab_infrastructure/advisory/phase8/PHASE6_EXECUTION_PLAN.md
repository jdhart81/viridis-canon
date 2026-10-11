# Phase 6 execution plan: test the raw-observation premise PL

Prepared 2026-10-11 for Justin’s decision. **Planning only: no experiment run, money spent, procurement, outreach, external registration or publication.** This is an implementation and cost plan for the existing local prospective protocol, not a replacement preregistration. It does not change any theorem, physical premise, certificate, verifier, publication gate, scheduler verification path or nightly streak.

Recommended decision: authorize the existing-equipment computational stage with **$0 incremental external spend, 20 investigator hours, 25 CPU-hours and 10 GB retained outputs**, retaining the exact preregistered design. Benchmark the complete physical model before the confirmatory freeze. If the full design cannot fit those caps, report COMPUTE_BUDGET_HOLD rather than trim cells, seeds, samples or unfavorable results. No hardware expenditure is recommended until the accounting is independently identifiable and an informative measurement is feasible.

## 1. Frozen starting protocol and what an outcome would mean

Input: `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/2026-10-04/game-plan-completion/PREREGISTRATION.md`, SHA-256 `bb1edecdb9f3bbca626e78aff5f37342a8e38d83d8c3d344dd65fdafe298b05f`. All original design and decision rules remain authoritative. This execution plan proposes concrete implementation details that must be frozen before confirmatory outcome inspection. A needed scientific design change gets a new preregistration version and a reason; this document authorizes none.

PL is the raw-observation bridge `R_obs K <= P`. PD is the useful-information bridge `rate <= R_obs D`. Run-902 proves their conditional algebraic consequence `rate <= P D/K`. Run-900 supplies a minimum-form conditional ceiling, and Run-901 supplies a mathematical positive-learning witness and an honest erasure/power transfer lemma. None proves raw-observation PL as a universal physical law, a physically realized learner, saturation, or the measured-to-formal unit bridge.

The question is whether a *fully accounted cyclic learning device* must pay Landauer-scale work for every acquired raw bit, or whether its cost can track useful retained information after reversible nuisance processing and complete restoration. Landauer’s original analysis addresses logical irreversibility; applying it to every observation requires an additional physical argument. [Landauer’s original paper](https://www.cpt.univ-mrs.fr/~verga/pdfs/Landauer-1961uq.pdf).

Measurement and erasure costs depend on the modeled memory and thermodynamic accounting. Computational copying can carry architecture-dependent accuracy and dissipation costs. Therefore, a reversible logical gate diagram alone is insufficient; all initialization, correlation, controller and reset costs must enter the modeled cycle. [Sagawa and Ueda](https://arxiv.org/abs/0809.4098), [Ouldridge, Govern and ten Wolde](https://arxiv.org/abs/1503.00909).

Predictive and nonpredictive retained information provide a mechanism comparison, not an automatic identification of Viridis’s D or rate. [Still et al.](https://arxiv.org/abs/1203.3271).

A simulation can find a **within-model PL counterexample candidate**, an obstruction, or non-identifiability. It cannot empirically validate or refute a universal physical premise. Nested min/product upper bounds are not mutually exclusive laws: a slack ceiling is consistent with both. The preregistered `H_raw` versus `H_useful` comparison concerns attainable envelopes of specified device architectures. It cannot refute the certified conditional algebra.

Printed scope throughout: **logical validity given the model, not empirical validation of its assumptions**.

## 2. Concrete implementation before any confirmatory run

Use a separate ordinary computational project and immutable dated output directory; never execute a local Lean path or modify sealed foundational objects. This experiment is separate from nightly certification and must not compete with the Comparator or its droplet resources. Limit workstation workers during scheduled checkpoints; if capacity is unavailable, pause this advisory experiment rather than the nightly engine.

The investigator first freezes `MODEL_SPEC.json` with:

- All raw, useful, scratch, controller and clock states; the source/environment state and correlations; transition graph; initial and restored distributions; reservoir temperatures; energy schedules; couplings; reset schedule; protocol timing; random seed namespaces.
- Isothermal finite-state Markov jump transition rates satisfying named local detailed balance. Work follows protocol energy changes; heat follows state transitions. Track every external positive work input separately from extracted work, so gross `P_in` is not silently replaced by net work or heat.
- Source preparation outside the device boundary **and** an enlarged end-to-end boundary, both fixed before outcomes. The acquisition register includes only bits actually observed. No favorable boundary selection after seeing results.
- Physical reset and scratch-uncompute operations for the useful-retention architecture. A proposed zero-cost operation must emerge from the physical model; it is never imposed by setting work equal to useful-bit count times K.
- The allowed factorization or sparse-state reduction and a proof/check that it preserves the joint entropy, work, heat and controller/reset flows required for the primary residuals. A naive source/raw/retained/scratch four-register 8-bit Cartesian state space already has `2^32` configurations, before controllers. Enumerating only 256 source blocks is not equivalent to solving that full device. If no valid manageable reduction exists, report NON_IDENTIFIABLE or COMPUTE_BUDGET_HOLD.
- Exact distribution propagation method, numerical integrator/tolerance where needed, trajectory sampler, information estimators, storage encoding and reconstruction policy. Preserve every confirmatory cell/seed/cycle count; changing storage is not permission to change sampling.

Deliver analytic positive controls before development tuning: exact 8-bit source entropy and useful mutual information; a detailed-balance equilibrium test; a raw-reset control approaching its specified reversible limit; restoration/no-growing-memory tests; and work/heat/energy closure. Include deliberately uncharged-controller and left-over-scratch cases that the accounting checker must reject as NON_IDENTIFIABLE.

## 3. Exact design and compute arithmetic

The preregistered positive-D design is unchanged:

| Factor | Levels |
|---|---|
| Useful target bits per 8-bit block | 1, 2, 4, 6, 8; hence D = 1/8, 1/4, 1/2, 3/4, 1 |
| Architecture | Raw-reset; useful-retention; blocked/zero-use control |
| Position stratum | Fixed known positions; predefined shuffled positions with flag/classification costs |
| Normalized power budget | `P_budget/K_bit = 1, 2, 4` useful bit/s |
| Development duration grid | 1, 2, 4, 8, 16, 32 relaxation-time units |
| Development reset-error grid | 0.001, 0.01, 0.05 |
| Confirmatory seeds | CONF-000 through CONF-029, paired source realizations |
| Cycles per confirmatory seed | 10,000 burn-in plus 100,000 measured |

Positive-D cells: `5 × 3 × 2 × 3 = 90`. The separate D=0 control gives `1 × 3 × 2 × 3 = 18` additional cells, excluded from the log-slope fit. Total base confirmatory cells: **108**, replicate runs: **3,240**, cycles: **356,400,000** (324,000,000 measured; 32,400,000 burn-in).

The preregistered grid is 18 settings per architecture/regime. Conservatively evaluating all 108 cells’ settings gives **1,944 development setting-cells**. Development seed count and cycle count are not fixed in the original protocol; the proposed pilot is three disjoint `DEV` seeds with 100 burn-in plus 1,000 measured cycles per setting, about 6.42 million cycles. This is only tuning/pilot work. It does not replace any confirmatory seed, shorten confirmatory horizons, or authorize inspecting CONF outcomes to choose a setting.

A within-model counterexample candidate must retain the registered doubled-horizon and halved-tolerance checks. In the conservative worst case where every cell requires both checks, doubling the *entire* cycle horizon adds 712.8 million cycles and the separate half-tolerance rerun adds 356.4 million, for **1.4256 billion total cycles**. The protocol does not require rerunning every noncandidate cell merely to manufacture a worst-case cost; every candidate does receive its prescribed checks. No candidate is selectively dropped because of its result or expense.

The existing confirmatory cap is 20 CPU-hours, following at most 5 development CPU-hours. To fit the base confirmatory matrix, the complete model must sustain at least **4,950 full cycles per CPU-second**; the all-cell worst-case robustness workload needs at least **19,800 cycles per CPU-second**. These are required throughputs derived from the matrix, not measured performance claims. Parallelism reduces elapsed time but does not reduce charged CPU-hours.

Before freeze, benchmark representative smallest/largest state spaces, both position strata and slowest protocol durations using DEV only. Record 100 pilot batches, the conservative slowest complete-cycle throughput, peak memory, output bytes/cycle, and 25% runtime contingency. Project total base and candidate-check workloads including exact propagation and bootstrap. If the projected cap fails, do not start a knowingly incomplete confirmatory matrix. Justin may choose a separately versioned larger compute budget; no cloud purchase or design truncation occurs automatically.

Storage also needs a real benchmark: a 32-byte per-cycle record for the base matrix is **11.40 GB**, already exceeding the original 10 GB cap before headers or robustness runs. A 24-byte encoding is 8.55 GB before overhead. Freeze a lossless compact format or reproducible trace/aggregate-receipt policy with full seed/implementation/model hashes and streaming trace hashes; retain failure traces and enough raw/aggregate evidence to reproduce every primary result. If the original retention requirement cannot fit, report the storage-budget HOLD. Never silently discard failed cells or claim an unretained full trace exists.

## 4. Observable and unit contract

Compute physical device information quantities in bits with `K_bit = k_B T ln 2`. Also retain natural-log quantities and use `I_nat = I_bit ln 2`, `r_bit = r_nat/ln 2`; the energy coefficient per nat is `k_B T`. The formal trajectory definitions and literal coefficient in the certified foundation do not independently certify this dimensional identification. A future exact bridge is portfolio item P8-11, not a conclusion of this simulation.

For each complete cycle, record raw acquired entropy, independent target/useful-source mutual information, retained predictive information, gross supplied work, bath heat, source preparation, controller/reset costs, final memory distribution and residual correlations. `D_eff` comes from the predefined acquired-input source law, never from measured `r/R_obs`. Retain available-source `D_src` separately, because informative acquisition changes the fraction in the observed sample.

Set the preregistered available bandwidth `B_avail = 16 P_budget/K_bit` and verify it from the independent input clock. At the smallest D, available useful input is twice the nominal useful-cost envelope. This is a proposed design to avoid a data ceiling; actual acquisitions, timing, selection and memory bottlenecks still need checking. No hardware “bit rate” is inserted into a nat-rate theorem without the named conversion and model bridge.

## 5. Analysis and independent accounting review

Freeze implementation, runtime and input hashes, chosen DEV settings, all exclusions and commands before CONF outcomes. Primary analyses remain exact distribution propagation where feasible and 30 independent replicate means, with 10,000 paired bootstrap resamples and 99% intervals. Cycles within a seed are not treated as independent replicates.

- Primary PL residual: `z_PL = P_in - K_bit R_obs`, plus per-cycle form. A candidate requires its upper 99% endpoint **plus** the deterministic numerical/accounting error bound to lie below zero, independently checked full-cycle accounting, doubled horizon and half tolerance.
- Secondary product residual: `z_product = r - P_in D_eff/K_bit`. A positive lower endpoint is interpretable only after units and PD are separately satisfied; otherwise diagnose the failed bridge rather than the certified algebra. Report min-leg residuals separately.
- Exploratory throughput slope uses the preregistered paired log regression and excludes D=0. A slope near 0 or 1 describes the device architecture and its bottlenecks; it is not a direct acceptance/rejection test of either inequality.
- Numerical closure remains: probability sum `1e-10`, nonnegativity `1e-12`, exact entropy discrepancy `1e-8` bit/block, first-law residual `1e-6 K_bit` per cycle or tighter, and refinement shift below `1e-4 K_bit`. Violations are retained as NUMERICAL_HOLD. Missing restoration/flows gives NON_IDENTIFIABLE. No exclusions for unfavorable outcomes.

Deliver the complete matrix and exclusions, primary interval/error tables, exact-distribution controls, bootstrap manifest, full flow ledger, candidate-check receipts, and an independent accounting review. The review checks source free energy, tapes, clock/controller costs, exported useful information and all final correlations. An uncharged external resource invalidates the stated PL application, not the Lean certificate.

## 6. Eight-working-day execution schedule and budget

Dates start only after Justin authorizes experiment execution; preparation of this plan is not that start. The original 20 investigator-hour estimate is a hard allocation in the recommended first option, with checkpoints instead of a promise that a physically complete model will fit it.

| Relative schedule | Investigator hours | CPU/output allocation | Concrete exit |
|---|---:|---|---|
| Days 1–2 | 6 | Workstation; prototype only | MODEL_SPEC, units/boundaries, state-space feasibility and analytic controls |
| Days 3–4 | 8 | ≤5 CPU-hours | Full DEV grid/pilots if feasible; runtime/storage estimate; frozen choices and hashes |
| Days 5–6 | Passive run supervision included above | ≤20 more CPU-hours; total retained outputs ≤10 GB | All 108 × 30 base runs, plus mandatory candidate checks within cap; otherwise documented HOLD |
| Days 7–8 | 6 | Within the same compute cap | Fixed analysis, independent accounting review and narrowly worded result |
| Optional feasibility review afterward | Not included; separately authorized | No equipment use or expenditure assumed | Calibrated empirical protocol and real partner/vendor quotes |

**Recommended Stage S total:** $0 incremental external spending; existing equipment only; 20 investigator hours; ≤25 CPU-hours; ≤10 GB. Labor opportunity cost is not $0: at an illustrative internal allocation of $100/hour, 20 hours represents $2,000. That rate is a planning convention, not a market quote, incurred cost or payment request. If model work exhausts the 20 hours without an identifiable protocol, report that honestly.

Possible future execution decision if the pilot fails only the compute cap: authorize a new *budget version* retaining the same scientific design and sampling, for example up to 100 existing-workstation CPU-hours and 50 GB with no external spend. This is an option for Justin, not applied here. If the model itself is incomplete, extra compute is not a remedy; revise/model-review before any CONF run. A reduced factorial or fewer seeds would be a scientific preregistration amendment, not a budget adjustment.

## 7. Physical/computational measurement: feasibility before procurement

At 300 K, NIST’s exact `k_B = 1.380649 × 10^-23 J/K` gives `K_bit ≈ 2.87098 × 10^-21 J/bit`. A million Landauer-scale bits per second corresponds to about **2.87 femtowatts**; a billion per second is **2.87 picowatts**. These are dimensional calculations, not claims about any apparatus. Commodity CPU or USB wall-power measurements do not have the apparatus boundary and dissipation resolution needed to establish per-observed-bit Landauer saturation. [NIST Boltzmann constant](https://physics.nist.gov/cgi-bin/cuu/Value?k%7Csearch_for=Boltzmann).

Existing small-system experiments infer erasure heat from calibrated microscopic dynamics, rather than reading femtowatts from an ordinary power meter. A colloidal double-well one-bit memory demonstrated its erasure protocol; that does not by itself test raw acquisition of an 8-bit learning block or account for an external feedback controller. [Bérut, Petrosyan and Ciliberto’s experimental paper](https://arxiv.org/abs/1503.06537).

| Candidate follow-up | What it can establish | Provisional resources and calendar | Decision |
|---|---|---|---|
| Existing-device computational energy screen | A conservative measured upper bound for a declared sensor/learning workload; may be inconclusive relative to PL | $0 if existing instrumentation; otherwise reserve $100–$500, 1–2 weeks, 10–20 hours | Optional applied engineering screen only; no spend now and no universal PL claim |
| Collaboration with an existing calibrated microscopic-memory apparatus | A new acquisition/useful-retention/restoration protocol if every relevant flow and controller boundary is identifiable | Planning reserve $5,000–$15,000 incremental experimental costs, 6–10 weeks, 40–80 investigator/collaborator hours; access, labor and apparatus capabilities unconfirmed | Preferred physical route after simulation and actual quotations; no outreach or booking executed |
| Build a new microscopic apparatus | Potentially resolvable small-system work/heat, but no guarantee of a fully closed learning protocol | Order-of-magnitude reserve $50,000–$150,000 and 4–9 months, excluding laboratory space/specialist staff; not a vendor quote | Do not approve as the default; obtain a proper engineering design and quotations first |

These monetary ranges are **planning allocations**, not observed prices or quotations. They are not used as evidence of feasibility and do not authorize expenditure. The existing-workstation option is the only recommended immediate execution decision. Actual physical budgets require instrument specifications, partner access, calibration costs and a signed boundary/uncertainty protocol.

A later physical experiment first measures a calibrated raw-reset positive control and independently reconstructs work/heat from the microscopic protocol. It must then implement acquisition, useful retention, scratch restoration, source exchanges and bounded controller accounting; test stationary repeated cycles; calibrate drift, measurement backaction, error and all reservoirs; and choose a sample size from a pilot uncertainty estimate. If a controller remains outside the measurable boundary, report both a narrower subsystem result and an enlarged-boundary NON_IDENTIFIABLE status. It cannot support a full-device PL violation.

Before collecting any empirical confirmatory data, prepare a separate versioned empirical preregistration specifying apparatus, calibration, measured flows, full boundary, uncertainty budget, power/sample-size calculation and falsification criterion. No simulated counterexample supplies those measurements. A robust measured violation would refute the **specified empirical application of PL**, not Run-902’s conditional theorem. An erasure benchmark or failure to find a violation cannot establish universal raw-observation PL.

## 8. Justin’s concrete decision packet

1. **Recommended: execute Stage S at $0 external spend with the original 20-hour/25-CPU-hour/10-GB caps.** Freeze MODEL_SPEC and pilot throughput/storage first; preserve the full preregistered matrix; produce a result or documented budget/model HOLD.
2. **If the pilot demonstrates budget infeasibility but complete accounting:** decide a larger existing-equipment budget in a new version while retaining the exact scientific design. No change is applied by this plan.
3. **After an informative model result:** decide whether to commission a quoted collaborative microscopic-memory feasibility protocol. Physical feasibility, spending and external registration remain unapproved by this planning deliverable.

Portfolio links: P8-01 (PL closed-cycle test), P8-02 (selection-aware PD), P8-03 (identifiability), P8-04/P8-08/P8-10 (conditional consequences), P8-09 (erasure bridge) and P8-11 (units/model identification). Successful simulation or proof records exactly which item it strengthens; it does not re-label other runs or upgrade physical assumptions automatically.

## 9. Delivery checklist and status

| Item | Current status | Required later evidence |
|---|---|---|
| Existing preregistration inspected and hash identified | DONE | Hash above; no source edits |
| Concrete unchanged factorial, compute and storage arithmetic | DONE — estimates only | DEV benchmark to establish actual feasibility |
| Model implementation / CONF runs | NOT EXECUTED | Immutable MODEL_SPEC, code/runtime inputs and terminal receipts |
| Physical measurement / spending / external registration | NOT EXECUTED | Separate explicit decision, quotations and empirical protocol |
| PL/PD empirically discharged | NOT ESTABLISHED | Identifiable calibrated empirical evidence scoped to a device/boundary |
| Comparator / issuer / verification path / streak | UNCHANGED BY THIS PLAN | Phase 8 installation’s independent before/after integrity receipt |

Every positive, negative, inconclusive, numerical-HOLD and non-identifiable outcome remains visible. The experiment should reduce uncertainty about the raw-observation premise, not manufacture another formally correct statement whose physical content was assumed at the start.
