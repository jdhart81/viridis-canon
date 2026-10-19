#!/usr/bin/env python3
"""Continue a published digest/successor through an owner-approved Canon package.

This additive wrapper does not call a Zenodo publisher, infer public mappings,
load an adapter from supplied source, or change frozen publication closures.
The owner wires a reviewed Canon adapter as a trusted Python callable, or binds
an already verified Canon receipt. Missing package/adapter evidence is a HOLD.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile

import postpublication_sync as sync
import verified_publication_dispatch as shared
import root_scope
from deadline import Budget

STANDARD = "VRS-APPROVED-CANON-CONTINUATION-1"
RUN = re.compile(r"Run-\d{3,}")


def bound_file(root, binding):
    sync.require(isinstance(binding, dict) and set(binding) == {"path", "sha256"}, "HOLD_CONTINUATION_FILE_BINDING")
    sync.require(isinstance(binding["path"], str) and sync.SHA64.fullmatch(str(binding["sha256"])), "HOLD_CONTINUATION_FILE_BINDING")
    path = Path(binding["path"])
    path = path if path.is_absolute() else root / path
    path = sync.regular(path, root)
    sync.require(sync.file_hash(path) == binding["sha256"], "HOLD_CONTINUATION_FILE_DRIFT")
    return path


def validate_binding(root, publication_receipt, route_binding, expected_binding_sha256):
    root = Path(root).resolve(strict=True)
    sync.require(route_binding is not None and expected_binding_sha256 is not None, "HOLD_CANON_RELEASE_PACKAGE_REQUIRED")
    path = sync.regular(route_binding, root)
    sync.require(sync.file_hash(path) == expected_binding_sha256, "HOLD_CONTINUATION_BINDING_DRIFT")
    value = sync.object_file(path)
    sync.require(value.get("standard") == STANDARD and value.get("status") == "OWNER_REVIEWED_PACKAGE_BINDING",
                 "HOLD_CANON_RELEASE_PACKAGE_REQUIRED")
    approval = bound_file(root, value.get("owner_approval"))
    scope = root_scope.load(root, approval, require_canon=True)
    publication_receipt = sync.regular(publication_receipt, root)
    sync.require(bound_file(root, value.get("publication_receipt")) == publication_receipt, "HOLD_CONTINUATION_PUBLICATION_MISMATCH")
    kind, published = sync.publication_dois(sync.object_file(publication_receipt))
    sync.require(kind in {"methods-digest", "successor-wave"} and value.get("publisher_format") == kind,
                 "HOLD_CONTINUATION_PUBLISHER_FORMAT")
    payload = bound_file(root, value.get("canon_payload_manifest"))
    # This is an explicitly reviewed owner adapter contract, not the older
    # Lean-only VRS-GIT-PAYLOAD-1 manifest guessed from a Zenodo archive.
    manifest = sync.object_file(payload)
    sync.require(manifest.get("standard") == "VRS-OWNER-CANON-RELEASE-PAYLOAD-1"
                 and manifest.get("publication_dois") == sorted(published), "HOLD_CANON_RELEASE_PACKAGE_REQUIRED")
    source_files = manifest.get("source_files")
    sync.require(isinstance(source_files, list) and source_files, "HOLD_CANON_PAYLOAD_SOURCES_REQUIRED")
    source_by_path = {}
    for row in source_files:
        source = bound_file(root, row)
        relative = str(source.relative_to(root))
        sync.require(relative not in source_by_path, "HOLD_CANON_PAYLOAD_DUPLICATE_SOURCE")
        source_by_path[relative] = row["sha256"]
    mappings = manifest.get("publication_mappings")
    sync.require(isinstance(mappings, list) and len(mappings) == len(published), "HOLD_CANON_PARENT_CHILD_MAPPING_REQUIRED")
    parents, parent_ids, child_ids, child_record_ids = set(), set(), set(), set()
    for mapping in mappings:
        sync.require(isinstance(mapping, dict) and mapping.get("parent_doi") in published
                     and mapping["parent_doi"] not in parents, "HOLD_CANON_PARENT_CHILD_MAPPING_REQUIRED")
        parents.add(mapping["parent_doi"])
        sync.require(isinstance(mapping.get("parent_canon_publication_id"), str) and mapping["parent_canon_publication_id"]
                     and mapping["parent_canon_publication_id"] not in parent_ids,
                     "HOLD_CANON_PARENT_ID_REQUIRED")
        parent_ids.add(mapping["parent_canon_publication_id"])
        children = mapping.get("children")
        sync.require(isinstance(children, list) and children, "HOLD_CANON_PARENT_CHILD_MAPPING_REQUIRED")
        for child in children:
            sync.require(isinstance(child, dict) and isinstance(child.get("run_id"), str) and RUN.fullmatch(child["run_id"])
                         and child["run_id"] not in child_ids, "HOLD_CANON_CHILD_ID_REQUIRED")
            child_ids.add(child["run_id"])
            sync.require(isinstance(child.get("canon_record_id"), str) and child["canon_record_id"]
                         and child["canon_record_id"] not in child_record_ids, "HOLD_CANON_CHILD_ID_REQUIRED")
            child_record_ids.add(child["canon_record_id"])
            # The owner explicitly chooses whether the child cites its digest
            # parent or preserves a prior standalone DOI. Never guess that
            # semantic mapping from archive membership alone.
            sync.require(isinstance(child.get("backing_doi"), str) and sync.DOI.fullmatch(child["backing_doi"]),
                         "HOLD_CANON_CHILD_DOI_MAPPING")
            sync.require(child.get("source_path") in source_by_path and child.get("source_sha256") == source_by_path[child["source_path"]],
                         "HOLD_CANON_CHILD_SOURCE_MAPPING")
    sync.require(parents == published, "HOLD_CANON_PARENT_CHILD_MAPPING_REQUIRED")
    root_scope.validate_w42_mapping(root, scope, manifest)
    adapter = value.get("owner_canon_adapter")
    sync.require(isinstance(adapter, dict) and isinstance(adapter.get("adapter_id"), str) and adapter["adapter_id"]
                 and adapter.get("reviewed_payload_sha256") == sync.file_hash(payload), "HOLD_OWNER_CANON_ADAPTER_BINDING")
    # Adapter implementation evidence is hash-bound, but never imported or
    # executed from data. The owning code supplies the callable after review.
    bound_file(root, adapter.get("implementation_source"))
    return {"kind": kind, "binding": value, "binding_path": path, "payload": payload,
            "approval": approval, "published_dois": published, "root": root, "root_scope": scope}


def checkpoint_once(path, value):
    """Persist immutable Canon closure before any downstream metadata action."""
    sync.require(not any(p.is_symlink() for p in (path, *path.parents)), "HOLD_CONTINUATION_CHECKPOINT_SYMLINK")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    fd, scratch = tempfile.mkstemp(prefix=".canon-continuation-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        try:
            # Link is atomic and refuses an existing destination. Never replace
            # a verified checkpoint because a later callback failed.
            os.link(scratch, path)
        except FileExistsError:
            sync.require(sync.object_file(sync.regular(path, path.parents[2])) == value,
                         "HOLD_CONTINUATION_CHECKPOINT_CONFLICT")
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(scratch):
            os.unlink(scratch)


def continue_release(publication_receipt, *, root, route_binding=None, expected_binding_sha256=None,
                     apply=False, canon_adapter=None, dispatcher=shared.dispatch, dispatcher_options=None, budget=None):
    budget = budget or Budget()
    budget.require_remaining()
    checked = validate_binding(root, publication_receipt, route_binding, expected_binding_sha256)
    root = Path(root).resolve(strict=True)
    value = checked["binding"]
    publication_receipt = bound_file(root, value["publication_receipt"])
    summary = {"standard": STANDARD, "publisher_format": checked["kind"],
               "route_binding_sha256": expected_binding_sha256, "canon_payload_sha256": sync.file_hash(checked["payload"]),
               "publication_dois": sorted(checked["published_dois"]), "publisher_invocations": 0, "zenodo_mutations": 0,
               "mapping_inferred": False, "frozen_source_changes": False}
    if not apply:
        return {**summary, "status": "OWNER_CONTINUATION_READY_FOR_INTEGRATION", "external_mutations": 0}
    root_scope.require_mutation_authority(checked["root_scope"])
    checkpoint_path = root / "reports/approved-canon-continuation" / (expected_binding_sha256 + ".json")
    context = {"standard": STANDARD, "status": "VERIFIED_CANON_CLOSURE_CHECKPOINT",
               "route_binding_sha256": expected_binding_sha256, "canon_payload_sha256": summary["canon_payload_sha256"],
               "publication_receipt_sha256": sync.file_hash(Path(publication_receipt)),
               "adapter_id": value["owner_canon_adapter"]["adapter_id"]}
    existing = value.get("verified_canon_receipt")
    checkpoint_reused = checkpoint_path.exists()
    if checkpoint_reused:
        checkpoint = sync.object_file(sync.regular(checkpoint_path, root))
        sync.require(set(checkpoint) == set(context) | {"canon_receipt"}
                     and all(checkpoint.get(key) == item for key, item in context.items()),
                     "HOLD_CONTINUATION_CHECKPOINT_CONFLICT")
        canon_binding = checkpoint["canon_receipt"]
        canon = bound_file(root, canon_binding)
        if existing is not None:
            sync.require(bound_file(root, existing) == canon and existing["sha256"] == canon_binding["sha256"],
                         "HOLD_CONTINUATION_CHECKPOINT_CONFLICT")
    elif existing is not None:
        canon = bound_file(root, existing)
    else:
        sync.require(callable(canon_adapter), "HOLD_OWNER_CANON_ADAPTER_IMPLEMENTATION_REQUIRED")
        # Reviewed owner implementation performs only its preapproved exact
        # Canon transaction. This wrapper never selects paths or publishes DOIs.
        try:
            result = canon_adapter(root=root, publication_receipt=Path(publication_receipt),
                                   route_binding=checked["binding_path"], expected_binding_sha256=expected_binding_sha256, budget=budget)
        except Exception:
            raise sync.SyncHold("HOLD_OWNER_CANON_ADAPTER") from None
        sync.require(isinstance(result, dict) and result.get("status") == "VERIFIED_CANON_CLOSURE"
                     and result.get("adapter_id") == value["owner_canon_adapter"]["adapter_id"]
                     and result.get("payload_sha256") == summary["canon_payload_sha256"], "HOLD_OWNER_CANON_ADAPTER_RESULT")
        canon = bound_file(root, result.get("canon_receipt"))
    # Reconsume the exact complete binding after an adapter's possible writes.
    validate_binding(root, publication_receipt, route_binding, expected_binding_sha256)
    kind, dois = sync.publication_dois(sync.object_file(canon))
    sync.require(kind == "lockstep" and dois == checked["published_dois"], "HOLD_MATCHING_VERIFIED_CANON_RECEIPT_REQUIRED")
    checkpoint_once(checkpoint_path, {**context, "canon_receipt": {"path": str(canon.relative_to(root)), "sha256": sync.file_hash(canon)}})
    try:
        result = dispatcher(publication_receipt, canon, [], root=root, publication_format=checked["kind"],
                            apply=True, route_binding=checked["binding_path"], budget=budget, **(dispatcher_options or {"transport": "existing-app-ssh"}))
    except Exception:
        raise sync.SyncHold("HOLD_METADATA_DISPATCH_AFTER_CANON_CHECKPOINT") from None
    return {**summary, "status": result["status"], "continuation": result,
            "canon_checkpoint": str(checkpoint_path.relative_to(root)), "canon_checkpoint_reused": checkpoint_reused}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--route-binding", type=Path)
    parser.add_argument("--expected-binding-sha256")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = continue_release(args.publication_receipt, root=args.root, route_binding=args.route_binding,
                                  expected_binding_sha256=args.expected_binding_sha256, apply=args.apply)
    except sync.SyncHold as error:
        result = {"standard": STANDARD, "status": "HOLD_CANON_CONTINUATION", "reason": str(error), "publisher_invocations": 0}
    except Exception:
        result = {"standard": STANDARD, "status": "HOLD_CANON_CONTINUATION", "reason": "HOLD_CONTINUATION_INPUT", "publisher_invocations": 0}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"OWNER_CONTINUATION_READY_FOR_INTEGRATION", "PRODUCTION_METADATA_PROPAGATION_VERIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
