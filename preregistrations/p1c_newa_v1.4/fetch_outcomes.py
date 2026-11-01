#!/usr/bin/env python3
"""P1 confirmatory replication (NE Washington): fetch outcomes ONLY after the freeze AND the public registration.

guards() runs inside fetch(), immediately before any outcome request; if a guard fails nothing is requested.
  G1  FREEZE.json exists and every frozen file still has its frozen SHA-256 (nothing edited after the freeze).
  G2  The plan is PUBLIC and is the frozen plan. REGISTRATION.json only says where to look: a commit in a public
      GitHub repository, or a Zenodo record. The guard itself downloads the registered
      PREREGISTRATION_P1C_NEWA_v1.4.md and FREEZE.json without credentials of its own, right now, and requires
      both to match the local frozen files byte-for-byte; a hand-written REGISTRATION.json cannot pass on its own.
      Limits: requests go through the environment's HTTPS proxy, which could add credentials, and a GitHub commit
      can later be deleted; Zenodo is therefore the preferred registration. The downloaded hashes are recorded.
  G3  No ignition in the confirmatory table appears in the pilot table.
Retrieval rules (registered):
  R1  every requested fod_id must come back, exactly once;
  R2  for every record, fire_year, discovery_date, latitude and longitude must equal the frozen blind record;
  R3  every request (URL and body) is logged to outcome_requests.log with a timestamp; afterwards
      OUTCOME_FETCH.json records counts, the service's layer metadata, and the SHA-256 of outcomes.csv and of
      the log, and is stamped with OpenTimestamps.
  If R1 or R2 fails, outcomes.csv is NOT written; the failure is recorded and must be resolved as a numbered
  deviation before any analysis.
Usage: python3 fetch_outcomes.py            (guards, then fetch)
       python3 fetch_outcomes.py --check    (guards only; fetches nothing)
"""
import csv, hashlib, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

PREREG = 'PREREGISTRATION_P1C_NEWA_v1.4.md'
SERVICE = 'https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0'


