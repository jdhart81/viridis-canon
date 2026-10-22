#!/usr/bin/env python3
"""Check that CALIBRATION.json, produced by the v1.3 code, is reproduced exactly by the current (v1.4) code.

v1.4 changed run_test.py and simcal.py only by additions that calibrate_critical.py does not use. The v1.3 versions of
both files are frozen in history_v1.3/. This check re-runs three of the calibration's models with the current code,
from their registered seeds (5,000,000 + 100,000 k for the k-th model), and requires every statistic to match
CALIBRATION.json bit for bit: the reference iid model, the largest retained block model, and the binding field.
Writes CALIBRATION_REPRO.json. No outcome is used. Usage: python3 check_calibration_repro.py   (about 3 minutes)"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
import hashlib, importlib.util, json, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import simcal  # noqa: E402

spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
sha = lambda p: hashlib.sha256(open(os.path.join(HERE, p), 'rb').read()).hexdigest()
CAL = json.load(open(os.path.join(HERE, 'CALIBRATION.json')))
for f in ('run_test.py', 'simcal.py', 'calibrate_critical.py'):
    assert sha(os.path.join('history_v1.3', f)) == CAL['code_sha256'][f], f'CALIBRATION.json was not produced by the frozen v1.3 {f}'
pred = rt.add_regions(pd.read_csv(os.path.join(HERE, 'predictors_blind.csv')))
DR, D0 = simcal.Design(rt, pred, fes=rt.FES_R), simcal.Design(rt, pred, fes=rt.FES)
xs, ys = pred['x'].values[DR.pos].astype(float), pred['y'].values[DR.pos].astype(float)
es = pred['erc_pct'].fillna(0.5).values[DR.pos]
names = list(CAL['models'])
blocks = [n for n in names if n.startswith('block_s')]
check = ['iid', max(blocks, key=lambda n: CAL['models'][n]['block_share']), CAL['binding_model_C2']]
out = dict(models={}, code_sha256={f: sha(f) for f in ('run_test.py', 'simcal.py', 'check_calibration_repro.py', 'CALIBRATION.json')},
           v13_code_sha256={f: CAL['code_sha256'][f] for f in ('run_test.py', 'simcal.py', 'calibrate_critical.py')})
ok = True
for name in check:
    k = names.index(name); mod = CAL['models'][name]
    model = {kk: mod[kk] for kk in ('var_total', 'block_share', 'field_share', 'range_km') if kk in mod}
    TmR, TyR, Tm0, Ty0 = simcal.null_t_pair(DR, D0, xs, ys, es, model, mod['reps'], 5_000_000 + 100_000 * k)
    row = {}
    for key, Tm in (('M2R', TmR), ('M2', Tm0)):
        a = np.abs(Tm)
        got = dict(q90_absT=float(np.quantile(a, 0.90)), q95_absT=float(np.quantile(a, 0.95)))
        exp = {q: mod[key][q] for q in got}
        row[key] = dict(recomputed=got, recorded=exp, identical=got == exp)
        ok = ok and got == exp
    out['models'][name] = row
    print(name, {key: row[key]['identical'] for key in row}, row['M2R']['recomputed'], flush=True)
out['all_identical'] = bool(ok)
json.dump(out, open(os.path.join(HERE, 'CALIBRATION_REPRO.json'), 'w'), indent=1)
print('all identical:', ok)
sys.exit(0 if ok else 1)
