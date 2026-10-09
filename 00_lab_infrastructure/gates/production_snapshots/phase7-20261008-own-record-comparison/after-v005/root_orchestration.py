"""Explicit root-only orchestration; no automatic operation or acceptance rule.

Every operation delegates an independently reviewed frozen consumer. Install,
close, source copy, preflight and plan preparation are distinct root calls.
No credential retrieval, production HTTP, scheduler or generation occurs here.
"""
from pathlib import Path
import hashlib,json,types
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
ADOPTER=Path('/private/tmp/phase7-own-record-root-adapter-successor-20261008-v003/public/00_lab_infrastructure/gates/production_snapshots/phase7-20261008-own-record-root-adapter/after/root_weekly_configuration.py');ADOPTER_SHA='cec387e1d993ec93f001e8eb33b2c8c89ad53104db93a0ab4da12554cb462129'
EXTENSION=Path('/private/tmp/phase7-own-record-root-adapter-successor-20261008-v003/public/00_lab_infrastructure/gates/production_snapshots/phase7-20261008-own-record-root-adapter/after/root_weekly_purpose_specs.py');EXTENSION_SHA='fe41f08b5b3b91fe3c740fef3c3b70d0c08e088c9f2edfcf8a1b79494f180e37'
UTILITY=Path('/private/tmp/phase7-own-record-runtime-successor-20261008-v005/runtime_successor.py');UTILITY_SHA='e9ad9d196fb6e384b96151226733ea5db42f490adb489bc265b02f58e135f498'
DEPENDENCIES=[{'path':'/private/tmp/phase7-generic-runtime-successor-20261008-v001/runtime_successor.py','sha256':'db1273bb1b345f80e41bc45f94aefa53e56a3be8d06afc28121e8404876cf0e7'},{'path':'/private/tmp/phase7-generic-runtime-successor-20261008-v001/generic_prospective_catalog.py','sha256':'2dca14f6efceb8141aa3e2d92d2e41cf44e4ec5b318a74a02caba047304d5529'},{'path':'/private/tmp/phase7-same-concept-runtime-successor-20261008-v001/runtime_successor.py','sha256':'daeb140dc581104127f2e9eeacf6efb56f016ab381c0202a52ea67a97f183599'},{'path':'/private/tmp/phase7-authority-import-runtime-successor-20261008-v001/runtime_successor.py','sha256':'e0ebe49d167f886f0a159743f177a7963b188a233f03602225979051d3a961d6'},{'path':'/private/tmp/phase7-public-state-runtime-installer-20261008-v003/runtime_successor.py','sha256':'99453df4fc6f62cab92e4604765a0ca492a0ad89903a21789a292874c417db5f'},{'path':'/private/tmp/phase7-first-seven-plan-builder-20261007-v003/prepare_first_seven_plan.py','sha256':'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'}]
DEPENDENCIES += [{'path':str(UTILITY),'sha256':UTILITY_SHA},{'path':'/private/tmp/phase7-own-record-runtime-successor-20261008-v005/own_prospective_catalog.py','sha256':'b9dd8954b2d6a51115a96e1ed6561401de3120fa56dbbff14ce8e37e2a2bffa9'}]

def need(value,reason):
 if not value:raise ValueError('HOLD_'+reason)
def raw(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'REGULAR_REVIEWED_SOURCE');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'SOURCE_RACE');return b
def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def binding(path):return {'path':str(Path(path)),'sha256':sha(path)}
def load(path,pin,name):
 need(sha(path)==pin,'FROZEN_CALLER_SOURCE');m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw(path),str(path),'exec'),m.__dict__);need(sha(path)==pin,'CALLER_IMPORT_RACE');return m
def callers():
 # Predecessor runtime admission must not see unbounded new canonical modules.
 # These exact caller modules are compiled from TMP; later purpose membership
 # is proven by the unchanged full collector/actual merged source graph.
 need(all(sha(r['path'])==r['sha256']for r in DEPENDENCIES),'EXACT_RESTORED_UNSYMLINKED_LITERAL_DEPENDENCIES')
 return load(ADOPTER,ADOPTER_SHA,'root_exact_generic_adopter'),load(EXTENSION,EXTENSION_SHA,'root_exact_generic_extra_purpose'),load(UTILITY,UTILITY_SHA,'root_exact_generic_runtime_utility')
def actual_merge(adopter,evidence):return adopter.require_merge(evidence)
def prepare_install_configuration(*,evidence,source_gates,output,predecessor_closure,predecessor_close,protected_before,reviewed_source_proof):
 a,x,u=callers();head,merge,tree=actual_merge(a,evidence);ssot=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before=u.raw(ssot);ledger=json.loads(before);rows=u.full35(ledger);_,activation_raw=u.closed_relative_binding(ledger['enforcement_activation']);activation=json.loads(activation_raw);source_gates=Path(source_gates).resolve(strict=True);hashes={n:u.sha(source_gates/n)for n in u.MATERIAL_NAMES}
 config={'standard':'VRS-PHASE7-OWN-RECORD-RUNTIME-SUCCESSOR-CONFIG-1','canonical_root':str(ROOT),'output':str(Path(output)),'expected_ssot_sha256':u.digest(before),'expected_publication_projection_sha256':u.digest(u.encoded(rows)),'predecessor_runtime':activation['authorized_runtime_update'],'predecessor_closure':predecessor_closure,'predecessor_close':predecessor_close,'source_gates':str(source_gates),'source_hashes':hashes,'merged_pr':evidence['MERGED_PR.json'],'expected_head_sha':head,'expected_merge_commit':merge,'merged_commit':evidence['MERGED_COMMIT.json'],'merged_tree':evidence['COMPLETE_MERGED_TREE.json'],'live_protected_before':protected_before,'reviewed_source_proof':reviewed_source_proof,'reviewed_driver_sha256':UTILITY_SHA}
 # Read-only actual preflight; it cannot install, nominate or supply a PASS.
 u.preflight(config);need(u.raw(ssot)==before,'PREFLIGHT_SSOT_RACE');return config

