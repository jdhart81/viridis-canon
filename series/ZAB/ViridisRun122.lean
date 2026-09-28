import Mathlib.Analysis.Convex.Deriv
import Mathlib.Analysis.Calculus.LHopital
import Mathlib.Analysis.Real.Pi.Bounds
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Bounds
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Deriv
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.FunProp
import Mathlib.Tactic.GCongr
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Push
import Mathlib.Tactic.Ring
namespace Viridis.Run122.PaperFormalization
open Real Set Finset
def admissibleIncrement : Set ℝ := Set.Ico 0 (π / 2)
noncomputable def geodesicState (θ : ℝ) : ℝ × ℝ := (Real.cos θ, Real.sin θ)
noncomputable def overlap (u v : ℝ × ℝ) : ℝ := u.1 * v.1 + u.2 * v.2
lemma geodesicState_normalized (θ : ℝ) : overlap (geodesicState θ) (geodesicState θ) = 1 := by
  have h := Real.sin_sq_add_cos_sq θ
  simp only [overlap, geodesicState]
  nlinarith [h]
lemma born_overlap_sq (a b : ℝ) :
    overlap (geodesicState a) (geodesicState b) ^ 2 = Real.cos (b - a) ^ 2 := by
  rw [Real.cos_sub]
  simp only [overlap, geodesicState]
  ring
noncomputable def idealSuccess {N : ℕ} (δ : Fin N → ℝ) : ℝ :=
  ∏ i, Real.cos (δ i) ^ 2
theorem idealSuccess_eq_prod_born {N : ℕ} (θ : Fin (N + 1) → ℝ) :
    ∏ i : Fin N, overlap (geodesicState (θ i.castSucc)) (geodesicState (θ i.succ)) ^ 2
      = idealSuccess (fun i : Fin N => θ i.succ - θ i.castSucc) := by
  rw [idealSuccess]
  exact Finset.prod_congr rfl fun i _ => born_overlap_sq _ _
noncomputable def uniformSchedule (N : ℕ) (Θ : ℝ) : Fin N → ℝ := fun _ => Θ / N
noncomputable def noisySuccess (q Θ : ℝ) (N : ℕ) : ℝ :=
  q ^ N * Real.cos (Θ / N) ^ (2 * N)
noncomputable def noisyLogObjective (q Θ : ℝ) (n : ℝ) : ℝ :=
  n * Real.log q + 2 * n * Real.log (Real.cos (Θ / n))
noncomputable def noisyLogDeriv (q Θ : ℝ) (n : ℝ) : ℝ :=
  Real.log q + 2 * (Real.log (Real.cos (Θ / n)) + (Θ / n) * Real.tan (Θ / n))
def zenoFirstOrderCondition (Θ q n : ℝ) : Prop := noisyLogDeriv q Θ n = 0
def admissibleCount (Θ : ℝ) : Set ℝ := Set.Ioi (2 * Θ / π)
noncomputable def logCosPlusHalfSq (x : ℝ) : ℝ := Real.log (Real.cos x) + x ^ 2 / 2
noncomputable def zenoAngularGain (x : ℝ) : ℝ :=
  2 * (Real.log (Real.cos x) + x * Real.tan x)
lemma noisyLogDeriv_eq (q Θ n : ℝ) :
    noisyLogDeriv q Θ n = Real.log q + zenoAngularGain (Θ / n) := by
  simp [noisyLogDeriv, zenoAngularGain]
