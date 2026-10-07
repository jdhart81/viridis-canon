"""Receipt-backed Methods Digest group/children SSOT route, not a verifier.

No write, certificate issuance, proof search or implicit publication is provided.
Legacy entity functions remain separate and are delegated byte-unchanged.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt,hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
import methods_digest as d

STANDARD='VRS-METHODS-DIGEST-REGISTRATION-1'
EVIDENCE_STANDARD='VRS-METHODS-DIGEST-READBACK-EVIDENCE-1'
GROUP_ROUTE='METHODS_DIGEST_GROUP_V1'
NOTE_ROUTE='METHODS_DIGEST_NOTE_V1'
RECEIPT_FIELDS={'standard','status','tree_root','record_id','doi','release_week','package_path','digest_manifest','digest_publication_binding','authority','public_evidence','children','issued_at_utc','consumer_sha256','certifies'}
EVIDENCE_FIELDS={'standard','status','record_id','doi','public_legacy_receipt','public_native_receipt','own_publish_receipt','expected_legacy','expected_native','source_legacy_receipt','source_native_receipt','relation_template','server_context','downloads','strict_readback_result'}
CONTEXT_KEYS={'same_operation_response','existing_concept_doi','previous_latest_index','chain_parent_id','temporal_baseline','existing_communities','public_communities','mirror_proof','own_publish_response','same_operation_reservation_id','previous_public_readback','revision_evidence','own_operation_record_id','version_chain_context','derived_preview_context'}

class RegistrationHold(ValueError):pass

def _time(value):
 t=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
 if t.tzinfo is None:raise RegistrationHold('timezone-aware registration time required')
 return t.astimezone(dt.timezone.utc)

def _binding(path):return {k:d.binding(path)[k]for k in ('path','sha256')}

def _read(root,binding,snapshots):
 if not isinstance(binding,dict)or set(binding)!={'path','sha256'}:raise RegistrationHold('closed canonical file binding required')
 p,b=d.bound_file(root,binding);h=d.digest(b)
 if str(p)in snapshots and snapshots[str(p)]!=h:raise RegistrationHold('registration input changed during consumption')
 snapshots[str(p)]=h;return p,b

def _object(root,binding,snapshots):
 p,b=_read(root,binding,snapshots);v=json.loads(b)
 if not isinstance(v,dict):raise RegistrationHold('bound JSON object required')
 return p,v

def _finish(snapshots):
 for p,h in snapshots.items():
  if d.digest(d.read_regular(p))!=h:raise RegistrationHold('registration input changed before admission')

def _own_receipt(root,binding,snapshots,*,method,url):
 p,v=_object(root,binding,snapshots)
 if (v.get('environment')!='zenodo.org'or v.get('method')!=method or v.get('url')!=url
  or v.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
  or type(v.get('http_status'))is not int or not 200<=v['http_status']<300
  or re.fullmatch('[0-9a-f]{64}',str(v.get('response_sha256')))is None
  or not isinstance(v.get('response'),dict)):
  raise RegistrationHold('successful source-bound own production receipt required')
 if method!='GET'and re.fullmatch('[0-9a-f]{64}',str(v.get('request_body_sha256')))is None:raise RegistrationHold('own mutation body hash required')
 return v

def _record_id(value):
 if not isinstance(value,str)or re.fullmatch('[1-9][0-9]*',value)is None:raise RegistrationHold('canonical own record ID required')
 return value

def _package(root,relative):
 if not isinstance(relative,str)or not relative or Path(relative).is_absolute():raise RegistrationHold('tree-relative immutable digest package required')
 p=Path(root)/relative
 if p.is_symlink()or not p.is_dir()or not p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True)):raise RegistrationHold('digest outside canonical root or a symlink')
 return p.resolve()

def current_digest(package,root):return d.require_publication_bound(package,root)

def _snapshot_digest(root,package,manifest,pub_binding,snapshots):
 for name,expected in(('DIGEST_MANIFEST.json',manifest),('PUBLICATION_BINDING.json',pub_binding)):
  raw=d.read_regular(Path(package)/name)
  if json.loads(raw)!=expected:raise RegistrationHold('digest changed after fresh consumption')
  snapshots[str((Path(package)/name).resolve())]=d.digest(raw)
 for path,h in manifest.get('input_bindings',{}).items():
  _,raw=_read(root,{'path':path,'sha256':h},snapshots)
 for upload in manifest['uploads']:
  p=Path(package)/upload['filename'];raw=d.read_regular(p)
  if d.digest(raw)!=upload['sha256']:raise RegistrationHold('digest upload changed after fresh consumption')
  snapshots[str(p.resolve())]=d.digest(raw)
 for note in manifest['notes']:
  for key in('publication_binding','certificate'):
   _read(root,{k:note[key][k]for k in ('path','sha256')},snapshots)
  if 'policy_receipt'in note:
   _,raw=_read(root,{k:note['policy_receipt'][k]for k in ('path','sha256')},snapshots);rule=json.loads(raw)
   for path,h in rule['inputs'].items():
    # The fresh current policy has already proved this exact closed list,
    # including its sole outside-tree pinned renderer binary observation.
    p=Path(path);data=d.read_regular(p)
    if d.digest(data)!=h:raise RegistrationHold('note proof/policy source changed after fresh consumption')
    snapshots[str(p)]=h


def _context(root,value,snapshots,record_id):
 _,context=_object(root,value,snapshots)
 if context.get('operation')!='NEW_VERSION'or context.get('phase')!='PUBLISHED':raise RegistrationHold('own initial published-record server context required')
 if 'source_bindings'in context:
  if set(context)!={'operation','phase','source_bindings'}or not isinstance(context['source_bindings'],dict)or set(context['source_bindings'])-CONTEXT_KEYS:raise RegistrationHold('closed source-bound server context required')
  answer={'operation':context['operation'],'phase':context['phase']}
  for key,source in context['source_bindings'].items():
   if not isinstance(source,dict)or set(source)!={'binding','selector'}or source['selector']not in {'OBJECT','RESPONSE','VALUE'}:raise RegistrationHold('source-bound server rule evidence required')
   _,raw=_read(root,source['binding'],snapshots);obj=json.loads(raw)
   if source['selector']=='OBJECT'and not isinstance(obj,dict):raise RegistrationHold('server context object required')
   if source['selector']=='RESPONSE':
    if not isinstance(obj,dict)or obj.get('environment')!='zenodo.org'or obj.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'or not isinstance(obj.get('response'),dict):raise RegistrationHold('server context response lacks production receipt')
    obj=obj['response']
   answer[key]=obj
 else:
  if set(context)-CONTEXT_KEYS-{'operation','phase','host','record_id'}:raise RegistrationHold('unlisted server rule context field')
  if ('host'in context and context['host']!='zenodo.org')or('record_id'in context and str(context['record_id'])!=record_id):raise RegistrationHold('server context own ID/host differs')
  answer={k:v for k,v in context.items()if k not in {'host','record_id'}}
  def capture(item):
   if isinstance(item,dict):
    if 'path'in item and 'sha256'in item:_read(root,{k:item[k]for k in ('path','sha256')},snapshots)
    for child in item.values():capture(child)
   elif isinstance(item,list):
    for child in item:capture(child)
  capture(answer)
 return answer

def assemble_evidence(*, record_id, public_legacy_receipt, public_native_receipt,
                      own_publish_receipt, expected_legacy, expected_native,
                      source_legacy_receipt, source_native_receipt, relation_template,
                      server_context, downloads, strict_readback_result):
 """Closed adapter from original own transport evidence; grants no PASS."""
 rid=_record_id(record_id)
 bindings={k:v for k,v in locals().copy().items() if k in EVIDENCE_FIELDS-{'standard','status','record_id','doi','downloads'}}
 for key,value in bindings.items():
  if not isinstance(value,dict)or set(value)!={'path','sha256'}or not isinstance(value['path'],str)or re.fullmatch('[0-9a-f]{64}',str(value['sha256']))is None:raise RegistrationHold('closed evidence path/hash required: '+key)
 if not isinstance(downloads,list)or len(downloads)!=6 or len({v.get('filename')for v in downloads if isinstance(v,dict)})!=6:raise RegistrationHold('exact six unique public downloads required')
 for row in downloads:
  if not isinstance(row,dict)or set(row)!={'filename','binding','url'}or not isinstance(row['binding'],dict)or set(row['binding'])!={'path','sha256'}:raise RegistrationHold('closed public download adapter row required')
  d.safe_member(row['filename'])
  if re.fullmatch('[0-9a-f]{64}',str(row['binding']['sha256']))is None or not isinstance(row['binding']['path'],str)or not isinstance(row['url'],str):raise RegistrationHold('bound public download adapter source required')
 value={'standard':EVIDENCE_STANDARD,'status':'SOURCE_BOUND_READBACK_INPUTS','record_id':rid,'doi':'10.5281/zenodo.'+rid,**deepcopy(bindings),'downloads':deepcopy(downloads)}
 if set(value)!=EVIDENCE_FIELDS:raise RegistrationHold('evidence adapter field coverage differs')
 return value

def source_custom_fields(public, source_legacy, source_native):
 """Preserve only actual source-bound existing legacy community membership."""
 source=source_native.get('custom_fields',{})
 if not isinstance(source,dict)or set(source)-{'legacy:communities'}:raise RegistrationHold('unapproved source custom fields')
 communities=source_legacy.get('metadata',{}).get('communities',[])
 if public.get('communities',[])!=communities:raise RegistrationHold('digest community membership changed')
 if 'legacy:communities'in source:
  if not isinstance(communities,list)or not communities or any(not isinstance(v,dict)or set(v)!={'id'}or not isinstance(v['id'],str)or not v['id']for v in communities):raise RegistrationHold('closed existing community membership required')
  if source['legacy:communities']!=[v['id']for v in communities]:raise RegistrationHold('source legacy community mirror differs from existing membership')
 return deepcopy(source)

def _check_public(package,root,m,evidence,snapshots,*,digest_consumer=current_digest,strict_consumer=d.strict_readback,audit_consumer=None,views=None):
 rid=_record_id(evidence.get('record_id'));doi='10.5281/zenodo.'+rid
 if set(evidence)!=EVIDENCE_FIELDS or evidence.get('standard')!=EVIDENCE_STANDARD or evidence.get('status')!='SOURCE_BOUND_READBACK_INPUTS'or evidence.get('doi')!=doi:raise RegistrationHold('closed own published digest evidence required')
 legacy_receipt=_own_receipt(root,evidence['public_legacy_receipt'],snapshots,method='GET',url='https://zenodo.org/api/records/'+rid)
 native_receipt=_own_receipt(root,evidence['public_native_receipt'],snapshots,method='GET',url='https://zenodo.org/api/records/'+rid)
 if native_receipt.get('accept')!='application/vnd.inveniordm.v1+json':raise RegistrationHold('bound native public representation required')
 publish=_own_receipt(root,evidence['own_publish_receipt'],snapshots,method='POST',url='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish')
 _,expected_legacy=_object(root,evidence['expected_legacy'],snapshots);_,expected_native=_object(root,evidence['expected_native'],snapshots)
 if (str(expected_legacy.get('id'))!=rid or expected_legacy.get('doi')!=doi or expected_native.get('id')!=rid):raise RegistrationHold('expected own digest identity/custom fields differ')
 # Predict native metadata from the preserved actual source pair and the byte-
 # bound digest payload, never from the current after-write response.
 _,source_legacy=_object(root,evidence['source_legacy_receipt'],snapshots);_,source_native=_object(root,evidence['source_native_receipt'],snapshots)
 for source in(source_legacy,source_native):
  if source.get('method')!='GET'or source.get('environment')!='zenodo.org'or source.get('http_status')!=200 or source.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'or source.get('url')!='https://zenodo.org/api/records/'+str(source.get('response',{}).get('id'))or re.fullmatch('[0-9a-f]{64}',str(source.get('response_sha256')))is None:raise RegistrationHold('fresh saved own source-pair GET required')
 if expected_native.get('custom_fields',{})!=source_custom_fields(m['public_metadata'],source_legacy['response'],source_native['response']):raise RegistrationHold('expected custom fields differ from exact existing community source')
 _,relation=_object(root,evidence['relation_template'],snapshots)
 _,source_raw=_read(root,m['source_metadata'],snapshots);approved=json.loads(source_raw);approved=approved.get('metadata',approved)
 import digest_metadata
 predicted=digest_metadata.native_metadata(m['public_metadata'],approved,source_legacy['response'],source_native['response'],relation)
 if expected_native.get('metadata')!=predicted:raise RegistrationHold('expected native metadata differs from exact source-bound digest projection')
 context=_context(root,evidence['server_context'],snapshots,rid)
 from server_managed_fields import audit_readback
 audit_consumer=audit_consumer or audit_readback
 actual_legacy,actual_native=(legacy_receipt['response'],native_receipt['response'])if views is None else views
 if (str(actual_legacy.get('id'))!=rid or actual_legacy.get('doi')!=doi or actual_native.get('id')!=rid or actual_native.get('is_published')is not True or actual_native.get('pids',{}).get('doi',{}).get('identifier')!=doi):raise RegistrationHold('published own native/legacy identity mismatch')
 checked=audit_consumer(actual_native,expected_native,host='zenodo.org',record_id=rid,**context)
 if checked.get('status')!='PASS':raise RegistrationHold('strict closed server-managed public readback HOLD: '+str(checked.get('reasons')))
 rows=evidence['downloads']
 if not isinstance(rows,list)or len(rows)!=6:raise RegistrationHold('exact six aggregate public downloads required')
 downloads={}
 for row in rows:
  if not isinstance(row,dict)or set(row)!={'filename','binding','url'}or row['filename']in downloads:raise RegistrationHold('closed unique download source required')
  name=d.safe_member(row['filename']);u=urlsplit(row['url'])
  if '/'in name or u.scheme!='https'or u.netloc!='zenodo.org'or u.query or u.fragment or not u.path.startswith('/api/'):raise RegistrationHold('own published download URL required')
  _,raw=_read(root,row['binding'],snapshots);downloads[name]=(row['url'],raw)
 def download(file,record_id):
  if record_id!=rid or file.get('key')not in downloads:raise RegistrationHold('foreign or missing public download')
  url,raw=downloads[file['key']]
  if file.get('links',{}).get('self')!=url:raise RegistrationHold('public file URL differs from saved own download source')
  return raw
 def metadata_check(actual,expected,own):
  from publication_preservation import require_public_metadata
  require_public_metadata(actual.get('metadata',{}),expected.get('metadata',{}))
  if actual.get('doi')!=expected.get('doi')or('pids'in expected and actual.get('pids')!=expected['pids']):raise RegistrationHold('public legacy PID mismatch')
 own={'record_id':rid,'doi':doi,'method':'POST','url':publish['url'],'status':publish['status']}
 result=strict_consumer(package,root,actual_legacy,own,download,expected_record=expected_legacy,metadata_consumer=metadata_check)
 _,recorded=_object(root,evidence['strict_readback_result'],snapshots)
 if result!=recorded or result.get('status')!='STRICT_OWN_PUBLIC_READBACK_PASS'or result.get('certifies')is not False:raise RegistrationHold('fresh strict public digest result differs')
 return result,actual_legacy,actual_native

def _children(root,package,m):
 result=[]
 for note in m['notes']:
  path=Path(note['path']).resolve(strict=True)
  if not path.is_relative_to(Path(root).resolve(strict=True)):raise RegistrationHold('foreign note artifact')
  result.append({'id':'publication:methods-note:'+m['release_week']+':'+note['run_id'],'path':str(path.relative_to(root)),'run_id':note['run_id'],'certificate':{k:note['certificate'][k]for k in ('path','sha256')},'publication_binding':{k:note['publication_binding'][k]for k in ('path','sha256')}})
 if not result or len({v['run_id']for v in result})!=len(result)or len({v['path']for v in result})!=len(result):raise RegistrationHold('unique per-note Run/path required')
 return result

def prepare_registration(root,package,public_evidence,*,digest_consumer=current_digest,strict_consumer=d.strict_readback,audit_consumer=None,issued_at_utc=None):
 """Return a source-bound registration proposal after actual public readback."""
 root=Path(root).resolve(strict=True);package=Path(package).resolve(strict=True)
 if not package.is_relative_to(root):raise RegistrationHold('foreign digest artifact')
 snapshots={};_,e=_object(root,public_evidence,snapshots);m,b=digest_consumer(package,root);_snapshot_digest(root,package,m,b,snapshots)
 _check_public(package,root,m,e,snapshots,digest_consumer=digest_consumer,strict_consumer=strict_consumer,audit_consumer=audit_consumer)
 at=issued_at_utc or dt.datetime.now(dt.timezone.utc).isoformat()
 if _time(at)>dt.datetime.now(dt.timezone.utc):raise RegistrationHold('future registration refused')
 value={'standard':STANDARD,'status':'PUBLISHED_GROUP_BOUND','tree_root':str(root),'record_id':e['record_id'],'doi':e['doi'],'release_week':m['release_week'],'package_path':str(package.relative_to(root)),'digest_manifest':_binding(package/'DIGEST_MANIFEST.json'),'digest_publication_binding':_binding(package/'PUBLICATION_BINDING.json'),'authority':m['authority'],'public_evidence':public_evidence,'children':_children(root,package,m),'issued_at_utc':at,'consumer_sha256':d.sha(__file__),'certifies':False}
 _finish(snapshots);return value

def require_registration(root,binding,ledger=None,*,digest_consumer=current_digest,strict_consumer=d.strict_readback,audit_consumer=None,views=None,parity_consumer=None):
 root=Path(root).resolve(strict=True);snapshots={};_,v=_object(root,binding,snapshots)
 if set(v)!=RECEIPT_FIELDS or v.get('standard')!=STANDARD or v.get('status')!='PUBLISHED_GROUP_BOUND'or v.get('tree_root')!=str(root)or v.get('consumer_sha256')!=d.sha(__file__)or v.get('certifies')is not False or _time(v['issued_at_utc'])>dt.datetime.now(dt.timezone.utc):raise RegistrationHold('current closed registered digest receipt required')
 package=_package(root,v['package_path']);m,b=digest_consumer(package,root);_snapshot_digest(root,package,m,b,snapshots)
 if v['digest_manifest']!=_binding(package/'DIGEST_MANIFEST.json')or v['digest_publication_binding']!=_binding(package/'PUBLICATION_BINDING.json')or v['authority']!=m['authority']or v['release_week']!=m['release_week']or v['children']!=_children(root,package,m):raise RegistrationHold('digest/group child binding differs')
 _,e=_object(root,v['public_evidence'],snapshots)
 if e['record_id']!=v['record_id']or e['doi']!=v['doi']:raise RegistrationHold('public evidence/group identity differs')
 result,legacy,native=_check_public(package,root,m,e,snapshots,digest_consumer=digest_consumer,strict_consumer=strict_consumer,audit_consumer=audit_consumer,views=views)
 if ledger is None:
  ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_raw=d.read_regular(ledger_path);snapshots[str(ledger_path)]=d.digest(ledger_raw);ledger=json.loads(ledger_raw)
 if not isinstance(ledger,dict)or Path(str(ledger.get('tree_root',''))).resolve()!=root:raise RegistrationHold('current own SSOT required for registered note parity')
 if parity_consumer is None:
  from mirror_parity import run_parity
  parity_consumer=run_parity
 parity_observations=[]
 if ledger is not None:
  for child in v['children']:
   matches=[x for x in ledger['run_entities']if x.get('id')==child['run_id']]
   if len(matches)!=1 or matches[0].get('status')!='CERTIFIED'or matches[0].get('certificate_valid')is not True:raise RegistrationHold('note has no fresh parity-qualified current Run certificate')
   parity=parity_consumer(root,matches[0].get('path'))
   if parity.get('status')!='MATCH'or parity.get('purpose')!='PARITY_ONLY_NOT_CERTIFICATION':raise RegistrationHold('fresh source/mirror parity failed for registered note: '+child['run_id'])
   parity_observations.append((matches[0]['path'],parity))
   cert=matches[0].get('certificate');cp=Path(cert)if isinstance(cert,str)else None
   if cp is None:raise RegistrationHold('Run certificate path absent')
   cp=cp if cp.is_absolute()else root/cp
   if cp.resolve(strict=True)!=Path(child['certificate']['path']).resolve(strict=True)or d.sha(cp)!=child['certificate']['sha256']:raise RegistrationHold('per-note current main certificate changed')
 for path,observed in parity_observations:
  if parity_consumer(root,path)!=observed:raise RegistrationHold('source/mirror inventory changed during registered-note readback')
 _finish(snapshots);return {'receipt':v,'manifest':m,'strict_readback':result,'public_legacy':legacy,'public_native':native}

def entity_rows(root,binding,ledger,*,consume=require_registration):
 result=consume(root,binding,ledger);v=result['receipt'];rid=v['record_id'];gid='publication:methods-digest:'+v['release_week']+':'+rid
 shared={'kind':'PUBLICATION','doi':v['doi'],'registration_receipt':binding,'publication_binding_status':'PUBLICATION_BOUND','publication_registration_status':'PASS','enforcement_acceptable':True,'registration_revalidated':True,'reasons':[],'publication_registration_reasons':[]}
 group={**shared,'id':gid,'path':v['package_path'],'entity_type':'METHODS_DIGEST_GROUP','registration_route':GROUP_ROUTE,'status':'SCOPED_DIGEST','certificate_valid':False,'certifies':False,'note_ids':[c['id']for c in v['children']]}
 children=[]
 for c in v['children']:
  cert=Path(c['certificate']['path']).resolve(strict=True)
  children.append({**shared,'id':c['id'],'path':c['path'],'run_id':c['run_id'],'entity_type':'METHODS_DIGEST_NOTE','registration_route':NOTE_ROUTE,'group_id':gid,'status':'CERTIFIED','certificate_valid':True,'certificate':str(cert.relative_to(root)),'certificate_sha256':c['certificate']['sha256'],'note_publication_binding':c['publication_binding'],'certifies':'LISTED_NOTE_SCOPE_ONLY'})
 return [group,*children]

def preserve(ledger,previous,*,legacy,consume=require_registration):
 """Delegate legacy registrations unchanged, then freshly consume named groups."""
 if not isinstance(previous,dict):return legacy(ledger,previous)
 rows=previous.get('publication_entities',[])
 if not isinstance(rows,list)or any(not isinstance(v,dict)for v in rows):return legacy(ledger,previous)
 selected=[v for v in rows if v.get('registration_route')in {GROUP_ROUTE,NOTE_ROUTE}]
 ordinary={**previous,'publication_entities':[v for v in rows if v.get('registration_route')not in {GROUP_ROUTE,NOTE_ROUTE}]}
 result=legacy(ledger,ordinary)
 if not selected:return result
 root=Path(result['tree_root']).resolve(strict=True);identities={v['id']for t in('file_entities','run_entities','publication_entities')for v in result.get(t,[])};paths={(root/v['path']).resolve()for t in('file_entities','run_entities','publication_entities')for v in result.get(t,[])}
 groups=[v for v in selected if v['registration_route']==GROUP_ROUTE];used=set()
 for group in groups:
  binding=group.get('registration_receipt');cohort=[v for v in selected if v.get('registration_receipt')==binding]
  try:
   fresh=entity_rows(root,binding,result,consume=consume)
   if len(cohort)!=len(fresh)or {v.get('id')for v in cohort}!={v['id']for v in fresh}:raise RegistrationHold('missing/duplicate registered per-note children')
   old_by_id={v['id']:v for v in cohort}
   for new in fresh:
    old=old_by_id[new['id']]
    for k in('id','path','doi','registration_route','entity_type','registration_receipt','group_id','run_id','certificate','certificate_sha256','note_publication_binding','note_ids','certifies'):
     if old.get(k)!=new.get(k):raise RegistrationHold('registered identity/path/certificate/group changed: '+k)
    if old.get('enforcement_acceptable')is not True:raise RegistrationHold('previous held group requires explicit re-registration')
   admitted=fresh
  except Exception as exc:
   admitted=[{**v,'status':'DEBT','certificate_valid':False,'publication_binding_status':'HOLD','publication_registration_status':'HOLD','enforcement_acceptable':False,'registration_revalidated':False,'reasons':[type(exc).__name__+': '+str(exc)],'publication_registration_reasons':[str(exc)]}for v in cohort]
  for v in admitted:
   if v['id']in identities or (root/v['path']).resolve()in paths or v['id']in used:raise RegistrationHold('ambiguous publication group/child identity or artifact')
   identities.add(v['id']);paths.add((root/v['path']).resolve());used.add(v['id']);result['publication_entities'].append(v)
   if v['enforcement_acceptable']is not True:result['publication_holds'].append({'id':v['id'],'reasons':v['reasons']})
 if len(used)!=len(selected):raise RegistrationHold('orphaned or duplicate digest registration row')
 from collections import Counter
 result['publication_registration_summary']=dict(Counter(v['publication_registration_status']for v in result['publication_entities']))
 result['publication_registration_enforcement_acceptable']=bool(result['publication_entities'])and all(v.get('enforcement_acceptable')is True for v in result['publication_entities'])
 result['publication_registration_defects']=[v['id']for v in result['publication_entities']if v.get('enforcement_acceptable')is not True]
 return result

def evaluate_publication(artifact,ledger,*,legacy,scoped_legacy=None,entity_id=None,inspector=None,enforce=False,require_premise_declaration=False):
 from claim_binding import find_entity
 try:entity=find_entity(ledger,Path(artifact),entity_id)
 except Exception:return legacy(artifact,ledger,entity_id=entity_id,inspector=inspector,enforce=enforce,require_premise_declaration=require_premise_declaration)
 if entity.get('registration_route')not in {GROUP_ROUTE,NOTE_ROUTE}:
  old=scoped_legacy if scoped_legacy is not None and (Path(artifact)/'SCOPED_RELEASE_MANIFEST.json').exists()else legacy
  return old(artifact,ledger,entity_id=entity_id,inspector=inspector,enforce=enforce,require_premise_declaration=require_premise_declaration)
 result={'artifact':str(Path(artifact).resolve()),'entity_id':entity['id'],'mode':'ENFORCING'if enforce else'REPORT_ONLY','enforcement':enforce,'status':'HOLD','verification_status':'UNCERTIFIED','reasons':[],'exact_publication_binding':False,'local_lean_execution':False,'published_doi_requires_human_decision':True,'doi':entity.get('doi')}
 try:
  rows=entity_rows(Path(ledger['tree_root']),entity['registration_receipt'],ledger)
  expected=next(v for v in rows if v['id']==entity['id'])
  if any(entity.get(k)!=expected.get(k)for k in('path','doi','registration_route','group_id','run_id','certificate','certificate_sha256','note_publication_binding','note_ids')):raise RegistrationHold('named SSOT entity differs from actual registration')
  if entity.get('enforcement_acceptable')is not True or any(entity.get(k)!=expected.get(k)for k in('status','certificate_valid','publication_binding_status','publication_registration_status','registration_revalidated','certifies')):raise RegistrationHold('registration is held or its exact scope status changed')
  group=entity['registration_route']==GROUP_ROUTE
  result.update(status='PASS',verification_status='SCOPED_DIGEST'if group else'CERTIFIED',label='METHODS DIGEST — individually bound scoped notes'if group else'SCOPED CERTIFIED — approved per-note mathematical statements',exact_publication_binding=True,certifies=False if group else'LISTED_NOTE_SCOPE_ONLY',scope='Per-note source-bound claims only; no theorem certificate is assigned to the aggregate',registration_route=entity['registration_route'])
 except Exception as exc:result['reasons'].append(type(exc).__name__+': '+str(exc))
 result.update(blocking=enforce and result['status']!='PASS',release_eligible=result['status']=='PASS',canon_eligible=result['status']=='PASS')
 return result

def augment_audit(root,ledger,audit,*,consume=require_registration):
 """Add one DOI/group join; do not count the aggregate as a certified paper."""
 out=deepcopy(audit);groups=[v for v in ledger.get('publication_entities',[])if v.get('registration_route')==GROUP_ROUTE]
 out['methods_digest_groups']=[]
 for group in groups:
  result=consume(root,group['registration_receipt'],ledger);v=result['receipt']
  if any(r.get('doi')==v['doi']for r in out['published_records']):raise RegistrationHold('digest DOI collides with an existing generic public artifact join')
  row={'doi':v['doi'],'deposit_paths':[str(Path(root)/v['package_path'])],'run_ids':[],'certificate_valid':False,'kind':'METHODS_DIGEST_GROUP','certifies':False,'publication_registration_status':'PASS','methods_digest_registration':{'tree_root':str(Path(root).resolve()),'receipt':group['registration_receipt']},'note_run_ids':[c['run_id']for c in v['children']]}
  out['methods_digest_groups'].append(row)
 out.setdefault('counts',{})['methods_digest_groups']=len(groups)
 return out

def _get_record(record_id,accept):
 import urllib.request
 request=urllib.request.Request('https://zenodo.org/api/records/'+record_id,headers={'Accept':accept,'User-Agent':'Viridis GET-only registered Methods Digest readback'})
 with urllib.request.urlopen(request,timeout=30)as response:
  if response.status!=200:raise RegistrationHold('public GET failed')
  raw=response.read()
 return json.loads(raw),d.digest(raw)

def public_label_read_record(row,*,legacy,getter=_get_record,consume=require_registration):
 marker=row.get('methods_digest_registration')
 if marker is None:return legacy(row)
 result={'doi':row.get('doi'),'status':'UNAVAILABLE','proposed_label':'METHODS DIGEST — individually bound scoped notes','proposed_label_disagrees':True,'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'local_manuscript_public_checksum_matches':[]}
 try:
  if not isinstance(marker,dict)or set(marker)!={'tree_root','receipt'}:raise RegistrationHold('closed digest public-label join required')
  root=Path(marker['tree_root']).resolve(strict=True);actual=consume(root,marker['receipt']);v=actual['receipt']
  if row.get('doi')!=v['doi']or row.get('deposit_paths')!=[str(root/v['package_path'])]:raise RegistrationHold('public-label digest DOI/artifact differs')
  old,h1=getter(v['record_id'],'application/json');native,h2=getter(v['record_id'],'application/vnd.inveniordm.v1+json')
  consume(root,marker['receipt'],views=(old,native))
  result.update(status='READ',url='https://zenodo.org/api/records/'+v['record_id'],title=old['metadata']['title'],description=old['metadata']['description'],files=old['files'],proposed_label_disagrees=False,public_verification_status='SCOPED_DIGEST',reason='Exact receipt-backed digest metadata/files and individually bound notes passed fresh readback; aggregate is not a theorem certificate',response_sha256=h1,native_response_sha256=h2)
 except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
 return result


def public_label_readback(audit,*,legacy):
 # Group DOIs are a separate population, never a whole-paper certificate count.
 # The existing reader still owns parallel GET scheduling and report shape.
 groups=audit.get('methods_digest_groups',[])
 if not isinstance(groups,list)or any(not isinstance(v,dict)for v in groups):raise RegistrationHold('malformed registered digest public population')
 ordinary=audit['published_records'];ids=[v.get('doi')for v in ordinary+groups]
 if len(ids)!=len(set(ids)):raise RegistrationHold('ambiguous generic/digest public DOI join')
 return legacy({**audit,'published_records':[*ordinary,*groups]})
