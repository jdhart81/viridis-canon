#!/usr/bin/env python3
"""Validate run_test.py on SYNTHETIC outcomes before the freeze (v7, for plan v1.4). No real outcome exists for
this region; the script asserts that before and after.

A. End to end through run_test.py (with --synthetic) on this region's real blind predictors, in a scratch directory:
     planted: log10 size = 0.30 * log10 Aenc_B + 0.5 * erc_pct + N(0, 1.08)  -> must be SUPPORTED
     null:    log10 size =                      0.5 * erc_pct + N(0, 1.08)  -> one fixed draw (seed 202), reported
B. Exactness: on a draw with block effects and a field, simcal's fast path equals run_test.fit_twoway for M2R (the
   primary) and for M2 (S13) to 1e-10.
C. Null check on FRESH seeds (not the calibration seeds), for the primary rule (M2R, beta +- C2 * max SE) and for
   S13's rule (M2, beta +- C2_M2 * max SE), with the final values of CRITICAL_VALUES.json, from the same draws:
   10,000 replicates under each statistic's binding model; 1,000 under every other model of CALIBRATION.json; 500
   under every other retained stress model (exact fields and compartment effects, plan v1.4).
PASS iff (A) planted is SUPPORTED, (B) holds, and (C) every fresh-seed false-call share is at most 0.058 at 10,000
replicates, 0.074 at 1,000 and 0.084 at 500 (5% plus 3.5 Monte Carlo standard errors). The pilot's rule and plan
v1.1's rule are reported alongside. Two worker processes.
History: v1.0 scored one null draw; v2 a 1,000-replicate iid calibration of the pilot's rule; v3 added
block-correlated errors and decided on t x max SE (plan v1.1); v4 checked a C2 calibrated on plug-in fits (plan v1.2);
v5-v6 check the critical values calibrated over every model the pilot cannot reject, for M2R and M2 (plan v1.3).
Usage: python3 validate_synthetic.py <scratch dir>
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
import hashlib, importlib.util, json, multiprocessing as mp, shutil, subprocess, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import simcal  # noqa: E402

assert not os.path.exists(os.path.join(HERE, 'outcomes.csv')), 'a real outcome file exists; stop'
SC = os.path.abspath(sys.argv[1]); os.makedirs(SC, exist_ok=True)
link = os.path.join(SC, 'p1')
if not os.path.islink(link):
    os.symlink('/home/claude/p1', link)            # so ../p1/... resolves for run_test.py
pred = pd.read_csv(os.path.join(HERE, 'predictors_blind.csv'))
la = np.log10(pred['Aenc_B'].where(pred['Aenc_B'] > 0, 1000.0)).values
erc = pred['erc_pct'].fillna(0.5).values
out = {}
for world, beta, seed in [('planted', 0.30, 101), ('null', 0.0, 202)]:
    d = os.path.join(SC, world); os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(HERE, 'run_test.py'), d)
    for f in ('predictors_blind.csv', 'EXPOSURE_LISTS.json', 'CALIBRATION.json', 'CRITICAL_VALUES.json'):
        dst = os.path.join(d, f)
        if not os.path.exists(dst):
            os.symlink(os.path.join(HERE, f), dst)
    rng = np.random.default_rng(seed)
    y = beta * la + 0.5 * erc + rng.normal(0, 1.08, len(pred))
    pd.DataFrame({'fod_id': pred['fod_id'], 'fire_size': 10 ** y, 'fire_size_class': 'SYN'}).to_csv(os.path.join(d, 'outcomes.csv'), index=False)
    subprocess.run([sys.executable, 'run_test.py', '--synthetic'], cwd=d, check=True, capture_output=True)
    R = json.load(open(os.path.join(d, 'results.json')))
    p = R['primary_test']
    out[world] = dict(planted_beta=beta, beta=round(p['beta'], 3), interval_registered=[round(v, 3) for v in p['interval_registered']],
                      ci95_year=[round(v, 3) for v in p['ci95_year']], n=p['n'], decision=R['decision'],
                      reading_v11_rule=R['reading_v11_rule'], decision_pilot_rule=R['decision_pilot_rule'],
                      reading=R['interpretation']['reading'], model=p['model'], regions_40km=p['regions_40km'])
    s13 = [r for r in R['sensitivity'] if r.get('label', '').startswith('S13')][0]
    out[world]['S13_pilot_model_M2'] = dict(beta=round(s13['beta'], 3), crit=s13['crit'], interval=[round(v, 3) for v in s13['interval_registered']],
                                            reading=s13['decision_registered_rule'])
assert not os.path.exists(os.path.join(HERE, 'outcomes.csv'))

spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
CAL = json.load(open(os.path.join(HERE, 'CALIBRATION.json')))
CV = json.load(open(os.path.join(HERE, 'CRITICAL_VALUES.json')))
assert (rt.C2, rt.C1, rt.C2_M2, rt.C1_M2) == (CV['C2'], CV['C1'], CV['C2_M2'], CV['C1_M2']), 'run_test.py critical values differ from CRITICAL_VALUES.json'
STRESS = CV['stress_set']['models']
predR = rt.add_regions(pred)
DR, D0 = simcal.Design(rt, predR, fes=rt.FES_R), simcal.Design(rt, predR, fes=rt.FES)
xs, ys = pred['x'].values[DR.pos].astype(float), pred['y'].values[DR.pos].astype(float)
es = erc[DR.pos]
# B. exactness: the fast path equals run_test.fit_twoway on one replicate with a field and block effects
m = CAL['models']['block_exp']
rng = np.random.default_rng(77)
F = simcal.Field(m['range_km'], xs, ys)
y = 0.5 * es + rng.normal(0, 1.0, DR.n) + rng.normal(0, 0.2, DR.nblocks)[DR.binv] + 0.2 * F.draw(rng)
yfull = np.zeros(len(pred)); yfull[DR.pos] = y
exact = {}
for D, fes in ((DR, rt.FES_R), (D0, rt.FES)):
    tw = rt.fit_twoway(predR.assign(fire_size=10 ** yfull), 'B', fes=fes); bj, sy, s2, sm = D.stats(y)
    err = max(abs(tw['beta'] - bj), abs(tw['se_year_only'] - sy), abs(tw['se'] - s2), abs(tw['se_max'] - sm))
    exact[D.model] = err
    assert err < 1e-10, (D.model, err)
out['exactness_max_abs_diff'] = exact
# C. fresh-seed null check
crit = {'M2R': rt.C2, 'M2': rt.C2_M2}
binding = {'M2R': CV['binding_model_C2'], 'M2': CV['binding_model_C2_M2']}      # 'stress:NAME' or 'calibration:NAME'
s_, _ = rt.sample(predR.assign(fire_size=1.0), 'B')
labC = np.load(os.path.join(HERE, 'compartments_static.npz'))['labB']
_, INV_C = np.unique(labC[s_['row'].values, s_['col'].values], return_inverse=True)
JOBS = [('calibration', n) for n in CAL['models']] + [('stress', n) for n in STRESS]
LIMIT = {10000: 0.058, 1000: 0.074, 500: 0.084}


def job(arg):
    k, (src, name) = arg
    seed = 70_000_000 + 1_000_000 * k
    if f'{src}:{name}' in binding.values():
        reps = 10000
    else:
        reps = 1000 if src == 'calibration' else 500
    if src == 'calibration':
        mod = CAL['models'][name]
        model = {kk: mod[kk] for kk in ('var_total', 'block_share', 'field_share', 'range_km') if kk in mod}
        TmR, TyR, Tm0, Ty0 = simcal.null_t_pair(DR, D0, xs, ys, es, model, reps, seed)
    else:
        mod = STRESS[name]
        errs = simcal.StressErrors(mod, xs, ys, INV_C if mod['kind'] == 'comp' else None)
        TmR, TyR, Tm0, Ty0 = simcal.null_t_pair_stress(DR, D0, es, errs, reps, seed)
    row = dict(source=src, reps=reps)
    for key, Tm, Ty in (('M2R', TmR, TyR), ('M2', Tm0, Ty0)):
        row[key] = dict(registered_rule=float(np.mean(np.abs(Tm) > crit[key])), v11_rule=float(np.mean(np.abs(Tm) > DR.t)),
                        pilot_rule=float(np.mean(np.abs(Ty) > 1.96)), threshold=LIMIT[reps])
        if src == 'stress':
            row[key]['calibration_share_final_rule'] = mod[key]['false_call_share_final_rule']
    return f'{src}:{name}', row


if __name__ == '__main__':
    checks = {}
    with mp.get_context('fork').Pool(2) as pool:
        for name, row in pool.imap(job, list(enumerate(JOBS))):
            checks[name] = row
    out['null_check_fresh_seeds'] = dict(C2=rt.C2, C1=rt.C1, C2_M2=rt.C2_M2, C1_M2=rt.C1_M2, binding_models=binding, models=checks)
    worst = {key: max(checks, key=lambda n: checks[n][key]['registered_rule'] - checks[n][key]['threshold']) for key in ('M2R', 'M2')}
    out['worst_margin'] = {key: dict(model=n, share=checks[n][key]['registered_rule'], threshold=checks[n][key]['threshold'])
                           for key, n in worst.items()}
    ok = out['planted']['decision'] == 'SUPPORTED' and all(
        checks[n][key]['registered_rule'] <= checks[n][key]['threshold'] for n in checks for key in ('M2R', 'M2'))
    out['pass_criterion'] = ('planted SUPPORTED; fast path exact for M2R and M2; and every fresh-seed false-call share of the '
                             'registered rules (M2R with C2, M2 with C2_M2) <= 0.058 at 10,000 replicates (binding models), '
                             '<= 0.074 at 1,000 (calibration models) and <= 0.084 at 500 (stress models)')
    out['pass'] = bool(ok)
    out['code_sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest()
                          for f in ('run_test.py', 'simcal.py', 'validate_synthetic.py', 'CALIBRATION.json', 'CRITICAL_VALUES.json')}
    json.dump(out, open(os.path.join(HERE, 'SYNTHETIC_VALIDATION.json'), 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('planted', 'null', 'exactness_max_abs_diff', 'worst_margin', 'pass')}, indent=1))
    sys.exit(0 if ok else 1)
