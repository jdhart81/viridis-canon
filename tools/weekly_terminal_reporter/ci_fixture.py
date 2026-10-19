"""CI-only finite reporter fixture; never installs or invokes a production CLI."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / 'tools/weekly_terminal_reporter/CI_CLOSURE.json'
CLOSURE_SHA256 = '9d85b2380019b16d12386abf81926c226d7323c8af1c6cda55de1888c81fed68'

class FixtureHold(ValueError):
    pass

def need(ok, why):
    if not ok:
        raise FixtureHold(why)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def physical(path):
    need(path.is_absolute(), 'ABSOLUTE_PATH')
    for parent in reversed((path, *path.parents)):
        need(stat.S_ISDIR(parent.lstat().st_mode), 'PHYSICAL_DIRECTORY_CHAIN')

def relative(value):
    need(type(value) is str and value and not PurePosixPath(value).is_absolute()
         and value == PurePosixPath(value).as_posix() and '\\' not in value
         and all(p not in ('', '.', '..') for p in value.split('/')), 'CLOSED_RELATIVE_PATH')
    return Path(value)

def regular(path, cap=4_000_000):
    physical(path.parent)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'REGULAR_BOUNDED_INPUT')
        parts = []
        total = 0
        while chunk := os.read(fd, 65536):
            total += len(chunk)
            need(total <= cap, 'READ_CAP')
            parts.append(chunk)
        after = os.fstat(fd)
        named = path.lstat()
        stable = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_mode)
        need(stable(before) == stable(after) == stable(named), 'STABLE_INPUT_I9_NO_CTIME')
        return b''.join(parts)
    finally:
        os.close(fd)

def bound(path, digest):
    raw = regular(path)
    need(sha(raw) == digest, 'SOURCE_HASH')
    return raw

def unique(pairs):
    out = {}
    for key, value in pairs:
        need(key not in out, 'DUPLICATE_KEY')
        out[key] = value
    return out

def closure():
    raw = bound(CLOSURE, CLOSURE_SHA256)
    value = json.loads(raw, object_pairs_hook=unique)
    need(value['standard'] == 'VRS-WEEKLY-TERMINAL-REPORTER-PUBLIC-CI-1'
         and all(value[k] is False for k in ('active', 'installed', 'production_admitted')), 'INACTIVE_FIXTURE_ONLY')
    need(len(value['support']) == 4 and len(value['expected_cases']) == 44
         and len(set(value['expected_cases'])) == 44
         and value['retained_cases'] == 16 and value['new_cases'] == 28, 'EXACT44_PROFILE')
    return value

def _derive(before: bytes, patch: bytes, target: str) -> bytes:
    """Apply one uniquely named unified diff section with exact context only."""
    source = before.decode("utf-8").splitlines(keepends=True)
    lines = patch.decode("utf-8").splitlines(keepends=True)
    sections = []
    for index, line in enumerate(lines):
        if line == "--- a/" + target + "\n":
            if index + 1 >= len(lines) or lines[index + 1] != "+++ b/" + target + "\n":
                raise FixtureHold("derived source has mismatched patch headers")
            end = next((j for j in range(index + 2, len(lines))
                        if lines[j].startswith("--- a/")), len(lines))
            sections.append(lines[index + 2:end])
    if len(sections) != 1:
        raise FixtureHold("derived source requires one unique patch section")
    output, cursor, hunks = [], 0, 0
    section, index = sections[0], 0
    while index < len(section):
        header = section[index]
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n", header)
        if match is None:
            raise FixtureHold("unsupported unified patch structure")
        old_start, old_count = int(match[1]), int(match[2] or 1)
        new_start, new_count = int(match[3]), int(match[4] or 1)
        position = old_start if old_count == 0 else old_start - 1
        if position < cursor or position > len(source):
            raise FixtureHold("patch hunk overlaps or escapes source")
        output.extend(source[cursor:position])
        if len(output) != (new_start if new_count == 0 else new_start - 1):
            raise FixtureHold("patch new-line identity differs")
        cursor, consumed, produced = position, 0, 0
        index += 1
        while index < len(section) and not section[index].startswith("@@ "):
            line = section[index]
            if line == "\n":
                # The pinned allocation diff spells empty context as bare LF.
                # Consume and reproduce that exact source line like any context.
                marker, content = " ", "\n"
            elif line and line[0] in {" ", "+", "-"}:
                marker, content = line[0], line[1:]
            else:
                raise FixtureHold("unsupported patch line")
            if marker in {" ", "-"}:
                if cursor >= len(source) or source[cursor] != content:
                    raise FixtureHold("patch context differs")
                cursor += 1
                consumed += 1
            if marker in {" ", "+"}:
                output.append(content)
                produced += 1
            index += 1
        if (consumed, produced) != (old_count, new_count):
            raise FixtureHold("patch hunk counts differ")
        hunks += 1
    if not hunks:
        raise FixtureHold("empty derived-source patch")
    output.extend(source[cursor:])
    return "".join(output).encode("utf-8")

def fixed_baseline(item):
    # Only the one closed public CE8 baseline captured by the workflow; no process/import.
    need(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('CI') == 'true', 'GITHUB_CI_ONLY')
    temp = Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
    physical(temp)
    need(item['baseline_filename'] == 'weekly-terminal-baseline.py.data'
         and item['baseline_origin_filename'] == 'weekly-terminal-baseline-origin.json', 'FIXED_BASELINE_FILENAMES')
    path = temp / item['baseline_filename']
    before = path.lstat()
    raw = bound(path, item['base_sha256'])
    after = path.lstat()
    identity = lambda s: {'dev': s.st_dev, 'ino': s.st_ino, 'mode': s.st_mode,
                          'bytes': s.st_size, 'mtime_ns': s.st_mtime_ns}
    need(identity(before) == identity(after), 'BASELINE_STABLE_I9_NO_CTIME')
    origin = item['baseline_origin']
    need(len(raw) == origin['bytes'] == 21834 and sha(raw) == origin['sha256'] == item['base_sha256']
         and hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == origin['blob_oid'],
         'EXACT_FROZEN_PUBLIC_BASELINE_BLOB_SIZE_SHA')
    origin_raw = regular(temp / item['baseline_origin_filename'])
    need(json.loads(origin_raw, object_pairs_hook=unique) == origin, 'WORKFLOW_FROZEN_COMMIT_PATH_BLOB_ORIGIN')
    return raw, {'frozen_public_origin': origin, 'baseline_identity': identity(after),
                 'baseline_filename': item['baseline_filename'], 'origin_filename': item['baseline_origin_filename'],
                 'origin_file_sha256': sha(origin_raw)}

def payloads(value):
    result = {}
    origins = []
    def add(name, raw, origin):
        name = relative(name).as_posix()
        need(name not in result, 'UNIQUE_FIXTURE_DESTINATION')
        result[name] = raw
        origins.append({'fixture_path': name, 'sha256': sha(raw), 'bytes': len(raw), 'origin': origin})
    item = value['reporter']
    baseline, baseline_origin = fixed_baseline(item)
    patch = bound(ROOT / relative(item['patch_public_path']), item['patch_sha256'])
    lines = patch.decode('utf-8').splitlines(keepends=True)
    need(lines[:2] == [item['before_header'], item['after_header']], 'EXACT_PATCH_HEADERS')
    target = 'nightly_proof_track_terminal_report.py'
    normalized = ('--- a/' + target + '\n+++ b/' + target + '\n' + ''.join(lines[2:])).encode()
    after = _derive(baseline, normalized, target)
    need(sha(after) == item['after_sha256'] and len(after) == item['after_bytes'], 'EXACT_REVIEWED_REPORTER')
    add(item['fixture_path'], after, {'baseline': baseline_origin, 'patch_public_path': item['patch_public_path']})
    item = value['test']
    raw = bound(ROOT / relative(item['public_path']), item['sha256'])
    need(len(raw) == item['bytes'] and sha(raw[:item['retained_prefix_bytes']]) == item['retained_prefix_sha256'], 'ORIGINAL16_PREFIX')
    add(item['fixture_path'], raw, item['public_path'])
    for item in value['support']:
        raw = bound(ROOT / relative(item['public_path']), item['sha256'])
        need(len(raw) == item['bytes'], 'EXACT_SUPPORT_SIZE')
        add(item['fixture_path'], raw, item['public_path'])
    item = value['seam']
    raw = item['content'].encode()
    need(sha(raw) == item['sha256'], 'EXACT_TEST_ONLY_SEAM')
    add(item['fixture_path'], raw, 'source-owned test-only seam; no production root helper')
    need(len(result) == 7 and sum(map(len, result.values())) < 200_000, 'FINITE7_CLOSURE')
    return result, origins

def output_root(value, exists):
    need(os.environ.get('GITHUB_ACTIONS') == 'true' and os.environ.get('CI') == 'true', 'GITHUB_CI_ONLY')
    physical(ROOT)
    need(Path(os.environ['GITHUB_WORKSPACE']).resolve(strict=True) == ROOT, 'ACTUAL_CHECKOUT_ROOT')
    temp = Path(os.environ['RUNNER_TEMP']).resolve(strict=True)
    physical(temp)
    root = Path(value)
    need(root.is_absolute() and root.parent == temp and root.name in ('weekly-terminal-3.12', 'weekly-terminal-3.14'), 'FIXED_RUNNER_SCRATCH')
    if exists:
        physical(root)
    else:
        need(not os.path.lexists(root), 'EXCLUSIVE_ABSENT_FIXTURE')
    return root

def put(path, raw):
    physical(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            need(count > 0, 'SHORT_WRITE')
            view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    need(regular(path) == raw, 'WRITTEN_BYTES_READBACK')

def jsonbytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()

def prepare(value, output):
    # Every finite input is validated before the first scratch write. No candidate import.
    data, origins = payloads(value)
    root = output_root(output, False)
    root.mkdir(mode=0o700)
    fixture = root / 'fixture'
    fixture.mkdir(mode=0o700)
    for name, raw in sorted(data.items()):
        target = fixture / relative(name)
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        put(target, raw)
    put(root / 'MATERIALIZATION.json', jsonbytes({'standard': 'VRS-WEEKLY-REPORTER-CI-MATERIALIZATION-1',
        'active': False, 'installed': False, 'production_admitted': False,
        'closure_sha256': CLOSURE_SHA256, 'revision_declaration': os.environ['GITHUB_SHA'],
        'source_head_declaration': os.environ['CI_SOURCE_HEAD'], 'origins': origins,
        'qualification': value['qualification']}))

def verify(value, output):
    data, origins = payloads(value)
    root = output_root(output, True)
    receipt = json.loads(regular(root / 'MATERIALIZATION.json'), object_pairs_hook=unique)
    need(receipt['closure_sha256'] == CLOSURE_SHA256 and receipt['origins'] == origins
         and receipt['revision_declaration'] == os.environ['GITHUB_SHA']
         and receipt['source_head_declaration'] == os.environ['CI_SOURCE_HEAD'], 'SAME_SOURCE_FIXTURE_RECEIPT')
    for name, raw in data.items():
        need(regular(root / 'fixture' / relative(name)) == raw, 'FIXTURE_INPUT_UNCHANGED')
    raw = regular(root / 'junit.xml', 2_000_000)
    need(b'<!DOCTYPE' not in raw and b'<!ENTITY' not in raw, 'NO_XML_EXTERNAL_OR_AMPLIFIED_INPUT')
    doc = ET.fromstring(raw)
    cases = list(doc.iter('testcase'))
    need([case.get('name') for case in cases] == value['expected_cases'], 'EXACT44_ORDERED_TEST_CASES')
    need(all(case.get('classname') == 'test_nightly_proof_track_terminal_report' for case in cases), 'EXACT_TEST_MODULE')
    need(not any(list(case) for case in cases), 'NO_FAILURE_ERROR_SKIP_OR_UNEXPECTED_TEST_PAYLOAD')
    suites = list(doc.iter('testsuite'))
    need(len(suites) == 1 and suites[0].get('tests') == '44'
         and all(suites[0].get(k) == '0' for k in ('errors', 'failures', 'skipped')), 'ALL44_EXECUTED_SUCCESS')
    seconds = [float(case.get('time')) for case in cases]
    need(all(math.isfinite(s) and 0 <= s <= 500 for s in seconds), 'FINITE_RECORDED_CASE_TIMES')
    put(root / 'CI_VALIDATION.json', jsonbytes({'standard': 'VRS-WEEKLY-REPORTER-CI-VALIDATION-1',
        'qualification': 'PUBLIC_SYNTHETIC_REPORTER_LOGIC_AND_REAL_HELPER_NEGATIVES_ONLY',
        'tests': 44, 'retained_tests': 16, 'new_cases': 28, 'skips': 0, 'failures': 0, 'errors': 0,
        'closure_sha256': CLOSURE_SHA256, 'junit_sha256': sha(raw),
        'revision_declaration': os.environ['GITHUB_SHA'], 'source_head_declaration': os.environ['CI_SOURCE_HEAD'],
        'actual_run_job_step_600s_API_authentication': 'ROOT_COLLECTOR_REQUIRED_NO_JUNIT_OR_ENV_SUBSTITUTION',
        'runtime_private_positive_auth_install_refresh_publication_or_science_credit': False}))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'verify'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    value = closure()
    (prepare if args.mode == 'prepare' else verify)(value, args.output)

if __name__ == '__main__':
    main()
