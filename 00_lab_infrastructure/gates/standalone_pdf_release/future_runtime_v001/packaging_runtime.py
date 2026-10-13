"""Closed additive packaging profile over the unchanged science runtime.

No installation, source rewrite, cached PASS, proof execution or publication.
The old runtime consumer must freshly admit the actual live predecessor before
this profile can admit its own merged additive source and exact user scope.
"""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import types

STANDARD = 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-1'
STATUS = 'INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS'
USER_DIRECTIVE = 'make sure all our deposits have the actual papers as separate PDFs and make that standard for future releases'

# Pre-execution trust roots are the genuine unchanged predecessor artifacts,
# never bindings supplied by a release config or a caller-selected profile.
LEGACY_CLOSURE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/typography-runtime-install-v001/CURRENT_RUNTIME_CLOSURE.json', 'sha256': '48ee958633d781244b52065540c813dbb436d7272353448ddebb838ab9f6e429'}
LEGACY_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/runtime_successor.py', 'sha256': 'b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'}
LEGACY_SCOPE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/publication-preparation-v003/CURRENT_SOURCE_SCOPE.json', 'sha256': '84eaef87c142ae3b588c8c534836311b3c051b35b94f1b8b91690bbda22a0a15'}
SESSION_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/prepare_first_seven_plan.py', 'sha256': 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'}
PROVIDER_SHA = 'fb57aeaf4a43f0183043d12c28ed02a2ce326f452b8a596f1231a29d98123f0b'
PROFILE_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/CURRENT_PACKAGING_PROFILE.json'
NOMINATION_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/INSTALLATION_NOMINATION.json'

GIT_PREFIX = '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v001/'
MODULE_NAMES = frozenset({
    'packaging_runtime.py', 'invoke_digest_v2.py', 'digest_controller_v2.py',
    'methods_digest_v2.py', 'methods_digest_registration_v3.py',
    'manuscript_access_registry.py', 'manuscript_access_correction.py',
    'manuscript_pdf_gate.py',
    'publish_dated_bundles_guarded.py', 'publish_successor_wave_guarded.py',
    'packaging_catalog.py', 'install_packaging_runtime.py',
    'packaging_nightly.py', 'nightly_checkpoint_guarded.py',
    'packaging_run_flow.py', 'packaging_nightly_coverage.py',
    'packaging_nightly_intake.py',
})
REQUIRED_CHECKS = frozenset({
    'report-only-consumers', 'verify-catalog', 'verify-functions', 'verify',
    'deposit-verify', 'lean-build-current', 'lean-build-p0', 'gitleaks',
    'standalone-manuscript-pdf',
})
PROFILE_FIELDS = {
    'standard', 'status', 'canonical_root', 'installed_at_utc', 'user_authority',
    'legacy_closure', 'legacy_consumer', 'legacy_scope', 'source_session_consumer', 'modules',
    'source_origin', 'source_review', 'access_registry', 'default_routes',
}
DEFAULT_ROUTES = {
    'digest': 'invoke_digest_v2.py',
    'dated_publisher': 'publish_dated_bundles_guarded.py',
    'successor_publisher': 'publish_successor_wave_guarded.py',
    'catalog': 'packaging_catalog.py',
    'nightly': 'packaging_nightly.py',
    'checkpoint': 'packaging_nightly.py checkpoint',
    'coverage': 'packaging_nightly.py health',
    'cycle': 'packaging_nightly.py cycle',
    'intake': 'packaging_nightly.py intake',
}


class PackagingHold(ValueError):
    pass


def need(value, reason):
    if not value:
        raise PackagingHold('HOLD_PACKAGING_' + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(root, binding):
    need(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}
         and isinstance(binding['path'], str)
         and re.fullmatch('[0-9a-f]{64}', str(binding['sha256'])), 'CLOSED_BINDING')
    root = Path(root).resolve(strict=True)
    p = Path(binding['path']); p = p if p.is_absolute() else root / p
    need('..' not in p.parts and p.resolve(strict=True).is_relative_to(root)
         and p.is_file() and not any(q.is_symlink() for q in (p, *p.parents)), 'REGULAR_CONTAINED_SOURCE')
    first = p.stat(); raw = p.read_bytes(); last = p.stat()
    need((first.st_ino, first.st_mtime_ns, first.st_size) == (last.st_ino, last.st_mtime_ns, last.st_size)
         and sha(raw) == binding['sha256'], 'SOURCE_HASH_OR_RACE')
    return p.resolve(strict=True), raw


