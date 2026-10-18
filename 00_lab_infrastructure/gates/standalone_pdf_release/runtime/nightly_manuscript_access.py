"""Faithful PDF access derived from an unchanged, freshly admitted nightly note.

This format authorizes no science or publication. Its predecessor is consumed
through the actual frozen default reader on every call. Private source modules
are freshly compiled from closed canonical byte pins; ambient Python modules,
bytecode and saved PASS dictionaries are never admission inputs.
"""
from __future__ import annotations
import builtins
from contextlib import contextmanager
from copy import deepcopy
import datetime as dt
from io import BytesIO
import json
import html
import os
import signal
import select
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import re
from pathlib import Path
import sys
import types
import unicodedata
import uuid
import zipfile
import methods_digest_v2 as d

STANDARD = 'VRS-NIGHTLY-ARCHIVAL-MANUSCRIPT-ACCESS-1'
BINDING_STANDARD = 'VRS-NIGHTLY-ARCHIVAL-MANUSCRIPT-ACCESS-BINDING-1'
RENDER_STANDARD = 'VRS-EXACT-HISTORICAL-MANUSCRIPT-RENDER-1'
GATES = 'RESEARCH_PIPELINE_v2/verification_coverage_gates'
# These two immutable helpers are already admitted at these original origins
# by the historical 130-source scope. No relocated copy is an input.
_HELPER_ORIGINS = {
    'nightly_release_checkpoint.py': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/nightly_release_checkpoint.py',
    'prepare_nightly_note.py': 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001/prepare_nightly_note.py',
}
HISTORICAL_TEX = 'historical/ORIGINAL_paper.tex'
HISTORICAL_PDF = 'historical/ORIGINAL_paper.pdf'
TOP_PDF = 'Historical-Paper.pdf'
MANIFEST_FIELDS = {'standard','run_id','predecessor','authority','execution_sources',
    'uploads','archive_members','manuscripts','historical_render','certifies',
    'publication_authorized','ssot_writes','zenodo_writes'}
PB_FIELDS = {'standard','status','run_id','manifest','predecessor_binding',
    'authority','issued_at_utc','certifies','publication_authorized'}
# Exact immutable historical code bytes. Only the current access format changes.
_FROZEN_HASHES = {'certificate_inspection.py': 'a7e3d2fcd167865b129529fce7e3599acf045a190cbc2107e87f39b0a3623ec8',
 'certificate_selection.py': '9f243a1025498ca03e22b0c94a711165d21554037ea434abe6cb9720ff8fbd07',
 'claim_binding.py': 'd0bac6e9739c41c5cc40cc57b932f1d15ac7a86f457a0ee3fecdc0ef7a2b7240',
 'closeout_streak.py': 'd447b86beb36841930f6472366be8dc69db8c4e85cc8cd21664ac32b2e2c22b2',
 'completion_links.py': 'c295a80b8602860c4a1acfaf962c01af2188c85e517c3a4eec761b478229c505',
 'corpus_ledger.py': '497aa58f686c48389ef5b4d62e00fa2621cdf45eff45ace4d8e79202076e94cf',
 'digest_metadata.py': 'e5c5cd3b7ca80d9c31c4adcafacc9bd357e440965a25baed291c99f70a4781fe',
 'digest_public_state.py': 'b746fbbd4acc393799c75eb49bcc432e6c130e2b0858d8ed16082c8724127fe0',
 'digest_public_state_legacy_b5545.py': 'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38',
 'digest_successor_state.py': '11a173b3781301cb6070ebc5d37763f5aca8558972351abfb2cf546c73369567',
 'digest_weekly_state.py': '96b3aa1eca1e2f6fa42563ea912338ae839d5d9786ee7eb777f81a12c988387c',
 'doi_audit.py': '72a78e3b305fdf78114414e6dce0a13594d09628f5ea06e04b098dbd49f6a743',
 'doi_triage.py': '86d9d1e65286ff13038dc75ab3150a616d5acc7515b1ee4fcf04644f1db171ca',
 'first_digest_state.py': 'cbd6aa9034e8d2e775c3b2f3226c9c41dbb39ccce1d7a59150ca52414ca8dfb2',
 'inv9_dependency_scope.py': '1b47d3ced31f7f18ffd33e69f1e0855c3935e02b1fb29a9ba3a86ac2e098c3b3',
 'inv9_title_basis.py': '5c9981fe2536a6cde3c8a1d2e7cdc9684c1369aeb145be4fda635c8af8dfec81',
 'manuscript_structure.py': '3177a850997c760ca65e23416116fa4920cf35f238753f63fa63d3a7e4b300a9',
 'methods_digest.py': '5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5',
 'methods_digest_registration.py': 'e97c6e906b6b2feeb348fc60dc0f4c22eac86cb23eac6f29afbf33dfe9df3cb5',
 'methods_digest_registration_legacy_0fc739.py': '0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9',
 'methods_digest_registration_legacy_21b813.py': '21b813c527566c12a06b15426c4a49370fd1e5ccbdcf9ca441bf5d305011d21c',
 'mirror_parity.py': '77033a9303519bc47493f4efc2b0872fff805baa9aa35aa61e34467f66336e80',
 'nightly_coverage.py': 'fd9a4fe406445f3181391ca83f462c4889fb3392c4c93d5ac0d54838c223484f',
 'nightly_minimal_policy.py': '49cd0e2b4fd30670fcd83d983554afe7e1440dda0d8ab2cecee5fb91a871d42c',
 'nightly_publication_intake.py': '9f3aa3c7f438f22b1c07242e9c548f6a9917ecbc2999ffe817256a602f472ba8',
 'nightly_release_checkpoint.py': '35c2d8ba078aec91100a3b7cb987cadc7e3d172405eeab48fc08ced232ba2c9f',
 'nonvacuity_tier0.py': '2c8400e23696d5cf112a0644ff33187de74a82ec5c65eaf4545d5796f439e526',
 'own_record_comparison.py': '55e9e4a070cd6d3ac0f0ceb5398d163b1f64c2463b41810bf82b63be537003bf',
 'own_record_comparison_legacy_cf74da.py': 'cf74da23ea7208260cee70f74f282b2b57a209d1347f14d4c47b465f2b50ebd8',
 'phase7_audit_policy.py': '91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e',
 'phase7_claim_label_render.py': 'b80b1c7c32bddbf176f08fd5250a7a4c1e610a4848de075397397d7106786141',
 'phase7_mutation_baseline.py': 'f48dfff1cbb3ca72ce88766f0d9e56664bb7fea17a0f60d8a5f60e21095f7145',
 'phase7_policy_versions.py': '8c784f49dd8a860900cb2d67fd7a305fc38fa6cc07fb567b65490147e7c0ce81',
 'phase7_runtime_update.py': '8d8bc5ebec57818f652518043aa65452e9a0514c564d4babf8848fcefbf68a7d',
 'premise_declaration.py': 'e00404ad578efa7dcd9299a5d947be594f36c15e53fd44479d22d578caab5137',
 'prepare_nightly_note.py': 'f2421402521d9316d61895b84ab033d8e3cc7f744f4b77c15502a445775cc2a2',
 'probe_observations.py': 'ebbe0ffff1570acec84bcaf18570e69c9a66938cee932999d9a6729208abb4de',
 'production_hooks.py': '9b0a3d48e2cabff04c58a9020c07db2a9afe7e7f8c7cbde5e034d56d0b77db81',
 'public_metadata_readback.py': '8365c8d2474c4b1bb3e7da8c332da61bd6378694ccfba0629084cff9512b3b30',
 'publication_binding.py': '1fb3d5bc1d0df57445b8d7fed8a034e7bab7f1aeb0314db21e3cedd5e237df2e',
 'publication_gate.py': '4166653c08e8e06e20fe004592df56152c407ab36b8003ecd3380ee8bf94a0f1',
 'registration_imports.py': '37fd17b61a869c8343d5cd035dbbf87f05ed259a9aa3ddb3a5d83da8796fc707',
 'release_packet.py': '972cc9816e3f2d1c3f93120666358421c9163535afd143a6f401725fc3545357',
 'run_flow.py': '00a6d309360aabda0e27f37a0cd757e103c1c502497b3f2553e28d2070b98b04',
 'science_release_queue.py': '04e50fe03aa7e2e5858fd1c4523632c1fff36a2f2f5c8833f80460c198f42e1d',
 'science_release_stage.py': 'f531c2c71b6b146fdacf8193877abbad953e6e2900891134d724d80e339000c6',
 'scoped_release.py': 'a6e5fe9b1213d91987a5cf125d1f591e643e3e68eb5bac05492196b77e7e3ea8',
 'scoped_statement_text.py': '8a820419f94f295485a65f00f7ea3c207604a0d159639bce64628aeefbb72a03',
 'static_pregate.py': '659e2d66a45af24a846a5fafe26564ccf713492d0d06be0fb8172e961e862153',
 'theorem_coverage.py': '62bb9e87b10b8ef317616e4b906878d03f06752ab4e7d2dff90bdf9dfb27e99d',
 'track_b.py': 'faed81a12261607af23ec24e81286a208d11f5b0c8c1fd69b65a518d3a304bca'}

