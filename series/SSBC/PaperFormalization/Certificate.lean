import PaperFormalization.Hall

/-!
# The Seed-Source Bottleneck Certificate — formal statements of the frozen targets

This file formalizes the preregistered model of `SEALED_paper.tex` (Run-130) and the four
frozen formal targets listed in `STATEMENT_CONTRACT.md`:

* `C1` : `seed_routing_common_fraction_eq_min_cut_ratio`
* `C2` : `seed_routing_feasible_iff_cut_conditions`
* `C3` : `capacity_outside_active_bottleneck_irrelevant`
* `C4` : `scenario_intersection_certificate_le_each_scenario`

## The preregistered model (paper, Section 2)

`σ` is the finite set `I` of restoration sites, `τ` is the finite set `J` of seed sources,
`d : σ → ℝ` are the site demands (the paper assumes `d i > 0`), `s : τ → ℝ` are the source
capacities (the paper assumes `s j ≥ 0`), and `E : τ → σ → Bool` is the frozen eligibility
graph `E ⊆ J × I` (`E j i = true` means the transfer `(j, i)` is eligible).

A routing `x : τ → σ → ℝ` is admissible for the common fulfillment fraction `lam` when it is
nonnegative, supported on `E`, satisfies the supply constraints (paper eq. 1) and the demand
constraints (paper eq. 2). This is `IsFeasibleFraction`.

`certificate E d s` is the right-hand side of the boxed equation (3) of the paper,
`min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`, realized as the minimum of the finite set of reals
`{1} ∪ {S(N(U))/D(U) : ∅ ≠ U ⊆ I}`.

Non-vacuity witnesses for all four targets are in `PaperFormalization/Witnesses.lean`.
-/

namespace Viridis.Run130

open Finset Viridis.Run130.Hall

variable {σ τ : Type*} [Fintype σ] [Fintype τ]

/-! ## Model definitions -/

/-- The eligible neighbourhood `N(U) = {j ∈ J : ∃ i ∈ U, (j,i) ∈ E}` of a set of sites. -/
abbrev nbhd (E : τ → σ → Bool) (U : Finset σ) : Finset τ := nbhdOn Finset.univ E U

/-- `D(U) = ∑_{i ∈ U} d i`. -/
abbrev demand (d : σ → ℝ) (U : Finset σ) : ℝ := dem d U

/-- `S(C) = ∑_{j ∈ C} s j`. -/
abbrev supply (s : τ → ℝ) (C : Finset τ) : ℝ := cap s C

/-- Paper equations (1) and (2): a common fulfillment fraction `lam` is *feasible* when some
nonnegative routing supported on the eligibility graph respects every source capacity and
delivers at least `lam * d i` to every site `i`. -/
def IsFeasibleFraction (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) (lam : ℝ) : Prop :=
  ∃ x : τ → σ → ℝ,
    (∀ j i, 0 ≤ x j i) ∧
    (∀ j i, ¬ E j i → x j i = 0) ∧
    (∀ j, ∑ i, x j i ≤ s j) ∧
    (∀ i, lam * d i ≤ ∑ j, x j i)

/-- The finite set of reals `{1} ∪ {S(N(U))/D(U) : ∅ ≠ U ⊆ I}`. -/
noncomputable def cutRatios (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) : Finset ℝ :=
  insert 1 ((Finset.univ.filter (fun U : Finset σ => U.Nonempty)).image
    (fun U => supply s (nbhd E U) / demand d U))

lemma cutRatios_nonempty (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) :
    (cutRatios E d s).Nonempty := ⟨1, Finset.mem_insert_self _ _⟩

/-- The cut certificate of the paper, boxed equation (3):
`λ* = min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`. -/
noncomputable def certificate (E : τ → σ → Bool) (d : σ → ℝ) (s : τ → ℝ) : ℝ :=
  (cutRatios E d s).min' (cutRatios_nonempty E d s)

/-! ## Elementary properties of the certificate -/

variable {E : τ → σ → Bool} {d : σ → ℝ} {s : τ → ℝ}

lemma ratio_mem_cutRatios {U : Finset σ} (hU : U.Nonempty) :
    supply s (nbhd E U) / demand d U ∈ cutRatios E d s :=
  Finset.mem_insert_of_mem (Finset.mem_image_of_mem _ (by simp [hU]))

lemma certificate_le_one : certificate E d s ≤ 1 :=
  Finset.min'_le _ _ (Finset.mem_insert_self _ _)

lemma certificate_le_ratio {U : Finset σ} (hU : U.Nonempty) :
    certificate E d s ≤ supply s (nbhd E U) / demand d U :=
  Finset.min'_le _ _ (ratio_mem_cutRatios hU)

