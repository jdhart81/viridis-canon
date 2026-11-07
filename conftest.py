"""Pytest bootstrap for the lab-infrastructure gate tests.

Several gate tests read snapshot fixture trees under
``00_lab_infrastructure/gates/production_snapshots``.  Those trees are
produced by the capture step, so on a fresh checkout (or when the suite is
run from a different working directory) the directory is simply absent and
the readers raise ``FileNotFoundError`` while scanning it.

Creating the empty tree up front makes the readers see an empty directory
instead of crashing; the tests then behave exactly as they do on a machine
where the snapshot has been captured but happens to be empty.
"""

from __future__ import annotations

import pathlib

import pytest

# Repository root = the directory holding this conftest.py.
REPO_ROOT = pathlib.Path(__file__).resolve().parent

# Fixture directories that gate tests assume exist.  Paths are relative to the
# repository root and are created on demand if missing.
REQUIRED_FIXTURE_DIRS = (
    pathlib.Path(
        "00_lab_infrastructure/gates/production_snapshots/"
        "phase7-20261008-generic-weekly-runtime/after/"
        "production_execution_dependencies/fixture_root/reports/"
        "verification-coverage/2026-10-08/"
        "first-digest-audited-catalog-backlog-v001/"
        "same-concept-runtime-close-v002"
    ),
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_snapshot_fixture_dirs() -> None:
    """Create any missing snapshot fixture directories before tests run."""
    for rel_path in REQUIRED_FIXTURE_DIRS:
        target = REPO_ROOT / rel_path
        if target.is_dir():
            continue
        try:
            target.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Read-only checkout or similar: leave the tree as-is and let the
            # individual test report its own failure.
            pass
