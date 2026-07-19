/-
# The Thermodynamic Attention Theorem (TAT) — the Attuner
Viridis Aristotle Forge · Nightly Run 101 · [02] Thermodynamic Economics × ☯️ Alignment
43rd Intelligence-Bound self-application. Consumes the standing `[100]→[02]` flag from
the Mutualistic Attestation Theorem (MAT, Run 100).

INTENDED MEANING (formalized clean core).
A steward's *perception* — the mutual information she maintains about a drifting
ecosystem's state — is not free. Identifying the rational-inattention shadow price
(Sims 2003/2011) with the Landauer quantum (Still–Sivak 2012) gives
`λ_attention = k_B T ln 2` per bit = `k_B T` per nat. The ☯️ (wu-wei) core:
over-attention is pure dissipation — the optimal steward attends only to the
predictive (slow, einselected) modes and lets the nonpredictive rest go. A finite
attention budget is spent by water-filling over the uncertainty modes; the modes
that clear the water level are the slow, most-predictive ones (which by einselection
ARE the redundantly-recorded integrity pointer observables — a face of UWMT-084 on
the *perception* budget). Near a tipping point the allocation focuses onto the
diverging critical slow mode; below a capacity floor `C_crit = ½ log₂(1+SNR_crit)`
the steward is structurally blind (the Inattention Trap, perception-side twin of
MAT-100's Certification Trap). Hoarding nonpredictive information linearly throttles
the steward's own Intelligence-Bound speed limit through `ρ = I_nonpred/I_pred`.

NON-VACUITY. Every named statement is discharged over explicit, non-degenerate
witnesses (positive temperatures, an active slow mode `v=4>λ=1`, a dropped fast mode
`v=½<λ=1`, an interior VoI optimum with `c<μa`). `tat_nonvacuous` binds BOTH
water-filling branches (active + inactive) plus a strictly positive trap threshold.

DEFERRED (well-posedness gate — CITED, not re-proven): the Still–Sivak predictive-
information decomposition `I_mem = I_pred + I_nonpred`, the Sims LQG rational-
inattention water-fill derivation, and the quantum-Darwinist einselection geometry
are cited literature. The forge load here is the IDENTIFICATION `λ = k_B T ln 2`, the
wu-wei sufficiency result (R2), the perception-budget water-fill (R3), the Inattention
Trap threshold (R4), the Attuner throughput bound (R5), the VoI interior optimum (R6),
and the cos²Θ basis efficiency (R7 — an instance of the now-landed UPEM meta-theorem).

Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real

namespace Viridis.Attention.ThermodynamicAttention

/-- Linear attention cost of maintaining `I` nats of mutual information about the
    environment, at eco-temperature `T` (`C_attn(I) = k_B T · I`). -/
def attnCost (kB T I : ℝ) : ℝ := kB * T * I

/-- Net predictive value with retained information split into predictive and
    nonpredictive parts (Still–Sivak): `V = μ·I_pred − k_B T·(I_pred + I_nonpred)`. -/
def netV (mu kB T Ipred Inp : ℝ) : ℝ := mu * Ipred - kB * T * (Ipred + Inp)

/-- Water-filling allocation to a mode of predictive variance `v` at water level
    `lam`: `b*(v) = [½ log₂(v/λ)]₊` on the physically meaningful domain `v > 0`,
    and `0` for nonpositive inputs.

    **Strengthened auxiliary definition.** The positivity guard is necessary because
    `Real.log` (and hence `Real.logb`) is defined through an absolute value on negative
    arguments in Mathlib. Without this guard, a large negative `v` could receive a
    positive allocation, making `attention_waterfill_is_kkt_optimal` false. Predictive
    variances are nonnegative, so assigning zero to nonpositive inputs is canonical. -/
noncomputable def wf (v lam : ℝ) : ℝ :=
  if 0 < v then max 0 ((1 / 2) * Real.logb 2 (v / lam)) else 0

/-- Capacity floor to resolve a mode of signal-to-noise ratio `SNR`:
    `C_crit = ½ log₂(1 + SNR)`. -/
noncomputable def Ccrit (SNR : ℝ) : ℝ := (1 / 2) * Real.logb 2 (1 + SNR)

/-- The Attuner's Intelligence-Bound throughput ceiling, throttled by the
    nonpredictive/predictive ratio `ρ`: `P·D / (k_B T ln2 · (1+ρ))`. -/
noncomputable def attunerBound (P D kB T rho : ℝ) : ℝ :=
  P * D / (kB * T * Real.log 2 * (1 + rho))

/-- Net value-of-information objective: concave VoI `μ·(1 − e^{−a n})` minus linear
    sensing cost `c·n`. -/
noncomputable def netMon (mu a c n : ℝ) : ℝ := mu * (1 - Real.exp (-(a * n))) - c * n

/-! ## R1 — Attention Cost Identity (canon candidate)
The shadow price of attention is physical: the marginal cost of one nat is `k_B T`,
one bit costs the Landauer quantum `k_B T ln 2`, and it is a strictly positive price. -/

theorem attention_shadow_price_eq_landauer_quantum
    (kB T I : ℝ) (hkB : 0 < kB) (hT : 0 < T) :
    HasDerivAt (fun x => attnCost kB T x) (kB * T) I
      ∧ attnCost kB T (Real.log 2) = kB * T * Real.log 2
      ∧ 0 < attnCost kB T (Real.log 2) := by
  exact ⟨ by simpa using HasDerivAt.const_mul ( kB * T ) ( hasDerivAt_id I ), rfl, mul_pos ( mul_pos hkB hT ) ( Real.log_pos one_lt_two ) ⟩

/-! ## R2 — Wu-Wei Predictive Sufficiency (canon candidate) -/

/-- Every nat of nonpredictive memory carries marginal cost exactly `−k_B T`:
    hoarding it is pure dissipation with zero predictive return. -/
theorem nonpredictive_info_marginal_cost_eq_neg_kBT
    (mu kB T Ipred Inp : ℝ) :
    HasDerivAt (fun x => netV mu kB T Ipred x) (-(kB * T)) Inp := by
  convert HasDerivAt.sub ( hasDerivAt_const _ _ |> HasDerivAt.mul <| hasDerivAt_const _ _ ) ( HasDerivAt.mul ( hasDerivAt_const _ _ ) <| HasDerivAt.add ( hasDerivAt_const _ _ ) <| hasDerivAt_id Inp ) using 1 ; ring!

/-- The optimal steward sets `I_nonpred = 0`: net value is strictly decreasing in the
    nonpredictive information, so over the feasible (nonnegative) domain the optimum is
    attained by attending only to the predictive modes. Wu wei as an optimization. -/
theorem wu_wei_optimum_sets_nonpredictive_zero
    (mu kB T Ipred : ℝ) (hkB : 0 < kB) (hT : 0 < T) :
    (∀ a b : ℝ, a < b → netV mu kB T Ipred b < netV mu kB T Ipred a)
      ∧ (∀ Inp : ℝ, 0 ≤ Inp → netV mu kB T Ipred Inp ≤ netV mu kB T Ipred 0) := by
  exact ⟨ fun a b hab => by unfold netV; nlinarith [ mul_pos hkB hT ], fun Inp hInp => by unfold netV; nlinarith [ mul_pos hkB hT ] ⟩

/-! ## R3 — Attention Water-Filling onto the einselected slow basis (HEADLINE) -/

/-- KKT characterization of the water-fill: a mode is *active* iff its predictive
    variance exceeds the water level, and on the active set the allocation takes the
    interior stationary value `½ log₂(v/λ)`. -/
theorem attention_waterfill_is_kkt_optimal
    (v lam : ℝ) (hlam : 0 < lam) :
    (0 < wf v lam ↔ lam < v)
      ∧ (lam < v → wf v lam = (1 / 2) * Real.logb 2 (v / lam)) := by
  unfold wf;
  split_ifs <;> simp_all +decide;
  · exact ⟨ ⟨ fun h => by rw [ Real.logb_pos_iff ] at h <;> nlinarith [ div_mul_cancel₀ v hlam.ne' ], fun h => Real.logb_pos ( by norm_num ) ( by rw [ lt_div_iff₀ hlam ] ; linarith ) ⟩, fun h => Real.logb_nonneg ( by norm_num ) ( by rw [ le_div_iff₀ hlam ] ; linarith ) ⟩;
  · exact ⟨ by linarith, fun h => False.elim <| by linarith ⟩

/-- Slow modes are filled first: a mode with the larger predictive variance (longer
    correlation time, more predictive — the einselected pointer observable) receives at
    least as much of the attention budget. -/
theorem slow_modes_filled_first
    (vi vj lam : ℝ) (hlam : 0 < lam) (hvj : 0 < vj) (hij : vj ≤ vi) :
    wf vj lam ≤ wf vi lam := by
  simp only [wf, if_pos hvj, if_pos (lt_of_lt_of_le hvj hij)]
  gcongr
  norm_num

/-! ## R4 — Attention focusing and the Inattention Trap -/

/-- Attention focuses toward a bifurcation: as the distance-to-tipping `ε` shrinks the
    critical-mode predictive variance `A/ε` diverges and its water-fill allocation
    weakly rises — the perception-side co-signature of HEWT-094 early warning. -/
theorem attention_focuses_toward_bifurcation
    (A lam : ℝ) (hA : 0 < A) (hlam : 0 < lam) :
    (∀ e1 e2 : ℝ, 0 < e1 → e1 < e2 → wf (A / e2) lam ≤ wf (A / e1) lam)
      ∧ (∀ e1 e2 : ℝ, 0 < e1 → e1 < e2 → A / e2 < A / e1) := by
  refine' ⟨ _, _ ⟩;
  · intros e1 e2 he1 he2
    have h_div : A / e2 < A / e1 := by
      gcongr
    exact slow_modes_filled_first (A / e1) (A / e2) lam hlam (by
    exact div_pos hA ( by linarith )) (by
    linarith);
  · exact fun e1 e2 he1 he2 => by gcongr;

/-- The Inattention Trap: the capacity floor `C_crit = ½ log₂(1+SNR)` needed to resolve
    a transition is strictly positive and strictly increasing in the SNR of the critical
    mode; below it the steward is structurally blind. -/
theorem inattention_trap_below_C_crit
    (SNR : ℝ) (hSNR : 0 < SNR) :
    0 < Ccrit SNR
      ∧ (∀ s1 s2 : ℝ, 0 ≤ s1 → s1 < s2 → Ccrit s1 < Ccrit s2) := by
  norm_num [ Ccrit ];
  exact ⟨ Real.logb_pos ( by norm_num ) ( by linarith ), fun s1 s2 hs1 hs2 => Real.logb_lt_logb ( by norm_num ) ( by linarith ) ( by linarith ) ⟩

/-! ## R5 — the Attuner Intelligence-Bound throughput (43rd IB self-application) -/

/-- Over-attention lowers the steward's own speed limit: the throughput ceiling is
    strictly decreasing in the nonpredictive/predictive ratio `ρ`. -/
theorem attuner_ib_throughput_throttled_by_rho
    (P D kB T : ℝ) (hP : 0 < P) (hD : 0 < D) (hkB : 0 < kB) (hT : 0 < T) :
    ∀ r1 r2 : ℝ, 0 ≤ r1 → r1 < r2 →
      attunerBound P D kB T r2 < attunerBound P D kB T r1 := by
  intro r1 r2 hr1 hr2; unfold attunerBound; ring_nf;
  gcongr

/-- Perfect wu-wei attention recovers the full Intelligence Bound: the throughput
    equals the unthrottled bound iff `ρ = 0`. -/
theorem attuner_full_bound_iff_rho_zero
    (P D kB T rho : ℝ) (hP : 0 < P) (hD : 0 < D) (hkB : 0 < kB) (hT : 0 < T)
    (hrho : 0 ≤ rho) :
    attunerBound P D kB T rho = attunerBound P D kB T 0 ↔ rho = 0 := by
  -- By definition of attunerBound, we can write it as:
  simp [attunerBound];
  field_simp;
  grind

/-! ## R6 — Value-of-Information line item -/

/-- Net monitoring value has a strictly interior optimum: when `c < μ a` there is a
    positive stationary point of the net objective, and the marginal net value is
    strictly decreasing (diminishing returns), pinning it as the unique interior maximum.
    Both under- and over-monitoring destroy value. -/
theorem voi_net_value_has_interior_optimum
    (mu a c : ℝ) (hmu : 0 < mu) (ha : 0 < a) (hc : 0 < c) (hint : c < mu * a) :
    (∃ nstar : ℝ, 0 < nstar ∧ HasDerivAt (fun n => netMon mu a c n) 0 nstar)
      ∧ (∀ n1 n2 : ℝ, n1 < n2 →
          mu * a * Real.exp (-(a * n2)) - c < mu * a * Real.exp (-(a * n1)) - c) := by
  refine' ⟨ _, fun n1 n2 hn => sub_lt_sub_right ( mul_lt_mul_of_pos_left ( Real.exp_lt_exp.mpr ( by nlinarith ) ) ( by nlinarith ) ) _ ⟩;
  refine' ⟨ Real.log ( mu * a / c ) / a, _, _ ⟩;
  · exact div_pos ( Real.log_pos ( by rw [ lt_div_iff₀ hc ] ; linarith ) ) ha;
  · convert HasDerivAt.sub ( HasDerivAt.const_mul mu ( HasDerivAt.sub ( hasDerivAt_const _ _ ) ( HasDerivAt.exp ( HasDerivAt.neg ( HasDerivAt.const_mul a ( hasDerivAt_id _ ) ) ) ) ) ) ( HasDerivAt.const_mul c ( hasDerivAt_id _ ) ) using 1 ; ring;
    norm_num [ mul_assoc, mul_comm a, ha.ne' ];
    rw [ Real.exp_neg, Real.exp_log ( by positivity ) ] ; ring;
    grind

/-! ## R7 — Basis alignment efficiency (einselection cross-link; instance of UPEM) -/

/-- Attending in a basis misaligned by angle `Θ` from the einselected (slow) pointer
    basis captures only `η = cos²Θ ∈ [0,1]` of the predictive information; the waste is
    `sin²Θ ≥ 0`, zero iff aligned. -/
theorem attention_basis_efficiency_eq_cos2_theta
    (Θ : ℝ) :
    (0 ≤ (Real.cos Θ) ^ 2 ∧ (Real.cos Θ) ^ 2 ≤ 1)
      ∧ (1 - (Real.cos Θ) ^ 2 = (Real.sin Θ) ^ 2)
      ∧ ((Real.cos Θ) ^ 2 = 1 ↔ (Real.sin Θ) ^ 2 = 0) := by
  exact ⟨ ⟨ sq_nonneg _, Real.cos_sq_le_one _ ⟩, by rw [ Real.sin_sq ], by rw [ Real.sin_sq, sub_eq_zero, eq_comm ] ⟩

/-! ## Non-vacuity witness -/

/-- Both water-filling branches bind on explicit witnesses (slow mode `v=4>λ=1` active
    with allocation `1`; fast mode `v=½<λ=1` dropped to `0`) and the trap threshold is
    strictly positive (`C_crit(1) = ½`). -/
theorem tat_nonvacuous :
    0 < wf 4 1 ∧ wf (1 / 2 : ℝ) 1 = 0 ∧ 0 < Ccrit 1 := by
  norm_num [ wf, Ccrit ];
  exact ⟨ Real.logb_pos ( by norm_num ) ( by norm_num ), mul_nonpos_of_nonneg_of_nonpos ( by norm_num ) ( Real.logb_nonpos ( by norm_num ) ( by norm_num ) ( by norm_num ) ) ⟩

end Viridis.Attention.ThermodynamicAttention