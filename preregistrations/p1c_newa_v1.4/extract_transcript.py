#!/usr/bin/env python3
"""Write logs/transcript_tool_calls_p1c_part2.jsonl: the command record that follows the extract frozen with plan v1.2.

Part 1, logs/transcript_tool_calls_p1c.jsonl, is kept exactly as frozen with v1.2 (its sha256 is in
history_v1.2/FREEZE.json). It holds the shell commands and file edits from 20:33 ET (00:33Z) to 02:09:27 ET whose
text matches PAT below, a filter of P1C file and script names; read-only monitors and runs that named no P1C file are
not in it. It cannot be regenerated, because the session transcript was compacted at about 02:51 ET and now begins
there.

Part 2 (written here, plan v1.4) has NO name filter. It holds, with a 'source' field on every row:
  (a) every Bash, Edit and Write call after part 1's last row and up to 02:31:57 ET (06:31:57Z), recovered from
      logs/transcript_view_by_third_audit_0232ET.txt: the third audit's own printout of the session transcript (every
      call from 06:09:28Z), made at 02:32 ET. Each recovered command's length must equal the length printed with it;
  (b) every Bash, Edit and Write call from 02:51 ET (06:51Z) onward, from the session transcript itself.
Calls between 02:32 and 02:51 ET cannot be recovered (plan, section 3). The only call skipped is a bare invocation of
this script ('python3 extract_transcript.py' with nothing else), whose output is this file.
Privacy: two personal identifiers occur in a few commands only as tokens of a privacy filter (a check that the
published audit reports contain no personal data). Any token whose lower-case SHA-256 is in REDACT is replaced by
'[redacted]'; nothing else is changed, and the rows carry 'redacted': true where it applied."""
import hashlib, json, re

SRC = '/root/.claude/projects/-home-claude/d23d759f-9c1b-589b-9849-6bba926e6bc3.jsonl'
VIEW = 'logs/transcript_view_by_third_audit_0232ET.txt'
PAT = re.compile(r'p1c|/p1/|\.\./p1|p1_config|fetch_data|build_predictors|run_test|run_chain|simcal|freeze\.py|equivalence|'
                 r'validate_synthetic|blind_design|fill_prereg|fetch_outcomes|PREREG|history_v1|calibrate_critical|exposure_lists')
BARE = re.compile(r'^\s*(cd\s+\S+\s*&&\s*)?python3\s+(\./)?extract_transcript\.py\s*$')
LAST_PART1 = '2026-10-21T06:09:27.776Z'           # the last row of part 1
REDACT = {'576ba7c2e4abb7184ca409154dbbbd5306c1a80747fbce4148ea6271fd21e776', 'b40e514e1865e87cf62386bb318d9ee6fcf5d6d4fd75456dbe62015c62886d5d'}
TOKEN = re.compile(r'[A-Za-z0-9_]+')


def redact(o):
    """Copy of o with every token whose lower-case sha256 is in REDACT replaced; returns (copy, changed)."""
    if isinstance(o, str):
        new = TOKEN.sub(lambda m: '[redacted]' if hashlib.sha256(m.group(0).lower().encode()).hexdigest() in REDACT else m.group(0), o)
        return new, new != o
    if isinstance(o, dict):
        out, ch = {}, False
        for k, v in o.items():
            out[k], c = redact(v); ch = ch or c
        return out, ch
    if isinstance(o, list):
        res = [redact(v) for v in o]
        return [r[0] for r in res], any(r[1] for r in res)
    return o, False
RESUME = '2026-10-21T06:51:00Z'


def keep(tool, inp):
    return not (tool == 'Bash' and BARE.match(inp.get('command', '')))


rows = []
view = open(VIEW).read()
recovered = re.findall(r'(\d{4}-\d\d-\d\dT[\d:.]+Z) (Bash|Edit|Write) (\d+)\n(.*?)\n=======(?:\n|$)', view, flags=re.S)
assert len(recovered) == view.count('\n=======') , 'unparsed blocks in the third audit view'
assert recovered, 'nothing parsed from the third audit view'
for ts, tool, n, text in recovered:
    assert len(text) == int(n), f'length mismatch at {ts}: {len(text)} != {n}'
    inp = {'command': text} if tool == 'Bash' else json.loads(text)
    if ts > LAST_PART1 and keep(tool, inp):
        rows.append(dict(timestamp=ts, tool=tool, input=inp,
                         source='third audit printout of the session transcript, 02:32 ET (command text only)'))
assert json.loads(open('logs/transcript_tool_calls_p1c.jsonl').readlines()[-1])['timestamp'] == LAST_PART1
n_a = len(rows)
for line in open(SRC):
    try:
        o = json.loads(line)
    except Exception:
        continue
    ts = o.get('timestamp') or ''
    m = o.get('message') or {}
    for c in (m.get('content') if isinstance(m.get('content'), list) else []):
        if isinstance(c, dict) and c.get('type') == 'tool_use' and c.get('name') in ('Bash', 'Edit', 'Write'):
            if ts >= RESUME and keep(c['name'], c.get('input') or {}):
                rows.append(dict(timestamp=ts, tool=c['name'], input=c['input'], source='session transcript'))
rows.sort(key=lambda r: r['timestamp'])
for r in rows:
    r['input'], changed = redact(r['input'])
    if changed:
        r['redacted'] = True
with open('logs/transcript_tool_calls_p1c_part2.jsonl', 'w') as fh:
    for r in rows:
        fh.write(json.dumps(r) + '\n')
print(f'{len(rows)} tool calls ({n_a} recovered, {len(rows) - n_a} from the session transcript)',
      rows[0]['timestamp'], '->', rows[-1]['timestamp'])
