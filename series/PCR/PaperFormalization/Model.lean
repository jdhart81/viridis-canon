import Mathlib

/-!
# The Run-127 model: definitions and assumptions

This file fixes the definitions used to state the frozen claims of the sealed paper
*The Precautionary Capacity Reserve* (Run-127).

Paper objects formalized here:

* the fixed positive scalars `P`, `k_B`, `T` of the model premise `r ≤ C(D) = P D / (k_B T ln 2)`
  (bundled in `RateModel`);
* the model ceiling `C` (`RateModel.ceiling`), Eq. (1);
* the required capacity `d(r) = (k_B T ln 2 / P) r` (`RateModel.requiredCapacity`), Eq. (2);
* the strict violation event `𝒱(r) = {r > C(D)}` (`RateModel.violationEvent`), Eq. (3);
* the Cantelli factor `√((1-α)/α)` (`cantelliFactor`);
* the two-moment capacity floor `d_α = [μ - σ √((1-α)/α)]_+` (`capacityFloor`), Eq. (4);
* the certified rate `r_α = P d_α / (k_B T ln 2)` (`RateModel.certifiedRate`), Eq. (5);
* the mean plug-in ceiling `r_μ = P μ / (k_B T ln 2)` (`RateModel.meanPlugInCeiling`);
* the coefficient of variation `CV(D) = σ / μ` (`coeffVar`).
-/

namespace Viridis.Run127.PaperFormalization

open MeasureTheory ProbabilityTheory

/-- The Cantelli factor `√((1-α)/α)` attached to a one-period violation budget `α`. -/
noncomputable def cantelliFactor (alpha : ℝ) : ℝ := Real.sqrt ((1 - alpha) / alpha)

/-- The positive part `[x]_+ = max 0 x` used in the paper. -/
def posPart (x : ℝ) : ℝ := max 0 x

/-- The two-moment capacity floor `d_α = [μ - σ √((1-α)/α)]_+` of Eq. (4). -/
noncomputable def capacityFloor (mu sigma alpha : ℝ) : ℝ :=
  posPart (mu - sigma * cantelliFactor alpha)

/-- The coefficient of variation `CV(D) = σ / μ`. -/
noncomputable def coeffVar (mu sigma : ℝ) : ℝ := sigma / mu

lemma cantelliFactor_nonneg (alpha : ℝ) : 0 ≤ cantelliFactor alpha := Real.sqrt_nonneg _

lemma cantelliFactor_pos {alpha : ℝ} (h0 : 0 < alpha) (h1 : alpha < 1) :
    0 < cantelliFactor alpha :=
  Real.sqrt_pos.2 (div_pos (by linarith) h0)

lemma cantelliFactor_sq {alpha : ℝ} (h0 : 0 < alpha) (h1 : alpha < 1) :
    cantelliFactor alpha ^ 2 = (1 - alpha) / alpha :=
  Real.sq_sqrt (le_of_lt (div_pos (by linarith) h0))

lemma capacityFloor_nonneg (mu sigma alpha : ℝ) : 0 ≤ capacityFloor mu sigma alpha :=
  le_max_left _ _

lemma capacityFloor_of_pos {mu sigma alpha : ℝ} (h : 0 < mu - sigma * cantelliFactor alpha) :
    capacityFloor mu sigma alpha = mu - sigma * cantelliFactor alpha :=
  max_eq_right h.le

lemma pos_of_capacityFloor_pos {mu sigma alpha : ℝ} (h : 0 < capacityFloor mu sigma alpha) :
    0 < mu - sigma * cantelliFactor alpha := by
  rcases max_cases (0 : ℝ) (mu - sigma * cantelliFactor alpha) with ⟨he, _⟩ | ⟨he, hle⟩
  · rw [capacityFloor, posPart, he] at h; exact absurd h (lt_irrefl 0)
  · rw [capacityFloor, posPart, he] at h; exact h

/-- Fixed positive scalars of the Viridis rate premise: power `P`, Boltzmann constant `kB`,
temperature `T`.  These are held fixed during the single decision that the paper models. -/
structure RateModel where
  /-- power -/
  P : ℝ
  /-- Boltzmann constant -/
  kB : ℝ
  /-- temperature -/
  T : ℝ
  /-- power is positive -/
  hP : 0 < P
  /-- Boltzmann constant is positive -/
  hkB : 0 < kB
  /-- temperature is positive -/
  hT : 0 < T

namespace RateModel

variable (M : RateModel)

/-- The Landauer cost `k_B T ln 2`, which is positive. -/
lemma erasureCost_pos : 0 < M.kB * M.T * Real.log 2 :=
  mul_pos (mul_pos M.hkB M.hT) (Real.log_pos (by norm_num))

/-- The model ceiling `C(D) = P D / (k_B T ln 2)` of Eq. (1). -/
noncomputable def ceiling (D : ℝ) : ℝ := M.P * D / (M.kB * M.T * Real.log 2)

/-- The required capacity `d(r) = (k_B T ln 2 / P) r` of Eq. (2). -/
noncomputable def requiredCapacity (r : ℝ) : ℝ := M.kB * M.T * Real.log 2 / M.P * r

/-- The certified precautionary rate `r_α = P d_α / (k_B T ln 2)` of Eq. (5). -/
noncomputable def certifiedRate (mu sigma alpha : ℝ) : ℝ :=
  M.ceiling (capacityFloor mu sigma alpha)

/-- The mean plug-in ceiling `r_μ = P μ / (k_B T ln 2)`. -/
noncomputable def meanPlugInCeiling (mu : ℝ) : ℝ := M.ceiling mu

/-- The strict violation event `𝒱(r) = {r > C(D)}` of Eq. (3). -/
def violationEvent {Ω : Type*} (D : Ω → ℝ) (r : ℝ) : Set Ω := {ω | r > M.ceiling (D ω)}

variable {M}

lemma ceiling_lt_ceiling_iff {x y : ℝ} : M.ceiling x < M.ceiling y ↔ x < y := by
  unfold ceiling
  rw [div_lt_div_iff_of_pos_right M.erasureCost_pos, mul_lt_mul_iff_of_pos_left M.hP]

lemma ceiling_smul (c x : ℝ) : c * M.ceiling x = M.ceiling (c * x) := by
  unfold ceiling; ring

lemma requiredCapacity_ceiling (x : ℝ) : M.requiredCapacity (M.ceiling x) = x := by
  have hc : M.kB * M.T * Real.log 2 ≠ 0 := M.erasureCost_pos.ne'
  have hP : M.P ≠ 0 := M.hP.ne'
  unfold requiredCapacity ceiling
  field_simp
  exact mul_div_cancel_left₀ x (mul_pos M.hkB M.hT).ne'

/-- Eq. (3) at the certified rate: the violation event is exactly `{D < d_α}`. -/
lemma violationEvent_certifiedRate {Ω : Type*} (D : Ω → ℝ) (mu sigma alpha : ℝ) :
    M.violationEvent D (M.certifiedRate mu sigma alpha)
      = {ω | D ω < capacityFloor mu sigma alpha} := by
  ext ω
  simp only [violationEvent, certifiedRate, Set.mem_setOf_eq, gt_iff_lt]
  exact ceiling_lt_ceiling_iff

end RateModel

end Viridis.Run127.PaperFormalization
