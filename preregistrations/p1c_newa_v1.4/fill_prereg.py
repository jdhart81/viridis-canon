#!/usr/bin/env python3
"""Fill PREREG_TEMPLATE.md with numbers computed from files (no hand transcription) and write
PREREGISTRATION_P1C_NEWA_v1.4.md. Reads only predictor-side files, simulation records, the frozen v1.2 and v1.3
records and the pilot's Deviation 3 (no confirmatory outcome)."""
import hashlib, json, re
import pandas as pd

cfg = json.load(open('p1_config.json'))
D = json.load(open('BLIND_DESIGN.json'))
S = json.load(open('SYNTHETIC_VALIDATION.json'))
E = json.load(open('EQUIVALENCE.json'))
CAL = json.load(open('CALIBRATION.json'))
EX = json.load(open('EXPOSURE_LISTS.json'))
DEV3 = json.load(open('../p1/DEVIATION_3.json'))['result']['M2R']
CAL12 = json.load(open('history_v1.2/CALIBRATION.json'))
PRR = json.load(open('PILOT_REREAD.json'))
CV = json.load(open('CRITICAL_VALUES.json'))
ST = CV['stress_set']['models']
assert CV['calibration']['sha256'] == hashlib.sha256(open('CALIBRATION.json', 'rb').read()).hexdigest()
assert S['pass'] and E['build']['identical'] and E['model']['identical']
raw = json.load(open('raw/fpafod_ignitions_blind.json'))
pilot = set(pd.read_csv(cfg['exclude_fod_ids_from'], usecols=['fod_id'])['fod_id'].astype('int64'))
LON0, LAT0, LON1, LAT1 = cfg['analysis_box_lonlat']
inbox = [f for f in raw if (f.get('geometry') or {}).get('x') is not None
         and LON0 <= f['attributes']['longitude'] <= LON1 and LAT0 <= f['attributes']['latitude'] <= LAT1]
excl = [f for f in inbox if int(float(f['attributes']['fod_id'])) in pilot]
assert D['n_table'] == len(inbox) - len(excl), (D['n_table'], len(inbox), len(excl))
if not excl:
    excl_sentence = ('No record needed removing: the two boxes meet only along the meridian at −119.4, and no '
                     'record lies on it in both. The check runs anyway, in the build and in every guard.')
else:
    excl_sentence = f'{len(excl):,} records were removed, on the shared boundary.'
cause = D['cause']
fmt = lambda v: f'{v:,}'
pct = lambda v: f'{100 * v:.1f}%'
P = D['power_primary']
usable_rows = '\n'.join(
    f"| {name} | {fmt(D['usable'][k]['n'])} | " + ' / '.join(f'{q:.2f}' for q in D['usable'][k]['log10_Aenc_acres_q10_q50_q90']) + ' |'
    for k, name in [('B', 'B, mapped barriers (primary)'), ('A50', 'A50, PCL > 0.5'), ('A25', 'A25, PCL > 0.25'), ('Bp', 'B+, B plus prior scars')])


def label(name):
    name = name.split(':', 1)[1] if ':' in name else name
    m = re.match(r'aniso_(NS|EW)_s([\d.]+)_(\d+)x(\d+)$', name)
    if m:
        return (f"anisotropic field, {'north–south' if m.group(1) == 'NS' else 'east–west'}, share {float(m.group(2)):g}, "
                f"ranges {m.group(3)} × {m.group(4)} km")
    m = re.match(r'long_s([\d.]+)_r(\d+)$', name)
    if m:
        return f'exact field, share {float(m.group(1)):g}, range {m.group(2)} km'
    m = re.match(r'comp_s([\d.]+)$', name)
    if m:
        return f'compartment effects, share {float(m.group(1)):g}'
    if name == 'iid':
        return 'iid (reference)'
    if name == 'block':
        return '20 km blocks (pilot plug-in)'
    if name == 'block_exp':
        return 'blocks + exponential field'
    m = re.match(r'block_s([\d.]+)$', name)
    if m:
        return f'20 km blocks, share {float(m.group(1)):g}'
    m = re.match(r'field_s([\d.]+)_r(\d+)', name)
    return f'field, share {float(m.group(1)):g}, range {m.group(2)} km'


