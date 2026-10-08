"""Root-only immutable source/PDF/admission path. No publishing/SSOT operation."""
from pathlib import Path
import datetime as dt,hashlib,json,os
import nightly_minimal_policy as policy
import methods_digest as d

def exclusive(path,data):
 p=Path(path);policy.need(not any(q.is_symlink()for q in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb')as out:out.write(data);out.flush();os.fsync(out.fileno())
def obj(path,v):exclusive(path,d.raw_json(v))

def prepare_source(root,out,source,*,render):
 """Generate exact neutral scoped prose from frozen source, not an old56 row.

 render is the exact root-reviewed already cached renderer. It must write its
 genuine closed render-observation, which admission independently consumes.
 No caller-supplied PDF pass marker or witness/probe status can clear a gate.
 """
 root=Path(root).resolve(strict=True);out=Path(out);seen={}
 policy.need(out.is_absolute()and(out.resolve().is_relative_to(root/'RESEARCH_PIPELINE_v2/science_release_queue')or(out.resolve().is_relative_to(Path('/private/tmp'))and not out.resolve().is_relative_to(root)))and not out.exists(),'NEW_IMMUTABLE_SCOPE_ATTEMPT')
 values=policy.source_values(root,source,seen);run=values['run'];scope=values['scope'];basis=source['foundation_basis'];original=values['original'];before=values['before_metadata']
 out.mkdir(parents=True,exist_ok=False)
 obj(out/'NIGHTLY_SCOPE_SOURCE.json',source)
 files=[('paper.tex',policy.expected_paper(run,basis,scope)),('VERIFICATION_CANDIDATE.lean',values['candidate_text'].encode()),('VERIFICATION_STATEMENT.lean',values['formal_text'].encode()),('LEAN_ZERO_SORRY_CERTIFICATE.json',d.read_regular(policy.resolve_binding(source['certificate'],root)))]
 evidence=[('historical/ORIGINAL_paper.tex',original),('rendered/HISTORICAL_SOURCE.txt',policy.ascii_render(original.decode()).encode()),('rendered/FROZEN_CONTEXT.txt',policy.ascii_render(values['formal_text']).encode())]
 for i,c in enumerate(scope,1):evidence.append((f'rendered/statement-{i:03d}.txt',policy.ascii_render(c['exact_source_signature']).encode()))
 for name,b in files+evidence:exclusive(out/name,b)
 fullmap={'run_id':run,'all_original_claims_explicitly_uncertified':True,'source_manuscript':source['source_manuscript'],'paragraph_partition':policy.source_partition(original),'all_bytes_accounted_for':True};obj(out/'WHOLE_PAPER_MAP.json',fullmap)
 obj(out/'SCOPED_CLAIM_MAP.json',{'run_id':run,'standard':policy.scoped.STANDARD,'claims':scope,'whole_paper_map':{'filename':'WHOLE_PAPER_MAP.json','sha256':d.sha(out/'WHOLE_PAPER_MAP.json')},'all_original_claims_explicitly_uncertified':True})
 obj(out/'SCOPED_STATEMENT_INVENTORY.json',{'run_id':run,'standard':policy.scoped.STANDARD,'declarations':scope,'elaborates_or_verifies_Lean':False})
 obj(out/'SCOPED_FOUNDATION_BASIS.json',{'run_id':run,'foundation_basis':basis,'historical_certificate_unchanged':True})
 from publication_gate import scoped_metadata_proposal
 metadata=scoped_metadata_proposal(before,{'statement_scope':scope,'foundation_basis':basis});obj(out/'metadata.json',metadata)
 exclusive(out/'SCOPE_EVIDENCE.zip',d.archive_bytes(evidence))
 pdf=render(out/'paper.tex',root=root);policy.need(isinstance(pdf,bytes)and pdf.startswith(b'%PDF-'),'GENUINE_RENDER_PDF');exclusive(out/'paper.pdf',pdf)
 local=lambda n:{'filename':n,'sha256':d.sha(out/n)}
 names=policy.UPLOAD_NAMES
 manifest={'standard':policy.scoped.STANDARD,'scope':policy.scoped.REVIEW_SCOPE,'run_id':run,'certificate':source['certificate'],'candidate':{'path':values['inspection']['candidate_path'],'sha256':values['inspection']['candidate_sha256']},'formal_statement':{'path':str(policy.resolve_binding(values['certificate']['bindings']['formal_statement'],root)),'sha256':values['certificate']['bindings']['formal_statement']['sha256']},'claim_map':local('SCOPED_CLAIM_MAP.json'),'statement_inventory':local('SCOPED_STATEMENT_INVENTORY.json'),'foundation_basis':local('SCOPED_FOUNDATION_BASIS.json'),'uploads':[local(n)for n in sorted(names)],'final_tex_sha256':d.sha(out/'paper.tex'),'final_pdf_sha256':d.sha(out/'paper.pdf'),'statement_scope':scope}
 obj(out/'SCOPED_RELEASE_MANIFEST.json',manifest);policy.finish(seen)
 return {'status':'EXACT_NIGHTLY_SCOPE_SOURCE_AND_PDF_STAGED_NOT_ADMITTED','run_id':run,'note_path':str(out),'manifest':policy.binding(out/'SCOPED_RELEASE_MANIFEST.json'),'selection_invocation':source['selection_invocation'],'certifies':False,'zenodo_writes':0,'ssot_writes':0}

def admit(root,note,authority,*,review_invocation):
 """Separate later invocation issues genuine policy + publish-time PB locally."""
 note=Path(note);policy.need(not(note/'PHASE7_RULE_EXECUTION.json').exists()and not(note/'PUBLICATION_BINDING.json').exists(),'NEW_IMMUTABLE_REVIEW_AND_BINDING')
 rule=policy.prepare_rule_receipt(note,root,authority,review_invocation=review_invocation);obj(note/'PHASE7_RULE_EXECUTION.json',rule)
 pb=policy.prepare_publication_binding(note,root,authority);obj(note/'PUBLICATION_BINDING.json',pb)
 # This final admission is the ordinary default-reader path, not a selected
 # direct consumer returning a convenient PASS dictionary.
 import phase7_audit_policy as default
 current=default.require_note_publication_bound(note,root,authority)
 policy.need(current['status']=='PUBLICATION_BOUND'and current['exact_publication_binding']is True,'ACTUAL_DEFAULT_READER_ADMISSION')
 return {'status':'ACTUAL_DEFAULT_NIGHTLY_MINIMAL_SCOPE_BINDING_PASS','run_id':current['run_id'],'policy_receipt':current['policy_receipt'],'publication_binding':current['publication_binding'],'certifies':False,'zenodo_writes':0,'ssot_writes':0}
if __name__=='__main__':raise SystemExit('HOLD: explicit root call inside the measured current source session is required')
