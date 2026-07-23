# Security policy

## Report a vulnerability

Please use GitHub's private vulnerability reporting for this repository:

`https://github.com/jdhart81/viridis-canon/security/advisories/new`

Do not open a public issue for a suspected secret exposure, signature bypass,
catalog-integrity flaw, or publication-gate bypass.

## Trust boundary

- This repository must never contain a production private signing key.
- Catalog records are deterministic metadata, not authorization tokens.
- GitHub Pages is a public, read-only research surface.
- A green build does not publish a research result to Zenodo or authorize a
  Viridis certificate.
- Formal verification and cryptographic integrity do not establish empirical
  validity.

If a private key is ever committed, treat it as compromised: revoke the
associated trust root, rotate the key, and reissue affected credentials under a
new key identifier.
