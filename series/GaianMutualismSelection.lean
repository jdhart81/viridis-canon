/-
# The Gaian Mutualism Selection Theorem (GMST) — the Symbiont
Viridis Aristotle Forge · Nightly Run 104 · [07] Gaian Systems × 🌿 Symbiosis
46th Intelligence-Bound self-application. Role tower: Steward@102 → Metronome@103 → the Symbiont@104.

INTENDED MEANING (formalized clean core).
The fifty-year-old Doolittle/Dawkins objection to Gaia — natural selection acts on
individual organisms, not on planets — is resolved by reading the biota and its abiotic
environment as MUTUALISTIC PARTNERS stabilized by partner-fidelity feedback (PFF). A
single control parameter, the FIDELITY COEFFICIENT `ρ_f ∈ [0,1]` (the fraction of the
environmental benefit a lineage generates that returns privately to that same lineage),
dials continuously between two rival paradigms: individually-selectable "Darwinian Gaia"
(high `ρ_f`) and unselectable, survivorship-filtered "dice-playing Gaia" / selection-by-
survival (low `ρ_f`). Its ceiling is set thermodynamically by the Intelligence Bound.

The clean core (formalized here; all seven were numerically verified 35/35 in the source
verify.py, numpy-only):

  R1  Fidelity decomposition & critical fidelity. selGrad(ρ_f) = ρ_f·b − c vanishes at
      the CRITICAL FIDELITY ρ_f⋆ = c/b; individual selection favours regulation iff ρ_f > ρ_f⋆.
  R2  (HEADLINE, canon candidate) Fidelity–Survival Bifurcation. ρ_f⋆ = c/b is a
      transcritical threshold; the regulating fixed point x=1 exchanges stability there.
  R3  (canon candidate) Landauer Fidelity Ceiling. ρ_f ≤ ρ_f^max = 1 − exp(−I_sus),
      I_sus = P_fid/(k_B T ln2 · κ_mix); ceiling in [0,1), non-increasing in κ_mix; fast
      mixing forbids Darwinian Gaia.
  R4  The Gaian Externality. r_priv(ρ_f)=ρ_f/(s+ρ_f) < r_soc=1/(s+1) for ρ_f<1, equal at 1;
      the gap ΔG is strictly decreasing in ρ_f and closes at ρ_f=1.
  R5  Fidelity biases the dice. Waiting time 1/p(ρ_f) strictly decreasing in ρ_f.
  R6  Reciprocity-Daisyworld (clean monotone surrogate): regulates iff q>0; bandwidth
      strictly increasing in q.
  R7  the Symbiont (46th IB self-application). D_mut(ρ_f)=D_B+D_E+ρ_f·√(D_B D_E): strictly
      increasing in ρ_f, additive baseline at 0, surplus AM–GM-capped; IB ceiling rises with ρ_f.

NON-VACUITY. gmst_nonvacuous binds explicit witnesses (b=2,c=1 ⇒ ρ_f⋆=1/2; gradient>0 at
ρ_f=3/4; Landauer ceiling interior at I_sus=1; r_priv(1/2)<r_soc at s=1; D_mut strictly rising).

DEFERRED (well-posedness gate — CITED, not re-proven, matching the source paper's own honest
disclosure): the full Watson–Lovelock two-daisy ODE simulation (R6 formalized via its verified
monotone surrogate metrics) and the empirical bandwidth integers — both established in the
source verify.py by direct numerical integration, not closed form.

Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real Set Filter

namespace Viridis.Gaian.GaianMutualismSelection

/-! ### R1 — Fidelity decomposition & critical fidelity. -/

/-- Individual-selection gradient on a regulating trait: private return `ρ_f·b`, cost `c`. -/
def selGrad (rho b c : ℝ) : ℝ := rho * b - c

/-- Critical fidelity `ρ_f⋆ = c/b`. -/
noncomputable def rhoStar (b c : ℝ) : ℝ := c / b

