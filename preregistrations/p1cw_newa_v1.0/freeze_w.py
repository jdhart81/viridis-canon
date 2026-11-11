#!/usr/bin/env python3
"""P1C-W Stage 1 freeze (v1.0): hash every frozen file into FREEZE.json, refusing if any check fails.

Run from this folder inside a viridis-canon checkout (it reads ../p1c_newa_v1.4).
  python3 freeze_w.py            write FREEZE.json (refuses if it already exists)
  python3 freeze_w.py --supersede "REASON"   replace an earlier FREEZE.json, keeping it as FREEZE_superseded_N.json
  python3 freeze_w.py --verify   recompute every hash and compare with FREEZE.json
  python3 freeze_w.py --stamp    OpenTimestamps-stamp FREEZE.json

Invariants checked (the run stops on any failure):
  W1 no outcomes.csv, results.json or REGISTRATION.json exists in this folder or in ../p1c_newa_v1.4
     (no confirmatory outcome has been joined here);
  W2 the wind table carries only fod_id and the six wind columns, no outcome field, and covers every ignition of the
     P1C blind predictor table;
  W3 the P1C files this test reads (run_test.py, simcal.py, predictors_blind.csv, CALIBRATION.json,
     CRITICAL_VALUES.json, compartments_static.npz and the two public pilot tables) are byte-identical to the
     P1C v1.4 freeze;
  W4 CALIBRATION_WIND.json was produced by the calibrate_wind.py, simcal.py, run_test.py and wind table being frozen;
  W5 the critical values obey plan invariant I3 (C_W >= 2.53, C1_W >= 2.08) and gamma_min = 0.0265;
  W6 the plan has no unfilled {{PLACEHOLDER}} and every frozen file exists.
"""
import gzip, hashlib, io, json, os, re, subprocess, sys, time

import pandas as pd

P1C = '../p1c_newa_v1.4'
PLAN = 'PREREGISTRATION_P1CW_NEWA_v1.0.md'
FROZEN = [PLAN, 'README.md', 'fetch_era5_wind.py', 'build_wind.py', 'calibrate_wind.py', 'freeze_w.py',
          'wind_blind_newa.csv', 'CALIBRATION_WIND.json', 'calibrate_wind.out', 'raw_era5_requests.log',
          'RAW_ERA5_SHA256SUMS.txt', 'stage2_oregon_p1_config.json']
# P1C dependency: (name used by calibrate_wind.py, file in ../p1c_newa_v1.4, key in the P1C FREEZE.json or None)
DEPS = [('p1c/run_test.py', 'run_test.py', 'run_test.py'),
        ('p1c/simcal.py', 'simcal.py', 'simcal.py'),
        ('p1c/predictors_blind.csv', 'predictors_blind.csv.gz', 'predictors_blind.csv'),
        ('p1c/CALIBRATION.json', 'CALIBRATION.json', 'CALIBRATION.json'),
        ('p1c/CRITICAL_VALUES.json', 'CRITICAL_VALUES.json', 'CRITICAL_VALUES.json'),
        ('p1c/compartments_static.npz', 'compartments_static.npz', None),   # in the P1C SHA256SUMS.txt
        ('p1/predictors_blind.csv', 'pilot_predictors_blind.csv.gz', '../p1/predictors_blind.csv'),
        ('p1/outcomes.csv', 'pilot_outcomes.csv.gz', '../p1/outcomes.csv')]
WIND_COLS = {'fod_id', 'W1', 'W3', 'W7', 'P3', 'W3mean', 'W3_pct'}
FORBID = {'fire_size', 'fire_size_class', 'cont_date', 'cont_doy', 'cont_time'}


def h(b):
    return hashlib.sha256(b).hexdigest()


def read(p):
    b = open(p, 'rb').read()
    return gzip.decompress(b) if p.endswith('.gz') else b


def p1c_sums():
    out = {}
    for line in open(os.path.join(P1C, 'SHA256SUMS.txt')):
        parts = line.split()
        if len(parts) == 2:
            out[parts[1].lstrip('*').lstrip('./')] = parts[0]
    return out


