"""Exercise only materialization and its exact byte/path boundaries."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

import pytest

from public_fixture import DEPENDENCIES, FixtureHold, _derive, materialize


REPOSITORY = Path(__file__).resolve().parents[3]


def synthetic_repository(tmp_path):
    """Copy the finite declared source inventory as data, without imports."""
    root = tmp_path / "repo"
    manifest = json.loads((REPOSITORY / DEPENDENCIES).read_bytes())
    names = {DEPENDENCIES.as_posix(), manifest["source_bindings_path"]}
    names.update(row["public_path"] for row in
                 [*manifest["source_freezes"], *manifest["public_sources"]])
    for row in manifest["derived_sources"]:
        names.update(row[key] for key in
                     ("before_path", "patch_path", "binding_manifest_path"))
    for name in sorted(names):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPOSITORY / name, target)
    return root, manifest


def write_manifest(root, value):
    (root / DEPENDENCIES).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def test_materializes_exact_finite_sources_and_test_only_seams(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    result = materialize(repo, tmp_path / "scratch")
    root = result["root"]
    receipt = json.loads((root / "MATERIALIZATION.json").read_bytes())
    assert all(receipt[key] is False for key in ("active", "installed", "production_admitted"))
    assert result["readbacks"] == receipt["readbacks"]
    assert result["materialized_manifest_sha256"] == hashlib.sha256(
        (root / "MATERIALIZATION.json").read_bytes()).hexdigest()
    for row in result["readbacks"]:
        if "fixture_path" in row:
            assert hashlib.sha256((root / row["fixture_path"]).read_bytes()).hexdigest() == row["sha256"]
    seam = root / "RESEARCH_PIPELINE_v2/viridis_paths.py"
    original = next(row for row in manifest["public_sources"]
                    if row["public_path"].endswith("/viridis_paths.py"))
    assert original["fixture_path"] is None
    assert hashlib.sha256(seam.read_bytes()).hexdigest() != original["sha256"]
    assert "TEST_FIXTURE_ONLY = True" in seam.read_text()
    for name in ("phase7_audit_policy.py", "publication_preservation.py"):
        assert (root / "_ZENODO_DEPOSITS" / name).read_text().startswith("raise RuntimeError(")
    assert not (root / "comparator-deploy/engine3_align_challenge.py").exists()
    assert (root / "RESEARCH_PIPELINE_v2/engine3_align_challenge.py").is_file()


def test_source_drift_stops_before_destination_creation(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    changed = repo / manifest["source_freezes"][0]["public_path"]
    changed.write_bytes(changed.read_bytes() + b"\n")
    destination = tmp_path / "scratch"
    with pytest.raises(FixtureHold, match="source hash differs"):
        materialize(repo, destination)
    assert not destination.exists()


def test_symlinked_source_is_refused_before_materialization(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    source = repo / manifest["public_sources"][0]["public_path"]
    saved = source.with_suffix(".saved")
    source.rename(saved)
    source.symlink_to(saved)
    with pytest.raises(FixtureHold, match="regular unsymlinked"):
        materialize(repo, tmp_path / "scratch")
    assert not (tmp_path / "scratch").exists()


def test_existing_or_repository_destination_is_refused(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    existing = tmp_path / "existing"
    existing.mkdir()
    for destination in (existing, repo / "scratch"):
        with pytest.raises(FixtureHold, match="fresh scratch destination"):
            materialize(repo, destination)
    assert not (repo / "scratch").exists()


def test_duplicate_materialized_role_fails_before_writes(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    manifest["public_sources"][0]["fixture_path"] = manifest["source_freezes"][0]["fixture_path"]
    write_manifest(repo, manifest)
    with pytest.raises(FixtureHold, match="duplicate fixture destination"):
        materialize(repo, tmp_path / "scratch")
    assert not (tmp_path / "scratch").exists()


def test_unsafe_materialized_path_fails_before_writes(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    manifest["public_sources"][0]["fixture_path"] = "../escape.py"
    write_manifest(repo, manifest)
    with pytest.raises(FixtureHold, match="canonical relative path"):
        materialize(repo, tmp_path / "scratch")
    assert not (tmp_path / "scratch").exists()
    assert not (tmp_path / "escape.py").exists()


def test_activation_flag_cannot_be_inherited_from_source_manifest(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    manifest["installed"] = True
    write_manifest(repo, manifest)
    with pytest.raises(FixtureHold, match="inactive public fixture"):
        materialize(repo, tmp_path / "scratch")


def test_derivation_requires_unique_target_and_exact_context():
    original = b"one\ntwo\n"
    patch = b"--- a/example.py\n+++ b/example.py\n@@ -1,2 +1,2 @@\n one\n-two\n+three\n"
    assert _derive(original, patch, "example.py") == b"one\nthree\n"
    with pytest.raises(FixtureHold, match="one unique patch section"):
        _derive(original, patch + patch, "example.py")
    with pytest.raises(FixtureHold, match="patch context differs"):
        _derive(b"different\ntwo\n", patch, "example.py")
