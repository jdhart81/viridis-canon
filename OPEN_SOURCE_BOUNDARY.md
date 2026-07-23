# Open-source boundary

Viridis Canon is the public research and verification substrate. It is not the
ViridisConservation.com product and it is not the production certificate
authority.

## Public in this repository

- Lean source, axiom audits, and integrity gates
- Canon schemas, canonical serialization, and digest verification
- Deterministic public-catalog builder
- Public research explorer and its generated JSON data
- Submission templates, review checklists, and release documentation
- Metadata and fingerprints for records that have been cleared for public use

## Never public here

- Production private signing keys or secret-manager exports
- Customer evidence, parcel data, identities, or private certificates
- ViridisConservation.com application source
- Billing, settlement, reviewer operations, or customer analytics
- Private institutional research workspaces
- Unpublished working research that has not passed a rights and scope review
- Third-party papers, datasets, or software without redistribution rights

The core can index records marked `private`, but the public catalog builder
emits only records whose visibility is explicitly `public`. The catalog tests
fail if a non-public record reaches the generated Pages data.

## Product boundary

The public repository supplies inspectability and interoperability. Commercial
services may charge for private workspaces, managed evidence ingestion, human
review, institutional governance, integrations, service levels, and authorized
certificate issuance.

Open code does not grant authority to issue a Viridis mark. Authority depends
on the published trust root, certificate policy, and custody of the production
private key.
