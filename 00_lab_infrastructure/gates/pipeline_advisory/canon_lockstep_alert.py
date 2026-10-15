#!/usr/bin/env python3
"""Report Canon DOI/tag/release gaps from supplied receipts, without API calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.parse import quote

SHA = re.compile(r"[a-f0-9]{64}")
COMMIT = re.compile(r"[a-f0-9]{40}")


def inspect_lockstep(snapshot: dict) -> dict:
    changes = snapshot.get("canon_changes")
    releases = snapshot.get("git_releases")
    result = {"schema": "VRS-CANON-LOCKSTEP-ALERT-1", "certifies": False,
              "external_mutations": 0, "scope": "SUPPLIED_RECEIPTS_ONLY_NO_LIVE_VERIFICATION",
              "status": "UNAVAILABLE", "checks": []}
    if not isinstance(changes, list) or not isinstance(releases, list):
        result["reason"] = "explicit Canon-change and Git-release snapshots required"
        return result
    if not changes:
        result["status"] = "NO_CHANGES_IN_SUPPLIED_SCOPE"
        return result
    seen = set()
    for change in changes:
        record_id = change.get("record_id")
        doi = change.get("doi")
        receipt = change.get("source_receipt_sha256")
        if not isinstance(record_id, str) or re.fullmatch(r"[1-9][0-9]*", record_id) is None or doi != "10.5281/zenodo." + record_id:
            raise ValueError("exact Canon record DOI required")
        if not isinstance(receipt, str) or SHA.fullmatch(receipt) is None:
            raise ValueError("hash-bound Zenodo-change receipt required")
        identity = (record_id, receipt)
        if identity in seen:
            raise ValueError("duplicate Canon change receipt")
        seen.add(identity)
        matches = [row for row in releases if row.get("record_id") == record_id and row.get("doi") == doi
                   and row.get("source_receipt_sha256") == receipt]
        row = {"record_id": record_id, "doi": doi, "source_receipt_sha256": receipt,
               "status": "ALERT_MISSING_MATCHING_TAG_AND_RELEASE"}
        if len(matches) > 1:
            row["status"] = "HOLD_AMBIGUOUS_RELEASE_MAPPING"
        elif len(matches) == 1:
            link = matches[0]
            tag = link.get("tag")
            release_url = "https://github.com/jdhart81/viridis-canon/releases/tag/" + quote(tag, safe="") if isinstance(tag, str) and tag else None
            if (link.get("annotated_tag") is True and release_url is not None and link.get("release_url") == release_url
                    and isinstance(link.get("commit_sha"), str) and COMMIT.fullmatch(link["commit_sha"]) is not None
                    and isinstance(link.get("tag_object_sha"), str) and COMMIT.fullmatch(link["tag_object_sha"]) is not None):
                row.update(status="MATCHED_SUPPLIED_TAG_AND_RELEASE", tag=tag, release_url=release_url,
                           commit_sha=link["commit_sha"], tag_object_sha=link["tag_object_sha"])
            else:
                row["status"] = "ALERT_INCOMPLETE_ANNOTATED_TAG_OR_RELEASE_EVIDENCE"
        result["checks"].append(row)
    result["status"] = "MATCHED_SUPPLIED_SCOPE" if all(row["status"] == "MATCHED_SUPPLIED_TAG_AND_RELEASE" for row in result["checks"]) else "ALERT_CANON_LOCKSTEP_GAP"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = inspect_lockstep(json.loads(args.snapshot.read_text()))
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"status": report["status"], "external_mutations": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
