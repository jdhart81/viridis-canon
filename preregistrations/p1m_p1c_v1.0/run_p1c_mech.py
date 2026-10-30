#!/usr/bin/env python3
"""Run the frozen pilot P1-M code on the P1C region, without editing it (MECH_PLAN.md §2).

Before the freeze (no edge statistic is computed):
  python3 -B run_p1c_mech.py sample primary   # disjoint sample -> SAMPLE_QA.json (+ robustness subset sizes)
  python3 -B run_p1c_mech.py sample full      # all P1C perimeters -> full_sample/SAMPLE_QA.json
  python3 -B run_p1c_mech.py union            # road classes vs the frozen road raster, no perimeters -> UNION_CHECK.json
After the freeze and the public registration:
  python3 -B run_p1c_mech.py real primary     # H1 and all types -> MECH_RESULTS.json, mech_profile.png
  python3 -B run_p1c_mech.py roads            # H2 and road classes, disjoint sample -> ROADS_CHECKS.json
  python3 -B run_p1c_mech.py robust           # descriptive subsets of the disjoint sample -> ROBUST.json
  python3 -B run_p1c_mech.py real full        # secondary: all P1C perimeters -> full_sample/MECH_RESULTS.json
  python3 -B run_p1c_mech.py decide           # readings under the plan -> P1M_P1C_DECISIONS.json

Invariants (asserted):
  R1  p1mech/mech_test.py and p1mech/posthoc_roads.py have their frozen sha256 values.
  R2  Only module-level settings change: the input folder (P1), the input table (INPUTS) and the output folder
      (HERE). No frozen function is replaced or edited. 'robust' calls the frozen analyse() on subsets of fires
      that the frozen build_pilot_fires() produced.
  R3  real, roads and robust refuse to run unless MECH_FREEZE.json matches the current files and
      REGISTRATION_P1M.json records a public copy identical to every frozen local file.
  R4  The frozen code's own fields are kept as written. The runner adds fields under new names only.
  R5  Each result file is stamped with OpenTimestamps immediately after it is written.
"""
import hashlib, importlib.util, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FULL = os.path.join(HERE, 'full_sample')
PILOT = '/home/claude/p1mech'
P1C = '/home/claude/p1c'
FROZEN = {'mech_test.py': '85d4f45f4a6b0e2009e5fd0783040655c13a4487f15f221371219863d2760893',
          'posthoc_roads.py': 'd61013e972208721d3fbe08fab129ff79f3f1892daf148b5c6040bfb00adcfff'}
REGION = ('P1C region: northeast Washington (eastern Okanogan, Ferry, Stevens and Pend Oreille counties); '
          'compute grid of p1c/p1_config.json')
NORTH_LAT = 49.0
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
sys.dont_write_bytecode = True

for f, h in FROZEN.items():                                                                   # R1
    assert sha(os.path.join(PILOT, f)) == h, f'R1: {f} is not the frozen pilot code'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inputs(variant):
    perims = os.path.join(HERE, 'mtbs_perims_disjoint.json') if variant == 'primary' else os.path.join(P1C, 'raw/mtbs_perims.json')
    return {'compartments_static.npz': os.path.join(P1C, 'compartments_static.npz'),
            'raw/mtbs_perims.json': perims,
            'raw/fpafod_ignitions_blind.json': os.path.join(P1C, 'raw/fpafod_ignitions_blind.json'),
            'p1_config.json': os.path.join(P1C, 'p1_config.json'),
            'build_predictors.py': os.path.join(P1C, 'build_predictors.py')}


def point_at_p1c(mt, variant):
    """R2: settings only."""
    mt.P1 = P1C
    mt.INPUTS = inputs(variant)
    mt.HERE = HERE if variant == 'primary' else FULL


