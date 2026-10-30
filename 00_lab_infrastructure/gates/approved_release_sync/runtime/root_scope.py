"""Consume explicit Root technical scope under existing publication authority.

This module creates no approval, human instruction, certification or merge
verdict. The trusted owning installation supplies the exact scope binding.
"""
from pathlib import Path
import sys
import postpublication_sync as sync

STANDARD = "VRS-APPROVED-RELEASE-SYNC-ROOT-SCOPE-1"
ACTIONS = {"EXECUTE_EXISTING_APPROVED_W42_CONTROLLER", "MIRROR_EXACT_APPROVED_CANON_PACKAGE", "REFRESH_DESCRIPTIVE_METADATA"}
MODULES = {"approved_release_continuation.py", "trusted_canon_adapter.py", "protected_pr_merge.py", "postpublication_sync.py",
           "verified_publication_dispatch.py", "deadline.py", "root_scope.py", "w42_receipt.py", "w42_after_source_session.py", "descriptive_os.py"}


def require_mutation_authority(scope):
    """Inactive source proposal: no installed qualified whole-Core host exists.

    A JSON flag, inherited descriptor, ENGINE lease or Root technical scope
    cannot grant that missing host boundary. Activation requires a separately
    reviewed host-integration source change, not a receipt/configuration toggle.
    """
    raise sync.SyncHold("HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED")


def validated_intake(root, scope):
    """Return private truthful W42 evidence from its actual causal exit proof."""
    root = Path(root).resolve(strict=True)
    proof_binding = scope.get("publisher_exit_checkpoint")
    proof = sync.object_file(_file(root, proof_binding))
    from w42_receipt import consume
    return consume(root, proof.get("terminal"), proof_binding, proof.get("root_scope"))


