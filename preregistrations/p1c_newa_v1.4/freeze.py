#!/usr/bin/env python3
"""Freeze the confirmatory plan (v1.4): hash every frozen file into FREEZE.json, refusing if any check fails.

Invariants checked here (the run stops on any failure):
  F1 no outcomes.csv, results.json or REGISTRATION.json exists in this folder (nothing fetched, run or registered);
  F2 the raw ignition records carry only the allow-listed fields, and every MTBS record carries only its year;
  F3 every frozen file exists; F4 the pre-registration has no unfilled {{PLACEHOLDER}};
  F5 EQUIVALENCE.json was produced by the build_predictors.py and run_test.py being frozen, and both are identical;
  F6 CALIBRATION.json, CRITICAL_VALUES.json, SYNTHETIC_VALIDATION.json, BLIND_DESIGN.json and PILOT_REREAD.json were
     produced by the code and inputs being frozen; the validation passed; run_test.py's C2, C1, C2_M2 and C1_M2 equal
     the final values in CRITICAL_VALUES.json, which are at least those of CALIBRATION.json.
Frozen set: the plan, its template and README, all code, the blind predictor table and configuration, every raw
input and the request log, every log (including background-command outputs and the transcript extract), the records,
the pilot files this test reads or cites, the v1.0-v1.3 freeze records, the development files of v1.1, v1.3 and
v1.4, and the four audit reports.
Then OpenTimestamps-stamp FREEZE.json (python3 freeze.py --stamp).
"""
import glob, hashlib, importlib.util, json, os, re, subprocess, sys, time

PREREG = 'PREREGISTRATION_P1C_NEWA_v1.4.md'
CODE = ['run_test.py', 'simcal.py', 'fetch_outcomes.py', 'build_predictors.py', 'fetch_data.py', 'check_predictors.py',
        'blind_design.py', 'validate_synthetic.py', 'verify_registration.py', 'equivalence.py', 'fill_prereg.py',
        'freeze.py', 'make_package.py', 'calibrate_critical.py', 'exposure_lists.py', 'extract_transcript.py', 'pilot_reread.py',
        'calibrate_stress.py', 'check_calibration_repro.py']
DOCS = [PREREG, 'PREREG_TEMPLATE.md', 'REGISTRATION_README.md', 'FETCH_PROVENANCE.md',
        'audits/AUDIT_1_of_v1.0.md', 'audits/AUDIT_2_of_v1.1.md', 'audits/AUDIT_3_of_v1.2.md', 'audits/AUDIT_4_of_v1.3.md']
RECORDS = ['p1_config.json', 'predictors_blind.csv', 'EQUIVALENCE.json', 'BLIND_DESIGN.json', 'SYNTHETIC_VALIDATION.json',
           'CHECKS.txt', 'CALIBRATION.json', 'EXPOSURE_LISTS.json', 'PILOT_REREAD.json', 'CRITICAL_VALUES.json', 'CALIBRATION_REPRO.json']
PILOT = ['../p1/predictors_blind.csv', '../p1/outcomes.csv', '../p1/p1_config.json', '../p1/results.json',
         '../p1/DEVIATION_2.json', '../p1/DEVIATION_3.json', '../p1/raw/mtbs_perims.json', '../p1/raw/requests.log']
HISTORY = ['history_v1.0/FREEZE.json', 'history_v1.0/FREEZE.json.ots', 'history_v1.1/FREEZE.json', 'history_v1.1/FREEZE.json.ots',
           'history_v1.2/FREEZE.json', 'history_v1.2/FREEZE.json.ots', 'history_v1.2/third_audit_jobC_alt_models.log',
           'history_v1.2/third_audit_jobD_plausibility.log', 'history_v1.3/FREEZE.json', 'history_v1.3/FREEZE.json.ots']


