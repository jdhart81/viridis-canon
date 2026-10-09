"""Explicit own-record payload comparison under the approved 2026-10-08 rule.

No transport, credentials, writes, certificates, or proof evaluation. Genuine
bound ownership precedes every relaxed housekeeping comparison. Unknown or
ambiguous scope never obtains this policy. Prior semantic content remains exact; approved processing differences are
retained as full diagnostics under the 2026-10-09 restatement.
"""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import hashlib, json, re

STANDARD='VRS-METHODS-DIGEST-OWN-RECORD-CONTEXT-1'
AUDIT_STANDARD='VRS-OWN-RECORD-COMPARISON-AUDIT-1'
STATUS='SOURCE_BOUND_OWN_RECORD_CONTROLLED_CONTEXT'
BASE='https://zenodo.org'
NATIVE='application/vnd.inveniordm.v1+json'
AUTHORITY_HEADER='## Own-record comparison principle (ends Zenodo field stops) — 2026-10-08 (evening)'
AUTHORITY_SECTION_SHA256='0073d050290065b1a661f6edc1472005c21f44f5eb2196aa03179d51daa35864'
CONTROL_FIELDS={'record_id','concept_id','phase','native_metadata','legacy_metadata','files','communities','native_community_ids','doi_required'}
OWNERSHIP_FIELDS={'creation_receipt','first_native_receipt','first_legacy_receipt','prior_ids'}
CONTEXT_ROLES={'authority','digest_manifest','source_legacy_receipt','source_native_receipt','creation_receipt','first_own_native_draft','first_own_legacy_draft','metadata_payload','metadata_put_receipt','relation_template','reservation_receipt','before_publish_native_receipt','publish_receipt','prior_after_native_receipt','prior_after_legacy_receipt'}
CONTEXT_FIELDS={'standard','status','phase','record_id','producer_sha256','source_bindings'}

class OwnRecordHold(ValueError):pass

def need(value, reason):
    if not value:raise OwnRecordHold('HOLD_OWN_RECORD_'+reason)

def raw_json(value):return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
def exact(left,right):return raw_json(left)==raw_json(right)
def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def identifier(value):
    need(type(value)is str and re.fullmatch('[1-9][0-9]*',value)is not None,'CANONICAL_ID')
    return value

def record_identifier(value):
    need(type(value)in(str,int),'ID_TYPE')
    return identifier(str(value))

def receipt(value,*,method,url,native=False,code=None):
    need(isinstance(value,dict)and value.get('environment')=='zenodo.org'and value.get('method')==method and value.get('url')==url and value.get('status')=='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'and type(value.get('http_status'))is int and 200<=value['http_status']<300 and isinstance(value.get('response'),dict)and re.fullmatch('[0-9a-f]{64}',str(value.get('response_sha256')))is not None,'GENUINE_RECEIPT')
    if code is not None:need(value['http_status']==code,'EXACT_HTTP_STATUS')
    if native:need(value.get('accept')==NATIVE,'NATIVE_RECEIPT')
    if method!='GET':need(re.fullmatch('[0-9a-f]{64}',str(value.get('request_body_sha256')))is not None,'REQUEST_BODY_HASH')
    return value['response']

def require_authority(raw):
    need(type(raw)is bytes,'AUTHORITY_BYTES')
    token=AUTHORITY_HEADER.encode();need(raw.count(token)==1,'UNIQUE_AUTHORITY')
    at=raw.index(token);end=raw.find(b'\n## ',at+len(token));section=raw[at:]if end<0 else raw[at:end]
    if hashlib.sha256(section).hexdigest()!=AUTHORITY_SECTION_SHA256:
        need(any(section.endswith(suffix)and hashlib.sha256(section[:-len(suffix)]).hexdigest()==AUTHORITY_SECTION_SHA256 for suffix in(b'\n---\n',b'\n---\n\n')),'EXACT_APPROVED_AUTHORITY')
    return {'section_sha256':AUTHORITY_SECTION_SHA256,'actual_sha256':hashlib.sha256(raw).hexdigest()}

PRIOR_AUTHORITY_HEADER='## Prior-record rule narrowed to content we control — 2026-10-09'
PRIOR_AUTHORITY_SECTION_SHA256='43b52d2f91d41bfbe3fba1294203a3c725cf4fd6064e037b833888aa82d1c080'
LEGACY_OWN_SOURCE_SHA256='cf74da23ea7208260cee70f74f282b2b57a209d1347f14d4c47b465f2b50ebd8'

# Closed processing paths. Semantic metadata/PIDs/version identity and unknown
# fields never enter this list. Main-file names/bytes/checksums remain exact.
_PROCESSING_ROOTS=frozenset({'media_files','stats','counters','ui','swh','revision','revision_id','revision_counter','updated','updated_at','modified','indexing_status','processing_status','indexing_state','processing_state'})
_PROCESSING_LINKS=frozenset({'thumbnails','thumbs','thumb250','preview','preview_html','iiif_api','iiif_base','iiif_canvas','iiif_info','iiif_manifest','iiif_image','self_iiif_manifest','self_iiif_sequence','archive_media','media_files'})
_PROCESSING_FILE_FIELDS=frozenset({'updated','updated_at','revision','revision_id','revision_counter','indexing_status','processing_status','indexing_state','processing_state','processor','processing'})

def require_prior_authority(raw):
    need(type(raw)is bytes,'PRIOR_AUTHORITY_BYTES')
    token=PRIOR_AUTHORITY_HEADER.encode();need(raw.count(token)==1,'UNIQUE_PRIOR_AUTHORITY')
    at=raw.index(token);end=raw.find(b'\n## ',at+len(token));section=raw[at:]if end<0 else raw[at:end]
    if hashlib.sha256(section).hexdigest()!=PRIOR_AUTHORITY_SECTION_SHA256:
        need(any(section.endswith(suffix)and hashlib.sha256(section[:-len(suffix)]).hexdigest()==PRIOR_AUTHORITY_SECTION_SHA256 for suffix in(b'\n---\n',b'\n---\n\n')),'EXACT_APPROVED_PRIOR_AUTHORITY')
    need(raw.index(AUTHORITY_HEADER.encode())<at,'PRIOR_AUTHORITY_ORDER')
    return {'section_sha256':PRIOR_AUTHORITY_SECTION_SHA256,'actual_sha256':hashlib.sha256(raw).hexdigest()}

