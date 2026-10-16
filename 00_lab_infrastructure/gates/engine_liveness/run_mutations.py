"""Behavioral mutants, including semantic ports of auditor R1-R20.

Refactored R9 applies to both issuance callsites; R12/R13 target the current
canonical FIFO report instead of the obsolete overwritten report dictionary.
An anchor, parse, import, or fixture-hash failure is never counted as a kill.
"""
from pathlib import Path
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
MUTANTS = [('third_request_allowed', 'scheduler_liveness.py', 'if len(active) >= 2:', 'if len(active) >= 3:'),
 ('ambiguous_request_redispatched',
  'scheduler_liveness.py',
  'return {"dispatch": False, "request": row}',
  'return {"dispatch": True, "request": row}'),
 ('owner_not_required', 'scheduler_liveness.py', 'if not self._owned:', 'if False:'),
 ('concurrent_owner_allowed',
  'scheduler_liveness.py',
  'fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)',
  'pass'),
 ('candidate_drift_reused', 'scheduler_liveness.py', 'if previous == identity:', 'if previous.run_id == identity.run_id and previous.request_sha256 == identity.request_sha256:'),
 ('receipt_identity_ignored',
  'scheduler_liveness.py',
  'if request.get("identity") != asdict(identity) or result.get("identity") != asdict(identity):',
  'if False:'),
 ('kernel_gates_ignored',
  'scheduler_liveness.py',
  'if any(result.get(name) is not True for name in (',
  'if False and any(result.get(name) is not True for name in ('),
 ('issuer_validation_ignored',
  'scheduler_liveness.py',
  'if validate_certificate(identity, result) is not True:',
  'if False:'),
 ('release_gap_skipped',
  'scheduler_liveness.py',
  'if identity.key not in completed or identity.key not in admitted:\n                break',
  'if identity.key not in completed or identity.key not in admitted:\n                continue'),
 ('release_admission_ignored',
  'scheduler_liveness.py',
  'if identity.key not in completed or identity.key not in admitted:',
  'if identity.key not in completed:'),
 ('younger_grants_oldest_credit',
  'scheduler_liveness.py',
  'return [run for run in targets if run in certified_runs]',
  'return list(certified_runs)'),
 ('terminal_hold_dispatched',
  'scheduler_liveness.py',
  '            if terminal_hold:\n                continue',
  '            if False:\n                continue'),
 ('immutable_collision_ignored', 'scheduler_liveness.py', 'if path.read_bytes() != encoded:', 'if False:'),
 ('rejected_request_can_accept',
  'scheduler_liveness.py',
  'if any(row["identity"] == asdict(identity) for row in self._rows("terminal")):',
  'if False:'),
 ('request_digest_reused',
  'scheduler_liveness.py',
  'if previous.request_sha256 == identity.request_sha256:',
  'if False:'),
 ('result_symlink_accepted',
  'scheduler_liveness.py',
  'if path.is_symlink() or path.parent.is_symlink():',
  'if False:'),
 ('stdout_prose_copied',
  'scheduler_liveness.py',
  'return match.group(1) if match else "UNAVAILABLE"',
  'return error if match else "UNAVAILABLE"'),
 ('review_contradiction_ignored',
  'scheduler_liveness.py',
  'return bool(re.search(',
  'return False and bool(re.search('),
 ('source_escape_ignored',
  'scheduler_liveness.py',
  'raise LivenessHold("HOLD_PAPER_SOURCE_ESCAPE") from exc',
  'return False'),
 ('due_generation_skipped',
  'scheduler_liveness.py',
  'generation = generation_step() if generation_due else None',
  'generation = None'),
 ('terminal_provider_validation_ignored',
  'scheduler_liveness.py',
  'cloud = validate_terminal_rejection(identity, provider_receipt, provider_receipt_sha256)',
  'cloud = json.loads(provider_receipt.read_text())'),
 ('reservation_directory_not_flushed',
  'scheduler_liveness.py',
  '        fsync_directory(path.parent)',
  '        pass'),
 ('new_directory_ancestry_not_flushed',
  'scheduler_liveness.py',
  '        fsync_directory(directory.parent)',
  '        pass'),
 ('accepted_result_artifact_drift_ignored',
  'checkpoint_certification_lane.py',
  'if current != _result_payload(accepted[identity.key]):',
  'if False:'),
 ('24_hour_fifo_alert_delayed',
  'checkpoint_advisory.py',
  'if seconds >= 24 * 3600:',
  'if seconds > 24 * 3600:'),
 ('terminal_row_validation_bypassed',
  'scheduler_liveness.py',
  'cloud = validate_terminal_rejection(identity, Path(receipt), value.get("provider_receipt_sha256"))',
  'cloud = {"provider_response": {"output": value.get("failing_goal", "")}}'),
 ('R1 terminal rejection never frees slot',
  'scheduler_liveness.py',
  'for folder in ("results", "terminal") for row in self._rows(folder)}',
  'for folder in ("results",) for row in self._rows(folder)}'),
 ('R2 publish non-contiguous prefix (skip unadmitted gap)',
  'scheduler_liveness.py',
  'if identity.key not in completed or identity.key not in admitted:\n                break',
  'if identity.key not in completed:\n'
  '                break\n'
  '            if identity.key not in admitted:\n'
  '                continue'),
 ('R3 younger acceptance credits oldest target',
  'scheduler_liveness.py',
  'return [run for run in targets if run in certified_runs]',
  'return [run for run in targets if certified_runs]'),
 ('R4 request/candidate input drift accepted (receipt reuse)',
  'checkpoint_certification_lane.py',
  'if any(inputs.get(path.name) != file_digest(path) for name, path in paths.items() if name != "request"):',
  'if False:'),
 ('R5 pre-existing receipt/certificate outputs reused',
  'checkpoint_certification_lane.py',
  'if not held and identity.key not in reserved_keys and any(Path(entry[key]).exists() for key in '
  '("receipt_output", "certificate_output")):',
  'if False:'),
 ('R6 adapter ignores dispatch:false (resend/3+ in flight)',
  'checkpoint_certification_lane.py',
  'work = [(identity, entry, paths) for identity, entry, paths, _ in prepared if identity.request_sha256 in '
  'selected]',
  'work = [(identity, entry, paths) for identity, entry, paths, held in prepared if not held]'),
 ('R7 adapter drops non-vacuity gate',
  'checkpoint_certification_lane.py',
  '"nonvacuity_witnesses", "premise_declaration", "allowed_axioms_only",',
  '"premise_declaration", "allowed_axioms_only",'),
 ('R8 adapter accepts local Lean execution',
  'checkpoint_certification_lane.py',
  ' or gates.get("local_lean_execution") is not False):',
  '):'),
 ('R9 issuer premise flag dropped (all issuance sites)',
  'checkpoint_certification_lane.py',
  'output_path=Path(entry["certificate_output"]), require_premise_declaration=True)',
  'output_path=Path(entry["certificate_output"]), require_premise_declaration=False)'),
 ('R10 unvalidated terminal_hold skips FIFO dispatch',
  'checkpoint_certification_lane.py',
  '    if value is None:\n        return False\n',
  '    if value is None:\n        return False\n    return True\n'),
 ('R11 rejection failing goal not bound to provider output',
  'scheduler_liveness.py',
  'if failing_goal not in str(cloud["provider_response"].get("output", "")):',
  'if False:'),
 ('R12 24h alert drops failing goal',
  'checkpoint_advisory.py',
  'fields["status"] = "ALERT"',
  'fields["status"] = "ALERT"; fields.pop("failing_goal", None)'),
 ('R13 missing held_hours reported as 0',
  'checkpoint_advisory.py',
  'fields.update(status="UNAVAILABLE", held_seconds=None, held_hours=None)',
  'fields.update(status="UNAVAILABLE", held_seconds=None, held_hours=0)'),
 ('R14 lint scope unbounded (all debts)',
  'checkpoint_advisory.py',
  'for run in debt[:2]:',
  'for run in debt:'),
 ('R15 advisory exception propagates (G2)',
  'G2_EXISTING_CHECKPOINT.patch',
  '+    except Exception:\n+        pass',
  '+    except Exception:\n+        raise'),
 ('R16 advisory child unbounded (no timeout, G2)',
  'G2_EXISTING_CHECKPOINT.patch',
  'timeout=15, check=False)',
  'timeout=None, check=False)'),
 ('R17 lane HOLD reported to scheduler as exit 0 (G2)',
  'G2_EXISTING_CHECKPOINT.patch',
  '+            return 2 if result["status"] == "HOLD" else 0',
  '+            return 0'),
 ('R18 rollback flag (active:false) ignored',
  'checkpoint_certification_lane.py',
  'or policy.get("active") is not True or policy.get("max_in_flight") != 2',
  'or policy.get("max_in_flight") != 2'),
 ('R19 installed source closure unchecked',
  'checkpoint_certification_lane.py',
  'if set(bindings) != required or any(file_digest(pipeline / name) != bindings[name] for name in required):',
  'if False:'),
 ('R20 reviewed-installation evidence unchecked',
  'checkpoint_certification_lane.py',
  'if (installation.get("merged_by") != "Justin" or installation.get("ci") != "PASS"',
  'if False and (installation.get("merged_by") != "Justin" or installation.get("ci") != "PASS"')]
