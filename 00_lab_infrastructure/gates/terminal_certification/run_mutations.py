"""Kill behavioral mutants in disposable mini-repositories; no runtime writes."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
SCOPE = HERE.relative_to(REPO)

MUTANTS = [
    ("receipt_hash", 'if _sha(receipt_bytes) != trusted_sha:', 'if False:'),
    ("frozen_byte_binding", 'if any(_sha(documents[filename]) != bindings.get(key)\n               for key, filename in BOUND_FILES.items()):', 'if False:'),
    ("selected_manifest", 'if _sha(_bytes(package / "PAPER_PACKAGE_MANIFEST.json")) != bindings["sealed_manifest_sha256"]:', 'if False:'),
    ("terminal_flag", '                and receipt.get("terminal_for_sealed_object") is True\n', ''),
    ("certificate_false", '                and receipt.get("certificate_issued") is False', ''),
    ("local_lean_false", 'if request.get("source_run") != run_id or request.get("local_lean_execution") is not False:', 'if request.get("source_run") != run_id:'),
    ("checker_source_pin", 'if any(_sha(loaded[path]) != expected for path, expected in sources.items()):', 'if False:'),
    ("fresh_pure_checker", 'result = _pure_check(sources, documents)', 'result = receipt["checker_result"]'),
    ("recorded_result_equality", 'result == receipt.get("checker_result")', 'True'),
    ("evidence_reread", 'if any(_bytes(folder / filename) != data for filename, data in documents.items()):', 'if False:'),
    ("symlink_refusal", 'if any(part.is_symlink() for part in (path, *path.parents)):', 'if False:'),
]
PATCH_MUTANTS = [
    ("actual_open_selection", "autonomous_pipeline_controller.py",
     '    terminal = terminal_premise_work_item(path, certificate_root)\n    if terminal is not None:\n        return terminal\n', ''),
    ("eligible_fifo", "science_foundry_continuity.py",
     'if f"Run-{number:03d}" not in terminal_ids', 'if True'),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def mini_repo(target):
    shutil.copytree(HERE, target / SCOPE, ignore=shutil.ignore_patterns("__pycache__"))
    binding = json.loads((HERE / "INTEGRATION_BINDING.json").read_text())
    files = ["00_lab_infrastructure/gates/premise_declaration.py",
             "00_lab_infrastructure/gates/inv9_title_basis.py",
             "comparator-deploy/engine3_align_challenge.py"]
    files += [row["snapshot"] for row in binding["files"]]
    for relative in files:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, destination)


def test(target):
    return subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
                           str(SCOPE / "tests"), "-v"], cwd=target, capture_output=True,
                          text=True, timeout=30)


def patch_mutant(target, filename, old, new):
    scope = target / SCOPE
    binding_path = scope / "INTEGRATION_BINDING.json"
    binding = json.loads(binding_path.read_text())
    patch_path = scope / "EXISTING_SELECTION.patch"
    for row in binding["files"]:
        destination = target / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target / row["snapshot"], destination)
    applied = subprocess.run(["patch", "--batch", "-p1", "-i", str(patch_path)],
                             cwd=target, capture_output=True, text=True, timeout=10)
    if applied.returncode:
        raise RuntimeError("mutation fixture patch did not apply")
    changes = []
    for row in binding["files"]:
        before = (target / row["snapshot"]).read_text()
        destination = target / row["path"]
        after = destination.read_text()
        if destination.name == filename:
            if after.count(old) != 1:
                raise RuntimeError("patch mutant anchor is not unique")
            after = after.replace(old, new)
        row["after_sha256"] = sha(after.encode())
        changes.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            fromfile="a/" + row["path"], tofile="b/" + row["path"]))
        destination.unlink()
    changed_patch = "".join(changes).encode()
    patch_path.write_bytes(changed_patch)
    binding["patch_sha256"] = sha(changed_patch)
    binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with tempfile.TemporaryDirectory(prefix="terminal-hold-mutants-") as temporary:
        root = Path(temporary).resolve()
        baseline = root / "baseline"
        mini_repo(baseline)
        checked = test(baseline)
        if checked.returncode:
            raise RuntimeError("baseline failed:\n" + checked.stdout + checked.stderr)
        for name, old, new in MUTANTS:
            target = root / name
            mini_repo(target)
            source = target / SCOPE / "terminal_hold.py"
            text = source.read_text()
            expected = 2 if name == "selected_manifest" else 1
            if text.count(old) != expected:
                raise RuntimeError("mutant anchor count differs: " + name)
            changed = text.replace(old, new)
            compile(changed, str(source), "exec")
            source.write_text(changed)
            binding_path = target / SCOPE / "INTEGRATION_BINDING.json"
            binding = json.loads(binding_path.read_text())
            binding["terminal_helper_sha256"] = sha(changed.encode())
            binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True) + "\n")
            checked = test(target)
            output = checked.stdout + checked.stderr
            rows.append({"mutant": name, "killed": checked.returncode != 0,
                         "behavioral_failure": "AssertionError" in output,
                         "returncode": checked.returncode})
        for name, filename, old, new in PATCH_MUTANTS:
            target = root / name
            mini_repo(target)
            patch_mutant(target, filename, old, new)
            checked = test(target)
            output = checked.stdout + checked.stderr
            rows.append({"mutant": name, "killed": checked.returncode != 0,
                         "behavioral_failure": "AssertionError" in output,
                         "returncode": checked.returncode})
    result = {"standard": "VRS-TERMINAL-HOLD-MUTATIONS-1", "baseline": "PASS",
              "mutant_source_and_patch_pins_refreshed": True,
              "helper_sha256": sha((HERE / "terminal_hold.py").read_bytes()),
              "patch_sha256": sha((HERE / "EXISTING_SELECTION.patch").read_bytes()),
              "total": len(rows), "killed": sum(row["killed"] for row in rows), "mutants": rows,
              "status": "PASS" if all(row["killed"] and row["behavioral_failure"] for row in rows) else "FAIL",
              "external_mutation": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "total", "killed")}))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