def require_bound_authority(root,binding):
    """Reconsume immutable snapshot + exact live section before any own write."""
    import methods_digest as digest
    root=Path(root).resolve(strict=True)
    _,authority_raw=digest.bound_file(root,binding);authority=json.loads(authority_raw)
    need(isinstance(authority,dict)and set(authority)=={'standard','authority_snapshot','section_sha256','actual_sha256'}and authority['standard']=='VRS-EXACT-OWN-RECORD-AUTHORITY-1'and authority['section_sha256']==AUTHORITY_SECTION_SHA256,'BOUND_AUTHORITY_OBSERVATION')
    live=root/'reports/verification-coverage/GAME_PLAN.md'
    snapshot,snapshot_raw=digest.bound_file(root,authority['authority_snapshot'])
    need(snapshot!=live,'IMMUTABLE_AUTHORITY_SNAPSHOT_NOT_LIVE_PLAN')
    own_proof=require_authority(snapshot_raw);prior_proof=require_prior_authority(snapshot_raw)
    need(own_proof['actual_sha256']==authority['actual_sha256'],'IMMUTABLE_APPROVED_AUTHORITY_SNAPSHOT')
    live_raw=digest.read_regular(live);require_authority(live_raw);require_prior_authority(live_raw)
    need(digest.bound_file(root,binding)[1]==authority_raw and digest.bound_file(root,authority['authority_snapshot'])[1]==snapshot_raw and digest.read_regular(live)==live_raw,'AUTHORITY_INPUT_RACE')
    return {'status':'EXACT_CURRENT_PRIOR_AUTHORITY_SNAPSHOT_AND_SECTION_PASS','own_section_sha256':AUTHORITY_SECTION_SHA256,'prior_section_sha256':PRIOR_AUTHORITY_SECTION_SHA256,'authority':deepcopy(binding),'authority_snapshot':deepcopy(authority['authority_snapshot']),'live_sha256':hashlib.sha256(live_raw).hexdigest(),'certifies':False}

def _prior_links(value):
    if not isinstance(value,dict):return deepcopy(value)
    return {k:deepcopy(v)for k,v in value.items()if k not in _PROCESSING_LINKS}

def _prior_file(row):
    need(isinstance(row,dict),'PRIOR_FILE_ROW')
    result={k:deepcopy(v)for k,v in row.items()if k not in _PROCESSING_FILE_FIELDS}
    if 'links'in result:result['links']=_prior_links(result['links'])
    return result

def prior_protected_projection(value,*,representation):
    need(isinstance(value,dict)and representation in{'NATIVE','LEGACY'},'PRIOR_PROJECTION_SCOPE')
    raw_json(value)
    result={k:deepcopy(v)for k,v in value.items()if k not in _PROCESSING_ROOTS}
    if 'links'in result:result['links']=_prior_links(result['links'])
    if isinstance(result.get('parent'),dict):
        result['parent']={k:deepcopy(v)for k,v in result['parent'].items()if k not in _PROCESSING_ROOTS}
        if 'links'in result['parent']:result['parent']['links']=_prior_links(result['parent']['links'])
    if 'files'in result:
        files=result['files']
        if representation=='NATIVE':
            need(isinstance(files,dict)and isinstance(files.get('entries'),dict),'PRIOR_NATIVE_FILES')
            entries={}
            for name,row in files['entries'].items():
                need(type(name)is str and isinstance(row,dict)and row.get('key')==name,'PRIOR_NATIVE_FILE_NAME')
                entries[name]=_prior_file(row)
            result['files']={k:deepcopy(v)for k,v in files.items()if k not in _PROCESSING_FILE_FIELDS}
            result['files']['entries']=entries
        else:
            need(isinstance(files,list),'PRIOR_LEGACY_FILES')
            entries={}
            for row in files:
                need(isinstance(row,dict),'PRIOR_LEGACY_FILE_ROW')
                name=row.get('key',row.get('filename'))
                need(type(name)is str and name and name not in entries,'PRIOR_LEGACY_FILE_UNIQUENESS')
                need('key'not in row or row['key']==name,'PRIOR_LEGACY_FILE_KEY')
                need('filename'not in row or row['filename']==name,'PRIOR_LEGACY_FILE_FILENAME')
                entries[name]=_prior_file(row)
            # The protected file contract is filename-keyed names/bytes/hash/count.
            # Full observed array order remains in the comparison diagnostics.
            result['files']=[entries[name]for name in sorted(entries)]
    return result

def _prior_differences(before,after,path='$'):
    if exact(before,after):return []
    if isinstance(before,dict)and isinstance(after,dict):
        rows=[]
        for key in sorted(set(before)|set(after)):
            at=path+'.'+key
            if key not in before:rows.append({'path':at,'before_present':False,'after_present':True,'after':deepcopy(after[key]),'after_type':type(after[key]).__name__})
            elif key not in after:rows.append({'path':at,'before_present':True,'after_present':False,'before':deepcopy(before[key]),'before_type':type(before[key]).__name__})
            else:rows.extend(_prior_differences(before[key],after[key],at))
        return rows
    if isinstance(before,list)and isinstance(after,list)and len(before)==len(after):
        return [row for i,(a,b)in enumerate(zip(before,after))for row in _prior_differences(a,b,path+'['+str(i)+']')]
    return [{'path':path,'before_present':True,'after_present':True,'before':deepcopy(before),'after':deepcopy(after),'before_type':type(before).__name__,'after_type':type(after).__name__}]

