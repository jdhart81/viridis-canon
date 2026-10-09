"""Portable, synthetic-fixture tests for the approved own-record policy.

No network, credentials, production records, Lean verification, or science PASS
is involved. Ownership objects are genuine-response-shaped fixtures, not public
publication evidence. This file is the reviewer's only authored parent file.
"""
from copy import deepcopy
import hashlib
import json
import unittest

import own_record_comparison as policy


RID = "102"
PARENT = "100"
PRIOR = "101"
CREATED = "2026-10-08T02:15:00Z"
DATE = "2026-10-08"
COMMUNITY_ID = "01234567-1234-1234-1234-012345678901"
DESCRIPTION = "Logical validity given the model, not empirical validation."
AUTHORITY_FIXTURE = "## Own-record comparison principle (ends Zenodo field stops) — 2026-10-08 (evening)\n\nTrigger: new-version draft 23246368's `publication_date` went from 2026-10-07 to 2026-10-08. Zenodo resets the date on a new draft. **APPROVED:** the draft's date comes from its own authenticated creation timestamp. Recover 23246368 in place; do not create another version.\n\nRoot cause of the repeated stops: the readback compares Zenodo's own housekeeping on the **new** record against expectations it can't know in advance. Permanent rule from now on:\n\n1. **Own new record or draft (the thing we are publishing).** Compare only what **we send or control**, and require it to equal our payload exactly:\n   - metadata we PUT, including an explicit `publication_date` that we set ourselves on every PUT, equal to the publish date (America/New_York);\n   - files: names, sizes, checksums;\n   - DOI and concept identity;\n   - related identifiers, communities, banner/description text.\n   Everything else Zenodo sets on the own record (dates, revisions, flags, ui, links, stats, previews, PIDs it mints) is logged, not gated. Sole exception: a server value that **contradicts** something we sent is a hard stop.\n2. **Every pre-existing record** (prior versions, untouched records): byte-exact as before, except the already-approved version-chain flags.\n3. With rule 1, a server-managed field on the own record is **never** a new mismatch class. Escalate only content, file, PID-identity or prior-record changes.\n\nResume: recover 23246368 (explicit publication_date in the PUT), then publish the 49 staged backlog notes through the weekly digest, ≤10 writes/day.\n".encode("utf-8")


def transport_receipt(method, url, response, *, code=200, native=False,
                      request=b"{}"):
    raw = json.dumps(response, sort_keys=True, separators=(",", ":")).encode()
    result = {
        "method": method, "url": url, "environment": "zenodo.org",
        "status": "HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE",
        "http_status": code, "response_sha256": hashlib.sha256(raw).hexdigest(),
        "response": deepcopy(response),
        "request_body_sha256": None if method == "GET" else hashlib.sha256(request).hexdigest(),
    }
    if native:
        result["accept"] = policy.NATIVE
    return result


