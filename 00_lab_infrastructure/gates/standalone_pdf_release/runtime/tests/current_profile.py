"""PRIVATE TEST ONLY full current20+shared1 plan/review/nomination DATA."""
from build_source_chain import *
import build_source_chain
build_source_chain.ALLOWED_RUNTIME_GLOBALS|=frozenset({'LEGACY_CONSUMER','LEGACY_SCOPE','SESSION_CONSUMER','PROVIDER_SHA'})

def build_current_profile(c,legacy):
 m=c.runtime
 for name,key in [('LEGACY_CLOSURE','legacy_closure'),('LEGACY_CONSUMER','legacy_consumer'),('LEGACY_SCOPE','legacy_scope'),('SESSION_CONSUMER','session_consumer')]:c.remap(name,legacy[key])
 directory=Path(m.PROFILE_PATH).parent;rows=[]
 for name in sorted(m.MODULE_NAMES):
  path=c.root/directory/name
  # Preserve the caller's declared TEST source/platform DATA copies when present.
  if not path.exists():c.put(directory/name,(RUNTIME/name).read_bytes())
  rows.append({'name':name,'path':str(path),'sha256':sha(path.read_bytes()),'git_path':m.GIT_PREFIX+name})
 common=c.put(directory/'common'/m.SHARED_INPUT_NAME,(RUNTIME.parent/'common'/m.SHARED_INPUT_NAME).read_bytes())
 shared=[{'name':m.SHARED_INPUT_NAME,**common,'git_path':m.SHARED_INPUT_GIT_PATH}];allrows=rows+shared;hashes={r['name']:r['sha256']for r in allrows}
 origin,oid=c.origin('metadata/CURRENT_ORIGIN',allrows)
 provider=c.put('metadata/PROVIDER.json',{'fixture':'SIMULATED_PROVIDER_NOT_ACTUAL_USER_AUTHORITY','standard':'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1','provider_tool':'mcp__codex_app__read_thread','thread_id':'01a12d47-02a3-78f3-beb4-6b8e1a079dd2','user_messages':[{'type':'userMessage','id':'01a132f6-4708-7440-a9ba-ebf03deeb906','content':[{'type':'text','text':m.USER_DIRECTIVE+'\n'}]}]})
 c.remap('PROVIDER_SHA',provider['sha256'])
 authority=c.put('metadata/AUTHORITY.json',{'standard':'VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1','source':'Current user message in this Codex chat','user_text':m.USER_DIRECTIVE,'captured_at_utc':'2020-01-01T00:00:00Z','scientific_scope_changes':False,'provider_instruction':provider})
 review=c.put('metadata/CURRENT_SOURCE_REVIEW.json',{'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-13','status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS','reviewer':'TEST ONLY simulated review DATA, not independent source review','source_hashes':hashes,'legacy_closure':m.LEGACY_CLOSURE,'review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK',**m.CURRENT_SOURCE_REVIEW_CHANGE_FLAGS})
 fields={'installed_at_utc':'2020-01-02T00:00:00Z','user_authority':authority,'source_origin':origin,'source_review':review,'access_registry':c.marker,'predecessor_installation':m.PREDECESSOR_INSTALLATION,'transient_rehydration':m.TRANSIENT_REHYDRATION_POLICY,'data_alias_observation':m.DATA_ALIAS_OBSERVATION,'platform_timezone_observation':m.PLATFORM_TIMEZONE_OBSERVATION,'shared_dependencies':shared,'note_preparation':m.NOTE_PREPARATION}
 value={'standard':m.STANDARD,'status':m.STATUS,'canonical_root':str(c.root),'legacy_closure':m.LEGACY_CLOSURE,'legacy_consumer':m.LEGACY_CONSUMER,'legacy_scope':m.LEGACY_SCOPE,'source_session_consumer':m.SESSION_CONSUMER,'modules':rows,'default_routes':m.DEFAULT_ROUTES,**fields}
 binding=c.put(m.PROFILE_PATH,value)
 plan={'standard':'VRS-EXACT-DIGEST-ARCHIVAL-PDF-RUNTIME-INSTALL-PLAN-1','status':'ROOT_REVIEWED_READY_NOT_INSTALLED','canonical_root':str(c.root),'source_modules':rows,'historical_publisher':m.HISTORICAL_PUBLISHER,**fields}
 rootreview=c.put('metadata/CURRENT_ROOT_REVIEW.json',{'standard':'VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-13','status':'EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS','reviewer':'TEST ONLY simulated root review DATA, no installation authority','plan_projection_sha256':sha(encoded(plan)),'merged_source_commit':oid,'source_hashes':hashes,'historical_publisher_sha256':'4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94',**m.CURRENT_SOURCE_REVIEW_CHANGE_FLAGS})
 plan['root_review']=rootreview;plan_binding=c.put(directory/'INSTALL_PLAN.json',plan)
 installer=next(r for r in rows if r['name']=='install_packaging_runtime.py')
 nomination={'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-13','status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING','profile':binding,'installer_source':{k:installer[k]for k in('path','sha256')},'merged_source_commit':oid,'root_review_receipt':rootreview}
 c.put(m.NOMINATION_PATH,nomination)
 m.module_table(c.root,rows);m.shared_dependency_table(c.root,shared,installed=True)
 proof=m.source_proof(c.root,origin,allrows)
 m.require_source_review(json.loads(Path(review['path']).read_bytes()),hashes,m.LEGACY_CLOSURE)
 m.require_nomination(c.root,binding);m.require_installed_plan(c.root,value,nomination,proof)
 return {'profile_binding':binding,'plan_binding':plan_binding,'module_rows':rows,'shared_rows':shared,'source_origin':origin,'source_proof':proof,'root_review':rootreview,'source_review':review,'actual_full_source_session_not_claimed':True}

if __name__=='__main__':
 c=Constructor(sys.argv[1]);c.predecessors()
 legacy={'legacy_closure':c.marker,'legacy_consumer':c.marker,'legacy_scope':c.marker,'session_consumer':c.marker}
 value=build_current_profile(c,legacy)
 report={'standard':'VRS-PRIVATE-W42-CURRENT20-CONTROL-POC-1','fixture_only':True,'current':value,'no_full_source_session_claim':True,'mocked_validators':0,'context_mints':0,'core_reads_exec_writes':0,'network':0}
 out=Path(sys.argv[2]);out.write_bytes(encoded(report));print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes()),'proof_rows':len(value['source_proof']['proofs'])}))
