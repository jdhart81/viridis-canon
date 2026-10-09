"""Current deterministic nightly scope consumer; never a Lean verifier.

The existing Comparator/issuer certificate and run-level nonvacuity are mandatory.
Only exact quoted frozen statements, named hypotheses and model-defined symbols
are admitted. Optional per-claim witnesses/depth are truthful non-blocking labels.
The historical56 authority population is never enlarged or relabeled.
"""
from __future__ import annotations
from copy import deepcopy
import datetime as dt,hashlib,json,re
from pathlib import Path
import methods_digest as d
import scoped_release as scoped
from certificate_inspection import inspect_certificate,resolve_binding
from theorem_coverage import declarations,triviality
from static_pregate import scan,code_only
from scoped_statement_text import signature_parts
from science_release_stage import ascii_render,latex,source_partition,binder_documentation
from premise_declaration import _aligner,evaluate as premise_evaluate

RULE_STANDARD='VRS-NIGHTLY-MINIMAL-EXACT-SCOPE-RULE-1'
BINDING_STANDARD='VRS-NIGHTLY-MINIMAL-EXACT-SCOPE-PUBLICATION-BINDING-1'
SOURCE_STANDARD='VRS-NIGHTLY-MINIMAL-EXACT-SCOPE-SOURCE-1'
DISCLAIMER=scoped.DISCLAIMER
ARCHIVE_MARKER=r'\section*{Entirely UNCERTIFIED historical manuscript}'
RULE_FIELDS={'standard','status','run_id','authority','source_manifest','issued_at_utc','execution_consumer_sha256','inputs','identity','claim_reviews','scope_comparison','certifies'}
BINDING_FIELDS={'standard','status','run_id','authority','policy_receipt','identity','issued_at_utc','execution_consumer_sha256','certifies'}
SOURCE_FIELDS={'standard','status','run_id','certificate','source_manuscript','before_metadata','selected_theorems','foundation_basis','selection_at_utc','selection_invocation','prior_cycle','source_pins','source_generator_sha256','certifies'}
class NightlyScopeHold(ValueError):pass

def need(v,r):
 if not v:raise NightlyScopeHold('HOLD_'+r)
def source_sha():return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def exact(a,b):return d.raw_json(a)==d.raw_json(b)
def now():return dt.datetime.now(dt.timezone.utc)
def time(value):
 result=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'));need(result.tzinfo is not None,'UTC_TIME_REQUIRED');return result.astimezone(dt.timezone.utc)
def binding(p):return {k:d.binding(p)[k]for k in('path','sha256')}
def read(root,value,seen):
 need(isinstance(value,dict)and set(value)=={'path','sha256'},'CLOSED_MATERIAL_BINDING')
 try:p,b=d.bound_file(root,value)
 except(OSError,ValueError)as exc:raise NightlyScopeHold('HOLD_BOUND_MATERIAL_UNAVAILABLE_OR_CHANGED')from exc
 need(str(p)not in seen or seen[str(p)]==d.digest(b),'CONFLICTING_INPUT');seen[str(p)]=d.digest(b);return p,b
def finish(seen):
 for p,h in seen.items():need(d.digest(d.read_regular(p))==h,'INPUT_CHANGED_BEFORE_RETURN')
def canonical_run(value):
 need(isinstance(value,str)and re.fullmatch('Run-[0-9]{3}',value)is not None and 189<=int(value[4:])<900,'NEW_NIGHTLY_RUN_ONLY');return value