def fixture(*, phase="DRAFT", doi_required=False):
    """Closed independent controls plus separate owned-creation source objects."""
    files = [
        {"name": "paper.pdf", "bytes": 17, "md5": "a" * 32},
        {"name": "evidence.json", "bytes": 9, "md5": "b" * 32},
    ]
    metadata = {
        "title": "Viridis Methods Digest — 2026-W41",
        "description": DESCRIPTION, "publication_date": DATE,
        "creators": [{"name": "Fixture Author"}],
        "related_identifiers": [{
            "identifier": "10.5281/zenodo.101", "scheme": "doi",
            "relation": "isSupplementTo",
        }],
        "keywords": ["methods", "conditional"],
        "version": "2",
    }
    legacy_metadata = dict(deepcopy(metadata), communities=[{"identifier": "viridis-canon"}])
    controlled = {
        "record_id": RID, "concept_id": PARENT, "phase": phase,
        "native_metadata": deepcopy(metadata),
        "legacy_metadata": deepcopy(legacy_metadata), "files": deepcopy(files),
        "communities": [{"identifier": "viridis-canon"}],
        "native_community_ids": [COMMUNITY_ID], "doi_required": doi_required,
    }
    native = {
        "id": RID, "created": CREATED, "updated": CREATED,
        "parent": {
            "id": PARENT,
            "pids": {"doi": {"identifier": "10.5281/zenodo." + PARENT}},
            "communities": {
                "ids": [COMMUNITY_ID], "default": COMMUNITY_ID,
                "entries": [{"id": COMMUNITY_ID, "slug": "viridis-canon"}],
            },
        },
        "metadata": deepcopy(metadata), "pids": {},
        "files": {
            "entries": {
                f["name"]: {"key": f["name"], "size": f["bytes"],
                            "checksum": "md5:" + f["md5"], "id": "uuid-" + f["name"]}
                for f in files
            },
            "count": len(files), "total_bytes": sum(f["bytes"] for f in files),
        },
        "custom_fields": {"legacy:communities": ["viridis-canon"]},
        "is_draft": True, "is_published": False, "status": "new_version_draft",
    }
    legacy = {
        "id": int(RID), "record_id": int(RID), "conceptrecid": PARENT,
        "conceptdoi": "10.5281/zenodo." + PARENT, "created": CREATED,
        "metadata": deepcopy(legacy_metadata), "title": metadata["title"],
        "files": [{"filename": f["name"], "filesize": f["bytes"],
                   "checksum": f["md5"], "id": "uuid-" + f["name"]}
                  for f in files],
        "state": "unsubmitted", "submitted": False,
    }
    if doi_required:
        native["pids"]["doi"] = {"identifier": "10.5281/zenodo." + RID}
        legacy["doi"] = "10.5281/zenodo." + RID
    if phase == "PUBLISHED":
        native.update(is_draft=False, is_published=True, status="published")
        legacy.update(state="done", submitted=True)
    creation = {
        "id": int(RID), "record_id": int(RID), "conceptrecid": PARENT,
        "created": CREATED, "modified": CREATED, "state": "unsubmitted",
        "submitted": False, "metadata": deepcopy(legacy_metadata),
        "files": deepcopy(legacy["files"]), "owner": 7,
        "links": {"latest_draft": policy.BASE + "/api/deposit/depositions/" + RID},
    }
    # Ownership always binds the first unpublished draft pair, even when the
    # separately tested current readback is post-reservation or published.
    first_native = deepcopy(native)
    first_native.update(is_draft=True, is_published=False, status="new_version_draft", pids={})
    first_legacy = deepcopy(legacy)
    first_legacy.update(state="unsubmitted", submitted=False)
    first_legacy.pop("doi", None)
    ownership = {
        "creation_receipt": transport_receipt(
            "POST", policy.BASE + "/api/deposit/depositions/" + PRIOR + "/actions/newversion",
            creation, code=201),
        "first_native_receipt": transport_receipt(
            "GET", policy.BASE + "/api/records/" + RID + "/draft", first_native, native=True),
        "first_legacy_receipt": transport_receipt(
            "GET", policy.BASE + "/api/deposit/depositions/" + RID, first_legacy),
        "prior_ids": [PRIOR],
    }
    return native, legacy, controlled, ownership


def prior_native():
    native, _, _, _ = fixture(phase="PUBLISHED", doi_required=True)
    native["id"] = PRIOR
    native["pids"]["doi"]["identifier"] = "10.5281/zenodo." + PRIOR
    native["versions"] = {"index": 2, "is_latest": True, "is_latest_draft": True}
    native["revision_id"] = 3
    native["links"] = {"self": policy.BASE + "/api/records/" + PRIOR}
    native["stats"] = {"views": 4}
    native["ui"] = {"is_draft": False}
    return native


def prior_legacy():
    _, legacy, _, _ = fixture(phase="PUBLISHED", doi_required=True)
    legacy["id"] = legacy["record_id"] = int(PRIOR)
    legacy["doi"] = "10.5281/zenodo." + PRIOR
    legacy["metadata"]["relations"] = {"version": [{
        "index": 1, "is_last": True,
        "parent": {"pid_type": "recid", "pid_value": PARENT},
    }]}
    legacy["modified"] = CREATED
    legacy["links"] = {"self": policy.BASE + "/api/records/" + PRIOR}
    legacy["stats"] = {"views": 4}
    return legacy


