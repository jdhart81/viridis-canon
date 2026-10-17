/- Engine-3 immutable source unit: Entropy.lean -/
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

/- Engine-3 immutable source unit: ChainRule.lean -/

/-!
# Chain rules and nonnegativity for the finite-alphabet information measures

The information quantities of `PaperFormalization.Entropy` are defined in divergence form.
Here we prove:

* the marginalisation lemmas relating the six marginals of a `JointLaw`;
* the *entropy-algebra* formulas for each information quantity (`I_RY_eq`, `I_RS_eq`,
  `I_RY_given_S_eq`, `I_RS_given_Y_eq`, `H_Y_given_S_eq`, `H_Y_given_RS_eq`);
* nonnegativity of `I(R;Y)`, `I(R;S|Y)` (Gibbs' inequality) and of `H(Y|R,S)`.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-! ### Elementary `x * logb` manipulations, valid with the `0 log 0 = 0` convention -/

lemma mul_logb_two {x c : ℝ} (hx : 0 ≤ x) (hc : x ≠ 0 → 0 < c) :
    x * Real.logb 2 (x / c) = x * (Real.logb 2 x - Real.logb 2 c) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    rw [Real.logb_div hxne (ne_of_gt (hc hxne))]

lemma mul_logb_three {x c d : ℝ} (hx : 0 ≤ x) (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (x / (c * d)) = x * (Real.logb 2 x - Real.logb 2 c - Real.logb 2 d) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div hxne (by positivity), Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]
    ring

lemma mul_logb_four {x b c d : ℝ} (hx : 0 ≤ x) (hb : x ≠ 0 → 0 < b)
    (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (x * b / (c * d))
      = x * (Real.logb 2 x + Real.logb 2 b - Real.logb 2 c - Real.logb 2 d) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hbp := hb hxne
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div (by positivity) (by positivity), Real.logb_mul hxne (ne_of_gt hbp),
      Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]
    ring

lemma mul_logb_quot3 {x b c d : ℝ} (hx : 0 ≤ x) (hb : x ≠ 0 → 0 < b)
    (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (c * d / b)
      = x * (Real.logb 2 c + Real.logb 2 d - Real.logb 2 b) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hbp := hb hxne
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div (by positivity) (by positivity),
      Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]

namespace JointLaw

variable {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ] (J : JointLaw ρ η σ)

/-! ### Marginalisation -/

lemma sum_s_p (r : ρ) (y : η) : ∑ s, J.p r y s = J.pRY (r, y) := rfl
lemma sum_y_p (r : ρ) (s : σ) : ∑ y, J.p r y s = J.pRS (r, s) := rfl
lemma sum_r_p (y : η) (s : σ) : ∑ r, J.p r y s = J.pYS (y, s) := rfl
lemma sum_y_pRY (r : ρ) : ∑ y, J.pRY (r, y) = J.pR r := rfl
lemma sum_r_pRY (y : η) : ∑ r, J.pRY (r, y) = J.pY y := rfl
lemma sum_r_pRS (s : σ) : ∑ r, J.pRS (r, s) = J.pS s := rfl

lemma sum_s_pRS (r : ρ) : ∑ s, J.pRS (r, s) = J.pR r := by
  simp only [pRS, pR]; exact Finset.sum_comm

lemma sum_s_pYS (y : η) : ∑ s, J.pYS (y, s) = J.pY y := by
  simp only [pYS, pY]; exact Finset.sum_comm

lemma sum_y_pYS (s : σ) : ∑ y, J.pYS (y, s) = J.pS s := by
  simp only [pYS, pS]; exact Finset.sum_comm

/-! ### Reduction of triple sums to marginal sums -/

lemma sum3_of_RY (f : ρ → η → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r y = ∑ r, ∑ y, J.pRY (r, y) * f r y :=
  Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => by
    rw [← Finset.sum_mul, sum_s_p]

lemma sum3_of_RS (f : ρ → σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r s = ∑ r, ∑ s, J.pRS (r, s) * f r s := by
  refine Finset.sum_congr rfl fun r _ => ?_
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_y_p]

lemma sum3_of_YS (f : η → σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f y s = ∑ y, ∑ s, J.pYS (y, s) * f y s := by
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun y _ => ?_
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_p]

lemma sum3_of_R (f : ρ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r = ∑ r, J.pR r * f r := by
  rw [J.sum3_of_RY (fun r _ => f r)]
  exact Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_y_pRY]

lemma sum3_of_Y (f : η → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f y = ∑ y, J.pY y * f y := by
  rw [J.sum3_of_RY (fun _ y => f y), Finset.sum_comm]
  exact Finset.sum_congr rfl fun y _ => by rw [← Finset.sum_mul, sum_r_pRY]

lemma sum3_of_S (f : σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f s = ∑ s, J.pS s * f s := by
  rw [J.sum3_of_RS (fun _ s => f s), Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_pRS]

lemma sum2RY_of_R (f : ρ → ℝ) :
    ∑ r, ∑ y, J.pRY (r, y) * f r = ∑ r, J.pR r * f r :=
  Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_y_pRY]

lemma sum2RY_of_Y (f : η → ℝ) :
    ∑ r, ∑ y, J.pRY (r, y) * f y = ∑ y, J.pY y * f y := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun y _ => by rw [← Finset.sum_mul, sum_r_pRY]

lemma sum2RS_of_R (f : ρ → ℝ) :
    ∑ r, ∑ s, J.pRS (r, s) * f r = ∑ r, J.pR r * f r :=
  Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_s_pRS]

lemma sum2RS_of_S (f : σ → ℝ) :
    ∑ r, ∑ s, J.pRS (r, s) * f s = ∑ s, J.pS s * f s := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_pRS]

lemma sum2YS_of_S (f : σ → ℝ) :
    ∑ y, ∑ s, J.pYS (y, s) * f s = ∑ s, J.pS s * f s := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_y_pYS]

/-! ### Entropies as explicit sums -/

lemma H_RYS_eq_sum :
    J.H_RYS = -∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (J.p r y s) := by
  simp [H_RYS, Hs, pRYS, Fintype.sum_prod_type]

lemma H_RY_eq_sum :
    J.H_RY = -∑ r, ∑ y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y)) := by
  simp [H_RY, Hs, Fintype.sum_prod_type]

lemma H_RS_eq_sum :
    J.H_RS = -∑ r, ∑ s, J.pRS (r, s) * Real.logb 2 (J.pRS (r, s)) := by
  simp [H_RS, Hs, Fintype.sum_prod_type]