def authority(root,compatibility_binding,seen):
 """Old authority is compatibility only; minimal current directive is causal."""
 import phase7_audit_policy as p
 import phase7_policy_versions as versions
 # Existing aggregate ABI expects this exact already-approved authority. No
 # fabricated historical entry is added for the new run.
 a=p.require_audit_authority(root,compatibility_binding)
 for path,h in a['input_bindings'].items():read(root,{'path':path,'sha256':h},seen)
 p.require_minimal_authority(root,seen)
 path=Path(root)/'reports/verification-coverage/GAME_PLAN.md';raw=d.read_regular(path);seen[str(path)]=d.digest(raw)
 view=versions.normalize_authority_plan(raw)
 start,end=versions._authority_section(view,versions.APPENDIX_HEADER)
 section=view[start:end]
 need(d.digest(section)==versions.APPENDIX_SHA256 or(section.endswith(versions.SUFFIX)and d.digest(section[:-len(versions.SUFFIX)])==versions.APPENDIX_SHA256),'CURRENT_APPROVED_BACKLOG_DIRECTIVE')
 return {'minimal_authority_sha256':p.MINIMAL_AUTHORITY_SHA,'approved_current_appendix_sha256':versions.APPENDIX_SHA256,'new_historical_audit_row':False}

def claim_scope(candidate,formal,inspection,selected):
 """Pure exact source correspondence and printed model tags, no elaboration."""
 names=[v['name']if isinstance(v,dict)else v for v in inspection.get('certified_theorems',[])]
 witnesses=[v['name']if isinstance(v,dict)else v for v in inspection.get('nonvacuity',[])]
 need(names and witnesses and len(names)==len(set(names))and len(witnesses)==len(set(witnesses)),'ISSUER_RUN_NONVACUITY_AND_EXPORTS')
 need(isinstance(selected,list)and selected and len(selected)==len(set(selected))and all(isinstance(n,str)and n in names for n in selected),'UNIQUE_CERTIFICATE_LISTED_SELECTION')
 ds=declarations(candidate);cov=triviality(candidate);aligner=_aligner();rows=[]
 for i,name in enumerate(selected,1):
  need(name in ds and name in cov,'EXACT_ACTIVE_DECLARATION');declaration=ds[name]
  need(aligner.normalized_signature(candidate,name)==aligner.normalized_signature(formal,name),'FROZEN_HYPOTHESIS_OR_CONCLUSION_CHANGED')
  need(not re.search(r':\s*(?:False|True)\s*$',declaration['signature']),'NO_VACUOUS_HEADLINE')
  qualified=[n for n,v in ds.items()if v is declaration and '.'in n]
  qualified=qualified[0]if len(qualified)==1 else name
  docs=binder_documentation(declaration['signature']);binders,conclusion=signature_parts(declaration['signature'])
  rows.append({'lean_theorem':name,'english_claim':'Under every hypothesis in the frozen statement, '+qualified+' establishes exactly its quoted conclusion. No empirical identification or additional physical law is asserted.',
   'exact_source_signature':declaration['signature'],'explicit_binders_and_hypotheses':binders,'conclusion':conclusion,'ambient_source_context':scoped.ambient_context(candidate,declaration['line']),
   'model_fidelity':{'defined':docs['defined_parameter_names']or['Mathlib mathematical values in the frozen statement'],'empirically_identified':[]},
   'evidence_class':'CERTIFIED_TRIVIAL'if cov[name]['classification']=='CERTIFIED_TRIVIAL'else'FORMALLY_VERIFIED','nonvacuity_obligation':None,
   'printed_disclaimer':DISCLAIMER,'scope_status':'SOURCE_BOUND_CURRENT_DETERMINISTIC_REVIEW_REQUIRED','display_file':{'relative_path':f'rendered/statement-{i:03d}.txt','sha256':d.digest(ascii_render(declaration['signature']).encode())},
   'context_display_file':{'relative_path':'rendered/FROZEN_CONTEXT.txt','sha256':d.digest(ascii_render(formal).encode())}})
 return rows

