#!/usr/bin/env python3
"""Freeze the P1-M confirmatory test for the P1C region (MECH_PLAN.md §7, step 3).

Writes MECH_FREEZE.json, then stamps it with OpenTimestamps (MECH_FREEZE.json.ots).
Usage: python3 -B freeze_p1c_mech.py

Invariants (asserted before anything is written):
  F1  The frozen pilot code, the pilot freeze record and every P1C input hash to the pinned values. Seven P1C inputs
      are also checked against p1c/FREEZE.json. The barrier raster is checked against the registered package's
      SHA256SUMS.txt (viridis-canon PR #138, commit 9e79127).
  F2  No result exists yet, in this folder or in full_sample/.
  F3  The checks made before the freeze came from the current scripts and inputs:
      - both sample checks and the union check record the current runner;
      - the disjoint input matches DISJOINT_FILTER.json, which records the current make_disjoint_perims.py;
      - the copies in frozen_pilot_code/ equal the originals.
  F4  The freeze record does not exist yet, so a freeze is never overwritten.
"""
import hashlib, json, os, shutil, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
EXPECTED_EXTERNAL = {
    '/home/claude/p1mech/mech_test.py': '85d4f45f4a6b0e2009e5fd0783040655c13a4487f15f221371219863d2760893',
    '/home/claude/p1mech/posthoc_roads.py': 'd61013e972208721d3fbe08fab129ff79f3f1892daf148b5c6040bfb00adcfff',
    '/home/claude/p1mech/MECH_FREEZE.json': 'c54863a74af39d71f9fe36e5aa9a019a21ec58df547bf0e2f9309f6f510f3967',
    '/home/claude/p1c/compartments_static.npz': 'd6fd8cb7590dc9cc70ec84bb6e5179d69212295a871c7586ae7fe571d960d996',
    '/home/claude/p1c/raw/mtbs_perims.json': 'd98e403368b58c5e91a68f17c6f27cdc3d5957f26cd828be12c3e89c8dff1b1e',
    '/home/claude/p1c/raw/fpafod_ignitions_blind.json': 'c6f4b3e4bd810827a257410a1615b099114867d483eae2a0394e2240e0466c9e',
    '/home/claude/p1c/p1_config.json': 'ce1d1452b567b19933eea05fdda02b0b2bb9cfe4ca35de0dc8dbfc72d6c5b213',
    '/home/claude/p1c/build_predictors.py': '590baa2a03de597f7f2f5ee12e1be9fdef5e199566d879c1eef82c9944e75636',
    '/home/claude/p1c/raw/roads_primary.json': 'c13239fe8ae5e78096d0213afe9416cb207f05e7b713f15b0635b4e9ee636858',
    '/home/claude/p1c/raw/roads_secondary.json': 'c7a0b9eaf315daf3dfca4d564b4ef2f596529d79b819082a1f084c0844b596a6',
    '/home/claude/p1c/raw/roads_local.json': 'ab53215a4580b04d95eec382529abceee4d8831c3a340996d0a33081919c4701',
    '/home/claude/p1/p1_config.json': 'd43bd6025f46a7efec48f644f65b1f15e6e8186163da4deb4afe199a0e704f99',
}
PILOT_COPIES = {'frozen_pilot_code/mech_test.py': '/home/claude/p1mech/mech_test.py',
                'frozen_pilot_code/posthoc_roads.py': '/home/claude/p1mech/posthoc_roads.py',
                'frozen_pilot_code/MECH_FREEZE.json': '/home/claude/p1mech/MECH_FREEZE.json',
                'frozen_pilot_code/MECH_FREEZE.json.ots': '/home/claude/p1mech/MECH_FREEZE.json.ots',
                'frozen_pilot_code/MECH_PLAN.md': '/home/claude/p1mech/MECH_PLAN.md',
                'frozen_pilot_code/ots_upgraded/MECH_FREEZE.json.ots': '/home/claude/p1mech/ots_upgraded/MECH_FREEZE.json.ots'}
LOCAL = ('MECH_PLAN.md', 'run_p1c_mech.py', 'freeze_p1c_mech.py', 'verify_p1m_registration.py', 'make_disjoint_perims.py',
         'DISJOINT_FILTER.json', 'mtbs_perims_disjoint.json', 'SAMPLE_QA.json', 'UNION_CHECK.json',
         'full_sample/SAMPLE_QA.json', 'full_sample/MECH_PLAN.md') + tuple(PILOT_COPIES)
RESULT_FILES = ('MECH_RESULTS.json', 'mech_profile.png', 'POSTHOC_ROADS.json', 'ROADS_CHECKS.json', 'ROBUST.json',
                'P1M_P1C_DECISIONS.json', 'full_sample/MECH_RESULTS.json', 'full_sample/mech_profile.png')


