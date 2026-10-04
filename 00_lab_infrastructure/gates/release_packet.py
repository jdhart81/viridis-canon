"""Prepare reviewable metadata bytes only. No network or publication capability."""
from copy import deepcopy
import argparse
import hashlib
import html
import json
from pathlib import Path

LABEL = ("UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. "
         "Lean sources may compile but have not been independently certified. "
         "Results are conditional on the stated model assumptions.")
SEPARATOR = '<hr/><p><strong>Historical description (verification assertions below are not current certification labels):</strong></p>'
DOCS = 'https://developers.zenodo.org/#representation'
EDITABLE = {'title','description','keywords','creators','contributors','publication_date',
            'access_right','communities','related_identifiers','language','notes','version',
            'doi','license'}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()


def amendment(before):
    if not isinstance(before,dict) or not before.get('title') or not before.get('doi'):
        raise ValueError('title and exact existing DOI required')
    if not isinstance(before.get('description'),str):
        raise ValueError('original description required')
    after=deepcopy(before)
    historical=before['description']
    # Make repeat preparation idempotent without rewriting the original title.
    prefix='<p><strong>'+html.escape(LABEL, quote=False)+'</strong></p>'+SEPARATOR
    if historical.startswith(prefix):historical=historical[len(prefix):]
    after['description']=prefix+historical
    keywords=before.get('keywords',[])
    if not isinstance(keywords,list) or any(not isinstance(k,str) for k in keywords):
        raise ValueError('keywords must be a string list')
    after['keywords']=[k for k in keywords if k.lower() not in ('conjecture','uncertified')]+['uncertified']
    if after['title']!=before['title']:raise ValueError('title changed')
    changes=[k for k in before.keys() | after.keys() if before.get(k)!=after.get(k)]
    if set(changes)-{'description','keywords'}:raise ValueError('unapproved metadata field change')
    return after


def deposition_projection(metadata, new_version=False):
    """Separate documented API shapes from the unchanged expected public readback.

    Unknown/custom fields are never silently dropped: they make the plan HOLD.
    Server-maintained version relations remain mandatory readback invariants.
    """
    result={k:deepcopy(v) for k,v in metadata.items() if k in EDITABLE}
    reasons=[]
    if 'communities' in result:
        communities=result['communities']
        if not isinstance(communities,list):raise ValueError('community list required')
        projected=[]
        for community in communities:
            if not isinstance(community,dict):raise ValueError('community object required')
            identifier=community.get('identifier',community.get('id'))
            if not identifier or set(community)-{'identifier','id'}:
                reasons.append('HOLD_UNSUPPORTED_COMMUNITY_SHAPE')
            projected.append({'identifier':identifier})
        result['communities']=projected
    resource=metadata.get('resource_type')
    if not isinstance(resource,dict) or not resource.get('type'):
        raise ValueError('resource type required')
    result['upload_type']=resource['type']
    if resource['type']=='publication':
        if not resource.get('subtype'):raise ValueError('publication subtype required')
        result['publication_type']=resource['subtype']
    license_value=metadata.get('license')
    if isinstance(license_value,dict) and set(license_value)=={'id'}:
        result['license']=license_value['id']
    elif not isinstance(license_value,str):
        reasons.append('HOLD_UNSUPPORTED_LICENSE_SHAPE')
    unknown=sorted(set(metadata)-EDITABLE-{'resource_type','relations'})
    for name in unknown:reasons.append('HOLD_UNSUPPORTED_FIELD:'+name)
    if new_version:result.pop('doi',None)
    table=[]
    for name,value in metadata.items():
        if name=='resource_type':
            action='API_SHAPE: upload_type/publication_type; public resource_type must read back unchanged'
        elif name=='license':
            action='API_SHAPE: license identifier string; public license object must read back unchanged'
        elif name=='communities':
            action='API_SHAPE: documented identifier key; public community IDs must read back unchanged'
        elif name=='relations':
            action='SERVER_MANAGED: edit retains exact chain; new version must extend same parent with one successor'
        elif name=='doi' and new_version:
            action='SERVER_ASSIGNED_NEW_VERSION_DOI: old DOI remains intact; never copy it into a new version'
        elif name in unknown:
            action='HOLD: unsupported legacy deposition field; use documented preserving API or exclude this transaction'
        else:action='PRESERVED_EXACTLY'
        table.append({'field':name,'action':action,'documentation':DOCS,
                      'before_value':deepcopy(value),'api_value':deepcopy(result.get(name)),
                      'expected_readback_value':deepcopy(value)})
    return {'metadata':result},table,reasons


