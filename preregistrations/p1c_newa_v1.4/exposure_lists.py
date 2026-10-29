#!/usr/bin/env python3
"""Blind lists for two v1.2 sensitivity analyses; writes EXPOSURE_LISTS.json. Uses coordinates and dates only.
  S10b  confirmatory ignitions inside (or within 1 km of) any of the pilot-fetched MTBS perimeters that reach this
        region (the pilot received those perimeters' full attribute records, including acreage). run_test.py drops
        them together with S10's pilot-compute-box ignitions.
  S12   confirmatory ignitions with a pilot ignition on the same discovery date within 5 km: possible duplicate
        reports of one fire across the boundary, whose size the pilot's outcomes would reveal."""
import importlib.util, json, os
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
spec = importlib.util.spec_from_file_location('bp', 'build_predictors.py'); bp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bp)
cfg = json.load(open('p1_config.json'))
lon0, lat0, lon1, lat1 = cfg['analysis_box_lonlat']
tr = Transformer.from_crs(4326, 5070, always_xy=True)
edge = ([(x, lat0) for x in np.linspace(lon0, lon1, 200)] + [(lon1, y) for y in np.linspace(lat0, lat1, 200)] +
        [(x, lat1) for x in np.linspace(lon1, lon0, 200)] + [(lon0, y) for y in np.linspace(lat1, lat0, 200)])
region = Polygon([tr.transform(x, y) for x, y in edge])
pil = json.load(open('../p1/raw/mtbs_perims.json'))
reach = []
for f in pil:
    ps = bp.esri_polys([f])
    if any(p.intersects(region) for p in ps):
        reach.append((f['attributes']['year'], unary_union(ps)))
zone = unary_union([g for _, g in reach]).buffer(1000)
pred = pd.read_csv('predictors_blind.csv')
pts = [Point(x, y) for x, y in zip(pred['x'], pred['y'])]
inside = np.array([zone.contains(p) for p in pts])
pc = json.load(open('../p1/p1_config.json'))['compute_box_5070']
in_box = ((pred.x >= pc[0]) & (pred.x <= pc[2]) & (pred.y >= pc[1]) & (pred.y <= pc[3])).values
# S12: same discovery date (year and day of year) within 5 km of a pilot ignition
pp = pd.read_csv('../p1/predictors_blind.csv')
tree = cKDTree(np.c_[pp['x'], pp['y']])
dup = []
for k, (x, y, yr, doy, fid) in enumerate(zip(pred['x'], pred['y'], pred['fire_year'], pred['doy'], pred['fod_id'])):
    for jj in tree.query_ball_point([x, y], 5000):
        if pp['fire_year'].iat[jj] == yr and pp['doy'].iat[jj] == doy:
            dup.append(dict(fod_id=int(fid), pilot_fod_id=int(pp['fod_id'].iat[jj]), year=int(yr), doy=int(doy),
                            distance_m=round(float(np.hypot(x - pp['x'].iat[jj], y - pp['y'].iat[jj])), 1)))
rec = dict(s10b=dict(pilot_perimeters_reaching_region=len(reach), years_1992_2024=sum(1992 <= y <= 2024 for y, _ in reach),
                     buffer_m=1000, fod_ids_inside_perimeters=[int(v) for v in pred.loc[inside, 'fod_id']],
                     n_inside_perimeters=int(inside.sum()), n_inside_perimeters_outside_pilot_box=int((inside & ~in_box).sum()),
                     n_inside_pilot_box=int(in_box.sum()), n_dropped_s10b=int((inside | in_box).sum())),
           s12=dict(rule='same fire_year and day of year as a pilot ignition, within 5 km', pairs=dup,
                    fod_ids=sorted({d['fod_id'] for d in dup})))
json.dump(rec, open('EXPOSURE_LISTS.json', 'w'), indent=1)
print({k: v for k, v in rec['s10b'].items() if k != 'fod_ids_inside_perimeters'})
print('S12 candidate duplicates:', len(rec['s12']['fod_ids']), rec['s12']['pairs'])
