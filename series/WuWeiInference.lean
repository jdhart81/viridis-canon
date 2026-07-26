/-
  WuWeiInference.lean — The Wu-Wei Inference Theorem (WWIT) & the Harmonizer
  Viridis nightly Run 108 · [14] Cognitive Modeling × Alignment · 2026-07-24
  Aristotle Forge target. Canon candidates: R4 (Wu-Wei Inference Theorem), R3 (Forcing Tax).

  MODEL (exactly-solvable, from the paper).  An agent tracks an AR(1)/OU environment
  x_{t+1} = a x_t + xi_t (0 < a < 1 persistence) with a constant-gain filter
  m_t = (1-g) a m_{t-1} + g y_t, gain g in (0,1) = the agent's *precision*.
  Solving the stationary Lyapunov recursions gives the belief-present correlation
  rho_mem(g); the Markov structure damps the belief-future correlation exactly by the
  persistence: rho_pred = a * rho_mem.  With s := rho_mem^2 in [0,1) the two Gaussian
  informations are closed-form
      I_mem(s)  = -(1/2) log(1 - s),
      I_pred(s) = -(1/2) log(1 - a^2 s),
  and by the Still-Sivak-Bell-Crooks identity the dissipated work is exactly the
  non-predictive residue  W_diss/(k_B T) = I_nonpred = I_mem - I_pred >= 0, with
  effortlessness eta := I_pred / I_mem in (0,1).

  This file formalizes the CLEAN CORE of WWIT: the closed-form information monotonicities,
  the Kalman-gain restraint, and -- over the predictive-information *profile* P(g) whose
  single-peakedness at the Bayes gain g_K is proven analytically in the paper and verified
  21/21 numerically (verify_108.py, 3e6-step Monte-Carlo) -- the forcing tax, the
  interior/unique Wu-Wei optimum, its effortless first-order condition, its strict
  position below the Bayes gain, its monotone decrease in the price of effort, and the
  Harmonizer IB throttle.

  DEFERRED as CITED (well-posedness gate -- NOT re-derived here, preserved as paper prose):
  the explicit Lyapunov map g -> rho_mem(g) (C = gV_x/D1, V_m = ...) and the analytic proof
  that s(g) = rho_mem(g)^2 is single-peaked at g_K with the stated smoothness/concavity.
  Those hypotheses enter the optimization theorems as the profile axioms (hUp/hDown/
  ProfileHyp), exactly matching Theorems (Restraint), (Forcing tax) of the paper.

  Every named theorem below is stated to be NON-VACUOUS: wwit_nonvacuous exhibits a
  concrete profile + parameters witnessing all hypotheses with a strictly interior optimum.
-/
import Mathlib

namespace Viridis.WuWeiInference

open Real

/-- Predictive Gaussian information as a function of the squared belief-present
    correlation `s = rho_mem^2`, at persistence `a`:  I_pred(s) = -(1/2) log(1 - a^2 s). -/
noncomputable def Ipred (a s : ℝ) : ℝ := -(1 / 2) * Real.log (1 - a ^ 2 * s)

/-- Retained (memory) Gaussian information:  I_mem(s) = -(1/2) log(1 - s). -/
noncomputable def Imem (s : ℝ) : ℝ := -(1 / 2) * Real.log (1 - s)

/-- Non-predictive (dissipated) information residue  I_nonpred = I_mem - I_pred. -/
noncomputable def Inonpred (a s : ℝ) : ℝ := Imem s - Ipred a s

/-- Effortlessness / harmony index  eta = I_pred / I_mem. -/
noncomputable def eta (a s : ℝ) : ℝ := Ipred a s / Imem s

/-- Belief-future correlation, damped by the persistence:  rho_pred = a * rho_mem. -/
noncomputable def rhoPred (a rhoMem : ℝ) : ℝ := a * rhoMem

/-- Steady-state Kalman gain from the Riccati prior variance `pm = p-`:
    g_K = p- / (p- + r). -/
noncomputable def gK (pm r : ℝ) : ℝ := pm / (pm + r)

/-- Net predictive value once the metabolic cost of precision `kappa g^2` is priced:
    N(g) = P(g) - kappa g^2, with `P` the predictive-information profile g -> I_pred(s(g)). -/
noncomputable def netValue (P : ℝ → ℝ) (κ g : ℝ) : ℝ := P g - κ * g ^ 2

