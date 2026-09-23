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

    build_os = sub.add_parser("build-os", help="compile function manifests into the Viridis OS bundle")
    build_os.add_argument("--root", type=Path, default=Path("."))
    build_os.add_argument("--out", type=Path, default=Path("os-bundle"))
    build_os.add_argument("--source-ref", default="", help="commit SHA recorded in the bundle (default: git HEAD)")
    build_os.add_argument("--release", default="", help="release tag recorded in the bundle (default: catalog release)")
    build_os.add_argument("--skip-parity", action="store_true", help="do not replay os/parity fixtures")

    check_fn = sub.add_parser("validate-functions", help="validate every function.json without building")
    check_fn.add_argument("--root", type=Path, default=Path("."))

    verify_os = sub.add_parser("verify-os", help="recompute an OS bundle's digest and run its self-test")
    verify_os.add_argument("bundle", type=Path)
    verify_os.add_argument("--expect-digest", default="")
    return parser


def _git_head(root: Path) -> str:
    import subprocess

    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


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

    if args.command == "build-os":
        from .os_build import BuildError, build_os

        try:
            result = build_os(
                args.root,
                args.out,
                source_ref=args.source_ref or _git_head(args.root),
                release=args.release,
                replay_parity=not args.skip_parity,
            )
        except BuildError as error:
            for line in error.errors:
                print(f"ERROR: {line}")
            return 1
        stats = result["stats"]
        print(
            f"os bundle built: {stats['functions']} functions ({stats['runnable']} runnable, "
            f"{stats['admitted']} admitted, {stats['blocked']} blocked), "
            f"{stats['catalog_records']} reference records, digest {result['digest']}"
        )
        for key, value in sorted(result["rejected"].items()):
            print(f"WARNING: function '{key}' left out of the callable set (recorded in the bundle): {'; '.join(value['errors'])}")
        return 0

    if args.command == "validate-functions":
        from .function_schema import RepoContext, discover_manifests, validate_admissions_ledger, validate_manifest

        root = args.root.resolve()
        context = RepoContext.load(root)
        errors: list[str] = []
        manifests = {}
        for path in discover_manifests(root):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(validate_manifest(manifest, path, context))
            manifests[manifest.get("id")] = manifest
        errors.extend(validate_admissions_ledger(context, manifests))
        for error in errors:
            print(f"ERROR: {error}")
        if not errors:
            print(f"functions valid: {len(manifests)} manifests")
        return 1 if errors else 0

    if args.command == "verify-os":
        import subprocess
        import sys

        from .os_build import bundle_digest

        bundle = args.bundle.resolve()
        recorded = (bundle / "DIGEST").read_text(encoding="utf-8").strip()
        actual = bundle_digest(bundle)
        problems = []
        if actual != recorded:
            problems.append(f"DIGEST {recorded} does not match the files ({actual})")
        if args.expect_digest and args.expect_digest != actual:
            problems.append(f"bundle digest {actual} is not the pinned {args.expect_digest}")
        proc = subprocess.run([sys.executable, "-I", "-B", str(bundle / "run.py"), "--self-test"], capture_output=True, text=True)
        if proc.returncode != 0:
            problems.append(f"self-test failed: {proc.stdout.strip()} {proc.stderr.strip()[:500]}")
        for problem in problems:
            print(f"ERROR: {problem}")
        if not problems:
            print(f"os bundle valid: digest {actual}; {proc.stdout.strip()}")
        return 1 if problems else 0

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
