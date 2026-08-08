import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace Viridis.EcopoieticHedge

noncomputable section

/-- Establishment exponent in the first reciprocal environment. -/
def regimeA (alpha beta dose x : ℝ) : ℝ :=
  alpha * x + beta * (dose - x)

/-- Establishment exponent in the reciprocal environment. -/
def regimeB (alpha beta dose x : ℝ) : ℝ :=
  beta * x + alpha * (dose - x)

/-- Worst-case establishment exponent across the two environments. -/
def robustExponent (alpha beta dose x : ℝ) : ℝ :=
  min (regimeA alpha beta dose x) (regimeB alpha beta dose x)

/-- Log-survival target corresponding to establishment probability `p`. -/
def targetLog (p : ℝ) : ℝ :=
  -Real.log (1 - p)

/-- Total mixed dose needed at the reciprocal equal split. -/
def mixedTargetDose (alpha beta p : ℝ) : ℝ :=
  2 * targetLog p / (alpha + beta)

/-- Total monoculture dose needed under the weak coefficient. -/
def monocultureTargetDose (beta p : ℝ) : ℝ :=
  targetLog p / beta

/-- In the reciprocal two-regime model, the unique maximin allocation is the
equal split. -/
theorem reciprocal_two_regime_maximin_equal_split
    (alpha beta dose x : ℝ)
    (h_alpha_beta : beta < alpha)
    (h_beta : 0 < beta)
    (h_dose : 0 < dose)
    (h_x_nonneg : 0 ≤ x)
    (h_x_le_dose : x ≤ dose) :
    robustExponent alpha beta dose x ≤
        robustExponent alpha beta dose (dose / 2) ∧
      (robustExponent alpha beta dose x =
          robustExponent alpha beta dose (dose / 2) ↔ x = dose / 2) := by
  have hgap : 0 < alpha - beta := by linarith
  have hmid :
      regimeA alpha beta dose (dose / 2) =
        regimeB alpha beta dose (dose / 2) := by
    simp only [regimeA, regimeB]
    ring
  simp only [robustExponent]
  rw [min_eq_left (le_of_eq hmid)]
  by_cases hleft : regimeA alpha beta dose x ≤ regimeB alpha beta dose x
  · rw [min_eq_left hleft]
    have hxhalf : x ≤ dose / 2 := by
      by_contra hnot
      have hfactor : (alpha - beta) * (dose - 2 * x) < 0 := by
        exact mul_neg_of_pos_of_neg hgap (by linarith)
      have hnonneg : 0 ≤ (alpha - beta) * (dose - 2 * x) := by
        calc
          0 ≤ regimeB alpha beta dose x - regimeA alpha beta dose x := sub_nonneg.mpr hleft
          _ = (alpha - beta) * (dose - 2 * x) := by
            simp only [regimeA, regimeB]
            ring
      linarith
    have hmono :
        regimeA alpha beta dose x ≤ regimeA alpha beta dose (dose / 2) := by
      have hproduct : 0 ≤ (alpha - beta) * (dose / 2 - x) :=
        mul_nonneg hgap.le (sub_nonneg.mpr hxhalf)
      calc
        regimeA alpha beta dose x ≤
            regimeA alpha beta dose x + (alpha - beta) * (dose / 2 - x) := by
          linarith
        _ = regimeA alpha beta dose (dose / 2) := by
          simp only [regimeA]
          ring
    constructor
    · exact hmono
    · constructor
      · intro heq
        have hproduct : (alpha - beta) * (x - dose / 2) = 0 := by
          calc
            (alpha - beta) * (x - dose / 2) =
                regimeA alpha beta dose x -
                  regimeA alpha beta dose (dose / 2) := by
              simp only [regimeA]
              ring
            _ = 0 := by rw [heq]; ring
        rcases mul_eq_zero.mp hproduct with hzero | hzero
        · exact False.elim (ne_of_gt hgap hzero)
        · linarith
      · intro heq
        rw [heq]
  · have hright : regimeB alpha beta dose x ≤ regimeA alpha beta dose x :=
      le_of_not_ge hleft
    rw [min_eq_right hright]
    have hxhalf : dose / 2 ≤ x := by
      by_contra hnot
      have hfactor : (alpha - beta) * (2 * x - dose) < 0 := by
        exact mul_neg_of_pos_of_neg hgap (by linarith)
      have hnonneg : 0 ≤ (alpha - beta) * (2 * x - dose) := by
        calc
          0 ≤ regimeA alpha beta dose x - regimeB alpha beta dose x := sub_nonneg.mpr hright
          _ = (alpha - beta) * (2 * x - dose) := by
            simp only [regimeA, regimeB]
            ring
      linarith
    have hmono :
        regimeB alpha beta dose x ≤ regimeB alpha beta dose (dose / 2) := by
      have hproduct : 0 ≤ (alpha - beta) * (x - dose / 2) :=
        mul_nonneg hgap.le (sub_nonneg.mpr hxhalf)
      calc
        regimeB alpha beta dose x ≤
            regimeB alpha beta dose x + (alpha - beta) * (x - dose / 2) := by
          linarith
        _ = regimeB alpha beta dose (dose / 2) := by
          simp only [regimeB]
          ring
    constructor
    · simpa [hmid] using hmono
    · constructor
      · intro heq
        have hproduct : (alpha - beta) * (x - dose / 2) = 0 := by
          calc
            (alpha - beta) * (x - dose / 2) =
                regimeB alpha beta dose (dose / 2) -
                  regimeB alpha beta dose x := by
              simp only [regimeB]
              ring
            _ = 0 := by rw [← hmid, heq]; ring
        rcases mul_eq_zero.mp hproduct with hzero | hzero
        · exact False.elim (ne_of_gt hgap hzero)
        · linarith
      · intro heq
        rw [heq, hmid]

