/-
Information-weighted stewardship: exact conditional optimality certificate.
Local review candidate. No empirical, novelty, or universal alignment claim.
The admitted policy class is locally absolutely continuous stock, measurable
control, and an a.e. physical ODE, with stock initially at the stated setpoint.
-/
import InformationWeightedStewardship.Raw

namespace Viridis.InformationWeightedStewardship
open MeasureTheory Set Filter
open scoped Topology
open Viridis.Stewardship.StewardshipSetpoint

/-- The complete information-weighted certificate includes an actual feasible
stationary trajectory, its objective integral, exact lifetime regret, dominance,
and equality in stock at every nonnegative time / control modulo null sets. -/
 theorem global_certificate (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (hr2 : r<2*a) (hcap : (a+r)/(3*phi) ≤ Omega)
    (h : Admissible a K phi Omega D H) (hinit : D 0=stockStar a K r) :
    Admissible a K phi Omega (fun _ => stockStar a K r)
      (fun _ => heldRate a K phi (stockStar a K r)) ∧
    objective K r (fun _ => stockStar a K r) (fun _ => heldRate a K phi (stockStar a K r)) =
      stationaryValue a K phi r ∧
    stationaryValue a K phi r-objective K r D H =
      a/(2*phi*K^2)*(∫ t in Ioi (0:ℝ),Real.exp (-r*t)*(D t-stockStar a K r)^2*(2*D t+stockStar a K r)) ∧
    objective K r D H ≤ stationaryValue a K phi r ∧
    (objective K r D H = stationaryValue a K phi r ↔ ∀ t,0≤t → D t=stockStar a K r) ∧
    (objective K r D H = stationaryValue a K phi r ↔
      ∀ᵐ t ∂volume.restrict (Ioi (0:ℝ)),H t=heldRate a K phi (stockStar a K r)) := by
  exact ⟨stationary_admissible a K phi Omega r ha hK hp hr hr2 hcap,
    stationary_objective a K phi r hr,
    lifetime_regret a K phi Omega r D H ha hK hp hO hr h hinit,
    (lifetime_optimal a K phi Omega r D H ha hK hp hO hr hr2 hcap h hinit).2,
    equality_iff_stock a K phi Omega r D H ha hK hp hO hr hr2 h hinit,
    equality_iff_control a K phi Omega r D H ha hK hp hO hr hr2 h hinit⟩

 theorem arbitrary_initial_upper_bound (a K phi Omega r : ℝ) (D H : ℝ → ℝ)
    (ha : 0<a) (hK : 0<K) (hp : 0<phi) (hO : 0<Omega) (hr : 0<r)
    (hr2 : r<2*a) (h : Admissible a K phi Omega D H) :
    objective K r D H ≤ (W K (D 0)+F a K r (stockStar a K r)/r)/phi := by
  have hf : Continuous (F a K r) := by unfold F W g; fun_prop
  have hi := discounted_stock_integrable h hr _ hf
  have he := integrableOn_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  have hm : (∫ t in Ioi (0:ℝ),Real.exp (-r*t)*F a K r (D t)) ≤
      (∫ t in Ioi (0:ℝ),Real.exp (-r*t)*F a K r (stockStar a K r)) := by
    apply integral_mono_ae hi (he.mul_const _)
    filter_upwards [ae_restrict_mem measurableSet_Ioi] with t ht
    exact mul_le_mul_of_nonneg_left (sub_nonneg.mp
      (potential_gap_nonneg a K r (D t) ha hK hr2 (h.bounds t ht.le).1)) (Real.exp_pos _).le
  have hint : (∫ t in Ioi (0:ℝ),Real.exp (-r*t))=1/r := by
    simpa using integral_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  rw [integral_mul_const,hint] at hm
  rw [infinite_accounting a K phi Omega r D H hK hp hO hr h]
  field_simp at hm ⊢
  nlinarith [hm]

 theorem raw_stationary_objective (a K phi r : ℝ) (hr : 0<r) :
    rawObjective r (fun _ => heldRate a K phi (Dstar a K r))=rawValue a K phi r := by
  unfold rawObjective rawValue
  rw [integral_mul_const]
  have hint : (∫ t in Ioi (0:ℝ),Real.exp (-r*t))=1/r := by
    simpa using integral_exp_mul_Ioi (show -r<0 by linarith) (0:ℝ)
  rw [hint]
  ring

end Viridis.InformationWeightedStewardship
