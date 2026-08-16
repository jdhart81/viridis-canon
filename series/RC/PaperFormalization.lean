import Mathlib

/-!
# Run-128 — "The Reciprocity Corridor: A Bilateral-Benefit Test for Directional
Information Exchange" (J. D. Hart, 12 August 2026) — Lean formalization

This file formalizes the four frozen `FORMAL_TARGET` claims of `STATEMENT_CONTRACT.md`
(paper Theorems 1–3 and Corollary 1), together with the auxiliary share-coordinate
target `share_coordinate_corridor_equivalence` listed in
`SEALED_CLAIM_INVENTORY.json → proposed_lean_targets`.

Everything below is stated over the real numbers under the paper's explicit standing
assumptions (Section 2 of the paper):

* one period, two partners `X` and `Y`;
* strictly positive directional flows `x = TE(X→Y) > 0`, `y = TE(Y→X) > 0`;
* strictly positive, known, constant coefficients `vX, cX, vY, cY > 0`;
* linear separable payoffs with zero disagreement utilities,
  `uX = vX*y - cX*x` and `uY = vY*x - cY*y`;
* no externalities.

Only the algebraic content of the paper is formalized. The Gaussian measurement layer
(paper Section 5, claim `C5`) is explicitly *not* a formal target of the contract
(`formal_status = NOT_A_NEW_FORMAL_CLAIM`), and the numerical/control claims
`C6`–`C9` are not formal targets either; see `BLOCKERS.md` for the audit.

Toolchain: `leanprover/lean4:v4.28.0`;
mathlib revision: see `MATHLIB_REVISION.txt` / `lake-manifest.json`.
-/

namespace Viridis.Run128.PaperFormalization

/-! ## Definitions (paper Section 2 and Section 4) -/

/-- Payoff of partner `X`: value of imported flow `y` minus effective cost of the
exported flow `x`.  Paper Eq. (1). -/
def uX (vX cX x y : ℝ) : ℝ := vX * y - cX * x

/-- Payoff of partner `Y`: value of imported flow `x` minus effective cost of the
exported flow `y`.  Paper Eq. (1). -/
def uY (vY cY x y : ℝ) : ℝ := vY * x - cY * y

/-- Strict bilateral benefit: both partners are strictly better off. -/
def BilateralBenefit (vX cX vY cY x y : ℝ) : Prop :=
  0 < uX vX cX x y ∧ 0 < uY vY cY x y

/-- The (open) reciprocity ratio corridor of paper Eq. (2): the flow ratio `y/x`
lies strictly between `cX/vX` and `vY/cY`. -/
def InCorridor (vX cX vY cY x y : ℝ) : Prop :=
  cX / vX < y / x ∧ y / x < vY / cY

/-- Lower zero-payoff share boundary `q_L = cX/(vX+cX)`.  Paper Eq. (3). -/
noncomputable def qL (vX cX : ℝ) : ℝ := cX / (vX + cX)

/-- Upper zero-payoff share boundary `q_U = vY/(vY+cY)`.  Paper Eq. (3). -/
noncomputable def qU (vY cY : ℝ) : ℝ := vY / (vY + cY)

/-- Payoff of `X` in share coordinates: total flow `R = x + y`, share `q = y/R`,
so `x = R(1-q)` and `y = Rq`.  Paper Section 4. -/
def uXshare (vX cX R q : ℝ) : ℝ := uX vX cX (R * (1 - q)) (R * q)

/-- Payoff of `Y` in share coordinates. -/
def uYshare (vY cY R q : ℝ) : ℝ := uY vY cY (R * (1 - q)) (R * q)

/-- The symmetric Nash product `uX * uY` at fixed total flow `R` and share `q`
(disagreement utilities are zero). -/
def nashProduct (vX cX vY cY R q : ℝ) : ℝ :=
  uXshare vX cX R q * uYshare vY cY R q

/-- The paper's product feasibility condition `cX cY < vX vY`.  Paper Eq. (4). -/
def ProductCondition (vX cX vY cY : ℝ) : Prop := cX * cY < vX * vY

/-! ## C1 — Theorem 1 (Bilateral-benefit corridor) -/