/-- The equal split's worst-case exponent exceeds either monoculture's
worst-case exponent by exactly `(alpha - beta) * dose / 2`. -/
theorem reciprocal_diversification_gain
    (alpha beta dose : ℝ)
    (h_alpha_beta : beta < alpha)
    (h_beta : 0 < beta)
    (h_dose : 0 < dose) :
    robustExponent alpha beta dose (dose / 2) -
        robustExponent alpha beta dose 0 =
      (alpha - beta) * dose / 2 := by
  have hmid :
      regimeA alpha beta dose (dose / 2) =
        regimeB alpha beta dose (dose / 2) := by
    simp only [regimeA, regimeB]
    ring
  have hzero : regimeA alpha beta dose 0 ≤ regimeB alpha beta dose 0 := by
    simp only [regimeA, regimeB]
    have hproduct : beta * dose ≤ alpha * dose :=
      mul_le_mul_of_nonneg_right h_alpha_beta.le h_dose.le
    linarith
  rw [robustExponent, min_eq_left (le_of_eq hmid)]
  rw [robustExponent, min_eq_left hzero]
  simp only [regimeA]
  ring

/-- At a fixed target establishment probability, the fractional dose saving
from the reciprocal equal split is `(alpha - beta) / (alpha + beta)`. -/
theorem target_probability_dose_saving
    (alpha beta p : ℝ)
    (h_alpha_beta : beta < alpha)
    (h_beta : 0 < beta)
    (h_p_pos : 0 < p)
    (h_p_lt_one : p < 1) :
    1 - mixedTargetDose alpha beta p / monocultureTargetDose beta p =
      (alpha - beta) / (alpha + beta) := by
  have hsum : alpha + beta ≠ 0 := by linarith
  have hlog : targetLog p ≠ 0 := by
    have harg_pos : 0 < 1 - p := by linarith
    have harg_lt_one : 1 - p < 1 := by linarith
    have hnegative : Real.log (1 - p) < 0 := Real.log_neg harg_pos harg_lt_one
    simp only [targetLog]
    linarith
  simp only [mixedTargetDose, monocultureTargetDose]
  field_simp [hsum, h_beta.ne', hlog]
  ring

/-- If strain A weakly dominates strain B in every scenario, then allocating
the entire feasible dose to A weakly improves every scenario. This pointwise
dominance is the sufficient maximin certificate. -/
theorem uniform_dominance_implies_monoculture_optimal
    {Scenario : Type*}
    (a b : Scenario → ℝ)
    (dose x : ℝ)
    (h_x_nonneg : 0 ≤ x)
    (h_x_le_dose : x ≤ dose)
    (h_dominance : ∀ s, b s ≤ a s) :
    ∀ s, a s * x + b s * (dose - x) ≤ a s * dose := by
  intro s
  have hremaining : 0 ≤ dose - x := sub_nonneg.mpr h_x_le_dose
  have hscaled : b s * (dose - x) ≤ a s * (dose - x) :=
    mul_le_mul_of_nonneg_right (h_dominance s) hremaining
  linarith

/-- When the two strains have identical coefficients in every scenario, the
scenario-value function is allocation-independent, so diversification gain is
zero. -/
theorem identical_strains_zero_diversification_gain
    {Scenario : Type*}
    (coefficient : Scenario → ℝ)
    (dose x : ℝ) :
    (fun s => coefficient s * x + coefficient s * (dose - x)) =
      fun s => coefficient s * dose := by
  funext s
  ring

/-- Concrete witness that the reciprocal-hedge assumptions are satisfiable and
the mixed allocation strictly improves the worst-case exponent. -/
theorem ecopoietic_hedge_nonvacuous :
    robustExponent 2 1 2 (2 / 2) = 3 ∧
      robustExponent 2 1 2 0 = 2 := by
  norm_num [robustExponent, regimeA, regimeB]

end

end Viridis.EcopoieticHedge
