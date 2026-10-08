"""Weekly Methods Digest byte packaging and publication guards, not a verifier.

No Lean, certification, credentials, transport mutations, implicit approval or
retry is implemented. Fresh note admission belongs to phase7_audit_policy.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import html
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
from zoneinfo import ZoneInfo

STANDARD='VRS-METHODS-DIGEST-1'
BINDING_STANDARD='VRS-METHODS-DIGEST-PUBLICATION-BINDING-1'
DISCLAIMER='logical validity given the model, not empirical validation of its assumptions'
FIRST_EIGHT=('Run-125','Run-126','Run-128','Run-129','Run-130','Run-131','Run-134','Run-141')
SOURCE_FIELDS=('creators','license','access_right','communities','language','resource_type','upload_type','publication_type')
TIERS={'DEFINITIONAL','ROUTINE','SUBSTANTIVE','UNCLASSIFIED','DEPTH_NOT_ASSESSED'}
TIER_PRINT={'UNCLASSIFIED':'UNCLASSIFIED (probe resource-limited)','DEPTH_NOT_ASSESSED':'depth not yet assessed'}

class DigestHold(ValueError):pass

def raw_json(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(Path(path).read_bytes())
def binding(path):
    p=Path(path);data=read_regular(p);return {'path':str(p.resolve()),'sha256':digest(data),'bytes':len(data)}

def read_regular(path):
    p=Path(path)
    if p.is_symlink()or not p.is_file()or any(x.is_symlink()for x in p.parents):raise DigestHold('regular unsymlinked file required')
    before=p.stat();data=p.read_bytes();after=p.stat()
    if (before.st_ino,before.st_mtime_ns,before.st_size)!=(after.st_ino,after.st_mtime_ns,after.st_size):raise DigestHold('file changed during read')
    return data

def bound_file(root,value):
    if not isinstance(value,dict)or not isinstance(value.get('path'),str)or re.fullmatch('[0-9a-f]{64}',str(value.get('sha256')))is None:raise DigestHold('exact path/hash binding required')
    p=Path(value['path']);p=p if p.is_absolute()else Path(root)/p
    if not p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True)):raise DigestHold('bound input outside canonical root')
    data=read_regular(p)
    if digest(data)!=value['sha256']or 'bytes'in value and value['bytes']!=len(data):raise DigestHold('bound input changed')
    return p.resolve(),data

def immutable(path,data):
    p=Path(path)
    if p.is_symlink()or any(x.is_symlink()for x in p.parents):raise DigestHold('immutable output symlink refused')
    p.parent.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    except FileExistsError:
        if read_regular(p)!=data:raise DigestHold('immutable output differs; no overwrite')
        return
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())

def safe_member(name):
    if (not isinstance(name,str)or not name or '\\'in name or any(ord(c)<32 or ord(c)==127 for c in name)
            or name.startswith('/')or '..'in name.split('/')or any(x in {'','.','..'}for x in name.split('/'))
            or PurePosixPath(name).as_posix()!=name):raise DigestHold('unsafe archive member')
    return name

def archive_bytes(members):
    from io import BytesIO
    pairs=list(members);names=[safe_member(n)for n,_ in pairs]
    if len(set(names))!=len(names)or any(not isinstance(b,bytes)for _,b in pairs):raise DigestHold('duplicate or non-byte archive member')
    out=BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_STORED)as z:
        for name,data in sorted(pairs):
            i=zipfile.ZipInfo(name,(1980,1,1,0,0,0));i.create_system=3;i.external_attr=(stat.S_IFREG|0o600)<<16;i.compress_type=zipfile.ZIP_STORED;z.writestr(i,data)
    return out.getvalue()

def member_inventory(members):return [{'path':n,'sha256':digest(b),'md5':hashlib.md5(b).hexdigest(),'bytes':len(b)}for n,b in sorted(members)]

def require_archive(data,inventory):
    from io import BytesIO
    if not isinstance(inventory,list)or not inventory:raise DigestHold('archive inventory required')
    expected={}
    for row in inventory:
        if not isinstance(row,dict)or set(row)!={'path','sha256','md5','bytes'}:raise DigestHold('closed archive inventory fields required')
        n=safe_member(row['path'])
        if n in expected:raise DigestHold('duplicate declared archive member')
        expected[n]=row
    actual={}
    try:
        with zipfile.ZipFile(BytesIO(data))as z:
            for i in z.infolist():
                n=safe_member(i.filename)
                if n in actual or i.is_dir()or stat.S_IFMT(i.external_attr>>16)!=stat.S_IFREG or i.flag_bits&1:raise DigestHold('duplicate, directory, link or encrypted archive member')
                if n not in expected or i.file_size!=expected[n]['bytes']:raise DigestHold('archive member set/size differs')
                b=z.read(i);actual[n]={'path':n,'sha256':digest(b),'md5':hashlib.md5(b).hexdigest(),'bytes':len(b)}
    except (zipfile.BadZipFile,RuntimeError,KeyError)as exc:raise DigestHold('invalid archive')from exc
    if actual!=expected:raise DigestHold('missing/changed archive members')
    return {'status':'EXACT_ARCHIVE_BYTES_PASS','members':len(actual)}

def current_note_consumer(note_path,root,authority_binding):
    """Default authority seam; no caller's cached PASS substitutes for it."""
    try:policy=importlib.import_module('phase7_audit_policy')
    except ModuleNotFoundError as exc:raise DigestHold('approved phase7_audit_policy consumer not installed')from exc
    return policy.require_note_publication_bound(Path(note_path),Path(root),authority_binding)