def object_at(root, binding):
    path, raw = read(root, binding); value = json.loads(raw)
    need(isinstance(value, dict), 'BOUND_OBJECT')
    return path, raw, value


def load(root, binding, name):
    path, raw = read(root, binding)
    module = types.ModuleType(name); module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    need(read(root, binding)[1] == raw, 'SOURCE_LOAD_RACE')
    return module


def source_proof(root, value, modules, *, required_checks=REQUIRED_CHECKS):
    """Require real merged PR, merge commit and complete Git tree observations."""
    need(isinstance(value, dict) and set(value) == {'pull_request', 'merge_commit', 'tree'}, 'SOURCE_ORIGIN')
    observations = {k: object_at(root, b)[2] for k, b in value.items()}
    pr = observations['pull_request']; commit = observations['merge_commit']; tree = observations['tree']
    oid = pr.get('mergeCommit', {}).get('oid')
    need(pr.get('state') == 'MERGED' and pr.get('baseRefName') == 'main'
         and pr.get('url') == 'https://github.com/jdhart81/viridis-canon/pull/' + str(pr.get('number'))
         and re.fullmatch('[0-9a-f]{40}', str(oid)) and commit.get('sha') == oid
         and tree.get('sha') == commit.get('tree', {}).get('sha') and tree.get('truncated') is False,
         'GENUINE_COMPLETE_MERGED_SOURCE')
    checks = pr.get('statusCheckRollup')
    need(isinstance(checks, list) and checks
         and all(isinstance(c, dict) and c.get('status') == 'COMPLETED'
                 and c.get('conclusion') in {'SUCCESS', 'SKIPPED'} for c in checks)
         and required_checks <= {c.get('name') for c in checks if c.get('conclusion') == 'SUCCESS'}, 'REQUIRED_SOURCE_CI')
    rows = tree.get('tree'); need(isinstance(rows, list), 'COMPLETE_GIT_TREE')
    by_path = {r.get('path'): r for r in rows if isinstance(r, dict)}
    need(len(by_path) == len(rows), 'UNIQUE_GIT_TREE_PATHS')
    proofs = []
    for row in modules:
        path, raw = read(root, {'path': row['path'], 'sha256': row['sha256']})
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        git_row = by_path.get(row['git_path'], {})
        need(git_row.get('type') == 'blob' and git_row.get('mode') == '100644'
             and git_row.get('sha') == blob, 'EXACT_MERGED_BLOB:' + row['name'])
        proofs.append({'name': row['name'], 'path': str(path), 'sha256': sha(raw),
                       'git_path': row['git_path'], 'git_blob_sha': blob})
    return {'merge_commit': oid, 'proofs': proofs}


def module_table(root, rows):
    need(isinstance(rows, list) and len(rows) == len(MODULE_NAMES)
         and all(isinstance(r, dict) and set(r) == {'name', 'path', 'sha256', 'git_path'} for r in rows)
         and {r['name'] for r in rows} == MODULE_NAMES
         and len({r['path'] for r in rows}) == len(rows), 'CLOSED_ADDITIVE_MODULES')
    pins = []
    for row in rows:
        path, raw = read(root, {'path': row['path'], 'sha256': row['sha256']})
        need(path.name == row['name'] and row['git_path'] == GIT_PREFIX + row['name'], 'CANONICAL_SOURCE_NAME')
        pins.append({k: row[k] for k in ('name', 'path', 'sha256')})
    return pins


def same_binding(root, actual, expected):
    """Compare normalized immutable bindings without executing either source."""
    p, _ = read(root, actual); q, _ = read(root, expected)
    return p == q and actual['sha256'] == expected['sha256']


