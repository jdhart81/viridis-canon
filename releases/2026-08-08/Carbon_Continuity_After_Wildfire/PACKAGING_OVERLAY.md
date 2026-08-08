# Reproducibility packaging overlay

This versioned overlay repairs a packaging-only defect in the original
Saturday candidate. The scientific paper, Lean source, theorem statements,
and scientific claims are unchanged.

The original checker attempted to open the author's private absolute path for
`Wildfires Carbon Impact Analysis.pdf` solely to print its SHA-256 digest. The
source ledger identifies that file as a user-supplied concept outline and
explicitly states that it is not scientific evidence. It is not consumed by
the mathematical model, numerical checks, Lean proof, or paper build.

The revised checker reads the same frozen concept-outline digest from the
included `provenance/SOURCE_BINDING.json`. The fuller provenance record is
included as `provenance/SOURCE_LEDGER.json`. This makes the public checker
portable without weakening or changing the recorded source binding.

The pre-overlay exact-hash review remains preserved as
`provenance/POST_ARISTOTLE_REVIEW_PRE_OVERLAY.json`. The release is eligible
only after the revised checker, numerical output, Lean build, paper render, and
fresh exact-hash review all pass.
