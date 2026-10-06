"""INV-8 byte comparison only. Source bytes are never certificate evidence."""
import hashlib
import os
from pathlib import Path

GENERATION_ROOT = Path('/Users/justinhart/Desktop/science ')
RUNS_REL = Path('07_nightly_engine/compound research papers')


def inventory(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError('missing or symlink run directory: ' + str(directory))
    files = {}
    def fail(error):
        raise error
    for base, dirs, names in os.walk(directory, followlinks=False, onerror=fail):
        for name in dirs + names:
            if (Path(base)/name).is_symlink():
                raise ValueError('symlink in run inventory: ' + str(Path(base)/name))
        for name in names:
            path = Path(base)/name
            before = path.stat()
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(1048576), b''):
                    digest.update(block)
            after = path.stat()
            if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError('run file changed during parity read: ' + str(path))
            files[str(path.relative_to(directory))] = digest.hexdigest()
    if not files:
        raise ValueError('empty run inventory: ' + str(directory))
    return files


def check_parity(source, mirror):
    source, mirror = Path(source), Path(mirror)
    result = {'status': 'MIRROR_DRIFT', 'source': str(source), 'mirror': str(mirror),
              'purpose': 'PARITY_ONLY_NOT_CERTIFICATION', 'differences': [], 'errors': [], 'file_count': 0}
    try:
        if source.resolve() == mirror.resolve():
            raise ValueError('source and mirror must be distinct')
        a, b = inventory(source), inventory(mirror)
        result['source_hashes'], result['mirror_hashes'] = a, b
        result['file_count'] = len(a)
        result['differences'] = [{'path': name, 'source_sha256': a.get(name), 'mirror_sha256': b.get(name)}
                                 for name in sorted(set(a) | set(b)) if a.get(name) != b.get(name)]
        # User-approved narrow exception: an extra regular Finder .DS_Store
        # with its format signature may differ in inventory, never proof bytes.
        ignored=[];kept=[]
        for difference in result['differences']:
            name=difference['path']
            extra=(source/name) if name in a and name not in b else (mirror/name) if name in b and name not in a else None
            if extra is not None and Path(name).name=='.DS_Store':
                metadata=extra.read_bytes()
                expected=a.get(name) or b.get(name)
                if hashlib.sha256(metadata).hexdigest()!=expected:
                    raise ValueError('metadata changed during parity classification: '+str(extra))
                if metadata[:8]==b'\x00\x00\x00\x01Bud1':
                    ignored.append({**difference,'reason':'EXTRA_FINDER_METADATA_ONLY'})
                    continue
            kept.append(difference)
        result['ignored_metadata_differences']=ignored
        result['differences']=kept
        if not result['differences']:
            result['status'] = 'MATCH'
    except Exception as exc:
        result['errors'].append(type(exc).__name__ + ': ' + str(exc))
    return result


def run_parity(root, run_path, generation_root=GENERATION_ROOT):
    mirror = Path(root)/run_path
    relative = mirror.relative_to(Path(root)/'science-engine')
    return check_parity(Path(generation_root)/relative, mirror)
