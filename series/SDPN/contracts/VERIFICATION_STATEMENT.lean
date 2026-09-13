import Mathlib

noncomputable section

namespace Viridis.ThermodynamicEconomics.SwitchingDissipationPayback

def switchingCharge (capital transition : ℝ) : ℝ := capital + transition

def switchingGain (horizon saving capital transition : ℝ) : ℝ :=
  horizon * saving - switchingCharge capital transition

theorem switching_gain_identity
    (horizon saving capital transition : ℝ) :
    switchingGain horizon saving capital transition =
      horizon * saving - capital - transition := by
  sorry

theorem break_even_iff
    (horizon saving capital transition : ℝ) :
    0 ≤ switchingGain horizon saving capital transition ↔
      switchingCharge capital transition ≤ horizon * saving := by
  sorry

theorem transition_charge_reduces_gain
    (horizon saving capital transitionLow transitionHigh : ℝ)
    (htransition : transitionLow ≤ transitionHigh) :
    switchingGain horizon saving capital transitionHigh ≤
      switchingGain horizon saving capital transitionLow := by
  sorry

theorem longer_horizon_not_worse
    (horizonShort horizonLong saving capital transition : ℝ)
    (hhorizon : horizonShort ≤ horizonLong) (hsaving : 0 ≤ saving) :
    switchingGain horizonShort saving capital transition ≤
      switchingGain horizonLong saving capital transition := by
  sorry

theorem payback_boundary_zero_gain
    (horizon saving capital transition : ℝ)
    (hboundary : horizon * saving = switchingCharge capital transition) :
    switchingGain horizon saving capital transition = 0 := by
  sorry

theorem no_churn_band
    (horizon advantage capital transition : ℝ)
    (hlower : -switchingCharge capital transition ≤ horizon * advantage)
    (hupper : horizon * advantage ≤ switchingCharge capital transition) :
    switchingGain horizon advantage capital transition ≤ 0 ∧
      switchingGain horizon (-advantage) capital transition ≤ 0 := by
  sorry

theorem forward_switch_profitable_outside_band
    (horizon advantage capital transition : ℝ)
    (houtside : switchingCharge capital transition < horizon * advantage) :
    0 < switchingGain horizon advantage capital transition := by
  sorry

theorem backward_switch_profitable_outside_band
    (horizon advantage capital transition : ℝ)
    (houtside : horizon * advantage < -switchingCharge capital transition) :
    0 < switchingGain horizon (-advantage) capital transition := by
  sorry

theorem round_trip_net_loss
    (horizon advantage capital transition : ℝ) :
    switchingGain horizon advantage capital transition +
        switchingGain horizon (-advantage) capital transition =
      -2 * switchingCharge capital transition := by
  sorry

theorem switching_payback_positive_witness :
    switchingGain 5 4 7 3 = 10 := by
  sorry

theorem omitting_transition_overstates_gain
    (horizon saving capital transition : ℝ) (htransition : 0 ≤ transition) :
    switchingGain horizon saving capital transition ≤
      switchingGain horizon saving capital 0 := by
  sorry

end Viridis.ThermodynamicEconomics.SwitchingDissipationPayback