def require_freeze_and_registration():
    """R3."""
    fz = os.path.join(HERE, 'MECH_FREEZE.json')
    assert os.path.exists(fz), 'R3: not frozen (MECH_FREEZE.json missing)'
    for rel, h in json.load(open(fz))['sha256'].items():
        assert sha(rel if rel.startswith('/') else os.path.join(HERE, rel)) == h, f'R3: {rel} changed since the freeze'
    reg = os.path.join(HERE, 'REGISTRATION_P1M.json')
    assert os.path.exists(reg), 'R3: no public registration recorded (REGISTRATION_P1M.json missing)'
    files = json.load(open(reg))['registered_files']
    for must in ('MECH_PLAN.md', 'MECH_FREEZE.json', 'MECH_FREEZE.json.ots', 'run_p1c_mech.py', 'mtbs_perims_disjoint.json'):
        assert must in files, f'R3: {must} is not in the registered record'
    for rel, rec in files.items():
        assert rec['sha256'] == sha(os.path.join(HERE, rel)), f'R3: the registered {rel} is not the local frozen file'


def annotate(path, extra):
    """R4."""
    out = json.load(open(path))
    clash = set(extra) & set(out)
    assert not clash, f'R4: would overwrite {clash}'
    out.update(extra)
    json.dump(out, open(path, 'w'), indent=1)


def stamp(*paths):
    """R5: stamp every output and assert that each proof was written."""
    for path in paths:
        r = subprocess.run(['ots', 'stamp', path], capture_output=True, text=True, timeout=180)
        print('ots stamp', os.path.basename(path), r.returncode, flush=True)
        assert os.path.exists(path + '.ots'), f'R5: OpenTimestamps proof not written for {path}'


def check_versions():
    """The libraries must be those recorded by the union check before the freeze."""
    import numpy as np, platform, rasterio, scipy, shapely, pyproj
    now = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__, rasterio=rasterio.__version__,
               gdal=rasterio.__gdal_version__, shapely=shapely.__version__, pyproj=pyproj.__version__)
    rec = json.load(open(os.path.join(HERE, 'UNION_CHECK.json')))['versions']
    assert now == rec, f'library versions differ from UNION_CHECK.json: {now} vs {rec}'


def runner_note():
    return dict(script='run_p1c_mech.py', sha256=sha(os.path.abspath(__file__)),
                note='Fields region_p1c, plan_primary, robustness_subsets and runner were added by the runner. The frozen '
                     'code labels its output with the pilot region and names E_B as its primary; MECH_PLAN.md names E_road (H1).')


def fire_lats_max(fires, bp):
    """Largest latitude of each fire's zone cells (perimeter geometry only)."""
    from pyproj import Transformer
    import numpy as np
    tr = Transformer.from_crs('EPSG:5070', 'EPSG:4326', always_xy=True)
    out = []
    for f in fires:
        x = bp.X0 + (np.asarray(f.cols) + 0.5) * bp.RES
        y = bp.Y1 - (np.asarray(f.rows) + 0.5) * bp.RES
        _, lat = tr.transform(x, y)
        out.append(float(np.max(lat)))
    return out


def robustness_subsets(mt, fires, bp):
    """The plan's descriptive subsets (§6): defined from perimeters and zones only."""
    cl = mt.make_clusters(fires)
    biggest = max(cl, key=lambda c: len(c.fires))
    big = {id(f) for f in biggest.fires}
    lats = fire_lats_max(fires, bp)
    return {'without_largest_cluster': [f for f in fires if id(f) not in big],
            'without_zones_north_of_49N': [f for f, la in zip(fires, lats) if la <= NORTH_LAT]}


