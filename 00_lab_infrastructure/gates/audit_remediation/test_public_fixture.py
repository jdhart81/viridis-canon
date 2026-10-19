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


ASSEMBLER_TARGET = "RESEARCH_PIPELINE_v2/assemble_saturday_candidate.py"
ASSEMBLER_AFTER_SHA256 = "d60371087d6db196069ab88bf25279ac0b7791c7e9ba38170e63728fa45458b7"
BLANK_CONTEXT_PATCH = (
    b"--- a/example.py\n+++ b/example.py\n@@ -1,3 +1,3 @@\n"
    b" one\n\n-two\n+three\n"
)


def canonical_assembler_inputs():
    manifest = json.loads((REPOSITORY / DEPENDENCIES).read_bytes())
    row = next(item for item in manifest["derived_sources"]
               if item["name"] == "assembler-installed-source")
    assert row["target"] == ASSEMBLER_TARGET
    assert row["before_sha256"] == "a94df6572ad68ada2f7d524aabde3d9f3ff1d6f69c7440a5f47653c71185c7c6"
    assert row["patch_sha256"] == "6f3c3777796df001f6f958ec8872197635e40b6c966e0da8090ac3793cc0fca1"
    assert row["after_sha256"] == ASSEMBLER_AFTER_SHA256
    before = (REPOSITORY / row["before_path"]).read_bytes()
    patch = (REPOSITORY / row["patch_path"]).read_bytes()
    assert hashlib.sha256(before).hexdigest() == row["before_sha256"]
    assert hashlib.sha256(patch).hexdigest() == row["patch_sha256"]
    return before, patch


def test_canonical_allocation_patch_derives_exact_installed_assembler():
    before, patch = canonical_assembler_inputs()
    assert b"\n" in patch.splitlines(keepends=True)
    derived = _derive(before, patch, ASSEMBLER_TARGET)
    assert hashlib.sha256(derived).hexdigest() == ASSEMBLER_AFTER_SHA256


def test_bare_lf_context_is_consumed_and_preserved_exactly():
    assert _derive(b"one\n\ntwo\n", BLANK_CONTEXT_PATCH, "example.py") == b"one\n\nthree\n"


@pytest.mark.parametrize("blank", [b"nonempty\n", b" \n", b"\r\n"])
def test_bare_lf_context_rejects_a_different_source_line(blank):
    with pytest.raises(FixtureHold, match="patch context differs"):
        _derive(b"one\n" + blank + b"two\n", BLANK_CONTEXT_PATCH, "example.py")


@pytest.mark.parametrize("malformed", [b"\r\n", b"\t\n", b"unmarked\n"])
def test_only_exact_bare_lf_is_accepted_as_unmarked_context(malformed):
    patch = BLANK_CONTEXT_PATCH.replace(b" one\n\n", b" one\n" + malformed)
    with pytest.raises(FixtureHold, match="unsupported patch line"):
        _derive(b"one\n\ntwo\n", patch, "example.py")


@pytest.mark.parametrize("counts", [b"@@ -1,2 +1,3 @@", b"@@ -1,3 +1,2 @@", b"@@ -1,4 +1,3 @@"])
def test_bare_lf_context_still_counts_in_both_hunk_totals(counts):
    patch = BLANK_CONTEXT_PATCH.replace(b"@@ -1,3 +1,3 @@", counts)
    with pytest.raises(FixtureHold, match="patch hunk counts differ"):
        _derive(b"one\n\ntwo\n", patch, "example.py")


def test_canonical_assembler_afterimage_pin_drift_stops_before_writes(tmp_path):
    repo, manifest = synthetic_repository(tmp_path)
    row = next(item for item in manifest["derived_sources"]
               if item["name"] == "assembler-installed-source")
    assert row["after_sha256"] == ASSEMBLER_AFTER_SHA256
    row["after_sha256"] = "0" * 64
    write_manifest(repo, manifest)
    destination = tmp_path / "scratch"
    with pytest.raises(FixtureHold, match="derived source does not match exact afterimage"):
        materialize(repo, destination)
    assert not destination.exists()
