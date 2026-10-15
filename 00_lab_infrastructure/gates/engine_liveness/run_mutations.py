"""Bounded behavioral mutation checks for the uninstalled liveness helper."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "scheduler_liveness.py").read_text()
MUTANTS = [
    ("third_request_allowed", "if len(active) >= 2:", "if len(active) >= 3:"),
    ("ambiguous_request_redispatched", 'return {"dispatch": False, "request": row}', 'return {"dispatch": True, "request": row}'),
    ("owner_not_required", "if not self._owned:", "if False:"),
    ("concurrent_owner_allowed", "fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)", "pass"),
    ("candidate_drift_reused", 'if row["identity"] != asdict(identity):', "if False:"),
    ("receipt_identity_ignored", 'if request.get("identity") != asdict(identity) or result.get("identity") != asdict(identity):', "if False:"),
    ("kernel_gates_ignored", 'if any(result.get(name) is not True for name in (', 'if False and any(result.get(name) is not True for name in ('),
    ("issuer_validation_ignored", "if validate_certificate(identity, result) is not True:", "if False:"),
    ("release_gap_skipped", 'if identity.key not in completed or identity.key not in admitted:\n                break', 'if identity.key not in completed or identity.key not in admitted:\n                continue'),
    ("release_admission_ignored", 'if identity.key not in completed or identity.key not in admitted:', 'if identity.key not in completed:'),
    ("younger_grants_oldest_credit", 'return [run for run in targets if run in certified_runs]', 'return list(certified_runs)'),
    ("terminal_hold_dispatched", '            if terminal_hold:\n                continue', '            if False:\n                continue'),
    ("immutable_collision_ignored", 'if path.read_bytes() != encoded:', 'if False:'),
    ("rejected_request_can_accept", 'if any(row["identity"] == asdict(identity) for row in self._rows("terminal")):', 'if False:'),
    ("request_digest_reused", 'if row["identity"]["request_sha256"] == identity.request_sha256:', 'if False:'),
    ("result_symlink_accepted", 'if path.is_symlink() or path.parent.is_symlink():', 'if False:'),
    ("stdout_prose_copied", 'return match.group(1) if match else "UNAVAILABLE"', 'return error if match else "UNAVAILABLE"'),
    ("review_contradiction_ignored", 'return bool(re.search(', 'return False and bool(re.search('),
    ("source_escape_ignored", 'raise LivenessHold("HOLD_PAPER_SOURCE_ESCAPE") from exc', 'return False'),
    ("due_generation_skipped", 'generation = generation_step() if generation_due else None', 'generation = None'),
]


def run():
    report = []
    baseline = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(HERE / "tests")],
                              capture_output=True, text=True, timeout=30)
    if baseline.returncode != 0:
        raise RuntimeError("baseline tests must pass before mutation scoring")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory) / "engine_liveness"
        shutil.copytree(HERE / "tests", root / "tests", ignore=shutil.ignore_patterns("__pycache__"))
        for name, original, replacement in MUTANTS:
            if SOURCE.count(original) != 1:
                raise RuntimeError("mutation anchor is not unique: " + name)
            changed = SOURCE.replace(original, replacement)
            compile(changed, name, "exec")
            (root / "scheduler_liveness.py").write_text(changed)
            shutil.rmtree(root / "__pycache__", ignore_errors=True)
            result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(root / "tests"), "-v"],
                                    capture_output=True, text=True, timeout=30)
            failed_tests = [line.split(" (")[0] for line in result.stderr.splitlines()
                            if line.startswith(("FAIL: ", "ERROR: "))]
            report.append({"mutant": name, "killed": result.returncode != 0 and bool(failed_tests),
                           "tests": failed_tests})
    print(json.dumps({"standard": "VRS-LIVENESS-MUTATION-EVIDENCE-1", "total": len(report),
                      "killed": sum(row["killed"] for row in report), "results": report}, indent=2))
    return 0 if sum(row["killed"] for row in report) >= 19 else 1


if __name__ == "__main__":
    raise SystemExit(run())
