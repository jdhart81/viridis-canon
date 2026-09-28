import Mathlib

noncomputable section

namespace Viridis.IntelligenceCapacity.FixedOverheadEnergy

def residualEnergy (budget overhead : ℝ) : ℝ :=
  budget - overhead

def processCost (units unitCost overhead : ℝ) : ℝ :=
  overhead + units * unitCost

theorem process_cost_decomposition (units unitCost overhead : ℝ) :
    processCost units unitCost overhead = overhead + units * unitCost := by
  rfl

theorem payload_energy_bound (budget overhead units unitCost : ℝ)
    (hfeasible : processCost units unitCost overhead ≤ budget) :
    units * unitCost ≤ residualEnergy budget overhead := by
  unfold processCost at hfeasible
  unfold residualEnergy
  linarith

theorem capacity_quotient_bound (budget overhead units unitCost : ℝ)
    (hcost : 0 < unitCost)
    (hfeasible : processCost units unitCost overhead ≤ budget) :
    units ≤ residualEnergy budget overhead / unitCost := by
  apply (le_div_iff₀ hcost).2
  exact payload_energy_bound budget overhead units unitCost hfeasible

theorem residual_energy_nonnegative (budget overhead : ℝ)
    (hoverhead : overhead ≤ budget) :
    0 ≤ residualEnergy budget overhead := by
  unfold residualEnergy
  linarith

theorem residual_budget_monotone (budget₁ budget₂ overhead unitCost : ℝ)
    (hbudget : budget₁ ≤ budget₂) (hcost : 0 < unitCost) :
    residualEnergy budget₁ overhead / unitCost ≤
      residualEnergy budget₂ overhead / unitCost := by
  apply (div_le_div_iff_of_pos_right hcost).2
  unfold residualEnergy
  linarith

theorem overhead_composition (budget overhead₁ overhead₂ : ℝ) :
    residualEnergy budget (overhead₁ + overhead₂) =
      residualEnergy (residualEnergy budget overhead₁) overhead₂ := by
  unfold residualEnergy
  ring

theorem fixed_overhead_positive_witness :
    processCost (4 : ℝ) 2 3 = 11 ∧
      residualEnergy 11 3 / 2 = 4 := by
  norm_num [processCost, residualEnergy]

end Viridis.IntelligenceCapacity.FixedOverheadEnergy
