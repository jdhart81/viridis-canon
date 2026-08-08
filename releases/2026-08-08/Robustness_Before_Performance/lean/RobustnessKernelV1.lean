import Mathlib.Data.Finset.Card
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

set_option autoImplicit false

namespace Viridis.RobustnessKernelV1

/-! ## F1 — Expanded dependency diversity -/

def dependencyIndependence {α : Type*} [DecidableEq α]
    (left right : Finset α) : ℚ :=
  1 - ((left ∩ right).card : ℚ) / ((left ∪ right).card : ℚ)

def HiddenCommonParent {α : Type*} [DecidableEq α]
    (directLeft directRight : Finset α) (parent : α) : Prop :=
  Disjoint directLeft directRight ∧
    parent ∉ directLeft ∧
    parent ∉ directRight

theorem shared_dependency_strictly_reduces_independence
    {α : Type*} [DecidableEq α]
    (left right : Finset α) (shared : α)
    (hleft : shared ∈ left) (hright : shared ∈ right) :
    dependencyIndependence left right < 1 := by
  have hi : 0 < ((left ∩ right).card : ℚ) := by
    exact_mod_cast Finset.card_pos.mpr ⟨shared, Finset.mem_inter.mpr ⟨hleft, hright⟩⟩
  have hu : 0 < ((left ∪ right).card : ℚ) := by
    exact_mod_cast Finset.card_pos.mpr ⟨shared, Finset.mem_union_left _ hleft⟩
  have hpos := div_pos hi hu
  unfold dependencyIndependence
  linarith

theorem hidden_common_parent_lowers_independence
    {α : Type*} [DecidableEq α]
    (directLeft directRight : Finset α) (parent : α)
    (hhidden : HiddenCommonParent directLeft directRight parent) :
    dependencyIndependence (insert parent directLeft) (insert parent directRight) <
      dependencyIndependence directLeft directRight := by
  obtain ⟨hdisj, hpL, hpR⟩ := hhidden
  have hinter : directLeft ∩ directRight = ∅ := Finset.disjoint_iff_inter_eq_empty.mp hdisj
  have hrhs : dependencyIndependence directLeft directRight = 1 := by
    simp [dependencyIndependence, hinter]
  have hinter2 : (insert parent directLeft) ∩ (insert parent directRight) = {parent} := by
    ext x
    simp only [Finset.mem_inter, Finset.mem_insert, Finset.mem_singleton]
    constructor
    · rintro ⟨hl | hl, hr | hr⟩
      · exact hl
      · exact hl
      · exact hr
      · exact absurd (Finset.mem_inter.mpr ⟨hl, hr⟩) (by simp [hinter])
    · rintro rfl
      exact ⟨Or.inl rfl, Or.inl rfl⟩
  have hu : 0 < ((insert parent directLeft ∪ insert parent directRight).card : ℚ) := by
    exact_mod_cast Finset.card_pos.mpr ⟨parent, by simp⟩
  rw [hrhs]
  unfold dependencyIndependence
  rw [hinter2]
  simp only [Finset.card_singleton, Nat.cast_one]
  have hpos := div_pos (by norm_num : (0 : ℚ) < 1) hu
  linarith

/-! ## F2 — Selection and execution authority are distinct -/

structure AuthorityLease where
  advisoryOnly : Bool
  actionAllowed : Bool
  active : Bool
  scopeMatches : Bool
  unexpired : Bool
deriving DecidableEq, Repr

def executionAuthorized (selected : Bool) (lease : AuthorityLease) : Bool :=
  selected &&
    !lease.advisoryOnly &&
    lease.actionAllowed &&
    lease.active &&
    lease.scopeMatches &&
    lease.unexpired

theorem execution_authority_gate_iff
    (selected : Bool) (lease : AuthorityLease) :
    executionAuthorized selected lease = true ↔
      selected = true ∧
      lease.advisoryOnly = false ∧
      lease.actionAllowed = true ∧
      lease.active = true ∧
      lease.scopeMatches = true ∧
      lease.unexpired = true := by
  obtain ⟨a, b, c, d, e⟩ := lease
  cases selected <;> cases a <;> cases b <;> cases c <;> cases d <;> cases e <;>
    simp [executionAuthorized]

