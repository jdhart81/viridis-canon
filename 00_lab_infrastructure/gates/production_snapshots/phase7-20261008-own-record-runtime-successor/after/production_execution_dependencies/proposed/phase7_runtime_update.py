"""Closed, approved Phase-7 runtime successors; never verification evidence."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
STANDARD = 'VRS-PHASE7-AUTHORIZED-RUNTIME-UPDATE-1'
APPROVED_AUDIT_SECTION_SHA256 = '0b90da9172c726cef65de5905fb289b79ec2367d0117b012f8ad74b324441390'
APPROVED_AUDIT_APPENDICES = (
    ('## Phase 7 Gate 3 resolution: decouple probes from witnesses — 2026-10-07 (evening)', 'ba56d7254744843b9e7512b61f0d80161cf33b366f076d516aa451ba21c8325a'),
    ('## SIMPLIFICATION — weekly push restored — 2026-10-07 (Justin directive; supersedes conflicting Phase 7 items)', '483fddbd90eb1782911db43de477c161d35214fd033061a83a87b9dec503652a'),
)
SELECTOR_SHA256 = '9f243a1025498ca03e22b0c94a711165d21554037ea434abe6cb9720ff8fbd07'
CORPUS_SHA256 = 'bfd2ec16c1e9c39ebcd39fdb45ccf9683b6864a95d3496109df49f9a7639a173'
GATE_PREFIX = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/'
SELECTOR_TARGETS = {GATE_PREFIX + 'corpus_ledger.py', GATE_PREFIX + 'nightly_coverage.py'}
GUARD_SHA256 = 'fd9a4fe406445f3181391ca83f462c4889fb3392c4c93d5ac0d54838c223484f'
CLOSEOUT_SHA256 = '9663c006df997e368373f64e0f10e324661893d7b9246ea92a6c8dfec0b7ec3b'
PREVIOUS_SELECTOR_RECEIPT_SHA256 = '02957fbd6ea67e02e7e6979a06f0d07d4e3d46be6dbe8b783b847fb9ba9192b9'
PREVIOUS_SELECTOR_MERGE_COMMIT = 'cb76d964121878031f2693f56cd21908d291b1d5'
POLICY_TARGETS = SELECTOR_TARGETS | {GATE_PREFIX + 'premise_declaration.py', GATE_PREFIX + 'publication_gate.py', GATE_PREFIX + 'doi_audit.py'}
PUBLICATION_ORIGINAL_SHA256 = 'a44fe11deccc4d1246d4d2b0fc53621807e1f06061eafff1fb684615fcff7fef'
PUBLICATION_SCOPED_SHA256 = '6c4f4506df1de812101dc5b97efdfbd0ed3d3bb3c5681266fa470474a119c30c'
DOI_AUDIT_SHA256 = '23173076f35f62ca0696544c3a5c7ee2bcf7bc39a8a649390ec8e616c2c06f29'
PUBLIC_READER_SHA256 = 'e731c8d61741d53caca7f627f0d400c8238c15fb57bf2bf9b23fc38d0d2ceca7'
POLICY_MODULE_NAMES = frozenset({'PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json', 'closeout_streak.py', 'digest_metadata.py', 'digest_public_state.py', 'digest_public_state_legacy_b5545.py', 'digest_successor_state.py', 'digest_weekly_state.py', 'first_digest_state.py', 'inv9_dependency_scope.py', 'inv9_title_basis.py', 'methods_digest.py', 'methods_digest_registration.py', 'methods_digest_registration_legacy_0fc739.py', 'nightly_minimal_policy.py', 'nonvacuity_tier0.py', 'own_record_comparison.py', 'phase7_audit_policy.py', 'phase7_claim_label_render.py', 'phase7_mutation_baseline.py', 'phase7_policy_versions.py', 'phase7_runtime_update.py', 'probe_observations.py', 'public_metadata_readback.py', 'registration_imports.py', 'scoped_release.py'})
POLICY_VERSION_NAMES = frozenset({'phase7_audit_policy.py', 'PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json', 'phase7_claim_label_render.py', 'nonvacuity_tier0.py', 'probe_observations.py', 'inv9_dependency_scope.py', 'methods_digest.py', 'publication_gate.py'})
PROFILES = {'RUN187_SELECTOR': SELECTOR_TARGETS, 'PHASE7_SCOPED_POLICY': POLICY_TARGETS}
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
    from phase7_policy_versions import normalize_authority_plan
    raw = normalize_authority_plan(raw)
    header = '## Phase 7 — Claude audit of release packet v002 — 2026-10-07'.encode()
    if raw.count(header) != 1:
        raise ValueError('unique approved audit section required')
    start = raw.index(header)
    end = raw.find(b'\n## ', start + len(header))
    section = raw[start:] if end < 0 else raw[start:end]
    suffix = b'\n---\n'
    if section.endswith(suffix) and hashlib.sha256(section[:-len(suffix)]).hexdigest() == APPROVED_AUDIT_SECTION_SHA256:
        # The current plan appends this exact separator to the immutable old
        # approval. Only the two already approved, byte-pinned appendices can
        # explain it; arbitrary whitespace or a changed approval never can.
        previous_appendix_start = start
        for title, expected in APPROVED_AUDIT_APPENDICES:
            appendix_header = title.encode()
            if raw.count(appendix_header) != 1:
                raise ValueError('unique exact approved authority appendix required')
            appendix_start = raw.index(appendix_header)
            if appendix_start <= previous_appendix_start:
                raise ValueError('approved authority appendices must follow the audit in order')
            previous_appendix_start = appendix_start
            appendix_end = raw.find(b'\n## ', appendix_start + len(appendix_header))
            appendix = raw[appendix_start:] if appendix_end < 0 else raw[appendix_start:appendix_end]
            if hashlib.sha256(appendix).hexdigest() != expected:
                raise ValueError('approved authority appendix bytes differ')
        return section[:-len(suffix)]
    return section

def _function_body_bytes(raw, node):
    lines = raw.splitlines(keepends=True)
    first, last = node.body[0], node.body[-1]
    if first.lineno == last.end_lineno:
        return lines[first.lineno-1][first.col_offset:last.end_col_offset]
    return b''.join([lines[first.lineno-1][first.col_offset:], *lines[first.lineno:last.end_lineno-1], lines[last.end_lineno-1][:last.end_col_offset]])

def _preserved_functions(old_raw, new_raw, renamed):
    old=ast.parse(old_raw);new=ast.parse(new_raw)
    old_functions={n.name:n for n in old.body if isinstance(n,ast.FunctionDef)}
    new_functions={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
    if len(new_functions)!=sum(isinstance(n,ast.FunctionDef)for n in new.body):raise ValueError('duplicate successor callable')
    reports=[]
    for name,node in old_functions.items():
        target=renamed.get(name,name);fresh=new_functions.get(target)
        if fresh is None or ast.dump(node.args,include_attributes=False)!=ast.dump(fresh.args,include_attributes=False) or (ast.dump(node.returns,include_attributes=False)if node.returns is not None else None)!=(ast.dump(fresh.returns,include_attributes=False)if fresh.returns is not None else None):raise ValueError('original callable signature changed: '+name)
        if [ast.dump(v,include_attributes=False)for v in node.decorator_list]!=[ast.dump(v,include_attributes=False)for v in fresh.decorator_list]:raise ValueError('original callable decorator changed')
        before=_function_body_bytes(old_raw,node);after=_function_body_bytes(new_raw,fresh)
        if before!=after:raise ValueError('selector or legacy body changed: '+name)
        reports.append({'name':name,'successor_name':target,'body_sha256':hashlib.sha256(before).hexdigest()})
    return old,new,old_functions,new_functions,reports

def module_preservation(old_raw,new_raw,baseline_sha,renamed,extras):
    if hashlib.sha256(old_raw).hexdigest()!=baseline_sha:raise ValueError('exact approved module baseline required')
    old,new,old_functions,new_functions,reports=_preserved_functions(old_raw,new_raw,renamed)
    remaining=[ast.dump(n,include_attributes=False)for n in old.body if not isinstance(n,ast.FunctionDef)];additions=[]
    for node in new.body:
        if isinstance(node,ast.FunctionDef):continue
        dumped=ast.dump(node,include_attributes=False)
        if remaining and dumped==remaining[0]:remaining.pop(0)
        else:additions.append(node)
    def allowed_import(n):
        if isinstance(n,ast.Import):return len(n.names)==1 and n.names[0].name=='methods_digest_registration' and n.names[0].asname is None
        return isinstance(n,ast.ImportFrom) and n.module=='methods_digest_registration' and n.level==0 and all(a.name!='*'for a in n.names)
    if remaining or any(not allowed_import(n)for n in additions):raise ValueError('original module semantics changed outside named registry import')
    protected_names=set(old_functions)
    for node in old.body:
        if isinstance(node,(ast.Import,ast.ImportFrom)):protected_names.update(a.asname or (a.name.split('.')[0]if isinstance(node,ast.Import)else a.name)for a in node.names)
        elif isinstance(node,ast.Assign):protected_names.update(t.id for t in node.targets if isinstance(t,ast.Name))
    if any((a.asname or a.name)in protected_names for n in additions for a in n.names):raise ValueError('new registry import shadows historical authority')
    if set(new_functions)-{v['successor_name']for v in reports}!=set(extras):raise ValueError('closed registry dispatch callable set required')
    for original,alias in renamed.items():
        wrapper=new_functions.get(original)
        if wrapper is None or ast.dump(wrapper.args,include_attributes=False)!=ast.dump(old_functions[original].args,include_attributes=False) or wrapper.decorator_list:raise ValueError('closed registry wrapper signature required')
    return {'status':'ORIGINAL_SELECTOR_AND_LEGACY_BODIES_IDENTICAL','baseline_sha256':baseline_sha,'functions':reports}

def corpus_preservation(old_raw,new_raw):
    # The original selector/legacy bodies stay protected by their existing
    # exact baseline. Only the tested import caller may wrap the old registry
    # dispatcher; its alias, body and signature are separately byte-pinned.
    tree = ast.parse(new_raw)
    functions = {n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    alias_name = '_preserve_publication_registrations_source_original'
    extras = {'preserve_publication_registrations'}
    namespace = alias_name in functions
    if namespace:
        extras.add(alias_name)
    report = module_preservation(old_raw,new_raw,CORPUS_SHA256,{'preserve_publication_registrations':'_preserve_publication_registrations_legacy'},extras)
    original = next(n for n in ast.parse(old_raw).body if isinstance(n,ast.FunctionDef) and n.name == 'preserve_publication_registrations')
    expected = {'preserve_publication_registrations':'a1f8d99c93e4d88fede85b47dd241124bc1503ea47916198e1e38139f795d028'}
    if namespace:
        expected = {
            alias_name:'a1f8d99c93e4d88fede85b47dd241124bc1503ea47916198e1e38139f795d028',
            'preserve_publication_registrations':'25191bd9ad9f9ff7bfb00a9ce92173555e56d1da00a503ee883e15123942d94e',
        }
    for name, body_sha in expected.items():
        node = functions[name]
        if ast.dump(node.args,include_attributes=False) != ast.dump(original.args,include_attributes=False) or (ast.dump(node.returns,include_attributes=False) if node.returns is not None else None) != (ast.dump(original.returns,include_attributes=False) if original.returns is not None else None) or node.decorator_list:
            raise ValueError('exact import caller/alias signature required')
        if hashlib.sha256(_function_body_bytes(new_raw,node)).hexdigest() != body_sha:
            raise ValueError('exact approved import caller/alias body required')
    guard_test = ast.dump(ast.parse("__name__ == '__main__'",mode='eval').body,include_attributes=False)
    guards = [n for n in tree.body if isinstance(n,ast.If) and ast.dump(n.test,include_attributes=False) == guard_test]
    if len(guards) != 1 or any(functions[name].lineno >= guards[0].lineno for name in expected):
        raise ValueError('exact import caller must precede the original CLI guard')
    if namespace:
        report['registry_import_caller'] = {'status':'EXACT_ORIGINAL_ALIAS_AND_APPROVED_NAMESPACE_WRAPPER','body_sha256':expected}
    return report

def publication_preservation(original_raw,scoped_raw,new_raw):
    if hashlib.sha256(original_raw).hexdigest()!=PUBLICATION_ORIGINAL_SHA256:raise ValueError('exact original publication baseline required')
    report=module_preservation(scoped_raw,new_raw,PUBLICATION_SCOPED_SHA256,{'evaluate_publication':'_evaluate_publication_scoped_legacy'},{'evaluate_publication','_evaluate_publication_original_legacy'})
    *_,original_reports=_preserved_functions(original_raw,new_raw,{'evaluate_publication':'_evaluate_publication_original_legacy'})
    return {'scoped':report,'original_default':{'status':'ORIGINAL_SELECTOR_AND_LEGACY_BODIES_IDENTICAL','baseline_sha256':PUBLICATION_ORIGINAL_SHA256,'functions':original_reports}}

def policy_catalog_closure(root, binding, current_policy_sha):
    """Prove every explicit installed archive against its own tested merged PR."""
    seen = {}
    def read(value):
        path = _bound(root, value); raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != value['sha256']:
            raise ValueError('version source changed during read')
        seen[str(path)] = value['sha256']
        return path, raw
    _, raw = read(binding); catalog = json.loads(raw)
    if not isinstance(catalog, dict) or set(catalog) != {'standard','status','tree_root','versions'} or catalog['standard'] != 'VRS-PHASE7-POLICY-VERSIONS-1' or catalog['status'] != 'MERGED_SOURCE_CATALOG' or catalog['tree_root'] != str(root):
        raise ValueError('closed installed version catalog required')
    versions = catalog['versions']
    if not isinstance(versions, list) or not versions:
        raise ValueError('explicit nonempty approved version catalog required')
    identities = [v.get('execution_consumer_sha256') for v in versions if isinstance(v,dict)]
    if len(identities) != len(versions) or any(not isinstance(v,str) or re.fullmatch('[0-9a-f]{64}',v) is None for v in identities) or len(set(identities)) != len(identities) or identities.count(current_policy_sha) != 1:
        raise ValueError('current exact policy and unique archived versions required')
    origins = {}; pinned = {}
    for entry in versions:
        if set(entry) != {'execution_consumer_sha256','files','pull_request_readback'}:
            raise ValueError('closed version authority entry required')
        version = entry['execution_consumer_sha256']; _, pr_raw = read(entry['pull_request_readback']); pr = json.loads(pr_raw)
        if pr.get('state') != 'MERGED' or pr.get('baseRefName') != 'main' or pr.get('url') != 'https://github.com/jdhart81/viridis-canon/pull/' + str(pr.get('number')) or not re.fullmatch('[0-9a-f]{40}', str(pr.get('mergeCommit',{}).get('oid'))):
            raise ValueError('own merged archive source PR required')
        checks = pr.get('statusCheckRollup')
        if not isinstance(checks,list) or not REQUIRED_CHECKS <= {v.get('name') for v in checks if isinstance(v,dict) and v.get('status') == 'COMPLETED' and v.get('conclusion') == 'SUCCESS'} or any(not isinstance(v,dict) or v.get('status') != 'COMPLETED' or v.get('conclusion') not in {'SUCCESS','SKIPPED'} for v in checks):
            raise ValueError('archive source repository checks incomplete')
        files = pr.get('files'); mapping = {v.get('path'):v for v in files if isinstance(v,dict)} if isinstance(files,list) else {}
        if not mapping or len(mapping) != len(files):
            raise ValueError('unique complete merged archive blob readback required')
        rows = entry['files']
        if not isinstance(rows,list) or len(rows) != len(POLICY_VERSION_NAMES) or any(not isinstance(v,dict) or set(v) != {'name','binding','git_path'} for v in rows) or {v.get('name') for v in rows} != POLICY_VERSION_NAMES:
            raise ValueError('exact closed eight-file archive required')
        values = {}
        for row in rows:
            name = row['name']; rel = GATE_PREFIX+'policy_versions/'+version+'/'+name
            if not isinstance(row['binding'],dict) or set(row['binding']) != {'path','sha256'} or row['binding'].get('path') != rel or row['git_path'] != '00_lab_infrastructure/gates/policy_versions/'+version+'/'+name:
                raise ValueError('explicit hash directory and own Git path required')
            _, content = read(row['binding'])
            blob = hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
            if mapping.get(row['git_path'],{}).get('sha') != blob:
                raise ValueError('installed archive differs from own merged Git blob')
            values[name] = content; origins[rel] = mapping; pinned[rel] = row['binding']['sha256']
        if hashlib.sha256(values['phase7_audit_policy.py']).hexdigest() != version:
            raise ValueError('archived implementation SHA differs from version identity')
        pins = re.findall(r"^CONTRACT_SHA='([0-9a-f]{64})'$", values['phase7_audit_policy.py'].decode(),re.M)
        if pins != [hashlib.sha256(values['PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json']).hexdigest()]:
            raise ValueError('archived implementation/data pin differs')
    for path, expected in seen.items():
        if sha(path) != expected:
            raise ValueError('catalog source changed before return')
    return {'origins':origins,'pinned':pinned,'seen':seen,'versions':identities,'binding':binding}

def validate(root, ledger, original_receipt, *, now=None):
    root = Path(root).resolve(strict=True)
    now = now or dt.datetime.now(dt.timezone.utc)
    wrapper = json.loads(_bound(root, ledger.get('enforcement_activation')).read_bytes())
    reference = wrapper.get('authorized_runtime_update')
    receipt_path = _bound(root, reference)
    r = json.loads(receipt_path.read_bytes())
    fields = {'standard', 'status', 'profile', 'tree_root', 'installed_at_utc', 'original_activation', 'original_after_manifest', 'audit_section', 'pull_request_readback', 'selector_pull_request_readback', 'runtime_targets', 'additional_modules', 'protected_readback'}
    policy = r.get('profile') == 'PHASE7_SCOPED_POLICY'
    if policy:
        fields |= {'previous_runtime_update','publication_gate_scoped_baseline','public_metadata_readback_baseline','policy_version_catalog'}
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
    previous_files = None
    previous = None
    if policy:
        prior_path = _bound(root, r['previous_runtime_update'])
        if r['previous_runtime_update']['sha256'] != PREVIOUS_SELECTOR_RECEIPT_SHA256:
            raise ValueError('exact installed selector predecessor required')
        previous = json.loads(prior_path.read_bytes())
        prior_fields = fields - {'previous_runtime_update','publication_gate_scoped_baseline','public_metadata_readback_baseline','policy_version_catalog'}
        if set(previous) != prior_fields or previous.get('standard') != STANDARD or previous.get('status') != 'INSTALLED_HASH_READBACK_PASS' or previous.get('profile') != 'RUN187_SELECTOR' or previous.get('tree_root') != str(root):
            raise ValueError('closed selector predecessor required')
        for key in ('original_activation', 'original_after_manifest', 'audit_section', 'selector_pull_request_readback'):
            if previous[key] != r[key]:
                raise ValueError('runtime successor changes original selector authority')
            _bound(root, previous[key])
        previous_installed = dt.datetime.fromisoformat(previous['installed_at_utc'].replace('Z', '+00:00'))
        if previous_installed.tzinfo is None or not previous_installed <= installed:
            raise ValueError('runtime successor precedes its selector predecessor')
        previous_pr = json.loads(_bound(root, previous['pull_request_readback']).read_bytes())
        if previous_pr.get('number') != 57 or previous_pr.get('state') != 'MERGED' or previous_pr.get('baseRefName') != 'main' or previous_pr.get('url') != 'https://github.com/jdhart81/viridis-canon/pull/57' or previous_pr.get('mergeCommit', {}).get('oid') != PREVIOUS_SELECTOR_MERGE_COMMIT:
            raise ValueError('exact merged selector bookkeeping PR required')
        previous_checks = previous_pr.get('statusCheckRollup')
        if not isinstance(previous_checks, list) or not previous_checks or any(c.get('status') != 'COMPLETED' or c.get('conclusion') not in {'SUCCESS', 'SKIPPED'} for c in previous_checks) or not REQUIRED_CHECKS <= {c.get('name') for c in previous_checks if c.get('conclusion') == 'SUCCESS'}:
            raise ValueError('selector predecessor PR checks incomplete')
        prior_files = previous_pr.get('files')
        if not isinstance(prior_files, list) or not prior_files or any(not isinstance(v, dict) for v in prior_files):
            raise ValueError('complete predecessor PR file readback required')
        previous_files = {v.get('path'): v for v in prior_files}
        if len(previous_files) != len(prior_files) or pr.get('number') in {55, 57} or pr.get('mergeCommit', {}).get('oid') == PREVIOUS_SELECTOR_MERGE_COMMIT:
            raise ValueError('distinct own merged policy PR required')
        # The exact archival receipt pins prior sources; never revalidate its old
        # helper against the newly installed helper, or mutate the old receipt.
        prior_targets = previous['runtime_targets']
        if not isinstance(prior_targets, list) or len(prior_targets) != 22 or len({v.get('path') for v in prior_targets}) != 22:
            raise ValueError('exact prior selector target set required')
        for v in prior_targets:
            if set(v) != {'path', 'before_sha256', 'after_sha256', 'source'}:
                raise ValueError('closed archived selector target required')
            _bound(root, v['source'])
        prior_modules = previous['additional_modules']
        if not isinstance(prior_modules, list) or len(prior_modules) != 2 or {v.get('path') for v in prior_modules} != {GATE_PREFIX+'phase7_runtime_update.py', GATE_PREFIX+'closeout_streak.py'}:
            raise ValueError('closed prior selector reporting modules required')
        for v in prior_modules:
            if set(v) != {'path', 'sha256', 'source'}:
                raise ValueError('closed archived selector module required')
            _bound(root, v['source'])
        _bound(root, previous['protected_readback'])
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
            source_files = (pr_files if policy else selector_files) if v['path'] == GATE_PREFIX + 'corpus_ledger.py' else (previous_files if policy and v['path'] == GATE_PREFIX + 'nightly_coverage.py' else pr_files)
            if source_files.get(gitpath, {}).get('sha') != blob:
                raise ValueError('runtime source not exact own merged Git blob')
    if changed != PROFILES[r['profile']]:
        raise ValueError('unapproved runtime target change')
    if not policy and actual[GATE_PREFIX + 'corpus_ledger.py'] != CORPUS_SHA256:
        raise ValueError('selector core differs from approved merged bytes')
    _bound(root, {'path': GATE_PREFIX + 'certificate_selection.py', 'sha256': SELECTOR_SHA256})
    if policy:
        if actual[GATE_PREFIX + 'nightly_coverage.py'] != GUARD_SHA256:
            raise ValueError('policy update changes the approved selector guard')
        prior_by_path = {v['path']: v for v in previous['runtime_targets']}
        if set(prior_by_path) != set(base) or any(v['before_sha256'] != base[v['path']] or sha(_bound(root, v['source'])) != v['after_sha256'] for v in previous['runtime_targets']):
            raise ValueError('selector predecessor original targets/sources differ')
        if prior_by_path[GATE_PREFIX+'nightly_coverage.py']['after_sha256'] != GUARD_SHA256 or prior_by_path[GATE_PREFIX+'corpus_ledger.py']['after_sha256'] != CORPUS_SHA256:
            raise ValueError('approved predecessor core/guard differs')
        old_corpus = _bound(root, prior_by_path[GATE_PREFIX+'corpus_ledger.py']['source']).read_bytes()
        new_corpus = _bound(root, {'path':GATE_PREFIX+'corpus_ledger.py','sha256':actual[GATE_PREFIX+'corpus_ledger.py']}).read_bytes()
        preservation = {'corpus':corpus_preservation(old_corpus, new_corpus)}
        original_publication=_bound(root,prior_by_path[GATE_PREFIX+'publication_gate.py']['source']).read_bytes()
        scoped_publication=_bound(root,r['publication_gate_scoped_baseline']).read_bytes()
        publication_source=_bound(root,{'path':GATE_PREFIX+'publication_gate.py','sha256':actual[GATE_PREFIX+'publication_gate.py']}).read_bytes()
        preservation['publication']=publication_preservation(original_publication,scoped_publication,publication_source)
        original_doi=_bound(root,prior_by_path[GATE_PREFIX+'doi_audit.py']['source']).read_bytes()
        new_doi=_bound(root,{'path':GATE_PREFIX+'doi_audit.py','sha256':actual[GATE_PREFIX+'doi_audit.py']}).read_bytes()
        preservation['doi_audit']=module_preservation(original_doi,new_doi,DOI_AUDIT_SHA256,{'build_audit':'_build_audit_legacy'},{'build_audit'})
    version_closure = policy_catalog_closure(root, r['policy_version_catalog'], sha(root/(GATE_PREFIX+'phase7_audit_policy.py'))) if policy else None
    modules = r['additional_modules']
    allowed_modules = {GATE_PREFIX+n for n in POLICY_MODULE_NAMES} if policy else {GATE_PREFIX+'phase7_runtime_update.py', GATE_PREFIX+'closeout_streak.py'}
    if policy: allowed_modules |= set(version_closure['pinned'])
    if not isinstance(modules, list) or len(modules) != len(allowed_modules) or {v.get('path') for v in modules} != allowed_modules:
        raise ValueError('closed additional runtime module required')
    for v in modules:
        if set(v) != {'path', 'sha256', 'source'}:
            raise ValueError('closed additional source required')
        p = _bound(root, {'path': v['path'], 'sha256': v['sha256']})
        source = _bound(root, v['source'])
        blob = hashlib.sha1(b'blob ' + str(source.stat().st_size).encode() + b'\x00' + source.read_bytes()).hexdigest()
        archived = policy and v['path'] in version_closure['pinned']
        source_files = version_closure['origins'][v['path']] if archived else (previous_files if policy and p.name == 'closeout_streak.py' else pr_files)
        git_path = '00_lab_infrastructure/gates/' + (v['path'][len(GATE_PREFIX):] if archived else p.name)
        if archived and v['sha256'] != version_closure['pinned'][v['path']]:
            raise ValueError('archive additional module differs from catalog binding')
        if p.read_bytes() != source.read_bytes() or source_files.get(git_path, {}).get('sha') != blob:
            raise ValueError('additional module differs from own merged Git blob')
        if policy and p.name == 'closeout_streak.py' and v['sha256'] != CLOSEOUT_SHA256:
            raise ValueError('policy update changes approved closeout consumer')
        if policy and not archived and p.name=='public_metadata_readback.py':
            prior_reader=_bound(root,r['public_metadata_readback_baseline']).read_bytes()
            preservation['public_reader']=module_preservation(prior_reader,source.read_bytes(),PUBLIC_READER_SHA256,{'read_record':'_read_record_legacy','readback':'_readback_legacy'},{'read_record','readback'})
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
    if protected_at.tzinfo is None or not activated <= installed <= protected_at <= now:
        raise ValueError('protected readback precedes installation or is future')
    result = {'targets': actual, 'installed_at_utc': r['installed_at_utc'], 'binding': reference, 'profile': r['profile']}
    if policy:
        for path, expected in version_closure['seen'].items():
            if sha(path) != expected: raise ValueError('version closure changed before runtime return')
        result['corpus_preservation'] = preservation
        result['policy_version_catalog'] = {'binding':r['policy_version_catalog'],'versions':version_closure['versions']}
    return result

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
