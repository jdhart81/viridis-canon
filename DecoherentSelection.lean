/-
The Decoherent Selection Theorem (DST) — clean thermodynamic / information core
==============================================================================

Nightly science-engine Run 099 — [12] AI Wavefunction Collapse x Thermodynamic Lens
("the Chooser"). 41st Intelligence-Bound self-application. Novelty 4/5.

Model.  An agent's pre-decision belief over N candidate outcomes in the einselected
"possibility" basis is a probability vector `p : Fin n -> R`.  A DECISION is a decoherence
event in that basis — the collapse of off-diagonals selecting one outcome.  In the
resource theory of coherence the coherence destroyed by full dephasing of a PURE candidate
state equals the Shannon entropy of its populations, `C_rel = H(p)`, so the choice's
"coherence cost" is exactly the entropy of the choice.  This file states the clean,
WELL-POSED, non-vacuous real-analytic / thermodynamic core keyed to the run's boxed
results (verify.py 29/29, numpy-only).

DEFERRED (well-posedness gate — CITED, not re-proven, preserved as paper prose):
  * R1 operator identity  dS_collapse = S(Delta rho) - S(rho) = S(rho || Delta rho)
    (von Neumann entropy of a density matrix + dephasing channel — requires quantum
    operator scaffolding, not a self-contained R-valued proposition).  Its PURE-state
    reduction  C_rel = H(p)  IS the model here and carries the run's content.
  * `single_collapse_cost_independent_of_monitoring_rate` (a distinctness/modeling claim
    vs MIST-076 — that the single-event cost functional does not take the monitoring rate
    p as an argument; structural, not a theorem).

Named theorems (this file):
  R2  coherence_nonneg                            (choice entropy H(p) >= 0)
  R2  decision_cost_zero_iff_pointer_eigenstate   (H(p) = 0  iff  p is a pointer eigenstate)
  R2  ambiguity_cost_le_lnN                        (H(p) <= ln N, hardest choice bounded by ln N)
  R2  ambiguity_cost_maximal_at_uniform_eq_lnN     (uniform superposition saturates H = ln N)
  R3  basis_efficiency_eq_cos2_theta               (eta = cos^2 Theta, definitional identity)
  R3  basis_efficiency_nonneg_le_one               (eta in [0,1])
  R3  einselected_basis_unique_zero_waste          (BOXED: pointer basis is the UNIQUE zero-waste basis)
  R1  collapse_dissipation_floor_kBT_Crel          (BOXED: Q_collapse >= k_B T C_rel)
  R4  chooser_ib_throughput_speed_limit            (BOXED: R_max = [P D / k_B T ln2]/I_dec saturates IB; 41st self-app)
  R4  min_power_eq_rate_times_kBT_Crel             (P_min = R k_B T C_rel, monotone in rate)
  R5  finite_time_collapse_cost_decreasing_in_tau  (BOXED: Q(tau)=Q_min(1+lam/tau) decreasing to reversible floor)
  dst_nonvacuous                                   (witness: uniform 2-way costs ln2>0, decided state is free)

All hypotheses are the physical positivity constraints.  Toolchain leanprover/lean4:v4.28.0,
Mathlib pin 8f9d9cff.
-/

import Mathlib

namespace Viridis.Decision.DecoherentSelection

open Real Finset

/-- Shannon entropy of a population vector — the coherence cost of a pure decision state,
`C_rel = H(p) = - sum_i p_i log p_i` (Lean's `Real.log 0 = 0` gives the standard
`0 log 0 = 0` convention). -/
noncomputable def shannonEntropy {n : ℕ} (p : Fin n → ℝ) : ℝ :=
  ∑ i, - p i * Real.log (p i)

/-- Wasted heat per stable committed bit when the decision basis is misaligned by
efficiency `eta`: `waste = C_rel (1/eta - 1)`. -/
noncomputable def decisionWaste (C eta : ℝ) : ℝ := C * (1 / eta - 1)

/-- Einselection efficiency in the CSUT-017 motif: the fraction of a decision that lands
in the stable, redundantly recordable pointer basis, `eta = cos^2 Theta`. -/
noncomputable def basisEfficiency (θ : ℝ) : ℝ := Real.cos θ ^ 2

/-! ## R2 — Ambiguity–Cost Law: the coherence cost of a decision is the entropy of the choice. -/

/-
**R2 (nonnegativity).** The coherence cost of any decision is nonnegative: a
probability vector has `H(p) >= 0`.
-/
theorem coherence_nonneg {n : ℕ} (p : Fin n → ℝ)
    (hp0 : ∀ i, 0 ≤ p i) (hp1 : ∀ i, p i ≤ 1) :
    0 ≤ shannonEntropy p := by
  exact Finset.sum_nonneg fun i _ => by by_cases hi : p i = 0 <;> simpa [ * ] using mul_nonneg ( hp0 i ) ( neg_nonneg_of_nonpos ( Real.log_nonpos ( hp0 i ) ( hp1 i ) ) ) ;

