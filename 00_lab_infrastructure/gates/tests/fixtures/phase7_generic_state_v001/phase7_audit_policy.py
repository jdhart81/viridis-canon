"""Mechanical execution of Justin's exact approved Phase7 audit rules.

No verifier, issuer, proof search, transport, publication, or manufactured Claude
review is implemented. Admission reuses the current certificate inspector and
static/scoped consumers and binds fresh own-job supplemental observations.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt,hashlib,json,re,sys
from pathlib import Path
import methods_digest as d
from certificate_inspection import inspect_certificate
import scoped_release as scoped
import nonvacuity_tier0 as tier0
import probe_observations as probes
from phase7_claim_label_render import apply_review_labels,render_claim_table

AUTH_STANDARD='VRS_PHASE7_CLAUDE_AUDIT_RULE_EXECUTION_1'
RULE_STANDARD='VRS_PHASE7_RULE_EXECUTION_1'
BINDING_STANDARD='VRS-PHASE7-SCOPED-PUBLICATION-BINDING-1'
SECTION_HEADER='## Phase 7 — Claude audit of release packet v002 — 2026-10-07'
AUTHORITY_SOURCE='Justin approved actual named GAME_PLAN audit section; execution is mechanical rule application, no fabricated Claude model/review timestamp'
AUTHORITY_SHA='8e39f9aecc4139fea929b4f45bf2cf5d9c24679796c7f14fe268ed830982aff9'
AUTHORITY_REL='reports/verification-coverage/2026-10-07/phase7-approved-audit-execution-v001/authority/AUDIT_AUTHORITY.json'
PINS={'audit_section':'0b90da9172c726cef65de5905fb289b79ec2367d0117b012f8ad74b324441390','audited_packet_md':'e3853d805d5f92d7352224924e7da1dea07aa15bc388f93f971be12f50dd7ab5','audited_packet_json':'972525b8159a02e8a6cea22e77433c90362ee71f1ebecbed0d025d504709be54','audited_input_manifest':'9d82072fa33a3fee17f4f7458cd3b1a92ed4cec7ef35b8514fec1a1b49977585'}
CONTRACT_SHA='11b1cdee4022471d16fd667e9a62ad4960f6b0c3f9f60d9c8ce6017b8c7a880d'
RUN127_BASE_SHA='495ce25fbbc2bcc2749905f3b43f2ff9c6f92eb1b298371e23fe0c7bdd615e99'
SENTENCE147='This note does not depend on the product-form Intelligence Bound conjecture; its results are independent of premises PL and PD.'
RULE_FIELDS={'standard','status','run_id','authority','audited_release_manifest','source_base_tex','before_metadata','supplemental_manifest','supplemental_certificate','issued_at_utc','inputs','claim_reviews','draft_assessment','execution_consumer_sha256'}
BINDING_FIELDS={'standard','status','run_id','authority','policy_receipt','identity','issued_at_utc','execution_consumer_sha256'}

class PolicyHold(ValueError):pass

def _time(value):
 p=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
 if p.tzinfo is None:raise PolicyHold('UTC timestamp required')
 return p.astimezone(dt.timezone.utc)

def _binding(path):
 v=d.binding(path);return {k:v[k]for k in ('path','sha256')}

def _closed_binding(root,value):
 if not isinstance(value,dict)or set(value)!={'path','sha256'}:raise PolicyHold('closed path/hash authority binding required')
 return d.bound_file(root,value)

def _read_bound(root,value,snapshots):
 p,b=_closed_binding(root,value);h=d.digest(b)
 if str(p)in snapshots and snapshots[str(p)]!=h:raise PolicyHold('input changed during rule execution')
 snapshots[str(p)]=h;return p,b

def _snapshot_certificate(root,binding,inspector,snapshots,run_id):
 p,raw=_read_bound(root,binding,snapshots);cert=json.loads(raw)
 def visit(value):
  if isinstance(value,dict):
   if 'path'in value:_read_bound(root,{k:value[k]for k in('path','sha256')},snapshots)
   else:
    for child in value.values():visit(child)
 visit(cert.get('bindings'))
 seen=inspector(p,root)
 if seen.get('valid')is not True or seen.get('run_id')!=run_id or seen.get('sha256')!=d.digest(raw):raise PolicyHold('unchanged certificate consumer HOLD: '+run_id)
 if cert['bindings']['candidate_proof']['sha256']!=seen.get('candidate_sha256'):raise PolicyHold('certificate candidate inspection identity differs')
 return cert,seen

def _finish(snapshots):
 for path,h in snapshots.items():
  if d.digest(d.read_regular(path))!=h:raise PolicyHold('rule input changed before admission')

def require_audit_authority(root,binding):
 root=Path(root).resolve(strict=True);snapshots={};p,b=_read_bound(root,binding,snapshots)
 if p!=root/AUTHORITY_REL or d.digest(b)!=AUTHORITY_SHA:raise PolicyHold('not the exact approved rule authority')
 a=json.loads(b)
 if (set(a)!={'standard','status','tree_root','audit_section','audited_packet_md','audited_packet_json','audited_input_manifest','assembly_observed_at_utc','authority_source'}
  or a['standard']!=AUTH_STANDARD or a['status']!='APPROVED_RULE_AUTHORITY' or a['tree_root']!=str(root) or a['authority_source']!=AUTHORITY_SOURCE):raise PolicyHold('closed actual approved rule authority required')
 if _time(a['assembly_observed_at_utc'])>dt.datetime.now(dt.timezone.utc):raise PolicyHold('future rule authority')
 for key,pin in PINS.items():
  if a[key]['sha256']!=pin:raise PolicyHold('approved audit packet hash changed')
  _read_bound(root,a[key],snapshots)
 plan=d.read_regular(root/'reports/verification-coverage/GAME_PLAN.md');text=plan.decode()
 if text.count(SECTION_HEADER)!=1:raise PolicyHold('actual approved audit section ambiguous or missing')
 section=text[text.index(SECTION_HEADER):];end=section.find('\n## ',len(SECTION_HEADER))
 if end!=-1:section=section[:end]
 _,expected=_read_bound(root,a['audit_section'],snapshots)
 if section.encode()!=expected:
  if section.encode()!=expected+b'\n---\n':raise PolicyHold('current GAME_PLAN approved section differs')
  # Exact appended section delimiter only, authenticated by the new authority.
  # The original approved scientific/release-rule text remains byte-identical.
  require_minimal_authority(root,snapshots)
 packet=json.loads(_read_bound(root,a['audited_packet_json'],snapshots)[1]);rows=packet.get('rows')
 if not isinstance(rows,list)or len(rows)!=56 or len({x.get('run_id')for x in rows})!=56:raise PolicyHold('exact56 audited note identities required')
 # All audited bytes are checked. The historical packet is authority; neither a
 # caller's input list nor a copied READY status substitutes this capture.
 inventory=json.loads(_read_bound(root,a['audited_input_manifest'],snapshots)[1])
 files=inventory.get('files')
 if not isinstance(files,list)or len(files)!=inventory.get('file_count'):raise PolicyHold('audited input coverage incomplete')
 seen=set()
 for row in files:
  if not isinstance(row,dict)or set(row)!={'path','relative_path','sha256','bytes'}or row['path']in seen:raise PolicyHold('closed unique audited file inventory required')
  seen.add(row['path']);_,raw=_read_bound(root,{k:row[k]for k in('path','sha256')},snapshots)
  if len(raw)!=row['bytes']:raise PolicyHold('audited file size differs')
 _finish(snapshots)
 return {**a,'binding':binding,'audited_rows':rows,'input_bindings':snapshots}

MINIMAL_AUTHORITY_REL='reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/authority/AUTHORITY.json'
MINIMAL_AUTHORITY_SHA='83e41448f5c413e2bff63b27f448c0ce6684c35b50536d83cbce3bb3606cae4c'
MINIMAL_SECTIONS=(
 ('DECOUPLING_SECTION.md','## Phase 7 Gate 3 resolution: decouple probes from witnesses — 2026-10-07 (evening)','ba56d7254744843b9e7512b61f0d80161cf33b366f076d516aa451ba21c8325a'),
 ('SIMPLIFICATION_SECTION.md','## SIMPLIFICATION — weekly push restored — 2026-10-07 (Justin directive; supersedes conflicting Phase 7 items)','483fddbd90eb1782911db43de477c161d35214fd033061a83a87b9dec503652a'))

def require_minimal_authority(root,snapshots):
 """Exact actual appended authority; optional enrichment never grants admission."""
 path=Path(root)/MINIMAL_AUTHORITY_REL
 _,raw=_read_bound(root,{'path':str(path),'sha256':MINIMAL_AUTHORITY_SHA},snapshots);authority=json.loads(raw)
 if (authority.get('standard')!='VRS-PHASE7-APPROVED-DECOUPLING-1'or authority.get('approved_by')!='Justin'
  or authority.get('new_review_fabricated')is not False or authority.get('local_lean_execution')is not False):raise PolicyHold('actual approved minimal authority required')
 if _time(authority['captured_at_utc'])>dt.datetime.now(dt.timezone.utc):raise PolicyHold('future minimal authority')
 if authority.get('original_audit_section',{}).get('sha256')!=PINS['audit_section']:raise PolicyHold('minimal authority must retain exact prior audit')
 _read_bound(root,authority['original_audit_section'],snapshots)
 text=d.read_regular(Path(root)/'reports/verification-coverage/GAME_PLAN.md').decode()
 if authority['sections']!=[{'path':name,'sha256':pin}for name,header,pin in MINIMAL_SECTIONS]:raise PolicyHold('closed approved section set changed')
 for name,header,pin in MINIMAL_SECTIONS:
  _,section=_read_bound(root,{'path':str(path.parent/name),'sha256':pin},snapshots)
  if text.count(header)!=1:raise PolicyHold('actual minimal GAME_PLAN section absent or ambiguous')
  current=text[text.index(header):];end=current.find('\n## ',len(header))
  if end!=-1:current=current[:end]
  if current.encode()!=section:raise PolicyHold('actual minimal GAME_PLAN section changed')
 return authority

def minimal_claim_reviews(run_id,candidate_text,scope,main_cert_binding,main_inspection):
 """Print truthful optional evidence while retaining issuer run-level witnesses."""
 names=_names(main_inspection.get('certified_theorems'));witnesses=_names(main_inspection.get('nonvacuity'))
 if not witnesses:raise PolicyHold('issuer run-level nonvacuity contract is missing')
 from theorem_coverage import triviality
 declarations=triviality(candidate_text);reviews=[]
 for claim in scope:
  name=claim['lean_theorem'];_one(name,names)
  if name not in declarations:raise PolicyHold('missing source-bound certified claim')
  semantic='UNCLASSIFIED'if run_id=='Run-130'else'DEPTH_NOT_ASSESSED'
  if declarations[name]['classification']=='CERTIFIED_TRIVIAL':semantic='DEFINITIONAL'
  witness=claim.get('nonvacuity_obligation')
  if witness is not None:
   witness=_one(witness,witnesses)
   nv={'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':witness,'certificate':main_cert_binding}
  else:
   # The domain rule is optional enrichment. Unsupported domains stay honestly
   # undemonstrated; no background proof failure substitutes for certification.
   try:classification=tier0.assess_candidate(candidate_text,name)
   except ValueError:classification={'status':'UNRESOLVED'}
   if classification['status']=='NO_HYPOTHESES':
    domains=list(dict.fromkeys(x['type']for x in classification['domains']))or['Unit (closed proposition; no quantified parameters)']
    nv={'tier':'TIER0','status':'NO_HYPOTHESES','domains':domains}
   else:nv={'tier':'TIER1','status':'NOT_DEMONSTRATED'}
  reviews.append({'lean_theorem':name,'semantic_tier':semantic,'nonvacuity':nv})
 return reviews

def _names(value):
 if not isinstance(value,list):raise PolicyHold('explicit certified export list required')
 return [v['name']if isinstance(v,dict)else v for v in value]

def _one(name,names):
 matches=[v for v in names if isinstance(v,str)and(v==name or v.endswith('.'+name))]
 if len(matches)!=1:raise PolicyHold('missing/ambiguous certified export: '+str(name))
 return matches[0]

def _strip_binding_paths(value):
 if isinstance(value,dict):return {k:_strip_binding_paths(v)for k,v in value.items()if not(k=='path'and'sha256'in value)}
 if isinstance(value,list):return [_strip_binding_paths(v)for v in value]
 return value

def _supplemental(root,run_id,main_cert_binding,candidate_text,scope,manifest_binding,certificate_binding,inspector,snapshots):
 contracts_raw=d.read_regular(Path(__file__).parent/'PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json')
 if d.digest(contracts_raw)!=CONTRACT_SHA:raise PolicyHold('approved exact supplemental source contracts changed')
 contract=json.loads(contracts_raw)['runs'][run_id]
 _,mb=_read_bound(root,manifest_binding,snapshots);sm=json.loads(mb)
 if _strip_binding_paths(sm)!=_strip_binding_paths(contract['manifest']):raise PolicyHold('supplemental original context/premise/witness source contract differs')
 if sm['main_certificate']['sha256']!=main_cert_binding['sha256']or sm['run_id']!=run_id:raise PolicyHold('wrong supplemental main certificate or run')
 cert,inspection=_snapshot_certificate(root,certificate_binding,inspector,snapshots,run_id)
 cb=cert['bindings'];_,candidate=_read_bound(root,cb['candidate_proof'],snapshots);_,formal=_read_bound(root,cb['formal_statement'],snapshots)
 if d.digest(candidate)!=contract['candidate_sha256']or d.digest(formal)!=contract['formal_statement_sha256']:raise PolicyHold('supplemental witness/probe proof bytes differ from approved exact source')
 prefix=sm['original_source_prefix']
 original=candidate_text.encode()
 if prefix['binding']['sha256']!=d.digest(original)or prefix['byte_length']!=len(original)or not candidate.startswith(original):raise PolicyHold('supplemental candidate lacks exact unchanged main prefix')
 _,request_raw=_read_bound(root,cb['request'],snapshots);request=json.loads(request_raw)
 if d.digest(request_raw)!=contract['request_sha256']:raise PolicyHold('supplemental own request bytes differ from exact approved attempt')
 if (request.get('source_run')!=run_id or request.get('supplemental_only')is not True or request.get('issuer_output_must_not_replace_main_certificate')is not True
  or request.get('expected_theorem_names')!=contract['expected_theorem_names']or request.get('nonvacuity_obligations')!=contract['nonvacuity_obligations']
  or request.get('input_sha256',{}).get('SUPPLEMENTAL_MANIFEST.json')!=d.digest(mb)):raise PolicyHold('supplemental own request export or witness contract differs')
 for name in contract['expected_theorem_names']:_one(name,_names(inspection['certified_theorems']))
 for name in contract['nonvacuity_obligations']:_one(name,_names(inspection['nonvacuity']))
 _,cloud_raw=_read_bound(root,cb['independent_cloud_receipt'],snapshots);cloud=json.loads(cloud_raw);response=cloud.get('provider_response')
 if not isinstance(response,dict)or response.get('type')!='verification-ok'or response.get('project')!='viridis-lean-4.28':raise PolicyHold('supplemental own terminal receipt missing')
 if (not re.fullmatch(r'[0-9a-f]{8}-[0-9a-f-]{27}',str(response.get('requestId')))
  or any(response.get(k)for k in('recoveredFromDiskCache','diskCacheEvidence'))):raise PolicyHold('fresh own supplemental round trip required; disk-cache evidence forbidden')
 canonical=(json.dumps(response,sort_keys=True,separators=(',',':'))+'\n').encode()
 if cloud.get('provider_response_sha256')!=d.digest(canonical):raise PolicyHold('own provider response hash differs')
 from certificate_inspection import pipeline_modules
 _,issuer=pipeline_modules(Path(root))
 observed=issuer.assess_job_observation(response,request,d.digest(formal),d.digest(candidate))
 evidence=response.get('executionEvidence',{});delivery=evidence.get('delivery',{})
 if (observed.get('status')!='OBSERVATION_MATCH_PARTIAL' or delivery.get('mode')!='FRESH_EXECUTION'
  or delivery.get('servedForRequestId')!=response['requestId']or evidence.get('executionId')!=response['requestId']):raise PolicyHold('own fresh source-bound supplemental execution observation required')
 if cloud.get('request')!=cb['request']or cloud.get('candidate')!=cb['candidate_proof']or cloud.get('formal_statement')!=cb['formal_statement']:raise PolicyHold('own request/candidate/statement receipt identity differs')
 for name in contract['expected_theorem_names']+contract['nonvacuity_obligations']:_one(name,response.get('theoremNames'))
 labels=[v['probe']['print_label']for v in sm['claims']]
 observations=probes.extract_tags(response.get('output'),formal.decode(),candidate.decode(),labels)
 original_rows={v['theorem']:v for v in sm['claims']};reviews=[]
 from theorem_coverage import triviality
 from scoped_release import ambient_context
 declarations=triviality(candidate_text)
 for claim in scope:
  name=claim['lean_theorem'];row=original_rows[name];actual=declarations[name]
  if row['exact_signature_sha256']!=d.digest(actual['signature'].encode())or row['source_context']!=ambient_context(candidate_text,actual['line']):raise PolicyHold('full original signature or ambient premises differ')
  semantic=observations[row['probe']['print_label']]['observed_label'];witness=claim['nonvacuity_obligation']
  if witness is not None:
   if row.get('existing_main_certificate_witness')!=witness:raise PolicyHold('original explicit witness assignment changed')
   nv={'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':witness,'certificate':main_cert_binding}
  else:
   classified=tier0.assess_candidate(candidate_text,name)
   if classified['status']=='NO_HYPOTHESES':
    if row['tier']!='TIER0':raise PolicyHold('fresh Tier0 classification differs from approved premise inventory')
    domains=list(dict.fromkeys(x['type']for x in classified['domains']))or['Unit (closed proposition; no quantified parameters)']
    nv={'tier':'TIER0','status':'NO_HYPOTHESES','domains':domains}
   else:
    if row['tier']!='TIER1'or row.get('all_premises_in_witness')is not True:raise PolicyHold('all-premise witness obligation unresolved')
    target=row['witness_target'];_one(target,_names(inspection['nonvacuity']));_one(target,_names(inspection['certified_theorems']))
    nv={'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':target,'certificate':certificate_binding}
  reviews.append({'lean_theorem':name,'semantic_tier':semantic,'nonvacuity':nv})
 return reviews,{'request_id':response['requestId'],'provider_response_sha256':cloud['provider_response_sha256'],'observations':observations,'inspection':inspection,'certificate':cert}

def require_write_budget(root,method,at_utc):
 from phase7_mutation_baseline import require_events
 return d.require_write_budget(require_events(root,at_utc),method,at_utc,complete=True)

def _scope_derivative(current,audited,reviews,run_id):
 expected=deepcopy(audited)
 if run_id=='Run-127':expected=[v for v in expected if v['lean_theorem']=='positive_floor_sharp_two_point_counterexample']
 for row in expected:
  review=next(v for v in reviews if v['lean_theorem']==row['lean_theorem'])
  if review['semantic_tier']=='DEFINITIONAL'and row['evidence_class']=='FORMALLY_VERIFIED':row['evidence_class']='CERTIFIED_TRIVIAL'
 if current!=expected:raise PolicyHold('final claim scope/hypotheses/context/fidelity/witness differs from approved derivative')
 return expected

def run147_approved_base(prior):
 """Insert only the approved sentence in the first actual main abstract.

    The frozen historical remainder may contain its own quoted abstract; that
    text never becomes an active main-abstract selector or amendment target.
    """
 archive=b'\\section*{Claims excluded from formal scope}'
 if not isinstance(prior,bytes)or prior.count(archive)!=1:raise PolicyHold('Run147 exact historical archive boundary required')
 main=prior.split(archive,1)[0];begin=b'\\begin{abstract}';end=b'\n\\end{abstract}'
 if main.count(begin)!=1 or main.count(end)!=1 or main.index(begin)>=main.index(end):raise PolicyHold('Run147 unique actual main abstract required')
 position=main.index(end)
 return prior[:position]+b'\n'+SENTENCE147.encode()+b'\n'+prior[position:]

def _source_derivative(root,rule,row,reviews,snapshots):
 _,raw=_read_bound(root,rule['source_base_tex'],snapshots);run=row['run_id']
 audited_bind={k:row['evidence']['paper_tex'][k]for k in('path','sha256')}
 if run=='Run-127':
  if d.digest(raw)!=RUN127_BASE_SHA:raise PolicyHold('Run127 is not the exact approved nonproduct successor')
 elif run=='Run-147':
  _,old=_read_bound(root,audited_bind,snapshots)
  expected=run147_approved_base(old)
  # The audited source may contain a blank line after begin; only the approved
  # approved sentence is inserted. No title or other source byte can change.
  if raw!=expected:raise PolicyHold('Run147 exception is confined to the exact main abstract sentence')
 else:
  if rule['source_base_tex']!=audited_bind:raise PolicyHold('audited base manuscript differs')
 return raw,apply_review_labels(raw,reviews)

RENDERER_SHA='568dea0a81f4ceed859e33734bbbea85d54a25f14b12665a48c98b536a887986'
RENDERER_CACHE_SHA='d312006417a3eef3fca66a51db558b1853476cd9a8ed0479fe04ed351f8a9dc4'

def check_pdf_observation(observation,tex,pdf):
 fields={'source_tex_sha256','rendered_pdf_sha256','command','renderer_binary','cache_manifest','cache_file_count','cache_and_binary_exact_after','started_at_utc','ended_at_utc','returncode','network_resource_fetch_disabled','no_env_or_stdin_or_credentials_captured','local_lean_execution'}
 if not isinstance(observation,dict)or set(observation)!=fields:raise PolicyHold('closed actual final PDF observation required')
 command=observation['command'];binary=observation['renderer_binary']
 if (not isinstance(command,list)or len(command)!=6 or command[:3]!=['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs']
  or command[3]!='--outdir'or not isinstance(command[4],str)or command[5]!='paper.tex'
  or set(binary)!={'invoked_path','resolved_path','sha256'}or binary['invoked_path']!=command[0]or binary['sha256']!=RENDERER_SHA):raise PolicyHold('foreign PDF renderer or command')
 if (observation['source_tex_sha256']!=d.digest(tex)or observation['rendered_pdf_sha256']!=d.digest(pdf)
  or observation['returncode']!=0 or observation['cache_and_binary_exact_after']is not True
  or observation['network_resource_fetch_disabled']is not True or observation['no_env_or_stdin_or_credentials_captured']is not True
  or observation['local_lean_execution']is not False or observation['cache_manifest']['sha256']!=RENDERER_CACHE_SHA
  or observation['cache_file_count']!=556):raise PolicyHold('final PDF/source/cache observation mismatch')
 if _time(observation['started_at_utc'])>_time(observation['ended_at_utc'])or _time(observation['ended_at_utc'])>dt.datetime.now(dt.timezone.utc):raise PolicyHold('PDF observation time invalid')
 return {'status':'SOURCE_BOUND_RENDER_OBSERVATION_MATCH_NOT_SEMANTIC_VERIFICATION'}

def require_pdf_provenance(note,root,tex,pdf,snapshots):
 path=Path(note)/'render-observation/RENDERER_OBSERVATION.json';raw=d.read_regular(path);snapshots[str(path)]=d.digest(raw);observation=json.loads(raw)
 check_pdf_observation(observation,tex,pdf)
 render_path=Path(note)/'render-observation/paper.pdf';rendered=d.read_regular(render_path);snapshots[str(render_path)]=d.digest(rendered)
 if rendered!=pdf:raise PolicyHold('actual renderer PDF differs from public PDF')
 binary=Path('/opt/homebrew/bin/tectonic').resolve(strict=True)
 if str(binary)!=observation['renderer_binary']['resolved_path']or d.digest(d.read_regular(binary))!=RENDERER_SHA:raise PolicyHold('current pinned renderer bytes differ')
 snapshots[str(binary)]=RENDERER_SHA
 cache_binding={k:observation['cache_manifest'][k]for k in('path','sha256')};_,cache_raw=_read_bound(root,cache_binding,snapshots);cache=json.loads(cache_raw)
 if cache.get('schema')!='VRS-PHASE7-TECTONIC-CACHE-1'or len(cache.get('files',{}))!=556:raise PolicyHold('complete pinned cache inventory required')
 cache_root=Path(cache['cache_root']).resolve(strict=True)
 if not cache_root.is_relative_to(Path(root).resolve()):raise PolicyHold('renderer cache outside canonical root')
 actual=[str(f.relative_to(cache_root))for f in cache_root.rglob('*')if f.is_file()]
 if set(actual)!=set(cache['files']):raise PolicyHold('renderer cache has unlisted or missing assets')
 for name,h in cache['files'].items():
  d.safe_member(name);_read_bound(root,{'path':str(cache_root/name),'sha256':h},snapshots)
 return observation

def _identity(result,manifest):
 keys=('manifest_sha256','certificate','candidate','formal_statement','claim_map_sha256','statement_inventory_sha256','foundation_basis_sha256','uploads','metadata_binding','final_tex_sha256','final_pdf_sha256','statement_scope','foundation_basis','inv9_projection_sha256','archival_exclusion_review_required','fresh_full_inv9','fresh_scoped_inv9')
 return {**{k:result[k]for k in keys},'run_id':manifest['run_id']}

def _require_audited_base_archive(note,root,rule,audit_manifest,run,snapshots):
 # Every archived scientific attachment is recomputed from the immutable
 # approved parent, rather than trusting a self-rehashed public manifest.
 base=Path(audit_manifest['path']).parent.resolve(strict=True)
 files=[]
 for path in sorted(base.rglob('*')):
  if path.is_symlink():raise PolicyHold('audited base symlink refused')
  if path.is_file():
   b=d.read_regular(path);snapshots[str(path)]=d.digest(b);files.append((str(path.relative_to(base)),b))
 expected={'base':str(base),'members':d.member_inventory(files),'source_unchanged':True}
 manifest_raw=d.read_regular(note/'AUDITED_BASE_MANIFEST.json')
 if json.loads(manifest_raw)!=expected:raise PolicyHold('public audited base descriptor differs from exact audited input inventory')
 if d.read_regular(note/'AUDITED_BASE.zip')!=d.archive_bytes(files):raise PolicyHold('public audited base archive differs from exact approved original bytes')
 return dict(files)

def transformed_whole_paper_map(run_id,*,audit_manifest,original_map_binding,prior_tex_binding,
                                base_tex_binding,prior_tex,base_tex,final_tex,final_pdf_binding,
                                final_tex_binding,statement_scope,reviews):
 """Closed approved source transformation; all other scientific bytes stay fixed."""
 if run_id not in {'Run-127','Run-147'}:raise PolicyHold('no approved transformed-map rule for this Run')
 if apply_review_labels(base_tex,reviews)!=final_tex:raise PolicyHold('final transformed manuscript differs from exact label rendering')
 if d.digest(prior_tex)!=prior_tex_binding['sha256']or d.digest(base_tex)!=base_tex_binding['sha256']or d.digest(final_tex)!=final_tex_binding['sha256']:raise PolicyHold('transformed map source binding mismatch')
 text=final_tex.decode();prior=prior_tex.decode()
 if run_id=='Run-127':
  if d.digest(base_tex)!=RUN127_BASE_SHA:raise PolicyHold('not the exact approved Run127 narrowed source')
  import inv9_dependency_scope as dependency
  if [c['lean_theorem']for c in statement_scope]!=[dependency.TARGET]:raise PolicyHold('transformed Run127 map includes excluded theorem')
  regions=dependency.paper_regions(text,prior)
 else:
  if base_tex!=run147_approved_base(prior_tex):raise PolicyHold('Run147 transformed map exceeds exact abstract sentence')
  marker=r'\section*{Claims excluded from formal scope}'
  if text.count(marker)!=1:raise PolicyHold('Run147 closed historical region marker missing or duplicated')
  split=text.index(marker);parts=[text[:split],text[split:]];offset=0;regions=[]
  for label,part in zip(('EXACT_STATEMENTS_AND_STATUS_ONLY','UNCHANGED_UNCERTIFIED_HISTORICAL_REMAINDER'),parts):
   raw=part.encode();regions.append({'region':label,'byte_start':offset,'byte_end_exclusive':offset+len(raw),'sha256':d.digest(raw)});offset+=len(raw)
 return {'standard':'VRS-PHASE7-APPROVED-TRANSFORMED-WHOLE-PAPER-MAP-1','run_id':run_id,'audited_release_manifest':audit_manifest,
  'original_whole_paper_map':original_map_binding,'prior_tex':prior_tex_binding,'source_base_tex':base_tex_binding,
  'paper':final_tex_binding,'final_pdf':final_pdf_binding,'statement_scope':deepcopy(statement_scope),
  'whole_paper_regions':regions,'original_historical_claims_remain_uncertified':True,'certifies':False}

def expected_whole_paper_map(note,root,rule,audit_manifest,before_manifest,base,tex,pdf,reviews,snapshots):
 from phase7_claim_label_render import shift_whole_paper_map
 audit_base=Path(audit_manifest['path']).parent
 local_map=json.loads(d.read_regular(audit_base/before_manifest['claim_map']['filename']))
 name=local_map.get('whole_paper_map',{}).get('filename','claim_map.json')
 original=audit_base/name;original_raw=d.read_regular(original);snapshots[str(original)]=d.digest(original_raw)
 if rule['run_id']in {'Run-127','Run-147'}:
  prior_path=audit_base/'paper.tex';prior=d.read_regular(prior_path);snapshots[str(prior_path)]=d.digest(prior)
  return transformed_whole_paper_map(rule['run_id'],audit_manifest=audit_manifest,
   original_map_binding={'path':str(original),'sha256':d.digest(original_raw)},prior_tex_binding={'path':str(prior_path),'sha256':d.digest(prior)},
   base_tex_binding=rule['source_base_tex'],prior_tex=prior,base_tex=base,final_tex=tex,
   final_pdf_binding={'path':str(note/'paper.pdf'),'sha256':d.digest(pdf)},final_tex_binding={'path':str(note/'paper.tex'),'sha256':d.digest(tex)},
   statement_scope=json.loads(d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json'))['statement_scope'],reviews=reviews)
 expected=shift_whole_paper_map(json.loads(original_raw),base,tex,render_claim_table(reviews))
 expected['paper']={'path':str(note/'paper.tex'),'sha256':d.digest(tex)};expected['final_pdf']={'path':str(note/'paper.pdf'),'sha256':d.digest(pdf)}
 return expected

def evaluate_note(note,root,authority_binding,*,rule=None,inspector=inspect_certificate,assessor=None,_preparing=False):
 """Fresh rule evaluation; no file is written and no public claim is admitted."""
 root=Path(root).resolve(strict=True);note=Path(note).resolve(strict=True)
 if not note.is_relative_to(root):raise PolicyHold('note outside mirror/certification root')
 authority=require_audit_authority(root,authority_binding);snapshots=dict(authority['input_bindings'])
 manifest_path=note/'SCOPED_RELEASE_MANIFEST.json';mp=d.read_regular(manifest_path);snapshots[str(manifest_path)]=d.digest(mp);manifest=json.loads(mp)
 run=manifest.get('run_id');rows=[v for v in authority['audited_rows']if v['run_id']==run]
 if len(rows)!=1:raise PolicyHold('note absent from exact approved audit population')
 row=rows[0]
 if rule is None:rule=json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'))
 if (not isinstance(rule,dict)or set(rule)!=RULE_FIELDS or rule['standard']!=RULE_STANDARD or rule['status']!='APPLIED_APPROVED_RULES'
  or rule['run_id']!=run or rule['authority']!=authority_binding or rule['execution_consumer_sha256']!=d.sha(__file__)
  or _time(rule['issued_at_utc'])>dt.datetime.now(dt.timezone.utc)):raise PolicyHold('closed current mechanical rule receipt required')
 audit_manifest={k:row['evidence']['release_manifest'][k]for k in('path','sha256')}
 if rule['audited_release_manifest']!=audit_manifest:raise PolicyHold('wrong audited parent manifest')
 _,before_manifest_raw=_read_bound(root,audit_manifest,snapshots);before_manifest=json.loads(before_manifest_raw)
 if any(manifest.get(k)!=before_manifest.get(k)for k in('certificate','candidate','formal_statement','run_id','scope','standard')):raise PolicyHold('main proof/certificate authority changed')
 cert,main_inspection=_snapshot_certificate(root,manifest['certificate'],inspector,snapshots,run)
 _,candidate_raw=_read_bound(root,manifest['candidate'],snapshots);_,formal_raw=_read_bound(root,manifest['formal_statement'],snapshots)
 minimal=rule['supplemental_manifest']is None and rule['supplemental_certificate']is None
 if (rule['supplemental_manifest']is None)!=(rule['supplemental_certificate']is None):raise PolicyHold('optional supplemental family must be complete or absent')
 if minimal:
  require_minimal_authority(root,snapshots)
  reviews=minimal_claim_reviews(run,candidate_raw.decode(),manifest['statement_scope'],manifest['certificate'],main_inspection)
  supplemental={'observations':{},'certificate':None}
 else:reviews,supplemental=_supplemental(root,run,manifest['certificate'],candidate_raw.decode(),manifest['statement_scope'],rule['supplemental_manifest'],rule['supplemental_certificate'],inspector,snapshots)
 if not _preparing and reviews!=rule['claim_reviews']:raise PolicyHold('labels or witness assignments differ from fresh own-job observations')
 _scope_derivative(manifest['statement_scope'],before_manifest['statement_scope'],reviews,run)
 for claim in manifest['statement_scope']:
  if claim['nonvacuity_obligation']is not None:_one(claim['nonvacuity_obligation'],_names(main_inspection['nonvacuity']))
 base,expected_tex=_source_derivative(root,rule,row,reviews,snapshots)
 tex=d.read_regular(note/'paper.tex');pdf=d.read_regular(note/'paper.pdf')
 snapshots[str(note/'paper.tex')]=d.digest(tex);snapshots[str(note/'paper.pdf')]=d.digest(pdf)
 if tex!=expected_tex:raise PolicyHold('unapproved final scientific sentence, theorem, hypothesis, or source change')
 if not pdf.startswith(b'%PDF-')or manifest['final_pdf_sha256']!=d.digest(pdf):raise PolicyHold('final PDF bytes missing or stale')
 if manifest['final_tex_sha256']!=d.digest(tex):raise PolicyHold('final TeX binding stale')
 require_pdf_provenance(note,root,tex,pdf,snapshots)
 # Every original display/source attachment remains exact. New operational
 # diagnostics may exist outside the public upload inventory; they grant no
 # semantic or publication authority.
 excluded={'paper.tex','paper.pdf','metadata.json','SCOPED_CLAIM_MAP.json','SCOPED_STATEMENT_INVENTORY.json','claim_map.json','INV9_MAIN_SCOPE_PROJECTION.json','SCOPE_EVIDENCE.zip'}
 for upload in before_manifest['uploads']:
  if upload['filename']not in excluded:
   raw=d.read_regular(note/upload['filename']);snapshots[str(note/upload['filename'])]=d.digest(raw)
   if d.digest(raw)!=upload['sha256']:raise PolicyHold('frozen proof/context/display upload changed')
 # Existing metadata title/keywords and all other fields are preserved. Only
 # the approved closed description/abstract helper may produce final text.
 expected_before={k:row['evidence']['metadata_before'][k]for k in('path','sha256')}
 if rule['before_metadata']!=expected_before:raise PolicyHold('metadata source differs from audited original')
 _,before_raw=_read_bound(root,expected_before,snapshots);before=json.loads(before_raw);before=before.get('metadata',before)
 basis_raw=d.read_regular(note/manifest['foundation_basis']['filename']);snapshots[str(note/manifest['foundation_basis']['filename'])]=d.digest(basis_raw);basis=json.loads(basis_raw)
 _,oldbasis_raw=_read_bound(root,{k:row['evidence']['basis'][k]for k in('path','sha256')},snapshots)
 if basis_raw!=oldbasis_raw:raise PolicyHold('original declared foundation basis changed')
 from publication_gate import scoped_metadata_proposal
 expected_metadata=scoped_metadata_proposal(before,{'statement_scope':manifest['statement_scope'],'foundation_basis':basis['foundation_basis']})
 metadata_raw=d.read_regular(note/'metadata.json');snapshots[str(note/'metadata.json')]=d.digest(metadata_raw);metadata=json.loads(metadata_raw)
 if metadata!=expected_metadata:raise PolicyHold('final metadata exceeds closed approved scientific scope or changes existing fields')
 # The whole paper's actual claims and their offset map must be the audited
 # map shifted by exactly the mechanically recomputed classification table.
 expected_map=expected_whole_paper_map(note,root,rule,audit_manifest,before_manifest,base,tex,pdf,reviews,snapshots)
 if json.loads(d.read_regular(note/'claim_map.json'))!=expected_map:raise PolicyHold('whole-paper map or original uncertified-claim coverage differs')
 lookup={v['lean_theorem']:v for v in reviews}
 def claim_consumer(**kwargs):
  name=kwargs['claim']['lean_theorem']
  if kwargs['candidate_text'].encode()!=candidate_raw or kwargs['formal_text'].encode()!=formal_raw:raise PolicyHold('source changed before fresh scoped evaluation')
  return deepcopy(lookup[name])
 premise_consumer=None
 if run=='Run-127':
  import inv9_dependency_scope as dependency
  prior_path=Path(audit_manifest['path']).parent/'paper.tex';prior=d.read_regular(prior_path).decode();snapshots[str(prior_path)]=d.sha(prior_path)
  def premise_consumer(**kwargs):
   receipt=dependency.make_receipt(candidate_raw.decode(),formal_raw.decode(),kwargs['paper_text'],prior,manifest['statement_scope'])
   return dependency.evaluate(receipt,candidate=candidate_raw.decode(),formal=formal_raw.decode(),paper=kwargs['paper_text'],prior_tex=prior,statement_scope=manifest['statement_scope'],certificate_sha256=manifest['certificate']['sha256'])
 if assessor is None:assessor=scoped.assess
 result=assessor(note,root,inspector=inspector,claim_rule_consumer=claim_consumer,premise_rule_consumer=premise_consumer)
 if result.get('status')!='DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND':raise PolicyHold('fresh unchanged/scoped consumers HOLD: '+str(result.get('reasons')))
 identity=_identity(result,manifest)
 if not _preparing and rule['draft_assessment']!=identity:raise PolicyHold('recorded rule execution identity differs from fresh assessment')
 # Bind the complete own supplemental family in public evidence bytes; a mere
 # local certificate reference cannot certify an undelivered witness.
 uploads={v['filename']:v for v in manifest['uploads']}
 supplemental_names={'SUPPLEMENTAL_WITNESS_CERTIFICATE.json','SUPPLEMENTAL_WITNESS_EVIDENCE.zip','SUPPLEMENTAL_WITNESS_MANIFEST.json'}
 if not minimal:
  sb,scraw=_read_bound(root,rule['supplemental_certificate'],snapshots)
  if (uploads.get('SUPPLEMENTAL_WITNESS_CERTIFICATE.json',{}).get('sha256')!=d.digest(scraw)
   or d.read_regular(note/'SUPPLEMENTAL_WITNESS_CERTIFICATE.json')!=scraw):raise PolicyHold('exact supplemental certificate public upload missing')
  family=[('LEAN_ZERO_SORRY_CERTIFICATE.json',scraw)];bindings=supplemental['certificate']['bindings'];required={'candidate_proof','formal_statement','request','independent_cloud_receipt','sealed_statement_contract','statement_alignment_receipt'}
  for key in sorted(required):
   p,b=_read_bound(root,bindings[key],snapshots);family.append((key+'/'+p.name,b))
  sealed={'SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json','SEALED_paper.pdf','SEALED_paper.tex'}
  if set(bindings['sealed_paper_inputs'])!=sealed:raise PolicyHold('supplemental sealed input set differs')
  for key in sorted(sealed):_,b=_read_bound(root,bindings['sealed_paper_inputs'][key],snapshots);family.append(('sealed_paper_inputs/'+key,b))
  descriptor={'standard':'VRS-SUPPLEMENTAL-EVIDENCE-FAMILY-1','certificate':rule['supplemental_certificate'],'run_id':run,'members':d.member_inventory(family),'certifies':False,'diagnostics_capture_included':False}
  family.append(('SUPPLEMENTAL_EVIDENCE_MANIFEST.json',d.raw_json(descriptor)));expected_archive=d.archive_bytes(family)
  if d.read_regular(note/'SUPPLEMENTAL_WITNESS_EVIDENCE.zip')!=expected_archive or uploads.get('SUPPLEMENTAL_WITNESS_EVIDENCE.zip',{}).get('sha256')!=d.digest(expected_archive):raise PolicyHold('complete supplemental witness evidence public archive differs')
  if json.loads(d.read_regular(note/'SUPPLEMENTAL_WITNESS_MANIFEST.json'))!=descriptor:raise PolicyHold('supplemental archive descriptor differs')
 required_uploads={v['filename']for v in before_manifest['uploads']}|{'metadata.json','CLAIM_CLASSIFICATIONS.json','AUDITED_BASE.zip','AUDITED_BASE_MANIFEST.json'}|(supplemental_names if not minimal else set())
 if set(uploads)!=required_uploads or len(uploads)!=len(manifest['uploads']):raise PolicyHold('unreviewed extra or missing public file')
 classifications_raw=d.read_regular(note/'CLAIM_CLASSIFICATIONS.json');classifications=json.loads(classifications_raw)
 expected_classifications={'run_id':run,'claim_reviews':reviews,'status':'PROPOSAL_NOT_RULE_EXECUTION_RECEIPT','authority':authority_binding,'source_statements_unchanged':True,'certifies':False}
 if classifications!=expected_classifications:raise PolicyHold('public classification labels differ from actual rule execution')
 base_files=_require_audited_base_archive(note,root,rule,audit_manifest,run,snapshots)
 # Closed mechanical JSON derivatives: a rehashed extra English claim must
 # not enter an auxiliary public map or the nested scope evidence archive.
 mapping=json.loads(base_files[before_manifest['claim_map']['filename']]);inventory=json.loads(base_files[before_manifest['statement_inventory']['filename']])
 if run=='Run-127':
  mapping['claims']=[v for v in mapping['claims']if v['lean_theorem']=='positive_floor_sharp_two_point_counterexample']
  inventory['declarations']=[v for v in inventory['declarations']if v['lean_theorem']=='positive_floor_sharp_two_point_counterexample']
 for rows_to_update in(mapping['claims'],inventory['declarations']):
  for claim in rows_to_update:
   if lookup[claim['lean_theorem']]['semantic_tier']=='DEFINITIONAL'and claim['evidence_class']=='FORMALLY_VERIFIED':claim['evidence_class']='CERTIFIED_TRIVIAL'
 if 'whole_paper_map'in mapping:mapping['whole_paper_map']={'filename':'claim_map.json','sha256':d.sha(note/'claim_map.json')}
 if manifest['claim_map']['filename']!='claim_map.json'and json.loads(d.read_regular(note/manifest['claim_map']['filename']))!=mapping:raise PolicyHold('unapproved public claim map field or sentence')
 if json.loads(d.read_regular(note/manifest['statement_inventory']['filename']))!=inventory:raise PolicyHold('unapproved public statement inventory field or sentence')
 if 'inv9_projection'in before_manifest:
  old_projection=json.loads(base_files[before_manifest['inv9_projection']['filename']]);text=tex.decode();marker=r'\section*{Claims excluded from formal scope}'
  if marker not in text:marker=r'\section*{Conjectures'
  if marker not in text:raise PolicyHold('actual archival projection marker missing')
  old_projection['paper_text']=text.split(marker,1)[0]+r'\end{document}';old_projection['final_tex_sha256']=d.digest(tex)
  if json.loads(d.read_regular(note/manifest['inv9_projection']['filename']))!=old_projection:raise PolicyHold('unapproved public projection field or sentence')
 if 'SCOPE_EVIDENCE.zip'in uploads:
  derived={'paper.tex','paper.pdf','metadata.json','SCOPED_CLAIM_MAP.json','SCOPED_STATEMENT_INVENTORY.json','SCOPED_RELEASE_MANIFEST.json','INV9_MAIN_SCOPE_PROJECTION.json','claim_map.json','SCOPE_EVIDENCE.zip','SCOPED_DRAFT_CHECK.json','PUBLICATION_BINDING_PLAN.json','PUBLICATION_BINDING.json','PHASE7_RULE_EXECUTION.json'}
  evidence={n:b for n,b in base_files.items()if n not in derived}
  for n in('claim_map.json',manifest['claim_map']['filename'],manifest['statement_inventory']['filename'],'metadata.json','CLAIM_CLASSIFICATIONS.json','AUDITED_BASE.zip','AUDITED_BASE_MANIFEST.json','SUPPLEMENTAL_WITNESS_CERTIFICATE.json','SUPPLEMENTAL_WITNESS_EVIDENCE.zip','SUPPLEMENTAL_WITNESS_MANIFEST.json'):
   if n in supplemental_names and minimal:continue
   evidence[n]=d.read_regular(note/n)
  if 'inv9_projection'in manifest:evidence[manifest['inv9_projection']['filename']]=d.read_regular(note/manifest['inv9_projection']['filename'])
  if d.read_regular(note/'SCOPE_EVIDENCE.zip')!=d.archive_bytes(evidence.items()):raise PolicyHold('unclassified or changed member in public scope evidence archive')
 for value in manifest['uploads']:
  name=d.safe_member(value['filename'])
  if '/'in name:raise PolicyHold('flat note upload inventory required')
  raw=d.read_regular(note/name);snapshots[str(note/name)]=d.digest(raw)
  if d.digest(raw)!=value['sha256']:raise PolicyHold('current upload differs')
 # A source-bound rule receipt cannot elide an input. It is deliberately not
 # hashed into itself; the later PUBLICATION_BINDING binds its final bytes.
 for path,h in snapshots.items():
  if not _preparing and(str(path)not in rule['inputs']or rule['inputs'][str(path)]!=h):raise PolicyHold('rule receipt input coverage incomplete or stale')
 if not _preparing and set(rule['inputs'])!=set(snapshots):raise PolicyHold('rule receipt unclassified source inputs')
 _finish(snapshots)
 return {'status':'APPROVED_RULES_APPLIED_NOT_PUBLICATION_BOUND','run_id':run,'identity':identity,'certificate':manifest['certificate'],'candidate':manifest['candidate'],'formal_statement':manifest['formal_statement'],'uploads':manifest['uploads'],'statement_scope':manifest['statement_scope'],'foundation_basis':basis['foundation_basis'],'claim_reviews':reviews,'public_metadata':metadata,'metadata_binding':next(v for v in manifest['uploads']if v['filename']=='metadata.json'),'input_bindings':snapshots,'prior_dois':row['existing_dois'],'actual_probe_observations':supplemental['observations']}

def require_note_publication_bound(note,root,authority_binding):
 import phase7_policy_versions as versions
 historical=versions.require_note_publication_bound(note,root,authority_binding,sys.modules[__name__])
 if historical is not None:return historical
 note=Path(note).resolve(strict=True);root=Path(root).resolve(strict=True)
 policy_path=note/'PHASE7_RULE_EXECUTION.json';policy_bytes=d.read_regular(policy_path)
 result=evaluate_note(note,root,authority_binding)
 bp=note/'PUBLICATION_BINDING.json';binding_bytes=d.read_regular(bp);binding=json.loads(binding_bytes)
 if (set(binding)!=BINDING_FIELDS or binding['standard']!=BINDING_STANDARD or binding['status']!='PUBLICATION_BOUND'
  or binding['run_id']!=result['run_id']or binding['authority']!=authority_binding or binding['policy_receipt']!=_binding(policy_path)
  or binding['identity']!=result['identity']or binding['execution_consumer_sha256']!=d.sha(__file__)
  or _time(binding['issued_at_utc'])>dt.datetime.now(dt.timezone.utc)
  or _time(binding['issued_at_utc'])<_time(json.loads(policy_bytes)['issued_at_utc'])):raise PolicyHold('exact fresh publication-time binding required')
 if d.read_regular(policy_path)!=policy_bytes or d.read_regular(bp)!=binding_bytes:raise PolicyHold('publication binding changed during admission')
 return {**result,'status':'PUBLICATION_BOUND','exact_publication_binding':True,'policy_receipt':_binding(policy_path),'publication_binding':_binding(bp)}


def prepare_rule_receipt(note,root,authority_binding,*,source_base_tex,before_metadata,supplemental_manifest=None,supplemental_certificate=None,at_utc=None):
 """Return actual evaluated receipt bytes to root; never writes or publishes."""
 note=Path(note).resolve(strict=True);root=Path(root).resolve(strict=True)
 manifest=json.loads(d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json'));authority=require_audit_authority(root,authority_binding)
 row=next(v for v in authority['audited_rows']if v['run_id']==manifest['run_id'])
 rule={'standard':RULE_STANDARD,'status':'APPLIED_APPROVED_RULES','run_id':manifest['run_id'],'authority':authority_binding,
 'audited_release_manifest':{k:row['evidence']['release_manifest'][k]for k in('path','sha256')},'source_base_tex':source_base_tex,
 'before_metadata':before_metadata,'supplemental_manifest':supplemental_manifest,'supplemental_certificate':supplemental_certificate,
 'issued_at_utc':at_utc or dt.datetime.now(dt.timezone.utc).isoformat(),'inputs':{},'claim_reviews':[],
 'draft_assessment':{},'execution_consumer_sha256':d.sha(__file__)}
 actual=evaluate_note(note,root,authority_binding,rule=rule,_preparing=True)
 rule['inputs']=actual['input_bindings'];rule['claim_reviews']=actual['claim_reviews'];rule['draft_assessment']=actual['identity']
 evaluate_note(note,root,authority_binding,rule=rule)
 return rule

def prepare_publication_binding(note,root,authority_binding,*,at_utc=None):
 import phase7_policy_versions as versions
 historical=versions.prepare_publication_binding(note,root,authority_binding,sys.modules[__name__],at_utc)
 if historical is not None:return historical
 """Recompute immediately before publish; root persists returned exact bytes."""
 result=evaluate_note(note,root,authority_binding);note=Path(note).resolve(strict=True)
 now=at_utc or dt.datetime.now(dt.timezone.utc).isoformat()
 if _time(now)>dt.datetime.now(dt.timezone.utc):raise PolicyHold('future publication binding')
 if _time(now)<_time(json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'))['issued_at_utc']):raise PolicyHold('publication binding predates actual rule execution')
 return {'standard':BINDING_STANDARD,'status':'PUBLICATION_BOUND','run_id':result['run_id'],'authority':authority_binding,'policy_receipt':_binding(note/'PHASE7_RULE_EXECUTION.json'),'identity':result['identity'],'issued_at_utc':now,'execution_consumer_sha256':d.sha(__file__)}
