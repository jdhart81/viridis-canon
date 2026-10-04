"""Readback checks for authorized edits; no network or publication authority."""
from copy import deepcopy
from html.parser import HTMLParser
import re
from zenodo_transport import TransportHold

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

def require_native_preservation(before,after,description,keywords):
    left=deepcopy(before['metadata']);right=deepcopy(after['metadata'])
    left.pop('description',None);right.pop('description',None)
    left.pop('subjects',None);right.pop('subjects',None)
    if left!=right:raise TransportHold('READBACK_MISMATCH_NATIVE_PROTECTED_METADATA')
    if description_tokens(after['metadata'].get('description'))!=description_tokens(description):raise TransportHold('READBACK_MISMATCH_NATIVE_DESCRIPTION')
    if [s.get('subject') for s in after['metadata'].get('subjects',[])]!=keywords:raise TransportHold('READBACK_MISMATCH_NATIVE_KEYWORDS')
    for key in ('custom_fields','access','files'):
        if before.get(key)!=after.get(key):raise TransportHold('READBACK_MISMATCH_NATIVE:'+key)