def current_authority_consumer(root,authority_binding):
    try:policy=importlib.import_module('phase7_audit_policy')
    except ModuleNotFoundError as exc:raise DigestHold('approved phase7_audit_policy consumer not installed')from exc
    return policy.require_audit_authority(Path(root),authority_binding)

def consume_notes(root,note_specs,authority_binding,*,consume=current_note_consumer,consume_authority=current_authority_consumer):
    root=Path(root).resolve(strict=True);authority_path,authority_bytes=bound_file(root,authority_binding)
    authority=consume_authority(root,authority_binding)
    if not isinstance(authority,dict)or authority.get('status')!='APPROVED_RULE_AUTHORITY':raise DigestHold('actual approved audit authority required')
    if not isinstance(note_specs,list)or not note_specs:raise DigestHold('at least one note required')
    notes=[];members=[('authority/AUDIT_AUTHORITY.json',authority_bytes)];inputs={str(authority_path):digest(authority_bytes)};seen=set()
    for spec in note_specs:
        if not isinstance(spec,dict)or set(spec)!={'run_id','path'}or re.fullmatch('Run-[0-9]{3}',str(spec.get('run_id')))is None or spec['run_id']in seen:raise DigestHold('unique canonical note identity required')
        rid=spec['run_id'];seen.add(rid);p=Path(spec['path']);p=p if p.is_absolute()else root/p
        if not p.resolve(strict=True).is_relative_to(root)or p.is_symlink()or not p.is_dir():raise DigestHold('note outside canonical tree')
        current=consume(p,root,authority_binding)
        if (not isinstance(current,dict)or current.get('status')!='PUBLICATION_BOUND' or current.get('exact_publication_binding')is not True or current.get('run_id')!=rid):raise DigestHold('note has not passed current publication admission: '+rid)
        certificate= current.get('certificate');certpath,certbytes=bound_file(root,certificate)
        if json.loads(certbytes).get('run_id')!=rid:raise DigestHold('foreign certificate run')
        inputs[str(certpath)]=digest(certbytes)
        for key in ('candidate','formal_statement'):
            path,data=bound_file(root,current.get(key));inputs[str(path)]=digest(data)
        if current.get('foundation_basis')not in {'INDEPENDENT','THEOREM','CONDITIONAL_PL_PD'}:raise DigestHold('unknown note basis')
        reviews=current.get('claim_reviews');claims=current.get('statement_scope')
        if not isinstance(reviews,list)or not reviews or not isinstance(claims,list)or not claims:raise DigestHold('exact claim reviews required')
        names=[c.get('lean_theorem')for c in claims];review_names=[c.get('lean_theorem')for c in reviews]
        if any(not isinstance(n,str)or not n for n in names+review_names)or len(set(names))!=len(names)or len(set(review_names))!=len(review_names)or set(names)!=set(review_names):raise DigestHold('claim review set differs')
        table=[]
        for review in reviews:
            semantic=review.get('semantic_tier');nv=review.get('nonvacuity')
            if semantic not in TIERS or not isinstance(nv,dict):raise DigestHold('truthful semantic/nonvacuity labels required')
            if nv.get('tier')=='TIER0':
                if nv.get('status')!='NO_HYPOTHESES'or not isinstance(nv.get('domains'),list)or not nv['domains']or any(not isinstance(d,str)or not d for d in nv['domains']):raise DigestHold('Tier0 nonempty domain rule evidence required')
                label='NO_HYPOTHESES (domain nonempty: '+', '.join(nv['domains'])+')';demonstrated=True
            elif nv.get('tier')=='TIER1':
                demonstrated=nv.get('status')=='CERTIFIED_WITNESS'
                if demonstrated:
                    if not isinstance(nv.get('witness_theorem'),str)or not nv['witness_theorem']:raise DigestHold('Tier1 exact witness theorem required')
                    wp,wb=bound_file(root,nv.get('certificate'));inputs[str(wp)]=digest(wb)
                    label='CERTIFIED_WITNESS: '+nv['witness_theorem']
                elif nv.get('status')=='NOT_DEMONSTRATED':label='certified; nonvacuity not demonstrated'
                else:raise DigestHold('unknown Tier1 witness state')
            else:raise DigestHold('unknown nonvacuity tier')
            table.append({'lean_theorem':review['lean_theorem'],'semantic_tier':semantic,'nonvacuity_label':label,'headline_eligible':demonstrated and semantic!='DEFINITIONAL'})
        uploads=current.get('uploads');declared={}
        if not isinstance(uploads,list)or not uploads:raise DigestHold('exact note upload inventory required')
        for value in uploads:
            if not isinstance(value,dict)or set(value)!={'filename','sha256'}:raise DigestHold('closed note file binding required')
            name=safe_member(value['filename'])
            if '/'in name or name in declared:raise DigestHold('unique note upload basename required')
            filedata=read_regular(p/name)
            if digest(filedata)!=value['sha256']:raise DigestHold('note upload changed')
            declared[name]=value;inputs[str((p/name).resolve())]=digest(filedata);members.append((f'notes/{rid}/{name}',filedata))
        if not {'paper.tex','paper.pdf'}<=set(declared)or any(current[k]['sha256'] not in {v['sha256']for v in uploads}for k in ('certificate','candidate','formal_statement')):raise DigestHold('main manuscript/proof/certificate missing from archived uploads')
        for filename in ('SCOPED_RELEASE_MANIFEST.json','PUBLICATION_BINDING.json'):
            data=read_regular(p/filename);inputs[str((p/filename).resolve())]=digest(data)
            if filename not in declared:members.append((f'notes/{rid}/{filename}',data))
        policy=current.get('policy_receipt');policy_path,policybytes=bound_file(root,policy)
        if policy_path.parent!=p.resolve():raise DigestHold('note policy receipt must belong to this exact package')
        inputs[str(policy_path)]=digest(policybytes)
        if policy_path.name not in declared and policy_path.name not in {'SCOPED_RELEASE_MANIFEST.json','PUBLICATION_BINDING.json'}:members.append((f'notes/{rid}/{policy_path.name}',policybytes))
        metadata=current.get('public_metadata');metadata_binding=current.get('metadata_binding')
        if not isinstance(metadata,dict)or not isinstance(metadata_binding,dict)or metadata_binding not in uploads:raise DigestHold('unreviewed note metadata')
        raw=json.loads(read_regular(p/metadata_binding['filename']));raw=raw.get('metadata',raw)
        if raw!=metadata:raise DigestHold('note public metadata differs from reviewed bytes')
        notes.append({'run_id':rid,'path':str(p.resolve()),'certificate':certificate,'candidate':current['candidate'],'formal_statement':current['formal_statement'],'foundation_basis':current['foundation_basis'],'statement_scope':claims,'claim_table':table,'section':'MAIN_NOTES'if any(c['headline_eligible']for c in table)else'DEFINITIONAL_OR_NONVACUITY_PENDING_APPENDIX','metadata_binding':metadata_binding,'policy_receipt':policy,'publication_binding':binding(p/'PUBLICATION_BINDING.json'),'uploads':uploads,'prior_dois':current.get('prior_dois',[])})
    for name,h in inputs.items():
        if sha(name)!=h:raise DigestHold('note/authority inputs changed during consumption')
    return {'notes':sorted(notes,key=lambda n:n['run_id']),'members':members,'input_bindings':inputs,'authority':authority_binding}