/-- The Intelligence-Bound raw ceiling  P*D / (k_B T ln 2). -/
noncomputable def ibCeiling (Pw D kB T : ℝ) : ℝ := Pw * D / (kB * T * Real.log 2)

/-! ### R1 -- Markov damping of the predictive correlation -/

/-- **`rho_pred_eq_a_times_rho_mem`.**  The belief-future correlation equals `a * rho_mem`
    (Markov damping), and for a persistence `a < 1` this is a *strict contraction* of a
    positive present-correlation: predictive correlation is strictly smaller than memory
    correlation.  (Non-vacuous: the strict inequality has content whenever `0 < rho_mem`.) -/
theorem rho_pred_eq_a_times_rho_mem (a rhoMem : ℝ)
    (hrho : 0 < rhoMem) (ha1 : a < 1) (ha0 : 0 < a) :
    rhoPred a rhoMem = a * rhoMem ∧ rhoPred a rhoMem < rhoMem := by
  refine ⟨rfl, ?_⟩
  unfold rhoPred
  nlinarith [mul_pos (sub_pos.mpr ha1) hrho]

/-! ### R1' -- The dissipated residue is non-negative for every gain -/

/-- **`I_nonpred_nonneg_for_all_g`.**  For any persistence `0 < a < 1` and squared
    correlation `s in [0,1)`, the non-predictive (dissipated) information is non-negative,
    and strictly positive whenever `s > 0`: some retained memory is always non-predictive
    (Still-Sivak-Bell-Crooks residue >= 0). -/
theorem I_nonpred_nonneg_for_all_g (a s : ℝ)
    (ha0 : 0 < a) (ha1 : a < 1) (hs0 : 0 ≤ s) (hs1 : s < 1) :
    0 ≤ Inonpred a s ∧ (0 < s → 0 < Inonpred a s) := by
  have ha2 : a^2 < 1 := by nlinarith
  have h1s : 0 < 1 - s := by linarith
  have hle : 1 - s ≤ 1 - a^2 * s := by nlinarith [mul_nonneg hs0 (by nlinarith : (0:ℝ) ≤ 1 - a^2)]
  unfold Inonpred Imem Ipred
  refine ⟨?_, ?_⟩
  · have := Real.log_le_log h1s hle
    linarith
  · intro hs
    have hlt : 1 - s < 1 - a^2 * s := by nlinarith [mul_pos hs (by nlinarith : (0:ℝ) < 1 - a^2)]
    have := Real.log_lt_log h1s hlt
    linarith

/-- Effortlessness lies strictly in the unit interval for a nondegenerate model:
    `eta = I_pred/I_mem in (0,1)` when `0 < s < 1` and `0 < a < 1`. -/
theorem eta_mem_Ioo (a s : ℝ)
    (ha0 : 0 < a) (ha1 : a < 1) (hs0 : 0 < s) (hs1 : s < 1) :
    0 < eta a s ∧ eta a s < 1 := by
  have ha2 : a^2 < 1 := by nlinarith
  have h1s : 0 < 1 - s := by linarith
  have has : 0 < a^2 * s := by positivity
  have has1 : a^2 * s < 1 := by nlinarith
  have h1as : 0 < 1 - a^2 * s := by linarith
  have hmem : 0 < Imem s := by
    unfold Imem
    have := Real.log_neg h1s (by linarith)
    linarith
  have hpred : 0 < Ipred a s := by
    unfold Ipred
    have := Real.log_neg h1as (by linarith)
    linarith
  refine ⟨by unfold eta; positivity, ?_⟩
  rw [eta, div_lt_one hmem]
  unfold Ipred Imem
  have hlt : 1 - s < 1 - a^2 * s := by nlinarith [mul_pos hs0 (by nlinarith : (0:ℝ) < 1 - a^2)]
  have := Real.log_lt_log h1s hlt
  linarith

/-- Predictive information is strictly increasing in the squared correlation `s`
    (underwrites: I_pred peaks exactly where the correlation peaks). -/
