#!/usr/bin/env python3
"""P1 confirmatory replication (NE Washington): holdable-feature compartments and BLIND predictors per ignition.

Derived from the pilot's build_predictors.py (frozen 2026-10-20, sha256 3af05e25...). Changes, none of which
alters any computed value (verified by rebuilding the pilot table byte-for-byte, see EQUIVALENCE.json):
  - pilot records (by fod_id, from CFG['exclude_fod_ids_from']) are dropped, so the samples are disjoint;
  - memory only: int32 summed-area tables (exact, since H*W < 2**31), burn-scar masks stored as packed bits,
    and the B+ holdable mask computed once per year instead of once per ignition;
  - v1.1: an explicit closed lon/lat box filter on each record's own coordinates, so the sample definition no
    longer depends on how the server answers the envelope query (it removes no record in either region).

Invariants (tested in check_predictors.py):
  P1  No outcome data is read. The only fire input is raw/fpafod_ignitions_blind.json (no size fields).
  P2  Fuel connectivity is 4-neighbour; rasterized line features are 8-connected, so a compartment
      cannot leak through a diagonal gap in a line.
  P3  A compartment touching the compute-box edge is censored; under A50/A25, so is one containing PCL no-data.
  P4  All layers share the 30 m EPSG:5070 grid of p1_config.json.
  P5  No ignition in this table appears in the pilot table (disjoint samples).
Definitions of holdable cells:
  A50 PCL > 0.5 (classes 3-4), Washington DNR raster (O'Connor, Calkin & Thompson 2017 model). A25: PCL > 0.25.
  B   TIGER roads (vehicle classes) U NHD river areas and lakes/reservoirs U LANDFIRE non-burnable (91-99).
  B+  B U MTBS burned-area perimeters from the 10 calendar years before the ignition year.
"""
import datetime as dt
import json
import numpy as np
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from scipy.io import netcdf_file
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString, Polygon

CFG = json.load(open('p1_config.json'))
X0, Y0, X1, Y1 = CFG['compute_box_5070']; RES = 30; W, H = CFG['W'], CFG['H']
AX0, AY0, AX1, AY1 = CFG['analysis_box_5070']
LON0, LAT0, LON1, LAT1 = CFG['analysis_box_lonlat']
TF = from_origin(X0, Y1, RES, RES)
ACRES_PER_CELL = RES * RES / 4046.8564224
FOUR = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=bool)

ROAD_MTFCC = {'S1100', 'S1200', 'S1400', 'S1630', 'S1640', 'S1730', 'S1740', 'S1780'}   # vehicle roads; no 4WD trails/paths
NHD_AREA_FTYPES = {460, 431}            # StreamRiver, Rapids
NHD_WB_FTYPES = {390, 436, 378}         # LakePond, Reservoir, IceMass
NONBURN = [91, 92, 93, 98, 99]


def esri_lines(feats, keep=lambda a: True):
    out = []
    for f in feats:
        if not keep(f['attributes']) or not f.get('geometry'):
            continue
        for p in f['geometry'].get('paths', []):
            if len(p) >= 2:
                out.append(LineString(p))
    return out


def esri_polys(feats, keep=lambda a: True):
    """Esri rings: clockwise = exterior (negative shapely signed area), counter-clockwise = hole."""
    out = []
    for f in feats:
        if not keep(f['attributes']) or not f.get('geometry'):
            continue
        rings = [r for r in f['geometry'].get('rings', []) if len(r) >= 4]
        ext, holes = [], []
        for r in rings:
            pr = Polygon(r)
            (ext if pr.exterior.is_ccw is False else holes).append(r)
        polys = [[e, []] for e in ext]
        for h in holes:
            hp = Polygon(h)
            for pe in polys:
                if Polygon(pe[0]).contains(hp.representative_point()):
                    pe[1].append(h); break
        for e, hs in polys:
            p = Polygon(e, hs)
            out.append(p if p.is_valid else p.buffer(0))
    return out


def burn(geoms, all_touched=False):
    if not geoms:
        return np.zeros((H, W), dtype=bool)
    return features.rasterize(((g, 1) for g in geoms), out_shape=(H, W), transform=TF,
                              all_touched=all_touched, dtype='uint8').astype(bool)


def label_fuel(holdable, censor_extra=None):
    lab, n = ndimage.label(~holdable, structure=FOUR)
    area = np.bincount(lab.ravel(), minlength=n + 1).astype(np.int64)
    edge = np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))
    cens = np.zeros(n + 1, dtype=bool); cens[edge] = True
    if censor_extra is not None:
        cens[np.unique(lab[censor_extra])] = True
    cens[0] = False
    return lab, area, cens


