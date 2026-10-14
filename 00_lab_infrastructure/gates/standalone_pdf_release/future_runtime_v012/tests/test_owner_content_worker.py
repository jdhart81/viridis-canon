"""Private synthetic IPC/transport tests; no original science or network.

The protocol subprocess below is an explicit test double. Its source proof
frames exercise the parser; they confer no actual source/runtime admission.
Production bootstrap independently refuses its temporary root.
"""
import argparse
import contextlib
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import owner_content_worker as worker


def proof(manifest):
    return {'status': 'ACTUAL_CURRENT_WORKER_SOURCE_AUTHORITY_AND_IDENTITY_VERIFIED',
        'source_manifest_sha256': hashlib.sha256(worker.encode_json(manifest)).hexdigest(),
        'source_modules': 19, 'metadata_files': 3, 'transient_restore_allowed': False,
        'scientific_population_admitted': False, 'certifies': False}


def fixture_body(rid, name):
    return ('synthetic-only:' + rid + ':' + name).encode()


@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(prefix='v009-owner-fixture-') as folder:
        root = Path(folder).resolve()
        data = root / 'source-manifest-data.json'
        data.write_bytes(b'{"synthetic":true}')
        binding = {'path': str(data), 'sha256': hashlib.sha256(data.read_bytes()).hexdigest()}
        modules = []
        installed = root / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012'
        installed.mkdir(parents=True)
        for name in sorted(worker.MODULE_NAMES):
            target = installed / name
            target.write_bytes(b'# synthetic inert source\n')
            modules.append({'name': name, 'path': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'identity': worker._identity(target.stat())})
        metadata = []
        for role, name in [('profile', 'CURRENT_PACKAGING_PROFILE.json'), ('nomination', 'INSTALLATION_NOMINATION.json'),
                           ('plan', 'INSTALL_PLAN.json')]:
            target = installed / name
            target.write_bytes(b'{}')
            metadata.append({'role': role, 'path': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'identity': worker._identity(target.stat())})
        manifest = {'standard': 'VRS-CURRENT-V012-WORKER-SOURCE-MANIFEST-1', 'canonical_root': str(root),
            'profile_binding': {'path': metadata[0]['path'], 'sha256': metadata[0]['sha256']},
            'modules': modules, 'metadata': metadata, 'source_origin': {}, 'legacy_closure': {},
            'source_review_change_flags': {}}
        descriptors, pairs = [], {}
        for index, count in enumerate([7, 10, 10, 10, 10, 9, 2]):
            rid = str(900000 + index)
            names = [('ORIGINAL', name) for name in ['METHODS_NOTES.zip', 'DIGEST_MANIFEST.json', 'METHODS_PAPER.pdf',
                'RUN_INDEX.csv', 'RELEASE_TAG.txt', 'MANIFEST.json']]
            names += [('MANUSCRIPT', 'Run-%d-Paper.pdf' % number) for number in range(count)]
            legacy_files, native_files = [], {}
            for role, name in names:
                raw = fixture_body(rid, name)
                descriptor = {'record_id': rid, 'filename': name, 'url': worker._url(rid, name), 'bytes': len(raw),
                    'sha256': hashlib.sha256(raw).hexdigest(), 'md5': hashlib.md5(raw).hexdigest(),
                    'source_role': role, 'source_bindings': [binding]}
                descriptors.append(descriptor)
                legacy_files.append({'filename': name, 'filesize': len(raw), 'checksum': 'md5:' + descriptor['md5']})
                native_files[name] = {'key': name, 'size': len(raw), 'checksum': {'algorithm': 'md5', 'value': descriptor['md5']}}
            pairs[rid] = ({'id': int(rid), 'files': legacy_files}, {'id': rid,
                'parent': {'access': {'owned_by': {'user': worker.OWNER_ID}}}, 'files': {'entries': native_files}})
        config = root / 'synthetic-pairs.json'
        config.write_text(json.dumps(pairs))
        yield SimpleNamespace(root=root, manifest=manifest, descriptors=descriptors, pairs=pairs, config=config)


