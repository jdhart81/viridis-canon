#!/usr/bin/env python3
"""Stage approved exact Canon bytes and use the existing protected Git mechanism.

No Zenodo publisher, inferred DOI mapping, license assignment, certificate
issuance, direct main push, administrator bypass or review approval is provided.
Default mode is preparation. Apply consumes an existing-authority Root scope
review, exact package/head/check bindings and any scheduled review it requires.
"""
from __future__ import annotations
from dataclasses import dataclass
import datetime as dt
import hashlib
import importlib.util
import json
import os
import selectors
import signal
import subprocess
import threading
import time
from pathlib import Path
import re
import shutil
import sys
import tempfile
from types import SimpleNamespace
import approved_release_continuation as continuation
import protected_pr_merge as protected_merge
import root_scope
from deadline import Budget

sync = continuation.sync
STANDARD = "VRS-TRUSTED-CANON-ADAPTER-1"
SAFE_TARGET = re.compile(r"(?:series/[A-Za-z0-9_./-]+|catalog/(?:config|publications)\.json|docs/data/[A-Za-z0-9_-]+\.json)")


class GuardQuiescenceHold(BaseException):
    """No later mutation may proceed after an unproved owned-child cleanup."""


class BoundedGuard:
    """Run unchanged guarded-client functions in one owned bounded process group.

    Credential arguments/results remain in memory. Only bounded JSON crosses a
    private pipe; exception text and child stdout/stderr are never forwarded.
    The direct child remains unreaped through group cleanup, preventing reuse
    of its PID as an unrelated process-group identifier.
    """
    MAX_RESULT_BYTES = 1024 * 1024

    def __init__(self, guard, budget):
        self._guard, self._budget = guard, budget

    def __getattr__(self, name):
        value = getattr(self._guard, name)
        if not callable(value): return value
        return lambda *args, **kwargs: self._call(value, args, kwargs)

    def _live_descendants(self, pid, *, cleanup=False):
        cap = self._budget.cleanup_remaining_cap(3) if cleanup else self._budget.remaining_cap(3)
        result = subprocess.run(["ps", "-axo", "pid=,pgid=,stat="], text=True, capture_output=True,
                                check=False, timeout=cap)
        sync.require(result.returncode == 0, "HOLD_GUARD_GROUP_OBSERVATION:ps_exit")
        sync.require(len(result.stdout.encode()) < 2 * 1024 * 1024, "HOLD_GUARD_GROUP_OBSERVATION:size")
        leader, live, seen = False, False, set()
        for line in result.stdout.splitlines():
            if not line.strip(): continue
            columns = line.split()
            sync.require(len(columns) == 3 and columns[0].isdigit() and columns[1].isdigit()
                         and re.fullmatch(r"[A-Za-z+<>]+", columns[2]) is not None,
                         "HOLD_GUARD_GROUP_OBSERVATION:malformed_row")
            current, group, status = int(columns[0]), int(columns[1]), columns[2]
            sync.require(current not in seen, "HOLD_GUARD_GROUP_OBSERVATION:duplicate_pid")
            seen.add(current)
            if current == pid:
                sync.require(group == pid and status.startswith("Z"), "HOLD_GUARD_GROUP_LEADER_OBSERVATION")
                leader = True
            elif group == pid and not status.startswith("Z"): live = True
        sync.require(leader, "HOLD_GUARD_GROUP_LEADER_OBSERVATION")
        return live

    @staticmethod
    def _exited(pid):
        return os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)

    @staticmethod
    def _signal(pid, isolated, number):
        try:
            if isolated: os.killpg(pid, number)
            else: os.kill(pid, number)
        except ProcessLookupError: pass

    def _cleanup(self, pid, isolated):
        # The unreaped leader reserves the PID/PGID throughout TERM/KILL.
        try:
            exited = self._exited(pid)
            if exited is not None and (not isolated or not self._live_descendants(pid, cleanup=True)):
                os.waitpid(pid, 0); return
            self._signal(pid, isolated, signal.SIGTERM)
            until = time.monotonic() + self._budget.cleanup_remaining_cap(1)
            while time.monotonic() < until:
                exited = self._exited(pid)
                if exited is not None and (not isolated or not self._live_descendants(pid, cleanup=True)):
                    os.waitpid(pid, 0); return
                time.sleep(min(0.01, self._budget.cleanup_remaining_cap(0.01)))
            self._signal(pid, isolated, signal.SIGKILL)
            while True:
                self._budget.cleanup_remaining_cap(0.01)
                exited = self._exited(pid)
                if exited is not None and (not isolated or not self._live_descendants(pid, cleanup=True)):
                    os.waitpid(pid, 0); return
                time.sleep(min(0.01, self._budget.cleanup_remaining_cap(0.01)))
        except BaseException:
            try: self._signal(pid, isolated, signal.SIGKILL)
            except BaseException: pass
            # No blocking reap once the shared cleanup reserve is exhausted.
            try:
                exited = self._exited(pid)
                if exited is not None: os.waitpid(pid, 0)
            except BaseException: pass
            raise GuardQuiescenceHold("HOLD_GUARD_OWNED_GROUP_QUIESCENCE_UNPROVED") from None

    def _call(self, function, args, kwargs):
        self._budget.require_remaining()
        sync.require(os.name == "posix" and hasattr(os, "fork") and hasattr(os, "WNOWAIT")
                     and threading.current_thread() is threading.main_thread() and threading.active_count() == 1
                     and signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL,
                     "HOLD_GUARD_POSIX_SINGLE_THREAD_REQUIRED")
        read_fd, write_fd = os.pipe()
        ack_read, ack_write = os.pipe()
        try: pid = os.fork()
        except BaseException:
            os.close(read_fd); os.close(write_fd); os.close(ack_read); os.close(ack_write); raise
        if pid == 0:
            os.close(read_fd); os.close(ack_write)
            def emit(value):
                raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode() + b"\n"
                if len(raw) > self.MAX_RESULT_BYTES: raise ValueError()
                while raw:
                    written = os.write(write_fd, raw); raw = raw[written:]
            try:
                os.setsid(); emit({"ready": os.getpid()})
                if os.read(ack_read, 1) != b"G": raise ValueError()
                os.close(ack_read)
                sink = os.open(os.devnull, os.O_WRONLY)
                os.dup2(sink, 1); os.dup2(sink, 2); os.close(sink)
                value = function(*args, **kwargs)
                if isinstance(value, subprocess.CompletedProcess):
                    value = {"wire_type": "process", "returncode": value.returncode,
                             "stdout": value.stdout, "stderr": value.stderr}
                else: value = {"wire_type": "json", "value": value}
                emit({"ok": True, "result": value})
            except BaseException:
                try: emit({"ok": False})
                except BaseException: pass
            finally:
                os.close(write_fd); os._exit(0)
        os.close(write_fd); os.close(ack_read); isolated = False; reaped = False
        os.set_blocking(read_fd, False)
        try:
            frames, buffer, total, eof = [], b"", 0, False
            with selectors.DefaultSelector() as selector:
                selector.register(read_fd, selectors.EVENT_READ)
                while not eof:
                    self._budget.require_remaining()
                    if not selector.select(self._budget.remaining_cap(0.1)): continue
                    block = os.read(read_fd, 65536)
                    if not block: eof = True; break
                    total += len(block); sync.require(total <= self.MAX_RESULT_BYTES + 128, "HOLD_GUARD_RESULT_SIZE")
                    buffer += block
                    while b"\n" in buffer:
                        frame, buffer = buffer.split(b"\n", 1)
                        value = json.loads(frame)
                        frames.append(value)
                        if len(frames) == 1:
                            sync.require(value == {"ready": pid}, "HOLD_GUARD_SESSION_HANDSHAKE")
                            isolated = True
                            os.write(ack_write, b"G"); os.close(ack_write); ack_write = -1
                        else: sync.require(len(frames) == 2, "HOLD_GUARD_RESULT_FRAME")
            sync.require(not buffer and len(frames) == 2, "HOLD_GUARD_RESULT_FRAME")
            while self._exited(pid) is None:
                self._budget.sleep(0.005)
            status = self._exited(pid)
            sync.require(status.si_code == os.CLD_EXITED and status.si_status == 0
                         and not self._live_descendants(pid), "HOLD_GUARD_GROUP_NOT_QUIESCENT")
            os.waitpid(pid, 0); reaped = True
            sync.require(frames[1].get("ok") is True, "HOLD_GUARDED_CLIENT_OPERATION")
            value = frames[1]["result"]
            if value.get("wire_type") == "process":
                return subprocess.CompletedProcess([], value["returncode"], value["stdout"], value["stderr"])
            sync.require(value.get("wire_type") == "json", "HOLD_GUARD_RESULT_FRAME")
            return value["value"]
        except BaseException:
            if not reaped: self._cleanup(pid, isolated); reaped = True
            raise
        finally:
            os.close(read_fd)
            if ack_write != -1: os.close(ack_write)


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_target(value):
    sync.require(isinstance(value, str) and SAFE_TARGET.fullmatch(value) and ".." not in Path(value).parts
                 and not Path(value).is_absolute() and not value.endswith("/"), "HOLD_CANON_TARGET_SCOPE")
    sync.require(Path(value).suffix.lower() not in {".py", ".js", ".ts", ".sh", ".pem", ".key"}, "HOLD_CANON_TARGET_SCOPE")
    sync.require(Path(value).name != "function.json", "HOLD_CANON_RUNTIME_MANIFEST_SCOPE")
    return value


