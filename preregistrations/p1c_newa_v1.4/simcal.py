#!/usr/bin/env python3
"""Fast simulations of the registered decision rules on a fixed blind design, for calibration and power.

Design() reproduces, for the B compartment slope under the primary model M2R (plan v1.3; or under M2 when
fes=rt.FES is passed), the exact arithmetic of run_test.fit (year-only CR1) and run_test.fit_twoway (two-way CR1 by
year and 20 km block, with the same fallback); callers check this against run_test on the first replicates. pilot_variance_components() estimates, from the PILOT's B/M2 residuals (pilot
outcomes are already known), how much residual variance is shared within 20 km blocks (one-way ANOVA, method of
moments). No confirmatory outcome is used anywhere."""
import math
import numpy as np


class Design:
    def __init__(self, rt, pred, block_m=20000, fes=None):
        self.fes = tuple(rt.FES_R if fes is None else fes)
        self.model = 'M2R' if 'region40' in self.fes else 'M2'
        if 'region40' not in pred.columns:
            pred = rt.add_regions(pred)
        s, a = rt.sample(pred.assign(fire_size=1.0), 'B')
        X = rt.design(s, a, 'rho_B', 'M2', self.fes)
        self.Xv = X.values.astype(float); self.n, self.k = self.Xv.shape
        self.XtX_inv = np.linalg.pinv(self.Xv.T @ self.Xv)
        self.h = self.Xv @ self.XtX_inv[:, list(X.columns).index('log10_Aenc')]
        self.pos = pred.index.get_indexer(s.index)
        self.la = np.log10(s[a].values)
        g = s['fire_year'].astype(str).values
        blk = ((s['x'] // block_m).astype(int).astype(str) + '_' + (s['y'] // block_m).astype(int).astype(str)).values
        _, self.yinv = np.unique(g, return_inverse=True)
        _, self.binv = np.unique(blk, return_inverse=True)
        _, self.ybinv = np.unique(np.char.add(np.char.add(g, '|'), blk), return_inverse=True)
        self.nblocks = int(self.binv.max() + 1)
        self.dof = int(min(self.yinv.max() + 1, self.nblocks) - 1)
        self.t = rt.t_crit(self.dof)
        c = lambda inv: (inv.max() + 1) / inv.max() * (self.n - 1) / (self.n - self.k)
        self.cY, self.cB, self.cYB = c(self.yinv), c(self.binv), c(self.ybinv)

    def stats(self, y):
        """beta, year-only SE, two-way SE, max SE for outcome vector y (sample rows, in sample order)."""
        bj = float(self.h @ y)
        e = y - self.Xv @ (self.XtX_inv @ (self.Xv.T @ y)); w = self.h * e
        vy = self.cY * float((np.bincount(self.yinv, weights=w) ** 2).sum())
        vb = self.cB * float((np.bincount(self.binv, weights=w) ** 2).sum())
        vyb = self.cYB * float((np.bincount(self.ybinv, weights=w) ** 2).sum())
        v2 = vy + vb - vyb
        if v2 <= 0:
            v2 = max(vy, vb)
        sy, s2 = math.sqrt(vy), math.sqrt(v2)
        return bj, sy, s2, max(sy, s2)


def simulate(D, erc_sample, beta, reps, seed0, var_block=0.0, var_within=1.08 ** 2):
    """Outcome = beta * log10 Aenc + 0.5 * erc_pct + block effect + noise; returns call shares per rule:
    primary  = the registered P1C rule, beta +- t(0.975, G-1) * max(two-way SE, year-only SE);
    pilot    = the pilot's rule, beta +- 1.96 * year-only SE;
    max_z    = beta +- 1.96 * max(...), for reference."""
    rules = {'primary': lambda sy, sm: (D.t, sm), 'pilot': lambda sy, sm: (1.96, sy), 'max_z': lambda sy, sm: (1.96, sm)}
    counts = {r: {'SUPPORTED': 0, 'CONTRADICTED': 0, 'NOT SUPPORTED': 0} for r in rules}
    for r in range(reps):
        rng = np.random.default_rng(seed0 + r)
        y = beta * D.la + 0.5 * erc_sample + rng.normal(0, math.sqrt(var_within), D.n)
        if var_block > 0:
            y = y + rng.normal(0, math.sqrt(var_block), D.nblocks)[D.binv]
        bj, sy, s2, sm = D.stats(y)
        for name, f in rules.items():
            c, se = f(sy, sm)
            lo, hi = bj - c * se, bj + c * se
            counts[name]['SUPPORTED' if lo > 0 else ('CONTRADICTED' if hi < 0 else 'NOT SUPPORTED')] += 1
    return {rule: {k: v / reps for k, v in c.items()} for rule, c in counts.items()}


def pilot_variance_components(rt, pilot_dir='/home/claude/p1/', block_m=20000):
    import pandas as pd
    dp = pd.read_csv(pilot_dir + 'predictors_blind.csv').merge(pd.read_csv(pilot_dir + 'outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
    sp, ap = rt.sample(dp, 'B')
    Xp = rt.design(sp, ap, 'rho_B', 'M2').values.astype(float); yp = np.log10(sp['fire_size'].values)
    ep = yp - Xp @ np.linalg.lstsq(Xp, yp, rcond=None)[0]
    bp = ((sp['x'] // block_m).astype(int).astype(str) + '_' + (sp['y'] // block_m).astype(int).astype(str)).values
    codes, inv = np.unique(bp, return_inverse=True); nb = np.bincount(inv); N, B = len(ep), len(codes)
    means = np.bincount(inv, weights=ep) / nb
    msw = float(((ep - means[inv]) ** 2).sum()) / (N - B)
    msb = float((nb * (means - ep.mean()) ** 2).sum()) / (B - 1); n0 = (N - (nb ** 2).sum() / N) / (B - 1)
    return dict(var_block=max(0.0, (msb - msw) / n0), var_within=msw, blocks=int(B), n=int(N))


# ---------------------------------------------------------------------------------------------------------------
# Continuous spatial error models (plan v1.2). The pilot's residuals are correlated across 20 km block boundaries
# (exponential correlogram, range about 11-12 km), which block clustering does not capture. These helpers fit
# that correlogram on the pilot and simulate persistent Gaussian random fields on a design, so the decision
# rule's critical value can be calibrated by simulation (calibrate_critical.py).

def pilot_residuals(rt, pilot_dir='/home/claude/p1/'):
    import pandas as pd
    dp = pd.read_csv(pilot_dir + 'predictors_blind.csv').merge(pd.read_csv(pilot_dir + 'outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
    sp, ap = rt.sample(dp, 'B')
    X = rt.design(sp, ap, 'rho_B', 'M2').values.astype(float); y = np.log10(sp['fire_size'].values)
    e = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    return e, sp['x'].values, sp['y'].values, sp['fire_year'].values


def pilot_correlogram(rt, max_km=60.0, block_m=20000):
    """Residual correlations by distance bin on the pilot: all pairs, and cross-year pairs (split by same block)."""
    e, x, y, yr = pilot_residuals(rt)
    z = e / e.std()
    blk = (np.floor(x / block_m).astype(int) * 100000 + np.floor(y / block_m).astype(int))
    i, j = np.triu_indices(len(z), 1)
    d = np.hypot(x[i] - x[j], y[i] - y[j]) / 1000.0
    k = d < max_km; i, j, d = i[k], j[k], d[k]
    prod = z[i] * z[j]; cross = yr[i] != yr[j]; same = blk[i] == blk[j]
    edges = np.array([0, 1, 2, 3.5, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60.0])

    def bins(mask):
        rows = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = mask & (d >= lo) & (d < hi)
            if m.sum():
                rows.append([float(d[m].mean()), float(prod[m].mean()), int(m.sum())])
        return np.array(rows)
    return dict(total_var=float(e.var()), all=bins(np.ones_like(cross)), cross=bins(cross),
                cross_same=bins(cross & same), cross_diff=bins(cross & ~same))


def fit_exponential(rows):
    from scipy.optimize import least_squares
    f = lambda p: (p[0] * np.exp(-rows[:, 0] / p[1]) - rows[:, 1]) * np.sqrt(rows[:, 2] / rows[:, 2].sum())
    r = least_squares(f, [0.05, 10.0], bounds=([0.0, 0.5], [1.0, 200.0]))
    return float(r.x[0]), float(r.x[1])


def fit_block_plus_exponential(same_rows, diff_rows):
    """corr = b * [same block] + s * exp(-d / r), fitted jointly to cross-year pairs."""
    from scipy.optimize import least_squares
    rows = np.vstack([np.c_[same_rows, np.ones(len(same_rows))], np.c_[diff_rows, np.zeros(len(diff_rows))]])
    w = np.sqrt(rows[:, 2] / rows[:, 2].sum())
    f = lambda p: (p[0] * rows[:, 3] + p[1] * np.exp(-rows[:, 0] / p[2]) - rows[:, 1]) * w
    r = least_squares(f, [0.02, 0.04, 10.0], bounds=([0.0, 0.0, 0.5], [1.0, 1.0, 200.0]))
    return float(r.x[0]), float(r.x[1]), float(r.x[2])


class Field:
    """Stationary Gaussian random field with unit variance and exponential correlation exp(-d / range_km), on a
    1 km periodic grid of NG x NG cells (circulant embedding, exact for the grid). Points are mapped to cells."""
    def __init__(self, range_km, xs, ys, NG=512):
        d1 = np.minimum(np.arange(NG), NG - np.arange(NG)).astype(float)
        lam = np.real(np.fft.fft2(np.exp(-np.sqrt(d1[:, None] ** 2 + d1[None, :] ** 2) / range_km)))
        self.sq = np.sqrt(np.clip(lam, 0, None)); self.NG = NG
        self.ci = ((xs - xs.min()) // 1000).astype(int) + 5
        self.cj = ((ys - ys.min()) // 1000).astype(int) + 5
        assert self.ci.max() < NG and self.cj.max() < NG

    def draw(self, rng):
        w = rng.normal(size=(self.NG, self.NG))
        return np.real(np.fft.ifft2(self.sq * np.fft.fft2(w)))[self.ci, self.cj]


def null_t(D, xs, ys, erc_sample, model, reps, seed0):
    """T = beta / max SE (and beta / year SE) under a null outcome with the given error model on design D.
    model: dict(var_total, block_share, field_share, range_km); the rest of the variance is independent noise."""
    vt = model['var_total']; vb = vt * model.get('block_share', 0.0); vf = vt * model.get('field_share', 0.0)
    vn = vt - vb - vf
    F = Field(model['range_km'], xs, ys) if vf > 0 else None
    Tm, Ty = np.empty(reps), np.empty(reps)
    for r in range(reps):
        rng = np.random.default_rng(seed0 + r)
        y = 0.5 * erc_sample + rng.normal(0, math.sqrt(vn), D.n)
        if vb > 0:
            y = y + rng.normal(0, math.sqrt(vb), D.nblocks)[D.binv]
        if F is not None:
            y = y + math.sqrt(vf) * F.draw(rng)
        bj, sy, s2, sm = D.stats(y)
        Tm[r], Ty[r] = bj / sm, bj / sy
    return Tm, Ty


def null_t_pair(D1, D2, xs, ys, erc_sample, model, reps, seed0):
    """null_t on two designs of the SAME sample (e.g. M2R and M2), from the same draws: (Tm1, Ty1, Tm2, Ty2)."""
    assert np.array_equal(D1.pos, D2.pos) and np.array_equal(D1.binv, D2.binv)
    vt = model['var_total']; vb = vt * model.get('block_share', 0.0); vf = vt * model.get('field_share', 0.0)
    vn = vt - vb - vf
    F = Field(model['range_km'], xs, ys) if vf > 0 else None
    out = np.empty((4, reps))
    for r in range(reps):
        rng = np.random.default_rng(seed0 + r)
        y = 0.5 * erc_sample + rng.normal(0, math.sqrt(vn), D1.n)
        if vb > 0:
            y = y + rng.normal(0, math.sqrt(vb), D1.nblocks)[D1.binv]
        if F is not None:
            y = y + math.sqrt(vf) * F.draw(rng)
        b1, sy1, _, sm1 = D1.stats(y); b2, sy2, _, sm2 = D2.stats(y)
        out[:, r] = (b1 / sm1, b1 / sy1, b2 / sm2, b2 / sy2)
    return out[0], out[1], out[2], out[3]


def sim_stats(D, xs, ys, erc_sample, model, reps, seed0, beta=0.0):
    """Like null_t, with a planted slope beta on log10 Aenc; returns arrays (beta_hat, se_year, se_max)."""
    vt = model['var_total']; vb = vt * model.get('block_share', 0.0); vf = vt * model.get('field_share', 0.0)
    vn = vt - vb - vf
    F = Field(model['range_km'], xs, ys) if vf > 0 else None
    B, SY, SM = np.empty(reps), np.empty(reps), np.empty(reps)
    for r in range(reps):
        rng = np.random.default_rng(seed0 + r)
        y = beta * D.la + 0.5 * erc_sample + rng.normal(0, math.sqrt(vn), D.n)
        if vb > 0:
            y = y + rng.normal(0, math.sqrt(vb), D.nblocks)[D.binv]
        if F is not None:
            y = y + math.sqrt(vf) * F.draw(rng)
        B[r], SY[r], _, SM[r] = D.stats(y)
    return B, SY, SM


class PilotPlausibility:
    """Indirect inference on the pilot (plan v1.3). A correlogram fitted to residuals is biased toward short ranges, so
    the plug-in fit (share 0.053, range 11.2 km) cannot be taken at face value. For a candidate field model
    (share, range), simulate field + independent noise on the pilot design, residualize on the pilot's B/M2 design
    matrix, recompute the all-pairs correlogram exactly as pilot_correlogram does, and refit the exponential. A model
    is RETAINED (the pilot cannot reject it) if the observed fitted share and range both lie inside the central 95%
    of its simulated fits. check_block() screens 20 km block effects the same way, on the pilot's ANOVA block share."""
    def __init__(self, rt, pilot_dir='/home/claude/p1/', max_km=60.0):
        import pandas as pd
        dp = pd.read_csv(pilot_dir + 'predictors_blind.csv').merge(pd.read_csv(pilot_dir + 'outcomes.csv')[['fod_id', 'fire_size']], on='fod_id', how='left')
        sp, ap = rt.sample(dp, 'B')
        self.X = rt.design(sp, ap, 'rho_B', 'M2').values.astype(float); self.M = np.linalg.pinv(self.X)
        self.x, self.y = sp['x'].values.astype(float), sp['y'].values.astype(float); self.n = len(self.x)
        i, j = np.triu_indices(self.n, 1); d = np.hypot(self.x[i] - self.x[j], self.y[i] - self.y[j]) / 1000.0
        k = d < max_km; self.i, self.j, d = i[k], j[k], d[k]
        edges = np.array([0, 1, 2, 3.5, 5, 7.5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60.0])
        self.b = np.digitize(d, edges) - 1; self.cnt = np.bincount(self.b, minlength=len(edges) - 1)
        self.dm = np.bincount(self.b, weights=d, minlength=len(edges) - 1) / self.cnt
        e_obs = pilot_residuals(rt, pilot_dir)[0]
        self.TOT = float(e_obs.var()); self.obs = self.fit(e_obs)
        blk = ((sp['x'] // 20000).astype(int).astype(str) + '_' + (sp['y'] // 20000).astype(int).astype(str)).values
        _, self.binv = np.unique(blk, return_inverse=True); self.nb = np.bincount(self.binv); self.nbk = len(self.nb)
        self.n0 = (self.n - (self.nb ** 2).sum() / self.n) / (self.nbk - 1)
        self.obs_block = self.anova_share(e_obs)

    def fit(self, e):
        z = e / e.std()
        pr = np.bincount(self.b, weights=z[self.i] * z[self.j], minlength=len(self.cnt)) / self.cnt
        return fit_exponential(np.c_[self.dm, pr, self.cnt])

    def anova_share(self, e):
        """One-way ANOVA (method of moments) share of variance between 20 km blocks, as pilot_variance_components."""
        means = np.bincount(self.binv, weights=e) / self.nb
        msw = float(((e - means[self.binv]) ** 2).sum()) / (self.n - self.nbk)
        msb = float((self.nb * (means - e.mean()) ** 2).sum()) / (self.nbk - 1)
        vb = max(0.0, (msb - msw) / self.n0)
        return vb / (vb + msw)

    def check_block(self, share, reps, seed):
        """Block effects with the given share of variance, plus independent noise, simulated on the pilot design and
        residualized like the real residuals; RETAINED if the pilot's observed ANOVA share lies inside the central 95%
        of the simulated estimates."""
        rng = np.random.default_rng(seed); est = []
        for _ in range(reps):
            yy = rng.normal(0, math.sqrt(self.TOT * (1 - share)), self.n) + rng.normal(0, math.sqrt(self.TOT * share), self.nbk)[self.binv]
            est.append(self.anova_share(yy - self.X @ (self.M @ yy)))
        q = np.quantile(est, [0.025, 0.5, 0.975])
        return dict(block_share=share, estimated_share_q025_q50_q975=q.tolist(), retained=bool(q[0] <= self.obs_block <= q[2]), reps=reps)

    def check(self, share, range_km, reps, seed):
        F = Field(range_km, self.x, self.y); rng = np.random.default_rng(seed); fs = []
        for _ in range(reps):
            yy = rng.normal(0, math.sqrt(self.TOT * (1 - share)), self.n) + math.sqrt(self.TOT * share) * F.draw(rng)
            fs.append(self.fit(yy - self.X @ (self.M @ yy)))
        fs = np.array(fs)
        qs = np.quantile(fs[:, 0], [0.025, 0.5, 0.975]); qr = np.quantile(fs[:, 1], [0.025, 0.5, 0.975])
        keep = bool(qs[0] <= self.obs[0] <= qs[2] and qr[0] <= self.obs[1] <= qr[2])
        return dict(share=share, range_km=range_km, fitted_share_q025_q50_q975=qs.tolist(),
                    fitted_range_q025_q50_q975=qr.tolist(), retained=keep, reps=reps)


# ---------------------------------------------------------------------------------------------------------------
# Stress set (plan v1.4): exact (Cholesky) fields, anisotropic or long-range, and compartment random effects. Exact
# fields avoid the periodic 512 km grid, which distorts long ranges. Used by calibrate_stress.py, pilot_reread.py,
# validate_synthetic.py and blind_design.py.

def anova_share_groups(e, inv):
    """One-way ANOVA (method of moments) share of variance between the groups coded by inv (0..G-1)."""
    nb = np.bincount(inv); G = len(nb); N = len(e)
    means = np.bincount(inv, weights=e) / nb
    msw = float(((e - means[inv]) ** 2).sum()) / (N - G)
    msb = float((nb * (means - e.mean()) ** 2).sum()) / (G - 1)
    n0 = (N - (nb ** 2).sum() / N) / (G - 1)
    vb = max(0.0, (msb - msw) / n0)
    return vb / (vb + msw)


def exact_chol(xs_m, ys_m, rx_km, ry_km, jitter=1e-6):
    """Lower Cholesky factor of exp(-sqrt((dx/rx)^2 + (dy/ry)^2)) at the given points (EPSG:5070 meters), built in
    row blocks. Coincident points make the matrix singular, so a jitter is added to the diagonal and raised tenfold
    until the factorization succeeds. Returns (L, jitter used)."""
    from scipy.linalg import cholesky
    x, y = np.asarray(xs_m, float) / 1000.0, np.asarray(ys_m, float) / 1000.0
    n = len(x)
    while True:
        C = np.empty((n, n))
        for i0 in range(0, n, 1000):
            dx = (x[i0:i0 + 1000, None] - x[None, :]) / rx_km
            dy = (y[i0:i0 + 1000, None] - y[None, :]) / ry_km
            C[i0:i0 + 1000] = np.exp(-np.sqrt(dx * dx + dy * dy))
        C[np.diag_indices(n)] += jitter
        try:
            return cholesky(C.T, lower=True, overwrite_a=True, check_finite=False), jitter   # C is symmetric
        except np.linalg.LinAlgError:
            del C
            jitter *= 10
            if jitter > 1e-2:
                raise


class StressErrors:
    """Errors for a stress model on one design: spec kind 'field' (exact field, var_total, share, rx_km, ry_km) or
    'comp' (compartment random effects, var_total, share; comp_inv codes each point's compartment), plus independent
    noise. Replicate r uses default_rng(seed0 + r): first the noise, then the standard normals of the field or of the
    compartments."""
    def __init__(self, spec, xs_m, ys_m, comp_inv=None):
        self.kind, self.n = spec['kind'], len(xs_m)
        self.sn = math.sqrt(spec['var_total'] * (1 - spec['share'])); self.sf = math.sqrt(spec['var_total'] * spec['share'])
        self.jitter = None
        if self.kind == 'field':
            self.L, self.jitter = exact_chol(xs_m, ys_m, spec['rx_km'], spec['ry_km'])
        else:
            self.inv = np.asarray(comp_inv); self.nc = int(self.inv.max()) + 1

    def batch(self, seeds):
        E = np.empty((len(seeds), self.n))
        Z = np.empty((self.n, len(seeds))) if self.kind == 'field' else None
        for j, s in enumerate(seeds):
            rng = np.random.default_rng(s)
            E[j] = rng.normal(0, self.sn, self.n)
            if Z is not None:
                Z[:, j] = rng.normal(size=self.n)
            else:
                E[j] += self.sf * rng.normal(size=self.nc)[self.inv]
        if Z is not None:
            E += self.sf * (self.L @ Z).T
        return E


def null_t_pair_stress(D1, D2, erc_sample, errs, reps, seed0, batch=200):
    """null_t_pair for a StressErrors model: (Tm1, Ty1, Tm2, Ty2) from the same draws on two designs of one sample."""
    assert np.array_equal(D1.pos, D2.pos)
    out = np.empty((4, reps))
    for b0 in range(0, reps, batch):
        idx = list(range(b0, min(reps, b0 + batch)))
        E = errs.batch([seed0 + r for r in idx])
        for j, r in enumerate(idx):
            y = 0.5 * erc_sample + E[j]
            b1, sy1, _, sm1 = D1.stats(y); b2, sy2, _, sm2 = D2.stats(y)
            out[:, r] = (b1 / sm1, b1 / sy1, b2 / sm2, b2 / sy2)
    return out[0], out[1], out[2], out[3]


def sim_stats_stress(D, erc_sample, errs, reps, seed0, beta=0.0, batch=200):
    """sim_stats for a StressErrors model: arrays (beta_hat, se_year, se_max) with a planted slope beta."""
    B, SY, SM = np.empty(reps), np.empty(reps), np.empty(reps)
    for b0 in range(0, reps, batch):
        idx = list(range(b0, min(reps, b0 + batch)))
        E = errs.batch([seed0 + r for r in idx])
        for j, r in enumerate(idx):
            B[r], SY[r], _, SM[r] = D.stats(beta * D.la + 0.5 * erc_sample + E[j])
    return B, SY, SM
