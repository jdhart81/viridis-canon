import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
REMOTE=ROOT/'comparator-deploy/remote_service'
SNAP=ROOT/'comparator-deploy/deployed_snapshots/F2h-20261003'

class SubprocessDiagnosticsTests(unittest.TestCase):
    def test_real_spawn_bodies_have_identical_verdicts_with_fake_children(self):
        # Execute the launcher used by the current spawnPromise, not a reconstructed body.
        source=(REMOTE/'exec.ts').read_text()
        self.assertIn('return runGuarded(command, args,',source)
        self.assertIn('throw new CheckingError(err.message, err.output)',source)
        result=subprocess.run(['node','--test',str(ROOT/'comparator-deploy/service-profile/tests/resource-termination.test.mjs')],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_diagnostics_appear_in_success_and_failure_provider_receipts(self):
        shared=(REMOTE/'shared.ts').read_text()
        self.assertEqual(shared.count('processDiagnostics: z.optional(z.record'),2)
        worker=(REMOTE/'worker.ts').read_text()
        self.assertIn('const result = await doWorkInternal(taskId, request);',worker)
        self.assertIn('processDiagnostics: processDiagnostics()',worker)
        self.assertEqual(shared.count('terminationDiagnostics: z.optional(z.record'),2)
        self.assertIn('withTerminationDiagnostics<VerifyResult>(result, currentExecutionContext())',worker)
        app=(REMOTE/'app.ts').read_text()
        self.assertIn('Queue failed outside subprocess result path',app)

if __name__=='__main__':unittest.main()
