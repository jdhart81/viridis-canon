"""The active wrapper never mirrors after a failed publication readback."""
import base64
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SPEC = importlib.util.spec_from_file_location("active_lockstep_hardening", Path(__file__).parents[1] / "weekend_canon_lockstep.py")
L = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = L
SPEC.loader.exec_module(L)
TOKEN = "test-pat-" + "t" * 40


class LockstepHardeningTests(unittest.TestCase):
    def test_doi_prefix_is_production_only(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "PUBLISHED_DOI.txt"
            for doi in ("10.5072/zenodo.777", "10.99999/zenodo.777", "10.5281/zenodo.777/extra"):
                path.write_text(doi)
                with self.assertRaisesRegex(L.LockstepError, "invalid production DOI"):
                    L.read_doi(path)
            path.write_text("10.5281/zenodo.777")
            self.assertEqual(L.read_doi(path), "10.5281/zenodo.777")

    def test_git_pat_is_only_in_process_local_http_header(self):
        with mock.patch.object(L, "run", return_value=SimpleNamespace(returncode=0)) as run:
            L.git(Path("/mock/repository"), "push", "origin", "HEAD:test", token=TOKEN)
        argv = run.call_args.args[0]
        env = run.call_args.kwargs["env"]
        self.assertNotIn(TOKEN, repr(argv))
        self.assertEqual(env["GIT_CONFIG_KEY_0"], "http.https://github.com/.extraHeader")
        authorization = env["GIT_CONFIG_VALUE_0"]
        self.assertEqual(base64.b64decode(authorization.removeprefix("Authorization: Basic ")).decode(), "x-access-token:" + TOKEN)
        self.assertEqual(env["GIT_CONFIG_KEY_1"], "http.followRedirects")
        self.assertEqual(env["GIT_CONFIG_VALUE_1"], "false")
        self.assertIn(authorization.split()[-1], run.call_args.kwargs["secrets"])

    def test_rehearsal_abbreviations_refused_before_discovery(self):
        for option in ("--rehearse", "--reh", "--re", "--rehearse=true"):
            with mock.patch.object(L, "discover_bundles") as discover:
                with self.assertRaisesRegex(L.LockstepError, "rehearsal cannot enter"):
                    L.main(["--date", "2026-10-16", "--", "publisher", option])
                discover.assert_not_called()

    def test_failed_publisher_with_existing_doi_cannot_mirror(self):
        calls = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); work = root / "work"; work.mkdir()
            row = SimpleNamespace(path=root, git_build_root=None, doi="10.5281/zenodo.777", abbreviation="XX")
            (root / "PUBLISHED_DOI.txt").write_text(row.doi)
            def run(argv, **kwargs):
                calls.append((argv, kwargs))
                return SimpleNamespace(returncode=2 if argv[0] == "reviewed-publisher" else 0)
            with (mock.patch.object(L, "discover_bundles", return_value=[row]),
                  mock.patch.object(L, "print_plan"), mock.patch.object(L, "read_github_token", return_value=TOKEN),
                  mock.patch.object(L.tempfile, "mkdtemp", return_value=str(work)),
                  mock.patch.object(L, "run", side_effect=run), mock.patch.object(L, "probe_git_write"),
                  mock.patch.object(L, "preflight_release"), mock.patch.object(L, "verification_coverage_report"),
                  mock.patch.object(L, "copy_payload"), mock.patch.object(L, "refresh_dois") as refresh,
                  mock.patch.object(L, "create_commit") as commit, mock.patch.object(L, "push_commit") as push,
                  mock.patch.object(L, "write_receipt") as receipt, contextlib.redirect_stdout(io.StringIO())):
                with self.assertRaisesRegex(L.LockstepError, "mirroring is forbidden"):
                    L.main(["--date", "2026-10-16", "--go", "--enforce-new-artifacts", "--",
                            "reviewed-publisher", "--publish", "--enforce-new-artifacts"])
                refresh.assert_not_called(); commit.assert_not_called(); push.assert_not_called(); receipt.assert_not_called()
            clone, options = calls[0]
            self.assertEqual(clone[:4], ["git", "clone", "--quiet", L.PUBLIC_REPO_URL])
            self.assertNotIn(TOKEN, repr(clone))
            self.assertIn("Authorization: Basic ", options["env"]["GIT_CONFIG_VALUE_0"])

    def test_fresh_recovery_invocation_cannot_mirror_persisted_uncertain_doi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); work=root/'work'; work.mkdir()
            row=SimpleNamespace(path=root,git_build_root=None,doi='10.5281/zenodo.777',abbreviation='XX')
            (root/'PUBLISHED_DOI.txt').write_text(row.doi)
            with (mock.patch.object(L,'discover_bundles',return_value=[row]),mock.patch.object(L,'print_plan'),
                  mock.patch.object(L,'read_github_token',return_value=TOKEN),
                  mock.patch.object(L.tempfile,'mkdtemp',return_value=str(work)),
                  mock.patch.object(L,'run',return_value=SimpleNamespace(returncode=0)),
                  mock.patch.object(L,'probe_git_write'),mock.patch.object(L,'preflight_release'),
                  mock.patch.object(L,'verification_coverage_report'),mock.patch.object(L,'copy_payload'),
                  mock.patch.object(L,'refresh_dois',return_value=[row]),
                  mock.patch.object(L,'verify_publication_readbacks',side_effect=L.LockstepError('current public upload/PDF readback HOLD')) as readback,
                  mock.patch.object(L,'create_commit') as commit,mock.patch.object(L,'push_commit') as push,
                  contextlib.redirect_stdout(io.StringIO())):
                with self.assertRaisesRegex(L.LockstepError,'current public upload/PDF readback HOLD'):
                    L.main(['--date','2026-10-16','--go','--enforce-new-artifacts'])
                readback.assert_called_once_with([row]);commit.assert_not_called();push.assert_not_called()

    def test_backfill_requires_fresh_exact_anonymous_file_and_pdf_readbacks(self):
        import hashlib,json
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); bundle=root/'XX';bundle.mkdir(); receipts=root/'receipts'
            data=b'%PDF-1.4 exact public manuscript';(bundle/'paper.pdf').write_bytes(data)
            (bundle/'PUBLISHED_DOI.txt').write_text('10.5281/zenodo.777')
            row=SimpleNamespace(path=bundle,doi='10.5281/zenodo.777')
            record={'id':777,'doi':row.doi,'files':[{'key':'paper.pdf','size':len(data),'checksum':'md5:'+hashlib.md5(data).hexdigest()}]}
            gate=L.reviewed_manuscript_gate();calls=[]
            def public(url):
                calls.append(url)
                return json.dumps(record).encode() if url.endswith('/records/777') else data
            gate['_public_bytes']=public
            with mock.patch.object(L,'reviewed_manuscript_gate',return_value=gate),mock.patch.object(L,'RECEIPT_DIR',receipts):
                result=L.verify_publication_readbacks([row])
                self.assertEqual(result[0]['state'],'CURRENT_PUBLIC_READBACK_VERIFIED')
                self.assertEqual(len(calls),2)
                self.assertEqual(result[0]['readback']['upload_files'][0]['sha256'],hashlib.sha256(data).hexdigest())
                record['files'][0]['checksum']='md5:'+'0'*32
                with self.assertRaisesRegex(L.LockstepError,'mirroring forbidden'):
                    L.verify_publication_readbacks([row])
            saved=[json.loads(p.read_text()) for p in receipts.rglob('*.json')]
            self.assertEqual(len(saved),2)
            self.assertEqual({r['state'] for r in saved},{'HOLD_PUBLIC_READBACK','CURRENT_PUBLIC_READBACK_VERIFIED'})

    def test_readback_gate_rejects_ambient_replacement_and_tampered_source(self):
        gate=L.reviewed_manuscript_gate()
        self.assertNotEqual(gate['__name__'],'manuscript_pdf_gate')
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve();(root/'manuscript_pdf_gate.py').write_text('raise RuntimeError("ambient executed")')
            with mock.patch.object(L,'HERE',root):
                with self.assertRaisesRegex(L.LockstepError,'reviewed manuscript readback source differs'):
                    L.reviewed_manuscript_gate()
