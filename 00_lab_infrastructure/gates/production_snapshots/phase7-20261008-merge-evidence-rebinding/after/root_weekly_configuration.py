"""Explicit source-bound root adoption/configuration, with no automatic action.

This ordinary adapter delegates current source/runtime/default/capture admission
to frozen generic recipe sources. Future merged evidence and current closure
must be supplied by root; no credential lookup, endpoint or SSOT action here.
"""
from pathlib import Path
import hashlib,json,re,types
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
TMP=Path('/private/tmp')
CONFIG_SHA='821dabc5aca3da8fbb18dfc9cd5bd063f01538475c0255634e66b81a28371061'
CAPTURE_SHA='987aec5ccb80db8222dc526ee9c361d510b4c8229f68f5bb7f525efed045e415'
PRODUCTION={'weekly_digest_executor.py': 'ce284d24ab309650a3f98b19a5edb8fd6c0912d40bb19bb868bb3bec7c6da28d', 'weekly_digest_boundary.py': '7b3c20bbf5d58a1715c69ebe811dd048105a25386f58d9e85218dd83a43b9b94', 'weekly_digest_runtime.py': '869bae5001fda493a8f7690eddac1cc3eb489329bb8543bf964ef83d4df2479b', 'weekly_checkpoint_replay.py': '86de42bbe3d216dabefa68e4d79f2896c3f1712b7e6ff5a834d9f9c073eb1530', 'prepare_weekly_digest_plan.py': '8bee9b1123e7cf9fcc860d6a02780c251d548c83bd429574d67e8bdfb49e758f', 'invoke_weekly_digest.py': '58b90ef7012750274abcf17dcceff9d5de80442798b594962032b1646233df47', 'weekly_archive_wait.py': '179cd1f897c8f4f68eb3dc2c7473c2fd28e6defef154d88541d9fa27540ed055', 'weekly_digest_queue.py': '24ef923a0dbd0da460d1e322d57c0fa2a706be2ba5964461d24277362889ec59', 'prepare_weekly_configuration.py': '821dabc5aca3da8fbb18dfc9cd5bd063f01538475c0255634e66b81a28371061', 'capture_weekly_inputs.py': '987aec5ccb80db8222dc526ee9c361d510b4c8229f68f5bb7f525efed045e415', 'weekly_pending_discovery.py': 'f016dfbfbc875b4effa39862006895d195a4d4cc7f0b360b353914d68f75cfd6', 'owned_digest_machine.py': '0ed1b5aae979b5db69d001783f77900bf3a9e9c7d9591c27ea08f8aae0396b2b', 'owned_journal_writer.py': '711cef68f1b67aed468d5f975535cb218f7bf7cc69fe2cc8bc069e6a526d83a5', 'owned_legacy_preview_aliases.py': '0739cf7351501062f8342e376d6e6e0db21096d35170a2a998858e6846cec775', 'owned_prior_legacy.py': '260ade5bcbb55bd2abe278d25df698cb0de7156ebe68b0ca939045600f3e50ca', 'owned_weekly_discovery.py': '18bb000d76258a3a5a04bbdd85a4274bbc3128bdee370c906515c5aa86653213', 'runtime_closure_view.py': '1bc540543f0058eeff6e3d5e80bdee20858be387b0a9e36bc11019407747d771'}
ORIGINAL={'first_digest_publisher.py':'551674f989688a5076d49308044c46e3294421fadf2c205381f20e14544631ba','publisher_previews.py':'f33df8657ef9a25174af360d54139f536d39d7ee1a463eea68bff4a3c2fc2c22','publisher_recovery.py':'fd75fa40fe52d157b3516bf8a96b9acdd203e1d76fff58c3949f667a6d44153c','readonly_account.py':'daa36ca7fa4c40d923be5b411cf47463f5ef61162bf7fb6e50b6a27ebb638720','mutation_journal_writer.py':'a2a72c49b5bc67a5c7535320bab5b6513b8cbfac3cf6c19d39b2e0c3d5d5c4e8'}
CHECKS={'gitleaks','report-only-consumers','verify-catalog','verify','verify-functions','lean-build-current','lean-build-p0','deposit-verify'}
def need(value,reason):
 if not value:raise ValueError('HOLD_'+reason)
