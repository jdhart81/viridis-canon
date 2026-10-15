# Production draft-and-discard rehearsals

Use `--rehearse --go` with `VIRIDIS_ENGINE_ROOT` naming the runbook engine
directory. Every receipt goes below `engine/rehearsals/<UTC>/`. A rehearsal
creates a fresh production draft, uploads the approved bytes, reads back the
complete names/sizes/checksums and metadata including copyright, deletes its
draft, and requires HTTP 404 or 410. It never writes inside a bundle, writes a
`PUBLISHED_DOI.txt`, invokes publication, registers a digest, or mirrors to Canon.

Both outer guards pass `--rehearse` through the actual digest child/controller.
The controller uses the same `run()` and its original package, source, scientific,
authority, account-discovery, ownership, original-budget and exact-draft checks.
Only the operational receipt reader admits the current engine output directory;
canonical source/configuration/authority bindings retain their original root.

The rehearsal journal holds the same live global writer lock and observes the
same complete original budget before every draft operation. Its intentions and
transport receipts remain in the engine directory and never alter the live
publication index. Both its reservation boundary and the publication URL builder
refuse `/actions/publish`. The original source session must exit successfully and
the package tree hash must remain exact before a terminal result is emitted.
Prepublication HOLDs attempt draft cleanup and retain any uncertain cleanup as a
HOLD requiring readback; they never claim successful deletion without the 404/410.

The dated and successor publishers provide the same draft-and-discard mode. The
active `weekend_canon_lockstep.py` refuses rehearsal argv before any action. The
historical lockstep snapshot remains immutable. `VIRIDIS_ZENODO_API_BASE` is
forbidden; production DOI receipts accept only `10.5281/zenodo.<digits>`.