LABELLED_STANDARD = 'VRS-NIGHTLY-UNCERTIFIED-ARTIFACT-ENVELOPE-1'
LABELLED_BINDING_STANDARD = 'VRS-NIGHTLY-UNCERTIFIED-ARTIFACT-BINDING-1'
LABEL_TEXT = 'UNCERTIFIED — no issuer-produced Viridis Comparator certificate binds the exact bytes of this derived manuscript. Attached certificates cover only their exact sealed predecessors and quoted formal statements under their stated hypotheses. They do not certify this new PDF, its prose, the historical manuscript, or empirical claims. Results remain conditional on the stated model assumptions.'
LABEL_AUTHORITY = {'path':'reports/verification-coverage/2026-10-17/w42-artifact-label-authority/JUSTIN_W42_ARTIFACT_LABEL_AUTHORITY.json',
    'sha256':'f4347618a6ce2857f58ba680c7fc25ad5d5b728111c096d59250c037d19dca9a'}
LABELLED_TOP_PDF = 'Historical-Paper-UNCERTIFIED.pdf'
NATIVE_RENDERER = '/opt/homebrew/bin/tectonic'
RENDER_CACHE = {'path':'reports/verification-coverage/2026-10-06/phase-7-science-catchup-v001/runtime-install-v001/RENDERER_CACHE_MANIFEST.json','sha256':'d312006417a3eef3fca66a51db558b1853476cd9a8ed0479fe04ed351f8a9dc4'}
LABELLED_MANIFEST_FIELDS = MANIFEST_FIELDS | {'artifact_label','label_authority','scope_render'}
LABELLED_PB_FIELDS = PB_FIELDS | {'review_invocation'}

class AccessHold(ValueError):
    pass

def need(value, reason):
    if not value:
        raise AccessHold('HOLD_ARCHIVAL_MANUSCRIPT_ACCESS: ' + reason)

def closed_binding(root, value):
    need(isinstance(value, dict) and set(value) == {'path','sha256'}, 'closed input binding')
    return d.bound_file(root, value)

def binding(path):
    return {k: d.binding(path)[k] for k in ('path','sha256')}

def frozen_source_relative(name):
    need(name in _FROZEN_HASHES, 'unknown frozen source origin')
    return _HELPER_ORIGINS[name] if name in _HELPER_ORIGINS else GATES + '/' + name

@contextmanager
def frozen_sources(root):
    """Fresh private import graph, preserving ordinary default-reader dispatch.

    Every local import in the frozen gates namespace resolves only to a closed
    measured source. The unique module names exist solely for old self-lookup;
    no canonical sys.modules entry is replaced, and no .pyc is read or written.
    """
    root = Path(root).resolve(strict=True)
    sources = {}
    for name, expected in _FROZEN_HASHES.items():
        path = root / frozen_source_relative(name)
        raw = d.read_regular(path)
        need(d.digest(raw) == expected, 'frozen source changed: ' + name)
        sources[name[:-3]] = (path, raw)
    modules = {}
    loading = set()
    prefix = '_vrs_archival_' + uuid.uuid4().hex + '_'
    ordinary_import = builtins.__import__
    def own_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in sources:
            return load(name)
        if level == 0 and '.' not in name:
            need(not (root / GATES / (name + '.py')).exists(), 'unbound local import: ' + name)
        return ordinary_import(name, globals, locals, fromlist, level)
    def load(name):
        if name in modules:
            return modules[name]
        path, raw = sources[name]
        module = types.ModuleType(prefix + name)
        module.__file__ = str(path)
        module.__package__ = ''
        module.__builtins__ = {**vars(builtins), '__import__': own_import}
        modules[name] = module
        sys.modules[module.__name__] = module
        loading.add(name)
        try:
            exec(compile(raw, str(path), 'exec'), module.__dict__)
        finally:
            loading.remove(name)
        return module
    try:
        yield load
        need(not loading, 'unfinished frozen import')
        for name, (path, raw) in sources.items():
            need(d.read_regular(path) == raw, 'frozen source race: ' + name)
    finally:
        for module in modules.values():
            sys.modules.pop(module.__name__, None)

def require_authority(root, authority):
    with frozen_sources(root) as load:
        return load('phase7_audit_policy').require_audit_authority(root, authority)

def predecessor(root, note, authority, load):
    note = Path(note).resolve(strict=True)
    need(note.is_relative_to(Path(root).resolve(strict=True)), 'canonical predecessor required')
    policy = load('phase7_audit_policy')
    # No alternate consumer or caller-supplied result is accepted here.
    current = policy.require_note_publication_bound(note, root, authority)
    need(current.get('status') == 'PUBLICATION_BOUND'
         and current.get('exact_publication_binding') is True,
         'actual default predecessor admission')
    manifest = json.loads(d.read_regular(note / 'SCOPED_RELEASE_MANIFEST.json'))
    minimal = load('nightly_minimal_policy')
    need(manifest.get('standard') == minimal.scoped.STANDARD
         and json.loads(d.read_regular(note / 'PHASE7_RULE_EXECUTION.json')).get('standard')
         == minimal.RULE_STANDARD, 'exact minimal-note predecessor only')
    need(current.get('publication_binding') == binding(note / 'PUBLICATION_BINDING.json')
         and current.get('identity', {}).get('manifest_sha256') == d.sha(note / 'SCOPED_RELEASE_MANIFEST.json'),
         'predecessor manifest/binding identity changed')
    return current

def archive(data):
    result = []
    with zipfile.ZipFile(BytesIO(data)) as z:
        for item in z.infolist():
            name = d.safe_member(item.filename)
            need(not item.is_dir() and not item.flag_bits & 1, 'regular clear archive member')
            result.append((name, z.read(item)))
    d.require_archive(data, d.member_inventory(result))
    return result

def manuscripts(run, current_pdf, historical_pdf):
    return [
        {'role':'CURRENT_SCOPED_MANUSCRIPT','filename':'paper.pdf',
         'archive_member':None,'sha256':d.digest(current_pdf),'certification':'EXACT_SCOPED_PREDECESSOR_ONLY'},
        {'role':'UNCERTIFIED_HISTORICAL_MANUSCRIPT','filename':run + '-' + TOP_PDF,
         'archive_member':'SCOPE_EVIDENCE.zip!/' + HISTORICAL_PDF,
         'sha256':d.digest(historical_pdf),'certification':'ENTIRELY_UNCERTIFIED'}]

