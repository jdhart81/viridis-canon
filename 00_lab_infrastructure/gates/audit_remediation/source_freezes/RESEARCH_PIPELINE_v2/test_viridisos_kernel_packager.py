from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPT = Path(__file__).with_name("viridisos_kernel_packager.py")
SPEC = importlib.util.spec_from_file_location("viridisos_kernel_packager", SCRIPT)
packager = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = packager
SPEC.loader.exec_module(packager)


def put(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_passing_review_cannot_mask_pending_manuscript_status(tmp_path):
    put(tmp_path / "PAPER_PACKAGE_MANIFEST.json", {"artifacts": {"paper_source": "paper.tex"}})
    (tmp_path / "paper.tex").write_text("Independent manuscript review remains pending.")
    with pytest.raises(packager.KernelPackageError, match="HOLD_REVIEW_STATUS_CONTRADICTION"):
        packager.validate_declared_scientific_bindings(tmp_path, {}, {"verdict": "pass"})


def finalized_fixture(root: Path, *, wrapper: bool) -> tuple[Path, Path]:
    finalized = root / "finalized"
    output = root / "kernel-packages"
    run = finalized / "Run-200"
    put(run / "FINALIZED_PACKAGE.json", {"status": "FINALIZED", "finalized_at_utc": "2026-09-01T10:00:00Z"})
    put(run / "POST_ARISTOTLE_REVIEW.json", {"verdict": "pass"})
    put(run / "PAPER_PACKAGE_MANIFEST.json", {"run_id": "Run-200"})
    put(
        run / "CANON_PRODUCT_ROUTE.json",
        {
            "result": "PRODUCT_ROUTE" if wrapper else "EXCLUDE_METHODS_NOTE",
            "product_disposition": "ADAPTER_REVIEW" if wrapper else "BACKLOG_NO_WRAPPER_METHODS_NOTE",
            "wrapper_candidate": {"module_id": "bounded-audit"} if wrapper else None,
            "product_reason": "No operational wrapper is justified." if not wrapper else "Deterministic bounded audit.",
        },
    )
    put(
        run / "LEAN_ZERO_SORRY_CERTIFICATE.json",
        {
            "run_id": "Run-200",
            "status": "LEAN_ZERO_SORRY_CERTIFIED",
            "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
            "gates": {
                "allowed_axioms_only": True,
                "comparator_lean_kernel": True,
                "comparator_nanoda_kernel": True,
                "comparator_statement_identity": True,
                "frozen_statement_and_candidate_hash_bound": True,
                "independent_cloud_kernel_verification": True,
                "local_lean_execution": False,
                "nonvacuity_witnesses": True,
                "sealed_statement_signature_alignment": True,
                "zero_sorries_or_admits": True,
            },
        },
    )
    add_admission_review(run, wrapper=wrapper)
    return finalized, output


def add_admission_review(run: Path, *, wrapper: bool) -> None:
    bindings = {
        field: digest(run / filename)
        for field, filename in {
            "finalized_package": "FINALIZED_PACKAGE.json",
            "independent_review": "POST_ARISTOTLE_REVIEW.json",
            "product_route": "CANON_PRODUCT_ROUTE.json",
            "paper_manifest": "PAPER_PACKAGE_MANIFEST.json",
            "lean_zero_sorry_certificate": "LEAN_ZERO_SORRY_CERTIFICATE.json",
        }.items()
    }
    put(
        run / "KERNEL_ADMISSION_REVIEW.json",
        {
            "schema_version": 1,
            "standard": "VRS-VIRIDISOS-KERNEL-ADMISSION-1",
            "run_id": "Run-200",
            "reviewer": {
                "system": "Codex",
                "model": "test-reviewer",
                "review_invocation_id": "review-2",
                "draft_invocation_id": "draft-1",
                "independent_from_draft_invocation": True,
            },
            "reviewed_at_utc": "2026-09-01T11:00:00Z",
            "g7_verdict": "PASS",
            "complete_pdf_review": True,
            "reviewed_artifact_sha256": bindings,
            "publication_rank": "SOLID" if wrapper else "MINOR",
            "science_score": 6 if wrapper else 3,
            "kernel_role": "KNOWN_METHOD_FORMALIZATION" if wrapper else "NO_RUNTIME_KERNEL",
            "runtime_verdict": "ADMIT_CANDIDATE" if wrapper else "NO_RUNTIME_KERNEL",
            "decision_family_id": "governance-integrity" if wrapper else None,
            "empirical_validation_status": "NOT_APPLICABLE",
            "nearest_prior_results": ["Named prior result"] if wrapper else [],
            "scope": "Declared-input deterministic audit only." if wrapper else None,
            "refusal_boundary": "Refuse inputs outside the closed schema." if wrapper else None,
            "no_runtime_reason": None if wrapper else "The reviewed methods note has no justified decision output.",
            "claim_separation": {
                "formally_proved": ["bounded identity"],
                "numeric_or_code": [],
                "empirical": [],
                "assumed": [],
                "cited": ["Named prior result"],
                "conjectured_or_deferred": [],
            },
            "scientific_probes": {
                "triviality": "CLASSIFIED",
                "nonvacuity": "PASS",
                "hypothesis_rearrangement": "CLASSIFIED",
                "numeric_consistency": "NOT_APPLICABLE",
                "prior_art": "PASS",
                "metadata_hygiene": "PASS",
            },
        },
    )


def add_complete_spec(run: Path) -> None:
    engine = run / "kernel.py"
    test = run / "test_kernel.py"
    fixture_input = run / "fixture_input.json"
    fixture_expected = run / "fixture_expected.json"
    engine.write_text("def compute(inputs):\n    return inputs\n", encoding="utf-8")
    test.write_text("def test_kernel():\n    assert True\n", encoding="utf-8")
    put(fixture_input, {"value": 1})
    put(fixture_expected, {"value": 1})
    put(
        run / "VIRIDISOS_KERNEL_SPEC.json",
        {
            "standard": "VRS-VIRIDISOS-KERNEL-SPEC-1",
            "run_id": "Run-200",
            "module": {
                "id": "bounded-audit",
                "name": "Bounded audit",
                "line": "Verification",
                "version": "0.1.0",
            },
            "backing": {
                "lean_module": "Viridis.Run200",
                "verification_receipt_id": "Run-200-Comparator-attempt-1",
            },
            "input_schema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"value": {"type": "number"}},
                "required": ["value"],
            },
            "units": {"value": "dimensionless"},
            "scope": "Declared-input deterministic audit only.",
            "engine": {"path": "kernel.py", "sha256": digest(engine), "entrypoint": "compute"},
            "tests": [{"path": "test_kernel.py", "sha256": digest(test)}],
            "fixtures": [{
                "input": "fixture_input.json",
                "input_sha256": digest(fixture_input),
                "expected": "fixture_expected.json",
                "expected_sha256": digest(fixture_expected),
            }],
        },
    )


    path = run / "VIRIDISOS_KERNEL_SPEC.json"
    spec = json.loads(path.read_text())
    output = run / "execution.log"
    output.write_text("SYNTHETIC UNIT TEST RECEIPT; not actual scientific verification\n")
    execution = {"standard": "VRS-KERNEL-EXECUTION-1", "run_id": "Run-200", "status": "PASS",
        "engine_sha256": spec["engine"]["sha256"], "module_id": spec["module"]["id"], "module_version": spec["module"]["version"],
        "tests": spec["tests"], "fixtures": spec["fixtures"], "exit_code": 0, "runtime": "fixture-only", "command": ["fixture-only"],
        "output_path": output.name, "output_sha256": digest(output)}
    put(run / "EXECUTION.json", execution)
    spec["execution_receipt"] = {"path": "EXECUTION.json", "sha256": digest(run / "EXECUTION.json")}
    correspondence = {"standard": "VRS-KERNEL-CORRESPONDENCE-1", "run_id": "Run-200", "status": "PASS",
        "engine_sha256": spec["engine"]["sha256"], "module_id": spec["module"]["id"], "module_version": spec["module"]["version"],
        "backing": spec["backing"], "reviewer": {"system": "fixture", "model": "fixture", "review_invocation_id": "review", "implementation_invocation_id": "draft"},
        "execution_receipt_sha256": spec["execution_receipt"]["sha256"], "limitations": ["Fixture only"],
        "formal_to_runtime_mapping": "Fixture identity only", "numerical_error_policy": "Fixture only", "units_and_domain_review": "Fixture only"}
    put(run / "CORRESPONDENCE.json", correspondence)
    spec["correspondence_review"] = {"path": "CORRESPONDENCE.json", "sha256": digest(run / "CORRESPONDENCE.json")}
    put(path, spec)


