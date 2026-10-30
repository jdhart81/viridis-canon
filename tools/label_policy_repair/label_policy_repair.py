"""Finite 067a policy metadata repair. SOURCE CANDIDATE: no admission is supplied.

No producer, certificate issuer, publisher helper, Git, or third-party imports.
The private plan, all evidence, admission and installed source are hash-bound.
"""
# The actual CLI arms its original deadline before argparse/HTTP/JSON imports.
# Imported TEST_ONLY fixtures do not acquire action authority or install timers.
import os
import signal
import sys
import time
WHOLE_ACTION_STARTED = time.monotonic()
MAX_SECONDS, ACTIVE_SECONDS, HARD_SECONDS, MAX_STRIKES = 600, 540, 590, 2
MAX_INPUT_BYTES, INPUT_CHUNK_BYTES = 16 * 1024 * 1024, 65536


class Hold(Exception):
    """Only fixed, non-secret diagnostic codes may cross this boundary."""


_DEADLINE_ARMED = False
_SOFT_REACHED = False
_SOFT_WATCHDOG_STARTED = False


def _soft_deadline(signum, frame):
    global _SOFT_REACHED
    _SOFT_REACHED = True
    # Never cancel, replace or extend the independently armed kernel hard end.
    raise Hold("ACTION_ACTIVE_DEADLINE")


def _arm_cli_deadline():
    global _DEADLINE_ARMED
    supported = (os.name == "posix" and all(hasattr(signal, x) for x in
                 ("SIGALRM", "SIGUSR1", "SIG_BLOCK", "ITIMER_REAL", "setitimer",
                  "getitimer", "pthread_sigmask")) and
                 all(hasattr(os, x) for x in ("O_NOFOLLOW", "O_NONBLOCK", "O_CLOEXEC")))
    if not supported or _DEADLINE_ARMED:
        raise Hold("SUPPORTED_MAIN_THREAD_POSIX_DEADLINE_REQUIRED")
    try:
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        if ({signal.SIGALRM, signal.SIGUSR1} & blocked or
            signal.getsignal(signal.SIGALRM) != signal.SIG_DFL or
            signal.getsignal(signal.SIGUSR1) != signal.SIG_DFL or
            signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0)):
            raise Hold("EXISTING_SIGNAL_OWNERSHIP_OR_MASK_FORBIDDEN")
        remaining = WHOLE_ACTION_STARTED + HARD_SECONDS - time.monotonic()
        if remaining <= 0:
            raise Hold("ACTION_HARD_DEADLINE")
        # signal.signal is a genuine main-thread prerequisite, before any input.
        signal.signal(signal.SIGUSR1, _soft_deadline)
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, remaining)
        _DEADLINE_ARMED = True
    except (ValueError, OSError):
        raise Hold("SUPPORTED_MAIN_THREAD_POSIX_DEADLINE_REQUIRED") from None


def _start_soft_watchdog():
    global _SOFT_WATCHDOG_STARTED
    if not _DEADLINE_ARMED or _SOFT_WATCHDOG_STARTED:
        raise Hold("SOFT_WATCHDOG_OWNERSHIP_REQUIRED")
    # The kernel hard alarm is ALREADY armed before this larger import.
    import threading
    soft_end = WHOLE_ACTION_STARTED + ACTIVE_SECONDS
    own_pid = os.getpid()
    def send_soft_once():
        remaining = soft_end - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        # A fixed self-signal from this still-live process; no caller PID/channel.
        os.kill(own_pid, signal.SIGUSR1)
    _SOFT_WATCHDOG_STARTED = True
    watchdog = threading.Thread(target=send_soft_once,
                                name="fixed-label-policy-soft-deadline", daemon=True)
    watchdog.start()


if __name__ == "__main__":
    try:
        _arm_cli_deadline()
        _start_soft_watchdog()
    except (Hold, RuntimeError, OSError):
        # No arguments, inputs, credentials, journal or requests have been read.
        os._exit(2)

import argparse
import copy
import hashlib
import json
import re
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

