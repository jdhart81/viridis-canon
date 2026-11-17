import Mathlib
import ViridisStatements.P3.CascadedRecovery

namespace Candidate

open ViridisStatements.P3.CascadedRecovery

/-- Every factor `1 - r i` lies in `[0, 1]`. -/
theorem factor_nonneg {n : ℕ} (r : Fin n → ℝ) (h1 : ∀ i, r i ≤ 1) (i : Fin n) :
    0 ≤ 1 - r i := by linarith [h1 i]

theorem factor_le_one {n : ℕ} (r : Fin n → ℝ) (h0 : ∀ i, 0 ≤ r i) (i : Fin n) :
    1 - r i ≤ 1 := by linarith [h0 i]

/-- Any sub-product of the factors lies in `[0, 1]`. -/
theorem subprod_le_one {n : ℕ} (r : Fin n → ℝ) (h0 : ∀ i, 0 ≤ r i) (h1 : ∀ i, r i ≤ 1)
    (s : Finset (Fin n)) : ∏ i ∈ s, (1 - r i) ≤ 1 :=
  Finset.prod_le_one (fun i _ => factor_nonneg r h1 i) (fun i _ => factor_le_one r h0 i)

theorem subprod_nonneg {n : ℕ} (r : Fin n → ℝ) (h1 : ∀ i, r i ≤ 1)
    (s : Finset (Fin n)) : 0 ≤ ∏ i ∈ s, (1 - r i) :=
  Finset.prod_nonneg (fun i _ => factor_nonneg r h1 i)

/-- Splitting off stage `j`: `virginShare r = (1 - r j) · ∏_{i ≠ j} (1 - r i)`. -/
theorem split {n : ℕ} (r : Fin n → ℝ) (j : Fin n) :
    virginShare r = (1 - r j) * ∏ i ∈ Finset.univ.erase j, (1 - r i) :=
  (Finset.mul_prod_erase Finset.univ (fun i => 1 - r i) (Finset.mem_univ j)).symm

/-- Uniform lower bound `(1 - m)^n ≤ virginShare r`. -/
theorem lower_bound {n : ℕ} (r : Fin n → ℝ) (m : ℝ) (hm : ∀ i, r i ≤ m) (hm1 : m ≤ 1) :
    (1 - m) ^ n ≤ virginShare r := by
  have hc : (1 - m) ^ n = ∏ _i : Fin n, (1 - m) := by
    rw [Finset.prod_const, Finset.card_univ, Fintype.card_fin]
  rw [hc, virginShare]
  exact Finset.prod_le_prod (fun _ _ => by linarith) (fun i _ => by linarith [hm i])

theorem main : ViridisStatements.P3.CascadedRecovery.Statement := by
  intro n r h0 h1
  refine ⟨⟨subprod_nonneg r h1 _, subprod_le_one r h0 h1 _⟩,
    fun m hm hm1 => lower_bound r m hm hm1, ?_, ?_, ?_⟩
  · -- the supremum bound
    rcases Nat.eq_zero_or_pos n with hn | hn
    · subst hn
      simp [virginShare]
    · haveI : Nonempty (Fin n) := ⟨⟨0, hn⟩⟩
      have hbdd : BddAbove (Set.range r) := (Set.finite_range r).bddAbove
      exact lower_bound r _ (fun i => le_ciSup hbdd i) (ciSup_le h1)
  · intro j
    rw [split r j]
    have hP := subprod_le_one r h0 h1 (Finset.univ.erase j)
    have hj := factor_nonneg r h1 j
    nlinarith
  · intro j k hkj hk hj
    rw [split r j]
    have hkmem : k ∈ Finset.univ.erase j := Finset.mem_erase.mpr ⟨hkj, Finset.mem_univ k⟩
    have hsplit := Finset.mul_prod_erase (Finset.univ.erase j) (fun i => 1 - r i) hkmem
    have hQ := subprod_le_one r h0 h1 ((Finset.univ.erase j).erase k)
    have hQ0 := subprod_nonneg r h1 ((Finset.univ.erase j).erase k)
    have hP : ∏ i ∈ Finset.univ.erase j, (1 - r i) < 1 := by
      rw [← hsplit]
      have hk1 := factor_nonneg r h1 k
      nlinarith
    have hj' : 0 < 1 - r j := by linarith
    nlinarith

end Candidate
