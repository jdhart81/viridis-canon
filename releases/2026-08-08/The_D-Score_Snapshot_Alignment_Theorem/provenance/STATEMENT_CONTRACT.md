# Frozen statement contract - Run 118 Snapshot Alignment

Source: immutable `Run-118_dscore-snapshot-alignment`, quality receipt `PASS / HOLD_ARISTOTLE` after the deterministic N4/N6 reader repair.

The following six declarations, their namespaces, hypotheses, conclusions, and auxiliary definitions are frozen exactly as written in `SnapshotAlignment.lean`:

1. `phasor_energy_pairwise_identity`
2. `alignment_efficiency_unit_interval`
3. `delay_variance_bounds_alignment_loss`
4. `alignment_budget_sufficient_for_band`
5. `equal_delay_perfect_alignment`
6. `two_channel_half_period_cancellation`

The first theorem is the exact double-sum form of the paper's diagonal-plus-off-diagonal cosine identity. The fourth theorem is only a model-scoped sufficient condition, never a necessary condition or empirical guarantee. The sixth theorem supplies an explicit two-channel destructive-interference control and non-vacuity witness.

No theorem may be weakened, renamed, made vacuous, or proved by adding axioms, `native_decide`, `implemented_by`, `@[extern]`, or other escape hatches. The definitions `phasor`, `alignment`, `weightedMean`, and `delayVariance` may not be strengthened or altered.

Novelty boundary: prior Viridis work uses generic cosine-squared alignment efficiency and ecological portfolio asynchrony, especially Runs 017, 086, 093, 095, 097, and 099. Run 118's distinct candidate contribution is the timestamp-delay phasor identity and its weighted delay-variance sufficient budget. This is a novelty reference, not a priority claim.
