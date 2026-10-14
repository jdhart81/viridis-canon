"""Closed additive packaging profile over the unchanged science runtime.

No installation, source rewrite, cached PASS, proof execution or publication.
The unchanged old helper freshly admits physical source/protected closure;
complete scientific population admission belongs to a fresh operational build.
Missing exact original temporary sources may be rehydrated with durable receipts.
"""
from __future__ import annotations
import contextlib
import contextvars
import datetime as dt
import hashlib
import json
import os
import stat
import functools
from pathlib import Path
import re
import types
from collections.abc import Mapping
import uuid
import sysconfig
import sys

STANDARD = 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-6'
STATUS = 'INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS'
USER_DIRECTIVE = 'make sure all our deposits have the actual papers as separate PDFs and make that standard for future releases'

# Pre-execution trust roots are the genuine unchanged predecessor artifacts,
# never bindings supplied by a release config or a caller-selected profile.
LEGACY_CLOSURE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/typography-runtime-install-v001/CURRENT_RUNTIME_CLOSURE.json', 'sha256': '48ee958633d781244b52065540c813dbb436d7272353448ddebb838ab9f6e429'}
LEGACY_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/runtime_successor.py', 'sha256': 'b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'}
LEGACY_SCOPE = {'path': 'reports/verification-coverage/2026-10-11/recent-science-push-v001/publication-preparation-v003/CURRENT_SOURCE_SCOPE.json', 'sha256': '84eaef87c142ae3b588c8c534836311b3c051b35b94f1b8b91690bbda22a0a15'}
SESSION_CONSUMER = {'path': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/prepare_first_seven_plan.py', 'sha256': 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'}
PROVIDER_SHA = 'fb57aeaf4a43f0183043d12c28ed02a2ce326f452b8a596f1231a29d98123f0b'
PROFILE_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v006/CURRENT_PACKAGING_PROFILE.json'
NOMINATION_PATH = '_ZENODO_DEPOSITS/standalone_pdf_runtime_v006/INSTALLATION_NOMINATION.json'

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
V004_PROFILE = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v004/CURRENT_PACKAGING_PROFILE.json','sha256':'f797c1f2a51f2b9a6a9b54244f4bd737f7e9b020e735d9b416b09d96dc8b5c79'}
V004_NOMINATION = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v004/INSTALLATION_NOMINATION.json','sha256':'f6fdc5cff5de09594eb25372c3544ded8da7242ceb8a98c7336c50ba3435afa1'}
V004_PLAN = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v004/INSTALL_PLAN.json','sha256':'ebd2edf10e6a7e46c2a77860f39139aec669a70b735e26652f2d459b94a237fb'}
V004_INSTALLATION = {'profile':V004_PROFILE,'nomination':V004_NOMINATION,'plan':V004_PLAN}
V005_PROFILE = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v005/CURRENT_PACKAGING_PROFILE.json','sha256':'0ff28cc686390b8d1fa1c23a6b6280e3fd6dec8c126508b92982f0506ba06482'}
V005_NOMINATION = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v005/INSTALLATION_NOMINATION.json','sha256':'3fcc84b318b2d9dbeb83b771d1798532c8435322043179efa19b6007400effa8'}
V005_PLAN = {'path':'_ZENODO_DEPOSITS/standalone_pdf_runtime_v005/INSTALL_PLAN.json','sha256':'205de67b0668e736f12d2d869da59edb93411377e5976fa4f7623caf44c118c1'}
V005_INSTALLATION = {'profile':V005_PROFILE,'nomination':V005_NOMINATION,'plan':V005_PLAN}
PREDECESSOR_INSTALLATION = {'v001':V001_INSTALLATION,'v002':V002_INSTALLATION,'v003':V003_INSTALLATION,'v004':V004_INSTALLATION,'v005':V005_INSTALLATION}
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

GIT_PREFIX = '00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v006/'
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


_JSON_DATA = contextvars.ContextVar('one_operation_pure_json_data', default=None)


def file_identity(stat):
    return (stat.st_dev, stat.st_ino, stat.st_mode, stat.st_size,
            stat.st_mtime_ns, stat.st_ctime_ns)


