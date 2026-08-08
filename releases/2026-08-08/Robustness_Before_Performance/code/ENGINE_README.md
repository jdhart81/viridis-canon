# Robustness Algorithm

A first-principles decision system for designing and governing systems that must remain viable under disturbance.

**Current reference kernel: v0.6.0.** It adds ordered disturbance trajectories,
coverage gates, recovery and aftershock measures to interval-valued outcomes,
robust dominance, content-addressed lineage and cascading recall, the
epistemic claim firewall, transitive failure-domain analysis, bounded
authority/execution boundary, and deterministic decision gates.

The project is intended to work across societal policy, cybersecurity, architecture, infrastructure, organizations, and product design. It does this through a stable domain-independent decision kernel plus domain-specific evidence, models, and metrics.

## Core proposition

Robustness is not an intrinsic score. It is a declared relationship:

> A system is robust when specified essential functions remain within acceptable bounds, for specified stakeholders and scales, across a declared range of disturbances and time horizons, without exporting unacceptable fragility elsewhere.

The algorithm therefore asks six questions before it scores anything:

1. What system and boundary are being considered?
2. Which functions, rights, or identities must remain viable?
3. Which disturbances and combinations must be survived?
4. Over what time horizon and at which scales?
5. Who benefits, who bears the cost, and where can fragility be displaced?
6. What evidence justifies the model and the decision?

## Architecture

The project has three layers:

1. **Constitutional layer** — authority, stakeholder rights, non-compensable constraints, decision rules, and auditability.
2. **Robustness kernel** — viability gates, scenario generation, stress evaluation, recovery and adaptation analysis, fragility accounting, and Pareto comparison.
3. **Domain adapters** — domain ontologies, simulators, evidence standards, scenarios, and metrics for policy, cyber, buildings, products, and later fields.

Fallback paths are expanded through a typed dependency DAG, allowing the kernel to identify hidden common owners, control planes, resources, locations, suppliers, and technologies. Selection is also separated from execution: a decision record can report `AUTHORIZED_NOT_EXECUTED` only when an active, unexpired authority lease covers the action, and the reference kernel never executes the action itself.

Important claims carry explicit, evidence-class-bound states: `ASSUMED`,
`HYPOTHESIZED`, `NUMERICALLY_SUPPORTED`, `REPRODUCED`, `FORMALLY_PROVED`,
`EMPIRICALLY_SUPPORTED`, `AUTHORIZED`, `DEPLOYED`, and `OBSERVED`. The engine
applies no implication edges among them. A proof therefore cannot silently
become authorization, and deployment cannot silently become an observed
successful outcome.

The kernel produces a robustness profile and decision record, not an allegedly universal number. A compact ranking score may be used only after all hard constraints pass and only within the same declared decision frame.

Every outcome bundle now binds its declared model and adapters through a
content-addressed lineage DAG. An effective recall propagates to every
descendant. If any required artifact is recalled or transitively quarantined,
the engine returns `HOLD` before evaluating candidates. Recall is evaluated at
the case's fixed timestamp, so a future-dated recall is visible but not applied
prematurely.

Assessments and comparison metrics may carry declared numeric intervals. A
mandatory non-compensable interval that stays safe passes; one that stays
outside the boundary fails; one that crosses the boundary returns `HOLD`.
Candidate A robustly dominates candidate B only when A's worst case is no worse
than B's best case in every comparison dimension and strictly better in at
least one. Overlapping intervals remain unresolved instead of being collapsed
to their point estimates.

Outcome bundles also carry ordered trajectory samples with explicit elapsed
time and evidence. The kernel reports declared piecewise-linear shortfall,
possible and robust violation spans, guaranteed recovery after the worst
sample, and pass-to-nonpass aftershocks. A governance-declared minimum coverage
floor prevents sparse path evidence from masquerading as complete temporal
analysis. These measures describe the supplied samples and interpolation
contract; they do not establish that the real system followed the path.

## Initial specification

