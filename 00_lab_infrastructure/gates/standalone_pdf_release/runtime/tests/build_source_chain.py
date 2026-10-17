"""PRIVATE TEST ONLY closed source-chain constructor; never production authority."""
from __future__ import annotations
import ast,base64,copy,datetime as dt,hashlib,importlib.util,json,os,sys,time,types
from pathlib import Path
_RELATIVE_RUNTIME=Path('00_lab_infrastructure/gates/standalone_pdf_release/runtime')
REPO=next((p for p in Path(__file__).resolve().parents if (p/_RELATIVE_RUNTIME/'packaging_runtime.py').is_file()),None)
if REPO is None:
 # Private qualification may locate only the already-local public checkout.
 hint=os.environ.get('VRS_W42_PUBLIC_TEST_REPO')
 if hint is None:raise RuntimeError('TEST_ONLY_PUBLIC_REPOSITORY_ROOT_REQUIRED')
 REPO=Path(hint).resolve(strict=True)
 if not(REPO/_RELATIVE_RUNTIME/'packaging_runtime.py').is_file():raise RuntimeError('TEST_ONLY_PUBLIC_RUNTIME_MISSING')
RUNTIME=REPO/'00_lab_infrastructure/gates/standalone_pdf_release/runtime'
HEAD='TEST_FIXTURE_ONLY_SOURCE_HASHES_ARE_AUTHORITATIVE'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def gitblob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def function_asts(raw):
 return {n.name:sha(ast.dump(n,include_attributes=False).encode())for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}

