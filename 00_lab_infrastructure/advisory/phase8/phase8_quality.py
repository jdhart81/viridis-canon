#!/usr/bin/env python3
"""Advisory science targeting metrics. This module never issues a gate or certificate.

Generation dates come only from manifests, certification status only from the
existing corpus ledger. Missing assessment/classification remains unknown.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import novelty_stage
except ImportError:
    novelty_stage = None

NOVELTY_STATUSES = {"KNOWN", "KNOWN_VARIANT", "LIKELY_NEW", "UNASSESSED"}
ASSESSED_DEPTH = {"DEFINITIONAL", "ROUTINE", "SUBSTANTIVE"}
RUN_ID = re.compile(r"Run-\d{3,}")
PORTFOLIO_ID = re.compile(r"P8-(?:0[1-9]|1[0-9]|20)")
TIMEZONE = ZoneInfo("America/New_York")


def iso_datetime(value: object) -> datetime | None:
    """A naive or malformed date cannot date an actual run."""
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return result if result.tzinfo is not None else None


def json_read(path: Path, bindings: dict, gaps: list) -> dict | None:
    try:
        raw = path.read_bytes()
        bindings[str(path)] = hashlib.sha256(raw).hexdigest()
        result = json.loads(raw)
        if not isinstance(result, dict):
            raise ValueError("object required")
        return result
    except (OSError, ValueError) as exc:
        gaps.append({"path": str(path), "reason": f"{type(exc).__name__}: {exc}"})
        return None


def strict_novelty(assessment: dict | None, run_id: str, run_attempt_at: datetime | None = None) -> str:
    if not isinstance(assessment, dict) or assessment.get("run_id") != run_id:
        return "UNASSESSED"
    status = assessment.get("status")
    if not isinstance(status, str) or status not in NOVELTY_STATUSES or status == "UNASSESSED":
        return "UNASSESSED"
    if novelty_stage is None or assessment.get("stale_at_run") is True or assessment.get("valid_at_target_selection") is False:
        return "UNASSESSED"
    try:
        review = assessment.get("comparison_review")
        classified = iso_datetime(assessment.get("classified_at_utc"))
        searched = iso_datetime(assessment.get("assessed_at_utc"))
        if not isinstance(review, dict) or classified is None or searched is None:
            return "UNASSESSED"
        if classified > datetime.now(timezone.utc) + timedelta(minutes=5):
            return "UNASSESSED"
        if assessment.get("review_sha256") != novelty_stage.digest(review):
            return "UNASSESSED"
        if assessment.get("target", {}).get("run_id", run_id) != run_id:
            return "UNASSESSED"
        if run_attempt_at and (classified > run_attempt_at + timedelta(minutes=5)
                               or run_attempt_at - searched > timedelta(days=7)):
            return "UNASSESSED"
        # Re-check the exact evidence at its original classification time. The
        # passing label does not expire merely because a later weekly report runs.
        checked = novelty_stage.classify(assessment, review, now=classified,
                                        evidence_root=assessment.get("review_evidence_root"))
        return status if checked.get("status") == status else "UNASSESSED"
    except Exception:
        return "UNASSESSED"


def add_novelty_to_claims(claims: list, assessment: dict | None, run_id: str) -> list:
    """Return an additive copy; the scientific/evidence fields stay byte-equivalent."""
    if not isinstance(claims, list) or any(not isinstance(row, dict) for row in claims):
        raise ValueError("claims must be an array of objects")
    result = copy.deepcopy(claims)
    for row in result:
        row["novelty_status"] = strict_novelty(assessment, run_id)
    return result


def md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def render_claim_table(claims: list, assessment: dict | None, run_id: str) -> str:
    """Render a new future-note table, retaining scope/evidence and adding novelty."""
    rows = add_novelty_to_claims(claims, assessment, run_id)
    output = ["| Claim / theorem | Evidence class | Foundation basis | Depth | Run-target novelty |",
              "|---|---|---|---|---|"]
    for row in rows:
        output.append("| " + " | ".join(md_cell(row.get(key, default)) for key, default in [
            ("lean_theorem", row.get("id", row.get("claim", "unspecified"))),
            ("evidence_class", "UNASSESSED"), ("foundation_basis", "UNSPECIFIED"),
            ("semantic_tier", "DEPTH_NOT_ASSESSED"), ("novelty_status", "UNASSESSED")]) + " |")
    output.append("\nRun-target novelty assesses the overall proposed target, not each auxiliary theorem. "
                  "It is a literature assessment, not certificate evidence. "
                  "logical validity given the model, not empirical validation of its assumptions")
    if isinstance(assessment, dict):
        output.append("Assessment: NOVELTY_ASSESSMENT.json; target SHA-256: " + md_cell(assessment.get("target_sha256", "UNRECORDED"))
                      + "; search-evidence SHA-256: " + md_cell(assessment.get("search_evidence_sha256", "UNRECORDED")) + ".")
    return "\n".join(output) + "\n"


def render_digest_table(notes: list, assessments: dict) -> str:
    """Generate an advisory per-run table beside, never inside, frozen metadata."""
    output = ["| Run | Run-target novelty | Portfolio item | Reason |", "|---|---|---|---|"]
    seen = set()
    for note in notes:
        if not isinstance(note, dict):
            continue
        run_id = note.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id) or run_id in seen:
            continue
        seen.add(run_id)
        assessment = assessments.get(run_id)
        output.append("| " + " | ".join(md_cell(value) for value in [
            run_id, strict_novelty(assessment, run_id), note.get("portfolio_item_id") or "UNRECORDED",
            (assessment if isinstance(assessment, dict) else {}).get("one_line_reasoning", "No valid assessment supplied.")]) + " |")
    output.append("\nRun-target labels do not assert novelty of each auxiliary theorem. These advisory labels do not change claim scope, evidence class, foundation basis or certification.")
    return "\n".join(output) + "\n"


def tex_escape(value: object) -> str:
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(value).replace("\n", " "))


def render_claim_table_tex(claims: list, assessment: dict | None, run_id: str) -> str:
    """Authoring fragment for NEW notes before initial claim-map/binding freeze."""
    rows = add_novelty_to_claims(claims, assessment, run_id)
    output = [r"\begin{tabular}{p{.36\linewidth}p{.25\linewidth}p{.25\linewidth}}",
              r"Claim / theorem & Evidence class & Run-target novelty \\ \hline"]
    for row in rows:
        output.append(" & ".join(tex_escape(value) for value in [
            row.get("lean_theorem", row.get("id", "unspecified")),
            row.get("evidence_class", "UNASSESSED"), row["novelty_status"]]) + r" \\")
    output.extend([r"\end{tabular}", r"\par Run-target novelty assesses the overall proposed target, not each auxiliary theorem. It is advisory literature assessment, not certificate evidence.",
                   "logical validity given the model, not empirical validation of its assumptions"])
    if isinstance(assessment, dict):
        output.append(r"\par Assessment: \texttt{NOVELTY\_ASSESSMENT.json}; target SHA-256: \texttt{" + tex_escape(assessment.get("target_sha256", "UNRECORDED"))
                      + r"}; search-evidence SHA-256: \texttt{" + tex_escape(assessment.get("search_evidence_sha256", "UNRECORDED")) + "}.")
    return "\n".join(output) + "\n"


def ratio(numerator: int, denominator: int) -> dict:
    return {"numerator": numerator, "denominator": denominator,
            "share": numerator / denominator if denominator else None}


def classify_run_depth(labels: list[str]) -> str:
    """Substantive needs at least one explicit label, never certificate inference."""
    if "SUBSTANTIVE" in labels:
        return "SUBSTANTIVE"
    if not labels or any(label not in ASSESSED_DEPTH for label in labels):
        return "UNASSESSED"
    return "ROUTINE" if "ROUTINE" in labels else "DEFINITIONAL"


def summarize_week(records: list, week: str, phase8_start: datetime | None = None) -> dict:
    """One generation attempt per run ID; replayed certifications/digests do not add runs."""
    year, number = map(int, week.split("-W"))
    monday = date.fromisocalendar(year, number, 1)
    end = monday + timedelta(days=7)
    by_run, conflicts, undated = {}, [], []
    for record in records:
        if not isinstance(record, dict):
            continue
        run_id = record.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            continue
        attempt = iso_datetime(record.get("generated_at_utc"))
        if attempt is None:
            undated.append(run_id)
            continue
        if run_id in by_run and by_run[run_id] != record:
            conflicts.append(run_id)
            continue
        by_run[run_id] = record
    cohort = []
    for run_id, record in sorted(by_run.items()):
        day = iso_datetime(record["generated_at_utc"]).astimezone(TIMEZONE).date()
        if monday <= day < end:
            row = copy.deepcopy(record)
            row["generated_date_new_york"] = day.isoformat()
            row["phase8_cohort"] = phase8_start is not None and iso_datetime(record["generated_at_utc"]) >= phase8_start
            if run_id in conflicts:
                row["novelty_status"] = "UNASSESSED"
                row["semantic_tier"] = "UNASSESSED"
                row["portfolio_item_id"] = None
                row["status"] = "UNKNOWN_CONFLICTING_INPUTS"
            cohort.append(row)
    depth = Counter(row.get("semantic_tier", "UNASSESSED") for row in cohort)
    novelty = Counter(row.get("novelty_status", "UNASSESSED") for row in cohort)
    status = Counter(row.get("status", "UNKNOWN_LEDGER_STATUS") for row in cohort)
    substantive = depth["SUBSTANTIVE"]
    certified_cohort = [row for row in cohort if row.get("status") == "CERTIFIED"]
    certified_substantive = sum(row.get("semantic_tier") == "SUBSTANTIVE" for row in certified_cohort)
    certified_depth_assessed = sum(row.get("semantic_tier") in ASSESSED_DEPTH for row in certified_cohort)
    assessed_depth = sum(depth[key] for key in ASSESSED_DEPTH)
    assessed_novelty = sum(value for key, value in novelty.items() if key != "UNASSESSED")
    selection_recorded = [row for row in cohort if row.get("selection_recorded") is True]
    portfolio_hits = sum(bool(PORTFOLIO_ID.fullmatch(row.get("portfolio_item_id") or ""))
                         for row in selection_recorded)
    outcomes = []
    for row in cohort:
        for outcome in row.get("portfolio_outcomes", []):
            if (isinstance(outcome, dict) and outcome.get("disposition") in {"STRENGTHENED", "DISCHARGED"}
                    and PORTFOLIO_ID.fullmatch(outcome.get("portfolio_item_id") or "")
                    and outcome.get("evidence_path") and outcome.get("evidence_current") is True
                    and outcome.get("reviewed") is True and outcome.get("review_reason")):
                outcomes.append({"run_id": row["run_id"], **outcome})
    phase8_cohort = [row for row in cohort if row["phase8_cohort"]]
    return {
        "schema_version": "VRS-PHASE8-QUALITY-1", "advisory_only": True,
        "certifies": False, "week": week, "timezone": str(TIMEZONE),
        "attempt_definition": "Unique run with actual timezone-aware RUN_MANIFEST.generated_at_utc in this week.",
        "certificate_definition": "Current SSOT RUN status CERTIFIED, not certificate issue events or public DOI count.",
        "runs_attempted": len(cohort), "certified": status["CERTIFIED"],
        "current_ledger_status_counts": dict(status),
        "substantive_run_share_assessed": ratio(substantive, assessed_depth),
        "depth_assessment_coverage": ratio(assessed_depth, len(cohort)),
        "substantive_all_attempts_evidenced_lower_bound": ratio(substantive, len(cohort)),
        "substantive_certified_run_share_evidenced_lower_bound": ratio(certified_substantive, len(certified_cohort)),
        "certified_run_depth_assessment_coverage": ratio(certified_depth_assessed, len(certified_cohort)),
        "likely_new_run_share_assessed": ratio(novelty["LIKELY_NEW"], assessed_novelty),
        "novelty_assessment_coverage": ratio(assessed_novelty, len(cohort)),
        "likely_new_all_attempts_evidenced_lower_bound": ratio(novelty["LIKELY_NEW"], len(cohort)),
        "portfolio_hit_rate_recorded_selections": ratio(portfolio_hits, len(selection_recorded)),
        "portfolio_all_attempts_evidenced_lower_bound": ratio(portfolio_hits, len(cohort)),
        "target_selection_coverage": ratio(len(selection_recorded), len(cohort)),
        "semantic_tier_counts": dict(depth), "novelty_status_counts": dict(novelty),
        "portfolio_items_strengthened_or_discharged": outcomes,
        "phase8_start": phase8_start.isoformat() if phase8_start else None, "phase8_runs_this_week": len(phase8_cohort),
        "phase8_run_ids_this_week": [row["run_id"] for row in phase8_cohort],
        "conflicting_run_inputs": sorted(set(conflicts)), "undated_runs_excluded": sorted(set(undated)),
        "runs": cohort,
    }


def trend_summary(weekly: list, phase8_start: datetime | None = None) -> dict:
    """Four-week advisory progress from Phase8 cohort only, without a gate verdict."""
    rows, seen = [], set()
    for week in sorted(weekly, key=lambda row: row.get("week", "")):
        for run in week.get("runs", []):
            if run.get("phase8_cohort") and run.get("run_id") not in seen:
                seen.add(run["run_id"])
                rows.append(run)
    denominator = len(rows)
    certified = [row for row in rows if row.get("status") == "CERTIFIED"]
    substantive = sum(row.get("semantic_tier") == "SUBSTANTIVE" for row in certified)
    likely = sum(row.get("novelty_status") == "LIKELY_NEW" for row in rows)
    return {"advisory_only": True, "changes_gate_verdict": False,
            "phase8_start": phase8_start.isoformat() if phase8_start else None,
            "four_week_review_date": (phase8_start + timedelta(days=28)).isoformat() if phase8_start else None,
            "targets": {"substantive": 0.60, "likely_new": 0.50},
            "phase8_runs_attempted": denominator,
            "substantive_evidenced_share_of_certified_runs": ratio(substantive, len(certified)),
            "likely_new_evidenced_share_of_attempts": ratio(likely, denominator),
            "interpretation": "SUBSTANTIVE uses all certified runs; LIKELY_NEW uses all attempted runs. Unknowns are not classified as routine/known. Missing cohorts yield null shares; targets never gate."}


def collect_tree(tree_root: Path, phase8_root: Path) -> tuple[list, dict, list]:
    """Read original ledger/manifests and advisory files; no verification or publication call."""
    bindings, gaps = {}, []
    ledger = json_read(tree_root / "RESEARCH_PIPELINE_v2/corpus_ledger.json", bindings, gaps) or {}
    statuses, exported_theorems = {}, {}
    for row in ledger.get("run_entities", []):
        if isinstance(row, dict) and row.get("entity_type") == "RUN":
            statuses[row.get("id", row.get("run_id"))] = row.get("status", "UNKNOWN_LEDGER_STATUS")
            exported_theorems[row.get("id", row.get("run_id"))] = set(row.get("certified_theorems", []))
    approved_note_paths = set()
    for row in ledger.get("publication_entities", []):
        if isinstance(row, dict) and row.get("kind") == "METHODS_NOTE" and row.get("path"):
            approved_note_paths.add(str((tree_root / row["path"]).resolve()))
    # Older ledger kind is METHODS_NOTE_PUBLICATION; select only an explicit note id.
    for row in ledger.get("publication_entities", []):
        if isinstance(row, dict) and str(row.get("id", "")).startswith("publication:methods-note:") and row.get("path"):
            approved_note_paths.add(str((tree_root / row["path"]).resolve()))
    depth_evidence = defaultdict(lambda: defaultdict(set))
    digest_root = tree_root / "RESEARCH_PIPELINE_v2/science_release_queue/digests"
    for path in sorted(digest_root.glob("*/DIGEST_MANIFEST.json")):
        digest = json_read(path, bindings, gaps) or {}
        for note in digest.get("notes", []):
            if not isinstance(note, dict) or str(Path(note.get("path", "")).resolve()) not in approved_note_paths:
                continue
            run_id = note.get("run_id")
            if note.get("section") != "MAIN_NOTES":
                continue
            for claim in note.get("claim_table", []):
                if (isinstance(claim, dict) and claim.get("headline_eligible") is True
                        and claim.get("lean_theorem") in exported_theorems.get(run_id, set())):
                    depth_evidence[run_id][claim["lean_theorem"]].add(claim.get("semantic_tier", "UNASSESSED"))
    records = []
    root = tree_root / "science-engine/07_nightly_engine/compound research papers"
    for manifest in sorted(root.glob("Run-*/RUN_MANIFEST.json")):
        run = json_read(manifest, bindings, gaps)
        if not run:
            continue
        run_id = run.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID.fullmatch(run_id):
            gaps.append({"path": str(manifest), "reason": "Missing or invalid run_id"})
            continue
        assessment, selection, outcomes = None, None, []
        for dirname in [manifest.parent, phase8_root / "runs" / run_id, phase8_root / "assessments" / run_id]:
            path = dirname / "NOVELTY_ASSESSMENT.json"
            if path.exists():
                assessment = json_read(path, bindings, gaps)
            path = dirname / "TARGET_SELECTION.json"
            if path.exists():
                selection = json_read(path, bindings, gaps)
            path = dirname / "PORTFOLIO_OUTCOMES.json"
            if path.exists():
                outcome_data = json_read(path, bindings, gaps) or {}
                if outcome_data.get("run_id") == run_id:
                    outcomes = outcome_data.get("outcomes", [])
                    outcomes = [row for row in outcomes if isinstance(row, dict)]
                    for row in outcomes:
                        evidence = Path(row.get("evidence_path", ""))
                        if not evidence.is_absolute():
                            evidence = tree_root / evidence
                        try:
                            observed = hashlib.sha256(evidence.read_bytes()).hexdigest()
                            bindings[str(evidence)] = observed
                            row["evidence_current"] = observed == row.get("evidence_sha256")
                        except OSError:
                            row["evidence_current"] = False
            path = dirname / "QUALITY_LABELS.json"
            if path.exists():
                quality = json_read(path, bindings, gaps) or {}
                if quality.get("run_id") == run_id:
                    for claim in quality.get("claims", []):
                        if (isinstance(claim, dict) and claim.get("headline_eligible") is True
                                and claim.get("lean_theorem") in exported_theorems.get(run_id, set())):
                            depth_evidence[run_id][claim["lean_theorem"]].add(claim.get("semantic_tier", "UNASSESSED"))
        labels, claim_counts = [], Counter()
        for theorem, tiers in depth_evidence.get(run_id, {}).items():
            tier = next(iter(tiers)) if len(tiers) == 1 else "UNASSESSED"
            labels.append(tier)
            claim_counts[tier] += 1
            if len(tiers) > 1:
                gaps.append({"run_id": run_id, "theorem": theorem, "reason": "Conflicting published/advisory depth labels; not resolved as substantive."})
        valid_selection = isinstance(selection, dict) and selection.get("run_id") == run_id
        item = selection.get("portfolio_item_id") if valid_selection else None
        if not isinstance(item, str) or not PORTFOLIO_ID.fullmatch(item):
            item = None
        records.append({"run_id": run_id, "generated_at_utc": run.get("generated_at_utc"),
                        "title": run.get("title"), "status": statuses.get(run_id, "UNKNOWN_LEDGER_STATUS"),
                        "semantic_tier": classify_run_depth(labels), "headline_claim_tier_counts": dict(claim_counts),
                        "novelty_status": strict_novelty(assessment, run_id, iso_datetime(run.get("generated_at_utc"))),
                        "selection_recorded": valid_selection, "portfolio_item_id": item,
                        "value_rationale": selection.get("value_rationale") if valid_selection else None,
                        "portfolio_outcomes": outcomes, "manifest_path": str(manifest)})
    return records, bindings, gaps


def render_weekly(report: dict) -> str:
    def display(value):
        if value["share"] is None:
            return f"UNASSESSED ({value['numerator']}/{value['denominator']})"
        return f"{value['share']:.1%} ({value['numerator']}/{value['denominator']})"
    rows = [f"Weekly quality ledger — {report['week']}", "",
            "Advisory only. Certification correctness, novelty and importance are separate.", "",
            "| Metric | Evidence |", "|---|---|",
            f"| Runs attempted (dated generation cohort) | {report['runs_attempted']} |",
            f"| Currently CERTIFIED in SSOT | {report['certified']} |"]
    for label, key in [("SUBSTANTIVE share among depth-assessed runs", "substantive_run_share_assessed"),
                       ("Depth assessment coverage", "depth_assessment_coverage"),
                       ("SUBSTANTIVE evidenced lower bound across attempts", "substantive_all_attempts_evidenced_lower_bound"),
                       ("SUBSTANTIVE target metric: lower bound across all certified runs", "substantive_certified_run_share_evidenced_lower_bound"),
                       ("Certified-run depth assessment coverage", "certified_run_depth_assessment_coverage"),
                       ("LIKELY_NEW share among novelty-assessed runs", "likely_new_run_share_assessed"),
                       ("Novelty assessment coverage", "novelty_assessment_coverage"),
                       ("LIKELY_NEW evidenced lower bound across attempts", "likely_new_all_attempts_evidenced_lower_bound"),
                       ("Portfolio hit rate among recorded selections", "portfolio_hit_rate_recorded_selections"),
                       ("Portfolio hit rate lower bound across attempts", "portfolio_all_attempts_evidenced_lower_bound"),
                       ("Selection coverage", "target_selection_coverage")]:
        rows.append(f"| {label} | {display(report[key])} |")
    rows += ["", f"Current ledger statuses: {json.dumps(report['current_ledger_status_counts'], sort_keys=True)}.",
             f"Phase 8 activation: {report['phase8_start'] or 'not supplied; no run credited'}; {report['phase8_runs_this_week']} run(s) in this week are in the Phase 8 cohort.",
             "", "Missing novelty/depth labels remain UNASSESSED. A lower bound of 0 is no demonstrated success, not proof of knownness or routine depth.",
             "", "| Run | Current SSOT status | Depth | Novelty | Portfolio |", "|---|---|---|---|---|"]
    for row in report["runs"]:
        rows.append("| " + " | ".join(md_cell(row.get(key) or "UNRECORDED") for key in
                    ["run_id", "status", "semantic_tier", "novelty_status", "portfolio_item_id"]) + " |")
    rows += ["", "Portfolio outcomes: " + (json.dumps(report["portfolio_items_strengthened_or_discharged"], ensure_ascii=False)
                                          if report["portfolio_items_strengthened_or_discharged"] else "No documented strengthened/discharged item in this cohort."),
             "", "Targets are SUBSTANTIVE ≥60% of all certified runs and LIKELY_NEW ≥50% of all attempted runs by the four-week review. Tiny assessed denominators cannot meet these targets. They never block certification or publication."]
    trend = report.get("trend")
    if isinstance(trend, dict):
        rows += ["", f"Phase 8 cumulative trend: {trend['phase8_runs_attempted']} attempted run(s). "
                 f"SUBSTANTIVE across certified runs: {display(trend['substantive_evidenced_share_of_certified_runs'])}; "
                 f"LIKELY_NEW across attempts: {display(trend['likely_new_evidenced_share_of_attempts'])}. "
                 f"Four-week review: {trend['four_week_review_date'] or 'activation not supplied'}. "
                 "Pre-rollout runs receive no Phase 8 target credit."]
    return "\n".join(rows) + "\n"


def _main(argv=None) -> int:
    import sys
    supplied = list(sys.argv[1:] if argv is None else argv)
    if supplied and supplied[0] in {"render-note", "render-digest"}:
        return render_main(supplied)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree-root", type=Path, required=True)
    parser.add_argument("--phase8-root", type=Path, required=True)
    parser.add_argument("--week", required=True, help="ISO week YYYY-Www in America/New_York")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--phase8-start", help="Exact timezone-aware activation time; omit to exclude pre-rollout cohorts.")
    args = parser.parse_args(argv)
    records, bindings, gaps = collect_tree(args.tree_root, args.phase8_root)
    phase8_start = iso_datetime(args.phase8_start)
    if args.phase8_start and phase8_start is None:
        parser.error("--phase8-start requires a timezone-aware ISO datetime")
    report = summarize_week(records, args.week, phase8_start)
    report["input_bindings"] = bindings
    report["input_coverage_gaps"] = gaps
    report["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    historical = []
    for prior in sorted((args.phase8_root / "weekly").glob("*/WEEKLY_QUALITY_METRICS.json")):
        old = json_read(prior, bindings, gaps)
        if old and old.get("schema_version") == "VRS-PHASE8-QUALITY-1" and old.get("week") != args.week:
            historical.append(old)
    report["trend"] = trend_summary(historical + [report], phase8_start)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "WEEKLY_QUALITY_METRICS.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (args.output_dir / "WEEKLY_QUALITY_LEDGER.md").write_text(render_weekly(report))
    print(json.dumps({"advisory_only": True, "certifies": False, "week": args.week,
                      "runs_attempted": report["runs_attempted"], "certified": report["certified"],
                      "input_coverage_gaps": len(gaps)}))
    return 0


def main(argv=None) -> int:
    """Advisory failures never become verification/publication failures."""
    try:
        return _main(argv)
    except Exception as exc:
        print(json.dumps({"advisory_only": True, "certifies": False,
                          "status": "ADVISORY_UNAVAILABLE", "error": f"{type(exc).__name__}: {exc}",
                          "action": "Preserve UNASSESSED labels and continue the unchanged pipeline."}))
        return 0


def write_authoring_fragment(path: Path, value: str) -> None:
    """Only create a new fragment or confirm identical bytes; never silently revise a frozen one."""
    if path.exists():
        if path.read_text() != value:
            raise ValueError("Refusing to replace a different existing authoring fragment; use a new pre-binding draft path.")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)


def render_main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Create advisory future-note/digest authoring fragments; never changes original maps or metadata.")
    parser.add_argument("mode", choices=["render-note", "render-digest"])
    parser.add_argument("--input", type=Path, required=True, help="Existing claim-map JSON (claims array) or digest JSON (notes array).")
    parser.add_argument("--run-id", help="Run ID for note authoring")
    parser.add_argument("--assessment", type=Path, help="Run NOVELTY_ASSESSMENT.json, optional; missing gives UNASSESSED")
    parser.add_argument("--phase8-root", type=Path, help="For digest, read runs/Run-NNN/NOVELTY_ASSESSMENT.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tex-output", type=Path, help="NEW note-authoring TeX fragment before initial binding")
    args = parser.parse_args(argv)
    bindings, gaps = {}, []
    source = json_read(args.input, bindings, gaps) or {}
    assessment = json_read(args.assessment, bindings, gaps) if args.assessment else None
    if args.mode == "render-note":
        if not args.run_id or not RUN_ID.fullmatch(args.run_id):
            parser.error("render-note requires a valid --run-id")
        claims = source.get("claims", [])
        write_authoring_fragment(args.output, render_claim_table(claims, assessment, args.run_id))
        if args.tex_output:
            write_authoring_fragment(args.tex_output, render_claim_table_tex(claims, assessment, args.run_id))
    else:
        assessments = {}
        notes = source.get("notes", [])
        if args.phase8_root:
            for note in notes:
                run_id = note.get("run_id") if isinstance(note, dict) else None
                if isinstance(run_id, str) and RUN_ID.fullmatch(run_id):
                    path = args.phase8_root / "runs" / run_id / "NOVELTY_ASSESSMENT.json"
                    if path.exists():
                        assessments[run_id] = json_read(path, bindings, gaps)
        write_authoring_fragment(args.output, render_digest_table(notes, assessments))
    print(json.dumps({"advisory_only": True, "certifies": False, "input_coverage_gaps": len(gaps), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
