"""Dummy HTTP checks for the sole selected runtime's guarded entry points."""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import traceback
import types
import unittest
from unittest import mock
import urllib.error
import urllib.request
import zipfile


HERE = Path(__file__).resolve().parents[1]
OUTER = HERE.parent
DUMMY = "DUMMY_GUARDED_CREDENTIAL_" + "x" * 40
REAL_IMPORT = importlib.import_module


def load_file(name, path, imports=None):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, imports or {}):
        spec.loader.exec_module(module)
    return module


# Reuse the reviewed Phase 2 behavioral cases, rather than duplicate their
# dummy successor server. This module's copy has isolated publisher globals.
FIXTURE = load_file("_guarded_successor_security_fixtures", OUTER / "tests/test_publish_successor_credentials.py")


class PackagingHold(RuntimeError):
    pass


def fake_packaging():
    return types.SimpleNamespace(
        session=mock.Mock(side_effect=lambda *args: contextlib.nullcontext()),
        nominated_binding=mock.Mock(return_value={"fixture": "NO_RUNTIME_ADMISSION"}),
        validate=mock.Mock(),
    )


def load_guarded(name, filename):
    packaging = fake_packaging()
    module = load_file(name, HERE / filename, {"packaging_runtime": packaging})
    coherence = types.SimpleNamespace(validate_bundle=mock.Mock(), CoherenceError=ValueError)
    module.importlib = types.SimpleNamespace(import_module=lambda name:
        FIXTURE.GATE if name == "manuscript_pdf_gate" else coherence if name == "release_coherence" else REAL_IMPORT(name))
    return module


SUCCESSOR = load_guarded("_selected_guarded_successor_security", "publish_successor_wave_guarded.py")
DATED = load_guarded("_selected_guarded_dated_security", "publish_dated_bundles_guarded.py")
SELECTED_GATE = load_file("_selected_actual_hardened_gate", HERE / "manuscript_pdf_gate.py")
REAL_COHERENCE = load_file("_selected_test_release_coherence", OUTER / "release_coherence.py")
HARDENING = load_file("_selected_gate_hardening_regressions", OUTER / "tests/test_gate_hardening.py")
HARDENING.gate = SELECTED_GATE
DATED_ORIGINAL = load_file("_selected_dated_baseline_fixtures", OUTER / "tests/test_publish_dated_bundles.py")
DATED_EXACT = load_file("_selected_dated_exact_regressions", OUTER / "tests/test_dated_exact_uploads.py",
                        {"test_publish_dated_bundles": DATED_ORIGINAL})
SUCCESSOR_EXACT = load_file("_selected_successor_exact_regressions", OUTER / "tests/test_successor_exact_uploads.py")


class SelectedGateHardeningBehavior(HARDENING.HardeningTests):
    """The audited gate's existing behavioral tests run on the selected copy."""


class GuardedDatedExactBehavior(DATED_EXACT.DatedExactUploadsTests):
    def setUp(self):
        DATED_EXACT.publisher = DATED
        DATED_ORIGINAL.publisher = DATED
        DATED.packaging = fake_packaging()
        DATED.importlib = types.SimpleNamespace(import_module=lambda name:
            SELECTED_GATE if name == "manuscript_pdf_gate" else REAL_COHERENCE if name == "release_coherence" else REAL_IMPORT(name))
        DATED.manuscript_pdf_gate = SELECTED_GATE
        DATED.release_coherence = REAL_COHERENCE


class GuardedSuccessorBehavior(FIXTURE.CredentialTests):
    def setUp(self):
        FIXTURE.PUBLISHER = SUCCESSOR
        SUCCESSOR.packaging = fake_packaging()
        SUCCESSOR.importlib = types.SimpleNamespace(import_module=lambda name:
            FIXTURE.GATE if name == "manuscript_pdf_gate" else REAL_COHERENCE if name == "release_coherence" else REAL_IMPORT(name))


class GuardedSuccessorExactBehavior(SUCCESSOR_EXACT.SuccessorExactUploadsTests):
    def setUp(self):
        SUCCESSOR_EXACT.publisher = SUCCESSOR
        SUCCESSOR_EXACT.gate = SELECTED_GATE
        SUCCESSOR.packaging = fake_packaging()
        SUCCESSOR.importlib = types.SimpleNamespace(import_module=lambda name:
            SELECTED_GATE if name == "manuscript_pdf_gate" else REAL_COHERENCE if name == "release_coherence" else REAL_IMPORT(name))
        SUCCESSOR.manuscript_pdf_gate = SELECTED_GATE