def require_prior_semantics(actual,before,*,representation):
    left=prior_protected_projection(actual,representation=representation);right=prior_protected_projection(before,representation=representation)
    differences=_prior_differences(before,actual)
    if not exact(left,right):
        error=OwnRecordHold('HOLD_OWN_RECORD_PRIOR_PROTECTED_CONTENT_CHANGED')
        error.audit={'representation':representation,'before':deepcopy(before),'after':deepcopy(actual),'differences':differences,'protected_differences':_prior_differences(right,left),'certifies':False}
        raise error
    return {'standard':'VRS-PRIOR-PROTECTED-CONTENT-COMPARISON-1','status':'PRIOR_RECORD_PROTECTED_READBACK_PASS','representation':representation,'authority_section_sha256':PRIOR_AUTHORITY_SECTION_SHA256,'protected_sha256':hashlib.sha256(raw_json(right)).hexdigest(),'before':deepcopy(before),'after':deepcopy(actual),'differences':differences,'processing_differences':deepcopy(differences),'certifies':False}

def creation_date(value):
    need(type(value)is str,'AUTHENTICATED_CREATION_TIME')
    try:stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:raise OwnRecordHold('HOLD_OWN_RECORD_CREATION_TIME')from exc
    need(stamp.tzinfo is not None,'AUTHENTICATED_CREATION_TIME')
    # The approved initial draft date is its authenticated creation UTC date.
    return stamp.astimezone(timezone.utc).date().isoformat()

def publication_date(value):
    need(type(value)is str,'EXPLICIT_NY_PUBLISH_TIME')
    try:stamp=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:raise OwnRecordHold('HOLD_OWN_RECORD_NY_PUBLISH_TIME')from exc
    need(stamp.tzinfo is not None,'EXPLICIT_NY_PUBLISH_TIME')
    return stamp.astimezone(ZoneInfo('America/New_York')).date().isoformat()

def require_metadata_put(payload,*,publish_at):
    need(isinstance(payload,dict)and set(payload)=={'metadata'}and isinstance(payload['metadata'],dict),'EXACT_METADATA_PUT')
    wanted=publication_date(publish_at)
    need(payload['metadata'].get('publication_date')==wanted,'EXPLICIT_NY_PUBLICATION_DATE')
    return deepcopy(payload)

def require_ownership(creation_receipt, first_native_receipt, first_legacy_receipt, *, prior_ids):
    need(isinstance(prior_ids,list)and len(prior_ids)==len(set(prior_ids))and all(type(x)is str and re.fullmatch('[1-9][0-9]*',x)for x in prior_ids),'UNIQUE_PRIOR_IDENTITIES')
    response=creation_receipt.get('response',{})if isinstance(creation_receipt,dict)else{}
    rid=record_identifier(response.get('id'));parent=record_identifier(response.get('conceptrecid'))
    need(rid not in prior_ids and rid!=parent,'OWN_NEW_SCOPE_ONLY')
    url=creation_receipt.get('url');newversion=re.fullmatch(re.escape(BASE)+'/api/deposit/depositions/([1-9][0-9]*)/actions/newversion',str(url))
    need(url==BASE+'/api/deposit/depositions'or(newversion is not None and newversion[1]in prior_ids),'OWN_START_ENDPOINT')
    created=receipt(creation_receipt,method='POST',url=url,code=201)
    if newversion:need(creation_receipt['request_body_sha256']==hashlib.sha256(b'{}').hexdigest(),'NEWVERSION_EMPTY_BODY')
    first_native=receipt(first_native_receipt,method='GET',url=BASE+'/api/records/'+rid+'/draft',native=True,code=200)
    first_legacy=receipt(first_legacy_receipt,method='GET',url=BASE+'/api/deposit/depositions/'+rid,code=200)
    need(first_native.get('id')==rid and record_identifier(first_legacy.get('id'))==rid and first_native.get('parent',{}).get('id')==parent and record_identifier(first_legacy.get('conceptrecid'))==parent,'OWN_FIRST_PAIR_IDENTITIES')
    # The genuine creation ACK supplies the approved initial date. First-GET
    # timestamps are own housekeeping; endpoint and pair identities prove scope.
    day=creation_date(created.get('created'))
    return {'record_id':rid,'concept_id':parent,'creation_publication_date':day,'start_kind':'NEW_VERSION'if newversion else'CREATE_WEEK'}

def _controls(value):
    need(isinstance(value,dict)and set(value)==CONTROL_FIELDS,'CLOSED_CONTROLLED_EXPECTATIONS')
    identifier(value['record_id']);identifier(value['concept_id']);need(value['record_id']!=value['concept_id'],'DISTINCT_CHILD_CONCEPT')
    need(value['phase']in{'DRAFT','PUBLISHED'}and type(value['doi_required'])is bool,'EXPLICIT_PHASE_PID_SCOPE')
    if value['phase']=='PUBLISHED':need(value['doi_required']is True,'PUBLIC_DOI_REQUIRED')
    for field in('native_metadata','legacy_metadata'):
        metadata=value[field];need(isinstance(metadata,dict)and {'title','description','publication_date'}<=set(metadata),'CONTROLLED_SCIENTIFIC_METADATA')
        need(type(metadata['publication_date'])is str and re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}',metadata['publication_date'])is not None,'EXPLICIT_PUBLICATION_DATE')
    need(value['native_metadata']['publication_date']==value['legacy_metadata']['publication_date'],'PAIR_CONTROLLED_DATE')
    rows=value['files'];need(isinstance(rows,list),'CONTROLLED_FILES');names=[]
    for row in rows:
        need(isinstance(row,dict)and set(row)=={'name','bytes','md5'}and type(row['name'])is str and row['name']not in{'','.','..'}and '/'not in row['name']and '\\'not in row['name']and type(row['bytes'])is int and row['bytes']>=0 and re.fullmatch('[0-9a-f]{32}',str(row['md5']))is not None,'CONTROLLED_FILE_ROW');names.append(row['name'])
    need(len(names)==len(set(names)),'UNIQUE_CONTROLLED_FILES')
    communities=value['communities'];need(isinstance(communities,list)and all(isinstance(c,dict)and set(c)=={'identifier'}and type(c['identifier'])is str and c['identifier']for c in communities),'CONTROLLED_COMMUNITIES')
    need(len({c['identifier']for c in communities})==len(communities),'UNIQUE_COMMUNITIES')
    ids=value['native_community_ids'];need(isinstance(ids,list)and all(type(i)is str and i for i in ids)and len(ids)==len(set(ids))and len(ids)==len(communities),'CONTROLLED_NATIVE_MEMBERSHIP')
    raw_json(value)
    return value