POLICY_SHA = "067a035165c96f70d89327aa87ed150288e9674b4f04c5637bbe142a790fa3c3"
AUTHORITY_SHA = "ce1ec797831bb1daea0c4242b3a95c35a09d5edc5dbca4b41184f6f7c42a9737"
BANNER = ("UNCERTIFIED manuscript artifact. No issuer-produced Viridis Comparator "
          "certificate has been shown to bind this public manuscript's exact bytes. "
          "Any linked certificate applies only to its exact sealed artifacts and stated "
          "theorem scope. Results remain conditional on the declared assumptions.")
RESTORE49 = frozenset("20008839 20010754 20320324 20399676 20412507 20763323 20800757 "
    "20838923 21168212 21168224 21168241 21223160 21223204 21223218 21223226 "
    "21223240 21609934 21609938 21609942 21609945 21609947 21609949 21609952 "
    "22236409 22236416 22236427 22236441 22236458 22236496 22236521 22236530 "
    "22236770 22665538 22736660 22736684 22736699 22736710 22848678 22848682 "
    "22848685 22848693 23004852 23004858 23004862 23004866 23004870 23329649 "
    "23329747 23329760".split())
MAP35 = frozenset("23329771 23329754 23329742 23329732 23329645 23141980 23141592 "
    "23112436 23112434 23112432 23004874 22736716 22736706 22736690 22736676 "
    "22736670 22736666 22736656 22736654 22736650 22736637 22665565 22236361 "
    "21002784 20982979 20982975 20982971 20982967 20982961 20982959 20982957 "
    "20982949 20982947 20982945 20551119".split())
INDEX18 = frozenset("21971041 21971042 21971043 21971046 21971047 21971052 21971057 "
    "22236735 22236741 22236748 22236755 22236761 22236768 22236775 22236785 "
    "22236789 22665525 22665554".split())
NON_MANUSCRIPTS = frozenset(("23112434", "23112432", "20551119"))
EXTRA8 = frozenset("21971042 21971043 21971047 21971052 22236748 22236755 22236775 22236789".split())
ORIGIN = "https://zenodo.org"
NATIVE_ACCEPT = "application/vnd.inveniordm.v1+json"
TOKEN_RELATIVE = Path("secrets/Zenodo_API/Zenodo_token.md")




def need(condition, code):
    if not condition:
        raise Hold(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def check_deadline(deadline=None):
    deadline = WHOLE_ACTION_STARTED + ACTIVE_SECONDS if deadline is None else deadline
    need(type(deadline) in (int, float) and deadline == deadline and
         abs(deadline) != float("inf"), "DEADLINE_INVALID")
    deadline = min(deadline, WHOLE_ACTION_STARTED + HARD_SECONDS)
    need(time.monotonic() < deadline, "ACTION_CAP")
    return deadline


def regular_bytes(path, deadline=None):
    path = Path(path)
    deadline = check_deadline(deadline)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
    fd = None
    try:
        fd = os.open(path, flags)
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_INPUT_BYTES,
             "INPUT_NOT_BOUNDED_REGULAR")
        chunks, count = [], 0
        while True:
            check_deadline(deadline)
            block = os.read(fd, min(INPUT_CHUNK_BYTES, MAX_INPUT_BYTES - count + 1))
            check_deadline(deadline)
            if not block:
                break
            count += len(block)
            need(count <= MAX_INPUT_BYTES, "INPUT_TOO_LARGE")
            chunks.append(block)
        after = os.fstat(fd)
        current = path.lstat()
    except OSError:
        raise Hold("INPUT_UNREADABLE") from None
    finally:
        if fd is not None:
            os.close(fd)
    identity = lambda v: (v.st_dev, v.st_ino, v.st_size, v.st_mtime_ns, v.st_ctime_ns)
    need(identity(before) == identity(after) == identity(current), "INPUT_CHANGED")
    check_deadline(deadline)
    return b"".join(chunks)


def stable_bytes(path, expected, deadline=None):
    need(re.fullmatch(r"[0-9a-f]{64}", expected or ""), "INPUT_HASH_REQUIRED")
    raw = regular_bytes(path, deadline)
    need(hashlib.sha256(raw).hexdigest() == expected, "INPUT_HASH_DRIFT")
    check_deadline(deadline)
    return raw


def read_json(path, expected, deadline=None):
    try:
        value = json.loads(stable_bytes(path, expected, deadline))
        check_deadline(deadline)
        return value
    except (ValueError, UnicodeError):
        raise Hold("INPUT_JSON_INVALID") from None