def raw(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'REGULAR_BOUND_SOURCE');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'SOURCE_RACE');return b
def sha(path):return hashlib.sha256(raw(path)).hexdigest()
def binding(path):return {'path':str(Path(path)),'sha256':sha(path)}
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def encode(value):return json.dumps(value,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()+b'\n'
def bound(root,value):
 need(isinstance(value,dict)and set(value)=={'path','sha256'}and Path(value['path']).resolve(strict=True).is_relative_to(root)and sha(value['path'])==value['sha256'],'CURRENT_CANONICAL_BINDING');return json.loads(raw(value['path']))
def module(path,pin,name):
 need(sha(path)==pin,'EXACT_FROZEN_SOURCE');m=types.ModuleType(name);m.__file__=str(path);exec(compile(raw(path),str(path),'exec'),m.__dict__);need(sha(path)==pin,'SOURCE_IMPORT_RACE');return m
def recipe(path):return module(path,CONFIG_SHA,'root_frozen_weekly_configuration_recipe')
def capture_recipe(config,path):
 import sys
 prior=sys.modules.get('prepare_weekly_configuration');need(prior is None or sha(prior.__file__)==CONFIG_SHA,'NO_FOREIGN_CONFIGURATION_IMPORT')
 if prior is None:sys.modules['prepare_weekly_configuration']=config
 try:return module(path,CAPTURE_SHA,'root_frozen_weekly_get_capture_recipe')
 finally:
  if prior is None:sys.modules.pop('prepare_weekly_configuration')
def _exact_rebound_merge_references(evidence,result):
 """Canonical copy provenance only; raw merge objects/verdicts stay exact.

 The original RESULT retains its original TMP references. A canonical copy
 can rebind only its outer file paths, with all four original bytes re-read.
 """
 fields=[('merged_pr','MERGED_PR.json'),('merged_commit','MERGED_COMMIT.json'),('merged_tree','COMPLETE_MERGED_TREE.json')]
 if all(result.get(field)==evidence[name]for field,name in fields):return
 def closed(value,name):
  need(isinstance(value,dict)and set(value)=={'path','sha256'}and isinstance(value['path'],str)and isinstance(value['sha256'],str)and re.fullmatch('[0-9a-f]{64}',str(value['sha256']))is not None,'OWN_MERGE_COPY_CLOSED_BINDING')
  p=Path(value['path']);need(p.is_absolute()and '..'not in p.parts and str(p)==value['path']and p.name==name and str(p.resolve(strict=True))==value['path'],'OWN_MERGE_COPY_EXACT_ROLE_PATH')
  b=raw(p);need(hashlib.sha256(b).hexdigest()==value['sha256'],'OWN_MERGE_COPY_BOUND_HASH');return p,b
 copies={name:closed(evidence[name],name)for name in ('RESULT.json','MERGED_PR.json','MERGED_COMMIT.json','COMPLETE_MERGED_TREE.json')}
 parent=copies['RESULT.json'][0].parent
 need(parent.name=='merge-evidence'and parent.is_relative_to(ROOT/'reports/verification-coverage')and all(p.parent==parent for p,b in copies.values()),'OWN_MERGE_COPY_CANONICAL_SIBLING_SET')
 originals={name:closed(result.get(field),name)for field,name in fields};original_parent=originals['MERGED_PR.json'][0].parent
 need(original_parent.is_relative_to(TMP)and original_parent!=TMP and all(p.parent==original_parent for p,b in originals.values()),'OWN_MERGE_COPY_EXACT_ORIGINAL_TMP_SET')
 for field,name in fields:
  need(result[field]['sha256']==evidence[name]['sha256']and originals[name][1]==copies[name][1],'OWN_MERGE_COPY_ORIGINAL_RAW_BYTES:'+name)
 original_result=raw(original_parent/'RESULT.json');need(hashlib.sha256(original_result).hexdigest()==evidence['RESULT.json']['sha256']and original_result==copies['RESULT.json'][1],'OWN_MERGE_COPY_ORIGINAL_RESULT_BYTES')

def require_merge(evidence):
 need(isinstance(evidence,dict)and set(evidence)=={'RESULT.json','MERGED_PR.json','MERGED_COMMIT.json','COMPLETE_MERGED_TREE.json'},'COMPLETE_OWN_MERGE_EVIDENCE');objects={}
 for name,b in evidence.items():need(set(b)=={'path','sha256'}and sha(b['path'])==b['sha256'],'OWN_MERGE_RAW_BINDING');objects[name]=json.loads(raw(b['path']))
 result=objects['RESULT.json'];pr=objects['MERGED_PR.json'];commit=objects['MERGED_COMMIT.json'];tree=objects['COMPLETE_MERGED_TREE.json'];head=pr.get('headRefOid');merge=commit.get('sha')
 need(result.get('status')=='EXACT_HEAD_ORDINARY_SOURCE_PR_MERGED_ALL_CHECKS_PASS'and re.fullmatch('[0-9a-f]{40}',str(head))is not None and re.fullmatch('[0-9a-f]{40}',str(merge))is not None and result.get('head')==head and result.get('merge_commit')==merge and pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and type(pr.get('number'))is int and pr['number']>71 and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr['number'])and pr.get('mergeCommit',{}).get('oid')==merge and commit.get('tree',{}).get('sha')==tree.get('sha')and tree.get('truncated')is False,'ACTUAL_OWN_SUCCESSOR_MERGE')
 checks=pr.get('statusCheckRollup');need(isinstance(checks,list)and CHECKS<={r.get('name')for r in checks if r.get('status')=='COMPLETED'and r.get('conclusion')=='SUCCESS'}and all(r.get('status')=='COMPLETED'and r.get('conclusion')in{'SUCCESS','SKIPPED'}for r in checks),'ACTUAL_ALL_EIGHT_HEAD_CHECKS')
 _exact_rebound_merge_references(evidence,result)
 need(isinstance(tree.get('tree'),list)and all(isinstance(r,dict)and isinstance(r.get('path'),str)for r in tree['tree'])and len({r['path']for r in tree['tree']})==len(tree['tree']),'COMPLETE_UNIQUE_TREE');return head,merge,tree