lemma H_YS_eq_sum :
    J.H_YS = -∑ y, ∑ s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s)) := by
  simp [H_YS, Hs, Fintype.sum_prod_type]

lemma H_R_eq_sum : J.H_R = -∑ r, J.pR r * Real.logb 2 (J.pR r) := rfl
lemma H_Y_eq_sum : J.H_Y = -∑ y, J.pY y * Real.logb 2 (J.pY y) := rfl
lemma H_S_eq_sum : J.H_S = -∑ s, J.pS s * Real.logb 2 (J.pS s) := rfl

/-! ### Chain rules: divergence forms equal entropy combinations -/

/-- `H(Y|S) = H(Y,S) - H(S)`. -/
theorem H_Y_given_S_eq : J.H_Y_given_S = J.H_YS - J.H_S := by
  have hterm : ∀ y s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s) / J.pS s)
      = J.pYS (y, s) * Real.logb 2 (J.pYS (y, s)) - J.pYS (y, s) * Real.logb 2 (J.pS s) := by
    intro y s
    rw [mul_logb_two (J.pYS_nonneg (y, s))
      (fun h => lt_of_lt_of_le (lt_of_le_of_ne (J.pYS_nonneg (y, s)) (Ne.symm h))
        (J.pYS_le_pS y s))]
    ring
  simp only [H_Y_given_S]
  rw [Finset.sum_congr rfl fun y _ => Finset.sum_congr rfl fun s _ => hterm y s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2YS_of_S (fun s => Real.logb 2 (J.pS s)), H_YS_eq_sum, H_S_eq_sum]
  ring

/-- `H(Y|R,S) = H(R,Y,S) - H(R,S)`. -/
theorem H_Y_given_RS_eq : J.H_Y_given_RS = J.H_RYS - J.H_RS := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s / J.pRS (r, s))
      = J.p r y s * Real.logb 2 (J.p r y s) - J.p r y s * Real.logb 2 (J.pRS (r, s)) := by
    intro r y s
    rw [mul_logb_two (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)) (J.p_le_pRS r y s))]
    ring
  simp only [H_Y_given_RS]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum3_of_RS (fun r s => Real.logb 2 (J.pRS (r, s))), H_RYS_eq_sum, H_RS_eq_sum]
  ring

/-- `I(R;Y) = H(R) + H(Y) - H(R,Y)`. -/
theorem I_RY_eq : J.I_RY = J.H_R + J.H_Y - J.H_RY := by
  have hterm : ∀ r y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y) / (J.pR r * J.pY y))
      = J.pRY (r, y) * Real.logb 2 (J.pRY (r, y)) - J.pRY (r, y) * Real.logb 2 (J.pR r)
        - J.pRY (r, y) * Real.logb 2 (J.pY y) := by
    intro r y
    have hpos : J.pRY (r, y) ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    rw [mul_logb_three (J.pRY_nonneg (r, y))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRY_le_pR r y))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRY_le_pY r y))]
    ring
  simp only [I_RY]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => hterm r y]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2RY_of_R (fun r => Real.logb 2 (J.pR r)), J.sum2RY_of_Y (fun y => Real.logb 2 (J.pY y)),
    H_RY_eq_sum, H_R_eq_sum, H_Y_eq_sum]
  ring

/-- `I(R;S) = H(R) + H(S) - H(R,S)`. -/
theorem I_RS_eq : J.I_RS = J.H_R + J.H_S - J.H_RS := by
  have hterm : ∀ r s, J.pRS (r, s) * Real.logb 2 (J.pRS (r, s) / (J.pR r * J.pS s))
      = J.pRS (r, s) * Real.logb 2 (J.pRS (r, s)) - J.pRS (r, s) * Real.logb 2 (J.pR r)
        - J.pRS (r, s) * Real.logb 2 (J.pS s) := by
    intro r s
    have hpos : J.pRS (r, s) ≠ 0 → 0 < J.pRS (r, s) := fun h =>
      lt_of_le_of_ne (J.pRS_nonneg (r, s)) (Ne.symm h)
    rw [mul_logb_three (J.pRS_nonneg (r, s))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRS_le_pR r s))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRS_le_pS r s))]
    ring
  simp only [I_RS]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun s _ => hterm r s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2RS_of_R (fun r => Real.logb 2 (J.pR r)), J.sum2RS_of_S (fun s => Real.logb 2 (J.pS s)),
    H_RS_eq_sum, H_R_eq_sum, H_S_eq_sum]
  ring

/-- `I(R;Y|S) = H(R,S) + H(Y,S) - H(R,Y,S) - H(S)`. -/
theorem I_RY_given_S_eq : J.I_RY_given_S = J.H_RS + J.H_YS - J.H_RYS - J.H_S := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pS s / (J.pRS (r, s) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) + J.p r y s * Real.logb 2 (J.pS s)
        - J.p r y s * Real.logb 2 (J.pRS (r, s)) - J.p r y s * Real.logb 2 (J.pYS (y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    rw [mul_logb_four (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (hpos h) (le_trans (J.p_le_pRS r y s) (J.pRS_le_pS r s)))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pRS r y s))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s))]
    ring
  simp only [I_RY_given_S]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib]
  rw [J.sum3_of_S (fun s => Real.logb 2 (J.pS s)),
    J.sum3_of_RS (fun r s => Real.logb 2 (J.pRS (r, s))),
    J.sum3_of_YS (fun y s => Real.logb 2 (J.pYS (y, s))),
    H_RYS_eq_sum, H_RS_eq_sum, H_YS_eq_sum, H_S_eq_sum]
  ring

/-- `I(R;S|Y) = H(R,Y) + H(Y,S) - H(R,Y,S) - H(Y)`. -/
theorem I_RS_given_Y_eq : J.I_RS_given_Y = J.H_RY + J.H_YS - J.H_RYS - J.H_Y := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pY y / (J.pRY (r, y) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) + J.p r y s * Real.logb 2 (J.pY y)
        - J.p r y s * Real.logb 2 (J.pRY (r, y)) - J.p r y s * Real.logb 2 (J.pYS (y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    rw [mul_logb_four (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (hpos h) (le_trans (J.p_le_pRY r y s) (J.pRY_le_pY r y)))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s))]
    ring
  simp only [I_RS_given_Y]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib]
  rw [J.sum3_of_Y (fun y => Real.logb 2 (J.pY y)),
    J.sum3_of_RY (fun r y => Real.logb 2 (J.pRY (r, y))),
    J.sum3_of_YS (fun y s => Real.logb 2 (J.pYS (y, s))),
    H_RYS_eq_sum, H_RY_eq_sum, H_YS_eq_sum, H_Y_eq_sum]
  ring

