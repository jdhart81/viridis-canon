# Parallel certification, ordered publication — proposal only

Status: PREPARED ONLY. A10 is unchecked. The existing scheduler, FIFO predicates,
certificate issuer and publication rules remain unchanged.

The present bottleneck is a held oldest proof preventing certification progress
on younger eligible work. The proposed policy separates independent verification
work from the ordered admission queue. It requires Justin's explicit policy
authorization and independent review before any activation.

Use the existing scheduler as the sole owner. At a normal checkpoint, it may
dispatch at most two independently hash-bound Comparator requests for eligible
debt, each with an immutable run/candidate/toolchain/Mathlib/request identity and
exclusive per-request ownership. A terminal or ambiguous existing request is
reconciled before another dispatch; no blind retries or alternate backend arise
from this policy. Local Lean execution remains forbidden.

Accepted younger results enter an immutable verified-results holding area.
They do not satisfy either of the original START's named oldest certificate
targets, change FIFO progress accounting, or become publishable while an older
eligible result remains held. Certificate issuance still requires genuine
nanoda/default-kernel acceptance and the existing zero-hole, premise and
non-vacuity checks. Publishing drains only the contiguous eligible oldest-first
prefix that has cleared every existing science, review, packaging and authority
gate. A release HOLD never cancels due generation.

At 24 hours of authenticated FIFO-head HOLD, emit a report-only alert containing
the run, held-since timestamp, exact failing goal, candidate hash and provider
receipt identity. Missing held-since or goal evidence remains unavailable. A
rejected proof produces no automatic repair attempt; Justin's exact authority
and the existing immutable correction policy still govern transport.

Required acceptance tests before activation: delayed oldest/accepted younger
does not permit publication or oldest-target credit; transport ambiguity does
not duplicate dispatch; one scheduler holds ownership across checkpoint resume;
candidate or statement drift refuses receipt reuse; each younger acceptance
retains its own certificate/proof bindings; due generation remains independent;
restoring the oldest result drains only the now-contiguous admitted prefix.

Rollback disables future parallel dispatch through a reviewed policy change,
then reconciles every in-flight request without discarding receipts or changing
proof bytes. Already accepted results retain their identities and ordered
publication status. No existing certificate, DOI or source seal is rewritten.
