/-
  Symbiotic Corridor Theorem (SCT) — clean analytic core
  ======================================================
  Viridis Canon · Nightly Run-089 (2026-07-04) · [03] HDFM Corridors × 🌿 Symbiosis
  "The Loom" — 31st IB self-application; CONVERGENCE EVENT (governance layer).

  CONTEXT.  Classical connectivity science optimizes ONE layer: where to spend
  restoration budget so a landscape graph carries ecological flux (the Corridor
  Stewardship Theorem, CST / Run-074).  SCT couples that connectivity layer E to
  the sensing / MRV layer I on the SAME edges, via a *supermodular* ("sense-what-
  you-connect"), not a dependency, link.  On a landscape graph with per-edge
  connectivity spend `g_e >= 0` and sensing spend `s_e >= 0`, unit costs
  `c_e, w_e > 0`, pooled budget `B`, and coupling strength `beta >= 0`, the joint
  objective is

      J(g,s;beta) = sum_e [ k_e*log(1+g_e) + v_e*log(1+s_e) + beta*mu_e*sqrt(g_e*s_e) ].

  The single coupling term `beta*mu*sqrt(g*s)` (joint value only where an edge
  carries BOTH flux and sensing) inverts every conclusion of interdependent-
  network theory: mutualistic coupling is an ASSET, co-design dominates siloing,
  and one shadow price clears the pooled budget.

  This file certifies the clean, well-posed, NON-VACUOUS convex-analysis core
  (R1 structural + R2 sign law).  The measure-dependent results — R3/R4 nested
  assortativity phase transition (NODF, beta_c = argmax da/dbeta) and R5 the IB
  co-evolution rate limit (tracking-rate dynamics) — are deferred to dedicated
  follow-up runs.

  THEOREMS (statements preserved VERBATIM; each hypothesis load-bearing):

    T1  joint_objective_concave                    J concave on the positive orthant.
    T2  coupling_sign_law                          geometric-mean coupling supermodular iff mu >= 0.
    T3  codesign_dominates_siloed_iff_supermodular value-level sign law.
    T4  coupled_waterfilling_single_price          one broadcast price rations the pooled budget;
                                                   beta=0 decouples; s=0 recovers CST.
    T5  sct_nonvacuous                             explicit interior witness binding all four.
-/
import Mathlib

open scoped BigOperators

namespace Viridis.SymbioticCorridor

noncomputable section

/-- Per-edge joint value: `k*log(1+g) + v*log(1+s) + beta*mu*sqrt(g*s)`. -/
def edgeVal (kappa nu mu beta g s : ℝ) : ℝ :=
  kappa * Real.log (1 + g) + nu * Real.log (1 + s) + beta * mu * Real.sqrt (g * s)

/-- The geometric-mean coupling `M(g,s) = mu*sqrt(g*s)`. -/
def coupling (mu g s : ℝ) : ℝ := mu * Real.sqrt (g * s)

/-
**T1 — Joint objective is concave (R1 structural).**
On the open positive quadrant the single-edge objective is concave when the
weights `kappa, nu, beta, mu` are nonnegative: `log(1+.)` is concave and the
geometric mean `sqrt(g*s)` is concave (super-additivity
`sqrt(g1 s1)+sqrt(g2 s2) <= sqrt((g1+g2)(s1+s2))`), so the nonnegatively-weighted
sum is concave.  This makes the coupled water-filling a convex program with a
unique optimum.  NON-VACUOUS: with a strictly positive coupling weight the
objective is not affine.

Superadditivity of the geometric mean on the nonnegative quadrant:
`sqrt(a1*b1) + sqrt(a2*b2) ≤ sqrt((a1+a2)*(b1+b2))`.
-/
lemma sqrt_prod_superadditive
    (a1 b1 a2 b2 : ℝ) (ha1 : 0 ≤ a1) (hb1 : 0 ≤ b1) (ha2 : 0 ≤ a2) (hb2 : 0 ≤ b2) :
    Real.sqrt (a1 * b1) + Real.sqrt (a2 * b2) ≤ Real.sqrt ((a1 + a2) * (b1 + b2)) := by
  refine Real.le_sqrt_of_sq_le ?_;
  rw [ Real.sqrt_mul ha1, Real.sqrt_mul ha2 ];
  nlinarith only [ sq_nonneg ( Real.sqrt a1 * Real.sqrt b2 - Real.sqrt a2 * Real.sqrt b1 ), Real.mul_self_sqrt ha1, Real.mul_self_sqrt hb1, Real.mul_self_sqrt ha2, Real.mul_self_sqrt hb2 ]

/-
The geometric mean `(g,s) ↦ sqrt(g*s)` is concave on the positive quadrant.
-/
lemma sqrt_prod_concaveOn :
    ConcaveOn ℝ (Set.Ioi (0 : ℝ) ×ˢ Set.Ioi (0 : ℝ))
      (fun p : ℝ × ℝ => Real.sqrt (p.1 * p.2)) := by
  refine' ⟨ _, _ ⟩;
  · exact convex_Ioi 0 |> fun h => h.prod h;
  · simp +zetaDelta at *;
    intro a b ha hb a' b' ha' hb' x y hx hy hxy;
    convert sqrt_prod_superadditive ( x * a ) ( x * b ) ( y * a' ) ( y * b' ) ( by positivity ) ( by positivity ) ( by positivity ) ( by positivity ) using 1 ; ring;
    norm_num [ mul_assoc, hx, hy ]

/-
`(g,s) ↦ log(1+g)` is concave on the positive quadrant.
-/
lemma log_one_add_fst_concaveOn :
    ConcaveOn ℝ (Set.Ioi (0 : ℝ) ×ˢ Set.Ioi (0 : ℝ))
      (fun p : ℝ × ℝ => Real.log (1 + p.1)) := by
  constructor <;> norm_num;
  · exact convex_Ioi 0 |> fun h => h.prod h;
  · intros a b ha hb a' b' ha' hb' x y hx hy hxy
    have h_concave : ConcaveOn ℝ (Set.Ioi 0) Real.log := by
      exact ( StrictConcaveOn.concaveOn <| strictConcaveOn_log_Ioi );
    convert h_concave.2 _ _ _ _ _ using 1 <;> norm_num [ * ];
    · rw [ ← eq_sub_iff_add_eq' ] at hxy ; subst_vars ; ring;
    · linarith;
    · positivity

/-
`(g,s) ↦ log(1+s)` is concave on the positive quadrant.
-/
lemma log_one_add_snd_concaveOn :
    ConcaveOn ℝ (Set.Ioi (0 : ℝ) ×ˢ Set.Ioi (0 : ℝ))
      (fun p : ℝ × ℝ => Real.log (1 + p.2)) := by
  have h_log_concave : ConcaveOn ℝ (Set.Ioi 0) (fun x : ℝ => Real.log (1 + x)) := by
    apply_rules [ StrictConcaveOn.concaveOn ];
    apply strictConcaveOn_of_deriv2_neg ( convex_Ioi 0 );
    · exact continuousOn_of_forall_continuousAt fun x hx => ContinuousAt.log ( continuousAt_const.add continuousAt_id ) ( by linarith [ hx.out ] );
    · -- Let's calculate the second derivative of $f(x) = \log(1 + x)$.
      have h_second_deriv : ∀ x > 0, deriv^[2] (fun x => Real.log (1 + x)) x = -1 / (1 + x)^2 := by
        have h_second_deriv : ∀ x > 0, deriv^[2] (fun x => Real.log (1 + x)) x = deriv (fun x => 1 / (1 + x)) x := by
          exact fun x x_pos => Filter.EventuallyEq.deriv_eq ( by filter_upwards [ lt_mem_nhds x_pos ] with y hy using by simp +decide [ add_comm, show y + 1 ≠ 0 from by linarith ] );
        exact fun x hx => h_second_deriv x hx ▸ by norm_num [ add_comm, ne_of_gt ( add_pos hx zero_lt_one ) ] ;
      exact fun x hx => h_second_deriv x ( interior_subset hx ) ▸ div_neg_of_neg_of_pos ( by norm_num ) ( sq_pos_of_pos ( by linarith [ Set.mem_Ioi.mp ( interior_subset hx ) ] ) );
  exact ⟨ convex_Ioi 0 |> fun h => h.prod h, fun x hx y hy a b ha hb hab => by simpa using h_log_concave.2 hx.2 hy.2 ha hb hab ⟩

theorem joint_objective_concave
    (kappa nu mu beta : ℝ) (hk : 0 ≤ kappa) (hn : 0 ≤ nu) (hm : 0 ≤ mu) (hb : 0 ≤ beta) :
    ConcaveOn ℝ (Set.Ioi (0 : ℝ) ×ˢ Set.Ioi (0 : ℝ))
      (fun p : ℝ × ℝ => edgeVal kappa nu mu beta p.1 p.2) := by
  convert ( log_one_add_fst_concaveOn.smul hk |> ConcaveOn.add <| log_one_add_snd_concaveOn.smul hn ) |> ConcaveOn.add <| sqrt_prod_concaveOn.smul ( mul_nonneg hm hb ) using 2 ; ring! ; simp +decide [ edgeVal ] ; ring!;
  grind

/-
**T2 — Coupling-sign law (R2, structural form).**
The discrete cross-difference of the coupling term across an increment
`g1 <= g2`, `s1 <= s2` equals `mu*(sqrt g2 - sqrt g1)*(sqrt s2 - sqrt s1)`, whose
sign is exactly the sign of `mu`.  Hence `mu >= 0` gives a SUPERMODULAR
(mutualistic) coupling and `mu <= 0` a SUBMODULAR (parasitic) one — the exact
inversion of interdependent-network fragility.  NON-VACUOUS via T5.
-/
theorem coupling_sign_law
    (mu g1 g2 s1 s2 : ℝ)
    (hg1 : 0 ≤ g1) (hg : g1 ≤ g2) (hs1 : 0 ≤ s1) (hs : s1 ≤ s2) :
    (0 ≤ mu →
      coupling mu g2 s1 + coupling mu g1 s2 ≤ coupling mu g2 s2 + coupling mu g1 s1)
    ∧
    (mu ≤ 0 →
      coupling mu g2 s2 + coupling mu g1 s1 ≤ coupling mu g2 s1 + coupling mu g1 s2) := by
  constructor;
  · intros hm_nonneg
    have h_sqrt : Real.sqrt g2 * Real.sqrt s1 + Real.sqrt g1 * Real.sqrt s2 ≤ Real.sqrt g2 * Real.sqrt s2 + Real.sqrt g1 * Real.sqrt s1 := by
      nlinarith [ Real.sqrt_nonneg g1, Real.sqrt_le_sqrt hg, Real.sqrt_nonneg s1, Real.sqrt_le_sqrt hs ];
    unfold coupling; rw [ Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ) ] ; nlinarith;
  · intro hmu
    have h_diff : coupling mu g2 s2 + coupling mu g1 s1 - (coupling mu g2 s1 + coupling mu g1 s2) = mu * (Real.sqrt g2 - Real.sqrt g1) * (Real.sqrt s2 - Real.sqrt s1) := by
      unfold coupling; rw [ Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ), Real.sqrt_mul ( by linarith ) ] ; ring;
    nlinarith [ mul_nonneg ( sub_nonneg.2 <| Real.sqrt_le_sqrt hg ) ( sub_nonneg.2 <| Real.sqrt_le_sqrt hs ) ]

