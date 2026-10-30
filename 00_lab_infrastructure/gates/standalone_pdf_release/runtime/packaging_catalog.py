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
import owner_content_worker as owner_worker

OBSERVATION_SECONDS = 900

_OPERATION = contextvars.ContextVar('exact_packaging_operation', default=None)

_SCIENCE = contextvars.ContextVar('exact_scientific_input_operation', default=None)
_READ_CAPTURE = contextvars.ContextVar('exact_scientific_read_capture', default=None)
_HASHING = contextvars.ContextVar('observer_internal_hash_read', default=False)


class _ProtectedAliasData:
    # Slot descriptors cannot be shadowed by the mutable ordinary DATA fields
    # in the child instance dictionary. The recursive stored values are tuples.
    __slots__ = ('_alias_material', '_alias_binding_material', '_alias_path_parts')
    def __setattr__(self, name, value):
        if name in {'_alias_material', '_alias_binding_material', '_alias_path_parts'} and hasattr(self, name):
            raise AttributeError('The historical alias DATA snapshot is immutable')
        object.__setattr__(self, name, value)
    def __delattr__(self, name):
        if name in {'_alias_material', '_alias_binding_material', '_alias_path_parts'}:
            raise AttributeError('The historical alias DATA snapshot cannot be deleted')
        object.__delattr__(self, name)
    @property
    def alias_observation(self):
        return None if self._alias_material is None else self._alias_material.export()
    @property
    def alias_binding(self):
        return None if self._alias_binding_material is None else self._alias_binding_material.export()


