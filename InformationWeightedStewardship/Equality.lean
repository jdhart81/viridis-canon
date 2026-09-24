import InformationWeightedStewardship.Lifetime

namespace Viridis.InformationWeightedStewardship
open MeasureTheory Set Filter
open scoped Topology
open Viridis.Stewardship.StewardshipSetpoint

 theorem stationary_objective (a K phi r : ℝ) (hr : 0<r) :
    objective K r (fun _ => stockStar a K r)
      (fun _ => heldRate a K phi (stockStar a K r)) = stationaryValue a K phi r := by
  unfold objective stationaryValue
  rw [integral_mul_const, integral_mul_const]
  have he : (∫ t in Ioi (0:ℝ), Real.exp (-r*t)) = 1/r := by
    simpa using integral_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  rw [he]
  ring

 theorem equality_iff_stock (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (hr2 : r<2*a) (h : Admissible a K phi Omega D H)
    (hinit : D 0 = stockStar a K r) :
    objective K r D H = stationaryValue a K phi r ↔
      ∀ t, 0≤t → D t = stockStar a K r := by
  let s := stockStar a K r
  let R := fun t => Real.exp (-r*t)*(D t-s)^2*(2*D t+s)
  have hi : IntegrableOn R (Ioi (0:ℝ)) := by
    have hf : Continuous (fun d : ℝ => (d-s)^2*(2*d+s)) := by fun_prop
    simpa [R, mul_assoc] using discounted_stock_integrable h hr _ hf
  have hn : ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)), 0≤R t := by
    filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
    have hd := (h.bounds t ht.le).1
    have hs : 0<s := stockStar_pos a K r ha hK hr2
    dsimp [R]; positivity
  have hid := lifetime_regret a K phi Omega r D H ha hK hp hO hr h hinit
  change stationaryValue a K phi r-objective K r D H = a/(2*phi*K^2)*(∫ t in Ioi (0:ℝ), R t) at hid
  constructor
  · intro he
    have hz : (∫ t in Ioi (0:ℝ), R t)=0 := by
      rw [he,sub_self] at hid
      exact (mul_eq_zero.mp hid.symm).resolve_left (ne_of_gt (by positivity))
    have hae := (integral_eq_zero_iff_of_nonneg_ae hn hi).1 hz
    have hds : D =ᵐ[volume.restrict (Ioi (0:ℝ))] (fun _ => s) := by
      filter_upwards [hae,ae_restrict_mem measurableSet_Ioi] with t ht hpos
      have hd := (h.bounds t hpos.le).1
      have hs : 0<s := stockStar_pos a K r ha hK hr2
      have hlast : 2*D t+s ≠ 0 := ne_of_gt (by linarith)
      have hexp : Real.exp (-r*t) ≠ 0 := ne_of_gt (Real.exp_pos _)
      simpa [R, mul_eq_zero, hlast, hexp, sub_eq_zero] using ht
    have hall := Measure.eqOn_open_of_ae_eq hds isOpen_Ioi h.continuousOn_positive continuousOn_const
    intro t ht
    rcases ht.eq_or_lt with hzero | hpos
    · simpa [← hzero] using hinit
    · exact hall hpos
  · intro hs
    have hz : (∫ t in Ioi (0:ℝ), R t)=0 := by
      apply integral_eq_zero_of_ae
      filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
      simp [R, hs t ht.le, s]
    rw [hz,mul_zero] at hid
    linarith

 theorem held_stock_control (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (hp : 0<phi) (h : Admissible a K phi Omega D H)
    (hs : ∀ t, 0≤t → D t=stockStar a K r) :
    ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)), H t=heldRate a K phi (stockStar a K r) := by
  filter_upwards [ae_restrict_mem measurableSet_Ioi,ae_restrict_of_ae h.ode] with t ht hd
  have heq : D =ᶠ[𝓝 t] (fun _ => stockStar a K r) := by
    filter_upwards [eventually_gt_nhds ht] with x hx using hs x hx.le
  have hc : HasDerivAt D 0 t := (hasDerivAt_const t (stockStar a K r)).congr_of_eventuallyEq heq
  have hz := (hd ht.le).unique hc
  rw [hs t ht.le] at hz
  unfold heldRate
  apply (eq_div_iff hp.ne').2
  nlinarith

/-- Uniqueness for the constant control, still for AC trajectories and a.e. ODE.
An exponentially weighted squared difference has nonpositive a.e. derivative. -/
 theorem held_control_stock (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hr2 : r<2*a)
    (h : Admissible a K phi Omega D H) (hinit : D 0=stockStar a K r)
    (hh : ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)), H t=heldRate a K phi (stockStar a K r)) :
    ∀ t, 0≤t → D t=stockStar a K r := by
  let s := stockStar a K r
  have hs : 0<s := stockStar_pos a K r ha hK hr2
  have hhae : ∀ᵐ t, t∈Ioi (0:ℝ) → H t=heldRate a K phi s :=
    (ae_restrict_iff' measurableSet_Ioi).1 hh
  intro T hT
  let E := fun t => Real.exp (-(2*a)*t)*(D t-s)^2
  have hsub : AbsolutelyContinuousOnInterval (fun t => D t-s) 0 T :=
    (h.ac T hT).sub ((LipschitzWith.const s).lipschitzOnWith.absolutelyContinuousOnInterval)
  have he : AbsolutelyContinuousOnInterval E 0 T := by
    simpa [E,pow_two] using (discount_ac (2*a) T (by positivity) hT).fun_mul (hsub.fun_mul hsub)
  have hder : ∀ᵐ t, t∈uIoc (0:ℝ) T → deriv E t ≤ 0 := by
    filter_upwards [h.ode,hhae] with t hd hc ht
    have hpos : 0<t := (show t∈Ioc 0 T by simpa [uIoc_of_le hT] using ht).1
    have hd0 := (h.bounds t hpos.le).1
    have hdt := hd hpos.le
    rw [hc hpos] at hdt
    have hz := held_rate_balance a K phi s hp.ne'
    have hdt' : HasDerivAt D (g a K (D t)-g a K s) t := by
      convert hdt using 1 <;> linarith
    have hformula : HasDerivAt E
        (-(2*a/K)*Real.exp (-(2*a)*t)*(D t-s)^2*(D t+s)) t := by
      convert (discount_derivative (2*a) t).mul ((hdt'.sub_const s).pow 2) using 1
      unfold g
      norm_num [Pi.pow_apply]
      field_simp
      <;> ring
    rw [hformula.deriv]
    have : 0 ≤ (2*a/K)*Real.exp (-(2*a)*t)*(D t-s)^2*(D t+s) := by positivity
    nlinarith
  have hint : (∫ t in (0:ℝ)..T, deriv E t) ≤ 0 := by
    rw [intervalIntegral.integral_of_le hT]
    apply integral_nonpos_of_ae
    filter_upwards [ae_restrict_mem measurableSet_Ioc, ae_restrict_of_ae hder] with t ht hd
    exact hd (by simpa [uIoc_of_le hT] using ht)
  rw [he.integral_deriv_eq_sub] at hint
  have he0 : E 0=0 := by simp [E,s,hinit]
  rw [he0,sub_zero] at hint
  have hsq : (D T-s)^2 ≤ 0 := by
    have hexp := Real.exp_pos (-(2*a)*T)
    dsimp [E] at hint
    nlinarith
  exact sub_eq_zero.mp (sq_eq_zero_iff.mp (le_antisymm hsq (sq_nonneg _)))

 theorem equality_iff_control (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (hr2 : r<2*a) (h : Admissible a K phi Omega D H)
    (hinit : D 0=stockStar a K r) :
    objective K r D H = stationaryValue a K phi r ↔
      ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)), H t=heldRate a K phi (stockStar a K r) := by
  rw [equality_iff_stock a K phi Omega r D H ha hK hp hO hr hr2 h hinit]
  exact ⟨held_stock_control a K phi Omega r D H hp h,
    held_control_stock a K phi Omega r D H ha hK hp hr2 h hinit⟩

end Viridis.InformationWeightedStewardship