def expected_paper(run,basis,scope):
 canonical_run(run);need(basis in{'INDEPENDENT','THEOREM','CONDITIONAL_PL_PD'},'EXPLICIT_BASIS')
 lines=[r'\documentclass[10pt]{article}',r'\usepackage[margin=0.75in]{geometry}',r'\usepackage{amsmath,amssymb,fvextra}',r'\emergencystretch=4em',r'\AtBeginDocument{\sloppy}',r'\title{'+latex(run)+r': exact certified mathematical statement scope}',r'\author{Justin D. Hart}',r'\date{}',r'\begin{document}',r'\maketitle',r'\begin{abstract}', 'Foundation basis: '+latex(basis)+'. '+('The result is conditional on premises PL and PD. 'if basis=='CONDITIONAL_PL_PD'else'')+'Only the exact quoted certified mathematical statements and every explicit or ambient hypothesis below are asserted. No aggregate theorem or empirical validation is claimed.',r'\end{abstract}',r'\section*{Frozen mathematical scope}',
  'Only the exact frozen statements below, including every named and ambient hypothesis, carry the indicated certificate evidence. The source declarations and full mathematical context are authoritative. No additional equation, number, empirical identification or physical law is asserted.',
  r'\noindent Foundation basis: \textbf{'+latex(basis)+'}. '+DISCLAIMER+'.',
  'The existing certificate includes its issuer-required run-level nonvacuity obligations. Optional per-claim nonvacuity/depth enrichment is independent of publication eligibility. No aggregate theorem is claimed.']
 for i,c in enumerate(scope,1):
  lines.extend([r'\subsection*{'+latex(c['lean_theorem'])+'}',latex(c['english_claim']),r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/statement-'+f'{i:03d}'+'.txt}',
    'Evidence class: '+latex(c['evidence_class'])+'. Model symbols are defined mathematical inputs; empirically identified symbols: none. '+DISCLAIMER+'.'])
 lines.extend([r'\section*{Full frozen mathematical context}',r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/FROZEN_CONTEXT.txt}',ARCHIVE_MARKER,
  r'\noindent\textbf{Every sentence, equation, number, theorem-like assertion and physical assumption in the entire historical listing below is UNCERTIFIED in this release.} Historical verification wording is archival text only. The byte-exact original manuscript and complete paragraph/formula map accompany the release.',
  r'\VerbatimInput[fontsize=\scriptsize,breaklines=true,breakanywhere=true]{rendered/HISTORICAL_SOURCE.txt}',r'\end{document}'])
 return ('\n\n'.join(lines)+'\n').encode()

def validate_exact_body(run,basis,scope,tex):
 need(isinstance(tex,bytes)and tex==expected_paper(run,basis,scope),'UNEXPECTED_SCIENTIFIC_SENTENCE_OR_HYPOTHESIS');need(DISCLAIMER.encode()in tex,'PRINTED_DISCLAIMER')
 return tex.decode().split(ARCHIVE_MARKER,1)[0]+r'\end{document}'