lemma le_certificate {t : ℝ} (h1 : t ≤ 1)
    (h2 : ∀ U : Finset σ, U.Nonempty → t ≤ supply s (nbhd E U) / demand d U) :
    t ≤ certificate E d s := by
  refine Finset.le_min' _ _ _ ?_
  intro y hy
  rcases Finset.mem_insert.1 hy with rfl | hy
  · exact h1
  · obtain ⟨U, hU, rfl⟩ := Finset.mem_image.1 hy
    exact h2 U (by simpa using hU)

omit [Fintype σ] in
lemma demand_pos {U : Finset σ} (hd : ∀ i, 0 < d i) (hU : U.Nonempty) : 0 < demand d U :=
  Finset.sum_pos (fun i _ => hd i) hU

lemma certificate_nonneg (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    0 ≤ certificate E d s := by
  refine le_certificate zero_le_one ?_
  intro U hU
  exact div_nonneg (cap_nonneg fun j _ => hs j) (demand_pos hd hU).le

/-- `λ* D(U) ≤ S(N(U))` for every nonempty `U`: the certificate satisfies every cut. -/
lemma certificate_mul_demand_le (hd : ∀ i, 0 < d i) {U : Finset σ} (hU : U.Nonempty) :
    certificate E d s * demand d U ≤ supply s (nbhd E U) :=
  (le_div_iff₀ (demand_pos hd hU)).1 (certificate_le_ratio hU)

/-- A convenient way to evaluate the certificate: if `U₀` is nonempty, its ratio is at most
`1`, and its ratio is minimal, then the certificate equals that ratio. -/
lemma certificate_eq_ratio_of_min {U₀ : Finset σ} (hU₀ : U₀.Nonempty)
    (h1 : supply s (nbhd E U₀) / demand d U₀ ≤ 1)
    (hmin : ∀ U : Finset σ, U.Nonempty →
      supply s (nbhd E U₀) / demand d U₀ ≤ supply s (nbhd E U) / demand d U) :
    certificate E d s = supply s (nbhd E U₀) / demand d U₀ :=
  le_antisymm (certificate_le_ratio hU₀) (le_certificate h1 hmin)

/-! ## The two directions of the cut equivalence -/

/-- Any feasible common fraction satisfies every cut condition: `lam D(U) ≤ S(N(U))`.
This is the easy ("min-cut is an upper bound") half of Proposition 1. -/
lemma cut_le_of_feasible {lam : ℝ} (h : IsFeasibleFraction E d s lam) (U : Finset σ) :
    lam * demand d U ≤ supply s (nbhd E U) := by
  obtain ⟨x, hx0, hxsupp, hxcol, hxrow⟩ := h
  have step1 : lam * demand d U ≤ ∑ i ∈ U, ∑ j, x j i := by
    have hms : lam * demand d U = ∑ i ∈ U, lam * d i := Finset.mul_sum ..
    rw [hms]
    exact Finset.sum_le_sum fun i _ => hxrow i
  have step2 : ∑ i ∈ U, ∑ j, x j i = ∑ j, ∑ i ∈ U, x j i := Finset.sum_comm
  have step3 : ∑ j, ∑ i ∈ U, x j i = ∑ j ∈ nbhd E U, ∑ i ∈ U, x j i := by
    refine (Finset.sum_subset (Finset.subset_univ _) ?_).symm
    intro j _ hj
    refine Finset.sum_eq_zero fun i hi => ?_
    refine hxsupp j i ?_
    intro hE
    exact hj (mem_nbhdOn.2 ⟨Finset.mem_univ _, i, hi, hE⟩)
  have step4 : ∑ j ∈ nbhd E U, ∑ i ∈ U, x j i ≤ supply s (nbhd E U) := by
    refine Finset.sum_le_sum fun j _ => ?_
    refine le_trans ?_ (hxcol j)
    exact Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ _)
      (fun i _ _ => hx0 j i)
  linarith [step1, step2 ▸ step1, step3 ▸ step2 ▸ step1]

