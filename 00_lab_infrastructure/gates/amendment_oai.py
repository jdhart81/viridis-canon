"""Approved own-amendment draft OAI workflow; no API, credential or write authority.

Public PIDs always remain exact. The independent caller's whole-record validator
is mandatory at every source boundary. Saved receipts prove the narrow private
transition; an independently qualified sandbox route determines publish readiness.
The producer contract is synchronous saved ZenodoTransport receipts; chronology
across frozen continuation directories is declared by the saved operation packet,
not invented timestamps. This module never retries or performs a mutation.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from publication_preservation import managed_pid_payload
from server_managed_fields import transport_contract_sha256
from zenodo_transport import TransportHold

SCHEMA = 'VRS-AMENDMENT-OAI-ROUTE-1'
ROUTE_A = 'ROUTE_A_PUBLISH_REGENERATES'
ROUTE_B = 'ROUTE_B_EXACT_NATIVE_RESTORE'
NATIVE = 'application/vnd.inveniordm.v1+json'
_QUALIFIED_MARKER = object()


def _hold(reason):
    raise TransportHold('HOLD_AMENDMENT_OAI:' + reason)


def _bytes(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
            separators=(',', ':'), allow_nan=False).encode()
    except (TypeError, ValueError):
        _hold('NON_JSON_INPUT')


def _exact(left, right, reason):
    if _bytes(left) != _bytes(right):
        _hold(reason)


def _id(value):
    if type(value) not in (str, int) or re.fullmatch(r'[1-9][0-9]*', str(value)) is None:
        _hold('OWN_ID')
    return str(value)


def _pinned(reference, *, receipt=False):
    names = {'receipt_path', 'receipt_sha256', 'transport_contract_sha256'} if receipt else {'path', 'sha256'}
    if not isinstance(reference, dict) or set(reference) != names:
        _hold('PINNED_REFERENCE_SHAPE')
    path = Path(reference['receipt_path' if receipt else 'path'])
    digest = reference['receipt_sha256' if receipt else 'sha256']
    if not path.is_absolute() or path.is_symlink() or not path.is_file() or re.fullmatch(r'[0-9a-f]{64}', str(digest)) is None:
        _hold('PINNED_REFERENCE_PATH_OR_HASH')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        _hold('PINNED_REFERENCE_HASH_MISMATCH')
    if receipt and reference['transport_contract_sha256'] != transport_contract_sha256():
        _hold('TRANSPORT_CONTRACT_HASH_MISMATCH')
    return raw


def _json_ref(reference, *, receipt=False):
    try:
        value = json.loads(_pinned(reference, receipt=receipt))
    except (ValueError, OSError):
        _hold('PINNED_REFERENCE_UNREADABLE')
    if not isinstance(value, dict):
        _hold('PINNED_OBJECT_REQUIRED')
    return value


def _receipt(reference, *, method, host, path, native=False, body_sha=None):
    value = _json_ref(reference, receipt=True)
    if (value.get('method') != method or value.get('url') != 'https://' + host + path
            or value.get('environment') != host
            or value.get('accept') != (NATIVE if native else 'application/json')
            or value.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
            or type(value.get('http_status')) is not int or not 200 <= value['http_status'] < 300
            or re.fullmatch(r'[0-9a-f]{64}', str(value.get('response_sha256'))) is None):
        _hold('SAVED_OWN_SUCCESS_RECEIPT_REQUIRED')
    if method == 'GET' and value.get('request_body_sha256') is not None:
        _hold('GET_BODY')
    if body_sha is not None and value.get('request_body_sha256') != body_sha:
        _hold('REVIEWED_REQUEST_BODY_HASH')
    if not isinstance(value.get('response'), dict):
        _hold('OWN_RESPONSE_OBJECT')
    return value


def _record(reference, *, host, record_id, draft=False):
    receipt = _receipt(reference, method='GET', host=host,
        path='/api/records/' + record_id + ('/draft' if draft else ''), native=True)
    value = receipt['response']
    if _id(value.get('id')) != record_id:
        _hold('SAVED_NATIVE_OWN_ID')
    if value.get('is_draft') is not draft:
        _hold('SAVED_NATIVE_DRAFT_BOUNDARY')
    return value


def _sequence(references, directory_order=None):
    """Require complete synchronous producer sequences and declared operation order."""
    paths = [Path(ref['receipt_path']) for ref in references]
    directories = list(dict.fromkeys(str(path.parent) for path in paths))
    order = directories if directory_order is None else directory_order
    if (not isinstance(order, list) or any(not isinstance(name, str) for name in order)
            or len(order) != len(set(order)) or set(order) != set(directories)):
        _hold('RECEIPT_CONTINUATION_ORDER')
    if len(directories) > 1 and directory_order is None:
        _hold('FROZEN_CONTINUATION_ORDER_REQUIRED')
    positions = []
    pattern = re.compile(r'([0-9]{3,})_(GET|POST|PUT|DELETE)\.json\Z')
    for directory in directories:
        numbered = {}
        for path in Path(directory).iterdir():
            match = pattern.fullmatch(path.name)
            if match is None:
                continue
            number = int(match[1])
            if number <= 0 or match[1] != f'{number:03d}' or number in numbered:
                _hold('AMBIGUOUS_RECEIPT_SEQUENCE')
            try:
                saved = json.loads(path.read_bytes())
            except (ValueError, OSError):
                _hold('UNREADABLE_RECEIPT_SEQUENCE')
            if not isinstance(saved, dict) or saved.get('method') != match[2]:
                _hold('RECEIPT_FILENAME_METHOD')
            numbered[number] = path
        if not numbered or set(numbered) != set(range(1, max(numbered) + 1)):
            _hold('INCOMPLETE_RECEIPT_SEQUENCE')
    for path in paths:
        match = pattern.fullmatch(path.name)
        if match is None:
            _hold('RECEIPT_FILENAME')
        positions.append((order.index(str(path.parent)), int(match[1])))
    if positions != sorted(set(positions)):
        _hold('RECEIPT_OPERATION_ORDER')


def _own_oai(pids, record_id):
    if not isinstance(pids, dict) or not pids:
        _hold('ORIGINAL_PIDS_REQUIRED')
    # The reviewed server uses this namespace in both environments.
    _exact(pids.get('oai'), {'identifier': 'oai:zenodo.org:' + record_id,
        'provider': 'oai'}, 'ORIGINAL_OAI_CANONICAL_OWN_ID_PROVIDER_SHAPE')


def require_public_pids(actual, original):
    """Absolute public invariant: complete original object, with no normalization."""
    if not isinstance(actual.get('pids'), dict) or not isinstance(original.get('pids'), dict):
        _hold('PUBLIC_PIDS_OBJECT')
    _exact(actual['pids'], original['pids'], 'PUBLIC_PID_MISMATCH_HARD_STOP')
    if _id(actual.get('id')) != _id(original.get('id')):
        _hold('PUBLIC_OWN_ID_MISMATCH')


def _source_check(validator, stage, actual, expected, context):
    if not callable(validator):
        _hold('INDEPENDENT_WHOLE_RECORD_VALIDATOR_REQUIRED')
    result = validator(stage, deepcopy(actual), deepcopy(expected), deepcopy(context))
    if not isinstance(result, dict) or result.get('status') not in (
            'SOURCE_VALIDATION_PASS', 'SERVER_MANAGED_READBACK_PASS',
            'OWN_EDIT_SOURCE_GUARD_PASS'):
        _hold('INDEPENDENT_SOURCE_VALIDATION_NOT_PASS:' + stage)


def _expected_metadata(record, payload):
    metadata = payload.get('metadata')
    if not isinstance(metadata, dict) or not isinstance(metadata.get('description'), str):
        _hold('REVIEWED_LEGACY_METADATA_BODY')
    keywords = metadata.get('keywords')
    if not isinstance(keywords, list) or any(type(word) is not str for word in keywords):
        _hold('REVIEWED_KEYWORDS')
    _exact(metadata.get('title'), record.get('metadata', {}).get('title'), 'REVIEWED_TITLE_CHANGED')
    doi = record.get('pids', {}).get('doi', {}).get('identifier')
    _exact(metadata.get('doi'), doi, 'REVIEWED_DOI_CHANGED')
    expected = deepcopy(record)
    expected['metadata']['description'] = metadata['description']
    expected['metadata']['subjects'] = [{'subject': word} for word in keywords]
    return expected


def _omission(original, after_edit, after_put, record_id, *, sandbox_doi_shape=False):
    _own_oai(original.get('pids'), record_id)
    _exact(after_edit.get('pids'), original['pids'], 'OAI_MUST_SURVIVE_INITIAL_EDIT')
    pids = after_put.get('pids')
    if not isinstance(pids, dict) or 'oai' in pids:
        _hold('ONLY_ABSENT_DRAFT_OAI_SUPPORTED')
    expected = deepcopy(original['pids']); expected.pop('oai')
    if sandbox_doi_shape and _bytes(pids.get('doi')) != _bytes(expected.get('doi')):
        # Already-decided legacy sandbox provider serialization, used solely to
        # qualify the transport experiment. It is NEVER a production exemption.
        doi = expected.get('doi', {})
        if doi.get('provider') != 'datacite':
            _hold('SANDBOX_ORIGINAL_DATACITE_PROVIDER_REQUIRED')
        permitted = {'identifier': doi.get('identifier'), 'provider': 'external'}
        _exact(pids.get('doi'), permitted, 'UNKNOWN_SANDBOX_DOI_TRANSIENT_SHAPE')
        normalized = deepcopy(pids); normalized['doi'] = deepcopy(doi)
        _exact(normalized, expected, 'OTHER_PID_CHANGED_OR_UNLISTED_PID')
    else:
        _exact(pids, expected, 'OTHER_PID_CHANGED_OR_UNLISTED_PID')


def _transition(evidence, *, host, record_id, source_validator, sandbox_qualification=False):
    required = {'original_native', 'edit', 'initial_edit_native', 'metadata_put',
        'after_put_native', 'metadata_put_body'}
    if not isinstance(evidence, dict) or set(evidence) - required - {'receipt_directory_order'} or not required <= set(evidence):
        _hold('TRANSITION_EVIDENCE_SHAPE')
    original = _record(evidence['original_native'], host=host, record_id=record_id)
    edit = _receipt(evidence['edit'], method='POST', host=host,
        path='/api/deposit/depositions/' + record_id + '/actions/edit',
        body_sha=hashlib.sha256(b'{}').hexdigest())
    if (_id(edit['response'].get('id')) != record_id or edit['response'].get('state') != 'inprogress'
            or edit['response'].get('submitted') is not True):
        _hold('OWN_EXISTING_EDIT_LIFECYCLE')
    initial = _record(evidence['initial_edit_native'], host=host, record_id=record_id, draft=True)
    body = _pinned(evidence['metadata_put_body'])
    payload = json.loads(body)
    put = _receipt(evidence['metadata_put'], method='PUT', host=host,
        path='/api/deposit/depositions/' + record_id,
        body_sha=hashlib.sha256(body).hexdigest())
    if _id(put['response'].get('id')) != record_id:
        _hold('OWN_LEGACY_PUT_RESPONSE_ID')
    after = _record(evidence['after_put_native'], host=host, record_id=record_id, draft=True)
    _sequence([evidence[name] for name in ('original_native', 'edit', 'initial_edit_native',
        'metadata_put', 'after_put_native')], evidence.get('receipt_directory_order'))
    _omission(original, initial, after, record_id,
        sandbox_doi_shape=sandbox_qualification and host == 'sandbox.zenodo.org')
    expected = _expected_metadata(initial, payload)
    normalized = deepcopy(after); normalized['pids'] = deepcopy(original['pids'])
    context = {'host': host, 'record_id': record_id, 'operation': 'AMENDMENT', 'phase': 'DRAFT',
        'edit_receipt': edit, 'evidence': evidence, 'payload': payload}
    _source_check(source_validator, 'INITIAL_EDIT', initial, original, context)
    _source_check(source_validator, 'AFTER_LEGACY_PUT', normalized, expected, context)
    return original, initial, after, payload, context


def _route_a_failure(reference, source_validator):
    """A failed experiment is evidence of route choice, never acceptance."""
    failure = _json_ref(reference)
    if failure.get('schema') != SCHEMA or failure.get('route') != ROUTE_A:
        _hold('ROUTE_A_ATTEMPT_REQUIRED_BEFORE_ROUTE_B')
    if failure.get('failure_kind') != 'DEFINITE_HTTP400_MANAGED_DOI_REJECTION':
        try:
            qualify_sandbox_route(reference, source_validator=source_validator)
        except TransportHold as exc:
            if str(exc) != 'HOLD_AMENDMENT_OAI:PUBLIC_PID_MISMATCH_HARD_STOP':
                _hold('ROUTE_A_ATTEMPT_NOT_VALIDATED_BEFORE_ROUTE_B')
        else:
            _hold('ROUTE_A_DID_NOT_FAIL_PUBLIC_PID_CHECK')
        refs = failure['receipts']
        return [(deepcopy(reference), False)] + [(deepcopy(ref), True) for ref in refs.values()]
    allowed = {'schema', 'route', 'host', 'record_id', 'transport_contract_sha256',
        'receipts', 'metadata_put_body', 'receipt_directory_order', 'failure_kind'}
    if (set(failure) - allowed or failure.get('host') != 'sandbox.zenodo.org'
            or failure.get('transport_contract_sha256') != transport_contract_sha256()):
        _hold('DEFINITE_ROUTE_A_FAILURE_SCOPE')
    receipts = failure.get('receipts')
    ordered = ['create', 'initial_publish', 'original_native', 'edit', 'initial_edit_native',
        'metadata_put', 'after_put_native', 'publish', 'final_native', 'post_failure_draft_native']
    if not isinstance(receipts, dict) or set(receipts) != set(ordered):
        _hold('DEFINITE_ROUTE_A_FAILURE_RECEIPTS')
    rid = _id(failure.get('record_id'))
    transition = {name: receipts[name] for name in ('original_native', 'edit', 'initial_edit_native',
        'metadata_put', 'after_put_native')}
    transition['metadata_put_body'] = failure['metadata_put_body']
    if 'receipt_directory_order' in failure:
        transition['receipt_directory_order'] = failure['receipt_directory_order']
    original, initial, after, payload, context = _transition(transition, host='sandbox.zenodo.org',
        record_id=rid, source_validator=source_validator, sandbox_qualification=True)
    create = _receipt(receipts['create'], method='POST', host='sandbox.zenodo.org', path='/api/deposit/depositions')
    initial_publish = _receipt(receipts['initial_publish'], method='POST', host='sandbox.zenodo.org',
        path='/api/deposit/depositions/' + rid + '/actions/publish', body_sha=hashlib.sha256(b'{}').hexdigest())
    if _id(create['response'].get('id')) != rid or _id(initial_publish['response'].get('id')) != rid:
        _hold('DEFINITE_ROUTE_A_FAILURE_OWN_ID')
    rejected = _json_ref(receipts['publish'], receipt=True)
    expected_message = ("The prefix '10.5072' is managed by Zenodo. Please supply an external DOI "
        "or select 'No' to have a DOI generated for you.")
    if (rejected.get('method') != 'POST' or rejected.get('url') !=
            'https://sandbox.zenodo.org/api/deposit/depositions/' + rid + '/actions/publish'
            or rejected.get('environment') != 'sandbox.zenodo.org'
            or rejected.get('accept') != 'application/json'
            or rejected.get('request_body_sha256') != hashlib.sha256(b'{}').hexdigest()
            or rejected.get('status') != 'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'
            or rejected.get('error_type') != 'HTTPError' or rejected.get('http_status') != 400
            or 'response' in rejected or 'response_sha256' in rejected
            or rejected.get('error_response') != {'status': 400, 'message': 'A validation error occurred.',
                'errors': [{'field': 'pids.doi', 'messages': [expected_message]}]}):
        _hold('DEFINITE_ROUTE_A_400_REJECTION_REQUIRED_NOT_TIMEOUT_OR_PENDING')
    if not original['pids'].get('doi', {}).get('identifier', '').startswith('10.5072/'):
        _hold('DEFINITE_ROUTE_A_MANAGED_PREFIX_SCOPE')
    public = _record(receipts['final_native'], host='sandbox.zenodo.org', record_id=rid)
    require_public_pids(public, original)
    _source_check(source_validator, 'UNCHANGED_PUBLIC', public, original, context)
    draft = _record(receipts['post_failure_draft_native'], host='sandbox.zenodo.org', record_id=rid, draft=True)
    _exact(draft.get('pids'), after.get('pids'), 'REJECTED_ROUTE_A_DRAFT_PID_CHANGED')
    _source_check(source_validator, 'CURRENT_DRAFT', draft, after, context)
    _sequence([receipts[name] for name in ordered], failure.get('receipt_directory_order'))
    return [(deepcopy(reference), False), (deepcopy(failure['metadata_put_body']), False)] + [
        (deepcopy(ref), True) for ref in receipts.values()]


@dataclass(frozen=True)
class RouteQualification:
    route: str
    proof_path: str
    proof_sha256: str
    transport_sha256: str
    references: tuple
    _qualified_marker: object = None

    def require_current(self):
        if self._qualified_marker is not _QUALIFIED_MARKER:
            _hold('STRUCTURAL_QUALIFICATION_FACTORY_REQUIRED')
        proof = _json_ref({'path': self.proof_path, 'sha256': self.proof_sha256})
        if proof.get('schema') != SCHEMA or proof.get('route') != self.route or proof.get('host') != 'sandbox.zenodo.org':
            _hold('QUALIFIED_ROUTE_CHANGED')
        if self.transport_sha256 != transport_contract_sha256():
            _hold('QUALIFIED_TRANSPORT_CHANGED')
        for reference, receipt in self.references:
            _pinned(reference, receipt=receipt)


def qualify_sandbox_route(proof_reference, *, source_validator):
    """Validate raw saved evidence; no summary boolean can qualify a route.

    Proof fields: schema, route, host, record_id, transport_contract_sha256,
    receipts, metadata_put_body, optional receipt_directory_order. Route B adds
    restore_body and route_a_failure (hash-bound failed Route A proof document).
    Whole-record callback(stage, actual, expected, context) must independently
    check source/lifecycle/preview/metadata/file fields and return a PASS status.
    """
    proof = _json_ref(proof_reference)
    route = proof.get('route')
    if (proof.get('schema') != SCHEMA or proof.get('host') != 'sandbox.zenodo.org'
            or route not in (ROUTE_A, ROUTE_B)
            or proof.get('transport_contract_sha256') != transport_contract_sha256()):
        _hold('SANDBOX_ROUTE_PROOF_SCOPE_OR_TRANSPORT')
    allowed = {'schema', 'route', 'host', 'record_id', 'transport_contract_sha256',
        'receipts', 'metadata_put_body', 'receipt_directory_order'}
    if route == ROUTE_B:
        allowed |= {'restore_body', 'route_a_failure'}
    if set(proof) - allowed:
        _hold('UNLISTED_ROUTE_PROOF_FIELD')
    record_id = _id(proof.get('record_id'))
    receipts = proof.get('receipts')
    required = {'create', 'initial_publish', 'original_native', 'edit',
        'initial_edit_native', 'metadata_put', 'after_put_native', 'publish', 'final_native'}
    if route == ROUTE_B:
        required |= {'restore', 'after_restore_native'}
    if not isinstance(receipts, dict) or set(receipts) != required:
        _hold('SANDBOX_RECEIPTS_REQUIRED')
    transition = {name: receipts[name] for name in ('original_native', 'edit', 'initial_edit_native',
        'metadata_put', 'after_put_native')}
    transition['metadata_put_body'] = proof.get('metadata_put_body')
    if 'receipt_directory_order' in proof:
        transition['receipt_directory_order'] = proof['receipt_directory_order']
    original, initial, after, payload, context = _transition(transition,
        host='sandbox.zenodo.org', record_id=record_id, source_validator=source_validator,
        sandbox_qualification=True)
    create = _receipt(receipts['create'], method='POST', host='sandbox.zenodo.org', path='/api/deposit/depositions')
    if _id(create['response'].get('id')) != record_id:
        _hold('SANDBOX_CREATE_OWN_ID')
    for name in ('initial_publish', 'publish'):
        pub = _receipt(receipts[name], method='POST', host='sandbox.zenodo.org',
            path='/api/deposit/depositions/' + record_id + '/actions/publish',
            body_sha=hashlib.sha256(b'{}').hexdigest())
        if _id(pub['response'].get('id')) != record_id:
            _hold('SANDBOX_PUBLISH_OWN_ID')
    ordered = ['create', 'initial_publish', 'original_native', 'edit', 'initial_edit_native',
        'metadata_put', 'after_put_native']
    references = [(deepcopy(ref), True) for ref in receipts.values()]
    references += [(deepcopy(proof_reference), False), (deepcopy(proof['metadata_put_body']), False)]
    if route == ROUTE_B:
        references += _route_a_failure(proof.get('route_a_failure'), source_validator)
        restore_body = _pinned(proof.get('restore_body'))
        _exact(json.loads(restore_body), managed_pid_payload(original, after), 'RESTORE_BODY_NOT_EXACT_HELPER_OUTPUT')
        restore = _receipt(receipts['restore'], method='PUT', host='sandbox.zenodo.org',
            path='/api/records/' + record_id + '/draft', native=True,
            body_sha=hashlib.sha256(restore_body).hexdigest())
        if _id(restore['response'].get('id')) != record_id:
            _hold('RESTORE_RESPONSE_OWN_ID')
        restored = _record(receipts['after_restore_native'], host='sandbox.zenodo.org', record_id=record_id, draft=True)
        expected = deepcopy(after); expected['pids'] = deepcopy(original['pids'])
        require_public_pids(restored, original)
        _source_check(source_validator, 'AFTER_NATIVE_RESTORE', restored, expected, context)
        ordered += ['restore', 'after_restore_native']
        references.append((deepcopy(proof['restore_body']), False))
    ordered += ['publish', 'final_native']
    _sequence([receipts[name] for name in ordered], proof.get('receipt_directory_order'))
    final = _record(receipts['final_native'], host='sandbox.zenodo.org', record_id=record_id)
    require_public_pids(final, original)
    expected = _expected_metadata(original, payload)
    _source_check(source_validator, 'FINAL_PUBLIC', final, expected, context)
    return RouteQualification(route, proof_reference['path'], proof_reference['sha256'],
        transport_contract_sha256(), tuple(references), _QUALIFIED_MARKER)


@dataclass(frozen=True)
class DraftOAIState:
    status: str
    route: str | None
    publication_allowed: bool
    original_pids: dict
    current_draft: dict
    qualification: RouteQualification | None


def classify_own_draft(actual, original, *, host, record_id, operation='AMENDMENT',
        phase='DRAFT', transition_evidence=None, qualification=None,
        source_validator=None, current_public=None):
    """Narrow comparison projection; no public PID exemption and no mutation.

    Caller must independently validate the current full draft against the saved
    after-PUT baseline; this function invokes that callback as CURRENT_DRAFT.
    With no PID difference it returns the normal path without an extra PUT.
    """
    record_id = _id(record_id)
    if host not in ('zenodo.org', 'sandbox.zenodo.org') or operation != 'AMENDMENT' or phase != 'DRAFT':
        _hold('TRANSIENT_OWN_AMENDMENT_DRAFT_SCOPE_ONLY')
    if _id(actual.get('id')) != record_id or _id(original.get('id')) != record_id or actual.get('is_draft') is not True:
        _hold('CURRENT_OWN_UNPUBLISHED_DRAFT_REQUIRED')
    if not isinstance(actual.get('pids'), dict) or not isinstance(original.get('pids'), dict) or not original['pids']:
        _hold('ORIGINAL_NONEMPTY_PIDS_OBJECT_REQUIRED')
    if _bytes(actual.get('pids')) == _bytes(original.get('pids')):
        return DraftOAIState('NORMAL_EXACT_PIDS', None, True, deepcopy(original['pids']), deepcopy(actual), None)
    if not isinstance(qualification, RouteQualification):
        _hold('SANDBOX_PROVEN_ROUTE_REQUIRED')
    qualification.require_current()
    saved_original, initial, after, payload, context = _transition(transition_evidence,
        host=host, record_id=record_id, source_validator=source_validator)
    require_public_pids(original, saved_original)
    if not isinstance(current_public, dict):
        _hold('CURRENT_UNCHANGED_PUBLIC_READBACK_REQUIRED')
    require_public_pids(current_public, saved_original)
    _source_check(source_validator, 'UNCHANGED_PUBLIC', current_public, saved_original, context)
    _omission(saved_original, initial, actual, record_id)
    _source_check(source_validator, 'CURRENT_DRAFT', actual, after, context)
    route = qualification.route
    return DraftOAIState('TRANSIENT_OAI_ROUTE_A_READY' if route == ROUTE_A else 'DRAFT_PID_REPAIR_REQUIRED',
        route, route == ROUTE_A, deepcopy(saved_original['pids']), deepcopy(actual), qualification)


def require_publish_ready(state, actual):
    """Caller preflight: never publish an unqualified/pending or changed draft."""
    if not isinstance(state, DraftOAIState) or state.publication_allowed is not True:
        _hold('PUBLISH_PROHIBITED_PENDING_ROUTE_OR_RESTORE')
    if state.qualification is not None:
        state.qualification.require_current()
    _exact(actual, state.current_draft, 'DRAFT_CHANGED_SINCE_PREFLIGHT')
    return {'status': state.status, 'publication_allowed': True, 'public_pids_must_remain_exact': True}


def require_exact_restoration(state, restored, *, restore_evidence, restore_body_reference,
        restored_native_evidence, host, record_id, source_validator):
    """Route B only: qualify exact own native restore before any publish."""
    if not isinstance(state, DraftOAIState) or state.route != ROUTE_B or state.status != 'DRAFT_PID_REPAIR_REQUIRED':
        _hold('EXACT_NATIVE_RESTORE_ROUTE_B_ONLY')
    state.qualification.require_current()
    record_id = _id(record_id)
    original = {'id': record_id, 'pids': state.original_pids}
    body = _pinned(restore_body_reference)
    _exact(json.loads(body), managed_pid_payload(original, state.current_draft), 'RESTORE_BODY_NOT_EXACT_HELPER_OUTPUT')
    receipt = _receipt(restore_evidence, method='PUT', host=host,
        path='/api/records/' + record_id + '/draft', native=True,
        body_sha=hashlib.sha256(body).hexdigest())
    if _id(receipt['response'].get('id')) != record_id:
        _hold('RESTORE_RESPONSE_OWN_ID')
    saved = _record(restored_native_evidence, host=host, record_id=record_id, draft=True)
    _sequence([restore_evidence, restored_native_evidence])
    _exact(restored, saved, 'RESTORED_SNAPSHOT_NOT_SAVED_RECEIPT')
    require_public_pids(restored, original)
    expected = deepcopy(state.current_draft); expected['pids'] = deepcopy(state.original_pids)
    _source_check(source_validator, 'AFTER_NATIVE_RESTORE', restored, expected,
        {'host': host, 'record_id': record_id, 'operation': 'AMENDMENT', 'phase': 'DRAFT'})
    return DraftOAIState('RESTORED_EXACT_PIDS_ROUTE_B_READY', ROUTE_B, True,
        deepcopy(state.original_pids), deepcopy(restored), state.qualification)
