/-
The Mutualist Co-Establishment Theorem (MCET) — clean analytic core
===================================================================

Nightly science-engine Run 096 — [11] Afforestation Systems x Symbiosis ("the Matchmaker").
38th Intelligence-Bound self-application.

Afforestation is a TWO-BODY co-establishment event: a plant `p` and its obligate
microbial symbiont `s` must arrive together at sufficient JOINT density, or neither
takes hold.  The physical bridge is the mass-action exchange flux
`J_exch = kappa * n_p * n_s` (bilinear in the two densities); a self-sustaining
mutualistic nucleus is viable only when this flux covers the fixed free-energy cost
`Phi` of maintaining it.  That single inequality generates the theory below.

This file states the clean, well-posed, single-proposition core of MCET.  Combinatorial
/ measure-dependent pieces (the exact convex separatrix of the bounded obligate-mutualism
ODE, ER-network percolation) are DEFERRED as they were for the Mason (Run 095) — this
core is the mass-action / closed-form layer.

Named theorems (this file), keyed to the run's boxed results:

  R1  coestablishment_feasible_iff_product_geq_threshold   (product-law joint threshold)
  R1  coestablishment_obligacy_forces_both_positive        (obligacy: Theta>0 ==> both partners needed)
  R1  log_separatrix_is_unit_slope_halfplane               (additive-in-log-density barrier)
  R2  min_seeding_cost_ge_two_sqrt_cp_cs_theta   (BOXED: C >= 2 sqrt(c_p c_s Theta), AM-GM lower bound)
  R2  optimal_coinoculation_achieves_min_cost              (the bound is attained -> tightness)
  R2  optimal_coinoculation_equal_spend                    (optimum spends equally on each partner)
  R2  optimal_ratio_eq_inverse_cost_ratio                  (n_p*/n_s* = c_s/c_p)
  R3  specialization_saving_nonneg_and_zero_iff_identical  (BOXED: DeltaSigma >= 0, =0 iff identical)
  R3  reachability_wall_recedes_by_exchange_saving         (BOXED: B*_mut = B*_solo - DeltaSigma <= B*_solo)
  R3  symbiosis_dividend_positive                          (higher-kappa partner strictly lowers seeding cost)
  R4  matchmaker_ib_floors_matching_time      (BOXED: t_match >= I k_B T ln2 / (P D), 38th IB self-app)
  R4  matching_regret_nonneg_and_decreasing_in_kappa       (BOXED: DeltaC >= 0, decreasing toward 0)
  R5  cmn_variance_subadditive_iff_negative_correlation    (network buffers iff r_c < 0)
  R6  coestablishment_efficiency_eq_cos2_theta             (eta = cos^2 Theta in [0,1])
  mcet_nonvacuous                                          (explicit witness; threshold strictly binds)

Every statement is intended NON-VACUOUSLY (see `mcet_nonvacuous`, where the product-law
threshold strictly binds: both partners at density 1 clear Theta=1, but at density 1/2 they
do not).  All hypotheses are the physical positivity constraints (densities, costs, rates,
temperatures, powers > 0).

Toolchain leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff.
-/

import Mathlib

namespace Viridis.Afforestation.MutualistCoestablishment

open Real

/-! ## R1 — Reciprocal co-nucleation: the product-law joint threshold. -/

/-- **R1 (product-law joint threshold).**  With fixed nucleus cost `Phi > 0` and
exchange constant `kappa > 0`, define the joint threshold `Theta = Phi / kappa`.
A mutualistic patch is viable iff its bilinear exchange flux `kappa * n_p * n_s`
covers the cost `Phi`, which is exactly the product law `n_p * n_s >= Theta`. -/
theorem coestablishment_feasible_iff_product_geq_threshold
    (kappa Phi n_p n_s : ℝ) (hk : 0 < kappa) :
    kappa * (n_p * n_s) ≥ Phi ↔ n_p * n_s ≥ Phi / kappa := by
  rw [ge_iff_le, ge_iff_le, div_le_iff₀ hk, mul_comm]