# Keep the two independently protected issuance paths separately observable.
MUTANTS.extend([
    ("R9 initial issuer premise flag dropped", "checkpoint_certification_lane.py",
     'cloud_receipt_path=Path(entry["receipt_output"]),\n                        output_path=Path(entry["certificate_output"]), require_premise_declaration=True)',
     'cloud_receipt_path=Path(entry["receipt_output"]),\n                        output_path=Path(entry["certificate_output"]), require_premise_declaration=False)'),
    ("R9 resumed issuer premise flag dropped", "checkpoint_certification_lane.py",
     'cloud_receipt_path=receipt,\n                          output_path=Path(entry["certificate_output"]), require_premise_declaration=True)',
     'cloud_receipt_path=receipt,\n                          output_path=Path(entry["certificate_output"]), require_premise_declaration=False)'),
])


# Round-2 semantic regressions: genuine deployed failures, rollback and stack ownership.
MUTANTS.extend([
    ("B2 success-path phases incorrectly required for rejection", "scheduler_liveness.py",
     '    request_id = response.get("requestId")',
     '    from job_observation_policy import assess_job_observation\n    if assess_job_observation(response, request, identity.statement_sha256, identity.candidate_sha256).get("status") != "OBSERVATION_MATCH_PARTIAL":\n        raise LivenessHold("HOLD_REJECTION_OBSERVATION")\n    request_id = response.get("requestId")'),
    ("B2 served request ID ignored", "scheduler_liveness.py",
     'or delivery.get("servedForRequestId") != request_id', 'or False'),
    ("B2 fresh delivery ignored", "scheduler_liveness.py",
     'or delivery.get("mode") != "FRESH_EXECUTION"', 'or False'),
    ("B2 termination standard ignored", "scheduler_liveness.py",
     'terminal.get("standard") != "VRS-COMPARATOR-TERMINATION-1"', 'False'),
    ("B2 recorded capture ignored", "scheduler_liveness.py",
     'or terminal.get("capture_status") != "RECORDED"', 'or False'),
    ("B2 terminal request ID ignored", "scheduler_liveness.py",
     'or terminal.get("requestId") != response.get("requestId")', 'or False'),
    ("B2 phase record request ID ignored", "scheduler_liveness.py",
     'and row.get("requestId") == response.get("requestId")', 'and True'),
    ("B2 zero exit code accepted", "scheduler_liveness.py",
     'and row["exitCode"] != 0', 'and True'),
    ("B2 boolean exit code accepted", "scheduler_liveness.py",
     'type(row.get("exitCode")) is int', 'isinstance(row.get("exitCode"), int)'),
    ("B2 non-exited termination accepted", "scheduler_liveness.py",
     'and row.get("reason") == "exited"', 'and True'),
    ("B2 signal termination accepted", "scheduler_liveness.py",
     'and row.get("signal") is None', 'and True'),
    ("B2 guard termination accepted", "scheduler_liveness.py",
     'and row.get("guard_fired") is False', 'and True'),
    ("B2 output hash ignored on terminal read", "scheduler_liveness.py",
     'if value.get("provider_output_sha256") != hashlib.sha256(output.encode()).hexdigest():', 'if False:'),
    ("B2 rollback refuses FINISH", "checkpoint_certification_lane.py",
     '(not reconcile_only and (start_path.parent / "FINISH.json").exists())',
     '(start_path.parent / "FINISH.json").exists()'),
    ("B2 per-run premise hold aborts drain", "checkpoint_certification_lane.py",
     'preflight_holds[identity.key] = "HOLD_QUEUE_PREMISE_PREFLIGHT"',
     'raise LivenessHold("HOLD_QUEUE_PREMISE_PREFLIGHT")'),
    ("B1 advisory freezes after 200 reservations", "checkpoint_advisory.py",
     'fields["reservation_evidence_budget"] = "LIMITED_TO_200"',
     'raise ValueError("FIFO reservation evidence budget")'),
    ("B1 advisory freezes after 20 premise holds", "checkpoint_advisory.py",
     'fields["hold_evidence_budget"] = "LIMITED_TO_20"',
     'raise ValueError("FIFO HOLD evidence budget")'),
    ("S8 second controller dispatch route retained", "scheduler_liveness.py",
     '    return "DRAIN_SCHEDULER_CERTIFICATION_LANE"',
     '    return "CERTIFY_COMPARATOR_FIFO"'),
    ("G1 finalized conflict guard ignored in composed controller", "G1_CONTROLLER_EXECUTOR.patch",
     '+    if pending_finalized_review:', '+    if pending_finalized_review and False:'),
    ("installer before-hash mismatch ignored", "install_integration.py",
     'if hashlib.sha256(raw).hexdigest() != row["before_sha256"]:', 'if False:'),
])


