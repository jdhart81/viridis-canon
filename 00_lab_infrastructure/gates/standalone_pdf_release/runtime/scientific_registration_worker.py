"""One-use live original scientific calls for the readonly health schedule.

This is an explicit evaluation transport, not an admission cache. Every job
calls the unchanged saved-registration function once. Only its corresponding
logical master call can consume the newly returned DATA, after a fresh replay
of the complete worker input union and exact source/argument/clock bindings.
"""
from __future__ import annotations
import argparse
import contextlib
import contextvars
from copy import deepcopy
import datetime as dt
import hashlib
import importlib
import importlib.machinery
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
import traceback
import types
import uuid
import warnings

# Python 3.14 re uses one identity-sensitive zero default. Keep the actual
# import-time objects; no other int subclass or equivalent copy is admitted.
_RE_ZERO_SENTINEL_TYPE = getattr(re, '_ZeroSentinel', None)
_RE_ZERO_SENTINEL = getattr(re, '_zero_sentinel', None)
_RE_ZERO_SENTINEL_CLASS_ITEMS = (tuple(vars(_RE_ZERO_SENTINEL_TYPE).items())
                               if _RE_ZERO_SENTINEL_TYPE is not None else ())

def _bootstrap_read(path, expected=None, identity=None):
    """Stdlib-only strict source checks before importing any runtime code."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('WORKER_BOOTSTRAP_ABSOLUTE_PATH')
    def sample():
        if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
            raise ValueError('WORKER_BOOTSTRAP_REGULAR_SOURCE')
        s = path.stat()
        if not stat.S_ISREG(s.st_mode):
            raise ValueError('WORKER_BOOTSTRAP_REGULAR_SOURCE')
        return {'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,
                'mtime_ns':s.st_mtime_ns}
    before = sample(); value = path.read_bytes(); readback = path.read_bytes(); after = sample()
    bound_identity = {**before, 'sha256':hashlib.sha256(value).hexdigest()}
    if before != after or value != readback or (identity is not None and bound_identity != identity):
        raise ValueError('WORKER_BOOTSTRAP_SOURCE_IDENTITY_RACE')
    if expected is not None and hashlib.sha256(value).hexdigest() != expected:
        raise ValueError('WORKER_BOOTSTRAP_SOURCE_HASH')
    return value


if not os.environ.get("VIRIDIS_CORE_ROOT"):
    raise RuntimeError("HOLD_CORE_ROOT_REQUIRED: set VIRIDIS_CORE_ROOT explicitly")
BOOTSTRAP_ROOT=Path(os.environ["VIRIDIS_CORE_ROOT"])
BOOTSTRAP_GIT_PREFIX='00_lab_infrastructure/gates/standalone_pdf_release/runtime/'
BOOTSTRAP_SHARED_NAME='stable_input_identity.py'
BOOTSTRAP_SHARED_SHA256='7e6c204993f0ba65650c58ad50a71073d803522d31fa08b93b7ce35054fa5eda'
BOOTSTRAP_SHARED_GIT_PATH='00_lab_infrastructure/gates/standalone_pdf_release/common/stable_input_identity.py'
BOOTSTRAP_MODULE_NAMES=frozenset({'packaging_runtime.py','invoke_digest_v2.py','digest_controller_v2.py',
    'methods_digest_v2.py','methods_digest_registration_v3.py','manuscript_access_registry.py',
    'manuscript_access_correction.py','manuscript_pdf_gate.py','publish_dated_bundles_guarded.py',
    'packaging_catalog.py','install_packaging_runtime.py',
    'packaging_nightly.py','nightly_checkpoint_guarded.py','packaging_run_flow.py',
    'packaging_nightly_coverage.py','packaging_nightly_intake.py','scientific_registration_worker.py',
    'owner_content_worker.py'})


def _bootstrap_artifacts(directory):
    if sys.pycache_prefix is not None:raise ValueError('WORKER_CURRENT_NAMESPACE_IMPORT_ARTIFACT:EXTERNAL_CACHE_PREFIX')
    probes=[Path(directory)/'__pycache__']
    probes.extend(Path(directory)/('publish_successor_wave_guarded'+suffix) for suffix in
        ('.py','','.pyc','.pyo',*importlib.machinery.EXTENSION_SUFFIXES))
    for name in sorted(BOOTSTRAP_MODULE_NAMES):
        stem=name[:-3]
        probes.extend(Path(directory)/(stem+suffix)for suffix in('', '.pyc','.pyo',*importlib.machinery.EXTENSION_SUFFIXES))
    for path in probes:
        if path.exists()or path.is_symlink():raise ValueError('WORKER_CURRENT_NAMESPACE_IMPORT_ARTIFACT:'+str(path))


def _bootstrap():
    # A master blocks these signals only while registering spawn ownership.
    # This normal exec child restores supervision before any source read.
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})
    _bootstrap_artifacts(Path(__file__).absolute().parent)
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--expected-config-sha256',required=True)
    args = parser.parse_args()
    config = json.loads(_bootstrap_read(args.config,args.expected_config_sha256))
    bound = config['source_manifest']
    manifest = json.loads(_bootstrap_read(bound['path'],bound['sha256']))
    root = BOOTSTRAP_ROOT
    fields = {'standard','canonical_root','profile_binding','modules','metadata','source_origin',
              'legacy_closure','source_review_change_flags','shared_dependencies'}
    if set(manifest) != fields or manifest['standard'] != 'VRS-CURRENT-DIGEST-ONLY-WORKER-SOURCE-MANIFEST-1' or manifest['canonical_root'] != str(root):
        raise ValueError('WORKER_BOOTSTRAP_CLOSED_FIXED_ROOT_MANIFEST')
    directory = root/'_ZENODO_DEPOSITS/standalone_pdf_runtime'
    names = {'profile':'CURRENT_PACKAGING_PROFILE.json','nomination':'INSTALLATION_NOMINATION.json','plan':'INSTALL_PLAN.json'}
    if len(manifest['modules']) != 18 or {r['name'] for r in manifest['modules']} != BOOTSTRAP_MODULE_NAMES or len(manifest['metadata']) != 3:
        raise ValueError('WORKER_BOOTSTRAP_EIGHTEEN_AND_THREE')
    metadata = {}
    for row in manifest['metadata']:
        if set(row) != {'role','path','sha256','identity'} or row['role'] not in names or row['role'] in metadata or Path(row['path']) != directory/names[row['role']]:
            raise ValueError('WORKER_BOOTSTRAP_FIXED_METADATA')
        metadata[row['role']] = json.loads(_bootstrap_read(row['path'],row['sha256'],row['identity']))
    profile_row = next(r for r in manifest['metadata'] if r['role']=='profile')
    profile_bound = {'path':profile_row['path'],'sha256':profile_row['sha256']}
    if manifest['profile_binding'] != profile_bound or metadata['nomination']['profile'] != profile_bound:
        raise ValueError('WORKER_BOOTSTRAP_NOMINATION_PROFILE')
    shared = manifest['shared_dependencies']
    if (not isinstance(shared,list) or len(shared)!=1 or not isinstance(shared[0],dict) or set(shared[0])!={'name','path','sha256','identity'}
            or shared[0]['name']!=BOOTSTRAP_SHARED_NAME or shared[0]['sha256']!=BOOTSTRAP_SHARED_SHA256
            or Path(shared[0]['path'])!=directory/'common'/BOOTSTRAP_SHARED_NAME):
        raise ValueError('WORKER_BOOTSTRAP_EXACT_SHARED_DEPENDENCY')
    _bootstrap_read(shared[0]['path'],shared[0]['sha256'],shared[0]['identity'])
    expected_shared=[{k:shared[0][k] for k in ('name','path','sha256')} | {'git_path':BOOTSTRAP_SHARED_GIT_PATH}]
    if metadata['profile'].get('shared_dependencies')!=expected_shared:
        raise ValueError('WORKER_BOOTSTRAP_SHARED_PROFILE_BINDING')
    module_rows = []
    for row in manifest['modules']:
        if set(row) != {'name','path','sha256','identity'} or Path(row['path']) != directory/row['name'] or '/' in row['name']:
            raise ValueError('WORKER_BOOTSTRAP_FIXED_MODULE')
        _bootstrap_read(row['path'],row['sha256'],row['identity'])
        module_rows.append({k:row[k] for k in ('name','path','sha256')})
    profile_rows=metadata['profile']['modules']
    if len(profile_rows)!=18 or any(set(r)!={'name','path','sha256','git_path'}
        or r['git_path']!=BOOTSTRAP_GIT_PREFIX+r['name']for r in profile_rows):
        raise ValueError('WORKER_BOOTSTRAP_CLOSED_FOUR_KEY_PROFILE_MODULES')
    projected=[{k:r[k]for k in('name','path','sha256')}for r in profile_rows]
    if sorted(module_rows,key=lambda r:r['name']) != sorted(projected,key=lambda r:r['name']):
        raise ValueError('WORKER_BOOTSTRAP_PROFILE_SOURCE_TABLE')
    self_row = next(r for r in manifest['modules'] if r['name']=='scientific_registration_worker.py')
    if Path(self_row['path']) != Path(__file__).absolute():
        raise ValueError('WORKER_BOOTSTRAP_EXACT_PUBLIC_ENTRY')


if __name__ == '__main__':
    _bootstrap()

import packaging_runtime as runtime

ROOT = Path(os.environ["VIRIDIS_CORE_ROOT"])
STAGES = ('build', 'activation_current_preserve', 'doi',
          'labels_initial_saved', 'labels_actual_views_saved')
PUB_FIELDS = frozenset({'publication_entities', 'publication_holds',
    'publication_registration_summary', 'publication_registration_enforcement_acceptable',
    'publication_registration_defects'})
CONFIG_STANDARD = 'VRS-V012-LIVE-ORIGINAL-SCIENTIFIC-CALL-1'
RESULT_STANDARD = 'VRS-V012-ONE-USE-LIVE-ORIGINAL-SCIENTIFIC-RESULT-1'
MAX_FRAME = 65536
SCIENTIFIC_HOLD_DEFINITIONS = (
    ('archive_053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7_methods_digest.py', '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5', 'DigestHold'),
    ('archive_053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7_phase7_audit_policy.py', '053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7', 'PolicyHold'),
    ('archive_053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7_publication_gate.py', '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1', 'PublicationGateHold'),
    ('archive_5d1832efb6d399d89e6d88d50034f8de10d46fc4247f1dd9f35fdabce3119768_methods_digest.py', 'fa114c3217f8c1bdb3655fe30df64b6c6d8eb84bf789e1d8652929d4d1e37c0c', 'DigestHold'),
    ('archive_5d1832efb6d399d89e6d88d50034f8de10d46fc4247f1dd9f35fdabce3119768_phase7_audit_policy.py', '5d1832efb6d399d89e6d88d50034f8de10d46fc4247f1dd9f35fdabce3119768', 'PolicyHold'),
    ('archive_5d1832efb6d399d89e6d88d50034f8de10d46fc4247f1dd9f35fdabce3119768_publication_gate.py', '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1', 'PublicationGateHold'),
    ('archive_66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654_methods_digest.py', '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5', 'DigestHold'),
    ('archive_66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654_phase7_audit_policy.py', '66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654', 'PolicyHold'),
    ('archive_66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654_publication_gate.py', '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1', 'PublicationGateHold'),
    ('archive_91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e_methods_digest.py', '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5', 'DigestHold'),
    ('archive_91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e_phase7_audit_policy.py', '91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e', 'PolicyHold'),
    ('archive_91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e_publication_gate.py', '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1', 'PublicationGateHold'),
    ('digest_metadata.py', 'e5c5cd3b7ca80d9c31c4adcafacc9bd357e440965a25baed291c99f70a4781fe', 'MetadataHold'),
    ('digest_public_state.py', 'b746fbbd4acc393799c75eb49bcc432e6c130e2b0858d8ed16082c8724127fe0', 'PublicStateHold'),
    ('digest_public_state_legacy_b5545.py', 'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38', 'PublicStateHold'),
    ('methods_digest.py', '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5', 'DigestHold'),
    ('methods_digest_registration.py', 'e97c6e906b6b2feeb348fc60dc0f4c22eac86cb23eac6f29afbf33dfe9df3cb5', 'RegistrationHold'),
    ('methods_digest_registration_legacy_0fc739.py', '0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9', 'RegistrationHold'),
    ('methods_digest_registration_legacy_21b813.py', '21b813c527566c12a06b15426c4a49370fd1e5ccbdcf9ca441bf5d305011d21c', 'RegistrationHold'),
    ('nightly_minimal_policy.py', '49cd0e2b4fd30670fcd83d983554afe7e1440dda0d8ab2cecee5fb91a871d42c', 'NightlyScopeHold'),
    ('own_prior_record.py', 'ff7d1b18bfad1a66662cc519415301a841b7ec05b9bc613dd8279d3644f8974f', 'PriorHold'),
    ('own_record_comparison.py', '55e9e4a070cd6d3ac0f0ceb5398d163b1f64c2463b41810bf82b63be537003bf', 'OwnRecordHold'),
    ('own_record_comparison_legacy_cf74da.py', 'cf74da23ea7208260cee70f74f282b2b57a209d1347f14d4c47b465f2b50ebd8', 'OwnRecordHold'),
    ('phase7_audit_policy.py', '91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e', 'PolicyHold'),
    ('publication_gate.py', '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1', 'PublicationGateHold'),
)

_STAGE = contextvars.ContextVar('v009_live_scientific_stage', default=None)
_WORKER_EFFECTS = contextvars.ContextVar('v009_readonly_science_worker_effects', default=None)
RESULT_FIELDS = frozenset({'standard','operation','job_nonce','stage','ordinal','binding','config',
    'profile','source_rows','environment','ledger','ledger_sha256','evaluation_kwargs','outcome',
    'original_result','original_hold','input_manifest','final_input_manifest','started_utc',
    'completed_utc','started_monotonic','completed_monotonic','source_finally_completed',
    'source_manifest','source_entry','source_exit','evaluation_state',
    'network_requests','ssot_writes','zenodo_writes','certifies'})


def _deny_worker_effect(event, args):
    output = _WORKER_EFFECTS.get()
    if output is None: return
    def evidence_path(value):
        if isinstance(value,int):return False
        path=Path(os.fsdecode(value))
        return(path.is_absolute()and'..'not in path.parts and path.is_relative_to(output)
               and not any(p.is_symlink()for p in(path,*path.parents)))
    if event in {'socket.connect','socket.getaddrinfo','urllib.Request','subprocess.Popen','os.system',
                 'os.fork','os.forkpty','os.posix_spawn','os.exec'} or event.startswith('os.spawn'):
        raise runtime.PackagingHold('READONLY_ORIGINAL_SCIENCE_EFFECT_DENIED:'+event)
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (
            mode is None and (flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
        if writing:
            runtime.need(evidence_path(path),
                         'READONLY_SCIENCE_WRITE_OUTSIDE_EXCLUSIVE_EVIDENCE')
    if event in {'os.mkdir','os.remove','os.rmdir','os.chmod','os.chown','os.utime','os.truncate'}:
        runtime.need(evidence_path(args[0]),
                     'READONLY_SCIENCE_FILESYSTEM_EFFECT_DENIED')
    if event in {'os.link','os.symlink'}:
        raise runtime.PackagingHold('READONLY_SCIENCE_LINK_EFFECT_DENIED')
    if event == 'os.rename':
        runtime.need(all(evidence_path(p)for p in args[:2]),
                     'READONLY_SCIENCE_FILESYSTEM_EFFECT_DENIED')


sys.addaudithook(_deny_worker_effect)


@contextlib.contextmanager
def worker_effect_scope(output):
    token=_WORKER_EFFECTS.set(Path(output))
    try:yield
    finally:_WORKER_EFFECTS.reset(token)


def raw(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'),allow_nan=False)+'\n').encode()


def binding(path):
    return {'path': str(path), 'sha256': runtime.sha(Path(path).read_bytes())}


def retain(path, value):
    path=Path(path)
    runtime.need(path.is_absolute()and'..'not in path.parts
                 and not any(p.is_symlink()for p in(path,*path.parents)), 'SCIENCE_EXCLUSIVE_REGULAR_OUTPUT')
    data = raw(value)
    if re.search(rb'(?i)(?:bearer[ \t]+[^ \t\r\n\"<>]+|(?:access_token|api_key|authorization)[\" \t]*[:=]|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})', data):
        raise runtime.PackagingHold('CREDENTIAL_PATTERN_IN_SCIENCE_EVIDENCE')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        s=os.fstat(fd);identity=(s.st_dev,s.st_ino,s.st_mode)
        remaining=memoryview(data)
        while remaining:
            current=os.fstat(fd)
            runtime.need((current.st_dev,current.st_ino,current.st_mode)==identity,'SCIENCE_OWNED_OUTPUT_FD')
            count=os.write(fd,remaining);runtime.need(count>0,'SCIENCE_EXCLUSIVE_WRITE_PROGRESS')
            remaining=remaining[count:]
        os.fsync(fd)
    finally:os.close(fd)
    runtime.need(not any(p.is_symlink()for p in(path,*path.parents)), 'SCIENCE_OUTPUT_PATH_RACE')
    runtime.need(Path(path).read_bytes() == data, 'SCIENCE_EXCLUSIVE_DATA_READBACK')
    return {'path': str(path), 'sha256': runtime.sha(data)}



# Evidence may retain the one read chunk that triggered the unchanged frame
# bound. This limit supplies no permission for accepting an oversized frame.
RAW_EVIDENCE_LIMIT = MAX_FRAME + 4 + 16384


def retain_raw(path, data):
    """Exact bounded private bytes; never an accepted worker result."""
    path = Path(path)
    runtime.need(type(data) is bytes and len(data) <= RAW_EVIDENCE_LIMIT,
                 'BOUNDED_PRIVATE_WORKER_STREAM')
    runtime.need(path.is_absolute() and '..' not in path.parts
                 and not any(p.is_symlink() for p in (path, *path.parents)),
                 'SCIENCE_EXCLUSIVE_REGULAR_OUTPUT')
    if re.search(rb'(?i)(?:bearer[ \t]+[^ \t\r\n"<>]+|(?:access_token|api_key|authorization)[" \t]*[:=]|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})', data):
        raise runtime.PackagingHold('CREDENTIAL_PATTERN_IN_SCIENCE_EVIDENCE')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        before = os.fstat(fd); identity = (before.st_dev, before.st_ino, before.st_mode)
        remaining = memoryview(data)
        while remaining:
            current = os.fstat(fd)
            runtime.need((current.st_dev, current.st_ino, current.st_mode) == identity,
                         'SCIENCE_OWNED_OUTPUT_FD')
            count = os.write(fd, remaining)
            runtime.need(count > 0, 'SCIENCE_EXCLUSIVE_WRITE_PROGRESS')
            remaining = remaining[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    runtime.need(not any(p.is_symlink() for p in (path, *path.parents))
                 and path.read_bytes() == data, 'SCIENCE_EXCLUSIVE_RAW_READBACK')
    return {'path': str(path), 'sha256': runtime.sha(data), 'bytes': len(data)}


def retain_process_output(state, code, phase, *, terminal=None, waited=False):
    """Retain received bytes before rejecting; EOF and partial capture are DATA."""
    state['capture_count'] += 1
    stem = str(state['journal']) + '-OUTPUT-' + str(state['capture_count'])
    outputs = {}
    for kind in ('out', 'err'):
        outputs[kind] = retain_raw(Path(stem + '-' + kind + '.bin'), bytes(state[kind]))
    value = {'standard': 'VRS-V012-ACTUAL-WORKER-OUTPUT-CAPTURE-1',
        'operation': state['operation'], 'job_nonce': state['config']['job_nonce'],
        'stage': state['config']['stage'], 'ordinal': state['config']['ordinal'],
        'config': state['binding'], 'source': state['source'],
        'actual_pid': state['child'].pid, 'actual_child_exit_code': code,
        'wait_completed': waited, 'phase': phase, 'terminal': terminal,
        'stdout': outputs['out'], 'stderr': outputs['err'],
        'stdout_eof_observed': 'out' in state['eof'],
        'stderr_eof_observed': 'err' in state['eof'],
        'capture_truncated': dict(state['truncated']),
        'stream_protocol_limit_bytes': MAX_FRAME + 4,
        'private_capture_limit_bytes': RAW_EVIDENCE_LIMIT,
        'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'completed_monotonic': time.monotonic(), 'source_finally_claimed': False,
        'result_accepted': False, 'certifies': False}
    return retain(Path(stem + '-CAPTURE.json'), value)


def drain_cleanup_output(state, selector):
    """Drain owned nonblocking pipes after actual wait, with no unbounded loop."""
    for fd in list(state['open']):
        key = selector.get_key(fd); bound_state, kind, identity = key.data
        runtime.need(bound_state is state and fd in state['owned'], 'SCIENCE_CLEANUP_PIPE_OWNER')
        while True:
            current = os.fstat(fd)
            runtime.need((current.st_dev, current.st_ino, current.st_mode) == identity,
                         'SCIENCE_OWNED_PIPE_IDENTITY')
            try:
                chunk = os.read(fd, 16384)
            except BlockingIOError:
                break
            if not chunk:
                state['eof'].add(kind)
                break
            room = RAW_EVIDENCE_LIMIT - len(state[kind])
            state[kind].extend(chunk[:max(0, room)])
            if len(chunk) > room:
                state['truncated'][kind] = True
                break


def retain_worker_exception(state, config_path, expected, exc):
    """Trusted-output phase/exception DATA, after genuine scopes unwind."""
    output = state['output']
    trace = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)).encode()
    clipped = trace[:RAW_EVIDENCE_LIMIT]
    trace_bound = retain_raw(output / 'WORKER_EXCEPTION_TRACEBACK.bin', clipped)
    return retain(output / 'WORKER_EXCEPTION.json', {
        'standard': 'VRS-V012-TRUSTED-WORKER-EXCEPTION-DATA-1',
        'config': {'path': str(config_path), 'sha256': expected},
        'operation': state['config']['operation'], 'job_nonce': state['config']['job_nonce'],
        'stage': state['config']['stage'], 'ordinal': state['config']['ordinal'],
        'actual_pid': os.getpid(), 'last_entered_phase': state['phase'],
        'exception_class': {'module': type(exc).__module__, 'name': type(exc).__qualname__},
        'traceback': trace_bound, 'traceback_truncated': len(trace) > len(clipped),
        'traceback_original_bytes': len(trace),
        'source_entry': state['source_entry'], 'source_exit': state['source_exit'],
        'original_call_started': state['original_call_started'],
        'original_call_returned': state['original_call_returned'],
        'evaluation_state_mismatch': state.get('evaluation_state_mismatch'),
        'source_finally_claimed': False, 'result_accepted': False, 'certifies': False})


def worker(config_path, expected):
    state = {'phase': 'CLOSED_CONFIG_SOURCE', 'output': None, 'config': None,
             'source_entry': None, 'source_exit': None,
             'original_call_started': False, 'original_call_returned': False}
    try:
        return _worker_body(config_path, expected, state)
    except BaseException as exc:
        if state['output'] is not None:
            try:
                with worker_effect_scope(state['output']):
                    retain_worker_exception(state, config_path, expected, exc)
            except BaseException as retention_error:
                if hasattr(exc, 'add_note'):
                    exc.add_note('Worker exception DATA retention unavailable: ' + type(retention_error).__name__)
        raise


def environment():
    """Closed worker launch environment; no credential-bearing environment."""
    value = {k: v for k, v in os.environ.items()
             if not re.search(r'TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY|ACCESS_KEY', k, re.I)}
    return value


def environment_frame(value=None):
    value = dict(os.environ) if value is None else value
    return {'complete_environment_sha256': runtime.sha(raw(value)),
            'timezone': value.get('TZ'), 'python_timezone_path': value.get('PYTHONTZPATH'),
            'python_path': value.get('PYTHONPATH'), 'python_home': value.get('PYTHONHOME'),
            'current_working_directory':os.getcwd(),
            'interpreter': sys.executable,
            'interpreter_physical_path':str(Path(sys.executable).resolve(strict=True)),
            'version': sys.version, 'platform': sys.platform,
            'launch_policy':'INHERITED_ENVIRONMENT_WITH_TOKEN_SECRET_PASSWORD_CREDENTIAL_API_KEY_ACCESS_KEY_NAMES_REMOVED'}


def source_rows(root, profile):
    rows = runtime.object_at(root, profile)[2]['modules']
    runtime.need(len(rows) == 18 and len({r['name'] for r in rows}) == 18,
                 'SCIENCE_CURRENT_EIGHTEEN_SOURCES')
    for row in rows:
        runtime.read(root, {k: row[k] for k in ('path', 'sha256')})
    return deepcopy(rows)


def argument_projection(ledger):
    runtime.need(ledger is None or isinstance(ledger, dict), 'SCIENCE_WHOLE_LEDGER_ARGUMENT')
    return None if ledger is None else {k: v for k, v in ledger.items() if k not in PUB_FIELDS}


def _code_constant(value):
    """Closed immutable constant DATA; no allocation or interning metadata."""
    if value is None:return {'kind':'None'}
    if value is Ellipsis:return {'kind':'Ellipsis'}
    if type(value)is bool:return {'kind':'bool','value':value}
    if type(value)is int:return {'kind':'int','value':value}
    if type(value)is float:return {'kind':'float','ieee754_binary64':struct.pack('!d',value).hex()}
    if type(value)is complex:
        return {'kind':'complex','real_ieee754_binary64':struct.pack('!d',value.real).hex(),
                'imag_ieee754_binary64':struct.pack('!d',value.imag).hex()}
    if type(value)is str:return {'kind':'str','utf8_surrogatepass_hex':value.encode('utf-8','surrogatepass').hex()}
    if type(value)is bytes:return {'kind':'bytes','hex':value.hex()}
    if type(value)is tuple:return {'kind':'tuple','items':[_code_constant(v)for v in value]}
    if type(value)is frozenset:
        return {'kind':'frozenset','items':sorted((_code_constant(v)for v in value),key=raw)}
    if type(value)is slice:
        return {'kind':'slice','start':_code_constant(value.start),
                'stop':_code_constant(value.stop),'step':_code_constant(value.step)}
    if type(value)is types.CodeType:return _code_projection(value)
    raise runtime.PackagingHold('UNSUPPORTED_IMMUTABLE_CODE_CONSTANT:'+type(value).__name__)


def _code_projection(code):
    """All public semantic CodeType fields, freshly projected without marshal.

    The exact bytecode, exception/line tables and recursive typed constants
    bind semantics; adaptive cache, refcounts and intern flags do not. Derived
    public line/position/branch views are retained as well. Unknown public
    co_* fields HOLD rather than silently dropping future semantics.
    """
    runtime.need(type(code)is types.CodeType,'EXACT_IMMUTABLE_CODE_TYPE')
    fields=('co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals',
            'co_stacksize','co_flags','co_code','co_consts','co_names','co_varnames',
            'co_filename','co_name','co_qualname','co_firstlineno','co_linetable',
            'co_exceptiontable','co_freevars','co_cellvars')
    optional_fields=('co_lnotab',)
    methods=('co_lines','co_positions')
    optional_methods=('co_branches',)
    actual={name for name in dir(code)if name.startswith('co_')}
    allowed=set(fields+optional_fields+methods+optional_methods)
    runtime.need(set(fields+methods).issubset(actual)and actual.issubset(allowed),
                 'COMPLETE_KNOWN_PUBLIC_CODE_FIELDS')
    values={name:_code_constant(_code_lnotab(code)if name=='co_lnotab'else getattr(code,name))
            for name in fields+optional_fields if name in actual}
    derived={name:_code_constant(tuple(getattr(code,name)()))
             for name in methods+optional_methods if name in actual}
    return {'kind':'CODE','standard':'VRS-DETERMINISTIC-COMPLETE-CODETYPE-DATA-1',
            'public_fields':sorted(actual),'fields':values,'derived':derived}


def _code_lnotab(code):
    # Reading this exact derived public field emits a deprecation notice in
    # current CPython. Only this DATA accessor is inside the restoring scope;
    # no scientific call, other getter or unrelated warning is suppressed.
    runtime.need(type(code)is types.CodeType,'EXACT_IMMUTABLE_CODE_TYPE')
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',
            message=r'^co_lnotab is deprecated, use co_lines instead\.$',
            category=DeprecationWarning,module=r'^'+re.escape(__name__)+r'$')
        return code.co_lnotab


def _definition(value):
    if isinstance(value, types.FunctionType):
        literals={}
        # Scope is source-defined scientific globals. Stdlib private scratch
        # caches (e.g. deepcopy dispatch with self-referential defaults) are
        # not recursively serialized as scientific qualifier state.
        names=(value.__code__.co_names if Path(value.__code__.co_filename).is_relative_to(ROOT)else())
        for name in names:
            if name not in value.__globals__:continue
            item=value.__globals__[name]
            if isinstance(item,types.ModuleType)or callable(item):continue
            literals[name]=_dependency(item)
        code_projection=_code_projection(value.__code__)
        return {'kind':'SOURCE_FUNCTION','module':value.__module__,'name':value.__qualname__,
                'code_sha256':runtime.sha(raw(code_projection)),
                'code_projection':code_projection,
                'defaults':[_dependency(v)for v in(value.__defaults__ or())],
                'keyword_defaults':{k:_dependency(v)for k,v in(value.__kwdefaults__ or{}).items()},
                'source_referenced_literal_globals':literals}
    if isinstance(value,type):
        return {'kind':'CLASS','module':value.__module__,'name':value.__qualname__,
                'bases':[[c.__module__,c.__qualname__]for c in value.__bases__],
                'methods':{k:_definition(v)for k,v in vars(value).items()if isinstance(v,types.FunctionType)}}
    if callable(value):
        return {'kind':'NATIVE_CALLABLE','module':getattr(value,'__module__',None),
                'name':getattr(value,'__qualname__',getattr(value,'__name__',None))}
    raise runtime.PackagingHold('UNSUPPORTED_SOURCE_DEFINITION')


def _re_zero_sentinel_dependency(value, *, sentinel=_RE_ZERO_SENTINEL,
        sentinel_type=_RE_ZERO_SENTINEL_TYPE,
        class_items=_RE_ZERO_SENTINEL_CLASS_ITEMS):
    runtime.need(sentinel is not None and sentinel_type is not None and
                 value is sentinel and type(value) is sentinel_type and
                 re.__dict__.get('_zero_sentinel') is sentinel and
                 re.__dict__.get('_ZeroSentinel') is sentinel_type,
                 'EXACT_STDLIB_RE_ZERO_SENTINEL_IDENTITY_AND_BINDING')
    current=vars(sentinel_type)
    runtime.need(tuple(current)==tuple(k for k,_ in class_items) and
                 all(type(current[k]) is type(v) and
                     (current[k]==v if type(v) in(str,int,bool,type(None),tuple)
                      else current[k] is v) for k,v in class_items) and
                 sentinel_type.__module__=='re' and
                 sentinel_type.__name__=='_ZeroSentinel' and
                 sentinel_type.__qualname__=='_ZeroSentinel' and
                 sentinel_type.__bases__==(int,) and
                 int.__int__(value)==0 and vars(value)=={},
                 'EXACT_STDLIB_RE_ZERO_SENTINEL_CLASS_VALUE_AND_STATE')
    return {'kind':'STDLIB_RE_ZERO_SENTINEL','module':'re',
            'type_definition':_definition(sentinel_type),
            'integer_value':0,'instance_state':{}}


def _dependency(value):
    if value is None or type(value) in (str,int,float,bool): return value
    if _RE_ZERO_SENTINEL is not None and (value is _RE_ZERO_SENTINEL or
                                        type(value) is _RE_ZERO_SENTINEL_TYPE):
        return _re_zero_sentinel_dependency(value)
    if type(value)is bytes:return {'kind':'bytes','hex':value.hex()}
    if isinstance(value,re.Pattern):return {'kind':'REGEX','pattern':_dependency(value.pattern),'flags':value.flags}
    if isinstance(value,Path):return {'kind':'LEXICAL_PATH','value':str(value)}
    if type(value) in (list,tuple):return {'kind':type(value).__name__,'items':[_dependency(v)for v in value]}
    if type(value) in (set,frozenset):return {'kind':type(value).__name__,'items':sorted((_dependency(v)for v in value),key=lambda v:raw(v))}
    if type(value) is dict:
        runtime.need(all(type(k)is str for k in value),'SOURCE_GLOBAL_STRING_KEYS')
        return {'kind':'dict','items':{k:_dependency(v)for k,v in value.items()}}
    if isinstance(value,types.ModuleType):
        p=getattr(value,'__file__',None)
        return {'kind':'MODULE','name':value.__name__,
                'source':None if p is None else {'path':str(p),'sha256':runtime.sha(Path(p).read_bytes())},
                'source_defined_functions':{k:_definition(v)for k,v in vars(value).items()
                    if isinstance(v,types.FunctionType)and v.__module__==value.__name__}}
    if callable(value):return _definition(value)
    raise runtime.PackagingHold('UNSUPPORTED_REFERENCED_SCIENTIFIC_GLOBAL:'+type(value).__name__)


HISTORICAL_STATE_ENTRY = ('methods_digest_registration_legacy_0fc739',
    '0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9')


def evaluation_state():
    """Live code/default and source-defined referenced global DATA, not a verdict."""
    registration=importlib.import_module('methods_digest_registration_v3')
    original=registration._original_registrar()
    # The original historical dispatcher stores module names as strings and
    # imports the selected registrar locally. A module/dict DATA frame for
    # that string table therefore cannot capture this entry's own defaults
    # or transitively referenced globals. Admit its fixed public source row,
    # then inspect definitions only; no original scientific call is made.
    historical_name,historical_sha=HISTORICAL_STATE_ENTRY
    runtime.need(original._HISTORICAL_PRIOR_REGISTRARS.get(historical_sha)==historical_name,
                 'EXACT_HISTORICAL_STATE_DISPATCH')
    historical=importlib.import_module(historical_name)
    runtime.need(runtime.sha(Path(historical.__file__).read_bytes())==historical_sha,
                 'EXACT_HISTORICAL_STATE_SOURCE')
    functions=(registration.require_registration,original.require_registration,
               historical.require_registration)
    result=[]
    for entry in functions:
        pending=[entry];seen=set();definitions={};globals_used={}
        while pending:
            function=pending.pop()
            if id(function)in seen:continue
            seen.add(id(function));definitions[function.__qualname__]=_definition(function)
            for name in function.__code__.co_names:
                if name not in function.__globals__:continue
                value=function.__globals__[name]
                globals_used[name]=_dependency(value)
                if isinstance(value,types.FunctionType)and value.__module__==entry.__module__:pending.append(value)
        result.append({'entry':_definition(entry),'definitions':definitions,'referenced_globals':globals_used})
    return result


def _evaluation_state_differences(expected,actual,path=()):
    """Typed JSON leaf DATA, never a substitute for the full equality gate."""
    if type(expected)is not type(actual):
        return [{'path':list(path),'kind':'TYPE','expected_type':type(expected).__name__,
                 'actual_type':type(actual).__name__,'expected':expected,'actual':actual}]
    if type(expected)is dict:
        result=[]
        for key in sorted(set(expected)|set(actual)):
            if key not in expected:
                result.append({'path':list(path+(key,)),'kind':'ADDED','actual':actual[key]})
            elif key not in actual:
                result.append({'path':list(path+(key,)),'kind':'REMOVED','expected':expected[key]})
            else:result.extend(_evaluation_state_differences(expected[key],actual[key],path+(key,)))
        return result
    if type(expected)is list:
        result=[]
        for index in range(max(len(expected),len(actual))):
            if index>=len(expected):result.append({'path':list(path+(index,)),'kind':'ADDED','actual':actual[index]})
            elif index>=len(actual):result.append({'path':list(path+(index,)),'kind':'REMOVED','expected':expected[index]})
            else:result.extend(_evaluation_state_differences(expected[index],actual[index],path+(index,)))
        return result
    return []if expected==actual else[{'path':list(path),'kind':'VALUE','expected':expected,'actual':actual}]


def _require_evaluation_state(config,state,config_binding,reason):
    """Retain complete trusted comparison DATA before the unchanged HOLD."""
    actual=evaluation_state();expected=config['evaluation_state'];retention_error=None
    if actual!=expected:
        try:
            phase=state['phase']
            runtime.need(phase in('COMPARE_EVALUATION_STATE_BEFORE','COMPARE_EVALUATION_STATE_AFTER'),
                         'TRUSTED_EVALUATION_MISMATCH_PHASE')
            state['evaluation_state_mismatch']=retain(state['output']/(phase+'_MISMATCH.json'),{
                'standard':'VRS-V012-TRUSTED-EVALUATION-STATE-MISMATCH-DATA-1',
                'status':'ACTUAL_STATE_COMPARISON_MISMATCH_NOT_ADMITTED','config':config_binding,
                'operation':config['operation'],'job_nonce':config['job_nonce'],
                'stage':config['stage'],'ordinal':config['ordinal'],'actual_pid':os.getpid(),
                'phase':phase,'expected':expected,'actual':actual,
                'expected_sha256':runtime.sha(raw(expected)),'actual_sha256':runtime.sha(raw(actual)),
                'differences':_evaluation_state_differences(expected,actual),
                'original_call_started':state['original_call_started'],
                'original_call_returned':state['original_call_returned'],
                'source_finally_claimed':False,'result_accepted':False,'certifies':False})
        except BaseException as exc:retention_error=exc
    try:runtime.need(actual==expected,reason)
    except BaseException as exc:
        if retention_error is not None and hasattr(exc,'add_note'):
            exc.add_note('Evaluation mismatch DATA retention unavailable: '+type(retention_error).__name__)
        raise


def _hold_source(root, public_name, expected_hash, class_name):
    runtime.need((public_name+'.py',expected_hash,class_name)in SCIENTIFIC_HOLD_DEFINITIONS,
                 'CLOSED_ORIGINAL_SCIENTIFIC_EXCEPTION_DEFINITION')
    scope=runtime.object_at(root,runtime.LEGACY_SCOPE)[2]
    rows=[r for r in scope['purpose_source_pins']if r['name']==public_name+'.py'and r['sha256']==expected_hash]
    runtime.need(len(rows)==1,'EXACT_ORIGINAL_EXCEPTION_SOURCE_PIN')
    path=Path(rows[0]['path']);path=path if path.is_absolute()else Path(root)/path
    runtime.read(root,{'path':str(path),'sha256':expected_hash})
    return path


def original_hold(root, exc):
    """Source-defined scientific exception from the actual saved call only.

    The definition list is literal reviewed source DATA, not a name suffix or
    remote module import. Unknown/builtin/transport/source errors stay infra.
    """
    frames = []; frame = exc.__traceback__; last=None
    while frame is not None:
        last=frame
        path = Path(frame.tb_frame.f_code.co_filename)
        if path.is_file():
            frames.append({'path': str(path), 'sha256': runtime.sha(path.read_bytes()),
                           'function': frame.tb_frame.f_code.co_name, 'line': frame.tb_lineno,
                           'module':frame.tb_frame.f_globals.get('__name__')})
        frame = frame.tb_next
    if last is None:return None
    cls=type(exc);g=last.tb_frame.f_globals
    if g.get(cls.__name__)is not cls or g.get('__name__')!=cls.__module__:return None
    raising=Path(last.tb_frame.f_code.co_filename)
    for public,expected,class_name in SCIENTIFIC_HOLD_DEFINITIONS:
        if class_name!=cls.__name__:continue
        path=_hold_source(root,public[:-3],expected,class_name)
        if path!=raising:continue
        runtime.need(cls.__qualname__==class_name and cls.__bases__==(ValueError,), 'EXACT_SCIENTIFIC_CLASS_IDENTITY')
        runtime.need(any(f['function']=='require_registration'for f in frames),'ACTUAL_ORIGINAL_REGISTRATION_EXCEPTION_STACK')
        return {'module':cls.__module__,'class':class_name,'public_source_module':public[:-3],
                'source':{'path':str(path),'sha256':expected},'message':str(exc),'frames':frames}
    return None


def resolved_hold(root, value):
    runtime.need(set(value)=={'module','class','public_source_module','source','message','frames'},
                 'CLOSED_ACTUAL_SOURCE_SCIENTIFIC_HOLD')
    source=value['source'];path=_hold_source(root,value['public_source_module'],source['sha256'],value['class'])
    runtime.need(source['path']==str(path)and value['frames'][-1]['path']==str(path)
                 and value['frames'][-1]['sha256']==source['sha256']
                 and value['frames'][-1]['module']==value['module']
                 and re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',value['module'])is not None,
                 'EXACT_ORIGINAL_RAISING_SOURCE')
    # Import a literal admitted public SourceFinder row, never an arbitrary
    # received module name or a private loader. No predicate is called here.
    module=importlib.import_module(value['public_source_module'])
    runtime.need(Path(module.__file__)==path and runtime.sha(path.read_bytes())==source['sha256'],
                 'ACTUAL_LOADED_ORIGINAL_EXCEPTION_SOURCE')
    cls=getattr(module,value['class'],None)
    runtime.need(isinstance(cls,type)and cls.__bases__==(ValueError,)
                 and cls.__module__==module.__name__ and cls.__qualname__==value['class'],
                 'ACTUAL_SOURCE_DEFINED_EXCEPTION_CLASS')
    # Historical consumers may compile the exact pinned file under a private
    # source-qualified namespace. This transport imports its fixed public
    # SourceFinder row, so object identity/module names across processes are
    # not asserted equal. The literal definition/source/class/message are;
    # the unchanged fold records only class name and message. Both namespaces
    # are retained below as actual evidence, without remote module imports.
    return cls(value['message'])


def _worker_body(config_path, expected, state):
    """Normal public entry, no original import before closed source admission."""
    root = ROOT.resolve(strict=True); profile = runtime.nominated_binding(root)
    _, config_bytes, config = runtime.object_at(root, {'path': str(config_path), 'sha256': expected})
    fields = {'standard', 'operation', 'job_nonce', 'stage', 'ordinal', 'root', 'profile',
              'source_rows', 'source_manifest', 'binding', 'ledger', 'ledger_sha256', 'environment', 'output',
              'evaluation_kwargs', 'evaluation_state', 'started_utc', 'started_monotonic'}
    runtime.need(set(config) == fields and config['standard'] == CONFIG_STANDARD
                 and config['root'] == str(root) and config['profile'] == profile
                 and config['stage'] in STAGES and type(config['ordinal']) is int,
                 'CLOSED_SOURCE_BOUND_LIVE_SCIENCE_CONFIG')
    for key in ('operation', 'job_nonce'):
        runtime.need(re.fullmatch('[0-9a-f]{32}', config[key]) is not None, 'LIVE_SCIENCE_NONCE')
    runtime.need(config['evaluation_kwargs'] == {'views': None, 'prior_chain_receipts': None},
                 'EXACT_ORIGINAL_DEFAULT_SAVED_SCIENCE_SIGNATURE')
    runtime.need(environment_frame() == config['environment'], 'LIVE_SCIENCE_ENVIRONMENT')
    runtime.need(source_rows(root, profile) == config['source_rows'], 'LIVE_SCIENCE_SOURCE_TABLE')
    output = Path(config['output'])
    runtime.need(output.is_absolute() and output.is_relative_to(root/'reports/verification-coverage')
                 and not output.exists() and not any(p.is_symlink() for p in (output, *output.parents)),
                 'EXCLUSIVE_LIVE_SCIENCE_OUTPUT')
    output.mkdir()
    state.update(output=output, config=config, phase='SOURCE_ENTRY')
    outcome = None; material = None; hold = None; manifest = None
    started = time.monotonic(); started_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    with worker_effect_scope(output), runtime.readonly_worker_scope():
        manifest_value = runtime.object_at(root, config['source_manifest'])[2]
        source_entry = runtime.verify_worker_source_manifest(root, profile, manifest_value)
        state.update(source_entry=source_entry, phase='SOURCE_SESSION_AND_OPERATION')
        with runtime.session(root, profile) as source_admission:
            catalog = importlib.import_module('packaging_catalog')
            registry = importlib.import_module('manuscript_access_registry')
            def denied(*args, **kwargs):
                raise runtime.PackagingHold('READONLY_SCIENCE_WORKER_NETWORK_DENIED')
            context = registry.RegistryContext(root, source_admission['access_registry'],
                download=denied, owner_getter=denied, observation_context=registry.CONTEXT)
            context.owner_evidence_directory = output
            with catalog.operation_scope(root, profile, context):
                data = catalog.scientific_data(root)
                state['phase'] = 'WHOLE_LEDGER_ARGUMENT'
                if config['ledger'] is None:
                    runtime.need(config['stage'].startswith('labels_'), 'LABEL_NONE_STAGE_ONLY')
                    inventory_ledger = runtime.json_file(root, root/'RESEARCH_PIPELINE_v2/corpus_ledger.json')[2]
                    ledger = None
                else:
                    ledger = runtime.object_at(root, config['ledger'])[2]
                    runtime.need(runtime.sha(raw(ledger)) == config['ledger_sha256'], 'WHOLE_WORKER_LEDGER_HASH')
                    inventory_ledger = ledger
                corpus = importlib.import_module('corpus_ledger')
                state['phase'] = 'CAPTURE_INVENTORY'
                data.capture_inventory(corpus, root/'RESEARCH_PIPELINE_v2/lean_certificates', inventory_ledger)
                registration = importlib.import_module('methods_digest_registration_v3')
                state['phase'] = 'COMPARE_EVALUATION_STATE_BEFORE'
                _require_evaluation_state(config,state,{'path':str(config_path),'sha256':expected},
                                          'LIVE_ORIGINAL_FUNCTION_DEFAULT_GLOBALS')
                effect_token = _WORKER_EFFECTS.set(output)
                try:
                    try:
                        state.update(phase='ORIGINAL_REGISTRATION', original_call_started=True)
                        material = registration.require_registration(root, config['binding'], ledger,
                                            views=None, prior_chain_receipts=None)
                        outcome = 'SCIENCE_RESULT'
                        state['original_call_returned'] = True
                    except Exception as exc:
                        hold = original_hold(root,exc)
                        if hold is None:
                            raise
                        outcome = 'SCIENTIFIC_HOLD'
                finally:
                    _WORKER_EFFECTS.reset(effect_token)
                state['phase'] = 'COMPARE_EVALUATION_STATE_AFTER'
                _require_evaluation_state(config,state,{'path':str(config_path),'sha256':expected},
                                          'LIVE_ORIGINAL_GLOBALS_CHANGED_DURING_CALL')
                state['phase'] = 'INPUT_REHASH_AND_INITIAL_MANIFEST'
                data.assert_current(); data.retain_manifest(); manifest = deepcopy(data.manifest)
            state['phase'] = 'OBSERVER_EXIT'
            runtime.need(data.final_manifest is not None, 'ACTUAL_WORKER_OBSERVER_EXIT')
            final_manifest = deepcopy(data.final_manifest)
        state['phase'] = 'SOURCE_FINAL'
        source_exit = runtime.verify_worker_source_manifest(root, profile, manifest_value)
        state['source_exit'] = source_exit
    # Output is emitted only after genuine observer and original source finally.
    completed_utc = dt.datetime.now(dt.timezone.utc).isoformat(); completed = time.monotonic()
    state['phase'] = 'SOURCE_ROWS_AND_ENVIRONMENT_FINAL'
    runtime.need(source_rows(root, profile) == config['source_rows'], 'LIVE_SCIENCE_SOURCE_EXIT')
    runtime.need(environment_frame() == config['environment'], 'LIVE_SCIENCE_ENVIRONMENT_EXIT')
    value = {'standard': RESULT_STANDARD, 'operation': config['operation'], 'job_nonce': config['job_nonce'],
        'stage': config['stage'], 'ordinal': config['ordinal'], 'binding': config['binding'],
        'config': {'path': str(config_path), 'sha256': expected}, 'profile': profile,
        'source_rows': config['source_rows'], 'environment': config['environment'],
        'ledger': config['ledger'], 'ledger_sha256': config['ledger_sha256'],
        'evaluation_kwargs': config['evaluation_kwargs'], 'outcome': outcome,
        'original_result': material, 'original_hold': hold, 'input_manifest': manifest,
        'final_input_manifest': final_manifest, 'started_utc': started_utc,
        'source_manifest':config['source_manifest'],'source_entry':source_entry,'source_exit':source_exit,
        'evaluation_state':config['evaluation_state'],
        'completed_utc': completed_utc, 'started_monotonic': started,
        'completed_monotonic': completed, 'source_finally_completed': True,
        'network_requests': 0, 'ssot_writes': 0, 'zenodo_writes': 0, 'certifies': False}
    state['phase'] = 'RETAIN_RESULT_AND_PIPE_FRAME'
    bound = retain(output/'ORIGINAL_FUNCTION_RESULT.json', value)
    frame = raw({'result': bound, 'pid': os.getpid(), 'job_nonce': config['job_nonce']})
    runtime.need(len(frame) <= MAX_FRAME, 'SCIENCE_RESULT_FRAME_SIZE')
    wire = struct.pack('!I', len(frame))+frame
    while wire:
        n = os.write(1, wire); runtime.need(n > 0, 'SCIENCE_RESULT_PIPE'); wire = wire[n:]
    return 0


class ScienceBatch:
    """One active readonly health operation; no cross-call or phase memoization."""
    def __init__(self, root, profile, context, previous, scan_data, output):
        self.root = Path(root).resolve(strict=True); self.profile = deepcopy(profile)
        self.context = context; self.previous = deepcopy(previous); self.baseline = deepcopy(scan_data)
        self.output = Path(output)/'live-science'; self.operation = uuid.uuid4().hex
        self.jobs = {}; self.used = set(); self.union = {}; self.prepared = False; self.closed = False
        self.consumptions=[]
        self.source_table = source_rows(self.root, profile)
        self.env = environment(); self.env_frame = environment_frame(self.env)
        self.qualification_utc = None
        self.evaluation_state = None

    @contextlib.contextmanager
    def stage(self, name):
        runtime.need(name in STAGES and self.prepared and not self.closed, 'LIVE_SCIENCE_STAGE')
        token = _STAGE.set((self, name))
        try:
            yield
        finally:
            _STAGE.reset(token)

    def _key(self, stage, bound):
        return stage, raw(bound)

    def prepare(self):
        runtime.need(not self.prepared and not self.closed, 'LIVE_SCIENCE_BATCH_ONCE')
        catalog = importlib.import_module('packaging_catalog')
        data = catalog.scientific_data(self.root)
        runtime.need(data.scan_data == self.baseline and not data.cas_events and data.pending_cas is None,
                     'READONLY_PARENT_ONCE_FRESH_SCAN_BASELINE')
        entries = self.context._registry()[0]['entries']
        # Saved science remains one original views=None call per record/stage.
        # A historical BEFORE_ACCESS processing chain is composed separately
        # by the unchanged master registry after that saved scientific call.
        chain_fields = {'baseline_legacy', 'baseline_native', 'creation', 'publish', 'stage'}
        runtime.need(len(entries) == 7 and all(e['archive'] is not None
            and (e['prior_chain'] is None or (type(e['prior_chain']) is dict
                and set(e['prior_chain']) == chain_fields
                and e['prior_chain']['stage'] == 'BEFORE_ACCESS')) for e in entries),
                     'EXACT_SEVEN_ACCESS_SAVED_REGISTRATION_BATCH')
        groups = {raw(r['registration_receipt']) for r in self.previous['publication_entities']
                  if r.get('entity_type') == 'METHODS_DIGEST_GROUP' or r.get('registration_route') == 'METHODS_DIGEST_GROUP_V1'}
        runtime.need(groups == {raw(e['registration']) for e in entries}, 'COMPLETE_SEVEN_GROUP_BINDINGS')
        self.output.mkdir(exist_ok=False)
        ledger_binding = retain(self.output/'WHOLE_SCANNER_LEDGER_ARGUMENT.json', self.baseline)
        manifest_value = runtime.build_worker_source_manifest(self.root, self.profile)
        manifest_binding = retain(self.output/'WORKER_SOURCE_MANIFEST.json', manifest_value)
        self.evaluation_state = evaluation_state()
        planned = []
        for stage in STAGES:
            for ordinal, entry in enumerate(entries):
                nonce = uuid.uuid4().hex; folder = self.output/(stage+'-'+str(ordinal))
                config = {'standard': CONFIG_STANDARD, 'operation': self.operation, 'job_nonce': nonce,
                    'stage': stage, 'ordinal': ordinal, 'root': str(self.root), 'profile': self.profile,
                    'source_rows': self.source_table, 'binding': deepcopy(entry['registration']),
                    'source_manifest':manifest_binding,
                    'ledger': None if stage.startswith('labels_') else ledger_binding,
                    'ledger_sha256': None if stage.startswith('labels_') else runtime.sha(raw(self.baseline)),
                    'environment': self.env_frame, 'output': str(folder),
                    'evaluation_state':self.evaluation_state,
                    'evaluation_kwargs': {'views': None, 'prior_chain_receipts': None},
                    'started_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'started_monotonic': time.monotonic()}
                config_bound = retain(self.output/(stage+'-'+str(ordinal)+'-CONFIG.json'), config)
                planned.append((config, config_bound))
        self._execute(planned)
        runtime.need(len(self.jobs) == 35, 'ALL_THIRTY_FIVE_DISTINCT_LIVE_CALLS')
        self.qualification_utc = dt.datetime.now(dt.timezone.utc).isoformat()
        self.prepared = True
        self._fresh_union()
        self.context.scientific_consumer = self.require
        self.context.scientific_batch = self

    def _execute(self, planned):
        """Bounded process pipes are drained concurrently before any wait."""
        active = {}; selector = selectors.DefaultSelector(); todo = list(planned)
        deadline = time.monotonic()+3000
        def launch(item):
            config, config_bound = item
            runtime.need(source_rows(self.root, self.profile) == self.source_table, 'SCIENCE_PREEXEC_SOURCES')
            manifest = runtime.object_at(self.root, config['source_manifest'])[2]
            runtime.need(runtime.build_worker_source_manifest(self.root,self.profile) == manifest,
                         'SCIENCE_GENUINE_PREEXEC_SOURCE_AUTHORITY')
            module = next(r for r in self.source_table if r['name'] == 'scientific_registration_worker.py')
            journal = self.output/(config['stage']+'-'+str(config['ordinal'])+'-PROCESS')
            retain(Path(str(journal)+'-INTENT.json'), {'operation':self.operation,
                'job_nonce':config['job_nonce'],'config':config_bound,'source':module,
                'command':[self.env_frame['interpreter'],'-B',module['path'],'--config',config_bound['path'],
                           '--expected-config-sha256',config_bound['sha256']],
                'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'started_monotonic':time.monotonic(),
                'scope':'READONLY_ONE_ORIGINAL_SCIENTIFIC_CALL','certifies':False})
            pipes = [];child=None;prior_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGALRM})
            try:
                pipes.append(os.pipe());pipes.append(os.pipe())
                child = subprocess.Popen([self.env_frame['interpreter'], '-B', module['path'],
                    '--config', config_bound['path'], '--expected-config-sha256', config_bound['sha256']],
                    stdout=pipes[0][1], stderr=pipes[1][1], env=self.env, close_fds=True,
                    start_new_session=False)
                state = {'child': child, 'config': config, 'binding': config_bound, 'out': bytearray(),
                         'err': bytearray(), 'open': set(), 'owned':{fd for pair in pipes for fd in pair},
                         'start': time.monotonic(),'journal':journal,'source':module,
                         'operation':self.operation,'capture_count':0,'eof':set(),
                         'truncated':{'out':False,'err':False}}
                active[child.pid] = state
            except BaseException:
                # A successful spawn belongs to this caller even if constructing
                # its state fails before the active table can own it.
                try:
                    if child is not None and child.pid not in active:
                        if child.poll() is None:child.terminate()
                        try:child.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            child.kill();child.wait(timeout=2)
                finally:
                    for pair in pipes:
                        for fd in pair:os.close(fd)
                raise
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,prior_mask)
            retain(Path(str(journal)+'-STARTED.json'), {'operation':self.operation,'job_nonce':config['job_nonce'],
                'config':config_bound,'actual_pid':child.pid,'actual_process_group':os.getpgid(child.pid),
                'source':module,'started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'started_monotonic':state['start'],'source_finally_claimed':False,'certifies':False})
            for kind, pair in zip(('out', 'err'), pipes):
                os.close(pair[1]);state['owned'].remove(pair[1]); os.set_blocking(pair[0], False)
                s=os.fstat(pair[0]); identity=(s.st_dev,s.st_ino,s.st_mode)
                state['open'].add(pair[0]); selector.register(pair[0], selectors.EVENT_READ, (state, kind, identity))
        try:
            while todo or active:
                runtime.need(time.monotonic() < deadline, 'LIVE_SCIENCE_PARENT_BATCH_TIMEOUT')
                while todo and len(active) < 7: launch(todo.pop(0))
                for key, _ in selector.select(min(0.2, max(0, deadline-time.monotonic()))):
                    state, kind, identity = key.data
                    s=os.fstat(key.fd)
                    runtime.need((s.st_dev,s.st_ino,s.st_mode)==identity,'SCIENCE_OWNED_PIPE_IDENTITY')
                    chunk = os.read(key.fd, 16384)
                    if not chunk:
                        state['eof'].add(kind)
                        selector.unregister(key.fd); state['open'].remove(key.fd); os.close(key.fd);state['owned'].remove(key.fd)
                    else:
                        state[kind].extend(chunk)
                        runtime.need(len(state[kind]) <= MAX_FRAME+4, 'BOUNDED_SCIENCE_PIPE_FRAME')
                for pid, state in list(active.items()):
                    if state['child'].poll() is None or state['open']: continue
                    code = state['child'].wait()
                    retention_error = None
                    try:
                        terminal = retain(Path(str(state['journal'])+'-TERMINAL.json'), {'operation':self.operation,
                            'job_nonce':state['config']['job_nonce'],'config':state['binding'],
                            'actual_pid':pid,'actual_child_exit_code':code,
                            'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                            'completed_monotonic':time.monotonic(),'source_finally_claimed':False,'certifies':False})
                        retain_process_output(state, code, 'NORMAL_WAIT_BEFORE_RESULT_GATE', terminal=terminal, waited=True)
                    except BaseException as exc:
                        retention_error = exc
                    try:
                        runtime.need(code == 0 and not state['err'], 'ACTUAL_NORMAL_SCIENTIFIC_WORKER_EXIT')
                    except BaseException as exc:
                        if retention_error is not None and hasattr(exc, 'add_note'):
                            exc.add_note('Worker output retention unavailable: ' + type(retention_error).__name__)
                        raise
                    if retention_error is not None: raise retention_error
                    self._accept(state, code); del active[pid]
        finally:
            primary_error=sys.exc_info()[1];cleanup_errors=[]
            def failed(phase,child,exc):
                cleanup_errors.append({'phase':phase,'actual_pid':child.pid if child is not None else None,
                                       'error_type':type(exc).__name__})
            try:
                # Broadcast first, then finish every child's wait and descriptor
                # cleanup even when a journal or another child's cleanup fails.
                for state in active.values():
                    child=state['child']
                    try:
                        if child.poll() is None:child.terminate()
                    except ProcessLookupError:pass
                    except BaseException as exc:failed('terminate',child,exc)
                for state in active.values():
                    child=state['child'];waited=False
                    try:
                        child.wait(timeout=2);waited=True
                    except subprocess.TimeoutExpired:pass
                    except BaseException as exc:failed('wait',child,exc)
                    if not waited:
                        try:child.kill()
                        except ProcessLookupError:pass
                        except BaseException as exc:failed('kill',child,exc)
                        try:child.wait(timeout=2);waited=True
                        except BaseException as exc:failed('kill_wait',child,exc)
                    try: drain_cleanup_output(state, selector)
                    except BaseException as exc: failed('drain_output', child, exc)
                    try: retain_process_output(state, child.returncode, 'ABORT_CLEANUP_AFTER_ACTUAL_WAIT', waited=waited)
                    except BaseException as exc: failed('retain_output', child, exc)
                    for fd in list(state['owned']):
                        try:
                            if fd in selector.get_map():selector.unregister(fd)
                        except BaseException as exc:failed('unregister',child,exc)
                        try:os.close(fd);state['owned'].remove(fd)
                        except BaseException as exc:failed('close_owned_fd',child,exc)
                    try:
                        retain(Path(str(state['journal'])+'-CLEANUP.json'), {'operation':self.operation,
                            'job_nonce':state['config']['job_nonce'],'actual_pid':child.pid,
                            'actual_child_exit_code':child.returncode,'wait_completed':waited,
                            'source_finally_claimed':False,'certifies':False})
                    except BaseException as exc:failed('cleanup_journal',child,exc)
            finally:
                try:selector.close()
                except BaseException as exc:failed('selector_close',None,exc)
            if cleanup_errors:
                try:
                    retain(self.output/'BATCH_CLEANUP_HOLD.json', {'standard':'VRS-V012-BATCH-CLEANUP-HOLD-1',
                        'primary_error_type':None if primary_error is None else type(primary_error).__name__,
                        'cleanup_errors':cleanup_errors,'owned_child_count':len(active),
                        'source_finally_claimed':False,'certifies':False})
                except BaseException as exc: failed('cleanup_hold_retention', None, exc)
                if primary_error is not None:
                    if hasattr(primary_error, 'add_note'):
                        primary_error.add_note('Worker cleanup DATA HOLD: '+raw(cleanup_errors).decode())
                else:
                    raise runtime.PackagingHold('LIVE_SCIENCE_CLEANUP_HOLD:'+raw(cleanup_errors).decode())

    def _accept(self, state, code):
        payload = bytes(state['out'])
        runtime.need(len(payload) >= 4 and len(payload)-4 == struct.unpack('!I', payload[:4])[0], 'SCIENCE_PIPE_EXACT_FRAME')
        frame = json.loads(payload[4:]); config = state['config']
        runtime.need(set(frame) == {'result', 'pid', 'job_nonce'} and frame['pid'] == state['child'].pid
                     and frame['job_nonce'] == config['job_nonce'], 'ACTUAL_WORKER_RESULT_FRAME_IDENTITY')
        result = runtime.object_at(self.root, frame['result'])[2]
        runtime.need(set(result) == RESULT_FIELDS, 'CLOSED_ACTUAL_SCIENCE_RESULT')
        for key in ('operation', 'job_nonce', 'stage', 'ordinal', 'binding', 'profile',
                    'source_rows', 'environment', 'ledger', 'ledger_sha256', 'evaluation_kwargs','evaluation_state'):
            runtime.need(result.get(key) == config[key], 'EXACT_LIVE_WORKER_RESULT:'+key)
        runtime.need(result.get('standard') == RESULT_STANDARD and result.get('source_finally_completed') is True
                     and result.get('outcome') in {'SCIENCE_RESULT', 'SCIENTIFIC_HOLD'}
                     and result.get('network_requests') == result.get('ssot_writes') == result.get('zenodo_writes') == 0
                     and result.get('certifies') is False,
                     'CLOSED_LIVE_WORKER_RESULT_AND_EXIT')
        runtime.need((result['outcome'] == 'SCIENCE_RESULT' and isinstance(result['original_result'],dict)
                      and result['original_hold'] is None)
                     or (result['outcome'] == 'SCIENTIFIC_HOLD' and result['original_result'] is None
                         and isinstance(result['original_hold'],dict)), 'TYPED_ORIGINAL_SCIENCE_OUTCOME')
        runtime.need(result.get('config') == state['binding'], 'WORKER_ACTUAL_CONFIG')
        runtime.need(result['source_manifest']==config['source_manifest']
                     and result['source_entry']==result['source_exit'],
                     'GENUINE_WORKER_SOURCE_ENTRY_AND_EXIT')
        actual_source_manifest=runtime.object_at(self.root,config['source_manifest'])[2]
        source_proof_valid=importlib.import_module('owner_content_worker').source_proof_valid
        source_proof_valid(result['source_entry'],actual_source_manifest)
        source_proof_valid(result['source_exit'],actual_source_manifest)
        runtime.need(config['started_monotonic'] <= result['started_monotonic'] <= result['completed_monotonic'] <= time.monotonic(),
                     'ACTUAL_WORKER_MONOTONIC_CHRONOLOGY')
        runtime.need(dt.datetime.fromisoformat(config['started_utc']) <= dt.datetime.fromisoformat(result['started_utc'])
                     <= dt.datetime.fromisoformat(result['completed_utc']) <= dt.datetime.now(dt.timezone.utc),
                     'ACTUAL_WORKER_UTC_CHRONOLOGY')
        manifest = runtime.object_at(self.root, result['final_input_manifest'])[2]
        runtime.need(manifest['status'] == 'COMPLETE_REHASHED_OPERATION_INPUT_DATA'
                     and manifest['authorized_canonical_cas'] == [] and isinstance(manifest['inventory'], dict),
                     'ACTUAL_COMPLETE_WORKER_INPUT_EXIT')
        for row in manifest['inputs']:
            key = row['path']
            runtime.need(key not in self.union or self.union[key] == row, 'WORKER_UNION_INPUT_RACE')
            self.union[key] = deepcopy(row)
        key = self._key(config['stage'], config['binding'])
        runtime.need(key not in self.jobs, 'NO_DUPLICATE_JOB_SLOT')
        self.jobs[key] = {'binding': deepcopy(frame['result']), 'config': deepcopy(config),
                          'manifest': deepcopy(result['final_input_manifest']), 'pid': frame['pid'], 'exit_code': code}

    def _fresh_union(self):
        catalog = importlib.import_module('packaging_catalog'); data = catalog.scientific_data(self.root)
        runtime.need(not data.cas_events and data.pending_cas is None, 'HEALTH_LIVE_RESULTS_INVALID_AFTER_CAS')
        if self.context.deadline_guard is not None: self.context.deadline_guard()
        runtime.need(source_rows(self.root, self.profile) == self.source_table, 'ONE_USE_SOURCE_CLOSURE_RACE')
        runtime.need(environment_frame(environment()) == self.env_frame, 'ONE_USE_ENVIRONMENT_RACE')
        runtime.need(evaluation_state()==self.evaluation_state,'ONE_USE_ORIGINAL_FUNCTION_GLOBAL_RACE')
        derived = {}; inventories = []
        for slot in self.jobs.values():
            manifest = runtime.object_at(self.root, slot['manifest'])[2]
            runtime.need(manifest['status'] == 'COMPLETE_REHASHED_OPERATION_INPUT_DATA'
                         and manifest['authorized_canonical_cas'] == [], 'ACTUAL_WORKER_INPUT_MANIFEST_RACE')
            if manifest['inventory'] not in inventories: inventories.append(manifest['inventory'])
            for row in manifest['inputs']:
                runtime.need(row['path'] not in derived or derived[row['path']] == row, 'ACTUAL_WORKER_UNION_CONFLICT')
                derived[row['path']] = row
        runtime.need(derived == self.union, 'NO_CALLER_WORKER_UNION_SUBSTITUTION')
        for path, expected in derived.items():
            data.record(path)
            runtime.need(runtime.same_observed_identity(data.inputs[path],expected), 'FULL_WORKER_UNION_CURRENT_BYTES_IDENTITY:'+path)
        # Each worker retained all8 actual inventories; rederive with the exact
        # original inventory reader, without invoking another scientific scan.
        current_inventory = data.inventory_reader()
        runtime.need(all(current_inventory == item for item in inventories), 'FULL_WORKER_INPUT_INVENTORY_RACE')
        data.alias_guard(complete=True); data.platform_guard()
        if self.context.deadline_guard is not None: self.context.deadline_guard()

    def require(self, bound, ledger=None, **kwargs):
        current = _STAGE.get()
        runtime.need(current is not None and current[0] is self and not self.closed, 'EXACT_LIVE_SCIENCE_STAGE_REQUIRED')
        key = self._key(current[1], bound)
        runtime.need(key in self.jobs and key not in self.used, 'ONE_USE_EXACT_STAGE_BINDING')
        runtime.need(set(kwargs)=={'views'}and kwargs['views']is None, 'EXACT_LOGICAL_SAVED_SCIENCE_KWARGS')
        slot = self.jobs[key]; config = slot['config']
        expected = None if config['ledger'] is None else runtime.object_at(self.root, config['ledger'])[2]
        runtime.need(raw(argument_projection(ledger)) == raw(argument_projection(expected)), 'EXACT_NONPUBLICATION_WHOLE_ARGUMENT')
        self._fresh_union()
        result = runtime.object_at(self.root, slot['binding'])[2]
        runtime.need(dt.datetime.fromisoformat(result['completed_utc']) <= dt.datetime.now(dt.timezone.utc)
                     and result['completed_monotonic'] <= time.monotonic(), 'LIVE_SCIENCE_CONSUMPTION_CLOCK')
        self.used.add(key)
        stem=current[1]+'-'+str(config.get('ordinal',0))+'-CONSUMPTION'
        logical_ledger=None if ledger is None else retain(self.output/(stem+'-WHOLE_MASTER_ARGUMENT.json'),ledger)
        differences=[]
        if ledger is not None:
            for field in sorted(PUB_FIELDS):
                if (field in ledger)!=(field in expected) or raw(ledger.get(field))!=raw(expected.get(field)):
                    differences.append({'field':field,'worker_present':field in expected,'master_present':field in ledger,
                        'worker_value_sha256':None if field not in expected else runtime.sha(raw(expected[field])),
                        'master_value_sha256':None if field not in ledger else runtime.sha(raw(ledger[field]))})
        consumed=retain(self.output/(stem+'.json'), {'standard':'VRS-V012-ACTUAL-ONE-USE-SCIENTIFIC-DATA-CONSUMPTION-1',
            'status':'ACTUAL_LIVE_ORIGINAL_FUNCTION_DATA_CONSUMED_NOT_NEW_AUTHORITY','operation':self.operation,
            'stage':current[1],'job_nonce':config.get('job_nonce'),'registration':deepcopy(bound),
            'worker_config':result.get('config'),'actual_worker_result':deepcopy(slot['binding']),
            'worker_whole_argument':deepcopy(config['ledger']),'master_whole_argument':logical_ledger,
            'evaluation_kwargs':{'views':None,'prior_chain_receipts':None},'allowed_publication_differences':differences,
            'all_other_whole_argument_fields_equal':True,'outcome':result['outcome'],
            'actual_worker_scientific_hold':result['original_hold'],
            'hold_namespace_contract':'WORKER_ACTUAL_RAISING_NAMESPACE_TO_FIXED_PUBLIC_SOURCE_ROW_SAME_DEFINITION_CLASS_MESSAGE',
            'consumed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'consumed_at_monotonic':time.monotonic(),
            'certifies':False})
        self.consumptions.append(consumed)
        if result['outcome'] == 'SCIENTIFIC_HOLD':
            raise resolved_hold(self.root,result['original_hold'])
        runtime.need(result['original_hold'] is None and isinstance(result['original_result'], dict), 'EXACT_RETURNED_ORIGINAL_DATA')
        return deepcopy(result['original_result'])

    def close(self, *, complete=False):
        try:
            if complete: runtime.need(len(self.used) == len(self.consumptions) == 35, 'COMPLETE_THIRTY_FIVE_LOGICAL_CONSUMPTIONS')
        finally:
            self.closed = True
            self.context.scientific_consumer = None
            self.context.scientific_batch = None

    def summary(self):
        return {'operation':self.operation,'calls_started':len(self.jobs),'logical_consumptions':len(self.used),
                'one_use_only':True,'closed':self.closed,'admission_cached':False,'certifies':False,
                'consumptions':deepcopy(self.consumptions),
                'jobs':[{'stage':slot['config']['stage'],'binding':slot['config']['binding'],
                         'job_nonce':slot['config']['job_nonce'],'result':slot['binding'],
                         'input_manifest':slot['manifest'],'actual_pid':slot['pid'],
                         'actual_child_exit_code':slot['exit_code']}for slot in self.jobs.values()]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--expected-config-sha256', required=True)
    args = parser.parse_args(argv)
    return worker(args.config, args.expected_config_sha256)


if __name__ == '__main__':
    raise SystemExit(main())