/-- **R1.** The selection gradient vanishes exactly at the critical fidelity `ρ_f⋆ = c/b`. -/
theorem critical_fidelity_eq_c_over_b (b c : ℝ) (hb : 0 < b) :
    selGrad (rhoStar b c) b c = 0 := by
  unfold rhoStar selGrad; norm_num [ hb.ne' ] ;

/-- **R1.** Individual selection favours regulation iff fidelity exceeds `ρ_f⋆ = c/b`. -/
theorem regulation_selected_iff_rho_f_gt_critical (rho b c : ℝ) (hb : 0 < b) :
    0 < selGrad rho b c ↔ rhoStar b c < rho := by
  unfold selGrad; unfold rhoStar; constructor <;> intro h <;> rw [ div_lt_iff₀ hb ] at * <;> linarith;

/-! ### R2 — Fidelity–Survival Bifurcation (HEADLINE, canon candidate). -/

/-- Linearized stability eigenvalue of the regulating fixed point `x=1`:
    `stabEig(ρ_f) = c − ρ_f·b` (negative ⇒ stable ⇒ "Darwinian Gaia"). -/
def stabEig (rho b c : ℝ) : ℝ := c - rho * b

/-- **R2 (HEADLINE, canon candidate).** `ρ_f⋆ = c/b` is a transcritical threshold: the
    stability eigenvalue vanishes there and crosses zero transversally (strictly antitone
    in `ρ_f`, nonzero speed `−b`) — the exchange of stability separating Darwinian Gaia
    from dice-playing Gaia. -/
theorem fidelity_survival_transcritical_at_c_over_b (b c : ℝ) (hb : 0 < b) :
    stabEig (rhoStar b c) b c = 0 ∧ StrictAnti (fun rho => stabEig rho b c) := by
  exact ⟨ by unfold rhoStar stabEig; rw [ div_mul_cancel₀ _ hb.ne' ] ; ring, fun x y hxy => by unfold stabEig; nlinarith ⟩

/-- **R2.** The regulating fixed point `x=1` is stable iff fidelity exceeds `ρ_f⋆ = c/b`. -/
theorem x1_stable_iff_rho_f_gt_critical (rho b c : ℝ) (hb : 0 < b) :
    stabEig rho b c < 0 ↔ rhoStar b c < rho := by
  constructor <;> intro <;> unfold stabEig rhoStar at * <;> nlinarith [ mul_div_cancel₀ c hb.ne' ] ;

/-! ### R3 — Landauer Fidelity Ceiling (canon candidate). -/

/-- Sustained mutual-information cost in bits: `I_sus = P_fid /(k_B T ln2 · κ_mix)`. -/
noncomputable def Isus (Pfid kBTln2 kappa : ℝ) : ℝ := Pfid / (kBTln2 * kappa)

/-- Landauer fidelity ceiling `ρ_f^max = 1 − exp(−I_sus)`. -/
noncomputable def rhoMax (I : ℝ) : ℝ := 1 - Real.exp (-I)

/-- **R3 (canon candidate).** The Landauer fidelity ceiling lies in `[0,1)` for any
    nonnegative sustained-information budget `I_sus ≥ 0`. -/
theorem landauer_fidelity_ceiling_one_minus_exp (I : ℝ) (hI : 0 ≤ I) :
    0 ≤ rhoMax I ∧ rhoMax I < 1 := by
  exact ⟨ sub_nonneg.2 <| Real.exp_le_one_iff.2 <| by linarith, sub_lt_self _ <| Real.exp_pos _ ⟩

/-- **R3.** The ceiling is non-increasing in the mixing rate `κ_mix` (honest non-increasing
    form — saturates at `1` in the slow-mixing limit). -/
theorem rho_max_nonincreasing_in_mixing_rate (Pfid kBTln2 : ℝ)
    (hP : 0 ≤ Pfid) (hK : 0 < kBTln2) :
    AntitoneOn (fun kappa => rhoMax (Isus Pfid kBTln2 kappa)) (Set.Ioi 0) := by
  intros kappa1 hkappa1 kappa2 hkappa2 hkappa;
  exact sub_le_sub_left ( Real.exp_le_exp.mpr <| neg_le_neg <| div_le_div_of_nonneg_left ( by positivity ) ( by nlinarith [ Set.mem_Ioi.mp hkappa1, Set.mem_Ioi.mp hkappa2 ] ) <| by nlinarith [ Set.mem_Ioi.mp hkappa1, Set.mem_Ioi.mp hkappa2 ] ) _

/-- **R3 (consequence).** In the fast-mixing limit the affordable fidelity falls below the
    critical threshold `ρ_f⋆ = c/b`: there is a mixing rate above which Darwinian Gaia is
    thermodynamically FORBIDDEN and regulation must rely on selection-by-survival. -/
theorem fast_mixing_forbids_darwinian_gaia (Pfid kBTln2 b c : ℝ)
    (hP : 0 < Pfid) (hK : 0 < kBTln2) (hb : 0 < b) (hc : 0 < c) (hcb : c < b) :
    ∃ kappa : ℝ, 0 < kappa ∧ rhoMax (Isus Pfid kBTln2 kappa) < rhoStar b c := by
  use 2 * Pfid * b / (kBTln2 * c)
  constructor
  · positivity
  have hI :
      Isus Pfid kBTln2 (2 * Pfid * b / (kBTln2 * c)) = c / (2 * b) := by
    unfold Isus
    field_simp
  rw [hI]
  have hSmall : c / (2 * b) < rhoStar b c := by
    unfold rhoStar
    rw [div_lt_div_iff₀ (by positivity : (0 : ℝ) < 2 * b) hb]
    nlinarith [hcb]
  have hn : -(c / (2 * b)) ≠ 0 :=
    neg_ne_zero.mpr (div_ne_zero hc.ne' (by positivity))
  have hExp : rhoMax (c / (2 * b)) < c / (2 * b) := by
    unfold rhoMax
    nlinarith [Real.add_one_lt_exp hn]
  exact hExp.trans hSmall

/-! ### R4 — The Gaian Externality. -/

/-- Planetarily-optimal regulation effort `r_soc = 1/(s+1)` (linear-quadratic model). -/
noncomputable def rSoc (s : ℝ) : ℝ := 1 / (s + 1)

/-- Privately-optimal regulation effort `r_priv(ρ_f) = ρ_f/(s+ρ_f)`. -/
noncomputable def rPriv (rho s : ℝ) : ℝ := rho / (s + rho)

/-- **R4.** Private regulation under-shoots the planetary optimum for every fidelity below
    full: `r_priv(ρ_f) < r_soc` whenever `0 < ρ_f < 1`. -/
theorem r_priv_lt_r_soc_for_rho_f_lt_one (rho s : ℝ)
    (hs : 0 < s) (hr0 : 0 < rho) (hr1 : rho < 1) :
    rPriv rho s < rSoc s := by
  rw [ rPriv, rSoc, div_lt_div_iff₀ ] <;> nlinarith

/-- **R4.** The externality gap `ΔG(ρ_f) = r_soc − r_priv(ρ_f)` closes at `ρ_f = 1` and is
    strictly decreasing in `ρ_f`. -/
theorem gaian_externality_gap_monotone_closes_at_one (s : ℝ) (hs : 0 < s) :
    (rSoc s - rPriv 1 s = 0) ∧
      StrictAntiOn (fun rho => rSoc s - rPriv rho s) (Set.Ioi 0) := by
  unfold rSoc rPriv;
  norm_num [ StrictAntiOn ];
  intro a ha b hb hab; rw [ div_lt_div_iff₀ ] <;> nlinarith;

/-! ### R5 — Fidelity biases the dice (PFF ↔ SBS continuum). -/

/-- Expected sequential-selection waiting time `1/p(ρ_f)`, `p(ρ_f)=p₀+(1−p₀)·ρ_f`. -/
noncomputable def waitingTime (p0 rho : ℝ) : ℝ := 1 / (p0 + (1 - p0) * rho)

/-- **R5.** The expected waiting time strictly decreases with fidelity on `[0,1]`. -/
theorem sbs_waiting_time_decreasing_in_fidelity (p0 : ℝ) (h0 : 0 < p0) (h1 : p0 < 1) :
    StrictAntiOn (fun rho => waitingTime p0 rho) (Set.Icc (0 : ℝ) 1) := by
  intros x hx y hy hxy;
  exact one_div_lt_one_div_of_lt ( by nlinarith [ hx.1, hx.2 ] ) ( by nlinarith [ hy.1, hy.2 ] )

/-! ### R6 — Reciprocity-Daisyworld (clean monotone surrogate). -/

/-- Variance-reduction (regulation effectiveness) surrogate `q/(1+q)`. -/
noncomputable def varReduction (q : ℝ) : ℝ := q / (1 + q)

/-- Regulation bandwidth surrogate `Bmax·q/(1+q)`. -/
noncomputable def bandwidth (Bmax q : ℝ) : ℝ := Bmax * (q / (1 + q))

/-- **R6.** Replicator-only regulation occurs iff local-heating fidelity is positive:
    `varReduction q > 0 ↔ q > 0` (for `q ≥ 0`). -/
theorem daisyworld_regulates_iff_fidelity_positive (q : ℝ) (hq : 0 ≤ q) :
    0 < varReduction q ↔ 0 < q := by
  unfold varReduction; rw [ lt_div_iff₀ ] ; aesop;
  linarith

/-- **R6.** The regulation bandwidth is strictly increasing in fidelity on `q ≥ 0`. -/
theorem bandwidth_monotone_in_fidelity (Bmax : ℝ) (hB : 0 < Bmax) :
    StrictMonoOn (fun q => bandwidth Bmax q) (Set.Ici (0 : ℝ)) := by
  intro x hx y hy hxy;
  exact mul_lt_mul_of_pos_left ( by rw [ div_lt_div_iff₀ ] <;> linarith [ hx.out, hy.out ] ) hB

/-! ### R7 — the Symbiont (46th IB self-application). -/

/-- Fidelity-weighted joint dissipative structure `D_mut(ρ_f)=D_B+D_E+ρ_f·√(D_B D_E)`. -/
noncomputable def Dmut (DB DE rho : ℝ) : ℝ := DB + DE + rho * Real.sqrt (DB * DE)

/-- **R7.** `D_mut` is strictly increasing in fidelity, reduces to the additive baseline at
    `ρ_f=0`, and the surplus coefficient is AM–GM-capped: `√(D_B D_E) ≤ (D_B+D_E)/2`. -/
theorem D_mut_monotone_and_am_gm_capped (DB DE : ℝ) (hB : 0 < DB) (hE : 0 < DE) :
    StrictMonoOn (fun rho => Dmut DB DE rho) (Set.Ici (0 : ℝ))
      ∧ Dmut DB DE 0 = DB + DE
      ∧ Real.sqrt (DB * DE) ≤ (DB + DE) / 2 := by
  unfold StrictMonoOn Dmut;
  exact ⟨ fun a ha b hb hab => by norm_num; nlinarith [ Real.sqrt_pos.2 ( mul_pos hB hE ) ], by ring, Real.sqrt_le_iff.2 ⟨ by positivity, by linarith [ sq_nonneg ( DB - DE ) ] ⟩ ⟩

/-- **R7 (the Symbiont).** The mutualism's IB regulatory ceiling `P·D_mut(ρ_f)/(k_B T ln2)`
    strictly increases with fidelity. -/
theorem symbiont_ib_self_application (P DB DE kT : ℝ)
    (hP : 0 < P) (hkT : 0 < kT) (hB : 0 < DB) (hE : 0 < DE) :
    StrictMonoOn (fun rho => P * Dmut DB DE rho / kT) (Set.Ici (0 : ℝ)) := by
  norm_num [ StrictMonoOn ];
  unfold Dmut; intros; gcongr;

/-! ### Non-vacuity witness. -/

/-- **Non-vacuity.** Explicit witnesses show none of the laws is vacuous. -/
theorem gmst_nonvacuous :
    rhoStar 2 1 = 1 / 2
      ∧ 0 < selGrad (3 / 4) 2 1
      ∧ (0 ≤ rhoMax 1 ∧ rhoMax 1 < 1)
      ∧ rPriv (1 / 2) 1 < rSoc 1
      ∧ Dmut 1 1 0 < Dmut 1 1 1 := by
  unfold rhoStar selGrad rhoMax rPriv rSoc Dmut; norm_num;
  positivity

end Viridis.Gaian.GaianMutualismSelection
