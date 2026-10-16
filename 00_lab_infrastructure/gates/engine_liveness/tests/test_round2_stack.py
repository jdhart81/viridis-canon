"""Compose exact PR109 first, then exercise PR108's controller and installer."""
from copy import deepcopy
import importlib.util
import ast
import py_compile
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import checkpoint_certification_lane as adapter
import install_integration as installer
from scheduler_liveness import LivenessHold, file_digest, certification_action, SchedulerLane
import test_audit_adapter as audit

HERE = Path(__file__).resolve().parents[1]
REPO = Path(os.environ.get("VIRIDIS_LIVENESS_REPO_ROOT", str(HERE.parents[2])))
GATES = REPO / "00_lab_infrastructure/gates"
sys.path.insert(0, str(GATES / "terminal_certification/tests"))
import test_terminal_hold as predecessor
from terminal_certification import terminal_hold as shared


class ComposedControllerTests(predecessor.TerminalFixture):
    load_patched_sources = predecessor.ActualSelectionTests.load_patched_sources

    def composed(self):
        before, continuity = self.load_patched_sources()
        shutil.copyfile(HERE / "tests/fixtures/autonomous_transition_executor.py.txt",
                        self.pipeline / "autonomous_transition_executor.py")
        self.assertEqual(file_digest(self.pipeline / "autonomous_pipeline_controller.py"),
            "86f1691fec4195fe3f0c499df47a934373d6fb55d616cfc7841479511d97fd22")
        result = subprocess.run(["git", "apply", "--unidiff-zero", str(HERE / "G1_CONTROLLER_EXECUTOR.patch")],
                                cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        spec = importlib.util.spec_from_file_location("composed_controller", self.pipeline / "autonomous_pipeline_controller.py")
        controller = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {spec.name: controller}):
            spec.loader.exec_module(controller)
        controller.certificate_clean = lambda *_: False
        return before, controller, continuity

    def test_stack_retains_terminal_rule_and_routes_active_S8_only_to_existing_lane(self):
        before, after, _ = self.composed()
        younger = self.package.with_name("Run-195"); younger.mkdir()
        for controller in (before, after):
            self.assertEqual(controller.inspect_open_run(self.package, self.folder.parent, True).state,
                             "TERMINAL_PREMISE_HOLD")
        self.assertEqual(before.inspect_open_run(younger, self.folder.parent, True).next_action, "CERTIFY_COMPARATOR_FIFO")
        (self.pipeline / "PARALLEL_CERTIFICATION_POLICY.json").write_text('{"active":true}')
        self.assertEqual(after.inspect_open_run(younger, self.folder.parent, True).next_action,
                         "DRAIN_SCHEDULER_CERTIFICATION_LANE")
        self.assertEqual(after.inspect_run(younger, self.folder.parent, set(), set(), self.root, True, self.root).next_action,
                         "DRAIN_SCHEDULER_CERTIFICATION_LANE")
        self.assertEqual(after.inspect_open_run(self.package, self.folder.parent, True).state, "TERMINAL_PREMISE_HOLD")
        self.receipt_path.write_text('{"invalid":"wrong hash"}')
        self.assertEqual(after.inspect_open_run(self.package, self.folder.parent, True).next_action,
                         "DRAIN_SCHEDULER_CERTIFICATION_LANE")
        self.assertEqual(after.inspect_run(self.package, self.folder.parent, set(), set(), self.root, True, self.root).next_action,
                         "DRAIN_SCHEDULER_CERTIFICATION_LANE")

    def test_stack_preserves_pre_review_route_and_applies_G1_only_after_finalization(self):
        before, after, _ = self.composed()
        run = self.package.with_name("Run-196"); run.mkdir()
        for name in ("CURATOR_DRAFT_READY", "CANON_PRODUCT_ROUTE", "KERNEL_ADMISSION_REVIEW"):
            (run / (name + ".json")).write_text("{}")
        (run / "PAPER_PACKAGE_MANIFEST.json").write_text(json.dumps({"artifacts": {"paper_source": "paper.tex"}}))
        (run / "paper.tex").write_text("Independent paper review remains pending.")
        for controller in (before, after):
            controller.certificate_clean = lambda *_: True
            item = controller.inspect_run(run, self.folder.parent, set(), set(), self.root, True, self.root)
            self.assertEqual(item.next_action, "REVIEW_PRIOR_INVOCATION_DRAFT")
        (run / "FINALIZED_PACKAGE.json").write_text("{}")
        (run / "POST_ARISTOTLE_REVIEW.json").write_text(json.dumps({"schema_version":2,"verdict":"pass",
            "reviewer_system":"fixture","reviewer_model":"fixture","checks":{"ok":True}}))
        item = after.inspect_run(run, self.folder.parent, set(), set(), self.root, True, self.root)
        self.assertEqual(item.next_action, "REVIEW_FINALIZED_PACKAGE_BINDINGS")
        self.assertFalse(item.human_gate)

    def test_stack_lane_uses_the_same_reviewed_terminal_classifier_as_PR109(self):
        # Adapt only the test request's basic transport identity. Scientific
        # documents and recorded pure-checker result remain the #109 fixture.
        self.request.update(toolchain="leanprover/lean4:v4.28.0", mathlib_rev="b"*40)
        self.rebind_document("ENGINE3_VERIFICATION_REQUEST.json", predecessor.encoded(self.request))
        entry = {"run_id":"Run-194", **{name:{"path":str(self.folder/filename),"sha256":file_digest(self.folder/filename)}
            for name,filename in (("request","ENGINE3_VERIFICATION_REQUEST.json"),
                                 ("formal_statement","VERIFICATION_STATEMENT.lean"),
                                 ("candidate","VERIFICATION_CANDIDATE.lean"))},
            "receipt_output":str(self.folder/"fresh-receipt.json"),"certificate_output":str(self.folder/"fresh-certificate.json"),
            "terminal_hold":{"path":str(self.receipt_path),"sha256":file_digest(self.receipt_path)}}
        identity,_=adapter.identity_for(entry,self.pipeline)
        namespace=types.ModuleType("verification_coverage_gates"); namespace.__path__=[]
        child=types.ModuleType("verification_coverage_gates.terminal_certification"); child.__path__=[]
        mods={"verification_coverage_gates":namespace,"verification_coverage_gates.terminal_certification":child,
              "verification_coverage_gates.terminal_certification.terminal_hold":shared}
        with patch.dict(sys.modules,mods):
            self.assertTrue(adapter.terminal_hold(entry,identity,self.pipeline))
            with patch.object(shared,"terminal_hold",return_value=None):
                with self.assertRaisesRegex(LivenessHold,"TERMINAL_HOLD_BINDING"):
                    adapter.terminal_hold(entry,identity,self.pipeline)
            # A successor's different request is never excluded by the original.
            request=Path(entry['request']['path']).with_name('successor.json')
            request.write_text(json.dumps({**self.request,"revision":"r2"}))
            successor={**entry,"request":{"path":str(request),"sha256":file_digest(request)}}
            newer,_=adapter.identity_for(successor,self.pipeline)
            with self.assertRaisesRegex(LivenessHold,"TERMINAL_HOLD_BINDING"):
                adapter.terminal_hold(successor,newer,self.pipeline)

    def installer_fixture(self):
        self.load_patched_sources()
        shutil.copyfile(HERE / "tests/fixtures/autonomous_transition_executor.py.txt", self.pipeline / "autonomous_transition_executor.py")
        shutil.copyfile(HERE / "tests/fixtures/nightly_checkpoint.py.txt", self.pipeline / "nightly_checkpoint.py")
        shutil.copyfile(HERE / "job_observation_policy.py", self.pipeline / "job_observation_policy.py")
        target=self.pipeline / "verification_coverage_gates/terminal_certification/terminal_hold.py"
        target.parent.mkdir(parents=True); shutil.copyfile(GATES / "terminal_certification/terminal_hold.py",target)

    def test_installer_real_CLI_refuses_before_hash_mismatch_without_writing_receipt_or_sources(self):
        self.installer_fixture()
        (self.pipeline / "autonomous_pipeline_controller.py").write_text("wrong predecessor\n")
        before={p.name:p.read_bytes() for p in self.pipeline.glob("*.py")}
        receipt=self.root/"never-created"/"INSTALL.json"
        result=subprocess.run([sys.executable,"-B",str(HERE/"install_integration.py"),"--pipeline",str(self.pipeline),
            "--apply","--receipt",str(receipt),"--review-evidence",str(self.root/"absent.json"),
            "--expected-review-evidence-sha256","0"*64],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertEqual(json.loads(result.stdout)["error"],"HOLD_INSTALL_BEFORE_HASH")
        self.assertFalse(receipt.parent.exists())
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.pipeline.glob("*.py")})
        self.assertFalse((self.pipeline/"scheduler_liveness.py").exists())

    def test_installer_real_CLI_plan_verifies_exact_composed_after_hashes(self):
        self.installer_fixture()
        before={p.name:p.read_bytes() for p in self.pipeline.glob("*.py")}
        result=subprocess.run([sys.executable,"-B",str(HERE/"install_integration.py"),"--pipeline",str(self.pipeline)],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        value=json.loads(result.stdout)
        self.assertEqual(value["status"],"PLANNED_INACTIVE")
        self.assertFalse(value["policy_activation"])
        binding=json.loads((HERE/"INTEGRATION_BINDING.json").read_text())
        for row in binding["files"]:
            self.assertEqual(value["after_sha256"][Path(row["path"]).name],row["after_sha256"])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.pipeline.glob("*.py")})

    def test_installer_real_CLI_applies_exact_stack_with_rollback_and_leaves_policy_inactive(self):
        self.installer_fixture()
        review=self.root/'REVIEW_FIXTURE.json'
        binding=json.loads((HERE/'INTEGRATION_BINDING.json').read_text())
        review.write_text(json.dumps({'merged_by':'Justin','ci':'PASS','independent_review':'PASS',
                                    'source_sha256':binding['source_files'],'binding_sha256':file_digest(HERE/'INTEGRATION_BINDING.json'),'fixture_only':True}))
        receipt=self.root/'installation-evidence'/'INSTALL.json'
        originals={p.name:p.read_bytes() for p in self.pipeline.glob('*.py')}
        result=subprocess.run([sys.executable,'-B',str(HERE/'install_integration.py'),'--pipeline',str(self.pipeline),
            '--apply','--receipt',str(receipt),'--review-evidence',str(review),
            '--expected-review-evidence-sha256',file_digest(review)],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        value=json.loads(receipt.read_text())
        self.assertEqual(value['status'],'INSTALLED_INACTIVE')
        self.assertEqual(value['readback'],'EXACT')
        for name,digest in value['after_sha256'].items():
            self.assertEqual(file_digest(self.pipeline/name),digest)
        for name,raw in originals.items():
            if name in value['after_sha256']:
                self.assertEqual((receipt.parent/'rollback'/name).read_bytes(),raw)
        self.assertFalse((self.pipeline/'PARALLEL_CERTIFICATION_POLICY.json').exists())

    def test_installer_real_CLI_ignores_timestamp_valid_substituted_bytecode_under_B(self):
        self.installer_fixture()
        terminal=self.pipeline/'verification_coverage_gates/terminal_certification/terminal_hold.py'
        original=terminal.read_bytes(); stamp=terminal.stat()
        marker=self.root/'unchecked-cache-executed.txt'
        alternate=('from pathlib import Path\nPath('+repr(str(marker))+').write_text("unchecked cache")\n'
                   'def terminal_hold(*args): return None\n').encode()
        alternate += b'#'*(len(original)-len(alternate))
        self.assertEqual(len(alternate),len(original))
        terminal.write_bytes(alternate)
        os.utime(terminal,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        py_compile.compile(str(terminal),doraise=True)
        terminal.write_bytes(original)
        os.utime(terminal,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        result=subprocess.run([sys.executable,'-B',str(HERE/'install_integration.py'),'--pipeline',str(self.pipeline)],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'PLANNED_INACTIVE')
        self.assertEqual(terminal.read_bytes(),original)
        self.assertFalse(marker.exists(),'Hash-checked source must be the only code executed; unchecked pycache ran')

    def test_installer_real_CLI_ignores_cached_local_dependency(self):
        self.installer_fixture()
        source=self.root/'installer-source';source.mkdir()
        binding=json.loads((HERE/'INTEGRATION_BINDING.json').read_text())
        for name in (*binding['source_files'],'INTEGRATION_BINDING.json'):
            shutil.copyfile(HERE/name,source/name)
        local=source/'scheduler_liveness.py';original=local.read_bytes();stamp=local.stat()
        marker=self.root/'local-import-cache-executed.txt'
        alternate=('from pathlib import Path\nPath('+repr(str(marker))+').write_text("unchecked local cache")\n').encode()
        alternate += b'#'*(len(original)-len(alternate))
        local.write_bytes(alternate);os.utime(local,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        py_compile.compile(str(local),doraise=True)
        local.write_bytes(original);os.utime(local,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        result=subprocess.run([sys.executable,'-B',str(source/'install_integration.py'),'--pipeline',str(self.pipeline)],
                              capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'],'PLANNED_INACTIVE')
        self.assertFalse(marker.exists(),'Installer executed unchecked local dependency cache')

    def test_installer_rechecks_predecessor_CAS_after_plan_before_any_write(self):
        self.installer_fixture()
        binding=json.loads((HERE/'INTEGRATION_BINDING.json').read_text())
        review=self.root/'CAS_REVIEW_FIXTURE.json'
        review.write_text(json.dumps({'merged_by':'Justin','ci':'PASS','independent_review':'PASS',
            'source_sha256':binding['source_files'],'binding_sha256':file_digest(HERE/'INTEGRATION_BINDING.json')}))
        receipt=self.root/'must-not-exist'/'INSTALL.json'
        original_plan=installer.plan
        def drift(pipeline):
            value,staged=original_plan(pipeline)
            (pipeline/'autonomous_pipeline_controller.py').write_text('changed after plan\n')
            return value,staged
        with patch.object(installer,'plan',side_effect=drift):
            with self.assertRaisesRegex(installer.LivenessHold,'INSTALL_BEFORE_CAS'):
                installer.install(self.pipeline,receipt,review,file_digest(review))
        self.assertFalse(receipt.parent.exists())
        self.assertFalse((self.pipeline/'scheduler_liveness.py').exists())
        self.assertEqual((self.pipeline/'autonomous_pipeline_controller.py').read_text(),'changed after plan\n')

    def terminal_drain_fixture(self):
        self.request.update(toolchain='leanprover/lean4:v4.28.0',mathlib_rev='b'*40)
        self.rebind_document('ENGINE3_VERIFICATION_REQUEST.json',predecessor.encoded(self.request))
        entry={'run_id':'Run-194',**{name:{'path':str(self.folder/filename),'sha256':file_digest(self.folder/filename)}
            for name,filename in (('request','ENGINE3_VERIFICATION_REQUEST.json'),
                                 ('formal_statement','VERIFICATION_STATEMENT.lean'),
                                 ('candidate','VERIFICATION_CANDIDATE.lean'))},
            'receipt_output':str(self.folder/'fresh-receipt.json'),'certificate_output':str(self.folder/'fresh-certificate.json'),
            'terminal_hold':{'path':str(self.receipt_path),'sha256':file_digest(self.receipt_path)}}
        self.entries=[entry,audit.AuditAdapterTests.entry(self,195)]
        checker=self.pipeline/'verification_coverage_gates/premise_declaration.py'
        checker.parent.mkdir(parents=True,exist_ok=True)
        checker.write_text('def validate_envelope(*args,**kwargs):\n return {"status":"PASS","historical_exemption":False}\n')
        self.start=self.pipeline/'nightly_checkpoints/terminal-fixture/START.json'
        self.start.parent.mkdir(parents=True)
        self.start.write_text(json.dumps({'science':{'certification':{'backlog_runs':['Run-194','Run-195']}}}))
        self.queue=self.start.parent/'QUEUE.json';audit.AuditAdapterTests.write_queue(self)
        namespace=types.ModuleType('verification_coverage_gates');namespace.__path__=[]
        child=types.ModuleType('verification_coverage_gates.terminal_certification');child.__path__=[]
        self.mods={'verification_coverage_gates':namespace,'verification_coverage_gates.terminal_certification':child,
            'verification_coverage_gates.terminal_certification.terminal_hold':shared,
            'nightly_checkpoint':types.SimpleNamespace(read_start=lambda path:json.loads(path.read_text())),
            'comparator_data_egress_authorization':types.SimpleNamespace(validate_authorization=lambda *a:{'status':'AUTHORIZED'})}
        return entry

    def terminal_drain(self,sent):
        def verify(identity,entry,paths):
            sent.append(identity.run_id)
            return audit.AuditAdapterTests.verifier(self,identity,entry,paths)
        with patch.dict(sys.modules,self.mods),patch.object(adapter,'validate_policy',return_value={}),\
             patch.object(adapter,'_verify_one',side_effect=verify):
            return adapter.drain_checkpoint(self.start,self.queue,pipeline=self.pipeline)

    def test_shared_authenticated_terminal_allows_only_younger_certificate_visibility_not_credit_or_publication(self):
        self.terminal_drain_fixture();sent=[]
        result=self.terminal_drain(sent)
        self.assertEqual(sent,['Run-195'])
        self.assertEqual(result['accepted'],['Run-195'])
        self.assertEqual(result['canonical_certificates'],['Run-195'])
        self.assertFalse(Path(self.entries[0]['certificate_output']).exists())
        self.assertTrue(Path(self.entries[1]['certificate_output']).exists())
        self.assertEqual(result['holds'][0]['code'],'HOLD_TERMINAL_SEALED_OBJECT')
        self.assertFalse(result['publication_performed'])
        # The actual original checkpoint still holds194's target/debt.
        tree=ast.parse((HERE/'tests/fixtures/nightly_checkpoint.py.txt').read_text())
        assess=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='assess')
        namespace={};exec(compile(ast.Module(body=[assess],type_ignores=[]),'checkpoint.py','exec'),namespace)
        certification={'backlog_runs':['Run-194','Run-195'],'certified_runs':[],'ready':True,'recent':True,'backlog_critical':7}
        start={'science':{'certification':certification},'invocation_id':'fixture','started_at_utc':'2026-10-16T12:00:00Z'}
        current={'certification':{**certification,'backlog_runs':['Run-194'],'certified_runs':['Run-195']},
                 'generation':{'ready':True,'due':False,'fresh':True},'evaluated_at_utc':'2026-10-16T12:01:00Z'}
        finished=namespace['assess'](start,current,{'items':[],'counts':{'submission_ready_packages':0}})
        self.assertEqual(finished['certification']['target_runs'],['Run-194','Run-195'])
        self.assertEqual(finished['certification']['cleared_prior_debt'],['Run-195'])
        self.assertIn('HOLD_FIFO_CERTIFICATION_TARGET_NOT_MET',finished['incidents'])
        identities=[adapter.identity_for(entry,self.pipeline)[0] for entry in self.entries]
        lane=SchedulerLane(self.pipeline/'parallel_certification')
        with lane.checkpoint():
            self.assertEqual(lane.publication_prefix(identities,{identities[1].key}),[])

    def test_terminal_exclusion_is_freshly_reauthenticated_before_certificate_visibility(self):
        self.terminal_drain_fixture();sent=[]
        classify=shared.terminal_hold;calls=[]
        def withdrawn(*args):
            calls.append(args)
            return classify(*args) if len(calls)==1 else None
        with patch.object(shared,'terminal_hold',side_effect=withdrawn):
            with self.assertRaisesRegex(LivenessHold,'TERMINAL_HOLD_BINDING'):
                self.terminal_drain(sent)
        self.assertEqual(sent,['Run-195'])
        self.assertEqual(len(calls),2)
        self.assertFalse(Path(self.entries[1]['certificate_output']).exists())

    def test_malformed_active_policy_retains_single_S8_route_and_false_restores_original(self):
        policy=self.pipeline/'PARALLEL_CERTIFICATION_POLICY.json'
        for raw in ('{"active":true}', '{}', '{malformed'):
            policy.write_text(raw)
            self.assertEqual(certification_action(self.folder.parent),'DRAIN_SCHEDULER_CERTIFICATION_LANE')
        policy.write_text('{"active":false}')
        self.assertEqual(certification_action(self.folder.parent),'CERTIFY_COMPARATOR_FIFO')
