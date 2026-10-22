#!/usr/bin/env python3
"""Build Addendum 1 to plan P1C v1.4: its records, its file table, its timestamp, and its place in the package.

Run once, as the last tool call of the session, exactly as:
    cd /home/claude/p1c/addendum_v1.4 && python3 -B make_addendum_records.py
With --dry-run it writes the records, COMPARTMENT_LABELS.json and ADDENDUM_v1.4.md here, then stops: no stamp, and the
package is not touched.

Invariants. Each is checked, and a failure stops the script with 'ADDENDUM FAIL'. Failures before the copy into the
package leave the package untouched; a failure after it removes the copies and restores the v1.4 SHA256SUMS.txt.
  I1  No file listed in FREEZE.json changes: all entries are hashed before anything is written and again at the end,
      and must equal FREEZE.json, which must be the v1.4 freeze. No outcome, fetch-record or registration file exists.
  I2  Command records from the session transcript SRC:
        addendum_transcript_post_freeze.jsonl  every Bash, Edit and Write call after the v1.4 freeze command FREEZE_CMD;
        addendum_transcript_other_tools.jsonl  every call of any other tool from the transcript's start.
      Both stop before this script's own invocation, which must be the transcript's last tool call and exactly the
      command above; it is the only call left out. FREEZE_CMD must be the last row of
      logs/transcript_tool_calls_p1c_part2.jsonl, and the transcript's copy of it must redact to that row. The
      transcript must hold no agent (sidechain) rows and no tool-call blocks other than 'tool_use'.
      Each row: timestamp, tool, input (as the transcript stores it, as in part 2), cwd, source. Redaction: tokens
      (extract_transcript.py's TOKEN) whose lower-case sha256 is in REDACT (the plan's two, checked against
      extract_transcript.py) or equals ACCT (the author's account name on his computer) become '[redacted]', and the
      row is flagged 'redacted'.
  P   Privacy, over both records and every shipped text file: no token, and no part of a token (4+ characters), may
      hash into REDACT or ACCT, and no e-mail address may appear. Any hit is fatal.
  I3  Compartment labels (COMPARTMENT_LABELS.json): each package label file is a byte copy of its source; each ID
      table equals labB read at the predictor table's (row, col); the B samples (run_test.sample) hold 11,314 and
      2,677 ignitions in 2,065 and 555 compartments, none on label 0. The README's 'Running the code' steps recreate
      every pilot file the code reads at ../p1/ byte for byte (each must match its FREEZE.json entry), and
      predictors_blind.csv.gz decompresses to the frozen table.
  I4  ADDENDUM_v1.4.md is ADDENDUM_v1.4.template.md with every @@...@@ filled and the file table written; nothing else
      differs. AUDIT_5_of_v1.4.md and REVIEW_of_ADDENDUM_v1.4.md equal their copies in p1c/audits/.
  I5  Package: the files listed in the v1.4 SHA256SUMS.txt keep their hashes; exactly the addendum's files are added;
      SHA256SUMS.txt is rewritten over every file, exactly as make_package.py writes it.
  I6  ADDENDUM_v1.4.md is stamped with OpenTimestamps. The proof's file digest, after the header, version byte and
      sha256 op (offset 33), must be the addendum's sha256. The proof is shipped.
No confirmatory outcome is read; the pilot outcome table is only hashed. Nothing is fetched except the OpenTimestamps
submission."""
import ast, gzip, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, time
from collections import Counter

sys.dont_write_bytecode = True
import numpy as np
import pandas as pd

