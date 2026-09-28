import Mathlib

namespace Viridis.IntelligenceBound.SymbioticAccounting

/-!
Codex-authored linked correction r1 for the frozen algebraic targets of Run 137.
These statements assume componentwise
linear rate ceilings and a fixed shared power budget. They do not formalize
Landauer's principle, network coding, empirical collective intelligence,
ecological mutualism, or novelty.

The original source and failed provider attempt remain preserved separately.
This candidate keeps their counterexamples as named targets, repairs only the
omitted domain hypotheses, and is not verified until the private Comparator
accepts the aligned exact bytes with both kernels.
-/

/-- The finite sum of a real-valued family indexed by `Fin n`.

The frozen source used the identifier `sum` for this operation without
providing it; `sum f` is the total `∑ i, f i` over all indices, which is the
only reading under which the frozen statements typecheck. -/
noncomputable def sum {n : Nat} (f : Fin n -> Real) : Real := ∑ i, f i

theorem sum_eq_finsetSum {n : Nat} (f : Fin n -> Real) :
    sum f = ∑ i, f i := rfl

noncomputable def harmonicCoeff {n : Nat} (w d : Fin n -> Real) : Real :=
  1 / (sum fun i => w i / d i)

noncomputable def rateStar {n : Nat} (w d : Fin n -> Real) (P eps : Real) : Real :=
  P / (eps * (sum fun i => w i / d i))

noncomputable def powerStar {n : Nat} (w d : Fin n -> Real) (P : Real) (i : Fin n) : Real :=
  P * (w i / d i) / (sum fun j => w j / d j)

/-!
### Two frozen statements are false as written

`conjunctive_rate_upper_bound` and `additive_rate_upper_bound` as frozen in the
contract are refutable: neither excludes the empty index set `n = 0`, where all
componentwise hypotheses hold vacuously while the conclusions constrain
`R` resp. `dmax`, which are then completely unconstrained.  The original texts
are preserved below in comments, the refutations are recorded as
`*_as_frozen_is_false`, and the repaired statements — carrying one extra
hypothesis each, in the same style as the other frozen targets — keep the
frozen names, binders and conclusions.
-/

/-- Refutation of the frozen form of `conjunctive_rate_upper_bound`: with
`n = 0` every hypothesis is vacuous or trivial, `rateStar = 0`, yet `R` is
arbitrary. -/
theorem conjunctive_rate_upper_bound_as_frozen_is_false :
    ¬ (forall (n : Nat) (w d p r : Fin n -> Real) (P eps R : Real),
        (forall i, 0 < w i) -> (forall i, 0 < d i) ->
        (forall i, 0 <= p i) -> (0 < eps) ->
        (sum p <= P) ->
        (forall i, r i <= p i * d i / eps) ->
        (forall i, w i * R <= r i) ->
        R <= rateStar w d P eps) := by
  intro h
  have := h 0 (fun i => i.elim0) (fun i => i.elim0) (fun i => i.elim0)
      (fun i => i.elim0) 0 1 1
      (fun i => i.elim0) (fun i => i.elim0) (fun i => i.elim0) one_pos
      (by simp [sum]) (fun i => i.elim0) (fun i => i.elim0)
  simp [rateStar, sum] at this
  linarith

/-- Repaired `conjunctive_rate_upper_bound`: identical to the frozen statement
except for the extra hypothesis `hden : 0 < sum fun i => w i / d i` (the same
nondegeneracy hypothesis already carried by `symbiotic_allocation_attains` and
`normalized_rates_equal`), which rules out the empty index set. -/
theorem conjunctive_rate_upper_bound
    {n : Nat} (w d p r : Fin n -> Real) (P eps R : Real)
    (hw : forall i, 0 < w i) (hd : forall i, 0 < d i)
    (hp : forall i, 0 <= p i) (heps : 0 < eps)
    (hden : 0 < sum fun i => w i / d i)
    (hpower : sum p <= P)
    (hcomponent : forall i, r i <= p i * d i / eps)
    (hrequired : forall i, w i * R <= r i) :
    R <= rateStar w d P eps := by
  have key : forall i, eps * R * (w i / d i) <= p i := by
    intro i
    have h1 : w i * R <= p i * d i / eps := le_trans (hrequired i) (hcomponent i)
    rw [le_div_iff₀ heps] at h1
    have hdi := hd i
    rw [show eps * R * (w i / d i) = (eps * R * w i) / d i by ring, div_le_iff₀ hdi]
    nlinarith [h1]
  have hsum : eps * R * (sum fun i => w i / d i) <= sum p := by
    rw [sum_eq_finsetSum, sum_eq_finsetSum, Finset.mul_sum]
    exact Finset.sum_le_sum fun i _ => key i
  have hepsden : 0 < eps * (sum fun i => w i / d i) := mul_pos heps hden
  rw [rateStar, le_div_iff₀ hepsden]
  nlinarith [hsum, hpower]

theorem symbiotic_allocation_attains
    {n : Nat} (w d : Fin n -> Real) (P eps : Real)
    (hw : forall i, 0 < w i) (hd : forall i, 0 < d i)
    (hden : 0 < sum fun i => w i / d i) :
    sum (powerStar w d P) = P := by
  have hne : (sum fun j => w j / d j) ≠ 0 := ne_of_gt hden
  rw [sum_eq_finsetSum]
  simp only [powerStar]
  rw [← Finset.sum_div, ← Finset.mul_sum, ← sum_eq_finsetSum]
  field_simp