/-! ### Nonnegativity -/

/-- Conditional entropy is nonnegative: `H(Y|R,S) ≥ 0`. -/
theorem H_Y_given_RS_nonneg : 0 ≤ J.H_Y_given_RS := by
  simp only [H_Y_given_RS, neg_nonneg]
  refine Finset.sum_nonpos fun r _ => Finset.sum_nonpos fun y _ => Finset.sum_nonpos fun s _ => ?_
  rcases eq_or_lt_of_le (J.nonneg r y s) with h0 | hpos
  · simp [← h0]
  · refine mul_nonpos_of_nonneg_of_nonpos (J.nonneg r y s) ?_
    refine Real.logb_nonpos (by norm_num)
      (div_nonneg (J.nonneg r y s) (J.pRS_nonneg (r, s))) ?_
    rw [div_le_one (lt_of_lt_of_le hpos (J.p_le_pRS r y s))]
    exact J.p_le_pRS r y s

/-- Mutual information is nonnegative: `I(R;Y) ≥ 0`. -/
theorem I_RY_nonneg : 0 ≤ J.I_RY := by
  have hQnonneg : ∀ x : ρ × η, 0 ≤ J.pR x.1 * J.pY x.2 := fun x =>
    mul_nonneg (J.pR_nonneg x.1) (J.pY_nonneg x.2)
  have hac : ∀ x : ρ × η, J.pRY x ≠ 0 → J.pR x.1 * J.pY x.2 ≠ 0 := by
    rintro ⟨r, y⟩ h
    have hpos : 0 < J.pRY (r, y) := lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    exact ne_of_gt (mul_pos (lt_of_lt_of_le hpos (J.pRY_le_pR r y))
      (lt_of_lt_of_le hpos (J.pRY_le_pY r y)))
  have hsum : ∑ x : ρ × η, J.pR x.1 * J.pY x.2 ≤ ∑ x : ρ × η, J.pRY x := by
    rw [Fintype.sum_prod_type, Fintype.sum_prod_type]
    have h1 : ∑ r, ∑ y, J.pR r * J.pY y = 1 := by
      rw [Finset.sum_congr rfl fun r _ => by rw [← Finset.mul_sum, J.sum_pY, mul_one]]
      exact J.sum_pR
    rw [h1, J.sum_pRY]
  have gibbs := sum_mul_logb_le J.pRY (fun x => J.pR x.1 * J.pY x.2)
    (fun x => J.pRY_nonneg x) hQnonneg hac hsum
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type] at gibbs
  have hterm : ∀ r y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y) / (J.pR r * J.pY y))
      = J.pRY (r, y) * Real.logb 2 (J.pRY (r, y))
        - J.pRY (r, y) * Real.logb 2 (J.pR r * J.pY y) := by
    intro r y
    have hpos : J.pRY (r, y) ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    rcases eq_or_lt_of_le (J.pRY_nonneg (r, y)) with h0 | hp
    · simp [← h0]
    · have hRpos := lt_of_lt_of_le hp (J.pRY_le_pR r y)
      have hYpos := lt_of_lt_of_le hp (J.pRY_le_pY r y)
      rw [Real.logb_div (ne_of_gt hp) (by positivity)]
      ring
  simp only [I_RY]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => hterm r y]
  simp only [Finset.sum_sub_distrib]
  linarith

/-- Conditional mutual information is nonnegative: `I(R;S|Y) ≥ 0`.
This is Gibbs' inequality applied to the joint law against the product-form kernel
`p(r,y) p(y,s) / p(y)`. -/
theorem I_RS_given_Y_nonneg : 0 ≤ J.I_RS_given_Y := by
  set Q : ρ × η × σ → ℝ :=
    fun x => J.pRY (x.1, x.2.1) * J.pYS (x.2.1, x.2.2) / J.pY x.2.1 with hQ
  have hQnonneg : ∀ x, 0 ≤ Q x := by
    rintro ⟨r, y, s⟩
    exact div_nonneg (mul_nonneg (J.pRY_nonneg (r, y)) (J.pYS_nonneg (y, s))) (J.pY_nonneg y)
  have hac : ∀ x, J.pRYS x ≠ 0 → Q x ≠ 0 := by
    rintro ⟨r, y, s⟩ h
    have hpos : 0 < J.p r y s := lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    have h1 : 0 < J.pRY (r, y) := lt_of_lt_of_le hpos (J.p_le_pRY r y s)
    have h2 : 0 < J.pYS (y, s) := lt_of_lt_of_le hpos (J.p_le_pYS r y s)
    have h3 : 0 < J.pY y := lt_of_lt_of_le h1 (J.pRY_le_pY r y)
    exact ne_of_gt (div_pos (mul_pos h1 h2) h3)
  have hsum : ∑ x, Q x ≤ ∑ x, J.pRYS x := by
    have hQsum : ∑ x, Q x = ∑ y, (J.pY y * J.pY y) / J.pY y := by
      simp only [hQ, Fintype.sum_prod_type]
      rw [Finset.sum_comm]
      refine Finset.sum_congr rfl fun y _ => ?_
      have h1 : ∀ r, ∑ s, J.pRY (r, y) * J.pYS (y, s) / J.pY y
          = J.pRY (r, y) * J.pY y / J.pY y := by
        intro r
        rw [← Finset.sum_div, ← Finset.mul_sum, J.sum_s_pYS]
      rw [Finset.sum_congr rfl fun r _ => h1 r, ← Finset.sum_div, ← Finset.sum_mul, J.sum_r_pRY]
    have hle : ∑ y, (J.pY y * J.pY y) / J.pY y ≤ ∑ y, J.pY y := by
      refine Finset.sum_le_sum fun y _ => ?_
      rcases eq_or_lt_of_le (J.pY_nonneg y) with h0 | hp
      · simp [← h0]
      · rw [mul_div_assoc, div_self (ne_of_gt hp), mul_one]
    rw [hQsum]
    calc ∑ y, (J.pY y * J.pY y) / J.pY y ≤ ∑ y, J.pY y := hle
      _ = 1 := J.sum_pY
      _ = ∑ x, J.pRYS x := by
          rw [Fintype.sum_prod_type]
          simpa [pRYS, Fintype.sum_prod_type] using J.total.symm
  have gibbs := sum_mul_logb_le J.pRYS Q (fun x => J.pRYS_nonneg x) hQnonneg hac hsum
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type] at gibbs
  simp only [Fintype.sum_prod_type] at gibbs
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pY y / (J.pRY (r, y) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) - J.p r y s * Real.logb 2 (Q (r, y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    have hb : J.p r y s ≠ 0 → 0 < J.pY y := fun h =>
      lt_of_lt_of_le (lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s)) (J.pRY_le_pY r y)
    have hc : J.p r y s ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s)
    have hd : J.p r y s ≠ 0 → 0 < J.pYS (y, s) := fun h =>
      lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s)
    rw [mul_logb_four (J.nonneg r y s) hb hc hd]
    simp only [hQ]
    rw [mul_logb_quot3 (J.nonneg r y s) hb hc hd]
    ring
  simp only [I_RS_given_Y]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib]
  have : ∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (Q (r, y, s))
      ≤ ∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (J.p r y s) := gibbs
  linarith

