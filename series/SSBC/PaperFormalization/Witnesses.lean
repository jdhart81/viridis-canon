import PaperFormalization.Certificate

/-!
# Non-vacuity witnesses

Explicit instances showing that the hypotheses of each frozen target `C1`–`C4` are
satisfiable and that the conclusions are non-trivial.

All witnesses use the paper's own negative control (Section 3.1 of `SEALED_paper.tex`):
two unit-demand sites, two sources with capacities `(1/10, 19/10)`, and the "private"
eligibility graph in which source `j` may serve site `i` only if `j = i`.  Total inventory
equals total demand, yet the certified common fulfillment fraction is `1/10`.
-/

namespace Viridis.Run130.Witnesses

open Finset Viridis.Run130 Viridis.Run130.Hall

/-- Two restoration sites, each with unit demand. -/
noncomputable def d2 : Fin 2 → ℝ := fun _ => 1

/-- Two seed sources with capacities `0.1` and `1.9`; total inventory `2` equals total
demand `2`. -/
noncomputable def s2 : Fin 2 → ℝ := fun j => if j = 0 then 1 / 10 else 19 / 10

/-- The "private" eligibility graph: source `j` is eligible for site `i` iff `j = i`. -/
def Epriv : Fin 2 → Fin 2 → Bool := fun j i => decide (j = i)

/-- The complete eligibility graph: every source is eligible for every site. -/
def Efull : Fin 2 → Fin 2 → Bool := fun _ _ => true

/-- A capacity vector that adds a large amount of capacity at source `1`. -/
noncomputable def s2' : Fin 2 → ℝ := fun j => if j = 0 then 1 / 10 else 100

lemma d2_pos : ∀ i, 0 < d2 i := by
  intro i; norm_num [d2]

lemma s2_nonneg : ∀ j, 0 ≤ s2 j := by
  intro j; by_cases h : j = 0 <;> norm_num [s2, h]

lemma s2'_nonneg : ∀ j, 0 ≤ s2' j := by
  intro j; by_cases h : j = 0 <;> norm_num [s2', h]

lemma nbhd_Epriv (U : Finset (Fin 2)) : nbhd Epriv U = U := by
  ext j; simp [Epriv]

lemma nbhd_Efull {U : Finset (Fin 2)} (hU : U.Nonempty) :
    nbhd Efull U = (Finset.univ : Finset (Fin 2)) := by
  obtain ⟨i, hi⟩ := hU
  ext j
  simp only [mem_nbhdOn, Finset.mem_univ, true_and, iff_true]
  exact ⟨i, hi, rfl⟩

/-- The three nonempty subsets of a two-element site set. -/
lemma sites_cases (U : Finset (Fin 2)) (hU : U.Nonempty) :
    U = {0} ∨ U = {1} ∨ U = {0, 1} := by
  revert hU
  revert U
  decide

/-! ## The negative control: adequate total inventory, ten-percent common fulfillment -/

lemma total_supply_eq_total_demand :
    supply s2 (Finset.univ : Finset (Fin 2)) = demand d2 (Finset.univ : Finset (Fin 2)) := by
  simp [cap, dem, s2, d2, Fin.sum_univ_two]
  norm_num

lemma ratio_priv_singleton_zero :
    supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = 1 / 10 := by
  rw [nbhd_Epriv]
  norm_num [cap, dem, s2, d2]

/-- The certificate of the paper's negative control is exactly `1/10`. -/
theorem certificate_priv : certificate Epriv d2 s2 = 1 / 10 := by
  rw [show (1 / 10 : ℝ) = supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) from
    ratio_priv_singleton_zero.symm]
  refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
  · rw [ratio_priv_singleton_zero]; norm_num
  · intro U hU
    rw [ratio_priv_singleton_zero, nbhd_Epriv]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2, d2]
    · norm_num [cap, dem, s2, d2]
    · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl]
      norm_num [cap, dem, s2, d2, Fin.sum_univ_two]

/-- **Non-vacuity for C1.** The hypotheses of `seed_routing_common_fraction_eq_min_cut_ratio`
are satisfiable, and in the paper's negative control the maximum common fulfillment fraction
is genuinely `1/10` — even though total inventory equals total demand. -/
theorem C1_witness :
    IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction Epriv d2 s2 lam} (1 / 10) := by
  have h := seed_routing_common_fraction_eq_min_cut_ratio (E := Epriv) (d := d2) (s := s2)
    d2_pos s2_nonneg
  rwa [certificate_priv] at h

