#!/usr/bin/env python3
"""Collect supplied snapshots only; never run checkpoints, publish, or certify."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
from zoneinfo import ZoneInfo

PHASE_LIMIT = 50 * 1024 * 1024
DAY_LIMIT = 200 * 1024 * 1024


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return parsed.astimezone(timezone.utc)


def unavailable(reason: str) -> dict:
    return {"status": "UNAVAILABLE", "reason": reason}


def coverage(supplied: dict | None, as_of: datetime | None = None) -> dict:
    if not supplied or supplied.get("status") != "KNOWN":
        return {**unavailable("no complete supplied coverage adjudication"), "covered": None,
                "total": None, "ratio": None}
    covered, total = supplied.get("covered"), supplied.get("total")
    if any(type(value) is not int for value in (covered, total)) or not 0 <= covered <= total:
        raise ValueError("invalid coverage counts")
    if not supplied.get("observed_at_utc") or not supplied.get("source_receipt"):
        raise ValueError("coverage counts require observation time and source receipt")
    observed = timestamp(supplied["observed_at_utc"])
    if as_of is not None and observed > as_of:
        raise ValueError("coverage observation is later than as-of time")
    return {"status": "KNOWN", "covered": covered, "total": total,
            "ratio": covered / total if total else None,
            "empty_inventory": total == 0, "source_receipt": supplied["source_receipt"],
            "observed_at_utc": supplied["observed_at_utc"]}


def scoped_footprint(supplied: dict | None, evidence_root: Path | None) -> dict:
    if supplied is None or "files" not in supplied or evidence_root is None:
        return {**unavailable("explicit file list and evidence root required"), "bytes": None,
                "phase_limit_bytes": PHASE_LIMIT, "day_limit_bytes": DAY_LIMIT}
    root = evidence_root.resolve(strict=True)
    paths = supplied["files"]
    if not isinstance(paths, list) or len(paths) > 1000:
        raise ValueError("bounded explicit evidence file list required")
    seen = set()
    size = 0
    for relative in paths:
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("evidence file must be relative to evidence root")
        path = root / rel
        if path in seen:
            raise ValueError("duplicate evidence file")
        seen.add(path)
        # Refuse symlink components before resolving, including directory links.
        current = root
        for component in rel.parts:
            current /= component
            if current.is_symlink():
                raise ValueError("symlink evidence input refused")
        if not path.resolve(strict=True).is_relative_to(root):
            raise ValueError("evidence file escapes scoped root")
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError("regular evidence file required")
        size += metadata.st_size
    day_before = supplied.get("day_bytes_before_phase")
    if day_before is not None and (type(day_before) is not int or day_before < 0):
        raise ValueError("invalid prior day evidence footprint")
    day_total = day_before + size if day_before is not None else None
    return {"status": "HOLD_BUDGET_EXCEEDED" if size > PHASE_LIMIT or (day_total is not None and day_total > DAY_LIMIT) else "KNOWN_SCOPED",
            "bytes": size, "file_count": len(seen), "scope": "supplied_files_only_no_tree_scan",
            "day_bytes": day_total, "day_status": "KNOWN" if day_total is not None else "UNAVAILABLE",
            "phase_limit_bytes": PHASE_LIMIT, "day_limit_bytes": DAY_LIMIT}


def collect(observer: dict, snapshot: dict, as_of: str, evidence_root: Path | None = None) -> dict:
    now = timestamp(as_of)
    observed_raw = observer.get("observed_at_utc")
    observed = timestamp(observed_raw) if observed_raw else None
    if observed and observed > now:
        raise ValueError("observer timestamp is later than as-of time")
    science = observer.get("science", {})
    generation = science.get("generation", {})
    generated_raw = generation.get("generated_at_utc")
    if generated_raw:
        generated = timestamp(generated_raw)
        if generated > now:
            raise ValueError("generation timestamp is later than as-of time")
        age = (now - generated).total_seconds() / 3600
        generation_status = {"status": "FRESH" if age <= 36 else "OVERDUE", "age_hours": round(age, 3),
                             "slo_hours": 36, "latest_run": generation.get("latest_run"),
                             "source_due": generation.get("window", {}).get("generation_due"),
                             "window_authority": "SUPPLIED_SNAPSHOT_ONLY_NO_DUE_DECISION"}
    else:
        generation_status = {**unavailable("generation timestamp missing"), "age_hours": None}
    certification = science.get("certification", {})
    age_observed = certification.get("age_hours")
    if observed and type(age_observed) in (int, float) and age_observed >= 0:
        age = age_observed + (now - observed).total_seconds() / 3600
        certification_status = {"status": "WITHIN_SLO" if age <= 36 else "OVERDUE",
                                "age_hours": round(age, 3), "slo_hours": 36,
                                "backlog_runs": certification.get("backlog_runs"),
                                "age_basis": "observer_age_plus_elapsed_not_certificate_validation"}
    else:
        certification_status = {**unavailable("certification age or observation time missing"), "age_hours": None}
    head = snapshot.get("fifo_head")
    if head and head.get("held_since_utc"):
        held = timestamp(head["held_since_utc"])
        if held > now:
            raise ValueError("FIFO held-since is later than as-of time")
        age = (now - held).total_seconds() / 3600
        fifo = {"status": "ALERT" if age > 24 else "BELOW_ALERT_THRESHOLD", "run_id": head.get("run_id"),
                "held_hours": round(age, 3), "alert_threshold_hours": 24,
                "failing_goal": head.get("failing_goal"),
                "failing_goal_status": "KNOWN" if head.get("failing_goal") else "UNAVAILABLE",
                "activation": "REPORT_ONLY_NO_TRANSPORT_OR_FIFO_CHANGE"}
    else:
        fifo = {**unavailable("authenticated FIFO held-since snapshot missing"), "held_hours": None,
                "failing_goal": head.get("failing_goal") if head else None}
    weekly = snapshot.get("weekly_digest")
    if not weekly or not weekly.get("status") or not weekly.get("iso_week") or not weekly.get("source_receipt"):
        weekly = unavailable("weekly digest receipt missing")
    else:
        weekly = dict(weekly)
        year, week, _ = now.astimezone(ZoneInfo("America/New_York")).isocalendar()
        current_week = f"{year}-W{week:02}"
        if weekly["iso_week"] != current_week:
            weekly.update(status="HOLD_WRONG_ISO_WEEK", source_iso_week=weekly["iso_week"],
                          iso_week=current_week, reason="supplied digest does not cover the current New York ISO week")
    leak = snapshot.get("leak_scan")
    if not leak or leak.get("status") != "KNOWN":
        leak = {**unavailable("scoped leak-scan receipt missing"), "hits": None}
    else:
        if type(leak.get("hits")) is not int or leak["hits"] < 0 or not leak.get("source_receipt") or not leak.get("scope"):
            raise ValueError("leak result requires count, receipt and scope")
        leak = {**leak, "status": "PASS_SCOPED" if leak["hits"] == 0 else "HOLD_TOKEN_HITS"}
    return {"schema": "VRS-PIPELINE-SLO-STATUS-1", "as_of_utc": as_of,
            "status": "ADVISORY_SNAPSHOT_NOT_PIPELINE_CERTIFICATION", "activation": "PREPARED_NOT_SCHEDULED",
            "source_observed_at_utc": observed_raw, "generation_freshness": generation_status,
            "certification_age": certification_status, "fifo_liveness": fifo, "weekly_digest": weekly,
            "pdf_coverage": coverage(snapshot.get("pdf_coverage"), now),
            "banner_coverage": coverage(snapshot.get("banner_coverage"), now), "leak_scan": leak,
            "new_evidence_footprint": scoped_footprint(snapshot.get("new_evidence"), evidence_root),
            "certifies": False, "external_mutations": 0}


def weekly_summary(report: dict) -> str:
    """Exactly ten lines, ready for a later approved Monday snapshot hook."""
    def state(key): return report[key]["status"]
    def age(key):
        value = report[key].get("age_hours")
        return "unavailable" if value is None else f"{value:.1f} h"
    goal = " ".join((report["fifo_liveness"].get("failing_goal") or "unavailable").split())
    return "\n".join([
        f"Viridis weekly snapshot: {report['as_of_utc']}",
        f"Generation: {state('generation_freshness')}; age {age('generation_freshness')}",
        f"Certification: {state('certification_age')}; age {age('certification_age')}",
        f"FIFO: {state('fifo_liveness')}; goal {goal}",
        f"Methods Digest ({report['weekly_digest'].get('iso_week', 'unavailable')}): {state('weekly_digest')}",
        f"PDF coverage: {state('pdf_coverage')}",
        f"UNCERTIFIED banner coverage: {state('banner_coverage')}",
        f"Token scan: {state('leak_scan')}",
        f"New evidence: {state('new_evidence_footprint')}",
        "Snapshot advisory only; no new certificate, publication, deployment or adoption claim.",
    ]) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observer", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--weekly-summary", type=Path)
    args = parser.parse_args(argv)
    observer_bytes, snapshot_bytes = args.observer.read_bytes(), args.snapshot.read_bytes()
    report = collect(json.loads(observer_bytes), json.loads(snapshot_bytes), args.as_of, args.evidence_root)
    report["input_sha256"] = {"observer": hashlib.sha256(observer_bytes).hexdigest(),
                              "snapshot": hashlib.sha256(snapshot_bytes).hexdigest()}
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True); stream.write("\n")
    if args.weekly_summary:
        with args.weekly_summary.open("x") as stream: stream.write(weekly_summary(report))
    print(json.dumps({"status": report["status"], "certifies": False, "external_mutations": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
