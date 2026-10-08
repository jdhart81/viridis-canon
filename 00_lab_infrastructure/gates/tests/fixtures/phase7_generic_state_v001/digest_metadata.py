"""Closed source-bound legacy API encoding and native metadata prediction.

The approved digest's public metadata remains unchanged. Only documented API
representations of resource_type and license are encoded for deposition input.
The native metadata is predicted from a fresh, bound source pair, never from
the new draft's metadata. This module confers no scientific approval.
"""
from copy import deepcopy
import re
class MetadataHold(ValueError):pass
FIELDS={'creators','license','access_right','communities','language','resource_type','upload_type','publication_type','title','description','publication_date','keywords','related_identifiers'}
PROTECTED=('creators','license','access_right','communities','language','resource_type')
def exact(a,b):
    import json
    return json.dumps(a,sort_keys=True,allow_nan=False,separators=(',',':'))==json.dumps(b,sort_keys=True,allow_nan=False,separators=(',',':'))
def check(v,c):
    if not v:raise MetadataHold('HOLD_'+c)
def license_id(v):
    if isinstance(v,str)and v:return v
    if isinstance(v,dict)and set(v)=={'id'}and isinstance(v['id'],str)and v['id']:return v['id']
    raise MetadataHold('HOLD_LICENSE_SHAPE')
def closed_payload(public,approved_source):
    check(isinstance(public,dict)and not(set(public)-FIELDS),'UNSUPPORTED_DIGEST_METADATA_FIELD')
    check(all(k in public for k in ('creators','license','access_right','title','description','publication_date','keywords','resource_type')),'REQUIRED_DIGEST_METADATA')
    for key in PROTECTED:
        check((key in public)==(key in approved_source)and exact(public.get(key),approved_source.get(key)),'SOURCE_FIELD_CHANGED_'+key)
    # This approved first digest uses the source's existing open preprint type;
    # no record-type or license choice is made here.
    typ=public['resource_type'];check(isinstance(typ,dict)and set(typ)=={'type','subtype','title'}and typ['type']=='publication'and typ['subtype']=='preprint','CLOSED_SOURCE_RESOURCE_TYPE')
    check(public['access_right']=='open','OPEN_SOURCE_ONLY')
    payload=deepcopy(public);payload.pop('resource_type');payload['upload_type']=typ['type'];payload['publication_type']=typ['subtype'];payload['license']=license_id(public['license'])
    for key in('upload_type','publication_type'):
        if key in public:check(public[key]==payload[key],'API_TYPE_CONFLICT_'+key)
    return {'metadata':payload}
def creator_projection(native):
    check(isinstance(native,list)and native,'NATIVE_CREATORS')
    rows=[]
    for c in native:
        check(isinstance(c,dict)and set(c)=={'affiliations','person_or_org'},'CREATOR_FIELDS')
        p=c['person_or_org'];check(isinstance(p,dict)and set(p)=={'family_name','given_name','identifiers','name','type'}and p['type']=='personal','PERSON_FIELDS')
        check(p['name']==p['family_name']+', '+p['given_name'],'PERSON_NAME_COMPONENTS')
        aff=c['affiliations'];check(isinstance(aff,list)and len(aff)<=1 and all(isinstance(a,dict)and set(a)=={'name'}and isinstance(a['name'],str)for a in aff),'AFFILIATION_FIELDS')
        row={'name':p['name']}
        if aff:row['affiliation']=aff[0]['name']
        ids=p['identifiers'];check(isinstance(ids,list),'CREATOR_IDENTIFIERS');seen=set()
        for i in ids:
            check(isinstance(i,dict)and set(i)=={'identifier','scheme'}and i['scheme']in {'orcid','gnd'}and i['scheme']not in seen and isinstance(i['identifier'],str),'CREATOR_IDENTIFIER_FIELDS')
            seen.add(i['scheme']);row[i['scheme']]=i['identifier']
        rows.append(row)
    return rows
def native_metadata(public,approved_source,fresh_legacy,fresh_native,relation_template):
    """Every preserved source field is checked against both saved fresh views."""
    check(isinstance(fresh_legacy,dict)and isinstance(fresh_native,dict),'SOURCE_PAIR_SHAPE')
    legacy=fresh_legacy.get('metadata');native=fresh_native.get('metadata');check(isinstance(legacy,dict)and isinstance(native,dict),'SOURCE_PAIR_METADATA')
    rid=str(fresh_legacy.get('id'));check(re.fullmatch('[1-9][0-9]*',rid)is not None and fresh_native.get('id')==rid,'SOURCE_PAIR_RECORD_ID')
    check(fresh_legacy.get('doi')==fresh_native.get('pids',{}).get('doi',{}).get('identifier'),'SOURCE_PAIR_DOI')
    for key in PROTECTED:
        check((key in approved_source)==(key in legacy)and exact(approved_source.get(key),legacy.get(key)),'FRESH_SOURCE_CHANGED_'+key)
    closed_payload(public,approved_source)
    check(exact(creator_projection(native.get('creators')),approved_source['creators']),'NATIVE_CREATOR_SOURCE')
    rights=native.get('rights');check(isinstance(rights,list)and len(rights)==1 and rights[0].get('id')==license_id(approved_source['license']),'NATIVE_LICENSE_SOURCE')
    typ=approved_source['resource_type'];check(native.get('resource_type',{}).get('id')==typ['type']+'-'+typ['subtype'],'NATIVE_RESOURCE_SOURCE')
    languages=native.get('languages');check(isinstance(languages,list)and len(languages)==1 and languages[0].get('id')==approved_source.get('language'),'NATIVE_LANGUAGE_SOURCE')
    access=fresh_native.get('access');check(access=={'record':'public','files':'public','status':'open','embargo':{'active':False,'reason':None}},'SOURCE_ACCESS')
    template=relation_template.get('relation_type',relation_template);check(isinstance(template,dict)and set(template)=={'id','title'}and template['id']=='issupplementto'and isinstance(template['title'],dict)and template['title'].get('en')=='Is supplement to','RELATION_VOCABULARY')
    result={k:deepcopy(native[k])for k in ('creators','rights','resource_type','languages')}
    result.update(title=public['title'],description=public['description'],publication_date=public['publication_date'],publisher=native.get('publisher'))
    check(result['publisher']=='Zenodo','SOURCE_PUBLISHER')
    result['subjects']=[{'subject':k}for k in public['keywords']]
    relations=public.get('related_identifiers',[]);check(isinstance(relations,list),'RELATED_IDENTIFIERS')
    if relations:
        result['related_identifiers']=[];seen=set()
        for r in relations:
            check(isinstance(r,dict)and set(r)=={'identifier','relation','scheme'}and r['relation']=='isSupplementTo'and r['scheme']=='doi'and re.fullmatch('10[.]5281/zenodo[.][1-9][0-9]*',str(r['identifier']))is not None and r['identifier']not in seen,'SOURCE_BOUND_SUPPLEMENT_RELATION')
            seen.add(r['identifier']);result['related_identifiers'].append({'identifier':r['identifier'],'relation_type':deepcopy(template),'scheme':'doi'})
    return result
