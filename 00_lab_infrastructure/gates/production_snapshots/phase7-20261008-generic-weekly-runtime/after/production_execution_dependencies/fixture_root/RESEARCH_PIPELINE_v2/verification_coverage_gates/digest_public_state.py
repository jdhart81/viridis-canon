"""Source-bound predictions for a digest's own publish boundary; no allow-rule.

Transport success is provenance only. The normal complete native/legacy and
scientific/publication consumers remain responsible for admission.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib, json, re
from pathlib import Path

STANDARD = 'VRS-METHODS-DIGEST-PUBLIC-STATE-CONTEXT-1'
STATUS = 'SOURCE_BOUND_PUBLIC_PREDICTION'
FIELDS = {'standard', 'status', 'phase', 'record_id', 'producer_sha256', 'source_bindings'}
ROLES = {'source_legacy_receipt', 'source_native_receipt', 'before_publish_native_receipt',
         'creation_receipt', 'reservation_receipt', 'publish_receipt', 'mirror_proof'}
NATIVE_ACCEPT = 'application/vnd.inveniordm.v1+json'
MIRROR_CONDITION = 'Only addition of exactly existing public metadata.communities IDs; every other native field remains checked; decisive full public metadata readback permits description/keywords changes only'
PARENT_KEYS = {'parent', 'parent_html', 'parent_doi', 'parent_doi_html'}
THUMB_SIZES = {'10', '50', '100', '250', '750', '1200'}
LINK_PATHS = {
 'access':'/api/records/{rid}/access', 'access_grants':'/api/records/{rid}/access/grants',
 'access_links':'/api/records/{rid}/access/links', 'access_request':'/api/records/{rid}/access/request',
 'access_users':'/api/records/{rid}/access/users', 'archive':'/api/records/{rid}/files-archive',
 'archive_media':'/api/records/{rid}/media-files-archive', 'communities':'/api/records/{rid}/communities',
 'communities-suggestions':'/api/records/{rid}/communities-suggestions', 'draft':'/api/records/{rid}/draft',
 'file_modification':'/api/records/{rid}/file-modification', 'files':'/api/records/{rid}/files',
 'latest':'/api/records/{rid}/versions/latest', 'latest_html':'/records/{rid}/latest',
 'media_files':'/api/records/{rid}/media-files', 'parent':'/api/records/{parent}',
 'parent_html':'/records/{parent}', 'preview_html':'/records/{rid}?preview=1',
 'quota_increase':'/api/records/{rid}/quota-increase', 'request_deletion':'/api/records/{rid}/request-deletion',
 'requests':'/api/records/{rid}/requests', 'reserve_doi':'/api/records/{rid}/draft/pids/doi',
 'self':'/api/records/{rid}', 'self_html':'/records/{rid}',
 'self_iiif_manifest':'/api/iiif/record:{rid}/manifest',
 'self_iiif_sequence':'/api/iiif/record:{rid}/sequence/default',
 'versions':'/api/records/{rid}/versions',
}

class PublicStateHold(ValueError): pass

def require(condition, reason):
 if not condition: raise PublicStateHold(reason)

def exact(left,right):
 """Preserve the original serializer's JSON type-sensitive equality."""
 return json.dumps(left,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))==json.dumps(right,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))


def identifier(value):
 require(isinstance(value,str) and re.fullmatch('[1-9][0-9]*',value) is not None, 'canonical record ID required')
 return value

def source_sha(): return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

def canonical_links(rid, parent):
 """The exact existing 33-key template shape; unknown links are not ignored."""
 identifier(rid);identifier(parent);require(rid!=parent,'record and parent must differ')
 links={k:'https://zenodo.org'+v.format(rid=rid,parent=parent) for k,v in LINK_PATHS.items()}
 for key,target in (('doi',rid),('self_doi',rid),('parent_doi',parent)):
  links[key]='https://doi.org/10.5281/zenodo.'+target
 for key,target in (('self_doi_html',rid),('parent_doi_html',parent)):
  links[key]='https://zenodo.org/doi/10.5281/zenodo.'+target
 links['thumbnails']={s:'https://zenodo.org/api/iiif/record:'+rid+':paper.pdf/full/%5E'+s+',/0/default.jpg' for s in THUMB_SIZES}
 return links

