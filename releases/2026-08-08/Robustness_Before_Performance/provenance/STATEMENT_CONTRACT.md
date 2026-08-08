# Frozen-candidate statement contract — Robustness Kernel v1.0

**State:** Local preflight candidate. This contract is not Aristotle-audited
until an immutable request is accepted, returned, and independently verified.

The successor package preserves the v0.3 results and adds exact mathematical
claims for the later deterministic mechanisms. The following definitions and
theorem signatures may not be weakened, renamed, made vacuous, or replaced by
stronger assumptions after submission:

1. `shared_dependency_strictly_reduces_independence`
2. `hidden_common_parent_lowers_independence`
3. `execution_authority_gate_iff`
4. `advisory_selection_never_authorizes_execution`
5. `revoked_or_expired_lease_denies_execution`
6. `derivable_iff_explicitly_asserted`
7. `distinct_state_is_not_derived_from_singleton`
8. `recalled_artifact_is_blocked`
9. `descendant_of_recalled_artifact_is_blocked`
10. `unrelated_artifact_is_not_blocked`
11. `robust_pass_and_fail_are_disjoint`
12. `interval_classification_complete`
13. `interval_classification_pass_iff`
14. `interval_classification_fail_iff`
15. `robust_dominance_irreflexive`
16. `robust_dominance_transitive`
17. `trajectory_shortfall_nonnegative`
18. `nonnegative_trajectory_has_zero_shortfall`
19. `marked_violation_span_nonnegative`
20. `aftershock_count_le_adjacent_pairs`
21. `release_states_are_independent_nonvacuous`
22. `robustness_kernel_v1_nonvacuous`

No `sorry`, `admit`, `sorryAx`, new `axiom`, unsafe declaration,
`native_decide`, `implemented_by`, `extern`, opaque proof escape, or partial
definition is allowed. Approved logical axioms are limited to those already
accepted by the Viridis Lean audit policy.

Scope boundary: the package proves properties of declared finite structures,
closed rational intervals, Boolean authority conditions, and sampled rational
trajectories. It does not prove real-world dependency completeness, calibrated
uncertainty, truthful evidence, legitimate authority, causal scenario
coverage, deployment, adoption, revenue, or observed outcomes.
