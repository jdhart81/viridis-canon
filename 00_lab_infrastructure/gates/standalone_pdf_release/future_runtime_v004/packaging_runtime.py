"""Closed additive packaging profile over the unchanged science runtime.

No installation, source rewrite, cached PASS, proof execution or publication.
The unchanged old helper freshly admits physical source/protected closure;
complete scientific population admission belongs to a fresh operational build.
Missing exact original temporary sources may be rehydrated with durable receipts.
"""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import types
import uuid
import sysconfig
import sys

STANDARD = 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-4'
STATUS = 'INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS'
USER_DIRECTIVE = 'make sure all our deposits have the actual papers as separate PDFs and make that standard for future releases'

# Pre-execution trust roots are the genuine unchanged predecessor artifacts,
# never bindings supplied by a release config or a caller-selected profile.
LEGACY_CLOSURE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/typography-runtime-install-v001/CURRENT_RUNTIME_CLOSURE.json', 'sha256': '48ee958633d781244b52065540c813dbb436d7272353448ddebb838ab9f6e429'}
LEGACY_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/runtime_successor.py', 'sha256': 'b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'}
LEGACY_SCOPE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/publication-preparation-v003/CURRENT_SOURCE_SCOPE.json', 'sha256': '84eaef87c142ae3b588c8c534836311b3c051b35b94f1b8b91690bbda22a0a15'}
SESSION_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/prepare_first_seven_plan.py', 'sha256': 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'}
PROVIDER_SHA = 'fb57aeaf4a43f0183043d12c28ed02a2ce326f452b8a596f1231a29d98123f0b'
PROFILE_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v004/CURRENT_PACKAGING_PROFILE.json'
NOMINATION_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v004/INSTALLATION_NOMINATION.json'

