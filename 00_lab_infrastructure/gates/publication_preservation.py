"""Readback checks for authorized edits; no network or publication authority."""
from copy import deepcopy
from html.parser import HTMLParser
import re
import json
from zenodo_transport import TransportHold

def require_file_preservation(actual, expected):
    """Ignore only array order for unique Zenodo filenames; retain every field.

    A duplicate on either side makes filename indexing ambiguous, so compare
    the complete ordered lists instead. Malformed or absent input fails closed.
    """
    for entries in (actual, expected):
        if not isinstance(entries, list) or any(
            not isinstance(entry, dict) or not isinstance(entry.get('key'), str)
            or not entry['key'] for entry in entries
        ):
            raise TransportHold('READBACK_MISMATCH_FILES_INPUT')
    def exact(value):
        try:
            return json.dumps(value, sort_keys=True, ensure_ascii=False,
                              separators=(',', ':'), allow_nan=False)
        except (TypeError, ValueError):
            raise TransportHold('READBACK_MISMATCH_FILES_INPUT') from None
    unique = all(len({entry['key'] for entry in entries}) == len(entries)
                 for entries in (actual, expected))
    if not unique:
        if exact(actual) != exact(expected):
            raise TransportHold('READBACK_MISMATCH_FILES_STRICT_ORDERED')
        return {'mode': 'STRICT_ORDERED_DUPLICATE_FILENAMES', 'count': len(actual)}
    left = {entry['key']: entry for entry in actual}
    right = {entry['key']: entry for entry in expected}
    if set(left) != set(right):
        raise TransportHold('READBACK_MISMATCH_FILES_FILENAME_SET')
    if exact(left) != exact(right):
        raise TransportHold('READBACK_MISMATCH_FILES_PER_FILE_FIELDS')
    return {'mode': 'FILENAME_KEYED_SET', 'count': len(actual)}

class _Description(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.tokens=[]
    def handle_starttag(self,tag,attrs):
        if tag!='hr':self.tokens.append(('open',tag,tuple(sorted(attrs))))
    def handle_startendtag(self,tag,attrs):
        if tag!='hr':self.tokens.append(('empty',tag,tuple(sorted(attrs))))
    def handle_endtag(self,tag):
        if tag!='hr':self.tokens.append(('close',tag))
    def handle_data(self,data):
        value=re.sub(r'\s+',' ',data).strip()
        if value:self.tokens.append(('text',value))
    def handle_comment(self,data):self.tokens.append(('comment',data))

def description_tokens(value):
    if not isinstance(value,str):raise TransportHold('READBACK_MISMATCH_DESCRIPTION_TYPE')
    parser=_Description();parser.feed(value);parser.close();return parser.tokens

def require_public_metadata(actual,expected):
    fields=[]
    for key in actual.keys()|expected.keys():
        equal=(description_tokens(actual.get(key))==description_tokens(expected.get(key))) if key=='description' else actual.get(key)==expected.get(key)
        if not equal:fields.append(key)
    if fields:raise TransportHold('READBACK_MISMATCH_PUBLIC:'+','.join(sorted(fields)))

def managed_pid_payload(original_public,draft):
    """Restore only the original PID object, never choose a new identifier."""
    original=original_public.get('pids');current=draft.get('pids')
    if not isinstance(original,dict) or not isinstance(current,dict):raise TransportHold('HOLD_MISSING_PIDS')
    doi=original.get('doi',{})
    if not doi.get('identifier') or doi.get('provider')!='datacite':raise TransportHold('HOLD_UNKNOWN_ORIGINAL_DOI_PROVIDER')
    if current.get('doi',{}).get('identifier')!=doi['identifier']:raise TransportHold('READBACK_MISMATCH_DOI_IDENTIFIER')
    required=('metadata','custom_fields','access','files')
    if any(key not in draft for key in required):raise TransportHold('HOLD_INCOMPLETE_NATIVE_DRAFT')
    return {**{key:deepcopy(draft[key]) for key in required},'pids':deepcopy(original)}

def _require_custom_fields(before,after,existing_communities,mirror_proof):
    left=before.get('custom_fields');right=after.get('custom_fields')
    if left==right:return
    if not isinstance(mirror_proof,dict) or mirror_proof.get('status')!='SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN' or mirror_proof.get('public_post_publish_exact_preservation') is not True:
        raise TransportHold('READBACK_MISMATCH_NATIVE:custom_fields')
    if not isinstance(left,dict) or not isinstance(right,dict) or not isinstance(existing_communities,list) or not existing_communities:
        raise TransportHold('READBACK_MISMATCH_COMMUNITY_MIRROR_INPUT')
    ids=[]
    for community in existing_communities:
        if not isinstance(community,dict) or set(community)!={'id'} or not isinstance(community['id'],str):
            raise TransportHold('READBACK_MISMATCH_COMMUNITY_ID_SHAPE')
        ids.append(community['id'])
    # Only the tested field may be added, with exactly the existing public IDs.
    expected=deepcopy(left)
    if 'legacy:communities' in expected and expected['legacy:communities']!=ids:
        raise TransportHold('READBACK_MISMATCH_EXISTING_LEGACY_COMMUNITIES')
    expected['legacy:communities']=ids
    if right!=expected:raise TransportHold('READBACK_MISMATCH_COMMUNITY_MIRROR_VALUE_OR_OTHER_FIELD')

def require_native_preservation(before,after,description,keywords,*,existing_communities=None,mirror_proof=None):
    left=deepcopy(before['metadata']);right=deepcopy(after['metadata'])
    left.pop('description',None);right.pop('description',None)
    left.pop('subjects',None);right.pop('subjects',None)
    if left!=right:raise TransportHold('READBACK_MISMATCH_NATIVE_PROTECTED_METADATA')
    if description_tokens(after['metadata'].get('description'))!=description_tokens(description):raise TransportHold('READBACK_MISMATCH_NATIVE_DESCRIPTION')
    if [s.get('subject') for s in after['metadata'].get('subjects',[])]!=keywords:raise TransportHold('READBACK_MISMATCH_NATIVE_KEYWORDS')
    _require_custom_fields(before,after,existing_communities,mirror_proof)
    for key in ('access','files'):
        if before.get(key)!=after.get(key):raise TransportHold('READBACK_MISMATCH_NATIVE:'+key)