def require_self_contained_original(original):
    """This first closed format has no caller-selected file dependency list.

    Only standalone source plus the exact pinned renderer cache is supported.
    A manuscript needing extra local inputs stays HOLD until a separately
    reviewed closed dependency format exists; its TeX is never rewritten.
    """
    need(isinstance(original, bytes), 'exact historical TeX bytes')
    text=original.decode('utf-8')
    # TeX translates ^^ before tokenization, including inside a control word.
    # The supported format also excludes category changes, macro construction,
    # custom commands and unreviewed package/environment file readers.
    need('^^' not in text, 'unbound historical translation syntax')
    need(all(c in '\t\r\n' or unicodedata.category(c) not in {'Cc','Cf','Cs'} for c in text),
         'unsupported historical control or formatting character')
    words={
        'documentclass','usepackage','begin','end','author','title','date',
        'maketitle','section','subsection','subsubsection','paragraph','emph',
        'textbf','textit','texttt','textrm','text','footnote','cite','bibitem',
        'label','ref','eqref','pageref','url','href','hypersetup','newtheorem',
        'setlength','parindent','parskip','baselineskip','linewidth','textwidth',
        'hfill','vfill','quad','qquad','noindent','sloppy','fussy','enlargethispage',
        'item','centering','small','footnotesize','scriptsize','tiny','large',
        'Large','LARGE','huge','Huge','rm','mathrm','mathbf','mathbb','mathcal',
        'mathit','mathsf','operatorname','frac','tfrac','dfrac','sqrt','bar','hat',
        'overline','underline','left','right','big','Big','bigl','bigr','Bigl',
        'Bigr','langle','rangle','lceil','rceil','lfloor','rfloor','vert','Vert',
        'sum','prod','int','lim','min','max','inf','sup','log','ln','exp','sin',
        'cos','tan','det','dim','ker','Pr','in','notin','subset','subseteq',
        'supset','supseteq','cup','cap','emptyset','forall','exists','neg','land',
        'lor','implies','iff','to','mapsto','rightarrow','leftarrow',
        'Rightarrow','Leftarrow','Leftrightarrow','Longleftrightarrow',
        'le','leq','ge','geq','ne','neq','equiv','approx','sim','simeq','cong',
        'propto','times','cdot','pm','mp','infty','partial','nabla','ell','square',
        'alpha','beta','gamma','delta','epsilon','varepsilon','zeta','eta',
        'theta','vartheta','iota','kappa','lambda','mu','nu','xi','pi','varpi',
        'rho','varrho','sigma','varsigma','tau','upsilon','phi','varphi','chi',
        'psi','omega','Gamma','Delta','Theta','Lambda','Xi','Pi','Sigma',
        'Upsilon','Phi','Psi','Omega','toprule','midrule','bottomrule','hline',
        'multicolumn','cline','ldots','cdots','vdots','ddots',
    }
    symbols=set('\\{}%$&#_~^ ,;:!/.=|()-[]\'"`\n\r\t')
    tokens=[];plain=[];i=0
    while i<len(text):
        if text[i]=='%':
            ends=[n for n in (text.find('\n',i),text.find('\r',i)) if n>=0]
            i=min(ends) if ends else len(text)
        elif text[i]=='\\':
            start=i;i+=1
            need(i<len(text), 'unsupported trailing historical control escape')
            if text[i].isascii() and (text[i].isalpha() or text[i]=='@'):
                begin=i
                while i<len(text) and text[i].isascii() and (text[i].isalpha() or text[i]=='@'):i+=1
                word=text[begin:i]
                need(word in words, 'unbound historical or unsupported control word: '+word)
                tokens.append((word,len(''.join(plain))))
            else:
                need(text[i] in symbols, 'unsupported historical control symbol')
                i+=1
            plain.append(text[start:i])
        else:
            plain.append(text[i]);i+=1
    clean=''.join(plain)
    # Bind every admitted file-loading markup operation to a fixed cache role.
    # Whitespace after the command is accepted; macro-valued arguments are not.
    for word,pos in tokens:
        tail=clean[pos:]
        if word in {'documentclass','usepackage'}:
            match=re.match(r'\\'+word+r'\s*(?:\[([^]\n]*)\])?\s*\{([^{}\\]*)\}',tail)
            need(match is not None, 'literal pinned-cache package and class declaration')
            options,names=match.groups();names=names.split(',')
            if word=='documentclass':
                need(names==['article'] and options in {None,'10pt','11pt','12pt'}, 'only pinned-cache article class')
            else:
                need(all(n in {'geometry','amsmath','amssymb','amsthm','booktabs','microtype','hyperref'} for n in names), 'only fixed pinned-cache packages')
                need(options is None or names==['hyperref'] and options=='hidelinks'
                     or names==['geometry'] and re.fullmatch(r'margin=(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)(?:in|cm|mm|pt)',options) is not None,
                     'only fixed pinned-cache package options')
        elif word in {'begin','end'}:
            match=re.match(r'\\'+word+r'\s*\{([^{}\\]*)\}',tail)
            need(match is not None and match[1] in {'document','abstract','equation','equation*',
                 'align','align*','aligned','gather','gather*','split','pmatrix','bmatrix','matrix',
                 'cases','center','tabular','thebibliography','itemize','enumerate','description',
                 'theorem','proposition','corollary','lemma','definition','remark','proof'},
                 'only fixed historical markup environments')
        elif word=='newtheorem':
            match=re.match(r'\\newtheorem\s*\{([^{}\\]*)\}\s*\{([^{}\\]*)\}',tail)
            need(match is not None and match[1] in {'theorem','proposition','corollary','lemma','definition','remark'}
                 and match[2]==match[1].capitalize(), 'only fixed historical theorem environment declaration')
        elif word=='hypersetup':
            need(re.match(r'\\hypersetup\s*\{hidelinks\}',tail) is not None,
                 'only fixed historical hyperlink options')
    return original

def require_pdf_envelope(pdf):
    # Structural envelope is an early cold-fail check, not visual review or a
    # replacement for the actual pinned render observation and source binding.
    need(isinstance(pdf, bytes) and re.match(br'%PDF-[12]\.[0-9](?:\r?\n|\r)', pdf) is not None,
         'actual historical PDF header required')
    end=re.search(br'startxref\s+([0-9]+)\s+%%EOF\s*$', pdf)
    need(end is not None and 0 < int(end[1]) < end.start(),
         'complete historical PDF envelope required')
    return pdf

def render_identity(note, root, original, pdf, load):
    require_self_contained_original(original)
    require_pdf_envelope(pdf)
    seen = {}
    # Same old pinned binary/cache/source/PDF observer as the scoped manuscript.
    # The isolated render input is paper.tex with exact ORIGINAL_paper.tex bytes.
    observation = load('phase7_audit_policy').require_pdf_provenance(
        Path(note) / 'historical-render', root, original, pdf, seen)
    need(d.read_regular(Path(note) / 'historical-render/paper.tex') == original,
         'historical render input must equal original archival TeX')
    seen[str((Path(note) / 'historical-render/paper.tex').resolve())] = d.digest(original)
    return {'standard':RENDER_STANDARD,'source_tex_sha256':d.digest(original),
        'rendered_pdf_sha256':d.digest(pdf),
        'observation':binding(Path(note) / 'historical-render/render-observation/RENDERER_OBSERVATION.json'),
        'inputs':seen,'historical_scope':'ENTIRELY_UNCERTIFIED',
        'semantic_or_scientific_review':False}, observation

def _finish(inputs):
    for path, expected in inputs.items():
        need(d.sha(path) == expected, 'input changed before return')

def _derive(root, base, authority, out, load):
    current = predecessor(root, base, authority, load)
    base = Path(base).resolve(strict=True)
    run = current['run_id']
    original = d.read_regular(base / HISTORICAL_TEX)
    pdf = d.read_regular(Path(out) / (run + '-' + TOP_PDF))
    render, _ = render_identity(out, root, original, pdf, load)
    original_members = archive(d.read_regular(base / 'SCOPE_EVIDENCE.zip'))
    need(HISTORICAL_TEX in dict(original_members)
         and dict(original_members)[HISTORICAL_TEX] == original
         and HISTORICAL_PDF not in dict(original_members), 'unchanged original archive identity')
    members = original_members + [(HISTORICAL_PDF, pdf)]
    expected = {}
    for row in current['uploads']:
        name = d.safe_member(row['filename'])
        need('/' not in name and name not in expected, 'closed predecessor upload names')
        raw = d.read_regular(base / name)
        need(d.digest(raw) == row['sha256'], 'predecessor upload changed')
        expected[name] = d.archive_bytes(members) if name == 'SCOPE_EVIDENCE.zip' else raw
    expected[run + '-' + TOP_PDF] = pdf
    # Original scientific review is a separately named exact attachment, never
    # an assertion that the old binding covers this changed access archive.
    expected['PREDECESSOR_SCOPED_RELEASE_MANIFEST.json'] = d.read_regular(base / 'SCOPED_RELEASE_MANIFEST.json')
    expected['PREDECESSOR_PUBLICATION_BINDING.json'] = d.read_regular(base / 'PUBLICATION_BINDING.json')
    expected['PHASE7_RULE_EXECUTION.json'] = d.read_regular(base / 'PHASE7_RULE_EXECUTION.json')
    manifest = {'standard':STANDARD,'run_id':run,
        'predecessor':{'path':str(base),'manifest':binding(base / 'SCOPED_RELEASE_MANIFEST.json'),
                       'publication_binding':binding(base / 'PUBLICATION_BINDING.json')},
        'authority':deepcopy(authority),
        'execution_sources':[{'name':n,'path':str(Path(root) / frozen_source_relative(n)),'sha256':h}
                             for n,h in sorted(_FROZEN_HASHES.items())],
        'uploads':[{'filename':n,'sha256':d.digest(b)} for n,b in sorted(expected.items())],
        'archive_members':d.member_inventory(members),
        'manuscripts':manuscripts(run,expected['paper.pdf'],pdf),
        'historical_render':render,'certifies':False,'publication_authorized':False,
        'ssot_writes':0,'zenodo_writes':0}
    _finish(render['inputs'])
    _finish(current['input_bindings'])
    need(predecessor(root, base, authority, load) == current, 'predecessor changed during access derivation')
    return manifest, expected, current

