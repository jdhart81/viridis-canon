"""Cause-specific assertion kills for the two fresh-precheck blocker groups.

Each named test must pass unmodified, fail by assertion after its semantic
mutation, and report zero errors. Integrity envelopes are refreshed so they
cannot substitute for a behavioral kill. No network or Lean is used.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PREFIX = 'test_round2_stack.ComposedControllerTests.'
MUTANTS = [
 ('N1_unchecked_cached_helper', 'install_integration.py',
  [('    exec(compile(terminal_raw, str(terminal), "exec"), module.__dict__)',
    '    import importlib.util\n    spec = importlib.util.spec_from_file_location("_unchecked_cache", terminal)\n    spec.loader.exec_module(module)')],
  PREFIX+'test_installer_real_CLI_ignores_timestamp_valid_substituted_bytecode_under_B'),
 ('N1_ambient_local_import_cache', 'install_integration.py',
  [('HELPERS = (', 'import scheduler_liveness\n\nHELPERS = (')],
  PREFIX+'test_installer_real_CLI_ignores_cached_local_dependency'),
 ('N1_stale_predecessor_installation', 'install_integration.py',
  [('if any(hashlib.sha256(original[name]).hexdigest() != expected for name, expected in value["before_sha256"].items()):','if False:'),
   ('if any(file_digest(pipeline / name) != digest for name, digest in value["before_sha256"].items()):','if False:')],
  PREFIX+'test_installer_rechecks_predecessor_CAS_after_plan_before_any_write'),
 ('N2_terminal_original_blocks_certificate_visibility', 'checkpoint_certification_lane.py',
  [('prefix = lane.publication_prefix(certification_order, accepted)',
    'prefix = lane.publication_prefix([identity for identity, _, _, _ in prepared], accepted)')],
  PREFIX+'test_shared_authenticated_terminal_allows_only_younger_certificate_visibility_not_credit_or_publication'),
 ('N2_terminal_exclusion_not_reauthenticated', 'checkpoint_certification_lane.py',
  [('if not terminal_hold(entry, identity, lane.root.parent):','if False:')],
  PREFIX+'test_terminal_exclusion_is_freshly_reauthenticated_before_certificate_visibility'),
 ('N2_rejected_request_misclassified_as_terminal_science', 'checkpoint_certification_lane.py',
  [('        if held:\n            if not terminal_hold(entry, identity, lane.root.parent):',
    '        if held or identity.key in {RequestIdentity(**row["identity"]).key for row in lane._rows("terminal")}:\n            if held and not terminal_hold(entry, identity, lane.root.parent):')],
  'test_round2_rejections.DeployedRejectionTests.test_authenticated_provider_rejection_remains_a_certificate_visibility_gap'),
]


def execute(root: Path, test: str) -> dict:
    process = subprocess.run([sys.executable, '-B', '-m', 'unittest', test, '-v'],
        cwd=root/'tests', capture_output=True, text=True, timeout=60,
        env={**os.environ, 'VIRIDIS_LIVENESS_REPO_ROOT':str(HERE.parents[2])})
    import re
    failures = re.findall(r'^FAIL: (\w+)', process.stderr, re.M)
    errors = re.findall(r'^ERROR: (\w+)', process.stderr, re.M)
    return {'returncode':process.returncode,'assertion_failures':failures,'errors':errors,
            'stdout_sha256':hashlib.sha256(process.stdout.encode()).hexdigest(),
            'stderr_sha256':hashlib.sha256(process.stderr.encode()).hexdigest()}


def run() -> int:
    rows=[]
    for name, target, changes, test in MUTANTS:
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)/'engine_liveness'
            shutil.copytree(HERE,root,ignore=shutil.ignore_patterns('__pycache__'))
            baseline=execute(root,test)
            if baseline['returncode'] or baseline['errors']:
                raise RuntimeError('named baseline must pass: '+name)
            path=root/target; raw=path.read_text()
            for old,new in changes:
                if raw.count(old)!=1:
                    raise RuntimeError('semantic mutation anchor must be unique: '+name)
                raw=raw.replace(old,new)
            compile(raw,target,'exec');path.write_text(raw)
            manifest=root/'INTEGRATION_BINDING.json';binding=json.loads(manifest.read_text())
            for source_name in binding['source_files']:
                binding['source_files'][source_name]=hashlib.sha256((root/source_name).read_bytes()).hexdigest()
            manifest.write_text(json.dumps(binding,indent=2,sort_keys=True)+'\n')
            result=execute(root,test)
            rows.append({'mutant':name,'named_test':test,'baseline':baseline,'result':result,
                         'killed':bool(result['returncode'] and result['assertion_failures'] and not result['errors'])})
    value={'standard':'VRS-PRECHECK-CAUSE-SPECIFIC-MUTATIONS-1','total':len(rows),
           'killed':sum(row['killed'] for row in rows),'errors':sum(len(row['result']['errors']) for row in rows),'results':rows}
    print(json.dumps(value,indent=2,sort_keys=True))
    return 0 if value['killed']==value['total'] and value['errors']==0 else 1


if __name__=='__main__':
    raise SystemExit(run())
