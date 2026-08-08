# Frozen statement contract - Run 119 Scheduler Free-Energy Certificate

Source: immutable `Run-119_scheduler-free-energy-certificate`, its hash-bound r1 replay/reconciliation overlay, and quality receipt `PASS / HOLD_ARISTOTLE`.

The following paper targets are frozen exactly as written in `SchedulerFreeEnergy.lean`:

1. `reset_partition_function_identity`
2. `max_age_minimizes_next_logsumexp`
3. `unique_max_age_unique_minimizer`
4. `tied_maxima_equal_next_potential`
5. `logsumexp_bounds_max_age`

The auxiliary theorem `scheduler_free_energy_nonvacuous` is the explicit concrete audit witness requested by the zero-sorry pipeline; it is not a sixth novelty claim.

No theorem or the definitions `nextAge`, `partition`, and `freeEnergy` may be weakened, renamed, totalized differently, or made vacuous. No new axioms, unsafe declarations, `native_decide`, `implemented_by`, `@[extern]`, or external proof escapes are allowed.

Scope boundary: this contract proves a one-step equal-cost deterministic age-reset certificate. It does not establish long-run scheduler optimality, productivity, scientific importance, unequal-cost optimality, policy adoption, or priority over Age-of-Information, MaxWeight, Whittle-index, or curriculum-scheduling theory.