def install_once(config):
 a,x,u=callers();need(config.get('reviewed_driver_sha256')==UTILITY_SHA,'EXACT_INSTALL_SOURCE');return u.install(config,reviewed_driver_sha256=UTILITY_SHA)
def close_once(output,protected_after):
 a,x,u=callers();return u.close(output,protected_after,reviewed_driver_sha256=UTILITY_SHA)

def matching_manual_spec(adopter,tree,name,path,destination):
 b=adopter.raw(path);matches=[r['path']for r in tree['tree']if r.get('type')=='blob'and r.get('mode')in{'100644','100755'}and r.get('sha')==adopter.blob(b)];adopter.need(matches,'ACTUAL_OWN_MANUAL_SOURCE_BLOB:'+name);gp=sorted(matches,key=lambda p:('/production_snapshots/'not in p,len(p),p))[0];return {'name':name,'source':str(path),'git_path':gp,'destination':destination}
def prepare_source_adoption(*,evidence,checkout,output,include_historical_c329=False):
 a,x,u=callers();head,merge,tree=actual_merge(a,evidence)
 manual={'manual_db1273bb':Path(DEPENDENCIES[0]['path']),'manual_daeb140d':Path(DEPENDENCIES[2]['path']),'manual_e0ebe49d':Path(DEPENDENCIES[3]['path']),'manual_99453df4':Path(DEPENDENCIES[4]['path'])}
 specs=a.source_specs(checkout,tree,runtime_consumer=UTILITY,manual_sources=manual);specs=x.add_purpose_specs(a,checkout,tree,specs)
 # Genuine pure-profile basename; never a mutable/runtime import alias.
 specs.append(matching_manual_spec(a,tree,'manual_generic_prospective_catalog',Path(DEPENDENCIES[1]['path']),'manual_dependencies/2dca14f6/generic_prospective_catalog.py'))
 specs.append(matching_manual_spec(a,tree,'manual_own_prospective_catalog',Path(DEPENDENCIES[-1]['path']),'manual_dependencies/b9dd8954/own_prospective_catalog.py'))
 for name,pin,path in [('root_weekly_configuration.py',ADOPTER_SHA,ADOPTER),('root_weekly_purpose_specs.py',EXTENSION_SHA,EXTENSION)]:
  a.need(a.sha(path)==pin,'EXACT_DURABLE_ROOT_CALLER:'+name);row=matching_manual_spec(a,tree,name,path,name);specs.append(row)
 if include_historical_c329:
  p=Path('/private/tmp/phase7-prospective-catalog-close-proposal-20261008-v001/prospective_catalog_close.py');a.need(a.sha(p)=='c329825ea3e9f498acf639edb29fed91ae7ab4376cce1d3319666648adc2a7e3','EXACT_HISTORICAL_C329');specs.append(matching_manual_spec(a,tree,'manual_historical_c329',p,'manual_dependencies/c329825e/prospective_catalog_close.py'))
 return a.adoption_plan(ROOT,evidence,specs,output)
def adopt_source_once(plan):
 a,x,u=callers();return a.adopt_sources(plan)
def fresh_source_preflight(adoption,current_generic_closure):
 a,x,u=callers();u.require_current_closure(current_generic_closure);return a.preflight_sources(ROOT,adoption,current_generic_closure)
def prepare_actual_inputs(*,adoption,current_generic_closure,package,captured_gets,recovery,source_registration,authority,community_mirror_proof,output):
 a,x,u=callers();u.require_current_closure(current_generic_closure);source_inputs,proof=a.preflight_sources(ROOT,adoption,current_generic_closure)
 return a.emit_actual_inputs(ROOT,adoption,source_inputs,package=package,captured_gets=captured_gets,registration_recovery=recovery,source_registration=source_registration,authority=authority,community_mirror_proof=community_mirror_proof,output=output)
def prepare_actual_plan(*,adoption,current_generic_closure,actual_inputs,output):
 a,x,u=callers();u.require_current_closure(current_generic_closure);source_inputs,proof=a.preflight_sources(ROOT,adoption,current_generic_closure);row=next(r for r in proof['purpose_source_pins']if r['name']=='invoke_weekly_digest.py');a.need(row['sha256']==a.PRODUCTION['invoke_weekly_digest.py'],'FROZEN_OWN_SOURCE_PROVEN_ENTRY');entry=load(Path(row['path']),row['sha256'],'root_exact_bound_weekly_invocation');return entry.prepare(ROOT,actual_inputs,output)
if __name__=='__main__':raise SystemExit('HOLD: only explicit root operations with actual successor merge/current closure; no automatic action')