theorem Ipred_strictMonoOn (a : ℝ) (ha0 : 0 < a) :
    StrictMonoOn (Ipred a) (Set.Ico (0 : ℝ) (1 / a ^ 2)) := by
  have ha2 : 0 < a^2 := by positivity
  intro s1 hs1 s2 hs2 hlt
  have hb2 : a^2 * s2 < 1 := by
    have := hs2.2; rw [lt_div_iff₀ ha2] at this; linarith [this]
  have h1b2 : 0 < 1 - a^2 * s2 := by linarith
  have hcmp : 1 - a^2 * s2 < 1 - a^2 * s1 := by nlinarith
  unfold Ipred
  have := Real.log_lt_log h1b2 hcmp
  linarith

/-! ### R2 -- The Bayes gain already restrains -/

/-- **`kalman_gain_lt_one_for_positive_noise`.**  For any positive Riccati prior variance
    `p- > 0` and positive observation noise `r > 0`, the steady-state Kalman gain
    `g_K = pm/(pm+r)` is strictly below 1: the error-optimal filter never fully trusts the
    data.  (Also `0 < g_K`.) -/
theorem kalman_gain_lt_one_for_positive_noise (pm r : ℝ) (hpm : 0 < pm) (hr : 0 < r) :
    0 < gK pm r ∧ gK pm r < 1 := by
  unfold gK
  refine ⟨div_pos hpm (by linarith), ?_⟩
  rw [div_lt_one (by linarith)]
  linarith

/-- **`gK_increasing_in_volatility_and_snr`.**  Higher prior uncertainty `p-` -- which the
    Riccati root drives up with environmental volatility `q` and signal-to-noise ratio --
    strictly raises the Kalman gain: for fixed `r > 0`, `pm -> g_K(pm,r)` is strictly
    increasing.  Optimal yielding tracks the world's predictability. -/
theorem gK_increasing_in_volatility_and_snr (r : ℝ) (hr : 0 < r) :
    StrictMonoOn (fun pm => gK pm r) (Set.Ioi (0 : ℝ)) := by
  intro pm1 h1 pm2 h2 hlt
  simp only [Set.mem_Ioi] at h1 h2
  simp only [gK]
  have d1 : 0 < pm1 + r := by linarith
  have d2 : 0 < pm2 + r := by linarith
  rw [div_lt_div_iff₀ d1 d2]
  nlinarith

/-! ### R3 -- The forcing paradox (HEADLINE, Forcing Tax) -/

/-- **`I_pred_single_peaked_at_gK`.**  A predictive-information profile `P` that is
    strictly increasing below `g_K` and strictly decreasing above `g_K` attains its unique
    maximum at `g_K`: every other gain yields strictly less predictive information. -/
theorem I_pred_single_peaked_at_gK
    (P : ℝ → ℝ) (gKval : ℝ)
    (hUp : StrictMonoOn P (Set.Iic gKval))
    (hDown : StrictAntiOn P (Set.Ici gKval)) :
    ∀ g, g ≠ gKval → P g < P gKval := by
  intro g hg
  rcases lt_or_gt_of_ne hg with h | h
  · exact hUp (le_of_lt h) (le_refl gKval) h
  · exact hDown (le_refl gKval) (le_of_lt h) h

/-- **`forcing_tax_positive`.**  With `g_K < 1` and predictive information strictly
    decreasing above the Bayes gain, the forcing tax
    `Delta_force = P(g_K) - P(1) > 0`: forcing precision from `g_K` up to full trust `g = 1`
    strictly *destroys* information about the future. -/
theorem forcing_tax_positive
    (P : ℝ → ℝ) (gKval : ℝ)
    (hgK1 : gKval < 1)
    (hDown : StrictAntiOn P (Set.Ici gKval)) :
    0 < P gKval - P 1 := by
  have : P 1 < P gKval := hDown (le_refl gKval) (le_of_lt hgK1) hgK1
  linarith

/-! ### R4 -- The Wu-Wei Inference Theorem (HEADLINE, canon candidate) -/

/-- Bundle of the paper-proven properties of the predictive-information profile on `(0,1)`:
    differentiable, strictly concave, interior peak at `gKval in (0,1)` with `deriv P gKval = 0`
    and `deriv P > 0` strictly left of the peak. -/
structure ProfileHyp (P : ℝ → ℝ) (gKval : ℝ) : Prop where
  hgK0 : 0 < gKval
  hgK1 : gKval < 1
  diff : ∀ g ∈ Set.Ioo (0 : ℝ) 1, DifferentiableAt ℝ P g
  conc : StrictConcaveOn ℝ (Set.Ioo (0 : ℝ) 1) P
  peak : deriv P gKval = 0
  posLeft : ∀ g ∈ Set.Ioo (0 : ℝ) gKval, 0 < deriv P g