def community_fields(public, source_legacy, source_native, before_native):
 source=source_native.get('custom_fields',{})
 require(isinstance(source,dict) and not set(source)-{'legacy:communities'},'unapproved source custom fields')
 require(exact(before_native.get('custom_fields',{}),source),'own draft custom fields differ from exact source')
 communities=source_legacy.get('metadata',{}).get('communities',[])
 require(exact(public.get('communities',[]),communities),'public membership differs from existing source')
 graph=source_native.get('parent',{}).get('communities',{})
 require(exact(before_native.get('parent',{}).get('communities',{}),{}),'own draft community graph must be empty')
 if not communities:
  require(source=={} and graph=={},'empty membership cannot remove a legacy mirror')
  return {},{}
 require(isinstance(communities,list) and all(isinstance(c,dict) and set(c)=={'id'} and isinstance(c['id'],str) and c['id'] for c in communities),'closed existing community IDs required')
 slugs=[c['id'] for c in communities]
 require(len(set(slugs))==len(slugs) and source=={'legacy:communities':slugs},'source legacy mirror differs from unique existing membership')
 require(isinstance(graph,dict) and set(graph)=={'default','ids','entries'},'closed source community graph required')
 ids=graph['ids'];entries=graph['entries']
 require(isinstance(ids,list) and len(ids)==len(slugs) and len(set(ids))==len(ids) and all(isinstance(x,str) and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',x) for x in ids),'unique source community UUIDs required')
 require(graph['default'] in ids and isinstance(entries,list) and len(entries)==len(ids),'source graph default/entries differ')
 require(all(isinstance(e,dict) for e in entries) and [e.get('id') for e in entries]==ids and [e.get('slug') for e in entries]==slugs,'source community UUID/slug association differs')
 return {},deepcopy(graph)

def legacy_relation(source_legacy,source_native,own_native):
 """Zenodo's existing legacy ordinal is exactly native ordinal minus one."""
 source_index=source_native.get('versions',{}).get('index');source_parent=source_native.get('parent',{}).get('id')
 own_index=own_native.get('versions',{}).get('index');own_parent=own_native.get('parent',{}).get('id')
 require(type(source_index)is int and source_index>=1 and type(own_index)is int and own_index>=1,'positive integer native ordinal required')
 identifier(source_parent);identifier(own_parent)
 relation=source_legacy.get('metadata',{}).get('relations',{})
 require(isinstance(relation,dict) and set(relation)=={'version'} and isinstance(relation['version'],list) and len(relation['version'])==1,'closed existing version relation required')
 row=relation['version'][0]
 require(isinstance(row,dict) and set(row)=={'index','is_last','parent'} and type(row['index'])is int and row['index']>=0,'closed integer legacy ordinal required')
 require(row['index']==source_index-1 and row['is_last'] is source_native.get('versions',{}).get('is_latest') and type(row['is_last'])is bool,'legacy/native offset must be exactly one')
 require(row['parent']=={'pid_type':'recid','pid_value':source_parent} and str(source_legacy.get('conceptrecid'))==source_parent,'source relation parent differs')
 require(own_native.get('versions',{}).get('is_latest') is True,'own predicted publish must be latest')
 return {'version':[{'index':own_index-1,'is_last':True,'parent':{'pid_type':'recid','pid_value':own_parent}}]}

def receipt(value, *,method,url,accept=None):
 require(isinstance(value,dict) and value.get('environment')=='zenodo.org' and value.get('method')==method and value.get('url')==url and value.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE' and type(value.get('http_status'))is int and 200<=value['http_status']<300 and isinstance(value.get('response'),dict) and re.fullmatch('[0-9a-f]{64}',str(value.get('response_sha256'))) is not None,'successful source-bound own transport receipt required')
 if method!='GET':require(re.fullmatch('[0-9a-f]{64}',str(value.get('request_body_sha256'))) is not None,'own mutation body hash required')
 if accept is not None:require(value.get('accept')==accept,'native representation required')
 return value['response']

def predict_native(public,source_legacy,source_native,before,created,reserved,published):
 """Only existing private→public projections plus source-bound public families."""
 rid=identifier(before.get('id'));parent=identifier(before.get('parent',{}).get('id'));doi='10.5281/zenodo.'+rid;concept='10.5281/zenodo.'+parent
 require(rid!=parent and str(created.get('id'))==rid and str(created.get('conceptrecid'))==parent,'own creation identity/parent differs')
 require(exact(created.get('metadata',{}).get('prereserve_doi'),{'doi':doi,'recid':int(rid)}),'own creation DOI preregistration differs')
 require(before.get('is_draft') is True and before.get('is_published') is False and before.get('status')=='draft','actual private prepublish state required')
 require(reserved.get('id')==rid and reserved.get('parent',{}).get('id')==parent and reserved.get('pids',{}).get('doi')=={'identifier':doi,'provider':'datacite','client':'datacite'},'same-own native DOI reservation differs')
 require(exact(before.get('pids',{}).get('doi'),reserved['pids']['doi']),'own before DOI differs from actual reservation')
 require(str(published.get('id'))==rid and published.get('state')=='done' and published.get('submitted') is True and published.get('doi')==doi and published.get('conceptdoi')==concept and str(published.get('conceptrecid'))==parent,'own terminal publish identity/DOI/parent differs')
 src=identifier(source_native.get('id'));src_parent=identifier(source_native.get('parent',{}).get('id'))
 require(src!=rid and src_parent!=parent and str(source_legacy.get('id'))==src and source_native.get('is_published') is True and source_native.get('is_draft') is False,'distinct existing public source pair required')
 require(source_native.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+src and source_legacy.get('doi')=='10.5281/zenodo.'+src,'source DOI pair differs')
 source_links=source_native.get('links');template=canonical_links(src,src_parent)
 require(isinstance(source_links,dict),'source public links object required')
 if 'thumbnails' not in source_links:template.pop('thumbnails')
 require(source_links==template and source_legacy.get('links')==source_links,'unknown, foreign or differing source public link template')
 custom,graph=community_fields(public,source_legacy,source_native,before)
 # Preserve the established executor's private→public projection exactly.
 expected=deepcopy(before);expected.update(is_draft=False,is_published=True,status='published')
 expected['parent']['pids']={'doi':{'identifier':concept,'provider':'datacite','client':'datacite'}}
 for entry in expected['files']['entries'].values():
  require(isinstance(entry,dict) and isinstance(entry.get('key'),str),'closed own file entry required')
  entry['links']=deepcopy(entry.get('links',{}));entry['links'].update(self='https://zenodo.org/api/records/'+rid+'/files/'+entry['key'],content='https://zenodo.org/api/records/'+rid+'/files/'+entry['key']+'/content')
 expected['links']=canonical_links(rid,parent);expected['links'].pop('thumbnails')
 before_links=before.get('links',{})
 require(isinstance(before_links,dict),'own before links object required')
 if 'thumbnails' in before_links:
  thumbs=before_links['thumbnails']
  require(isinstance(thumbs,dict) and thumbs and all(isinstance(k,str) and k for k in thumbs),'own before thumbnail map required')
  # Reuse the unchanged approved preview URL predicate, including exact own ID
  # and current source key. A source paper's thumbnails are never transplanted.
  from server_managed_fields import _preview_url
  for url in thumbs.values():_preview_url(url,host='zenodo.org',record_id=rid,allowed_keys={'paper.pdf'})
  pdf=before['files']['entries'].get('paper.pdf')
  require(isinstance(pdf,dict) and pdf.get('key')=='paper.pdf' and type(pdf.get('size')) is int and pdf['size']>=0 and isinstance(pdf.get('id'),str) and pdf['id'] and re.fullmatch('md5:[0-9a-f]{32}',str(pdf.get('checksum'))) is not None,'own before thumbnail main-file inventory required')
  expected['links']['thumbnails']=deepcopy(thumbs)
 expected['custom_fields']=custom;expected['parent']['communities']=graph
 if 'oai' in source_native.get('pids',{}):
  require(source_native['pids']['oai']=={'identifier':'oai:zenodo.org:'+src,'provider':'oai'},'source OAI identifier/provider differs')
  require('oai' not in before['pids'],'own draft unexpectedly already carries OAI')
  expected['pids']['oai']={'identifier':'oai:zenodo.org:'+rid,'provider':'oai'}
 # Do not admit a native ordinal or parent by reading the current after body.
 legacy_relation(source_legacy,source_native,{**expected,'versions':{**expected.get('versions',{}),'is_latest':True}})
 return expected

def assemble_context(*,record_id,source_legacy_receipt,source_native_receipt,
 before_publish_native_receipt,creation_receipt,reservation_receipt,publish_receipt,mirror_proof):
 rid=identifier(record_id);sources={k:v for k,v in locals().copy().items() if k in ROLES}
 require(set(sources)==ROLES,'complete public prediction sources required')
 for value in sources.values():
  require(isinstance(value,dict) and set(value)=={'path','sha256'} and isinstance(value['path'],str) and re.fullmatch('[0-9a-f]{64}',str(value['sha256'])) is not None,'closed public prediction source binding required')
 return {'standard':STANDARD,'status':STATUS,'phase':'PUBLISHED','record_id':rid,'producer_sha256':source_sha(),'source_bindings':deepcopy(sources)}

def consume_context(context, *,load, public, evidence_sources):
 """Read every exact bound source through the registrar's snapshot consumer."""
 require(isinstance(context,dict) and set(context)==FIELDS and context['standard']==STANDARD and context['status']==STATUS and context['phase']=='PUBLISHED' and context['producer_sha256']==source_sha(),'current closed public prediction context required')
 rid=identifier(context['record_id']);sources=context['source_bindings']
 require(isinstance(sources,dict) and set(sources)==ROLES,'closed public prediction source roles required')
 for role in ('source_legacy_receipt','source_native_receipt','publish_receipt'):
  key='own_publish_receipt' if role=='publish_receipt' else role
  require(sources[role]==evidence_sources[key],'public context/evidence source differs: '+role)
 objects={role:load(binding) for role,binding in sources.items()}
 source_id=str(objects['source_legacy_receipt'].get('response',{}).get('id'))
 source_legacy=receipt(objects['source_legacy_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id)
 source_native=receipt(objects['source_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id,accept=NATIVE_ACCEPT)
 before=receipt(objects['before_publish_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE_ACCEPT)
 created=receipt(objects['creation_receipt'],method='POST',url='https://zenodo.org/api/deposit/depositions')
 reserved=receipt(objects['reservation_receipt'],method='POST',url='https://zenodo.org/api/records/'+rid+'/draft/pids/doi',accept=NATIVE_ACCEPT)
 published=receipt(objects['publish_receipt'],method='POST',url='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish')
 # Bind the actual final pre-publish GET and its own immediately following POST,
 # not a content-identical earlier private readback with a different causal role.
 bp=Path(sources['before_publish_native_receipt']['path']);pp=Path(sources['publish_receipt']['path'])
 bm=re.fullmatch('([0-9]{3})_GET[.]json',bp.name);pm=re.fullmatch('([0-9]{3})_POST[.]json',pp.name)
 require(bp.parent==pp.parent and bm is not None and pm is not None and int(pm[1])==int(bm[1])+1,'same-operation final prepublish GET→POST provenance required')
 mirror=objects['mirror_proof']
 require(isinstance(mirror,dict) and mirror.get('status')=='SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN' and mirror.get('field')=='custom_fields.legacy:communities' and mirror.get('condition')==MIRROR_CONDITION and mirror.get('public_post_publish_exact_preservation') is True and type(mirror.get('production_writes_in_test')) is int and mirror['production_writes_in_test']==0,'decisive tested existing community mirror proof required')
 require(isinstance(mirror.get('checks'),dict) and set(mirror['checks'])=={'communities','conceptdoi','conceptrecid','doi','files','native_membership'} and all(type(v)is bool and v is True for v in mirror['checks'].values()),'complete tested mirror preservation checks required')
 tested=mirror.get('existing_public_communities')
 require(mirror.get('before_custom_fields')=={} and isinstance(tested,list) and tested and all(isinstance(x,dict) and set(x)=={'id'} and isinstance(x['id'],str) and x['id'] for x in tested) and mirror.get('after_custom_fields')=={'legacy:communities':[x['id'] for x in tested]} and re.fullmatch('[0-9a-f]{64}',str(mirror.get('transport_sha256'))) is not None,'source-bound tested pure mirror addition required')
 native=predict_native(public,source_legacy,source_native,before,created,reserved,published)
 relation=legacy_relation(source_legacy,source_native,{**native,'versions':{**native['versions'],'is_latest':True}})
 return {'record_id':rid,'native':native,'legacy_relation':relation,'source_legacy':source_legacy,'source_native':source_native,'before_native':before}

def require_native_audit(report,*,record_id,sm):
 """The real server consumer's terminal contract, never a generic PASS flag."""
 extra={'record_identity','own_publish_scope','revision_id','deletion_status','expires_at','swh','ui.is_draft','ui_display_fields','derived_previews','content_metadata','unlisted_fields'}
 names=set(sm.ALLOW_LIST)|extra
 require(isinstance(report,dict) and report.get('status')=='SERVER_MANAGED_READBACK_PASS' and report.get('reasons')==[] and report.get('record_id')==record_id and report.get('operation')=='NEW_VERSION' and report.get('phase')=='PUBLISHED','exact complete native audit terminal required')
 checks=report.get('checks')
 require(isinstance(checks,dict) and set(checks)==names and all(isinstance(row,dict) and row.get('status')=='PASS' for row in checks.values()),'all named native audit rows must pass')


def checked_public_links(checked_native):
 """Derived previews mirror the fully audited native, never an untested flag.

The caller must first run the unchanged full native audit with its source-bound
preview context. Every non-derived link remains exactly source-predicted.
"""
 rid=identifier(checked_native.get('id'));parent=identifier(checked_native.get('parent',{}).get('id'))
 links=checked_native.get('links');require(isinstance(links,dict),'checked native links object required')
 ordinary=deepcopy(links);ordinary.pop('thumbnails',None)
 template=canonical_links(rid,parent);template.pop('thumbnails')
 require(ordinary==template,'checked native non-derived link template differs')
 return deepcopy(links)


def predict_legacy(source_legacy,checked_native,public_metadata):
 """Existing serializer coupling, called only after the full native audit.

Scientific metadata remains the manifest's input. Only its existing scalar and
file-UUID representation is taken from the already completely checked native.
"""
 fields={'conceptdoi','conceptrecid','created','doi','doi_url','files','id','links','metadata','modified','owners','recid','revision','state','stats','status','submitted','swh','title','updated'}
 required={'conceptdoi','conceptrecid','created','doi','doi_url','files','id','links','metadata','modified','owners','recid','revision','stats','title'}
 require(set(source_legacy)<=fields and required<=set(source_legacy),'closed existing legacy public schema required')
 rid=identifier(checked_native.get('id'));parent=identifier(checked_native.get('parent',{}).get('id'))
 doi='10.5281/zenodo.'+rid;concept='10.5281/zenodo.'+parent
 owner=checked_native['parent']['access']['owned_by']['user']
 require(source_legacy['owners']==[{'id':owner}],'existing public owner shape differs')
 links=checked_public_links(checked_native)
 values={'conceptdoi':concept,'conceptrecid':parent,'created':checked_native['created'],'doi':doi,'doi_url':'https://doi.org/'+doi,'id':int(rid),'metadata':deepcopy(public_metadata),'modified':checked_native['updated'],'owners':deepcopy(source_legacy['owners']),'recid':rid,'revision':checked_native['revision_id'],'title':public_metadata['title'],'updated':checked_native['updated'],'state':'done','status':'published','submitted':True,'swh':deepcopy(checked_native.get('swh',{})),'links':links,'stats':{}}
 result={k:deepcopy(values[k]) for k in source_legacy if k!='files'}
 result['metadata']['doi']=doi
 result['files']=[{'id':r['id'],'key':r['key'],'checksum':r['checksum'],'size':r['size'],'links':{'self':'https://zenodo.org/api/records/'+rid+'/files/'+r['key']+'/content'}} for r in (checked_native['files']['entries'][key]for key in sorted(checked_native['files']['entries']))]
 return result

def require_legacy(actual,expected,checked_native,*,source_legacy,source_native,sm,preservation,native_expected,server_context):
 """Complete original legacy guards with an explicit source-derived link baseline."""
 rid=identifier(checked_native.get('id'));parent=identifier(checked_native.get('parent',{}).get('id'))
 require(isinstance(server_context,dict) and server_context.get('operation')=='NEW_VERSION' and server_context.get('phase')=='PUBLISHED','complete own public server context required')
 audit=sm.audit_readback(checked_native,native_expected,host='zenodo.org',record_id=rid,**server_context)
 require_native_audit(audit,record_id=rid,sm=sm)
 source_id=identifier(source_native.get('id'));source_parent=identifier(source_native.get('parent',{}).get('id'))
 source_links=source_native.get('links');template=canonical_links(source_id,source_parent)
 if isinstance(source_links,dict) and 'thumbnails' not in source_links:template.pop('thumbnails')
 require(source_legacy.get('links')==source_links==template,'legacy/native existing public link templates differ')
 links=checked_public_links(checked_native)
 require(expected.get('links')==links and actual.get('links')==links,'own public legacy/native links differ from exact existing template')
 require(expected.get('metadata',{}).get('relations')==legacy_relation(source_legacy,source_native,checked_native),'expected legacy ordinal/parent differs')
 preservation.require_public_metadata(actual.get('metadata',{}),expected['metadata'])
 preservation.require_file_preservation(actual.get('files'),expected['files'])
 left,right=deepcopy(actual),deepcopy(expected)
 for key in ('metadata','files','links','stats'):left.pop(key,None);right.pop(key,None)
 require(exact(left,right),'public legacy unlisted or content field changed')
 sm.require_links_stats({'links':actual.get('links',{}),'stats':actual.get('stats',{}),'pids':checked_native['pids']},{'links':links,'stats':{}},host='zenodo.org',record_id=rid)
 return {'status':'STRICT_COMPLETE_PUBLIC_LEGACY_PASS','record_id':rid,'all_source_and_remaining_fields_exact':True}


# Closed ordinary same-concept integration. All original helpers above remain
# byte-faithful; old producer identities are consumed by exact archived bytes.
_consume_context_source_original = consume_context
_community_fields_source_original = community_fields
_LEGACY_PUBLIC_SOURCE_SHA = 'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38'

def consume_context(context, *,load,public,evidence_sources):
 import digest_successor_state as successor
 if isinstance(context,dict)and context.get('standard')==successor.STANDARD:
  return successor.consume_context(context,load=load,public=public,evidence_sources=evidence_sources)
 if isinstance(context,dict)and context.get('standard')==STANDARD and context.get('producer_sha256')==_LEGACY_PUBLIC_SOURCE_SHA:
  import digest_public_state_legacy_b5545 as legacy
  require(legacy.source_sha()==_LEGACY_PUBLIC_SOURCE_SHA,'exact historical public-state producer bytes required')
  return legacy.consume_context(context,load=load,public=public,evidence_sources=evidence_sources)
 return _consume_context_source_original(context,load=load,public=public,evidence_sources=evidence_sources)

def community_fields(public,source_legacy,source_native,before_native):
 if source_native.get('parent',{}).get('id')==before_native.get('parent',{}).get('id') and source_native.get('id')!=before_native.get('id'):
  import digest_successor_state as successor
  return successor.community_fields(public,source_legacy,source_native,before_native)
 return _community_fields_source_original(public,source_legacy,source_native,before_native)