class OwnRecordTests(unittest.TestCase):
    def setUp(self):
        self.native, self.legacy, self.controlled, self.ownership = fixture()

    def audit(self):
        return policy.require_own_readback(
            self.native, self.legacy, controlled=self.controlled, ownership=self.ownership)

    def assert_hold(self):
        with self.assertRaises(policy.OwnRecordHold):
            self.audit()

    def test_owned_creation_and_complete_controlled_readback_pass_without_science_credit(self):
        self.assertEqual(policy.require_ownership(**self.ownership), {
            "record_id": RID, "concept_id": PARENT,
            "creation_publication_date": DATE, "start_kind": "NEW_VERSION",
        })
        result = self.audit()
        self.assertEqual(result["status"], "OWN_RECORD_CONTROLLED_READBACK_PASS")
        self.assertIs(result["certifies"], False)
        self.assertEqual(result["controlled_sha256"], hashlib.sha256(policy.raw_json(self.controlled)).hexdigest())

    def test_published_requires_own_native_and_legacy_doi(self):
        self.native, self.legacy, self.controlled, self.ownership = fixture(phase="PUBLISHED", doi_required=True)
        self.assertEqual(self.audit()["phase"], "PUBLISHED")
        self.native["pids"].pop("doi")
        self.assert_hold()

    def test_published_doi_requirement_cannot_be_disabled(self):
        self.controlled["phase"] = "PUBLISHED"
        self.assert_hold()

    def test_controlled_expectations_are_closed(self):
        self.controlled["ignore_metadata"] = True
        self.assert_hold()

    def test_native_title_change_holds(self):
        self.native["metadata"]["title"] = "rewritten title"
        self.assert_hold()

    def test_legacy_title_change_holds(self):
        self.legacy["metadata"]["title"] = "rewritten title"
        self.assert_hold()

    def test_legacy_top_title_contradiction_holds(self):
        self.legacy["title"] = "rewritten title"
        self.assert_hold()

    def test_native_top_title_contradiction_holds(self):
        self.native["title"] = "rewritten title"
        self.assert_hold()

    def test_metadata_types_are_not_coerced(self):
        for which, key, value in [("native", "title", True), ("legacy", "description", 1),
                                  ("native", "version", 2), ("legacy", "keywords", "methods")]:
            with self.subTest(which=which, key=key):
                self.setUp()
                getattr(self, which)["metadata"][key] = value
                self.assert_hold()

    def test_metadata_missing_sent_field_holds(self):
        self.native["metadata"].pop("creators")
        self.assert_hold()

    def test_publication_date_changed_on_either_readback_holds(self):
        for which in ("native", "legacy"):
            with self.subTest(which=which):
                self.setUp()
                getattr(self, which)["metadata"]["publication_date"] = "2026-10-09"
                self.assert_hold()

    def test_description_and_banner_exact(self):
        for which in ("native", "legacy"):
            with self.subTest(which=which):
                self.setUp()
                getattr(self, which)["metadata"]["description"] += " Machine checked unconditionally."
                self.assert_hold()

    def test_related_identifier_relation_or_doi_changed_holds(self):
        for which, key, value in [("native", "identifier", "10.5281/zenodo.999"),
                                  ("legacy", "relation", "isIdenticalTo")]:
            with self.subTest(which=which, key=key):
                self.setUp()
                getattr(self, which)["metadata"]["related_identifiers"][0][key] = value
                self.assert_hold()

    def test_unsent_related_identifiers_cannot_be_added(self):
        for expected in (self.controlled["native_metadata"], self.controlled["legacy_metadata"]):
            expected.pop("related_identifiers")
        self.native["metadata"]["related_identifiers"] = []
        self.legacy["metadata"]["related_identifiers"] = []
        self.audit()
        self.native["metadata"]["related_identifiers"] = [{"identifier": "10.5281/zenodo.999"}]
        self.assert_hold()

    def test_native_filename_set_exact(self):
        self.native["files"]["entries"]["extra.pdf"] = deepcopy(self.native["files"]["entries"]["paper.pdf"])
        self.assert_hold()

    def test_native_missing_filename_holds(self):
        self.native["files"]["entries"].pop("paper.pdf")
        self.assert_hold()

    def test_native_entry_key_contradiction_holds(self):
        self.native["files"]["entries"]["paper.pdf"]["key"] = "other.pdf"
        self.assert_hold()

    def test_native_size_or_md5_change_holds(self):
        for key, value in [("size", 18), ("size", True), ("checksum", "md5:" + "c" * 32)]:
            with self.subTest(key=key, value=value):
                self.setUp()
                self.native["files"]["entries"]["paper.pdf"][key] = value
                self.assert_hold()

    def test_native_filename_alias_contradiction_holds(self):
        self.native["files"]["entries"]["paper.pdf"]["filename"] = "other.pdf"
        self.assert_hold()

    def test_native_size_alias_contradiction_holds(self):
        self.native["files"]["entries"]["paper.pdf"]["filesize"] = 18
        self.assert_hold()

    def test_native_count_or_total_bytes_contradiction_holds(self):
        for key, value in [("count", 3), ("total_bytes", 27), ("count", True)]:
            with self.subTest(key=key):
                self.setUp()
                self.native["files"][key] = value
                self.assert_hold()

    def test_legacy_filename_set_exact(self):
        self.legacy["files"].pop()
        self.assert_hold()

    def test_legacy_duplicate_filename_holds(self):
        self.legacy["files"][1] = deepcopy(self.legacy["files"][0])
        self.assert_hold()

    def test_legacy_size_checksum_or_bool_size_holds(self):
        for key, value in [("filesize", 18), ("filesize", True), ("checksum", "c" * 32)]:
            with self.subTest(key=key, value=value):
                self.setUp()
                self.legacy["files"][0][key] = value
                self.assert_hold()

    def test_legacy_md5_prefix_and_key_size_aliases_pass_when_identical(self):
        row = self.legacy["files"][0]
        row.update(key=row["filename"], size=row["filesize"], checksum="md5:" + row["checksum"])
        self.audit()

    def test_legacy_name_alias_contradiction_holds(self):
        self.legacy["files"][0]["key"] = "other.pdf"
        self.assert_hold()

    def test_legacy_size_alias_contradiction_holds(self):
        for value in (18, True):
            with self.subTest(value=value):
                self.setUp()
                self.legacy["files"][0]["size"] = value
                self.assert_hold()

    def test_controlled_duplicate_filename_or_bool_size_holds(self):
        for mutation in (lambda c: c["files"].append(deepcopy(c["files"][0])),
                         lambda c: c["files"][0].__setitem__("bytes", True)):
            self.setUp()
            mutation(self.controlled)
            self.assert_hold()

    def test_native_record_or_concept_contradiction_holds(self):
        self.native["id"] = PRIOR
        self.assert_hold()
        self.setUp()
        self.native["parent"]["id"] = "999"
        self.assert_hold()

    def test_native_record_alias_contradiction_holds(self):
        self.native["record_id"] = "999"
        self.assert_hold()

    def test_legacy_record_alias_contradiction_holds(self):
        for key in ("id", "record_id", "recid"):
            with self.subTest(key=key):
                self.setUp()
                self.legacy[key] = 999
                self.assert_hold()

    def test_native_doi_or_concept_doi_contradiction_holds(self):
        self.native["pids"]["doi"] = {"identifier": "10.5281/zenodo.999"}
        self.assert_hold()
        self.setUp()
        self.native["parent"]["pids"]["doi"]["identifier"] = "10.5281/zenodo.999"
        self.assert_hold()

    def test_legacy_doi_or_concept_doi_contradiction_holds(self):
        for key in ("doi", "conceptdoi"):
            with self.subTest(key=key):
                self.setUp()
                self.legacy[key] = "10.5281/zenodo.999"
                self.assert_hold()

    def test_metadata_doi_and_prereservation_contradiction_holds(self):
        for which, key, value in [("native", "doi", "10.5281/zenodo.999"),
                                  ("legacy", "prereserve_doi", {"doi": "10.5281/zenodo." + RID, "recid": 999})]:
            with self.subTest(which=which, key=key):
                self.setUp()
                getattr(self, which)["metadata"][key] = value
                self.assert_hold()

    def test_legacy_community_membership_changed_holds(self):
        self.legacy["metadata"]["communities"] = [{"identifier": "other-community"}]
        self.assert_hold()

    def test_native_community_identity_or_slug_contradiction_holds(self):
        for mutation in (lambda g: g.__setitem__("ids", ["foreign-uuid"]),
                         lambda g: g["entries"][0].__setitem__("slug", "other-community"),
                         lambda g: g.__setitem__("default", "foreign-uuid")):
            self.setUp()
            mutation(self.native["parent"]["communities"])
            self.assert_hold()

    def test_community_mirror_cannot_contradict_membership(self):
        self.native["custom_fields"]["legacy:communities"] = ["other-community"]
        self.assert_hold()

    def test_empty_membership_cannot_hide_native_or_legacy_members(self):
        self.controlled["communities"] = []
        self.controlled["native_community_ids"] = []
        self.controlled["legacy_metadata"]["communities"] = []
        self.assert_hold()

    def test_noncontradictory_own_housekeeping_is_accepted_and_logged(self):
        self.native.update(
            updated="2030-01-01T00:00:00Z", revision_id=0,
            status="server-rendering-state", is_draft=False, is_published=True,
            links={"server_alias": "https://zenodo.org/server-managed-path"},
            stats={"views": 200}, ui={"rendered": "arbitrary rendering"},
            media_files={"entries": {"tiles": {"processor": "server"}}},
            server_managed_future={"value": "logged"},
        )
        self.native["pids"]["oai"] = {"identifier": "oai:zenodo.org:" + RID, "provider": "oai"}
        self.native["files"]["entries"]["paper.pdf"].update(
            id="new-server-uuid", links={"preview": "https://zenodo.org/server-preview"},
            metadata={"width": 50})
        self.legacy["server_managed_future"] = {"value": "legacy logged"}
        result = self.audit()
        self.assertEqual(result["housekeeping"]["native"]["server_managed_future"], {"value": "logged"})
        self.assertEqual(result["housekeeping"]["native"]["ui"], self.native["ui"])
        self.assertEqual(result["housekeeping"]["native"]["pids"]["oai"], self.native["pids"]["oai"])
        self.assertEqual(result["housekeeping"]["native"]["file_housekeeping"], self.native["files"])
        self.assertIs(result["certifies"], False)

    def test_ownership_is_revalidated_each_call(self):
        self.audit()
        self.ownership["first_native_receipt"]["response"]["parent"]["id"] = "999"
        self.assert_hold()

    def test_invalid_explicit_ownership_does_not_fall_back(self):
        called = []
        bad = dict(self.ownership, ignored_source=True)
        with self.assertRaises(policy.OwnRecordHold):
            policy.compare_or_strict(self.native, self.legacy, controlled=self.controlled,
                                     ownership=bad, strict_consumer=lambda *args: called.append(args))
        self.assertEqual(called, [])

    def test_absent_ownership_invokes_unchanged_strict_callback(self):
        calls = []
        marker = object()
        def strict(native, legacy):
            calls.append((native, legacy))
            return marker
        self.assertIs(policy.compare_or_strict(self.native, self.legacy,
                                             controlled=None, ownership=None,
                                             strict_consumer=strict), marker)
        self.assertEqual(calls, [(self.native, self.legacy)])

    def test_strict_fallback_error_propagates(self):
        def strict(*args):
            raise ValueError("original strict hold")
        with self.assertRaisesRegex(ValueError, "original strict hold"):
            policy.compare_or_strict(self.native, self.legacy, controlled=None,
                                     ownership=None, strict_consumer=strict)

    def test_ambiguous_or_own_prior_identity_holds(self):
        for ids in ([PRIOR, PRIOR], [PRIOR, RID], [], [True]):
            with self.subTest(ids=ids):
                self.setUp()
                self.ownership["prior_ids"] = ids
                self.assert_hold()

    def test_creation_http_body_endpoint_or_response_identity_holds(self):
        for mutation in (
            lambda o: o["creation_receipt"].__setitem__("http_status", 200),
            lambda o: o["creation_receipt"].__setitem__("request_body_sha256", "0" * 64),
            lambda o: o["creation_receipt"].__setitem__("url", policy.BASE + "/api/deposit/depositions/999/actions/newversion"),
            lambda o: o["creation_receipt"]["response"].__setitem__("id", True),
            lambda o: o["creation_receipt"]["response"].__setitem__("conceptrecid", int(RID)),
        ):
            self.setUp()
            mutation(self.ownership)
            self.assert_hold()

    def test_first_pair_endpoint_accept_identity_or_status_holds(self):
        for mutation in (
            lambda o: o["first_native_receipt"].__setitem__("accept", "application/json"),
            lambda o: o["first_native_receipt"].__setitem__("url", policy.BASE + "/api/records/999/draft"),
            lambda o: o["first_native_receipt"]["response"].__setitem__("id", PRIOR),
            lambda o: o["first_legacy_receipt"]["response"].__setitem__("conceptrecid", "999"),
            lambda o: o["first_legacy_receipt"].__setitem__("status", "HOLD_TRANSPORT_UNCERTAIN_NO_RETRY"),
            lambda o: o["first_native_receipt"].__setitem__("http_status", True),
        ):
            self.setUp()
            mutation(self.ownership)
            self.assert_hold()

    def test_community_display_fields_are_logged(self):
        row = self.legacy["metadata"]["communities"][0]
        row.update(title="Server display", links={"self": "https://zenodo.org/server/community"})
        result = self.audit()
        self.assertEqual(result["housekeeping"]["legacy"]["observed_record"]["metadata"]["communities"][0], row)

    def test_equivalent_community_identifiers_and_aliases_pass(self):
        for row in ({"id": "viridis-canon"},
                    {"identifier": "viridis-canon"},
                    {"id": "viridis-canon", "identifier": "viridis-canon", "title": "display"}):
            with self.subTest(row=row):
                self.setUp()
                self.legacy["metadata"]["communities"] = [row]
                self.audit()

    def test_first_draft_pending_native_membership_passes_exact_request_mirror(self):
        self.ownership["creation_receipt"]["url"] = policy.BASE + "/api/deposit/depositions"
        self.native["parent"]["communities"] = {}
        result = self.audit()
        self.assertEqual(result["housekeeping"]["native"]["observed_record"]["parent"]["communities"], {})

    def test_first_draft_empty_lists_and_noncontradictory_graph_display_pass(self):
        self.native["parent"]["communities"] = {"ids": [], "entries": [], "default": None, "display": "pending"}
        self.audit()

    def test_pending_membership_requires_exact_legacy_and_native_mirror(self):
        for mutation in (lambda: self.native["custom_fields"].pop("legacy:communities"),
                         lambda: self.native["custom_fields"].__setitem__("legacy:communities", ["foreign"]),
                         lambda: self.legacy["metadata"].__setitem__("communities", [])):
            self.setUp()
            self.native["parent"]["communities"] = {}
            mutation()
            self.assert_hold()

    def test_public_missing_membership_never_uses_pending_draft_branch(self):
        self.native, self.legacy, self.controlled, self.ownership = fixture(phase="PUBLISHED", doi_required=True)
        self.native["parent"]["communities"] = {}
        self.assert_hold()

    def test_partial_foreign_or_contradictory_draft_graph_holds(self):
        for graph in ({"ids": ["foreign"], "entries": []},
                      {"ids": [], "entries": [{"id": COMMUNITY_ID, "slug": "viridis-canon"}]},
                      {"ids": [], "entries": [], "default": "foreign"},
                      {"ids": [COMMUNITY_ID], "entries": [{"id": COMMUNITY_ID, "slug": "foreign"}]}):
            self.setUp()
            self.native["parent"]["communities"] = graph
            self.assert_hold()

    def test_community_missing_wrong_or_contradictory_identifiers_hold(self):
        for row in ({"title": "viridis-canon"}, {"id": "other"},
                    {"id": "viridis-canon", "identifier": "other"},
                    {"id": "viridis-canon", "identifier": True},
                    {"id": "viridis-canon", "identifier": ""}):
            with self.subTest(row=row):
                self.setUp()
                self.legacy["metadata"]["communities"] = [row]
                self.assert_hold()

    def test_first_get_creation_display_is_not_ownership_authority(self):
        for role in ("first_native_receipt", "first_legacy_receipt"):
            for value in ("2030-01-01T00:00:00Z", None):
                with self.subTest(role=role, value=value):
                    self.setUp()
                    self.ownership[role]["response"]["created"] = value
                    self.assertEqual(policy.require_ownership(**self.ownership)["creation_publication_date"], DATE)
                    self.audit()

    def test_creation_ack_requires_authenticated_aware_date(self):
        for value in (None, "not-a-date", "2026-10-08T00:00:00", True):
            with self.subTest(value=value):
                self.setUp()
                self.ownership["creation_receipt"]["response"]["created"] = value
                self.assert_hold()

    def test_controls_cannot_borrow_another_own_identity(self):
        self.controlled["record_id"] = "103"
        self.assert_hold()

    def test_creating_a_new_week_has_distinct_own_scope(self):
        self.ownership["creation_receipt"]["url"] = policy.BASE + "/api/deposit/depositions"
        scope = policy.require_ownership(**self.ownership)
        self.assertEqual(scope["start_kind"], "CREATE_WEEK")


