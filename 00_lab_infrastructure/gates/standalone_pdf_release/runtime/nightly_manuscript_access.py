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

if __name__ == '__main__':
    raise SystemExit('HOLD: measured explicit preparation only; no publication authority')
