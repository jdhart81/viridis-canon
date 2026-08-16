import Mathlib

/-!
# The heavy-tailed change-time prior of Run-129

This file formalizes Equation (1) of the sealed paper `SEALED_paper.tex`:

  `π_k = 1 / (k (k+1))`,  `t_n = ∑_{k > n} π_k = 1 / (n+1)`.

`changePrior` is `π` and `priorTail` is `t`.  Both are defined for every natural index;
the paper only uses `k ≥ 1` for `π` (and `changePrior 0 = 0` in Lean, which is harmless
since the index `0` never occurs in the recursion).

The two facts that the rest of the development needs are

* `changePrior_add_priorTail`: `π_{n+1} + t_{n+1} = t_n` (the identity `π_n + t_n = t_{n-1}`
  used in the martingale computation), and
* `hasSum_changePrior_tail`: `t_n` really is the tail mass `∑_{k > n} π_k` of the prior,
  so in particular (`hasSum_changePrior`) `π` is a probability distribution on `{1, 2, …}`.
-/

namespace Viridis.Run129.PaperFormalization

open scoped Topology
open Filter

/-- The heavy-tailed change-time prior `π_k = 1 / (k (k+1))` of Equation (1). -/
noncomputable def changePrior (k : ℕ) : ℝ := 1 / ((k : ℝ) * (k + 1))

/-- The prior tail mass `t_n = ∑_{k>n} π_k = 1 / (n+1)` of Equation (1). -/
noncomputable def priorTail (n : ℕ) : ℝ := 1 / ((n : ℝ) + 1)

@[simp] lemma priorTail_zero : priorTail 0 = 1 := by norm_num [priorTail]

lemma priorTail_pos (n : ℕ) : 0 < priorTail n := by
  have : (0 : ℝ) < (n : ℝ) + 1 := by positivity
  simpa [priorTail] using this

lemma changePrior_nonneg (k : ℕ) : 0 ≤ changePrior k := by
  unfold changePrior
  positivity

lemma changePrior_pos {k : ℕ} (hk : 1 ≤ k) : 0 < changePrior k := by
  have hk' : (1 : ℝ) ≤ (k : ℝ) := by exact_mod_cast hk
  have h : (0 : ℝ) < (k : ℝ) * ((k : ℝ) + 1) := by nlinarith
  exact div_pos one_pos h

/-- `π_k = 1/k - 1/(k+1)` for `k ≥ 1`; stated in the shifted form used for telescoping. -/
lemma changePrior_succ_eq_sub (k : ℕ) :
    changePrior (k + 1) = 1 / ((k : ℝ) + 1) - 1 / ((k : ℝ) + 2) := by
  have h1 : ((k : ℝ) + 1) ≠ 0 := by positivity
  have h2 : ((k : ℝ) + 2) ≠ 0 := by positivity
  unfold changePrior
  push_cast
  field_simp
  ring

/-- Equation (1): `π_{n+1} + t_{n+1} = t_n`, i.e. `π_n + t_n = t_{n-1}`. -/
lemma changePrior_add_priorTail (n : ℕ) :
    changePrior (n + 1) + priorTail (n + 1) = priorTail n := by
  have h := changePrior_succ_eq_sub n
  have h2 : priorTail (n + 1) = 1 / ((n : ℝ) + 2) := by
    simp [priorTail]; ring_nf
  rw [h, h2]
  simp [priorTail]

/-- Equation (1): the tail mass identity `∑_{k>n} π_k = t_n`. -/
theorem hasSum_changePrior_tail (n : ℕ) :
    HasSum (fun j : ℕ => changePrior (n + 1 + j)) (priorTail n) := by
  set f : ℕ → ℝ := fun j => 1 / ((n : ℝ) + 1 + j) with hf
  have hterm : ∀ j : ℕ, changePrior (n + 1 + j) = f j - f (j + 1) := by
    intro j
    have := changePrior_succ_eq_sub (n + j)
    have hcast : ((n + 1 + j : ℕ) : ℝ) = ((n + j : ℕ) : ℝ) + 1 := by push_cast; ring
    have h1 : changePrior (n + 1 + j) = changePrior ((n + j) + 1) := by
      congr 1; omega
    rw [h1, this]
    simp only [hf]
    push_cast
    ring_nf
  have hpartial : ∀ m : ℕ, ∑ j ∈ Finset.range m, changePrior (n + 1 + j)
      = priorTail n - f m := by
    intro m
    simp only [hterm]
    rw [Finset.sum_range_sub' f m]
    simp [hf, priorTail]
  have hsummable : Summable (fun j : ℕ => changePrior (n + 1 + j)) := by
    refine summable_of_sum_range_le (c := priorTail n) (fun j => changePrior_nonneg _) (fun m => ?_)
    rw [hpartial m]
    have : 0 ≤ f m := by
      simp only [hf]
      positivity
    linarith
  rw [hsummable.hasSum_iff_tendsto_nat]
  have hlim : Tendsto f atTop (𝓝 0) := by
    simp only [hf]
    have : Tendsto (fun m : ℕ => ((n : ℝ) + 1 + m)) atTop atTop := by
      apply Filter.tendsto_atTop_add_const_left
      exact tendsto_natCast_atTop_atTop
    exact this.inv_tendsto_atTop.congr (fun m => by simp [one_div])
  have := (tendsto_const_nhds (x := priorTail n) (f := atTop (α := ℕ))).sub hlim
  simpa [hpartial, sub_zero] using this

/-- The prior `π` is a probability distribution on the change times `{1, 2, …}`. -/
theorem hasSum_changePrior : HasSum (fun j : ℕ => changePrior (j + 1)) 1 := by
  have h := hasSum_changePrior_tail 0
  simpa [add_comm] using h

end Viridis.Run129.PaperFormalization
