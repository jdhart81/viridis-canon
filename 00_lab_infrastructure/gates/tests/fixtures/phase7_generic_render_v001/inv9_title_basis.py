"""Approved title-only INV-9 exception, confined to the first main abstract.

This does not remove a source dependency or qualify any product formula.
"""
import re

BASIS_SENTENCE = 'This note does not depend on the product-form Intelligence Bound conjecture; its results are independent of premises PL and PD.'
FORMULA = re.compile(r'\\[dt]?frac\s*\{\s*P\s*(?:(?:\\cdot|\\times|\\,|\\!|\\;|\\quad)\s*)*D\b|'
                     r'\bP\s*(?:\\cdot|\\times|\*)\s*D\s*(?:/|\\over)|'
                     r'\bP\s*D\s*(?:/|\\over)',re.I)
BOUND_PHRASE = re.compile(r'intelligence\s+bound',re.I)

def _balanced(text,start):
    if start>=len(text) or text[start]!='{':raise ValueError('unbalanced title field')
    depth=1;i=start+1
    while i<len(text) and depth:
        if text[i]=='{' and (i==0 or text[i-1]!='\\'):depth+=1
        elif text[i]=='}' and (i==0 or text[i-1]!='\\'):depth-=1
        i+=1
    if depth:raise ValueError('unbalanced title field')
    return i

def _approved_title_only_view(paper):
    """Return two exact-check views, or None. Never invent omitted assumptions.

    Product view removes only the exact approved basis sentence. Bound-phrase
    view additionally removes title and PDF-title fields. No body assertion or
    Lean formula can be excluded through this rule.
    """
    text=re.sub(r'(?<!\\)%[^\n]*','',paper)
    if text.count(BASIS_SENTENCE)!=1:return None
    matches=list(re.finditer(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',text,re.S))
    if not matches:return None
    main=matches[0]
    if BASIS_SENTENCE not in main[1]:return None
    prefix=text[:main.start()]
    if r'\begin{document}' not in prefix:return None
    # A sentence in an archived quote/footnote/listing or a later abstract is
    # not the main-abstract basis declaration.
    if re.search(r'\\begin\{(?:quote|quotation|Verbatim|verbatim|lstlisting)\}',prefix):return None
    paragraph=main[1].split(BASIS_SENTENCE,1)
    if paragraph[0].rstrip().endswith(('{','[')) or paragraph[1].lstrip().startswith(('}',']')):return None
    product_view=text.replace(BASIS_SENTENCE,'',1)
    if FORMULA.search(product_view):return None
    title_matches=list(re.finditer(r'\\title\s*\{',product_view))
    if len(title_matches)!=1:return None
    spans=[]
    start=title_matches[0].end()-1;end=_balanced(product_view,start)
    if not BOUND_PHRASE.search(product_view[start:end]):return None
    spans.append((title_matches[0].start(),end))
    # Only the PDF-title value is covered, never all hypersetup options.
    for match in re.finditer(r'\bpdftitle\s*=\s*\{',product_view):
        start=match.end()-1;end=_balanced(product_view,start)
        spans.append((match.start(),end))
    bound_view=product_view
    for start,end in sorted(spans,reverse=True):bound_view=bound_view[:start]+bound_view[end:]
    if BOUND_PHRASE.search(bound_view):return None
    return {'product_view':product_view,'bound_view':bound_view,
            'rule':'APPROVED_PHRASE_ONLY_HISTORICAL_TITLE_MAIN_ABSTRACT_BASIS',
            'basis_sentence':BASIS_SENTENCE,'product_formula_matches':0}

def approved_title_only_view(paper):
    try:
        return _approved_title_only_view(paper)
    except (TypeError,ValueError):
        return None