def broker_fixture(f, *, mode='normal', observation_seconds=900):
    clock = {'deadline': None, 'starts': 0}
    journals = []
    def start():
        clock['starts'] += 1
        if clock['deadline'] is None: clock['deadline'] = time.monotonic() + observation_seconds
    def guard():
        if clock['deadline'] is not None: worker.deadline_check(clock['deadline'])
    broker = worker.TransportBroker(operation_nonce='a' * 32, token='synthetic-secret-only',
        source_manifest=f.manifest, source_guard=lambda: deepcopy(f.manifest), start_get_clock=start,
        observation_deadline=lambda: clock['deadline'], deadline_guard=guard,
        journal=lambda value: journals.append(deepcopy(value)))
    def command(_, incoming, outgoing, errors):
        return [sys.executable, '-B', str(Path(__file__).resolve()), '--stub',
            '--input-fd', str(incoming.fd), '--output-fd', str(outgoing.fd), '--error-fd', str(errors.fd)]
    stack = contextlib.ExitStack()
    stack.enter_context(patch.object(worker, '_worker_command', command))
    stack.enter_context(patch.dict(os.environ, {'V7_SYNTHETIC_MODE': mode, 'V7_SYNTHETIC_CONFIG': str(f.config)}))
    return broker, clock, journals, stack


def stub_main(input_fd, output_fd, error_fd):
    """No actual connection or original source authority is invoked."""
    incoming, outgoing, errors = worker.OwnedFD.bind(input_fd, 'read'), worker.OwnedFD.bind(output_fd, 'write'), worker.OwnedFD.bind(error_fd, 'write')
    limit = time.monotonic() + 30
    try:
        hello = worker.decode_json(worker._receive(incoming, 'HELLO', limit))
        nonce = hello['request_nonce']
        request = hello['request']
        mode = os.environ.get('V7_SYNTHETIC_MODE', 'normal')
        value = proof(hello['source_manifest'])
        if mode == 'wrong_source': value['source_manifest_sha256'] = '0' * 64
        worker._emit(outgoing, 'SOURCE_READY', {'request_nonce': nonce, 'proof': value}, limit)
        token = worker._receive(incoming, 'TOKEN', limit)
        if mode == 'dns_stall': time.sleep(30)
        if mode == 'delay_ready': time.sleep(0.03)
        worker._emit(outgoing, 'READY', {'request_nonce': nonce}, limit)
        grant = worker.decode_json(worker._receive(incoming, 'GRANT', limit))
        if mode == 'header_stall': time.sleep(30)
        before, before_utc = time.monotonic(), worker.utc()
        after, after_utc = time.monotonic(), worker.utc()
        worker._emit(outgoing, 'HEADER_ACK', {'request_nonce': nonce, 'before_monotonic': before,
            'after_monotonic': after, 'before_utc': before_utc, 'after_utc': after_utc}, limit)
        pairs = json.loads(Path(os.environ['V7_SYNTHETIC_CONFIG']).read_text())
        if request['role'] == 'metadata':
            raw = worker.encode_json(pairs[request['record_id']][0 if request['accept'] == 'application/json' else 1])
        else:
            raw = fixture_body(request['record_id'], request['filename'])
        if mode == 'large_body': raw = b'x' * (1024 * 1024)
        if mode == 'credential': raw = b'a' * (worker.CHUNK_BYTES - 5) + token + b'b'
        if mode == 'wrong_content': raw = b'wrong'
        final_url = request['url'] if mode != 'redirect' else 'https://example.invalid/redirect'
        worker._emit(outgoing, 'RESPONSE', {'request_nonce': nonce, 'status': 200, 'reason': 'OK',
            'headers': [['Content-Type', 'application/json']], 'final_url': final_url}, limit)
        for start in range(0, len(raw), worker.CHUNK_BYTES):
            if mode == 'drip': time.sleep(0.2)
            worker._emit(outgoing, 'DATA', raw[start:start + worker.CHUNK_BYTES], limit)
        completed, completed_utc = time.monotonic(), worker.utc()
        if mode == 'post_body_stall': time.sleep(30)
        if mode == 'wrong_final': value = {**value, 'source_manifest_sha256': '0' * 64}
        worker._emit(outgoing, 'SOURCE_FINAL', {'request_nonce': nonce, 'proof': value}, limit)
        worker._emit(outgoing, 'DONE', {'request_nonce': nonce, 'pid': os.getpid(), 'source_scopes_exited': True,
            'body_bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'md5': hashlib.md5(raw).hexdigest(),
            'body_completed_monotonic': completed, 'body_completed_at_utc': completed_utc,
            'finished_monotonic': time.monotonic(), 'finished_at_utc': worker.utc()}, limit)
        if mode == 'extra_frame': worker._emit(outgoing, 'READY', {'request_nonce': nonce}, limit)
        if mode == 'nonzero_after_done': return 3
        return 0
    except BaseException:
        return 1
    finally:
        for endpoint in (incoming, outgoing, errors):
            try: endpoint.close()
            except OSError: pass