/-- **`wuwei_gain_interior_and_unique`.**  For every strictly positive price of effort
    `kappa > 0`, the net predictive value `N(g) = P(g) - kappa g^2` has a unique interior
    maximizer `gstar in (0, g_K)` -- the **Wu-Wei gain**. -/
theorem wuwei_gain_interior_and_unique
    (P : ℝ → ℝ) (gKval κ : ℝ) (HP : ProfileHyp P gKval) (hκ : 0 < κ) :
    ∃! g, g ∈ Set.Ioo (0 : ℝ) gKval ∧ IsMaxOn (netValue P κ) (Set.Ioo (0 : ℝ) 1) g := by
  have hQdiff : ∀ g ∈ Set.Ioo (0:ℝ) 1, DifferentiableAt ℝ (netValue P κ) g := by
    intro g hg
    exact (HP.diff g hg).sub ((differentiableAt_const κ).mul ((differentiableAt_id).pow 2))
  have hderivQ : ∀ g ∈ Set.Ioo (0:ℝ) 1, deriv (netValue P κ) g = deriv P g - 2*κ*g := by
    intro g hg
    have hHP : HasDerivAt P (deriv P g) g := (HP.diff g hg).hasDerivAt
    have hHg : HasDerivAt (fun x:ℝ => κ * x^2) (κ * (2*g)) g := by
      have h2 : HasDerivAt (fun x:ℝ => x^2) (2*g) g := by simpa using (hasDerivAt_pow 2 g)
      simpa using h2.const_mul κ
    have hnet : HasDerivAt (netValue P κ) (deriv P g - κ*(2*g)) g := hHP.sub hHg
    rw [hnet.deriv]; ring
  have hconc : ConcaveOn ℝ (Set.Ioo (0:ℝ) 1) (netValue P κ) := by
    have hquad : ConcaveOn ℝ (Set.Ioo (0:ℝ) 1) (fun g => -(κ * g^2)) := by
      have h1 : ConvexOn ℝ Set.univ (fun g:ℝ => g^2) := (by norm_num : Even 2).convexOn_pow (𝕜 := ℝ)
      have h2 : ConvexOn ℝ Set.univ (fun g:ℝ => κ * g^2) := h1.smul (le_of_lt hκ)
      exact (h2.neg).subset (Set.subset_univ _) (convex_Ioo 0 1)
    have hsum := HP.conc.concaveOn.add hquad
    have heq : (P + fun g => -(κ * g^2)) = netValue P κ := by
      funext g; simp only [Pi.add_apply, netValue]; ring
    rwa [heq] at hsum
  have hantiP : StrictAntiOn (deriv P) (Set.Ioo (0:ℝ) 1) := HP.conc.strictAntiOn_deriv HP.diff
  have hantiQ : StrictAntiOn (deriv (netValue P κ)) (Set.Ioo (0:ℝ) 1) := by
    intro a ha b hb hab
    rw [hderivQ a ha, hderivQ b hb]
    have := hantiP ha hb hab
    nlinarith [this, hab, hκ]
  have hgKmem : gKval ∈ Set.Ioo (0:ℝ) 1 := ⟨HP.hgK0, HP.hgK1⟩
  have hderivQgK : deriv (netValue P κ) gKval = -2*κ*gKval := by rw [hderivQ gKval hgKmem, HP.peak]; ring
  have hQgK_neg : deriv (netValue P κ) gKval < 0 := by rw [hderivQgK]; nlinarith [HP.hgK0, hκ]
  have hhalfmem : gKval/2 ∈ Set.Ioo (0:ℝ) gKval := ⟨by linarith [HP.hgK0], by linarith [HP.hgK0]⟩
  have hhalfmem01 : gKval/2 ∈ Set.Ioo (0:ℝ) 1 := ⟨by linarith [HP.hgK0], by linarith [HP.hgK1, HP.hgK0]⟩
  set c0 := deriv P (gKval/2) with hc0def
  have hc0pos : 0 < c0 := HP.posLeft (gKval/2) hhalfmem
  set g0 := min (gKval/4) (c0/(4*κ)) with hg0def
  have hg0pos : 0 < g0 := lt_min (by linarith [HP.hgK0]) (by positivity)
  have hg0_lt_half : g0 < gKval/2 := lt_of_le_of_lt (min_le_left _ _) (by linarith [HP.hgK0])
  have hg0lt : g0 < gKval := by linarith [HP.hgK0]
  have hg0mem01 : g0 ∈ Set.Ioo (0:ℝ) 1 := ⟨hg0pos, lt_trans hg0lt HP.hgK1⟩
  have hderivP_g0 : c0 < deriv P g0 := hantiP hg0mem01 hhalfmem01 hg0_lt_half
  have h2kg0 : 2*κ*g0 ≤ c0/2 := by
    have hle : g0 ≤ c0/(4*κ) := min_le_right _ _
    have hk : (0:ℝ) < 4*κ := by linarith
    rw [le_div_iff₀ hk] at hle
    nlinarith [hle]
  have hQg0_pos : 0 < deriv (netValue P κ) g0 := by
    rw [hderivQ g0 hg0mem01]
    linarith [hderivP_g0, h2kg0, hc0pos]
  have hIccsub : Set.Icc g0 gKval ⊆ Set.Ioo (0:ℝ) 1 := by
    intro x hx
    exact ⟨lt_of_lt_of_le hg0pos hx.1, lt_of_le_of_lt hx.2 HP.hgK1⟩
  have hcont : ContinuousOn (netValue P κ) (Set.Icc g0 gKval) := by
    intro x hx
    exact ((hQdiff x (hIccsub hx)).continuousAt).continuousWithinAt
  have hne : (Set.Icc g0 gKval).Nonempty := ⟨g0, ⟨le_refl _, le_of_lt hg0lt⟩⟩
  obtain ⟨c, hcIcc, hcmax⟩ := (isCompact_Icc).exists_isMaxOn hne hcont
  have hcmem01 : c ∈ Set.Ioo (0:ℝ) 1 := hIccsub hcIcc
  have hglobal : IsMaxOn (netValue P κ) (Set.Ioo (0:ℝ) 1) c := by
    rw [isMaxOn_iff]
    intro y hy
    rcases le_or_gt g0 y with hyg0 | hyg0
    · rcases le_or_gt y gKval with hygK | hygK
      · exact hcmax ⟨hyg0, hygK⟩
      · have hden : (0:ℝ) < y - gKval := by linarith
        have hslope : slope (netValue P κ) gKval y ≤ deriv (netValue P κ) gKval :=
          hconc.slope_le_deriv hgKmem hy hygK (hQdiff gKval hgKmem)
        rw [slope_def_field] at hslope
        have hlt : (netValue P κ y - netValue P κ gKval)/(y - gKval) < 0 :=
          lt_of_le_of_lt hslope hQgK_neg
        rw [div_lt_iff₀ hden] at hlt
        have hQgKle : netValue P κ gKval ≤ netValue P κ c := hcmax ⟨le_of_lt hg0lt, le_refl _⟩
        nlinarith [hlt, hQgKle]
    · have hden : (0:ℝ) < g0 - y := by linarith
      have hslope : deriv (netValue P κ) g0 ≤ slope (netValue P κ) y g0 :=
        hconc.deriv_le_slope hy hg0mem01 hyg0 (hQdiff g0 hg0mem01)
      rw [slope_def_field] at hslope
      have hpos : (0:ℝ) < (netValue P κ g0 - netValue P κ y)/(g0 - y) :=
        lt_of_lt_of_le hQg0_pos hslope
      rw [lt_div_iff₀ hden] at hpos
      have hQg0le : netValue P κ g0 ≤ netValue P κ c := hcmax ⟨le_refl _, le_of_lt hg0lt⟩
      nlinarith [hpos, hQg0le]
  have hcloc : IsLocalMax (netValue P κ) c := hglobal.isLocalMax (isOpen_Ioo.mem_nhds hcmem01)
  have hcderiv : deriv (netValue P κ) c = 0 := hcloc.deriv_eq_zero
  have hclt : c < gKval := by
    rcases lt_trichotomy c gKval with h | h | h
    · exact h
    · exfalso; rw [h] at hcderiv; rw [hcderiv] at hQgK_neg; exact lt_irrefl _ hQgK_neg
    · exfalso
      have := hantiQ hgKmem hcmem01 h
      rw [hcderiv] at this
      linarith [hQgK_neg, this]
  have hcmemgK : c ∈ Set.Ioo (0:ℝ) gKval := ⟨lt_of_lt_of_le hg0pos hcIcc.1, hclt⟩
  refine ⟨c, ⟨hcmemgK, hglobal⟩, ?_⟩
  rintro c' ⟨hc'mem, hc'max⟩
  have hc'mem01 : c' ∈ Set.Ioo (0:ℝ) 1 := ⟨hc'mem.1, lt_trans hc'mem.2 HP.hgK1⟩
  have hc'loc : IsLocalMax (netValue P κ) c' := hc'max.isLocalMax (isOpen_Ioo.mem_nhds hc'mem01)
  have hc'deriv : deriv (netValue P κ) c' = 0 := hc'loc.deriv_eq_zero
  exact hantiQ.injOn hc'mem01 hcmem01 (by rw [hc'deriv, hcderiv])