def prepare(root, base, out, authority, *, render):
    """Derive access only after genuine later predecessor review. Never render
    a corrected or invented manuscript in place of the exact original bytes.
    render writes the ordinary pinned render observation in historical-render.
    """
    root = Path(root).resolve(strict=True)
    out = Path(out)
    need(not any(p.is_symlink() for p in (out, *out.parents)), 'regular access output ancestry')
    out = out.resolve()
    need(out.is_relative_to(root / 'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access')
         and not out.exists(), 'new canonical immutable access output required')
    with frozen_sources(root) as load:
        current = predecessor(root, base, authority, load)
        original = require_self_contained_original(d.read_regular(Path(base) / HISTORICAL_TEX))
        out.mkdir(parents=True, exist_ok=False)
        render_dir = out / 'historical-render'
        d.immutable(render_dir / 'paper.tex', original)
        pdf = render(render_dir / 'paper.tex', root=root)
        require_pdf_envelope(pdf)
        d.immutable(out / (current['run_id'] + '-' + TOP_PDF), pdf)
        manifest, expected, _ = _derive(root, base, authority, out, load)
        for name, raw in expected.items():
            d.immutable(out / name, raw)
        # Preserve the unmodified on-disk historical originals and displays too.
        for name, raw in archive(d.read_regular(base / 'SCOPE_EVIDENCE.zip')):
            d.immutable(out / name, raw)
        d.immutable(out / HISTORICAL_PDF, pdf)
        d.immutable(out / 'SCOPED_RELEASE_MANIFEST.json', d.raw_json(manifest))
        pb = {'standard':BINDING_STANDARD,'status':'ACCESS_BYTES_BOUND_NOT_PUBLICATION_AUTHORIZED',
              'run_id':current['run_id'],'manifest':binding(out / 'SCOPED_RELEASE_MANIFEST.json'),
              'predecessor_binding':manifest['predecessor']['publication_binding'],
              'authority':deepcopy(authority),'issued_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
              'certifies':False,'publication_authorized':False}
        d.immutable(out / 'PUBLICATION_BINDING.json', d.raw_json(pb))
    return require_current(out, root, authority)

def require_current(note, root, authority):
    root = Path(root).resolve(strict=True)
    note = Path(note).resolve(strict=True)
    need(note.is_relative_to(root), 'access note outside canonical root')
    before = d.read_regular(note / 'SCOPED_RELEASE_MANIFEST.json')
    pb_before = d.read_regular(note / 'PUBLICATION_BINDING.json')
    manifest = json.loads(before)
    need(isinstance(manifest, dict) and set(manifest) == MANIFEST_FIELDS
         and manifest.get('standard') == STANDARD, 'closed distinct archival access manifest')
    need(manifest['authority'] == authority, 'same approved predecessor authority')
    base = Path(manifest['predecessor']['path'])
    need(base.resolve(strict=True) != note, 'distinct immutable scientific predecessor')
    with frozen_sources(root) as load:
        actual, expected, current = _derive(root, base, authority, note, load)
        need(actual == manifest, 'fresh exact additive access identity')
        for name, raw in expected.items():
            need(d.read_regular(note / name) == raw, 'changed copied access input: ' + name)
        for name, raw in archive(d.read_regular(note / 'SCOPE_EVIDENCE.zip')):
            need(d.read_regular(note / name) == raw, 'archive/local access bytes differ')
        pb = json.loads(pb_before)
        need(set(pb) == PB_FIELDS and pb['standard'] == BINDING_STANDARD
             and pb['status'] == 'ACCESS_BYTES_BOUND_NOT_PUBLICATION_AUTHORIZED'
             and pb['run_id'] == manifest['run_id'] and pb['authority'] == authority
             and pb['manifest'] == binding(note / 'SCOPED_RELEASE_MANIFEST.json')
             and pb['predecessor_binding'] == actual['predecessor']['publication_binding']
             and pb['certifies'] is False and pb['publication_authorized'] is False,
             'exact distinct access binding')
        issued = load('nightly_minimal_policy').time(pb['issued_at_utc'])
        base_pb = json.loads(d.read_regular(base / 'PUBLICATION_BINDING.json'))
        need(load('nightly_minimal_policy').time(base_pb['issued_at_utc']) <= issued
             <= dt.datetime.now(dt.timezone.utc), 'access after genuine predecessor admission')
        need(d.read_regular(note / 'SCOPED_RELEASE_MANIFEST.json') == before
             and d.read_regular(note / 'PUBLICATION_BINDING.json') == pb_before,
             'access manifest/binding race')
        return {**current, 'status':'PUBLICATION_BOUND','exact_publication_binding':True,
                'access_standard':STANDARD,'manuscripts':manifest['manuscripts'],
                'uploads':manifest['uploads'],
                'policy_receipt':binding(note / 'PHASE7_RULE_EXECUTION.json'),
                'publication_binding':binding(note / 'PUBLICATION_BINDING.json'),
                'scientific_predecessor':actual['predecessor'],
                'certifies':False,'publication_authorized':False}



def cache_snapshot(directory):
    directory=Path(directory)
    need(directory.is_dir()and not any(p.is_symlink()for p in(directory,*directory.parents)),'regular exact renderer cache')
    rows={}
    for path in sorted(directory.rglob('*')):
        need(not path.is_symlink(),'renderer cache symlink')
        if path.is_file():rows[d.safe_member(str(path.relative_to(directory)))]=d.digest(d.read_regular(path))
    return rows


