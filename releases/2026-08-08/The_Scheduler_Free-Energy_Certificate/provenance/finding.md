# Finding - Run 119: The Scheduler Free-Energy Certificate

## Status boundary

`GENERATED_EXPLORATION`; novelty `UNASSESSED`; numerical status
`NUMERICAL_GATE_PASS`; Aristotle `NOT_RUN`. Every proposed Lean target is
unproved. This META may propose policy changes but cannot adopt them.

## Preregistered question

Can the severe-starvation rule be given an exact one-step potential certificate,
and is the current versioned policy sufficient to reproduce the selector
without inherited prose?

Before drafting conclusions, `verification.py` fixed four hypotheses:

1. resetting a maximum-age component minimizes a log-sum-exp staleness
   potential for every positive inverse temperature;
2. the locked META transition raises the live checksum from 139 to 155 and
   makes area `[13]` the unique Run 120 severe-starvation choice;
3. the v1 policy is not a total executable selector because
   `scoring_staleness` and tie-breaking are undefined; and
4. a proposal that defines those operations leaves the actual Run 119/120
   replay unchanged while resolving an adversarial tied state.

The gate would falsify the run on any analytic or randomized counterexample,
any temperature-dependent change in the next area, any existing policy text
that supplied the allegedly missing definitions, or any replay drift.

## Assumptions

1. Ages are nonnegative integers measured immediately before a run.
2. A normal area run has equal unit cost: all ages increment, then the selected
   area resets to zero.
3. A META increments all ages and resets none.
4. The certificate concerns staleness only. Scientific importance, inbound
   flags, tier value, lens fit, expected information gain, and unequal effort
   costs are held outside the theorem.
5. The current machine state and policy hashes are the locked inputs printed in
   `verification_output.txt`.

## Exact result

Let `a=(a_1,...,a_n)` and let service of area `j` produce

`a'_j=0`, and `a'_i=a_i+1` for `i != j`.

For `beta>0`, define the exponential staleness partition function and free
energy

`Z_beta(a)=sum_i exp(beta a_i)`,

`F_beta(a)=beta^-1 log Z_beta(a)`.

After serving `j`,

`Z_beta(a after j) = 1 + exp(beta)[Z_beta(a)-exp(beta a_j)]`.

Thus for two choices `j` and `k`,

`Z_beta(a after j)-Z_beta(a after k)
 = exp(beta)[exp(beta a_k)-exp(beta a_j)]`.

Because the logarithm is increasing, `F_beta(a after j)` is minimized exactly
when `a_j` is maximal. The choice is unique exactly when the maximum is unique.
The numerical gate checked the identity directly, exhaustively over 78,100
small state/temperature combinations, and on 10,000 randomized unique-maximum
states.

This is a scheduling identity, not a thermodynamic law about the research
system. The thermodynamic lens supplies a soft-maximum potential: as
`beta -> infinity`, `F_beta` approaches the worst age; as `beta -> 0`, the
unscaled partition function loses selection information. The beta-zero case is
retained as a negative control.

## Locked Run 119/120 replay

The authoritative pre-run ages sum to 139. A META increments all sixteen ages
and resets none, so the post-Run-119 checksum is 155. The deepest post-META
ages are:

| Area | Post-META age | Relevant rail |
|---|---:|---|
| `[13]` Computational Theory | 22 | severe starvation |
| `[12]` AI Wavefunction Collapse | 20 | below severe threshold |
| `[06]` Entropy-Driven Learning | 16 | Tier-2 floor |
| `[07]` Gaian Systems | 15 | Tier-2 floor |

Severe starvation precedes tier floors. Area `[13]` is therefore the unique
Run 120 area for every tested `beta` from `1e-6` through `100`. Lens rotation
after Thermodynamic gives Stewardship, and the area was last visited in Run 097,
so the distance at Run 120 is 23, above the 16-run combination guard.

## Policy-schema HOLD

The science result supports the existing severe-starvation idea but the policy
artifact is not yet a complete executable specification:

- its score formula is `tier_weight * scoring_staleness +
  standing_inbound_flags + coverage_relief`, while `scoring_staleness` has no
  JSON definition;
- no deterministic tie-break is specified for severe-starvation or other
  same-precedence candidates; and
- the normal and META state transitions are not encoded in the policy.

The current Run 120 decision is unaffected because the maximum is unique.
An adversarial state tying areas `[12]` and `[13]` at age 22 produces two valid
current-policy candidates. The proposal resolves that state by pre-run age,
then current score, then area ID. That tie-break is one reviewable choice, not a
scientific necessity.

`POLICY_PROPOSAL_v1.1.json` records the versioned draft. It was replayed against
the actual state and does not change Runs 119 or 120. It remains blocked on an
independent accountable control-plane review, schema validation, a full replay
from a machine-readable transition ledger, and fresh regression tests. No
governing file was changed.

## Negative controls and limits

- Equal maximum ages give equal one-step free energy, so the certificate cannot
  choose between tied maxima.
- At `beta=0`, every choice has the same unscaled partition function.
- If service costs differ, the oldest area need not maximize net benefit. The
  gate constructs a two-area counterexample with costs 100 and 1.
- One-step potential minimization does not imply long-run scientific
  productivity, novelty, optimal thresholds, or correct tier weights.
- Prior Age-of-Information and MaxWeight literature contains richer stochastic,
  unreliable, and weighted scheduling results. This run does not claim priority
  over those theories.

## Falsification and verification plan

For the policy proposal, build an append-only machine transition ledger from a
frozen historical start state. Replay every subsequent selection twice: once
with an independently implemented reference selector and once with the proposed
schema. Require byte-identical directives and state hashes on all untied
historical cases, explicitly enumerate tied cases, and compare starvation,
diversity, flag-debt, and override-rate metrics out of sample. Reject the
proposal if it changes an untied historical decision, hides a prose-only input,
increases maximum age, or reduces diversity without a predeclared benefit.

For the scientific model, introduce unequal service costs and stochastic
research returns. Compare max-age, current score, and risk-sensitive index
policies over preregistered synthetic regimes. The equal-cost certificate is
refuted as a general scheduler claim as soon as a costed or stochastic regime
chooses a different action with lower declared loss; the included cost control
already shows why the current result must remain narrow.

## Proposed Lean targets - explicitly unproved

- `reset_partition_function_identity`
- `max_age_minimizes_next_logsumexp`
- `unique_max_age_unique_minimizer`
- `tied_maxima_equal_next_potential`
- `logsumexp_bounds_max_age`

These are `FORMAL_TARGET` entries only. Aristotle was not run.

## Advisory outcome

Internal methods branch; `HOLD` policy adoption pending independent review and
full replay. Proposed spine effect: none. The generator exits only
`GENERATED_EXPLORATION`.
