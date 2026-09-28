import Mathlib

namespace Viridis.EntropyLearning.RetentionFloor

/-!
Frozen algebraic certificate for Run 136. This file formalizes rational
availability and the max-min budget certificate. It does not formalize a
continuous-time Markov chain, empirical forgetting, replay safety, or novelty.

Notes on the frozen source.

* The three definitions had to be marked `noncomputable`; real division is
  noncomputable in Mathlib, so the file as delivered did not elaborate. The
  definitions themselves are unchanged.
* Two of the six frozen statements are false as written. Both are preserved
  verbatim, commented out, immediately above an explicit disproof
  (`..._as_frozen_is_false`) and a minimally repaired version that keeps the
  frozen name. The repairs add one hypothesis each and nothing else:
  - `retention_floor_upper_bound` needs `0 < n` (with `n = 0` and `B = 0`
    every hypothesis is vacuous or trivial while the conclusion reads
    `q ≤ qStar 0 0 = 0`, which fails for e.g. `q = 1/2`);
  - `retention_floor_unique` needs `∀ i, 0 ≤ r i` (the same nonnegativity the
    frozen `retention_floor_upper_bound` already assumes): if `r i < -lam i`
    then `retained (r i) (lam i) > 1`, so the attainment hypothesis is
    satisfied by grossly negative rates that free up budget elsewhere.
-/

noncomputable def retained (r lam : ℝ) : ℝ := r / (r + lam)

noncomputable def qStar (B L : ℝ) : ℝ := B / (B + L)

noncomputable def rateStar (B L lam : ℝ) : ℝ := B * lam / L

theorem stationary_availability_balance
    (r lam : ℝ) (hr : 0 ≤ r) (hlam : 0 < lam) :
    (1 - retained r lam) * r = retained r lam * lam := by
  sorry

theorem floor_requirement
    (q r lam : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q < 1)
    (hr : 0 ≤ r) (hlam : 0 < lam)
    (hfloor : q ≤ retained r lam) :
    (q / (1 - q)) * lam ≤ r := by
  sorry

/-- The frozen form of `retention_floor_upper_bound` is refuted by the empty
index set together with zero budget: there `qStar B (∑ i, c i * lam i)`
is `0 / 0 = 0`, while `q` is only constrained by `0 ≤ q < 1`. -/
theorem retention_floor_upper_bound_as_frozen_is_false :
    ¬ (∀ {n : ℕ} (B : ℝ) (c lam r : Fin n → ℝ) (q : ℝ),
        0 ≤ B → (∀ i, 0 < c i) → (∀ i, 0 < lam i) → (∀ i, 0 ≤ r i) →
        0 ≤ q → q < 1 → (∀ i, q ≤ retained (r i) (lam i)) →
        (∑ i, c i * r i ≤ B) → q ≤ qStar B (∑ i, c i * lam i)) := by
  sorry

/-- Repaired `retention_floor_upper_bound`: the frozen statement with the
single extra hypothesis `hn : 0 < n`, which rules out the degenerate empty
system in which the budget constraint carries no information. All other
hypotheses and the conclusion are unchanged. -/
theorem retention_floor_upper_bound
    {n : ℕ} (B : ℝ) (c lam r : Fin n → ℝ) (q : ℝ)
    (hn : 0 < n)
    (hB : 0 ≤ B) (hc : ∀ i, 0 < c i) (hlam : ∀ i, 0 < lam i)
    (hr : ∀ i, 0 ≤ r i) (hq0 : 0 ≤ q) (hq1 : q < 1)
    (hret : ∀ i, q ≤ retained (r i) (lam i))
    (hbudget : ∑ i, c i * r i ≤ B) :
    q ≤ qStar B (∑ i, c i * lam i) := by
  sorry

theorem hazard_proportional_attains_floor
    (B L lam : ℝ) (hB : 0 < B) (hL : 0 < L) (hlam : 0 < lam) :
    retained (rateStar B L lam) lam = qStar B L := by
  sorry

/-- The frozen form of `retention_floor_unique` is refuted by `n = 2`,
`B = 2`, unit costs and hazards and `r = (-2, 1)`: since `retained (-2) 1 = 2`,
the attainment hypothesis holds at both coordinates and the budget is met,
yet `r 0 ≠ rateStar 2 2 1 = 1`. -/
theorem retention_floor_unique_as_frozen_is_false :
    ¬ (∀ {n : ℕ} (B : ℝ) (c lam r : Fin n → ℝ),
        0 < B → (∀ i, 0 < c i) → (∀ i, 0 < lam i) → (0 < ∑ i, c i * lam i) →
        (∑ i, c i * r i ≤ B) →
        (∀ i, qStar B (∑ j, c j * lam j) ≤ retained (r i) (lam i)) →
        ∀ i, r i = rateStar B (∑ j, c j * lam j) (lam i)) := by
  sorry

/-- Repaired `retention_floor_unique`: the frozen statement with the single
extra hypothesis `hr : ∀ i, 0 ≤ r i` (nonnegativity of the refresh rates,
exactly as assumed in `retention_floor_upper_bound`). All other hypotheses and
the conclusion are unchanged. -/
theorem retention_floor_unique
    {n : ℕ} (B : ℝ) (c lam r : Fin n → ℝ)
    (hB : 0 < B) (hc : ∀ i, 0 < c i) (hlam : ∀ i, 0 < lam i)
    (hr : ∀ i, 0 ≤ r i)
    (hL : 0 < ∑ i, c i * lam i)
    (hbudget : ∑ i, c i * r i ≤ B)
    (hattain : ∀ i, qStar B (∑ j, c j * lam j) ≤ retained (r i) (lam i)) :
    ∀ i, r i = rateStar B (∑ j, c j * lam j) (lam i) := by
  sorry

theorem retention_floor_nonvacuous :
    let B : ℝ := 10
    let L : ℝ := 10
    retained (rateStar B L 1) 1 = (1 / 2 : ℝ) ∧
    retained (rateStar B L 9) 9 = (1 / 2 : ℝ) ∧
    rateStar B L 1 + rateStar B L 9 = 10 := by
  sorry

end Viridis.EntropyLearning.RetentionFloor