class GuardedBoundaryTests(unittest.TestCase):
    def setUp(self):
        SUCCESSOR.packaging = fake_packaging()
        DATED.packaging = fake_packaging()
        DATED.importlib = types.SimpleNamespace(import_module=lambda name:
            FIXTURE.GATE if name == "manuscript_pdf_gate" else REAL_COHERENCE if name == "release_coherence" else REAL_IMPORT(name))
        DATED.manuscript_pdf_gate = FIXTURE.GATE

    def test_selected_gate_bytes_equal_the_runbook_codec_successor_blob(self):
        expected = "3ca55bf1e3e25e920ce9b79a5363e8d17138183ad592675d6fc058996fa41d0d"
        self.assertEqual(hashlib.sha256((HERE / "manuscript_pdf_gate.py").read_bytes()).hexdigest(), expected)

    def test_selected_gate_inspects_prefixed_zip_bytes_with_an_unrelated_name(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w") as stream:
            stream.writestr("papers/Hidden-Paper.pdf", b"%PDF-hidden manuscript")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated summary")
            (root / "opaque.bin").write_bytes(b"MZ prefixed ZIP\n" + archive.getvalue())
            with self.assertRaisesRegex(SELECTED_GATE.ManuscriptPDFHold, "byte-identical"):
                SELECTED_GATE.require_local(root)

    def test_all_original_session_guard_decorators_remain(self):
        required = {
            "publish_successor_wave_guarded.py": {"load_and_validate_wave", "ensure_draft", "verify_manuscript_readback", "publish_candidate", "main"},
            "publish_dated_bundles_guarded.py": {"metadata_payload", "ensure_draft", "verify_manuscript_readback", "publish_bundle", "plan", "main"},
        }
        for filename, names in required.items():
            tree = ast.parse((HERE / filename).read_bytes())
            guarded = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)
                       and any(isinstance(decorator, ast.Name) and decorator.id == "guarded" for decorator in node.decorator_list)}
            self.assertLessEqual(names, guarded)

    def test_main_session_hold_precedes_credential_loading_and_http(self):
        for module, loader in ((SUCCESSOR, "credential"), (DATED, "token")):
            module.packaging.session.side_effect = PackagingHold("PROFILE_OR_SOURCE_HOLD")
            with self.subTest(module=module.__name__), mock.patch.object(module, loader) as credential, \
                 mock.patch.object(module.urllib.request, "build_opener") as http:
                with self.assertRaises(PackagingHold):
                    module.main()
                credential.assert_not_called()
                http.assert_not_called()

    def test_mutation_revalidates_profile_before_constructing_the_request(self):
        for module in (SUCCESSOR, DATED):
            events = []
            module.packaging.validate.side_effect = lambda *args: events.append("validate")
            opener = types.SimpleNamespace(open=lambda *args, **kwargs: FIXTURE.Response({}))
            original = module.urllib.request.Request
            def request(*args, **kwargs):
                events.append("request")
                return original(*args, **kwargs)
            with self.subTest(module=module.__name__), mock.patch.object(module.urllib.request, "build_opener", return_value=opener), \
                 mock.patch.object(module.urllib.request, "Request", side_effect=request):
                module.api_call(DUMMY, "POST", "https://zenodo.org/api/deposit/depositions", b"{}")
            self.assertEqual(events, ["validate", "request"])

    def test_profile_hold_blocks_http_and_redacts_credential_traceback(self):
        for module in (SUCCESSOR, DATED):
            module.packaging.validate.side_effect = PackagingHold("source failure " + DUMMY)
            with self.subTest(module=module.__name__), mock.patch.object(module.urllib.request, "build_opener") as factory:
                with self.assertRaises(RuntimeError) as caught:
                    module.api_call(DUMMY, "PUT", "https://zenodo.org/api/files/bucket/paper.pdf", b"x")
                factory.return_value.open.assert_not_called()
            self.assertNotIn(DUMMY, "".join(traceback.format_exception(caught.exception)))

    def test_both_transports_refuse_url_and_redirect_credentials(self):
        for module in (SUCCESSOR, DATED):
            for query in ("access_token=anything", "access%255Ftoken=anything", "other=" + DUMMY):
                with self.subTest(module=module.__name__, query_kind=query.split("=")[0]), \
                     mock.patch.object(module.urllib.request, "build_opener") as factory:
                    with self.assertRaises(RuntimeError):
                        module.api_call(DUMMY, "GET", "https://zenodo.org/api/records/1?" + query)
                    factory.assert_not_called()
            request = urllib.request.Request("https://zenodo.org/api/records/1", headers={"Authorization": "Bearer " + DUMMY})
            with self.assertRaises(RuntimeError):
                module.ZenodoRedirectHandler().redirect_request(request, None, 302, "Found", {},
                    "https://zenodo.org/api/records/1?other=" + DUMMY)

    def test_dated_transport_header_only_and_raw_http_causes_do_not_escape(self):
        captured = []
        def opened(request, **kwargs):
            captured.append(request)
            return FIXTURE.Response({})
        with mock.patch.object(DATED.urllib.request, "build_opener", return_value=types.SimpleNamespace(open=opened)):
            DATED.api_call(DUMMY, "GET", "https://zenodo.org/api/records/1")
        self.assertNotIn(DUMMY, captured[0].full_url)
        self.assertEqual(captured[0].get_header("Authorization"), "Bearer " + DUMMY)
        failures = [urllib.error.URLError(DUMMY), urllib.error.HTTPError("https://zenodo.org/api/records/1", 400, DUMMY, {}, io.BytesIO(DUMMY.encode()))]
        for failure in failures:
            with mock.patch.object(DATED.urllib.request, "build_opener") as factory:
                factory.return_value.open.side_effect = failure
                with self.assertRaises(DATED.PublisherError) as caught:
                    DATED.api_call(DUMMY, "POST", "https://zenodo.org/api/deposit/depositions", b"{}")
            self.assertNotIn(DUMMY, "".join(traceback.format_exception(caught.exception)))

    def test_error_body_and_close_failures_cannot_escape_successor_redaction(self):
        class BrokenError(urllib.error.HTTPError):
            def read(self):
                raise RuntimeError(DUMMY)
            def close(self):
                super().close()
                raise RuntimeError(DUMMY)
        failure = BrokenError("https://zenodo.org/api/records/1", 400, "dummy", {}, io.BytesIO())
        with mock.patch.object(SUCCESSOR.urllib.request, "build_opener") as factory:
            factory.return_value.open.side_effect = failure
            with self.assertRaises(SUCCESSOR.SuccessorPublisherError) as caught:
                SUCCESSOR.api_call(DUMMY, "POST", "https://zenodo.org/api/records/1", b"{}")
        self.assertNotIn(DUMMY, "".join(traceback.format_exception(caught.exception)))

    def test_malformed_port_does_not_echo_a_credential(self):
        for module in (SUCCESSOR, DATED):
            with self.subTest(module=module.__name__), mock.patch.object(module.urllib.request, "build_opener") as factory:
                with self.assertRaises(RuntimeError) as caught:
                    module.api_call(DUMMY, "GET", "https://zenodo.org:" + DUMMY + "/api/records/1")
                factory.assert_not_called()
            self.assertNotIn(DUMMY, "".join(traceback.format_exception(caught.exception)))

    def test_dated_catchall_redacts_unexpected_failure(self):
        with mock.patch.object(DATED.sys, "argv", ["dated", "--date", "2026-10-14", "--publish", "--go", "--enforce-new-artifacts"]), \
             mock.patch.object(DATED, "plan", return_value={}), mock.patch.object(DATED, "token", return_value=DUMMY), \
             mock.patch.object(DATED, "bundles", return_value=[Path("fixture")]), \
             mock.patch.object(DATED, "publish_bundle", side_effect=ValueError(DUMMY)), \
             contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(DATED.main(), 2)
        self.assertNotIn(DUMMY, stdout.getvalue() + stderr.getvalue())

    def test_dated_receipt_redacts_exact_credential(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            DATED.write_once(path, json.dumps({"response": DUMMY}), credential=DUMMY)
            self.assertNotIn(DUMMY, path.read_text())

    def test_dated_upload_path_is_encoded_without_relaxing_publish_guards(self):
        calls = []
        def api(credential, method, url, data=None, *args, **kwargs):
            calls.append((method, url))
            if method == "POST": return {"metadata": {"doi": "10.5281/zenodo.123"}}
            return {"checksum": hashlib.md5(data).hexdigest()} if method == "PUT" and "/api/files/" in url else {}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "Paper with space.pdf"
            path.write_bytes(b"%PDF-dummy")
            with mock.patch.object(DATED, "metadata_payload", return_value={"metadata": {}}), \
                 mock.patch.object(DATED, "ensure_draft", return_value={"id": 123, "metadata": {}, "links": {"bucket": "https://zenodo.org/api/files/bucket"}}), \
                 mock.patch.object(DATED, "upload_files", return_value=[path]), \
                 mock.patch.object(DATED, "snapshot_uploads", return_value={path.name: path.read_bytes()}), \
                 mock.patch.object(DATED, "check_draft_files"), \
                 mock.patch.object(DATED, "verification_coverage_report"), mock.patch.object(DATED, "verify_manuscript_readback"), \
                 mock.patch.object(DATED, "api_call", side_effect=api):
                self.assertEqual(DATED.publish_bundle(root, DUMMY, enforce_new_artifacts=True), "10.5281/zenodo.123")
        self.assertIn(("PUT", "https://zenodo.org/api/files/bucket/Paper%20with%20space.pdf"), calls)


if __name__ == "__main__":
    unittest.main()
