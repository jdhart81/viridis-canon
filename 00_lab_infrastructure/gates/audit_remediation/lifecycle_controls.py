"""Exercise F1 in finite disposable processes before any candidate materialization."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from run_pure_checks import identity_probe, runtime_environment, sha, write_json


CASES = ("normal", "timeout", "wait_baseexception", "term", "int", "spawn_interruption", "whole_expiry",
         "worker_watchdog", "normal_linger", "constructor_unknown", "group_unknown", "quiet_unknown")


def run_controls(processes, repo: Path, output: Path) -> dict:
    output.mkdir(exist_ok=False)
    helper = Path(__file__).resolve().with_name("lifecycle_fixture.py")
    result = {"status": "HOLD", "controls_sha256": sha(Path(__file__).resolve()),
              "fixture_sha256": sha(helper), "original_whole_deadline": processes.deadline, "cases": []}
    try:
        for case in CASES:
            processes.checkpoint()
            directory = output / case
            directory.mkdir()
            argv = [sys.executable, "-B", str(helper), "--probe", case,
                    "--output", str(directory / "probe"), "--whole-deadline", str(processes.deadline)]
            lifecycle = processes.execute(argv, cwd=repo, environment=runtime_environment(None, directory),
                                          output=directory, child_seconds=8.0)
            row = {"case": case, "lifecycle": lifecycle, "status": "HOLD", "actual_quiet_probes": []}
            result["cases"].append(row)
            assert lifecycle["status"] == "OWNED_PROCESS_COMPLETE" and lifecycle["returncode"] == 0
            control = json.loads((directory / "probe/CONTROL_RESULT.json").read_bytes())
            row["control"] = control
            assert control["case"] == case and control["status"] == "DISPOSABLE_LIFECYCLE_CONTROL_PASS"
            # Never accept a self-reported cleanup receipt as a quiet proof.
            # Independently probe every actual child/group identity recorded by
            # the finite helper plus the parent's exact returned Popen owner.
            identities = [{"pid": lifecycle["pid"], "pgid": lifecycle["pgid"]}]
            owned = control["owned_record"]
            if "pid" in owned:
                identities.append({"pid": owned["pid"], "pgid": owned["pid"]})
            for name in ("leaf.json", "descendant.json"):
                path = directory / "probe" / name
                if path.exists():
                    identities.append(json.loads(path.read_bytes()))
            for identity in identities:
                proof = {"identity": identity, "pid": identity_probe(identity["pid"], group=False),
                         "group": identity_probe(identity["pgid"], group=True)}
                row["actual_quiet_probes"].append(proof)
                assert proof["pid"]["state"] == proof["group"]["state"] == "ABSENT"
            assert not (directory / "probe/NEXT_SCOPE_WAS_ADMITTED").exists()
            if case != "normal":
                assert control["next_scope_blocked"]
            row["status"] = "DISPOSABLE_LIFECYCLE_CONTROL_PASS"
        result["status"] = "ALL_DISPOSABLE_LIFECYCLE_CONTROLS_PASS"
        return result
    except BaseException as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        raise
    finally:
        write_json(output / "RESULT.json", result)
