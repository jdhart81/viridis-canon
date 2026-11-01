from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest
import autonomous_pipeline_controller as controller
from autonomous_pipeline_controller import build_state


def put(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def cert(root: Path, run_id: str) -> None:
    put(root / run_id / "LEAN_ZERO_SORRY_CERTIFICATE.json", {
        "run_id": run_id,
        "status": "LEAN_ZERO_SORRY_CERTIFIED",
        "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
        "gates": {
            "allowed_axioms_only": True,
            "comparator_lean_kernel": True,
            "comparator_nanoda_kernel": True,
            "comparator_statement_identity": True,
            "frozen_statement_and_candidate_hash_bound": True,
            "independent_cloud_kernel_verification": True,
            "nonvacuity_witnesses": True,
            "sealed_statement_signature_alignment": True,
            "zero_sorries_or_admits": True,
            "local_lean_execution": False,
        },
    })


def review(root: Path) -> None:
    put(root / "POST_ARISTOTLE_REVIEW.json", {
        "schema_version": 2,
        "verdict": "pass",
        "reviewer_system": "Codex",
        "reviewer_model": "test",
        "checks": {"hashes": True},
    })


def full_package(root: Path, run_id: str) -> None:
    # A valid legacy fixture has an explicit reviewed disposition and FINALIZED
    # status, rather than a fabricated status-only cached kernel receipt.
    from viridisos_kernel_packager import build_kernel_package
    finalized = root.parent / "finalized" / run_id
    final_path = finalized / "FINALIZED_PACKAGE.json"
    final = json.loads(final_path.read_text()) if final_path.is_file() else {}
    put(final_path, {**final, "status": "FINALIZED"})
    route_path = finalized / "CANON_PRODUCT_ROUTE.json"
    route = json.loads(route_path.read_text()) if route_path.is_file() else {}
    put(route_path, {**route, "product_disposition": "BACKLOG_NO_WRAPPER_METHODS_NOTE",
                     "wrapper_candidate": None, "product_reason": "Explicit fixture no-runtime review."})
    if not (finalized / "POST_ARISTOTLE_REVIEW.json").is_file():
        review(finalized)
    if not (finalized / "PAPER_PACKAGE_MANIFEST.json").is_file():
        put(finalized / "PAPER_PACKAGE_MANIFEST.json", {"run_id": run_id})
    build_kernel_package(run_id, finalized_root=finalized.parent,
                         output_root=root.parent / "viridisos_kernel_packages")
    bundle = root / "2026-08-31" / f"2026-08-31_{run_id}_standalone"
    names = (
        "paper.pdf", "paper.tex", "CITATION.cff", "RIGHTS_AND_LICENSE.md",
        "RELEASE_README.md", "REPRODUCTION_BUNDLE.zip",
        "GIT_PAYLOAD_MANIFEST.json", "zenodo_metadata.json",
    )
    for name in names:
        path = bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
    sums = "".join(
        f"{hashlib.sha256((bundle / name).read_bytes()).hexdigest()}  {name}\n"
        for name in names
    )
    (bundle / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    put(bundle / "BUNDLE_MANIFEST.json", {
        "run_id": run_id,
        "package_completeness": {
            "status": "READY_EXCEPT_RIGHTS_LICENSE_LEDGER_AUTHORIZATION",
        },
    })


def test_orders_reversible_work_before_human_gate(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    r1, r2 = finalized / "Run-001", finalized / "Run-002"
    r1.mkdir(parents=True); r2.mkdir()
    cert(certificates, "Run-001"); cert(certificates, "Run-002")
    put(r1 / "CURATOR_DRAFT_READY.json", {})
    put(r2 / "CURATOR_DRAFT_READY.json", {})
    review(r2); put(r2 / "FINALIZED_PACKAGE.json", {})
    put(r2 / "CANON_PRODUCT_ROUTE.json", {})
    put(r2 / "PAPER_PACKAGE_MANIFEST.json", {"release_metadata": {"license": "cc-by-4.0", "ledger_row": 90}})
    full_package(tmp_path / "saturday_candidates", "Run-002")
    state = build_state(finalized, certificates, tmp_path / "missing.json")
    assert state["first_action"]["run_id"] == "Run-001"
    assert state["first_action"]["state"] == "INDEPENDENT_REVIEW_REQUIRED"
    assert state["counts"]["human_gated"] == 1


def test_published_intake_becomes_viridisos_tracked(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    root = finalized / "Run-003"; root.mkdir(parents=True)
    cert(certificates, "Run-003"); put(root / "CURATOR_DRAFT_READY.json", {})
    review(root); put(root / "FINALIZED_PACKAGE.json", {}); put(root / "CANON_PRODUCT_ROUTE.json", {})
    put(root / "PAPER_PACKAGE_MANIFEST.json", {"release_metadata": {"license": "cc-by-4.0", "ledger_row": 91}})
    intake = tmp_path / "intake.json"
    put(intake, {"records": [{"run_id": "Run-003", "doi": "10.5281/zenodo.1"}]})
    state = build_state(finalized, certificates, intake)
    assert state["items"][0]["state"] == "VIRIDISOS_TRACKED"
    assert state["counts"]["machine_actionable"] == 0


def test_never_grants_scheduled_publication(tmp_path: Path):
    state = build_state(tmp_path / "none", tmp_path / "certs", tmp_path / "intake")
    assert state["autonomy"]["scheduled_publication"] is False
    assert state["autonomy"]["scheduled_production_deployment"] is False


def test_historical_final_review_is_not_recertified(tmp_path: Path):
    finalized = tmp_path / "finalized"
    root = finalized / "Run-004"; root.mkdir(parents=True)
    put(root / "CURATOR_DRAFT_READY.json", {})
    review(root); put(root / "FINALIZED_PACKAGE.json", {})
    state = build_state(finalized, tmp_path / "no-certs", tmp_path / "no-intake")
    assert state["items"][0]["state"] == "CANON_SCAN_REQUIRED"


def test_public_source_hash_blocks_duplicate_publication(tmp_path: Path):
    import hashlib

    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    root = finalized / "Run-005"; root.mkdir(parents=True)
    lean = root / "AlreadyPublic.lean"; lean.write_text("theorem public : True := by trivial\n")
    source_hash = hashlib.sha256(lean.read_bytes()).hexdigest()
    submission_map = tmp_path / "submission-map.json"
    put(submission_map, {"github_catalog": [{
        "doi": "10.5281/zenodo.5",
        "source_sha256": source_hash,
    }]})
    state = build_state(finalized, certificates, tmp_path / "no-intake", submission_map)
    assert state["items"][0]["state"] == "PUBLICATION_RECONCILIATION_REQUIRED"
    assert state["items"][0]["next_action"] == "SEAL_EXISTING_DOI_GIT_IDENTITY"

    put(root / "PUBLIC_IDENTITY_RECONCILIATION.json", {"status": "READY_FOR_AUTHORIZATION"})
    state = build_state(finalized, certificates, tmp_path / "no-intake", submission_map)
    assert state["items"][0]["state"] == "READY_FOR_EXISTING_IDENTITY_BINDING_AUTHORIZATION"
    assert state["items"][0]["human_gate"] is True


def test_release_binding_proposal_becomes_exact_human_gate(tmp_path: Path):
    finalized = tmp_path / "finalized"
    root = finalized / "Run-006"; root.mkdir(parents=True)
    put(root / "CURATOR_DRAFT_READY.json", {})
    review(root); put(root / "FINALIZED_PACKAGE.json", {}); put(root / "CANON_PRODUCT_ROUTE.json", {})
    put(root / "PAPER_PACKAGE_MANIFEST.json", {"release_metadata": {"license": None, "ledger_row": None}})
    put(root / "RELEASE_BINDING_PROPOSAL.json", {
        "status": "READY_FOR_EXACT_AUTHORIZATION",
        "run_id": "Run-006",
        "proposed_ledger_row": 90,
        "proposed_license": "cc-by-4.0",
    })
    full_package(tmp_path / "saturday_candidates", "Run-006")
    state = build_state(finalized, tmp_path / "no-certs", tmp_path / "no-intake", tmp_path / "no-map")
    assert state["items"][0]["state"] == "READY_FOR_RELEASE_BINDING_AUTHORIZATION"
    assert state["items"][0]["human_gate"] is True


def test_independent_review_hold_is_explicit_repair_state(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    root = finalized / "Run-007"; root.mkdir(parents=True)
    cert(certificates, "Run-007")
    put(root / "CURATOR_DRAFT_READY.json", {})
    put(root / "FINALIZED_PACKAGE.json", {})
    put(root / "POST_ARISTOTLE_REVIEW.json", {
        "schema_version": 2,
        "verdict": "hold",
        "hold": {"code": "HOLD_CONTRADICTORY_VERIFICATION_STATE"},
    })
    state = build_state(finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map")
    assert state["items"][0]["state"] == "REVIEW_HOLD_REPAIR_REQUIRED"
    assert state["items"][0]["next_action"] == "CREATE_VERSIONED_CORRECTION_OVERLAY"


def test_certified_metadata_contradiction_is_machine_reconciliation(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    root = finalized / "Run-008"; root.mkdir(parents=True)
    cert(certificates, "Run-008")
    put(root / "CURATOR_DRAFT_READY.json", {})
    put(root / "PAPER_PACKAGE_MANIFEST.json", {
        "formal_verification": {
            "provider": "COMPARATOR_CLOUD",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "aristotle_required": False,
        },
        "release_metadata": {
            "description": "No formally verified result exists.",
            "spine_reason": "No certified result exists.",
        },
    })
    state = build_state(finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map")
    assert state["items"][0]["state"] == "VERIFICATION_METADATA_RECONCILIATION_REQUIRED"
    assert state["items"][0]["human_gate"] is False


def test_open_frontier_run_with_transport_hold_is_visible(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    (finalized / "Run-009").mkdir(parents=True)
    packages = tmp_path / "nightly_packages"
    (packages / "Run-010").mkdir(parents=True)
    put(certificates / "Run-010/COMPARATOR_SUBMISSION_HOLD.json", {
        "status": "HOLD_EXPLICIT_PAYLOAD_DESTINATION_AUTHORIZATION_REQUIRED",
    })
    state = build_state(
        finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map", packages,
        comparator_authorization_path=tmp_path / "missing-authorization.json",
        verifier_backends_path=tmp_path / "missing-backends.json",
    )
    item = next(row for row in state["items"] if row["run_id"] == "Run-010")
    assert item["state"] == "READY_FOR_COMPARATOR_TRANSPORT_AUTHORIZATION"
    assert item["human_gate"] is True


def test_active_standing_authorization_consumes_stale_transport_hold(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    packages = tmp_path / "nightly_packages"
    (packages / "Run-010").mkdir(parents=True)
    put(certificates / "Run-010/COMPARATOR_SUBMISSION_HOLD.json", {
        "status": "HOLD_EXPLICIT_PAYLOAD_DESTINATION_AUTHORIZATION_REQUIRED",
    })
    authorization = tmp_path / "authorization.json"
    backends = tmp_path / "backends.json"
    put(authorization, {
        "authorization_id": "test",
        "authorized_by": "Justin D. Hart",
        "status": "ACTIVE_STANDING_AUTHORIZATION",
        "destination": {
            "host": "root@138.197.18.27",
            "project": "viridis-lean-4.28",
            "service_visibility": "PRIVATE_LOOPBACK_BEHIND_DEDICATED_SSH",
        },
        "scope": {
            "inputs": [
                "Viridis paper inputs required to bind a frozen verification request",
                "Lean formal statements",
                "Lean proof candidates",
            ],
            "outputs": [
                "immutable dual-kernel verification receipts",
                "zero-sorry certificates",
            ],
            "runs": ["current FIFO certification backlog", "future nightly science runs"],
        },
        "required_invariants": {
            "backlog_first_fifo": True,
            "nanoda_kernel_required": True,
            "lean_default_kernel_required": True,
            "zero_sorries_required": True,
            "local_lean_execution": False,
            "aristotle_required": False,
            "fail_closed": True,
        },
        "excluded_actions": {
            "publication": True,
            "credential_recording_in_receipts": True,
            "weakening_or_rewriting_frozen_claims": True,
        },
    })
    put(backends, {
        "primary_backend": "COMPARATOR_CLOUD",
        "backends": [{
            "id": "COMPARATOR_CLOUD",
            "status": "ENABLED",
            "endpoint": "root@138.197.18.27:/usr/local/bin/viridis-comparator-verify",
            "project": "viridis-lean-4.28",
            "public_http_exposure": False,
            "kernels": ["LEAN_DEFAULT_KERNEL", "NANODA"],
            "permitted_sorries": [],
        }],
        "local_lean_fallback_authorized": False,
        "aristotle_required": False,
    })
    state = build_state(
        finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map", packages,
        comparator_authorization_path=authorization,
        verifier_backends_path=backends,
    )
    item = next(row for row in state["items"] if row["run_id"] == "Run-010")
    assert item["state"] == "CERTIFICATE_REQUIRED"
    assert item["human_gate"] is False
    assert state["comparator_data_egress_authorization"]["publication_authorized"] is False


def test_submission_ready_count_includes_only_final_reversible_boundary(tmp_path: Path):
    finalized = tmp_path / "finalized"
    root = finalized / "Run-006"; root.mkdir(parents=True)
    put(root / "CURATOR_DRAFT_READY.json", {})
    review(root); put(root / "FINALIZED_PACKAGE.json", {}); put(root / "CANON_PRODUCT_ROUTE.json", {})
    put(root / "PAPER_PACKAGE_MANIFEST.json", {"release_metadata": {"license": None, "ledger_row": None}})
    put(root / "RELEASE_BINDING_PROPOSAL.json", {
        "status": "READY_FOR_EXACT_AUTHORIZATION",
        "run_id": "Run-006",
        "proposed_ledger_row": 90,
        "proposed_license": "cc-by-4.0",
    })
    full_package(tmp_path / "saturday_candidates", "Run-006")
    state = build_state(finalized, tmp_path / "no-certs", tmp_path / "no-intake", tmp_path / "no-map")
    assert state["counts"]["submission_ready_packages"] == 1


def test_historical_open_run_is_not_hidden_by_newer_finalized_run(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    (finalized / "Run-020").mkdir(parents=True)
    packages = tmp_path / "nightly_packages"
    (packages / "Run-010").mkdir(parents=True)
    cert(certificates, "Run-010")
    state = build_state(
        finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map", packages
    )
    item = next(row for row in state["items"] if row["run_id"] == "Run-010")
    assert item["state"] == "RECONCILIATION_REQUIRED"


def test_certified_open_run_with_manuscript_hold_is_repair_not_reconciliation(tmp_path: Path):
    finalized, certificates = tmp_path / "finalized", tmp_path / "certs"
    packages = tmp_path / "nightly_packages"
    root = packages / "Run-011"
    root.mkdir(parents=True)
    cert(certificates, "Run-011")
    put(root / "QUALITY_GATE.json", {
        "quality_verdict": "HOLD",
        "checks": [{"code": "N4", "passed": False}],
    })
    state = build_state(
        finalized, certificates, tmp_path / "no-intake", tmp_path / "no-map", packages
    )
    item = next(row for row in state["items"] if row["run_id"] == "Run-011")
    assert item["state"] == "PAPER_PACKAGE_REPAIR_REQUIRED"
    assert item["next_action"] == "CREATE_VERSIONED_PRE_CURATOR_PAPER_CORRECTION"



def checksum_fixture(tmp_path):
    candidates = tmp_path / "saturday_candidates"
    full_package(candidates, "Run-149")
    bundle = candidates / "2026-08-31/2026-08-31_Run-149_standalone"
    return candidates, bundle


def test_submission_checksum_accepts_complete_bound_package(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    extra = bundle / "nested/evidence.txt"
    extra.parent.mkdir()
    extra.write_text("fixture evidence")
    sums = bundle / "SHA256SUMS.txt"
    sums.write_text(sums.read_text() + f"{hashlib.sha256(extra.read_bytes()).hexdigest()}  nested/evidence.txt\n")
    assert complete_submission_package("Run-149", candidates) is True


def test_submission_checksum_rejects_empty_and_incomplete_inventory(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    sums = bundle / "SHA256SUMS.txt"
    original = sums.read_text()
    for contents in ("", "\n", "\n".join(original.splitlines()[1:]) + "\n"):
        sums.write_text(contents)
        assert complete_submission_package("Run-149", candidates) is False


def test_submission_checksum_rejects_missing_mandatory_artifact(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    (bundle / "paper.pdf").unlink()
    assert complete_submission_package("Run-149", candidates) is False


def test_submission_checksum_rejects_duplicate_and_noncanonical_paths(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    sums = bundle / "SHA256SUMS.txt"
    original = sums.read_text()
    digest = hashlib.sha256((bundle / "paper.pdf").read_bytes()).hexdigest()
    for relative in ("paper.pdf", "./paper.pdf", "nested/../paper.pdf", "/paper.pdf",
                     str(bundle / "paper.pdf"), "nested//paper.pdf", "nested\\paper.pdf"):
        sums.write_text(original + f"{digest}  {relative}\n")
        assert complete_submission_package("Run-149", candidates) is False


def test_submission_checksum_rejects_symlink_paths(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    target = bundle / "paper.pdf"
    alias = bundle / "paper-alias.pdf"
    alias.symlink_to(target)
    sums = bundle / "SHA256SUMS.txt"
    sums.write_text(sums.read_text() + f"{hashlib.sha256(target.read_bytes()).hexdigest()}  paper-alias.pdf\n")
    assert complete_submission_package("Run-149", candidates) is False


def test_submission_checksum_rejects_wrong_hash_for_required_or_extra_artifact(tmp_path):
    from autonomous_pipeline_controller import complete_submission_package

    candidates, bundle = checksum_fixture(tmp_path)
    sums = bundle / "SHA256SUMS.txt"
    original = sums.read_text()
    sums.write_text("0" * 64 + original[64:])
    assert complete_submission_package("Run-149", candidates) is False
    (bundle / "extra.txt").write_text("fixture")
    sums.write_text(original + "0" * 64 + "  extra.txt\n")
    assert complete_submission_package("Run-149", candidates) is False


def test_stale_kernel_package_is_review_work_not_release_ready(tmp_path):
    finalized = tmp_path / "finalized"
    run = finalized / "Run-006"
    put(run / "CURATOR_DRAFT_READY.json", {})
    review(run)
    put(run / "FINALIZED_PACKAGE.json", {})
    put(run / "CANON_PRODUCT_ROUTE.json", {})
    put(run / "PAPER_PACKAGE_MANIFEST.json", {"release_metadata": {"license": None, "ledger_row": None}})
    put(run / "RELEASE_BINDING_PROPOSAL.json", {
        "status": "READY_FOR_EXACT_AUTHORIZATION", "run_id": "Run-006",
        "proposed_ledger_row": 90, "proposed_license": "cc-by-4.0",
    })
    full_package(tmp_path / "saturday_candidates", "Run-006")
    package = tmp_path / "viridisos_kernel_packages/Run-006/VIRIDISOS_KERNEL_PACKAGE.json"
    before = package.read_bytes()
    for name in ("FINALIZED_PACKAGE.json", "POST_ARISTOTLE_REVIEW.json", "CANON_PRODUCT_ROUTE.json", "PAPER_PACKAGE_MANIFEST.json"):
        original = (run / name).read_bytes()
        (run / name).write_bytes(original + b"\n")
        state = build_state(finalized, tmp_path / "no-certs", tmp_path / "no-intake", tmp_path / "no-map")
        assert state["items"][0]["state"] == "KERNEL_PACKAGE_RECONCILIATION_REQUIRED"
        assert state["items"][0]["next_action"] == "REVIEW_EXISTING_KERNEL_PACKAGE_BINDINGS"
        assert state["counts"]["submission_ready_packages"] == 0
        assert package.read_bytes() == before
        (run / name).write_bytes(original)


def snapshot_files(root):
    return {
        p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
        for p in root.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize("tamper", ["admission_hold", "certificate_gate", "engine", "spec"])
def test_kernel_completion_revalidates_full_current_closure_without_writes(tmp_path, tamper):
    from test_viridisos_kernel_packager import finalized_fixture, add_complete_spec, packager, put as fixture_put

    finalized, packages = finalized_fixture(tmp_path, wrapper=True)
    run = finalized / "Run-200"
    add_complete_spec(run)
    packager.build_kernel_package("200", finalized_root=finalized, output_root=packages)
    receipt = packages / "Run-200/VIRIDISOS_KERNEL_PACKAGE.json"
    original_receipt = receipt.read_bytes()
    assert controller.complete_kernel_package("Run-200", packages, run) is True
    core_names = ("FINALIZED_PACKAGE.json", "POST_ARISTOTLE_REVIEW.json",
                  "CANON_PRODUCT_ROUTE.json", "PAPER_PACKAGE_MANIFEST.json")
    core_before = {name: (run / name).read_bytes() for name in core_names}
    if tamper == "admission_hold":
        path = run / "KERNEL_ADMISSION_REVIEW.json"
        value = json.loads(path.read_text())
        value["runtime_verdict"] = "HOLD"
        fixture_put(path, value)
    elif tamper == "certificate_gate":
        path = run / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        value = json.loads(path.read_text())
        value["gates"]["comparator_nanoda_kernel"] = False
        fixture_put(path, value)
    elif tamper == "engine":
        (run / "kernel.py").write_text("def compute(inputs):\n    return {}\n")
    else:
        path = run / "VIRIDISOS_KERNEL_SPEC.json"
        value = json.loads(path.read_text())
        value["units"]["value"] = "changed-but-valid-unit-string"
        fixture_put(path, value)
    assert {name: (run / name).read_bytes() for name in core_names} == core_before
    before_status = snapshot_files(tmp_path)
    assert controller.complete_kernel_package("Run-200", packages, run) is False
    assert receipt.read_bytes() == original_receipt
    assert snapshot_files(tmp_path) == before_status


@pytest.mark.parametrize("wrapper", [False, True])
def test_kernel_completion_status_cannot_call_any_package_writer(tmp_path, monkeypatch, wrapper):
    from test_viridisos_kernel_packager import finalized_fixture, add_complete_spec, packager

    finalized, packages = finalized_fixture(tmp_path, wrapper=wrapper)
    run = finalized / "Run-200"
    if wrapper:
        add_complete_spec(run)
    packager.build_kernel_package("200", finalized_root=finalized, output_root=packages)
    before = snapshot_files(tmp_path)
    def forbidden_write(*args, **kwargs):
        raise AssertionError("status called the operational package writer")
    monkeypatch.setattr(controller.kernel_packager, "write_json_atomic", forbidden_write)
    assert controller.complete_kernel_package("Run-200", packages, run) is True
    assert snapshot_files(tmp_path) == before
    missing = tmp_path / "missing-packages"
    assert controller.complete_kernel_package("Run-200", missing, run) is False
    assert not missing.exists()


def test_legacy_declared_certificate_is_revalidated(tmp_path):
    from viridisos_kernel_packager import build_kernel_package

    candidates = tmp_path / "saturday_candidates"
    full_package(candidates, "Run-149")
    run = tmp_path / "finalized/Run-149"
    # Prepare a separate legitimate legacy fixture revision, then preserve its receipt.
    package = tmp_path / "viridisos_kernel_packages/Run-149/VIRIDISOS_KERNEL_PACKAGE.json"
    package.unlink()
    cert(tmp_path / "finalized", "Run-149")
    certificate = run / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    manifest = json.loads((run / "PAPER_PACKAGE_MANIFEST.json").read_text())
    manifest["formal_verification"] = {"certificate": {
        "path": certificate.name, "sha256": hashlib.sha256(certificate.read_bytes()).hexdigest(),
    }}
    put(run / "PAPER_PACKAGE_MANIFEST.json", manifest)
    build_kernel_package("149", finalized_root=run.parent, output_root=tmp_path / "viridisos_kernel_packages")
    assert controller.complete_kernel_package("Run-149", tmp_path / "viridisos_kernel_packages", run) is True
    value = json.loads(certificate.read_text())
    value["gates"]["comparator_nanoda_kernel"] = False
    put(certificate, value)
    before = snapshot_files(tmp_path)
    assert controller.complete_kernel_package("Run-149", tmp_path / "viridisos_kernel_packages", run) is False
    assert snapshot_files(tmp_path) == before


def admission_controller_fixture(tmp_path):
    from test_viridisos_kernel_packager import finalized_fixture, add_admission_review

    finalized, packages = finalized_fixture(tmp_path, wrapper=False)
    run = finalized / "Run-200"
    review(run)
    put(run / "CURATOR_DRAFT_READY.json", {})
    add_admission_review(run, wrapper=False)
    return finalized, packages, run


def inspect_admission_fixture(tmp_path, finalized, packages):
    return controller.inspect_run(finalized / "Run-200", tmp_path / "no-certs", set(), set(),
                                  tmp_path / "no-candidates", False, packages)


def test_valid_exact_admission_offers_packaging_without_writing(tmp_path, monkeypatch):
    finalized, packages, run = admission_controller_fixture(tmp_path)
    before = snapshot_files(tmp_path)
    monkeypatch.setattr(controller.kernel_packager, "write_json_atomic",
                        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("writer invoked")))
    item = inspect_admission_fixture(tmp_path, finalized, packages)
    assert item.next_action == "BUILD_VIRIDISOS_KERNEL_PACKAGE"
    assert snapshot_files(tmp_path) == before
    assert not packages.exists()


@pytest.mark.parametrize("defect", ["hold", "metadata_hold", "manifest_hash", "malformed", "symlink", "chronology"])
def test_held_or_invalid_admission_routes_to_versioned_correction_without_writes(tmp_path, defect):
    finalized, packages, run = admission_controller_fixture(tmp_path)
    admission = run / "KERNEL_ADMISSION_REVIEW.json"
    value = json.loads(admission.read_text())
    if defect == "hold":
        value["runtime_verdict"] = "HOLD"
        put(admission, value)
    elif defect == "metadata_hold":
        value["scientific_probes"]["metadata_hygiene"] = "HOLD"
        put(admission, value)
    elif defect == "manifest_hash":
        manifest = run / "PAPER_PACKAGE_MANIFEST.json"
        manifest.write_bytes(manifest.read_bytes() + b"\n")
    elif defect == "malformed":
        admission.write_text("{")
    elif defect == "symlink":
        original = run / "original-admission.json"
        admission.rename(original)
        admission.symlink_to(original)
    else:
        value["reviewed_at_utc"] = "2026-08-01T10:00:00Z"
        put(admission, value)
    before = snapshot_files(tmp_path)
    item = inspect_admission_fixture(tmp_path, finalized, packages)
    assert item.state == "KERNEL_ADMISSION_CORRECTION_REQUIRED"
    assert item.next_action == "PREPARE_VERSIONED_KERNEL_ADMISSION_CORRECTION"
    assert item.human_gate is False
    assert "Do not infer NO_RUNTIME_KERNEL" in item.detail
    assert snapshot_files(tmp_path) == before
    assert not packages.exists()


def test_pending_paper_status_is_correction_work_even_with_passing_admission(tmp_path):
    from test_viridisos_kernel_packager import add_admission_review

    finalized, packages, run = admission_controller_fixture(tmp_path)
    manifest = json.loads((run / "PAPER_PACKAGE_MANIFEST.json").read_text())
    manifest["artifacts"] = {"paper_source": "paper.tex"}
    put(run / "PAPER_PACKAGE_MANIFEST.json", manifest)
    (run / "paper.tex").write_text("Independent manuscript review remains pending.")
    add_admission_review(run, wrapper=False)
    before = snapshot_files(tmp_path)
    item = inspect_admission_fixture(tmp_path, finalized, packages)
    assert item.next_action == "PREPARE_VERSIONED_KERNEL_ADMISSION_CORRECTION"
    assert "HOLD_REVIEW_STATUS_CONTRADICTION" in item.detail
    assert snapshot_files(tmp_path) == before


def test_missing_admission_still_requires_later_independent_review(tmp_path):
    finalized, packages, run = admission_controller_fixture(tmp_path)
    (run / "KERNEL_ADMISSION_REVIEW.json").unlink()
    before = snapshot_files(tmp_path)
    item = inspect_admission_fixture(tmp_path, finalized, packages)
    assert item.next_action == "REVIEW_KERNEL_ADMISSION"
    assert snapshot_files(tmp_path) == before
