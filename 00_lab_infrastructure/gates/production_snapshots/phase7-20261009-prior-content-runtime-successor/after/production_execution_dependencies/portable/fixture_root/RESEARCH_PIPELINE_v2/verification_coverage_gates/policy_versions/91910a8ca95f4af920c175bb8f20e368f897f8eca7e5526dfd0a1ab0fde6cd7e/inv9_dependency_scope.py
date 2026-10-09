"""Approved Run-127 exact dependency-scope narrowing, never proof verification.

Only the already audited immutable Run-127 source family is supported. All proof
bytes remain bound. A recomputed full-body source inventory and complete paper
regions select a mathematically independent retained statement; no arbitrary
substring archival exclusion can remove a Lean dependency or hypothesis.
"""
from __future__ import annotations
import hashlib,re
from static_pregate import code_only
from scoped_release import ambient_context,_inline_present
from theorem_coverage import triviality
from scoped_statement_text import signature_parts
import premise_declaration as premise

STANDARD='VRS-INV9-EXACT-DEPENDENCY-SCOPE-1'
RUN='Run-127'
TARGET='positive_floor_sharp_two_point_counterexample'
EXCLUDED=('cantelli_capacity_certificate','precautionary_rate_le_violation_budget','capacity_reserve_fraction_eq','mean_only_plugin_arbitrarily_unsafe')
CANDIDATE_SHA='e930944c7b5efe69cecc90884243a8aca6a09a6930442196347b6d4227334d9a'
FORMAL_SHA='cb9a966f3d2130bb5a91a15baaa809dc976f35713623190116a235f4867a1b44'
CERTIFICATE_SHA='b9f10f5798a7adc9de6c1e8e93cc27190a0beff41284401620960181e2b088f3'
PRIOR_TEX_SHA='32d1c366a6005526303882a51e54f2f884532d5b4bffc3217426272c4c2b429e'
COMMAND=re.compile(r'(?m)^[ \t]*(?:(?:noncomputable|private|protected)\s+)*(def|abbrev|structure|lemma|theorem|instance|namespace|section|end|variable|variables|import|open|set_option|attribute)\b')
DECLARATIONS={'def','abbrev','structure','lemma','theorem','instance'}
sha=lambda text:hashlib.sha256(text.encode()).hexdigest()

def declaration_inventory(source,targets):
    code=code_only(source)
    if re.search(r'(?m)^\s*(?:local\s+|scoped\s+)?(?:notation|macro|syntax|axiom|opaque|constant|inductive|class)\b',code):
        raise ValueError('unsupported source command; dependency analysis unresolved')
    commands=list(COMMAND.finditer(code));nodes={};scopes=[]
    for i,match in enumerate(commands):
        end=commands[i+1].start()if i+1<len(commands)else len(code)
        tail=code[match.end():end].strip()
        if match[1] in {'namespace','section'}:
            scopes.append((match[1],tail.split()[0]if tail else''));continue
        if match[1]=='end':
            if scopes:scopes.pop()
            continue
        if match[1] not in DECLARATIONS:continue
        name_match=re.match(r'([A-Za-z_][\w\'.]*)',tail)
        if not name_match:raise ValueError('anonymous/unresolved declaration')
        name=name_match[1]
        if name in nodes:raise ValueError('ambiguous local declaration name')
        begin=match.start();text=source[begin:end]
        fq='.'.join([n for kind,n in scopes if kind=='namespace']+[name])
        line=code.count('\n',0,begin)+1
        nodes[name]={'name':name,'qualified_name':fq,'kind':match[1],'source_line':line,
            'byte_start':len(source[:begin].encode()),'byte_end_exclusive':len(source[:end].encode()),
            'source_sha256':sha(text),'source_text':text,'masked_code':code[begin:end],
            'ambient_source_context':ambient_context(source,line)}
    for name,node in nodes.items():
        node['references']=sorted(other for other in nodes if other!=name and re.search(r'(?<![\w])'+re.escape(other)+r'(?![\w])',node['masked_code']))
    seen=set();queue=list(targets)
    while queue:
        name=queue.pop()
        if name not in nodes:raise ValueError('unresolved retained target or local dependency')
        if name in seen:continue
        seen.add(name);queue.extend(nodes[name]['references'])
    return [nodes[name]for name in sorted(seen)]

def validate_inventory(source,targets,recorded):
    actual=declaration_inventory(source,targets)
    if actual!=recorded:raise ValueError('missing, added, changed or reordered source dependency/span/context')
    texts='\n'.join(node['masked_code']+'\n'+'\n'.join(c['source_text']for c in node['ambient_source_context'])for node in actual)
    if premise.PRODUCT_CODE.search(texts)or premise.BOUND_CODE.search(texts):
        raise ValueError('retained definition/proof/context encodes product or bound dependency')
    return actual

