import copy
import hashlib
import importlib.util
import json
import os
from unittest import mock
from pathlib import Path
import tempfile
import unittest
import urllib.error

SPEC = importlib.util.spec_from_file_location("repair", Path(__file__).resolve().parents[1] / "zenodo_metadata_repair.py")
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
DUMMY = "DUMMY_REPAIR_CREDENTIAL_" + "x" * 40


def baseline(record="21855705"):
    return {"id": record, "revision_id": 1, "updated": "before", "status": "published",
            "metadata": {"title": "Protected title", "creators": [{"person_or_org": {"name": "Example"}}],
                         "rights": [{"id": "cc-by-4.0"}], "description": "<p>Unchanged scientific claims</p>"},
            "files": {"entries": {"paper.pdf": {"key": "paper.pdf", "checksum": "md5:unchanged", "size": 12}}}}


class Client:
    def __init__(self, before, unplanned=False, uncertain=False, opening_drift=False):
        self.current = copy.deepcopy(before)
        self.draft = None
        self.calls = []; self.puts = []; self.deleted = False
        self.unplanned, self.uncertain = unplanned, uncertain
        self.opening_drift = opening_drift

    def __call__(self, method, url, data=None, *, rdm=False):
        assert rdm
        self.calls.append((method, url))
        if url.endswith("/draft/actions/publish"):
            if self.uncertain:
                raise RuntimeError(DUMMY)
            self.current["metadata"] = copy.deepcopy(self.draft["metadata"])
            self.current.update(revision_id=2, updated="after", ui={"updated_date_l10n_long": "after"}, stats={"downloads": 4})
            return copy.deepcopy(self.current)
        if url.endswith("/draft"):
            if method == "DELETE":
                self.deleted = True; self.draft = None; return {}
            if method == "GET" and self.deleted:
                raise urllib.error.HTTPError(url, 404, "deleted", {}, None)
            if method == "POST":
                self.draft = {**copy.deepcopy(self.current), "status": "draft"}
                if self.opening_drift:
                    self.draft["custom_fields"] = {"unexpected": "opening draft drift"}
            if method == "PUT":
                self.puts.append(json.loads(data))
                self.draft = json.loads(data)
                if self.unplanned:
                    self.draft["metadata"]["title"] = "Unexpected title"
            return copy.deepcopy(self.draft)
        return copy.deepcopy(self.current)


