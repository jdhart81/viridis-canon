"""Closed GAME_PLAN server-field readback rules; no network or write authority.

The caller supplies the planned public snapshot, including exact predicted
values for unlisted transitions such as is_draft/is_published. For a successor,
temporal_baseline must be the actual before-publish snapshot, not a prediction.
Same-operation response provenance is the transport caller's responsibility.
"""
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import zenodo_transport

from publication_preservation import (
    require_file_preservation, require_public_metadata,
)
from zenodo_transport import TransportHold


ALLOW_LIST = (
    'pids.oai', 'minted_doi_and_existing_concept',
    'custom_fields.legacy:communities', 'created_updated_revision_id',
    'versions_index_latest_parent', 'links_and_stats', 'file_entry_order',
    'revision_id', 'deletion_status', 'expires_at', 'swh', 'ui.is_draft',
    'ui_display_fields',
)


def _hold(reason):
    raise TransportHold('READBACK_MISMATCH_SERVER_MANAGED:' + reason)


def _json(value):
    def require_string_keys(item):
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                _hold('NON_JSON_OBJECT_KEY')
            for child in item.values():
                require_string_keys(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                require_string_keys(child)

    require_string_keys(value)
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError):
        _hold('NON_JSON_INPUT')


def _exact(left, right):
    return _json(left) == _json(right)