MUTANTS.extend([
    ("N1 installer executes unchecked cached helper", "install_integration.py",
     '    exec(compile(terminal_raw, str(terminal), "exec"), module.__dict__)',
     '    import importlib.util\n    spec = importlib.util.spec_from_file_location("_checked_terminal_helper", terminal)\n    spec.loader.exec_module(module)'),
    ("N1 installer imports unchecked local dependency cache", "install_integration.py",
     'HELPERS = (', 'import scheduler_liveness\n\nHELPERS = ('),
    ("N2 terminal original blocks younger certificate visibility", "checkpoint_certification_lane.py",
     'prefix = lane.publication_prefix(certification_order, accepted)',
     'prefix = lane.publication_prefix([identity for identity, _, _, _ in prepared], accepted)'),
    ("N2 terminal exclusion not reauthenticated before visibility", "checkpoint_certification_lane.py",
     'if not terminal_hold(entry, identity, lane.root.parent):', 'if False:'),
])


def refresh_checkpoint_binding(root):
    with tempfile.TemporaryDirectory() as directory:
        target=Path(directory)/"RESEARCH_PIPELINE_v2/nightly_checkpoint.py"
        target.parent.mkdir();shutil.copyfile(root/"tests/fixtures/nightly_checkpoint.py.txt",target)
        applied=subprocess.run(["git","apply","--unidiff-zero",str(root/"G2_EXISTING_CHECKPOINT.patch")],cwd=directory,capture_output=True)
        if applied.returncode: raise RuntimeError("mutant patch does not apply")
        ast.parse(target.read_text())
        value=json.loads((root/"INTEGRATION_BINDING.json").read_text())
        for row in value["files"]:
            if row["path"].endswith("/nightly_checkpoint.py"):
                row["after_sha256"]=hashlib.sha256(target.read_bytes()).hexdigest()
        (root/"INTEGRATION_BINDING.json").write_text(json.dumps(value))