class FramingAndDescriptorTests(unittest.TestCase):
    def test_actual_http_client_wire_headers_equal_original_urllib_get(self):
        # Exercise the real stdlib wire builder with an inert socket. No DNS,
        # original scientific function, external transport or TLS is used.
        class Socket:
            def __init__(self):self.sent=[]
            def sendall(self,value):self.sent.append(value)
        for accept,path in (('application/json','/api/records/42'),
                ('*/*','/api/records/42/files/Run-042.pdf/content')):
            headers={'Authorization':'Bearer synthetic-token','Accept':accept,
                'User-Agent':'Python-urllib/%d.%d'%sys.version_info[:2],
                'Connection':'close'}
            original=worker.http.client.HTTPConnection('zenodo.org')
            original.sock=Socket();original.request('GET',path,None,headers)
            corrected=worker.http.client.HTTPConnection('zenodo.org')
            corrected.sock=Socket()
            corrected.putrequest('GET',path,skip_accept_encoding=True)
            corrected.putheader('Accept-Encoding','identity')
            for key,value in headers.items():corrected.putheader(key,value)
            corrected.endheaders()
            self.assertEqual(b''.join(corrected.sock.sent),b''.join(original.sock.sent))
            self.assertIn(b'Accept-Encoding: identity\r\n',b''.join(corrected.sock.sent))
            self.assertNotIn(b'Content-Type:',b''.join(corrected.sock.sent))

    def test_fragmented_frames_and_closed_length_kind(self):
        reader = worker.FrameReader(tagged=True)
        raw = worker.frame_bytes(b'abc', 'DATA') + worker.frame_bytes(worker.encode_json({'one': 1}), 'READY')
        answer = []
        for byte in raw: answer.extend(reader.feed(bytes((byte,))))
        reader.finish()
        self.assertEqual(answer, [('DATA', b'abc'), ('READY', b'{"one":1}')])
        for raw in [struct.pack('!I', 0), struct.pack('!I', 65537), struct.pack('!I', 1) + b'\xff']:
            with self.subTest(raw=raw), self.assertRaises(worker.TransportHold): worker.FrameReader(tagged=True).feed(raw)
        reader = worker.FrameReader()
        reader.feed(struct.pack('!I', 4) + b'ab')
        with self.assertRaises(worker.TransportHold): reader.finish()

    def test_science_compatible_plain_json_frame_and_real_pipe(self):
        read_fd, write_fd = worker.pipe_pair()
        deadline = time.monotonic() + 2
        try:
            worker.write_frame(write_fd, worker.encode_json({'synthetic': True}), deadline=deadline)
            self.assertEqual(worker.decode_json(worker.read_frame(read_fd, deadline=deadline)), {'synthetic': True})
        finally:
            read_fd.close(); write_fd.close()

    def test_owned_pipe_replacement_regular_file_and_blocking_rejected(self):
        with tempfile.TemporaryFile() as file:
            with self.assertRaises(worker.TransportHold): worker.OwnedFD.bind(file.fileno(), 'read')
        read_fd, write_fd = worker.pipe_pair()
        try:
            os.set_blocking(write_fd.fd, True)
            with self.assertRaises(worker.TransportHold): write_fd.check()
            os.set_blocking(write_fd.fd, False)
            replacement, replacement_write = worker.pipe_pair()
            os.dup2(replacement.fd, read_fd.fd)
            with self.assertRaises(worker.TransportHold): read_fd.check()
            os.close(read_fd.fd)
            replacement.close(); replacement_write.close()
        finally:
            write_fd.close()

    def test_blocked_pipe_write_obeys_absolute_deadline(self):
        read_fd, write_fd = worker.pipe_pair()
        try:
            began = time.monotonic()
            with self.assertRaisesRegex(worker.TransportHold, 'DEADLINE'):
                worker.write_frame(write_fd, b'x' * 65536, deadline=began + 0.03)
            self.assertLess(time.monotonic() - began, 0.5)
        finally:
            read_fd.close(); write_fd.close()

    def test_header_gate_waits_completed_ack_and_poison(self):
        gate = worker.HeaderGate()
        gate.grant('one', 10)
        self.assertFalse(gate.can_grant(100))
        gate.acknowledge('one', 20, 22, 23)
        self.assertFalse(gate.can_grant(25.049))
        self.assertTrue(gate.can_grant(25.05))
        gate.grant('two', 25.05)
        with self.assertRaises(worker.TransportHold): gate.acknowledge('other', 26, 27, 28)
        gate.fail()
        self.assertFalse(gate.can_grant(1000))
        self.assertEqual(worker.START_SPACING, 2.05)

    def test_closed100_inventory_all_source_and_current_pair_mismatches(self):
        with fixture() as f:
            self.assertEqual(len(worker.validate_content_allowlist(f.descriptors, f.pairs)), 100)
            for change in ['missing', 'extra', 'traversal', 'unknown', 'size', 'owner', 'pair_extra', 'role']:
                values, pairs = deepcopy(f.descriptors), deepcopy(f.pairs)
                if change == 'missing': values.pop()
                if change == 'extra': values.append(values[0])
                if change == 'traversal': values[0]['filename'] = '../file'
                if change == 'unknown': values[0]['extra'] = True
                if change == 'size': values[0]['bytes'] += 1
                if change == 'owner': pairs[next(iter(pairs))][1]['parent']['access']['owned_by']['user'] = 'other'
                if change == 'pair_extra': pairs[next(iter(pairs))][0]['files'].append({'filename': 'extra', 'filesize': 1, 'checksum': 'md5:' + '0' * 32})
                if change == 'role': values[0]['source_role'] = 'MANUSCRIPT'
                with self.subTest(change=change), self.assertRaises((worker.TransportHold, TypeError)):
                    worker.validate_content_allowlist(values, pairs)

    def test_exact_urls_no_queries_encodings_or_headers_and_environment_sanitized(self):
        req = worker.metadata_request('900000', 'application/json')
        for url in ['http://zenodo.org/api/records/900000', req['url'] + '?x=1', req['url'] + '#x',
                    'https://other.invalid/api/records/900000']:
            with self.subTest(url=url), self.assertRaises(worker.TransportHold): worker.validate_request({**req, 'url': url})
        with self.assertRaises(worker.TransportHold): worker._url('900000', 'A%2fB.pdf')
        with patch.dict(os.environ, {'ZENODO_TOKEN': 'secret', 'OPENAI_API_KEY': 'also-secret', 'ORDINARY_TEST': 'public',
                                   'EMBEDDED': 'prefix-live-token-suffix', 'PYTHONPATH': 'foreign'}):
            value = worker.safe_worker_environment('live-token')
            self.assertNotIn('ZENODO_TOKEN', value); self.assertNotIn('OPENAI_API_KEY', value)
            self.assertNotIn('EMBEDDED', value); self.assertNotIn('PYTHONPATH', value)
            self.assertEqual(value['ORDINARY_TEST'], 'public')

    def test_bootstrap_fixed_root_exact19_3_and_fullsix_races(self):
        with fixture() as f:
            with self.assertRaisesRegex(worker.TransportHold, 'FIXED_WORKER_CANONICAL_ROOT'):
                worker.bootstrap_sources(f.manifest)
            with patch.object(worker, 'FIXED_CANONICAL_ROOT', f.root):
                self.assertEqual(worker.bootstrap_sources(f.manifest), f.root)
                for change in ['module_missing', 'metadata_missing', 'identity', 'bytes', 'module_extra']:
                    value = deepcopy(f.manifest)
                    if change == 'module_missing': value['modules'].pop()
                    if change == 'metadata_missing': value['metadata'].pop()
                    if change == 'identity': value['modules'][0]['identity']['ctime_ns'] += 1
                    if change == 'bytes': value['modules'][0]['sha256'] = '0' * 64
                    if change == 'module_extra': value['modules'][0]['name'] = 'foreign.py'
                    with self.subTest(change=change), self.assertRaises(worker.TransportHold): worker.bootstrap_sources(value)

    def test_bootstrap_rejects_import_cache_and_shadow_artifacts_without_deletion(self):
        with fixture() as f, patch.object(worker.sys, 'pycache_prefix', '/unadmitted-cache-prefix'), \
                patch.object(worker, 'FIXED_CANONICAL_ROOT', f.root), \
                self.assertRaisesRegex(worker.TransportHold, 'ALTERNATE_PYCACHE_PREFIX'):
            worker.bootstrap_sources(f.manifest)
        for name in ('__pycache__', 'packaging_runtime.pyc', 'packaging_runtime.pyo',
                     'packaging_runtime', *('packaging_runtime' + suffix
                         for suffix in worker.importlib.machinery.EXTENSION_SUFFIXES)):
            with self.subTest(name=name), fixture() as f:
                installed = f.root / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012'
                path = installed / name
                if name in ('__pycache__', 'packaging_runtime'): path.mkdir()
                else: path.write_bytes(b'never admitted as source')
                with patch.object(worker, 'FIXED_CANONICAL_ROOT', f.root), \
                        self.assertRaisesRegex(worker.TransportHold, 'IMPORT_ARTIFACT'):
                    worker.bootstrap_sources(f.manifest)
                self.assertTrue(path.exists())