def _id(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        _hold('RECORD_ID_TYPE')
    result = str(value)
    if not result.isascii() or not result.isdecimal() or str(int(result)) != result or int(result) <= 0:
        _hold('RECORD_ID_VALUE')
    return result


def _host(value):
    if value not in ('zenodo.org', 'sandbox.zenodo.org'):
        _hold('HOST')
    return value


def _objects(actual, expected):
    if not isinstance(actual, dict) or not isinstance(expected, dict):
        _hold('RECORD_OBJECT_REQUIRED')
    _json(actual)
    _json(expected)


def require_publish_scope(*, host, record_id, own_publish_response,
                          same_operation_reservation_id):
    """A GET or another operation's response never proves the publish boundary."""
    host, record_id = _host(host), _id(record_id)
    if _id(same_operation_reservation_id) != record_id:
        _hold('PUBLISH_RESERVATION_ID_MISMATCH')
    receipt = own_publish_response
    if not isinstance(receipt, dict) or receipt.get('method') != 'POST':
        _hold('OWN_PUBLISH_POST_RECEIPT_REQUIRED')
    status = receipt.get('http_status')
    if type(status) is not int or status < 200 or status >= 300:
        _hold('OWN_PUBLISH_HTTP_SUCCESS_REQUIRED')
    if not isinstance(receipt.get('response_sha256'), str) or re.fullmatch(r'[0-9a-f]{64}', receipt['response_sha256']) is None:
        _hold('OWN_PUBLISH_RAW_RESPONSE_SHA256_REQUIRED')
    parsed = urlsplit(receipt.get('url', ''))
    allowed_paths = ('/api/records/' + record_id + '/draft/actions/publish',
                     '/api/deposit/depositions/' + record_id + '/actions/publish')
    if parsed.scheme != 'https' or parsed.netloc != host or parsed.path not in allowed_paths or parsed.query or parsed.fragment:
        _hold('OWN_PUBLISH_ENDPOINT_REQUIRED')
    response = receipt.get('response')
    if not isinstance(response, dict) or _id(response.get('id')) != record_id:
        _hold('OWN_PUBLISH_RESPONSE_ID_MISMATCH')
    return response


def transport_contract_sha256():
    """Hash of the reviewed synchronous Bearer-authenticated receipt producer."""
    return hashlib.sha256(Path(zenodo_transport.__file__).read_bytes()).hexdigest()


def require_revision_evidence(*, host, record_id, own_publish_response,
                              same_operation_reservation_id, revision_evidence):
    """Prove the first native GET from the producer's numbered saved receipts.

    Existing receipts have no timestamps or independent auth marker. Their
    sequence proves chronology under the reviewed ZenodoTransport contract:
    each request has a Bearer header and finishes saving its receipt before
    returning. Raw response hashes are the producer's saved hashes; parsed
    receipt JSON is not falsely presented as the original response bytes.
    """
    require_publish_scope(host=host, record_id=record_id,
        own_publish_response=own_publish_response,
        same_operation_reservation_id=same_operation_reservation_id)
    if not isinstance(revision_evidence, dict) or set(revision_evidence) != {
            'receipt_directory', 'publish_receipt_name', 'first_native_get_receipt_name', 'transport_contract_sha256'}:
        _hold('REVISION_EVIDENCE_INPUT_REQUIRED')
    if revision_evidence['transport_contract_sha256'] != transport_contract_sha256():
        _hold('AUTHENTICATED_TRANSPORT_CONTRACT_HASH_MISMATCH')
    directory_value = revision_evidence['receipt_directory']
    if not isinstance(directory_value, str) or not Path(directory_value).is_absolute():
        _hold('REVISION_RECEIPT_DIRECTORY_REQUIRED')
    directory = Path(directory_value)
    if not directory.is_dir():
        _hold('REVISION_RECEIPT_DIRECTORY_MISSING')
    names = [revision_evidence[key] for key in ('publish_receipt_name', 'first_native_get_receipt_name')]
    pattern = re.compile(r'([0-9]{3,})_(GET|POST|PUT|DELETE)\.json\Z')
    if any(not isinstance(name, str) or pattern.fullmatch(name) is None for name in names):
        _hold('REVISION_RECEIPT_NAME')
    numbered = {}
    for path in directory.iterdir():
        match = pattern.fullmatch(path.name)
        if match is None:
            continue
        sequence = int(match[1])
        if sequence <= 0 or match[1] != f'{sequence:03d}' or sequence in numbered:
            _hold('REVISION_RECEIPT_SEQUENCE_AMBIGUOUS')
        try:
            raw = path.read_bytes()
            receipt = json.loads(raw)
        except (OSError, ValueError):
            _hold('REVISION_RECEIPT_UNREADABLE')
        if not isinstance(receipt, dict) or receipt.get('method') != match[2]:
            _hold('REVISION_RECEIPT_METHOD_MISMATCH')
        numbered[sequence] = (path.name, receipt, hashlib.sha256(raw).hexdigest())
    if not numbered or set(numbered) != set(range(1, max(numbered) + 1)):
        _hold('REVISION_RECEIPT_SEQUENCE_INCOMPLETE')
    by_name = {value[0]: (sequence, *value[1:]) for sequence, value in numbered.items()}
    if any(name not in by_name for name in names):
        _hold('REVISION_RECEIPT_NOT_SAVED')
    publish_sequence, saved_publish, publish_file_hash = by_name[names[0]]
    get_sequence, first_get, get_file_hash = by_name[names[1]]
    if not _exact(saved_publish, own_publish_response):
        _hold('SAVED_OWN_PUBLISH_RECEIPT_CHANGED')
    if get_sequence <= publish_sequence:
        _hold('R0_GET_PRECEDES_OWN_PUBLISH')
    record_id = _id(record_id)
    endpoint = 'https://' + _host(host) + '/api/records/' + record_id
    candidates = [(sequence, receipt) for sequence, (_, receipt, _) in numbered.items()
        if sequence > publish_sequence and receipt.get('method') == 'GET'
        and receipt.get('url') == endpoint and receipt.get('accept') == 'application/vnd.inveniordm.v1+json']
    if not candidates or get_sequence != min(sequence for sequence, _ in candidates):
        _hold('R0_NOT_FIRST_NATIVE_GET_AFTER_OWN_PUBLISH')
    if (first_get.get('method') != 'GET' or first_get.get('url') != endpoint
            or first_get.get('accept') != 'application/vnd.inveniordm.v1+json'
            or first_get.get('environment') != host
            or first_get.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
            or type(first_get.get('http_status')) is not int or not 200 <= first_get['http_status'] < 300):
        _hold('FIRST_AUTHENTICATED_NATIVE_GET_REQUIRED')
    if (saved_publish.get('environment') != host
            or saved_publish.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'):
        _hold('SAVED_PUBLISH_PRODUCER_CONTRACT_MISMATCH')
    if not isinstance(first_get.get('response_sha256'), str) or re.fullmatch(r'[0-9a-f]{64}', first_get['response_sha256']) is None:
        _hold('FIRST_NATIVE_GET_RAW_RESPONSE_SHA256_REQUIRED')
    record = first_get.get('response')
    if not isinstance(record, dict) or _id(record.get('id')) != record_id:
        _hold('FIRST_NATIVE_GET_RECORD_ID_MISMATCH')
    r0 = _revision(record, 'FIRST_NATIVE_GET_R0')
    return {'r0': r0, 'first_native_record': deepcopy(record),
        'publish_receipt_file_sha256': publish_file_hash, 'native_get_receipt_file_sha256': get_file_hash,
        'publish_raw_response_sha256': saved_publish['response_sha256'],
        'native_get_raw_response_sha256': first_get['response_sha256'],
        'publish_sequence': publish_sequence, 'native_get_sequence': get_sequence,
        'chronology_evidence': 'Same-directory complete ZenodoTransport synchronous receipt sequence',
        'authentication_evidence': 'Reviewed ZenodoTransport Bearer-header contract; receipts have no independent auth marker',
        'transport_contract_sha256': revision_evidence['transport_contract_sha256']}


def own_representation_projection(actual, expected):
    """Normalize only absent/null pairs at the closed approved server paths.

    The caller must first prove own publish scope. This never changes non-null
    values, content fields, PID providers, files, or unlisted field names.
    """
    left, right = deepcopy(actual), deepcopy(expected)
    changes = []
    paths = [('pids', 'oai'), ('created',), ('updated',), ('revision_id',),
        ('deletion_status',), ('expires_at',), ('swh',), ('ui', 'is_draft'),
        ('versions', 'index'), ('versions', 'is_latest'), ('parent', 'id'),
        ('links',), ('stats',)]
    def pair_at(path):
        l, r = left, right
        for key in path[:-1]:
            if not isinstance(l.get(key), dict) or not isinstance(r.get(key), dict):
                return
            l, r = l[key], r[key]
        key = path[-1]
        if (key in l) != (key in r) and l.get(key) is None and r.get(key) is None:
            l.pop(key, None); r.pop(key, None); changes.append('.'.join(path))
    for path in paths:
        pair_at(path)
    def nullable_leaves(l, r, prefix):
        if not isinstance(l, dict) or not isinstance(r, dict):
            return
        for key in sorted(l.keys() | r.keys()):
            if (key in l) != (key in r) and l.get(key) is None and r.get(key) is None:
                l.pop(key, None); r.pop(key, None); changes.append(prefix + '.' + key)
            elif key in l and key in r:
                nullable_leaves(l[key], r[key], prefix + '.' + key)
    for group in ('links', 'stats'):
        nullable_leaves(left.get(group), right.get(group), group)
    return left, right, changes


def require_pids(actual, expected, *, host, record_id, new_version=False,
                 phase='PUBLISHED', own_publish_response=None,
                 same_operation_reservation_id=None):
    """Row 1: only a new own-ID OAI PID can be added; old PID bytes stay exact."""
    _objects(actual, expected)
    host, record_id = _host(host), _id(record_id)
    left, right = actual.get('pids'), expected.get('pids')
    if not isinstance(left, dict) or not isinstance(right, dict):
        _hold('PIDS_OBJECT_REQUIRED')
    normalized = deepcopy(left)
    if new_version and phase == 'PUBLISHED' and 'oai' in left:
        require_publish_scope(host=host, record_id=record_id,
            own_publish_response=own_publish_response,
            same_operation_reservation_id=same_operation_reservation_id)
        required = {'identifier': 'oai:zenodo.org:' + record_id, 'provider': 'oai'}
        if not _exact(left['oai'], required):
            _hold('OAI_HOST_OWN_ID_PROVIDER_OR_SHAPE')
        if 'oai' not in right:
            normalized.pop('oai')
    if not _exact(normalized, right):
        _hold('PREEXISTING_PID_CHANGED_OR_UNLISTED_PID')


def _response_doi(response, record_id):
    if not isinstance(response, dict) or _id(response.get('id')) != record_id:
        _hold('SAME_OPERATION_RESPONSE_RECORD_ID')
    values = []
    for value in (response.get('doi'), response.get('pids', {}).get('doi', {}).get('identifier'),
                  response.get('metadata', {}).get('prereserve_doi', {}).get('doi')):
        if value is not None:
            if not isinstance(value, str) or not value:
                _hold('SAME_OPERATION_DOI_SHAPE')
            values.append(value)
    if not values or len(set(values)) != 1:
        _hold('SAME_OPERATION_DOI_MISSING_OR_CONFLICTING')
    return values[0]


def require_minted_identifiers(actual, *, record_id, same_operation_response,
                               existing_concept_doi):
    """Row 2: consume the same response's minted DOI and the existing concept."""
    record_id = _id(record_id)
    if not isinstance(existing_concept_doi, str) or not existing_concept_doi:
        _hold('EXISTING_CONCEPT_DOI_REQUIRED')
    minted = _response_doi(same_operation_response, record_id)
    doi = actual.get('pids', {}).get('doi', {}).get('identifier')
    if doi != minted or ('doi' in actual and actual['doi'] != minted):
        _hold('MINTED_DOI_CHANGED')
    concepts = []
    for value in (actual.get('conceptdoi'),
                  actual.get('parent', {}).get('pids', {}).get('doi', {}).get('identifier')):
        if value is not None:
            concepts.append(value)
    if not concepts or any(value != existing_concept_doi for value in concepts):
        _hold('EXISTING_CONCEPT_DOI_CHANGED_OR_MISSING')
    returned_concept = same_operation_response.get('conceptdoi')
    if returned_concept is not None and returned_concept != existing_concept_doi:
        _hold('SAME_OPERATION_CONCEPT_DOI_CHANGED')


def require_community_mirror(actual, expected, *, existing_communities=None,
                             public_communities=None, mirror_proof=None):
    """Row 3: only the tested pure-existing-membership mirror may be added."""
    if ('custom_fields' in actual) != ('custom_fields' in expected):
        _hold('CUSTOM_FIELDS_PRESENCE_CHANGED')
    left, right = expected.get('custom_fields'), actual.get('custom_fields')
    if _exact(left, right):
        return
    if not isinstance(left, dict) or not isinstance(right, dict):
        _hold('CUSTOM_FIELDS_OBJECT_REQUIRED')
    if not isinstance(mirror_proof, dict) or mirror_proof.get('status') != 'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN' or mirror_proof.get('public_post_publish_exact_preservation') is not True:
        _hold('COMMUNITY_MIRROR_PROOF_REQUIRED')
    if not isinstance(existing_communities, list) or not existing_communities:
        _hold('EXISTING_COMMUNITIES_REQUIRED')
    ids = []
    for item in existing_communities:
        if not isinstance(item, dict) or set(item) != {'id'} or not isinstance(item['id'], str) or not item['id']:
            _hold('COMMUNITY_ID_SHAPE')
        ids.append(item['id'])
    if 'legacy:communities' in left:
        # The approved transformation is addition, never a preexisting edit.
        _hold('PREEXISTING_LEGACY_COMMUNITIES_CHANGED')
    projected = deepcopy(left)
    projected['legacy:communities'] = ids
    if not _exact(right, projected):
        _hold('COMMUNITY_MIRROR_OR_OTHER_CUSTOM_FIELD_CHANGED')
    if not _exact(public_communities, existing_communities):
        _hold('PUBLIC_COMMUNITIES_CHANGED_OR_UNAVAILABLE')


def _timestamp(value):
    if not isinstance(value, str):
        _hold('TIMESTAMP_TYPE')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        _hold('TIMESTAMP_VALUE')
    if result.tzinfo is None or result.utcoffset() is None:
        _hold('TIMESTAMP_TIMEZONE_REQUIRED')
    return result


def require_time(actual, expected, *, temporal_baseline=None):
    """Unamended row 4: timezone-aware nondecreasing timestamps only."""
    baseline = expected if temporal_baseline is None else temporal_baseline
    if not isinstance(baseline, dict):
        _hold('TEMPORAL_BASELINE_REQUIRED')
    for field in ('created', 'updated'):
        if field in actual or field in expected or field in baseline:
            if field not in actual or field not in baseline:
                _hold('TIMESTAMP_BASELINE_MISSING:' + field)
            if _timestamp(actual[field]) < _timestamp(baseline[field]):
                _hold('TIMESTAMP_DECREASE:' + field)
    if 'created' in actual and 'updated' in actual:
        if _timestamp(actual['updated']) < _timestamp(actual['created']):
            _hold('UPDATED_BEFORE_CREATED')


def _revision(record, name, *, minimum=1):
    value = record.get('revision_id') if isinstance(record, dict) else None
    if type(value) is not int or value < minimum:
        _hold(name + ('_POSITIVE_INTEGER_REQUIRED' if minimum == 1 else '_NONNEGATIVE_INTEGER_REQUIRED'))
    return value


def require_revision(actual, expected, *, phase, operation, host, record_id,
                     temporal_baseline=None, own_publish_response=None,
                     same_operation_reservation_id=None,
                     previous_public_readback=None, revision_evidence=None):
    """Draft monotonicity, an evidenced own publish reset, and public monotonicity."""
    baseline = expected if temporal_baseline is None else temporal_baseline
    if not isinstance(baseline, dict):
        _hold('REVISION_BASELINE_REQUIRED')
    current = _revision(actual, 'CURRENT_REVISION', minimum=1 if phase == 'PUBLISHED' and operation == 'NEW_VERSION' else 0)
    if operation == 'PRIOR_VERSION':
        previous = _revision(expected, 'PRIOR_REVISION', minimum=0)
        if current < previous:
            _hold('PRIOR_REVISION_DECREASE')
        for field in ('metadata', 'custom_fields'):
            if (field in actual) != (field in expected) or not _exact(actual.get(field), expected.get(field)):
                _hold('PRIOR_REVISION_CHANGED_WITH_CONTENT:' + field)
        if current != previous:
            if expected.get('versions', {}).get('is_latest') is not True or actual.get('versions', {}).get('is_latest') is not False:
                _hold('PRIOR_REVISION_CHANGE_WITHOUT_LATEST_FLIP')
            # The approved order exemption still requires every entry byte-exact.
            require_file_entries(actual, expected)
        return {'phase': 'PRIOR_VERSION', 'revision': current}
    if phase == 'DRAFT':
        previous = _revision(baseline, 'DRAFT_REVISION', minimum=0)
        if current < previous:
            _hold('DRAFT_REVISION_DECREASE')
        return {'phase': 'DRAFT', 'revision': current}
    if phase != 'PUBLISHED':
        _hold('REVISION_PHASE')
    if operation != 'NEW_VERSION':
        previous = _revision(baseline, 'PREEXISTING_REVISION', minimum=0)
        if current < previous:
            _hold('PREEXISTING_REVISION_DECREASE')
        return {'phase': 'PREEXISTING_MONOTONIC', 'revision': current}
    evidence = require_revision_evidence(host=host, record_id=record_id,
        own_publish_response=own_publish_response,
        same_operation_reservation_id=same_operation_reservation_id,
        revision_evidence=revision_evidence)
    r0 = evidence.pop('r0'); evidence.pop('first_native_record')
    if current < r0:
        _hold('PUBLIC_REVISION_BELOW_OWN_PUBLISH_R0')
    if previous_public_readback is not None:
        if not isinstance(previous_public_readback, dict) or _id(previous_public_readback.get('id')) != _id(record_id):
            _hold('PREVIOUS_PUBLIC_READBACK_ID')
        previous = _revision(previous_public_readback, 'PREVIOUS_PUBLIC_REVISION')
        if previous < r0 or current < previous:
            _hold('PUBLIC_REVISION_DECREASE')
    return {'phase': 'PUBLISHED', 'first_authenticated_native_r0': r0, 'revision': current, 'evidence': evidence}


def _same_field(actual, baseline, field):
    return (field in actual) == (field in baseline) and _exact(actual.get(field), baseline.get(field))


def require_publish_field(actual, expected, *, field, operation, phase, host,
                          record_id, temporal_baseline=None,
                          own_publish_response=None,
                          same_operation_reservation_id=None,
                          previous_public_readback=None,
                          own_operation_record_id=None):
    """Only the four specifically named own-publish field transitions normalize."""
    baseline = expected if temporal_baseline is None else temporal_baseline
    if not isinstance(baseline, dict):
        _hold('PUBLISH_FIELD_BASELINE_REQUIRED')
    own = operation == 'NEW_VERSION' and phase == 'PUBLISHED'
    if field == 'expires_at' and operation == 'NEW_VERSION' and phase == 'DRAFT':
        if field not in actual or actual[field] is None or field not in baseline or baseline[field] is None:
            _hold('OWN_DRAFT_EXPIRES_AT_PRESENT_NONNULL_REQUIRED')
    if field == 'ui.is_draft':
        if own_operation_record_id is not None and not own and operation != 'PRIOR_VERSION':
            _require_own_ui_scope(actual, expected, record_id, own_operation_record_id)
            return _require_own_ui_flag(actual, phase)
        left, right = actual.get('ui'), baseline.get('ui')
        if not isinstance(left, dict) or not isinstance(right, dict) or 'is_draft' not in left or 'is_draft' not in right:
            if _same_field(actual, baseline, 'ui'):
                return
            _hold('UI_DRAFT_FLAG_INPUT_REQUIRED')
        current, previous = left['is_draft'], right['is_draft']
        if type(current) is not bool or type(previous) is not bool or current is True and previous is False:
            _hold('UI_DRAFT_FLAG_INVALID_OR_REOPENED')
        if own:
            require_publish_scope(host=host, record_id=record_id,
                own_publish_response=own_publish_response,
                same_operation_reservation_id=same_operation_reservation_id)
            if previous is not True or current is not False:
                _hold('UI_OWN_PUBLISH_DRAFT_FLAG_NOT_TRUE_TO_FALSE')
        elif current is not previous:
            _hold('UI_DRAFT_FLAG_CHANGED_ON_PREEXISTING_RECORD')
        return
    if not own:
        if not _same_field(actual, baseline, field):
            _hold(field.upper() + '_CHANGED_ON_PREEXISTING_RECORD')
        return
    require_publish_scope(host=host, record_id=record_id,
        own_publish_response=own_publish_response,
        same_operation_reservation_id=same_operation_reservation_id)
    if field == 'deletion_status':
        if field not in baseline:
            if field not in actual or not _exact(actual[field], {'is_deleted': False, 'status': 'P'}):
                _hold('OWN_DELETION_STATUS_EXACT_P_REQUIRED')
        elif not _same_field(actual, baseline, field):
            _hold('PREEXISTING_DELETION_STATUS_CHANGED')
    elif field == 'expires_at':
        if field not in baseline or baseline[field] is None:
            _hold('OWN_DRAFT_EXPIRES_AT_PRESENT_NONNULL_REQUIRED')
        if field in actual and actual[field] is not None:
            _hold('OWN_PUBLISHED_EXPIRES_AT_ABSENT_OR_NULL_REQUIRED')
    elif field == 'swh':
        if previous_public_readback is None:
            if field not in baseline:
                if field not in actual or not _exact(actual[field], {}):
                    _hold('INITIAL_OWN_SWH_EMPTY_OBJECT_REQUIRED')
            elif not _same_field(actual, baseline, field):
                _hold('PREEXISTING_SWH_CHANGED')
        else:
            if not isinstance(previous_public_readback, dict) or _id(previous_public_readback.get('id')) != _id(record_id):
                _hold('PREVIOUS_SWH_PUBLIC_READBACK_ID')
            if field not in previous_public_readback or not isinstance(previous_public_readback[field], dict) or field not in actual or not isinstance(actual[field], dict):
                _hold('LATER_SWH_OBJECT_REQUIRED')
            if actual[field]:
                return {'ignored_for_content_comparison': True, 'logged_value': deepcopy(actual[field])}
    else:
        _hold('UNLISTED_PUBLISH_FIELD')


_CHAIN_FIELDS = ('index', 'is_latest', 'is_latest_draft')
_CHAIN_KEYS = {
    'boundary', 'prior_record_id', 'successor_record_id', 'chain_parent_id',
    'prior_before_create', 'prior_actual', 'successor_actual', 'successor_expected',
    'creation_evidence', 'operation_evidence', 'successor_before_boundary',
    'successor_absence_evidence',
}


def _saved_chain_receipt(evidence, *, host, method, endpoint, success=True):
    """Require immutable saved producer evidence, never an invented response."""
    if not isinstance(evidence, dict) or set(evidence) != {
            'receipt_path', 'receipt_sha256', 'transport_contract_sha256'}:
        _hold('CHAIN_SAVED_RECEIPT_EVIDENCE_REQUIRED')
    if evidence['transport_contract_sha256'] != transport_contract_sha256():
        _hold('CHAIN_TRANSPORT_CONTRACT_HASH_MISMATCH')
    value = evidence['receipt_path']
    if not isinstance(value, str) or not Path(value).is_absolute():
        _hold('CHAIN_RECEIPT_ABSOLUTE_PATH_REQUIRED')
    path = Path(value)
    if path.is_symlink() or not path.is_file():
        _hold('CHAIN_RECEIPT_REGULAR_SAVED_FILE_REQUIRED')
    try:
        raw = path.read_bytes()
        receipt = json.loads(raw)
    except (OSError, ValueError):
        _hold('CHAIN_RECEIPT_UNREADABLE')
    digest = hashlib.sha256(raw).hexdigest()
    if evidence['receipt_sha256'] != digest:
        _hold('CHAIN_RECEIPT_FILE_SHA256_MISMATCH')
    if not isinstance(receipt, dict) or receipt.get('method') != method or receipt.get('url') not in ((endpoint,) if isinstance(endpoint, str) else endpoint) or receipt.get('environment') != host:
        _hold('CHAIN_RECEIPT_OPERATION_OR_HOST_MISMATCH')
    status = receipt.get('http_status')
    if success:
        if type(status) is not int or not 200 <= status < 300 or receipt.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE':
            _hold('CHAIN_OWN_OPERATION_HTTP_SUCCESS_REQUIRED')
        for field in ('request_body_sha256', 'response_sha256'):
            if not isinstance(receipt.get(field), str) or re.fullmatch(r'[0-9a-f]{64}', receipt[field]) is None:
                _hold('CHAIN_OWN_OPERATION_' + field.upper() + '_REQUIRED')
        if not isinstance(receipt.get('response'), dict):
            _hold('CHAIN_OWN_OPERATION_RESPONSE_REQUIRED')
    elif (type(status) is not int or status != 404
            or receipt.get('accept') != 'application/vnd.inveniordm.v1+json'
            or receipt.get('status') != 'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'
            or receipt.get('error_type') != 'HTTPError'):
        _hold('CHAIN_AUTHENTICATED_SUCCESSOR_404_REQUIRED')
    return receipt, {'receipt_path': str(path), 'receipt_file_sha256': digest,
        'raw_response_sha256': receipt.get('response_sha256'),
        'request_body_sha256': receipt.get('request_body_sha256'),
        'transport_contract_sha256': evidence['transport_contract_sha256']}


def _chain_response_identity(receipt, record_id, parent_id):
    response = receipt.get('response')
    if not isinstance(response, dict) or _id(response.get('id')) != record_id:
        _hold('CHAIN_OPERATION_RESPONSE_ID_MISMATCH')
    parents = [response.get('conceptrecid')]
    if isinstance(response.get('parent'), dict):
        parents.append(response['parent'].get('id'))
    for value in parents:
        if value is not None and _id(value) != parent_id:
            _hold('CHAIN_OPERATION_RESPONSE_PARENT_MISMATCH')


def _chain_record(record, record_id, parent_id, *, draft=None):
    if not isinstance(record, dict) or _id(record.get('id')) != record_id:
        _hold('CHAIN_RECORD_ID_MISMATCH')
    if not isinstance(record.get('parent'), dict) or _id(record['parent'].get('id')) != parent_id:
        _hold('CHAIN_PARENT_ID_MISMATCH')
    if not isinstance(record.get('versions'), dict):
        _hold('CHAIN_VERSIONS_OBJECT_REQUIRED')
    if draft is not None:
        if record.get('is_draft') is not draft or record.get('is_published') is not (not draft):
            _hold('CHAIN_RECORD_DRAFT_PUBLISHED_BOUNDARY')
    _json(record)
    return record['versions']


def _chain_index(versions, name):
    value = versions.get('index')
    if type(value) is not int or value < 0:
        _hold('CHAIN_' + name + '_INDEX_INTEGER_REQUIRED')
    return value


def _chain_flags(versions, latest, latest_draft, *, own_published=False):
    if versions.get('is_latest') is not latest:
        _hold('CHAIN_IS_LATEST_WRONG_DIRECTION_OR_BOUNDARY')
    if own_published and ('is_latest_draft' not in versions or versions['is_latest_draft'] is None):
        return {'path': 'versions.is_latest_draft', 'present': 'is_latest_draft' in versions,
                'value': deepcopy(versions.get('is_latest_draft')), 'representation': 'OWN_PUBLISHED_ABSENT_OR_NULL'}
    if versions.get('is_latest_draft') is not latest_draft:
        _hold('CHAIN_IS_LATEST_DRAFT_WRONG_DIRECTION_OR_BOUNDARY')
    return None


def _chain_unknown_versions(actual, expected):
    left = {key: value for key, value in actual.items() if key not in _CHAIN_FIELDS}
    right = {key: value for key, value in expected.items() if key not in _CHAIN_FIELDS}
    if not _exact(left, right):
        _hold('CHAIN_UNLISTED_VERSIONS_FIELD_CHANGED')


def _require_prior_chain_sources(actual, expected):
    # Prior UI/content never inherits the own successor rendering exceptions.
    for field in ('metadata', 'custom_fields', 'pids', 'access', 'media_files', 'ui', 'parent'):
        if not _same_field(actual, expected, field):
            _hold('CHAIN_PRIOR_PROTECTED_SOURCE_CHANGED:' + field)
    require_file_entries(actual, expected)


def require_version_chain_state(*, host, boundary, prior_record_id,
        successor_record_id, chain_parent_id, prior_before_create, prior_actual,
        successor_actual, successor_expected, creation_evidence,
        operation_evidence=None, successor_before_boundary=None,
        successor_absence_evidence=None):
    """Receipt-bound paired state only; no operation or publication authority.

    A complete successor readback audit remains mandatory. The separate paired
    audit also closes all prior-record fields against the pre-create snapshot.
    """
    host = _host(host); prior_id = _id(prior_record_id); parent_id = _id(chain_parent_id)
    if boundary not in ('CREATE', 'PUBLISH', 'DISCARD', 'EDIT'):
        _hold('CHAIN_BOUNDARY')
    initial = _chain_record(prior_before_create, prior_id, parent_id, draft=False)
    prior = _chain_record(prior_actual, prior_id, parent_id, draft=False)
    index = _chain_index(initial, 'PRIOR')
    if _chain_index(prior, 'PRIOR_ACTUAL') != index:
        _hold('CHAIN_PRIOR_INDEX_CHANGED')
    _chain_unknown_versions(prior, initial)
    _require_prior_chain_sources(prior_actual, prior_before_create)
    evidence_log = {}; representation_log = []
    if boundary == 'EDIT':
        if any(value is not None for value in (successor_record_id, successor_actual,
                successor_expected, creation_evidence, successor_before_boundary,
                successor_absence_evidence)):
            _hold('CHAIN_EDIT_MUST_HAVE_NO_SUCCESSOR')
        receipt, evidence_log['operation'] = _saved_chain_receipt(operation_evidence,
            host=host, method='POST', endpoint='https://' + host + '/api/deposit/depositions/' + prior_id + '/actions/edit')
        _chain_response_identity(receipt, prior_id, parent_id)
        if not _exact(prior, initial):
            _hold('CHAIN_EDIT_VERSIONS_CHANGED')
    else:
        successor_id = _id(successor_record_id)
        if successor_id == prior_id or successor_id == parent_id:
            _hold('CHAIN_DISTINCT_PRIOR_SUCCESSOR_REQUIRED')
        creation, evidence_log['creation'] = _saved_chain_receipt(creation_evidence,
            host=host, method='POST', endpoint='https://' + host + '/api/deposit/depositions/' + prior_id + '/actions/newversion')
        response = creation['response']
        if _id(response.get('id')) != successor_id:
            _hold('CHAIN_CREATION_SUCCESSOR_ID_MISMATCH')
        response_parent = response.get('conceptrecid')
        native_parent = response.get('parent', {}).get('id') if isinstance(response.get('parent'), dict) else None
        if response_parent is None and native_parent is None:
            _hold('CHAIN_CREATION_PARENT_ID_REQUIRED')
        if any(_id(value) != parent_id for value in (response_parent, native_parent) if value is not None):
            _hold('CHAIN_CREATION_PARENT_ID_MISMATCH')
        if response.get('submitted') is not False or response.get('state') != 'unsubmitted':
            _hold('CHAIN_CREATION_UNPUBLISHED_SUCCESSOR_REQUIRED')
        _chain_flags(initial, True, True)
        if boundary in ('CREATE', 'PUBLISH'):
            child = _chain_record(successor_actual, successor_id, parent_id, draft=boundary == 'CREATE')
            child_expected = _chain_record(successor_expected, successor_id, parent_id)
            _chain_unknown_versions(child, child_expected)
            if boundary == 'CREATE':
                if any(value is not None for value in (operation_evidence, successor_absence_evidence, successor_before_boundary)):
                    _hold('CHAIN_CREATE_UNEXPECTED_BOUNDARY_EVIDENCE')
                _chain_flags(prior, True, False); _chain_flags(child, False, True)
                if 'index' not in child or child['index'] is None:
                    representation_log.append({'path': 'versions.index', 'present': 'index' in child,
                        'value': deepcopy(child.get('index')), 'representation': 'OWN_DRAFT_ABSENT_OR_NULL'})
                elif _chain_index(child, 'SUCCESSOR') != index + 1:
                    _hold('CHAIN_SUCCESSOR_INDEX_GAP_OR_REUSE')
            else:
                if successor_absence_evidence is not None:
                    _hold('CHAIN_PUBLISH_UNEXPECTED_ABSENCE_EVIDENCE')
                before = _chain_record(successor_before_boundary, successor_id, parent_id, draft=True)
                _chain_flags(before, False, True)
                if before.get('index') is not None and _chain_index(before, 'SUCCESSOR_BEFORE_PUBLISH') != index + 1:
                    _hold('CHAIN_BEFORE_PUBLISH_INDEX_GAP_OR_REUSE')
                published, evidence_log['operation'] = _saved_chain_receipt(operation_evidence,
                    host=host, method='POST', endpoint=('https://' + host + '/api/deposit/depositions/' + successor_id + '/actions/publish',
                              'https://' + host + '/api/records/' + successor_id + '/draft/actions/publish'))
                _chain_response_identity(published, successor_id, parent_id)
                _chain_flags(prior, False, False)
                rendered = _chain_flags(child, True, True, own_published=True)
                if rendered is not None: representation_log.append(rendered)
                if _chain_index(child, 'PUBLISHED_SUCCESSOR') != index + 1:
                    _hold('CHAIN_SUCCESSOR_INDEX_GAP_OR_REUSE')
        else:
            if successor_actual is not None or successor_expected is not None:
                _hold('CHAIN_DISCARDED_SUCCESSOR_MUST_BE_GONE')
            before = _chain_record(successor_before_boundary, successor_id, parent_id, draft=True)
            _chain_flags(before, False, True)
            if before.get('index') is not None and _chain_index(before, 'SUCCESSOR_BEFORE_DISCARD') != index + 1:
                _hold('CHAIN_BEFORE_DISCARD_INDEX_GAP_OR_REUSE')
            discard, evidence_log['operation'] = _saved_chain_receipt(operation_evidence,
                host=host, method='POST', endpoint='https://' + host + '/api/deposit/depositions/' + successor_id + '/actions/discard')
            _chain_response_identity(discard, successor_id, parent_id)
            gone, evidence_log['successor_absence'] = _saved_chain_receipt(successor_absence_evidence,
                host=host, method='GET', endpoint='https://' + host + '/api/records/' + successor_id + '/draft', success=False)
            operation_path = Path(operation_evidence['receipt_path'])
            gone_path = Path(successor_absence_evidence['receipt_path'])
            pattern = re.compile(r'([0-9]{3,})_(POST|GET)\.json\Z')
            first, second = pattern.fullmatch(operation_path.name), pattern.fullmatch(gone_path.name)
            if (operation_path.parent != gone_path.parent or first is None or second is None
                    or first[2] != 'POST' or second[2] != 'GET' or int(second[1]) <= int(first[1])):
                _hold('CHAIN_404_MUST_FOLLOW_OWN_DISCARD')
            sequences = set()
            for path in operation_path.parent.iterdir():
                match = re.fullmatch(r'([0-9]{3,})_(GET|POST|PUT|DELETE)\.json', path.name)
                if match is None or int(match[1]) > int(second[1]):
                    continue
                sequence = int(match[1])
                if sequence <= 0 or match[1] != f'{sequence:03d}' or sequence in sequences:
                    _hold('CHAIN_DISCARD_RECEIPT_SEQUENCE_AMBIGUOUS')
                sequences.add(sequence)
            if sequences != set(range(1, int(second[1]) + 1)):
                _hold('CHAIN_DISCARD_RECEIPT_SEQUENCE_INCOMPLETE')
            if not _exact(prior, initial):
                _hold('CHAIN_DISCARD_PRIOR_NOT_RESTORED')
    return {'boundary': boundary, 'prior_record_id': prior_id,
        'successor_record_id': None if boundary == 'EDIT' else successor_id,
        'chain_parent_id': parent_id, 'evidence': evidence_log,
        'prior_versions_before': deepcopy(initial), 'prior_versions_after': deepcopy(prior),
        'successor_versions_after': None if boundary in ('DISCARD', 'EDIT') else deepcopy(child),
        'representation_log': representation_log,
        'prior_diff_appendix': _full_differences(prior, initial, 'versions'),
        'successor_content_comparison_required': boundary in ('CREATE', 'PUBLISH')}


def require_versions(actual, expected, *, operation, previous_latest_index=None,
                     chain_parent_id=None, phase='PUBLISHED', host=None,
                     version_chain_context=None, own_publish_response=None):
    """Only named, receipt-bound paired transitions may change versions.*."""
    if version_chain_context is not None:
        if not isinstance(version_chain_context, dict) or set(version_chain_context) - _CHAIN_KEYS:
            _hold('CHAIN_CONTEXT_UNKNOWN_OR_INVALID_KEY')
        detail = require_version_chain_state(host=host, **version_chain_context)
        boundary = version_chain_context['boundary']
        current_id = _id(actual.get('id'))
        if current_id == detail['prior_record_id']:
            if operation not in ('PRIOR_VERSION', 'AMENDMENT') or not _exact(actual, version_chain_context['prior_actual']) or not _exact(expected, version_chain_context['prior_before_create']):
                _hold('CHAIN_PRIOR_READBACK_OR_BASELINE_MISMATCH')
            if operation == 'AMENDMENT' and boundary != 'EDIT':
                _hold('CHAIN_AMENDMENT_CANNOT_USE_SUCCESSOR_TRANSITION')
        elif current_id == detail['successor_record_id']:
            if operation != 'NEW_VERSION' or not _exact(actual, version_chain_context['successor_actual']) or not _exact(expected, version_chain_context['successor_expected']):
                _hold('CHAIN_SUCCESSOR_READBACK_OR_BASELINE_MISMATCH')
            if (boundary == 'CREATE' and phase != 'DRAFT') or (boundary == 'PUBLISH' and phase != 'PUBLISHED') or boundary not in ('CREATE', 'PUBLISH'):
                _hold('CHAIN_SUCCESSOR_PHASE_MISMATCH')
            if boundary == 'PUBLISH':
                saved, _ = _saved_chain_receipt(version_chain_context['operation_evidence'],
                    host=host, method='POST', endpoint=('https://' + _host(host) + '/api/deposit/depositions/' + current_id + '/actions/publish',
                              'https://' + _host(host) + '/api/records/' + current_id + '/draft/actions/publish'))
                if not _exact(saved, own_publish_response):
                    _hold('CHAIN_PUBLISH_AND_R0_RECEIPTS_DIFFER')
        else:
            _hold('CHAIN_CONTEXT_UNRELATED_RECORD')
        if chain_parent_id is not None and _id(chain_parent_id) != detail['chain_parent_id']:
            _hold('CHAIN_CALLER_PARENT_MISMATCH')
        return detail
    if operation == 'AMENDMENT' or phase == 'DRAFT' or operation == 'PRIOR_VERSION':
        if not _same_field(actual, expected, 'versions') or not _same_field(actual, expected, 'parent'):
            _hold('VERSION_TRANSITION_MATCHING_OWN_CHAIN_RECEIPT_REQUIRED')
        return
    versions = actual.get('versions'); old_versions = expected.get('versions')
    if not isinstance(versions, dict) or not isinstance(old_versions, dict):
        _hold('VERSIONS_OBJECT_REQUIRED')
    if type(versions.get('index')) is not int or type(versions.get('is_latest')) is not bool:
        _hold('VERSIONS_INDEX_OR_LATEST_TYPE')
    if operation != 'NEW_VERSION' or type(previous_latest_index) is not int or previous_latest_index < 0:
        _hold('PREVIOUS_LATEST_INDEX_REQUIRED')
    if previous_latest_index > 0:
        _hold('EXISTING_CHAIN_PUBLISH_PAIRED_RECEIPT_CONTEXT_REQUIRED')
    if versions['index'] != previous_latest_index + 1 or versions['is_latest'] is not True:
        _hold('NEW_VERSION_INDEX_OR_LATEST')
    require_publish_scope(host=host, record_id=actual.get('id'),
        own_publish_response=own_publish_response,
        same_operation_reservation_id=actual.get('id'))
    if not isinstance(actual.get('parent'), dict) or not isinstance(expected.get('parent'), dict):
        _hold('PARENT_OBJECT_REQUIRED')
    parent_id = _id(chain_parent_id)
    if _id(actual['parent'].get('id')) != parent_id or _id(expected['parent'].get('id')) != parent_id:
        _hold('CHAIN_PARENT_CHANGED')


def audit_version_chain(*, host, **version_chain_context):
    """Audit both version states and the entire prior record; performs no I/O writes."""
    report = {'status': 'HOLD', 'acceptance_authority': False, 'checks': {}, 'reasons': []}
    try:
        if set(version_chain_context) - _CHAIN_KEYS:
            _hold('CHAIN_CONTEXT_UNKNOWN_KEY')
        detail = require_version_chain_state(host=host, **version_chain_context)
        report['checks']['version_chain_state'] = {'status': 'PASS', 'detail': detail}
        prior = audit_readback(version_chain_context['prior_actual'], version_chain_context['prior_before_create'],
            host=host, record_id=version_chain_context['prior_record_id'], operation='PRIOR_VERSION',
            chain_parent_id=version_chain_context['chain_parent_id'], version_chain_context=version_chain_context)
        report['checks']['prior_closed_readback'] = prior
        if prior['status'] != 'SERVER_MANAGED_READBACK_PASS':
            report['reasons'].append({'rule': 'prior_closed_readback', 'reason': 'Full prior readback HOLD',
                'detail': prior['reasons']})
        else:
            report['status'] = 'VERSION_CHAIN_STATE_PASS'
    except Exception as exc:
        report['checks']['version_chain_state'] = {'status': 'HOLD', 'reason': str(exc)}
        report['reasons'].append({'rule': 'version_chain_state', 'reason': str(exc)})
    return report


def _own_url(value, record_id, host, own_doi):
    if isinstance(value, dict):
        if not value or any(not isinstance(key, str) for key in value):
            _hold('LINK_URL_MAP_SHAPE')
        for child in value.values():
            _own_url(child, record_id, host, own_doi)
        return
    if not isinstance(value, str):
        _hold('LINK_NOT_URL')
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        _hold('LINK_PORT')
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or port not in (None, 443):
        _hold('LINK_URL_SHAPE')
    if parsed.hostname != host:
        resolvers = ('doi.org', 'dx.doi.org') if host == 'zenodo.org' else ('handle.test.datacite.org',)
        if parsed.hostname not in resolvers or not isinstance(own_doi, str) or unquote(parsed.path).lstrip('/') != own_doi or parsed.query or parsed.fragment:
            _hold('LINK_NOT_OWN_HOST_OR_OWN_DOI_RESOLVER')
        return
    tokens = [unquote(part) for part in parsed.path.split('/') if part]
    iiif = re.compile(r'(?:record|draft):' + re.escape(record_id) + r'(?::[^/:]+)?\Z')
    if not any(part == record_id or part == 'zenodo.' + record_id or iiif.fullmatch(part) for part in tokens):
        _hold('LINK_NOT_THIS_RECORD_ID')


def _counters(value):
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            _hold('STATS_KEY_TYPE')
        for child in value.values():
            _counters(child)
    elif type(value) is int:
        if value < 0:
            _hold('STATS_NEGATIVE_COUNTER')
    elif type(value) is float:
        if not math.isfinite(value) or value < 0 or not value.is_integer():
            _hold('STATS_NOT_COUNTER')
    else:
        _hold('STATS_NOT_COUNTER')


_PREVIEW_FILE_LINKS = frozenset({'iiif_api', 'iiif_base', 'iiif_canvas', 'iiif_info', 'container'})
_PREVIEW_CONTEXT_KEYS = frozenset({'own_record_id', 'approved_inventory_evidence', 'approved_removal_inventory_evidence',
    'lineage_evidence', 'source_readback_evidence', 'delete_evidence',
    'upload_evidence', 'publish_evidence'})


def _preview_key(value):
    if (not isinstance(value, str) or not value or value in ('.', '..')
            or '/' in value or '\\' in value or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        _hold('PREVIEW_INVALID_FILE_KEY')
    return value


def _preview_inventory(evidence, *, removals=False):
    if not isinstance(evidence, dict) or set(evidence) != {'path', 'sha256'}:
        _hold('PREVIEW_APPROVED_INVENTORY_EVIDENCE_REQUIRED')
    value = evidence['path']
    if not isinstance(value, str) or not Path(value).is_absolute():
        _hold('PREVIEW_INVENTORY_ABSOLUTE_PATH_REQUIRED')
    path = Path(value)
    if path.is_symlink() or not path.is_file():
        _hold('PREVIEW_INVENTORY_SAVED_FILE_REQUIRED')
    try:
        raw = path.read_bytes(); document = json.loads(raw)
    except (OSError, ValueError):
        _hold('PREVIEW_INVENTORY_UNREADABLE')
    if evidence['sha256'] != hashlib.sha256(raw).hexdigest():
        _hold('PREVIEW_INVENTORY_HASH_MISMATCH')
    values = document.get('drop' if removals else 'files') if isinstance(document, dict) else document
    if not isinstance(values, list) or not values:
        _hold('PREVIEW_APPROVED_MAIN_INVENTORY_REQUIRED')
    entries = {}
    for row in values:
        if not isinstance(row, dict): _hold('PREVIEW_APPROVED_ENTRY_TYPE')
        names = [row[key] for key in ('name', 'filename', 'key') if key in row]
        if not names or any(not _exact(name, names[0]) for name in names):
            _hold('PREVIEW_APPROVED_FILE_KEY_CONFLICT')
        name = _preview_key(names[0])
        if name in entries: _hold('PREVIEW_DUPLICATE_APPROVED_FILE_KEY')
        if type(row.get('size')) is not int or row['size'] < 0:
            _hold('PREVIEW_APPROVED_FILE_SIZE')
        checksums = [('md5:' + row['checksum'] if removals and isinstance(row['checksum'], str) and not row['checksum'].startswith('md5:') else row['checksum'])] if 'checksum' in row else []
        if 'md5' in row: checksums.append('md5:' + str(row['md5']))
        if not checksums or any(checksum != checksums[0] for checksum in checksums) or not isinstance(checksums[0], str) or re.fullmatch(r'md5:[0-9a-f]{32}', checksums[0]) is None:
            _hold('PREVIEW_APPROVED_CHECKSUM')
        if 'id' in row and (not isinstance(row['id'], str) or not row['id']):
            _hold('PREVIEW_APPROVED_SOURCE_ID')
        if 'sha256' in row and (not isinstance(row['sha256'], str) or re.fullmatch(r'[0-9a-f]{64}', row['sha256']) is None):
            _hold('PREVIEW_APPROVED_SOURCE_SHA256')
        if 'path' in row and (not isinstance(row['path'], str) or not Path(row['path']).is_absolute()):
            _hold('PREVIEW_APPROVED_LOCAL_PATH')
        if removals:
            original = row.get('original_entry')
            if (not isinstance(original, dict) or original.get('filename') != name
                    or original.get('filesize') != row['size']
                    or 'md5:' + str(original.get('checksum')) != checksums[0]
                    or not isinstance(row.get('file_id'), str) or not row['file_id']
                    or row['file_id'] != original.get('id')):
                _hold('PREVIEW_APPROVED_REMOVAL_ORIGINAL_ENTRY_MISMATCH')
            row = dict(row, id=row['file_id'])
        entries[name] = {'key': name, 'size': row['size'], 'checksum': checksums[0],
                        **{key: row[key] for key in ('id', 'sha256', 'path') if key in row}}
    return entries, {'path': str(path), 'sha256': evidence['sha256'], 'main_count': len(entries)}


def _preview_receipt(evidence, host):
    if not isinstance(evidence, dict) or set(evidence) != {'receipt_path', 'receipt_sha256', 'transport_contract_sha256'}:
        _hold('PREVIEW_SAVED_OPERATION_EVIDENCE_REQUIRED')
    if evidence['transport_contract_sha256'] != transport_contract_sha256():
        _hold('PREVIEW_TRANSPORT_CONTRACT_HASH_MISMATCH')
    value = evidence['receipt_path']
    if not isinstance(value, str) or not Path(value).is_absolute():
        _hold('PREVIEW_RECEIPT_ABSOLUTE_PATH_REQUIRED')
    path = Path(value)
    if path.is_symlink() or not path.is_file(): _hold('PREVIEW_SAVED_RECEIPT_REQUIRED')
    try:
        raw = path.read_bytes(); receipt = json.loads(raw)
    except (OSError, ValueError): _hold('PREVIEW_RECEIPT_UNREADABLE')
    if hashlib.sha256(raw).hexdigest() != evidence['receipt_sha256']:
        _hold('PREVIEW_RECEIPT_FILE_HASH_MISMATCH')
    if (not isinstance(receipt, dict) or receipt.get('environment') != host
            or receipt.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
            or type(receipt.get('http_status')) is not int or not 200 <= receipt['http_status'] < 300
            or not isinstance(receipt.get('response_sha256'), str)
            or re.fullmatch(r'[0-9a-f]{64}', receipt['response_sha256']) is None):
        _hold('PREVIEW_SUCCESSFUL_HASH_BOUND_RECEIPT_REQUIRED')
    parsed = urlsplit(receipt.get('url', ''))
    if parsed.scheme != 'https' or parsed.netloc != host or parsed.query or parsed.fragment:
        _hold('PREVIEW_RECEIPT_FOREIGN_ENDPOINT')
    return receipt, {'receipt_path': str(path), 'receipt_file_sha256': evidence['receipt_sha256'],
        'raw_response_sha256': receipt['response_sha256'],
        'transport_contract_sha256': evidence['transport_contract_sha256']}


def _preview_after(first, second):
    left, right = Path(first['receipt_path']), Path(second['receipt_path'])
    pattern = re.compile(r'([0-9]{3,})_(GET|POST|PUT|DELETE)\.json\Z')
    before, after = pattern.fullmatch(left.name), pattern.fullmatch(right.name)
    return (left.parent == right.parent and before is not None and after is not None
            and int(after[1]) > int(before[1]))


def _preview_entries(record):
    files = record.get('files')
    if not isinstance(files, dict) or not isinstance(files.get('entries'), dict):
        _hold('PREVIEW_NATIVE_MAIN_ENTRIES_REQUIRED')
    entries = files['entries']; ids = []
    for name, row in entries.items():
        _preview_key(name)
        if not isinstance(row, dict) or row.get('key') != name:
            _hold('PREVIEW_MAIN_FILE_KEY_MISMATCH')
        if type(row.get('size')) is not int or row['size'] < 0 or not isinstance(row.get('checksum'), str) or re.fullmatch(r'md5:[0-9a-f]{32}', row['checksum']) is None:
            _hold('PREVIEW_MAIN_FILE_BYTES_SHAPE')
        if not isinstance(row.get('id'), str) or not row['id']:
            _hold('PREVIEW_MAIN_SOURCE_ID_REQUIRED')
        ids.append(row['id'])
    if len(ids) != len(set(ids)): _hold('PREVIEW_AMBIGUOUS_MAIN_SOURCE_ID')
    return entries


def _preview_url(value, *, host, record_id, allowed_keys):
    """A real URL must name this record AND the exact approved source key."""
    if not isinstance(value, str): _hold('PREVIEW_LINK_NOT_URL')
    parsed = urlsplit(value)
    try: port = parsed.port
    except ValueError: _hold('PREVIEW_LINK_PORT')
    if (parsed.scheme != 'https' or parsed.hostname != host or parsed.username
            or parsed.password or port not in (None, 443) or parsed.fragment):
        _hold('PREVIEW_LINK_FOREIGN_HOST_OR_SHAPE')
    parts = [unquote(part) for part in parsed.path.split('/') if part]
    key = None
    if len(parts) >= 3 and parts[:2] == ['api', 'iiif']:
        match = re.fullmatch(r'(?:record|draft):' + re.escape(record_id) + r':(.+)', parts[2])
        if match: key = match[1]
        elif (len(parts) == 5 and parts[2] in ('record:' + record_id, 'draft:' + record_id)
                and parts[3] == 'canvas'):
            key = parts[4]
    elif len(parts) >= 5 and parts[:3] == ['api', 'records', record_id]:
        rest = parts[3:]
        if rest and rest[0] == 'draft': rest = rest[1:]
        if len(rest) >= 2 and rest[0] in ('files', 'media-files'): key = rest[1]
    if key is None or _preview_key(key) not in allowed_keys:
        _hold('PREVIEW_LINK_FOREIGN_RECORD_FILE_OR_UNAPPROVED_SOURCE')
    return key


def _preview_field_differences(actual, expected, field, path):
    """Keep absence distinct from null and log complete changed derived values."""
    if (field in actual) != (field in expected):
        return [{'path': path, 'before_present': field in expected,
            'after_present': field in actual, 'before': deepcopy(expected.get(field)),
            'after': deepcopy(actual.get(field))}]
    return _full_differences(actual.get(field), expected.get(field), path)


def require_derived_previews(actual, expected, *, host, record_id, operation,
        phase='PUBLISHED', derived_preview_context=None):
    """Source-bound rendering projection only; never alters the main inventory.

    Frozen approved target bytes remain authoritative. An inherited file being
    replaced may explain thumbnail disappearance only through its exact saved
    own deletion. No old inherited byte is thereby admitted as a certified file.
    Complete normalized main entries still undergo the ordinary exact consumer.
    """
    _objects(actual, expected); host = _host(host); record_id = _id(record_id)
    if _id(actual.get('id')) != record_id or _id(expected.get('id')) != record_id:
        _hold('PREVIEW_RECORD_ID_MISMATCH')
    left, right = deepcopy(actual), deepcopy(expected)
    differences = []
    if not _same_field(actual.get('links', {}), expected.get('links', {}), 'thumbnails'):
        differences.extend(_preview_field_differences(actual.get('links', {}), expected.get('links', {}), 'thumbnails', 'links.thumbnails'))
    if not _same_field(actual, expected, 'media_files'):
        differences.extend(_preview_field_differences(actual, expected, 'media_files', 'media_files'))
    aentries = actual.get('files', {}).get('entries', {}) if isinstance(actual.get('files'), dict) else {}
    eentries = expected.get('files', {}).get('entries', {}) if isinstance(expected.get('files'), dict) else {}
    for name in set(aentries) & set(eentries):
        alinks = aentries[name].get('links', {}) if isinstance(aentries[name], dict) else {}
        elinks = eentries[name].get('links', {}) if isinstance(eentries[name], dict) else {}
        if not isinstance(alinks, dict) or not isinstance(elinks, dict): _hold('PREVIEW_FILE_LINKS_OBJECT_REQUIRED')
        for field in _PREVIEW_FILE_LINKS:
            if not _same_field(alinks, elinks, field):
                differences.extend(_preview_field_differences(alinks, elinks, field, 'files.entries.' + name + '.links.' + field))
        if not _same_field(aentries[name], eentries[name], 'metadata'):
            differences.extend(_preview_field_differences(aentries[name], eentries[name], 'metadata', 'files.entries.' + name + '.metadata'))
    if not differences:
        return {'normalized_actual': left, 'normalized_expected': right, 'diff_appendix': [],
                'provenance': {}, 'own_record': False, 'main_inventory_separate': True}
    if operation == 'PRIOR_VERSION' or operation not in ('NEW_VERSION', 'AMENDMENT') or phase not in ('DRAFT', 'PUBLISHED'):
        _hold('PREVIEW_UNTOUCHED_PRIOR_OR_INVALID_OPERATION')
    ctx = derived_preview_context
    if not isinstance(ctx, dict) or set(ctx) - _PREVIEW_CONTEXT_KEYS or _id(ctx.get('own_record_id')) != record_id:
        _hold('PREVIEW_EXPLICIT_OWN_RECORD_CONTEXT_REQUIRED')
    inventory, inventory_log = _preview_inventory(ctx.get('approved_inventory_evidence'))
    removal_inventory, removal_inventory_log = ({}, None)
    if ctx.get('approved_removal_inventory_evidence') is not None:
        removal_inventory, removal_inventory_log = _preview_inventory(ctx['approved_removal_inventory_evidence'], removals=True)
    main, baseline = _preview_entries(actual), _preview_entries(expected)
    if set(main) != set(baseline): _hold('PREVIEW_MAIN_FILENAME_SET_CHANGED')
    lineage, lineage_log = _preview_receipt(ctx.get('lineage_evidence'), host)
    response = lineage.get('response'); path = urlsplit(lineage['url']).path
    if (lineage.get('method') != 'POST' or not isinstance(response, dict)
            or _id(response.get('id')) != record_id
            or not (path == '/api/deposit/depositions' or path == '/api/deposit/depositions/' + record_id + '/actions/edit'
                    or re.fullmatch(r'/api/deposit/depositions/[1-9][0-9]*/actions/newversion', path))):
        _hold('PREVIEW_OWN_LINEAGE_RECEIPT_REQUIRED')
    if path.endswith('/actions/newversion') and path.split('/')[4] == record_id:
        _hold('PREVIEW_NEWVERSION_MUST_CREATE_DISTINCT_RECORD')
    reads = []; buckets = set(); read_logs = []
    bucket = response.get('links', {}).get('bucket') if isinstance(response.get('links'), dict) else None
    if isinstance(bucket, str): buckets.add(bucket)
    read_evidence = ctx.get('source_readback_evidence', [])
    if not isinstance(read_evidence, list) or not read_evidence: _hold('PREVIEW_SOURCE_READBACK_EVIDENCE_REQUIRED')
    for evidence in read_evidence:
        receipt, log = _preview_receipt(evidence, host); record = receipt.get('response')
        if receipt.get('method') != 'GET' or not isinstance(record, dict) or _id(record.get('id')) != record_id:
            _hold('PREVIEW_OWN_SOURCE_GET_REQUIRED')
        endpoint = urlsplit(receipt['url']).path
        if endpoint in ('/api/records/' + record_id, '/api/records/' + record_id + '/draft') and receipt.get('accept') == 'application/vnd.inveniordm.v1+json':
            entries = _preview_entries(record)
            reads.append((record, entries, log))
        elif endpoint == '/api/deposit/depositions/' + record_id and receipt.get('accept') == 'application/json':
            own_bucket = record.get('links', {}).get('bucket')
            if isinstance(own_bucket, str): buckets.add(own_bucket)
        else: _hold('PREVIEW_OWN_AUTHENTICATED_SOURCE_ENDPOINT_REQUIRED')
        read_logs.append(log)
    if not reads: _hold('PREVIEW_NATIVE_SOURCE_ID_EVIDENCE_REQUIRED')
    deletions = {}; delete_logs = []
    delete_evidence = ctx.get('delete_evidence', [])
    if not isinstance(delete_evidence, list): _hold('PREVIEW_DELETE_EVIDENCE_LIST')
    for evidence in delete_evidence:
        receipt, log = _preview_receipt(evidence, host)
        prefix = '/api/deposit/depositions/' + record_id + '/files/'
        endpoint = urlsplit(receipt['url']).path
        if (receipt.get('method') != 'DELETE' or not endpoint.startswith(prefix)
                or receipt.get('http_status') != 204
                or receipt.get('request_body_sha256') != hashlib.sha256(b'').hexdigest()
                or receipt.get('response_sha256') != hashlib.sha256(b'').hexdigest()
                or not _exact(receipt.get('response'), {'empty_204': True, 'draft_file_removed': True})):
            _hold('PREVIEW_OWN_DRAFT_FILE_DELETE_REQUIRED')
        file_id = endpoint[len(prefix):]
        before = [(record, entries, proof) for record, entries, proof in reads
                  if _preview_after(proof, log) and any(row['id'] == file_id for row in entries.values())]
        after = [(record, entries, proof) for record, entries, proof in reads
                 if _preview_after(log, proof) and not any(row['id'] == file_id for row in entries.values())]
        if not before or not after: _hold('PREVIEW_DELETE_BEFORE_AFTER_SOURCE_PROOF_REQUIRED')
        names = {name for _, entries, _ in before for name, row in entries.items() if row['id'] == file_id}
        if len(names) != 1: _hold('PREVIEW_DELETED_SOURCE_KEY_AMBIGUOUS')
        name = next(iter(names))
        if name not in removal_inventory: _hold('PREVIEW_DELETED_SOURCE_NOT_IN_APPROVED_REMOVAL_INVENTORY')
        if any(record.get('is_draft') is not True or record.get('is_published') is not False for record, _, _ in before + after):
            _hold('PREVIEW_DELETE_REQUIRES_UNPUBLISHED_SOURCE')
        source = [entries[name] for _, entries, _ in before if name in entries and entries[name]['id'] == file_id]
        if any(not _exact(row, source[0]) for row in source): _hold('PREVIEW_DELETED_SOURCE_CHANGED')
        approved_source = removal_inventory[name]
        if any(not _exact(source[0].get(field), approved_source.get(field)) for field in ('key', 'id', 'checksum', 'size')):
            _hold('PREVIEW_DELETED_SOURCE_BYTES_NOT_APPROVED')
        deletions[name] = {'entry': deepcopy(source[0]), 'evidence': log}
        delete_logs.append({'key': name, 'source_file_id': file_id, **log})
    uploads = set(); upload_logs = []; uploaded_native_proofs = {}
    upload_evidence = ctx.get('upload_evidence', [])
    if not isinstance(upload_evidence, list): _hold('PREVIEW_UPLOAD_EVIDENCE_LIST')
    for evidence in upload_evidence:
        receipt, log = _preview_receipt(evidence, host); uploaded = receipt.get('response')
        endpoint = receipt['url']; own = None
        for bucket in buckets:
            if endpoint.startswith(bucket + '/'):
                candidate = unquote(endpoint[len(bucket) + 1:])
                if candidate in inventory: own = candidate
        if receipt.get('method') != 'PUT' or own is None or not isinstance(uploaded, dict):
            _hold('PREVIEW_OWN_APPROVED_UPLOAD_REQUIRED')
        target = inventory[own]
        if (uploaded.get('key') != own or uploaded.get('checksum') != target['checksum']
                or type(uploaded.get('size')) is not int or uploaded['size'] != target['size']
                or uploaded.get('is_head') is not True or uploaded.get('delete_marker') is not False
                or not isinstance(receipt.get('request_body_sha256'), str)
                or re.fullmatch(r'[0-9a-f]{64}', receipt['request_body_sha256']) is None
                or 'sha256' in target and receipt['request_body_sha256'] != target['sha256']):
            _hold('PREVIEW_UPLOADED_SOURCE_BYTES_MISMATCH')
        native_proofs = [(entries[own], proof) for _, entries, proof in reads
            if _preview_after(log, proof) and own in entries and entries[own]['checksum'] == target['checksum'] and entries[own]['size'] == target['size']]
        if not native_proofs:
            _hold('PREVIEW_UPLOAD_NATIVE_SOURCE_READBACK_REQUIRED')
        uploaded_native_proofs[own] = (receipt, log, native_proofs)
        uploads.add(own); upload_logs.append({'key': own, **log})
    publish = ctx.get('publish_evidence'); publish_log = None
    if publish is not None:
        receipt, publish_log = _preview_receipt(publish, host)
        require_publish_scope(host=host, record_id=record_id, own_publish_response=receipt,
            same_operation_reservation_id=record_id)

    def bound_source(name, *, current=True):
        if not current and name in deletions: return deletions[name]['entry']
        if name not in inventory: _hold('PREVIEW_UNAPPROVED_SOURCE_FILE')
        if name not in main:
            _hold('PREVIEW_SOURCE_FILE_NOT_IN_MAIN_INVENTORY')
        entry = main[name]; target = inventory[name]
        if entry['checksum'] != target['checksum'] or entry['size'] != target['size'] or 'id' in target and entry['id'] != target['id']:
            _hold('PREVIEW_MAIN_SOURCE_BYTES_OR_ID_CHANGED')
        if not any(name in entries and all(_exact(entries[name].get(field), entry.get(field)) for field in ('key', 'id', 'checksum', 'size')) for _, entries, _ in reads):
            _hold('PREVIEW_SOURCE_FILE_ID_UNRESOLVED')
        return entry

    def thumbnail_keys(value):
        if not isinstance(value, dict) or not value: _hold('PREVIEW_THUMBNAIL_URL_MAP_REQUIRED')
        names = set()
        for url in value.values(): names.add(_preview_url(url, host=host, record_id=record_id, allowed_keys=set(inventory) | set(deletions)))
        return names

    a_links, e_links = actual.get('links', {}), expected.get('links', {})
    if not _same_field(a_links, e_links, 'thumbnails'):
        prior_names = thumbnail_keys(e_links['thumbnails']) if 'thumbnails' in e_links else set()
        names = thumbnail_keys(a_links['thumbnails']) if 'thumbnails' in a_links else set()
        if any(name not in deletions for name in prior_names - names):
            _hold('PREVIEW_THUMBNAIL_DISAPPEARANCE_REQUIRES_OWN_DELETE')
        if not names:
            if not prior_names or any(name not in deletions for name in prior_names):
                _hold('PREVIEW_THUMBNAIL_DISAPPEARANCE_REQUIRES_OWN_DELETE')
        else:
            for name in names:
                bound_source(name)
                if name not in uploads and publish_log is None:
                    _hold('PREVIEW_THUMBNAIL_APPEARANCE_REQUIRES_UPLOAD_OR_PUBLISH')
        if 'thumbnails' in e_links: left.setdefault('links', {})['thumbnails'] = deepcopy(e_links['thumbnails'])
        else: left.get('links', {}).pop('thumbnails', None)
    for name in main:
        a_links, e_links = main[name].get('links', {}), baseline[name].get('links', {})
        for field in _PREVIEW_FILE_LINKS:
            if _same_field(a_links, e_links, field): continue
            bound_source(name)
            if field == 'container' and not name.lower().endswith('.zip'):
                _hold('PREVIEW_CONTAINER_REQUIRES_APPROVED_ARCHIVE')
            for links in (a_links, e_links):
                if field in links: _preview_url(links[field], host=host, record_id=record_id, allowed_keys={name})
            row = left['files']['entries'][name]
            if field in e_links: row.setdefault('links', {})[field] = deepcopy(e_links[field])
            else:
                row.get('links', {}).pop(field, None)
                if not row.get('links') and 'links' not in baseline[name]: row.pop('links', None)
    if not _same_field(actual, expected, 'media_files'):
        for record in (actual, expected):
            media = record.get('media_files', {'entries': {}})
            if not isinstance(media, dict) or not isinstance(media.get('entries', {}), dict):
                _hold('PREVIEW_MEDIA_ENTRIES_OBJECT_REQUIRED')
            entries = media.get('entries', {})
            for name, entry in entries.items():
                _preview_key(name)
                if not isinstance(entry, dict) or entry.get('key', name) != name or not isinstance(entry.get('processor'), dict):
                    _hold('PREVIEW_MEDIA_ENTRY_OR_PROCESSOR_REQUIRED')
                source_id = entry['processor'].get('source_file_id')
                matches = [key for key, row in main.items() if row['id'] == source_id]
                if not isinstance(source_id, str) or len(matches) != 1:
                    _hold('PREVIEW_MEDIA_SOURCE_FILE_ID_UNRESOLVED')
                bound_source(matches[0])
                if 'links' in entry:
                    if not isinstance(entry['links'], dict): _hold('PREVIEW_MEDIA_LINKS_OBJECT_REQUIRED')
                    for url in entry['links'].values():
                        _preview_url(url, host=host, record_id=record_id, allowed_keys={name, matches[0]})
            if 'count' in media and (type(media['count']) is not int or media['count'] != len(entries)):
                _hold('PREVIEW_MEDIA_AGGREGATE_COUNT')
            if 'total_bytes' in media:
                if type(media['total_bytes']) is not int or media['total_bytes'] < 0 or any(type(row.get('size')) is not int or row['size'] < 0 for row in entries.values()) or media['total_bytes'] != sum(row['size'] for row in entries.values()):
                    _hold('PREVIEW_MEDIA_AGGREGATE_BYTES')
        if 'media_files' in expected: left['media_files'] = deepcopy(expected['media_files'])
        else: left.pop('media_files', None)
    byte_metadata_logs = []
    for name in main:
        entry, previous = main[name], baseline[name]
        if _same_field(entry, previous, 'metadata'): continue
        bound_source(name)
        metadata, prior_metadata = entry.get('metadata'), previous.get('metadata', {})
        if not isinstance(metadata, dict) or not isinstance(prior_metadata, dict):
            _hold('BYTE_METADATA_FLAT_OBJECT_REQUIRED')
        if set(prior_metadata) - set(metadata):
            _hold('BYTE_METADATA_SERVER_FIELD_DISAPPEARANCE_NOT_COMPUTABLE')
        if any(not isinstance(field, str) for field in metadata):
            _hold('BYTE_METADATA_FIELD_NAME_TYPE')
        target = inventory[name]
        if 'path' not in target or 'sha256' not in target:
            _hold('BYTE_METADATA_APPROVED_LOCAL_PATH_AND_SHA_REQUIRED')
        if name not in uploaded_native_proofs:
            _hold('BYTE_METADATA_MATCHING_OWN_UPLOAD_REQUIRED')
        upload_receipt, upload_proof, native_proofs = uploaded_native_proofs[name]
        if operation == 'AMENDMENT':
            if path != '/api/deposit/depositions/' + record_id + '/actions/edit' or not _preview_after(lineage_log, upload_proof):
                _hold('BYTE_METADATA_AMENDMENT_UPLOAD_MUST_FOLLOW_OWN_EDIT')
        elif path.endswith('/actions/edit'):
            _hold('BYTE_METADATA_NEW_VERSION_CREATION_REQUIRED')
        # A new version's distinct ID/bucket is minted by this original own
        # CREATE. Resumed upload logs may live in a later immutable directory;
        # historical uploads from an earlier EDIT never qualify as new bytes.
        own_bucket = response.get('links', {}).get('bucket') if isinstance(response.get('links'), dict) else None
        if (not isinstance(own_bucket, str) or not upload_receipt['url'].startswith(own_bucket + '/')
                or unquote(upload_receipt['url'][len(own_bucket) + 1:]) != name):
            _hold('BYTE_METADATA_UPLOAD_NOT_ORIGINAL_OWN_OPERATION_BUCKET')
        if Path(lineage_log['receipt_path']).parent == Path(upload_proof['receipt_path']).parent and not _preview_after(lineage_log, upload_proof):
            _hold('BYTE_METADATA_UPLOAD_PRECEDES_OWN_LINEAGE')
        if upload_receipt['request_body_sha256'] != target['sha256']:
            _hold('BYTE_METADATA_OWN_UPLOAD_HASH_MISMATCH')
        matched_reads = [proof for row, proof in native_proofs
            if all(_exact(row.get(field), entry.get(field)) for field in ('key', 'id', 'checksum', 'size'))]
        if not matched_reads:
            _hold('BYTE_METADATA_OWN_POST_UPLOAD_UUID_BYTES_UNRESOLVED')
        from file_byte_metadata import compute_approved_file_facts, require_computed_field
        computed = compute_approved_file_facts(target['path'], sha256=target['sha256'],
            checksum=target['checksum'], size=target['size'])
        changed_fields = [field for field in metadata if not _same_field(metadata, prior_metadata, field)]
        if not changed_fields:
            _hold('BYTE_METADATA_EMPTY_CONTAINER_PRESENCE_NOT_COMPUTABLE')
        # Geometry is a pair; partial/null/malformed values are not invented.
        if set(changed_fields) & {'width', 'height'}:
            if not {'width', 'height'} <= set(metadata):
                _hold('BYTE_METADATA_WIDTH_HEIGHT_PAIR_REQUIRED')
            for field in ('width', 'height'):
                require_computed_field(metadata[field], field=field, facts=computed['facts'])
        for field in changed_fields:
            require_computed_field(metadata[field], field=field, facts=computed['facts'])
            if field in prior_metadata:
                require_computed_field(prior_metadata[field], field=field, facts=computed['facts'])
        if 'metadata' in previous:
            left['files']['entries'][name]['metadata'] = deepcopy(previous['metadata'])
        else:
            left['files']['entries'][name].pop('metadata', None)
        byte_metadata_logs.append({'file_key': name, 'source_file_id': entry['id'],
            'source_checksum': entry['checksum'], 'source_size': entry['size'],
            'changed_fields': sorted(changed_fields), 'parser_output': computed,
            'own_upload': upload_proof, 'post_upload_native_readbacks': matched_reads,
            'diff_appendix': _preview_field_differences(entry, previous, 'metadata',
                'files.entries.' + name + '.metadata'), 'source_comparison_authoritative': True})
    require_file_entries(left, right)
    return {'normalized_actual': left, 'normalized_expected': right,
        'diff_appendix': differences, 'own_record': True, 'main_inventory_separate': True,
        'provenance': {'own_record_id': record_id, 'approved_inventory': inventory_log,
            'approved_removal_inventory': removal_inventory_log,
            'lineage': lineage_log, 'source_readbacks': read_logs, 'deletions': delete_logs,
            'uploads': upload_logs, 'publish': publish_log, 'byte_metadata': byte_metadata_logs}}


def require_links_stats(actual, expected, *, record_id, host):
    """Row 6: changed URLs own this ID; changed statistics contain counters only."""
    record_id = _id(record_id)
    host = _host(host)
    own_doi = actual.get('pids', {}).get('doi', {}).get('identifier')
    for group in ('links', 'stats'):
        left, right = actual.get(group, {}), expected.get(group, {})
        if not isinstance(left, dict) or not isinstance(right, dict):
            _hold(group.upper() + '_OBJECT_REQUIRED')
        # Removal is a field disappearance, not a changed URL or counter value.
        if set(right) - set(left):
            _hold(group.upper() + '_FIELD_REMOVED')
        for key, value in left.items():
            if not isinstance(key, str):
                _hold(group.upper() + '_KEY_TYPE')
            if key in right and _exact(value, right[key]):
                continue
            if group == 'links':
                _own_url(value, record_id, host, own_doi)
            else:
                _counters(value)


def require_file_entries(actual, expected):
    """Row 7: only complete unique-filename entry order is normalized."""
    if 'files' not in actual or 'files' not in expected:
        _hold('FILES_INPUT_MISSING')
    left, right = actual.get('files'), expected.get('files')
    if isinstance(left, list) or isinstance(right, list):
        return require_file_preservation(left, right)
    if not isinstance(left, dict) or not isinstance(right, dict):
        _hold('FILES_INPUT_TYPE')
    if _exact(left, right):
        return {'mode': 'EXACT_NATIVE_FILES_OBJECT'}
    left_rest, right_rest = deepcopy(left), deepcopy(right)
    left_order, right_order = left_rest.pop('order', None), right_rest.pop('order', None)
    if ('order' in left) != ('order' in right) or not _exact(left_rest, right_rest):
        _hold('NATIVE_FILES_PER_FILE_OR_OTHER_FIELD_CHANGED')
    for order in (left_order, right_order):
        if not isinstance(order, list) or any(not isinstance(key, str) or not key for key in order):
            _hold('NATIVE_FILE_ORDER_INPUT')
    if len(set(left_order)) != len(left_order) or len(set(right_order)) != len(right_order):
        if not _exact(left_order, right_order):
            _hold('NATIVE_FILE_ORDER_STRICT_DUPLICATE_FILENAMES')
        return {'mode': 'STRICT_ORDERED_DUPLICATE_FILENAMES', 'count': len(left_order)}
    entries = left.get('entries')
    if not isinstance(entries, dict) or any(not isinstance(key, str) or not key or not isinstance(value, dict) for key, value in entries.items()):
        _hold('NATIVE_FILE_ENTRIES_REQUIRED')
    if set(left_order) != set(right_order) or set(left_order) != set(entries):
        _hold('NATIVE_FILE_ORDER_FILENAME_SET')
    return {'mode': 'FILENAME_KEYED_NATIVE_ORDER', 'count': len(entries)}


def require_content_metadata(actual, expected):
    """Keep the existing tested HTML rule and every other metadata field exact."""
    left, right = actual.get('metadata'), expected.get('metadata')
    if not isinstance(left, dict) or not isinstance(right, dict):
        _hold('METADATA_OBJECT_REQUIRED')
    require_public_metadata(left, right)
    left, right = deepcopy(left), deepcopy(right)
    # Only the already-approved description rendering differences normalize.
    if ('description' in left) != ('description' in right):
        _hold('DESCRIPTION_PRESENCE_CHANGED')
    left.pop('description', None)
    right.pop('description', None)
    if not _exact(left, right):
        _hold('CONTENT_METADATA_CHANGED')


def _differences(left, right, path=''):
    if isinstance(left, dict) and isinstance(right, dict):
        result = []
        for key in sorted(left.keys() | right.keys()):
            name = path + '.' + key if path else key
            if key not in left or key not in right:
                result.append(name)
            else:
                result.extend(_differences(left[key], right[key], name))
        return result
    return [] if _exact(left, right) else [path]


def _full_differences(actual, expected, path='ui'):
    """Append complete values, including presence, for every changed UI leaf."""
    if isinstance(actual, dict) and isinstance(expected, dict):
        result = []
        for key in sorted(actual.keys() | expected.keys()):
            name = path + '.' + key
            if key not in actual or key not in expected:
                result.append({'path': name, 'before_present': key in expected,
                    'after_present': key in actual, 'before': deepcopy(expected.get(key)),
                    'after': deepcopy(actual.get(key))})
            else:
                result.extend(_full_differences(actual[key], expected[key], name))
        return result
    if _exact(actual, expected):
        return []
    return [{'path': path, 'before_present': True, 'after_present': True,
             'before': deepcopy(expected), 'after': deepcopy(actual)}]


def _ui_differences(actual, expected):
    if ('ui' in actual) != ('ui' in expected):
        return [{'path': 'ui', 'before_present': 'ui' in expected,
                 'after_present': 'ui' in actual, 'before': deepcopy(expected.get('ui')),
                 'after': deepcopy(actual.get('ui'))}]
    return _full_differences(actual.get('ui'), expected.get('ui'))


def _require_own_ui_scope(actual, expected, record_id, own_operation_record_id):
    record_id = _id(record_id)
    if (_id(own_operation_record_id) != record_id or
            _id(actual.get('id')) != record_id or _id(expected.get('id')) != record_id):
        _hold('UI_OWN_OPERATION_RECORD_ID_MISMATCH')


def _require_own_ui_flag(actual, phase):
    ui = actual.get('ui')
    if not isinstance(ui, dict) or type(ui.get('is_draft')) is not bool:
        _hold('UI_RULE_HOLD:IS_DRAFT_BOOLEAN_REQUIRED')
    if phase not in ('DRAFT', 'PUBLISHED'):
        _hold('UI_RULE_HOLD:PHASE')
    if ui['is_draft'] is not (phase == 'DRAFT'):
        _hold('UI_RULE_HOLD:IS_DRAFT_PHASE_MISMATCH')
    return {'phase': phase, 'is_draft': ui['is_draft']}


_ENGLISH_MONTHS = {
    name: number for number, names in enumerate((
        ('january', 'jan'), ('february', 'feb'), ('march', 'mar'), ('april', 'apr'),
        ('may',), ('june', 'jun'), ('july', 'jul'), ('august', 'aug'),
        ('september', 'sep', 'sept'), ('october', 'oct'), ('november', 'nov'),
        ('december', 'dec')), 1) for name in names
}


def _display_date(value):
    """Deterministic ISO/English parsing, independent of process locale."""
    if not isinstance(value, str):
        _hold('UI_RULE_HOLD:DATE_STRING_REQUIRED')
    text = value.strip()
    if re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', text):
        try:
            return date.fromisoformat(text)
        except ValueError:
            _hold('UI_RULE_HOLD:INVALID_CALENDAR_DATE')
    match = re.fullmatch(r'([A-Za-z]+)\s+([0-9]{1,2}),\s*([0-9]{4})', text)
    if match is None:
        _hold('UI_RULE_HOLD:UNPARSEABLE_DISPLAY_DATE')
    month = _ENGLISH_MONTHS.get(match[1].lower())
    if month is None:
        _hold('UI_RULE_HOLD:UNPARSEABLE_DISPLAY_MONTH')
    try:
        return date(int(match[3]), month, int(match[2]))
    except ValueError:
        _hold('UI_RULE_HOLD:INVALID_CALENDAR_DATE')


def require_ui_display(actual, expected, *, record_id, operation,
                       phase='PUBLISHED', own_operation_record_id=None):
    """Night UI table only; the caller must still check every source field.

    An explicit operation-owned ID scopes amendments and draft reads. The
    complete audit also derives this ID from an already-proven own new-version
    publish receipt. This helper supplies no publication authority by itself.
    Prior/untouched records always keep their UI byte-exact.
    """
    _objects(actual, expected)
    if operation not in ('NEW_VERSION', 'AMENDMENT', 'PRIOR_VERSION') or phase not in ('DRAFT', 'PUBLISHED'):
        _hold('UI_RULE_HOLD:OPERATION_OR_PHASE')
    if _id(actual.get('id')) != _id(record_id) or _id(expected.get('id')) != _id(record_id):
        _hold('UI_OWN_OPERATION_RECORD_ID_MISMATCH')
    differences = _ui_differences(actual, expected)
    if operation == 'PRIOR_VERSION' or own_operation_record_id is None:
        if not _same_field(actual, expected, 'ui'):
            _hold('UNTOUCHED_UI_CHANGED')
        return {'own_record': False, 'diff_appendix': differences}
    _require_own_ui_scope(actual, expected, record_id, own_operation_record_id)
    _require_own_ui_flag(actual, phase)
    date_checks = []

    def check_dates(value, prior, path='ui'):
        if isinstance(value, dict) or isinstance(prior, dict):
            current_fields = value if isinstance(value, dict) else {}
            prior_fields = prior if isinstance(prior, dict) else {}
            for key in sorted(current_fields.keys() | prior_fields.keys()):
                child = current_fields.get(key)
                name = path + '.' + key
                if 'date' in key.lower():
                    # No calendar date is asserted by a byte-exact existing
                    # null display leaf (e.g. inactive embargo rendering).
                    # Do not invent a source mapping or ignore its presence.
                    if (key in current_fields and key in prior_fields and
                            child is None and prior_fields[key] is None):
                        date_checks.append({'path': name, 'unchanged_null_no_calendar_date': True})
                        continue
                    if key not in current_fields:
                        _hold('UI_RULE_HOLD:DATE_FIELD_REMOVED:' + name)
                    source_match = re.fullmatch(r'(created|updated|publication)_date(?:_.*)?', key.lower())
                    if source_match is None:
                        _hold('UI_RULE_HOLD:UNMAPPABLE_DATE_SOURCE:' + name)
                    source = source_match[1]
                    if source == 'publication':
                        source_path = 'metadata.publication_date'
                        metadata = actual.get('metadata')
                        if not isinstance(metadata, dict):
                            _hold('UI_RULE_HOLD:PUBLICATION_DATE_SOURCE:' + name)
                        source_value = metadata.get('publication_date')
                        if not isinstance(source_value, str) or re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', source_value) is None:
                            _hold('UI_RULE_HOLD:PUBLICATION_DATE_SOURCE:' + name)
                        source_date = _display_date(source_value)
                    else:
                        source_path = source
                        source_date = _timestamp(actual.get(source)).astimezone(timezone.utc).date()
                    displayed = _display_date(child)
                    offset = (displayed - source_date).days
                    if abs(offset) > 1:
                        _hold('UI_RULE_HOLD:DATE_DOES_NOT_MATCH_SOURCE:' + name)
                    date_checks.append({'path': name, 'source_path': source_path,
                        'display_date': displayed.isoformat(), 'source_utc_date': source_date.isoformat(),
                        'display_day_offset': offset})
                else:
                    check_dates(child, prior_fields.get(key), name)
        elif isinstance(value, list) or isinstance(prior, list):
            current_items = value if isinstance(value, list) else []
            prior_items = prior if isinstance(prior, list) else []
            for index in range(max(len(current_items), len(prior_items))):
                child = current_items[index] if index < len(current_items) else None
                old_child = prior_items[index] if index < len(prior_items) else None
                check_dates(child, old_child, path + '[' + str(index) + ']')

    check_dates(actual['ui'], expected.get('ui'))
    return {'own_record': True, 'own_operation_record_id': _id(own_operation_record_id),
            'date_checks': date_checks, 'diff_appendix': differences,
            'source_comparison_authoritative': True}


def audit_readback(actual, expected, *, host, record_id, operation,
                   same_operation_response=None, existing_concept_doi=None,
                   previous_latest_index=None, chain_parent_id=None,
                   temporal_baseline=None, existing_communities=None,
                   public_communities=None, mirror_proof=None,
                   phase='PUBLISHED', own_publish_response=None,
                   same_operation_reservation_id=None,
                   previous_public_readback=None, revision_evidence=None,
                   own_operation_record_id=None, version_chain_context=None,
                   derived_preview_context=None):
    """Collect every rule conflict; this diagnostic report never authorizes writes."""
    _objects(actual, expected)
    record_id = _id(record_id)
    _host(host)
    if operation not in ('NEW_VERSION', 'AMENDMENT', 'PRIOR_VERSION'):
        _hold('OPERATION')
    if phase not in ('DRAFT', 'PUBLISHED'):
        _hold('PHASE')
    normalized = deepcopy(actual)
    report = {'status': 'HOLD', 'operation': operation, 'record_id': record_id,
              'phase': phase, 'checks': {}, 'reasons': [], 'acceptance_authority': False}
    report['ui_diff_appendix'] = _ui_differences(actual, expected)
    own_ui_id = own_operation_record_id

    def run(name, function):
        try:
            detail = function()
            report['checks'][name] = {'status': 'PASS', 'detail': detail}
            return True
        except Exception as exc:
            reason = str(exc)
            report['checks'][name] = {'status': 'HOLD', 'reason': reason}
            report['reasons'].append({'rule': name, 'reason': reason})
            return False

    def restore_top(field):
        if field in comparable_expected:
            normalized[field] = deepcopy(comparable_expected[field])
        else:
            normalized.pop(field, None)

    run('record_identity', lambda: None if _id(actual.get('id')) == record_id and _id(expected.get('id')) == record_id else _hold('RECORD_ID_CHANGED'))
    comparable_actual, comparable_expected = actual, expected
    preview = None
    preview_result = {}

    def check_previews():
        result = require_derived_previews(actual, expected, host=host, record_id=record_id,
            operation=operation, phase=phase, derived_preview_context=derived_preview_context)
        preview_result.update(result)
        return result

    if run('derived_previews', check_previews):
        preview = preview_result
        comparable_actual, comparable_expected = preview['normalized_actual'], preview['normalized_expected']
        normalized = deepcopy(comparable_actual)
        report['derived_preview_diff_appendix'] = preview['diff_appendix']
        report['checks']['derived_previews']['detail'] = {key: preview[key] for key in
            ('diff_appendix', 'provenance', 'own_record', 'main_inventory_separate')}
    if operation == 'NEW_VERSION' and phase == 'PUBLISHED':
        scope_pass = run('own_publish_scope', lambda: require_publish_scope(host=host, record_id=record_id,
            own_publish_response=own_publish_response, same_operation_reservation_id=same_operation_reservation_id))
        if scope_pass:
            if own_ui_id is None:
                own_ui_id = same_operation_reservation_id
            comparable_actual, comparable_expected, representation_paths = own_representation_projection(comparable_actual, comparable_expected)
            report['representation_normalizations'] = representation_paths
            normalized = deepcopy(comparable_actual)
    if run(ALLOW_LIST[0], lambda: require_pids(comparable_actual, comparable_expected, host=host, record_id=record_id,
            new_version=operation == 'NEW_VERSION', phase=phase, own_publish_response=own_publish_response,
            same_operation_reservation_id=same_operation_reservation_id)):
        restore_top('pids')
    if operation == 'NEW_VERSION' and (phase == 'PUBLISHED' or same_operation_response is not None):
        run(ALLOW_LIST[1], lambda: require_minted_identifiers(actual, record_id=record_id,
                same_operation_response=same_operation_response, existing_concept_doi=existing_concept_doi))
    else:
        report['checks'][ALLOW_LIST[1]] = {'status': 'PASS', 'detail': 'No published minted-identifier claim; PIDs remain exact'}
    if run(ALLOW_LIST[2], lambda: require_community_mirror(actual, expected,
            existing_communities=existing_communities, public_communities=public_communities, mirror_proof=mirror_proof)):
        restore_top('custom_fields')
    def check_time():
        if operation == 'NEW_VERSION' and phase == 'PUBLISHED' and temporal_baseline is None:
            _hold('ACTUAL_BEFORE_PUBLISH_TEMPORAL_BASELINE_REQUIRED')
        return require_time(actual, expected, temporal_baseline=temporal_baseline)

    if run(ALLOW_LIST[3], check_time):
        for field in ('created', 'updated'):
            restore_top(field)
    if run('revision_id', lambda: require_revision(actual, expected, phase=phase,
            operation=operation, host=host, record_id=record_id,
            temporal_baseline=temporal_baseline, own_publish_response=own_publish_response,
            same_operation_reservation_id=same_operation_reservation_id,
            previous_public_readback=previous_public_readback, revision_evidence=revision_evidence)):
        restore_top('revision_id')
    for field in ('deletion_status', 'expires_at', 'swh', 'ui.is_draft'):
        if run(field, lambda field=field: require_publish_field(actual, expected,
                field=field, operation=operation, phase=phase, host=host,
                record_id=record_id, temporal_baseline=temporal_baseline,
                own_publish_response=own_publish_response,
                same_operation_reservation_id=same_operation_reservation_id,
                previous_public_readback=previous_public_readback,
                own_operation_record_id=own_ui_id)):
            if field == 'ui.is_draft':
                if isinstance(normalized.get('ui'), dict) and isinstance(expected.get('ui'), dict):
                    if 'is_draft' in expected['ui']:
                        normalized['ui']['is_draft'] = expected['ui']['is_draft']
                    else:
                        normalized['ui'].pop('is_draft', None)
            else:
                restore_top(field)
    if run('ui_display_fields', lambda: require_ui_display(actual, expected,
            record_id=record_id, operation=operation, phase=phase,
            own_operation_record_id=own_ui_id)):
        restore_top('ui')
    if run(ALLOW_LIST[4], lambda: require_versions(actual, expected, operation=operation,
            previous_latest_index=previous_latest_index, chain_parent_id=chain_parent_id, phase=phase,
            host=host, version_chain_context=version_chain_context, own_publish_response=own_publish_response)):
        if version_chain_context is not None or (operation == 'NEW_VERSION' and phase == 'PUBLISHED'):
            for field in (_CHAIN_FIELDS if version_chain_context is not None else ('index', 'is_latest')):
                if field in expected['versions']:
                    normalized['versions'][field] = deepcopy(expected['versions'][field])
                else:
                    normalized['versions'].pop(field, None)
            normalized['parent']['id'] = deepcopy(expected['parent']['id'])
    if run(ALLOW_LIST[5], lambda: require_links_stats(comparable_actual, comparable_expected, record_id=record_id, host=host)):
        restore_top('links')
        restore_top('stats')
    if run(ALLOW_LIST[6], lambda: require_file_entries(comparable_actual, comparable_expected)):
        restore_top('files')
    if run('content_metadata', lambda: require_content_metadata(actual, expected)):
        restore_top('metadata')
    differences = _differences(normalized, comparable_expected)
    if differences:
        report['checks']['unlisted_fields'] = {'status': 'HOLD', 'paths': differences}
        report['reasons'].append({'rule': 'unlisted_fields', 'reason': 'Unapproved or failed-rule differences', 'paths': differences})
    else:
        report['checks']['unlisted_fields'] = {'status': 'PASS', 'detail': 'Every remaining field is exact'}
    if not report['reasons']:
        report['status'] = 'SERVER_MANAGED_READBACK_PASS'
    return report


class ServerManagedMismatch(TransportHold):
    def __init__(self, report):
        self.report = report
        super().__init__('READBACK_MISMATCH_SERVER_MANAGED:' + '; '.join(
            item['rule'] + ':' + item['reason'] for item in report['reasons']))


def _require(actual, expected, **context):
    report = audit_readback(actual, expected, **context)
    if report['status'] != 'SERVER_MANAGED_READBACK_PASS':
        raise ServerManagedMismatch(report)
    return report


def validate_new_version(actual, expected_public_snapshot, **context):
    return _require(actual, expected_public_snapshot, operation='NEW_VERSION', **context)


def validate_amendment(actual, expected_public_snapshot, **context):
    return _require(actual, expected_public_snapshot, operation='AMENDMENT', **context)


def validate_prior_version(actual, expected_public_snapshot, **context):
    return _require(actual, expected_public_snapshot, operation='PRIOR_VERSION', **context)