def window_frac(mask, half=66):
    """Fraction of True cells in a (2*half+1)^2 window (half=66 -> ~4 km square) via a summed-area table.
    int32 is exact: every partial sum is at most H*W < 2**31, and window arithmetic stays within +-2*H*W."""
    assert 2 * H * W < 2 ** 31 - 1
    s = np.zeros((H + 1, W + 1), dtype=np.int32)
    s[1:, 1:] = np.cumsum(np.cumsum(mask, axis=0, dtype=np.int32), axis=1, dtype=np.int32)
    def at(r, c):
        r0, r1 = np.clip(r - half, 0, H), np.clip(r + half + 1, 0, H)
        c0, c1 = np.clip(c - half, 0, W), np.clip(c + half + 1, 0, W)
        tot = s[r1, c1] - s[r0, c1] - s[r1, c0] + s[r0, c0]
        return tot / ((r1 - r0) * (c1 - c0))
    return at


def snap_area(lab, area, cens, r, c, rad=3):
    """For an ignition on a holdable cell: the largest uncensored-or-censored compartment within rad cells."""
    r0, r1, c0, c1 = max(r - rad, 0), min(r + rad + 1, H), max(c - rad, 0), min(c + rad + 1, W)
    ids = np.unique(lab[r0:r1, c0:c1]); ids = ids[ids > 0]
    if ids.size == 0:
        return np.nan, True
    k = ids[area[ids].argmax()]
    return area[k] * ACRES_PER_CELL, bool(cens[k])


