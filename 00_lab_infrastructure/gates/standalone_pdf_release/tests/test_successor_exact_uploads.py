"""Successor publication must retain its original approval across HTTP and DOI outcomes."""
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import urllib.parse

HERE = Path(__file__).resolve().parents[1]


def load(name, path, imports=None):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, imports or {}):
        spec.loader.exec_module(module)
    return module


gate = load("_successor_exact_actual_gate", HERE / "manuscript_pdf_gate.py")
publisher = load("_successor_exact_publisher", HERE / "publish_successor_wave.py", {"manuscript_pdf_gate": gate})
TOKEN = "DUMMY_SUCCESSOR_APPROVAL_" + "x" * 40
DOI = "10.5281/zenodo.200"


class SuccessorExactUploadsTests(unittest.TestCase):
    def make_wave(self, root):
        rows = []
        for abbreviation in ("AA", "BB", "CC", "DD", "EE", "FF", "GG"):
            bundle = root / abbreviation
            bundle.mkdir()
            (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 sealed manuscript")
            metadata = {"metadata": {"version": "v2", "license": "cc-by-4.0", "access_right": "open"}}
            (bundle / "zenodo_metadata.json").write_text(json.dumps(metadata))
            hashes = {name: publisher.sha256(bundle / name) for name in ("paper.pdf", "zenodo_metadata.json")}
            correction = {"abbreviation": abbreviation, "predecessor_doi": "10.5281/zenodo.100", "new_version": "v2",
                          "science_changed": False, "candidate_sha256": hashes,
                          "protected_unchanged_files": ["paper.pdf"], "original_sha256": {"paper.pdf": hashes["paper.pdf"]},
                          "zenodo_metadata_sha256": hashes["zenodo_metadata.json"]}
            path = bundle / "CORRECTION_MANIFEST.json"
            path.write_text(json.dumps(correction))
            rows.append({"abbreviation": abbreviation, "predecessor_doi": "10.5281/zenodo.100", "new_version": "v2",
                         "manifest": abbreviation + "/CORRECTION_MANIFEST.json", "manifest_sha256": publisher.sha256(path)})
        path = root / "WAVE_MANIFEST.json"
        path.write_text(json.dumps({"standard": "VRS-ZENODO-SUCCESSOR-WAVE-1", "candidate_count": 7,
                                    "science_changed": False, "candidates": rows}))
        return publisher.sha256(path)

    def make_candidate(self, root):
        bundle = root / "XX"
        bundle.mkdir()
        (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 original approved manuscript")
        (bundle / "data.json").write_bytes(b'{"original":true}')
        names = ("data.json", "paper.pdf")
        approved = gate.require_local(bundle, [bundle / name for name in names])
        return {"abbreviation": "XX", "bundle": bundle, "upload_names": names,
                "predecessor_doi": "10.5281/zenodo.100", "new_version": "v2",
                "metadata": {"metadata": {"title": "Approved science"}},
                "approved_preflight_json": json.dumps(approved, sort_keys=True, separators=(",", ":"))}

    @contextlib.contextmanager
    def server(self, root, candidate, *, mutate_during_http=False, mutate_after_doi=False,
               replace_public=False, bad_put=False, bad_draft=None):
        bundle = candidate["bundle"]
        captured = {}; calls = []; approvals = []; published = False
        real_public = gate.require_public

        def api(token, method, url, data=None, content_type="application/json", **kwargs):
            nonlocal published
            self.assertEqual(token, TOKEN)
            calls.append((method, url, data))
            if method == "GET" and url.endswith("/records/100"):
                if mutate_during_http:
                    (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 replaced during network activity")
                return {"id": 100, "metadata": {}}
            if method == "GET" and url.endswith("/records/200"):
                if not published:
                    return None
                public_bytes = dict(captured)
                if replace_public:
                    public_bytes["paper.pdf"] = (bundle / "paper.pdf").read_bytes()
                return {"id": 200, "metadata": {"doi": DOI}, "files": [
                    {"key": name, "size": len(raw), "checksum": "md5:" + hashlib.md5(raw).hexdigest()}
                    for name, raw in public_bytes.items()]}
            if method == "GET" and url.endswith("/deposit/depositions/200"):
                files = [{"filename": name, "checksum": "md5:" + hashlib.md5(raw).hexdigest(),
                          "filesize": len(raw)} for name, raw in captured.items()]
                if files and bad_draft:
                    if bad_draft == "checksum": files[0]["checksum"] = "0" * 32
                    elif bad_draft == "size": files[0]["filesize"] += 1
                    elif bad_draft == "duplicate": files.append(dict(files[0]))
                    elif bad_draft == "extra": files.append({"filename": "extra.txt"})
                return {"id": 200, "files": files, "links": {"bucket": "https://zenodo.org/api/files/bucket"}}
            if method == "PUT" and "/api/files/" in url:
                name = urllib.parse.unquote(url.rsplit("/", 1)[1])
                captured[name] = data
                return {"checksum": "md5:" + ("0" * 32 if bad_put else hashlib.md5(data).hexdigest())}
            if method == "PUT" and url.endswith("/deposit/depositions/200"):
                return {}
            if method == "POST" and url.endswith("/actions/publish"):
                published = True
                if mutate_after_doi:
                    (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 replacement after DOI mint")
                return {"id": 200, "metadata": {"doi": DOI}}
            self.fail("unexpected mocked request: " + method + " " + url)

        def public(record, approval):
            approvals.append(json.loads(json.dumps(approval)))
            def download(record_id, name):
                if replace_public and name == "paper.pdf":
                    return (bundle / name).read_bytes()
                return captured[name]
            return real_public(record, approval, download=download)

        with (mock.patch.object(publisher, "ROOT", root),
              mock.patch.object(publisher, "api_call", side_effect=api),
              mock.patch.object(publisher, "ensure_draft", return_value="200"),
              mock.patch.object(gate, "require_public", side_effect=public)):
            yield captured, calls, approvals

    def test_exact_snapshot_publishes_and_public_readback_uses_original_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            original = json.loads(candidate["approved_preflight_json"])
            with self.server(root, candidate) as (captured, calls, approvals):
                result = publisher.publish_candidate(candidate, TOKEN)
            self.assertEqual(result["doi"], DOI)
            self.assertEqual(approvals, [original])
            self.assertEqual(set(captured), set(candidate["upload_names"]))
            receipt = json.loads((candidate["bundle"] / "APPROVED_UPLOAD_PREFLIGHT.json").read_text())
            self.assertEqual(receipt, original)

    def test_wave_planning_retains_each_exact_sealed_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = self.make_wave(root)
            candidates = publisher.load_and_validate_wave(root, expected)
            self.assertEqual(len(candidates), 7)
            for candidate in candidates:
                approved = json.loads(candidate["approved_preflight_json"])
                self.assertEqual(approved, gate.require_local(candidate["bundle"],
                    [candidate["bundle"] / name for name in candidate["upload_names"]]))

    def test_wave_gate_race_cannot_approve_bytes_different_from_sealed_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = self.make_wave(root)
            real_local = gate.require_local
            def changed_before_gate(bundle, paths):
                (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 changed after sealed hash verification")
                return real_local(bundle, paths)
            with mock.patch.object(gate, "require_local", side_effect=changed_before_gate):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "sealed successor-wave manifest"):
                    publisher.load_and_validate_wave(root, expected)

    def test_pre_network_change_holds_before_any_http(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            (candidate["bundle"] / "paper.pdf").write_bytes(b"%PDF-changed before publish")
            with self.server(root, candidate) as (_, calls, _):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "changed before network"):
                    publisher.publish_candidate(candidate, TOKEN)
            self.assertFalse(calls)

    def test_mutation_during_first_http_cannot_change_uploaded_snapshot_or_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            original = (candidate["bundle"] / "paper.pdf").read_bytes()
            with self.server(root, candidate, mutate_during_http=True) as (captured, calls, _):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "changed before publication"):
                    publisher.publish_candidate(candidate, TOKEN)
            self.assertEqual(captured["paper.pdf"], original)
            self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_bad_put_checksum_holds_before_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            with self.server(root, candidate, bad_put=True) as (_, calls, _):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "PUT response checksum"):
                    publisher.publish_candidate(candidate, TOKEN)
            self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_draft_checksum_size_duplicates_and_extras_hold_before_publish(self):
        for fault in ("checksum", "size", "duplicate", "extra"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); candidate = self.make_candidate(root)
                with self.server(root, candidate, bad_draft=fault) as (_, calls, _):
                    with self.assertRaises(publisher.SuccessorPublisherError):
                        publisher.publish_candidate(candidate, TOKEN)
                self.assertFalse(any(method == "POST" for method, _, _ in calls))

    def test_local_mutation_after_doi_cannot_replace_public_readback_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            original = json.loads(candidate["approved_preflight_json"])
            with self.server(root, candidate, mutate_after_doi=True) as (_, _, approvals):
                result = publisher.publish_candidate(candidate, TOKEN)
            self.assertEqual(result["doi"], DOI)
            self.assertEqual(approvals, [original])

    def test_mutated_local_and_public_bytes_hold_but_keep_minted_doi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            original = json.loads(candidate["approved_preflight_json"])
            with self.server(root, candidate, mutate_after_doi=True, replace_public=True) as (_, calls, approvals):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "published DOI retained"):
                    publisher.publish_candidate(candidate, TOKEN)
            self.assertEqual(approvals, [original])
            self.assertEqual((candidate["bundle"] / "PUBLISHED_DOI.txt").read_text().strip(), DOI)
            self.assertEqual(sum(method == "POST" for method, _, _ in calls), 1)

    def test_resume_cannot_adopt_new_approval_after_minted_doi(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); candidate = self.make_candidate(root)
            with self.server(root, candidate):
                publisher.publish_candidate(candidate, TOKEN)
            (candidate["bundle"] / "paper.pdf").write_bytes(b"%PDF-replacement on retry")
            changed = gate.require_local(candidate["bundle"], [candidate["bundle"] / name for name in candidate["upload_names"]])
            candidate["approved_preflight_json"] = json.dumps(changed)
            with self.server(root, candidate) as (_, calls, _):
                with self.assertRaisesRegex(publisher.SuccessorPublisherError, "conflicting receipt"):
                    publisher.publish_candidate(candidate, TOKEN)
            self.assertFalse(calls)
            self.assertEqual((candidate["bundle"] / "PUBLISHED_DOI.txt").read_text().strip(), DOI)

    def test_missing_or_duplicate_approved_inventory_holds_before_http(self):
        for fault in ("missing", "duplicate"):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); candidate = self.make_candidate(root)
                if fault == "missing": candidate.pop("approved_preflight_json")
                else:
                    approved = json.loads(candidate["approved_preflight_json"])
                    approved["upload_files"].append(dict(approved["upload_files"][0]))
                    candidate["approved_preflight_json"] = json.dumps(approved)
                with self.server(root, candidate) as (_, calls, _):
                    with self.assertRaises(publisher.SuccessorPublisherError):
                        publisher.publish_candidate(candidate, TOKEN)
                self.assertFalse(calls)


if __name__ == "__main__":
    unittest.main()