class AuthorityTests(unittest.TestCase):
    def test_exact_independent_approved_authority_passes(self):
        result = policy.require_authority(AUTHORITY_FIXTURE)
        self.assertEqual(result["section_sha256"], hashlib.sha256(AUTHORITY_FIXTURE).hexdigest())

    def test_authority_tamper_or_old_policy_holds(self):
        for body in (AUTHORITY_FIXTURE.replace(b"America/New_York", b"UTC"),
                     b"Old server managed policy with no own-record authority"):
            with self.subTest(body=body[:40]):
                with self.assertRaises(policy.OwnRecordHold):
                    policy.require_authority(body)

    def test_duplicate_approved_authority_is_ambiguous(self):
        with self.assertRaises(policy.OwnRecordHold):
            policy.require_authority(AUTHORITY_FIXTURE + AUTHORITY_FIXTURE)

    def test_authority_must_be_exact_bytes(self):
        with self.assertRaises(policy.OwnRecordHold):
            policy.require_authority(AUTHORITY_FIXTURE.decode("utf-8"))


class DateTests(unittest.TestCase):
    def test_creation_date_uses_authenticated_utc_day(self):
        self.assertEqual(policy.creation_date("2026-10-07T23:30:00-04:00"), "2026-10-08")

    def test_put_date_uses_new_york_publish_day(self):
        self.assertEqual(policy.publication_date("2026-10-08T02:15:00Z"), "2026-10-07")
        payload = {"metadata": {"publication_date": "2026-10-07"}}
        self.assertEqual(policy.require_metadata_put(payload, publish_at=CREATED), payload)
        payload["metadata"]["publication_date"] = "2026-10-08"
        with self.assertRaises(policy.OwnRecordHold):
            policy.require_metadata_put(payload, publish_at=CREATED)

    def test_date_requires_explicit_timezone_and_value(self):
        for value in ("2026-10-08", "2026-10-08T02:15:00", True, "invalid"):
            for function in (policy.creation_date, policy.publication_date):
                with self.subTest(value=value, function=function.__name__):
                    with self.assertRaises(policy.OwnRecordHold):
                        function(value)

    def test_every_put_needs_explicit_correct_date(self):
        for payload in ({"metadata": {}}, {"metadata": {"publication_date": DATE}, "extra": True}, {}):
            with self.subTest(payload=payload):
                with self.assertRaises(policy.OwnRecordHold):
                    policy.require_metadata_put(payload, publish_at=CREATED)