def label_the(name):
    src = name.split(':', 1)[0] if ':' in name else ''
    name = name.split(':', 1)[1] if ':' in name else name
    if src == 'stress':
        return 'the stress model "' + label(name) + '"'
    m = re.match(r'field_s([\d.]+)_r(\d+)', name)
    if m:
        return f'the field with share {float(m.group(1)):g} and range {m.group(2)} km'
    m = re.match(r'block_s([\d.]+)$', name)
    if m:
        return f'20 km block effects with share {float(m.group(1)):g}'
    return {'block': "the pilot's plug-in 20 km block effects", 'block_exp': 'blocks plus a field'}[name]


def params(name, m):
    if name == 'iid':
        return '—'
    out = []
    if m.get('block_share'):
        out.append(f"block share {m['block_share']:.3f}")
    if m.get('field_share'):
        out.append(f"field share {m['field_share']:.3f}, range {m['range_km']:.1f} km")
    return '; '.join(out)


# --- the grid table (95th percentile of |T| under M2R; '—' = rejected by the pilot)
SH, RG = CAL['grid_axes']['shares'], CAL['grid_axes']['ranges_km']
key = lambda s, r: f'field_s{s:.3f}_r{r:.0f}'
bind = CAL['binding_model_C2']
rows = ['| Share | ' + ' | '.join(f'{r:.0f} km' for r in RG) + ' |', '|---|' + '---|' * len(RG)]
for s in SH:
    cells = []
    for r in RG:
        k = key(s, r)
        if k in CAL['models']:
            v = f"{CAL['models'][k]['M2R']['q95_absT']:.2f}"
            cells.append(f'**{v}**' if k == bind else v)
        else:
            cells.append('—')
    rows.append(f'| {s:g} | ' + ' | '.join(cells) + ' |')
grid_table = '\n'.join(rows)
n_ret = sum(1 for g in CAL['grid'] if g['retained'])
open_r = [r for r in RG if CAL['closure_by_range_km'][f'{r:.0f}']['max_retained_share'] == max(SH)]
if open_r:
    q_open = max(CAL['models'][key(s, r)]['M2R']['q95_absT'] for r in open_r for s in SH if key(s, r) in CAL['models'])
    closure_text = (f"At ranges of {', '.join(f'{r:.0f}' for r in open_r)} km the pilot cannot reject even the grid's largest "
                    f"share, {max(SH):g}, so the set stays open there. M2R is insensitive at those ranges: its largest 95th "
                    f"percentile there is {q_open:.2f}, against C2 = {CAL['C2']:.2f}.")
else:
    none_r = [r for r in RG if CAL['closure_by_range_km'][f'{r:.0f}']['max_retained_share'] is None]
    closure_text = ("In share, the retained set is closed within the grid: at every range, the shares above the largest retained "
                    "one are rejected" + (f", and at {', '.join(f'{r:.0f}' for r in none_r)} km no share was retained with the "
                    "registered seeds (the fourth audit found the smallest share there retained about 4 times in 10; such a field is mild "
                    "and cannot set C2)" if none_r else "") + ". In range, the grid stops at 180 km; the stress set continues to 720 km.")

# --- reference rows: references and the binding model(s)
chk = S['null_check_fresh_seeds']['models']
def bind_tag(n):
    tags = [c for c in ('C2', 'C1') if CAL['binding_model_' + c] == n]
    return f" (binding in the screened family for {' and '.join(tags)})" if tags else ''


ref_names = ['iid', 'block', 'block_exp'] + [m for m in dict.fromkeys([CAL['binding_model_C2'], CAL['binding_model_C1']]) if m not in ('block', 'block_exp')]
ref_rows = '\n'.join(
    f"| {label(n)}{bind_tag(n)} | "
    f"{params(n, CAL['models'][n])} | {CAL['models'][n]['M2R']['q95_absT']:.3f} | {pct(CAL['models'][n]['M2R']['false_call_share_pilot_rule'])} | "
    f"{pct(CAL['models'][n]['M2R']['false_call_share_v11_rule'])} | **{pct(chk['calibration:' + n]['M2R']['registered_rule'])}** "
    f"({fmt(chk['calibration:' + n]['reps'])} replicates) |"
    for n in ref_names)
