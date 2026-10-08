"""Closed source-derived same-concept digest constructors; never acceptance.

The unchanged complete native/legacy/scientific consumers admit every output.
The predecessor's default registration and newly bound digest manifest are
mandatory. No after body supplies scientific metadata, parent, owner, ordinal
or inherited main-file bytes. Transport provenance is never certification.
"""
from copy import deepcopy
from pathlib import Path
import hashlib,json,re
import digest_public_state_legacy_b5545 as old
STANDARD='VRS-METHODS-DIGEST-SAME-CONCEPT-SUCCESSOR-CONTEXT-1'
STATUS=old.STATUS
FIELDS=old.FIELDS
ROLES=old.ROLES|{'source_native_before_create','first_own_native_draft','first_own_legacy_draft','predecessor_registration','successor_digest_manifest'}
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
OLD_SEVEN={'Run-125','Run-126','Run-128','Run-129','Run-131','Run-134','Run-141'}
NEW_49={'Run-127','Run-130'}|{'Run-'+str(i)for i in range(140,189)if i not in(141,142)}
require=old.require;exact=old.exact;identifier=old.identifier
NATIVE_ACCEPT=old.NATIVE_ACCEPT
MIRROR_CONDITION=old.MIRROR_CONDITION

def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def canonical(raw):return json.dumps(raw,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))
def community_fields(public,source_legacy,source_native,before_native):
    """Preserve a completely checked same-parent published community graph."""
    parent=identifier(source_native.get('parent',{}).get('id'))
    require(before_native.get('parent',{}).get('id')==parent and before_native.get('id')!=source_native.get('id'),'same distinct-child concept required')
    source=source_native.get('custom_fields',{})
    require(isinstance(source,dict)and not set(source)-{'legacy:communities'},'unapproved source custom fields')
    require(exact(before_native.get('custom_fields',{}),source),'own draft custom fields differ from exact source')
    communities=source_legacy.get('metadata',{}).get('communities',[])
    require(exact(public.get('communities',[]),communities),'public membership differs from existing source')
    graph=source_native.get('parent',{}).get('communities',{})
    require(exact(before_native.get('parent',{}).get('communities',{}),graph),'same-parent community graph changed')
    if not communities:
        require(source=={}and graph=={},'empty membership cannot remove a source graph');return {},{}
    require(isinstance(communities,list)and all(isinstance(c,dict)and set(c)=={'id'}and isinstance(c['id'],str)and c['id']for c in communities),'closed existing community IDs required')
    slugs=[c['id']for c in communities]
    require(len(slugs)==len(set(slugs))and(source=={}or source=={'legacy:communities':slugs}),'exact source mirror or published empty custom object required')
    require(isinstance(graph,dict)and set(graph)=={'default','ids','entries'},'closed source community graph required')
    ids=graph['ids'];entries=graph['entries']
    require(isinstance(ids,list)and len(ids)==len(slugs)and len(set(ids))==len(ids)and all(isinstance(v,str)and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',v)for v in ids),'unique source community UUIDs required')
    require(graph['default']in ids and isinstance(entries,list)and len(entries)==len(ids),'source graph default/entries differ')
    require(all(isinstance(e,dict)for e in entries)and[e.get('id')for e in entries]==ids and[e.get('slug')for e in entries]==slugs,'source community UUID/slug association differs')
    owner=source_native.get('parent',{}).get('access',{}).get('owned_by')
    require(isinstance(owner,dict)and set(owner)=={'user'}and exact(before_native.get('parent',{}).get('access',{}).get('owned_by'),owner),'same-parent source owner changed')
    return {},deepcopy(graph)

def private_metadata_projection(payload,response,native_metadata):
    """Reuse the unchanged request→private codec; no after metadata baseline."""
    from first_digest_state import private_metadata_expected
    return private_metadata_expected(payload,response,native_metadata)

def _inherited(source,created,rid):
    rows=created.get('files');entries=source.get('files',{}).get('entries')
    require(isinstance(rows,list)and isinstance(entries,dict)and len(rows)==len(entries),'complete inherited file set required')
    names=[r.get('filename')for r in rows]
    require(all(isinstance(n,str)and n for n in names)and len(names)==len(set(names))and set(names)==set(entries),'unique exact inherited names required')
    expected={}
    for row in rows:
        name=row['filename'];src=entries[name]
        require(set(row)=={'id','filename','filesize','checksum','links'},'closed inherited ACK file schema')
        require(src.get('key')==name and row['id']==src.get('id')and type(row['filesize'])is int and row['filesize']==src.get('size')and 'md5:'+row['checksum']==src.get('checksum'),'inherited UUID/bytes differ from source')
        require(row['links']=={'self':'https://zenodo.org/api/deposit/depositions/'+rid+'/files/'+row['id'],'download':'https://zenodo.org/api/records/'+rid+'/draft/files/'+name+'/content'},'inherited own draft links differ')
        expected[name]=deepcopy(src)
        expected[name]['links']=deepcopy(src.get('links',{}))
        for key in('self','content'):
            expected[name]['links'][key]='https://zenodo.org/api/records/'+rid+'/draft/files/'+name+('/content'if key=='content'else'')
        # Other derived file aliases remain subject to unchanged byte-derived
        # preview checks; never replace source bytes or accept a new main key.
    return expected

def initial_newversion_projection(prior_legacy,prior_native_before_create,creation_receipt,first_legacy,first_native):
    """Source-derived initial expectations; server scalars are separately typed.

    The caller must apply the unchanged paired CREATE audit and complete
    native/legacy readback before storing the first admitted temporal baseline.
    """
    source=prior_native_before_create;src=identifier(source.get('id'));parent=identifier(source.get('parent',{}).get('id'))
    created=old.receipt(creation_receipt,method='POST',url='https://zenodo.org/api/deposit/depositions/'+src+'/actions/newversion')
    require(creation_receipt['http_status']==201,'genuine own newversion HTTP201 required')
    rid=identifier(str(created.get('id')));require(rid not in{src,parent},'distinct own successor required')
    fields={'conceptdoi','conceptrecid','created','files','id','links','metadata','modified','owner','record_id','state','submitted','title'}
    require(set(created)==fields,'closed inherited creation ACK required')
    require(str(created['record_id'])==rid and str(created['conceptrecid'])==parent and created['conceptdoi']=='10.5281/zenodo.'+parent and created['state']=='unsubmitted'and created['submitted']is False,'own unpublished same-concept ACK required')
    require(str(prior_legacy.get('id'))==src and str(prior_legacy.get('conceptrecid'))==parent and prior_legacy.get('doi')=='10.5281/zenodo.'+src and source.get('is_draft')is False and source.get('is_published')is True,'existing published source pair required')
    require(source.get('versions',{}).get('is_latest')is True and source['versions'].get('is_latest_draft')is True,'exact predecessor latest/latest-draft required')
    index=source['versions'].get('index');require(type(index)is int and index>=1,'source positive native ordinal required')
    old.legacy_relation(prior_legacy,source,{**source,'versions':{**source['versions'],'is_latest':True}})
    owner=source['parent']['access']['owned_by']['user']
    require(str(created['owner'])==str(owner)and type(created['owner'])in(str,int),'creation owner differs from source')
    require(created['title']==prior_legacy['metadata']['title']==source['metadata']['title'],'inherited title differs')
    require(created['links'].get('latest_draft')=='https://zenodo.org/api/deposit/depositions/'+rid and created['links'].get('publish')=='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish','creation own draft endpoint differs')
    from digest_metadata import FIELDS as metadata_fields,closed_payload
    from first_digest_state import encode_api_communities,private_metadata_expected
    require(not(set(prior_legacy['metadata'])-metadata_fields-{'doi','relations'}),'unclassified inherited source metadata field')
    public_source={k:deepcopy(v)for k,v in prior_legacy['metadata'].items()if k in metadata_fields}
    payload=encode_api_communities(closed_payload(public_source,public_source))
    metadata=private_metadata_expected(payload,created,source['metadata'])
    require(exact(created['metadata'],metadata),'inherited creation metadata changed')
    entries=_inherited(source,created,rid)
    from server_managed_fields import _timestamp
    require(first_native.get('id')==rid and type(first_native.get('revision_id'))is int and first_native['revision_id']>=0,'typed initial own revision required')
    expiry=first_native.get('expires_at');require(isinstance(expiry,str)and abs((_timestamp(expiry)-_timestamp(created['created'])).total_seconds())<1,'creation-tied own expiry required')
    expected={'id':rid,'created':created['created'],'updated':created['modified'],'revision_id':first_native['revision_id'],'expires_at':expiry,'metadata':deepcopy(source['metadata']),'access':deepcopy(source['access']),'custom_fields':deepcopy(source.get('custom_fields',{})),'parent':deepcopy(source['parent']),'pids':{'doi':{'client':'datacite','identifier':metadata['prereserve_doi']['doi'],'provider':'datacite'}},'files':{'enabled':True,'entries':entries,'count':len(entries),'total_bytes':sum(r['size']for r in entries.values()),'order':[]},'media_files':{'enabled':False,'entries':{},'count':0,'total_bytes':0,'order':[]},'is_draft':True,'is_published':False,'status':'draft','links':{},'ui':{'is_draft':True,'access_status':{'embargo_date_l10n':None}},'versions':{'index':index+1,'is_latest':False,'is_latest_draft':True}}
    community_fields(prior_legacy['metadata'],prior_legacy,source,expected)
    return expected,deepcopy(created)

def first_legacy_receipt_from_creation(state,*,root):
    value=state.get('first_owned_legacy_draft')
    require(isinstance(value,dict)and set(value)=={'path','sha256'},'explicit genuine first own legacy GET binding required');return deepcopy(value)

def predecessor_inventory(plan,*,root):
    import methods_digest_registration as registration
    admitted=registration.require_registration(root,plan['predecessor_registration'])
    require(admitted['receipt']['record_id']==plan['predecessor_record_id']and admitted['receipt']['record_id']=='23226761'and admitted['receipt']['release_week']=='2026-W41'and{v['run_id']for v in admitted['receipt']['children']}==OLD_SEVEN,'exact default-admitted predecessor seven required')
    manifest=admitted['manifest'];package=Path(root)/admitted['receipt']['package_path']
    from methods_digest import read_regular
    rows=[]
    for value in manifest['uploads']:
        path=package/value['filename'];raw=read_regular(path)
        require(hashlib.sha256(raw).hexdigest()==value['sha256']and hashlib.md5(raw).hexdigest()==value['md5']and len(raw)==value['bytes'],'default-admitted predecessor upload changed')
        rows.append({'name':value['filename'],'path':str(path),'sha256':value['sha256'],'md5':value['md5'],'bytes':value['bytes']})
    for name in('DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
        path=package/name;raw=read_regular(path);rows.append({'name':name,'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'md5':hashlib.md5(raw).hexdigest(),'bytes':len(raw)})
    require(len(rows)==6 and len({r['name']for r in rows})==6,'exact predecessor six main files required');return rows

def inherited_download_spec(name,creation_entry,plan,*,root):
    rows=predecessor_inventory(plan,root=root);matched=[r for r in rows if r['name']==name]
    require(len(matched)==1,'unique predecessor download required');row=matched[0]
    require(creation_entry.get('filename')==name and creation_entry.get('filesize')==row['bytes']and creation_entry.get('checksum')==row['md5'],'creation bytes differ from admitted predecessor');return deepcopy(row)

def assemble_context(*,record_id,source_legacy_receipt,source_native_receipt,source_native_before_create,first_own_native_draft,first_own_legacy_draft,predecessor_registration,successor_digest_manifest,before_publish_native_receipt,creation_receipt,reservation_receipt,publish_receipt,mirror_proof):
    rid=identifier(record_id);sources={k:v for k,v in locals().copy().items()if k in ROLES}
    require(set(sources)==ROLES,'complete successor context required')
    for v in sources.values():require(isinstance(v,dict)and set(v)=={'path','sha256'}and isinstance(v['path'],str)and re.fullmatch('[0-9a-f]{64}',str(v['sha256']))is not None,'closed successor material binding required')
    return {'standard':STANDARD,'status':STATUS,'phase':'PUBLISHED','record_id':rid,'producer_sha256':source_sha(),'source_bindings':deepcopy(sources)}

def consume_context(context,*,load,public,evidence_sources,root=ROOT):
    require(isinstance(context,dict)and set(context)==FIELDS and context['standard']==STANDARD and context['status']==STATUS and context['phase']=='PUBLISHED'and context['producer_sha256']==source_sha(),'current closed same-concept context required')
    sources=context['source_bindings'];require(isinstance(sources,dict)and set(sources)==ROLES,'closed same-concept roles required')
    for role in('source_legacy_receipt','source_native_receipt','publish_receipt'):
        key='own_publish_receipt'if role=='publish_receipt'else role;require(sources[role]==evidence_sources[key],'successor/evidence source differs: '+role)
    objects={role:load(binding)for role,binding in sources.items()};rid=identifier(context['record_id']);source_id=str(objects['source_legacy_receipt'].get('response',{}).get('id'))
    sl=old.receipt(objects['source_legacy_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id)
    sn=old.receipt(objects['source_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id,accept=NATIVE_ACCEPT)
    pre=old.receipt(objects['source_native_before_create'],method='GET',url='https://zenodo.org/api/records/'+source_id,accept=NATIVE_ACCEPT)
    require(exact(sn,pre),'source native before-create differs from bound source')
    fn=old.receipt(objects['first_own_native_draft'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE_ACCEPT)
    fl=old.receipt(objects['first_own_legacy_draft'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid)
    initial,wanted=initial_newversion_projection(sl,pre,objects['creation_receipt'],fl,fn)
    # Exact initial metadata/ownership/parent/file inheritance must be checked
    # again, not merely an old claimed initial-success flag.
    require(not(set(fn)-set(initial)-{'stats','swh','deletion_status'}),'unclassified first native field')
    require(exact(fn.get('pids'),initial['pids'])and fn.get('is_draft')is True and fn.get('is_published')is False and fn.get('status')=='draft','first native own PID/state differs')
    require(exact(fn.get('metadata'),initial['metadata'])and exact(fn.get('access'),initial['access'])and exact(fn.get('custom_fields',{}),initial['custom_fields'])and exact(fn.get('parent'),initial['parent']),'first native scientific/source fields differ')
    require(exact(fn.get('files',{}).get('entries'),initial['files']['entries'])and exact(fl,wanted),'first inherited complete bytes differ')
    before=old.receipt(objects['before_publish_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE_ACCEPT)
    created=objects['creation_receipt']['response'];reserved=old.receipt(objects['reservation_receipt'],method='POST',url='https://zenodo.org/api/records/'+rid+'/draft/pids/doi',accept=NATIVE_ACCEPT)
    published=old.receipt(objects['publish_receipt'],method='POST',url='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish')
    bp=Path(sources['before_publish_native_receipt']['path']);pp=Path(sources['publish_receipt']['path']);bm=re.fullmatch('([0-9]{3,})_GET[.]json',bp.name);pm=re.fullmatch('([0-9]{3,})_POST[.]json',pp.name)
    require(bp.parent==pp.parent and bm is not None and pm is not None and int(pm[1])==int(bm[1])+1,'same-operation final prepublish GET→POST provenance required')
    import methods_digest_registration as registration
    previous=registration.require_registration(root,sources['predecessor_registration'])
    require(previous['receipt']['record_id']==source_id=='23226761'and previous['receipt']['release_week']=='2026-W41'and{v['run_id']for v in previous['receipt']['children']}==OLD_SEVEN,'genuine default predecessor admission required')
    require_mirror_proof(objects['mirror_proof'])
    manifest=objects['successor_digest_manifest']
    require(isinstance(manifest,dict)and manifest.get('release_week')=='2026-W41'and{n['run_id']for n in manifest.get('notes',[])}==NEW_49 and len(manifest['notes'])==49 and not({n['run_id']for n in manifest['notes']}&OLD_SEVEN),'exact49 new disjoint successor notes required')
    require(manifest.get('public_metadata')==public and public['title']==sl['metadata']['title']=='Viridis Methods Digest — 2026-W41','unchanged weekly title/current metadata required')
    require(not(set(before)-set(initial)-{'stats','swh','deletion_status'}),'unclassified prepublish native field')
    require(exact(before.get('parent'),sn['parent'])and exact(before.get('pids'),reserved.get('pids'))and before.get('created')==created['created'],'immutable same-concept parent/PIDs/creation differ')
    native=predict_native(public,sl,sn,before,created,reserved,published)
    relation=old.legacy_relation(sl,sn,{**native,'versions':{**native['versions'],'is_latest':True}})
    return {'record_id':rid,'native':native,'legacy_relation':relation,'source_legacy':sl,'source_native':sn,'before_native':before}

canonical_links=old.canonical_links
legacy_relation=old.legacy_relation

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
 require(src!=rid and src_parent==parent and str(source_legacy.get('id'))==src and source_native.get('is_published') is True and source_native.get('is_draft') is False,'distinct existing same-concept public source pair required')
 require(source_native.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+src and source_legacy.get('doi')=='10.5281/zenodo.'+src,'source DOI pair differs')
 source_index=source_native.get('versions',{}).get('index');own_index=before.get('versions',{}).get('index')
 require(type(source_index)is int and source_index>=1 and (own_index is None or type(own_index)is int and own_index==source_index+1),'same-concept source+1 ordinal required')
 require(exact(before.get('parent',{}).get('access'),source_native.get('parent',{}).get('access')) and exact(before.get('access'),source_native.get('access')),'same-concept source ownership/access differs')
 source_links=source_native.get('links');template=canonical_links(src,src_parent)
 require(isinstance(source_links,dict),'source public links object required')
 if 'thumbnails' not in source_links:template.pop('thumbnails')
 require(source_links==template and source_legacy.get('links')==source_links,'unknown, foreign or differing source public link template')
 custom,graph=community_fields(public,source_legacy,source_native,before)
 # Preserve the established executor's private→public projection exactly.
 expected=deepcopy(before);expected.update(is_draft=False,is_published=True,status='published')
 expected['versions']['index']=source_index+1
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

def require_mirror_proof(mirror):
 require(isinstance(mirror,dict) and mirror.get('status')=='SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN' and mirror.get('field')=='custom_fields.legacy:communities' and mirror.get('condition')==MIRROR_CONDITION and mirror.get('public_post_publish_exact_preservation') is True and type(mirror.get('production_writes_in_test')) is int and mirror['production_writes_in_test']==0,'decisive tested existing community mirror proof required')
 require(isinstance(mirror.get('checks'),dict) and set(mirror['checks'])=={'communities','conceptdoi','conceptrecid','doi','files','native_membership'} and all(type(v)is bool and v is True for v in mirror['checks'].values()),'complete tested mirror preservation checks required')
 tested=mirror.get('existing_public_communities')
 require(mirror.get('before_custom_fields')=={} and isinstance(tested,list) and tested and all(isinstance(x,dict) and set(x)=={'id'} and isinstance(x['id'],str) and x['id'] for x in tested) and mirror.get('after_custom_fields')=={'legacy:communities':[x['id'] for x in tested]} and re.fullmatch('[0-9a-f]{64}',str(mirror.get('transport_sha256'))) is not None,'source-bound tested pure mirror addition required')

