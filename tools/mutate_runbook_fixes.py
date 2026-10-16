"""Revert each blocking review fix and run its named behavioral regression."""
import argparse,ast,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
GATE='00_lab_infrastructure/gates/standalone_pdf_release'
MUTANTS=[
('F1 production environment boundary',GATE+'/publish_dated_bundles.py','    rehearsal.require_production()\n    prior =','    prior =','test_runbook_fixes.RehearsalTests.test_environment_override_holds_before_network',GATE+'/tests'),
('F1 production DOI only',GATE+'/publish_dated_bundles.py','re.compile(r"^10\\.5281/zenodo\\.[0-9]+$")','re.compile(r"10\\.\\d{4,9}/zenodo\\.\\d+")','test_runbook_fixes.RehearsalTests.test_foreign_doi_holds_before_any_receipt',GATE+'/tests'),
('F2 generated README',GATE+'/README.md','Enforcement status (verified 2026-10-16):','The current dated and successor publishers enforce this gate.','test_enforcement_claims.EnforcementClaimsTests.test_repository_readme_status_is_current',GATE+'/tests'),
('F3 ledger certificate authority','tools/zenodo_metadata_repair.py','if any(row.get("certificate_valid") is not False or row.get("certificate") is not None for row in rows):','if False:','test_zenodo_metadata_repair.RepairTests.test_unmt_holds_if_ledger_missing_entities_valid_certificate_or_hash_drift','tools/tests'),
('F4 NATIVE protected projection','tools/zenodo_metadata_repair.py','return full_diff(prior_protected_projection(before, representation="NATIVE"),\n                     prior_protected_projection(after, representation="NATIVE"))','return full_diff(before, after)','test_zenodo_metadata_repair.RepairTests.test_real_record_projection_and_already_applied_replay','tools/tests'),
('F5 full draft PUT','tools/zenodo_metadata_repair.py','payload = copy.deepcopy(draft)','payload = {"metadata": copy.deepcopy(draft["metadata"])}','test_zenodo_metadata_repair.RepairTests.test_real_record_projection_and_already_applied_replay','tools/tests'),
('F5 prepublish readback gate','tools/zenodo_metadata_repair.py','if (checked.get("metadata") != payload["metadata"]\n                or [row["path"] for row in receipt["draft_diff"]] != [allowed_path]\n                or [row["path"] for row in receipt["draft_public_diff"]] != [allowed_path]):','if False:','test_zenodo_metadata_repair.RepairTests.test_unplanned_draft_diff_blocks_publish','tools/tests'),
('F5 held draft cleanup','tools/zenodo_metadata_repair.py','if draft_opened and not publish_requested:','if False:','test_zenodo_metadata_repair.RepairTests.test_unplanned_draft_diff_blocks_publish','tools/tests'),
('B6 immediate controller re-preflight',GATE+'/guard_methods_digest_release.py','            checked = preflight(config_path, expected_sha256)','            checked = checked','test_runbook_fixes.GuardRepreflightTests.test_package_mutation_after_controller_load_blocks_execute',GATE+'/tests'),
]
def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();rows=[]
 for label,path,old,new,test,testdir in MUTANTS:
  original=(repo/path).read_text()
  if original.count(old)!=1:rows.append({'mutant':label,'result':'INVALID_PATTERN'});continue
  pair=[]
  for mutate in (False,True):
   with tempfile.TemporaryDirectory(prefix='viridis-finding-mutant-')as temp:
    root=Path(temp)
    for child in (GATE,'tools/tests'):
     target=root/child;target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(repo/child,target,ignore=shutil.ignore_patterns('runtime','common','__pycache__'))
    for child in ('tools/zenodo_metadata_repair.py','00_lab_infrastructure/gates/own_record_comparison.py'):
     target=root/child;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/child,target)
    if mutate:
     modified=original.replace(old,new)
     if path.endswith('.py'):ast.parse(modified)
     (root/path).write_text(modified)
    result=subprocess.run([sys.executable,'-m','unittest',test],cwd=root/testdir,capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=30)
    pair.append(result)
  valid=pair[0].returncode==0 and not any(s in pair[1].stderr for s in ('ImportError:','ModuleNotFoundError:','SyntaxError:'))
  rows.append({'mutant':label,'test':test,'result':'KILLED'if valid and pair[1].returncode else'SURVIVED'if valid else'INVALID_BASELINE_OR_IMPORT','baseline_exit_code':pair[0].returncode,'mutant_exit_code':pair[1].returncode,'mutant_stderr_sha256':hashlib.sha256(pair[1].stderr.encode()).hexdigest()})
 receipt={'status':'PASS'if all(r['result']=='KILLED'for r in rows)else'HOLD','mutants':rows,'killed':sum(r['result']=='KILLED'for r in rows),'declared_mutants':len(MUTANTS),'external_calls':0}
 with a.output.open('x')as out:out.write(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':receipt['status'],'killed':receipt['killed'],'declared_mutants':len(MUTANTS)}));return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
