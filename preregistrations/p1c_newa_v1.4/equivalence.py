#!/usr/bin/env python3
"""Code equivalence with the pilot, rerun before every freeze. Writes EQUIVALENCE.json.
  (1) build: the confirmatory build_predictors.py, run on the pilot's raw data and config in a scratch directory,
      must reproduce the frozen pilot predictor table byte-for-byte (sha256 57118595...).
  (2) model: replaying the pilot's run_test_dev1.py call sequence with the confirmatory run_test.py functions
      (same RNG seed and order) must reproduce EVERY number in the pilot's results.json exactly, including the
      bootstrap intervals, H3, H4 and every sensitivity analysis.
Pilot outcomes are already known; no confirmatory outcome is read."""
import hashlib, importlib.util, json, os, shutil, subprocess, sys, time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
SC = sys.argv[1]
PILOT_TABLE_SHA = '57118595eea2a28b2e268733ec9645304fdb283bfc60ed107c332624a96dc4d0'

# (1) build
b = os.path.join(SC, 'build'); shutil.rmtree(b, ignore_errors=True); os.makedirs(b)
os.symlink('/home/claude/p1/raw', os.path.join(b, 'raw'))
shutil.copy('/home/claude/p1/p1_config.json', b); shutil.copy(os.path.join(HERE, 'build_predictors.py'), b)
t = time.time(); subprocess.run([sys.executable, 'build_predictors.py'], cwd=b, check=True, capture_output=True)
rebuilt = sha(os.path.join(b, 'predictors_blind.csv'))
build = dict(build_predictors_sha256=sha(os.path.join(HERE, 'build_predictors.py')), rebuilt_pilot_table_sha256=rebuilt,
             frozen_pilot_table_sha256=PILOT_TABLE_SHA, identical=(rebuilt == PILOT_TABLE_SHA), seconds=round(time.time() - t))

# (2) model
spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
rt.RNG = np.random.default_rng(20261020)
df = pd.read_csv('/home/claude/p1/predictors_blind.csv').merge(pd.read_csv('/home/claude/p1/outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
R = {'primary': []}
for defn in ['A50', 'B']:
    R['primary'].append(rt.fit(df, defn, 'M1'))
    R['primary'].append(rt.fit(df, defn, 'M2', boot=True))
R['H3_escaped'] = [rt.fit(df, d, 'M2', min_size=10) for d in ['A50', 'B']]
R['H4_containment'] = [rt.containment_perm(df, d) for d in ['A50', 'B']]
S = [dict(label='A25 secondary definition (PCL > 0.25), M1', **rt.fit(df, 'A25', 'M1')),
     dict(label='A25 secondary definition (PCL > 0.25), M2', **rt.fit(df, 'A25', 'M2'))]
for d in ['A50', 'B']:
    S.append(dict(label='S1 snap on-holdable', **rt.fit(df, d, 'M2', snap=True)))
    S.append(dict(label='S2 include censored', **rt.fit(df, d, 'M2', include_censored=True)))
    S.append(dict(label='S3 drop coarse coords', **rt.fit(df, d, 'M2', extra=lambda s: ~s['coarse_coords'].astype(bool))))
    S.append(dict(label='S6a natural cause', **rt.fit(df, d, 'M2', extra=lambda s: s['cause'] == 'Natural')))
    S.append(dict(label='S6b human cause', **rt.fit(df, d, 'M2', extra=lambda s: s['cause'] == 'Human')))
    S.append(dict(label='S8 years >= 2010', **rt.fit(df, d, 'M2', extra=lambda s: s['fire_year'] >= 2010)))
S.append(dict(label='S5 B+ (prior 10-yr scars)', **rt.fit(df, 'Bp', 'M2')))
R['sensitivity'] = S
P = json.load(open('/home/claude/p1/results.json'))
leaves, bad = [0], []


def cmp(a, b, path):
    if isinstance(a, dict):
        for k in a:
            cmp(a[k], b.get(k, '<missing>') if isinstance(b, dict) else '<missing>', path + '.' + k)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            bad.append(path); return
        for i, (x, y) in enumerate(zip(a, b)):
            cmp(x, y, f'{path}[{i}]')
    else:
        leaves[0] += 1
        if a != b:
            bad.append(f'{path}: {a!r} vs {b!r}')


for key in ['primary', 'H3_escaped', 'H4_containment', 'sensitivity']:
    cmp(P[key], R[key], key)
model = dict(run_test_sha256=sha(os.path.join(HERE, 'run_test.py')), outputs_compared=sum(len(P[k]) for k in ['primary', 'H3_escaped', 'H4_containment', 'sensitivity']),
             values_compared=leaves[0], mismatches=bad, identical=(not bad))
E = dict(run_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), build=build, model=model)
json.dump(E, open(os.path.join(HERE, 'EQUIVALENCE.json'), 'w'), indent=1)
print(json.dumps(E, indent=1))
sys.exit(0 if build['identical'] and model['identical'] else 1)
