"""Source-bound, parent-supervised raw OWNER HTTP transport.

No scientific function, SCI ContextVar, certificate or canonical writer is
called here.  All authority-bearing scientific/public predicates stay in the
master.  Pipes contain raw transport material, never an admission result.

The framing helpers are also available to the separate scientific worker.
They use owned integer descriptors and os.read/write, without io.open(PIPE).
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import email.message
import fcntl
import hashlib
import http.client
import io
import importlib.machinery
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import ssl
import stat
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
from collections import deque
from collections.abc import Mapping


MAX_FRAME = 65536
CHUNK_BYTES = 32768
MAX_METADATA_BYTES = 16 * 1024 * 1024
MAX_BUFFERED_CONTENT_BYTES = 1024 * 1024 * 1024
MAX_HTTP_WORKERS = 6
REQUEST_SECONDS = 120.0
OBSERVATION_SECONDS = 900.0
START_SPACING = 2.05
OWNER_ID = '1591505'
FIXED_CANONICAL_ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
NATIVE_ACCEPT = 'application/vnd.inveniordm.v1+json'
ACCEPTS = frozenset({'application/json', NATIVE_ACCEPT})
MANIFEST_FIELDS = frozenset({'standard', 'canonical_root', 'profile_binding',
    'modules', 'metadata', 'source_origin', 'legacy_closure', 'source_review_change_flags'})
IDENTITY_FIELDS = frozenset({'device', 'inode', 'mode', 'bytes', 'mtime_ns', 'ctime_ns'})
SOURCE_FIELDS = frozenset({'status', 'source_manifest_sha256', 'source_modules',
    'metadata_files', 'transient_restore_allowed', 'scientific_population_admitted', 'certifies'})
KINDS = {'HELLO': 1, 'SOURCE_READY': 2, 'TOKEN': 3, 'READY': 4, 'GRANT': 5,
    'HEADER_ACK': 6, 'RESPONSE': 7, 'DATA': 8, 'SOURCE_FINAL': 9, 'DONE': 10,
    'ERROR': 11}
KIND_NAMES = {value: key for key, value in KINDS.items()}
MODULE_NAMES = frozenset({'packaging_runtime.py', 'invoke_digest_v2.py', 'digest_controller_v2.py',
    'methods_digest_v2.py', 'methods_digest_registration_v3.py', 'manuscript_access_registry.py',
    'manuscript_access_correction.py', 'manuscript_pdf_gate.py', 'publish_dated_bundles_guarded.py',
    'publish_successor_wave_guarded.py', 'packaging_catalog.py', 'install_packaging_runtime.py',
    'packaging_nightly.py', 'nightly_checkpoint_guarded.py', 'packaging_run_flow.py',
    'packaging_nightly_coverage.py', 'packaging_nightly_intake.py',
    'scientific_registration_worker.py', 'owner_content_worker.py'})


class TransportHold(ValueError):
    """Infrastructure/transport failure; never an original scientific HOLD."""


def need(condition, reason):
    if not condition:
        raise TransportHold(reason)


def encode_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')


def decode_json(raw):
    try:
        return json.loads(raw.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise TransportHold('MALFORMED_WORKER_JSON') from exc


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def utc_value(value):
    try:
        parsed = dt.datetime.fromisoformat(value)
        need(parsed.tzinfo is not None and parsed.utcoffset() == dt.timedelta(), 'WORKER_UTC')
        return parsed
    except (TypeError, ValueError) as exc:
        raise TransportHold('WORKER_UTC') from exc


def deadline_check(deadline):
    need(finite(deadline) and time.monotonic() <= deadline, 'ABSOLUTE_WORKER_DEADLINE')


def safe_worker_environment(token=None):
    """HTTP credentials travel only over its anonymous owned token pipe."""
    result = {}
    private = ('TOKEN', 'SECRET', 'PASSWORD', 'CREDENTIAL', 'API_KEY', 'PRIVATE_KEY', 'ACCESS_KEY', 'AUTH')
    for key, value in os.environ.items():
        if any(word in key.upper() for word in private) or (token is not None and token in value):
            continue
        # No caller-selected import search path may outrank the public entry.
        if key in {'PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP'}:
            continue
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class OwnedFD:
    fd: int
    role: str
    identity: tuple

    @classmethod
    def bind(cls, fd, role):
        need(type(fd) is int and fd >= 0 and role in {'read', 'write'}, 'OWNED_PIPE_DESCRIPTOR')
        observed = os.fstat(fd)
        need(stat.S_ISFIFO(observed.st_mode), 'ANONYMOUS_PIPE_REQUIRED')
        access = fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE
        need(access == (os.O_RDONLY if role == 'read' else os.O_WRONLY), 'PIPE_ACCESS_ROLE')
        os.set_blocking(fd, False)
        return cls(fd, role, (observed.st_dev, observed.st_ino, observed.st_mode))

    def check(self):
        observed = os.fstat(self.fd)
        need((observed.st_dev, observed.st_ino, observed.st_mode) == self.identity
            and stat.S_ISFIFO(observed.st_mode), 'OWNED_PIPE_IDENTITY_CHANGED')
        flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
        access = flags & os.O_ACCMODE
        need(access == (os.O_RDONLY if self.role == 'read' else os.O_WRONLY)
            and flags & os.O_NONBLOCK, 'PIPE_ACCESS_ROLE_OR_NONBLOCK_CHANGED')

    def close(self):
        self.check()
        os.close(self.fd)


def pipe_pair():
    read_fd, write_fd = os.pipe()
    try:
        return OwnedFD.bind(read_fd, 'read'), OwnedFD.bind(write_fd, 'write')
    except BaseException:
        os.close(read_fd)
        os.close(write_fd)
        raise


def frame_bytes(payload, kind=None, *, max_bytes=MAX_FRAME):
    need(type(payload) is bytes, 'RAW_FRAME_BYTES_REQUIRED')
    if kind is not None:
        need(kind in KINDS, 'UNKNOWN_FRAME_KIND')
        payload = bytes((KINDS[kind],)) + payload
    need(0 < len(payload) <= max_bytes, 'BOUNDED_FRAME_LENGTH')
    return struct.pack('!I', len(payload)) + payload


class FrameReader:
    def __init__(self, max_bytes=MAX_FRAME, *, tagged=False, max_total_bytes=None):
        need(type(max_bytes) is int and max_bytes > 0, 'FRAME_LIMIT')
        self.max_bytes = max_bytes
        self.tagged = tagged
        self.max_total_bytes = max_total_bytes
        self.total = 0
        self.buffer = bytearray()
        self.length = None

    def feed(self, raw):
        need(type(raw) is bytes, 'RAW_PIPE_READ')
        self.total += len(raw)
        need(self.max_total_bytes is None or self.total <= self.max_total_bytes, 'TOTAL_PIPE_FRAME_LIMIT')
        self.buffer.extend(raw)
        frames = []
        while True:
            if self.length is None:
                if len(self.buffer) < 4:
                    break
                self.length = struct.unpack('!I', self.buffer[:4])[0]
                del self.buffer[:4]
                need(0 < self.length <= self.max_bytes, 'BOUNDED_FRAME_LENGTH')
            if len(self.buffer) < self.length:
                break
            payload = bytes(self.buffer[:self.length])
            del self.buffer[:self.length]
            self.length = None
            if self.tagged:
                need(payload[0] in KIND_NAMES, 'UNKNOWN_FRAME_KIND')
                frames.append((KIND_NAMES[payload[0]], payload[1:]))
            else:
                frames.append(payload)
        return frames

    def finish(self):
        need(not self.buffer and self.length is None, 'PARTIAL_WORKER_FRAME')


def _wait(fd, event, deadline):
    fd.check()
    deadline_check(deadline)
    with selectors.DefaultSelector() as selector:
        selector.register(fd.fd, event)
        selector.select(min(0.05, max(0.0, deadline - time.monotonic())))
    fd.check()
    deadline_check(deadline)


def write_frame(fd, payload, *, deadline, kind=None, max_bytes=MAX_FRAME):
    fd = fd if isinstance(fd, OwnedFD) else OwnedFD.bind(fd, 'write')
    need(fd.role == 'write', 'PIPE_WRITE_ROLE')
    raw = frame_bytes(payload, kind, max_bytes=max_bytes)
    view = memoryview(raw)
    offset = 0
    while offset < len(view):
        fd.check()
        deadline_check(deadline)
        try:
            sent = os.write(fd.fd, view[offset:offset + CHUNK_BYTES])
        except BlockingIOError:
            _wait(fd, selectors.EVENT_WRITE, deadline)
            continue
        need(sent > 0, 'PIPE_WRITE_CLOSED')
        offset += sent
        fd.check()
        deadline_check(deadline)


def read_frame(fd, *, deadline, max_bytes=MAX_FRAME, tagged=False):
    fd = fd if isinstance(fd, OwnedFD) else OwnedFD.bind(fd, 'read')
    need(fd.role == 'read', 'PIPE_READ_ROLE')
    def exact(count):
        chunks = bytearray()
        while len(chunks) < count:
            fd.check()
            deadline_check(deadline)
            try:
                raw = os.read(fd.fd, min(CHUNK_BYTES, count - len(chunks)))
            except BlockingIOError:
                _wait(fd, selectors.EVENT_READ, deadline)
                continue
            need(bool(raw), 'PIPE_EOF_BEFORE_FRAME')
            chunks.extend(raw)
            fd.check()
            deadline_check(deadline)
        return bytes(chunks)
    size = struct.unpack('!I', exact(4))[0]
    need(0 < size <= max_bytes, 'BOUNDED_FRAME_LENGTH')
    raw = exact(size)
    if tagged:
        need(raw[0] in KIND_NAMES, 'UNKNOWN_FRAME_KIND')
        return KIND_NAMES[raw[0]], raw[1:]
    return raw


def kill_wait(child, grace_seconds=0.2):
    """Actual bounded cleanup; forced termination never proves source-finally."""
    need(isinstance(child, subprocess.Popen), 'REAL_SUBPROCESS_HANDLE')
    terminated = killed = False
    if child.poll() is None:
        child.terminate()
        terminated = True
        try:
            child.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            child.kill()
            killed = True
    try:
        code = child.wait(timeout=2.0)
        return {'pid': child.pid, 'exit_code': code, 'terminated': terminated,
            'killed': killed, 'reaped': True, 'source_finally_inferred': False}
    except subprocess.TimeoutExpired:
        return {'pid': child.pid, 'exit_code': None, 'terminated': terminated,
            'killed': killed, 'reaped': False, 'source_finally_inferred': False}


def terminate_and_reap(children, grace_seconds=0.2):
    need(all(isinstance(child, subprocess.Popen) for child in children), 'REAL_SUBPROCESS_HANDLES')
    flags = {}
    # Broadcast cancellation before waiting for any one child.  A stalled
    # first child cannot leave the other requests running during cleanup.
    for child in children:
        flags[child.pid] = {'terminated': False, 'killed': False}
        if child.poll() is None:
            child.terminate()
            flags[child.pid]['terminated'] = True
    grace = time.monotonic() + grace_seconds
    while any(child.poll() is None for child in children) and time.monotonic() < grace:
        time.sleep(min(0.01, max(0.0, grace - time.monotonic())))
    for child in children:
        if child.poll() is None:
            child.kill()
            flags[child.pid]['killed'] = True
    final_deadline = time.monotonic() + 2.0
    records = []
    for child in children:
        try:
            code = child.wait(timeout=max(0.001, final_deadline - time.monotonic()))
            reaped = True
        except subprocess.TimeoutExpired:
            code, reaped = None, False
        records.append({'pid': child.pid, 'exit_code': code, **flags[child.pid],
            'reaped': reaped, 'source_finally_inferred': False})
    if not all(row['reaped'] for row in records):
        error = TransportHold('WORKER_CLEANUP_INCOMPLETE')
        error.cleanup_records = tuple(dict(row) for row in records)
        raise error
    return records


def _identity(observed):
    return dict(zip(('device', 'inode', 'mode', 'bytes', 'mtime_ns', 'ctime_ns'),
        (observed.st_dev, observed.st_ino, observed.st_mode, observed.st_size,
            observed.st_mtime_ns, observed.st_ctime_ns)))


def _strict_source_read(path, expected, identity):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts
        and set(identity) == IDENTITY_FIELDS, 'CLOSED_BOOTSTRAP_SOURCE_IDENTITY')
    def no_links():
        need(not any(p.is_symlink() for p in (path, *path.parents)), 'STRICT_BOOTSTRAP_SOURCE_PATH')
    no_links()
    first = path.stat()
    need(stat.S_ISREG(first.st_mode) and _identity(first) == identity, 'BOOTSTRAP_SOURCE_IDENTITY')
    raw = path.read_bytes()
    last = path.stat()
    no_links()
    need(_identity(first) == _identity(last) == identity
        and hashlib.sha256(raw).hexdigest() == expected, 'BOOTSTRAP_SOURCE_BYTES_OR_RACE')
    return raw


def reject_import_artifacts(installed):
    """A -B process can still read cached or extension/package code.

    Reject these artifacts; never remove them or change the original loader.
    The actual current source table remains the only admitted implementation.
    """
    need(sys.pycache_prefix is None, 'CURRENT_NAMESPACE_ALTERNATE_PYCACHE_PREFIX')
    installed = Path(installed)
    probes = [installed / '__pycache__']
    for name in sorted(MODULE_NAMES):
        stem = name[:-3]
        probes.extend(installed / (stem + suffix) for suffix in
            ('', '.pyc', '.pyo', *importlib.machinery.EXTENSION_SUFFIXES))
    for path in probes:
        need(not path.exists() and not path.is_symlink(), 'CURRENT_NAMESPACE_IMPORT_ARTIFACT')


def bootstrap_sources(manifest):
    """Only checked current source bytes may precede a runtime import/token."""
    need(type(manifest) is dict and set(manifest) == MANIFEST_FIELDS
        and manifest['standard'] == 'VRS-CURRENT-V012-WORKER-SOURCE-MANIFEST-1', 'CLOSED_SOURCE_MANIFEST')
    root = Path(manifest['canonical_root'])
    need(root == FIXED_CANONICAL_ROOT, 'FIXED_WORKER_CANONICAL_ROOT')
    installed = root / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012'
    reject_import_artifacts(installed)
    modules, metadata = manifest['modules'], manifest['metadata']
    need(type(modules) is list and len(modules) == 19 and type(metadata) is list and len(metadata) == 3,
        'EXACT19_AND3_SOURCE_BOOTSTRAP')
    names = set()
    for row in modules:
        need(type(row) is dict and set(row) == {'name', 'path', 'sha256', 'identity'}
            and type(row['name']) is str and re.fullmatch(r'[a-z][a-z0-9_]*\.py', row['name'])
            and row['name'] not in names and Path(row['path']) == installed / row['name'], 'FIXED_INSTALLED_MODULE')
        names.add(row['name'])
        _strict_source_read(row['path'], row['sha256'], row['identity'])
    need(names == MODULE_NAMES, 'EXACT_CURRENT19_WORKER_MODULES')
    expected = {'profile': 'CURRENT_PACKAGING_PROFILE.json', 'nomination': 'INSTALLATION_NOMINATION.json',
        'plan': 'INSTALL_PLAN.json'}
    roles = set()
    for row in metadata:
        need(type(row) is dict and set(row) == {'role', 'path', 'sha256', 'identity'}
            and row['role'] in expected and row['role'] not in roles
            and Path(row['path']) == installed / expected[row['role']], 'FIXED_CURRENT_METADATA')
        roles.add(row['role'])
        _strict_source_read(row['path'], row['sha256'], row['identity'])
    need(roles == set(expected), 'COMPLETE_CURRENT_METADATA')
    profile = next(row for row in metadata if row['role'] == 'profile')
    need(manifest['profile_binding'] == {'path': profile['path'], 'sha256': profile['sha256']}, 'NOMINATED_BOOTSTRAP_PROFILE')
    reject_import_artifacts(installed)
    return root


def source_proof_valid(proof, manifest):
    need(type(proof) is dict and set(proof) == SOURCE_FIELDS
        and proof['status'] == 'ACTUAL_CURRENT_WORKER_SOURCE_AUTHORITY_AND_IDENTITY_VERIFIED'
        and proof['source_manifest_sha256'] == hashlib.sha256(encode_json(manifest)).hexdigest()
        and proof['source_modules'] == 19 and proof['metadata_files'] == 3
        and proof['transient_restore_allowed'] is False and proof['scientific_population_admitted'] is False
        and proof['certifies'] is False, 'CURRENT_WORKER_SOURCE_PROOF')


def _url(record_id, filename=None):
    need(type(record_id) is str and re.fullmatch('[1-9][0-9]*', record_id), 'EXACT_RECORD_ID')
    if filename is None:
        return 'https://zenodo.org/api/records/' + record_id
    need(type(filename) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', filename)
        and filename not in {'.', '..'}, 'SAFE_EXACT_CONTENT_NAME')
    return 'https://zenodo.org/api/records/' + record_id + '/files/' + filename + '/content'


@dataclass(frozen=True, slots=True)
class ContentDescriptor:
    record_id: str
    filename: str
    url: str
    bytes: int
    sha256: str
    md5: str
    source_role: str
    source_bindings: tuple

    @classmethod
    def parse(cls, value):
        fields = {'record_id', 'filename', 'url', 'bytes', 'sha256', 'md5', 'source_role', 'source_bindings'}
        need(type(value) is dict and set(value) == fields and value['url'] == _url(value['record_id'], value['filename']),
            'CLOSED_CONTENT_DESCRIPTOR')
        need(type(value['bytes']) is int and value['bytes'] > 0
            and re.fullmatch('[0-9a-f]{64}', value['sha256'])
            and re.fullmatch('[0-9a-f]{32}', value['md5'])
            and value['source_role'] in {'ORIGINAL', 'MANUSCRIPT'}, 'EXACT_CONTENT_EXPECTATIONS')
        bindings = value['source_bindings']
        need(type(bindings) is list and bindings, 'CONTENT_SOURCE_BINDINGS')
        checked = []
        for item in bindings:
            need(type(item) is dict and set(item) == {'path', 'sha256'} and type(item['path']) is str
                and re.fullmatch('[0-9a-f]{64}', item['sha256']), 'CLOSED_CONTENT_SOURCE_BINDING')
            checked.append((item['path'], item['sha256']))
        return cls(*(value[name] for name in ('record_id', 'filename', 'url', 'bytes', 'sha256', 'md5', 'source_role')),
            tuple(checked))

    def request(self):
        return {'role': 'content', 'record_id': self.record_id, 'filename': self.filename,
            'url': self.url, 'accept': '*/*', 'max_bytes': self.bytes,
            'expected_bytes': self.bytes, 'expected_sha256': self.sha256, 'expected_md5': self.md5}


def _file_inventory(body):
    value = body.get('files')
    rows = list(value.get('entries', {}).values()) if type(value) is dict and type(value.get('entries')) is dict else value
    need(type(rows) is list, 'COMPLETE_CURRENT_FILE_INVENTORY')
    result = {}
    for row in rows:
        need(type(row) is dict, 'CURRENT_FILE_ROW')
        name = row.get('filename', row.get('key'))
        size = row.get('filesize', row.get('size'))
        checksum = row.get('checksum')
        if type(checksum) is dict:
            need(checksum.get('algorithm') == 'md5', 'CURRENT_MD5_ALGORITHM')
            checksum = 'md5:' + str(checksum.get('value'))
        need(type(name) is str and name not in result and type(size) is int and size > 0
            and type(checksum) is str and re.fullmatch('md5:[0-9a-f]{32}', checksum), 'CURRENT_FILE_IDENTITY')
        result[name] = (size, checksum[4:])
    return result


def validate_content_allowlist(descriptors, metadata_pairs):
    """Transport precheck only; it cannot replace original science/pair checks."""
    need(type(descriptors) is list and len(descriptors) == 100, 'EXACT100_CONTENT_DESCRIPTORS')
    parsed = tuple(ContentDescriptor.parse(value) for value in descriptors)
    keys = {(item.record_id, item.filename) for item in parsed}
    records = {item.record_id for item in parsed}
    need(len(keys) == 100 and len(records) == 7 and type(metadata_pairs) is dict
        and set(metadata_pairs) == records, 'EXACT7_OWNER_PAIRS_AND100_FILES')
    need(sum(item.source_role == 'ORIGINAL' for item in parsed) == 42
        and sum(item.source_role == 'MANUSCRIPT' for item in parsed) == 58
        and sum(item.filename.lower().endswith('.pdf') for item in parsed) == 65, 'CLOSED_ORIGINAL_AND_MANUSCRIPT_POPULATION')
    for rid in records:
        pair = metadata_pairs[rid]
        need(type(pair) in (list, tuple) and len(pair) == 2 and all(type(body) is dict for body in pair), 'ACTUAL_OWNER_BODY_PAIR')
        legacy, native = pair
        need(str(legacy.get('id')) == rid and str(native.get('id')) == rid
            and str(native.get('parent', {}).get('access', {}).get('owned_by', {}).get('user')) == OWNER_ID, 'ACTUAL_PAIR_OWNER_AND_ID')
        expected = {item.filename: (item.bytes, item.md5) for item in parsed if item.record_id == rid}
        need(_file_inventory(legacy) == _file_inventory(native) == expected
            and sum(item.record_id == rid and item.source_role == 'ORIGINAL' for item in parsed) == 6,
            'COMPLETE_DESCRIPTOR_CURRENT_PAIR_JOIN')
    return parsed


def validate_request(value):
    fields = {'role', 'record_id', 'filename', 'url', 'accept', 'max_bytes', 'expected_bytes', 'expected_sha256', 'expected_md5'}
    need(type(value) is dict and set(value) == fields and value['role'] in {'metadata', 'content'}, 'CLOSED_OWNER_REQUEST')
    metadata = value['role'] == 'metadata'
    need(value['url'] == _url(value['record_id'], None if metadata else value['filename'])
        and value['accept'] in (ACCEPTS if metadata else {'*/*'}), 'EXACT_OWNER_GET_URL_AND_ACCEPT')
    need(type(value['max_bytes']) is int and 0 < value['max_bytes'] <= (MAX_METADATA_BYTES if metadata else value['expected_bytes']),
        'RAW_BODY_SIZE_BOUND')
    if metadata:
        need(value['filename'] is None and value['expected_bytes'] is None
            and value['expected_sha256'] is None and value['expected_md5'] is None, 'METADATA_RAW_SEMANTICS')
    else:
        need(type(value['expected_bytes']) is int and value['expected_bytes'] == value['max_bytes']
            and re.fullmatch('[0-9a-f]{64}', value['expected_sha256'])
            and re.fullmatch('[0-9a-f]{32}', value['expected_md5']), 'CONTENT_RAW_EXPECTATIONS')
    return value


def metadata_request(record_id, accept):
    return validate_request({'role': 'metadata', 'record_id': record_id, 'filename': None,
        'url': _url(record_id), 'accept': accept, 'max_bytes': MAX_METADATA_BYTES,
        'expected_bytes': None, 'expected_sha256': None, 'expected_md5': None})


def _worker_command(worker, child_in, child_out, child_error):
    return [sys.executable, '-B', worker['path'], '--input-fd', str(child_in.fd),
        '--output-fd', str(child_out.fd), '--error-fd', str(child_error.fd)]


@dataclass(frozen=True, slots=True)
class RawResponse:
    request_nonce: str
    request: bytes
    status: int
    reason: str
    headers: tuple
    body: bytes
    source_ready: bytes
    source_final: bytes
    header_send_before_monotonic: float
    header_send_after_monotonic: float
    body_completed_monotonic: float
    body_completed_at_utc: str
    actual_child_pid: int
    actual_child_exit_code: int

    @property
    def url(self):
        return decode_json(self.request)['url']


class MemoryResponse:
    """An actual child's raw bytes/status; original transport consumes it."""
    def __init__(self, value):
        self.status = self.code = value.status
        self.reason = value.reason
        self.headers = email.message.Message()
        for name, text in value.headers:
            self.headers[name] = text
        self._stream = io.BytesIO(value.body)
        self._url = value.url

    def geturl(self): return self._url
    def getcode(self): return self.status
    def info(self): return self.headers
    def read(self, size=-1): return self._stream.read(size)
    def close(self): self._stream.close()
    def __enter__(self): return self
    def __exit__(self, *_): self.close()


