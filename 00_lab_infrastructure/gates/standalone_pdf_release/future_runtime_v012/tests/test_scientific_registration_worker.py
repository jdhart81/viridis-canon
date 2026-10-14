"""Synthetic live-function transport checks; no actual scientific execution."""
from contextlib import ExitStack
import contextlib
import ast
import copy
from copy import deepcopy
import datetime as dt
import json
import io
import os
import re
import marshal
import signal
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import types
import unittest
import warnings
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime
import packaging_catalog as catalog
import scientific_registration_worker as science


class ScienceTransportTests(unittest.TestCase):
    def test_deterministic_code_frame_survives_retained_literal_refs_intern_and_hot_calls(self):
        namespace={'__name__':'synthetic_code_data'}
        exec(compile("def toy():\n return {'value':'synthetic non-interned phrase / 719302','number':1791983972865477715}\n",'<synthetic-code-data>','exec'),namespace)
        toy=namespace['toy'];before=science._definition(toy)
        old_before=marshal.dumps(toy.__code__)
        result=toy();old_after=marshal.dumps(toy.__code__)
        self.assertNotEqual(old_before,old_after,'portable control must reproduce allocation-sensitive rawmarshal')
        self.assertEqual(before,science._definition(toy))
        refs=list(toy.__code__.co_consts)
        self.assertEqual(before,science._definition(toy))
        literal=next(v for v in refs if type(v)is str and 'non-interned phrase' in v)
        interned=sys.intern(literal);self.assertIs(interned,literal)
        self.assertEqual(before,science._definition(toy))
        for _ in range(20000):toy()
        self.assertEqual(before,science._definition(toy))
        self.assertEqual(before,json.loads(science.raw(before)))
        self.assertEqual(before['code_sha256'],runtime.sha(science.raw(before['code_projection'])))
        self.assertEqual(result['value'],literal)

    def test_code_projection_covers_each_public_field_and_derived_view(self):
        def toy(value,*args,flag=1,**kwargs):
            local=value+flag
            return local
        code=toy.__code__;frame=science._code_projection(code)
        self.assertEqual(frame['public_fields'],sorted(n for n in dir(code)if n.startswith('co_')))
        self.assertEqual(set(frame['fields'])|set(frame['derived']),set(frame['public_fields']))
        self.assertEqual(frame['fields']['co_code'],{'kind':'bytes','hex':code.co_code.hex()})
        self.assertEqual(frame['fields']['co_lnotab'],{'kind':'bytes','hex':science._code_lnotab(code).hex()})
        for name in('co_lines','co_positions','co_branches'):
            if hasattr(code,name):self.assertEqual(frame['derived'][name],science._code_constant(tuple(getattr(code,name)())))
        replacements={
            'co_argcount':0,'co_posonlyargcount':1,'co_kwonlyargcount':0,
            'co_nlocals':code.co_nlocals+1,'co_stacksize':code.co_stacksize+1,
            'co_flags':code.co_flags^0x20,'co_consts':code.co_consts+('another constant',),
            'co_names':code.co_names+('another_name',),
            'co_varnames':code.co_varnames[:-1]+('changed_varname',),
            'co_filename':code.co_filename+'-changed','co_name':code.co_name+'-changed',
            'co_qualname':code.co_qualname+'-changed','co_firstlineno':code.co_firstlineno+1,
            'co_linetable':b'','co_exceptiontable':b'\x80\x01\x01\x00',
            'co_freevars':code.co_freevars+('new_freevar',),
            'co_cellvars':code.co_cellvars+('new_cellvar',)}
        # For nlocals Python requires one corresponding extra lexical name.
        for name,value in replacements.items():
            with self.subTest(field=name):
                changes={name:value}
                if name=='co_nlocals':changes['co_varnames']=code.co_varnames+('extra_local',)
                changed=code.replace(**changes)
                self.assertNotEqual(frame,science._code_projection(changed))
        # A legal NOP replaces the entry RESUME; never execute modified code.
        changed=code.replace(co_code=b'\x09\x00'+code.co_code[2:])
        self.assertNotEqual(frame['fields']['co_code'],science._code_projection(changed)['fields']['co_code'])
        with patch.object(science,'dir',return_value=dir(code)+['co_unknown_semantic_field'],create=True):
            with self.assertRaisesRegex(runtime.PackagingHold,'COMPLETE_KNOWN_PUBLIC_CODE_FIELDS'):
                science._code_projection(code)

    def test_lnotab_data_warning_scope_is_exact_restored_and_does_not_hide_other_warnings(self):
        def toy():return 1
        outer_filters=warnings.filters;before=list(warnings.filters);stderr=io.StringIO()
        with warnings.catch_warnings():
            warnings.simplefilter('always',DeprecationWarning)
            scope_filters=warnings.filters;scope_before=list(warnings.filters)
            with contextlib.redirect_stderr(stderr):
                frame=science._code_projection(toy.__code__)
                self.assertEqual(warnings.filters,scope_before)
                self.assertIs(warnings.filters,scope_filters)
                warnings.warn('unrelated scientific warning remains visible',DeprecationWarning)
                warnings.warn('co_lnotab is deprecated, use co_lines instead.',UserWarning)
            self.assertNotIn('DeprecationWarning: co_lnotab is deprecated',stderr.getvalue())
            self.assertIn('unrelated scientific warning remains visible',stderr.getvalue())
            self.assertIn('UserWarning: co_lnotab is deprecated',stderr.getvalue())
            self.assertEqual(frame['fields']['co_lnotab']['hex'],science._code_lnotab(toy.__code__).hex())
            with patch.object(warnings,'filterwarnings',side_effect=ValueError('synthetic exact accessor setup failure')):
                with self.assertRaisesRegex(ValueError,'synthetic exact accessor setup failure'):
                    science._code_lnotab(toy.__code__)
            self.assertEqual(warnings.filters,scope_before)
            self.assertIs(warnings.filters,scope_filters)
            class UntrustedAccessor:
                @property
                def co_lnotab(self):
                    raise AssertionError('caller-defined getter must never execute')
            with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_IMMUTABLE_CODE_TYPE'):
                science._code_lnotab(UntrustedAccessor())
        self.assertEqual(warnings.filters,before)
        self.assertIs(warnings.filters,outer_filters)
        # The actual implementation also avoids its own warning when hosted
        # as __main__, the ordinary child entry's module identity.
        tree=ast.parse((HERE/'scientific_registration_worker.py').read_bytes())
        helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_code_lnotab')
        namespace={'warnings':warnings,'re':re,'runtime':runtime,'types':types,'__name__':'__main__'}
        exec(compile(ast.Module(body=[helper],type_ignores=[]),'<synthetic-main-data-accessor>','exec'),namespace)
        captured=io.StringIO()
        with warnings.catch_warnings(),contextlib.redirect_stderr(captured):
            warnings.simplefilter('always',DeprecationWarning)
            self.assertEqual(namespace['_code_lnotab'](toy.__code__),science._code_lnotab(toy.__code__))
        self.assertEqual(captured.getvalue(),'')

    def test_typed_code_constants_preserve_bits_nested_code_order_and_json_shape(self):
        nan_a=struct.unpack('!d',bytes.fromhex('7ff8000000000001'))[0]
        nan_b=struct.unpack('!d',bytes.fromhex('7ff8000000000002'))[0]
        values=(None,Ellipsis,False,0,0.0,-0.0,nan_a,nan_b,float('inf'),
                complex(-0.0,0.0),complex(0.0,-0.0),b'\x00\xff','\ud800',
                (1,'x'),frozenset({1,'x',b'x'}),slice(None,3,-1))
        encoded=[science._code_constant(v)for v in values]
        self.assertEqual(encoded,json.loads(science.raw(encoded)))
        self.assertNotEqual(encoded[2],encoded[3])
        self.assertNotEqual(encoded[4],encoded[5])
        self.assertNotEqual(encoded[6],encoded[7])
        self.assertNotEqual(encoded[9],encoded[10])
        self.assertEqual(encoded[12],{'kind':'str','utf8_surrogatepass_hex':'eda080'})
        self.assertNotEqual(science._code_constant((1,2)),science._code_constant((2,1)))
        self.assertEqual(science._code_constant(frozenset([1,'x',b'x'])),science._code_constant(frozenset([b'x','x',1])))
        namespace={};exec(compile('def outer():\n def inner(): return 7\n return inner\n','<nested-code-data>','exec'),namespace)
        outer=namespace['outer'].__code__;original=science._code_projection(outer)
        nested=next(c for c in outer.co_consts if type(c)is types.CodeType)
        changed_nested=nested.replace(co_consts=tuple(8 if type(c)is int and c==7 else c for c in nested.co_consts))
        changed=outer.replace(co_consts=tuple(changed_nested if c is nested else c for c in outer.co_consts))
        self.assertNotEqual(original,science._code_projection(changed))
        self.assertEqual(original,json.loads(science.raw(original)))
        class ImpostorInt(int):pass
        for value in([1],{'x':1},bytearray(b'x'),ImpostorInt(1),slice([1],2,None),object()):
            with self.subTest(type=type(value).__name__):
                with self.assertRaisesRegex(runtime.PackagingHold,'UNSUPPORTED_IMMUTABLE_CODE_CONSTANT'):
                    science._code_constant(value)

    def test_stable_code_hash_does_not_drop_defaults_kwargs_or_literal_globals(self):
        namespace={'SOURCE_TOGGLE':1,'__name__':'synthetic_code_data'}
        exec(compile('def toy(value=7,*,flag=2):\n return SOURCE_TOGGLE+value+flag\n','/synthetic-code-data/toy.py','exec'),namespace)
        toy=namespace['toy']
        with patch.object(science,'ROOT',Path('/synthetic-code-data')):
            before=science._definition(toy);toy()
            self.assertEqual(before,science._definition(toy))
            toy.__defaults__=(8,);self.assertNotEqual(before,science._definition(toy));toy.__defaults__=(7,)
            toy.__kwdefaults__={'flag':3};self.assertNotEqual(before,science._definition(toy));toy.__kwdefaults__={'flag':2}
            namespace['SOURCE_TOGGLE']=2;self.assertNotEqual(before,science._definition(toy));namespace['SOURCE_TOGGLE']=1
            self.assertEqual(before,science._definition(toy))

    def test_before_and_after_state_mismatch_retains_full_typed_data_before_same_hold(self):
        for phase,returned,reason in(('COMPARE_EVALUATION_STATE_BEFORE',False,'LIVE_ORIGINAL_FUNCTION_DEFAULT_GLOBALS'),
                                      ('COMPARE_EVALUATION_STATE_AFTER',True,'LIVE_ORIGINAL_GLOBALS_CHANGED_DURING_CALL')):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory()as folder:
                output=Path(folder).resolve();cfg_path=output/'config.json';cfg_path.write_text('{}')
                expected=[{'definition':{'code_projection':{'fields':{'co_flags':{'kind':'int','value':3}}}}}]
                actual=deepcopy(expected);actual[0]['definition']['code_projection']['fields']['co_flags']['value']=4
                config={'operation':'a'*32,'job_nonce':'b'*32,'stage':'build','ordinal':0,'evaluation_state':expected}
                state={'phase':phase,'output':output,'original_call_started':returned,'original_call_returned':returned}
                config_binding={'path':str(cfg_path),'sha256':runtime.sha(cfg_path.read_bytes())}
                with patch.object(science,'evaluation_state',return_value=actual)as evaluated:
                    with self.assertRaisesRegex(runtime.PackagingHold,reason):
                        science._require_evaluation_state(config,state,config_binding,reason)
                evaluated.assert_called_once_with()
                evidence=json.loads((output/(phase+'_MISMATCH.json')).read_bytes())
                self.assertEqual(evidence['expected'],expected);self.assertEqual(evidence['actual'],actual)
                self.assertEqual(evidence['config'],config_binding)
                self.assertEqual(evidence['phase'],phase)
                self.assertEqual(evidence['original_call_returned'],returned)
                self.assertEqual(evidence['differences'][0]['path'],[0,'definition','code_projection','fields','co_flags','value'])
                self.assertEqual(state['evaluation_state_mismatch'],science.binding(output/(phase+'_MISMATCH.json')))
                self.assertFalse(evidence['source_finally_claimed']);self.assertFalse(evidence['result_accepted'])
                self.assertFalse(evidence['certifies'])

    def test_mismatch_evidence_credential_or_write_hold_does_not_mask_scientific_state_hold(self):
        for fault in('credential','write'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory()as folder:
                output=Path(folder).resolve();config={'operation':'a'*32,'job_nonce':'b'*32,'stage':'build','ordinal':0,'evaluation_state':[]}
                state={'phase':'COMPARE_EVALUATION_STATE_AFTER','output':output,'original_call_started':True,'original_call_returned':True}
                actual=[{'changed':'value'}]if fault=='write'else[{'authorization':'Bearer synthetic-secret'}]
                with ExitStack()as stack:
                    stack.enter_context(patch.object(science,'evaluation_state',return_value=actual))
                    if fault=='write':stack.enter_context(patch.object(science,'retain',side_effect=OSError('synthetic retention fault')))
                    with self.assertRaisesRegex(runtime.PackagingHold,'LIVE_ORIGINAL_GLOBALS_CHANGED_DURING_CALL')as caught:
                        science._require_evaluation_state(config,state,{'path':str(output/'config.json'),'sha256':'1'*64},'LIVE_ORIGINAL_GLOBALS_CHANGED_DURING_CALL')
                self.assertTrue(any('retention unavailable'in note for note in caught.exception.__notes__))
                self.assertNotIn('evaluation_state_mismatch',state)
                self.assertEqual(list(output.iterdir()),[])

    def test_equal_fresh_state_creates_no_mismatch_evidence_or_cached_verdict(self):
        with tempfile.TemporaryDirectory()as folder:
            output=Path(folder).resolve();config={'evaluation_state':[{'value':1}]}
            state={'output':output,'phase':'COMPARE_EVALUATION_STATE_BEFORE'}
            with patch.object(science,'evaluation_state',side_effect=[[{'value':1}],[{'value':2}]])as evaluated:
                science._require_evaluation_state(config,state,{},'UNCHANGED_EQUALITY')
                self.assertEqual(list(output.iterdir()),[])
                # A second fresh mismatch remains HOLD, even though the first matched.
                with self.assertRaisesRegex(runtime.PackagingHold,'UNCHANGED_EQUALITY'):
                    science._require_evaluation_state(config,state,{},'UNCHANGED_EQUALITY')
                self.assertEqual(evaluated.call_count,2)

    def test_actual_stdlib_re_default_v008_hold_v009_identity_data(self):
        sentinel=getattr(re,'_zero_sentinel',None)
        if sentinel is None:
            self.assertIsNone(science._RE_ZERO_SENTINEL_TYPE)
            class ArbitraryZero(int):pass
            with self.assertRaisesRegex(runtime.PackagingHold,'UNSUPPORTED_REFERENCED'):
                science._dependency(ArbitraryZero(0))
            return
        # Execute only these serializer definitions, never original science.
        old_path=HERE.parent/'future_runtime_v008/scientific_registration_worker.py'
        old_raw=old_path.read_bytes()
        self.assertEqual(runtime.sha(old_raw),'622846b2b6f5f371e9aed3a0c24479bf52af48b60374ad474ea0c01d44b71c4f')
        tree=ast.parse(old_raw);definitions=[n for n in tree.body
            if isinstance(n,ast.FunctionDef)and n.name in('_definition','_dependency')]
        namespace={'types':types,'re':re,'Path':Path,'ROOT':science.ROOT,
                   'runtime':runtime,'marshal':marshal,'raw':science.raw}
        exec(compile(ast.Module(body=definitions,type_ignores=[]),str(old_path),'exec'),namespace)
        with self.assertRaisesRegex(runtime.PackagingHold,'UNSUPPORTED_REFERENCED_SCIENTIFIC_GLOBAL:_ZeroSentinel'):
            namespace['_dependency'](re)
        value=science._dependency(re);self.assertEqual(value['name'],'re')
        for fn in('sub','subn'):
            for key in('count','flags'):
                self.assertIs(getattr(re,fn).__kwdefaults__[key],sentinel)
                default=value['source_defined_functions'][fn]['keyword_defaults'][key]
                self.assertEqual(default['kind'],'STDLIB_RE_ZERO_SENTINEL')
                self.assertEqual(default['integer_value'],0)
                self.assertEqual(default['instance_state'],{})
                self.assertEqual(default['type_definition']['name'],'_ZeroSentinel')
        self.assertNotEqual(science._dependency(sentinel),science._dependency(0))
        self.assertEqual(value,science._dependency(re))

    def test_real_re_sentinel_copy_impostor_and_binding_drift_rejected(self):
        sentinel=getattr(re,'_zero_sentinel',None)
        if sentinel is None:self.skipTest('Python before re identity-sensitive zero default')
        class ArbitraryZero(int):pass
        had_slotnames='__slotnames__'in vars(type(sentinel))
        try:
            for value in(copy.copy(sentinel),type(sentinel)(0),ArbitraryZero(0)):
                with self.subTest(kind=type(value).__name__),self.assertRaises(runtime.PackagingHold):
                    science._dependency(value)
        finally:
            # copy.copy adds a stdlib scratch cache to this otherwise empty
            # class; restore the exact test-process import-time definition.
            if not had_slotnames and '__slotnames__'in vars(type(sentinel)):
                del type(sentinel).__slotnames__
        for name,value in(('_zero_sentinel',type(sentinel)(0)),('_ZeroSentinel',ArbitraryZero)):
            with patch.object(re,name,value),self.assertRaisesRegex(runtime.PackagingHold,'EXACT_STDLIB_RE_ZERO_SENTINEL_IDENTITY_AND_BINDING'):
                science._dependency(sentinel)
        self.assertEqual(science._dependency(sentinel)['integer_value'],0)

    def test_real_re_sentinel_state_and_class_definition_drift_rejected(self):
        sentinel=getattr(re,'_zero_sentinel',None)
        if sentinel is None:self.skipTest('Python before re identity-sensitive zero default')
        sentinel.synthetic_state='changed'
        try:
            with self.assertRaisesRegex(runtime.PackagingHold,'CLASS_VALUE_AND_STATE'):
                science._dependency(sentinel)
        finally:del sentinel.synthetic_state
        for name,value in(('__doc__','changed'),('synthetic_added_field',True)):
            with patch.object(type(sentinel),name,value,create=True),self.assertRaisesRegex(runtime.PackagingHold,'CLASS_VALUE_AND_STATE'):
                science._dependency(sentinel)
        original_name=type(sentinel).__name__
        try:
            type(sentinel).__name__='impostor'
            with self.assertRaisesRegex(runtime.PackagingHold,'CLASS_VALUE_AND_STATE'):
                science._dependency(sentinel)
        finally:type(sentinel).__name__=original_name
        self.assertEqual(science._dependency(sentinel)['instance_state'],{})

    def test_re_sentinel_absence_does_not_normalize_unknown_int_subclasses(self):
        class ArbitraryZero(int):pass
        with patch.object(science,'_RE_ZERO_SENTINEL',None),patch.object(science,'_RE_ZERO_SENTINEL_TYPE',None):
            with self.assertRaisesRegex(runtime.PackagingHold,'UNSUPPORTED_REFERENCED'):
                science._dependency(ArbitraryZero(0))
            self.assertEqual(science._dependency(0),0)

    def fixture(self, tmp):
        dependency_patch=patch.object(science,'evaluation_state',return_value=None)
        dependency_patch.start();self.addCleanup(dependency_patch.stop)
        root = Path(tmp).resolve(); output = root/'reports/verification-coverage/owner'
        output.mkdir(parents=True)
        context = SimpleNamespace(owner_evidence_directory=output, deadline_guard=lambda:None,
                                  scientific_consumer=None, scientific_batch=None)
        data = catalog.ScientificInputData(root, context)
        data.inventory_reader = lambda: {'synthetic_inventory': ['complete']}
        data.inventory = data.inventory_reader()
        rows = [{'name':'source.py','path':str(root/'source.py'),'sha256':'1'*64}]
        with patch.object(science, 'source_rows', return_value=rows):
            batch = science.ScienceBatch(root, {'path':'profile','sha256':'2'*64}, context, {}, {}, output)
        batch.prepared = True
        batch.output.mkdir()
        return root, context, data, batch, rows

    def prepare_fixture(self, tmp, mutate=None):
        """Real planner/config writes; original evaluation and authority are stubs."""
        root=Path(tmp).resolve();output=root/'reports/verification-coverage/owner'
        output.mkdir(parents=True)
        ids=('23226761','23246368','23290448','23290748','23291581','23292552','23308138')
        entries=[]
        for ordinal,rid in enumerate(ids):
            binding={'path':str(root/(rid+'-registration.json')),'sha256':str(ordinal+1)*64}
            chain=None if ordinal==6 else {key:{'path':str(root/(rid+'-'+key+'.json')),
                'sha256':'a'*64}for key in('baseline_legacy','baseline_native','creation','publish')}
            if chain is not None:chain['stage']='BEFORE_ACCESS'
            entries.append({'record_id':rid,'registration':binding,
                'archive':{'path':str(root/(rid+'.zip')),'sha256':'b'*64},'prior_chain':chain})
        previous={'publication_entities':[{'entity_type':'METHODS_DIGEST_GROUP',
            'registration_receipt':entry['registration']}for entry in entries]}
        if mutate is not None:mutate(entries,previous)
        baseline={'tree_root':str(root),'run_entities':[],'synthetic_science':'not an admission'}
        context=SimpleNamespace(_registry=lambda:({'entries':deepcopy(entries)},b'SYNTHETIC_REGISTRY'),
            scientific_consumer=None,scientific_batch=None)
        source_rows=[{'name':'synthetic_source.py','path':str(root/'synthetic_source.py'),'sha256':'c'*64}]
        patches=ExitStack();self.addCleanup(patches.close)
        patches.enter_context(patch.object(science,'source_rows',return_value=source_rows))
        patches.enter_context(patch.object(science,'evaluation_state',return_value={'synthetic':'DATA only'}))
        patches.enter_context(patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'SOURCE fixture'}))
        patches.enter_context(patch.object(catalog,'scientific_data',return_value=SimpleNamespace(
            scan_data=baseline,cas_events=[],pending_cas=None)))
        batch=science.ScienceBatch(root,{'path':'synthetic-profile','sha256':'d'*64},context,previous,baseline,output)
        plans=[]
        def execute(planned):
            plans.extend(deepcopy(planned))
            for config,bound in planned:
                batch.jobs[batch._key(config['stage'],config['binding'])]={'synthetic':'not executed'}
        patches.enter_context(patch.object(batch,'_execute',side_effect=execute))
        patches.enter_context(patch.object(batch,'_fresh_union'))
        return batch,entries,plans

    def test_actual_six_before_access_one_none_plan_preserves_exact35_saved_calls(self):
        with tempfile.TemporaryDirectory()as tmp:
            batch,entries,plans=self.prepare_fixture(tmp);original=deepcopy(entries);batch.prepare()
            self.assertEqual(len(plans),35);self.assertEqual(entries,original)
            self.assertEqual(len({c['job_nonce']for c,b in plans}),35)
            self.assertEqual({(c['stage'],c['ordinal'])for c,b in plans},
                {(stage,n)for stage in science.STAGES for n in range(7)})
            for config,bound in plans:
                self.assertEqual(config['binding'],entries[config['ordinal']]['registration'])
                self.assertEqual(config['evaluation_kwargs'],{'views':None,'prior_chain_receipts':None})
                self.assertEqual(config['ledger']is None,config['stage'].startswith('labels_'))
                self.assertEqual(runtime.object_at(batch.root,bound)[2],config)
            self.assertIs(batch.context.scientific_batch,batch)

    def test_chain_only_after_access_and_malformed_batch_hold_before_any_worker_plan(self):
        mutations=[lambda e,p:e[0].update(archive=None),
            lambda e,p:e[0]['prior_chain'].update(stage='AFTER_ACCESS'),
            lambda e,p:e[0]['prior_chain'].update(stage='UNKNOWN'),
            lambda e,p:e[0]['prior_chain'].update(extra='not permitted'),
            lambda e,p:e[0]['prior_chain'].pop('creation'),
            lambda e,p:e[0].update(prior_chain=[]),lambda e,p:e.pop()]
        for mutate in mutations:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory()as tmp:
                batch,entries,plans=self.prepare_fixture(tmp,mutate)
                with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_SEVEN_ACCESS_SAVED_REGISTRATION_BATCH'):
                    batch.prepare()
                self.assertEqual(plans,[]);self.assertFalse(batch.output.exists())
                self.assertIsNone(batch.context.scientific_batch)

    def test_before_access_does_not_permit_missing_or_different_original_group_bindings(self):
        with tempfile.TemporaryDirectory()as tmp:
            batch,entries,plans=self.prepare_fixture(tmp,lambda e,p:p['publication_entities'].pop())
            with self.assertRaisesRegex(runtime.PackagingHold,'COMPLETE_SEVEN_GROUP_BINDINGS'):batch.prepare()
            self.assertEqual(plans,[]);self.assertFalse(batch.output.exists())

    def slot(self, batch, stage='build', ledger=None, outcome='SCIENCE_RESULT'):
        bound = {'path':'registration.json','sha256':'3'*64}
        config = {'ledger':ledger, 'stage':stage, 'binding':bound}
        result = {'completed_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                  'completed_monotonic':science.time.monotonic(), 'outcome':outcome,
                  'original_hold':None, 'original_result':{'actual':'new function DATA'}}
        p = batch.output.parent/'result.json'; p.write_bytes(science.raw(result))
        slot = {'config':config,'binding':science.binding(p)}
        batch.jobs[batch._key(stage,bound)] = slot
        return bound, result

    def test_class_base_state_is_exactly_closed_under_real_json_roundtrip(self):
        class ParentA: pass
        class ParentB: pass
        class Child(ParentA,ParentB):
            def method(self,flag=False): return flag
        value=science._definition(Child)
        self.assertEqual(value['bases'],[[ParentA.__module__,ParentA.__qualname__],
                                        [ParentB.__module__,ParentB.__qualname__]])
        self.assertEqual(value,json.loads(science.raw(value)))
        # Actual stdlib regex module/sentinel DATA only. No re/science function
        # is invoked, and Python3.12 legitimately has no zero sentinel.
        module=science._dependency(re)
        self.assertEqual(module,json.loads(science.raw(module)))
        if science._RE_ZERO_SENTINEL is not None:
            sentinel=science._dependency(science._RE_ZERO_SENTINEL)
            self.assertEqual(sentinel,json.loads(science.raw(sentinel)))
            self.assertEqual(sentinel['type_definition']['bases'],[['builtins','int']])

    def test_class_identity_order_code_and_defaults_still_change_bound_state(self):
        class ParentA: pass
        class ParentB: pass
        class Child(ParentA,ParentB):
            def method(self,flag=False): return flag
        before=science._definition(Child)
        Child.__bases__=(ParentB,ParentA)
        self.assertNotEqual(science._definition(Child),before)
        self.assertEqual(science._definition(Child)['bases'],list(reversed(before['bases'])))
        Child.__bases__=(ParentA,ParentB)
        Child.method.__defaults__=(True,)
        changed=science._definition(Child)
        self.assertNotEqual(changed['methods']['method']['defaults'],before['methods']['method']['defaults'])
        Child.method.__defaults__=(False,)
        def replacement(self,flag=False): return not flag
        Child.method.__code__=replacement.__code__
        self.assertNotEqual(science._definition(Child)['methods']['method']['code_sha256'],
                            before['methods']['method']['code_sha256'])
        Child.__module__='synthetic_rebound_module'
        self.assertEqual(science._definition(Child)['module'],'synthetic_rebound_module')
        self.assertNotEqual(science._definition(Child),before)

    def test_general_tuple_dependency_kind_remains_distinct_from_list(self):
        tuple_data=science._dependency(('module','Class'))
        list_data=science._dependency(['module','Class'])
        self.assertEqual(tuple_data['kind'],'tuple');self.assertEqual(list_data['kind'],'list')
        self.assertNotEqual(tuple_data,list_data)
        self.assertEqual(tuple_data,json.loads(science.raw(tuple_data)))
        self.assertEqual(list_data,json.loads(science.raw(list_data)))
        with self.assertRaisesRegex(runtime.PackagingHold,'UNSUPPORTED_REFERENCED_SCIENTIFIC_GLOBAL'):
            science._dependency(object())

    def test_exact_five_publication_fields_only(self):
        ledger = {'tree_root':'root','run_entities':[{'id':'Run-1','status':'CERTIFIED',
                 'certificate_valid':True,'path':'paper','certificate':'actual'}],'unknown_science':'bound'}
        changed = deepcopy(ledger)
        for field in science.PUB_FIELDS: changed[field] = ['different publication control']
        self.assertEqual(science.argument_projection(ledger), science.argument_projection(changed))
        for field in ('tree_root','unknown_science'):
            item = deepcopy(ledger); item[field] = 'changed'
            self.assertNotEqual(science.argument_projection(item), science.argument_projection(ledger))
        for field in ('id','status','certificate_valid','path','certificate'):
            item = deepcopy(ledger); item['run_entities'][0][field] = 'changed'
            self.assertNotEqual(science.argument_projection(item), science.argument_projection(ledger))

    def test_one_use_stage_identity_and_output_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, batch, _ = self.fixture(tmp); bound, _ = self.slot(batch)
            with patch.object(batch,'_fresh_union') as guard:
                with self.assertRaisesRegex(runtime.PackagingHold,'STAGE_REQUIRED'):
                    batch.require(bound, views=None)
                with batch.stage('doi'):
                    with self.assertRaisesRegex(runtime.PackagingHold,'ONE_USE'):
                        batch.require(bound, views=None)
                with batch.stage('build'):
                    value = batch.require(bound, views=None); value['actual'] = 'caller mutation'
                    with self.assertRaisesRegex(runtime.PackagingHold,'ONE_USE'):
                        batch.require(bound, views=None)
                self.assertEqual(guard.call_count,1)
                self.assertEqual(runtime.object_at(batch.root,next(iter(batch.jobs.values()))['binding'])[2]['original_result'],
                                 {'actual':'new function DATA'})

    def test_wrong_kwargs_and_nonpublication_argument_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _, batch, _ = self.fixture(tmp)
            ledger = {'tree_root':str(root),'run_entities':[],'unknown':'fixed','certificate_flag':True}
            p = root/'ledger.json'; p.write_bytes(science.raw(ledger))
            bound, _ = self.slot(batch, ledger=science.binding(p))
            with batch.stage('build'), patch.object(batch,'_fresh_union'):
                with self.assertRaisesRegex(runtime.PackagingHold,'KWARGS'):
                    batch.require(bound, ledger, views={'fabricated':'pair'})
                with self.assertRaisesRegex(runtime.PackagingHold,'WHOLE_ARGUMENT'):
                    batch.require(bound, {**ledger,'unknown':'changed'}, views=None)
                with self.assertRaisesRegex(runtime.PackagingHold,'WHOLE_ARGUMENT'):
                    batch.require(bound, {**ledger,'certificate_flag':1}, views=None)
                self.assertFalse(batch.used)
                value = batch.require(bound, {**ledger,'publication_entities':['growing']}, views=None)
                self.assertEqual(value['actual'],'new function DATA')

    def test_current_complete_worker_union_body_and_inode(self):
        for change in ('bytes','inode'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root, _, data, batch, rows = self.fixture(tmp)
                p = root/'actual-input'; p.write_bytes(b'exact body'); data.record(p)
                row = deepcopy(data.inputs[str(p)])
                manifest = root/'manifest.json'; manifest.write_bytes(science.raw({
                    'status':'COMPLETE_REHASHED_OPERATION_INPUT_DATA','authorized_canonical_cas':[],
                    'inventory':data.inventory,'inputs':[row]}))
                batch.union[str(p)] = row; batch.jobs[('stage',b'key')] = {'manifest':science.binding(manifest)}
                with patch.object(catalog,'scientific_data',return_value=data), patch.object(science,'source_rows',return_value=rows):
                    batch._fresh_union()
                    if change == 'bytes': p.write_bytes(b'changed body')
                    else: p.unlink(); p.write_bytes(b'exact body')
                    with self.assertRaises(runtime.PackagingHold): batch._fresh_union()

    def test_union_cache_and_inventory_substitution_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, data, batch, rows = self.fixture(tmp)
            p = root/'actual-input'; p.write_bytes(b'exact'); data.record(p)
            row = deepcopy(data.inputs[str(p)])
            manifest = root/'manifest.json'; manifest.write_bytes(science.raw({
                'status':'COMPLETE_REHASHED_OPERATION_INPUT_DATA','authorized_canonical_cas':[],
                'inventory':data.inventory,'inputs':[row]}))
            batch.union[str(p)] = row; batch.jobs[('stage',b'key')] = {'manifest':science.binding(manifest)}
            with patch.object(catalog,'scientific_data',return_value=data), patch.object(science,'source_rows',return_value=rows):
                batch.union[str(p)] = {**row,'sha256':'0'*64}
                with self.assertRaisesRegex(runtime.PackagingHold,'SUBSTITUTION'): batch._fresh_union()
                batch.union[str(p)] = row
                data.inventory_reader = lambda:{'synthetic_inventory':['new member']}
                with self.assertRaisesRegex(runtime.PackagingHold,'INVENTORY'): batch._fresh_union()

    def test_deadline_and_cas_reject_before_input_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, context, data, batch, _ = self.fixture(tmp)
            with patch.object(catalog,'scientific_data',return_value=data), patch.object(data,'record') as read:
                def expired(): raise runtime.PackagingHold('EXPIRED900')
                context.deadline_guard = expired
                with self.assertRaisesRegex(runtime.PackagingHold,'EXPIRED900'): batch._fresh_union()
                self.assertEqual(read.call_count,0)
                context.deadline_guard = lambda:None; data.cas_events.append({'actual':'CAS'})
                with self.assertRaisesRegex(runtime.PackagingHold,'AFTER_CAS'): batch._fresh_union()
                self.assertEqual(read.call_count,0)

    def test_original_typed_hold_consumed_once(self):
        class ActualOriginalHold(ValueError): pass
        original = SimpleNamespace(__name__='actual_original',RegistrationHold=ActualOriginalHold)
        with tempfile.TemporaryDirectory() as tmp:
            _, _, _, batch, _ = self.fixture(tmp); bound, value = self.slot(batch,outcome='SCIENTIFIC_HOLD')
            value.update(original_result=None,original_hold={'module':'actual_original','class':'RegistrationHold','message':'original reason'})
            slot = next(iter(batch.jobs.values())); p = Path(slot['binding']['path']); p.write_bytes(science.raw(value));slot['binding']=science.binding(p)
            module = SimpleNamespace(_original_registrar=lambda:original)
            with patch.object(batch,'_fresh_union'), patch.object(science,'resolved_hold',return_value=ActualOriginalHold('original reason')), batch.stage('build'):
                with self.assertRaisesRegex(ActualOriginalHold,'original reason'): batch.require(bound,views=None)
                with self.assertRaisesRegex(runtime.PackagingHold,'ONE_USE'): batch.require(bound,views=None)

    def test_source_defined_hold_provenance_and_arbitrary_import_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve();p=root/'synthetic_original.py'
            p.write_text("class RegistrationHold(ValueError):pass\ndef require_registration():\n raise RegistrationHold('exact actual original reason')\n")
            module=types.ModuleType('synthetic_original');module.__file__=str(p)
            exec(compile(p.read_bytes(),str(p),'exec'),module.__dict__)
            expected=runtime.sha(p.read_bytes());scope=root/'scope.json'
            scope.write_bytes(science.raw({'purpose_source_pins':[{'name':p.name,'path':str(p),'sha256':expected}]}))
            definitions=((p.name,expected,'RegistrationHold'),)
            with patch.object(science,'SCIENTIFIC_HOLD_DEFINITIONS',definitions),patch.object(runtime,'LEGACY_SCOPE',science.binding(scope)),patch.dict(sys.modules,{'synthetic_original':module}):
                try:module.require_registration()
                except module.RegistrationHold as exc:value=science.original_hold(root,exc)
                self.assertEqual(value['module'],'synthetic_original')
                self.assertEqual(value['frames'][-1]['module'],'synthetic_original')
                rebuilt=science.resolved_hold(root,value)
                self.assertIs(type(rebuilt),module.RegistrationHold)
                self.assertEqual(str(rebuilt),'exact actual original reason')
                changed={**value,'public_source_module':'arbitrary_remote_module'}
                with patch.object(science.importlib,'import_module') as imported:
                    with self.assertRaisesRegex(runtime.PackagingHold,'CLOSED_ORIGINAL'):science.resolved_hold(root,changed)
                    imported.assert_not_called()
                forged={**value,'module':'different_unproven_alias'}
                with self.assertRaisesRegex(runtime.PackagingHold,'RAISING_SOURCE'):science.resolved_hold(root,forged)
                try:raise OSError('an infrastructure file failure')
                except OSError as exc:self.assertIsNone(science.original_hold(root,exc))

    def test_closed_scope_and_complete_count_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, context, _, batch, _ = self.fixture(tmp)
            context.scientific_consumer = batch.require; context.scientific_batch = batch
            with self.assertRaisesRegex(runtime.PackagingHold,'THIRTY_FIVE'): batch.close(complete=True)
            self.assertTrue(batch.closed);self.assertIsNone(context.scientific_consumer);self.assertIsNone(context.scientific_batch)
            with self.assertRaisesRegex(runtime.PackagingHold,'STAGE'):
                with batch.stage('build'): pass

    def test_worker_effect_denial_and_nonworker_inert(self):
        science._deny_worker_effect('socket.connect', ())
        with tempfile.TemporaryDirectory() as tmp:
            token = science._WORKER_EFFECTS.set(Path(tmp).resolve())
            try:
                for event in ('socket.connect','socket.getaddrinfo','urllib.Request','subprocess.Popen','os.system',
                              'os.fork','os.forkpty','os.posix_spawn','os.exec','os.spawn'):
                    with self.subTest(event=event),self.assertRaises(runtime.PackagingHold):
                        science._deny_worker_effect(event,())
                with self.assertRaises(runtime.PackagingHold):
                    science._deny_worker_effect('open',('/different/file','w',os.O_WRONLY))
            finally:science._WORKER_EFFECTS.reset(token)

    def test_supervision_abort_preserves_cleanup_and_signal_handlers(self):
        previous=signal.getsignal(signal.SIGTERM);events=[]
        with self.assertRaises(runtime.HealthSupervisionHold):
            with runtime.health_supervision_scope():
                try:signal.raise_signal(signal.SIGTERM)
                finally:events.append('actual-normal-finally')
        self.assertEqual(events,['actual-normal-finally'])
        self.assertIs(signal.getsignal(signal.SIGTERM),previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))

    def test_existing_timer_is_not_silently_replaced(self):
        previous=signal.setitimer(signal.ITIMER_REAL,60)
        try:
            with self.assertRaisesRegex(runtime.PackagingHold,'INHERITED'):
                with runtime.health_supervision_scope():pass
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0],0)
        finally:signal.setitimer(signal.ITIMER_REAL,*previous)

    def test_live_function_defaults_and_referenced_global_data(self):
        with tempfile.TemporaryDirectory()as tmp:
            p=Path(tmp).resolve()/'historical.py';p.write_bytes(b'Synthetic pinned source, no original qualifier')
            historical_sha=runtime.sha(p.read_bytes());historical_name='synthetic_historical'
            namespace={'__name__':'synthetic_original','CONST':{'scientific_scope':'bound'}}
            exec(compile('def saved(value=None):\n return CONST\n','synthetic-original-source.py','exec'),namespace)
            fn=namespace['saved'];original=SimpleNamespace(require_registration=fn,
                _HISTORICAL_PRIOR_REGISTRARS={historical_sha:historical_name})
            historical=SimpleNamespace(require_registration=fn,__file__=str(p))
            module=SimpleNamespace(require_registration=fn,_original_registrar=lambda:original)
            lookup=lambda name:module if name=='methods_digest_registration_v3'else historical
            with patch.object(science.importlib,'import_module',side_effect=lookup),\
                 patch.object(science,'HISTORICAL_STATE_ENTRY',(historical_name,historical_sha)):
                before=science.evaluation_state()
                namespace['CONST']['scientific_scope']='changed'
                self.assertNotEqual(before,science.evaluation_state())
                namespace['CONST']['scientific_scope']='bound';self.assertEqual(before,science.evaluation_state())
                fn.__defaults__=('changed default',)
                self.assertNotEqual(before,science.evaluation_state())

    def test_string_selected_historical_entry_defaults_and_transitive_globals_are_bound(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();p=root/'historical.py';p.write_bytes(b'Synthetic public source only')
            historical_sha=runtime.sha(p.read_bytes());historical_name='synthetic_historical'
            original_ns={'__name__':'synthetic_original','HISTORICAL':{historical_sha:historical_name}}
            exec(compile('def saved(value=None):\n return HISTORICAL\n',str(root/'original.py'),'exec'),original_ns)
            historical_ns={'__name__':historical_name,'SCOPE':{'scientific_scope':'bound'}}
            exec(compile('def helper():\n return SCOPE\ndef saved(value=None):\n return helper()\n',str(p),'exec'),historical_ns)
            original=SimpleNamespace(require_registration=original_ns['saved'],
                _HISTORICAL_PRIOR_REGISTRARS=original_ns['HISTORICAL'])
            historical=SimpleNamespace(require_registration=historical_ns['saved'],__file__=str(p))
            module=SimpleNamespace(require_registration=original_ns['saved'],_original_registrar=lambda:original)
            lookups=[]
            def lookup(name):
                lookups.append(name)
                return module if name=='methods_digest_registration_v3'else historical
            with patch.object(science,'ROOT',root),\
                 patch.object(science,'HISTORICAL_STATE_ENTRY',(historical_name,historical_sha)),\
                 patch.object(science.importlib,'import_module',side_effect=lookup):
                before=science.evaluation_state();self.assertEqual(len(before),3)
                # Old two-entry graph misses the locally string-selected module;
                # its dispatch map itself remains unchanged and still bound.
                historical_ns['SCOPE']['scientific_scope']='changed';changed=science.evaluation_state()
                self.assertEqual(before[:2],changed[:2]);self.assertNotEqual(before[2],changed[2])
                historical_ns['SCOPE']['scientific_scope']='bound'
                historical_ns['saved'].__defaults__=('changed default',)
                self.assertNotEqual(before,science.evaluation_state())
                self.assertTrue(all(name in{'methods_digest_registration_v3',historical_name}for name in lookups))
                original._HISTORICAL_PRIOR_REGISTRARS[historical_sha]='arbitrary_receiver_module'
                count=len(lookups)
                with self.assertRaisesRegex(runtime.PackagingHold,'EXACT_HISTORICAL_STATE_DISPATCH'):
                    science.evaluation_state()
                self.assertEqual(lookups[count:],['methods_digest_registration_v3'])

    def test_actual_manual_pipe_drain_before_wait_and_bounded_output(self):
        # Public worker source admission is a separate tested boundary. Here
        # actual harmless children exercise the pipe lifecycle, without any
        # original module, network, canonical path or scientific callback.
        for size, expected_hold in ((60000,False),(70000,True)):
            with self.subTest(size=size),tempfile.TemporaryDirectory() as tmp:
                root, _, _, batch, _ = self.fixture(tmp)
                script = root/'synthetic-child.py'
                script.write_text('import os\nraw=b"x"*'+str(size)+'\nwhile raw:\n n=os.write(1,raw);raw=raw[n:]\n')
                rows = [{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
                batch.source_table = rows
                source = root/'source-manifest.json'; source.write_bytes(science.raw({'synthetic':'source boundary'}))
                bound = {'path':str(root/'synthetic-config.json'),'sha256':'0'*64}
                config = {'source_manifest':science.binding(source),'stage':'build','ordinal':0,'job_nonce':'1'*32}
                consumed=[]
                with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'source boundary'}),patch.object(batch,'_accept',side_effect=lambda state,code:consumed.append((len(state['out']),code,state['child'].poll()))):
                    if expected_hold:
                        with self.assertRaisesRegex(runtime.PackagingHold,'BOUNDED_SCIENCE_PIPE'):
                            batch._execute([(config,bound)])
                        self.assertEqual(consumed,[])
                    else:
                        batch._execute([(config,bound)])
                        self.assertEqual(consumed,[(60000,0,0)])

    def test_actual_abnormal_child_has_no_accepted_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _, batch, _ = self.fixture(tmp)
            script=root/'synthetic-child.py';script.write_text('raise SystemExit(7)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows
            p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(batch,'_accept') as accepted:
                with self.assertRaisesRegex(runtime.PackagingHold,'NORMAL_SCIENTIFIC_WORKER_EXIT'):
                    batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
                accepted.assert_not_called()

    def test_spawn_journal_failure_reaps_actual_child_and_closes_all_pipe_fds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _, _, batch, _=self.fixture(tmp)
            script=root/'synthetic-child.py';script.write_text('import signal,time\nsignal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})\ntime.sleep(30)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            fds=[];children=[];actual_pipe=os.pipe;actual_popen=science.subprocess.Popen;actual_retain=science.retain
            prior_mask=signal.pthread_sigmask(signal.SIG_BLOCK,set())
            def tracked_pipe():
                pair=actual_pipe();fds.extend(pair);return pair
            def tracked_child(*args,**kwargs):
                value=actual_popen(*args,**kwargs);children.append(value);return value
            def fail_started(path,value):
                if str(path).endswith('-STARTED.json'):raise OSError('actual synthetic STARTED retention fault')
                return actual_retain(path,value)
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(science.os,'pipe',side_effect=tracked_pipe),patch.object(science.subprocess,'Popen',side_effect=tracked_child),patch.object(science,'retain',side_effect=fail_started):
                with self.assertRaisesRegex(OSError,'STARTED retention fault'):
                    batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
            # Popen may create its own internal error pipe after our two pairs.
            self.assertGreaterEqual(len(fds),4);self.assertEqual(len(children),1)
            self.assertIsNotNone(children[0].returncode)
            for fd in fds[:4]:
                with self.assertRaises(OSError):os.fstat(fd)
            self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK,set()),prior_mask)
            cleanup=json.loads(next(batch.output.glob('*-CLEANUP.json')).read_bytes())
            self.assertTrue(cleanup['wait_completed']);self.assertFalse(cleanup['source_finally_claimed'])

    def bootstrap_fixture(self, root, *, changed_git=False):
        directory=root/'_ZENODO_DEPOSITS/standalone_pdf_runtime_v012';directory.mkdir(parents=True)
        rows=[];modules=[]
        for name in sorted(science.BOOTSTRAP_MODULE_NAMES):
            p=directory/name;p.write_bytes(b'# synthetic source only\n');s=p.stat()
            identity={'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
            bound=science.binding(p);rows.append({'name':name,**bound,'identity':identity})
            modules.append({'name':name,**bound,'git_path':science.BOOTSTRAP_GIT_PREFIX+name})
        if changed_git:modules[0]['git_path']='unreviewed/other-source.py'
        profile=directory/'CURRENT_PACKAGING_PROFILE.json';profile.write_bytes(science.raw({'modules':modules}))
        nomination=directory/'INSTALLATION_NOMINATION.json';nomination.write_bytes(science.raw({'profile':science.binding(profile)}))
        plan=directory/'INSTALL_PLAN.json';plan.write_bytes(science.raw({'synthetic_only':True}))
        metadata=[]
        for role,p in (('profile',profile),('nomination',nomination),('plan',plan)):
            s=p.stat();metadata.append({'role':role,**science.binding(p),'identity':{'device':s.st_dev,'inode':s.st_ino,'mode':s.st_mode,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}})
        manifest=root/'manifest.json';manifest.write_bytes(science.raw({'standard':'VRS-CURRENT-V012-WORKER-SOURCE-MANIFEST-1','canonical_root':str(root),
            'profile_binding':science.binding(profile),'modules':rows,'metadata':metadata,'source_origin':{'synthetic':True},
            'legacy_closure':{'synthetic':True},'source_review_change_flags':{'synthetic':True}}))
        config=root/'config.json';config.write_bytes(science.raw({'source_manifest':science.binding(manifest)}))
        return directory,config

    def test_cleanup_journal_failure_still_reaps_all_children_and_closes_selector(self):
        with tempfile.TemporaryDirectory()as tmp:
            root, _, _, batch, _=self.fixture(tmp)
            script=root/'synthetic-child.py';script.write_text('import signal,time\nsignal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})\ntime.sleep(30)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            children=[];pairs=[];selectors=[];started=[];cleanup=[]
            actual_pipe=os.pipe;actual_child=science.subprocess.Popen;actual_retain=science.retain;actual_selector=science.selectors.DefaultSelector
            def pipe():
                value=actual_pipe();pairs.append(value);return value
            def child(*args,**kwargs):
                value=actual_child(*args,**kwargs);children.append((value,kwargs['stdout'],kwargs['stderr']));return value
            def selector():
                value=actual_selector();selectors.append(value);return value
            def retained(path,value):
                if str(path).endswith('-STARTED.json'):
                    started.append(path)
                    if len(started)==2:raise OSError('synthetic second STARTED fault')
                if str(path).endswith('-CLEANUP.json'):
                    cleanup.append(path)
                    if len(cleanup)==1:raise OSError('synthetic first CLEANUP fault')
                return actual_retain(path,value)
            planned=[({'source_manifest':science.binding(p),'stage':'build','ordinal':i,'job_nonce':str(i+1)*32},
                      {'path':str(root/('synthetic-config-'+str(i))),'sha256':'0'*64})for i in range(2)]
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(science.os,'pipe',side_effect=pipe),patch.object(science.subprocess,'Popen',side_effect=child),patch.object(science.selectors,'DefaultSelector',side_effect=selector),patch.object(science,'retain',side_effect=retained):
                with self.assertRaisesRegex(OSError,'second STARTED fault')as caught:batch._execute(planned)
            self.assertTrue(any('cleanup DATA HOLD' in note for note in getattr(caught.exception,'__notes__',[])))
            self.assertEqual(len(children),2);self.assertEqual(len(cleanup),2)
            for process,out,err in children:
                self.assertIsNotNone(process.returncode)
                for pair in pairs:
                    if pair[1]in(out,err):
                        for fd in pair:
                            with self.assertRaises(OSError):os.fstat(fd)
            self.assertIsNone(selectors[0].get_map())
            self.assertTrue(json.loads(cleanup[1].read_bytes())['wait_completed'])

    def test_post_spawn_state_failure_reaps_child_before_endpoint_close(self):
        with tempfile.TemporaryDirectory()as tmp:
            root, _, _, batch, _=self.fixture(tmp)
            script=root/'synthetic-child.py';script.write_text('import signal,time\nsignal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})\ntime.sleep(30)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            actual_child=science.subprocess.Popen;actual_clock=science.time.monotonic;children=[];fail=[False]
            def child(*args,**kwargs):
                value=actual_child(*args,**kwargs);children.append(value);fail[0]=True;return value
            def clock():
                if fail[0]:fail[0]=False;raise OSError('synthetic post-spawn state fault')
                return actual_clock()
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(science.subprocess,'Popen',side_effect=child),patch.object(science.time,'monotonic',side_effect=clock):
                with self.assertRaisesRegex(OSError,'post-spawn state fault'):batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
            self.assertEqual(len(children),1);self.assertIsNotNone(children[0].returncode)

    def test_accept_requires_closed_actual_manifest_entry_and_exit_source_proofs(self):
        import owner_content_worker as transport
        for change in ('none','extra','missing','manifest_hash','population','certifies','restore','entry'):
            with self.subTest(change=change),tempfile.TemporaryDirectory()as tmp:
                root, _, _, batch, _=self.fixture(tmp)
                now=dt.datetime.now(dt.timezone.utc).isoformat();mono=science.time.monotonic()
                source=root/'source.json';source_value={'synthetic':'complete bound source DATA'};source.write_bytes(science.raw(source_value))
                proof={'status':'ACTUAL_CURRENT_WORKER_SOURCE_AUTHORITY_AND_IDENTITY_VERIFIED',
                    'source_manifest_sha256':runtime.sha(transport.encode_json(source_value)), 'source_modules':19,'metadata_files':3,
                    'transient_restore_allowed':False,'scientific_population_admitted':False,'certifies':False}
                config={key:None for key in('operation','stage','ordinal','binding','profile','source_rows','environment','ledger','ledger_sha256','evaluation_state')}
                config.update(operation=batch.operation,job_nonce='1'*32,stage='build',binding={'path':'registration','sha256':'1'*64},
                    evaluation_kwargs={'views':None,'prior_chain_receipts':None},source_manifest=science.binding(source),started_utc=now,started_monotonic=mono)
                manifest=root/'input.json';manifest.write_bytes(science.raw({'status':'COMPLETE_REHASHED_OPERATION_INPUT_DATA','authorized_canonical_cas':[],'inventory':{},'inputs':[]}))
                result={key:None for key in science.RESULT_FIELDS};result.update(config)
                config_bound={'path':str(root/'synthetic-config'),'sha256':'0'*64}
                result.update(standard=science.RESULT_STANDARD,config=config_bound,outcome='SCIENCE_RESULT',original_result={'synthetic':'actual returned DATA'},
                    original_hold=None,source_finally_completed=True,network_requests=0,ssot_writes=0,zenodo_writes=0,certifies=False,
                    completed_utc=now,completed_monotonic=mono,source_entry=deepcopy(proof),source_exit=deepcopy(proof),
                    final_input_manifest=science.binding(manifest),input_manifest=science.binding(manifest))
                if change=='extra':result['source_exit']['invented']='authority'
                elif change=='missing':del result['source_exit']['certifies']
                elif change=='manifest_hash':result['source_exit']['source_manifest_sha256']='0'*64
                elif change=='population':result['source_exit']['scientific_population_admitted']=True
                elif change=='certifies':result['source_exit']['certifies']=True
                elif change=='restore':result['source_exit']['transient_restore_allowed']=True
                if change not in('none','entry'):result['source_entry']=deepcopy(result['source_exit'])
                if change=='entry':result['source_entry']['scientific_population_admitted']=True
                p=root/'result.json';p.write_bytes(science.raw(result))
                frame=science.raw({'result':science.binding(p),'pid':12345,'job_nonce':config['job_nonce']})
                state={'out':struct.pack('!I',len(frame))+frame,'config':config,'binding':config_bound,'child':SimpleNamespace(pid=12345)}
                if change=='none':batch._accept(state,0);self.assertEqual(len(batch.jobs),1)
                else:
                    with self.assertRaises(ValueError):batch._accept(state,0)
                    self.assertEqual(batch.jobs,{})

    def test_realistic_four_key_profile_bootstrap_and_git_relation(self):
        for bad in (False,True):
            with self.subTest(changed_git=bad),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve();directory,config=self.bootstrap_fixture(root,changed_git=bad)
                argv=['synthetic-worker','--config',str(config),'--expected-config-sha256',science.binding(config)['sha256']]
                with patch.object(science,'BOOTSTRAP_ROOT',root),patch.object(science,'__file__',str(directory/'scientific_registration_worker.py')),patch.object(sys,'argv',argv):
                    if bad:
                        with self.assertRaisesRegex(ValueError,'FOUR_KEY_PROFILE'):science._bootstrap()
                    else:science._bootstrap()

    def test_current_import_artifacts_including_dangling_shadow_hold(self):
        import packaging_nightly as nightly
        with tempfile.TemporaryDirectory()as tmp:
            directory=Path(tmp).resolve()
            with patch.object(sys,'pycache_prefix',None),patch.object(nightly,'__file__',str(directory/'packaging_nightly.py')):
                science._bootstrap_artifacts(directory);nightly._current_namespace_artifacts()
            with patch.object(sys,'pycache_prefix',str(directory/'external-cache')),patch.object(nightly,'__file__',str(directory/'packaging_nightly.py')):
                with self.assertRaisesRegex(ValueError,'EXTERNAL_CACHE_PREFIX'):science._bootstrap_artifacts(directory)
                with self.assertRaisesRegex(ValueError,'EXTERNAL_CACHE_PREFIX'):nightly._current_namespace_artifacts()
            self.assertFalse((directory/'external-cache').exists())
        for artifact in ('__pycache__','packaging_runtime','packaging_runtime.pyc','packaging_runtime.pyo',
                         'packaging_runtime'+science.importlib.machinery.EXTENSION_SUFFIXES[0]):
            with self.subTest(artifact=artifact),tempfile.TemporaryDirectory() as tmp:
                directory=Path(tmp).resolve();science._bootstrap_artifacts(directory)
                (directory/artifact).symlink_to(directory/'nonexistent-shadow')
                with self.assertRaisesRegex(ValueError,'IMPORT_ARTIFACT'):science._bootstrap_artifacts(directory)

    def test_signal_pending_at_spawn_return_is_owned_reaped_and_mask_restored(self):
        with tempfile.TemporaryDirectory()as tmp:
            root, _, _, batch, _=self.fixture(tmp)
            script=root/'synthetic-child.py';script.write_text('import signal,time\nsignal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})\ntime.sleep(30)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            children=[];actual=science.subprocess.Popen;prior=signal.pthread_sigmask(signal.SIG_BLOCK,set())
            def pending(*args,**kwargs):
                child=actual(*args,**kwargs);children.append(child)
                signal.raise_signal(signal.SIGTERM)
                return child
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(science.subprocess,'Popen',side_effect=pending):
                with self.assertRaises(runtime.HealthSupervisionHold):
                    with runtime.health_supervision_scope():batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
            self.assertEqual(len(children),1);self.assertIsNotNone(children[0].returncode)
            self.assertEqual(signal.pthread_sigmask(signal.SIG_BLOCK,set()),prior)
            self.assertEqual(len(list(batch.output.glob('*-CLEANUP.json'))),1)

    def test_failed_worker_exact_streams_are_retained_before_unchanged_gate(self):
        for code in (0,7):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as tmp:
                root,_,_,batch,_=self.fixture(tmp)
                script=root/'synthetic-error-child.py'
                script.write_text('import os\nos.write(1,b"\\xffactual stdout")\nos.write(2,b"precise worker failure\\n")\nraise SystemExit('+str(code)+')\n')
                rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
                batch.source_table=rows;manifest=root/'source.json';manifest.write_bytes(science.raw({'synthetic':'boundary'}))
                config={'source_manifest':science.binding(manifest),'stage':'build','ordinal':0,'job_nonce':'1'*32}
                cfg={'path':str(root/'synthetic-config'),'sha256':'0'*64}
                with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(batch,'_accept')as accept:
                    with self.assertRaisesRegex(runtime.PackagingHold,'NORMAL_SCIENTIFIC_WORKER_EXIT'):batch._execute([(config,cfg)])
                    accept.assert_not_called()
                captures=[json.loads(p.read_bytes()) for p in batch.output.glob('*-CAPTURE.json')]
                initial=next(v for v in captures if v['phase']=='NORMAL_WAIT_BEFORE_RESULT_GATE')
                self.assertEqual(Path(initial['stdout']['path']).read_bytes(),b'\xffactual stdout')
                self.assertEqual(Path(initial['stderr']['path']).read_bytes(),b'precise worker failure\n')
                self.assertEqual(initial['config'],cfg);self.assertEqual(initial['job_nonce'],config['job_nonce'])
                self.assertEqual(initial['actual_child_exit_code'],code);self.assertTrue(initial['wait_completed'])
                self.assertTrue(initial['stdout_eof_observed'] and initial['stderr_eof_observed'])
                self.assertFalse(initial['source_finally_claimed']);self.assertFalse(initial['result_accepted'])
                terminal=json.loads(Path(initial['terminal']['path']).read_bytes())
                self.assertEqual(terminal['actual_pid'],initial['actual_pid'])
                for name in ('stdout','stderr'):
                    path=Path(initial[name]['path']);self.assertEqual(path.stat().st_mode&0o777,0o600)
                    self.assertEqual(runtime.sha(path.read_bytes()),initial[name]['sha256'])

    def test_first_worker_failure_retains_sibling_output_and_normal_reaping(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_,batch,_=self.fixture(tmp);script=root/'synthetic-sibling-child.py'
            script.write_text('import os,signal,sys,time\nsignal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGTERM,signal.SIGALRM})\nname=sys.argv[sys.argv.index("--config")+1]\nif name.endswith("-0"):\n time.sleep(.15);os.write(2,b"first actual failure");raise SystemExit(6)\nos.write(1,b"sibling stdout");os.write(2,b"sibling stderr");time.sleep(30)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            planned=[({'source_manifest':science.binding(p),'stage':'build','ordinal':i,'job_nonce':str(i+1)*32},
                      {'path':str(root/('synthetic-config-'+str(i))),'sha256':'0'*64})for i in range(2)]
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(batch,'_accept')as accept:
                with self.assertRaisesRegex(runtime.PackagingHold,'NORMAL_SCIENTIFIC_WORKER_EXIT'):batch._execute(planned)
                accept.assert_not_called()
            captures=[json.loads(p.read_bytes())for p in batch.output.glob('*-CAPTURE.json')]
            sibling=next(v for v in captures if v['ordinal']==1 and v['phase']=='ABORT_CLEANUP_AFTER_ACTUAL_WAIT')
            self.assertEqual(Path(sibling['stdout']['path']).read_bytes(),b'sibling stdout')
            self.assertEqual(Path(sibling['stderr']['path']).read_bytes(),b'sibling stderr')
            self.assertTrue(sibling['wait_completed'])
            self.assertTrue(sibling['stdout_eof_observed']and sibling['stderr_eof_observed'])
            self.assertIsInstance(sibling['actual_child_exit_code'],int)
            self.assertNotEqual(sibling['actual_child_exit_code'],0)
            self.assertFalse(sibling['source_finally_claimed']);self.assertFalse(sibling['result_accepted'])
            self.assertEqual(len(list(batch.output.glob('*-CLEANUP.json'))),2)

    def test_raw_stream_credential_refusal_preserves_primary_exit_and_cleanup(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_,batch,_=self.fixture(tmp);script=root/'synthetic-credential-child.py'
            script.write_text('import os\nos.write(2,b"Bearer private-fixture-secret")\nraise SystemExit(9)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(batch,'_accept')as accept:
                with self.assertRaisesRegex(runtime.PackagingHold,'NORMAL_SCIENTIFIC_WORKER_EXIT')as caught:
                    batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
                accept.assert_not_called()
            self.assertTrue(any('retention unavailable' in n for n in caught.exception.__notes__))
            self.assertEqual(list(batch.output.glob('*-err.bin')),[])
            cleanup=json.loads(next(batch.output.glob('*-CLEANUP.json')).read_bytes())
            self.assertTrue(cleanup['wait_completed']);self.assertEqual(cleanup['actual_child_exit_code'],9)
            self.assertFalse(cleanup['source_finally_claimed'])
            self.assertTrue((batch.output/'BATCH_CLEANUP_HOLD.json').is_file())

    def test_output_retention_fault_cannot_skip_actual_reap_or_fd_close(self):
        with tempfile.TemporaryDirectory()as tmp:
            root,_,_,batch,_=self.fixture(tmp);script=root/'synthetic-child.py'
            script.write_text('import os\nos.write(2,b"failure-data")\nraise SystemExit(4)\n')
            rows=[{'name':'scientific_registration_worker.py','path':str(script),'sha256':runtime.sha(script.read_bytes())}]
            batch.source_table=rows;p=root/'source.json';p.write_bytes(science.raw({'synthetic':'boundary'}))
            config={'source_manifest':science.binding(p),'stage':'build','ordinal':0,'job_nonce':'1'*32}
            actual_pipe=os.pipe;actual_child=science.subprocess.Popen;actual_raw=science.retain_raw;pairs=[];children=[]
            def pipe():
                pair=actual_pipe();pairs.append(pair);return pair
            def child(*a,**kw):
                value=actual_child(*a,**kw);children.append(value);return value
            def fault(path,data):
                if str(path).endswith('-err.bin'):raise OSError('synthetic raw retention fault')
                return actual_raw(path,data)
            with patch.object(science,'source_rows',return_value=rows),patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic':'boundary'}),patch.object(science.os,'pipe',side_effect=pipe),patch.object(science.subprocess,'Popen',side_effect=child),patch.object(science,'retain_raw',side_effect=fault):
                with self.assertRaisesRegex(runtime.PackagingHold,'NORMAL_SCIENTIFIC_WORKER_EXIT')as caught:
                    batch._execute([(config,{'path':str(root/'synthetic-config'),'sha256':'0'*64})])
            self.assertEqual(len(children),1);self.assertEqual(children[0].returncode,4)
            for pair in pairs[:2]:
                for fd in pair:
                    with self.assertRaises(OSError):os.fstat(fd)
            self.assertTrue(any('cleanup DATA HOLD' in n for n in caught.exception.__notes__))
            record=json.loads((batch.output/'BATCH_CLEANUP_HOLD.json').read_bytes())
            self.assertEqual(record['primary_error_type'],'PackagingHold')
            self.assertTrue(any(e['phase']=='retain_output'for e in record['cleanup_errors']))

    def test_trusted_worker_exception_phase_does_not_replace_original_error(self):
        with tempfile.TemporaryDirectory()as tmp:
            output=Path(tmp).resolve()/'trusted-output';output.mkdir()
            primary=runtime.PackagingHold('synthetic exact state mismatch')
            def body(path,expected,state):
                state.update(output=output,config={'operation':'2'*32,'job_nonce':'1'*32,'stage':'build','ordinal':0},phase='COMPARE_EVALUATION_STATE_BEFORE')
                raise primary
            with patch.object(science,'_worker_body',side_effect=body):
                with self.assertRaises(runtime.PackagingHold)as caught:science.worker(output.parent/'fixed-config','0'*64)
            self.assertIs(caught.exception,primary)
            value=json.loads((output/'WORKER_EXCEPTION.json').read_bytes())
            self.assertEqual(value['last_entered_phase'],'COMPARE_EVALUATION_STATE_BEFORE')
            self.assertFalse(value['original_call_started']);self.assertFalse(value['source_finally_claimed'])
            self.assertIn(b'synthetic exact state mismatch',Path(value['traceback']['path']).read_bytes())
            self.assertEqual(value['exception_class']['name'],'PackagingHold')
        with tempfile.TemporaryDirectory()as tmp:
            primary=OSError('before trusted output')
            with patch.object(science,'_worker_body',side_effect=primary),patch.object(science,'retain_worker_exception')as retained:
                with self.assertRaises(OSError)as caught:science.worker(Path(tmp)/'untrusted-config','0'*64)
            self.assertIs(caught.exception,primary);retained.assert_not_called()

    def test_fresh_environment_clock_and_manifest_no_false_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, data, batch, rows=self.fixture(tmp)
            with patch.object(catalog,'scientific_data',return_value=data),patch.object(science,'source_rows',return_value=rows),patch.dict(os.environ,{'TZ':'CHANGED-ACTUAL-ENVIRONMENT'}):
                with self.assertRaisesRegex(runtime.PackagingHold,'ENVIRONMENT_RACE'):batch._fresh_union()
            bound,value=self.slot(batch)
            value['completed_utc']='2999-01-01T00:00:00+00:00'
            slot=next(iter(batch.jobs.values()));p=Path(slot['binding']['path']);p.write_bytes(science.raw(value));slot['binding']=science.binding(p)
            with patch.object(batch,'_fresh_union'),batch.stage('build'):
                with self.assertRaisesRegex(runtime.PackagingHold,'CONSUMPTION_CLOCK'):batch.require(bound,views=None)
            self.assertEqual(batch.used,set())


if __name__ == '__main__': unittest.main()