def _freeze_json(value):
    if isinstance(value, dict):
        return ('object', tuple((k, _freeze_json(v)) for k, v in value.items()))
    if isinstance(value, list):
        return ('array', tuple(_freeze_json(v) for v in value))
    return ('scalar', value)


def _thaw_json(value):
    kind, material = value
    if kind == 'object': return {k: _thaw_json(v) for k, v in material}
    if kind == 'array': return [_thaw_json(v) for v in material]
    return material


class ImmutableJsonObject(Mapping):
    """Pure immutable object DATA; export allocates only when requested.

    Its full recursive material is tuple/scalar only. This is neither a file
    observation nor an admission; only a new checked read can supply it to a
    consumer. Mapping access does not reconstruct the entire descriptor.
    """
    __slots__ = ('_value',)
    def __init__(self, value):
        need(value[0] == 'object', 'BOUND_OBJECT')
        object.__setattr__(self, '_value', value)
    def __setattr__(self, name, value):
        raise AttributeError('Immutable JSON DATA cannot be replaced')
    def __delattr__(self, name):
        raise AttributeError('Immutable JSON DATA cannot be deleted')
    def __getitem__(self, key):
        for name, value in self._value[1]:
            if name == key: return _immutable_json_view(value)
        raise KeyError(key)
    def __iter__(self): return (name for name, _ in self._value[1])
    def __len__(self): return len(self._value[1])
    def __eq__(self, other):
        if isinstance(other, ImmutableJsonObject):
            if self._value == other._value: return True
            return len(self) == len(other) and all(k in other and _immutable_json_equal(self[k], other[k]) for k in self)
        if isinstance(other, dict):
            return len(self) == len(other) and all(k in other and _immutable_json_equal(self[k], other[k]) for k in self)
        return False
    def export(self): return _thaw_json(self._value)


