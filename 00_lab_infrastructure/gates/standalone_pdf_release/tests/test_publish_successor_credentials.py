"""Credential boundary tests: mocked HTTP and dummy credentials only."""

import contextlib
import copy
import hashlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import urllib.error
import urllib.parse
import urllib.request


TOKEN = "DUMMY_CREDENTIAL_" + "x" * 40
COPYRIGHT = "Copyright © 2026 Example Research"


def legacy_public_gate(record, preflight):
    # The production gate consumes legacy files:list. Native RDM rights reads
    # must not accidentally replace the separately checked public inventory.
    assert isinstance(record.get("files"), list)
    return {"state": "MOCK_READBACK", "server_value": TOKEN}


def local_preflight(bundle, paths):
    rows = []
    for path in paths:
        raw = path.read_bytes()
        rows.append({"filename": path.name, "sha256": hashlib.sha256(raw).hexdigest(),
                     "md5": hashlib.md5(raw).hexdigest(), "bytes": len(raw)})
    return {"state": "MOCK_PREFLIGHT", "upload_files": sorted(rows, key=lambda row: row["filename"])}


GATE = types.SimpleNamespace(
    ManuscriptPDFHold=type("ManuscriptPDFHold", (RuntimeError,), {}),
    require_local=local_preflight,
    _read=lambda path: path.read_bytes(),
    require_public=legacy_public_gate,
)
SPEC = importlib.util.spec_from_file_location(
    "successor_credentials_under_test", Path(__file__).resolve().parents[1] / "publish_successor_wave.py"
)
PUBLISHER = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"manuscript_pdf_gate": GATE}):
    SPEC.loader.exec_module(PUBLISHER)


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.data


class SuccessorHTTP:
    """A legacy round trip drops copyright, requiring the RDM fallback."""
    def __init__(self):
        self.requests = []
        self.files = []
        self.metadata = {"title": "Retained scientific title", "creators": [{"name": "Example"}]}
        self.published = False
        self.rdm_updates = []

    def open(self, request, timeout):
        self.requests.append(request)
        assert TOKEN not in request.full_url
        assert request.get_header("Authorization") == "Bearer " + TOKEN
        path = urllib.parse.urlsplit(request.full_url).path
        method = request.get_method()
        if path == "/api/records/100" and method == "GET":
            assert request.get_header("Accept") == "application/vnd.inveniordm.v1+json"
            return Response({"id": 100, "metadata": {"copyright": COPYRIGHT}})
        if path == "/api/records/100/draft" and method == "GET":
            raise urllib.error.HTTPError(request.full_url, 404, "missing", {}, io.BytesIO())
        if path == "/api/records/100/versions" and method == "POST":
            return Response({"id": 200})
        if path == "/api/records/200" and method == "GET":
            if not self.published:
                raise urllib.error.HTTPError(request.full_url, 404, "missing", {}, io.BytesIO())
            files = {"entries": {}} if request.get_header("Accept") == "application/vnd.inveniordm.v1+json" else []
            return Response({"id": 200, "metadata": {"doi": "10.5281/zenodo.200", **self.metadata}, "files": files})
        if path == "/api/deposit/depositions/200":
            if method == "PUT":
                metadata = json.loads(request.data)["metadata"]
                assert metadata["copyright"] == COPYRIGHT
                # Emulate the exact legacy-API data loss being fixed.
                self.metadata = {key: value for key, value in metadata.items() if key != "copyright"}
                return Response({})
            return Response({"id": 200, "files": self.files,
                             "links": {"bucket": "https://zenodo.org/api/files/bucket-id"}})
        if path.startswith("/api/files/bucket-id/") and method == "PUT":
            name = urllib.parse.unquote(path.rsplit("/", 1)[1])
            checksum = "md5:" + hashlib.md5(request.data).hexdigest()
            self.files.append({"filename": name, "checksum": checksum, "filesize": len(request.data)})
            return Response({"filename": name, "checksum": checksum})
        if path == "/api/records/200/draft":
            assert request.get_header("Accept") == "application/vnd.inveniordm.v1+json"
            if method == "PUT":
                metadata = json.loads(request.data)["metadata"]
                before = copy.deepcopy(self.metadata)
                self.metadata = metadata
                self.rdm_updates.append((before, copy.deepcopy(metadata)))
            return Response({"id": 200, "metadata": self.metadata})
        if path == "/api/deposit/depositions/200/actions/publish" and method == "POST":
            assert self.metadata["copyright"] == COPYRIGHT
            self.published = True
            return Response({"id": 200, "metadata": {"doi": "10.5281/zenodo.200"}})
        raise AssertionError(f"unexpected mocked request: {method} {path}")


