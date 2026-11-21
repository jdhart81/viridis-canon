import Mathlib
import ViridisStatements.P3.LoopMassBalance

namespace Candidate

open Filter Topology
open ViridisStatements.P3.LoopMassBalance

/-- One-step gap recursion: `S(t+1) - S* = ρ · (S(t) - S*)`. -/
theorem gap_succ (ρ r D S0 : ℝ) (hρ : ρ < 1) (t : ℕ) :
    stock ρ r D S0 (t + 1) - steadyStock ρ r D
      = ρ * (stock ρ r D S0 t - steadyStock ρ r D) := by
  have h : (1 - ρ) ≠ 0 := by linarith
  simp only [stock, steadyStock]
  field_simp
  ring

/-- Closed form of the stock gap. -/
theorem gap_closed (ρ r D S0 : ℝ) (hρ : ρ < 1) (t : ℕ) :
    stock ρ r D S0 t - steadyStock ρ r D = ρ ^ t * (S0 - steadyStock ρ r D) := by
  induction t with
  | zero => simp [stock]
  | succ n ih => rw [gap_succ ρ r D S0 hρ, ih, pow_succ]; ring

/-- Cumulative virgin input equals `T·D·(1 - r)`. -/
theorem cumulative_eq (D r : ℝ) (T : ℕ) :
    cumulativeVirgin D r T = (T : ℝ) * D * (1 - r) := by
  simp [cumulativeVirgin, virgin, Finset.sum_const, Finset.card_range, nsmul_eq_mul]
  ring

/-- Convergence of the stock to the steady stock. -/
theorem stock_tendsto (ρ r D S0 : ℝ) (h0 : 0 ≤ ρ) (hρ : ρ < 1) :
    Tendsto (stock ρ r D S0) atTop (𝓝 (steadyStock ρ r D)) := by
  have hp : Tendsto (fun t : ℕ => ρ ^ t) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one h0 hρ
  have hg : Tendsto (fun t : ℕ => ρ ^ t * (S0 - steadyStock ρ r D) + steadyStock ρ r D)
      atTop (𝓝 (0 * (S0 - steadyStock ρ r D) + steadyStock ρ r D)) :=
    (hp.mul_const _).add_const _
  rw [zero_mul, zero_add] at hg
  refine hg.congr' (Eventually.of_forall fun t => ?_)
  have := gap_closed ρ r D S0 hρ t
  linarith

theorem main : ViridisStatements.P3.LoopMassBalance.Statement := by
  refine ⟨?_, ?_⟩
  · intro D r ρ S0 hD hr0 hr1 hρ0 hρ1
    refine ⟨⟨?_, ?_⟩, gap_closed ρ r D S0 hρ1, stock_tendsto ρ r D S0 hρ0 hρ1,
      cumulative_eq D r⟩
    · unfold virgin; exact mul_nonneg hD (by linarith)
    · unfold virgin; nlinarith
  · intro D T hD hT a _ b _ hab
    simp only [cumulative_eq]
    have hT' : (0 : ℝ) < T := by exact_mod_cast hT
    have : 0 < (T : ℝ) * D := mul_pos hT' hD
    nlinarith

end Candidate
