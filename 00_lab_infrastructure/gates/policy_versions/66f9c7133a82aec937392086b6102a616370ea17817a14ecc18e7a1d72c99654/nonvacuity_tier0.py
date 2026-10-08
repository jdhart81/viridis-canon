"""Approved Oct-7 premise-free nonvacuity classification; never Lean verification.

The caller must first validate the unchanged candidate certificate. This module
documents nonempty quantification domains; it cannot certify a theorem, approve
a physical premise, or replace a Tier-1 Comparator witness.
"""
from __future__ import annotations
import hashlib
import re
from scoped_statement_text import binder_documentation

STANDARD = 'VRS-NONVACUITY-NO-HYPOTHESES-1'

def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()

def _split_arrow(value):
    stack=[]; pairs={'(':')','{':'}','[':']'}
    for i,c in enumerate(value):
        if c in pairs: stack.append(pairs[c])
        elif stack and c==stack[-1]: stack.pop()
        elif not stack and (c=='→' or value[i:i+2]=='->'):
            return value[:i].strip(),value[i+(1 if c=='→' else 2):].strip()
    return None

def domain_evidence(type_text, *, source='', custom_domains=None):
    """Closed constructive inventory. An unknown spelling always remains HOLD."""
    value=' '.join(type_text.split())
    # The displayed type spelling alone cannot prove it denotes Mathlib's type.
    # Reject local notation and shadowing rather than infer name resolution.
    if re.search(r'(?m)^\s*(?:local\s+|scoped\s+)?(?:notation|macro|syntax)\b',source):
        return None
    builtin_names={'Real','Nat','Int','Rat','Bool','Unit','PUnit','NNReal','ENNReal','Finset','Fin'}
    declared=re.findall(r'(?m)^\s*(?:noncomputable\s+)?(?:def|abbrev|structure|inductive|class)\s+([\w.]+)',source)
    if any(name.rsplit('.',1)[-1] in builtin_names for name in declared):
        return None
    zeros={'ℝ':'(0 : ℝ)','Real':'(0 : Real)','ℕ':'(0 : ℕ)',
           'Nat':'(0 : Nat)','ℤ':'(0 : ℤ)','Int':'(0 : Int)',
           'ℚ':'(0 : ℚ)','Rat':'(0 : Rat)','Bool':'false',
           'Unit':'()','PUnit':'PUnit.unit','NNReal':'(0 : NNReal)',
           'ENNReal':'(0 : ENNReal)'}
    if value in zeros:
        return {'type':value,'kind':'EXPLICIT_BUILTIN_TERM','term':zeros[value]}
    if re.fullmatch(r'Type(?:\s+[A-Za-z][\w]*)?|Type\*',value):
        return {'type':value,'kind':'EXPLICIT_UNIVERSE_TYPE','term':'Nat'}
    # Empty input domains are fine: a constant function still exists. Do not
    # treat a proposition-to-proposition implication as a data function.
    arrow=_split_arrow(value)
    if arrow:
        if arrow[1] in {'ℝ','Real'}:
            return {'type':value,'kind':'EXPLICIT_CONSTANT_FUNCTION',
                    'term':'fun _ => (0 : '+arrow[1]+')'}
        return None
    if re.fullmatch(r'Finset\s+(?:Nat|ℕ|Int|ℤ|Real|ℝ|Rat|ℚ|Bool)',value):
        return {'type':value,'kind':'EXPLICIT_EMPTY_FINSET','term':'(∅ : '+value+')'}
    fin=re.fullmatch(r'Fin\s+([1-9][0-9]*)',value)
    if fin:
        return {'type':value,'kind':'EXPLICIT_POSITIVE_FIN_TERM',
                'term':'(0 : '+value+')','cardinality':int(fin[1])}
    evidence=(custom_domains or {}).get(value)
    if not isinstance(evidence,dict) or set(evidence)!={'kind','source_sha256','term_declaration','term'}:
        return None
    if evidence['kind']!='CERTIFICATE_BOUND_CLOSED_EXPLICIT_TERM' or evidence['source_sha256']!=_sha(source):
        return None
    name=evidence['term']; decl=evidence['term_declaration']
    # A caller cannot declare a parameterized/assumption-bearing function to be
    # a closed term. Exact typed declaration and complete source bind the term.
    if not isinstance(name,str) or not re.fullmatch(r'[\w.]+',name): return None
    prefix=r'(?m)^\s*(?:noncomputable\s+)?def\s+'+re.escape(name)+r'\s*:\s*'+re.escape(value)+r'\s*:='
    matches=list(re.finditer(prefix,source))
    if len(matches)!=1 or not isinstance(decl,str) or decl not in source or not re.match(prefix,decl): return None
    # Global assumptions may make a typed "constant" conditional. Require a
    # separate elaborated certificate receipt for that case, never guess here.
    if re.search(r'(?m)^\s*(?:variable|variables|constant|constants|hypothesis|axiom)\b',source[:matches[0].start()]): return None
    return {'type':value,'kind':evidence['kind'],'term':name,
            'source_sha256':evidence['source_sha256'],'term_declaration':decl}

