#!/usr/bin/env python3
"""P1-M: do final fire perimeters run along mapped barriers? Pilot region only; pre-specified in MECH_PLAN.md.

Question. Trees Cannot Cut predicts that fires end where closed loops of holdable features stop them (definition B:
vehicle roads, open water, non-burnable ground). If so, the land just beyond a final fire perimeter should hold more
barrier cells than the land a little farther out.

Statistic, for each barrier type t (B = any of the three; road; water; nonburn), pooled over fires:
    E_t = [share of unburned cells with 0 < s <= 90 m that are barrier t]
          / [share of unburned cells with 150 < s <= 600 m that are barrier t],
where s is the distance from an unburned cell's centre to the nearest burned cell's centre (30 m grid, EDT).
E = 1 when perimeters ignore barriers. Secondary: the inside ratio C_t (burned cells 150 < d_in <= 600 m against the
same outside reference) and the profile of barrier share by signed distance (30 m bins, -600 to +600 m).

Clusters. Fires whose zones (burned cells plus 600 m) share a cell, directly or through other fires, form one cluster:
reburns and neighbours share landscape, so clusters, not fires, are the independent units.
Inference. (a) A 95% percentile interval from N_BOOT bootstrap resamples of clusters. (b) A shift null: each cluster's
masks, with all their bands, are moved rigidly by one random whole-cell vector and E is recomputed from the barrier map
at the new place; N_SHIFT replicates, clusters shifted independently. The vector is drawn from the shifts that keep the
cluster's zones on the grid, with length uniform on 2-6 km and direction uniform (lattice points weighted by 1/length).
p_shift = (1 + #{E_null >= E_obs}) / (1 + N_SHIFT).
Decision (primary: E_B over the PRIMARY sample): SUPPORTED if the interval lies above 1 and p_shift < 0.025;
CONTRADICTED if the interval lies below 1 and (1 + #{E_null <= E_obs}) / (1 + N_SHIFT) < 0.025; else INCONCLUSIVE.

Samples. A fire is an MTBS perimeter feature whose polygon intersects the pilot analysis box and whose zone (burned
cells plus 600 m) lies on the compute grid with room for a 2 km shift. PRIMARY: perimeters of 1992-2024 that contain,
or lie within 300 m of, at least one FPA FOD ignition of the same year (the pilot's blind ignition table): matched
wildfires, which excludes prescribed burns (not in FPA FOD) whose edges are planned along roads. Secondary: all
perimeters, any year; and the primary sample split at 2010 (older fires are more exposed to roads and fuels mapped
later).

Usage:  python3 -B mech_test.py synthetic   planted-world validation -> SYNTHETIC_CHECK.json (reads no real data)
        python3 -B mech_test.py sample      builds the fire samples and clusters only -> SAMPLE_QA.json (no barrier map
                                            is read, so no perimeter is compared with any barrier)
        python3 -B mech_test.py real        the pre-specified analysis -> MECH_RESULTS.json, mech_profile.png
"""
import hashlib, importlib.util, json, math, os, sys, time
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
P1 = '/home/claude/p1'
RES = 30.0
NB = 20                                   # profile bins of 30 m on each side: bins -20..-1 (inside), 1..20 (outside)
EDGE_BINS = range(1, 4)                   # 0 < s <= 90 m
REF_OUT_BINS = range(6, NB + 1)           # 150 < s <= 600 m
REF_IN_BINS = range(-NB, -5)              # 150 < d_in <= 600 m  (bins -20..-6)
SHIFT_M = (2000.0, 6000.0)
MATCH_M = 300.0
N_BOOT, N_SHIFT = 2000, 1000
SEED_BOOT, SEED_SHIFT = 1, 2
TYPE_BITS = {'B': 7, 'road': 1, 'water': 2, 'nonburn': 4}     # barrier code: road=1 | water=2 | nonburn=4
TYPES = tuple(TYPE_BITS)
CODE_HAS = {t: np.array([(c & b) != 0 for c in range(8)]) for t, b in TYPE_BITS.items()}


def bidx(b):
    return b + NB                          # bin -20..20 -> row 0..40 of a (41, 8) count table


