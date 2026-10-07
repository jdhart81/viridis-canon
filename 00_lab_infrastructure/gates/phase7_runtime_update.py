"""Closed, approved Phase-7 runtime successors; never verification evidence."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
STANDARD = 'VRS-PHASE7-AUTHORIZED-RUNTIME-UPDATE-1'
APPROVED_AUDIT_SECTION_SHA256 = '0b90da9172c726cef65de5905fb289b79ec2367d0117b012f8ad74b324441390'
SELECTOR_SHA256 = '9f243a1025498ca03e22b0c94a711165d21554037ea434abe6cb9720ff8fbd07'
CORPUS_SHA256 = 'bfd2ec16c1e9c39ebcd39fdb45ccf9683b6864a95d3496109df49f9a7639a173'
GATE_PREFIX = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/'
SELECTOR_TARGETS = {GATE_PREFIX + 'corpus_ledger.py', GATE_PREFIX + 'nightly_coverage.py'}
PROFILES = {'RUN187_SELECTOR': SELECTOR_TARGETS}
REQUIRED_CHECKS = {'report-only-consumers', 'verify-catalog', 'verify-functions', 'verify', 'deposit-verify', 'lean-build-current', 'lean-build-p0', 'gitleaks'}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _bound(root, value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('closed runtime source binding required')
    if not isinstance(value['path'], str) or not re.fullmatch('[0-9a-f]{64}', str(value['sha256'])):
        raise ValueError('closed runtime hash/path required')
    rel = Path(value['path'])
    if rel.is_absolute() or not rel.parts or '..' in rel.parts or str(rel) != value['path']:
        raise ValueError('canonical relative runtime source required')
    p = root / rel
    if not p.resolve(strict=True).is_relative_to(root) or any((q.is_symlink() for q in [p, *p.parents] if q.is_relative_to(root))) or (not p.is_file()) or (sha(p) != value['sha256']):
        raise ValueError('runtime source hash/path differs')
    return p

def audit_section(raw):
    header = '## Phase 7 — Claude audit of release packet v002 — 2026-10-07'.encode()
    if raw.count(header) != 1:
        raise ValueError('unique approved audit section required')
    start = raw.index(header)
    end = raw.find(b'\n## ', start + len(header))
    return raw[start:] if end < 0 else raw[start:end]

def validate(root, ledger, original_receipt, *, now=None):
    root = Path(root).resolve(strict=True)
    now = now or dt.datetime.now(dt.timezone.utc)
    wrapper = json.loads(_bound(root, ledger.get('enforcement_activation')).read_bytes())
    reference = wrapper.get('authorized_runtime_update')
    receipt_path = _bound(root, reference)
    r = json.loads(receipt_path.read_bytes())
    fields = {'standard', 'status', 'profile', 'tree_root', 'installed_at_utc', 'original_activation', 'original_after_manifest', 'audit_section', 'pull_request_readback', 'selector_pull_request_readback', 'runtime_targets', 'additional_modules', 'protected_readback'}
    if set(r) != fields or r['standard'] != STANDARD or r['status'] != 'INSTALLED_HASH_READBACK_PASS' or (r['profile'] not in PROFILES) or (r['tree_root'] != str(root)):
        raise ValueError('closed approved runtime update required')
    installed = dt.datetime.fromisoformat(r['installed_at_utc'].replace('Z', '+00:00'))
    if installed.tzinfo is None or now.tzinfo is None or installed > now:
        raise ValueError('future/naive runtime update')
    if {k: v for k, v in wrapper.items() if k != 'authorized_runtime_update'} != original_receipt:
        raise ValueError('runtime wrapper modifies original activation')
    original = json.loads(_bound(root, r['original_activation']).read_bytes())
    if original != original_receipt or r['original_after_manifest'] != original['proofs']['after_manifest']:
        raise ValueError('runtime update changes original activation/manifest')
    section = _bound(root, r['audit_section']).read_bytes()
    if hashlib.sha256(section).hexdigest() != APPROVED_AUDIT_SECTION_SHA256 or audit_section((root / 'reports/verification-coverage/GAME_PLAN.md').read_bytes()) != section:
        raise ValueError('runtime update lacks exact approved audit authority')
    pr = json.loads(_bound(root, r['pull_request_readback']).read_bytes())
    if pr.get('state') != 'MERGED' or pr.get('baseRefName') != 'main' or pr.get('url') != 'https://github.com/jdhart81/viridis-canon/pull/' + str(pr.get('number')) or (not re.fullmatch('[0-9a-f]{40}', str(pr.get('mergeCommit', {}).get('oid')))):
        raise ValueError('own tested merged PR required')
    selector_pr = json.loads(_bound(root, r['selector_pull_request_readback']).read_bytes())
    if selector_pr.get('number') != 55 or selector_pr.get('state') != 'MERGED' or selector_pr.get('baseRefName') != 'main' or selector_pr.get('url') != 'https://github.com/jdhart81/viridis-canon/pull/55' or selector_pr.get('mergeCommit', {}).get('oid') != 'bd7746b8fe01a8ede95db27cd553978fb4733dbb':
        raise ValueError('approved merged selector PR differs')
    checks = pr.get('statusCheckRollup')
    if not isinstance(checks, list) or not checks or any((c.get('status') != 'COMPLETED' or c.get('conclusion') not in {'SUCCESS', 'SKIPPED'} for c in checks)) or (not REQUIRED_CHECKS <= {c.get('name') for c in checks if c.get('conclusion') == 'SUCCESS'}):
        raise ValueError('runtime PR checks incomplete')
    selector_rows = selector_pr.get('files')
    if not isinstance(selector_rows, list) or not selector_rows or any(not isinstance(v, dict) for v in selector_rows):
        raise ValueError('complete approved selector PR file readback required')
    selector_files = {v.get('path'): v for v in selector_rows}
    if len(selector_files) != len(selector_rows):
        raise ValueError('duplicate approved selector PR file readback')
    files = pr.get('files')
    pr_files = {v.get('path'): v for v in files} if isinstance(files, list) else {}
    if not pr_files or len(pr_files) != len(files):
        raise ValueError('complete own PR file readback required')
    old = json.loads(_bound(root, r['original_after_manifest']).read_bytes())
    base_rows = old['snapshots']
    if not isinstance(base_rows, list) or len(base_rows) != 22:
        raise ValueError('exact original 22 snapshot rows required')
    base = {v['relative_path']: v['after_sha256'] for v in base_rows}
    rows = r['runtime_targets']
    if not isinstance(rows, list) or len(rows) != 22 or len(base) != 22 or (len({v.get('path') for v in rows}) != 22) or ({v.get('path') for v in rows} != set(base)):
        raise ValueError('exact original 22 target set required')
    actual = {}
    changed = set()
    for v in rows:
        if set(v) != {'path', 'before_sha256', 'after_sha256', 'source'} or v['before_sha256'] != base[v['path']]:
            raise ValueError('original runtime target hash changed')
        p = _bound(root, {'path': v['path'], 'sha256': v['after_sha256']})
        source = _bound(root, v['source'])
        if source.read_bytes() != p.read_bytes():
            raise ValueError('installed runtime differs from captured merged source')
        actual[v['path']] = v['after_sha256']
        if v['before_sha256'] != v['after_sha256']:
            changed.add(v['path'])
            gitpath = '00_lab_infrastructure/gates/' + Path(v['path']).name
            blob = hashlib.sha1(b'blob ' + str(source.stat().st_size).encode() + b'\x00' + source.read_bytes()).hexdigest()
            if (selector_files if v['path'] == GATE_PREFIX + 'corpus_ledger.py' else pr_files).get(gitpath, {}).get('sha') != blob:
                raise ValueError('runtime source not exact own merged Git blob')
    if changed != PROFILES[r['profile']]:
        raise ValueError('unapproved runtime target change')
    if actual[GATE_PREFIX + 'corpus_ledger.py'] != CORPUS_SHA256:
        raise ValueError('selector core differs from approved merged bytes')
    _bound(root, {'path': GATE_PREFIX + 'certificate_selection.py', 'sha256': SELECTOR_SHA256})
    modules = r['additional_modules']
    allowed_modules={GATE_PREFIX+'phase7_runtime_update.py', GATE_PREFIX+'closeout_streak.py'}
    if not isinstance(modules, list) or len(modules) != 2 or {v.get('path') for v in modules} != allowed_modules:
        raise ValueError('closed additional runtime module required')
    for v in modules:
        if set(v) != {'path', 'sha256', 'source'}:
            raise ValueError('closed additional source required')
        p = _bound(root, {'path': v['path'], 'sha256': v['sha256']})
        source = _bound(root, v['source'])
        blob = hashlib.sha1(b'blob ' + str(source.stat().st_size).encode() + b'\x00' + source.read_bytes()).hexdigest()
        if p.read_bytes() != source.read_bytes() or pr_files.get('00_lab_infrastructure/gates/' + p.name, {}).get('sha') != blob:
            raise ValueError('additional module differs from own merged Git blob')
        if p.name == 'closeout_streak.py':
            assignments=[node.value.value for node in ast.parse(source.read_bytes()).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='INSTALLED_GUARD_SHA256' for t in node.targets) and isinstance(node.value,ast.Constant)]
            if assignments != [actual[GATE_PREFIX+'nightly_coverage.py']]:
                raise ValueError('closeout reporting pin differs from installed current guard')
    protected = json.loads(_bound(root, r['protected_readback']).read_bytes())
    prior_protected = json.loads(_bound(root, original['sources']['protected_readback']).read_bytes())
    def protected_set(value):
        rows = value.get('checks')
        if not isinstance(rows, list) or len(rows) != 22 or any(not isinstance(v, dict) for v in rows):
            raise ValueError('exact protected check rows required')
        identities = {(v.get('path'), v.get('surface')) for v in rows}
        if len(identities) != 22:
            raise ValueError('unique protected check identities required')
        if any(not isinstance(v.get('path'), str) or not re.fullmatch('[0-9a-f]{64}', str(v.get('expected_sha256'))) or v.get('match') is not True or v.get('actual_sha256') != v['expected_sha256'] for v in rows):
            raise ValueError('protected hashes differ')
        return {(v['path'], v.get('surface'), v['expected_sha256']) for v in rows}
    if protected.get('status') != 'LIVE_PROTECTED_HASH_READBACK_PASS' or protected_set(protected) != protected_set(prior_protected) or protected.get('baseline_sha256') != original['proofs']['protected_baseline']['sha256'] or any(protected.get(k) != 0 for k in ('remote_script_writes', 'restarts', 'certification_attempts')):
        raise ValueError('exact unchanged protected hash closure required')
    protected_at = dt.datetime.fromisoformat(protected['at_utc'].replace('Z', '+00:00'))
    activated = dt.datetime.fromisoformat(original['activated_at_utc'].replace('Z', '+00:00'))
    if protected_at.tzinfo is None or not activated <= protected_at <= now:
        raise ValueError('protected readback precedes activation or is future')
    return {'targets': actual, 'installed_at_utc': r['installed_at_utc'], 'binding': reference, 'profile': r['profile']}

def current_runtime_binding(root, relative, original_hash, original_receipt, *, now=None):
    root = Path(root).resolve(strict=True)
    try:
        _bound(root, {'path': relative, 'sha256': original_hash})
        return {'path': relative, 'sha256': original_hash}
    except (ValueError, FileNotFoundError):
        pass
    ledger = json.loads((root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
    v = validate(root, ledger, original_receipt, now=now)
    if relative not in v['targets']:
        raise ValueError('runtime source outside closed update')
    return {'path': relative, 'sha256': v['targets'][relative]}

def unwrap_activation(root, wrapper, *, now=None):
    root = Path(root).resolve(strict=True)
    ledger = json.loads((root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
    nominated = json.loads(_bound(root, ledger.get('enforcement_activation')).read_bytes())
    if nominated != wrapper:
        raise ValueError('runtime wrapper differs from SSOT nomination')
    reference = wrapper.get('authorized_runtime_update')
    update = json.loads(_bound(root, reference).read_bytes())
    original = json.loads(_bound(root, update['original_activation']).read_bytes())
    if set(wrapper) != set(original) | {'authorized_runtime_update'} or {k: v for k, v in wrapper.items() if k != 'authorized_runtime_update'} != original:
        raise ValueError('runtime wrapper changes original activation fields')
    validate(root, ledger, original, now=now)
    return original