end Viridis.Run122.PaperFormalization
namespace Viridis.Run122.PaperFormalization
open Real Set Finset
theorem concaveOn_logCosPlusHalfSq :
    ConcaveOn ℝ (Set.Ioo (-(π / 2)) (π / 2)) logCosPlusHalfSq := by
  have hcos : ∀ x ∈ Set.Ioo (-(π / 2)) (π / 2), 0 < Real.cos x := fun x hx =>
    Real.cos_pos_of_mem_Ioo hx
  have hint : interior (Set.Ioo (-(π / 2)) (π / 2)) = Set.Ioo (-(π / 2)) (π / 2) := interior_Ioo
  apply concaveOn_of_hasDerivWithinAt2_nonpos (f' := fun x => x - Real.tan x)
      (f'' := fun x => 1 - 1 / Real.cos x ^ 2) (convex_Ioo _ _)
  · intro x hx
    exact ((Real.continuousAt_log (hcos x hx).ne').comp
      Real.continuous_cos.continuousAt).continuousWithinAt.add (by fun_prop)
  · intro x hx
    rw [hint] at hx ⊢
    have h1 : HasDerivAt (fun x => Real.log (Real.cos x)) (-Real.sin x / Real.cos x) x := by
      simpa using (Real.hasDerivAt_cos x).log (hcos x hx).ne'
    have h2 : HasDerivAt (fun x : ℝ => x ^ 2 / 2) x x := by
      simpa using (hasDerivAt_pow 2 x).div_const 2
    have h3 := h1.add h2
    have heq : -Real.sin x / Real.cos x + x = x - Real.tan x := by
      rw [Real.tan_eq_sin_div_cos]; ring
    rw [heq] at h3
    exact h3.hasDerivWithinAt
  · intro x hx
    rw [hint] at hx ⊢
    have h := (hasDerivAt_id x).sub (Real.hasDerivAt_tan (hcos x hx).ne')
    simpa using h.hasDerivWithinAt
  · intro x hx
    rw [hint] at hx
    have h := hcos x hx
    have hge : 1 ≤ 1 / Real.cos x ^ 2 := by
      rw [le_div_iff₀ (by positivity)]
      nlinarith [Real.cos_le_one x, Real.neg_one_le_cos x]
    linarith
lemma incr_mem_Ioo {x : ℝ} (hx : x ∈ admissibleIncrement) :
    x ∈ Set.Ioo (-(π / 2)) (π / 2) :=
  ⟨lt_of_lt_of_le (by linarith [Real.pi_pos]) hx.1, hx.2⟩
lemma cos_pos_of_admissible {x : ℝ} (hx : x ∈ admissibleIncrement) : 0 < Real.cos x :=
  Real.cos_pos_of_mem_Ioo (incr_mem_Ioo hx)
theorem mean_increment_mem_Ioo {N : ℕ} (hN : 0 < N) (δ : Fin N → ℝ)
    (hδ : ∀ i, δ i ∈ Set.Ioo (-(π / 2)) (π / 2)) :
    (∑ i, δ i) / N ∈ Set.Ioo (-(π / 2)) (π / 2) := by
  have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
  have hne : (Finset.univ : Finset (Fin N)).Nonempty := by
    simpa [Finset.univ_nonempty_iff] using Fin.pos_iff_nonempty.mp hN
  constructor
  · rw [lt_div_iff₀ hNpos]
    have h1 : ∑ _i : Fin N, (-(π / 2)) < ∑ i, δ i :=
      Finset.sum_lt_sum_of_nonempty hne fun i _ => (hδ i).1
    simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul] at h1
    linarith
  · rw [div_lt_iff₀ hNpos]
    have h1 : ∑ i, δ i < ∑ _i : Fin N, (π / 2) :=
      Finset.sum_lt_sum_of_nonempty hne fun i _ => (hδ i).2
    simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul] at h1
    linarith
lemma idealSuccess_pos {N : ℕ} (δ : Fin N → ℝ) (hδ : ∀ i, 0 < Real.cos (δ i)) :
    0 < idealSuccess δ :=
  Finset.prod_pos fun i _ => pow_pos (hδ i) 2
lemma log_idealSuccess {N : ℕ} (δ : Fin N → ℝ) (hδ : ∀ i, 0 < Real.cos (δ i)) :
    Real.log (idealSuccess δ) = 2 * ∑ i, Real.log (Real.cos (δ i)) := by
  rw [idealSuccess, Real.log_prod fun i _ => (pow_pos (hδ i) 2).ne']
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [Real.log_pow]
  push_cast
  ring
lemma log_idealSuccess_uniform {N : ℕ} (Θ : ℝ)
    (hΘ : 0 < Real.cos (Θ / N)) :
    Real.log (idealSuccess (uniformSchedule N Θ)) = 2 * N * Real.log (Real.cos (Θ / N)) := by
  rw [show (uniformSchedule N Θ) = (fun _ : Fin N => Θ / N) from rfl,
    log_idealSuccess _ (fun _ => hΘ)]
  simp [Finset.sum_const, Finset.card_univ]
  ring
theorem sum_log_cos_add_variance_le {N : ℕ} (hN : 0 < N) (δ : Fin N → ℝ)
    (hδ : ∀ i, δ i ∈ Set.Ioo (-(π / 2)) (π / 2)) (Θ : ℝ) (hsum : ∑ i, δ i = Θ) :
    ∑ i, Real.log (Real.cos (δ i)) + (1 / 2) * ∑ i, (δ i - Θ / N) ^ 2
      ≤ N * Real.log (Real.cos (Θ / N)) := by
  have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
  set m : ℝ := Θ / N with hm
  have hjen := concaveOn_logCosPlusHalfSq.le_map_sum (t := (Finset.univ : Finset (Fin N)))
      (w := fun _ => (1 : ℝ) / N) (p := δ)
      (fun i _ => by positivity) (by simp [Finset.card_univ]; field_simp)
      (fun i _ => hδ i)
  have hpt : ∑ i, (1 / (N : ℝ)) • δ i = m := by
    rw [hm, ← hsum]
    simp [smul_eq_mul, ← Finset.mul_sum]
    ring
  rw [hpt] at hjen
  simp only [smul_eq_mul] at hjen
  have hjen2 : ∑ i, logCosPlusHalfSq (δ i) ≤ N * logCosPlusHalfSq m := by
    have hmul : (N : ℝ) * ∑ i, (1 / (N : ℝ)) * logCosPlusHalfSq (δ i)
        ≤ (N : ℝ) * logCosPlusHalfSq m := mul_le_mul_of_nonneg_left hjen hNpos.le
    calc ∑ i, logCosPlusHalfSq (δ i)
        = (N : ℝ) * ∑ i, (1 / (N : ℝ)) * logCosPlusHalfSq (δ i) := by
          rw [Finset.mul_sum]
          exact Finset.sum_congr rfl fun i _ => by field_simp
      _ ≤ (N : ℝ) * logCosPlusHalfSq m := hmul
  have hexp : ∑ i, logCosPlusHalfSq (δ i)
      = ∑ i, Real.log (Real.cos (δ i)) + (1 / 2) * ∑ i, (δ i) ^ 2 := by
    simp only [logCosPlusHalfSq, Finset.sum_add_distrib, Finset.mul_sum]
    congr 1
    exact Finset.sum_congr rfl fun i _ => by ring
  have hvar : ∑ i, (δ i - m) ^ 2 = (∑ i, (δ i) ^ 2) - N * m ^ 2 := by
    have hsq : ∀ i, (δ i - m) ^ 2 = (δ i) ^ 2 - 2 * m * (δ i) + m ^ 2 := fun i => by ring
    simp only [hsq, Finset.sum_add_distrib, Finset.sum_sub_distrib, ← Finset.mul_sum, hsum,
      Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    have h2 : 2 * m * Θ = 2 * (N : ℝ) * m ^ 2 := by rw [hm]; field_simp
    rw [h2]; ring
  have hFm : (N : ℝ) * logCosPlusHalfSq m
      = N * Real.log (Real.cos m) + (N / 2) * m ^ 2 := by
    simp [logCosPlusHalfSq]; ring
  rw [hexp, hFm] at hjen2
  rw [hvar]
  linarith
theorem zeno_schedule_log_gap_ge_variance {N : ℕ} (hN : 0 < N) (Θ : ℝ) (δ : Fin N → ℝ)
    (hδ : ∀ i, δ i ∈ admissibleIncrement) (hsum : ∑ i, δ i = Θ) :
    ∑ i, (δ i - Θ / N) ^ 2
      ≤ Real.log (idealSuccess (uniformSchedule N Θ) / idealSuccess δ) := by
  have hδ' : ∀ i, δ i ∈ Set.Ioo (-(π / 2)) (π / 2) := fun i => incr_mem_Ioo (hδ i)
  have hcosδ : ∀ i, 0 < Real.cos (δ i) := fun i => cos_pos_of_admissible (hδ i)
  have hmean : Θ / N ∈ Set.Ioo (-(π / 2)) (π / 2) := by
    have := mean_increment_mem_Ioo hN δ hδ'
    rwa [hsum] at this
  have hcosm : 0 < Real.cos (Θ / N) := Real.cos_pos_of_mem_Ioo hmean
  have hPpos : 0 < idealSuccess δ := idealSuccess_pos δ hcosδ
  have hUpos : 0 < idealSuccess (uniformSchedule N Θ) :=
    idealSuccess_pos _ fun _ => hcosm
  rw [Real.log_div hUpos.ne' hPpos.ne', log_idealSuccess_uniform Θ hcosm,
    log_idealSuccess δ hcosδ]
  have := sum_log_cos_add_variance_le hN δ hδ' Θ hsum
  linarith
theorem uniform_zeno_schedule_maximizes_success {N : ℕ} (hN : 0 < N) (Θ : ℝ) (δ : Fin N → ℝ)
    (hδ : ∀ i, δ i ∈ admissibleIncrement) (hsum : ∑ i, δ i = Θ) :
    idealSuccess δ ≤ idealSuccess (uniformSchedule N Θ) ∧
      (idealSuccess δ = idealSuccess (uniformSchedule N Θ) → ∀ i, δ i = Θ / N) := by
  have hδ' : ∀ i, δ i ∈ Set.Ioo (-(π / 2)) (π / 2) := fun i => incr_mem_Ioo (hδ i)
  have hcosδ : ∀ i, 0 < Real.cos (δ i) := fun i => cos_pos_of_admissible (hδ i)
  have hmean : Θ / N ∈ Set.Ioo (-(π / 2)) (π / 2) := by
    have := mean_increment_mem_Ioo hN δ hδ'
    rwa [hsum] at this
  have hcosm : 0 < Real.cos (Θ / N) := Real.cos_pos_of_mem_Ioo hmean
  have hPpos : 0 < idealSuccess δ := idealSuccess_pos δ hcosδ
  have hUpos : 0 < idealSuccess (uniformSchedule N Θ) := idealSuccess_pos _ fun _ => hcosm
  have hgap := zeno_schedule_log_gap_ge_variance hN Θ δ hδ hsum
  have hvarnn : (0 : ℝ) ≤ ∑ i, (δ i - Θ / N) ^ 2 :=
    Finset.sum_nonneg fun i _ => sq_nonneg _
  have hlog : Real.log (idealSuccess δ) ≤ Real.log (idealSuccess (uniformSchedule N Θ)) := by
    rw [Real.log_div hUpos.ne' hPpos.ne'] at hgap
    linarith
  have hle : idealSuccess δ ≤ idealSuccess (uniformSchedule N Θ) :=
    (Real.log_le_log_iff hPpos hUpos).mp hlog
  refine ⟨hle, fun heq i => ?_⟩
  have hzero : Real.log (idealSuccess (uniformSchedule N Θ) / idealSuccess δ) = 0 := by
    rw [heq, div_self hUpos.ne']
    exact Real.log_one
  rw [hzero] at hgap
  have hall : ∀ j ∈ (Finset.univ : Finset (Fin N)), (δ j - Θ / N) ^ 2 = 0 := by
    refine (Finset.sum_eq_zero_iff_of_nonneg fun j _ => sq_nonneg _).mp (le_antisymm ?_ hvarnn)
    ·
      exact hgap
  have := hall i (Finset.mem_univ i)
  have : δ i - Θ / N = 0 := by
    exact pow_eq_zero_iff (n := 2) (by norm_num) |>.mp this
  linarith
end Viridis.Run122.PaperFormalization
namespace Viridis.Run122.PaperFormalization
open Real Set Filter Topology
lemma pos_of_admissibleCount {Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) : 0 < n :=
  lt_of_le_of_lt (by positivity) hn
lemma angle_lt_pi_div_two {Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    Θ / n < π / 2 := by
  have hpi := Real.pi_pos
  have hn0 : 0 < n := pos_of_admissibleCount hΘ hn
  have hn' : 2 * Θ / π < n := hn
  rw [div_lt_iff₀ hn0]
  rw [div_lt_iff₀ hpi] at hn'
  nlinarith
lemma angle_pos {Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) : 0 < Θ / n :=
  div_pos hΘ (pos_of_admissibleCount hΘ hn)
lemma cos_angle_pos {Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    0 < Real.cos (Θ / n) :=
  Real.cos_pos_of_mem_Ioo ⟨by linarith [angle_pos hΘ hn, Real.pi_pos], angle_lt_pi_div_two hΘ hn⟩
lemma isOpen_admissibleCount (Θ : ℝ) : IsOpen (admissibleCount Θ) := isOpen_Ioi
lemma convex_admissibleCount (Θ : ℝ) : Convex ℝ (admissibleCount Θ) := convex_Ioi _
lemma interior_admissibleCount (Θ : ℝ) : interior (admissibleCount Θ) = admissibleCount Θ :=
  (isOpen_admissibleCount Θ).interior_eq
lemma hasDerivAt_div_self {Θ n : ℝ} (hn0 : 0 < n) :
    HasDerivAt (fun m : ℝ => Θ / m) (-(Θ / n ^ 2)) n := by
  have h2 := (hasDerivAt_const n Θ).div (hasDerivAt_id n) hn0.ne'
  convert h2 using 1
  simp
  field_simp
theorem hasDerivAt_noisyLogObjective {q Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    HasDerivAt (noisyLogObjective q Θ) (noisyLogDeriv q Θ n) n := by
  have hn0 : 0 < n := pos_of_admissibleCount hΘ hn
  have hcos : 0 < Real.cos (Θ / n) := cos_angle_pos hΘ hn
  have hd1 : HasDerivAt (fun m : ℝ => Θ / m) (-(Θ / n ^ 2)) n := hasDerivAt_div_self hn0
  have hdcos : HasDerivAt (fun m : ℝ => Real.cos (Θ / m))
      (-Real.sin (Θ / n) * (-(Θ / n ^ 2))) n := by
    simpa [Function.comp] using (Real.hasDerivAt_cos (Θ / n)).comp n hd1
  have hd3 : HasDerivAt (fun m : ℝ => Real.log (Real.cos (Θ / m)))
      ((-Real.sin (Θ / n) * (-(Θ / n ^ 2))) / Real.cos (Θ / n)) n := hdcos.log hcos.ne'
  have hd4 : HasDerivAt (fun m : ℝ => 2 * m * Real.log (Real.cos (Θ / m)))
      (2 * Real.log (Real.cos (Θ / n)) +
        2 * n * ((-Real.sin (Θ / n) * (-(Θ / n ^ 2))) / Real.cos (Θ / n))) n := by
    simpa using ((hasDerivAt_id n).const_mul (2 : ℝ)).mul hd3
  have hd5 : HasDerivAt (fun m : ℝ => m * Real.log q) (Real.log q) n := by
    simpa using (hasDerivAt_id n).mul_const (Real.log q)
  have h := hd5.add hd4
  convert h using 1
  rw [noisyLogDeriv, Real.tan_eq_sin_div_cos]
  field_simp
theorem hasDerivAt_noisyLogDeriv {q Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    HasDerivAt (noisyLogDeriv q Θ)
      (-2 * (Θ / n) ^ 2 / (Real.cos (Θ / n) ^ 2 * n)) n := by
  have hn0 : 0 < n := pos_of_admissibleCount hΘ hn
  have hcos : 0 < Real.cos (Θ / n) := cos_angle_pos hΘ hn
  have hd1 : HasDerivAt (fun m : ℝ => Θ / m) (-(Θ / n ^ 2)) n := hasDerivAt_div_self hn0
  have hdcos : HasDerivAt (fun m : ℝ => Real.cos (Θ / m))
      (-Real.sin (Θ / n) * (-(Θ / n ^ 2))) n := by
    simpa [Function.comp] using (Real.hasDerivAt_cos (Θ / n)).comp n hd1
  have hd3 : HasDerivAt (fun m : ℝ => Real.log (Real.cos (Θ / m)))
      ((-Real.sin (Θ / n) * (-(Θ / n ^ 2))) / Real.cos (Θ / n)) n := hdcos.log hcos.ne'
  have hdtan : HasDerivAt (fun m : ℝ => Real.tan (Θ / m))
      ((1 / Real.cos (Θ / n) ^ 2) * (-(Θ / n ^ 2))) n := by
    simpa [Function.comp] using (Real.hasDerivAt_tan hcos.ne').comp n hd1
  have hd4 : HasDerivAt (fun m : ℝ => (Θ / m) * Real.tan (Θ / m))
      ((-(Θ / n ^ 2)) * Real.tan (Θ / n) +
        (Θ / n) * ((1 / Real.cos (Θ / n) ^ 2) * (-(Θ / n ^ 2)))) n := hd1.mul hdtan
  have h := (hasDerivAt_const n (Real.log q)).add ((hd3.add hd4).const_mul (2 : ℝ))
  convert h using 1
  rw [Real.tan_eq_sin_div_cos]
  field_simp
  ring
lemma noisyLogDeriv2_neg {Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    -2 * (Θ / n) ^ 2 / (Real.cos (Θ / n) ^ 2 * n) < 0 := by
  have hn0 : 0 < n := pos_of_admissibleCount hΘ hn
  have hcos : 0 < Real.cos (Θ / n) := cos_angle_pos hΘ hn
  have hx : 0 < Θ / n := angle_pos hΘ hn
  have : 0 < 2 * (Θ / n) ^ 2 / (Real.cos (Θ / n) ^ 2 * n) := by positivity
  linarith [this, show -2 * (Θ / n) ^ 2 / (Real.cos (Θ / n) ^ 2 * n)
      = -(2 * (Θ / n) ^ 2 / (Real.cos (Θ / n) ^ 2 * n)) by ring]
lemma continuousOn_noisyLogDeriv {q Θ : ℝ} (hΘ : 0 < Θ) :
    ContinuousOn (noisyLogDeriv q Θ) (admissibleCount Θ) := fun _ hn =>
  ((hasDerivAt_noisyLogDeriv (q := q) hΘ hn).continuousAt).continuousWithinAt
lemma continuousOn_noisyLogObjective {q Θ : ℝ} (hΘ : 0 < Θ) :
    ContinuousOn (noisyLogObjective q Θ) (admissibleCount Θ) := fun _ hn =>
  ((hasDerivAt_noisyLogObjective (q := q) hΘ hn).continuousAt).continuousWithinAt
lemma deriv_noisyLogObjective_eq {q Θ n : ℝ} (hΘ : 0 < Θ) (hn : n ∈ admissibleCount Θ) :
    deriv (noisyLogObjective q Θ) n = noisyLogDeriv q Θ n :=
  (hasDerivAt_noisyLogObjective hΘ hn).deriv
theorem strictAntiOn_noisyLogDeriv {q Θ : ℝ} (hΘ : 0 < Θ) :
    StrictAntiOn (noisyLogDeriv q Θ) (admissibleCount Θ) := by
  apply strictAntiOn_of_deriv_neg (convex_admissibleCount Θ) (continuousOn_noisyLogDeriv hΘ)
  intro n hn
  rw [interior_admissibleCount] at hn
  rw [(hasDerivAt_noisyLogDeriv (q := q) hΘ hn).deriv]
  exact noisyLogDeriv2_neg hΘ hn
theorem noisy_zeno_log_objective_strictConcave {q Θ : ℝ} (hq0 : 0 < q) (hq1 : q < 1)
    (hΘ : 0 < Θ) :
    StrictConcaveOn ℝ (admissibleCount Θ) (noisyLogObjective q Θ) := by
  apply StrictAntiOn.strictConcaveOn_of_deriv (convex_admissibleCount Θ)
    (continuousOn_noisyLogObjective hΘ)
  rw [interior_admissibleCount]
  intro a ha b hb hab
  rw [deriv_noisyLogObjective_eq hΘ ha, deriv_noisyLogObjective_eq hΘ hb]
  exact strictAntiOn_noisyLogDeriv hΘ ha hb hab
lemma one_mem_admissibleCount {Θ : ℝ} (hΘ : Θ < π / 2) :
    (1 : ℝ) ∈ admissibleCount Θ := by
  have hpi := Real.pi_pos
  show 2 * Θ / π < 1
  rw [div_lt_one hpi]
  linarith
lemma Ici_one_subset {Θ : ℝ} (hΘ : Θ < π / 2) :
    Set.Ici (1 : ℝ) ⊆ admissibleCount Θ := by
  intro n hn
  have h1 : 2 * Θ / π < 1 := one_mem_admissibleCount hΘ
  exact lt_of_lt_of_le h1 hn
@[simp] lemma zenoAngularGain_zero : zenoAngularGain 0 = 0 := by simp [zenoAngularGain]
lemma continuousAt_zenoAngularGain_zero : ContinuousAt zenoAngularGain 0 := by
  unfold zenoAngularGain
  have h1 : ContinuousAt (fun x : ℝ => Real.log (Real.cos x)) 0 :=
    (Real.continuousAt_log (by simp)).comp Real.continuous_cos.continuousAt
  have h2 : ContinuousAt (fun x : ℝ => x * Real.tan x) 0 :=
    continuousAt_id.mul (Real.continuousAt_tan.mpr (by simp))
  exact continuousAt_const.mul (h1.add h2)
lemma tendsto_zenoAngularGain_atTop (Θ : ℝ) :
    Tendsto (fun n : ℝ => zenoAngularGain (Θ / n)) atTop (𝓝 0) := by
  have h0 : Tendsto (fun n : ℝ => Θ / n) atTop (𝓝 0) :=
    Filter.Tendsto.div_atTop tendsto_const_nhds tendsto_id
  have h := continuousAt_zenoAngularGain_zero.tendsto.comp h0
  rw [zenoAngularGain_zero] at h
  exact h
theorem noisy_zeno_boundary_or_unique_interior_optimizer {q Θ : ℝ} (hq0 : 0 < q) (hq1 : q < 1)
    (hΘ0 : 0 < Θ) (hΘ : Θ < π / 2) :
    (noisyLogDeriv q Θ 1 ≤ 0 ∧ IsMaxOn (noisyLogObjective q Θ) (Set.Ici 1) 1) ∨
      (0 < noisyLogDeriv q Θ 1 ∧ ∃ nstar : ℝ, 1 < nstar ∧ nstar ∈ admissibleCount Θ ∧
        zenoFirstOrderCondition Θ q nstar ∧
        (∀ m ∈ admissibleCount Θ, zenoFirstOrderCondition Θ q m → m = nstar) ∧
        IsMaxOn (noisyLogObjective q Θ) (Set.Ici 1) nstar) := by
  have h1mem : (1 : ℝ) ∈ admissibleCount Θ := one_mem_admissibleCount hΘ
  have hsub : Set.Ici (1 : ℝ) ⊆ admissibleCount Θ := Ici_one_subset hΘ
  have hcontIci : ContinuousOn (noisyLogObjective q Θ) (Set.Ici 1) :=
    (continuousOn_noisyLogObjective hΘ0).mono hsub
  by_cases hb : noisyLogDeriv q Θ 1 ≤ 0
  · left
    refine ⟨hb, ?_⟩
    have hanti : StrictAntiOn (noisyLogObjective q Θ) (Set.Ici 1) := by
      apply strictAntiOn_of_deriv_neg (convex_Ici 1) hcontIci
      intro n hn
      rw [interior_Ici] at hn
      have hn' : (1 : ℝ) ≤ n := le_of_lt hn
      have hnadm : n ∈ admissibleCount Θ := hsub hn'
      rw [deriv_noisyLogObjective_eq hΘ0 hnadm]
      have := strictAntiOn_noisyLogDeriv (q := q) hΘ0 h1mem hnadm hn
      linarith
    intro m hm
    rcases eq_or_lt_of_le (Set.mem_Ici.mp hm) with h | h
    · simp [← h]
    · exact le_of_lt (hanti Set.self_mem_Ici hm h)
  · right
    push_neg at hb
    have hlogq : Real.log q < 0 := Real.log_neg hq0 hq1
    have hev : ∀ᶠ n : ℝ in atTop, zenoAngularGain (Θ / n) < -Real.log q :=
      (tendsto_zenoAngularGain_atTop Θ).eventually
        (gt_mem_nhds (show (0 : ℝ) < -Real.log q by linarith))
    obtain ⟨n₂, hn₂⟩ := (hev.and (eventually_gt_atTop (1 : ℝ))).exists
    have hn₂1 : (1 : ℝ) < n₂ := hn₂.2
    have hn₂neg : noisyLogDeriv q Θ n₂ < 0 := by rw [noisyLogDeriv_eq]; linarith [hn₂.1]
    have hcont : ContinuousOn (noisyLogDeriv q Θ) (Set.Icc 1 n₂) :=
      (continuousOn_noisyLogDeriv hΘ0).mono fun x hx => hsub hx.1
    have hmem : (0 : ℝ) ∈ Set.Ioo (noisyLogDeriv q Θ n₂) (noisyLogDeriv q Θ 1) := ⟨hn₂neg, hb⟩
    obtain ⟨nstar, hns, hns0⟩ := intermediate_value_Ioo' (le_of_lt hn₂1) hcont hmem
    have hns1 : (1 : ℝ) < nstar := hns.1
    have hnsadm : nstar ∈ admissibleCount Θ := hsub (le_of_lt hns1)
    refine ⟨hb, nstar, hns1, hnsadm, hns0, ?_, ?_⟩
    · intro m hm hfoc
      by_contra hne
      rcases lt_or_gt_of_ne hne with h | h
      · have := strictAntiOn_noisyLogDeriv (q := q) hΘ0 hm hnsadm h
        rw [hfoc, hns0] at this
        exact lt_irrefl 0 this
      · have := strictAntiOn_noisyLogDeriv (q := q) hΘ0 hnsadm hm h
        rw [hfoc, hns0] at this
        exact lt_irrefl 0 this
    · have hmono : StrictMonoOn (noisyLogObjective q Θ) (Set.Icc 1 nstar) := by
        apply strictMonoOn_of_deriv_pos (convex_Icc _ _) (hcontIci.mono fun x hx => hx.1)
        intro x hx
        rw [interior_Icc] at hx
        have hx1 : (1 : ℝ) ≤ x := le_of_lt hx.1
        have hxadm : x ∈ admissibleCount Θ := hsub hx1
        rw [deriv_noisyLogObjective_eq hΘ0 hxadm]
        have := strictAntiOn_noisyLogDeriv (q := q) hΘ0 hxadm hnsadm hx.2
        rw [hns0] at this
        exact this
      have hanti : StrictAntiOn (noisyLogObjective q Θ) (Set.Ici nstar) := by
        apply strictAntiOn_of_deriv_neg (convex_Ici _)
          (hcontIci.mono fun x hx => le_trans (le_of_lt hns1) hx)
        intro x hx
        rw [interior_Ici] at hx
        have hx1 : (1 : ℝ) ≤ x := le_trans (le_of_lt hns1) (le_of_lt hx)
        have hxadm : x ∈ admissibleCount Θ := hsub hx1
        rw [deriv_noisyLogObjective_eq hΘ0 hxadm]
        have := strictAntiOn_noisyLogDeriv (q := q) hΘ0 hnsadm hxadm hx
        rw [hns0] at this
        exact this
      intro m hm
      have hm1 : (1 : ℝ) ≤ m := hm
      rcases le_or_gt m nstar with h | h
      · exact hmono.monotoneOn ⟨hm1, h⟩ ⟨le_of_lt hns1, le_refl _⟩ h
      · exact le_of_lt (hanti Set.self_mem_Ici (le_of_lt h) h)
theorem exists_optimal_count {q Θ : ℝ} (hq0 : 0 < q) (hq1 : q < 1)
    (hΘ0 : 0 < Θ) (hΘ : Θ < π / 2) :
    ∃ nstar : ℝ, 1 ≤ nstar ∧ IsMaxOn (noisyLogObjective q Θ) (Set.Ici 1) nstar := by
  rcases noisy_zeno_boundary_or_unique_interior_optimizer hq0 hq1 hΘ0 hΘ with
    ⟨_, h⟩ | ⟨_, ns, h1, _, _, _, hm⟩
  · exact ⟨1, le_refl 1, h⟩
  · exact ⟨ns, le_of_lt h1, hm⟩
lemma concaveOn_le_of_left {s : Set ℝ} {f : ℝ → ℝ} (hf : ConcaveOn ℝ s f)
    {c a b : ℝ} (hmax : IsMaxOn f s c) (ha : a ∈ s) (hc : c ∈ s)
    (hab : a ≤ b) (hbc : b ≤ c) : f a ≤ f b := by
  rcases eq_or_lt_of_le (hab.trans hbc) with h | h
  · have hba : b = a := le_antisymm (h ▸ hbc) hab
    rw [hba]
  · have hca : 0 < c - a := by linarith
    set t : ℝ := (c - b) / (c - a) with ht
    set u : ℝ := (b - a) / (c - a) with hu
    have ht0 : 0 ≤ t := div_nonneg (by linarith) hca.le
    have hu0 : 0 ≤ u := div_nonneg (by linarith) hca.le
    have htu : t + u = 1 := by rw [ht, hu]; field_simp; ring
    have hcomb : t • a + u • c = b := by
      simp only [ht, hu, smul_eq_mul]; field_simp; ring
    have h1 := hf.2 ha hc ht0 hu0 htu
    rw [hcomb] at h1
    have h2 : f a ≤ f c := hmax ha
    simp only [smul_eq_mul] at h1
    have e : f a = t * f a + u * f a := by rw [← add_mul, htu, one_mul]
    have hmul : u * f a ≤ u * f c := mul_le_mul_of_nonneg_left h2 hu0
    linarith
lemma concaveOn_le_of_right {s : Set ℝ} {f : ℝ → ℝ} (hf : ConcaveOn ℝ s f)
    {c a b : ℝ} (hmax : IsMaxOn f s c) (ha : a ∈ s) (hc : c ∈ s)
    (hcb : c ≤ b) (hba : b ≤ a) : f a ≤ f b := by
  rcases eq_or_lt_of_le (hcb.trans hba) with h | h
  · have hba' : b = a := le_antisymm hba (h ▸ hcb)
    rw [hba']
  · have hac : 0 < a - c := by linarith
    set t : ℝ := (b - c) / (a - c) with ht
    set u : ℝ := (a - b) / (a - c) with hu
    have ht0 : 0 ≤ t := div_nonneg (by linarith) hac.le
    have hu0 : 0 ≤ u := div_nonneg (by linarith) hac.le
    have htu : t + u = 1 := by rw [ht, hu]; field_simp; ring
    have hcomb : t • a + u • c = b := by
      simp only [ht, hu, smul_eq_mul]; field_simp; ring
    have h1 := hf.2 ha hc ht0 hu0 htu
    rw [hcomb] at h1
    have h2 : f a ≤ f c := hmax ha
    simp only [smul_eq_mul] at h1
    have e : f a = t * f a + u * f a := by rw [← add_mul, htu, one_mul]
    have hmul : u * f a ≤ u * f c := mul_le_mul_of_nonneg_left h2 hu0
    linarith
theorem noisy_zeno_integer_optimum_floor_or_ceil {q Θ : ℝ} (hq0 : 0 < q) (hq1 : q < 1)
    (hΘ0 : 0 < Θ) (hΘ : Θ < π / 2) {nstar : ℝ} (h1 : 1 ≤ nstar)
    (hmax : IsMaxOn (noisyLogObjective q Θ) (Set.Ici 1) nstar) {N : ℕ} (hN : 1 ≤ N) :
    noisyLogObjective q Θ N ≤
      max (noisyLogObjective q Θ ⌊nstar⌋₊) (noisyLogObjective q Θ ⌈nstar⌉₊) := by
  have hconc : ConcaveOn ℝ (Set.Ici (1 : ℝ)) (noisyLogObjective q Θ) :=
    ((noisy_zeno_log_objective_strictConcave hq0 hq1 hΘ0).subset
      (Ici_one_subset hΘ) (convex_Ici 1)).concaveOn
  have hNr : (1 : ℝ) ≤ (N : ℝ) := by exact_mod_cast hN
  have hcmem : nstar ∈ Set.Ici (1 : ℝ) := h1
  have hamem : (N : ℝ) ∈ Set.Ici (1 : ℝ) := hNr
  rcases le_or_gt N ⌊nstar⌋₊ with h | h
  · refine le_trans ?_ (le_max_left _ _)
    have hb1 : (N : ℝ) ≤ (⌊nstar⌋₊ : ℝ) := by exact_mod_cast h
    have hb2 : ((⌊nstar⌋₊ : ℕ) : ℝ) ≤ nstar := Nat.floor_le (by linarith)
    exact concaveOn_le_of_left hconc hmax hamem hcmem hb1 hb2
  · refine le_trans ?_ (le_max_right _ _)
    have hceil : ⌈nstar⌉₊ ≤ N := le_trans (Nat.ceil_le_floor_add_one nstar) h
    have hb1 : ((⌈nstar⌉₊ : ℕ) : ℝ) ≤ (N : ℝ) := by exact_mod_cast hceil
    have hb2 : nstar ≤ ((⌈nstar⌉₊ : ℕ) : ℝ) := Nat.le_ceil nstar
    exact concaveOn_le_of_right hconc hmax hamem hcmem hb2 hb1
end Viridis.Run122.PaperFormalization
namespace Viridis.Run122.PaperFormalization
open Real Set Filter Topology
theorem hasDerivAt_zenoAngularGain {x : ℝ} (hx : x ∈ Set.Ioo (-(π / 2)) (π / 2)) :
    HasDerivAt zenoAngularGain (2 * x / Real.cos x ^ 2) x := by
  have hcos : 0 < Real.cos x := Real.cos_pos_of_mem_Ioo hx
  have h1 : HasDerivAt (fun y : ℝ => Real.log (Real.cos y)) (-Real.sin x / Real.cos x) x := by
    simpa using (Real.hasDerivAt_cos x).log hcos.ne'
  have h2 : HasDerivAt (fun y : ℝ => y * Real.tan y)
      (1 * Real.tan x + x * (1 / Real.cos x ^ 2)) x :=
    (hasDerivAt_id x).mul (Real.hasDerivAt_tan hcos.ne')
  have h := (h1.add h2).const_mul (2 : ℝ)
  convert h using 1
  rw [Real.tan_eq_sin_div_cos]
  field_simp
  ring
theorem zenoAngularGain_ge_sq {x : ℝ} (hx : x ∈ Set.Ico 0 (π / 2)) :
    x ^ 2 ≤ zenoAngularGain x := by
  have hpi := Real.pi_pos
  have hd : ∀ y ∈ Set.Ioo (-(π / 2)) (π / 2),
      HasDerivAt (fun z : ℝ => zenoAngularGain z - z ^ 2)
        (2 * y / Real.cos y ^ 2 - 2 * y) y := by
    intro y hy
    have h := (hasDerivAt_zenoAngularGain hy).sub (hasDerivAt_pow 2 y)
    convert h using 1
    norm_num
  have hmono : MonotoneOn (fun z : ℝ => zenoAngularGain z - z ^ 2) (Set.Ico 0 (π / 2)) := by
    apply monotoneOn_of_deriv_nonneg (convex_Ico _ _)
    · intro y hy
      have hy' : y ∈ Set.Ioo (-(π / 2)) (π / 2) := ⟨by linarith [hy.1], hy.2⟩
      exact ((hd y hy').continuousAt).continuousWithinAt
    · intro y hy
      rw [interior_Ico] at hy
      have hy' : y ∈ Set.Ioo (-(π / 2)) (π / 2) := ⟨by linarith [hy.1], hy.2⟩
      exact (hd y hy').differentiableAt.differentiableWithinAt
    · intro y hy
      rw [interior_Ico] at hy
      have hy' : y ∈ Set.Ioo (-(π / 2)) (π / 2) := ⟨by linarith [hy.1], hy.2⟩
      have hcos : 0 < Real.cos y := Real.cos_pos_of_mem_Ioo hy'
      rw [(hd y hy').deriv]
      have hc1 : Real.cos y ^ 2 ≤ 1 := by
        nlinarith [Real.cos_le_one y, Real.neg_one_le_cos y]
      have hge : 2 * y ≤ 2 * y / Real.cos y ^ 2 := by
        rw [le_div_iff₀ (by positivity)]
        nlinarith [hy.1]
      linarith
  have h0 : zenoAngularGain 0 - (0 : ℝ) ^ 2 = 0 := by simp
  have hmain := hmono (Set.left_mem_Ico.mpr (by linarith)) hx hx.1
  simp only [h0] at hmain
  linarith
theorem tendsto_zenoAngularGain_div_sq :
    Tendsto (fun x : ℝ => zenoAngularGain x / x ^ 2) (𝓝[>] 0) (𝓝 1) := by
  have hpi := Real.pi_pos
  have hIoo : Set.Ioo (0 : ℝ) (π / 2) ∈ 𝓝[>] (0 : ℝ) := Ioo_mem_nhdsGT (by linarith)
  have hff' : ∀ᶠ x in 𝓝[>] (0 : ℝ), HasDerivAt zenoAngularGain (2 * x / Real.cos x ^ 2) x := by
    filter_upwards [hIoo] with x hx
    exact hasDerivAt_zenoAngularGain ⟨by linarith [hx.1], hx.2⟩
  have hgg' : ∀ᶠ x in 𝓝[>] (0 : ℝ), HasDerivAt (fun y : ℝ => y ^ 2) (2 * x) x := by
    filter_upwards with x
    simpa using hasDerivAt_pow 2 x
  have hg' : ∀ᶠ x in 𝓝[>] (0 : ℝ), (2 * x) ≠ 0 := by
    filter_upwards [self_mem_nhdsWithin] with x hx
    have hx0 : (0 : ℝ) < x := hx
    positivity
  have hfa : Tendsto zenoAngularGain (𝓝[>] (0 : ℝ)) (𝓝 0) := by
    have h := continuousAt_zenoAngularGain_zero.tendsto.mono_left
      (nhdsWithin_le_nhds (s := Set.Ioi (0 : ℝ)))
    rwa [zenoAngularGain_zero] at h
  have hga : Tendsto (fun y : ℝ => y ^ 2) (𝓝[>] (0 : ℝ)) (𝓝 0) := by
    have hc : ContinuousAt (fun y : ℝ => y ^ 2) 0 := by fun_prop
    have h := hc.tendsto.mono_left (nhdsWithin_le_nhds (s := Set.Ioi (0 : ℝ)))
    simpa using h
  have hdiv : Tendsto (fun x : ℝ => (2 * x / Real.cos x ^ 2) / (2 * x)) (𝓝[>] (0 : ℝ)) (𝓝 1) := by
    have heq : ∀ᶠ x in 𝓝[>] (0 : ℝ),
        (2 * x / Real.cos x ^ 2) / (2 * x) = 1 / Real.cos x ^ 2 := by
      filter_upwards [hIoo] with x hx
      have hx0 : (0 : ℝ) < x := hx.1
      have hcos : 0 < Real.cos x := Real.cos_pos_of_mem_Ioo ⟨by linarith [hx.1], hx.2⟩
      field_simp
    rw [tendsto_congr' heq]
    have hc : ContinuousAt (fun x : ℝ => 1 / Real.cos x ^ 2) 0 := by
      apply ContinuousAt.div continuousAt_const
      · exact Real.continuous_cos.continuousAt.pow 2
      · simp
    have h := hc.tendsto.mono_left (nhdsWithin_le_nhds (s := Set.Ioi (0 : ℝ)))
    simpa using h
  exact HasDerivAt.lhopital_zero_nhdsGT hff' hgg' hg' hfa hga hdiv
theorem noisy_zeno_high_quality_asymptotic {Θ : ℝ} (hΘ : 0 < Θ)
    (q n : ℕ → ℝ) (hq : ∀ k, q k ∈ Set.Ioo (0 : ℝ) 1)
    (hqlim : Tendsto q atTop (𝓝 1))
    (hn : ∀ k, n k ∈ admissibleCount Θ)
    (hfoc : ∀ k, zenoFirstOrderCondition Θ (q k) (n k)) :
    Tendsto (fun k => n k * Real.sqrt (-Real.log (q k)) / Θ) atTop (𝓝 1) := by
  have hpi := Real.pi_pos
  set x : ℕ → ℝ := fun k => Θ / n k with hxdef
  have hx0 : ∀ k, 0 < x k := fun k => angle_pos hΘ (hn k)
  have hxpi : ∀ k, x k < π / 2 := fun k => angle_lt_pi_div_two hΘ (hn k)
  have hgain : ∀ k, zenoAngularGain (x k) = -Real.log (q k) := by
    intro k
    have h := hfoc k
    rw [zenoFirstOrderCondition, noisyLogDeriv_eq] at h
    linarith
  have heps : Tendsto (fun k => -Real.log (q k)) atTop (𝓝 0) := by
    have hc : ContinuousAt Real.log 1 := Real.continuousAt_log (by norm_num)
    have h := hc.tendsto.comp hqlim
    simp only [Real.log_one] at h
    simpa using h.neg
  have hsq : Tendsto (fun k => (x k) ^ 2) atTop (𝓝 0) := by
    apply squeeze_zero (fun k => sq_nonneg _) _ heps
    intro k
    rw [← hgain k]
    exact zenoAngularGain_ge_sq ⟨(hx0 k).le, hxpi k⟩
  have hxlim : Tendsto x atTop (𝓝 0) := by
    have h := (Real.continuous_sqrt.tendsto 0).comp hsq
    rw [Real.sqrt_zero] at h
    exact h.congr fun k => Real.sqrt_sq (hx0 k).le
  have hxlim' : Tendsto x atTop (𝓝[>] 0) :=
    tendsto_nhdsWithin_of_tendsto_nhds_of_eventually_within _ hxlim
      (Eventually.of_forall fun k => hx0 k)
  have hratio : Tendsto (fun k => zenoAngularGain (x k) / (x k) ^ 2) atTop (𝓝 1) :=
    tendsto_zenoAngularGain_div_sq.comp hxlim'
  have hkey : ∀ k, n k * Real.sqrt (-Real.log (q k)) / Θ
      = Real.sqrt (zenoAngularGain (x k) / (x k) ^ 2) := by
    intro k
    rw [hgain k]
    have hnk : 0 < n k := pos_of_admissibleCount hΘ (hn k)
    have hxk : 0 < x k := hx0 k
    have hnonneg : (0 : ℝ) ≤ -Real.log (q k) := by
      rw [← hgain k]
      exact le_trans (sq_nonneg _) (zenoAngularGain_ge_sq ⟨hxk.le, hxpi k⟩)
    rw [Real.sqrt_div hnonneg, Real.sqrt_sq hxk.le, hxdef]
    field_simp
  rw [funext hkey]
  have h := (Real.continuous_sqrt.tendsto 1).comp hratio
  simpa using h
end Viridis.Run122.PaperFormalization
namespace Viridis.Run122.PaperFormalization
open Real Set Finset Filter Topology
lemma idealSuccess_uniform_eq (N : ℕ) (Θ : ℝ) :
    idealSuccess (uniformSchedule N Θ) = (Real.cos (Θ / N) ^ 2) ^ N := by
  simp [idealSuccess, uniformSchedule]
theorem ideal_zeno_uniform_success_tendsto_one (Θ : ℝ) :
    Tendsto (fun N : ℕ => idealSuccess (uniformSchedule N Θ)) atTop (nhds 1) := by
  have hinv : Tendsto (fun N : ℕ => ((N : ℝ)⁻¹)) atTop (nhds 0) :=
    tendsto_inv_atTop_zero.comp tendsto_natCast_atTop_atTop
  have hx : Tendsto (fun N : ℕ => Θ / (N : ℝ)) atTop (nhds 0) := by
    simpa [div_eq_mul_inv] using tendsto_const_nhds.mul hinv
  have hx2 : Tendsto (fun N : ℕ => (Θ / (N : ℝ)) ^ 2) atTop (nhds 0) := by
    simpa using hx.pow 2
  have hsmall : ∀ᶠ N : ℕ in atTop, (Θ / (N : ℝ)) ^ 2 < 1 :=
    (tendsto_order.1 hx2).2 1 (by norm_num)
  have hNpos : ∀ᶠ N : ℕ in atTop, 0 < N := eventually_atTop.2 ⟨1, fun _ h => h⟩
  have hlower : Tendsto (fun N : ℕ => 1 - Θ ^ 2 * ((N : ℝ)⁻¹)) atTop (nhds 1) := by
    simpa using tendsto_const_nhds.sub (tendsto_const_nhds.mul hinv)
  have hbound : ∀ᶠ N : ℕ in atTop,
      1 - Θ ^ 2 * ((N : ℝ)⁻¹) ≤ idealSuccess (uniformSchedule N Θ) ∧
        idealSuccess (uniformSchedule N Θ) ≤ 1 := by
    filter_upwards [hsmall, hNpos] with N hs hNp
    let x : ℝ := Θ / (N : ℝ)
    have hx2le : x ^ 2 ≤ 1 := le_of_lt hs
    have hbase0 : 0 ≤ 1 - x ^ 2 := sub_nonneg.mpr hx2le
    have hcoslo : 1 - x ^ 2 ≤ Real.cos x ^ 2 := by
      have hc := Real.one_sub_sq_div_two_le_cos (x := x)
      have hc1 : Real.cos x ≤ 1 := Real.cos_le_one x
      have hcm1 : -1 ≤ Real.cos x := Real.neg_one_le_cos x
      have ha : 0 ≤ 1 - Real.cos x := sub_nonneg.mpr hc1
      have hb : 0 ≤ 1 + Real.cos x := by linarith
      have hac : 1 - Real.cos x ≤ x ^ 2 / 2 := by linarith
      have hbd : 1 + Real.cos x ≤ 2 := by linarith
      have hmul := mul_le_mul hac hbd hb (by positivity : 0 ≤ x ^ 2 / 2)
      nlinarith
    have hpowlo : (1 - x ^ 2) ^ N ≤ (Real.cos x ^ 2) ^ N :=
      pow_le_pow_left₀ hbase0 hcoslo N
    have hbern : 1 + (N : ℝ) * (-x ^ 2) ≤ (1 + (-x ^ 2)) ^ N := by
      exact one_add_mul_le_pow (by linarith : (-2 : ℝ) ≤ -x ^ 2) N
    have halg : 1 - Θ ^ 2 * ((N : ℝ)⁻¹) = 1 + (N : ℝ) * (-x ^ 2) := by
      dsimp [x]
      field_simp
      ring
    have hupperbase : Real.cos x ^ 2 ≤ 1 := by
      nlinarith [Real.cos_le_one x, Real.neg_one_le_cos x]
    constructor
    · rw [idealSuccess_uniform_eq]
      change 1 - Θ ^ 2 * ((N : ℝ)⁻¹) ≤ (Real.cos x ^ 2) ^ N
      rw [halg]
      exact hbern.trans (by simpa using hpowlo)
    · rw [idealSuccess_uniform_eq]
      change (Real.cos x ^ 2) ^ N ≤ 1
      simpa using pow_le_one₀ (sq_nonneg (Real.cos x)) hupperbase
  exact hlower.squeeze' tendsto_const_nhds (hbound.mono fun _ h => h.1)
    (hbound.mono fun _ h => h.2)
end Viridis.Run122.PaperFormalization
namespace Viridis.Run122.PaperFormalization
open Real Set Filter Topology
theorem witness_C1 :
    idealSuccess ![(0.2 : ℝ), 0.6] < idealSuccess (uniformSchedule 2 (0.8 : ℝ)) := by
  have hpi : (3 : ℝ) < π := Real.pi_gt_three
  have hδ : ∀ i, (![(0.2 : ℝ), 0.6]) i ∈ admissibleIncrement := by
    intro i
    fin_cases i <;> constructor <;> simp <;> linarith
  have hsum : ∑ i, (![(0.2 : ℝ), 0.6]) i = 0.8 := by
    simp [Fin.sum_univ_two]
    norm_num
  obtain ⟨hle, huniq⟩ := uniform_zeno_schedule_maximizes_success (N := 2) (by norm_num)
    (0.8 : ℝ) ![(0.2 : ℝ), 0.6] hδ hsum
  rcases lt_or_eq_of_le hle with h | h
  · exact h
  · exfalso
    have h0 := huniq h 0
    norm_num at h0
theorem witness_C2 :
    (0.08 : ℝ) ≤
      Real.log (idealSuccess (uniformSchedule 2 (0.8 : ℝ)) / idealSuccess ![(0.2 : ℝ), 0.6]) := by
  have hpi : (3 : ℝ) < π := Real.pi_gt_three
  have hδ : ∀ i, (![(0.2 : ℝ), 0.6]) i ∈ admissibleIncrement := by
    intro i
    fin_cases i <;> constructor <;> simp <;> linarith
  have hsum : ∑ i, (![(0.2 : ℝ), 0.6]) i = 0.8 := by
    simp [Fin.sum_univ_two]
    norm_num
  have h := zeno_schedule_log_gap_ge_variance (N := 2) (by norm_num) (0.8 : ℝ)
    ![(0.2 : ℝ), 0.6] hδ hsum
  have hv : ∑ i, ((![(0.2 : ℝ), 0.6]) i - (0.8 : ℝ) / (2 : ℕ)) ^ 2 = 0.08 := by
    simp [Fin.sum_univ_two]
    norm_num
  rwa [hv] at h
lemma witness_half_pos : (0 : ℝ) < 1 / 2 := by norm_num
lemma witness_half_lt_one : (1 : ℝ) / 2 < 1 := by norm_num
lemma witness_theta_lt : (1 : ℝ) < π / 2 := by linarith [Real.pi_gt_three]
theorem witness_C3_strictConcave :
    (1 : ℝ) ∈ admissibleCount 1 ∧ (2 : ℝ) ∈ admissibleCount 1 ∧
      StrictConcaveOn ℝ (admissibleCount 1) (noisyLogObjective (1 / 2) 1) := by
  refine ⟨one_mem_admissibleCount witness_theta_lt, ?_,
    noisy_zeno_log_objective_strictConcave witness_half_pos witness_half_lt_one one_pos⟩
  have h1 : (2 : ℝ) * 1 / π < 1 := one_mem_admissibleCount witness_theta_lt
  show (2 : ℝ) * 1 / π < 2
  linarith
theorem witness_C3_optimizer :
    (noisyLogDeriv (1 / 2) 1 1 ≤ 0 ∧
        IsMaxOn (noisyLogObjective (1 / 2) 1) (Set.Ici 1) 1) ∨
      (0 < noisyLogDeriv (1 / 2) 1 1 ∧ ∃ nstar : ℝ, 1 < nstar ∧ nstar ∈ admissibleCount 1 ∧
        zenoFirstOrderCondition 1 (1 / 2) nstar ∧
        (∀ m ∈ admissibleCount 1, zenoFirstOrderCondition 1 (1 / 2) m → m = nstar) ∧
        IsMaxOn (noisyLogObjective (1 / 2) 1) (Set.Ici 1) nstar) :=
  noisy_zeno_boundary_or_unique_interior_optimizer witness_half_pos witness_half_lt_one
    one_pos witness_theta_lt
theorem witness_C4 :
    ∃ nstar : ℝ, 1 ≤ nstar ∧ IsMaxOn (noisyLogObjective (1 / 2) 1) (Set.Ici 1) nstar ∧
      ∀ N : ℕ, 1 ≤ N → noisyLogObjective (1 / 2) 1 N ≤
        max (noisyLogObjective (1 / 2) 1 ⌊nstar⌋₊) (noisyLogObjective (1 / 2) 1 ⌈nstar⌉₊) := by
  obtain ⟨nstar, h1, hmax⟩ :=
    exists_optimal_count witness_half_pos witness_half_lt_one one_pos witness_theta_lt
  refine ⟨nstar, h1, hmax, fun N hN => ?_⟩
  exact noisy_zeno_integer_optimum_floor_or_ceil witness_half_pos witness_half_lt_one
    one_pos witness_theta_lt h1 hmax hN
noncomputable def witnessQ : ℕ → ℝ := fun k => Real.exp (-(zenoAngularGain (1 / ((k : ℝ) + 1))))
noncomputable def witnessN : ℕ → ℝ := fun k => (k : ℝ) + 1
lemma witness_x_mem (k : ℕ) : (1 : ℝ) / ((k : ℝ) + 1) ∈ Set.Ico 0 (π / 2) := by
  have hpi : (3 : ℝ) < π := Real.pi_gt_three
  have hk : (0 : ℝ) < (k : ℝ) + 1 := by positivity
  refine ⟨by positivity, ?_⟩
  have h1 : (1 : ℝ) / ((k : ℝ) + 1) ≤ 1 := by
    rw [div_le_one hk]
    have : (0 : ℝ) ≤ (k : ℝ) := Nat.cast_nonneg k
    linarith
  linarith
lemma witness_gain_pos (k : ℕ) : 0 < zenoAngularGain (1 / ((k : ℝ) + 1)) := by
  have h1 := zenoAngularGain_ge_sq (witness_x_mem k)
  have h2 : (0 : ℝ) < (1 / ((k : ℝ) + 1)) ^ 2 := by positivity
  linarith
lemma witnessQ_mem (k : ℕ) : witnessQ k ∈ Set.Ioo (0 : ℝ) 1 :=
  ⟨Real.exp_pos _, Real.exp_lt_one_iff.mpr (by linarith [witness_gain_pos k])⟩
lemma witnessN_mem (k : ℕ) : witnessN k ∈ admissibleCount 1 := by
  have hpi : (3 : ℝ) < π := Real.pi_gt_three
  show 2 * 1 / π < witnessN k
  have h1 : 2 * (1 : ℝ) / π < 1 := by
    rw [div_lt_one (by linarith)]
    linarith
  have h2 : (1 : ℝ) ≤ witnessN k := by simp [witnessN]
  linarith
lemma witness_foc (k : ℕ) : zenoFirstOrderCondition 1 (witnessQ k) (witnessN k) := by
  rw [zenoFirstOrderCondition, noisyLogDeriv_eq, witnessQ, Real.log_exp]
  have h : (1 : ℝ) / witnessN k = 1 / ((k : ℝ) + 1) := by simp [witnessN]
  rw [h]
  ring
lemma witnessQ_tendsto : Tendsto witnessQ atTop (𝓝 1) := by
  have h0 : Tendsto (fun k : ℕ => (1 : ℝ) / ((k : ℝ) + 1)) atTop (𝓝 0) :=
    tendsto_one_div_add_atTop_nhds_zero_nat
  have h1 := continuousAt_zenoAngularGain_zero.tendsto.comp h0
  rw [zenoAngularGain_zero] at h1
  have h1n := h1.neg
  rw [neg_zero] at h1n
  have h2 := (Real.continuous_exp.tendsto 0).comp h1n
  rw [Real.exp_zero] at h2
  exact h2
theorem witness_C5 :
    Tendsto (fun k => witnessN k * Real.sqrt (-Real.log (witnessQ k)) / 1) atTop (𝓝 1) :=
  noisy_zeno_high_quality_asymptotic (Θ := 1) one_pos witnessQ witnessN witnessQ_mem
    witnessQ_tendsto witnessN_mem witness_foc
end Viridis.Run122.PaperFormalization
