"""Closed merged-source policy-version dispatch; fresh validation, never cached PASS."""
from __future__ import annotations
import builtins,hashlib,json,re,sys,types
from pathlib import Path
import methods_digest as d

STANDARD='VRS-PHASE7-POLICY-VERSIONS-1'
NAMES={'phase7_audit_policy.py','PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','methods_digest.py','publication_gate.py'}
CHECKS={'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}

class VersionHold(ValueError):pass

def _read(root,v,seen):
 if not isinstance(v,dict)or set(v)!={'path','sha256'}:raise VersionHold('closed version source binding required')
 p,b=d.bound_file(root,v);h=d.digest(b)
 if str(p)in seen and seen[str(p)]!=h:raise VersionHold('version source changed during dispatch')
 seen[str(p)]=h;return p,b

def _finish(seen):
 for p,h in seen.items():
  if d.digest(d.read_regular(p))!=h:raise VersionHold('version source changed before return')

def current_catalog(root,seen):
 root=Path(root).resolve(strict=True);ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_raw=d.read_regular(ledger_path);seen[str(ledger_path)]=d.digest(ledger_raw);ledger=json.loads(ledger_raw)
 activation=ledger.get('enforcement_activation');_,raw=_read(root,activation,seen);wrapper=json.loads(raw)
 _,raw=_read(root,wrapper.get('authorized_runtime_update'),seen);runtime=json.loads(raw)
 if runtime.get('standard')!='VRS-PHASE7-AUTHORIZED-RUNTIME-UPDATE-1'or runtime.get('status')!='INSTALLED_HASH_READBACK_PASS'or runtime.get('profile')!='PHASE7_SCOPED_POLICY'or runtime.get('tree_root')!=str(root):raise VersionHold('approved installed policy source closure required')
 from phase7_runtime_update import validate
 _,original_raw=_read(root,runtime.get('original_activation'),seen);validated=validate(root,ledger,json.loads(original_raw))
 if validated.get('profile')!='PHASE7_SCOPED_POLICY'or validated.get('binding')!=wrapper.get('authorized_runtime_update'):raise VersionHold('fresh installed helper did not validate nominated policy runtime')
 _,raw=_read(root,runtime.get('policy_version_catalog'),seen);catalog=json.loads(raw)
 if (set(catalog)!={'standard','status','tree_root','versions'}or catalog['standard']!=STANDARD or catalog['status']!='MERGED_SOURCE_CATALOG'or catalog['tree_root']!=str(root)or not isinstance(catalog['versions'],list)or not catalog['versions']):raise VersionHold('closed current runtime-bound policy catalog required')
 return catalog

def _prove(root,entry,seen):
 if not isinstance(entry,dict)or set(entry)!={'execution_consumer_sha256','files','pull_request_readback'}or re.fullmatch('[0-9a-f]{64}',str(entry['execution_consumer_sha256']))is None:raise VersionHold('closed exact version entry required')
 if not isinstance(entry['files'],list)or len(entry['files'])!=len(NAMES):raise VersionHold('full frozen deterministic helper set required')
 sources={};names=[];base=None
 for row in entry['files']:
  if not isinstance(row,dict)or set(row)!={'name','binding','git_path'}or row['name']not in NAMES:raise VersionHold('closed approved version file required')
  name=row['name'];names.append(name);p,raw=_read(root,row['binding'],seen)
  if p.name!=name or p.parent.name!=entry['execution_consumer_sha256']or p.parent.parent.name!='policy_versions':raise VersionHold('version file outside exact hash directory')
  if base is None:base=p.parent
  if p.parent!=base or row['git_path']!='00_lab_infrastructure/gates/policy_versions/'+entry['execution_consumer_sha256']+'/'+name:raise VersionHold('version files must share own merged hash directory')
  sources[name]=(p,raw,row['git_path'])
 if len(set(names))!=len(NAMES)or set(names)!=NAMES:raise VersionHold('duplicate or missing version helper')
 if d.digest(sources['phase7_audit_policy.py'][1])!=entry['execution_consumer_sha256']:raise VersionHold('policy implementation SHA differs')
 _,raw=_read(root,entry['pull_request_readback'],seen);pr=json.loads(raw)
 if pr.get('state')!='MERGED'or pr.get('baseRefName')!='main'or pr.get('url')!='https://github.com/jdhart81/viridis-canon/pull/'+str(pr.get('number'))or re.fullmatch('[0-9a-f]{40}',str(pr.get('mergeCommit',{}).get('oid')))is None:raise VersionHold('own merged policy-source PR required')
 checks=pr.get('statusCheckRollup')
 if (not isinstance(checks,list)or not CHECKS<={v.get('name')for v in checks if v.get('status')=='COMPLETED'and v.get('conclusion')=='SUCCESS'}or any(v.get('status')!='COMPLETED'or v.get('conclusion')not in {'SUCCESS','SKIPPED'}for v in checks)):raise VersionHold('policy-source repository checks are incomplete')
 rows=pr.get('files');mapping={v.get('path'):v for v in rows}if isinstance(rows,list)else{}
 if not mapping or len(mapping)!=len(rows):raise VersionHold('complete own merged blob readback required')
 for name,(p,raw,git_path)in sources.items():
  gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
  if mapping.get(git_path,{}).get('sha')!=gitsha:raise VersionHold('version source differs from own merged Git blob')
 # The pinned data asset is part of the exact unchanged implementation bytes.
 text=sources['phase7_audit_policy.py'][1].decode()
 pins=re.findall(r"^CONTRACT_SHA='([0-9a-f]{64})'$",text,re.M)
 if pins!=[d.digest(sources['PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json'][1])]:raise VersionHold('version implementation/contract pair differs')
 return sources

def _load(sources,version):
 modules={};original_import=builtins.__import__
 def own_import(name,globals=None,locals=None,fromlist=(),level=0):
  if level==0 and name in modules:return modules[name]
  return original_import(name,globals,locals,fromlist,level)
 # Load only exact reviewed source bytes already proved against the merged PR.
 # Current certificate_inspection, static gate and scoped_release are always
 # imported normally; their fresh verdicts are never replaced by old results.
 order=['methods_digest.py','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','publication_gate.py','phase7_audit_policy.py']
 for name in order:
  p,raw,_=sources[name];short=name[:-3];qualified='_viridis_policy_'+version+'_'+short
  module=types.ModuleType(qualified);module.__file__=str(p);module.__package__='';module.__builtins__={**vars(builtins),'__import__':own_import};sys.modules[qualified]=module
  exec(compile(raw,str(p),'exec'),module.__dict__);modules[short]=module
 return modules['phase7_audit_policy']

def implementation_for_note(note,root,current_module,*,catalog_consumer=current_catalog):
 """Return the exact old consumer only for an approved source-bound old receipt."""
 root=Path(root).resolve(strict=True);note=Path(note).resolve(strict=True)
 if not note.is_relative_to(root):raise VersionHold('note outside canonical root')
 rule=json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'));sha=rule.get('execution_consumer_sha256')
 if re.fullmatch('[0-9a-f]{64}',str(sha))is None:raise VersionHold('exact issued execution consumer SHA required')
 # The current default is already covered by the installed runtime/ordinary
 # consumer guard. This branch preserves its existing tests and behavior.
 if sha==d.sha(current_module.__file__):return current_module
 seen={};catalog=catalog_consumer(root,seen);rows=[v for v in catalog['versions']if v.get('execution_consumer_sha256')==sha]
 if len(rows)!=1 or len({v.get('execution_consumer_sha256')for v in catalog['versions']})!=len(catalog['versions']):raise VersionHold('unknown or ambiguous execution consumer version')
 all_sources={}
 for entry in catalog['versions']:all_sources[entry['execution_consumer_sha256']]=_prove(root,entry,seen)
 sources=all_sources[sha];module=_load(sources,sha);_finish(seen)
 module._phase7_version_source_inputs=dict(seen)
 return module

def require_note_publication_bound(note,root,authority,current_module):
 module=implementation_for_note(note,root,current_module)
 if module is current_module:return None
 result=module.require_note_publication_bound(note,root,authority)
 _finish(module._phase7_version_source_inputs);return result

def prepare_publication_binding(note,root,authority,current_module,at_utc=None):
 module=implementation_for_note(note,root,current_module)
 if module is current_module:return None
 result=module.prepare_publication_binding(note,root,authority,at_utc=at_utc)
 _finish(module._phase7_version_source_inputs);return result
