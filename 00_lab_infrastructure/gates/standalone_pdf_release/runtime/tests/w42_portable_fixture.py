"""TEST ONLY: synthetic trust/provider/platform/render material, never admission.

Scientific validators and native lifetime helpers remain exact. Trust data,
path mapping and an explicit platform prerequisite substitute are TEST ONLY.
No CORE read/import, network, renderer or Lean execution occurs in these tests.
Production source SHA pins are checked before any test-specific substitutions.
"""
from __future__ import annotations
import ast
import builtins
from copy import deepcopy
import datetime as dt
import hashlib
import json
import os
import signal
import threading
from pathlib import Path
import shutil
import sys
import types
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
RUNTIME=HERE.parent
GATES=RUNTIME.parents[1]
REPO=GATES.parents[1]
sys.path.insert(0,str(RUNTIME))
import methods_digest_v2 as digest
import nightly_manuscript_access as access

AUDIT='## Phase 7 — Claude audit of release packet v002 — 2026-10-07'
DECOUPLE='## Phase 7 Gate 3 resolution: decouple probes from witnesses — 2026-10-07 (evening)'
SIMPLIFY='## SIMPLIFICATION — weekly push restored — 2026-10-07 (Justin directive; supersedes conflicting Phase 7 items)'
APPENDIX='## First Methods Digest audit + catalog provenance decision — 2026-10-08'
AUTH_REL='reports/verification-coverage/2026-10-07/phase7-approved-audit-execution-v001/authority/AUDIT_AUTHORITY.json'
MINIMAL_REL='reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/authority/AUTHORITY.json'
G='RESEARCH_PIPELINE_v2/verification_coverage_gates/'
CHECKS={'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}
FROZEN_PUBLIC_SOURCES={
    'publication_binding.py':'00_lab_infrastructure/gates/production_snapshots/phase5-20261004/after/RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py',
    'track_b.py':'00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/track_b.py',
}
PROVIDER_FUNCTION_AST_SHA256={
    'sha256_file':'fd55fbabb37965382e8715dc5b3a88c8608850e06c1387691aad233770619a61',
    'read_json':'fad7a7dbea5c6e6963a2b9ec5e263b3ee8adc45d87467ef0b4aa65e2c9a9aa08',
    'binding_is_current':'c81a442b63cc7b34e7996fc1036c4ed578e9dd52e04bee8c151a180299d43b01',
    'current_certificate':'8587ecf5eac26714040436265844d3088520f74d9704ce7645a6c466ed490f23',
}
TRUST_CONSTANT_NAMES={
    'phase7_audit_policy.py':{'PINS','AUTHORITY_SHA','MINIMAL_AUTHORITY_SHA','MINIMAL_SECTIONS','RENDERER_SHA','RENDERER_CACHE_SHA'},
    'phase7_policy_versions.py':{'APPENDIX_SHA256','SIMPLIFICATION_SHA256','DECOUPLING_SHA256'},
    'phase7_runtime_update.py':{'APPROVED_AUDIT_SECTION_SHA256','APPROVED_AUDIT_APPENDICES','PREVIOUS_SELECTOR_RECEIPT_SHA256'},
}
CANDIDATE='''import Mathlib
namespace Example
variable (a : ℝ)
theorem bounded (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) : q ≤ 1 := by exact hq1
theorem witness : (0 : ℝ) ≤ 1 := by norm_num
end Example
'''
FORMAL=CANDIDATE.replace('by exact hq1','by sorry').replace('by norm_num','by sorry')
ORIGINAL=b'\\documentclass{article}\n\\title{Synthetic historical manuscript}\n\\author{Fixture author}\n\\date{}\n\\begin{document}\n\\maketitle\nINDEPENDENT historical manuscript. All physical assumptions remain uncertified.\n\\end{document}\n'

def pdf(text):
    """Small valid one-page PDF bytes; simulated renderer output, no TeX run."""
    text=text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    stream=('BT /F1 12 Tf 36 760 Td ('+text+') Tj ET\n').encode()
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'endstream']
    result=b'%PDF-1.4\n';offsets=[0]
    for i,o in enumerate(objects,1):offsets.append(len(result));result+=str(i).encode()+b' 0 obj\n'+o+b'\nendobj\n'
    start=len(result);result+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(('%010d 00000 n \n'%n).encode()for n in offsets[1:])
    return result+b'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n'+str(start).encode()+b'\n%%EOF\n'

def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def encoded(x):return digest.raw_json(x)

def _ast_digest(node):
    # Python3.14 ast.dump omits empty fields which3.12 printed. Normalize only
    # parser-schema empties; preserve every nonempty node, field and scalar.
    def normalized(value):
        if isinstance(value,ast.AST):
            return {'_type':type(value).__name__,**{key:normalized(child)for key,child in ast.iter_fields(value)if child is not None and child!=[]}}
        if isinstance(value,list):return [normalized(child)for child in value]
        return value
    return hashlib.sha256(json.dumps(normalized(node),sort_keys=True,separators=(',',':')).encode()).hexdigest()

