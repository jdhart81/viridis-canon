/-
Independent review checks for `RobustnessKernelV1`.

This file adds *no* new definitions, hypotheses, or axioms to the frozen
contract in `RobustnessKernelV1.lean`.  It only records executable sanity
certificates showing that the frozen definitions are non-degenerate: the
Jaccard-style dependency metric takes its expected intermediate values, the
Boolean authority gate really can deny as well as grant, the epistemic
firewall really does block a non-asserted state, the closed-interval
classifier really does emit all three verdicts, robust dominance is
non-trivially inhabited, and the trajectory and aftershock measures return the
expected rational / natural values on concrete data.

Every statement below is closed by `decide`, `norm_num`, or `rfl`, i.e. by
kernel-checked evaluation only.
-/
import RobustnessKernelV1

namespace Viridis.RobustnessKernelV1.ReviewChecks

open Viridis.RobustnessKernelV1

/-! ### F1 — the dependency metric is a genuine Jaccard complement -/

/-- Disjoint dependency sets give full independence. -/
theorem dependency_disjoint_is_one :
    dependencyIndependence ({1, 2} : Finset ℕ) ({3, 4} : Finset ℕ) = 1 := by
  norm_num [dependencyIndependence]

/-- One shared dependency out of three gives `2/3`, an intermediate value. -/
theorem dependency_one_shared_is_two_thirds :
    dependencyIndependence ({1, 2} : Finset ℕ) ({2, 3} : Finset ℕ) = 2 / 3 := by
  norm_num [dependencyIndependence]

/-- Identical dependency sets give zero independence. -/
theorem dependency_equal_is_zero :
    dependencyIndependence ({1, 2} : Finset ℕ) ({1, 2} : Finset ℕ) = 0 := by
  norm_num [dependencyIndependence]

/-! ### F2 — the authority gate both grants and denies -/

theorem authority_grants_on_full_lease :
    executionAuthorized true ⟨false, true, true, true, true⟩ = true := by decide

theorem authority_denies_unselected :
    executionAuthorized false ⟨false, true, true, true, true⟩ = false := by decide

theorem authority_denies_advisory :
    executionAuthorized true ⟨true, true, true, true, true⟩ = false := by decide

theorem authority_denies_out_of_scope :
    executionAuthorized true ⟨false, true, true, false, true⟩ = false := by decide

/-! ### F3 — the epistemic firewall blocks a non-asserted state -/

theorem numerical_support_does_not_yield_proof :
    ¬ derivable {ClaimState.numericallySupported} ClaimState.formallyProved := by
  unfold derivable; decide

theorem asserted_state_is_derivable :
    derivable {ClaimState.numericallySupported} ClaimState.numericallySupported := by
  unfold derivable; decide

/-! ### F5 — the classifier emits all three verdicts -/

theorem classifier_emits_pass :
    classifyInterval .ge 1 ⟨2, 3, by norm_num⟩ = .robustPass := by
  norm_num [classifyInterval, robustPass]

theorem classifier_emits_fail :
    classifyInterval .ge 1 ⟨-1, 0, by norm_num⟩ = .robustFail := by
  norm_num [classifyInterval, robustPass, robustFail]

theorem classifier_emits_uncertain :
    classifyInterval .ge 1 ⟨0, 2, by norm_num⟩ = .uncertain := by
  norm_num [classifyInterval, robustPass, robustFail]

/-! ### F6 — robust dominance is non-trivially inhabited -/

theorem robust_dominance_nonvacuous :
    robustDominates (fun _ : Fin 1 => Direction.maximize)
      (fun _ => ⟨5, 6, by norm_num⟩) (fun _ => ⟨0, 1, by norm_num⟩) := by
  refine ⟨fun _ => ?_, ⟨0, ?_⟩⟩ <;> norm_num [robustNoWorse, robustStrict]

/-- Overlapping intervals are *not* robustly dominant: the relation is strict. -/
theorem overlapping_intervals_do_not_dominate :
    ¬ robustDominates (fun _ : Fin 1 => Direction.maximize)
      (fun _ => ⟨0, 2, by norm_num⟩) (fun _ => ⟨1, 3, by norm_num⟩) := by
  rintro ⟨hno, -⟩
  have := hno 0
  norm_num [robustNoWorse] at this

/-! ### F7 — the trajectory measures are non-degenerate -/

theorem shortfall_of_violating_trajectory :
    trajectoryShortfall [⟨2, by norm_num, -1, -3⟩] = 4 := by
  norm_num [trajectoryShortfall, segmentShortfall, marginShortfall]

theorem span_counts_only_marked_segments :
    markedViolationSpan (fun segment => decide (segment.leftMargin < 0))
      [⟨2, by norm_num, -1, 0⟩, ⟨5, by norm_num, 1, 1⟩] = 2 := by
  norm_num [markedViolationSpan]

/-! ### F8 — the aftershock counter is non-degenerate -/

theorem aftershock_counts_downward_transitions :
    aftershockCount [.robustPass, .uncertain, .robustPass, .robustFail] = 2 := by
  decide

theorem aftershock_of_stable_trajectory_is_zero :
    aftershockCount [.robustPass, .robustPass, .robustPass] = 0 := by decide

/-! ### F9 — release states are genuinely independent -/

theorem release_states_deployment_without_observation :
    ∃ states : ReleaseStates,
      states.formallyProved = true ∧ states.selected = true ∧
      states.authorized = true ∧ states.deployed = true ∧
      states.observed = false :=
  ⟨⟨true, true, true, true, false⟩, by decide⟩

end Viridis.RobustnessKernelV1.ReviewChecks