def exact_sources(tree,specs):
 need(isinstance(specs,list)and specs,'EXPLICIT_SOURCE_SPECS');nodes={r['path']:r for r in tree['tree']};rows=[]
 for row in specs:
  need(isinstance(row,dict)and set(row)=={'name','source','git_path','destination'}and isinstance(row['name'],str),'CLOSED_SOURCE_SPEC');b=raw(row['source']);gp=row['git_path'];dest=row['destination'];need(isinstance(gp,str)and not Path(gp).is_absolute()and'..'not in Path(gp).parts and isinstance(dest,str)and not Path(dest).is_absolute()and'..'not in Path(dest).parts,'RELATIVE_SOURCE_DESTINATION');node=nodes.get(gp,{});need(node.get('type')=='blob'and node.get('mode')in{'100644','100755'}and node.get('sha')==blob(b),'OWN_EXACT_MERGED_BLOB:'+row['name']);h=hashlib.sha256(b).hexdigest();need(row['name']not in PRODUCTION or PRODUCTION[row['name']]==h,'FROZEN_GENERIC_PRODUCTION:'+row['name']);need(row['name']not in ORIGINAL or ORIGINAL[row['name']]==h,'UNCHANGED_ORIGINAL_PRIVATE_HELPER:'+row['name']);rows.append(dict(row,sha256=h,bytes=len(b),git_blob_sha=node['sha']))
 need(len({r['name']for r in rows})==len(rows)and len({r['destination']for r in rows})==len(rows),'UNIQUE_SOURCE_NAMES_DESTINATIONS');names={r['name']for r in rows};need(set(PRODUCTION)|set(ORIGINAL)|{'prepare_first_seven_plan.py','runtime_successor.py'}<=names,'COMPLETE_GENERIC_SOURCE_POOL');need(all(r['destination']==r['name']if not r['name'].startswith('manual_')else r['destination'].startswith('manual_dependencies/')for r in rows),'EXPLICIT_FLAT_OR_MANUAL_DESTINATIONS');return rows