# The prior additive install is a source-only predecessor, not a cached runtime
# admission. Its original files and failed readback receipts stay immutable.
PREDECESSOR_PROFILE = {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/CURRENT_PACKAGING_PROFILE.json', 'sha256': '42f13247047ca4476fe8961719cc6cacb10a85b8781985b7cdb05e2e5118c38d'}
PREDECESSOR_NOMINATION = {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/INSTALLATION_NOMINATION.json', 'sha256': 'c0f5413ce14cdc0c0e8a4ab99b614c939f99b172131b1a54093b802db7ddaf59'}
PREDECESSOR_PLAN = {'path': '_ZENODO_DEPOSITS/standalone_pdf_runtime_v001/INSTALL_PLAN.json', 'sha256': '41d98540979cb646a7535c298cc4612b5f4e8707a07494c3a32cccacc3a1b2a8'}
LEGACY_TRANSIENT_SOURCES = ({'name': 'manual_99453df4.py',
  'target': '/private/tmp/phase7-public-state-runtime-installer-20261008-v003/runtime_successor.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/99453df4/runtime_successor.py',
             'sha256': '99453df4fc6f62cab92e4604765a0ca492a0ad89903a21789a292874c417db5f'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/manual_hash_checked_dependencies/99453df4/runtime_successor.py'},
 {'name': 'manual_daeb140d.py',
  'target': '/private/tmp/phase7-same-concept-runtime-successor-20261008-v001/runtime_successor.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/daeb140d/runtime_successor.py',
             'sha256': 'daeb140dc581104127f2e9eeacf6efb56f016ab381c0202a52ea67a97f183599'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/runtime_successor.py'},
 {'name': 'manual_db1273bb.py',
  'target': '/private/tmp/phase7-generic-runtime-successor-20261008-v001/runtime_successor.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/db1273bb/runtime_successor.py',
             'sha256': 'db1273bb1b345f80e41bc45f94aefa53e56a3be8d06afc28121e8404876cf0e7'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-generic-weekly-runtime/after/production_execution_dependencies/runtime_successor.py'},
 {'name': 'manual_e0ebe49d.py',
  'target': '/private/tmp/phase7-authority-import-runtime-successor-20261008-v001/runtime_successor.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/e0ebe49d/runtime_successor.py',
             'sha256': 'e0ebe49d167f886f0a159743f177a7963b188a233f03602225979051d3a961d6'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/manual_hash_checked_dependencies/e0ebe49d/runtime_successor.py'},
 {'name': 'manual_generic_prospective_catalog.py',
  'target': '/private/tmp/phase7-generic-runtime-successor-20261008-v001/generic_prospective_catalog.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/2dca14f6/generic_prospective_catalog.py',
             'sha256': '2dca14f6efceb8141aa3e2d92d2e41cf44e4ec5b318a74a02caba047304d5529'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-generic-weekly-runtime/after/production_execution_dependencies/generic_prospective_catalog.py'},
 {'name': 'manual_own_prospective_catalog.py',
  'target': '/private/tmp/phase7-own-record-runtime-successor-20261008-v005/own_prospective_catalog.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/b9dd8954/own_prospective_catalog.py',
             'sha256': 'b9dd8954b2d6a51115a96e1ed6561401de3120fa56dbbff14ce8e37e2a2bffa9'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-own-record-comparison/after/own_prospective_catalog.py'},
 {'name': 'manual_prior_content_prospective_catalog.py',
  'target': '/private/tmp/phase7-prior-content-runtime-successor-20261009-v001/prior_content_prospective_catalog.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/manual_dependencies/prior-content/prior_content_prospective_catalog.py',
             'sha256': '03402b690a77f0b9301bda37de46be84bc9996f3610a6576f9979984d6efd431'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261009-prior-content-runtime-successor/after/production_execution_dependencies/prior_content_prospective_catalog.py'},
 {'name': 'legacy_builder.py',
  'target': '/private/tmp/phase7-first-seven-plan-builder-20261007-v003/prepare_first_seven_plan.py',
  'source': {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/prepare_first_seven_plan.py',
             'sha256': 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'},
  'git_path': '00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/prepare_first_seven_plan.py'})
TRANSIENT_REHYDRATION_POLICY = {'standard': 'VRS-EXACT-LEGACY-TRANSIENT-REHYDRATION-1', 'mode': 'EXCLUSIVE_MISSING_ONLY_EXISTING_EXACT_NOOP', 'allowed_targets': [r['target'] for r in LEGACY_TRANSIENT_SOURCES]}
V001_INSTALLATION = {'profile': PREDECESSOR_PROFILE, 'nomination': PREDECESSOR_NOMINATION, 'plan': PREDECESSOR_PLAN}
V002_PROFILE = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v002/CURRENT_PACKAGING_PROFILE.json','sha256':'eac418327c9fda48ed872e5a7689487b9e2302e3f167a287b7ec9dd772faa7f9'}
V002_NOMINATION = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v002/INSTALLATION_NOMINATION.json','sha256':'b569596606b9ca44a361f7db6066f118e1ae11bf59ccaca790290c9d6d6c8075'}
V002_PLAN = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v002/INSTALL_PLAN.json','sha256':'dbd922f91728eeef73e9a50deb1ed7dcba22219df8cf1dcde86fed41465c1261'}
V002_INSTALLATION = {'profile':V002_PROFILE,'nomination':V002_NOMINATION,'plan':V002_PLAN}
V003_PROFILE = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v003/CURRENT_PACKAGING_PROFILE.json','sha256':'a22777c92707d757b7d101d36ee5b5dabd336b98dfa55d57933cd533a970479d'}
V003_NOMINATION = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v003/INSTALLATION_NOMINATION.json','sha256':'18f14e26300b25621edbe10e8f89e1319a498b8a21cfd36815d6342efb864cd4'}
V003_PLAN = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v003/INSTALL_PLAN.json','sha256':'43a7857dacd173019e0011865240e21106a0f6e4a3a5e754375884f6ac260c29'}
V003_INSTALLATION = {'profile':V003_PROFILE,'nomination':V003_NOMINATION,'plan':V003_PLAN}
PREDECESSOR_INSTALLATION = {'v001':V001_INSTALLATION,'v002':V002_INSTALLATION,'v003':V003_INSTALLATION}
PLATFORM_TIMEZONE_OBSERVATION = {'path':'reports/verification-coverage/2026-10-13/standalone-pdf-platform-timezone-v001/PLATFORM_NEW_YORK_TZIF_READBACK.json','sha256':'3bde531e08f840dab3a55ce4f492d660f48597a7e2490e13ffda7e58875ea94e'}
PLATFORM_TZ_LOGICAL = Path('/usr/share/zoneinfo/America/New_York')
PLATFORM_TZ_PHYSICAL = Path('/private/var/db/timezone/tz/2026d.1.0/zoneinfo/America/New_York')
PLATFORM_TZ_LINK_PATHS = (Path('/usr/share/zoneinfo'),Path('/var'),Path('/private/var/db/timezone/zoneinfo'))
DATA_ALIAS_OBSERVATION = {'path':'reports/verification-coverage/2026-10-13/standalone-pdf-path-alias-v001/HISTORICAL_CONTROLPLANE_ALIAS_READBACK.json','sha256':'e65f0cf031a64103fad9d059972394d7a99832fba7863a8c375434d51a1f6ca9'}
SCIENTIFIC_ALIAS_PATH = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs  2.0')
SCIENTIFIC_ALIAS_READLINK = 'Viridis Core docs 2.0'


PREDECESSOR_GIT_PREFIX = '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v001/'
LEGACY_TRANSIENT_ROOT = Path('/private/tmp')
HISTORICAL_PUBLISHER = {'path': '_ZENODO_DEPOSITS/publish_dated_bundles.py', 'sha256': '4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94'}

GIT_PREFIX = '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v004/'
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
    'predecessor_installation', 'transient_rehydration', 'data_alias_observation', 'platform_timezone_observation',
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


def module_table(root, rows, *, git_prefix=GIT_PREFIX):
    need(isinstance(rows, list) and len(rows) == len(MODULE_NAMES)
         and all(isinstance(r, dict) and set(r) == {'name', 'path', 'sha256', 'git_path'} for r in rows)
         and {r['name'] for r in rows} == MODULE_NAMES
         and len({r['path'] for r in rows}) == len(rows), 'CLOSED_ADDITIVE_MODULES')
    pins = []
    for row in rows:
        path, raw = read(root, {'path': row['path'], 'sha256': row['sha256']})
        need(path.name == row['name'] and row['git_path'] == git_prefix + row['name'], 'CANONICAL_SOURCE_NAME')
        pins.append({k: row[k] for k in ('name', 'path', 'sha256')})
    return pins


def v001_predecessor_installation(root):
    """Fresh byte/Git proof of the immutable v001 install; no runtime verdict."""
    profile=object_at(root,PREDECESSOR_PROFILE)[2]
    nomination=object_at(root,PREDECESSOR_NOMINATION)[2]
    plan=object_at(root,PREDECESSOR_PLAN)[2]
    need(profile['standard']=='VRS-STANDALONE-PDF-PACKAGING-PROFILE-1'
         and profile['canonical_root']==str(Path(root).resolve(strict=True))
         and same_binding(root,nomination['profile'],PREDECESSOR_PROFILE)
         and nomination['status']=='EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-1',
         'EXACT_FROZEN_V001_INSTALLATION')
    module_table(root,profile['modules'],git_prefix=PREDECESSOR_GIT_PREFIX)
    proof=source_proof(root,profile['source_origin'],profile['modules'])
    for key in ('source_origin','source_review','user_authority','access_registry','installed_at_utc'):
        need(plan[key]==profile[key],'FROZEN_V001_PLAN_PROFILE:'+key)
    expected={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in plan['source_modules']}
    actual={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in profile['modules']}
    need(expected==actual and nomination['merged_source_commit']==proof['merge_commit'],
         'FROZEN_V001_SOURCE_AND_NOMINATION')
    for row in plan['source_modules']:
        read(root,{k:row[k]for k in ('path','sha256')})
    review=object_at(root,plan['source_review'])[2]
    need(review['review_scope']=='SOURCE_ONLY'and review['actual_live_runtime_admission']is False
         and review['actual_seven_record_admission']=='PENDING_POST_INSTALL_FRESH_READBACK'
         and review['source_hashes']=={r['name']:r['sha256']for r in profile['modules']},
         'FROZEN_V001_SOURCE_REVIEW_SCOPE')
    object_at(root,plan['root_review'])
    read(root,HISTORICAL_PUBLISHER)
    return {'status':'EXACT_FROZEN_V001_INSTALLATION_SOURCE_READBACK_ONLY',
            'profile':PREDECESSOR_PROFILE,'nomination':PREDECESSOR_NOMINATION,'plan':PREDECESSOR_PLAN,
            'merged_source':proof,'actual_runtime_admission':False,'certifies':False}


def v002_predecessor_installation(root):
    """Both immutable installs are source predecessors, never live verdicts."""
    first=v001_predecessor_installation(root)
    profile=object_at(root,V002_PROFILE)[2]
    nomination=object_at(root,V002_NOMINATION)[2]
    plan=object_at(root,V002_PLAN)[2]
    need(profile['standard']=='VRS-STANDALONE-PDF-PACKAGING-PROFILE-2'
         and profile['canonical_root']==str(Path(root).resolve(strict=True))
         and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-2'
         and nomination['standard']=='VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-2'
         and nomination['status']=='EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and same_binding(root,nomination['profile'],V002_PROFILE)
         and profile['predecessor_installation']==plan['predecessor_installation']==V001_INSTALLATION,
         'EXACT_FROZEN_V002_INSTALLATION')
    module_table(root,profile['modules'],git_prefix='00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v002/')
    proof=source_proof(root,profile['source_origin'],profile['modules'])
    for key in ('source_origin','source_review','user_authority','access_registry','installed_at_utc','transient_rehydration'):
        need(plan[key]==profile[key],'FROZEN_V002_PLAN_PROFILE:'+key)
    expected={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in plan['source_modules']}
    actual={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in profile['modules']}
    need(expected==actual and nomination['merged_source_commit']==proof['merge_commit']
         and nomination['root_review_receipt']==plan['root_review'],'FROZEN_V002_SOURCE_AND_NOMINATION')
    for row in plan['source_modules']:read(root,{k:row[k]for k in ('path','sha256')})
    review=object_at(root,plan['source_review'])[2]
    need(review['standard']=='VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-2'
         and review['review_scope']=='SOURCE_ONLY'and review['actual_live_runtime_admission']is False
         and review['actual_seven_record_admission']=='PENDING_POST_INSTALL_FRESH_READBACK'
         and review['source_hashes']=={r['name']:r['sha256']for r in profile['modules']},'FROZEN_V002_SOURCE_REVIEW_SCOPE')
    object_at(root,plan['root_review']);read(root,nomination['installer_source']);read(root,HISTORICAL_PUBLISHER)
    return {'status':'EXACT_FROZEN_V001_AND_V002_INSTALLATIONS_SOURCE_READBACK_ONLY',
            'v001':first,'v002':{'profile':V002_PROFILE,'nomination':V002_NOMINATION,'plan':V002_PLAN,
                                'merged_source':proof},'actual_runtime_admission':False,'certifies':False}


def predecessor_installation(root):
    """Three exact installed source predecessors; their failures stay failures."""
    previous=v002_predecessor_installation(root)
    profile=object_at(root,V003_PROFILE)[2];nomination=object_at(root,V003_NOMINATION)[2];plan=object_at(root,V003_PLAN)[2]
    need(profile['standard']=='VRS-STANDALONE-PDF-PACKAGING-PROFILE-3'
         and profile['canonical_root']==str(Path(root).resolve(strict=True))
         and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-3'
         and nomination['standard']=='VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-3'
         and nomination['status']=='EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and same_binding(root,nomination['profile'],V003_PROFILE)
         and profile['predecessor_installation']==plan['predecessor_installation']=={'v001':V001_INSTALLATION,'v002':V002_INSTALLATION},
         'EXACT_FROZEN_V003_INSTALLATION')
    module_table(root,profile['modules'],git_prefix='00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v003/')
    proof=source_proof(root,profile['source_origin'],profile['modules'])
    for key in ('source_origin','source_review','user_authority','access_registry','installed_at_utc','transient_rehydration','data_alias_observation'):
        need(plan[key]==profile[key],'FROZEN_V003_PLAN_PROFILE:'+key)
    expected={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in plan['source_modules']}
    actual={r['name']:{k:r[k]for k in ('name','sha256','git_path')}for r in profile['modules']}
    need(expected==actual and nomination['merged_source_commit']==proof['merge_commit']
         and nomination['root_review_receipt']==plan['root_review'],'FROZEN_V003_SOURCE_AND_NOMINATION')
    for row in plan['source_modules']:read(root,{k:row[k]for k in ('path','sha256')})
    review=object_at(root,plan['source_review'])[2]
    need(review['standard']=='VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-3'
         and review['review_scope']=='SOURCE_ONLY'and review['actual_live_runtime_admission']is False
         and review['actual_seven_record_admission']=='PENDING_POST_INSTALL_FRESH_READBACK'
         and review['source_hashes']=={r['name']:r['sha256']for r in profile['modules']},'FROZEN_V003_SOURCE_REVIEW_SCOPE')
    need(same_binding(root,profile['data_alias_observation'],DATA_ALIAS_OBSERVATION),'FROZEN_V003_HISTORICAL_DATA_ALIAS')
    object_at(root,plan['root_review']);read(root,nomination['installer_source']);read(root,HISTORICAL_PUBLISHER)
    return {'status':'EXACT_FROZEN_V001_V002_V003_INSTALLATIONS_SOURCE_READBACK_ONLY',
            'previous':previous,'v003':{'profile':V003_PROFILE,'nomination':V003_NOMINATION,'plan':V003_PLAN,
                                      'merged_source':proof},'actual_runtime_admission':False,'certifies':False}


def data_alias_identity(path):
    path=Path(path);before=path.lstat()
    need(path.is_symlink(),'HISTORICAL_DATA_ALIAS_SYMLINK')
    target=os.readlink(path);after=path.lstat()
    fields=lambda s:{'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,
                     'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'readlink':target}
    need(fields(before)==fields(after),'HISTORICAL_DATA_ALIAS_IDENTITY_RACE')
    return fields(after)


def require_data_alias_observation(root,binding):
    """Only the exact existing historical ancestor; no operator whitelist."""
    root=Path(root).resolve(strict=True)
    need(same_binding(root,binding,DATA_ALIAS_OBSERVATION),'FIXED_HISTORICAL_DATA_ALIAS_OBSERVATION')
    observation=object_at(root,binding)[2]
    fields={'alias_path','alias_writes','canonical_root','certificate_writes','certifies','identity',
            'network_requests','observed_at_utc','original_binding_readbacks','physical_target',
            'representative_original_certificate','scope','source_or_ssot_writes','standard','status'}
    need(set(observation)==fields
         and observation['standard']=='VRS-HISTORICAL-CONTROLPLANE-DATA-ALIAS-OBSERVATION-1'
         and observation['status']=='ACTUAL_EXISTING_HISTORICAL_ALIAS_AND_ORIGINAL_CERTIFICATE_BYTES_VERIFIED_NOT_RUNTIME_ADMISSION'
         and observation['canonical_root']==observation['physical_target']==str(root)
         and observation['alias_path']==str(SCIENTIFIC_ALIAS_PATH)
         and observation['certifies']is False
         and all(observation[k]==0 for k in ('alias_writes','certificate_writes','network_requests','source_or_ssot_writes')),
         'CLOSED_HISTORICAL_DATA_ALIAS_OBSERVATION')
    expected=observation['identity']
    need(set(expected)=={'device','inode','mode','bytes','mtime_ns','ctime_ns','readlink'}
         and expected['readlink']==SCIENTIFIC_ALIAS_READLINK
         and SCIENTIFIC_ALIAS_PATH.parent/SCIENTIFIC_ALIAS_READLINK==root
         and not any(p.is_symlink()for p in SCIENTIFIC_ALIAS_PATH.parents)
         and SCIENTIFIC_ALIAS_PATH.resolve(strict=True)==root
         and data_alias_identity(SCIENTIFIC_ALIAS_PATH)==expected,'EXACT_HISTORICAL_DATA_ALIAS_IDENTITY')
    observed=dt.datetime.fromisoformat(observation['observed_at_utc'].replace('Z','+00:00'))
    need(observed.tzinfo is not None and observed<=dt.datetime.now(dt.timezone.utc),'DATA_ALIAS_OBSERVATION_TIME')
    rows=observation['original_binding_readbacks']
    names={'candidate_proof':'VERIFICATION_CANDIDATE.lean','formal_statement':'VERIFICATION_STATEMENT_V2.lean',
           'independent_cloud_receipt':'COMPARATOR_VERIFICATION_RECEIPT_V2.json','request':'ENGINE3_FROZEN_REQUEST_V2.json',
           'sealed:SEALED_CLAIM_INVENTORY.json':'SEALED_CLAIM_INVENTORY.json',
           'sealed:SEALED_RUN_MANIFEST.json':'SEALED_RUN_MANIFEST.json',
           'sealed:SEALED_paper.pdf':'SEALED_paper.pdf','sealed:SEALED_paper.tex':'SEALED_paper.tex'}
    need(isinstance(rows,list)and len(rows)==8 and {r.get('binding_name')for r in rows}==set(names),
         'EXACT_EIGHT_HISTORICAL_ALIAS_BINDINGS')
    for row in rows:
        need(set(row)=={'binding_name','bytes','logical_path','physical_path','sha256'},'CLOSED_ALIAS_BINDING_READBACK')
        relative=Path('RESEARCH_PIPELINE_v2/engine3_verification/Run-117')/names[row['binding_name']]
        need(row['logical_path']==str(SCIENTIFIC_ALIAS_PATH/relative)
             and row['physical_path']==str(root/relative),'EXACT_HISTORICAL_ALIAS_BINDING_PATH')
        need(len(read(root,{'path':row['physical_path'],'sha256':row['sha256']})[1])==row['bytes'],
             'HISTORICAL_ALIAS_ORIGINAL_BYTE_READBACK')
    read(root,observation['representative_original_certificate'])
    need(data_alias_identity(SCIENTIFIC_ALIAS_PATH)==expected,'HISTORICAL_DATA_ALIAS_FINAL_IDENTITY')
    return observation


def default_platform_tzpath():
    """Native lookup configuration only; never construct/prewarm ZoneInfo."""
    value=os.environ.get('PYTHONTZPATH')
    if value is None:value=sysconfig.get_config_var('TZPATH')
    need(isinstance(value,str),'NATIVE_PLATFORM_TZPATH_CONFIGURATION')
    return tuple(value.split(os.pathsep))


def platform_file_identity(path):
    s=Path(path).lstat()
    return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,
            'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}


def platform_timezone_frame(observation):
    """Exact three-link resolution and one native DATA leaf, no wildcard."""
    logical=Path(observation['logical_selected_path']);physical=Path(observation['physical_path'])
    expected=observation['after'];links=expected['resolution_symlink_chain']
    need(logical==PLATFORM_TZ_LOGICAL and physical==PLATFORM_TZ_PHYSICAL
         and len(links)==3 and tuple(Path(r['path'])for r in links)==PLATFORM_TZ_LINK_PATHS,
         'CLOSED_NATIVE_TIMEZONE_PATHS')
    def closed_resolution_components():
        routes=[logical]
        for row in links:
            target=Path(row['identity']['readlink'])
            routes.append(target if target.is_absolute()else Path(row['path']).parent/target)
        for route in routes:
            for path in(route,*route.parents):
                if path.is_symlink():
                    component=path.parent.resolve(strict=True)/path.name
                    need(component in PLATFORM_TZ_LINK_PATHS,
                         'UNDECLARED_NATIVE_TIMEZONE_LINK:'+str(path))
    closed_resolution_components()
    need(default_platform_tzpath()==tuple(observation['stdlib_TZPATH'])
         and next((Path(p)/observation['zone_key']for p in default_platform_tzpath()
                   if (Path(p)/observation['zone_key']).is_file()),None)==logical,
         'ACTUAL_NATIVE_NEW_YORK_LOOKUP')
    current_links=[]
    for row in links:
        need(set(row)=={'path','identity','resolved_target'},'CLOSED_NATIVE_TIMEZONE_LINK')
        path=Path(row['path']);identity=data_alias_identity(path)
        need(identity==row['identity']and str(path.resolve(strict=True))==row['resolved_target'],
             'EXACT_NATIVE_TIMEZONE_LINK_IDENTITY:'+str(path))
        current_links.append({'path':str(path),'identity':identity,'resolved_target':row['resolved_target']})
    need(logical.resolve(strict=True)==physical and physical.is_file()
         and not any(p.is_symlink()for p in(physical,*physical.parents)),
         'NATIVE_TIMEZONE_REGULAR_PHYSICAL_LEAF')
    parents=expected['physical_regular_parent_chain']
    need([r.get('path')for r in parents]==[str(p)for p in reversed(physical.parents)],
         'COMPLETE_NATIVE_TIMEZONE_PHYSICAL_PARENTS')
    observed_parents=[]
    for row in parents:
        need(set(row)=={'path','identity'},'CLOSED_NATIVE_TIMEZONE_PARENT')
        path=Path(row['path']);identity=platform_file_identity(path)
        need(path.is_dir()and not path.is_symlink()
             and {k:identity[k]for k in ('device','inode','mode')}=={k:row['identity'][k]for k in ('device','inode','mode')},
             'NATIVE_TIMEZONE_PARENT_STRUCTURE:'+str(path))
        observed_parents.append({'path':str(path),'identity':identity})
    before=platform_file_identity(physical)
    need(before==expected['physical_file_identity'],'EXACT_NATIVE_TIMEZONE_LEAF_IDENTITY')
    raw=physical.read_bytes()
    need(platform_file_identity(physical)==before,'NATIVE_TIMEZONE_READ_RACE')
    for row in links:
        need(data_alias_identity(Path(row['path']))==row['identity']
             and str(Path(row['path']).resolve(strict=True))==row['resolved_target'],
             'NATIVE_TIMEZONE_POST_READ_LINK_RACE')
    need(not any(p.is_symlink()for p in(physical,*physical.parents))
         and logical.resolve(strict=True)==physical,'NATIVE_TIMEZONE_POST_READ_PATH_RACE')
    closed_resolution_components()
    for row in parents:
        current=platform_file_identity(Path(row['path']))
        need({k:current[k]for k in ('device','inode','mode')}=={k:row['identity'][k]for k in ('device','inode','mode')},
             'NATIVE_TIMEZONE_POST_READ_PARENT_RACE')
    need(platform_file_identity(physical)==before,'NATIVE_TIMEZONE_FINAL_LEAF_RACE')
    need(sha(raw)==expected['sha256']and len(raw)==expected['bytes']
         and raw[:5].hex()==expected['TZif_header_hex'],'EXACT_NATIVE_TIMEZONE_BYTES')
    return {'physical_file_identity':before,'resolution_symlink_chain':current_links,
            'physical_regular_parent_chain':observed_parents,'bytes':expected['bytes'],
            'sha256':expected['sha256'],'TZif_header_hex':expected['TZif_header_hex']}


def require_platform_timezone_observation(root,binding):
    need(same_binding(root,binding,PLATFORM_TIMEZONE_OBSERVATION),'FIXED_NATIVE_PLATFORM_TIMEZONE_OBSERVATION')
    observation=object_at(root,binding)[2]
    fields={'actual_failed_child_path_limitation','actual_failed_execution','after','before','certifies','created_at_utc',
            'heavy_scientific_executions','independent_platform_path_evidence','logical_selected_path','network_requests',
            'physical_path','root_executable','scope','source_certificate_alias_ledger_timezone_writes','standard','status',
            'stdlib_TZPATH','zone_key'}
    need(set(observation)==fields and observation['standard']=='VRS-ROOT-EXACT-PLATFORM-TIMEZONE-DATA-READBACK-1'
         and observation['status']=='EXACT_CURRENT_NATIVE_DATA_PATH_VERIFIED_NOT_RUNTIME_ADMISSION'
         and observation['zone_key']=='America/New_York'and observation['certifies']is False
         and observation['root_executable']==sys.executable
         and observation['heavy_scientific_executions']==observation['network_requests']==observation['source_certificate_alias_ledger_timezone_writes']==0
         and observation['before']==observation['after'],'CLOSED_NATIVE_PLATFORM_TIMEZONE_OBSERVATION')
    frame=observation['after']
    need(set(frame)=={'TZif_header_hex','bytes','physical_file_identity','physical_regular_parent_chain','resolution_symlink_chain','sha256'},
         'CLOSED_NATIVE_PLATFORM_TIMEZONE_FRAME')
    captured=dt.datetime.fromisoformat(observation['created_at_utc'].replace('Z','+00:00'))
    need(captured.tzinfo is not None and captured<=dt.datetime.now(dt.timezone.utc),'NATIVE_PLATFORM_TIMEZONE_OBSERVATION_TIME')
    platform_timezone_frame(observation)
    return observation


def legacy_transient_precheck(root, original_source_origin, *, restore=False, require_present=True):
    """Eight Git-bound copies only; durable intent/readback for every creation.

    All sources and existing targets are checked before any write. Rehydration
    is separate from GET-only reads and never changes installed source/SSOT.
    Existing exact copies create no new recovery event. No cached PASS is used.
    """
    root=Path(root).resolve(strict=True);pending=[];proof_rows=[]
    need(len(LEGACY_TRANSIENT_SOURCES)==8
         and len({r['target']for r in LEGACY_TRANSIENT_SOURCES})==8,'EXACT_EIGHT_LEGACY_TRANSIENTS')
    for row in LEGACY_TRANSIENT_SOURCES:
        source,raw=read(root,row['source'])
        proof_rows.append({'name':row['name'],'path':str(source),'sha256':row['source']['sha256'],
                           'git_path':row['git_path']})
        target=Path(row['target'])
        need(target.is_absolute()and target.is_relative_to(LEGACY_TRANSIENT_ROOT)
             and '..'not in target.parts and not any(p.is_symlink()for p in (target,*target.parents)),
             'LEGACY_TRANSIENT_REGULAR_TARGET')
        if target.exists():
            need(target.is_file()and sha(target.read_bytes())==row['source']['sha256'],
                 'LEGACY_TRANSIENT_EXISTING_MISMATCH:'+row['name'])
        pending.append((row,target,raw))
    proof=source_proof(root,original_source_origin,proof_rows,
                       required_checks=REQUIRED_CHECKS-{'standalone-manuscript-pdf'})
    absent=[str(t)for _,t,_ in pending if not t.exists()]
    journal=None;restored=[];missing=[]
    def receipt(name,value):
        data=(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
        path=journal/name
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
        with os.fdopen(fd,'wb')as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        need(path.read_bytes()==data,'TRANSIENT_RECOVERY_JOURNAL_READBACK')
        return {'path':str(path),'sha256':sha(data)}
    if restore and absent:
        stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
        journal=root/'reports/verification-coverage'/stamp/('legacy-transient-recovery-'+uuid.uuid4().hex)
        need(not any(p.is_symlink()for p in (journal,*journal.parents)),'TRANSIENT_RECOVERY_JOURNAL_REGULAR')
        journal.mkdir(parents=True,exist_ok=False)
        intent=receipt('RECOVERY_INTENT.json',{'standard':'VRS-EXACT-LEGACY-TRANSIENT-RECOVERY-1',
            'status':'SOURCE_PROVED_EXCLUSIVE_REHYDRATION_INTENT_NOT_COMPLETION',
            'captured_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'original_source_origin':original_source_origin,'source_proof':proof,
            'allowed_sources':list(LEGACY_TRANSIENT_SOURCES),'absent_targets':absent,
            'installed_source_writes':0,'ssot_writes':0,'zenodo_writes':0,'network_requests':0,'certifies':False})
    try:
        for row,target,raw in pending:
            need(read(root,row['source'])[1]==raw,'LEGACY_TRANSIENT_DURABLE_RACE')
            need(not any(p.is_symlink()for p in (target,*target.parents)),'LEGACY_TRANSIENT_TARGET_RACE')
            if not target.exists():
                if not restore:
                    need(not require_present,'LEGACY_TRANSIENT_ABSENT:'+row['name'])
                    missing.append(str(target));continue
                target.parent.mkdir(parents=True,exist_ok=True)
                need(not any(p.is_symlink()for p in (target,*target.parents)),'LEGACY_TRANSIENT_PARENT_RACE')
                fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0),0o600)
                with os.fdopen(fd,'wb')as stream:
                    stream.write(raw);stream.flush();os.fsync(stream.fileno())
                restored.append(str(target))
            need(target.is_file()and not any(p.is_symlink()for p in (target,*target.parents))
                 and target.read_bytes()==raw,'LEGACY_TRANSIENT_EXACT_READBACK')
        result={'status':'EXACT_ORIGINAL_GIT_BOUND_TRANSIENT_SOURCE_READBACK'if not missing else'SOURCE_PROVED_TRANSIENTS_ABSENT_NOT_REHYDRATED',
                'source_proof':proof,'targets':[{'path':str(t),'sha256':r['source']['sha256']}for r,t,_ in pending],
                'restored_targets':restored,'missing_targets':missing,'transient_source_writes':len(restored),
                'network_requests':0,'installed_source_writes':0,'ssot_writes':0,'zenodo_writes':0,'certifies':False}
        if journal is not None:
            result['recovery_intent']=intent
            result['recovery_receipt']=receipt('RECOVERY_READBACK.json',{
                'standard':'VRS-EXACT-LEGACY-TRANSIENT-RECOVERY-1',**result,
                'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()})
        return result
    except Exception as error:
        if journal is not None:
            receipt('RECOVERY_HOLD.json',{'standard':'VRS-EXACT-LEGACY-TRANSIENT-RECOVERY-1',
                'status':'HOLD_TRANSIENT_RECOVERY_NOT_ADMISSION','intent':intent,
                'restored_targets':restored,'error_type':type(error).__name__,'error':str(error),
                'automatic_mismatch_overwrite':False,'ssot_writes':0,'zenodo_writes':0,'certifies':False})
        raise


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
         and nomination['standard'] == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-4'
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
            'user_authority','access_registry','historical_publisher','installed_at_utc','root_review',
            'predecessor_installation','transient_rehydration','data_alias_observation','platform_timezone_observation'}
    need(set(plan)==fields and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-4'
         and plan['status']=='ROOT_REVIEWED_READY_NOT_INSTALLED'and plan['canonical_root']==str(root), 'CLOSED_INSTALLED_PLAN')
    for field in ('source_origin','source_review','user_authority','access_registry','installed_at_utc',
                  'predecessor_installation','transient_rehydration','data_alias_observation','platform_timezone_observation'):
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
                       'source_hashes','historical_publisher_sha256','scientific_or_authority_changes'}
         and review['standard']=='VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-4'
         and review['status']=='EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS'
         and isinstance(review['reviewer'],str)and review['reviewer']
         and review['plan_projection_sha256']==sha((json.dumps({k:v for k,v in plan.items()if k!='root_review'},sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode())
         and review['merged_source_commit']==proof['merge_commit']==nomination['merged_source_commit']
         and review['source_hashes']=={r['name']:r['sha256']for r in rows}
         and review['historical_publisher_sha256']=='4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94'
         and review['scientific_or_authority_changes']is False, 'ROOT_REVIEW_EXACT_INSTALLED_PLAN_AND_SOURCE')
    need(same_binding(root,plan['historical_publisher'],HISTORICAL_PUBLISHER),'PRESERVED_HISTORICAL_PUBLISHER_BINDING')
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
    need(profile['predecessor_installation']==PREDECESSOR_INSTALLATION
         and profile['transient_rehydration']==TRANSIENT_REHYDRATION_POLICY,'EXACT_PREDECESSOR_AND_TRANSIENT_POLICY')
    predecessor=predecessor_installation(root)
    alias_observation=require_data_alias_observation(root,profile['data_alias_observation'])
    platform_observation=require_platform_timezone_observation(root,profile['platform_timezone_observation'])
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
    # Prove the additive source before importing any new executable module.
    proof = source_proof(root, profile['source_origin'], profile['modules'])
    _, review_raw, review = object_at(root, profile['source_review'])
    hashes = {r['name']: r['sha256'] for r in profile['modules']}
    need(set(review) == {'standard', 'status', 'reviewer', 'source_hashes', 'legacy_closure',
                        'scientific_admission_changed', 'historical_sources_changed',
                        'review_scope', 'actual_live_runtime_admission', 'actual_seven_record_admission'}
         and review['standard'] == 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-4'
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
    # Source/helper admission is distinct from operational scientific data.
    # The catalog performs one fresh complete original corpus build and the
    # original baseline/current-population comparator in each operation.
    transients=legacy_transient_precheck(root,
        {'pull_request':origin['merged_pr'],'merge_commit':origin['merged_commit'],'tree':origin['merged_tree']},
        restore=True)
    # The genuine unchanged finder is installed before every original corpus
    # import, including a cold direct entry and its ordinary checkpoint child.
    with builder_source_scope(root,profile,combined):
        legacy=load(root,LEGACY_CONSUMER,'_exact_packaging_legacy_closure')
        need(legacy.read_bound_closure(LEGACY_CLOSURE)==saved,'ACTUAL_LEGACY_CLOSURE_READ')
        view=load(root,{k:view_rows[0][k]for k in ('path','sha256')},'_exact_packaging_runtime_view')
        with view.exact_runtime_view(root,combined,legacy_pins):
            current=legacy.current_closure(Path(profile['legacy_closure']['path']).parent if Path(profile['legacy_closure']['path']).is_absolute()
                        else(root/profile['legacy_closure']['path']).parent,saved['protected_readback'])
            need(current==saved and current.get('certifies')is False,'ACTUAL_UNCHANGED_LEGACY_SOURCE_AND_HELPER_CLOSURE')
    need(ledger_path.read_bytes()==ledger_raw,'ACTUAL_SCIENCE_POPULATION_RACE')
    need(proof['merge_commit']==nomination['merged_source_commit'],'INSTALLED_NOMINATED_MERGE')
    _, registry_raw = read(root, profile['access_registry'])
    need(read(root, profile_binding)[1] == profile_raw
         and read(root, profile['user_authority'])[1] == authority_raw
         and read(root, authority['provider_instruction'])[1] == provider_raw
         and read(root, profile['source_review'])[1] == review_raw
         and read(root, profile['access_registry'])[1] == registry_raw, 'FINAL_PROFILE_INPUT_RACE')
    require_data_alias_observation(root,profile['data_alias_observation'])
    require_platform_timezone_observation(root,profile['platform_timezone_observation'])
    for row in combined:
        read(root, {'path': row['path'], 'sha256': row['sha256']})
    return {'status': 'ACTUAL_SOURCE_HELPER_AND_ADDITIVE_PACKAGING_SCOPE_PASS',
            'legacy_closure': profile['legacy_closure'], 'source_pins': combined,
            'merged_source': proof, 'access_registry': profile['access_registry'],
            'default_routes': DEFAULT_ROUTES, 'predecessor_installation':predecessor,
            'data_alias_observation':profile['data_alias_observation'],
            'platform_timezone_observation':profile['platform_timezone_observation'],
            'transient_source_readback':transients, 'scientific_population_admitted':False, 'certifies': False,
            'ssot_writes': 0, 'zenodo_writes': 0}


@contextlib.contextmanager
def session(root, profile_binding):
    """The sole default v4 dispatch scope; prove entry and exit, no cache bypass."""
    result = validate(root, profile_binding)
    profile = object_at(root, profile_binding)[2]
    builder = load(root, profile['source_session_consumer'], '_exact_packaging_session_builder')
    with builder.source_session(root, result['source_pins']):
        validate(root, profile_binding, purpose_pins=result['source_pins'])
        try:
            yield result
        finally:
            validate(root, profile_binding, purpose_pins=result['source_pins'])


if __name__ == '__main__':
    raise SystemExit('Explicit source-bound default entry required; no automatic installation.')
