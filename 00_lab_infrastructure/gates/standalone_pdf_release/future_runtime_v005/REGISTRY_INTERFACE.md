# Additive registration and manuscript-access interface

The original Phase7 source closure and exact historical scientific registrar must be consumed first. These candidate modules neither install that closure nor grant new scientific or publication authority. V1 registrations delegate their original scientific defaults; only V3 registrations consume the unique `methods_digest_v2` assembler. V3 readback inventories must equal every freshly admitted manifest upload plus `DIGEST_MANIFEST.json` and `PUBLICATION_BINDING.json`, including every separate per-note paper.

## Explicit context

`RegistryContext(root, binding, download=reader, observation_context=OWNER_CONTEXT, owner_getter=getter, deadline_guard=None)` reads the nominated source files freshly. `reader(record_id, filename)` returns actual observed file bytes; `getter(record_id, accept)` returns the complete actual body from the matching owner GET. Neither callback is discovered implicitly. The GET-only catalog/nightly operation may reread its own complete timestamped bodies, file bytes and transport receipts within the explicitly declared observation deadline. Each reuse rehashes the retained inputs and checks expiry; all scientific/access predicates run again, and no admission verdict is cached. A new operation performs new GETs. Publication controllers continue to obtain fresh observations at every causal boundary. Independent anonymous paper-byte readback remains mandatory outside this adapter. On the actual Zenodo file/content endpoint, binary GET uses `Accept: */*`; `Accept: application/octet-stream` was observed to return HTTP406.

`OWNER_CONTEXT` is exactly:

```json
{"authentication":"OWNER","owner_id":"1591505","legacy_accept":"application/json","native_accept":"application/vnd.inveniordm.v1+json"}
```

The closed registry fields are `standard`, `status`, `observation_context`, `entries`. Its standard is `VRS-MANUSCRIPT-ACCESS-REGISTRY-1`, and its status is `NOMINATED_INPUTS_NOT_AUTHORITY`. Each entry has exactly `record_id`, `registration`, `archive`, `access_correction`, `user_authority`, `prior_chain`. The four source inputs are contained regular-file path/SHA256 bindings. Duplicate records or registrations, alternative registrations for a named record, changed source bytes, anonymous context, cached validation PASS, unapproved copies, altered original files, changed metadata/permissions or unknown fields all HOLD.

The authority input binds the exact actual human request, the actual provider-attributed user-message excerpt, and the reviewed 58-manuscript copy plan. Each record must nominate all its manuscripts; Run167's earlier direct copy is included because its saved scientific admission contained six files. A new empty registry is valid for genuine V3 registrations needing no historical correction; it confers no legacy-access exception. A chain-only V3 entry uses the same closed fields with archive, access_correction and user_authority jointly null, and a mandatory AFTER_ACCESS actual observed-pair chain. Partial null fields and any V1 chain-only shortcut HOLD. This supports later default reads of V3 predecessors without inventing a legacy manuscript-access exception.

## Genuine chain composition

`prior_chain` is null for unchanged latest flags. Otherwise it has the four exact bindings `baseline_legacy`, `baseline_native`, `creation`, `publish`, plus `stage` equal to `BEFORE_ACCESS` or `AFTER_ACCESS`. `publish` alone may be null while a genuinely created successor remains unpublished. Baseline bindings name actual complete GET transport receipts, not declared expectations.

* `BEFORE_ACCESS`: baseline is the actual historical post-chain/pre-access OWNER pair. The unchanged original `own_prior_record.require_pair` consumes original saved science views, those actual baseline views and actual creation/publish receipts. Only after that does exact access-copy comparison consume baseline to current.
* `AFTER_ACCESS`: baseline is the actual pre-operation OWNER pair with the direct papers present. Exact access comparison first proves original scientific views to this complete baseline. The unchanged original chain consumer compares baseline to current using actual creation/publish receipts, preserving all the direct papers.

For a new operation, `require_registration(..., views=actual_pair, prior_chain_receipts=...)` accepts exactly those same four bindings without `stage`, using AFTER_ACCESS ordering. It may follow a nominated BEFORE_ACCESS chain. Overlapping AFTER_ACCESS chains HOLD. Full original views, every actual baseline and current view, genuine operation bindings, old/new/concept IDs and observed dates remain in the returned audit. No normalized or fabricated body is sent to scientific admission or to the original chain consumer. PDF authority cannot authorize a flag change.

The original chain source SHA256 is independently checked as `ff7d1b18bfad1a66662cc519415301a841b7ec05b9bc613dd8279d3644f8974f`. The unchanged scientific registrar source is `e97c6e906b6b2feeb348fc60dc0f4c22eac86cb23eac6f29afbf33dfe9df3cb5`. Existing source closure supplies and verifies the unchanged metadata, preservation, certificate and parity consumers.

## Default consumers

The context exposes `require_registration`, `registered_relation_template` and `public_label_read_record`. Corpus preservation and publication evaluation pass `consume=context.require_registration` explicitly. Corrected V1 entities remain on the original registrar's preserve/evaluate/augment route with this explicit access consumer; V3 entities route to the new registrar. Public-label reads must reach the context's OWNER pair adapter. Passing fixture tests, creating these nominees or reading this document is not installation or a public certification claim.

The optional scalar `deadline_guard()` performs no input read or clock reset. The production OWNER factory passes it explicitly, and the context invokes it before nominated-registry/hash work and immediately before/after each successful saved scientific admission. Scientific exceptions remain original and unmasked. This scalar may run before observation depth begins; it does not authorize any GET/replay, whose original active-depth, exact causal-byte and permanent-close predicates remain required. An expired registrar group is still represented as HOLD/DEBT by the unchanged complete-population consumer.
