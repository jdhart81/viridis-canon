import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Analysis.SpecialFunctions.Log.Basic

set_option autoImplicit false

open scoped BigOperators

namespace Viridis.SchedulerFreeEnergy

noncomputable section

/-- Age vector after serving `j`: the selected component resets and every other component ages once. -/
def nextAge {ι : Type*} [DecidableEq ι]
    (age : ι → ℝ) (j i : ι) : ℝ :=
  if i = j then 0 else age i + 1

/-- Exponential age partition function. -/
def partition {ι : Type*} [Fintype ι]
    (β : ℝ) (age : ι → ℝ) : ℝ :=
  ∑ i, Real.exp (β * age i)

/-- Soft maximum age. -/
def freeEnergy {ι : Type*} [Fintype ι]
    (β : ℝ) (age : ι → ℝ) : ℝ :=
  Real.log (partition β age) / β

/-- Exact reset identity for the post-service partition function. -/
theorem reset_partition_function_identity
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j : ι) :
    partition β (nextAge age j) =
      1 + Real.exp β * (partition β age - Real.exp (β * age j)) := by
  classical
  unfold partition nextAge
  rw [← Finset.add_sum_erase _ (fun i => Real.exp (β * if i = j then 0 else age i + 1))
        (Finset.mem_univ j),
      ← Finset.add_sum_erase _ (fun i => Real.exp (β * age i)) (Finset.mem_univ j)]
  simp only [if_true, mul_zero, Real.exp_zero, add_sub_cancel_left]
  rw [Finset.mul_sum]
  congr 1
  apply Finset.sum_congr rfl
  intro i hi
  rw [if_neg (Finset.ne_of_mem_erase hi), ← Real.exp_add]
  ring_nf

/-- The complementary sum appearing in the reset identity is nonnegative. -/
private theorem partition_sub_exp_nonneg
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j : ι) :
    0 ≤ partition β age - Real.exp (β * age j) := by
  classical
  have h : partition β age - Real.exp (β * age j)
      = ∑ i ∈ Finset.univ.erase j, Real.exp (β * age i) := by
    unfold partition
    rw [← Finset.add_sum_erase _ (fun i => Real.exp (β * age i)) (Finset.mem_univ j)]
    ring
  rw [h]
  exact Finset.sum_nonneg fun i _ => (Real.exp_pos _).le

/-- The post-service partition function is at least one, hence positive. -/
private theorem one_le_partition_nextAge
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j : ι) :
    1 ≤ partition β (nextAge age j) := by
  rw [reset_partition_function_identity]
  have h := partition_sub_exp_nonneg β age j
  have := (Real.exp_pos β).le
  nlinarith

/-- Serving a maximum-age component minimizes next-step soft maximum for positive inverse temperature. -/
theorem max_age_minimizes_next_logsumexp
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j : ι)
    (hβ : 0 < β)
    (hmax : ∀ i, age i ≤ age j) :
    ∀ k, freeEnergy β (nextAge age j) ≤ freeEnergy β (nextAge age k) := by
  intro k
  have hexp : Real.exp (β * age k) ≤ Real.exp (β * age j) :=
    Real.exp_le_exp.mpr (by nlinarith [hmax k])
  have hZ : partition β (nextAge age j) ≤ partition β (nextAge age k) := by
    rw [reset_partition_function_identity, reset_partition_function_identity]
    have hpos := (Real.exp_pos β).le
    nlinarith
  have hpos : (0 : ℝ) < partition β (nextAge age j) :=
    lt_of_lt_of_le zero_lt_one (one_le_partition_nextAge β age j)
  have hlog : Real.log (partition β (nextAge age j)) ≤ Real.log (partition β (nextAge age k)) :=
    Real.log_le_log hpos hZ
  unfold freeEnergy
  gcongr

