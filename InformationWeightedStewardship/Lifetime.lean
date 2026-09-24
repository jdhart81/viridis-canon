import InformationWeightedStewardship.Trajectory

namespace Viridis.InformationWeightedStewardship
open MeasureTheory Set Filter
open scoped Topology
open Viridis.Stewardship.StewardshipSetpoint

 theorem Admissible.continuousOn_positive {a K phi Omega : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) : ContinuousOn D (Ioi 0) := by
  intro t ht
  change 0<t at ht
  have hac := (h.ac (t+1) (by linarith [ht])).continuousOn
  rw [uIcc_of_le (show (0:ℝ)≤t+1 by linarith [ht])] at hac
  exact (hac.continuousAt (Icc_mem_nhds ht (by linarith))).continuousWithinAt

 theorem discounted_stock_integrable {a K phi Omega r : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) (hr : 0<r)
    (f : ℝ → ℝ) (hf : Continuous f) :
    IntegrableOn (fun t => Real.exp (-r*t)*f (D t)) (Ioi (0:ℝ)) := by
  obtain ⟨C,hC⟩ := isCompact_Icc.exists_bound_of_continuousOn (s := Icc (0:ℝ) K) hf.continuousOn
  apply (integrableOn_exp_mul_Ioi (show -r<0 by linarith) 0).mul_bdd
    ((hf.comp_continuousOn h.continuousOn_positive).aestronglyMeasurable measurableSet_Ioi)
  filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
  exact hC (D t) (h.bounds t ht.le)

 theorem objective_integrable {a K phi Omega r : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) (hK : 0<K) (hO : 0<Omega) (hr : 0<r) :
    IntegrableOn (fun t => Real.exp (-r*t)*(D t/K)*H t) (Ioi (0:ℝ)) := by
  have hm : AEStronglyMeasurable (fun t => (D t/K)*H t) (volume.restrict (Ioi (0:ℝ))) :=
    (h.continuousOn_positive.div_const K).aestronglyMeasurable measurableSet_Ioi |>.mul
      h.measurable_control.aestronglyMeasurable
  have hi := (integrableOn_exp_mul_Ioi (show -r<0 by linarith) 0).mul_bdd (c := Omega*K) hm
  have hb : ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)), ‖(D t/K)*H t‖ ≤ Omega*K := by
    filter_upwards [ae_restrict_mem measurableSet_Ioi, ae_restrict_of_ae h.control] with t ht hc
    obtain ⟨hd0,hdk⟩ := h.bounds t ht.le
    obtain ⟨hh0,hhcap⟩ := hc ht.le
    rw [Real.norm_eq_abs, abs_of_nonneg (mul_nonneg (div_nonneg hd0 hK.le) hh0)]
    have hq : D t/K ≤ 1 := (div_le_one hK).2 hdk
    calc
      D t/K*H t ≤ H t := mul_le_of_le_one_left hh0 hq
      _ ≤ Omega*D t := hhcap
      _ ≤ Omega*K := mul_le_mul_of_nonneg_left hdk hO.le
  simpa [mul_assoc] using hi hb

 theorem terminal_vanishes {a K phi Omega r : ℝ} {D H : ℝ → ℝ}
    (h : Admissible a K phi Omega D H) (hK : 0<K) (hr : 0<r) :
    Tendsto (fun T => Real.exp (-r*T)*W K (D T)) atTop (𝓝 0) := by
  have he : Tendsto (fun T : ℝ => Real.exp (-r*T)) atTop (𝓝 0) :=
    Real.tendsto_exp_atBot.comp ((tendsto_const_mul_atBot_of_neg (show -r<0 by linarith)).2 tendsto_id)
  apply squeeze_zero'
  · filter_upwards [eventually_ge_atTop (0:ℝ)] with t ht
    unfold W
    positivity
  · filter_upwards [eventually_ge_atTop (0:ℝ)] with t ht
    obtain ⟨hd0,hdk⟩ := h.bounds t ht
    have hw : W K (D t) ≤ K/2 := by
      unfold W
      apply (div_le_iff₀ (by positivity : 0<2*K)).2
      nlinarith [sq_nonneg (K-D t)]
    exact mul_le_mul_of_nonneg_left hw (Real.exp_pos _).le
  · simpa using he.mul_const (K/2)

 theorem infinite_accounting (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (h : Admissible a K phi Omega D H) :
    objective K r D H = W K (D 0)/phi +
      (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*F a K r (D t))/phi := by
  have hf : Continuous (F a K r) := by unfold F W g; fun_prop
  have hj := intervalIntegral_tendsto_integral_Ioi 0 (objective_integrable h hK hO hr) tendsto_id
  have hi := intervalIntegral_tendsto_integral_Ioi 0 (discounted_stock_integrable h hr _ hf) tendsto_id
  have ht := terminal_vanishes h hK hr
  have hrhs := (((tendsto_const_nhds (x := W K (D 0)/phi)).sub (ht.div_const phi)).add (hi.div_const phi))
  have heq : (fun T => ∫ t in (0:ℝ)..T, Real.exp (-r*t)*(D t/K)*H t) =ᶠ[atTop]
      (fun T => W K (D 0)/phi - Real.exp (-r*T)*W K (D T)/phi +
        (∫ t in (0:ℝ)..T, Real.exp (-r*t)*F a K r (D t))/phi) := by
    filter_upwards [eventually_ge_atTop (0:ℝ)] with T hT
    exact finite_accounting a K phi Omega r T D H hK hp hr hT h
  have := tendsto_nhds_unique hj (hrhs.congr' heq.symm)
  simpa [objective] using this

/-- Full AC infinite-horizon regret identity. The model-to-integral bridge is proved
above; neither an accounting nor an optimality identity is a hypothesis. -/
 theorem lifetime_regret (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (h : Admissible a K phi Omega D H) (hinit : D 0 = stockStar a K r) :
    stationaryValue a K phi r - objective K r D H =
      a/(2*phi*K^2) * (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*
        (D t-stockStar a K r)^2*(2*D t+stockStar a K r)) := by
  let s := stockStar a K r
  have hf : Continuous (F a K r) := by unfold F W g; fun_prop
  have hfi := discounted_stock_integrable h hr _ hf
  have he := integrableOn_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  have hint : (∫ t in Ioi (0:ℝ), Real.exp (-r*t)) = 1/r := by
    simpa using integral_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  have hgap : (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*(F a K r s-F a K r (D t))) =
      F a K r s/r - (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*F a K r (D t)) := by
    simp_rw [mul_sub]
    rw [integral_sub (he.mul_const _) hfi, integral_mul_const, hint]
    ring
  have hfactor : (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*(F a K r s-F a K r (D t))) =
      a/(2*K^2)*(∫ t in Ioi (0:ℝ), Real.exp (-r*t)*(D t-s)^2*(2*D t+s)) := by
    simp_rw [s, factorization a K r _ ha.ne' hK.ne']
    rw [← integral_const_mul]
    apply integral_congr_ae
    exact Filter.Eventually.of_forall (fun _ => by ring)
  rw [infinite_accounting a K phi Omega r D H hK hp hO hr h, hinit,
      stationary_value_accounting a K phi r hp.ne' hr.ne']
  have hh := hgap.symm.trans hfactor
  dsimp [s] at hh
  field_simp at hh ⊢
  nlinarith [hh]

 theorem lifetime_optimal (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (hr2 : r<2*a) (hcap : (a+r)/(3*phi) ≤ Omega)
    (h : Admissible a K phi Omega D H) (hinit : D 0 = stockStar a K r) :
    Admissible a K phi Omega (fun _ => stockStar a K r)
      (fun _ => heldRate a K phi (stockStar a K r)) ∧
    objective K r D H ≤ stationaryValue a K phi r := by
  refine ⟨stationary_admissible a K phi Omega r ha hK hp hr hr2 hcap, ?_⟩
  have hid := lifetime_regret a K phi Omega r D H ha hK hp hO hr h hinit
  have hi : 0 ≤ (∫ t in Ioi (0:ℝ), Real.exp (-r*t)*(D t-stockStar a K r)^2*
      (2*D t+stockStar a K r)) := by
    apply integral_nonneg_of_ae
    filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
    have hd := (h.bounds t ht.le).1
    have hs := stockStar_pos a K r ha hK hr2
    positivity
  have hc : 0 ≤ a/(2*phi*K^2) := by positivity
  nlinarith [mul_nonneg hc hi]

end Viridis.InformationWeightedStewardship
