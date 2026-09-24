import InformationWeightedStewardship.Equality

namespace Viridis.InformationWeightedStewardship
open MeasureTheory Set Filter
open scoped Topology
open Viridis.Stewardship.StewardshipSetpoint

noncomputable def rawObjective (r : ℝ) (H : ℝ → ℝ) : ℝ :=
  ∫ t in Ioi (0:ℝ), Real.exp (-r*t)*H t
noncomputable def rawValue (a K phi r : ℝ) : ℝ := heldRate a K phi (Dstar a K r)/r

 theorem raw_finite_accounting (a K phi Omega r T : ℝ) (D H : ℝ → ℝ)
    (hp : 0<phi) (hr : 0<r) (hT : 0≤T) (h : Admissible a K phi Omega D H) :
    (∫ t in (0:ℝ)..T, Real.exp (-r*t)*H t) = D 0/phi-Real.exp (-r*T)*D T/phi+
      (∫ t in (0:ℝ)..T, Real.exp (-r*t)*Phi a K r (D t))/phi := by
  let B := fun t => Real.exp (-r*t)*D t
  let A := fun t => Real.exp (-r*t)*Phi a K r (D t)
  let L := fun t => Real.exp (-r*t)*H t
  have hb : AbsolutelyContinuousOnInterval B 0 T := (discount_ac r T hr hT).fun_mul (h.ac T hT)
  have hc := (h.ac T hT).continuousOn
  have ha : ContinuousOn A (uIcc 0 T) := by unfold A Phi g; fun_prop
  have hai : IntervalIntegrable A volume 0 T := ha.intervalIntegrable
  have heq : ∀ᵐ t, t∈uIoc (0:ℝ) T → deriv B t=A t-phi*L t := by
    filter_upwards [h.ode] with t ht hi
    have ht0 : 0≤t := le_of_lt (show t∈Ioc 0 T by simpa [uIoc_of_le hT] using hi).1
    have hd : HasDerivAt B (A t-phi*L t) t := by
      convert (discount_derivative r t).mul (ht ht0) using 1
      unfold A Phi L
      ring
    exact hd.deriv
  have hei : deriv B =ᵐ[volume.restrict (uIoc (0:ℝ) T)] (fun t => A t-phi*L t) :=
    (ae_restrict_iff' measurableSet_uIoc).2 heq
  have hsubi := hb.intervalIntegrable_deriv.congr_ae hei
  have hli : IntervalIntegrable L volume 0 T := by
    have hh := (hai.sub hsubi).div_const phi
    convert hh using 1
    ext t
    field_simp
    <;> ring
  have hi : (∫ t in (0:ℝ)..T,A t-phi*L t)=B T-B 0 := by
    rw [← hb.integral_deriv_eq_sub]
    apply intervalIntegral.integral_congr_ae
    filter_upwards [heq] with t ht hm using (ht hm).symm
  rw [intervalIntegral.integral_sub hai (hli.const_mul phi),intervalIntegral.integral_const_mul] at hi
  change (∫ t in (0:ℝ)..T,L t)=_
  simp only [B,neg_mul,mul_zero,neg_zero,Real.exp_zero,one_mul] at hi
  dsimp [A] at hi
  simp only [neg_mul] at hi
  field_simp
  nlinarith [hi]

 theorem raw_objective_integrable {a K phi Omega r : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) (hO : 0<Omega) (hr : 0<r) :
    IntegrableOn (fun t => Real.exp (-r*t)*H t) (Ioi (0:ℝ)) := by
  apply (integrableOn_exp_mul_Ioi (show -r<0 by linarith) 0).mul_bdd (c := Omega*K)
    h.measurable_control.aestronglyMeasurable
  filter_upwards [ae_restrict_mem measurableSet_Ioi,ae_restrict_of_ae h.control] with t ht hc
  obtain ⟨hh0,hhcap⟩ := hc ht.le
  rw [Real.norm_eq_abs,abs_of_nonneg hh0]
  exact hhcap.trans (mul_le_mul_of_nonneg_left (h.bounds t ht.le).2 hO.le)

 theorem raw_terminal_vanishes {a K phi Omega r : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) (hr : 0<r) :
    Tendsto (fun T => Real.exp (-r*T)*D T) atTop (𝓝 0) := by
  have he : Tendsto (fun T : ℝ => Real.exp (-r*T)) atTop (𝓝 0) :=
    Real.tendsto_exp_atBot.comp ((tendsto_const_mul_atBot_of_neg (show -r<0 by linarith)).2 tendsto_id)
  apply squeeze_zero'
  · filter_upwards [eventually_ge_atTop (0:ℝ)] with t ht
    exact mul_nonneg (Real.exp_pos _).le (h.bounds t ht).1
  · filter_upwards [eventually_ge_atTop (0:ℝ)] with t ht
    exact mul_le_mul_of_nonneg_left (h.bounds t ht).2 (Real.exp_pos _).le
  · simpa using he.mul_const K

 theorem raw_infinite_accounting (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (hp : 0<phi) (hO : 0<Omega) (hr : 0<r) (h : Admissible a K phi Omega D H) :
    rawObjective r H = D 0/phi+(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*Phi a K r (D t))/phi := by
  have hf : Continuous (Phi a K r) := by unfold Phi g; fun_prop
  have hj := intervalIntegral_tendsto_integral_Ioi 0 (raw_objective_integrable h hO hr) tendsto_id
  have hi := intervalIntegral_tendsto_integral_Ioi 0 (discounted_stock_integrable h hr _ hf) tendsto_id
  have ht := raw_terminal_vanishes h hr
  have hrhs := ((tendsto_const_nhds (x := D 0/phi)).sub (ht.div_const phi)).add (hi.div_const phi)
  have heq : (fun T => ∫ t in (0:ℝ)..T,Real.exp (-r*t)*H t) =ᶠ[atTop]
      (fun T => D 0/phi-Real.exp (-r*T)*D T/phi+
        (∫ t in (0:ℝ)..T,Real.exp (-r*t)*Phi a K r (D t))/phi) := by
    filter_upwards [eventually_ge_atTop (0:ℝ)] with T hT
    exact raw_finite_accounting a K phi Omega r T D H hp hr hT h
  simpa [rawObjective] using tendsto_nhds_unique hj (hrhs.congr' heq.symm)

 theorem raw_lifetime_regret (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (h : Admissible a K phi Omega D H) (hinit : D 0=Dstar a K r) :
    rawValue a K phi r-rawObjective r H =
      a/(phi*K)*(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(D t-Dstar a K r)^2) := by
  let s := Dstar a K r
  have hf : Continuous (Phi a K r) := by unfold Phi g; fun_prop
  have hfi := discounted_stock_integrable h hr _ hf
  have he := integrableOn_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  have hint : (∫ t in Ioi (0:ℝ),Real.exp (-r*t))=1/r := by
    simpa using integral_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  have hgap : (∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(Phi a K r s-Phi a K r (D t))) =
      Phi a K r s/r-(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*Phi a K r (D t)) := by
    simp_rw [mul_sub]
    rw [integral_sub (he.mul_const _) hfi,integral_mul_const,hint]
    ring
  have hfactor : (∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(Phi a K r s-Phi a K r (D t))) =
      a/K*(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(D t-s)^2) := by
    simp_rw [s,raw_gap a K r _ ha.ne' hK.ne']
    rw [← integral_const_mul]
    apply integral_congr_ae
    exact Filter.Eventually.of_forall (fun _ => by ring)
  rw [raw_infinite_accounting a K phi Omega r D H hp hO hr h,hinit]
  have hh := hgap.symm.trans hfactor
  dsimp [s] at hh
  unfold rawValue heldRate
  unfold Phi at hh ⊢
  field_simp at hh ⊢
  nlinarith [hh]

 theorem raw_stationary_admissible (a K phi Omega r : ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hr : 0<r) (hra : r<a)
    (hcap : (a+r)/(2*phi) ≤ Omega) :
    Admissible a K phi Omega (fun _ => Dstar a K r) (fun _ => heldRate a K phi (Dstar a K r)) := by
  have hs := (Dstar_eq_half_K_one_minus_r_over_rho a K r hK ha hr.le hra).2
  have hf : 0≤heldRate a K phi (Dstar a K r) ∧ heldRate a K phi (Dstar a K r)≤Omega*Dstar a K r := by
    rw [raw_held_rate a K phi r ha.ne' hK.ne' hp.ne',mul_div_assoc]
    have hspos := hs.1
    refine ⟨by positivity, ?_⟩
    simpa [mul_comm] using mul_le_mul_of_nonneg_left hcap hs.1.le
  constructor
  · intro T _
    exact (LipschitzWith.const _).lipschitzOnWith.absolutelyContinuousOnInterval
  · exact measurable_const
  · intro t _; exact ⟨hs.1.le,by linarith [hs.2]⟩
  · exact Filter.Eventually.of_forall (fun _ _ => hf)
  · apply Filter.Eventually.of_forall
    intro t _
    rw [held_rate_balance a K phi _ hp.ne']
    exact hasDerivAt_const t _

 theorem raw_lifetime_optimal (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r) (hra : r<a)
    (hcap : (a+r)/(2*phi) ≤ Omega) (h : Admissible a K phi Omega D H)
    (hinit : D 0=Dstar a K r) :
    Admissible a K phi Omega (fun _ => Dstar a K r) (fun _ => heldRate a K phi (Dstar a K r)) ∧
    rawObjective r H ≤ rawValue a K phi r := by
  refine ⟨raw_stationary_admissible a K phi Omega r ha hK hp hr hra hcap, ?_⟩
  have hid := raw_lifetime_regret a K phi Omega r D H ha hK hp hO hr h hinit
  have hi : 0≤(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(D t-Dstar a K r)^2) :=
    integral_nonneg (fun _ => by positivity)
  have hc : 0≤a/(phi*K) := by positivity
  nlinarith [mul_nonneg hc hi]

end Viridis.InformationWeightedStewardship
