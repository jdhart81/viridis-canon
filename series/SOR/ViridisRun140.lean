import Mathlib

namespace Viridis.Ecoterraforming.StewardshipOptionReserve

def optionValue (p b h s d m : ℝ) : ℝ := (1-p)*h*(1-s^2)-p*b*(1-d)-m

theorem option_value_identity (p b h s d m : ℝ) :
    (d*p*b-(1-p)*h*s^2-m) - (p*b-(1-p)*h) = optionValue p b h s d m := by
  unfold optionValue
  ring

theorem staging_preferred_iff (p b h s d m : ℝ) :
    d*p*b-(1-p)*h*s^2-m ≥ p*b-(1-p)*h ↔ optionValue p b h s d m ≥ 0 := by
  rw [← option_value_identity p b h s d m]
  constructor <;> intro h' <;> linarith

theorem reserve_bound_iff (p b h s d m : ℝ) (hp : 0 ≤ p) (hp1 : p < 1) (hh : 0 < h)
    (hs : 0 ≤ s) (hq0 : 0 ≤ (p*b*(1-d)+m)/((1-p)*h))
    (hq1 : (p*b*(1-d)+m)/((1-p)*h) ≤ 1) :
    optionValue p b h s d m ≥ 0 ↔
      s ≤ Real.sqrt (1-(p*b*(1-d)+m)/((1-p)*h)) := by
  have hph : 0 < (1-p)*h := mul_pos (by linarith) hh
  set q : ℝ := (p*b*(1-d)+m)/((1-p)*h) with hqdef
  have hqe : q * ((1-p)*h) = p*b*(1-d)+m :=
    div_mul_cancel₀ _ (ne_of_gt hph)
  rw [Real.le_sqrt hs (by linarith)]
  unfold optionValue
  constructor
  · intro hv
    have h1 : q ≤ 1 - s^2 := le_of_mul_le_mul_right (by nlinarith) hph
    linarith
  · intro hv
    have h1 : q * ((1-p)*h) ≤ (1 - s^2) * ((1-p)*h) :=
      mul_le_mul_of_nonneg_right (by linarith) (le_of_lt hph)
    nlinarith

theorem option_value_antitone_stage (p b h d m s₁ s₂ : ℝ) (hp : p ≤ 1) (hh : 0 ≤ h)
    (hs1 : 0 ≤ s₁) (hss : s₁ ≤ s₂) :
    optionValue p b h s₂ d m ≤ optionValue p b h s₁ d m := by
  unfold optionValue
  have hph : 0 ≤ (1-p)*h := mul_nonneg (by linarith) hh
  nlinarith [mul_nonneg hph (sub_nonneg.mpr (pow_le_pow_left₀ hs1 hss 2))]

theorem option_value_antitone_cost (p b h s d m₁ m₂ : ℝ) (hm : m₁ ≤ m₂) :
    optionValue p b h s d m₂ ≤ optionValue p b h s d m₁ := by
  unfold optionValue
  linarith

theorem stewardship_option_nonvacuous :
    optionValue (1/4:ℝ) 4 8 (1/4) (9/10) (1/5) > 0 := by
  unfold optionValue
  norm_num

end Viridis.Ecoterraforming.StewardshipOptionReserve