def checks():
    for d in ('.', P1C):
        for f in ('outcomes.csv', 'results.json', 'REGISTRATION.json'):
            assert not os.path.exists(os.path.join(d, f)), f'W1: {d}/{f} present'
    missing = [f for f in FROZEN if not os.path.exists(f) and f != 'freeze_w.py']
    assert not missing, f'W6: missing {missing}'
    assert not re.search(r'\{\{[A-Z0-9_]+\}\}', open(PLAN).read()), 'W6: unfilled placeholder in the plan'
    w = pd.read_csv('wind_blind_newa.csv')
    assert set(w.columns) == WIND_COLS, f'W2: wind columns {sorted(w.columns)}'
    assert not ({c.lower() for c in w.columns} & FORBID), 'W2: outcome field in the wind table'
    pred = pd.read_csv(io.BytesIO(read(os.path.join(P1C, 'predictors_blind.csv.gz'))))
    assert not ({c.lower() for c in pred.columns} & FORBID), 'W2: outcome field in the P1C predictor table'
    assert set(pred['fod_id']) <= set(w['fod_id']), 'W2: wind table misses P1C ignitions'
    assert w[list(WIND_COLS - {'fod_id'})].notna().all().all(), 'W2: missing wind values'
    F = json.load(open(os.path.join(P1C, 'FREEZE.json')))['sha256']; S = p1c_sums()
    dep = {}
    for name, f, key in DEPS:
        got = h(read(os.path.join(P1C, f)))
        want = F[key] if key else S[f]
        assert got == want, f'W3: {f} differs from the P1C v1.4 freeze'
        dep[name] = got
    C = json.load(open('CALIBRATION_WIND.json'))
    cs = C['code_sha256']
    assert cs['calibrate_wind.py'] == h(read('calibrate_wind.py')), 'W4: calibration stale for calibrate_wind.py'
    assert cs['simcal.py'] == dep['p1c/simcal.py'] and cs['run_test.py'] == dep['p1c/run_test.py'], 'W4: P1C code stale'
    assert cs['wind'] == h(read('wind_blind_newa.csv')), 'W4: calibration stale for the wind table'
    cr = C['critical']
    assert cr['C_W'] >= 2.53 and cr['C1_W'] >= 2.08 and C['gamma_min'] == 0.0265, 'W5: critical values break I3'
    return dep, cr


def main(reason=None):
    sup = []
    for k in range(1, 10):
        p = f'FREEZE_superseded_{k}.json'
        if os.path.exists(p):
            sup.append(json.load(open(p))['_superseded'])
    if os.path.exists('FREEZE.json'):
        assert reason, 'FREEZE.json exists; use --verify, or --supersede "REASON"'
        old = json.load(open('FREEZE.json')); k = len(sup) + 1
        entry = dict(freeze_sha256=h(read('FREEZE.json')), frozen_at_utc=old['frozen_at_utc'], reason=reason)
        old['_superseded'] = entry
        json.dump(old, open(f'FREEZE_superseded_{k}.json', 'w'), indent=1)
        os.remove('FREEZE.json'); sup.append(entry)
    for k in range(1, len(sup) + 1):
        FROZEN.append(f'FREEZE_superseded_{k}.json')
    dep, cr = checks()
    t = time.time()
    rec = dict(version='1.0', supersedes=sup,
               stage='1 (northeast Washington, the P1C v1.4 sample)',
               extends=dict(registration='preregistrations/p1c_newa_v1.4',
                            freeze_sha256=h(read(os.path.join(P1C, 'FREEZE.json')))),
               frozen_at_local=time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(t)),
               frozen_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t)),
               decision_rule=(f"SUPPORTED iff gamma + {cr['C_W']} * max(SE_twoway, SE_year) < 0; CONTRADICTED iff "
                              f"gamma - {cr['C_W']} * max(SE_twoway, SE_year) > 0; WIND-INVARIANT iff gamma -/+ "
                              f"{cr['C1_W']} * max(SE_twoway, SE_year) lies inside +/-0.0265; else INCONCLUSIVE. "
                              'gamma = coefficient on Lc x z_w (Lc = log10 A_enc - 3.63, z_w = standardized W3) in '
                              'M2R-W = M2R + z_w + Lc*z_w + Lc*cause + z_w*cause, definition B, the P1C v1.4 sample.'),
               critical_values=dict(C_W=cr['C_W'], C1_W=cr['C1_W'], gamma_min=0.0265),
               note=('Frozen before wind and fire size were joined for any ignition in this region. No P1C '
                     'outcomes.csv was read in building the wind table or the calibration (asserted in code). '
                     'Raw ERA5 months are not shipped (1.1 GB); their hashes are in RAW_ERA5_SHA256SUMS.txt and '
                     'fetch_era5_wind.py re-fetches them from the public NSF NCAR mirror.'),
               sha256={f: h(read(f)) for f in FROZEN},
               p1c_dependencies_sha256=dep)
    json.dump(rec, open('FREEZE.json', 'w'), indent=1)
    print('frozen', len(FROZEN) + len(dep), 'files at', rec['frozen_at_local'])
    print('FREEZE.json sha256', h(read('FREEZE.json')))


def verify():
    dep, _ = checks()
    R = json.load(open('FREEZE.json'))
    bad = [f for f, v in R['sha256'].items() if h(read(f)) != v] + [k for k, v in R['p1c_dependencies_sha256'].items() if dep[k] != v]
    print('OK, all hashes match' if not bad else f'MISMATCH: {bad}')
    sys.exit(1 if bad else 0)


def stamp():
    cals = ['https://alice.btc.calendar.opentimestamps.org', 'https://finney.calendar.eternitywall.com',
            'https://bob.btc.calendar.opentimestamps.org', 'https://a.pool.opentimestamps.org']
    cmd = ['ots', 'stamp', '-m', '1'] + sum([['-c', c] for c in cals], []) + ['FREEZE.json']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(r.stdout, r.stderr)
    assert os.path.exists('FREEZE.json.ots'), 'stamp failed'


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    a = sys.argv[1] if len(sys.argv) > 1 else ''
    if a == '--supersede':
        main(sys.argv[2])
    else:
        {'--verify': verify, '--stamp': stamp}.get(a, main)()