def require_native_render_supervision():
    """Fail before scratch or Popen; capabilities are checked, never inferred."""
    need(sys.platform == 'darwin' and sys.version_info[:2] == (3, 14),
         'native renderer requires actual supported Mac Python3.14')
    need(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL,
         'native renderer requires default SIGCHLD')
    need(threading.active_count() == 1 and threading.current_thread() is threading.main_thread(),
         'native renderer requires one main thread')
    need(all(hasattr(os, name) for name in ('waitid', 'P_PID', 'WNOWAIT', 'WEXITED', 'WNOHANG',
                                           'waitpid', 'waitstatus_to_exitcode')),
         'native renderer requires actual waitid WNOWAIT')
    try:
        os.waitid(os.P_PID, os.getpid(), os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return  # Valid native non-child probe; not child/OS qualification.
    except (OSError, NotImplementedError) as exc:
        raise AccessHold('native renderer waitid capability unavailable') from exc
    raise AccessHold('native renderer non-child capability probe ambiguous')


def native_render_observe(reservation):
    process = reservation['process'];pid = reservation['pid']
    need(type(process) is subprocess.Popen and process.pid==pid
         and reservation['parent_pid']==os.getpid()
         and not reservation['reaped'] and not reservation['lost'] and process.returncode is None,
         'native renderer reservation lost or already reaped')
    try:
        observed = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except (ChildProcessError, OSError) as exc:
        reservation['lost'] = True
        raise AccessHold('native renderer own unreaped reservation unavailable') from exc
    need(observed is None or observed.si_pid == pid, 'native renderer wrong native child observation')
    return observed


# Executed only by the original parent's actual Popen child, after Python exec.
# This is NOT preexec_fn: the constructor's exec-error pipe has already closed.
# The fixed shim has no fork, Core/network operation or arbitrary-command API.
_NATIVE_RENDER_STARTUP = r'''
import os, sys
try:
    if len(sys.argv) != 6:
        raise RuntimeError('CLOSED_RENDER_STARTUP_ARGV')
    ready, go, parent = (int(value) for value in sys.argv[1:4])
    binary, outdir = sys.argv[4:6]
    pid = os.getpid()
    if os.getppid() != parent or os.getsid(0) != pid or os.getpgid(0) != pid:
        raise RuntimeError('ORIGINAL_NATIVE_PARENT_AND_SESSION')
    if os.write(ready, b'R') != 1:
        raise RuntimeError('RENDER_READY_WRITE')
    os.close(ready)
    if os.read(go, 1) != b'G':
        raise RuntimeError('RENDER_GO_REQUIRED')
    os.close(go)
    if os.getppid() != parent or os.getsid(0) != pid or os.getpgid(0) != pid:
        raise RuntimeError('ORIGINAL_PARENT_BEFORE_RENDER_EXEC')
    os.execve(binary, ['/opt/homebrew/bin/tectonic', '--only-cached', '--keep-logs',
                       '--outdir', outdir, 'paper.tex'], os.environ)
finally:
    os._exit(127)
'''


def native_render_reservation(process):
    """Bind only original native parent/child here; isolation needs live READY.

    WNOWAIT exit remains valid ownership even when Darwin live SID queries
    return ESRCH. This function NEVER queries SID/PGID or invents isolation.
    """
    need(type(process) is subprocess.Popen and type(process.pid) is int and process.pid > 1,
         'native renderer actual owned Popen required')
    reservation = {'process':process, 'pid':process.pid, 'parent_pid':os.getpid(),
        'reaped':False, 'lost':False, 'isolated':False, 'bound_sid':None, 'bound_pgid':None,
        'bound_before_go':False, 'go_attempted':False, 'term_attempted':False,
        'final_signal_attempted':False, 'reap_started':False, 'returncode':None,
        'group_absent':False, 'term_deadline':None, 'reap_deadline':None, 'absence_deadline':None}
    native_render_observe(reservation)
    return reservation


class NativeRenderAdmission:
    """One actual own Popen object and pre-render READY/GO control descriptors.

    Unknown constructor ownership closes GO and retains cache. There is no
    saved/reported PID fallback, callback, extra process or post-reap signal.
    """
    def __init__(self, binary, command, directory, environment, stdout, stderr, deadline):
        self.binary = str(binary);self.command = list(command);self.directory = directory
        self.environment = environment;self.stdout = stdout;self.stderr = stderr
        self.deadline = deadline;self.parent_pid = os.getpid()
        self.process = None;self.reservation = None
        self.constructor_attempted = False;self.constructor_completed = False
        self.ready_read = None;self.ready_write = None;self.go_read = None;self.go_write = None

    def close_control(self):
        # Close the original owner GO writer first. A constructor-loss shim can
        # then only see EOF and exit127 before any renderer exec.
        for name in ('go_write', 'go_read', 'ready_write', 'ready_read'):
            fd = getattr(self, name)
            if fd is not None:
                setattr(self, name, None)  # Never re-close a reused descriptor.
                os.close(fd)

    def start(self):
        require_native_render_supervision()
        need(self.process is None and not self.constructor_attempted,
             'exclusive native renderer constructor')
        need(self.command == ['/opt/homebrew/bin/tectonic', '--only-cached', '--keep-logs',
                              '--outdir', str(Path(self.directory)/'render-observation'), 'paper.tex'],
             'fixed native renderer command')
        need(time.monotonic() < self.deadline, 'native startup inside original180 deadline')
        self.ready_read,self.ready_write = os.pipe()
        self.go_read,self.go_write = os.pipe()
        self.constructor_attempted = True
        # Python shim exec completes before Popen returns. The payload still
        # waits for GO, so the parent can genuinely bind live SID/PGID first.
        self.process = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c',
            _NATIVE_RENDER_STARTUP, str(self.ready_write), str(self.go_read),
            str(self.parent_pid), self.binary, str(Path(self.directory)/'render-observation')],
            executable=sys.executable, cwd=self.directory, env=self.environment,
            stdin=subprocess.DEVNULL, stdout=self.stdout, stderr=self.stderr,
            start_new_session=True, pass_fds=(self.ready_write,self.go_read))
        self.constructor_completed = True
        self.reservation = native_render_reservation(self.process)
        for name in ('ready_write','go_read'):
            fd=getattr(self,name);setattr(self,name,None);os.close(fd)
        return self

    def bind_ready(self):
        state=self.reservation
        need(state is not None and not state['go_attempted'] and self.parent_pid==os.getpid(),
             'original native admission owner')
        while True:
            need(time.monotonic()<self.deadline, 'native READY inside original180 deadline')
            readable,_,_=select.select([self.ready_read],[],[],min(.01,max(0,self.deadline-time.monotonic())))
            if readable:
                need(os.read(self.ready_read,1)==b'R', 'native READY missing or EOF')
                # The fixed shim remains blocked on GO throughout these actual
                # kernel queries. An externally killed/unbound child stays HOLD.
                need(native_render_observe(state) is None, 'native child exited before READY binding')
                try:
                    sid=os.getsid(state['pid']);pgid=os.getpgid(state['pid'])
                except OSError as exc:
                    raise AccessHold('native live isolation binding unavailable') from exc
                need(sid==pgid==state['pid'] and native_render_observe(state) is None,
                     'actual live original child SID/PGID before GO')
                state['bound_sid']=sid;state['bound_pgid']=pgid
                state['bound_before_go']=True;state['isolated']=True
                fd=self.ready_read;self.ready_read=None;os.close(fd)
                return state
            need(native_render_observe(state) is None, 'native child exited before READY')

    def go(self):
        state=self.reservation
        need(state is not None and state['isolated'] and state['bound_before_go']
             and not state['go_attempted'] and self.parent_pid==os.getpid(),
             'genuine pre-exec native binding required')
        need(native_render_observe(state) is None and time.monotonic()<self.deadline,
             'original live child before GO inside original180 deadline')
        state['go_attempted']=True  # A failed/interrupted write is never replayed.
        need(os.write(self.go_write,b'G')==1, 'single exact native renderer GO')
        fd=self.go_write;self.go_write=None;os.close(fd)

    def close(self):
        self.close_control()
        if self.process is None:
            need(not self.constructor_attempted, 'unknown renderer constructor; cache retained')
            return
        if self.reservation is None:
            self.reservation=native_render_reservation(self.process)
        close_render_group(self.reservation)


def native_render_signal(reservation, sig):
    # Every nonzero signal has a fresh native OWN-child reservation. A saved
    # numeric PGID, successful wait, or parent JSON can never satisfy this.
    need(sig in (signal.SIGTERM, signal.SIGKILL) and reservation['parent_pid']==os.getpid()
         and not reservation['reap_started'] and not reservation['reaped']
         and not reservation['final_signal_attempted']
         and (not reservation['isolated'] or (reservation['bound_before_go']
              and reservation['bound_sid']==reservation['bound_pgid']==reservation['pid'])),
         'native renderer signal phase closed')
    observed = native_render_observe(reservation)
    if sig == signal.SIGKILL:
        reservation['final_signal_attempted'] = True  # Before syscall/interruption.
    else:
        reservation['term_attempted'] = True
    try:
        (os.killpg if reservation['isolated'] else os.kill)(reservation['pid'], sig)
    except ProcessLookupError:
        pass
    except PermissionError as exc:
        # A zombie-only Darwin group can deny a signal. This is NEVER absence:
        # exact exit, own reap AND subsequent ESRCH are still mandatory.
        if native_render_observe(reservation) is None:
            raise AccessHold('native renderer live signal permission unknown') from exc


