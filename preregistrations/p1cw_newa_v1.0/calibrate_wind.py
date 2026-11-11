#!/usr/bin/env python3
"""P1C-W: calibrate the critical values for the wind-interaction statistic on the blind P1C design, and simulate power.
T_W = gamma / max(SE_twoway, SE_year), gamma = coefficient on Lc x z_w in M2R-W:
  M2R-W = M2R + z_w + Lc*z_w + Lc*cause + z_w*cause      (Lc = log10 Aenc - 3.63; z_w = standardized W3)
Error models (null, gamma = 0), each 4,000 replicates on THIS design:
  - the 81 models of the P1C screened family (CALIBRATION.json: iid, block, block+field, retained blocks and fields)
  - the 52 retained P1C stress models (CRITICAL_VALUES.json: anisotropic, long-range exact fields, compartment effects)
  - new S-D: discovery-date random effects (all ignitions on one date share an error), screened on the PILOT's B/M2
    residuals by one-way ANOVA share between dates, as S-C was (pilot outcomes are public and were used in P1C)
  - new S-H: heteroskedastic noise, sd multiplied by exp(a*z_w/2), a in {0.25, 0.5}; unscreened (conservative)
C_W = max(2.53, max q95 |T_W| rounded up); C1_W = max(2.08, max q90 |T_W| rounded up).
No confirmatory outcome is read (asserted). Usage: python3 calibrate_wind.py WIND_CSV OUT_JSON [workers]"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
import sys, json, math, time, hashlib, importlib.util, multiprocessing as mp
import numpy as np, pandas as pd
WIND, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'p1c'); sys.path.insert(0, HERE); os.chdir(HERE)
import simcal  # noqa
spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec); spec.loader.exec_module(rt)
assert not os.path.exists(os.path.join(HERE, 'outcomes.csv'))
NW = int(sys.argv[3]) if len(sys.argv) > 3 else 3
L_CENTER = 3.63
t0 = time.time()

class DesignW:
    """simcal.Design arithmetic (year CR1, two-way CR1 year x 20 km block) for a chosen column of a given design."""
    def __init__(self, X, target, s, block_m=20000):
        self.cols = list(X.columns); self.Xv = X.values.astype(float); self.n, self.k = self.Xv.shape
        self.XtX_inv = np.linalg.pinv(self.Xv.T @ self.Xv); self.j = self.cols.index(target)
        self.h = self.Xv @ self.XtX_inv[:, self.j]
        g = s['fire_year'].astype(str).values
        blk = ((s['x'] // block_m).astype(int).astype(str) + '_' + (s['y'] // block_m).astype(int).astype(str)).values
        _, self.yinv = np.unique(g, return_inverse=True); _, self.binv = np.unique(blk, return_inverse=True)
        _, self.ybinv = np.unique(np.char.add(np.char.add(g, '|'), blk), return_inverse=True)
        self.nblocks = int(self.binv.max() + 1)
        c = lambda inv: (inv.max() + 1) / inv.max() * (self.n - 1) / (self.n - self.k)
        self.cY, self.cB, self.cYB = c(self.yinv), c(self.binv), c(self.ybinv)
    stats = simcal.Design.stats

def build(pred, wind, wcol='W3'):
    pred = rt.add_regions(pred).merge(wind[['fod_id', wcol]], on='fod_id', how='left')
    s, a = rt.sample(pred.assign(fire_size=1.0), 'B', extra=lambda d: d[wcol].notna())
    X = rt.design(s, a, 'rho_B', 'M2', rt.FES_R)
    w = s[wcol].values; z = (w - w.mean()) / w.std(); Lc = np.log10(s[a].values) - L_CENTER
    X['wind_z'] = z; X['L_x_w'] = Lc * z
    for lvl in sorted(s['cause'].astype(str).unique()):
        if lvl == 'Human':
            continue
        d = (s['cause'].astype(str) == lvl).values.astype(float); tag = 'Natural' if lvl == 'Natural' else 'Missing'
        X[f'L_x_{tag}'] = Lc * d; X[f'w_x_{tag}'] = z * d
    return s, a, X, z, Lc, float(w.mean()), float(w.std())

pred = pd.read_csv(os.path.join(HERE, 'predictors_blind.csv')); wind = pd.read_csv(WIND)
s, a, X, Z, LC, WMEAN, WSD = build(pred, wind)
D = DesignW(X, 'L_x_w', s)
XS, YS = s['x'].values.astype(float), s['y'].values.astype(float)
ES = s['erc_pct'].fillna(0.5).values
labC = np.load(os.path.join(HERE, 'compartments_static.npz'))['labB']; _, INV_C = np.unique(labC[s['row'].values, s['col'].values], return_inverse=True)
_, INV_D = np.unique((s['fire_year'].astype(int) * 1000 + s['doy'].astype(int)).values, return_inverse=True)
CAL = json.load(open('CALIBRATION.json')); CV = json.load(open('CRITICAL_VALUES.json'))
TOT = CAL['models']['iid']['var_total']

# pilot screen for date effects (pilot residuals under B/M2; no wind involved)
e_p = simcal.pilot_residuals(rt, '../p1/')[0]
dp = pd.read_csv('../p1/predictors_blind.csv').merge(pd.read_csv('../p1/outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
sp, _ = rt.sample(dp, 'B'); Xp = rt.design(sp, _, 'rho_B', 'M2').values.astype(float); Mp = np.linalg.pinv(Xp)
_, INV_DP = np.unique((sp['fire_year'].astype(int) * 1000 + sp['doy'].astype(int)).values, return_inverse=True)
OBS_DATE = simcal.anova_share_groups(e_p, INV_DP)

def screen_date(share, reps=1000, seed=7_000_000):
    rng = np.random.default_rng(seed + int(share * 1000)); est = []; nd = INV_DP.max() + 1
    for _ in range(reps):
        yy = rng.normal(0, math.sqrt(TOT * (1 - share)), len(e_p)) + rng.normal(0, math.sqrt(TOT * share), nd)[INV_DP]
        est.append(simcal.anova_share_groups(yy - Xp @ (Mp @ yy), INV_DP))
    q = np.quantile(est, [0.025, 0.5, 0.975]); return dict(q025_q50_q975=q.tolist(), retained=bool(q[0] <= OBS_DATE <= q[2]))

def errors_iter(m, reps, seed0):
    """Yield null error vectors for model spec m (one per replicate)."""
    kind = m['kind']
    if kind == 'cal':           # screened family: iid / block / field via simcal conventions
        vb = TOT * m.get('block_share', 0.0); vf = TOT * m.get('field_share', 0.0); vn = TOT - vb - vf
        F = simcal.Field(m['range_km'], XS, YS) if vf > 0 else None
        for r in range(reps):
            rng = np.random.default_rng(seed0 + r); y = rng.normal(0, math.sqrt(vn), D.n)
            if vb > 0: y = y + rng.normal(0, math.sqrt(vb), D.nblocks)[D.binv]
            if F is not None: y = y + math.sqrt(vf) * F.draw(rng)
            yield y
    elif kind in ('field', 'comp'):
        errs = simcal.StressErrors(dict(m, var_total=TOT), XS, YS, INV_C if kind == 'comp' else None)
        for b0 in range(0, reps, 200):
            E = errs.batch([seed0 + r for r in range(b0, min(reps, b0 + 200))])
            for e in E: yield e
    elif kind == 'date':
        nd = INV_D.max() + 1
        for r in range(reps):
            rng = np.random.default_rng(seed0 + r)
            yield rng.normal(0, math.sqrt(TOT * (1 - m['share'])), D.n) + rng.normal(0, math.sqrt(TOT * m['share']), nd)[INV_D]
    elif kind == 'het':
        sd = math.sqrt(TOT) * np.exp(m['a'] * Z / 2); sd = sd * math.sqrt(TOT) / math.sqrt((sd ** 2).mean())
        for r in range(reps):
            yield np.random.default_rng(seed0 + r).normal(size=D.n) * sd

def null_job(arg):
    k, m = arg; T = np.empty(REPS)
    for r, e in enumerate(errors_iter(m, REPS, 50_000_000 + 100_000 * k)):
        g, sy, s2, sm = D.stats(0.5 * ES + e); T[r] = g / sm
    a_ = np.abs(T)
    return m['name'], dict(m, q90_absT=float(np.quantile(a_, .90)), q95_absT=float(np.quantile(a_, .95)),
                           false_call_share_at_2_53=float(np.mean(a_ > 2.53)))

def power_job(arg):
    name, m, gamma, reps = arg; base = 0.053 * (LC + L_CENTER); calls = {'SUPPORTED': 0, 'CONTRADICTED': 0, 'INCONCLUSIVE': 0, 'WIND-INVARIANT': 0}
    G = []
    for r, e in enumerate(errors_iter(m, reps, 90_000_000 + int(abs(gamma) * 1e5) + (7 if m['kind'] != 'cal' else 0))):
        g, sy, s2, sm = D.stats(base + 0.5 * ES + gamma * LC * Z + e); G.append(g)
        lo, hi = g - CW['C_W'] * sm, g + CW['C_W'] * sm; lo1, hi1 = g - CW['C1_W'] * sm, g + CW['C1_W'] * sm
        if hi < 0: calls['SUPPORTED'] += 1
        elif lo > 0: calls['CONTRADICTED'] += 1
        elif lo1 > -GMIN and hi1 < GMIN: calls['WIND-INVARIANT'] += 1
        else: calls['INCONCLUSIVE'] += 1
    return name, gamma, {k: v / reps for k, v in calls.items()}, float(np.mean(G)), float(np.std(G))

GMIN = 0.0265
REPS = int(os.environ.get('P1CW_REPS', 4000)); PREPS = int(os.environ.get('P1CW_PREPS', 2000)); ONLY = os.environ.get('P1CW_ONLY')
if __name__ == '__main__':
    ctx = mp.get_context('fork')
    models = []
    for name, v in CAL['models'].items():
        models.append(dict(name='cal:' + name, kind='cal', **{kk: v[kk] for kk in ('block_share', 'field_share', 'range_km') if kk in v}))
    for name, v in CV['stress_set']['models'].items():
        models.append(dict(name='stress:' + name, kind=v['kind'], share=v['share'], **({'rx_km': v['rx_km'], 'ry_km': v['ry_km']} if v['kind'] == 'field' else {})))
    if ONLY: models = [m for m in models if any(o in m['name'] for o in ONLY.split(','))]
    date_screens = {}
    for sh in (0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.15):
        date_screens[sh] = screen_date(sh)
        if date_screens[sh]['retained']:
            models.append(dict(name=f'date:s{sh:.3f}', kind='date', share=sh))
    for aa in (0.25, 0.5):
        models.append(dict(name=f'het:a{aa}', kind='het', a=aa))
    print(f'n={D.n} k={D.k} wind mean {WMEAN:.3f} sd {WSD:.3f}; pilot date share {OBS_DATE:.4f}; models {len(models)}', flush=True)
    res = {}
    with ctx.Pool(NW) as pool:
        for name, out in pool.imap_unordered(null_job, list(enumerate(models))):
            res[name] = out; print(f"{name:34s} q95 {out['q95_absT']:.3f} q90 {out['q90_absT']:.3f} ({time.time()-t0:.0f}s)", flush=True)
    ceil2 = lambda v: math.ceil(v * 100) / 100
    top95 = max(res, key=lambda k: res[k]['q95_absT']); top90 = max(res, key=lambda k: res[k]['q90_absT'])
    CW = dict(C_W=max(2.53, ceil2(res[top95]['q95_absT'])), C1_W=max(2.08, ceil2(res[top90]['q90_absT'])),
              binding_C_W=top95, binding_C1_W=top90, max_q95=res[top95]['q95_absT'], max_q90=res[top90]['q90_absT'])
    print(json.dumps(CW), flush=True)
    by = {m['name']: m for m in models}
    pjobs = [(nm, by[nm], g, 2000) for nm in dict.fromkeys(('cal:iid', top95)) for g in (0.0, -0.02, -0.03, -0.04, -0.053)]
    pjobs = [(a_, b_, c_, PREPS) for a_, b_, c_, _ in pjobs]
    power = {}
    with ctx.Pool(NW) as pool:
        for nm, g, calls, gm, gs in pool.imap_unordered(power_job, pjobs):
            power.setdefault(nm, {})[str(g)] = dict(calls, mean_gamma_hat=gm, sd_gamma_hat=gs)
            print('power', nm, g, calls, round(gm, 4), round(gs, 4), flush=True)
    out = dict(design=dict(n=D.n, k=D.k, wind_column='W3', wind_mean=WMEAN, wind_sd=WSD, L_center=L_CENTER, columns_added=[c for c in D.cols if c.startswith(('wind_z', 'L_x_', 'w_x_'))]),
               pilot_date_share=OBS_DATE, date_screens={str(k): v for k, v in date_screens.items()}, models=res, critical=CW, gamma_min=GMIN, power=power,
               code_sha256={f: hashlib.sha256(open(p, 'rb').read()).hexdigest() for f, p in (('calibrate_wind.py', os.path.abspath(__file__)), ('simcal.py', 'simcal.py'), ('run_test.py', 'run_test.py'), ('wind', WIND))},
               seconds=round(time.time() - t0))
    json.dump(out, open(OUT, 'w'), indent=1); print('done', out['seconds'], 's')
