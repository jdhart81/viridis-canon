"""Kill source-bound allocation mutants through named assertion regressions.

Each clone uses unchanged test bytes. Resolver mutations regenerate the three
source pins; consumer mutations regenerate exact after-source/patch hashes.
No stale-pin, import, syntax or generic unittest error is credited as a kill.
"""
import argparse,ast,difflib,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
R='tools/effective_allocation.py'
T='test_effective_allocation.'
M=[
 ('exact immutable input hashes',R,'and sha(raw) == expected','and True',1,T+'ResolverTests.test_every_original_science_authority_and_overlay_tamper_holds'),
 ('ordinary global collisions',R,"need(len(set([*view.public_rows,*rows])) == len([*view.public_rows,*rows]), 'GLOBAL_RESERVATION_COLLISION')","pass",1,T+'ResolverTests.test_default_no_overlay_keeps_original_global_collision_hold'),
 ('closed overlay fields',R,"need(isinstance(value, dict) and set(value) == fields, reason)","need(isinstance(value, dict), reason)",1,T+'ResolverTests.test_only183147to148_local_only_and_closed_overlay_fields'),
 ('only approved183 row',R,"and type(overlay['approved_local_row']) is int and overlay['approved_local_row'] == 148","and True",1,T+'ResolverTests.test_only183147to148_local_only_and_closed_overlay_fields'),
 ('overlay never grants publication',R,"overlay['publication_authorized'] is False","True",1,T+'ResolverTests.test_only183147to148_local_only_and_closed_overlay_fields'),
 ('genuine authority scope',R,"authority['approved'] is True","True",1,T+'ResolverTests.test_authority_scope_and_exact_linked_hash_are_enforced_after_hash_admission'),
 ('every science byte bound',R,"        view.read(row['path'], expected)","        pass",1,T+'ResolverTests.test_every_original_science_authority_and_overlay_tamper_holds'),
 ('local companion never grants publication',R,"local['publication_authorized'] is False","True",1,T+'ResolverTests.test_companion_local_binding_is_closed_local_only_and_matches_same_authorities'),
 ('row148 same scientific identity',R,"and cells[3] == 'nightly Run-183'","and True",1,T+'ResolverTests.test_bound_row148_has_same_receipt_binding_schema_and_identity'),
 ('boolean is not a row',R,"type(value) is int and value > 0","isinstance(value, int) and value > 0",1,T+'ResolverTests.test_boolean_rows_and_duplicate_global_public_or_effective_reservations_hold'),
 ('no symlink ancestry',R,"'..' not in path.parts and not any(p.is_symlink() for p in (path, *path.parents))","'..' not in path.parts",1,T+'ResolverTests.test_regular_inputs_reject_leaf_and_ancestor_links'),
 ('byte and frame CAS',R,"need(regular(path) == value, 'INPUT_RACE')","pass",1,T+'ResolverTests.test_bytes_frames_and_proposal_inventory_are_rechecked_before_use'),
 ('reservation inventory CAS',R,"need(proposal_inventory(self.root) == self.paths, 'RESERVATION_SET_RACE')","pass",4,T+'ResolverTests.test_bytes_frames_and_proposal_inventory_are_rechecked_before_use'),
 ('fixed ledger role',R,"need(view.ledger_path == view.root.parent.parent/'ZENODO_SUBMISSION_LEDGER.md', 'CURRENT_ROOT_LEDGER_ROLE')","pass",1,T+'ResolverTests.test_ledger_and_public_reservation_inputs_have_fixed_root_roles'),
 ('source pin before exec','after:canon_product_router.py','if hashlib.sha256(raw).hexdigest() != EFFECTIVE_ALLOCATION_SOURCE_SHA256:','if False:',1,T+'PatchedConsumerTests.test_hash_bound_loader_rejects_tampered_source_symlinks_and_ambient_module'),
 ('no ambient resolver import','after:canon_product_router.py','exec(compile(raw, str(path), "exec"), namespace)',"namespace.update(__import__('effective_allocation').__dict__)",1,T+'PatchedConsumerTests.test_hash_bound_loader_rejects_tampered_source_symlinks_and_ambient_module'),
 ('router uses effective reservation','after:canon_product_router.py','list(view.proposal_rows)','[147, 147]',1,T+'PatchedConsumerTests.test_all_three_consumers_share_effective_rows_with_explicit_binding'),
 ('assembler uses effective projection','after:assemble_saturday_candidate.py','"proposed_ledger_row": proposal["proposed_ledger_row"]','"proposed_ledger_row": allocation.original_proposal(run_id)["proposed_ledger_row"]',1,T+'PatchedConsumerTests.test_staged_projection_retains_original147_and_proposes148_without_assigning_rights'),
 ('reconciler uses effective proposal','after:reconcile_publication_receipt.py','        result[abbreviation] = proposal','        proposal["proposed_ledger_row"] = view.original_proposal(run_id)["proposed_ledger_row"]\n        result[abbreviation] = proposal',1,T+'PatchedConsumerTests.test_all_three_consumers_share_effective_rows_with_explicit_binding'),
 ('router write CAS','after:canon_product_router.py','    allocation.revalidate()','    pass',2,T+'PatchedConsumerTests.test_router_revalidates_the_snapshot_before_writing_any_new_route'),
 ('assembler write CAS','after:assemble_saturday_candidate.py','    allocation.revalidate()','    pass',3,T+'PatchedConsumerTests.test_assembler_revalidates_after_review_before_creating_candidate_files'),
 ('reconciler first write CAS','after:reconcile_publication_receipt.py','    allocation.revalidate()\n    if apply:','    if apply:',1,T+'PatchedConsumerTests.test_reconciler_revalidates_before_first_write_and_after_its_owned_ledger_write'),
 ('reconciler second write CAS','after:reconcile_publication_receipt.py','                allocation.revalidate_after_ledger_write(ledger_after.encode("utf-8"))','                pass',1,T+'PatchedConsumerTests.test_reconciler_revalidates_before_first_write_and_after_its_owned_ledger_write'),
 ('reconciler ledger snapshot','after:reconcile_publication_receipt.py','ledger_before = allocation.read(ledger_path).decode("utf-8")','ledger_before = ledger_path.read_text(encoding="utf-8")',1,T+'PatchedConsumerTests.test_reconciler_uses_captured_ledger_bytes_instead_of_an_unbound_second_read'),
]
# Round2 reviewer findings, exercised through real argv and semantic guards.
M += [
 ('B1 Path frozen as string',R,"'overlay':{'path':str(overlay_path),'sha256':binding['sha256']}","'overlay':deepcopy(binding)",1,T+'PatchedConsumerTests.test_real_argparse_cli_all_three_with_path_flags_and_automatic_defaults'),
 ('B1 router receipt before writes','after:canon_product_router.py','    serialized_receipt(proposal)','    pass',1,T+'PatchedConsumerTests.test_receipt_serialization_failure_precedes_every_consumer_write'),
 ('B1 assembler manifest before mkdir','after:assemble_saturday_candidate.py','    manifest_bytes = serialized_receipt(bundle_manifest).encode("utf-8")','    manifest_bytes = b""',1,T+'PatchedConsumerTests.test_receipt_serialization_failure_precedes_every_consumer_write'),
 ('B1 reconciler receipt before apply','after:reconcile_publication_receipt.py','    serialized_receipt(result)','    pass',1,T+'PatchedConsumerTests.test_receipt_serialization_failure_precedes_every_consumer_write'),
 ('B2 no incidental177 dependency',R,"need(str(root/'Run-183/RELEASE_BINDING_PROPOSAL.json') not in view.input_bindings,\n             'APPROVED_183_OVERLAY_REQUIRED')","pass",1,T+'PatchedConsumerTests.test_no_overlay_never_falls_back_when_original177_removed_or_not_ready'),
 ('B2 occupied proposal identity',R,"need(len(cells) == 9 and (cells[2] == full_title or published_title)\n                     and cells[3] == 'nightly ' + run, 'OCCUPIED_PROPOSAL_IDENTITY')","pass",1,T+'PatchedConsumerTests.test_every_occupied_effective_proposal_row_requires_exact_same_identity'),
 ('X9 no-overlay ledger CAS',R,"need(expected_ledger_sha256 is None, 'EXPLICIT_OVERLAY_REQUIRED')","pass",1,T+'PatchedConsumerTests.test_no_overlay_cannot_accept_ledger_cas_even_without183'),
 ('M1 exclude unrelated inputs from source identity','after:assemble_saturday_candidate.py','    row = metadata["ledger_row"]','    bound_sources.update(allocation.input_bindings)\n    row = metadata["ledger_row"]',1,T+'PatchedConsumerTests.test_staging_idempotency_after_unrelated_inputs_and_legacy_unaffected_bundle'),
 ('M1 run receipt excludes ledger CAS',R,"correction.pop('ledger_sha256')","pass",1,T+'PatchedConsumerTests.test_same_run_stable_receipt_changes_only_when_its_inputs_change'),
 ('M1 compare same-run allocation on staged replay','after:assemble_saturday_candidate.py','if prior.get("source_sha256") == bound_sources and same_allocation:','if prior.get("source_sha256") == bound_sources:',1,T+'PatchedConsumerTests.test_staging_idempotency_after_unrelated_inputs_and_legacy_unaffected_bundle'),
 ('M2 translate late per-run hold','after:assemble_saturday_candidate.py','return ConsumerAllocationView(view, module["AllocationHold"])','return view',1,T+'PatchedConsumerTests.test_scan_records_one_late_allocation_hold_and_continues'),
 ('D1 automatic fixed approved overlay','after:assemble_saturday_candidate.py','if allocation_correction is None and (root / "Run-183/RELEASE_BINDING_PROPOSAL.json").exists():','if False:',1,T+'PatchedConsumerTests.test_real_argparse_cli_all_three_with_path_flags_and_automatic_defaults'),
 ('C4 overlay never authorizes bind promotion','after:assemble_saturday_candidate.py','            raise AssemblyError("allocation projection does not authorize bind or promotion")','            pass',1,T+'PatchedConsumerTests.test_bind_and_promotion_cli_never_gain_authority_from_overlay'),
 ('C6 second router CAS and owned rollback','after:canon_product_router.py','    try:\n        allocation.revalidate()\n        write_json_atomic(proposal_path, proposal)','    try:\n        write_json_atomic(proposal_path, proposal)',1,T+'PatchedConsumerTests.test_router_second_cas_removes_only_its_owned_route_on_race'),
]