class ActualPipeProcessTests(unittest.TestCase):
    def test_partial_pipe_and_failed_spawn_journals_close_every_owned_endpoint(self):
        for failure in ('pipe2', 'pipe3', 'pid_journal', 'cleanup_journal'):
            with self.subTest(failure=failure), fixture() as f:
                broker, _, journal, stack = broker_fixture(f)
                allocated, children, count = [], [], [0]
                actual_pair, actual_popen = worker.pipe_pair, worker.subprocess.Popen
                def pair():
                    count[0] += 1
                    if failure == 'pipe' + str(count[0]): raise OSError('synthetic allocation failure')
                    result = actual_pair(); allocated.extend(result); return result
                class TrackedPopen(actual_popen):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs); children.append(self)
                def record(value):
                    journal.append(value)
                    if value['stage'] == 'PID': raise OSError('synthetic PID journal failure')
                    if failure == 'cleanup_journal' and value['stage'] == 'SPAWN_HOLD_TERMINAL':
                        raise OSError('synthetic cleanup journal failure')
                if failure.endswith('journal'): broker._journal = record
                old_mask = worker.signal.pthread_sigmask(worker.signal.SIG_BLOCK, set())
                with stack, patch.object(worker, 'pipe_pair', side_effect=pair), \
                        patch.object(worker.subprocess, 'Popen', TrackedPopen), self.assertRaises(OSError):
                    broker.metadata('900000', 'application/json')
                self.assertEqual(worker.signal.pthread_sigmask(worker.signal.SIG_BLOCK, set()), old_mask)
                self.assertFalse(broker.active_children)
                self.assertTrue(all(child.poll() is not None for child in children))
                for endpoint in allocated:
                    with self.assertRaises(OSError): os.fstat(endpoint.fd)

    def test_startup_signal_unwinds_only_after_actual_child_owned_and_restores_mask(self):
        class SyntheticShutdown(BaseException): pass
        with fixture() as f:
            broker, _, journal, stack = broker_fixture(f)
            children, owned_at_signal = [], []
            actual_popen = worker.subprocess.Popen
            old_handler = worker.signal.getsignal(worker.signal.SIGTERM)
            old_mask = worker.signal.pthread_sigmask(worker.signal.SIG_BLOCK, set())
            def shutdown(*_):
                owned_at_signal.append(broker.active_children)
                raise SyntheticShutdown('actual pending shutdown signal')
            class TrackedPopen(actual_popen):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs); children.append(self)
                    os.kill(os.getpid(), worker.signal.SIGTERM)
            try:
                worker.signal.signal(worker.signal.SIGTERM, shutdown)
                with stack, patch.object(worker.subprocess, 'Popen', TrackedPopen), \
                        self.assertRaises(SyntheticShutdown):
                    broker.metadata('900000', 'application/json')
            finally:
                worker.signal.signal(worker.signal.SIGTERM, old_handler)
                worker.signal.pthread_sigmask(worker.signal.SIG_SETMASK, old_mask)
            self.assertEqual(owned_at_signal, [(children[0].pid,)])
            self.assertFalse(broker.active_children)
            self.assertIsNotNone(children[0].poll())
            self.assertTrue(any(row['stage'] == 'SPAWN_HOLD_TERMINAL' and row['cleanup']['reaped'] for row in journal))

    def test_cancel_helper_failure_retains_observations_and_closes_every_owned_handle(self):
        with fixture() as f:
            broker, _, journal, stack = broker_fixture(f, mode='header_stall')
            actual_cleanup = worker.terminate_and_reap
            actual_spawn = broker._spawn_child
            jobs = []
            def spawn(*args):
                job = actual_spawn(*args); jobs.append(job); return job
            def failed_helper(children):
                rows = actual_cleanup(children)
                error = worker.TransportHold('synthetic helper failure after genuine wait')
                error.cleanup_records = tuple(rows)
                raise error
            with stack, patch.object(broker, '_spawn_child', side_effect=spawn), \
                    patch.object(worker, 'REQUEST_SECONDS', 0.05), \
                    patch.object(worker, 'terminate_and_reap', side_effect=failed_helper), \
                    self.assertRaisesRegex(worker.TransportHold, 'HTTP_WORKER_CLEANUP_INCOMPLETE'):
                broker.metadata('900000', 'application/json')
            self.assertFalse(broker.active_children)
            self.assertEqual(len(jobs), 1)
            self.assertIsNotNone(jobs[0].child.poll())
            for endpoint in (jobs[0].incoming, jobs[0].outgoing, jobs[0].errors):
                with self.assertRaises(OSError): os.fstat(endpoint.fd)
            self.assertTrue(any(row['stage'] == 'CANCEL_TERMINAL' and row['cleanup']['reaped'] for row in journal))
            held = next(row for row in journal if row['stage'] == 'CANCEL_HOLD')
            self.assertIs(held['source_finally_inferred'], False)
            self.assertIs(held['raw_response_admitted'], False)

    def test_real_child_code_source_scopes_header_send_and_chunk_reader_without_network(self):
        with fixture() as f:
            request = f.descriptors[0]
            raw = fixture_body(request['record_id'], request['filename'])
            calls, scopes, outcome, sent_headers = [], [], [], []
            @contextlib.contextmanager
            def readonly():
                scopes.append('source_enter')
                try: yield
                finally: scopes.append('source_exit')
            @contextlib.contextmanager
            def json_scope(_):
                yield
            def verify(*_):
                calls.append('source_verify')
                return proof(f.manifest)
            class Response:
                status = 200
                reason = 'OK'
                def __init__(self): self.offset = 0
                def getheaders(self): return [('Content-Length', str(len(raw)))]
                def getheader(self, name): return str(len(raw)) if name == 'Content-Length' else None
                def read1(self, count):
                    self.assert_bound(count)
                    value = raw[self.offset:self.offset + count]
                    self.offset += len(value)
                    return value
                def assert_bound(self, count):
                    if not 0 < count <= worker.CHUNK_BYTES: raise AssertionError('unbounded body read')
            class Connection:
                def connect(self): calls.append('connect')
                def putrequest(self, *args, **kwargs): calls.append('GET')
                def putheader(self, *args): sent_headers.append(args)
                def endheaders(self): calls.append('actual_header_send')
                def getresponse(self): return Response()
                def close(self): calls.append('connection_closed')
            current = SimpleNamespace(__file__=str(f.root / '_ZENODO_DEPOSITS/standalone_pdf_runtime_v012/packaging_runtime.py'),
                readonly_worker_scope=readonly, json_data_scope=json_scope, verify_worker_source_manifest=verify)
            cin, pin = worker.pipe_pair(); pout, cout = worker.pipe_pair(); perr, cerr = worker.pipe_pair()
            deadline = time.monotonic() + 3
            hello = {'standard': 'VRS-SOURCE-BOUND-OWNER-HTTP-JOB-1', 'operation_nonce': 'a' * 32,
                'request_nonce': 'b' * 32, 'request': worker.metadata_request(request['record_id'], 'application/json'),
                'source_manifest': f.manifest, 'request_started_monotonic': time.monotonic(), 'absolute_deadline': deadline}
            own = next(row for row in f.manifest['modules'] if row['name'] == 'owner_content_worker.py')
            with patch.object(worker, 'bootstrap_sources', return_value=f.root), patch.object(worker, '__file__', own['path']), \
                    patch.dict(sys.modules, {'packaging_runtime': current}), \
                    patch.object(worker.http.client, 'HTTPSConnection', return_value=Connection()), \
                    patch.object(worker.ssl, 'create_default_context', return_value=None):
                child = threading.Thread(target=lambda: outcome.append(worker.child_main(cin.fd, cout.fd, cerr.fd)))
                child.start()
                try:
                    worker.write_frame(pin, worker.encode_json(hello), kind='HELLO', deadline=deadline)
                    kind, _ = worker.read_frame(pout, tagged=True, deadline=deadline)
                    self.assertEqual(kind, 'SOURCE_READY')
                    self.assertEqual(calls, ['source_verify'])
                    worker.write_frame(pin, b'synthetic-token', kind='TOKEN', deadline=deadline)
                    kind, _ = worker.read_frame(pout, tagged=True, deadline=deadline)
                    self.assertEqual(kind, 'READY')
                    self.assertNotIn('actual_header_send', calls)
                    worker.write_frame(pin, worker.encode_json({'request_nonce': 'b' * 32,
                        'grant_monotonic': time.monotonic()}), kind='GRANT', deadline=deadline)
                    kinds, body = [], bytearray()
                    while not kinds or kinds[-1] != 'DONE':
                        kind, value = worker.read_frame(pout, tagged=True, deadline=deadline)
                        kinds.append(kind)
                        if kind == 'DATA': body.extend(value)
                    child.join(timeout=1)
                    self.assertFalse(child.is_alive())
                    self.assertEqual(outcome, [0])
                    self.assertEqual(body, raw)
                    self.assertEqual(kinds[0], 'HEADER_ACK')
                    self.assertEqual(kinds[-2:], ['SOURCE_FINAL', 'DONE'])
                    self.assertEqual(calls.count('source_verify'), 2)
                    self.assertEqual(scopes, ['source_enter', 'source_exit'])
                    self.assertEqual(sent_headers, [('Accept-Encoding', 'identity'),
                        ('Authorization', 'Bearer synthetic-token'),
                        ('Accept', 'application/json'),
                        ('User-Agent', 'Python-urllib/%d.%d' % sys.version_info[:2]),
                        ('Connection', 'close')])
                finally:
                    child.join(timeout=4)
                    for endpoint in (pin, pout, perr): endpoint.close()

    def test_large_response_drained_before_real_exit_no_pipe_deadlock(self):
        with fixture() as f:
            broker, clock, journal, stack = broker_fixture(f, mode='large_body')
            with stack:
                result = broker.metadata('900000', 'application/json')
            self.assertEqual(len(result.body), 1024 * 1024)
            self.assertEqual(result.actual_child_exit_code, 0)
            self.assertFalse(broker.active_children)
            self.assertEqual([item['stage'] for item in journal], ['INTENT', 'PID', 'TERMINAL'])
            self.assertEqual(journal[1]['pgid'], journal[1]['parent_pgid'])
            self.assertEqual(clock['starts'], 1)
            with self.assertRaises(worker.TransportHold): broker.metadata('900000', 'application/json')
            broker.close()

    def test_source_ready_final_redirect_and_secret_rejections_kill_wait(self):
        for mode in ['wrong_source', 'wrong_final', 'redirect', 'credential', 'extra_frame', 'nonzero_after_done']:
            with self.subTest(mode=mode), fixture() as f:
                broker, _, journal, stack = broker_fixture(f, mode=mode)
                with stack, self.assertRaises(worker.TransportHold): broker.metadata('900000', 'application/json')
                self.assertFalse(broker.active_children)
                self.assertTrue(any(item['stage'] == 'CANCEL_TERMINAL' and item['cleanup']['reaped'] for item in journal))
                self.assertNotIn('synthetic-secret-only', json.dumps(journal))
                with self.assertRaises(worker.TransportHold): broker.metadata('900001', 'application/json')

    def test_changed_parent_source_before_token_rejected(self):
        with fixture() as f:
            broker, _, journal, stack = broker_fixture(f)
            count = [0]
            def source():
                count[0] += 1
                value = deepcopy(f.manifest)
                if count[0] >= 2: value['metadata'][0]['sha256'] = '0' * 64
                return value
            broker._source_guard = source
            with stack, self.assertRaisesRegex(worker.TransportHold, 'SOURCE_CHANGED'):
                broker.metadata('900000', 'application/json')
            self.assertFalse(broker.active_children)
            self.assertEqual(broker.header_dispatch_records, [])
            self.assertTrue(any(item['stage'] == 'CANCEL_TERMINAL' for item in journal))

    def test_manual_parent_subprocess_does_not_open_unknown_integer_fd(self):
        active = [False]
        def audit(event, args):
            if active[0] and event == 'open' and type(args[0]) is int:
                raise AssertionError('Unknown io.open(intfd) while synthetic audit active')
        sys.addaudithook(audit)
        with fixture() as f:
            broker, _, _, stack = broker_fixture(f)
            try:
                active[0] = True
                with stack: self.assertEqual(broker.metadata('900000', 'application/json').actual_child_exit_code, 0)
            finally:
                active[0] = False
            broker.close()

    def test_dns_header_body_drip_and_postbody_absolute_timeout(self):
        for mode in ['dns_stall', 'header_stall', 'drip', 'post_body_stall']:
            with self.subTest(mode=mode), fixture() as f:
                broker, _, journal, stack = broker_fixture(f, mode=mode)
                with stack, patch.object(worker, 'REQUEST_SECONDS', 0.15):
                    began = time.monotonic()
                    with self.assertRaises(worker.TransportHold): broker.metadata('900000', 'application/json')
                    self.assertLess(time.monotonic() - began, 3)
                self.assertFalse(broker.active_children)
                self.assertTrue(all(item['cleanup']['reaped'] and item['cleanup']['source_finally_inferred'] is False
                    for item in journal if item['stage'] == 'CANCEL_TERMINAL'))

    def test_first_clock_precedes_ready_and_observation_cutoff_not_reset(self):
        with fixture() as f:
            broker, clock, journal, stack = broker_fixture(f, mode='dns_stall', observation_seconds=0.08)
            with stack:
                with self.assertRaises(worker.TransportHold): broker.metadata('900000', 'application/json')
            self.assertIsNotNone(clock['deadline'])
            self.assertEqual(clock['starts'], 1)
            self.assertEqual(journal[0]['absolute_deadline'], clock['deadline'])
            self.assertFalse(broker.active_children)

    def test_complete14_pairs_and100_content_max6_with_actual_ack_spacing(self):
        with fixture() as f:
            broker, _, journal, stack = broker_fixture(f)
            with stack, patch.object(worker, 'START_SPACING', 0.005):
                for rid in f.pairs:
                    for accept in worker.ACCEPTS:
                        self.assertEqual(worker.decode_json(broker.metadata(rid, accept).body)['id'], int(rid) if accept == 'application/json' else rid)
                values = broker.prefetch_content(f.descriptors, f.pairs)
            self.assertEqual(len(values), 100)
            self.assertEqual(len(broker.records), 114)
            active, maximum = set(), 0
            for item in journal:
                if item['stage'] == 'PID': active.add(item['pid']); maximum = max(maximum, len(active))
                if item['stage'] == 'TERMINAL': active.remove(item['pid'])
            self.assertFalse(active)
            self.assertLessEqual(maximum, 6)
            self.assertEqual(len({value.actual_child_pid for value in values.values()}), 100)
            records = broker.header_dispatch_records
            for previous, current in zip(records, records[1:]):
                self.assertGreaterEqual(current['grant_monotonic'], previous['ack_received_monotonic'] + 0.005)
            for descriptor in f.descriptors:
                self.assertEqual(values[(descriptor['record_id'], descriptor['filename'])].body,
                    fixture_body(descriptor['record_id'], descriptor['filename']))
            broker.close()

    def test_simultaneous_batch_failure_cancels_all_without_uncertain_gate_continuation(self):
        with fixture() as f:
            broker, _, journal, stack = broker_fixture(f, mode='header_stall')
            requests = [worker.metadata_request(rid, 'application/json') for rid in list(f.pairs)[:6]]
            with stack, patch.object(worker, 'REQUEST_SECONDS', 0.15):
                with self.assertRaises(worker.TransportHold): broker._run(requests, 6)
            self.assertFalse(broker.active_children)
            pids = [item['pid'] for item in journal if item['stage'] == 'PID']
            cleanup = [item['cleanup'] for item in journal if item['stage'] == 'CANCEL_TERMINAL']
            self.assertEqual({row['pid'] for row in cleanup}, set(pids))
            self.assertTrue(all(row['reaped'] for row in cleanup))
            self.assertLessEqual(len(broker.header_dispatch_records), 1)

    def test_original_metadata_http_error_uses_actual_raw_body(self):
        response = worker.RawResponse('0' * 32, worker.encode_json(worker.metadata_request('900000', 'application/json')),
            302, 'Found', (('Location', 'https://other.invalid'),), b'{"error":"actual"}', b'{}', b'{}',
            1, 2, 3, '2026-01-01T00:00:00+00:00', 1, 0)
        broker = SimpleNamespace(_token='synthetic-token', metadata=lambda *_: response, close=lambda: None)
        import urllib.request
        request = urllib.request.Request(response.url, headers={'Authorization': 'Bearer synthetic-token', 'Accept': 'application/json'})
        with self.assertRaises(worker.urllib.error.HTTPError) as caught: worker.MemoryOpener(broker).open(request)
        self.assertEqual(caught.exception.code, 302)
        self.assertEqual(caught.exception.read(), b'{"error":"actual"}')
        caught.exception.close()


if __name__ == '__main__':
    if '--stub' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--stub', action='store_true')
        parser.add_argument('--input-fd', type=int, required=True)
        parser.add_argument('--output-fd', type=int, required=True)
        parser.add_argument('--error-fd', type=int, required=True)
        args = parser.parse_args()
        raise SystemExit(stub_main(args.input_fd, args.output_fd, args.error_fd))
    unittest.main()
