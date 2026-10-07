"""Exact new-record predictions and whole-record source guards.

Existing server_managed_fields remains the only server-field allow-list.
No unknown source, content, file, PID or server field is adopted to pass.
"""
from copy import deepcopy
import hashlib,json,re,urllib.parse
from digest_metadata import check,exact,license_id

def identifier(value):
    check(type(value)in(str,int)and re.fullmatch('[1-9][0-9]*',str(value))is not None,'CANONICAL_RECORD_ID');return str(value)
def private_metadata_expected(payload,created,native_metadata):
    m=deepcopy(payload['metadata']);actual=created.get('metadata');check(isinstance(actual,dict),'CREATION_METADATA')
    if 'imprint_publisher'in actual:
        check(actual['imprint_publisher']==native_metadata['publisher'],'CREATION_PUBLISHER');m['imprint_publisher']=native_metadata['publisher']
    prereg=actual.get('prereserve_doi');rid=identifier(created.get('id'))
    check(prereg=={'doi':'10.5281/zenodo.'+rid,'recid':int(rid)},'CREATION_OWN_PRERESERVE_DOI')
    m['prereserve_doi']=deepcopy(prereg);return m
def private_file_compare_rows(rows):
    # Existing filename-keyed rule uses public `key`; draft API spells it
    # `filename`. Add a comparison key while retaining EVERY original field.
    check(isinstance(rows,list)and all(isinstance(row,dict)and isinstance(row.get('filename'),str)and row['filename']and 'key'not in row for row in rows),'PRIVATE_FILE_SCHEMA')
    return [{**deepcopy(row),'key':row['filename']}for row in rows]

def require_private_source(legacy,expected,native,sm,preservation):
    check(isinstance(legacy,dict)and isinstance(expected,dict),'PRIVATE_LEGACY_OBJECTS')
    preservation.require_public_metadata(legacy.get('metadata',{}),expected.get('metadata',{}));preservation.require_file_preservation(private_file_compare_rows(legacy.get('files')),private_file_compare_rows(expected.get('files')))
    left,right=deepcopy(legacy),deepcopy(expected)
    for key in ('metadata','files','links','modified'):left.pop(key,None);right.pop(key,None)
    check(exact(left,right),'UNLISTED_OR_CHANGED_PRIVATE_LEGACY_FIELD')
    check(legacy.get('modified')==native.get('updated'),'PRIVATE_MODIFIED_NATIVE_SOURCE')
    check(legacy.get('created')==native.get('created'),'PRIVATE_CREATED_NATIVE_SOURCE')
    # Legacy bucket links are not own-record-ID URLs. They are frozen from the
    # own creation response and remain byte-exact for the entire operation.
    check(exact(legacy.get('links'),expected.get('links')),'PRIVATE_LINKS_CHANGED')
    check(legacy.get('state')=='unsubmitted'and legacy.get('submitted')is False,'PRIVATE_DRAFT_REQUIRED')