/-- The maximum common fraction of the negative control is strictly below `1`, so `C1_witness`
is not the trivial instance. -/
theorem C1_witness_nontrivial : (1 : ℝ) / 10 < 1 := by norm_num

/-! ## C2 witnesses: both sides of the equivalence are realized -/

/-- **Non-vacuity for C2, negative side.** Full demand is *not* routable in the negative
control, and correspondingly the capacitated Hall condition fails for `U = {0}`. -/
theorem C2_witness_infeasible :
    ¬ IsFeasibleFraction Epriv d2 s2 1 ∧
      ¬ (∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Epriv U)) := by
  have hfail : ¬ (∀ U : Finset (Fin 2), U.Nonempty →
      demand d2 U ≤ supply s2 (nbhd Epriv U)) := by
    intro h
    have h0 := h {0} ⟨0, by simp⟩
    rw [nbhd_Epriv] at h0
    norm_num [cap, dem, s2, d2] at h0
  refine ⟨?_, hfail⟩
  intro hfeas
  exact hfail ((seed_routing_feasible_iff_cut_conditions d2_pos s2_nonneg).1 hfeas)

/-- **Non-vacuity for C2, positive side.** With the same demands and the same total
inventory, but a complete eligibility graph, full demand *is* routable. -/
theorem C2_witness_feasible :
    IsFeasibleFraction Efull d2 s2 1 ∧
      (∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Efull U)) := by
  have hhall : ∀ U : Finset (Fin 2), U.Nonempty → demand d2 U ≤ supply s2 (nbhd Efull U) := by
    intro U hU
    rw [nbhd_Efull hU]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
    · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  exact ⟨(seed_routing_feasible_iff_cut_conditions d2_pos s2_nonneg).2 hhall, hhall⟩

/-! ## C3 witness -/

