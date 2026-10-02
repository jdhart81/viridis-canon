# Verification coverage and publication gate

These consumers are untrusted implementer tooling under VRS-LEAN-ZERO-SORRY-CERTIFICATE-1. The private Comparator remains the sole verifier of record. They never run Lean, Lake, Elan, or a second kernel, and never modify the canonical verifier, issuer, backend pins, keys, challenge candidates, or existing DOI records.

The canonical input is `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0`. `~/Desktop/science ` is a noncanonical snapshot. The gates run from this repository while their `--root` and certificate bindings point at the live control plane. The certificate consumer reuses the unchanged `nightly_proof_track.current_certificate`, `binding_is_current`, and issuer `validate_comparator_witness_evidence`. Historical receipts missing the later targeted-export summary flag must pass the same raw-response export check. A false flag is HOLD. Issued historical input contracts are inspected as recorded; every new foundational envelope requires four sealed inputs.

## Report-only operation

Quote paths, including their spaces. Write derived reports into a separate output directory. The following commands never change publication artifacts or transmit proofs:

```sh
python3 00_lab_infrastructure/gates/corpus_ledger.py build \
  --root '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0' \
  --cert-root RESEARCH_PIPELINE_v2/lean_certificates \
  --out '/private/tmp/viridis-coverage-report/corpus_ledger.json'

python3 00_lab_infrastructure/gates/doi_audit.py \
  --root '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0' \
  --ledger '/private/tmp/viridis-coverage-report/corpus_ledger.json' \
  --out '/private/tmp/viridis-coverage-report/PUBLISHED_WITHOUT_CERT.json' \
  --markdown '/private/tmp/viridis-coverage-report/PUBLISHED_WITHOUT_CERT.md'

python3 00_lab_infrastructure/gates/claim_binding.py check \
  --run '/absolute/path/to/artifact' --entity-id Run-142 \
  --ledger '/private/tmp/viridis-coverage-report/corpus_ledger.json'

python3 00_lab_infrastructure/gates/publication_gate.py check \
  --artifact '/absolute/path/to/artifact' --entity-id Run-142 \
  --ledger '/private/tmp/viridis-coverage-report/corpus_ledger.json' \
  --output-dir '/private/tmp/viridis-publication-proposal'

python3 scripts/generate_public_index.py \
  --ledger '/private/tmp/viridis-coverage-report/corpus_ledger.json' \
  --output-dir '/private/tmp/viridis-public-index'
```

`file_entities` and `run_entities` are separate strict partitions. Priority is UNSOUND > HAS_SORRY > DEBT > NO_FORMALIZATION > CLEAN_UNCERTIFIED > CERTIFIED. A paper run represents its immutable certificate envelope when available; its historical sorry-bearing challenge files remain HAS_SORRY file entities. The whole-tree file census includes dependencies, archives, and exact-byte copies; a certified file copy is not another certified theorem or paper. Run-META-001 is kind SYNTHESIS, excluded from paper counts. `_LATEST` is excluded. Any traversal/read error is retained as a coverage HOLD.

Proof certification and claim-publication eligibility are separate. Publication requires current paper hashes and a `claim_binding.json` containing one certified theorem and exported witness per English formal claim, explicit defined/empirical symbols, and the exact disclaimer. Every formal claim in the hash-bound sealed inventory must be covered; numerical/deferred content remains explicitly unverified. Static rejection is advisory and conservative. It does not establish general semantic non-vacuity or empirical truth; the frozen witness contract and independent correspondence review remain necessary.

A publication HOLD produces the label `CONJECTURE — not machine-verified`. `--enforce` is a separate flag that stages metadata and a banner in an explicit successor output directory. It never edits the source artifact or remote Zenodo record. Generated public indexes are derived from the ledger; rerunning replaces manual edits in the generated output directory. Publication artifacts whose paper bytes were edited after certificate sealing remain binding HOLD even when their proofs retain valid certificates.

## Clean foundational preparation (Track B)

```sh
python3 00_lab_infrastructure/gates/track_b.py \
  --root '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0' \
  --source '/absolute/canonical/path/to/clean.lean' \
  --claim-binding '/absolute/path/to/reviewed/claim_binding.json' \
  --run-id Run-900 --out '/private/tmp/foundational-envelopes'
```

The default returns a read-only plan. `--enforce` freezes a new immutable Methods Note envelope only after source/claim hashes, named declarations, static triage, and the reserved Run-900–999 ID checks pass. It imports the unchanged canonical alignment helper. PDF generation requires an existing runtime with ReportLab; unavailable dependencies are HOLD before any partial envelope. No claims, witness names, or model identifications are invented. Unsupported term-proof syntax is HOLD under the existing helper. Every UNSOUND source, including the origin paper, is permanently ineligible for this preparation path. Existing certificates or envelope IDs are preserved.

Preparation leaves DEBT and produces the exact unchanged verifier/issuer command plan. It does not execute those commands or obtain transport authority. A later opt-in promotion must pass the applicable exact-hash egress authorization, then the unchanged client and issuer; only a valid issued certificate can clear debt. The preparation inventory uses FORMAL_TARGET pending receipt rather than falsely asserting FORMALLY_VERIFIED.

## Production integration and activation

This PR installs consumers and report-only CI tests. The external production scheduler/publishers are **not switched over by this PR**. Their hook locations and stale source-root issue are documented in `INTEGRATION.md`. Run one real nightly report cycle and inspect proposed labels before activating enforcement. Existing DOI amendments require Justin's separate explicit go; this code has no remote writer.

Tests:

```sh
python3 -m unittest discover -s 00_lab_infrastructure/gates -p 'test*.py' -v
```

The checked-in `.lean.txt` fixtures preserve the real T1–T3 sources and seven clean nucleus sources. The alignment fixture is an unchanged text-freezing helper, not a verifier. Private issued-receipt tests run when the canonical tree is available; portable regression tests need no credentials or Lean installation.