end JointLaw

end Viridis.Run126.PaperFormalization

/- Engine-3 immutable source unit: Claims.lean -/

/-!
# The frozen Run-126 claims C1–C4

This file states and proves the first four named targets of `STATEMENT_CONTRACT.md`:

* `mutual_information_chain_balance`      (C1, Theorem 1, Eq. 1);
* `forbidden_proxy_capacity_ceiling`      (C2, Corollary 1, Eq. 2);
* `capacity_ceiling_slack_decomposition`  (C3, Theorem 1, Eq. 3);
* `perfect_invariance_target_proxy_collapse` (C4, Boundary cases).

Target C5 (`erasure_family_tightness`, Proposition 1) is in
`PaperFormalization.ErasureFamily`.

Each claim is followed by explicit non-vacuity witnesses: concrete finite joint laws for
which the hypotheses hold and all quantities appearing in the statement are computed.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-! ### Numerical values of `logb 2` used by the witnesses -/

lemma logb2_two : Real.logb 2 (2 : ℝ) = 1 := Real.logb_self_eq_one (by norm_num)

lemma logb2_half : Real.logb 2 (1 / 2 : ℝ) = -1 := by
  rw [one_div, Real.logb_inv, logb2_two]

lemma logb2_quarter : Real.logb 2 (1 / 4 : ℝ) = -2 := by
  have h : (1 / 4 : ℝ) = (1 / 2) * (1 / 2) := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_half]
  norm_num

lemma logb2_eighth : Real.logb 2 (1 / 8 : ℝ) = -3 := by
  have h : (1 / 8 : ℝ) = (1 / 4) * (1 / 2) := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_half, logb2_quarter]
  norm_num

/-! ### C1 — `mutual_information_chain_balance` (Theorem 1, Eq. 1)

Paper statement: for finite `R, Y, S`, `I(R;Y) = I(R;Y|S) + I(R;S) - I(R;S|Y)`. -/

/-- **C1 (Theorem 1, Eq. 1).** For every finite joint law of `(R, Y, S)`,
`I(R;Y) = I(R;Y|S) + I(R;S) - I(R;S|Y)`. -/
theorem mutual_information_chain_balance {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) :
    J.I_RY = J.I_RY_given_S + J.I_RS - J.I_RS_given_Y := by
  rw [J.I_RY_eq, J.I_RY_given_S_eq, J.I_RS_eq, J.I_RS_given_Y_eq]
  ring

/-! ### C2 — `forbidden_proxy_capacity_ceiling` (Corollary 1, Eq. 2)

Paper statement: if `I(R;S) ≤ δ` then `I(R;Y) ≤ H(Y|S) + δ`. -/

/-- **C2 (Corollary 1, Eq. 2).** A forbidden-proxy leakage budget `I(R;S) ≤ δ` implies the
task-information ceiling `I(R;Y) ≤ H(Y|S) + δ`. -/
theorem forbidden_proxy_capacity_ceiling {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) (δ : ℝ) (hδ : J.I_RS ≤ δ) :
    J.I_RY ≤ J.H_Y_given_S + δ := by
  have h1 := J.H_Y_given_RS_nonneg
  have h2 := J.I_RS_given_Y_nonneg
  have hbal : J.H_Y_given_S + J.I_RS - J.I_RY = J.H_Y_given_RS + J.I_RS_given_Y := by
    rw [J.H_Y_given_S_eq, J.I_RS_eq, J.I_RY_eq, J.H_Y_given_RS_eq, J.I_RS_given_Y_eq]
    ring
  linarith

/-- **C2, Eq. 4 (combined ceiling).** If an independently justified ceiling `C` also holds,
then `I(R;Y) ≤ min C (H(Y|S) + δ)`. -/
theorem forbidden_proxy_capacity_ceiling_combined {ρ η σ : Type*} [Fintype ρ] [Fintype η]
    [Fintype σ] (J : JointLaw ρ η σ) (δ C : ℝ) (hδ : J.I_RS ≤ δ) (hC : J.I_RY ≤ C) :
    J.I_RY ≤ min C (J.H_Y_given_S + δ) :=
  le_min hC (forbidden_proxy_capacity_ceiling J δ hδ)

/-! ### C3 — `capacity_ceiling_slack_decomposition` (Theorem 1, Eq. 3)

Paper statement: `H(Y|S) + I(R;S) - I(R;Y) = H(Y|R,S) + I(R;S|Y) ≥ 0`. -/

/-- **C3 (Theorem 1, Eq. 3).** The ceiling slack decomposes exactly as
`H(Y|S) + I(R;S) - I(R;Y) = H(Y|R,S) + I(R;S|Y)`, and this common value is nonnegative. -/
theorem capacity_ceiling_slack_decomposition {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) :
    J.H_Y_given_S + J.I_RS - J.I_RY = J.H_Y_given_RS + J.I_RS_given_Y ∧
      0 ≤ J.H_Y_given_RS + J.I_RS_given_Y := by
  constructor
  · rw [J.H_Y_given_S_eq, J.I_RS_eq, J.I_RY_eq, J.H_Y_given_RS_eq, J.I_RS_given_Y_eq]
    ring
  · linarith [J.H_Y_given_RS_nonneg, J.I_RS_given_Y_nonneg]

/-! ### C4 — `perfect_invariance_target_proxy_collapse` (Boundary cases)

Paper statement: when `Y = S`, perfect invariance (`I(R;S) = 0`) forces `I(R;Y) = 0`.

