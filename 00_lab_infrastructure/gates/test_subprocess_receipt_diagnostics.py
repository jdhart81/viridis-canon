import json
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
REMOTE=ROOT/'comparator-deploy/remote_service'
SNAP=ROOT/'comparator-deploy/deployed_snapshots/F2h-20261003'

class SubprocessDiagnosticsTests(unittest.TestCase):
    def test_real_spawn_bodies_have_identical_verdicts_with_fake_children(self):
        old=(SNAP/'exec.ts').read_text();new=(REMOTE/'exec.ts').read_text()
        def body(source):
            start=source.index('  const description = options?.description')
            end=source.index('\n}\n\nconst staging',start)
            return source[start:end].replace("const output: string[]", "const output").replace("(str: string)", "(str)")
        program='''
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import {withResourceProfile,processDiagnostics,comparatorWallMilliseconds,beginProcess,markDeadline,closeProcess} from './comparator-deploy/remote_service/resource-profile.mjs';
let time=0;
Object.defineProperty(globalThis,'performance',{value:{now:()=>time},configurable:true});
class CheckingError extends Error {constructor(description,output){super(description);this.output=output;}}
const oldBody=OLD_BODY, newBody=NEW_BODY;
async function invoke(body,kind,run,description='Comparator') {
 const child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();child.pid=42;
 let timer, delay, killed=[];
 const spawn=()=>child;
 const setTimeout=(callback,milliseconds)=>{timer=callback;delay=milliseconds;return 1};
 const clearTimeout=()=>{};
 const process={env:{},kill:(...args)=>killed.push(args)};
 const method=new Function('command','args','options','spawn','CheckingError','setTimeout','clearTimeout','process','comparatorWallMilliseconds','beginProcess','markDeadline','closeProcess','BACKUP_SIGKILL_MS','BUFFER_LIMIT',body);
 return withResourceProfile(run,async()=>{
  const resultPromise=method('fake',[],{description},spawn,CheckingError,setTimeout,clearTimeout,process,comparatorWallMilliseconds,beginProcess,markDeadline,closeProcess,285000,1000000);
  child.stdout.emit('data',Buffer.from('same output'));time+=4200;
  let code=kind==='success'?0:kind==='nonzero'?1:null;
  let signal=kind==='cpu'?'SIGXCPU':kind==='kill'||kind==='deadline'?'SIGKILL':null;
  if(kind==='deadline')timer();
  child.exitCode=code;child.signalCode=signal;
  if(kind==='spawnerror')child.emit('error',new Error('fixture spawn failure'));
  child.emit('close',code,signal);
  let result;
  try{result={ok:true,output:await resultPromise}}catch(error){result={ok:false,message:error.message,output:error.output}}
  return {result,diagnostics:processDiagnostics(),delay,killed};
 });
}
for(const kind of ['success','nonzero','cpu','kill','deadline','spawnerror']) {
 const prior=await invoke(oldBody,kind,{});
 const current=await invoke(newBody,kind,{});
 assert.deepEqual(current.result,prior.result);
 assert.equal(current.delay,285000);
 assert.equal(current.diagnostics.acceptanceEvidence,false);
 assert.equal(current.diagnostics.phaseReached,'compare-kernels');
 assert.equal(current.diagnostics.comparator.elapsedSeconds,4.2);
 assert.equal(current.diagnostics.comparator.complete,true);
 assert.equal(current.diagnostics.comparator.signal,kind==='cpu'?'SIGXCPU':kind==='kill'||kind==='deadline'?'SIGKILL':null);
 assert.equal(current.diagnostics.comparator.exitCode,kind==='success'?0:kind==='nonzero'?1:null);
 assert.equal(current.diagnostics.comparator.deadlineFired,kind==='deadline');
 if(kind==='deadline')assert.deepEqual(current.killed,[[-42,'SIGKILL']]);
}
const foundation={runId:'Run-900',resourceProfile:'foundational'};
assert.equal((await invoke(newBody,'success',foundation)).delay,600000);
assert.equal((await invoke(newBody,'success',foundation,'Compilation of olean for Solution')).delay,285000);
assert.equal((await invoke(newBody,'success',foundation,'Challenge theorem collection')).delay,285000);
await withResourceProfile({},async()=>{
 const diagnostic=processDiagnostics();
 assert.equal(diagnostic.comparator.exitCode,null);assert.equal(diagnostic.comparator.signal,null);
 assert.equal(diagnostic.phaseReached,'not-started');
 const record=beginProcess('Compilation of olean for Challenge',285000);closeProcess(record,0,null);
 assert.equal(processDiagnostics().phaseReached,'compile-Challenge');
 closeProcess(null,1,'SIGKILL');markDeadline(null); // absent storage never changes verdict
});
'''.replace('OLD_BODY',json.dumps(body(old))).replace('NEW_BODY',json.dumps(body(new)))
        result=subprocess.run(['node','--input-type=module','-e',program],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_diagnostics_appear_in_success_and_failure_provider_receipts(self):
        shared=(REMOTE/'shared.ts').read_text()
        self.assertEqual(shared.count('processDiagnostics: z.optional(z.record'),2)
        worker=(REMOTE/'worker.ts').read_text()
        self.assertIn('const result = await doWorkInternal(taskId, request);',worker)
        self.assertIn('processDiagnostics: processDiagnostics()',worker)
        app=(REMOTE/'app.ts').read_text()
        self.assertIn('Queue failed outside subprocess result path',app)

if __name__=='__main__':unittest.main()
