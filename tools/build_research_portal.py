#!/usr/bin/env python3
"""Build the GitHub Pages data file from the checked-in Lean canon."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canon_core.catalog import build_catalog, validate_catalog, write_catalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "data" / "catalog.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the checked-in catalog differs from a fresh deterministic build",
    )
    args = parser.parse_args()

    if args.check:
        expected = build_catalog(args.root)
        errors = validate_catalog(expected)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        if not args.output.exists():
            print(f"ERROR: missing generated catalog: {args.output}")
            return 1
        actual = json.loads(args.output.read_text(encoding="utf-8"))
        if actual != expected:
            print("ERROR: docs/data/catalog.json is stale; rebuild it")
            return 1
        print(
            f"catalog current: {actual['stats']['records']} records, "
            f"digest {actual['catalog_digest'][:16]}"
        )
        return 0

    document = write_catalog(args.root, args.output)
    print(
        f"wrote {args.output}: {document['stats']['records']} records, "
        f"digest {document['catalog_digest'][:16]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