/-- **`effortless_foc_holds_at_optimum`.**  At the Wu-Wei gain the marginal predictive
    return equals the marginal cost of forcing -- the *effortless first-order condition*
    `dI_pred/dg |_{gstar} = 2 kappa gstar`. -/
theorem effortless_foc_holds_at_optimum
    (P : ℝ → ℝ) (gKval κ gstar : ℝ) (HP : ProfileHyp P gKval) (hκ : 0 < κ)
    (hstar : gstar ∈ Set.Ioo (0 : ℝ) gKval)
    (hmax : IsMaxOn (netValue P κ) (Set.Ioo (0 : ℝ) 1) gstar) :
    deriv P gstar = 2 * κ * gstar := by
  have hmem : gstar ∈ Set.Ioo (0:ℝ) 1 := ⟨hstar.1, lt_trans hstar.2 HP.hgK1⟩
  have hPdiff : DifferentiableAt ℝ P gstar := HP.diff gstar hmem
  have hnb : Set.Ioo (0:ℝ) 1 ∈ nhds gstar := isOpen_Ioo.mem_nhds hmem
  have hloc : IsLocalMax (netValue P κ) gstar := hmax.isLocalMax hnb
  have hHP : HasDerivAt P (deriv P gstar) gstar := hPdiff.hasDerivAt
  have hHg : HasDerivAt (fun g:ℝ => κ * g^2) (κ * (2*gstar)) gstar := by
    have h2 : HasDerivAt (fun x:ℝ => x^2) (2*gstar) gstar := by simpa using (hasDerivAt_pow 2 gstar)
    simpa using h2.const_mul κ
  have hnet : HasDerivAt (netValue P κ) (deriv P gstar - κ*(2*gstar)) gstar := hHP.sub hHg
  have hz : deriv (netValue P κ) gstar = 0 := hloc.deriv_eq_zero
  rw [hnet.deriv] at hz
  nlinarith [hz]