def _sent_equal(actual,expected):
    if isinstance(expected,dict):return isinstance(actual,dict)and all(key in actual and _sent_equal(actual[key],value)for key,value in expected.items())
    if isinstance(expected,list):return isinstance(actual,list)and len(actual)==len(expected)and all(_sent_equal(a,b)for a,b in zip(actual,expected))
    return exact(actual,expected)

def native_sent_metadata(projected):
    result=deepcopy(projected);result.pop('publisher',None)
    for key in('rights','languages'):
        if key in result:result[key]=[{'id':row['id']}for row in result[key]]
    if 'resource_type'in result:result['resource_type']={'id':result['resource_type']['id']}
    for row in result.get('related_identifiers',[]):row['relation_type']={'id':row['relation_type']['id']}
    return result

def legacy_sent_metadata(projected):
    result=deepcopy(projected)
    if isinstance(result.get('resource_type'),dict):result['resource_type'].pop('title',None)
    return result

def _community_identifiers(rows):
    need(isinstance(rows,list),'LEGACY_COMMUNITY_SHAPE');answer=[]
    for row in rows:
        need(isinstance(row,dict)and ('id'in row or 'identifier'in row),'LEGACY_COMMUNITY_ROW')
        values=[row[key]for key in('id','identifier')if key in row]
        need(all(type(value)is str and value for value in values),'LEGACY_COMMUNITY_IDENTIFIER')
        need(all(value==values[0]for value in values),'CONTRADICTORY_COMMUNITY_IDENTIFIER')
        answer.append(values[0])
    return answer

def _metadata(actual,expected,label):
    need(isinstance(actual,dict),'METADATA_'+label)
    for key,wanted in expected.items():
        need(key in actual,'SENT_METADATA_'+label+'_'+key)
        if label=='LEGACY'and key=='communities':
            need(exact(_community_identifiers(actual[key]),_community_identifiers(wanted)),'SENT_METADATA_LEGACY_communities')
        else:need(_sent_equal(actual[key],wanted),'SENT_METADATA_'+label+'_'+key)
    # Absent payload lists mean an explicitly empty content set, not free space.
    for key in('related_identifiers',):
        if key not in expected:need(actual.get(key,[])==[],'UNSENT_CONTENT_'+label+'_'+key)

def _files(native,legacy,rows):
    want={r['name']:r for r in rows};entries=native.get('files',{}).get('entries');need(isinstance(entries,dict)and set(entries)==set(want),'NATIVE_EXACT_FILE_NAMES')
    for key,wanted in(('count',len(want)),('total_bytes',sum(r['bytes']for r in rows))):
        if key in native['files']:need(type(native['files'][key])is int and native['files'][key]==wanted,'CONTRADICTORY_NATIVE_FILE_'+key.upper())
    for name,row in entries.items():
        need(isinstance(row,dict)and row.get('key')==name and type(row.get('size'))is int and row['size']==want[name]['bytes']and row.get('checksum')=='md5:'+want[name]['md5'],'NATIVE_EXACT_FILE_BYTES')
        if 'filename'in row:need(row['filename']==name,'CONTRADICTORY_NATIVE_FILE_NAME')
        if 'filesize'in row:need(type(row['filesize'])is int and row['filesize']==want[name]['bytes'],'CONTRADICTORY_NATIVE_FILE_SIZE')
    files=legacy.get('files');need(isinstance(files,list)and len(files)==len(want),'LEGACY_EXACT_FILE_NAMES');seen=set()
    for row in files:
        need(isinstance(row,dict),'LEGACY_FILE_OBJECT');name=row.get('filename',row.get('key'))
        need(type(name)is str and name in want and name not in seen,'LEGACY_UNIQUE_FILE_NAMES');seen.add(name)
        size=row.get('filesize',row.get('size'));checksum=row.get('checksum');checksum=checksum[4:]if type(checksum)is str and checksum.startswith('md5:')else checksum
        need(type(size)is int and size==want[name]['bytes']and checksum==want[name]['md5'],'LEGACY_EXACT_FILE_BYTES')
        if 'filename'in row and 'key'in row:need(row['filename']==row['key'],'CONTRADICTORY_FILE_NAME')
        if 'filesize'in row and 'size'in row:need(type(row['filesize'])is int and type(row['size'])is int and row['filesize']==row['size'],'CONTRADICTORY_FILE_SIZE')

