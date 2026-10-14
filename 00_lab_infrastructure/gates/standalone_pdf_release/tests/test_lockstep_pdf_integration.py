"""Exercise the historical lockstep's publisher dispatch with mocked HTTP.

The sealed wrapper is read without changing its bytes. Git/science admission is
mocked here; these tests establish the PDF behavior at its publisher boundary.
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zipfile

import test_dated_exact_uploads as exact

SCRIPT = (Path(__file__).resolve().parents[2] / "production_snapshots" /
          "phase5-20261004/after/_ZENODO_DEPOSITS/weekend_canon_lockstep.py")
SPEC = importlib.util.spec_from_file_location("_lockstep_pdf_integration", SCRIPT)
lockstep = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = lockstep
SPEC.loader.exec_module(lockstep)


class DispatchFinished(Exception):
    pass


class LockstepPDFIntegrationTests(unittest.TestCase):
    @contextlib.contextmanager
    def dispatch(self, root, bundle):
        calls = []
        def run(argv, **kwargs):
            if argv[0] == "mock-reviewed-publisher":
                calls.append("publisher")
                exact.publisher.publish_bundle(bundle, exact.TOKEN,
                                               enforce_new_artifacts=True)
            return SimpleNamespace(returncode=0)
        row = SimpleNamespace(path=bundle, git_build_root=None)
        temporary = root / "mock-git-clone"
        temporary.mkdir()
        with (mock.patch.object(lockstep, "discover_bundles", return_value=[row]),
              mock.patch.object(lockstep, "print_plan"),
              mock.patch.object(lockstep, "read_github_token", return_value="dummy-git"),
              mock.patch.object(lockstep.tempfile, "mkdtemp", return_value=str(temporary)),
              mock.patch.object(lockstep, "run", side_effect=run),
              mock.patch.object(lockstep, "probe_git_write"),
              mock.patch.object(lockstep, "preflight_release"),
              mock.patch.object(lockstep, "verification_coverage_report"),
              mock.patch.object(lockstep, "copy_payload"),
              mock.patch.object(lockstep, "refresh_dois", side_effect=DispatchFinished),
              contextlib.redirect_stdout(io.StringIO())):
            yield calls

    def invoke(self):
        return lockstep.main(["--date", "2026-08-02", "--go",
                              "--enforce-new-artifacts", "--",
                              "mock-reviewed-publisher", "--publish",
                              "--enforce-new-artifacts"])

    def test_archived_only_paper_holds_through_lockstep_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); fixture = exact.DatedExactUploadsTests()
            bundle = fixture.make_bundle(root, archive=True)
            with zipfile.ZipFile(bundle / "reproduction.zip", "w") as archive:
                archive.writestr("papers/hidden-paper.pdf", b"%PDF-hidden-paper")
            binding_path = bundle / "RELEASE_BINDING.json"
            binding = json.loads(binding_path.read_text())
            binding["final_artifact_sha256"] = exact.publisher.release_coherence.tree_hashes(bundle)
            binding_path.write_text(json.dumps(binding))
            with fixture.server(root, bundle) as (_, http_calls, _):
                with self.dispatch(root, bundle) as calls:
                    with self.assertRaisesRegex(exact.publisher.PublisherError,
                                                "byte-identical separate PDF"):
                        self.invoke()
            self.assertEqual(calls, ["publisher"])
            self.assertEqual(http_calls, [])

    def test_valid_bundle_gets_full_public_readback_through_lockstep(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); fixture = exact.DatedExactUploadsTests()
            bundle = fixture.make_bundle(root, archive=True)
            with fixture.server(root, bundle) as (uploaded, http_calls, snapshots):
                with self.dispatch(root, bundle) as calls:
                    with self.assertRaises(DispatchFinished):
                        self.invoke()
            self.assertEqual(calls, ["publisher"])
            self.assertTrue(any(method == "POST" for method, _, _ in http_calls))
            self.assertEqual(set(uploaded), {row["filename"] for row in snapshots[0]["upload_files"]})
            receipt = root / "reports/publication-manuscript-pdf-readback/12345678/MANUSCRIPT_PDF_READBACK.json"
            self.assertEqual(set(uploaded), {row["filename"] for row in json.loads(receipt.read_text())["upload_files"]})


if __name__ == "__main__":
    unittest.main()