def nominated_binding(root):
    """The operational default resolves only the root installation nomination."""
    root=Path(root).resolve(strict=True);p=root/NOMINATION_PATH
    need(p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)), 'INSTALLED_DEFAULT_NOMINATION_REQUIRED')
    first=p.read_bytes();value=json.loads(first)
    need(isinstance(value,dict)and isinstance(value.get('profile'),dict),'INSTALLED_DEFAULT_PROFILE_BINDING')
    profile=value['profile'];require_nomination(root,profile)
    need(p.read_bytes()==first,'DEFAULT_NOMINATION_RACE')
    return profile


def require_nomination(root, profile_binding):
    root = Path(root).resolve(strict=True)
    expected = root / PROFILE_PATH
    path, _ = read(root, profile_binding)
    need(expected.is_file() and path == expected.resolve(strict=True), 'CANONICAL_INSTALLED_PROFILE_PATH')
    nomination_path = root / NOMINATION_PATH
    need(nomination_path.is_file() and not any(p.is_symlink() for p in (nomination_path,*nomination_path.parents)), 'CANONICAL_INSTALLATION_NOMINATION')
    raw = nomination_path.read_bytes(); nomination = json.loads(raw)
    need(set(nomination) == {'standard','status','profile','installer_source','merged_source_commit','root_review_receipt'}
         and nomination['standard'] == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-1'
         and nomination['status'] == 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and same_binding(root,nomination['profile'],profile_binding)
         and re.fullmatch('[0-9a-f]{40}',str(nomination['merged_source_commit'])), 'ROOT_REVIEWED_INSTALLED_NOMINATION')
    # These are immutable root installation evidence inputs, not executable code.
    read(root,nomination['installer_source']); read(root,nomination['root_review_receipt'])
    need(nomination_path.read_bytes() == raw, 'INSTALLATION_NOMINATION_RACE')
    return nomination


