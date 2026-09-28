import Mathlib

namespace Viridis.Ecoterraforming.StewardshipOptionReserve

def optionValue (p b h s d m : ℝ) : ℝ := (1-p)*h*(1-s^2)-p*b*(1-d)-m

theorem option_value_identity (p b h s d m : ℝ) :
    (d*p*b-(1-p)*h*s^2-m) - (p*b-(1-p)*h) = optionValue p b h s d m := by
  sorry

theorem staging_preferred_iff (p b h s d m : ℝ) :
    d*p*b-(1-p)*h*s^2-m ≥ p*b-(1-p)*h ↔ optionValue p b h s d m ≥ 0 := by
  sorry

theorem reserve_bound_iff (p b h s d m : ℝ) (hp : 0 ≤ p) (hp1 : p < 1) (hh : 0 < h)
    (hs : 0 ≤ s) (hq0 : 0 ≤ (p*b*(1-d)+m)/((1-p)*h))
    (hq1 : (p*b*(1-d)+m)/((1-p)*h) ≤ 1) :
    optionValue p b h s d m ≥ 0 ↔
      s ≤ Real.sqrt (1-(p*b*(1-d)+m)/((1-p)*h)) := by
  sorry

theorem option_value_antitone_stage (p b h d m s₁ s₂ : ℝ) (hp : p ≤ 1) (hh : 0 ≤ h)
    (hs1 : 0 ≤ s₁) (hss : s₁ ≤ s₂) :
    optionValue p b h s₂ d m ≤ optionValue p b h s₁ d m := by
  sorry

theorem option_value_antitone_cost (p b h s d m₁ m₂ : ℝ) (hm : m₁ ≤ m₂) :
    optionValue p b h s d m₂ ≤ optionValue p b h s d m₁ := by
  sorry

theorem stewardship_option_nonvacuous :
    optionValue (1/4:ℝ) 4 8 (1/4) (9/10) (1/5) > 0 := by
  sorry

end Viridis.Ecoterraforming.StewardshipOptionReserve