/-- If every cut condition holds for `lam` then `lam` is feasible.  This is the hard
("max-flow attains the min cut") half of Proposition 1; it rests on the capacitated Hall
theorem proved in `PaperFormalization/Hall.lean`. -/
lemma feasible_of_cut_le [DecidableEq σ] [DecidableEq τ] {lam : ℝ} (hlam : 0 ≤ lam) (hd : ∀ i, 0 ≤ d i) (hs : ∀ j, 0 ≤ s j)
    (hcut : ∀ U : Finset σ, U.Nonempty → lam * demand d U ≤ supply s (nbhd E U)) :
    IsFeasibleFraction E d s lam := by
  obtain ⟨x, hx⟩ := exists_routing_of_hall (Finset.univ : Finset σ) (Finset.univ : Finset τ)
    E (fun i => lam * d i) s
    (fun i _ => mul_nonneg hlam (hd i)) (fun j _ => hs j)
    (by
      intro U _
      rcases U.eq_empty_or_nonempty with rfl | hU
      · simp
      · have hmul : dem (fun i => lam * d i) U = lam * demand d U :=
          (Finset.mul_sum ..).symm
        rw [hmul]
        exact hcut U hU)
  refine ⟨x, hx.nonneg, ?_, ?_, ?_⟩
  · intro j i hE
    exact hx.support j i (by tauto)
  · intro j
    exact hx.cols j (Finset.mem_univ _)
  · intro i
    exact le_of_eq (hx.rows i (Finset.mem_univ _)).symm

/-! ## C1 — the cut certificate -/

