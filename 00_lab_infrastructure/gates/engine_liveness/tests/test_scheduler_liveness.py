from dataclasses import asdict, replace
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scheduler_liveness import (LivenessHold, RequestIdentity, SchedulerLane,
                               oldest_target_credit, paper_review_pending, writer_hold_code,
                               scheduler_checkpoint)


def identity(number):
    return RequestIdentity(f"Run-{number:03d}", *[f"{number * 10 + n:064x}" for n in range(5)])


def accepted(request):
    return {"identity": asdict(request), "nanoda_accepted": True,
            "default_kernel_accepted": True, "zero_holes": True,
            "premise_gate": True, "nonvacuity_gate": True,
            "certificate_sha256": f"{int(request.run_id[4:]) * 20:064x}",
            "proof_sha256": f"{int(request.run_id[4:]) * 30:064x}",
            "provider_receipt_sha256": f"{int(request.run_id[4:]) * 40:064x}"}


class LivenessTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "lane"
        self.lane = SchedulerLane(self.root)
        self.old, self.young, self.third = [identity(i) for i in (194, 195, 196)]

    def accept(self, request):
        return self.lane.accept(request, accepted(request), lambda identity, result: True)

    def test_A1_delayed_oldest_younger_accepted_never_publishes_or_earns_oldest_credit(self):
        with self.lane.checkpoint():
            self.lane.eligible_dispatches([(self.old, False), (self.young, False)])
            self.accept(self.young)
            self.assertEqual(self.lane.publication_prefix([self.old, self.young], {self.young.key}), [])
            self.assertEqual(oldest_target_credit([self.old.run_id], {self.young.run_id}), [])

    def test_A2_ambiguous_transport_resume_never_duplicates_dispatch(self):
        with self.lane.checkpoint():
            self.assertTrue(self.lane.reserve(self.old)["dispatch"])
        before = (self.root / "requests" / (self.old.key + ".json")).read_bytes()
        with SchedulerLane(self.root).checkpoint() as resumed:
            self.assertFalse(resumed.reserve(self.old)["dispatch"])
        self.assertEqual(before, (self.root / "requests" / (self.old.key + ".json")).read_bytes())

    def test_A3_single_scheduler_ownership_spans_checkpoint_resume(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            with self.assertRaisesRegex(LivenessHold, "CONCURRENT_SCHEDULER"):
                with SchedulerLane(self.root).checkpoint():
                    self.fail("a second scheduler acquired ownership")
        with SchedulerLane(self.root).checkpoint() as resumed:
            self.assertFalse(resumed.reserve(self.old)["dispatch"])

    def test_A4_candidate_statement_drift_refuses_receipt_reuse(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            for field in ("candidate_sha256", "statement_sha256", "toolchain_sha256", "mathlib_sha256"):
                drifted = replace(self.old, **{field: "a" * 64})
                with self.subTest(field=field), self.assertRaisesRegex(LivenessHold, "BINDING_DRIFT"):
                    self.lane.reserve(drifted)
                value = accepted(self.old)
                value["identity"][field] = "a" * 64
                with self.assertRaisesRegex(LivenessHold, "RESULT_BINDING_DRIFT"):
                    self.lane.accept(self.old, value, lambda *_: True)

    def test_A5_younger_acceptances_retain_separate_certificate_and_proof_bindings(self):
        with self.lane.checkpoint():
            for request in (self.old, self.young):
                self.lane.reserve(request)
                self.accept(request)
            rows = self.lane._rows("results")
            self.assertEqual({row["identity"]["run_id"] for row in rows}, {"Run-194", "Run-195"})
            self.assertEqual(len({row["certificate_sha256"] for row in rows}), 2)
            self.assertEqual(len({row["proof_sha256"] for row in rows}), 2)
            with self.assertRaisesRegex(LivenessHold, "COLLISION"):
                changed = accepted(self.young)
                changed["proof_sha256"] = "a" * 64
                self.lane.accept(self.young, changed, lambda *_: True)

    def test_A6_due_generation_is_independent_of_held_or_full_lane(self):
        generated = []
        with self.lane.checkpoint():
            self.lane.eligible_dispatches([(self.old, True), (self.young, False), (self.third, False)])
            report = scheduler_checkpoint(generation_due=True,
                generation_step=lambda: generated.append("one-due-window"),
                certification_step=lambda: self.lane.reserve(identity(197)))
            self.assertEqual(report["certification"], {"status": "HOLD", "code": "HOLD_TWO_REQUEST_LIMIT"})
            scheduler_checkpoint(generation_due=False,
                generation_step=lambda: self.fail("duplicate generation"),
                certification_step=lambda: self.lane.reserve(identity(197)))
        self.assertEqual(generated, ["one-due-window"])

    def test_A7_restored_oldest_drains_only_contiguous_admitted_prefix(self):
        with self.lane.checkpoint():
            for request in (self.old, self.young, self.third):
                self.lane.reserve(request)
                self.accept(request)
            admitted = {self.old.key, self.young.key}
            self.assertEqual(self.lane.publication_prefix([self.old, self.young, self.third], admitted),
                             ["Run-194", "Run-195"])
            self.assertEqual(self.lane.publication_prefix([self.old, self.young, self.third], {self.old.key, self.third.key}),
                             ["Run-194"])

    def test_terminal_hold_skips_dispatch_but_still_blocks_release_order(self):
        with self.lane.checkpoint():
            reservations = self.lane.eligible_dispatches([(self.old, True), (self.young, False)])
            self.assertEqual([row["request"]["identity"]["run_id"] for row in reservations], ["Run-195"])
            self.accept(self.young)
            self.assertEqual(self.lane.publication_prefix([self.old, self.young], {self.young.key}), [])

    def test_owner_and_lock_are_required(self):
        with self.assertRaisesRegex(LivenessHold, "SCHEDULER_OWNER"):
            SchedulerLane(self.root, "another-scheduler")
        with self.assertRaisesRegex(LivenessHold, "LOCK_REQUIRED"):
            self.lane.reserve(self.old)

    def test_science_and_issuer_gates_remain_mandatory(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            for flag in ("nanoda_accepted", "default_kernel_accepted", "zero_holes", "premise_gate", "nonvacuity_gate"):
                value = accepted(self.old)
                value[flag] = False
                with self.subTest(flag=flag), self.assertRaisesRegex(LivenessHold, "SCIENCE_GATE"):
                    self.lane.accept(self.old, value, lambda *_: True)
            with self.assertRaisesRegex(LivenessHold, "ISSUER_CERTIFICATE"):
                self.lane.accept(self.old, accepted(self.old), lambda *_: False)

    def test_rejection_frees_capacity_without_authorizing_retry(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            self.lane.reserve(self.young)
            self.lane.record_rejection(self.old, "b" * 64, "exact failing goal")
            self.assertTrue(self.lane.reserve(self.third)["dispatch"])
            self.assertFalse(self.lane.reserve(self.old)["dispatch"])
            with self.assertRaisesRegex(LivenessHold, "REJECTED_REQUEST"):
                self.accept(self.old)

    def test_request_identity_cannot_be_reused_for_another_run(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            with self.assertRaisesRegex(LivenessHold, "REQUEST_DIGEST_REUSED"):
                self.lane.reserve(replace(self.old, run_id="Run-195"))

    def test_result_symlink_is_rejected(self):
        with self.lane.checkpoint():
            self.lane.reserve(self.old)
            (self.root / "results").mkdir()
            (self.root / "results" / (self.old.key + ".json")).symlink_to(self.root / "OWNER.lock")
            with self.assertRaisesRegex(LivenessHold, "SYMLINK"):
                self.accept(self.old)

    def test_writer_stdout_hold_code_survives_empty_stderr_without_copying_prose(self):
        self.assertEqual(writer_hold_code(json.dumps({"status": "HOLD", "error":
            "HOLD_REVIEW_STATUS_CONTRADICTION: credential-like prose is excluded"})),
                         "HOLD_REVIEW_STATUS_CONTRADICTION")
        for value in ("not JSON", "[]", '{"status":"HOLD","error":"unbounded prose"}'):
            self.assertEqual(writer_hold_code(value), "UNAVAILABLE")

    def test_finalized_pending_manuscript_routes_to_review_without_rewriting_bytes(self):
        root = Path(self.temporary.name) / "finalized"
        root.mkdir()
        (root / "PAPER_PACKAGE_MANIFEST.json").write_text(json.dumps({"artifacts": {"paper_source": "paper.tex"}}))
        paper = root / "paper.tex"
        paper.write_text("Independent manuscript review remains pending.")
        before = paper.read_bytes()
        self.assertTrue(paper_review_pending(root))
        self.assertEqual(before, paper.read_bytes())
        paper.write_text("External peer review remains pending.")
        self.assertFalse(paper_review_pending(root))

    def test_paper_source_escape_and_symlink_refused(self):
        root = Path(self.temporary.name) / "finalized"
        root.mkdir()
        manifest = root / "PAPER_PACKAGE_MANIFEST.json"
        manifest.write_text(json.dumps({"artifacts": {"paper_source": "../outside.tex"}}))
        with self.assertRaisesRegex(LivenessHold, "ESCAPE"):
            paper_review_pending(root)
        manifest.write_text(json.dumps({"artifacts": {"paper_source": "paper.tex"}}))
        (root / "paper.tex").symlink_to(root / "absent.tex")
        with self.assertRaisesRegex(LivenessHold, "SYMLINK"):
            paper_review_pending(root)


if __name__ == "__main__":
    unittest.main()