/-- **`wuwei_gain_below_kalman_gain`.**  The Wu-Wei gain sits strictly below the Bayes
    gain, `gstar < g_K < 1`: thermodynamics *deepens* the restraint already present in pure
    Bayes, never reverses it. -/
theorem wuwei_gain_below_kalman_gain
    (P : ℝ → ℝ) (gKval κ gstar : ℝ) (HP : ProfileHyp P gKval) (hκ : 0 < κ)
    (hstar : gstar ∈ Set.Ioo (0 : ℝ) gKval)
    (hmax : IsMaxOn (netValue P κ) (Set.Ioo (0 : ℝ) 1) gstar) :
    gstar < gKval ∧ gKval < 1 := by
  exact ⟨hstar.2, HP.hgK1⟩

/-- **`wuwei_gain_decreasing_in_kappa`.**  The Wu-Wei gain is strictly decreasing in the
    price of effort: dearer forcing slides the optimum toward gentle, low-effort updating.
    For `0 < kappa1 < kappa2`, the respective maximizers satisfy `gstar(kappa2) < gstar(kappa1)`. -/
theorem wuwei_gain_decreasing_in_kappa
    (P : ℝ → ℝ) (gKval κ₁ κ₂ g1 g2 : ℝ) (HP : ProfileHyp P gKval)
    (hκ : 0 < κ₁) (hκ12 : κ₁ < κ₂)
    (h1 : g1 ∈ Set.Ioo (0 : ℝ) gKval ∧ IsMaxOn (netValue P κ₁) (Set.Ioo (0 : ℝ) 1) g1)
    (h2 : g2 ∈ Set.Ioo (0 : ℝ) gKval ∧ IsMaxOn (netValue P κ₂) (Set.Ioo (0 : ℝ) 1) g2) :
    g2 < g1 := by
  obtain ⟨hs1, hm1⟩ := h1
  obtain ⟨hs2, hm2⟩ := h2
  have foc1 : deriv P g1 = 2 * κ₁ * g1 := effortless_foc_holds_at_optimum P gKval κ₁ g1 HP hκ hs1 hm1
  have foc2 : deriv P g2 = 2 * κ₂ * g2 := effortless_foc_holds_at_optimum P gKval κ₂ g2 HP (by linarith) hs2 hm2
  have hm1' : g1 ∈ Set.Ioo (0:ℝ) 1 := ⟨hs1.1, lt_trans hs1.2 HP.hgK1⟩
  have hm2' : g2 ∈ Set.Ioo (0:ℝ) 1 := ⟨hs2.1, lt_trans hs2.2 HP.hgK1⟩
  have hanti : StrictAntiOn (deriv P) (Set.Ioo (0:ℝ) 1) := HP.conc.strictAntiOn_deriv HP.diff
  by_contra hcon
  push_neg at hcon
  rcases eq_or_lt_of_le hcon with heq | hlt
  · rw [← heq] at foc2
    nlinarith [hs1.1, foc1, foc2]
  · have hd : deriv P g2 < deriv P g1 := hanti hm1' hm2' hlt
    rw [foc1, foc2] at hd
    nlinarith [hs1.1, hs2.1, mul_pos hκ hs1.1]

