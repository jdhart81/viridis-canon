# BCAN erratum and corrected-version proposal

DOI: 10.5281/zenodo.22236387; Run-142. Proposal only. Preserve the exact existing title, published files, DOI versions, proof candidate and certificate. No manuscript was replaced or published.

The existing certificate binds the frozen scalar statement (SHA256 `621290dae7c84af88be4fdf4ec59e1639b17725ea470181eb28e1de73ddcba26`) and certificate SHA256 `22e627600351643caaa03e03375b1d7a5e9245b55936b2f39fa93db24c7c7cc8`. The prior comparison retains the full manuscript and certified contract in [the review packet](../pr37-followup/statement-comparisons/22236387.md).

Proposed erratum text:

> The formal certificate covers the scalar inequalities stated below. It does not certify the derivation of those scalar hypotheses from unit-vector geometry, existence of a geometric bisector, or an arbitrary finite corridor aggregation. The earlier geometric interpretation and aggregation discussion exceeded the named certified statement scope. They must be treated as separate mathematical/model arguments until independently reviewed and separately bound. The scalar diagonal identity is not evidence of a geometrically realizable maximizing configuration.

Proposed replacement for the formally supported part of Proposition 1:

> Let a, b, c be real numbers. Assume c ≥ −1 and ((a+b)/2)² ≤ (1+c)/2. Define M(c) = √((1+c)/2). Then min(a,b) ≤ M(c). The quadratic inequality is an explicit premise; this result does not establish that particular vectors, trajectories or ecological corridors satisfy it.

Bind only this conditional claim to `Viridis.HDFMCorridors.Alignment.two_direction_alignment_ceiling`. Its hypotheses are exactly `hc : -1 ≤ c` and `hquad : ((a + b) / 2)^2 ≤ (1 + c) / 2`, with conclusion `min a b ≤ alignmentCeiling c`. The unit-vector parameterization remains outside the formal model. No empirical identification of a, b or c is asserted.

Proposed scalar identity note:

> For c ≥ −1, min(M(c),M(c)) = M(c). This diagonal scalar identity does not assert existence of any vector or corridor realizing both projections.

This corresponds to `bisector_scalar_attains_ceiling`; label it an identity/supporting definition fact and do not use it as a FORMALLY_VERIFIED scientific claim. The triviality/non-vacuity coverage gate must assess its actual candidate proof before any claim label. The name “bisector” supplies no geometric proof.

Proposed replacement for Proposition 2's formally supported part:

> For real lengths ℓ₁, ℓ₂ ≥ 0 and real numbers m, a₁, a₂ satisfying a₁ ≥ m and a₂ ≥ m, one has m(ℓ₁+ℓ₂) ≤ ℓ₁a₁+ℓ₂a₂. This is the two-segment scalar statement; no arbitrary finite aggregation or vector model is included in this formal claim.

Bind this claim only to `two_segment_alignment_persists`. A finite-family extension would require a separately named certified result; repeating a plausible induction argument in prose is not an existing exact certificate binding.

Proposed length-floor correction:

> A lower bound A ≥ mL together with A ≥ D does not imply L ≥ D/m. If a decision policy instead explicitly requires the conservative lower-bound certificate mL ≥ D and assumes m > 0, its length threshold is L ≥ D/m. That policy is separate from the above named certified inequalities.

Remove the earlier necessary-length inference from the certified claim list, abstract and conclusion. Scalar arithmetic review example: m = 1/2, L = 1, A = D = 1 meets A ≥ mL and A ≥ D but violates L ≥ D/m. This example is an explanatory arithmetic check, not a new formal certificate.

Proposed scope/labels in a corrected manuscript:

- Formal claim BCAN-C1: the conditional scalar ceiling, exactly one theorem binding.
- Formal claim BCAN-C2: the conditional two-segment scalar inequality, exactly one theorem binding.
- Supporting scalar identity: no scientific FORMALLY_VERIFIED label.
- Geometry, finite-family generalization and physical interpretation: outside the certified scope; omit them from the formally verified result summary.

Publication remains HOLD. This is a scientific scope correction, not a verification-status-only allowed diff. Before a corrected version can receive a PUBLICATION_BINDING receipt, preserve the old record, prepare a fresh immutable corrected manuscript/sealed envelope, obtain the required independent statement correspondence review and existing unchanged Comparator/issuer evidence under the applicable correction contract, then bind the final manuscript and reviewed allowed diff. Do not reuse an old status-only receipt to authorize these substantive changes. No certification call or publication is authorized by this proposal.