def source_json(source, deadline=None):
    return read_json(source["path"], source["sha256"], deadline)


def projection(record):
    """All native fields protected except enumerated server lifecycle/URL fields.

    Metadata related identifiers, authorship, rights and parent communities remain.
    File bytes/keys/sizes are independently verified before and after the action.
    """
    result = copy.deepcopy(record)
    for key in ("links", "revision_id", "created", "updated", "is_draft",
                "is_published", "status", "versions"):
        result.pop(key, None)
    for entry in result.get("files", {}).get("entries", {}).values():
        entry.pop("links", None)
    return result


def native_record(record):
    need(isinstance(record, dict) and type(record.get("revision_id")) is int and
         isinstance(record.get("metadata"), dict) and
         "keywords" not in record["metadata"] and
         isinstance(record["metadata"].get("subjects", []), list) and
         isinstance(record.get("files"), dict) and
         isinstance(record["files"].get("entries"), dict), "NATIVE_SERIALIZER_REQUIRED")


def file_table(record):
    entries = record.get("files", {}).get("entries", {})
    need(isinstance(entries, dict), "FILE_TABLE_INVALID")
    return sorted((key, item["size"], item["checksum"])
                  for key, item in entries.items())


def changed_metadata(before, item):
    """No arbitrary metadata replacement: exact, single-occurrence operations."""
    result = copy.deepcopy(before)
    description = result.get("description", "")
    need(isinstance(description, str), "DESCRIPTION_INVALID")
    for edit in item["description_edits"]:
        need(set(edit) == {"kind", "before", "after"}, "EDIT_FIELDS_INVALID")
        need(edit["kind"] in {"historical_caveat", "index_byte_claim", "working_paper_caveat"}, "EDIT_KIND")
        if edit["kind"] == "working_paper_caveat":
            need(item["id"] in RESTORE49 and "Working paper" in edit["after"],
                 "WORKING_PAPER_SCOPE")
        if item["id"] in INDEX18 - EXTRA8:
            need(edit["kind"] == "index_byte_claim", "INDEX_SCOPE")
        need(isinstance(edit["before"], str) and edit["before"] and
             isinstance(edit["after"], str) and edit["after"], "EDIT_TEXT_INVALID")
        need(description.count(edit["before"]) == 1, "EDIT_NOT_UNIQUE")
        description = description.replace(edit["before"], edit["after"], 1)
    if item["add_banner"]:
        need(BANNER not in description, "BANNER_ALREADY_PRESENT")
        description = "<p>" + BANNER + "</p>\n" + description
    result["description"] = description
    subjects = result.get("subjects", [])
    need(isinstance(subjects, list), "SUBJECTS_INVALID")
    need(len({edit["index"] for edit in item["subject_edits"]}) == len(item["subject_edits"]),
         "DUPLICATE_SUBJECT_EDIT")
    for edit in item["subject_edits"]:
        need(set(edit) == {"index", "before", "after"}, "SUBJECT_EDIT_FIELDS")
        i = edit["index"]
        need(type(i) is int and 0 <= i < len(subjects), "SUBJECT_INDEX")
        need(isinstance(subjects[i], dict) and subjects[i].get("subject") ==
             edit["before"] and isinstance(edit["after"], str), "SUBJECT_CAS")
        subjects[i]["subject"] = edit["after"]
    if item["subject_edits"]:
        result["subjects"] = subjects
    need(result != before, "NO_METADATA_CHANGE")
    need({k: v for k, v in result.items() if k not in {"description", "subjects"}} ==
         {k: v for k, v in before.items() if k not in {"description", "subjects"}},
         "UNEXPECTED_METADATA_DIFF")
    need(digest(result) == item["expected_metadata_sha256"], "EXPECTED_DIFF_DRIFT")
    return result


