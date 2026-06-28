# Cognition & Learning Under a Thermodynamic Bound: The Viridis Canon Series S6

**Justin Hart¹, Aristotle (Harmonic)²**
¹ Viridis LLC, Columbia Falls, Montana, USA · ORCID 0009-0008-3082-2482
² Automated theorem-proving system (machine verification)

*Viridis Canon — Series S6, v1.0.0. isDerivedFrom the Intelligence Bound spine, DOI 10.5281/zenodo.19317982.*

---

## Abstract

The Intelligence Bound (IB) states that the rate at which any physical agent can acquire mutual information about its environment is capped by the thermodynamic power it dissipates: dI/dt ≤ P·D/(k_BT ln2). Prior Viridis Canon series apply this ceiling to valuation (S1), monitoring (S2), planetary harmonization (S3), governance (S4), and corridors (S5). Series S6 turns the bound inward, onto the process of cognition and learning itself — asking not what an intelligence values or monitors, but how fast and how well it can *learn*, and on what schedule. We collect four machine-verified results into a single coherent pillar: a throughput law for attention (CTT), a generalization-as-crypticity identity for learning (DGT), the IB applied to a learner together with the optimality of square-root annealing (HDT), and a mutualism trichotomy for joint learning (MELT). Each is formalized in Lean 4 and verified by Aristotle with zero `sorry` and a clean axiom audit. Together they constitute the thermodynamic theory of how a Viridis agent — or any bounded learner — acquires and generalizes information.

## 1. Why a cognition series

The IB is a statement about an agent coupled to a world. Four of its faces concern what the agent *does* with the world. A fifth concerns what the agent does to *itself*: every act of learning is a physical process that stores information in a substrate, dissipates heat, and pays a Landauer cost to erase what it overwrites. A theory of conservation intelligence is incomplete without a theory of the learner. S6 is that theory. Its results share a common subject (the learning/cognition process), a common method (Lean-verified thermodynamic bounds), and a common object (the same I(W;D) mutual information that the IB ceilings). They had been scattered across standalone deposits and the governance series; S6 gives them one home and one citable concept DOI.

## 2. The four founding results

**CTT — Cognitive Throughput Theorem ("the Throughput", 13th IB self-application).** Establishes an inverse-square-root throughput law for attention: the maximum cognitive information rate scales as dI_cog/dt|max = K_cog·N^(−1/2) in the number of attended channels N, with a conserved attention budget R·√N = K (the "attentional iris"). A decoupled AI has zero throughput; a symbiotically coupled one has strictly positive throughput K_cog = √(2·W_attn·Φ_eco/(k_BT ln2)). 5 theorems. DOI 10.5281/zenodo.20763323.

**DGT — Dissipative Generalization Theorem ("the Annealer", 17th IB self-application).** Decomposes the stored information of a learner as S_mem = E_pred + χ_L (Still–Crooks), proves the generalization gap *equals* crypticity exactly (a learner generalizes iff it is non-cryptic), and shows the generalizing-information rate carries a crypticity debit against the IB ceiling, dE_pred/dt ≤ P·D/(k_BT ln2) − χ̇_L. The optimal learning temperature is β* = 1/σ² (thermal matching). 6 theorems. DOI 10.5281/zenodo.20982958.

**HDT — Harmonized Descent Theorem ("the Learner", 6th IB self-application).** Applies the IB directly to a learner: the generalizing-information acquisition rate is ceilinged at I_gen ≤ P_learn·D_L/(k_BT_eff ln2). It then proves the optimality of the square-root annealing schedule — T_eff ∝ t^(−1/2) is the *unique* global minimizer of the annealing action A(α) = α + 1/(4α) — the learning-rate face of Square-Root Universality. 4 theorems. (Awaiting deposit as a founding member.)

**MELT — Mutualistic Entropy-driven Learning Theorem.** Gives a mutualism trichotomy over joint learning efficiency η_joint = η_L + η_E + 2μ_LE/√(λ_L λ_E): super-additive when the stewardship coupling μ > 0, additive when μ = 0, and parasitically sub-additive when μ < 0, with a Cauchy–Schwarz / AM–GM core and an exact rank-1 saturation condition. 6 theorems. DOI 10.5281/zenodo.20982974.

## 3. What S6 gives Viridis

S6 is the in-house-model-training science of the company. HDT prescribes the training schedule (√-cooling), DGT supplies a crypticity-audited early-stop and a thermal-matching rule (β ← 1/σ̂²), CTT bounds the attention throughput of any cognitive module, and MELT certifies when two models (or a model and a steward) learn better together than apart. It is the cognition counterpart to S2 (how we observe the world) and S4 (how we govern the agent): how the agent itself comes to know.

## 4. Verification

Every theorem in S6 is stated and proved in Lean 4 and verified by Aristotle (Harmonic): zero `sorry`, axiom audit ⊆ {propext, Classical.choice, Quot.sound}, statements preserved verbatim and machine-checked non-vacuous. The `.lean` sources and Aristotle provenance are included in this deposit as the verification backbone.

*Scope note: Lean certifies the reasoning, not the empirical magnitudes. The theorems bound and relate quantities; calibrating constants to a given biome or model is an empirical task outside the proof.*

## References (canon lineage)

- Intelligence Bound spine — concept DOI 10.5281/zenodo.19317982 (FROZEN at v10.0.0, record 20801185).
- CTT 10.5281/zenodo.20763323 · DGT 10.5281/zenodo.20982958 · MELT 10.5281/zenodo.20982974 · HDT (pending deposit).