class Constructor:
 def __init__(self,root,*,existing_root=False,loader=None):
  self.root=Path(root).resolve();self.root.mkdir(exist_ok=existing_root)
  os.environ['VIRIDIS_CORE_ROOT']=str(self.root)
  raw=(RUNTIME/'packaging_runtime.py').read_bytes()
  self.runtime=types.ModuleType('_private_complete_packaging_source_fixture');self.runtime.__file__=str(RUNTIME/'packaging_runtime.py')
  if loader is not None:
   self.runtime.__dict__['__builtins__']=loader.fixture_builtins
   common=RUNTIME.parent/'common/stable_input_identity.py'
   loader.register_source(common,common.read_bytes())
  exec(compile(raw,self.runtime.__file__,'exec'),self.runtime.__dict__)
  self.original_raw=raw;self.remaps={};self.blobs={};self.profiles=[]
  spec=importlib.util.spec_from_file_location('_private_exact_history_reader',RUNTIME.parent/'common/runtime_history.py')
  self.history=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.history)
  self.marker=self.put('TEST_ONLY.json',{'fixture':'SYNTHETIC_NOT_AUTHORITY','authorizes':False})
 def put(self,name,value):
  path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True)
  raw=value if isinstance(value,bytes)else encoded(value);path.write_bytes(raw)
  return {'path':str(path),'sha256':sha(raw)}
 def remap(self,name,value):
  assert name in ALLOWED_RUNTIME_GLOBALS,name
  self.remaps[name]=copy.deepcopy(value);setattr(self.runtime,name,value)
 def origin(self,label,rows):
  number=800+len(self.profiles);oid=('%040x'%number);tree_sha=('%040x'%(number+100))
  pr=self.put(label+'/PR.json',{'fixture':'SIMULATED_PROVIDER_NOT_GITHUB_EVIDENCE','state':'MERGED','baseRefName':'main','number':number,'url':'https://github.com/jdhart81/viridis-canon/pull/'+str(number),'mergeCommit':{'oid':oid},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in sorted(self.runtime.REQUIRED_CHECKS)]})
  commit=self.put(label+'/COMMIT.json',{'fixture':'SIMULATED_PROVIDER_NOT_GITHUB_EVIDENCE','sha':oid,'tree':{'sha':tree_sha}})
  tree=self.put(label+'/TREE.json',{'fixture':'SIMULATED_PROVIDER_NOT_GITHUB_EVIDENCE','sha':tree_sha,'truncated':False,'tree':[{'path':r['git_path'],'type':'blob','mode':'100644','sha':gitblob(Path(r['path']).read_bytes())}for r in rows]})
  return {'pull_request':pr,'merge_commit':commit,'tree':tree},oid
 def module_rows(self,version):
  runtime=self.runtime;names=runtime.FROZEN_MODULE_NAMES if version<7 else runtime.FROZEN_FULL_MODULE_NAMES
  rows=[]
  for name in sorted(names):
   raw=self.history.historical_bytes('v%03d'%version,name);digest=sha(raw)
   key=(digest,name)
   if key not in self.blobs:self.blobs[key]=self.put('source-blobs/'+digest+'/'+name,raw)
   rows.append({'name':name,**self.blobs[key],'git_path':'00_lab_infrastructure/gates/standalone_pdf_release/future_runtime_v%03d/'%version+name})
  return rows
 def predecessors(self):
  m=self.runtime
  if 'LEGACY_CLOSURE'not in self.remaps:self.remap('LEGACY_CLOSURE',self.marker)
  self.remap('HISTORICAL_PUBLISHER',self.put('historical-publisher/publish_dated_bundles.py',(REPO/'00_lab_infrastructure/gates/production_snapshots/phase7-20261007-decoupled-policy/after/_ZENODO_DEPOSITS/publish_dated_bundles.py').read_bytes()))
  if 'DATA_ALIAS_OBSERVATION'not in self.remaps:self.remap('DATA_ALIAS_OBSERVATION',self.marker)
  if 'PLATFORM_TIMEZONE_OBSERVATION'not in self.remaps:self.remap('PLATFORM_TIMEZONE_OBSERVATION',self.marker)
  prior={}
  for version in range(1,12):
   label='metadata/lineage-%02d'%version;rows=self.module_rows(version);origin,oid=self.origin(label,rows)
   review={'standard':'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-'+str(version),'status':'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS','reviewer':'TEST ONLY simulated source-review provider; not an independent review','legacy_closure':m.LEGACY_CLOSURE,'source_hashes':{r['name']:r['sha256']for r in rows},'review_scope':'SOURCE_ONLY','actual_live_runtime_admission':False,'actual_seven_record_admission':'PENDING_POST_INSTALL_FRESH_READBACK'}
   if version==6:review.update(scientific_admission_changed=False,historical_sources_changed=False)
   if version>=7:review.update(m.SOURCE_REVIEW_CHANGE_FLAGS)
   review_binding=self.put(label+'/SOURCE_REVIEW.json',review)
   common={'source_origin':origin,'source_review':review_binding,'user_authority':self.marker,'access_registry':self.marker,'installed_at_utc':'2020-01-01T00:00:00Z','transient_rehydration':m.TRANSIENT_REHYDRATION_POLICY,'data_alias_observation':m.DATA_ALIAS_OBSERVATION,'platform_timezone_observation':m.PLATFORM_TIMEZONE_OBSERVATION}
   if version>=2:common['predecessor_installation']=prior['v001'] if version==2 else copy.deepcopy(prior)
   profile=self.put(label+'/PROFILE.json',{'standard':'VRS-STANDALONE-PDF-PACKAGING-PROFILE-'+str(version),'canonical_root':str(self.root),'modules':rows,'legacy_closure':m.LEGACY_CLOSURE,**common})
   plan=self.put(label+'/PLAN.json',{'standard':'VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-'+str(version),'source_modules':rows,'root_review':self.marker,**common})
   installer=next(row for row in rows if row['name']=='install_packaging_runtime.py')
   nomination=self.put(label+'/NOMINATION.json',{'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-'+str(version),'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING','profile':profile,'merged_source_commit':oid,'root_review_receipt':self.marker,'installer_source':{k:installer[k]for k in('path','sha256')}})
   installation={'profile':profile,'nomination':nomination,'plan':plan}
   if version==1:
    for field,value in [('PREDECESSOR_PROFILE',profile),('PREDECESSOR_NOMINATION',nomination),('PREDECESSOR_PLAN',plan)]:self.remap(field,value)
   else:
    for suffix,value in [('PROFILE',profile),('NOMINATION',nomination),('PLAN',plan)]:self.remap('V%03d_'%version+suffix,value)
   self.remap('V%03d_INSTALLATION'%version,installation);prior['v%03d'%version]=installation
   self.profiles.append({'version':version,'source_rows':len(rows),'source_origin':origin,'profile':profile,'plan':plan,'nomination':nomination})
  self.remap('PREDECESSOR_INSTALLATION',copy.deepcopy(prior))
  result=m.predecessor_installation(self.root)
  assert result['actual_runtime_admission']is False and result['certifies']is False
  return {'status':'TEST_ONLY_ALL11_GENUINE_PREDECESSOR_VALIDATOR_BODIES_EXECUTED','lineage_entries':11,'source_rows':sum(p['source_rows']for p in self.profiles),'unique_source_blobs':len(self.blobs),'full_version_tree_copies':0,'actual_runtime_admission':False,'certifies':False}
 def probes(self):
  m=self.runtime;results=[]
  row=self.profiles[-1];profile=json.loads(Path(row['profile']['path']).read_bytes());source=Path(profile['modules'][0]['path']);before=source.read_bytes();source.write_bytes(before+b'\n# source drift negative\n')
  try:
   try:m.predecessor_installation(self.root)
   except ValueError as e:results.append({'probe':'historical_source_drift','result':'HOLD','reason':str(e)})
   else:raise AssertionError('source drift admitted')
  finally:source.write_bytes(before)
  origin=copy.deepcopy(row['source_origin']);pr=json.loads(Path(origin['pull_request']['path']).read_bytes());pr['state']='OPEN';origin['pull_request']=self.put('negatives/OPEN_PR.json',pr)
  try:m.source_proof(self.root,origin,profile['modules'])
  except ValueError as e:results.append({'probe':'provider_open_pr','result':'HOLD','reason':str(e)})
  else:raise AssertionError('provider open PR admitted')
  try:m.require_source_session(self.root,row['profile'])
  except ValueError as e:results.append({'probe':'unscoped_capability','result':'HOLD','reason':str(e)})
  else:raise AssertionError('unscoped capability admitted')
  return results