def initial_expected(created,actual,native_metadata,source_native,payload,sm,preservation,*,source_legacy):
    check(isinstance(created,dict)and isinstance(actual,dict),'OWN_CREATION_OBJECTS')
    fields={'conceptrecid','created','files','id','links','metadata','modified','owner','record_id','state','submitted','title'}
    check(set(created)==fields,'UNCLASSIFIED_CREATION_FIELD')
    rid=identifier(created['id']);parent=identifier(created['conceptrecid']);owner=identifier(source_native['parent']['access']['owned_by']['user'])
    check(identifier(created['record_id'])==rid and parent!=rid,'OWN_CREATION_ID_CHAIN')
    check(identifier(created['owner'])==owner,'OWN_ACCOUNT_OWNER_CHANGED')
    check(created['files']==[]and created['state']=='unsubmitted'and created['submitted']is False,'EMPTY_OWN_UNPUBLISHED_CREATION')
    check(created['title']==payload['metadata']['title'],'CREATION_TITLE')
    expected_md=private_metadata_expected(payload,created,native_metadata);preservation.require_public_metadata(created['metadata'],expected_md)
    check(actual.get('id')==rid,'FIRST_NATIVE_ID')
    revision=actual.get('revision_id');expiry=actual.get('expires_at')
    check(type(revision)is int and revision>=0 and isinstance(expiry,str),'OWN_INITIAL_SERVER_ASSIGNMENTS');sm._timestamp(expiry)
    check(abs((sm._timestamp(expiry)-sm._timestamp(created['created'])).total_seconds())<1,'INITIAL_EXPIRY_CREATION_TIME')
    communities=payload['metadata'].get('communities',[]);check(isinstance(communities,list)and all(set(c)=={'id'}for c in communities),'COMMUNITY_REQUEST_SHAPE')
    # The legacy request is a metadata mirror, not a blind community admission.
    mirrored=[c['id']for c in communities]
    from methods_digest_registration import source_custom_fields
    source_bound_custom=source_custom_fields(payload['metadata'],source_legacy,source_native)
    expected={'id':rid,'created':created['created'],'updated':created['modified'],'revision_id':revision,'expires_at':expiry,'metadata':deepcopy(native_metadata),'access':deepcopy(source_native['access']),'custom_fields':source_bound_custom,'parent':{'id':parent,'access':{'grants':[],'links':[],'owned_by':{'user':owner},'settings':{'accept_conditions_text':None,'allow_guest_requests':False,'allow_user_requests':False,'secret_link_expiration':0}},'communities':{},'pids':{}},'pids':{'doi':{'client':'datacite','identifier':created['metadata']['prereserve_doi']['doi'],'provider':'datacite'}},'files':{'enabled':True,'entries':{},'count':0,'total_bytes':0,'order':[]},'media_files':{'enabled':False,'entries':{},'count':0,'total_bytes':0,'order':[]},'is_draft':True,'is_published':False,'status':'draft','links':{},'ui':{'is_draft':True,'access_status':{'embargo_date_l10n':None}},'versions':{'index':1,'is_latest':False,'is_latest_draft':True}}
    # The source's actual immutable mirror spelling is not changed here.
    if communities:
        source_custom=source_native.get('custom_fields',{})
        check(source_custom.get('legacy:communities')==mirrored,'SOURCE_COMMUNITY_MIRROR_NOT_PROVEN')
    legacy_expected=deepcopy(created);legacy_expected['metadata']=expected_md
    return expected,legacy_expected
def file_from_upload(legacy,response,approved,rid):
    check(set(legacy)=={'checksum','filename','filesize','id','links'},'UPLOADED_LEGACY_FILE_SCHEMA')
    fid=legacy['id'];name=approved['name'];check(isinstance(fid,str)and re.fullmatch('[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',fid)is not None,'UPLOADED_FILE_ID')
    check(legacy['filename']==name and type(legacy['filesize'])is int and legacy['filesize']==approved['size']and legacy['checksum']==approved['md5'],'UPLOADED_LEGACY_FILE_BYTES')
    base='https://zenodo.org/api/records/'+rid;draft='https://zenodo.org/api/deposit/depositions/'+rid
    check(legacy['links']=={'download':base+'/draft/files/'+name+'/content','self':draft+'/files/'+fid},'UPLOADED_LEGACY_FILE_LINKS')
    check(response.get('key')==name and response.get('checksum')=='md5:'+approved['md5']and type(response.get('size'))is int and response['size']==approved['size']and response.get('is_head')is True and response.get('delete_marker')is False and isinstance(response.get('mimetype'),str),'OWN_UPLOAD_ACK_BYTES')
    return {'access':{'hidden':False},'checksum':'md5:'+approved['md5'],'ext':name.rsplit('.',1)[-1].lower(),'id':fid,'key':name,'metadata':{},'mimetype':response['mimetype'],'size':approved['size'],'storage_class':'L'}
def refresh_totals(native):
    rows=native['files']['entries'];native['files']['count']=len(rows);native['files']['total_bytes']=sum(x['size']for x in rows.values())