UPLOAD_NAMES={'paper.tex','paper.pdf','VERIFICATION_CANDIDATE.lean','VERIFICATION_STATEMENT.lean','LEAN_ZERO_SORRY_CERTIFICATE.json','SCOPED_CLAIM_MAP.json','SCOPED_STATEMENT_INVENTORY.json','SCOPED_FOUNDATION_BASIS.json','SCOPE_EVIDENCE.zip','WHOLE_PAPER_MAP.json','metadata.json','NIGHTLY_SCOPE_SOURCE.json'}
MANIFEST_FIELDS={'standard','scope','run_id','certificate','candidate','formal_statement','claim_map','statement_inventory','foundation_basis','uploads','final_tex_sha256','final_pdf_sha256','statement_scope'}
def require_manifest(manifest,values,source):
 need(isinstance(manifest,dict)and set(manifest)==MANIFEST_FIELDS,'CLOSED_NIGHTLY_MANIFEST')
 need(manifest['standard']==scoped.STANDARD and manifest['scope']==scoped.REVIEW_SCOPE and manifest['run_id']==values['run'],'EXACT_NIGHTLY_SCOPE_CONTRACT')
 need(manifest['certificate']==source['certificate'],'EXACT_SELECTED_CERTIFICATE')
 uploads=manifest['uploads'];need(isinstance(uploads,list)and all(isinstance(v,dict)and set(v)=={'filename','sha256'}and isinstance(v['filename'],str)and re.fullmatch('[0-9a-f]{64}',str(v['sha256']))for v in uploads),'CLOSED_PUBLIC_UPLOAD_BINDINGS')
 names=[v['filename']for v in uploads];need(len(names)==len(UPLOAD_NAMES)and len(set(names))==len(names)and set(names)==UPLOAD_NAMES,'EXACT_PUBLIC_FILES_NO_EXTRA_CLAIMS')
 for key,name in [('claim_map','SCOPED_CLAIM_MAP.json'),('statement_inventory','SCOPED_STATEMENT_INVENTORY.json'),('foundation_basis','SCOPED_FOUNDATION_BASIS.json')]:
  need(manifest[key]==next(v for v in uploads if v['filename']==name),'REVIEWED_PUBLIC_SCOPE_FILE:'+key)
 need(manifest['candidate']=={'path':values['inspection']['candidate_path'],'sha256':values['inspection']['candidate_sha256']},'EXACT_BOUND_CANDIDATE')
 return manifest

def snapshot_certificate(root,value,run,seen):
 p,b=read(root,value,seen);cert=json.loads(b)
 def visit(value):
  if isinstance(value,dict):
   if'path'in value:
    q=resolve_binding({k:value[k]for k in('path','sha256')},root);read(root,{'path':str(q),'sha256':value['sha256']},seen)
   else:
    for v in value.values():visit(v)
 visit(cert.get('bindings'));inspection=inspect_certificate(p,root)
 need(inspection.get('valid')is True and inspection.get('run_id')==run and inspection.get('sha256')==d.digest(b),'UNCHANGED_CERTIFICATE_CONSUMER')
 need(inspection.get('nonvacuity'),'ISSUER_RUN_LEVEL_NONVACUITY_MISSING');return cert,inspection