def week_title(week):
    if not isinstance(week,str)or re.fullmatch('[0-9]{4}-W(?:0[1-9]|[1-4][0-9]|5[0-3])',week)is None:raise DigestHold('canonical ISO release week required')
    return 'Viridis Methods Digest — '+week

def metadata_proposal(source,week,notes,publication_date,*,existing_title=None):
    if not isinstance(source,dict)or any(k not in source for k in ('creators','license')):raise DigestHold('approved creator/rights source required')
    publication_day=dt.date.fromisoformat(publication_date);year,number,_=publication_day.isocalendar()
    if week!=f'{year}-W{number:02d}':raise DigestHold('publication date outside exact release week')
    title=week_title(week)
    if existing_title is not None and existing_title!=title:raise DigestHold('existing weekly title differs from discovered exact week title')
    meta={k:source[k]for k in SOURCE_FIELDS if k in source}
    sections=[]
    for section in ('MAIN_NOTES','DEFINITIONAL_OR_NONVACUITY_PENDING_APPENDIX'):
        rows=[]
        for note in notes:
            if note['section']!=section:continue
            claims='; '.join(html.escape(c['lean_theorem']+' ['+TIER_PRINT.get(c['semantic_tier'],c['semantic_tier'])+'; '+c['nonvacuity_label']+']',quote=False)for c in note['claim_table'])
            rows.append('<li>'+note['run_id']+' — foundation basis '+note['foundation_basis']+': '+claims+'</li>')
        if rows:sections.append('<h2>'+('Reviewed scoped notes'if section=='MAIN_NOTES'else'Definitional / nonvacuity-pending appendix')+'</h2><ul>'+''.join(rows)+'</ul>')
    description='<p><strong>'+html.escape(title,quote=False)+'</strong></p><p>'+DISCLAIMER+'</p>'+''.join(sections)+'<p>Every archived historical claim outside the listed exact note scopes is UNCERTIFIED. This digest creates no aggregate theorem or empirical validation. Appendix results do not count toward certified-result headlines.</p>'
    meta.update(title=title,description=description,publication_date=publication_date,keywords=['Viridis Methods Digest',week,'scoped mathematical results'])
    dois=sorted({doi for n in notes for doi in n['prior_dois']})
    if any(re.fullmatch('10[.]5281/zenodo[.][1-9][0-9]*',str(d))is None for d in dois):raise DigestHold('foreign/malformed prior DOI')
    if dois:meta['related_identifiers']=[{'identifier':d,'relation':'isSupplementTo','scheme':'doi'}for d in dois]
    return meta

