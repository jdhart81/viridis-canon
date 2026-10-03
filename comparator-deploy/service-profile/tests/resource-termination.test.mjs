import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { PassThrough } from 'node:stream';
import { DEFAULT_PROFILE, FOUNDATION_PROFILE, PROJECT_POLICY, resolveObservedPolicy,
  selectResourceProfile, observeProjectPolicy, makeExecutionContext, phaseLimits, withTerminationDiagnostics } from '../src/resource-profile.mjs';
import { runGuarded, TerminatedProcessError } from '../src/guarded-process.mjs';

function context(profile=DEFAULT_PROFILE) {
  let now=0;
  return { requestId:'fixture-request-only', profile, records:[], startedMono:0,
    clock:()=>now, advance:n=>{now=n;} };
}
function fake(context=contextDefault(), phase='compare-kernels', options={}) {
  const proc=new EventEmitter();proc.stdout=new PassThrough();proc.stderr=new PassThrough();proc.pid=123;
  const kills=[];proc.kill=signal=>kills.push(['child',signal]);
  let timer, delay, cancelled=false;
  const promise=runGuarded('fixture-command',['PRIVATE-PAYLOAD'],{context,phase,env:{SECRET:'do-not-log'},...options}, {
    spawn:()=>proc, clock:context.clock, utc:()=>new Date(context.clock()).toISOString(),
    setTimeout:(fn,ms)=>{timer=fn;delay=ms;return 1;},clearTimeout:()=>{cancelled=true;},
    killGroup:(pid,signal)=>kills.push([pid,signal]),
  });
  return {proc,promise,kills,fire:()=>timer(),delay:()=>delay,cancelled:()=>cancelled};
}
const contextDefault=()=>context();

