#!/usr/bin/env python3
"""Make the primary perimeter input disjoint from the pilot (MECH_PLAN.md §4). Reads perimeters only, no barrier map.

Rule. Drop every P1C MTBS perimeter that intersects the pilot's compute box (p1/p1_config.json compute_box_5070),
widened by 600 m on every side.
- Why that guarantees disjointness: the frozen code kept a pilot fire only if its ±600 m zone fit on the pilot grid,
  with a 22-cell (660 m) pad beyond its bounding box. So every pilot perimeter lies at least 660 m inside the pilot
  compute box.
- A kept P1C perimeter lies at least 600 m outside that box, so it is at least 1,260 m from any pilot perimeter.
- That is more than the 1,200 m at which two ±600 m zones could meet.
- Result: no fire, and no zone cell, is shared with the pilot P1-M sample.

Outputs (this folder): mtbs_perims_disjoint.json (the same JSON layout as the input, with dropped features left out)
and DISJOINT_FILTER.json (counts and the dropped features' indices and years).
Usage: python3 -B make_disjoint_perims.py
"""
import hashlib, importlib.util, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
P1C = '/home/claude/p1c'
SRC = os.path.join(P1C, 'raw/mtbs_perims.json')
WIDEN_M = 600.0
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
sys.dont_write_bytecode = True


def main():
    from shapely.geometry import box
    cwd = os.getcwd(); os.chdir(P1C)                         # the builder reads p1_config.json from its folder
    spec = importlib.util.spec_from_file_location('bp', os.path.join(P1C, 'build_predictors.py'))
    bp = importlib.util.module_from_spec(spec); spec.loader.exec_module(bp)
    os.chdir(cwd)
    x0, y0, x1, y1 = json.load(open('/home/claude/p1/p1_config.json'))['compute_box_5070']
    pilot = box(x0 - WIDEN_M, y0 - WIDEN_M, x1 + WIDEN_M, y1 + WIDEN_M)
    mt = json.load(open(SRC))
    keep, dropped = [], []
    for i, f in enumerate(mt):
        polys = bp.esri_polys([f])
        if polys and any(p.intersects(pilot) for p in polys):
            dropped.append(dict(index=i, year=(f.get('attributes') or {}).get('year')))
        else:
            keep.append(f)
    out = os.path.join(HERE, 'mtbs_perims_disjoint.json')
    json.dump(keep, open(out, 'w'))
    rec = dict(rule='drop P1C perimeters intersecting the pilot compute box widened by 600 m',
               pilot_compute_box_5070=[x0, y0, x1, y1], widen_m=WIDEN_M,
               source=dict(path=SRC, sha256=sha(SRC), features=len(mt)),
               output=dict(path=out, sha256=sha(out), features=len(keep)),
               dropped=dict(count=len(dropped), features=dropped),
               code_sha256=sha(os.path.abspath(__file__)),
               note='Perimeter geometry and pilot configuration only. No barrier map was read.')
    json.dump(rec, open(os.path.join(HERE, 'DISJOINT_FILTER.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k != 'dropped'} | {'dropped_count': len(dropped)}, indent=1))


if __name__ == '__main__':
    main()
