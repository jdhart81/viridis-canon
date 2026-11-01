#!/usr/bin/env python3
"""P1 confirmatory replication (NE Washington): the pre-registered test.
Frozen with PREREGISTRATION_P1C_NEWA_v1.4.md; SHA-256 hashes in FREEZE.json.

Derived from the pilot's run_test_dev1.py (pilot frozen 2026-10-20 20:13 ET; its Deviation 1 guard included).
The model arithmetic (design, ols_cluster, cluster_bootstrap, sample, fit, containment_perm) is unchanged for
default arguments: replaying the pilot's call sequence reproduces every number in the pilot's results.json.
Changes, all fixed before any confirmatory outcome exists on disk:
  1. ONE primary test: H2 under definition B (mapped barriers), model M2R (M2 plus fixed effects for 40 km regions;
     plan v1.3), decided on the interval beta +- C2 * max(two-way SE by year and 20 km block, year-only SE). C2 is a
     critical value calibrated by simulation on this design: the largest 95th percentile of |T| over the screened
     error models (calibrate_critical.py -> CALIBRATION.json) and the stress set of plan v1.4 (calibrate_stress.py ->
     CRITICAL_VALUES.json, which holds the final values read here).
     Two other readings are reported, not decisive:
     the pilot's rule (beta +- 1.96 * year-only SE) and plan v1.1's rule (beta +- t(0.975, G-1) * max SE).
  2. Disjointness assertion: no fod_id from the pilot predictor table may appear in this sample.
  3. Interpretive outputs that never change the decision: a small-telescopes reading (Simonsohn 2015) using the
     calibrated one-sided value C1, and the difference from / pooling with the pilot (independent and stacked).
  4. The pilot's Deviation 1 not-estimable guard is built in (NOT ESTIMABLE when n <= k or < 2 year clusters).
  5. S9: the two-way clustered interval, part of the primary decision and reported for A50.
  6. S10 / S10b: drop ignitions inside the pilot's compute box, and additionally inside the pilot-fetched MTBS
     perimeters (EXPOSURE_LISTS.json).
  7. Stacked model with the pilot (separate coefficients; clustered across both regions by year and two-way),
     so the difference test and the pooled estimate account for the 33 shared years.
  8. Leave-one-year-out stability of the primary estimate and decision.
  9. S11: M2 without the fuel-group term (LANDFIRE 2024 fuels partly reflect post-fire updates).
 10. S12: drop possible cross-boundary duplicate reports (EXPOSURE_LISTS.json).
 11. verify_inputs(): refuses to run unless FREEZE.json is the publicly verified copy, the running script and its
     inputs match FREEZE.json, and outcomes.csv matches OUTCOME_FETCH.json; --synthetic only with all-synthetic rows.
 12. The regional terms (plan v1.3): add_regions() labels each ignition with its 40 km EPSG:5070 cell
     (x // 40000, y // 40000), the 2 x 2 parent of the 20 km clustering block. The primary model, the stacked model,
     S10, S10b, S11, S12 and leave-one-year-out use M2R. The pilot's functions with default arguments are untouched.
 13. S13: the pilot's exact model M2 on this region, with its own calibrated critical value C2_M2 (not decisive).
 14. Plan v1.4: the critical values come from CRITICAL_VALUES.json; verify_inputs() checks the very file that was
     loaded, refuses cleanly when the fetch record is missing, and S9 (A50, M2) shows C2 for reference only.
Inputs : predictors_blind.csv, outcomes.csv, EXPOSURE_LISTS.json, CRITICAL_VALUES.json, CALIBRATION.json, and the pilot's
         predictors_blind.csv, outcomes.csv and p1_config.json (all hashed in FREEZE.json).
Outputs: results.json
Models (M1 and M2 exactly as in the pilot):
  Y = log10(fire_size acres)
  M1: Y ~ log10(Aenc) + erc_pct + C(fuel_group) + C(cause) + C(month) + C(year)
  M2: M1 + log10(rho + 0.001) + log10(road_dist_m + 30)
  M2R (the confirmatory primary, not in the pilot): M2 + C(region40)
Decision (registered, on M2R): SUPPORTED iff beta - C2 * max(SE_twoway, SE_year) > 0; CONTRADICTED iff
beta + C2 * max(...) < 0; otherwise NOT SUPPORTED; NOT ESTIMABLE iff n <= k or fewer than 2 year clusters.
"""
import json
import math
import sys
import numpy as np
import pandas as pd

