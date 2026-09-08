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
  have hrl : r + lam ≠ 0 := by positivity
  simp only [retained]
  field_simp
  ring

theorem floor_requirement
    (q r lam : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q < 1)
    (hr : 0 ≤ r) (hlam : 0 < lam)
    (hfloor : q ≤ retained r lam) :
    (q / (1 - q)) * lam ≤ r := by
  have hrl : 0 < r + lam := by linarith
  rw [retained, le_div_iff₀ hrl] at hfloor
  rw [div_mul_eq_mul_div, div_le_iff₀ (by linarith : (0:ℝ) < 1 - q)]
  nlinarith

/-- The frozen form of `retention_floor_upper_bound` is refuted by the empty
index set together with zero budget: there `qStar B (∑ i, c i * lam i)`
is `0 / 0 = 0`, while `q` is only constrained by `0 ≤ q < 1`. -/
theorem retention_floor_upper_bound_as_frozen_is_false :
    ¬ (∀ {n : ℕ} (B : ℝ) (c lam r : Fin n → ℝ) (q : ℝ),
        0 ≤ B → (∀ i, 0 < c i) → (∀ i, 0 < lam i) → (∀ i, 0 ≤ r i) →
        0 ≤ q → q < 1 → (∀ i, q ≤ retained (r i) (lam i)) →
        (∑ i, c i * r i ≤ B) → q ≤ qStar B (∑ i, c i * lam i)) := by
  intro h
  have key := @h 0 0 (fun _ => 1) (fun _ => 1) (fun _ => 1) (1 / 2) le_rfl
    (by simp) (by simp) (by simp) (by norm_num) (by norm_num) (by simp) (by simp)
  simp [qStar] at key
  linarith

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
  haveI : Nonempty (Fin n) := Fin.pos_iff_nonempty.mp hn
  set L := ∑ i, c i * lam i with hLdef
  have hL : 0 < L := by
    rw [hLdef]
    exact Finset.sum_pos (fun i _ => mul_pos (hc i) (hlam i)) Finset.univ_nonempty
  have hq1' : (0:ℝ) < 1 - q := by linarith
  have key : ∀ i, (q / (1 - q)) * lam i ≤ r i := fun i =>
    floor_requirement q (r i) (lam i) hq0 hq1 (hr i) (hlam i) (hret i)
  have hsum : (q / (1 - q)) * L ≤ ∑ i, c i * r i := by
    rw [hLdef, Finset.mul_sum]
    refine Finset.sum_le_sum fun i _ => ?_
    have h1 := key i
    nlinarith [(hc i).le]
  have hfin : (q / (1 - q)) * L ≤ B := le_trans hsum hbudget
  rw [div_mul_eq_mul_div, div_le_iff₀ hq1'] at hfin
  rw [qStar, le_div_iff₀ (by linarith)]
  nlinarith

theorem hazard_proportional_attains_floor
    (B L lam : ℝ) (hB : 0 < B) (hL : 0 < L) (hlam : 0 < lam) :
    retained (rateStar B L lam) lam = qStar B L := by
  have hLne : L ≠ 0 := ne_of_gt hL
  have hBL : B + L ≠ 0 := by positivity
  have hden : B * lam / L + lam ≠ 0 := by positivity
  rw [retained, rateStar, qStar, div_eq_div_iff hden hBL]
  field_simp

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
  intro h
  have key := @h 2 2 (fun _ => 1) (fun _ => 1) (fun i => if i = 0 then -2 else 1)
    (by norm_num) (by simp) (by simp) (by norm_num [Fin.sum_univ_two])
    (by norm_num [Fin.sum_univ_two]) ?_ 0
  · norm_num [rateStar, Fin.sum_univ_two] at key
  · intro i
    fin_cases i <;> norm_num [qStar, retained, Fin.sum_univ_two]

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
  intro i
  set L := ∑ j, c j * lam j with hLdef
  have hLne : L ≠ 0 := ne_of_gt hL
  have hBL : (0:ℝ) < B + L := by linarith
  have hq0 : 0 ≤ qStar B L := by rw [qStar]; positivity
  have hq1 : qStar B L < 1 := by
    rw [qStar, div_lt_one hBL]; linarith
  have hne : (1 : ℝ) - qStar B L ≠ 0 := ne_of_gt (by linarith)
  have hratio : qStar B L / (1 - qStar B L) = B / L := by
    rw [div_eq_div_iff hne hLne, qStar]
    field_simp
    ring
  have key : ∀ j, (B / L) * lam j ≤ r j := by
    intro j
    have h1 := floor_requirement (qStar B L) (r j) (lam j) hq0 hq1 (hr j) (hlam j) (hattain j)
    rwa [hratio] at h1
  have hge : ∀ j ∈ Finset.univ, c j * ((B / L) * lam j) ≤ c j * r j :=
    fun j _ => mul_le_mul_of_nonneg_left (key j) (hc j).le
  have hsum : ∑ j, c j * ((B / L) * lam j) = B := by
    have h2 : ∑ j, c j * ((B / L) * lam j) = (B / L) * L := by
      rw [hLdef, Finset.mul_sum]
      exact Finset.sum_congr rfl fun j _ => by ring
    rw [h2]
    field_simp
  have hle : ∑ j, c j * ((B / L) * lam j) ≤ ∑ j, c j * r j :=
    Finset.sum_le_sum hge
  have heq : ∑ j, c j * ((B / L) * lam j) = ∑ j, c j * r j :=
    le_antisymm hle (by rw [hsum]; exact hbudget)
  have hi := (Finset.sum_eq_sum_iff_of_le hge).mp heq i (Finset.mem_univ i)
  have h3 : (B / L) * lam i = r i := mul_left_cancel₀ (ne_of_gt (hc i)) hi
  rw [← h3, rateStar]
  ring

theorem retention_floor_nonvacuous :
    let B : ℝ := 10
    let L : ℝ := 10
    retained (rateStar B L 1) 1 = (1 / 2 : ℝ) ∧
    retained (rateStar B L 9) 9 = (1 / 2 : ℝ) ∧
    rateStar B L 1 + rateStar B L 9 = 10 := by
  norm_num [retained, rateStar]

end Viridis.EntropyLearning.RetentionFloor
