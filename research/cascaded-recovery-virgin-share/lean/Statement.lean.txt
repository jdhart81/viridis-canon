import Mathlib

/-!
# P3 · Cascaded recovery: virgin share after `n` recovery stages

Model: a material stream passes through `n` recovery stages in series. Stage `i` recovers the
fraction `r i ∈ [0, 1]` of what reaches it, so the fraction that passes it unrecovered is
`1 - r i`. The share of the original stream that still has to be met by virgin material after
the cascade (the *virgin share*) is the product `∏ i, (1 - r i)`.

`Statement` (for every `n` and every `r : Fin n → ℝ` with all `r i ∈ [0, 1]`):
1. `0 ≤ ∏ (1 - r i) ≤ 1`;
2. for every uniform upper bound `m` with `r i ≤ m ≤ 1`: `(1 - m)^n ≤ ∏ (1 - r i)`;
   in particular `(1 - max_i r i)^n ≤ ∏ (1 - r i)`, where the maximum is `⨆ i, r i`;
3. for every stage `j`: `∏ (1 - r i) ≤ 1 - r j` (the cascade is never worse than any one stage);
4. strictness: if `j` has `r j < 1` and some *other* stage `k ≠ j` has `r k > 0`, then
   `∏ (1 - r i) < 1 - r j`.

For `n = 0` the maximum `⨆ i, r i` over the empty type is `0` in Mathlib's conditionally
complete lattice `ℝ`, and both sides of part 2 equal `1`.

No claim is made about any real recovery rate or material.
-/

namespace ViridisStatements.P3.CascadedRecovery

/-- Virgin share after a cascade of `n` stages with recovery fractions `r`. -/
def virginShare {n : ℕ} (r : Fin n → ℝ) : ℝ := ∏ i, (1 - r i)

/-- **Proposed sealed target `P3.CascadedRecovery`.** -/
def Statement : Prop :=
  ∀ (n : ℕ) (r : Fin n → ℝ), (∀ i, 0 ≤ r i) → (∀ i, r i ≤ 1) →
    (0 ≤ virginShare r ∧ virginShare r ≤ 1) ∧
    (∀ m : ℝ, (∀ i, r i ≤ m) → m ≤ 1 → (1 - m) ^ n ≤ virginShare r) ∧
    (1 - ⨆ i, r i) ^ n ≤ virginShare r ∧
    (∀ j, virginShare r ≤ 1 - r j) ∧
    (∀ j k, k ≠ j → 0 < r k → r j < 1 → virginShare r < 1 - r j)

/-! ## Sanity checks -/

/-- Two stages recovering one half each leave a virgin share of `1/4`, which lies between the
lower bound `(1 - 1/2)^2 = 1/4` and the single-stage share `1/2`, strictly below the latter. -/
example : virginShare ![(1/2 : ℝ), 1/2] = 1/4 ∧ (1 - (1/2 : ℝ)) ^ 2 ≤ 1/4 ∧
    virginShare ![(1/2 : ℝ), 1/2] < 1 - 1/2 := by
  norm_num [virginShare, Fin.prod_univ_two]

/-- Three heterogeneous stages `1/2, 1/4, 0`: share `3/8`, above `(1 - 1/2)^3 = 1/8`. -/
example : virginShare ![(1/2 : ℝ), 1/4, 0] = 3/8 ∧
    (1 - (1/2 : ℝ)) ^ 3 < virginShare ![(1/2 : ℝ), 1/4, 0] := by
  simp only [virginShare, Fin.prod_univ_three, Matrix.cons_val_zero, Matrix.cons_val_one,
    Matrix.cons_val_two, Matrix.head_cons, Matrix.tail_cons]
  norm_num

/-- Negative control for strictness: if every *other* stage recovers nothing, the cascade
equals the single stage, so part 4 genuinely needs some `r k > 0` with `k ≠ j`. -/
example : virginShare ![(0 : ℝ), 1/2] = 1 - 1/2 := by
  norm_num [virginShare, Fin.prod_univ_two]

/-- Negative control for strictness: if stage `j` recovers everything (`r j = 1`) the share is
`0 = 1 - r j`, so part 4 genuinely needs `r j < 1`. -/
example : virginShare ![(1/2 : ℝ), 1] = 1 - 1 := by
  norm_num [virginShare, Fin.prod_univ_two]

/-- Negative control: `r i ≤ 1` is needed. An out-of-range stage `r = 2` makes the
"virgin share" negative. -/
example : virginShare ![(2 : ℝ), 1/2] < 0 := by
  norm_num [virginShare, Fin.prod_univ_two]

/-- Negative control: `0 ≤ r i` is needed for part 3. A "stage" with `r = -1` (one that adds
demand) pushes the share above the other stage's share. -/
example : 1 - (1/2 : ℝ) < virginShare ![(-1 : ℝ), 1/2] := by
  norm_num [virginShare, Fin.prod_univ_two]

end ViridisStatements.P3.CascadedRecovery
