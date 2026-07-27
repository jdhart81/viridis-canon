# Viridis research portal

The repository now serves two compatible audiences:

1. researchers inspect the formal canon directly; and
2. humans and software inspect the same repository through a deterministic
   catalog and GitHub Pages explorer.

## Local use

Build and verify the catalog:

```bash
python3 -m canon_core build
python3 -m canon_core verify docs/data/catalog.json
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Preview the static portal:

```bash
python3 -m http.server 8080 --directory docs
```

Then open `http://127.0.0.1:8080`.

The public explorer includes:

- a deterministic, interactive research graph grouped by spine, flagship, and
  working-corpus tiers, with import and topic relationships;
- a readable abstract on every public record;
- a direct paper link when a DOI or curated paper target exists; and
- a full-source link for records whose public research artifact is the Lean
  module itself.

## Machine interface

GitHub Pages exposes `data/catalog.json`. The document and every record carry
SHA-256 digests over canonical JSON. Consumers can recompute these using
`canon_core.canonical`. Each public record also carries `abstract`,
`source_url`, and `paper_url`. When a distinct paper has not been deposited,
`paper_url` deliberately resolves to the complete public source artifact rather
than inventing a publication.

The catalog keeps three distinctions visible:

- `status`: verified, working, or quarantined;
- `tier`: spine, flagship, or working corpus; and
- `external_validation`: evidence outside the formal proof system.

Those fields must not be collapsed into a single "truth" score.

External validation is recorded separately from repository traffic. A reader
who reproduces a build, finds a counterexample, cites a result, or tests an
empirical interpretation can submit a structured
[external-validation report](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml).
See [`EXTERNAL_VALIDATION.md`](./EXTERNAL_VALIDATION.md) for the evidence
ladder and the current no-inference boundary.

## Indexing the broader private research estate

`catalog/viridis-workspace.example.json` is an allowlisted starting point for
the wider Viridis research workspace. It defaults every discovered record to
`private`, so a normal public build emits none of it. Build an internal catalog
only with the explicit workspace flag:

```bash
python3 -m canon_core build \
  --root /path/to/viridis-workspace \
  --config catalog/viridis-workspace.example.json \
  --output private-catalog.json \
  --include-private
```

The generated private catalog should remain outside the public repository.
Promoting a record requires a curated public configuration plus the rights,
significance, provenance, and human publication gates.

## Reproduce the formal artifacts

[`REPRODUCE.md`](./REPRODUCE.md) separates the current Lean 4.28 corpus build
from the historical Lean 4.24 P0 build and lists the expected audit markers.
Failed reproductions are evidence and should be reported through the same
external-validation pathway as successful ones.

## Human workflow

Research enters through the GitHub issue template. A pull request carries the
formal, significance, provenance, rights, and honest-scope checklists. CI checks
the deterministic catalog, but publication remains a separate human decision.

## Institutional deployment

The same core can generate a private catalog from an organization-specific
configuration. Private hosting, authentication, customer data, and production
signing are intentionally outside this public repository; see
`OPEN_SOURCE_BOUNDARY.md`.