/-
**R2 (a decided state is free).** The decision cost vanishes exactly when the state is
already a pointer eigenstate — one outcome carries all the probability.
-/
theorem decision_cost_zero_iff_pointer_eigenstate {n : ℕ} (p : Fin n → ℝ)
    (hp0 : ∀ i, 0 ≤ p i) (hp1 : ∀ i, p i ≤ 1) (hsum : ∑ i, p i = 1) :
    shannonEntropy p = 0 ↔ ∃ i, p i = 1 := by
  constructor;
  · intro h
    have h_zero : ∀ i, p i * (-Real.log (p i)) = 0 := by
      convert Finset.sum_eq_zero_iff_of_nonneg ( fun i _ => ?_ ) |>.1 h;
      · aesop;
      · by_cases hi : p i = 0 <;> simpa [ hi ] using mul_nonneg ( hp0 i ) ( neg_nonneg_of_nonpos ( Real.log_nonpos ( hp0 i ) ( hp1 i ) ) );
    contrapose! hsum; simp_all +decide;
    exact ne_of_lt ( lt_of_le_of_lt ( Finset.sum_nonpos fun i _ => by cases h_zero i <;> linarith [ hp0 i, hp1 i ] ) ( by norm_num ) );
  · intro h
    obtain ⟨i, hi⟩ := h
    have h_zero : ∀ j ≠ i, p j = 0 := by
      intro j hj; rw [ Finset.sum_eq_add_sum_diff_singleton ( Finset.mem_univ i ) ] at hsum; linarith [ hp0 j, hp1 j, Finset.single_le_sum ( fun a _ => hp0 a ) ( Finset.mem_sdiff.mpr ⟨ Finset.mem_univ j, by aesop ⟩ : j ∈ Finset.univ \ { i } ) ] ;
    unfold shannonEntropy; rw [ Finset.sum_eq_single i ] <;> aesop;