def run():
    environment={**os.environ,"VIRIDIS_LIVENESS_REPO_ROOT":str(HERE.parents[2])}
    command=[sys.executable,"-B","-m","unittest","discover","-s",str(HERE/"tests"),"-v"]
    baseline=subprocess.run(command,capture_output=True,text=True,timeout=60,env=environment)
    if baseline.returncode: raise RuntimeError("baseline tests must pass before mutation scoring")
    results=[]
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)/"engine_liveness"
        shutil.copytree(HERE,root,ignore=shutil.ignore_patterns("__pycache__"))
        command[-2]=str(root/"tests")
        for name,target,original,replacement in MUTANTS:
            path=root/target;before=path.read_bytes();text=before.decode()
            count=text.count(original)
            expected=2 if name.endswith("(all issuance sites)") else 1
            if count!=expected: raise RuntimeError("mutation anchor mismatch: "+name+" count="+str(count))
            changed=text.replace(original,replacement)
            if path.suffix==".py": compile(changed,name,"exec")
            binding=(root/"INTEGRATION_BINDING.json").read_bytes()
            path.write_text(changed)
            if path.suffix==".patch":
                if path.name == "G2_EXISTING_CHECKPOINT.patch":
                    refresh_checkpoint_binding(root)
                else:
                    with tempfile.TemporaryDirectory() as staging:
                        pipe = Path(staging) / "RESEARCH_PIPELINE_v2"; pipe.mkdir()
                        predecessor = HERE.parent / "terminal_certification"
                        parent_binding = json.loads((predecessor / "INTEGRATION_BINDING.json").read_text())
                        for row in parent_binding["files"]:
                            shutil.copyfile(HERE.parents[2] / row["snapshot"], Path(staging) / row["path"])
                        parent_applied = subprocess.run(["git", "apply", "--unidiff-zero", str(predecessor / "EXISTING_SELECTION.patch")],
                                                        cwd=staging, capture_output=True)
                        if parent_applied.returncode: raise RuntimeError("exact predecessor patch does not apply")
                        shutil.copyfile(root / "tests/fixtures/autonomous_transition_executor.py.txt", pipe / "autonomous_transition_executor.py")
                        applied = subprocess.run(["git", "apply", "--unidiff-zero", str(path)], cwd=staging, capture_output=True)
                        if applied.returncode: raise RuntimeError("mutated composed patch does not apply")
                        value = json.loads((root / "INTEGRATION_BINDING.json").read_text())
                        for row in value["files"]:
                            output = pipe / Path(row["path"]).name
                            if output.exists(): row["after_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
                        (root / "INTEGRATION_BINDING.json").write_text(json.dumps(value))
            # Refresh integrity envelopes so only semantic assertions can score.
            value = json.loads((root / "INTEGRATION_BINDING.json").read_text())
            for source_name in value["source_files"]:
                value["source_files"][source_name] = hashlib.sha256((root / source_name).read_bytes()).hexdigest()
            (root / "INTEGRATION_BINDING.json").write_text(json.dumps(value))
            process=subprocess.run(command,capture_output=True,text=True,timeout=60,env=environment)
            failures=sorted(set(re.findall(r"^FAIL: (\w+)",process.stderr,re.M)))
            # ERRORs alone, source-hash guards alone and infrastructure failures
            # do not establish a behavioral kill.
            behavioral=[test for test in failures if test not in {"test_actual_checkpoint_patch_hashes_and_drains_original_start"}]
            results.append({"mutant":name,"killed":bool(process.returncode and behavioral),"behavioral_failures":behavioral,
                            "returncode":process.returncode,"errors":re.findall(r"^ERROR: (\w+)",process.stderr,re.M)})
            path.write_bytes(before);(root/"INTEGRATION_BINDING.json").write_bytes(binding)
    value={"standard":"VRS-LIVENESS-MUTATION-EVIDENCE-2","total":len(results),"killed":sum(r["killed"] for r in results),"results":results}
    print(json.dumps(value,indent=2));return 0 if value["total"]==value["killed"] else 1

if __name__=="__main__":raise SystemExit(run())