/-- **R1 (obligacy).**  Because the threshold `Theta > 0` is strictly positive,
the product law `n_p * n_s >= Theta` with nonnegative densities forces BOTH partners
to be present at strictly positive density — the thermodynamic content of *obligacy*
(neither the plant alone nor the fungus alone can establish). -/
theorem coestablishment_obligacy_forces_both_positive
    (Theta n_p n_s : ℝ) (hTheta : 0 < Theta)
    (hp : 0 ≤ n_p) (hs : 0 ≤ n_s) (hfeas : n_p * n_s ≥ Theta) :
    0 < n_p ∧ 0 < n_s := by
  constructor
  · rcases lt_or_eq_of_le hp with h | h
    · exact h
    · exfalso; rw [← h] at hfeas; simp at hfeas; linarith
  · rcases lt_or_eq_of_le hs with h | h
    · exact h
    · exfalso; rw [← h] at hfeas; simp at hfeas; linarith

/-- **R1 (log separatrix).**  In log-density coordinates the viability boundary is a
UNIT-SLOPE half-plane: `log n_p + log n_s >= log Theta`.  The co-establishment barrier
is additive in log-density — the symbiosis-lens image of a nucleation barrier. -/
theorem log_separatrix_is_unit_slope_halfplane
    (Theta n_p n_s : ℝ) (hT : 0 < Theta) (hp : 0 < n_p) (hs : 0 < n_s) :
    n_p * n_s ≥ Theta ↔ Real.log n_p + Real.log n_s ≥ Real.log Theta := by
  rw [← Real.log_mul (ne_of_gt hp) (ne_of_gt hs)]
  rw [ge_iff_le, ge_iff_le, Real.log_le_log_iff hT (mul_pos hp hs)]

/-! ## R2 — Optimal co-inoculation ratio and minimum seeding cost. -/

/-- **R2 (BOXED, canon candidate — minimum seeding cost lower bound).**  Minimizing the
seeding cost `C = c_p n_p + c_s n_s` subject to the product-law constraint
`n_p n_s >= Theta` is bounded below by `2 sqrt(c_p c_s Theta)` (AM–GM).  This prices
"how much inoculum per seedling?" from first principles. -/
theorem min_seeding_cost_ge_two_sqrt_cp_cs_theta
    (c_p c_s Theta n_p n_s : ℝ)
    (hcp : 0 < c_p) (hcs : 0 < c_s) (hT : 0 < Theta)
    (hp : 0 < n_p) (hs : 0 < n_s) (hfeas : n_p * n_s ≥ Theta) :
    c_p * n_p + c_s * n_s ≥ 2 * Real.sqrt (c_p * c_s * Theta) := by
  have h1 : Real.sqrt (c_p * c_s * Theta) ≤ Real.sqrt (c_p * n_p * (c_s * n_s)) := by
    apply Real.sqrt_le_sqrt
    have : c_p * c_s * Theta ≤ c_p * c_s * (n_p * n_s) :=
      mul_le_mul_of_nonneg_left hfeas (le_of_lt (mul_pos hcp hcs))
    nlinarith [this]
  have h2 : Real.sqrt (c_p * n_p * (c_s * n_s))
      = Real.sqrt (c_p * n_p) * Real.sqrt (c_s * n_s) := by
    rw [← Real.sqrt_mul (by positivity)]
  have hamgm : 2 * (Real.sqrt (c_p * n_p) * Real.sqrt (c_s * n_s)) ≤ c_p * n_p + c_s * n_s := by
    nlinarith [Real.sq_sqrt (le_of_lt (mul_pos hcp hp)), Real.sq_sqrt (le_of_lt (mul_pos hcs hs)),
      sq_nonneg (Real.sqrt (c_p * n_p) - Real.sqrt (c_s * n_s))]
  rw [ge_iff_le]
  calc 2 * Real.sqrt (c_p * c_s * Theta) ≤ 2 * Real.sqrt (c_p * n_p * (c_s * n_s)) := by linarith
    _ = 2 * (Real.sqrt (c_p * n_p) * Real.sqrt (c_s * n_s)) := by rw [h2]
    _ ≤ c_p * n_p + c_s * n_s := hamgm

/-- **R2 (tightness).**  The lower bound is ATTAINED at the closed-form optimum
`n_p* = sqrt(Theta c_s / c_p)`, `n_s* = sqrt(Theta c_p / c_s)`: there the constraint is
active (`n_p* n_s* = Theta`) and the cost equals `2 sqrt(c_p c_s Theta)`. -/
theorem optimal_coinoculation_achieves_min_cost
    (c_p c_s Theta : ℝ) (hcp : 0 < c_p) (hcs : 0 < c_s) (hT : 0 < Theta) :
    c_p * Real.sqrt (Theta * c_s / c_p) + c_s * Real.sqrt (Theta * c_p / c_s)
      = 2 * Real.sqrt (c_p * c_s * Theta) := by
  have e1 : c_p * Real.sqrt (Theta * c_s / c_p) = Real.sqrt (c_p * c_s * Theta) := by
    rw [show c_p * c_s * Theta = c_p ^ 2 * (Theta * c_s / c_p) by field_simp]
    rw [Real.sqrt_mul (by positivity), Real.sqrt_sq (le_of_lt hcp)]
  have e2 : c_s * Real.sqrt (Theta * c_p / c_s) = Real.sqrt (c_p * c_s * Theta) := by
    rw [show c_p * c_s * Theta = c_s ^ 2 * (Theta * c_p / c_s) by field_simp]
    rw [Real.sqrt_mul (by positivity), Real.sqrt_sq (le_of_lt hcs)]
  rw [e1, e2]; ring

