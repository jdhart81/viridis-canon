"""Mocked HTTP regressions for the complete dated upload/publication path."""
import contextlib
import hashlib
import http.client
import io
import json
from pathlib import Path
import tempfile
import traceback
import unittest
from unittest import mock
import urllib.error
import urllib.parse
import zipfile

import test_publish_dated_bundles as original

publisher = original.publisher
DOI = "10.5281/zenodo.12345678"
TOKEN = "dummy-token-that-must-never-appear-in-output"


class DatedExactUploadsTests(unittest.TestCase):
    def make_bundle(self, root, extra_space_pdf=False, archive=False):
        bundle = original.PublishDatedBundlesTests().make_bundle(root)
        if extra_space_pdf:
            (bundle / "paper with space.pdf").write_bytes((bundle / "paper.pdf").read_bytes())
        if archive:
            with zipfile.ZipFile(bundle / "reproduction.zip", "w") as stream:
                stream.writestr("paper.pdf", (bundle / "paper.pdf").read_bytes())
        binding = json.loads((bundle / "RELEASE_BINDING.json").read_text())
        binding["final_artifact_sha256"] = publisher.release_coherence.tree_hashes(bundle)
        (bundle / "RELEASE_BINDING.json").write_text(json.dumps(binding))
        return bundle

    @contextlib.contextmanager
    def server(self, root, bundle, *, initial_extra=False, late_extra=False, bad_put_checksum=False,
               public_extra=False, corrupt_public_archive=False, mutate_after_upload=False):
        captured = {}; calls = []; snapshots = []
        gate_public = publisher.manuscript_pdf_gate.require_public
        initial = [{"filename": "stale.txt", "checksum": "0" * 32, "filesize": 0}] if initial_extra else []
        def api(credential, method, url, data=None, content_type="application/json", **kwargs):
            self.assertEqual(credential, TOKEN)
            calls.append((method, url, data))
            if method == "GET" and url.endswith("/files"):
                if not captured: return initial
                result = [{"filename": name, "checksum": hashlib.md5(raw).hexdigest(), "filesize": len(raw)} for name, raw in captured.items()]
                if late_extra: result += [{"filename": "late.txt", "checksum": "0" * 32, "filesize": 0}]
                return result
            if method == "PUT" and "/api/files/" in url:
                name = urllib.parse.unquote(url.rsplit("/", 1)[1]); captured[name] = data
                if mutate_after_upload and name == "paper.pdf":
                    (bundle / "paper.pdf").write_bytes(b"%PDF-mutated-after-snapshot")
                return {"checksum": "md5:" + ("0" * 32 if bad_put_checksum else hashlib.md5(data).hexdigest())}
            if method == "PUT": return {"id": 12345678}
            if method == "POST" and url.endswith("/actions/publish"):
                return {"id": 12345678, "metadata": {"doi": DOI}, "submitted": True, "state": "done"}
            if method == "GET" and "/records/" in url:
                files = [{"key": name, "size": len(raw), "checksum": "md5:" + hashlib.md5(raw).hexdigest()} for name, raw in captured.items()]
                if public_extra: files += [{"key": "extra.pdf", "size": 0, "checksum": "md5:" + "0" * 32}]
                return {"id": 12345678, "doi": DOI, "files": files}
            self.fail("unexpected request " + method + " " + url)
        def public(record, approved):
            snapshots.append(approved)
            def download(record_id, name):
                if corrupt_public_archive and name.endswith(".zip"): return b"corrupt"
                return captured[name]
            return gate_public(record, approved, download=download)
        deposition = {"id": 12345678, "links": {"bucket": "https://zenodo.org/api/files/bucket"},
                      "metadata": {"doi": DOI}, "submitted": False, "state": "inprogress"}
        with (mock.patch.object(publisher, "ROOT", root),
              mock.patch.object(publisher, "api_call", side_effect=api),
              mock.patch.object(publisher, "ensure_draft", return_value=deposition),
              mock.patch.object(publisher, "verification_coverage_report", return_value=None),
              mock.patch.object(publisher.manuscript_pdf_gate, "require_public", side_effect=public)):
            yield captured, calls, snapshots

    def test_correct_bundle_publishes_then_exactly_reads_every_file_and_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root, archive=True)
            with self.server(root, bundle) as (captured, calls, snapshots):
                result = publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertEqual(result, DOI)
            self.assertIn("reproduction.zip", captured)
            self.assertTrue(any(method == "POST" for method, _, _ in calls))
            self.assertEqual({row["filename"] for row in snapshots[0]["upload_files"]}, set(captured))
            receipt = json.loads((root / "reports/publication-manuscript-pdf-readback/12345678/MANUSCRIPT_PDF_READBACK.json").read_text())
            self.assertEqual({row["filename"] for row in receipt["upload_files"]}, set(captured))

    def test_reserved_draft_doi_is_not_treated_as_published(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            with self.server(root, bundle) as (captured, calls, _):
                publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertTrue(captured)
            self.assertEqual(sum(method == "POST" for method, _, _ in calls), 1)

    def test_draft_extra_file_holds_before_upload_or_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            with self.server(root, bundle, initial_extra=True) as (_, calls, _):
                with self.assertRaisesRegex(publisher.PublisherError, "outside the approved"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertFalse(any(method in {"PUT", "POST"} for method, _, _ in calls))

    def test_late_draft_extra_holds_before_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            with self.server(root, bundle, late_extra=True) as (_, calls, _):
                with self.assertRaisesRegex(publisher.PublisherError, "outside the approved"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_upload_uses_encoded_filename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root, extra_space_pdf=True)
            with self.server(root, bundle) as (_, calls, _):
                publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertTrue(any("paper%20with%20space.pdf" in url for _, url, _ in calls))

    def test_put_checksum_mismatch_holds_before_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            with self.server(root, bundle, bad_put_checksum=True) as (_, calls, _):
                with self.assertRaisesRegex(publisher.PublisherError, "PUT response checksum"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_uploaded_bytes_equal_hashed_snapshot_and_local_mutation_holds(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root); approved = (bundle / "paper.pdf").read_bytes()
            with self.server(root, bundle, mutate_after_upload=True) as (captured, calls, _):
                with self.assertRaisesRegex(publisher.PublisherError, "inventory changed"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertEqual(captured["paper.pdf"], approved)
            self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_public_extra_preserves_minted_doi_and_holds_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            with self.server(root, bundle, public_extra=True):
                with self.assertRaisesRegex(publisher.PublisherError, "published DOI retained"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertEqual((bundle / "PUBLISHED_DOI.txt").read_text().strip(), DOI)

    def test_public_archive_download_is_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root, archive=True)
            with self.server(root, bundle, corrupt_public_archive=True):
                with self.assertRaisesRegex(publisher.PublisherError, "published DOI retained"):
                    publisher.publish_bundle(bundle, TOKEN, enforce_new_artifacts=True)
            self.assertEqual((bundle / "PUBLISHED_DOI.txt").read_text().strip(), DOI)

    def test_snapshot_refuses_changed_bytes_before_external_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); bundle = self.make_bundle(root)
            approved = publisher.manuscript_pdf_gate.require_local(bundle, publisher.upload_files(bundle))
            (bundle / "paper.pdf").write_bytes(b"%PDF-changed")
            with self.assertRaisesRegex(publisher.PublisherError, "changed before snapshot"):
                publisher.snapshot_uploads(bundle, approved)

    def test_catch_all_redacts_token_from_unexpected_exception(self):
        with (mock.patch.object(publisher.sys, "argv", ["publish", "--date", "2026-10-14", "--publish", "--go", "--enforce-new-artifacts"]),
              mock.patch.object(publisher, "plan", return_value={}), mock.patch.object(publisher, "token", return_value=TOKEN),
              mock.patch.object(publisher, "bundles", return_value=[Path("bundle")]),
              mock.patch.object(publisher, "publish_bundle", side_effect=http.client.InvalidURL(TOKEN)),
              contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr):
            self.assertEqual(publisher.main(), 2)
        self.assertNotIn(TOKEN, stdout.getvalue() + stderr.getvalue())
        self.assertIn("***", stderr.getvalue())

    def test_uncertain_post_is_not_blindly_retried(self):
        with (mock.patch.object(publisher.urllib.request.OpenerDirector, "open", side_effect=urllib.error.URLError("uncertain")) as opened,
              mock.patch.object(publisher.time, "sleep") as slept):
            with self.assertRaises(publisher.PublisherError):
                publisher.api_call(TOKEN, "POST", "https://zenodo.org/api/deposit/depositions", b"{}")
        self.assertEqual(opened.call_count, 1); slept.assert_not_called()

    def test_configured_sandbox_refuses_cross_environment_redirect(self):
        with mock.patch.object(publisher, "BASE", "https://sandbox.zenodo.org/api"):
            self.assertEqual(publisher.validated_zenodo_url("https://sandbox.zenodo.org/api/files/bucket/paper.pdf"), "https://sandbox.zenodo.org/api/files/bucket/paper.pdf")
            with self.assertRaises(publisher.PublisherError): publisher.validated_zenodo_url("https://zenodo.org/api/files/bucket/paper.pdf")

    def test_credential_value_in_any_url_field_is_refused_before_http(self):
        with mock.patch.object(publisher.urllib.request.OpenerDirector, "open") as opened:
            for url in ("https://zenodo.org/api/records/1?diagnostic=" + TOKEN,
                        "https://zenodo.org/api/records/" + TOKEN,
                        "https://zenodo.org/api/records/1?diagnostic=" + urllib.parse.quote(TOKEN, safe="")):
                with self.subTest(url=url), self.assertRaises(publisher.PublisherError) as caught:
                    publisher.api_call(TOKEN, "GET", url)
                self.assertNotIn(TOKEN, str(caught.exception))
            opened.assert_not_called()

    def test_redirect_cannot_put_credential_in_url(self):
        request = publisher.urllib.request.Request("https://zenodo.org/api/records/1",
                    headers={"Authorization": "Bearer " + TOKEN})
        with self.assertRaises(publisher.PublisherError):
            publisher.ZenodoRedirectHandler().redirect_request(request, None, 302, "move", {},
                    "https://zenodo.org/api/records/2?diagnostic=" + TOKEN)

    def test_api_boundary_drops_credential_bearing_exception_causes(self):
        for error in (urllib.error.URLError(TOKEN), http.client.InvalidURL(TOKEN),
                      urllib.error.HTTPError("https://zenodo.org/api/" + TOKEN, 400, TOKEN, {}, io.BytesIO(TOKEN.encode()))):
            with self.subTest(error=type(error).__name__), mock.patch.object(publisher.time, "sleep"), \
                 mock.patch.object(publisher.urllib.request.OpenerDirector, "open", side_effect=error):
                try:
                    publisher.api_call(TOKEN, "GET", "https://zenodo.org/api/records/1")
                except publisher.PublisherError:
                    diagnostic = traceback.format_exc()
                else:
                    self.fail("unsafe transport exception was not held")
                self.assertNotIn(TOKEN, diagnostic)


if __name__ == "__main__":
    unittest.main()
