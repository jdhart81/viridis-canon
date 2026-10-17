"""PRIVATE TEST ONLY alias/TZIF/eight-transient closed DATA constructor."""
from build_source_chain import *
import build_source_chain
EXTRA=frozenset({'SCIENTIFIC_ALIAS_PATH','SCIENTIFIC_ALIAS_READLINK','PLATFORM_TZ_LOGICAL','PLATFORM_TZ_PHYSICAL','PLATFORM_TZ_LINK_PATHS','LEGACY_TRANSIENT_SOURCES','LEGACY_TRANSIENT_ROOT','TRANSIENT_REHYDRATION_POLICY'})
build_source_chain.ALLOWED_RUNTIME_GLOBALS|=EXTRA

def platform(c, certificate=None):
 m=c.runtime;base=c.root.parent/(c.root.name+'-platform');base.mkdir()
 alias=c.root.parent/(c.root.name+'  ');alias.symlink_to(c.root.name)
 c.remap('SCIENTIFIC_ALIAS_PATH',alias);c.remap('SCIENTIFIC_ALIAS_READLINK',c.root.name)
 names={'candidate_proof':'VERIFICATION_CANDIDATE.lean','formal_statement':'VERIFICATION_STATEMENT_V2.lean','independent_cloud_receipt':'COMPARATOR_VERIFICATION_RECEIPT_V2.json','request':'ENGINE3_FROZEN_REQUEST_V2.json','sealed:SEALED_CLAIM_INVENTORY.json':'SEALED_CLAIM_INVENTORY.json','sealed:SEALED_RUN_MANIFEST.json':'SEALED_RUN_MANIFEST.json','sealed:SEALED_paper.pdf':'SEALED_paper.pdf','sealed:SEALED_paper.tex':'SEALED_paper.tex'}
 rows=[]
 for name,file in names.items():
  relative=Path('RESEARCH_PIPELINE_v2/engine3_verification/Run-117')/file;b=c.put(relative,('TEST ONLY source DATA '+name).encode());rows.append({'binding_name':name,'bytes':len(Path(b['path']).read_bytes()),'logical_path':str(alias/relative),'physical_path':b['path'],'sha256':b['sha256']})
 if certificate is None:certificate=c.put('metadata/ALIAS_CERTIFICATE_DATA.json',{'fixture':'TEST ONLY original binding DATA, not scientific admission'})
 observation={'standard':'VRS-HISTORICAL-CONTROLPLANE-DATA-ALIAS-OBSERVATION-1','status':'ACTUAL_EXISTING_HISTORICAL_ALIAS_AND_ORIGINAL_CERTIFICATE_BYTES_VERIFIED_NOT_RUNTIME_ADMISSION','alias_path':str(alias),'canonical_root':str(c.root),'physical_target':str(c.root),'identity':m.data_alias_identity(alias),'observed_at_utc':'2020-01-01T00:00:00Z','original_binding_readbacks':rows,'representative_original_certificate':certificate,'scope':'TEST ONLY fixed temporary alias and DATA','alias_writes':0,'certificate_writes':0,'source_or_ssot_writes':0,'network_requests':0,'certifies':False}
 binding=c.put('metadata/ALIAS.json',observation);c.remap('DATA_ALIAS_OBSERVATION',binding)
 astdata=ast.parse((RUNTIME/'tests/test_packaging_v004_platform_timezone.py').read_bytes());b64=next(ast.literal_eval(n.value)for n in astdata.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='TZIF_B64'for t in n.targets));raw=base64.b64decode(b64)
 physical=base/'private/var/db/timezone/tz/fixture-version/zoneinfo/America/New_York';physical.parent.mkdir(parents=True);physical.write_bytes(raw)
 logical=base/'usr/share/zoneinfo/America/New_York';logical.parent.parent.parent.mkdir(parents=True)
 links=(base/'usr/share/zoneinfo',base/'var',base/'private/var/db/timezone/zoneinfo');links[0].symlink_to(str(base/'var/db/timezone/zoneinfo'));links[1].symlink_to('private/var');links[2].symlink_to(str(base/'private/var/db/timezone/tz/fixture-version/zoneinfo'))
 for name,value in [('PLATFORM_TZ_LOGICAL',logical),('PLATFORM_TZ_PHYSICAL',physical),('PLATFORM_TZ_LINK_PATHS',links)]:c.remap(name,value)
 os.environ['PYTHONTZPATH']=str(logical.parent.parent)
 frame={'TZif_header_hex':raw[:5].hex(),'bytes':len(raw),'sha256':sha(raw),'physical_file_identity':m.platform_file_identity(physical),'physical_regular_parent_chain':[{'path':str(p),'identity':m.platform_file_identity(p)}for p in reversed(physical.parents)],'resolution_symlink_chain':[{'path':str(p),'identity':m.data_alias_identity(p),'resolved_target':str(p.resolve(strict=True))}for p in links]}
 observation={'standard':'VRS-ROOT-EXACT-PLATFORM-TIMEZONE-DATA-READBACK-1','status':'EXACT_CURRENT_NATIVE_DATA_PATH_VERIFIED_NOT_RUNTIME_ADMISSION','zone_key':'America/New_York','logical_selected_path':str(logical),'physical_path':str(physical),'root_executable':sys.executable,'stdlib_TZPATH':[str(logical.parent.parent)],'before':copy.deepcopy(frame),'after':copy.deepcopy(frame),'created_at_utc':'2020-01-01T00:00:00Z','actual_failed_child_path_limitation':'TEST ONLY temporary descriptor','actual_failed_execution':c.marker,'independent_platform_path_evidence':c.marker,'scope':'TEST ONLY exact3552byte NY fixture and three links','heavy_scientific_executions':0,'network_requests':0,'source_certificate_alias_ledger_timezone_writes':0,'certifies':False}
 tz=c.put('metadata/TIMEZONE.json',observation);c.remap('CURRENT_PLATFORM_TIMEZONE_OBSERVATION',tz)
 m.require_data_alias_observation(c.root,binding);m.require_platform_timezone_observation(c.root,tz)
 return {'alias':binding,'timezone':tz,'genuine_validator_bodies':True,'tzif_bytes':len(raw)}