def main(mode, variant):
    if mode == 'sample':
        assert variant in ('primary', 'full')
        mt = load('mt', os.path.join(PILOT, 'mech_test.py')); point_at_p1c(mt, variant)
        os.makedirs(mt.HERE, exist_ok=True)
        if variant == 'full':                                    # the frozen code hashes MECH_PLAN.md in its HERE
            open(os.path.join(FULL, 'MECH_PLAN.md'), 'wb').write(open(os.path.join(HERE, 'MECH_PLAN.md'), 'rb').read())
        mt.sample_qa()
        extra = dict(region_p1c=REGION, variant=variant, runner=runner_note())
        if variant == 'primary':
            bp = mt.load_builder(); _, _, _, samples = mt.build_pilot_fires(bp)
            subs = robustness_subsets(mt, samples['primary'], bp)
            extra['robustness_subsets'] = {k: dict(n_fires=len(v), n_clusters=len(mt.make_clusters(v)) if v else 0)
                                           for k, v in subs.items()}
        annotate(os.path.join(mt.HERE, 'SAMPLE_QA.json'), extra)
    elif mode == 'union':
        import numpy as np, platform, rasterio, scipy, shapely, pyproj
        ph = load('ph', os.path.join(PILOT, 'posthoc_roads.py'))
        point_at_p1c(ph.mt, 'primary')
        bp = ph.mt.load_builder()
        road = np.load(ph.mt.INPUTS['compartments_static.npz'])['road']
        raw = []
        for fn in ('roads_primary.json', 'roads_secondary.json', 'roads_local.json'):
            raw += json.load(open(os.path.join(P1C, 'raw', fn)))
        cls = {name: bp.burn(bp.esri_lines(raw, keep=lambda a, m=m: a.get('MTFCC') in m)) for name, m in ph.CLASSES.items()}
        union = cls['highway'] | cls['local'] | cls['other_vehicle']
        rec = dict(note='Road classes rasterized with the builder functions and compared with the frozen road raster. '
                        'No perimeter was read.',
                   union_equals_frozen_road_raster=bool(np.array_equal(union, road)),
                   class_cells={k: int(v.sum()) for k, v in cls.items()}, road_cells=int(road.sum()),
                   versions=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                                 rasterio=rasterio.__version__, gdal=rasterio.__gdal_version__, shapely=shapely.__version__,
                                 pyproj=pyproj.__version__),
                   runner=runner_note())
        json.dump(rec, open(os.path.join(HERE, 'UNION_CHECK.json'), 'w'), indent=1)
        print(json.dumps(rec, indent=1))
    elif mode == 'real':
        assert variant in ('primary', 'full')
        require_freeze_and_registration()
        mt = load('mt', os.path.join(PILOT, 'mech_test.py')); point_at_p1c(mt, variant)
        mt.real()
        path = os.path.join(mt.HERE, 'MECH_RESULTS.json')
        road = json.load(open(path))['samples']['primary']['by_type']['road']
        annotate(path, dict(region_p1c=REGION, variant=variant,
                            plan_primary=dict(hypothesis='H1: E_road > 1, primary sample' + (' (disjoint)' if variant == 'primary'
                                                                                              else ' (secondary: all perimeters)'),
                                              decision=road['decision']),
                            runner=runner_note()))
        stamp(path, os.path.join(mt.HERE, 'mech_profile.png'))
    elif mode == 'roads':
        require_freeze_and_registration()
        check_versions()
        ph = load('ph', os.path.join(PILOT, 'posthoc_roads.py'))
        point_at_p1c(ph.mt, 'primary')
        ph.HERE = HERE
        ph.main()
        out = json.load(open(os.path.join(HERE, 'POSTHOC_ROADS.json')))
        out['note_p1c'] = ('Pre-specified in MECH_PLAN.md (H2 and road classes). The code is the pilot post hoc check, '
                           'hash-recorded but not frozen before its pilot run; it is run unchanged. Its own note is kept.')
        out['region_p1c'] = REGION
        out['runner'] = runner_note()
        path = os.path.join(HERE, 'ROADS_CHECKS.json')
        json.dump(out, open(path, 'w'), indent=1)
        stamp(path, os.path.join(HERE, 'POSTHOC_ROADS.json'))
    elif mode == 'robust':
        require_freeze_and_registration()
        import numpy as np
        mt = load('mt', os.path.join(PILOT, 'mech_test.py')); point_at_p1c(mt, 'primary')
        bp = mt.load_builder(); _, _, _, samples = mt.build_pilot_fires(bp)
        z = np.load(mt.INPUTS['compartments_static.npz'])
        code = (z['road'].astype(np.uint8) | (z['water'].astype(np.uint8) << 1) | (z['nonburn'].astype(np.uint8) << 2))
        res = {}
        recorded = json.load(open(os.path.join(HERE, 'SAMPLE_QA.json')))['robustness_subsets']
        subs = robustness_subsets(mt, samples['primary'], bp)
        for name, fs in subs.items():
            assert len(fs) == recorded[name]['n_fires'], f'{name}: {len(fs)} fires, but {recorded[name]["n_fires"]} were recorded before the freeze'
        for name, fs in subs.items():
            if len(fs) < 5:
                res[name] = dict(n_fires=len(fs), note='fewer than 5 fires; not analysed'); continue
            r = mt.analyse(fs, code.ravel(), code.shape[1], profile_null=False)
            res[name] = dict(n_fires=r['n_fires'], n_clusters=r.get('n_clusters'),
                             by_type={t: {k: r['by_type'][t][k] for k in ('E', 'ci95', 'p_shift_upper', 'p_shift_lower', 'decision')}
                                      for t in mt.TYPES})
            print(name, {t: (round(res[name]['by_type'][t]['E'], 3), res[name]['by_type'][t]['decision']) for t in mt.TYPES}, flush=True)
        path = os.path.join(HERE, 'ROBUST.json')
        json.dump(dict(note='Descriptive subsets pre-specified in MECH_PLAN.md §6; frozen analyse(), unchanged.',
                       region_p1c=REGION, subsets=res, runner=runner_note()), open(path, 'w'), indent=1)
        stamp(path)
    elif mode == 'decide':
        r = json.load(open(os.path.join(HERE, 'MECH_RESULTS.json')))
        q = json.load(open(os.path.join(HERE, 'ROADS_CHECKS.json')))
        h1 = r['samples']['primary']['by_type']['road']
        reading1 = {'SUPPORTED': 'REPLICATED', 'INCONCLUSIVE': 'NOT REPLICATED (inconclusive)',
                    'CONTRADICTED': 'CONTRADICTED'}[h1['decision']]
        c2 = q['checks']['B_road_away_from_valley_floors']
        finite = all(map(lambda v: v == v and abs(v) != float('inf'), [c2['E'], *c2['ci95']]))
        h2_dec = 'SUPPORTED' if finite and c2['ci95'][0] > 1 and c2['p_shift_upper'] < 0.025 else 'NOT SUPPORTED'
        if h1['decision'] != 'SUPPORTED':
            reading2 = 'not tested confirmatorily (H1 not SUPPORTED); reported descriptively'
        elif h2_dec == 'SUPPORTED':
            reading2 = 'the road edge excess holds away from valley floors'
        elif finite and c2['ci95'][1] < 1.10:
            reading2 = 'valley floors account for the excess: no excess of 10% or more away from them'
        else:
            reading2 = 'away from valley floors: undetermined'
        def rule2(c):
            ok = all(map(lambda v: v == v and abs(v) != float('inf'), [c['E'], *c['ci95']]))
            return 'SUPPORTED' if ok and c['ci95'][0] > 1 and c['p_shift_upper'] < 0.025 else 'NOT SUPPORTED'
        dec = dict(H1_road=dict(E=h1['E'], ci95=h1['ci95'], p_shift_upper=h1['p_shift_upper'], p_shift_lower=h1.get('p_shift_lower'),
                                decision=h1['decision'], reading=reading1,
                                pilot_E_1_45_inside_ci=bool(h1['ci95'][0] <= 1.445 <= h1['ci95'][1])),
                   H2_road_away_from_valley_floors=dict(E=c2['E'], ci95=c2['ci95'], p_shift_upper=c2['p_shift_upper'],
                                                        n_fires=c2['n_fires'], n_clusters=c2['n_clusters'],
                                                        decision=h2_dec, reading=reading2),
                   road_classes={k[2:]: dict(E=v['E'], ci95=v['ci95'], p_shift_upper=v['p_shift_upper'], decision=rule2(v))
                                 for k, v in q['checks'].items() if k.startswith('A_')},
                   types_primary_sample={t: dict(E=v['E'], ci95=v['ci95'], decision=v['decision'])
                                         for t, v in r['samples']['primary']['by_type'].items()},
                   n_fires=r['samples']['primary']['n_fires'], runner=runner_note())
        path = os.path.join(HERE, 'P1M_P1C_DECISIONS.json')
        json.dump(dec, open(path, 'w'), indent=1)
        stamp(path)
        print(json.dumps(dec, indent=1))
    else:
        sys.exit('mode must be sample, union, real, roads, robust or decide')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '', sys.argv[2] if len(sys.argv) > 2 else 'primary')
