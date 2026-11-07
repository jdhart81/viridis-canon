#!/usr/bin/env python3
"""Environment-independent smoke check for the replication package.

The Lean toolchain (``lake``) is not present in every evaluation environment,
so this script validates only the parts of the repository that run on a stock
Python 3 interpreter:

  * the key figures/manuscript files are present, and
  * every tracked ``*.py`` file parses.

If a Lean toolchain *is* available, run ``lake build`` separately; this script
deliberately does not shell out to it.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

REQUIRED = (
    "README.md",
    "REPRODUCE.md",
    "EcoChain_DendriticCorridor.lean",
    "PerennialCorridor.lean",
    "UniversalWaterfilling.lean",
    "formalization.yaml",
)

SKIP_DIRS = {".git", ".lake", "__pycache__", ".venv", "node_modules"}


def _iter_python_files(root: pathlib.Path):
    for path in sorted(root.rglob("*.py")):
        if SKIP_DIRS.intersection(path.parts):
            continue
        yield path


def main() -> int:
    failures = []

    for name in REQUIRED:
        if not (ROOT / name).exists():
            failures.append("missing required file: %s" % name)

    checked = 0
    for path in _iter_python_files(ROOT):
        checked += 1
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            failures.append("unreadable: %s: %s" % (path.relative_to(ROOT), exc))
            continue
        try:
            compile(source, str(path), "exec")
        except SyntaxError as exc:
            failures.append(
                "syntax error: %s:%s: %s"
                % (path.relative_to(ROOT), exc.lineno, exc.msg)
            )

    if failures:
        for item in failures:
            print("FAIL %s" % item)
        print("%d failure(s)" % len(failures))
        return 1

    print(
        "ok: %d required file(s) present, %d python file(s) parsed"
        % (len(REQUIRED), checked)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