def prepare_amendment(before):
    after=amendment(before)
    payload,table,reasons=deposition_projection(after)
    rollback,_,rollback_reasons=deposition_projection(before)
    return {'mode':'DRY_RUN_ONLY','execution_authorized':False,'writes_executed':0,
            'status':'HOLD' if reasons else 'PREPARED_AWAITING_APPROVAL',
            'reasons':reasons+rollback_reasons,'before_metadata':deepcopy(before),
            'expected_after_metadata':after,'api_payload':payload,'payload_sha256':digest(payload),
            'rollback_payload':rollback,'rollback_payload_sha256':digest(rollback),
            'field_preservation':table,'allowed_public_changes':['description','keywords']}


def build_amendment_plan(source, out):
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    records=[]
    for row in source['records']:
        if row['operation']!='CONJECTURE_METADATA_AMENDMENT':continue
        prepared=prepare_amendment(row['before_metadata'])
        prepared.update(doi=row['doi'],record_id=row['record_id'],concept_id=row['concept_id'],
                        before_read_at_utc=row['before_read_at_utc'],operation='UNCERTIFIED_METADATA_AMENDMENT',
                        before_metadata_sha256=digest(row['before_metadata']),
                        preconditions=row['preconditions']+[
                            'Exact title, DOI, license, resource type and relations must survive authenticated draft and public readback',
                            'Unsupported fields require a preserving API route and sandbox proof; HOLD cannot be approved away',
                            'No upload or file deletion in a metadata-only amendment'],
                        rollback_note=row['rollback'])
        d=out/row['record_id'];d.mkdir()
        for name,value in [('before_metadata',prepared['before_metadata']),
                           ('expected_after_metadata',prepared['expected_after_metadata']),
                           ('after_payload',prepared['api_payload']),
                           ('rollback_payload',prepared['rollback_payload']),
                           ('field_preservation',prepared['field_preservation'])]:
            (d/(name+'.json')).write_bytes(encode(value))
        base='https://zenodo.org/api/deposit/depositions/'+row['record_id']
        prepared['api_calls']=[{'method':'GET','url':base,'purpose':'fresh exact metadata and files preflight'},
            {'method':'POST','url':base+'/actions/edit','body':{}},
            {'method':'PUT','url':base,'payload_file':str(d/'after_payload.json'),'sha256':prepared['payload_sha256']},
            {'method':'POST','url':base+'/actions/publish','body':{},'precondition':'approved exact payload and preserved draft readback'},
            {'method':'GET','url':'https://zenodo.org/api/records/'+row['record_id'],'purpose':'strict public readback; abort on mismatch'}]
        prepared['payload_file']=str(d/'after_payload.json')
        (d/'PLAN.json').write_bytes(encode(prepared));records.append(prepared)
    result={'mode':'DRY_RUN_ONLY','execution_authorized':False,'writes_executed':0,
            'record_count':len(records),'records':records,'source_sha256':digest(source)}
    (out/'AMENDMENT_PLAN.json').write_bytes(encode(result))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=build_amendment_plan(json.loads(args.source.read_text()),args.out)
    print(json.dumps({'prepared':result['record_count'],'hold':sum(r['status']=='HOLD' for r in result['records']),
                      'production_writes':0}))


if __name__=='__main__':main()