def source_values(root,source,seen):
 need(isinstance(source,dict)and set(source)==SOURCE_FIELDS and source['standard']==SOURCE_STANDARD and source['status']=='STAGED_SOURCE_NOT_REVIEW_OR_PUBLICATION_BOUND'and source['certifies']is False,'CLOSED_CURRENT_SOURCE_CONTRACT')
 run=canonical_run(source['run_id']);need(source['source_generator_sha256']==source_sha(),'EXACT_SOURCE_GENERATOR')
 need(isinstance(source['selection_invocation'],str)and len(source['selection_invocation'])>=12,'NAMED_STAGE_INVOCATION')
 cert,inspection=snapshot_certificate(root,source['certificate'],run,seen)
 candidate,b=read(root,{'path':inspection['candidate_path'],'sha256':inspection['candidate_sha256']},seen);candidate_text=b.decode()
 formal=resolve_binding(cert['bindings']['formal_statement'],root);_,b=read(root,{'path':str(formal),'sha256':cert['bindings']['formal_statement']['sha256']},seen);formal_text=b.decode()
 need(scan(candidate).get('static_pass')is True,'UNCHANGED_STATIC_GATE')
 source_paper,original=read(root,source['source_manuscript'],seen);_,oldmetadata=read(root,source['before_metadata'],seen)
 _,prior_cycle_raw=read(root,source['prior_cycle'],seen);prior_cycle=json.loads(prior_cycle_raw)
 need(source['selection_at_utc']and time(source['selection_at_utc'])>=time(cert['issued_at_utc'])and time(source['selection_at_utc'])<=now(),'STAGE_AFTER_CERTIFICATE')
 # A real prior invocation/report, not a caller-supplied pass checklist.
 run_mentions=[r for r in prior_cycle.get('run_flows',[])if isinstance(r,dict)and r.get('id')==run]
 need(prior_cycle.get('local_lean_execution')is False and isinstance(prior_cycle.get('checkpoint'),dict),'ACTUAL_NO_LOCAL_LEAN_CYCLE_CONTRACT')
 read(root,prior_cycle['checkpoint'],seen)
 need(run_mentions or prior_cycle.get('run_id')==run,'REAL_PRIOR_RUN_CYCLE_BINDING')
 prior_at=prior_cycle.get('observed_at_utc')
 need(prior_at is not None and time(prior_at)<time(source['selection_at_utc']),'SEPARATE_LATER_STAGE_INVOCATION')
 pins=source['source_pins'];need(isinstance(pins,list)and pins and len({x.get('name')for x in pins})==len(pins),'COMPLETE_GENERATOR_SOURCE_PINS')
 for row in pins:
  need(isinstance(row,dict)and set(row)=={'name','path','sha256'}and (Path(row['path']).name==row['name'] or row['name']=='archive_'+Path(row['path']).parent.name+'_'+Path(row['path']).name),'EXACT_GENERATOR_SOURCE_PIN');read(root,{k:row[k]for k in('path','sha256')},seen)
 require_names={'nightly_minimal_policy.py','certificate_inspection.py','scoped_release.py','theorem_coverage.py','premise_declaration.py','science_release_stage.py','phase7_audit_policy.py'}
 need(require_names<={x['name']for x in pins},'MEASURED_COMPLETE_NIGHTLY_SCOPE_SOURCES')
 return {'run':run,'certificate':cert,'inspection':inspection,'candidate_text':candidate_text,'formal_text':formal_text,'original':original,'source_paper':source_paper,'before_metadata':json.loads(oldmetadata).get('metadata',json.loads(oldmetadata)),
  'scope':claim_scope(candidate_text,formal_text,inspection,source['selected_theorems'])}

def fresh_target(root,run,certificate,inspection,seen):
 import mirror_parity
 path=Path(root)/'RESEARCH_PIPELINE_v2/corpus_ledger.json';raw=d.read_regular(path);ledger=json.loads(raw)
 need(ledger.get('tree_root')==str(Path(root).resolve()),'CURRENT_CANONICAL_SSOT_ROOT');rows=[r for r in ledger.get('run_entities',[])if r.get('id')==run]
 need(len(rows)==1 and rows[0].get('status')=='CERTIFIED'and rows[0].get('certificate_valid')is True,'CURRENT_PARITY_QUALIFIED_CERTIFIED_RUN')
 row=rows[0];cp=Path(row.get('certificate',''));cp=cp if cp.is_absolute()else Path(root)/cp
 need(cp.resolve(strict=True)==resolve_binding(certificate,root),'CURRENT_CERTIFICATE_SELECTION')
 parity=mirror_parity.run_parity(root,row['path']);need(parity.get('status')=='MATCH'and not parity.get('differences')and not parity.get('errors')and parity==row.get('parity'),'CURRENT_PARITY_ONLY_GATE')
 need(row.get('certified_theorems')==inspection['certified_theorems']and row.get('nonvacuity')==inspection['nonvacuity'],'CURRENT_SSOT_EXACT_EXPORTS')
 # Bind the target semantic projection rather than freeze unrelated scan date.
 seen[str(path)]=d.digest(raw)
 return {k:row.get(k)for k in('id','path','status','certificate_valid','certificate','certified_theorems','nonvacuity','parity')}