def source_specs(checkout,tree,*,runtime_consumer,manual_sources=None):
 """Pure own-checkout path selection; exact_sources reproves each byte."""
 checkout=Path(checkout).resolve(strict=True);need(tree.get('truncated')is False and isinstance(tree.get('tree'),list),'REAL_COMPLETE_OWN_TREE');manual_sources={}if manual_sources is None else manual_sources;need(isinstance(manual_sources,dict)and all(isinstance(n,str)and n.startswith('manual_')for n in manual_sources),'EXPLICIT_MANUAL_SOURCE_POOL');specs=[];base='00_lab_infrastructure/gates/'
 def add(name,path,destination,pin=None):
  path=Path(path);b=raw(path);need(pin is None or hashlib.sha256(b).hexdigest()==pin,'EXPECTED_ADOPTION_SOURCE:'+name);matches=[r['path']for r in tree['tree']if r.get('type')=='blob'and r.get('mode')in{'100644','100755'}and r.get('sha')==blob(b)];need(matches,'REAL_OWN_MERGED_SOURCE_PATH:'+name);preferred=base+name;gp=preferred if preferred in matches else sorted(matches,key=lambda x:('/production_snapshots/'not in x,len(x),x))[0];specs.append({'name':name,'source':str(path),'git_path':gp,'destination':destination})
 for name,pin in PRODUCTION.items():add(name,checkout/base/name,name,pin)
 for name,pin in ORIGINAL.items():
  matches=[r['path']for r in tree['tree']if r.get('type')=='blob'and r.get('mode')in{'100644','100755'}and Path(r['path']).name==name and '/production_snapshots/'in r['path']];paths=[checkout/x for x in matches if(checkout/x).is_file()and sha(checkout/x)==pin];need(paths,'UNCHANGED_PUBLIC_SOURCE_SNAPSHOT:'+name);add(name,sorted(paths,key=lambda x:(len(str(x)),str(x)))[0],name,pin)
 name='prepare_first_seven_plan.py';pin='da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740';matches=[checkout/r['path']for r in tree['tree']if r.get('type')=='blob'and Path(r['path']).name==name and '/production_snapshots/'in r['path']];paths=[x for x in matches if x.is_file()and sha(x)==pin];need(paths,'UNCHANGED_BUILDER_PUBLIC_SNAPSHOT');add(name,sorted(paths,key=lambda x:(len(str(x)),str(x)))[0],name,pin);add('runtime_successor.py',runtime_consumer,'runtime_successor.py')
 for name,path in sorted(manual_sources.items()):add(name,path,'manual_dependencies/'+name[7:]+'/runtime_successor.py')
 exact_sources(tree,specs);return specs
def adoption_plan(root,evidence,specs,output):
 root=Path(root).resolve(strict=True);out=Path(output);need(root==ROOT.resolve(strict=True)and out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists(),'NEW_CANONICAL_ADOPTION');head,merge,tree=require_merge(evidence);rows=exact_sources(tree,specs)
 return {'standard':'VRS-GENERIC-WEEKLY-SOURCE-ADOPTION-PLAN-1','status':'ACTUAL_MERGED_BLOBS_PENDING_ROOT_COPY_NOT_RUNTIME_ADMISSION','canonical_root':str(root),'output':str(out),'head':head,'merge':merge,'sources':rows,'merge_evidence':evidence,'unresolved':['actual_generic_runtime_closure','fresh_default_population','actual_source_account_GET_admission','actual_immutable_plan'],'zenodo_writes':0,'certifies':False}