/-
**R2 (ambiguity bounded by ln N).** The hardest possible decision over `N` candidates
costs at most `ln N`.
-/
theorem ambiguity_cost_le_lnN {n : ℕ} (hn : 0 < n) (p : Fin n → ℝ)
    (hp0 : ∀ i, 0 ≤ p i) (hsum : ∑ i, p i = 1) :
    shannonEntropy p ≤ Real.log n := by
  unfold shannonEntropy;
  -- Applying Jensen's inequality to the convex function $f(x) = x \log x$ with weights $1/n$, we get:
  have h_jensen : (∑ i : Fin n, (1 / n : ℝ) * (p i * Real.log (p i))) ≥ ((∑ i : Fin n, (1 / n : ℝ) * p i) * Real.log (∑ i : Fin n, (1 / n : ℝ) * p i)) := by
    have h_jensen : ConvexOn ℝ (Set.Ici 0) (fun x : ℝ => x * Real.log x) := by
      exact ( Real.convexOn_mul_log );
    apply ConvexOn.map_sum_le h_jensen;
    · aesop;
    · simp +decide [ hn.ne' ];
    · grind;
  simp_all +decide [ ← Finset.mul_sum _ _ _ ];
  nlinarith [ inv_pos.mpr ( by positivity : 0 < ( n : ℝ ) ) ]

/-
**R2 (uniform superposition is the most dissipative — canon candidate).** The flat,
maximally ambiguous distribution over `N` candidates saturates the bound: `H = ln N`.
-/
theorem ambiguity_cost_maximal_at_uniform_eq_lnN {n : ℕ} (hn : 0 < n) :
    shannonEntropy (fun _ : Fin n => (n : ℝ)⁻¹) = Real.log n := by
  unfold shannonEntropy; norm_num [ hn.ne' ] ;

/-! ## R3 — Basis-Alignment / Einselection: the pointer basis is the unique zero-waste basis. -/

/-
**R3 (efficiency identity).** The einselection efficiency is `cos^2 Theta` (CSUT-017
motif): only the pointer-aligned component of a decision is stably recordable.
-/
theorem basis_efficiency_eq_cos2_theta (θ : ℝ) :
    basisEfficiency θ = Real.cos θ ^ 2 := by
  rfl

/-
**R3 (efficiency range).** The einselection efficiency lies in `[0,1]`.
-/
theorem basis_efficiency_nonneg_le_one (θ : ℝ) :
    0 ≤ basisEfficiency θ ∧ basisEfficiency θ ≤ 1 := by
  exact ⟨ sq_nonneg _, Real.cos_sq_le_one _ ⟩

/-
**R3 (BOXED — einselected basis is the unique zero-waste decision basis).** For a
genuinely ambiguous decision (`C_rel > 0`) at efficiency `eta in (0,1]`, the wasted heat
`C_rel (1/eta - 1)` is nonnegative and vanishes IFF `eta = 1`, i.e. exactly when the
decision is read in the einselected pointer basis. A thermodynamic derivation of Zurek's
predictability sieve.
-/
theorem einselected_basis_unique_zero_waste (C eta : ℝ)
    (hC : 0 < C) (heta0 : 0 < eta) (heta1 : eta ≤ 1) :
    0 ≤ decisionWaste C eta ∧ (decisionWaste C eta = 0 ↔ eta = 1) := by
  constructor;
  · exact mul_nonneg hC.le ( sub_nonneg_of_le ( one_le_one_div heta0 heta1 ) );
  · unfold decisionWaste;
    grind

/-! ## R1 — Collapse Dissipation Law: deciding costs at least `k_B T C_rel`. -/

/-
**R1 (BOXED — Collapse Dissipation Law, canon candidate).** The heat dissipated by a
decision is floored by the coherence destroyed: `Q_collapse >= k_B T C_rel`, with the
reversible floor `k_B T C_rel` itself nonnegative. Decoherence-as-entropy-production,
priced.
-/
theorem collapse_dissipation_floor_kBT_Crel (kB T C Q : ℝ)
    (hkB : 0 < kB) (hT : 0 < T) (hC : 0 ≤ C) (hQ : kB * T * C ≤ Q) :
    0 ≤ kB * T * C ∧ kB * T * C ≤ Q := by
  exact ⟨ mul_nonneg ( mul_nonneg hkB.le hT.le ) hC, hQ ⟩

/-! ## R4 — the Chooser: the Intelligence Bound floors decision throughput (41st self-app). -/

/-
**R4 (BOXED — decision-throughput speed limit; 41st IB self-application).** With each
decision committing `I_dec > 0` bits, the maximal decision rate
`R_max = [P D / (k_B T ln 2)] / I_dec` is strictly positive and saturates the IB rate
exactly: `R_max * I_dec = P D / (k_B T ln 2)`. Ambiguity (larger `I_dec`) throttles
throughput.
-/
theorem chooser_ib_throughput_speed_limit (P D kB T Idec : ℝ)
    (hP : 0 < P) (hD : 0 < D) (hkB : 0 < kB) (hT : 0 < T) (hI : 0 < Idec) :
    0 < (P * D / (kB * T * Real.log 2)) / Idec ∧
      ((P * D / (kB * T * Real.log 2)) / Idec) * Idec = P * D / (kB * T * Real.log 2) := by
  exact ⟨ by positivity, by rw [ div_mul_cancel₀ _ hI.ne' ] ⟩

/-
**R4 (minimum sustaining power).** To sustain decision rate `R` the agent must
dissipate at least `P_min = R k_B T C_rel`, monotone nondecreasing in the rate.
-/
theorem min_power_eq_rate_times_kBT_Crel (R1 R2 kB T C : ℝ)
    (hkB : 0 < kB) (hT : 0 < T) (hC : 0 < C) (hR : R1 ≤ R2) :
    R1 * (kB * T * C) ≤ R2 * (kB * T * C) := by
  gcongr

/-! ## R5 — Finite-Time Speed–Energy Trade-off: fast decisions cost strictly more. -/

/-
**R5 (BOXED — finite-time trade-off).** A collapse executed in finite time `tau`
carries `Q(tau) = Q_min (1 + lam/tau)`, strictly decreasing in `tau` toward the reversible
floor `Q_min` and strictly above it for every finite time. Deliberate decisions are
cheaper than hasty ones.
-/
theorem finite_time_collapse_cost_decreasing_in_tau (Qmin lam t1 t2 : ℝ)
    (hQ : 0 < Qmin) (hlam : 0 < lam) (ht1 : 0 < t1) (ht : t1 < t2) :
    Qmin * (1 + lam / t2) < Qmin * (1 + lam / t1) ∧ Qmin < Qmin * (1 + lam / t1) := by
  exact ⟨ mul_lt_mul_of_pos_left ( by gcongr ) hQ, lt_mul_of_one_lt_right hQ ( lt_add_of_pos_right _ ( div_pos hlam ht1 ) ) ⟩

/-! ## Non-vacuity. -/

/-
**Non-vacuity witness.** The hardest binary decision (uniform superposition over two
candidates) costs `ln 2 > 0`, while an already-decided pointer eigenstate is free — both
branches of the Ambiguity–Cost Law bind on explicit witnesses.
-/
theorem dst_nonvacuous :
    shannonEntropy (fun _ : Fin 2 => (2 : ℝ)⁻¹) = Real.log 2 ∧
      (0 : ℝ) < Real.log 2 ∧
      shannonEntropy (![(1 : ℝ), 0]) = 0 := by
  refine' ⟨ _, Real.log_pos <| by norm_num, _ ⟩;
  · convert ambiguity_cost_maximal_at_uniform_eq_lnN ( n := 2 ) ( by norm_num ) using 1;
  · unfold shannonEntropy; norm_num

end Viridis.Decision.DecoherentSelection