theorem advisory_selection_never_authorizes_execution
    (selected : Bool) (lease : AuthorityLease)
    (hadvisory : lease.advisoryOnly = true) :
    executionAuthorized selected lease = false := by
  rw [Bool.eq_false_iff, ne_eq, execution_authority_gate_iff]
  rintro ⟨-, hnotAdvisory, -⟩
  rw [hadvisory] at hnotAdvisory
  exact Bool.noConfusion hnotAdvisory

theorem revoked_or_expired_lease_denies_execution
    (selected : Bool) (lease : AuthorityLease)
    (hclosed : lease.active = false ∨ lease.unexpired = false) :
    executionAuthorized selected lease = false := by
  rcases hclosed with h | h <;> simp [executionAuthorized, h]

/-! ## F3 — Epistemic firewall -/

inductive ClaimState where
  | assumed
  | hypothesized
  | numericallySupported
  | reproduced
  | formallyProved
  | empiricallySupported
  | authorized
  | deployed
  | observed
deriving DecidableEq, Repr

def derivable (asserted : Finset ClaimState) (state : ClaimState) : Prop :=
  state ∈ asserted

theorem derivable_iff_explicitly_asserted
    (asserted : Finset ClaimState) (state : ClaimState) :
    derivable asserted state ↔ state ∈ asserted := Iff.rfl

theorem distinct_state_is_not_derived_from_singleton
    (source target : ClaimState) (hdifferent : source ≠ target) :
    ¬ derivable {source} target := by
  intro hderived
  have heq : target = source := by
    simpa [derivable] using hderived
  exact hdifferent heq.symm

/-! ## F4 — Cascading recall -/

def lineageBlocked {α : Type*} [DecidableEq α]
    (parent : α → α → Prop) (recalled : Finset α) (node : α) : Prop :=
  ∃ root, root ∈ recalled ∧
    (node = root ∨ Relation.TransGen parent root node)

theorem recalled_artifact_is_blocked
    {α : Type*} [DecidableEq α]
    (parent : α → α → Prop) (recalled : Finset α) (node : α)
    (hrecalled : node ∈ recalled) :
    lineageBlocked parent recalled node := by
  exact ⟨node, hrecalled, Or.inl rfl⟩

theorem descendant_of_recalled_artifact_is_blocked
    {α : Type*} [DecidableEq α]
    (parent : α → α → Prop) (recalled : Finset α) (root node : α)
    (hrecalled : root ∈ recalled)
    (hdescendant : Relation.TransGen parent root node) :
    lineageBlocked parent recalled node := by
  exact ⟨root, hrecalled, Or.inr hdescendant⟩

theorem unrelated_artifact_is_not_blocked
    {α : Type*} [DecidableEq α]
    (parent : α → α → Prop) (recalled : Finset α) (node : α)
    (hunrelated : ∀ root ∈ recalled,
      node ≠ root ∧ ¬ Relation.TransGen parent root node) :
    ¬ lineageBlocked parent recalled node := by
  rintro ⟨root, hrecalled, heq | hdescendant⟩
  · exact (hunrelated root hrecalled).1 heq
  · exact (hunrelated root hrecalled).2 hdescendant

/-! ## F5 — Closed-interval viability -/

structure ClosedInterval where
  lower : ℚ
  upper : ℚ
  valid : lower ≤ upper
deriving Repr

inductive InvariantOperator where
  | ge
  | gt
  | le
  | lt
  | eq
deriving DecidableEq, Repr

inductive ViabilityState where
  | robustPass
  | robustFail
  | uncertain
deriving DecidableEq, Repr

def robustPass (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) : Prop :=
  match operator with
  | .ge => threshold ≤ interval.lower
  | .gt => threshold < interval.lower
  | .le => interval.upper ≤ threshold
  | .lt => interval.upper < threshold
  | .eq => interval.lower = threshold ∧ interval.upper = threshold