def public_projection(before,publish_response,rid):
    check(identifier(publish_response.get('id'))==rid and publish_response.get('state')=='done'and publish_response.get('submitted')is True,'OWN_TERMINAL_PUBLISH_RESPONSE')
    doi=publish_response.get('doi')or publish_response.get('metadata',{}).get('prereserve_doi',{}).get('doi');concept=publish_response.get('conceptdoi')
    check(doi==before['pids']['doi']['identifier']and isinstance(concept,str)and re.fullmatch('10[.]5281/zenodo[.][1-9][0-9]*',concept)is not None,'OWN_PUBLISH_DOI_CONCEPT')
    check(identifier(publish_response.get('conceptrecid'))==before['parent']['id'],'OWN_PUBLISH_PARENT')
    expected=deepcopy(before);expected.update(is_draft=False,is_published=True,status='published');expected['parent']['pids']={'doi':{'identifier':concept,'provider':'datacite','client':'datacite'}}
    expected['links']=deepcopy(before.get('links',{}));expected['links'].update(parent_doi='https://doi.org/'+concept,parent_doi_html='https://zenodo.org/doi/'+concept)
    for entry in expected['files']['entries'].values():
        entry['links']=deepcopy(entry.get('links',{}));entry['links'].update(self='https://zenodo.org/api/records/'+rid+'/files/'+entry['key'],content='https://zenodo.org/api/records/'+rid+'/files/'+entry['key']+'/content')
    return expected,doi,concept
def public_legacy_projection(template,native,public_metadata,doi,concept):
    # These public top-level fields were independently seen in the bound source
    # public representation. Any new top-level field remains a hard mismatch.
    fields={'conceptdoi','conceptrecid','created','doi','doi_url','files','id','links','metadata','modified','owners','recid','revision','state','stats','status','submitted','swh','title','updated'}
    check(set(template)<=fields and {'conceptdoi','conceptrecid','created','doi','doi_url','files','id','links','metadata','modified','owners','recid','revision','stats','title'}<=set(template),'PUBLIC_LEGACY_SOURCE_SCHEMA')
    rid=identifier(native['id']);parent=native['parent']['id'];result={}
    owner=native['parent']['access']['owned_by']['user'];check(template['owners']==[{'id':owner}],'SOURCE_PUBLIC_OWNER_SHAPE')
    values={'conceptdoi':concept,'conceptrecid':parent,'created':native['created'],'doi':doi,'doi_url':'https://doi.org/'+doi,'id':int(rid),'metadata':deepcopy(public_metadata),'modified':native['updated'],'owners':deepcopy(template['owners']),'recid':rid,'revision':native['revision_id'],'title':public_metadata['title'],'updated':native['updated'],'state':'done','status':'published','submitted':True,'swh':deepcopy(native.get('swh',{})),'links':{},'stats':{}}
    result={k:deepcopy(values[k])for k in template if k not in {'files'}}
    result['metadata']['doi']=doi;result['metadata']['relations']={'version':[{'index':1,'is_last':True,'parent':{'pid_type':'recid','pid_value':parent}}]}
    result['files']=[{'id':r['id'],'key':r['key'],'checksum':r['checksum'],'size':r['size'],'links':{'self':'https://zenodo.org/api/records/'+rid+'/files/'+r['key']+'/content'}}for r in native['files']['entries'].values()]
    return result
def require_public_legacy(actual,expected,native,sm,preservation):
    preservation.require_public_metadata(actual.get('metadata',{}),expected['metadata']);preservation.require_file_preservation(actual.get('files'),expected['files'])
    left,right=deepcopy(actual),deepcopy(expected)
    for k in ('metadata','files','links','stats'):left.pop(k,None);right.pop(k,None)
    check(exact(left,right),'PUBLIC_LEGACY_UNLISTED_OR_CONTENT_FIELD')
    sm.require_links_stats({'links':actual.get('links',{}),'stats':actual.get('stats',{}),'pids':native['pids']},{'links':{},'stats':{}},host='zenodo.org',record_id=native['id'])
    return {'status':'STRICT_COMPLETE_PUBLIC_LEGACY_PASS','record_id':native['id'],'all_source_and_remaining_fields_exact':True}