def evaluate_note(note,root,compatibility_authority,*,rule=None,preparing=False,review_invocation=None):
 note=Path(note);need(not any(p.is_symlink()for p in(note,*note.parents)),'NOTE_SYMLINK');note=note.resolve(strict=True);root=Path(root).resolve(strict=True);need(note.is_relative_to(root),'CANONICAL_NOTE_ONLY');seen={}
 auth=authority(root,compatibility_authority,seen)
 source_path=note/'NIGHTLY_SCOPE_SOURCE.json';source_raw=d.read_regular(source_path);seen[str(source_path)]=d.digest(source_raw);source=json.loads(source_raw)
 values=source_values(root,source,seen);run=values['run'];manifest_raw=d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json');seen[str(note/'SCOPED_RELEASE_MANIFEST.json')]=d.digest(manifest_raw);manifest=json.loads(manifest_raw);require_manifest(manifest,values,source)
 rule_before=d.read_regular(note/'PHASE7_RULE_EXECUTION.json')if rule is None else None
 if rule is None:rule=json.loads(rule_before)
 need(isinstance(rule,dict)and set(rule)==RULE_FIELDS and rule['standard']==RULE_STANDARD and rule['status']=='CURRENT_MINIMAL_RULES_APPLIED'and rule['certifies']is False and rule['execution_consumer_sha256']==source_sha()and rule['run_id']==run and rule['authority']==compatibility_authority and rule['source_manifest']==binding(source_path),'CLOSED_CURRENT_RULE_RECEIPT')
 need(time(rule['issued_at_utc'])>time(source['selection_at_utc'])and time(rule['issued_at_utc'])<=now(),'LATER_CURRENT_REVIEW_TIME')
 scope=values['scope'];need(manifest['statement_scope']==scope,'EXACT_STATEMENT_HYPOTHESIS_MODEL_SCOPE')
 tex=d.read_regular(note/'paper.tex');pdf=d.read_regular(note/'paper.pdf');seen[str(note/'paper.tex')]=d.digest(tex);seen[str(note/'paper.pdf')]=d.digest(pdf)
 main=validate_exact_body(run,source['foundation_basis'],scope,tex)
 import phase7_audit_policy as policy
 policy.require_pdf_provenance(note,root,tex,pdf,seen)
 original=values['original'];need(d.read_regular(note/'historical/ORIGINAL_paper.tex')==original,'HISTORICAL_SOURCE_BYTES_CHANGED')
 need(d.read_regular(note/'rendered/HISTORICAL_SOURCE.txt')==ascii_render(original.decode()).encode(),'ARCHIVAL_RENDER_CHANGED')
 fullmap={'run_id':run,'all_original_claims_explicitly_uncertified':True,'source_manuscript':source['source_manuscript'],'paragraph_partition':source_partition(original),'all_bytes_accounted_for':True}
 need(json.loads(d.read_regular(note/'WHOLE_PAPER_MAP.json'))==fullmap,'EXHAUSTIVE_ARCHIVAL_MAP')
 from publication_gate import scoped_metadata_proposal
 expected_metadata=scoped_metadata_proposal(values['before_metadata'],{'statement_scope':scope,'foundation_basis':source['foundation_basis']})
 need(json.loads(d.read_regular(note/'metadata.json'))==expected_metadata,'EXACT_METADATA_SCOPE_AND_FIELDS')
 reviews=policy.minimal_claim_reviews(run,values['candidate_text'],scope,manifest['certificate'],values['inspection']);lookup={r['lean_theorem']:r for r in reviews}
 def claim_consumer(**kw):
  need(kw['candidate_text']==values['candidate_text']and kw['formal_text']==values['formal_text'],'CANDIDATE_CHANGED_BEFORE_SCOPE');return deepcopy(lookup[kw['claim']['lean_theorem']])
 def premise_consumer(**kw):
  need(kw['full_inv9'].get('reasons')==['PREMISE_UNDERDECLARED'],'NONARCHIVAL_INV9_FAILURE');need(kw['paper_text'].encode()==tex,'PREMISE_SOURCE_CHANGED')
  return premise_evaluate({'foundation_basis':source['foundation_basis']},{'foundation_basis':source['foundation_basis'],'claims':[{'claim':c['english_claim'],'lean_theorem':c['lean_theorem']}for c in scope]},formal_statement=values['formal_text'],candidate=values['candidate_text'],paper_text=main,theorem_names=[c['lean_theorem']for c in scope],required=True)
 result=scoped.assess(note,root,claim_rule_consumer=claim_consumer,premise_rule_consumer=premise_consumer)
 need(result.get('status')=='DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND','UNCHANGED_SCOPED_CONSUMERS:'+str(result.get('reasons')))
 target=fresh_target(root,run,manifest['certificate'],values['inspection'],seen)
 identity=policy._identity(result,manifest)
 scope_comparison={'current_invocation':rule['scope_comparison'].get('current_invocation')if not preparing else review_invocation,'source_selection_invocation':source['selection_invocation'],'new_historical_audit_row':False,'scope_is_exact_template':True,'hypotheses_and_ambient_context_exact':True,'original_scope_is_all_uncertified':True,'model_identification':'DEFINED_ONLY','optional_depth_or_claim_witness_is_release_gate':False,'authority':auth,'target':target}
 need(isinstance(scope_comparison['current_invocation'],str)and len(scope_comparison['current_invocation'])>=12 and scope_comparison['current_invocation']!=source['selection_invocation'],'SEPARATE_CURRENT_REVIEW_INVOCATION')
 for value in manifest['uploads']:
  p=scoped._local_file(note,value);seen[str(p)]=value['sha256']
 for p in [note/'WHOLE_PAPER_MAP.json',note/'historical/ORIGINAL_paper.tex',note/'rendered/HISTORICAL_SOURCE.txt',note/'rendered/FROZEN_CONTEXT.txt',*[note/c['display_file']['relative_path']for c in scope]]:
  seen[str(p)]=d.sha(p)
 # Every public map and auxiliary file is a deterministic projection. Public
 # archive bytes may contain only the frozen exact original/display artifacts.
 expected_map={'run_id':run,'standard':scoped.STANDARD,'claims':scope,'whole_paper_map':{'filename':'WHOLE_PAPER_MAP.json','sha256':d.sha(note/'WHOLE_PAPER_MAP.json')},'all_original_claims_explicitly_uncertified':True}
 need(json.loads(d.read_regular(note/'SCOPED_CLAIM_MAP.json'))==expected_map,'CLOSED_CLAIM_MAP')
 need(json.loads(d.read_regular(note/'SCOPED_STATEMENT_INVENTORY.json'))=={'run_id':run,'standard':scoped.STANDARD,'declarations':scope,'elaborates_or_verifies_Lean':False},'CLOSED_STATEMENT_INVENTORY')
 expected_basis={'run_id':run,'foundation_basis':source['foundation_basis'],'historical_certificate_unchanged':True}
 need(json.loads(d.read_regular(note/'SCOPED_FOUNDATION_BASIS.json'))==expected_basis,'CLOSED_BASIS')
 archive_members=[('historical/ORIGINAL_paper.tex',original),('rendered/HISTORICAL_SOURCE.txt',ascii_render(original.decode()).encode()),('rendered/FROZEN_CONTEXT.txt',ascii_render(values['formal_text']).encode())]
 for i,c in enumerate(scope,1):archive_members.append((f'rendered/statement-{i:03d}.txt',ascii_render(c['exact_source_signature']).encode()))
 need(d.read_regular(note/'SCOPE_EVIDENCE.zip')==d.archive_bytes(archive_members),'EXACT_CLOSED_SCIENTIFIC_ARCHIVE')
 if not preparing:need(rule['identity']==identity and rule['claim_reviews']==reviews and rule['scope_comparison']==scope_comparison,'FRESH_REVIEW_IDENTITY_AND_LABELS')
 inputs={k:v for k,v in seen.items()if not k.endswith('/corpus_ledger.json')}
 if not preparing:need(rule['inputs']==inputs,'EXACT_CURRENT_RULE_INPUT_COVERAGE')
 finish(seen)
 if rule_before is not None:need(d.read_regular(note/'PHASE7_RULE_EXECUTION.json')==rule_before,'RULE_RECEIPT_CHANGED_BEFORE_RETURN')
 return {'status':'CURRENT_MINIMAL_RULES_APPLIED_NOT_PUBLICATION_BOUND','run_id':run,'identity':identity,'input_bindings':inputs,'scope_comparison':scope_comparison,'certificate':manifest['certificate'],'candidate':manifest['candidate'],'formal_statement':manifest['formal_statement'],'statement_scope':scope,'foundation_basis':source['foundation_basis'],'claim_reviews':reviews,'uploads':manifest['uploads'],'public_metadata':expected_metadata,'metadata_binding':next(v for v in manifest['uploads']if v['filename']=='metadata.json'),'prior_dois':[]}