RUNNER='''import json,sys,unittest
class Counts(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.infrastructure_errors=0
 def addError(self,test,error):
  if issubclass(error[0],(ImportError,SyntaxError))or type(test).__name__=="_FailedTest":self.infrastructure_errors+=1
  super().addError(test,error)
r=unittest.TextTestRunner(resultclass=Counts).run(unittest.defaultTestLoader.loadTestsFromName(sys.argv[1]))
print("COUNTS:"+json.dumps(dict(tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),infrastructure_errors=r.infrastructure_errors)))
raise SystemExit(not r.wasSuccessful())
'''

def sha(raw):return hashlib.sha256(raw).hexdigest()

def clone(repo,root):
 for relative in (R,'tools/tests/test_effective_allocation.py'):
  p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/relative,p)
 shutil.copytree(repo/'tools/allocation_correction',root/'tools/allocation_correction',ignore=shutil.ignore_patterns('__pycache__'))

def mutate_consumer(root,target,old,new,count):
 bundle=root/'tools/allocation_correction';spec={ '__file__':str(bundle/'build_patches.py'),'__name__':'mutation_build'}
 exec(compile((bundle/'build_patches.py').read_bytes(),str(bundle/'build_patches.py'),'exec'),spec)
 manifest=json.loads((bundle/'PATCH_MANIFEST.json').read_bytes());before=(bundle/'before'/(target+'.txt')).read_text();after=spec['TRANSFORMS'][target][0](before);at=after.index('\ndef read_json(');after=after[:at]+spec['loader'](spec['TRANSFORMS'][target][1])+after[at:]
 after=spec['once'](after,'    args = parser.parse_args()', '''    parser.add_argument("--allocation-correction", type=Path)
    parser.add_argument("--allocation-correction-sha256")
    parser.add_argument("--expected-ledger-sha256")
    args = parser.parse_args()''')
 assert after.count(old)==count,(target,old,after.count(old));changed=after.replace(old,new);ast.parse(changed)
 relative='RESEARCH_PIPELINE_v2/'+target;patch=''.join(difflib.unified_diff(before.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile='a/'+relative,tofile='b/'+relative)).encode();(bundle/'patches'/(target+'.patch')).write_bytes(patch)
 manifest['sources'][target].update(after_sha256=sha(changed.encode()),patch_sha256=sha(patch));(bundle/'PATCH_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n');return sha(after.encode()),sha(changed.encode())

