"""Command-line interface for building and verifying a research catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog import validate_catalog, write_catalog


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="viridis-canon")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build a deterministic public catalog")
    build.add_argument("--root", type=Path, default=Path("."))
    build.add_argument("--config", type=Path)
    build.add_argument("--output", type=Path, default=Path("docs/data/catalog.json"))
    build.add_argument(
        "--include-private",
        action="store_true",
        help="build a local workspace catalog instead of a public release",
    )

    verify = sub.add_parser("verify", help="verify an existing catalog and its digests")
    verify.add_argument("catalog", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "build":
        document = write_catalog(
            args.root,
            args.output,
            config_path=args.config,
            include_private=args.include_private,
        )
        stats = document["stats"]
        print(
            f"catalog built: {stats['records']} records, "
            f"{stats['verified']} verified, digest {document['catalog_digest'][:16]}"
        )
        return 0

    document = json.loads(args.catalog.read_text(encoding="utf-8"))
    errors = validate_catalog(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"catalog valid: {len(document['records'])} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