def validate_mapping(item, sources):
    evidence = item["status_mapping_evidence"]
    need(evidence["verdict"] == "INDEPENDENT_EXACT_BYTES_SCOPE_REVIEW_PASS",
         "MAPPING_REVIEW_REQUIRED")
    need(evidence["source_ids"] and evidence["source_ids"] == item["mapping_source_ids"],
         "MAPPING_SOURCE_BINDING")
    files = {f["key"]: f for f in item["public_files"]}
    pdfs = {key for key in files if key.lower().endswith(".pdf")}
    artifacts = evidence["artifacts"]
    need(len({a["key"] for a in artifacts}) == len(artifacts) and
         {a["key"] for a in artifacts} == pdfs, "MAPPING_PDF_COVERAGE")
    for artifact in artifacts:
        need(artifact["public_sha256"] == files[artifact["key"]]["sha256"],
             "MAPPING_PUBLIC_BYTES")
        need(artifact["status"] in {"UNMATCHED_EXACT_BYTES", "BOUND_EXACT_BYTES"},
             "UNKNOWN_CERTIFICATE_MAPPING")
        need(artifact["certificate_inventory_source_ids"] and
             set(artifact["certificate_inventory_source_ids"]) <=
             set(evidence["source_ids"]), "CERTIFICATE_SEARCH_REQUIRED")
        for cert in artifact["certificates"]:
            need(cert["source_id"] in evidence["source_ids"] and
                 cert["sha256"] == sources[cert["source_id"]]["sha256"] and
                 re.fullmatch(r"[0-9a-f]{64}", cert["sha256"]) and
                 re.fullmatch(r"[0-9a-f]{64}", cert["bound_artifact_sha256"]) and
                 bool(cert["theorem_scope"]), "CERTIFICATE_BINDING_REQUIRED")
        if artifact["status"] == "BOUND_EXACT_BYTES":
            need(any(c["bound_artifact_sha256"] == artifact["public_sha256"]
                     for c in artifact["certificates"]), "BOUND_WITHOUT_CERTIFICATE")
        else:
            need(all(c["bound_artifact_sha256"] != artifact["public_sha256"]
                     for c in artifact["certificates"]), "FALSE_UNMATCHED_LABEL")
    if item["add_banner"]:
        need(pdfs and all(a["status"] == "UNMATCHED_EXACT_BYTES" for a in artifacts),
             "BANNER_MISDESCRIBES_BOUND_OR_UNKNOWN_ARTIFACT")
    if item["id"] in RESTORE49 | MAP35:
        need(item["add_banner"], "UNMATCHED_ARTIFACT_BANNER_REQUIRED")
    need(item["id"] not in NON_MANUSCRIPTS, "NO_MANUSCRIPT_NO_REPAIR")


def validate_record(item, sources):
    need(item["id"] in RESTORE49 | MAP35 | INDEX18, "FOREIGN_RECORD_ID")
    need(type(item["before_revision"]) is int, "REVISION_REQUIRED")
    need(item["mapping_source_ids"] and set(item["mapping_source_ids"]) <= set(sources),
         "MAPPING_SOURCE_NOT_PINNED")
    need(len({f["key"] for f in item["public_files"]}) == len(item["public_files"]),
         "DUPLICATE_FILE")
    for f in item["public_files"]:
        need(set(f) == {"key", "size", "checksum", "sha256"} and
             type(f["size"]) is int and f["size"] >= 0 and
             re.fullmatch(r"[0-9a-f]{64}", f["sha256"]), "FILE_SHA_REQUIRED")
    if item["id"] not in RESTORE49 | EXTRA8:
        need(not item["subject_edits"], "SUBJECT_SCOPE")
    validate_mapping(item, sources)
    changed_metadata(item["before_metadata"], item)