/-- **C1** (`seed_routing_common_fraction_eq_min_cut_ratio`, paper Proposition 1, boxed
equation (3)).  Under the preregistered continuous one-period model, the maximum common
fulfillment fraction exists and equals
`min {1, min_{∅ ≠ U ⊆ I} S(N(U))/D(U)}`. -/
theorem seed_routing_common_fraction_eq_min_cut_ratio [DecidableEq σ] [DecidableEq τ]
    (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsGreatest {lam : ℝ | 0 ≤ lam ∧ lam ≤ 1 ∧ IsFeasibleFraction E d s lam}
      (certificate E d s) := by
  constructor
  · refine ⟨certificate_nonneg hd hs, certificate_le_one, ?_⟩
    refine feasible_of_cut_le (certificate_nonneg hd hs) (fun i => (hd i).le) hs ?_
    intro U hU
    exact certificate_mul_demand_le hd hU
  · rintro lam ⟨-, hlam1, hfeas⟩
    refine le_certificate hlam1 ?_
    intro U hU
    exact (le_div_iff₀ (demand_pos hd hU)).2 (cut_le_of_feasible hfeas U)

/-! ## C2 — the capacitated Hall condition -/

/-- **C2** (`seed_routing_feasible_iff_cut_conditions`, paper equation (4)).  Full demand
(`lam = 1`) is feasible exactly when every nonempty set of sites passes the capacitated Hall
condition `D(U) ≤ S(N(U))`. -/
theorem seed_routing_feasible_iff_cut_conditions [DecidableEq σ] [DecidableEq τ] (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) :
    IsFeasibleFraction E d s 1 ↔
      ∀ U : Finset σ, U.Nonempty → demand d U ≤ supply s (nbhd E U) := by
  constructor
  · intro h U _
    have := cut_le_of_feasible h U
    linarith
  · intro h
    refine feasible_of_cut_le zero_le_one (fun i => (hd i).le) hs ?_
    intro U hU
    have := h U hU
    linarith

/-! ## Monotonicity of the certificate -/

/-- Adding capacity cannot decrease the certificate. -/
lemma certificate_mono_capacity {s' : τ → ℝ} (hd : ∀ i, 0 < d i)
    (hss' : ∀ j, s j ≤ s' j) : certificate E d s ≤ certificate E d s' := by
  refine le_certificate certificate_le_one ?_
  intro U hU
  refine le_trans (certificate_le_ratio hU) ?_
  have hden : 0 < demand d U := demand_pos hd hU
  have hnum : supply s (nbhd E U) ≤ supply s' (nbhd E U) :=
    Finset.sum_le_sum fun j _ => hss' j
  gcongr

/-- Adding eligibility edges cannot decrease the certificate. -/
lemma certificate_mono_edges {F : τ → σ → Bool} (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j)
    (hEF : ∀ j i, E j i → F j i) : certificate E d s ≤ certificate F d s := by
  refine le_certificate certificate_le_one ?_
  intro U hU
  refine le_trans (certificate_le_ratio hU) ?_
  have hden : 0 < demand d U := demand_pos hd hU
  have hnum : supply s (nbhd E U) ≤ supply s (nbhd F U) :=
    cap_mono (nbhdOn_mono_edges hEF U) (fun j _ => hs j)
  gcongr

/-! ## C3 — capacity outside an active bottleneck is irrelevant -/

/-- **C3** (`capacity_outside_active_bottleneck_irrelevant`, paper Corollary 1).
Let `U` be a nonempty set of sites attaining the certificate (an *active* minimizing subset)
with `λ* < 1`.  Increasing the capacity of a single source `j₀ ∉ N(U)` cannot improve the
certificate.

Remarks on the hypotheses, kept exactly as the paper states them:
`hlt` (`λ* < 1`) and `hincr` (the perturbation *increases* the capacity) are recorded because
the paper's Corollary 1 states them, but the proof does not use either: for *any* change of
capacity at a single source outside `N(U)` the certificate cannot rise above its old value.
Together with `certificate_mono_capacity`, `hincr` upgrades this to the equality
`capacity_outside_active_bottleneck_eq` below. -/
theorem capacity_outside_active_bottleneck_irrelevant {s' : τ → ℝ} {U : Finset σ} {j₀ : τ}
    (hU : U.Nonempty)
    (hactive : certificate E d s = supply s (nbhd E U) / demand d U)
    (hlt : certificate E d s < 1)
    (hj₀ : j₀ ∉ nbhd E U)
    (hoff : ∀ j, j ≠ j₀ → s' j = s j)
    (hincr : s j₀ ≤ s' j₀) :
    certificate E d s' ≤ certificate E d s := by
  have hsupply : supply s' (nbhd E U) = supply s (nbhd E U) :=
    Finset.sum_congr rfl fun j hj => hoff j (by rintro rfl; exact hj₀ hj)
  calc certificate E d s' ≤ supply s' (nbhd E U) / demand d U := certificate_le_ratio hU
    _ = supply s (nbhd E U) / demand d U := by rw [hsupply]
    _ = certificate E d s := hactive.symm

/-- The equality form of **C3**: adding capacity at a source outside the neighbourhood of an
active minimizing subset leaves the certificate exactly unchanged. -/
theorem capacity_outside_active_bottleneck_eq {s' : τ → ℝ} {U : Finset σ} {j₀ : τ}
    (hd : ∀ i, 0 < d i)
    (hU : U.Nonempty)
    (hactive : certificate E d s = supply s (nbhd E U) / demand d U)
    (hlt : certificate E d s < 1)
    (hj₀ : j₀ ∉ nbhd E U)
    (hoff : ∀ j, j ≠ j₀ → s' j = s j)
    (hincr : s j₀ ≤ s' j₀) :
    certificate E d s' = certificate E d s := by
  refine le_antisymm
    (capacity_outside_active_bottleneck_irrelevant hU hactive hlt hj₀ hoff hincr) ?_
  refine certificate_mono_capacity hd ?_
  intro j
  by_cases h : j = j₀
  · subst h; exact hincr
  · exact le_of_eq (hoff j h).symm

/-! ## C4 — scenario robustness -/

/-- The intersection `E_∩ = ⋂_k E_k` of a finite family of scenario eligibility graphs. -/
def scenarioIntersection {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) : τ → σ → Bool :=
  fun j i => decide (∀ k, Es k j i)

/-- The union `E_∪ = ⋃_k E_k` of a finite family of scenario eligibility graphs. -/
def scenarioUnion {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) : τ → σ → Bool :=
  fun j i => decide (∃ k, Es k j i)

omit [Fintype σ] [Fintype τ] in
lemma scenarioIntersection_subset {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) (k : κ) :
    ∀ j i, scenarioIntersection Es j i → Es k j i := by
  intro j i h
  simpa using (of_decide_eq_true h) k

omit [Fintype σ] [Fintype τ] in
lemma subset_scenarioUnion {κ : Type*} [Fintype κ] (Es : κ → τ → σ → Bool) (k : κ) :
    ∀ j i, Es k j i → scenarioUnion Es j i := by
  intro j i h
  exact decide_eq_true ⟨k, h⟩

/-- **C4** (`scenario_intersection_certificate_le_each_scenario`, paper equation (5)).
The certificate of the intersection of the scenario eligibility graphs cannot exceed the
certificate of any individual scenario. -/
theorem scenario_intersection_certificate_le_each_scenario {κ : Type*} [Fintype κ]
    (Es : κ → τ → σ → Bool) (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) (k : κ) :
    certificate (scenarioIntersection Es) d s ≤ certificate (Es k) d s :=
  certificate_mono_edges hd hs (scenarioIntersection_subset Es k)

/-- Companion to C4: every scenario certificate is at most the certificate of the union,
which is the precise sense in which the union "can be falsely reassuring". -/
theorem scenario_certificate_le_union {κ : Type*} [Fintype κ]
    (Es : κ → τ → σ → Bool) (hd : ∀ i, 0 < d i) (hs : ∀ j, 0 ≤ s j) (k : κ) :
    certificate (Es k) d s ≤ certificate (scenarioUnion Es) d s :=
  certificate_mono_edges hd hs (subset_scenarioUnion Es k)

end Viridis.Run130
