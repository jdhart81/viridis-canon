import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

set_option autoImplicit false

namespace Viridis.CarbonContinuity

/-- Living-pool value after one standardized disturbance-recovery cycle. -/
def stepLiving (a r L D : ℝ) : ℝ := a * L + r * D

/-- Durable-pool value after one standardized disturbance-recovery cycle. -/
def stepDurable (d p L D : ℝ) : ℝ := p * L + d * D

/-- If regenerative loop gain offsets the two leakage terms, the explicit
portfolio `(L,D) = (r,1-a)` is positive and componentwise nondecreasing. -/
theorem carbon_continuity_threshold_sufficient
    (a d r p : ℝ)
    (ha0 : 0 ≤ a) (ha1 : a < 1)
    (hd0 : 0 ≤ d) (hd1 : d < 1)
    (hr : 0 < r) (hp : 0 < p)
    (hthreshold : (1 - a) * (1 - d) ≤ r * p) :
    ∃ L D : ℝ,
      0 < L ∧ 0 < D ∧
      L ≤ stepLiving a r L D ∧
      D ≤ stepDurable d p L D := by
  refine ⟨r, 1 - a, hr, by linarith, ?_, ?_⟩
  · simp only [stepLiving]; exact le_of_eq (by ring)
  · simp only [stepDurable]; nlinarith [hthreshold]

/-- Any strictly positive componentwise nondecreasing portfolio forces the
regenerative loop gain to offset the product of the two leakage terms. -/
theorem carbon_continuity_threshold_necessary
    (a d r p L D : ℝ)
    (ha0 : 0 ≤ a) (ha1 : a < 1)
    (hd0 : 0 ≤ d) (hd1 : d < 1)
    (hr : 0 < r) (hp : 0 < p)
    (hL : 0 < L) (hD : 0 < D)
    (hliving : L ≤ stepLiving a r L D)
    (hdurable : D ≤ stepDurable d p L D) :
    (1 - a) * (1 - d) ≤ r * p := by
  simp only [stepLiving] at hliving
  simp only [stepDurable] at hdurable
  have h1 : (1 - a) * L ≤ r * D := by linarith
  have h2 : (1 - d) * D ≤ p * L := by linarith
  have hLD : 0 < L * D := mul_pos hL hD
  have h3 : ((1 - a) * L) * ((1 - d) * D) ≤ (r * D) * (p * L) :=
    mul_le_mul h1 h2 (by nlinarith) (by nlinarith)
  have h4 : ((1 - a) * (1 - d)) * (L * D) ≤ (r * p) * (L * D) := by nlinarith
  exact le_of_mul_le_mul_right h4 hLD

/-- A strictly positive cycle-nondecreasing portfolio exists exactly at or
above the regenerative coupling threshold. -/
theorem carbon_continuity_threshold_iff
    (a d r p : ℝ)
    (ha0 : 0 ≤ a) (ha1 : a < 1)
    (hd0 : 0 ≤ d) (hd1 : d < 1)
    (hr : 0 < r) (hp : 0 < p) :
    (∃ L D : ℝ,
      0 < L ∧ 0 < D ∧
      L ≤ stepLiving a r L D ∧
      D ≤ stepDurable d p L D) ↔
    (1 - a) * (1 - d) ≤ r * p := by
  constructor
  · rintro ⟨L, D, hL, hD, hliving, hdurable⟩
    exact carbon_continuity_threshold_necessary a d r p L D ha0 ha1 hd0 hd1 hr hp hL hD
      hliving hdurable
  · intro hthreshold
    exact carbon_continuity_threshold_sufficient a d r p ha0 ha1 hd0 hd1 hr hp hthreshold

/-- At exact threshold equality, `(r,1-a)` is a positive stationary
portfolio. -/
theorem carbon_continuity_boundary_stationary
    (a d r p : ℝ)
    (ha1 : a < 1) (hr : 0 < r)
    (hboundary : (1 - a) * (1 - d) = r * p) :
    0 < r ∧ 0 < (1 - a) ∧
    stepLiving a r r (1 - a) = r ∧
    stepDurable d p r (1 - a) = (1 - a) := by
  refine ⟨hr, by linarith, ?_, ?_⟩
  · simp only [stepLiving]; ring
  · simp only [stepDurable]; nlinarith [hboundary]

/-- Strictly above the threshold, the explicit witness holds living carbon
exactly while its durable component grows strictly. -/
theorem carbon_continuity_strict_threshold_growth
    (a d r p : ℝ)
    (ha1 : a < 1) (hr : 0 < r)
    (hstrict : (1 - a) * (1 - d) < r * p) :
    stepLiving a r r (1 - a) = r ∧
    (1 - a) < stepDurable d p r (1 - a) := by
  refine ⟨?_, ?_⟩
  · simp only [stepLiving]; ring
  · simp only [stepDurable]; nlinarith [hstrict]

/-- Concrete strict-threshold witness:
`(a,d,r,p) = (3/5,4/5,1/2,1/5)` and `(L,D) = (1/2,2/5)`. -/
theorem carbon_continuity_nonvacuous :
    let a : ℝ := 3 / 5
    let d : ℝ := 4 / 5
    let r : ℝ := 1 / 2
    let p : ℝ := 1 / 5
    let L : ℝ := 1 / 2
    let D : ℝ := 2 / 5
    0 ≤ a ∧ a < 1 ∧ 0 ≤ d ∧ d < 1 ∧
    0 < r ∧ 0 < p ∧ 0 < L ∧ 0 < D ∧
    (1 - a) * (1 - d) < r * p ∧
    stepLiving a r L D = L ∧
    D < stepDurable d p L D := by
  intro a d r p L D
  refine ⟨by norm_num [a], by norm_num [a], by norm_num [d], by norm_num [d],
    by norm_num [r], by norm_num [p], by norm_num [L], by norm_num [D], ?_, ?_, ?_⟩
  · norm_num [a, d, r, p]
  · norm_num [stepLiving, a, r, L, D]
  · norm_num [stepDurable, d, p, L, D]

end Viridis.CarbonContinuity
