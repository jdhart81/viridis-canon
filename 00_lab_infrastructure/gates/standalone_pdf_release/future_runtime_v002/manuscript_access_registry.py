"""Closed, read-only nomination of original registrations and exact access copies.

This module grants no scientific or publication authority. The installed exact
historical registrar admits original evidence first. Only the explicitly named
copy receipt, original archive and actual user instruction may then establish
the narrowly declared extra PDF files in matching complete owner observations.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path
import re

import methods_digest_registration_v3 as registration
import manuscript_access_correction as access

STANDARD = 'VRS-MANUSCRIPT-ACCESS-REGISTRY-1'
REGISTRY_FIELDS = {'standard', 'status', 'observation_context', 'entries'}
ENTRY_FIELDS = {'record_id', 'registration', 'archive', 'access_correction', 'user_authority', 'prior_chain'}
CHAIN_FIELDS = {'baseline_legacy', 'baseline_native', 'creation', 'publish'}
ORIGINAL_CHAIN_SHA256 = 'ff7d1b18bfad1a66662cc519415301a841b7ec05b9bc613dd8279d3644f8974f'
CONTEXT = {'authentication': 'OWNER', 'owner_id': '1591505',
           'legacy_accept': 'application/json',
           'native_accept': 'application/vnd.inveniordm.v1+json'}
AUTHORITY_FIELDS = {'standard', 'status', 'record_id', 'doi', 'instruction', 'provider_instruction', 'copy_plan', 'scientific_change'}
INSTRUCTION_FIELDS = {'standard', 'evidence_kind', 'recorded_at_utc', 'task_id',
                      'user_message_verbatim', 'source', 'authorized_scope',
                      'does_not_authorize', 'claim'}
USER_REQUEST = 'make sure all our deposits have the actual papers as separate PDFs and make that standard for future releases'
DIRECT_USER_EVIDENCE_SHA256 = '7d6fb03a20152ccda9baa0a9e9e4239a53414a3453ab86fe3666042859f5dee4'
PROVIDER_USER_EVIDENCE_SHA256 = 'fb57aeaf4a43f0183043d12c28ed02a2ce326f452b8a596f1231a29d98123f0b'
REVIEWED_ARCHIVE_COPY_PLAN_SHA256 = '52ea2d0613dfbb3fcfe54e91f3619ba86cf2f8d6e9ebae183993893e34b1a331'


def need(condition, reason):
    if not condition:
        raise registration.RegistrationHold('HOLD_ACCESS_REGISTRY_' + reason)


def bound(root, binding):
    need(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}
         and type(binding['path']) is str and re.fullmatch('[0-9a-f]{64}', str(binding['sha256'])),
         'CLOSED_REGULAR_SOURCE_BINDING')
    return registration.d.bound_file(root, binding)[1]


def _object(root, binding):
    raw = bound(root, binding)
    value = json.loads(raw)
    need(isinstance(value, dict), 'BOUND_JSON_OBJECT')
    return value, raw


def _context(value):
    need(isinstance(value, dict) and value == CONTEXT, 'MATCHING_OWNER_OBSERVATION_CONTEXT')
    return deepcopy(value)


class RegistryContext:
    """Explicit factory used by the additive controller and corpus wrappers.

    download(record_id, filename) returns actual observed bytes. The matching
    owner_getter(record_id,accept) returns a complete actual owner GET body.
    A separately bounded GET-only observation operation may reread its exact
    retained bodies, byte files and transport journal, checking their hashes
    and expiry each time. Scientific/access admission runs again; a cached
    verdict is never an input. Publication mutations require fresh observations
    at each causal boundary. Anonymous PDF verification remains independently
    required by the outer gate. No network or credentials are discovered here.
    """

    def __init__(self, root, binding, *, download, observation_context, owner_getter=None):
        self.root = Path(root).resolve(strict=True)
        self.binding = deepcopy(binding)
        need(callable(download), 'ACTUAL_BYTE_READER')
        need(owner_getter is None or callable(owner_getter), 'OWNER_READER')
        self.download = download
        self.owner_getter = owner_getter
        self.observation_context = _context(observation_context)
        self._registry()

    def _registry(self):
        value, raw = _object(self.root, self.binding)
        need(set(value) == REGISTRY_FIELDS and value['standard'] == STANDARD
             and value['status'] == 'NOMINATED_INPUTS_NOT_AUTHORITY', 'CLOSED_REGISTRY')
        need(value['observation_context'] == self.observation_context, 'REGISTRY_CONTEXT')
        entries = value['entries']
        need(isinstance(entries, list), 'ENTRY_LIST')
        ids, bindings = set(), set()
        for entry in entries:
            need(isinstance(entry, dict) and set(entry) == ENTRY_FIELDS, 'CLOSED_ENTRY')
            rid = entry['record_id']
            need(type(rid) is str and re.fullmatch('[1-9][0-9]*', rid), 'RECORD_ID')
            key = json.dumps(entry['registration'], sort_keys=True)
            need(rid not in ids and key not in bindings, 'UNIQUE_NOMINATION')
            ids.add(rid)
            bindings.add(key)
            null_access = all(entry[field] is None for field in ('archive', 'access_correction', 'user_authority'))
            if null_access:
                named, _ = _object(self.root, entry['registration'])
                need(named.get('standard') == registration.STANDARD
                     and isinstance(entry['prior_chain'], dict)
                     and entry['prior_chain'].get('stage') == 'AFTER_ACCESS', 'EXPLICIT_CHAIN_ONLY_V3_NOMINATION')
            else:
                need(all(entry[field] is not None for field in ('archive', 'access_correction', 'user_authority')),
                     'NO_PARTIAL_ACCESS_NOMINATION')
            for field in ENTRY_FIELDS - {'record_id', 'prior_chain'}:
                if field in {'archive', 'access_correction', 'user_authority'} and null_access:
                    continue
                # Checks exact path/hash shape, containment, regular files and
                # observed source hash on each read; never stores a PASS.
                bound(self.root, entry[field])
            if entry['prior_chain'] is not None:
                chain = entry['prior_chain']
                need(isinstance(chain, dict) and set(chain) == CHAIN_FIELDS | {'stage'}
                     and chain['stage'] in {'BEFORE_ACCESS', 'AFTER_ACCESS'}, 'CLOSED_NOMINATED_CHAIN')
                self._chain_inputs({k: chain[k] for k in CHAIN_FIELDS}, rid)
        return value, raw

    def _plain_chain_registration(self, binding, ledger, *, views, chain, registered, registry_raw, registered_raw):
        """Actual V3 baseline is freshly admitted before unchanged chain replay."""
        need(registered.get('standard') == registration.STANDARD, 'CHAIN_ONLY_GENUINE_V3_REGISTRATION')
        admitted = registration.require_registration(self.root, binding, ledger, views=None)
        rid = admitted['receipt']['record_id']
        objects, snapshots = self._chain_inputs(chain, rid)
        baseline = (objects['baseline_legacy']['response'], objects['baseline_native']['response'])
        before = registration.require_registration(self.root, binding, ledger, views=baseline)
        need(before['receipt'] == admitted['receipt'] and before['strict_readback'] == admitted['strict_readback']
             and before['public_legacy'] == baseline[0] and before['public_native'] == baseline[1],
             'ACTUAL_CHAIN_BASELINE_REPLAY')
        if views is None:
            need(self.owner_getter is not None, 'FRESH_OWNER_PAIR_REQUIRED')
            views = (self.owner_getter(rid, CONTEXT['legacy_accept']), self.owner_getter(rid, CONTEXT['native_accept']))
        need(isinstance(views, (tuple, list)) and len(views) == 2 and all(isinstance(v, dict) for v in views)
             and str(views[1].get('parent', {}).get('access', {}).get('owned_by', {}).get('user')) == CONTEXT['owner_id'],
             'ACTUAL_OWNER_PAIR')
        checked = self._chain_pair(views, baseline, objects, chain)
        for source, raw in snapshots + [(self.binding, registry_raw), (binding, registered_raw)]:
            need(bound(self.root, source) == raw, 'CHAIN_ONLY_SOURCE_RACE')
        return {**admitted, 'public_legacy': deepcopy(views[0]), 'public_native': deepcopy(views[1]),
                'registered_public_views': {'legacy': deepcopy(admitted['public_legacy']), 'native': deepcopy(admitted['public_native'])},
                'prior_processing_audit': {'route': 'GENUINE_V3_FULL_OBSERVED_BASELINE_CHAIN',
                    'genuine_chain_audits': [checked], 'baseline_admission_audit': deepcopy(before.get('prior_processing_audit')),
                    'registry_binding': deepcopy(self.binding), 'observation_context': deepcopy(self.observation_context), 'certifies': False}}

    def _chain_inputs(self, value, rid):
        """Read actual operations and their complete observed OWNER baseline.

        BEFORE_ACCESS names the actual post-chain/pre-access GETs. AFTER_ACCESS
        names the actual pre-operation GETs, with the access PDFs already there.
        Neither input is a synthesized flag-adjusted representation.
        """
        need(isinstance(value, dict) and set(value) == CHAIN_FIELDS
             and value['creation'] is not None, 'CLOSED_GENUINE_CHAIN_INPUTS')
        objects, snapshots = {}, []
        for key, binding in value.items():
            if binding is None:
                need(key == 'publish', 'CHAIN_REQUIRED_BINDING')
                objects[key] = None
            else:
                objects[key], raw = _object(self.root, binding)
                snapshots.append((binding, raw))
        for key, accept in (('baseline_legacy', CONTEXT['legacy_accept']),
                            ('baseline_native', CONTEXT['native_accept'])):
            receipt = objects[key]
            need(receipt.get('environment') == 'zenodo.org' and receipt.get('method') == 'GET'
                 and receipt.get('url') == 'https://zenodo.org/api/records/' + rid
                 and receipt.get('accept') == accept
                 and receipt.get('status') == 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
                 and receipt.get('http_status') == 200
                 and receipt.get('request_body_sha256') is None
                 and isinstance(receipt.get('response'), dict), 'GENUINE_OWNER_BASELINE_RECEIPT')
        native = objects['baseline_native']['response']
        legacy = objects['baseline_legacy']['response']
        need(str(legacy.get('id')) == rid and native.get('id') == rid
             and str(native.get('parent', {}).get('access', {}).get('owned_by', {}).get('user')) == CONTEXT['owner_id'],
             'GENUINE_OWNER_BASELINE_IDENTITY')
        return objects, snapshots

    def _chain_pair(self, actual, before, objects, bindings):
        """Freshly use the unchanged original chain consumer on actual pairs."""
        original = importlib.import_module('own_prior_record')
        need(registration.d.sha(original.__file__) == ORIGINAL_CHAIN_SHA256,
             'EXACT_ORIGINAL_CHAIN_SOURCE')
        preservation = importlib.import_module('publication_preservation')
        checked = original.require_pair(actual[0], actual[1], before[0], before[1],
                                        creation=objects['creation'], publish=objects['publish'],
                                        preservation=preservation)
        # Preserve source/target/concept and actual creation/publication dates.
        # Dates are observations, not authority to change any flag.
        creation = objects['creation']['response']
        publication = None if objects['publish'] is None else objects['publish']['response']
        source_date = before[1].get('created', before[0].get('created'))
        date_rows = {'source_created': source_date, 'newer_created': creation.get('created'),
                     'newer_published_created': None if publication is None else publication.get('created')}
        parsed = []
        for name, value in date_rows.items():
            if name == 'newer_published_created' and publication is None:
                continue
            need(type(value) is str, 'CHAIN_OBSERVED_DATE:' + name)
            stamp = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
            need(stamp.tzinfo is not None and stamp <= dt.datetime.now(dt.timezone.utc),
                 'CHAIN_REAL_DATE:' + name)
            parsed.append(stamp)
        need(parsed == sorted(parsed), 'CHAIN_DATE_ORDER')
        return {'route': 'UNCHANGED_GENUINE_OBSERVED_PAIR_CHAIN_CONSUMER', 'pair': checked,
                'operation_inputs': deepcopy(bindings), 'old_id': before[1]['id'],
                'newer_id': str(creation['id']), 'concept_id': before[1]['parent']['id'],
                'observed_dates': date_rows, 'certifies': False}

    def _authority(self, nominated, correction):
        authority, authority_raw = _object(self.root, nominated)
        need(set(authority) == AUTHORITY_FIELDS
             and authority['standard'] == 'VRS-USER-MANUSCRIPT-ACCESS-AUTHORITY-1'
             and authority['status'] == 'SOURCE_BOUND_USER_INSTRUCTION'
             and authority['scientific_change'] is False, 'CLOSED_USER_AUTHORITY_INPUT')
        need(authority['record_id'] == correction['record_id']
             and authority['doi'] == correction['doi'], 'AUTHORITY_RECORD')
        for key in ('instruction', 'provider_instruction', 'copy_plan'):
            bound(self.root, authority[key])
        need(authority['instruction'].get('sha256') == DIRECT_USER_EVIDENCE_SHA256
             and authority['provider_instruction'].get('sha256') == PROVIDER_USER_EVIDENCE_SHA256
             and authority['copy_plan'].get('sha256') == REVIEWED_ARCHIVE_COPY_PLAN_SHA256,
             'GENUINE_REVIEWED_USER_AND_PLAN_SOURCES')
        instruction, instruction_raw = _object(self.root, authority['instruction'])
        need(set(instruction) == INSTRUCTION_FIELDS
             and instruction['standard'] == 'VRS-DIRECT-USER-MANUSCRIPT-ACCESS-INSTRUCTION-1'
             and instruction['evidence_kind'] == 'DIRECT_HUMAN_USER_MESSAGE'
             and instruction['task_id'] == '01a12d47-02a3-78f3-beb4-6b8e1a079dd2'
             and type(instruction['recorded_at_utc']) is str and instruction['recorded_at_utc']
             and type(instruction['source']) is str and instruction['source']
             and type(instruction['claim']) is str and instruction['claim']
             and instruction['user_message_verbatim'] == USER_REQUEST
             and instruction['authorized_scope'] == {
                 'owned_published_deposits': True, 'separate_actual_manuscript_pdfs': True,
                 'preserve_original_scientific_evidence': True, 'make_pdf_requirement_future_release_standard': True}
             and instruction['does_not_authorize'] == {
                 'new_scientific_certification': True, 'changed_original_archives': True,
                 'expanded_automatic_scientific_publication': True}, 'EXACT_EXISTING_HUMAN_USER_REQUEST')
        provider, provider_raw = _object(self.root, authority['provider_instruction'])
        need(set(provider) == {'standard', 'provider_tool', 'captured_at_utc', 'thread_id', 'thread_title',
                              'turn_id', 'projection', 'user_messages', 'validation_pass_claimed'}
             and provider['standard'] == 'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1'
             and provider['provider_tool'] == 'mcp__codex_app__read_thread'
             and provider['thread_id'] == instruction['task_id']
             and provider['turn_id'] == '01a132f6-46cd-7e41-9c02-f8ca68567a46'
             and provider['validation_pass_claimed'] is False
             and provider['user_messages'] == [{'type': 'userMessage',
                 'id': '01a132f6-4708-7440-a9ba-ebf03deeb906',
                 'content': [{'type': 'text', 'text': USER_REQUEST + '\n'}]}],
             'GENUINE_PROVIDER_USER_MESSAGE')
        plan, plan_raw = _object(self.root, authority['copy_plan'])
        records = plan.get('records')
        need(isinstance(records, list), 'EXACT_REVIEWED_COPY_PLAN')
        matching = [row for row in records if isinstance(row, dict)
                    and str(row.get('record_id')) == correction['record_id']]
        need(len(matching) == 1 and matching[0].get('doi') == correction['doi'], 'PLAN_RECORD')
        manuscripts = matching[0].get('manuscripts')
        need(isinstance(manuscripts, list) and manuscripts, 'PLAN_MANUSCRIPTS')
        authorized = []
        for row in manuscripts:
            need(isinstance(row, dict), 'PLAN_MANUSCRIPT_ROW')
            authorized.append({'run_id': row.get('run_id'), 'member': row.get('archive_member'),
                               'filename': row.get('filename'), 'sha256': row.get('sha256'),
                               'md5': row.get('md5'), 'bytes': row.get('bytes')})
        # Already-visible special copies also belong here if they were absent
        # in saved admission. Exact source registration, not audit baseline,
        # defines originals; the plan's ADD marker never narrows human scope.
        projected = [{k: row[k] for k in access.COPY_FIELDS} for row in correction['copies']]
        need(len(authorized) == len(projected)
             and sorted(authorized, key=lambda row: row['run_id']) == sorted(projected, key=lambda row: row['run_id']),
             'EXACT_ALL_NOMINATED_ARCHIVE_PAPERS')
        for binding, raw in ((nominated, authority_raw), (authority['instruction'], instruction_raw),
                             (authority['provider_instruction'], provider_raw),
                             (authority['copy_plan'], plan_raw)):
            need(bound(self.root, binding) == raw, 'USER_AUTHORITY_SOURCE_RACE')
        return {'status': 'EXACT_USER_ACCESS_COPY_AUTHORITY_PASS', 'record_id': correction['record_id'],
                'doi': correction['doi'], 'instruction': deepcopy(authority['instruction']),
                'provider_instruction': deepcopy(authority['provider_instruction']),
                'copy_plan': deepcopy(authority['copy_plan']), 'certifies': False}

    def require_registration(self, root, binding, ledger=None, *, views=None, prior_chain_receipts=None):
        need(Path(root).resolve(strict=True) == self.root, 'CANONICAL_ROOT')
        registry, registry_raw = self._registry()
        registered, registered_raw = _object(self.root, binding)
        matches = [entry for entry in registry['entries'] if entry['registration'] == binding]
        if not matches:
            need(all(entry['record_id'] != registered.get('record_id') for entry in registry['entries']),
                 'NAMED_RECORD_DIFFERENT_REGISTRATION')
            if isinstance(prior_chain_receipts, dict) and set(prior_chain_receipts) == CHAIN_FIELDS:
                return self._plain_chain_registration(binding, ledger, views=views, chain=prior_chain_receipts,
                    registered=registered, registry_raw=registry_raw, registered_raw=registered_raw)
            result = registration.require_registration(self.root, binding, ledger,
                                                        views=views, prior_chain_receipts=prior_chain_receipts)
            need(bound(self.root, self.binding) == registry_raw and bound(self.root, binding) == registered_raw,
                 'UNNOMINATED_SOURCE_RACE')
            return result
        entry = matches[0]
        if entry['archive'] is None:
            need(prior_chain_receipts is None, 'NO_OVERLAPPING_NOMINATED_CHAIN_ONLY_OPERATION')
            return self._plain_chain_registration(binding, ledger, views=views,
                chain={k: entry['prior_chain'][k] for k in CHAIN_FIELDS}, registered=registered,
                registry_raw=registry_raw, registered_raw=registered_raw)
        # Original scientific source always consumes saved evidence first.
        admitted = registration.require_registration(self.root, binding, ledger, views=None)
        need(admitted['receipt']['record_id'] == entry['record_id'], 'NOMINATED_ADMITTED_IDENTITY')
        if views is None:
            need(self.owner_getter is not None, 'FRESH_OWNER_PAIR_REQUIRED')
            views = (self.owner_getter(entry['record_id'], CONTEXT['legacy_accept']),
                     self.owner_getter(entry['record_id'], CONTEXT['native_accept']))
        need(isinstance(views, (tuple, list)) and len(views) == 2
             and all(isinstance(v, dict) for v in views), 'ACTUAL_OWNER_PAIR')
        actual_legacy, actual_native = views
        need(str(actual_native.get('parent', {}).get('access', {}).get('owned_by', {}).get('user')) == CONTEXT['owner_id'],
             'ACTUAL_OWNER_ID')
        correction, correction_raw = _object(self.root, entry['access_correction'])
        need(correction.get('authority') == entry['user_authority'], 'EXACT_NOMINATED_AUTHORITY')
        manifest_binding = admitted['receipt']['digest_manifest']
        manifest_raw = bound(self.root, manifest_binding)
        archive_raw = bound(self.root, entry['archive'])
        expected_archive = [u for u in admitted['manifest']['uploads'] if u['filename'] == 'METHODS_NOTES.zip']
        need(len(expected_archive) == 1 and entry['archive']['sha256'] == expected_archive[0]['sha256'],
             'ADMITTED_ORIGINAL_ARCHIVE_HASH')
        import own_record_comparison as protected

        def authority_consumer(value):
            need(value == entry['user_authority'], 'AUTHORITY_SUBSTITUTION')
            return self._authority(value, correction)

        chain_audits = []
        chain_snapshots = []
        access_before = (admitted['public_legacy'], admitted['public_native'])
        access_actual = (actual_legacy, actual_native)
        nominated_chain = entry['prior_chain']
        if nominated_chain is not None:
            objects, sources = self._chain_inputs({k: nominated_chain[k] for k in CHAIN_FIELDS}, entry['record_id'])
            baseline = (objects['baseline_legacy']['response'], objects['baseline_native']['response'])
            chain_snapshots.extend(sources)
            if nominated_chain['stage'] == 'BEFORE_ACCESS':
                chain_audits.append(self._chain_pair(baseline, access_before, objects, nominated_chain))
                access_before = baseline
            else:
                # A persistent AFTER_ACCESS nomination validates access on the
                # actual pre-operation baseline, followed by the genuine chain.
                access_actual = baseline
                chain_audits.append(self._chain_pair((actual_legacy, actual_native), baseline, objects, nominated_chain))
        if prior_chain_receipts is not None:
            need(nominated_chain is None or nominated_chain['stage'] == 'BEFORE_ACCESS',
                 'NO_AMBIGUOUS_OVERLAPPING_AFTER_ACCESS_CHAINS')
            objects, sources = self._chain_inputs(prior_chain_receipts, entry['record_id'])
            baseline = (objects['baseline_legacy']['response'], objects['baseline_native']['response'])
            chain_snapshots.extend(sources)
            access_actual = baseline
            chain_audits.append(self._chain_pair((actual_legacy, actual_native), baseline, objects, prior_chain_receipts))
        checked = access.require_pair(access_actual[0], access_actual[1],
                                      access_before[0], access_before[1],
                                      receipt=correction, manifest_bytes=manifest_raw,
                                      archive_bytes=archive_raw, download=self.download,
                                      authority_consumer=authority_consumer,
                                      protected_projection=protected.prior_protected_projection)
        for source, raw in ((self.binding, registry_raw), (binding, registered_raw),
                            (entry['access_correction'], correction_raw),
                            (manifest_binding, manifest_raw), (entry['archive'], archive_raw)):
            need(bound(self.root, source) == raw, 'FINAL_SOURCE_RACE')
        for source, raw in chain_snapshots:
            need(bound(self.root, source) == raw, 'CHAIN_SOURCE_RACE')
        return {**admitted, 'public_legacy': deepcopy(actual_legacy), 'public_native': deepcopy(actual_native),
                'registered_public_views': {'legacy': deepcopy(admitted['public_legacy']),
                                            'native': deepcopy(admitted['public_native'])},
                'prior_processing_audit': {'route': 'EXACT_RECEIPT_BOUND_MANUSCRIPT_ACCESS_COPIES',
                                           'access_correction': checked,
                                           'correction_binding': deepcopy(entry['access_correction']),
                                           'registry_binding': deepcopy(self.binding),
                                           'genuine_chain_audits': chain_audits,
                                           'observation_context': deepcopy(self.observation_context)}}

    def registered_relation_template(self, binding, *, root, source_native, source_legacy):
        admitted = self.require_registration(root, binding, views=(source_legacy, source_native))
        need(admitted['public_native'] == source_native and admitted['public_legacy'] == source_legacy,
             'ACTUAL_REGISTERED_SOURCE_PAIR')
        receipt = admitted['receipt']
        rid = receipt['record_id']
        need(source_native.get('id') == rid and str(source_legacy.get('id')) == rid
             and source_native.get('is_published') is True and source_native.get('is_draft') is False
             and source_legacy.get('doi') == receipt['doi'], 'PUBLISHED_RELATION_SOURCE')
        need(source_legacy.get('metadata', {}).get('title') == registration.d.week_title(receipt['release_week']),
             'ADMITTED_SOURCE_WEEK')
        evidence, evidence_raw = _object(self.root, receipt['public_evidence'])
        relation, relation_raw = _object(self.root, evidence['relation_template'])
        template = relation.get('relation_type', relation)
        need(isinstance(template, dict) and set(template) == {'id', 'title'}
             and template['id'] == 'issupplementto' and isinstance(template['title'], dict)
             and template['title'].get('en') == 'Is supplement to', 'ORIGINAL_RELATION_VOCABULARY')
        present = [r['relation_type'] for r in source_native['metadata'].get('related_identifiers', [])
                   if isinstance(r, dict) and r.get('relation_type', {}).get('id') == 'issupplementto']
        need(all(value == template for value in present), 'RELATION_ENUM_DRIFT')
        need(bound(self.root, receipt['public_evidence']) == evidence_raw
             and bound(self.root, evidence['relation_template']) == relation_raw, 'RELATION_SOURCE_RACE')
        return deepcopy(template)

    def public_label_read_record(self, row, *, legacy):
        marker = row.get('methods_digest_registration')
        if marker is None:
            return legacy(row)
        need(isinstance(marker, dict) and set(marker) == {'tree_root', 'receipt'}, 'PUBLIC_LABEL_MARKER')
        need(Path(marker['tree_root']).resolve(strict=True) == self.root and self.owner_getter is not None,
             'PUBLIC_LABEL_OWNER_READER')
        pair = None

        def getter(rid, accept):
            nonlocal pair
            if pair is None:
                pair = (self.owner_getter(rid, CONTEXT['legacy_accept']),
                        self.owner_getter(rid, CONTEXT['native_accept']))
            need(isinstance(pair, (tuple, list)) and len(pair) == 2, 'PUBLIC_LABEL_OWNER_PAIR')
            body = pair[0] if accept == CONTEXT['legacy_accept'] else pair[1]
            need(accept in {CONTEXT['legacy_accept'], CONTEXT['native_accept']}, 'PUBLIC_LABEL_ACCEPT')
            return body, registration.d.digest(registration.d.raw_json(body))

        module = registration if registration.is_v3_binding(self.root, marker['receipt']) else registration._original_registrar()
        return module.public_label_read_record(row, legacy=legacy, getter=getter, consume=self.require_registration)
