"""Syntactic coverage labels only; no Lean execution, elaboration or proof issuance."""
import re
from pathlib import Path
from static_pregate import code_only

COMMAND=re.compile(r'(?m)^\s*(?:@\[[^\n]*\]\s*)?(?:(?:private|protected|noncomputable)\s+)*(theorem|lemma|def|abbrev|structure|instance|example|namespace|section|end|variable)\b')

def declarations(text):
    code=code_only(text);starts=list(COMMAND.finditer(code));result={};scopes=[]
    for i,m in enumerate(starts):
        tail=code[m.end():code.find('\n',m.end()) if code.find('\n',m.end())>=0 else len(code)].strip()
        if m[1] in ('namespace','section'):
            scopes.append((m[1],tail.split()[0] if tail else ''));continue
        if m[1]=='end':
            if scopes:scopes.pop()
            continue
        if m[1] not in ('theorem','lemma'):continue
        end=starts[i+1].start() if i+1<len(starts) else len(code)
        chunk=code[m.start():end].strip();n=re.match(r'(?:@\[[^\n]*\]\s*)?(?:(?:private|protected)\s+)*(?:theorem|lemma)\s+([\w\'.]+)',chunk)
        if n is None:raise ValueError('unparsed theorem declaration')
        # Frozen witnesses often use let-bindings in conclusions. Their final
        # := by boundary is distinct from those := terms. No parser result is
        # an elaboration/equivalence verdict.
        split=re.search(r':=\s*(?:by\b|rfl\b|(?:Eq|Iff|HEq)\.refl\b|le_rfl\b)',chunk)
        if split is None:split=re.search(r':=',chunk)
        if split is None:raise ValueError('missing proof boundary for '+n[1])
        qualified='.'.join([scope for kind,scope in scopes if kind=='namespace']+[n[1]])
        if qualified in result:raise ValueError('duplicate qualified theorem '+qualified)
        result[qualified]={'name':n[1],'signature':chunk[:split.start()].strip(),'proof':chunk[split.start()+2:].strip(),'line':code.count('\n',0,m.start())+1}
    # Unqualified names resolve only when there is exactly one declaration.
    short={}
    for qualified,d in list(result.items()):short.setdefault(d['name'],[]).append(d)
    for name,values in short.items():
        if len(values)==1:result[name]=values[0]
    return result

def triviality(text):
    ds=declarations(text);masked=code_only(text)
    defs=set(re.findall(r'(?m)^\s*(?:noncomputable\s+)?(?:def|abbrev)\s+([\w\'.]+)',masked));results={}
    reflexive=r'(?:rfl|reflexivity|(?:Eq|Iff|HEq)\.refl(?:\s+[^;\n]+)?|(?:exact\s+)?(?:rfl|le_rfl|le_refl(?:\s+\w+)?))'
    for name,d in ds.items():
        p=d['proof'];q=re.sub(r'^by\b','',p).strip();q=re.sub(r'\s+',' ',q)
        label='NO_SYNTACTIC_TRIVIAL_PATTERN';reason='No recognized reflexivity/definition-only proof; certificate validity remains independently assessed.'
        if re.fullmatch(reflexive,q):label='CERTIFIED_TRIVIAL';reason='Proof is reflexivity alone.'
        else:
            unfolding=re.fullmatch(r'(?:simp only|dsimp(?: only)?|unfold)\s*(?:\[([^\]]*)\]|([\w.\s]+?))(?:\s*;?\s*(?:rfl|reflexivity))?',q)
            if unfolding:
                names=[n.strip() for n in re.split(r'[,\s]+',unfolding[1] or unfolding[2]) if n.strip()]
                if names and all(n in defs for n in names):label='CERTIFIED_TRIVIAL';reason='Only locally defined symbols unfold; no theorem lemma used.'
            elif re.fullmatch(r'(?:simp|dsimp)(?:\s*\[[^\]]*\])?',q):
                label='TRIVIALITY_UNRESOLVED';reason='Unrestricted simplifier may unfold definitions or invoke lemmas; independent review required.'
        results[name]={**d,'classification':label,'reason':reason,'mode':'REPORT_ONLY','certifies':False}
    # Simple local aliases must not launder an already recognized trivial proof.
    for _ in range(len(results)):
        changed=False
        for name,d in results.items():
            if d['classification']=='CERTIFIED_TRIVIAL':continue
            q=re.sub(r'^by\s+exact\s+|^exact\s+','',d['proof']).strip();head=re.match(r'^([\w\'.]+)(?:\s+[\w\s()]+)?$',q)
            if head and head[1] in results and results[head[1]]['classification']=='CERTIFIED_TRIVIAL':
                d.update(classification='CERTIFIED_TRIVIAL',reason='Alias of local reflexivity/definition-only theorem '+head[1]);changed=True
        if not changed:break
    return results
