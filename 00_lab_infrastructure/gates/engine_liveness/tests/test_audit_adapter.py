"""Independent-audit regressions on the real adapter and canonical outputs."""
import json
import ast
from copy import deepcopy
import datetime as dt
import os
from types import SimpleNamespace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import checkpoint_certification_lane as adapter
from scheduler_liveness import LivenessHold, SchedulerLane, file_digest
import test_checkpoint_adapter as fixture
from liveness_fixtures import write_rejection


class AuditAdapterTests(unittest.TestCase):
    setUp = fixture.CheckpointAdapterTests.setUp
    verifier = fixture.CheckpointAdapterTests.verifier
    write_queue = fixture.CheckpointAdapterTests.write_queue
    drain = fixture.CheckpointAdapterTests.drain

    def entry(self, number, suffix=""):
        folder = self.pipeline / "lean_certificates" / f"Run-{number}"
        folder.mkdir(parents=True, exist_ok=True)
        statement, candidate = folder / "statement.lean", folder / "candidate.lean"
        statement.write_text("frozen statement"); candidate.write_text("frozen candidate")
        request = folder / ("request" + suffix + ".json")
        request.write_text(json.dumps({"source_run": f"Run-{number}", "toolchain": "leanprover/lean4:v4.28.0",
            "mathlib_rev": "b" * 40, "local_lean_execution": False, "revision": suffix,
            "input_sha256": {statement.name: file_digest(statement), candidate.name: file_digest(candidate)}}))
        return {"run_id": f"Run-{number}", **{name: {"path": str(path), "sha256": file_digest(path)}
            for name, path in (("request", request), ("formal_statement", statement), ("candidate", candidate))},
            "receipt_output": str(folder / ("receipt" + suffix + ".json")),
            "certificate_output": str(folder / ("certificate" + suffix + ".json"))}

    def next_checkpoint(self, entries, invocation="next"):
        self.entries = entries
        self.start = self.pipeline / "nightly_checkpoints" / invocation / "START.json"
        self.start.parent.mkdir(parents=True)
        self.start.write_text(json.dumps({"science": {"certification": {"backlog_runs": [e["run_id"] for e in entries]}}}))
        self.queue = self.start.parent / "QUEUE.json"
        self.write_queue()

    def complete_files(self, identity, entry, paths):
        _, certificate = self.verifier(identity, entry, paths)
        receipt = Path(entry["receipt_output"])
        receipt.write_text(json.dumps({"status": "VERIFIED"}))
        certificate["bindings"]["independent_cloud_receipt"]["sha256"] = file_digest(receipt)
        Path(entry["certificate_output"]).write_text(json.dumps(certificate))
        return {"status": "VERIFIED"}, certificate

    def test_B2_authenticated_rejections_free_slots_and_all_blocked_items_report(self):
        calls = []
        def reject(identity, entry, paths):
            calls.append(identity.key)
            return write_rejection(identity, entry), {}
        self.drain(reject)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(list((self.pipeline / "parallel_certification/terminal").glob("*.json"))), 2)
        extra = [self.entry(196), self.entry(197)]
        self.next_checkpoint(self.entries + extra)
        calls.clear()
        def accept(identity, entry, paths):
            calls.append(identity.run_id)
            return self.verifier(identity, entry, paths)
        result = self.drain(accept)
        self.assertEqual(calls, ["Run-196", "Run-197"])
        self.assertEqual(result["accepted"], ["Run-196", "Run-197"])
        self.assertEqual({h["run_id"] for h in result["holds"]}, {"Run-194", "Run-195"})
        calls.clear()
        self.drain(accept)
        self.assertEqual(calls, [], "all send counters are asserted outside swallowed callback exceptions")

    def test_B2_successor_identity_does_not_retry_old_rejected_request_or_abort_younger(self):
        old194 = self.entries[0]
        def first(identity, entry, paths):
            return (write_rejection(identity, entry), {}) if identity.run_id == "Run-194" else self.verifier(identity, entry, paths)
        self.drain(first)
        successor = self.entry(194, "_reviewed_r2")
        extra = self.entry(196)
        self.next_checkpoint([successor, self.entries[1], extra])
        calls = []
        def send(identity, entry, paths):
            calls.append(identity.request_sha256)
            return self.verifier(identity, entry, paths)
        self.drain(send)
        self.assertEqual(calls, [successor["request"]["sha256"], extra["request"]["sha256"]])
        self.assertNotIn(old194["request"]["sha256"], calls)

    def test_B2_ambiguity_never_sends_again_and_reports_younger_capacity_hold(self):
        calls = []
        def ambiguous(identity, entry, paths):
            calls.append(identity.key)
            raise TimeoutError("unknown provider state")
        self.drain(ambiguous)
        self.assertEqual(len(calls), 2)
        self.next_checkpoint(self.entries + [self.entry(196)])
        calls.clear()
        result = self.drain(ambiguous)
        self.assertEqual(calls, [])
        self.assertEqual({h["run_id"] for h in result["holds"]}, {"Run-194", "Run-195", "Run-196"})
        self.assertEqual(next(h["code"] for h in result["holds"] if h["run_id"] == "Run-196"), "HOLD_TWO_REQUEST_LIMIT")

    def test_B2_outputs_arriving_after_ambiguity_are_reconciled_without_transport(self):
        calls = []
        def ambiguous(identity, entry, paths):
            calls.append(identity.key)
            raise TimeoutError()
        self.drain(ambiguous)
        for entry in self.entries:
            identity, paths = adapter.identity_for(entry, self.pipeline)
            held = adapter._held_entry(SchedulerLane(self.pipeline / "parallel_certification"), identity, entry)
            self.complete_files(identity, held, paths)
        calls.clear()
        result = self.drain(ambiguous)
        self.assertEqual(calls, [])
        self.assertEqual(result["accepted"], ["Run-194", "Run-195"])
        self.assertEqual(result["canonical_certificates"], ["Run-194", "Run-195"])

    def test_B3_A1_younger_certificate_is_not_canonical_while_oldest_delayed(self):
        def delayed(identity, entry, paths):
            if identity.run_id == "Run-194":
                raise TimeoutError()
            return self.verifier(identity, entry, paths)
        result = self.drain(delayed)
        self.assertEqual(result["accepted"], ["Run-195"])
        self.assertEqual(result["canonical_certificates"], [])
        self.assertFalse(Path(self.entries[1]["certificate_output"]).exists())
        self.assertEqual(len(list((self.pipeline / "parallel_certification/verified-results").glob("*/certificate.json"))), 1)

    def test_B3_A7_restored_oldest_promotes_only_actual_contiguous_prefix(self):
        third = self.entry(196)
        self.next_checkpoint(self.entries + [third], "three")
        def delayed(identity, entry, paths):
            if identity.run_id != "Run-195":
                raise TimeoutError()
            return self.verifier(identity, entry, paths)
        self.drain(delayed)
        identity, paths = adapter.identity_for(self.entries[0], self.pipeline)
        held = adapter._held_entry(SchedulerLane(self.pipeline / "parallel_certification"), identity, self.entries[0])
        self.complete_files(identity, held, paths)
        result = self.drain(delayed)
        self.assertEqual(result["canonical_certificates"], ["Run-194", "Run-195"])
        self.assertTrue(Path(self.entries[0]["certificate_output"]).exists())
        self.assertTrue(Path(self.entries[1]["certificate_output"]).exists())
        self.assertFalse(Path(third["certificate_output"]).exists())

    def publication_source(self, run):
        # Execute the actual current source_for_cycle function and its first
        # admission gate. Only downstream scientific-policy work is stubbed.
        repo=Path(os.environ.get("VIRIDIS_LIVENESS_REPO_ROOT",str(Path(__file__).resolve().parents[4])))
        source=repo/"00_lab_infrastructure/gates/nightly_release_checkpoint.py"
        tree=ast.parse(source.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="source_for_cycle")
        rows=[]
        for entry in self.entries:
            certified=Path(entry['certificate_output']).exists()
            rows.append({'id':entry['run_id'],'status':'CERTIFIED' if certified else 'UNCERTIFIED',
                'certificate_valid':certified,'certificate':entry['certificate_output'],'path':str(Path(entry['request']['path']).parent)})
        (self.pipeline/'corpus_ledger.json').write_text(json.dumps({'tree_root':str(self.pipeline.parent.resolve()),'run_entities':rows}))
        def need(condition,code):
            if not condition: raise LivenessHold(code)
        policy=SimpleNamespace(canonical_run=lambda value:value,need=need,binding=lambda path:{'path':str(path)},
            snapshot_certificate=lambda *a:({'foundation_basis':'THEOREM'},{'certified_theorems':['fixture']}),
            fresh_target=lambda *a:None,SOURCE_STANDARD='FIXTURE',source_sha=lambda:'source',
            source_values=lambda *a:None,finish=lambda *a:None)
        namespace={'Path':Path,'json':json,'policy':policy,'digest':SimpleNamespace(read_regular=lambda p:p.read_bytes()),'deepcopy':deepcopy,'dt':dt}
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(source),'exec'),namespace)
        return namespace['source_for_cycle'](self.pipeline.parent,run,{}, {}, {},selection_invocation='actual-test')

    def test_B3_actual_publication_source_refuses_held_younger_then_admits_prefix_only(self):
        third=self.entry(196);self.next_checkpoint(self.entries+[third],'publication')
        def delayed(identity,entry,paths):
            if identity.run_id!='Run-195': raise TimeoutError()
            return self.verifier(identity,entry,paths)
        self.drain(delayed)
        with self.assertRaisesRegex(LivenessHold,'ELIGIBLE_CURRENT_MAIN_CERTIFICATE_ONLY'):
            self.publication_source('Run-195')
        identity,paths=adapter.identity_for(self.entries[0],self.pipeline)
        self.complete_files(identity,adapter._held_entry(SchedulerLane(self.pipeline/'parallel_certification'),identity,self.entries[0]),paths)
        self.drain(delayed)
        self.assertEqual(self.publication_source('Run-194')['run_id'],'Run-194')
        self.assertEqual(self.publication_source('Run-195')['run_id'],'Run-195')
        with self.assertRaisesRegex(LivenessHold,'ELIGIBLE_CURRENT_MAIN_CERTIFICATE_ONLY'):
            self.publication_source('Run-196')

    def test_B1_authenticated_lane_head_populates_goal_candidate_receipt_and_timestamp(self):
        import checkpoint_advisory as advisory
        def reject(identity,entry,paths):return write_rejection(identity,entry),{}
        self.drain(reject)
        result=advisory.fifo_head(self.pipeline.parent.resolve(),json.loads(self.start.read_text()))
        self.assertEqual(result['run_id'],'Run-194')
        self.assertEqual(result['failing_goal'],'exact failing goal')
        self.assertEqual(result['candidate_sha256'],self.entries[0]['candidate']['sha256'])
        self.assertEqual(result['provider_receipt'],{'path':str(Path(self.entries[0]['receipt_output']).resolve()),
            'sha256':file_digest(Path(self.entries[0]['receipt_output']))})
        self.assertNotEqual(result['held_since_utc'],'UNAVAILABLE')
        self.assertGreaterEqual(result['held_seconds'],0)

    def test_terminal_hold_rechecks_exact_checker_and_skips_dispatch_without_release(self):
        checker=self.pipeline/'verification_coverage_gates/premise_declaration.py'
        checker.write_text('def validate_envelope(request,*args,**kwargs):\n return {"status":"HOLD"} if "Run-194" in str(request) else {"status":"PASS","historical_exemption":False}\n')
        entry=self.entries[0];identity,_=adapter.identity_for(entry,self.pipeline)
        hold=self.pipeline/'terminal194.json'
        hold.write_text(json.dumps({'schema_version':'VRS-CERTIFICATION-PREMISE-HOLD-1','run_id':'Run-194',
            'status':'HOLD_PREMISE_DECLARATION','terminal_for_sealed_object':True,'certificate_issued':False,
            'checker_result':{'status':'HOLD','certifies':False,'local_lean_execution':False},
            'bindings':{'request_sha256':identity.request_sha256,'formal_statement_sha256':identity.statement_sha256,
                'candidate_sha256':identity.candidate_sha256,'premise_checker_sha256':file_digest(checker)}}))
        entry['terminal_hold']={'path':str(hold),'sha256':file_digest(hold)};self.write_queue();calls=[]
        def send(identity,entry,paths):calls.append(identity.run_id);return self.verifier(identity,entry,paths)
        # A self-asserted HOLD cannot create a different terminal policy from #109.
        with self.assertRaisesRegex(LivenessHold, 'TERMINAL_HOLD_BINDING'):
            self.drain(send)
        self.assertEqual(calls, [])

    def test_R9_reconciliation_issuer_requires_premise_without_resending(self):
        from types import SimpleNamespace
        calls=[]
        self.drain(lambda *args: (_ for _ in ()).throw(TimeoutError()))
        entry=self.entries[0];identity,paths=adapter.identity_for(entry,self.pipeline)
        Path(entry['receipt_output']).write_text(json.dumps({'status':'VERIFIED'}))
        def issue(**kwargs):
            calls.append(kwargs)
            held=adapter._held_entry(SchedulerLane(self.pipeline/'parallel_certification'),identity,entry)
            return self.verifier(identity,held,paths)[1]
        with patch.dict(sys.modules,{'issue_lean_zero_sorry_certificate':SimpleNamespace(issue=issue)}):
            sent=[];self.drain(lambda *args:sent.append(args))
        self.assertEqual(sent,[]);self.assertEqual(len(calls),1)
        self.assertIs(calls[0]['require_premise_declaration'],True)

    def test_R4_input_hash_drift_refused_before_any_send(self):
        request = Path(self.entries[0]["request"]["path"])
        value = json.loads(request.read_text()); value["input_sha256"]["candidate.lean"] = "f" * 64
        request.write_text(json.dumps(value)); self.entries[0]["request"]["sha256"] = file_digest(request); self.write_queue()
        calls = []
        with self.assertRaisesRegex(LivenessHold, "QUEUE_REQUEST_INPUT"):
            self.drain(lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_R5_fresh_preexisting_output_is_not_reused_or_sent_again(self):
        Path(self.entries[0]["receipt_output"]).write_text("preexisting receipt")
        calls = []
        with self.assertRaisesRegex(LivenessHold, "FRESH_OUTPUT_ALREADY_EXISTS"):
            self.drain(lambda *args: calls.append(args))
        self.assertEqual(calls, [])

    def test_R7_nonvacuity_is_rechecked_from_real_certificate_bytes(self):
        identity, paths = adapter.identity_for(self.entries[0], self.pipeline)
        _, cert = self.verifier(identity, self.entries[0], paths)
        cert["gates"]["nonvacuity_witnesses"] = False
        with self.assertRaisesRegex(LivenessHold, "ISSUER_RESULT_BINDING"):
            adapter._certificate_result(identity, self.entries[0], cert)

    def test_R8_local_lean_is_refused_from_real_certificate_bytes(self):
        identity, paths = adapter.identity_for(self.entries[0], self.pipeline)
        _, cert = self.verifier(identity, self.entries[0], paths)
        cert["gates"]["local_lean_execution"] = True
        with self.assertRaisesRegex(LivenessHold, "ISSUER_RESULT_BINDING"):
            adapter._certificate_result(identity, self.entries[0], cert)

    def test_R10_terminal_hold_requires_exact_source_binding(self):
        identity, _ = adapter.identity_for(self.entries[0], self.pipeline)
        hold = self.pipeline / "forged_hold.json"; hold.write_text(json.dumps({"status": "HOLD_PREMISE_DECLARATION"}))
        self.entries[0]["terminal_hold"] = {"path": str(hold), "sha256": file_digest(hold)}
        with self.assertRaisesRegex(LivenessHold, "TERMINAL_HOLD_BINDING"):
            adapter.terminal_hold(self.entries[0], identity, self.pipeline)

    def test_accepted_artifact_drift_is_checked_before_younger_transport(self):
        self.drain()
        old = Path(self.entries[0]["certificate_output"])
        value = json.loads(old.read_text()); value["scope"] = "edited"; old.write_text(json.dumps(value))
        self.next_checkpoint(self.entries + [self.entry(196)])
        calls = []
        with self.assertRaisesRegex(LivenessHold, "RESULT_ARTIFACT_DRIFT"):
            self.drain(lambda *args: calls.append(args))
        self.assertEqual(calls, [])


class PolicyGuardTests(unittest.TestCase):
    setUp = fixture.CheckpointAdapterTests.setUp
    verifier = fixture.CheckpointAdapterTests.verifier
    write_queue = fixture.CheckpointAdapterTests.write_queue

    def policy(self, **changes):
        required = {"nightly_checkpoint.py", "checkpoint_certification_lane.py", "scheduler_liveness.py",
            "job_observation_policy.py", "comparator_cloud_lean_verifier.py",
            "verification_coverage_gates/terminal_certification/terminal_hold.py", "issue_lean_zero_sorry_certificate.py",
            "verification_coverage_gates/premise_declaration.py", "checkpoint_advisory.py",
            "pipeline_advisory/checkpoint_slo_hook.py", "pipeline_advisory/pipeline_slo.py", "pipeline_advisory/lean_repair_lint.py"}
        for name in required:
            path = self.pipeline / name; path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists(): path.write_text("fixture source " + name)
        bindings = {name: file_digest(self.pipeline / name) for name in required}
        install = self.pipeline / "INSTALL.json"
        install.write_text(json.dumps({"merged_by": "Justin", "ci": "PASS", "independent_review": "PASS", "installed_source_sha256": bindings}))
        policy = {"standard": "VRS-PARALLEL-CERTIFY-ORDERED-PUBLISH-1", "active": True, "max_in_flight": 2,
            "scheduler_id": "viridis-nightly-science-generator", "installed_source_sha256": bindings,
            "reviewed_installation": {"path": str(install), "sha256": file_digest(install)}, **changes}
        (self.pipeline / "PARALLEL_CERTIFICATION_POLICY.json").write_text(json.dumps(policy))
        return policy

    def test_T2_active_false_refuses_dispatch_but_allows_reconciliation_validation(self):
        self.policy(active=False)
        with self.assertRaisesRegex(LivenessHold, "POLICY_NOT_INSTALLED"):
            adapter.validate_policy(self.pipeline)
        self.assertFalse(adapter.validate_policy(self.pipeline, reconcile_only=True)["active"])

    def test_T2_wrong_standard_owner_and_capacity_each_refuse(self):
        for changes in ({"standard": "WRONG"}, {"scheduler_id": "other"}, {"max_in_flight": 3}):
            self.policy(**changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(LivenessHold, "POLICY_NOT_INSTALLED"):
                adapter.validate_policy(self.pipeline)

    def test_T2_missing_and_changed_source_closure_each_refuse(self):
        value = self.policy(); value["installed_source_sha256"].pop("scheduler_liveness.py")
        (self.pipeline / "PARALLEL_CERTIFICATION_POLICY.json").write_text(json.dumps(value))
        with self.assertRaisesRegex(LivenessHold, "SOURCE_CLOSURE"): adapter.validate_policy(self.pipeline)
        self.policy(); (self.pipeline / "scheduler_liveness.py").write_text("drift")
        with self.assertRaisesRegex(LivenessHold, "SOURCE_CLOSURE"): adapter.validate_policy(self.pipeline)

    def test_T2_every_reviewed_installation_predicate_refuses(self):
        for field, value in (("merged_by", "other"), ("ci", "FAIL"), ("independent_review", "PENDING"), ("installed_source_sha256", {})):
            policy = self.policy(); install = self.pipeline / "INSTALL.json"
            row = json.loads(install.read_text()); row[field] = value; install.write_text(json.dumps(row))
            policy["reviewed_installation"]["sha256"] = file_digest(install)
            (self.pipeline / "PARALLEL_CERTIFICATION_POLICY.json").write_text(json.dumps(policy))
            with self.subTest(field=field), self.assertRaisesRegex(LivenessHold, "INSTALLATION_EVIDENCE"):
                adapter.validate_policy(self.pipeline)

    def test_T2_rollback_reconciles_in_flight_outputs_while_inactive_without_send_or_promotion(self):
        self.policy()
        with patch.dict(sys.modules, self.modules), patch.object(adapter, "_verify_one", side_effect=TimeoutError()):
            adapter.drain_checkpoint(self.start, self.queue, pipeline=self.pipeline)
        for entry in self.entries:
            identity, paths = adapter.identity_for(entry, self.pipeline)
            held = adapter._held_entry(SchedulerLane(self.pipeline / "parallel_certification"), identity, entry)
            _, cert = self.verifier(identity, held, paths)
            Path(held["receipt_output"]).write_text(json.dumps({"status": "VERIFIED"}))
            cert["bindings"]["independent_cloud_receipt"]["sha256"] = file_digest(Path(held["receipt_output"]))
            Path(held["certificate_output"]).write_text(json.dumps(cert))
        self.policy(active=False)
        calls = []
        with patch.dict(sys.modules, self.modules), patch.object(adapter, "_verify_one", side_effect=lambda *args: calls.append(args)):
            result = adapter.reconcile_checkpoint(self.start, self.queue, pipeline=self.pipeline)
        self.assertEqual(calls, [])
        self.assertEqual(result["accepted"], ["Run-194", "Run-195"])
        self.assertEqual(result["canonical_certificates"], [])
        self.assertFalse(any(Path(entry["certificate_output"]).exists() for entry in self.entries))