def admit(plan, plan_sha, source_path, receipt, deadline=None):
    deadline = check_deadline(deadline)
    need("VIRIDIS_ZENODO_API_BASE" not in os.environ, "ENDPOINT_OVERRIDE_FORBIDDEN")
    need(plan["schema"] == "VRS-067A-LABEL-METADATA-PLAN-1", "PLAN_SCHEMA")
    need(plan["enabled"] is True, "ACTION_DISABLED")
    need(plan["policy_sha256"] == POLICY_SHA and
         plan["authority_sha256"] == AUTHORITY_SHA, "POLICY_AUTHORITY_MISMATCH")
    need(plan["max_strikes"] == MAX_STRIKES and
         plan["max_seconds"] == MAX_SECONDS, "ATTEMPT_LIMIT_CHANGED")
    need(plan["preserve_all_prior_holds"] is True and
         plan["both_successors_quarantined"] is True, "PRIOR_HOLD_CHANGED")
    sources = plan["sources"]
    need(set(sources) >= {"policy", "direct_authority", "strike_history"}, "SOURCES_MISSING")
    need(sources["policy"]["sha256"] == POLICY_SHA and
         sources["direct_authority"]["sha256"] == AUTHORITY_SHA, "SOURCE_BINDING")
    for source in sources.values():
        stable_bytes(source["path"], source["sha256"], deadline)
    need(receipt["plan_sha256"] == plan_sha and
         receipt["tool_sha256"] == hashlib.sha256(regular_bytes(source_path, deadline)).hexdigest(),
         "INSTALL_PLAN_BINDING")
    need(receipt["main_commit"] == receipt["reviewed_commit"] == receipt["installed_commit"]
         and re.fullmatch(r"[0-9a-f]{40}", receipt["main_commit"]), "MERGED_SOURCE_REQUIRED")
    for key in ("actual_claude_pass", "full_ci_pass", "normal_main_merge",
                "S4_pass", "I14_pass", "independent_mapping_pass"):
        need(receipt[key] is True and receipt[key + "_source_id"] in sources,
             "FRESH_REVIEW_ADMISSION_REQUIRED")
    # This source belongs only to the separate admission, never plan.sources:
    # authority -> immutable plan is acyclic, and CAS rereads it before each call.
    action_source = receipt["exact_metadata_action_authority"]
    need(receipt["exact_metadata_action_authorized"] is True and
         isinstance(action_source, dict) and set(action_source) == {"path", "sha256"},
         "EXACT_ACTION_AUTHORITY_REQUIRED")
    action_authority = source_json(action_source, deadline)
    need(action_authority["schema"] == "VRS-067A-EXACT-NATIVE-ACTION-AUTHORITY-1" and
         action_authority["policy_sha256"] == POLICY_SHA and
         action_authority["direct_authority_sha256"] == AUTHORITY_SHA and
         action_authority["plan_sha256"] == plan_sha and
         action_authority["tool_sha256"] == receipt["tool_sha256"] and
         action_authority["record_ids"] == sorted(r["id"] for r in plan["records"]) and
         action_authority["allowed_modes"] == receipt["allowed_modes"] and
         set(receipt["allowed_modes"]) <= {"rehearse", "apply"} and receipt["allowed_modes"],
         "EXACT_ACTION_AUTHORITY_BINDING")
    history = source_json(sources["strike_history"], deadline)
    need(history["case"] == "067A_CORRECTIVE_LABEL_POLICY" and
         history["max_strikes"] == MAX_STRIKES, "STRIKE_HISTORY_SCOPE")
    strikes = history["failed_attempt_source_ids"]
    need(len(strikes) == len(set(strikes)) and set(strikes) <= set(sources), "STRIKE_SOURCES")
    for source_id in strikes:
        need(source_json(sources[source_id], deadline)["first_failure"] is not None, "STRIKE_RECEIPT")
    need(type(receipt["attempts_used"]) is int and
         receipt["attempts_used"] == len(strikes) < MAX_STRIKES, "ATTEMPTS_EXHAUSTED")
    need(receipt["quarantines_preserved"] is True, "QUARANTINE_ADMISSION")
    records = plan["records"]
    need(records and len({r["id"] for r in records}) == len(records), "DUPLICATE_RECORD")
    for item in records:
        validate_record(item, sources)
    return receipt


class Journal:
    """A persistent O_EXCL record claim; a crash or failure never permits replay."""
    def __init__(self, directory, record_id, plan_sha, mode):
        need(mode in {"rehearse", "apply"}, "CLAIM_KIND_INVALID")
        self.path = Path(directory) / (record_id + "." + mode + ".jsonl")
        self.value = {"record_id": record_id, "plan_sha256": plan_sha,
                      "kind": mode, "state": "CLAIMED", "first_failure": None, "calls": 0,
                      "owned_draft": False, "cleanup_confirmed": False}
        try:
            fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(canonical(self.value) + b"\n"); handle.flush(); os.fsync(handle.fileno())
        except OSError:
            raise Hold("ACTION_ALREADY_CLAIMED_OR_JOURNAL_UNAVAILABLE") from None

    def save(self):
        # Append-only: a later cleanup/readback cannot erase the first failure.
        flags = os.O_WRONLY | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(self.path, flags), "wb") as handle:
            handle.write(canonical(self.value) + b"\n"); handle.flush(); os.fsync(handle.fileno())

    def fail(self, code):
        if self.value["first_failure"] is None:
            self.value["first_failure"] = code
        self.value["state"] = "HOLD"
        self.save()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Hold("REDIRECT_FORBIDDEN")