- [First-principles constitution](docs/FIRST_PRINCIPLES.md)
- [Algorithm specification](docs/ALGORITHM_SPEC.md)
- [Epistemic claim firewall](docs/EPISTEMIC_FIREWALL.md)
- [Content-addressed lineage and cascading recall](docs/LINEAGE_AND_RECALL.md)
- [Intervals and robust dominance](docs/INTERVALS_AND_ROBUST_DOMINANCE.md)
- [Trajectory analysis](docs/TRAJECTORY_ANALYSIS.md)
- [v1.0 final release criteria](docs/FINAL_RELEASE_CRITERIA.md)
- [v1.0 formal claim matrix](docs/FORMAL_CLAIM_MATRIX.md)
- [Cross-domain mapping](docs/CROSS_DOMAIN_MAPPING.md)
- [Decision-case schema](schemas/decision-case.schema.json)
- [Outcome-bundle schema](schemas/outcome-bundle.schema.json)
- [Decision-record schema](schemas/decision-record.schema.json)
- [Reference implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Known limitations and v0.7 target](docs/KNOWN_LIMITATIONS.md)
- [Viridis cross-project source synthesis](docs/VIRIDIS_SOURCE_SYNTHESIS.md)
- [Audited v1 formal package](formal/v1/aristotle_audited/attempt-1/AUDITED_FORMAL_RECEIPT.json)
- [Final v1 paper package](paper/v1/README.md)
- [Directed canon successor and holds](canon/v1/README.md)
- [Production fleet service receipt](integration/agent_fleet/robustness-engine-agent/PRODUCTION_DEPLOYMENT_RECEIPT.json)
- [Current five-gate release receipt](release/v1/CURRENT_GATE_RECEIPT.json)
- [Changelog](CHANGELOG.md)

The v0.3 formal and paper package remains an immutable predecessor. The v1
successor separately freezes 27 named Lean theorems, including 22 contract
targets in F1--F9 for dependency diversity, authority, claim-state separation,
cascading recall, closed intervals, robust dominance, trajectories,
aftershocks, and release-state separation. Aristotle returned the exact frozen
source byte-for-byte and added 19 non-degeneracy review checks. The independent
Viridis rebuild passed 930 jobs, statement freeze, zero-sorry,
forbidden-construct, allowed-axiom, non-vacuity, and significance gates.

The five-page v1 paper is reconciled to that exact audit. The v0.6 engine passes
35 reference tests, and the complete isolated agent fleet passes 2,136 tests
across 37 agents. The digest-bound AMD64 service is deployed internally on the
Viridis fleet with final health, canonical evaluation, internal reachability,
and an eight-second rollback drill verified. It evaluates only and never
executes a decision. These facts do not establish empirical validity,
legitimate authority, adoption, revenue, or beneficial outcomes. Public canon
release remains held on a separate curator review, exact license, real ledger
row, and accountable publication authorization.

## Development sequence

1. Freeze the conceptual constitution and vocabulary.
2. Implement a deterministic reference kernel operating on structured decision cases.
3. Build one societal-governance adapter and one cybersecurity adapter to test whether the kernel is genuinely domain-independent.
4. Add interval uncertainty, trajectory analysis, scenario-generation,
   simulation, and adversarial modules.
5. Validate decisions retrospectively, prospectively, and through red-team exercises.

## Run the reference cases

```bash
PYTHONPATH=src python3 -m robustness_engine.cli \
  examples/municipal_heat/case.json \
  examples/municipal_heat/outcomes.json \
  --pretty

PYTHONPATH=src python3 -m robustness_engine.cli \
  examples/cyber_identity/case.json \
  examples/cyber_identity/outcomes.json \
  --pretty
```

Run the test suite with:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Non-goals

This system will not:

- claim to eliminate uncertainty;
- replace political legitimacy, professional judgment, or accountable decision-makers;
- average away rights violations or catastrophic outcomes;
- label ordinary redundancy as robust when all backups share a failure mode;
- optimize a system by exporting fragility to another population, place, or time;
- treat efficiency and robustness as universal opposites.