def zone_cells(mask):
    """Cells within 600 m of the perimeter of a burned window mask: (rows, cols, bins), bins as in NB."""
    d_out = ndimage.distance_transform_edt(~mask, sampling=RES)    # unburned cells: distance to the nearest burned cell
    d_in = ndimage.distance_transform_edt(mask, sampling=RES)      # burned cells: distance to the nearest unburned cell
    b_out = np.ceil(np.round(d_out / RES, 6)).astype(np.int16)
    b_in = np.ceil(np.round(d_in / RES, 6)).astype(np.int16)
    out = (~mask) & (b_out >= 1) & (b_out <= NB)
    ins = mask & (b_in >= 1) & (b_in <= NB)
    ro, co = np.nonzero(out); ri, ci = np.nonzero(ins)
    rows = np.concatenate([ro, ri]); cols = np.concatenate([co, ci])
    bins = np.concatenate([b_out[ro, co], -b_in[ri, ci]]).astype(np.int8)
    return rows, cols, bins, d_out


def counts_at(codes_flat, W, rows, cols, bins, dr=0, dc=0):
    key = (bins.astype(np.int64) + NB) * 8 + codes_flat[(rows + dr).astype(np.int64) * W + (cols + dc)]
    return np.bincount(key, minlength=(2 * NB + 1) * 8).reshape(2 * NB + 1, 8)


def summarize(C):
    """C: (41, 8) counts pooled over fires -> E_t, C_t, profile shares, and the cell counts used."""
    cells = C.sum(1).astype(float)
    bar = {t: C[:, CODE_HAS[t]].sum(1).astype(float) for t in TYPES}
    def share(t, bins):
        rows = [bidx(b) for b in bins]
        n = cells[rows].sum()
        return bar[t][rows].sum() / n if n else float('nan')
    out = {}
    for t in TYPES:
        e, ro, ri = share(t, EDGE_BINS), share(t, REF_OUT_BINS), share(t, REF_IN_BINS)
        out[t] = dict(E=e / ro if ro > 0 else float('nan'), C_inside=ri / ro if ro > 0 else float('nan'),
                      share_edge=e, share_ref_out=ro, share_ref_in=ri)
    out['cells'] = dict(edge=float(cells[[bidx(b) for b in EDGE_BINS]].sum()),
                        ref_out=float(cells[[bidx(b) for b in REF_OUT_BINS]].sum()),
                        ref_in=float(cells[[bidx(b) for b in REF_IN_BINS]].sum()))
    out['profile'] = {t: [float(bar[t][bidx(b)] / cells[bidx(b)]) if cells[bidx(b)] else None
                          for b in list(range(-NB, 0)) + list(range(1, NB + 1))] for t in TYPES}
    return out


class Fire:
    def __init__(self, name, rows, cols, bins, H, W):
        self.name, self.rows, self.cols, self.bins = name, rows.astype(np.int32), cols.astype(np.int32), bins
        self.rmin, self.rmax, self.cmin, self.cmax = int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())
        self.H, self.W = H, W


_CAND = {}


def shift_candidates():
    """Whole-cell shifts with length in SHIFT_M, weighted 1/length so that length is uniform and direction uniform."""
    if not _CAND:
        lo, hi = SHIFT_M[0] / RES, SHIFT_M[1] / RES
        R = int(math.ceil(hi))
        dr, dc = np.mgrid[-R:R + 1, -R:R + 1]
        r = np.hypot(dr, dc); keep = (r >= lo) & (r <= hi)
        _CAND.update(dr=dr[keep].astype(np.int64), dc=dc[keep].astype(np.int64), w=1.0 / r[keep])
    return _CAND['dr'], _CAND['dc'], _CAND['w']


class Cluster(Fire):
    """Fires whose zones share a cell (transitively); shifted together, resampled together."""
    def __init__(self, fires):
        self.fires = fires; self.name = '+'.join(f.name for f in fires)
        self.rmin, self.rmax = min(f.rmin for f in fires), max(f.rmax for f in fires)
        self.cmin, self.cmax = min(f.cmin for f in fires), max(f.cmax for f in fires)
        self.H, self.W = fires[0].H, fires[0].W
        dr, dc, w = shift_candidates()
        ok = (self.rmin + dr >= 0) & (self.rmax + dr < self.H) & (self.cmin + dc >= 0) & (self.cmax + dc < self.W)
        self.sdr, self.sdc = dr[ok], dc[ok]
        cw = np.cumsum(w[ok]); self.cw = cw / cw[-1] if len(cw) else cw

    def room(self):
        return len(self.sdr) > 0

    def draw_shift(self, rng):
        i = min(int(np.searchsorted(self.cw, rng.random(), side='right')), len(self.cw) - 1)
        return int(self.sdr[i]), int(self.sdc[i])


