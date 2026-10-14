"""Actual owner adapter/registry/input guards with local synthetic transport.

No original qualifier, source factory, network, proof or canonical job runs.
The real descriptor/current-metadata join and physical replay guards remain.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_catalog as catalog
import packaging_runtime as runtime
import manuscript_access_registry as registry
import manuscript_access_correction as correction
import owner_content_worker as transport_worker

SIZES = (7, 10, 10, 10, 10, 9, 2)
COMPLETED = '2026-10-12T09:00:00+00:00'
# Actual broker ACK field shape, with entirely synthetic fixture values.
# Retention of this sample proves no real pacing, request or admission.
ACK_SAMPLE = {'request_nonce': 'a'*32, 'grant_monotonic': 99.0,
              'header_send_before_monotonic': 99.01,
              'header_send_after_monotonic': 99.02,
              'ack_received_monotonic': 99.03}


def hashes(value):
    return {'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest(),
            'md5': hashlib.md5(value).hexdigest()}


def put(path, value):
    raw = value if type(value) is bytes else json.dumps(value, sort_keys=True).encode()
    path.write_bytes(raw)
    return {'path': str(path), 'sha256': hashes(raw)['sha256']}


class OwnerContextIntegration(unittest.TestCase):
    def fixture(self, root, clock, mutate_pairs=None, response_count=None):
        bodies = {}; pairs = {}; entries = []
        for ordinal, count in enumerate(SIZES):
            rid = str(24000000+ordinal)
            papers = {f'Run-{ordinal*10+note+1:03d}/paper.pdf':
                      b'%PDF-synthetic actual archived manuscript '+str((ordinal, note)).encode()
                      for note in range(count)}
            archive = BytesIO()
            with zipfile.ZipFile(archive, 'w') as stream:
                for member, body in papers.items(): stream.writestr(member, body)
            original = {'bundle.zip': archive.getvalue(), 'paper.pdf': b'%PDF-synthetic aggregate '+rid.encode(),
                        'README.md': b'Synthetic original DATA', 'paper.tex': b'Synthetic TeX DATA',
                        'DIGEST_MANIFEST.json': b'{"synthetic":"original manifest"}',
                        'PUBLICATION_BINDING.json': b'{"synthetic":"original binding"}'}
            copies = {f'Run-{ordinal*10+note+1:03d}-Paper.pdf': body
                      for note, body in enumerate(papers.values())}
            file_rows = []
            for name, body in {**original, **copies}.items():
                bodies[(rid, name)] = body
                file_rows.append({'filename': name, 'filesize': len(body),
                                  'checksum': 'md5:'+hashes(body)['md5']})
            legacy = {'id': int(rid), 'metadata': {'title': 'Synthetic exact metadata',
                       'custom_unknown': {'keep': ['all', 'fields']}}, 'files': deepcopy(file_rows)}
            native = {'id': rid, 'parent': {'access': {'owned_by': {'user': '1591505'}}},
                      'files': {'entries': {v['filename']: {'key': v['filename'], 'size': v['filesize'],
                                             'checksum': v['checksum']} for v in file_rows}},
                      'custom_fields': {'unrecognized_but_retained': [1, {'exact': True}]}}
            pairs[rid] = (legacy, native)
            folder = root/('source-'+rid); folder.mkdir()
            manifest = put(folder/'MANIFEST.json', {'synthetic': 'fixed manifest input', 'members': list(papers)})
            archive_binding = put(folder/'archive.zip', archive.getvalue())
            registered = put(folder/'registration.json', {'synthetic': 'nominated input only', 'digest_manifest': manifest})
            authority = put(folder/'authority.json', {'synthetic': 'not user authority or scientific admission'})
            copies_rows = [{'filename': name, **hashes(body), 'run_id': name.split('-Paper')[0],
                            'member': member} for (name, body), member in zip(copies.items(), papers)]
            access = {'standard': correction.STANDARD, 'status': 'SYNTHETIC_INPUTS_NOT_AUTHORITY',
                      'record_id': rid, 'doi': f'10.5281/zenodo.{rid}',
                      'source_manifest_sha256': manifest['sha256'],
                      'source_archive_sha256': archive_binding['sha256'],
                      'original_files': [{'filename': name, **hashes(body)} for name, body in original.items()],
                      'copies': copies_rows, 'authority': authority}
            access_binding = put(folder/'access.json', access)
            entries.append({'record_id': rid, 'registration': registered, 'archive': archive_binding,
                            'access_correction': access_binding, 'user_authority': authority, 'prior_chain': None})
        if mutate_pairs is not None: mutate_pairs(pairs)
        registry_binding = put(root/'registry.json', {'standard': registry.STANDARD,
            'status': 'NOMINATED_INPUTS_NOT_AUTHORITY', 'observation_context': registry.CONTEXT, 'entries': entries})
        profile = {'access_registry': registry_binding}
        output = root/'reports/verification-coverage/synthetic-owner'
        calls = []; brokers = []; source_events = []; transport_constructions = []
        source_manifest = {'synthetic': '22 source DATA rows, authority tested separately'}

        class Broker:
            def __init__(self, **kwargs):
                self.hooks = kwargs; self.records = []
                self.header_dispatch_records = [deepcopy(ACK_SAMPLE)]
                self.active_children = (); self.last_response = None; self.closed = False
                self.descriptors = None; self.actual_pairs = None
                brokers.append(self); self.check_sources()

            def check_sources(self):
                current = self.hooks['source_guard']()
                if current != self.hooks['source_manifest']: raise AssertionError('source DATA substituted')

            def metadata(self, rid, accept):
                self.check_sources(); self.hooks['start_get_clock'](); self.hooks['deadline_guard']()
                calls.append(('metadata', rid, accept))
                value = pairs[rid][0 if accept == registry.CONTEXT['legacy_accept'] else 1]
                # Raw HTTP bytes intentionally differ from canonical JSON.
                raw = (json.dumps(value, indent=3)+'\n').encode()
                response = SimpleNamespace(url='https://zenodo.org/api/records/'+rid, status=200,
                    body=raw, body_completed_at_utc=COMPLETED, actual_child_exit_code=0)
                self.last_response = response
                self.records.append({'synthetic': 'terminal metadata', 'record_id': rid})
                self.hooks['journal']({'stage': 'SYNTHETIC_METADATA_TERMINAL', 'record_id': rid,
                                      'child_authority': 'SEPARATELY_TESTED_FULL_GENUINE_CHILD_VALIDATION'})
                return response

            def prefetch_content(self, descriptors, observed_pairs):
                self.check_sources(); self.hooks['deadline_guard']()
                self.descriptors = deepcopy(descriptors); self.actual_pairs = deepcopy(observed_pairs)
                parsed = transport_worker.validate_content_allowlist(descriptors, observed_pairs)
                responses = {}
                for desc in parsed:
                    body = bodies[(desc.record_id, desc.filename)]
                    self.assert_body(desc, body)
                    calls.append(('content', desc.record_id, desc.filename))
                    responses[(desc.record_id, desc.filename)] = SimpleNamespace(
                        status=200, actual_child_exit_code=0, url=desc.url, body=body,
                        body_completed_at_utc=COMPLETED)
                self.hooks['journal']({'stage': 'SYNTHETIC_CONTENT_TERMINALS', 'files': len(responses),
                                      'child_authority': 'SEPARATELY_TESTED_FULL_GENUINE_CHILD_VALIDATION'})
                if response_count is not None:
                    if response_count == 99: responses.pop(next(iter(responses)))
                    elif response_count == 101: responses[('24000000', 'unexpected.pdf')] = next(iter(responses.values()))
                    elif response_count == 'active': self.active_children = (99999,)
                self.records.extend({'synthetic': 'terminal content'} for _ in responses)
                return responses

            @staticmethod
            def assert_body(desc, body):
                actual = hashes(body)
                if actual != {'bytes': desc.bytes, 'sha256': desc.sha256, 'md5': desc.md5}:
                    raise AssertionError('wrong descriptor/body join')

            def cancel(self): self.active_children = (); self.records.append({'synthetic': 'cancelled'})
            def close(self): self.check_sources(); self.closed = True

        class MemoryOpener:
            def __init__(self, broker): self.broker = broker

        class Transport:
            def __init__(self, host, token, out, opener):
                self.out = out; out.mkdir(parents=True, exist_ok=True)
                self.opener = opener; self.sequence = 0; transport_constructions.append(opener)
            def request(self, method, url, *, accept):
                rid = url.rsplit('/', 1)[1]
                if isinstance(self.opener, MemoryOpener):
                    body = json.loads(self.opener.broker.metadata(rid, accept).body)
                else:
                    calls.append(('legacy-metadata', rid, accept))
                    body = deepcopy(pairs[rid][0 if accept == registry.CONTEXT['legacy_accept'] else 1])
                self.sequence += 1
                (self.out/f'{self.sequence:03d}_GET.json').write_text(json.dumps(
                    {'method': method, 'url': url, 'accept': accept, 'response': body}))
                return body

        class Response:
            status = 200
            def __init__(self, url, body): self.url = url; self.body = body
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return self.url
            def read(self): return self.body

        class PacedOpener:
            def __init__(self, opener): self.deadline = None
            def open(self, request, timeout):
                parts = request.full_url.split('/')
                key = (parts[-4], parts[-2]); calls.append(('legacy-content', *key))
                return Response(request.full_url, bodies[key])

        class NoRedirect(urllib.request.BaseHandler): pass
        actual_import = catalog.importlib.import_module
        def imports(name, *args, **kwargs):
            if name == 'zenodo_transport': return SimpleNamespace(NoRedirect=NoRedirect, ZenodoTransport=Transport)
            if name == 'first_digest_publisher': return SimpleNamespace(PacedOpener=PacedOpener)
            return actual_import(name, *args, **kwargs)
        stack = ExitStack()
        stack.enter_context(patch.object(runtime, 'validate', return_value=profile))
        stack.enter_context(patch.object(runtime, 'build_worker_source_manifest',
            side_effect=lambda *args: (source_events.append('GENUINE_INITIAL_AUTHORITY_BOUNDARY') or deepcopy(source_manifest))))
        stack.enter_context(patch.object(runtime, 'refresh_worker_source_manifest_data',
            side_effect=lambda root_, manifest: (source_events.append('CURRENT22_DATA_ONLY_REFRESH') or deepcopy(manifest))))
        stack.enter_context(patch.object(catalog.importlib, 'import_module', side_effect=imports))
        stack.enter_context(patch.object(catalog.time, 'monotonic', side_effect=lambda: clock[0]))
        stack.enter_context(patch.object(catalog.owner_worker, 'TransportBroker', Broker))
        stack.enter_context(patch.object(catalog.owner_worker, 'MemoryOpener', MemoryOpener))
        stack.enter_context(patch.object(catalog, 'checked_context', side_effect=lambda root_, profile_, context: context))
        context = catalog.owner_context(root, {'synthetic': 'source profile'}, 'synthetic-private-token', output)
        context.scientific_batch = SimpleNamespace(prepared=True, closed=False, operation='e'*32)
        return stack, context, output, entries, bodies, pairs, calls, brokers, source_events, transport_constructions

    def scope(self, root, context):
        return catalog.operation_scope(root, {'synthetic': 'source profile'}, context)

    def test_exact14_pairs_100_bound_descriptors65pdf_completion_times_rawbytes_and_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); clock = [100.0]
            fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock)
            with fixture, self.scope(root, context):
                data = catalog.scientific_data(root); data.scan_data = {'synthetic': 'complete parent scan'}
                context.prepare_owner_prefetch()
                self.assertEqual(len([v for v in calls if v[0] == 'metadata']), 14)
                self.assertEqual(len([v for v in calls if v[0] == 'content']), 100)
                allowlist = json.loads((output/'observations/CLOSED_CONTENT_ALLOWLIST.json').read_bytes())
                descriptors = allowlist['descriptors']
                self.assertEqual(len(descriptors), 100)
                self.assertEqual(sum(d['source_role'] == 'ORIGINAL' for d in descriptors), 42)
                self.assertEqual(sum(d['source_role'] == 'MANUSCRIPT' for d in descriptors), 58)
                self.assertEqual(sum(d['filename'].endswith('.pdf') for d in descriptors), 65)
                for desc in descriptors:
                    self.assertEqual({k: desc[k] for k in ('bytes', 'sha256', 'md5')}, hashes(bodies[(desc['record_id'], desc['filename'])]))
                    self.assertEqual(len(desc['source_bindings']), 6)
                    for bound in desc['source_bindings']: runtime.read(root, bound)
                stamp = json.loads((output/'observations/0001/OBSERVATION.json').read_bytes())
                self.assertEqual(stamp['observed_at_utc'], COMPLETED)
                self.assertNotEqual(stamp['retained_at_utc'], COMPLETED)
                raw_bound = stamp['actual_raw_http_body']
                raw_http = runtime.read(root, raw_bound)[1]
                self.assertEqual(json.loads(raw_http), pairs['24000000'][0])
                self.assertNotEqual(raw_http, (output/'observations/0001/ACTUAL_BODY.json').read_bytes())
                file_stamp = json.loads(next((output/'bytes').glob('*/GET.json')).read_bytes())
                self.assertEqual(file_stamp['observed_at_utc'], COMPLETED)
                self.assertNotEqual(file_stamp['retained_at_utc'], COMPLETED)
                before = len(calls)
                for key, body in bodies.items(): self.assertEqual(context.download(*key), body)
                self.assertEqual(context.owner_getter('24000000', registry.CONTEXT['native_accept']), pairs['24000000'][1])
                self.assertEqual(len(calls), before)
                self.assertEqual(events.count('GENUINE_INITIAL_AUTHORITY_BOUNDARY'), 1)
                self.assertGreater(events.count('CURRENT22_DATA_ONLY_REFRESH'), 1)
                self.assertEqual(len(constructors), 2)
                self.assertTrue(list((output/'transport/workers').glob('*.json')))
                # Exercise the real timing exporter and a retained JSON
                # roundtrip. The broker/source/clock are fixture seams, so
                # these records cannot establish production spacing or PASS.
                timing = context.observation_timing()
                retained = output/'SYNTHETIC_DEFAULT_HEALTH_TIMING.json'
                retained.write_text(json.dumps({'observation_timing': timing}, sort_keys=True))
                actual = json.loads(retained.read_bytes())['observation_timing']['owner_transport']
                self.assertEqual(actual['header_dispatch_records'], [ACK_SAMPLE])
                self.assertEqual(actual['header_dispatch_records'], brokers[0].header_dispatch_records)
                self.assertEqual(actual['request_records'], brokers[0].records)
                self.assertEqual(actual['requests'], len(actual['request_records']))
                self.assertEqual(actual['header_dispatches'], len(actual['header_dispatch_records']))
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_PREFETCHED'):
                    context.download('24000000', 'not-approved.pdf')
                with self.assertRaises(runtime.PackagingHold):
                    context.owner_getter('99999999', registry.CONTEXT['legacy_accept'])
                self.assertEqual(len(calls), before)
            self.assertTrue(brokers[0].closed)
            with self.assertRaises(runtime.PackagingHold): context.owner_getter('24000000', 'application/json')
            self.assertIsNone(catalog._SCIENCE.get()); self.assertIsNone(catalog._READ_CAPTURE.get())

    def test_no_batch_no_scan_cas_and_duplicate_prefetch_fail_before_further_requests(self):
        for reason in ('batch', 'scan', 'cas', 'duplicate'):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); clock = [100.0]
                fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock)
                with fixture, self.scope(root, context):
                    data = catalog.scientific_data(root); data.scan_data = {'synthetic': 'complete parent scan'}
                    if reason == 'batch': context.scientific_batch = None
                    elif reason == 'scan': data.scan_data = None
                    elif reason == 'cas': data.cas_events.append({'synthetic': 'actual canonical effect'})
                    else: context.prepare_owner_prefetch()
                    before = len(calls)
                    with self.assertRaises(runtime.PackagingHold): context.prepare_owner_prefetch()
                    self.assertEqual(len(calls), before)
                    if reason != 'duplicate': self.assertEqual(calls, [])

    def test_metadata_missing_extra_or_checksum_file_rejects_before_content_requests(self):
        for change in ('missing', 'extra', 'checksum'):
            def modify(pairs):
                rows = pairs['24000000'][1]['files']['entries']
                if change == 'missing': rows.pop(next(iter(rows)))
                elif change == 'extra': rows['unexpected.pdf'] = {'key': 'unexpected.pdf', 'size': 1, 'checksum': 'md5:'+'f'*32}
                else: rows[next(iter(rows))]['checksum'] = 'md5:'+'0'*32
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); clock = [100.0]
                fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock, modify)
                with fixture, self.assertRaises(transport_worker.TransportHold):
                    with self.scope(root, context):
                        catalog.scientific_data(root).scan_data = {'synthetic': 'complete parent scan'}
                        context.prepare_owner_prefetch()
                self.assertEqual(sum(v[0] == 'content' for v in calls), 0)
                self.assertTrue(brokers[0].closed)

    def test_incomplete_extra_or_active_content_results_hold(self):
        for count in (99, 101, 'active'):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); clock = [100.0]
                fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock, response_count=count)
                with fixture, self.assertRaisesRegex(runtime.PackagingHold, 'COMPLETE_TERMINAL_OWNER_CONTENT'):
                    with self.scope(root, context):
                        catalog.scientific_data(root).scan_data = {'synthetic': 'complete parent scan'}
                        context.prepare_owner_prefetch()
                self.assertFalse((output/'bytes').exists())
                self.assertTrue(brokers[0].closed)
                if count == 'active': self.assertIn({'synthetic': 'cancelled'}, brokers[0].records)

    def test_source_archive_or_manifest_changed_cannot_prefetch_body(self):
        for which in ('archive', 'manifest', 'correction'):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); clock = [100.0]
                fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock)
                if which == 'archive': target = Path(entries[0]['archive']['path'])
                elif which == 'manifest':
                    receipt = json.loads(Path(entries[0]['registration']['path']).read_bytes()); target = Path(receipt['digest_manifest']['path'])
                else: target = Path(entries[0]['access_correction']['path'])
                with fixture, self.assertRaises((runtime.PackagingHold, registry.registration.d.DigestHold)):
                    with self.scope(root, context):
                        catalog.scientific_data(root).scan_data = {'synthetic': 'complete parent scan'}
                        target.write_bytes(b'changed source binding')
                        context.prepare_owner_prefetch()
                self.assertFalse(any(v[0] == 'content' for v in calls))

    def test_tampered_replay_or_expiry_never_refetches_and_closes(self):
        for change in ('body', 'raw', 'stamp', 'expired'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve(); clock = [100.0]
                fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock)
                with fixture, self.assertRaises(runtime.PackagingHold):
                    with self.scope(root, context):
                        catalog.scientific_data(root).scan_data = {'synthetic': 'complete parent scan'}
                        context.prepare_owner_prefetch(); before = len(calls)
                        if change == 'expired': clock[0] = 1001.0
                        else:
                            target = {'body': output/'observations/0001/ACTUAL_BODY.json',
                                      'raw': output/'observations/0001/ACTUAL_RAW_HTTP_BODY.json',
                                      'stamp': next((output/'bytes').glob('*/GET.json'))}[change]
                            target.write_bytes(b'{"changed":"retained observation"}')
                        if change == 'stamp': context.download('24000000', 'bundle.zip')
                        else: context.owner_getter('24000000', registry.CONTEXT['legacy_accept'])
                self.assertEqual(len(calls), before)
                self.assertTrue(brokers[0].closed)
                self.assertIsNone(catalog._SCIENCE.get()); self.assertIsNone(catalog._READ_CAPTURE.get())

    def test_nonhealth_synchronous_read_route_keeps_old_single_request_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); clock = [100.0]
            fixture, context, output, entries, bodies, pairs, calls, brokers, events, constructors = self.fixture(root, clock)
            with fixture, self.scope(root, context):
                first = context.owner_getter('24000000', registry.CONTEXT['legacy_accept'])
                self.assertEqual(first, pairs['24000000'][0])
                self.assertEqual(context.download('24000000', 'paper.pdf'), bodies[('24000000', 'paper.pdf')])
                context.owner_getter('24000000', registry.CONTEXT['legacy_accept'])
                context.download('24000000', 'paper.pdf')
                self.assertEqual(calls, [('legacy-metadata', '24000000', registry.CONTEXT['legacy_accept']),
                                         ('legacy-content', '24000000', 'paper.pdf')])
                self.assertEqual(len(constructors), 1)
                self.assertEqual(brokers, [])
                self.assertEqual(events, [])


if __name__ == '__main__': unittest.main()