def _identities(native,legacy,c):
    rid=c['record_id'];parent=c['concept_id'];doi='10.5281/zenodo.'+rid;concept='10.5281/zenodo.'+parent
    need(native.get('id')==rid and record_identifier(legacy.get('id'))==rid and native.get('parent',{}).get('id')==parent and record_identifier(legacy.get('conceptrecid'))==parent,'EXACT_OWN_CONCEPT_IDENTITIES')
    for key in('recid','record_id'):
        for view in(native,legacy):
            if key in view:need(record_identifier(view[key])==rid,'CONTRADICTORY_RECORD_ID')
    if 'conceptrecid'in native:need(record_identifier(native['conceptrecid'])==parent,'CONTRADICTORY_NATIVE_CONCEPT_ID')
    native_doi=native.get('pids',{}).get('doi');legacy_doi=legacy.get('doi');parent_doi=native.get('parent',{}).get('pids',{}).get('doi')
    for row,wanted,label in((native_doi,doi,'DOI'),(parent_doi,concept,'CONCEPT_DOI')):
        if row is not None:need(isinstance(row,dict)and row.get('identifier')==wanted,'CONTRADICTORY_'+label)
    for row,wanted,label in((native.get('pids',{}).get('oai'),'oai:zenodo.org:'+rid,'OAI'),(native.get('parent',{}).get('pids',{}).get('oai'),'oai:zenodo.org:'+parent,'CONCEPT_OAI')):
        if isinstance(row,dict)and row.get('identifier')is not None:need(row['identifier']==wanted,'CONTRADICTORY_'+label)
    for metadata in(native.get('metadata',{}),legacy.get('metadata',{})):
        if 'doi'in metadata:need(metadata['doi']==doi,'CONTRADICTORY_METADATA_DOI')
        if 'prereserve_doi'in metadata:
            p=metadata['prereserve_doi'];need(isinstance(p,dict)and p.get('doi')==doi and record_identifier(p.get('recid'))==rid,'CONTRADICTORY_PRERESERVE_DOI')
    if legacy_doi is not None:need(legacy_doi==doi,'CONTRADICTORY_LEGACY_DOI')
    if 'conceptdoi'in legacy:need(legacy['conceptdoi']==concept,'CONTRADICTORY_LEGACY_CONCEPT_DOI')
    if c['doi_required']:need(isinstance(native_doi,dict)and legacy_doi==doi,'OWN_RESERVED_OR_PUBLIC_DOI_REQUIRED')
    for view,key in((native,'native_metadata'),(legacy,'legacy_metadata')):
        if 'title'in view:need(exact(view['title'],c[key]['title']),'CONTRADICTORY_TOP_TITLE')

def _access(native,c):
    access=c['legacy_metadata'].get('access_right')
    if access=='open':
        actual=native.get('access');need(isinstance(actual,dict)and actual.get('record')=='public'and actual.get('files')=='public','CONTRADICTORY_SENT_OPEN_ACCESS')
        embargo=actual.get('embargo',{})
        if 'active'in embargo:need(embargo['active']is False,'CONTRADICTORY_SENT_OPEN_EMBARGO')

def _communities(native,legacy,c):
    expected=[x['identifier']for x in c['communities']]
    ids=_community_identifiers(legacy.get('metadata',{}).get('communities',[]))
    need(exact(ids,expected),'EXACT_CONTROLLED_COMMUNITIES')
    graph=native.get('parent',{}).get('communities',{})
    custom=native.get('custom_fields',{});need(isinstance(custom,dict),'CUSTOM_FIELDS_OBJECT')
    empty=isinstance(graph,dict)and exact(graph.get('ids',[]),[])and exact(graph.get('entries',[]),[])and graph.get('default')is None
    if c['phase']=='DRAFT'and expected and empty:
        # The proven first-draft protocol records requested membership in the
        # exact legacy list/mirror before the public native graph activates.
        need('legacy:communities'in custom and exact(custom['legacy:communities'],expected),'EXACT_PENDING_DRAFT_COMMUNITY_MIRROR')
    elif not c['native_community_ids']:need(empty,'CONTRADICTORY_NATIVE_COMMUNITIES')
    else:
        need(isinstance(graph,dict)and exact(graph.get('ids'),c['native_community_ids']),'EXACT_NATIVE_COMMUNITY_IDENTITIES')
        entries=graph.get('entries');need(isinstance(entries,list)and len(entries)==len(expected)and all(isinstance(x,dict)for x in entries),'NATIVE_COMMUNITY_ENTRIES')
        need(exact([x.get('id')for x in entries],c['native_community_ids'])and exact([x.get('slug')for x in entries],expected),'NATIVE_COMMUNITY_ASSOCIATION')
        if 'default'in graph:need(graph['default']in c['native_community_ids'],'CONTRADICTORY_NATIVE_DEFAULT_COMMUNITY')
    if 'legacy:communities'in custom:need(exact(custom['legacy:communities'],expected),'CONTRADICTORY_COMMUNITY_MIRROR')

def _housekeeping(value,metadata_controls):
    answer=deepcopy(value)
    for key in('id','record_id','recid','conceptrecid','doi','conceptdoi','files','title'):answer.pop(key,None)
    if isinstance(answer.get('metadata'),dict):
        for key in set(metadata_controls)|{'doi','prereserve_doi','communities','related_identifiers'}:answer['metadata'].pop(key,None)
    if isinstance(answer.get('pids'),dict)and isinstance(answer['pids'].get('doi'),dict):answer['pids']['doi'].pop('identifier',None)
    if isinstance(answer.get('parent'),dict):
        answer['parent'].pop('id',None)
        if isinstance(answer['parent'].get('pids'),dict)and isinstance(answer['parent']['pids'].get('doi'),dict):answer['parent']['pids']['doi'].pop('identifier',None)
        graph=answer['parent'].get('communities')
        if isinstance(graph,dict):
            for key in('ids','default'):graph.pop(key,None)
            for row in graph.get('entries',[]):
                if isinstance(row,dict):row.pop('id',None);row.pop('slug',None)
    # UUIDs, preview URLs, file aliases, media derivatives and minted PID
    # representations remain visible even though main bytes already matched.
    answer['file_housekeeping']=deepcopy(value.get('files'))
    answer['observed_record']=deepcopy(value)
    return answer

