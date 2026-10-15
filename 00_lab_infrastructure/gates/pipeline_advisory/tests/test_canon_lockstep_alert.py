import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("canon_lockstep_alert", Path(__file__).resolve().parents[1] / "canon_lockstep_alert.py")
alert = importlib.util.module_from_spec(spec); spec.loader.exec_module(alert)


class CanonLockstepTests(unittest.TestCase):
    def setUp(self):
        change = {"record_id": "23174891", "doi": "10.5281/zenodo.23174891", "source_receipt_sha256": "a" * 64}
        release = {**change, "tag": "canon-v10.2.0-hub-20261013", "annotated_tag": True,
                   "release_url": "https://github.com/jdhart81/viridis-canon/releases/tag/canon-v10.2.0-hub-20261013",
                   "commit_sha": "b" * 40, "tag_object_sha": "c" * 40}
        self.snapshot = {"canon_changes": [change], "git_releases": [release]}

    def test_exact_annotated_tag_release_and_change_receipt_match(self):
        row = alert.inspect_lockstep(self.snapshot)
        self.assertEqual(row["status"], "MATCHED_SUPPLIED_SCOPE")
        self.assertFalse(row["certifies"]); self.assertEqual(row["external_mutations"], 0)

    def test_missing_release_alerts(self):
        self.snapshot["git_releases"] = []
        self.assertEqual(alert.inspect_lockstep(self.snapshot)["status"], "ALERT_CANON_LOCKSTEP_GAP")

    def test_later_change_requires_a_new_exact_receipt_binding(self):
        self.snapshot["canon_changes"][0]["source_receipt_sha256"] = "d" * 64
        row = alert.inspect_lockstep(self.snapshot)["checks"][0]
        self.assertEqual(row["status"], "ALERT_MISSING_MATCHING_TAG_AND_RELEASE")

    def test_lightweight_tag_foreign_release_missing_commit_cannot_pass(self):
        for key, value in (("annotated_tag", False), ("release_url", "https://example.invalid/release"),
                           ("commit_sha", None), ("tag_object_sha", "")):
            snapshot = copy.deepcopy(self.snapshot); snapshot["git_releases"][0][key] = value
            with self.subTest(key=key):
                self.assertEqual(alert.inspect_lockstep(snapshot)["status"], "ALERT_CANON_LOCKSTEP_GAP")

    def test_ambiguous_release_mapping_holds(self):
        self.snapshot["git_releases"] *= 2
        self.assertEqual(alert.inspect_lockstep(self.snapshot)["checks"][0]["status"], "HOLD_AMBIGUOUS_RELEASE_MAPPING")

    def test_missing_snapshots_are_unavailable_not_clean(self):
        self.assertEqual(alert.inspect_lockstep({})["status"], "UNAVAILABLE")
        self.assertEqual(alert.inspect_lockstep({"canon_changes": [], "git_releases": []})["status"], "NO_CHANGES_IN_SUPPLIED_SCOPE")

    def test_false_doi_and_unbound_change_are_rejected(self):
        for key, value in (("doi", "10.5072/zenodo.23174891"), ("source_receipt_sha256", "")):
            snapshot = copy.deepcopy(self.snapshot); snapshot["canon_changes"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): alert.inspect_lockstep(snapshot)


if __name__ == "__main__":
    unittest.main()