DRY = '--dry-run' in sys.argv[1:]
P1C, P1 = '/home/claude/p1c', '/home/claude/p1'
ADD = os.path.join(P1C, 'addendum_v1.4')
PKG = '/home/claude/p1c_registration_v1.4'
SRC = '/root/.claude/projects/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3.jsonl'
FREEZE_SHA = '4efb62b83fa8f8a5bbb674739f5102dd87bb599a17bf2f0b10f813789019e042'
PREREG = 'PREREGISTRATION_P1C_NEWA_v1.4.md'
PREREG_SHA = '36e6383621e3f2d228c11ef13300e15b991787d827c242b5caf3e65a61c5f57f'
FREEZE_CMD = '2026-10-21T12:15:47.486Z'
SELF_CMD = re.compile(r'(cd /home/claude/p1c/addendum_v1\.4 && )?python3 -B make_addendum_records\.py( --dry-run)?')
EDIT_TOOLS = ('Bash', 'Edit', 'Write')
REDACT = {'576ba7c2e4abb7184ca409154dbbbd5306c1a80747fbce4148ea6271fd21e776', 'b40e514e1865e87cf62386bb318d9ee6fcf5d6d4fd75456dbe62015c62886d5d'}
ACCT = '46711eb1a331c17ea8bfeadc8f2b22195b1c690b0c210d02fe7c0ebeffb0d8c3'
HIDE = REDACT | {ACCT}
TOKEN = re.compile(r'[A-Za-z0-9_]+')
EMAIL = re.compile(r'[\w.+-]+@(?:\[redacted\]|[\w-]+)\.[A-Za-z]{2,}')
OTS_MAGIC = b'\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94'
DISPLAY = {'mcp__remote-devices__device_bash': "shell on the author's computer",
           'mcp__remote-devices__device_list_dir': "folder listing on the author's computer",
           'mcp__remote-devices__device_stage_files': "file copy from the author's computer",
           'mcp__remote-devices__device_commit_files': "file copy to the author's computer"}
ADD_FILES = [  # (file, what it is), in table order; ADDENDUM_v1.4.md and its .ots are added after these
    ('AUDIT_5_of_v1.4.md', 'the fifth audit, verbatim below a header comment'),
    ('REVIEW_of_ADDENDUM_v1.4.md', "the independent review of this addendum's draft, verbatim below a header comment (§6)"),
    ('COMPARTMENT_LABELS.json', 'hashes and counts of the compartment labels (m1)'),
    ('compartments_static.npz', "this region's compartment label arrays (copy of p1c/compartments_static.npz)"),
    ('pilot_compartments_static.npz', "the pilot's compartment label arrays (copy of p1/compartments_static.npz)"),
    ('compartment_ids_blind.csv.gz', 'definition-B compartment of each of the 14,105 ignitions of this region'),
    ('pilot_compartment_ids.csv.gz', 'definition-B compartment of each of the 4,642 pilot ignitions'),
    ('addendum_transcript_post_freeze.jsonl', 'Bash, Edit and Write calls after the freeze command (m3)'),
    ('addendum_transcript_other_tools.jsonl', 'calls of all other tools from 06:51Z (m3)'),
    ('make_addendum_records.py', 'this build script'),
    ('verify_addendum_public.py', 'checks the public record for this addendum before any outcome (m5)'),
]
README_STEPS = {  # package file -> the FREEZE.json entry it must recreate (the README's 'Running the code' steps)
    'pilot_predictors_blind.csv.gz': '../p1/predictors_blind.csv', 'pilot_outcomes.csv.gz': '../p1/outcomes.csv',
    'pilot_raw_mtbs_perims.json.gz': '../p1/raw/mtbs_perims.json', 'pilot_p1_config.json': '../p1/p1_config.json',
    'pilot_results.json': '../p1/results.json', 'pilot_DEVIATION_2.json': '../p1/DEVIATION_2.json',
    'pilot_DEVIATION_3.json': '../p1/DEVIATION_3.json', 'pilot_raw_requests.log': '../p1/raw/requests.log',
    'predictors_blind.csv.gz': 'predictors_blind.csv'}
OUTCOME_FILES = ('outcomes.csv', 'OUTCOME_FETCH.json', 'OUTCOME_FETCH_FAILED.json', 'REGISTRATION.json',
                 'ADDENDUM_REGISTRATION.json', 'results.json')


def fail(msg):
    sys.exit('ADDENDUM FAIL: ' + msg)


