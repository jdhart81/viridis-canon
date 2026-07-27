# Reproduce the Viridis Canon

The repository maintains two explicit Lean environments:

- the current spine and series package under Lean 4.28; and
- the foundational P0 module under its historical Lean 4.24 / Mathlib
  `f897ebcf72cd16f89ab4577d0c826cd14afaafc7` pin.

Run both. A successful current build does not substitute for the historical P0
build.

## Clone

```bash
git clone https://github.com/jdhart81/viridis-canon.git
cd viridis-canon
```

## Current corpus

```bash
lake exe cache get
lake build
```

Expected output includes:

```text
Axiom audit PASSED
```

## Historical P0

```bash
cd compat/v4_24
lake exe cache get
lake build
```

Expected output includes:

```text
P0 axiom audit PASSED
```

The audit covers 72 P0 declarations and permits only `propext`,
`Classical.choice`, and `Quot.sound`.

## Catalog and portal

From the repository root:

```bash
python3 tools/build_research_portal.py --check
python3 -m unittest discover -s tests -v
```

The command reports the current record count and digest and fails if they do
not match the checked-in catalog.

## Report the result

Open an
[external-validation report](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml)
with the commit SHA, operating system, toolchain output, and relevant logs.
Clean, failed, and inconclusive reproductions are all preserved as evidence.