def close_render_group(reservation):
    """Last nonzero signal, native reap, then ONLY zero/ESRCH absence probes.

    One-way state and absolute per-phase deadlines survive error/finally
    reentry. Lost reservation or unknown cleanup retains the private cache.
    This does not qualify owner-death or a whole-action outer600 supervisor.
    """
    process = reservation['process'];pid = reservation['pid']
    if not reservation['reaped']:
        if not reservation['reap_started']:
            if not reservation['final_signal_attempted']:
                observed = native_render_observe(reservation)
                if observed is None:
                    if reservation['term_deadline'] is None:
                        reservation['term_deadline'] = time.monotonic() + 10
                    if not reservation['term_attempted']:
                        native_render_signal(reservation, signal.SIGTERM)
                    while time.monotonic() < reservation['term_deadline']:
                        if native_render_observe(reservation) is not None:
                            break
                        time.sleep(.01)
                native_render_signal(reservation, signal.SIGKILL)
            # Even if interrupted after final-signal flag/before syscall, no
            # reentry can signal after a later reap; unproved exit stays HOLD.
            reservation['reap_started'] = True
        if reservation['reap_deadline'] is None:
            reservation['reap_deadline'] = time.monotonic() + 5
        while native_render_observe(reservation) is None:
            need(time.monotonic() < reservation['reap_deadline'],
                 'native renderer exit unobserved after final signal; cache retained')
            time.sleep(.01)
        actual, status = os.waitpid(pid, 0)
        need(actual == pid, 'native renderer wrong own child reap')
        code = os.waitstatus_to_exitcode(status)
        # reap_started was set BEFORE waitpid. An interruption after kernel
        # reap but before these stores cannot reopen any nonzero signal path.
        reservation['returncode'] = code
        process.returncode = code
        reservation['reaped'] = True
    need(reservation['isolated'] and reservation['bound_before_go'],
         'unbound renderer reaped; group closure unproven; cache retained')
    if reservation['absence_deadline'] is None:
        reservation['absence_deadline'] = time.monotonic() + 5
    while True:
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            reservation['group_absent'] = True
            return reservation['returncode']
        except PermissionError:
            pass  # Unknown/present. Never manufacture ESRCH.
        need(time.monotonic() < reservation['absence_deadline'],
             'native renderer group absence unproved; private cache retained')
        time.sleep(.01)


def require_render_logs(directory,seen):
    """Bound fresh retained logs; a missing glyph is never faithful output."""
    for name in ('stdout.txt','stderr.txt','paper.log'):
        path=Path(directory)/'render-observation'/name
        need(not any(p.is_symlink()for p in(path,*path.parents)),'regular renderer log ancestry')
        if name=='paper.log'and not path.exists():continue
        identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        entry=path.lstat();need(stat.S_ISREG(entry.st_mode),'regular renderer log')
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        with os.fdopen(fd,'rb')as file:
            before=os.fstat(file.fileno());need(identity(entry)==identity(before),'renderer log changed before read')
            raw=file.read(4194305);after=os.fstat(file.fileno())
        final=path.lstat()
        need(not any(p.is_symlink()for p in(path,*path.parents)),'regular renderer log ancestry')
        need(len(raw)<=4194304 and len(raw)==before.st_size
             and identity(entry)==identity(before)==identity(after)==identity(final),'bounded stable renderer log')
        need(b'Missing character:'not in raw and b'could not represent character'not in raw,
             'native renderer missing glyph; artifact not faithful')
        seen[str(path.resolve(strict=True))]=d.digest(raw)


def native_render(path,*,root):
    """Fixed current-source callback; pinned binary/cache checked BEFORE exec.

    One owned temporary input cache exists at a time. It is deleted only after
    the renderer exits and its exact hashes are compared; no cache copy becomes
    release evidence. This function runs no Lean, network fetch or publisher.
    """
    require_native_render_supervision()
    root=Path(root).resolve(strict=True);path=Path(path)
    need(not any(p.is_symlink()for p in(path,*path.parents)),'regular native render input ancestry')
    path=path.resolve(strict=True)
    need(path.name=='paper.tex'and path.is_relative_to(root),'canonical exact render input')
    before=d.read_regular(path);binary=Path(NATIVE_RENDERER).resolve(strict=True)
    binary_before=d.read_regular(binary)
    manifest_path,manifest_raw=closed_binding(root,RENDER_CACHE);manifest=json.loads(manifest_raw)
    with frozen_sources(root)as load:
        policy=load('phase7_audit_policy')
        need(d.digest(binary_before)==policy.RENDERER_SHA and d.digest(manifest_raw)==policy.RENDERER_CACHE_SHA,
             'pinned renderer and cache before execution')
    cache=Path(manifest['cache_root']).resolve(strict=True)
    need(cache.is_relative_to(root)and manifest.get('schema')=='VRS-PHASE7-TECTONIC-CACHE-1'
         and len(manifest.get('files',{}))==556,'complete contained renderer cache')
    expected=cache_snapshot(cache);need(expected==manifest['files'],'all pinned renderer assets before execution')
    build=path.parent/'render-observation';need(not build.exists(),'exclusive native render attempt')
    build.mkdir()
    command=['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs','--outdir',str(build),'paper.tex']
    process=None;reservation=None;admission=None;spawn_attempted=False;group_closed=False;started=dt.datetime.now(dt.timezone.utc).isoformat()
    private=Path(tempfile.mkdtemp(prefix='vrs-labelled-render-cache-')).resolve(strict=True)
    try:
        for name,pin in expected.items():
            raw=d.read_regular(cache/name);need(d.digest(raw)==pin,'cache changed during private copy')
            d.immutable(private/name,raw)
        need(cache_snapshot(private)==expected,'private exact input cache')
        environment={k:os.environ[k]for k in ('PATH','LANG','LC_ALL','TMPDIR')if k in os.environ}
        environment['TECTONIC_CACHE_DIR']=str(private)
        try:
            with (build/'stdout.txt').open('xb')as stdout,(build/'stderr.txt').open('xb')as stderr:
                render_deadline=time.monotonic()+180  # Startup consumes this original budget.
                admission=NativeRenderAdmission(binary,command,path.parent,environment,stdout,stderr,render_deadline)
                spawn_attempted=True
                admission.start();admission.bind_ready();admission.go()
                process=admission.process;reservation=admission.reservation
                while native_render_observe(reservation) is None:
                    if time.monotonic() >= render_deadline:
                        close_render_group(reservation);group_closed=True
                        raise AccessHold('HOLD_NATIVE_RENDER_180S_WITH_CLEANUP')
                    time.sleep(.01)
            close_render_group(reservation);group_closed=True
            ended=dt.datetime.now(dt.timezone.utc).isoformat()
            closure=(cache_snapshot(cache)==cache_snapshot(private)==expected
                and d.read_regular(binary)==binary_before and Path(NATIVE_RENDERER).resolve(strict=True)==binary
                and d.read_regular(path)==before and d.read_regular(manifest_path)==manifest_raw)
            pdf=d.read_regular(build/'paper.pdf')if process.returncode==0 else b''
            observation={'source_tex_sha256':d.digest(before),'rendered_pdf_sha256':d.digest(pdf),
                'command':command,'renderer_binary':{'invoked_path':command[0],'resolved_path':str(binary),'sha256':d.digest(binary_before)},
                'cache_manifest':deepcopy(RENDER_CACHE),'cache_file_count':len(expected),'cache_and_binary_exact_after':closure,
                'started_at_utc':started,'ended_at_utc':ended,'returncode':process.returncode,
                'network_resource_fetch_disabled':True,'no_env_or_stdin_or_credentials_captured':True,'local_lean_execution':False}
            d.immutable(build/'RENDERER_OBSERVATION.json',d.raw_json(observation))
            require_render_logs(path.parent,{})
            need(process.returncode==0 and closure,'native renderer failed or input closure changed')
            require_pdf_envelope(pdf)
        finally:
            if admission is not None:
                admission.close_control()
                if not group_closed:
                    admission.close();group_closed=True
    finally:
        # A failed group closure retains this one scratch tree for diagnosis.
        # Never delete input files while a renderer descendant may still use them.
        if not spawn_attempted or group_closed:shutil.rmtree(private)
        # Constructor loss/unknown reservation never proves no child exists.
        # The scratch cache remains; future Root orchestration must HOLD.
    return pdf

