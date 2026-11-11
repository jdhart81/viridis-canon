#!/usr/bin/env python3
"""P1C-W: build the blind wind predictor table for a P1C-style ignition table.
Inputs: raw/era5/era5_wind_YYYYMM.npz (ERA5 hourly 10 m u, v; fetch_era5_wind.py) and a blind predictor table with
fod_id, fire_year, doy, lon, lat. No outcome column is read (asserted). Output columns per ignition:
  W1, W3, W7   max over local standard days d0..d0+k-1 of the hourly 10 m wind speed (m/s), bilinear at the ignition
  W3mean       max over d0..d0+2 of the daily MEAN speed (closest analogue of gridMET vs)
  P3           placebo: W3 computed for days d0-30..d0-28
  W3_pct       percentile of W3 at the ignition among all 3-day windows 1992-2024 at the same point
Local standard day = UTC-8 (PST), 08:00 UTC to 07:00 UTC next day. d0 = FPA FOD discovery date (fire_year, doy).
Window lengths are fixed by discovery date alone; no containment or other outcome-linked field is used."""
import glob, sys, datetime as dt, numpy as np, pandas as pd
FORBID = {'fire_size', 'fire_size_class', 'cont_date', 'cont_doy', 'cont_time'}
inp, out = sys.argv[1], sys.argv[2]
p = pd.read_csv(inp)
assert not (set(c.lower() for c in p.columns) & FORBID), 'outcome field present'
files = sorted(glob.glob('raw/era5/era5_wind_*.npz'))
T, S = [], []
for f in files:
    z = np.load(f); T.append(z['time']); S.append(np.hypot(z['u10'], z['v10']).astype(np.float32)); lat, lon = z['lat'], z['lon']
T = np.concatenate(T).astype(np.int64); S = np.concatenate(S)
assert np.all(np.diff(T) == 1), 'hourly series has gaps'
t0 = dt.datetime(1900, 1, 1) + dt.timedelta(hours=int(T[0]))
def hour_index(d):   # first UTC hour of local standard day d (08 UTC)
    return int(((dt.datetime(d.year, d.month, d.day, 8) - dt.datetime(1900, 1, 1)).total_seconds() // 3600) - T[0])
# bilinear weights (lat descending)
lo = (p['lon'].values % 360.0); la = p['lat'].values
fi = (lat[0] - la) / 0.25; fj = (lo - lon[0]) / 0.25
i0 = np.floor(fi).astype(int); j0 = np.floor(fj).astype(int); di = fi - i0; dj = fj - j0
assert i0.min() >= 0 and i0.max() + 1 < len(lat) and j0.min() >= 0 and j0.max() + 1 < len(lon)
def series(k, h0, nh):
    if h0 < 0 or h0 + nh > len(T):
        return None
    a = S[h0:h0 + nh]
    return ((1 - di[k]) * (1 - dj[k]) * a[:, i0[k], j0[k]] + (1 - di[k]) * dj[k] * a[:, i0[k], j0[k] + 1]
            + di[k] * (1 - dj[k]) * a[:, i0[k] + 1, j0[k]] + di[k] * dj[k] * a[:, i0[k] + 1, j0[k] + 1])
d0s = [dt.date(int(y), 1, 1) + dt.timedelta(days=int(d) - 1) for y, d in zip(p['fire_year'], p['doy'])]
# climatology of 3-day windows at each ignition point is expensive per point; use the point's own full series once
h92 = hour_index(dt.date(1992, 1, 1)); h24 = hour_index(dt.date(2024, 12, 29))
rows = []
for k, d0 in enumerate(d0s):
    h = hour_index(d0); r = {'fod_id': p['fod_id'].iat[k]}
    for name, off, nd in (('W1', 0, 1), ('W3', 0, 3), ('W7', 0, 7), ('P3', -30, 3)):
        s = series(k, h + 24 * off, 24 * nd); r[name] = float(s.max()) if s is not None else np.nan
    s = series(k, h, 72); r['W3mean'] = float(s.reshape(3, 24).mean(1).max()) if s is not None else np.nan
    rows.append(r)
W = pd.DataFrame(rows)
# per-point percentile of W3 among all 3-day windows 1992-2024 (non-overlapping start days, every day)
pct = np.full(len(p), np.nan)
full = None
for k in range(len(p)):
    if np.isnan(W['W3'].iat[k]):
        continue
    s = series(k, h92, h24 - h92 + 72)
    dmax = s[: (len(s) // 24) * 24].reshape(-1, 24).max(1)
    w3 = np.maximum(np.maximum(dmax[:-2], dmax[1:-1]), dmax[2:])
    pct[k] = float(np.searchsorted(np.sort(w3), W['W3'].iat[k], side='right') / len(w3))
W['W3_pct'] = pct
W.to_csv(out, index=False)
print('rows', len(W), 'missing W3', int(W['W3'].isna().sum()), 'missing W7', int(W['W7'].isna().sum()), 'missing P3', int(W['P3'].isna().sum()))
print(W.describe().T.round(3))
