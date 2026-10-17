"""Read truthful W42 publication evidence without importing any Core source.

Publication registration establishes exact published bytes, never certification
of the newly labelled artifacts. All returned data is PRIVATE intake evidence;
public Canon payloads require separately Root-reviewed public path mappings.
"""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys

SHA = re.compile(r"[0-9a-f]{64}")
DOI = re.compile(r"10\.5281/zenodo\.([0-9]+)")
LABELLED_STANDARD = "VRS-METHODS-DIGEST-UNCERTIFIED-ARTIFACT-ENVELOPE-1"
ARTIFACT_LABEL = "UNCERTIFIED — no issuer-produced Viridis Comparator certificate binds the exact bytes of this derived manuscript. Attached certificates cover only their exact sealed predecessors and quoted formal statements under their stated hypotheses. They do not certify this new PDF, its prose, the historical manuscript, or empirical claims. Results remain conditional on the stated model assumptions."
STATEMENT_SCOPE = "EXACT_SEALED_PREDECESSOR_AND_QUOTED_FORMAL_STATEMENTS_ONLY"
ROOT_STANDARD = "VRS-APPROVED-RELEASE-SYNC-ROOT-SCOPE-1"
EXIT_STANDARD = "VRS-W42-GENUINE-OUTER-SOURCE-EXIT-1"
GUARD_SHA256 = "7d19e7b3456af246139a43598d233eb947dc626707a9c8bac73e15a28ff2b3df"
FROZEN_WEEKEND_SHA256 = "36b23f17c4ef4a9758f587caeb52f16c72d149fb49776e4e2fc920f5d2e32bec"


class PublicationHold(ValueError): pass


def need(value, reason):
    if not value: raise PublicationHold(reason)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def encoded(value): return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False).encode() + b"\n"


def fixed_command(root, scope):
    root = Path(root).resolve(strict=True)
    output = Path(scope.get("publisher_output", ""))
    need(output.is_absolute() and output.is_relative_to(root / "reports/verification-coverage") and ".." not in output.parts
         and not any(path.is_symlink() for path in (output, *output.parents)), "HOLD_FIXED_W42_OUTPUT")
    config, _ = read_bound(root, scope["config"])
    return [sys.executable, "-B", str(root / "_ZENODO_DEPOSITS/guard_methods_digest_release.py"), "--config", str(config),
            "--expected-config-sha256", scope["config"]["sha256"], "--go", "--output", str(output)]


def path_at(root, value, *, directory=False):
    root = Path(root).resolve(strict=True)
    need(isinstance(value, str) and value and ".." not in Path(value).parts, "HOLD_W42_PATH")
    path = Path(value) if Path(value).is_absolute() else root / value
    need(path.is_relative_to(root) and not any(p.is_symlink() for p in (path, *path.parents)), "HOLD_W42_PATH")
    need(path.is_dir() if directory else path.is_file(), "HOLD_W42_REGULAR_INPUT")
    return path


def read_bound(root, binding):
    need(isinstance(binding, dict) and set(binding) == {"path", "sha256"}
         and isinstance(binding["sha256"], str) and SHA.fullmatch(binding["sha256"]), "HOLD_W42_FILE_BINDING")
    path = path_at(root, binding["path"])
    before = path.stat(); raw = path.read_bytes(); after = path.stat()
    identity = lambda st: (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns)
    need(identity(before) == identity(after) and raw == path.read_bytes() and digest(raw) == binding["sha256"], "HOLD_W42_INPUT_DRIFT")
    return path, raw


def binding(root, path):
    path = path_at(root, str(path))
    return {"path": str(path.relative_to(Path(root).resolve(strict=True))), "sha256": digest(path.read_bytes())}


def evidence_binding(root, value):
    """Normalize only the producer's closed optional-byte evidence binding.

    methods_digest_v2 emits three-key note/PB evidence; registrar_v3 slices its
    operational child binding to two keys. Operational scope/exit inputs remain
    strictly two-key bindings everywhere else.
    """
    need(isinstance(value, dict) and set(value) in ({"path", "sha256"}, {"path", "sha256", "bytes"}),
         "HOLD_W42_EVIDENCE_FILE_BINDING")
    normal = {key: value[key] for key in ("path", "sha256")}
    _, raw = read_bound(root, normal)
    if "bytes" in value:
        need(type(value["bytes"]) is int and value["bytes"] == len(raw), "HOLD_W42_EVIDENCE_BYTE_SIZE")
    return normal