class HeaderGate:
    """One actual send grant, held until completed-send ACK is received."""
    def __init__(self):
        self.pending = None
        self.last_ack_received = None
        self.poisoned = False
        self.records = []

    def can_grant(self, now):
        return (not self.poisoned and self.pending is None
            and (self.last_ack_received is None or now >= self.last_ack_received + START_SPACING))

    def grant(self, nonce, now):
        need(self.can_grant(now), 'HEADER_DISPATCH_GATE')
        self.pending = (nonce, now)

    def acknowledge(self, nonce, before, after, received):
        need(not self.poisoned and self.pending is not None and self.pending[0] == nonce
            and all(finite(value) for value in (before, after, received))
            and self.pending[1] <= before <= after <= received, 'ACTUAL_COMPLETED_HEADER_ACK')
        self.records.append({'request_nonce': nonce, 'grant_monotonic': self.pending[1],
            'header_send_before_monotonic': before, 'header_send_after_monotonic': after,
            'ack_received_monotonic': received})
        self.pending = None
        self.last_ack_received = received

    def fail(self): self.poisoned = True


def _emit(fd, kind, value, deadline):
    write_frame(fd, value if type(value) is bytes else encode_json(value), deadline=deadline, kind=kind)


def _receive(fd, kind, deadline):
    actual, raw = read_frame(fd, deadline=deadline, tagged=True)
    need(actual == kind, 'WORKER_PROTOCOL_SEQUENCE')
    return raw


