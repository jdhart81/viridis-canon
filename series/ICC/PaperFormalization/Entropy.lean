import Mathlib

/-!
# Finite-alphabet Shannon information measures

This file develops, from first principles, the discrete (finite-alphabet, base-two)
Shannon information quantities used by the Run-126 paper
*"The Invariance Capacity Ceiling: Forbidden-Proxy Alignment Caps Predictive Information"*.

Mathlib (at the revision pinned by this project) contains no discrete entropy or mutual
information API, so everything used by the formalized claims is built here:

* `Viridis.Run126.PaperFormalization.Hs` : Shannon entropy `H(p) = -∑ p log₂ p` of a finite mass function;
* `Viridis.Run126.PaperFormalization.JointLaw ρ η σ` : a joint probability law of the triple `(R, Y, S)` on
  finite alphabets `ρ`, `η`, `σ`;
* its six marginals and the associated entropies;
* the information quantities `I(R;Y)`, `I(R;S)`, `I(R;Y|S)`, `I(R;S|Y)`, `H(Y|S)`,
  `H(Y|R,S)`, each defined in **divergence form** (as an expectation of a log-ratio),
  i.e. *not* defined by the entropy-algebra identities that the paper's Theorem 1 asserts;
* the chain-rule lemmas converting each divergence form into an entropy combination;
* nonnegativity of conditional mutual information and of conditional entropy, via a
  Gibbs / log-sum inequality proved here (`Viridis.Run126.PaperFormalization.sum_mul_logb_le`).

Conventions: `Real.logb 2 0 = 0`, so a mass-zero outcome contributes `0` to every sum,
which is the standard `0 log 0 = 0` convention of information theory.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-- Shannon entropy, in bits, of a finite mass function `p`.
With Lean's convention `Real.logb 2 0 = 0` this implements `0 log 0 = 0`. -/
noncomputable def Hs {α : Type*} [Fintype α] (p : α → ℝ) : ℝ :=
  -∑ a, p a * Real.logb 2 (p a)

/-! ### A Gibbs (log-sum) inequality -/

/-- **Gibbs' inequality**, in the form needed below: if `p` and `q` are nonnegative,
`q` is absolutely continuous with respect to `p` (`p a ≠ 0 → q a ≠ 0`) and the total mass
of `q` does not exceed that of `p`, then `∑ p log₂ q ≤ ∑ p log₂ p`. -/
theorem sum_mul_logb_le {α : Type*} [Fintype α] (p q : α → ℝ)
    (hp : ∀ a, 0 ≤ p a) (hq : ∀ a, 0 ≤ q a)
    (hac : ∀ a, p a ≠ 0 → q a ≠ 0)
    (hsum : ∑ a, q a ≤ ∑ a, p a) :
    ∑ a, p a * Real.logb 2 (q a) ≤ ∑ a, p a * Real.logb 2 (p a) := by
  have hlog2 : (0 : ℝ) < Real.log 2 := Real.log_pos (by norm_num)
  have key : ∀ a, p a * Real.logb 2 (q a) - p a * Real.logb 2 (p a)
      ≤ (q a - p a) / Real.log 2 := by
    intro a
    rcases eq_or_lt_of_le (hp a) with h0 | hpos
    · rw [← h0]
      have hz : (0:ℝ) * Real.logb 2 (q a) - 0 * Real.logb 2 0 = 0 := by ring
      rw [hz, sub_zero]
      exact div_nonneg (hq a) hlog2.le
    · have hqpos : 0 < q a := lt_of_le_of_ne (hq a) (Ne.symm (hac a (ne_of_gt hpos)))
      have hle : Real.log (q a / p a) ≤ q a / p a - 1 :=
        Real.log_le_sub_one_of_pos (div_pos hqpos hpos)
      have hsplit : Real.log (q a / p a) = Real.log (q a) - Real.log (p a) :=
        Real.log_div (ne_of_gt hqpos) (ne_of_gt hpos)
      have hmul := mul_le_mul_of_nonneg_left hle (le_of_lt hpos)
      rw [hsplit] at hmul
      have hexp : p a * (q a / p a - 1) = q a - p a := by
        field_simp
      rw [hexp] at hmul
      have : p a * Real.logb 2 (q a) - p a * Real.logb 2 (p a)
          = (p a * (Real.log (q a) - Real.log (p a))) / Real.log 2 := by
        unfold Real.logb; ring
      rw [this]
      exact div_le_div_of_nonneg_right hmul hlog2.le
  have hsum' : ∑ a, (p a * Real.logb 2 (q a) - p a * Real.logb 2 (p a))
      ≤ ∑ a, (q a - p a) / Real.log 2 := Finset.sum_le_sum fun a _ => key a
  have hrhs : ∑ a, (q a - p a) / Real.log 2 ≤ 0 := by
    rw [← Finset.sum_div, Finset.sum_sub_distrib]
    exact div_nonpos_of_nonpos_of_nonneg (by linarith) (le_of_lt hlog2)
  rw [Finset.sum_sub_distrib] at hsum'
  linarith