def object_at(root, value):
    _, raw = read_bound(root, value)
    def unique(pairs):
        result = {}
        for key, item in pairs:
            need(key not in result, "HOLD_W42_DUPLICATE_JSON_KEY")
            result[key] = item
        return result
    try: result = json.loads(raw, object_pairs_hook=unique)
    except (ValueError, TypeError): raise PublicationHold("HOLD_W42_JSON") from None
    need(isinstance(result, dict), "HOLD_W42_JSON_OBJECT")
    return result


def root_scope(root, scope_binding):
    import root_scope as reviewed
    return reviewed.load(root, scope_binding)


def source_snapshot(root, scope_binding):
    """Read fixed installed guard/20+1/130/config/profile identities, no imports."""
    root = Path(root).resolve(strict=True); scope = root_scope(root, scope_binding)
    guard, _ = read_bound(root, scope.get("publisher_guard"))
    need(guard == root / "_ZENODO_DEPOSITS/guard_methods_digest_release.py"
         and scope["publisher_guard"]["sha256"] == GUARD_SHA256, "HOLD_FIXED_W42_OUTER_GUARD_REQUIRED")
    config = object_at(root, scope.get("config"))
    need(config.get("canonical_root") == str(root), "HOLD_W42_CONFIG_ROOT")
    profile_binding = config.get("packaging_profile")
    profile_path, _ = read_bound(root, profile_binding)
    need(profile_path == root / "_ZENODO_DEPOSITS/standalone_pdf_runtime/CURRENT_PACKAGING_PROFILE.json", "HOLD_FIXED_W42_PROFILE")
    profile = object_at(root, profile_binding)
    nomination_path = root / "_ZENODO_DEPOSITS/standalone_pdf_runtime/INSTALLATION_NOMINATION.json"
    nomination_binding = binding(root, nomination_path); nomination = object_at(root, nomination_binding)
    need(nomination.get("profile") == profile_binding
         and nomination.get("standard") == "VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-13"
         and nomination.get("status") == "EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING"
         and profile.get("standard") == "VRS-DIGEST-ARCHIVAL-PDF-PACKAGING-PROFILE-1"
         and profile.get("status") == "INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS"
         and profile.get("default_routes") == {"digest": "invoke_digest_v2.py"}
         and profile.get("canonical_root") == str(root), "HOLD_W42_NOMINATED_PROFILE")
    modules, shared = profile.get("modules"), profile.get("shared_dependencies")
    need(isinstance(modules, list) and len(modules) == 20 and isinstance(shared, list) and len(shared) == 1,
         "HOLD_W42_CURRENT20_PLUS1")
    legacy_scope = object_at(root, profile.get("legacy_scope"))
    legacy = legacy_scope.get("purpose_source_pins")
    need(isinstance(legacy, list) and len(legacy) == 130, "HOLD_W42_FROZEN130")
    pins = [{key: row[key] for key in ("name", "path", "sha256")} for row in [*legacy, *modules, *shared]]
    need(all(isinstance(row, dict) and isinstance(row.get("name"), str) for row in pins)
         and len({row["name"] for row in pins}) == 151 and len({row.get("path") for row in pins}) == 151,
         "HOLD_W42_SOURCE_PIN_UNIQUENESS")
    need(config.get("source_pins") == sorted(pins, key=lambda row: row["name"]), "HOLD_W42_CONFIG_COMPLETE_SOURCE_PINS")
    controller = next((row for row in modules if row["name"] == "digest_controller_v2.py"), None)
    registrar = next((row for row in modules if row["name"] == "methods_digest_registration_v3.py"), None)
    need(controller is not None and registrar is not None and config.get("controller") == {key: controller[key] for key in ("path", "sha256")},
         "HOLD_W42_FIXED_CONTROLLER")
    weekend = [row for row in legacy if row["name"] == "weekend_canon_lockstep.py"]
    need(len(weekend) == 1 and weekend[0]["sha256"] == FROZEN_WEEKEND_SHA256,
         "HOLD_W42_ORIGINAL_WEEKEND_PIN")
    all_bindings = [{key: row[key] for key in ("path", "sha256")} for row in pins]
    all_bindings += [scope_binding, scope["publisher_guard"], scope["config"], profile_binding, nomination_binding,
                     profile["legacy_scope"], scope["existing_publication_authority"], scope["scientific_package_authority"],
                     *scope["sources"].values()]
    frames = []
    for row in all_bindings:
        path, raw = read_bound(root, row); stat = path.stat()
        frames.append({"path": str(path.relative_to(root)), "sha256": digest(raw), "mode": stat.st_mode,
                       "size": stat.st_size, "device": stat.st_dev, "inode": stat.st_ino, "mtime_ns": stat.st_mtime_ns})
    return {"frames": sorted(frames, key=lambda row: (row["path"], row["sha256"])), "scope": scope_binding,
            "config": scope["config"], "profile": profile_binding, "nomination": nomination_binding,
            "guard": scope["publisher_guard"], "controller": config["controller"], "registrar_sha256": registrar["sha256"],
            "frozen_source_count": 130, "current_source_count": 20, "shared_source_count": 1}