class RepairTests(unittest.TestCase):
    def plan(self, before=None):
        return M.make_plan(before or baseline(), "21855705", "copyright", M.COPYRIGHTS["21855705"],
                           verified_source={"sha256": "a" * 64, "source": "DataCite activity v1"})

    def run_apply(self, root, plan, client, *, reviewed=True, datacite=True, rehearse=False):
        transport = root / "transport.py"
        transport.write_text("# dummy reviewed mock transport")
        digest = hashlib.sha256(transport.read_bytes()).hexdigest()
        receipt = root / "installation.json"
        receipt.write_text(json.dumps({"independent_review_merged": reviewed, "ci_green": True,
                                      "merged_blob_sha256": digest, "installed_sha256": digest, "merged_commit": "a" * 40}))
        return M.apply_plan(client, plan, root / "receipt.json", installation_receipt=receipt,
                            installed_transport=transport, expected_installation_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
                            expected_plan_sha256=M.canonical_hash(plan), sanitize=lambda text: text.replace(DUMMY, "***"),
                            verify_datacite=lambda *a: datacite, rehearse=rehearse)

    def ledger(self, root, *, valid=False, missing=False):
        path = root / "RESEARCH_PIPELINE_v2/corpus_ledger.json"; path.parent.mkdir(exist_ok=True)
        rows = [{"id": entity, "certificate": None, "certificate_valid": valid} for entity in M.UNMT_ENTITY_IDS]
        path.write_text(json.dumps({"file_entities": [] if missing else rows}), encoding="utf-8")
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_unmt_holds_if_ledger_missing_entities_valid_certificate_or_hash_drift(self):
        for condition in ("valid", "missing", "drift"):
            with self.subTest(condition=condition), tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, VIRIDIS_CORE_ROOT=temporary):
                digest = self.ledger(Path(temporary), valid=condition == "valid", missing=condition == "missing")
                with self.assertRaises(M.RepairHold):
                    M.unmt_ledger("a" * 64 if condition == "drift" else digest)

    def test_unmt_rechecks_bound_ledger_before_any_network_call(self):
        banner = "<p><strong>UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. Lean sources may compile but have not been independently certified. Results are conditional on the stated model assumptions.</strong></p>"
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, VIRIDIS_CORE_ROOT=temporary):
            root = Path(temporary); digest = self.ledger(root); before = baseline("23329823")
            plan = M.make_plan(before, "23329823", "description", banner + before["metadata"]["description"],
                               verified_source={"sha256": "a" * 64, "banner": banner}, expected_ledger_sha256=digest)
            self.ledger(root, valid=True); client = Client(before)
            with self.assertRaises(M.RepairHold): self.run_apply(root, plan, client)
            self.assertEqual(client.calls, [])

    def test_real_record_projection_and_already_applied_replay(self):
        before = json.loads((Path(__file__).parent / "fixtures/rdm-21855705.json").read_text(encoding="utf-8"))
        before = before.get("response", before)
        plan = self.plan(before); client = Client(before)
        with tempfile.TemporaryDirectory() as temporary:
            receipt = self.run_apply(Path(temporary), plan, client)
        self.assertEqual(receipt["state"], "PUBLIC_REPAIR_READBACK_VERIFIED")
        self.assertEqual(client.puts[0]["custom_fields"], before["custom_fields"])
        self.assertEqual(set(client.puts[0]), set(receipt["draft_before"]))
        with tempfile.TemporaryDirectory() as temporary:
            replay = self.run_apply(Path(temporary), plan, client)
        self.assertEqual(replay["state"], "ALREADY_APPLIED_NO_MUTATION")
        self.assertEqual([row["path"] for row in receipt["public_diff"]], ["/metadata/copyright"])

    def test_rehearsal_discards_edit_and_preserves_published_record(self):
        plan = self.plan(); client = Client(plan["before"])
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, VIRIDIS_ENGINE_ROOT=temporary):
            root = Path(temporary) / "rehearsals/now"; root.mkdir(parents=True)
            receipt = self.run_apply(root, plan, client, rehearse=True)
        self.assertEqual(receipt["state"], "REHEARSED_DRAFT_DELETED")
        self.assertTrue(client.deleted)
        self.assertEqual(client.current, plan["before"])
        self.assertFalse(any(url.endswith("/actions/publish") for method, url in client.calls))

    def test_plan_changes_only_exact_copyright(self):
        plan = self.plan()
        self.assertEqual([row["path"] for row in plan["planned_diff"]], ["/metadata/copyright"])
        self.assertEqual(plan["before"]["files"], plan["planned_after"]["files"])
        self.assertEqual(plan["before"]["metadata"]["rights"], plan["planned_after"]["metadata"]["rights"])
        self.assertEqual(plan["before"]["metadata"]["creators"], plan["planned_after"]["metadata"]["creators"])

    def test_no_unapproved_record_or_field(self):
        for field, value in (("copyright", "Different owner"), ("title", "Other")):
            with self.assertRaises(M.RepairHold):
                M.make_plan(baseline(), "21855705", field, value, verified_source={"sha256": "a" * 64})

    def test_banner_bytes_and_certificate_gate(self):
        source = {"metadata": {"description": "<p><strong>UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. Lean sources may compile but have not been independently certified. Results are conditional on the stated model assumptions.</strong></p><p>rest</p>"}}
        banner = M.first_banner(source)
        before = baseline("23329823")
        value = banner + before["metadata"]["description"]
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ, VIRIDIS_CORE_ROOT=temporary):
            ledger = self.ledger(Path(temporary))
            plan = M.make_plan(before, "23329823", "description", value,
                               verified_source={"sha256": "b" * 64, "banner": banner},
                               expected_ledger_sha256=ledger, certificate_valid=False)
        self.assertEqual(plan["planned_after"]["metadata"]["description"], value)
        with self.assertRaises(M.RepairHold):
            M.make_plan(before, "23329823", "description", value,
                        verified_source={"sha256": "b" * 64, "banner": banner}, certificate_valid=True)

    def test_missing_review_prevents_even_network_read(self):
        plan = self.plan()
        client = Client(plan["before"])
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(M.RepairHold):
            self.run_apply(Path(temporary), plan, client, reviewed=False)
        self.assertFalse(client.calls)

    def test_mocked_repair_preserves_full_record_and_datacite_readback(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as temporary:
            receipt = self.run_apply(Path(temporary), plan, Client(plan["before"]))
        self.assertEqual(receipt["state"], "PUBLIC_REPAIR_READBACK_VERIFIED")
        self.assertEqual({row["path"] for row in receipt["public_diff"]}, {"/metadata/copyright"})

    def test_opening_draft_protected_drift_is_deleted_before_any_put_or_publish(self):
        plan = self.plan(); client = Client(plan["before"], opening_drift=True)
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(M.RepairHold):
            self.run_apply(Path(temporary), plan, client)
        self.assertTrue(client.deleted)
        self.assertFalse(any(method == "PUT" or url.endswith("/actions/publish") for method, url in client.calls))

    def test_unplanned_draft_diff_blocks_publish(self):
        plan = self.plan()
        client = Client(plan["before"], unplanned=True)
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(M.RepairHold):
            self.run_apply(Path(temporary), plan, client)
        self.assertFalse(any(url.endswith("/actions/publish") for method, url in client.calls))
        self.assertTrue(client.deleted)

    def test_uncertain_publish_is_retained_without_retry_or_token_output(self):
        plan = self.plan()
        client = Client(plan["before"], uncertain=True)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(M.RepairHold) as caught:
                self.run_apply(Path(temporary), plan, client)
            self.assertNotIn(DUMMY, str(caught.exception))
            self.assertNotIn(DUMMY, (Path(temporary) / "receipt.json").read_text())
        self.assertEqual(sum(url.endswith("/actions/publish") for method, url in client.calls), 1)

    def test_datacite_absence_does_not_claim_complete(self):
        plan = self.plan()
        with tempfile.TemporaryDirectory() as temporary, self.assertRaises(M.RepairHold):
            self.run_apply(Path(temporary), plan, Client(plan["before"]), datacite=False)

    def test_idempotent_replay_still_requires_datacite_confirmation(self):
        plan = self.plan()
        for confirmed in (False, True):
            with self.subTest(confirmed=confirmed), tempfile.TemporaryDirectory() as temporary:
                client = Client(plan["planned_after"])
                if confirmed:
                    receipt = self.run_apply(Path(temporary), plan, client, datacite=True)
                    self.assertEqual(receipt["state"], "ALREADY_APPLIED_NO_MUTATION")
                else:
                    with self.assertRaises(M.RepairHold):
                        self.run_apply(Path(temporary), plan, client, datacite=False)
                    receipt = json.loads((Path(temporary) / "receipt.json").read_text())
                    self.assertEqual(receipt["state"], "HOLD_ALREADY_APPLIED_DATACITE_READBACK_REQUIRED")
                self.assertEqual([method for method, url in client.calls], ["GET"])

    def test_hash_bound_plan_cannot_expand_A4_record_field_or_value(self):
        for alteration in ("record", "field", "value", "extra_diff"):
            plan = self.plan()
            if alteration == "record":
                plan["record_id"] = "99999"
                plan["before"]["id"] = "99999"
                plan["planned_after"]["id"] = "99999"
            elif alteration == "field":
                plan["field"] = "title"
            elif alteration == "value":
                plan["planned_after"]["metadata"]["copyright"] = "Unapproved copyright owner"
            else:
                plan["planned_after"]["metadata"]["title"] = "Changed scientific title"
            client = Client(plan["before"])
            with self.subTest(alteration=alteration), tempfile.TemporaryDirectory() as temporary, self.assertRaises(M.RepairHold):
                self.run_apply(Path(temporary), plan, client)
            self.assertFalse(client.calls)


if __name__ == "__main__":
    unittest.main()
