import PaperFormalization.Mixture

/-!
# C3: component dominance and the late-change evidence penalty

This file formalizes Equations (5)–(6) of `SEALED_paper.tex`:

* `M_n ≥ π_ν ∏_{i=ν}^{n} Λ_i` (Equation 5), hence the mixture alarm time is never later
  than the alarm time of the embedded change-time-`ν` component;
* `a_ν = log(1/(α π_ν)) = log(1/α) + log[ν(ν+1)]` (Equation 6), whose late-change part
  `log[ν(ν+1)]` is asymptotically `2 log ν`.

The alarm time is formalized by `firstAlarm f c`, the first index at which the path `f`
reaches the level `c`, valued in `ℕ∞` so that "never alarms" is represented by `⊤`.
-/

namespace Viridis.Run129.PaperFormalization

open Filter
open scoped Topology

variable {Ω : Type*}

/-- The first index at which the path `f` reaches level `c`, or `⊤` if it never does. -/
noncomputable def firstAlarm (f : ℕ → ℝ) (c : ℝ) : ℕ∞ :=
  sInf ((fun n : ℕ => (n : ℕ∞)) '' {n : ℕ | c ≤ f n})

lemma firstAlarm_le_of_le {f : ℕ → ℝ} {c : ℝ} {n : ℕ} (h : c ≤ f n) :
    firstAlarm f c ≤ (n : ℕ∞) :=
  sInf_le ⟨n, h, rfl⟩

lemma firstAlarm_eq_top_iff {f : ℕ → ℝ} {c : ℝ} :
    firstAlarm f c = ⊤ ↔ ∀ n, ¬ (c ≤ f n) := by
  constructor
  · intro h n hn
    have h2 := firstAlarm_le_of_le (f := f) (c := c) hn
    rw [h] at h2
    simp at h2
  · intro h
    have : ((fun n : ℕ => (n : ℕ∞)) '' {n : ℕ | c ≤ f n}) = ∅ := by
      ext x; simp only [Set.mem_image, Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
      rintro ⟨n, hn, rfl⟩; exact h n hn
    simp [firstAlarm, this]

/-- `firstAlarm` computes the least crossing index. -/
lemma firstAlarm_eq_of_isLeast {f : ℕ → ℝ} {c : ℝ} {m : ℕ}
    (h : IsLeast {n : ℕ | c ≤ f n} m) : firstAlarm f c = (m : ℕ∞) := by
  refine le_antisymm (sInf_le ⟨m, h.1, rfl⟩) (le_sInf ?_)
  rintro x ⟨k, hk, rfl⟩
  simp only
  exact_mod_cast h.2 hk

/-- A path that dominates another alarms no later than it. -/
lemma firstAlarm_mono {f g : ℕ → ℝ} (h : ∀ n, g n ≤ f n) (c : ℝ) :
    firstAlarm f c ≤ firstAlarm g c := by
  refine sInf_le_sInf ?_
  rintro x ⟨n, hn, rfl⟩
  exact ⟨n, (hn.trans (h n) : c ≤ f n), rfl⟩

/-- The embedded change-time-`ν` likelihood-ratio component `π_ν ∏_{i=ν}^{n} Λ_i`. -/
noncomputable def component (Λ : ℕ → Ω → ℝ) (ν : ℕ) (n : ℕ) (ω : Ω) : ℝ :=
  changePrior ν * ∏ i ∈ Finset.Icc ν n, Λ i ω

/-- The evidence boundary `a_ν = log(1/(α π_ν))` of Equation (6). -/
noncomputable def evidenceBoundary (α : ℝ) (ν : ℕ) : ℝ := Real.log (1 / (α * changePrior ν))

/-- **C3** (`change_component_dominance_and_penalty`, Equations 5–6).

1. Equation (5): the mixture dominates the embedded change-time-`ν` component pathwise.
2. Consequently the mixture alarm time at threshold `1/α` is never later than the alarm
   time of that component ("the mixture stops no later than the embedded true-change
   component").
3. Equation (6): the evidence the component must accumulate is
   `a_ν = log(1/α) + log[ν(ν+1)]`, exhibiting the late-change penalty `log[ν(ν+1)]`. -/
theorem change_component_dominance_and_penalty (Λ : ℕ → Ω → ℝ) (hΛ : ∀ n ω, 0 ≤ Λ n ω)
    {ν : ℕ} (hν : 1 ≤ ν) {α : ℝ} (hα : 0 < α) :
    (∀ n ω, component Λ ν n ω ≤ mixture Λ n ω) ∧
    (∀ ω, firstAlarm (fun n => mixture Λ n ω) (1 / α)
        ≤ firstAlarm (fun n => component Λ ν n ω) (1 / α)) ∧
    evidenceBoundary α ν = Real.log (1 / α) + Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) := by
  have hdom : ∀ n ω, component Λ ν n ω ≤ mixture Λ n ω := fun n ω =>
    component_le_mixture hΛ hν n ω
  refine ⟨hdom, fun ω => firstAlarm_mono (fun n => hdom n ω) _, ?_⟩
  have hνR : (1 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
  have hν1 : (0 : ℝ) < (ν : ℝ) * ((ν : ℝ) + 1) := by nlinarith
  have hπ : changePrior ν = 1 / ((ν : ℝ) * ((ν : ℝ) + 1)) := rfl
  have hne1 : (1 / α) ≠ 0 := by positivity
  have hne2 : ((ν : ℝ) * ((ν : ℝ) + 1)) ≠ 0 := ne_of_gt hν1
  have hrw : 1 / (α * changePrior ν) = (1 / α) * ((ν : ℝ) * ((ν : ℝ) + 1)) := by
    rw [hπ]
    field_simp
  rw [evidenceBoundary, hrw, Real.log_mul hne1 hne2]

/-- Equation (6) read as an evidence threshold: for a strictly positive likelihood-ratio
path, the change-time-`ν` component reaches the alarm level `1/α` exactly when the
post-change log-likelihood sum reaches the boundary `a_ν`. -/
lemma component_crossing_iff_evidence (Λ : ℕ → Ω → ℝ) {ν : ℕ} (hν : 1 ≤ ν) {α : ℝ}
    (hα : 0 < α) (ω : Ω) (hpos : ∀ i, 0 < Λ i ω) (n : ℕ) :
    (1 / α ≤ component Λ ν n ω) ↔
      evidenceBoundary α ν ≤ ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) := by
  have hprodpos : 0 < ∏ i ∈ Finset.Icc ν n, Λ i ω :=
    Finset.prod_pos (fun i _ => hpos i)
  have hπpos : 0 < changePrior ν := changePrior_pos hν
  have hcomp : 0 < component Λ ν n ω := mul_pos hπpos hprodpos
  have hlogprod : Real.log (∏ i ∈ Finset.Icc ν n, Λ i ω)
      = ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) :=
    Real.log_prod (fun i _ => ne_of_gt (hpos i))
  have hcompl : Real.log (component Λ ν n ω)
      = Real.log (changePrior ν) + ∑ i ∈ Finset.Icc ν n, Real.log (Λ i ω) := by
    rw [component, Real.log_mul (ne_of_gt hπpos) (ne_of_gt hprodpos), hlogprod]
  have hb : evidenceBoundary α ν = Real.log (1 / α) - Real.log (changePrior ν) := by
    rw [evidenceBoundary, one_div, Real.log_inv, Real.log_mul (ne_of_gt hα)
      (ne_of_gt hπpos), one_div, Real.log_inv]
    ring
  constructor
  · intro h
    have := Real.log_le_log (by positivity) h
    rw [hcompl] at this
    rw [hb]
    have h2 : Real.log (1 / α) ≤ Real.log (component Λ ν n ω) := by
      rw [hcompl]; exact this
    rw [hcompl] at h2
    linarith
  · intro h
    rw [hb] at h
    have h2 : Real.log (1 / α) ≤ Real.log (component Λ ν n ω) := by
      rw [hcompl]; linarith
    have := Real.exp_le_exp.2 h2
    rwa [Real.exp_log (by positivity), Real.exp_log hcomp] at this