class PriorRecordTests(unittest.TestCase):
    def assert_hold(self, actual, before, *, representation="NATIVE", boundary="CREATE"):
        with self.assertRaises(policy.OwnRecordHold):
            policy.require_prior_exact(actual, before, representation=representation, boundary=boundary)

    def test_native_exact_body_is_unchanged(self):
        before = prior_native()
        result = policy.require_prior_exact(deepcopy(before), before, representation="NATIVE", boundary="EDIT")
        self.assertEqual(result["changed_flags"], [])
        self.assertIs(result["certifies"], False)

    def test_native_create_publish_and_discard_closed_flags(self):
        for boundary, flag, old, new in (
            ("CREATE", "is_latest_draft", True, False),
            ("PUBLISH", "is_latest", True, False),
            ("DISCARD", "is_latest_draft", False, True),
        ):
            with self.subTest(boundary=boundary):
                before = prior_native()
                before["versions"][flag] = old
                if boundary == "PUBLISH":
                    before["versions"]["is_latest_draft"] = False
                actual = deepcopy(before)
                actual["versions"][flag] = new
                result = policy.require_prior_exact(actual, before, representation="NATIVE", boundary=boundary)
                self.assertEqual(result["changed_flags"], ["versions." + flag])
                self.assertEqual(before["versions"][flag], old)
                self.assertEqual(actual["versions"][flag], new)

    def test_wrong_boundary_direction_or_typed_native_flag_holds(self):
        for boundary, flag, old, new in (
            ("CREATE", "is_latest", True, False),
            ("EDIT", "is_latest_draft", True, False),
            ("PUBLISH", "is_latest_draft", True, False),
            ("CREATE", "is_latest_draft", False, True),
            ("DISCARD", "is_latest_draft", True, False),
            ("CREATE", "is_latest_draft", True, 0),
        ):
            with self.subTest(boundary=boundary, flag=flag, new=new):
                before = prior_native()
                before["versions"][flag] = old
                actual = deepcopy(before)
                actual["versions"][flag] = new
                self.assert_hold(actual, before, boundary=boundary)

    def test_prior_index_unknown_flag_or_parent_holds(self):
        for mutation in (lambda v: v["versions"].__setitem__("index", 3),
                         lambda v: v["versions"].__setitem__("unlisted_flag", True),
                         lambda v: v["parent"].__setitem__("id", "999")):
            before = prior_native()
            actual = deepcopy(before)
            actual["versions"]["is_latest_draft"] = False
            mutation(actual)
            self.assert_hold(actual, before)

    def test_every_nonflag_prior_leaf_remains_exact(self):
        mutations = {
            "title": lambda v: v["metadata"].__setitem__("title", "changed"),
            "date": lambda v: v["metadata"].__setitem__("publication_date", "2026-10-09"),
            "checksum": lambda v: v["files"]["entries"]["paper.pdf"].__setitem__("checksum", "md5:" + "c" * 32),
            "size": lambda v: v["files"]["entries"]["paper.pdf"].__setitem__("size", 18),
            "pid": lambda v: v["pids"]["doi"].__setitem__("identifier", "10.5281/zenodo.999"),
            "custom": lambda v: v["custom_fields"].__setitem__("extra", True),
            "created": lambda v: v.__setitem__("created", "2026-10-09T00:00:00Z"),
            "updated": lambda v: v.__setitem__("updated", "2026-10-09T00:00:00Z"),
            "revision": lambda v: v.__setitem__("revision_id", 4),
            "links": lambda v: v["links"].__setitem__("extra", "https://zenodo.org/extra"),
            "stats": lambda v: v["stats"].__setitem__("views", 5),
            "ui": lambda v: v["ui"].__setitem__("extra", True),
            "status": lambda v: v.__setitem__("status", "changed"),
            "unknown": lambda v: v.__setitem__("new_server_field", True),
            "disappearance": lambda v: v.pop("created"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                before = prior_native()
                actual = deepcopy(before)
                actual["versions"]["is_latest_draft"] = False
                mutation(actual)
                self.assert_hold(actual, before)

    def test_legacy_only_publish_is_last_changes(self):
        before = prior_legacy()
        actual = deepcopy(before)
        actual["metadata"]["relations"]["version"][0]["is_last"] = False
        result = policy.require_prior_exact(actual, before, representation="LEGACY", boundary="PUBLISH")
        self.assertEqual(result["changed_flags"], ["metadata.relations.version[0].is_last"])
        for boundary in ("CREATE", "EDIT", "DISCARD"):
            with self.subTest(boundary=boundary):
                self.assert_hold(actual, before, representation="LEGACY", boundary=boundary)

    def test_legacy_relation_index_parent_extra_row_or_bool_alias_holds(self):
        for mutation in (
            lambda v: v["metadata"]["relations"]["version"][0].__setitem__("index", 2),
            lambda v: v["metadata"]["relations"]["version"][0]["parent"].__setitem__("pid_value", "999"),
            lambda v: v["metadata"]["relations"]["version"].append(deepcopy(v["metadata"]["relations"]["version"][0])),
            lambda v: v["metadata"]["relations"]["version"][0].__setitem__("is_last", 0),
        ):
            before = prior_legacy()
            actual = deepcopy(before)
            actual["metadata"]["relations"]["version"][0]["is_last"] = False
            mutation(actual)
            self.assert_hold(actual, before, representation="LEGACY", boundary="PUBLISH")

    def test_legacy_nonflag_fields_remain_exact_at_publish(self):
        for mutation in (
            lambda v: v.__setitem__("modified", "2026-10-09T00:00:00Z"),
            lambda v: v["links"].__setitem__("server_link", "https://zenodo.org/other"),
            lambda v: v["stats"].__setitem__("views", 5),
            lambda v: v["metadata"].__setitem__("title", "changed"),
            lambda v: v["files"][0].__setitem__("checksum", "c" * 32),
            lambda v: v.__setitem__("doi", "10.5281/zenodo.999"),
        ):
            before = prior_legacy()
            actual = deepcopy(before)
            actual["metadata"]["relations"]["version"][0]["is_last"] = False
            mutation(actual)
            self.assert_hold(actual, before, representation="LEGACY", boundary="PUBLISH")

    def test_invalid_prior_scope_has_no_own_exemption(self):
        before = prior_native()
        with self.assertRaises(policy.OwnRecordHold):
            policy.require_prior_exact(before, before, representation="OWN", boundary="CREATE")


class OaiIdentityTests(unittest.TestCase):
    # Run only these eight new cases; inherited ordinary cases remain in
    # OwnRecordTests once, keeping the portable historical count explicit.
    setUp = OwnRecordTests.setUp
    audit = OwnRecordTests.audit

    def test_correct_own_oai_identity_passes_and_is_logged(self):
        row = {"identifier": "oai:zenodo.org:" + RID, "provider": "oai"}
        self.native["pids"]["oai"] = row
        result = self.audit()
        self.assertEqual(result["housekeeping"]["native"]["pids"]["oai"], row)
        self.assertIs(result["certifies"], False)

    def test_correct_parent_oai_identity_passes_and_is_logged(self):
        row = {"identifier": "oai:zenodo.org:" + PARENT, "provider": "oai"}
        self.native["parent"]["pids"]["oai"] = row
        result = self.audit()
        self.assertEqual(result["housekeeping"]["native"]["parent"]["pids"]["oai"], row)

    def test_foreign_or_noncanonical_own_oai_identity_holds(self):
        for identifier in ("oai:zenodo.org:999", "oai:zenodo.org:" + PARENT,
                           "", True, 1, ["oai:zenodo.org:" + RID], {}):
            with self.subTest(identifier=identifier):
                self.setUp()
                self.native["pids"]["oai"] = {"identifier": identifier, "provider": "arbitrary"}
                with self.assertRaisesRegex(policy.OwnRecordHold, "CONTRADICTORY_OAI"):
                    self.audit()

    def test_foreign_or_noncanonical_parent_oai_identity_holds(self):
        for identifier in ("oai:zenodo.org:999", "oai:zenodo.org:" + RID,
                           "", False, 0, ["oai:zenodo.org:" + PARENT], {}):
            with self.subTest(identifier=identifier):
                self.setUp()
                self.native["parent"]["pids"]["oai"] = {"identifier": identifier, "provider": "arbitrary"}
                with self.assertRaisesRegex(policy.OwnRecordHold, "CONTRADICTORY_CONCEPT_OAI"):
                    self.audit()

    def test_absent_own_and_parent_oai_are_not_required(self):
        self.native["pids"].pop("oai", None)
        self.native["parent"]["pids"].pop("oai", None)
        result = self.audit()
        self.assertNotIn("oai", result["housekeeping"]["native"]["pids"])
        self.assertNotIn("oai", result["housekeeping"]["native"]["parent"]["pids"])

    def test_absent_or_none_identifier_has_no_shape_or_provider_rule(self):
        for place in ("own", "parent"):
            for row in (None, {}, {"provider": "arbitrary", "extra": [1, 2]},
                        {"identifier": None, "provider": False}, "unsent server representation"):
                with self.subTest(place=place, row=row):
                    self.setUp()
                    target = self.native["pids"] if place == "own" else self.native["parent"]["pids"]
                    target["oai"] = deepcopy(row)
                    result = self.audit()
                    logged = result["housekeeping"]["native"]
                    logged = logged["pids"] if place == "own" else logged["parent"]["pids"]
                    self.assertEqual(logged["oai"], row)

    def test_arbitrary_unsent_provider_and_housekeeping_survive_with_exact_identity(self):
        for place, identifier in (("own", RID), ("parent", PARENT)):
            with self.subTest(place=place):
                self.setUp()
                row = {"identifier": "oai:zenodo.org:" + identifier,
                       "provider": {"unsent": "arbitrary"}, "client": False,
                       "future_server_field": [1, {"value": "logged"}]}
                target = self.native["pids"] if place == "own" else self.native["parent"]["pids"]
                target["oai"] = row
                result = self.audit()
                logged = result["housekeeping"]["native"]
                logged = logged["pids"] if place == "own" else logged["parent"]["pids"]
                self.assertEqual(logged["oai"], row)

    def test_other_unsent_pid_fields_remain_logged_without_new_shape_policy(self):
        row = {"identifier": "uncontrolled:other-namespace:999", "provider": ["arbitrary"]}
        self.native["pids"]["future_pid"] = deepcopy(row)
        self.native["parent"]["pids"]["future_pid"] = deepcopy(row)
        result = self.audit()
        self.assertEqual(result["housekeeping"]["native"]["pids"]["future_pid"], row)
        self.assertEqual(result["housekeeping"]["native"]["parent"]["pids"]["future_pid"], row)


if __name__ == "__main__":
    unittest.main()