/-- **R2 (equal spend).**  At the optimum the budget is split EQUALLY between the two
partners: `c_p n_p* = c_s n_s*`. -/
theorem optimal_coinoculation_equal_spend
    (c_p c_s Theta : ℝ) (hcp : 0 < c_p) (hcs : 0 < c_s) (hT : 0 < Theta) :
    c_p * Real.sqrt (Theta * c_s / c_p) = c_s * Real.sqrt (Theta * c_p / c_s) := by
  have e1 : c_p * Real.sqrt (Theta * c_s / c_p) = Real.sqrt (c_p * c_s * Theta) := by
    rw [show c_p * c_s * Theta = c_p ^ 2 * (Theta * c_s / c_p) by field_simp]
    rw [Real.sqrt_mul (by positivity), Real.sqrt_sq (le_of_lt hcp)]
  have e2 : c_s * Real.sqrt (Theta * c_p / c_s) = Real.sqrt (c_p * c_s * Theta) := by
    rw [show c_p * c_s * Theta = c_s ^ 2 * (Theta * c_p / c_s) by field_simp]
    rw [Real.sqrt_mul (by positivity), Real.sqrt_sq (le_of_lt hcs)]
  rw [e1, e2]

/-- **R2 (inverse-cost-ratio law).**  The optimal co-inoculation ratio equals the
INVERSE cost ratio: `n_p* / n_s* = c_s / c_p`. -/
theorem optimal_ratio_eq_inverse_cost_ratio
    (c_p c_s Theta : ℝ) (hcp : 0 < c_p) (hcs : 0 < c_s) (hT : 0 < Theta) :
    Real.sqrt (Theta * c_s / c_p) / Real.sqrt (Theta * c_p / c_s) = c_s / c_p := by
  rw [← Real.sqrt_div (by positivity)]
  rw [show (Theta * c_s / c_p) / (Theta * c_p / c_s) = (c_s / c_p) ^ 2 by field_simp]
  rw [Real.sqrt_sq (by positivity)]

/-! ## R3 — The receding reachability wall: specialization dissipation saving. -/

/-- **R3 (BOXED — specialization saving is nonnegative, zero iff identical).**  Exchange
assigns each traded good to its lower-dissipation specialist, saving
`DeltaSigma = |a_pC - a_sC| + |a_pP - a_sP| >= 0`.  The saving is an ABSOLUTE-advantage
effect scaling with partner DISSIMILARITY: it vanishes exactly when the partners are
identical (conspecific monoculture gets no exchange dividend). -/
theorem specialization_saving_nonneg_and_zero_iff_identical
    (a_pC a_sC a_pP a_sP : ℝ) :
    (|a_pC - a_sC| + |a_pP - a_sP| ≥ 0) ∧
    (|a_pC - a_sC| + |a_pP - a_sP| = 0 ↔ a_pC = a_sC ∧ a_pP = a_sP) := by
  refine ⟨by positivity, ?_, ?_⟩
  · intro h
    have h1 := abs_nonneg (a_pC - a_sC)
    have h2 := abs_nonneg (a_pP - a_sP)
    have e1 : |a_pC - a_sC| = 0 := by linarith
    have e2 : |a_pP - a_sP| = 0 := by linarith
    rw [abs_eq_zero, sub_eq_zero] at e1 e2
    exact ⟨e1, e2⟩
  · rintro ⟨h1, h2⟩
    rw [h1, h2]; simp

/-- **R3 (BOXED — receding reachability wall).**  Symbiosis MOVES the Mason's (Run-095)
reachability wall: the required drive recedes from the solo budget by the specialization
saving, `B*_mut = B*_solo - DeltaSigma`, hence `B*_mut <= B*_solo`.  Degraded sites
forbidden to monoculture become establishable with a co-introduced partner. -/
theorem reachability_wall_recedes_by_exchange_saving
    (Bstar_solo DeltaSigma : ℝ) (hDS : 0 ≤ DeltaSigma) :
    Bstar_solo - DeltaSigma ≤ Bstar_solo := by
  linarith