def test_methods_note_gets_explicit_no_runtime_kernel_receipt(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    receipt = packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    assert receipt["status"] == "NO_RUNTIME_KERNEL"
    assert receipt["eligible_for_runtime_module"] is False
    assert receipt["authority"]["production_deployment_authorized"] is False
    assert (output / "Run-200/VIRIDISOS_KERNEL_PACKAGE.json").is_file()
    assert packager.build_kernel_package("Run-200", finalized_root=finalized, output_root=output) == receipt


def test_wrapper_candidate_holds_without_complete_spec(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    with pytest.raises(packager.KernelPackageError, match="lacks VIRIDISOS_KERNEL_SPEC"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_missing_admission_review_holds(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    (finalized / "Run-200/KERNEL_ADMISSION_REVIEW.json").unlink()
    with pytest.raises(packager.KernelPackageError, match="kernel_admission_review is missing"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_same_invocation_review_holds(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    path = finalized / "Run-200/KERNEL_ADMISSION_REVIEW.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    review["reviewer"]["review_invocation_id"] = review["reviewer"]["draft_invocation_id"]
    put(path, review)
    with pytest.raises(packager.KernelPackageError, match="independent later invocation"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_unresolved_empirical_validation_holds_runtime_candidate(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    path = finalized / "Run-200/KERNEL_ADMISSION_REVIEW.json"
    review = json.loads(path.read_text(encoding="utf-8"))
    review["empirical_validation_status"] = "REQUIRED"
    put(path, review)
    add_complete_spec(finalized / "Run-200")
    with pytest.raises(packager.KernelPackageError, match="unresolved empirical validation"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_certificate_gate_failure_holds(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    run = finalized / "Run-200"
    certificate_path = run / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["gates"]["comparator_nanoda_kernel"] = False
    put(certificate_path, certificate)
    add_admission_review(run, wrapper=False)
    with pytest.raises(packager.KernelPackageError, match="clean exact-run Comparator"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_complete_hash_bound_adapter_becomes_implementation_ready(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    add_complete_spec(finalized / "Run-200")
    receipt = packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    assert receipt["status"] == "KERNEL_IMPLEMENTATION_READY"
    assert receipt["eligible_for_runtime_module"] is True
    assert receipt["implementation"]["module"]["id"] == "bounded-audit"
    assert receipt["authority"]["automatic_certification_authority"] is False


def test_digest_drift_fails_closed(tmp_path: Path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    run = finalized / "Run-200"
    add_complete_spec(run)
    (run / "kernel.py").write_text("def compute(inputs):\n    return {}\n", encoding="utf-8")
    with pytest.raises(packager.KernelPackageError, match="does not match"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_tests_present_without_execution_is_not_ready(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    run = finalized / "Run-200"
    add_complete_spec(run)
    path = run / "VIRIDISOS_KERNEL_SPEC.json"
    spec = json.loads(path.read_text()); del spec["execution_receipt"]; put(path,spec)
    with pytest.raises(packager.KernelPackageError, match="execution_receipt exact-engine evidence"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)

def test_failed_engine_execution_holds(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True); run = finalized / "Run-200"; add_complete_spec(run)
    receipt = run / "EXECUTION.json"; value = json.loads(receipt.read_text()); value["exit_code"]=1; put(receipt,value)
    specpath=run/"VIRIDISOS_KERNEL_SPEC.json"; spec=json.loads(specpath.read_text());spec["execution_receipt"]["sha256"]=digest(receipt);put(specpath,spec)
    with pytest.raises(packager.KernelPackageError, match="passing exact-engine"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)

def test_tests_without_correspondence_hold(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=True); run=finalized/"Run-200";add_complete_spec(run)
    path=run/"VIRIDISOS_KERNEL_SPEC.json";spec=json.loads(path.read_text());del spec["correspondence_review"];put(path,spec)
    with pytest.raises(packager.KernelPackageError, match="correspondence_review exact-engine evidence"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)

def test_different_invocation_strings_do_not_override_chronology(tmp_path):
    finalized, output=finalized_fixture(tmp_path,wrapper=False);path=finalized/"Run-200/KERNEL_ADMISSION_REVIEW.json"
    value=json.loads(path.read_text());value["reviewed_at_utc"]="2026-09-01T09:59:00Z";put(path,value)
    with pytest.raises(packager.KernelPackageError,match="later than the exact finalized"):
        packager.build_kernel_package("200",finalized_root=finalized,output_root=output)


@pytest.mark.parametrize("classification", ["EXCLUDE_METHODS_NOTE", "NOT_CANDIDATE"])
def test_publication_classification_does_not_veto_reviewed_runtime(tmp_path, classification):
    finalized, output = finalized_fixture(tmp_path, wrapper=True)
    run = finalized / "Run-200"
    route_path = run / "CANON_PRODUCT_ROUTE.json"
    route = json.loads(route_path.read_text())
    route["result"] = classification
    put(route_path, route)
    add_admission_review(run, wrapper=True)
    add_complete_spec(run)
    result = packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    assert result["status"] == "KERNEL_IMPLEMENTATION_READY"


@pytest.mark.parametrize("classification", ["EXCLUDE_METHODS_NOTE", "NOT_CANDIDATE", "PRODUCT_ROUTE"])
def test_absent_wrapper_does_not_manufacture_no_runtime_verdict(tmp_path, classification):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    run = finalized / "Run-200"
    put(run / "CANON_PRODUCT_ROUTE.json", {"result": classification, "wrapper_candidate": None})
    add_admission_review(run, wrapper=False)
    with pytest.raises(packager.KernelPackageError, match="runtime role is unresolved"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    assert not (output / "Run-200/VIRIDISOS_KERNEL_PACKAGE.json").exists()


def test_missing_empirical_dependency_is_not_no_runtime_disposition(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    path = finalized / "Run-200/KERNEL_ADMISSION_REVIEW.json"
    value = json.loads(path.read_text())
    value["kernel_role"] = "EMPIRICAL_VALIDATION_REQUIRED"
    value["empirical_validation_status"] = "REQUIRED"
    put(path, value)
    with pytest.raises(packager.KernelPackageError, match="must remain HOLD"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


def test_no_runtime_route_requires_reason_and_no_conflicting_wrapper(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    run = finalized / "Run-200"
    path = run / "CANON_PRODUCT_ROUTE.json"
    route = json.loads(path.read_text())
    route["product_reason"] = ""
    put(path, route)
    with pytest.raises(packager.KernelPackageError, match="documented product reason"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    route["product_reason"] = "Explicit fixture reason."
    route["wrapper_candidate"] = {"module_id": "conflicting-candidate"}
    put(path, route)
    with pytest.raises(packager.KernelPackageError, match="conflicts with a wrapper candidate"):
        packager.build_kernel_package("200", finalized_root=finalized, output_root=output)


@pytest.mark.parametrize("wrapper", [False, True])
def test_validate_only_requires_existing_exact_receipt_and_never_writes(tmp_path, monkeypatch, wrapper):
    finalized, output = finalized_fixture(tmp_path, wrapper=wrapper)
    if wrapper:
        add_complete_spec(finalized / "Run-200")
    receipt = packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    path = output / "Run-200/VIRIDISOS_KERNEL_PACKAGE.json"
    original = path.read_bytes()
    original_mtime = path.stat().st_mtime_ns
    def forbidden_write(*args, **kwargs):
        raise AssertionError("validate-only called the package writer")
    monkeypatch.setattr(packager, "write_json_atomic", forbidden_write)
    assert packager.validate_existing_kernel_package("200", finalized_root=finalized, output_root=output) == receipt
    assert path.read_bytes() == original and path.stat().st_mtime_ns == original_mtime
    missing = tmp_path / "missing-output"
    with pytest.raises(packager.KernelPackageError, match="validation-only never creates"):
        packager.validate_existing_kernel_package("200", finalized_root=finalized, output_root=missing)
    assert not missing.exists()


def test_validate_only_cli_is_read_only_and_reports_missing_receipt(tmp_path):
    import os
    import subprocess

    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()}
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    command = [sys.executable, str(SCRIPT), "--run", "200", "--finalized-root", str(finalized),
               "--output-root", str(output), "--validate-only"]
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "NO_RUNTIME_KERNEL"
    assert {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.rglob("*") if p.is_file()} == before
    command[command.index(str(output))] = str(tmp_path / "absent-output")
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=10)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "HOLD"
    assert not (tmp_path / "absent-output").exists()


def test_validate_only_rejects_symlinked_core_evidence_and_receipt(tmp_path):
    finalized, output = finalized_fixture(tmp_path, wrapper=False)
    packager.build_kernel_package("200", finalized_root=finalized, output_root=output)
    for path in (finalized / "Run-200/FINALIZED_PACKAGE.json",
                 output / "Run-200/VIRIDISOS_KERNEL_PACKAGE.json"):
        saved = path.with_suffix(".saved")
        path.rename(saved)
        path.symlink_to(saved)
        with pytest.raises(packager.KernelPackageError, match="symlink"):
            packager.validate_existing_kernel_package("200", finalized_root=finalized, output_root=output)
        path.unlink()
        saved.rename(path)