def frozen_list():
    raw = sorted(p for p in glob.glob('raw/*') + glob.glob('raw/erc/*') if os.path.isfile(p))
    logs = sorted(p for p in glob.glob('logs/**', recursive=True) if os.path.isfile(p))
    dev = sorted(glob.glob('history_v1.1_dev/*') + glob.glob('history_v1.3_dev/*') + glob.glob('history_v1.4_dev/*'))
    return DOCS + CODE + RECORDS + raw + logs + PILOT + HISTORY + dev


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def main():
    for f in ('outcomes.csv', 'results.json', 'REGISTRATION.json'):
        assert not os.path.exists(f), f'F1: {f} present'
    allow = {'objectid', 'fod_id', 'fire_year', 'discovery_date', 'discovery_doy', 'nwcg_cause_classification',
             'nwcg_general_cause', 'latitude', 'longitude', 'owner_descr', 'state', 'nwcg_reporting_agency'}
    keys = {k.lower() for f in json.load(open('raw/fpafod_ignitions_blind.json')) for k in f['attributes']}
    assert keys <= allow, f'F2: non-allow-listed fields in raw ignitions: {keys - allow}'
    mk = {k for f in json.load(open('raw/mtbs_perims.json')) for k in f['attributes']}
    assert mk == {'year'}, f'F2: MTBS attributes beyond year: {mk}'
    FROZEN = frozen_list()
    missing = [f for f in FROZEN if not os.path.exists(f)]
    assert not missing, f'F3: missing {missing}'
    assert not re.search(r'\{\{[A-Z0-9_]+\}\}', open(PREREG).read()), 'F4: unfilled placeholder in the prereg'
    E = json.load(open('EQUIVALENCE.json'))
    assert E['build']['build_predictors_sha256'] == sha('build_predictors.py') and E['build']['identical'], 'F5: build equivalence stale'
    assert E['model']['run_test_sha256'] == sha('run_test.py') and E['model']['identical'], 'F5: model equivalence stale'
    C = json.load(open('CALIBRATION.json')); S = json.load(open('SYNTHETIC_VALIDATION.json')); B = json.load(open('BLIND_DESIGN.json'))
    PRR = json.load(open('PILOT_REREAD.json')); CV = json.load(open('CRITICAL_VALUES.json'))
    REP = json.load(open('CALIBRATION_REPRO.json'))
    for rec, name in ((CV, 'CRITICAL_VALUES'), (S, 'SYNTHETIC_VALIDATION'), (B, 'BLIND_DESIGN'), (PRR, 'PILOT_REREAD'), (REP, 'CALIBRATION_REPRO')):
        for f, h in rec['code_sha256'].items():
            assert sha(f) == h, f'F6: {name}.json is stale for {f}'
    # CALIBRATION.json was produced by the v1.3 code, frozen in history_v1.3/; the current code reproduces it (REP)
    for f, h in C['code_sha256'].items():
        assert sha(f if f == 'predictors_blind.csv' else 'history_v1.3/' + f) == h, f'F6: CALIBRATION.json does not match the frozen v1.3 {f}'
    assert REP['all_identical'], 'F6: the current code does not reproduce CALIBRATION.json'
    assert S['pass'], 'F6: synthetic validation did not pass'
    spec = importlib.util.spec_from_file_location('rt', 'run_test.py'); rt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rt)
    assert (rt.C2, rt.C1, rt.C2_M2, rt.C1_M2) == (CV['C2'], CV['C1'], CV['C2_M2'], CV['C1_M2']), \
        'F6: run_test.py critical values differ from CRITICAL_VALUES.json'
    assert all(CV[k] >= C[k] for k in ('C2', 'C1', 'C2_M2', 'C1_M2')), 'F6: a final value is below the calibration'
    assert CV['calibration']['sha256'] == sha('CALIBRATION.json'), 'F6: CRITICAL_VALUES.json was built on another CALIBRATION.json'
    t = time.time()
    rec = dict(version='1.4',
               supersedes=[dict(version='1.0', freeze_sha256=sha('history_v1.0/FREEZE.json'), published=False),
                           dict(version='1.1', freeze_sha256=sha('history_v1.1/FREEZE.json'), published=False),
                           dict(version='1.2', freeze_sha256=sha('history_v1.2/FREEZE.json'), published=False),
                           dict(version='1.3', freeze_sha256=sha('history_v1.3/FREEZE.json'), published=False)],
               frozen_at_local=time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime(t)),
               frozen_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t)),
               decision_rule=(f'SUPPORTED iff beta - {rt.C2} * max(SE_twoway, SE_year) > 0 (H2, definition B, model M2R = '
                              'M2 + fixed effects for 40 km regions)'),
               note=('Frozen before any FPA FOD outcome field (fire_size etc.) for this region was requested. '
                     'fetch_outcomes.py verifies these hashes and downloads the public copy of the plan before fetching.'),
               sha256={f: sha(f) for f in FROZEN})
    json.dump(rec, open('FREEZE.json', 'w'), indent=1)
    print(f'frozen {len(FROZEN)} files at', rec['frozen_at_local'])
    print('FREEZE.json sha256', sha('FREEZE.json'))


def stamp():
    cals = ['https://alice.btc.calendar.opentimestamps.org', 'https://finney.calendar.eternitywall.com',
            'https://bob.btc.calendar.opentimestamps.org', 'https://a.pool.opentimestamps.org']
    cmd = ['ots', 'stamp', '-m', '1'] + sum([['-c', c] for c in cals], []) + ['FREEZE.json']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(r.stdout, r.stderr)
    assert os.path.exists('FREEZE.json.ots'), 'stamp failed'
    print(subprocess.run(['ots', 'info', 'FREEZE.json.ots'], capture_output=True, text=True).stdout[:600])


if __name__ == '__main__':
    stamp() if '--stamp' in sys.argv else main()