class CredentialTests(unittest.TestCase):
    def test_token_travels_only_in_authorization_header(self):
        opener = types.SimpleNamespace(open=lambda request, **kwargs: Response({}))
        with patch.object(PUBLISHER.urllib.request, "build_opener", return_value=opener) as factory:
            PUBLISHER.api_call(TOKEN, "GET", "https://zenodo.org/api/records/100")
        self.assertIsInstance(factory.call_args.args[0], PUBLISHER.ZenodoRedirectHandler)

    def test_raw_space_in_upload_url_is_clean_hold(self):
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["publisher", "--wave-root", ".", "--expected-manifest-sha256", "a", "--publish", "--go"]), \
             patch.object(PUBLISHER, "credential", return_value=TOKEN), \
             patch.object(PUBLISHER, "load_and_validate_wave", return_value=[]), \
             patch.object(PUBLISHER, "json_write_atomic", side_effect=lambda *a, **k: PUBLISHER.api_call(
                 TOKEN, "PUT", "https://zenodo.org/api/files/bucket/Run 167 Paper.pdf", b"x")), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(PUBLISHER.main(), 2)
        self.assertIn('"state": "HOLD"', err.getvalue())
        self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())

    def test_http_error_body_is_redacted_in_exception_and_traceback(self):
        error = urllib.error.HTTPError("https://zenodo.org/api/records/1", 400, "bad", {}, io.BytesIO(TOKEN.encode()))
        opener = types.SimpleNamespace(open=lambda *args, **kwargs: (_ for _ in ()).throw(error))
        with patch.object(PUBLISHER.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(PUBLISHER.SuccessorPublisherError) as caught:
                PUBLISHER.api_call(TOKEN, "GET", "https://zenodo.org/api/records/1")
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertIn("***", str(caught.exception))
        self.assertTrue(caught.exception.__suppress_context__)

    def test_catch_all_main_redacts_invalid_url_exception(self):
        out, err = io.StringIO(), io.StringIO()
        error = http.client.InvalidURL("unexpected " + TOKEN)
        with patch.object(sys, "argv", ["publisher", "--wave-root", ".", "--expected-manifest-sha256", "a", "--publish", "--go"]), \
             patch.object(PUBLISHER, "credential", return_value=TOKEN), \
             patch.object(PUBLISHER, "load_and_validate_wave", return_value=[{"abbreviation": "XX", "predecessor_doi": "10.5281/zenodo.100", "new_version": "v2", "upload_names": (), "bundle": Path(".")}]), \
             patch.object(PUBLISHER, "publish_candidate", side_effect=error), \
             contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(PUBLISHER.main(), 2)
        self.assertIn("InvalidURL", err.getvalue())
        self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())

    def test_query_credential_is_rejected_before_http(self):
        for query in ("access_token=x", "ACCESS_TOKEN=x", "access%5Ftoken=x", "access%255Ftoken=x"):
            with self.subTest(query=query), patch.object(PUBLISHER.urllib.request, "build_opener") as opener:
                with self.assertRaises(PUBLISHER.SuccessorPublisherError):
                    PUBLISHER.api_call(TOKEN, "GET", "https://zenodo.org/api/records/1?" + query)
                opener.assert_not_called()

    def test_destinations_fail_closed(self):
        for url in ("http://zenodo.org/api/records/1", "https://zenodo.org.evil.invalid/api/a",
                    "https://user@zenodo.org/api/a", "https://zenodo.org:444/api/a",
                    "https://zenodo.org/api/a#fragment", "https://zenodo.org/not-api/a",
                    "https://zenodo.org/api/a?other=" + TOKEN):
            with self.subTest(url=url.replace(TOKEN, "***")):
                with self.assertRaises(PUBLISHER.SuccessorPublisherError):
                    PUBLISHER.api_call(TOKEN, "GET", url)
        with patch.object(PUBLISHER, "BASE", "https://sandbox.zenodo.org/api"):
            self.assertEqual(PUBLISHER.validated_zenodo_url("https://sandbox.zenodo.org/api/a"),
                             "https://sandbox.zenodo.org/api/a")

    def test_direct_bucket_requests_stay_on_configured_credential_origin(self):
        for base, foreign in (("https://zenodo.org/api", "sandbox.zenodo.org"),
                              ("https://sandbox.zenodo.org/api", "zenodo.org")):
            with self.subTest(base=base), patch.object(PUBLISHER, "BASE", base), \
                 patch.object(PUBLISHER.urllib.request, "build_opener") as factory:
                with self.assertRaises(PUBLISHER.SuccessorPublisherError):
                    PUBLISHER.api_call(TOKEN, "PUT", f"https://{foreign}/api/files/bucket/paper.pdf", b"x")
                factory.assert_not_called()

    def test_configured_sandbox_requests_use_only_sandbox_and_header_credentials(self):
        captured=[]
        def opened(request, **kwargs):
            captured.append(request)
            return Response({})
        opener=types.SimpleNamespace(open=opened)
        with patch.object(PUBLISHER, "BASE", "https://sandbox.zenodo.org/api"), \
             patch.object(PUBLISHER.urllib.request, "build_opener", return_value=opener):
            PUBLISHER.api_call(TOKEN, "GET", "https://sandbox.zenodo.org/api/records/100")
        self.assertEqual(len(captured),1)
        self.assertEqual(captured[0].full_url,"https://sandbox.zenodo.org/api/records/100")
        self.assertEqual(captured[0].get_header("Authorization"),"Bearer "+TOKEN)
        self.assertNotIn(TOKEN,captured[0].full_url)

    def test_invalid_configured_base_cannot_authorize_any_request(self):
        for base in ("http://zenodo.org/api","https://evil.invalid/api", "https://zenodo.org:444/api",
                     "https://user@zenodo.org/api", "https://zenodo.org/not-api", "https://zenodo.org/api?x=1",
                     "https://zenodo.org/api#fragment", " https://zenodo.org/api"):
            with self.subTest(base=base), patch.object(PUBLISHER,"BASE",base), \
                 patch.object(PUBLISHER.urllib.request,"build_opener") as factory:
                with self.assertRaises(PUBLISHER.SuccessorPublisherError):
                    PUBLISHER.api_call(TOKEN,"GET","https://zenodo.org/api/records/100")
                factory.assert_not_called()

    def test_redirects_cannot_forward_header_to_another_origin(self):
        request = urllib.request.Request("https://zenodo.org/api/a", headers={"Authorization": "Bearer " + TOKEN})
        handler = PUBLISHER.ZenodoRedirectHandler()
        for target in ("https://evil.invalid/api/a", "https://sandbox.zenodo.org/api/a", "https://zenodo.org/api/a?access_token=x",
                       "https://zenodo.org/api/a?other=" + TOKEN):
            with self.subTest(target=target.replace(TOKEN, "***")), self.assertRaises(PUBLISHER.SuccessorPublisherError):
                handler.redirect_request(request, None, 302, "Found", {}, target)
        redirected = handler.redirect_request(request, None, 302, "Found", {}, "https://zenodo.org/api/b")
        self.assertEqual(redirected.get_header("Authorization"), "Bearer " + TOKEN)
        self.assertNotIn(TOKEN, redirected.full_url)

    def test_uncertain_post_is_not_blindly_retried(self):
        opener = types.SimpleNamespace(open=lambda *a, **k: (_ for _ in ()).throw(urllib.error.URLError(TOKEN)))
        with patch.object(PUBLISHER.urllib.request, "build_opener", return_value=opener), \
             patch.object(PUBLISHER.time, "sleep") as sleep:
            with self.assertRaises(PUBLISHER.SuccessorPublisherError) as caught:
                PUBLISHER.api_call(TOKEN, "POST", "https://zenodo.org/api/records/100/versions", b"{}")
        self.assertNotIn(TOKEN, str(caught.exception))
        sleep.assert_not_called()

    def test_end_to_end_successor_has_encoded_upload_copyright_and_redacted_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bundle = root / "XX"
            bundle.mkdir()
            name = "Run 167 Paper.pdf"
            (bundle / name).write_bytes(b"%PDF-1.4 dummy mocked content")
            candidate = {"abbreviation": "XX", "predecessor_doi": "10.5281/zenodo.100", "new_version": "v2",
                         "bundle": bundle, "upload_names": (name,), "metadata": {"metadata": {"title": "Retained scientific title", "creators": [{"name": "Example"}]}}}
            candidate["approved_preflight_json"] = json.dumps(local_preflight(bundle, [bundle / name]))
            http = SuccessorHTTP()
            out, err = io.StringIO(), io.StringIO()
            with patch.object(PUBLISHER, "ROOT", root), \
                 patch.object(PUBLISHER.urllib.request, "build_opener", return_value=http), \
                 patch.object(PUBLISHER, "load_and_validate_wave", return_value=[candidate]), \
                 patch.object(PUBLISHER, "credential", return_value=TOKEN), \
                 patch.object(sys, "argv", ["publisher", "--wave-root", str(root), "--expected-manifest-sha256", "a", "--publish", "--go"]), \
                 contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(PUBLISHER.main(), 0, err.getvalue())
            urls = [request.full_url for request in http.requests]
            self.assertIn("https://zenodo.org/api/files/bucket-id/Run%20167%20Paper.pdf", urls)
            self.assertEqual(len(http.rdm_updates), 1)
            before, after = http.rdm_updates[0]
            self.assertEqual(after, {**before, "copyright": COPYRIGHT})
            self.assertNotIn(TOKEN, out.getvalue() + err.getvalue())
            receipts = [path for path in root.rglob("*") if path.is_file() and path.name != name]
            self.assertGreaterEqual(len(receipts), 4)
            for path in receipts:
                self.assertNotIn(TOKEN.encode(), path.read_bytes(), str(path))

    def test_copyright_fallback_holds_on_unplanned_metadata_diff(self):
        responses = iter([
            {"metadata": {"title": "Approved", "creators": [{"name": "Example"}]}}, {},
            {"metadata": {"title": "Changed unexpectedly", "creators": [{"name": "Example"}], "copyright": COPYRIGHT}},
        ])
        with patch.object(PUBLISHER, "api_call", side_effect=lambda *a, **k: next(responses)), \
             patch.object(PUBLISHER, "json_write_atomic"):
            with self.assertRaises(PUBLISHER.SuccessorPublisherError):
                PUBLISHER.preserve_draft_copyright({"expected_copyright": COPYRIGHT, "bundle": Path("."),
                                                  "predecessor_doi": "10.5281/zenodo.100"}, TOKEN, "200")

    def test_public_gate_inventory_stays_legacy_while_copyright_readback_is_native(self):
        http = SuccessorHTTP()
        http.published = True
        http.metadata["copyright"] = COPYRIGHT
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(PUBLISHER, "ROOT", Path(temporary)), \
             patch.object(PUBLISHER.urllib.request, "build_opener", return_value=http):
            name = "paper.pdf"
            bundle = Path(temporary)
            (bundle / name).write_bytes(b"%PDF-dummy")
            PUBLISHER.verify_manuscript_readback(
                {"bundle": bundle, "upload_names": (name,), "expected_copyright": COPYRIGHT,
                 "approved_preflight_json": json.dumps(local_preflight(bundle, [bundle / name]))},
                TOKEN, "10.5281/zenodo.200")
        accepts = [request.get_header("Accept") for request in http.requests]
        self.assertEqual(accepts, ["application/json", "application/vnd.inveniordm.v1+json"])


if __name__ == "__main__":
    unittest.main()