def labelled_tex(original, *, historical):
    """Only a fixed banner insertion; never execute or rewrite source commands.

    Historical source must first pass the unchanged closed N1 grammar. The
    other input is supplied only by the freshly admitted exact scoped template.
    Scan real control tokens; comments/escaped lookalikes cannot select a site.
    """
    need(isinstance(original,bytes) and len(original)<=4194304, 'bounded exact label source')
    if historical:
        require_self_contained_original(original)
    text=original.decode('utf-8')
    need(LABEL_TEXT not in text, 'source already has artifact label')
    depth=0; env=[]; documents=[]; titles=[]; i=0
    while i<len(text):
        c=text[i]
        if c=='%':
            while i<len(text) and text[i] not in '\r\n':i+=1
            continue
        if c=='{':depth+=1;i+=1;continue
        if c=='}':
            need(depth>0,'unbalanced label source braces');depth-=1;i+=1;continue
        if c!='\\':i+=1;continue
        start=i;i+=1
        need(i<len(text),'trailing label source escape')
        if not (text[i].isascii() and (text[i].isalpha() or text[i]=='@')):
            i+=1;continue
        begin=i
        while i<len(text) and text[i].isascii() and (text[i].isalpha() or text[i]=='@'):i+=1
        word=text[begin:i]
        if word in {'begin','end'}:
            match=re.match(r'\s*\{([A-Za-z*]+)\}',text[i:])
            need(match is not None,'literal label environment required')
            name=match[1];i+=match.end()
            if name=='document':
                need(depth==0,'nested document label source')
                documents.append((word,start,i))
            if word=='begin':env.append(name)
            else:
                need(env and env[-1]==name,'unbalanced label environments');env.pop()
        elif word=='maketitle':
            need(depth==0 and env==['document'],'nested label title refused')
            titles.append((start,i))
    need(depth==0 and not env and len(documents)==2 and [r[0]for r in documents]==['begin','end']
         and len(titles)==1 and documents[0][2]<=titles[0][0]<documents[1][1], 'unique complete document/title required')
    between=text[documents[0][2]:titles[0][0]]
    need(not re.sub(r'%[^\r\n]*(?:\r\n|\r|\n|$)','',between).strip(), 'title must begin document body')
    position=titles[0][1]
    insertion='\n\n'+r'\noindent\textbf{'+LABEL_TEXT+'}\n\n'
    result=(text[:position]+insertion+text[position:]).encode()
    if historical:
        require_self_contained_original(result)
    return result


def require_label_authority(root):
    path,raw=closed_binding(root,LABEL_AUTHORITY)
    value=json.loads(raw)
    need(value.get('answer')=='Approve artifact-specific wording'
         and value.get('approved_text')==LABEL_TEXT
         and value.get('proposal_sha256')=='76b32310416d262351666e2b3baa8f19916e87400960659ddb334b82ce5e6cde',
         'actual approved artifact label authority')
    captured=dt.datetime.fromisoformat(value['at_utc'].replace('Z','+00:00'))
    need(captured.tzinfo is not None and captured<=dt.datetime.now(dt.timezone.utc), 'actual label authority time')
    return value,{str(path):d.digest(raw)}


def labelled_render_identity(note,root,original,pdf,load,*,historical):
    expected=labelled_tex(original,historical=historical)
    directory=Path(note)/('historical-render' if historical else 'scope-render')
    need(d.read_regular(directory/'paper.tex')==expected,'exact labelled render source')
    require_pdf_envelope(pdf)
    seen={str((directory/'paper.tex').resolve()):d.digest(expected)}
    require_render_logs(directory,seen)
    observation=load('phase7_audit_policy').require_pdf_provenance(directory,root,expected,pdf,seen)
    return {'standard':'VRS-EXACT-LABELLED-MANUSCRIPT-RENDER-1',
        'source_tex_sha256':d.digest(original),'labelled_tex_sha256':d.digest(expected),
        'rendered_pdf_sha256':d.digest(pdf),'artifact_label':LABEL_TEXT,'ended_at_utc':observation['ended_at_utc'],
        'observation':binding(directory/'render-observation/RENDERER_OBSERVATION.json'),
        'inputs':seen,'certifies':False}


def _derive_labelled(root,base,authority,note,load):
    """Fresh predecessor science plus closed new artifact bytes, never a waiver."""
    current=predecessor(root,base,authority,load)
    label_authority,label_inputs=require_label_authority(root)
    run=current['run_id'];base=Path(base);note=Path(note)
    original=d.read_regular(base/HISTORICAL_TEX)
    require_self_contained_original(original)
    current_tex=d.read_regular(base/'paper.tex')
    scope_pdf=d.read_regular(note/'paper.pdf')
    historical_pdf=d.read_regular(note/(run+'-'+LABELLED_TOP_PDF))
    scope_render=labelled_render_identity(note,root,current_tex,scope_pdf,load,historical=False)
    historical_render=labelled_render_identity(note,root,original,historical_pdf,load,historical=True)
    members=archive(d.read_regular(base/'SCOPE_EVIDENCE.zip'))
    need(dict(members).get(HISTORICAL_TEX)==original and HISTORICAL_PDF not in dict(members),'exact raw historical archive source')
    # The scoped template reads only these already bound literal displays.
    for name,raw in members:
        if name.startswith('rendered/'):
            need(d.read_regular(note/'scope-render'/name)==raw,'labelled scope display differs')
            scope_render['inputs'][str((note/'scope-render'/name).resolve())]=d.digest(raw)
    expected={}
    for row in current['uploads']:
        name=d.safe_member(row['filename']);need('/'not in name and name not in expected,'closed labelled uploads')
        raw=d.read_regular(base/name);need(d.digest(raw)==row['sha256'],'predecessor upload changed')
        expected[name]=raw
    expected['paper.tex']=labelled_tex(current_tex,historical=False)
    expected['paper.pdf']=scope_pdf
    members += [(HISTORICAL_PDF,historical_pdf)]
    expected['SCOPE_EVIDENCE.zip']=d.archive_bytes(members)
    expected[run+'-'+LABELLED_TOP_PDF]=historical_pdf
    metadata=deepcopy(current['public_metadata'])
    metadata['description']='<p>'+html.escape(LABEL_TEXT,quote=False)+'</p><p>'+html.escape(run+'-Paper.pdf — '+LABEL_TEXT,quote=False)+'</p><p>'+html.escape(run+'-'+LABELLED_TOP_PDF+' — '+LABEL_TEXT,quote=False)+'</p>'+metadata.get('description','')
    expected['metadata.json']=d.raw_json(metadata)
    expected['PREDECESSOR_SCOPED_RELEASE_MANIFEST.json']=d.read_regular(base/'SCOPED_RELEASE_MANIFEST.json')
    expected['PREDECESSOR_PUBLICATION_BINDING.json']=d.read_regular(base/'PUBLICATION_BINDING.json')
    expected['PHASE7_RULE_EXECUTION.json']=d.read_regular(base/'PHASE7_RULE_EXECUTION.json')
    manifest={'standard':LABELLED_STANDARD,'run_id':run,
        'predecessor':{'path':str(base),'manifest':binding(base/'SCOPED_RELEASE_MANIFEST.json'),
                       'publication_binding':binding(base/'PUBLICATION_BINDING.json')},
        'authority':deepcopy(authority),'artifact_label':LABEL_TEXT,'label_authority':deepcopy(LABEL_AUTHORITY),
        'execution_sources':[{'name':n,'path':str(Path(root)/frozen_source_relative(n)),'sha256':h}for n,h in sorted(_FROZEN_HASHES.items())],
        'uploads':[{'filename':n,'sha256':d.digest(b)}for n,b in sorted(expected.items())],
        'archive_members':d.member_inventory(members),
        'manuscripts':[
            {'role':'UNCERTIFIED_DERIVED_SCOPED_MANUSCRIPT','filename':'paper.pdf','archive_member':None,
             'sha256':d.digest(scope_pdf),'certification':'ENTIRELY_UNCERTIFIED_ARTIFACT'},
            {'role':'UNCERTIFIED_HISTORICAL_MANUSCRIPT','filename':run+'-'+LABELLED_TOP_PDF,
             'archive_member':'SCOPE_EVIDENCE.zip!/'+HISTORICAL_PDF,'sha256':d.digest(historical_pdf),
             'certification':'ENTIRELY_UNCERTIFIED'}],
        'scope_render':scope_render,'historical_render':historical_render,
        'certifies':False,'publication_authorized':False,'ssot_writes':0,'zenodo_writes':0}
    _finish(label_inputs);_finish(scope_render['inputs']);_finish(historical_render['inputs']);_finish(current['input_bindings'])
    need(predecessor(root,base,authority,load)==current,'label predecessor changed during derivation')
    need(require_label_authority(root)[0]==label_authority,'label authority changed during derivation')
    return manifest,expected,current,metadata


