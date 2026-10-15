#!/usr/bin/env python3
"""Scan explicit files, receipt directories, or Git commit blobs for a token.

The credential is read internally from --token-file (or VIRIDIS_CORE_ROOT).
Only counts and sanitized paths are emitted. The credential source itself is
excluded, symlinks are refused, and unreadable inputs fail closed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


class ScanError(RuntimeError):
    pass


def read_token(path: Path) -> bytes:
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        raise ScanError("credential source unavailable") from None
    # This matches the existing local Markdown credential convention.
    candidates = re.findall(r"[A-Za-z0-9_\-]{30,}", raw.replace("\\", ""))
    if not candidates:
        raise ScanError("credential shape validation failed")
    return max(candidates, key=len).encode("ascii")


def count_stream(handle, token: bytes, chunk_size: int = 1024 * 1024) -> int:
    """Count exact non-overlapping matches, including chunk boundaries."""
    if not token or chunk_size < 1:
        raise ScanError("invalid stream scan parameters")
    pending = b""
    count = 0
    while chunk := handle.read(chunk_size):
        pending += chunk
        start = 0
        while (found := pending.find(token, start)) >= 0:
            count += 1
            start = found + len(token)
        pending = pending[max(start, len(pending) - len(token) + 1):]
    return count


def scan_paths(paths: list[Path], token: bytes, token_file: Path) -> dict:
    excluded = token_file.resolve()
    seen: set[Path] = set()
    hits: list[dict] = []
    scanned = 0
    errors: list[str] = []
    for root in paths:
        if not root.exists() and not root.is_symlink():
            errors.append(str(root))
            continue
        entries = [root]
        if root.is_dir() and not root.is_symlink():
            def walk_error(exc):
                errors.append(str(exc.filename or root))
            entries = []
            for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
                for name in list(dirs):
                    if (Path(directory) / name).is_symlink():
                        errors.append(str(Path(directory) / name))
                        dirs.remove(name)
                entries.extend(Path(directory) / name for name in files)
        for path in entries:
            if path.is_symlink():
                errors.append(str(path))
                continue
            resolved = path.resolve()
            if resolved == excluded or resolved in seen:
                continue
            seen.add(resolved)
            try:
                if not path.is_file():
                    errors.append(str(path))
                    continue
                with path.open("rb") as handle:
                    count = count_stream(handle, token) + os.fsencode(path).count(token)
                scanned += 1
                if count:
                    hits.append({"path": str(path), "count": count})
            except OSError:
                errors.append(str(path))
    return {"scanned_files": scanned, "hit_count": sum(row["count"] for row in hits),
            "paths": hits, "unreadable_paths": errors}


def git_bytes(repo: Path, arguments: list[str]) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *arguments], capture_output=True)
    if result.returncode:
        raise ScanError("Git scan input unavailable")
    return result.stdout


def scan_commit(repo: Path, revision: str, token: bytes) -> dict:
    # Resolve first, so caller input cannot become a Git option.
    oid = git_bytes(repo, ["rev-parse", "--verify", "--end-of-options", revision + "^{commit}"]).strip()
    if re.fullmatch(rb"[0-9a-f]{40,64}", oid) is None:
        raise ScanError("Git commit identity invalid")
    commit = oid.decode("ascii")
    hits = []
    scanned = 0
    commit_body = git_bytes(repo, ["cat-file", "commit", commit])
    if count := commit_body.count(token):
        hits.append({"path": f"git:{commit}:COMMIT_MESSAGE", "count": count})
    entries = git_bytes(repo, ["ls-tree", "-rz", commit]).split(b"\0")
    counts: dict[bytes, int] = {}
    # One persistent process avoids a subprocess per historical runtime copy.
    process = subprocess.Popen(["git", "-C", str(repo), "cat-file", "--batch"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for entry in entries:
            if not entry:
                continue
            header, name = entry.split(b"\t", 1)
            _mode, kind, blob = header.split()
            if kind != b"blob":
                continue
            scanned += 1
            if blob not in counts:
                process.stdin.write(blob + b"\n")
                process.stdin.flush()
                response = process.stdout.readline().split()
                if len(response) != 3 or response[0] != blob or response[1] != b"blob":
                    raise ScanError("Git batch blob unavailable")
                remaining = int(response[2])
                class LimitedReader:
                    def read(self, size):
                        nonlocal remaining
                        if not remaining:
                            return b""
                        data = process.stdout.read(min(size, remaining))
                        if not data:
                            raise ScanError("Git batch blob truncated")
                        remaining -= len(data)
                        return data
                counts[blob] = count_stream(LimitedReader(), token)
                if process.stdout.read(1) != b"\n":
                    raise ScanError("Git batch framing invalid")
            if count := counts[blob] + name.count(token):
                hits.append({"path": f"git:{commit}:" + os.fsdecode(name), "count": count})
        process.stdin.close()
        if process.wait() != 0:
            raise ScanError("Git batch scan failed")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()
        process.stdout.close()
        process.stderr.close()
        if not process.stdin.closed:
            process.stdin.close()
    return {"scanned_files": scanned, "hit_count": sum(row["count"] for row in hits),
            "paths": hits, "unreadable_paths": []}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--commit", action="append", default=[])
    args = parser.parse_args(argv)
    token = b""
    try:
        token_file = args.token_file
        if token_file is None:
            root = os.environ.get("VIRIDIS_CORE_ROOT")
            if not root:
                raise ScanError("set --token-file or VIRIDIS_CORE_ROOT")
            token_file = Path(root) / "secrets/Zenodo_API/Zenodo_token.md"
        token = read_token(token_file)
        if not args.paths and not args.commit:
            raise ScanError("provide explicit paths or --commit")
        reports = [scan_paths(args.paths, token, token_file)]
        reports.extend(scan_commit(args.repo, ref, token) for ref in args.commit)
        result = {
            "hit_count": sum(report["hit_count"] for report in reports),
            "scanned_files": sum(report["scanned_files"] for report in reports),
            "paths": [row for report in reports for row in report["paths"]],
            "unreadable_paths": [path for report in reports for path in report["unreadable_paths"]],
        }
        # Paths can contain a token too. Sanitize the complete output envelope.
        text = json.dumps(result, sort_keys=True, ensure_ascii=False)
        print(text.replace(token.decode("ascii"), "***"))
        return 2 if result["unreadable_paths"] else int(bool(result["hit_count"]))
    except Exception as exc:
        # No exception text or input bytes leave this process.
        print(json.dumps({"scan_error_count": 1, "error_type": type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