def require_own_readback(native,legacy,*,controlled,ownership):
    """Revalidate scope and exact independent controls; log every other field."""
    need(isinstance(ownership,dict)and set(ownership)==OWNERSHIP_FIELDS,'CLOSED_OWNERSHIP_SOURCES')
    scope=require_ownership(ownership['creation_receipt'],ownership['first_native_receipt'],ownership['first_legacy_receipt'],prior_ids=ownership['prior_ids'])
    c=_controls(controlled);need(scope['record_id']==c['record_id']and scope['concept_id']==c['concept_id'],'BOUND_OWN_SCOPE')
    need(isinstance(native,dict)and isinstance(legacy,dict),'PAIR_READBACK_OBJECTS')
    raw_json(native);raw_json(legacy)
    _identities(native,legacy,c);_metadata(native.get('metadata'),c['native_metadata'],'NATIVE');_metadata(legacy.get('metadata'),c['legacy_metadata'],'LEGACY');_files(native,legacy,c['files']);_access(native,c);_communities(native,legacy,c)
    return {'standard':AUDIT_STANDARD,'status':'OWN_RECORD_CONTROLLED_READBACK_PASS','record_id':c['record_id'],'concept_id':c['concept_id'],'phase':c['phase'],'controlled_sha256':hashlib.sha256(raw_json(c)).hexdigest(),'checks':{name:{'status':'PASS'}for name in('ownership','metadata','files','doi_concept_identity','related_identifiers','communities','description_banner','access_right')},'housekeeping':{'native':_housekeeping(native,c['native_metadata']),'legacy':_housekeeping(legacy,c['legacy_metadata'])},'certifies':False}

def compare_or_strict(native,legacy,*,controlled,ownership,strict_consumer):
    """A missing ownership claim uses the existing strict route, never this rule."""
    if ownership is None:return strict_consumer(native,legacy)
    # An invalid explicit claim holds; it is never silently treated as own.
    return require_own_readback(native,legacy,controlled=controlled,ownership=ownership)

def require_prior_exact(actual,before,*,representation,boundary):
    need(isinstance(actual,dict)and isinstance(before,dict)and representation in{'NATIVE','LEGACY'}and boundary in{'CREATE','EDIT','PUBLISH','DISCARD'},'PRIOR_SCOPE')
    left,right=deepcopy(actual),deepcopy(before);changed=[]
    if representation=='NATIVE':
        a=left.get('versions');b=right.get('versions');need(isinstance(a,dict)and isinstance(b,dict),'PRIOR_VERSIONS')
        transitions={'CREATE':{'is_latest_draft':(True,False)},'EDIT':{},'PUBLISH':{'is_latest':(True,False)},'DISCARD':{'is_latest_draft':(False,True)}}[boundary]
        for key,(old,new)in transitions.items():
            need(type(a.get(key))is bool and type(b.get(key))is bool,'PRIOR_FLAG_TYPE')
            if a[key]!=b[key]:need(b[key]is old and a[key]is new,'PRIOR_APPROVED_FLAG_TRANSITION');a[key]=b[key];changed.append('versions.'+key)
    elif boundary=='PUBLISH':
        a=left.get('metadata',{}).get('relations',{}).get('version');b=right.get('metadata',{}).get('relations',{}).get('version')
        need(isinstance(a,list)and isinstance(b,list)and len(a)==len(b)==1 and isinstance(a[0],dict)and isinstance(b[0],dict),'PRIOR_LEGACY_RELATION')
        need(type(a[0].get('is_last'))is bool and type(b[0].get('is_last'))is bool,'PRIOR_LEGACY_FLAG_TYPE')
        if a[0]['is_last']!=b[0]['is_last']:need(b[0]['is_last']is True and a[0]['is_last']is False,'PRIOR_LEGACY_APPROVED_FLAG_TRANSITION');a[0]['is_last']=b[0]['is_last'];changed.append('metadata.relations.version[0].is_last')
    audit=require_prior_semantics(left,right,representation=representation)
    audit.update({'status':'PRIOR_RECORD_PROTECTED_EXCEPT_APPROVED_VERSION_FLAGS_PASS','changed_flags':changed,'observed_before':deepcopy(before),'observed_after':deepcopy(actual)})
    return audit

def initial_projection(prior_legacy,prior_native,creation_receipt,first_legacy_receipt,first_native_receipt):
    """Derive inherited controls before PUT; only authenticated creation date resets."""
    src=record_identifier(prior_legacy.get('id'));parent=identifier(prior_native.get('parent',{}).get('id'))
    need(prior_native.get('id')==src and record_identifier(prior_legacy.get('conceptrecid'))==parent,'SOURCE_PAIR_IDENTITIES')
    scope=require_ownership(creation_receipt,first_native_receipt,first_legacy_receipt,prior_ids=[src])
    need(scope['concept_id']==parent,'SAME_CONCEPT_INITIAL_SCOPE')
    native_metadata=deepcopy(prior_native['metadata']);native_metadata['publication_date']=scope['creation_publication_date']
    # Use the existing request/private representation codec on source metadata.
    import digest_metadata as metadata
    import first_digest_state as codec
    public={k:deepcopy(v)for k,v in prior_legacy['metadata'].items()if k in metadata.FIELDS}
    public['publication_date']=scope['creation_publication_date']
    payload=codec.encode_api_communities(metadata.closed_payload(public,public))
    legacy_metadata=deepcopy(payload['metadata'])
    files=[]
    for name,row in prior_native.get('files',{}).get('entries',{}).items():
        need(isinstance(row,dict)and row.get('key')==name and type(row.get('size'))is int and re.fullmatch('md5:[0-9a-f]{32}',str(row.get('checksum')))is not None,'INHERITED_SOURCE_FILE_BYTES')
        files.append({'name':name,'bytes':row['size'],'md5':row['checksum'][4:]})
    communities=codec.community_request(public.get('communities',[]))
    graph=prior_native.get('parent',{}).get('communities',{})
    control={'record_id':scope['record_id'],'concept_id':parent,'phase':'DRAFT','native_metadata':native_sent_metadata(native_metadata),'legacy_metadata':legacy_metadata,'files':sorted(files,key=lambda x:x['name']),'communities':communities,'native_community_ids':deepcopy(graph.get('ids',[])),'doi_required':False}
    ownership={'creation_receipt':creation_receipt,'first_native_receipt':first_native_receipt,'first_legacy_receipt':first_legacy_receipt,'prior_ids':[src]}
    audit=require_own_readback(first_native_receipt['response'],first_legacy_receipt['response'],controlled=control,ownership=ownership)
    return {'controlled':control,'ownership':ownership,'audit':audit,'native':deepcopy(first_native_receipt['response']),'legacy':deepcopy(first_legacy_receipt['response'])}

