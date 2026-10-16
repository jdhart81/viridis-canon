# Corrected write-plan review packet

PR #38 merged at `4d5259da8a07ef313e06c00fa1e3b9a38be9a277` after the completed successful workflow and successful check conclusions were verified. One aggregate job label remained stale/in-progress despite all completed successful steps; its enclosing workflow was completed/success. This was corroborated before merge.

Production writes: **0**. No production runtime, scripts, manifests, metadata, files, DOI records or certification evidence were changed. The new preparation code and corrected packet live only in the feature checkout. The old canonical audit packet is preserved and superseded for approval purposes.

- [Corrected plan](ZENODO_WRITE_PLAN.md): 36 amendments; 16 held reissue audit rows / nine chains.
- [Exact payload SHA256 list](PAYLOAD_SHA256.json): each expected-public, transport and rollback payload; every title restored exactly, including Canon v5.
- [Per-field preservation table](FIELD_PRESERVATION.md): all original logical fields restored, transport conversions explicit, missing evidence held.
- [Reissue chain holds](REISSUE_CHAINS.json): zero proposed mutation calls; no interim uncertified new versions; valid PUBLICATION_BINDING and claim eligibility must precede one verified version per chain.
- [BCAN scope correction](BCAN_CORRECTED_VERSION_PROPOSAL.md) and [SAC bridge text](SAC_BRIDGE_TEXT_PROPOSAL.md): proposals only.
- [Sandbox status](SANDBOX_VALIDATION.md): **HOLD — actual authenticated readback unavailable**. The guarded preflight stopped before any network operation because a sandbox-specific credential is absent. The open direct sandbox login is waiting for Justin. GitHub login requested new webhook administrator access; it was not authorized. No sandbox publish or new-version transaction occurred.

Validation: 85 gate/preparation/sandbox-boundary tests pass; every amendment's title and all non-description/keyword metadata fields are preserved; every single-label description retains exact historical prose; secret scans pass; unchanged protected issuer/client/backend hashes verified. A test-only sandbox runner pins every URL to sandbox.zenodo.org, rejects redirects, never uses production credentials and preserves unknown fields or holds rather than discarding them.

This packet is not ready for production approval until the requested complete sandbox amendment and new-version sequences produce a real title/DOI/relations readback. An authenticated production deposition-base reconciliation and fresh exact-hash approval will also be required before any future production PUT. No production write authority is granted by these documents.