def transients(c):
 m=c.runtime;rows=[];sources=[];mapping={};targetroot=c.root/'transient-fixture';targetroot.mkdir()
 for row in m.LEGACY_TRANSIENT_SOURCES:
  raw=(REPO/row['git_path']).read_bytes();assert sha(raw)==row['source']['sha256'];b=c.put('durable-transients/'+row['name'],raw);target=targetroot/row['name'];target.write_bytes(raw);mapping[row['target']]=str(target)
  rows.append({**row,'source':b,'target':str(target)});sources.append({'name':row['name'],**b,'git_path':row['git_path']})
 c.remap('LEGACY_TRANSIENT_SOURCES',tuple(rows));c.remap('LEGACY_TRANSIENT_ROOT',targetroot);c.remap('TRANSIENT_REHYDRATION_POLICY',{'standard':'VRS-EXACT-LEGACY-TRANSIENT-REHYDRATION-1','mode':'EXCLUSIVE_MISSING_ONLY_EXISTING_EXACT_NOOP','allowed_targets':[r['target']for r in rows]})
 origin,_=c.origin('metadata/TRANSIENT_ORIGIN',sources);value=m.legacy_transient_precheck(c.root,origin,restore=False);assert value['transient_source_writes']==0
 return {'origin':origin,'path_map':mapping,'readback':value}

if __name__=='__main__':
 c=Constructor(sys.argv[1]);p=platform(c);t=transients(c)
 report={'standard':'VRS-PRIVATE-W42-PLATFORM-TRANSIENT-POC-1','fixture_only':True,'platform':p,'transients':t,'applied_data_remaps':c.remaps,'no_scientific_or_source_session_admission_claim':True,'core_reads_exec_writes':0,'secrets_reads':0,'network':0,'context_mints':0}
 out=Path(sys.argv[2]);out.write_text(json.dumps(report,sort_keys=True,indent=2,default=str)+'\n');print(json.dumps({'path':str(out),'sha256':sha(out.read_bytes())}))