def paper_regions(paper,prior_tex):
    if sha(prior_tex)!=PRIOR_TEX_SHA:raise ValueError('not the approved prior manuscript')
    retained=r'\section*{Certified-scope statement S127-04}'
    conjectural=r'\section*{Conjectural context}'
    archive=r'\section*{Conjectures / uncertified remarks}'
    if paper.count(retained)!=1 or paper.count(conjectural)!=1 or paper.count(archive)!=1:raise ValueError('closed paper-region structure missing or duplicated')
    i=paper.index(retained);j=paper.index(conjectural);k=paper.index(archive)
    if not 0<i<j<k:raise ValueError('paper-region order differs')
    if paper[k:]!=prior_tex[prior_tex.index(archive):]:raise ValueError('original historical claims or final status text changed')
    main=paper[:j]
    heads=re.findall(r'\\section\*\{Certified-scope statement ([^}]+)\}',paper)
    if heads!=['S127-04']:raise ValueError('excluded certified headline leaked into successor')
    # Excluded names may occur only in the closed conjectural or archival zones.
    for name in EXCLUDED:
        latex=name.replace('_',r'\_\allowbreak{}')
        if name in main or latex in main:raise ValueError('excluded certified target appears in main scientific scope')
    section=paper[j:k]
    if section.count('UNCERTIFIED as a scientific interpretation and excluded from the retained scope.')!=4:raise ValueError('every excluded statement needs its own UNCERTIFIED qualification')
    if '10.5281/zenodo.23141592'not in section or 'Run-902'not in section or 'conditional on premises PL and PD'not in section:raise ValueError('conjectural context lacks exact foundation/conditional references')
    for index in ('01','02','03','05'):
        if section.count(r'\section*{Excluded defined-model statement S127-'+index+'}')!=1:raise ValueError('closed excluded statement inventory differs')
    boundaries=[0,i,j,k,len(paper)];labels=['STATUS_AND_READING_INSTRUCTIONS','EXACT_RETAINED_STATEMENT_AND_WITNESS','CONJECTURAL_EXCLUDED_PRODUCT_MODEL','UNCHANGED_UNCERTIFIED_HISTORICAL_CLAIMS_AND_STATUS']
    return [{'region':labels[n],'byte_start':len(paper[:boundaries[n]].encode()),'byte_end_exclusive':len(paper[:boundaries[n+1]].encode()),'sha256':sha(paper[boundaries[n]:boundaries[n+1]])}for n in range(4)]

def make_receipt(candidate,formal,paper,prior_tex,statement_scope):
    if sha(candidate)!=CANDIDATE_SHA or sha(formal)!=FORMAL_SHA:raise ValueError('closed approved source family mismatch')
    if [s['lean_theorem']for s in statement_scope]!=[TARGET]:raise ValueError('only approved nonproduct target subset allowed')
    cd=triviality(candidate)[TARGET];fd=triviality(formal)[TARGET]
    scope=statement_scope[0]
    if scope['exact_source_signature']!=cd['signature']or fd['signature']!=cd['signature']:raise ValueError('retained exact statement changed')
    binders,conclusion=signature_parts(cd['signature'])
    if scope['explicit_binders_and_hypotheses']!=binders or scope['conclusion']!=conclusion:
        raise ValueError('retained binder or conclusion map differs from exact source')
    if scope['ambient_source_context']!=ambient_context(candidate,cd['line']):raise ValueError('ambient hypothesis omitted or changed')
    if not _inline_present(cd['signature'],paper):raise ValueError('full frozen statement not printed')
    for ctx in scope['ambient_source_context']:
        if not _inline_present(ctx['source_text'],paper):raise ValueError('full ambient hypothesis not printed')
    return {'standard':STANDARD,'run_id':RUN,'foundation_basis':'INDEPENDENT',
        'certificate_sha256':CERTIFICATE_SHA,'candidate_sha256':sha(candidate),'formal_statement_sha256':sha(formal),
        'prior_tex_sha256':sha(prior_tex),'final_tex_sha256':sha(paper),
        'retained_theorem_names':[TARGET],'excluded_theorem_names':list(EXCLUDED),
        'candidate_dependency_inventory':declaration_inventory(candidate,[TARGET]),
        'formal_dependency_inventory':declaration_inventory(formal,[TARGET]),
        'whole_paper_regions':paper_regions(paper,prior_tex),
        'retained_signature_sha256':sha(cd['signature']),
        'retained_ambient_context':scope['ambient_source_context'],
        'classification_only_not_certification':True}

def evaluate(receipt,*,candidate,formal,paper,prior_tex,statement_scope,certificate_sha256):
    result={'standard':STANDARD,'status':'HOLD','reasons':[],'certifies':False,'local_lean_execution':False,'full_candidate_remains_hash_bound':True}
    try:
        if certificate_sha256!=CERTIFICATE_SHA:raise ValueError('wrong certificate family')
        expected=make_receipt(candidate,formal,paper,prior_tex,statement_scope)
        if receipt!=expected:raise ValueError('closed exact receipt differs from recomputed inventory/regions/type')
        ci=validate_inventory(candidate,[TARGET],receipt['candidate_dependency_inventory'])
        fi=validate_inventory(formal,[TARGET],receipt['formal_dependency_inventory'])
        main=paper[:paper.index(r'\section*{Conjectural context}')]+r'\end{document}'
        # Select only exact fully inventoried dependencies for classification.
        # The unchanged existing certificate continues to bind the full source.
        selected='\n'.join(n['source_text']for n in ci)
        frozen='\n'.join(n['source_text']for n in fi)
        status=premise.evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT'},candidate=selected,formal_statement=frozen,paper_text=main,theorem_names=[TARGET],required=True)
        result['existing_premise_consumer_on_exact_dependency_scope']=status
        if status['status']!='PASS':raise ValueError('retained exact source scope failed INV9: '+','.join(status['reasons']))
        result.update(status='PASS',foundation_basis='INDEPENDENT',retained_theorem_names=[TARGET],dependency_count=len(ci),whole_paper_regions=receipt['whole_paper_regions'])
    except Exception as exc:result['reasons'].append(str(exc))
    return result
