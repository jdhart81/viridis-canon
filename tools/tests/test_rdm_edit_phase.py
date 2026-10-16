"""Offline public/POST edit capture plus separately labeled post-PUT simulations.

No HTTP client, credential file, production import, or live PUT is used here.
The public and POST draft bodies are exact captured native JSON subobjects.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
from unittest import mock
import unittest

import test_zenodo_metadata_repair as helpers
M, Client = helpers.M, helpers.Client

FIXTURE = Path(__file__).parent / "fixtures/rdm-edit-21855705-20261016.json"
FIXTURE_SHA256 = "fbb3dacdfc2ebe9dd9e35948eb0e8a28c9b51b6b82bc564c5f02908bcf945d4d"


def captured():
    return json.loads(FIXTURE.read_bytes())


class CapturedClient(Client):
    """Only POST bodies are observed; GET-after-PUT variations are simulations."""
    def __init__(self, *, opening_change=None, checked_change=None):
        pair = captured()
        super().__init__(pair["before"])
        self.observed_draft = pair["draft_before"]
        self.opening_change, self.checked_change = opening_change, checked_change

    def __call__(self, method, url, data=None, *, rdm=False):
        if method == "POST" and url.endswith("/draft"):
            self.calls.append((method, url))
            self.draft = copy.deepcopy(self.observed_draft)
            if self.opening_change:
                self.opening_change(self.draft)
            return copy.deepcopy(self.draft)
        result = super().__call__(method, url, data, rdm=rdm)
        if method == "GET" and url.endswith("/draft") and self.puts and self.checked_change:
            self.checked_change(result)
        return result


def materialize_file_links(draft):
    for name, row in draft["files"]["entries"].items():
        base = M.RDM + draft["id"] + "/draft/files/" + name
        row["links"] = {"self": base, "content": base + "/content",
                        "container": base + "/container", "commit": base + "/commit"}


class NativeEditPhaseTests(unittest.TestCase):
    def apply_rehearsal(self, client):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, VIRIDIS_ENGINE_ROOT=temporary):
            root = Path(temporary) / "rehearsals/offline"; root.mkdir(parents=True)
            harness = helpers.RepairTests()
            try:
                return harness.run_apply(root, harness.plan(client.current), client, rehearse=True)
            except M.RepairHold:
                client.saved_receipt = json.loads((root / "receipt.json").read_bytes())
                raise

    def test_observed_native_post_projection_matches_public_without_changing_either_body(self):
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), FIXTURE_SHA256)
        pair = captured(); original = copy.deepcopy(pair)
        self.assertEqual(M.draft_against_public(pair["before"], pair["draft_before"]), [])
        self.assertEqual(pair, original)
        self.assertIn("/created", [row["path"] for row in M.protected_diff(pair["before"], pair["draft_before"])])
        # Public-to-public protection never accepts these edit-phase differences.
        self.assertTrue(M.protected_diff(pair["before"], pair["draft_before"]))

    def test_same_public_baseline_normalizes_semantic_post_put_file_link_materialization(self):
        client = CapturedClient(checked_change=materialize_file_links)
        try:
            receipt = self.apply_rehearsal(client)
        except M.RepairHold:
            receipt = {"state": "HOLD"}
        self.assertEqual(receipt["state"], "REHEARSED_DRAFT_DELETED")
        expected = copy.deepcopy(client.observed_draft)
        expected["metadata"]["copyright"] = M.COPYRIGHTS["21855705"]
        self.assertEqual(client.puts, [expected])  # Full original draft body, never a projection PUT.
        self.assertEqual([row["path"] for row in receipt["draft_diff"]], ["/metadata/copyright"])
        self.assertEqual([row["path"] for row in receipt["draft_public_diff"]], ["/metadata/copyright"])
        self.assertTrue(client.deleted)
        self.assertFalse(any(url.endswith("/actions/publish") for method, url in client.calls))
        self.assertEqual(client.current, captured()["before"])

    def test_wrong_record_parent_pid_and_edit_flags_are_cold_holds(self):
        pair = captured()
        changes = [lambda d: d.update(id="21855706"),
                   lambda d: d["parent"].update(id="21855703"),
                   lambda d: d["pids"]["doi"].update(identifier="10.5281/zenodo.21855706"),
                   lambda d: d.update(is_draft=False), lambda d: d.update(is_draft=1),
                   lambda d: d.update(is_published=False), lambda d: d.update(is_published=1),
                   lambda d: d.update(status="draft"),
                   lambda d: d["links"].update(self=M.RDM + "21855706/draft"),
                   lambda d: d["links"].update(self_html="https://zenodo.org/uploads/21855706")]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                draft = copy.deepcopy(pair["draft_before"]); change(draft)
                with self.assertRaises(M.RepairHold):
                    M.draft_against_public(pair["before"], draft)

    def test_invalid_naive_or_out_of_order_phase_timestamps_are_cold_holds(self):
        pair = captured()
        changes = [("created", "2026-10-16T12:16:01"), ("created", "2026-02-30T00:00:00+00:00"),
                   ("created", "2026-10-12T00:00:00+00:00"), ("created", "2026-10-17T00:00:00+00:00"),
                   ("updated", "2026-10-16T12:16:01.000000+00:00"),
                   ("expires_at", "yesterday"), ("expires_at", "2026-10-16T12:16:01"),
                   ("expires_at", "2026-08-07T00:00:00+00:00")]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                draft = copy.deepcopy(pair["draft_before"]); draft[key] = value
                with self.assertRaises(M.RepairHold):
                    M.draft_against_public(pair["before"], draft)

    def test_content_custom_fields_access_and_unknown_links_stay_protected(self):
        pair = captured(); filename = next(iter(pair["before"]["files"]["entries"]))
        changes = [lambda d: d["metadata"].update(title="Unapproved title"),
                   lambda d: d["metadata"].update(creators=[]), lambda d: d["metadata"].update(rights=[]),
                   lambda d: d["metadata"].update(description="Unapproved claim"),
                   lambda d: d["custom_fields"].update(unapproved="protected"),
                   lambda d: d["access"].update(record="restricted"),
                   lambda d: d["files"]["entries"][filename].update(checksum="md5:" + "0" * 32),
                   lambda d: d["files"]["entries"][filename].update(size=0),
                   lambda d: d["files"]["entries"][filename]["access"].update(hidden=True),
                   lambda d: d.update(deletion_status={"is_deleted": True, "status": "D"}),
                   lambda d: d.update(unrecognized={"cannot": "drop"}),
                   lambda d: d["links"].update(unrecognized="https://example.invalid/other"),
                   lambda d: d["links"].update(review=M.RDM + "21855706/draft/review"),
                   lambda d: d["links"].update(files=M.RDM + "21855706/draft/files"),
                   lambda d: d["links"].update(parent=M.RDM + "21855703")]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                draft = copy.deepcopy(pair["draft_before"]); change(draft)
                self.assertTrue(M.draft_against_public(pair["before"], draft))

    def test_omitted_file_links_require_closed_identity_bound_public_links(self):
        pair = captured(); filename = next(iter(pair["before"]["files"]["entries"]))
        for key, value in (("content", "https://example.invalid/other"), ("unrecognized", "protected")):
            with self.subTest(key=key):
                before = copy.deepcopy(pair["before"])
                before["files"]["entries"][filename]["links"][key] = value
                self.assertTrue(M.draft_against_public(before, pair["draft_before"]))
        draft = copy.deepcopy(pair["draft_before"])
        draft["files"]["entries"][filename]["links"] = {}  # Missing object and empty object differ.
        self.assertTrue(M.draft_against_public(pair["before"], draft))
        materialize_file_links(draft)
        draft["files"]["entries"][filename]["links"]["content"] = "https://example.invalid/other"
        self.assertTrue(M.draft_against_public(pair["before"], draft))

    def test_actual_opening_unknown_drift_deletes_before_put(self):
        client = CapturedClient(opening_change=lambda d: d["custom_fields"].update(unapproved="drift"))
        with self.assertRaises(M.RepairHold):
            self.apply_rehearsal(client)
        self.assertTrue(client.deleted)
        self.assertEqual(client.puts, [])
        self.assertFalse(any(url.endswith("/actions/publish") for method, url in client.calls))

    def test_semantic_after_put_protected_drift_or_invalid_phase_blocks_publish(self):
        filename = next(iter(captured()["before"]["files"]["entries"]))
        changes = [lambda d: d["custom_fields"].update(unapproved="drift"),
                   lambda d: d["metadata"].update(title="Drift"),
                   lambda d: d["access"].update(record="restricted"),
                   lambda d: d["files"]["entries"][filename].update(checksum="md5:" + "0" * 32),
                   lambda d: d["links"].update(review="https://example.invalid/review"),
                   lambda d: d.update(expires_at="invalid"), lambda d: d.pop("is_draft"),
                   lambda d: d.update(created="2026-10-16T12:16:01.900000+00:00")]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                client = CapturedClient(checked_change=change)
                with self.assertRaises(M.RepairHold):
                    self.apply_rehearsal(client)
                self.assertTrue(client.deleted)
                self.assertIn("draft_after", client.saved_receipt)
                expected = copy.deepcopy(client.puts[0]); change(expected)
                self.assertEqual(client.saved_receipt["draft_after"], expected)
                self.assertEqual(len(client.puts), 1)
                self.assertFalse(any(url.endswith("/actions/publish") for method, url in client.calls))


if __name__ == "__main__":
    unittest.main()
