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
STANDARD='VRS-METHODS-DIGEST-GENERIC-SAME-CONCEPT-SUCCESSOR-CONTEXT-1'
LEGACY_SAME_CONCEPT_STANDARD='VRS-METHODS-DIGEST-SAME-CONCEPT-SUCCESSOR-CONTEXT-1'
FIRST_WEEK_STANDARD='VRS-METHODS-DIGEST-FIRST-WEEK-PUBLIC-CONTEXT-1'
STATUS=old.STATUS
FIELDS=old.FIELDS
ROLES=old.ROLES|{'source_native_before_create','first_own_native_draft','first_own_legacy_draft','predecessor_registration','successor_digest_manifest'}
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
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
    require(admitted['receipt']['record_id']==plan['predecessor_record_id']and admitted['receipt']['release_week']==plan['release_week'],'exact default-admitted same-week predecessor required')
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

def assemble_context(*,record_id,source_legacy_receipt,source_native_receipt,source_native_before_create,first_own_native_draft,first_own_legacy_draft,successor_digest_manifest,before_publish_native_receipt,creation_receipt,reservation_receipt,publish_receipt,mirror_proof,predecessor_registration=None,account_discovery=None,metadata_source_registration=None,start_kind='NEW_VERSION'):
    require(start_kind in{'NEW_VERSION','CREATE_WEEK'},'closed owned digest operation required')
    roles=ROLES if start_kind=='NEW_VERSION'else FIRST_WEEK_ROLES
    require((account_discovery is None and metadata_source_registration is None)if start_kind=='NEW_VERSION'else(predecessor_registration is None),'own operation-specific context required')
    rid=identifier(record_id);sources={k:v for k,v in locals().copy().items()if k in roles}
    require(set(sources)==roles,'complete successor context required')
    for v in sources.values():require(isinstance(v,dict)and set(v)=={'path','sha256'}and isinstance(v['path'],str)and re.fullmatch('[0-9a-f]{64}',str(v['sha256']))is not None,'closed successor material binding required')
    return {'standard':STANDARD if start_kind=='NEW_VERSION'else FIRST_WEEK_STANDARD,'status':STATUS,'phase':'PUBLISHED','record_id':rid,'producer_sha256':source_sha(),'source_bindings':deepcopy(sources)}


def registered_lineage_runs(admitted,*,root):
    """Every ancestor is reconsumed by the unchanged default registrar."""
    import methods_digest_registration as registration
    import methods_digest as digest
    week=admitted['receipt']['release_week'];seen_records=set();seen_runs=set()
    while True:
        receipt=admitted['receipt'];rid=identifier(receipt.get('record_id'))
        require(rid not in seen_records and len(seen_records)<1000,'closed acyclic owned weekly lineage required')
        require(receipt.get('release_week')==week,'weekly lineage changed week')
        seen_records.add(rid);children=receipt.get('children')
        require(isinstance(children,list)and children,'default-admitted nonempty children required')
        runs=[x.get('run_id')for x in children]
        require(all(isinstance(x,str)and re.fullmatch('Run-[0-9]{3,}',x)for x in runs)and len(runs)==len(set(runs))and not(seen_runs&set(runs)),'duplicate or invalid ancestor note IDs')
        seen_runs.update(runs)
        evidence=json.loads(digest.bound_file(root,receipt['public_evidence'])[1])
        context=json.loads(digest.bound_file(root,evidence['public_state_context'])[1])
        if context.get('standard')==old.STANDARD:return seen_runs
        require(context.get('standard')in{STANDARD,LEGACY_SAME_CONCEPT_STANDARD,FIRST_WEEK_STANDARD},'unknown predecessor public context')
        if context['standard']==FIRST_WEEK_STANDARD:return seen_runs
        binding=context['source_bindings']['predecessor_registration']
        admitted=registration.require_registration(root,binding)

