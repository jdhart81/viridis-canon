#!/usr/bin/env python3
"""Invariant checks for the P1 confirmatory predictors (run before freezing). Exit code != 0 on any failure.
Same checks as the pilot (P1-P4) plus P5 (disjoint from the pilot) and P6 (completeness of the sample)."""
import hashlib, json, sys
import numpy as np
import pandas as pd
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from shapely.geometry import LineString

FOUR = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)
FORBIDDEN = {'fire_size', 'fire_size_class', 'cont_date', 'cont_doy', 'cont_time', 'mtbs_id', 'mtbs_fire_name',
             'complex_name', 'ics_209_plus_incident_join_id', 'ics_209_plus_complex_join_id'}
fails = []

def check(name, ok, detail=''):
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
    if not ok:
        fails.append(name)

# P1 blindness
df = pd.read_csv('predictors_blind.csv')
check('P1 predictors carry no outcome column', not (set(c.lower() for c in df.columns) & FORBIDDEN), str(set(df.columns) & FORBIDDEN))
raw = json.load(open('raw/fpafod_ignitions_blind.json'))
keys = set(k.lower() for f in raw for k in f['attributes'])
check('P1 raw ignition records carry no outcome field', not (keys & FORBIDDEN), str(keys & FORBIDDEN))

# P2 diagonal lines block 4-connected fuel (toy grid, same rasterizer settings)
tf = from_origin(0, 100, 1, 1)
line = LineString([(0.5, 99.5), (99.5, 0.5)])      # a pure diagonal across a 100x100 grid
m = features.rasterize([(line, 1)], out_shape=(100, 100), transform=tf, all_touched=False, dtype='uint8').astype(bool)
lab, n = ndimage.label(~m, structure=FOUR)
check('P2 an 8-connected diagonal line splits 4-connected fuel into 2 compartments', n == 2, f'n={n}')
lab8, n8 = ndimage.label(~m, structure=np.ones((3, 3), bool))
check('P2 control: the same line leaks under 8-connected fuel', n8 == 1, f'n8={n8}')

# P3 censoring on the real output: recompute from saved labels for every ignition
cfg = json.load(open('p1_config.json')); H, W = cfg['H'], cfg['W']
z = np.load('compartments_static.npz')
for d in ['A50', 'A25', 'B']:
    labd = z[f'lab{d}']
    edge = set(np.unique(np.concatenate([labd[0, :], labd[-1, :], labd[:, 0], labd[:, -1]])).tolist())
    ks = labd[df['row'].values, df['col'].values]
    exp_edge = np.array([k in edge for k in ks])
    got = df[f'cens_{d}'].astype(bool).values
    # censored must include every edge-touching compartment (A may add PCL no-data censoring)
    ok = np.all(got[exp_edge & (ks > 0)])
    check(f'P3 every edge-touching compartment is censored ({d})', bool(ok))
    if d == 'B':
        check('P3 B censoring equals edge-touching exactly', bool(np.all(got[ks > 0] == exp_edge[ks > 0])))

# P4 grid
check('P4 compartment rasters on the compute grid', all(z[k].shape == (H, W) for k in ['labA50', 'labA25', 'labB']))

# P5 disjoint from the pilot, using the frozen pilot table
PILOT_SHA = '57118595eea2a28b2e268733ec9645304fdb283bfc60ed107c332624a96dc4d0'
ex = cfg['exclude_fod_ids_from']
check('P5 exclusion list is the frozen pilot table', hashlib.sha256(open(ex, 'rb').read()).hexdigest() == PILOT_SHA)
pilot_ids = set(pd.read_csv(ex, usecols=['fod_id'])['fod_id'].astype('int64'))
mine = df['fod_id'].astype('int64')
check('P5 no pilot ignition in the confirmatory table', not (pilot_ids & set(mine)), f'overlap={len(pilot_ids & set(mine))}')
check('P5 fod_id unique in the confirmatory table', mine.is_unique)
# P6 completeness: every raw record inside the closed lon/lat analysis box is in the table unless it is a pilot record
LON0, LAT0, LON1, LAT1 = cfg['analysis_box_lonlat']
inbox = [int(float(f['attributes']['fod_id'])) for f in raw
         if (f.get('geometry') or {}).get('x') is not None
         and LON0 <= f['attributes']['longitude'] <= LON1 and LAT0 <= f['attributes']['latitude'] <= LAT1]
missing = set(inbox) - pilot_ids - set(mine)
check('P6 table = raw in-box records minus pilot records', not missing and len(set(mine)) == len(set(inbox) - pilot_ids),
      f'raw in box {len(inbox)}, pilot {len(set(inbox) & pilot_ids)}, table {len(mine)}, missing {len(missing)}')

# Descriptives (no outcomes)
print('\nDESCRIPTIVES (blind)')
print('ignitions in analysis box:', len(df))
print('cause:', df['cause'].value_counts(dropna=False).to_dict())
print('years:', int(df['fire_year'].min()), '-', int(df['fire_year'].max()), '| ERC available:', round(df['erc_pct'].notna().mean(), 3))
for d in ['A50', 'A25', 'B', 'Bp']:
    on = df[f'on_hold_{d}'].astype(bool); ce = df[f'cens_{d}'].astype(bool)
    usable = df[~on & ~ce & df[f'Aenc_{d}'].notna()]
    q = np.log10(usable[f'Aenc_{d}']).quantile([.1, .25, .5, .75, .9]).round(2).tolist()
    print(f'{d}: on-holdable {on.mean():.3f}, censored {ce.mean():.3f}, usable n={len(usable)}, log10 Aenc acres q10..q90 {q}')
    if d in ('A50', 'A25', 'B'):
        rho = usable[f'rho_{d}']
        r = np.corrcoef(np.log10(usable[f'Aenc_{d}']), np.log10(rho + 0.001))[0, 1]
        r2 = np.corrcoef(np.log10(usable[f'Aenc_{d}']), np.log10(usable['road_dist_m'] + 30))[0, 1]
        print(f'   corr(log Aenc, log rho) = {r:.2f}; corr(log Aenc, log road dist) = {r2:.2f}')
print('coarse coordinates:', round(df['coarse_coords'].astype(bool).mean(), 3))
sys.exit(1 if fails else 0)