def sha256b(b):
    return hashlib.sha256(b).hexdigest()


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'viridis-p1c/1.1'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def guards():
    # G1
    if not os.path.exists('FREEZE.json'):
        sys.exit('G1 FAIL: FREEZE.json missing; the plan is not frozen')
    frozen = json.load(open('FREEZE.json'))
    for path, h in frozen['sha256'].items():
        if sha256b(open(path, 'rb').read()) != h:
            sys.exit(f'G1 FAIL: {path} changed after the freeze')
    # G2: download the public copies now and compare
    if not os.path.exists('REGISTRATION.json'):
        sys.exit('G2 FAIL: REGISTRATION.json missing; the plan is not yet publicly registered')
    reg = json.load(open('REGISTRATION.json'))
    files = [PREREG, 'FREEZE.json']
    if 'github' in reg:
        gh = reg['github']
        if not (re.fullmatch(r'[A-Za-z0-9-]+/[A-Za-z0-9._-]+', gh.get('repo', '')) and re.fullmatch(r'[0-9a-f]{40}', gh.get('commit', ''))):
            sys.exit('G2 FAIL: REGISTRATION.json github entry needs repo owner/name and a full 40-hex commit')
        urls = {f: f"https://raw.githubusercontent.com/{gh['repo']}/{gh['commit']}/{gh['folder'].strip('/')}/{f}" for f in files}
        where = f"github.com/{gh['repo']}@{gh['commit'][:12]}"
    elif 'zenodo' in reg:
        rid = str(reg['zenodo'].get('record', ''))
        if not rid.isdigit():
            sys.exit('G2 FAIL: REGISTRATION.json zenodo entry needs a numeric record id')
        rec = json.loads(get(f'https://zenodo.org/api/records/{rid}'))
        byname = {f['key']: f for f in rec.get('files', [])}
        if any(f not in byname for f in files):
            sys.exit('G2 FAIL: the Zenodo record does not hold both registered files')
        urls = {f: byname[f]['links']['self'] for f in files}
        where = f"doi:{rec.get('doi')}"
    else:
        sys.exit('G2 FAIL: REGISTRATION.json names neither a GitHub commit nor a Zenodo record')
    downloads = {}
    for f, u in urls.items():
        try:
            public = get(u)
        except Exception as e:
            sys.exit(f'G2 FAIL: could not download the public copy of {f} anonymously ({e})')
        if sha256b(public) != sha256b(open(f, 'rb').read()):
            sys.exit(f'G2 FAIL: the public copy of {f} differs from the local frozen file')
        downloads[f] = dict(url=u, sha256=sha256b(public), at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    # G3
    pilot = {int(float(r['fod_id'])) for r in csv.DictReader(open(json.load(open('p1_config.json'))['exclude_fod_ids_from']))}
    mine = [int(float(r['fod_id'])) for r in csv.DictReader(open('predictors_blind.csv'))]
    if pilot & set(mine):
        sys.exit('G3 FAIL: pilot ignitions present in the confirmatory table')
    print(f'guards passed: frozen files intact; public copy verified at {where}; samples disjoint')
    return mine, where, downloads


def fetch():
    ids, where, downloads = guards()           # always re-run the guards immediately before requesting outcomes
    blind = {int(float(f['attributes']['fod_id'])): f['attributes'] for f in json.load(open('raw/fpafod_ignitions_blind.json'))}
    log = open('outcome_requests.log', 'a')
    log.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} GET {SERVICE}?f=json\n"); log.flush()
    meta = json.loads(get(SERVICE + '?f=json'))
    rows = []
    for i in range(0, len(ids), 200):
        chunk = ids[i:i + 200]
        q = dict(where='fod_id IN (' + ','.join(str(x) for x in chunk) + ')',
                 outFields='fod_id,fire_size,fire_size_class,fire_year,discovery_date,latitude,longitude',
                 returnGeometry='false', f='json')
        body = urllib.parse.urlencode(q)
        for attempt in range(4):
            try:
                log.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} POST {SERVICE}/query {body}\n"); log.flush()
                r = json.loads(get(SERVICE + '/query', data=body.encode()))
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(5 * (attempt + 1))
        rows += [f['attributes'] for f in r['features']]
    log.close()
    got = [int(row['fod_id']) for row in rows]
    problems = []
    if sorted(got) != sorted(ids):                                       # R1
        problems.append(f'R1: requested {len(ids)} ids, received {len(got)} records ({len(set(ids) - set(got))} missing, '
                        f'{len(got) - len(set(got))} duplicated)')
    mism = [row['fod_id'] for row in rows if int(row['fod_id']) in blind and any(
        row[k] != blind[int(row['fod_id'])][k] for k in ('fire_year', 'discovery_date', 'latitude', 'longitude'))]
    if mism:                                                             # R2
        problems.append(f'R2: {len(mism)} records differ from the frozen blind records in year, date or location')
    rec = dict(fetched_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), registration=where, g2_downloads=downloads,
               requested=len(ids), received=len(got), layer_name=meta.get('name'),
               layer_description=(meta.get('description') or '')[:2000], layer_editing_info=meta.get('editingInfo'),
               log_sha256=sha256b(open('outcome_requests.log', 'rb').read()), problems=problems)
    if problems:
        json.dump(rec, open('OUTCOME_FETCH_FAILED.json', 'w'), indent=1)
        sys.exit('RETRIEVAL FAIL (outcomes.csv not written; record a deviation): ' + '; '.join(problems))
    with open('outcomes.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['fod_id', 'fire_size', 'fire_size_class'], extrasaction='ignore')
        w.writeheader(); w.writerows(rows)
    rec['outcomes_sha256'] = sha256b(open('outcomes.csv', 'rb').read())
    json.dump(rec, open('OUTCOME_FETCH.json', 'w'), indent=1)
    stamped = False
    try:
        stamped = subprocess.run(['ots', 'stamp', 'OUTCOME_FETCH.json'], capture_output=True, timeout=120).returncode == 0
    except Exception:
        pass
    json.dump(dict(ots_stamped=stamped, at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())), open('OUTCOME_FETCH_STAMP.json', 'w'))
    if not stamped:
        print('WARNING: OpenTimestamps stamp of OUTCOME_FETCH.json failed; stamp it by hand and record that.')
    print('outcomes fetched:', len(rows), 'of', len(ids), '| record: OUTCOME_FETCH.json')


if __name__ == '__main__':
    if '--check' in sys.argv:
        guards()
    else:
        fetch()