def sha_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def redact(o, hide):
    """As extract_transcript.redact, for the hash set hide: copy of o with every token whose lower-case sha256 is in
    hide replaced by '[redacted]'; returns (copy, changed)."""
    if isinstance(o, str):
        new = TOKEN.sub(lambda m: '[redacted]' if sha_bytes(m.group(0).lower().encode()) in hide else m.group(0), o)
        return new, new != o
    if isinstance(o, dict):
        out, ch = {}, False
        for k, v in o.items():
            out[k], c = redact(v, hide); ch = ch or c
        return out, ch
    if isinstance(o, list):
        res = [redact(v, hide) for v in o]
        return [r[0] for r in res], any(r[1] for r in res)
    return o, False


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def privacy_hits(text):
    """Tokens with a part of 4+ characters (case-folded) that hashes into HIDE, and e-mail addresses."""
    hits = []
    for t in set(TOKEN.findall(text)):
        tl = t.lower()
        n = len(tl)
        if any(sha_bytes(tl[i:j].encode()) in HIDE for i in range(n) for j in range(i + 4, min(n, i + 40) + 1)):
            hits.append('token #' + sha_bytes(tl.encode())[:12])
    hits += ['e-mail address'] * len(EMAIL.findall(text))
    return hits


# ---- I1 (before): the freeze, and no outcome --------------------------------------------------------------------
os.chdir(ADD)
if sha_file(os.path.join(P1C, 'FREEZE.json')) != FREEZE_SHA:
    fail('p1c/FREEZE.json is not the v1.4 freeze')
F = json.load(open(os.path.join(P1C, 'FREEZE.json')))['sha256']
if F.get(PREREG) != PREREG_SHA:
    fail('FREEZE.json does not hold the v1.4 plan')


def check_frozen(when):
    bad = [p for p, h in F.items() if sha_file(os.path.join(P1C, p)) != h]
    if bad:
        fail(f'{when}: {len(bad)} frozen files differ from FREEZE.json, e.g. {bad[:3]}')
    for d in (P1C, PKG, ADD):
        hit = [f for f in OUTCOME_FILES if os.path.exists(os.path.join(d, f))]
        if hit:
            fail(f'{when}: outcome, fetch-record or registration file present in {d}: {hit}')
    return len(F)


n_frozen = check_frozen('before')
et = open(os.path.join(P1C, 'extract_transcript.py')).read()
if ast.literal_eval(re.search(r"^REDACT = (\{.*\})$", et, re.M).group(1)) != REDACT:
    fail('REDACT differs from extract_transcript.py')
if "TOKEN = re.compile(r'[A-Za-z0-9_]+')" not in et:
    fail('TOKEN differs from extract_transcript.py')

# ---- I2: command records ---------------------------------------------------------------------------------------
uses = []
for line in open(SRC):
    try:
        o = json.loads(line)
    except Exception:
        continue
    if o.get('isSidechain'):
        fail('the session transcript holds an agent (sidechain) row')
    ts = o.get('timestamp') or ''
    m = o.get('message') or {}
    wire = o.get('wireToolInputs') or {}
    for c in (m.get('content') if isinstance(m.get('content'), list) else []):
        if not isinstance(c, dict):
            continue
        if c.get('type') != 'tool_use' and str(c.get('type', '')).endswith('tool_use'):
            fail(f"unrecorded tool-call block type {c.get('type')} at {ts}")
        if c.get('type') == 'tool_use':
            uses.append(dict(ts=ts, id=c.get('id'), tool=c.get('name'), input=c.get('input') or {},
                             wire=wire.get(c.get('id')), cwd=o.get('cwd')))
ids = [u['id'] for u in uses]
if len(set(ids)) != len(ids):
    fail('duplicate tool_use ids in the session transcript')
uses.sort(key=lambda u: u['ts'])
last = uses[-1]
last_cmd = (last['wire'] or last['input']).get('command', '')
if not (last['tool'] == 'Bash' and SELF_CMD.fullmatch(last_cmd) and ('--dry-run' in last_cmd) == DRY):
    fail(f"this script's exact invocation must be the last tool call; the last is {last['ts']} {last['tool']}")
self_ts = last['ts']
uses = uses[:-1]

part2 = [json.loads(l) for l in open(os.path.join(P1C, 'logs/transcript_tool_calls_p1c_part2.jsonl'))]
if part2[-1]['timestamp'] != FREEZE_CMD:
    fail('part 2 does not end with the freeze command')
fz = [u for u in uses if u['ts'] == FREEZE_CMD]
if len(fz) != 1 or fz[0]['tool'] != part2[-1]['tool'] or redact(fz[0]['input'], REDACT)[0] != part2[-1]['input']:
    fail('the transcript copy of the freeze command does not match part 2')