`Y = S` is formalized as: the joint law is supported on the diagonal `y = s`, which is
exactly the statement that the random variables `Y` and `S` are almost surely equal. -/

/-- If the joint law is supported on `y = s`, then `H(Y|S) = 0`. -/
theorem H_Y_given_S_eq_zero_of_diagonal {ρ η : Type*} [Fintype ρ] [Fintype η]
    (J : JointLaw ρ η η) (hdiag : ∀ r y s, y ≠ s → J.p r y s = 0) :
    J.H_Y_given_S = 0 := by
  have hoff : ∀ y s : η, y ≠ s → J.pYS (y, s) = 0 := by
    intro y s hys
    simp only [JointLaw.pYS]
    exact Finset.sum_eq_zero fun r _ => hdiag r y s hys
  have hdiagS : ∀ s : η, J.pYS (s, s) = J.pS s := by
    intro s
    rw [← J.sum_y_pYS s]
    refine (Finset.sum_eq_single s (fun y _ hy => hoff y s hy) (by simp)).symm
  rw [J.H_Y_given_S_eq, JointLaw.H_YS_eq_sum, JointLaw.H_S_eq_sum]
  have hrow : ∀ y : η, ∑ s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s))
      = J.pS y * Real.logb 2 (J.pS y) := by
    intro y
    rw [Finset.sum_eq_single y (fun s _ hs => by rw [hoff y s (Ne.symm hs)]; ring) (by simp)]
    rw [hdiagS y]
  rw [Finset.sum_congr rfl fun y _ => hrow y]
  ring

/-- **C4 (Boundary cases).** If the task target equals the forbidden proxy (`Y = S`, i.e. the
law is supported on the diagonal) and the representation is perfectly invariant
(`I(R;S) = 0`), then the representation carries no task information: `I(R;Y) = 0`. -/
theorem perfect_invariance_target_proxy_collapse {ρ η : Type*} [Fintype ρ] [Fintype η]
    (J : JointLaw ρ η η) (hdiag : ∀ r y s, y ≠ s → J.p r y s = 0) (hinv : J.I_RS = 0) :
    J.I_RY = 0 := by
  have hceil := forbidden_proxy_capacity_ceiling J 0 (le_of_eq hinv)
  rw [H_Y_given_S_eq_zero_of_diagonal J hdiag] at hceil
  have := J.I_RY_nonneg
  linarith

/-! ## Non-vacuity witnesses

Three explicit finite joint laws on `Bool × Bool × Bool`, with all information quantities
of the claims computed exactly. -/

section Witnesses

/-- Witness law 1: `R`, `Y`, `S` are all equal to one fair bit. -/
noncomputable def diagLaw : JointLaw Bool Bool Bool where
  p r y s := if r = y ∧ y = s then 1 / 2 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp; norm_num

/-- Witness law 2: `Y = S` is a fair bit and `R` is an independent fair bit. -/
noncomputable def indepRLaw : JointLaw Bool Bool Bool where
  p _ y s := if y = s then 1 / 4 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp; norm_num

/-- Witness law 3: `R`, `Y`, `S` are three independent fair bits. -/
noncomputable def uniformLaw : JointLaw Bool Bool Bool where
  p _ _ _ := 1 / 8
  nonneg := by intro r y s; norm_num
  total := by norm_num [Fintype.sum_bool]

