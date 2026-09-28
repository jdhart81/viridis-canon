import Mathlib

noncomputable section

namespace Viridis.Ecoterraforming.UsefulDissipatedWork

def supplied (w1 w2 : ℝ) : ℝ := w1 + w2
def useful (w1 w2 e1 e2 : ℝ) : ℝ := e1 * w1 + e2 * w2
def modeledDissipation (w1 w2 e1 e2 : ℝ) : ℝ :=
  (1 - e1) * w1 + (1 - e2) * w2

theorem useful_nonnegative (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : 0 ≤ e1) (he2 : 0 ≤ e2) :
    0 ≤ useful w1 w2 e1 e2 := by
  sorry

theorem modeled_dissipation_nonnegative (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : e1 ≤ 1) (he2 : e2 ≤ 1) :
    0 ≤ modeledDissipation w1 w2 e1 e2 := by
  sorry

theorem work_partition (w1 w2 e1 e2 : ℝ) :
    useful w1 w2 e1 e2 + modeledDissipation w1 w2 e1 e2 = supplied w1 w2 := by
  sorry

theorem useful_le_supplied (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : e1 ≤ 1) (he2 : e2 ≤ 1) :
    useful w1 w2 e1 e2 ≤ supplied w1 w2 := by
  sorry

theorem dissipation_le_supplied (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : 0 ≤ e1) (he2 : 0 ≤ e2) :
    modeledDissipation w1 w2 e1 e2 ≤ supplied w1 w2 := by
  sorry

theorem uniform_efficiency_bound (w1 w2 e1 e2 emax : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2)
    (he1 : e1 ≤ emax) (he2 : e2 ≤ emax) :
    useful w1 w2 e1 e2 ≤ emax * supplied w1 w2 := by
  sorry

theorem target_requires_supply (w1 w2 e1 e2 emax T : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2)
    (he1 : e1 ≤ emax) (he2 : e2 ≤ emax) (hmax : 0 < emax)
    (hT : T ≤ useful w1 w2 e1 e2) :
    T / emax ≤ supplied w1 w2 := by
  sorry

theorem partial_partition_witness :
    useful (8 : ℝ) 4 (3 / 4) (1 / 2) = 8 ∧
    modeledDissipation (8 : ℝ) 4 (3 / 4) (1 / 2) = 4 ∧
    supplied (8 : ℝ) 4 = 12 := by
  sorry

theorem target_floor_witness :
    useful (8 : ℝ) 4 (3 / 4) (1 / 2) = 8 ∧
    (8 : ℝ) / (3 / 4) ≤ supplied 8 4 := by
  sorry

end Viridis.Ecoterraforming.UsefulDissipatedWork
