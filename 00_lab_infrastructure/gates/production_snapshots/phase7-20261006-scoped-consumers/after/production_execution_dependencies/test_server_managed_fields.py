from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from server_managed_fields import (
    ServerManagedMismatch, audit_readback, validate_amendment,
    validate_new_version, validate_prior_version, require_revision,
    transport_contract_sha256, require_ui_display, audit_version_chain, require_derived_previews,
)
from zenodo_transport import TransportHold


class ServerManagedFieldsTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'id': '1001', 'metadata': {'title': 'Exact title', 'description': '<p>Exact claim</p>',
                'keywords': ['uncertified'], 'communities': [{'id': 'existing'}]},
            'pids': {'doi': {'identifier': '10.5281/zenodo.1001', 'provider': 'datacite'},
                     'other': {'identifier': 'unchanged', 'provider': 'local'}},
            'parent': {'id': '77', 'pids': {'doi': {'identifier': '10.5281/zenodo.77', 'provider': 'datacite'}}},
            'versions': {'index': 1, 'is_latest': True, 'other': 'unchanged'},
            'custom_fields': {}, 'access': {'record': 'public', 'files': 'public'},
            'created': '2026-10-04T01:00:00Z', 'updated': '2026-10-04T01:00:00Z', 'revision_id': 1,
            'links': {'self': 'https://zenodo.org/api/records/1001', 'parent': 'https://zenodo.org/api/records/77'},
            'stats': {'views': 0}, 'is_draft': False, 'is_published': True,
            'ui': {'is_draft': False, 'other': 'exact'},
            'deletion_status': {'is_deleted': False, 'status': 'P'}, 'expires_at': None, 'swh': {},
            'files': [{'key': f'file-{i}.txt', 'checksum': f'md5:{i:032x}', 'size': i + 1,
                       'id': str(i), 'mimetype': 'text/plain', 'extra': {'keep': True}} for i in range(6)],
        }
        self.context = {'host': 'zenodo.org', 'record_id': '1001',
            'same_operation_response': {'id': '1001', 'doi': '10.5281/zenodo.1001', 'conceptdoi': '10.5281/zenodo.77'},
            'existing_concept_doi': '10.5281/zenodo.77', 'previous_latest_index': 0, 'chain_parent_id': '77',
            'temporal_baseline': deepcopy(self.expected),
            'same_operation_reservation_id': '1001',
            'own_publish_response': {'method': 'POST', 'url': 'https://zenodo.org/api/records/1001/draft/actions/publish',
                'http_status': 202, 'response': {'id': '1001'}, 'environment': 'zenodo.org',
                'accept': 'application/json', 'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE',
                'response_sha256': hashlib.sha256(b'{"id":"1001"}').hexdigest()}}
        self.context['temporal_baseline']['ui']['is_draft'] = True
        self.context['temporal_baseline']['expires_at'] = '2026-10-05T01:00:00Z'
        self.context['temporal_baseline']['revision_id'] = 31
        self.context['temporal_baseline'].pop('swh')
        self.context['temporal_baseline'].pop('deletion_status')
        self.actual = deepcopy(self.expected)
        self.context['revision_evidence'] = self.evidence()

    def evidence(self, publish=None, native=None, host='zenodo.org'):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        publish = deepcopy(publish if publish is not None else self.context['own_publish_response'])
        native = deepcopy(native if native is not None else self.expected)
        get = {'method': 'GET', 'url': 'https://' + host + '/api/records/1001', 'environment': host,
            'accept': 'application/vnd.inveniordm.v1+json', 'http_status': 200,
            'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'response': native,
            'response_sha256': hashlib.sha256(json.dumps(native).encode()).hexdigest()}
        for name, receipt in (('001_POST.json', publish), ('002_GET.json', get)):
            Path(directory.name, name).write_text(json.dumps(receipt))
        return {'receipt_directory': directory.name, 'publish_receipt_name': '001_POST.json',
            'first_native_get_receipt_name': '002_GET.json', 'transport_contract_sha256': transport_contract_sha256()}

    def change_receipt(self, evidence, name, mutate):
        path = Path(evidence['receipt_directory'], name)
        value = json.loads(path.read_text()); mutate(value); path.write_text(json.dumps(value))

    def check(self, actual=None, expected=None, **extra):
        context = self.context | extra
        if 'revision_evidence' not in extra and isinstance(context.get('own_publish_response'), dict):
            context['revision_evidence'] = self.evidence(context['own_publish_response'], host=context['host'])
        return validate_new_version(actual or self.actual, expected or self.expected, **context)

    def saved_chain_receipt(self, directory, name, method, url, response, *, status=201):
        receipt = {'method': method, 'url': url, 'environment': 'zenodo.org',
            'accept': 'application/json', 'http_status': status,
            'status': 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE', 'response': response,
            'response_sha256': hashlib.sha256(json.dumps(response).encode()).hexdigest(),
            'request_body_sha256': hashlib.sha256(b'{}' if method == 'POST' else b'').hexdigest()}
        if status == 404:
            receipt.update(accept='application/vnd.inveniordm.v1+json',
                status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY', error_type='HTTPError')
        path = Path(directory, name); path.write_text(json.dumps(receipt))
        return {'receipt_path': str(path), 'receipt_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'transport_contract_sha256': transport_contract_sha256()}

    def chain_fixture(self, boundary='CREATE', *, prior_before=None, prior_actual=None):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        initial = deepcopy(self.expected if prior_before is None else prior_before)
        initial['versions'].update(is_latest=True, is_latest_draft=True)
        prior = deepcopy(initial) if prior_actual is None else deepcopy(prior_actual)
        prior['versions']['is_latest_draft'] = False
        child = deepcopy(initial); child['id'] = '1002'
        child['pids']['doi']['identifier'] = '10.5281/zenodo.1002'
        child['links']['self'] = 'https://zenodo.org/api/records/1002'
        child['versions'].update(index=initial['versions']['index'] + 1,
                                 is_latest=False, is_latest_draft=True)
        child.update(is_draft=True, is_published=False)
        child['ui']['is_draft'] = True; child['expires_at'] = '2026-10-05T01:00:00Z'
        creation = self.saved_chain_receipt(directory.name, '001_POST.json', 'POST',
            'https://zenodo.org/api/deposit/depositions/1001/actions/newversion',
            {'id': '1002', 'conceptrecid': '77', 'submitted': False, 'state': 'unsubmitted'})
        ctx = {'boundary': boundary, 'prior_record_id': '1001', 'successor_record_id': '1002',
            'chain_parent_id': '77', 'prior_before_create': initial, 'prior_actual': prior,
            'successor_actual': child, 'successor_expected': deepcopy(child),
            'creation_evidence': creation, 'operation_evidence': None,
            'successor_before_boundary': None, 'successor_absence_evidence': None}
        if boundary == 'PUBLISH':
            ctx['successor_before_boundary'] = deepcopy(child)
            prior['versions']['is_latest'] = False
            child['versions']['is_latest'] = True
            child.update(is_draft=False, is_published=True); child['ui']['is_draft'] = False
            child['expires_at'] = None
            ctx['successor_expected'] = deepcopy(child)
            ctx['operation_evidence'] = self.saved_chain_receipt(directory.name, '002_POST.json', 'POST',
                'https://zenodo.org/api/deposit/depositions/1002/actions/publish', {'id': '1002'}, status=202)
        elif boundary == 'DISCARD':
            ctx['successor_before_boundary'] = deepcopy(child)
            ctx['prior_actual'] = deepcopy(initial)
            ctx['successor_actual'] = ctx['successor_expected'] = None
            ctx['operation_evidence'] = self.saved_chain_receipt(directory.name, '002_POST.json', 'POST',
                'https://zenodo.org/api/deposit/depositions/1002/actions/discard', {'id': '1002'}, status=200)
            ctx['successor_absence_evidence'] = self.saved_chain_receipt(directory.name, '003_GET.json', 'GET',
                'https://zenodo.org/api/records/1002/draft', {'message': 'Not found'}, status=404)
        elif boundary == 'EDIT':
            ctx['prior_actual'] = deepcopy(initial)
            ctx.update(successor_record_id=None, successor_actual=None, successor_expected=None,
                       creation_evidence=None)
            ctx['operation_evidence'] = self.saved_chain_receipt(directory.name, '002_POST.json', 'POST',
                'https://zenodo.org/api/deposit/depositions/1001/actions/edit', {'id': '1001'}, status=200)
        return ctx

    def assert_chain_pass(self, ctx):
        report = audit_version_chain(host='zenodo.org', **ctx)
        self.assertEqual(report['status'], 'VERSION_CHAIN_STATE_PASS', report)
        return report

    def assert_chain_hold(self, ctx, reason=None):
        report = audit_version_chain(host='zenodo.org', **ctx)
        self.assertEqual(report['status'], 'HOLD', report)
        if reason is not None: self.assertIn(reason, json.dumps(report))
        return report

    def receipt_backed_prior_pass(self, actual, before):
        ctx = self.chain_fixture('PUBLISH', prior_before=before, prior_actual=actual)
        return validate_prior_version(ctx['prior_actual'], ctx['prior_before_create'],
            host='zenodo.org', record_id='1001', chain_parent_id='77', version_chain_context=ctx)

    def test_row1_added_own_host_oai_and_preexisting_pids_exact_pass(self):
        self.actual['pids']['oai'] = {'identifier': 'oai:zenodo.org:1001', 'provider': 'oai'}
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row1_wrong_host_provider_id_or_preexisting_pid_must_fail(self):
        for oai in ({'identifier': 'oai:sandbox.zenodo.org:1001', 'provider': 'oai'},
                    {'identifier': 'oai:zenodo.org:1002', 'provider': 'oai'},
                    {'identifier': 'oai:zenodo.org:1001', 'provider': 'external'}):
            actual = deepcopy(self.expected); actual['pids']['oai'] = oai
            with self.subTest(oai=oai), self.assertRaises(ServerManagedMismatch): self.check(actual)
        self.actual['pids']['other']['identifier'] = 'changed'
        with self.assertRaises(ServerManagedMismatch): self.check()

    def test_row2_same_response_doi_existing_concept_pass(self):
        self.assertEqual(self.check()['checks']['minted_doi_and_existing_concept']['status'], 'PASS')

    def test_row2_wrong_minted_doi_concept_or_response_identity_must_fail(self):
        for edit in ('doi', 'concept', 'response'):
            actual = deepcopy(self.expected); context = deepcopy(self.context)
            if edit == 'doi': actual['pids']['doi']['identifier'] = '10.5281/zenodo.1002'
            elif edit == 'concept': actual['parent']['pids']['doi']['identifier'] = '10.5281/zenodo.78'
            else: context['same_operation_response']['id'] = '1002'
            with self.subTest(edit=edit), self.assertRaises(ServerManagedMismatch):
                validate_new_version(actual, self.expected, **context)

    def test_row3_existing_community_mirror_and_public_preservation_pass(self):
        self.actual['custom_fields']['legacy:communities'] = ['existing']
        self.assertEqual(self.check(existing_communities=[{'id': 'existing'}],
            public_communities=[{'id': 'existing'}], mirror_proof={'status': 'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN',
            'public_post_publish_exact_preservation': True})['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row3_wrong_member_missing_proof_or_public_membership_must_fail(self):
        self.actual['custom_fields']['legacy:communities'] = ['new-member']
        with self.assertRaises(ServerManagedMismatch): self.check(existing_communities=[{'id': 'existing'}],
            public_communities=[{'id': 'existing'}], mirror_proof={'status': 'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN',
            'public_post_publish_exact_preservation': True})
        self.actual['custom_fields']['legacy:communities'] = ['existing']
        for public, proof in (([{'id': 'existing'}], None), (None, {'status': 'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN',
                             'public_post_publish_exact_preservation': True})):
            with self.assertRaises(ServerManagedMismatch):
                self.check(existing_communities=[{'id': 'existing'}], public_communities=public, mirror_proof=proof)

    def test_row4_aware_monotonic_time_integer_revision_pass(self):
        self.actual.update(created='2026-10-04T02:00:00+00:00', updated='2026-10-04T03:00:00Z', revision_id=2)
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row4_decreasing_naive_time_bool_or_unevidenced_revision_reset_must_fail(self):
        for changes in ({'updated': '2026-10-04T00:59:00Z'}, {'created': '2026-10-04T01:00:00'}, {'revision_id': True}):
            actual = deepcopy(self.expected); actual.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ServerManagedMismatch): self.check(actual)
        baseline = deepcopy(self.expected); baseline['revision_id'] = 31
        actual = deepcopy(self.expected); actual['revision_id'] = 3
        with self.assertRaisesRegex(ServerManagedMismatch, 'OWN_PUBLISH_POST_RECEIPT_REQUIRED'):
            self.check(actual, temporal_baseline=baseline, own_publish_response=None)

    def test_row5_next_index_latest_true_parent_and_prior_false_pass(self):
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')
        prior = deepcopy(self.expected); prior['versions']['is_latest'] = False
        self.assertEqual(self.receipt_backed_prior_pass(prior, self.expected)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row5_wrong_index_latest_parent_or_prior_content_must_fail(self):
        for key, value in (('index', 2), ('is_latest', False), ('is_latest', 1)):
            actual = deepcopy(self.expected); actual['versions'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ServerManagedMismatch): self.check(actual)
        self.actual['parent']['id'] = '78'
        with self.assertRaises(ServerManagedMismatch): self.check()
        prior = deepcopy(self.expected); prior['versions']['is_latest'] = False; prior['metadata']['title'] = 'changed'
        with self.assertRaises(ServerManagedMismatch): validate_prior_version(prior, self.expected,
            host='zenodo.org', record_id='1001', chain_parent_id='77')

    def test_row6_changed_own_record_urls_and_counters_pass(self):
        self.actual['links']['preview'] = 'https://zenodo.org/records/1001?preview=1'
        self.actual['links']['doi'] = 'https://doi.org/10.5281/zenodo.1001'
        self.actual['links']['iiif'] = 'https://zenodo.org/api/iiif/record:1001:figure.svg/full/max/0/default.png'
        self.actual['stats'] = {'views': 1, 'all_versions': {'downloads': 2, 'data_volume': 42.0}}
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row6_wrong_record_urls_noncounters_or_removed_fields_must_fail(self):
        for group, key, value in (('links', 'preview', 'https://zenodo.org/records/11001'),
                                  ('links', 'preview', 'https://evil.org/records/1001'),
                                  ('links', 'doi', 'https://doi.org/10.5281/zenodo.1002'),
                                  ('links', 'thumbnails', {'small': 'https://zenodo.org/api/iiif/record:11001:file/full/max/0/default.png'}),
                                  ('stats', 'views', -1), ('stats', 'views', '1'), ('stats', 'views', True),
                                  ('stats', 'views', 1.5)):
            actual = deepcopy(self.expected); actual[group][key] = value
            with self.subTest(group=group, value=value), self.assertRaises(ServerManagedMismatch): self.check(actual)
        del self.actual['links']['self']
        with self.assertRaises(ServerManagedMismatch): self.check()

    def test_row7_six_files_full_entry_reorder_and_duplicate_ordered_pass(self):
        self.actual['files'].reverse()
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')
        expected = deepcopy(self.expected); expected['files'].append(deepcopy(expected['files'][0]))
        self.assertEqual(self.check(deepcopy(expected), expected)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_row7_checksum_unknown_field_or_duplicate_reorder_must_fail(self):
        for change in ('checksum', 'unknown'):
            actual = deepcopy(self.expected)
            actual['files'][0][change] = 'changed'
            with self.subTest(change=change), self.assertRaises(ServerManagedMismatch): self.check(actual)
        expected = deepcopy(self.expected); expected['files'].append(dict(expected['files'][0], id='distinct'))
        actual = deepcopy(expected); actual['files'].reverse()
        with self.assertRaises(ServerManagedMismatch): self.check(actual, expected)

    def test_native_file_order_only_permutation_complete_entries_exact(self):
        expected = deepcopy(self.expected)
        expected['files'] = {'enabled': True, 'order': [entry['key'] for entry in expected['files']],
            'entries': {entry['key']: entry for entry in expected['files']}, 'unknown': 'exact'}
        actual = deepcopy(expected); actual['files']['order'].reverse()
        self.assertEqual(self.check(actual, expected)['checks']['file_entry_order']['detail']['mode'],
                         'FILENAME_KEYED_NATIVE_ORDER')
        for field in ('checksum', 'unknown'):
            changed = deepcopy(actual); changed['files']['entries']['file-0.txt'][field] = 'changed'
            with self.subTest(field=field), self.assertRaises(ServerManagedMismatch): self.check(changed, expected)
        changed = deepcopy(actual); changed['files']['unknown'] = 'changed'
        with self.assertRaises(ServerManagedMismatch): self.check(changed, expected)
        changed = deepcopy(actual); changed['files']['order'][0] = 'unknown.txt'
        with self.assertRaises(ServerManagedMismatch): self.check(changed, expected)
        expected['files']['order'].append(expected['files']['order'][0])
        actual = deepcopy(expected); actual['files']['order'].reverse()
        with self.assertRaises(ServerManagedMismatch): self.check(actual, expected)

    def test_unlisted_fields_and_unpredicted_publication_flags_never_ignored(self):
        for group in ('top', 'parent', 'versions', 'custom_fields', 'access'):
            actual = deepcopy(self.expected)
            if group == 'top': actual['unlisted'] = 'new'
            else: actual[group]['unlisted'] = 'new'
            with self.subTest(group=group), self.assertRaises(ServerManagedMismatch): self.check(actual)
        actual = deepcopy(self.expected); actual['is_draft'] = True
        with self.assertRaises(ServerManagedMismatch): self.check(actual)

    def test_exact_json_types_presence_and_required_inputs_never_collapse(self):
        for group in ('metadata', 'custom_fields'):
            expected = deepcopy(self.expected); expected[group]['protected'] = True
            actual = deepcopy(expected); actual[group]['protected'] = 1
            with self.subTest(group=group), self.assertRaises(ServerManagedMismatch):
                self.check(actual, expected)
        actual = deepcopy(self.expected); actual['metadata']['unlisted'] = None
        with self.assertRaises(ServerManagedMismatch): self.check(actual)
        actual = deepcopy(self.expected); del actual['custom_fields']
        with self.assertRaises(ServerManagedMismatch): self.check(actual)
        for value in (None, 'missing'):
            actual = deepcopy(self.expected)
            if value == 'missing': del actual['files']
            else: actual['files'] = value
            with self.subTest(files=value), self.assertRaises(ServerManagedMismatch): self.check(actual)
        with self.assertRaisesRegex(ServerManagedMismatch, 'ACTUAL_BEFORE_PUBLISH_TEMPORAL_BASELINE_REQUIRED'):
            self.check(temporal_baseline=None)

    def test_malformed_object_keys_and_nonfinite_values_fail_closed(self):
        for value in ({1: 'invalid-json-key'}, {'counter': float('nan')}):
            actual = deepcopy(self.expected); actual['unlisted'] = value
            with self.subTest(value=value), self.assertRaises(TransportHold): self.check(actual)

    def test_amendment_identifiers_and_content_remain_exact(self):
        self.actual.update(updated='2026-10-04T02:00:00Z')
        self.assertEqual(validate_amendment(self.actual, self.expected, host='zenodo.org', record_id='1001')['status'],
            'SERVER_MANAGED_READBACK_PASS')
        self.actual['pids']['doi']['provider'] = 'external'
        with self.assertRaises(ServerManagedMismatch): validate_amendment(self.actual, self.expected,
            host='zenodo.org', record_id='1001')

    def test_sandbox_legacy_envelope_omission_get_r0_and_expiry_absence_pass(self):
        actual = deepcopy(self.expected); expected = deepcopy(self.expected)
        actual['pids']['oai'] = {'identifier': 'oai:zenodo.org:1001', 'provider': 'oai'}
        baseline = deepcopy(self.context['temporal_baseline']); actual['revision_id'] = 3
        actual.pop('expires_at')
        receipt = deepcopy(self.context['own_publish_response'])
        receipt['url'] = 'https://sandbox.zenodo.org/api/deposit/depositions/1001/actions/publish'
        receipt['environment'] = 'sandbox.zenodo.org'
        evidence = self.evidence(receipt, host='sandbox.zenodo.org')
        report = audit_readback(actual, expected, operation='NEW_VERSION',
            **(self.context | {'host': 'sandbox.zenodo.org', 'temporal_baseline': baseline,
                              'own_publish_response': receipt, 'revision_evidence': evidence}))
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertEqual(report['checks']['pids.oai']['status'], 'PASS')
        self.assertEqual(report['checks']['revision_id']['status'], 'PASS')
        self.assertEqual(report['checks']['expires_at']['status'], 'PASS')
        self.assertEqual(report['checks']['content_metadata']['status'], 'PASS')
        self.assertEqual(report['checks']['file_entry_order']['status'], 'PASS')

    def test_amended_oai_literal_namespace_both_hosts_and_negative_cases(self):
        self.actual['pids']['oai'] = {'identifier': 'oai:zenodo.org:1001', 'provider': 'oai'}
        for host in ('zenodo.org', 'sandbox.zenodo.org'):
            receipt = deepcopy(self.context['own_publish_response'])
            receipt['url'] = 'https://' + host + '/api/records/1001/draft/actions/publish'
            receipt['environment'] = host
            with self.subTest(host=host): self.assertEqual(self.check(host=host, own_publish_response=receipt)['status'], 'SERVER_MANAGED_READBACK_PASS')
            for value in ({'identifier': 'oai:sandbox.zenodo.org:1001', 'provider': 'oai'},
                          {'identifier': 'oai:zenodo.org:1002', 'provider': 'oai'},
                          {'identifier': 'oai:zenodo.org:1001', 'provider': 'other'}):
                actual = deepcopy(self.actual); actual['pids']['oai'] = value
                with self.subTest(host=host, oai=value), self.assertRaises(ServerManagedMismatch):
                    self.check(actual, host=host, own_publish_response=receipt)

    def test_amended_revision_draft_monotonic_and_own_publish_reset_pass(self):
        baseline = deepcopy(self.context['temporal_baseline'])
        actual = deepcopy(baseline); actual['revision_id'] = 32
        result = require_revision(actual, baseline, phase='DRAFT', operation='NEW_VERSION', host='zenodo.org', record_id='1001')
        self.assertEqual(result['revision'], 32)
        self.assertEqual(self.check()['checks']['revision_id']['detail']['first_authenticated_native_r0'], 1)
        previous_public = deepcopy(self.expected); previous_public['revision_id'] = 2
        self.actual['revision_id'] = 3
        self.assertEqual(self.check(previous_public_readback=previous_public)['status'], 'SERVER_MANAGED_READBACK_PASS')
        receipt = deepcopy(self.context['own_publish_response']); receipt['response'] = {'id': '1001', 'revision': 0}
        # Legacy response revision fields never substitute for the authenticated GET.
        self.assertEqual(self.check(own_publish_response=receipt)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_draft_zero_nondecreasing_pass_negative_or_bool_fail(self):
        baseline = deepcopy(self.expected); baseline['revision_id'] = 0
        for value in (0, 1):
            actual = deepcopy(baseline); actual['revision_id'] = value
            self.assertEqual(require_revision(actual, baseline, phase='DRAFT', operation='NEW_VERSION',
                host='zenodo.org', record_id='1001')['revision'], value)
        for value in (-1, True, False):
            actual = deepcopy(baseline); actual['revision_id'] = value
            with self.subTest(value=value), self.assertRaises(TransportHold):
                require_revision(actual, baseline, phase='DRAFT', operation='NEW_VERSION', host='zenodo.org', record_id='1001')

    def test_amended_revision_every_listed_negative_and_get_not_publish(self):
        draft = deepcopy(self.context['temporal_baseline']); draft['revision_id'] = 30
        with self.assertRaisesRegex(TransportHold, 'DRAFT_REVISION_DECREASE'):
            require_revision(draft, self.context['temporal_baseline'], phase='DRAFT', operation='NEW_VERSION', host='zenodo.org', record_id='1001')
        for r0 in (None, 0, -1, True, '3'):
            native = deepcopy(self.expected)
            if r0 is None: native.pop('revision_id')
            else: native['revision_id'] = r0
            evidence = self.evidence(native=native)
            with self.subTest(r0=r0), self.assertRaisesRegex(ServerManagedMismatch, 'FIRST_NATIVE_GET_R0_POSITIVE_INTEGER_REQUIRED'):
                self.check(revision_evidence=evidence)
        receipt = deepcopy(self.context['own_publish_response']); receipt['method'] = 'GET'
        with self.assertRaisesRegex(ServerManagedMismatch, 'OWN_PUBLISH_POST_RECEIPT_REQUIRED'): self.check(own_publish_response=receipt)
        previous_public = deepcopy(self.expected); previous_public['revision_id'] = 2
        with self.assertRaisesRegex(ServerManagedMismatch, 'PUBLIC_REVISION_DECREASE'): self.check(previous_public_readback=previous_public)
        with self.assertRaisesRegex(ServerManagedMismatch, 'PUBLISH_RESERVATION_ID_MISMATCH'):
            self.check(same_operation_reservation_id='1002')

    def test_amended_prior_revision_flip_exact_content_pass(self):
        prior = deepcopy(self.expected); prior['versions']['is_latest'] = False; prior['revision_id'] = 2
        self.assertEqual(self.receipt_backed_prior_pass(prior, self.expected)['status'], 'SERVER_MANAGED_READBACK_PASS')
        prior['files'].reverse()
        self.assertEqual(self.receipt_backed_prior_pass(prior, self.expected)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_amended_prior_revision_without_flip_or_with_any_content_change_fails(self):
        expected = deepcopy(self.expected); expected['versions']['is_latest'] = False
        actual = deepcopy(expected); actual['revision_id'] = 2
        with self.assertRaisesRegex(ServerManagedMismatch, 'PRIOR_REVISION_CHANGE_WITHOUT_LATEST_FLIP'):
            validate_prior_version(actual, expected, host='zenodo.org', record_id='1001', chain_parent_id='77')
        for field in ('metadata', 'files', 'custom_fields'):
            actual = deepcopy(self.expected); actual['versions']['is_latest'] = False; actual['revision_id'] = 2
            if field == 'metadata': actual[field]['description'] = '<p>Exact  claim</p>'
            elif field == 'files': actual[field][0]['checksum'] = 'changed'
            else: actual[field]['unlisted'] = 'changed'
            with self.subTest(field=field), self.assertRaises(ServerManagedMismatch):
                validate_prior_version(actual, self.expected, host='zenodo.org', record_id='1001', chain_parent_id='77')
        actual = deepcopy(self.expected); actual['versions']['is_latest'] = False
        actual['metadata']['description'] = '<p>Exact  claim</p>'
        with self.assertRaisesRegex(ServerManagedMismatch, 'PRIOR_REVISION_CHANGED_WITH_CONTENT'):
            validate_prior_version(actual, self.expected, host='zenodo.org', record_id='1001', chain_parent_id='77')
        # The globally approved ordering rule still applies when revision is exact.
        actual = deepcopy(self.expected); actual['versions']['is_latest'] = False; actual['files'].reverse()
        self.assertEqual(self.receipt_backed_prior_pass(actual, self.expected)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_amended_deletion_status_own_exact_p_pass(self):
        self.assertEqual(self.check()['checks']['deletion_status']['status'], 'PASS')

    def test_amended_deletion_status_deleted_wrong_status_preexisting_change_fail(self):
        for value in ({'is_deleted': True, 'status': 'P'}, {'is_deleted': False, 'status': 'D'}, {'is_deleted': False, 'status': 'P', 'other': True}):
            actual = deepcopy(self.expected); actual['deletion_status'] = value
            with self.subTest(value=value), self.assertRaises(ServerManagedMismatch): self.check(actual)
        expected = deepcopy(self.expected); expected.pop('deletion_status')
        with self.assertRaises(ServerManagedMismatch):
            validate_amendment(self.actual, expected, host='zenodo.org', record_id='1001')

    def test_amended_expires_nonnull_draft_present_null_public_pass(self):
        self.assertEqual(self.check()['checks']['expires_at']['status'], 'PASS')

    def test_amended_expires_nonnull_gain_preexisting_change_fail(self):
        actual = deepcopy(self.expected); actual['expires_at'] = '2026-10-06T01:00:00Z'
        with self.assertRaisesRegex(ServerManagedMismatch, 'OWN_PUBLISHED_EXPIRES_AT_ABSENT_OR_NULL_REQUIRED'):
            self.check(actual)
        actual = deepcopy(self.expected); actual['expires_at'] = '2026-10-06T01:00:00Z'
        with self.assertRaises(ServerManagedMismatch): validate_amendment(actual, self.expected, host='zenodo.org', record_id='1001')
        expected = deepcopy(self.expected); expected['expires_at'] = '2026-10-06T01:00:00Z'
        with self.assertRaises(ServerManagedMismatch): validate_amendment(self.actual, expected, host='zenodo.org', record_id='1001')

    def test_amended_swh_initial_empty_later_nonempty_logged_pass(self):
        self.assertEqual(self.check()['checks']['swh']['status'], 'PASS')
        self.actual['swh'] = {'swhid': 'swh:1:rev:example'}
        result = self.check(previous_public_readback=self.expected)
        self.assertEqual(result['checks']['swh']['detail'], {'ignored_for_content_comparison': True, 'logged_value': self.actual['swh']})

    def test_amended_swh_preexisting_appearance_change_and_initial_nonempty_fail(self):
        for expected_swh in ('ABSENT', {}):
            expected = deepcopy(self.expected)
            if expected_swh == 'ABSENT': expected.pop('swh')
            actual = deepcopy(expected); actual['swh'] = {'swhid': 'changed'}
            with self.subTest(expected_swh=expected_swh), self.assertRaises(ServerManagedMismatch):
                validate_amendment(actual, expected, host='zenodo.org', record_id='1001')
        self.actual['swh'] = {'swhid': 'initial-nonempty'}
        with self.assertRaises(ServerManagedMismatch): self.check()

    def test_amended_ui_draft_true_public_false_pass(self):
        self.assertEqual(self.check()['checks']['ui.is_draft']['status'], 'PASS')

    def test_amended_ui_true_after_publish_or_false_to_true_anywhere_fail(self):
        self.actual['ui']['is_draft'] = True
        with self.assertRaises(ServerManagedMismatch): self.check()
        for operation in ('AMENDMENT', 'PRIOR_VERSION'):
            kwargs = {'operation': operation, 'host': 'zenodo.org', 'record_id': '1001', 'chain_parent_id': '77'}
            actual = deepcopy(self.expected); actual['ui']['is_draft'] = True
            if operation == 'PRIOR_VERSION': actual['versions']['is_latest'] = False
            self.assertEqual(audit_readback(actual, self.expected, **kwargs)['checks']['ui.is_draft']['status'], 'HOLD')

    def test_amended_all_rows_missing_or_wrong_own_publish_scope_fail_closed(self):
        for edit in ('absent', 'id', 'endpoint', 'status', 'reservation'):
            context = deepcopy(self.context)
            if edit == 'absent': context['own_publish_response'] = None
            elif edit == 'id': context['own_publish_response']['response']['id'] = '1002'
            elif edit == 'endpoint': context['own_publish_response']['url'] = 'https://zenodo.org/api/records/77/draft/actions/publish'
            elif edit == 'status': context['own_publish_response']['http_status'] = 500
            else: context['same_operation_reservation_id'] = '1002'
            actual = deepcopy(self.expected); actual['pids']['oai'] = {'identifier': 'oai:zenodo.org:1001', 'provider': 'oai'}
            report = audit_readback(actual, self.expected, operation='NEW_VERSION', **context)
            with self.subTest(edit=edit):
                self.assertEqual(report['status'], 'HOLD')
                for row in ('own_publish_scope', 'pids.oai', 'revision_id', 'deletion_status', 'expires_at', 'swh', 'ui.is_draft'):
                    self.assertEqual(report['checks'][row]['status'], 'HOLD')

    def test_revision_evidence_saved_first_native_get_has_logged_hashes(self):
        result = self.check()['checks']['revision_id']['detail']
        self.assertEqual(result['first_authenticated_native_r0'], 1)
        evidence = result['evidence']
        self.assertEqual((evidence['publish_sequence'], evidence['native_get_sequence']), (1, 2))
        for key in ('publish_receipt_file_sha256', 'native_get_receipt_file_sha256',
                    'publish_raw_response_sha256', 'native_get_raw_response_sha256'):
            self.assertRegex(evidence[key], r'^[0-9a-f]{64}$')
        self.assertIn('no independent auth marker', evidence['authentication_evidence'])

    def test_revision_evidence_no_saved_post_non2xx_or_record_id_mismatch_fail(self):
        with self.assertRaises(ServerManagedMismatch): self.check(revision_evidence=None)
        evidence = self.evidence()
        Path(evidence['receipt_directory'], '001_POST.json').unlink()
        with self.assertRaises(ServerManagedMismatch): self.check(revision_evidence=evidence)
        for edit in ('http', 'post-id', 'get-id'):
            receipt = deepcopy(self.context['own_publish_response'])
            native = deepcopy(self.expected)
            if edit == 'http': receipt['http_status'] = 500
            elif edit == 'post-id': receipt['response']['id'] = '1002'
            else: native['id'] = '1002'
            evidence = self.evidence(receipt, native)
            with self.subTest(edit=edit), self.assertRaises(ServerManagedMismatch):
                self.check(own_publish_response=receipt, revision_evidence=evidence)

    def test_revision_evidence_get_preceding_post_or_not_first_native_fails(self):
        evidence = self.evidence()
        directory = Path(evidence['receipt_directory'])
        post = (directory / '001_POST.json').read_bytes(); get = (directory / '002_GET.json').read_bytes()
        (directory / '001_POST.json').unlink(); (directory / '002_GET.json').unlink()
        (directory / '001_GET.json').write_bytes(get); (directory / '002_POST.json').write_bytes(post)
        evidence.update(publish_receipt_name='002_POST.json', first_native_get_receipt_name='001_GET.json')
        with self.assertRaisesRegex(ServerManagedMismatch, 'R0_GET_PRECEDES_OWN_PUBLISH'): self.check(revision_evidence=evidence)
        evidence = self.evidence()
        directory = Path(evidence['receipt_directory'])
        (directory / '003_GET.json').write_bytes((directory / '002_GET.json').read_bytes())
        evidence['first_native_get_receipt_name'] = '003_GET.json'
        with self.assertRaisesRegex(ServerManagedMismatch, 'R0_NOT_FIRST_NATIVE_GET_AFTER_OWN_PUBLISH'):
            self.check(revision_evidence=evidence)

    def test_revision_evidence_missing_raw_hash_contract_or_native_accept_fails(self):
        for edit in ('publish-hash', 'native-hash', 'contract', 'accept', 'environment', 'status', 'changed-saved-post'):
            receipt = deepcopy(self.context['own_publish_response'])
            if edit == 'publish-hash': receipt.pop('response_sha256')
            evidence = self.evidence(receipt)
            if edit == 'native-hash': self.change_receipt(evidence, '002_GET.json', lambda j: j.pop('response_sha256'))
            elif edit == 'contract': evidence['transport_contract_sha256'] = '0' * 64
            elif edit == 'accept': self.change_receipt(evidence, '002_GET.json', lambda j: j.update(accept='application/json'))
            elif edit == 'environment': self.change_receipt(evidence, '002_GET.json', lambda j: j.update(environment='sandbox.zenodo.org'))
            elif edit == 'status': self.change_receipt(evidence, '002_GET.json', lambda j: j.update(http_status=500))
            elif edit == 'changed-saved-post': self.change_receipt(evidence, '001_POST.json', lambda j: j.update(response={'id': '1002'}))
            with self.subTest(edit=edit), self.assertRaises(ServerManagedMismatch):
                self.check(own_publish_response=receipt, revision_evidence=evidence)

    def test_revision_evidence_later_readback_below_r0_fails(self):
        native = deepcopy(self.expected); native['revision_id'] = 3
        evidence = self.evidence(native=native)
        actual = deepcopy(self.expected); actual['revision_id'] = 2
        with self.assertRaisesRegex(ServerManagedMismatch, 'PUBLIC_REVISION_BELOW_OWN_PUBLISH_R0'):
            self.check(actual, revision_evidence=evidence)

    def test_expiry_absent_or_null_own_publish_pass_draft_missing_or_null_fail(self):
        actual = deepcopy(self.expected); actual.pop('expires_at')
        self.assertEqual(self.check(actual)['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertEqual(self.check()['status'], 'SERVER_MANAGED_READBACK_PASS')
        for value in ('ABSENT', None):
            baseline = deepcopy(self.context['temporal_baseline'])
            if value == 'ABSENT': baseline.pop('expires_at')
            else: baseline['expires_at'] = None
            with self.subTest(value=value), self.assertRaisesRegex(ServerManagedMismatch, 'OWN_DRAFT_EXPIRES_AT_PRESENT_NONNULL_REQUIRED'):
                self.check(temporal_baseline=baseline)

    def test_expiry_presence_change_on_preexisting_record_both_directions_fails(self):
        expected = deepcopy(self.expected); actual = deepcopy(expected); actual.pop('expires_at')
        for left, right in ((actual, expected), (expected, actual)):
            with self.assertRaises(ServerManagedMismatch):
                validate_amendment(left, right, host='zenodo.org', record_id='1001')

    def test_own_allowed_nullable_link_stat_leaves_only_pass(self):
        actual = deepcopy(self.expected)
        actual['links']['optional'] = None; actual['stats']['asynchronous'] = None
        result = self.check(actual)
        self.assertEqual(result['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertEqual(result['representation_normalizations'], ['links.optional', 'stats.asynchronous'])
        expected = deepcopy(self.expected); expected['links']['optional'] = None
        self.assertEqual(self.check(expected=expected)['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_nullable_representation_never_content_certificate_unlisted_or_preexisting(self):
        for field in ('metadata', 'custom_fields', 'files', 'certificate', 'unlisted'):
            actual = deepcopy(self.expected)
            if field in ('metadata', 'custom_fields'): actual[field]['unlisted'] = None
            elif field == 'files': actual[field][0]['unlisted'] = None
            else: actual[field] = None
            with self.subTest(field=field), self.assertRaises(ServerManagedMismatch): self.check(actual)
        actual = deepcopy(self.expected); actual['links']['optional'] = None
        with self.assertRaises(ServerManagedMismatch): validate_amendment(actual, self.expected,
            host='zenodo.org', record_id='1001')
        actual = deepcopy(self.expected); actual['stats']['views'] = None
        with self.assertRaises(ServerManagedMismatch): self.check(actual)

    def test_original_amendment_monotonic_revision_increase_pass_decrease_fail(self):
        actual = deepcopy(self.expected); actual['revision_id'] = 2
        self.assertEqual(validate_amendment(actual, self.expected, host='zenodo.org', record_id='1001')['status'],
                         'SERVER_MANAGED_READBACK_PASS')
        actual['revision_id'] = 0
        with self.assertRaisesRegex(ServerManagedMismatch, 'PREEXISTING_REVISION_DECREASE'):
            validate_amendment(actual, self.expected, host='zenodo.org', record_id='1001')
        actual['revision_id'] = 2; actual['metadata']['title'] = 'changed'
        with self.assertRaises(ServerManagedMismatch): validate_amendment(actual, self.expected,
            host='zenodo.org', record_id='1001')

    def test_draft_full_closed_readback_pre_reservation_pass_and_index_parent_flag_fail(self):
        expected = deepcopy(self.context['temporal_baseline'])
        expected['pids'] = {}; expected['versions'].update(index=0, is_latest=False)
        expected.update(is_draft=True, is_published=False)
        context = {'host': 'zenodo.org', 'record_id': '1001', 'operation': 'NEW_VERSION', 'phase': 'DRAFT'}
        actual = deepcopy(expected); actual['revision_id'] += 1
        report = audit_readback(actual, expected, **context)
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertFalse(report['acceptance_authority'])
        for edit in ('index', 'parent', 'flag', 'nullable', 'expiry'):
            actual = deepcopy(expected)
            if edit == 'index': actual['versions']['index'] = 1
            elif edit == 'parent': actual['parent']['id'] = '78'
            elif edit == 'flag': actual['ui']['is_draft'] = False
            elif edit == 'nullable': actual['links']['optional'] = None
            else: actual.pop('expires_at')
            with self.subTest(edit=edit): self.assertEqual(audit_readback(actual, expected, **context)['status'], 'HOLD')

    def test_night_own_amendment_updated_created_publication_dates_pass(self):
        expected = deepcopy(self.expected)
        expected['metadata']['publication_date'] = '2026-10-04'
        actual = deepcopy(expected)
        actual['updated'] = '2026-10-05T01:00:00Z'
        actual['ui'].update(updated_date_l10n_long='October 5, 2026',
            created_date_l10n_long='October 4, 2026',
            publication_date_l10n_medium='Oct 4, 2026', publication_date_l10n_long='2026-10-04')
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', own_operation_record_id='1001')
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        dates = report['checks']['ui_display_fields']['detail']['date_checks']
        self.assertEqual({d['source_path'] for d in dates}, {'updated', 'created', 'metadata.publication_date'})
        self.assertEqual(len(report['ui_diff_appendix']), 4)

    def test_night_dates_utc_conversion_and_both_locale_day_offsets_pass(self):
        expected = deepcopy(self.expected); expected['metadata']['publication_date'] = '2026-10-04'
        for offset, updated, other in ((-1, 'October 4, 2026', 'Oct 3, 2026'),
                                      (0, '2026-10-05', '2026-10-04'),
                                      (1, 'October 6, 2026', 'Oct 5, 2026')):
            actual = deepcopy(expected); actual['updated'] = '2026-10-04T23:30:00-02:00'
            actual['ui'].update(updated_date_l10n_long=updated,
                created_date_l10n_long=other, publication_date_l10n_medium=other)
            report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', own_operation_record_id='1001')
            with self.subTest(offset=offset):
                self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
                for item in report['checks']['ui_display_fields']['detail']['date_checks']:
                    self.assertEqual(item['display_day_offset'], offset)

    def test_night_wrong_date_and_date_matching_another_source_fail(self):
        expected = deepcopy(self.expected); expected['metadata']['publication_date'] = '2026-10-04'
        for field, value in (('updated_date_l10n_long', 'October 4, 2026'),
                             ('created_date_l10n_long', 'October 20, 2026'),
                             ('publication_date_l10n_medium', 'Oct 20, 2026')):
            actual = deepcopy(expected); actual['updated'] = '2026-10-20T01:00:00Z'
            actual['ui'][field] = value
            report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', own_operation_record_id='1001')
            with self.subTest(field=field):
                self.assertEqual(report['status'], 'HOLD')
                self.assertIn('UI_RULE_HOLD:DATE_DOES_NOT_MATCH_SOURCE',
                    report['checks']['ui_display_fields']['reason'])
                self.assertTrue(report['ui_diff_appendix'])

    def test_night_malformed_unmappable_missing_source_dates_fail_closed(self):
        cases = [('updated_date_l10n_long', value) for value in
                 ('October 4', '10/04/2026', 'February 30, 2026', None, True, 123,
                  'Unknown 4, 2026')]
        cases.extend((('unknown_date_l10n_long', 'October 4, 2026'),
                      ('publication_date_l10n_long', 'October 4, 2026')))
        for field, value in cases:
            actual = deepcopy(self.expected); actual['ui'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(TransportHold):
                require_ui_display(actual, self.expected, record_id='1001', operation='AMENDMENT',
                    own_operation_record_id='1001')
        actual = deepcopy(self.expected); actual['ui']['created_date_l10n_long'] = 'October 4, 2026'
        for source in (None, '2026-10-04T01:00:00'):
            actual['created'] = source
            with self.subTest(source=source), self.assertRaises(TransportHold):
                require_ui_display(actual, self.expected, record_id='1001', operation='AMENDMENT',
                    own_operation_record_id='1001')

    def test_night_untouched_prior_and_unrelated_ui_remain_exact(self):
        for key, value in (('updated_date_l10n_long', 'October 4, 2026'),
                           ('other', 'changed'), ('is_draft', True)):
            actual = deepcopy(self.expected); actual['ui'][key] = value
            with self.subTest(key=key), self.assertRaises(ServerManagedMismatch):
                validate_amendment(actual, self.expected, host='zenodo.org', record_id='1001')
            actual['versions']['is_latest'] = False
            with self.subTest(prior=key), self.assertRaises(ServerManagedMismatch):
                validate_prior_version(actual, self.expected, host='zenodo.org', record_id='1001',
                    chain_parent_id='77', own_operation_record_id='1001')

    def test_night_own_record_scope_requires_all_ids_identical(self):
        actual = deepcopy(self.expected); actual['ui']['other'] = 'changed'
        for own_id in ('1002', None, True, '01001'):
            report = audit_readback(actual, self.expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', own_operation_record_id=own_id)
            with self.subTest(own_id=own_id): self.assertEqual(report['status'], 'HOLD')
        actual['id'] = '1002'
        with self.assertRaisesRegex(TransportHold, 'UI_OWN_OPERATION_RECORD_ID_MISMATCH'):
            require_ui_display(actual, self.expected, record_id='1001', operation='AMENDMENT',
                own_operation_record_id='1001')

    def test_night_other_own_ui_changes_excluded_and_full_values_logged(self):
        actual = deepcopy(self.expected); del actual['ui']['other']
        actual['ui']['future_rendering'] = {'title': 'presentation', 'nested': [True, {'complete': 'value'}]}
        report = audit_readback(actual, self.expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', own_operation_record_id='1001')
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        diffs = {item['path']: item for item in report['ui_diff_appendix']}
        self.assertEqual(diffs['ui.future_rendering']['after'], actual['ui']['future_rendering'])
        self.assertFalse(diffs['ui.future_rendering']['before_present'])
        self.assertEqual(diffs['ui.other']['before'], 'exact')
        self.assertFalse(diffs['ui.other']['after_present'])
        self.assertEqual(report['checks']['ui_display_fields']['detail']['diff_appendix'], report['ui_diff_appendix'])

    def test_night_ui_exclusion_never_masks_source_content_custom_file_or_pid_change(self):
        for field in ('title', 'description', 'publication_date', 'related_identifiers', 'custom', 'files', 'pids'):
            actual = deepcopy(self.expected)
            if field == 'custom': actual['custom_fields']['hidden'] = 'changed'
            elif field == 'files': actual['files'][0]['checksum'] = 'changed'
            elif field == 'pids': actual['pids']['doi']['identifier'] = '10.5281/zenodo.1002'
            elif field == 'publication_date': actual['metadata'][field] = '2026-10-04'
            elif field == 'related_identifiers': actual['metadata'][field] = [{'identifier': 'changed'}]
            else: actual['metadata'][field] = 'Changed scientific claim'
            actual['ui']['other'] = {'copied_changed_source': field}
            report = audit_readback(actual, self.expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', own_operation_record_id='1001')
            with self.subTest(field=field):
                self.assertEqual(report['checks']['ui_display_fields']['status'], 'PASS')
                self.assertEqual(report['status'], 'HOLD')

    def test_night_changed_publication_source_with_corresponding_ui_date_still_fails(self):
        expected = deepcopy(self.expected); expected['metadata']['publication_date'] = '2026-10-04'
        actual = deepcopy(expected); actual['metadata']['publication_date'] = '2026-10-20'
        actual['ui']['publication_date_l10n_medium'] = 'Oct 20, 2026'
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', own_operation_record_id='1001')
        self.assertEqual(report['checks']['ui_display_fields']['status'], 'PASS')
        self.assertEqual(report['checks']['content_metadata']['status'], 'HOLD')
        self.assertEqual(report['status'], 'HOLD')

    def test_night_own_private_draft_true_and_own_published_false_pass(self):
        expected = deepcopy(self.expected); expected['is_draft'] = True
        actual = deepcopy(expected); actual['ui']['is_draft'] = True
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', phase='DRAFT', own_operation_record_id='1001')
        # Night table supersedes the old false-public -> true-private UI rejection.
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertEqual(report['checks']['ui.is_draft']['status'], 'PASS')
        expected = deepcopy(self.expected); expected['ui']['is_draft'] = True
        actual = deepcopy(expected); actual['ui']['is_draft'] = False
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', own_operation_record_id='1001')
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')

    def test_night_own_wrong_phase_missing_or_nonboolean_ui_flags_fail(self):
        for phase, value in (('DRAFT', False), ('PUBLISHED', True), ('DRAFT', 1), ('PUBLISHED', 0), ('DRAFT', None)):
            actual = deepcopy(self.expected); actual['ui']['is_draft'] = value
            report = audit_readback(actual, self.expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', phase=phase, own_operation_record_id='1001')
            with self.subTest(phase=phase, value=value): self.assertEqual(report['status'], 'HOLD')
        actual = deepcopy(self.expected); actual['ui'].pop('is_draft')
        with self.assertRaises(TransportHold): require_ui_display(actual, self.expected,
            record_id='1001', operation='AMENDMENT', own_operation_record_id='1001')

    def test_night_new_version_publish_scope_still_mandatory(self):
        actual = deepcopy(self.expected); actual['ui']['other'] = 'rendered'
        self.assertEqual(self.check(actual)['status'], 'SERVER_MANAGED_READBACK_PASS')
        with self.assertRaises(ServerManagedMismatch): self.check(actual,
            own_operation_record_id='1001', own_publish_response=None)

    def test_night_unknown_non_ui_field_and_actual_status_flag_never_excluded(self):
        for field, value in (('unexpected', 'changed'), ('is_draft', True), ('is_published', False)):
            actual = deepcopy(self.expected); actual[field] = value; actual['ui']['other'] = 'rendered'
            report = audit_readback(actual, self.expected, host='zenodo.org', record_id='1001',
                operation='AMENDMENT', own_operation_record_id='1001')
            with self.subTest(field=field): self.assertEqual(report['status'], 'HOLD')

    def test_night_exact_existing_null_date_is_not_an_asserted_calendar_date(self):
        expected = deepcopy(self.expected)
        expected['ui']['access_status'] = {'embargo_date_l10n': None, 'status': 'open'}
        expected['access'] = {'embargo': {'active': False, 'reason': None},
            'files': 'public', 'record': 'public', 'status': 'open'}
        actual = deepcopy(expected); actual['ui']['other'] = 'new rendering'
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', own_operation_record_id='1001')
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS')
        self.assertIn({'path': 'ui.access_status.embargo_date_l10n',
            'unchanged_null_no_calendar_date': True},
            report['checks']['ui_display_fields']['detail']['date_checks'])
        for edit in ('non-null', 'remove', 'appears'):
            left, right = deepcopy(expected), deepcopy(expected)
            if edit == 'non-null': left['ui']['access_status']['embargo_date_l10n'] = 'October 4, 2026'
            elif edit == 'remove': left['ui']['access_status'].pop('embargo_date_l10n')
            else: right['ui']['access_status'].pop('embargo_date_l10n')
            with self.subTest(edit=edit), self.assertRaises(TransportHold):
                require_ui_display(left, right, record_id='1001', operation='AMENDMENT',
                    own_operation_record_id='1001')

    def test_night_removing_an_existing_real_date_fails(self):
        expected = deepcopy(self.expected); expected['ui']['updated_date_l10n_long'] = 'October 4, 2026'
        actual = deepcopy(expected); actual['ui'].pop('updated_date_l10n_long')
        with self.assertRaisesRegex(TransportHold, 'UI_RULE_HOLD:DATE_FIELD_REMOVED'):
            require_ui_display(actual, expected, record_id='1001', operation='AMENDMENT',
                own_operation_record_id='1001')


    def test_chain_create_saved_receipt_pair_and_draft_readback_pass(self):
        ctx = self.chain_fixture()
        report = self.assert_chain_pass(ctx)
        self.assertEqual(report['checks']['version_chain_state']['detail']['boundary'], 'CREATE')
        for operation, record, expected in (
                ('PRIOR_VERSION', ctx['prior_actual'], ctx['prior_before_create']),
                ('NEW_VERSION', ctx['successor_actual'], ctx['successor_expected'])):
            result = audit_readback(record, expected, host='zenodo.org', record_id=record['id'],
                operation=operation, phase='DRAFT' if operation == 'NEW_VERSION' else 'PUBLISHED',
                chain_parent_id='77', own_operation_record_id='1002' if operation == 'NEW_VERSION' else None,
                version_chain_context=ctx)
            self.assertEqual(result['status'], 'SERVER_MANAGED_READBACK_PASS', result)

    def test_chain_create_draft_index_absent_or_null_pass_logged(self):
        for mode in ('absent', 'null'):
            ctx = self.chain_fixture()
            if mode == 'absent': ctx['successor_actual']['versions'].pop('index')
            else: ctx['successor_actual']['versions']['index'] = None
            with self.subTest(mode=mode):
                report = self.assert_chain_pass(ctx)
                self.assertTrue(report['checks']['version_chain_state']['detail']['representation_log'])

    def test_chain_publish_own_receipt_prior_flip_and_single_latest_pass(self):
        ctx = self.chain_fixture('PUBLISH')
        report = self.assert_chain_pass(ctx)
        self.assertFalse(report['checks']['version_chain_state']['detail']['prior_versions_after']['is_latest'])
        self.assertTrue(report['checks']['version_chain_state']['detail']['successor_versions_after']['is_latest'])
        child = ctx['successor_actual']; publish = json.loads(Path(ctx['operation_evidence']['receipt_path']).read_text())
        context = dict(host='zenodo.org', record_id='1002', chain_parent_id='77', previous_latest_index=1,
            existing_concept_doi='10.5281/zenodo.77',
            same_operation_response={'id': '1002', 'doi': '10.5281/zenodo.1002', 'conceptdoi': '10.5281/zenodo.77'},
            own_publish_response=publish, same_operation_reservation_id='1002',
            temporal_baseline=ctx['successor_before_boundary'], version_chain_context=ctx)
        directory = Path(ctx['operation_evidence']['receipt_path']).parent
        self.saved_chain_receipt(str(directory), '003_GET.json', 'GET', 'https://zenodo.org/api/records/1002', child, status=200)
        path = directory / '003_GET.json'; receipt = json.loads(path.read_text())
        receipt['accept'] = 'application/vnd.inveniordm.v1+json'; path.write_text(json.dumps(receipt))
        context['revision_evidence'] = {'receipt_directory': str(directory), 'publish_receipt_name': '002_POST.json',
            'first_native_get_receipt_name': '003_GET.json', 'transport_contract_sha256': transport_contract_sha256()}
        self.assertEqual(validate_new_version(child, ctx['successor_expected'], **context)['status'], 'SERVER_MANAGED_READBACK_PASS')
        wrong = deepcopy(publish); wrong['response_sha256'] = 'e' * 64
        with self.assertRaisesRegex(ServerManagedMismatch, 'CHAIN_PUBLISH_AND_R0_RECEIPTS_DIFFER'):
            validate_new_version(child, ctx['successor_expected'], **(context | {'own_publish_response': wrong}))

    def test_chain_publish_latest_draft_absent_null_logged_present_false_fails(self):
        for mode in ('absent', 'null', 'false'):
            ctx = self.chain_fixture('PUBLISH')
            if mode == 'absent': ctx['successor_actual']['versions'].pop('is_latest_draft')
            else: ctx['successor_actual']['versions']['is_latest_draft'] = None if mode == 'null' else False
            with self.subTest(mode=mode):
                if mode == 'false': self.assert_chain_hold(ctx, 'CHAIN_IS_LATEST_DRAFT')
                else:
                    report = self.assert_chain_pass(ctx)
                    self.assertTrue(report['checks']['version_chain_state']['detail']['representation_log'])

    def test_chain_discard_saved_404_restores_prior_pass(self):
        ctx = self.chain_fixture('DISCARD'); self.assert_chain_pass(ctx)

    def test_chain_edit_own_receipt_versions_exact_pass(self):
        ctx = self.chain_fixture('EDIT'); self.assert_chain_pass(ctx)
        ctx['prior_actual']['versions']['is_latest_draft'] = False
        self.assert_chain_hold(ctx, 'CHAIN_EDIT_VERSIONS_CHANGED')

    def test_chain_every_boundary_missing_receipt_hash_tamper_or_non_2xx_fails(self):
        for boundary in ('CREATE', 'PUBLISH', 'DISCARD', 'EDIT'):
            key = 'creation_evidence' if boundary == 'CREATE' else 'operation_evidence'
            for change in ('missing', 'hash', 'method', 'status', 'raw_hash', 'body_hash', 'contract', 'host', 'endpoint', 'response_id'):
                ctx = self.chain_fixture(boundary)
                evidence = ctx[key]
                if change == 'missing': ctx[key] = None
                elif change == 'hash': evidence['receipt_sha256'] = '0' * 64
                elif change == 'contract': evidence['transport_contract_sha256'] = '0' * 64
                else:
                    path = Path(evidence['receipt_path']); receipt = json.loads(path.read_text())
                    if change == 'method': receipt['method'] = 'GET'
                    elif change == 'status': receipt['http_status'] = 500
                    elif change == 'raw_hash': receipt.pop('response_sha256')
                    elif change == 'body_hash': receipt.pop('request_body_sha256')
                    elif change == 'host': receipt['environment'] = 'sandbox.zenodo.org'
                    elif change == 'endpoint': receipt['url'] = receipt['url'].replace('zenodo.org', 'evil.org')
                    else: receipt['response']['id'] = '1003'
                    path.write_text(json.dumps(receipt)); evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
                with self.subTest(boundary=boundary, change=change): self.assert_chain_hold(ctx)

    def test_chain_wrong_direction_boundary_types_and_two_latest_fail(self):
        mutations = (
            ('CREATE', 'prior', 'is_latest_draft', True), ('CREATE', 'prior', 'is_latest', False),
            ('CREATE', 'child', 'is_latest_draft', False), ('CREATE', 'child', 'is_latest', True),
            ('CREATE', 'child', 'is_latest', 0), ('CREATE', 'child', 'is_latest_draft', 1),
            ('PUBLISH', 'prior', 'is_latest', True), ('PUBLISH', 'prior', 'is_latest_draft', True),
            ('PUBLISH', 'child', 'is_latest', False), ('DISCARD', 'prior', 'is_latest_draft', False),
        )
        for boundary, side, flag, value in mutations:
            ctx = self.chain_fixture(boundary)
            record = ctx['prior_actual'] if side == 'prior' else ctx['successor_actual']
            record['versions'][flag] = value
            with self.subTest(boundary=boundary, side=side, flag=flag, value=value): self.assert_chain_hold(ctx)
        ctx = self.chain_fixture('PUBLISH'); ctx['boundary'] = 'CREATE'
        self.assert_chain_hold(ctx)

    def test_chain_index_gap_reuse_prior_change_bool_and_published_missing_fail(self):
        for boundary in ('CREATE', 'PUBLISH'):
            for index in (0, 1, 3, True, -1, '2'):
                ctx = self.chain_fixture(boundary); ctx['successor_actual']['versions']['index'] = index
                with self.subTest(boundary=boundary, index=index): self.assert_chain_hold(ctx)
            ctx = self.chain_fixture(boundary); ctx['prior_actual']['versions']['index'] = 2
            self.assert_chain_hold(ctx, 'CHAIN_PRIOR_INDEX_CHANGED')
        for mode in ('absent', 'null'):
            ctx = self.chain_fixture('PUBLISH')
            if mode == 'absent': ctx['successor_actual']['versions'].pop('index')
            else: ctx['successor_actual']['versions']['index'] = None
            with self.subTest(mode=mode): self.assert_chain_hold(ctx)

    def test_chain_unrelated_record_parent_receipt_parent_or_unknown_versions_fails(self):
        for change in ('prior_id', 'child_id', 'prior_parent', 'child_parent', 'receipt_parent', 'parent_absent', 'prior_unknown', 'child_unknown'):
            ctx = self.chain_fixture()
            if change == 'prior_id': ctx['prior_actual']['id'] = '1003'
            elif change == 'child_id': ctx['successor_actual']['id'] = '1003'
            elif change == 'prior_parent': ctx['prior_actual']['parent']['id'] = '78'
            elif change == 'child_parent': ctx['successor_actual']['parent']['id'] = '78'
            elif change in ('receipt_parent', 'parent_absent'):
                evidence = ctx['creation_evidence']; path = Path(evidence['receipt_path']); receipt = json.loads(path.read_text())
                if change == 'receipt_parent': receipt['response']['conceptrecid'] = '78'
                else: receipt['response'].pop('conceptrecid')
                path.write_text(json.dumps(receipt)); evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            elif change == 'prior_unknown': ctx['prior_actual']['versions']['future'] = True
            else: ctx['successor_actual']['versions']['future'] = True
            with self.subTest(change=change): self.assert_chain_hold(ctx)
        ctx = self.chain_fixture()
        actual = deepcopy(ctx['prior_before_create']); actual['id'] = '1003'
        expected = deepcopy(actual)
        report = audit_readback(actual, expected, host='zenodo.org', record_id='1003', operation='PRIOR_VERSION',
            chain_parent_id='77', version_chain_context=ctx)
        self.assertEqual(report['status'], 'HOLD'); self.assertIn('CHAIN_CONTEXT_UNRELATED_RECORD', json.dumps(report))

    def test_chain_prior_all_sources_ui_pids_media_and_unknown_exact_checksum_fails(self):
        for boundary in ('CREATE', 'PUBLISH', 'DISCARD', 'EDIT'):
            for field in ('metadata', 'custom_fields', 'pids', 'files', 'ui', 'access', 'media_files', 'unlisted'):
                ctx = self.chain_fixture(boundary); prior = ctx['prior_actual']
                if field == 'metadata': prior[field]['description'] = '<p>Exact  claim</p>'
                elif field == 'files': prior[field][0]['checksum'] = 'changed'
                elif field == 'unlisted': prior[field] = 'changed'
                elif field == 'media_files': prior[field] = {'future': 'changed'}
                else: prior[field]['future'] = 'changed'
                with self.subTest(boundary=boundary, field=field): self.assert_chain_hold(ctx)
        ctx = self.chain_fixture('PUBLISH'); ctx['prior_actual']['files'].reverse()
        self.assert_chain_pass(ctx)

    def test_chain_discard_requires_actual_draft_and_later_saved_404(self):
        for change in ('no_before', 'published', 'missing_404', 'not_404', 'wrong_id', 'wrong_order', 'not_gone', 'not_restored'):
            ctx = self.chain_fixture('DISCARD')
            if change == 'no_before': ctx['successor_before_boundary'] = None
            elif change == 'published': ctx['successor_before_boundary'].update(is_draft=False, is_published=True)
            elif change == 'missing_404': ctx['successor_absence_evidence'] = None
            elif change == 'not_gone': ctx['successor_actual'] = deepcopy(ctx['successor_before_boundary'])
            elif change == 'not_restored': ctx['prior_actual']['versions']['is_latest'] = False
            else:
                evidence = ctx['successor_absence_evidence']; path = Path(evidence['receipt_path']); receipt = json.loads(path.read_text())
                if change == 'not_404': receipt['http_status'] = 200
                elif change == 'wrong_id': receipt['url'] = receipt['url'].replace('1002', '1003')
                else:
                    new = path.with_name('001_GET.json'); new.write_text(path.read_text()); evidence['receipt_path'] = str(new); path = new
                path.write_text(json.dumps(receipt)); evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(change=change): self.assert_chain_hold(ctx)

    def test_chain_no_receipt_unrelated_chain_and_amendment_versions_changes_hold(self):
        initial = deepcopy(self.expected); initial['versions']['is_latest_draft'] = True
        actual = deepcopy(initial); actual['versions']['is_latest_draft'] = False
        with self.assertRaisesRegex(ServerManagedMismatch, 'MATCHING_OWN_CHAIN_RECEIPT_REQUIRED'):
            validate_prior_version(actual, initial, host='zenodo.org', record_id='1001', chain_parent_id='77')
        with self.assertRaises(ServerManagedMismatch):
            validate_amendment(actual, initial, host='zenodo.org', record_id='1001')
        ctx = self.chain_fixture()
        with self.assertRaisesRegex(ServerManagedMismatch, 'CHAIN_AMENDMENT_CANNOT_USE_SUCCESSOR_TRANSITION'):
            validate_amendment(ctx['prior_actual'], ctx['prior_before_create'], host='zenodo.org', record_id='1001',
                chain_parent_id='77', version_chain_context=ctx)


    def test_chain_publish_native_existing_endpoint_receipt_pass(self):
        ctx = self.chain_fixture('PUBLISH')
        evidence = ctx['operation_evidence']; path = Path(evidence['receipt_path'])
        receipt = json.loads(path.read_text())
        receipt['url'] = 'https://zenodo.org/api/records/1002/draft/actions/publish'
        path.write_text(json.dumps(receipt)); evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assert_chain_pass(ctx)

    def test_chain_wrong_operation_response_parent_receipt_required_hash_and_symlink_fail(self):
        for boundary in ('PUBLISH', 'DISCARD', 'EDIT'):
            ctx = self.chain_fixture(boundary); evidence = ctx['operation_evidence']
            path = Path(evidence['receipt_path']); receipt = json.loads(path.read_text())
            receipt['response']['conceptrecid'] = '78'; path.write_text(json.dumps(receipt))
            evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(boundary=boundary): self.assert_chain_hold(ctx, 'CHAIN_OPERATION_RESPONSE_PARENT_MISMATCH')
        ctx = self.chain_fixture(); ctx['creation_evidence']['unlisted'] = True
        self.assert_chain_hold(ctx, 'CHAIN_SAVED_RECEIPT_EVIDENCE_REQUIRED')
        ctx = self.chain_fixture(); evidence = ctx['creation_evidence']
        path = Path(evidence['receipt_path']); link = path.with_name('saved-link.json'); link.symlink_to(path)
        evidence['receipt_path'] = str(link)
        self.assert_chain_hold(ctx, 'CHAIN_RECEIPT_REGULAR_SAVED_FILE_REQUIRED')
        ctx = self.chain_fixture(); path = Path(ctx['creation_evidence']['receipt_path'])
        receipt = json.loads(path.read_text()); receipt['response']['submitted'] = True
        path.write_text(json.dumps(receipt)); ctx['creation_evidence']['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assert_chain_hold(ctx, 'CHAIN_CREATION_UNPUBLISHED_SUCCESSOR_REQUIRED')

    def test_chain_saved_404_wrong_authentication_or_sequence_gap_fail(self):
        for change in ('accept', 'status', 'error_type', 'sequence_gap'):
            ctx = self.chain_fixture('DISCARD')
            evidence = ctx['successor_absence_evidence']; path = Path(evidence['receipt_path'])
            if change == 'sequence_gap': Path(ctx['creation_evidence']['receipt_path']).rename(path.with_name('outside-sequence.json'))
            else:
                receipt = json.loads(path.read_text()); receipt[change] = 'wrong'
                path.write_text(json.dumps(receipt)); evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.subTest(change=change): self.assert_chain_hold(ctx)

    def test_existing_chain_publish_cannot_omit_pair_context_or_guess_prior(self):
        actual = deepcopy(self.expected); actual['versions']['index'] = 2
        with self.assertRaisesRegex(ServerManagedMismatch, 'EXISTING_CHAIN_PUBLISH_PAIRED_RECEIPT_CONTEXT_REQUIRED'):
            self.check(actual, previous_latest_index=1)
        ctx = self.chain_fixture('PUBLISH'); ctx['prior_actual']['versions']['is_latest'] = True
        self.assert_chain_hold(ctx, 'CHAIN_IS_LATEST_WRONG_DIRECTION_OR_BOUNDARY')

    def test_chain_prior_revision_remains_monotonic_and_requires_latest_flip(self):
        for boundary in ('CREATE', 'PUBLISH', 'DISCARD', 'EDIT'):
            ctx = self.chain_fixture(boundary); ctx['prior_actual']['revision_id'] += 1
            with self.subTest(boundary=boundary):
                if boundary == 'PUBLISH': self.assert_chain_pass(ctx)
                else: self.assert_chain_hold(ctx, 'PRIOR_REVISION_CHANGE_WITHOUT_LATEST_FLIP')
        ctx = self.chain_fixture('PUBLISH'); ctx['prior_actual']['revision_id'] = 0
        self.assert_chain_hold(ctx, 'PRIOR_REVISION_DECREASE')


    def preview_fixture(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        expected = deepcopy(self.expected)
        rows = []
        for name, data, source_id in (
                ('paper.pdf', b'approved PDF bytes', '11111111-1111-1111-1111-111111111111'),
                ('archive.zip', b'approved ZIP bytes', '22222222-2222-2222-2222-222222222222')):
            rows.append({'key': name, 'size': len(data), 'checksum': 'md5:' + hashlib.md5(data).hexdigest(),
                'id': source_id, 'sha256': hashlib.sha256(data).hexdigest()})
        expected['files'] = {'enabled': True, 'order': [], 'count': len(rows),
            'total_bytes': sum(row['size'] for row in rows),
            'entries': {row['key']: {key: value for key, value in row.items() if key != 'sha256'} for row in rows}}
        expected['media_files'] = {'enabled': False, 'order': [], 'count': 0, 'total_bytes': 0, 'entries': {}}
        inventory_path = Path(directory.name, 'APPROVED_INVENTORY.json')
        inventory_path.write_text(json.dumps({'files': rows}))
        lineage = self.saved_chain_receipt(directory.name, '001_POST.json', 'POST',
            'https://zenodo.org/api/deposit/depositions/1001/actions/edit',
            {'id': '1001', 'links': {'bucket': 'https://zenodo.org/api/files/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}}, status=201)
        upload = self.saved_chain_receipt(directory.name, '002_PUT.json', 'PUT',
            'https://zenodo.org/api/files/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/paper.pdf',
            {**{key: rows[0][key] for key in ('key', 'size', 'checksum')}, 'is_head': True, 'delete_marker': False}, status=200)
        self.preview_receipt_change(upload, lambda r:r.update(request_body_sha256=rows[0]['sha256']))
        native = self.saved_chain_receipt(directory.name, '003_GET.json', 'GET',
            'https://zenodo.org/api/records/1001', expected, status=200)
        self.preview_receipt_change(native, lambda r:r.update(accept='application/vnd.inveniordm.v1+json',request_body_sha256=None))
        ctx = {'own_record_id': '1001', 'approved_inventory_evidence': {'path': str(inventory_path),
            'sha256': hashlib.sha256(inventory_path.read_bytes()).hexdigest()}, 'lineage_evidence': lineage,
            'source_readback_evidence': [native], 'delete_evidence': [], 'upload_evidence': [upload], 'publish_evidence': None}
        return expected, deepcopy(expected), ctx

    def preview_receipt_change(self, evidence, mutate):
        path = Path(evidence['receipt_path']); receipt = json.loads(path.read_text())
        mutate(receipt); path.write_text(json.dumps(receipt))
        evidence['receipt_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()

    def preview_audit(self, actual, expected, ctx, operation='AMENDMENT'):
        return audit_readback(actual, expected, host='zenodo.org', record_id='1001', operation=operation,
            own_operation_record_id='1001', derived_preview_context=ctx)

    def test_preview_thumbnail_uploaded_source_appearance_full_log_pass(self):
        expected, actual, ctx = self.preview_fixture()
        actual['links']['thumbnails'] = {'small': 'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/100,/0/default.jpg'}
        report = self.preview_audit(actual, expected, ctx)
        self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS', report)
        self.assertEqual(report['derived_preview_diff_appendix'][0]['path'], 'links.thumbnails')
        projection = require_derived_previews(actual, expected, host='zenodo.org', record_id='1001',
            operation='AMENDMENT', derived_preview_context=ctx)
        self.assertEqual(projection['normalized_actual'], expected)
        self.assertTrue(projection['main_inventory_separate'])

    def test_preview_thumbnail_publish_source_reappearance_pass(self):
        expected, actual, ctx = self.preview_fixture();ctx['upload_evidence'] = []
        directory = Path(ctx['lineage_evidence']['receipt_path']).parent
        ctx['publish_evidence'] = self.saved_chain_receipt(str(directory),'004_POST.json','POST',
            'https://zenodo.org/api/deposit/depositions/1001/actions/publish',{'id':'1001'},status=202)
        actual['links']['thumbnails']={'small':'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
        self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')

    def test_preview_iiif_four_fields_current_source_pass_and_remove_regenerate(self):
        for field in ('iiif_api','iiif_base','iiif_canvas','iiif_info'):
            expected,actual,ctx=self.preview_fixture();ctx['upload_evidence']=[]
            actual['files']['entries']['paper.pdf']['links']={field:'https://zenodo.org/api/iiif/draft:1001:paper.pdf/'+field}
            with self.subTest(field=field):
                self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')
                self.assertEqual(self.preview_audit(expected,actual,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')

    def test_preview_zip_container_exact_source_pass(self):
        expected,actual,ctx=self.preview_fixture();ctx['upload_evidence']=[]
        actual['files']['entries']['archive.zip']['links']={'container':'https://zenodo.org/api/records/1001/files/archive.zip/container'}
        self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')
        actual['files']['entries']['paper.pdf']['links']={'container':'https://zenodo.org/api/records/1001/files/paper.pdf/container'}
        self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_preview_media_derived_current_source_separate_inventory_pass(self):
        expected,actual,ctx=self.preview_fixture();ctx['upload_evidence']=[]
        actual['media_files']={'enabled':True,'order':['paper.pdf.ptif'],'count':1,'total_bytes':12,'entries':{
            'paper.pdf.ptif':{'key':'paper.pdf.ptif','size':12,'processor':{'source_file_id':actual['files']['entries']['paper.pdf']['id']},
            'links':{'self':'https://zenodo.org/api/records/1001/media-files/paper.pdf.ptif'}}}}
        report=self.preview_audit(actual,expected,ctx)
        self.assertEqual(report['status'],'SERVER_MANAGED_READBACK_PASS',report)
        projection=require_derived_previews(actual,expected,host='zenodo.org',record_id='1001',operation='AMENDMENT',derived_preview_context=ctx)
        self.assertEqual(projection['normalized_actual']['files'],actual['files'])
        self.assertEqual(projection['normalized_actual']['files']['count'],2)
        self.assertTrue(any(row['path'].startswith('media_files') for row in projection['diff_appendix']))
        self.assertEqual(self.preview_audit(expected,actual,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')

    def preview_disappearance_fixture(self):
        expected,actual,ctx=self.preview_fixture()
        directory=Path(ctx['lineage_evidence']['receipt_path']).parent
        old=deepcopy(expected);old.update(is_draft=True,is_published=False);old['ui']['is_draft']=True
        old['expires_at']='2026-10-05T01:00:00Z';old['links']['thumbnails']={'small':'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
        before=self.saved_chain_receipt(str(directory),'004_GET.json','GET','https://zenodo.org/api/records/1001/draft',old,status=200)
        self.preview_receipt_change(before,lambda r:r.update(accept='application/vnd.inveniordm.v1+json'))
        source=old['files']['entries']['paper.pdf']
        removed=self.saved_chain_receipt(str(directory),'005_DELETE.json','DELETE',
            'https://zenodo.org/api/deposit/depositions/1001/files/'+source['id'],{'empty_204':True,'draft_file_removed':True},status=204)
        self.preview_receipt_change(removed,lambda r:r.update(request_body_sha256=hashlib.sha256(b'').hexdigest(),response_sha256=hashlib.sha256(b'').hexdigest()))
        after=deepcopy(old);after['files']['entries'].pop('paper.pdf');after['files']['count']=1
        after['files']['total_bytes']=after['files']['entries']['archive.zip']['size'];after['links'].pop('thumbnails')
        following=self.saved_chain_receipt(str(directory),'006_GET.json','GET','https://zenodo.org/api/records/1001/draft',after,status=200)
        self.preview_receipt_change(following,lambda r:r.update(accept='application/vnd.inveniordm.v1+json'))
        removal_plan=Path(directory,'APPROVED_REMOVAL_PLAN.json');removal_plan.write_text(json.dumps({'drop':[{
            'name':'paper.pdf','size':source['size'],'checksum':source['checksum'][4:],'file_id':source['id'],
            'original_entry':{'filename':'paper.pdf','filesize':source['size'],'checksum':source['checksum'][4:],'id':source['id']}}]}))
        ctx['approved_removal_inventory_evidence']={'path':str(removal_plan),'sha256':hashlib.sha256(removal_plan.read_bytes()).hexdigest()}
        ctx['source_readback_evidence']=[before,following];ctx['upload_evidence']=[];ctx['delete_evidence']=[removed]
        expected=deepcopy(after);expected['links']['thumbnails']=old['links']['thumbnails']
        return expected,after,ctx

    def test_preview_thumbnail_disappearance_exact_saved_delete_staged_source_pass(self):
        expected,actual,ctx=self.preview_disappearance_fixture()
        # The frozen approved replacement may differ from the removed old PDF.
        path=Path(ctx['approved_inventory_evidence']['path']);inventory=json.loads(path.read_text())
        inventory['files'][0]['checksum']='md5:'+'e'*32;inventory['files'][0]['size']=999
        path.write_text(json.dumps(inventory));ctx['approved_inventory_evidence']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        report=audit_readback(actual,expected,host='zenodo.org',record_id='1001',operation='AMENDMENT',phase='DRAFT',
            own_operation_record_id='1001',derived_preview_context=ctx)
        self.assertEqual(report['status'],'SERVER_MANAGED_READBACK_PASS',report)
        self.assertTrue(report['checks']['derived_previews']['detail']['provenance']['deletions'])

    def test_preview_disappearance_no_context_no_receipt_wrong_direction_scope_hash_and_source_fail(self):
        for change in ('context','delete','removal_plan','wrong_id','wrong_host','non2xx','before_after','source_checksum','source_size','source_key','source_id','inventory_hash','file_hash'):
            expected,actual,ctx=self.preview_disappearance_fixture()
            if change=='context':ctx=None
            elif change=='delete':ctx['delete_evidence']=[]
            elif change=='removal_plan':ctx.pop('approved_removal_inventory_evidence')
            elif change=='wrong_id':ctx['own_record_id']='1002'
            elif change=='inventory_hash':ctx['approved_removal_inventory_evidence']['sha256']='0'*64
            elif change=='file_hash':ctx['delete_evidence'][0]['receipt_sha256']='0'*64
            else:
                if change=='wrong_host':self.preview_receipt_change(ctx['delete_evidence'][0],lambda r:r.update(url=r['url'].replace('zenodo.org','evil.org')))
                elif change=='non2xx':self.preview_receipt_change(ctx['delete_evidence'][0],lambda r:r.update(http_status=500))
                elif change=='before_after':ctx['source_readback_evidence']=ctx['source_readback_evidence'][:1]
                else:
                    path=Path(ctx['approved_removal_inventory_evidence']['path']);v=json.loads(path.read_text());row=v['drop'][0]
                    if change=='source_checksum':row['checksum']='0'*32;row['original_entry']['checksum']='0'*32
                    elif change=='source_size':row['size']+=1;row['original_entry']['filesize']+=1
                    elif change=='source_key':row['name']='foreign.pdf';row['original_entry']['filename']='foreign.pdf'
                    else:row['file_id']='foreign';row['original_entry']['id']='foreign'
                    path.write_text(json.dumps(v));ctx['approved_removal_inventory_evidence']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            report=audit_readback(actual,expected,host='zenodo.org',record_id='1001',operation='AMENDMENT',phase='DRAFT',
                own_operation_record_id='1001',derived_preview_context=ctx)
            with self.subTest(change=change):self.assertEqual(report['status'],'HOLD')

    def test_preview_foreign_host_record_file_unapproved_link_all_classes_fail(self):
        for derived in ('thumbnail','iiif','container','media'):
            for error in ('host','record','file'):
                expected,actual,ctx=self.preview_fixture()
                source='archive.zip' if derived=='container' else 'paper.pdf'
                url='https://zenodo.org/api/records/1001/files/'+source+'/container' if derived=='container' else 'https://zenodo.org/api/iiif/record:1001:'+source+'/full/max/0/default.jpg'
                if error=='host':url=url.replace('zenodo.org','evil.org')
                elif error=='record':url=url.replace('1001','1002')
                else:url=url.replace(source,'foreign.pdf')
                if derived=='thumbnail':actual['links']['thumbnails']={'small':url}
                elif derived=='iiif':actual['files']['entries'][source]['links']={'iiif_api':url}
                elif derived=='container':actual['files']['entries'][source]['links']={'container':url}
                else:actual['media_files']={'entries':{'paper.ptif':{'processor':{'source_file_id':actual['files']['entries'][source]['id']},'links':{'self':url}}}}
                with self.subTest(derived=derived,error=error):self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_preview_media_source_unresolved_unapproved_foreign_and_cannot_replace_main_fail(self):
        for change in ('unknown_id','foreign_id','unapproved','missing_main','checksum','size','key','media_count'):
            expected,actual,ctx=self.preview_fixture();source=actual['files']['entries']['paper.pdf']
            actual['media_files']={'entries':{'paper.ptif':{'size':9,'processor':{'source_file_id':source['id']}}},'count':1,'total_bytes':9}
            if change in ('unknown_id','foreign_id'):actual['media_files']['entries']['paper.ptif']['processor']['source_file_id']='foreign'
            elif change=='unapproved':
                path=Path(ctx['approved_inventory_evidence']['path']);v=json.loads(path.read_text());v['files']=v['files'][1:]
                path.write_text(json.dumps(v));ctx['approved_inventory_evidence']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            elif change=='missing_main':actual['files']['entries'].pop('paper.pdf')
            elif change=='checksum':source['checksum']='md5:'+'0'*32
            elif change=='size':source['size']+=1
            elif change=='key':source['key']='foreign.pdf'
            else:actual['media_files']['count']=2
            with self.subTest(change=change):self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_preview_own_source_get_lineage_upload_or_publish_provenance_tamper_fail(self):
        for change in ('lineage_missing','lineage_foreign','read_missing','read_foreign','upload_missing','upload_bucket','upload_hash','upload_checksum','publish_foreign'):
            expected,actual,ctx=self.preview_fixture();actual['links']['thumbnails']={'small':'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
            if change=='lineage_missing':ctx['lineage_evidence']=None
            elif change=='lineage_foreign':self.preview_receipt_change(ctx['lineage_evidence'],lambda r:r['response'].update(id='1002'))
            elif change=='read_missing':ctx['source_readback_evidence']=[]
            elif change=='read_foreign':self.preview_receipt_change(ctx['source_readback_evidence'][0],lambda r:r['response'].update(id='1002'))
            elif change=='upload_missing':ctx['upload_evidence']=[]
            elif change=='upload_bucket':self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(url=r['url'].replace('aaaaaaaa','bbbbbbbb')))
            elif change=='upload_hash':self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(request_body_sha256='0'*64))
            elif change=='upload_checksum':self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r['response'].update(checksum='md5:'+'0'*32))
            else:
                directory=Path(ctx['lineage_evidence']['receipt_path']).parent
                ctx['upload_evidence']=[];ctx['publish_evidence']=self.saved_chain_receipt(str(directory),'004_POST.json','POST',
                    'https://zenodo.org/api/deposit/depositions/1002/actions/publish',{'id':'1002'},status=202)
            with self.subTest(change=change):self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_preview_prior_untouched_change_and_required_links_stats_removal_still_fail(self):
        expected,actual,ctx=self.preview_fixture();actual['links']['thumbnails']={'small':'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
        self.assertEqual(self.preview_audit(actual,expected,ctx,operation='PRIOR_VERSION')['status'],'HOLD')
        for group,key in (('links','self'),('links','parent'),('stats','views')):
            changed=deepcopy(actual);changed[group].pop(key)
            with self.subTest(group=group,key=key):self.assertEqual(self.preview_audit(changed,expected,ctx)['status'],'HOLD')
        changed=deepcopy(actual);changed['metadata']['title']='foreign claim'
        self.assertEqual(self.preview_audit(changed,expected,ctx)['status'],'HOLD')


    def test_preview_exact_canvas_grammar_pass_foreign_record_file_host_fail(self):
        for variant in ('valid', 'host', 'record', 'file', 'extra_segment'):
            expected, actual, ctx = self.preview_fixture();ctx['upload_evidence'] = []
            url = 'https://zenodo.org/api/iiif/record:1001/canvas/paper.pdf'
            if variant == 'host': url = url.replace('zenodo.org', 'evil.org')
            elif variant == 'record': url = url.replace('1001', '1002')
            elif variant == 'file': url = url.replace('paper.pdf', 'foreign.pdf')
            elif variant == 'extra_segment': url += '/extra'
            actual['files']['entries']['paper.pdf']['links'] = {'iiif_canvas': url}
            with self.subTest(variant=variant):
                report = self.preview_audit(actual, expected, ctx)
                self.assertEqual(report['status'], 'SERVER_MANAGED_READBACK_PASS' if variant == 'valid' else 'HOLD', report)

    def test_preview_all_main_checksum_size_key_drift_fails_each_derived_row(self):
        for derived in ('thumbnail', 'iiif', 'container', 'media'):
            for field in ('checksum', 'size', 'key'):
                expected, actual, ctx = self.preview_fixture()
                name = 'archive.zip' if derived == 'container' else 'paper.pdf'
                row = actual['files']['entries'][name]
                if derived == 'thumbnail': actual['links']['thumbnails'] = {'small': 'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
                elif derived == 'iiif': row['links'] = {'iiif_canvas': 'https://zenodo.org/api/iiif/record:1001/canvas/paper.pdf'}
                elif derived == 'container': row['links'] = {'container': 'https://zenodo.org/api/records/1001/files/archive.zip/container'}
                else: actual['media_files'] = {'entries': {'paper.ptif': {'processor': {'source_file_id': row['id']}}}}
                row[field] = 'md5:' + '0' * 32 if field == 'checksum' else row[field] + 1 if field == 'size' else 'foreign.pdf'
                with self.subTest(derived=derived, field=field): self.assertEqual(self.preview_audit(actual, expected, ctx)['status'], 'HOLD')

    def test_preview_presence_full_values_and_media_aggregate_consistency(self):
        expected, actual, ctx = self.preview_fixture()
        actual['links']['thumbnails'] = {'small': 'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
        result = require_derived_previews(actual, expected, host='zenodo.org', record_id='1001', operation='AMENDMENT', derived_preview_context=ctx)
        log = result['diff_appendix'][0]
        self.assertEqual(log['before_present'], False); self.assertEqual(log['after_present'], True)
        self.assertEqual(log['after'], actual['links']['thumbnails'])
        expected, actual, ctx = self.preview_disappearance_fixture()
        result = require_derived_previews(actual, expected, host='zenodo.org', record_id='1001', operation='AMENDMENT', phase='DRAFT', derived_preview_context=ctx)
        log = result['diff_appendix'][0]
        self.assertEqual(log['before_present'], True); self.assertEqual(log['after_present'], False)
        self.assertEqual(log['before'], expected['links']['thumbnails'])
        for field, value in (('count', 2), ('count', True), ('total_bytes', 10), ('total_bytes', True)):
            expected, actual, ctx = self.preview_fixture()
            actual['media_files'] = {'enabled': True, 'order': ['paper.ptif'], 'type': 'image-tiles', 'entries': {'paper.ptif': {'size': 9, 'processor': {'source_file_id': actual['files']['entries']['paper.pdf']['id']}}}, 'count': 1, 'total_bytes': 9}
            with self.subTest(field=field, value=value):
                self.assertEqual(self.preview_audit(actual, expected, ctx)['status'], 'SERVER_MANAGED_READBACK_PASS')
                actual['media_files'][field] = value
                self.assertEqual(self.preview_audit(actual, expected, ctx)['status'], 'HOLD')

    def test_preview_partial_thumbnail_source_disappearance_requires_delete(self):
        expected, actual, ctx = self.preview_fixture()
        expected['links']['thumbnails'] = {'pdf': 'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg', 'zip': 'https://zenodo.org/api/iiif/record:1001:archive.zip/full/max/0/default.jpg'}
        actual['links']['thumbnails'] = {'pdf': expected['links']['thumbnails']['pdf']}
        self.assertEqual(self.preview_audit(actual, expected, ctx)['status'], 'HOLD')

    def test_preview_deleted_source_cannot_reappear_or_seed_media(self):
        for derived in ('thumbnail', 'media'):
            expected, actual, ctx = self.preview_disappearance_fixture()
            directory = Path(ctx['lineage_evidence']['receipt_path']).parent
            ctx['publish_evidence'] = self.saved_chain_receipt(str(directory), '007_POST.json', 'POST', 'https://zenodo.org/api/deposit/depositions/1001/actions/publish', {'id': '1001'}, status=202)
            if derived == 'thumbnail':
                actual['links']['thumbnails'] = {'large': 'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/200,/0/default.jpg'}
            else:
                source = json.loads(Path(ctx['source_readback_evidence'][0]['receipt_path']).read_text())['response']['files']['entries']['paper.pdf']['id']
                actual['media_files'] = {'entries': {'paper.ptif': {'processor': {'source_file_id': source}}}}
            with self.subTest(derived=derived):
                report = audit_readback(actual, expected, host='zenodo.org', record_id='1001', operation='AMENDMENT', phase='DRAFT', own_operation_record_id='1001', derived_preview_context=ctx)
                self.assertEqual(report['status'], 'HOLD')


    def pdf_bytes(self, *, pages=2, width='612', height='792', mixed=False,
                  rotate=0, user_unit='1', crop=False, encrypted=False):
        from io import BytesIO
        from pypdf import PdfWriter
        from pypdf.generic import ArrayObject, NameObject, NumberObject, FloatObject
        writer = PdfWriter()
        for index in range(pages):
            page = writer.add_blank_page(width=612, height=792)
            w = str(int(width) + 1) if mixed and index else width
            page[NameObject('/MediaBox')] = ArrayObject([NumberObject(0), NumberObject(0), FloatObject(w), FloatObject(height)])
            if crop: page[NameObject('/CropBox')] = ArrayObject([NumberObject(0), NumberObject(0), NumberObject(600), NumberObject(780)])
            if rotate: page[NameObject('/Rotate')] = NumberObject(rotate)
            if user_unit != '1': page[NameObject('/UserUnit')] = FloatObject(user_unit)
        if encrypted: writer.encrypt('test-password')
        result=BytesIO();writer.write(result);return result.getvalue()

    def byte_metadata_fixture(self, **pdf_options):
        expected,actual,ctx=self.preview_fixture()
        directory=Path(ctx['lineage_evidence']['receipt_path']).parent
        data=self.pdf_bytes(**pdf_options);source_path=directory/'APPROVED_PAPER.pdf';source_path.write_bytes(data)
        entry=expected['files']['entries']['paper.pdf'];entry.update(size=len(data),checksum='md5:'+hashlib.md5(data).hexdigest(),metadata={})
        expected['files']['total_bytes']=sum(row['size'] for row in expected['files']['entries'].values())
        inventory_path=Path(ctx['approved_inventory_evidence']['path']);inventory=json.loads(inventory_path.read_text())
        row=inventory['files'][0];row.update(path=str(source_path),size=len(data),checksum=entry['checksum'],sha256=hashlib.sha256(data).hexdigest())
        inventory_path.write_text(json.dumps(inventory));ctx['approved_inventory_evidence']['sha256']=hashlib.sha256(inventory_path.read_bytes()).hexdigest()
        self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(request_body_sha256=row['sha256'],response={**{key:entry[key] for key in ('key','checksum','size')},'is_head':True,'delete_marker':False}))
        self.preview_receipt_change(ctx['source_readback_evidence'][0],lambda r:r.update(response=deepcopy(expected)))
        actual=deepcopy(expected);actual['files']['entries']['paper.pdf']['metadata']={'width':612,'height':792}
        return expected,actual,ctx

    def test_byte_metadata_same_pdf_integer_float_pair_full_parser_receipt_pass(self):
        from file_byte_metadata import compute_pdf_facts
        for representation in ('integer','float'):
            expected,actual,ctx=self.byte_metadata_fixture()
            if representation=='float':actual['files']['entries']['paper.pdf']['metadata']={'width':612.0,'height':792.0}
            report=self.preview_audit(actual,expected,ctx)
            with self.subTest(representation=representation):self.assertEqual(report['status'],'SERVER_MANAGED_READBACK_PASS',report)
            detail=report['checks']['derived_previews']['detail']['provenance']['byte_metadata'][0]
            self.assertEqual(detail['parser_output']['parser']['dependency_version'],'6.10.0')
            self.assertEqual(detail['parser_output']['parser']['name'],'ViridisApprovedPDFByteFacts')
            self.assertEqual(detail['parser_output']['facts']['page_count']['value'],2)
            self.assertEqual(detail['parser_output']['facts']['width']['decimal'],'612')
            projection=require_derived_previews(actual,expected,host='zenodo.org',record_id='1001',operation='AMENDMENT',derived_preview_context=ctx)
            self.assertEqual(projection['normalized_actual']['files'],expected['files'])
            self.assertEqual(projection['normalized_actual']['files']['count'],2)

    def test_byte_metadata_generalized_computable_page_and_format_facts_pass(self):
        expected,actual,ctx=self.byte_metadata_fixture()
        actual['files']['entries']['paper.pdf']['metadata'].update(page_count=2,number_of_pages=2,num_pages=2,mimetype='application/pdf',mime_type='application/pdf',format='PDF',pdf_version='1.3')
        report=self.preview_audit(actual,expected,ctx)
        self.assertEqual(report['status'],'SERVER_MANAGED_READBACK_PASS',report)
        output=report['checks']['derived_previews']['detail']['provenance']['byte_metadata'][0]
        self.assertEqual(len(output['changed_fields']),9)
        self.assertEqual(output['parser_output']['page_geometries'][0]['rotation_applied'],'0')
        self.assertEqual(output['parser_output']['page_geometries'][0]['selected_box'],'MediaBox')

    def test_byte_metadata_recomputation_mismatch_wrong_type_pair_noncomputable_fail(self):
        for error in ('width','height','zero','negative','nan','infinity','boolean','string','null','missing_width','missing_height','count','count_float','format','mime','version','unknown','nested','metadata_list','disappearance','empty_container'):
            expected,actual,ctx=self.byte_metadata_fixture();meta=actual['files']['entries']['paper.pdf']['metadata']
            if error=='width':meta['width']=613
            elif error=='height':meta['height']=791
            elif error=='zero':meta['width']=0
            elif error=='negative':meta['width']=-612
            elif error=='nan':meta['width']=float('nan')
            elif error=='infinity':meta['width']=float('inf')
            elif error=='boolean':meta['width']=True
            elif error=='string':meta['width']='612'
            elif error=='null':meta['height']=None
            elif error=='missing_width':meta.pop('width')
            elif error=='missing_height':meta.pop('height')
            elif error=='count':meta['page_count']=3
            elif error=='count_float':meta['page_count']=2.0
            elif error=='format':meta['format']='JPEG'
            elif error=='mime':meta['mimetype']='text/plain'
            elif error=='version':meta['pdf_version']='1.7'
            elif error=='unknown':meta['author']='arbitrary server value'
            elif error=='nested':meta['format']={'name':'PDF'}
            elif error=='metadata_list':actual['files']['entries']['paper.pdf']['metadata']=[]
            elif error=='empty_container':
                expected['files']['entries']['paper.pdf'].pop('metadata');actual['files']['entries']['paper.pdf']['metadata']={}
            else:
                expected['files']['entries']['paper.pdf']['metadata']={'page_count':2};meta.clear()
            with self.subTest(error=error):
                if error in ('nan','infinity'):
                    with self.assertRaisesRegex(TransportHold,'NON_JSON_INPUT'):
                        self.preview_audit(actual,expected,ctx)
                else:
                    self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_byte_metadata_approved_byte_identity_uuid_key_and_source_receipts_fail(self):
        for error in ('one_byte','checksum','size','key','uuid','path_missing','sha_missing','no_upload','no_get','get_before','foreign_record','foreign_bucket','wrong_upload_hash','wrong_parser_version'):
            expected,actual,ctx=self.byte_metadata_fixture();entry=actual['files']['entries']['paper.pdf']
            if error=='one_byte':
                inventory=json.loads(Path(ctx['approved_inventory_evidence']['path']).read_text());path=Path(inventory['files'][0]['path']);path.write_bytes(path.read_bytes()+b' ')
            elif error=='checksum':entry['checksum']='md5:'+'0'*32
            elif error=='size':entry['size']+=1
            elif error=='key':entry['key']='foreign.pdf'
            elif error=='uuid':entry['id']='foreign-source'
            elif error in ('path_missing','sha_missing'):
                path=Path(ctx['approved_inventory_evidence']['path']);v=json.loads(path.read_text());v['files'][0].pop('path' if error=='path_missing' else 'sha256');path.write_text(json.dumps(v));ctx['approved_inventory_evidence']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            elif error=='no_upload':ctx['upload_evidence']=[]
            elif error=='no_get':ctx['source_readback_evidence']=[]
            elif error=='get_before':
                old=ctx['source_readback_evidence'][0];new=Path(old['receipt_path']).with_name('001_GET.json');new.write_bytes(Path(old['receipt_path']).read_bytes());old.update(receipt_path=str(new),receipt_sha256=hashlib.sha256(new.read_bytes()).hexdigest())
            elif error=='foreign_record':self.preview_receipt_change(ctx['source_readback_evidence'][0],lambda r:r['response'].update(id='1002'))
            elif error=='foreign_bucket':self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(url=r['url'].replace('aaaaaaaa','bbbbbbbb')))
            elif error=='wrong_upload_hash':self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(request_body_sha256='0'*64))
            if error=='wrong_parser_version':
                import pypdf
                from unittest.mock import patch
                with patch.object(pypdf,'__version__','0.0.0'):
                    report=self.preview_audit(actual,expected,ctx)
            else:report=self.preview_audit(actual,expected,ctx)
            with self.subTest(error=error):self.assertEqual(report['status'],'HOLD')

    def test_byte_metadata_prior_untouched_record_record_metadata_and_other_entry_fields_fail(self):
        for error in ('prior','own_scope','record_title','other_field','main_count','unknown_existing_change'):
            expected,actual,ctx=self.byte_metadata_fixture();operation='AMENDMENT'
            if error=='prior':operation='PRIOR_VERSION'
            elif error=='own_scope':ctx['own_record_id']='1002'
            elif error=='record_title':actual['metadata']['title']='New scientific claim'
            elif error=='other_field':actual['files']['entries']['paper.pdf']['storage_class']='FOREIGN'
            elif error=='main_count':actual['files']['count']=3
            else:
                expected['files']['entries']['paper.pdf']['metadata']['author']='Alice';actual['files']['entries']['paper.pdf']['metadata']['author']='Bob'
            with self.subTest(error=error):self.assertEqual(self.preview_audit(actual,expected,ctx,operation)['status'],'HOLD')

    def test_byte_metadata_unsupported_geometry_and_malformed_pdf_fail(self):
        for options in ({'mixed':True},{'rotate':90},{'rotate':180},{'rotate':360},{'user_unit':'2'},{'crop':True},{'encrypted':True},{'pages':0},{'width':'0'}):
            expected,actual,ctx=self.byte_metadata_fixture(**options)
            with self.subTest(options=options):self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')
        expected,actual,ctx=self.byte_metadata_fixture()
        path=Path(ctx['approved_inventory_evidence']['path']);v=json.loads(path.read_text());row=v['files'][0];source=Path(row['path']);source.write_bytes(b'%PDF-1.3\nmalformed\n%%EOF\n')
        row.update(size=source.stat().st_size,checksum='md5:'+hashlib.md5(source.read_bytes()).hexdigest(),sha256=hashlib.sha256(source.read_bytes()).hexdigest());path.write_text(json.dumps(v));ctx['approved_inventory_evidence']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        for record in (expected,actual):record['files']['entries']['paper.pdf'].update(size=row['size'],checksum=row['checksum'])
        self.preview_receipt_change(ctx['upload_evidence'][0],lambda r:r.update(request_body_sha256=row['sha256'],response={**{k:row[k] for k in ('key','size','checksum')},'is_head':True,'delete_marker':False}))
        self.preview_receipt_change(ctx['source_readback_evidence'][0],lambda r:r.update(response=deepcopy(expected)))
        self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')

    def test_byte_metadata_exact_decimal_tokens_no_rounding_and_reader_restored(self):
        from file_byte_metadata import compute_pdf_facts, require_computed_field
        from pypdf.generic import NumberObject
        original=NumberObject.read_from_stream
        data=self.pdf_bytes(width='612.125',height='792.5')
        facts=compute_pdf_facts(data)
        self.assertIs(NumberObject.read_from_stream,original)
        self.assertEqual(facts['facts']['width']['decimal'],'612.125')
        require_computed_field(612.125,field='width',facts=facts['facts'])
        with self.assertRaises(ValueError):require_computed_field(612.1250001,field='width',facts=facts['facts'])
        # A valid independent PDF fixture retains >8-decimal original tokens.
        objects=[b'<< /Type /Catalog /Pages 2 0 R >>',
            b'<< /Type /Pages /Count 1 /Kids [3 0 R] >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612.1234567890123 792] /Resources << >> >>']
        exact=b'%PDF-1.5\n';offsets=[0]
        for index,obj in enumerate(objects,1):
            offsets.append(len(exact));exact+=str(index).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(exact);exact+=b'xref\n0 4\n0000000000 65535 f \n'
        for offset in offsets[1:]:exact+=f'{offset:010d} 00000 n \n'.encode()
        exact+=b'trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n'
        output=compute_pdf_facts(exact)
        self.assertEqual(output['facts']['width']['decimal'],'612.1234567890123')
        require_computed_field(612.1234567890123,field='width',facts=output['facts'])
        with self.assertRaises(ValueError):require_computed_field(612.12345679,field='width',facts=output['facts'])
        with self.assertRaises(ValueError):compute_pdf_facts(exact.replace(b'612.1234567890123',b'611'))
        self.assertIs(NumberObject.read_from_stream,original)

    def test_byte_metadata_absent_parser_dependency_is_hold_old_rules_still_standalone(self):
        expected,actual,ctx=self.byte_metadata_fixture()
        from unittest.mock import patch
        with patch.dict('sys.modules',{'pypdf':None}):
            self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'HOLD')
        # No new metadata means this lazy dependency is never consumed.
        expected,actual,ctx=self.preview_fixture()
        with patch.dict('sys.modules',{'file_byte_metadata':None,'pypdf':None}):
            self.assertEqual(self.preview_audit(actual,expected,ctx)['status'],'SERVER_MANAGED_READBACK_PASS')


    def test_byte_metadata_historical_or_reversed_amendment_upload_is_hold(self):
        for error in ('reversed','other_directory','create_not_edit'):
            expected,actual,ctx=self.byte_metadata_fixture()
            if error=='reversed':
                old=ctx['lineage_evidence'];new=Path(old['receipt_path']).with_name('004_POST.json');new.write_bytes(Path(old['receipt_path']).read_bytes())
                old.update(receipt_path=str(new),receipt_sha256=hashlib.sha256(new.read_bytes()).hexdigest())
            elif error=='other_directory':
                old=ctx['lineage_evidence'];new=Path(old['receipt_path']).parent/'later_edit'/'001_POST.json';new.parent.mkdir();new.write_bytes(Path(old['receipt_path']).read_bytes())
                old.update(receipt_path=str(new),receipt_sha256=hashlib.sha256(new.read_bytes()).hexdigest())
            else:self.preview_receipt_change(ctx['lineage_evidence'],lambda r:r.update(url='https://zenodo.org/api/deposit/depositions'))
            with self.subTest(error=error):
                report=self.preview_audit(actual,expected,ctx)
                self.assertEqual(report['status'],'HOLD')
                self.assertIn('BYTE_METADATA_AMENDMENT_UPLOAD_MUST_FOLLOW_OWN_EDIT',report['checks']['derived_previews']['reason'])

    def test_byte_metadata_concurrent_parser_calls_restore_exact_reader_function(self):
        import threading
        from concurrent.futures import ThreadPoolExecutor
        from unittest.mock import patch
        import pypdf
        import file_byte_metadata as parser
        from pypdf.generic import NumberObject
        original=NumberObject.read_from_stream;native_reader=pypdf.PdfReader
        first_inside=threading.Event();second_waiting=threading.Event()
        actual_lock=threading.RLock();counter_lock=threading.Lock();enters=0;readers=0
        class ObservedLock:
            def __enter__(self):
                nonlocal enters
                with counter_lock:
                    enters+=1
                    if enters==2:second_waiting.set()
                actual_lock.acquire()
                return self
            def __exit__(self,*args):actual_lock.release()
        def delayed_reader(*args,**kwargs):
            nonlocal readers
            readers+=1
            if readers==1:
                first_inside.set()
                if not second_waiting.wait(5):raise AssertionError('Second reader never reached the held parser lock')
            return native_reader(*args,**kwargs)
        content=self.pdf_bytes()
        with patch.object(parser,'_PARSE_LOCK',ObservedLock()),patch.object(pypdf,'PdfReader',delayed_reader):
            with ThreadPoolExecutor(max_workers=2) as workers:
                first=workers.submit(parser.compute_pdf_facts,content)
                self.assertTrue(first_inside.wait(5))
                second=workers.submit(parser.compute_pdf_facts,content)
                outputs=[first.result(timeout=10),second.result(timeout=10)]
        self.assertIs(NumberObject.read_from_stream,original)
        self.assertEqual(outputs[0],outputs[1])
        self.assertEqual(outputs[0]['facts']['width']['decimal'],'612')


if __name__ == '__main__':
    unittest.main()
