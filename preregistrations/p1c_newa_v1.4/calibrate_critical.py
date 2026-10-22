#!/usr/bin/env python3
"""Calibrate the decision rule's critical values by simulation (plan v1.3). Writes CALIBRATION.json.

Statistic: T = beta / max(SE_twoway, SE_year) for the B compartment slope, under the primary model M2R (M2 plus fixed
effects for 40 km regions), and under the pilot's model M2 for the secondary reading S13. Both come from the same draws.
Step 1, which spatial error models are credible (simcal.PilotPlausibility). A correlogram fitted to residuals is
  biased toward short ranges, so the pilot's plug-in fit (share 0.053, range 11.2 km) is not taken at face value.
  Every persistent exponential field on a grid of correlated shares x ranges is simulated on the PILOT design
  (200 replicates, residualized on the pilot's B/M2 design, correlogram refitted exactly as for the real residuals);
  a model is RETAINED if the pilot's observed fitted share and range both lie inside the central 95% of its fits.
  The grid reaches share 0.60 and range 180 km, so that the retained set is closed wherever the pilot can close it.
  20 km block effects are screened the same way, on a grid of block shares, against the pilot's ANOVA block share.
Step 2, null outcomes on THIS region's blind design, 4,000 replicates per model, for: every retained field model;
  every retained block model; the pilot's plug-in block model (one-way ANOVA on its residuals); block effects plus a
  field (fitted jointly to cross-year pairs); and iid errors (reference only).
Registered values, the MAXIMUM over the spatial models (iid excluded), rounded UP to 2 decimals:
  C2 (M2R), C2_M2 (M2) = 95th percentile of |T| (two-sided 5%: the decision interval beta +- C2 * max SE)
  C1 (M2R), C1_M2 (M2) = 90th percentile of |T| (one-sided 5%: the bound used by the NOT REPLICATED reading)
Step 3, the pilot re-read: the reference models and the three binding models of each statistic, on the PILOT's own
  design, 5,000 replicates (pilot T: 2.31 under M2; 2.98 under M2R, pilot Deviation 3).
No confirmatory outcome is used anywhere. Two worker processes. Usage: python3 calibrate_critical.py (about 1 hour)"""
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
SHARES = [0.03, 0.045, 0.06, 0.075, 0.09, 0.11, 0.13, 0.16, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
BLOCK_SHARES = [0.03, 0.045, 0.06, 0.075, 0.09, 0.11, 0.13, 0.16, 0.20]
RANGES = [6.0, 11.0, 16.0, 22.0, 30.0, 45.0, 60.0, 90.0, 120.0, 180.0]
T_OBS = {'M2': 0.06317647448409425 / 0.027318251774805232,       # pilot beta / max(two-way 0.0234, year 0.0273)
         'M2R': 0.07913393598337634 / 0.026581989430332444}      # pilot Deviation 3: beta / max(two-way 0.0252, year 0.0266)
PP = simcal.PilotPlausibility(rt)
pred = rt.add_regions(pd.read_csv(os.path.join(HERE, 'predictors_blind.csv')))
pp = rt.add_regions(pd.read_csv('/home/claude/p1/predictors_blind.csv'))
DES = {}
for tag, df in (('conf', pred), ('pilot', pp)):
    DR, D0 = simcal.Design(rt, df, fes=rt.FES_R), simcal.Design(rt, df, fes=rt.FES)
    xs, ys = df['x'].values[DR.pos].astype(float), df['y'].values[DR.pos].astype(float)
    DES[tag] = (DR, D0, xs, ys, df['erc_pct'].fillna(0.5).values[DR.pos])
MODELS = {}


def plaus_job(arg):
    share, range_km, seed = arg
    return PP.check(share, range_km, 200, seed)


def block_job(arg):
    share, seed = arg
    return PP.check_block(share, 200, seed)


def null_job(arg):
    tag, name, reps, seed = arg
    DR, D0, xs, ys, es = DES[tag]
    TmR, TyR, Tm0, Ty0 = simcal.null_t_pair(DR, D0, xs, ys, es, MODELS[name], reps, seed)
    return name, TmR, TyR, Tm0, Ty0


def summarize(name, TmR, TyR, Tm0, Ty0, DR):
    out = dict(MODELS[name], reps=len(TmR))
    for key, Tm, Ty in (('M2R', TmR, TyR), ('M2', Tm0, Ty0)):
        a = np.abs(Tm)
        out[key] = dict(q90_absT=float(np.quantile(a, 0.90)), q95_absT=float(np.quantile(a, 0.95)),
                        false_call_share_v11_rule=float(np.mean(a > DR.t)),
                        false_call_share_pilot_rule=float(np.mean(np.abs(Ty) > 1.96)))
    return out


if __name__ == '__main__':
    ctx = mp.get_context('fork')
    args = [(s, r, 1_000_000 + 1000 * (len(RANGES) * a + b)) for a, s in enumerate(SHARES) for b, r in enumerate(RANGES)]
    with ctx.Pool(2) as pool:
        grid = []
        for g in pool.imap(plaus_job, args):
            grid.append(g)
            print(f"plausibility share {g['share']:.3f} range {g['range_km']:5.1f}: retained={g['retained']} fitted share q50 "
                  f"{g['fitted_share_q025_q50_q975'][1]:.3f}, range q50 {g['fitted_range_q025_q50_q975'][1]:.1f}  ({time.time() - t0:.0f}s)", flush=True)
    with ctx.Pool(2) as pool:
        block_grid = list(pool.imap(block_job, [(s, 2_000_000 + 1000 * i) for i, s in enumerate(BLOCK_SHARES)]))
    for g in block_grid:
        print(f"block plausibility share {g['block_share']:.3f}: retained={g['retained']} estimate q50 "
              f"{g['estimated_share_q025_q50_q975'][1]:.3f}  ({time.time() - t0:.0f}s)", flush=True)
    closure = {}
    for r in RANGES:
        kept = [g['share'] for g in grid if g['range_km'] == r and g['retained']]
        closure[f'{r:.0f}'] = dict(max_retained_share=max(kept) if kept else None,
                                   closed=bool(kept) and max(kept) < max(SHARES))
    cg = simcal.pilot_correlogram(rt)
    vc = simcal.pilot_variance_components(rt)
    TOT = cg['total_var']
    b_be, s_be, r_be = simcal.fit_block_plus_exponential(cg['cross_same'], cg['cross_diff'])
    MODELS.update({'iid': dict(var_total=TOT, range_km=10.0),
                   'block': dict(var_total=TOT, block_share=vc['var_block'] / (vc['var_block'] + vc['var_within']), range_km=10.0),
                   'block_exp': dict(var_total=TOT, block_share=b_be, field_share=s_be, range_km=r_be)})
    for g in block_grid:
        if g['retained']:
            MODELS[f"block_s{g['block_share']:.3f}"] = dict(var_total=TOT, block_share=g['block_share'], range_km=10.0)
    for g in grid:
        if g['retained']:
            MODELS[f"field_s{g['share']:.3f}_r{g['range_km']:.0f}"] = dict(var_total=TOT, field_share=g['share'], range_km=g['range_km'])
    SPATIAL = [m for m in MODELS if m != 'iid']
    DR = DES['conf'][0]
    res = {'grid': grid, 'grid_axes': dict(shares=SHARES, ranges_km=RANGES), 'closure_by_range_km': closure,
           'block_grid': block_grid, 'pilot_observed_block_share': PP.obs_block,
           'pilot_observed_fit': dict(share=PP.obs[0], range_km=PP.obs[1]), 'models': {},
           'confirmatory_design': dict(n=DR.n, k_M2R=DR.k, k_M2=DES['conf'][1].k, blocks=DR.nblocks, dof=DR.dof, t_crit=DR.t)}
    sims = {}
    with ctx.Pool(2) as pool:            # forked after MODELS is complete
        jobs = [('conf', name, 4000, 5_000_000 + 100_000 * k) for k, name in enumerate(MODELS)]
        for name, TmR, TyR, Tm0, Ty0 in pool.imap(null_job, jobs):
            sims[name] = (TmR, Tm0)
            res['models'][name] = summarize(name, TmR, TyR, Tm0, Ty0, DR)
            print(f"  {name}: q95|T| M2R {res['models'][name]['M2R']['q95_absT']:.3f}  M2 {res['models'][name]['M2']['q95_absT']:.3f}"
                  f"  ({time.time() - t0:.0f}s)", flush=True)
    ceil2 = lambda v: math.ceil(v * 100) / 100
    for key, c2, c1 in (('M2R', 'C2', 'C1'), ('M2', 'C2_M2', 'C1_M2')):
        res[c2] = ceil2(max(res['models'][m][key]['q95_absT'] for m in SPATIAL))
        res[c1] = ceil2(max(res['models'][m][key]['q90_absT'] for m in SPATIAL))
        res['binding_model_' + c2] = max(SPATIAL, key=lambda m: res['models'][m][key]['q95_absT'])
        res['binding_model_' + c1] = max(SPATIAL, key=lambda m: res['models'][m][key]['q90_absT'])
        for name in MODELS:
            Tm = sims[name][0 if key == 'M2R' else 1]
            res['models'][name][key]['false_call_share_C2_rule'] = float(np.mean(np.abs(Tm) > res[c2]))
    # pilot re-read on its own design: references plus the three binding models of each statistic
    pm = ['iid', 'block', 'block_exp']
    for key in ('M2R', 'M2'):
        for m in sorted(SPATIAL, key=lambda m: -res['models'][m][key]['q95_absT'])[:3]:
            if m not in pm:
                pm.append(m)
    DRp = DES['pilot'][0]
    res['pilot_reread'] = dict(T_obs=T_OBS, design=dict(n=DRp.n, blocks=DRp.nblocks, dof=DRp.dof, k_M2R=DRp.k), models={})
    with ctx.Pool(2) as pool:
        jobs = [('pilot', name, 5000, 60_000_000 + 100_000 * k) for k, name in enumerate(pm)]
        for name, TmR, TyR, Tm0, Ty0 in pool.imap(null_job, jobs):
            row = {}
            for key, Tm in (('M2R', TmR), ('M2', Tm0)):
                a = np.abs(Tm)
                row[key] = dict(p_two_sided=float(np.mean(a >= T_OBS[key])), c_5pct=float(np.quantile(a, 0.95)),
                                c_2p5pct=float(np.quantile(a, 0.975)))
            res['pilot_reread']['models'][name] = dict(row, reps=len(TmR))
            print(f"  pilot {name}: M2R p {row['M2R']['p_two_sided']:.4f} c5% {row['M2R']['c_5pct']:.3f} | "
                  f"M2 p {row['M2']['p_two_sided']:.4f} c5% {row['M2']['c_5pct']:.3f}  ({time.time() - t0:.0f}s)", flush=True)
    res['correlogram'] = {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in cg.items()}
    res['fits'] = dict(block_exp=dict(block_share=b_be, field_share=s_be, range_km=r_be), anova=vc)
    res['code_sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest()
                          for f in ('run_test.py', 'simcal.py', 'calibrate_critical.py', 'predictors_blind.csv')}
    res['seconds'] = round(time.time() - t0)
    json.dump(res, open(os.path.join(HERE, 'CALIBRATION.json'), 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('C2', 'C1', 'C2_M2', 'C1_M2', 'binding_model_C2', 'binding_model_C1',
                                          'binding_model_C2_M2', 'binding_model_C1_M2', 'closure_by_range_km')}, indent=1))
    print('retained field models:', sum(1 for m in MODELS if m.startswith('field')), 'of', len(grid),
          '| retained block models:', sum(1 for m in MODELS if m.startswith('block_s')), 'of', len(block_grid))
    print('seconds', res['seconds'])
