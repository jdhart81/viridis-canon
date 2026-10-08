#!/usr/bin/env python3
"""Stage reviewed-scope proposals, never issue proof/publication acceptance.

All original bytes and sealed Comparator inputs are preserved. Current ordinary
consumers are invoked unchanged. No Lean execution or network writes occur.
"""
from __future__ import annotations
import datetime, difflib, hashlib, json, re, shutil, sys, unicodedata
from pathlib import Path
sys.dont_write_bytecode = True

STANDARD = 'VRS-PHASE7-SCOPED-RELEASE-PROPOSAL-1'
STAGING = 'HOLD_PENDING_INDEPENDENT_SCOPE_REVIEW_AND_PUBLICATION_BINDING'
PLAIN_DISCLAIMER = 'logical validity given the model, not empirical validation of its assumptions'
BANNER = "UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. Lean sources may compile but have not been independently certified. Results are conditional on the stated model assumptions."
UNICODE_RENDER = {'ℝ':'Real','ℕ':'Nat','ℤ':'Int','ℚ':'Rat','ℂ':'Complex','≤':'<=','≥':'>=','↔':'<->','→':'->','←':'<-','∧':'/\\','∨':'\\/','¬':'not ','∀':'forall ','∃':'exists ','ε':'epsilon','λ':'lambda','τ':'tau','η':'eta','ρ':'rho','μ':'mu','Ω':'Omega','σ':'sigma','δ':'delta','θ':'theta','α':'alpha','β':'beta','γ':'gamma','κ':'kappa','π':'pi','⊤':'top','⊥':'bottom','≠':'!=','∈':'in','∉':'notin','∑':'sum','⊆':'subset','×':' x ','₂':'_2','₁':'_1','₀':'_0','₃':'_3','₄':'_4','₅':'_5','₆':'_6','₇':'_7','₈':'_8','₉':'_9','ᵢ':'_i','⟨':'<','⟩':'>','·':'.','∘':' o ','⁻':'^-','ᶠ':'^f','∞':'infinity','₊':'_+','ᵒ':'^o','ι':'iota','φ':'phi','ψ':'psi'}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bsha(b): return hashlib.sha256(b).hexdigest()
def write_json(p, v): Path(p).write_text(json.dumps(v, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
def binding(p):
    p=Path(p); return {'path':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size}

def _staging_output(root, value):
    """Closed staging destinations; never origin, sealed, source or finalized."""
    root=Path(root).resolve(strict=True);raw=Path(value)
    if raw.is_symlink() or any(p.is_symlink() for p in raw.parents):
        raise ValueError('symlink staging output refused')
    out=raw.resolve()
    queue=root/'RESEARCH_PIPELINE_v2/science_release_queue/staged'
    allowed=out.is_relative_to(queue) and out!=queue
    reports=root/'reports/verification-coverage'
    if out.is_relative_to(reports):
        rel=out.relative_to(reports).parts
        allowed=allowed or (len(rel)>=3
            and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',rel[0]) is not None
            and re.fullmatch(r'phase[-_]?7(?:[-_][A-Za-z0-9_.-]+)?',rel[1],re.I) is not None)
    # Offline staging is permitted in TMP, but cannot use the canonical tree
    # as an accidental TMP exception in portable tests or local snapshots.
    allowed=allowed or (out.is_relative_to(Path('/private/tmp')) and not out.is_relative_to(root))
    if not allowed:
        raise ValueError('output must be a new scoped staging attempt, never a proof/source directory')
    return out


def _assert_snapshot(files):
    for path,digest in files.items():
        if Path(path).is_symlink() or sha(path)!=digest:
            raise ValueError('staging input changed: '+str(path))
def ascii_render(text):
    return ''.join(UNICODE_RENDER.get(c,c if ord(c)<128 else '[U+%04X]'%ord(c)) for c in text)
def latex(text):
    return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','$':r'\$','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}.get(c,c) for c in ascii_render(text))
def source_partition(data):
    ends=[m.end() for m in re.finditer(br'\n[ \t]*\n+',data)]
    if not ends or ends[-1]!=len(data): ends.append(len(data))
    start=0;result=[]
    for i,end in enumerate(ends,1):
        if end<=start: continue
        frag=data[start:end]
        result.append({'id':f'HISTORICAL-PARAGRAPH-{i:04d}','byte_start':start,'byte_end_exclusive':end,'sha256':bsha(frag),'line_start':data[:start].count(b'\n')+1,'line_end':data[:end].count(b'\n')+1,'evidence_class':'UNCERTIFIED_HISTORICAL_REMAINDER','verification_status':'NOT_FORMALLY_VERIFIED','scope':'Every sentence, theorem statement, equation, numerical value and assumption in this byte span is archival and explicitly unverified in this release.'})
        start=end
    assert start==len(data) and b''.join(data[x['byte_start']:x['byte_end_exclusive']] for x in result)==data
    return result

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

