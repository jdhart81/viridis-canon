#!/usr/bin/env python3
"""Cause-specific W42 access mutants in an isolated copied checkout.

Numeric unittest failures are required. Import/fixture/runtime errors never
count as a kill; each named test must first pass against unmodified source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE=Path(__file__).resolve().parents[1]
RUNTIME=Path('00_lab_infrastructure/gates/standalone_pdf_release/runtime')
ACCESS=RUNTIME/'nightly_manuscript_access.py'
DIGEST=RUNTIME/'methods_digest_v2.py'
TESTS=RUNTIME/'tests'
MUTANTS=[
 ('W01_unbound_file_dependencies',ACCESS,[('    require_self_contained_original(original)\n','')],
  'HistoricalInputTests.test_unbound_file_input_graphics_dynamic_and_external_package_hold',
  [('    need(not forbidden.intersection(commands),', '    need(True or not forbidden.intersection(commands),'),
   ("        need(all(re.fullmatch(r'[A-Za-z0-9_-]+', n) for n in names.split(',')),", "        need(True or all(re.fullmatch(r'[A-Za-z0-9_-]+', n) for n in names.split(',')),")]),
 ('W02_frozen_source_hash',ACCESS,[("        need(d.digest(raw) == expected, 'frozen source changed: ' + name)","        need(True, 'frozen source changed: ' + name)")],
  'FrozenInputBoundaryTests.test_frozen_hash_boundary_rejects_source_drift_before_execution',[]),
 ('W03_frozen_source_race',ACCESS,[("            need(d.read_regular(path) == raw, 'frozen source race: ' + name)","            need(True, 'frozen source race: ' + name)")],
  'FrozenInputBoundaryTests.test_frozen_hash_boundary_rejects_race_before_return',[]),
 ('W04_exact_original_render_input',ACCESS,[("    need(d.read_regular(Path(note) / 'historical-render/paper.tex') == original,", "    need(True or d.read_regular(Path(note) / 'historical-render/paper.tex') == original,")],
  'ArchivalAccessTests.test_historical_render_input_cannot_be_corrected_r3_tex',[]),
 ('W05_actual_render_provenance',ACCESS,[("    observation = load('phase7_audit_policy').require_pdf_provenance(\n        Path(note) / 'historical-render', root, original, pdf, seen)","    observation = {}  # MUTANT bypasses genuine historical provenance")],
  'ArchivalAccessTests.test_wrong_source_observation_holds',[]),
 ('W06_exact_copied_uploads',ACCESS,[("            need(d.read_regular(note / name) == raw, 'changed copied access input: ' + name)","            need(True, 'changed copied access input: ' + name)")],
  'ArchivalAccessTests.test_missing_historical_same_stem_archive_pdf_holds',[]),
 ('W07_access_not_publication_authority',ACCESS,[("and pb['certifies'] is False and pb['publication_authorized'] is False,", "and pb['certifies'] is False,")],
  'ArchivalAccessTests.test_access_binding_cannot_claim_scientific_or_publication_authority',[]),
 ('W08_fresh_target_after_derivation',ACCESS,[("    need(predecessor(root, base, authority, load) == current, 'predecessor changed during access derivation')", "    need(True, 'predecessor changed during access derivation')")],
  'ArchivalAccessTests.test_current_target_changed_after_reader_is_not_cached',[]),
 ('W09_closed_digest_roles',DIGEST,[("    if roles!=expected or expected[1]['sha256']is None:", "    if False:")],
  'DigestRoleTests.test_closed_role_binding_rejects_omission_swap_extra_or_changed_hash',[]),
 ('W10_historical_top_copy',DIGEST,[("    if 'manuscripts'in note:","    if False:")],
  'DigestAccessTests.test_partitioned_actual_consumer_digest_exact_two_roles_and_recursive_gate',[]),
 ('W11_complete_historical_pdf',ACCESS,[("    require_pdf_envelope(pdf)","    pass  # MUTANT accepts header-only historical PDF")],
  'ArchivalAccessTests.test_header_only_pdf_cannot_become_bound_even_with_matching_observation',[]),
]

HARNESS=r'''import json,sys,unittest
sys.dont_write_bytecode=True
sys.path[:0]=[sys.argv[1]]
suite=unittest.defaultTestLoader.loadTestsFromName('test_nightly_manuscript_access.'+sys.argv[2])
r=unittest.TextTestRunner(verbosity=2).run(suite)
print('VRS_NUMERIC_UNITTEST_RESULT='+json.dumps({'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'skips':len(r.skipped),'assertion_failures':[text for _,text in r.failures]}))
sys.exit(0 if r.wasSuccessful()else 1)
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()
def run(root,test,timeout):
    p=subprocess.run([sys.executable,'-B','-c',HARNESS,str(root/TESTS),test],cwd=root,
        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
    lines=[x.split('=',1)[1]for x in p.stdout.splitlines()if x.startswith('VRS_NUMERIC_UNITTEST_RESULT=')]
    return p,json.loads(lines[-1])if lines else None

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=120);parser.add_argument('--only',action='append')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False);results=[]
    with tempfile.TemporaryDirectory(prefix='w42-mutants-')as tmp:
        root=Path(tmp)/'checkout';shutil.copytree(BASE,root,ignore=shutil.ignore_patterns('.git','__pycache__','*.pyc','*.pyo'))
        for name,path,replacements,test,extra in MUTANTS:
            if args.only and name not in args.only:continue
            source=(root/path).read_text();control,control_result=run(root,test,args.timeout)
            (args.output/(name+'-control.log')).write_text(control.stdout)
            if control.returncode!=0 or control_result is None or control_result['tests']<1 or control_result['failures']or control_result['errors']:
                results.append({'name':name,'status':'INVALID_CONTROL','test':test,'control':control_result});continue
            mutated=source
            for before,after in replacements+extra:
                expected=2 if name=='W11_complete_historical_pdf' else 1
                if mutated.count(before)!=expected:raise ValueError('unique closed mutation sites required: '+name+' '+repr(before))
                mutated=mutated.replace(before,after)
            (root/path).write_text(mutated)
            try:p,result=run(root,test,args.timeout)
            finally:(root/path).write_text(source)
            (args.output/(name+'-mutant.log')).write_text(p.stdout)
            killed=result is not None and result['tests']>=1 and result['failures']>=1 and result['errors']==0
            results.append({'name':name,'status':'KILLED_ASSERTION'if killed else'INVALID_ERROR'if result is None or result['errors']else'SURVIVED',
                'test':test,'source':str(path),'source_before_sha256':sha(source.encode()),'source_mutant_sha256':sha(mutated.encode()),
                'control':control_result,'mutant':result,'control_log_sha256':sha(control.stdout.encode()),'mutant_log_sha256':sha(p.stdout.encode())})
            print(name,results[-1]['status'],flush=True)
    summary={'standard':'VRS-W42-CAUSE-SPECIFIC-MUTATIONS-1','python':sys.version,'results':results,
        'killed':sum(r['status']=='KILLED_ASSERTION'for r in results),'total':len(results),
        'errors_credited':0,'all_killed':all(r['status']=='KILLED_ASSERTION'for r in results)}
    (args.output/'RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    return 0 if summary['all_killed']else 1

if __name__=='__main__':raise SystemExit(main())
