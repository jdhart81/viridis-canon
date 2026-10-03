#!/usr/bin/env python3
"""Submit one fixed-project verification job or probe the private Comparator."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:3100/comparator/api"
PROJECT = "viridis-lean-4.28"
MAX_SOURCE_BYTES = 4 * 1024 * 1024
TERMINAL_TYPES = {"verification-ok", "verification-failed", "system-error", "overload"}


def fail(message: str) -> int:
    print(json.dumps({"type": "client-error", "description": message}, sort_keys=True))
    return 2


def health() -> int:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as response:
            health_value = json.load(response)
        with urllib.request.urlopen(f"{BASE_URL}/projects", timeout=10) as response:
            projects = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return fail(f"health probe failed: {type(exc).__name__}")
    project_ready = isinstance(projects, list) and any(
        isinstance(item, dict) and item.get("project") == PROJECT for item in projects
    )
    result = {
        "type": "health-ok" if project_ready else "health-failed",
        "project": PROJECT,
        "projectReady": project_ready,
        "service": health_value,
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if project_ready else 2


def verify() -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_SOURCE_BYTES * 2 + 4096)
        if len(raw) > MAX_SOURCE_BYTES * 2:
            return fail("request exceeds the verifier input limit")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return fail("stdin must contain one JSON request")
    if not isinstance(payload, dict):
        return fail("request root must be an object")
    challenge = payload.get("challenge")
    solution = payload.get("solution")
    theorem_names = payload.get("theoremNames")
    if not isinstance(challenge, str) or not isinstance(solution, str):
        return fail("challenge and solution must be strings")
    if not challenge.strip() or not solution.strip():
        return fail("challenge and solution must be non-empty")
    if not isinstance(theorem_names, list) or not theorem_names or not all(
        isinstance(name, str) and name for name in theorem_names
    ):
        return fail("theoremNames must be a non-empty string list")
    if len(challenge.encode()) > MAX_SOURCE_BYTES or len(solution.encode()) > MAX_SOURCE_BYTES:
        return fail("one source exceeds the verifier input limit")

    request = urllib.request.Request(
        f"{BASE_URL}/start",
        data=json.dumps({
            "project": PROJECT,
            "challenge": challenge,
            "solution": solution,
            "theoremNames": theorem_names,
        }).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            started = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return fail(f"could not start verification: {type(exc).__name__}")
    if not isinstance(started, dict) or started.get("type") != "ready":
        print(json.dumps(started, sort_keys=True))
        return 2
    request_id = started.get("requestId")
    if not isinstance(request_id, str) or not request_id:
        return fail("service returned no request identifier")

    deadline = time.monotonic() + 300
    try:
        with urllib.request.urlopen(f"{BASE_URL}/track/{request_id}", timeout=300) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line.startswith("data:"):
                    continue
                event = json.loads(line.removeprefix("data:").strip())
                if isinstance(event, dict) and event.get("type") in TERMINAL_TYPES:
                    event["requestId"] = request_id
                    event["project"] = PROJECT
                    print(json.dumps(event, sort_keys=True))
                    return 0 if event.get("type") == "verification-ok" else 2
                if time.monotonic() >= deadline:
                    break
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        tracking_error = type(exc).__name__
    else:
        tracking_error = "stream-ended-without-terminal"

    try:
        with urllib.request.urlopen(f"{BASE_URL}/result/{request_id}", timeout=30) as response:
            event = json.load(response)
        if isinstance(event, dict) and event.get("type") in TERMINAL_TYPES:
            event["requestId"] = request_id
            event["project"] = PROJECT
            event["recoveredFromTerminalJournal"] = True
            print(json.dumps(event, sort_keys=True))
            return 0 if event.get("type") == "verification-ok" else 2
    except (OSError, urllib.error.URLError, json.JSONDecodeError):
        pass
    return fail(f"verification tracking failed and no terminal journal was available: {tracking_error}")


if __name__ == "__main__":
    sys.exit(health() if sys.argv[1:] == ["--health"] else verify())