def require_successor_scope(previous,manifest,public,source_legacy,*,root):
    import methods_digest as digest
    require(isinstance(manifest,dict)and isinstance(manifest.get('notes'),list)and manifest['notes'],'nonempty bound successor scope required')
    week=manifest.get('release_week');require(week==previous['receipt'].get('release_week'),'same concept cannot change release week')
    runs=[n.get('run_id')for n in manifest['notes']]
    require(all(isinstance(x,str)and re.fullmatch('Run-[0-9]{3,}',x)for x in runs)and len(runs)==len(set(runs)),'unique canonical successor note IDs required')
    require(not(set(runs)&registered_lineage_runs(previous,root=root)),'new notes collide with an admitted predecessor version')
    require(manifest.get('public_metadata')==public and public['title']==source_legacy['metadata']['title']==digest.week_title(week),'unchanged weekly title/current metadata required')
    return runs

def consume_context(context,*,load,public,evidence_sources,root=ROOT):
    if isinstance(context,dict)and context.get('standard')==FIRST_WEEK_STANDARD:return consume_first_week_context(context,load=load,public=public,evidence_sources=evidence_sources,root=root)
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
    require(previous['receipt']['record_id']==source_id,'genuine default predecessor admission required')
    require_mirror_proof(objects['mirror_proof'])
    manifest=objects['successor_digest_manifest']
    require_successor_scope(previous,manifest,public,sl,root=root)
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


FIRST_WEEK_ROLES=old.ROLES|{'source_native_before_create','first_own_native_draft','first_own_legacy_draft','account_discovery','successor_digest_manifest','metadata_source_registration'}

def is_first_week_projection(public,source_legacy,source_native,before):
    """Closed weekly-title/parent selector; full context separately proves no record."""
    title=public.get('title');source_title=source_legacy.get('metadata',{}).get('title')
    return(isinstance(title,str)and isinstance(source_title,str)and re.fullmatch('Viridis Methods Digest — [0-9]{4}-W[0-9]{2}',title)is not None and re.fullmatch('Viridis Methods Digest — [0-9]{4}-W[0-9]{2}',source_title)is not None and title!=source_title and before.get('parent',{}).get('id')!=source_native.get('parent',{}).get('id'))