def make_row(u):
    red, changed = redact(u['input'], HIDE)
    r = dict(timestamp=u['ts'], tool=u['tool'], input=red, cwd=u['cwd'], source='session transcript')
    if changed:
        r['redacted'] = True
    return r


post = [make_row(u) for u in uses if u['tool'] in EDIT_TOOLS and u['ts'] > FREEZE_CMD]
other = [make_row(u) for u in uses if u['tool'] not in EDIT_TOOLS]
if not post or not other:
    fail('empty record')
for fn, rows in (('addendum_transcript_post_freeze.jsonl', post), ('addendum_transcript_other_tools.jsonl', other)):
    seen = set()
    if os.path.exists(fn):
        seen = {l.rstrip('\n') for l in open(fn)}
    with open(fn, 'w') as fh:
        for r in rows:
            fh.write(json.dumps(r) + '\n')
    back = [json.loads(l) for l in open(fn)]
    if back != rows:
        fail(f'{fn} does not read back')
    for r in back:
        h = privacy_hits('\n'.join(strings(r)))
        if h:
            fail(f'{fn}: privacy check failed at {r["timestamp"]}: {h}')
    new = [json.dumps(r) for r in rows if json.dumps(r) not in seen]
    print(f'{fn}: {len(rows)} rows, {len(new)} not in the previous build:', flush=True)
    for s in new:
        r = json.loads(s)
        print('   ', r['timestamp'], r['tool'], json.dumps(r['input'])[:150].replace('\\n', ' | '), flush=True)
by_tool = Counter(r['tool'] for r in other)
other_pre = sum(r['timestamp'] < FREEZE_CMD for r in other)
print(f'records: {len(post)} post-freeze ({post[0]["timestamp"]} -> {post[-1]["timestamp"]}); {len(other)} other-tool '
      f'({other_pre} before the freeze); left out: {self_ts}', flush=True)