def assess_declaration(signature, ambient_source_context, *, source='', custom_domains=None):
    result={'standard':STANDARD,'status':'HOLD','reasons':[],
            'rule_discharge_only':True,'certifies':False,'local_lean_execution':False,
            'signature_sha256':_sha(signature),'candidate_sha256':_sha(source),
            'ambient_source_context':ambient_source_context,'domains':[]}
    try:
        docs=binder_documentation(signature)
        if docs.get('conclusion_utf8') is None: raise ValueError('unresolved full source declaration')
        groups=list(docs['binder_groups'])
        for row in ambient_source_context:
            if not isinstance(row,dict) or set(row)!={'line','source_text'}: raise ValueError('unresolved ambient context')
            text=re.sub(r'^\s*variables?\b','theorem ambient',row['source_text'],count=1)
            adocs=binder_documentation(text+' : True')
            if not adocs['binder_groups']: raise ValueError('unparsed ambient context')
            groups += adocs['binder_groups']
        for group in groups:
            if group.startswith('['): raise ValueError('typeclass/instance hypothesis needs Tier-1 evidence')
            inner=group[1:-1]
            if ':' not in inner: raise ValueError('untyped binder')
            names,typ=inner.split(':',1)
            if not names.strip() or any(x in names for x in '=,'): raise ValueError('binder assignment/unresolved names')
            evidence=domain_evidence(typ,source=source,custom_domains=custom_domains)
            if evidence is None: raise ValueError('premise or unproved nonempty domain: '+typ.strip())
            result['domains'].append({'binders':names.split(),**evidence})
        # A top-level implication is also a hypothesis, even when written after
        # the colon. Nested function type annotations are not implications.
        if _split_arrow(docs['conclusion_utf8']): raise ValueError('conclusion contains implication hypothesis')
        if re.match(r'\s*(?:∀|forall\b)',docs['conclusion_utf8']):
            raise ValueError('unparsed universal conclusion; explicit binder inventory required')
        types=list(dict.fromkeys(d['type'] for d in result['domains']))
        domain=', '.join(types) if types else 'Unit (closed proposition; no quantified parameters)'
        result.update(status='NO_HYPOTHESES',witness='NO_HYPOTHESES (domain nonempty: '+domain+')')
    except Exception as exc:
        result['reasons'].append(str(exc))
    return result

def assess_candidate(candidate_text, theorem_name, *, custom_domains=None):
    """Recompute full source signature and live variables with existing consumers."""
    from theorem_coverage import triviality
    from scoped_release import ambient_context
    try:
        declaration=triviality(candidate_text)[theorem_name]
        result=assess_declaration(declaration['signature'],
            ambient_context(candidate_text,declaration['line']),source=candidate_text,
            custom_domains=custom_domains)
        result.update(theorem=theorem_name,source_line=declaration['line'],
                      exact_source_signature=declaration['signature'])
        return result
    except Exception as exc:
        return {'standard':STANDARD,'status':'HOLD','theorem':theorem_name,
                'reasons':['unresolved source: '+str(exc)],'certifies':False,
                'local_lean_execution':False}