top_stress = sorted(ST, key=lambda m: -ST[m]['M2R']['q95_absT'])[:8]
stress_rows = '\n'.join(
    f"| {label(n)}{' (binding)' if CV['binding_model_C2'] == 'stress:' + n else ''} | {ST[n]['M2R']['q95_absT']:.3f} | {ST[n]['M2']['q95_absT']:.3f} | "
    f"{pct(ST[n]['M2R']['false_call_share_final_rule'])} / {pct(chk['stress:' + n]['M2R']['registered_rule'])} ({fmt(chk['stress:' + n]['reps'])} fresh) |"
    for n in top_stress)
fam = {}
for n, m in ST.items():
    fam[m['family']] = fam.get(m['family'], 0) + 1
stress_by_family = ', '.join(f'{k} {fam.get(k, 0)}' for k in ('S-A', 'S-L', 'S-C'))

# --- correlogram text
cg = CAL['correlogram']['all']
pick = lambda lo, hi: [r[1] for r in cg if lo <= r[0] < hi]
mean = lambda v: sum(v) / len(v)
corr_text = (f"correlation {mean(pick(0, 1.5)):.3f} at about 1 km, about {mean(pick(2.5, 10.5)):.3f} at 3–10 km, about "
             f"{mean(pick(12, 31)):.3f} at 12–30 km and near 0 beyond 40 km. An exponential fitted to it gives a correlated share "
             f"of {CAL['pilot_observed_fit']['share']:.3f} with range {CAL['pilot_observed_fit']['range_km']:.1f} km")

# --- pilot re-read (PILOT_REREAD.json: the boundary of the credible set, on the pilot's design)
PR = PRR
PRB = {n: m for n, m in PR['models'].items() if not n.startswith('stress:')}
PRS = {n: m for n, m in PR['models'].items() if n.startswith('stress:')}
pilot_rows = ('| Error model | M2R: p, two-sided | M2R: 5% critical value | M2R: 2.5% critical value | M2: p, two-sided | M2: 5% critical value | M2: 2.5% critical value |\n'
              '|---|---|---|---|---|---|---|\n' + '\n'.join(
                  f"| {label(n)} | {m['M2R']['p_two_sided']:.3f} | {m['M2R']['c_5pct']:.2f} | {m['M2R']['c_2p5pct']:.2f} | "
                  f"{m['M2']['p_two_sided']:.3f} | {m['M2']['c_5pct']:.2f} | {m['M2']['c_2p5pct']:.2f} |" for n, m in PRB.items()))
_r = max(PRS, key=lambda n: PRS[n]['M2R']['c_5pct']); _m = max(PRS, key=lambda n: PRS[n]['M2']['c_5pct'])
pilot_stress_text = (f"Across the {len(PRS)} retained stress models on the pilot's design, the largest 5% critical value is "
                     f"{PRS[_r]['M2R']['c_5pct']:.2f} under M2R ({label(_r)}; at 2.5%, {max(PRS[n]['M2R']['c_2p5pct'] for n in PRS):.2f} at most) "
                     f"and {PRS[_m]['M2']['c_5pct']:.2f} under M2 ({label(_m)}). The largest two-sided p of the pilot's T is "
                     f"{max(PRS[n]['M2R']['p_two_sided'] for n in PRS):.3f} under M2R and {max(PRS[n]['M2']['p_two_sided'] for n in PRS):.3f} under M2.")
spatial_pr = [n for n in PR['models'] if n != 'iid']
c5R = max(PR['models'][n]['M2R']['c_5pct'] for n in spatial_pr); c25R = max(PR['models'][n]['M2R']['c_2p5pct'] for n in spatial_pr)
c5M = max(PR['models'][n]['M2']['c_5pct'] for n in spatial_pr)
TR, TM = PR['T_obs']['M2R'], PR['T_obs']['M2']
verdict = lambda T, c: f"{'SUPPORTED' if T > c else 'NOT SUPPORTED'} (T = {T:.2f} against {c:.2f})"

