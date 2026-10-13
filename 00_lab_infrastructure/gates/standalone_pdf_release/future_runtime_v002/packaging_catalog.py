"""Explicit additive registrar dispatch for current default corpus/DOI reads.

No monkeypatch or hidden scientific consumer replacement. Every v1 row stays
on its exact old default route; only truthfully v3-bound rows take the new route.
The wrapper returns a proposal and performs no canonical write itself.
"""
from __future__ import annotations
from copy import deepcopy
import importlib
import hashlib
import argparse
import urllib.request
import json
from pathlib import Path
import contextlib
import contextvars
import functools
import time
import os
import sys

import packaging_runtime as runtime

OBSERVATION_SECONDS = 900

_OPERATION = contextvars.ContextVar('exact_packaging_operation', default=None)

_SCIENCE = contextvars.ContextVar('exact_scientific_input_operation', default=None)
_READ_CAPTURE = contextvars.ContextVar('exact_scientific_read_capture', default=None)
_HASHING = contextvars.ContextVar('observer_internal_hash_read', default=False)


class ScientificInputData:
    """One operation's observed scan DATA; every reused byte is rechecked.

    The original scanner runs once. Original registry/science predicates run
    again over its unchanged data. There is no stored admission/PASS verdict.
    Every actual read, including sibling mirror inputs and absent read targets,
    is observed without replacing any original reader or function body.
    """
    def __init__(self,root,context):
        self.root=Path(root).resolve(strict=True);self.context=context
        self.inputs={};self.scan_data=None;self.inventory_reader=None;self.inventory=None
        self.pending_cas=None;self.manifest=None;self.final_manifest=None;self.depth=0;self.cas_events=[]
    def record(self,path):
        if isinstance(path,int):
            stat=os.fstat(path)
            matched=[r for r in self.inputs.values()if r.get('exists')is True
                     and (r['inode'],r['bytes'],r['mtime_ns'])==(stat.st_ino,stat.st_size,stat.st_mtime_ns)]
            runtime.need(bool(matched)and len({r['sha256']for r in matched})==1,
                         'SCIENTIFIC_UNBOUND_READ_DESCRIPTOR')
            for row in matched:self.record(row['path'])
            return
        path=Path(os.fsdecode(path)).absolute()
        token=_HASHING.set(True)
        try:
            runtime.need('..'not in path.parts and not any(p.is_symlink()for p in(path,*path.parents)),
                         'SCIENTIFIC_INPUT_REGULAR_PATH')
            if not path.exists():row={'path':str(path),'exists':False}
            else:
                if not path.is_file():return
                first=path.stat();raw=path.read_bytes();last=path.stat()
                runtime.need((first.st_ino,first.st_size,first.st_mtime_ns)==(last.st_ino,last.st_size,last.st_mtime_ns),
                             'SCIENTIFIC_INPUT_READ_RACE')
                row={'path':str(path),'exists':True,'sha256':runtime.sha(raw),
                     'inode':last.st_ino,'bytes':last.st_size,'mtime_ns':last.st_mtime_ns}
            old=self.inputs.get(str(path))
            if old is not None and old!=row:
                allowed=self.pending_cas
                runtime.need(allowed is not None and str(path)==allowed['path']
                             and old.get('sha256')==allowed['before']and row.get('sha256')==allowed['after'],
                             'SCIENTIFIC_INPUT_CHANGED:'+str(path))
            self.inputs[str(path)]=row
        finally:_HASHING.reset(token)
    def capture_inventory(self,corpus,certificates,previous=None):
        def entry(path):
            kind='SYMLINK'if path.is_symlink()else'DIRECTORY'if path.is_dir()else'FILE'if path.is_file()else'OTHER'
            return {'path':str(path.absolute()),'kind':kind}
        def run_entries(directory):
            result=[]
            for run in sorted(directory.glob('Run-*')):
                result.append(entry(run))
                if run.is_dir()and not run.is_symlink():result.extend(entry(p)for p in sorted(run.rglob('*')))
            return result
        # Freeze the complete actual predecessor artifact root set before the
        # scan. Its metadata bytes remain observed; only an admitted canonical
        # CAS may change that ledger. Newly intaken Run inputs are already in
        # the complete Run inventory and freshly classified before that CAS.
        canonical=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        registered=json.loads(canonical.read_bytes()).get('publication_entities',[])if canonical.is_file()else[]
        artifacts=[]
        for row in [*registered,*(previous or{}).get('publication_entities',[])]:
            artifact=(self.root/row['path']).absolute()
            runtime.need(artifact.is_relative_to(self.root)and'..'not in artifact.parts,'SCIENTIFIC_PUBLICATION_ARTIFACT_ROOT')
            if artifact not in artifacts:artifacts.append(artifact)
        def inventory():
            paths,errors,excluded=corpus.discover(self.root)
            papers=self.root/'science-engine/07_nightly_engine/compound research papers'
            mirror=Path(corpus.GENERATION_ROOT)
            source_papers=mirror/'07_nightly_engine/compound research papers'
            reviews=mirror/'nightly_reviews'
            artifact_entries=[]
            for artifact in sorted(artifacts):
                artifact_entries.append(entry(artifact))
                if artifact.is_dir()and not artifact.is_symlink():artifact_entries.extend(entry(p)for p in sorted(artifact.rglob('*')))
            return {'lean_paths':[str(p.absolute())for p in paths],'discover_errors':errors,'excluded':excluded,
                    'certificate_files':sorted(str(p.absolute())for p in Path(certificates).rglob('*.json')),
                    'paper_run_entries':run_entries(papers),'mirror_run_entries':run_entries(source_papers),
                    'mirror_review_entries':[entry(p)for p in sorted(reviews.rglob('*'))],
                    'registered_publication_artifact_entries':artifact_entries}
        self.inventory_reader=inventory;self.inventory=inventory()
    def assert_current(self):
        for path in list(self.inputs):self.record(path)
        if self.inventory_reader is not None:
            runtime.need(self.inventory_reader()==self.inventory,'SCIENTIFIC_INPUT_INVENTORY_CHANGED')
    def retain_manifest(self):
        output=getattr(self.context,'owner_evidence_directory',None)
        if output is None:return
        self.assert_current();path=Path(output)/'SCIENTIFIC_INPUT_DATA_MANIFEST.json'
        value={'standard':'VRS-ONE-OPERATION-SCIENTIFIC-INPUT-DATA-1','scope':'THIS_ACTIVE_OPERATION_ONLY',
               'data_only':True,'admission_cached':False,'inputs':list(self.inputs.values()),
               'inventory':self.inventory,'captured_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
        token=_HASHING.set(True)
        try:
            with path.open('x')as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n')
            self.manifest={'path':str(path),'sha256':runtime.sha(path.read_bytes())}
        finally:_HASHING.reset(token)
    def authorize_cas(self,path,before,after):
        self.assert_current();path=Path(path).resolve(strict=True)
        runtime.need(path==self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'and self.pending_cas is None,
                     'SCIENTIFIC_CANONICAL_CAS_ONLY')
        self.pending_cas={'path':str(path),'before':before,'after':after}
    def finish_cas(self):
        runtime.need(self.pending_cas is not None,'SCIENTIFIC_CAS_INTENT_REQUIRED')
        value=self.pending_cas;self.record(value['path'])
        runtime.need(self.inputs[value['path']].get('sha256')==value['after'],'SCIENTIFIC_CAS_AFTER_READBACK')
        self.cas_events.append(value);self.pending_cas=None;self.assert_current()


    def retain_final(self,failed):
        output=getattr(self.context,'owner_evidence_directory',None)
        if output is None:return
        if not failed:self.assert_current()
        value={'standard':'VRS-ONE-OPERATION-SCIENTIFIC-INPUT-DATA-1',
               'status':'HOLD_OPERATION_INPUT_DATA'if failed else'COMPLETE_REHASHED_OPERATION_INPUT_DATA',
               'data_only':True,'admission_cached':False,'initial_manifest':self.manifest,
               'inputs':list(self.inputs.values()),'inventory':self.inventory,
               'authorized_canonical_cas':self.cas_events,'completed_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()}
        path=Path(output)/('SCIENTIFIC_INPUT_DATA_HOLD.json'if failed else'SCIENTIFIC_INPUT_DATA_FINAL.json')
        token=_HASHING.set(True)
        try:
            with path.open('x')as stream:json.dump(value,stream,sort_keys=True,indent=2);stream.write('\n')
            self.final_manifest={'path':str(path),'sha256':runtime.sha(path.read_bytes())}
        finally:_HASHING.reset(token)


def _observe_original_read(event,args):
    capture=_READ_CAPTURE.get()
    if event!='open'or capture is None or _HASHING.get():return
    path,mode,flags=args
    read=(isinstance(mode,str)and('r'in mode or '+'in mode))or(mode is None and flags&os.O_ACCMODE!=os.O_WRONLY)
    if read:capture.record(path)

# The hook is inert outside the explicit operation; it never replaces a reader.
sys.addaudithook(_observe_original_read)


def scientific_data(root):
    value=_SCIENCE.get()
    runtime.need(value is not None and value.root==Path(root).resolve(strict=True),
                 'ONE_CURRENT_SCIENTIFIC_INPUT_OPERATION_REQUIRED')
    return value


@contextlib.contextmanager
def operation_scope(root, profile_binding, registry_context):
    """Explicit additive callsite scope; original module globals stay untouched."""
    begin=getattr(registry_context,'begin_observation_operation',None)
    end=getattr(registry_context,'end_observation_operation',None)
    if begin is not None:begin()
    token=None;failed=True
    parent=_SCIENCE.get()
    snapshot=parent if parent is not None and parent.root==Path(root).resolve(strict=True)and parent.context is registry_context else ScientificInputData(root,registry_context)
    snapshot.depth+=1
    science_token=_SCIENCE.set(snapshot);read_token=_READ_CAPTURE.set(snapshot)
    try:
        checked_context(root, profile_binding, registry_context)
        token = _OPERATION.set((Path(root).resolve(strict=True), profile_binding, registry_context))
        yield
        observation_guard(registry_context)
        failed=False
    finally:
        try:
            try:
                snapshot.depth-=1
                if snapshot.depth==0:snapshot.retain_final(failed)
            except BaseException:
                failed=True
                raise
            finally:
                if end is not None:end(failed=failed)
        finally:
            if token is not None:_OPERATION.reset(token)
            _READ_CAPTURE.reset(read_token);_SCIENCE.reset(science_token)


def operation(root):
    value = _OPERATION.get()
    runtime.need(value is not None and value[0] == Path(root).resolve(strict=True),
                 'EXPLICIT_DEFAULT_OPERATION_SCOPE_REQUIRED')
    return value[1], value[2]


def checked_context(root,profile_binding,context):
    profile=runtime.validate(root,profile_binding)
    registry=importlib.import_module('manuscript_access_registry')
    runtime.need(isinstance(context,registry.RegistryContext)and context.root==Path(root).resolve(strict=True)
                 and context.binding==profile['access_registry'],'EXACT_DEFAULT_REGISTRY_CONTEXT')
    context._registry()
    observation_guard(context)
    return context


def observation_guard(context):
    """Production factory guard is mandatory there; explicit injected diagnostic
    readers retain their own evidence/context contract and grant no live claim.
    """
    guard=getattr(context,'assert_observation_current',None)
    if guard is not None:guard()
    data=_SCIENCE.get()
    if data is not None and data.context is context:data.assert_current()


def authorize_canonical_write(path,ledger,expected_sha256):
    data=scientific_data(Path(path).resolve(strict=True).parents[1])
    runtime.need(data.scan_data is not None,'FRESH_COMPLETE_OPERATIONAL_SCAN_REQUIRED')
    raw=(json.dumps(ledger,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    data.authorize_cas(path,expected_sha256,runtime.sha(raw))


def finish_canonical_write(root):
    scientific_data(root).finish_cas()


def owner_context(root,profile_binding,memory_token,output):
    """One bounded observation operation; retained exact inputs are rechecked.

    First reads are real paced owner GETs. Within this operation only, later
    consumers re-read their complete immutable observed bodies and file bytes.
    No admission verdict, normalized view or evidence from an earlier operation
    is cached. All scientific/access consumers run again on every invocation.
    """
    profile=runtime.validate(root,profile_binding);root=Path(root).resolve(strict=True);output=Path(output)
    runtime.need(output.resolve().is_relative_to(root/'reports/verification-coverage')and not output.exists(),'EXCLUSIVE_OWNER_READBACK_OUTPUT')
    output.mkdir(parents=True,exist_ok=False)
    transport=importlib.import_module('zenodo_transport');registry=importlib.import_module('manuscript_access_registry')
    pacing=importlib.import_module('first_digest_publisher')
    opener=pacing.PacedOpener(urllib.request.build_opener(transport.NoRedirect()))
    opened=time.monotonic();first_get=None;opener.deadline=None
    t=transport.ZenodoTransport('zenodo.org',memory_token,output/'transport',opener=opener)
    sequence=0;observed={};bodies={};operation_state={'depth':0,'closed':False}
    def unexpired():
        runtime.need(not operation_state['closed']and operation_state['depth']>0,'ONE_ACTIVE_OBSERVATION_OPERATION_REQUIRED')
        runtime.need(first_get is None or time.monotonic()<=first_get+OBSERVATION_SECONDS,'BOUNDED_OBSERVATION_OPERATION_EXPIRED')
    def start_get_clock():
        nonlocal first_get
        unexpired()
        if first_get is None:
            first_get=time.monotonic();opener.deadline=first_get+OBSERVATION_SECONDS
    def replay(entry):
        unexpired()
        body=None
        for path, expected in entry['inputs']:
            runtime.need(path.is_file()and not any(p.is_symlink()for p in(path,*path.parents)),
                         'ACTUAL_OBSERVATION_INPUT_CHANGED')
            first=path.stat();raw=path.read_bytes();last=path.stat()
            runtime.need((first.st_ino,first.st_size,first.st_mtime_ns)==(last.st_ino,last.st_size,last.st_mtime_ns)
                         and runtime.sha(raw)==expected,'ACTUAL_OBSERVATION_INPUT_CHANGED')
            if path==entry['path']:body=raw
        unexpired();runtime.need(body is not None,'CHECKED_OBSERVATION_BODY_REQUIRED')
        return body
    def get(rid,accept):
        unexpired()
        key=(rid,accept)
        if key not in observed:
            start_get_clock()
            value=t.request('GET','https://zenodo.org/api/records/'+rid,accept=accept)
            encoded=json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()
            runtime.need(memory_token.encode()not in encoded,'CREDENTIAL_IN_OWNER_BODY')
            folder=output/'observations'/f'{len(observed)+1:04d}';folder.mkdir(parents=True,exist_ok=False)
            path=folder/'ACTUAL_BODY.json'
            with path.open('xb')as stream:stream.write(encoded)
            receipt=t.out/f'{t.sequence:03d}_GET.json'
            info={'method':'GET','record_id':rid,'accept':accept,'authentication':'OWNER','owner_id':'1591505',
                  'observed_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                  'transport_receipt':{'path':str(receipt),'sha256':runtime.sha(receipt.read_bytes())},
                  'actual_complete_body':{'path':str(path),'sha256':runtime.sha(encoded)},
                  'reuse_scope':'THIS_BOUND_900_SECOND_OPERATION_ONLY','admission_cached':False}
            stamp=folder/'OBSERVATION.json'
            with stamp.open('x')as stream:json.dump(info,stream,sort_keys=True,indent=2);stream.write('\n')
            observed[key]={'path':path,'inputs':[(p,runtime.sha(p.read_bytes()))for p in(path,receipt,stamp)]}
        return json.loads(replay(observed[key]))
    def download(rid,name):
        nonlocal sequence
        unexpired()
        runtime.need(Path(name).name==name,'OWNER_BYTE_BASENAME')
        key=(rid,name)
        if key in bodies:return replay(bodies[key])
        url='https://zenodo.org/api/records/'+rid+'/files/'+name+'/content'
        start_get_clock()
        request=urllib.request.Request(url,headers={'Authorization':'Bearer '+memory_token,'Accept':'*/*'})
        with opener.open(request,timeout=120)as response:
            runtime.need(response.status==200 and response.geturl()==url,'EXACT_OWNER_BYTE_URL');raw=response.read()
        sequence+=1;folder=output/'bytes'/f'{sequence:04d}';folder.mkdir(parents=True,exist_ok=False)
        with(folder/name).open('xb')as stream:stream.write(raw)
        stamp=folder/'GET.json'
        with stamp.open('x')as stream:json.dump({'method':'GET','url':url,'authentication':'OWNER','owner_id':'1591505',
            'accept':'*/*','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
            'observed_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'reuse_scope':'THIS_BOUND_900_SECOND_OPERATION_ONLY','admission_cached':False},stream,sort_keys=True,indent=2);stream.write('\n')
        bodies[key]={'path':folder/name,'inputs':[(p,runtime.sha(p.read_bytes()))for p in(folder/name,stamp)]}
        return replay(bodies[key])
    context=registry.RegistryContext(root,profile['access_registry'],download=download,
                                    observation_context=registry.CONTEXT,owner_getter=get)
    def assert_current():
        unexpired()
        for entry in [*observed.values(),*bodies.values()]:replay(entry)
    context.owner_evidence_directory=output
    context.assert_observation_current=assert_current
    context.begin_public_get=start_get_clock
    def begin_operation():
        runtime.need(not operation_state['closed'],'OBSERVATION_OPERATION_ALREADY_CLOSED')
        operation_state['depth']+=1
    def end_operation(*,failed):
        runtime.need(operation_state['depth']>0,'OBSERVATION_SCOPE_BALANCE')
        operation_state['depth']-=1
        if failed or operation_state['depth']==0:operation_state['closed']=True
    context.begin_observation_operation=begin_operation
    context.end_observation_operation=end_operation
    context.observation_timing=lambda:{'elapsed_seconds':time.monotonic()-opened,
        'pre_get_scientific_seconds':(first_get if first_get is not None else time.monotonic())-opened,
        'observation_elapsed_seconds':time.monotonic()-first_get if first_get is not None else None,
        'clock_start':'FIRST_ACTUAL_GET','limit_seconds':OBSERVATION_SECONDS,'owner_api_views':len(observed),'file_bodies':len(bodies),
        'same_operation_byte_replay':True,'admission_cached':False}
    return context


def split_registered(root, previous, registrar):
    rows = previous.get('publication_entities', [])
    runtime.need(isinstance(rows, list) and all(isinstance(r, dict) for r in rows), 'PUBLICATION_ENTITY_ROWS')
    selected = []; ordinary = []
    for row in rows:
        binding = row.get('registration_receipt')
        if binding is None:
            ordinary.append(row); continue
        receipt = runtime.object_at(root, binding)[2]
        is_digest = row.get('registration_route') in {registrar.GROUP_ROUTE, registrar.NOTE_ROUTE}
        if is_digest:
            runtime.need(row.get('registration_route') in {registrar.GROUP_ROUTE, registrar.NOTE_ROUTE}, 'V3_EXPLICIT_ENTITY_ROUTE')
            selected.append(row)
        else:
            ordinary.append(row)
    return {**deepcopy(previous), 'publication_entities': deepcopy(ordinary)}, deepcopy(selected)


def prime_scientific_data(root,certificates,previous,profile_binding,*,registry_context,inventory_publications=None):
    """Fresh original scan DATA before any registry request; no admission PASS.

    Activation and registration retain all original consumers after this scan.
    This cannot reset existing input inventories or an observation clock.
    """
    with runtime.session(root,profile_binding):
        checked_context(root,profile_binding,registry_context)
        data=scientific_data(root)
        if data.scan_data is not None:
            data.assert_current();return
        runtime.need(data.inventory is None,'SCIENTIFIC_INPUT_SCAN_CANNOT_REBASELINE')
        corpus=importlib.import_module('corpus_ledger')
        registrar=importlib.import_module('methods_digest_registration_v3')
        ordinary,_=split_registered(root,previous,registrar)
        data.capture_inventory(corpus,certificates,inventory_publications if inventory_publications is not None else previous)
        scanned=corpus.build(root,certificates,previous_ledger=ordinary)
        data.assert_current();data.scan_data=deepcopy(scanned)


def build(root, certificates, previous, profile_binding, *, registry_context, inventory_publications=None):
    """Original selector and v1 replay first; add v3 only after fresh admission."""
    root = Path(root).resolve(strict=True)
    with runtime.session(root, profile_binding):
        checked_context(root,profile_binding,registry_context)
        corpus = importlib.import_module('corpus_ledger')
        registrar = importlib.import_module('methods_digest_registration_v3')
        ordinary, selected = split_registered(root, previous, registrar)
        data=scientific_data(root)
        first=data.scan_data is None
        prime_scientific_data(root,certificates,previous,profile_binding,registry_context=registry_context,
                              inventory_publications=inventory_publications)
        data.assert_current()
        legacy=deepcopy(data.scan_data)if first else corpus.preserve_publication_registrations(deepcopy(data.scan_data),ordinary)
        original_rows = deepcopy(legacy.get('publication_entities', []))
        selected_previous = {**previous, 'publication_entities': selected}
        # preserve delegates only the empty ordinary subset in this invocation;
        # the original complete selector/replay has already run just above.
        result = registrar.preserve(legacy, selected_previous,
                    legacy=lambda ledger, old: registrar._original_registrar().preserve(
                        ledger, old, legacy=lambda current, _: current,
                        consume=registry_context.require_registration),
                    consume=registry_context.require_registration)
        actual = {row['id']: row for row in result.get('publication_entities', [])}
        runtime.need(all(actual.get(row['id']) == row for row in original_rows), 'ALL_ORIGINAL_PUBLICATION_ROWS_UNCHANGED')
        runtime.need(result.get('enforcement_activation') == legacy.get('enforcement_activation')
                     and result.get('premise_declaration_cutover_run') == legacy.get('premise_declaration_cutover_run'), 'ORIGINAL_ACTIVATION_AND_CUTOVER')
        original=runtime.load(root,runtime.LEGACY_CONSUMER,'_current_operation_original_population')
        baseline=original.baseline_rows((root/runtime.LEGACY_CLOSURE['path']).parent)
        original.preserving_population(previous,baseline,result)
        observation_guard(registry_context)
        if data.manifest is None:data.retain_manifest()
        return result


def preserve_registered(root, ledger, previous, profile_binding, *, registry_context):
    """The existing ordinary registration consumer, then exact v1/access/v3.

    This is also the nominated seam for nightly intake and activation replay;
    none of those consumers can silently drop a digest row to obtain a PASS.
    """
    with runtime.session(root, profile_binding):
        checked_context(root, profile_binding, registry_context)
        prime_scientific_data(root,Path(root)/'RESEARCH_PIPELINE_v2/lean_certificates',previous,
                              profile_binding,registry_context=registry_context)
        corpus = importlib.import_module('corpus_ledger')
        registrar = importlib.import_module('methods_digest_registration_v3')
        ordinary, selected = split_registered(root, previous, registrar)
        # The caller contributes authoritative registration metadata only.
        # Current scientific file/Run/certificate/parity tables must come from
        # the complete freshly observed scan, never its old persisted ledger.
        base_ordinary, _ = split_registered(root, deepcopy(scientific_data(root).scan_data), registrar)
        base = corpus.preserve_publication_registrations(base_ordinary, ordinary)
        original_rows = deepcopy(base.get('publication_entities', []))
        result = registrar.preserve(base, {**previous, 'publication_entities': selected},
            legacy=lambda current, old: registrar._original_registrar().preserve(
                current, old, legacy=lambda actual, _: actual,
                consume=registry_context.require_registration),
            consume=registry_context.require_registration)
        actual = {r['id']: r for r in result.get('publication_entities', [])}
        runtime.need(all(actual.get(r['id']) == r for r in original_rows),
                     'ORIGINAL_REGISTRATION_ROWS_PRESERVED')
        runtime.need(len(actual) == len(result.get('publication_entities', []))
                     and set(actual) == {r['id'] for r in previous.get('publication_entities', [])},
                     'COMPLETE_REGISTRATION_POPULATION_PRESERVED')
        observation_guard(registry_context)
        return result


def refresh_canonical(root, profile_binding, *, registry_context, expected_sha256):
    """Fresh full dispatch followed by the unchanged exact-predecessor CAS."""
    root = Path(root).resolve(strict=True)
    with runtime.session(root, profile_binding):
        canonical = root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        raw = canonical.read_bytes()
        runtime.need(runtime.sha(raw) == expected_sha256, 'CANONICAL_EXACT_PREDECESSOR')
        previous = json.loads(raw)
        result = build(root, root/'RESEARCH_PIPELINE_v2/lean_certificates', previous,
                       profile_binding, registry_context=registry_context)
        runtime.need(canonical.read_bytes() == raw, 'CANONICAL_PROPOSAL_RACE')
        observation_guard(registry_context)
        corpus = importlib.import_module('corpus_ledger')
        data=scientific_data(root)
        after=runtime.sha((json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+'\n').encode())
        data.authorize_cas(canonical,expected_sha256,after)
        corpus.write_guarded_ledger(canonical, result, expected_sha256)
        data.finish_cas()
        actual = json.loads(canonical.read_bytes())
        runtime.need(actual == result, 'CANONICAL_CAS_READBACK')
        observation_guard(registry_context)
        return result


def publication_report(root, artifact, context, *, enforce_new_artifacts=False):
    """Original publication/claim/premise policy with explicit digest dispatch."""
    import datetime as dt
    root = Path(root).resolve(strict=True); artifact = Path(artifact).resolve(strict=True)
    profile, registry = operation(root)
    try:
        runtime.need(artifact.is_relative_to(root), 'PUBLICATION_ARTIFACT_ROOT')
        ledger = json.loads((root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
        find_entity = importlib.import_module('claim_binding').find_entity
        entity = find_entity(ledger, artifact)
        result = evaluate_publication(artifact, ledger, profile, registry_context=registry,
                                      entity_id=entity['id'], enforce=enforce_new_artifacts)
    except Exception as exc:
        original = importlib.import_module('publication_gate')
        result = {'artifact':str(artifact), 'status':'HOLD', 'label':original.UNCERTIFIED_LABEL,
                  'verification_status':'UNCERTIFIED', 'reasons':[type(exc).__name__+': '+str(exc)]}
    result.update(context=context, mode='ENFORCING' if enforce_new_artifacts else 'REPORT_ONLY',
                  enforcement=enforce_new_artifacts, blocking=enforce_new_artifacts and result['status']!='PASS',
                  metadata_modified=False, zenodo_writes=False,
                  observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    return result


def augment_audit(root, ledger, profile_binding, *, registry_context):
    with runtime.session(root, profile_binding):
        checked_context(root,profile_binding,registry_context)
        runtime.need(scientific_data(root).scan_data is not None,'FRESH_COMPLETE_OPERATIONAL_SCAN_REQUIRED')
        audit_module = importlib.import_module('doi_audit')
        registrar = importlib.import_module('methods_digest_registration_v3')
        ordinary, selected = split_registered(root, ledger, registrar)
        audit = audit_module.build_audit(root, ordinary)
        # Avoid the v1 population double count; this branch receives only v3 rows.
        v3=[row for row in selected if registrar.is_v3_binding(root,row['registration_receipt'])]
        v1=[row for row in selected if row not in v3]
        first=registrar._original_registrar().augment_audit(root,{**ledger,'publication_entities':v1},audit,
                                                          consume=registry_context.require_registration)
        result=registrar.augment_audit(root,{**ledger,'publication_entities':v3},first,
                                       consume=registry_context.require_registration)
        observation_guard(registry_context)
        return result


def evaluate_publication(artifact, ledger, profile_binding, *, registry_context, **kwargs):
    root = Path(ledger['tree_root']).resolve(strict=True)
    with runtime.session(root, profile_binding):
        checked_context(root,profile_binding,registry_context)
        original = importlib.import_module('publication_gate')
        registrar = importlib.import_module('methods_digest_registration_v3')
        from claim_binding import find_entity
        entity=find_entity(ledger,Path(artifact),kwargs.get('entity_id'))
        if entity.get('registration_route')in {registrar.GROUP_ROUTE,registrar.NOTE_ROUTE}:
            registry_context.require_registration(root,entity['registration_receipt'],ledger)
        result=registrar.evaluate_publication(artifact, ledger, legacy=original.evaluate_publication,
                    consume=registry_context.require_registration, **kwargs)
        observation_guard(registry_context)
        return result


def public_label_readback(root, audit, profile_binding, *, registry_context):
    """Actual owner views for digest groups, original anonymous generic reader."""
    root=Path(root).resolve(strict=True)
    with runtime.session(root,profile_binding):
        checked_context(root,profile_binding,registry_context)
        runtime.need(scientific_data(root).scan_data is not None,'FRESH_COMPLETE_OPERATIONAL_SCAN_REQUIRED')
        original=importlib.import_module('public_metadata_readback')
        groups=audit.get('methods_digest_groups',[]);ordinary=audit.get('published_records',[])
        runtime.need(isinstance(groups,list)and isinstance(ordinary,list),'CLOSED_PUBLIC_LABEL_POPULATION')
        population=[*ordinary,*groups];ids=[r.get('doi')for r in population]
        runtime.need(len(ids)==len(set(ids)),'UNIQUE_PUBLIC_LABEL_DOI')
        def paced_generic(row):
            # The original reader owns its anonymous HTTP operation. Keep its
            # policy unchanged, but serialize and pace this default callsite.
            guard=getattr(registry_context,'assert_observation_current',None)
            if guard is not None:guard()
            time.sleep(2.05)
            if guard is not None:guard()
            begin=getattr(registry_context,'begin_public_get',None)
            if begin is not None:begin()
            value=original._read_record_legacy(row)
            if guard is not None:guard()
            return value
        rows=[registry_context.public_label_read_record(row,legacy=paced_generic)
              for row in population]
        observation_guard(registry_context)
        return {'mode':'REPORT_ONLY','method':'Owner-context matching GETs for registered digests; anonymous GETs for generic records',
                'zenodo_writes':False,'counts':{'records':len(rows),'read':sum(r['status']=='READ'for r in rows),
                'unavailable':sum(r['status']!='READ'for r in rows),
                'label_disagreements':sum(r.get('proposed_label_disagrees',False)for r in rows),
                'locally_deposited_manuscripts_confirmed_public':sum(any(m['confirmed']for m in r['local_manuscript_public_checksum_matches'])for r in rows)},'records':rows}


def saved_scientific_population(root, ledger, original_scan):
    """Fresh saved scientific receipts after original selector/science replay.

    This source-profile check does not claim current public-owner observations;
    the operational catalog/label routes separately require RegistryContext.
    No v1 callable or scientific input is replaced or monkeypatched.
    """
    registrar=importlib.import_module('methods_digest_registration_v3')
    selected=[r for r in ledger['publication_entities']if r.get('registration_receipt')is not None
              and registrar.is_v3_binding(root,r['registration_receipt'])]
    return registrar.preserve(original_scan,{**ledger,'publication_entities':selected},
                              legacy=lambda scan,_:scan)


def main():
    """Default catalog route: proposals only; the existing guarded writer owns CAS."""
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--mode',choices=['ledger','doi','labels','refresh'],required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--expected-input-sha256',required=True)
    p.add_argument('--certificates',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--owner-evidence',type=Path,required=True);a=p.parse_args();root=a.root.resolve(strict=True)
    profile=runtime.nominated_binding(root)
    with runtime.session(root,profile):
        value=runtime.object_at(root,{'path':str(a.input.resolve(strict=True)),'sha256':a.expected_input_sha256})[2]
        publisher=importlib.import_module('publish_dated_bundles_guarded');context=owner_context(root,profile,publisher.token(),a.owner_evidence)
        with operation_scope(root,profile,context):
            if a.mode=='refresh':
                runtime.need(a.input.resolve(strict=True)==root/'RESEARCH_PIPELINE_v2/corpus_ledger.json', 'REFRESH_CANONICAL_INPUT')
                result=refresh_canonical(root,profile,registry_context=context,expected_sha256=a.expected_input_sha256)
            elif a.mode=='ledger':
                runtime.need(a.input.resolve(strict=True)==root/'RESEARCH_PIPELINE_v2/corpus_ledger.json','LEDGER_CANONICAL_INPUT')
                runtime.need(a.certificates is not None,'ORIGINAL_CERTIFICATE_ROOT_REQUIRED');result=build(root,a.certificates,value,profile,registry_context=context)
            elif a.mode=='doi':
                runtime.need(a.input.resolve(strict=True)==root/'RESEARCH_PIPELINE_v2/corpus_ledger.json','DOI_CANONICAL_INPUT')
                fresh=build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',value,profile,registry_context=context)
                result=augment_audit(root,fresh,profile,registry_context=context)
            else:
                canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
                current=json.loads(canonical.read_bytes())
                fresh=build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates',current,profile,registry_context=context)
                fresh_audit=augment_audit(root,fresh,profile,registry_context=context)
                runtime.need(value==fresh_audit,'LABELS_EXACT_CURRENT_OPERATION_AUDIT')
                result=public_label_readback(root,fresh_audit,profile,registry_context=context)
        runtime.need(a.out.resolve().is_relative_to(root/'reports/verification-coverage')and not a.out.exists(),'EXCLUSIVE_PROPOSAL_OUTPUT')
        a.out.parent.mkdir(parents=True,exist_ok=True)
        with a.out.open('x')as stream:json.dump(result,stream,sort_keys=True,indent=2,ensure_ascii=False);stream.write('\n')
        print(json.dumps({'status':'FRESH_DEFAULT_CATALOG_PROPOSAL_NOT_CANONICAL_WRITE','path':str(a.out),
                          'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest(),'zenodo_writes':0,'certifies':False},sort_keys=True))
    return 0


if __name__=='__main__':raise SystemExit(main())
