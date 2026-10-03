import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / 'comparator-deploy'
SNAPSHOT = DEPLOY / 'deployed_snapshots/F2h-20261003'
REMOTE = DEPLOY / 'remote_service'

def load_client():
    sys.path.insert(0,str(DEPLOY))
    spec = importlib.util.spec_from_file_location('profile_client', DEPLOY/'comparator_cloud_lean_verifier.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class FoundationalProfileTests(unittest.TestCase):
    def test_server_selection_boundaries_and_async_isolation(self):
        program = """
import assert from 'node:assert/strict';
import {selectResourceProfile,withResourceProfile,currentResourceProfile,DEFAULT_PROFILE,FOUNDATION_PROFILE,resolveObservedPolicy,PROJECT_POLICY} from './comparator-deploy/remote_service/resource-profile.mjs';
for (const runId of ['Run-001','Run-185','Run-899','Run-900','Run-999']) {
 assert.equal(selectResourceProfile({runId,resourceProfile:'foundational',timeout:1200}),DEFAULT_PROFILE);
}
assert.equal(selectResourceProfile({resourceProfile:'unbounded'}),DEFAULT_PROFILE);
assert.equal(resolveObservedPolicy(PROJECT_POLICY.project,PROJECT_POLICY),FOUNDATION_PROFILE);
for (const field of ['project_manifest_sha256','toolchain_file_sha256','challenge_sha256','solution_sha256','theorem_names']) {
 assert.equal(resolveObservedPolicy(PROJECT_POLICY.project,{...PROJECT_POLICY,[field]:null}),DEFAULT_PROFILE);
}
await Promise.all([
 withResourceProfile({runId:'Run-900',resourceProfile:'foundational'},async()=>{
  await new Promise(r=>setTimeout(r,5));assert.equal(currentResourceProfile(),DEFAULT_PROFILE);
 },'fixture-foundation-forgery'),
 withResourceProfile({runId:'Run-185',resourceProfile:'nightly'},async()=>{
  await new Promise(r=>setTimeout(r,1));assert.equal(currentResourceProfile(),DEFAULT_PROFILE);
 },'fixture-nightly')
]);
assert.equal(currentResourceProfile(),DEFAULT_PROFILE);
"""
        subprocess.run(['node','--input-type=module','-e',program],cwd=ROOT,check=True,capture_output=True)

    def test_client_verify_acceptance_function_byte_identical(self):
        before=(ROOT/'00_lab_infrastructure/gates/fixtures/comparator_client_f2d.py').read_text()
        after=(DEPLOY/'comparator_cloud_lean_verifier.py').read_text()
        def body(text):
            node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='verify')
            return ast.get_source_segment(text,node)
        self.assertEqual(body(before),body(after))

    def test_nightly_launcher_and_service_config_bytes_unchanged(self):
        for name in ['comparator.sh','compile.sh','collectThms.sh']:
            self.assertEqual((SNAPSHOT/name).read_bytes(),(REMOTE/name).read_bytes())
        self.assertIn('ulimit -t 600',(REMOTE/'comparator.sh').read_text())
        source=(REMOTE/'exec.ts').read_text()
        self.assertIn('context: currentExecutionContext()',source)
        policy=(REMOTE/'resource-profile.mjs').read_text()
        self.assertIn('comparator_wall_ms: 285000',policy)
        self.assertIn('compile_wall_ms: 285000, collection_wall_ms: 285000',policy)

    def test_frozen_request_routing_only_reserved_run_ids(self):
        client=load_client()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'request.json'
            for value,expected in [('Run-900','foundational'),('Run-999','foundational'),('Run-185','nightly'),('Run-899','nightly'),('Run-900-MethodsNote','foundational')]:
                p.write_text(json.dumps({'source_run':value}))
                self.assertEqual(client._resource_request(p)['resourceProfile'],expected)
            for value in [None,'Run-1000','Run-900x',900]:
                p.write_text(json.dumps({'source_run':value}))
                self.assertEqual(client._resource_request(p),{})

    def test_server_schema_blocks_nightly_foundational_request(self):
        source=(REMOTE/'shared.ts').read_text()
        self.assertIn('request.resourceProfile === "foundational"',source)
        self.assertIn('!/^Run-9\\d{2}$/.test(request.runId ?? "")',source)

    def test_core_worker_acceptance_body_byte_identical(self):
        old=(SNAPSHOT/'worker.ts').read_text();new=(REMOTE/'worker.ts').read_text()
        def body(s):return s[s.index('async function doUncachedWork('):s.index('\nexport async function doWork(',s.index('async function doUncachedWork('))] if '\nexport async function doWork(' in s else ''
        # Imported core unchanged; only its enclosing resource/diagnostic wrapper may vary.
        old=old[old.index('async function doUncachedWork('):old.index('\nexport async function doWork(')]
        new=new[new.index('async function doUncachedWork('):new.index('\nasync function doWorkInternal(')]
        self.assertEqual(old,new)

if __name__=='__main__':unittest.main()
