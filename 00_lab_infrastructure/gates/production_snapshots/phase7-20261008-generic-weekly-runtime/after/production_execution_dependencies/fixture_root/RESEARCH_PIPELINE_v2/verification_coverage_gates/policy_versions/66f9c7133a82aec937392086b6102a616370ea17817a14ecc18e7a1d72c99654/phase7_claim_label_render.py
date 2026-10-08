"""Pure approved-label rendering. Validated audit policy remains admission owner."""
import re
import hashlib
from copy import deepcopy
TIERS={'DEFINITIONAL','ROUTINE','SUBSTANTIVE','UNCLASSIFIED','DEPTH_NOT_ASSESSED'}
TIER_PRINT={'UNCLASSIFIED':'UNCLASSIFIED (probe resource-limited)','DEPTH_NOT_ASSESSED':'depth not yet assessed'}
MARKER='% VRS_PHASE7_APPROVED_CLAIM_LABEL_TABLE_1'
def _latex(value):
    if not isinstance(value,str)or not value or any(ord(c)<32 for c in value):raise ValueError('literal one-line claim label required')
    text=''.join(c if ord(c)<128 else (('\\u%04x'if ord(c)<=0xffff else'\\U%08x')%ord(c))for c in value)
    return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','_':r'\_\allowbreak{}','%':r'\%','&':r'\&','#':r'\#','$':r'\$','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}.get(c,c)for c in text)
def render_claim_table(claim_reviews):
    if not isinstance(claim_reviews,list)or not claim_reviews:raise ValueError('all approved claim reviews required')
    names=[];rows=[];eligible=[]
    for row in claim_reviews:
        if not isinstance(row,dict)or set(row)!={'lean_theorem','semantic_tier','nonvacuity'}or row['semantic_tier']not in TIERS:raise ValueError('closed semantic label row required')
        name=row['lean_theorem'];_latex(name)
        if name in names:raise ValueError('duplicate claim label')
        names.append(name);nv=row['nonvacuity'];semantic=row['semantic_tier']
        if not isinstance(nv,dict):raise ValueError('nonvacuity classification required')
        if nv.get('tier')=='TIER0':
            if set(nv)!={'tier','status','domains'}or nv['status']!='NO_HYPOTHESES'or not isinstance(nv['domains'],list)or not nv['domains']:raise ValueError('closed Tier0 domain rule required')
            for d in nv['domains']:_latex(d)
            label='NO_HYPOTHESES (domain nonempty: '+', '.join(nv['domains'])+')';demonstrated=True
        elif nv.get('tier')=='TIER1'and nv.get('status')=='CERTIFIED_WITNESS':
            if set(nv)!={'tier','status','witness_theorem','certificate'}or not isinstance(nv['certificate'],dict)or set(nv['certificate'])!={'path','sha256'}or re.fullmatch('[0-9a-f]{64}',str(nv['certificate']['sha256']))is None:raise ValueError('closed exact certified witness label required')
            _latex(nv['witness_theorem']);_latex(nv['certificate']['path'])
            label='CERTIFIED_WITNESS: '+nv['witness_theorem']+'; certificate SHA-256 '+nv['certificate']['sha256'];demonstrated=True
        elif nv.get('tier')=='TIER1'and nv.get('status')=='NOT_DEMONSTRATED':
            if set(nv)!={'tier','status'}:raise ValueError('closed undemonstrated state required')
            label='certified; nonvacuity not demonstrated';demonstrated=False
        else:raise ValueError('unknown witness state')
        headline=demonstrated and semantic!='DEFINITIONAL';eligible.append(headline)
        rows.extend([r'\par\noindent\texttt{'+_latex(name)+'}: '+_latex(TIER_PRINT.get(semantic,semantic))+'. '+_latex(label)+'. '+('Eligible for a scoped mathematical result headline.'if headline else'Excluded from certified-result headlines; appendix status only.')])
    return ('\n'+MARKER+'\n'+r'\section*{Approved claim classifications}'+'\n'+r'\noindent Labels follow the approved Phase 7 audit rules. The unchanged Comparator certificate proves only its bound mathematical statements. Downgrade probes are not independent certification. No empirical validation is implied.'+'\n'+('\\par\\noindent This entire Methods Note is admitted to the weekly digest appendix only; no certified-result headline credit.\n'if not any(eligible)else'')+'\n'.join(rows)+'\n% END VRS_PHASE7_APPROVED_CLAIM_LABEL_TABLE_1\n')
def apply_review_labels(base_tex,claim_reviews):
    if not isinstance(base_tex,bytes):raise ValueError('exact audited TeX bytes required')
    text=base_tex.decode('utf-8')
    if MARKER in text:raise ValueError('already labeled source; no nested/repeated table')
    match=re.search(r'\\section\*?\{(?:Main results|Certified-scope)[^}]*\}',text)
    if not match:raise ValueError('exact main/certified scope insertion boundary required')
    table=render_claim_table(claim_reviews)
    return (text[:match.start()]+table+text[match.start():]).encode('utf-8')

def shift_whole_paper_map(original,old,new,table):
 """Preserve exact claim content; shift byte/character provenance spans honestly."""
 value=deepcopy(original);oldtext=old.decode();newtext=new.decode();insert=new.index(table.encode());delta=len(table.encode());charinsert=len(new[:insert].decode());chardelta=len(table)
 for family in ('formal_section_spans','successor_regions','uncertified_remark_spans'):
  for row in value.get(family,[]):
   char=row.get('offset_encoding')=='UNICODE_CHARACTER_OFFSETS';source=oldtext if char else old;target=newtext if char else new;pos=charinsert if char else insert;amount=chardelta if char else delta
   start=row['byte_start'];end=row['byte_end_exclusive'];segment=source[start:end];raw=segment.encode()if char else segment
   key='section_sha256'if 'section_sha256'in row else'sha256'
   if key in row and hashlib.sha256(raw).hexdigest()!=row[key]:raise ValueError('audited coverage span hash differs')
   row['byte_start']=start+(amount if start>=pos else 0);row['byte_end_exclusive']=end+(amount if end>pos or end==pos and start>=pos else 0)
   if 'start_offset'in row:row['start_offset']=row['byte_start']
   if 'end_offset'in row:row['end_offset']=row['byte_end_exclusive']
   fragment=target[row['byte_start']:row['byte_end_exclusive']];row[key]=hashlib.sha256(fragment.encode()if char else fragment).hexdigest()
 value['nonclaim_regions']=[*value.get('nonclaim_regions',[]),'approved-rule semantic/nonvacuity label table; no new theorem statement']
 return value