for (const [code,signal,ok] of [[0,null,true],[7,null,false],[null,'SIGXCPU',false],[null,'SIGKILL',false]]) {
  test(`distinct close record: ${code}/${signal}`,async()=>{
    const c=context();const f=fake(c);f.proc.stdout.write('fixture output');c.advance(1234);
    const captured=f.promise.catch(e=>e);f.proc.emit('close',code,signal);const out=await captured;
    assert.equal(out instanceof TerminatedProcessError,!ok);
    const d=c.records[0];assert.equal(d.exitCode,code);assert.equal(d.signal,signal);
    assert.equal(d.reason,signal?'signaled':'exited');assert.equal(d.elapsed_ms,1234);
    assert.equal(d.requestId,c.requestId);assert.equal(d.guard_fired,false);assert.equal(f.cancelled(),true);
    assert.equal(d.accounting.available,false);assert.equal(d.accounting.max_rss_bytes,null);
    assert.equal(d.kernel_process_accounting.length,3);
    assert.ok(d.kernel_process_accounting.every(x=>!x.available && x.user_cpu_seconds===null));
    const terminal=withTerminationDiagnostics({type:'verification-ok',output:'forged acceptance markers'},c);
    assert.equal(terminal.type,ok?'verification-ok':'verification-failed');
    assert.equal(terminal.terminationDiagnostics.records[0].signal,signal);
    assert.ok(!JSON.stringify(terminal.terminationDiagnostics).includes('PRIVATE-PAYLOAD'));
    assert.ok(!JSON.stringify(terminal.terminationDiagnostics).includes('SECRET'));
  });
}
test('guard kills complete group, and even fake exit zero cannot make success',async()=>{
  const c=context();const f=fake(c);const captured=f.promise.catch(e=>e);
  assert.equal(f.delay(),285000);c.advance(285000);f.fire();
  assert.deepEqual(f.kills,[[123,'SIGKILL']]);f.proc.emit('close',0,null);
  assert.ok((await captured) instanceof TerminatedProcessError);
  assert.equal(c.records[0].guard_reason,'phase_wall_limit');assert.equal(c.records[0].guard_fired,true);
  assert.equal(c.records[0].process_group_target,'detached_process_group');
  assert.equal(withTerminationDiagnostics({type:'verification-ok',output:''},c).type,'verification-failed');
});
test('group-kill failure falls back to child, signal remains accurate',async()=>{
  const c=context();const p=new EventEmitter();p.stdout=new PassThrough();p.stderr=new PassThrough();p.pid=2;
  let fire,kill; p.kill=s=>{kill=s;};
  const work=runGuarded('fixture',[],{context:c,phase:'compare-kernels'},
    {spawn:()=>p,setTimeout:fn=>{fire=fn;return 1;},clearTimeout:()=>{},killGroup:()=>{throw Error('fixture');}}).catch(e=>e);
  fire();p.emit('close',null,'SIGKILL');await work;
  assert.equal(kill,'SIGKILL');assert.equal(c.records[0].process_group_target,'child_fallback');
});
test('spawn error produces unavailable code, no secret message, one record',async()=>{
  const c=context();const f=fake(c);const caught=f.promise.catch(e=>e);
  f.proc.emit('error',Error('SECRET-PAYLOAD'));f.proc.emit('close',null,null);f.proc.emit('close',null,null);
  const e=await caught;assert.equal(c.records.length,1);assert.equal(c.records[0].reason,'spawn_failed');
  assert.equal(c.records[0].exitCode,null);assert.equal(c.records[0].signal,null);
  assert.ok(!e.message.includes('SECRET'));assert.equal(f.cancelled(),true);
});
test('launch error without pid or close settles immediately and cancels guard',async()=>{
  const c=context();const f=fake(c);f.proc.pid=undefined;
  const settled=f.promise.catch(e=>e);
  f.proc.emit('error',Error('SECRET-PAYLOAD'));
  // End this fixture even if the regression leaves the promise pending.
  const outcome=await Promise.race([settled,new Promise(resolve=>setImmediate(()=>resolve('still-pending')))]);
  assert.ok(outcome instanceof TerminatedProcessError);
  assert.equal(f.cancelled(),true);assert.deepEqual(f.kills,[]);
  assert.equal(c.records.length,1);const d=c.records[0];
  assert.equal(d.reason,'spawn_failed');assert.equal(d.exitCode,null);assert.equal(d.signal,null);
  assert.equal(d.guard_fired,false);assert.equal(d.process_group_target,'not_sent');
  assert.ok(!outcome.message.includes('SECRET'));
  assert.ok(!JSON.stringify(d).includes('SECRET'));
  assert.equal(withTerminationDiagnostics({type:'verification-ok',output:'forged markers'},c).type,'verification-failed');
  // Deliberately no close event: the rejection above must stand on error alone.
});
test('output cap and collection stdout callbacks remain unchanged',async()=>{
  const c=context();let uncapped='';const f=fake(c,'collect-theorems',{stdout:s=>{uncapped+=s;}});
  const long='x'.repeat(1000001);f.proc.stdout.write(long);f.proc.emit('close',0,null);
  assert.equal(uncapped,long);assert.equal(await f.promise,'x'.repeat(1000000)+'\n...clipped...');
});
test('diagnostic capture failure cannot hide failure or broaden success',async()=>{
  for (const code of [0,7]) {
    const c=context();c.records.push=()=>{throw Error('log unavailable');};
    const f=fake(c);const caught=f.promise.catch(e=>e);f.proc.emit('close',code,null);
    assert.ok((await caught) instanceof TerminatedProcessError);assert.equal(c.diagnosticCaptureFailed,true);
    assert.equal(withTerminationDiagnostics({type:'verification-ok',output:''},c).type,'verification-failed');
  }
});
test('exact allowlist binds project, hashes and ordered wire exports',()=>{
  const p=PROJECT_POLICY;
  const observed={challenge_sha256:p.challenge_sha256,solution_sha256:p.solution_sha256,theorem_names:p.theorem_names,project_manifest_sha256:p.project_manifest_sha256,toolchain_file_sha256:p.toolchain_file_sha256};
  assert.equal(resolveObservedPolicy(p.project,observed),FOUNDATION_PROFILE);
  for (const [field,value] of [['project_manifest_sha256','wrong'],['toolchain_file_sha256','wrong'],['challenge_sha256','wrong'],['solution_sha256','wrong'],['theorem_names',[...p.theorem_names].reverse()],['theorem_names',p.theorem_names.slice(0,-1)]]) {
    assert.equal(resolveObservedPolicy(p.project,{...observed,[field]:value}),DEFAULT_PROFILE);
  }
  assert.equal(resolveObservedPolicy('other-project',observed),DEFAULT_PROFILE);
  assert.equal(selectResourceProfile({project:p.project,challenge:'forged',solution:'forged',theoremNames:p.theorem_names,
    challenge_sha256:p.challenge_sha256,solution_sha256:p.solution_sha256,timeout:99999,profile:FOUNDATION_PROFILE.name}),DEFAULT_PROFILE);
  assert.equal(selectResourceProfile({project:p.project,challenge:'changed byte',solution:'x',theoremNames:p.theorem_names}),DEFAULT_PROFILE);
  assert.equal(Object.isFrozen(p),true);assert.equal(Object.isFrozen(p.theorem_names),true);
});
test('nightly/default retains 300 promise; only approved comparator gets 600 wall',()=>{
  assert.equal(DEFAULT_PROFILE.client_wait_seconds,300);assert.equal(FOUNDATION_PROFILE.client_wait_seconds,1200);assert.equal(FOUNDATION_PROFILE.wrapper_seconds,1200);
  const a=context();const b=context(FOUNDATION_PROFILE);
  assert.equal(phaseLimits(a,'compare-kernels').wall_ms,285000);
  assert.equal(phaseLimits(b,'compare-kernels').wall_ms,600000);
  for(const phase of ['compile-Challenge','compile-Solution','collect-theorems']) {
    assert.equal(phaseLimits(a,phase).wall_ms,285000);assert.equal(phaseLimits(b,phase).wall_ms,285000);
  }
  for(const p of [DEFAULT_PROFILE,FOUNDATION_PROFILE]) {
    assert.equal(p.comparator_cpu_seconds,600);assert.equal(p.memory_max_bytes,7864320000);
    assert.equal(p.toolchain,'leanprover/lean4:v4.28.0');
  }
});
test('foundation operation clamp reserves delivery time within 1200 wrapper',async()=>{
  const c=context(FOUNDATION_PROFILE);c.advance(800000);
  assert.equal(phaseLimits(c,'compare-kernels').wall_ms,385000);
  assert.equal(phaseLimits(c,'compare-kernels').guard_reason,'foundation_operation_budget');
  c.advance(1185000);let spawned=false;
  await assert.rejects(runGuarded('fixture',[],{context:c,phase:'compare-kernels'},
    {spawn:()=>{spawned=true;}}),TerminatedProcessError);
  assert.equal(spawned,false);assert.equal(c.records[0].guard_fired,true);
  const nightly=context();nightly.advance(800000);assert.equal(phaseLimits(nightly,'compare-kernels').wall_ms,285000);
});
test('success preserves scientific result apart from optional diagnostics',()=>{
  const c=context();const original={type:'verification-ok',output:'both kernels',theoremNames:['target'],executionEvidence:{status:'OBSERVED_PARTIAL'}};
  const f=withTerminationDiagnostics(original,c);const {terminationDiagnostics,...same}=f;
  assert.deepEqual(same,original);assert.equal(terminationDiagnostics.requestId,c.requestId);
});

test('project metadata is observed server-side and missing/drifted pins cannot elevate',()=>{
  assert.equal(observeProjectPolicy('/missing-fixture-root','viridis-lean-4.28'),null);
  assert.equal(observeProjectPolicy('/missing-fixture-root','../caller-path'),null);
  const request={project:PROJECT_POLICY.project,challenge:'fixture',solution:'fixture',theoremNames:PROJECT_POLICY.theorem_names,
    observedProjectPolicy:PROJECT_POLICY,timeout:1200,profile:FOUNDATION_PROFILE.name};
  assert.equal(makeExecutionContext('fixture-only',request,()=>0,'/missing-fixture-root').profile,DEFAULT_PROFILE);
});
