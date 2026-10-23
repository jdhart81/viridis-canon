#!/usr/bin/env python3
"""P1-M post hoc checks. NOT in the plan: added after the results, at the independent reviewer's suggestion
(REVIEW_of_P1M.md, alternative explanation 1). Reported in full whatever they show.

Question. Is the road edge excess (E_road = 1.45) a valley-floor or fuel-transition effect, rather than perimeters
lying at roads? Roads run along valley floors, where fuels change to farmland, development and riparian vegetation.
What each check would show under that explanation is stated here, before the run:
  A. Road class. Highways (MTFCC S1100, S1200), local roads (S1400) and other vehicle roads (S1630, S1640, S1730,
     S1740, S1780) are rasterized separately with the builder's own functions. A valley-floor effect should sit
     mainly on highways. Dozer lines later mapped as roads cannot be highways.
  B. Away from valley floors. E_road counts only cells with no water and no non-burnable cell within 300 m, in
     both the edge band and the reference band. The mask is a property of the landscape, so it moves with the
     landscape in the shift null. A valley-floor effect should shrink or vanish here.
Same primary sample, statistic, cluster bootstrap (2,000; seed 1) and shift null (1,000; seed 2) as mech_test.py,
whose frozen functions are imported unchanged. Writes POSTHOC_ROADS.json.
Usage: python3 -B posthoc_roads.py"""
import hashlib, importlib.util, json, os, sys, time
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('mt', os.path.join(HERE, 'mech_test.py')); mt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mt)
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
FROZEN = json.load(open(os.path.join(HERE, 'MECH_FREEZE.json')))['sha256']
assert sha(os.path.join(HERE, 'mech_test.py')) == FROZEN['mech_test.py'], 'mech_test.py is not the frozen code'
CLASSES = {'highway': {'S1100', 'S1200'}, 'local': {'S1400'}, 'other_vehicle': {'S1630', 'S1640', 'S1730', 'S1740', 'S1780'}}
NEAR_M = 300.0


def ratio_ci_null(fires, codes_flat, W, num_ok, den_ok):
    """E = (edge share of codes in num_ok among codes in den_ok) / (same for the outside reference); with the plan's
    cluster bootstrap and shift null. num_ok, den_ok: boolean arrays over the 8 codes."""
    clusters = mt.make_clusters(fires)
    edge = [mt.bidx(b) for b in mt.EDGE_BINS]; ref = [mt.bidx(b) for b in mt.REF_OUT_BINS]
    def E(C):
        e = C[edge][:, num_ok].sum() / C[edge][:, den_ok].sum()
        r = C[ref][:, num_ok].sum() / C[ref][:, den_ok].sum()
        return float(e / r), float(e), float(r)
    obs_c = np.stack([sum(mt.counts_at(codes_flat, W, f.rows, f.cols, f.bins) for f in c.fires) for c in clusters])
    e_obs, se, sr = E(obs_c.sum(0))
    rng = np.random.default_rng(mt.SEED_BOOT); k = len(clusters)
    boot = [E(obs_c[rng.integers(0, k, k)].sum(0))[0] for _ in range(mt.N_BOOT)]
    rng = np.random.default_rng(mt.SEED_SHIFT); null = []
    for _ in range(mt.N_SHIFT):
        tot = np.zeros((2 * mt.NB + 1, 8), dtype=np.int64)
        for c in clusters:
            dr, dc = c.draw_shift(rng)
            for f in c.fires:
                tot += mt.counts_at(codes_flat, W, f.rows, f.cols, f.bins, dr, dc)
        null.append(E(tot)[0])
    z = np.array(null)
    return dict(E=e_obs, share_edge=se, share_ref_out=sr, ci95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                null_q025=float(np.percentile(z, 2.5)), null_median=float(np.median(z)), null_q975=float(np.percentile(z, 97.5)),
                p_shift_upper=float((1 + np.sum(z >= e_obs)) / (1 + len(z))), n_fires=len(fires), n_clusters=k)


def main():
    t0 = time.time()
    bp = mt.load_builder()
    _, _, _, samples = mt.build_pilot_fires(bp)
    fires = samples['primary']
    z = np.load(mt.INPUTS['compartments_static.npz'])
    road, water, nonburn = z['road'], z['water'], z['nonburn']
    H, W = road.shape
    raw = []
    for fn in ('roads_primary.json', 'roads_secondary.json', 'roads_local.json'):
        raw += json.load(open(os.path.join(mt.P1, 'raw', fn)))
    cls = {name: bp.burn(bp.esri_lines(raw, keep=lambda a, m=m: a.get('MTFCC') in m)) for name, m in CLASSES.items()}
    union = cls['highway'] | cls['local'] | cls['other_vehicle']
    assert np.array_equal(union, road), 'the class rasters do not reproduce the frozen road raster'
    out = dict(note='Post hoc checks, not in the plan; see the docstring of posthoc_roads.py.', code_sha256=sha(__file__),
               mech_test_sha256=FROZEN['mech_test.py'], class_cells={k: int(v.sum()) for k, v in cls.items()},
               union_equals_frozen_road_raster=True, checks={})
    T = np.arange(8)
    has1, has2 = (T & 1) != 0, (T & 2) != 0
    for name, m in cls.items():                                   # A: road class; bit 1 = this class
        codes = (m.astype(np.uint8) | (water.astype(np.uint8) << 1) | (nonburn.astype(np.uint8) << 2)).ravel()
        out['checks'][f'A_{name}'] = r = ratio_ci_null(fires, codes, W, has1, np.ones(8, bool))
        print('A', name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    near = ndimage.distance_transform_edt(~(water | nonburn), sampling=mt.RES) <= NEAR_M   # within 300 m of water or non-burnable
    codes = (road.astype(np.uint8) | (near.astype(np.uint8) << 1)).ravel()                  # bit 1 = road, bit 2 = near
    out['checks']['B_road_away_from_valley_floors'] = r = ratio_ci_null(fires, codes, W, has1 & ~has2, ~has2)
    r['share_of_grid_kept'] = float((~near).mean())
    print('B', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(HERE, 'POSTHOC_ROADS.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