def assemble_context(*,record_id,source_bindings):
    """Bind exact current source roles; construction itself never admits a record."""
    identifier(record_id);need(isinstance(source_bindings,dict)and set(source_bindings)==CONTEXT_ROLES,'COMPLETE_CONTEXT_ROLES')
    for value in source_bindings.values():
        need(isinstance(value,dict)and set(value)=={'path','sha256'}and type(value['path'])is str and re.fullmatch('[0-9a-f]{64}',str(value['sha256']))is not None,'BOUND_CONTEXT_SOURCE')
    return {'standard':STANDARD,'status':STATUS,'phase':'PUBLISHED','record_id':record_id,'producer_sha256':source_sha(),'source_bindings':deepcopy(source_bindings)}

def _wire_payload(payload):return json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False).encode()+b'\n'

def public_projection(controlled):
    """Predict only controlled public fields; never manufacture housekeeping."""
    c=_controls(controlled);rid=c['record_id'];parent=c['concept_id'];doi='10.5281/zenodo.'+rid
    native={'id':rid,'parent':{'id':parent},'metadata':deepcopy(c['native_metadata']),'files':{'entries':{r['name']:{'key':r['name'],'size':r['bytes'],'checksum':'md5:'+r['md5']}for r in c['files']}},'pids':{'doi':{'identifier':doi}}}
    legacy={'id':int(rid),'conceptrecid':parent,'doi':doi,'metadata':deepcopy(c['legacy_metadata']),'files':[{'key':r['name'],'size':r['bytes'],'checksum':'md5:'+r['md5'],'links':{'self':BASE+'/api/records/'+rid+'/files/'+r['name']+'/content'}}for r in c['files']]}
    return native,legacy