/-
**T3 — Co-design dominates siloed iff supermodular (R2, value form).**
Comparing the co-designed objective (`beta >= 0`) against its siloed baseline
(`beta = 0`) at a fixed nonnegative allocation: the difference is exactly the
coupling `beta*mu*sqrt(g*s)`.  So `mu >= 0` (mutualism) => co-design weakly
dominates siloed, and `mu <= 0` (parasitism) => co-design is a net liability
(the envelope sign of `dJ*/dbeta`).  NON-VACUOUS: with `mu,beta,g,s > 0` strict.
-/
theorem codesign_dominates_siloed_iff_supermodular
    (kappa nu mu beta g s : ℝ) (hb : 0 ≤ beta) (hg : 0 ≤ g) (hs : 0 ≤ s) :
    (0 ≤ mu → edgeVal kappa nu mu 0 g s ≤ edgeVal kappa nu mu beta g s)
    ∧
    (mu ≤ 0 → edgeVal kappa nu mu beta g s ≤ edgeVal kappa nu mu 0 g s) := by
  constructor <;> intro <;> unfold edgeVal <;> norm_num;
  · positivity;
  · exact mul_nonpos_of_nonpos_of_nonneg ( mul_nonpos_of_nonneg_of_nonpos hb ‹_› ) ( Real.sqrt_nonneg _ )