RNG = np.random.default_rng(20261020)

# Pilot primary estimate (B, M2), from p1/results.json, fixed before the freeze.
PILOT = dict(beta=0.06317647448409425, se=0.027318251774805232, n=2677, clusters=33)
# The pilot under this plan's primary model M2R (pilot Deviation 3, p1/DEVIATION_3.json; exploratory): its slope and
# max(two-way, year-only) SE. Used for the independent comparison; the stacked model recomputes both from the data.
PILOT_M2R = dict(beta=0.07913393598337634, se=0.026581989430332444, n=2677, clusters=33)
Z = 1.96                                     # the pilot's critical value (pilot-rule reading, secondary intervals)
PHI_INV_033 = -0.4399131656732338            # standard normal quantile at 0.33
BETA33 = PILOT['se'] * (Z + PHI_INV_033)     # effect the pilot had 33% power to detect with its own rule
# Registered critical values for T = beta / max(SE_twoway, SE_year), set by simulation before the freeze
# (calibrate_critical.py -> CALIBRATION.json, then calibrate_stress.py -> CRITICAL_VALUES.json, read here;
# verify_inputs() checks the file actually loaded against FREEZE.json):
#   C2: two-sided 5%, the decision interval beta +- C2 * max SE;  C1: one-sided 5%, the NOT REPLICATED bound.


def _load_critical():
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CRITICAL_VALUES.json')
    if os.path.exists(p):
        c = json.load(open(p))
        return p, c.get('C2'), c.get('C1'), c.get('C2_M2'), c.get('C1_M2')
    return None, None, None, None, None


CRIT_PATH, C2, C1, C2_M2, C1_M2 = _load_critical()   # C2, C1: primary (M2R); C2_M2, C1_M2: S13 (the pilot's model M2)
PILOT_DIR = '../p1/'
PILOT_TABLE = PILOT_DIR + 'predictors_blind.csv'
FES = ('fuel_group', 'cause', 'month', 'fire_year')
REGION_M = 40000                                  # plan v1.3: 40 km regions, the 2 x 2 parents of the 20 km blocks
FES_R = FES + ('region40',)                       # M2R = M2 + C(region40)


