"""Replay named source-contract assertions against isolated single mutations.

All executable copies and fixtures stay beneath an explicit temporary output.
No scientific producer, publication transport, Core root or credential runs.
A kill requires an intended unittest assertion failure with zero ERRORs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

SOURCE_FILES = ('packaging_runtime.py','install_packaging_runtime.py',
                'guard_methods_digest_release.py','owner_content_worker.py','scientific_registration_worker.py')
TEST_MODULE = 'test_archival_profile.ArchivalProfileTests.'
MUTANTS = (
 ('drop_current_access_module','packaging_runtime.py',
  "MODULE_NAMES = PRIOR_DIGEST_MODULE_NAMES | {'nightly_manuscript_access.py', 'nightly_manuscript_checkpoint.py'}",
  "MODULE_NAMES = PRIOR_DIGEST_MODULE_NAMES | {'nightly_manuscript_checkpoint.py'}",
  'test_current20_does_not_admit_prior18_or_successor_in_either_slot'),
 ('profile_accepts_wrong_note_preparation','packaging_runtime.py',
  "and profile['note_preparation'] == NOTE_PREPARATION, 'CLOSED_INSTALLED_PROFILE')",
  "and True, 'CLOSED_INSTALLED_PROFILE')",
  'test_profile_wrong_missing_reordered_or_old_nomination_holds_before_authority'),
 ('installer_accepts_wrong_note_preparation','install_packaging_runtime.py',
  "runtime.need(plan['note_preparation']==runtime.NOTE_PREPARATION,'EXACT_NOTE_PREPARATION_NOMINATION')",
  "runtime.need(True,'EXACT_NOTE_PREPARATION_NOMINATION')",
  'test_installer_altered_note_preparation_holds_before_source_proof_or_writes'),
 ('outer_guard_accepts_wrong_note_preparation','guard_methods_digest_release.py',
  "and profile.get('note_preparation') == NOTE_PREPARATION, 'exact installed successor profile required')",
  "and True, 'exact installed successor profile required')",
  'test_outer_guard_altered_note_preparation_holds_before_real_child'),
 ('owner_bootstrap_accepts_wrong_note_preparation','owner_content_worker.py',
  "and manifest['note_preparation'] == NOTE_PREPARATION, 'NOMINATED_BOOTSTRAP_NOTE_PREPARATION')",
  "and True, 'NOMINATED_BOOTSTRAP_NOTE_PREPARATION')",
  'test_owner_bootstrap_rejects_altered_facade_manifest'),
 ('science_bootstrap_accepts_wrong_note_preparation','scientific_registration_worker.py',
  "or manifest['note_preparation'] != NOTE_PREPARATION):",
  "or False):",
  'test_science_bootstrap_rejects_altered_facade_manifest_before_runtime'),
 ('source_proof_accepts_wrong_note_preparation','owner_content_worker.py',
  "and proof['certifies'] is False and proof['note_preparation'] == NOTE_PREPARATION",
  "and proof['certifies'] is False and True",
  'test_manifest_proof_binds_facade_and_new_module_count'),
 ('new_module_cache_admitted','packaging_runtime.py',
  'for name in sorted(MODULE_NAMES):', 'for name in sorted(PRIOR_DIGEST_MODULE_NAMES):',
  'test_new_module_alternate_import_artifacts_hold_in_all_current_bootstraps'),
 ('facade_runs_outside_source_session','packaging_runtime.py',
  'with session(root, binding):', 'with contextlib.nullcontext():',
  'test_preparation_route_uses_pinned_facade_in_genuine_source_session'),
 ('canonical_runtime_capability_not_propagated','packaging_runtime.py',
  'contexts.append(canonical._ACTIVE_SOURCE_SESSION)', 'pass # canonical context omitted',
  'test_preparation_route_uses_pinned_facade_in_genuine_source_session'),
 ('source_session_capability_not_revoked','packaging_runtime.py',
  'context.reset(token)', 'pass # capability wrongly retained',
  'test_active_source_scope_requires_exact_profile_and_revokes_after_exception'),
 ('accept_previous_source_review_schema','packaging_runtime.py',
  "and review['standard']=='VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-13'",
  "and review['standard'] in {'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-13','VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-12'}",
  'test_current_review_schema_requires_archival_flags_and_every_new_source_hash'),
)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def run(runtime, output, interpreter):
    output.mkdir(exist_ok=False, parents=True)
    captured = {name:(runtime/name).read_bytes() for name in SOURCE_FILES}
    tests = runtime/'tests'
    test_raw = (tests/'test_archival_profile.py').read_bytes()
    results = []
    with tempfile.TemporaryDirectory(prefix='w42-profile-causal-') as folder:
        temp = Path(folder).resolve(); copied = temp/'00_lab_infrastructure'/'gates'/'standalone_pdf_release'/'runtime'
        copied.mkdir(parents=True)
        shutil.copytree(runtime.parent/'common', copied.parent/'common', ignore=shutil.ignore_patterns('__pycache__'))
        (copied/'tests').mkdir()
        for path in runtime.glob('*.py'): shutil.copy2(path, copied/path.name)
        for path in tests.glob('*.py'): shutil.copy2(path, copied/'tests'/path.name)
        # These two unchanged scientific source-scope definitions are read
        # only as SHA-bound fixture bodies, never as production execution.
        for relative in (
            'production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/prepare_first_seven_plan.py',
            'production_snapshots/phase7-20261008-own-record-comparison/before/execution/runtime_closure_view.py',
        ):
            source = runtime.parents[1]/relative
            target = copied.parents[1]/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
        env = dict(os.environ,VIRIDIS_CORE_ROOT=str(temp/'isolated-root'))
        for name in ('PYTHONPATH','PYTHONHOME','PYTHONPYCACHEPREFIX'):
            env.pop(name,None)
        def execute(label, test):
            command = [interpreter,'-B','-m','unittest',TEST_MODULE+test]
            start = time.monotonic()
            result = subprocess.run(command,cwd=copied/'tests',env=env,
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
            stdout = output/(label+'.stdout.txt'); stderr = output/(label+'.stderr.txt')
            stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
            diagnostic = result.stderr.decode('utf-8',errors='replace')
            failures = re.findall(r'^FAIL: (\S+)',diagnostic,re.M)
            errors = re.findall(r'^ERROR: (\S+)',diagnostic,re.M)
            return {'label':label,'named_test':TEST_MODULE+test,'command':command,'returncode':result.returncode,
                    'seconds':time.monotonic()-start,'assertion_failures':len(failures),
                    'errors':len(errors),'infrastructure_errors':int(not re.search(r'Ran 1 test\b',diagnostic)),
                    'stdout':{'path':str(stdout),'sha256':digest(result.stdout)},
                    'stderr':{'path':str(stderr),'sha256':digest(result.stderr)}}
        for name, file, old, replacement, test in MUTANTS:
            baseline = execute(name+'.baseline',test)
            original = captured[file].decode()
            if original.count(old)!=1: raise ValueError('MUTATION_ANCHOR_NOT_UNIQUE:'+name)
            mutated = original.replace(old,replacement)
            (copied/file).write_text(mutated)
            try: mutant = execute(name+'.mutant',test)
            finally: (copied/file).write_bytes(captured[file])
            qualified = (baseline['returncode']==0 and baseline['assertion_failures']==0
                         and baseline['errors']==0 and baseline['infrastructure_errors']==0
                         and mutant['returncode']==1 and mutant['assertion_failures']>0
                         and mutant['errors']==0 and mutant['infrastructure_errors']==0)
            results.append({'name':name,'source_file':file,'before_sha256':digest(captured[file]),
                            'mutant_sha256':digest(mutated.encode()),'removed':old,'added':replacement,
                            'baseline':baseline,'mutant':mutant,'qualified_assertion_kill':qualified})
    if any((runtime/name).read_bytes()!=raw for name,raw in captured.items()):
        raise ValueError('SOURCE_CAPTURE_DRIFT')
    report = {'standard':'VRS-W42-ARCHIVAL-PROFILE-CAUSAL-REPLAY-1','interpreter':interpreter,
              'source_hashes':{name:digest(raw) for name,raw in captured.items()},
              'test_sha256':digest(test_raw),'mutants':results,'count':len(results),
              'qualified_assertion_kills':sum(row['qualified_assertion_kill'] for row in results),
              'zero_core_execution':True,'zero_science_admission_claim':True}
    path = output/'PROFILE_CAUSAL.json'; path.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'path':str(path),'sha256':digest(path.read_bytes()),
                      'count':report['count'],'qualified_assertion_kills':report['qualified_assertion_kills']}))
    return 0 if report['qualified_assertion_kills']==report['count'] else 1


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--python',required=True)
    args=parser.parse_args()
    raise SystemExit(run(Path(__file__).resolve().parents[1],args.output.resolve(),args.python))