def _platform_builtins(binary,generation,historical_generation_literal):
    """TEST ONLY two exact platform path substitutions, never a verdict seam."""
    native=type(Path())
    class PlatformPath(native):
        @staticmethod
        def mapped(args):
            if len(args)==1:
                text=str(args[0])
                if text=='/opt/homebrew/bin/tectonic':return (str(binary),)
                if text==historical_generation_literal:return (str(generation),)
            return args
        def __new__(cls,*args,**kwargs):
            return super().__new__(cls,*cls.mapped(args),**kwargs)
        def __init__(self,*args,**kwargs):
            if native.__init__ is object.__init__:super().__init__()
            else:super().__init__(*self.mapped(args),**kwargs)
    synthetic=types.ModuleType('TEST_ONLY_BUILTINS')
    synthetic.__dict__.update(vars(builtins))
    original=builtins.__import__
    def test_import(name,globals=None,locals=None,fromlist=(),level=0):
        result=original(name,globals,locals,fromlist,level)
        if name=='pathlib':
            proxy=types.ModuleType('TEST_ONLY_PLATFORM_PATHS')
            proxy.__dict__.update(vars(result));proxy.Path=PlatformPath
            return proxy
        return result
    synthetic.__import__=test_import
    return synthetic

def _portable_renderer_prerequisites():
    """TEST ONLY platform substitution; real kernel reservation is NOT faked.

    Ubuntu3.12/3.14 synthetic-renderer semantics, not Mac/Tectonic qualification.
    Production require_native_render_supervision remains unchanged and pinned.
    Unsupported native primitives are fixture errors, never skips/mutant kills.
    """
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise RuntimeError('TEST_ONLY_DEFAULT_SIGCHLD_REQUIRED')
    if threading.active_count() != 1 or threading.current_thread() is not threading.main_thread():
        raise RuntimeError('TEST_ONLY_SINGLE_MAIN_THREAD_REQUIRED')
    if not all(hasattr(os, n) for n in ('waitid','P_PID','WNOWAIT','WEXITED','WNOHANG','waitpid','waitstatus_to_exitcode')):
        raise RuntimeError('TEST_ONLY_ACTUAL_WNOWAIT_UNAVAILABLE_NO_QUALIFICATION')
    try:
        os.waitid(os.P_PID, os.getpid(), os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return
    raise RuntimeError('TEST_ONLY_NONCHILD_PROBE_AMBIGUOUS')

class PortableFixture:
    def __init__(self,root,*,renderer_mode='normal'):
        if renderer_mode not in {'normal','timeout180'}:raise ValueError('closed TEST_ONLY renderer mode')
        self.root=Path(root).resolve();self.root.mkdir(exist_ok=True)
        self.gates=self.root/G;self.gates.mkdir(parents=True)
        self.seed=json.loads((HERE/'fixtures/w42_trust_seed.json').read_bytes())
        self.production_native_prerequisite=access.require_native_render_supervision
        self.original_source_hashes=deepcopy(access._FROZEN_HASHES)
        self.original_source_bytes={}
        self.constant_overrides={}
        # First prove every unmodified production raw source against its pin.
        for name,h in self.original_source_hashes.items():
            path=REPO/FROZEN_PUBLIC_SOURCES[name] if name in FROZEN_PUBLIC_SOURCES else GATES/name
            raw=path.read_bytes();assert digest.digest(raw)==h,name
            self.original_source_bytes[name]=raw
            self.write(access.frozen_source_relative(name),raw)
        parity_tree=ast.parse(self.read(G+'mirror_parity.py'))
        self.historical_generation_literal=next(ast.literal_eval(n.value.args[0])for n in parity_tree.body
            if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='GENERATION_ROOT'for t in n.targets))
        self.gen=self.root/'simulated-generation';self.gen.mkdir()
        self.binary=self.root/'simulated-platform/tectonic'
        # An explicit simulated platform executable exercises the real current
        # subprocess/provenance body; its bytes are TEST DATA, never production.
        pdf_source=ast.get_source_segment(Path(__file__).read_text(),next(n for n in ast.parse(Path(__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='pdf'))
        script=('#!'+sys.executable+'\nimport hashlib,sys\nfrom pathlib import Path\n'+pdf_source+'\n'
                +"out=Path(sys.argv[sys.argv.index('--outdir')+1]);out.mkdir(exist_ok=True)\n"
                +"raw=Path('paper.tex').read_bytes();(out/'paper.pdf').write_bytes(pdf('SIMULATED '+hashlib.sha256(raw).hexdigest()))\n")
        if renderer_mode=='timeout180':
            script='#!'+sys.executable+'\nimport time\ntime.sleep(220)\n'
        self.write(self.binary,script.encode());self.binary.chmod(0o700)
        cache=self.root/'simulated-cache';cache.mkdir()
        cachefiles={}
        for i in range(556):
            name='asset-%03d.dat'%i;raw=('TEST_ONLY_CACHE_ASSET_%03d'%i).encode();self.write(cache/name,raw);cachefiles[name]=digest.digest(raw)
        self.cache=self.put('simulated-platform/CACHE.json',{'schema':'VRS-PHASE7-TECTONIC-CACHE-1','cache_root':str(cache),'files':cachefiles})
        self.label_authority=self.put('synthetic-trust/LABEL_AUTHORITY.json',{'fixture':'SIMULATED_AUTHORITY_NOT_A_LIVE_GRANT','answer':'Approve artifact-specific wording','approved_text':access.LABEL_TEXT,'proposal_sha256':'76b32310416d262351666e2b3baa8f19916e87400960659ddb334b82ce5e6cde','at_utc':'2026-10-14T00:00:00Z'})
        self.sections={header:(header+'\nTEST ONLY SYNTHETIC TRUST SECTION; NOT JUSTIN AUTHORITY.').encode()for header in [AUDIT,DECOUPLE,SIMPLIFY,APPENDIX]}
        self.write('reports/verification-coverage/GAME_PLAN.md',b'\n'.join(self.sections.values()))
        audit=self.put('synthetic-trust/AUDIT.md',self.sections[AUDIT]);md=self.put('synthetic-trust/PACKET.md',b'TEST ONLY56 IDENTITIES\n')
        packet=self.put('synthetic-trust/PACKET.json',{'rows':[{'run_id':'Run-%03d'%i}for i in range(100,156)]})
        covered=self.put('synthetic-trust/COVERED.txt',b'TEST_ONLY_BOUND_INPUT\n')
        inventory=self.put('synthetic-trust/INPUTS.json',{'file_count':1,'files':[{'path':covered['path'],'relative_path':'COVERED.txt','sha256':covered['sha256'],'bytes':len(self.read(covered['path']))}]})
        pins={'audit_section':audit['sha256'],'audited_packet_md':md['sha256'],'audited_packet_json':packet['sha256'],'audited_input_manifest':inventory['sha256']}
        # AUTHORITY_SOURCE literal stays exact in the validator; the path/hash
        # authority is a declared simulated provider fixture, never a live grant.
        source='Justin approved actual named GAME_PLAN audit section; execution is mechanical rule application, no fabricated Claude model/review timestamp'
        self.authority=self.put(AUTH_REL,{'standard':'VRS_PHASE7_CLAUDE_AUDIT_RULE_EXECUTION_1','status':'APPROVED_RULE_AUTHORITY','tree_root':str(self.root),'audit_section':audit,'audited_packet_md':md,'audited_packet_json':packet,'audited_input_manifest':inventory,'assembly_observed_at_utc':'2026-10-01T00:00:00Z','authority_source':source})
        minimal=[]
        for name,header in [('DECOUPLING_SECTION.md',DECOUPLE),('SIMPLIFICATION_SECTION.md',SIMPLIFY)]:
            self.put(str(Path(MINIMAL_REL).parent/name),self.sections[header]);minimal.append({'path':name,'sha256':digest.digest(self.sections[header])})
        minauth=self.put(MINIMAL_REL,{'standard':'VRS-PHASE7-APPROVED-DECOUPLING-1','approved_by':'Justin','new_review_fabricated':False,'local_lean_execution':False,'captured_at_utc':'2026-10-01T00:00:00Z','original_audit_section':audit,'sections':minimal})
        self.audit_constants={'PINS':pins,'AUTHORITY_SHA':self.authority['sha256'],'MINIMAL_AUTHORITY_SHA':minauth['sha256'],
            'MINIMAL_SECTIONS':tuple((name,header,digest.digest(self.sections[header]))for name,header in [('DECOUPLING_SECTION.md',DECOUPLE),('SIMPLIFICATION_SECTION.md',SIMPLIFY)]),
            'RENDERER_SHA':digest.sha(self.binary),'RENDERER_CACHE_SHA':self.cache['sha256']}
        self.version_constants={'APPENDIX_SHA256':digest.digest(self.sections[APPENDIX]),'SIMPLIFICATION_SHA256':digest.digest(self.sections[SIMPLIFY]),'DECOUPLING_SHA256':digest.digest(self.sections[DECOUPLE])}
        self.append_constants('phase7_audit_policy.py',self.audit_constants)
        self.append_constants('phase7_policy_versions.py',self.version_constants)
        self.runtime_trust(audit)
        self.test_hashes={name:digest.sha(self.root/access.frozen_source_relative(name))for name in self.original_source_hashes}
        self.install_current_fixture()
        self.scientific_fixture()

    def read(self,name):return (self.root/name).read_bytes()
    def write(self,name,raw):
        p=Path(name);p=p if p.is_absolute()else self.root/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);return p
    def put(self,name,value):
        p=self.write(name,value if isinstance(value,bytes)else encoded(value));return {'path':str(p),'sha256':digest.sha(p)}
    def relbound(self,name):return {'path':str(Path(name).relative_to(self.root))if Path(name).is_absolute()else str(name),'sha256':digest.sha(self.root/name)}
    def source(self,row):
        if 'fixture_bytes'in row:return row['fixture_bytes'].encode()
        p=REPO/row['repository_path'];raw=p.read_bytes();assert digest.digest(raw)==row['sha256'];return raw
    def append_constants(self,name,values):
        assert set(values)<=TRUST_CONSTANT_NAMES[name],(name,values)
        self.constant_overrides.setdefault(name,{}).update(deepcopy(values))
        p=self.gates/name;p.write_bytes(p.read_bytes()+b'\n# TEST ONLY synthetic trust constants; validator bodies unchanged.\n'+''.join(k+' = '+repr(v)+'\n'for k,v in values.items()).encode())
    def pr(self,number,files,oid=None):
        return {'fixture':'SIMULATED_PROVIDER_NOT_GITHUB_EVIDENCE','state':'MERGED','baseRefName':'main','number':number,'url':'https://github.com/jdhart81/viridis-canon/pull/'+str(number),'mergeCommit':{'oid':oid or 'a'*40},'statusCheckRollup':[{'name':n,'status':'COMPLETED','conclusion':'SUCCESS'}for n in sorted(CHECKS)],'files':files}
    def runtime_trust(self,audit):
        # Minimal closed DATA chain; all actual runtime validator branches run.
        previous=deepcopy(self.seed['previous']);current=deepcopy(self.seed['current'])
        for label,r in [('previous',previous),('current',current)]:
            for row in r['runtime_targets']+r['additional_modules']:
                raw=self.source(row['source'])
                capture='synthetic-trust/'+label+'/'+row['path']
                row['source']=self.relbound(self.write(capture,raw))
                if label=='current' and row['path'].endswith('.py') and not(self.root/row['path']).exists():self.write(row['path'],raw)
        # Actual target sources replace none of the current measured gate bytes.
        for row in current['runtime_targets']:
            if (self.root/row['path']).exists():
                assert digest.sha(self.root/row['path'])==row['after_sha256'],row['path']
            else:self.write(row['path'],self.read(row['source']['path']))
        baseline=self.put('synthetic-trust/BASELINE.json',{'fixture':True})
        checks=[{'path':'/simulated/protected/'+str(i),'surface':'SIMULATED','expected_sha256':digest.digest(str(i).encode()),'actual_sha256':digest.digest(str(i).encode()),'match':True}for i in range(22)]
        protected={'status':'LIVE_PROTECTED_HASH_READBACK_PASS','at_utc':'2026-10-14T00:00:00Z','baseline_sha256':baseline['sha256'],'remote_script_writes':0,'restarts':0,'certification_attempts':0,'checks':checks}
        protected_b=self.put('synthetic-trust/PROTECTED.json',protected)
        after=self.put('synthetic-trust/AFTER.json',self.seed['original_after_manifest'])
        original={'activated_at_utc':'2026-10-01T00:00:00Z','proofs':{'after_manifest':self.relbound(after['path']),'protected_baseline':self.relbound(baseline['path'])},'sources':{'protected_readback':self.relbound(protected_b['path'])}}
        original_b=self.put('synthetic-trust/ORIGINAL.json',original)
        selectorfiles=[{'path':'00_lab_infrastructure/gates/'+Path(row['path']).name,'sha':blob(self.read(row['source']['path']))}for row in previous['runtime_targets']]
        selector=self.put('synthetic-trust/PR55.json',self.pr(55,selectorfiles,'bd7746b8fe01a8ede95db27cd553978fb4733dbb'))
        priorfiles=selectorfiles+[{'path':'00_lab_infrastructure/gates/'+Path(row['path']).name,'sha':blob(self.read(row['source']['path']))}for row in previous['additional_modules']]
        priorpr=self.put('synthetic-trust/PR57.json',self.pr(57,priorfiles,'cb76d964121878031f2693f56cd21908d291b1d5'))
        common={'tree_root':str(self.root),'original_activation':self.relbound(original_b['path']),'original_after_manifest':self.relbound(after['path']),'audit_section':self.relbound(audit['path']),'selector_pull_request_readback':self.relbound(selector['path']),'protected_readback':self.relbound(protected_b['path'])}
        previous.update(common,pull_request_readback=self.relbound(priorpr['path']))
        priorb=self.put('synthetic-trust/PREVIOUS_RUNTIME.json',previous)
        self.append_constants('phase7_runtime_update.py',{'APPROVED_AUDIT_SECTION_SHA256':audit['sha256'],
            'APPROVED_AUDIT_APPENDICES':tuple((h,digest.digest(self.sections[h]))for h in [DECOUPLE,SIMPLIFY]),
            'PREVIOUS_SELECTOR_RECEIPT_SHA256':priorb['sha256']})
        current.update(common,previous_runtime_update=self.relbound(priorb['path']))
        for key in ['publication_gate_scoped_baseline','public_metadata_readback_baseline']:
            current[key]=self.relbound(self.write('synthetic-trust/'+key+'.py',self.source(self.seed[key])))
        # Exactly one simulated policy version, with the unchanged real eight
        # source bodies and test trust constants. No version verdict is stubbed.
        names={'phase7_audit_policy.py','PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','methods_digest.py','publication_gate.py'}
        for row in current['additional_modules']:
            if Path(row['path']).name=='PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json':self.write(row['path'],self.read(row['source']['path']))
        version=digest.sha(self.gates/'phase7_audit_policy.py');files=[];prfiles=[]
        for name in sorted(names):
            rel=G+'policy_versions/'+version+'/'+name;raw=self.read(G+name);self.write(rel,raw)
            git='00_lab_infrastructure/gates/policy_versions/'+version+'/'+name
            files.append({'name':name,'binding':self.relbound(rel),'git_path':git});prfiles.append({'path':git,'sha':blob(raw)})
        archivepr=self.put('synthetic-trust/ARCHIVE_PR.json',self.pr(998,prfiles))
        catalog=self.put('synthetic-trust/CATALOG.json',{'standard':'VRS-PHASE7-POLICY-VERSIONS-1','status':'MERGED_SOURCE_CATALOG','tree_root':str(self.root),'versions':[{'execution_consumer_sha256':version,'files':files,'pull_request_readback':self.relbound(archivepr['path'])}]})
        current['policy_version_catalog']=self.relbound(catalog['path'])
        module_names={Path(r['path']).name for r in current['additional_modules']if '/policy_versions/'not in r['path']}
        current['additional_modules']=[]
        for rel in sorted([G+n for n in module_names]+[f['binding']['path']for f in files]):
            raw=self.read(rel);source=self.write('synthetic-trust/current-source/'+rel,raw)
            current['additional_modules'].append({'path':rel,'sha256':digest.digest(raw),'source':self.relbound(source)})
            prfiles.append({'path':'00_lab_infrastructure/gates/'+rel[len(G):],'sha':blob(raw)})
        for row in current['runtime_targets']:
            prfiles.append({'path':'00_lab_infrastructure/gates/'+Path(row['path']).name,'sha':blob(self.read(row['source']['path']))})
        # Duplicate Git paths from the version catalog are one exact row.
        prfiles=list({r['path']:r for r in prfiles}.values())
        merged=self.put('synthetic-trust/CURRENT_PR.json',self.pr(999,prfiles))
        current['pull_request_readback']=self.relbound(merged['path'])
        update=self.put('synthetic-trust/CURRENT_RUNTIME.json',current)
        wrapper=self.put('synthetic-trust/ACTIVATION.json',{**original,'authorized_runtime_update':self.relbound(update['path'])})
        self.ledger={'tree_root':str(self.root),'enforcement_activation':self.relbound(wrapper['path']),'run_entities':[],'publication_entities':[]}
        self.put('RESEARCH_PIPELINE_v2/corpus_ledger.json',self.ledger)

    def install_current_fixture(self):
        previous=os.environ.get('VIRIDIS_CORE_ROOT')
        os.environ['VIRIDIS_CORE_ROOT']=str(self.root)
        try:
            import packaging_runtime as runtime
        finally:
            if previous is None:os.environ.pop('VIRIDIS_CORE_ROOT',None)
            else:os.environ['VIRIDIS_CORE_ROOT']=previous
        directory=self.root/'_ZENODO_DEPOSITS/standalone_pdf_runtime';directory.mkdir(parents=True)
        rows=[]
        for name in sorted(runtime.MODULE_NAMES):
            raw=(RUNTIME/name).read_bytes();p=self.write(directory/name,raw)
            rows.append({'name':name,'path':str(p),'sha256':digest.digest(raw),'git_path':runtime.GIT_PREFIX+name})
        # Current access source itself remains unchanged; only its frozen trust
        # map is test-local data, installed in this simulated source copy.
        p=directory/'nightly_manuscript_access.py'
        self.installed_access_original=p.read_bytes()
        platform=next(n for n in ast.parse(Path(__file__).read_bytes()).body
            if isinstance(n,ast.FunctionDef)and n.name=='_platform_builtins')
        portable=next(n for n in ast.parse(Path(__file__).read_bytes()).body
            if isinstance(n,ast.FunctionDef)and n.name=='_portable_renderer_prerequisites')
        supplement=('\n# TEST ONLY trust/platform; native prerequisite override is explicit, not Mac qualification.\n'
            +'_FROZEN_HASHES = '+repr(self.test_hashes)+'\n'
            +'LABEL_AUTHORITY = '+repr(self.label_authority)+'\n'
            +'NATIVE_RENDERER = '+repr(str(self.binary))+'\n'
            +'RENDER_CACHE = '+repr(self.cache)+'\n'
            +ast.unparse(platform)+'\n'+ast.unparse(portable)+'\n'
            +'require_native_render_supervision = _portable_renderer_prerequisites\n'
            +'builtins = _platform_builtins('+repr(str(self.binary))+','+repr(str(self.gen))+','+repr(self.historical_generation_literal)+')\n')
        p.write_bytes(p.read_bytes()+supplement.encode())
        next(r for r in rows if r['name']==p.name)['sha256']=digest.sha(p)
        dummy=self.put('synthetic-trust/INSTALL_REVIEW.json',{'fixture':'NOT_AN_INSTALLATION'})
        profile=self.put(runtime.PROFILE_PATH,{'standard':runtime.STANDARD,'note_preparation':getattr(runtime,'NOTE_PREPARATION',{}),'modules':rows})
        self.put(runtime.NOMINATION_PATH,{'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-'+('13'if hasattr(runtime,'NOTE_PREPARATION')else'12'),'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING','profile':profile,'installer_source':dummy,'merged_source_commit':'a'*40,'root_review_receipt':dummy})

    def structural_readback(self):
        """Prove original source prefixes/ASTs and disclose every test override."""
        rows=[]
        for name,original in self.original_source_bytes.items():
            actual=self.read(access.frozen_source_relative(name))
            assert actual.startswith(original),name
            old=ast.parse(original);new=ast.parse(actual)
            assert ast.dump(ast.Module(body=old.body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=new.body[:len(old.body)],type_ignores=[]),include_attributes=False),name
            suffix=new.body[len(old.body):]
            names=[]
            for node in suffix:
                assert isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name),name
                key=node.targets[0].id;names.append(key)
                assert key in TRUST_CONSTANT_NAMES.get(name,set()),(name,key)
                assert ast.literal_eval(node.value)==self.constant_overrides[name][key],(name,key)
            rows.append({'name':name,'production_sha256':digest.digest(original),'test_copy_sha256':digest.digest(actual),
                'original_bytes_and_all_AST_nodes_preserved':True,'appended_trust_constant_names':names,
                'public_source':FROZEN_PUBLIC_SOURCES.get(name,'00_lab_infrastructure/gates/'+name),
                'canonical_fixture_relative_origin':access.frozen_source_relative(name)})
        provider=ast.parse((HERE/'fixtures/w42_proof_provider.py').read_bytes())
        for name,expected in PROVIDER_FUNCTION_AST_SHA256.items():
            node=next(n for n in provider.body if isinstance(n,ast.FunctionDef)and n.name==name)
            assert _ast_digest(node)==expected,name
        installed=self.read('_ZENODO_DEPOSITS/standalone_pdf_runtime/nightly_manuscript_access.py')
        assert installed.startswith(self.installed_access_original)
        old=ast.parse(self.installed_access_original);new=ast.parse(installed)
        assert ast.dump(ast.Module(body=old.body,type_ignores=[]),include_attributes=False)==ast.dump(ast.Module(body=new.body[:len(old.body)],type_ignores=[]),include_attributes=False)
        return {'standard':'TEST_ONLY_REAL_VALIDATOR_BODY_EQUIVALENCE_1','source_rows':rows,
            'provider_function_AST_sha256':PROVIDER_FUNCTION_AST_SHA256,
            'installed_access_production_prefix_sha256':digest.digest(self.installed_access_original),
            'installed_access_original_bytes_and_AST_preserved':True,
            'platform_mapping':'Exactly pinned mirror_parity.GENERATION_ROOT literal and exact /opt/homebrew/bin/tectonic; no prefix/suffix mapping',
            'simulated_platform_renderer_cache_and_provider_not_production_evidence':True,
            'TEST_ONLY_native_platform_prerequisite_override':True,'actual_waitid_reservation_signal_reap_helpers_unchanged':True,'Mac_native_qualification':False,'mocked_validator_or_PB_outputs':False,'genuine_complete_packaging_session':'NOT_ESTABLISHED'}

    def scientific_fixture(self):
        # A source-only provider fixture implements ordinary binding selection;
        # raw simulated Comparator evidence still faces the real inspector and
        # unchanged issuer's validate_comparator_witness_evidence function.
        self.write('RESEARCH_PIPELINE_v2/nightly_proof_track.py',(HERE/'fixtures/w42_proof_provider.py').read_bytes())
        deploy=REPO/'comparator-deploy'
        for name in ['issue_lean_zero_sorry_certificate.py','engine3_align_challenge.py','job_observation_policy.py']:
            self.write('RESEARCH_PIPELINE_v2/'+name,(deploy/name).read_bytes())
        # Imported issuer dependencies are public reviewed test source files.
        sys.path.insert(0,str(self.root/'RESEARCH_PIPELINE_v2'))
        self.run='Run-191';runpath='science-engine/07_nightly_engine/compound research papers/'+self.run
        self.write(runpath+'/paper.tex',ORIGINAL);self.write(self.gen/'07_nightly_engine/compound research papers'/self.run/'paper.tex',ORIGINAL)
        attempt='RESEARCH_PIPELINE_v2/lean_certificates/'+self.run
        candidate=self.put(attempt+'/CANDIDATE.lean',CANDIDATE.encode());formal=self.put(attempt+'/STATEMENT.lean',FORMAL.encode())
        sealed={}
        for name,raw in {'SEALED_paper.tex':ORIGINAL,'SEALED_paper.pdf':pdf('SIMULATED historical original'),'SEALED_CLAIM_INVENTORY.json':encoded({'claims':[],'foundation_basis':'INDEPENDENT'}),'SEALED_RUN_MANIFEST.json':encoded({'source_run':self.run,'foundation_basis':'INDEPENDENT'})}.items():sealed[name]=self.put(attempt+'/'+name,raw)
        inputs={Path(b['path']).name:b['sha256']for b in [candidate,formal,*sealed.values()]}
        request=self.put(attempt+'/REQUEST.json',{'request_kind':'LEAN_PROOF','source_run':self.run,'candidate_id':'TEST_ONLY_SIMULATED_PROVIDER','expected_theorem_names':['bounded','witness'],'nonvacuity_obligations':['witness'],'toolchain':'leanprover/lean4:v4.28.0','mathlib_rev':'8f9d9cff6bd728b17a24e163c9402775d9e6a365','input_sha256':inputs})
        response={'type':'verification-ok','project':'viridis-lean-4.28','theoremNames':['bounded','witness'],'output':'Nanoda kernel accepts the solution\nLean default kernel accepts the solution\nYour solution is okay!','fixture':'SIMULATED_PROVIDER_NOT_VERIFICATION'}
        cloud=self.put(attempt+'/CLOUD.json',{'status':'VERIFIED','provider':'VIRIDIS_COMPARATOR_CLOUD','project':'viridis-lean-4.28','local_lean_execution':False,'request':request,'candidate':candidate,'formal_statement':formal,'contract':{'candidate_id':'TEST_ONLY_SIMULATED_PROVIDER','expected_theorem_names':['bounded','witness'],'permitted_axioms':['propext','Quot.sound','Classical.choice'],'named_nonvacuity_obligations':['witness']},'checks':{n:True for n in ['comparator_accepted','nanoda_kernel_accepted','lean_kernel_accepted','solution_ok_terminal','candidate_forbidden_constructs_empty','contract_declarations_present','targeted_export_complete']},'provider_response':response,'provider_response_sha256':hashlib.sha256((json.dumps(response,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()})
        gates={n:True for n in ['allowed_axioms_only','zero_sorries_or_admits','nonvacuity_witnesses','frozen_statement_and_candidate_hash_bound','independent_cloud_kernel_verification','comparator_lean_kernel','comparator_nanoda_kernel','comparator_statement_identity']};gates['local_lean_execution']=False
        self.certificate=self.put(attempt+'/LEAN_ZERO_SORRY_CERTIFICATE.json',{'standard':'VRS-LEAN-ZERO-SORRY-CERTIFICATE-1','status':'LEAN_ZERO_SORRY_CERTIFIED','run_id':self.run,'candidate_id':'TEST_ONLY_SIMULATED_PROVIDER','issued_at_utc':'2026-10-01T00:00:00Z','verification_standard':'VRS-COMPARATOR-DUAL-KERNEL-1','foundation_basis':'INDEPENDENT','gates':gates,'bindings':{'request':request,'independent_cloud_receipt':cloud,'candidate_proof':candidate,'formal_statement':formal,'sealed_paper_inputs':sealed}})
        self.before_metadata=self.put('synthetic-trust/BEFORE_METADATA.json',{'title':'Historical title unchanged','description':'Entire historical original is uncertified.','creators':[{'name':'Synthetic fixture author'}],'license':'cc-by-4.0','access_right':'open'})
        checkpoint=self.put('synthetic-trust/CHECKPOINT.json',{'fixture':'SIMULATED_PRIOR_CHECKPOINT_NO_PROGRESS_CLAIM'})
        self.cycle=self.put('synthetic-trust/CYCLE.json',{'observed_at_utc':'2026-10-01T01:00:00Z','local_lean_execution':False,'checkpoint':checkpoint,'run_flows':[{'id':self.run}]})
        with self.context():
            with access.frozen_sources(self.root)as load:
                parity=load('mirror_parity').run_parity(self.root,runpath)
                assert parity['status']=='MATCH',parity
                self.ledger['run_entities']=[{'id':self.run,'path':runpath,'status':'CERTIFIED','certificate_valid':True,'certificate':self.certificate['path'],'certified_theorems':['bounded','witness'],'nonvacuity':['witness'],'parity':parity}]
                self.put('RESEARCH_PIPELINE_v2/corpus_ledger.json',self.ledger)
                inspection=load('certificate_inspection').inspect_certificate(Path(self.certificate['path']),self.root)
                assert inspection['valid'],inspection

    def context(self):
        fixture=self
        synthetic=_platform_builtins(self.binary,self.gen,self.historical_generation_literal)
        class Scope:
            def __enter__(self):
                self.patches=[patch.object(access,'require_native_render_supervision',_portable_renderer_prerequisites),patch.object(access,'_FROZEN_HASHES',fixture.test_hashes),patch.object(access,'builtins',synthetic),patch.object(access,'LABEL_AUTHORITY',fixture.label_authority),patch.object(access,'NATIVE_RENDERER',str(fixture.binary)),patch.object(access,'RENDER_CACHE',fixture.cache)]
                for p in self.patches:p.start()
            def __exit__(self,*args):
                for p in reversed(self.patches):p.stop()
        return Scope()

    def render(self,tex,*,root):
        raw=Path(tex).read_bytes();result=pdf('SIMULATED '+digest.digest(raw))
        directory=Path(tex).parent/'render-observation';self.write(directory/'paper.pdf',result)
        self.put(directory/'RENDERER_OBSERVATION.json',{'source_tex_sha256':digest.digest(raw),'rendered_pdf_sha256':digest.digest(result),'command':['/opt/homebrew/bin/tectonic','--only-cached','--keep-logs','--outdir',str(directory),'paper.tex'],'renderer_binary':{'invoked_path':'/opt/homebrew/bin/tectonic','resolved_path':str(self.binary),'sha256':digest.sha(self.binary)},'cache_manifest':self.cache,'cache_file_count':556,'cache_and_binary_exact_after':True,'started_at_utc':'2026-10-15T00:00:00Z','ended_at_utc':'2026-10-15T00:00:01Z','returncode':0,'network_resource_fetch_disabled':True,'no_env_or_stdin_or_credentials_captured':True,'local_lean_execution':False})
        return result

    def account_discovery(self,week='2026-W42'):
        """Simulated complete double-pass DATA; the real selector must consume it.

        No HTTP took place. The empty test account is deliberately local fixture
        material, never a claim about a real owned Zenodo account.
        """
        passes=[]
        for label in ['first','second']:
            response=self.put('simulated-account/'+label+'-response.json',
                {'hits':{'total':{'value':0,'relation':'eq'},'hits':[]}})
            receipt=self.put('simulated-account/'+label+'-get.json',{
                'standard':'VRS-PHASE7-READONLY-ACCOUNT-GET-1','method':'GET',
                'url':'https://zenodo.org/api/user/records?page=1&size=100',
                'status':'RAW_ACCOUNT_GET_CAPTURED_NOT_COMPLETE','http_status':200,
                'response_path':response['path'],'response_sha256':response['sha256'],
                'response_bytes':len(self.read(response['path'])),
                'fixture':'SIMULATED_ACCOUNT_DATA_NO_HTTP'})
            passes.append([receipt])
        records=self.put('simulated-account/records.json',{'records':[]})
        with self.context(),access.frozen_sources(self.root)as load:
            weekly=load('digest_weekly_state')
            proof={'standard':'VRS-OWNED-WEEKLY-DISCOVERY-1','release_week':week,
                'record_id':None,'concept_id':None,'passes':passes,'records':records,
                'record_count':0,'producer_sha256':weekly.OWNED_DISCOVERY_PRODUCER_SHA,
                'writes':0,'start_kind':'CREATE_WEEK'}
            result=weekly.require_account_discovery(proof,root=self.root)
            assert result['status']=='NO_EXISTING_WEEKLY_RECORD',result
        return self.put('simulated-account/DISCOVERY.json',proof)

    def base_note(self):
        out=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/base/Run-191'
        with self.context():
            with access.frozen_sources(self.root)as load:
                checkpoint=load('nightly_release_checkpoint')
                pins=[{'name':n,'path':str(self.root/access.frozen_source_relative(n)),'sha256':h}for n,h in self.test_hashes.items()]
                source=checkpoint.source_for_cycle(self.root,self.run,self.cycle,self.before_metadata,pins,selection_invocation='TEST_ONLY_SOURCE_INVOCATION',selected_theorems=['bounded'],selection_at_utc='2026-10-14T00:00:00Z')
                load('prepare_nightly_note').prepare_source(self.root,out,source,render=self.render)
                result=checkpoint.review_checkpoint(self.root,out,self.authority,review_invocation='TEST_ONLY_LATER_REVIEW_INVOCATION')
                assert result['status']=='ACTUAL_DEFAULT_NIGHTLY_MINIMAL_SCOPE_BINDING_PASS',result
        return out
