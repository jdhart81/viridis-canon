/-
Copyright (c) 2026 Justin Hart. Released under Apache 2.0.
Exact algebra for information-weighted stewardship. Local research candidate;
not a physical validation, novelty certificate, or full trajectory theorem.
-/
import StewardshipSetpoint

namespace Viridis.InformationWeightedStewardship
open Viridis.Stewardship.StewardshipSetpoint

noncomputable def stockStar (a K r : ℝ) : ℝ := K * (2*a-r)/(3*a)
noncomputable def W (K D : ℝ) : ℝ := D^2/(2*K)
noncomputable def F (a K r D : ℝ) : ℝ := D/K * g a K D - r * W K D
noncomputable def heldRate (a K phi D : ℝ) : ℝ := g a K D / phi
noncomputable def duty (a phi Omega r : ℝ) : ℝ := (a+r)/(3*phi*Omega)
noncomputable def stationaryValue (a K phi r : ℝ) : ℝ :=
  stockStar a K r / K * heldRate a K phi (stockStar a K r) / r

 theorem factorization (a K r D : ℝ) (ha : a ≠ 0) (hK : K ≠ 0) :
    F a K r (stockStar a K r) - F a K r D =
      a/(2*K^2) * (D-stockStar a K r)^2 * (2*D+stockStar a K r) := by
  unfold F W stockStar g
  field_simp
  <;> ring

 theorem stockStar_pos (a K r : ℝ) (ha : 0 < a) (hK : 0 < K) (hr : r < 2*a) :
    0 < stockStar a K r := by
  unfold stockStar
  exact div_pos (mul_pos hK (by linarith)) (by positivity)

 theorem stockStar_lt_capacity (a K r : ℝ) (ha : 0 < a) (hK : 0 < K) (hr : 0 < r) :
    stockStar a K r < K := by
  unfold stockStar
  apply (div_lt_iff₀ (by positivity : 0 < 3*a)).2
  nlinarith [mul_pos hK (show 0 < a+r by positivity)]

 theorem potential_gap_nonneg (a K r D : ℝ) (ha : 0 < a) (hK : 0 < K)
    (hr : r < 2*a) (hD : 0 ≤ D) : 0 ≤ F a K r (stockStar a K r)-F a K r D := by
  rw [factorization a K r D ha.ne' hK.ne']
  have hs := stockStar_pos a K r ha hK hr
  positivity

 theorem potential_gap_eq_zero_iff (a K r D : ℝ) (ha : 0 < a) (hK : 0 < K)
    (hr : r < 2*a) (hD : 0 ≤ D) :
    F a K r (stockStar a K r)-F a K r D = 0 ↔ D = stockStar a K r := by
  rw [factorization a K r D ha.ne' hK.ne']
  have hc : a/(2*K^2) ≠ 0 := ne_of_gt (by positivity)
  have hp : 2*D+stockStar a K r ≠ 0 := ne_of_gt (by
    have := stockStar_pos a K r ha hK hr
    linarith)
  simp [mul_eq_zero, hc, hp, sub_eq_zero]

 theorem held_rate_balance (a K phi D : ℝ) (hp : phi ≠ 0) :
    g a K D - phi * heldRate a K phi D = 0 := by
  unfold heldRate
  field_simp
  <;> ring

 theorem held_rate_at_star (a K phi r : ℝ) (ha : a ≠ 0) (hK : K ≠ 0)
    (hp : phi ≠ 0) :
    heldRate a K phi (stockStar a K r) = stockStar a K r * (a+r)/(3*phi) := by
  unfold heldRate stockStar g
  field_simp
  <;> ring

 theorem held_rate_feasible (a K phi Omega r : ℝ) (ha : 0<a) (hK : 0<K)
    (hp : 0<phi) (hr : 0<r) (hr2 : r<2*a) (hcap : (a+r)/(3*phi) ≤ Omega) :
    0 ≤ heldRate a K phi (stockStar a K r) ∧
    heldRate a K phi (stockStar a K r) ≤ Omega*stockStar a K r := by
  rw [held_rate_at_star a K phi r ha.ne' hK.ne' hp.ne', mul_div_assoc]
  have hs := stockStar_pos a K r ha hK hr2
  constructor
  · positivity
  · simpa [mul_comm] using mul_le_mul_of_nonneg_left hcap hs.le

 theorem duty_feasible (a phi Omega r : ℝ) (ha : 0<a) (hp : 0<phi)
    (hO : 0<Omega) (hr : 0<r) (hcap : (a+r)/(3*phi) ≤ Omega) :
    0 < duty a phi Omega r ∧ duty a phi Omega r ≤ 1 := by
  unfold duty
  constructor
  · positivity
  · apply (div_le_one (by positivity : 0<3*phi*Omega)).2
    have := (div_le_iff₀ (by positivity : 0<3*phi)).1 hcap
    nlinarith

 theorem stationary_value_accounting (a K phi r : ℝ) (hp : phi ≠ 0) (hr : r ≠ 0) :
    stationaryValue a K phi r =
      W K (stockStar a K r)/phi + F a K r (stockStar a K r)/(phi*r) := by
  unfold stationaryValue heldRate F
  field_simp
  <;> ring

/-- Constant-quality counterpart, reusing the historical setpoint and growth. -/
 theorem raw_gap (a K r D : ℝ) (ha : a ≠ 0) (hK : K ≠ 0) :
    Phi a K r (Dstar a K r) - Phi a K r D = a/K*(D-Dstar a K r)^2 := by
  unfold Phi Dstar g
  field_simp
  <;> ring

 theorem raw_held_rate (a K phi r : ℝ) (ha : a ≠ 0) (hK : K ≠ 0) (hp : phi ≠ 0) :
    heldRate a K phi (Dstar a K r) = Dstar a K r * (a+r)/(2*phi) := by
  unfold heldRate Dstar g
  field_simp
  <;> ring

 theorem explicit_nonvacuity :
    stockStar (1/2) 1 (1/10) = 3/5 ∧
    heldRate (1/2) 1 1 (3/5) = 3/25 ∧
    duty (1/2) 1 1 (1/10) = 1/5 ∧
    stationaryValue (1/2) 1 1 (1/10) = 18/25 := by
  norm_num [stockStar, heldRate, duty, stationaryValue, g]

end Viridis.InformationWeightedStewardship