# ---- I3: compartment labels and the re-run recipe ----------------------------------------------------------------
spec = importlib.util.spec_from_file_location('rt', os.path.join(P1C, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
labels = {}
for key, pkg_npz, src_npz, pred_csv, ids_gz, n_b, n_b_comp in (
        ('this_region', 'compartments_static.npz', os.path.join(P1C, 'compartments_static.npz'),
         os.path.join(P1C, 'predictors_blind.csv'), 'compartment_ids_blind.csv.gz', 11314, 2065),
        ('pilot', 'pilot_compartments_static.npz', os.path.join(P1, 'compartments_static.npz'),
         os.path.join(P1, 'predictors_blind.csv'), 'pilot_compartment_ids.csv.gz', 2677, 555)):
    if sha_file(pkg_npz) != sha_file(src_npz):
        fail(f'{pkg_npz} is not a byte copy of {src_npz}')
    L = np.load(pkg_npz)['labB']
    pred = rt.add_regions(pd.read_csv(pred_csv))
    ids = pd.read_csv(ids_gz)
    exp = L[pred['row'].values, pred['col'].values]
    if list(ids.columns) != ['fod_id', 'compartment_B'] or len(ids) != len(pred) or \
            not (ids['fod_id'].values == pred['fod_id'].values).all() or not (ids['compartment_B'].values == exp).all():
        fail(f'{ids_gz} does not equal labB at the cells of {pred_csv}')
    sB, _ = rt.sample(pred.assign(fire_size=1.0), 'B')
    labs = L[sB['row'].values, sB['col'].values]
    if len(sB) != n_b or (labs == 0).any() or len(np.unique(labs)) != n_b_comp:
        fail(f'{key}: the B sample has {len(sB)} ignitions, label 0, or {len(np.unique(labs))} compartments '
             f'(expected {n_b}, {n_b_comp})')
    labels[key] = dict(package_file=pkg_npz, copy_of=os.path.relpath(src_npz, '/home/claude'), npz_sha256=sha_file(pkg_npz),
                       labB_shape=list(L.shape), labB_dtype=str(L.dtype),
                       labB_bytes_sha256=sha_bytes(np.ascontiguousarray(L).tobytes()),
                       ids_file=ids_gz, ids_gz_sha256=sha_file(ids_gz), ids_csv_sha256=sha_bytes(gzip.open(ids_gz).read()),
                       n_ignitions=int(len(ids)), n_ignitions_on_label_0=int((ids['compartment_B'] == 0).sum()),
                       n_compartments=int(ids.loc[ids['compartment_B'] != 0, 'compartment_B'].nunique()),
                       b_sample=dict(n=int(len(sB)), compartments=int(len(np.unique(labs))), on_label_0=0))
EXPECT_LABB = dict(this_region='ee515ce845f3ee1e22ce309170cd149753f41607d26a2922918879853481c89a',
                   pilot='47f992dbe50ced1fa495a9cca8e66172439930a76e3c50584a1d133a04be6bfa')
for k, v in EXPECT_LABB.items():
    if labels[k]['labB_bytes_sha256'] != v:
        fail(f'{k}: labB bytes hash differs from the one stated in the addendum')
recipe = {}
for pf, key in README_STEPS.items():
    p = os.path.join(PKG, pf)
    got = sha_bytes(gzip.open(p).read()) if pf.endswith('.gz') else sha_file(p)
    if got != F[key]:
        fail(f'package {pf} does not recreate the frozen {key}')
    recipe[pf] = dict(recreates=key, sha256=got)
recipe['pilot_compartments_static.npz'] = dict(recreates='../p1/compartments_static.npz (not frozen; see labels.pilot)',
                                               sha256=labels['pilot']['npz_sha256'])
json.dump(dict(note='Addendum 1 to plan P1C v1.4, m1. Definition-B compartment labels (labB) used by the compartment '
                    'models of the stress set, the pilot re-read, the validation and the power analysis. Label 0 is '
                    'outside every compartment.', labels=labels, rerun_recipe=recipe),
          open('COMPARTMENT_LABELS.json', 'w'), indent=1)

# ---- I4: fill the addendum --------------------------------------------------------------------------------------
for f in ('AUDIT_5_of_v1.4.md', 'REVIEW_of_ADDENDUM_v1.4.md'):
    if sha_file(f) != sha_file(os.path.join(P1C, 'audits', f)):
        fail(f'{f} is not the saved report')
old_sums = {}
for line in open(os.path.join(PKG, 'SHA256SUMS.txt')):
    h, n = line.rstrip('\n').split('  ', 1); old_sums[n] = h
old_sums_bytes = open(os.path.join(PKG, 'SHA256SUMS.txt'), 'rb').read()
old_listing = sorted(n for n in os.listdir(PKG) if n != 'SHA256SUMS.txt')
if old_listing != sorted(old_sums):
    fail('the package listing differs from its SHA256SUMS.txt')
new_names = [f for f, _ in ADD_FILES] + ['ADDENDUM_v1.4.md', 'ADDENDUM_v1.4.md.ots']
clash = [n for n in new_names if n in old_sums]
if clash:
    fail(f'addendum files already in the package: {clash}')
gen_utc = time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())
fill = {
    'GEN_UTC': gen_utc,
    'OTHER_N': f'{len(other):,}',
    'OTHER_BY_TOOL': ', '.join(f'{DISPLAY.get(t, t)} {n}' for t, n in sorted(by_tool.items(), key=lambda x: (-x[1], x[0]))),
    'OTHER_PRE_N': f'{other_pre:,}',
    'POST_N': f'{len(post):,}',
    'POST_FIRST': post[0]['timestamp'],
    'POST_LAST': post[-1]['timestamp'],
    'NFREEZE': f'{n_frozen:,}',
    'NOLD': f'{len(old_sums):,}',
    'NADD': f'{len(new_names):,}',
    'NNEW': f'{len(old_sums) + len(new_names):,}',
}
tpl = open('ADDENDUM_v1.4.template.md').read()
out = tpl
for k, v in fill.items():
    out = out.replace(f'@@{k}@@', v)
if '@@' in out:
    fail('unfilled placeholder: ' + re.search(r'@@\w*@@', out).group(0))
expect = out
table = ['| File | Bytes | SHA-256 | What it is |', '|---|---|---|---|']
for f, what in ADD_FILES:
    table.append(f'| `{f}` | {os.path.getsize(f):,} | `{sha_file(f)}` | {what} |')
out = out.replace('<!-- FILES -->\n<!-- /FILES -->', '<!-- FILES -->\n' + '\n'.join(table) + '\n<!-- /FILES -->')
blk = out.split('<!-- FILES -->\n', 1)[1].split('\n<!-- /FILES -->', 1)[0]
if len(blk.splitlines()) != len(ADD_FILES) + 2:
    fail('file table not written')
if out.replace('<!-- FILES -->\n' + blk + '\n<!-- /FILES -->', '<!-- FILES -->\n<!-- /FILES -->', 1) != expect:
    fail('the addendum differs from its template by more than the placeholders and the file table')
with open('ADDENDUM_v1.4.md', 'w') as fh:
    fh.write(out)

# ---- P: privacy over every shipped text file ---------------------------------------------------------------------
for f in ['ADDENDUM_v1.4.md'] + [f for f, _ in ADD_FILES if not f.endswith(('.npz', '.gz'))]:
    h = privacy_hits(open(f, encoding='utf-8').read())
    if h:
        fail(f'{f}: privacy check failed: {h}')
for f in ('compartment_ids_blind.csv.gz', 'pilot_compartment_ids.csv.gz'):
    if privacy_hits(gzip.open(f).read().decode()):
        fail(f'{f}: privacy check failed')
if DRY:
    check_frozen('after (dry run)')
    print('DRY RUN: not stamped; package untouched'); print(json.dumps(fill, indent=1))
    sys.exit(0)

# ---- I6: timestamp ----------------------------------------------------------------------------------------------
if os.path.exists('ADDENDUM_v1.4.md.ots'):
    os.remove('ADDENDUM_v1.4.md.ots')
st = subprocess.run(['ots', 'stamp', 'ADDENDUM_v1.4.md'], capture_output=True, text=True, timeout=180)
if st.returncode != 0 or not os.path.exists('ADDENDUM_v1.4.md.ots'):
    fail('OpenTimestamps stamp failed: ' + (st.stderr or st.stdout)[-500:])
ots = open('ADDENDUM_v1.4.md.ots', 'rb').read()
if not (ots[:31] == OTS_MAGIC and ots[31] == 1 and ots[32] == 0x08 and ots[33:65] == bytes.fromhex(sha_file('ADDENDUM_v1.4.md'))):
    fail('the .ots proof does not hold the addendum digest at offset 33 after a sha256 op')

# ---- I5: the package --------------------------------------------------------------------------------------------
check_frozen('before copying')
copied = []
try:
    for n in new_names:
        shutil.copy2(n, os.path.join(PKG, n)); copied.append(n)
    names = sorted(n for n in os.listdir(PKG) if n != 'SHA256SUMS.txt')
    if names != sorted(old_listing + new_names):
        raise RuntimeError('unexpected files in the package')
    sums = {n: sha_file(os.path.join(PKG, n)) for n in names}
    changed = [n for n in old_sums if sums[n] != old_sums[n]]
    if changed:
        raise RuntimeError(f'package files changed: {changed}')
    for n in new_names:
        if sums[n] != sha_file(n):
            raise RuntimeError(f'copy of {n} differs')
    with open(os.path.join(PKG, 'SHA256SUMS.txt'), 'w') as fh:
        for n in names:
            fh.write(f'{sums[n]}  {n}\n')
    check_frozen('after')
except (Exception, SystemExit) as e:
    for n in copied:
        os.remove(os.path.join(PKG, n))
    open(os.path.join(PKG, 'SHA256SUMS.txt'), 'wb').write(old_sums_bytes)
    fail(f'package step failed and was rolled back: {e}')
size = sum(os.path.getsize(os.path.join(PKG, n)) for n in names)
print(json.dumps(dict(built_utc=gen_utc, addendum_sha256=sha_file('ADDENDUM_v1.4.md'), ots_bytes=len(ots),
                      frozen_files_unchanged=n_frozen, package_files_listed=len(names), package_kib=size // 1024,
                      post_freeze_calls=len(post), other_tool_calls=len(other), other_by_tool=dict(by_tool),
                      labels={k: dict(npz_sha256=v['npz_sha256'][:12], b_compartments=v['b_sample']['compartments'])
                              for k, v in labels.items()}), indent=1))
print('ADDENDUM OK')
