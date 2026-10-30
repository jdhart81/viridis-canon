"""Root-executed native DATA observer; prints the unchanged closed receipt schema.

No output path, Core/runtime imports, network, OS-link changes or admission.
Root separately retains stdout in its authorized immutable Core receipt path.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import sysconfig

LOGICAL = Path('/usr/share/zoneinfo/America/New_York')
PHYSICAL = Path('/private/var/db/timezone/tz/2026e.1.0/zoneinfo/America/New_York')
LINKS = (Path('/usr/share/zoneinfo'), Path('/var'), Path('/private/var/db/timezone/zoneinfo'))
LIMIT = 65536


def require(value, message):
    if not value:
        raise RuntimeError('HOLD_' + message)


def fingerprint(path):
    value = path.lstat()
    return dict(device=value.st_dev, inode=value.st_ino, mode=value.st_mode,
                bytes=value.st_size, mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns)


def capture_frame(logical, physical, links):
    """Independent implementation; fixtures may supply temporary exact paths."""
    require(logical.resolve(strict=True) == physical, 'CURRENT_NATIVE_RESOLUTION')
    leaf = fingerprint(physical)
    require(stat.S_ISREG(leaf['mode']) and leaf['bytes'] <= LIMIT, 'REGULAR_NATIVE_DATA')
    parents = []
    for path in reversed(physical.parents):
        row = fingerprint(path)
        require(stat.S_ISDIR(row['mode']), 'REGULAR_NATIVE_PARENT')
        parents.append({'path': str(path), 'identity': row})
    chain = []
    for path in links:
        row = fingerprint(path)
        require(stat.S_ISLNK(row['mode']), 'EXACT_THREE_LINKS')
        row['readlink'] = os.readlink(path)
        chain.append({'path': str(path), 'identity': row,
                      'resolved_target': str(path.resolve(strict=True))})
    fd = os.open(physical, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read(LIMIT + 1)
    require(len(raw) <= LIMIT and raw.startswith(b'TZif') and fingerprint(physical) == leaf,
            'NATIVE_LEAF_READ_RACE')
    for row in chain:
        path = Path(row['path'])
        require({**fingerprint(path), 'readlink': os.readlink(path)} == row['identity']
                and str(path.resolve(strict=True)) == row['resolved_target'], 'NATIVE_LINK_READ_RACE')
    for row in parents:
        current = fingerprint(Path(row['path']))
        require({k: current[k] for k in ('device', 'inode', 'mode')}
                == {k: row['identity'][k] for k in ('device', 'inode', 'mode')}, 'NATIVE_PARENT_READ_RACE')
    require(logical.resolve(strict=True) == physical, 'NATIVE_FINAL_RESOLUTION')
    return {'TZif_header_hex': raw[:5].hex(), 'bytes': len(raw),
            'physical_file_identity': leaf, 'physical_regular_parent_chain': parents,
            'resolution_symlink_chain': chain, 'sha256': hashlib.sha256(raw).hexdigest()}


def bounded_file(path, expected):
    require(path.is_absolute() and not any(p.is_symlink() for p in (path, *path.parents)),
            'REGULAR_PROOF_FILE')
    before = fingerprint(path)
    require(stat.S_ISREG(before['mode']) and before['bytes'] <= 1048576, 'BOUNDED_PROOF_FILE')
    with path.open('rb') as stream:
        raw = stream.read(1048577)
    require(len(raw) <= 1048576 and fingerprint(path) == before
            and hashlib.sha256(raw).hexdigest() == expected, 'PROOF_HASH_OR_RACE')
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--independent-proof', type=Path, required=True)
    parser.add_argument('--expected-independent-proof-sha256', required=True)
    parser.add_argument('--failed-preflight', type=Path, required=True)
    parser.add_argument('--expected-failed-preflight-sha256', required=True)
    parser.add_argument('--root-exec-tool-exit-code', type=int)
    args = parser.parse_args()
    proof_raw = bounded_file(args.independent_proof.absolute(), args.expected_independent_proof_sha256)
    proof = json.loads(proof_raw)
    failed = bounded_file(args.failed_preflight.absolute(), args.expected_failed_preflight_sha256)
    require(b'EXACT_NATIVE_TIMEZONE_LINK_IDENTITY' in failed, 'ACTUAL_FAILED_PREFLIGHT')
    lookup = tuple(p for p in (sysconfig.get_config_var('TZPATH') or '').split(os.pathsep) if p)
    require(next((Path(p) / 'America/New_York' for p in lookup
                  if (Path(p) / 'America/New_York').is_file()), None) == LOGICAL, 'NATIVE_DEFAULT_LOOKUP')
    before = capture_frame(LOGICAL, PHYSICAL, LINKS)
    after = capture_frame(LOGICAL, PHYSICAL, LINKS)
    require(before == after, 'CURRENT_FRAME_STABLE')
    require(proof.get('standard') == 'VRS-INDEPENDENT-NATIVE-TIMEZONE-PATH-OBSERVATION-1'
            and proof.get('status') == 'READ_ONLY_NATIVE_TIMEZONE_PATH_OBSERVED'
            and proof.get('logical_selected_path') == str(LOGICAL)
            and proof.get('physical_path') == str(PHYSICAL)
            and proof.get('root_executable') == sys.executable
            and proof.get('stdlib_TZPATH') == list(lookup)
            and proof.get('certifies') is False and proof.get('network_requests') == 0,
            'GENUINE_INDEPENDENT_PATH_PROOF')
    independent = proof['frame']
    for field in ('physical_file_identity', 'resolution_symlink_chain', 'sha256', 'bytes', 'TZif_header_hex'):
        require(independent[field] == after[field], 'INDEPENDENT_CURRENT_FRAME_MATCH')
    require([(r['path'], {k: r['identity'][k] for k in ('device', 'inode', 'mode')})
             for r in independent['physical_regular_parent_chain']]
            == [(r['path'], {k: r['identity'][k] for k in ('device', 'inode', 'mode')})
                for r in after['physical_regular_parent_chain']], 'INDEPENDENT_PARENT_MATCH')
    value = {'actual_failed_child_path_limitation': 'Retained actual read-only installer failure; no scientific execution or traced historical ZoneInfo open claimed.',
             'actual_failed_execution': {'path': str(args.failed_preflight.absolute()),
                                        'sha256': args.expected_failed_preflight_sha256,
                                        'actual_child_exit_code': 1,
                                        'actual_root_exec_tool_exit_code': args.root_exec_tool_exit_code},
             'after': after, 'before': before, 'certifies': False,
             'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'heavy_scientific_executions': 0,
             'independent_platform_path_evidence': {'path': str(args.independent_proof.absolute()),
                                                   'sha256': args.expected_independent_proof_sha256},
             'logical_selected_path': str(LOGICAL), 'network_requests': 0,
             'physical_path': str(PHYSICAL), 'root_executable': sys.executable,
             'scope': 'Current2026e native NewYork DATA leaf and exact three-link identity; no source, certificate, ledger, science predicate, clock semantics or timezone mutation.',
             'source_certificate_alias_ledger_timezone_writes': 0,
             'standard': 'VRS-ROOT-EXACT-PLATFORM-TIMEZONE-DATA-READBACK-1',
             'status': 'EXACT_CURRENT_NATIVE_DATA_PATH_VERIFIED_NOT_RUNTIME_ADMISSION',
             'stdlib_TZPATH': list(lookup), 'zone_key': 'America/New_York'}
    print(json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
