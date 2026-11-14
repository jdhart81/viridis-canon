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
  unfold useful
  positivity

theorem modeled_dissipation_nonnegative (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : e1 ≤ 1) (he2 : e2 ≤ 1) :
    0 ≤ modeledDissipation w1 w2 e1 e2 := by
  unfold modeledDissipation
  exact add_nonneg (mul_nonneg (sub_nonneg.mpr he1) hw1)
    (mul_nonneg (sub_nonneg.mpr he2) hw2)

theorem work_partition (w1 w2 e1 e2 : ℝ) :
    useful w1 w2 e1 e2 + modeledDissipation w1 w2 e1 e2 = supplied w1 w2 := by
  unfold useful modeledDissipation supplied
  ring

theorem useful_le_supplied (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : e1 ≤ 1) (he2 : e2 ≤ 1) :
    useful w1 w2 e1 e2 ≤ supplied w1 w2 := by
  have hd := modeled_dissipation_nonnegative w1 w2 e1 e2 hw1 hw2 he1 he2
  have hp := work_partition w1 w2 e1 e2
  linarith

theorem dissipation_le_supplied (w1 w2 e1 e2 : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2) (he1 : 0 ≤ e1) (he2 : 0 ≤ e2) :
    modeledDissipation w1 w2 e1 e2 ≤ supplied w1 w2 := by
  have hu := useful_nonnegative w1 w2 e1 e2 hw1 hw2 he1 he2
  have hp := work_partition w1 w2 e1 e2
  linarith

theorem uniform_efficiency_bound (w1 w2 e1 e2 emax : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2)
    (he1 : e1 ≤ emax) (he2 : e2 ≤ emax) :
    useful w1 w2 e1 e2 ≤ emax * supplied w1 w2 := by
  have hgap1 : 0 ≤ (emax - e1) * w1 := mul_nonneg (sub_nonneg.mpr he1) hw1
  have hgap2 : 0 ≤ (emax - e2) * w2 := mul_nonneg (sub_nonneg.mpr he2) hw2
  unfold useful supplied
  nlinarith

theorem target_requires_supply (w1 w2 e1 e2 emax T : ℝ)
    (hw1 : 0 ≤ w1) (hw2 : 0 ≤ w2)
    (he1 : e1 ≤ emax) (he2 : e2 ≤ emax) (hmax : 0 < emax)
    (hT : T ≤ useful w1 w2 e1 e2) :
    T / emax ≤ supplied w1 w2 := by
  have hu := uniform_efficiency_bound w1 w2 e1 e2 emax hw1 hw2 he1 he2
  have hmul : T ≤ emax * supplied w1 w2 := le_trans hT hu
  apply (div_le_iff₀ hmax).2
  simpa [mul_comm] using hmul

theorem partial_partition_witness :
    useful (8 : ℝ) 4 (3 / 4) (1 / 2) = 8 ∧
    modeledDissipation (8 : ℝ) 4 (3 / 4) (1 / 2) = 4 ∧
    supplied (8 : ℝ) 4 = 12 := by
  norm_num [useful, modeledDissipation, supplied]

theorem target_floor_witness :
    useful (8 : ℝ) 4 (3 / 4) (1 / 2) = 8 ∧
    (8 : ℝ) / (3 / 4) ≤ supplied 8 4 := by
  norm_num [useful, supplied]

end Viridis.Ecoterraforming.UsefulDissipatedWork
