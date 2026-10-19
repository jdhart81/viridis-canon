"""Materialize a finite, inactive public test fixture without importing it.

Only the exact declared public blobs and source freezes are read. The one
production-root helper is verified as reference evidence and replaced in the
scratch tree by the explicit test-only seam bound by PUBLIC_DEPENDENCIES.json.
This fixture is neither an installed pipeline nor a publisher/authority closure.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re


NAMESPACE = Path("00_lab_infrastructure/gates/audit_remediation")
DEPENDENCIES = NAMESPACE / "PUBLIC_DEPENDENCIES.json"


class FixtureHold(ValueError):
    """Exact source, derivation or scratch-boundary validation failed."""


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _relative(value: object) -> Path:
    if (not isinstance(value, str) or not value or "\\" in value
            or value != PurePosixPath(value).as_posix()
            or PurePosixPath(value).is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise FixtureHold("canonical relative path required")
    return Path(value)


def _regular(root: Path, relative: object) -> bytes:
    path = root / _relative(relative)
    if any(part.is_symlink() for part in (path, *path.parents)) or not path.is_file():
        raise FixtureHold("declared source must be a regular unsymlinked file")
    if not path.resolve().is_relative_to(root.resolve()):
        raise FixtureHold("declared source escapes repository")
    before = path.stat()
    if before.st_size > 4_000_000:
        raise FixtureHold("declared source exceeds finite fixture bound")
    raw = path.read_bytes()
    after = path.stat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)):
        raise FixtureHold("declared source changed while reading")
    return raw


def _object(raw: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise FixtureHold("duplicate manifest key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, UnicodeError) as exc:
        raise FixtureHold("invalid fixture manifest") from exc
    if not isinstance(value, dict):
        raise FixtureHold("fixture manifest object required")
    return value


def _bound(root: Path, relative: object, digest: object) -> bytes:
    if not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None:
        raise FixtureHold("exact source hash required")
    raw = _regular(root, relative)
    if _sha(raw) != digest:
        raise FixtureHold("declared source hash differs")
    return raw


def _derive(before: bytes, patch: bytes, target: str) -> bytes:
    """Apply one uniquely named unified diff section with exact context only."""
    source = before.decode("utf-8").splitlines(keepends=True)
    lines = patch.decode("utf-8").splitlines(keepends=True)
    sections = []
    for index, line in enumerate(lines):
        if line == "--- a/" + target + "\n":
            if index + 1 >= len(lines) or lines[index + 1] != "+++ b/" + target + "\n":
                raise FixtureHold("derived source has mismatched patch headers")
            end = next((j for j in range(index + 2, len(lines))
                        if lines[j].startswith("--- a/")), len(lines))
            sections.append(lines[index + 2:end])
    if len(sections) != 1:
        raise FixtureHold("derived source requires one unique patch section")
    output, cursor, hunks = [], 0, 0
    section, index = sections[0], 0
    while index < len(section):
        header = section[index]
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n", header)
        if match is None:
            raise FixtureHold("unsupported unified patch structure")
        old_start, old_count = int(match[1]), int(match[2] or 1)
        new_start, new_count = int(match[3]), int(match[4] or 1)
        position = old_start if old_count == 0 else old_start - 1
        if position < cursor or position > len(source):
            raise FixtureHold("patch hunk overlaps or escapes source")
        output.extend(source[cursor:position])
        if len(output) != (new_start if new_count == 0 else new_start - 1):
            raise FixtureHold("patch new-line identity differs")
        cursor, consumed, produced = position, 0, 0
        index += 1
        while index < len(section) and not section[index].startswith("@@ "):
            line = section[index]
            if line == "\n":
                # The pinned allocation diff spells empty context as bare LF.
                # Consume and reproduce that exact source line like any context.
                marker, content = " ", "\n"
            elif line and line[0] in {" ", "+", "-"}:
                marker, content = line[0], line[1:]
            else:
                raise FixtureHold("unsupported patch line")
            if marker in {" ", "-"}:
                if cursor >= len(source) or source[cursor] != content:
                    raise FixtureHold("patch context differs")
                cursor += 1
                consumed += 1
            if marker in {" ", "+"}:
                output.append(content)
                produced += 1
            index += 1
        if (consumed, produced) != (old_count, new_count):
            raise FixtureHold("patch hunk counts differ")
        hunks += 1
    if not hunks:
        raise FixtureHold("empty derived-source patch")
    output.extend(source[cursor:])
    return "".join(output).encode("utf-8")


def materialize(repo_root: Path, destination: Path) -> dict:
    """Return root/readbacks for a fresh finite scratch tree; never import it."""
    repo_root, destination = Path(repo_root), Path(destination)
    if repo_root.is_symlink() or not repo_root.is_dir():
        raise FixtureHold("real repository root required")
    if (destination.exists() or destination.is_symlink()
            or any(parent.is_symlink() for parent in destination.parents)
            or destination.resolve().is_relative_to(repo_root.resolve())):
        raise FixtureHold("fresh scratch destination outside repository required")
    raw = _regular(repo_root, DEPENDENCIES.as_posix())
    manifest = _object(raw)
    if (manifest.get("standard") != "VRS-AUDIT-REMEDIATION-PUBLIC-TEST-DEPENDENCIES-1"
            or any(manifest.get(key) is not False
                   for key in ("active", "installed", "production_admitted"))):
        raise FixtureHold("inactive public fixture contract required")
    binding_raw = _bound(repo_root, manifest["source_bindings_path"], manifest["source_bindings_sha256"])
    bindings = _object(binding_raw)
    if (bindings.get("baseline_commit") != manifest.get("baseline_commit")
            or any(bindings.get(key) is not False
                   for key in ("active", "installed", "production_admitted"))):
        raise FixtureHold("source freeze is not an inactive matching baseline")
    freeze_rows = [{key: row[key] for key in ("public_path", "fixture_path", "sha256")}
                   for row in bindings["sources"]]
    if freeze_rows != manifest["source_freezes"]:
        raise FixtureHold("declared source-freeze inventory differs")

    payloads, readbacks = {}, []
    def add(target, data, origin):
        relative = _relative(target).as_posix()
        if relative in payloads:
            raise FixtureHold("duplicate fixture destination")
        payloads[relative] = data
        readbacks.append({"fixture_path": relative, "sha256": _sha(data),
                          "bytes": len(data), "origin": origin})

    # Read and validate every finite source before creating any destination.
    for row in [*manifest["source_freezes"], *manifest["public_sources"]]:
        data = _bound(repo_root, row["public_path"], row["sha256"])
        target = row["fixture_path"]
        if target is not None:
            add(target, data, row["public_path"])
        else:
            readbacks.append({"public_path": row["public_path"], "sha256": _sha(data),
                              "bytes": len(data), "reference_only": True})
    for row in manifest["derived_sources"]:
        before = _bound(repo_root, row["before_path"], row["before_sha256"])
        patch = _bound(repo_root, row["patch_path"], row["patch_sha256"])
        _bound(repo_root, row["binding_manifest_path"], row["binding_manifest_sha256"])
        derived = _derive(before, patch, row["target"])
        if _sha(derived) != row["after_sha256"]:
            raise FixtureHold("derived source does not match exact afterimage")
        if row["fixture_path"] is not None:
            add(row["fixture_path"], derived, row["name"])
        else:
            source = next((item for item in bindings["sources"]
                           if item["fixture_path"] == row["target"]), None)
            if source is None or source.get("installed_base_sha256") != _sha(derived):
                raise FixtureHold("successor installed baseline differs from derivation")
            readbacks.append({"derivation": row["name"], "sha256": _sha(derived),
                              "bytes": len(derived), "reference_only": True})
    for row in manifest["generated_test_inputs"]:
        data = row["content"].encode("utf-8")
        if _sha(data) != row["sha256"]:
            raise FixtureHold("generated test seam differs from reviewed bytes")
        add(row["fixture_path"], data, row["role"])

    # All source bytes were checked without importing candidate/helper code.
    destination.mkdir(parents=True, exist_ok=False)
    for relative, data in payloads.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
        if _regular(destination, relative) != data:
            raise FixtureHold("materialized file differs from reviewed source")
    receipt = {"active": False, "installed": False, "production_admitted": False,
               "dependencies_manifest_sha256": _sha(raw),
               "source_bindings_sha256": _sha(binding_raw), "readbacks": readbacks}
    receipt_raw = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
    with (destination / "MATERIALIZATION.json").open("xb") as stream:
        stream.write(receipt_raw)
    return {"root": destination, "readbacks": readbacks,
            "dependencies_manifest_sha256": _sha(raw),
            "source_bindings_sha256": _sha(binding_raw),
            "materialized_manifest_sha256": _sha(receipt_raw)}
