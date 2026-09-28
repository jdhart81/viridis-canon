#!/usr/bin/env python3
"""Viridis OS bundle dispatcher (Python stdlib only).

Runs callable functions from the bundle this file ships in.

    echo '{"id": "tempo", "inputs": {...}}' | python3 run.py
    echo '{"calls": [{"id": ..., "inputs": ...}, ...]}' | python3 run.py
    python3 run.py --self-test        # every published example, exact match

Each result is ``{"ok": true, "output": {...}}`` or
``{"ok": false, "error_class": "input"|"blocked"|"unknown"|"fault", "error": "..."}``.
Non-finite numbers are returned as ``null`` (JSON has no Infinity/NaN).
Reads no network, clock, environment or files outside the bundle.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "runners"))

from viridis_fn import InputError, validate_schema  # noqa: E402
from theorem_runner import run_theorem  # noqa: E402

_FUNCTIONS = None
_MODULES = {}


def functions() -> dict:
    global _FUNCTIONS
    if _FUNCTIONS is None:
        document = json.loads((HERE / "functions.json").read_text(encoding="utf-8"))
        _FUNCTIONS = {entry["id"]: entry for entry in document["functions"]}
    return _FUNCTIONS


def _runner(entry: dict):
    fid = entry["id"]
    if fid not in _MODULES:
        path = HERE / entry["runner_path"]
        spec = importlib.util.spec_from_file_location(f"viridis_runner_{fid.replace('-', '_')}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULES[fid] = module
    return _MODULES[fid]


def sanitize(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    return value


def call(fid, inputs) -> dict:
    entry = functions().get(fid) if isinstance(fid, str) else None
    if entry is None:
        return {"ok": False, "error_class": "unknown", "error": f"unknown decision kernel: {fid}"}
    if not entry.get("runnable"):
        return {"ok": False, "error_class": "blocked", "error": f"decision kernel '{fid}' is blocked: {entry['service_state']}"}
    try:
        validate_schema(inputs, entry["input_schema"])
        if entry["runner"] == "theorem":
            output = run_theorem(entry, inputs)
        else:
            output = _runner(entry).run(json.loads(json.dumps(inputs)))
        return {"ok": True, "output": sanitize(output)}
    except InputError as error:
        return {"ok": False, "error_class": "input", "error": str(error)}
    except Exception as error:  # a runner fault is never reported as a result
        return {"ok": False, "error_class": "fault", "error": f"runner fault in '{fid}': {type(error).__name__}"}


def _same(a, b) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is bool and type(b) is bool and a == b
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_same(a[k], b[k]) for k in a)  # JSON objects are unordered
    return a == b


def self_test() -> int:
    failures = 0
    count = 0
    for fid, entry in functions().items():
        if not entry.get("runnable"):
            continue
        count += 1
        result = call(fid, entry["example"]["inputs"])
        if not result["ok"] or not _same(result["output"], sanitize(entry["example"]["expected_outputs"])):
            failures += 1
            print(json.dumps({"id": fid, "result": result}), file=sys.stderr)
    print(json.dumps({"self_test": "PASS" if failures == 0 else "FAIL", "examples": count, "failures": failures}))
    return 0 if failures == 0 else 1


def main(argv) -> int:
    if "--self-test" in argv:
        return self_test()
    request = json.loads(sys.stdin.read() or "{}")
    if isinstance(request, dict) and "calls" in request:
        response = {"results": [call(c.get("id"), c.get("inputs")) for c in request["calls"]]}
    else:
        response = call(request.get("id"), request.get("inputs"))
    sys.stdout.write(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
