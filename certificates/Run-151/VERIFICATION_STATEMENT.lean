import Mathlib

noncomputable section

namespace Viridis.EntropyLearning.ThermalStepCorridor

def surrogateGain (a q eta : ℝ) : ℝ := a * eta * (2 * q - eta)

def heatCost (d eta : ℝ) : ℝ := d * eta ^ 2

theorem gain_peak_deficit_identity (a q eta : ℝ) :
    surrogateGain a q q - surrogateGain a q eta = a * (eta - q) ^ 2 := by
  sorry

theorem gain_nonnegative_corridor (a q eta : ℝ)
    (ha : 0 ≤ a) (heta0 : 0 ≤ eta) (heta2 : eta ≤ 2 * q) :
    0 ≤ surrogateGain a q eta := by
  sorry

theorem gain_peak_upper_bound (a q eta : ℝ) (ha : 0 ≤ a) :
    surrogateGain a q eta ≤ surrogateGain a q q := by
  sorry

theorem gain_symmetric_mistuning (a q delta : ℝ) :
    surrogateGain a q (q - delta) = surrogateGain a q (q + delta) := by
  sorry

theorem heat_quadratic_scaling (d eta k : ℝ) :
    heatCost d (k * eta) = k ^ 2 * heatCost d eta := by
  sorry

theorem thermal_corridor_positive_witness :
    surrogateGain 2 3 3 = 18 ∧ heatCost 1 3 = 9 ∧
      (0 : ℝ) < surrogateGain 2 3 3 := by
  sorry

theorem thermal_corridor_overshoot_witness :
    surrogateGain 1 2 5 = -5 ∧ heatCost 1 5 = 25 ∧
      surrogateGain 1 2 5 < 0 := by
  sorry

end Viridis.EntropyLearning.ThermalStepCorridor