def validate_w42_mapping(root, scope, payload, catalog_rows=None):
    """Bind explicit public choices to every actual published W42 child.

    This does not manufacture a new Methods Digest consumer. The existing
    Methods Digest pointer format requires certification semantics incompatible
    with the new labelled artifacts; unsupported formats remain an explicit
    HOLD. Generic source records may preserve restrictive coverage labels.
    """
    intake = validated_intake(root, scope)
    sync.require(scope.get("public_projection_format") == "EXISTING_SOURCE_RECORD_WITH_RESTRICTIVE_COVERAGE",
                 "HOLD_CANON_FORMAT_SUCCESSOR_REQUIRED")
    mappings = payload.get("publication_mappings")
    sync.require(isinstance(mappings, list) and len(mappings) == 1
                 and mappings[0].get("parent_doi") == intake["doi"], "HOLD_W42_EXACT_PARENT_MAPPING")
    children = mappings[0].get("children")
    actual = {row["run_id"]: row for row in intake["children"]}
    sync.require(isinstance(children, list) and len(children) == len(actual)
                 and {row.get("run_id") for row in children if isinstance(row, dict)} == set(actual), "HOLD_W42_EXACT_CHILD_MAPPING")
    seen_records = set()
    for child in children:
        row = actual[child["run_id"]]
        sync.require(isinstance(child.get("canon_record_id"), str) and child["canon_record_id"]
                     and child["canon_record_id"] not in seen_records, "HOLD_W42_PUBLIC_RECORD_ID")
        seen_records.add(child["canon_record_id"])
        source = {"path": child.get("source_path"), "sha256": child.get("source_sha256")}
        sync.require(source in row["source_files"] and Path(source["path"]).suffix == ".lean", "HOLD_W42_EXACT_CHILD_PUBLISHED_SOURCE")
        sync.require(child.get("backing_doi") == intake["doi"], "HOLD_W42_EXPLICIT_PARENT_DOI_FOR_SOURCE_PROJECTION")
        if catalog_rows is not None:
            catalog = catalog_rows.get(child["canon_record_id"])
            metadata = catalog.get("metadata") if isinstance(catalog, dict) else None
            coverage = metadata.get("verification_coverage") if isinstance(metadata, dict) else None
            sync.require(isinstance(catalog, dict) and catalog.get("doi") == child["backing_doi"]
                         and catalog.get("source_sha256") == child["source_sha256"]
                         and catalog.get("status") == "working" and catalog.get("integrity") == "not-canon-admitted"
                         and isinstance(coverage, dict) and coverage.get("status") == "HOLD"
                         and coverage.get("canon_eligible") is False and coverage.get("proposed_canon_eligible") is False
                         and coverage.get("label") == intake["artifact_label"]
                         and all(catalog.get(key) is None for key in ("certificate", "certificate_sha256"))
                         and catalog.get("certifies", False) is False and catalog.get("tier") != "spine"
                         and isinstance(catalog.get("tags"), list)
                         and not {"verified", "spine"}.intersection(catalog["tags"]),
                         "HOLD_W42_CURRENT_ARTIFACT_MUST_REMAIN_UNCERTIFIED")
            sync.require(not {"current_artifact", "statement_certificate_evidence"}.intersection(metadata),
                         "HOLD_CANON_FORMAT_SUCCESSOR_REQUIRED")
            expected = {key: row[key] for key in ("status", "certifies", "certificate_valid", "certificate", "certificate_sha256", "artifact_label")}
            current = coverage.get("current_artifact")
            sync.require(current == expected and current.get("certifies") is False and current.get("certificate_valid") is False,
                         "HOLD_W42_CURRENT_ARTIFACT_MUST_REMAIN_UNCERTIFIED")
            projection = child.get("statement_certificate_evidence")
            sync.require(isinstance(projection, dict) and coverage.get("statement_certificate_evidence") == projection,
                         "HOLD_W42_EXPLICIT_PUBLIC_STATEMENT_PROJECTION")
            evidence = row["statement_certificate_evidence"]
            from w42_receipt import digest, encoded, STATEMENT_SCOPE
            required = {"scope", "certifies_current_artifact", "certificate_valid", "source_evidence_sha256",
                        "certificate", "candidate", "formal_statement", "statement_scope", "scientific_predecessor_sha256"}
            sync.require(set(projection) == required and projection.get("scope") == STATEMENT_SCOPE
                         and projection.get("certifies_current_artifact") is False and projection.get("certificate_valid") is True
                         and projection.get("source_evidence_sha256") == digest(encoded(evidence))
                         and projection.get("statement_scope") == evidence["statement_scope"]
                         and projection.get("scientific_predecessor_sha256") == digest(encoded(evidence["scientific_predecessor"]))
                         and str(Path(root).resolve()) not in str(projection), "HOLD_W42_PUBLIC_STATEMENT_SCOPE")
            files = payload.get("git_files", [])
            for key in ("certificate", "candidate", "formal_statement"):
                bound = projection[key]
                sync.require(isinstance(bound, dict) and set(bound) == {"path", "sha256"}
                             and isinstance(bound.get("path"), str) and not Path(bound["path"]).is_absolute()
                             and ".." not in Path(bound["path"]).parts and bound.get("sha256") == evidence[key]["sha256"]
                             and any(item.get("target_path") == bound["path"]
                                     and item.get("source", {}).get("sha256") == bound["sha256"] for item in files),
                             "HOLD_W42_PUBLIC_STATEMENT_FILE_MAPPING")
    return intake


def _file(root, value):
    sync.require(isinstance(value, dict) and set(value) == {"path", "sha256"} and isinstance(value.get("path"), str)
                 and sync.SHA64.fullmatch(str(value.get("sha256"))), "HOLD_ROOT_SCOPE_FILE_BINDING")
    path = Path(value["path"])
    path = sync.regular(path if path.is_absolute() else root / path, root)
    sync.require(sync.file_hash(path) == value["sha256"], "HOLD_ROOT_SCOPE_FILE_DRIFT")
    return path


