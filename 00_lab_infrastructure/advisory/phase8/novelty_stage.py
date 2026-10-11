#!/usr/bin/env python3
"""Advisory prior-art search; never verifies, certifies, or gates publication.

Public metadata is untrusted evidence. Labels beyond UNASSESSED require an
explicit statement/hypothesis comparison tied to this search's exact hash.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import queue
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

STATUS = {"KNOWN", "KNOWN_VARIANT", "LIKELY_NEW", "UNASSESSED"}
CHANNELS = ("arxiv", "openalex_or_semantic_scholar", "crossref", "mathlib", "canon")
MAX_RESPONSE_BYTES = 1024 * 1024
MAX_SEARCH_SECONDS = 90.0
USER_AGENT = "ViridisNoveltyAdvisory/1.0 (public read-only metadata search)"
QUERY_STOPWORDS = set("a an the for under from with without in on of to by and or as if then let assume assuming exists every each some all any explicit explicitly named frozen positive specified given proposed theorem lemma result proof prove determine whether can satisfy finite model statement relation conclusion hypotheses premise premises input output bound bounds".split())


def focused_terms(query, limit=6):
    terms = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_]+", query.lower()):
        if word not in QUERY_STOPWORDS and len(word) > 2 and word not in terms:
            terms.append(word)
    return terms[:limit]
DOCS = {
    "arxiv": "https://info.arxiv.org/help/api/user-manual.html",
    "openalex": "https://docs.openalex.org/api-entities/works/search-works",
    "semantic_scholar": "https://api.semanticscholar.org/api-docs/graph",
    "crossref": "https://www.crossref.org/documentation/retrieve-metadata/rest-api/",
}


def utc_now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stable_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def clean(text):
    return " ".join(str(text or "").split())


def words(text):
    return set(re.findall(r"[a-z][a-z0-9_]{2,}", clean(text).lower()))


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def target_spec(raw):
    if not isinstance(raw, dict):
        raise ValueError("target must be an object")
    target = dict(raw)
    statement = target.get("exact_statement", target.get("statement", ""))
    if not isinstance(statement, str):
        raise ValueError("exact statement must be a string")
    target["exact_statement"] = statement
    if not target["exact_statement"].strip():
        raise ValueError("target requires an exact statement")
    target.setdefault("hypotheses", [])
    if not isinstance(target["hypotheses"], list) or not all(isinstance(x, str) for x in target["hypotheses"]):
        raise ValueError("hypotheses must be an explicit list of strings, including []")
    target.setdefault("synonyms", [])
    if not isinstance(target["synonyms"], list) or not all(isinstance(x, str) for x in target["synonyms"]):
        raise ValueError("synonyms must be a list of strings")
    target.setdefault("value_rationale", "")
    target.setdefault("portfolio_item_id", target.get("id"))
    return target


def queries_for(target):
    # The full exact target remains hash-bound even when API query length is capped.
    proposed = target.get("queries", [])
    if not isinstance(proposed, list) or not all(isinstance(q, str) for q in proposed):
        raise ValueError("queries must be a list of strings")
    values = [target["exact_statement"]] + proposed + target.get("synonyms", [])
    result = []
    for value in values:
        query = " ".join(re.findall(r"[\w-]+", value, flags=re.UNICODE))[:350]
        if query and query not in result:
            result.append(query)
    return result[:3]


def fetch_bytes(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/atom+xml"})
    with urllib.request.urlopen(req, timeout=max(0.05, timeout)) as response:
        data = response.read(MAX_RESPONSE_BYTES + 1)
    if len(data) > MAX_RESPONSE_BYTES:
        raise ValueError("public metadata response exceeded 1 MiB")
    return data


def api_url(provider, query):
    if provider == "arxiv":
        # Query construction uses literal terms, not caller-supplied arXiv operators.
        parts = ["all:" + word for word in focused_terms(query)]
        if not parts:
            raise ValueError("arXiv query has no substantive search terms")
        return "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": " AND ".join(parts), "max_results": 10, "sortBy": "relevance"})
    if provider == "openalex":
        return "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": query, "per-page": 10})
    if provider == "semantic_scholar":
        return "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode({"query": query.replace("-", " "), "limit": 10, "fields": "title,url,abstract,year,externalIds"})
    if provider == "crossref":
        return "https://api.crossref.org/works?" + urllib.parse.urlencode({"query.bibliographic": query, "rows": 10})
    raise ValueError("unknown provider")


def parse_api(provider, body):
    hits = []
    if provider == "arxiv":
        root = ET.fromstring(body)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        if root.tag != "{http://www.w3.org/2005/Atom}feed":
            raise ValueError("arXiv returned a non-Atom feed")
        for entry in root.findall("a:entry", ns):
            url = clean(entry.findtext("a:id", "", ns))
            if "/api/errors" in url:
                raise ValueError("arXiv API error entry")
            hits.append({"title": clean(entry.findtext("a:title", "", ns)), "url": url.replace("http://", "https://"), "summary": clean(entry.findtext("a:summary", "", ns))[:1800], "published": entry.findtext("a:published", "", ns)})
    else:
        data = json.loads(body)
        if provider == "openalex":
            if not isinstance(data, dict) or not isinstance(data.get("results"), list):
                raise ValueError("malformed OpenAlex results")
            for item in data["results"]:
                abstract = item.get("abstract_inverted_index") or {}
                positions = [(int(p), token) for token, ps in abstract.items() for p in ps] if isinstance(abstract, dict) else []
                text = " ".join(token for _, token in sorted(positions))
                hits.append({"title": clean(item.get("title")), "url": item.get("doi") or item.get("id"), "summary": clean(text)[:1800], "published": item.get("publication_year")})
        elif provider == "semantic_scholar":
            if not isinstance(data, dict) or not isinstance(data.get("data"), list):
                raise ValueError("malformed Semantic Scholar results")
            for item in data["data"]:
                doi = (item.get("externalIds") or {}).get("DOI")
                hits.append({"title": clean(item.get("title")), "url": "https://doi.org/" + doi if doi else item.get("url"), "summary": clean(item.get("abstract"))[:1800], "published": item.get("year")})
        elif provider == "crossref":
            items = data.get("message", {}).get("items") if isinstance(data, dict) else None
            if not isinstance(items, list):
                raise ValueError("malformed Crossref items")
            for item in items:
                title = item.get("title", [])
                doi = item.get("DOI")
                hits.append({"title": clean(title[0] if isinstance(title, list) and title else ""), "url": "https://doi.org/" + doi if doi else item.get("URL"), "summary": clean(item.get("abstract"))[:1800], "published": item.get("published", item.get("issued", {}))})
    for hit in hits:
        if not hit.get("title") or not isinstance(hit.get("url"), str) or not hit["url"].startswith(("https://", "http://")):
            raise ValueError("metadata hit missing title or public link")
    return hits


def fetch_bounded(url, deadline, fetcher, retry_log):
    for number in range(1, 4):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Overall advisory deadline elapsed")
        entry = {"attempt": number, "requested_at_utc": utc_now()}
        try:
            body = fetcher(url, min(12.0, remaining))
            if not isinstance(body, bytes) or len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("metadata response must be bytes within 1 MiB")
            entry.update(status="RECEIVED", response_sha256=hashlib.sha256(body).hexdigest())
            retry_log.append(entry)
            return body
        except Exception as exc:
            code = getattr(exc, "code", None)
            transient = code == 429 or (isinstance(code, int) and 500 <= code < 600) or isinstance(exc, (TimeoutError, urllib.error.URLError))
            entry.update(status="ERROR", error_type=type(exc).__name__)
            if code is not None:
                entry["http_status"] = code
            retry_log.append(entry)
            if isinstance(exc, urllib.error.HTTPError):
                exc.close()
            delay = float(number)
            if not transient or number == 3 or deadline - time.monotonic() <= delay + 0.1:
                raise
            time.sleep(delay)


def search_remote(channel, queries, deadline, fetcher=fetch_bytes):
    providers = ["openalex", "semantic_scholar"] if channel == "openalex_or_semantic_scholar" else [channel]
    attempts, combined = [], []
    for provider in providers:
        success = True
        for query in queries:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                success = False
                attempts.append({"provider": provider, "query": query, "status": "TIMEOUT"})
                break
            url = api_url(provider, query)
            attempt = {"provider": provider, "query": query, "url": url, "retrieved_at_utc": utc_now()}
            try:
                attempt["network_attempts"] = []
                body = fetch_bounded(url, deadline, fetcher, attempt["network_attempts"])
                attempt["response_sha256"] = hashlib.sha256(body).hexdigest()
                hits = parse_api(provider, body)
                attempt.update(status="SUCCESS", hit_count=len(hits))
                for hit in hits:
                    hit.update(channel=channel, provider=provider, response_sha256=attempt["response_sha256"], retrieved_at_utc=attempt["retrieved_at_utc"], matched_query=query)
                    combined.append(hit)
            except Exception as exc:
                success = False
                attempt.update(status="ERROR", error=type(exc).__name__ + ": " + clean(str(exc))[:180])
            attempts.append(attempt)
            if provider == "arxiv" and query != queries[-1]:
                # arXiv requests are spaced by its documented three-second guidance.
                time.sleep(min(3.0, max(0.0, deadline - time.monotonic())))
        if success:
            return {"channel": channel, "status": "SUCCESS", "provider": provider, "queries": attempts, "hits": combined, "scope": "Top 10 metadata hits per query; not exhaustive literature coverage"}
    return {"channel": channel, "status": "ERROR", "queries": attempts, "hits": combined, "scope": "Incomplete metadata search; no novelty inference"}


def similarity(query, title, text):
    wanted, found = words(query), words(title + " " + text)
    return round(len(wanted & found) / max(1, len(wanted)), 6)


def search_index(channel, index_path, queries, deadline):
    if not index_path:
        return {"channel": channel, "status": "ERROR", "error": "Missing read-only index", "hits": []}
    index_file = Path(index_path)
    if index_file.stat().st_size > 128 * 1024 * 1024:
        raise ValueError("index larger than 128 MiB")
    body = index_file.read_bytes()
    if len(body) > 128 * 1024 * 1024:
        raise ValueError("index grew larger than 128 MiB while read")
    data = json.loads(body)
    if not isinstance(data, dict) or data.get("source") != channel or not isinstance(data.get("items"), list):
        raise ValueError("index source or items malformed")
    snapshot = data.get("snapshot") or {}
    complete = snapshot.get("complete") is True and bool(snapshot.get("revision")) and bool(snapshot.get("description"))
    freshness = "CURRENT"
    try:
        generated = parse_time(snapshot["generated_at_utc"])
        current = dt.datetime.now(dt.timezone.utc)
        allowance = dt.timedelta(days=7) if channel == "mathlib" else dt.timedelta(hours=48)
        if generated > current + dt.timedelta(minutes=5) or current - generated > allowance:
            complete = False
            freshness = "EXPIRED_OR_FUTURE"
    except Exception:
        complete = False
        freshness = "MISSING_OR_INVALID_TIMESTAMP"
    hits = []
    query_word_sets = [words(query) for query in queries]
    for item in data["items"]:
        if time.monotonic() >= deadline:
            return {"channel": channel, "status": "TIMEOUT", "hits": hits, "index_sha256": hashlib.sha256(body).hexdigest()}
        if not isinstance(item, dict) or not isinstance(item.get("text"), str) or not item.get("title") or not item.get("url"):
            raise ValueError("index item missing text/title/url")
        if not item["url"].startswith(("https://", "http://", "file://")):
            raise ValueError("index link must be a public URL or explicit local source file")
        text_sha = hashlib.sha256(item["text"].encode()).hexdigest()
        if item.get("text_sha256") and item["text_sha256"] != text_sha:
            raise ValueError("index text hash mismatch")
        if item.get("content_sha256") and not item.get("text_sha256") and item["content_sha256"] != text_sha:
            raise ValueError("full-text index content hash mismatch; excerpts require an explicit text_sha256")
        source_words = words(item["title"] + " " + item["text"])
        scores = [round(len(wanted & source_words) / max(1, len(wanted)), 6) for wanted in query_word_sets]
        score = max(scores)
        if score > 0:
            hits.append({"title": item["title"], "url": item["url"], "summary": clean(item["text"])[:1800], "channel": channel, "provider": "read_only_index", "content_sha256": item.get("content_sha256", text_sha), "text_sha256": text_sha, "score": score, "matched_query": queries[scores.index(score)]})
    hits.sort(key=lambda h: (-h["score"], h["url"]))
    return {"channel": channel, "status": "SUCCESS" if complete else "INCOMPLETE", "index_sha256": hashlib.sha256(body).hexdigest(), "snapshot": snapshot, "snapshot_freshness": freshness, "queries": queries, "hits": hits[:20], "scope": "Bounded lexical search of stated read-only snapshot; no compilation or verification"}


def evidence_payload(assessment):
    return {key: assessment[key] for key in ("target_sha256", "query_sha256", "queries", "assessed_at_utc", "source_coverage", "all_candidate_sources", "top_closest_sources")}


def assess(target_raw, run_id=None, mathlib_index=None, canon_index=None, budget_seconds=75, fetcher=fetch_bytes):
    target = target_spec(target_raw)
    queries = queries_for(target)
    if not queries:
        raise ValueError("target has no searchable terms")
    budget = max(0.05, min(MAX_SEARCH_SECONDS, float(budget_seconds)))
    start = time.monotonic()
    deadline = start + budget
    mailbox = queue.Queue()
    def worker(channel):
        try:
            if channel in {"mathlib", "canon"}:
                result = search_index(channel, mathlib_index if channel == "mathlib" else canon_index, queries, deadline)
            else:
                result = search_remote(channel, queries, deadline, fetcher)
        except Exception as exc:
            result = {"channel": channel, "status": "ERROR", "error": type(exc).__name__ + ": " + clean(str(exc))[:180], "hits": []}
        mailbox.put(result)
    for channel in CHANNELS:
        # Daemon workers cannot hold up the generator if an upstream hangs.
        threading.Thread(target=worker, args=(channel,), daemon=True).start()
    responses = {}
    while len(responses) < len(CHANNELS) and time.monotonic() < deadline:
        try:
            result = mailbox.get(timeout=max(0.01, deadline - time.monotonic()))
            responses[result["channel"]] = result
        except queue.Empty:
            break
    coverage, hits = [], []
    for channel in CHANNELS:
        result = responses.get(channel, {"channel": channel, "status": "TIMEOUT", "hits": [], "error": "Overall advisory search deadline elapsed"})
        hits.extend(result.get("hits", []))
        coverage.append({k: v for k, v in result.items() if k != "hits"})
    dedup = {}
    for hit in hits:
        hit = dict(hit)
        hit["score"] = max(hit.get("score", 0), max(similarity(q, hit["title"], hit.get("summary", "")) for q in queries))
        key = hit["url"].lower().replace("http://doi.org/", "https://doi.org/")
        if key not in dedup or hit["score"] > dedup[key]["score"]:
            dedup[key] = hit
    ordered = sorted(dedup.values(), key=lambda h: (-h["score"], h["url"]))
    assessment = {"schema_version": 1, "advisory_only": True, "run_id": run_id or target.get("run_id"), "target": target, "target_sha256": digest(target), "query_sha256": digest(queries), "queries": queries, "assessed_at_utc": utc_now(), "search_budget_seconds": budget, "elapsed_seconds": round(time.monotonic() - start, 3), "source_coverage": coverage, "all_candidate_sources": ordered, "top_closest_sources": ordered[:5], "status": "UNASSESSED", "one_line_reasoning": "Statement and hypothesis comparison has not yet been reviewed; search hits or their absence do not establish novelty.", "classification_basis": "No comparison review", "api_documentation": DOCS, "failure_is_non_blocking": True}
    assessment["search_evidence_sha256"] = digest(evidence_payload(assessment))
    return assessment


def parse_time(value):
    result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return result


def classify(search, review, now=None, evidence_root=None):
    result = json.loads(json.dumps(search))
    result["status"] = "UNASSESSED"
    result["classification_basis"] = "Comparison review rejected or absent"
    try:
        if search.get("advisory_only") is not True or search.get("failure_is_non_blocking") is not True:
            raise ValueError("assessment is not an advisory-only artifact")
        if digest(evidence_payload(search)) != search.get("search_evidence_sha256"):
            raise ValueError("search evidence hash mismatch")
        if digest(target_spec(search["target"])) != search.get("target_sha256"):
            raise ValueError("target changed after search")
        if not isinstance(review, dict):
            raise ValueError("comparison review missing")
        if search.get("review_sha256") and digest(review) != search["review_sha256"]:
            raise ValueError("comparison review hash mismatch")
        for field in ("target_sha256", "query_sha256", "search_evidence_sha256"):
            if review.get(field) != search.get(field):
                raise ValueError("stale or mismatched review: " + field)
        current = now or dt.datetime.now(dt.timezone.utc)
        searched = parse_time(search["assessed_at_utc"])
        reviewed = parse_time(review["reviewed_at_utc"])
        if reviewed < searched or reviewed > current + dt.timedelta(minutes=5) or current - searched > dt.timedelta(days=7):
            raise ValueError("review/search time invalid or search older than seven days")
        if not clean(review.get("reviewer")) or not clean(review.get("one_line_reasoning")):
            raise ValueError("named reviewer and one-line reasoning required")
        coverage = {row["channel"]: row["status"] for row in search["source_coverage"]}
        requested = review.get("proposed_status")
        if requested not in STATUS:
            raise ValueError("invalid proposed novelty label")
        candidates = {hit["url"]: hit for hit in search["all_candidate_sources"]}
        inspection_root = Path(evidence_root or review.get("evidence_root") or ".").resolve()
        if evidence_root and review.get("evidence_root") and Path(review["evidence_root"]).resolve() != inspection_root:
            raise ValueError("saved review and supplied inspection root disagree")
        comparisons = review.get("source_comparisons", [])
        if not isinstance(comparisons, list):
            raise ValueError("source comparisons must be a list")
        inspected = {}
        for comparison in comparisons:
            if not isinstance(comparison, dict) or comparison.get("url") not in candidates:
                raise ValueError("comparison source is absent from this search")
            if not clean(comparison.get("source_statement")) or not clean(comparison.get("statement_locator")) or not clean(comparison.get("reason")) or not valid_sha(comparison.get("source_evidence_sha256")):
                raise ValueError("inspection requires source statement, locator, evidence hash and reason")
            evidence_path = comparison.get("source_evidence_path")
            if not isinstance(evidence_path, str) or not evidence_path:
                raise ValueError("inspection requires a saved source evidence file")
            saved_path = Path(evidence_path)
            saved_path = (saved_path if saved_path.is_absolute() else inspection_root / saved_path).resolve()
            if not saved_path.is_relative_to(inspection_root):
                raise ValueError("source evidence lies outside the advisory inspection folder")
            if not saved_path.is_file() or saved_path.stat().st_size > MAX_RESPONSE_BYTES:
                raise ValueError("source evidence missing or larger than 1 MiB; save a located excerpt")
            with saved_path.open("rb") as stream:
                saved_bytes = stream.read(MAX_RESPONSE_BYTES + 1)
            if len(saved_bytes) > MAX_RESPONSE_BYTES or hashlib.sha256(saved_bytes).hexdigest() != comparison["source_evidence_sha256"]:
                raise ValueError("saved source inspection bytes hash mismatch or size exceeded")
            if not isinstance(comparison.get("source_hypotheses"), list) or comparison.get("target_hypotheses") != search["target"]["hypotheses"]:
                raise ValueError("explicit hypothesis comparison missing or target hypotheses omitted")
            if comparison.get("relation") not in {"EQUIVALENT", "TARGET_SPECIAL_CASE", "KNOWN_VARIANT", "EXTENSION", "DISTINCT", "UNCERTAIN"}:
                raise ValueError("invalid statement relation")
            if comparison["url"] in inspected:
                raise ValueError("duplicate source comparison")
            inspected[comparison["url"]] = comparison
        has_known = any(c["relation"] in {"EQUIVALENT", "TARGET_SPECIAL_CASE"} for c in comparisons)
        requested_before_resolution = requested
        if has_known and requested != "UNASSESSED":
            requested = "KNOWN"
        if requested == "KNOWN" and not any(c["relation"] in {"EQUIVALENT", "TARGET_SPECIAL_CASE"} for c in comparisons):
            raise ValueError("KNOWN requires an inspected equivalent or stronger source statement")
        if requested == "KNOWN_VARIANT" and not any(c["relation"] in {"KNOWN_VARIANT", "EXTENSION"} for c in comparisons):
            raise ValueError("KNOWN_VARIANT requires an inspected close variant or explicit extension")
        if requested == "LIKELY_NEW":
            if any(coverage.get(channel) != "SUCCESS" for channel in CHANNELS):
                raise ValueError("one or more required source searches unavailable or incomplete")
            top_urls = {hit["url"] for hit in search["top_closest_sources"]}
            if len(inspected) < 3 or not top_urls or not top_urls <= set(inspected):
                raise ValueError("LIKELY_NEW requires inspection of every top-five hit and at least three sources")
            external = {candidates[url]["channel"] for url in inspected} & set(CHANNELS[:3])
            if len(external) < 2:
                raise ValueError("LIKELY_NEW requires inspected literature from at least two external channels")
            if any(c["relation"] not in {"DISTINCT", "EXTENSION"} for c in comparisons):
                raise ValueError("LIKELY_NEW contradicted by a known, variant or uncertain comparison")
            notes = review.get("coverage_review", {})
            if any(not clean(notes.get(channel)) for channel in CHANNELS):
                raise ValueError("LIKELY_NEW requires review notes for every source channel")
            if not clean(review.get("novel_delta")):
                raise ValueError("LIKELY_NEW requires an explicit mathematical delta")
        result.update(status=requested, one_line_reasoning=(("An inspected source already covers the exact target; classified KNOWN. " if requested_before_resolution != requested else "") + clean(review["one_line_reasoning"])), classification_basis="Advisory reviewed statement/hypothesis comparison, not a certificate of novelty", comparison_review=review, review_sha256=digest(review), classified_at_utc=utc_now(), review_evidence_root=str(inspection_root))
    except Exception as exc:
        result["one_line_reasoning"] = "UNASSESSED: " + clean(str(exc))[:240] + "; certification and publication continue independently."
    return result


def select_target(portfolio, assessments=None, history=None, run_id=None, area=None, now=None):
    items = portfolio.get("items", []) if isinstance(portfolio, dict) else portfolio
    assessments = assessments or {}
    history = history or []
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        raise ValueError("selector time must include timezone")
    current_week = current.astimezone(ZoneInfo("America/New_York")).isocalendar()[:2]
    valid_ids = {item.get("id", item.get("portfolio_item_id")) for item in items if isinstance(item, dict)}
    valid_ids.discard(None)
    attempted_by_run, history_warnings = {}, []
    for row in history:
        if not isinstance(row, dict) or not isinstance(row.get("run_id"), str) or not re.fullmatch(r"Run-[0-9]+", row["run_id"]):
            history_warnings.append("Ignored history row without canonical run ID")
            continue
        stamp = row.get("attempted_at_utc", row.get("generated_at_utc"))
        if not stamp:
            continue  # A selection proposal is not an attempted run.
        try:
            attempted_at = parse_time(stamp)
            if attempted_at > current + dt.timedelta(minutes=5):
                raise ValueError("future attempt")
        except Exception:
            history_warnings.append("Ignored invalid attempt timestamp for " + row["run_id"])
            continue
        item_id = row.get("portfolio_item_id")
        item_id = item_id if item_id in valid_ids else None
        previous = attempted_by_run.get(row["run_id"])
        if previous:
            previous["attempted_at"] = min(previous["attempted_at"], attempted_at)
            if previous["portfolio_item_id"] != item_id:
                previous["portfolio_item_id"] = None
                previous["conflicted"] = True
                history_warnings.append("Conflicting portfolio bindings for " + row["run_id"] + " counted as unknown")
        else:
            attempted_by_run[row["run_id"]] = {"attempted_at": attempted_at, "portfolio_item_id": item_id, "conflicted": False}
    attempted = [row for row in attempted_by_run.values() if row["attempted_at"].astimezone(ZoneInfo("America/New_York")).isocalendar()[:2] == current_week]
    hits = sum(row["portfolio_item_id"] is not None and not row["conflicted"] for row in attempted)
    required_after_next = (3 * (len(attempted) + 1) + 4) // 5  # ceil(0.6 * n), exact integers.
    quota_due = hits < required_after_next
    history_summary = {"current_ny_iso_week": "%04d-W%02d" % current_week, "actual_attempts_in_week": len(attempted), "portfolio_hits_in_week": hits, "portfolio_hits_required_after_next": required_after_next, "history_warnings": history_warnings}
    candidates = []
    skipped = []
    rank_label = {"LIKELY_NEW": 0, "UNASSESSED": 1, "KNOWN_VARIANT": 2}
    for raw in items:
        target = target_spec(raw)
        if target.get("status", "OPEN") not in {"OPEN", "IN_PROGRESS"}:
            continue
        area_ids = target.get("area_ids", [target.get("subject_area")])
        if area and area not in area_ids:
            continue
        assessment = assessments.get(target.get("id", target.get("portfolio_item_id")), {})
        label = "UNASSESSED"
        if assessment.get("target_sha256") == digest(target) and assessment.get("comparison_review"):
            label = classify(assessment, assessment["comparison_review"], evidence_root=assessment.get("review_evidence_root")).get("status", "UNASSESSED")
        if label not in STATUS:
            label = "UNASSESSED"
        if label == "KNOWN":
            skipped.append({"id": target.get("id"), "reason": "Reviewed KNOWN target skipped"})
            continue
        # Only an explicit reviewed extension avoids variant deprioritization.
        extension = label == "KNOWN_VARIANT" and target.get("extends_known") is True and clean(target.get("extension_statement")) and any(comparison.get("relation") == "EXTENSION" and comparison.get("target_extension_statement") == target.get("extension_statement") for comparison in assessment.get("comparison_review", {}).get("source_comparisons", []))
        priority = 1 if extension else rank_label[label]
        candidates.append((priority, int(target.get("rank", 999)), target.get("id", ""), target, label))
    candidates.sort(key=lambda row: row[:3])
    if not candidates:
        return {"schema_version": 1, "advisory_only": True, "run_id": run_id, "proposed_at_utc": utc_now(), "portfolio_item_id": None, "target": None, "novelty_status": "UNASSESSED", "value_rationale": "No eligible non-KNOWN portfolio target in the original selected subject area; generator must propose a new target with one-line value rationale.", "policy_reason": "Advisory fallback; original generator and certification continue", "portfolio_quota_due": quota_due, "history_summary": history_summary, "skipped": skipped, "failure_is_non_blocking": True}
    _, _, _, target, label = candidates[0]
    return {"schema_version": 1, "advisory_only": True, "run_id": run_id, "proposed_at_utc": utc_now(), "portfolio_item_id": target.get("portfolio_item_id", target.get("id")), "target": target, "novelty_status": label, "value_rationale": target.get("value_rationale", ""), "policy_reason": "Prefer reviewed LIKELY_NEW; skip KNOWN; deprioritize variants without an explicit extension; preserve original subject area", "portfolio_quota_due": quota_due, "portfolio_hit_rate_before": hits / len(attempted) if attempted else None, "history_summary": history_summary, "skipped": skipped, "failure_is_non_blocking": True}


def write_new(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation preserves frozen advisory evidence from accidental reruns.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    search = sub.add_parser("search", help="Bounded read-only search; emits UNASSESSED before review")
    search.add_argument("--target", required=True)
    search.add_argument("--run-id")
    search.add_argument("--mathlib-index")
    search.add_argument("--canon-index")
    search.add_argument("--budget-seconds", type=float, default=75)
    search.add_argument("--output", required=True)
    review = sub.add_parser("classify", help="Apply an explicit hash-bound statement comparison review")
    review.add_argument("--search", required=True)
    review.add_argument("--review", required=True)
    review.add_argument("--output", required=True)
    select = sub.add_parser("select", help="Propose a portfolio target; does not generate a run")
    select.add_argument("--portfolio", required=True)
    select.add_argument("--assessments")
    select.add_argument("--history")
    select.add_argument("--run-id")
    select.add_argument("--area")
    select.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "search":
            result = assess(read_json(args.target), args.run_id, args.mathlib_index, args.canon_index, args.budget_seconds)
        elif args.command == "classify":
            result = classify(read_json(args.search), read_json(args.review), evidence_root=Path(args.review).parent)
        else:
            result = select_target(read_json(args.portfolio), read_json(args.assessments) if args.assessments else None, read_json(args.history) if args.history else None, args.run_id, args.area)
        write_new(args.output, result)
        print(json.dumps({"advisory_only": True, "status": result.get("status", result.get("novelty_status")), "output": str(Path(args.output)), "failure_is_non_blocking": True}))
    except Exception as exc:
        fallback = {"schema_version": 1, "advisory_only": True, "run_id": getattr(args, "run_id", None), "assessed_at_utc": utc_now(), "status": "UNASSESSED", "top_closest_sources": [], "one_line_reasoning": "Advisory stage unavailable: " + type(exc).__name__ + ": " + clean(str(exc))[:240], "failure_is_non_blocking": True}
        try:
            write_new(args.output, fallback)
        except Exception:
            # Never overwrite an existing/frozen artifact or block the original flow.
            pass
        print(json.dumps(fallback))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
