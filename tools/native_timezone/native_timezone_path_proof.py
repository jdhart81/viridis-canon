"""Read-only independent native-path observation; prints DATA, never admission."""
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


def identity(path):
    value = os.lstat(path)
    return {'device': value.st_dev, 'inode': value.st_ino, 'mode': value.st_mode,
            'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns, 'ctime_ns': value.st_ctime_ns}


def observe(logical, physical, links, lookup):
    """Arguments exist only for isolated fixtures; CLI fixes all native paths."""
    if logical.resolve(strict=True) != physical:
        raise RuntimeError('HOLD_NATIVE_RESOLUTION')
    if next((Path(p) / 'America/New_York' for p in lookup
             if (Path(p) / 'America/New_York').is_file()), None) != logical:
        raise RuntimeError('HOLD_NATIVE_LOOKUP')
    chain = []
    for path in links:
        before = identity(path)
        if not stat.S_ISLNK(before['mode']):
            raise RuntimeError('HOLD_EXPECTED_LINK')
        target = os.readlink(path)
        resolved = str(path.resolve(strict=True))
        if identity(path) != before or os.readlink(path) != target:
            raise RuntimeError('HOLD_LINK_RACE')
        chain.append({'path': str(path), 'identity': {**before, 'readlink': target},
                      'resolved_target': resolved})
    parent_rows = []
    for path in reversed(physical.parents):
        row = identity(path)
        if not stat.S_ISDIR(row['mode']):
            raise RuntimeError('HOLD_NATIVE_REGULAR_PARENT')
        parent_rows.append({'path': str(path), 'identity': row})
    first = identity(physical)
    if not stat.S_ISREG(first['mode']) or first['bytes'] > LIMIT:
        raise RuntimeError('HOLD_NATIVE_REGULAR_LEAF')
    fd = os.open(physical, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT or identity(physical) != first or not raw.startswith(b'TZif'):
        raise RuntimeError('HOLD_NATIVE_LEAF_RACE')
    for row in chain:
        path = Path(row['path'])
        if {**identity(path), 'readlink': os.readlink(path)} != row['identity']:
            raise RuntimeError('HOLD_NATIVE_POSTREAD_LINK')
    return {'logical_selected_path': str(logical), 'physical_path': str(physical),
            'root_executable': sys.executable, 'stdlib_TZPATH': list(lookup),
            'frame': {'resolution_symlink_chain': chain,
                      'physical_regular_parent_chain': parent_rows,
                      'physical_file_identity': first, 'bytes': len(raw),
                      'sha256': hashlib.sha256(raw).hexdigest(), 'TZif_header_hex': raw[:5].hex()}}


def main():
    lookup = tuple(p for p in (sysconfig.get_config_var('TZPATH') or '').split(os.pathsep) if p)
    before = observe(LOGICAL, PHYSICAL, LINKS, lookup)
    after = observe(LOGICAL, PHYSICAL, LINKS, lookup)
    if before != after:
        raise RuntimeError('HOLD_NATIVE_OBSERVATION_CHANGED')
    print(json.dumps({'standard': 'VRS-INDEPENDENT-NATIVE-TIMEZONE-PATH-OBSERVATION-1',
                      'status': 'READ_ONLY_NATIVE_TIMEZONE_PATH_OBSERVED',
                      'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      **after, 'certifies': False, 'Core_or_OS_writes': 0, 'network_requests': 0},
                     sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