def main():
    lf = np.load('raw/fbfm40_lf2024.npy'); pcl = np.load('raw/pcl_class.npy')
    roads = esri_lines(json.load(open('raw/roads_primary.json')) + json.load(open('raw/roads_secondary.json')) +
                       json.load(open('raw/roads_local.json')), keep=lambda a: a.get('MTFCC') in ROAD_MTFCC)
    road_m = burn(roads)
    water = esri_polys(json.load(open('raw/nhd_area.json')), keep=lambda a: (a.get('FTYPE') if 'FTYPE' in a else a.get('ftype')) in NHD_AREA_FTYPES) + \
            esri_polys(json.load(open('raw/nhd_waterbody.json')), keep=lambda a: (a.get('FTYPE') if 'FTYPE' in a else a.get('ftype')) in NHD_WB_FTYPES)
    water_m = burn(water)
    nb_m = np.isin(lf, NONBURN)
    hold_B = road_m | water_m | nb_m
    pcl_nodata = pcl < 0
    # Definition A amended BEFORE any outcome was seen: the top PCL class alone (>0.75) left 99.5% of
    # ignition compartments open (22 usable ignitions), so A50 (PCL > 0.5) is primary and A25 (> 0.25) secondary.
    HOLD = {'A50': pcl >= 3, 'A25': pcl >= 2, 'B': hold_B}
    print('holdable fractions: roads %.4f water %.4f nonburn %.4f B %.4f A50 %.4f A25 %.4f; PCL nodata %.4f' %
          (road_m.mean(), water_m.mean(), nb_m.mean(), hold_B.mean(), HOLD['A50'].mean(), HOLD['A25'].mean(),
           pcl_nodata.mean()))
    LAB = {d: label_fuel(m, censor_extra=(pcl_nodata if d.startswith('A') else None)) for d, m in HOLD.items()}
    np.savez_compressed('compartments_static.npz', **{f'lab{d}': LAB[d][0] for d in HOLD},
                        road=road_m, water=water_m, nonburn=nb_m)
    FRAC = {d: window_frac(m) for d, m in HOLD.items()}; fracR = window_frac(road_m)
    rr, rc = np.nonzero(road_m)
    tree = cKDTree(np.column_stack([rr, rc]))

    # MTBS perimeters by year (barrier features only)
    mt = json.load(open('raw/mtbs_perims.json'))
    scars_by_year = {}
    for f in mt:
        scars_by_year.setdefault(f['attributes']['year'], []).append(f)
    scar_bits = {y: np.packbits(burn(esri_polys(fs))) for y, fs in scars_by_year.items()}   # 1 bit per cell

    def scar_mask(y):
        return np.unpackbits(scar_bits[y], count=H * W).reshape(H, W).view(bool)

    # gridMET ERC: per-cell percentile over 1992-2024
    erc_days, erc_vals = [], []
    for yr in range(1992, 2025):
        f = netcdf_file(f'raw/erc/erc_{yr}.nc', 'r', mmap=False)
        v = f.variables['daily_mean_energy_release_component-g'].data.astype(np.float32)
        v[v >= 32767] = np.nan
        erc_days.append(f.variables['day'].data.astype(np.int64)); erc_vals.append(v)
        lat = f.variables['lat'].data.copy(); lon = f.variables['lon'].data.copy()
    erc_days = np.concatenate(erc_days); erc_vals = np.concatenate(erc_vals, axis=0)   # (T, nlat, nlon)
    day_index = {int(d): i for i, d in enumerate(erc_days)}
    erc_sorted = np.sort(erc_vals, axis=0)
    nvalid = np.isfinite(erc_vals).sum(0)

    feats = json.load(open('raw/fpafod_ignitions_blind.json'))
    exclude = set()
    if CFG.get('exclude_fod_ids_from'):            # confirmatory sample must be disjoint from the pilot
        import csv as _csv
        exclude = {str(int(float(r['fod_id']))) for r in _csv.DictReader(open(CFG['exclude_fod_ids_from']))}
    n_excluded = 0
    rows = []
    for f in feats:
        a = f['attributes']; g = f.get('geometry') or {}
        if exclude and str(int(float(a['fod_id']))) in exclude:
            n_excluded += 1
            continue
        x, y = g.get('x'), g.get('y')
        if x is None:
            continue
        if not (LON0 <= a['longitude'] <= LON1 and LAT0 <= a['latitude'] <= LAT1):   # the closed lon/lat box queried
            continue
        if not (AX0 <= x <= AX1 and AY0 <= y <= AY1):
            continue
        r = int((Y1 - y) // RES); c = int((x - X0) // RES)
        if not (0 <= r < H and 0 <= c < W):
            continue
        yr = int(a['fire_year'])
        rec = dict(fod_id=a['fod_id'], fire_year=yr, doy=a.get('discovery_doy'),
                   cause=a.get('nwcg_cause_classification'), general_cause=a.get('nwcg_general_cause'),
                   owner=a.get('owner_descr'), agency=a.get('nwcg_reporting_agency'),
                   lat=a.get('latitude'), lon=a.get('longitude'), x=x, y=y, row=r, col=c)
        dd = a.get('discovery_date')
        if dd is not None:
            d = dt.datetime(1970, 1, 1) + dt.timedelta(milliseconds=dd)
            rec['month'] = d.month
            gday = (d.date() - dt.date(1900, 1, 1)).days
            ti = day_index.get(gday)
            li = int(np.abs(lat - a['latitude']).argmin()); lo = int(np.abs(lon - a['longitude']).argmin())
            if ti is not None and np.isfinite(erc_vals[ti, li, lo]):
                val = erc_vals[ti, li, lo]
                rec['erc'] = float(val)
                rec['erc_pct'] = float(np.searchsorted(erc_sorted[:, li, lo], val, side='right') / nvalid[li, lo])
        code = int(lf[r, c]); rec['fbfm40'] = code
        rec['fuel_group'] = {9: 'NB', 10: 'GR', 12: 'GS', 14: 'SH', 16: 'TU', 18: 'TL', 20: 'SB'}.get(code // 10, 'NB')
        rec['pcl_nodata'] = bool(pcl_nodata[r, c])
        for d in HOLD:
            lab, area, cens = LAB[d]
            k = lab[r, c]
            rec[f'on_hold_{d}'] = bool(HOLD[d][r, c])
            rec[f'Aenc_{d}'] = float(area[k] * ACRES_PER_CELL) if k > 0 else np.nan
            rec[f'cens_{d}'] = bool(cens[k]) if k > 0 else True
            rec[f'Aenc_{d}_snap'], rec[f'cens_{d}_snap'] = ((rec[f'Aenc_{d}'], rec[f'cens_{d}']) if k > 0
                                                            else snap_area(lab, area, cens, r, c))
            rec[f'rho_{d}'] = float(FRAC[d](r, c))
        rec['rho_road'] = float(fracR(r, c))
        dist, _ = tree.query([r, c]); rec['road_dist_m'] = float(dist * RES)
        rec['coarse_coords'] = bool(abs(round(a['latitude'], 2) - a['latitude']) < 1e-9 and
                                    abs(round(a['longitude'], 2) - a['longitude']) < 1e-9)
        rows.append(rec)

    # Def B+ (time-varying): label once per ignition year
    years = sorted({r['fire_year'] for r in rows})
    for yr in years:
        scars = np.zeros((H, W), dtype=bool)
        for yy in range(yr - 10, yr):
            if yy in scar_bits:
                scars |= scar_mask(yy)
        hold_Bp = hold_B | scars
        lab, area, cens = label_fuel(hold_Bp)
        for rec in rows:
            if rec['fire_year'] != yr:
                continue
            r, c = rec['row'], rec['col']; k = lab[r, c]
            rec['on_hold_Bp'] = bool(hold_Bp[r, c])
            rec['Aenc_Bp'] = float(area[k] * ACRES_PER_CELL) if k > 0 else np.nan
            rec['cens_Bp'] = bool(cens[k]) if k > 0 else True
    import csv
    keys = sorted({k for r in rows for k in r})
    with open('predictors_blind.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print('ignitions in analysis box:', len(rows), '| excluded as pilot records:', n_excluded)


if __name__ == '__main__':
    main()