def adopt_sources(plan):
 root=Path(plan['canonical_root']).resolve(strict=True);out=Path(plan['output']);need(root==ROOT.resolve(strict=True)and set(plan)=={'standard','status','canonical_root','output','head','merge','sources','merge_evidence','unresolved','zenodo_writes','certifies'}and plan['standard']=='VRS-GENERIC-WEEKLY-SOURCE-ADOPTION-PLAN-1'and plan['status']=='ACTUAL_MERGED_BLOBS_PENDING_ROOT_COPY_NOT_RUNTIME_ADMISSION'and plan['zenodo_writes']==0 and plan['certifies']is False and out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists(),'ROOT_EXPLICIT_ADOPTION');head,merge,tree=require_merge(plan['merge_evidence']);need(head==plan['head']and merge==plan['merge'],'SAME_OWN_MERGE');specs=[{k:r[k]for k in('name','source','git_path','destination')}for r in plan['sources']];rows=exact_sources(tree,specs);need(rows==plan['sources'],'UNCHANGED_SOURCE_PROOF_BEFORE_COPY');by={r['name']:r for r in rows};c=recipe(by['prepare_weekly_configuration.py']['source']);out.mkdir(parents=True,exist_ok=False)
 for row in rows:c.immutable(out/row['destination'],raw(row['source']));need(sha(out/row['destination'])==row['sha256'],'SOURCE_COPY_READBACK')
 evidence={}
 for name,b in plan['merge_evidence'].items():need(sha(b['path'])==b['sha256'],'MERGE_READBACK_RACE');p=out/'merge-evidence'/name;c.immutable(p,raw(b['path']));evidence[name]=binding(p)
 receipt={**plan,'standard':'VRS-GENERIC-WEEKLY-SOURCE-ADOPTION-1','status':'ACTUAL_OWN_MERGED_SOURCE_ADOPTED_NOT_RUNTIME_OR_PUBLICATION_CLEARANCE','sources':[{**r,'binding':binding(out/r['destination'])}for r in rows],'merge_evidence':evidence,'ssot_writes':0};p=out/'ADOPTION_RECEIPT.json';c.immutable(p,encode(receipt));return binding(p)
def build_source_inputs(root,adoption,current_runtime_closure):
 root=Path(root).resolve(strict=True);a=bound(root,adoption);need(root==ROOT.resolve(strict=True)and a.get('standard')=='VRS-GENERIC-WEEKLY-SOURCE-ADOPTION-1'and a.get('status')=='ACTUAL_OWN_MERGED_SOURCE_ADOPTED_NOT_RUNTIME_OR_PUBLICATION_CLEARANCE','ACTUAL_SOURCE_ADOPTION');head,merge,tree=require_merge(a['merge_evidence']);need(head==a['head']and merge==a['merge'],'OWN_SOURCE_MERGE');rows=a['sources'];by={r['name']:r for r in rows};need(len(by)==len(rows),'UNIQUE_ADOPTED_NAMES')
 for row in rows:need(row['binding']==binding(row['binding']['path'])and row['binding']['sha256']==row['sha256']and Path(row['binding']['path'])==Path(adoption['path']).parent/row['destination'],'EXACT_OWN_ADOPTED_SOURCE')
 c=recipe(by['prepare_weekly_configuration.py']['binding']['path']);builder=by['prepare_first_seven_plan.py']['binding'];consumer=by['runtime_successor.py']['binding'];pool=[r['binding']['path']for r in rows if not r['name'].startswith('manual_')];extras,edges,duplicates=c.collect_extra_sources(root,current_runtime_closure,builder,pool);_,closure=c.bound(root,current_runtime_closure,relative=True);pins=closure['source_pins']+extras;mapping=c.suggest_git_paths(root,pins,a['merge_evidence']['COMPLETE_MERGED_TREE.json']);inputs={'canonical_root':str(root),'current_runtime_closure':current_runtime_closure,'extra_purpose_sources':extras,'git_path_by_name':mapping,'merged_pr':a['merge_evidence']['MERGED_PR.json'],'merged_commit':a['merge_evidence']['MERGED_COMMIT.json'],'merged_tree':a['merge_evidence']['COMPLETE_MERGED_TREE.json'],'runtime_consumer':consumer,'source_session_consumer':builder};actual,origin=c.source_materials(root,inputs)
 return inputs,{'status':'ACTUAL_BOUND_SOURCE_MATERIALS_NOT_RUNTIME_OR_PUBLICATION_CLEARANCE','source_pins':actual,'source_origin':origin,'edges':edges,'identical_copies':duplicates,'certifies':False}
