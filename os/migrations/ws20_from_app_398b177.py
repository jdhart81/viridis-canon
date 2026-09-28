"""WS-20 one-time migration: author the 18 decision-kernel manifests and the
``os/`` governance files from viridis-conservation-app@398b177.

Kept in the repository as provenance: it documents exactly which app records
each manifest field was taken from.  After WS-20 the repository is the source
of truth and this script is not run again (running it twice is idempotent).

Usage (from the canon root)::

    python3 os/migrations/ws20_from_app_398b177.py \
        --app ../viridis-conservation-app --golden os/parity/app-398b177-published.json

Inputs taken from the app (all at commit 398b177):
  src/content/viridisOSProductState.json   modules: name, version, line, state,
                                           backing, input_schema, units, scope,
                                           warrant_verdict; research_intake
  src/content/conservationKernelMap.json   families; runtime_rule; authority
  src/content/coreKernelOS.json            operating tree, held proposals, purpose
  src/content/kernelCustomerGuide.json     plain-language summaries + input help
  src/lib/kernelFamilyLabels.ts            family labels + audience (copied below)
  src/lib/decisionKernelCatalog.ts         EXAMPLES, service-state rules
  src/lib/conservationDecisionRuntime.ts   AUTHORITY_BOUNDARY (runner code was
                                           ported by hand to each runner.py)
  src/lib/osMap.ts                         FOUNDATION_MODULES
Expected outputs come from the TypeScript runtime itself (``--golden``), so each
manifest example is the app's own published result, bit for bit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA_URL = "https://jdhart81.github.io/viridis-canon/schemas/function-v1.json"

DIRS = {
    "mutualist": "os/functions/mutualist",
    "restoration": "os/functions/restoration",
    "afforestation": "os/functions/afforestation",
    "harmonization": "os/functions/harmonization",
    "carbon-continuity": "os/functions/carbon-continuity",
    "tempo": "os/functions/tempo",
    "shared-channel-coverage": "series/SBB",
    "invariance-capacity": "series/ICC",
    "precautionary-capacity": "series/PCR",
    "reciprocity-corridor": "series/RC",
    "anytime-change": "series/ACC",
    "seed-source-bottleneck": "series/SSBC",
    "switching-hysteresis": "series/CSHC",
    "shadow-price-capacity": "P5_SLSPT",
    "multi-ring-alignment-capacity": "os/functions/multi-ring-alignment-capacity",
    "symbiotic-surplus": "os/functions/symbiotic-surplus",
    "decision-information-capacity": "os/functions/decision-information-capacity",
    "thermodynamic-economic-allocation": "series/TRWFN",
}

LEAN_SOURCES = {
    "mutualist": ["series/SymbioticRiskPremium.lean"],
    "restoration": ["series/ForestNucleation.lean"],
    "afforestation": ["series/AfforestationStewardship.lean"],
    "harmonization": ["series/GaianHarmonization.lean"],
    "carbon-continuity": ["releases/2026-08-08/Carbon_Continuity_After_Wildfire/lean/CarbonContinuity.lean"],
    "tempo": [],
    "shared-channel-coverage": ["series/SBB/PaperFormalization.lean"],
    "invariance-capacity": ["series/ICC/PaperFormalization.lean", "series/ICC/PaperFormalization/Claims.lean"],
    "precautionary-capacity": ["series/PCR/PaperFormalization.lean", "series/PCR/PaperFormalization/Targets.lean"],
    "reciprocity-corridor": ["series/RC/PaperFormalization.lean"],
    "anytime-change": [
        "series/ACC/PaperFormalization.lean",
        "series/ACC/PaperFormalization/NullMartingale.lean",
        "series/ACC/PaperFormalization/Dominance.lean",
        "series/ACC/PaperFormalization/Wald.lean",
    ],
    "seed-source-bottleneck": ["series/SSBC/PaperFormalization.lean"],
    "switching-hysteresis": ["series/CSHC/CognitiveSwitchingHysteresis.lean"],
    "shadow-price-capacity": [
        "P5_SLSPT/InverseSquare.lean",
        "P5_SLSPT/ShadowPrice.lean",
        "P5_SLSPT/ShadowPriceLevelCurves.lean",
        "P5_SLSPT/IntelligenceBound.lean",
        "P5_SLSPT/SLSPTTowerOrdering.lean",
    ],
    "multi-ring-alignment-capacity": ["MRAB.lean"],
    "symbiotic-surplus": ["SymbioticIntelligenceBound.lean"],
    "decision-information-capacity": ["P0_IntelligenceBound_COMPILED.lean"],
    "thermodynamic-economic-allocation": ["series/TRWFN/ViridisRun139.lean"],
}

THEOREMS = {
    "mutualist": ["risk_premium_tur_floor", "mutualistic_iff_covariance_negative", "diversification_wall_residual_positive", "srpt_nonvacuous"],
    "restoration": ["critical_nucleus", "barrier_half_identity", "broadcast_suboptimal", "FNT_nonvacuous"],
    "afforestation": ["establishment_efficiency_cubic_in_drive_over_tension", "site_prep_halving_sigma_eightfolds_efficiency", "homogeneous_limit_recovers_fnt", "sower_IB_ceiling", "seeding_efficiency_eq_cos2_theta"],
    "harmonization": ["ght_best_response_minimizes", "ght_market_clears", "ght_equimarginal", "ght_strong_duality_decentralized_eq_centralized", "ght_scalar_price_minimal_sufficient", "ght_harmonization_bandwidth_from_IB", "ght_bandwidth_antitone_temp", "ght_wuwei_robustness_ratio_ge_one", "ght_wuwei_robustness_strict", "ght_nonvacuous"],
    "carbon-continuity": ["carbon_continuity_threshold_sufficient", "carbon_continuity_threshold_necessary", "carbon_continuity_threshold_iff", "carbon_continuity_boundary_stationary", "carbon_continuity_strict_threshold_growth", "carbon_continuity_nonvacuous"],
    # Named on /research/recompute; no Lean source is present in this repository.
    "tempo": ["Sigma_strictConvexOn", "tempo_floor", "tempo_optimum", "tempo_unique_minimizer", "haste_neglect_cosh", "governability_tax"],
    "shared-channel-coverage": ["shared_channel_inverse", "directional_gain_bounds", "rank_deficient_unit_gain", "worstcase_deadline", "top_subspace_mean_cost", "isotropic_rank_fraction"],
    "invariance-capacity": ["mutual_information_chain_balance", "forbidden_proxy_capacity_ceiling", "forbidden_proxy_capacity_ceiling_combined", "capacity_ceiling_slack_decomposition", "perfect_invariance_target_proxy_collapse"],
    "precautionary-capacity": ["capacityFloor_violation_prob_le", "cantelli_capacity_certificate", "precautionary_rate_le_violation_budget", "capacity_reserve_fraction_eq", "positive_floor_sharp_two_point_counterexample", "mean_only_plugin_arbitrarily_unsafe"],
    "reciprocity-corridor": ["bilateral_benefit_iff_reciprocity_corridor", "ratio_interval_nonempty_iff_product_condition", "share_payoff_identities", "nash_midpoint_unique_maximizer", "bandwidth_scaling_cannot_restore_feasibility"],
    "anytime-change": ["anytime_change_mixture_martingale", "ville_inequality", "anytime_change_ville_certificate", "anytime_change_ville_certificate_sup", "change_component_dominance_and_penalty", "bounded_overshoot_expected_delay"],
    "seed-source-bottleneck": ["seed_routing_common_fraction_eq_min_cut_ratio", "seed_routing_feasible_iff_cut_conditions", "capacity_outside_active_bottleneck_irrelevant", "scenario_intersection_certificate_le_each_scenario"],
    "switching-hysteresis": ["statement", "threshold_order", "band_width_identity", "closed_loop_area_identity", "bias_translation", "directional_cost_recovery", "cshc_nonvacuous"],
    "shadow-price-capacity": ["inv_sq_strict_mono_decreasing", "shadow_price_strict_decreasing", "shadow_price_level_curve", "shadow_price_budget_tradeoff", "prefactor_ordering", "tower_ordering_trans", "cap_nonneg", "cap_strictMono_P", "cap_strictMono_D", "cap_strictAnti_C"],
    "multi-ring-alignment-capacity": ["Dbar_le_arith_mean", "mrab_bound_le_baseRate", "mrab_saturation", "mrab_reduces_to_IB"],
    "symbiotic-surplus": ["joint_bound_from_partners", "ness_reciprocity", "symbiotic_surplus_threshold", "cos_sq_extraction_bounded"],
    "decision-information-capacity": ["intelligence_bound", "data_bound_lemma_conditional", "landauer_dissipation_bound", "thermodynamic_bound_lemma"],
    "thermodynamic-economic-allocation": ["clippedAllocation_nonnegative", "clippedAllocation_le_one", "interior_stationarity", "embodied_burden_lowers_benefit", "retrofit_allocation_nonvacuous"],
}

# Tier = the app's recorded human decisions at 398b177, carried forward, never raised.
ADMITTED = {
    "restoration", "afforestation", "harmonization", "carbon-continuity",
    "shadow-price-capacity", "multi-ring-alignment-capacity", "symbiotic-surplus",
    "decision-information-capacity", "thermodynamic-economic-allocation",
}
CANON_CLASSIFICATION = {
    "shared-channel-coverage", "invariance-capacity", "precautionary-capacity",
    "reciprocity-corridor", "anytime-change", "seed-source-bottleneck", "switching-hysteresis",
}

INPUT_UNITS = {
    "mutualist": {"rho": "dimensionless correlation", "sigma": "same units as returns", "sigma_tot": "same units as returns", "r_c": "same units as returns"},
    "restoration": {"sigma": "dimensionless", "delta_mu": "dimensionless"},
    "afforestation": {"sigma": "dimensionless", "delta_mu": "dimensionless", "prep": "×", "rate": "declared seeding rate", "rate_max": "declared seeding rate"},
    "harmonization": {"marginal_costs": "cost/unit", "command_overhead": "cost", "bandwidth": "declared information rate", "ib_bound": "declared information rate"},
    "carbon-continuity": {"a": "dimensionless retention coefficient", "d": "dimensionless retention coefficient", "r": "dimensionless coupling coefficient", "p": "dimensionless coupling coefficient"},
    "tempo": {"haste_cost": "cost per cycle", "neglect_cost": "cost per cycle", "cadence": "time"},
    "shared-channel-coverage": {"dimension": "count", "rank": "count", "kappa": "dimensionless", "captured_fraction": "fraction", "baseline_cost": "cost", "dissipation_budget": "cost/time"},
    "invariance-capacity": {"conditional_task_entropy": "bits", "proxy_leakage_budget": "bits", "task_information_ceiling": "bits", "observed_task_information": "bits"},
    "precautionary-capacity": {"mean_capacity": "declared capacity units", "capacity_sd": "declared capacity units", "alpha": "probability", "power": "W", "temperature": "K"},
    "reciprocity-corridor": {"value_x": "value per unit flow", "value_y": "value per unit flow", "cost_x": "cost per unit flow", "cost_y": "cost per unit flow", "total_flow": "flow"},
    "anytime-change": {"observations": "binary (0/1)", "p0": "probability", "p1": "probability", "alpha": "probability"},
    "seed-source-bottleneck": {"demands": "seed units", "supplies": "seed units", "edges": "index pairs [supply, site]"},
    "switching-hysteresis": {"bias": "evidence", "cost_plus_to_minus": "evidence", "cost_minus_to_plus": "evidence", "current_state": "state (-1 or 1)", "evidence": "evidence"},
    "shadow-price-capacity": {"distance": "declared distance", "area": "declared area", "horizon": "declared time", "tolerance": "declared tolerance", "budget": "declared cost", "power": "declared power", "dissipation_factor": "dimensionless", "capacity_cost": "declared cost per rate", "tower_prefactors": "declared cost*tolerance^2"},
    "multi-ring-alignment-capacity": {"power": "power", "boltzmann_constant": "energy/temperature", "temperature": "temperature", "dissipation_factors": "dimensionless", "alignment_factors": "dimensionless"},
    "symbiotic-surplus": {"epsilon_landauer": "energy/information", "partner_a_power": "power", "partner_a_dissipation": "dimensionless", "partner_e_power": "power", "partner_e_dissipation": "dimensionless", "subsidy_e_to_a": "information/time", "subsidy_a_to_e": "information/time", "housekeeping_dissipation": "information/time", "observed_rate_a": "information/time", "observed_rate_e": "information/time", "inner_product": "declared geometry", "norm_a_squared": "declared geometry", "norm_e_squared": "declared geometry"},
    "decision-information-capacity": {"predictive_richness": "dimensionless", "observation_bandwidth": "information/time", "maintenance_power": "power", "temperature": "temperature", "boltzmann_constant": "energy/temperature", "landauer_maintenance_assumption": "bool", "observed_information_rate": "information/time"},
    "thermodynamic-economic-allocation": {"budget_usd": "USD", "declared_evidence_ready": "bool", "declared_price_authorized": "bool", "assets": "list of declared alternatives (USD fields)"},
}

H = lambda i, s, c: {"id": i, "statement": s, "check": c}  # noqa: E731
HYPOTHESES = {
    "mutualist": [
        H("rho_nonnegative", "The declared correlation magnitude is non-negative.", "rho >= 0"),
        H("sigma_positive", "The partner volatility is positive.", "sigma > 0"),
        H("sigma_tot_positive", "The total volatility is positive.", "sigma_tot > 0"),
    ],
    "restoration": [
        H("variability_nonnegative", "Site variability σ is non-negative.", "sigma >= 0"),
        H("drive_positive", "The establishment advantage Δμ is positive.", "delta_mu > 0"),
    ],
    "afforestation": [
        H("tension_positive", "Site variability σ is positive.", "sigma > 0"),
        H("drive_positive", "The establishment advantage Δμ is positive.", "delta_mu > 0"),
        H("prep_in_range", "The site-preparation lever is between 1 and 2 when supplied.", "prep is None or 1 <= prep <= 2"),
        H("rates_nonnegative", "Declared seeding rates are non-negative when supplied.", "(rate is None or rate >= 0) and (rate_max is None or rate_max >= 0)"),
    ],
    "harmonization": [
        H("costs_declared", "At least one steward reports a non-negative marginal cost.", "len(marginal_costs) >= 1 and all(c >= 0 for c in marginal_costs)"),
        H("overheads_nonnegative", "Declared overhead, bandwidth and ceiling are non-negative when supplied.", "(command_overhead is None or command_overhead >= 0) and (bandwidth is None or bandwidth >= 0) and (ib_bound is None or ib_bound >= 0)"),
    ],
    "carbon-continuity": [
        H("retention_living", "Living retention a lies in [0, 1).", "0 <= a < 1"),
        H("retention_durable", "Durable retention d lies in [0, 1).", "0 <= d < 1"),
        H("coupling_positive", "Both coupling coefficients r and p are positive.", "r > 0 and p > 0"),
    ],
    "tempo": [
        H("costs_positive", "Haste and neglect costs are positive.", "haste_cost > 0 and neglect_cost > 0"),
        H("cadence_positive", "The current cadence is positive.", "cadence > 0"),
    ],
    "shared-channel-coverage": [
        H("dimension_positive", "The control space has at least one dimension.", "dimension >= 1"),
        H("rank_within_dimension", "The shared channel's rank is between 0 and the dimension.", "0 <= rank <= dimension"),
        H("rank_zero_captures_nothing", "A rank-zero channel captures no fraction of the load.", "rank > 0 or captured_fraction == 0"),
        H("coefficients_in_range", "κ is non-negative, the captured fraction lies in [0, 1], cost and budget are positive.", "kappa >= 0 and 0 <= captured_fraction <= 1 and baseline_cost > 0 and dissipation_budget > 0"),
    ],
    "invariance-capacity": [
        H("entropy_nonnegative", "The conditional task entropy is non-negative.", "conditional_task_entropy >= 0"),
        H("leakage_budget_nonnegative", "The proxy-leakage budget is non-negative and separately justified.", "proxy_leakage_budget >= 0"),
    ],
    "precautionary-capacity": [
        H("moments_declared", "Mean capacity and its standard deviation are non-negative.", "mean_capacity >= 0 and capacity_sd >= 0"),
        H("violation_budget", "The violation probability α lies strictly between 0 and 1.", "0 < alpha < 1"),
        H("rate_pair", "Power and temperature are supplied together or not at all.", "(power is None) == (temperature is None)"),
    ],
    "reciprocity-corridor": [
        H("values_positive", "Both parties' values per unit flow are positive.", "value_x > 0 and value_y > 0"),
        H("costs_positive", "Both parties' costs per unit flow are positive.", "cost_x > 0 and cost_y > 0"),
        H("flow_positive", "Total flow is positive.", "total_flow > 0"),
    ],
    "anytime-change": [
        H("frozen_likelihoods", "Pre- and post-change Bernoulli probabilities lie in (0, 1) and differ.", "0 < p0 < 1 and 0 < p1 < 1 and p0 != p1"),
        H("alarm_budget", "The false-alarm budget α lies in (0, 1).", "0 < alpha < 1"),
        H("binary_observations", "Every observation is 0 or 1.", "all(o == 0 or o == 1 for o in observations)"),
    ],
    "seed-source-bottleneck": [
        H("demands_positive", "Every restoration site demands a positive amount.", "len(demands) >= 1 and all(x > 0 for x in demands)"),
        H("supplies_nonnegative", "Every seed source supplies a non-negative amount.", "len(supplies) >= 1 and all(x >= 0 for x in supplies)"),
        H("edges_in_range", "Every eligibility edge names an existing source and site.", "all(0 <= e[0] < len(supplies) and 0 <= e[1] < len(demands) for e in edges)"),
    ],
    "switching-hysteresis": [
        H("switch_costs_nonnegative", "Directional switching costs are non-negative.", "cost_plus_to_minus >= 0 and cost_minus_to_plus >= 0"),
        H("binary_state", "The current state is −1 or +1.", "current_state == 1 or current_state == -1"),
    ],
    "shadow-price-capacity": [
        H("geometry_positive", "Distance, area, horizon, tolerance and budget are positive.", "distance > 0 and area > 0 and horizon > 0 and tolerance > 0 and budget > 0"),
        H("capacity_coefficients", "Power and dissipation factor are non-negative; capacity cost is positive.", "power >= 0 and dissipation_factor >= 0 and capacity_cost > 0"),
        H("tower_prefactors_positive", "Every tower prefactor is positive.", "len(tower_prefactors) >= 1 and all(x > 0 for x in tower_prefactors)"),
    ],
    "multi-ring-alignment-capacity": [
        H("thermodynamic_constants", "Power is non-negative; k_B and T are positive.", "power >= 0 and boltzmann_constant > 0 and temperature > 0"),
        H("factors_unit_interval", "Every dissipation and alignment factor lies in [0, 1].", "all(0 <= x <= 1 for x in dissipation_factors) and all(0 <= x <= 1 for x in alignment_factors)"),
        H("one_factor_per_ring", "Each ring has one dissipation and one alignment factor.", "len(dissipation_factors) == len(alignment_factors) and len(dissipation_factors) >= 1"),
    ],
    "symbiotic-surplus": [
        H("landauer_positive", "The Landauer cost per bit is positive.", "epsilon_landauer > 0"),
        H("partners_declared", "Partner powers are non-negative and dissipation fractions lie in [0, 1].", "partner_a_power >= 0 and partner_e_power >= 0 and 0 <= partner_a_dissipation <= 1 and 0 <= partner_e_dissipation <= 1"),
        H("cauchy_schwarz", "The declared geometry satisfies the Cauchy–Schwarz premise.", "norm_a_squared > 0 and norm_e_squared > 0 and inner_product ** 2 <= norm_a_squared * norm_e_squared + 1e-12"),
        H("housekeeping_nonnegative", "Housekeeping dissipation is non-negative.", "housekeeping_dissipation >= 0"),
    ],
    "decision-information-capacity": [
        H("richness_unit_interval", "Predictive richness lies in [0, 1].", "0 <= predictive_richness <= 1"),
        H("rates_nonnegative", "Bandwidth, maintenance power and observed rate are non-negative.", "observation_bandwidth >= 0 and maintenance_power >= 0 and observed_information_rate >= 0"),
        H("thermodynamic_constants", "k_B and T are positive.", "boltzmann_constant > 0 and temperature > 0"),
    ],
    "thermodynamic-economic-allocation": [
        H("budget_nonnegative", "The declared budget is non-negative.", "budget_usd >= 0"),
        H("alternatives_declared", "Every alternative has positive capital cost and friction and non-negative burdens.", "len(assets) >= 1 and all(a['capital_cost_usd'] > 0 and a['transition_friction_usd'] > 0 and a['gross_avoided_value_usd'] >= 0 and a['embodied_transition_cost_usd'] >= 0 for a in assets)"),
        H("distinct_alternatives", "Alternative identifiers are distinct.", "len(sorted(a['asset_id'] for a in assets)) == len(assets)"),
    ],
}

# src/lib/kernelFamilyLabels.ts @ 398b177
FAMILY_LABELS = {
    "restoration-design": {"label": "Restoration & planting", "audience": "Conservation · land trusts · agencies"},
    "continuity-monitoring": {"label": "Continuity & timing", "audience": "Conservation · industry operations"},
    "governance-coordination": {"label": "Coordination & integrity", "audience": "Industry · business · multi-party programs"},
    "finance-risk": {"label": "Finance & risk", "audience": "Business · funders · natural-capital finance"},
}

# src/lib/decisionKernelCatalog.ts and conservationDecisionRuntime.ts @ 398b177
DATA_BOUNDARY = "Use synthetic, public, or de-identified values only. Do not submit customer records, credentials, or confidential evidence."
AUTHORITY_BOUNDARY = "This is an unsigned deterministic preview. It is not a Viridis-reviewed decision, production certificate, empirical validation, registry determination, credit, insurance decision, or legal conclusion."
# src/lib/osMap.ts @ 398b177
FOUNDATION_MODULES = ["P0_IntelligenceBound_COMPILED", "Viridis.P0BoundedMemoryDissipation", "Viridis.BoundedMemoryLearning", "Viridis.BiosphereErasureBound", "P4_ThermodynamicEconomics"]

STANDARD_BOUNDARY = "The result is conditional on the supplied inputs; it does not establish empirical validity, Viridis review, certification, a credit, or a registry determination."


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--app", type=Path, required=True)
    cli.add_argument("--golden", type=Path, required=True)
    cli.add_argument("--root", type=Path, default=Path("."))
    args = cli.parse_args()
    root = args.root.resolve()
    app = args.app.resolve()
    state = json.loads((app / "src/content/viridisOSProductState.json").read_text())
    kmap = json.loads((app / "src/content/conservationKernelMap.json").read_text())
    core = json.loads((app / "src/content/coreKernelOS.json").read_text())
    guide = json.loads((app / "src/content/kernelCustomerGuide.json").read_text())["modules"]
    golden = json.loads(args.golden.read_text())

    family_of = {m["id"]: f["id"] for f in kmap["families"] for m in f["modules"]}
    boundary_of = {f["id"]: f["decision_boundary"] for f in kmap["families"]}

    for module in state["modules"]:
        mid = module["id"]
        schema = module["input_schema"]
        required = list(schema.get("required", []))
        names = required + sorted(k for k in schema["properties"] if k not in required)
        inputs = []
        for name in names:
            prop = dict(schema["properties"][name])
            entry = {"name": name, "required": name in required, **prop}
            entry["unit"] = INPUT_UNITS[mid][name]
            entry["help"] = guide[mid]["inputs"][name]
            inputs.append(entry)
        units = module["units"]
        if mid in golden:
            out_names = list(golden[mid]["outputs"].keys())
        else:
            out_names = list(units.keys())
        outputs = [{"name": n, **({"unit": units[n]} if n in units else {})} for n in out_names]
        extra_units = [n for n in units if n not in out_names]
        for n in extra_units:  # declared unit for an input echo or a legacy field
            outputs.append({"name": n, "unit": units[n], "input_echo": True})
        sources = [{"path": p, "sha256": sha256_file(root / p)} for p in LEAN_SOURCES[mid]]
        if mid == "mutualist":
            tier, runner, reconciliation = "reference", None, None
        elif mid in ADMITTED:
            tier, runner, reconciliation = "admitted", "runner.py", None
        elif mid == "tempo":
            tier, runner = "callable", "runner.py"
            reconciliation = {
                "code": "CANON_RECORD",
                "note": "The StewardshipTempo Lean source behind DOI 10.5281/zenodo.20705183 is not in this repository; the function stays callable preview-only until the source is deposited here and its hash is recorded.",
            }
        else:
            tier, runner = "callable", "runner.py"
            reconciliation = {
                "code": "CANON_CLASSIFICATION",
                "note": "The package's Lean status in the canon catalog is 'working' (not spine-admitted); the product warrant was admitted but the canon classification must be reconciled before admission as a function.",
            }
        family = family_of.get(mid)
        manifest = {
            "$schema": SCHEMA_URL,
            "schema_version": 1,
            "id": mid,
            "kind": "decision_kernel",
            "name": module["name"],
            "version": module["version"],
            "summary": guide[mid]["summary"],
            "line": module["line"],
            "decision_family": family,
            "tier": tier,
            "state": module["state"],
            "reconciliation": reconciliation,
            "blocked": (
                {"verdict": module["warrant_verdict"], "reason": "BLOCKED_PRODUCT_WARRANT_REQUIRED: no accepted product warrant; no runner is published."}
                if module["state"] == "BLOCKED"
                else None
            ),
            "doi": module["backing"]["doi"],
            "lean": {
                "module": module["backing"]["lean_module"],
                "sources": sources,
                "theorems": THEOREMS[mid],
                "verification_provider": module["backing"].get("verification_provider"),
                "verification_receipt_id": module["backing"].get("verification_receipt_id"),
            },
            "inputs": inputs,
            "outputs": outputs,
            "hypotheses": HYPOTHESES[mid],
            "example": (
                {"inputs": golden[mid]["inputs"], "expected_outputs": golden[mid]["outputs"]}
                if mid in golden
                else None
            ),
            "scope": module["scope"],
            "boundary": f"{boundary_of[family]} {STANDARD_BOUNDARY}" if family else STANDARD_BOUNDARY,
            "empirical_validation": "NOT_VALIDATED",
            "runner": runner,
            "provenance": {
                "migrated_from": "viridis-conservation-app@398b177",
                "warrant_verdict": module["warrant_verdict"],
                "doi_state": module["doi_state"],
            },
        }
        write_json(root / DIRS[mid] / "function.json", manifest)

    families = []
    for family in kmap["families"]:
        families.append({
            "id": family["id"],
            "name": family["name"],
            "label": FAMILY_LABELS[family["id"]]["label"],
            "audience": FAMILY_LABELS[family["id"]]["audience"],
            "question": family["question"],
            "decision_boundary": family["decision_boundary"],
            "required_evidence": family["required_evidence"],
            "function_order": [m["id"] for m in family["modules"]],
        })
    write_json(root / "os/families.json", {"schema_version": 1, "standard": "VOS-DECISION-FAMILIES-1", "families": families})

    write_json(root / "os/core.json", {
        "schema_version": 1,
        "standard": core["standard"],
        "purpose": core["purpose"],
        "snapshot_date": core["snapshot_date"],
        "authority": core["authority"],
        "map_authority": kmap["authority"],
        "runtime_rule": kmap["runtime_rule"],
        "service": {
            "name": "Viridis Conservation decision-kernel previews",
            "schema_version": "viridisos.conservation-decision-services.v1",
            "access": "OPEN_REFERENCE",
            "receipt_class": "UNSIGNED_PUBLIC_PREVIEW",
            "public_run_authority": "UNSIGNED_NOT_VIRIDIS_REVIEWED",
            "data_boundary": DATA_BOUNDARY,
            "authority_boundary": AUTHORITY_BOUNDARY,
        },
        "function_order": [m["id"] for m in state["modules"]],
        "foundation_lean_modules": FOUNDATION_MODULES,
        "operating_tree": core["operating_tree"],
        "held_science_proposals": core["held_science_proposals"],
    })
    write_json(root / "os/research_intake.json", {
        "schema_version": 1,
        "standard": state["source"]["research_intake_standard"],
        "records": state["research_intake"],
    })
    ledger = []
    for module in state["modules"]:
        if module["id"] in ADMITTED:
            ledger.append({
                "id": module["id"],
                "tier": "admitted",
                "warrant_verdict": module["warrant_verdict"],
                "evidence": f"Product warrant {module['warrant_verdict']} with service state READY_UNSIGNED_PREVIEW in viridis-conservation-app@398b177 (backing receipt {module['backing'].get('verification_receipt_id')}).",
                "human_gate": "Carried forward by the WS-20 migration; takes effect only when the repository owner merges the PR that adds this entry.",
            })
    write_json(root / "os/admissions.json", {
        "schema_version": 1,
        "policy": "A function may declare tier 'admitted' only if it is listed here. Entries are added by human-authored commits reviewed by the repository owner (see CODEOWNERS). The OS compiler reads this file and never writes it.",
        "admitted": ledger,
    })
    print(f"wrote {len(state['modules'])} manifests and os/ governance files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
