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

## Machine interface

GitHub Pages exposes `data/catalog.json`. The document and every record carry
SHA-256 digests over canonical JSON. Consumers can recompute these using
`canon_core.canonical`.

The catalog keeps three distinctions visible:

- `status`: verified, working, or quarantined;
- `tier`: spine, flagship, or working corpus; and
- `external_validation`: evidence outside the formal proof system.

Those fields must not be collapsed into a single "truth" score.

## Human workflow

Research enters through the GitHub issue template. A pull request carries the
formal, significance, provenance, rights, and honest-scope checklists. CI checks
the deterministic catalog, but publication remains a separate human decision.

## Institutional deployment

The same core can generate a private catalog from an organization-specific
configuration. Private hosting, authentication, customer data, and production
signing are intentionally outside this public repository; see
`OPEN_SOURCE_BOUNDARY.md`.
