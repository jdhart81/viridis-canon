from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.error


SCRIPT = Path(__file__).resolve().parents[1] / "publish_dated_bundles.py"
SPEC = importlib.util.spec_from_file_location("publish_dated_bundles", SCRIPT)
publisher = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = publisher
SPEC.loader.exec_module(publisher)


class PublishDatedBundlesTests(unittest.TestCase):
    def make_bundle(self, root: Path) -> Path:
        bundle = root / "2026-08-02_EXR_standalone"
        bundle.mkdir()
        (bundle / "zenodo_metadata.json").write_text(
            json.dumps(
                {
                    "metadata": {
                        "title": "Example",
                        "license": "cc-by-4.0",
                        "description": "Public working-corpus release.",
                        "notes": "Lean checks the stated mathematics.",
                    }
                }
            ),
            encoding="utf-8",
        )
        (bundle / "RIGHTS_AND_LICENSE.md").write_text(
            publisher.release_coherence.assigned_rights_notice("Example", "cc-by-4.0"),
            encoding="utf-8",
        )
        (bundle / "BUNDLE_MANIFEST.json").write_text(
            json.dumps(
                {
                    "source_finalized": "/private/local/path",
                    "package_completeness": {
                        "license_gate": "ASSIGNED_CC_BY_4_0",
                        "status": "READY_FOR_PUBLICATION",
                    },
                }
            ),
            encoding="utf-8",
        )
        (bundle / "LEDGER_BINDING.json").write_text(
            json.dumps({"approved_by": "Justin D. Hart"}), encoding="utf-8"
        )
        (bundle / "paper.pdf").write_bytes(b"%PDF-example")
        (bundle / "RELEASE_BINDING.json").write_text(
            json.dumps(
                {
                    "license": "cc-by-4.0",
                    "approved_by": "Justin D. Hart",
                    "final_artifact_sha256": publisher.release_coherence.tree_hashes(bundle),
                }
            ),
            encoding="utf-8",
        )
        return bundle

    def test_plan_is_local_and_lists_exact_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_bundle(root)
            result = publisher.plan("2026-08-02", root)
            self.assertFalse(result["external_mutation"])
            self.assertEqual(
                result["bundles"][0]["files"],
                ["RIGHTS_AND_LICENSE.md", "paper.pdf"],
            )

    def test_plan_rejects_assigned_metadata_with_unassigned_rights_notice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root)
            (bundle / "RIGHTS_AND_LICENSE.md").write_text(
                "Current gate: HOLD_UNASSIGNED\nNo license is granted.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(publisher.PublisherError, "conflicts"):
                publisher.plan("2026-08-02", root)

    def test_published_bundle_is_idempotently_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.make_bundle(Path(temp))
            (bundle / "PUBLISHED_DOI.txt").write_text("10.5281/zenodo.99999999\n", encoding="utf-8")
            with mock.patch.object(publisher, "api_call") as api:
                doi = publisher.publish_bundle(bundle, "secret")
            self.assertEqual(doi, "10.5281/zenodo.99999999")
            api.assert_not_called()

    def test_existing_draft_is_reused_not_recreated(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = self.make_bundle(Path(temp))
            (bundle / "ZENODO_DRAFT_ID.txt").write_text("123\n", encoding="utf-8")
            with mock.patch.object(
                publisher,
                "api_call",
                return_value={"id": 123, "links": {"bucket": "https://example.invalid/bucket"}},
            ) as api:
                draft = publisher.ensure_draft(bundle, "secret")
            self.assertEqual(draft["id"], 123)
            self.assertEqual(api.call_args.args[1], "GET")

    def test_conflicting_receipt_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "receipt.txt"
            path.write_text("first\n", encoding="utf-8")
            with self.assertRaises(publisher.PublisherError):
                publisher.write_once(path, "second")

    def test_bucket_upload_uses_binary_content_type(self):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"{}"
        with mock.patch.object(publisher.urllib.request.OpenerDirector, "open", return_value=response) as opened:
            publisher.api_call(
                "secret",
                "PUT",
                "https://zenodo.org/api/files/bucket/paper.pdf",
                b"%PDF-test",
                "application/octet-stream",
            )
        request = opened.call_args.args[0]
        self.assertEqual(request.headers["Content-type"], "application/octet-stream")

    def test_transient_gateway_error_is_retried(self):
        transient = urllib.error.HTTPError(
            "https://zenodo.org/api/files/bucket/paper.pdf",
            504,
            "Gateway Time-out",
            {},
            None,
        )
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"{}"
        with (
            mock.patch.object(
                publisher.urllib.request.OpenerDirector,
                "open",
                side_effect=[transient, response],
            ) as opened,
            mock.patch.object(publisher.time, "sleep") as slept,
        ):
            result = publisher.api_call(
                "secret",
                "PUT",
                "https://zenodo.org/api/files/bucket/paper.pdf",
                b"%PDF-test",
                "application/octet-stream",
            )
        self.assertEqual(result, {})
        self.assertEqual(opened.call_count, 2)
        slept.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