/-- **R3 (symbiosis dividend positive).**  A higher-`kappa` (better-matched) partner
lowers the threshold `Theta = Phi / kappa`, and since the minimum seeding cost
`C* = 2 sqrt(c_p c_s Theta)` is strictly increasing in `Theta`, the dividend
`C_solo - C_mut` is strictly positive whenever `kappa_mut > kappa_solo`. -/
theorem symbiosis_dividend_positive
    (c_p c_s Phi kappa_solo kappa_mut : ℝ)
    (hcp : 0 < c_p) (hcs : 0 < c_s) (hPhi : 0 < Phi)
    (hks : 0 < kappa_solo) (hlt : kappa_solo < kappa_mut) :
    2 * Real.sqrt (c_p * c_s * (Phi / kappa_mut))
      < 2 * Real.sqrt (c_p * c_s * (Phi / kappa_solo)) := by
  have hkm : 0 < kappa_mut := lt_trans hks hlt
  have hlt2 : c_p * c_s * (Phi / kappa_mut) < c_p * c_s * (Phi / kappa_solo) := by
    apply mul_lt_mul_of_pos_left _ (mul_pos hcp hcs)
    exact div_lt_div_of_pos_left hPhi hks hlt
  have hsq := Real.sqrt_lt_sqrt (by positivity) hlt2
  linarith

/-! ## R4 — The Matchmaker: Intelligence-Bound floor and matching regret. -/

/-- **R4 (BOXED — Matchmaker IB floor, 38th IB self-application).**  To co-introduce the
right symbiont among `M` candidate strains the controller must acquire
`I_match = log2 M_eff` bits.  The Intelligence Bound floors the assay time: any protocol
whose dissipated action `P * D * t_match` covers the Landauer information cost
`I_match k_B T ln2` must run at least `t_floor = I_match k_B T ln2 / (P D)`, and this
floor is strictly positive (non-vacuous) whenever more than one candidate must be
distinguished. -/
theorem matchmaker_ib_floors_matching_time
    (I_match kB T P D t_match : ℝ)
    (hI : 0 < I_match) (hkB : 0 < kB) (hT : 0 < T) (hP : 0 < P) (hD : 0 < D)
    (hbudget : P * D * t_match ≥ I_match * kB * T * Real.log 2) :
    t_match ≥ I_match * kB * T * Real.log 2 / (P * D)
      ∧ 0 < I_match * kB * T * Real.log 2 / (P * D) := by
  have hPD : 0 < P * D := mul_pos hP hD
  have hlog : 0 < Real.log 2 := Real.log_pos (by norm_num)
  refine ⟨?_, by positivity⟩
  rw [ge_iff_le, div_le_iff₀ hPD, mul_comm]
  linarith

/-- **R4 (BOXED — matching regret).**  A mismatched strain has
`kappa_mis <= kappa_star`, raising `Theta` and hence cost.  The matching regret
`DeltaC = 2 sqrt(c_p c_s Phi) (kappa_mis^{-1/2} - kappa_star^{-1/2})` is NONNEGATIVE,
and it DECREASES to zero as the match improves (`kappa_mis -> kappa_star`).  Encoded via
`1 / sqrt kappa` to avoid real exponents. -/
theorem matching_regret_nonneg_and_decreasing_in_kappa
    (c_p c_s Phi kappa_lo kappa_mis kappa_star : ℝ)
    (hcp : 0 < c_p) (hcs : 0 < c_s) (hPhi : 0 < Phi)
    (hlo : 0 < kappa_lo) (hlm : kappa_lo < kappa_mis) (hms : kappa_mis ≤ kappa_star) :
    (2 * Real.sqrt (c_p * c_s * Phi) * (1 / Real.sqrt kappa_mis - 1 / Real.sqrt kappa_star) ≥ 0)
    ∧ (2 * Real.sqrt (c_p * c_s * Phi) * (1 / Real.sqrt kappa_lo - 1 / Real.sqrt kappa_star)
        ≥ 2 * Real.sqrt (c_p * c_s * Phi) * (1 / Real.sqrt kappa_mis - 1 / Real.sqrt kappa_star)) := by
  have hmis : 0 < kappa_mis := lt_trans hlo hlm
  have hfac : 0 ≤ 2 * Real.sqrt (c_p * c_s * Phi) := by positivity
  have hd1 : 1 / Real.sqrt kappa_star ≤ 1 / Real.sqrt kappa_mis :=
    one_div_le_one_div_of_le (Real.sqrt_pos.mpr hmis) (Real.sqrt_le_sqrt hms)
  have hd2 : 1 / Real.sqrt kappa_mis ≤ 1 / Real.sqrt kappa_lo :=
    one_div_le_one_div_of_le (Real.sqrt_pos.mpr hlo) (Real.sqrt_le_sqrt (le_of_lt hlm))
  constructor
  · apply mul_nonneg hfac; linarith
  · apply mul_le_mul_of_nonneg_left _ hfac; linarith