def public_files(record):
    files = record.get("files")
    sync.require(isinstance(files, list) and files, "HOLD_PUBLIC_MANUSCRIPT_FILE_INVENTORY")
    inventory = []
    for row in files:
        sync.require(isinstance(row, dict), "HOLD_PUBLIC_MANUSCRIPT_FILE_INVENTORY")
        name, size = row.get("key", row.get("filename")), row.get("size", row.get("filesize"))
        sync.require(isinstance(name, str) and name and type(size) is int and size >= 0 and isinstance(row.get("checksum"), str),
                     "HOLD_PUBLIC_MANUSCRIPT_FILE_INVENTORY")
        inventory.append({"name": name, "bytes": size, "checksum": row["checksum"]})
    sync.require(len({row["name"] for row in inventory}) == len(inventory), "HOLD_PUBLIC_MANUSCRIPT_FILE_INVENTORY")
    return sorted(inventory, key=lambda row: row["name"])


def require_exact_approval(approval, *, root, approval_path, publication_sha256, payload_sha256, adapter_sha256):
    # This is an owning Root technical review under existing publication
    # authority. It never asserts a newly supplied human exact-head approval.
    scope = root_scope.load(root, approval_path, require_canon=True)
    required = {"publication_receipt_sha256": publication_sha256,
                "payload_manifest_sha256": payload_sha256, "adapter_source_sha256": adapter_sha256}
    capability = scope.get("canon_package")
    sync.require(isinstance(capability, dict) and all(capability.get(key) == value for key, value in required.items()),
                 "HOLD_EXACT_ROOT_CANON_PACKAGE_SCOPE_REQUIRED")
    return scope


