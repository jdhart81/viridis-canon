import copy
import datetime as dt
import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import novelty_stage as n


class NoveltyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = {"id": "P8-01", "rank": 1, "exact_statement": "A positive channel information bound under an explicit erasure premise", "hypotheses": ["named Landauer premise"], "synonyms": [], "value_rationale": "Discriminates a useful model"}
        self.indices = {}
        for channel in ("mathlib", "canon"):
            path = self.root / (channel + ".json")
            data = {"schema_version": 1, "source": channel, "snapshot": {"complete": True, "revision": "123abc", "description": "Test source snapshot", "generated_at_utc": n.utc_now()}, "items": [{"title": channel + " channel information bound", "url": "https://example.test/" + channel, "text": "A channel information inequality under a named premise"}]}
            path.write_text(json.dumps(data))
            self.indices[channel] = str(path)

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, url, timeout):
        if "arxiv" in url:
            return b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/1234.56789</id><title>Channel information bound</title><summary>A positive channel bound</summary></entry></feed>'
        if "openalex" in url:
            return json.dumps({"results": [{"id": "https://openalex.org/W1", "title": "Information bound and erasure", "abstract_inverted_index": {"channel": [0], "information": [1]}}]}).encode()
        if "crossref" in url:
            return json.dumps({"message": {"items": [{"title": ["Positive channel erasure bound"], "DOI": "10.1234/positive", "abstract": "information bound"}]}}).encode()
        return json.dumps({"data": [{"title": "Channel semantic bound", "url": "https://example.test/semantic", "abstract": "information"}]}).encode()

    def search(self, target=None, fetcher=None):
        return n.assess(target or self.target, "Run-194", self.indices["mathlib"], self.indices["canon"], 0.5, fetcher or self.fetch)

    def review(self, search, status="LIKELY_NEW"):
        evidence = self.root / "source-statement.txt"
        evidence.write_text("Test fixture public-source statement at Theorem 1: I(X;Y) ≤ H(Y).\n")
        evidence_sha = n.hashlib.sha256(evidence.read_bytes()).hexdigest()
        comparisons = []
        for source in search["top_closest_sources"]:
            comparisons.append({"url": source["url"], "source_statement": "I(X;Y) ≤ H(Y)", "source_hypotheses": ["finite random variables"], "target_hypotheses": search["target"]["hypotheses"], "statement_locator": "Theorem 1", "source_evidence_sha256": evidence_sha, "source_evidence_path": str(evidence), "relation": "DISTINCT", "reason": "Target conclusion includes a new named cost variable absent from this result"})
        if status == "KNOWN":
            comparisons[0]["relation"] = "EQUIVALENT"
        elif status == "KNOWN_VARIANT":
            comparisons[0]["relation"] = "KNOWN_VARIANT"
        return {"evidence_root": str(self.root), "target_sha256": search["target_sha256"], "query_sha256": search["query_sha256"], "search_evidence_sha256": search["search_evidence_sha256"], "reviewer": "Test comparison reviewer", "reviewed_at_utc": n.utc_now(), "proposed_status": status, "one_line_reasoning": "Compared exact named premises and conclusion against the inspected source statements", "source_comparisons": comparisons, "coverage_review": {c: "Reviewed this snapshot's scope" for c in n.CHANNELS}, "novel_delta": "Cost-bounded extension beyond the cited information inequality"}

    def test_search_never_infers_novelty_from_hits(self):
        result = self.search()
        self.assertEqual("UNASSESSED", result["status"])
        self.assertEqual(5, len(result["top_closest_sources"]))
        self.assertTrue(all(c["status"] == "SUCCESS" for c in result["source_coverage"]))

    def test_reviewed_likely_new(self):
        search = self.search()
        self.assertEqual("LIKELY_NEW", n.classify(search, self.review(search))["status"])

    def test_known_requires_equivalent_statement(self):
        search = self.search()
        self.assertEqual("KNOWN", n.classify(search, self.review(search, "KNOWN"))["status"])
        review = self.review(search)
        review["proposed_status"] = "KNOWN"
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_variant_requires_comparison(self):
        search = self.search()
        self.assertEqual("KNOWN_VARIANT", n.classify(search, self.review(search, "KNOWN_VARIANT"))["status"])
        review = self.review(search)
        review["proposed_status"] = "KNOWN_VARIANT"
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_exact_inequalities_preserved(self):
        target = copy.deepcopy(self.target)
        target["exact_statement"] = "If x < 2 and y > 0, then x ≤ y."
        self.assertEqual(target["exact_statement"], n.target_spec(target)["exact_statement"])

    def test_missing_index_non_blocking(self):
        result = n.assess(self.target, "Run-194", None, None, 0.2, self.fetch)
        self.assertEqual("UNASSESSED", result["status"])
        self.assertTrue(result["failure_is_non_blocking"])
        self.assertTrue(any(c["status"] == "ERROR" for c in result["source_coverage"]))

    def test_malformed_response_cannot_be_likely_new(self):
        search = self.search(fetcher=lambda *_: b"<bad")
        self.assertEqual("UNASSESSED", search["status"])
        self.assertTrue(any(c["status"] == "ERROR" for c in search["source_coverage"]))
        self.assertEqual("UNASSESSED", n.classify(search, self.review(search))["status"])

    def test_openalex_failure_falls_back_semantic_scholar(self):
        def fetch(url, timeout):
            if "openalex" in url:
                raise TimeoutError("public API temporarily unavailable")
            return self.fetch(url, timeout)
        result = self.search(fetcher=fetch)
        channel = next(c for c in result["source_coverage"] if c["channel"] == "openalex_or_semantic_scholar")
        self.assertEqual("SUCCESS", channel["status"])
        self.assertEqual("semantic_scholar", channel["provider"])

    def test_global_deadline_bounds_hung_upstream(self):
        def hang(*_):
            time.sleep(2)
            return b"{}"
        start = time.monotonic()
        result = n.assess(self.target, "Run-194", None, None, 0.1, hang)
        self.assertLess(time.monotonic() - start, 0.6)
        self.assertEqual("UNASSESSED", result["status"])
        self.assertTrue(any(c["status"] == "TIMEOUT" for c in result["source_coverage"]))

    def test_index_text_hash_mismatch(self):
        path = Path(self.indices["mathlib"])
        data = json.loads(path.read_text())
        data["items"][0]["text_sha256"] = "0" * 64
        path.write_text(json.dumps(data))
        result = self.search()
        self.assertEqual("ERROR", next(c for c in result["source_coverage"] if c["channel"] == "mathlib")["status"])

    def test_partial_index_cannot_support_likely_new(self):
        path = Path(self.indices["mathlib"])
        data = json.loads(path.read_text())
        data["snapshot"]["complete"] = False
        path.write_text(json.dumps(data))
        search = self.search()
        self.assertEqual("UNASSESSED", n.classify(search, self.review(search))["status"])

    def test_stale_review_hash(self):
        search = self.search()
        review = self.review(search)
        review["target_sha256"] = "0" * 64
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_source_review_from_other_search_rejected(self):
        search = self.search()
        review = self.review(search)
        review["search_evidence_sha256"] = "0" * 64
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_tampered_source_search_rejected(self):
        search = self.search()
        review = self.review(search)
        search["all_candidate_sources"][0]["title"] += " altered"
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_old_search_requires_refresh(self):
        search = self.search()
        search["assessed_at_utc"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=8)).isoformat()
        search["search_evidence_sha256"] = n.digest(n.evidence_payload(search))
        self.assertEqual("UNASSESSED", n.classify(search, self.review(search))["status"])

    def test_omitted_hypothesis_rejected(self):
        search = self.search()
        review = self.review(search)
        review["source_comparisons"][0]["target_hypotheses"] = []
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_inspection_requires_statement_evidence_and_locator(self):
        search = self.search()
        for field in ("source_statement", "source_evidence_sha256", "statement_locator"):
            review = self.review(search)
            review["source_comparisons"][0].pop(field)
            self.assertEqual("UNASSESSED", n.classify(search, review)["status"], field)

    def test_uninspected_top_source_rejected(self):
        search = self.search()
        review = self.review(search)
        review["source_comparisons"].pop()
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_likely_new_requires_all_channel_review_notes(self):
        search = self.search()
        review = self.review(search)
        review["coverage_review"].pop("canon")
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_zero_hits_does_not_establish_novelty(self):
        search = self.search()
        search["all_candidate_sources"] = []
        search["top_closest_sources"] = []
        search["search_evidence_sha256"] = n.digest(n.evidence_payload(search))
        review = self.review(search)
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_known_target_skipped(self):
        search = self.search()
        known = n.classify(search, self.review(search, "KNOWN"))
        other = {**self.target, "id": "P8-02", "rank": 2}
        result = n.select_target([self.target, other], {"P8-01": known})
        self.assertEqual("P8-02", result["portfolio_item_id"])
        self.assertEqual(1, len(result["skipped"]))

    def test_unreviewed_known_cannot_skip_target(self):
        result = n.select_target([self.target], {"P8-01": {"status": "KNOWN"}})
        self.assertEqual("P8-01", result["portfolio_item_id"])
        self.assertEqual("UNASSESSED", result["novelty_status"])

    def test_likely_new_preferred_to_unassessed(self):
        search = self.search()
        novel = n.classify(search, self.review(search))
        other = {**self.target, "id": "P8-02", "rank": 0}
        result = n.select_target([other, self.target], {"P8-01": novel})
        self.assertEqual("P8-01", result["portfolio_item_id"])

    def test_known_variant_deprioritized_unless_explicit_extension(self):
        search = self.search()
        variant = n.classify(search, self.review(search, "KNOWN_VARIANT"))
        other = {**self.target, "id": "P8-02", "rank": 2}
        self.assertEqual("P8-02", n.select_target([self.target, other], {"P8-01": variant})["portfolio_item_id"])
        extended = {**self.target, "extends_known": True, "extension_statement": "Replace scalar premise by a named product-channel premise"}
        search = self.search(extended)
        review = self.review(search, "KNOWN_VARIANT")
        variant = n.classify(search, review)
        self.assertEqual("P8-02", n.select_target([extended, other], {"P8-01": variant})["portfolio_item_id"])
        review["source_comparisons"][0]["relation"] = "EXTENSION"
        review["source_comparisons"][0]["target_extension_statement"] = extended["extension_statement"]
        variant = n.classify(search, review)
        self.assertEqual("P8-01", n.select_target([extended, other], {"P8-01": variant})["portfolio_item_id"])

    def test_selected_area_preserved_and_empty_pool_falls_back(self):
        item = {**self.target, "subject_area": "02"}
        self.assertEqual("P8-01", n.select_target([item], area="02")["portfolio_item_id"])
        result = n.select_target([item], area="01")
        self.assertIsNone(result["portfolio_item_id"])
        self.assertTrue(result["failure_is_non_blocking"])

    def test_history_counts_actual_attempts_once_not_proposals(self):
        history = [{"run_id": "Run-1", "attempted_at_utc": n.utc_now(), "portfolio_item_id": None}, {"run_id": "Run-1", "attempted_at_utc": n.utc_now(), "portfolio_item_id": None}, {"run_id": "Run-2", "proposed_at_utc": n.utc_now(), "portfolio_item_id": "P8-01"}]
        result = n.select_target([self.target], history=history)
        self.assertEqual(0, result["portfolio_hit_rate_before"])
        self.assertTrue(result["portfolio_quota_due"])

    def test_cli_missing_target_is_nonblocking(self):
        output = self.root / "NOVELTY_ASSESSMENT.json"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, n.main(["search", "--target", str(self.root / "missing.json"), "--output", str(output)]))
        self.assertEqual("UNASSESSED", json.loads(output.read_text())["status"])

    def test_known_positive_comparison_survives_other_search_outage(self):
        search = self.search()
        search["source_coverage"][0]["status"] = "ERROR"
        search["search_evidence_sha256"] = n.digest(n.evidence_payload(search))
        review = self.review(search, "KNOWN")
        self.assertEqual("KNOWN", n.classify(search, review)["status"])
        self.assertEqual("UNASSESSED", n.classify(search, self.review(search))["status"])

    def test_assessment_time_tampering_rejected(self):
        search = self.search()
        review = self.review(search)
        search["assessed_at_utc"] = n.utc_now()
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_top_five_tampering_rejected(self):
        search = self.search()
        review = self.review(search)
        search["top_closest_sources"] = search["top_closest_sources"][:3]
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_arxiv_substantive_terms_omit_boilerplate(self):
        query = n.urllib.parse.parse_qs(n.urllib.parse.urlsplit(n.api_url("arxiv", "For an explicitly frozen finite-state isothermal observation erasure model determine whether an entropy bound follows")).query)["search_query"][0]
        self.assertNotIn("all:for", query)
        self.assertNotIn("all:explicitly", query)
        self.assertIn("all:observation", query)

    def test_existing_frozen_artifact_never_overwritten(self):
        output = self.root / "NOVELTY_ASSESSMENT.json"
        output.write_bytes(b"frozen-original")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(0, n.main(["search", "--target", str(self.root / "missing.json"), "--output", str(output)]))
        self.assertEqual(b"frozen-original", output.read_bytes())

    def test_index_mutation_with_old_content_hash_rejected(self):
        path = Path(self.indices["mathlib"])
        data = json.loads(path.read_text())
        data["items"][0]["content_sha256"] = n.hashlib.sha256(data["items"][0]["text"].encode()).hexdigest()
        data["items"][0]["text"] += " altered claim"
        path.write_text(json.dumps(data))
        result = self.search()
        self.assertEqual("ERROR", next(c for c in result["source_coverage"] if c["channel"] == "mathlib")["status"])

    def test_explicit_review_root_cannot_disagree(self):
        search = self.search()
        review = self.review(search)
        self.assertEqual("UNASSESSED", n.classify(search, review, evidence_root=self.root / "other")["status"])

    def test_known_dominates_variant_and_likely_new_requests(self):
        search = self.search()
        for proposed in ("KNOWN_VARIANT", "LIKELY_NEW"):
            review = self.review(search, proposed)
            review["source_comparisons"][0]["relation"] = "EQUIVALENT"
            self.assertEqual("KNOWN", n.classify(search, review)["status"])

    def test_snapshot_freshness_missing_expired_future(self):
        path = Path(self.indices["mathlib"])
        original = json.loads(path.read_text())
        for timestamp in (None, (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=8)).isoformat(), (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat(), "invalid"):
            data = copy.deepcopy(original)
            if timestamp is None:
                data["snapshot"].pop("generated_at_utc")
            else:
                data["snapshot"]["generated_at_utc"] = timestamp
            path.write_text(json.dumps(data))
            search = self.search()
            row = next(c for c in search["source_coverage"] if c["channel"] == "mathlib")
            self.assertEqual("INCOMPLETE", row["status"], timestamp)
            self.assertEqual("UNASSESSED", n.classify(search, self.review(search))["status"])
        path.write_text(json.dumps(original))
        self.assertEqual("SUCCESS", next(c for c in self.search()["source_coverage"] if c["channel"] == "mathlib")["status"])

    def test_canon_forty_eight_hour_freshness(self):
        path = Path(self.indices["canon"])
        data = json.loads(path.read_text())
        data["snapshot"]["generated_at_utc"] = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=49)).isoformat()
        path.write_text(json.dumps(data))
        self.assertEqual("INCOMPLETE", next(c for c in self.search()["source_coverage"] if c["channel"] == "canon")["status"])

    def test_selector_current_new_york_week_and_generated_alias(self):
        current = dt.datetime(2026, 10, 14, 12, tzinfo=dt.timezone.utc)
        history = [
            {"run_id": "Run-1", "attempted_at_utc": "2026-10-11T20:00:00-04:00", "portfolio_item_id": "P8-01"},
            {"run_id": "Run-2", "generated_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-01"},
            {"run_id": "Run-3", "attempted_at_utc": "2026-10-12T03:00:00+00:00", "portfolio_item_id": "P8-01"},
        ]
        result = n.select_target([self.target], history=history, now=current)
        self.assertEqual(1, result["history_summary"]["actual_attempts_in_week"])
        self.assertEqual("2026-W42", result["history_summary"]["current_ny_iso_week"])
        self.assertEqual(1, result["portfolio_hit_rate_before"])

    def test_selector_invalid_id_timestamp_and_duplicate_conflict(self):
        current = dt.datetime(2026, 10, 14, 12, tzinfo=dt.timezone.utc)
        history = [
            {"run_id": "Run-1", "attempted_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-01"},
            {"run_id": "Run-1", "attempted_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-invalid"},
            {"run_id": "Run-2", "attempted_at_utc": "2026-10-12T02:00:00", "portfolio_item_id": "P8-01"},
            {"run_id": "Run-3", "generated_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-fake"},
            {"run_id": "Draft-4", "attempted_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-01"},
        ]
        result = n.select_target([self.target], history=history, now=current)
        self.assertEqual(2, result["history_summary"]["actual_attempts_in_week"])
        self.assertEqual(0, result["history_summary"]["portfolio_hits_in_week"])
        self.assertTrue(result["history_summary"]["history_warnings"])

    def test_selector_fraction_rounding_exact_integer_quota(self):
        current = dt.datetime(2026, 10, 14, 12, tzinfo=dt.timezone.utc)
        history = [{"run_id": "Run-" + str(i), "attempted_at_utc": "2026-10-12T01:00:00-04:00", "portfolio_item_id": "P8-01" if i < 3 else None} for i in range(5)]
        result = n.select_target([self.target], history=history, now=current)
        self.assertEqual(4, result["history_summary"]["portfolio_hits_required_after_next"])
        self.assertTrue(result["portfolio_quota_due"])
        history[3]["portfolio_item_id"] = "P8-01"
        self.assertFalse(n.select_target([self.target], history=history, now=current)["portfolio_quota_due"])

    def test_selector_retains_saved_review_root_after_cwd_change(self):
        search = self.search()
        review = self.review(search, "KNOWN")
        review.pop("evidence_root")
        known = n.classify(search, review, evidence_root=self.root)
        self.assertEqual("KNOWN", known["status"])
        self.assertIsNone(n.select_target([self.target], {"P8-01": known})["portfolio_item_id"])

    def test_missing_inspection_bytes_rejected(self):
        search = self.search()
        review = self.review(search)
        Path(review["source_comparisons"][0]["source_evidence_path"]).unlink()
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_changed_inspection_bytes_rejected(self):
        search = self.search()
        review = self.review(search)
        Path(review["source_comparisons"][0]["source_evidence_path"]).write_text("changed statement")
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_inspection_cannot_read_outside_advisory_folder(self):
        search = self.search()
        review = self.review(search)
        review["source_comparisons"][0]["source_evidence_path"] = "/etc/passwd"
        self.assertEqual("UNASSESSED", n.classify(search, review)["status"])

    def test_transient_retry_is_bounded_and_logged(self):
        attempts = []
        def fetch(url, timeout):
            attempts.append(url)
            if len(attempts) < 3:
                raise n.urllib.error.HTTPError(url, 429, "busy", {}, None)
            return b"{}"
        log = []
        with patch.object(n.time, "sleep") as sleeping:
            self.assertEqual(b"{}", n.fetch_bounded("https://example.test/public", time.monotonic() + 30, fetch, log))
        self.assertEqual(3, len(log))
        self.assertEqual([1.0, 2.0], [call.args[0] for call in sleeping.call_args_list])
        self.assertEqual(429, log[0]["http_status"])

    def test_response_size_cap(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return None
            def read(self, size):
                return b"x" * size
        with patch.object(n.urllib.request, "urlopen", return_value=Response()):
            with self.assertRaisesRegex(ValueError, "exceeded 1 MiB"):
                n.fetch_bytes("https://example.test/public", 1)

    def test_network_budget_cannot_exceed_ninety_seconds(self):
        result = n.assess(self.target, "Run-194", self.indices["mathlib"], self.indices["canon"], 999, self.fetch)
        self.assertEqual(90, result["search_budget_seconds"])

    def test_explicit_target_without_hypotheses_defaults_to_empty_list(self):
        self.assertEqual([], n.target_spec({"exact_statement": "1 ≤ 2"})["hypotheses"])
        with self.assertRaises(ValueError):
            n.target_spec({"exact_statement": "1 ≤ 2", "hypotheses": "hidden premise"})

    def test_no_verifier_or_publication_imports(self):
        import ast
        tree = ast.parse(Path(n.__file__).read_text())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.add(node.module)
        self.assertFalse(any("comparator" in name or "issuer" in name or "publication_gate" in name for name in names if name))

    def test_api_operators_are_not_injected(self):
        url = n.api_url("arxiv", 'observation OR id:unsafe')
        query = n.urllib.parse.parse_qs(n.urllib.parse.urlsplit(url).query)["search_query"][0]
        self.assertNotIn("id:", query)
        self.assertIn("all:observation", query)

    def test_provider_parser_rejects_arxiv_error_feed(self):
        with self.assertRaises(ValueError):
            n.parse_api("arxiv", b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/api/errors#incorrect_id_format</id><title>Error</title></entry></feed>')


if __name__ == "__main__":
    unittest.main()