theorem normalized_rates_equal
    {n : Nat} (w d : Fin n -> Real) (P eps : Real)
    (hw : forall i, 0 < w i) (hd : forall i, 0 < d i)
    (heps : 0 < eps) (hden : 0 < sum fun i => w i / d i) :
    forall i, (powerStar w d P i * d i / eps) / w i = rateStar w d P eps := by
  intro i
  have hwi := (hw i).ne'
  have hdi := (hd i).ne'
  have hne : (sum fun j => w j / d j) ≠ 0 := ne_of_gt hden
  simp only [powerStar, rateStar]
  field_simp

theorem weighted_harmonic_le_max
    {n : Nat} [Nonempty (Fin n)] (w d : Fin n -> Real) (dmax : Real)
    (hw : forall i, 0 < w i) (hwsum : sum w = 1)
    (hd : forall i, 0 < d i) (hmax : forall i, d i <= dmax) :
    harmonicCoeff w d <= dmax := by
  obtain ⟨i0⟩ := ‹Nonempty (Fin n)›
  have hdmax : 0 < dmax := lt_of_lt_of_le (hd i0) (hmax i0)
  have hlb : 1 / dmax <= sum fun i => w i / d i := by
    have hstep : ∀ i ∈ Finset.univ, w i / dmax ≤ w i / d i := fun i _ =>
      div_le_div_of_nonneg_left (hw i).le (hd i) (hmax i)
    have := Finset.sum_le_sum hstep
    rwa [← Finset.sum_div, ← sum_eq_finsetSum, hwsum, ← sum_eq_finsetSum] at this
  have hden : 0 < sum fun i => w i / d i :=
    lt_of_lt_of_le (by positivity) hlb
  rw [harmonicCoeff, div_le_iff₀ hden]
  rw [div_le_iff₀ hdmax] at hlb
  nlinarith [hlb]

theorem two_partner_closed_form
    (w1 w2 d1 d2 P eps : Real)
    (hw1 : 0 < w1) (hw2 : 0 < w2)
    (hd1 : 0 < d1) (hd2 : 0 < d2) (heps : 0 < eps) :
    P / (eps * (w1 / d1 + w2 / d2)) =
      P * d1 * d2 / (eps * (w1 * d2 + w2 * d1)) := by
  have h1 : d1 ≠ 0 := hd1.ne'
  have h2 : d2 ≠ 0 := hd2.ne'
  have h3 : eps ≠ 0 := heps.ne'
  have h4 : w1 * d2 + w2 * d1 ≠ 0 := by positivity
  field_simp

/-- Refutation of the frozen form of `additive_rate_upper_bound`: with `n = 0`
every hypothesis is vacuous or trivial, the left-hand side is `0`, yet `dmax`
may be negative. -/
theorem additive_rate_upper_bound_as_frozen_is_false :
    ¬ (forall (n : Nat) (d p r : Fin n -> Real) (P eps dmax : Real),
        (forall i, 0 <= p i) -> (0 < eps) ->
        (forall i, d i <= dmax) ->
        (sum p <= P) ->
        (forall i, r i <= p i * d i / eps) ->
        sum r <= P * dmax / eps) := by
  intro h
  have := h 0 (fun i => i.elim0) (fun i => i.elim0) (fun i => i.elim0) 1 1 (-1)
      (fun i => i.elim0) one_pos (fun i => i.elim0) (by simp [sum])
      (fun i => i.elim0)
  simp [sum] at this
  linarith

/-- Repaired `additive_rate_upper_bound`: identical to the frozen statement
except for the extra hypothesis `hdmax0 : 0 <= dmax`, which is automatic as
soon as the index set is nonempty and the efficiencies `d i` are positive, and
which rules out the empty index set with a negative ceiling. -/
theorem additive_rate_upper_bound
    {n : Nat} (d p r : Fin n -> Real) (P eps dmax : Real)
    (hp : forall i, 0 <= p i) (heps : 0 < eps)
    (hdmax : forall i, d i <= dmax) (hdmax0 : 0 <= dmax)
    (hpower : sum p <= P)
    (hcomponent : forall i, r i <= p i * d i / eps) :
    sum r <= P * dmax / eps := by
  have h1 : sum r <= ∑ i, p i * dmax / eps := by
    rw [sum_eq_finsetSum]
    refine Finset.sum_le_sum fun i _ => le_trans (hcomponent i) ?_
    gcongr
    · exact hp i
    · exact hdmax i
  have h2 : (∑ i, p i * dmax / eps) = sum p * dmax / eps := by
    rw [sum_eq_finsetSum, ← Finset.sum_div, ← Finset.sum_mul]
  rw [h2] at h1
  refine le_trans h1 ?_
  gcongr

theorem symbiotic_accounting_nonvacuous :
    let P : Real := 12
    let eps : Real := 2
    let w1 : Real := 1 / 2
    let w2 : Real := 1 / 2
    let d1 : Real := 1 / 2
    let d2 : Real := 1
    P / (eps * (w1 / d1 + w2 / d2)) = 4 /\
    (P * (w1 / d1) / (w1 / d1 + w2 / d2)) = 8 /\
    (P * (w2 / d2) / (w1 / d1 + w2 / d2)) = 4 := by
  norm_num

end Viridis.IntelligenceBound.SymbioticAccounting