def add_regions(df):
    """Copy of df with region40, the ignition's 40 km EPSG:5070 cell (x // 40000, y // 40000)."""
    return df.assign(region40=(df['x'] // REGION_M).astype(int).astype(str) + '_' + (df['y'] // REGION_M).astype(int).astype(str))


def t_crit(df_, q=0.975):
    """Student-t quantile for the few-cluster correction (Cameron & Miller 2015): df = G - 1."""
    from scipy.stats import t
    return float(t.ppf(q, df_))


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def design(df, aenc_col, rho_col, model, fes=FES):
    cols = {'log10_Aenc': np.log10(df[aenc_col].values), 'erc_pct': df['erc_pct'].values}
    if model == 'M2':
        cols['log10_rho'] = np.log10(df[rho_col].values + 0.001)
        cols['log10_roaddist'] = np.log10(df['road_dist_m'].values + 30.0)
    X = pd.DataFrame(cols, index=df.index)
    for fe in fes:
        d = pd.get_dummies(df[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        X = pd.concat([X, d], axis=1)
    X.insert(0, 'const', 1.0)
    X = X.loc[:, X.std(ddof=0).gt(0) | (X.columns == 'const')]
    return X


def ols_cluster(X, y, groups):
    Xv = X.values.astype(float); yv = y.astype(float)
    XtX_inv = np.linalg.pinv(Xv.T @ Xv)
    b = XtX_inv @ Xv.T @ yv
    e = yv - Xv @ b
    n, k = Xv.shape
    G = pd.unique(groups); meat = np.zeros((k, k))
    if n - k <= 0 or len(G) < 2:          # pilot Deviation 1: not estimable
        nanv = pd.Series(np.nan, index=X.columns)
        return nanv, nanv, len(G), n
    for g in G:
        idx = groups == g
        s = Xv[idx].T @ e[idx]
        meat += np.outer(s, s)
    c = len(G) / (len(G) - 1) * (n - 1) / (n - k)
    V = c * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))
    return pd.Series(b, index=X.columns), pd.Series(se, index=X.columns), len(G), n


def cluster_bootstrap(X, y, groups, col, reps=2000):
    G = pd.unique(groups); idx_by = {g: np.nonzero(groups == g)[0] for g in G}
    j = list(X.columns).index(col); out = []
    Xv = X.values.astype(float)
    for _ in range(reps):
        pick = RNG.choice(G, size=len(G), replace=True)
        ii = np.concatenate([idx_by[g] for g in pick])
        b = np.linalg.lstsq(Xv[ii], y[ii], rcond=None)[0]
        out.append(b[j])
    return np.percentile(out, [2.5, 97.5]).tolist()


def sample(df, defn, snap=False, include_censored=False, extra=None):
    a = f'Aenc_{defn}_snap' if snap else f'Aenc_{defn}'
    c = f'cens_{defn}_snap' if snap else f'cens_{defn}'
    s = df[df['fire_size'] > 0].copy()
    s = s[s['erc_pct'].notna() & s['month'].notna()]
    if not snap:
        s = s[~s[f'on_hold_{defn}'].astype(bool)]
    if not include_censored:
        s = s[~s[c].astype(bool)]
    s = s[s[a].notna() & (s[a] > 0)]
    if extra is not None:
        s = s[extra(s)]
    return s, a


def fit(df, defn, model, snap=False, include_censored=False, extra=None, boot=False, min_size=None, fes=FES):
    s, a = sample(df, defn, snap, include_censored, extra)
    if min_size is not None:
        s = s[s['fire_size'] >= min_size]
    rho = {'A50': 'rho_A50', 'A25': 'rho_A25', 'B': 'rho_B', 'Bp': 'rho_B'}[defn]
    X = design(s, a, rho, model, fes)
    if include_censored:
        X['censored'] = s[f'cens_{defn}'].astype(float).values
    y = np.log10(s['fire_size'].values)
    b, se, ng, n = ols_cluster(X, y, s['fire_year'].values)
    if not np.isfinite(b['log10_Aenc']):
        return dict(defn=defn, model=model, n=int(n), clusters=int(ng), k=int(X.shape[1]), not_estimable=True,
                    beta=None, se=None, ci95=[None, None])
    res = dict(defn=defn, model=model, n=int(n), clusters=int(ng), beta=float(b['log10_Aenc']),
               se=float(se['log10_Aenc']), ci95=[float(b['log10_Aenc'] - 1.96 * se['log10_Aenc']),
                                                 float(b['log10_Aenc'] + 1.96 * se['log10_Aenc'])])
    if model == 'M2':
        res['beta_log10_rho'] = float(b['log10_rho']); res['beta_log10_roaddist'] = float(b['log10_roaddist'])
    if boot:
        res['boot_ci95'] = cluster_bootstrap(X, y, s['fire_year'].values, 'log10_Aenc')
    return res


def decide_ci(lo, hi):
    return 'SUPPORTED' if lo > 0 else ('CONTRADICTED' if hi < 0 else 'NOT SUPPORTED')


def fit_twoway(df, defn, block_m=20000, extra=None, fes=FES, label='S9 two-way clustered (year x 20 km block)', crit=None):
    """S9: same M2 point estimate; SEs clustered by year (as registered) and two-way by year and 20 km block
    (Cameron, Gelbach & Miller 2011: V = V_year + V_block - V_year*block, each with the CR1 factor; if that
    variance is not positive, the larger one-way variance is used). The registered interval uses the larger of
    the two-way and year-only SEs with the calibrated critical value C2 (or crit, if given: S13 uses C2_M2)."""
    crit = C2 if crit is None else crit
    mname = 'M2R' if 'region40' in fes else 'M2'
    s, a = sample(df, defn, extra=extra)
    rho = {'A50': 'rho_A50', 'A25': 'rho_A25', 'B': 'rho_B', 'Bp': 'rho_B'}[defn]
    X = design(s, a, rho, 'M2', fes); y = np.log10(s['fire_size'].values)
    Xv = X.values.astype(float); n, k = Xv.shape
    if n - k <= 0 or s['fire_year'].nunique() < 2:
        return dict(defn=defn, model=mname, label=label, not_estimable=True, beta=None, se=None, ci95=[None, None])
    XtX_inv = np.linalg.pinv(Xv.T @ Xv); b = XtX_inv @ Xv.T @ y; e = y - Xv @ b
    j = list(X.columns).index('log10_Aenc')
    year = s['fire_year'].astype(str).values
    block = ((s['x'] // block_m).astype(int).astype(str) + '_' + (s['y'] // block_m).astype(int).astype(str)).values

    def V(groups):
        G = pd.unique(groups); meat = np.zeros((k, k))
        for g in G:
            idx = groups == g; sc = Xv[idx].T @ e[idx]; meat += np.outer(sc, sc)
        return (len(G) / (len(G) - 1) * (n - 1) / (n - k)) * XtX_inv @ meat @ XtX_inv, len(G)
    Vy, Gy = V(year); Vb, Gb = V(block); Vyb, _ = V(np.char.add(np.char.add(year, '|'), block))
    var2 = (Vy + Vb - Vyb)[j, j]
    fallback = bool(var2 <= 0)
    if fallback:
        var2 = max(Vy[j, j], Vb[j, j])
    se2, sey = float(np.sqrt(var2)), float(np.sqrt(Vy[j, j]))
    sem = max(se2, sey); bj = float(b[j])
    dof = int(min(Gy, Gb) - 1); tc = t_crit(dof)
    return dict(defn=defn, model=mname, fes=list(fes), label=label, n=int(n), year_clusters=int(Gy), block_clusters=int(Gb),
                beta=bj, se=se2, ci95=[bj - Z * se2, bj + Z * se2], se_year_only=sey,
                se_block_only=float(np.sqrt(Vb[j, j])), nonpositive_fallback=fallback, se_max=sem,
                crit=crit, interval_registered=[bj - crit * sem, bj + crit * sem],
                reading_registered=decide_ci(bj - crit * sem, bj + crit * sem),
                dof=dof, t_crit=tc, interval_v11_t=[bj - tc * sem, bj + tc * sem],
                reading_v11_t=decide_ci(bj - tc * sem, bj + tc * sem))


def containment_perm(df, defn, reps=10000):
    s, a = sample(df, defn)
    s = s[s['fire_size'] >= 10]
    obs = float((s['fire_size'] <= s[a]).mean())
    strata = s['fire_year'].astype(str) + '|' + s['fuel_group'].astype(str)
    A = s[a].values; F = s['fire_size'].values
    groups = [np.nonzero((strata == k).values)[0] for k in strata.unique()]
    null = np.empty(reps)
    for i in range(reps):
        Ap = A.copy()
        for g in groups:
            if len(g) > 1:
                Ap[g] = A[RNG.permutation(g)]
        null[i] = (F <= Ap).mean()
    return dict(defn=defn, n=int(len(s)), observed=obs, null_mean=float(null.mean()),
                p_one_sided=float((np.sum(null >= obs) + 1) / (reps + 1)))


def decide(r):
    """Decision on a result's CR1 95% CI (by year). Used for the pilot-rule reading and for secondary models."""
    if r.get('not_estimable') or r['ci95'][0] is None:
        return 'NOT ESTIMABLE'
    return decide_ci(r['ci95'][0], r['ci95'][1])


def decide_primary(tw):
    """The registered P1C decision: the interval beta +- C2 * max(two-way SE, year-only SE)."""
    if tw.get('not_estimable'):
        return 'NOT ESTIMABLE'
    return decide_ci(tw['interval_registered'][0], tw['interval_registered'][1])


def stacked_with_pilot(df_conf, block_m=20000, fes=FES_R):
    """Item 7: pilot and confirmatory B samples under the primary model (M2R) in one block-diagonal OLS (every
    coefficient region-specific,
    so the point estimates equal the two separate fits), clustered across both regions by year, and two-way by
    year and 20 km block. Returns the joint covariance of the two compartment slopes, the difference test and the
    GLS-pooled estimate under each clustering."""
    dp = pd.read_csv(PILOT_TABLE).merge(pd.read_csv(PILOT_DIR + 'outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
    blocks, ys, years, blks, js = [], [], [], [], []
    off = 0
    for d in (add_regions(dp), add_regions(df_conf)):
        s, a = sample(d, 'B'); X = design(s, a, 'rho_B', 'M2', fes)
        blocks.append(X.values.astype(float)); ys.append(np.log10(s['fire_size'].values))
        years.append(s['fire_year'].astype(str).values)
        blks.append(((s['x'] // block_m).astype(int).astype(str) + '_' + (s['y'] // block_m).astype(int).astype(str)).values)
        js.append(off + list(X.columns).index('log10_Aenc')); off += X.shape[1]
    n1 = len(ys[0])
    Xs = np.zeros((n1 + len(ys[1]), off)); Xs[:n1, :blocks[0].shape[1]] = blocks[0]; Xs[n1:, blocks[0].shape[1]:] = blocks[1]
    y = np.concatenate(ys); yr = np.concatenate(years); bl = np.concatenate(blks)
    n, k = Xs.shape
    XtX_inv = np.linalg.pinv(Xs.T @ Xs); b = XtX_inv @ Xs.T @ y; e = y - Xs @ b
    A = XtX_inv[:, js]                                   # only the two slope rows are needed
    W = (Xs @ A) * e[:, None]                            # per-observation influence on the two slopes

    def V(groups):
        codes, inv = np.unique(groups, return_inverse=True)
        sums = np.zeros((len(codes), 2)); np.add.at(sums, inv, W)
        return (len(codes) / (len(codes) - 1) * (n - 1) / (n - k)) * sums.T @ sums
    Vy = V(yr); Vb = V(bl); Vyb = V(np.char.add(np.char.add(yr, '|'), bl)); V2 = Vy + Vb - Vyb
    bp, bc = float(b[js[0]]), float(b[js[1]])

    def summarize(S, label):
        if np.any(np.linalg.eigvalsh(S) <= 0):
            return dict(clustering=label, not_positive_definite=True)
        w = np.linalg.solve(S, np.ones(2)); den = float(w.sum())
        pooled = float(w @ np.array([bp, bc]) / den); pse = math.sqrt(1 / den)
        dz = (bc - bp) / math.sqrt(S[0, 0] + S[1, 1] - 2 * S[0, 1])
        return dict(clustering=label, se_pilot=math.sqrt(S[0, 0]), se_conf=math.sqrt(S[1, 1]), cov=float(S[0, 1]),
                    corr=float(S[0, 1] / math.sqrt(S[0, 0] * S[1, 1])),
                    difference=dict(diff=bc - bp, z=dz, p_two_sided=2 * (1 - phi(abs(dz)))),
                    pooled_gls=dict(beta=pooled, se=pse, ci95=[pooled - Z * pse, pooled + Z * pse]))
    return dict(model='M2R' if 'region40' in fes else 'M2', beta_pilot=bp, beta_conf=bc, year=summarize(Vy, 'year'),
                twoway=summarize(V2, 'year x 20 km block'))


def leave_one_year_out(df):
    """Item 8: the primary estimate and the registered decision with each year removed in turn."""
    base = decide_primary(fit_twoway(df, 'B', fes=FES_R))
    out = []
    for yr in sorted(df['fire_year'].dropna().unique()):
        r = fit_twoway(df, 'B', extra=lambda s, yr=yr: s['fire_year'] != yr, fes=FES_R, label=f'LOYO {int(yr)}')
        out.append(dict(year=int(yr), beta=r['beta'], interval_registered=r.get('interval_registered'), decision=decide_primary(r)))
    betas = [o['beta'] for o in out if o['beta'] is not None]
    return dict(min_beta=min(betas), max_beta=max(betas),
                years_changing_decision=[o['year'] for o in out if o['decision'] != base], per_year=out)


def interpret(prim, decision, stacked):
    """Pre-specified reading of the primary result against the pilot. Never changes the decision."""
    if decision == 'NOT ESTIMABLE':
        return dict(reading='NOT ESTIMABLE')
    b, se = prim['beta'], prim['se_max']
    upper90 = b + C1 * se
    P = PILOT_M2R                                      # the pilot under the same model as the primary (Deviation 3)
    d = b - P['beta']; sd = math.sqrt(se ** 2 + P['se'] ** 2)
    w1, w2 = 1 / P['se'] ** 2, 1 / se ** 2
    pooled = (w1 * P['beta'] + w2 * b) / (w1 + w2); pooled_se = 1 / math.sqrt(w1 + w2)
    small_telescopes_reject = upper90 < BETA33
    if decision == 'SUPPORTED':
        reading = 'REPLICATED'
    elif decision == 'CONTRADICTED':
        reading = 'CONTRADICTED (effect of the opposite sign)'
    elif small_telescopes_reject:
        reading = 'NOT REPLICATED (effect significantly smaller than the pilot could detect)'
    else:
        reading = 'INCONCLUSIVE (neither supported nor shown smaller than the pilot could detect)'
    return dict(reading=reading,
                per_tenfold_multiplier=10 ** b,
                small_telescopes=dict(beta33=BETA33, upper90=upper90, reject_beta_ge_beta33=bool(small_telescopes_reject)),
                independent=dict(note=('pilot under M2R (Deviation 3); assumes the two estimates are independent '
                                       '(they share 33 years); see stacked'), pilot_beta_M2R=P['beta'],
                                 diff=d, z=d / sd, p_two_sided=2 * (1 - phi(abs(d / sd))),
                                 pilot_beta_inside_registered_interval=bool(prim['interval_registered'][0] <= P['beta'] <= prim['interval_registered'][1]),
                                 pooled_fixed_effect=dict(beta=pooled, se=pooled_se,
                                                          ci95=[pooled - Z * pooled_se, pooled + Z * pooled_se])),
                stacked_with_pilot=stacked)


def verify_inputs():
    """Refuse to run on inputs that differ from the frozen ones, or on outcomes that are not the fetched ones.
    Uses explicit exits (not assert, which python -O strips)."""
    import hashlib
    import os
    sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
    for p in ('OUTCOME_FETCH.json', 'FREEZE.json', 'outcomes.csv'):
        if not os.path.exists(p):
            sys.exit(f'VERIFY FAIL: {p} is missing')
    if CRIT_PATH is None:
        sys.exit('VERIFY FAIL: CRITICAL_VALUES.json is missing')
    rec = json.load(open('OUTCOME_FETCH.json'))
    if sha('FREEZE.json') != rec['g2_downloads']['FREEZE.json']['sha256']:
        sys.exit('VERIFY FAIL: FREEZE.json differs from the public copy verified at fetch time')
    F = json.load(open('FREEZE.json'))['sha256']
    if sha(__file__) != F['run_test.py']:
        sys.exit('VERIFY FAIL: the running run_test.py differs from the frozen file')
    if sha(CRIT_PATH) != F['CRITICAL_VALUES.json']:
        sys.exit('VERIFY FAIL: the critical values loaded differ from the frozen CRITICAL_VALUES.json')
    for p in ['predictors_blind.csv', 'EXPOSURE_LISTS.json', 'CALIBRATION.json', 'CRITICAL_VALUES.json', PILOT_TABLE,
              PILOT_DIR + 'outcomes.csv', PILOT_DIR + 'p1_config.json']:
        if sha(p) != F[p]:
            sys.exit(f'VERIFY FAIL: {p} differs from the frozen file')
    if sha('outcomes.csv') != rec['outcomes_sha256']:
        sys.exit('VERIFY FAIL: outcomes.csv is not the file fetch_outcomes.py wrote')
    if None in (C2, C1, C2_M2, C1_M2):
        sys.exit('VERIFY FAIL: critical values missing')


def main():
    synthetic = '--synthetic' in sys.argv
    out = pd.read_csv('outcomes.csv')
    if synthetic:                                # validate_synthetic.py: synthetic outcomes only
        if not (out['fire_size_class'] == 'SYN').all():
            sys.exit('REFUSED: --synthetic is allowed only when every outcome row is synthetic (size class SYN)')
    else:
        verify_inputs()
    pred = pd.read_csv('predictors_blind.csv')
    pilot_ids = set(pd.read_csv(PILOT_TABLE, usecols=['fod_id'])['fod_id'].astype('int64'))
    overlap = pilot_ids & set(pred['fod_id'].astype('int64'))
    if overlap:
        sys.exit(f'REFUSED: {len(overlap)} pilot ignitions in the confirmatory table')
    EX = json.load(open('EXPOSURE_LISTS.json'))
    df = add_regions(pred.merge(out[['fod_id', 'fire_size']], on='fod_id', how='left'))
    R = {'n_ignitions': int(len(pred)), 'n_with_outcome': int(df['fire_size'].notna().sum()), 'pilot_overlap': 0,
         'critical_values': dict(C2=C2, C1=C1, C2_M2=C2_M2, C1_M2=C1_M2), 'inputs_verified': not synthetic,
         'synthetic': synthetic}
    R['n_missing_outcome'] = R['n_ignitions'] - R['n_with_outcome']
    # PRIMARY (the only confirmatory test): H2, B, M2R; interval beta +- C2 * max(two-way SE, year-only SE)
    py = fit(df, 'B', 'M2', boot=True, fes=FES_R)       # year-only CR1 and bootstrap, as the pilot's estimator, on M2R
    tw = fit_twoway(df, 'B', fes=FES_R, label='primary (B, M2R)')
    if py['defn'] != 'B' or py['model'] != 'M2':
        sys.exit('INTERNAL: primary model mismatch')
    if not tw.get('not_estimable') and (abs(tw['beta'] - py['beta']) > 1e-12 or abs(tw['se_year_only'] - py['se']) > 1e-12):
        sys.exit('INTERNAL: two-way fit and year-only fit disagree')
    R['primary_test'] = dict(hypothesis='H2', defn='B', model='M2R', n=py['n'], year_clusters=py['clusters'],
                             block_clusters=tw.get('block_clusters'), regions_40km=int(df.loc[sample(df, 'B')[0].index, 'region40'].nunique()),
                             beta=py['beta'], se_year=py['se'],
                             se_twoway=tw.get('se'), se_max=tw.get('se_max'), C2=C2,
                             interval_registered=tw.get('interval_registered'),
                             interval_v11_t=tw.get('interval_v11_t'), dof=tw.get('dof'), t_crit=tw.get('t_crit'),
                             ci95_year=py['ci95'], boot_ci95=py.get('boot_ci95'),
                             beta_log10_rho=py.get('beta_log10_rho'), beta_log10_roaddist=py.get('beta_log10_roaddist'))
    R['decision'] = decide_primary(tw)
    R['reading_v11_rule'] = tw.get('reading_v11_t')     # t x max SE (plan v1.1): reported, not decisive
    R['decision_pilot_rule'] = decide(py)               # 1.96 x year-only SE, as in the pilot: reported, not decisive
    stacked = stacked_with_pilot(df) if R['decision'] != 'NOT ESTIMABLE' else None
    R['interpretation'] = interpret(R['primary_test'], R['decision'], stacked)
    # SECONDARY: everything the pilot reported, unchanged, then the confirmatory additions
    R['secondary_models'] = [fit(df, 'B', 'M1'), fit(df, 'A50', 'M1'), fit(df, 'A50', 'M2', boot=True),
                             fit(df, 'A25', 'M1'), fit(df, 'A25', 'M2')]
    R['secondary_decisions_not_confirmatory'] = {f"{r['defn']}_{r['model']}": decide(r) for r in R['secondary_models']}
    R['H3_escaped'] = [fit(df, d, 'M2', min_size=10) for d in ['A50', 'B']]
    R['H4_containment'] = [containment_perm(df, d) for d in ['A50', 'B']]
    S = []
    for d in ['A50', 'B']:
        S.append(dict(label='S1 snap on-holdable', **fit(df, d, 'M2', snap=True)))
        S.append(dict(label='S2 include censored', **fit(df, d, 'M2', include_censored=True)))
        S.append(dict(label='S3 drop coarse coords', **fit(df, d, 'M2', extra=lambda s: ~s['coarse_coords'].astype(bool))))
        S.append(dict(label='S6a natural cause (lightning)', **fit(df, d, 'M2', extra=lambda s: s['cause'] == 'Natural')))
        S.append(dict(label='S6b human cause', **fit(df, d, 'M2', extra=lambda s: s['cause'] == 'Human')))
        S.append(dict(label='S8 years >= 2010', **fit(df, d, 'M2', extra=lambda s: s['fire_year'] >= 2010)))
    S.append(dict(label='S5 B+ (prior 10-yr scars)', **fit(df, 'Bp', 'M2')))
    S.append(fit_twoway(df, 'A50', label='S9 two-way clustered (year x 20 km block), A50 under M2; the interval uses C2 '
                                          'for reference only (C2 is calibrated for B under M2R)'))
    pc = json.load(open(PILOT_DIR + 'p1_config.json'))['compute_box_5070']
    in_box = lambda s: (s['x'] >= pc[0]) & (s['x'] <= pc[2]) & (s['y'] >= pc[1]) & (s['y'] <= pc[3])
    in_perims = set(EX['s10b']['fod_ids_inside_perimeters']); dups = set(EX['s12']['fod_ids'])
    S.append(fit_twoway(df, 'B', extra=lambda s: ~in_box(s), fes=FES_R, label="S10 outside the pilot's compute box"))
    S.append(fit_twoway(df, 'B', extra=lambda s: ~in_box(s) & ~s['fod_id'].isin(in_perims), fes=FES_R,
                        label='S10b outside the pilot box and the pilot-fetched MTBS perimeters'))
    S.append(fit_twoway(df, 'B', fes=('cause', 'month', 'fire_year', 'region40'), label='S11 no fuel-group term'))
    S.append(fit_twoway(df, 'B', extra=lambda s: ~s['fod_id'].isin(dups), fes=FES_R,
                        label='S12 without possible cross-boundary duplicates'))
    S.append(fit_twoway(df, 'B', fes=FES, crit=C2_M2,
                        label="S13 the pilot's model M2 (no regional terms), with its own calibrated critical value C2_M2"))
    for r in S:
        if 'interval_registered' in r:
            r['decision_registered_rule'] = decide_primary(r)
    R['sensitivity'] = S
    R['leave_one_year_out'] = leave_one_year_out(df)
    json.dump(R, open('results.json', 'w'), indent=1)
    print('PRIMARY (B, M2R, C2 x max-SE interval):', R['decision'], '|', R['interpretation']['reading'],
          '| v1.1-rule reading:', R['reading_v11_rule'], '| pilot-rule reading:', R['decision_pilot_rule'])
    print(json.dumps(R['primary_test']))


if __name__ == '__main__':
    main()