/-- **C1 / paper Theorem 1.**  For strictly positive flows and coefficients, both
payoffs of Eq. (1) are strictly positive if and only if the flow ratio lies in the
reciprocity corridor `cX/vX < y/x < vY/cY`.

All six positivity hypotheses of the paper's statement are retained verbatim; the
proof in fact only needs `hx`, `hvX` and `hcY`, so `hy`, `hvY`, `hcX` are kept purely
for faithfulness to the frozen statement. -/
theorem bilateral_benefit_iff_reciprocity_corridor
    {x y vX vY cX cY : ℝ} (hx : 0 < x) (hy : 0 < y)
    (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    BilateralBenefit vX cX vY cY x y ↔ InCorridor vX cX vY cY x y := by
  have h1 : (0 < uX vX cX x y) ↔ cX / vX < y / x := by
    rw [div_lt_div_iff₀ hvX hx]
    constructor
    · intro h
      simp only [uX] at h
      nlinarith
    · intro h
      simp only [uX]
      nlinarith
  have h2 : (0 < uY vY cY x y) ↔ y / x < vY / cY := by
    rw [div_lt_div_iff₀ hx hcY]
    constructor
    · intro h
      simp only [uY] at h
      nlinarith
    · intro h
      simp only [uY]
      nlinarith
  exact and_congr h1 h2

/-! ## C2 — Theorem 2 (Strict feasibility) -/

/-- Supporting lemma (not one of the frozen targets): the ratio interval
`(cX/vX, vY/cY)` is nonempty iff `cX cY < vX vY`.  Only positivity of `vX` and `cY`
is needed here. -/
theorem ratio_interval_nonempty_iff_product_condition
    {vX vY cX cY : ℝ} (hvX : 0 < vX) (hcY : 0 < cY) :
    (∃ r : ℝ, cX / vX < r ∧ r < vY / cY) ↔ ProductCondition vX cX vY cY := by
  constructor
  · rintro ⟨r, h1, h2⟩
    have : cX / vX < vY / cY := lt_trans h1 h2
    rw [div_lt_div_iff₀ hvX hcY] at this
    simpa [ProductCondition, mul_comm] using this
  · intro h
    have hlt : cX / vX < vY / cY := by
      rw [div_lt_div_iff₀ hvX hcY]
      simpa [mul_comm] using h
    exact ⟨(cX / vX + vY / cY) / 2, by linarith, by linarith⟩

/-- **C2 / paper Theorem 2.**  The open reciprocity corridor is nonempty — i.e. there
exist strictly positive flows `x, y` whose ratio lies in it — if and only if the product
of import values exceeds the product of export costs, `cX cY < vX vY`.

The paper's four coefficient positivity hypotheses are kept verbatim; `hvY` is not
needed by the proof. -/
theorem strict_corridor_nonempty_iff_product_condition
    {vX vY cX cY : ℝ} (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    (∃ x y : ℝ, 0 < x ∧ 0 < y ∧ InCorridor vX cX vY cY x y)
      ↔ ProductCondition vX cX vY cY := by
  constructor
  · rintro ⟨x, y, _, _, h1, h2⟩
    exact (ratio_interval_nonempty_iff_product_condition hvX hcY).1 ⟨y / x, h1, h2⟩
  · intro h
    obtain ⟨r, h1, h2⟩ := (ratio_interval_nonempty_iff_product_condition hvX hcY).2 h
    have hr : 0 < r := lt_trans (div_pos hcX hvX) h1
    refine ⟨1, r, one_pos, hr, ?_, ?_⟩
    · simpa using h1
    · simpa using h2

/-! ## Share coordinates (paper Section 4, target
`share_coordinate_corridor_equivalence`) -/

/-- Paper Eq. (5): in share coordinates the payoffs are
`uX = R(vX+cX)(q - qL)` and `uY = R(vY+cY)(qU - q)`. -/
theorem share_payoff_identities
    {vX vY cX cY R q : ℝ} (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    uXshare vX cX R q = R * (vX + cX) * (q - qL vX cX) ∧
      uYshare vY cY R q = R * (vY + cY) * (qU vY cY - q) := by
  have hX : vX + cX ≠ 0 := by positivity
  have hY : vY + cY ≠ 0 := by positivity
  constructor
  · simp only [uXshare, uX, qL]
    field_simp
    ring
  · simp only [uYshare, uY, qU]
    field_simp
    ring

/-- `qL < qU` is equivalent to the product condition. -/
theorem qL_lt_qU_iff_product_condition
    {vX vY cX cY : ℝ} (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    qL vX cX < qU vY cY ↔ ProductCondition vX cX vY cY := by
  have h1 : (0:ℝ) < vX + cX := by linarith
  have h2 : (0:ℝ) < vY + cY := by linarith
  rw [qL, qU, div_lt_div_iff₀ h1 h2]
  constructor
  · intro h
    simp only [ProductCondition]
    nlinarith
  · intro h
    simp only [ProductCondition] at h
    nlinarith

/-- **`share_coordinate_corridor_equivalence`** (paper Section 4).  At fixed positive
total flow `R`, strict bilateral benefit at share `q` holds exactly when
`qL < q < qU`; and `qL < qU` is equivalent to the product condition. -/
theorem share_coordinate_corridor_equivalence
    {vX vY cX cY R q : ℝ} (hR : 0 < R)
    (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    (0 < uXshare vX cX R q ∧ 0 < uYshare vY cY R q ↔ qL vX cX < q ∧ q < qU vY cY) ∧
      (qL vX cX < qU vY cY ↔ ProductCondition vX cX vY cY) := by
  obtain ⟨eX, eY⟩ := share_payoff_identities (R := R) (q := q) hvX hvY hcX hcY
  refine ⟨?_, qL_lt_qU_iff_product_condition hvX hvY hcX hcY⟩
  have hX : 0 < R * (vX + cX) := by positivity
  have hY : 0 < R * (vY + cY) := by positivity
  rw [eX, eY]
  constructor
  · rintro ⟨h1, h2⟩
    constructor
    · nlinarith [h1, hX]
    · nlinarith [h2, hY]
  · rintro ⟨h1, h2⟩
    exact ⟨by nlinarith, by nlinarith⟩

/-! ## C3 — Theorem 3 (Symmetric Nash midpoint) -/

/-- **C3 / paper Theorem 3.**  Suppose the corridor is nonempty (`cX cY < vX vY`) and
the total flow `R > 0` is fixed.  Then the symmetric Nash product `uX * uY` has the
*unique* maximizer `q* = (qL + qU)/2` over all shares `q`, and the associated payoffs
are `uX* = R(vX+cX)δ/2`, `uY* = R(vY+cY)δ/2` with `δ = qU - qL > 0`. -/
theorem nash_midpoint_unique_maximizer
    {vX vY cX cY R : ℝ} (hR : 0 < R)
    (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY)
    (hfeas : ProductCondition vX cX vY cY) :
    (∀ q : ℝ, q ≠ (qL vX cX + qU vY cY) / 2 →
        nashProduct vX cX vY cY R q
          < nashProduct vX cX vY cY R ((qL vX cX + qU vY cY) / 2)) ∧
      uXshare vX cX R ((qL vX cX + qU vY cY) / 2)
          = R * (vX + cX) * (qU vY cY - qL vX cX) / 2 ∧
      uYshare vY cY R ((qL vX cX + qU vY cY) / 2)
          = R * (vY + cY) * (qU vY cY - qL vX cX) / 2 := by
  set a := qL vX cX with ha
  set b := qU vY cY with hb
  have hab : a < b := (qL_lt_qU_iff_product_condition hvX hvY hcX hcY).2 hfeas
  have hX : 0 < R * (vX + cX) := by positivity
  have hY : 0 < R * (vY + cY) := by positivity
  have key : ∀ q : ℝ, nashProduct vX cX vY cY R q
      = (R * (vX + cX)) * (R * (vY + cY)) * ((q - a) * (b - q)) := by
    intro q
    obtain ⟨eX, eY⟩ := share_payoff_identities (R := R) (q := q) hvX hvY hcX hcY
    rw [nashProduct, eX, eY, ← ha, ← hb]; ring
  refine ⟨?_, ?_, ?_⟩
  · intro q hq
    rw [key q, key ((a + b) / 2)]
    have hne : (q - (a + b) / 2) ^ 2 > 0 := by
      have : q - (a + b) / 2 ≠ 0 := sub_ne_zero.mpr hq
      positivity
    nlinarith [mul_pos hX hY]
  · obtain ⟨eX, _⟩ := share_payoff_identities (R := R) (q := (a + b) / 2) hvX hvY hcX hcY
    rw [eX, ← ha]; ring
  · obtain ⟨_, eY⟩ := share_payoff_identities (R := R) (q := (a + b) / 2) hvX hvY hcX hcY
    rw [eY, ← hb]; ring

/-! ## C4 — Corollary 1 (Bandwidth cannot restore feasibility) -/

/-- **C4 / paper Corollary 1.**  Within this model:
(i) the set of feasible shares — hence also the optimal share `q*` and the feasibility
condition — does not depend on the total flow `R`;
(ii) when the corridor is nonempty, all payoffs scale linearly in `R`;
(iii) when the corridor is empty (`¬ (cX cY < vX vY)`), no total flow `R > 0` and no
split of it makes both payoffs strictly positive — indeed no positive flow pair
`(x, y)` does. -/
theorem bandwidth_scaling_cannot_restore_feasibility
    {vX vY cX cY : ℝ} (hvX : 0 < vX) (hvY : 0 < vY) (hcX : 0 < cX) (hcY : 0 < cY) :
    (∀ R₁ R₂ : ℝ, 0 < R₁ → 0 < R₂ →
        {q : ℝ | 0 < uXshare vX cX R₁ q ∧ 0 < uYshare vY cY R₁ q}
          = {q : ℝ | 0 < uXshare vX cX R₂ q ∧ 0 < uYshare vY cY R₂ q}) ∧
      (∀ R s q : ℝ, uXshare vX cX (s * R) q = s * uXshare vX cX R q ∧
        uYshare vY cY (s * R) q = s * uYshare vY cY R q) ∧
      (¬ ProductCondition vX cX vY cY →
        ∀ x y : ℝ, 0 < x → 0 < y → ¬ BilateralBenefit vX cX vY cY x y) := by
  refine ⟨?_, ?_, ?_⟩
  · intro R₁ R₂ hR₁ hR₂
    ext q
    simp only [Set.mem_setOf_eq]
    rw [(share_coordinate_corridor_equivalence (R := R₁) (q := q) hR₁ hvX hvY hcX hcY).1,
      (share_coordinate_corridor_equivalence (R := R₂) (q := q) hR₂ hvX hvY hcX hcY).1]
  · intro R s q
    constructor
    · simp only [uXshare, uX]; ring
    · simp only [uYshare, uY]; ring
  · intro hempty x y hx hy hben
    obtain ⟨h1, h2⟩ :=
      (bilateral_benefit_iff_reciprocity_corridor hx hy hvX hvY hcX hcY).1 hben
    exact hempty
      ((strict_corridor_nonempty_iff_product_condition hvX hvY hcX hcY).1
        ⟨x, y, hx, hy, h1, h2⟩)

/-! ## Non-vacuity witnesses

Each formalized target is instantiated at explicit positive data, and both sides of
each equivalence are shown to be realizable (feasible and infeasible economies both
occur).  This rules out vacuous satisfaction of the hypotheses. -/

section NonVacuity

/-- A feasible economy: `vX = vY = 2`, `cX = cY = 1`, so `cX cY = 1 < 4 = vX vY`. -/
theorem witness_feasible_product_condition : ProductCondition 2 1 2 1 := by
  norm_num [ProductCondition]

/-- An infeasible economy: `vX = vY = 1`, `cX = cY = 2`, so `cX cY = 4 > 1 = vX vY`. -/
theorem witness_infeasible_product_condition : ¬ ProductCondition 1 2 1 2 := by
  norm_num [ProductCondition]

/-- Non-vacuity for C1, positive side: in the feasible economy the flows `x = y = 1`
give strict bilateral benefit, and the ratio `y/x = 1` is indeed in the corridor. -/
theorem witness_C1_benefit :
    BilateralBenefit 2 1 2 1 1 1 ∧ InCorridor 2 1 2 1 1 1 := by
  refine ⟨?_, ?_⟩
  · exact (bilateral_benefit_iff_reciprocity_corridor (x := 1) (y := 1)
      one_pos one_pos two_pos two_pos one_pos one_pos).2 (by norm_num [InCorridor])
  · norm_num [InCorridor]

/-- Non-vacuity for C1, negative side: in the same feasible economy the flow pair
`x = 1, y = 10` lies outside the corridor and does *not* give bilateral benefit, so
the equivalence of C1 is not trivially true. -/
theorem witness_C1_no_benefit :
    ¬ BilateralBenefit 2 1 2 1 1 10 ∧ ¬ InCorridor 2 1 2 1 1 10 := by
  constructor
  · rintro ⟨-, h⟩; norm_num [uY] at h
  · rintro ⟨-, h⟩; norm_num at h

/-- Non-vacuity for C2: the corridor of the feasible economy really is nonempty. -/
theorem witness_C2_corridor_nonempty :
    ∃ x y : ℝ, 0 < x ∧ 0 < y ∧ InCorridor 2 1 2 1 x y :=
  (strict_corridor_nonempty_iff_product_condition two_pos two_pos one_pos one_pos).2
    witness_feasible_product_condition

/-- Non-vacuity for C2: the corridor of the infeasible economy really is empty. -/
theorem witness_C2_corridor_empty :
    ¬ ∃ x y : ℝ, 0 < x ∧ 0 < y ∧ InCorridor 1 2 1 2 x y := fun h =>
  witness_infeasible_product_condition
    ((strict_corridor_nonempty_iff_product_condition one_pos one_pos two_pos two_pos).1 h)

/-- Non-vacuity for C3: in the feasible economy with `R = 1`, the hypotheses of C3 are
satisfiable, the optimal share is `q* = 1/2`, and the Nash product there is strictly
positive (so the maximizer is not a degenerate zero). -/
theorem witness_C3 :
    (qL 2 1 + qU 2 1) / 2 = 1 / 2 ∧
      0 < nashProduct 2 1 2 1 1 ((qL 2 1 + qU 2 1) / 2) ∧
      ∀ q : ℝ, q ≠ (qL 2 1 + qU 2 1) / 2 →
        nashProduct 2 1 2 1 1 q < nashProduct 2 1 2 1 1 ((qL 2 1 + qU 2 1) / 2) := by
  have hq : (qL 2 1 + qU 2 1) / 2 = 1 / 2 := by norm_num [qL, qU]
  refine ⟨hq, ?_, ?_⟩
  · rw [hq]; norm_num [nashProduct, uXshare, uYshare, uX, uY]
  · exact (nash_midpoint_unique_maximizer (R := 1) one_pos two_pos two_pos one_pos one_pos
      witness_feasible_product_condition).1

/-- Non-vacuity for C4: bandwidth genuinely scales payoffs (doubling `R` doubles both
payoffs at the optimal share of the feasible economy), while in the infeasible economy
no positive flow pair gives bilateral benefit. -/
theorem witness_C4 :
    uXshare 2 1 2 (1 / 2) = 2 * uXshare 2 1 1 (1 / 2) ∧
      uXshare 2 1 1 (1 / 2) = 1 / 2 ∧
      ∀ x y : ℝ, 0 < x → 0 < y → ¬ BilateralBenefit 1 2 1 2 x y := by
  refine ⟨by norm_num [uXshare, uX], by norm_num [uXshare, uX], ?_⟩
  exact (bandwidth_scaling_cannot_restore_feasibility
      (vX := 1) (cX := 2) (vY := 1) (cY := 2) one_pos one_pos two_pos two_pos).2.2
    witness_infeasible_product_condition

end NonVacuity

/-! ## Axiom audit -/

section AxiomAudit

-- Each target depends only on the standard axioms `propext`, `Classical.choice`,
-- `Quot.sound`; no `sorry`, no new axiom, no `native_decide`.
#print axioms bilateral_benefit_iff_reciprocity_corridor
#print axioms strict_corridor_nonempty_iff_product_condition
#print axioms share_coordinate_corridor_equivalence
#print axioms nash_midpoint_unique_maximizer
#print axioms bandwidth_scaling_cannot_restore_feasibility

end AxiomAudit

end Viridis.Run128.PaperFormalization