def robustFail (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) : Prop :=
  match operator with
  | .ge => interval.upper < threshold
  | .gt => interval.upper ≤ threshold
  | .le => threshold < interval.lower
  | .lt => threshold ≤ interval.lower
  | .eq => interval.upper < threshold ∨ threshold < interval.lower

instance robustPassDecidable (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    Decidable (robustPass operator threshold interval) := by
  unfold robustPass
  cases operator <;> infer_instance

instance robustFailDecidable (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    Decidable (robustFail operator threshold interval) := by
  unfold robustFail
  cases operator <;> infer_instance

def classifyInterval (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) : ViabilityState :=
  if robustPass operator threshold interval then .robustPass
  else if robustFail operator threshold interval then .robustFail
  else .uncertain

theorem robust_pass_and_fail_are_disjoint
    (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    ¬ (robustPass operator threshold interval ∧
      robustFail operator threshold interval) := by
  intro h
  rcases h with ⟨hpass, hfail⟩
  cases operator <;>
    simp only [robustPass, robustFail] at hpass hfail
  · linarith [interval.valid]
  · linarith [interval.valid]
  · linarith [interval.valid]
  · linarith [interval.valid]
  · rcases hpass with ⟨hlower, hupper⟩
    rcases hfail with hfail | hfail <;> linarith

theorem interval_classification_complete
    (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    classifyInterval operator threshold interval = .robustPass ∨
    classifyInterval operator threshold interval = .robustFail ∨
    classifyInterval operator threshold interval = .uncertain := by
  cases classifyInterval operator threshold interval <;> simp

theorem interval_classification_pass_iff
    (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    classifyInterval operator threshold interval = .robustPass ↔
      robustPass operator threshold interval := by
  constructor
  · intro hclassification
    by_cases hpass : robustPass operator threshold interval
    · exact hpass
    · by_cases hfail : robustFail operator threshold interval
      · have : False := by
          simp [classifyInterval, hpass, hfail] at hclassification
        exact this.elim
      · have : False := by
          simp [classifyInterval, hpass, hfail] at hclassification
        exact this.elim
  · intro hpass
    simp [classifyInterval, hpass]

theorem interval_classification_fail_iff
    (operator : InvariantOperator) (threshold : ℚ)
    (interval : ClosedInterval) :
    classifyInterval operator threshold interval = .robustFail ↔
      robustFail operator threshold interval := by
  constructor
  · simp only [classifyInterval]
    split <;> rename_i hpass
    · simp
    · split <;> simp_all
  · intro hfail
    have hnotpass : ¬ robustPass operator threshold interval := by
      intro hpass
      exact robust_pass_and_fail_are_disjoint operator threshold interval
        ⟨hpass, hfail⟩
    simp [classifyInterval, hnotpass, hfail]

/-! ## F6 — Robust interval dominance -/

inductive Direction where
  | maximize
  | minimize
deriving DecidableEq, Repr

def robustNoWorse (direction : Direction)
    (left right : ClosedInterval) : Prop :=
  match direction with
  | .maximize => right.upper ≤ left.lower
  | .minimize => left.upper ≤ right.lower

def robustStrict (direction : Direction)
    (left right : ClosedInterval) : Prop :=
  match direction with
  | .maximize => right.upper < left.lower
  | .minimize => left.upper < right.lower

def robustDominates {n : Nat} (directions : Fin n → Direction)
    (left right : Fin n → ClosedInterval) : Prop :=
  (∀ index, robustNoWorse (directions index) (left index) (right index)) ∧
    ∃ index, robustStrict (directions index) (left index) (right index)

theorem robust_no_worse_transitive
    (direction : Direction) (left middle right : ClosedInterval)
    (hlm : robustNoWorse direction left middle)
    (hmr : robustNoWorse direction middle right) :
    robustNoWorse direction left right := by
  cases direction <;> simp [robustNoWorse] at * <;> linarith [middle.valid]

theorem robust_strict_then_no_worse
    (direction : Direction) (left middle right : ClosedInterval)
    (hlm : robustStrict direction left middle)
    (hmr : robustNoWorse direction middle right) :
    robustStrict direction left right := by
  cases direction <;> simp [robustStrict, robustNoWorse] at * <;>
    linarith [middle.valid]

theorem robust_dominance_irreflexive
    {n : Nat} (directions : Fin n → Direction)
    (profile : Fin n → ClosedInterval) :
    ¬ robustDominates directions profile profile := by
  rintro ⟨-, index, hstrict⟩
  cases hdirection : directions index <;>
    simp [robustStrict, hdirection] at hstrict <;>
    linarith [(profile index).valid]

theorem robust_dominance_transitive
    {n : Nat} (directions : Fin n → Direction)
    (left middle right : Fin n → ClosedInterval)
    (hlm : robustDominates directions left middle)
    (hmr : robustDominates directions middle right) :
    robustDominates directions left right := by
  rcases hlm with ⟨hlmNoWorse, index, hlmStrict⟩
  rcases hmr with ⟨hmrNoWorse, -⟩
  constructor
  · intro current
    exact robust_no_worse_transitive
      (directions current) (left current) (middle current) (right current)
      (hlmNoWorse current) (hmrNoWorse current)
  · exact ⟨index, robust_strict_then_no_worse
      (directions index) (left index) (middle index) (right index)
      hlmStrict (hmrNoWorse index)⟩

/-! ## F7 — Sampled trajectory measures -/

def marginShortfall (margin : ℚ) : ℚ := max 0 (-margin)

structure TrajectorySegment where
  duration : ℚ
  durationNonnegative : 0 ≤ duration
  leftMargin : ℚ
  rightMargin : ℚ
deriving Repr

def segmentShortfall (segment : TrajectorySegment) : ℚ :=
  segment.duration *
    (marginShortfall segment.leftMargin + marginShortfall segment.rightMargin) / 2

def trajectoryShortfall (segments : List TrajectorySegment) : ℚ :=
  (segments.map segmentShortfall).sum

theorem margin_shortfall_nonnegative (margin : ℚ) :
    0 ≤ marginShortfall margin := by
  exact le_max_left 0 (-margin)

theorem segment_shortfall_nonnegative (segment : TrajectorySegment) :
    0 ≤ segmentShortfall segment := by
  have hleft := margin_shortfall_nonnegative segment.leftMargin
  have hright := margin_shortfall_nonnegative segment.rightMargin
  have hsum : 0 ≤ marginShortfall segment.leftMargin +
      marginShortfall segment.rightMargin := add_nonneg hleft hright
  have hproduct : 0 ≤ segment.duration *
      (marginShortfall segment.leftMargin +
        marginShortfall segment.rightMargin) :=
    mul_nonneg segment.durationNonnegative hsum
  unfold segmentShortfall
  exact div_nonneg hproduct (by norm_num)

theorem trajectory_shortfall_nonnegative
    (segments : List TrajectorySegment) :
    0 ≤ trajectoryShortfall segments := by
  induction segments with
  | nil => simp [trajectoryShortfall]
  | cons head tail ih =>
      simp only [trajectoryShortfall, List.map_cons, List.sum_cons]
      exact add_nonneg (segment_shortfall_nonnegative head) ih

theorem margin_shortfall_eq_zero (margin : ℚ) (hnonnegative : 0 ≤ margin) :
    marginShortfall margin = 0 := by
  simp [marginShortfall, max_eq_left (neg_nonpos.mpr hnonnegative)]

theorem nonnegative_trajectory_has_zero_shortfall
    (segments : List TrajectorySegment)
    (hnonnegative : ∀ segment ∈ segments,
      0 ≤ segment.leftMargin ∧ 0 ≤ segment.rightMargin) :
    trajectoryShortfall segments = 0 := by
  induction segments with
  | nil => simp [trajectoryShortfall]
  | cons head tail ih =>
      have hhead := hnonnegative head (by simp)
      have htail : ∀ segment ∈ tail,
          0 ≤ segment.leftMargin ∧ 0 ≤ segment.rightMargin := by
        intro segment hsegment
        exact hnonnegative segment (by simp [hsegment])
      have hzLeft := margin_shortfall_eq_zero head.leftMargin hhead.1
      have hzRight := margin_shortfall_eq_zero head.rightMargin hhead.2
      have htailZero : (tail.map segmentShortfall).sum = 0 := by
        simpa [trajectoryShortfall] using ih htail
      simp [trajectoryShortfall, segmentShortfall, hzLeft, hzRight, htailZero]

def markedViolationSpan (mark : TrajectorySegment → Bool)
    (segments : List TrajectorySegment) : ℚ :=
  (segments.map fun segment => if mark segment then segment.duration else 0).sum

theorem marked_violation_span_nonnegative
    (mark : TrajectorySegment → Bool) (segments : List TrajectorySegment) :
    0 ≤ markedViolationSpan mark segments := by
  induction segments with
  | nil => simp [markedViolationSpan]
  | cons head tail ih =>
      have ihExpanded :
          0 ≤ (tail.map fun segment =>
            if mark segment then segment.duration else 0).sum := by
        simpa [markedViolationSpan] using ih
      cases hmark : mark head
      · simpa [markedViolationSpan, hmark] using ihExpanded
      · simpa [markedViolationSpan, hmark] using
          add_nonneg head.durationNonnegative ihExpanded

/-! ## F8 — Aftershock count -/

def aftershockTransition (left right : ViabilityState) : Nat :=
  if left = .robustPass ∧ right ≠ .robustPass then 1 else 0

def aftershockCount : List ViabilityState → Nat
  | [] => 0
  | [_] => 0
  | left :: right :: rest =>
      aftershockTransition left right + aftershockCount (right :: rest)

theorem aftershock_count_le_adjacent_pairs
    (states : List ViabilityState) :
    aftershockCount states ≤ states.length - 1 := by
  induction states with
  | nil => simp [aftershockCount]
  | cons head tail ih =>
      cases tail with
      | nil => simp [aftershockCount]
      | cons next rest =>
          simp only [aftershockCount, List.length_cons, Nat.add_sub_cancel]
          have htransition : aftershockTransition head next ≤ 1 := by
            unfold aftershockTransition
            split <;> simp
          have hrest : aftershockCount (next :: rest) ≤ rest.length := by
            simpa using ih
          calc
            aftershockTransition head next + aftershockCount (next :: rest) ≤
                1 + rest.length := Nat.add_le_add htransition hrest
            _ = rest.length + 1 := Nat.add_comm 1 rest.length

/-! ## F9 — Release and outcome states remain independently representable -/

structure ReleaseStates where
  formallyProved : Bool
  selected : Bool
  authorized : Bool
  deployed : Bool
  observed : Bool
deriving DecidableEq, Repr

theorem release_states_are_independent_nonvacuous :
    ∃ states : ReleaseStates,
      states.formallyProved = true ∧
      states.selected = false ∧
      states.authorized = false ∧
      states.deployed = false ∧
      states.observed = false := by
  exact ⟨⟨true, false, false, false, false⟩, by decide⟩

/-! ## Cross-mechanism non-vacuity witness -/

theorem robustness_kernel_v1_nonvacuous :
    let safe : ClosedInterval := ⟨2, 3, by norm_num⟩
    let unsafeInterval : ClosedInterval := ⟨-3, -2, by norm_num⟩
    let validLease : AuthorityLease :=
      ⟨false, true, true, true, true⟩
    classifyInterval .ge 1 safe = .robustPass ∧
      classifyInterval .ge 1 unsafeInterval = .robustFail ∧
      robustStrict .maximize safe unsafeInterval ∧
      executionAuthorized true validLease = true ∧
      aftershockCount [.robustPass, .robustFail, .robustPass, .robustFail] = 2 := by
  norm_num [classifyInterval, robustPass, robustFail, robustStrict,
    executionAuthorized, aftershockCount, aftershockTransition]
  decide

end Viridis.RobustnessKernelV1