/-- The late-change penalty `log[ν(ν+1)]` is asymptotically `2 log ν` (difference form). -/
theorem late_change_penalty_sub_tendsto_zero :
    Tendsto (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν)
      atTop (𝓝 0) := by
  have hev : (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν)
      =ᶠ[atTop] (fun ν : ℕ => Real.log (1 + 1 / (ν : ℝ))) := by
    filter_upwards [eventually_ge_atTop 1] with ν hν
    have hνR : (1 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
    have hpos : (0 : ℝ) < (ν : ℝ) := by linarith
    have h1 : Real.log ((ν : ℝ) * ((ν : ℝ) + 1))
        = Real.log ν + Real.log ((ν : ℝ) + 1) :=
      Real.log_mul (ne_of_gt hpos) (by positivity)
    have h2 : (1 : ℝ) + 1 / (ν : ℝ) = ((ν : ℝ) + 1) / (ν : ℝ) := by
      field_simp
    rw [h1, h2, Real.log_div (by positivity) (ne_of_gt hpos)]
    ring
  refine Tendsto.congr' hev.symm ?_
  have h1 : Tendsto (fun ν : ℕ => 1 + 1 / (ν : ℝ)) atTop (𝓝 1) := by
    have h0 : Tendsto (fun n : ℕ => 1 / (n : ℝ)) atTop (𝓝 0) :=
      tendsto_one_div_atTop_nhds_zero_nat
    simpa using (tendsto_const_nhds (x := (1 : ℝ)) (f := (atTop : Filter ℕ))).add h0
  have := (Real.continuousAt_log (by norm_num : (1 : ℝ) ≠ 0)).tendsto.comp h1
  simpa using this

/-- The late-change penalty `log[ν(ν+1)]` is asymptotically `2 log ν` (ratio form). -/
theorem late_change_penalty_ratio_tendsto_one :
    Tendsto (fun ν : ℕ => Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) / (2 * Real.log ν))
      atTop (𝓝 1) := by
  have hlog : Tendsto (fun ν : ℕ => 2 * Real.log ν) atTop atTop := by
    have h : Tendsto (fun ν : ℕ => Real.log ν) atTop atTop :=
      Real.tendsto_log_atTop.comp (tendsto_natCast_atTop_atTop (R := ℝ))
    exact Filter.Tendsto.const_mul_atTop (by norm_num : (0:ℝ) < 2) h
  have hquot : Tendsto
      (fun ν : ℕ => (Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν) / (2 * Real.log ν))
      atTop (𝓝 0) := late_change_penalty_sub_tendsto_zero.div_atTop hlog
  have hev : ∀ᶠ ν : ℕ in atTop,
      1 + (Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) - 2 * Real.log ν) / (2 * Real.log ν)
        = Real.log ((ν : ℝ) * ((ν : ℝ) + 1)) / (2 * Real.log ν) := by
    filter_upwards [eventually_ge_atTop 2] with ν hν
    have hνR : (2 : ℝ) ≤ (ν : ℝ) := by exact_mod_cast hν
    have hlogpos : 0 < Real.log ν := Real.log_pos (by linarith)
    field_simp
    ring
  refine Tendsto.congr' hev ?_
  simpa using (tendsto_const_nhds (x := (1 : ℝ)) (f := (atTop : Filter ℕ))).add hquot

end Viridis.Run129.PaperFormalization