/-- Every information quantity of the diagonal witness law. -/
theorem diagLaw_values :
    diagLaw.I_RY = 1 ∧ diagLaw.I_RS = 1 ∧ diagLaw.I_RY_given_S = 0 ∧
      diagLaw.I_RS_given_Y = 0 ∧ diagLaw.H_Y_given_S = 0 ∧ diagLaw.H_Y_given_RS = 0 := by
  have hR : diagLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : diagLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : diagLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : diagLaw.H_RY = 1 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRS : diagLaw.H_RS = 1 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hYS : diagLaw.H_YS = 1 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRYS : diagLaw.H_RYS = 1 := by
    simp only [JointLaw.H_RYS_eq_sum, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num
  · rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num
  · rw [JointLaw.I_RY_given_S_eq, hRS, hYS, hRYS, hS]; norm_num
  · rw [JointLaw.I_RS_given_Y_eq, hRY, hYS, hRYS, hY]; norm_num
  · rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num
  · rw [JointLaw.H_Y_given_RS_eq, hRYS, hRS]; norm_num

/-- Every information quantity of the independent-`R`, `Y = S` witness law. -/
theorem indepRLaw_values :
    indepRLaw.H_R = 1 ∧ indepRLaw.I_RY = 0 ∧ indepRLaw.I_RS = 0 ∧
      indepRLaw.H_Y_given_S = 0 := by
  have hR : indepRLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : indepRLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : indepRLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : indepRLaw.H_RY = 2 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRS : indepRLaw.H_RS = 2 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hYS : indepRLaw.H_YS = 1 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  exact ⟨hR, by rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num,
    by rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num,
    by rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num⟩

/-- Every information quantity of the three-independent-bits witness law. -/
theorem uniformLaw_values :
    uniformLaw.I_RY = 0 ∧ uniformLaw.I_RS = 0 ∧ uniformLaw.H_Y_given_S = 1 ∧
      uniformLaw.H_Y_given_RS = 1 ∧ uniformLaw.I_RS_given_Y = 0 := by
  have hR : uniformLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : uniformLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : uniformLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : uniformLaw.H_RY = 2 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRS : uniformLaw.H_RS = 2 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hYS : uniformLaw.H_YS = 2 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRYS : uniformLaw.H_RYS = 3 := by
    simp only [JointLaw.H_RYS_eq_sum, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_eighth]
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num
  · rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num
  · rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num
  · rw [JointLaw.H_Y_given_RS_eq, hRYS, hRS]; norm_num
  · rw [JointLaw.I_RS_given_Y_eq, hRY, hYS, hRYS, hY]; norm_num

/-- **Non-vacuity for C1.** The chain balance has non-trivial content: for `diagLaw` it reads
`1 = 0 + 1 - 0`, with both sides equal to `1 ≠ 0`. -/
theorem mutual_information_chain_balance_nonvacuity :
    diagLaw.I_RY = 1 ∧ diagLaw.I_RY_given_S + diagLaw.I_RS - diagLaw.I_RS_given_Y = 1 := by
  obtain ⟨h1, h2, h3, h4, -, -⟩ := diagLaw_values
  exact ⟨h1, by rw [h2, h3, h4]; norm_num⟩

/-- **Non-vacuity for C2.** The hypothesis `I(R;S) ≤ δ` is satisfiable with a nonzero
conclusion: for `uniformLaw` and `δ = 0` the ceiling reads `0 = I(R;Y) ≤ H(Y|S) + 0 = 1`. -/
theorem forbidden_proxy_capacity_ceiling_nonvacuity :
    uniformLaw.I_RS ≤ 0 ∧ uniformLaw.I_RY = 0 ∧ uniformLaw.H_Y_given_S = 1 := by
  obtain ⟨h1, h2, h3, -, -⟩ := uniformLaw_values
  exact ⟨le_of_eq h2, h1, h3⟩

/-- **Non-vacuity for C3.** The slack is strictly positive for `uniformLaw`
(`H(Y|S) + I(R;S) - I(R;Y) = 1 > 0`, decomposing as `H(Y|R,S) = 1` plus `I(R;S|Y) = 0`),
and it vanishes for `diagLaw`; so the decomposition is neither always trivial nor
always strict. -/
theorem capacity_ceiling_slack_decomposition_nonvacuity :
    uniformLaw.H_Y_given_S + uniformLaw.I_RS - uniformLaw.I_RY = 1 ∧
      uniformLaw.H_Y_given_RS + uniformLaw.I_RS_given_Y = 1 ∧
      diagLaw.H_Y_given_S + diagLaw.I_RS - diagLaw.I_RY = 0 := by
  obtain ⟨h1, h2, h3, h4, h5⟩ := uniformLaw_values
  obtain ⟨d1, d2, -, -, d5, -⟩ := diagLaw_values
  exact ⟨by rw [h1, h2, h3]; norm_num, by rw [h4, h5]; norm_num,
    by rw [d1, d2, d5]; norm_num⟩

/-- **Non-vacuity for C4.** The hypotheses of C4 are satisfiable by a law whose
representation is *not* degenerate: `indepRLaw` is supported on `Y = S`, has
`I(R;S) = 0`, and its representation carries a full bit of entropy `H(R) = 1`,
yet `I(R;Y) = 0`. -/
theorem perfect_invariance_target_proxy_collapse_nonvacuity :
    (∀ r y s, y ≠ s → indepRLaw.p r y s = 0) ∧ indepRLaw.I_RS = 0 ∧
      indepRLaw.H_R = 1 ∧ indepRLaw.I_RY = 0 := by
  obtain ⟨hR, hRY, hRS, -⟩ := indepRLaw_values
  refine ⟨?_, hRS, hR, hRY⟩
  intro r y s hys
  simp [indepRLaw, hys]

end Witnesses

end Viridis.Run126.PaperFormalization

/- Engine-3 immutable source unit: ErasureFamily.lean -/

/-!
# C5 — the tight erasure family (Proposition 1)

Paper statement (Proposition 1, Eq. 5): let `S` and `U` be independent fair bits, let
`Y = (S, U)`, and let `L` reveal `S` with probability `q` and otherwise output an erasure
symbol.  For `R = (U, L)`,
`I(R;S) = q`, `H(Y|S) = 1`, `I(R;Y) = 1 + q`,
so the ceiling `I(R;Y) ≤ H(Y|S) + δ` of Corollary 1 is tight for every `q ∈ [0,1]` bit.

Formalization: the alphabets are `ρ = Bool × Option Bool` (the pair `(U, L)`, with `none`
the erasure symbol), `η = Bool × Bool` (the pair `(S, U)`) and `σ = Bool` (the proxy `S`),
and the joint mass function is
`p (u,l) (y₁,y₂) s = ¼ · leak q l s` when `y₁ = s` and `y₂ = u`, and `0` otherwise.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-- The binary erasure channel used by Proposition 1: on input `s` it outputs `some s`
with probability `q` and the erasure symbol `none` with probability `1 - q`. -/
noncomputable def leak (q : ℝ) : Option Bool → Bool → ℝ :=
  fun l s => if l = some s then q else if l = none then 1 - q else 0

lemma leak_nonneg {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (l : Option Bool) (s : Bool) :
    0 ≤ leak q l s := by
  unfold leak
  split
  · exact hq0
  · split
    · linarith
    · exact le_refl 0

lemma leak_none (q : ℝ) (s : Bool) : leak q none s = 1 - q := by simp [leak]

lemma leak_some_self (q : ℝ) (b : Bool) : leak q (some b) b = q := by simp [leak]

lemma leak_some_tf (q : ℝ) : leak q (some true) false = 0 := by simp [leak]

lemma leak_some_ft (q : ℝ) : leak q (some false) true = 0 := by simp [leak]

/-- The independent-bit plus erasure-leakage family of Proposition 1:
`S, U` independent fair bits, `Y = (S, U)`, `L` the erasure-channel output on `S`,
and `R = (U, L)`. -/
noncomputable def erasureLaw (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    JointLaw (Bool × Option Bool) (Bool × Bool) Bool where
  p r y s := if y.1 = s ∧ y.2 = r.1 then (1 / 4) * leak q r.2 s else 0
  nonneg := by
    intro r y s
    split
    · have h := leak_nonneg hq0 hq1 r.2 s
      positivity
    · exact le_refl 0
  total := by
    simp [Fintype.sum_prod_type, Fintype.sum_option, leak]
    ring

section
variable {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1)

/-! ### Marginals of the erasure family -/

lemma erasure_pS (s : Bool) : (erasureLaw q hq0 hq1).pS s = 1 / 2 := by
  cases s <;> simp [JointLaw.pS, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pY (y : Bool × Bool) : (erasureLaw q hq0 hq1).pY y = 1 / 4 := by
  obtain ⟨y1, y2⟩ := y
  cases y1 <;> cases y2 <;>
    simp [JointLaw.pY, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pYS (y1 y2 s : Bool) :
    (erasureLaw q hq0 hq1).pYS ((y1, y2), s) = if y1 = s then 1 / 4 else 0 := by
  cases y1 <;> cases y2 <;> cases s <;>
    simp [JointLaw.pYS, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pR_none (u : Bool) : (erasureLaw q hq0 hq1).pR (u, none) = (1 - q) / 2 := by
  cases u <;> simp [JointLaw.pR, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pR_some (u b : Bool) : (erasureLaw q hq0 hq1).pR (u, some b) = q / 4 := by
  cases u <;> cases b <;> simp [JointLaw.pR, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pRY_diag (u : Bool) (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((u, l), (y1, u)) = leak q l y1 / 4 := by
  cases u <;> cases y1 <;> simp [JointLaw.pRY, erasureLaw] <;> ring

lemma erasure_pRY_tf (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((true, l), (y1, false)) = 0 := by
  cases y1 <;> simp [JointLaw.pRY, erasureLaw]

lemma erasure_pRY_ft (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((false, l), (y1, true)) = 0 := by
  cases y1 <;> simp [JointLaw.pRY, erasureLaw]

lemma erasure_pRS (u : Bool) (l : Option Bool) (s : Bool) :
    (erasureLaw q hq0 hq1).pRS ((u, l), s) = leak q l s / 4 := by
  cases u <;> cases s <;> simp [JointLaw.pRS, erasureLaw, Fintype.sum_prod_type] <;> ring

/-! ### Entropies of the erasure family -/

/-- The binary-entropy shorthand `A q = -q log₂ q - (1-q) log₂ (1-q)`. -/
noncomputable def binEnt (q : ℝ) : ℝ :=
  -(q * Real.logb 2 q) - (1 - q) * Real.logb 2 (1 - q)

private lemma div_mul_logb_div {x c : ℝ} (hx : 0 ≤ x) (hc : 0 < c) :
    x / c * Real.logb 2 (x / c) = (x * Real.logb 2 x - x * Real.logb 2 c) / c := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · rw [Real.logb_div (ne_of_gt hpos) (ne_of_gt hc)]
    ring

private lemma logb2_four : Real.logb 2 (4 : ℝ) = 2 := by
  have h : (4 : ℝ) = 2 * 2 := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_two]
  norm_num

private lemma logb_q_div_four (hq0 : 0 ≤ q) :
    q / 4 * Real.logb 2 (q / 4) = (q * Real.logb 2 q - 2 * q) / 4 := by
  rw [div_mul_logb_div hq0 (by norm_num : (0:ℝ) < 4), logb2_four]
  ring

private lemma logb_one_sub_q_div_four (hq1 : q ≤ 1) :
    (1 - q) / 4 * Real.logb 2 ((1 - q) / 4) = ((1 - q) * Real.logb 2 (1 - q) - 2 * (1 - q)) / 4 := by
  rw [div_mul_logb_div (by linarith) (by norm_num : (0:ℝ) < 4), logb2_four]
  ring

private lemma logb_one_sub_q_div_two (hq1 : q ≤ 1) :
    (1 - q) / 2 * Real.logb 2 ((1 - q) / 2) = ((1 - q) * Real.logb 2 (1 - q) - (1 - q)) / 2 := by
  rw [div_mul_logb_div (by linarith) (by norm_num : (0:ℝ) < 2), logb2_two]
  ring

lemma erasure_H_S : (erasureLaw q hq0 hq1).H_S = 1 := by
  rw [JointLaw.H_S_eq_sum]
  simp only [Fintype.sum_bool, erasure_pS]
  norm_num [logb2_half]

lemma erasure_H_Y : (erasureLaw q hq0 hq1).H_Y = 2 := by
  rw [JointLaw.H_Y_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, erasure_pY]
  norm_num [logb2_quarter]

lemma erasure_H_YS : (erasureLaw q hq0 hq1).H_YS = 2 := by
  rw [JointLaw.H_YS_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, erasure_pYS]
  norm_num [logb2_quarter]

lemma erasure_H_R : (erasureLaw q hq0 hq1).H_R = binEnt q + 1 + q := by
  rw [JointLaw.H_R_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pR_none, erasure_pR_some]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_two hq1]
  unfold binEnt
  ring

lemma erasure_H_RY : (erasureLaw q hq0 hq1).H_RY = binEnt q + 2 := by
  rw [JointLaw.H_RY_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pRY_diag, erasure_pRY_tf, erasure_pRY_ft, leak_none, leak_some_self, leak_some_tf,
    leak_some_ft, zero_div, zero_mul, add_zero, zero_add]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_four hq1]
  unfold binEnt
  ring

lemma erasure_H_RS : (erasureLaw q hq0 hq1).H_RS = binEnt q + 2 := by
  rw [JointLaw.H_RS_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pRS, leak_none, leak_some_self, leak_some_tf, leak_some_ft, zero_div, zero_mul,
    add_zero, zero_add]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_four hq1]
  unfold binEnt
  ring

/-! ### C5 -/

/-- **C5 (Proposition 1).** For the independent-bit plus erasure-leakage family with
erasure-channel reliability `q ∈ [0,1]`:
`I(R;S) = q`, `H(Y|S) = 1` and `I(R;Y) = 1 + q`; consequently the forbidden-proxy
capacity ceiling `I(R;Y) ≤ H(Y|S) + δ` of Corollary 1 is attained with equality at the
leakage budget `δ = q`, for every `q ∈ [0,1]`. -/
theorem erasure_family_tightness (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    (erasureLaw q hq0 hq1).I_RS = q ∧
      (erasureLaw q hq0 hq1).H_Y_given_S = 1 ∧
      (erasureLaw q hq0 hq1).I_RY = 1 + q ∧
      (erasureLaw q hq0 hq1).I_RY = (erasureLaw q hq0 hq1).H_Y_given_S + q := by
  have hR := erasure_H_R hq0 hq1
  have hY := erasure_H_Y hq0 hq1
  have hS := erasure_H_S hq0 hq1
  have hRY := erasure_H_RY hq0 hq1
  have hRS := erasure_H_RS hq0 hq1
  have hYS := erasure_H_YS hq0 hq1
  have hIRS : (erasureLaw q hq0 hq1).I_RS = q := by
    rw [JointLaw.I_RS_eq, hR, hS, hRS]; ring
  have hHYS : (erasureLaw q hq0 hq1).H_Y_given_S = 1 := by
    rw [JointLaw.H_Y_given_S_eq, hYS, hS]; ring
  have hIRY : (erasureLaw q hq0 hq1).I_RY = 1 + q := by
    rw [JointLaw.I_RY_eq, hR, hY, hRY]; ring
  exact ⟨hIRS, hHYS, hIRY, by rw [hIRY, hHYS]⟩

end

/-! ### Non-vacuity witness for C5 -/

/-- **Non-vacuity for C5.** At `q = 1/2` the family is a concrete finite law with
`I(R;S) = 1/2`, `H(Y|S) = 1` and `I(R;Y) = 3/2`: the leakage budget is nonzero, the task
information is nonzero, and the ceiling of C2 is attained. -/
theorem erasure_family_tightness_nonvacuity :
    (erasureLaw (1/2) (by norm_num) (by norm_num)).I_RS = 1/2 ∧
      (erasureLaw (1/2) (by norm_num) (by norm_num)).H_Y_given_S = 1 ∧
      (erasureLaw (1/2) (by norm_num) (by norm_num)).I_RY = 3/2 := by
  obtain ⟨h1, h2, h3, -⟩ := erasure_family_tightness (1/2) (by norm_num) (by norm_num)
  exact ⟨h1, h2, by rw [h3]; norm_num⟩

end Viridis.Run126.PaperFormalization

/- Engine-3 immutable source unit: ZeroCovariance.lean -/

/-!
# The nonlinear negative control (paper claim C7)

The paper's negative control (Section "Boundary cases and controls", inventory claim C7,
evidence class NUMERIC) states: let `S` be uniform on `{-1, 0, 1}` and `R = S²`.  Then
`Cov(R, S) = 0` by symmetry, but `R` reveals whether `S = 0`, giving
`I(R;S) = H(R) = 0.918296…` bit.

This claim is *not* one of the five frozen formal targets, but it is formalized here as an
exact statement: the covariance vanishes while the mutual information equals
`log₂ 3 - 2/3 = 0.9182958…` bit, which is strictly positive.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-- Covariance of real-valued codings `f ∘ R` and `g ∘ S` under a joint law. -/
noncomputable def JointLaw.cov {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) (f : ρ → ℝ) (g : σ → ℝ) : ℝ :=
  (∑ r, ∑ s, J.pRS (r, s) * (f r * g s)) - (∑ r, J.pR r * f r) * (∑ s, J.pS s * g s)

/-- The real value coded by the proxy alphabet `Fin 3`: `-1, 0, 1`. -/
noncomputable def sval : Fin 3 → ℝ := fun s => (s : ℝ) - 1

/-- The real value coded by the representation alphabet `Bool`: `1` and `0`. -/
noncomputable def rval : Bool → ℝ := fun b => if b then 1 else 0

/-- The representation `R = S²`, as a map of alphabets. -/
def rmap : Fin 3 → Bool := fun s => if s = 1 then false else true

/-- `rmap` really codes `R = S²`. -/
lemma rval_rmap (s : Fin 3) : rval (rmap s) = (sval s) ^ 2 := by
  fin_cases s <;> norm_num [rval, rmap, sval]

/-- The negative-control law: `S` uniform on `{-1, 0, 1}`, `R = S²`, `Y` trivial. -/
noncomputable def squareLaw : JointLaw Bool Unit (Fin 3) where
  p r _ s := if r = rmap s then 1 / 3 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp [Fin.sum_univ_three, rmap]; norm_num

private lemma logb2_three_pos : 0 < Real.logb 2 (3 : ℝ) :=
  Real.logb_pos (by norm_num) (by norm_num)

private lemma logb2_third : Real.logb 2 (1 / 3 : ℝ) = -Real.logb 2 3 := by
  rw [one_div, Real.logb_inv]

private lemma logb2_two_thirds : Real.logb 2 (2 / 3 : ℝ) = 1 - Real.logb 2 3 := by
  rw [Real.logb_div (by norm_num) (by norm_num), logb2_two]

lemma squareLaw_pS (s : Fin 3) : squareLaw.pS s = 1 / 3 := by
  fin_cases s <;> simp [JointLaw.pS, squareLaw, rmap]

lemma squareLaw_pR_true : squareLaw.pR true = 2 / 3 := by
  simp [JointLaw.pR, squareLaw, rmap]
  rw [Fin.sum_univ_three]
  norm_num [Fin.ext_iff]

lemma squareLaw_pR_false : squareLaw.pR false = 1 / 3 := by
  simp [JointLaw.pR, squareLaw, rmap]

lemma squareLaw_pRS (r : Bool) (s : Fin 3) :
    squareLaw.pRS (r, s) = if r = rmap s then 1 / 3 else 0 := by
  simp [JointLaw.pRS, squareLaw]

lemma squareLaw_H_S : squareLaw.H_S = Real.logb 2 3 := by
  rw [JointLaw.H_S_eq_sum]
  simp only [Fin.sum_univ_three, squareLaw_pS]
  rw [logb2_third]
  ring

lemma squareLaw_H_RS : squareLaw.H_RS = Real.logb 2 3 := by
  rw [JointLaw.H_RS_eq_sum]
  simp only [Fintype.sum_bool, Fin.sum_univ_three, squareLaw_pRS, rmap, Fin.reduceEq, reduceIte,
    Bool.false_eq_true, Bool.true_eq_false, zero_mul, add_zero, zero_add]
  rw [logb2_third]
  ring

lemma squareLaw_H_R : squareLaw.H_R = Real.logb 2 3 - 2 / 3 := by
  rw [JointLaw.H_R_eq_sum]
  simp only [Fintype.sum_bool, squareLaw_pR_true, squareLaw_pR_false]
  rw [logb2_third, logb2_two_thirds]
  ring

/-- **Paper claim C7 (negative control).** For `S` uniform on `{-1,0,1}` and `R = S²`,
the covariance of `R` and `S` vanishes, yet the mutual information is
`I(R;S) = log₂ 3 - 2/3 = 0.9182958…` bit, which is strictly positive.
Hence zero covariance does not certify representation–proxy independence. -/
theorem zero_covariance_does_not_certify_invariance :
    squareLaw.cov rval sval = 0 ∧
      squareLaw.I_RS = Real.logb 2 3 - 2 / 3 ∧ 0 < squareLaw.I_RS := by
  have hI : squareLaw.I_RS = Real.logb 2 3 - 2 / 3 := by
    rw [JointLaw.I_RS_eq, squareLaw_H_R, squareLaw_H_S, squareLaw_H_RS]
    ring
  refine ⟨?_, hI, ?_⟩
  · simp only [JointLaw.cov, Fintype.sum_bool, Fin.sum_univ_three, squareLaw_pRS,
      squareLaw_pR_true, squareLaw_pR_false, squareLaw_pS, rmap, rval, sval]
    norm_num [Fin.ext_iff]
  · rw [hI]
    have h : (2 : ℝ) / 3 < Real.logb 2 3 := by
      have h2 : Real.logb 2 (2 : ℝ) < Real.logb 2 3 :=
        Real.logb_lt_logb (by norm_num) (by norm_num) (by norm_num)
      rw [logb2_two] at h2
      linarith
    linarith

end Viridis.Run126.PaperFormalization
