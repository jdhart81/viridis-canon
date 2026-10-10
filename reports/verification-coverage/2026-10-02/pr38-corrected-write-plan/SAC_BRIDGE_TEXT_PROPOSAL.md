# SAC explicit model-to-Lean bridge proposal

DOI: 10.5281/zenodo.22236768; corrected Run-137 contract. Proposal only. Preserve exact existing title, published manuscript, old DOI versions, candidate and certificate. No source or certificate was edited.

The corrected frozen statement SHA256 is `914947efc9341f44104a52c6283ac6d4ac1c96c33226381d07ac3d55a5f53cbb`; certificate SHA256 is `d92193d2b290e62fbfa8929243219665b06559448249cccec0be08bdf67ba529`. [The prior comparison](../pr37-followup/statement-comparisons/22236768.md) includes the corrected and frozen-false counterexample targets. Use only the corrected positive statements for claim coverage.

Proposed Methods insertion, referenced explicitly by each theorem:

> Throughout, n is an integer with n ≥ 1, indexed partners are i ∈ {0,…,n−1}, wᵢ > 0, dᵢ > 0, and ε > 0. For the normalized-weight comparisons we additionally require Σᵢwᵢ = 1. Put D = Σᵢ wᵢ/dᵢ and explicitly assume D > 0 in every displayed result dividing by D. Under the nonempty positive-weight/positive-efficiency model, each summand is positive and hence D > 0; this mathematical bridge is written out here, rather than inferred from a theorem title. Formal use of the corrected Lean statement supplies the explicit `hden` premise.

> Define d_max = maxᵢ dᵢ over this finite nonempty family. In every result using d_max, require dᵢ ≤ d_max for every i and d_max ≥ 0 explicitly. The model's positive efficiencies imply that the actual finite maximum is positive; the bound cannot silently replace that maximum by an arbitrary negative upper-bound symbol. The Lean predicates are `hmax`/`hdmax` and `hdmax0`, with their exact domains stated below.

Proposed standalone Theorem 1 wording:

> Let n ≥ 1, wᵢ > 0, dᵢ > 0, ε > 0 and D = Σᵢ wᵢ/dᵢ > 0. Assume pᵢ ≥ 0, Σᵢpᵢ ≤ P, rᵢ ≤ pᵢdᵢ/ε, and wᵢR ≤ rᵢ for every i. Then R ≤ P/(εD).

Exact binding: `conjunctive_rate_upper_bound`, including `hw`, `hd`, `hp`, `heps`, `hden`, `hpower`, `hcomponent`, `hrequired`. An operational nonnegative power budget also follows from a feasible nonnegative power allocation; retain P ≥ 0 explicitly when presenting feasible allocations. The logical bound remains conditional on the supplied model, not an empirical assessment of partner efficiencies.

Proposed allocation identities, kept as separate claims:

> Define pᵢ* = P(wᵢ/dᵢ)/D. Under wᵢ > 0, dᵢ > 0 and D > 0, Σᵢpᵢ* = P. With ε > 0, every normalized modeled rate (pᵢ*dᵢ/ε)/wᵢ equals P/(εD).

Bind the sum identity to `symbiotic_allocation_attains` and the normalized-rate identity to `normalized_rates_equal`, one claim per theorem. These identities alone do not certify global optimality, feasibility of arbitrary operational constraints, empirical partner rates or additional equality/attainment cases. When describing nonnegative allocations, retain P ≥ 0. Do not merge both identities into one exact-theorem claim binding.

Proposed standalone harmonic comparison:

> For a finite nonempty family with wᵢ > 0, Σᵢwᵢ = 1, dᵢ > 0 and dᵢ ≤ d_max for every i, the defined weighted harmonic coefficient is at most d_max.

Exact binding: `weighted_harmonic_le_max`, with `[Nonempty (Fin n)]`, `hw`, `hwsum`, `hd`, `hmax`. The n ≥ 1 indexing convention supplies nonemptiness; an explicitly reviewed formal bridge would be needed to carry that implication as separate machine-certified evidence. Equality characterization is not separately named in this certificate and should not inherit a formal label.

Proposed standalone additive bound:

> Let ε > 0, pᵢ ≥ 0, dᵢ ≤ d_max for every i, d_max ≥ 0, Σᵢpᵢ ≤ P, and rᵢ ≤ pᵢdᵢ/ε. Then Σᵢrᵢ ≤ Pd_max/ε.

Exact binding: `additive_rate_upper_bound`, with `hp`, `heps`, `hdmax`, `hdmax0`, `hpower`, `hcomponent`. Displaying `d_max ≥ 0` prevents standalone reuse under the false frozen negative-upper-bound formulation. The certificate's frozen-false counterexample is retained as historical evidence, never promoted to the desired positive bound.

The bridges above are explicit model assumptions and mathematical explanation, not new Lean-certified derivations. No local Lean or replacement verifier is used. A fresh independent review must check the bridge premises and one-theorem claim bindings. Adding mathematical premises/clarifications is not automatically a verification-status-only allowed diff; the PUBLICATION_BINDING consumer must hold the changed manuscript until a fresh sealed correction contract and the applicable unchanged certification/review path support it. No production metadata, manuscript or DOI writes are authorized by this text proposal.
