"""Port the auditor's surviving mutants to named, source-bound behavior tests.

Disposable source copies retain the exact current test bytes. Active pins of a
mutated source are refreshed, so stale hash admission is never a credited kill.
Structured unittest results exclude import/syntax-only failures from kills.
"""
import argparse,ast,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
from mutate_gate_features import classify_test_run
G='00_lab_infrastructure/gates/standalone_pdf_release/'
T=G+'tests';R=G+'runtime/tests'
M=[
 ('M01 successor override',G+'publish_successor_wave.py','rehearsal.require_production()','pass',4,T,'test_successor_hardening.SuccessorHardeningTests.test_successor_override_refused_before_any_api_or_receipt'),
 ('M02 successor DOI prefix',G+'publish_successor_wave.py','DOI_RE = re.compile(r"^10\\.5281/zenodo\\.([0-9]+)$")','DOI_RE = re.compile(r"10\\.\\d{4,9}/zenodo\\.(\\d+)")',1,T,'test_successor_hardening.SuccessorHardeningTests.test_foreign_doi_holds_before_any_receipt'),
 ('M05 dated HOLD cleanup',G+'publish_dated_bundles.py','if isinstance(draft, dict) and type(draft.get("id")) is int:','if receipt["state"] == "DRAFT_READBACK_VERIFIED" and isinstance(draft, dict) and type(draft.get("id")) is int:',1,T,'test_rehearsal_cleanup_hardening.RehearsalCleanupTests.test_midway_hold_still_deletes_and_records_draft'),
 ('M06 successor rehearsal cleanup',G+'publish_successor_wave.py','        if draft is not None:\n            receipt["deletion"]','        if False:\n            receipt["deletion"]',1,T,'test_successor_hardening.SuccessorHardeningTests.test_successor_rehearsal_retry_delete_and_accept_410'),
 ('M07 controller HOLD cleanup',G+'runtime/digest_controller_v2.py',"   if rehearse and state['record_id']is not None:","   if False:",1,R,'test_rehearsal.ControllerHoldPathTests.test_owned_checkpoint_hold_deletes_draft_through_actual_controller_except'),
 ('M09 controller run override',G+'runtime/digest_controller_v2.py'," need('VIRIDIS_ZENODO_API_BASE'not in os.environ,'API_BASE_OVERRIDE_FORBIDDEN')\n root=ROOT"," root=ROOT",1,R,'test_rehearsal.ControllerHoldPathTests.test_run_api_override_holds_before_source_or_transport'),
 ('M10 outer guard override',G+'guard_methods_digest_release.py','rehearsal.require_production()','pass',2,T,'test_runbook_fixes.GuardRepreflightTests.test_guard_override_refused_before_any_credential_or_network'),
 ('M13 guarded successor override',G+'runtime/publish_successor_wave_guarded.py','    if "VIRIDIS_ZENODO_API_BASE" in os.environ:\n        raise SuccessorPublisherError("VIRIDIS_ZENODO_API_BASE is forbidden")\n','',2,R,'test_guarded_publisher_credentials.GuardedSuccessorHardeningBehavior.test_successor_override_refused_before_any_api_or_receipt'),
 ('M15 public repair extra paths','tools/zenodo_metadata_repair.py','if after.get("metadata") != payload["metadata"] or [row["path"] for row in receipt["public_diff"]] != [allowed_path]:','if allowed_path not in [row["path"] for row in receipt["public_diff"]]:',1,'tools/tests','test_zenodo_metadata_repair.RepairTests.test_public_readback_extra_protected_path_holds'),
 ('M18 repair rehearsal public unchanged','tools/zenodo_metadata_repair.py','            if protected_diff(current, after):','            if False:',1,'tools/tests','test_zenodo_metadata_repair.RepairTests.test_rehearsal_published_record_drift_holds_after_delete'),
 ('M20 copyright HOLD cleanup',G+'publish_successor_wave.py','            api_call(token, "DELETE", url, rdm=True, allow_not_found=True)','            pass',1,T,'test_publish_successor_credentials.CredentialTests.test_copyright_fallback_holds_on_unplanned_metadata_diff'),
 ('M22 successor prepublish cleanup',G+'publish_successor_wave.py','        if not publish_requested and not doi_observed:','        if False:',1,T,'test_successor_hardening.SuccessorHardeningTests.test_legacy_put_custom_fields_loss_holds_before_publish'),
 ('M24 immediate ledger reread','tools/zenodo_metadata_repair.py','if plan.get("ledger_binding") is not None and unmt_ledger(plan["ledger_binding"]["sha256"]) != plan["ledger_binding"]:','if False:',1,'tools/tests','test_zenodo_metadata_repair.RepairTests.test_unmt_ledger_flip_after_baseline_get_holds_before_post'),
 ('B1 complete native projection',G+'publish_successor_wave.py','        verify_native_successor(candidate, token, draft)','        pass',1,T,'test_successor_hardening.SuccessorHardeningTests.test_legacy_put_custom_fields_loss_holds_before_publish'),
 ('B2 recovered DOI no cleanup',G+'publish_successor_wave.py','        if not publish_requested and not doi_observed:','        if not publish_requested:',1,T,'test_successor_hardening.SuccessorHardeningTests.test_recovered_doi_readback_error_is_preserved_without_delete'),
 ('B1 guarded complete native projection',G+'runtime/publish_successor_wave_guarded.py','        verify_native_successor(candidate, token, draft)','        pass',1,R,'test_guarded_publisher_credentials.GuardedSuccessorHardeningBehavior.test_legacy_put_custom_fields_loss_holds_before_publish'),
 ('B2 guarded recovered DOI no cleanup',G+'runtime/publish_successor_wave_guarded.py','        if not publish_requested and not doi_observed:','        if not publish_requested:',1,R,'test_guarded_publisher_credentials.GuardedSuccessorHardeningBehavior.test_recovered_doi_readback_error_is_preserved_without_delete'),
 ('N2 rehearsal coverage sink',G+'publish_dated_bundles.py','        if out is not None:','        if False:',1,T,'test_rehearsal_cleanup_hardening.RehearsalCleanupTests.test_real_coverage_hook_persists_only_in_engine_scope'),
 ('N3 baseline protected projection','tools/zenodo_metadata_repair.py','if protected_diff(plan["before"], current):','if canonical_hash(current) != plan["before_sha256"]:',1,'tools/tests','test_zenodo_metadata_repair.RepairTests.test_stats_drift_between_plan_and_apply_is_not_protected_drift'),
 ('N6 persisted DOI recovery readback',G+'weekend_canon_lockstep.py','        publication_readbacks = verify_publication_readbacks(published)','        publication_readbacks = []',1,T,'test_lockstep_hardening.LockstepHardeningTests.test_fresh_recovery_invocation_cannot_mirror_persisted_uncertain_doi'),
 ('107 N1 exact dependency pins','00_lab_infrastructure/gates/generation_premise_guard.py','if any(hashlib.sha256(raws[name]).hexdigest() != expected\n           for name, (_, expected) in paths.items()):','if False:',1,'00_lab_infrastructure/gates','test_generation_premise_guard.StagedBoundaryTests.test_unchanged_checker_and_title_dependency_pins_are_enforced'),
 ('107 N2 draft re-read','00_lab_infrastructure/gates/generation_premise_guard.py','if any(_bytes(stage / name) != data for name, data in raw.items()):','if False:',1,'00_lab_infrastructure/gates','test_generation_premise_guard.StagedBoundaryTests.test_input_mutation_during_require_premise_has_exact_hold'),
 ('107 N2 symlink ancestor','00_lab_infrastructure/gates/generation_premise_guard.py','any(p.is_symlink() for p in (path, *path.parents))','path.is_symlink()',2,'00_lab_infrastructure/gates','test_generation_premise_guard.StagedBoundaryTests.test_symlinked_stage_ancestor_has_exact_path_hold'),
 ('107 N3 malformed draft exact label','00_lab_infrastructure/gates/generation_premise_guard.py','if not isinstance(inventory, dict) or not isinstance(contract, dict):','if False:',1,'00_lab_infrastructure/gates','test_generation_premise_guard.StagedBoundaryTests.test_invalid_draft_encoding_and_json_raise_labeled_hold_without_writes'),
 ('107 N4 recursion labeled HOLD','00_lab_infrastructure/gates/generation_premise_guard.py','except (UnicodeError, json.JSONDecodeError, RecursionError):','except (UnicodeError, json.JSONDecodeError):',2,'00_lab_infrastructure/gates','test_generation_premise_guard.StagedBoundaryTests.test_json_recursion_is_labeled_before_any_write'),

]
RUNNER='''import json,sys,unittest
class Counts(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.infrastructure_errors=0
 def addError(self,test,error):
  if issubclass(error[0],(ImportError,SyntaxError))or type(test).__name__=="_FailedTest":self.infrastructure_errors+=1
  super().addError(test,error)
result=unittest.TextTestRunner(resultclass=Counts).run(unittest.defaultTestLoader.loadTestsFromName(sys.argv[1]))
print("COUNTS:"+json.dumps(dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),infrastructure_errors=result.infrastructure_errors)))
raise SystemExit(not result.wasSuccessful())
'''
def copy_sources(repo,root):
 for sub in (G.rstrip('/'),'tools'):
  target=root/sub;target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copytree(repo/sub,target,ignore=shutil.ignore_patterns('__pycache__'))
 aligner=root/'comparator-deploy/engine3_align_challenge.py';aligner.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(repo/'comparator-deploy/engine3_align_challenge.py',aligner)
 gates=Path('00_lab_infrastructure/gates')
 for source in (repo/gates).glob('*.py'):
  shutil.copy2(source,root/gates/source.name)

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();rows=[];started=time.monotonic()
 for name,relative,old,new,count,testdir,test in M:
  if time.monotonic()-started>550:raise SystemExit('ten-minute mutation budget exceeded')
  original=(repo/relative).read_text()
  if original.count(old)!=count:
   rows.append({'mutant':name,'result':'INVALID_PATTERN','expected':count,'actual':original.count(old)});continue
  pair=[];pins=[]
  for mutated in (False,True):
   with tempfile.TemporaryDirectory(prefix='viridis-audit-mutant-')as folder:
    root=Path(folder).resolve();copy_sources(repo,root)
    if mutated:
     changed=original.replace(old,new);ast.parse(changed);(root/relative).write_text(changed)
     before=hashlib.sha256(original.encode()).hexdigest();after=hashlib.sha256(changed.encode()).hexdigest()
     for pin in (root/G).rglob('*'):
      if not pin.is_file()or pin.suffix not in {'.json','.py','.md'}or 'common'in pin.parts:continue
      text=pin.read_text()
      if before in text:pin.write_text(text.replace(before,after));pins.append(str(pin.relative_to(root)))
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','VIRIDIS_CORE_ROOT':str(root/'.fixture-core')}
    proc=subprocess.run([sys.executable,'-B','-c',RUNNER,test],cwd=root/testdir,env=env,capture_output=True,text=True,timeout=30)
    metrics=[line[7:]for line in proc.stdout.splitlines()if line.startswith('COUNTS:')]
    try:counts=json.loads(metrics[0])if len(metrics)==1 else None
    except ValueError:counts=None
    pair.append((classify_test_run(proc.returncode,counts,baseline=not mutated),proc))
  result=pair[1][0]['result']if pair[0][0]['result']=='PASS'else'BASELINE_FAILURE'
  rows.append({'mutant':name,'source':relative,'source_sha256':hashlib.sha256(original.encode()).hexdigest(),
   'test':test,'result':result,'baseline':pair[0][0],'mutated':pair[1][0],
   'pins_refreshed':sorted(set(pins)),'stderr_sha256':hashlib.sha256(pair[1][1].stderr.encode()).hexdigest(),
   'failing_tests':[line for line in pair[1][1].stderr.splitlines()if line.startswith(('FAIL:','ERROR:'))]})
  print(name+': '+result,flush=True)
 receipt={'status':'PASS'if len(rows)==len(M)and all(r['result']=='KILLED'for r in rows)else'HOLD',
  'lineage':'current-code behavioral port of auditor M01,M02,M05,M06,M07,M09,M10,M13,M15,M18,M20,M22,M24 plus new blocking/nit and107 regressions',
  'mutants':rows,'killed':sum(r['result']=='KILLED'for r in rows),'declared_mutants':len(M),'elapsed_seconds':round(time.monotonic()-started,3),
  'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version.split()[0],'external_network':False}
 with a.output.open('x')as out:out.write(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:receipt[k]for k in('status','killed','declared_mutants','elapsed_seconds')}));return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