def _immutable_json_equal(left, right):
    if isinstance(left, ImmutableJsonObject): return left == right
    if isinstance(left, tuple):
        return isinstance(right, (tuple, list)) and len(left) == len(right) and all(
            _immutable_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def _immutable_json_view(value):
    kind, material = value
    if kind == 'object': return ImmutableJsonObject(value)
    if kind == 'array': return tuple(_immutable_json_view(v) for v in material)
    return material


def immutable_json_object(value):
    return ImmutableJsonObject(_freeze_json(value))


class _JsonDataOperation:
    """Immutable holder; mutable bookkeeping is inaccessible closure storage.

    The scope view exposes counters only. Immutable tuple material is never
    exposed as a mutable cache entry, and callers cannot nominate a cache.
    """
    __slots__ = ('root', '_is_closed', '_fresh', '_parse', '_close', 'view')
    def __init__(self, root):
        frames = {}; material = {}; state = {'closed': False}
        counters = {'data_only': True, 'admission_cached': False, 'fresh_reads': 0,
                    'parses': 0, 'parse_reuses': 0}
        def fresh(path, raw, identity):
            need(not state['closed'], 'JSON_DATA_OPERATION_CLOSED')
            counters['fresh_reads'] += 1; frames[str(path)] = (raw, identity)
        def parse(path, raw, copy_result):
            need(not state['closed'], 'JSON_DATA_OPERATION_CLOSED')
            frame = frames.pop(str(path), None)
            need(frame is not None and frame[0] == raw, 'FRESH_CHECKED_JSON_DATA_FRAME_REQUIRED')
            old = material.get(str(path))
            if old is None or (old[0], old[1]) != frame:
                parsed = _freeze_json(json.loads(raw)); material[str(path)] = (raw, frame[1], parsed)
                counters['parses'] += 1
            else:
                parsed = old[2]; counters['parse_reuses'] += 1
            return _thaw_json(parsed) if copy_result else parsed
        def close():
            state['closed'] = True; frames.clear(); material.clear()
        for key, value in (('root', root), ('_is_closed', lambda: state['closed']),
                           ('_fresh', fresh), ('_parse', parse), ('_close', close),
                           ('view', types.MappingProxyType(counters))):
            object.__setattr__(self, key, value)
    def __setattr__(self, name, value):
        raise AttributeError('The operation DATA holder is immutable')
    @property
    def closed(self): return self._is_closed()


@contextlib.contextmanager
def json_data_scope(root):
    """Nested uses share pure DATA only during this single active root scope.

    Every use needs a new complete checked physical read; no verdict or parsed
    object from a completed/failed operation is accepted by the next operation.
    """
    root = Path(root).resolve(strict=True); parent = _JSON_DATA.get()
    if parent is not None and parent.root == root:
        need(not parent.closed, 'JSON_DATA_OPERATION_CLOSED')
        yield parent.view
        return
    scope = _JsonDataOperation(root); token = _JSON_DATA.set(scope)
    try: yield scope.view
    finally:
        scope._close(); _JSON_DATA.reset(token)


def parse_json_data(root, path, raw, *, copy_result=True):
    scope = _JSON_DATA.get()
    root = checked_root(root)
    # The old parser's root.resolve was its own fresh sample after the final
    # file-path sample. Retain that position, without generic resolve work.
    strict_directory_frame(root, 'ONE_ACTIVE_JSON_DATA_OPERATION_REQUIRED')
    need(scope is not None and scope.root == root,
         'ONE_ACTIVE_JSON_DATA_OPERATION_REQUIRED')
    return scope._parse(Path(path), raw, copy_result)


@functools.lru_cache(maxsize=32768)
def lexical_ancestors(path):
    """Path tuples only: no filesystem observations, identities or verdicts."""
    path = Path(path)
    return (path, *path.parents)


@functools.lru_cache(maxsize=32768)
def lexical_component_strings(path):
    return tuple(map(str, lexical_ancestors(path)))


def fresh_symlink_components(path):
    """Full fresh walk; only the immutable lexical path tuples are reused."""
    links = []
    for component, name in zip(lexical_ancestors(path), lexical_component_strings(path)):
        try: observed = os.lstat(name)
        except (FileNotFoundError, NotADirectoryError): continue
        if stat.S_ISLNK(observed.st_mode): links.append(component)
    return links


def checked_root(root):
    """An active operation supplies a lexical canonical root, never FS trust.

    Every read still samples every root/target component at every distinct old
    sampling stage.
    A different or aliased root takes the existing strict resolution route.
    """
    root = root if isinstance(root, Path) else Path(root); scope = _JSON_DATA.get()
    return root if scope is not None and root == scope.root else root.resolve(strict=True)


def strict_regular_source_frame(root, path, reason):
    """Fresh closed lexical containment and complete ancestry sampling.

    With no '..' and no symlink in any component, lexical containment equals
    physical containment. This performs a full new lstat walk every call;
    directory device/inode/mode and full leaf identity remain race evidence.
    """
    need(path.is_absolute() and '..' not in path.parts
         and path.parts[:len(root.parts)] == root.parts, reason)
    rows = []
    for index, component in enumerate(lexical_component_strings(path)):
        try: observed = os.lstat(component)
        except OSError as exc:
            raise PackagingHold('HOLD_PACKAGING_' + reason) from exc
        need(not stat.S_ISLNK(observed.st_mode)
             and (stat.S_ISREG(observed.st_mode) if index == 0 else stat.S_ISDIR(observed.st_mode)), reason)
        rows.append(file_identity(observed) if index == 0
                    else (observed.st_dev, observed.st_ino, observed.st_mode))
    return tuple(rows)


def strict_directory_frame(path, reason):
    rows = []
    for component in lexical_component_strings(path):
        try: observed = os.lstat(component)
        except OSError as exc:
            raise PackagingHold('HOLD_PACKAGING_' + reason) from exc
        need(stat.S_ISDIR(observed.st_mode), reason)
        rows.append((observed.st_dev, observed.st_ino, observed.st_mode))
    return tuple(rows)


def strict_historical_alias_target(alias, root, expected_readlink):
    """Fresh exact fixed-link resolution without generic path normalization.

    Both logical parent and physical target ancestry are sampled anew at the
    existing resolve position. Only the one fixed link is permitted; an added
    parent link or a missing/non-directory target cannot be silently followed.
    """
    alias = Path(alias); target = Path(expected_readlink)
    need(not target.is_absolute() and len(target.parts) == 1 and '..' not in target.parts
         and alias.parent / target == root, 'SCIENTIFIC_HISTORICAL_ALIAS_OBSERVATION_CHANGED')
    for component in lexical_component_strings(alias.parent):
        observed = os.lstat(component)
        need(stat.S_ISDIR(observed.st_mode), 'SCIENTIFIC_HISTORICAL_ALIAS_OBSERVATION_CHANGED')
    link = alias.lstat()
    need(stat.S_ISLNK(link.st_mode) and os.readlink(alias) == expected_readlink,
         'SCIENTIFIC_HISTORICAL_ALIAS_OBSERVATION_CHANGED')
    # The fixed single-component relative target shares the already sampled
    # logical parent chain, exactly as the old relative-link resolver did.
    # Sample its one new physical directory component at that position.
    observed = os.lstat(root)
    need(stat.S_ISDIR(observed.st_mode), 'SCIENTIFIC_HISTORICAL_ALIAS_OBSERVATION_CHANGED')
    return root


def read_data_file(root, path, *, expected_sha256=None):
    """A fresh strict regular-source read, with full before/after identity.

    A checked frame is pure DATA and grants no admission. Source imports remain
    strict: historical DATA aliases and native timezone links are not allowed.
    """
    root = checked_root(root); p = Path(path)
    # Stage map: old root.resolve -> root frame; old pre no-link walk and
    # pre resolve -> two separate frames; old post no-link walk and resolve
    # -> two separate frames; old final resolve -> final frame. No old live
    # sampling position is elided, even when a lexical tuple is memoized.
    root_frame = strict_directory_frame(root, 'REGULAR_CONTAINED_SOURCE')
    p = p if p.is_absolute() else root / p
    pre_links = strict_regular_source_frame(root, p, 'REGULAR_CONTAINED_SOURCE')
    before = strict_regular_source_frame(root, p, 'REGULAR_CONTAINED_SOURCE')
    need(pre_links == before, 'SOURCE_HASH_OR_RACE')
    first = p.stat(); raw = p.read_bytes(); last = p.stat()
    post_links = strict_regular_source_frame(root, p, 'SOURCE_HASH_OR_RACE')
    after = strict_regular_source_frame(root, p, 'SOURCE_HASH_OR_RACE')
    need(file_identity(first) == file_identity(last)
         and before == post_links == after and before[0] == file_identity(first)
         and after[0] == file_identity(last)
         and file_identity(p.stat()) == file_identity(last)
         and (expected_sha256 is None or sha(raw) == expected_sha256), 'SOURCE_HASH_OR_RACE')
    final = strict_regular_source_frame(root, p, 'SOURCE_HASH_OR_RACE')
    root_position = len(p.parts) - len(root.parts)
    need(final == after and final[root_position:] == root_frame, 'SOURCE_HASH_OR_RACE')
    path = p
    scope = _JSON_DATA.get()
    if scope is not None:
        need(scope.root == root, 'JSON_DATA_OPERATION_ROOT')
        scope._fresh(path, raw, file_identity(last))
    return path, raw


def read(root, binding):
    need(isinstance(binding, dict) and set(binding) == {'path', 'sha256'}
         and isinstance(binding['path'], str)
         and re.fullmatch('[0-9a-f]{64}', str(binding['sha256'])), 'CLOSED_BINDING')
    return read_data_file(root, binding['path'], expected_sha256=binding['sha256'])


def object_at(root, binding):
    path, raw = read(root, binding)
    value = (parse_json_data(root, path, raw) if _JSON_DATA.get() is not None else json.loads(raw))
    need(isinstance(value, dict), 'BOUND_OBJECT')
    return path, raw, value


def immutable_object_at(root, binding):
    """Full fresh bound read and syntax parse; no mutable reconstruction."""
    path, raw = read(root, binding)
    value = (parse_json_data(root, path, raw, copy_result=False) if _JSON_DATA.get() is not None
             else _freeze_json(json.loads(raw)))
    return path, raw, ImmutableJsonObject(value)


def json_file(root, path):
    """Fresh unbound actual DATA; syntax/shape admission remains at the caller."""
    path, raw = read_data_file(root, path)
    value = parse_json_data(root, path, raw) if _JSON_DATA.get() is not None else json.loads(raw)
    return path, raw, value


def json_file_field(root, path, field, default=None):
    """Full fresh file and whole JSON syntax; export only one DATA branch."""
    path, raw = read_data_file(root, path)
    value = (parse_json_data(root, path, raw, copy_result=False) if _JSON_DATA.get() is not None
             else _freeze_json(json.loads(raw)))
    need(value[0] == 'object', 'JSON_FIELD_OBJECT')
    for key, material in value[1]:
        if key == field: return path, raw, _thaw_json(material)
    return path, raw, default


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


def v003_predecessor_installation(root):
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


def v004_predecessor_installation(root):
    """Four fixed installed predecessors; a failed live check stays a HOLD."""
    previous = v003_predecessor_installation(root)
    profile = object_at(root, V004_PROFILE)[2]
    nomination = object_at(root, V004_NOMINATION)[2]
    plan = object_at(root, V004_PLAN)[2]
    need(profile['standard'] == 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-4'
         and profile['canonical_root'] == str(Path(root).resolve(strict=True))
         and plan['standard'] == 'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-4'
         and nomination['standard'] == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-4'
         and nomination['status'] == 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and same_binding(root, nomination['profile'], V004_PROFILE)
         and profile['predecessor_installation'] == plan['predecessor_installation']
             == {'v001': V001_INSTALLATION, 'v002': V002_INSTALLATION, 'v003': V003_INSTALLATION},
         'EXACT_FROZEN_V004_INSTALLATION')
    module_table(root, profile['modules'], git_prefix='00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v004/')
    proof = source_proof(root, profile['source_origin'], profile['modules'])
    for key in ('source_origin', 'source_review', 'user_authority', 'access_registry', 'installed_at_utc',
                'transient_rehydration', 'data_alias_observation', 'platform_timezone_observation'):
        need(plan[key] == profile[key], 'FROZEN_V004_PLAN_PROFILE:' + key)
    expected = {r['name']: {k: r[k] for k in ('name', 'sha256', 'git_path')} for r in plan['source_modules']}
    actual = {r['name']: {k: r[k] for k in ('name', 'sha256', 'git_path')} for r in profile['modules']}
    need(expected == actual and nomination['merged_source_commit'] == proof['merge_commit']
         and nomination['root_review_receipt'] == plan['root_review'], 'FROZEN_V004_SOURCE_AND_NOMINATION')
    for row in plan['source_modules']: read(root, {k: row[k] for k in ('path', 'sha256')})
    review = object_at(root, plan['source_review'])[2]
    need(review['standard'] == 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-4'
         and review['review_scope'] == 'SOURCE_ONLY' and review['actual_live_runtime_admission'] is False
         and review['actual_seven_record_admission'] == 'PENDING_POST_INSTALL_FRESH_READBACK'
         and review['source_hashes'] == {r['name']: r['sha256'] for r in profile['modules']},
         'FROZEN_V004_SOURCE_REVIEW_SCOPE')
    need(same_binding(root, profile['data_alias_observation'], DATA_ALIAS_OBSERVATION)
         and same_binding(root, profile['platform_timezone_observation'], PLATFORM_TIMEZONE_OBSERVATION),
         'FROZEN_V004_FIXED_DATA_OBSERVATIONS')
    object_at(root, plan['root_review']); read(root, nomination['installer_source']); read(root, HISTORICAL_PUBLISHER)
    return {'status': 'EXACT_FROZEN_V001_V002_V003_V004_INSTALLATIONS_SOURCE_READBACK_ONLY',
            'previous': previous, 'v004': {'profile': V004_PROFILE, 'nomination': V004_NOMINATION,
            'plan': V004_PLAN, 'merged_source': proof}, 'actual_runtime_admission': False, 'certifies': False}


def predecessor_installation(root):
    """Five fixed installed predecessors; a failed live check stays a HOLD."""
    previous = v004_predecessor_installation(root)
    profile = object_at(root, V005_PROFILE)[2]
    nomination = object_at(root, V005_NOMINATION)[2]
    plan = object_at(root, V005_PLAN)[2]
    need(profile['standard'] == 'VRS-STANDALONE-PDF-PACKAGING-PROFILE-5'
         and profile['canonical_root'] == str(Path(root).resolve(strict=True))
         and plan['standard'] == 'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-5'
         and nomination['standard'] == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-5'
         and nomination['status'] == 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING'
         and same_binding(root, nomination['profile'], V005_PROFILE)
         and profile['predecessor_installation'] == plan['predecessor_installation']
             == {'v001': V001_INSTALLATION, 'v002': V002_INSTALLATION, 'v003': V003_INSTALLATION, 'v004': V004_INSTALLATION},
         'EXACT_FROZEN_V005_INSTALLATION')
    module_table(root, profile['modules'], git_prefix='00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v005/')
    proof = source_proof(root, profile['source_origin'], profile['modules'])
    for key in ('source_origin', 'source_review', 'user_authority', 'access_registry', 'installed_at_utc',
                'transient_rehydration', 'data_alias_observation', 'platform_timezone_observation'):
        need(plan[key] == profile[key], 'FROZEN_V005_PLAN_PROFILE:' + key)
    expected = {r['name']: {k: r[k] for k in ('name', 'sha256', 'git_path')} for r in plan['source_modules']}
    actual = {r['name']: {k: r[k] for k in ('name', 'sha256', 'git_path')} for r in profile['modules']}
    need(expected == actual and nomination['merged_source_commit'] == proof['merge_commit']
         and nomination['root_review_receipt'] == plan['root_review'], 'FROZEN_V005_SOURCE_AND_NOMINATION')
    for row in plan['source_modules']: read(root, {k: row[k] for k in ('path', 'sha256')})
    review = object_at(root, plan['source_review'])[2]
    need(review['standard'] == 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-5'
         and review['review_scope'] == 'SOURCE_ONLY' and review['actual_live_runtime_admission'] is False
         and review['actual_seven_record_admission'] == 'PENDING_POST_INSTALL_FRESH_READBACK'
         and review['source_hashes'] == {r['name']: r['sha256'] for r in profile['modules']},
         'FROZEN_V005_SOURCE_REVIEW_SCOPE')
    need(same_binding(root, profile['data_alias_observation'], DATA_ALIAS_OBSERVATION)
         and same_binding(root, profile['platform_timezone_observation'], PLATFORM_TIMEZONE_OBSERVATION),
         'FROZEN_V005_FIXED_DATA_OBSERVATIONS')
    object_at(root, plan['root_review']); read(root, nomination['installer_source']); read(root, HISTORICAL_PUBLISHER)
    return {'status': 'EXACT_FROZEN_V001_V002_V003_V004_V005_INSTALLATIONS_SOURCE_READBACK_ONLY',
            'previous': previous, 'v005': {'profile': V005_PROFILE, 'nomination': V005_NOMINATION,
            'plan': V005_PLAN, 'merged_source': proof}, 'actual_runtime_admission': False, 'certifies': False}


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
    _,first,value=json_file(root,p)
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
    _,raw,nomination=json_file(root,nomination_path)
    need(set(nomination) == {'standard','status','profile','installer_source','merged_source_commit','root_review_receipt'}
         and nomination['standard'] == 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-6'
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
    _,raw,plan=json_file(root,plan_path)
    fields={'standard','status','canonical_root','source_modules','source_origin','source_review',
            'user_authority','access_registry','historical_publisher','installed_at_utc','root_review',
            'predecessor_installation','transient_rehydration','data_alias_observation','platform_timezone_observation'}
    need(set(plan)==fields and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-6'
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
         and review['standard']=='VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-6'
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
         and review['standard'] == 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-6'
         and review['status'] == 'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS'
         and isinstance(review['reviewer'], str) and review['reviewer']
         and review['source_hashes'] == hashes and review['legacy_closure'] == profile['legacy_closure']
         and review['scientific_admission_changed'] is False
         and review['historical_sources_changed'] is False
         and review['review_scope'] == 'SOURCE_ONLY'
         and review['actual_live_runtime_admission'] is False
         and review['actual_seven_record_admission'] == 'PENDING_POST_INSTALL_FRESH_READBACK', 'EXACT_INDEPENDENT_SOURCE_REVIEW')
    require_installed_plan(root,profile,nomination,proof)
    ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';_,ledger_raw=read_data_file(root,ledger_path)
    if _JSON_DATA.get() is None:json.loads(ledger_raw)
    else:parse_json_data(root,ledger_path,ledger_raw,copy_result=False)
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
    """Default v5 source scope: fresh byte checks plus pure parse DATA reuse."""
    with json_data_scope(root):
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