def make_clusters(fires):
    """Union-find over fires whose zone cells overlap, in input order; deterministic."""
    H, W = fires[0].H, fires[0].W
    parent = list(range(len(fires)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    owner = np.full(H * W, -1, dtype=np.int32)
    for i, f in enumerate(fires):
        idx = f.rows.astype(np.int64) * W + f.cols
        for j in np.unique(owner[idx]):
            if j >= 0:
                parent[find(int(j))] = find(i)
        owner[idx] = i
    groups = {}
    for i in range(len(fires)):
        groups.setdefault(find(i), []).append(fires[i])
    return [Cluster(g) for g in groups.values()]


def analyse(fires, codes_flat, W, n_boot=N_BOOT, n_shift=N_SHIFT, seed_boot=SEED_BOOT, seed_shift=SEED_SHIFT, profile_null=True):
    clusters = make_clusters(fires)
    if not all(c.room() for c in clusters):
        raise RuntimeError('a cluster has no room for a 2 km shift')
    obs_c = np.stack([sum(counts_at(codes_flat, W, f.rows, f.cols, f.bins) for f in c.fires) for c in clusters])   # (k, 41, 8)
    obs = summarize(obs_c.sum(0))
    rng = np.random.default_rng(seed_boot); k = len(clusters)
    boot = {t: [] for t in TYPES}
    for _ in range(n_boot):
        s = summarize(obs_c[rng.integers(0, k, k)].sum(0))
        for t in TYPES:
            boot[t].append(s[t]['E'])
    rng = np.random.default_rng(seed_shift)
    null = {t: [] for t in TYPES}; null_prof = []
    for _ in range(n_shift):
        tot = np.zeros((2 * NB + 1, 8), dtype=np.int64)
        for c in clusters:
            dr, dc = c.draw_shift(rng)
            for f in c.fires:
                tot += counts_at(codes_flat, W, f.rows, f.cols, f.bins, dr, dc)
        s = summarize(tot)
        for t in TYPES:
            null[t].append(s[t]['E'])
        if profile_null:
            null_prof.append(s['profile']['B'])
    res = dict(n_fires=len(fires), n_clusters=k, largest_cluster=max(len(c.fires) for c in clusters), observed=obs, by_type={})
    for t in TYPES:
        b = np.array(boot[t]); z = np.array(null[t]); e = obs[t]['E']
        res['by_type'][t] = dict(E=e, ci95=[float(np.nanpercentile(b, 2.5)), float(np.nanpercentile(b, 97.5))],
                                 null_median=float(np.nanmedian(z)), null_q025=float(np.nanpercentile(z, 2.5)),
                                 null_q975=float(np.nanpercentile(z, 97.5)),
                                 p_shift_upper=float((1 + np.sum(z >= e)) / (1 + len(z))),
                                 p_shift_lower=float((1 + np.sum(z <= e)) / (1 + len(z))))
        r = res['by_type'][t]
        r['decision'] = ('SUPPORTED' if r['ci95'][0] > 1 and r['p_shift_upper'] < 0.025 else
                         'CONTRADICTED' if r['ci95'][1] < 1 and r['p_shift_lower'] < 0.025 else 'INCONCLUSIVE')
    if profile_null:
        P = np.array([[np.nan if v is None else v for v in p] for p in null_prof])
        res['profile_null_B'] = dict(q025=np.nanpercentile(P, 2.5, axis=0).tolist(), q975=np.nanpercentile(P, 97.5, axis=0).tolist(),
                                     median=np.nanmedian(P, axis=0).tolist())
    return res


# ------------------------------------------------------------------ synthetic validation (no real data) -----------
def synth_world(seed, H=2000, W=2000):
    from skimage.draw import line, disk
    rng = np.random.default_rng(seed)
    code = np.zeros((H, W), dtype=np.uint8)
    for _ in range(40):                                   # straight roads, edge to edge
        side = rng.integers(0, 4, 2)
        pts = []
        for s in side:
            u = int(rng.integers(0, H if s < 2 else W))
            pts.append((0, u) if s == 0 else (H - 1, u) if s == 1 else (u, 0) if s == 2 else (u, W - 1))
        rr, cc = line(pts[0][0], pts[0][1], pts[1][0], pts[1][1])
        code[rr, cc] |= 1
        code[np.clip(rr + 1, 0, H - 1), cc] |= 1          # 2 cells thick, so 4-connected fire cannot slip through
    for bit in (2, 4):
        for _ in range(25):
            rr, cc = disk((rng.integers(0, H), rng.integers(0, W)), rng.integers(4, 30), shape=(H, W))
            code[rr, cc] |= bit
    return code, rng


def eden_fire(rng, burnable, r0, c0, target, p=0.55, size=360):
    """Random growth from (r0, c0) through burnable cells in a size x size window; returns window mask and origin."""
    h = size // 2
    wr0, wc0 = r0 - h, c0 - h
    B = burnable[wr0:wr0 + size, wc0:wc0 + size]
    m = np.zeros_like(B); m[h, h] = True
    four = ndimage.generate_binary_structure(2, 1)
    stall = 0
    while m.sum() < target and stall < 30:
        cand = ndimage.binary_dilation(m, four) & ~m & B
        acc = cand & (rng.random(m.shape) < p)
        stall = stall + 1 if not acc.any() else 0
        m |= acc
    m[[0, -1], :] = False; m[:, [0, -1]] = False
    return m, wr0, wc0


def synth_fires(code, rng, n, mechanism, H=2000, W=2000):
    burnable = (code == 0) if mechanism else np.ones_like(code, dtype=bool)
    fires = []
    lo, hi = 210, H - 210
    while len(fires) < n:
        r0, c0 = int(rng.integers(lo, hi)), int(rng.integers(lo, hi))
        if not burnable[r0, c0]:
            continue
        m, wr0, wc0 = eden_fire(rng, burnable, r0, c0, int(rng.integers(1500, 12000)))
        if m.sum() < 500:
            continue
        rows, cols, bins, _ = zone_cells(m)
        fires.append(Fire(f'syn{len(fires)}', rows + wr0, cols + wc0, bins, H, W))
    return fires


def synthetic():
    t0 = time.time(); out = dict(mechanism=[], null=[])
    for k in range(5):                                    # power: planted mechanism
        code, rng = synth_world(100 + k)
        fires = synth_fires(code, rng, 40, True)
        r = analyse(fires, code.ravel(), code.shape[1], n_boot=500, n_shift=300, profile_null=False)
        out['mechanism'].append({t: dict(E=r['by_type'][t]['E'], ci95=r['by_type'][t]['ci95'], p=r['by_type'][t]['p_shift_upper'],
                                         decision=r['by_type'][t]['decision']) for t in TYPES})
        print('mechanism', k, {t: (round(r['by_type'][t]['E'], 3), r['by_type'][t]['decision']) for t in TYPES}, flush=True)
    for k in range(60):                                   # calibration: perimeters independent of barriers
        code, rng = synth_world(200 + k)
        fires = synth_fires(code, rng, 40, False)
        r = analyse(fires, code.ravel(), code.shape[1], n_boot=500, n_shift=300, profile_null=False)
        out['null'].append({t: dict(E=r['by_type'][t]['E'], ci95=r['by_type'][t]['ci95'], p=r['by_type'][t]['p_shift_upper'],
                                    decision=r['by_type'][t]['decision']) for t in TYPES})
        print('null', k, {t: (round(r['by_type'][t]['E'], 3), r['by_type'][t]['decision']) for t in TYPES}, flush=True)
    out['summary'] = dict(
        mechanism_supported_B=sum(m['B']['decision'] == 'SUPPORTED' for m in out['mechanism']),
        null_supported_B=sum(m['B']['decision'] == 'SUPPORTED' for m in out['null']),
        null_contradicted_B=sum(m['B']['decision'] == 'CONTRADICTED' for m in out['null']),
        null_E_B_mean=float(np.mean([m['B']['E'] for m in out['null']])),
        null_any_type_not_inconclusive=sum(m[t]['decision'] != 'INCONCLUSIVE' for m in out['null'] for t in TYPES),
        seconds=round(time.time() - t0, 1))
    out['code_sha256'] = hashlib.sha256(open(__file__, 'rb').read()).hexdigest()
    json.dump(out, open(os.path.join(HERE, 'SYNTHETIC_CHECK.json'), 'w'), indent=1)
    print(json.dumps(out['summary'], indent=1))


# ------------------------------------------------------------------ the real analysis (pilot region) --------------
INPUTS = {k: os.path.join(P1, k) for k in ('compartments_static.npz', 'raw/mtbs_perims.json', 'raw/fpafod_ignitions_blind.json',
                                           'p1_config.json', 'build_predictors.py')}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def load_builder():
    cwd = os.getcwd(); os.chdir(P1)                       # the builder reads p1_config.json from its folder
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('bp', os.path.join(P1, 'build_predictors.py'))
    bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)
    os.chdir(cwd)
    return bp


def build_pilot_fires(bp):
    """MTBS perimeters -> Fire objects with zones, year, wildfire match and burned cells. Reads no barrier map."""
    from rasterio import features
    from rasterio.transform import from_origin
    from shapely.geometry import box
    H, W = bp.H, bp.W
    abox = box(bp.AX0, bp.AY0, bp.AX1, bp.AY1)
    ign = json.load(open(INPUTS['raw/fpafod_ignitions_blind.json']))
    ign_by_year = {}
    for f in ign:
        g = f.get('geometry') or {}
        if g.get('x') is None:
            continue
        r, c = int((bp.Y1 - g['y']) // RES), int((g['x'] - bp.X0) // RES)
        ign_by_year.setdefault(int(f['attributes']['fire_year']), []).append((r, c))
    mt = json.load(open(INPUTS['raw/mtbs_perims.json']))
    pad = int(math.ceil((NB * RES + 2 * RES) / RES))
    fires, skipped = [], dict(no_geometry=0, outside_analysis_box=0, zone_off_grid=0, tiny=0)
    for i, f in enumerate(mt):
        polys = bp.esri_polys([f])
        if not polys:
            skipped['no_geometry'] += 1; continue
        if not any(p.intersects(abox) for p in polys):
            skipped['outside_analysis_box'] += 1; continue
        x0 = min(p.bounds[0] for p in polys); y0 = min(p.bounds[1] for p in polys)
        x1 = max(p.bounds[2] for p in polys); y1 = max(p.bounds[3] for p in polys)
        r0, r1 = int((bp.Y1 - y1) // RES) - pad, int((bp.Y1 - y0) // RES) + pad + 1
        c0, c1 = int((x0 - bp.X0) // RES) - pad, int((x1 - bp.X0) // RES) + pad + 1
        if r0 < 0 or c0 < 0 or r1 > H or c1 > W:
            skipped['zone_off_grid'] += 1; continue
        tf = from_origin(bp.X0 + c0 * RES, bp.Y1 - r0 * RES, RES, RES)
        m = features.rasterize(((p, 1) for p in polys), out_shape=(r1 - r0, c1 - c0), transform=tf,
                               all_touched=False, dtype='uint8').astype(bool)
        if m.sum() < 20:
            skipped['tiny'] += 1; continue
        rows, cols, bins, d_out = zone_cells(m)
        yr = int(f['attributes']['year'])
        matched = False
        for (r, c) in ign_by_year.get(yr, []):
            if r0 <= r < r1 and c0 <= c < c1 and (m[r - r0, c - c0] or d_out[r - r0, c - c0] <= MATCH_M):
                matched = True; break
        fire = Fire(f'mtbs{i}_{yr}', rows + r0, cols + c0, bins, H, W)
        fire.year, fire.matched, fire.burned_cells = yr, matched, int(m.sum())
        fires.append(fire)
    primary = [f for f in fires if f.matched and 1992 <= f.year <= 2024]
    samples = {'primary': primary, 'all_perimeters': fires,
               'primary_before_2010': [f for f in primary if f.year < 2010],
               'primary_2010_on': [f for f in primary if f.year >= 2010]}
    return mt, fires, skipped, samples


def sample_qa():
    bp = load_builder()
    mt, fires, skipped, samples = build_pilot_fires(bp)
    out = dict(note='Sample construction only: rasterization, inclusion, wildfire matching and clustering. No barrier map was read.',
               code_sha256=sha(__file__), mtbs_features=len(mt), included=len(fires), skipped=skipped, samples={})
    for name, fs in samples.items():
        cl = make_clusters(fs) if fs else []
        out['samples'][name] = dict(n_fires=len(fs), n_clusters=len(cl), largest_cluster=max((len(c.fires) for c in cl), default=0),
                                    clusters_without_room=sum(not c.room() for c in cl),
                                    years=[min((f.year for f in fs), default=None), max((f.year for f in fs), default=None)],
                                    burned_cells=int(sum(f.burned_cells for f in fs)), zone_cells=int(sum(len(f.bins) for f in fs)))
    json.dump(out, open(os.path.join(HERE, 'SAMPLE_QA.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


def real():
    t0 = time.time()
    bp = load_builder()
    mt, fires, skipped, samples = build_pilot_fires(bp)
    z = np.load(INPUTS['compartments_static.npz'])
    code = (z['road'].astype(np.uint8) | (z['water'].astype(np.uint8) << 1) | (z['nonburn'].astype(np.uint8) << 2))
    H, W = code.shape
    assert (H, W) == (bp.H, bp.W)
    codes_flat = code.ravel()
    out = dict(question='Do final fire perimeters run along mapped barriers (definition B) more than the land just beyond them?',
               region='P1 pilot (Okanogan, Methow and Chelan, WA); compute grid of p1_config.json',
               input_sha256={k: sha(p) for k, p in INPUTS.items()},
               code_sha256=sha(__file__), plan_sha256=sha(os.path.join(HERE, 'MECH_PLAN.md')),
               mtbs_features=len(mt), included=len(fires), skipped=skipped,
               settings=dict(edge_m=[0, 90], ref_out_m=[150, 600], ref_in_m=[150, 600], shift_m=list(SHIFT_M), match_m=MATCH_M,
                             n_boot=N_BOOT, n_shift=N_SHIFT, seed_boot=SEED_BOOT, seed_shift=SEED_SHIFT),
               samples={})
    for name, fs in samples.items():
        if len(fs) < 5:
            out['samples'][name] = dict(n_fires=len(fs), note='fewer than 5 fires; not analysed'); continue
        r = analyse(fs, codes_flat, W, profile_null=(name == 'primary'))
        r['years'] = [min(f.year for f in fs), max(f.year for f in fs)]
        r['burned_cells'] = int(sum(f.burned_cells for f in fs))
        out['samples'][name] = r
        print(name, r['n_fires'], {t: (round(r['by_type'][t]['E'], 3), [round(v, 3) for v in r['by_type'][t]['ci95']],
                                       round(r['by_type'][t]['p_shift_upper'], 4), r['by_type'][t]['decision']) for t in TYPES}, flush=True)
    out['primary_decision'] = out['samples']['primary']['by_type']['B']['decision']
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(HERE, 'MECH_RESULTS.json'), 'w'), indent=1)
    plot(out)
    print('PRIMARY (E_B, matched wildfires 1992-2024):', out['primary_decision'])


def plot(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r = out['samples']['primary']; prof = r['observed']['profile']
    x = [(b + 0.5) * RES for b in range(-NB, 0)] + [(b - 0.5) * RES for b in range(1, NB + 1)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    ax = axes[0]
    ax.fill_between(x, r['profile_null_B']['q025'], r['profile_null_B']['q975'], color='0.85', label='shift null, 95% band')
    ax.plot(x, prof['B'], color='black', lw=2, label='observed, any barrier (B)')
    ax.axvline(0, color='0.4', lw=0.8, ls='--')
    ax.set_xlabel('signed distance from the final perimeter (m; negative = burned side)')
    ax.set_ylabel('share of cells that are barriers'); ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"Matched wildfires, n = {r['n_fires']}")
    ax = axes[1]
    for t, col in (('road', '#b2182b'), ('water', '#2166ac'), ('nonburn', '#4d9221')):
        ax.plot(x, prof[t], color=col, lw=1.6, label=t)
    ax.axvline(0, color='0.4', lw=0.8, ls='--'); ax.set_xlabel('signed distance from the final perimeter (m)')
    ax.set_title('By barrier type'); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, 'mech_profile.png'), dpi=150)


if __name__ == '__main__':
    {'synthetic': synthetic, 'sample': sample_qa, 'real': real}[sys.argv[1]]()
