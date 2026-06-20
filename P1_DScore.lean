import Mathlib

/-!
# D-Score Bound

We formalize the D-Score bound from "The Geometry of Biodiversity Collapse" (Hart, 2026).

The D-Score is defined as `D ≡ I(X;Y) / H(X)`, and the main result is that `D ∈ [0, 1]`.

This requires:
1. Shannon entropy is nonnegative for probability measures on finite types.
2. Mutual information is nonnegative (subadditivity of entropy / Gibbs' inequality).
3. Mutual information is bounded above by the marginal entropy.

## Main definitions

* `DScore.entropy μ X` — Shannon entropy of a discrete random variable `X` under measure `μ`.
* `DScore.mutualInfo μ X Y` — Mutual information of `X` and `Y` under measure `μ`.
* `DScore.dScore μ X Y` — The D-Score, `I(X;Y) / H(X)` (with the convention `0` when `H(X) = 0`).

## Main results

* `DScore.mutualInfo_le_entropy_left` — `I(X;Y) ≤ H(X)`.
* `DScore.dScore_mem_Icc` — `D(X;Y) ∈ [0, 1]`.
-/

noncomputable section

open Finset Real MeasureTheory Set

namespace DScore

variable {Ω : Type*} [MeasurableSpace Ω]
variable {α : Type*} [Fintype α] [MeasurableSpace α] [MeasurableSingletonClass α]
variable {β : Type*} [Fintype β] [MeasurableSpace β] [MeasurableSingletonClass β]

/-- Shannon entropy of a discrete random variable `X : Ω → α` under a measure `μ`. -/
noncomputable def entropy (μ : Measure Ω) (X : Ω → α) : ℝ :=
  ∑ a : α, negMulLog ((μ (X ⁻¹' {a})).toReal)

/-- Mutual information of discrete random variables `X` and `Y` under measure `μ`,
    defined as `H(X) + H(Y) - H(X,Y)`. -/
noncomputable def mutualInfo (μ : Measure Ω) (X : Ω → α) (Y : Ω → β) : ℝ :=
  entropy μ X + entropy μ Y - entropy μ (fun ω => (X ω, Y ω))

/-! ### Measure-theoretic auxiliary lemmas -/

private lemma prob_le_one (μ : Measure Ω) [IsProbabilityMeasure μ] (S : Set Ω) :
    (μ S).toReal ≤ 1 := by
  calc (μ S).toReal ≤ (μ Set.univ).toReal :=
        ENNReal.toReal_mono (measure_ne_top _ _) (measure_mono (Set.subset_univ _))
    _ = 1 := by simp [measure_univ]

private lemma prob_nonneg (μ : Measure Ω) (S : Set Ω) :
    0 ≤ (μ S).toReal := ENNReal.toReal_nonneg

private lemma preimage_singleton_measurable {X : Ω → α} (hX : Measurable X) (a : α) :
    MeasurableSet (X ⁻¹' {a}) :=
  hX (measurableSet_singleton a)

private lemma sum_prob_eq_one (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) :
    ∑ a : α, (μ (X ⁻¹' {a})).toReal = 1 := by
      have h_sum_finite : ∑ a : α, μ (X ⁻¹' {a}) = μ Set.univ := by
        rw [ ← MeasureTheory.measure_biUnion_finset ];
        · congr with ω ; aesop;
        · exact fun a _ b _ hab => Set.disjoint_left.mpr fun x => by aesop;
        · exact fun a _ => hX ( MeasurableSingletonClass.measurableSet_singleton a );
      rw [ ← ENNReal.toReal_sum, h_sum_finite, MeasureTheory.IsProbabilityMeasure.measure_univ, ENNReal.toReal_one ];
      exact fun a _ => MeasureTheory.measure_ne_top _ _

private lemma preimage_pair_eq (X : Ω → α) (Y : Ω → β) (a : α) (b : β) :
    (fun ω => (X ω, Y ω)) ⁻¹' {(a, b)} = X ⁻¹' {a} ∩ Y ⁻¹' {b} := by
  ext ω; simp [Set.mem_preimage, Set.mem_inter_iff, Prod.mk.injEq]

private lemma sum_joint_eq_marginal_right (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) (Y : Ω → β) (b : β) :
    ∑ a : α, (μ (X ⁻¹' {a} ∩ Y ⁻¹' {b})).toReal = (μ (Y ⁻¹' {b})).toReal := by
      rw [ ← ENNReal.toReal_sum _ ] <;> norm_num [ hX, Set.preimage ];
      convert congr_arg _ ( MeasureTheory.measure_biUnion_finset _ _ ) using 1;
      rw [ ENNReal.toReal_sum ];
      rotate_left;
      exact fun a _ => MeasureTheory.measure_ne_top _ _;
      rotate_left;
      use fun x => x.toReal;
      exact α;
      exact α;
      exact inferInstance;
      exact MeasureTheory.Measure.map ( fun ω => X ω ) ( μ.restrict { ω | Y ω = b } );
      exact Finset.univ;
      use fun a => { a };
      · exact fun a _ b _ hab => Set.disjoint_singleton.2 hab;
      · exact fun _ _ => MeasurableSingletonClass.measurableSet_singleton _;
      · rw [ MeasureTheory.Measure.map_apply ] <;> norm_num [ hX ];
        · rw [ MeasureTheory.measure_iUnion ];
          · rw [ tsum_fintype ];
            rw [ ENNReal.toReal_sum ];
            · congr! 2;
              rw [ MeasureTheory.Measure.restrict_apply ] ; aesop;
              exact hX ( MeasurableSingletonClass.measurableSet_singleton _ );
            · exact fun a _ => MeasureTheory.measure_ne_top _ _;
          · exact fun i j hij => Set.disjoint_left.mpr fun x hx hx' => hij <| by aesop;
          · exact fun a => hX ( MeasurableSingletonClass.measurableSet_singleton a );
        · exact MeasurableSet.iUnion fun _ => MeasurableSingletonClass.measurableSet_singleton _;
      · rw [ ← MeasureTheory.measure_biUnion_finset ] <;> norm_num [ hX, Set.preimage ];
        · rw [ MeasureTheory.Measure.map_apply ] <;> norm_num [ hX ];
          · rw [ show ( ⋃ i, ( fun ω => X ω ) ⁻¹' { i } ) = Set.univ from Set.eq_univ_of_forall fun x => Set.mem_iUnion.2 ⟨ X x, by simp +decide ⟩ ] ; simp +decide [ MeasureTheory.Measure.restrict_apply ] ;
          · exact MeasurableSet.iUnion fun _ => MeasurableSingletonClass.measurableSet_singleton _;
        · exact fun x _ y _ hxy => Set.disjoint_singleton.2 hxy

private lemma sum_joint_eq_marginal_left (μ : Measure Ω) [IsProbabilityMeasure μ]
    (X : Ω → α) {Y : Ω → β} (hY : Measurable Y) (a : α) :
    ∑ b : β, (μ (X ⁻¹' {a} ∩ Y ⁻¹' {b})).toReal = (μ (X ⁻¹' {a})).toReal := by
  conv_lhs => arg 2; ext b; rw [Set.inter_comm]
  exact sum_joint_eq_marginal_right μ hY X a

private lemma sum_joint_prob_eq_one (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) {Y : Ω → β} (hY : Measurable Y) :
    ∑ a : α, ∑ b : β, (μ (X ⁻¹' {a} ∩ Y ⁻¹' {b})).toReal = 1 := by
  simp_rw [sum_joint_eq_marginal_left _ X hY]
  exact sum_prob_eq_one μ hX

/-! ### negMulLog subadditivity -/

private lemma negMulLog_add_le {a b : ℝ} (ha : 0 ≤ a) (hb : 0 ≤ b) :
    negMulLog (a + b) ≤ negMulLog a + negMulLog b := by
  rcases eq_or_lt_of_le ha with rfl | ha_pos
  · simp [negMulLog_zero]
  rcases eq_or_lt_of_le hb with rfl | hb_pos
  · simp [negMulLog_zero]
  · simp only [negMulLog_eq_neg]
    nlinarith [log_le_log (by positivity) (show a ≤ a + b by linarith),
               log_le_log (by positivity) (show b ≤ a + b by linarith)]

private lemma negMulLog_sum_le {ι : Type*} (s : Finset ι) {f : ι → ℝ}
    (hf : ∀ i ∈ s, 0 ≤ f i) :
    negMulLog (∑ i ∈ s, f i) ≤ ∑ i ∈ s, negMulLog (f i) := by
  classical
  induction' s using Finset.induction with a s ha ih
  · simp [negMulLog_zero]
  · rw [Finset.sum_insert ha, Finset.sum_insert ha]
    have h1 := negMulLog_add_le (hf _ (mem_insert_self _ _))
      (Finset.sum_nonneg fun i hi => hf _ (mem_insert_of_mem hi))
    have h2 := ih fun i hi => hf _ (mem_insert_of_mem hi)
    linarith

/-! ### Gibbs' inequality (finite version) -/

private lemma mul_log_div_le {x y : ℝ} (hx : 0 < x) (hy : 0 < y) :
    x * log (y / x) ≤ y - x := by
  nlinarith [Real.log_le_sub_one_of_pos (div_pos hy hx), mul_div_cancel₀ y hx.ne']

private lemma mul_log_div_le' {x y : ℝ} (hx : 0 ≤ x) (hy : 0 ≤ y) (h : 0 < x → 0 < y) :
    x * log (y / x) ≤ y - x := by
  rcases eq_or_lt_of_le hx with rfl | hx_pos
  · simp; linarith
  · exact mul_log_div_le hx_pos (h hx_pos)

private lemma gibbs_inequality {ι : Type*} (s : Finset ι) {p q : ι → ℝ}
    (hp : ∀ i ∈ s, 0 ≤ p i)
    (hq : ∀ i ∈ s, 0 ≤ q i)
    (hpq : ∀ i ∈ s, 0 < p i → 0 < q i) :
    ∑ i ∈ s, p i * log (q i / p i) ≤ ∑ i ∈ s, q i - ∑ i ∈ s, p i := by
  calc ∑ i ∈ s, p i * log (q i / p i)
      ≤ ∑ i ∈ s, (q i - p i) :=
        Finset.sum_le_sum fun i hi => mul_log_div_le' (hp i hi) (hq i hi) (hpq i hi)
    _ = ∑ i ∈ s, q i - ∑ i ∈ s, p i := by rw [← Finset.sum_sub_distrib]

/-! ### Entropy properties -/

private lemma entropy_nonneg (μ : Measure Ω) [IsProbabilityMeasure μ] (X : Ω → α) :
    0 ≤ entropy μ X :=
  Finset.sum_nonneg fun a _ =>
    Real.negMulLog_nonneg MeasureTheory.measureReal_nonneg MeasureTheory.measureReal_le_one

private lemma entropy_right_le_entropy_prod (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) (Y : Ω → β) :
    entropy μ Y ≤ entropy μ (fun ω => (X ω, Y ω)) := by
      unfold entropy;
      -- By definition of entropy, we can rewrite the right-hand side as a double sum.
      have h_double_sum : ∑ x : α × β, negMulLog ((μ ({ω | (X ω, Y ω) = x})).toReal) = ∑ a : α, ∑ b : β, negMulLog ((μ ({ω | X ω = a ∧ Y ω = b})).toReal) := by
        erw [ Finset.sum_product ] ; aesop;
      have h_double_sum : ∑ a : α, ∑ b : β, negMulLog ((μ ({ω | X ω = a ∧ Y ω = b})).toReal) ≥ ∑ b : β, negMulLog (∑ a : α, (μ ({ω | X ω = a ∧ Y ω = b})).toReal) := by
        rw [ Finset.sum_comm ];
        exact Finset.sum_le_sum fun b _ => negMulLog_sum_le _ fun a _ => by positivity;
      convert h_double_sum.le using 1;
      convert rfl using 2;
      convert congr_arg _ ( sum_joint_eq_marginal_right μ hX Y ‹_› ) using 1

private lemma entropy_prod_le_add (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) {Y : Ω → β} (hY : Measurable Y) :
    entropy μ (fun ω => (X ω, Y ω)) ≤ entropy μ X + entropy μ Y := by
      -- Let's define the probabilities $p(a,b)$, $p(a)$, and $p(b)$ as given in the provided solution.
      set p : α → β → ℝ := fun a b => (μ (X ⁻¹' {a} ∩ Y ⁻¹' {b})).toReal
      set pX : α → ℝ := fun a => (μ (X ⁻¹' {a})).toReal
      set pY : β → ℝ := fun b => (μ (Y ⁻¹' {b})).toReal;
      -- By Gibbs' inequality, we have $\sum_{a,b} p(a,b) \log \frac{p(a,b)}{p(a)p(b)} \geq 0$.
      have gibbs : ∑ a : α, ∑ b : β, p a b * Real.log (p a b / (pX a * pY b)) ≥ 0 := by
        have gibbs : ∀ a b, p a b * Real.log (p a b / (pX a * pY b)) ≥ p a b - pX a * pY b := by
          intro a b
          by_cases h_cases : p a b = 0 ∨ pX a = 0 ∨ pY b = 0;
          · rcases h_cases with ( h | h | h ) <;> simp +decide [ h ];
            · exact mul_nonneg ( ENNReal.toReal_nonneg ) ( ENNReal.toReal_nonneg );
            · exact le_trans ( ENNReal.toReal_mono ( MeasureTheory.measure_ne_top _ _ ) ( MeasureTheory.measure_mono ( Set.inter_subset_left ) ) ) h.le;
            · exact le_trans ( ENNReal.toReal_mono ( MeasureTheory.measure_ne_top _ _ ) ( MeasureTheory.measure_mono ( Set.inter_subset_right ) ) ) h.le;
          · have h_log_ineq : ∀ x y : ℝ, 0 < x → 0 < y → x * Real.log (x / y) ≥ x - y := by
              intro x y hx hy; rw [ Real.log_div hx.ne' hy.ne' ] ; ring_nf; norm_num [ hx, hy ] ;
              have := Real.log_le_sub_one_of_pos ( div_pos hy hx ) ; rw [ Real.log_div hy.ne' hx.ne' ] at this; ring_nf at *; nlinarith [ inv_mul_cancel₀ hx.ne', inv_mul_cancel₀ hy.ne' ] ;
            exact h_log_ineq _ _ ( lt_of_le_of_ne ( ENNReal.toReal_nonneg ) ( Ne.symm ( by tauto ) ) ) ( mul_pos ( lt_of_le_of_ne ( ENNReal.toReal_nonneg ) ( Ne.symm ( by tauto ) ) ) ( lt_of_le_of_ne ( ENNReal.toReal_nonneg ) ( Ne.symm ( by tauto ) ) ) );
        refine' le_trans _ ( Finset.sum_le_sum fun a _ => Finset.sum_le_sum fun b _ => gibbs a b );
        simp +decide [ ← Finset.mul_sum _ _ _, ← Finset.sum_mul, sum_joint_prob_eq_one μ hX hY, sum_prob_eq_one μ hX, sum_prob_eq_one μ hY ];
        rw [ sum_prob_eq_one μ hX, sum_prob_eq_one μ hY, sum_joint_prob_eq_one μ hX hY ] ; norm_num;
      -- Expanding the logarithm in Gibbs' inequality, we get $\sum_{a,b} p(a,b) \log p(a,b) - \sum_{a,b} p(a,b) \log p(a) - \sum_{a,b} p(a,b) \log p(b) \geq 0$.
      have gibbs_expanded : ∑ a, ∑ b, p a b * Real.log (p a b) - ∑ a, ∑ b, p a b * Real.log (pX a) - ∑ a, ∑ b, p a b * Real.log (pY b) ≥ 0 := by
        -- Apply the logarithm property log(a/b) = log(a) - log(b) to each term in the sum.
        have h_log_prop : ∀ a b, p a b * Real.log (p a b / (pX a * pY b)) = p a b * Real.log (p a b) - p a b * Real.log (pX a) - p a b * Real.log (pY b) ∨ p a b = 0 := by
          intro a b; by_cases h : p a b = 0 <;> by_cases h' : pX a = 0 <;> by_cases h'' : pY b = 0 <;> simp +decide [ *, Real.log_div, Real.log_mul ] ; ring;
          · contrapose! h';
            refine' ne_of_gt ( ENNReal.toReal_pos _ _ );
            · intro H; simp_all +decide [ MeasureTheory.measure_eq_zero_iff_ae_notMem ] ;
              exact h ( by rw [ show p a b = 0 from by rw [ show p a b = ( μ ( X ⁻¹' { a } ∩ Y ⁻¹' { b } ) |> ENNReal.toReal ) from rfl ] ; exact by rw [ MeasureTheory.measure_eq_zero_iff_ae_notMem.mpr ( by filter_upwards [ H ] with ω hω; aesop ) ] ; norm_num ] );
            · exact MeasureTheory.measure_ne_top _ _;
          · simp +zetaDelta at *;
            rw [ MeasureTheory.measure_mono_null ( Set.inter_subset_left ) ( show μ ( X ⁻¹' { a } ) = 0 from by rw [ ENNReal.toReal_eq_zero_iff ] at h'; aesop ) ] at h; aesop;
          · contrapose! h''; simp_all +decide [ Set.preimage ] ; (
            exact ne_of_gt ( ENNReal.toReal_pos ( by aesop ) ( by aesop ) ) |> fun h => ne_of_gt ( lt_of_lt_of_le ( show 0 < p a b from lt_of_le_of_ne ( ENNReal.toReal_nonneg ) ( Ne.symm h ) ) ( ENNReal.toReal_mono ( by aesop ) ( MeasureTheory.measure_mono ( show X ⁻¹' { a } ∩ Y ⁻¹' { b } ⊆ Y ⁻¹' { b } from fun x hx => hx.2 ) ) ) ) ;);
          · ring;
        refine' gibbs.trans _;
        simpa only [ ← Finset.sum_sub_distrib ] using Finset.sum_le_sum fun a _ => Finset.sum_le_sum fun b _ => by cases h_log_prop a b <;> simp +decide [ * ] ;
      -- Using the definitions of $p$, $pX$, and $pY$, we can rewrite the sums in Gibbs' inequality.
      have gibbs_rewrite : ∑ a, ∑ b, p a b * Real.log (p a b) = -entropy μ (fun ω => (X ω, Y ω)) ∧ ∑ a, ∑ b, p a b * Real.log (pX a) = -entropy μ X ∧ ∑ a, ∑ b, p a b * Real.log (pY b) = -entropy μ Y := by
        refine' ⟨ _, _, _ ⟩ <;> simp +decide [ negMulLog_eq_neg, entropy ] <;> ring!;
        · simp +decide [ Set.preimage, Finset.sum_product' ];
          rw [ ← Finset.sum_product' ] ; congr ; ext ; aesop;
        · rw [ Finset.sum_congr rfl ] ; intros ; rw [ ← Finset.sum_mul _ _ _ ] ; rw [ sum_joint_eq_marginal_left ] ; aesop;
        · rw [ Finset.sum_comm ];
          exact Finset.sum_congr rfl fun _ _ => by rw [ ← Finset.sum_mul ] ; exact sum_joint_eq_marginal_right μ hX Y _ ▸ rfl;
      linarith

private lemma mutualInfo_nonneg (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) {Y : Ω → β} (hY : Measurable Y) :
    0 ≤ mutualInfo μ X Y :=
  sub_nonneg_of_le (entropy_prod_le_add μ hX hY)

/-! ### Main theorems -/

/-- **Theorem 1**: Mutual information is bounded above by the entropy of the first marginal:
    `I(X; Y) ≤ H(X)`. -/
theorem mutualInfo_le_entropy_left (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) (Y : Ω → β) :
    mutualInfo μ X Y ≤ entropy μ X := by
  unfold mutualInfo
  linarith [entropy_right_le_entropy_prod μ hX Y]

/-- The D-Score: ratio of mutual information to marginal entropy,
    with the convention that D = 0 when H(X) = 0. -/
noncomputable def dScore (μ : Measure Ω) (X : Ω → α) (Y : Ω → β) : ℝ :=
  if _ : entropy μ X = 0 then 0
  else mutualInfo μ X Y / entropy μ X

/-- **Theorem 2**: The D-Score lies in `[0, 1]`. -/
theorem dScore_mem_Icc (μ : Measure Ω) [IsProbabilityMeasure μ]
    {X : Ω → α} (hX : Measurable X) {Y : Ω → β} (hY : Measurable Y) :
    dScore μ X Y ∈ Set.Icc 0 1 := by
  unfold dScore
  split_ifs with h
  · constructor <;> norm_num
  · constructor
    · exact div_nonneg (mutualInfo_nonneg μ hX hY) (entropy_nonneg μ X)
    · exact div_le_one_of_le₀ (mutualInfo_le_entropy_left μ hX Y) (entropy_nonneg μ X)

end DScore