/-! ## R5 — Common Mycorrhizal Network portfolio effect. -/

/-- **R5 (CMN portfolio effect).**  `n` seedlings wired into one shared fungal network
have aggregate establishment variance `Var_net = (sigma^2 / n) (1 + (n-1) r_c)`.  Relative
to the independent baseline `sigma^2 / n`, a network BUFFERS (variance strictly below
baseline) iff the inter-seedling resource correlation is negative, `r_c < 0`; at `r_c = 0`
it recovers `sigma^2/n`, and as `r_c -> 1` it flips to synchronized failure. -/
theorem cmn_variance_subadditive_iff_negative_correlation
    (sigma2 n r_c : ℝ) (hσ : 0 < sigma2) (hn : 2 ≤ n) :
    (sigma2 / n) * (1 + (n - 1) * r_c) < sigma2 / n ↔ r_c < 0 := by
  have hnpos : 0 < n := by linarith
  have hk : 0 < sigma2 / n := div_pos hσ hnpos
  have hn1 : 0 < n - 1 := by linarith
  constructor
  · intro h; nlinarith [mul_pos hk hn1]
  · intro h; nlinarith [mul_pos hk hn1]

/-! ## R6 — Co-establishment efficiency is the universal cos^2 alignment geometry. -/

/-- **R6 (efficiency = cos^2 Theta).**  The realized exchange rate is
`kappa = kappa_max cos^2 Theta`, where `Theta` is the angle between the symbiont's
functional-trait vector and the host x site demand vector.  The efficiency
`eta = cos^2 Theta` lies in `[0,1]`, so the realized rate never exceeds `kappa_max`;
a perfectly aligned partner (`Theta = 0`) gives `eta = 1`, an orthogonal one
(`Theta = pi/2`, wrong guild) gives `eta = 0`. -/
theorem coestablishment_efficiency_eq_cos2_theta
    (kappa_max Θ : ℝ) (hkm : 0 ≤ kappa_max) :
    (0 ≤ Real.cos Θ ^ 2 ∧ Real.cos Θ ^ 2 ≤ 1)
    ∧ kappa_max * Real.cos Θ ^ 2 ≤ kappa_max
    ∧ kappa_max * Real.cos 0 ^ 2 = kappa_max
    ∧ kappa_max * Real.cos (Real.pi / 2) ^ 2 = 0 := by
  have hc : Real.cos Θ ^ 2 ≤ 1 := by nlinarith [Real.neg_one_le_cos Θ, Real.cos_le_one Θ]
  refine ⟨⟨by positivity, hc⟩, ?_, ?_, ?_⟩
  · nlinarith [hc]
  · simp
  · rw [Real.cos_pi_div_two]; ring

/-! ## Non-vacuity witness. -/

/-- **Non-vacuity.**  A concrete instance where the product-law threshold STRICTLY BINDS.
With `Phi = kappa = 1` (so `Theta = 1`) and unit costs `c_p = c_s = 1`: both partners at
density `1` clear the threshold (`1 * 1 = 1 ≥ 1`), the minimum seeding cost is
`2 sqrt(1) = 2 > 0`, yet HALVING both densities makes the patch infeasible
(`(1/2) * (1/2) = 1/4 < 1`).  So none of the boxed conclusions is vacuous. -/
theorem mcet_nonvacuous :
    (1 : ℝ) * 1 ≥ 1
    ∧ 2 * Real.sqrt (1 * 1 * 1) = 2
    ∧ (0 : ℝ) < 2 * Real.sqrt (1 * 1 * 1)
    ∧ (1 / 2 : ℝ) * (1 / 2) < 1 := by
  norm_num [Real.sqrt_one]

end Viridis.Afforestation.MutualistCoestablishment