@dataclass(slots=True)
class _Job:
    request_nonce: str
    request: dict
    child: subprocess.Popen
    incoming: OwnedFD
    outgoing: OwnedFD
    errors: OwnedFD
    started: float
    deadline: float
    reader: FrameReader
    pending: bytearray
    state: str = 'source'
    eof: bool = False
    err_eof: bool = False
    error_bytes: bytearray = None
    body: bytearray = None
    ready_proof: dict = None
    final_proof: dict = None
    response: dict = None
    acknowledgement: dict = None
    done: dict = None

    def __post_init__(self):
        self.error_bytes = bytearray()
        self.body = bytearray()


class TransportBroker:
    """One closed operation's supervised raw transport; no verdict reuse.

    The master provides genuine public-runtime source and observation hooks.
    The child independently rebuilds the source authority before receiving a
    token and at final exit.  Constructor data is copied into immutable bytes.
    """
    def __init__(self, *, operation_nonce, token, source_manifest,
                 source_guard, start_get_clock, observation_deadline, deadline_guard, journal):
        need(type(operation_nonce) is str and re.fullmatch('[0-9a-f]{32}', operation_nonce), 'OPERATION_NONCE')
        need(type(token) is str and token and len(token) <= 16384
            and all(33 <= ord(char) <= 126 for char in token), 'MEMORY_ONLY_BEARER_TOKEN')
        need(all(callable(hook) for hook in (source_guard, start_get_clock, observation_deadline, deadline_guard)),
            'GENUINE_MASTER_SOURCE_AND_CLOCK_HOOKS')
        need(callable(journal), 'ACTUAL_PARENT_LIFECYCLE_JOURNAL')
        self._operation_nonce = operation_nonce
        self._token = token
        self._secret = token.encode('ascii')
        self._manifest_raw = encode_json(source_manifest)
        self._source_guard = source_guard
        self._start_get_clock = start_get_clock
        self._observation_deadline = observation_deadline
        self._deadline_guard = deadline_guard
        self._journal = journal
        self._gate = HeaderGate()
        self._active = {}
        self._records = []
        self._closed = False
        self._metadata_keys = set()
        self._content_keys = set()
        self.last_response = None
        self._check_sources()

    @property
    def records(self):
        return decode_json(encode_json(self._records))

    @property
    def header_dispatch_records(self):
        return decode_json(encode_json(self._gate.records))

    @property
    def last_header_ack_received(self):
        return self._gate.last_ack_received

    @property
    def active_children(self):
        return tuple(job.child.pid for job in self._active.values())

    def _guard(self):
        need(not self._closed, 'HTTP_OPERATION_CLOSED')
        self._deadline_guard()
        deadline = self._observation_deadline()
        need(deadline is None or finite(deadline), 'REAL_OBSERVATION_DEADLINE')
        if deadline is not None:
            deadline_check(deadline)

    def _check_sources(self):
        self._guard()
        current = self._source_guard()
        need(encode_json(current) == self._manifest_raw, 'MASTER_CURRENT_WORKER_SOURCE_CHANGED')
        self._guard()

    def _spawn_child(self, request_nonce, request, started, deadline):
        endpoints, child, job = [], None, None
        prior_mask = None
        try:
            # No handler can interrupt anonymous-pipe acquisition or actual
            # spawn before the returned handles have an owned active state.
            # Restore the exact caller mask before the PID journal or I/O.
            prior_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM, signal.SIGALRM})
            child_in, master_in = pipe_pair(); endpoints.extend((child_in, master_in))
            master_out, child_out = pipe_pair(); endpoints.extend((master_out, child_out))
            master_error, child_error = pipe_pair(); endpoints.extend((master_error, child_error))
            manifest = decode_json(self._manifest_raw)
            worker = next(row for row in manifest['modules'] if row['name'] == 'owner_content_worker.py')
            command = _worker_command(worker, child_in, child_out, child_error)
            self._journal({'stage': 'INTENT', 'operation_nonce': self._operation_nonce,
                'request_nonce': request_nonce, 'command': command, 'request': request,
                'request_started_monotonic': started, 'absolute_deadline': deadline,
                'source_manifest_sha256': hashlib.sha256(self._manifest_raw).hexdigest(),
                'owned_pipes': [{'fd': endpoint.fd, 'role': endpoint.role, 'identity': list(endpoint.identity)}
                    for endpoint in endpoints]})
            child = subprocess.Popen(command, stdin=child_in.fd, stdout=child_out.fd,
                stderr=child_error.fd, pass_fds=(child_in.fd, child_out.fd, child_error.fd),
                close_fds=True, env=safe_worker_environment(self._token))
            hello = {'standard': 'VRS-SOURCE-BOUND-OWNER-HTTP-JOB-1',
                'operation_nonce': self._operation_nonce, 'request_nonce': request_nonce,
                'request': request, 'source_manifest': manifest,
                'request_started_monotonic': started, 'absolute_deadline': deadline}
            overhead = 10 * MAX_FRAME + ((request['max_bytes'] // CHUNK_BYTES) + 1) * 5
            job = _Job(request_nonce, request, child, master_in, master_out, master_error,
                started, deadline, FrameReader(tagged=True, max_total_bytes=request['max_bytes'] + overhead),
                bytearray(frame_bytes(encode_json(hello), 'HELLO')))
            need(child.pid not in {item.child.pid for item in self._active.values()}, 'UNIQUE_HTTP_CHILD_PID')
            self._active[request_nonce] = job
            signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)
            prior_mask = None
            self._journal({'stage': 'PID', 'operation_nonce': self._operation_nonce,
                'request_nonce': request_nonce, 'pid': child.pid, 'pgid': os.getpgid(child.pid),
                'parent_pgid': os.getpgrp()})
            child_in.close(); child_out.close(); child_error.close()
            return job
        except BaseException:
            try:
                if child is not None:
                    cleanup = kill_wait(child)
                    need(cleanup['reaped'], 'HTTP_SPAWN_CLEANUP_INCOMPLETE')
                    self._active.pop(request_nonce, None)
                    self._journal({'stage': 'SPAWN_HOLD_TERMINAL', 'request_nonce': request_nonce, 'cleanup': cleanup})
            finally:
                # A second journal failure or a stale endpoint must not stop
                # attempts to close every still-owned descriptor.
                for endpoint in endpoints:
                    try: endpoint.close()
                    except (OSError, TransportHold): pass
            raise
        finally:
            if prior_mask is not None:
                signal.pthread_sigmask(signal.SIG_SETMASK, prior_mask)

    def _launch(self, request):
        import uuid
        self._check_sources()
        # Exactly the existing clock boundary: before process/DNS/TLS/READY.
        self._start_get_clock()
        self._guard()
        started = time.monotonic()
        deadline = self._observation_deadline()
        need(finite(deadline), 'FIRST_GET_CLOCK_NOT_STARTED')
        deadline = min(started + REQUEST_SECONDS, deadline)
        deadline_check(deadline)
        nonce = uuid.uuid4().hex
        job = self._spawn_child(nonce, request, started, deadline)
        return job

    def _process_frame(self, job, kind, raw):
        deadline_check(job.deadline)
        self._guard()
        if kind == 'ERROR':
            value = decode_json(raw)
            need(type(value) is dict and set(value) == {'exception_type', 'infrastructure_hold'}
                and value['infrastructure_hold'] is True and type(value['exception_type']) is str
                and re.fullmatch('[A-Za-z_][A-Za-z0-9_]{0,127}', value['exception_type']), 'SAFE_WORKER_ERROR')
            raise TransportHold('HTTP_CHILD_INFRASTRUCTURE_HOLD:' + value['exception_type'])
        if kind == 'DATA':
            need(job.state == 'body' and 0 < len(raw) <= CHUNK_BYTES
                and len(job.body) + len(raw) <= job.request['max_bytes'], 'BOUNDED_BODY_SEQUENCE')
            tail = bytes(job.body[-len(self._secret):])
            need(self._secret not in tail + raw, 'CREDENTIAL_IN_RAW_RESPONSE')
            job.body.extend(raw)
            return
        value = decode_json(raw)
        need(type(value) is dict and value.get('request_nonce') == job.request_nonce, 'EXACT_RESPONSE_REQUEST_NONCE')
        if kind == 'SOURCE_READY':
            need(job.state == 'source' and set(value) == {'request_nonce', 'proof'}, 'SOURCE_READY_SEQUENCE')
            source_proof_valid(value['proof'], decode_json(self._manifest_raw))
            self._check_sources()
            job.ready_proof = value['proof']
            job.pending.extend(frame_bytes(self._secret, 'TOKEN'))
            job.state = 'connect'
        elif kind == 'READY':
            need(job.state == 'connect' and set(value) == {'request_nonce'}, 'CONNECTION_READY_SEQUENCE')
            job.state = 'ready'
        elif kind == 'HEADER_ACK':
            need(job.state == 'grant' and set(value) == {'request_nonce', 'before_monotonic', 'after_monotonic',
                'before_utc', 'after_utc'} and not job.pending, 'HEADER_ACK_SEQUENCE')
            need(utc_value(value['before_utc']) <= utc_value(value['after_utc']) <= dt.datetime.now(dt.timezone.utc),
                'HEADER_ACK_REAL_UTC_CHRONOLOGY')
            self._gate.acknowledge(job.request_nonce, value['before_monotonic'],
                value['after_monotonic'], time.monotonic())
            job.acknowledgement = value
            job.state = 'headers'
        elif kind == 'RESPONSE':
            need(job.state == 'headers' and set(value) == {'request_nonce', 'status', 'reason', 'headers', 'final_url'}
                and type(value['status']) is int and 100 <= value['status'] <= 599
                and type(value['reason']) is str and value['final_url'] == job.request['url']
                and type(value['headers']) is list, 'ACTUAL_RAW_RESPONSE_HEADERS')
            need(self._secret not in raw, 'CREDENTIAL_IN_RESPONSE_HEADERS')
            for header in value['headers']:
                need(type(header) is list and len(header) == 2 and all(type(x) is str for x in header)
                    and all('\r' not in x and '\n' not in x for x in header), 'RAW_HEADER_PAIR')
            if job.request['role'] == 'content':
                need(value['status'] == 200, 'EXACT_CONTENT_HTTP200')
            job.response = value
            job.state = 'body'
        elif kind == 'SOURCE_FINAL':
            need(job.state == 'body' and set(value) == {'request_nonce', 'proof'}, 'SOURCE_FINAL_SEQUENCE')
            source_proof_valid(value['proof'], decode_json(self._manifest_raw))
            job.final_proof = value['proof']
            job.state = 'final'
        elif kind == 'DONE':
            need(job.state == 'final' and set(value) == {'request_nonce', 'pid', 'source_scopes_exited', 'body_bytes',
                'sha256', 'md5', 'body_completed_monotonic', 'body_completed_at_utc', 'finished_monotonic', 'finished_at_utc'}
                and value['pid'] == job.child.pid and value['source_scopes_exited'] is True
                and value['body_bytes'] == len(job.body)
                and value['sha256'] == hashlib.sha256(job.body).hexdigest()
                and value['md5'] == hashlib.md5(job.body).hexdigest(), 'COMPLETE_RAW_BODY_AND_NORMAL_SOURCE_EXIT')
            need(all(finite(value[key]) for key in ('body_completed_monotonic', 'finished_monotonic'))
                and job.acknowledgement['after_monotonic'] <= value['body_completed_monotonic']
                <= value['finished_monotonic'] <= time.monotonic() <= job.deadline,
                'ACTUAL_BODY_AND_SOURCE_COMPLETION_DEADLINE')
            need(utc_value(job.acknowledgement['after_utc']) <= utc_value(value['body_completed_at_utc'])
                <= utc_value(value['finished_at_utc']) <= dt.datetime.now(dt.timezone.utc), 'BODY_REAL_UTC_CHRONOLOGY')
            if job.request['role'] == 'content':
                need(len(job.body) == job.request['expected_bytes'] and value['sha256'] == job.request['expected_sha256']
                    and value['md5'] == job.request['expected_md5'], 'EXPECTED_CONTENT_FULL_BYTES')
            job.done = value
            job.state = 'done'
        else:
            raise TransportHold('UNKNOWN_OR_OUT_OF_ORDER_HTTP_FRAME')

    def _grant_ready(self):
        now = time.monotonic()
        if not self._gate.can_grant(now): return
        ready = next((job for job in self._active.values() if job.state == 'ready'), None)
        if ready is not None:
            deadline_check(ready.deadline)
            self._guard()
            self._gate.grant(ready.request_nonce, now)
            ready.pending.extend(frame_bytes(encode_json({'request_nonce': ready.request_nonce,
                'grant_monotonic': now}), 'GRANT'))
            ready.state = 'grant'

    def _step(self):
        self._guard()
        for job in self._active.values(): deadline_check(job.deadline)
        self._grant_ready()
        with selectors.DefaultSelector() as selector:
            for job in self._active.values():
                if not job.eof: selector.register(job.outgoing.fd, selectors.EVENT_READ, (job, 'out'))
                if not job.err_eof: selector.register(job.errors.fd, selectors.EVENT_READ, (job, 'err'))
                if job.pending: selector.register(job.incoming.fd, selectors.EVENT_WRITE, (job, 'in'))
            nearest = min((job.deadline for job in self._active.values()), default=time.monotonic() + 0.05)
            events = selector.select(min(0.05, max(0.0, nearest - time.monotonic())))
            for key, _ in events:
                job, role = key.data
                endpoint = {'out': job.outgoing, 'err': job.errors, 'in': job.incoming}[role]
                endpoint.check()
                deadline_check(job.deadline)
                self._guard()
                try:
                    if role == 'in':
                        sent = os.write(endpoint.fd, memoryview(job.pending)[:CHUNK_BYTES])
                        need(sent > 0, 'HTTP_CHILD_INPUT_CLOSED')
                        del job.pending[:sent]
                    else:
                        raw = os.read(endpoint.fd, CHUNK_BYTES)
                        if not raw:
                            if role == 'out': job.eof = True; job.reader.finish()
                            else: job.err_eof = True
                        elif role == 'err':
                            need(len(job.error_bytes) + len(raw) <= MAX_FRAME, 'BOUNDED_STDERR')
                            need(self._secret not in bytes(job.error_bytes[-len(self._secret):]) + raw, 'CREDENTIAL_IN_STDERR')
                            job.error_bytes.extend(raw)
                        else:
                            for kind, payload in job.reader.feed(raw): self._process_frame(job, kind, payload)
                except BlockingIOError:
                    pass
                endpoint.check()
                deadline_check(job.deadline)
                self._guard()
        completed = []
        for nonce, job in list(self._active.items()):
            code = job.child.poll()  # actual waitpid(WNOHANG), never wait before draining
            if code is None: continue
            need(code == 0, 'ACTUAL_NONZERO_HTTP_CHILD_EXIT')
            if not job.eof or not job.err_eof: continue
            need(code == 0 and not job.error_bytes and job.state == 'done' and job.done is not None
                and job.final_proof is not None and not job.pending, 'ACTUAL_NORMAL_HTTP_CHILD_EXIT')
            deadline_check(job.deadline)
            self._check_sources()
            deadline_check(job.deadline)
            record = {'request_nonce': nonce, 'pid': job.child.pid, 'actual_child_exit_code': code,
                'request': job.request, 'request_started_monotonic': job.started,
                'absolute_deadline': job.deadline, 'body_completed_at_utc': job.done['body_completed_at_utc'],
                'body_completed_monotonic': job.done['body_completed_monotonic'], 'reaped': True,
                'source_ready': job.ready_proof, 'source_final': job.final_proof, 'source_scopes_exited': True}
            self._records.append(record)
            self._journal({'stage': 'TERMINAL', 'operation_nonce': self._operation_nonce, **record})
            value = RawResponse(nonce, encode_json(job.request), job.response['status'], job.response['reason'],
                tuple(tuple(item) for item in job.response['headers']), bytes(job.body), encode_json(job.ready_proof),
                encode_json(job.final_proof), job.acknowledgement['before_monotonic'],
                job.acknowledgement['after_monotonic'], job.done['body_completed_monotonic'],
                job.done['body_completed_at_utc'], job.child.pid, code)
            for endpoint in (job.incoming, job.outgoing, job.errors): endpoint.close()
            del self._active[nonce]
            completed.append(value)
        return completed

    def _run(self, requests, maximum):
        need(not self._active and not self._gate.poisoned and 1 <= maximum <= MAX_HTTP_WORKERS, 'ONE_HTTP_BATCH')
        queue = deque(validate_request(value) for value in requests)
        results = []
        try:
            while queue or self._active:
                self._guard()
                while queue and len(self._active) < maximum:
                    self._launch(queue.popleft())
                results.extend(self._step())
            need(self._gate.pending is None, 'ALL_HEADER_ACKNOWLEDGED')
            return results
        except BaseException:
            self._gate.fail()
            try: self.cancel()
            except BaseException as cleanup:
                raise TransportHold('HTTP_WORKER_CLEANUP_INCOMPLETE') from cleanup
            raise

    def metadata(self, record_id, accept):
        key = (record_id, accept)
        need(key not in self._metadata_keys, 'METADATA_RESPONSE_ONE_USE')
        value = self._run([metadata_request(record_id, accept)], 1)[0]
        self._metadata_keys.add(key)
        self.last_response = value
        return value

    def prefetch_content(self, descriptors, metadata_pairs):
        parsed = validate_content_allowlist(descriptors, metadata_pairs)
        need(sum(item.bytes for item in parsed) <= MAX_BUFFERED_CONTENT_BYTES, 'BOUNDED_COMPLETE_CONTENT_BUFFER')
        self._check_sources()
        import packaging_runtime as runtime
        root = Path(decode_json(self._manifest_raw)['canonical_root'])
        # Descriptor derivation remains in the reviewed master adapter.  Every
        # nominated source is still freshly byte/identity/path checked here;
        # its declared hash is not accepted merely because a current API body
        # happens to advertise the same filename/size/checksum.
        for path, expected in sorted({binding for item in parsed for binding in item.source_bindings}):
            selected = Path(path)
            selected = selected if selected.is_absolute() else root / selected
            runtime.read_data_file(root, selected, expected_sha256=expected)
            self._guard()
        need(len(self._metadata_keys) == 14 and {rid for rid, _ in self._metadata_keys} == set(metadata_pairs)
            and all((rid, accept) in self._metadata_keys for rid in metadata_pairs for accept in ACCEPTS),
            'ALL14_RAW_METADATA_TERMINAL_BEFORE_CONTENT')
        keys = {(item.record_id, item.filename) for item in parsed}
        need(not self._content_keys and len(keys) == 100, 'ONE_CLOSED_CONTENT_PREFETCH')
        values = self._run([item.request() for item in parsed], MAX_HTTP_WORKERS)
        output = {}
        for value in values:
            request = decode_json(value.request)
            key = (request['record_id'], request['filename'])
            need(key not in output and key in keys, 'UNIQUE_ACTUAL_CONTENT_RESULT')
            output[key] = value
        need(set(output) == keys and not self._active, 'COMPLETE100_TERMINAL_CONTENT_RESULTS')
        self._content_keys = keys
        return output

    def cancel(self):
        self._closed = True
        self._gate.fail()
        jobs = tuple(self._active.values())
        cleanup, cleanup_error, endpoint_holds = [], None, []
        try:
            cleanup = terminate_and_reap([job.child for job in jobs])
        except BaseException as exc:
            cleanup_error = exc
            cleanup = [dict(row) for row in getattr(exc, 'cleanup_records', ())]
        finally:
            for job in jobs:
                for endpoint in (job.incoming, job.outgoing, job.errors):
                    try: endpoint.close()
                    except OSError: pass
                    except TransportHold as exc: endpoint_holds.append(type(exc).__name__)
        recorded = {row['pid'] for row in cleanup}
        for job in jobs:
            # poll() is a real waitpid observation. If helper execution was
            # interrupted, retain only what this current observation proves.
            code = job.child.poll()
            if job.child.pid not in recorded:
                cleanup.append({'pid': job.child.pid, 'exit_code': code,
                    'reaped': code is not None, 'signal_attempt_accounting': 'UNAVAILABLE',
                    'source_finally_inferred': False})
            if code is not None: self._active.pop(job.request_nonce, None)
        self._records.extend({'cleanup': value, 'raw_response_admitted': False} for value in cleanup)
        for value in cleanup:
            self._journal({'stage': 'CANCEL_TERMINAL', 'operation_nonce': self._operation_nonce,
                'cleanup': value, 'raw_response_admitted': False})
        if cleanup_error is not None:
            self._journal({'stage': 'CANCEL_HOLD', 'operation_nonce': self._operation_nonce,
                'error_type': type(cleanup_error).__name__, 'active_children': list(self.active_children),
                'all_owned_endpoint_closes_attempted': True, 'raw_response_admitted': False,
                'source_finally_inferred': False})
            raise cleanup_error
        need(not endpoint_holds, 'CANCEL_ENDPOINT_IDENTITY_CHANGED')
        return cleanup

    def close(self):
        need(not self._active, 'NO_BACKGROUND_HTTP_CHILDREN')
        self._closed = True
        self._token = None
        self._secret = b''


class MemoryOpener:
    """Original ZenodoTransport's explicit opener seam, no source interposition."""
    def __init__(self, broker): self.broker = broker

    def open(self, request, timeout=None):
        need(request.get_method() == 'GET' and request.data is None, 'GET_ONLY_ORIGINAL_TRANSPORT')
        parsed = urllib.parse.urlsplit(request.full_url)
        match = re.fullmatch(r'/api/records/([1-9][0-9]*)', parsed.path)
        need(parsed.scheme == 'https' and parsed.netloc == 'zenodo.org' and not parsed.query and not parsed.fragment
            and match is not None, 'ORIGINAL_METADATA_URL')
        headers = {key.lower(): value for key, value in request.header_items()}
        need(headers.get('authorization') == 'Bearer ' + self.broker._token
            and headers.get('accept') in ACCEPTS
            and set(headers) <= {'authorization', 'accept', 'content-type'}, 'ORIGINAL_METADATA_HEADERS')
        value = self.broker.metadata(match.group(1), headers['accept'])
        response = MemoryResponse(value)
        # urllib's inherited no-redirect error processor raises HTTPError for
        # actual non2xx statuses; preserve that raw error body in the seam.
        if not 200 <= response.status < 300:
            self.broker.close()
            raise urllib.error.HTTPError(value.url, response.status, response.reason, response.headers, response)
        return response


def child_main(input_fd, output_fd, error_fd):
    """Ordinary public source-bound entry; no source recovery or SCI scope."""
    signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGTERM, signal.SIGALRM})
    incoming, outgoing = OwnedFD.bind(input_fd, 'read'), OwnedFD.bind(output_fd, 'write')
    error = OwnedFD.bind(error_fd, 'write')
    deadline = time.monotonic() + REQUEST_SECONDS
    token = None
    try:
        hello = decode_json(_receive(incoming, 'HELLO', deadline))
        need(type(hello) is dict and set(hello) == {'standard', 'operation_nonce', 'request_nonce', 'request',
            'source_manifest', 'request_started_monotonic', 'absolute_deadline'}
            and hello['standard'] == 'VRS-SOURCE-BOUND-OWNER-HTTP-JOB-1', 'CLOSED_HTTP_JOB')
        need(all(type(hello[key]) is str and re.fullmatch('[0-9a-f]{32}', hello[key])
            for key in ('operation_nonce', 'request_nonce')), 'OWNER_JOB_NONCE')
        need(finite(hello['request_started_monotonic']) and finite(hello['absolute_deadline'])
            and hello['request_started_monotonic'] <= time.monotonic()
            and hello['absolute_deadline'] <= hello['request_started_monotonic'] + REQUEST_SECONDS, 'ACTUAL_REQUEST_DEADLINE')
        deadline = min(deadline, hello['absolute_deadline'])
        deadline_check(deadline)
        request = validate_request(hello['request'])
        manifest = hello['source_manifest']
        root = bootstrap_sources(manifest)
        own = next(row for row in manifest['modules'] if row['name'] == 'owner_content_worker.py')
        need(Path(__file__).absolute() == Path(own['path']), 'EXECUTED_PUBLIC_OWNER_WORKER')
        import packaging_runtime as runtime
        need(Path(runtime.__file__).absolute() == root / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012/packaging_runtime.py',
            'CURRENT_BOOTSTRAPPED_RUNTIME')
        with runtime.readonly_worker_scope(), runtime.json_data_scope(root):
            proof = runtime.verify_worker_source_manifest(root, manifest['profile_binding'], manifest)
            source_proof_valid(proof, manifest)
            _emit(outgoing, 'SOURCE_READY', {'request_nonce': hello['request_nonce'], 'proof': proof}, deadline)
            raw_token = _receive(incoming, 'TOKEN', deadline)
            need(0 < len(raw_token) <= 16384 and all(33 <= byte <= 126 for byte in raw_token), 'MEMORY_ONLY_BEARER_TOKEN')
            token = raw_token.decode('ascii')
            connection = http.client.HTTPSConnection('zenodo.org', 443,
                timeout=max(0.001, deadline - time.monotonic()), context=ssl.create_default_context())
            try:
                # DNS/TLS can block; parent independently enforces total deadline.
                deadline_check(deadline)
                connection.connect()
                deadline_check(deadline)
                parsed = urllib.parse.urlsplit(request['url'])
                connection.putrequest('GET', parsed.path, skip_accept_encoding=True)
                connection.putheader('Accept-Encoding', 'identity')
                connection.putheader('Authorization', 'Bearer ' + token)
                connection.putheader('Accept', request['accept'])
                connection.putheader('User-Agent', 'Python-urllib/%d.%d' % sys.version_info[:2])
                connection.putheader('Connection', 'close')
                _emit(outgoing, 'READY', {'request_nonce': hello['request_nonce']}, deadline)
                grant = decode_json(_receive(incoming, 'GRANT', deadline))
                need(type(grant) is dict and set(grant) == {'request_nonce', 'grant_monotonic'}
                    and grant['request_nonce'] == hello['request_nonce'] and finite(grant['grant_monotonic'])
                    and grant['grant_monotonic'] <= time.monotonic(), 'EXACT_HEADER_GRANT')
                deadline_check(deadline)
                before = time.monotonic()
                before_utc = utc()
                connection.endheaders()
                after = time.monotonic()
                after_utc = utc()
                deadline_check(deadline)
                _emit(outgoing, 'HEADER_ACK', {'request_nonce': hello['request_nonce'], 'before_monotonic': before,
                    'after_monotonic': after, 'before_utc': before_utc, 'after_utc': after_utc}, deadline)
                response = connection.getresponse()
                deadline_check(deadline)
                headers = response.getheaders()
                length = response.getheader('Content-Length')
                if length is not None:
                    need(re.fullmatch('[0-9]+', length) is not None and int(length) <= request['max_bytes'], 'DECLARED_RESPONSE_SIZE_BOUND')
                _emit(outgoing, 'RESPONSE', {'request_nonce': hello['request_nonce'], 'status': response.status,
                    'reason': response.reason, 'headers': headers, 'final_url': request['url']}, deadline)
                sha, md5, count = hashlib.sha256(), hashlib.md5(), 0
                while True:
                    deadline_check(deadline)
                    raw = response.read1(min(CHUNK_BYTES, request['max_bytes'] - count + 1))
                    deadline_check(deadline)
                    if not raw: break
                    count += len(raw)
                    need(count <= request['max_bytes'], 'RESPONSE_EXCESS_BYTES')
                    sha.update(raw)
                    md5.update(raw)
                    _emit(outgoing, 'DATA', raw, deadline)
                completed, completed_utc = time.monotonic(), utc()
                if request['role'] == 'content':
                    need(response.status == 200 and count == request['expected_bytes']
                        and sha.hexdigest() == request['expected_sha256'] and md5.hexdigest() == request['expected_md5'],
                        'CONTENT_STATUS_SIZE_OR_HASH')
            finally:
                connection.close()
            final = runtime.verify_worker_source_manifest(root, manifest['profile_binding'], manifest)
            source_proof_valid(final, manifest)
            _emit(outgoing, 'SOURCE_FINAL', {'request_nonce': hello['request_nonce'], 'proof': final}, deadline)
        # Only after both genuine source scopes exit is terminal material sent.
        deadline_check(deadline)
        _emit(outgoing, 'DONE', {'request_nonce': hello['request_nonce'], 'pid': os.getpid(),
            'source_scopes_exited': True, 'body_bytes': count, 'sha256': sha.hexdigest(), 'md5': md5.hexdigest(),
            'body_completed_monotonic': completed, 'body_completed_at_utc': completed_utc,
            'finished_monotonic': time.monotonic(), 'finished_at_utc': utc()}, deadline)
        return 0
    except BaseException as exc:
        # Never serialize an exception's arguments, headers, token or traceback.
        try:
            _emit(outgoing, 'ERROR', {'exception_type': type(exc).__name__, 'infrastructure_hold': True}, deadline)
        except BaseException:
            pass
        return 1
    finally:
        token = None
        for fd in (incoming, outgoing, error):
            try: fd.close()
            except OSError: pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Raw source-bound OWNER HTTP worker; parent IPC required')
    parser.add_argument('--input-fd', type=int, required=True)
    parser.add_argument('--output-fd', type=int, required=True)
    parser.add_argument('--error-fd', type=int, required=True)
    args = parser.parse_args()
    raise SystemExit(child_main(args.input_fd, args.output_fd, args.error_fd))
