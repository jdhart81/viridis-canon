"""Read exact historical test source from local Git; never import a runtime.

The selected V012 source keeps its canonical Git namespace and semantic labels.
This module changes only how predecessor test fixtures obtain immutable bytes.
No filesystem extraction, source rehydration, network or admission is performed.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

RELEASE = Path(__file__).resolve().parents[1]
REPO = RELEASE.parents[2]
HISTORY = RELEASE / "RUNTIME_HISTORY.json"
PREFIX = "00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_"


class RuntimeHistoryError(ValueError):
    pass


def _git(repo: Path, *arguments: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True,
                            check=False, timeout=15,
                            env={**os.environ, "GIT_NO_LAZY_FETCH": "1",
                                 "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0",
                                 "GIT_OPTIONAL_LOCKS": "0"})
    if result.returncode:
        raise RuntimeHistoryError("required immutable local Git object unavailable")
    return result.stdout


def historical_bytes(version: str, filename: str, *, repo: Path = REPO,
                     manifest: Path = HISTORY) -> bytes:
    """Return one hash-bound source blob after checking its merge-tree path."""
    if (not isinstance(version, str) or re.fullmatch(r"v[0-9]{3}", version) is None
            or not isinstance(filename, str) or not filename
            or "\\" in filename or PurePosixPath(filename).as_posix() != filename
            or any(part in {"", ".", ".."} for part in filename.split("/"))
            or filename.startswith("/")):
        raise RuntimeHistoryError("exact historical version and safe relative filename required")
    try:
        history = json.loads(Path(manifest).read_bytes())
        if not isinstance(history, dict) or history.get("schema") != "VRS-RUNTIME-HISTORY-1":
            raise RuntimeHistoryError("reviewed runtime history manifest required")
        versions = history.get("versions")
        if not isinstance(versions, list):
            raise RuntimeHistoryError("exact historical version table required")
        matches = [row for row in versions if isinstance(row, dict) and row.get("version") == version]
        if len(matches) != 1:
            raise RuntimeHistoryError("unique historical version required")
        entry = matches[0]; commit = entry.get("merge_commit"); tree = entry.get("tree_sha")
        if not all(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value) for value in (commit, tree)):
            raise RuntimeHistoryError("complete immutable commit and tree required")
        path = PREFIX + version + "/" + filename
        files = entry.get("files")
        if not isinstance(files, list):
            raise RuntimeHistoryError("exact historical blob inventory required")
        matches = [row for row in files if isinstance(row, dict) and row.get("path") == path]
        if len(matches) != 1:
            raise RuntimeHistoryError("unique historical file binding required")
        row = matches[0]; blob = row.get("blob_sha")
        if (row.get("type") != "blob" or row.get("mode") != "100644"
                or not isinstance(blob, str) or re.fullmatch(r"[a-f0-9]{40}", blob) is None):
            raise RuntimeHistoryError("regular immutable historical blob required")
        repo = Path(repo)
        observed_tree = _git(repo, "rev-parse", "--verify", "--end-of-options", commit + ":" + PREFIX + version).strip().decode("ascii")
        if observed_tree != tree:
            raise RuntimeHistoryError("historical version tree differs from reviewed manifest")
        listing = _git(repo, "ls-tree", "-z", commit, "--", path)
        expected = ("100644 blob " + blob + "\t" + path).encode() + b"\0"
        if listing != expected:
            raise RuntimeHistoryError("historical commit path/blob binding differs")
        raw = _git(repo, "cat-file", "blob", blob)
        if hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != blob:
            raise RuntimeHistoryError("historical blob bytes differ from reviewed identity")
        return raw
    except RuntimeHistoryError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, subprocess.SubprocessError):
        raise RuntimeHistoryError("historical source cannot be read from exact local Git evidence") from None
