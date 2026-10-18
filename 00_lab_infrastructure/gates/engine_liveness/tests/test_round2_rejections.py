"""Round-2 regressions use deployed rejection envelopes and the real client."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import test_audit_adapter as audit
import test_checkpoint_advisory as advisory_fixture
import checkpoint_advisory as advisory
import checkpoint_certification_lane as adapter
from scheduler_liveness import LivenessHold, SchedulerLane, file_digest, validate_terminal_rejection

HERE = Path(__file__).resolve().parents[1]
REPO = Path(os.environ.get("VIRIDIS_LIVENESS_REPO_ROOT", str(HERE.parents[2])))
sys.path.insert(1, str(REPO / "comparator-deploy"))
import comparator_cloud_lean_verifier as real_client


class DeployedRejectionTests(unittest.TestCase):
    setUp = audit.AuditAdapterTests.setUp
    entry = audit.AuditAdapterTests.entry
    verifier = audit.AuditAdapterTests.verifier
    write_queue = audit.AuditAdapterTests.write_queue
    drain = audit.AuditAdapterTests.drain
    next_checkpoint = audit.AuditAdapterTests.next_checkpoint

    def real_entry(self, number):
        value = self.entry(number)
        statement = Path(value["formal_statement"]["path"])
        candidate = Path(value["candidate"]["path"])
        statement.write_text("theorem target : True := by\n  sorry\n\ntheorem witness : True := by\n  sorry\n")
        candidate.write_text("theorem target : True := by\n  exact bogus\n\ntheorem witness : True := by\n  trivial\n")
        request = Path(value["request"]["path"])
        data = json.loads(request.read_text())
        data.update(statement_contract_sha256=file_digest(statement), expected_theorem_names=["target"],
                    nonvacuity_obligations=["witness"], input_sha256={
                        statement.name: file_digest(statement), candidate.name: file_digest(candidate)})
        request.write_text(json.dumps(data))
        for name in ("request", "formal_statement", "candidate"):
            value[name]["sha256"] = file_digest(Path(value[name]["path"]))
        return value

    def fixture(self, attempt):
        manifest = json.loads((HERE / "tests/fixtures/run191-rejections-provenance.json").read_text())
        row = manifest["rows"][attempt - 1]
        path = HERE / "tests/fixtures" / row["fixture_filename"]
        self.assertEqual(file_digest(path), row["fixture_sha256"])
        response = json.loads(path.read_text())
        self.assertEqual(set(response["executionEvidence"]), {"delivery"})
        return response

    def verify_fixture(self, identity, entry, paths, response, sent):
        key = self.pipeline / "dummy-transport-key"
        key.write_text("inert fixture key")
        def transport(payload, host, key, timeout):
            sent.append(identity.run_id)
            return 2, deepcopy(response)
        cloud = real_client.verify(request_path=paths["request"], formal_statement_path=paths["formal_statement"],
            candidate_path=paths["candidate"], output_path=Path(entry["receipt_output"]),
            key=key, transport=transport)
        if not hasattr(self, "observed_clouds"):
            self.observed_clouds = []
        self.observed_clouds.append(cloud)
        return cloud, {}

    def test_B2_all_three_real_failure_envelopes_free_slots_through_real_client(self):
        self.next_checkpoint([self.real_entry(194), self.real_entry(195)], "real-failures")
        sent = []
        responses = [self.fixture(1), self.fixture(2)]
        def reject(identity, entry, paths):
            return self.verify_fixture(identity, entry, paths, responses[len(sent)], sent)
        self.drain(reject)
        self.assertEqual(sent, ["Run-194", "Run-195"])
        terminal = self.pipeline / "parallel_certification/terminal"
        self.assertEqual(len(list(terminal.glob("*.json"))), 2)
        self.next_checkpoint(self.entries + [self.real_entry(196)], "third-real-failure")
        sent.clear()
        third_response = self.fixture(3)
        self.drain(lambda i, e, p: self.verify_fixture(i, e, p, third_response, sent))
        self.assertEqual(sent, ["Run-196"])
        self.assertEqual(len(list(terminal.glob("*.json"))), 3)
        self.assertEqual([cloud["status"] for cloud in self.observed_clouds], ["HOLD"] * 3)
        self.assertEqual([cloud["runtime_observation_assessment"]["status"] for cloud in self.observed_clouds],
                         ["INVALID_OBSERVATION"] * 3)
        head = advisory.fifo_head(self.pipeline.parent.resolve(), json.loads(self.start.read_text()),
                                 as_of=datetime.now(timezone.utc) + timedelta(hours=25))
        self.assertEqual(head["status"], "ALERT")
        self.assertNotEqual(head["failing_goal"], "UNAVAILABLE")
        self.assertNotEqual(head["provider_receipt"], "UNAVAILABLE")
        successor = deepcopy(self.entries[0])
        request = Path(successor["request"]["path"]).with_name("request_reviewed_r2.json")
        value = json.loads(Path(successor["request"]["path"]).read_text())
        value["revision"] = "reviewed_r2"
        request.write_text(json.dumps(value))
        successor["request"] = {"path": str(request), "sha256": file_digest(request)}
        successor["receipt_output"] += ".reviewed_r2"
        successor["certificate_output"] += ".reviewed_r2"
        self.next_checkpoint([successor, self.entries[1], self.entries[2]], "reviewed-successor")
        sent.clear()
        def accept(identity, entry, paths):
            sent.append(identity.request_sha256)
            return self.verifier(identity, entry, paths)
        self.drain(accept)
        self.assertEqual(sent, [successor["request"]["sha256"]])

    def real_rejection(self):
        entry = self.real_entry(194)
        identity, paths = adapter.identity_for(entry, self.pipeline)
        sent = []
        cloud, _ = self.verify_fixture(identity, entry, paths, self.fixture(1), sent)
        self.assertEqual(sent, ["Run-194"])
        return entry, identity, cloud

    def test_B2_every_deployed_authentication_field_and_response_hash_is_required(self):
        entry, identity, original = self.real_rejection()
        receipt = Path(entry["receipt_output"])
        changes = {
            "served_request": lambda r: r["executionEvidence"]["delivery"].update(servedForRequestId="different"),
            "fresh_delivery": lambda r: r["executionEvidence"]["delivery"].update(mode="CACHE_HIT"),
            "request_id": lambda r: r.update(requestId=""),
            "terminal_standard": lambda r: r["terminationDiagnostics"].update(standard="different"),
            "capture": lambda r: r["terminationDiagnostics"].update(capture_status="UNAVAILABLE"),
            "terminal_request": lambda r: r["terminationDiagnostics"].update(requestId="different"),
            "row_request": lambda r: r["terminationDiagnostics"]["records"][0].update(requestId="different"),
            "nonzero_exit": lambda r: r["terminationDiagnostics"]["records"][0].update(exitCode=0),
            "literal_exit_code": lambda r: r["terminationDiagnostics"]["records"][0].update(exitCode=True),
            "phase": lambda r: r["terminationDiagnostics"]["records"][0].update(phase="unknown"),
            "reason": lambda r: r["terminationDiagnostics"]["records"][0].update(reason="timed-out"),
            "signal": lambda r: r["terminationDiagnostics"]["records"][0].update(signal="SIGKILL"),
            "guard": lambda r: r["terminationDiagnostics"]["records"][0].update(guard_fired=True),
        }
        for label, mutate in changes.items():
            cloud = deepcopy(original)
            mutate(cloud["provider_response"])
            cloud["provider_response_sha256"] = hashlib.sha256((json.dumps(cloud["provider_response"], sort_keys=True,
                separators=(",", ":")) + "\n").encode()).hexdigest()
            receipt.write_text(json.dumps(cloud))
            with self.subTest(field=label), self.assertRaises(LivenessHold):
                validate_terminal_rejection(identity, receipt, file_digest(receipt))
        cloud = deepcopy(original); cloud["provider_response_sha256"] = "0" * 64
        receipt.write_text(json.dumps(cloud))
        with self.assertRaisesRegex(LivenessHold, "RESPONSE_HASH"):
            validate_terminal_rejection(identity, receipt, file_digest(receipt))

    def test_B2_terminal_read_reauthenticates_provider_after_attacker_rehashes_receipt(self):
        entry, identity, cloud = self.real_rejection()
        receipt = Path(entry['receipt_output'])
        lane = SchedulerLane(self.pipeline / 'parallel_certification')
        with lane.checkpoint():
            lane.reserve(identity)
            lane.record_rejection(identity, receipt, file_digest(receipt), cloud['provider_response']['output'])
        cloud['status'] = 'VERIFIED'
        receipt.write_text(json.dumps(cloud))
        row_path = lane.root / 'terminal' / (identity.key + '.json')
        row = json.loads(row_path.read_text())
        row['provider_receipt_sha256'] = file_digest(receipt)
        row_path.write_text(json.dumps(row))
        with self.assertRaisesRegex(LivenessHold, 'REJECTION_PROVIDER'):
            lane._rows('terminal')

    def test_B2_large_failure_output_records_bounded_excerpt_and_full_output_hash(self):
        self.next_checkpoint([self.real_entry(194), self.real_entry(195)], "long-output")
        response = self.fixture(1)
        response["output"] = "first failing goal\n" + "x" * 40000
        sent = []
        self.drain(lambda i, e, p: self.verify_fixture(i, e, p, response, sent))
        self.assertEqual(sent, ["Run-194", "Run-195"])
        for path in (self.pipeline / "parallel_certification/terminal").glob("*.json"):
            row = json.loads(path.read_text())
            self.assertEqual(len(row["failing_goal"]), 32768)
            self.assertEqual(row["provider_output_sha256"], hashlib.sha256(response["output"].encode()).hexdigest())
        with SchedulerLane(self.pipeline / "parallel_certification").checkpoint() as lane:
            self.assertEqual(len(lane._rows("terminal")), 2)
        row = json.loads(path.read_text()); row["provider_output_sha256"] = "0" * 64; path.write_text(json.dumps(row))
        with self.assertRaisesRegex(LivenessHold, "OUTPUT_BINDING"):
            SchedulerLane(self.pipeline / "parallel_certification")._rows("terminal")

    def test_B2_younger_nonterminal_premise_failure_is_per_run_hold(self):
        self.next_checkpoint(self.entries + [self.entry(196)], "per-run-hold")
        checker = self.pipeline / "verification_coverage_gates/premise_declaration.py"
        checker.write_text('def validate_envelope(request,*a,**k):\n return {"status":"HOLD"} if "Run-196" in str(request) else {"status":"PASS","historical_exemption":False}\n')
        sent = []
        def send(identity, entry, paths):
            sent.append(identity.run_id)
            return self.verifier(identity, entry, paths)
        try:
            result = self.drain(send)
        except LivenessHold as exc:
            self.fail("A younger per-run premise HOLD aborted passing FIFO work: " + str(exc))
        self.assertEqual(sent, ["Run-194", "Run-195"])
        self.assertEqual(result["accepted"], sent)
        self.assertEqual(result["holds"][0]["run_id"], "Run-196")
        self.assertEqual(result["holds"][0]["code"], "HOLD_QUEUE_PREMISE_PREFLIGHT")
        self.assertEqual(len(list((self.pipeline / "parallel_certification/preflight-holds").glob("*.json"))), 1)

    def test_authenticated_provider_rejection_remains_a_certificate_visibility_gap(self):
        from liveness_fixtures import write_rejection
        sent=[]
        def verify(identity,entry,paths):
            sent.append(identity.run_id)
            if identity.run_id=='Run-194':
                return write_rejection(identity,entry),{}
            return self.verifier(identity,entry,paths)
        result=self.drain(verify)
        self.assertEqual(sent,['Run-194','Run-195'])
        self.assertEqual(result['accepted'],['Run-195'])
        self.assertEqual(result['canonical_certificates'],[])
        self.assertFalse(Path(self.entries[1]['certificate_output']).exists())
        self.assertEqual(result['holds'][0]['code'],'HOLD_TERMINAL_REJECTED_REQUEST')

    def test_B2_reserved_request_keeps_original_outputs_on_later_queue_path_drift(self):
        self.drain(lambda *args: (_ for _ in ()).throw(TimeoutError()))
        changed = deepcopy(self.entries)
        for entry in changed:
            entry["receipt_output"] += ".later"
            entry["certificate_output"] += ".later"
        self.next_checkpoint(changed, "later-paths")
        sent = []
        result = self.drain(lambda *args: sent.append(args))
        self.assertEqual(sent, [])
        self.assertEqual(len(result["holds"]), 2)
        self.assertFalse(any(Path(entry["receipt_output"]).exists() for entry in changed))

    def test_B2_rollback_reconciles_finished_original_start_without_any_new_send(self):
        self.drain(lambda *args: (_ for _ in ()).throw(TimeoutError()))
        (self.start.parent / "FINISH.json").write_text('{"status":"finished"}')
        calls = []
        with patch.dict(sys.modules, self.modules), patch.object(adapter, "validate_policy", return_value={}), \
             patch.object(adapter, "_verify_one", side_effect=lambda *args: calls.append(args)):
            result = adapter.reconcile_checkpoint(self.start, self.queue, pipeline=self.pipeline)
            with self.assertRaisesRegex(LivenessHold, "CHECKPOINT_IDENTITY"):
                adapter.drain_checkpoint(self.start, self.queue, pipeline=self.pipeline)
        self.assertEqual(calls, [])
        self.assertTrue(result["reconcile_only"])
        self.assertEqual(result["canonical_certificates"], [])


    def test_B2_real_checkpoint_CLI_reconcile_accepts_finished_START_with_inactive_policy(self):
        self.drain(lambda *args: (_ for _ in ()).throw(TimeoutError()))
        value = json.loads(self.start.read_text())
        value.update(standard="VRS-NIGHTLY-CHECKPOINT-1", invocation_id=self.start.parent.name,
                     started_at_utc=datetime.now(timezone.utc).isoformat())
        self.start.write_text(json.dumps(value)); self.write_queue()
        finish = self.start.parent / "FINISH.json"; finish.write_text('{"status":"FINISHED"}')
        before_finish = finish.read_bytes()
        target = self.pipeline / "nightly_checkpoint.py"
        target.write_bytes((HERE / "tests/fixtures/nightly_checkpoint.py.txt").read_bytes())
        applied = subprocess.run(["git","apply","--unidiff-zero",str(HERE/"G2_EXISTING_CHECKPOINT.patch")],
                                 cwd=self.pipeline.parent,capture_output=True,timeout=10)
        self.assertEqual(applied.returncode,0,applied.stderr)
        for name in ("scheduler_liveness.py","checkpoint_certification_lane.py","job_observation_policy.py","checkpoint_advisory.py"):
            (self.pipeline/name).write_bytes((HERE/name).read_bytes())
        (self.pipeline/'autonomous_pipeline_controller.py').write_text('def build_state(): return {}\n')
        (self.pipeline/'science_foundry_continuity.py').write_text('def evaluate(): return {}\n')
        (self.pipeline/'comparator_cloud_lean_verifier.py').write_text('raise AssertionError("reconcile imported transport")\n')
        audit.PolicyGuardTests.policy(self,active=False)
        result = subprocess.run([sys.executable,"-B",str(target),"--reconcile-certification",str(self.start),
                                 "--certification-queue",str(self.queue)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        self.assertNotIn('Traceback',result.stderr)
        self.assertNotIn('HOLD_CHECKPOINT_IDENTITY',result.stdout)
        value=json.loads(result.stdout)
        self.assertTrue(value['reconcile_only'])
        self.assertEqual(value['canonical_certificates'],[])
        self.assertEqual(finish.read_bytes(),before_finish)
        self.assertFalse(any(Path(entry['certificate_output']).exists() for entry in self.entries))


class AdvisoryHistoryTests(unittest.TestCase):
    setUp = advisory_fixture.AdvisoryCheckpointTests.setUp

    def test_SLO_refreshes_after_201_reservations_and_21_hold_files(self):
        requests = self.pipeline / "parallel_certification/requests"
        requests.mkdir(parents=True)
        for number in range(201):
            (requests / f"{number:064x}.json").write_text("{}")
        folder = self.pipeline / "lean_certificates/Run-194"
        for number in range(21):
            (folder / f"PREMISE_DECLARATION_HOLD_{number}.json").write_text("{}")
        status = self.pipeline / "PIPELINE_SLO_STATUS.json"
        status.write_text('{"stale":"previous-checkpoint"}')
        try:
            with patch.object(advisory, "PLAYBOOK_SHA256", file_digest(self.playbook)):
                advisory.observe(self.root, self.checkpoint)
        except Exception as exc:
            self.fail("Bounded history prevented the SLO refresh: " + type(exc).__name__)
        value = json.loads(status.read_text())
        self.assertNotIn("stale", value)
        self.assertEqual(value["checkpoint_sha256"], file_digest(self.checkpoint))
        self.assertEqual(value["fifo_liveness"]["reservation_evidence_budget"], "LIMITED_TO_200")
        self.assertEqual(value["fifo_liveness"]["hold_evidence_budget"], "LIMITED_TO_20")
        self.assertEqual(value["fifo_liveness"]["held_since_utc"], "UNAVAILABLE")