class ScientificInputData(_ProtectedAliasData):
    """One operation's observed scan DATA; every reused byte is rechecked.

    The original scanner runs once. Original registry/science predicates run
    again over its unchanged data. There is no stored admission/PASS verdict.
    Every actual read, including sibling mirror inputs and absent read targets,
    is observed without replacing any original reader or function body.

    V006 deliberately checks alias authority per read only for lexical paths
    at/below the fixed historical alias. Canonical no-link DATA has no alias
    permission. Complete global alias checks still bracket input admission,
    source validation, observations, manifests, canonical CAS and source exit.
    """
    def __init__(self,root,context,*,data_alias_observation=None,platform_timezone_observation=None):
        self.root=Path(root).resolve(strict=True);self.context=context
        self.inputs={};self.scan_data=None;self.inventory_reader=None;self.inventory=None
        self.pending_cas=None;self.manifest=None;self.final_manifest=None;self.depth=0;self.cas_events=[]
        self._alias_binding_material=(runtime.immutable_json_object(data_alias_observation)
                                      if data_alias_observation is not None else None)
        observation=(runtime.require_data_alias_observation(self.root,data_alias_observation)
                     if data_alias_observation is not None else None)
        self._alias_material=(runtime.immutable_json_object(observation) if observation is not None else None)
        self._alias_path_parts=(Path(observation['alias_path']).parts if observation is not None
                                else runtime.SCIENTIFIC_ALIAS_PATH.parts)
        self.platform_binding=platform_timezone_observation
        self.platform_observation=(runtime.require_platform_timezone_observation(self.root,platform_timezone_observation)
                                   if platform_timezone_observation is not None else None)
        self.platform_initial_frame=None;self.platform_latest_frame=None
        if self.platform_observation is not None:
            self.platform_initial_frame=runtime.platform_timezone_frame(self.platform_observation)
            self.platform_latest_frame=self.platform_initial_frame
    def platform_guard(self):
        if self.platform_observation is None:return
        token=_HASHING.set(True)
        try:
            current=runtime.object_at(self.root,self.platform_binding)[2]
            runtime.need(current==self.platform_observation,'NATIVE_PLATFORM_TIMEZONE_OBSERVATION_CHANGED')
            self.platform_latest_frame=runtime.platform_timezone_frame(current)
        finally:_HASHING.reset(token)
    def alias_guard(self,*,complete=False):
        if self._alias_material is None:return
        token=_HASHING.set(True)
        try:
            current=(runtime.immutable_json_object(runtime.require_data_alias_observation(self.root,self.alias_binding))if complete
                     else runtime.immutable_object_at(self.root,self.alias_binding)[2])
            runtime.need(current==self._alias_material
                         and runtime.same_observed_identity(runtime.data_alias_identity(Path(current['alias_path'])),current['identity'])
                         and runtime.strict_historical_alias_target(Path(current['alias_path']),self.root,
                              current['identity']['readlink'])==self.root,
                         'SCIENTIFIC_HISTORICAL_ALIAS_OBSERVATION_CHANGED')
        finally:_HASHING.reset(token)
    def data_path(self,path):
        runtime.need('..'not in path.parts,'SCIENTIFIC_INPUT_REGULAR_PATH:'+str(path))
        # Classify lexical use of the FIXED alias, never the current existence
        # of a symlink. A missing alias or one replaced by an ordinary directory
        # therefore cannot become an unauthenticated canonical DATA read.
        alias_parts=self._alias_path_parts
        uses_alias=path.parts[:len(alias_parts)]==alias_parts
        if uses_alias:
            runtime.need(self._alias_material is not None,'SCIENTIFIC_INPUT_REGULAR_PATH:'+str(path))
            self.alias_guard()
        if self.platform_observation is not None and path==Path(self.platform_observation['logical_selected_path']):
            self.platform_guard()
            return Path(self.platform_observation['physical_path']),None
        links=runtime.fresh_symlink_components(path)
        physical=path;alias=None
        if links:
            runtime.need(self._alias_material is not None,'SCIENTIFIC_INPUT_REGULAR_PATH:'+str(path))
            alias_root=Path(self._alias_material['alias_path'])
            runtime.need(uses_alias and links==[alias_root]and path.is_relative_to(alias_root),'SCIENTIFIC_INPUT_REGULAR_PATH:'+str(path))
            physical=self.root/path.relative_to(alias_root)
            alias=self._alias_material['identity']
        runtime.need(not runtime.fresh_symlink_components(physical),
                     'SCIENTIFIC_INPUT_REGULAR_PATH:'+str(path))
        return physical,alias
    def _raise_input_read_race(self, path, physical, first, last, final, raw, phase):
        """Failure DATA only: preserve the same primary HOLD and existing samples."""
        try:
            runtime.need(False, 'SCIENTIFIC_INPUT_READ_RACE')
        except runtime.PackagingHold as primary:
            token = _HASHING.set(True)
            try:
                self._retain_input_read_race(path, physical, first, last, final, raw, phase)
            except BaseException as retention_error:
                if hasattr(primary, 'add_note'):
                    primary.add_note('Scientific input read-race DATA retention unavailable: '
                                     + type(retention_error).__name__)
            finally:
                _HASHING.reset(token)
            raise

    def _retain_input_read_race(self, path, physical, first, last, final, raw, phase):
        """Exclusive bounded metadata under this context's owned evidence root.

        No input stat/read is performed here. Optional caller joins are DATA,
        never proof of a result, source exit, original call or admission.
        """
        fields = ('device', 'inode', 'mode', 'bytes', 'mtime_ns', 'ctime_ns')
        def frame(sample):
            return None if sample is None else dict(zip(fields, (
                sample.st_dev, sample.st_ino, sample.st_mode, sample.st_size,
                sample.st_mtime_ns, sample.st_ctime_ns)))
        output = getattr(self.context, 'owner_evidence_directory', None)
        runtime.need(output is not None, 'READ_RACE_OWNED_EVIDENCE_DIRECTORY')
        output = Path(output)
        runtime.need(output.is_absolute() and '..' not in output.parts
                     and output.is_relative_to(self.root)
                     and output.is_dir()
                     and not any(p.is_symlink() for p in (output, *output.parents)),
                     'READ_RACE_STRICT_OWNED_EVIDENCE_DIRECTORY')
        causal = {key: None for key in ('operation', 'job_nonce', 'stage', 'ordinal', 'config', 'result')}
        runtime.need(type(raw) is bytes and phase in {'BODY_FIRST_LAST', 'FINAL_LEAF_AFTER_PATH'}, 'READ_RACE_SAMPLED_DATA')
        value = {'standard': 'VRS-SCIENTIFIC-INPUT-READ-RACE-DATA-1',
                 'status': 'READ_RACE_PRIMARY_HOLD_DIAGNOSTIC_ONLY',
                 'logical_path': str(path), 'physical_path': str(physical),
                 'phase': phase, 'first': frame(first), 'last': frame(last), 'final': frame(final),
                 'acquired_raw_sha256': runtime.sha(raw), 'acquired_raw_bytes': len(raw),
                 'causal_joins': causal, 'causal_joins_are_data_only': True,
                 'causal_join_availability': 'UNAVAILABLE_CURRENT_CONTEXT_HAS_NO_CAUSAL_PRODUCER',
                 'captured_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                 'actual_runtime_admission': False, 'source_finally_claimed': False,
                 'original_call_claimed': False, 'certifies': False}
        encoded = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
        runtime.need(len(encoded) <= 16384, 'BOUNDED_READ_RACE_DIAGNOSTIC')
        import re
        runtime.need(re.search(rb'(?i)(?:bearer[ \t]+[^ \t\r\n"<>]+|(?:access_token|api_key|authorization)[" \t]*[:=]|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})', encoded) is None,
                     'READ_RACE_CREDENTIAL_PATTERN')
        name = 'SCIENTIFIC_INPUT_READ_RACE_' + str(os.getpid()) + '_' + str(time.monotonic_ns()) + '.json'
        directories = []; fd = None
        try:
            directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            parent = os.open('/', directory_flags); directories.append(parent)
            for component in output.parts[1:]:
                parent = os.open(component, directory_flags, dir_fd=parent); directories.append(parent)
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            created = os.fstat(fd); owned = (created.st_dev, created.st_ino, created.st_mode)
            remaining = memoryview(encoded)
            while remaining:
                current = os.fstat(fd)
                runtime.need((current.st_dev, current.st_ino, current.st_mode) == owned, 'READ_RACE_OWNED_OUTPUT_FD')
                count = os.write(fd, remaining)
                runtime.need(count > 0, 'READ_RACE_OUTPUT_PROGRESS'); remaining = remaining[count:]
            os.fsync(fd)
        finally:
            close_error = None
            for owned_fd in ([fd] if fd is not None else []) + list(reversed(directories)):
                try: os.close(owned_fd)
                except BaseException as exc:
                    if close_error is None: close_error = exc
            if close_error is not None: raise close_error
        diagnostic = output / name
        runtime.need(not any(p.is_symlink() for p in (diagnostic, *diagnostic.parents)), 'READ_RACE_OUTPUT_READBACK')
        readback = diagnostic.read_bytes(); observed = diagnostic.stat()
        runtime.need((observed.st_dev, observed.st_ino, observed.st_mode) == owned
                     and readback == encoded, 'READ_RACE_OUTPUT_READBACK')
        self.read_race_diagnostic = {'path': str(diagnostic), 'sha256': runtime.sha(encoded)}

    def record(self,path):
        if isinstance(path,int):
            stat=os.fstat(path)
            matched=[r for r in self.inputs.values()if r.get('exists')is True
                     and (r['device'],r['inode'],r['bytes'],r['mtime_ns'])==(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)]
            runtime.need(bool(matched)and len({r['sha256']for r in matched})==1,
                         'SCIENTIFIC_UNBOUND_READ_DESCRIPTOR')
            for row in matched:self.record(row['path'])
            return
        path=Path(os.fsdecode(path)).absolute()
        token=_HASHING.set(True)
        try:
            physical,alias=self.data_path(path)
            if not physical.exists():row={'path':str(path),'physical_path':str(physical),'exists':False}
            else:
                if not physical.is_file():
                    kind=physical.stat();directory_identity=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns)
                    runtime.need(self.data_path(path)==(physical,alias)
                                 and physical.exists()and not physical.is_file()
                                 and directory_identity(physical.stat())==directory_identity(kind),
                                 'SCIENTIFIC_INPUT_PATH_READ_RACE');return
                first=physical.stat();raw=physical.read_bytes();last=physical.stat()
                identity=runtime.file_identity
                if identity(first)!=identity(last):
                    self._raise_input_read_race(path,physical,first,last,None,raw,'BODY_FIRST_LAST')
                try:
                    snapshot=runtime.read_stable_input(physical)
                    runtime.need(snapshot.data==raw and snapshot.identity==runtime.stable_input_identity(raw,last),
                                 'SCIENTIFIC_INPUT_READ_RACE')
                except runtime.PackagingHold:
                    self._raise_input_read_race(path,physical,first,last,None,raw,'BODY_FIRST_LAST')
                row={'path':str(path),'physical_path':str(physical),'exists':True,'sha256':runtime.sha(raw),
                     'device':last.st_dev,'inode':last.st_ino,'mode':last.st_mode,'bytes':last.st_size,
                     'mtime_ns':last.st_mtime_ns,'ctime_ns':last.st_ctime_ns}
            runtime.need(self.data_path(path)==(physical,alias),'SCIENTIFIC_INPUT_PATH_READ_RACE')
            runtime.need(physical.exists()is row['exists']
                         and (not row['exists']or physical.is_file()),'SCIENTIFIC_INPUT_EXISTENCE_OR_TYPE_RACE')
            if row['exists']:
                final=physical.stat()
                if identity(final)!=identity(last):
                    self._raise_input_read_race(path,physical,first,last,final,raw,'FINAL_LEAF_AFTER_PATH')
                try:
                    runtime.read_stable_input(physical,expected=snapshot.identity)
                except runtime.PackagingHold:
                    self._raise_input_read_race(path,physical,first,last,final,raw,'FINAL_LEAF_AFTER_PATH')
            if alias is not None:row['historical_alias_identity']=dict(alias)
            if self.platform_observation is not None and path==Path(self.platform_observation['logical_selected_path']):
                row['platform_timezone_observation']=self.platform_binding
                row['native_timezone_identity']=self.platform_observation['after']['physical_file_identity']
                row['native_timezone_link_chain']=self.platform_observation['after']['resolution_symlink_chain']
            self._commit_checked_row(row)
        finally:_HASHING.reset(token)
    def _commit_checked_row(self, row):
        old = self.inputs.get(row['path'])
        if old is not None and not runtime.same_observed_identity(old, row):
            allowed = self.pending_cas
            runtime.need(allowed is not None and row['path'] == allowed['path']
                         and old.get('sha256') == allowed['before'] and row.get('sha256') == allowed['after'],
                         'SCIENTIFIC_INPUT_CHANGED:' + row['path'])
        self.inputs[row['path']] = row

    def read_owned(self, path, *, expected_sha256=None):
        """One full fresh read of this operation's exact retained OWNER DATA.

        Only additive evidence leaves use this buffer. The original readers
        remain observed by the unmodified audit hook. Before/after complete
        paths, six identities and row/current-byte checks remain mandatory.
        """
        runtime.need(_SCIENCE.get() is self and _READ_CAPTURE.get() is self, 'ONE_ACTIVE_OWNED_DATA_OPERATION_REQUIRED')
        deadline = getattr(self.context, 'deadline_guard', None)
        if deadline is not None: deadline()
        path = Path(path).absolute(); output = getattr(self.context, 'owner_evidence_directory', None)
        runtime.need(output is not None, 'OWNED_OWNER_EVIDENCE_REQUIRED')
        output = Path(output).absolute()
        runtime.need(path.is_relative_to(output) and '..' not in path.parts
                     and len(path.relative_to(output).parts) >= 2
                     and path.relative_to(output).parts[0] in {'observations', 'bytes', 'transport'},
                     'OWNED_OWNER_EVIDENCE_LEAF_ONLY')
        token = _HASHING.set(True)
        try:
            physical, alias = self.data_path(path)
            runtime.need(physical == path and alias is None and physical.is_file(), 'OWNED_OWNER_REGULAR_LEAF')
            first = physical.stat(); raw = physical.read_bytes(); last = physical.stat(); digest = runtime.sha(raw)
            snapshot = runtime.read_stable_input(physical)
            runtime.need(runtime.file_identity(first) == runtime.file_identity(last)
                         and self.data_path(path) == (physical, alias) and physical.is_file()
                         and runtime.file_identity(physical.stat()) == runtime.file_identity(last)
                         and snapshot.data == raw and snapshot.identity == runtime.stable_input_identity(raw,last)
                         and (expected_sha256 is None or digest == expected_sha256),
                         'OWNED_OWNER_INPUT_HASH_OR_RACE')
            runtime.read_stable_input(physical, expected=snapshot.identity)
            if deadline is not None: deadline()
            row = {'path': str(path), 'physical_path': str(physical), 'exists': True, 'sha256': digest,
                   'device': last.st_dev, 'inode': last.st_ino, 'mode': last.st_mode, 'bytes': last.st_size,
                   'mtime_ns': last.st_mtime_ns, 'ctime_ns': last.st_ctime_ns}
            self._commit_checked_row(row)
            return raw
        finally: _HASHING.reset(token)

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
        registered=runtime.json_file_field(self.root,canonical,'publication_entities',[])[2]if canonical.is_file()else[]
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
        self.alias_guard(complete=True)
        self.platform_guard()
        if self.scan_data is not None:self.require_platform_read()
        for path in list(self.inputs):self.record(path)
        if self.inventory_reader is not None:
            runtime.need(self.inventory_reader()==self.inventory,'SCIENTIFIC_INPUT_INVENTORY_CHANGED')
        # Canonical reads no longer need alias permission; this final global
        # authority check catches descriptor/link drift during their replay
        # before a full input/admission/manifest/CAS boundary can return.
        self.alias_guard(complete=True)
    def require_platform_read(self):
        """The unchanged original reader must actually request the pinned leaf.

        A nominal descriptor check, physical observer-internal read, or cached
        ZoneInfo object supplies no current-operation logical DATA observation.
        """
        if self.platform_observation is None:return
        row=self.inputs.get(self.platform_observation['logical_selected_path'])
        runtime.need(row is not None and row.get('exists')is True
                     and row.get('physical_path')==self.platform_observation['physical_path']
                     and row.get('sha256')==self.platform_observation['after']['sha256']
                     and row.get('platform_timezone_observation')==self.platform_binding,
                     'ACTUAL_CURRENT_OPERATION_NEW_YORK_TZ_DATA_READ_REQUIRED')
    def retain_manifest(self):
        output=getattr(self.context,'owner_evidence_directory',None)
        if output is None:return
        self.assert_current();path=Path(output)/'SCIENTIFIC_INPUT_DATA_MANIFEST.json'
        value={'standard':'VRS-ONE-OPERATION-SCIENTIFIC-INPUT-DATA-1','scope':'THIS_ACTIVE_OPERATION_ONLY',
               'data_only':True,'admission_cached':False,'inputs':list(self.inputs.values()),
               'data_alias_observation':self.alias_binding,'historical_alias':self.alias_observation,
               'platform_timezone_observation':self.platform_binding,'native_timezone':self.platform_observation,
               'native_timezone_initial_frame':self.platform_initial_frame,'native_timezone_latest_frame':self.platform_latest_frame,
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
               'data_alias_observation':self.alias_binding,'historical_alias':self.alias_observation,
               'platform_timezone_observation':self.platform_binding,'native_timezone':self.platform_observation,
               'native_timezone_initial_frame':self.platform_initial_frame,'native_timezone_latest_frame':self.platform_latest_frame,
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
    shared=runtime._SHARED_SOURCE_READ.get()
    if (shared is not None and not isinstance(path,int)
            and shared==(os.fsdecode(path),runtime.SHARED_INPUT_SHA256)):
        return  # Only the separately hash-bound helper's own source read.
    read=(isinstance(mode,str)and('r'in mode or '+'in mode))or(mode is None and flags&os.O_ACCMODE!=os.O_WRONLY)
    if read:
        try:capture.record(path)
        except runtime.PackagingHold as exc:
            detail='descriptor:'+str(path)if isinstance(path,int)else os.fsdecode(path)
            raise runtime.PackagingHold(str(exc)+'; read_path='+detail)from exc

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
    with runtime.json_data_scope(root):
        begin=getattr(registry_context,'begin_observation_operation',None)
        end=getattr(registry_context,'end_observation_operation',None)
        if begin is not None:begin()
        token=None;science_token=None;read_token=None;failed=True;snapshot=None;counted=False
        try:
            parent=_SCIENCE.get()
            snapshot=parent if parent is not None and parent.root==Path(root).resolve(strict=True)and parent.context is registry_context else ScientificInputData(
                root,registry_context,data_alias_observation=(runtime.DATA_ALIAS_OBSERVATION
                    if Path(root).resolve(strict=True)==runtime.SCIENTIFIC_ALIAS_PATH.parent/runtime.SCIENTIFIC_ALIAS_READLINK else None),
                platform_timezone_observation=(runtime.CURRENT_PLATFORM_TIMEZONE_OBSERVATION
                    if Path(root).resolve(strict=True)==runtime.SCIENTIFIC_ALIAS_PATH.parent/runtime.SCIENTIFIC_ALIAS_READLINK else None))
            snapshot.depth+=1;counted=True
            science_token=_SCIENCE.set(snapshot);read_token=_READ_CAPTURE.set(snapshot)
            checked_context(root, profile_binding, registry_context)
            token = _OPERATION.set((Path(root).resolve(strict=True), profile_binding, registry_context))
            yield
            observation_guard(registry_context)
            failed=False
        finally:
            try:
                try:
                    if counted:
                        snapshot.depth-=1
                        if snapshot.depth==0:snapshot.retain_final(failed)
                except BaseException:
                    failed=True
                    raise
                finally:
                    if end is not None:end(failed=failed)
            finally:
                if token is not None:_OPERATION.reset(token)
                if read_token is not None:_READ_CAPTURE.reset(read_token)
                if science_token is not None:_SCIENCE.reset(science_token)

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
    broker=None;prefetched=False;process_sequence=0
    def deadline_guard():
        # Scalar only: constructor may check it before begin/depth exists.
        # It never starts/resets the clock and cannot authorize a GET/replay.
        runtime.need(not operation_state['closed'],'OBSERVATION_OPERATION_ALREADY_CLOSED')
        runtime.need(first_get is None or time.monotonic()<=first_get+OBSERVATION_SECONDS,'BOUNDED_OBSERVATION_OPERATION_EXPIRED')
    def unexpired():
        runtime.need(not operation_state['closed']and operation_state['depth']>0,'ONE_ACTIVE_OBSERVATION_OPERATION_REQUIRED')
        deadline_guard()
    def start_get_clock():
        nonlocal first_get
        unexpired()
        if first_get is None:
            first_get=time.monotonic();opener.deadline=first_get+OBSERVATION_SECONDS
    def owned_read(path, expected=None):
        data = _SCIENCE.get()
        if data is not None:
            runtime.need(data.root == root and data.context is context, 'EXACT_OWNED_DATA_OPERATION')
            return data.read_owned(path, expected_sha256=expected)
        # Explicit diagnostic callers still need complete fresh source checks.
        return runtime.read_data_file(root, path, expected_sha256=expected)[1]
    def replay(entry):
        unexpired(); body = None
        for path, expected in entry['inputs']:
            try:raw = owned_read(path, expected)
            except (runtime.PackagingHold, OSError) as exc:
                raise runtime.PackagingHold('HOLD_PACKAGING_ACTUAL_OBSERVATION_INPUT_CHANGED') from exc
            if path == entry['path']: body = raw
        unexpired(); runtime.need(body is not None, 'CHECKED_OBSERVATION_BODY_REQUIRED')
        return body
    def get(rid,accept):
        unexpired()
        key=(rid,accept)
        if key not in observed:
            runtime.need(not prefetched,'ONLY_CLOSED_PREFETCHED_HEALTH_METADATA')
            start_get_clock()
            value=t.request('GET','https://zenodo.org/api/records/'+rid,accept=accept)
            actual = broker.last_response if broker is not None else None
            if actual is not None:
                runtime.need(actual.url=='https://zenodo.org/api/records/'+rid, 'EXACT_ACTUAL_OWNER_METADATA_URL')
                credential_guard(actual.body)
            encoded=json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()
            runtime.need(memory_token.encode()not in encoded,'CREDENTIAL_IN_OWNER_BODY')
            folder=output/'observations'/f'{len(observed)+1:04d}';folder.mkdir(parents=True,exist_ok=False)
            path=folder/'ACTUAL_BODY.json'
            with path.open('xb')as stream:stream.write(encoded)
            raw_path=folder/'ACTUAL_RAW_HTTP_BODY.json' if actual is not None else None
            if raw_path is not None:
                with raw_path.open('xb')as stream:stream.write(actual.body)
            receipt=t.out/f'{t.sequence:03d}_GET.json'
            info={'method':'GET','record_id':rid,'accept':accept,'authentication':'OWNER','owner_id':'1591505',
                  'observed_at_utc':actual.body_completed_at_utc if actual is not None else __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                  'retained_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                  'actual_raw_http_body':None if raw_path is None else {'path':str(raw_path),'sha256':runtime.sha(actual.body)},
                  'transport_receipt':{'path':str(receipt),'sha256':runtime.sha(owned_read(receipt))},
                  'actual_complete_body':{'path':str(path),'sha256':runtime.sha(encoded)},
                  'reuse_scope':'THIS_BOUND_900_SECOND_OPERATION_ONLY','admission_cached':False}
            stamp=folder/'OBSERVATION.json'
            with stamp.open('x')as stream:json.dump(info,stream,sort_keys=True,indent=2);stream.write('\n')
            observed[key]={'path':path,'inputs':[(p,runtime.sha(owned_read(p)))for p in([path,receipt,stamp]+([raw_path]if raw_path is not None else[]))]}
        # Exact owned buffer and JSON parsing are separate: no caller-minted
        # parse frame crosses the trusted physical-reader boundary.
        return json.loads(replay(observed[key]))
    def download(rid,name):
        nonlocal sequence
        unexpired()
        runtime.need(Path(name).name==name,'OWNER_BYTE_BASENAME')
        key=(rid,name)
        if key in bodies:return replay(bodies[key])
        runtime.need(broker is None,'ONLY_CLOSED_PREFETCHED_HEALTH_CONTENT')
        url='https://zenodo.org/api/records/'+rid+'/files/'+name+'/content'
        start_get_clock()
        request=urllib.request.Request(url,headers={'Authorization':'Bearer '+memory_token,'Accept':'*/*'})
        with opener.open(request,timeout=120)as response:
            runtime.need(response.status==200 and response.geturl()==url,'EXACT_OWNER_BYTE_URL');raw=response.read()
        return retain_content(rid,name,raw,url,
            __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat())
    def retain_content(rid,name,raw,url,completed_utc):
        nonlocal sequence
        unexpired()
        if broker is not None:credential_guard(raw)
        runtime.need(type(raw)is bytes and url=='https://zenodo.org/api/records/'+rid+'/files/'+name+'/content',
                     'EXACT_ACTUAL_OWNER_CONTENT_IDENTITY')
        key=(rid,name);runtime.need(key not in bodies,'ONE_CONTENT_RETENTION_ONLY')
        sequence+=1;folder=output/'bytes'/f'{sequence:04d}';folder.mkdir(parents=True,exist_ok=False)
        with(folder/name).open('xb')as stream:stream.write(raw)
        stamp=folder/'GET.json'
        with stamp.open('x')as stream:json.dump({'method':'GET','url':url,'authentication':'OWNER','owner_id':'1591505',
            'accept':'*/*','sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
            'observed_at_utc':completed_utc,
            'retained_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
            'reuse_scope':'THIS_BOUND_900_SECOND_OPERATION_ONLY','admission_cached':False},stream,sort_keys=True,indent=2);stream.write('\n')
        bodies[key]={'path':folder/name,'inputs':[(p,runtime.sha(owned_read(p)))for p in(folder/name,stamp)]}
        return replay(bodies[key])
    context=registry.RegistryContext(root,profile['access_registry'],download=download,
                                    observation_context=registry.CONTEXT,owner_getter=get,
                                    deadline_guard=deadline_guard)
    def assert_current():
        unexpired()
        for entry in [*observed.values(),*bodies.values()]:replay(entry)
    context.owner_evidence_directory=output
    context.assert_observation_current=assert_current
    context.begin_public_get=start_get_clock
    context.deadline_guard=deadline_guard
    def credential_guard(raw):
        runtime.need(memory_token.encode() not in raw, 'CREDENTIAL_IN_HOLD_DIAGNOSTIC')
        credential_patterns_guard(raw)
    context.credential_safe_diagnostic=credential_guard
    def process_journal(value):
        nonlocal process_sequence
        raw=json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()
        credential_guard(raw);process_sequence+=1
        folder=output/'transport'/'workers';folder.mkdir(exist_ok=True)
        path=folder/(str(process_sequence).zfill(6)+'_'+value['stage']+'.json')
        with path.open('xb')as stream:stream.write(raw)
        runtime.need(owned_read(path)==raw,'ACTUAL_OWNER_PROCESS_JOURNAL_READBACK')
    def prepare_owner_prefetch():
        nonlocal broker,t,prefetched
        unexpired()
        runtime.need(broker is None and first_get is None and not observed and not bodies and not prefetched,
                     'ONE_HEALTH_OWNER_PREFETCH_BEFORE_FIRST_GET')
        batch=getattr(context,'scientific_batch',None)
        runtime.need(batch is not None and batch.prepared and not batch.closed,
                     'COMPLETE_READONLY_SCIENCE_BATCH_BEFORE_OWNER_PREFETCH')
        data=scientific_data(root)
        runtime.need(data.scan_data is not None and not data.cas_events and data.pending_cas is None,
                     'READONLY_COMPLETE_SCAN_BEFORE_OWNER_PREFETCH')
        source_manifest=runtime.build_worker_source_manifest(root,profile_binding)
        broker=owner_worker.TransportBroker(operation_nonce=batch.operation,token=memory_token,
            source_manifest=source_manifest,
            source_guard=lambda:runtime.refresh_worker_source_manifest_data(root,source_manifest),
            start_get_clock=start_get_clock,
            observation_deadline=lambda:None if first_get is None else first_get+OBSERVATION_SECONDS,
            deadline_guard=deadline_guard,journal=process_journal)
        t=transport.ZenodoTransport('zenodo.org',memory_token,output/'transport',
                                  opener=owner_worker.MemoryOpener(broker))
        entries=context._registry()[0]['entries']
        runtime.need(len(entries)==7 and len({e['record_id']for e in entries})==7
                     and all(e['archive']is not None for e in entries),'COMPLETE_SEVEN_HEALTH_COPY_ENTRIES')
        pairs={entry['record_id']:(get(entry['record_id'],registry.CONTEXT['legacy_accept']),
            get(entry['record_id'],registry.CONTEXT['native_accept']))for entry in entries}
        descriptors=[]
        for entry in entries:
            correction=runtime.object_at(root,entry['access_correction'])[2]
            receipt=runtime.object_at(root,entry['registration'])[2]
            manifest_binding=receipt['digest_manifest']
            manifest_raw=runtime.read_data_file(root,manifest_binding['path'],
                expected_sha256=manifest_binding['sha256'])[1]
            archive_raw=runtime.read_data_file(root,entry['archive']['path'],
                expected_sha256=entry['archive']['sha256'])[1]
            runtime.need(set(correction)==importlib.import_module('manuscript_access_correction').FIELDS
                and correction['record_id']==entry['record_id']
                and correction['source_manifest_sha256']==runtime.sha(manifest_raw)
                and correction['source_archive_sha256']==runtime.sha(archive_raw),
                'EXACT_PREFETCH_MANIFEST_AND_ARCHIVE_BINDINGS')
            bindings=[profile['access_registry'],entry['registration'],entry['archive'],
                      entry['access_correction'],entry['user_authority'],manifest_binding]
            for source_binding in bindings:runtime.read(root,source_binding)
            for role,key in (('ORIGINAL','original_files'),('MANUSCRIPT','copies')):
                for row in correction[key]:
                    name=row['filename']
                    descriptors.append({'record_id':entry['record_id'],'filename':name,
                        'url':'https://zenodo.org/api/records/'+entry['record_id']+'/files/'+name+'/content',
                        'bytes':row['bytes'],'sha256':row['sha256'],'md5':row['md5'],
                        'source_role':role,'source_bindings':bindings})
        raw=json.dumps({'operation_nonce':batch.operation,'descriptors':descriptors},
                       sort_keys=True,ensure_ascii=False,allow_nan=False).encode()
        credential_guard(raw);path=output/'observations'/'CLOSED_CONTENT_ALLOWLIST.json'
        with path.open('xb')as stream:stream.write(raw)
        runtime.need(owned_read(path)==raw,'EXACT_CLOSED_CONTENT_ALLOWLIST_READBACK')
        responses=broker.prefetch_content(descriptors,pairs)
        runtime.need(len(responses)==100 and not broker.active_children,'COMPLETE_TERMINAL_OWNER_CONTENT')
        for (rid,name),response in sorted(responses.items()):
            runtime.need(response.status==200 and response.actual_child_exit_code==0,
                         'ACTUAL_OWNER_CONTENT_NORMAL_EXIT')
            retain_content(rid,name,response.body,response.url,response.body_completed_at_utc)
        prefetched=True
    context.prepare_owner_prefetch=prepare_owner_prefetch
    context.owner_transport_records=lambda:[]if broker is None else broker.records
    context.owner_header_dispatch_records=lambda:[]if broker is None else broker.header_dispatch_records
    def begin_operation():
        runtime.need(not operation_state['closed'],'OBSERVATION_OPERATION_ALREADY_CLOSED')
        operation_state['depth']+=1
    def end_operation(*,failed):
        runtime.need(operation_state['depth']>0,'OBSERVATION_SCOPE_BALANCE')
        operation_state['depth']-=1
        if failed or operation_state['depth']==0:
            try:
                if broker is not None:
                    if broker.active_children:broker.cancel()
                    broker.close()
            finally:operation_state['closed']=True
    context.begin_observation_operation=begin_operation
    context.end_observation_operation=end_operation
    context.observation_timing=lambda:{'elapsed_seconds':time.monotonic()-opened,
        'pre_get_scientific_seconds':(first_get if first_get is not None else time.monotonic())-opened,
        'observation_elapsed_seconds':time.monotonic()-first_get if first_get is not None else None,
        'clock_start':'FIRST_ACTUAL_GET','limit_seconds':OBSERVATION_SECONDS,'owner_api_views':len(observed),'file_bodies':len(bodies),
        'same_operation_byte_replay':True,'admission_cached':False,
        'owner_transport':None if broker is None else {'requests':len(broker.records),
            'active_children':list(broker.active_children),'header_dispatches':len(broker.header_dispatch_records),
            'header_dispatch_records':broker.header_dispatch_records,
            'request_records':broker.records,
            'content_prefetched':prefetched,'absolute_request_seconds':120,'max_http_children':6}}
    return context


def credential_patterns_guard(raw):
    import re
    runtime.need(not re.search(rb'(?i)(?:bearer[ \t]+[^ \t\r\n\"<>]+|(?:access_token|api_key|authorization)[\" \t]*[:=]|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})', raw),
                 'CREDENTIAL_PATTERN_IN_HOLD_DIAGNOSTIC')


def retain_comparator_hold(previous, baseline, result, context, exc, *, phase):
    """Retain genuine failed comparator inputs only; preserve its exception.

    No source/science read, GET, predicate replay or qualifier is introduced.
    A retention error is attached as a type-only note; it never masks the
    actual complete-population failure or supplies any runtime admission.
    """
    try:
        output = getattr(context, 'owner_evidence_directory', None)
        scanner = getattr(context, 'credential_safe_diagnostic', None)
        runtime.need(output is not None and callable(scanner), 'OWNER_HOLD_DIAGNOSTIC_CONTEXT')
        timing = getattr(context, 'observation_timing', None)
        value = {'standard': 'VRS-GENUINE-COMPLETE-REGISTRATION-REPLAY-HOLD-1',
                 'status': 'HOLD_GENUINE_COMPLETE_REGISTRATION_COMPARATOR', 'phase': phase,
                 'actual_exception_type': type(exc).__name__, 'actual_exception_message': str(exc),
                 'expected_publication_entities': previous.get('publication_entities', []),
                 'actual_publication_entities': result.get('publication_entities', []),
                 'qualification_baseline': baseline,
                 'publication_holds': result.get('publication_holds'),
                 'publication_registration_defects': result.get('publication_registration_defects'),
                 'publication_registration_summary': result.get('publication_registration_summary'),
                 'publication_registration_enforcement_acceptable': result.get('publication_registration_enforcement_acceptable'),
                 'observation_timing': timing() if callable(timing) else None,
                 'retention_writes': 1, 'certifies': False, 'cached_admission': False}
        raw = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
        scanner(raw); credential_patterns_guard(raw)
        path = Path(output) / 'COMPLETE_REGISTRATION_REPLAY_HOLD.json'
        runtime.need(Path(output).is_dir() and not any(p.is_symlink() for p in (path, *path.parents)),
                     'OWNER_HOLD_DIAGNOSTIC_REGULAR_OUTPUT')
        token = _HASHING.set(True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            first = path.stat(); readback = path.read_bytes(); last = path.stat()
            runtime.need(readback == raw and runtime.file_identity(first) == runtime.file_identity(last)
                         and not any(p.is_symlink() for p in (path, *path.parents)), 'GENUINE_HOLD_DIAGNOSTIC_READBACK')
            context.comparator_hold_diagnostic = {'path': str(path), 'sha256': runtime.sha(readback)}
        finally: _HASHING.reset(token)
    except Exception as retention_error:
        exc.add_note('HOLD diagnostic retention unavailable: ' + type(retention_error).__name__)


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
        data.require_platform_read();data.assert_current();data.scan_data=deepcopy(scanned)


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
        try:
            original.preserving_population(previous,baseline,result)
        except Exception as exc:
            retain_comparator_hold(previous,baseline,result,registry_context,exc,phase='FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY')
            raise
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
        _,raw,previous=runtime.json_file(root,canonical)
        runtime.need(runtime.sha(raw) == expected_sha256, 'CANONICAL_EXACT_PREDECESSOR')
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
        actual = runtime.json_file(root,canonical)[2]
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
        ledger = runtime.json_file(root,root/'RESEARCH_PIPELINE_v2/corpus_ledger.json')[2]
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
            deadline=getattr(registry_context,'deadline_guard',None)
            if deadline is not None:deadline()
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
                current=runtime.json_file(root,canonical)[2]
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