def consume_context(context,*,load,public,evidence_sources):
    """Source-derived control plane; no after metadata or caller PASS is trusted."""
    need(isinstance(context,dict)and set(context)==CONTEXT_FIELDS and context['standard']==STANDARD and context['status']==STATUS and context['phase']=='PUBLISHED'and context['producer_sha256']==source_sha(),'CURRENT_OWN_CONTEXT')
    rid=identifier(context['record_id']);bindings=context['source_bindings'];need(isinstance(bindings,dict)and set(bindings)==CONTEXT_ROLES,'CLOSED_CONTEXT_ROLES')
    for role,key in(('source_legacy_receipt','source_legacy_receipt'),('source_native_receipt','source_native_receipt'),('publish_receipt','own_publish_receipt')):
        need(exact(bindings[role],evidence_sources[key]),'CONTEXT_EVIDENCE_ROLE_'+role)
    objects={role:load(binding)for role,binding in bindings.items()}
    authority=objects['authority'];need(isinstance(authority,dict)and set(authority)=={'standard','authority_snapshot','section_sha256','actual_sha256'}and authority['standard']=='VRS-EXACT-OWN-RECORD-AUTHORITY-1'and authority['section_sha256']==AUTHORITY_SECTION_SHA256,'BOUND_AUTHORITY_OBSERVATION')
    # The original approved authority bytes are immutable registration inputs.
    # A later approved appendix must not invalidate a permanent registration.
    import methods_digest as digest
    authority_path=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/GAME_PLAN.md')
    snapshot_binding=authority['authority_snapshot']
    snapshot_path,snapshot_raw=digest.bound_file(authority_path.parents[2],snapshot_binding)
    need(snapshot_path!=authority_path,'IMMUTABLE_AUTHORITY_SNAPSHOT_NOT_LIVE_PLAN')
    snapshot_proof=require_authority(snapshot_raw)
    prior_snapshot_proof=require_prior_authority(snapshot_raw)
    need(snapshot_proof['actual_sha256']==authority['actual_sha256'],'IMMUTABLE_APPROVED_AUTHORITY_SNAPSHOT')
    authority_raw=digest.read_regular(authority_path)
    proof=require_authority(authority_raw)
    prior_authority_proof=require_prior_authority(authority_raw)
    manifest=objects['digest_manifest'];need(isinstance(manifest,dict)and exact(manifest.get('public_metadata'),public),'ACTUAL_MANIFEST_PAYLOAD')
    source_id=record_identifier(objects['source_legacy_receipt'].get('response',{}).get('id'))
    sl=receipt(objects['source_legacy_receipt'],method='GET',url=BASE+'/api/records/'+source_id,code=200)
    sn=receipt(objects['source_native_receipt'],method='GET',url=BASE+'/api/records/'+source_id,native=True,code=200)
    scope=require_ownership(objects['creation_receipt'],objects['first_own_native_draft'],objects['first_own_legacy_draft'],prior_ids=[source_id]);need(scope['record_id']==rid,'OWN_CONTEXT_CREATION_IDENTITY')
    parent=scope['concept_id'];ownership={'creation_receipt':objects['creation_receipt'],'first_native_receipt':objects['first_own_native_draft'],'first_legacy_receipt':objects['first_own_legacy_draft'],'prior_ids':[source_id]}
    # Both prior readbacks are real observations, not an inferred prior PASS.
    prior_n=receipt(objects['prior_after_native_receipt'],method='GET',url=BASE+'/api/records/'+source_id,native=True,code=200)
    prior_l=receipt(objects['prior_after_legacy_receipt'],method='GET',url=BASE+'/api/records/'+source_id,code=200)
    prior_audits=[]
    if scope['start_kind']=='NEW_VERSION':
        after_create=deepcopy(sn);need(after_create.get('versions',{}).get('is_latest_draft')is True,'SOURCE_LATEST_DRAFT_BEFORE_CREATE');after_create['versions']['is_latest_draft']=False
        prior_audits.append(require_prior_exact(after_create,sn,representation='NATIVE',boundary='CREATE'))
        prior_audits.append(require_prior_exact(prior_n,after_create,representation='NATIVE',boundary='PUBLISH'));prior_audits.append(require_prior_exact(prior_l,sl,representation='LEGACY',boundary='PUBLISH'))
    else:
        prior_audits.append(require_prior_exact(prior_n,sn,representation='NATIVE',boundary='EDIT'));prior_audits.append(require_prior_exact(prior_l,sl,representation='LEGACY',boundary='EDIT'))
    before=receipt(objects['before_publish_native_receipt'],method='GET',url=BASE+'/api/records/'+rid+'/draft',native=True,code=200)
    publish=receipt(objects['publish_receipt'],method='POST',url=BASE+'/api/deposit/depositions/'+rid+'/actions/publish')
    need(record_identifier(publish.get('id'))==rid and record_identifier(publish.get('conceptrecid'))==parent and publish.get('doi')=='10.5281/zenodo.'+rid,'GENUINE_OWN_PUBLIC_IDENTITY')
    reserved=receipt(objects['reservation_receipt'],method='POST',url=BASE+'/api/records/'+rid+'/draft/pids/doi',native=True,code=201)
    need(objects['reservation_receipt']['request_body_sha256']==hashlib.sha256(b'{}').hexdigest()and reserved.get('id')==rid and reserved.get('parent',{}).get('id')==parent and reserved.get('pids',{}).get('doi',{}).get('identifier')=='10.5281/zenodo.'+rid,'GENUINE_OWN_RESERVATION')
    bp=Path(bindings['before_publish_native_receipt']['path']);pp=Path(bindings['publish_receipt']['path']);bm=re.fullmatch('([0-9]{3})_GET[.]json',bp.name);pm=re.fullmatch('([0-9]{3})_POST[.]json',pp.name)
    need(bp.parent==pp.parent and bm is not None and pm is not None and int(pm[1])==int(bm[1])+1,'FINAL_PREPUBLISH_CAUSAL_ROLE')
    import digest_metadata as metadata
    import first_digest_state as codec
    payload=codec.encode_api_communities(metadata.closed_payload(public,sl['metadata']))
    need(exact(objects['metadata_payload'],payload),'SENT_PAYLOAD_EXACT_MANIFEST')
    if scope['start_kind']=='CREATE_WEEK':
        need(exact(bindings['metadata_put_receipt'],bindings['creation_receipt']),'CREATE_WEEK_SENT_METADATA_ROLE')
        put=receipt(objects['metadata_put_receipt'],method='POST',url=BASE+'/api/deposit/depositions',code=201)
    else:put=receipt(objects['metadata_put_receipt'],method='PUT',url=BASE+'/api/deposit/depositions/'+rid)
    need(objects['metadata_put_receipt']['request_body_sha256']==hashlib.sha256(_wire_payload(payload)).hexdigest(),'GENUINE_EXACT_METADATA_PUT_BODY')
    # The publication package already fixes its explicit NY publish day. The
    # live caller checks the actual NY day at PUBLISH. Earlier PUTs use that
    # same planned publish date, even when performed on an earlier day.
    need(re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}',str(public.get('publication_date')))is not None,'EXPLICIT_MANIFEST_PUBLICATION_DATE')
    native_metadata=metadata.native_metadata(public,sl['metadata'],sl,sn,objects['relation_template'])
    uploads=list(manifest.get('uploads',[]))
    for name in('DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
        package=Path(bindings['digest_manifest']['path']).parent;raw=digest.read_regular(package/name)
        uploads.append({'filename':name,'bytes':len(raw),'md5':hashlib.md5(raw).hexdigest()})
    files=[{'name':r['filename'],'bytes':r['bytes'],'md5':r['md5']}for r in uploads]
    graph=sn.get('parent',{}).get('communities',{})
    controlled={'record_id':rid,'concept_id':parent,'phase':'PUBLISHED','native_metadata':native_sent_metadata(native_metadata),'legacy_metadata':legacy_sent_metadata(public),'files':sorted(files,key=lambda x:x['name']),'communities':codec.community_request(public.get('communities',[])),'native_community_ids':deepcopy(graph.get('ids',[])),'doi_required':True}
    # The acknowledged PUT must already satisfy the sent representation. It
    # does not define any expected value or supply a publication PASS.
    _metadata(put.get('metadata'),payload['metadata'],'PUT_ACK')
    expected_native,expected_legacy=public_projection(controlled)
    expected_legacy['metadata']=deepcopy(public)
    return {'record_id':rid,'native':expected_native,'legacy':expected_legacy,'legacy_relation':None,'source_legacy':sl,'source_native':sn,'before_native':before,'controlled':controlled,'ownership':ownership,'own_record_context_standard':STANDARD,'authority':proof,'prior_authority':prior_authority_proof,'prior_processing_audits':prior_audits,'extra_inputs':{str(authority_path):proof['actual_sha256'],str(snapshot_path):snapshot_proof['actual_sha256']}}


_consume_context_current_prior_content = consume_context

def consume_context(context,*,load,public,evidence_sources):
    # Permanent sealed cf74 contexts re-run their exact historical consumer.
    if isinstance(context,dict)and context.get('producer_sha256')==LEGACY_OWN_SOURCE_SHA256:
        import own_record_comparison_legacy_cf74da as historical
        need(hashlib.sha256(Path(historical.__file__).read_bytes()).hexdigest()==LEGACY_OWN_SOURCE_SHA256,'EXACT_HISTORICAL_OWN_SOURCE')
        return historical.consume_context(context,load=load,public=public,evidence_sources=evidence_sources)
    return _consume_context_current_prior_content(context,load=load,public=public,evidence_sources=evidence_sources)
