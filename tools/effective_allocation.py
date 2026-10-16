"""Closed, read-only projection of the exact approved Run-183 row correction.

An explicit overlay pin and current ledger CAS are mandatory. This module
assigns no license, scientific verdict, publication authority or installation.
Original proposal bytes are never changed. Consumers must revalidate the view
immediately before their own separately authorized write boundary.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat

STANDARD = 'VRS-EFFECTIVE-ALLOCATION-PROJECTION-1'
OVERLAY_NAME = 'APPROVED_ALLOCATION_CORRECTION_20261016.json'
OVERLAY_SHA256 = '9a25d095f1fecbf591e1f26e91af9fc5856f9b62e76296a09ddd2773d19da921'
LOCAL_BINDING_NAME = 'LOCAL_RELEASE_BINDING_AUTHORIZATION_20261016.json'
LOCAL_BINDING_SHA256 = '53eefdfcb2b242f02a83564b895721e8bbc180ee4c1df11fb02c56afd7d4982f'
LOCAL_DECISIONS_SHA256 = '5c0ff7e4bf6d563266455fa8ab0df158a42baa8056dd5678198585b5a04a5af2'
AUTHORITY_SHA256 = 'd0429a8b2885d6716db80d8981f9758ee3cfd53cb35d80d7fc9d89045ca88ee0'
LINKED_PROPOSAL_SHA256 = '2f63c06ca7964103f9cf5784f4b7bd60f1e73b45e045efdd03fa94bcf7c108ab'
ORIGINALS = {
    'Run-177': '290860184267124c6bc7f716e3a8ef591836c832c89a02047886ad4eef4856ae',
    'Run-183': '3c6c883796aab54c14062f9e905c375fd705faa547779a18c2930692a6ddbe1d',
}
SCIENCE = {
    'canon_product_route_sha256': ('CANON_PRODUCT_ROUTE.json', '036eef44b8d53aba1c870672bf5cd785fbc236ffe846f612ffb17ba0b8d5a47f'),
    'finalized_package_sha256': ('FINALIZED_PACKAGE.json', '3059a4ab9d31a8c255ec9a7bbf47eb654e11aef6e110239d527a9b7bc9f98a56'),
    'lean_zero_sorry_certificate_sha256': ('LEAN_ZERO_SORRY_CERTIFICATE.json', '5639a01baf4a4dcc5e491aed25c39bfa802213fd94376ffb2681040e3625c07e'),
    'paper_package_manifest_sha256': ('PAPER_PACKAGE_MANIFEST.json', '89e099d772762343db11652770041f55ced629ee8feb22c24d7984370f992bbc'),
    'paper_pdf_sha256': ('paper.pdf', 'b5f135cb9ba2b5a1aabb89ecf7cbbdbcfd33a5f418f4f0e49769261067add539'),
    'post_review_sha256': ('POST_ARISTOTLE_REVIEW.json', '19938cee3733770a640c4bb517e8e6d477693d8104896da8683dd45888d69ba0'),
}
OVERLAY_FIELDS = {'standard','run_id','old_proposed_row','approved_local_row','run177_row_unchanged',
    'original_proposal','authority','scientific_evidence','publication_authorized',
    'installed_router_consumes_this_overlay','global_reservation_collision','original_proposal_unchanged'}
AUTHORITY_FIELDS = {'schema','at_utc','human_source','source_text','proposal_path','proposal_sha256',
    'approved','run183_row','run177_row','scientific_evidence_changes_authorized',
    'publication_authorized','original_packets_preserved'}
LOCAL_BINDING_FIELDS = {'standard','run_id','approved_ledger_row','license','authority',
    'original_approved_proposal','promotion_authorized','publication_authorized','publication_status',
    'row_correction_authority','scientific_evidence','source_manifest_unchanged'}
MAX_BYTES = 32 * 1024 * 1024


class AllocationHold(ValueError):
    pass


def need(value, reason):
    if not value:
        raise AllocationHold('HOLD_EFFECTIVE_ALLOCATION_' + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def closed(value, fields, reason):
    need(isinstance(value, dict) and set(value) == fields, reason)
    return value


def positive_row(value):
    need(type(value) is int and value > 0, 'POSITIVE_INTEGER_ROW')
    return value


def safe_path(value):
    need(isinstance(value, (str, Path)), 'REGULAR_PATH')
    path = Path(value).absolute()
    need('..' not in path.parts and not any(p.is_symlink() for p in (path, *path.parents)), 'REGULAR_PATH')
    return path


def frame(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def regular(path):
    path = safe_path(path)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            before = os.fstat(descriptor)
            need(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_BYTES, 'REGULAR_INPUT')
            def read():
                chunks = []; size = 0
                while size <= MAX_BYTES:
                    data = os.read(descriptor, min(1024 * 1024, MAX_BYTES + 1 - size))
                    if not data:
                        break
                    size += len(data); chunks.append(data)
                return b''.join(chunks)
            raw = read(); os.lseek(descriptor, 0, os.SEEK_SET); repeated = read()
            after = os.fstat(descriptor); final = path.lstat()
            need(raw == repeated and len(raw) == before.st_size and frame(before) == frame(after) == frame(final), 'READ_RACE')
            safe_path(path)
            return raw, frame(final)
        finally:
            os.close(descriptor)
    except OSError:
        raise AllocationHold('HOLD_EFFECTIVE_ALLOCATION_REGULAR_INPUT') from None


def document(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            need(key not in value, 'DUPLICATE_JSON_KEY'); value[key] = item
        return value
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda value: need(False, 'FINITE_JSON'))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise AllocationHold('HOLD_EFFECTIVE_ALLOCATION_JSON') from None
    need(isinstance(value, dict), 'JSON_OBJECT')
    return value


def proposal_inventory(root):
    safe_path(root)
    return tuple(sorted(safe_path(p) for p in root.glob('Run-*/RELEASE_BINDING_PROPOSAL.json')))


class AllocationView:
    def __init__(self, root, paths):
        self.root, self.paths = root, paths
        self._reads = {}; self._proposals = {}; self._originals = {}; self.correction = None; self.ledger_path = None

    def read(self, path, expected=None):
        path = safe_path(path); raw, observed = regular(path)
        if expected is not None:
            need(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected) is not None and sha(raw) == expected, 'EXACT_INPUT_HASH')
        if path in self._reads:
            need(self._reads[path] == (raw, observed), 'INPUT_RACE')
        self._reads[path] = (raw, observed)
        return raw

    def revalidate(self):
        need(proposal_inventory(self.root) == self.paths, 'RESERVATION_SET_RACE')
        for path, value in self._reads.items():
            need(regular(path) == value, 'INPUT_RACE')
        need(proposal_inventory(self.root) == self.paths, 'RESERVATION_SET_RACE')
        return self.receipt()

    @property
    def proposals(self):
        return deepcopy(self._proposals)

    def original_proposal(self, run_id):
        need(run_id in self._originals, 'PROPOSAL_REQUIRED')
        return deepcopy(self._originals[run_id])

    def revalidate_after_ledger_write(self, expected_afterimage):
        # A reconciler may have just performed its separately authorized ledger
        # write. Verify that exact owned afterimage, retaining the original CAS
        # in provenance, while every immutable allocation input remains exact.
        need(type(expected_afterimage) is bytes and self.ledger_path in self._reads, 'OWNED_LEDGER_AFTERIMAGE')
        need(proposal_inventory(self.root) == self.paths, 'RESERVATION_SET_RACE')
        for path, value in self._reads.items():
            observed = regular(path)
            need(observed[0] == expected_afterimage if path == self.ledger_path else observed == value, 'INPUT_RACE')
        need(proposal_inventory(self.root) == self.paths, 'RESERVATION_SET_RACE')
        return self.receipt()

    def proposal(self, run_id):
        need(run_id in self._proposals, 'PROPOSAL_REQUIRED')
        return deepcopy(self._proposals[run_id])

    @property
    def input_bindings(self):
        return {str(path): sha(value[0]) for path, value in sorted(self._reads.items())}

    def receipt(self):
        return {'standard': STANDARD, 'effective_rows': {run: p.get('proposed_ledger_row') for run,p in sorted(self._proposals.items())},
                'original_rows': {run: p.get('proposed_ledger_row') for run,p in sorted(self._originals.items())},
                'input_sha256': self.input_bindings, 'correction': deepcopy(self.correction),
                'original_proposals_unchanged': True, 'publication_authorized': False,
                'license_authorized': False, 'certifies': False}


def apply_correction(view, binding, ledger_path, expected_ledger_sha256):
    closed(binding, {'path','sha256'}, 'EXPLICIT_OVERLAY_BINDING')
    overlay_path = view.root / 'Run-183' / OVERLAY_NAME
    need(safe_path(binding['path']) == overlay_path and binding['sha256'] == OVERLAY_SHA256, 'EXACT_APPROVED_OVERLAY')
    overlay = document(view.read(overlay_path, binding['sha256']))
    closed(overlay, OVERLAY_FIELDS, 'CLOSED_OVERLAY')
    need(overlay['standard'] == 'VRS-APPROVED-LINKED-ALLOCATION-CORRECTION-1' and overlay['run_id'] == 'Run-183', 'OVERLAY_IDENTITY')
    need(type(overlay['old_proposed_row']) is int and overlay['old_proposed_row'] == 147
         and type(overlay['approved_local_row']) is int and overlay['approved_local_row'] == 148
         and type(overlay['run177_row_unchanged']) is int and overlay['run177_row_unchanged'] == 147, 'ONLY_183_147_TO_148')
    need(overlay['publication_authorized'] is False and overlay['installed_router_consumes_this_overlay'] is False
         and overlay['original_proposal_unchanged'] is True
         and overlay['global_reservation_collision'] == 'HOLD_UNTIL_REVIEWED_SHARED_ALLOCATION_RESOLVER', 'LOCAL_ONLY_OVERLAY')
    original = closed(overlay['original_proposal'], {'path','sha256','exists'}, 'ORIGINAL_BINDING')
    need(original['exists'] is True and safe_path(original['path']) == view.root/'Run-183/RELEASE_BINDING_PROPOSAL.json'
         and original['sha256'] == ORIGINALS['Run-183'], 'ORIGINAL_183_BINDING')
    for run, expected in ORIGINALS.items():
        path = view.root/run/'RELEASE_BINDING_PROPOSAL.json'
        value = document(view.read(path, expected))
        need(value == view._originals.get(run) and value.get('run_id') == run
             and type(value.get('proposed_ledger_row')) is int and value['proposed_ledger_row'] == 147
             and value.get('status') == 'READY_FOR_EXACT_AUTHORIZATION', 'UNCHANGED_ORIGINAL_PROPOSAL')
    authority_binding = closed(overlay['authority'], {'path','sha256'}, 'AUTHORITY_BINDING')
    need(authority_binding['sha256'] == AUTHORITY_SHA256, 'EXACT_AUTHORITY_PIN')
    authority = document(view.read(authority_binding['path'], AUTHORITY_SHA256))
    closed(authority, AUTHORITY_FIELDS, 'CLOSED_AUTHORITY')
    need(authority['schema'] == 'VRS-JUSTIN-ROW-CORRECTION-AUTHORITY-1' and authority['approved'] is True
         and type(authority['run183_row']) is int and authority['run183_row'] == 148
         and type(authority['run177_row']) is int and authority['run177_row'] == 147
         and authority['scientific_evidence_changes_authorized'] is False and authority['publication_authorized'] is False
         and authority['original_packets_preserved'] is True and authority['proposal_sha256'] == LINKED_PROPOSAL_SHA256
         and authority['source_text'] == 'Yes, use row148 for Run-183', 'EXACT_HUMAN_SCOPE')
    view.read(authority['proposal_path'], LINKED_PROPOSAL_SHA256)
    rows = overlay['scientific_evidence']; need(isinstance(rows,list) and len(rows) == len(SCIENCE), 'SIX_SCIENCE_BINDINGS')
    seen = set()
    for row in rows:
        closed(row, {'exists','expected_sha256','field','matches','path','sha256'}, 'CLOSED_SCIENCE_BINDING')
        key = row['field']; need(key in SCIENCE and key not in seen, 'UNIQUE_SCIENCE_ROLES'); seen.add(key)
        name, expected = SCIENCE[key]
        need(row['exists'] is True and row['matches'] is True and safe_path(row['path']) == view.root/'Run-183'/name
             and row['sha256'] == row['expected_sha256'] == expected
             and view._originals['Run-183'].get('evidence',{}).get(key) == expected, 'EXACT_SCIENCE_BINDING')
        view.read(row['path'], expected)
    need(seen == set(SCIENCE), 'ALL_SCIENCE_ROLES')
    local_path = view.root/'Run-183'/LOCAL_BINDING_NAME
    local = closed(document(view.read(local_path, LOCAL_BINDING_SHA256)), LOCAL_BINDING_FIELDS, 'CLOSED_LOCAL_BINDING')
    need(local['standard'] == 'VRS-LOCAL-RELEASE-BINDING-AUTHORIZATION-1' and local['run_id'] == 'Run-183'
         and type(local['approved_ledger_row']) is int and local['approved_ledger_row'] == 148
         and local['license'] == 'cc-by-4.0' and local['promotion_authorized'] is False
         and local['publication_authorized'] is False and local['source_manifest_unchanged'] is True
         and local['publication_status'] == 'HOLD_EXACT_PUBLICATION_AUTHORIZATION'
         and local['original_approved_proposal'] == original and local['row_correction_authority'] == authority_binding
         and local['scientific_evidence'] == rows, 'EXACT_LOCAL_BINDING_SCOPE')
    local_authority = closed(local['authority'], {'path','sha256'}, 'LOCAL_DECISIONS_BINDING')
    need(local_authority['sha256'] == LOCAL_DECISIONS_SHA256, 'EXACT_LOCAL_DECISIONS_PIN')
    view.read(local_authority['path'], LOCAL_DECISIONS_SHA256)
    need(ledger_path is not None and expected_ledger_sha256 is not None, 'CURRENT_LEDGER_CAS_REQUIRED')
    view.ledger_path = safe_path(ledger_path)
    need(view.ledger_path == view.root.parent.parent/'ZENODO_SUBMISSION_LEDGER.md', 'CURRENT_ROOT_LEDGER_ROLE')
    ledger = view.read(view.ledger_path, expected_ledger_sha256).decode('utf-8')
    occupied = []
    ledger_numbers = []
    for line in ledger.splitlines():
        if not re.match(r'^\|\s*[0-9]+\s*\|',line):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        number = positive_row(int(cells[0])); ledger_numbers.append(number)
        if number == 148:
            occupied.append(cells)
    need(len(occupied) <= 1, 'UNIQUE_CURRENT_ROW148')
    if occupied:
        cells = occupied[0]
        original_proposal = view._originals['Run-183']
        need(len(cells) == 9 and cells[2] == '**' + original_proposal['abbreviation'] + ' — ' + original_proposal['title'] + '**'
             and cells[3] == 'nightly Run-183', 'ROW148_SAME_SCIENTIFIC_IDENTITY')
    view.authoritative_max = max([view.authoritative_max,*ledger_numbers],default=0)
    projected = deepcopy(view._proposals['Run-183']); projected['proposed_ledger_row'] = 148
    view._proposals['Run-183'] = projected
    view.correction = {'run_id':'Run-183','original_proposed_row':147,'effective_row':148,
        'original_proposal':deepcopy(original),'overlay':deepcopy(binding),'authority':deepcopy(authority_binding),
        'scientific_evidence':deepcopy(rows),'ledger_sha256':expected_ledger_sha256,
        'local_binding':{'path':str(local_path),'sha256':LOCAL_BINDING_SHA256},
        'local_decisions_authority':deepcopy(local_authority),'publication_authorized':False}


def resolve(finalized_root, reconciliation_surface, *, correction=None, ledger_path=None, expected_ledger_sha256=None):
    root = safe_path(finalized_root); paths = proposal_inventory(root); view = AllocationView(root,paths)
    need(safe_path(reconciliation_surface) == root.parent/'PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json', 'RECONCILIATION_SURFACE_ROLE')
    surface = document(view.read(reconciliation_surface))
    maximum = surface.get('authoritative_ledger_max_row_observed',0)
    need(type(maximum) is int and maximum >= 0, 'AUTHORITATIVE_MAXIMUM')
    view.authoritative_max = maximum
    records = surface.get('records',[]); need(isinstance(records,list), 'PUBLIC_RESERVATIONS')
    need(all(isinstance(row,dict) and 'proposed_ledger_row' in row for row in records), 'PUBLIC_RESERVATION_ROWS')
    view.public_rows = tuple(sorted(positive_row(row['proposed_ledger_row']) for row in records))
    for path in paths:
        proposal = document(view.read(path)); run = proposal.get('run_id')
        need(isinstance(run,str) and re.fullmatch(r'Run-[0-9]{3,}',run) is not None and path.parent.name == run and run not in view._proposals, 'UNIQUE_PROPOSAL_IDENTITY')
        if 'proposed_ledger_row' in proposal or proposal.get('status') == 'READY_FOR_EXACT_AUTHORIZATION':
            positive_row(proposal.get('proposed_ledger_row'))
        view._originals[run] = deepcopy(proposal); view._proposals[run] = deepcopy(proposal)
    if correction is not None:
        apply_correction(view,correction,ledger_path,expected_ledger_sha256)
    else:
        need(expected_ledger_sha256 is None, 'EXPLICIT_OVERLAY_REQUIRED')
        if ledger_path is not None:
            view.ledger_path = safe_path(ledger_path); view.read(view.ledger_path)
    rows = [positive_row(value['proposed_ledger_row']) for value in view._proposals.values() if value.get('status') == 'READY_FOR_EXACT_AUTHORIZATION']
    need(len(set([*view.public_rows,*rows])) == len([*view.public_rows,*rows]), 'GLOBAL_RESERVATION_COLLISION')
    view.proposal_rows = tuple(sorted(rows))
    view.revalidate()
    return view
