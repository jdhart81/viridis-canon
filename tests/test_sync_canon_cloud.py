from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.sync_canon_cloud import main


class _Response:
    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return b'{"imported":1,"unchanged":0}'


class CanonCloudSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.catalog = Path(self.temporary.name) / "catalog.json"
        self.catalog.write_text(
            json.dumps({"catalog_digest": "abc", "records": [{"record_id": "one"}]}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @patch("tools.sync_canon_cloud.urlopen")
    def test_missing_configuration_skips_without_network(self, urlopen: object) -> None:
        result = main(["--catalog", str(self.catalog), "--url", "", "--secret", ""])
        self.assertEqual(result, 0)
        urlopen.assert_not_called()

    @patch("tools.sync_canon_cloud.urlopen", return_value=_Response())
    def test_sender_posts_catalog_and_source_ref(self, urlopen: object) -> None:
        result = main(
            [
                "--catalog",
                str(self.catalog),
                "--url",
                "https://canon.example/",
                "--secret",
                "test-secret",
                "--source-ref",
                "commit-123",
            ]
        )
        self.assertEqual(result, 0)
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://canon.example/api/integrations/catalog-sync",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-secret")
        payload = json.loads(request.data)
        self.assertEqual(payload["source_ref"], "commit-123")
        self.assertEqual(payload["catalog"]["catalog_digest"], "abc")
        self.assertNotIn("org", payload)
        self.assertNotIn("actor", payload)


if __name__ == "__main__":
    unittest.main()