def load(root, binding_or_path, *, require_canon=False):
    root = Path(root).resolve(strict=True)
    path = _file(root, binding_or_path) if isinstance(binding_or_path, dict) else sync.regular(binding_or_path, root)
    scope = sync.object_file(path)
    sync.require(scope.get("standard") == STANDARD and scope.get("status") == "ROOT_REVIEWED"
                 and scope.get("canonical_root") == str(root), "HOLD_EXPLICIT_ROOT_SCOPE_REQUIRED")
    actions = scope.get("permitted_actions")
    sync.require(isinstance(actions, list) and len(actions) == len(ACTIONS) and set(actions) == ACTIONS, "HOLD_ROOT_RELEASE_SYNC_SCOPE")
    config = sync.object_file(_file(root, scope.get("config")))
    sync.require(config.get("canonical_root") == str(root)
                 and scope.get("existing_publication_authority") == config.get("user_authorization")
                 and scope.get("scientific_package_authority") == config.get("authority"), "HOLD_EXISTING_PUBLICATION_AUTHORITY_BINDING")
    for key in ("existing_publication_authority", "scientific_package_authority", "publisher_guard"):
        _file(root, scope.get(key))
    sources = scope.get("sources")
    runtime = Path(__file__).resolve(strict=True).parent
    allowed = {root / "_ZENODO_DEPOSITS/approved_release_sync",
               root / "00_lab_infrastructure/gates/approved_release_sync/runtime"}
    sync.require(runtime in allowed and isinstance(sources, dict) and set(sources) == MODULES, "HOLD_ROOT_COMPLETE_ADDITIVE_SOURCE_CLOSURE")
    for name, value in sources.items():
        sync.require(isinstance(name, str) and isinstance(value, dict) and name == Path(value.get("path", "")).name,
                     "HOLD_ROOT_ADDITIVE_SOURCE_BINDINGS")
        source = _file(root, value)
        sync.require(source == runtime / name, "HOLD_ROOT_ADDITIVE_SOURCE_ROLE")
        loaded = sys.modules.get(name[:-3])
        if loaded is not None:
            sync.require(Path(loaded.__file__).resolve(strict=True) == source
                         and sync.file_hash(Path(loaded.__file__)) == value["sha256"], "HOLD_ROOT_EXECUTING_SOURCE_ROLE")
    review = scope.get("data_pr_review_policy")
    sync.require(isinstance(review, dict) and review.get("required") is True, "HOLD_SCHEDULED_EXACT_HEAD_DATA_PR_REVIEW_REQUIRED")
    if not require_canon: return scope
    package = scope.get("canon_package")
    sync.require(isinstance(package, dict) and all(sync.SHA64.fullmatch(str(package.get(key))) for key in
                 ("publication_receipt_sha256", "payload_manifest_sha256", "adapter_source_sha256")), "HOLD_CANON_PACKAGE_REQUIRED")
    payload = scope.get("canon_payload_manifest")
    _file(root, payload)
    sync.require(payload["sha256"] == package["payload_manifest_sha256"], "HOLD_ROOT_CANON_PAYLOAD_BINDING")
    merge = scope.get("protected_pr_merge")
    sync.require(isinstance(merge, dict) and sync.SHA40.fullmatch(str(merge.get("head_sha")))
                 and merge.get("repository") == sync.REPOSITORY and merge.get("base_branch") == "main"
                 and merge.get("publication_receipt_sha256") == package["publication_receipt_sha256"]
                 and merge.get("payload_manifest_sha256") == package["payload_manifest_sha256"]
                 and merge.get("adapter_source_sha256") == package["adapter_source_sha256"]
                 and sync.SHA64.fullmatch(str(merge.get("merge_policy_source_sha256"))), "HOLD_ROOT_PROTECTED_MERGE_SCOPE_REQUIRED")
    names = merge.get("required_check_names")
    sync.require(isinstance(names, list) and names and all(isinstance(name, str) and name for name in names)
                 and names == sorted(set(names)), "HOLD_ROOT_PROTECTED_CHECK_SET")
    proof = sync.object_file(_file(root, scope.get("publisher_exit_checkpoint")))
    sync.require(proof.get("standard") == "VRS-W42-GENUINE-OUTER-SOURCE-EXIT-1"
                 and proof.get("status") == "GUARD_REAPED_EXIT0_SOURCE_UNCHANGED" and proof.get("returncode") == 0
                 and proof.get("before") == proof.get("after") and isinstance(proof.get("before"), dict)
                 and type(proof.get("child_pid")) is int and proof["child_pid"] > 0,
                 "HOLD_GENUINE_OUTER_SOURCE_EXIT_REQUIRED")
    terminal = proof.get("terminal")
    sync.require(isinstance(terminal, dict) and terminal.get("sha256") == package["publication_receipt_sha256"],
                 "HOLD_ROOT_CANON_PUBLICATION_BINDING")
    _file(root, terminal)
    prior_binding = proof.get("root_scope")
    sync.require(isinstance(prior_binding, dict) and _file(root, prior_binding) != path, "HOLD_INITIAL_EXIT_SCOPE_REQUIRED")
    prior = load(root, prior_binding, require_canon=False)
    sync.require(all(prior.get(key) == scope.get(key) for key in
                 ("canonical_root", "config", "existing_publication_authority", "scientific_package_authority",
                  "publisher_guard", "publisher_output", "sources", "permitted_actions", "data_pr_review_policy")), "HOLD_ROOT_POSTPUBLICATION_SCOPE_DRIFT")
    from w42_receipt import consume
    consume(root, terminal, scope["publisher_exit_checkpoint"], prior_binding)
    return scope