class Transport:
    def __init__(self, token):
        self._token = token
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def __repr__(self):
        return "<Transport credential redacted>"

    def request(self, method, path, authenticated=False, body=None, etag=None,
                file_size=None, deadline=None):
        need(path.startswith("/api/records/") and "?" not in path and "#" not in path,
             "ENDPOINT_SCOPE")
        is_file = (method == "GET" and re.fullmatch(
            r"/api/records/[0-9]+/files/[^/]+/content", path) is not None)
        need((file_size is not None) == is_file, "FILE_TRANSPORT_SCOPE")
        if is_file:
            need(type(file_size) is int and file_size >= 0 and not authenticated,
                 "ANONYMOUS_FILE_SIZE_REQUIRED")
        headers = {"Accept": "*/*" if is_file else NATIVE_ACCEPT}
        if is_file:
            headers["Accept-Encoding"] = "identity"
        if authenticated:
            headers["Authorization"] = "Bearer " + self._token
        if etag:
            headers["If-Match"] = etag
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(ORIGIN + path, data=None if body is None else
                                        canonical(body), headers=headers, method=method)
        try:
            deadline = check_deadline(deadline)
            remaining = deadline - time.monotonic()
            response = self._opener.open(request, timeout=min(30, remaining))
        except urllib.error.HTTPError as error:
            return error.code, None, {}
        except Hold:
            raise
        except Exception:
            raise Hold("TRANSPORT_UNKNOWN") from None
        try:
            with response:
                if file_size is not None:
                    h = hashlib.sha256(); count = 0
                    while True:
                        need(time.monotonic() < deadline, "ACTION_DEADLINE")
                        block = response.read(INPUT_CHUNK_BYTES)
                        check_deadline(deadline)
                        if not block:
                            break
                        count += len(block)
                        need(count <= file_size, "FILE_SIZE_DRIFT")
                        h.update(block)
                    body = {"size": count, "sha256": h.hexdigest()}
                else:
                    raw = response.read(10 * 1024 * 1024 + 1)
                    check_deadline(deadline)
                    need(len(raw) <= 10 * 1024 * 1024, "RESPONSE_TOO_LARGE")
                    body = json.loads(raw) if raw else None
                check_deadline(deadline)
                return response.status, body, {k.lower(): v for k, v in response.headers.items()}
        except Hold:
            raise
        except Exception:
            raise Hold("RESPONSE_UNKNOWN") from None


def credential(core_root, expected_sha, deadline=None):
    root = Path(core_root).resolve(strict=True)
    path = root / TOKEN_RELATIVE
    need(path.resolve(strict=True) == path and root.is_dir(), "CREDENTIAL_PATH_SCOPE")
    raw = stable_bytes(path, expected_sha, deadline)
    try:
        text = raw.decode("utf-8").replace("\\", "")
        candidates = re.findall(r"[A-Za-z0-9_\-]{30,}", text)
        need(candidates, "CREDENTIAL_FORMAT")
        longest = max(map(len, candidates))
        winners = set(c for c in candidates if len(c) == longest)
        need(len(winners) == 1, "CREDENTIAL_AMBIGUOUS")
        return winners.pop().encode("ascii").decode("ascii")
    except (UnicodeError, ValueError):
        raise Hold("CREDENTIAL_FORMAT") from None


