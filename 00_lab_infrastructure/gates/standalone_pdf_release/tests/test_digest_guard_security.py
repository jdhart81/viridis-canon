"""The outer PDF guard never prints credential-bearing controller diagnostics."""
from __future__ import annotations

import contextlib
import hashlib
from io import BytesIO, StringIO
import json
from pathlib import Path
import sys
import tempfile
import traceback
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import guard_methods_digest_release as guard
import manuscript_pdf_gate as gate
import publish_dated_bundles as publisher

DUMMY_TOKEN = "DUMMY_TOKEN_FOR_GUARD_TESTS_0123456789"


class DigestGuardSecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.package = self.root / "bundle"; self.package.mkdir()
        self.output = self.root / "reports/dispatch"; self.output.mkdir(parents=True)
        self.config = self.root / "CONFIG.json"; self.controller = self.root / "controller.py"
        paper = b"%PDF-1.4\nactual manuscript\n%%EOF"
        (self.package / "Run-167-Paper.pdf").write_bytes(paper)
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("notes/Run-167/paper.pdf", paper)
        (self.package / "METHODS_NOTES.zip").write_bytes(stream.getvalue())
        self.manifest = {"notes": [{"run_id": "Run-167", "uploads": [{"filename": "paper.pdf", "sha256": hashlib.sha256(paper).hexdigest()}]}],
                         "uploads": [{"filename": "Run-167-Paper.pdf", **gate._hashes(paper)}, {"filename": "METHODS_NOTES.zip"}]}
        self.write_manifest(self.manifest)
        self.configure("def execute(config, output, token):\n    return {'published': True, 'record_id': '123', 'doi': '10.5281/zenodo.123'}\n")

    def write_manifest(self, value):
        (self.package / "DIGEST_MANIFEST.json").write_text(json.dumps(value))

    def configure(self, source):
        self.controller.write_text(source)
        self.config.write_text(json.dumps({"package": str(self.package), "canonical_root": str(self.root),
            "controller": {"path": "controller.py", "sha256": hashlib.sha256(self.controller.read_bytes()).hexdigest()}}))
        self.digest = hashlib.sha256(self.config.read_bytes()).hexdigest()

    def test_malformed_config_and_inventory_shapes_hold_cleanly(self):
        for value in ([], None, "bad", {"package": []}, {}):
            with self.subTest(config=value):
                self.config.write_text(json.dumps(value)); digest = hashlib.sha256(self.config.read_bytes()).hexdigest()
                with self.assertRaises(gate.ManuscriptPDFHold):
                    guard.preflight(self.config, digest)
        self.configure(self.controller.read_text())
        for value in ([], None, "bad", {"uploads": None}, {"uploads": [None]}, {"uploads": [{"filename": []}]},
                      {"uploads": [{"filename": "../outside.pdf"}]}, {"uploads": [{"filename": ""}]}):
            with self.subTest(manifest=value):
                self.write_manifest(value)
                with self.assertRaises(gate.ManuscriptPDFHold):
                    guard.preflight(self.config, self.digest)

    def test_pdf_gate_runs_before_credential_loading(self):
        (self.package / "Run-167-Paper.pdf").unlink()
        with mock.patch.object(publisher, "token") as loader:
            with self.assertRaises(gate.ManuscriptPDFHold):
                guard.dispatch(self.config, self.digest, self.output)
        loader.assert_not_called()

    def test_controller_exception_and_python_streams_do_not_escape(self):
        self.configure("import sys\nprint('import diagnostic suppressed')\ndef execute(config, output, token):\n    print(token)\n    print(token, file=sys.stderr)\n    raise RuntimeError('private credential ' + token)\n")
        out = StringIO(); err = StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(publisher, "token", return_value=DUMMY_TOKEN):
            try:
                guard.dispatch(self.config, self.digest, self.output)
            except gate.ManuscriptPDFHold as exc:
                rendered = "".join(traceback.format_exception(exc))
            else:
                self.fail("controller exception was not held")
        self.assertNotIn(DUMMY_TOKEN, rendered + out.getvalue() + err.getvalue())
        self.assertEqual(out.getvalue(), ""); self.assertEqual(err.getvalue(), "")

    def test_credential_bearing_result_is_refused_before_readback_or_receipt(self):
        self.configure("def execute(config, output, token):\n    return {'published': True, 'record_id': '123', 'doi': '10.5281/zenodo.123', 'raw': token}\n")
        with mock.patch.object(publisher, "token", return_value=DUMMY_TOKEN), mock.patch.object(gate, "public_record") as public:
            with self.assertRaises(gate.ManuscriptPDFHold) as held:
                guard.dispatch(self.config, self.digest, self.output)
        self.assertNotIn(DUMMY_TOKEN, str(held.exception)); public.assert_not_called()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_clean_controller_result_retains_public_readback_and_safe_receipt(self):
        self.configure("import sys\ndef execute(config, output, token):\n    print(token)\n    print(token, file=sys.stderr)\n    return {'published': True, 'record_id': '123', 'doi': '10.5281/zenodo.123'}\n")
        out = StringIO(); err = StringIO(); receipt = {"status": "TEST_PUBLIC_READBACK", "certifies": False}
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch.object(publisher, "token", return_value=DUMMY_TOKEN), \
             mock.patch.object(gate, "public_record", return_value={"id": 123, "doi": "10.5281/zenodo.123"}) as public, \
             mock.patch.object(gate, "require_public", return_value=receipt) as readback:
            result = guard.dispatch(self.config, self.digest, self.output)
        public.assert_called_once_with("123"); readback.assert_called_once()
        self.assertEqual(result["standalone_manuscript_pdf_readback"], receipt)
        persisted = (self.output / "STANDALONE_MANUSCRIPT_PDF_READBACK.json").read_text()
        self.assertNotIn(DUMMY_TOKEN, persisted + json.dumps(result) + out.getvalue() + err.getvalue())

    def test_main_catchall_never_echoes_unexpected_exception_text(self):
        out = StringIO(); err = StringIO()
        with mock.patch.object(guard, "dispatch", side_effect=RuntimeError(DUMMY_TOKEN)), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = guard.main(["--config", str(self.config), "--expected-config-sha256", self.digest, "--go", "--output", str(self.output)])
        self.assertEqual(result, 1)
        self.assertNotIn(DUMMY_TOKEN, out.getvalue() + err.getvalue())
        self.assertIn("HOLD_STANDALONE_MANUSCRIPT_PDF", err.getvalue())


if __name__ == "__main__":
    unittest.main()