def preflight_sources(root,adoption,current_runtime_closure):
 inputs,materials=build_source_inputs(root,adoption,current_runtime_closure);a=bound(Path(root),adoption);by={r['name']:r for r in a['sources']};c=recipe(by['prepare_weekly_configuration.py']['binding']['path']);q=capture_recipe(c,by['capture_weekly_inputs.py']['binding']['path']);return inputs,q.preflight_sources(root,inputs)
def capture_sources(root,adoption,inputs,week,source_id,source_registration,memory_token,output):
 a=bound(Path(root),adoption);by={r['name']:r for r in a['sources']};c=recipe(by['prepare_weekly_configuration.py']['binding']['path']);q=capture_recipe(c,by['capture_weekly_inputs.py']['binding']['path']);return q.capture_inputs(root,inputs,week,source_id,memory_token,output,source_registration=source_registration)
def emit_actual_inputs(root,adoption,source_inputs,*,package,captured_gets,registration_recovery,source_registration,authority,community_mirror_proof,output):
 root=Path(root).resolve(strict=True);a=bound(root,adoption);by={r['name']:r for r in a['sources']};c=recipe(by['prepare_weekly_configuration.py']['binding']['path']);capture=bound(root,captured_gets);need(capture.get('standard')=='VRS-OWNED-DIGEST-ROOT-GET-INPUTS-1'and capture.get('status')=='GETS_CAPTURED_NOT_PUBLICATION_CLEARANCE'and capture.get('zenodo_writes')==0 and capture.get('certifies')is False,'GENUINE_GET_ONLY_CAPTURE');account=bound(root,capture['account_discovery']);need(account.get('start_kind')in{'NEW_VERSION','CREATE_WEEK'},'ACTUAL_ACCOUNT_KIND');pins,_=c.source_materials(root,source_inputs);registrar=next(r for r in pins if r['name']=='methods_digest_registration.py');ordinary={k:registrar[k]for k in('path','sha256')}
 value={**source_inputs,'standard':'VRS-OWNED-DIGEST-CONFIG-CONSTRUCTION-1','canonical_root':str(root),'package':str(package),'registration_recovery':registration_recovery,'predecessor_registration':source_registration,'source_legacy_receipt':capture['source_legacy_receipt'],'source_native_receipt':capture['source_native_receipt'],'source_native_before_create':capture['source_native_before_create'],'authority':authority,'community_mirror_proof':community_mirror_proof,'recovery_consumer':ordinary,'ordinary_cohort_consumer':ordinary,'account_discovery':capture['account_discovery'],'start_kind':account['start_kind']}
 return c.emit_inputs(root,value,output)
if __name__=='__main__':raise SystemExit('HOLD: root explicit own merged evidence/current generic closure required; no write or GET invoked')