def require_installed_plan(root, profile, nomination, proof):
    """Root review binds the actual exclusive install plan and merged modules.

    An unrelated review receipt or merely self-recorded installer hash cannot
    nominate a different module table, registry, authority or merged source.
    """
    plan_path=Path(root)/Path(PROFILE_PATH).parent/'INSTALL_PLAN.json'
    need(plan_path.is_file()and not any(p.is_symlink()for p in(plan_path,*plan_path.parents)), 'ACTUAL_EXCLUSIVE_INSTALL_PLAN')
    raw=plan_path.read_bytes();plan=json.loads(raw)
    fields={'standard','status','canonical_root','source_modules','source_origin','source_review',
            'user_authority','access_registry','restore_publisher','installed_at_utc','root_review'}
    need(set(plan)==fields and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-1'
         and plan['status']=='ROOT_REVIEWED_READY_NOT_INSTALLED'and plan['canonical_root']==str(root), 'CLOSED_INSTALLED_PLAN')
    for field in ('source_origin','source_review','user_authority','access_registry','installed_at_utc'):
        need(plan[field]==profile[field],'INSTALLED_PLAN_PROFILE_BINDING:'+field)
    need(plan['root_review']==nomination['root_review_receipt'], 'NOMINATED_ACTUAL_ROOT_REVIEW')
    rows=plan['source_modules'];module_table(root,rows)
    expected={r['name']:{k:r[k]for k in('name','sha256','git_path')}for r in rows}
    actual={r['name']:{k:r[k]for k in('name','sha256','git_path')}for r in profile['modules']}
    need(expected==actual,'INSTALLED_AND_REVIEWED_MODULE_ROWS')
    for row in profile['modules']:
        need(Path(row['path']).resolve(strict=True)==(Path(root)/Path(PROFILE_PATH).parent/row['name']).resolve(strict=True),
             'CANONICAL_INSTALLED_MODULE_PATH')
    installer=next(r for r in rows if r['name']=='install_packaging_runtime.py')
    need(same_binding(root,nomination['installer_source'],{k:installer[k]for k in('path','sha256')}),
         'NOMINATED_PROVED_EXECUTED_INSTALLER')
    review=object_at(root,plan['root_review'])[2]
    need(set(review)=={'standard','status','reviewer','plan_projection_sha256','merged_source_commit',
                       'source_hashes','historical_restore_sha256','scientific_or_authority_changes'}
         and review['standard']=='VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-1'
         and review['status']=='EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS'
         and isinstance(review['reviewer'],str)and review['reviewer']
         and review['plan_projection_sha256']==sha((json.dumps({k:v for k,v in plan.items()if k!='root_review'},sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
         and review['merged_source_commit']==proof['merge_commit']==nomination['merged_source_commit']
         and review['source_hashes']=={r['name']:r['sha256']for r in rows}
         and review['historical_restore_sha256']=='4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94'
         and review['scientific_or_authority_changes']is False, 'ROOT_REVIEW_EXACT_INSTALLED_PLAN_AND_SOURCE')
    need(plan_path.read_bytes()==raw,'INSTALLED_PLAN_RACE')


@contextlib.contextmanager
def builder_source_scope(root,profile,pins):
    builder=load(root,SESSION_CONSUMER,'_exact_packaging_approved_builder')
    with builder.source_session(root,pins):
        yield


def validate(root, profile_binding, *, purpose_pins=None):
    root = Path(root).resolve(strict=True)
    nomination = require_nomination(root, profile_binding)
    _, profile_raw, profile = object_at(root, profile_binding)
    need(set(profile) == PROFILE_FIELDS and profile['standard'] == STANDARD
         and profile['status'] == STATUS and profile['canonical_root'] == str(root)
         and profile['default_routes'] == DEFAULT_ROUTES, 'CLOSED_INSTALLED_PROFILE')
    installed = dt.datetime.fromisoformat(profile['installed_at_utc'].replace('Z', '+00:00'))
    need(installed.tzinfo is not None and installed <= dt.datetime.now(dt.timezone.utc), 'INSTALLATION_TIME')
    _, authority_raw, authority = object_at(root, profile['user_authority'])
    need(set(authority) == {'standard', 'source', 'user_text', 'captured_at_utc', 'scientific_scope_changes', 'provider_instruction'}
         and authority['standard'] == 'VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1'
         and authority['source'] == 'Current user message in this Codex chat'
         and authority['user_text'] == USER_DIRECTIVE
         and authority['scientific_scope_changes'] is False, 'EXACT_PACKAGING_USER_AUTHORITY')
    _, provider_raw, provider = object_at(root,authority['provider_instruction'])
    need(sha(provider_raw) == PROVIDER_SHA
         and provider.get('standard') == 'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1'
         and provider.get('provider_tool') == 'mcp__codex_app__read_thread'
         and provider.get('thread_id') == '01a12d47-02a3-78f3-beb4-6b8e1a079dd2'
         and provider.get('user_messages') == [{'type':'userMessage','id':'01a132f6-4708-7440-a9ba-ebf03deeb906','content':[{'type':'text','text':USER_DIRECTIVE+'\n'}]}], 'ACTUAL_PROVIDER_PACKAGING_AUTHORITY')
    captured = dt.datetime.fromisoformat(authority['captured_at_utc'].replace('Z', '+00:00'))
    need(captured.tzinfo is not None and captured <= installed, 'AUTHORITY_TIME')

    # Re-consume the actual installed predecessor first. A changed historical
    # publisher, registrar or science file holds here; a saved PASS never wins.
    for field, anchor in (('legacy_closure',LEGACY_CLOSURE),('legacy_consumer',LEGACY_CONSUMER),
                          ('legacy_scope',LEGACY_SCOPE),('source_session_consumer',SESSION_CONSUMER)):
        need(same_binding(root,profile[field],anchor),'UNCHANGED_PREEXEC_ANCHOR:'+field)
    # Read and prove the complete old source tables before exec-loading any
    # consumer. Crafted contained sources cannot run even if later checks HOLD.
    saved = object_at(root,LEGACY_CLOSURE)[2]
    legacy_pins = saved.get('source_pins')
    need(isinstance(legacy_pins, list) and legacy_pins, 'ACTUAL_LEGACY_SOURCE_TABLE')
    _, _, scope = object_at(root, profile['legacy_scope'])
    base_pins = scope.get('purpose_source_pins')
    need(isinstance(base_pins, list) and base_pins and scope.get('canonical_root') == str(root)
         and same_binding(root,scope.get('source_session_consumer'),SESSION_CONSUMER)
         and same_binding(root,scope.get('current_runtime_closure'),LEGACY_CLOSURE)
         and same_binding(root,scope.get('runtime_consumer'),LEGACY_CONSUMER), 'ORIGINAL_MEASURED_PURPOSE_SCOPE')
    need(len({r.get('name') for r in base_pins}) == len(base_pins)
         and len({r.get('path') for r in base_pins}) == len(base_pins)
         and all(r in base_pins for r in legacy_pins), 'COMPLETE_UNCHANGED_BASE_PURPOSE_PINS')
    for row in base_pins:
        need(isinstance(row, dict) and set(row) == {'name', 'path', 'sha256'}, 'BASE_PIN_SCHEMA')
        read(root, {'path': row['path'], 'sha256': row['sha256']})
    origin = scope.get('source_origin', {})
    old_rows = origin.get('source_rows')
    need(isinstance(old_rows, list) and len(old_rows) == len(base_pins)
         and all({k: r.get(k) for k in ('name','path','sha256')} in base_pins for r in old_rows), 'BASE_SOURCE_ORIGIN_ROWS')
    source_proof(root, {'pull_request': origin['merged_pr'], 'merge_commit': origin['merged_commit'],
                       'tree': origin['merged_tree']}, old_rows,
                 required_checks=REQUIRED_CHECKS - {'standalone-manuscript-pdf'})
    for name, anchor in (('runtime_successor.py',LEGACY_CONSUMER),('prepare_first_seven_plan.py',SESSION_CONSUMER)):
        selected=[r for r in base_pins if r['name']==name]
        need(len(selected)==1 and same_binding(root,{k:selected[0][k] for k in ('path','sha256')},anchor),'BASE_EXECUTABLE_ANCHOR:'+name)
    # All executable loads below have now been proved against hard-bound base
    # receipts and their actual merged Git blobs.
    legacy = load(root,LEGACY_CONSUMER,'_exact_packaging_legacy_closure')
    need(legacy.read_bound_closure(LEGACY_CLOSURE)==saved,'ACTUAL_LEGACY_CLOSURE_READ')
    legacy_paths = {r['path']: r['sha256'] for r in base_pins}
    additional = module_table(root, profile['modules'])
    need(not ({r['name'] for r in base_pins} & MODULE_NAMES)
         and not (set(legacy_paths) & {r['path'] for r in additional}), 'ADDITIVE_ONLY_NAMESPACE')
    combined = sorted([*base_pins, *additional], key=lambda r: r['name'])
    if purpose_pins is not None:
        need(isinstance(purpose_pins, list) and sorted(purpose_pins,key=lambda r:r['name']) == combined,
             'EXACT_PURPOSE_ORIGINAL_AND_ADDITIVE')
    view_rows = [r for r in base_pins if r['name'] == 'runtime_closure_view.py']
    need(len(view_rows) == 1, 'ORIGINAL_MEASURED_VIEW_CONSUMER')
    view = load(root, {k:view_rows[0][k] for k in ('path','sha256')}, '_exact_packaging_runtime_view')
    # Prove the additive source before importing any new executable module.
    proof = source_proof(root, profile['source_origin'], profile['modules'])
    _, review_raw, review = object_at(root, profile['source_review'])
    hashes = {r['name']: r['sha256'] for r in profile['modules']}
    need(set(review) == {'standard', 'status', 'reviewer', 'source_hashes', 'legacy_closure',
                        'scientific_admission_changed', 'historical_sources_changed',
                        'review_scope', 'actual_live_runtime_admission', 'actual_seven_record_admission'}
         and review['standard'] == 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-1'
         and review['status'] == 'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS'
         and isinstance(review['reviewer'], str) and review['reviewer']
         and review['source_hashes'] == hashes and review['legacy_closure'] == profile['legacy_closure']
         and review['scientific_admission_changed'] is False
         and review['historical_sources_changed'] is False
         and review['review_scope'] == 'SOURCE_ONLY'
         and review['actual_live_runtime_admission'] is False
         and review['actual_seven_record_admission'] == 'PENDING_POST_INSTALL_FRESH_READBACK', 'EXACT_INDEPENDENT_SOURCE_REVIEW')
    require_installed_plan(root,profile,nomination,proof)
    ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_raw=ledger_path.read_bytes();ledger=json.loads(ledger_raw)
    # V3 records cannot be replayed by the original v1-only full-population
    # convenience function. Its unchanged current_closure/helper and selector
    # are still consumed in the exact original 99-source view; then the exact
    # original population comparator checks the completed v1+v3 replay.
    v3_bindings=set()
    for row in ledger.get('publication_entities',[]):
        binding=row.get('registration_receipt')
        if binding is not None and object_at(root,binding)[2].get('standard')=='VRS-METHODS-DIGEST-REGISTRATION-3':
            v3_bindings.add(json.dumps(binding,sort_keys=True))
    ordinary={**ledger,'publication_entities':[r for r in ledger.get('publication_entities',[])
                  if json.dumps(r.get('registration_receipt'),sort_keys=True)not in v3_bindings]}
    with view.exact_runtime_view(root,combined,legacy_pins):
        current=legacy.current_closure(Path(profile['legacy_closure']['path']).parent if Path(profile['legacy_closure']['path']).is_absolute()
                    else(root/profile['legacy_closure']['path']).parent,saved['protected_readback'])
        need(current==saved and current.get('certifies')is False,'ACTUAL_UNCHANGED_LEGACY_SOURCE_AND_HELPER_CLOSURE')
        import importlib
        corpus=importlib.import_module('corpus_ledger')
        original_scan=corpus.build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=ordinary)
        baseline=legacy.baseline_rows((root/LEGACY_CLOSURE['path']).parent)
        legacy.preserving_population(ordinary,baseline,original_scan)
    # The purpose finder below admits only the exact already merged modules.
    # Saved scientific replay is local; live access/labels are a separate,
    # explicit real-owner RegistryContext check in the operational dispatcher.
    with builder_source_scope(root,profile,combined):
        import importlib
        catalog=importlib.import_module('packaging_catalog')
        full_scan=catalog.saved_scientific_population(root,ledger,original_scan)
        legacy.preserving_population(ledger,baseline,full_scan)
    need(ledger_path.read_bytes()==ledger_raw,'ACTUAL_SCIENCE_POPULATION_RACE')
    need(proof['merge_commit']==nomination['merged_source_commit'],'INSTALLED_NOMINATED_MERGE')
    _, registry_raw = read(root, profile['access_registry'])
    need(read(root, profile_binding)[1] == profile_raw
         and read(root, profile['user_authority'])[1] == authority_raw
         and read(root, authority['provider_instruction'])[1] == provider_raw
         and read(root, profile['source_review'])[1] == review_raw
         and read(root, profile['access_registry'])[1] == registry_raw, 'FINAL_PROFILE_INPUT_RACE')
    for row in combined:
        read(root, {'path': row['path'], 'sha256': row['sha256']})
    return {'status': 'ACTUAL_LEGACY_AND_ADDITIVE_PACKAGING_PROFILE_PASS',
            'legacy_closure': profile['legacy_closure'], 'source_pins': combined,
            'merged_source': proof, 'access_registry': profile['access_registry'],
            'default_routes': DEFAULT_ROUTES, 'certifies': False,
            'ssot_writes': 0, 'zenodo_writes': 0}


@contextlib.contextmanager
def session(root, profile_binding):
    """The sole default v2 dispatch scope; prove entry and exit, no cache bypass."""
    result = validate(root, profile_binding)
    profile = object_at(root, profile_binding)[2]
    builder = load(root, profile['source_session_consumer'], '_exact_packaging_session_builder')
    with builder.source_session(root, result['source_pins']):
        validate(root, profile_binding, purpose_pins=result['source_pins'])
        yield result
        validate(root, profile_binding, purpose_pins=result['source_pins'])


if __name__ == '__main__':
    raise SystemExit('Explicit source-bound default entry required; no automatic installation.')
