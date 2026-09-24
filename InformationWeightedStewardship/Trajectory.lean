import InformationWeightedStewardship.Algebra
import Mathlib.MeasureTheory.Integral.IntervalIntegral.AbsolutelyContinuousFun
import Mathlib.Analysis.SpecialFunctions.ImproperIntegrals

namespace Viridis.InformationWeightedStewardship
open MeasureTheory Set Filter
open scoped Topology
open Viridis.Stewardship.StewardshipSetpoint

/-- Functions on R represent their restrictions to nonnegative times. No accounting,
regret, optimality, or stationary conclusion is assumed. -/
structure Admissible (a K phi Omega : ℝ) (D H : ℝ → ℝ) : Prop where
  ac : ∀ T, 0 ≤ T → AbsolutelyContinuousOnInterval D 0 T
  measurable_control : Measurable H
  bounds : ∀ t, 0 ≤ t → 0 ≤ D t ∧ D t ≤ K
  control : ∀ᵐ t, 0 ≤ t → 0 ≤ H t ∧ H t ≤ Omega * D t
  ode : ∀ᵐ t, 0 ≤ t → HasDerivAt D (g a K (D t) - phi * H t) t

noncomputable def objective (K r : ℝ) (D H : ℝ → ℝ) : ℝ :=
  ∫ t in Ioi (0 : ℝ), Real.exp (-r*t) * (D t/K) * H t

 theorem stationary_admissible (a K phi Omega r : ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hr : 0<r) (hr2 : r<2*a)
    (hcap : (a+r)/(3*phi) ≤ Omega) :
    Admissible a K phi Omega (fun _ => stockStar a K r)
      (fun _ => heldRate a K phi (stockStar a K r)) := by
  constructor
  · intro T _
    exact (LipschitzWith.const (stockStar a K r)).lipschitzOnWith.absolutelyContinuousOnInterval
  · exact measurable_const
  · intro t _
    exact ⟨(stockStar_pos a K r ha hK hr2).le,
      (stockStar_lt_capacity a K r ha hK hr).le⟩
  · exact Filter.Eventually.of_forall (fun _ _ => held_rate_feasible a K phi Omega r ha hK hp hr hr2 hcap)
  · apply Filter.Eventually.of_forall
    intro t _
    rw [held_rate_balance a K phi _ hp.ne']
    exact hasDerivAt_const t _

 theorem discount_derivative (r t : ℝ) :
    HasDerivAt (fun x : ℝ => Real.exp (-r*x)) (-r*Real.exp (-r*t)) t := by
  simpa [mul_comm] using ((hasDerivAt_id t).const_mul (-r)).exp

 theorem discount_ac (r T : ℝ) (hr : 0<r) (hT : 0≤T) :
    AbsolutelyContinuousOnInterval (fun t : ℝ => Real.exp (-r*t)) 0 T := by
  apply LipschitzOnWith.absolutelyContinuousOnInterval (K := ⟨r,hr.le⟩)
  apply (convex_uIcc (0:ℝ) T).lipschitzOnWith_of_nnnorm_hasDerivWithin_le
    (fun t _ => (discount_derivative r t).hasDerivWithinAt)
  intro t ht
  have ht0 : 0≤t := (show t ∈ Icc 0 T by simpa [uIcc_of_le hT] using ht).1
  change ‖-r * Real.exp (-r*t)‖ ≤ r
  rw [norm_mul, Real.norm_eq_abs, abs_neg, abs_of_pos hr,
      Real.norm_eq_abs, abs_of_pos (Real.exp_pos _)]
  exact mul_le_of_le_one_right hr.le (Real.exp_le_one_iff.mpr (by nlinarith))

 theorem primitive_ac {D : ℝ → ℝ} {T : ℝ} (K : ℝ)
    (hD : AbsolutelyContinuousOnInterval D 0 T) :
    AbsolutelyContinuousOnInterval (fun t => W K (D t)) 0 T := by
  simpa [W, pow_two, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
    (hD.fun_mul hD).const_mul ((2*K)⁻¹)

 theorem discounted_primitive_derivative (a K phi r : ℝ) (D H : ℝ → ℝ)
    (hK : K ≠ 0) {t : ℝ} (hd : HasDerivAt D (g a K (D t)-phi*H t) t) :
    HasDerivAt (fun x => Real.exp (-r*x)*W K (D x))
      (Real.exp (-r*t)*F a K r (D t) - phi*(Real.exp (-r*t)*(D t/K)*H t)) t := by
  have hw := (hd.pow 2).div_const (2*K)
  convert (discount_derivative r t).mul hw using 1
  unfold F W
  norm_num [Pi.pow_apply]
  field_simp
  <;> ring

 theorem finite_accounting (a K phi Omega r T : ℝ) (D H : ℝ → ℝ)
    (hK : 0<K) (hp : 0<phi) (hr : 0<r) (hT : 0≤T)
    (h : Admissible a K phi Omega D H) :
    (∫ t in (0:ℝ)..T, Real.exp (-r*t)*(D t/K)*H t) =
      W K (D 0)/phi - Real.exp (-r*T)*W K (D T)/phi +
      (∫ t in (0:ℝ)..T, Real.exp (-r*t)*F a K r (D t))/phi := by
  let B := fun t => Real.exp (-r*t)*W K (D t)
  let A := fun t => Real.exp (-r*t)*F a K r (D t)
  let L := fun t => Real.exp (-r*t)*(D t/K)*H t
  have hb : AbsolutelyContinuousOnInterval B 0 T :=
    (discount_ac r T hr hT).fun_mul (primitive_ac K (h.ac T hT))
  have hc := (h.ac T hT).continuousOn
  have ha : ContinuousOn A (uIcc 0 T) := by
    unfold A F W g
    fun_prop
  have hai : IntervalIntegrable A volume 0 T := ha.intervalIntegrable
  have heq : ∀ᵐ t, t ∈ uIoc (0:ℝ) T → deriv B t = A t-phi*L t := by
    filter_upwards [h.ode] with t ht hi
    have ht0 : 0≤t := le_of_lt (show t ∈ Ioc 0 T by simpa [uIoc_of_le hT] using hi).1
    exact (discounted_primitive_derivative a K phi r D H hK.ne' (ht ht0)).deriv
  have hei : deriv B =ᵐ[volume.restrict (uIoc (0:ℝ) T)] (fun t => A t-phi*L t) :=
    (ae_restrict_iff' measurableSet_uIoc).2 heq
  have hsubi := hb.intervalIntegrable_deriv.congr_ae hei
  have hli : IntervalIntegrable L volume 0 T := by
    have hh := (hai.sub hsubi).div_const phi
    convert hh using 1
    ext t
    field_simp
    <;> ring
  have hi : (∫ t in (0:ℝ)..T, A t-phi*L t) = B T-B 0 := by
    rw [← hb.integral_deriv_eq_sub]
    apply intervalIntegral.integral_congr_ae
    filter_upwards [heq] with t ht hmem using (ht hmem).symm
  rw [intervalIntegral.integral_sub hai (hli.const_mul phi),
      intervalIntegral.integral_const_mul] at hi
  change (∫ t in (0:ℝ)..T, L t) = _
  simp only [B, neg_mul, mul_zero, neg_zero, Real.exp_zero, one_mul] at hi
  dsimp [A] at hi
  simp only [neg_mul] at hi
  field_simp
  nlinarith [hi]

end Viridis.InformationWeightedStewardship