/-- The certificate is unchanged by adding a large amount of capacity at source `1`, which
lies outside the eligible neighbourhood of the active bottleneck `U = {0}`. -/
theorem certificate_priv' : certificate Epriv d2 s2' = 1 / 10 := by
  have hratio : supply s2' (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = 1 / 10 := by
    rw [nbhd_Epriv]
    norm_num [cap, dem, s2', d2]
  rw [show (1 / 10 : ℝ) = supply s2' (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) from
    hratio.symm]
  refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
  · rw [hratio]; norm_num
  · intro U hU
    rw [hratio, nbhd_Epriv]
    rcases sites_cases U hU with rfl | rfl | rfl
    · norm_num [cap, dem, s2', d2]
    · norm_num [cap, dem, s2', d2]
    · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl]
      norm_num [cap, dem, s2', d2, Fin.sum_univ_two]

/-- **Non-vacuity for C3.** All hypotheses of
`capacity_outside_active_bottleneck_irrelevant` are satisfied by the negative control with
active bottleneck `U = {0}` and the outside source `j₀ = 1`; the conclusion is realized as
the equality `1/10 = 1/10`, i.e. adding `98.1` units of capacity at source `1` provably does
not help. -/
theorem C3_witness :
    ({0} : Finset (Fin 2)).Nonempty ∧
    certificate Epriv d2 s2 = supply s2 (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) ∧
    certificate Epriv d2 s2 < 1 ∧
    (1 : Fin 2) ∉ nbhd Epriv {0} ∧
    (∀ j, j ≠ 1 → s2' j = s2 j) ∧
    s2 1 ≤ s2' 1 ∧
    certificate Epriv d2 s2' = certificate Epriv d2 s2 := by
  refine ⟨⟨0, by simp⟩, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [certificate_priv, ratio_priv_singleton_zero]
  · rw [certificate_priv]; norm_num
  · rw [nbhd_Epriv]; decide
  · intro j hj
    have hj0 : j = 0 := by revert hj; revert j; decide
    subst hj0
    norm_num [s2, s2']
  · norm_num [s2, s2']
  · rw [certificate_priv, certificate_priv']

/-! ## The negative control in general form (paper claim C130-06)

"Adequate total seed inventory can coexist with an arbitrarily small common fulfillment
fraction when eligibility neighborhoods are imbalanced." -/

/-- Capacities `(e, 2 - e)` for a parameter `e`; total inventory is always `2`, which equals
total demand for `d2`. -/
noncomputable def sEps (e : ℝ) : Fin 2 → ℝ := fun j => if j = 0 then e else 2 - e

lemma sEps_nonneg {e : ℝ} (he0 : 0 < e) (he1 : e ≤ 1) : ∀ j, 0 ≤ sEps e j := by
  intro j
  by_cases h : j = 0 <;> simp only [sEps, h, if_true, if_false] <;> linarith

lemma sEps_total {e : ℝ} :
    supply (sEps e) (Finset.univ : Finset (Fin 2))
      = demand d2 (Finset.univ : Finset (Fin 2)) := by
  simp [cap, dem, sEps, d2, Fin.sum_univ_two]

/-- **Arbitrarily severe negative control.**  For every `0 < e ≤ 1` the two-site, two-source
instance with private eligibility and capacities `(e, 2 - e)` has total inventory equal to
total demand, yet its maximum common fulfillment fraction is exactly `e`. -/
theorem negative_control_arbitrarily_severe {e : ℝ} (he0 : 0 < e) (he1 : e ≤ 1) :
    supply (sEps e) (Finset.univ : Finset (Fin 2))
        = demand d2 (Finset.univ : Finset (Fin 2)) ∧
      IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction Epriv d2 (sEps e) lam} e := by
  have hratio : supply (sEps e) (nbhd Epriv {0}) / demand d2 ({0} : Finset (Fin 2)) = e := by
    rw [nbhd_Epriv]
    norm_num [cap, dem, sEps, d2]
  have hcert : certificate Epriv d2 (sEps e) = e := by
    have h0 : certificate Epriv d2 (sEps e)
        = supply (sEps e) (nbhd Epriv ({0} : Finset (Fin 2)))
            / demand d2 ({0} : Finset (Fin 2)) := by
      refine certificate_eq_ratio_of_min ⟨0, by simp⟩ ?_ ?_
      · rw [hratio]; exact he1
      · intro U hU
        rw [hratio, nbhd_Epriv]
        rcases sites_cases U hU with rfl | rfl | rfl
        · norm_num [cap, dem, sEps, d2]
        · rw [show supply (sEps e) ({1} : Finset (Fin 2))
              / demand d2 ({1} : Finset (Fin 2)) = 2 - e by norm_num [cap, dem, sEps, d2]]
          linarith
        · rw [show ({0, 1} : Finset (Fin 2)) = Finset.univ from rfl,
            show supply (sEps e) (Finset.univ : Finset (Fin 2))
              / demand d2 (Finset.univ : Finset (Fin 2)) = 1 by
                norm_num [cap, dem, sEps, d2, Fin.sum_univ_two]]
          exact he1
    rw [h0, hratio]
  refine ⟨sEps_total, ?_⟩
  have h := seed_routing_common_fraction_eq_min_cut_ratio (E := Epriv) (d := d2)
    (s := sEps e) d2_pos (sEps_nonneg he0 he1)
  rwa [hcert] at h

/-! ## C4 witnesses -/

/-- Two scenarios: the complete eligibility graph and the "private" one. -/
def Es2 : Fin 2 → Fin 2 → Fin 2 → Bool := fun k => if k = 0 then Efull else Epriv

lemma scenarioIntersection_Es2 : scenarioIntersection Es2 = Epriv := by decide

lemma scenarioUnion_Es2 : scenarioUnion Es2 = Efull := by decide

theorem certificate_full : certificate Efull d2 s2 = 1 := by
  refine le_antisymm certificate_le_one (le_certificate le_rfl ?_)
  intro U hU
  rw [nbhd_Efull hU]
  rcases sites_cases U hU with rfl | rfl | rfl
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]
  · norm_num [cap, dem, s2, d2, Fin.sum_univ_two]

/-- **Non-vacuity for C4.** For the two-scenario family `Es2`, the intersection certificate
is `1/10`, strictly below the certificate `1` of scenario `0`, and equal to the certificate
of scenario `1`.  Moreover the *union* certificate is `1`: the union is falsely reassuring,
exactly as the paper's scenario-robustness section asserts. -/
theorem C4_witness :
    certificate (scenarioIntersection Es2) d2 s2 = 1 / 10 ∧
    certificate (Es2 0) d2 s2 = 1 ∧
    certificate (Es2 1) d2 s2 = 1 / 10 ∧
    certificate (scenarioUnion Es2) d2 s2 = 1 ∧
    certificate (scenarioIntersection Es2) d2 s2 < certificate (Es2 0) d2 s2 := by
  have h0 : Es2 0 = Efull := by decide
  have h1 : Es2 1 = Epriv := by decide
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [scenarioIntersection_Es2, certificate_priv]
  · rw [h0, certificate_full]
  · rw [h1, certificate_priv]
  · rw [scenarioUnion_Es2, certificate_full]
  · rw [scenarioIntersection_Es2, h0, certificate_priv, certificate_full]
    norm_num

end Viridis.Run130.Witnesses
