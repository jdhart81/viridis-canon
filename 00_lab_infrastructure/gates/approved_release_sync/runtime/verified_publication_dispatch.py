#!/usr/bin/env python3
"""Additive descriptive continuation, inactive until the real Core host qualifies.

No old OS queue is imported or invoked. The fixed reviewed descriptive adapter
owns a separate index and actual reader readback; legacy certification/admission
remains HOLD. This module never invokes a Zenodo publisher or creates a proof.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess

from deadline import Budget, DeadlineExceeded
import postpublication_sync as sync

STANDARD = "VRS-VERIFIED-PUBLICATION-DISPATCH-2"
LEGACY_HOLD = "HOLD_UNCERTIFIED_ARTIFACT"


def _scope(root, route_binding):
    import root_scope
    sync.require(route_binding is not None, "HOLD_EXPLICIT_ROUTE_BINDING_REQUIRED")
    route_binding = sync.regular(route_binding, root)
    route = sync.object_file(route_binding)
    scope = root_scope.load(root, route.get("owner_approval"), require_canon=True)
    return route_binding, scope


def _fixed_descriptive_adapter(root, scope):
    """Load one fixed sibling only after its existing Root scope binds its bytes."""
    source = Path(__file__).resolve().with_name("descriptive_os.py")
    binding = scope.get("sources", {}).get("descriptive_os.py")
    sync.require(isinstance(binding, dict), "HOLD_REVIEWED_DESCRIPTIVE_ADAPTER_REQUIRED")
    path = Path(binding.get("path", ""))
    bound = sync.regular(path if path.is_absolute() else root / path, root)
    sync.require(bound == source and binding.get("sha256") == sync.file_hash(source),
                 "HOLD_REVIEWED_DESCRIPTIVE_ADAPTER_REQUIRED")
    spec = importlib.util.spec_from_file_location("_approved_release_descriptive_os", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.reconcile


def validate_descriptive_result(value, *, root):
    sync.require(isinstance(value, dict) and value.get("status") == "DESCRIPTIVE_OS_INDEX_READBACK_VERIFIED"
                 and value.get("readback_verified") is True and value.get("certifies") is False
                 and value.get("runtime_admission") is False and value.get("automatic_adoption") is False
                 and "certificate" in value and value["certificate"] is None
                 and value.get("legacy_consumer_status") == LEGACY_HOLD,
                 "HOLD_DESCRIPTIVE_OS_READBACK_REQUIRED")
    proof = value.get("reader_proof")
    sync.require(isinstance(proof, dict) and proof.get("reader") == "descriptive_os.read_index"
                 and sync.SHA64.fullmatch(str(proof.get("source_sha256")))
                 and sync.SHA64.fullmatch(str(proof.get("artifact_sha256"))),
                 "HOLD_DESCRIPTIVE_OS_READER_REQUIRED")
    source = Path(__file__).resolve().with_name("descriptive_os.py")
    sync.require(proof["source_sha256"] == sync.file_hash(source), "HOLD_DESCRIPTIVE_OS_READER_SOURCE")
    binding = proof.get("index")
    sync.require(isinstance(binding, dict) and set(binding) == {"path", "sha256"}
                 and isinstance(binding.get("path"), str) and binding.get("sha256") == proof["artifact_sha256"],
                 "HOLD_DESCRIPTIVE_OS_INDEX_BINDING")
    path = Path(binding["path"])
    path = sync.regular(path if path.is_absolute() else root / path, root)
    sync.require(str(path.relative_to(root)).startswith("ViridisOS/data/approved_release_sync/")
                 and sync.file_hash(path) == binding["sha256"], "HOLD_DESCRIPTIVE_OS_INDEX_READBACK")
    return value


def dispatch(publication_receipt, canon_receipt, doi_receipts, *, root, publication_format,
             apply=False, http=sync.http_json, environ=None, local_os=None,
             transport="environment", runner=subprocess.run, route_binding=None, budget):
    budget.require_remaining()
    root = Path(root).resolve(strict=True)
    publication_receipt = sync.regular(publication_receipt, root)
    canon_receipt = sync.regular(canon_receipt, root)
    publication = sync.object_file(publication_receipt)
    kind, published_dois = sync.publication_dois(publication)
    sync.require(kind == publication_format, "HOLD_PUBLICATION_FORMAT_MISMATCH")
    canon_kind, canon_dois = sync.publication_dois(sync.object_file(canon_receipt))
    sync.require(canon_kind == "lockstep" and canon_dois == published_dois, "HOLD_MATCHING_VERIFIED_CANON_RECEIPT_REQUIRED")
    durable = list(doi_receipts)
    if not durable and kind in {"methods-digest", "successor-wave"}:
        durable = [publication_receipt]
    # Only public GETs and pure validation occur before the qualified-host gate.
    plan = sync.synchronize(canon_receipt, durable, root=root, apply=False, http=http, environ=environ,
                            transport=transport, runner=runner, budget=budget)
    evidence = {"publication_format": kind,
                "publication_receipt": str(publication_receipt.relative_to(root)),
                "publication_receipt_sha256": sync.file_hash(publication_receipt),
                "canon_receipt": str(canon_receipt.relative_to(root)),
                "canon_receipt_sha256": sync.file_hash(canon_receipt)}
    if not apply:
        return {"standard": STANDARD, "status": "DRY_RUN", **evidence,
                "metadata_plan": plan["status"], "local_os_reconciliation": "QUALIFIED_HOST_AND_DESCRIPTIVE_READER_REQUIRED",
                "legacy_consumer_status": LEGACY_HOLD, "runtime_adoption": False,
                "external_mutations": 0, "publisher_invocations": 0}
    route_binding, scope = _scope(root, route_binding)
    # Intentionally unconditional HOLD in this source-only proposal. There is no
    # FD, lease, JSON verdict or receipt which can simulate real host ownership.
    sync.require_mutation_authority(scope)
    evidence["route_binding_sha256"] = sync.file_hash(route_binding)
    if transport == "environment":
        secret = (os.environ if environ is None else environ).get("CRON_SECRET")
        sync.require(isinstance(secret, str) and bool(secret) and "\n" not in secret and "\r" not in secret, "HOLD_CRON_AUTH_MISSING")
    identity = sync.digest(evidence)
    output = root / "reports/approved-release-sync/verified-publication-dispatch" / (identity + ".json")
    try:
        # The Python callable seam is for trusted inert tests, never selected by
        # a command argument, untrusted receipt or source path from data.
        adapter = local_os if local_os is not None else _fixed_descriptive_adapter(root, scope)
        reconciled = validate_descriptive_result(budget.call(adapter, root, canon_receipt, publication_receipt,
                                                            route_binding, budget=budget), root=root)
        sync.require(sync.file_hash(publication_receipt) == evidence["publication_receipt_sha256"]
                     and sync.file_hash(canon_receipt) == evidence["canon_receipt_sha256"]
                     and sync.file_hash(route_binding) == evidence["route_binding_sha256"], "HOLD_PUBLICATION_EVIDENCE_CHANGED")
        result = sync.synchronize(canon_receipt, durable, root=root, apply=True, http=http, environ=environ,
                                  transport=transport, runner=runner, budget=budget, approved_scope=scope)
        summary = {"standard": STANDARD, **evidence, "local_os_reconciliation": reconciled,
                   "status": result["status"], "metadata_sync_status": result["status"],
                   "metadata_release_identity": result["release_identity"],
                   "legacy_consumer_status": LEGACY_HOLD, "publisher_invocations": 0, "zenodo_mutations": 0,
                   "runtime_adoption": False, "runtime_admission": False, "certifies": False,
                   "scope": "NEW_DESCRIPTIVE_OS_INDEX_AND_BOTH_APP_METADATA_READBACKS_ONLY"}
    except (sync.SyncHold, DeadlineExceeded) as error:
        summary = {"standard": STANDARD, **evidence, "status": "CANON_PUBLISHED_VIRIDISOS_PENDING",
                   "reason": "HOLD_SHARED_DEADLINE" if isinstance(error, DeadlineExceeded) else str(error),
                   "legacy_consumer_status": LEGACY_HOLD, "publisher_invocations": 0, "zenodo_mutations": 0,
                   "runtime_adoption": False, "runtime_admission": False, "certifies": False}
    except Exception:
        summary = {"standard": STANDARD, **evidence, "status": "CANON_PUBLISHED_VIRIDISOS_PENDING",
                   "reason": "HOLD_POSTPUBLICATION_DISPATCH", "legacy_consumer_status": LEGACY_HOLD,
                   "publisher_invocations": 0, "zenodo_mutations": 0, "runtime_adoption": False,
                   "runtime_admission": False, "certifies": False}
    if output.exists() and sync.object_file(output).get("status") == "PRODUCTION_METADATA_PROPAGATION_VERIFIED":
        previous = sync.object_file(output)
        if previous != summary:
            summary["existing_verified_receipt_sha256"] = sync.file_hash(output)
            output = output.with_name(identity + "-readback-" + sync.digest(summary) + ".json")
    budget.cleanup_remaining_cap(30)
    sync.atomic_receipt(output, summary)
    return summary


def after_methods_digest(terminal_receipt, canon_receipt, *, root, apply=False, **kwargs):
    return dispatch(terminal_receipt, canon_receipt, [], root=root, publication_format="methods-digest", apply=apply, **kwargs)


def after_successor_wave(publication_receipt, canon_receipt, *, root, apply=False, **kwargs):
    return dispatch(publication_receipt, canon_receipt, [], root=root, publication_format="successor-wave", apply=apply, **kwargs)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--publication-format", choices=("lockstep", "methods-digest", "successor-wave"), required=True)
    parser.add_argument("--publication-receipt", type=Path, required=True)
    parser.add_argument("--canon-receipt", type=Path, required=True)
    parser.add_argument("--doi-receipt", action="append", type=Path, default=[])
    parser.add_argument("--route-binding", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--transport", choices=("environment", "existing-app-ssh"), default="environment")
    args = parser.parse_args(argv)
    try:
        result = dispatch(args.publication_receipt, args.canon_receipt, args.doi_receipt, root=args.root,
                          publication_format=args.publication_format, apply=args.apply, transport=args.transport,
                          route_binding=args.route_binding, budget=Budget())
    except sync.SyncHold as error:
        result = {"standard": STANDARD, "status": "HOLD_PUBLICATION_DISPATCH", "reason": str(error), "publisher_invocations": 0}
    except Exception:
        result = {"standard": STANDARD, "status": "HOLD_PUBLICATION_DISPATCH", "reason": "HOLD_DISPATCH_INPUT", "publisher_invocations": 0}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"DRY_RUN", "PRODUCTION_METADATA_PROPAGATION_VERIFIED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