def wrapper_tex(week,notes):
    def escape(value):
        text=''.join(c if ord(c)<128 else '[U+%04X]'%ord(c)for c in str(value))
        return ''.join({'\\':r'\textbackslash{}','{':r'\{','}':r'\}','_':r'\_','%':r'\%','&':r'\&','#':r'\#','$':r'\$','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}.get(c,c)for c in text)
    lines=[r'\documentclass[11pt]{article}',r'\usepackage[margin=1in]{geometry}',r'\usepackage[T1]{fontenc}',r'\begin{document}',r'\section*{'+escape(week_title(week))+'}',escape(DISCLAIMER)+'.',r'\par Each note retains its own unchanged Comparator certificate, exact scope and publication binding. Historical remainders are UNCERTIFIED. No aggregate theorem is claimed.']
    for section in ('MAIN_NOTES','DEFINITIONAL_OR_NONVACUITY_PENDING_APPENDIX'):
        lines.append(r'\section*{'+('Reviewed scoped notes'if section=='MAIN_NOTES'else'Definitional / nonvacuity-pending appendix')+'}')
        for note in notes:
            if note['section']!=section:continue
            lines.extend([r'\subsection*{'+escape(note['run_id'])+'}',escape('Foundation basis: '+note['foundation_basis'])+'.',r'\begin{itemize}'])
            for c in note['claim_table']:lines.append(r'\item '+escape(c['lean_theorem']+' | '+TIER_PRINT.get(c['semantic_tier'],c['semantic_tier'])+' | '+c['nonvacuity_label']+' | '+('headline eligible'if c['headline_eligible']else'appendix/non-headline')))
            lines.append(r'\end{itemize}')
    lines.extend([r'\section*{Archive inventory}',r'\noindent The byte-bound archive contains each note manuscript, Lean candidate, frozen statement, certificate, claim map, basis, policy evidence and publication-binding receipt. Use DIGEST\_MANIFEST.json for exact checksums.',r'\end{document}']);return ('\n'.join(lines)+'\n').encode()

def _output(root,out):
    root=Path(root).resolve(strict=True);out=Path(out)
    if out.is_symlink()or any(p.is_symlink()for p in out.parents):raise DigestHold('digest output symlink')
    out=out.resolve()
    allowed=out.is_relative_to(root/'RESEARCH_PIPELINE_v2/science_release_queue/digests')or (out.is_relative_to(Path('/private/tmp'))and not out.is_relative_to(root))
    if not allowed:raise DigestHold('new digest staging destination required')
    if out.exists():raise DigestHold('immutable digest attempt already exists')
    return out

def prepare(root,out,week,note_specs,authority_binding,source_metadata_binding,publication_date,*,consume=current_note_consumer,consume_authority=current_authority_consumer,render=None,existing_title=None):
    """Freeze a new aggregate proposal; no automatic review or publication."""
    root=Path(root).resolve(strict=True);out=_output(root,out)
    consumed=consume_notes(root,note_specs,authority_binding,consume=consume,consume_authority=consume_authority)
    source_path,source_bytes=bound_file(root,source_metadata_binding);source=json.loads(source_bytes);source=source.get('metadata',source)
    metadata=metadata_proposal(source,week,consumed['notes'],publication_date,existing_title=existing_title)
    inputs={**consumed['input_bindings'],str(source_path):digest(source_bytes)}
    out.mkdir(parents=True,exist_ok=False)
    immutable(out/'paper.tex',wrapper_tex(week,consumed['notes']));immutable(out/'metadata.json',raw_json(metadata))
    if render is None:raise DigestHold('PDF rendering adapter required; immutable draft retained')
    pdf=render(out/'paper.tex')
    if not isinstance(pdf,bytes)or not pdf.startswith(b'%PDF-'):raise DigestHold('actual wrapper PDF bytes required')
    immutable(out/'paper.pdf',pdf)
    arc=archive_bytes(consumed['members']);immutable(out/'METHODS_NOTES.zip',arc);inventory=member_inventory(consumed['members']);require_archive(arc,inventory)
    upload_names=('paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip')
    manifest={'standard':STANDARD,'release_week':week,'status':'ASSEMBLED_NOT_PUBLICATION_BOUND','authority':authority_binding,'source_metadata':source_metadata_binding,'notes':consumed['notes'],'archive_members':inventory,'input_bindings':inputs,'uploads':[{'filename':n,'sha256':sha(out/n),'md5':hashlib.md5(read_regular(out/n)).hexdigest(),'bytes':(out/n).stat().st_size}for n in upload_names],'public_metadata':metadata,'review_pdf_is_publication':False,'certifies':False,'local_lean_execution':False,'zenodo_writes':0}
    for path,h in inputs.items():
        if sha(path)!=h:raise DigestHold('inputs changed during aggregate assembly')
    immutable(out/'DIGEST_MANIFEST.json',raw_json(manifest));return manifest

def require_current(package,root,*,consume=current_note_consumer,consume_authority=current_authority_consumer):
    package=Path(package);root=Path(root).resolve(strict=True);manifest=json.loads(read_regular(package/'DIGEST_MANIFEST.json'))
    fields={'standard','release_week','status','authority','source_metadata','notes','archive_members','input_bindings','uploads','public_metadata','review_pdf_is_publication','certifies','local_lean_execution','zenodo_writes'}
    if set(manifest)!=fields or manifest.get('standard')!=STANDARD or manifest.get('status')!='ASSEMBLED_NOT_PUBLICATION_BOUND' or any(manifest.get(k)is not False for k in ('review_pdf_is_publication','certifies','local_lean_execution')) or manifest.get('zenodo_writes')!=0:raise DigestHold('actual closed digest manifest required')
    week_title(manifest.get('release_week'))
    current=consume_notes(root,[{'run_id':n['run_id'],'path':n['path']}for n in manifest['notes']],manifest['authority'],consume=consume,consume_authority=consume_authority)
    source_path,source_bytes=bound_file(root,manifest['source_metadata'])
    current_inputs={**current['input_bindings'],str(source_path):digest(source_bytes)}
    if current['notes']!=manifest['notes']or current_inputs!=manifest['input_bindings']:raise DigestHold('aggregate current note/authority bindings changed')
    for path,h in manifest['input_bindings'].items():
        if sha(path)!=h:raise DigestHold('aggregate input changed')
    expected={'paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip'}
    if {u['filename']for u in manifest['uploads']}!=expected or len(manifest['uploads'])!=len(expected):raise DigestHold('exact aggregate upload set required')
    for u in manifest['uploads']:
        b=read_regular(package/u['filename'])
        if digest(b)!=u['sha256']or hashlib.md5(b).hexdigest()!=u['md5']or len(b)!=u['bytes']:raise DigestHold('aggregate main file changed')
    source=json.loads(source_bytes);source=source.get('metadata',source)
    proposed=metadata_proposal(source,manifest['release_week'],current['notes'],manifest['public_metadata']['publication_date'])
    if json.loads(read_regular(package/'metadata.json'))!=manifest['public_metadata'] or proposed!=manifest['public_metadata']:raise DigestHold('aggregate metadata differs from actual deterministic approved scope')
    if read_regular(package/'paper.tex')!=wrapper_tex(manifest['release_week'],current['notes']):raise DigestHold('aggregate wrapper differs from actual deterministic approved scope')
    require_archive(read_regular(package/'METHODS_NOTES.zip'),manifest['archive_members'])
    if member_inventory(current['members'])!=manifest['archive_members']:raise DigestHold('aggregate archive differs from actual notes')
    return manifest

def publication_binding(package,root,assembled_at_utc=None,*,consume=current_note_consumer,consume_authority=current_authority_consumer):
    """Mechanical bind after actual note admission; this is not a new review."""
    manifest=require_current(package,root,consume=consume,consume_authority=consume_authority)
    prior=Path(package)/'PUBLICATION_BINDING.json'
    if prior.exists():return require_publication_bound(package,root,consume=consume,consume_authority=consume_authority)[1]
    assembled_at_utc=assembled_at_utc or dt.datetime.now(dt.timezone.utc).isoformat()
    t=dt.datetime.fromisoformat(assembled_at_utc.replace('Z','+00:00'))
    if t.tzinfo is None:raise DigestHold('assembly time must be timezone-aware')
    value={'standard':BINDING_STANDARD,'status':'PUBLICATION_BOUND','manifest':binding(Path(package)/'DIGEST_MANIFEST.json'),'authority':manifest['authority'],'note_publication_bindings':[n['publication_binding']for n in manifest['notes']],'uploads':manifest['uploads'],'assembly_at_utc':assembled_at_utc,'review_provenance':'Approved GAME_PLAN Claude audit v002 rule execution; no new Claude identity, model or review timestamp claimed','certifies':False,'acceptance_diagnostics_are_evidence':False}
    immutable(Path(package)/'PUBLICATION_BINDING.json',raw_json(value));return value

def require_publication_bound(package,root,*,consume=current_note_consumer,consume_authority=current_authority_consumer):
    m=require_current(package,root,consume=consume,consume_authority=consume_authority);b=json.loads(read_regular(Path(package)/'PUBLICATION_BINDING.json'))
    fields={'standard','status','manifest','authority','note_publication_bindings','uploads','assembly_at_utc','review_provenance','certifies','acceptance_diagnostics_are_evidence'}
    if set(b)!=fields or b.get('certifies')is not False or b.get('acceptance_diagnostics_are_evidence')is not False or b.get('review_provenance')!='Approved GAME_PLAN Claude audit v002 rule execution; no new Claude identity, model or review timestamp claimed' or b.get('standard')!=BINDING_STANDARD or b.get('status')!='PUBLICATION_BOUND' or b.get('manifest')!=binding(Path(package)/'DIGEST_MANIFEST.json')or b.get('authority')!=m['authority']or b.get('uploads')!=m['uploads']or b.get('note_publication_bindings')!=[n['publication_binding']for n in m['notes']]:raise DigestHold('publish-time aggregate binding missing or stale')
    return m,b

def discover_weekly_record(records,week,*,complete=False):
    """Consume full preserving account/SSOT discovery evidence, never create."""
    title=week_title(week)
    if complete is not True or not isinstance(records,list):raise DigestHold('complete fresh weekly-record discovery required')
    matches=[r for r in records if isinstance(r,dict)and r.get('metadata',{}).get('title')==title]
    if not matches:return {'status':'NO_EXISTING_WEEKLY_RECORD','release_week':week,'title':title}
    concepts={str(r.get('conceptrecid',r.get('parent',{}).get('id','')))for r in matches}
    if len(concepts)!=1 or ''in concepts:raise DigestHold('duplicate/unknown weekly concept chains')
    latest=[r for r in matches if r.get('versions',{}).get('is_latest')is True or any(v.get('is_last')is True for v in r.get('metadata',{}).get('relations',{}).get('version',[]))]
    if len(latest)!=1:raise DigestHold('unique own latest weekly version readback required')
    return {'status':'EXISTING_WEEKLY_RECORD','release_week':week,'title':title,'record_id':str(latest[0]['id']),'concept_id':next(iter(concepts)),'doi':latest[0]['doi']}

def require_write_budget(events,method,at_utc,*,complete=False):
    """Count every mutation attempt, including failed/uncertain attempts."""
    if complete is not True or not isinstance(events,list)or method not in {'POST','PUT','DELETE'}:raise DigestHold('complete mutation journal required')
    now=dt.datetime.fromisoformat(at_utc.replace('Z','+00:00'))
    if now.tzinfo is None:raise DigestHold('write time timezone required')
    day=now.astimezone(ZoneInfo('America/New_York')).date();seen=set();count=0
    for event in events:
        if not isinstance(event,dict)or set(event)!={'operation_id','method','host','at_utc','status','receipt_binding'}or event['method']not in {'POST','PUT','DELETE'}or event['host']!='zenodo.org'or event['operation_id']in seen:raise DigestHold('invalid or duplicate mutation journal row')
        seen.add(event['operation_id']);t=dt.datetime.fromisoformat(event['at_utc'].replace('Z','+00:00'))
        if t.tzinfo is None or t>now:raise DigestHold('unanchored mutation time')
        if not isinstance(event['receipt_binding'],dict)or re.fullmatch('[0-9a-f]{64}',str(event['receipt_binding'].get('sha256')))is None:raise DigestHold('mutation receipt hash required')
        if t.astimezone(ZoneInfo('America/New_York')).date()==day:count+=1
    if count>=10:raise DigestHold('daily 10-write cap reached; no write/retry')
    return {'status':'WRITE_SLOT_AVAILABLE','date_new_york':str(day),'used':count,'remaining_including_next':10-count}

def prewrite(package,root,method,at_utc,events,*,complete_journal=False,budget_consumer=None,consume=current_note_consumer,consume_authority=current_authority_consumer):
    require_publication_bound(package,root,consume=consume,consume_authority=consume_authority)
    computed=require_write_budget(events,method,at_utc,complete=complete_journal)
    # A caller's complete=True and empty list cannot authorize a production
    # write. The preserving executor must freshly consume its full immutable
    # mutation journal under the approved policy before reserving this slot.
    if budget_consumer is None:
        try:policy=importlib.import_module('phase7_audit_policy')
        except ModuleNotFoundError as exc:raise DigestHold('actual preserving mutation-budget consumer required')from exc
        budget_consumer=policy.require_write_budget
    actual=budget_consumer(Path(root),method,at_utc)
    if actual!=computed:raise DigestHold('actual preserving mutation journal differs from supplied count')
    return computed

def strict_readback(package,root,record,own_publish_receipt,download,*,expected_record,metadata_consumer=None,consume=current_note_consumer,consume_authority=current_authority_consumer):
    """Own public GET + exact downloaded bytes; metadata/PIDs reuse consumers."""
    m,b=require_publication_bound(package,root,consume=consume,consume_authority=consume_authority)
    rid=str(expected_record.get('id'));doi=expected_record.get('doi')
    if (re.fullmatch('[1-9][0-9]*',rid)is None or record.get('id')!=expected_record.get('id')or record.get('doi')!=doi or own_publish_receipt.get('record_id')!=rid or own_publish_receipt.get('doi')!=doi or own_publish_receipt.get('method')!='POST'or own_publish_receipt.get('url')!='https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish' or own_publish_receipt.get('status')!='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'):raise DigestHold('own-record publish/readback identity mismatch')
    expected_metadata=expected_record.get('metadata',{})
    if not isinstance(expected_metadata,dict)or any(expected_metadata.get(k)!=v for k,v in m['public_metadata'].items()):raise DigestHold('expected public metadata differs from byte-bound aggregate payload')
    if metadata_consumer is None:
        from publication_preservation import require_public_metadata
        require_public_metadata(record.get('metadata',{}),expected_record.get('metadata',{}))
        if record.get('pids')!=expected_record.get('pids'):raise DigestHold('public PID mismatch')
    else:metadata_consumer(record,expected_record,own_publish_receipt)
    uploads=[*m['uploads'],{'filename':'DIGEST_MANIFEST.json','sha256':sha(Path(package)/'DIGEST_MANIFEST.json'),'md5':hashlib.md5(read_regular(Path(package)/'DIGEST_MANIFEST.json')).hexdigest(),'bytes':(Path(package)/'DIGEST_MANIFEST.json').stat().st_size},{'filename':'PUBLICATION_BINDING.json','sha256':sha(Path(package)/'PUBLICATION_BINDING.json'),'md5':hashlib.md5(read_regular(Path(package)/'PUBLICATION_BINDING.json')).hexdigest(),'bytes':(Path(package)/'PUBLICATION_BINDING.json').stat().st_size}]
    expected={v['filename']:v for v in uploads};public=record.get('files')
    if not isinstance(public,list)or any(not isinstance(f,dict)for f in public):raise DigestHold('own public file inventory required')
    names=[f.get('key')for f in public]
    if len(set(names))!=len(names)or set(names)!=set(expected):raise DigestHold('public main/evidence filename set differs')
    for f in public:
        u=expected[f['key']];data=download(f,rid)
        if not isinstance(data,bytes)or digest(data)!=u['sha256']or hashlib.md5(data).hexdigest()!=u['md5']or len(data)!=u['bytes']or f.get('checksum')!='md5:'+u['md5']or f.get('size')!=u['bytes']:raise DigestHold('public main/evidence bytes differ')
        if f['key']=='METHODS_NOTES.zip':require_archive(data,m['archive_members'])
    return {'status':'STRICT_OWN_PUBLIC_READBACK_PASS','record_id':rid,'doi':doi,'files':len(public),'notes':[n['run_id']for n in m['notes']],'binding_sha256':sha(Path(package)/'PUBLICATION_BINDING.json'),'certifies':False}