/-! ### Joint laws on finite alphabets -/

/-- A joint probability law of `(R, Y, S)` on the finite alphabets `ρ`, `η`, `σ`.
This is the paper's setting: "`R, Y, S` discrete random variables with finite alphabets",
represented by their joint probability mass function. -/
structure JointLaw (ρ η σ : Type*) [Fintype ρ] [Fintype η] [Fintype σ] where
  /-- The joint probability mass function `p r y s = P(R = r, Y = y, S = s)`. -/
  p : ρ → η → σ → ℝ
  nonneg : ∀ r y s, 0 ≤ p r y s
  total : ∑ r, ∑ y, ∑ s, p r y s = 1

namespace JointLaw

variable {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ] (J : JointLaw ρ η σ)

/-- The joint law of `(R, Y, S)`, as a mass function on the product alphabet. -/
def pRYS : ρ × η × σ → ℝ := fun x => J.p x.1 x.2.1 x.2.2

/-- The marginal law of `(R, Y)`. -/
def pRY : ρ × η → ℝ := fun x => ∑ s, J.p x.1 x.2 s

/-- The marginal law of `(R, S)`. -/
def pRS : ρ × σ → ℝ := fun x => ∑ y, J.p x.1 y x.2

/-- The marginal law of `(Y, S)`. -/
def pYS : η × σ → ℝ := fun x => ∑ r, J.p r x.1 x.2

/-- The marginal law of `R`. -/
def pR : ρ → ℝ := fun r => ∑ y, ∑ s, J.p r y s

/-- The marginal law of `Y`. -/
def pY : η → ℝ := fun y => ∑ r, ∑ s, J.p r y s

/-- The marginal law of `S`. -/
def pS : σ → ℝ := fun s => ∑ r, ∑ y, J.p r y s

/-! #### Nonnegativity, comparison and normalisation of the marginals -/

lemma pRYS_nonneg (x : ρ × η × σ) : 0 ≤ J.pRYS x := J.nonneg _ _ _

lemma pRY_nonneg (x : ρ × η) : 0 ≤ J.pRY x :=
  Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma pRS_nonneg (x : ρ × σ) : 0 ≤ J.pRS x :=
  Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma pYS_nonneg (x : η × σ) : 0 ≤ J.pYS x :=
  Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma pR_nonneg (r : ρ) : 0 ≤ J.pR r :=
  Finset.sum_nonneg fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma pY_nonneg (y : η) : 0 ≤ J.pY y :=
  Finset.sum_nonneg fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma pS_nonneg (s : σ) : 0 ≤ J.pS s :=
  Finset.sum_nonneg fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _

lemma p_le_pRY (r : ρ) (y : η) (s : σ) : J.p r y s ≤ J.pRY (r, y) :=
  Finset.single_le_sum (f := fun s => J.p r y s) (fun _ _ => J.nonneg _ _ _) (mem_univ s)

lemma p_le_pRS (r : ρ) (y : η) (s : σ) : J.p r y s ≤ J.pRS (r, s) :=
  Finset.single_le_sum (f := fun y => J.p r y s) (fun _ _ => J.nonneg _ _ _) (mem_univ y)

lemma p_le_pYS (r : ρ) (y : η) (s : σ) : J.p r y s ≤ J.pYS (y, s) :=
  Finset.single_le_sum (f := fun r => J.p r y s) (fun _ _ => J.nonneg _ _ _) (mem_univ r)

lemma pRY_le_pR (r : ρ) (y : η) : J.pRY (r, y) ≤ J.pR r :=
  Finset.single_le_sum (f := fun y => ∑ s, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ y)

lemma pRY_le_pY (r : ρ) (y : η) : J.pRY (r, y) ≤ J.pY y :=
  Finset.single_le_sum (f := fun r => ∑ s, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ r)

lemma pRS_le_pR (r : ρ) (s : σ) : J.pRS (r, s) ≤ J.pR r := by
  have h : J.pR r = ∑ s, ∑ y, J.p r y s := by
    simp only [pR]; exact Finset.sum_comm
  rw [h]
  exact Finset.single_le_sum (f := fun s => ∑ y, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ s)

lemma pRS_le_pS (r : ρ) (s : σ) : J.pRS (r, s) ≤ J.pS s :=
  Finset.single_le_sum (f := fun r => ∑ y, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ r)