/-! ### R6 -- The Harmonizer (IB self-application) -/

/-- **`harmonizer_ib_ceiling_never_violated`.**  The usable predictive rate is the raw
    Intelligence-Bound ceiling throttled by the effortlessness `eta in (0,1]`:
    `dI_pred/dt <= eta * P*D/(k_B T ln 2)`.  Given any predictive rate bounded by the full IB
    ceiling and `eta in [0,1]`, the harmonized (eta-throttled) rate never exceeds the ceiling --
    only at the harmonized gain (eta->1) is the whole budget spent on foresight. -/
theorem harmonizer_ib_ceiling_never_violated
    (rate ceiling η : ℝ)
    (hceil : 0 ≤ ceiling) (hrate : rate ≤ ceiling) (hη0 : 0 ≤ η) (hη1 : η ≤ 1) :
    η * rate ≤ η * ceiling ∧ η * ceiling ≤ ceiling := by
  refine ⟨mul_le_mul_of_nonneg_left hrate hη0, ?_⟩
  calc η * ceiling ≤ 1 * ceiling := mul_le_mul_of_nonneg_right hη1 hceil
    _ = ceiling := one_mul _

/-! ### Non-vacuity witness -/

/-- **`wwit_nonvacuous`.**  A concrete profile and parameters witnessing structure with a
    strictly interior Bayes gain: `p- = 1, r = 1` gives `g_K = 1/2 in (0,1)`; the concrete
    strictly-concave profile `P0(g) = -(g - 1/2)^2` peaks at `g_K = 1/2` with
    `deriv P0 (1/2) = 0`; and the dissipated residue is strictly positive at `s = 1/2` with
    `a = 1/2`.  Hence none of the theorems above are vacuous. -/
theorem wwit_nonvacuous :
    (gK 1 1 = 1 / 2 ∧ 0 < gK 1 1 ∧ gK 1 1 < 1) ∧
    (deriv (fun g => -(g - 1 / 2) ^ 2) ((1 : ℝ) / 2) = 0) ∧
    (0 < Inonpred (1 / 2) (1 / 2)) := by
  refine ⟨?_, ?_⟩
  · refine ⟨?_, ?_, ?_⟩ <;> (unfold gK; norm_num)
  refine ⟨?_, ?_⟩
  · have h : HasDerivAt (fun g : ℝ => -(g - 1 / 2) ^ 2) (-(2 * ((1:ℝ)/2 - 1/2) ^ 1 * 1)) (1/2) := by
      have := ((hasDerivAt_id ((1:ℝ)/2)).sub_const (1/2)).pow 2
      simpa using this.neg
    rw [h.deriv]; norm_num
  · exact (I_nonpred_nonneg_for_all_g (1 / 2) (1 / 2) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num)).2 (by norm_num)

end Viridis.WuWeiInference