def main():
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();rows=[];started=time.monotonic();logs=a.output.with_suffix('.logs');logs.mkdir()
 for index,(name,target,old,new,count,test)in enumerate(M,1):
  if time.monotonic()-started>500:raise SystemExit('bounded mutation budget exceeded')
  pair=[];source_pair=None
  for changed in (False,True):
   with tempfile.TemporaryDirectory(prefix='allocation-mutant-')as temp:
    root=Path(temp).resolve();clone(repo,root)
    if changed:
     if target.startswith('after:'):source_pair=mutate_consumer(root,target[6:],old,new,count)
     else:
      path=root/target;raw=path.read_text();assert raw.count(old)==count,(name,raw.count(old));value=raw.replace(old,new);ast.parse(value);path.write_text(value);source_pair=(sha(raw.encode()),sha(value.encode()))
      subprocess.run([sys.executable,'-B',str(root/'tools/allocation_correction/build_patches.py')],check=True,capture_output=True)
    r=subprocess.run([sys.executable,'-B','-c',RUNNER,test],cwd=root/'tools/tests',capture_output=True,text=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},timeout=25)
    log=logs/(f'{index:02d}-'+('mutant.log'if changed else'control.log'));log.write_text(r.stdout+r.stderr)
    values=[line[7:]for line in r.stdout.splitlines()if line.startswith('COUNTS:')];counts=json.loads(values[0])if len(values)==1 else {}
    ok=counts.get('tests_run',0)>0 and counts.get('errors')==0 and counts.get('infrastructure_errors')==0
    status=('KILLED'if r.returncode!=0 and counts.get('failures',0)>0 and ok else'HOLD')if changed else('PASS'if r.returncode==0 and counts.get('failures')==0 and ok else'HOLD')
    pair.append(dict(result=status,returncode=r.returncode,counts=counts,log=str(log),log_sha256=sha(log.read_bytes())))
  result='KILLED'if pair[0]['result']=='PASS'and pair[1]['result']=='KILLED'else'HOLD';rows.append(dict(name=name,target=target,test=test,result=result,source_before_after_sha256=source_pair,baseline=pair[0],mutated=pair[1]));print(name+': '+result,flush=True)
 receipt=dict(status='PASS'if all(r['result']=='KILLED'for r in rows)else'HOLD',mutants=rows,declared_mutants=len(M),killed=sum(r['result']=='KILLED'for r in rows),python=sys.version,elapsed_seconds=round(time.monotonic()-started,3),source_sha256=sha((repo/R).read_bytes()),test_sha256=sha((repo/'tools/tests/test_effective_allocation.py').read_bytes()),builder_sha256=sha((repo/'tools/allocation_correction/build_patches.py').read_bytes()),runner_sha256=sha(Path(__file__).read_bytes()),counts_policy='assertion failures only; zero errors or infrastructure errors',no_core_or_network_actions=True)
 with a.output.open('x')as f:json.dump(receipt,f,indent=2)
 print(json.dumps({k:receipt[k]for k in ('status','killed','declared_mutants','elapsed_seconds')}));return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