ALLOWED_RUNTIME_GLOBALS=frozenset({'LEGACY_CLOSURE','HISTORICAL_PUBLISHER','DATA_ALIAS_OBSERVATION','PLATFORM_TIMEZONE_OBSERVATION','PREDECESSOR_PROFILE','PREDECESSOR_NOMINATION','PREDECESSOR_PLAN','PREDECESSOR_INSTALLATION'}|{'V%03d_%s'%(v,f)for v in range(1,12)for f in('PROFILE','NOMINATION','PLAN','INSTALLATION')})

def main():
 start=time.monotonic();root=Path(sys.argv[1]);out=Path(sys.argv[2]);c=Constructor(root)
 result=c.predecessors();negatives=c.probes()
 report={'standard':'VRS-PRIVATE-W42-COMPLETE-PREDECESSOR-POC-1','fixture_only':True,'not_source_review_verdict':True,'candidate_head':HEAD,'original_runtime_sha256':sha(c.original_raw),'original_function_class_asts':function_asts(c.original_raw),'validator_bodies_modified':False,'declared_data_remap_allowlist':sorted(ALLOWED_RUNTIME_GLOBALS),'applied_data_remaps':c.remaps,'positive':result,'negatives':negatives,'seconds':time.monotonic()-start,'core_reads_execution_writes':0,'network_requests':0,'secrets_read':0,'contextvar_mints':0,'current_closure_or_validate_mocked':False,'module_aliases':0,'root':str(c.root)}
 out.write_bytes(encoded(report));print(json.dumps({'report':str(out),'sha256':sha(out.read_bytes()),'positive':result,'negative_count':len(negatives),'seconds':report['seconds']}))
if __name__=='__main__':main()