def prepare_labelled(root,base,out,authority,*,render=None):
    need(render is None,'caller-selected labelled renderer forbidden')
    root=Path(root).resolve(strict=True);base=Path(base).resolve(strict=True);out=Path(out)
    need(not any(p.is_symlink()for p in(out,*out.parents)),'regular labelled output ancestry')
    out=out.resolve();need(out.is_relative_to(root/'RESEARCH_PIPELINE_v2/science_release_queue/manuscript_access')
        and not out.exists(),'new immutable labelled output required')
    with frozen_sources(root)as load:
        current=predecessor(root,base,authority,load);require_label_authority(root)
        original=d.read_regular(base/HISTORICAL_TEX);require_self_contained_original(original)
        out.mkdir(parents=True,exist_ok=False)
        members=archive(d.read_regular(base/'SCOPE_EVIDENCE.zip'))
        for name,raw in members:
            d.immutable(out/name,raw)
            if name.startswith('rendered/'):d.immutable(out/'scope-render'/name,raw)
        for historical,source,filename in [(False,d.read_regular(base/'paper.tex'),'paper.pdf'),
                                           (True,original,current['run_id']+'-'+LABELLED_TOP_PDF)]:
            directory=out/('historical-render'if historical else'scope-render')
            d.immutable(directory/'paper.tex',labelled_tex(source,historical=historical))
            pdf=native_render(directory/'paper.tex',root=root);require_pdf_envelope(pdf)
            d.immutable(out/filename,pdf)
        manifest,expected,_,_= _derive_labelled(root,base,authority,out,load)
        for name,raw in expected.items():d.immutable(out/name,raw)
        d.immutable(out/HISTORICAL_PDF,d.read_regular(out/(current['run_id']+'-'+LABELLED_TOP_PDF)))
        d.immutable(out/'SCOPED_RELEASE_MANIFEST.json',d.raw_json(manifest))
    return {'status':'LABELLED_ARTIFACT_STAGED_REVIEW_REQUIRED','manifest':binding(out/'SCOPED_RELEASE_MANIFEST.json'),
            'run_id':current['run_id'],'full_pdf_review_required':True,'certifies':False,'publication_authorized':False}


def review_labelled(root,note,authority,*,review_invocation):
    """Explicit later artifact review; never issue a scientific certificate."""
    root=Path(root).resolve(strict=True);note=Path(note).resolve(strict=True)
    need(note.is_relative_to(root)and not(note/'PUBLICATION_BINDING.json').exists(),'new canonical labelled review required')
    need(isinstance(review_invocation,str)and len(review_invocation)>=12,'actual later artifact review invocation')
    with frozen_sources(root)as load:
        manifest,expected,current,_=_derive_labelled(root,Path(json.loads(d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json'))['predecessor']['path']),authority,note,load)
        need(json.loads(d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json'))==manifest,'review exact labelled manifest')
        for name,raw in expected.items():need(d.read_regular(note/name)==raw,'review exact labelled artifact bytes')
        base=Path(manifest['predecessor']['path'])
        previous=json.loads(d.read_regular(base/'PHASE7_RULE_EXECUTION.json'))['scope_comparison']
        need(review_invocation not in {previous['current_invocation'],previous['source_selection_invocation']},'separate later artifact review')
        pb={'standard':LABELLED_BINDING_STANDARD,'status':'LABELLED_ARTIFACT_BYTES_BOUND_NOT_PUBLICATION_AUTHORIZED',
            'run_id':current['run_id'],'manifest':binding(note/'SCOPED_RELEASE_MANIFEST.json'),
            'predecessor_binding':manifest['predecessor']['publication_binding'],'authority':deepcopy(authority),
            'review_invocation':review_invocation,'issued_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'certifies':False,'publication_authorized':False}
        d.immutable(note/'PUBLICATION_BINDING.json',d.raw_json(pb))
    return require_labelled(note,root,authority)


def require_labelled(note,root,authority):
    root=Path(root).resolve(strict=True);note=Path(note).resolve(strict=True)
    need(note.is_relative_to(root),'labelled note outside canonical root')
    before=d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json');pb_before=d.read_regular(note/'PUBLICATION_BINDING.json')
    manifest=json.loads(before)
    need(isinstance(manifest,dict)and set(manifest)==LABELLED_MANIFEST_FIELDS
         and manifest.get('standard')==LABELLED_STANDARD and manifest['authority']==authority,'closed labelled manifest')
    base=Path(manifest['predecessor']['path']);need(base.resolve(strict=True)!=note,'distinct immutable label predecessor')
    with frozen_sources(root)as load:
        actual,expected,current,metadata=_derive_labelled(root,base,authority,note,load)
        need(actual==manifest,'fresh exact labelled artifact identity')
        for name,raw in expected.items():need(d.read_regular(note/name)==raw,'labelled artifact bytes differ: '+name)
        for name,raw in archive(d.read_regular(note/'SCOPE_EVIDENCE.zip')):
            need(d.read_regular(note/name)==raw,'labelled archive/local bytes differ')
        pb=json.loads(pb_before)
        need(set(pb)==LABELLED_PB_FIELDS and pb['standard']==LABELLED_BINDING_STANDARD
             and pb['status']=='LABELLED_ARTIFACT_BYTES_BOUND_NOT_PUBLICATION_AUTHORIZED'
             and pb['run_id']==manifest['run_id']and pb['authority']==authority
             and pb['manifest']==binding(note/'SCOPED_RELEASE_MANIFEST.json')
             and pb['predecessor_binding']==actual['predecessor']['publication_binding']
             and pb['certifies']is False and pb['publication_authorized']is False,'exact distinct labelled artifact binding')
        prior_review=json.loads(d.read_regular(base/'PHASE7_RULE_EXECUTION.json'))['scope_comparison']
        need(isinstance(pb['review_invocation'],str)and len(pb['review_invocation'])>=12
             and pb['review_invocation']not in{prior_review['current_invocation'],prior_review['source_selection_invocation']},'fresh later artifact review identity')
        issued=load('nightly_minimal_policy').time(pb['issued_at_utc'])
        base_pb=json.loads(d.read_regular(base/'PUBLICATION_BINDING.json'));label_auth,_=require_label_authority(root)
        need(max(load('nightly_minimal_policy').time(base_pb['issued_at_utc']),
                 load('nightly_minimal_policy').time(label_auth['at_utc']),
                 load('nightly_minimal_policy').time(actual['scope_render']['ended_at_utc']),
                 load('nightly_minimal_policy').time(actual['historical_render']['ended_at_utc']))<=issued<=dt.datetime.now(dt.timezone.utc),
             'labelled artifact after predecessor and human authority')
        need(d.read_regular(note/'SCOPED_RELEASE_MANIFEST.json')==before
             and d.read_regular(note/'PUBLICATION_BINDING.json')==pb_before,'labelled binding race')
        return {**current,'status':'PUBLICATION_BOUND','exact_publication_binding':True,
            'access_standard':LABELLED_STANDARD,'artifact_label':LABEL_TEXT,
            'manuscripts':manifest['manuscripts'],'uploads':manifest['uploads'],'public_metadata':metadata,
            'metadata_binding':next(v for v in manifest['uploads']if v['filename']=='metadata.json'),
            'policy_receipt':binding(note/'PHASE7_RULE_EXECUTION.json'),'publication_binding':binding(note/'PUBLICATION_BINDING.json'),
            'scientific_predecessor':actual['predecessor'],'certifies':False,'publication_authorized':False}

if __name__ == '__main__':
    raise SystemExit('HOLD: measured explicit preparation only; no publication authority')