def consume(root, terminal_binding, exit_binding, scope_binding, *, budget=None):
    if budget is not None: budget.require_remaining()
    root = Path(root).resolve(strict=True); scope = root_scope(root, scope_binding)
    terminal = object_at(root, terminal_binding); exit_proof = object_at(root, exit_binding)
    snapshot = source_snapshot(root, scope_binding)
    command = fixed_command(root, scope)
    need(exit_proof.get("standard") == EXIT_STANDARD and exit_proof.get("status") == "GUARD_REAPED_EXIT0_SOURCE_UNCHANGED"
         and exit_proof.get("root_scope") == scope_binding and exit_proof.get("terminal") == terminal_binding
         and exit_proof.get("before") == snapshot and exit_proof.get("after") == snapshot
         and exit_proof.get("returncode") == 0 and exit_proof.get("process_reaped") is True
         and type(exit_proof.get("child_pid")) is int and exit_proof["child_pid"] > 0
         and exit_proof.get("command") == command and exit_proof.get("command_sha256") == digest(encoded(command))
         and exit_proof.get("caller") == scope["sources"]["w42_after_source_session.py"]
         and path_at(root, terminal_binding["path"]) == Path(scope["publisher_output"]) / "TERMINAL_RESULT.json",
         "HOLD_GENUINE_OUTER_SOURCE_EXIT_REQUIRED")
    try:
        started = dt.datetime.fromisoformat(exit_proof["started_at_utc"])
        finished = dt.datetime.fromisoformat(exit_proof["finished_at_utc"])
        need(started.tzinfo is not None and finished.tzinfo is not None and started <= finished <= dt.datetime.now(dt.timezone.utc),
             "HOLD_W42_EXIT_TIME")
    except (KeyError, TypeError, ValueError): raise PublicationHold("HOLD_W42_EXIT_TIME") from None
    need(terminal.get("standard") == "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2" and terminal.get("status") == "PUBLISHED_STRICT_READBACK_PASS"
         and terminal.get("published") is True and terminal.get("source_session_exit_succeeded") is True
         and terminal.get("certifies") is False and terminal.get("ssot_writes") == 0 and terminal.get("certificates_issued") == 0
         and terminal.get("canonical_root") == str(root)
         and terminal.get("controller") == snapshot["controller"], "HOLD_W42_FINAL_PUBLICATION_REQUIRED")
    match = DOI.fullmatch(str(terminal.get("doi"))); need(match is not None and match.group(1) == str(terminal.get("record_id")), "HOLD_W42_DOI_IDENTITY")
    config = object_at(root, terminal["config"])
    copied_config_path, copied_config_raw = read_bound(root, terminal["config"])
    need(copied_config_path == Path(scope["publisher_output"]) / "CONFIG.json"
         and config == object_at(root, snapshot["config"]) and copied_config_raw == encoded(config), "HOLD_W42_OWNED_CONFIG_COPY")
    need(terminal.get("source_pins") == config.get("source_pins") and terminal.get("source_scope_plan") == config.get("source_scope_plan"),
         "HOLD_W42_TERMINAL_SOURCE_BINDING")
    manifest = object_at(root, terminal.get("digest_manifest")); publication = object_at(root, terminal.get("publication_binding"))
    registration = object_at(root, terminal.get("registration_receipt"))
    for key in ("public_evidence", "strict_readback", "public_native_receipt", "public_legacy_receipt", "checkpoint"):
        read_bound(root, terminal.get(key))
    strict = object_at(root, terminal["strict_readback"])
    need(strict.get("status") == "STRICT_OWN_PUBLIC_READBACK_PASS" and strict.get("certifies") is False
         and str(strict.get("record_id")) == str(terminal["record_id"]) and strict.get("doi") == terminal["doi"]
         and strict.get("binding_sha256") == terminal["publication_binding"]["sha256"], "HOLD_W42_STRICT_OWN_READBACK")
    need(manifest.get("standard") == LABELLED_STANDARD and manifest.get("certifies") is False
         and manifest.get("authority") == scope["scientific_package_authority"]
         and evidence_binding(root, publication.get("manifest")) == terminal["digest_manifest"] and publication.get("certifies") is False
         and publication.get("authority") == manifest["authority"], "HOLD_W42_LABELLED_MANIFEST_BINDING")
    inputs = manifest.get("input_bindings")
    need(isinstance(inputs, dict) and inputs, "HOLD_W42_COMPLETE_INPUT_BINDINGS")
    for path, sha256 in inputs.items():
        if budget is not None: budget.require_remaining()
        read_bound(root, {"path": path, "sha256": sha256})
    uploads = manifest.get("uploads")
    need(isinstance(uploads, list) and uploads and publication.get("uploads") == uploads, "HOLD_W42_UPLOAD_INVENTORY")
    expected_downloads = {row.get("filename"): row.get("sha256") for row in uploads if isinstance(row, dict)}
    need(len(expected_downloads) == len(uploads) and all(isinstance(name, str) and name not in {".", ".."}
         and name == Path(name).name and SHA.fullmatch(str(sha256))
         for name, sha256 in expected_downloads.items()), "HOLD_W42_UPLOAD_INVENTORY")
    expected_downloads.update({"DIGEST_MANIFEST.json": terminal["digest_manifest"]["sha256"],
                               "PUBLICATION_BINDING.json": terminal["publication_binding"]["sha256"]})
    downloads = terminal.get("downloads")
    need(isinstance(downloads, list) and len(downloads) == len(expected_downloads), "HOLD_W42_EXACT_PUBLIC_DOWNLOADS")
    seen_downloads = set()
    for row in downloads:
        need(isinstance(row, dict) and row.get("filename") in expected_downloads and row["filename"] not in seen_downloads
             and row.get("binding", {}).get("sha256") == expected_downloads[row["filename"]], "HOLD_W42_EXACT_PUBLIC_DOWNLOADS")
        seen_downloads.add(row["filename"]); read_bound(root, row["binding"])
    need(registration.get("standard") == "VRS-METHODS-DIGEST-REGISTRATION-3" and registration.get("status") == "PUBLISHED_GROUP_BOUND"
         and registration.get("tree_root") == str(root) and registration.get("doi") == terminal["doi"]
         and str(registration.get("record_id")) == str(terminal["record_id"]) and registration.get("certifies") is False
         and registration.get("consumer_sha256") == snapshot["registrar_sha256"]
         and registration.get("digest_manifest") == terminal["digest_manifest"]
         and registration.get("digest_publication_binding") == terminal["publication_binding"]
         and registration.get("public_evidence") == terminal["public_evidence"]
         and registration.get("authority") == manifest["authority"], "HOLD_W42_REGISTRATION_BINDING")
    notes, children = manifest.get("notes"), registration.get("children")
    week = terminal.get("release_week")
    need(week == "2026-W42" and registration.get("release_week") == week and manifest.get("release_week") == week,
         "HOLD_W42_EXACT_RELEASE_WEEK")
    need(isinstance(notes, list) and notes and isinstance(children, list) and len(notes) == len(children), "HOLD_W42_CHILDREN")
    rows, seen = [], set()
    for note, child in zip(notes, children):
        need(isinstance(note, dict) and isinstance(child, dict) and child.get("run_id") == note.get("run_id")
             and isinstance(child.get("run_id"), str) and re.fullmatch(r"Run-\d{3,}", child["run_id"])
             and child.get("id") == "publication:methods-note:" + week + ":" + child["run_id"]
             and child["run_id"] not in seen and "certificate" in child and child["certificate"] is None
             and child.get("artifact_label") == ARTIFACT_LABEL and note.get("artifact_label") == ARTIFACT_LABEL,
             "HOLD_W42_UNCERTIFIED_CHILD")
        seen.add(child["run_id"])
        artifact = path_at(root, child.get("path"), directory=True)
        need(artifact == path_at(root, note.get("path"), directory=True)
             and child.get("publication_binding") == evidence_binding(root, note.get("publication_binding")), "HOLD_W42_CHILD_ARTIFACT_BINDING")
        read_bound(root, child["publication_binding"])
        evidence = child.get("statement_certificate_evidence")
        need(isinstance(evidence, dict) and evidence.get("scope") == STATEMENT_SCOPE
             and evidence.get("certifies_current_artifact") is False and evidence.get("certificate_valid") is True
             and all(evidence.get(key) == note.get(key) for key in
                     ("certificate", "candidate", "formal_statement", "statement_scope", "scientific_predecessor")),
             "HOLD_W42_SEPARATE_STATEMENT_EVIDENCE")
        for key in ("certificate", "candidate", "formal_statement"):
            evidence_binding(root, evidence[key])
        note_uploads = note.get("uploads")
        need(isinstance(note_uploads, list) and note_uploads, "HOLD_W42_NOTE_SOURCE_INVENTORY")
        source_files = []
        for upload in note_uploads:
            need(isinstance(upload, dict) and set(upload) == {"filename", "sha256"}
                 and isinstance(upload["filename"], str) and upload["filename"] not in {".", ".."}
                 and upload["filename"] == Path(upload["filename"]).name, "HOLD_W42_NOTE_SOURCE_INVENTORY")
            source = {"path": str((artifact / upload["filename"]).relative_to(root)), "sha256": upload["sha256"]}
            read_bound(root, source)
            need(inputs.get(str(artifact / upload["filename"])) == upload["sha256"], "HOLD_W42_NOTE_INPUT_SOURCE_BINDING")
            source_files.append(source)
        need(len({row["path"] for row in source_files}) == len(source_files), "HOLD_W42_NOTE_SOURCE_INVENTORY")
        rows.append({"id": child.get("id"), "run_id": child["run_id"], "path": child["path"], "doi": terminal["doi"],
            "status": "UNCERTIFIED", "certificate_valid": False, "certificate": None, "certificate_sha256": None,
            "certifies": False, "artifact_label": ARTIFACT_LABEL, "statement_certificate_evidence": copy.deepcopy(evidence),
            "note_publication_binding": copy.deepcopy(child["publication_binding"]), "source_files": source_files,
            "runtime_admission": False})
    need(terminal.get("run_ids") == [row["run_id"] for row in rows]
         and len({row["id"] for row in rows}) == len(rows) and len({row["path"] for row in rows}) == len(rows), "HOLD_W42_EXACT_CHILD_SET")
    if budget is not None: budget.require_remaining()
    return {"standard": "VRS-W42-TRUTHFUL-PUBLICATION-INTAKE-1", "status": "W42_PUBLISHED_SOURCE_EXIT_VERIFIED",
            "publication": terminal_binding, "source_exit": exit_binding, "root_scope": scope_binding,
            "doi": terminal["doi"], "record_id": str(terminal["record_id"]), "release_week": terminal.get("release_week"),
            "certifies": False, "certificate": None, "certificate_valid": False, "status_label": "UNCERTIFIED",
            "artifact_label": ARTIFACT_LABEL, "children": rows, "private_evidence_only": True,
            "legacy_consumer_status": "HOLD_UNCERTIFIED_ARTIFACT", "runtime_admission": False}
