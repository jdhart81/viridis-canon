"""Reviewed packaging successor for explicitly authorized same-concept digests.

The original transport, ownership, causal publish boundary, source session,
mutation journal and scientific note consumers remain the authority. Dynamic
file inventory is derived from the freshly admitted v2 digest; inherited access
copies require the nominated exact registry. No automatic spine, certification,
local proof execution, ledger write or scope expansion is provided.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt
import fcntl, hashlib, importlib, json, os, re, types
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
BASE='https://zenodo.org'
NATIVE='application/vnd.inveniordm.v1+json'
STANDARD='VRS-STANDALONE-PDF-DIGEST-EXECUTION-2'
RULE_HEADER=b'## Backlog delivery fix \xe2\x80\x94 split the digest \xe2\x80\x94 2026-10-10\n'
PINNED={
 'zenodo_transport':'69bcfa0c7008f052a0c30d06d23e94a226c5b40707905550e41c40e16c379b65',
 'digest_weekly_state':'96b3aa1eca1e2f6fa42563ea912338ae839d5d9786ee7eb777f81a12c988387c',
 'mutation_journal_writer':'a2a72c49b5bc67a5c7535320bab5b6513b8cbfac3cf6c19d39b2e0c3d5d5c4e8',
}
MODULES=('methods_digest_v2','methods_digest_registration_v3','manuscript_access_registry','manuscript_pdf_gate','packaging_runtime')+tuple(PINNED)+('own_record_comparison','own_prior_record','publication_preservation','digest_metadata','first_digest_state','phase7_mutation_baseline','weekly_archive_wait','first_digest_publisher','owned_weekly_discovery')
CONFIG_FIELDS={'standard','canonical_root','package','batch_label','authority','predecessor_registration','source_legacy_receipt','source_native_receipt','source_native_before_create','existing_ownership','existing_package','existing_validation','source_pins','controller','expected_ssot_sha256','split_rule','source_scope_plan','user_authorization','account_discovery','release_scope','packaging_profile','access_registry'}

class Hold(ValueError):pass
def need(value,reason):
 if not value:raise Hold('HOLD_SPLIT_'+reason)
def encoded(value):return json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n'
def sha(data):return hashlib.sha256(data).hexdigest()
def raw(path):
 p=Path(path);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'REGULAR_INPUT')
 a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'READ_RACE');return b
def binding(path):return {'path':str(Path(path).resolve(strict=True)),'sha256':sha(raw(path))}
def bound(root,value):
 need(isinstance(value,dict)and set(value)=={'path','sha256'}and isinstance(value['path'],str)and re.fullmatch('[0-9a-f]{64}',str(value['sha256'])),'CLOSED_BINDING')
 p=Path(value['path']);p=p if p.is_absolute()else root/p
 need('..'not in p.parts and p.resolve(strict=True).is_relative_to(root),'OWN_INPUT')
 b=raw(p);need(sha(b)==value['sha256'],'BOUND_HASH');return p,b
def obj(root,value):return json.loads(bound(root,value)[1])
def immutable(path,data):
 p=Path(path);need(not p.exists()and not any(q.is_symlink()for q in(p,*p.parents)),'EXCLUSIVE_OUTPUT');p.parent.mkdir(parents=True,exist_ok=True)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 need(raw(p)==data,'OUTPUT_READBACK')
def utc(value):
 t=dt.datetime.fromisoformat(value.replace('Z','+00:00'));need(t.tzinfo is not None,'TIMEZONE');return t.astimezone(dt.timezone.utc)
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def record_id(value):
 need(isinstance(value,str)and re.fullmatch('[1-9][0-9]*',value),'RECORD_ID');return value
def own_url(url):
 u=urlsplit(url);need(u.scheme=='https'and u.netloc=='zenodo.org'and not u.query and not u.fragment and u.path.startswith('/api/'),'OWN_URL');return u.path

def publication_budget(events,at_utc,load,*,complete):
 """Classify the original complete source-bound journal, without SHA dedupe.

 Only /actions/publish consumes the new user-approved publication limit.
 An uncertain or merely reserved publication conservatively consumes a slot.
 Old upload/metadata reservations remain in the original journal unchanged.
 """
 need(complete is True and isinstance(events,list),'COMPLETE_ORIGINAL_JOURNAL')
 t=utc(at_utc);day=t.astimezone(ZoneInfo('America/New_York')).date();seen=set();charged=[]
 for e in events:
  need(isinstance(e,dict)and set(e)=={'operation_id','method','host','at_utc','status','receipt_binding'}and isinstance(e['operation_id'],str)and e['operation_id']and e['operation_id']not in seen and e['host']=='zenodo.org'and e['method']in{'POST','PUT','DELETE'}and e['status']in{'STARTED_NO_RETRY','HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'},'JOURNAL_ROW')
  seen.add(e['operation_id']);et=utc(e['at_utc']);need(et<=t,'FUTURE_EVENT')
  r=load(e['receipt_binding']);need(isinstance(r,dict)and r.get('method')==e['method'],'EVENT_METHOD')
  if 'transport_receipt_path'in r:
   need(set(r)=={'operation_id','method','url','request_body_sha256','transport_receipt_path'}and r['operation_id']==e['operation_id']and e['status']=='STARTED_NO_RETRY','ORIGINAL_INTENDED_REQUEST')
  else:
   need(r.get('environment')=='zenodo.org'and r.get('status')==e['status'],'ORIGINAL_TRANSPORT_RECEIPT')
   if r['status']=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE':need(re.fullmatch('[0-9a-f]{64}',str(r.get('response_sha256'))),'ORIGINAL_RESPONSE_HASH')
  path=own_url(r.get('url',''))
  need(re.fullmatch('[0-9a-f]{64}',str(r.get('request_body_sha256'))),'REQUEST_HASH')
  if re.fullmatch('/api/deposit/depositions/[1-9][0-9]*/actions/publish',path):
   need(e['method']=='POST'and r['request_body_sha256']==sha(b'{}'),'PUBLISH_REQUEST')
   if et.astimezone(ZoneInfo('America/New_York')).date()==day:charged.append(e['operation_id'])
 return {'status':'ORIGINAL_JOURNAL_PUBLICATION_COUNT','date_new_york':str(day),'used':len(charged),'remaining':max(0,10-len(charged)),'charged_operation_ids':charged,'all_original_events_retained':len(events),'writes_authorized':len(charged)<10}

def require_publish_day(public,at_utc):
 day=str(utc(at_utc).astimezone(ZoneInfo('America/New_York')).date())
 need(public.get('publication_date')==day,'ACTUAL_PUBLICATION_DAY');return day

def require_mutation_day(manifest,at_utc):
 """Every new mutation retains the immutable actual NY day and ISO week."""
 day=require_publish_day(manifest['public_metadata'],at_utc)
 year,week,_=dt.date.fromisoformat(day).isocalendar()
 need(manifest.get('release_week')==f'{year}-W{week:02d}','ACTUAL_RELEASE_WEEK');return day

def require_cohort(scope,run_ids):
 need(isinstance(scope,dict)and scope.get('run_ids')==run_ids and run_ids
      and len(set(run_ids))==len(run_ids)and all(re.fullmatch('Run-[0-9]{3}',r)for r in run_ids),'EXACT_BOUND_RELEASE_SCOPE')

def draft_cleanup_entry(legacy,native,entry,ownership,*,allowed_names):
 """Exact current draft file, including an uploaded partial rather than inheritance."""
 rid=record_id(str(legacy.get('id')));parent=record_id(str(legacy.get('conceptrecid')))
 need(rid==ownership['record_id']and parent==ownership['concept_id']and rid!=parent,'CLEANUP_OWNERSHIP')
 need(legacy.get('state')=='unsubmitted'and legacy.get('submitted')is False and native.get('id')==rid and native.get('is_published')is False and native.get('parent',{}).get('id')==parent,'UNPUBLISHED_DRAFT_ONLY')
 need(isinstance(entry,dict)and isinstance(entry.get('filename'),str)and '/'not in entry['filename']and entry['filename']in allowed_names and isinstance(entry.get('id'),str)and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',entry['id'])and type(entry.get('filesize'))is int and entry['filesize']>=0 and re.fullmatch('[0-9a-f]{32}',str(entry.get('checksum'))),'EXACT_CLEANUP_ENTRY')
 matches=[f for f in legacy.get('files',[])if isinstance(f,dict)and f.get('id')==entry['id']]
 need(len(matches)==1 and encoded(matches[0])==encoded(entry),'CURRENT_DRAFT_ENTRY')
 en=native.get('files',{}).get('entries',{}).get(entry['filename'])
 need(isinstance(en,dict)and en.get('id')==entry['id']and en.get('key')==entry['filename']and en.get('size')==entry['filesize']and en.get('checksum')=='md5:'+entry['checksum'],'NATIVE_DRAFT_ENTRY')
 return BASE+'/api/deposit/depositions/'+rid+'/files/'+entry['id']

def classify_draft_effect(before,intended,validate,rejection):
 """Use the unchanged own-record guard, never fields from an after body."""
 try:return 'NO_EFFECT',validate(before)
 except rejection:pass
 try:return 'EXACT_INTENDED_EFFECT_WITHOUT_ACK',validate(intended)
 except rejection:raise Hold('HOLD_SPLIT_UNCERTAIN_CONTENT_OR_FILE_MISMATCH')from None

def exact_main_inventory(legacy,inventory):
 files=legacy.get('files');need(isinstance(files,list)and len(files)==len(inventory),'EXACT_MAIN_FILE_COUNT')
 names=[x.get('filename')for x in files];need(len(set(names))==len(names)and set(names)==set(inventory),'EXACT_MAIN_FILENAMES')
 for f in files:
  expected=inventory[f['filename']];need(type(f.get('filesize'))is int and f['filesize']==expected['bytes']and f.get('checksum')==expected['md5'],'EXACT_MAIN_FILE_BYTES')
 return True


def registered_runs(admitted,root,reg,successor,own,*,load=None,ledger=None):
 """Bridge only the existing own-context producer; default registrar remains.

 The original traversal handles its original context standards unchanged.
 New own contexts locate their source only through a unique current SSOT
 group and independently reconsume every original registration.
 """
 load=load or(lambda b:obj(root,b));ledger=ledger or json.loads(raw(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))
 week=admitted['receipt']['release_week'];seen_records=set();seen_runs=set();current=admitted;parent=None
 while True:
  receipt=current['receipt'];rid=record_id(receipt['record_id']);need(rid not in seen_records and receipt['release_week']==week,'LINEAGE_CYCLE_OR_WEEK');seen_records.add(rid)
  children=[x['run_id']for x in receipt['children']];need(children and len(children)==len(set(children))and not set(children)&seen_runs,'LINEAGE_SCOPE_OVERLAP')
  evidence=load(receipt['public_evidence']);context=load(evidence['public_state_context'])
  if context.get('standard')!=own.STANDARD:
   # Reject arbitrary standards; delegate only standards the old traversal knows.
   need(context.get('standard')in{successor.old.STANDARD,successor.STANDARD,successor.LEGACY_SAME_CONCEPT_STANDARD,successor.FIRST_WEEK_STANDARD},'UNKNOWN_LINEAGE_CONTEXT')
   older=successor.registered_lineage_runs(current,root=root);need(not older&seen_runs,'LINEAGE_OLD_SCOPE_OVERLAP');return seen_runs|older
  seen_runs.update(children);sources=context.get('source_bindings',{});sl=load(sources['source_legacy_receipt']);sn=load(sources['source_native_receipt']);public=load(evidence['public_native_receipt'])
  source=str(sl.get('response',{}).get('id'));record_id(source)
  need(sl.get('method')=='GET'and sl.get('url')==BASE+'/api/records/'+source and sl.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and sl.get('http_status')==200 and sn.get('method')=='GET'and sn.get('url')==BASE+'/api/records/'+source and sn.get('accept')==NATIVE and sn.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and sn.get('http_status')==200 and sn.get('response',{}).get('id')==source,'GENUINE_LINEAGE_SOURCE_PAIR')
  source_parent=sn['response'].get('parent',{}).get('id');actual_parent=public.get('response',{}).get('parent',{}).get('id')
  created=load(sources['creation_receipt']);first_n=load(sources['first_own_native_draft']);first_l=load(sources['first_own_legacy_draft'])
  own_scope=own.require_ownership(created,first_n,first_l,prior_ids=[source])
  if own_scope['start_kind']=='CREATE_WEEK':
   need(own_scope['record_id']==rid and own_scope['concept_id']==actual_parent and actual_parent!=source_parent,'GENUINE_FIRST_WEEK_LINEAGE_CUTOVER')
   return seen_runs
  need(source_parent==actual_parent and (parent is None or parent==actual_parent),'LINEAGE_CONCEPT');parent=actual_parent
  own_index=public.get('response',{}).get('versions',{}).get('index');source_index=sn['response'].get('versions',{}).get('index');need(type(own_index)is int and type(source_index)is int and own_index==source_index+1,'LINEAGE_VERSION_INDEX')
  matches=[x for x in ledger.get('publication_entities',[])if x.get('entity_type')=='METHODS_DIGEST_GROUP'and x.get('doi')=='10.5281/zenodo.'+source]
  need(len(matches)==1,'UNIQUE_REGISTERED_LINEAGE_SOURCE');row=matches[0];need(isinstance(row.get('registration_receipt'),dict),'REGISTERED_LINEAGE_BINDING');current=reg.require_registration(root,row['registration_receipt'],ledger)
  need(current['receipt']['record_id']==source and current['receipt']['release_week']==week,'EXACT_REGISTERED_LINEAGE_SOURCE')

def loaded_sources(root,pins):
 need(isinstance(pins,list)and len({x.get('name')for x in pins})==len(pins),'UNIQUE_SOURCE_PINS');table={x['name']:x for x in pins};modules={}
 for name in MODULES:
  need(name+'.py'in table,'SOURCE_PIN:'+name);pin=table[name+'.py'];_,data=bound(root,{k:pin[k]for k in('path','sha256')})
  if name in PINNED:need(sha(data)==PINNED[name],'UNCHANGED_CONSUMER:'+name)
  m=importlib.import_module(name);need(Path(m.__file__).resolve(strict=True)==Path(pin['path']).resolve(strict=True)and raw(m.__file__)==data,'EXACT_LOADED_SOURCE:'+name);modules[name]=m
 return modules

def config_value(root,config):
 need(root==ROOT.resolve(strict=True)and isinstance(config,dict)and set(config)==CONFIG_FIELDS
      and config['standard']==STANDARD and config['canonical_root']==str(root),'CLOSED_CONFIG')
 release=obj(root,config['release_scope']);require_release_scope(root,config,release)
 need(all(config[k]is None for k in('existing_ownership','existing_package','existing_validation')),'NO_REUSE_OR_DUPLICATE_DRAFT')
 need(config['controller']==binding(__file__),'CONTROLLER_SOURCE')
 scope=obj(root,config['source_scope_plan'])
 need(scope.get('purpose_source_pins')==config['source_pins']and scope.get('canonical_root')==str(root),'MEASURED_SOURCE_SCOPE')
 package=Path(config['package']).resolve(strict=True)
 need(package.is_relative_to(root/'RESEARCH_PIPELINE_v2/science_release_queue/digests'),'OWN_PACKAGE')
 _,rule=bound(root,config['split_rule']);need(rule.count(RULE_HEADER)==1,'SPLIT_AUTHORITY')
 need(b'One digest publication counts as one write toward the 10/day limit.'in rule
      and b'Upload attempts that fail without changing anything do not count against the daily limit.'in rule,'EXACT_ACCOUNTING_AUTHORITY')
 need(sha(raw(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))==config['expected_ssot_sha256'],'CURRENT_SSOT')
 return package

def require_release_scope(root,config,value):
 fields={'standard','canonical_root','release_week','batch_label','run_ids','predecessor_registration',
         'predecessor_record_id','concept_id','publication_route','start_kind','new_scientific_or_runtime_authority'}
 routes={'NEW_VERSION':'Existing same-concept weekly Methods Digest successor',
         'CREATE_WEEK':'First Methods Digest of an explicitly authorized new ISO week'}
 need(isinstance(value,dict)and set(value)==fields and value['standard']=='VRS-EXACT-DIGEST-RELEASE-SCOPE-2'
      and value['canonical_root']==str(root)and re.fullmatch('[0-9]{4}-W[0-9]{2}',str(value['release_week']))
      and value['batch_label']==config['batch_label']and value['predecessor_registration']==config['predecessor_registration']
      and value['start_kind']in routes and value['publication_route']==routes[value['start_kind']]
      and value['new_scientific_or_runtime_authority']is False,'EXACT_RELEASE_SCOPE')
 record_id(value['predecessor_record_id']);require_cohort(value,value['run_ids'])
 if value['start_kind']=='NEW_VERSION':record_id(value['concept_id'])
 else:need(value['concept_id']is None and value['release_week']!='2026-W41','EXPLICIT_NEW_WEEK_ONLY')
 authorization=obj(root,config['user_authorization'])
 fields={'standard','captured_at_utc','provider_instruction','provider_user_message_id','release_scope','scope_review'}
 need(isinstance(authorization,dict)and set(authorization)==fields
      and authorization['standard']=='VRS-PROVIDER-BOUND-EXACT-DIGEST-PUBLICATION-AUTHORITY-1'
      and authorization['release_scope']==config['release_scope']
      and utc(authorization['captured_at_utc'])<=utc(now()),'EXACT_PUBLICATION_AUTHORITY')
 provider=obj(root,authorization['provider_instruction'])
 need(provider.get('standard')=='VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1'
      and provider.get('provider_tool')=='mcp__codex_app__read_thread'
      and isinstance(provider.get('thread_id'),str)and isinstance(provider.get('turn_id'),str),'ACTUAL_PUBLICATION_USER_PROVIDER')
 messages=[m for m in provider.get('user_messages',[])if m.get('type')=='userMessage'
           and m.get('id')==authorization['provider_user_message_id']]
 need(len(messages)==1 and isinstance(messages[0].get('content'),list),'ACTUAL_PUBLICATION_USER_MESSAGE')
 text=''.join(c['text']for c in messages[0]['content']if c.get('type')=='text')
 need(text.strip()and text.strip()!=__import__('packaging_runtime').USER_DIRECTIVE,'PACKAGING_IS_NOT_PUBLICATION_AUTHORITY')
 review=obj(root,authorization['scope_review'])
 fields={'standard','status','reviewer','provider_instruction','provider_user_message_id','user_text',
         'release_scope','authorized_run_ids','publication_route','start_kind','scientific_admission_changed','new_runtime_authority'}
 need(set(review)==fields and review['standard']=='VRS-REVIEWED-PROVIDER-DIGEST-PUBLICATION-SCOPE-1'
      and review['status']=='EXACT_USER_INSTRUCTION_RELEASE_SCOPE_REVIEW_PASS'
      and isinstance(review['reviewer'],str)and review['reviewer']
      and review['provider_instruction']==authorization['provider_instruction']
      and review['provider_user_message_id']==authorization['provider_user_message_id']and review['user_text']==text
      and review['release_scope']==config['release_scope']and review['authorized_run_ids']==value['run_ids']
      and review['publication_route']==value['publication_route']and review['start_kind']==value['start_kind']
      and review['scientific_admission_changed']is False and review['new_runtime_authority']is False,
      'EXACT_REVIEWED_PUBLICATION_SCOPE')
 return value

def require_predecessor(scope,discovered,receipt,legacy,native):
 rid=scope['predecessor_record_id'];parent=str(legacy.get('conceptrecid'));week=scope['release_week']
 need(discovered.get('release_week')==week,'CURRENT_COMPLETE_OWN_DISCOVERY_WEEK')
 if scope['start_kind']=='NEW_VERSION':
  need(discovered.get('status')=='EXISTING_WEEKLY_RECORD'and discovered.get('record_id')==rid
       and discovered.get('concept_id')==scope['concept_id']and receipt.get('release_week')==week
       and parent==scope['concept_id'],'CURRENT_COMPLETE_OWN_DISCOVERY')
 else:
  need(discovered.get('status')=='NO_EXISTING_WEEKLY_RECORD'and discovered.get('record_id')is None
       and discovered.get('concept_id')is None and receipt.get('release_week')!=week,
       'NO_EXISTING_OR_PENDING_WEEK_AND_OTHER_WEEK_SOURCE')
 need(receipt.get('record_id')==rid and str(legacy.get('id'))==rid and native.get('id')==rid
      and native.get('parent',{}).get('id')==parent
      and legacy.get('metadata',{}).get('title')=='Viridis Methods Digest — '+receipt['release_week'],
      'PRESERVED_REGISTERED_SOURCE_IDENTITY_AND_TITLE')
 need(native.get('is_published')is True and native.get('is_draft')is False and native.get('status')=='published'
      and native.get('versions',{}).get('is_latest')is True,'PUBLISHED_LATEST_SOURCE_ONLY')
 return {'record_id':rid,'concept_id':parent,'release_week':week,'new_run_ids':scope['run_ids'],'start_kind':scope['start_kind']}


def initial_week_controls(own,source_native,payload,native_metadata,created,first_legacy,first_native,source_id):
 """Use the unchanged own CREATE_WEEK rule; no inherited files or after-derived metadata."""
 scope=own.require_ownership(created,first_native,first_legacy,prior_ids=[source_id])
 need(scope['start_kind']=='CREATE_WEEK'and scope['concept_id']!=source_native['parent']['id'],'DISTINCT_EXPLICIT_NEW_WEEK_CONCEPT')
 need(created['request_body_sha256']==sha(encoded(payload)),'EXACT_CREATION_METADATA_BODY')
 own._metadata(created['response'].get('metadata'),payload['metadata'],'CREATE_ACK')
 controls={'record_id':scope['record_id'],'concept_id':scope['concept_id'],'phase':'DRAFT',
           'native_metadata':own.native_sent_metadata(native_metadata),'legacy_metadata':deepcopy(payload['metadata']),
           'files':[],'communities':deepcopy(payload['metadata'].get('communities',[])),
           'native_community_ids':deepcopy(source_native.get('parent',{}).get('communities',{}).get('ids',[])),
           'doi_required':False}
 own.require_own_readback(first_native['response'],first_legacy['response'],controlled=controls,
                         ownership={'creation_receipt':created,'first_native_receipt':first_native,
                                    'first_legacy_receipt':first_legacy,'prior_ids':[source_id]})
 return controls

def approved_inventory(package,manifest):
 rows=manifest.get('uploads');need(isinstance(rows,list)and rows,'DECLARED_UPLOADS')
 names=[]
 for row in rows:
  name=row.get('filename');need(isinstance(name,str)and Path(name).name==name
       and name not in {'DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'}and name not in names,'UNIQUE_UPLOAD_BASENAME');names.append(name)
 names+=['DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'];result={}
 for name in names:
  data=raw(Path(package)/name)
  if name not in {'DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'}:
   row=next(r for r in rows if r['filename']==name)
   need(row.get('sha256')==sha(data)and row.get('md5')==hashlib.md5(data).hexdigest()
        and row.get('bytes')==len(data),'DECLARED_UPLOAD_BYTES')
  result[name]={'name':name,'path':str(package/name),'sha256':sha(data),'md5':hashlib.md5(data).hexdigest(),'bytes':len(data)}
 return result

def inherited_inventory(admitted):
 rows=admitted.get('public_legacy',{}).get('files');need(isinstance(rows,list),'ADMITTED_INHERITED_FILES')
 result={}
 for row in rows:
  name=row.get('key',row.get('filename'));size=row.get('size',row.get('filesize'));checksum=row.get('checksum')
  need(isinstance(name,str)and Path(name).name==name and name not in result
       and type(size)is int and size>=0 and isinstance(checksum,str),'EXACT_INHERITED_ENTRY')
  md5=checksum[4:]if checksum.startswith('md5:')else checksum
  need(re.fullmatch('[0-9a-f]{32}',md5),'INHERITED_MD5')
  result[name]={'bytes':size,'md5':md5}
 return result

class OperationJournal:
 """Reuse original index/intent/reservation format and exclusive global lock."""
 def __init__(self,root,out,modules):self.root=root;self.out=out;self.modules=modules;self.writer=None
 def __enter__(self):
  original=self.modules['mutation_journal_writer'];self.writer=original.JournalWriter(self.root,self.out,lambda *_:None,lambda *_:None);self.writer.__enter__();return self
 def __exit__(self,*args):return self.writer.__exit__(*args)
 def budget(self,at):
  events=self.modules['phase7_mutation_baseline'].require_events(self.root,at)
  return publication_budget(events,at,lambda b:obj(self.root,b),complete=True)
 def reserve(self,method,url,body,transport_path,at,operation_id):
  need(self.writer.lock_fd is not None,'JOURNAL_LOCK');own_url(url);need(method in{'POST','PUT','DELETE'}and isinstance(body,bytes)and not transport_path.exists(),'EXACT_NEW_OPERATION')
  # The original complete journal is re-consumed before EVERY mutation.
  observed=self.budget(at)
  if url.endswith('/actions/newversion'):need(observed['writes_authorized'],'DAILY_SLOT_REQUIRED_BEFORE_CREATE')
  if url.endswith('/actions/publish'):
   budget=observed;need(budget['writes_authorized'],'DAILY_PUBLICATION_LIMIT')
  else:budget={'status':'DRAFT_OPERATION_NOT_A_PUBLICATION','publication_charge':0,'old_attempt_history_preserved':True,'complete_publication_observation':observed}
  index_path=self.writer.index;before=raw(index_path);index=json.loads(before)
  need(set(index)=={'standard','status','baseline','reservations','updated_at_utc'}and index['standard']=='VRS_PHASE7_MUTATION_JOURNAL_INDEX_1'and index['status']=='ACTIVE'and isinstance(index['reservations'],list)and utc(index['updated_at_utc'])<=utc(at),'ORIGINAL_INDEX')
  folder=self.out/(f'{len(index["reservations"])+1:04d}_'+operation_id);folder.mkdir(parents=True,exist_ok=False)
  intent={'operation_id':operation_id,'method':method,'url':url,'request_body_sha256':sha(body),'transport_receipt_path':str(transport_path)};immutable(folder/'INTENDED_REQUEST.json',encoded(intent))
  reservation={'operation_id':operation_id,'method':method,'host':'zenodo.org','at_utc':at,'status':'STARTED_NO_RETRY','receipt_binding':binding(folder/'INTENDED_REQUEST.json')};immutable(folder/'RESERVATION.json',encoded(reservation));immutable(folder/'BEFORE_INDEX.json',before);immutable(folder/'PUBLICATION_ACCOUNTING.json',encoded(budget))
  index['reservations'].append(binding(folder/'RESERVATION.json'));index['updated_at_utc']=at;after=encoded(index);immutable(folder/'AFTER_INDEX.json',after)
  need(raw(index_path)==before,'JOURNAL_CAS');tmp=index_path.parent/('.split-'+operation_id+'.pending');immutable(tmp,after);need(raw(index_path)==before,'JOURNAL_CAS');os.replace(tmp,index_path)
  fd=os.open(index_path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
  need(raw(index_path)==after,'JOURNAL_READBACK');return binding(folder/'RESERVATION.json')

def run(config,output,token,*,opener=None,clock=now):
 """One packet, resumable only from its own immutable operational checkpoint.

 Original registered-ancestor and scientific guards are called directly.
 No old executor budget/machine admission is claimed. A failed mutation keeps
 its authentic reservation and receipt; no failed publication is auto-replayed.
 """
 root=ROOT.resolve(strict=True);import packaging_runtime;packaging_runtime.validate(root,config['packaging_profile'],purpose_pins=config['source_pins']);package=config_value(root,config);mods=loaded_sources(root,config['source_pins']);d=mods['methods_digest_v2'];reg_module=mods['methods_digest_registration_v3'];own=mods['own_record_comparison'];prior=mods['own_prior_record'];metadata=mods['digest_metadata'];codec=mods['first_digest_state'];successor=mods['digest_weekly_state'];transport=mods['zenodo_transport']
 need(isinstance(token,str)and len(token)>=24,'MEMORY_CREDENTIAL');out=Path(output);need(out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not any(p.is_symlink()for p in(out,*out.parents)),'OWN_OUTPUT')
 out.mkdir(parents=True,exist_ok=True)
 if not(out/'CONFIG.json').exists():immutable(out/'CONFIG.json',encoded(config))
 need(raw(out/'CONFIG.json')==encoded(config),'RESUME_CONFIG_CHANGED')
 checkpoints=sorted((out/'checkpoints').glob('*.json'))if(out/'checkpoints').exists()else[]
 state=json.loads(raw(checkpoints[-1]))if checkpoints else {'standard':STANDARD,'config':binding(out/'CONFIG.json'),'record_id':None,'concept_id':None,'ownership':None,'controlled':None,'operations':[],'metadata_put':None,'reservation_receipt':None,'pending':None,'published':False,'publication_evidence':None}
 need(state['standard']==STANDARD and state['config']==binding(out/'CONFIG.json')and state['published']is False,'OWN_NONTERMINAL_CHECKPOINT');state.setdefault('needs_upload_ack',[])
 attempt=len(list(out.glob('attempt-*')))+1;attempt_out=out/f'attempt-{attempt:04d}';attempt_out.mkdir(exist_ok=False)
 if opener is None:
  import urllib.request
  opener=mods['weekly_archive_wait'].WeeklyArchiveWait(mods['first_digest_publisher'].PacedOpener(urllib.request.build_opener(transport.NoRedirect())))
 t=transport.ZenodoTransport('zenodo.org',token,attempt_out/'transport',opener=opener);serial=len(checkpoints)
 def emit(name,value):
  data=encoded(value);need(token.encode()not in data,'NO_CREDENTIAL_IN_EVIDENCE');p=attempt_out/name;immutable(p,data);return binding(p)
 def save():
  nonlocal serial
  serial+=1;p=out/'checkpoints'/f'{serial:05d}.json';immutable(p,encoded(state));return binding(p)
 def get(rid,published=False,native=False):
  url=BASE+'/api/records/'+rid if published else BASE+('/api/records/'+rid+'/draft'if native else'/api/deposit/depositions/'+rid)
  value=t.request('GET',url,accept=NATIVE if native else'application/json');return value,binding(t.out/f'{t.sequence:03d}_GET.json')
 def prior_pair(publish=None):
  sl=obj(root,config['source_legacy_receipt'])['response'];sn=obj(root,config['source_native_before_create'])['response'];rid=str(sl['id']);l,lb=get(rid,True);n,nb=get(rid,True,True)
  created=obj(root,state['ownership']['creation_receipt'])if state['ownership']and start_kind=='NEW_VERSION'else None
  audit=prior.require_pair(l,n,sl,sn,creation=created,publish=obj(root,publish)if publish and start_kind=='NEW_VERSION'else None,preservation=mods['publication_preservation']);emit('prior/'+f'{t.sequence:03d}.json',audit);return l,n,lb,nb
 manifest,pub=d.require_publication_bound(package,root);scope=obj(root,config['release_scope']);start_kind=scope['start_kind'];need(manifest['release_week']==scope['release_week'],'CANONICAL_WEEK')
 access_sequence=0
 def access_download(rid,name):
  nonlocal access_sequence
  need(Path(name).name==name,'ACCESS_COPY_BASENAME');url=BASE+'/api/records/'+record_id(rid)+'/files/'+name+'/content';own_url(url)
  request=__import__('urllib.request',fromlist=['Request']).Request(url,headers={'Authorization':'Bearer '+token,'Accept':'*/*'})
  with t.opener.open(request,timeout=120)as response:
   need(response.status==200 and own_url(response.geturl())==own_url(url),'ACCESS_DOWNLOAD_HTTP_AND_URL');data=response.read()
  access_sequence+=1;path=attempt_out/'access-downloads'/f'{access_sequence:04d}'/name;immutable(path,data)
  emit('access-downloads/'+f'{access_sequence:04d}'+'/RECEIPT.json',{'method':'GET','url':url,'accept':'*/*','authentication':'OWNER','owner_id':'1591505','http_status':200,'bytes':len(data),'sha256':sha(data),'file':binding(path)})
  return data
 reg=mods['manuscript_access_registry'].RegistryContext(root,config['access_registry'],download=access_download,observation_context={'authentication':'OWNER','owner_id':'1591505','legacy_accept':'application/json','native_accept':NATIVE},owner_getter=lambda rid,accept:get(rid,True,accept==NATIVE)[0])
 resume_chain=None
 if state['ownership']is not None and start_kind=='NEW_VERSION':
  publication=None
  if state['pending']is not None:
   pending=state['operations'][state['pending']]
   if pending['step']=='PUBLISH'and pending['outcome']=='ACKNOWLEDGED_NOT_ADMITTED':publication=pending['transport']
  resume_chain={'baseline_legacy':config['source_legacy_receipt'],'baseline_native':config['source_native_before_create'],
                'creation':state['ownership']['creation_receipt'],'publish':publication}
 admitted=reg.require_registration(root,config['predecessor_registration'],prior_chain_receipts=resume_chain);prior_runs=registered_runs(admitted,root,reg,successor,own)if start_kind=='NEW_VERSION'else set();ids=[n['run_id']for n in manifest['notes']]
 require_cohort(scope,ids);need(not set(ids)&set(prior_runs),'DISJOINT_APPROVED_COHORT')
 sl=obj(root,config['source_legacy_receipt'])['response'];sn=obj(root,config['source_native_before_create'])['response'];source_id=str(sl['id']);need(admitted['receipt']['record_id']==source_id and (start_kind=='CREATE_WEEK'or sl['metadata']['title']==manifest['public_metadata']['title']),'EXACT_REGISTERED_PREDECESSOR')
 discovered=mods['owned_weekly_discovery'].require_discovery(obj(root,config['account_discovery']),root=root)
 require_predecessor(scope,discovered,admitted['receipt'],sl,sn)
 admitted=reg.require_registration(root,config['predecessor_registration'],views=(sl,sn));inherited=inherited_inventory(admitted)
 relation=reg.registered_relation_template(config['predecessor_registration'],root=root,source_native=sn,source_legacy=sl);payload=codec.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],sl['metadata']));native_md=metadata.native_metadata(manifest['public_metadata'],sl['metadata'],sl,sn,relation)
 inventory=approved_inventory(package,manifest);names=set(inventory)
 mods['manuscript_pdf_gate'].require_local(package,[Path(v['path'])for v in inventory.values()])
 def ownership_values():
  return {'creation_receipt':obj(root,state['ownership']['creation_receipt']),'first_native_receipt':obj(root,state['ownership']['first_own_native_draft']),'first_legacy_receipt':obj(root,state['ownership']['first_own_legacy_draft']),'prior_ids':[source_id]}
 def check_pair(l,n):return own.require_own_readback(n,l,controlled=state['controlled'],ownership=ownership_values())
 with OperationJournal(root,attempt_out/'reservations',mods)as journal:
  def operation(step,method,url,body,*,empty=False):
   need(state['pending']is None,'UNRESOLVED_OPERATION');mods['packaging_runtime'].validate(root,config['packaging_profile'],purpose_pins=config['source_pins']);d.require_publication_bound(package,root);mods['manuscript_pdf_gate'].require_local(package,[Path(v['path'])for v in inventory.values()]);at=clock();require_mutation_day(manifest,at);before=deepcopy(state['controlled']);intended=deepcopy(before)
   if step=='METADATA':intended.update(native_metadata=own.native_sent_metadata(native_md),legacy_metadata=deepcopy(payload['metadata']))
   elif step.startswith('UPLOAD:'):
    name=step[7:];intended['files']=[x for x in intended['files']if x['name']!=name]+[{'name':name,'bytes':inventory[name]['bytes'],'md5':inventory[name]['md5']}];intended['files'].sort(key=lambda x:x['name'])
   elif step.startswith('CLEANUP:'):intended['files']=[x for x in intended['files']if x['name']!=step[8:]]
   elif step=='RESERVE_DOI':intended['doi_required']=True
   elif step=='PUBLISH':intended.update(phase='PUBLISHED',legacy_metadata=own.legacy_sent_metadata(manifest['public_metadata']))
   record={'step':step,'method':method,'url':url,'body_sha256':sha(body),'reservation':None,'transport':None,'outcome':'RESERVED','before_controlled':before,'intended_controlled':intended}
   # Refresh after fallible preparation, before any reservation or write.
   at=clock();require_mutation_day(manifest,at)
   record['reservation']=journal.reserve(method,url,body,t.out/f'{t.sequence+1:03d}_{method}.json',at,f'split-{config["batch_label"]}-{attempt:04d}-{len(state["operations"]):04d}')
   state['operations'].append(record);state['pending']=len(state['operations'])-1;save()
   try:require_mutation_day(manifest,clock())
   except Hold as exc:
    # A crossed reservation remains charged and known unsent. No transport
    # receipt is invented, and this pending operation cannot be retried.
    record['outcome']='KNOWN_UNSENT_DAY_HOLD';record['error']=str(exc);save();raise
   try:
    if empty:value=t._send(method,url,body,sha(body),'application/json',True,'application/json',empty_response=True)
    else:value=t.request(method,url,body,expected_sha256=sha(body),authorized=True,content_type='application/octet-stream'if step.startswith('UPLOAD:')else'application/json',accept=NATIVE if step=='RESERVE_DOI'else'application/json')
   except Exception:
    record['transport']=binding(t.out/f'{t.sequence:03d}_{method}.json');record['outcome']='UNCERTAIN';save();raise
   record['transport']=binding(t.out/f'{t.sequence:03d}_{method}.json');record['outcome']='ACKNOWLEDGED_NOT_ADMITTED';save();return value,record['transport']
  def checked_ack(record):
   receipt=obj(root,record['transport']);need(receipt.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and receipt.get('method')==record['method']and receipt.get('url')==record['url']and receipt.get('request_body_sha256')==record['body_sha256'],'OWN_EXACT_ACK')
   value=receipt.get('response');step=record['step']
   if step.startswith('UPLOAD:'):
    name=step[7:];need(value.get('key')==name and value.get('checksum')=='md5:'+inventory[name]['md5']and value.get('size')==inventory[name]['bytes'],'EXACT_UPLOAD_ACK')
   elif step=='METADATA':own._metadata(value.get('metadata'),payload['metadata'],'PUT_ACK')
   elif step.startswith('CLEANUP:'):need(receipt.get('http_status')==204 and value=={'empty_204':True,'draft_file_removed':True},'EXACT_DELETE_ACK')
   elif step=='RESERVE_DOI':need(receipt.get('http_status')==201 and value.get('id')==state['record_id']and value.get('parent',{}).get('id')==state['concept_id']and value.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+state['record_id'],'DOI_RESERVATION')
   elif step=='PUBLISH':need(str(value.get('id'))==state['record_id']and str(value.get('conceptrecid'))==state['concept_id']and value.get('doi')=='10.5281/zenodo.'+state['record_id'],'OWN_PUBLISH_ACK');state['physical_publication_acknowledged']=True
   else:need(step==start_kind and receipt.get('http_status')==201,'KNOWN_ACK_STEP')
   return value
  def finish(audit):
   record=state['operations'][state['pending']];record['outcome']='STRICT_READBACK_PASS';record['validation']=emit('validated/'+f'{len(state["operations"]):04d}.json',audit);state['pending']=None;save()
  def finalize(published,before_binding):
   emit('MINTED_PUBLICATION_IDENTITY.json',{'record_id':state['record_id'],'doi':'10.5281/zenodo.'+state['record_id'],'published':True,'readback_pending':True})
   public_n,pnb=get(state['record_id'],True,True);public_l,plb=get(state['record_id'],True);_,_,prior_lb,prior_nb=prior_pair(published)
   controlled=deepcopy(state['controlled']);controlled.update(phase='PUBLISHED',legacy_metadata=own.legacy_sent_metadata(manifest['public_metadata']));controlled['files']=[{'name':name,'bytes':row['bytes'],'md5':row['md5']}for name,row in sorted(inventory.items())]
   own.require_own_readback(public_n,public_l,controlled=controlled,ownership=ownership_values());expected_n,expected_l=own.public_projection(controlled);expected_l['metadata']=deepcopy(manifest['public_metadata'])
   roles={'authority':config['authority'],'digest_manifest':binding(package/'DIGEST_MANIFEST.json'),'source_legacy_receipt':config['source_legacy_receipt'],'source_native_receipt':config['source_native_receipt'],**state['ownership'],'metadata_payload':emit('METADATA_PAYLOAD.json',payload),'metadata_put_receipt':state['metadata_put'],'relation_template':emit('RELATION_TEMPLATE.json',relation),'reservation_receipt':state['reservation_receipt'],'before_publish_native_receipt':before_binding,'publish_receipt':published,'prior_after_native_receipt':prior_nb,'prior_after_legacy_receipt':prior_lb}
   context=own.assemble_context(record_id=state['record_id'],source_bindings=roles);context_binding=emit('PUBLIC_STATE_CONTEXT.json',context)
   prediction=own.consume_context(context,load=lambda x:obj(root,x),public=manifest['public_metadata'],evidence_sources={'source_legacy_receipt':config['source_legacy_receipt'],'source_native_receipt':config['source_native_receipt'],'own_publish_receipt':published});need(encoded(prediction['native'])==encoded(expected_n)and encoded(prediction['legacy'])==encoded(expected_l),'INDEPENDENT_PUBLIC_PREDICTION')
   downloads=[]
   def download(file,rid):
    need(rid==state['record_id']and file['key']in inventory,'OWN_DOWNLOAD');url=file['links']['self'];path=own_url(url);need(path in{'/api/records/'+rid+'/files/'+file['key'],'/api/records/'+rid+'/files/'+file['key']+'/content'},'OWN_FILE_URL')
    request=__import__('urllib.request',fromlist=['Request']).Request(url,headers={'Authorization':'Bearer '+token,'Accept':'*/*'})
    with t.opener.open(request,timeout=120)as response:need(response.status==200,'PUBLIC_DOWNLOAD_HTTP');data=response.read()
    p=attempt_out/'downloads'/file['key'];immutable(p,data);downloads.append({'filename':file['key'],'binding':binding(p),'url':url});return data
   own_receipt={'record_id':state['record_id'],'doi':'10.5281/zenodo.'+state['record_id'],'method':'POST','url':obj(root,published)['url'],'status':obj(root,published)['status']}
   strict=d.strict_readback(package,root,public_l,own_receipt,download,expected_record=expected_l,metadata_consumer=lambda actual,expected,receipt:own.require_own_readback(public_n,actual,controlled=controlled,ownership=ownership_values()));strict_binding=emit('STRICT_DIGEST_READBACK.json',strict)
   evidence=reg_module.assemble_evidence(manifest=manifest,record_id=state['record_id'],public_legacy_receipt=plb,public_native_receipt=pnb,own_publish_receipt=published,expected_legacy=emit('EXPECTED_PUBLIC_LEGACY.json',expected_l),expected_native=emit('EXPECTED_PUBLIC_NATIVE.json',expected_n),source_legacy_receipt=config['source_legacy_receipt'],source_native_receipt=config['source_native_receipt'],relation_template=roles['relation_template'],server_context=emit('SERVER_CONTEXT.json',{'operation':start_kind,'phase':'PUBLISHED'}),downloads=downloads,strict_readback_result=strict_binding,public_state_context=context_binding);evidence_binding=emit('METHODS_DIGEST_PUBLIC_EVIDENCE.json',evidence)
   registration=reg_module.prepare_registration(root,package,evidence_binding);registration_binding=emit('METHODS_DIGEST_REGISTRATION_RECEIPT.json',registration);reg.require_registration(root,registration_binding)
   standalone=mods['manuscript_pdf_gate'].require_public(mods['manuscript_pdf_gate'].public_record(state['record_id']),mods['manuscript_pdf_gate'].require_local(package,[Path(v['path'])for v in inventory.values()]));standalone_binding=emit('ANONYMOUS_STANDALONE_PDF_READBACK.json',standalone)
   finish({'standalone_pdf_readback':standalone_binding,'strict_readback':strict_binding,'public_evidence':evidence_binding,'registration_receipt':registration_binding});state['controlled']=controlled;state['published']=True;state['publication_evidence']=evidence_binding;state['package']=str(package);state['registration_receipt']=registration_binding;state['strict_readback']=strict_binding;checkpoint=save()
   result={'standard':STANDARD,'status':'PUBLISHED_STRICT_READBACK_PASS','canonical_root':str(root),'config':binding(out/'CONFIG.json'),'package':str(package),'digest_manifest':binding(package/'DIGEST_MANIFEST.json'),'publication_binding':binding(package/'PUBLICATION_BINDING.json'),'batch_label':config['batch_label'],'release_week':manifest['release_week'],'run_ids':ids,'record_id':state['record_id'],'concept_id':state['concept_id'],'doi':'10.5281/zenodo.'+state['record_id'],'published':True,'public_evidence':evidence_binding,'registration_receipt':registration_binding,'strict_readback':strict_binding,'public_native_receipt':pnb,'public_legacy_receipt':plb,'own_publish_receipt':published,'downloads':downloads,'checkpoint':checkpoint,'source_pins':config['source_pins'],'controller':config['controller'],'source_scope_plan':config['source_scope_plan'],'ssot_writes':0,'certificates_issued':0,'certifies':False}
   loaded_sources(root,config['source_pins']);need(sha(raw(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))==config['expected_ssot_sha256'],'FINAL_SSOT_RACE');candidate=deepcopy(result);candidate['status']='PUBLISHED_STRICT_READBACK_PASS_PENDING_SOURCE_SESSION_EXIT';emit('READBACK_RESULT.json',candidate);return result
  try:
   if state['pending']is not None:
    pending=state['operations'][state['pending']]
    if pending['step']=='PUBLISH'and pending['outcome']=='ACKNOWLEDGED_NOT_ADMITTED':
     checked_ack(pending);post=Path(pending['transport']['path']);before=post.parent/f'{int(post.name[:3])-1:03d}_GET.json';return finalize(pending['transport'],binding(before))
   if state['record_id']is None:
    if config['existing_ownership']is not None:
     need(False,'LEGACY_DRAFT_REUSE_FORBIDDEN')
     old_package=Path(config['existing_package']);d.require_publication_bound(old_package,root);roles=config['existing_ownership'];need(set(roles)=={'creation_receipt','first_own_native_draft','first_own_legacy_draft'},'OWNERSHIP_ROLES')
     proof=own.require_ownership(obj(root,roles['creation_receipt']),obj(root,roles['first_own_native_draft']),obj(root,roles['first_own_legacy_draft']),prior_ids=[source_id]);need(proof['record_id']=='23246368','REUSE_EXACT_EXISTING_DRAFT')
     state.update(record_id=proof['record_id'],concept_id=proof['concept_id'],ownership=roles)
     old=obj(root,config['existing_validation']);need(old.get('record_id')==state['record_id']and old.get('standard')=='VRS-OWNED-DIGEST-FULL-READBACK-1','GENUINE_PRIOR_DRAFT_VALIDATION')
     expected=old['expected_native'];legacy=old['expected_legacy'];files=[{'name':name,'bytes':entry['size'],'md5':entry['checksum'][4:]}for name,entry in expected['files']['entries'].items()]
     state['controlled']={'record_id':state['record_id'],'concept_id':state['concept_id'],'phase':'DRAFT','native_metadata':own.native_sent_metadata(expected['metadata']),'legacy_metadata':deepcopy(legacy['metadata']),'files':sorted(files,key=lambda v:v['name']),'communities':codec.community_request(json.loads(raw(old_package/'DIGEST_MANIFEST.json'))['public_metadata'].get('communities',[])),'native_community_ids':deepcopy(sn.get('parent',{}).get('communities',{}).get('ids',[])),'doi_required':False}
     l,lb=get(state['record_id']);n,nb=get(state['record_id'],native=True);audit=check_pair(l,n);prior_pair();emit('INITIAL_OWNED_DRAFT.json',{'legacy_get':lb,'native_get':nb,'original_validation':config['existing_validation'],'audit':audit});save()
    else:
     need(config['existing_validation']is None and config['existing_package']is None,'NO_INVENTED_EXISTING_DRAFT');prior_pair()
     if state['pending']is not None:
      pending=state['operations'][state['pending']];need(pending['step']==start_kind and pending['outcome']=='ACKNOWLEDGED_NOT_ADMITTED','NO_DUPLICATE_VERSION');created=pending['transport'];value=checked_ack(pending)
     else:
      # Re-enumerate both complete owner pages immediately before starting;
      # saved account discovery alone never creates another weekly concept.
      fresh=mods['owned_weekly_discovery'].capture(root,scope['release_week'],token,attempt_out/'fresh-start-account',t.opener)
      require_predecessor(scope,mods['owned_weekly_discovery'].require_discovery(obj(root,fresh),root=root),admitted['receipt'],sl,sn)
      url=BASE+'/api/deposit/depositions/'+source_id+'/actions/newversion'if start_kind=='NEW_VERSION'else BASE+'/api/deposit/depositions'
      value,created=operation(start_kind,'POST',url,b'{}'if start_kind=='NEW_VERSION'else encoded(payload))
     rid=str(value.get('id'));record_id(rid);l,lb=get(rid);n,nb=get(rid,native=True)
     roles={'creation_receipt':created,'first_own_native_draft':nb,'first_own_legacy_draft':lb};proof=own.require_ownership(obj(root,created),obj(root,nb),obj(root,lb),prior_ids=[source_id]);state.update(record_id=proof['record_id'],concept_id=proof['concept_id'],ownership=roles)
     if start_kind=='NEW_VERSION':
      initial=own.initial_projection(sl,sn,obj(root,created),obj(root,lb),obj(root,nb));state['controlled']=initial['controlled']
     else:
      state['controlled']=initial_week_controls(own,sn,payload,native_md,obj(root,created),obj(root,lb),obj(root,nb),source_id)
      state['metadata_put']=created
     finish(check_pair(l,n))
   # A mutation uncertainty is never converted to acceptance. GET-only proof
   # of no upload effect permits a fresh same-byte upload with a new receipt.
   if state['pending']is not None and state['operations'][state['pending']]['outcome']=='ACKNOWLEDGED_NOT_ADMITTED':
    pending=state['operations'][state['pending']];need(pending['step']in{'METADATA','RESERVE_DOI'}or pending['step'].startswith(('UPLOAD:','CLEANUP:')),'NO_UNKNOWN_ACK_RECOVERY');checked_ack(pending);state['controlled']=deepcopy(pending['intended_controlled'])
    if pending['step']=='METADATA':state['metadata_put']=pending['transport']
    elif pending['step'].startswith('UPLOAD:'):state['needs_upload_ack']=[x for x in state['needs_upload_ack']if x!=pending['step'][7:]]
    elif pending['step']=='RESERVE_DOI':state['reservation_receipt']=pending['transport']
    l,lb=get(state['record_id']);n,nb=get(state['record_id'],native=True);audit=check_pair(l,n);prior_pair();finish({'audit':audit,'legacy_get':lb,'native_get':nb,'own_original_ack':pending['transport'],'fresh_readback_recovery':True})
   if state['pending']is not None:
    pending=state['operations'][state['pending']];need((pending['step']in{'METADATA','PUBLISH'}or pending['step'].startswith(('UPLOAD:','CLEANUP:')) )and pending['outcome']=='UNCERTAIN','NO_AUTOMATIC_MUTATION_REPLAY')
    l,lb=get(state['record_id']);n,nb=get(state['record_id'],native=True);prior_pair()
    effect,audit=classify_draft_effect(pending['before_controlled'],pending['intended_controlled'],lambda controls:own.require_own_readback(n,l,controlled=controls,ownership=ownership_values()),own.OwnRecordHold)
    need(effect=='NO_EFFECT'or pending['step']!='PUBLISH','NO_PUBLICATION_WITHOUT_OWN_ACK');state['controlled']=deepcopy(pending['before_controlled']if effect=='NO_EFFECT'else pending['intended_controlled'])
    # Exact observed draft effect is diagnostic, not a successful old operation.
    # A metadata/file PUT still needs its own fresh same-byte ACK and readback.
    if pending['step']=='METADATA':state['metadata_put']=None
    elif pending['step'].startswith('UPLOAD:')and effect!='NO_EFFECT':state['needs_upload_ack'].append(pending['step'][7:])
    pending['effect_observation']=emit('UNCERTAIN_DRAFT_EFFECT.json',{'status':effect,'legacy_get':lb,'native_get':nb,'audit':audit,'old_outcome':'UNCERTAIN','historical_attempt_retained':True,'old_attempt_accepted':False});state['pending']=None;save()
   # Remove only exact current files whose bytes differ from this cohort.
   l,lb=get(state['record_id']);n,nb=get(state['record_id'],native=True);check_pair(l,n);prior_pair()
   for entry in sorted(l.get('files',[]),key=lambda x:x['filename']):
    name=entry['filename'];need(name in inventory or name in inherited,'UNAPPROVED_CURRENT_MAIN_FILE')
    if name not in inventory:need(entry['checksum']==inherited[name]['md5']and entry['filesize']==inherited[name]['bytes'],'EXACT_INHERITED_ACCESS_FILE')
    if name in inventory and entry['checksum']==inventory[name]['md5']and entry['filesize']==inventory[name]['bytes']:continue
    fresh_l,flb=get(state['record_id']);fresh_n,fnb=get(state['record_id'],native=True);check_pair(fresh_l,fresh_n);prior_pair();proof=own.require_ownership(**ownership_values());url=draft_cleanup_entry(fresh_l,fresh_n,entry,proof,allowed_names=set(inventory)|set(inherited))
    value,removed=operation('CLEANUP:'+name,'DELETE',url,b'',empty=True);checked_ack(state['operations'][state['pending']]);state['controlled']=deepcopy(state['operations'][state['pending']]['intended_controlled'])
    a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);need(all(f.get('id')!=entry['id']for f in a.get('files',[])),'DRAFT_FILE_REMOVAL_READBACK');finish({'audit':check_pair(a,b),'draft_only':True,'dropped_file':entry,'legacy_get':ab,'native_get':bb,'transport':removed});l=a;n=b
   if state['metadata_put']is None:
    check_pair(l,n);prior_pair();d.require_publication_bound(package,root);value,put=operation('METADATA','PUT',BASE+'/api/deposit/depositions/'+state['record_id'],encoded(payload));checked_ack(state['operations'][state['pending']]);state['controlled']=deepcopy(state['operations'][state['pending']]['intended_controlled']);state['metadata_put']=put
    a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);finish({'audit':check_pair(a,b),'legacy_get':ab,'native_get':bb,'transport':put})
   for name in sorted(names):
    a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);check_pair(a,b);prior_pair()
    files={x['filename']:x for x in a.get('files',[])}
    if name in files:
     need(files[name]['checksum']==inventory[name]['md5']and files[name]['filesize']==inventory[name]['bytes'],'EXACT_PRESENT_FILE')
     if name not in state['needs_upload_ack']:continue
    d.require_publication_bound(package,root);data=raw(package/name);need(sha(data)==inventory[name]['sha256'],'CURRENT_APPROVED_UPLOAD')
    if name=='METHODS_NOTES.zip'and start_kind=='NEW_VERSION':need(callable(getattr(t.opener,'arm',None)),'ORIGINAL_ARCHIVE_WAIT');t.opener.arm(state['record_id'],source_id,obj(root,state['ownership']['creation_receipt']),obj(root,state['ownership']['first_own_legacy_draft']),inventory[name])
    value,upload=operation('UPLOAD:'+name,'PUT',a['links']['bucket']+'/'+name,data);checked_ack(state['operations'][state['pending']]);state['controlled']=deepcopy(state['operations'][state['pending']]['intended_controlled']);state['needs_upload_ack']=[x for x in state['needs_upload_ack']if x!=name]
    a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);finish({'audit':check_pair(a,b),'legacy_get':ab,'native_get':bb,'transport':upload})
   if state['reservation_receipt']is None:
    a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);check_pair(a,b);prior_pair();value,reserved=operation('RESERVE_DOI','POST',BASE+'/api/records/'+state['record_id']+'/draft/pids/doi',b'{}');need(value.get('id')==state['record_id']and value.get('parent',{}).get('id')==state['concept_id']and value.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+state['record_id'],'DOI_RESERVATION');state['reservation_receipt']=reserved;state['controlled']['doi_required']=True;a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);finish({'audit':check_pair(a,b),'legacy_get':ab,'native_get':bb,'transport':reserved})
   d.require_publication_bound(package,root);require_publish_day(manifest['public_metadata'],clock());a,ab=get(state['record_id']);b,bb=get(state['record_id'],native=True);check_pair(a,b);prior_pair();exact_main_inventory(a,inventory);need(not state['needs_upload_ack'],'NO_MISSING_UPLOAD_ACK')
   # Causal own native GET is immediately followed by the publish POST.
   before,before_binding=get(state['record_id'],native=True);check_pair(a,before);value,published=operation('PUBLISH','POST',BASE+'/api/deposit/depositions/'+state['record_id']+'/actions/publish',b'{}');checked_ack(state['operations'][state['pending']]);save()
   return finalize(published,before_binding)
  except Exception as exc:
   checkpoint=save();ack=state.get('physical_publication_acknowledged')is True;uncertain_publish=state['pending']is not None and state['operations'][state['pending']]['step']=='PUBLISH'and state['operations'][state['pending']]['outcome']=='UNCERTAIN';result={'standard':STANDARD,'status':'PUBLISHED_READBACK_PENDING'if ack else'HOLD','error_type':type(exc).__name__,'error':str(exc),'published':True if ack else(None if uncertain_publish else False),'strict_readback_pass':False,'physical_publication_acknowledged':ack,'record_id':state['record_id'],'checkpoint':checkpoint,'config':binding(out/'CONFIG.json'),'ssot_writes':0,'certifies':False};emit('RESULT.json',result);raise

def execute(config_binding,output,token,*,opener=None,clock=now):
 """Expose terminal success only after the original measured session exits."""
 root=ROOT.resolve(strict=True);config=obj(root,config_binding)
 import packaging_runtime
 with packaging_runtime.session(root,config['packaging_profile']):
  packaging_runtime.validate(root,config['packaging_profile'],purpose_pins=config['source_pins'])
  result=run(config,output,token,opener=opener,clock=clock)
  packaging_runtime.validate(root,config['packaging_profile'],purpose_pins=config['source_pins'])
 # No final success is exposed if the original context's exit checks fail.
 need(config==obj(root,config_binding)and config['controller']==binding(__file__),'FINAL_CONFIG_SOURCE_RACE')
 result['source_session_exit_succeeded']=True;p=Path(output)/'TERMINAL_RESULT.json';immutable(p,encoded(result));return result,binding(p)

if __name__=='__main__':raise SystemExit('Explicit approved root execute(config_binding, output, memory_token) call only; no automatic execution.')
