import Mathlib

/-!
# Run 131 cognitive switching hysteresis certificate

Statement contract `VRS-FORMAL-TARGET-CONTRACT-1` (run 131).  Every definition and
theorem statement below is preserved verbatim from the frozen contract; only the
proof bodies have been supplied.
-/

namespace Viridis.Cognition.CognitiveSwitchingHysteresis

noncomputable def hDown (bias cPlusToMinus : ℝ) : ℝ := -bias - cPlusToMinus / 2

noncomputable def hUp (bias cMinusToPlus : ℝ) : ℝ := -bias + cMinusToPlus / 2

noncomputable def bandWidth (bias cPlusToMinus cMinusToPlus : ℝ) : ℝ :=
  hUp bias cMinusToPlus - hDown bias cPlusToMinus

noncomputable def signedLoopIntegral (bias cPlusToMinus cMinusToPlus : ℝ) : ℝ :=
  2 * hDown bias cPlusToMinus - 2 * hUp bias cMinusToPlus

theorem threshold_order
    (bias cPlusToMinus cMinusToPlus : ℝ)
    (hpm : 0 ≤ cPlusToMinus) (hmp : 0 ≤ cMinusToPlus) :
    hDown bias cPlusToMinus ≤ hUp bias cMinusToPlus := by
  unfold hDown hUp
  linarith

theorem band_width_identity
    (bias cPlusToMinus cMinusToPlus : ℝ) :
    bandWidth bias cPlusToMinus cMinusToPlus =
      (cPlusToMinus + cMinusToPlus) / 2 := by
  unfold bandWidth hDown hUp
  ring

theorem closed_loop_area_identity
    (bias cPlusToMinus cMinusToPlus : ℝ)
    (hpm : 0 ≤ cPlusToMinus) (hmp : 0 ≤ cMinusToPlus) :
    |signedLoopIntegral bias cPlusToMinus cMinusToPlus| =
      cPlusToMinus + cMinusToPlus := by
  have hval : signedLoopIntegral bias cPlusToMinus cMinusToPlus
      = -(cPlusToMinus + cMinusToPlus) := by
    unfold signedLoopIntegral hDown hUp
    ring
  rw [hval, abs_neg, abs_of_nonneg (by linarith)]

theorem bias_translation
    (bias delta cPlusToMinus cMinusToPlus : ℝ) :
    hDown (bias + delta) cPlusToMinus = hDown bias cPlusToMinus - delta ∧
    hUp (bias + delta) cMinusToPlus = hUp bias cMinusToPlus - delta := by
  unfold hDown hUp
  constructor <;> ring

theorem directional_cost_recovery
    (bias cPlusToMinus cMinusToPlus : ℝ) :
    -2 * (hDown bias cPlusToMinus + bias) = cPlusToMinus ∧
    2 * (hUp bias cMinusToPlus + bias) = cMinusToPlus := by
  unfold hDown hUp
  constructor <;> ring

theorem cshc_nonvacuous :
    hDown 0 2 = -1 ∧ hUp 0 2 = 1 ∧
    bandWidth 0 2 2 = 2 ∧
    |signedLoopIntegral 0 2 2| = 4 := by
  refine ⟨by unfold hDown; norm_num, by unfold hUp; norm_num,
    by unfold bandWidth hDown hUp; norm_num, ?_⟩
  have hval : signedLoopIntegral 0 2 2 = -4 := by
    unfold signedLoopIntegral hDown hUp; norm_num
  rw [hval]
  norm_num

end Viridis.Cognition.CognitiveSwitchingHysteresis
