# Source review and activation

This is an additive review packet. The private dated and successor publishers
already call the standalone-PDF preflight before publication and perform direct
anonymous PDF readback after preserving a minted DOI. The current operational
instructions and nightly prompt route future Methods Digest dispatch through
`guard_methods_digest_release.py`. Its default invocation is read-only. The
real current archive-only configuration is held before controller dispatch;
`digest_pdf_v2_review/LEGACY_CONFIG_PREFLIGHT_NEGATIVE.json` records that check.

The original Phase-7 assembler, registrar, controller, runtime profiles,
immutable policy catalog and historical registrations are unchanged. Calling
an old controller directly bypasses the outer gate; the current default
operational route prohibits that invocation. This packet does not claim that
the underlying pinned runtime has been upgraded.

## Remaining compatible runtime work

1. Review the v2 assembler and exact access-copy adapter in this packet. The
   assembler uses admitted note bytes for each top-level `Run-N-Paper.pdf` and
   declares hashes and sizes in its fresh immutable upload manifest.
2. Produce a compatible controller that uses the complete manifest upload
   inventory plus `DIGEST_MANIFEST.json` and `PUBLICATION_BINDING.json`, rather
   than the historical six-name constant. Its predecessor comparison and draft
   cleanup must account for only receipt-bound exact inherited manuscript
   copies. The old W41 controller is cohort-specific and cannot become a
   general future-release controller by substituting a helper hash.
3. Add reviewed version dispatch for v2 registration while retaining the exact
   saved v1 admission source. Nominate each historical access correction in a
   closed, source-bound registry. `registered_manuscript_access.py` first runs
   saved historical scientific admission and only then compares full fresh
   views using the additive rule. No cached PASS or unbound registry discovery
   establishes authority.
4. Extend the authorized runtime profile and source closure to the exact new
   paths and source hashes. `phase7_runtime_update.validate` currently admits a
   closed module list, genuine merged-main PR identity and Git blobs, and the
   original protected runtime target set. Tests or this draft cannot satisfy
   that installed-source receipt. Preserve all old profile snapshots.
5. Obtain the genuine merged PR and successful required CI readbacks:
   `report-only-consumers`, `verify-catalog`, `verify-functions`, `verify`,
   `deposit-verify`, `lean-build-current`, `lean-build-p0` and `gitleaks`.
   Use the approved remote proof route; do not substitute local Lean execution.
   Add the standalone manuscript workflow's successful readback as well.
6. Capture exact merged file/blob readbacks, predecessor runtime binding and
   protected-content comparison in a new immutable installation receipt.
   Bind a fresh config, compatible controller, correction registry and direct
   user authorization to their exact hashes. Never edit an old sealed config,
   historical manuscript, certificate, archive or access receipt in place.
7. Validate saved historical registrations, fresh public-label reads with full
   access-copy audit, the current default read-only dispatch, and exact inherited
   draft inventory. A new release still requires every original science,
   ownership, source-session, transport and publication gate plus this PDF gate.

An independent agent review can evaluate these bytes and tests. It cannot
truthfully manufacture a merged GitHub readback, successful CI or installation
receipt. This PR prepares reviewable code; the unimplemented compatible
controller/registry/profile work above remains explicit. Until that successor
is genuinely installed, archive-only digest publication remains held.

## Read-only access-copy comparison input

The adapter API is intentionally transport-free. Root supplies actual complete
legacy/native JSON bodies from own-record GET receipts, exact saved original
bodies, original admitted manifest and archive bytes, and the real source-bound
authority consumer. Do not normalize away server fields before calling it.

```python
require_pair(
    actual_legacy, actual_native, saved_legacy, saved_native,
    receipt=correction_receipt,
    manifest_bytes=original_manifest_bytes,
    archive_bytes=original_methods_notes_zip_bytes,
    download=own_public_file_bytes,  # (record_id, basename) -> actual bytes
    authority_consumer=consume_exact_user_access_copy_authority,
    protected_projection=own_record_comparison.prior_protected_projection,
)
```

The original saved registration must be admitted first through its exact
historical source. The authority consumer must read and validate the nominated
exact user directive binding at invocation and return
`EXACT_USER_ACCESS_COPY_AUTHORITY_PASS`; a lambda returning that label or a
cached PASS is only a synthetic unit fixture. Genuine existing version-chain
handling remains separate: the access-copy rule grants no flag exception.

The correction receipt has this closed shape; hash values are computed from
the actual original files and copied archive members:

```json
{
  "standard": "VRS-DIGEST-MANUSCRIPT-ACCESS-CORRECTION-1",
  "status": "EXACT_EXISTING_ARCHIVE_ACCESS_COPIES",
  "record_id": "own version record ID",
  "doi": "10.5281/zenodo.own version record ID",
  "source_manifest_sha256": "original manifest SHA-256",
  "source_archive_sha256": "original METHODS_NOTES.zip SHA-256",
  "original_files": [
    {"filename": "original top-level basename", "sha256": "SHA-256", "md5": "MD5", "bytes": 1}
  ],
  "copies": [
    {"run_id": "Run-167", "member": "notes/Run-167/paper.pdf", "filename": "Run-167-Paper.pdf", "sha256": "SHA-256", "md5": "MD5", "bytes": 1}
  ],
  "authority": {"path": "exact nominated immutable user-authority receipt", "sha256": "SHA-256"}
}
```

All original filenames and bytes must remain, the actual file set must equal
the originals plus declared copies, and every added PDF must match its note
admission, manifest archive-member binding and downloaded public bytes. The
rule downloads and rehashes every original file too. Both full actual views
remain in the returned audit. Only the added PDF entries and exactly derived
native `count`/`total_bytes` are allowed; rights, metadata, unknown fields and
version identities remain protected. The return value certifies no new claim.

## Actual observation-context review

A read-only check of repaired record 23308138 compared the genuine saved
legacy/native bodies with fresh complete public observations. The legacy view
matches after removing only the two declared PDF entries for comparison. The
fresh anonymous native view correctly holds because it omits three protected
fields present in the saved body: `parent.access.grants`, `parent.access.links`
and `versions.is_latest_draft`. They are not PDF-access exceptions.

A separately authorized fresh owner-native GET retains those fields unchanged.
Its complete protected comparison matches after only the declared PDF entries
and exactly derived `count`/`total_bytes` changes. Both owner and anonymous
observations are retained. The saved transport receipt lacks an explicit
authentication label, so the owner context is inferred from the saved
owner-only fields; do not relabel or rewrite that historical receipt.

The compatible source review must bind matching request/observation contexts,
preserve the independent anonymous observation and direct PDF-byte readback,
and reject unknown-field drift. This result permits no field normalization,
scientific upgrade or installed-registrar claim. The registrar/runtime adapter
remains staged until the genuine source closure and installation work above
are completed.
