"""Shared frozen-signature documentation only; never Lean elaboration or verification."""
import re

def binder_documentation(signature):
    """Document raw explicit binders; full frozen source remains authoritative.

    This does not elaborate Lean types or discharge any hypothesis.
    """
    m=re.match(r'(?:theorem|lemma)\s+[^\s]+',signature)
    if not m: return {'binder_groups':[], 'defined_parameter_names':[], 'conclusion_utf8':None}
    i=m.end();groups=[];names=[]
    pairs={'(' : ')','{' : '}','[' : ']'}
    while i<len(signature):
        while i<len(signature) and signature[i].isspace(): i+=1
        if i==len(signature) or signature[i]==':': break
        if signature[i] not in pairs: break
        begin=i;stack=[pairs[signature[i]]];i+=1
        while i<len(signature) and stack:
            c=signature[i]
            if c in pairs: stack.append(pairs[c])
            elif c==stack[-1]: stack.pop()
            i+=1
        raw=signature[begin:i];groups.append(raw)
        inner=raw[1:-1]
        if ':' in inner:
            names.extend(x for x in inner.split(':',1)[0].split() if re.fullmatch(r'[^,(){}\[\]]+',x))
    return {'binder_groups':groups,'defined_parameter_names':list(dict.fromkeys(names)),'conclusion_utf8':signature[i+1:].strip() if i<len(signature) and signature[i]==':' else None,'documentation_only_not_elaborated_constant_type':True}


def signature_parts(signature):
    """Preserve exact raw hypothesis/conclusion substrings using balanced binders."""
    documentation = binder_documentation(signature)
    if documentation.get('conclusion_utf8') is None:
        raise ValueError('source signature missing top-level conclusion')
    after = re.sub(r'^(?:theorem|lemma)\s+[^\s]+', '', signature, count=1).strip()
    stack = []
    pairs = {'(': ')', '{': '}', '[': ']'}
    for i, ch in enumerate(after):
        if ch in pairs:
            stack.append(pairs[ch])
        elif stack and ch == stack[-1]:
            stack.pop()
        elif ch == ':' and not stack:
            if after[i+1:].strip() != documentation['conclusion_utf8']:
                raise ValueError('signature documentation parser disagreement')
            return after[:i].strip(), documentation['conclusion_utf8']
    raise ValueError('source signature missing balanced top-level conclusion')


def inline_unicode_escape(text):
    """Injective printable escaping; literal backslashes cannot spoof codepoints."""
    return ''.join('\\\\' if c == '\\' else c if ord(c) < 128
                   else ('\\u'+format(ord(c), '04x') if ord(c) <= 65535
                         else '\\U'+format(ord(c), '08x')) for c in text)
