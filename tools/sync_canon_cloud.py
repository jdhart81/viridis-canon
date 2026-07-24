"""Upload the deterministic public catalog to a configured Canon Cloud."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()
    cli.add_argument("--catalog", type=Path, required=True)
    cli.add_argument("--url", default=os.environ.get("CANON_CLOUD_URL", ""))
    cli.add_argument(
        "--secret",
        default=os.environ.get("CANON_CLOUD_SYNC_SECRET", ""),
    )
    cli.add_argument("--source-ref", default=os.environ.get("GITHUB_SHA", ""))
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if not args.url or not args.secret:
        print("Canon Cloud sync skipped: URL or secret is not configured")
        return 0
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    body = json.dumps(
        {
            "source_ref": args.source_ref,
            "catalog": catalog,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    request = Request(
        args.url.rstrip("/") + "/api/integrations/catalog-sync",
        data=body,
        headers={
            "Authorization": f"Bearer {args.secret}",
            "Content-Type": "application/json",
            "User-Agent": "viridis-canon-sync/1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"Canon Cloud sync failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Canon Cloud sync complete: "
        f"{result['imported']} imported, {result['unchanged']} unchanged"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