/-- A unique maximum age gives a unique strict next-step minimizer. -/
theorem unique_max_age_unique_minimizer
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j : ι)
    (hβ : 0 < β)
    (hunique : ∀ i, i ≠ j → age i < age j) :
    ∀ k, k ≠ j →
      freeEnergy β (nextAge age j) < freeEnergy β (nextAge age k) := by
  intro k hk
  have hexp : Real.exp (β * age k) < Real.exp (β * age j) :=
    Real.exp_lt_exp.mpr (by nlinarith [hunique k hk])
  have hZ : partition β (nextAge age j) < partition β (nextAge age k) := by
    rw [reset_partition_function_identity, reset_partition_function_identity]
    have hpos := Real.exp_pos β
    nlinarith
  have hpos : (0 : ℝ) < partition β (nextAge age j) :=
    lt_of_lt_of_le zero_lt_one (one_le_partition_nextAge β age j)
  have hlog : Real.log (partition β (nextAge age j)) < Real.log (partition β (nextAge age k)) :=
    Real.log_lt_log hpos hZ
  unfold freeEnergy
  gcongr

/-- Tied maximum ages give equal next-step potential, so uniqueness is not manufactured. -/
theorem tied_maxima_equal_next_potential
    {ι : Type*} [Fintype ι] [DecidableEq ι]
    (β : ℝ) (age : ι → ℝ) (j k : ι)
    (hage : age j = age k) :
    freeEnergy β (nextAge age j) = freeEnergy β (nextAge age k) := by
  unfold freeEnergy
  rw [reset_partition_function_identity, reset_partition_function_identity, hage]

/-- The soft maximum lies between the attained maximum age and its log-cardinality envelope. -/
theorem logsumexp_bounds_max_age
    (n : ℕ) [NeZero n]
    (β : ℝ) (age : Fin n → ℝ) (j : Fin n)
    (hβ : 0 < β)
    (hmax : ∀ i, age i ≤ age j) :
    age j ≤ freeEnergy β age ∧
      freeEnergy β age ≤ age j + Real.log (n : ℝ) / β := by
  have hnpos : (0 : ℝ) < (n : ℝ) := by
    have : 0 < n := Nat.pos_of_ne_zero (NeZero.ne n)
    exact_mod_cast this
  have hlow : Real.exp (β * age j) ≤ partition β age := by
    unfold partition
    exact Finset.single_le_sum (f := fun i => Real.exp (β * age i))
      (fun i _ => (Real.exp_pos _).le) (Finset.mem_univ j)
  have hZpos : (0 : ℝ) < partition β age := lt_of_lt_of_le (Real.exp_pos _) hlow
  have hhigh : partition β age ≤ (n : ℝ) * Real.exp (β * age j) := by
    unfold partition
    calc ∑ i, Real.exp (β * age i)
        ≤ ∑ _i : Fin n, Real.exp (β * age j) := by
          refine Finset.sum_le_sum ?_
          intro i _
          exact Real.exp_le_exp.mpr (by nlinarith [hmax i])
      _ = (n : ℝ) * Real.exp (β * age j) := by
          simp [Finset.sum_const]
  constructor
  · have h1 : β * age j ≤ Real.log (partition β age) := by
      have := Real.log_le_log (Real.exp_pos (β * age j)) hlow
      rwa [Real.log_exp] at this
    unfold freeEnergy
    rw [le_div_iff₀ hβ]
    linarith [h1]
  · have h2 : Real.log (partition β age) ≤ Real.log (n : ℝ) + β * age j := by
      have := Real.log_le_log hZpos hhigh
      rwa [Real.log_mul (ne_of_gt hnpos) (Real.exp_ne_zero _), Real.log_exp] at this
    unfold freeEnergy
    rw [div_le_iff₀ hβ, add_mul, div_mul_cancel₀ _ (ne_of_gt hβ)]
    linarith

/-- Concrete two-area witness: serving the unique older area strictly lowers the next-step potential. -/
theorem scheduler_free_energy_nonvacuous
    (β : ℝ) (hβ : 0 < β) :
    let age : Fin 2 → ℝ := fun i => if i = 0 then 1 else 0
    freeEnergy β (nextAge age 0) < freeEnergy β (nextAge age 1) := by
  intro age
  have hunique : ∀ i, i ≠ (0 : Fin 2) → age i < age 0 := by
    intro i hi
    fin_cases i
    · exact absurd rfl hi
    · norm_num [age]
  exact unique_max_age_unique_minimizer β age 0 hβ hunique 1 (by decide)

end

end Viridis.SchedulerFreeEnergy