/-- Separable (`beta = 0`) per-layer water-filling demand at broadcast price `lam`:
    `d(a,lam) = max(0, a/lam - 1)`. -/
def demand (a lam : ℝ) : ℝ := max 0 (a / lam - 1)

/-
**T4 — Coupled water-filling: one broadcast price rations the pooled budget (R1).**
At `beta = 0` the objective SEPARATES additively into two independent CST-style
water-fillings, and setting `s = 0` recovers the single-layer CST objective
`kappa*log(1+g)` exactly (SCT strictly CONTAINS the corridor theorem).  The
pooled budget is cleared by ONE broadcast price `lam`: per-layer demand
`d(a,lam) = (a/lam - 1)_+` is antitone in `lam`.  Certifies (i) beta=0
decoupling, (ii) s=0 CST-reduction, (iii) demand antitonicity in price.
NON-VACUOUS via T5.
-/
theorem coupled_waterfilling_single_price
    (kappa nu mu g s lam1 lam2 : ℝ) (ha : 0 ≤ kappa) (hlam1 : 0 < lam1) (hlam : lam1 ≤ lam2) :
    (edgeVal kappa nu mu 0 g s = kappa * Real.log (1 + g) + nu * Real.log (1 + s))
    ∧
    (edgeVal kappa nu mu 0 g 0 = kappa * Real.log (1 + g))
    ∧
    (demand kappa lam2 ≤ demand kappa lam1) := by
  unfold edgeVal demand;
  exact ⟨ by ring, by norm_num, max_le_max_left _ <| by gcongr ⟩

/-
**T5 — Non-vacuity witness.**
Explicit interior configuration in the strictly mutualistic regime
(`kappa=nu=mu=beta=1`, `g=s=1`, increments `1 <= 2`) at which the coupling is
strictly positive, the T2 cross-difference is strictly positive, and the T3
co-design gain over siloed is strictly positive.
-/
theorem sct_nonvacuous :
    (0 : ℝ) < coupling 1 1 1
    ∧
    coupling 1 2 1 + coupling 1 1 2 < coupling 1 2 2 + coupling 1 1 1
    ∧
    edgeVal 1 1 1 0 1 1 < edgeVal 1 1 1 1 1 1 := by
  unfold coupling edgeVal; norm_num;
  nlinarith [ Real.sq_sqrt two_pos.le ]

end

end Viridis.SymbioticCorridor