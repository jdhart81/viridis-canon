"""Closed-input and actual-byte regressions; fixture science is not authority."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE.parent))
# Production gets this exact module from its validated installed closure.
gates = HERE.parents[2] / 'RESEARCH_PIPELINE_v2/verification_coverage_gates'
if gates.is_dir():
    sys.path.insert(2, str(gates))
    sys.path.insert(3, str(HERE.parents[2] / 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001'))
    sys.path.insert(4, str(HERE.parents[2] / 'reports/verification-coverage/2026-10-04/game-plan-completion/late-version-chain-consolidated-review-v004/implementation'))
else:
    # The public packet is nested two levels below its unchanged gate modules.
    sys.path.insert(2, str(HERE.parents[1]))
import manuscript_access_registry as registry
import methods_digest_registration_v3 as registration
import manuscript_access_correction as access


class AccessRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.paper = b'%PDF-1.4\nexact old note paper\n%%EOF'
        stream = BytesIO()
        with zipfile.ZipFile(stream, 'w') as z:
            z.writestr('notes/Run-167/paper.pdf', self.paper)
        archived = stream.getvalue()
        blobs = {'paper.pdf': b'%PDF-summary', 'paper.tex': b'digest source', 'metadata.json': b'{}', 'METHODS_NOTES.zip': archived}
        manifest = {'notes': [{'run_id': 'Run-167', 'uploads': [{'filename': 'paper.pdf', 'sha256': hashlib.sha256(self.paper).hexdigest()}]}],
                    'archive_members': [{'path': 'notes/Run-167/paper.pdf', **access._hashes(self.paper)}],
                    'uploads': [{'filename': n, **access._hashes(b)} for n, b in blobs.items()]}
        manifest_binding = self.write('DIGEST_MANIFEST.json', manifest)
        blobs['DIGEST_MANIFEST.json'] = (self.root / 'DIGEST_MANIFEST.json').read_bytes()
        blobs['PUBLICATION_BINDING.json'] = b'original binding bytes'
        originals = [{'filename': n, **access._hashes(b)} for n, b in blobs.items()]
        files = [{'key': r['filename'], 'size': r['bytes'], 'checksum': 'md5:' + r['md5']} for r in originals]
        old_l = {'id': 23290748, 'conceptrecid': '23226760', 'created': '2000-01-01T00:00:00+00:00',
                 'doi': '10.5281/zenodo.23290748', 'metadata': {'title': 'unchanged science', 'license': 'cc-by-4.0',
                    'relations': {'version': [{'is_last': True}]}}, 'files': files}
        old_n = {'id': '23290748', 'pids': {'doi': {'identifier': old_l['doi']}}, 'metadata': deepcopy(old_l['metadata']),
                 'parent': {'id': '23226760', 'access': {'owned_by': {'user': '1591505'}, 'grants': [], 'links': []}},
                 'created': old_l['created'],
                 'versions': {'is_latest': True, 'is_latest_draft': True, 'index': 1},
                 'files': {'entries': {f['key']: deepcopy(f) for f in files}, 'count': len(files), 'total_bytes': sum(f['size'] for f in files)}}
        self.copy = {'run_id': 'Run-167', 'member': 'notes/Run-167/paper.pdf', 'filename': 'Run-167-Carbon-Albedo-Paper.pdf', **access._hashes(self.paper)}
        self.after_l, self.after_n = deepcopy(old_l), deepcopy(old_n)
        added = {'key': self.copy['filename'], 'size': self.copy['bytes'], 'checksum': 'md5:' + self.copy['md5']}
        self.after_l['files'].append(added)
        self.after_n['files']['entries'][added['key']] = deepcopy(added)
        self.after_n['files']['count'] += 1
        self.after_n['files']['total_bytes'] += self.copy['bytes']
        blobs[self.copy['filename']] = self.paper
        self.blobs = blobs
        self.registration = self.write('registration.json', {'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2', 'record_id': '23290748'})
        self.admitted = {'receipt': {'record_id': '23290748', 'doi': old_l['doi'], 'digest_manifest': manifest_binding},
                         'manifest': manifest, 'public_legacy': old_l, 'public_native': old_n, 'strict_readback': {'fixture_science_only': True}}
        instruction = {'standard': 'VRS-DIRECT-USER-MANUSCRIPT-ACCESS-INSTRUCTION-1', 'evidence_kind': 'DIRECT_HUMAN_USER_MESSAGE',
                       'recorded_at_utc': 'fixture time', 'task_id': '01a12d47-02a3-78f3-beb4-6b8e1a079dd2',
                       'user_message_verbatim': registry.USER_REQUEST, 'source': 'fixture source', 'claim': 'not actual authority',
                       'authorized_scope': {'owned_published_deposits': True, 'separate_actual_manuscript_pdfs': True,
                                            'preserve_original_scientific_evidence': True, 'make_pdf_requirement_future_release_standard': True},
                       'does_not_authorize': {'new_scientific_certification': True, 'changed_original_archives': True, 'expanded_automatic_scientific_publication': True}}
        provider = {'standard': 'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1', 'provider_tool': 'mcp__codex_app__read_thread',
                    'captured_at_utc': 'fixture time', 'thread_id': instruction['task_id'], 'thread_title': 'fixture',
                    'turn_id': '01a132f6-46cd-7e41-9c02-f8ca68567a46', 'projection': 'fixture', 'validation_pass_claimed': False,
                    'user_messages': [{'type': 'userMessage', 'id': '01a132f6-4708-7440-a9ba-ebf03deeb906',
                                       'content': [{'type': 'text', 'text': registry.USER_REQUEST + '\n'}]}]}
        self.instruction = self.write('instruction.json', instruction)
        self.provider = self.write('provider.json', provider)
        plan_row = {**self.copy, 'archive_member': self.copy['member'], 'action': 'ALREADY_PRESENT'}
        self.plan = self.write('plan.json', {'records': [{'record_id': 23290748, 'doi': old_l['doi'], 'manuscripts': [plan_row]}]})
        self.authority_value = {'standard': 'VRS-USER-MANUSCRIPT-ACCESS-AUTHORITY-1', 'status': 'SOURCE_BOUND_USER_INSTRUCTION',
                                'record_id': '23290748', 'doi': old_l['doi'], 'instruction': self.instruction,
                                'provider_instruction': self.provider, 'copy_plan': self.plan, 'scientific_change': False}
        self.authority = self.write('authority.json', self.authority_value)
        self.correction_value = {'standard': access.STANDARD, 'status': 'EXACT_EXISTING_ARCHIVE_ACCESS_COPIES',
                                 'record_id': '23290748', 'doi': old_l['doi'], 'source_manifest_sha256': manifest_binding['sha256'],
                                 'source_archive_sha256': access._hashes(archived)['sha256'], 'original_files': originals,
                                 'copies': [self.copy], 'authority': self.authority}
        correction = self.write('correction.json', self.correction_value)
        archive = self.write_bytes('METHODS_NOTES.zip', archived)
        self.entry = {'record_id': '23290748', 'registration': self.registration, 'archive': archive,
                      'access_correction': correction, 'user_authority': self.authority, 'prior_chain': None}
        self.registry_value = {'standard': registry.STANDARD, 'status': 'NOMINATED_INPUTS_NOT_AUTHORITY',
                               'observation_context': deepcopy(registry.CONTEXT), 'entries': [self.entry]}
        self.registry_binding = self.write('registry.json', self.registry_value)

    def write_bytes(self, name, value):
        path = self.root / name
        path.write_bytes(value)
        return {'path': str(path), 'sha256': hashlib.sha256(value).hexdigest()}

    def write(self, name, value):
        return self.write_bytes(name, json.dumps(value, sort_keys=True).encode())

    def context(self, **kwargs):
        return registry.RegistryContext(self.root, self.registry_binding,
                                        download=kwargs.pop('download', lambda rid, name: self.blobs[name]),
                                        observation_context=kwargs.pop('observation_context', deepcopy(registry.CONTEXT)),
                                        owner_getter=kwargs.pop('owner_getter', None), **kwargs)

    def fixture_authority(self):
        # Test fixtures cannot be real authority: only this test patches pins.
        stack = ExitStack()
        for constant, source in [('DIRECT_USER_EVIDENCE_SHA256', self.instruction),
                                 ('PROVIDER_USER_EVIDENCE_SHA256', self.provider),
                                 ('REVIEWED_ARCHIVE_COPY_PLAN_SHA256', self.plan)]:
            stack.enter_context(patch.object(registry, constant, source['sha256']))
        return stack

    def admitted_call(self, context, **kwargs):
        with patch.object(registration, 'require_registration', return_value=deepcopy(self.admitted)) as science:
            value = context.require_registration(self.root, self.registration, views=(self.after_l, self.after_n), **kwargs)
        self.assertEqual(science.call_args.kwargs['views'], None)
        return value

    def test_original_admission_precedes_exact_full_actual_copy_readback(self):
        with self.fixture_authority():
            value = self.admitted_call(self.context())
        self.assertEqual(value['public_legacy'], self.after_l)
        self.assertEqual(value['public_native'], self.after_n)
        self.assertEqual(value['registered_public_views']['native'], self.admitted['public_native'])
        self.assertEqual(value['strict_readback'], self.admitted['strict_readback'])
        self.assertFalse(value['prior_processing_audit']['access_correction']['certifies'])

    def test_nomination_requires_fresh_owner_gets_if_views_absent(self):
        calls = []
        def getter(rid, accept):
            calls.append((rid, accept))
            return self.after_l if accept == registry.CONTEXT['legacy_accept'] else self.after_n
        with self.fixture_authority(), patch.object(registration, 'require_registration', return_value=deepcopy(self.admitted)):
            self.context(owner_getter=getter).require_registration(self.root, self.registration)
        self.assertEqual(calls, [('23290748', registry.CONTEXT['legacy_accept']), ('23290748', registry.CONTEXT['native_accept'])])

    def test_changed_public_paper_bytes_rejected(self):
        with self.fixture_authority(), self.assertRaisesRegex(access.AccessCorrectionHold, 'PUBLIC_PDF_BYTES'):
            self.admitted_call(self.context(download=lambda rid, name: b'%PDF-modified' if name == self.copy['filename'] else self.blobs[name]))

    def test_anonymous_view_context_is_not_owner(self):
        wrong = {**registry.CONTEXT, 'authentication': 'ANONYMOUS'}
        with self.assertRaisesRegex(registration.RegistrationHold, 'OWNER_OBSERVATION_CONTEXT'):
            self.context(observation_context=wrong)

    def test_actual_anonymous_field_absence_remains_hold(self):
        self.after_n['parent']['access'].pop('grants')
        with self.fixture_authority(), self.assertRaisesRegex(access.AccessCorrectionHold, 'UNCHANGED_ALL_OTHER'):
            self.admitted_call(self.context())

    def test_cached_pass_cannot_replace_recorded_user_input(self):
        self.authority_value['status'] = 'EXACT_USER_ACCESS_COPY_AUTHORITY_PASS'
        self.entry['user_authority'] = self.write('authority.json', self.authority_value)
        self.correction_value['authority'] = self.entry['user_authority']
        self.entry['access_correction'] = self.write('correction.json', self.correction_value)
        self.registry_binding = self.write('registry.json', self.registry_value)
        with self.fixture_authority(), self.assertRaisesRegex(registration.RegistrationHold, 'CLOSED_USER_AUTHORITY_INPUT'):
            self.admitted_call(self.context())

    def test_fixture_human_text_is_not_real_production_authority(self):
        with self.assertRaisesRegex(registration.RegistrationHold, 'GENUINE_REVIEWED_USER_AND_PLAN_SOURCES'):
            self.admitted_call(self.context())

    def test_original_registered_archive_cannot_be_substituted(self):
        self.entry['archive'] = self.write_bytes('other.zip', b'unrelated archive')
        self.registry_binding = self.write('registry.json', self.registry_value)
        with self.fixture_authority(), self.assertRaisesRegex(registration.RegistrationHold, 'ADMITTED_ORIGINAL_ARCHIVE_HASH'):
            self.admitted_call(self.context())

    def test_duplicate_nomination_is_not_automatic_discovery(self):
        self.registry_value['entries'].append(deepcopy(self.entry))
        self.registry_binding = self.write('registry.json', self.registry_value)
        with self.assertRaisesRegex(registration.RegistrationHold, 'UNIQUE_NOMINATION'):
            self.context()

    def test_source_change_after_context_creation_is_not_cached_pass(self):
        context = self.context()
        (self.root / 'registry.json').write_text('{}')
        with self.assertRaises(registration.d.DigestHold):
            context.require_registration(self.root, self.registration)

    def test_same_record_cannot_use_a_different_registration_binding(self):
        other = self.write('different.json', {'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2', 'record_id': '23290748', 'extra': True})
        with self.assertRaisesRegex(registration.RegistrationHold, 'DIFFERENT_REGISTRATION'):
            self.context().require_registration(self.root, other)

    def test_flags_cannot_change_without_genuine_chain(self):
        self.after_n['versions']['is_latest'] = False
        with self.fixture_authority(), self.assertRaisesRegex(access.AccessCorrectionHold, 'UNCHANGED_ALL_OTHER'):
            self.admitted_call(self.context())

    def test_chain_requires_actual_bound_owner_baseline(self):
        with self.assertRaisesRegex(registration.RegistrationHold, 'CLOSED_GENUINE_CHAIN_INPUTS'):
            self.admitted_call(self.context(), prior_chain_receipts={'creation': None, 'publish': None})

    def chain(self, baseline):
        legacy, native = baseline
        def get(name, body, accept):
            return self.write(name, {'environment': 'zenodo.org', 'method': 'GET',
                'url': 'https://zenodo.org/api/records/23290748', 'accept': accept,
                'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'http_status': 200,
                'request_body_sha256': None, 'response': deepcopy(body)})
        self.creation_value = {'environment': 'zenodo.org', 'method': 'POST',
            'url': 'https://zenodo.org/api/deposit/depositions/23290748/actions/newversion',
            'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'http_status': 201,
            'request_body_sha256': hashlib.sha256(b'{}').hexdigest(),
            'response': {'id': 24000001, 'conceptrecid': '23226760', 'created': '2001-01-01T00:00:00+00:00'}}
        self.publish_value = {'environment': 'zenodo.org', 'method': 'POST',
            'url': 'https://zenodo.org/api/deposit/depositions/24000001/actions/publish',
            'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'http_status': 202,
            'response': {'id': 24000001, 'conceptrecid': '23226760',
                         'doi': '10.5281/zenodo.24000001', 'created': '2002-01-01T00:00:00+00:00'}}
        return {'baseline_legacy': get('chain-legacy.json', legacy, registry.CONTEXT['legacy_accept']),
                'baseline_native': get('chain-native.json', native, registry.CONTEXT['native_accept']),
                'creation': self.write('chain-creation.json', self.creation_value),
                'publish': self.write('chain-publish.json', self.publish_value)}

    def set_published_flags(self, legacy, native):
        native['versions']['is_latest_draft'] = False
        native['versions']['is_latest'] = False
        legacy['metadata']['relations']['version'][0]['is_last'] = False

    def test_access_then_genuine_chain_preserves_full_observed_pairs(self):
        baseline = (deepcopy(self.after_l), deepcopy(self.after_n))
        chain = self.chain(baseline)
        self.set_published_flags(self.after_l, self.after_n)
        with self.fixture_authority():
            value = self.admitted_call(self.context(), prior_chain_receipts=chain)
        audit = value['prior_processing_audit']
        self.assertEqual(audit['access_correction']['observed_after']['native'], baseline[1])
        actual = audit['genuine_chain_audits'][0]['pair']
        self.assertEqual(actual['observed_before']['native'], baseline[1])
        self.assertEqual(actual['observed_after']['native'], self.after_n)
        self.assertEqual(value['strict_readback'], self.admitted['strict_readback'])

    def test_historical_chain_then_access_uses_actual_postchain_snapshot(self):
        baseline = (deepcopy(self.admitted['public_legacy']), deepcopy(self.admitted['public_native']))
        self.set_published_flags(*baseline)
        chain = self.chain(baseline)
        self.entry['prior_chain'] = {'stage': 'BEFORE_ACCESS', **chain}
        self.registry_binding = self.write('registry.json', self.registry_value)
        self.set_published_flags(self.after_l, self.after_n)
        with self.fixture_authority():
            value = self.admitted_call(self.context())
        audit = value['prior_processing_audit']
        self.assertEqual(audit['access_correction']['observed_before']['native'], baseline[1])
        self.assertEqual(audit['genuine_chain_audits'][0]['pair']['observed_before']['native'], self.admitted['public_native'])

    def test_cached_chain_pass_cannot_replace_actual_operation(self):
        chain = self.chain((self.after_l, self.after_n))
        chain['creation'] = self.write('chain-creation.json', {'status': 'PRIOR_RECORD_PROTECTED_READBACK_PASS'})
        with self.fixture_authority(), self.assertRaisesRegex(ValueError, 'GENUINE_OWN_CHAIN_RECEIPT'):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def test_wrong_newer_version_is_rejected(self):
        chain = self.chain((self.after_l, self.after_n))
        self.publish_value['response']['id'] = 24000002
        chain['publish'] = self.write('chain-publish.json', self.publish_value)
        with self.fixture_authority(), self.assertRaisesRegex(ValueError, 'OWN_TERMINAL_PUBLISH'):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def test_wrong_parent_is_rejected(self):
        chain = self.chain((self.after_l, self.after_n))
        self.creation_value['response']['conceptrecid'] = '99999999'
        chain['creation'] = self.write('chain-creation.json', self.creation_value)
        with self.fixture_authority(), self.assertRaisesRegex(ValueError, 'OWN_DISTINCT_SAME_PARENT'):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def test_chain_does_not_authorize_permissions_change(self):
        chain = self.chain((self.after_l, self.after_n))
        self.set_published_flags(self.after_l, self.after_n)
        self.after_n['parent']['access']['grants'] = [{'subject': 'unapproved'}]
        with self.fixture_authority(), self.assertRaisesRegex(ValueError, 'PROTECTED_CONTENT_CHANGED'):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def test_altered_bound_chain_operation_is_rejected(self):
        chain = self.chain((self.after_l, self.after_n))
        Path(chain['creation']['path']).write_text('{}')
        with self.assertRaises(registration.d.DigestHold):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def test_chain_does_not_authorize_version_index_change(self):
        chain = self.chain((self.after_l, self.after_n))
        self.set_published_flags(self.after_l, self.after_n)
        self.after_n['versions']['index'] = 2
        with self.fixture_authority(), self.assertRaisesRegex(ValueError, 'PROTECTED_CONTENT_CHANGED'):
            self.admitted_call(self.context(), prior_chain_receipts=chain)

    def v3_chain_science(self):
        admitted = {**deepcopy(self.admitted), 'receipt': {**deepcopy(self.admitted['receipt']), 'standard': registration.STANDARD},
                    'public_legacy': deepcopy(self.after_l), 'public_native': deepcopy(self.after_n)}
        def science(*args, **kwargs):
            result = deepcopy(admitted)
            pair = kwargs.get('views')
            if pair is not None:
                result.update(public_legacy=deepcopy(pair[0]), public_native=deepcopy(pair[1]), prior_processing_audit={'fixture_baseline_only': True})
            return result
        return science

    def test_future_v3_full_observed_chain_needs_no_access_exception(self):
        chain = self.chain((self.after_l, self.after_n))
        science = self.v3_chain_science()
        self.set_published_flags(self.after_l, self.after_n)
        self.registry_value['entries'] = []
        self.registry_binding = self.write('registry.json', self.registry_value)
        v3 = self.write('new-v3.json', {'standard': registration.STANDARD, 'record_id': '23290748'})
        with patch.object(registration, 'require_registration', side_effect=science) as calls:
            result = self.context().require_registration(self.root, v3, views=(self.after_l, self.after_n), prior_chain_receipts=chain)
        self.assertIsNone(calls.call_args_list[0].kwargs['views'])
        self.assertEqual(len(calls.call_args_list), 2)
        self.assertEqual(result['public_native'], self.after_n)
        self.assertEqual(result['prior_processing_audit']['route'], 'GENUINE_V3_FULL_OBSERVED_BASELINE_CHAIN')

    def test_future_v3_resume_after_creation_preserves_actual_published_latest(self):
        chain = self.chain((self.after_l, self.after_n))
        chain['publish'] = None
        science = self.v3_chain_science()
        self.after_n['versions']['is_latest_draft'] = False
        self.registry_value['entries'] = []
        self.registry_binding = self.write('registry.json', self.registry_value)
        v3 = self.write('new-v3.json', {'standard': registration.STANDARD, 'record_id': '23290748'})
        with patch.object(registration, 'require_registration', side_effect=science):
            result = self.context().require_registration(self.root, v3, views=(self.after_l, self.after_n), prior_chain_receipts=chain)
        self.assertEqual(result['public_native'], self.after_n)
        self.assertTrue(result['public_native']['versions']['is_latest'])
        self.assertTrue(result['public_legacy']['metadata']['relations']['version'][0]['is_last'])
        self.assertEqual(result['prior_processing_audit']['genuine_chain_audits'][0]['pair']['chain_state'], 'OWN_CREATED')

    def test_future_v3_creation_does_not_authorize_published_latest_change(self):
        chain = self.chain((self.after_l, self.after_n))
        chain['publish'] = None
        science = self.v3_chain_science()
        self.set_published_flags(self.after_l, self.after_n)
        self.registry_value['entries'] = []
        self.registry_binding = self.write('registry.json', self.registry_value)
        v3 = self.write('new-v3.json', {'standard': registration.STANDARD, 'record_id': '23290748'})
        with patch.object(registration, 'require_registration', side_effect=science), self.assertRaisesRegex(ValueError, 'PROTECTED_CONTENT_CHANGED'):
            self.context().require_registration(self.root, v3, views=(self.after_l, self.after_n), prior_chain_receipts=chain)

    def test_persistent_chain_only_v3_nomination_uses_fresh_owner_pair(self):
        chain = self.chain((self.after_l, self.after_n))
        science = self.v3_chain_science()
        self.set_published_flags(self.after_l, self.after_n)
        self.entry.update(registration=self.write('v3.json', {'standard': registration.STANDARD, 'record_id': '23290748'}),
                          archive=None, access_correction=None, user_authority=None, prior_chain={'stage': 'AFTER_ACCESS', **chain})
        self.registry_binding = self.write('registry.json', self.registry_value)
        def getter(rid, accept):
            return self.after_l if accept == registry.CONTEXT['legacy_accept'] else self.after_n
        with patch.object(registration, 'require_registration', side_effect=science):
            result = self.context(owner_getter=getter).require_registration(self.root, self.entry['registration'])
        self.assertEqual(result['public_native'], self.after_n)

    def test_chain_only_nomination_cannot_bypass_v1_access_evidence(self):
        chain = self.chain((self.after_l, self.after_n))
        self.entry.update(archive=None, access_correction=None, user_authority=None, prior_chain={'stage': 'AFTER_ACCESS', **chain})
        self.registry_binding = self.write('registry.json', self.registry_value)
        with self.assertRaisesRegex(registration.RegistrationHold, 'EXPLICIT_CHAIN_ONLY_V3'):
            self.context()

    def test_partial_null_access_entry_is_not_valid_nomination(self):
        self.entry['archive'] = None
        self.registry_binding = self.write('registry.json', self.registry_value)
        with self.assertRaisesRegex(registration.RegistrationHold, 'NO_PARTIAL_ACCESS'):
            self.context()

    def test_future_v3_without_legacy_access_nomination_delegates(self):
        self.registry_value['entries'] = []
        self.registry_binding = self.write('registry.json', self.registry_value)
        v3 = self.write('new-v3.json', {'standard': registration.STANDARD, 'record_id': '24000001'})
        with patch.object(registration, 'require_registration', return_value={'fixture_v3': True}) as consume:
            value = self.context().require_registration(self.root, v3)
        self.assertEqual(value, {'fixture_v3': True})
        self.assertEqual(consume.call_args.args[1], v3)


if __name__ == '__main__':
    unittest.main()