def prepare_rule_receipt(note,root,authority_binding,*,review_invocation,at_utc=None):
 note=Path(note);source=json.loads(d.read_regular(note/'NIGHTLY_SCOPE_SOURCE.json'));run=canonical_run(source['run_id'])
 r={'standard':RULE_STANDARD,'status':'CURRENT_MINIMAL_RULES_APPLIED','run_id':run,'authority':authority_binding,'source_manifest':binding(note/'NIGHTLY_SCOPE_SOURCE.json'),'issued_at_utc':at_utc or now().isoformat(),'execution_consumer_sha256':source_sha(),'inputs':{},'identity':{},'claim_reviews':[],'scope_comparison':{},'certifies':False}
 actual=evaluate_note(note,root,authority_binding,rule=r,preparing=True,review_invocation=review_invocation)
 r.update(inputs=actual['input_bindings'],identity=actual['identity'],claim_reviews=actual['claim_reviews'],scope_comparison=actual['scope_comparison']);evaluate_note(note,root,authority_binding,rule=r);return r

def prepare_publication_binding(note,root,authority_binding,*,at_utc=None):
 note=Path(note);actual=evaluate_note(note,root,authority_binding);rule=json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'));issued=at_utc or now().isoformat()
 need(time(issued)>=time(rule['issued_at_utc'])and time(issued)<=now(),'PUBLICATION_TIME_AFTER_REVIEW')
 return {'standard':BINDING_STANDARD,'status':'PUBLICATION_BOUND','run_id':actual['run_id'],'authority':authority_binding,'policy_receipt':binding(note/'PHASE7_RULE_EXECUTION.json'),'identity':actual['identity'],'issued_at_utc':issued,'execution_consumer_sha256':source_sha(),'certifies':False}

def require_note_publication_bound(note,root,authority_binding):
 note=Path(note);before=d.read_regular(note/'PUBLICATION_BINDING.json');b=json.loads(before);actual=evaluate_note(note,root,authority_binding);rule=json.loads(d.read_regular(note/'PHASE7_RULE_EXECUTION.json'))
 need(set(b)==BINDING_FIELDS and b['standard']==BINDING_STANDARD and b['status']=='PUBLICATION_BOUND'and b['run_id']==actual['run_id']and b['authority']==authority_binding and b['policy_receipt']==binding(note/'PHASE7_RULE_EXECUTION.json')and b['identity']==actual['identity']and b['execution_consumer_sha256']==source_sha()and b['certifies']is False,'EXACT_NIGHTLY_PUBLICATION_BINDING')
 need(time(rule['issued_at_utc'])<=time(b['issued_at_utc'])<=now(),'PUBLICATION_CHRONOLOGY');need(d.read_regular(note/'PUBLICATION_BINDING.json')==before,'BINDING_RACE')
 return {**actual,'status':'PUBLICATION_BOUND','exact_publication_binding':True,'policy_receipt':binding(note/'PHASE7_RULE_EXECUTION.json'),'publication_binding':binding(note/'PUBLICATION_BINDING.json')}