def stage_run(inventory_row, output_dir, canonical_root, gates_path, ledger, paper_override=None):
    """Reusable root-only staging helper. Inputs use inventory agent INVENTORY.rows schema.

    Only output_dir is written. Never mutate inventory/sealed artifacts, issue a
    review receipt, change a certificate, or claim current publication PASS.
    """
    root=Path(canonical_root).resolve(strict=True); gates=Path(gates_path).resolve(strict=True);out=_staging_output(root,output_dir)
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(gates))
    import certificate_inspection, static_pregate, theorem_coverage, claim_binding, manuscript_structure, publication_binding, premise_declaration
    row=inventory_row;rid=row['run_id']; insp_record=row['independent_current_certificate']; cert=Path(insp_record['path'])
    source_hashes={cert:sha(cert)}
    if source_hashes[cert]!=insp_record.get('sha256'):raise ValueError('certificate inventory binding changed')
    inspection=certificate_inspection.inspect_certificate(cert,root)
    if (inspection.get('valid') is not True or inspection.get('run_id')!=rid
            or inspection.get('sha256')!=source_hashes[cert]):raise ValueError('current certificate invalid or changed: '+str(inspection.get('reasons')))
    for entry in inspection.get('bindings',[]):
        p=certificate_inspection.resolve_binding({'path':entry['resolved_path'],'sha256':entry['sha256']},root)
        source_hashes[p]=entry['sha256']
    module_inputs={Path(m.__file__).resolve():sha(m.__file__) for m in (certificate_inspection,static_pregate,theorem_coverage,claim_binding,manuscript_structure,publication_binding,premise_declaration)}
    candidate=Path(inspection['candidate_path']);candidate_text=candidate.read_text()
    cert_doc=json.loads(cert.read_text()); sealed=inspection['sealed_paper_inputs']; sealed_tex=certificate_inspection.resolve_binding(sealed['SEALED_paper.tex'],root)
    frozen=certificate_inspection.resolve_binding(cert_doc['bindings']['formal_statement'],root)
    static=static_pregate.scan(candidate); trivial=theorem_coverage.triviality(candidate_text);decls=theorem_coverage.declarations(candidate_text)
    if static.get('static_pass') is not True: raise ValueError('candidate static HOLD')
    aligner=premise_declaration._aligner()
    frozen_text=frozen.read_text(); globals_=premise_declaration._global_assumptions(aligner.strip_comments(frozen_text))
    pubs=row.get('publications',[])
    pub=pubs[0] if pubs else None
    published_tex=((pub or {}).get('published_local_manuscript') or {}).get('tex') or {}
    finalized_tex=(row.get('manuscripts') or {}).get('finalized_tex') or {}
    if paper_override: current=Path(paper_override)
    elif published_tex.get('path') and Path(published_tex['path']).is_file(): current=Path(published_tex['path'])
    elif finalized_tex.get('path') and Path(finalized_tex['path']).is_file(): current=Path(finalized_tex['path'])
    else: current=sealed_tex
    for p in (candidate,frozen,sealed_tex,current):
        digest=sha(p)
        if p in source_hashes and source_hashes[p]!=digest:raise ValueError('source changed after inspection')
        source_hashes[p]=digest
    source_claim_path=certificate_inspection.resolve_binding(sealed['SEALED_CLAIM_INVENTORY.json'],root)
    source_hashes[source_claim_path]=sha(source_claim_path)
    original=current.read_bytes();text=original.decode('utf-8'); sealed_bytes=sealed_tex.read_bytes()
    if text.count('\\begin{document}')!=1 or text.count('\\end{document}')!=1: raise ValueError('one document region required')
    before,after=text.split('\\begin{document}',1); body=after.rsplit('\\end{document}',1)[0]
    # The title/preamble remain exact. Move the original document body, unchanged,
    # into an explicit archival region; remove only the original maketitle token,
    # which is reproduced once before the scoped successor body.
    had_title='\\maketitle' in body
    archived_body=body.replace('\\maketitle','',1) if had_title else body
    title=((pub or {}).get('receipt_confirmed_uncertified_banner') or {}).get('title') or ((pub or {}).get('historical_public_get') or {}).get('title') or row.get('run_manifest',{}).get('value',{}).get('title') or rid
    hist=out/'historical';hist.mkdir(exist_ok=True)
    (hist/'PUBLISHED_ORIGINAL_paper.tex').write_bytes(original)
    (hist/'SEALED_ORIGINAL_paper.tex').write_bytes(sealed_bytes)
    # Frozen statement/candidate remain raw exact UTF-8 bytes; rendered ASCII
    # listings are explicitly presentation-only and never proof inputs.
    (out/'VERIFICATION_CANDIDATE.lean').write_bytes(candidate.read_bytes())
    (out/'VERIFICATION_STATEMENT.lean').write_bytes(frozen.read_bytes())
    (out/'LEAN_ZERO_SORRY_CERTIFICATE.json').write_bytes(cert.read_bytes())
    render_dir=out/'rendered';render_dir.mkdir(exist_ok=True)
    (render_dir/'FROZEN_CONTEXT.txt').write_text(ascii_render(frozen_text))
    (render_dir/'ARCHIVED_SOURCE.txt').write_text(ascii_render(text))
    targets=inspection['certified_theorems']; witnesses=inspection['nonvacuity']
    qualified={n:next((k for k,v in decls.items() if v['name']==n and '.' in k),n) for n in targets}
    full_scope=[];eligible=[];excluded=[]
    for ix,name in enumerate(targets,1):
        if name not in decls: raise ValueError('declaration not found: '+name)
        signature=decls[name]['signature']
        if aligner.normalized_signature(candidate_text,name)!=aligner.normalized_signature(frozen_text,name): raise ValueError('statement drift: '+name)
        start=aligner._declaration_start(aligner.strip_comments(frozen_text),name)
        classification=trivial.get(name,{}).get('classification','TRIVIALITY_UNRESOLVED')
        contradiction=bool(re.search(r':\s*False\s*$',signature))
        reason=('CERTIFIED_CONTRADICTION_LEMMA_NOT_A_SATISFIABLE_AFFIRMATIVE_CLAIM' if contradiction else classification)
        eligible_status=classification=='NO_SYNTACTIC_TRIVIAL_PATTERN' and not contradiction
        english='Under every hypothesis in the frozen statement, '+qualified[name]+' establishes exactly its quoted conclusion. No empirical identification or additional physical law is asserted.'
        entry={'id':f'{rid}-S{ix:02d}','lean_theorem':name,'qualified_name':qualified[name],'frozen_signature_utf8':signature,'frozen_signature_sha256':bsha(signature.encode()),'raw_binder_documentation':binder_documentation(signature),'statement_context_sha256':sha(frozen),'full_context_artifact':'VERIFICATION_STATEMENT.lean','context_prefix_before_declaration_utf8':aligner.strip_comments(frozen_text)[:start], 'ambient_global_assumptions_utf8':globals_,'signature_normalization':'unchanged pinned align_challenge parser, comment removal and whitespace collapse only','signature_identity_with_frozen_statement':True,'statement_type_kind':'SOURCE_DECLARATION_WITH_FULL_FROZEN_LEAN_CONTEXT_NOT_AN_INDEPENDENT_ELABORATED_TYPE_DUMP','english_claim':english,'is_nonvacuity_obligation':name in witnesses,'triviality':classification,'scope_disposition':'PROPOSED_FORMALLY_VERIFIED_SCOPE' if eligible_status else 'EXCLUDED_FROM_FORMALLY_VERIFIED_SCOPE','exclusion_reason':None if eligible_status else reason,'model_fidelity':{'defined':list(dict.fromkeys(binder_documentation(signature)['defined_parameter_names']+re.findall(r'(?m)^\s*(?:noncomputable\s+)?(?:def|abbrev)\s+(\w+)',candidate_text))) or ['Mathlib mathematical values in the frozen statement'],'empirically_identified':[]},'printed_disclaimer':PLAIN_DISCLAIMER,'review_status':'PENDING_INDEPENDENT_CLAUDE_SCOPE_REVIEW'}
        full_scope.append(entry)
        (eligible if eligible_status else excluded).append(entry)
        (render_dir/(entry['id']+'.txt')).write_text(ascii_render(signature))
    certified_witnesses=[w for w in witnesses if w in decls and trivial.get(w,{}).get('classification')=='NO_SYNTACTIC_TRIVIAL_PATTERN' and aligner.normalized_signature(candidate_text,w)==aligner.normalized_signature(frozen_text,w)]
    if not certified_witnesses: raise ValueError('no eligible certificate-listed nonvacuity obligation')
    source_claims=json.loads(source_claim_path.read_text())
    imported_claims=[]
    for i,c in enumerate(source_claims.get('claims',[]),1):
        imported_claims.append({'original_claim_index':i,'original_claim':c,'classification':'UNCERTIFIED_HISTORICAL_REMAINDER','original_english_is_not_inherited_as_certified':True,'reason':'Only the exact successor frozen-statement scope is proposed; every original English claim and empirical/numeric/novelty assertion remains explicitly unverified.'})
    nonvacuity={'status':'EXISTING_CERTIFICATE_NONVACUITY_CONTRACT_PRESENT','claims_certifies':False,'certificate_listed_obligations':witnesses,'eligible_witnesses':certified_witnesses,'witness_statement_records':[{'name':w,'qualified_name':next((k for k,v in decls.items() if v['name']==w and '.' in k),w),'frozen_signature_utf8':decls[w]['signature'],'statement_context_sha256':sha(frozen),'full_context_artifact':'VERIFICATION_STATEMENT.lean','receipt_contract_member':True,'primary_scientific_claim':False} for w in certified_witnesses],'limitation':'This is receipt consumption, not a new satisfiability verifier. Each proposed claim binds one existing certificate-listed witness; the independent review must check that witness actually instantiates the claim hypotheses. Contradictory impossibility statements are not affirmative certified claims.'}
    core_eligible=[x for x in eligible if not x['is_nonvacuity_obligation']]
    proposed_claims=[]
    for x in eligible:
        proposed_claims.append({'id':x['id'],'english_claim':x['english_claim'],'lean_theorem':x['lean_theorem'],'evidence_class':'FORMALLY_VERIFIED','nonvacuity_obligation':None,'witness_binding_status':'UNREVIEWED_NO_PER_THEOREM_COMPATIBILITY_INFERRED','candidate_witnesses':certified_witnesses,'model_fidelity':x['model_fidelity'],'disclaimer':claim_binding.DISCLAIMER,'scope_signature_sha256':x['frozen_signature_sha256'],'review_status':'PENDING_INDEPENDENT_CLAUDE_SCOPE_REVIEW'})
    proposed_binding={'standard':STANDARD,'status':'PROPOSAL_ONLY_NOT_A_PUBLICATION_BINDING_RECEIPT','claims':proposed_claims,'uncertified_remainder':{'all_historical_source_bytes':True,'all_original_inventory_claims':True},'certificate_sha256':sha(cert),'publication_authorized':False}
    write_json(out/'claim_binding.json',proposed_binding)
    # Main scientific prose contains only the exact quoted frozen statements.
    parts=[r'\section*{Frozen mathematical scope}',r'\begin{abstract}',latex(rid)+' belongs to the weekly Viridis Methods Digest. The mathematical scope below consists only of the exact frozen Lean statements and their named hypotheses. Foundation basis: INDEPENDENT, subject to independent statement-and-scope review. The unchanged Comparator certificate covers its frozen Lean candidate, not this successor manuscript. All historical prose, equations, numbers and claims reproduced later are UNCERTIFIED. '+latex(PLAIN_DISCLAIMER)+'.',r'\end{abstract}',r'\noindent Publication scope is limited to the listed frozen mathematical statements; the accompanying claim map and \texttt{PUBLICATION\_BINDING.json} control publication clearance.',r'\section*{Main results}',r'\noindent Foundation basis proposed for these mathematical claims: \textbf{INDEPENDENT}. No empirical parameter calibration or physical identification is admitted. Every binder, hypothesis, definition, namespace, import and typeclass context is preserved in the frozen statement attachment and its full listing below. '+latex(PLAIN_DISCLAIMER)+'.']
    for x in eligible:
        parts += [r'\subsection*{'+latex(x['id'])+': '+latex(x['lean_theorem'])+'}',latex(x['english_claim']),r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/'+x['id']+'.txt}',r'\noindent Certificate-listed witness candidate (compatibility unreviewed): \texttt{'+latex(certified_witnesses[0])+r'}. Model symbols are defined inputs; empirically identified symbols: none. '+latex(PLAIN_DISCLAIMER)+'.']
    parts += [r'\section*{Claims excluded from formal scope}']
    if excluded:
        for x in excluded:
            parts += [r'\noindent\textbf{'+latex(x['lean_theorem'])+': '+latex(x['exclusion_reason'])+'}. This declaration is not evidence for a FORMALLY VERIFIED scientific claim.',r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/'+x['id']+'.txt}']
    else: parts += ['No listed theorem is excluded by the current syntactic triviality rule. This does not constitute an independent nontriviality finding.']
    parts += [r'\section*{Full frozen mathematical context}',r'\noindent The following is a presentation-only ASCII rendering of the frozen statement. The byte-exact UTF-8 attachment is authoritative. Challenge placeholders here are the sealed statement contract; acceptance evidence is the separate unchanged Comparator certificate and its bound candidate.',r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/FROZEN_CONTEXT.txt}',r'\clearpage',r'\section*{Conjectures and UNCERTIFIED historical remarks}',r'\noindent\textbf{Every claim in the entire historical block below is UNCERTIFIED in this successor.} This applies to every paragraph, equation, theorem-like display, number, experiment, interpretation, source attribution and empirical assumption. Historical assertions of verification or proof status in this block are retained as historical text only and are not current evidence. Only the explicitly numbered frozen-statement scope above is proposed for later certification labeling. The original manuscript bytes are separately preserved with a complete paragraph-and-formula hash map.',r'\begin{quote}',r'\textbf{BEGIN ENTIRELY UNCERTIFIED HISTORICAL BLOCK}',archived_body,r'\textbf{END ENTIRELY UNCERTIFIED HISTORICAL BLOCK}',r'\end{quote}']
    extra=r'\usepackage{fvextra}'+'\n'
    onecolumn=r'\onecolumn'+'\n' if 'twocolumn' in before else ''
    paper=before+extra+r'\begin{document}'+'\n'+onecolumn+(r'\maketitle'+'\n' if had_title else '')+'\n\n'.join(parts)+'\n'+r'\end{document}'+'\n'
    # Intended publication text is neutral; audit/acceptance state stays in
    # external proposal receipts. All historical title/prose remains scoped.
    qualifier = r'\noindent\textbf{Historical title retained for provenance only; it is not a certified claim.}'
    if r'\maketitle' in paper:
        paper = paper.replace(r'\maketitle', r'\maketitle'+'\n'+qualifier, 1)
    else:
        paper = paper.replace(r'\begin{document}', r'\begin{document}'+'\n'+qualifier, 1)
    paper = paper.replace(r'\_',r'\_\allowbreak{}')
    paper = paper.replace(r'\begin{document}', r'\emergencystretch=4em'+'\n'+r'\AtBeginDocument{\sloppy}'+'\n'+r'\begin{document}',1)
    (out/'paper.tex').write_text(paper)
    # Every original byte is preserved in the archival attachment and classified.
    coverage={'standard':STANDARD,'status':'EXHAUSTIVE_PROPOSAL_PENDING_REVIEW','run_id':rid,'original_manuscripts':[],'new_scoped_claims':full_scope,'original_inventory_claims':imported_claims,'all_old_claims_explicitly_uncertified':True,'historical_block_is_verbatim_body':True,'historical_body_sha256':bsha(archived_body.encode()),'manuscript_title_preamble_preserved':True,'public_metadata_title_must_equal_before_title':title,'narrowing_is_not_approved_or_certified_by_this_map':True}
    for label,p in [('PUBLISHED_OR_CURRENT',current),('SEALED',sealed_tex)]:
        data=p.read_bytes();coverage['original_manuscripts'].append({'label':label,'source':binding(p),'preserved_attachment':binding(hist/('PUBLISHED_ORIGINAL_paper.tex' if label=='PUBLISHED_OR_CURRENT' else 'SEALED_ORIGINAL_paper.tex')),'paragraph_partition':source_partition(data),'formulas':[{'byte_start':m.start(),'byte_end_exclusive':m.end(),'sha256':bsha(m.group()),'evidence_class':'UNCERTIFIED_HISTORICAL_REMAINDER'} for m in re.finditer(br'\\\[.*?\\\]|\\begin\{(?:equation\*?|align\*?|gather\*?|theorem|lemma|proposition)\}.*?\\end\{(?:equation\*?|align\*?|gather\*?|theorem|lemma|proposition)\}',data,re.S)],'all_bytes_accounted_for':True})
    archived_rendered_body = archived_body.replace(r'\_',r'\_\allowbreak{}')
    coverage['historical_block_is_verbatim_body'] = archived_rendered_body == archived_body
    coverage['historical_body_rendered_sha256'] = bsha(archived_rendered_body.encode())
    coverage['layout_only_archive_rendering'] = {'before':r'\_', 'after':r'\_\allowbreak{}', 'original_attachment_unchanged':True}
    archive_start=paper.index(archived_rendered_body,paper.index(r'\textbf{BEGIN ENTIRELY UNCERTIFIED HISTORICAL BLOCK}'))
    archive_end=archive_start+len(archived_rendered_body)
    coverage['successor_regions']=[{'id':'NEW_SCOPED_PROPOSAL_AND_CONTEXT','byte_start':0,'byte_end_exclusive':len(paper[:archive_start].encode()),'sha256':bsha(paper[:archive_start].encode()),'evidence_class':'PROPOSED_SCOPE_NOT_REVIEWED','scope':'New status, exact frozen statement/context listings and exclusions only; no publication acceptance'}, {'id':'ENTIRE_UNCERTIFIED_ARCHIVE','byte_start':len(paper[:archive_start].encode()),'byte_end_exclusive':len(paper[:archive_end].encode()),'sha256':bsha(archived_rendered_body.encode()),'evidence_class':'UNCERTIFIED_HISTORICAL_REMAINDER','scope':'Every historical sentence, claim, formula, number and proof-status assertion'}, {'id':'ARCHIVE_CLOSE_AND_DOCUMENT_END','byte_start':len(paper[:archive_end].encode()),'byte_end_exclusive':len(paper.encode()),'sha256':bsha(paper[archive_end:].encode()),'evidence_class':'STATUS_AND_LAYOUT_ONLY'}]
    coverage['per_theorem_witness_compatibility_review']='PENDING; no automatic inference from a run-level certified witness'
    write_json(out/'WHOLE_PAPER_CLAIM_MAP.json',coverage)
    write_json(out/'WITNESS_REVIEW_MATRIX.json',{'status':'PENDING_INDEPENDENT_PER_THEOREM_COMPATIBILITY_REVIEW','run_id':rid,'run_level_nonvacuity_contract':witnesses,'rows':[{'claim_id':x['id'],'theorem':x['lean_theorem'],'exact_signature':x['frozen_signature_utf8'],'candidate_witnesses':[{'name':w,'exact_signature':decls[w]['signature']} for w in certified_witnesses],'selected_reviewed_witness':None,'compatibility_demonstrated':False,'required_review':'Provide an explicit substitution or argument matching every hypothesis in the theorem and record its exact frozen witness, including any theorem context; run-level witness existence alone is insufficient.'} for x in eligible]})
    write_json(out/'CERTIFIED_SCOPE.json',{'standard':STANDARD,'run_id':rid,'status':'PROPOSED_SCOPE_NOT_REVIEWED','certificate':binding(cert),'frozen_statement':binding(frozen),'candidate':binding(candidate),'ambient_global_assumptions':globals_,'full_frozen_context_retained':True,'eligible_claims':eligible,'excluded_claims':excluded,'nonvacuity':nonvacuity,'original_inventory':binding(Path(sealed['SEALED_CLAIM_INVENTORY.json']['path'])),'sealed_statement_not_modified':True})
    original_diff=''.join(difflib.unified_diff(text.splitlines(True),paper.splitlines(True),fromfile=str(current),tofile='paper.tex'))
    sealed_diff=''.join(difflib.unified_diff(sealed_bytes.decode().splitlines(True),paper.splitlines(True),fromfile=str(sealed_tex),tofile='paper.tex'))
    (out/'paper.diff').write_text(original_diff);(out/'paper_vs_sealed.diff').write_text(sealed_diff)
    structural=manuscript_structure.classify(sealed_bytes.decode(),paper);write_json(out/'STRUCTURE_DIFF.json',structural)
    entity=next(e for e in ledger['run_entities'] if e['id']==rid)
    claim_result=claim_binding.check_bindings(proposed_binding,entity,ledger)
    try:
        claim_binding._check_inventory(inspection,ledger,[{'english_claim':x['english_claim'],'lean_theorem':x['lean_theorem']} for x in eligible],targets)
        inventory_probe={'status':'PASS','scope':'Sealed English inventory comparison only; no claim or witness approval'}
    except Exception as e:
        inventory_probe={'status':'HOLD','reasons':[type(e).__name__+': '+str(e)],'scope':'Unchanged sealed English inventory comparison only; not a certification verdict'}
    # Invoke unchanged consumers truthfully; /private/tmp is deliberately outside
    # the canonical publication root and no publication receipt exists.
    try:
        p_result=publication_binding.validate_publication_binding(out,inspection,cert,root,[])
        binding_result={'status':'PASS','bindings':p_result}
    except Exception as e: binding_result={'status':'HOLD','reasons':[type(e).__name__+': '+str(e)]}
    premise_full=premise_declaration.evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT','claims':[{'claim':x['english_claim']} for x in eligible]},formal_statement=frozen_text,candidate=candidate_text,paper_text=paper,theorem_names=[x['lean_theorem'] for x in core_eligible] or [x['lean_theorem'] for x in eligible],required=True)
    main_source='\n'.join(parts).split(r'\section*{Claims excluded from formal scope}',1)[0]+r'\end{document}'
    premise_main=premise_declaration.evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT','claims':[{'claim':x['english_claim']} for x in eligible]},formal_statement=frozen_text,candidate=candidate_text,paper_text=main_source,theorem_names=[x['lean_theorem'] for x in core_eligible] or [x['lean_theorem'] for x in eligible],required=True)
    module_sources={m.__name__:binding(Path(m.__file__)) for m in (certificate_inspection,static_pregate,theorem_coverage,claim_binding,manuscript_structure,publication_binding,premise_declaration)}
    write_json(out/'CURRENT_GATE_RESULTS.json',{'status':'HOLD','certificate_inspection':inspection,'static_gate':static,'target_triviality':{n:trivial.get(n,{}) for n in targets},'claim_binding':claim_result,'sealed_inventory_scope_probe':inventory_probe,'publication_binding':binding_result,'structural_diff_classification':structural['classification'],'premise_proposal_full_paper':premise_full,'premise_main_scope_only_advisory_not_acceptance':premise_main,'gate_modules':module_sources,'local_lean_execution':False,'production_writes':False,'does_not_create_new_verification_evidence':True,'required_scoped_consumer_support':['Independently reviewed exact frozen theorem/hypothesis scope, no sealed input alteration','Exhaustive explicitly uncertified historical-region coverage','Allow independently audited narrowing with exact final upload hashes; ordinary status-only binding currently rejects CONTENT_CHANGED','Historical INV-9 declaration without certificate mutation; full-paper unverified archival region must not imply an admitted scientific premise']})
    code=aligner.strip_comments(candidate_text)
    basis_proposal={'standard':'VRS-PHASE7-INV9-BASIS-PROPOSAL-1','run_id':rid,'status':'PENDING_INDEPENDENT_STATEMENT_PREMISE_IMPORT_REVIEW','foundation_basis':'INDEPENDENT','scope':'Only exact frozen mathematical statements in the successor main scope; historical physical interpretations remain UNCERTIFIED','existing_55_classification_matches':row.get('existing_55_classification_matches',[]),'fresh_review_required':True,'imports':re.findall(r'(?m)^\s*import\s+[^\n]+',code),'candidate':binding(candidate),'statement':binding(frozen),'all_hypotheses_are_quoted_exactly':True,'global_assumptions':globals_,'definitions':re.findall(r'(?m)^\s*(?:noncomputable\s+)?(?:def|abbrev)\s+(\w+)',code),'reason':'The proposed scope is a scalar/Boolean/finite defined mathematical model. No Run-900/901 min-form theorem or Run-902 PL/PD product-form law is claimed; empirical meanings of parameters are excluded. Fresh independent review must validate this declaration against full frozen context and whole-paper coverage. Existing 55-classification describes historical physical interpretation, not proof certificate inheritance.','unchanged_full_paper_gate_result':premise_full,'unchanged_main_only_advisory_result':premise_main,'does_not_retrofit_certificate':True}
    write_json(out/'INV9_BASIS_PROPOSAL.json',basis_proposal)
    disp=row.get('mirror_disposition',{});dv=disp.get('value',{});corrections=[]
    for k in ('formal_status','proof_status'):
        if isinstance(dv.get(k),str) and any(s in dv[k] for s in ('UNCERTIFIED','UNPROVED','NOT_RUN')): corrections.append({'field':k,'before':dv[k],'proposed_after':'CERTIFIED_FROZEN_LEAN_ONLY_SUCCESSOR_SCOPE_PENDING_REVIEW','reason':'The existing valid Comparator certificate supersedes the old candidate proof-status label; this correction does not approve manuscript claims, novelty, significance, or publication.'})
    write_json(out/'DISPOSITION_CORRECTION_PLAN.json',{'standard':'VRS-APPEND-ONLY-DISPOSITION-CORRECTION-PLAN-1','run_id':rid,'status':'PLAN_ONLY_NO_ORIGINAL_EDITS','original':disp.get('binding'),'original_value':dv,'corrections':corrections,'append_only_successor_required':True,'keep_disposition':'METHODS_NOTE','keep_novelty_significance_unassessed':True,'certificate':binding(cert),'publication_binding_not_required_until_publish':True,'original_bytes_unchanged':True})
    metadata={'standard':STANDARD,'status':'PROPOSAL_ONLY_NO_WRITES','route':'VIRIDIS_METHODS_DIGEST_WEEKLY','standalone_new_doi_authorized_by_this_packet':False,'original_doi':pub.get('doi') if pub else None,'title_before_exact':title,'title_after_exact':title,'current_uncertified_banner_must_remain_until_all_gates_pass':True,'fallback_banner':BANNER,'conditional_after_all_gates_and_claude_audit':'SCOPED CERTIFIED mathematical claims only: '+', '.join(x['qualified_name'] for x in core_eligible)+'. All other historical claims remain UNCERTIFIED. '+PLAIN_DISCLAIMER+'.','certified_scope_claim_ids':[x['id'] for x in core_eligible],'excluded_claims':[{'id':x['id'],'name':x['qualified_name'],'classification':x['exclusion_reason']} for x in excluded],'current_public_evidence':pub.get('receipt_confirmed_uncertified_banner') if pub else None,'before_payload':'A fresh full metadata/public PID/file readback is required at execution; this proposal does not reconstruct or drop any metadata field.'}
    write_json(out/'METADATA_PROPOSAL.json',metadata)
    plan={'standard':'VRS-PHASE7-PUBLICATION-BINDING-PLAN-1','run_id':rid,'status':'PLAN_ONLY_NOT_PUBLICATION_BOUND','publication_authorized':False,'proof_certificate':binding(cert),'candidate_upload':binding(out/'VERIFICATION_CANDIDATE.lean'),'statement_upload':binding(out/'VERIFICATION_STATEMENT.lean'),'staged_tex':binding(out/'paper.tex'),'final_pdf_hash':None,'exact_upload_hashes':'Compute after final PDF rendering and independent review; never substitute historical PDF or invent a future hash','scope_review_status':'PENDING_CLAUDE_SPOT_AUDIT_FIRST_BATCH_AND_INDEPENDENT_SCOPE_REVIEW','current_consumer_status':'HOLD','current_consumer_reasons':binding_result['reasons'],'content_diff_requires_reviewed_scoped_consumer_support':structural['classification'],'steps':['Render this exact staged paper.tex and all local rendering inputs into a new paper.pdf; inspect PDF/source correspondence','Freeze exact inventory and SHA-256 of all final upload files; certificate, candidate and statement bytes must be the inspected exact original bytes','Independent reviewer checks every proposed theorem hypothesis/conclusion, full context, per-claim witness compatibility, excluded trivial/contradictory statements and exhaustive archival coverage','Root records approved scoped-release review receipt bound to exact claim map, diff, final TeX/PDF and certificate; no fabricated approval','Generate publication binding only immediately before publish; it binds certificate plus exact final manuscript and upload inventory hashes under approved scoped consumer','Reuse strict metadata/file/PID precheck and readback; Methods Notes are included in one weekly digest with per-note certificate/binding/scope, old DOI provenance retained','If any gate cannot PASS, keep UNCERTIFIED banner and HOLD publication/relabel']}
    write_json(out/'PUBLICATION_BINDING_PLAN.json',plan)
    inputs=[cert,candidate,frozen,sealed_tex,current,source_claim_path]
    checks=[{'path':str(p),'sha256':sha(p),'expected_sha256':next((z['sha256'] for z in inspection.get('bindings',[]) if z.get('resolved_path')==str(p)),None)} for p in inputs]
    # Ensure no canonical source changed during staging and copied proof bytes exact.
    _assert_snapshot({**source_hashes,**module_inputs})
    for p,copy in [(candidate,out/'VERIFICATION_CANDIDATE.lean'),(frozen,out/'VERIFICATION_STATEMENT.lean'),(cert,out/'LEAN_ZERO_SORRY_CERTIFICATE.json'),(current,hist/'PUBLISHED_ORIGINAL_paper.tex'),(sealed_tex,hist/'SEALED_ORIGINAL_paper.tex')]:
        if p.read_bytes()!=copy.read_bytes():raise ValueError('copied source differs: '+str(p))
    summary={'run_id':rid,'status':STAGING,'route':'METHODS_DIGEST_WEEKLY','original_doi':pub.get('doi') if pub else None,'title_exact':title,'eligible_scoped_declarations':len(eligible),'eligible_nonwitness_main_claims':len(core_eligible),'excluded_declarations':[{'name':x['lean_theorem'],'reason':x['exclusion_reason']} for x in excluded],'original_inventory_claim_count':len(imported_claims),'original_paragraphs_classified_uncertified':sum(len(v['paragraph_partition']) for v in coverage['original_manuscripts']),'certificate_valid':True,'static_gate_pass':True,'current_claim_gate_status':claim_result['status'],'current_claim_gate_reasons':claim_result['reasons'],'sealed_inventory_scope_probe':inventory_probe,'current_publication_gate_status':binding_result['status'],'unchanged_premise_full_paper':premise_full['status'],'unchanged_premise_full_paper_reasons':premise_full['reasons'],'disposition_correction_count':len(corrections),'paper_tex_sha256':sha(out/'paper.tex'),'source_inputs':checks,'package_path':str(out),'local_lean_execution':False,'production_writes':False}
    write_json(out/'PACKAGE_STATUS.json',summary)
    write_json(out/'SOURCE_INPUTS.json',{'canonical_root':str(root),'generation_root_read_for_certification':False,'inputs':checks,'module_sources':module_sources,'source_hashes_stable':True})
    return summary