lemma pYS_le_pY (y : η) (s : σ) : J.pYS (y, s) ≤ J.pY y := by
  have h : J.pY y = ∑ s, ∑ r, J.p r y s := by
    simp only [pY]; exact Finset.sum_comm
  rw [h]
  exact Finset.single_le_sum (f := fun s => ∑ r, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ s)

lemma pYS_le_pS (y : η) (s : σ) : J.pYS (y, s) ≤ J.pS s := by
  have h : J.pS s = ∑ y, ∑ r, J.p r y s := by
    simp only [pS]; exact Finset.sum_comm
  rw [h]
  exact Finset.single_le_sum (f := fun y => ∑ r, J.p r y s)
    (fun _ _ => Finset.sum_nonneg fun _ _ => J.nonneg _ _ _) (mem_univ y)

lemma sum_pRY : ∑ r, ∑ y, J.pRY (r, y) = 1 := J.total

lemma sum_pR : ∑ r, J.pR r = 1 := J.total

lemma sum_pY : ∑ y, J.pY y = 1 := by
  rw [show (∑ y, J.pY y) = ∑ r, ∑ y, ∑ s, J.p r y s by
    simp only [pY]; exact Finset.sum_comm]
  exact J.total

lemma sum_pS : ∑ s, J.pS s = 1 := by
  rw [show (∑ s, J.pS s) = ∑ r, ∑ y, ∑ s, J.p r y s by
    simp only [pS]
    rw [Finset.sum_comm]
    exact Finset.sum_congr rfl fun r _ => Finset.sum_comm]
  exact J.total

/-! #### Entropies -/

/-- Joint entropy `H(R, Y, S)`. -/
noncomputable def H_RYS : ℝ := Hs J.pRYS
/-- Joint entropy `H(R, Y)`. -/
noncomputable def H_RY : ℝ := Hs J.pRY
/-- Joint entropy `H(R, S)`. -/
noncomputable def H_RS : ℝ := Hs J.pRS
/-- Joint entropy `H(Y, S)`. -/
noncomputable def H_YS : ℝ := Hs J.pYS
/-- Entropy `H(R)`. -/
noncomputable def H_R : ℝ := Hs J.pR
/-- Entropy `H(Y)`. -/
noncomputable def H_Y : ℝ := Hs J.pY
/-- Entropy `H(S)`. -/
noncomputable def H_S : ℝ := Hs J.pS

/-! #### Information quantities, in divergence form

Each quantity below is defined directly as an expectation of a log-ratio, i.e. as a
Kullback–Leibler divergence, *not* as a combination of entropies.  The entropy-algebra
formulas are proved as lemmas (`I_RY_eq`, `I_RS_given_Y_eq`, ...), so that the paper's
Theorem 1 is a genuine statement rather than an unfolding of definitions. -/

/-- Mutual information `I(R;Y) = ∑ p(r,y) log₂ (p(r,y) / (p(r) p(y)))`. -/
noncomputable def I_RY : ℝ :=
  ∑ r, ∑ y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y) / (J.pR r * J.pY y))

/-- Mutual information `I(R;S) = ∑ p(r,s) log₂ (p(r,s) / (p(r) p(s)))`. -/
noncomputable def I_RS : ℝ :=
  ∑ r, ∑ s, J.pRS (r, s) * Real.logb 2 (J.pRS (r, s) / (J.pR r * J.pS s))

/-- Conditional mutual information
`I(R;Y|S) = ∑ p(r,y,s) log₂ (p(r,y,s) p(s) / (p(r,s) p(y,s)))`. -/
noncomputable def I_RY_given_S : ℝ :=
  ∑ r, ∑ y, ∑ s, J.p r y s *
    Real.logb 2 (J.p r y s * J.pS s / (J.pRS (r, s) * J.pYS (y, s)))

/-- Conditional mutual information
`I(R;S|Y) = ∑ p(r,y,s) log₂ (p(r,y,s) p(y) / (p(r,y) p(y,s)))`. -/
noncomputable def I_RS_given_Y : ℝ :=
  ∑ r, ∑ y, ∑ s, J.p r y s *
    Real.logb 2 (J.p r y s * J.pY y / (J.pRY (r, y) * J.pYS (y, s)))

/-- Conditional entropy `H(Y|S) = -∑ p(y,s) log₂ (p(y,s) / p(s))`. -/
noncomputable def H_Y_given_S : ℝ :=
  -∑ y, ∑ s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s) / J.pS s)

/-- Conditional entropy `H(Y|R,S) = -∑ p(r,y,s) log₂ (p(r,y,s) / p(r,s))`. -/
noncomputable def H_Y_given_RS : ℝ :=
  -∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (J.p r y s / J.pRS (r, s))

end JointLaw

end Viridis.Run126.PaperFormalization