def build_route_binding(*, root, publication_receipt, owner_approval, payload_manifest,
                        implementation_source, adapter_id, stage=False):
    """Generate a deterministic binding only from an exact explicit approval."""
    root = Path(root).resolve(strict=True)
    paths = {key: sync.regular(value, root) for key, value in {
        "publication_receipt": publication_receipt, "owner_approval": owner_approval,
        "canon_payload_manifest": payload_manifest, "implementation_source": implementation_source}.items()}
    sync.require(sync.file_hash(paths["implementation_source"]) == sync.file_hash(Path(__file__)), "HOLD_TRUSTED_ADAPTER_EXECUTING_SOURCE")
    kind, _ = sync.publication_dois(sync.object_file(paths["publication_receipt"]))
    sync.require(kind in {"methods-digest", "successor-wave"}, "HOLD_CONTINUATION_PUBLISHER_FORMAT")
    sync.require(isinstance(adapter_id, str) and bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", adapter_id)), "HOLD_CANON_ADAPTER_ID")
    approval = sync.object_file(paths["owner_approval"])
    scope = require_exact_approval(approval, root=root, approval_path=paths["owner_approval"], publication_sha256=sync.file_hash(paths["publication_receipt"]),
                           payload_sha256=sync.file_hash(paths["canon_payload_manifest"]), adapter_sha256=sync.file_hash(paths["implementation_source"]))
    bindings = {key: {"path": str(path.relative_to(root)), "sha256": sync.file_hash(path)} for key, path in paths.items()}
    value = {"standard": continuation.STANDARD, "status": "OWNER_REVIEWED_PACKAGE_BINDING", "publisher_format": kind,
        "owner_approval": bindings["owner_approval"], "publication_receipt": bindings["publication_receipt"],
        "canon_payload_manifest": bindings["canon_payload_manifest"], "owner_canon_adapter": {"adapter_id": adapter_id,
            "reviewed_payload_sha256": bindings["canon_payload_manifest"]["sha256"], "implementation_source": bindings["implementation_source"]}}
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    identity = sha_bytes(raw)
    path = root / "reports/approved-canon-route-bindings" / (identity + ".json")
    if stage:
        root_scope.require_mutation_authority(scope)
        continuation.checkpoint_once(path, value)
    return {"binding": value, "sha256": identity, "path": path, "writes_performed": stage}


def prepare_package(*, root, publication_receipt, route_binding, expected_binding_sha256, stage=False):
    """Deterministically copy an explicitly approved complete Git payload."""
    root = Path(root).resolve(strict=True)
    checked = continuation.validate_binding(root, publication_receipt, route_binding, expected_binding_sha256)
    executing_sha = sync.file_hash(Path(__file__))
    implementation = checked["binding"]["owner_canon_adapter"]["implementation_source"]
    sync.require(implementation["sha256"] == executing_sha, "HOLD_TRUSTED_ADAPTER_EXECUTING_SOURCE")
    require_exact_approval(sync.object_file(checked["approval"]), root=root, approval_path=checked["approval"],
        publication_sha256=checked["binding"]["publication_receipt"]["sha256"],
        payload_sha256=sync.file_hash(checked["payload"]), adapter_sha256=executing_sha)
    payload = sync.object_file(checked["payload"])
    required = {"canon_repository", "base_commit", "expected_catalog_digest", "release_date", "git_files", "protected_guard", "guard_dependencies", "released_public_records"}
    missing = sorted(required - set(payload))
    sync.require(not missing, "HOLD_CANON_ADAPTER_FIELDS_REQUIRED:" + ",".join(missing))
    sync.require(payload["canon_repository"] == sync.REPOSITORY, "HOLD_CANON_REPOSITORY")
    sync.require(sync.SHA40.fullmatch(str(payload["base_commit"])) and sync.SHA64.fullmatch(str(payload["expected_catalog_digest"])),
                 "HOLD_CANON_RELEASE_PINS")
    try:
        release_date = dt.date.fromisoformat(payload["release_date"])
    except (ValueError, TypeError):
        raise sync.SyncHold("HOLD_CANON_RELEASE_DATE") from None
    sync.require(str(release_date) == payload["release_date"], "HOLD_CANON_RELEASE_DATE")
    guard = continuation.bound_file(root, payload["protected_guard"])
    sync.require(guard == root / "_ZENODO_DEPOSITS/weekend_canon_lockstep.py", "HOLD_EXISTING_PROTECTED_GUARD_REQUIRED")
    dependencies = payload["guard_dependencies"]
    sync.require(isinstance(dependencies, list) and dependencies, "HOLD_GUARD_CLOSURE_REQUIRED")
    dependency_paths = [continuation.bound_file(root, row) for row in dependencies]
    sync.require(root / "_ZENODO_DEPOSITS/release_coherence.py" in dependency_paths, "HOLD_GUARD_CLOSURE_REQUIRED")
    snapshots = payload["released_public_records"]
    sync.require(isinstance(snapshots, list) and len(snapshots) == len(checked["published_dois"]), "HOLD_RELEASED_PUBLIC_METADATA_REQUIRED")
    public_records = {}
    for row in snapshots:
        sync.require(isinstance(row, dict) and set(row) == {"doi", "snapshot"} and row.get("doi") in checked["published_dois"]
                     and row["doi"] not in public_records, "HOLD_RELEASED_PUBLIC_METADATA_REQUIRED")
        record = sync.object_file(continuation.bound_file(root, row["snapshot"]))
        sync.require(str(record.get("id")) == sync.DOI.fullmatch(row["doi"]).group(1) and record.get("doi") == row["doi"]
                     and isinstance(record.get("metadata"), dict), "HOLD_RELEASED_PUBLIC_RECORD_IDENTITY")
        public_files(record)
        public_records[row["doi"]] = record
    rows = payload["git_files"]
    sync.require(isinstance(rows, list) and rows, "HOLD_CANON_GIT_FILES_REQUIRED")
    files, frozen = [], {}
    for row in rows:
        sync.require(isinstance(row, dict) and set(row) == {"source", "target_path"}, "HOLD_CANON_GIT_FILE_BINDING")
        source = continuation.bound_file(root, row["source"])
        target = safe_target(row["target_path"])
        sync.require(target not in frozen, "HOLD_CANON_DUPLICATE_TARGET")
        raw = source.read_bytes()
        sync.require(sha_bytes(raw) == row["source"]["sha256"], "HOLD_CANON_SOURCE_RACE")
        frozen[target] = raw
        files.append({"source_path": str(source.relative_to(root)), "target_path": target, "sha256": sha_bytes(raw)})
    sync.require("docs/data/catalog.json" in frozen and "catalog/config.json" in frozen, "HOLD_APPROVED_COMPLETE_CATALOG_REQUIRED")
    try:
        catalog = json.loads(frozen["docs/data/catalog.json"])
    except (TypeError, ValueError):
        raise sync.SyncHold("HOLD_APPROVED_CATALOG_JSON") from None
    catalog_rows = sync.catalog_rows(catalog)
    root_scope.validate_w42_mapping(root, checked["root_scope"], payload, catalog_rows=catalog_rows)
    sync.require(catalog["catalog_digest"] == payload["expected_catalog_digest"], "HOLD_APPROVED_CATALOG_DIGEST")
    sync.require(checked["published_dois"].issubset({row.get("doi") for row in catalog_rows.values()}),
                 "HOLD_APPROVED_CATALOG_PUBLICATION_MAPPING")
    # Require the explicit child map to agree with the approved catalog bytes;
    # never derive IDs, status, proof labels or backing DOIs in this adapter.
    for parent in payload["publication_mappings"]:
        sync.require(isinstance(parent.get("title"), str) and parent["title"] and isinstance(parent.get("abbreviation"), str)
                     and re.fullmatch(r"[A-Z0-9_-]+", parent["abbreviation"]), "HOLD_CANON_PARENT_METADATA_REQUIRED")
        sync.require(parent["title"] == public_records[parent["parent_doi"]]["metadata"].get("title"),
                     "HOLD_APPROVED_PUBLIC_TITLE_MAPPING")
        for child in parent["children"]:
            row = catalog_rows.get(child["canon_record_id"])
            sync.require(isinstance(row, dict) and row.get("doi") == child["backing_doi"]
                         and row.get("source_sha256") == child["source_sha256"], "HOLD_APPROVED_CHILD_CATALOG_MAPPING")
            sync.require(row.get("path") in frozen and sha_bytes(frozen[row["path"]]) == child["source_sha256"],
                         "HOLD_APPROVED_CHILD_GIT_SOURCE_REQUIRED")
    plan = {"standard": STANDARD, "status": "APPROVED_CANON_PACKAGE_PREPARED",
            "route_binding_sha256": expected_binding_sha256, "payload_sha256": sync.file_hash(checked["payload"]),
            "base_commit": payload["base_commit"], "catalog_digest": payload["expected_catalog_digest"],
            "release_date": payload["release_date"], "files": sorted(files, key=lambda row: row["target_path"]),
            "publication_dois": sorted(checked["published_dois"]), "publisher_invocations": 0, "zenodo_mutations": 0,
            "license_or_certification_inferred": False, "public_actions_performed": False}
    directory = root / "reports/approved-canon-packages" / expected_binding_sha256
    if stage:
        root_scope.require_mutation_authority(checked["root_scope"])
        sync.require(not any(p.is_symlink() for p in (directory, *directory.parents)), "HOLD_CANON_STAGE_SYMLINK")
        for row in plan["files"]:
            destination = directory / "payload" / row["target_path"]
            sync.require(not any(p.is_symlink() for p in (destination, *destination.parents)), "HOLD_CANON_STAGE_SYMLINK")
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                sync.require(destination.is_file() and sync.file_hash(destination) == row["sha256"], "HOLD_CANON_STAGE_CONFLICT")
            else:
                with destination.open("xb") as stream:
                    stream.write(frozen[row["target_path"]])
        sync.atomic_receipt(directory / "PACKAGE_MANIFEST.json", plan)
    return {"plan": plan, "directory": directory, "frozen": frozen, "checked": checked, "payload": payload, "public_records": public_records}


def load_existing_guard(root, payload):
    """Import only the fixed existing guard role after complete source checks."""
    guard_path = continuation.bound_file(root, payload["protected_guard"])
    dependencies = payload["guard_dependencies"]
    for row in dependencies:
        continuation.bound_file(root, row)
    prior = list(sys.path)
    try:
        sys.path.insert(0, str(guard_path.parent))
        spec = importlib.util.spec_from_file_location("_approved_existing_canon_guard", guard_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = prior
    sync.require(Path(module.ROOT).resolve() == root, "HOLD_EXISTING_GUARD_ROOT")
    coherence = module.release_coherence
    sync.require(Path(coherence.__file__).resolve() == root / "_ZENODO_DEPOSITS/release_coherence.py", "HOLD_GUARD_IMPORT_ROLE")
    continuation.bound_file(root, payload["protected_guard"])
    for row in dependencies:
        continuation.bound_file(root, row)
    return module


def preserve_public_history(repo, package):
    """Require additive DOI/source history and unchanged nonspine policy."""
    old_catalog = sync.object_file(repo / "docs/data/catalog.json")
    new_catalog = json.loads(package["frozen"]["docs/data/catalog.json"])
    old_rows, new_rows = sync.catalog_rows(old_catalog), sync.catalog_rows(new_catalog)
    sync.require(set(old_rows).issubset(new_rows), "HOLD_HISTORICAL_CANON_RECORD_REMOVAL")
    mapped = {parent["parent_canon_publication_id"] for parent in package["payload"]["publication_mappings"]}
    mapped.update(child["canon_record_id"] for parent in package["payload"]["publication_mappings"] for child in parent["children"])
    sync.require(all(old_rows[key] == new_rows[key] for key in old_rows if key not in mapped), "HOLD_UNRELATED_CANON_RECORD_CHANGE")
    sync.require(all(old_catalog.get(key) == new_catalog.get(key) for key in ("concept_doi", "release")), "HOLD_CANON_SPINE_CHANGE")
    old_config = sync.object_file(repo / "catalog/config.json")
    new_config = json.loads(package["frozen"]["catalog/config.json"])
    appendable = {"doi_by_path", "curation"}
    sync.require(isinstance(new_config, dict)
                 and {key: value for key, value in old_config.items() if key not in appendable} ==
                     {key: value for key, value in new_config.items() if key not in appendable}, "HOLD_CANON_POLICY_CHANGE")
    old_curation, new_curation = old_config.get("curation", {}), new_config.get("curation", {})
    sync.require(isinstance(old_curation, dict) and isinstance(new_curation, dict)
                 and all(new_curation.get(key) == value for key, value in old_curation.items()),
                 "HOLD_EXISTING_CANON_CURATION_CHANGE")
    old_paths = {row.get("path") for row in old_rows.values()}
    new_paths = {row.get("path") for row in new_rows.values()} - old_paths
    added_curation = set(new_curation) - set(old_curation)
    sync.require(added_curation.issubset(new_paths & set(package["frozen"]))
                 and all(isinstance(new_curation[key], dict) for key in added_curation),
                 "HOLD_NEW_CANON_CURATION_SCOPE")
    for key in set(new_rows) - set(old_rows):
        row = new_rows[key]
        coverage = row.get("metadata", {}).get("verification_coverage") or {}
        sync.require(row.get("status") == "working" and row.get("integrity") != "gate-passed"
                     and row.get("tier") != "spine" and not {"verified", "spine"}.intersection(row.get("tags", []))
                     and coverage.get("canon_eligible") is not True,
                     "HOLD_NEW_SOURCE_CANNOT_GAIN_SCIENTIFIC_ADMISSION")
    old_dois, new_dois = old_config.get("doi_by_path", {}), new_config.get("doi_by_path", {})
    sync.require(isinstance(old_dois, dict) and isinstance(new_dois, dict)
                 and all(new_dois.get(key) == value for key, value in old_dois.items()), "HOLD_EXISTING_DOI_MAPPING_CHANGE")
    for target, raw in package["frozen"].items():
        path = repo / target
        if target.startswith("series/") and target != "series/README.md" and path.exists():
            sync.require(path.is_file() and not path.is_symlink() and path.read_bytes() == raw, "HOLD_EXISTING_SCIENCE_BYTES_IMMUTABLE")


class ProtectedCanonTransaction:
    """Reuse existing guarded credentials, Git/PR, CI, Pages and byte readback."""
    def run(self, root, package, *, budget):
        budget.require_remaining()
        root_scope.require_mutation_authority(package["checked"]["root_scope"])
        protected_merge.require_approval(package)  # Before existing credentials or public work.
        guard = BoundedGuard(load_existing_guard(root, package["payload"]), budget)
        plan, payload = package["plan"], package["payload"]
        token = guard.read_github_token()  # Existing guarded client only; never returned or logged.
        branch = "canon/approved-" + plan["route_binding_sha256"][:20]
        with tempfile.TemporaryDirectory(prefix="approved-canon-") as scratch:
            repo = Path(scratch).resolve(strict=True) / "viridis-canon"
            guard.run(["git", "clone", "--quiet", guard.TOKEN_REPO_URL.format(token=token), str(repo)], secrets=(token,))
            main_commit = guard.git(repo, "rev-parse", "HEAD", token=token).stdout.strip()
            matches = all((repo / path).is_file() and sync.file_hash(repo / path) == sha_bytes(raw)
                          for path, raw in package["frozen"].items())
            sync.require(matches or main_commit == plan["base_commit"], "HOLD_CANON_BASE_COMMIT_DRIFT")
            preserve_public_history(repo, package)
            pr_url, source_commit = None, main_commit
            if not matches:
                protected_merge.require_repository_policy(guard, token, package)
                new_branch = False
                exists = guard.git(repo, "ls-remote", "--exit-code", "--heads", "origin", "refs/heads/" + branch,
                                   token=token, check=False)
                if exists.returncode == 0:
                    guard.git(repo, "fetch", "--quiet", "origin", branch, token=token)
                    guard.git(repo, "checkout", "--quiet", "--detach", "FETCH_HEAD", token=token)
                    sync.require(guard.git(repo, "merge-base", "--is-ancestor", plan["base_commit"], "HEAD", token=token, check=False).returncode == 0,
                                 "HOLD_CANON_BRANCH_BASE_CONFLICT")
                    changed = guard.git(repo, "diff", "--name-only", plan["base_commit"], "HEAD", token=token).stdout.splitlines()
                    sync.require(set(changed).issubset(package["frozen"]), "HOLD_CANON_BRANCH_SCOPE_CONFLICT")
                    sync.require(all((repo / path).is_file() and sync.file_hash(repo / path) == sha_bytes(raw)
                                     for path, raw in package["frozen"].items()), "HOLD_CANON_BRANCH_CONTENT_CONFLICT")
                else:
                    new_branch = True
                    sync.require(exists.returncode == 2, "HOLD_CANON_BRANCH_READBACK")
                    guard.git(repo, "checkout", "--quiet", "-b", branch, token=token)
                    for path, raw in package["frozen"].items():
                        destination = repo / path
                        sync.require(not any(p.is_symlink() for p in (destination, *destination.parents)), "HOLD_CANON_REPO_SYMLINK")
                        destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
                    guard.preflight_release(repo)  # Check only; never regenerate approved payload bytes.
                    sync.require(all((repo / path).is_file() and sync.file_hash(repo / path) == sha_bytes(raw)
                                     for path, raw in package["frozen"].items()), "HOLD_CANON_PREFLIGHT_PAYLOAD_DRIFT")
                    guard.git(repo, "add", "--", *sorted(package["frozen"]), token=token)
                    command, environment = protected_merge.commit_command(repo, plan["payload_sha256"], plan["release_date"])
                    guard.run(command, env=environment, secrets=(token,))
                source_commit = guard.git(repo, "rev-parse", "HEAD", token=token).stdout.strip()
                protected_merge.require_approval(package, source_commit)
                if new_branch:
                    guard.git(repo, "push", "origin", "HEAD:refs/heads/" + branch, token=token)
                viewed = guard.gh("pr", "view", branch, "--repo", sync.REPOSITORY, "--json", "url,state,headRefOid",
                                  token=token, check=False)
                if viewed.returncode == 0:
                    pr = json.loads(viewed.stdout)
                    sync.require(pr.get("headRefOid") == source_commit and pr.get("state") in {"OPEN", "MERGED"}, "HOLD_CANON_PR_IDENTITY")
                    pr_url = pr["url"]
                else:
                    body = repo / ".git/approved-publication-body.md"
                    body.write_text("Mirrors the explicitly approved publication payload.\n\nDOIs: " + ", ".join(plan["publication_dois"]) +
                                    "\n\nNo Zenodo publication, source relabeling, runtime admission or deployment occurs.\n")
                    created = guard.gh("pr", "create", "--repo", sync.REPOSITORY, "--base", "main", "--head", branch,
                                       "--title", "canon: approved publication " + plan["route_binding_sha256"][:12],
                                       "--body-file", str(body), token=token)
                    pr_url = created.stdout.strip()
                main_commit = protected_merge.merge_approved_pr(guard, token, package, pr_url, source_commit, budget=budget)
            workflows = guard.wait_for_main_workflows(main_commit, token)
            hashes = {path: sha_bytes(raw) for path, raw in package["frozen"].items()}
            verified = guard.verify_public("main", main_commit, hashes)
            sync.require(verified == hashes, "HOLD_CANON_PUBLIC_SOURCE_READBACK")
            catalog_rows = sync.catalog_rows(json.loads(package["frozen"]["docs/data/catalog.json"]))
            bundles = []
            for row in payload["publication_mappings"]:
                bundles.append(SimpleNamespace(doi=row["parent_doi"], payload=(), payload_targets=()))
                for child in row["children"]:
                    target = catalog_rows[child["canon_record_id"]]["path"]
                    bundles.append(SimpleNamespace(doi=child["backing_doi"], payload=(Path(target),), payload_targets=(target,)))
            catalog_url = guard.verify_pages(plan["catalog_digest"], bundles)
            return {"commit_sha": main_commit, "proposed_source_commit_sha": source_commit,
                    "pull_request_url": pr_url, "workflows": workflows, "sha256": hashes, "public_catalog_url": catalog_url}


@dataclass
class ApprovedCanonAdapter:
    apply: bool = False
    transaction: object = None
    http: object = sync.http_json

    def __call__(self, *, root, publication_receipt, route_binding, expected_binding_sha256, budget=None):
        budget = budget or Budget()
        budget.require_remaining()
        root = Path(root).resolve(strict=True)
        package = prepare_package(root=root, publication_receipt=publication_receipt, route_binding=route_binding,
                                  expected_binding_sha256=expected_binding_sha256)
        implementation = package["checked"]["binding"]["owner_canon_adapter"]["implementation_source"]
        sync.require(implementation["sha256"] == sync.file_hash(Path(__file__)), "HOLD_TRUSTED_ADAPTER_EXECUTING_SOURCE")
        if not self.apply:
            return package["plan"]
        root_scope.require_mutation_authority(package["checked"]["root_scope"])
        protected_merge.require_approval(package)
        package = prepare_package(root=root, publication_receipt=publication_receipt, route_binding=route_binding,
                                  expected_binding_sha256=expected_binding_sha256, stage=True)
        for doi, snapshot in package["public_records"].items():
            actual = sync.get(self.http, "https://zenodo.org/api/records/" + sync.DOI.fullmatch(doi).group(1), budget=budget)
            sync.require(actual.get("id") == snapshot.get("id") and actual.get("doi") == doi
                         and actual.get("metadata") == snapshot["metadata"] and public_files(actual) == public_files(snapshot),
                         "HOLD_RELEASED_PUBLIC_METADATA_DRIFT")
        result = (self.transaction or ProtectedCanonTransaction()).run(root, package, budget=budget)
        sync.require(isinstance(result, dict) and sync.SHA40.fullmatch(str(result.get("commit_sha", "")))
                     and result.get("public_catalog_url") == sync.CATALOG_URL, "HOLD_PROTECTED_CANON_RESULT")
        workflows = result.get("workflows")
        required_workflows = {"viridis-canon-ci", "research-catalog-and-pages"}
        sync.require(isinstance(workflows, list) and required_workflows.issubset({row.get("name") for row in workflows if isinstance(row, dict)})
                     and all(isinstance(row, dict) and row.get("status") == "completed" and row.get("conclusion") == "success"
                             and row.get("headSha", result["commit_sha"]) == result["commit_sha"] for row in workflows), "HOLD_CANON_REQUIRED_WORKFLOWS")
        sync.require(result.get("sha256") == {path: sha_bytes(raw) for path, raw in package["frozen"].items()},
                     "HOLD_CANON_SOURCE_HASH_RECEIPT")
        # Reconsume approval, source bytes and explicit mappings after Git work.
        fresh = prepare_package(root=root, publication_receipt=publication_receipt, route_binding=route_binding,
                                expected_binding_sha256=expected_binding_sha256)
        sync.require(fresh["plan"] == package["plan"], "HOLD_CANON_INPUT_RACE")
        plan = package["plan"]
        receipt = {"schema_version": 2, "status": "verified", "repository": sync.REPOSITORY, "branch": "main", "spine_changed": False,
                   "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "commit_sha": result["commit_sha"],
                   "source_commit_sha": result["commit_sha"], "proposed_source_commit_sha": result.get("proposed_source_commit_sha"),
                   "catalog_digest": plan["catalog_digest"], "public_catalog_url": sync.CATALOG_URL,
                   "workflows": result.get("workflows"), "pull_request_url": result.get("pull_request_url"), "sha256": result.get("sha256"),
                   "approved_payload_sha256": plan["payload_sha256"], "route_binding_sha256": expected_binding_sha256,
                   "release_date": plan["release_date"],
                   "bundles": [{"abbreviation": row["abbreviation"], "title": row["title"], "doi": row["parent_doi"]}
                               for row in package["payload"]["publication_mappings"]]}
        path = root / "_ZENODO_DEPOSITS/LOCKSTEP_RECEIPTS" / (plan["release_date"] + "--" + expected_binding_sha256 + ".json")
        if path.exists():
            old = sync.object_file(sync.regular(path, root))
            # A prior closure survives a crash before the outer continuation
            # checkpoint. Fresh readback above proves the approved bytes remain
            # public; later main commits, PR discovery and workflow reruns must
            # not replace the historical provenance stored in this receipt.
            observations = {"verified_at_utc", "commit_sha", "source_commit_sha", "proposed_source_commit_sha",
                            "workflows", "pull_request_url"}
            sync.require(set(old) == set(receipt)
                         and {key: value for key, value in old.items() if key not in observations} ==
                             {key: value for key, value in receipt.items() if key not in observations},
                         "HOLD_CANON_RECEIPT_COLLISION")
            old_commit = old.get("commit_sha")
            sync.require(sync.SHA40.fullmatch(str(old_commit)) and old.get("source_commit_sha") == old_commit
                         and sync.SHA40.fullmatch(str(old.get("proposed_source_commit_sha")))
                         and (old.get("pull_request_url") is None or
                              re.fullmatch(r"https://github\.com/jdhart81/viridis-canon/pull/[1-9][0-9]*", str(old["pull_request_url"])))
                         and isinstance(old.get("verified_at_utc"), str) and old["verified_at_utc"],
                         "HOLD_CANON_RECEIPT_COLLISION")
            prior_workflows = old.get("workflows")
            sync.require(isinstance(prior_workflows, list)
                         and required_workflows.issubset({row.get("name") for row in prior_workflows if isinstance(row, dict)})
                         and all(isinstance(row, dict) and row.get("status") == "completed" and row.get("conclusion") == "success"
                                 and row.get("headSha", old_commit) == old_commit for row in prior_workflows),
                         "HOLD_CANON_RECEIPT_COLLISION")
        else:
            continuation.checkpoint_once(path, receipt)
        return {"status": "VERIFIED_CANON_CLOSURE", "adapter_id": package["checked"]["binding"]["owner_canon_adapter"]["adapter_id"],
                "payload_sha256": plan["payload_sha256"], "canon_receipt": {"path": str(path.relative_to(root)), "sha256": sync.file_hash(path)}}
