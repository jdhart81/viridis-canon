import Mathlib

namespace Viridis.GaianSystems.AlignmentCone

/-!
Frozen algebraic targets for Run 138. These statements describe weighted sums
of two-coordinate subsystem response vectors under explicit nonnegative weights,
positive target projections, and residual bounds. They do not formalize Earth
system dynamics, ecological safety, agency, governance legitimacy, or novelty.

Codex authored and froze this zero-sorry candidate after reviewing the original
statement contract and preserved historical provider artifact. The historical
artifact is diagnostic input only; verification requires the exact-byte aligned
private Comparator receipt and issued certificate below this source boundary.
-/

/-
Elaboration fixes to the frozen source (no statement was weakened,
renamed, or reinterpreted):

* `alignmentScore` is marked `noncomputable`, since `Real.sqrt` is
  noncomputable.  The definitional body is unchanged.
* The frozen theorem statements use the bare identifier `sum` applied to a
  function `Fin n -> Real`.  No such identifier exists in Mathlib's root
  namespace, so the statements did not elaborate.  It is supplied below with
  its intended meaning, the total sum of the function over `Fin n`.  The
  theorem statements themselves are reproduced verbatim.
-/

/-- Total sum of a real-valued function on `Fin n`. -/
def sum {n : Nat} (f : Fin n -> Real) : Real := Finset.sum Finset.univ f

theorem sum_eq_finsetSum {n : Nat} (f : Fin n -> Real) :
    sum f = ∑ i, f i := rfl

noncomputable def alignmentScore (A B : Real) : Real := A / Real.sqrt (A ^ 2 + B ^ 2)

theorem aggregate_projection_positive
    {n : Nat} [Nonempty (Fin n)] (w a : Fin n -> Real)
    (hw : forall i, 0 < w i) (ha : forall i, 0 < a i) :
    0 < sum fun i => w i * a i := by
  rw [sum_eq_finsetSum]
  refine Finset.sum_pos (fun i _ => mul_pos (hw i) (ha i)) ?_
  exact Finset.univ_nonempty

theorem aggregate_residual_bound
    {n : Nat} (w a b eps : Fin n -> Real)
    (hw : forall i, 0 <= w i) (ha : forall i, 0 <= a i)
    (heps : forall i, 0 <= eps i)
    (hb : forall i, |b i| <= eps i * a i) :
    |sum fun i => w i * b i| <= sum fun i => w i * eps i * a i := by
  rw [sum_eq_finsetSum, sum_eq_finsetSum]
  refine (Finset.abs_sum_le_sum_abs _ _).trans ?_
  refine Finset.sum_le_sum (fun i _ => ?_)
  rw [abs_mul, abs_of_nonneg (hw i), mul_assoc]
  exact mul_le_mul_of_nonneg_left (hb i) (hw i)

theorem common_cone_closed_under_weighted_sum
    {n : Nat} (w a b : Fin n -> Real) (kappa : Real)
    (hw : forall i, 0 <= w i) (ha : forall i, 0 <= a i)
    (hk : 0 <= kappa) (hb : forall i, |b i| <= kappa * a i) :
    |sum fun i => w i * b i| <= kappa * (sum fun i => w i * a i) := by
  rw [sum_eq_finsetSum, sum_eq_finsetSum, Finset.mul_sum]
  refine (Finset.abs_sum_le_sum_abs _ _).trans ?_
  refine Finset.sum_le_sum (fun i _ => ?_)
  rw [abs_mul, abs_of_nonneg (hw i)]
  calc w i * |b i| ≤ w i * (kappa * a i) :=
        mul_le_mul_of_nonneg_left (hb i) (hw i)
    _ = kappa * (w i * a i) := by ring

theorem alignment_floor_of_residual_bound
    (A B E : Real) (hA : 0 < A) (hE : 0 <= E) (hB : |B| <= E) :
    A / Real.sqrt (A ^ 2 + E ^ 2) <= alignmentScore A B := by
  have hBsq : B ^ 2 <= E ^ 2 := by
    have := abs_nonneg B
    nlinarith [sq_abs B]
  have hpos : 0 < Real.sqrt (A ^ 2 + B ^ 2) := by
    refine Real.sqrt_pos.mpr ?_
    nlinarith [sq_nonneg B]
  have hle : Real.sqrt (A ^ 2 + B ^ 2) <= Real.sqrt (A ^ 2 + E ^ 2) :=
    Real.sqrt_le_sqrt (by linarith)
  simpa [alignmentScore] using div_le_div_of_nonneg_left hA.le hpos hle

theorem uniform_cone_alignment_floor
    (A B kappa : Real) (hA : 0 < A) (hk : 0 <= kappa)
    (hB : |B| <= kappa * A) :
    1 / Real.sqrt (1 + kappa ^ 2) <= alignmentScore A B := by
  have key := alignment_floor_of_residual_bound A B (kappa * A) hA
    (mul_nonneg hk hA.le) hB
  have hsq : A ^ 2 + (kappa * A) ^ 2 = (1 + kappa ^ 2) * A ^ 2 := by ring
  have hsqrt : Real.sqrt (A ^ 2 + (kappa * A) ^ 2)
      = Real.sqrt (1 + kappa ^ 2) * A := by
    rw [hsq, Real.sqrt_mul (by positivity), Real.sqrt_sq hA.le]
  have hden : 0 < Real.sqrt (1 + kappa ^ 2) :=
    Real.sqrt_pos.mpr (by positivity)
  rw [hsqrt] at key
  have : A / (Real.sqrt (1 + kappa ^ 2) * A) = 1 / Real.sqrt (1 + kappa ^ 2) := by
    field_simp
  rwa [this] at key

theorem cancellation_gives_perfect_alignment
    (A B : Real) (hA : 0 < A) (hB : B = 0) :
    alignmentScore A B = 1 := by
  subst hB
  have : Real.sqrt (A ^ 2 + (0:Real) ^ 2) = A := by
    rw [show A ^ 2 + (0:Real) ^ 2 = A ^ 2 by ring, Real.sqrt_sq hA.le]
  rw [alignmentScore, this, div_self hA.ne']

theorem magnitude_masking_witness :
    (99 : Real) / 100 > 9 / 10 /\
    (99 : Real) * 1 + (-150) < 0 := by
  constructor <;> norm_num

theorem gaian_alignment_nonvacuous :
    alignmentScore 2 1 > (4 : Real) / 5 /\ alignmentScore 2 1 < 1 := by
  have h5 : ((2:Real) ^ 2 + 1 ^ 2) = 5 := by norm_num
  have hs : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  have hpos : 0 < Real.sqrt 5 := Real.sqrt_pos.mpr (by norm_num)
  have hval : alignmentScore 2 1 = 2 / Real.sqrt 5 := by
    rw [alignmentScore, h5]
  constructor
  · rw [hval, gt_iff_lt, lt_div_iff₀ hpos]
    nlinarith
  · rw [hval, div_lt_one hpos]
    nlinarith

end Viridis.GaianSystems.AlignmentCone
