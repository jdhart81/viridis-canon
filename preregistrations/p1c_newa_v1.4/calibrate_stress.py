#!/usr/bin/env python3
"""Stress-test the decision rule beyond the registered calibration (plan v1.4). Writes CRITICAL_VALUES.json.

The fourth audit found structures outside the registered family (CALIBRATION.json) under which the rule over-calls.
This script adds them as a STRESS SET, fixed in history_v1.4_dev/DECISION_stress_set.md before any of it was
simulated, and sets the final critical values as the maxima over both sets.
  S-A  anisotropic exponential fields, corr = exp(-sqrt((dx/rx)^2 + (dy/ry)^2)), elongated north-south or east-west,
       (short, long) ranges (10, 60), (10, 120), (15, 90), (20, 180) km, shares 0.08-0.25        (48 candidates)
  S-L  long-range isotropic exponential fields, ranges 180-720 km, shares 0.3-0.9                 (35 candidates)
  S-C  compartment random effects (definition-B compartments), shares 0.02-0.15                    (7 candidates)
All fields are exact (Cholesky at the actual points; simcal.exact_chol). Screens on the PILOT design, 1,000
replicates: S-A and S-L by the registered statistic (exponential fit to the residual correlogram; retained if the
pilot's observed share and range both lie inside the central 95% of simulated fits); S-C by the one-way ANOVA share
between compartments of the pilot's M2 residuals. No directional screen (conservative). Every retained model:
4,000 null replicates on THIS region's blind design, for M2R (primary) and M2 (S13).
Final values: C2 = max(CALIBRATION C2, stress max q95 |T| under M2R rounded up to 2 decimals); C1 at the 90th
percentile; C2_M2, C1_M2 likewise for M2. No confirmatory outcome is used. Two worker processes.
Usage: python3 calibrate_stress.py   (about 45 minutes)"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('MKL_NUM_THREADS', '1')
import hashlib, importlib.util, json, math, multiprocessing as mp, sys, time
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import simcal  # noqa: E402

spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
assert not os.path.exists(os.path.join(HERE, 'outcomes.csv'))
t0 = time.time()
CAL = json.load(open(os.path.join(HERE, 'CALIBRATION.json')))
PP = simcal.PilotPlausibility(rt)
TOT = PP.TOT
# pilot compartments (same sample and order as PilotPlausibility)
dp = pd.read_csv('/home/claude/p1/predictors_blind.csv').merge(pd.read_csv('/home/claude/p1/outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
sp, _ = rt.sample(dp, 'B')
assert np.array_equal(sp['x'].values.astype(float), PP.x) and np.array_equal(sp['y'].values.astype(float), PP.y)
labP = np.load('/home/claude/p1/compartments_static.npz')['labB']
_, INV_P = np.unique(labP[sp['row'].values, sp['col'].values], return_inverse=True)
OBS_COMP = simcal.anova_share_groups(simcal.pilot_residuals(rt)[0], INV_P)
# this region's blind design and compartments
pred = rt.add_regions(pd.read_csv(os.path.join(HERE, 'predictors_blind.csv')))
DR, D0 = simcal.Design(rt, pred, fes=rt.FES_R), simcal.Design(rt, pred, fes=rt.FES)
s, _ = rt.sample(pred.assign(fire_size=1.0), 'B')
assert np.array_equal(pred.index.get_indexer(s.index), DR.pos)
labC = np.load(os.path.join(HERE, 'compartments_static.npz'))['labB']
_, INV_C = np.unique(labC[s['row'].values, s['col'].values], return_inverse=True)
XS, YS = s['x'].values.astype(float), s['y'].values.astype(float)
ES = pred['erc_pct'].fillna(0.5).values[DR.pos]

CAND = []
for orient in ('NS', 'EW'):
    for short, long_ in ((10, 60), (10, 120), (15, 90), (20, 180)):
        for sh in (0.08, 0.10, 0.13, 0.15, 0.20, 0.25):
            rx, ry = (short, long_) if orient == 'NS' else (long_, short)
            CAND.append(dict(name=f'aniso_{orient}_s{sh:.3f}_{short}x{long_}', family='S-A', kind='field', share=sh, rx_km=rx, ry_km=ry))
for r in (180, 240, 360, 480, 720):
    for sh in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        CAND.append(dict(name=f'long_s{sh:.3f}_r{r}', family='S-L', kind='field', share=sh, rx_km=r, ry_km=r))
for sh in (0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15):
    CAND.append(dict(name=f'comp_s{sh:.3f}', family='S-C', kind='comp', share=sh))


def screen_job(arg):
    i, c = arg
    sp_ = dict(c, var_total=TOT); seed = 3_000_000 + 10_000 * i
    errs = simcal.StressErrors(sp_, PP.x, PP.y, INV_P if c['kind'] == 'comp' else None)
    stats = []
    for b0 in range(0, 1000, 200):
        E = errs.batch([seed + r for r in range(b0, b0 + 200)])
        R = E - (PP.X @ (PP.M @ E.T)).T
        stats += [simcal.anova_share_groups(e, INV_P) for e in R] if c['kind'] == 'comp' else [PP.fit(e) for e in R]
    st = np.array(stats)
    if c['kind'] == 'comp':
        q = np.quantile(st, [0.025, 0.5, 0.975])
        return dict(c, statistic='compartment ANOVA share', observed=OBS_COMP, q025_q50_q975=q.tolist(),
                    retained=bool(q[0] <= OBS_COMP <= q[2]), reps=1000)
    qs = np.quantile(st[:, 0], [0.025, 0.5, 0.975]); qr = np.quantile(st[:, 1], [0.025, 0.5, 0.975])
    return dict(c, statistic='correlogram fit', observed=list(PP.obs), fitted_share_q025_q50_q975=qs.tolist(),
                fitted_range_q025_q50_q975=qr.tolist(), jitter=errs.jitter, reps=1000,
                retained=bool(qs[0] <= PP.obs[0] <= qs[2] and qr[0] <= PP.obs[1] <= qr[2]))


def null_job(arg):
    k, c = arg
    errs = simcal.StressErrors(dict(c, var_total=TOT), XS, YS, INV_C if c['kind'] == 'comp' else None)
    TmR, TyR, Tm0, Ty0 = simcal.null_t_pair_stress(DR, D0, ES, errs, 4000, 20_000_000 + 100_000 * k)
    out = dict(c, var_total=TOT, reps=4000, jitter_confirmatory=errs.jitter)
    for key, Tm, Ty in (('M2R', TmR, TyR), ('M2', Tm0, Ty0)):
        a = np.abs(Tm)
        out[key] = dict(q90_absT=float(np.quantile(a, 0.90)), q95_absT=float(np.quantile(a, 0.95)),
                        false_call_share_v11_rule=float(np.mean(a > DR.t)), false_call_share_pilot_rule=float(np.mean(np.abs(Ty) > 1.96)))
    return c['name'], out, TmR, Tm0


if __name__ == '__main__':
    ctx = mp.get_context('fork')
    print(f'observed pilot compartment ANOVA share (M2 residuals) {OBS_COMP:.4f}; pilot fit {PP.obs}', flush=True)
    with ctx.Pool(2) as pool:
        screens = []
        for g in pool.imap(screen_job, list(enumerate(CAND))):
            screens.append(g)
            print(f"screen {g['name']:28s} retained={g['retained']}  ({time.time() - t0:.0f}s)", flush=True)
    kept = [g for g in screens if g['retained']]
    keep_specs = [{kk: g[kk] for kk in ('name', 'family', 'kind', 'share') + (('rx_km', 'ry_km') if g['kind'] == 'field' else ())} for g in kept]
    models, T = {}, {}
    with ctx.Pool(2) as pool:
        for name, out, TmR, Tm0 in pool.imap(null_job, list(enumerate(keep_specs))):
            models[name] = out; T[name] = (TmR, Tm0)
            print(f"  {name:28s} q95|T| M2R {out['M2R']['q95_absT']:.3f}  M2 {out['M2']['q95_absT']:.3f}  ({time.time() - t0:.0f}s)", flush=True)
    ceil2 = lambda v: math.ceil(v * 100) / 100
    res = dict(stress_set=dict(definition='history_v1.4_dev/DECISION_stress_set.md', candidates=len(CAND), retained=len(kept),
                               observed_pilot_compartment_share=OBS_COMP, observed_pilot_fit=list(PP.obs), screens=screens, models=models),
               calibration=dict(sha256=hashlib.sha256(open(os.path.join(HERE, 'CALIBRATION.json'), 'rb').read()).hexdigest(),
                                **{k: CAL[k] for k in ('C2', 'C1', 'C2_M2', 'C1_M2', 'binding_model_C2', 'binding_model_C1',
                                                       'binding_model_C2_M2', 'binding_model_C1_M2')}))
    for key, c2, c1 in (('M2R', 'C2', 'C1'), ('M2', 'C2_M2', 'C1_M2')):
        for cv, q in ((c2, 'q95_absT'), (c1, 'q90_absT')):
            top = max(models, key=lambda m: models[m][key][q]) if models else None
            sv = ceil2(models[top][key][q]) if top else -1.0
            res[cv] = max(CAL[cv], sv)
            res['binding_model_' + cv] = ('stress:' + top) if sv > CAL[cv] else ('calibration:' + CAL['binding_model_' + cv])
            res['stress_max_' + cv] = dict(model=top, value=models[top][key][q] if top else None)
    for name in models:
        for key, crit in (('M2R', res['C2']), ('M2', res['C2_M2'])):
            models[name][key]['false_call_share_final_rule'] = float(np.mean(np.abs(T[name][0 if key == 'M2R' else 1]) > crit))
    res['code_sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest()
                          for f in ('run_test.py', 'simcal.py', 'calibrate_stress.py', 'CALIBRATION.json', 'predictors_blind.csv')}
    res['seconds'] = round(time.time() - t0)
    json.dump(res, open(os.path.join(HERE, 'CRITICAL_VALUES.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('C2', 'C1', 'C2_M2', 'C1_M2', 'binding_model_C2', 'binding_model_C1', 'binding_model_C2_M2',
                                          'binding_model_C1_M2', 'stress_max_C2', 'stress_max_C2_M2')}, indent=1))
    print('retained stress models', len(kept), 'of', len(CAND), '| seconds', res['seconds'])