def complete_package(artifact, canonical_root):
    """Bind the rendered draft; semantic/whole-PDF approval remains independent.

    This only documents exact already-certified source declarations. It cannot
    fabricate a witness assignment, review approval, binding receipt or verdict.
    """
    from scoped_release import ambient_context, STANDARD as SCOPE_STANDARD, REVIEW_SCOPE
    from scoped_statement_text import signature_parts
    from theorem_coverage import triviality
    from certificate_inspection import inspect_certificate, resolve_binding
    root=Path(canonical_root).resolve(strict=True);artifact=_staging_output(root,artifact).resolve(strict=True)
    outputs=('SCOPED_CLAIM_MAP.json','SCOPED_STATEMENT_INVENTORY.json','SCOPED_FOUNDATION_BASIS.json','SCOPE_EVIDENCE.zip','INV9_MAIN_SCOPE_PROJECTION.json','SCOPED_RELEASE_MANIFEST.json')
    if any((artifact/n).exists() or (artifact/n).is_symlink() for n in outputs):
        raise ValueError('immutable package outputs already exist; HOLD, never overwrite')
    original_inputs={}
    for p in artifact.rglob('*'):
        if p.is_symlink():raise ValueError('normalizer input symlink refused')
        if p.is_file():original_inputs[p]=sha(p)
    rid=artifact.name.split('-',2)
    if (artifact/'CERTIFIED_SCOPE.json').is_file():
        scope=json.loads((artifact/'CERTIFIED_SCOPE.json').read_text()); identity=scope['run_id']
        certificate=resolve_binding(scope['certificate'],root); original=scope['eligible_claims']
        records={v['lean_theorem']:v for v in json.loads((artifact/'claim_binding.json').read_text())['claims']}
        basis_name='INV9_BASIS_PROPOSAL.json'; inventory_name='CERTIFIED_SCOPE.json'; full_map='WHOLE_PAPER_CLAIM_MAP.json'
    else:
        scope=json.loads((artifact/'statement_inventory.json').read_text());identity=scope['run_id']
        old_map=json.loads((artifact/'claim_map.json').read_text());certificate=resolve_binding(old_map['certificate'],root)
        original=scope['declarations'];records={v['lean_theorem']:v for v in old_map['claims']}
        basis_name='foundation_basis.json'; inventory_name='statement_inventory.json';full_map='claim_map.json'
    original_inputs[certificate]=sha(certificate)
    inspection=inspect_certificate(certificate,root)
    if (inspection.get('valid') is not True or inspection.get('run_id')!=identity
            or inspection.get('sha256')!=original_inputs[certificate]):raise ValueError('current certificate HOLD or changed')
    for record in inspection.get('bindings',[]):
        p=resolve_binding({'path':record['resolved_path'],'sha256':record['sha256']},root)
        original_inputs[p]=record['sha256']
    candidate=Path(inspection['candidate_path']);cert=json.loads(certificate.read_text())
    formal=resolve_binding(cert['bindings']['formal_statement'],root)
    if sha(candidate)!=inspection.get('candidate_sha256'):raise ValueError('candidate changed after inspection')
    original_inputs[candidate]=inspection['candidate_sha256'];original_inputs[formal]=cert['bindings']['formal_statement']['sha256']
    for source,target in ((certificate,'LEAN_ZERO_SORRY_CERTIFICATE.json'),(candidate,'VERIFICATION_CANDIDATE.lean'),(formal,'VERIFICATION_STATEMENT.lean')):
        if source.read_bytes()!=(artifact/target).read_bytes():raise ValueError('raw frozen upload changed: '+target)
    source=candidate.read_text();coverage=triviality(source);statements=[]
    for original_record in original:
        name=original_record['lean_theorem'];record=records[name];declaration=coverage[name]
        docs=binder_documentation(declaration['signature']); exact_binders, exact_conclusion = signature_parts(declaration['signature'])
        claim={'lean_theorem':name,'english_claim':record['english_claim'],'exact_source_signature':declaration['signature'],
            'ambient_source_context':ambient_context(source,declaration['line']),
            'explicit_binders_and_hypotheses':exact_binders, 'conclusion':exact_conclusion,
            'model_fidelity':record['model_fidelity'],'evidence_class':'CERTIFIED_TRIVIAL' if declaration['classification']=='CERTIFIED_TRIVIAL' else 'FORMALLY_VERIFIED',
            'nonvacuity_obligation':record.get('nonvacuity_obligation'),
            'scope_status':'PROPOSAL_ONLY_NOT_APPROVED','printed_disclaimer':PLAIN_DISCLAIMER}
        if 'id' in original_record and (artifact/'rendered'/(original_record['id']+'.txt')).is_file():
            p=artifact/'rendered'/(original_record['id']+'.txt');claim['display_file']={'relative_path':str(p.relative_to(artifact)),'sha256':sha(p)}
            context=artifact/'rendered/FROZEN_CONTEXT.txt'
            claim['context_display_file']={'relative_path':str(context.relative_to(artifact)),'sha256':sha(context)}
        statements.append(claim)
    write_json(artifact/'SCOPED_CLAIM_MAP.json',{'run_id':identity,'standard':SCOPE_STANDARD,'status':'DRAFT_AWAITING_CLAUDE_AUDIT',
        'claims':statements,'whole_paper_map':{'filename':full_map,'sha256':sha(artifact/full_map)},'all_original_claims_explicitly_uncertified':True})
    write_json(artifact/'SCOPED_STATEMENT_INVENTORY.json',{'run_id':identity,'standard':SCOPE_STANDARD,'declarations':statements,
        'frozen_context_inventory':{'filename':inventory_name,'sha256':sha(artifact/inventory_name)},'elaborates_or_verifies_Lean':False})
    basis=json.loads((artifact/basis_name).read_text())
    if basis.get('foundation_basis') not in {'THEOREM','INDEPENDENT','CONDITIONAL_PL_PD'}:raise ValueError('explicit INV-9 basis absent')
    write_json(artifact/'SCOPED_FOUNDATION_BASIS.json',{'run_id':identity,'foundation_basis':basis['foundation_basis'],
        'status':'FRESH_CLASSIFICATION_PROPOSED_FOR_INDEPENDENT_REVIEW','source':{'filename':basis_name,'sha256':sha(artifact/basis_name)},'historical_certificate_unchanged':True})
    # Exact rendering inputs and archival originals travel inside an evidence
    # archive. The attached raw UTF-8 Lean files remain proof inputs of record.
    import zipfile
    archive=artifact/'SCOPE_EVIDENCE.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(artifact.rglob('*')):
            if not p.is_file() or p.is_symlink() or 'build' in p.relative_to(artifact).parts or p.name in {'paper.pdf','paper.tex','SCOPE_EVIDENCE.zip','SCOPED_RELEASE_MANIFEST.json','SCOPED_DRAFT_CHECK.json','PUBLICATION_BINDING_PLAN.json'}:continue
            info=zipfile.ZipInfo(str(p.relative_to(artifact)),date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o600<<16
            z.writestr(info,p.read_bytes())
    local=lambda name:{'filename':name,'sha256':sha(artifact/name)}
    tex=artifact/'paper.tex';pdf=artifact/'paper.pdf'
    manifest={'standard':SCOPE_STANDARD,'scope':REVIEW_SCOPE,'run_id':identity,
        'certificate':{'path':str(certificate),'sha256':sha(certificate)},'candidate':{'path':str(candidate),'sha256':sha(candidate)},
        'formal_statement':{'path':str(formal),'sha256':sha(formal)},'claim_map':local('SCOPED_CLAIM_MAP.json'),
        'statement_inventory':local('SCOPED_STATEMENT_INVENTORY.json'),'foundation_basis':local('SCOPED_FOUNDATION_BASIS.json'),
        'uploads':[local(n)for n in ('paper.tex','paper.pdf','VERIFICATION_CANDIDATE.lean','VERIFICATION_STATEMENT.lean','LEAN_ZERO_SORRY_CERTIFICATE.json','SCOPED_CLAIM_MAP.json','SCOPED_STATEMENT_INVENTORY.json','SCOPED_FOUNDATION_BASIS.json','SCOPE_EVIDENCE.zip')],
        'final_tex_sha256':sha(tex),'final_pdf_sha256':sha(pdf),'statement_scope':statements}
    text=tex.read_text()
    marker=r'\section*{Claims excluded from formal scope}'
    if marker not in text:marker=r'\section*{Conjectures'
    if marker in text:
        main=text.split(marker,1)[0]+r'\end{document}'
        write_json(artifact/'INV9_MAIN_SCOPE_PROJECTION.json',{'rule':'AUDITED_UNCERTIFIED_ARCHIVE_EXCLUSION','final_tex_sha256':sha(tex),'paper_text':main,
            'status':'DRAFT_ONLY; independent whole-paper coverage approval required','excluded_historical_claims_remain_uncertified':True})
        manifest['inv9_projection']=local('INV9_MAIN_SCOPE_PROJECTION.json')
        manifest['uploads'].append(local('INV9_MAIN_SCOPE_PROJECTION.json'))
    _assert_snapshot(original_inputs)
    write_json(artifact/'SCOPED_RELEASE_MANIFEST.json',manifest)
    return manifest



def _fresh_stage_target(root, entry, ledger):
    """Fresh receipt/SSOT/parity consumption; Desktop bytes are parity only.

    The whole ledger is a per-invocation read snapshot, not an everlasting
    package input. This closed target projection omits other runs and scan-wide
    timestamps/counts while retaining the fields which authorize this intake.
    """
    import mirror_parity
    from science_release_queue import (PAPER_ROOT, contained_file,
        full_directory_snapshot, load_existing_consumers)
    identity=entry['run_id'];source=Path(entry['source_dir'])
    rows=[row for row in ledger.get('run_entities',[]) if row.get('id')==identity]
    if len(rows)!=1:raise ValueError('staging target must match exactly one current SSOT entity')
    row=rows[0];relative=Path(row.get('path',''))
    if (relative.is_absolute() or relative.parent!=PAPER_ROOT
            or not relative.name.startswith(identity+'_') or root/relative!=source
            or row.get('entity_type')!='RUN' or row.get('kind')!='PAPER'
            or row.get('status')!='CERTIFIED' or row.get('certificate_valid')is not True):
        raise ValueError('current staging target path/kind/status/certificate differs')
    certificate=contained_file(root,entry['certificate']['path'])
    if (certificate.parent!=root/'RESEARCH_PIPELINE_v2/lean_certificates'/identity
            or contained_file(root,row.get('certificate',''))!=certificate):
        raise ValueError('current SSOT certificate differs from immutable intake')
    existing=load_existing_consumers(root)
    if {k:existing[k+'_binding'] for k in ('proof_track','inspection')}!=entry['consumer_bindings']:
        raise ValueError('fresh canonical consumer binding differs from intake')
    current=existing['proof_track'].current_certificate(root,identity)
    if not current or contained_file(root,current[0])!=certificate:
        raise ValueError('fresh canonical current-certificate selector differs')
    inspection=existing['inspection'].inspect_certificate(certificate,root)
    if (inspection.get('valid')is not True or inspection.get('recorded_certificate_current')is not True
            or inspection.get('run_id')!=identity or inspection.get('path')!=str(certificate)
            or inspection.get('sha256')!=entry['certificate']['sha256']):
        raise ValueError('fresh current certificate HOLD')
    inspected=[{'label':v['label'],'path':str(contained_file(root,v['resolved_path'])),
        'sha256':v['sha256']} for v in inspection.get('bindings',[])]
    if sorted(inspected,key=lambda v:v['label'])!=sorted(entry['certified_inputs'],key=lambda v:v['label']):
        raise ValueError('fresh certificate input contract differs from intake')
    if (row.get('certified_theorems')!=inspection.get('certified_theorems')
            or row.get('nonvacuity')!=inspection.get('nonvacuity')):
        raise ValueError('current SSOT certified theorem/witness inventory differs')
    parity=mirror_parity.run_parity(root,relative)
    if (parity.get('status')!='MATCH' or parity.get('mirror')!=str(source)
            or parity.get('purpose')!='PARITY_ONLY_NOT_CERTIFICATION'
            or parity.get('mirror_hashes')!=entry['source_hashes']
            or not isinstance(parity.get('source_hashes'),dict)
            or parity.get('errors') or parity.get('differences')
            or parity!=row.get('parity')):
        raise ValueError('fresh source/mirror parity differs from current SSOT/intake')
    if full_directory_snapshot(root,source)!=entry['source_hashes']:
        raise ValueError('intake source snapshot changed')
    projection={key:row.get(key) for key in ('id','entity_type','kind','path','status',
        'certificate_valid','certified_theorems','nonvacuity','parity','certificate_artifacts')}
    projection['certificate']=str(certificate)
    return projection


def stage_current_entry(root, entry_path, ledger_path, *, renderer=None):
    """Automatic immutable scope-package path after intake, never publish."""
    import subprocess
    from science_release_queue import full_directory_snapshot, contained_file, run_id, write_immutable
    root=Path(root).resolve(strict=True)
    entry_path=contained_file(root,entry_path);ledger_path=contained_file(root,ledger_path)
    initial={entry_path:sha(entry_path),ledger_path:sha(ledger_path)}
    entry=json.loads(entry_path.read_text());ledger=json.loads(ledger_path.read_text())
    identity=run_id(entry['run_id']);certificate=entry['certificate']
    certificate_path=contained_file(root,certificate['path'])
    certificate_sha=certificate.get('sha256')
    if re.fullmatch(r'[0-9a-f]{64}',str(certificate_sha)) is None:
        raise ValueError('exact certificate hash required')
    expected_entry_id=identity+'-'+certificate_sha
    if (entry.get('entry_id')!=expected_entry_id or entry_path.name!=expected_entry_id+'.json'
            or entry.get('schema')!='VRS-SCIENCE-RELEASE-QUEUE-1'
            or entry.get('mode')!='REPORT_ONLY' or entry.get('publication_enabled') is not False):
        raise ValueError('closed report-only intake identity required')
    if (entry.get('route') not in {'WEEKLY_METHODS_DIGEST','SCOPED_SUCCESSOR_REVIEW','STANDALONE_PAPER_REVIEW'}
            or re.fullmatch(r'[0-9]{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3])',str(entry.get('digest_week'))) is None):
        raise ValueError('closed route and digest week required')
    if ledger.get('tree_root')!=str(root):raise ValueError('ledger tree root differs')
    bindings=entry.get('certified_inputs')
    consumers=entry.get('consumer_bindings')
    required={'bindings.candidate_proof','bindings.formal_statement','bindings.request',
        'bindings.independent_cloud_receipt','bindings.sealed_paper_inputs.SEALED_paper.tex',
        'bindings.sealed_paper_inputs.SEALED_paper.pdf'}
    if (not isinstance(bindings,list) or any(not isinstance(v,dict)for v in bindings)
            or len({v.get('label')for v in bindings})!=len(bindings)
            or not required.issubset({v.get('label')for v in bindings})
            or not isinstance(consumers,dict) or set(consumers)!={'proof_track','inspection'}):
        raise ValueError('complete certified input and consumer bindings required')
    for bound in [certificate,*bindings,*consumers.values()]:
        path=contained_file(root,bound['path'])
        if sha(path)!=bound.get('sha256'):raise ValueError('intake bound input changed')
        if path in initial and initial[path]!=bound['sha256']:raise ValueError('conflicting intake input binding')
        initial[path]=bound['sha256']
    source=Path(entry['source_dir'])
    if full_directory_snapshot(root,source)!=entry['source_hashes']:raise ValueError('intake source snapshot changed')
    target_projection=_fresh_stage_target(root,entry,ledger)
    _assert_snapshot(initial)
    out=_staging_output(root,root/'RESEARCH_PIPELINE_v2/science_release_queue/staged'/expected_entry_id/identity)
    if out.exists():
        status_path=out/'AUTO_STAGE_RESULT.json'
        if not status_path.is_file() or status_path.is_symlink():raise ValueError('incomplete immutable staging attempt; HOLD, never overwrite')
        status=json.loads(status_path.read_text())
        if (status.get('entry_sha256')!=initial[entry_path] or status.get('run_id')!=identity
                or status.get('artifact')!=str(out) or status.get('publication_enabled')is not False
                or status.get('zenodo_writes')!=0 or status.get('local_lean_execution')is not False
                or status.get('route')!=entry['route'] or status.get('digest_week')!=entry['digest_week']):
            raise ValueError('staged intake identity or report-only state changed')
        files=status.get('files')
        if not isinstance(files,dict)or not files:raise ValueError('complete immutable package inventory required')
        actual={}
        for p in sorted(out.rglob('*')):
            if p.is_symlink():raise ValueError('immutable staged package contains a symlink')
            if p.is_file()and p!=status_path:actual[str(p.relative_to(out))]=sha(p)
        if files!=actual:raise ValueError('staged package bytes/inventory changed')
        historical=status.get('input_bindings')
        current_bindings={str(p):h for p,h in initial.items()}
        ledger_key=str(ledger_path)
        if (not isinstance(historical,dict)
                or re.fullmatch(r'[0-9a-f]{64}',str(historical.get(ledger_key))) is None
                or {k:v for k,v in historical.items()if k!=ledger_key}
                    !={k:v for k,v in current_bindings.items()if k!=ledger_key}):
            raise ValueError('staged source/receipt/consumer binding changed')
        prior_projection=status.get('target_projection')
        if prior_projection is not None and prior_projection!=target_projection:
            raise ValueError('staged target semantic SSOT binding changed')
        status_hash=sha(status_path)
        _assert_snapshot(initial)
        if _fresh_stage_target(root,entry,ledger)!=target_projection:
            raise ValueError('target/parity changed while checking staged output')
        _assert_snapshot(initial)
        if sha(status_path)!=status_hash:raise ValueError('immutable staged status changed during revalidation')
        result={**status,'state':'ALREADY_STAGED_IDENTICAL_BYTES'}
        if historical[ledger_key]!=current_bindings[ledger_key]:
            # A new proof of current consumption lives outside the immutable
            # package. Its historical ledger hash remains original provenance.
            receipt={'schema':'VRS-SCIENCE-STAGING-REVALIDATION-1',
                'state':'ALREADY_STAGED_IDENTICAL_BYTES','run_id':identity,
                'entry_binding':{'path':str(entry_path),'sha256':initial[entry_path]},
                'immutable_status_binding':{'path':str(status_path),'sha256':status_hash},
                'historical_ledger_binding':{'path':ledger_key,'sha256':historical[ledger_key]},
                'current_ledger_binding':{'path':ledger_key,'sha256':current_bindings[ledger_key]},
                'target_projection':target_projection,'current_input_bindings':current_bindings,
                'immutable_output_inventory':files,
                'publication_enabled':False,'zenodo_writes':0,'local_lean_execution':False,
                'certificate_acceptance_changed':False,'source_reads':'PARITY_ONLY_NOT_CERTIFICATION'}
            receipt_hash=bsha(json.dumps(receipt,indent=2,sort_keys=True).encode()+b'\n')
            receipt_path=root/'RESEARCH_PIPELINE_v2/science_release_queue/revalidations'/expected_entry_id/(receipt_hash+'.json')
            write_immutable(receipt_path,receipt)
            _assert_snapshot(initial)
            if sha(status_path)!=status_hash:raise ValueError('immutable staged status changed during receipt creation')
            result['revalidation_receipt']={'path':str(receipt_path),'sha256':sha(receipt_path)}
        return result
    executable=Path(renderer or '/opt/homebrew/bin/tectonic')
    if str(executable)!='/opt/homebrew/bin/tectonic':raise ValueError('only the installed PDF renderer /opt/homebrew/bin/tectonic is permitted; no substituted executable')
    gates=Path(__file__).parent
    disposition_path=source/'DISPOSITION.json'
    row={'run_id':identity,'independent_current_certificate':certificate,
        'mirror_disposition':{'binding':binding(disposition_path),'value':json.loads(disposition_path.read_text())},
        'manuscripts':{'finalized_tex':{'path':str(root/'RESEARCH_PIPELINE_v2/finalized_runs'/identity/'paper.tex')}},
        'publications':[{'doi':d}for d in entry['existing_public_dois']]}
    stage_run(row,out,root,gates,ledger)
    # If any remaining step fails, the first immutable attempt remains intact.
    # A repeated call cannot overwrite or retry a consumed renderer operation.
    try:
        build=out/'build';build.mkdir()
        command=[str(executable),'--keep-logs','--outdir',str(build),'paper.tex']
        proc=subprocess.run(command,cwd=out,capture_output=True,timeout=180)
        (build/'COMPILER.stdout').write_bytes(proc.stdout);(build/'COMPILER.stderr').write_bytes(proc.stderr)
        if proc.returncode!=0:raise ValueError('PDF renderer HOLD; immutable attempt retained')
        shutil.copyfile(build/'paper.pdf',out/'paper.pdf')
        complete_package(out,root)
        _assert_snapshot(initial)
        if full_directory_snapshot(root,source)!=entry['source_hashes']:raise ValueError('source changed during staging')
        if _fresh_stage_target(root,entry,ledger)!=target_projection:raise ValueError('target/parity changed during staging')
        _assert_snapshot(initial)
        status={'state':'STAGED_PENDING_INDEPENDENT_CLAUDE_AUDIT','run_id':identity,'artifact':str(out),
            'entry_sha256':initial[entry_path],'input_bindings':{str(p):h for p,h in initial.items()},
            'target_projection':target_projection,
            'publication_enabled':False,'zenodo_writes':0,'local_lean_execution':False,
            'route':entry['route'],'digest_week':entry['digest_week'],
            'files':{str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}}
        if any(p.is_symlink()for p in out.rglob('*')):raise ValueError('staged package contains a symlink')
        write_json(out/'AUTO_STAGE_RESULT.json',status)
        return status
    except Exception as exc:
        failure=out/'AUTO_STAGE_HOLD.json'
        if not failure.exists():
            write_json(failure,{'state':'HOLD','run_id':identity,'entry_sha256':initial[entry_path],
                'cause':type(exc).__name__+': '+str(exc),'publication_enabled':False,'zenodo_writes':0,'local_lean_execution':False,
                'immutable_attempt_retained':True,'automatic_retry_permitted':False})
        raise
