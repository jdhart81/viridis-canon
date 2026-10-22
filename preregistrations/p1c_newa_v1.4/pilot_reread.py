#!/usr/bin/env python3
"""The pilot re-read for plan v1.4, section 1 (exploratory; pilot Deviations 2 and 3). Writes PILOT_REREAD.json.

How strong is the pilot's B result under the credible set of error models? CALIBRATION.json re-reads the pilot under
the models that bind on THIS region's design, but the models that most inflate |T| on the smaller pilot design can be
different. Here every boundary model of the credible set is simulated on the PILOT's own design: for each range, the
field with the largest retained share; the block model with the largest retained share; plus the reference models
(iid, the plug-in block model, blocks + field); and every retained model of the plan v1.4 stress set
(CRITICAL_VALUES.json: exact anisotropic and long-range fields, compartment effects), drawn on the pilot's own points
and compartments. 5,000 null replicates each; both statistics from the same draws:
  M2R (the confirmatory primary; pilot T = 2.98, Deviation 3) and M2 (the pilot's model; pilot T = 2.31).
Reports, per model, the two-sided p of the pilot's T and the 5% and 2.5% critical values. No confirmatory outcome is
used. Two worker processes. Usage: python3 pilot_reread.py"""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1'); os.environ.setdefault('OMP_NUM_THREADS', '1')
import hashlib, importlib.util, json, multiprocessing as mp, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import simcal  # noqa: E402

spec = importlib.util.spec_from_file_location('rt', os.path.join(HERE, 'run_test.py')); rt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rt)
assert not os.path.exists(os.path.join(HERE, 'outcomes.csv'))
CAL = json.load(open(os.path.join(HERE, 'CALIBRATION.json')))
CV = json.load(open(os.path.join(HERE, 'CRITICAL_VALUES.json')))
STRESS = CV['stress_set']['models']
T_OBS = CAL['pilot_reread']['T_obs']
pp = rt.add_regions(pd.read_csv('/home/claude/p1/predictors_blind.csv'))
DR, D0 = simcal.Design(rt, pp, fes=rt.FES_R), simcal.Design(rt, pp, fes=rt.FES)
xs, ys = pp['x'].values[DR.pos].astype(float), pp['y'].values[DR.pos].astype(float)
es = pp['erc_pct'].fillna(0.5).values[DR.pos]
_s, _ = rt.sample(pp.assign(fire_size=1.0), 'B')
_labP = np.load('/home/claude/p1/compartments_static.npz')['labB']
_, INV_P = np.unique(_labP[_s['row'].values, _s['col'].values], return_inverse=True)
names = ['iid', 'block', 'block_exp']
blocks = [g for g in CAL['block_grid'] if g['retained']]
names.append(f"block_s{max(g['block_share'] for g in blocks):.3f}")
for r, c in CAL['closure_by_range_km'].items():
    if c['max_retained_share'] is not None:
        names.append(f"field_s{c['max_retained_share']:.3f}_r{float(r):.0f}")
assert all(n in CAL['models'] for n in names), [n for n in names if n not in CAL['models']]
names += ['stress:' + n for n in STRESS]


def job(arg):
    k, name = arg
    if name.startswith('stress:'):
        mod = STRESS[name.split(':', 1)[1]]
        errs = simcal.StressErrors(mod, xs, ys, INV_P if mod['kind'] == 'comp' else None)
        TmR, _, Tm0, _ = simcal.null_t_pair_stress(DR, D0, es, errs, 5000, 61_000_000 + 100_000 * k)
    else:
        mod = CAL['models'][name]
        model = {kk: mod[kk] for kk in ('var_total', 'block_share', 'field_share', 'range_km') if kk in mod}
        TmR, _, Tm0, _ = simcal.null_t_pair(DR, D0, xs, ys, es, model, 5000, 61_000_000 + 100_000 * k)
    row = {}
    for key, Tm in (('M2R', TmR), ('M2', Tm0)):
        a = np.abs(Tm)
        row[key] = dict(p_two_sided=float(np.mean(a >= T_OBS[key])), c_5pct=float(np.quantile(a, 0.95)), c_2p5pct=float(np.quantile(a, 0.975)))
    return name, row


if __name__ == '__main__':
    out = dict(T_obs=T_OBS, design=dict(n=DR.n, blocks=DR.nblocks, regions_40km=int(pp.loc[pp.index[DR.pos], 'region40'].nunique()),
                                        k_M2R=DR.k, k_M2=D0.k), reps=5000, models={})
    with mp.get_context('fork').Pool(2) as pool:
        for name, row in pool.imap(job, list(enumerate(names))):
            out['models'][name] = row
            print(f"{name:22s} M2R p {row['M2R']['p_two_sided']:.4f} c5 {row['M2R']['c_5pct']:.3f} c2.5 {row['M2R']['c_2p5pct']:.3f} | "
                  f"M2 p {row['M2']['p_two_sided']:.4f} c5 {row['M2']['c_5pct']:.3f} c2.5 {row['M2']['c_2p5pct']:.3f}", flush=True)
    sp = [n for n in names if n != 'iid']
    for key in ('M2R', 'M2'):
        c5 = max(out['models'][n][key]['c_5pct'] for n in sp); c25 = max(out['models'][n][key]['c_2p5pct'] for n in sp)
        out[f'summary_{key}'] = dict(T=T_OBS[key], max_c_5pct=c5, max_c_2p5pct=c25, supported_5pct=bool(T_OBS[key] > c5),
                                     supported_2p5pct=bool(T_OBS[key] > c25),
                                     max_p=max(out['models'][n][key]['p_two_sided'] for n in sp))
    out['code_sha256'] = {f: hashlib.sha256(open(os.path.join(HERE, f), 'rb').read()).hexdigest()
                          for f in ('run_test.py', 'simcal.py', 'pilot_reread.py', 'CALIBRATION.json', 'CRITICAL_VALUES.json')}
    json.dump(out, open(os.path.join(HERE, 'PILOT_REREAD.json'), 'w'), indent=1)
    print(json.dumps({k: out[k] for k in ('summary_M2R', 'summary_M2')}, indent=1))
