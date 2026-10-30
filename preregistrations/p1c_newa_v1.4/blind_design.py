#!/usr/bin/env python3
"""Blind design summary for the confirmatory pre-registration (plan v1.3). Reads predictors only; no outcome exists.

Writes BLIND_DESIGN.json with:
  - sample sizes per definition after every predictor-based filter (the only outcome-based filter,
    fire_size > 0, removed no record in the pilot);
  - predicted standard error and power for the primary test (B, M2R), from the pilot's residual SD and
    design effect applied to THIS region's blind design matrix, checked by a Monte Carlo on that matrix; and the
    simulated power of the registered rule under the reference and binding error models (two worker processes);
  - how many usable confirmatory ignitions share a B compartment with a pilot ignition (landscape overlap).
"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
import importlib.util, json, math, multiprocessing as mp
import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location('rt', 'run_test.py'); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
CFG = json.load(open('p1_config.json'))
# Pilot quantities for B, M2 (from the pilot's own data and the frozen pilot code; see the prereg, section 4)
PILOT = dict(n=2677, beta=0.06317647448409425, se_cr1=0.027318251774805232, se_iid=0.02567459347212416,
             deff=1.064018863802679, sigma=1.0797053862182389, sd_resid_log10Aenc=0.8127884182365132)

pred = pd.read_csv('predictors_blind.csv')
assert not ({'fire_size', 'fire_size_class'} & set(pred.columns))
pred = rt.add_regions(pred)
df = pred.assign(fire_size=1.0)      # placeholder so sample() applies only predictor-based filters
D = dict(n_table=int(len(pred)), years=[int(pred.fire_year.min()), int(pred.fire_year.max())],
         cause={str(k): int(v) for k, v in pred['cause'].value_counts(dropna=False).items()},
         erc_available=round(float(pred['erc_pct'].notna().mean()), 4), usable={})
for d in ['A50', 'A25', 'B', 'Bp']:
    s, a = rt.sample(df, d)
    D['usable'][d] = dict(n=int(len(s)), log10_Aenc_acres_q10_q50_q90=[round(float(v), 2) for v in np.log10(s[a]).quantile([.1, .5, .9])])

# Power for the primary test (M2R)
s, a = rt.sample(df, 'B'); X = rt.design(s, a, 'rho_B', 'M2', rt.FES_R)
others = [c for c in X.columns if c != 'log10_Aenc']
Z = X[others].values.astype(float); xa = X['log10_Aenc'].values
resid = xa - Z @ np.linalg.lstsq(Z, xa, rcond=None)[0]
n, sdres = len(s), float(resid.std(ddof=0))
X0 = rt.design(s, a, 'rho_B', 'M2')                 # the pilot's model M2 (S13), for comparison
Z0 = X0[[c for c in X0.columns if c != 'log10_Aenc']].values.astype(float)
sdres_M2 = float((xa - Z0 @ np.linalg.lstsq(Z0, xa, rcond=None)[0]).std(ddof=0))


def power(beta, se):
    """Analytic reference only (the pilot's 1.96 rule, iid errors): P(beta_hat - 1.96 * se > 0) at true slope beta.
    The registered rule's power is the simulated one below."""
    return rt.phi(beta / se - 1.96)


scen = {'base: pilot residual SD and design effect': (PILOT['sigma'], PILOT['deff']),
        'pessimistic: residual SD +15%, design effect 1.5': (PILOT['sigma'] * 1.15, 1.5)}
betas = {'pilot under M2R 0.079': rt.PILOT_M2R['beta'], 'pilot estimate 0.063': PILOT['beta'],
         'beta33 0.0415 (small-telescopes benchmark)': rt.BETA33, 'half the pilot estimate 0.032': PILOT['beta'] / 2}
D['power_primary'] = dict(model='M2R', n_usable_B=n, k_columns=int(X.shape[1]), regions_40km=int(s['region40'].nunique()),
                          sd_resid_log10Aenc=sdres, sd_resid_log10Aenc_M2=sdres_M2, k_columns_M2=int(X0.shape[1]),
                          pilot_sd_resid_log10Aenc=PILOT['sd_resid_log10Aenc'], scenarios={})
for name, (sig, deff) in scen.items():
    se = deff * sig / (math.sqrt(n) * sdres)
    D['power_primary']['scenarios'][name] = dict(predicted_se=se, power={k: round(power(b, se), 3) for k, b in betas.items()})

# Simulated power of the REGISTERED rule (beta +- C2 * max SE, M2R) on this design, under the reference error models
# and the binding models of CRITICAL_VALUES.json (plan v1.4: from CALIBRATION.json or from the stress set):
# P(SUPPORTED) at each slope, 4,000 replicates per cell; and P(NOT REPLICATED) under a true null, registered reading
# (C2, C1 with max SE) against the pilot's rule (1.96 / 1.645 with year SE)
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import simcal
CAL = json.load(open('CALIBRATION.json'))
CV = json.load(open('CRITICAL_VALUES.json'))
assert (rt.C2, rt.C1, rt.C2_M2) == (CV['C2'], CV['C1'], CV['C2_M2']), 'run_test.py critical values differ from CRITICAL_VALUES.json'
Dd = simcal.Design(rt, pred, fes=rt.FES_R); es = pred['erc_pct'].fillna(0.5).values[Dd.pos]
D0 = simcal.Design(rt, pred, fes=rt.FES)            # S13: the pilot's model M2 with its own critical value C2_M2
xs, ys = pred['x'].values[Dd.pos].astype(float), pred['y'].values[Dd.pos].astype(float)
_labC = np.load('compartments_static.npz')['labB']
_sB, _ = rt.sample(df, 'B')
_, INV_C = np.unique(_labC[_sB['row'].values, _sB['col'].values], return_inverse=True)
PM = ['calibration:iid', 'calibration:block', 'calibration:block_exp']
for m in (CV['binding_model_C2'], CV['binding_model_C1']):
    if m not in PM:
        PM.append(m)


def _stats(D, name, reps, seed, beta):
    src, n = name.split(':', 1)
    if src == 'calibration':
        mod = {kk: CAL['models'][n][kk] for kk in ('var_total', 'block_share', 'field_share', 'range_km') if kk in CAL['models'][n]}
        return simcal.sim_stats(D, xs, ys, es, mod, reps, seed, beta=beta)
    mod = CV['stress_set']['models'][n]
    errs = simcal.StressErrors(mod, xs, ys, INV_C if mod['kind'] == 'comp' else None)
    return simcal.sim_stats_stress(D, es, errs, reps, seed, beta=beta)


def _power_job(arg):
    mi, name, bi, k, b = arg
    Bh, SY, SM = _stats(Dd, name, 4000, 30_000_000 + 1_000_000 * mi + 10_000 * bi, b)
    return name, k, float(np.mean(Bh - rt.C2 * SM > 0))


def _power_m2_job(arg):
    mi, name, bi, k, b = arg
    Bh, SY, SM = _stats(D0, name, 4000, 50_000_000 + 1_000_000 * mi + 10_000 * bi, b)
    return name, k, float(np.mean(Bh - rt.C2_M2 * SM > 0))


def _null_job(arg):
    mi, name = arg
    Bh, SY, SM = _stats(Dd, name, 4000, 40_000_000 + 1_000_000 * mi, 0.0)
    reg = np.mean((np.abs(Bh) <= rt.C2 * SM) & (Bh + rt.C1 * SM < rt.BETA33))
    pil = np.mean((np.abs(Bh) <= 1.96 * SY) & (Bh + 1.6448536269514722 * SY < rt.BETA33))
    return name, dict(registered=float(reg), pilot_rule=float(pil))


if __name__ == '__main__':
    with mp.get_context('fork').Pool(2) as pool:
        sim = {name: {} for name in PM}
        for name, k, v in pool.imap(_power_job, [(mi, name, bi, k, b) for mi, name in enumerate(PM) for bi, (k, b) in enumerate(betas.items())]):
            sim[name][k] = v
        notrep = dict(pool.imap(_null_job, list(enumerate(PM))))
        PM0 = ['calibration:iid', CV['binding_model_C2_M2']]
        sim0 = {name: {} for name in PM0}
        for name, k, v in pool.imap(_power_m2_job, [(mi, name, bi, k, b) for mi, name in enumerate(PM0) for bi, (k, b) in enumerate(betas.items())]):
            sim0[name][k] = v
    D['power_primary']['simulated_registered_rule'] = dict(reps=4000, C2=rt.C2, models=PM, power_P_SUPPORTED=sim)
    D['power_primary']['p_not_replicated_under_null'] = dict(reps=4000, by_model=notrep)
    D['power_s13_pilot_model_M2'] = dict(reps=4000, C2_M2=rt.C2_M2, models=PM0, power_P_SUPPORTED=sim0)

    # S10 sample: usable B ignitions outside the pilot's compute box (where the pilot's MTBS fetch reached)
    pc = json.load(open('../p1/p1_config.json'))['compute_box_5070']
    inside = (s['x'] >= pc[0]) & (s['x'] <= pc[2]) & (s['y'] >= pc[1]) & (s['y'] <= pc[3])
    EXL = json.load(open('EXPOSURE_LISTS.json'))
    D['s10b_usable_B'] = int((~inside & ~s['fod_id'].isin(set(EXL['s10b']['fod_ids_inside_perimeters']))).sum())
    D['s12_usable_B'] = int((~s['fod_id'].isin(set(EXL['s12']['fod_ids']))).sum())
    D['s10_outside_pilot_compute_box'] = dict(usable_B=int((~inside).sum()), usable_B_inside=int(inside.sum()),
                                              all_ignitions_inside=int(((pred.x >= pc[0]) & (pred.x <= pc[2]) & (pred.y >= pc[1]) & (pred.y <= pc[3])).sum()))

    # Monte Carlo on the real blind design (iid normal errors with the pilot residual SD): checks the analytic SE
    rng = np.random.default_rng(7)
    Xv = X.values.astype(float); XtX_inv = np.linalg.pinv(Xv.T @ Xv); j = list(X.columns).index('log10_Aenc')
    g = s['fire_year'].values; G = pd.unique(g); kk = Xv.shape[1]
    cfac = len(G) / (len(G) - 1) * (n - 1) / (n - kk)
    rej, ses = 0, []
    for _ in range(400):
        y = PILOT['beta'] * xa + rng.normal(0, PILOT['sigma'], n)
        b = XtX_inv @ Xv.T @ y; e = y - Xv @ b
        meat = np.zeros((kk, kk))
        for gg in G:
            sc = Xv[g == gg].T @ e[g == gg]; meat += np.outer(sc, sc)
        se = math.sqrt(cfac * (XtX_inv @ meat @ XtX_inv)[j, j]); ses.append(se)
        rej += (b[j] - 1.96 * se) > 0
    D['power_primary']['monte_carlo_iid'] = dict(reps=400, beta=PILOT['beta'], rejection_rate=rej / 400,
                                                 mean_cr1_se=float(np.mean(ses)),
                                                 analytic_iid_se=PILOT['sigma'] / (math.sqrt(n) * sdres))

    # Landscape overlap with the pilot: confirmatory B compartments that also contain a pilot ignition
    z = np.load('compartments_static.npz'); labB = z['labB']
    X0, Y0, X1, Y1 = CFG['compute_box_5070']; H, W = CFG['H'], CFG['W']
    pil = pd.read_csv(CFG['exclude_fod_ids_from'], usecols=['x', 'y'])
    r = ((Y1 - pil['y'].values) // 30).astype(int); c = ((pil['x'].values - X0) // 30).astype(int)
    ok = (r >= 0) & (r < H) & (c >= 0) & (c < W)
    shared = set(np.unique(labB[r[ok], c[ok]]).tolist()) - {0}
    sB, _ = rt.sample(df, 'B')
    k_conf = labB[sB['row'].values, sB['col'].values]
    D['landscape_overlap'] = dict(pilot_ignitions_inside_confirmatory_grid=int(ok.sum()),
                                  usable_B_ignitions_sharing_a_compartment_with_a_pilot_ignition=int(np.isin(k_conf, list(shared)).sum()),
                                  usable_B_ignitions=int(len(sB)))
    import hashlib
    D['code_sha256'] = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in ('run_test.py', 'simcal.py', 'blind_design.py', 'predictors_blind.csv', 'CALIBRATION.json', 'CRITICAL_VALUES.json')}
    json.dump(D, open('BLIND_DESIGN.json', 'w'), indent=1)
    print(json.dumps(D, indent=1))
