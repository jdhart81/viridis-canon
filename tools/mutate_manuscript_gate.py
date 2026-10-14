"""Run 18 behavioral guard mutants using only the gate and focused regressions.

Original M12 and M19 are excluded as equivalent guards: no-PDF deposits are
already rejected by the manuscript-role rule, and a filename cannot start with
two distinct Run prefixes. No syntax/import failures count as kills.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


MUTANTS = {
    "M1 top-level PDF magic": ('_pdf(data); top[path.name] = _hashes(data)', 'top[path.name] = _hashes(data)'),
    "M2 Run-specific filename": ('and name.startswith(run + "-"))', ')'),
    "M3 digest upload binding": ('if require_digest_inventory:', 'if False:'),
    "M4 safe archive paths": ('def _safe_member(name: str) -> None:\n', 'def _safe_member(name: str) -> None:\n    return\n'),
    "M5 unknown-role manuscript coverage": ('    return not figure\n', '    return False\n'),
    "M6 anonymous downloaded byte hashes": ('if _hashes(data) != {k: expected[k] for k in ("sha256", "md5", "bytes")}:', 'if False:'),
    "M7 public metadata size and md5": ('if (actual is None or actual.get("size") != expected["bytes"]\n                or actual.get("checksum") != "md5:" + expected["md5"]):', 'if actual is None:'),
    "M8 duplicate archive members": ('if name in seen:\n                raise ManuscriptPDFHold("duplicate reproduction archive member")', 'if False:\n                raise ManuscriptPDFHold("duplicate reproduction archive member")'),
    "M9 artifact symlink refusal": ('if path.is_symlink() or not path.is_file() or any(', 'if not path.is_file() or False and any('),
    "M10 exact note archive hash": ('if len(papers) != 1 or papers[0].get("sha256") != member["sha256"]:', 'if False:'),
    "M11 Word manuscript coverage": ('    if path.suffix in {".docx", ".doc", ".odt"}:\n        return True', '    if path.suffix in {".docx", ".doc", ".odt"}:\n        return False'),
    "M13 TAR nonregular manuscript": ('if _archived_manuscript(name) and not item.isfile():', 'if False:'),
    "M14 top-level upload boundary": ('if len(set(names)) != len(names) or any(p.parent.resolve() != bundle.resolve() for p in paths):', 'if len(set(names)) != len(names):'),
    "M15 figure-only deposit": ('if not declared_names and not any(_manuscript_name(name) for name in top):', 'if False:'),
    "M16 read-race identity": ('if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):', 'if False:'),
    "M17 role declaration byte binding": ('if row["filename"] not in top or top[row["filename"]] != {k: row[k] for k in ("sha256", "md5", "bytes")}:', 'if row["filename"] not in top:'),
    "M18 inspect TAR family": ('if _archive_kind(upload_bytes[path.name]) is None and not path.name.lower().endswith(ARCHIVE_SUFFIXES):', 'if _archive_kind(upload_bytes[path.name]) == "tar" or (_archive_kind(upload_bytes[path.name]) is None and not path.name.lower().endswith(ARCHIVE_SUFFIXES)):'),
    "M20 exact Run identity grammar": ('re.fullmatch(r"Run-[0-9]{3,}", run)', 're.fullmatch(r".+", run)'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    gate = source / "manuscript_pdf_gate.py"
    tests = source / "tests/test_gate_hardening.py"
    original = gate.read_text(); test_bytes = tests.read_bytes()
    started = time.monotonic(); rows = []; baseline_count = None
    for label, replacement in [("BASELINE", None), *MUTANTS.items()]:
        if time.monotonic() - started > 550:
            raise SystemExit("ten-minute mutation budget would be exceeded")
        modified = original
        if replacement:
            old, new = replacement
            if original.count(old) != 1:
                rows.append({"mutant": label, "result": "INVALID_PATTERN", "occurrences": original.count(old)})
                continue
            modified = original.replace(old, new)
        try:
            ast.parse(modified)
        except SyntaxError:
            rows.append({"mutant": label, "result": "INVALID_SYNTAX"})
            continue
        with tempfile.TemporaryDirectory(prefix="viridis-gate-mutation-") as temp:
            root = Path(temp); (root / "tests").mkdir()
            (root / "manuscript_pdf_gate.py").write_text(modified)
            (root / "tests/test_gate_hardening.py").write_bytes(test_bytes)
            run = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_gate_hardening.py"],
                cwd=root, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                capture_output=True, text=True, timeout=30, check=False)
            match = re.search(r"Ran ([0-9]+) tests?", run.stderr)
            count = int(match[1]) if match else None
            if label == "BASELINE":
                result = "PASS" if run.returncode == 0 and count else "BASELINE_FAILURE"
                baseline_count = count
            elif count != baseline_count or re.search(r"(?:ImportError|SyntaxError|ModuleNotFoundError)", run.stderr):
                result = "INVALID_EXECUTION"
            elif run.returncode == 0:
                result = "SURVIVED"
            elif re.search(r"FAILED \(failures=[0-9]+\)", run.stderr):
                result = "KILLED"
            else:
                result = "INVALID_TEST_ERROR"
            rows.append({"mutant": label, "result": result, "tests": count,
                         "failing_tests": re.findall(r"^FAIL: (.+)$", run.stderr, re.M)})
            if label == "BASELINE" and result != "PASS":
                break
    real = rows[1:]
    receipt = {"standard": "VRS-MANUSCRIPT-GATE-BEHAVIORAL-MUTATIONS-1",
        "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "gate_sha256": hashlib.sha256(gate.read_bytes()).hexdigest(),
        "tests_sha256": hashlib.sha256(test_bytes).hexdigest(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": sys.version.split()[0], "baseline": rows[0], "mutants": real,
        "declared_mutants": 18,
        "killed": sum(row["result"] == "KILLED" for row in real),
        "survived": sum(row["result"] == "SURVIVED" for row in real),
        "invalid": sum(row["result"] not in {"KILLED", "SURVIVED"} for row in real),
        "excluded_original_mutants": {"M12": "equivalent: no-PDF rejection is also enforced by manuscript-role rule", "M19": "equivalent: unique Run-specific prefixes prevent sharing one filename between Runs"},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "full_runtime_copies": 0, "external_requests": 0}
    receipt["status"] = "PASS" if receipt["baseline"]["result"] == "PASS" and len(real) == 18 and receipt["invalid"] == 0 and receipt["killed"] >= 17 else "HOLD"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as output:
        output.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: receipt[key] for key in ("status", "killed", "survived", "invalid", "declared_mutants", "elapsed_seconds")}, indent=2))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
