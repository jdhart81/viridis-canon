"""Closed merged-source policy-version dispatch; fresh validation, never cached PASS."""
from __future__ import annotations
import builtins,hashlib,json,re,sys,types
from contextlib import contextmanager
from pathlib import Path
import methods_digest as d

STANDARD='VRS-PHASE7-POLICY-VERSIONS-1'
NAMES={'phase7_audit_policy.py','PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','methods_digest.py','publication_gate.py'}
CHECKS={'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}

class VersionHold(ValueError):pass

APPENDIX_HEADER='## First Methods Digest audit + catalog provenance decision — 2026-10-08'
APPENDIX_SHA256='a8732599e0aeadec82f6ab27871158b119bc3d96dc6131606b30df9dcf7ba370'
SIMPLIFICATION_HEADER='## SIMPLIFICATION — weekly push restored — 2026-10-07 (Justin directive; supersedes conflicting Phase 7 items)'
SIMPLIFICATION_SHA256='483fddbd90eb1782911db43de477c161d35214fd033061a83a87b9dec503652a'
DECOUPLING_HEADER='## Phase 7 Gate 3 resolution: decouple probes from witnesses — 2026-10-07 (evening)'
DECOUPLING_SHA256='ba56d7254744843b9e7512b61f0d80161cf33b366f076d516aa451ba21c8325a'
SUFFIX=b'\n---\n'

def _authority_section(raw,header):
 token=header.encode()
 if raw.count(token)!=1:raise ValueError('HOLD_UNIQUE_APPROVED_AUTHORITY_SECTION')
 start=raw.index(token);end=raw.find(b'\n## ',start+len(token))
 return start,len(raw)if end<0 else end

def normalize_authority_plan(raw):
 """Strip one boundary only after every new and old section byte pin passes."""
 if not isinstance(raw,bytes):raise ValueError('HOLD_AUTHORITY_PLAN_BYTES')
 token=APPENDIX_HEADER.encode()
 if token not in raw:return raw
 a,b=_authority_section(raw,APPENDIX_HEADER)
 if b!=len(raw):raise ValueError('HOLD_UNKNOWN_AUTHORITY_APPENDIX')
 appendix=raw[a:b]
 if hashlib.sha256(appendix).hexdigest()!=APPENDIX_SHA256:
  if not(appendix.endswith(SUFFIX)and hashlib.sha256(appendix[:-len(SUFFIX)]).hexdigest()==APPENDIX_SHA256):raise ValueError('HOLD_APPROVED_AUTHORITY_APPENDIX_BYTES')
 c,e=_authority_section(raw,SIMPLIFICATION_HEADER);d,f=_authority_section(raw,DECOUPLING_HEADER)
 if not(d<c<a):raise ValueError('HOLD_APPROVED_AUTHORITY_APPENDIX_ORDER')
 if hashlib.sha256(raw[d:f]).hexdigest()!=DECOUPLING_SHA256:raise ValueError('HOLD_OLD_DECOUPLING_SCIENTIFIC_BYTES')
 section=raw[c:e]
 if hashlib.sha256(section).hexdigest()==SIMPLIFICATION_SHA256:return raw
 if not(section.endswith(SUFFIX)and hashlib.sha256(section[:-len(SUFFIX)]).hexdigest()==SIMPLIFICATION_SHA256):raise ValueError('HOLD_OLD_MINIMAL_SCIENTIFIC_BYTES')
 return raw[:e-len(SUFFIX)]+raw[e:]

def authority_plan_view(path,reader):
 return normalize_authority_plan(reader(Path(path)))

def authority_framing_proof(path,reader):
 path=Path(path);raw=reader(path);view=normalize_authority_plan(raw)
 return {'standard':'VRS_PHASE7_EXACT_APPROVED_AUTHORITY_FRAMING_1','path':str(path),'actual_sha256':hashlib.sha256(raw).hexdigest(),'view_sha256':hashlib.sha256(view).hexdigest(),'removed_bytes':len(raw)-len(view),'only_exact_terminal_markdown_delimiter':len(raw)-len(view)in(0,len(SUFFIX)),'approved_appendix_sha256':APPENDIX_SHA256,'old_scientific_section_sha256':SIMPLIFICATION_SHA256,'certifies':False,'new_review_fabricated':False,'writes':0}

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

@contextmanager
def _exact_authority_framing(module,root):
 path=Path(root).resolve(strict=True)/'reports/verification-coverage/GAME_PLAN.md'
 if module.d is d:raise VersionHold('framing requires isolated exact archival reader')
 original=module.d.read_regular;actual=original(path);view=normalize_authority_plan(actual)
 def framed(value):
  if Path(value)==path:
   fresh=original(path)
   if fresh!=actual:raise VersionHold('authority bytes changed during archival framing')
   return view
  return original(value)
 module.d.read_regular=framed
 try:yield
 finally:
  changed=module.d.read_regular is not framed
  module.d.read_regular=original
  if changed:raise VersionHold('archival framing reader identity changed')
  if original(path)!=actual:raise VersionHold('authority bytes changed before archival return')

def require_note_publication_bound(note,root,authority,current_module):
 module=implementation_for_note(note,root,current_module)
 if module is current_module:return None
 with _exact_authority_framing(module,root):
  result=module.require_note_publication_bound(note,root,authority)
 _finish(module._phase7_version_source_inputs);return result

def prepare_publication_binding(note,root,authority,current_module,at_utc=None):
 module=implementation_for_note(note,root,current_module)
 if module is current_module:return None
 with _exact_authority_framing(module,root):
  result=module.prepare_publication_binding(note,root,authority,at_utc=at_utc)
 _finish(module._phase7_version_source_inputs);return result


# Additive current-nightly scope route. Every historical helper above and its
# genuine archived source identity remain untouched. Generic selection never
# creates a row in the historical56 authority population.
_require_note_publication_bound_historical = require_note_publication_bound
_prepare_publication_binding_historical = prepare_publication_binding

def _nightly_scope_implementation(note,root):
 note=Path(note);root=Path(root).resolve(strict=True)
 if not note.is_relative_to(root):raise VersionHold('nightly note outside canonical root')
 rule=json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'))
 if rule.get('standard')!='VRS-NIGHTLY-MINIMAL-EXACT-SCOPE-RULE-1':return None
 import nightly_minimal_policy as nightly
 seen={};catalog=current_catalog(root,seen)
 ledger=json.loads(d.read_regular(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))
 _,raw=_read(root,ledger['enforcement_activation'],seen);activation=json.loads(raw)
 _,raw=_read(root,activation['authorized_runtime_update'],seen);runtime=json.loads(raw)
 path='RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_minimal_policy.py'
 rows=[r for r in runtime['additional_modules']if r.get('path')==path]
 if len(rows)!=1 or rows[0].get('sha256')!=rule.get('execution_consumer_sha256') or nightly.source_sha()!=rows[0]['sha256'] or Path(nightly.__file__).resolve(strict=True)!=root/path:raise VersionHold('exact nominated current nightly consumer required')
 _read(root,{'path':path,'sha256':rows[0]['sha256']},seen);_finish(seen)
 return nightly

def require_note_publication_bound(note,root,authority,current_module):
 module=_nightly_scope_implementation(note,root)
 if module is not None:return module.require_note_publication_bound(note,root,authority)
 return _require_note_publication_bound_historical(note,root,authority,current_module)

def prepare_publication_binding(note,root,authority,current_module,at_utc=None):
 module=_nightly_scope_implementation(note,root)
 if module is not None:return module.prepare_publication_binding(note,root,authority,at_utc=at_utc)
 return _prepare_publication_binding_historical(note,root,authority,current_module,at_utc)


# Exact separately approved comparison rule; historical scientific view stays.
_normalize_authority_pre_own_record = normalize_authority_plan
OWN_RECORD_HEADER='## Own-record comparison principle (ends Zenodo field stops) — 2026-10-08 (evening)'
OWN_RECORD_SECTION_SHA256='0073d050290065b1a661f6edc1472005c21f44f5eb2196aa03179d51daa35864'

def normalize_authority_plan(raw):
 if not isinstance(raw,bytes):raise ValueError('HOLD_AUTHORITY_PLAN_BYTES')
 token=OWN_RECORD_HEADER.encode()
 if token not in raw:return _normalize_authority_pre_own_record(raw)
 a,b=_authority_section(raw,OWN_RECORD_HEADER)
 if b!=len(raw)or hashlib.sha256(raw[a:b]).hexdigest()!=OWN_RECORD_SECTION_SHA256:raise ValueError('HOLD_EXACT_APPROVED_OWN_RECORD_AUTHORITY')
 c,e=_authority_section(raw,APPENDIX_HEADER)
 if not(c<a)or e!=a-1:raise ValueError('HOLD_APPROVED_OWN_RECORD_AUTHORITY_ORDER')
 # Keep the entire earlier section plus its exact delimiter. The unchanged
 # old parser rechecks catalog/decoupling/minimal byte pins in this view.
 if raw[a-6:a]!=b'\n---\n\n':raise ValueError('HOLD_EXACT_OWN_RECORD_BOUNDARY')
 return _normalize_authority_pre_own_record(raw[:a-1])


# Exact approved restatement: only the historical authority framing view changes.
_normalize_authority_pre_prior_processing = normalize_authority_plan
PRIOR_CONTENT_HEADER='## Prior-record rule narrowed to content we control — 2026-10-09'
PRIOR_CONTENT_SECTION_SHA256='43b52d2f91d41bfbe3fba1294203a3c725cf4fd6064e037b833888aa82d1c080'

def normalize_authority_plan(raw):
 if not isinstance(raw,bytes):raise ValueError('HOLD_AUTHORITY_PLAN_BYTES')
 token=PRIOR_CONTENT_HEADER.encode()
 if token not in raw:return _normalize_authority_pre_prior_processing(raw)
 a,b=_authority_section(raw,PRIOR_CONTENT_HEADER)
 if b!=len(raw)or hashlib.sha256(raw[a:b]).hexdigest()!=PRIOR_CONTENT_SECTION_SHA256:raise ValueError('HOLD_EXACT_APPROVED_PRIOR_CONTENT_AUTHORITY')
 c,e=_authority_section(raw,OWN_RECORD_HEADER)
 if not(c<a)or e!=a-1 or raw[a-6:a]!=b'\n---\n\n':raise ValueError('HOLD_PRIOR_CONTENT_AUTHORITY_ORDER')
 return _normalize_authority_pre_prior_processing(raw[:a-6])