def first_week_community_fields(public,source_legacy,source_native,before):
    require(is_first_week_projection(public,source_legacy,source_native,before),'distinct first-week source title/parent required')
    communities=source_legacy.get('metadata',{}).get('communities',[])
    require(public.get('communities',[])==communities,'new week cannot change existing source memberships')
    require(isinstance(communities,list)and all(isinstance(c,dict)and set(c)=={'id'}and isinstance(c['id'],str)and c['id']for c in communities),'closed existing community IDs required')
    slugs=[c['id']for c in communities];require(len(slugs)==len(set(slugs)),'unique existing memberships required')
    source=source_native.get('custom_fields',{})
    require(source in({}, {'legacy:communities':slugs})and before.get('custom_fields',{})==({'legacy:communities':slugs}if slugs else{}),'exact source membership draft mirror required')
    graph=source_native.get('parent',{}).get('communities',{})
    require(before.get('parent',{}).get('communities',{})=={},'first own unpublished parent graph must be empty')
    if not slugs:require(graph=={}and source=={},'empty source membership graph required');return {},{}
    require(isinstance(graph,dict)and set(graph)=={'default','ids','entries'},'closed source membership graph required')
    ids=graph['ids'];entries=graph['entries']
    require(isinstance(ids,list)and len(ids)==len(slugs)and len(set(ids))==len(ids)and all(isinstance(x,str)and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',x)for x in ids),'unique source UUIDs required')
    require(graph['default']in ids and isinstance(entries,list)and len(entries)==len(ids)and all(isinstance(x,dict)for x in entries)and[x.get('id')for x in entries]==ids and[x.get('slug')for x in entries]==slugs,'exact existing UUID/slug/default association required')
    require(before.get('parent',{}).get('access',{}).get('owned_by')==source_native.get('parent',{}).get('access',{}).get('owned_by'),'new-week source owner differs')
    return {},deepcopy(graph)

def registered_relation_template(registration_binding,*,root,source_native,source_legacy):
    """Return only the vocabulary in an actual default-admitted source evidence.

    Empty scientific relation lists do not erase the original registered enum.
    This constructor does not admit the new package or change its relation list.
    """
    import methods_digest as digest
    import methods_digest_registration as registration
    snapshots=[]
    def read(binding):
        _,raw=digest.bound_file(root,binding);snapshots.append((deepcopy(binding),raw));return json.loads(raw)
    read(registration_binding)
    admitted=registration.require_registration(root,registration_binding)
    rid=identifier(source_native.get('id'))
    require(admitted['receipt']['record_id']==rid and str(source_legacy.get('id'))==rid,'exact default-admitted metadata source required')
    require(source_native.get('is_published')is True and source_native.get('is_draft')is False and source_legacy.get('doi')=='10.5281/zenodo.'+rid,'published source identity required')
    actual_native=admitted['public_native'];actual_legacy=admitted['public_legacy']
    require(actual_native.get('id')==rid and str(actual_legacy.get('id'))==rid,'registered public pair identity differs')
    for field in('metadata','access','custom_fields','parent','pids','files','media_files'):
        require(exact(source_native.get(field),actual_native.get(field)),'registered source field differs: '+field)
    legacy_metadata=lambda v:{k:x for k,x in v.get('metadata',{}).items()if k!='relations'}
    require(exact(legacy_metadata(source_legacy),legacy_metadata(actual_legacy)) and source_legacy.get('conceptrecid')==actual_legacy.get('conceptrecid'),'registered legacy science/concept differs')
    require(source_legacy['metadata'].get('title')==digest.week_title(admitted['receipt']['release_week']),'registered source week/title differs')
    evidence=read(admitted['receipt']['public_evidence']);relation=read(evidence['relation_template'])
    require(isinstance(relation,dict),'registered relation vocabulary shape required')
    template=relation.get('relation_type',relation)
    require(isinstance(template,dict)and set(template)=={'id','title'}and template['id']=='issupplementto'and isinstance(template['title'],dict)and template['title'].get('en')=='Is supplement to','registered relation vocabulary required')
    present=[r['relation_type']for r in source_native['metadata'].get('related_identifiers',[])if isinstance(r,dict)and r.get('relation_type',{}).get('id')=='issupplementto']
    require(all(exact(value,template)for value in present),'registered/source relation vocabulary differs')
    for binding,raw in snapshots:require(digest.bound_file(root,binding)[1]==raw,'registered vocabulary material changed')
    return deepcopy(template)

def first_week_projection(prior_legacy,source_native,creation_receipt,first_legacy,first_native,public_metadata,*,relation_template=None):
    """New IDs only from genuine CREATE; source metadata only from bound payload."""
    from digest_metadata import closed_payload,native_metadata,FIELDS as metadata_fields
    from first_digest_state import encode_api_communities,private_metadata_expected,identifier as codec_id
    from server_managed_fields import _timestamp
    src=identifier(source_native.get('id'));source_parent=identifier(source_native.get('parent',{}).get('id'))
    created=old.receipt(creation_receipt,method='POST',url='https://zenodo.org/api/deposit/depositions')
    require(creation_receipt['http_status']==201,'genuine own first-week CREATE201 required')
    fields={'conceptrecid','created','files','id','links','metadata','modified','owner','record_id','state','submitted','title'}
    require(set(created)==fields,'closed own first-week CREATE shape required')
    rid=codec_id(created.get('id'));parent=codec_id(created.get('conceptrecid'));owner=codec_id(source_native['parent']['access']['owned_by']['user'])
    require(rid!=parent and rid not in{src,source_parent}and parent!=source_parent and codec_id(created['record_id'])==rid and codec_id(created['owner'])==owner,'new own IDs/concept/account required')
    require(created['files']==[]and created['state']=='unsubmitted'and created['submitted']is False,'empty own first-week draft required')
    require(str(prior_legacy.get('id'))==src and str(prior_legacy.get('conceptrecid'))==source_parent and source_native.get('is_published')is True and source_native.get('is_draft')is False,'genuine published source pair required')
    require(not(set(prior_legacy['metadata'])-metadata_fields-{'doi','relations'}),'unclassified source metadata field')
    source={k:deepcopy(v)for k,v in prior_legacy['metadata'].items()if k in metadata_fields}
    payload=encode_api_communities(closed_payload(public_metadata,source))
    relations=[r['relation_type']for r in source_native['metadata'].get('related_identifiers',[])if r.get('relation_type',{}).get('id')=='issupplementto']
    template=relation_template if relation_template is not None else(relations[0]if relations else None)
    require(isinstance(template,dict)and all(exact(v,template)for v in relations),'registered/source relation vocabulary required')
    native=native_metadata(public_metadata,source,prior_legacy,source_native,template);md=private_metadata_expected(payload,created,native)
    require(created['title']==public_metadata['title']and created['metadata']==md,'exact new-week reviewed metadata required')
    require(created['links'].get('latest_draft')=='https://zenodo.org/api/deposit/depositions/'+rid and created['links'].get('publish')=='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish','own CREATE endpoints differ')
    revision=first_native.get('revision_id');expiry=first_native.get('expires_at')
    require(first_native.get('id')==rid and type(revision)is int and revision>=0 and isinstance(expiry,str)and abs((_timestamp(expiry)-_timestamp(created['created'])).total_seconds())<1,'creation-tied typed first server scalars required')
    slugs=[c['id']for c in public_metadata.get('communities',[])]
    expected={'id':rid,'created':created['created'],'updated':created['modified'],'revision_id':revision,'expires_at':expiry,'metadata':native,'access':deepcopy(source_native['access']),'custom_fields':{'legacy:communities':slugs}if slugs else{},'parent':{'id':parent,'access':{'grants':[],'links':[],'owned_by':{'user':owner},'settings':{'accept_conditions_text':None,'allow_guest_requests':False,'allow_user_requests':False,'secret_link_expiration':0}},'communities':{},'pids':{}},'pids':{'doi':{'client':'datacite','identifier':md['prereserve_doi']['doi'],'provider':'datacite'}},'files':{'enabled':True,'entries':{},'count':0,'total_bytes':0,'order':[]},'media_files':{'enabled':False,'entries':{},'count':0,'total_bytes':0,'order':[]},'is_draft':True,'is_published':False,'status':'draft','links':{},'ui':{'is_draft':True,'access_status':{'embargo_date_l10n':None}},'versions':{'index':1,'is_latest':False,'is_latest_draft':True}}
    first_week_community_fields(public_metadata,prior_legacy,source_native,expected)
    return expected,deepcopy(created)

def consume_first_week_context(context,*,load,public,evidence_sources,root):
    require(isinstance(context,dict)and set(context)==FIELDS and context['standard']==FIRST_WEEK_STANDARD and context['status']==STATUS and context['phase']=='PUBLISHED'and context['producer_sha256']==source_sha(),'closed current first-week context required')
    sources=context['source_bindings'];require(isinstance(sources,dict)and set(sources)==FIRST_WEEK_ROLES,'closed first-week roles required')
    for role in('source_legacy_receipt','source_native_receipt','publish_receipt'):
        require(sources[role]==evidence_sources['own_publish_receipt'if role=='publish_receipt'else role],'first-week/evidence source differs')
    objects={r:load(b)for r,b in sources.items()};rid=identifier(context['record_id']);source_id=str(objects['source_legacy_receipt'].get('response',{}).get('id'))
    sl=old.receipt(objects['source_legacy_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id);sn=old.receipt(objects['source_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+source_id,accept=NATIVE_ACCEPT)
    pre=old.receipt(objects['source_native_before_create'],method='GET',url='https://zenodo.org/api/records/'+source_id,accept=NATIVE_ACCEPT);require(exact(pre,sn),'first-week source snapshot differs')
    manifest=objects['successor_digest_manifest'];week=manifest.get('release_week');notes=manifest.get('notes')
    import methods_digest as digest
    require(isinstance(notes,list)and notes and manifest.get('public_metadata')==public and public.get('title')==digest.week_title(week),'bound first-week own note scope/title required')
    runs=[n.get('run_id')for n in notes];require(all(isinstance(v,str)and re.fullmatch('Run-[0-9]{3,}',v)for v in runs)and len(runs)==len(set(runs)),'unique first-week note identities required')
    discovery=objects['account_discovery'];observed=require_account_discovery(discovery,root=Path(root))
    require(discovery['start_kind']=='CREATE_WEEK'and discovery['release_week']==week and observed['status']=='NO_EXISTING_WEEKLY_RECORD'and week!='2026-W41','complete actual no-existing-week proof required')
    fn=old.receipt(objects['first_own_native_draft'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE_ACCEPT);fl=old.receipt(objects['first_own_legacy_draft'],method='GET',url='https://zenodo.org/api/deposit/depositions/'+rid)
    template=registered_relation_template(sources['metadata_source_registration'],root=root,source_native=sn,source_legacy=sl)
    require(sl['metadata']['title']!=public['title'],'first-week source registration must belong to another week')
    initial,wanted=first_week_projection(sl,sn,objects['creation_receipt'],fl,fn,public,relation_template=template)
    require(not(set(fn)-set(initial)-{'stats','swh','deletion_status'}),'unclassified first native field')
    for key in('metadata','access','custom_fields','parent','pids','files','media_files'):
        require(exact(fn.get(key),initial[key]),'first own scientific/source field differs: '+key)
    require(exact(fl,wanted),'exact first own legacy CREATE required')
    before=old.receipt(objects['before_publish_native_receipt'],method='GET',url='https://zenodo.org/api/records/'+rid+'/draft',accept=NATIVE_ACCEPT)
    created=objects['creation_receipt']['response'];reserved=old.receipt(objects['reservation_receipt'],method='POST',url='https://zenodo.org/api/records/'+rid+'/draft/pids/doi',accept=NATIVE_ACCEPT);published=old.receipt(objects['publish_receipt'],method='POST',url='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish')
    bp=Path(sources['before_publish_native_receipt']['path']);pp=Path(sources['publish_receipt']['path']);bm=re.fullmatch('([0-9]{3,})_GET[.]json',bp.name);pm=re.fullmatch('([0-9]{3,})_POST[.]json',pp.name)
    require(bp.parent==pp.parent and bm is not None and pm is not None and int(pm[1])==int(bm[1])+1,'same-operation first-week GET→publish required')
    require_mirror_proof(objects['mirror_proof'])
    require(not(set(before)-set(initial)-{'stats','swh','deletion_status'}),'unclassified first-week prepublish native field')
    for key in('metadata','access','custom_fields','parent','pids'):
        require(exact(before.get(key),initial[key]),'immutable first-week field differs: '+key)
    require(before.get('created')==created['created'],'first-week immutable creation time differs')
    native=predict_first_week_native(public,sl,sn,before,created,reserved,published)
    relation=old.legacy_relation(sl,sn,{**native,'versions':{**native['versions'],'is_latest':True}})
    return {'record_id':rid,'native':native,'legacy_relation':relation,'source_legacy':sl,'source_native':sn,'before_native':before}

def predict_first_week_native(public,source_legacy,source_native,before,created,reserved,published):
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
 custom,graph=first_week_community_fields(public,source_legacy,source_native,before)
 require(before.get('versions',{}).get('index')is None or type(before.get('versions',{}).get('index'))is int and before['versions']['index']==1,'first-week ordinal1 required')
 # Preserve the established executor's private→public projection exactly.
 expected=deepcopy(before);expected.update(is_draft=False,is_published=True,status='published');expected['versions']['index']=1
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

# Pure raw-account consumption copied from exactly reviewed producer bytes.
import urllib.parse
import methods_digest as d
_account_HOST="zenodo.org"
_account_SIZE=100
_account_FIELDS={"standard","release_week","record_id","concept_id","passes","records","record_count","producer_sha256","writes","start_kind"}
OWNED_DISCOVERY_PRODUCER_SHA="18bb000d76258a3a5a04bbdd85a4274bbc3128bdee370c906515c5aa86653213"
def _account_source_sha():return OWNED_DISCOVERY_PRODUCER_SHA
class _account_AccountHold(ValueError):
    pass

def _account_require_url(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.netloc != _account_HOST or p.path != '/api/user/records' or p.fragment or p.username or p.password:
        raise _account_AccountHold('HOLD_ACCOUNT_URL')
    q = urllib.parse.parse_qs(p.query, strict_parsing=True)
    if set(q) != {'page', 'size'} or q['size'] != [str(_account_SIZE)] or len(q['page']) != 1 or (re.fullmatch('[1-9][0-9]*', q['page'][0]) is None) or (p.query != 'page=' + q['page'][0] + '&size=' + str(_account_SIZE)):
        raise _account_AccountHold('HOLD_ACCOUNT_QUERY')
    return int(q['page'][0])

def _account_total(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, dict) and set(value) == {'value', 'relation'} and (value['relation'] == 'eq') and (type(value['value']) is int) and (value['value'] >= 0):
        return value['value']
    raise _account_AccountHold('HOLD_ACCOUNT_TOTAL_NOT_EXACT')

def _account_identity(row):
    if not isinstance(row, dict) or re.fullmatch('[1-9][0-9]*', str(row.get('id'))) is None or (not isinstance(row.get('metadata'), dict)) or (not isinstance(row['metadata'].get('title'), str)):
        raise _account_AccountHold('HOLD_ACCOUNT_ROW')
    return str(row['id'])

def _account_discovery_signature(rows):
    return [{k: r.get(k) for k in ('id', 'metadata', 'parent', 'versions', 'pids', 'is_draft', 'is_published', 'status')} for r in rows]

class _account_DiscoveryHold(ValueError):
    pass

def _account_need(value, reason):
    if not value:
        raise _account_DiscoveryHold('HOLD_' + reason)

def _account_raw(path):
    p = Path(path)
    _account_need(p.is_absolute() and p.is_file() and (not any((q.is_symlink() for q in (p, *p.parents)))), 'REGULAR_BOUND_SOURCE')
    a = p.stat()
    value = p.read_bytes()
    z = p.stat()
    _account_need((a.st_ino, a.st_mtime_ns, a.st_size) == (z.st_ino, z.st_mtime_ns, z.st_size), 'SOURCE_READ_RACE')
    return value

def _account_bound(root, value):
    _account_need(isinstance(value, dict) and set(value) == {'path', 'sha256'} and isinstance(value['path'], str) and (re.fullmatch('[0-9a-f]{64}', str(value['sha256'])) is not None), 'CLOSED_SOURCE_BINDING')
    p = Path(value['path'])
    data = _account_raw(p)
    _account_need(p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True)) and hashlib.sha256(data).hexdigest() == value['sha256'], 'CURRENT_CANONICAL_SOURCE')
    return (p, json.loads(data))

def _account_decode_pass(root, rows):
    _account_need(isinstance(rows, list) and rows, 'EXACT_ACCOUNT_PAGES')
    out = []
    expected = None
    ids = set()
    for page, row in enumerate(rows, 1):
        _, receipt = _account_bound(root, row)
        _account_need(receipt.get('standard') == 'VRS-PHASE7-READONLY-ACCOUNT-GET-1' and receipt.get('method') == 'GET' and (receipt.get('status') == 'RAW_ACCOUNT_GET_CAPTURED_NOT_COMPLETE') and (receipt.get('http_status') == 200) and (_account_require_url(receipt.get('url')) == page), 'GENUINE_ACCOUNT_PAGE')
        p = Path(receipt.get('response_path'))
        data_bytes = _account_raw(p)
        _account_need(p.resolve(strict=True).is_relative_to(root) and hashlib.sha256(data_bytes).hexdigest() == receipt.get('response_sha256') and (len(data_bytes) == receipt.get('response_bytes')) and (len(data_bytes) <= 16 * 1024 * 1024), 'ACCOUNT_RAW_BINDING')
        data = json.loads(data_bytes)
        hits = data.get('hits')
        _account_need(isinstance(hits, dict) and isinstance(hits.get('hits'), list), 'ACCOUNT_NATIVE_HITS')
        count = _account_total(hits.get('total'))
        _account_need(count <= 100000, 'BOUNDED_ACCOUNT_TOTAL')
        if expected is None:
            expected = count
        _account_need(count == expected and len(hits['hits']) == min(100, expected - len(out)), 'COMPLETE_EXACT_ACCOUNT_PAGE')
        for record in hits['hits']:
            rid = _account_identity(record)
            _account_need(rid not in ids, 'UNIQUE_ACCOUNT_ID')
            ids.add(rid)
            out.append(record)
        _account_need(len(out) <= expected, 'ACCOUNT_OVERFLOW')
        if len(out) == expected:
            _account_need(page == len(rows), 'NO_EXTRA_ACCOUNT_PAGE')
    _account_need(len(out) == expected, 'ACCOUNT_INCOMPLETE')
    return out

def _account_discover(rows, week):
    projected = deepcopy(rows)
    for row in projected:
        rid = _account_identity(row)
        doi = row.get('pids', {}).get('doi', {}).get('identifier')
        if 'doi' in row:
            _account_need(doi is None or row['doi'] == doi, 'ACCOUNT_DOI_REPRESENTATION_CONFLICT')
        elif doi is not None:
            _account_need(doi == '10.5281/zenodo.' + rid, 'ACCOUNT_OWN_DOI')
            row['doi'] = doi
    result = d.discover_weekly_record(projected, week, complete=True)
    if result['status'] == 'EXISTING_WEEKLY_RECORD':
        own = next((r for r in rows if _account_identity(r) == result['record_id']))
        _account_need(own.get('is_published') is True and own.get('is_draft') is False and (own.get('status') == 'published') and (result['doi'] == '10.5281/zenodo.' + result['record_id']), 'GENUINE_PUBLISHED_WEEKLY_SOURCE')
    return result

def require_account_discovery(v, *, root):
    _account_need(isinstance(v, dict) and set(v) == _account_FIELDS and (v['standard'] == 'VRS-OWNED-WEEKLY-DISCOVERY-1') and (v['producer_sha256'] == _account_source_sha()) and (type(v['writes']) is int) and (v['writes'] == 0), 'CURRENT_CLOSED_WEEKLY_DISCOVERY')
    _account_need(isinstance(v['passes'], list) and len(v['passes']) == 2, 'REAL_DOUBLE_PASS')
    first, second = [_account_decode_pass(root, rows) for rows in v['passes']]
    _account_need(_account_discovery_signature(first) == _account_discovery_signature(second), 'ACCOUNT_RACE')
    _, saved = _account_bound(root, v['records'])
    _account_need(saved == {'records': first} and type(v['record_count']) is int and (v['record_count'] == len(first)), 'EXACT_RECORDED_ACCOUNT')
    result = _account_discover(first, v['release_week'])
    _account_need(v['start_kind'] in {'NEW_VERSION', 'CREATE_WEEK'}, 'CLOSED_DISCOVERY_OPERATION')
    if v['start_kind'] == 'NEW_VERSION':
        _account_need(result['status'] == 'EXISTING_WEEKLY_RECORD' and result['record_id'] == v['record_id'] and (result['concept_id'] == v['concept_id']), 'ONE_EXISTING_WEEKLY_CONCEPT')
    else:
        _account_need(result['status'] == 'NO_EXISTING_WEEKLY_RECORD' and v['record_id'] is None and (v['concept_id'] is None) and (v['release_week'] != '2026-W41'), 'NO_DUPLICATE_FIRST_WEEK_CONCEPT')
    return result