def main():
    out_path = os.path.join(HERE, 'MECH_FREEZE.json')
    assert not os.path.exists(out_path), 'F4: MECH_FREEZE.json already exists'
    for p, h in EXPECTED_EXTERNAL.items():                                                      # F1
        assert sha(p) == h, f'F1: {p} does not match its pinned hash'
    p1c_freeze = json.load(open('/home/claude/p1c/FREEZE.json'))['sha256']
    for rel in ('raw/mtbs_perims.json', 'raw/fpafod_ignitions_blind.json', 'p1_config.json', 'build_predictors.py',
                'raw/roads_primary.json', 'raw/roads_secondary.json', 'raw/roads_local.json'):
        assert p1c_freeze[rel] == EXPECTED_EXTERNAL['/home/claude/p1c/' + rel], f'F1: {rel} differs from p1c/FREEZE.json'
    sums = dict(l.split()[::-1] for l in open('/home/claude/p1c_registration_v1.4/SHA256SUMS.txt') if l.strip())
    assert sums['compartments_static.npz'] == EXPECTED_EXTERNAL['/home/claude/p1c/compartments_static.npz'], \
        'F1: barrier raster differs from the registered package'
    present = [f for f in RESULT_FILES if os.path.exists(os.path.join(HERE, f))]                 # F2
    assert not present, f'F2: results already exist: {present}'
    runner = sha(os.path.join(HERE, 'run_p1c_mech.py'))                                          # F3
    for rel in ('SAMPLE_QA.json', 'full_sample/SAMPLE_QA.json', 'UNION_CHECK.json'):
        rec = json.load(open(os.path.join(HERE, rel)))
        assert rec['runner']['sha256'] == runner, f'F3: {rel} was not made by the current runner'
    for rel in ('SAMPLE_QA.json', 'full_sample/SAMPLE_QA.json'):
        assert json.load(open(os.path.join(HERE, rel)))['code_sha256'] == EXPECTED_EXTERNAL['/home/claude/p1mech/mech_test.py']
    assert json.load(open(os.path.join(HERE, 'UNION_CHECK.json')))['union_equals_frozen_road_raster'] is True
    dfil = json.load(open(os.path.join(HERE, 'DISJOINT_FILTER.json')))
    assert dfil['code_sha256'] == sha(os.path.join(HERE, 'make_disjoint_perims.py')), 'F3: disjoint filter code changed'
    assert dfil['output']['sha256'] == sha(os.path.join(HERE, 'mtbs_perims_disjoint.json')), 'F3: disjoint input changed'
    assert dfil['source']['sha256'] == EXPECTED_EXTERNAL['/home/claude/p1c/raw/mtbs_perims.json']
    assert json.load(open(os.path.join(HERE, 'SAMPLE_QA.json')))['mtbs_features'] == dfil['output']['features'], \
        'F3: SAMPLE_QA.json was not built from the disjoint input'
    assert json.load(open(os.path.join(HERE, 'full_sample/SAMPLE_QA.json')))['mtbs_features'] == dfil['source']['features'], \
        'F3: full_sample/SAMPLE_QA.json was not built from the full input'
    for rel, orig in PILOT_COPIES.items():
        assert sha(os.path.join(HERE, rel)) == sha(orig), f'F3: {rel} differs from {orig}'
    # the frozen code hashes MECH_PLAN.md in its output folder, so the full-sample folder carries an identical copy
    shutil.copyfile(os.path.join(HERE, 'MECH_PLAN.md'), os.path.join(HERE, 'full_sample/MECH_PLAN.md'))
    assert sha(os.path.join(HERE, 'full_sample/MECH_PLAN.md')) == sha(os.path.join(HERE, 'MECH_PLAN.md'))
    qa = json.load(open(os.path.join(HERE, 'SAMPLE_QA.json')))
    rec = dict(
        test='P1-M confirmatory test for the P1C region (MECH_PLAN.md v1.0)',
        frozen_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        frozen_at_local=time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()),
        primary='H1: E_road > 1 in the disjoint primary sample (matched wildfires 1992-2024); frozen rule of mech_test.py',
        sample=dict(n_fires=qa['samples']['primary']['n_fires'], n_clusters=qa['samples']['primary']['n_clusters']),
        registered_basis=dict(p1c_registration='github.com/jdhart81/viridis-canon PR #138, commit 9e79127d9ba9b17812f8fb567bef5ec858693a8d',
                              p1m_pilot_freeze='p1mech/MECH_FREEZE.json (c54863a7...), Bitcoin block 972546'),
        no_results_existed=True,
        sha256={**{f: sha(os.path.join(HERE, f)) for f in LOCAL}, **EXPECTED_EXTERNAL},
    )
    json.dump(rec, open(out_path, 'w'), indent=1)
    r = subprocess.run(['ots', 'stamp', out_path], capture_output=True, text=True, timeout=180)
    print(json.dumps({k: v for k, v in rec.items() if k != 'sha256'}, indent=1))
    print('files hashed:', len(rec['sha256']), '| ots:', r.returncode, (r.stdout + r.stderr).strip()[-200:])
    assert os.path.exists(out_path + '.ots'), 'OpenTimestamps proof was not written'


if __name__ == '__main__':
    main()