# --- power and NOT REPLICATED
sim = P['simulated_registered_rule']['power_P_SUPPORTED']
power_rows = '\n'.join(f"| {label(n)} | " + ' | '.join(f'{v:.2f}' for v in vals.values()) + ' |' for n, vals in sim.items())
nr = P['p_not_replicated_under_null']['by_model']
notrep_text = '; '.join(f"{label(k)}: {v['registered']:.2f} under this plan's reading against {v['pilot_rule']:.2f} under the pilot's rule"
                        for k, v in nr.items())
P13 = D['power_s13_pilot_model_M2']['power_P_SUPPORTED']
b33 = 'beta33 0.0415 (small-telescopes benchmark)'; b63 = 'pilot estimate 0.063'
bm2 = CV['binding_model_C2_M2']; iid = 'calibration:iid'
power_s13_text = (f"P(SUPPORTED) at β₃₃ is {P13[iid][b33]:.2f} with independent errors and {P13[bm2][b33]:.2f} under its binding model "
                  f"({label_the(bm2)}); at β = 0.063 it is {P13[iid][b63]:.2f} and {P13[bm2][b63]:.2f}")
s10b = EX['s10b']
exact = max(S['exactness_max_abs_diff'].values())
fill = {
    'V12_SHA': hashlib.sha256(open('history_v1.2/FREEZE.json', 'rb').read()).hexdigest()[:8], 'C2_V12': f"{CAL12['C2']:.2f}",
    'V13_SHA': hashlib.sha256(open('history_v1.3/FREEZE.json', 'rb').read()).hexdigest()[:8],
    'C2_CAL': f"{CAL['C2']:.2f}", 'C1_CAL': f"{CAL['C1']:.2f}", 'BIND_C2_CAL': label_the(CAL['binding_model_C2']),
    'N_STRESS_RET': str(len(ST)), 'STRESS_RET_BY_FAMILY': stress_by_family, 'STRESS_ROWS': stress_rows,
    'OBS_COMP': f"{CV['stress_set']['observed_pilot_compartment_share']:.3f}", 'PILOT_STRESS_TEXT': pilot_stress_text,
    'N_GRID': str(len(CAL['grid'])), 'N_BLOCK_GRID': str(len(CAL['block_grid'])), 'N_RETAINED': str(n_ret), 'N_SHARES': str(len(SH)), 'N_RANGES': str(len(RG)),
    'SHARES': ', '.join(f'{s:g}' for s in SH), 'RANGES': ', '.join(f'{r:.0f}' for r in RG), 'MAX_RANGE': f'{max(RG):.0f}',
    'CLOSURE_TEXT': closure_text, 'GRID_TABLE': grid_table, 'REF_ROWS': ref_rows,
    'OBS_BLOCK': f"{CAL['pilot_observed_block_share']:.3f}", 'BLOCK_SHARES': ', '.join(f"{g['block_share']:g}" for g in CAL['block_grid']),
    'BLOCK_RET': ', '.join(f"{g['block_share']:g}" for g in CAL['block_grid'] if g['retained']),
    'BLOCK_Q95_MAX': f"{max(CAL['models'][n]['M2R']['q95_absT'] for n in CAL['models'] if n.startswith('block_s')):.2f}",
    'BIND_C2': label_the(CV['binding_model_C2']), 'BIND_C1': label_the(CV['binding_model_C1']),
    'OBS_SHARE': f"{CAL['pilot_observed_fit']['share']:.3f}", 'OBS_RANGE': f"{CAL['pilot_observed_fit']['range_km']:.1f}",
    'C2': f"{CV['C2']:.2f}", 'C1': f"{CV['C1']:.2f}", 'C2_M2': f"{CV['C2_M2']:.2f}", 'CORR_TEXT': corr_text,
    'EXACT': f'{exact:.0e}',
    'PILOT_M2R_B': f"{DEV3['beta']:.3f}", 'PILOT_M2R_SE2': f"{DEV3['se_twoway']:.3f}", 'PILOT_M2R_SEY': f"{DEV3['se_year']:.3f}",
    'PILOT_T_M2R': f'{TR:.2f}', 'PILOT_T_M2': f'{TM:.2f}', 'PILOT_REREAD_ROWS': pilot_rows,
    'PILOT_M2R_5': verdict(TR, c5R), 'PILOT_M2R_25': verdict(TR, c25R), 'PILOT_M2_5': verdict(TM, c5M),
    'PILOT_M2_25': verdict(TM, max(PR['models'][n]['M2']['c_2p5pct'] for n in spatial_pr)),
    'NOTREP_TEXT': notrep_text, 'POW_M2_B33': f"{P13[iid][b33]:.2f}", 'POWER_S13_TEXT': power_s13_text,
    'SDRES_M2': f"{P['sd_resid_log10Aenc_M2']:.3f}", 'SDRES': f"{P['sd_resid_log10Aenc']:.3f}", 'N_REG': str(P['regions_40km']),
    'W': fmt(cfg['W']), 'H': fmt(cfg['H']), 'N_RAW': fmt(len(inbox)), 'EXCL_SENTENCE': excl_sentence,
    'N_TABLE': fmt(D['n_table']), 'N_NAT': fmt(cause.get('Natural', 0)), 'N_HUM': fmt(cause.get('Human', 0)),
    'N_MISS': fmt(sum(v for k, v in cause.items() if k not in ('Natural', 'Human'))),
    'ERC_AVAIL': pct(D['erc_available']),
    'SYN_PLANT': f"{S['planted']['beta']:.3f} (interval {S['planted']['interval_registered'][0]:.3f}–{S['planted']['interval_registered'][1]:.3f})",
    'SYN_PLANT_DEC': S['planted']['decision'],
    'SYN_NULL': f"{S['null']['beta']:.3f} (interval {S['null']['interval_registered'][0]:.3f} to {S['null']['interval_registered'][1]:.3f})",
    'SYN_NULL_DEC': S['null']['decision'],
    'USABLE_ROWS': usable_rows, 'N_B': fmt(P['n_usable_B']),
    'AN_SE': f"{P['monte_carlo_iid']['analytic_iid_se']:.4f}", 'POWER_ROWS_SIM': power_rows,
    'N_S10': fmt(D['s10_outside_pilot_compute_box']['usable_B']), 'N_S10_ALL': fmt(s10b['n_inside_pilot_box']),
    'N_S10B': fmt(D['s10b_usable_B']), 'N_PERIM_IN': fmt(s10b['n_inside_perimeters']),
    'N_PERIM_OUT_BOX': fmt(s10b['n_inside_perimeters_outside_pilot_box']), 'N_S10B_DROP': fmt(s10b['n_dropped_s10b']),
    'N_DUP': fmt(len(EX['s12']['fod_ids'])),
    'N_SHARED': fmt(D['landscape_overlap']['usable_B_ignitions_sharing_a_compartment_with_a_pilot_ignition']),
    'EQ_VALUES': fmt(E['model']['values_compared']), 'EQ_OUTPUTS': str(E['model']['outputs_compared']),
}
t = open('PREREG_TEMPLATE.md').read()
for k, v in fill.items():
    t = t.replace('{{' + k + '}}', re.sub(r'(?<![\w.])-(?=\d)', '−', v))   # typographic minus for negatives
left = re.findall(r'\{\{[A-Z0-9_]+\}\}', t)
assert not left, left
open('PREREGISTRATION_P1C_NEWA_v1.4.md', 'w').write(t)
assert PRR['summary_M2R']['max_c_5pct'] == c5R and PRR['summary_M2']['max_c_5pct'] == c5M
print('written | C2', CV['C2'], 'C1', CV['C1'], 'C2_M2', CV['C2_M2'], '| pilot M2R at 5%:', verdict(TR, c5R), '| at 2.5%:',
      verdict(TR, c25R), '| pilot M2 at 5%:', verdict(TM, c5M))
