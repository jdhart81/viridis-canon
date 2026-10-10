"""Pure dry-run metadata preparation. This module performs no network writes."""
import copy

UNCERTIFIED_STATEMENT = (
    "UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. "
    "Lean sources may compile but have not been independently certified. "
    "Results are conditional on the stated model assumptions."
)
HISTORICAL_SEPARATOR = '<hr/><p><strong>Historical description:</strong></p>'
API_DOCS = 'https://developers.zenodo.org/#deposit-metadata'
DEPOSITION_FIELDS = {
    'title','description','creators','contributors','publication_date','keywords',
    'related_identifiers','communities','access_right','access_conditions','embargo_date',
    'license','grants','notes','language','references','version','doi','subjects',
    'journal_title','journal_volume','journal_issue','journal_pages','conference_title',
    'conference_acronym','conference_dates','conference_place','conference_url',
    'conference_session','conference_session_part','imprint_publisher','imprint_isbn',
    'imprint_place','partof_title','partof_pages','thesis_supervisors','thesis_university',
    'upload_type','publication_type','image_type'
}


def amendment(before):
    if not isinstance(before,dict) or not isinstance(before.get('title'),str):
        raise ValueError('original metadata and exact title required')
    historical=before.get('description')
    if not isinstance(historical,str):raise ValueError('original description required')
    if UNCERTIFIED_STATEMENT in historical or 'Historical description:' in historical:
        raise ValueError('already labeled description requires a fresh reviewed baseline')
    after=copy.deepcopy(before)
    after['description']='<p><strong>'+UNCERTIFIED_STATEMENT+'</strong></p>'+HISTORICAL_SEPARATOR+historical
    keywords=before.get('keywords',[])
    if not isinstance(keywords,list) or any(not isinstance(k,str) for k in keywords):
        raise ValueError('invalid original keywords')
    after['keywords']=[k for k in keywords if k.casefold()!='conjecture']
    if not any(k.casefold()=='uncertified' for k in after['keywords']):after['keywords'].append('uncertified')
    validate_amendment(before,after)
    return after


def validate_amendment(before,after):
    if set(after)-set(before)-{'keywords'} or set(before)-set(after):
        raise ValueError('non-editable metadata field added or removed')
    for name in set(before)|set(after):
        if name not in ('description','keywords') and before.get(name)!=after.get(name):
            raise ValueError('metadata preservation failed: '+name)
    if after['description'].count(UNCERTIFIED_STATEMENT)!=1:
        raise ValueError('uncertified statement must appear exactly once')
    if HISTORICAL_SEPARATOR not in after['description']:raise ValueError('historical separator missing')
    if not after['description'].endswith(before['description']):raise ValueError('historical description changed')
    forbidden=('not machine-verified','Machine-checked: logical validity',
               'logical validity given the model, not empirical validation of its assumptions')
    if any(s.casefold() in after['description'].casefold() for s in forbidden):
        raise ValueError('contradictory or duplicated injected disclaimer')
    if 'uncertified' not in after['keywords'] or any(k.casefold()=='conjecture' for k in after['keywords']):
        raise ValueError('incorrect keyword')


def deposition_projection(public_metadata):
    """Documented transport conversions, never silent deletion of unknown fields.

    Public expected metadata remains complete. A projection is not execution
    approval: server graph preservation must be demonstrated in sandbox and
    an authenticated production deposition read must supply the final base.
    """
    wire=copy.deepcopy(public_metadata);changes=[];holds=[]
    if 'resource_type' in wire:
        rt=wire.pop('resource_type')
        if not isinstance(rt,dict) or rt.get('type') not in ('publication','poster','presentation','dataset','image','video','software','lesson','physicalobject','other'):
            raise ValueError('unmapped resource type')
        wire['upload_type']=rt['type']
        if rt['type']=='publication':
            if not rt.get('subtype'):raise ValueError('publication subtype missing')
            wire['publication_type']=rt['subtype']
        if rt['type']=='image':
            if not rt.get('subtype'):raise ValueError('image subtype missing')
            wire['image_type']=rt['subtype']
        changes.append({'field':'resource_type','classification':'DOCUMENTED_TRANSPORT_MAPPING',
            'reason':'Deposition API uses upload_type/publication_type/image_type; public display title is a response representation. Public expected resource_type stays exact.','docs':API_DOCS})
    if isinstance(wire.get('license'),dict):
        lic=wire['license']
        if not isinstance(lic.get('id'),str):raise ValueError('license identifier missing')
        wire['license']=lic['id']
        changes.append({'field':'license','classification':'DOCUMENTED_TRANSPORT_MAPPING',
            'reason':'Deposition metadata license is a string ID; public expected license object stays exact.','docs':API_DOCS})
    if 'communities' in wire:
        communities=[]
        for c in wire['communities']:
            if not isinstance(c,dict) or not isinstance(c.get('id',c.get('identifier')),str):raise ValueError('unmapped community')
            converted=copy.deepcopy(c)
            if 'id' in converted:converted['identifier']=converted.pop('id')
            communities.append(converted)
        if communities!=wire['communities']:
            changes.append({'field':'communities','classification':'DOCUMENTED_TRANSPORT_MAPPING',
                'reason':'Deposition API names community identifiers identifier rather than public record id. Expected community membership stays exact.','docs':API_DOCS})
        wire['communities']=communities
    if 'relations' in wire:
        wire.pop('relations')
        changes.append({'field':'relations','classification':'HOLD_SERVER_GRAPH_PRESERVATION_UNPROVEN',
            'reason':'relations is absent from documented deposition input; version actions create the server graph. This is an inference, not permission to drop relationships. Public expected relations are restored in after_payload. Actual authenticated edit metadata and sandbox readback are required.','docs':'https://developers.zenodo.org/#new-version'})
        holds.append('Server version graph preservation requires sandbox and authenticated deposition readback')
    unknown=sorted(set(wire)-DEPOSITION_FIELDS)
    for field in unknown:
        changes.append({'field':field,'classification':'HOLD_UNDOCUMENTED_FIELD_RESTORED',
            'reason':'No documented deposition-input mapping. Value retained unchanged; do not execute until authenticated deposition schema/readback confirms preservation.','docs':API_DOCS})
        holds.append('Undocumented input field retained: '+field)
    return {'metadata':wire},changes,holds


def field_table(before,after,wire):
    changes={c['field']:c for c in deposition_projection(after)[1]};rows=[]
    for field in sorted(set(before)|set(after)|set(wire['metadata'])):
        b=before.get(field);a=after.get(field);w=wire['metadata'].get(field)
        rows.append({'field':field,'before':copy.deepcopy(b),'after_expected_public':copy.deepcopy(a),
            'deposition_wire':copy.deepcopy(w),'logical_change':b!=a,'transport_change':a!=w,
            'assessment':changes.get(field,{'classification':'AUTHORIZED_DESCRIPTION_KEYWORDS_ONLY' if field in ('description','keywords') else 'EXACT_PRESERVATION' if b==a==w else 'DOCUMENTED_RESOURCE_TYPE_TRANSPORT_FIELD' if field in ('upload_type','publication_type','image_type') else 'HOLD_UNJUSTIFIED_CHANGE'})})
    return rows