class Action:
    def __init__(self, plan, item, journal, transport, cas, started):
        self.plan, self.item, self.journal = plan, item, journal
        self.transport, self.cas = transport, cas
        self.started, self.owned = started, False
        self.base = "/api/records/" + item["id"]

    def call(self, method, path, expected, cleanup=False, **kwargs):
        need(cleanup or self.journal.value["first_failure"] is None, "ACTION_POISONED")
        allowed = ((path == self.base and method == "GET") or
                   (path == self.base + "/draft" and method in {"GET", "POST", "PUT", "DELETE"}) or
                   (path == self.base + "/draft/actions/publish" and method == "POST" and
                    getattr(self, "mode", None) == "apply" and getattr(self, "ready", False)) or
                   (method == "GET" and path.startswith(self.base + "/files/") and
                    path.endswith("/content")))
        need(allowed, "ACTION_ENDPOINT_OR_PUBLISH_SCOPE")
        deadline = self.started + (MAX_SECONDS if cleanup else ACTIVE_SECONDS)
        deadline = check_deadline(deadline)
        self.cas(deadline)  # Includes installed source, all input hashes and authority.
        self.journal.value["calls"] += 1
        self.journal.save()  # Persist budget before dispatch; no automatic retry.
        try:
            status, value, headers = self.transport.request(method, path, deadline=deadline, **kwargs)
            need(status in expected, "HTTP_" + str(status) if type(status) is int else
                 "TRANSPORT_UNKNOWN")
            return status, value, headers
        except Hold as error:
            self.journal.fail(str(error))
            raise

    def verify_files(self, public):
        wanted = self.item["public_files"]
        need(file_table(public) == sorted((f["key"], f["size"], f["checksum"])
                                         for f in wanted), "FILE_INVENTORY_DRIFT")
        observed = []
        for f in wanted:
            path = self.base + "/files/" + urllib.parse.quote(f["key"], safe="") + "/content"
            _, actual, _ = self.call("GET", path, {200}, file_size=f["size"])
            need(actual == {"size": f["size"], "sha256": f["sha256"]}, "FILE_BYTES_DRIFT")
            observed.append({"key": f["key"], **actual})
        return observed

    def discard(self):
        need(self.owned, "UNOWNED_DRAFT_CLEANUP_FORBIDDEN")
        self.call("DELETE", self.base + "/draft", {204}, cleanup=True, authenticated=True)
        self.call("GET", self.base + "/draft", {404, 410}, cleanup=True, authenticated=True)
        self.journal.value["cleanup_confirmed"] = True
        self.journal.save()
        self.owned = False

    def run(self, mode):
        need(mode in {"rehearse", "apply"}, "MODE_INVALID")
        self.mode = mode
        try:
            _, public, _ = self.call("GET", self.base, {200})
            native_record(public)
            need(str(public["id"]) == self.item["id"] and
                 public["revision_id"] == self.item["before_revision"] and
                 digest(projection(public)) == self.item["before_projection_sha256"] and
                 public["metadata"] == self.item["before_metadata"], "PUBLIC_CAS")
            before_files = self.verify_files(public)
            self.call("GET", self.base + "/draft", {404, 410}, authenticated=True)
            _, current, headers = self.call("GET", self.base, {200}, authenticated=True)
            native_record(current)
            need(digest(projection(current)) == digest(projection(public)) and
                 current["revision_id"] == public["revision_id"], "REVISION_CAS")
            etag = headers.get("etag")
            need(isinstance(etag, str) and etag == self.item["before_etag"], "ETAG_CAS")
            _, draft, creation_headers = self.call("POST", self.base + "/draft", {201},
                                                   authenticated=True, etag=etag)
            native_record(draft)
            # Ownership is granted only by a successful response with the exact ID.
            need(str(draft["id"]) == self.item["id"] and draft["is_draft"] is True,
                 "DRAFT_OWNERSHIP_UNCONFIRMED")
            self.owned = True
            self.journal.value["owned_draft"] = True; self.journal.save()
            need(projection(draft) == projection(public), "DRAFT_BASELINE_DRIFT")
            body = copy.deepcopy(draft)
            body["metadata"] = changed_metadata(draft["metadata"], self.item)
            expected = projection(body)
            creation_etag = creation_headers.get("etag")
            need(isinstance(creation_etag, str) and creation_etag, "CREATED_DRAFT_ETAG_REQUIRED")
            self.call("PUT", self.base + "/draft", {200}, authenticated=True, body=body,
                      etag=creation_etag)
            _, readback, draft_headers = self.call("GET", self.base + "/draft", {200}, authenticated=True)
            native_record(readback)
            need(projection(readback) == expected and file_table(readback) == file_table(public),
                 "DRAFT_PROJECTED_DIFF_MISMATCH")
            if mode == "rehearse":
                self.discard()
                _, unchanged, _ = self.call("GET", self.base, {200})
                native_record(unchanged)
                need(projection(unchanged) == projection(public) and
                     self.verify_files(unchanged) == before_files, "REHEARSAL_PUBLIC_DRIFT")
                self.journal.value["state"] = "REHEARSED_DISCARDED_NOT_PUBLISHED"
            else:
                self.ready = True
                draft_etag = draft_headers.get("etag")
                need(isinstance(draft_etag, str) and draft_etag, "DRAFT_REVISION_REQUIRED")
                self.call("POST", self.base + "/draft/actions/publish", {202}, authenticated=True,
                          etag=draft_etag)
                self.owned = False
                _, final, _ = self.call("GET", self.base, {200})
                native_record(final)
                need(str(final["id"]) == self.item["id"] and
                     projection(final) == expected, "FINAL_METADATA_DIFF_MISMATCH")
                need(self.verify_files(final) == before_files, "FINAL_FILE_BYTES_DRIFT")
                self.journal.value["state"] = "PUBLISHED_METADATA_AND_BYTES_VERIFIED"
                self.journal.value["final_metadata_sha256"] = digest(final["metadata"])
            self.journal.save()
        except Exception as error:
            code = str(error) if isinstance(error, Hold) else "ACTION_UNKNOWN"
            self.journal.fail(code)
            if self.owned:
                try:
                    self.discard()
                except Exception:
                    self.journal.value["cleanup_confirmed"] = False
                    self.journal.save()
            raise Hold(self.journal.value["first_failure"]) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--expected-plan-sha256", required=True)
    parser.add_argument("--admission", required=True)
    parser.add_argument("--expected-admission-sha256", required=True)
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--core-root", required=True)
    parser.add_argument("--journal-dir", required=True)
    parser.add_argument("--mode", required=True, choices=("rehearse", "apply"))
    args = parser.parse_args()
    try:
        plan = read_json(args.plan, args.expected_plan_sha256)
        receipt = read_json(args.admission, args.expected_admission_sha256)
        source_path = Path(__file__).resolve(strict=True)
        source_sha = hashlib.sha256(regular_bytes(source_path)).hexdigest()
        token_path = None
        def cas(deadline=WHOLE_ACTION_STARTED + ACTIVE_SECONDS):
            stable_bytes(args.plan, args.expected_plan_sha256, deadline)
            stable_bytes(source_path, source_sha, deadline)
            stable_bytes(args.admission, args.expected_admission_sha256, deadline)
            need(time.monotonic() < deadline, "ACTION_CAP")
            admit(plan, args.expected_plan_sha256, source_path, receipt, deadline)
            if token_path is not None:
                need(token_path.resolve(strict=True) == token_path, "CREDENTIAL_PATH_SCOPE")
                stable_bytes(token_path, plan["credential_source_sha256"], deadline)
            need(time.monotonic() < deadline, "ACTION_CAP")
        cas()
        need(args.mode in receipt["allowed_modes"], "ACTION_MODE_NOT_AUTHORIZED")
        need(str(Path(args.core_root).resolve(strict=True)) == plan["core_root"],
             "AUTHORIZED_CORE_ROOT_REQUIRED")
        need(str(Path(args.journal_dir).resolve(strict=True)) == plan["journal_dir"],
             "AUTHORIZED_CLAIM_LOG_REQUIRED")
        token_path = Path(plan["core_root"]) / TOKEN_RELATIVE
        items = [r for r in plan["records"] if r["id"] == args.record_id]
        need(len(items) == 1, "RECORD_NOT_IN_EXACT_PLAN")
        journal = Journal(args.journal_dir, args.record_id, args.expected_plan_sha256, args.mode)
        try:
            token = credential(args.core_root, plan["credential_source_sha256"])
            Action(plan, items[0], journal, Transport(token), cas, WHOLE_ACTION_STARTED).run(args.mode)
        except Hold as error:
            journal.fail(str(error))
            raise
        print(json.dumps({"record_id": args.record_id, "state": journal.value["state"]}))
    except Hold as error:
        print(json.dumps({"state": "HOLD", "code": str(error)}))
        return 2
    except Exception:
        print(json.dumps({"state": "HOLD", "code": "CLOSED_INPUT_OR_RUNTIME_FAILURE"}))
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
