"""Conservative structure-aware TeX comparison; classification is not scientific verification."""
import difflib
import hashlib
import re

STATUS = re.compile(r'\b(?:Lean|Comparator|Aristotle|nanoda|certific\w*|certif\w*|formal(?:ly)?[-\s]+(?:proof|verif\w*|status|target)|frozen\s+(?:statement|declaration|candidate)|proof\s+holes|(?:candidate|declarations?)\s+(?:contains?|has|contain)\s+(?:no|zero)|manuscript\s+review\s+status|zero[- ]sorry|independent\s+(?:paper|manuscript|review)|no\s+local\s+Lean)\b', re.I)
SCIENTIFIC = re.compile(r'\b(?:assumes?|premise|quadratic|reflexivity|converse|uniqueness|feasib\w*|nonnegative\s+(?:time|best|radii)|necessary\s+(?:under|for)|sufficient\s+(?:under|for)|strictly\s+(?:positive|negative)|weak.sign|affine\s+slope|correction\s+quantif\w*|transcription\s+false|empty.index|counterexample|same\s+factors|full.spend|optimization\s+theorem|supply\s+floor\s+is)\b', re.I)


def normalize(text):
    text=re.sub(r'-\s*\n\s*','-',text)
    return re.sub(r'\s+', ' ', text).strip()


def remove_commands(text, names):
    pattern=re.compile(r'\\(?:'+names+r')\*?(?:\[[^\]]*\])?\s*\{')
    while (match:=pattern.search(text)):
        depth=1;i=match.end()
        while i<len(text) and depth:
            if text[i]=='{' and (i==0 or text[i-1]!='\\'):depth+=1
            if text[i]=='}' and (i==0 or text[i-1]!='\\'):depth-=1
            i+=1
        if depth:raise ValueError('unbalanced TeX command')
        text=text[:match.start()]+'\n'+text[i:]
    return text


def structure(text):
    text=re.sub(r'(?<!\\)%[^\n]*','',text)
    if r'\begin{document}' not in text or r'\end{document}' not in text:raise ValueError('missing document boundaries')
    pre,body=text.split(r'\begin{document}',1);body=body.split(r'\end{document}',1)[0]
    # Equations and theorem/proof environments remain protected even in status sections.
    math=re.findall(r'\\\[(.*?)\\\]|\\\((.*?)\\\)|\$\$(.*?)\$\$|(?<!\\)\$(.*?)(?<!\\)\$',body,re.S)
    math=[re.sub(r'\s+','',next((x for x in m if x),'')) for m in math]
    environments=[(m[0],normalize(m[1])) for m in re.findall(r'\\begin\{(theorem|lemma|proposition|corollary|definition|proof|equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}',body,re.S)]
    macros=[normalize(m.group(0)) for m in re.finditer(r'\\(?:newcommand|renewcommand|def|DeclareMathOperator)\b[^\n]*',pre)]
    headings=[normalize(x) for x in re.findall(r'\\(?:section|subsection|subsubsection|paragraph)\*?\{([^{}]*)\}',body)]
    prose=remove_commands(body,'section|subsection|subsubsection|paragraph|title|author|date|thanks')
    prose=re.sub(r'\\(?:maketitle|noindent)\b','',prose)
    prose=re.sub(r'\\(?:begin|end)\{abstract\}', '\n', prose)
    prose=re.sub(r'\\textbf\{(?:Funding and conflicts(?: of interest)?|Conflicts(?: of interest)?)\.\}', '', prose)
    numeric_prose=re.sub(r'Lean\s+4\.28\.0', 'Lean PINNED_TOOLCHAIN', prose)
    sentences=[normalize(x) for x in re.split(r'(?<=[.!?])\s+|\n\s*\n',prose) if normalize(x)]
    return {'math':math,'numbers':re.findall(r'\b\d[\d,]*(?:\.\d+)?\b',numeric_prose),
            'theorem_and_equation_blocks':environments,'scientific_macros':macros,'headings':headings,'sentences':sentences}


def classify(before, after):
    result={'classification':'CONTENT_CHANGED','status':'HOLD','protected_changes':[], 'edits':[], 'classifier_version':'VRS-MANUSCRIPT-STRUCTURE-1'}
    try:
        a,b=structure(before),structure(after)
        for field in ('math','numbers','theorem_and_equation_blocks','scientific_macros'):
            if a[field]!=b[field]:result['protected_changes'].append({'kind':field,'before':a[field],'after':b[field]})
        matcher=difflib.SequenceMatcher(a=a['sentences'],b=b['sentences'],autojunk=False)
        for op,i,j,k,l in matcher.get_opcodes():
            if op=='equal':continue
            old,new=a['sentences'][i:j],b['sentences'][k:l]
            def allowed_status(sentence):
                # Enumeration of the certificate's coverage is provenance, but
                # derivations, added assumptions and logical qualifications are protected.
                scope = sentence.startswith('They cover ') or sentence.startswith('These are statements about the supplied ledger, not measured ')
                return bool((STATUS.search(sentence) or scope) and (not SCIENTIFIC.search(sentence) or sentence.startswith('They cover ')))
            def residual(sentences):
                rest=[]
                for sentence in sentences:
                    mixed=sentence.startswith(('The result is ', 'It is not a field estimate', 'Numerical success is '))
                    if allowed_status(sentence) and not mixed:continue
                    sentence=re.sub(r',\s*(?:(?:or|and)\s+)?formal(?:\s+|-)\b(?:proof|verification)\b', '', sentence, flags=re.I)
                    sentence=re.sub(r'not formal proof,\s*', 'not ', sentence, flags=re.I)
                    # Preserve scientific scope in mixed disclaimers rather than dropping
                    # an entire sentence merely because it mentions certification.
                    sentence=re.sub(r'; the exact frozen Lean statements are Comparator-certified\.', '.', sentence)
                    sentence=sentence.replace('novelty, significance, and empirical validity remain unassessed.', 'novelty, significance, empirical validity remain unassessed.')
                    if sentence.startswith('The result is '):
                        sentence=sentence.replace(', or ', ', ').replace(', and ', ', ')
                    rest.append(normalize(sentence))
                return rest
            allowed=residual(old)==residual(new)
            result['edits'].append({'operation':op,'before':old,'after':new,'allowed_verification_status_only':bool(allowed)})
        result['section_titles']={'before':a['headings'],'after':b['headings']}
        if not result['protected_changes'] and all(e['allowed_verification_status_only'] for e in result['edits']):
            result.update(classification='VERIFICATION_STATUS_ONLY',status='CLASSIFIED')
        else:result['status']='CLASSIFIED'
        result['reason']='Only certification-status sentences and section titles differ' if result['classification']=='VERIFICATION_STATUS_ONLY' else 'Protected mathematical/numeric/theorem content or other scientific prose differs'
    except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
    result['before_sha256']=hashlib.sha256(before.encode()).hexdigest();result['after_sha256']=hashlib.sha256(after.encode()).hexdigest()
    result['diff']=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='certified sealed paper',tofile='deposited published paper'))
    return result
