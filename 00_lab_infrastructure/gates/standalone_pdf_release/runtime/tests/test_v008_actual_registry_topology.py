"""Actual metadata topology plus synthetic scheduling and master-consumer checks.

The embedded bytes are the exact sealed registry94832 metadata, not science,
OWNER evidence or credentials. No actual bound path is opened by these tests.
All scientific/public/admission/worker-process functions are synthetic seams.
The seven actual archive-access nominations must retain their chains in the
master while each distinct saved-science worker receives None kwargs.
"""
import ast
import base64
import contextlib
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE.parent))
sys.path.insert(0,str(HERE))
from common.runtime_history import historical_bytes
import packaging_runtime as runtime
import packaging_catalog as catalog
import manuscript_access_registry as registry
import scientific_registration_worker as science

ACTUAL_REGISTRY_SHA='94832b9e15609cfdcdbf9dae0e9ae06745d438482e377f0dbb2c6f808e2d9afa'
ACTUAL_REGISTRY_BYTES=zlib.decompress(base64.b64decode(
    'eJzlnN1vWze2xd/7Vxh+vVW0SW5+zVsm8e3NQ+MidmYw9+JC2CQ3E01dyZBkdzqD/u+zKLtJ29jxJ2ZiDQwIkA91LC1trv1bPDz+'
    'x1d7e/u62Kzmut7/w97/4ene3j+2jzggtep6PavL1UrrZr5cYMgvB3H4VDbv8Zv96du1rtbTv56tN/PFe1ltpi91/f1meTp9sfxx'
    'ufp+b/qn+Wre5uu9F8uV7rVlXe/ZZzSd/e/B68OXh7OXB98dHr06Ppq2+Ttdb2anrc/O7Wyl53P9cdrPNmcrna3OFpv5Dzo7JzJT'
    'qZszOcGId/P1ZvXTrMqizZtsLg9bZ22IwUyfv3hxcHQ0e3H43V9mr15/9/b42V/X+BRff/wM6/difRiforCJ7MWprcVTSI1DaJZt'
    'UkeVo6fiMksJufkkRkomH33OztZgvAt9//KkP3/9Qb5VfT8/18cVbaWny9VmPT3X1bzPq4yvZVKXeCrvdGrJhomhCcXp6XtZa5w0'
    'rcuz0xNtE/2b1rPt8K1Ifb5abyY/6Ob9sq0nF9JPTpfrzelZOZmv30/qyXKty7PNGG6nbfnj4mQpbT3dHq9TIj/99uD4fw5fHs1e'
    'Hx4fHD37+/z0amm5k/SePN5dcVZdsQRpCb8VZ1LPPYmSUdag4nK3vtbAMVe1zXkT06fSnq7my9Wsvpf572qy4EOfzBc6O9F3Un/6'
    'zcF/mfqGpuvTk/lmUqR+f7J8hy/hBIWw+ulC+Q9fxPriFX9mUy6OyGajP5xuJjQU36xksR5/DlK72TcHnxTvbzQOmbPXUJq6EARn'
    'ZNNC1NSKULSSPGXVShHlTbFanDJbMZqoOfWN6/6H0/789RVyLvBRf1fKT1hOvlFOzlKb6YF7QjFa040LZIzznJ0nX0pqHnK27GIv'
    'dRSu7yxNjPE5JqNXy1lXKp/46L/OFNLlpL+c7HLW5hsYA8bLkPUXebfavdMFTlYnmPbaOE9OT2Txid6r5XIzGac3ROni6G+rFsb+'
    'eZ2hW0h5TPXOxZeK+Q7vTjGIVltyra4Sa9SiXJLFi4rv0SQlFRgJt6t1vrSwp1uuv9Ex+lvoqEmSjcaboDZYwQSXQib3VmpobLn0'
    'KMVD7dqj95KLbdamGEOSyomu1nG9wQcbp//jwX8fvjmYXfTTT+0YeLBctdm8jbG/dN/9Xx3e9ulPS//JdsNfGt/LV98cHB3P3hx8'
    '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'))

IDS=('23226761','23246368','23290448','23290748','23291581','23292552','23308138')

def actual_entries():
    return deepcopy(json.loads(ACTUAL_REGISTRY_BYTES)['entries'])


class ActualRegistryTopology(unittest.TestCase):
    def fixture(self, root, entries=None):
        entries=actual_entries() if entries is None else deepcopy(entries)
        output=root/'synthetic-owner';output.mkdir()
        ctx=registry.RegistryContext.__new__(registry.RegistryContext)
        ctx.root=root;ctx.deadline_guard=None;ctx.scientific_consumer=None;ctx.scientific_batch=None
        ctx._registry=lambda:({'entries':deepcopy(entries)},ACTUAL_REGISTRY_BYTES)
        previous={'tree_root':str(root),'publication_entities':[{'entity_type':'METHODS_DIGEST_GROUP',
            'registration_receipt':deepcopy(e['registration'])}for e in actual_entries()]}
        baseline={'tree_root':str(root),'file_entities':[],'run_entities':[],
            'publication_entities':[],'opaque_nonpublication':{'ordered':['b','a']}}
        data=SimpleNamespace(scan_data=deepcopy(baseline),cas_events=[],pending_cas=None)
        rows=[{'name':name,'path':str(root/name),'sha256':'b'*64}for name in sorted(runtime.MODULE_NAMES)]
        with patch.object(science,'source_rows',return_value=rows):
            batch=science.ScienceBatch(root,{'path':str(root/'profile.json'),'sha256':'c'*64},
                                      ctx,previous,baseline,output)
        observed=[]
        def execute(planned):
            for cfg,bound in planned:
                observed.append((deepcopy(cfg),deepcopy(bound)))
                batch.jobs[batch._key(cfg['stage'],cfg['binding'])]={'config':deepcopy(cfg)}
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(catalog,'scientific_data',return_value=data))
        stack.enter_context(patch.object(runtime,'build_worker_source_manifest',return_value={'synthetic_source_only':True}))
        stack.enter_context(patch.object(science,'evaluation_state',return_value={'synthetic_only':True}))
        stack.enter_context(patch.object(batch,'_execute',side_effect=execute))
        barrier=stack.enter_context(patch.object(batch,'_fresh_union'))
        return stack,batch,ctx,observed,barrier

    def test_exact_sealed_registry_has_six_before_access_and_one_without_chain(self):
        self.assertEqual(hashlib.sha256(ACTUAL_REGISTRY_BYTES).hexdigest(),ACTUAL_REGISTRY_SHA)
        entries=actual_entries();self.assertEqual(tuple(e['record_id']for e in entries),IDS)
        self.assertEqual(sum(e['prior_chain']is None for e in entries),1)
        self.assertEqual(entries[-1]['prior_chain'],None)
        for e in entries:
            self.assertEqual(set(e),registry.ENTRY_FIELDS)
            self.assertIsNotNone(e['archive'])
            for key in ('registration','archive','access_correction','user_authority'):
                self.assertEqual(set(e[key]),{'path','sha256'})
            if e['prior_chain']is not None:
                self.assertEqual(set(e['prior_chain']),registry.CHAIN_FIELDS|{'stage'})
                self.assertEqual(e['prior_chain']['stage'],'BEFORE_ACCESS')
                for key in registry.CHAIN_FIELDS:
                    self.assertEqual(set(e['prior_chain'][key]),{'path','sha256'})

    def test_actual_topology_prepares_35_distinct_saved_calls_without_chain_or_owner_skip(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,batch,ctx,observed,barrier=self.fixture(root)
            original=actual_entries()
            with stack:batch.prepare()
            self.assertEqual(len(observed),35);self.assertEqual(len(batch.jobs),35)
            self.assertEqual(len({cfg['job_nonce']for cfg,_ in observed}),35)
            self.assertEqual(ctx._registry()[0]['entries'],original)
            for stage in science.STAGES:
                configs=[cfg for cfg,_ in observed if cfg['stage']==stage]
                self.assertEqual([c['binding']for c in configs],[e['registration']for e in original])
                self.assertEqual([c['ordinal']for c in configs],list(range(7)))
                for cfg in configs:
                    self.assertEqual(cfg['evaluation_kwargs'],{'views':None,'prior_chain_receipts':None})
                    if stage.startswith('labels_'):
                        self.assertIsNone(cfg['ledger']);self.assertIsNone(cfg['ledger_sha256'])
                    else:self.assertIsNotNone(cfg['ledger'])
            barrier.assert_called_once();self.assertIsNotNone(ctx.scientific_consumer)
            batch.close();self.assertIsNone(ctx.scientific_consumer);self.assertIsNone(ctx.scientific_batch)

    def test_non_access_or_non_before_chain_holds_before_any_plan_or_process(self):
        mutations=[lambda es:es[0].update(archive=None),
            lambda es:es[0]['prior_chain'].update(stage='AFTER_ACCESS'),
            lambda es:es[0]['prior_chain'].update(stage='UNKNOWN'),
            lambda es:es[0]['prior_chain'].update(unreviewed=True),
            lambda es:es[0]['prior_chain'].pop('creation'),
            lambda es:es[0].update(prior_chain=[]),
            lambda es:es.pop()]
        for mutate in mutations:
            with self.subTest(mutate=mutate),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();entries=actual_entries();mutate(entries)
                stack,batch,ctx,observed,_=self.fixture(root,entries)
                with stack,self.assertRaisesRegex(runtime.PackagingHold,'EXACT_SEVEN_ACCESS_SAVED_REGISTRATION_BATCH'):
                    batch.prepare()
                self.assertFalse(batch.output.exists());self.assertEqual(observed,[])
                self.assertIsNone(ctx.scientific_consumer);self.assertFalse(batch.prepared)

    def test_missing_original_group_is_not_normalized_or_filtered_to_pass(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,batch,ctx,observed,_=self.fixture(root)
            batch.previous['publication_entities'].pop()
            with stack,self.assertRaisesRegex(runtime.PackagingHold,'COMPLETE_SEVEN_GROUP_BINDINGS'):
                batch.prepare()
            self.assertEqual(observed,[]);self.assertFalse(batch.output.exists())

    def master_fixture(self, root, original):
        # Build only synthetic local DATA; actual production bindings are never
        # read. The seven original nomination structures are copied, while the
        # _object/bound reader seams return fresh deterministic fixture bytes.
        entry=deepcopy(original);rid=entry['record_id'];values={};events=[]
        manifest_bound={'path':str(root/'manifest.json'),'sha256':'d'*64}
        entry['registration']={'path':str(root/'registration.json'),'sha256':'a'*64}
        entry['access_correction']={'path':str(root/'correction.json'),'sha256':'b'*64}
        entry['user_authority']={'path':str(root/'authority.json'),'sha256':'c'*64}
        entry['archive']={'path':str(root/'METHODS_NOTES.zip'),'sha256':'e'*64}
        reg_bound={'path':str(root/'registry.json'),'sha256':'f'*64}
        correction={'record_id':rid,'authority':deepcopy(entry['user_authority'])}
        manifest={'uploads':[{'filename':'METHODS_NOTES.zip','sha256':entry['archive']['sha256']}]}
        admitted={'receipt':{'record_id':rid,'digest_manifest':manifest_bound},'manifest':manifest,
            'public_legacy':{'id':rid,'phase':'original-saved'},
            'public_native':{'id':rid,'phase':'original-saved'}}
        legacy={'id':rid,'phase':'current-owner'}
        native={'id':rid,'phase':'current-owner','parent':{'access':{'owned_by':{'user':registry.CONTEXT['owner_id']}}}}
        before=({'id':rid,'phase':'genuine-before-access-legacy'},
                {'id':rid,'phase':'genuine-before-access-native'})
        objects={'baseline_legacy':{'response':before[0]},'baseline_native':{'response':before[1]}}
        for b,obj in ((reg_bound,{'entries':[entry]}),(entry['registration'],{'record_id':rid}),
                      (entry['access_correction'],correction),(manifest_bound,manifest)):
            values[science.raw(b)]=(deepcopy(obj),science.raw(obj))
        values[science.raw(entry['archive'])]=(None,b'exact synthetic original archive body')
        ctx=registry.RegistryContext.__new__(registry.RegistryContext)
        ctx.root=root;ctx.binding=reg_bound;ctx.deadline_guard=None;ctx.observation_context=deepcopy(registry.CONTEXT)
        ctx._registry=lambda:({'entries':[deepcopy(entry)]},values[science.raw(reg_bound)][1])
        def saved(binding,ledger,**kw):
            events.append(('saved',deepcopy(binding),deepcopy(ledger),deepcopy(kw)))
            return deepcopy(admitted)
        ctx._scientific_registration=saved
        def getter(record,accept):
            events.append(('owner',record,accept));return deepcopy(legacy if accept==registry.CONTEXT['legacy_accept']else native)
        ctx.owner_getter=getter;ctx.download=lambda *args:(_ for _ in()).throw(AssertionError('real download forbidden'))
        def chain_inputs(chain,record):
            events.append(('chain-inputs',deepcopy(chain),record));return deepcopy(objects),[]
        def chain_pair(first,second,observation,chain):
            events.append(('chain-pair',deepcopy(first),deepcopy(second),deepcopy(chain)))
            return {'fixture_only':True,'certifies':False}
        ctx._chain_inputs=chain_inputs;ctx._chain_pair=chain_pair
        def authority(binding,value):
            events.append(('authority',deepcopy(binding)));self.assertEqual(binding,entry['user_authority']);return {'fixture_only':True}
        ctx._authority=authority
        calls=[]
        def access_pair(actual_legacy,actual_native,saved_legacy,saved_native,**kw):
            events.append(('access',));calls.append((deepcopy((actual_legacy,actual_native)),deepcopy((saved_legacy,saved_native)),kw))
            kw['authority_consumer'](entry['user_authority'])
            return {'fixture_only':True,'certifies':False}
        stack=contextlib.ExitStack()
        stack.enter_context(patch.object(registry,'_object',side_effect=lambda r,b:deepcopy(values[science.raw(b)])))
        stack.enter_context(patch.object(registry,'bound',side_effect=lambda r,b:values[science.raw(b)][1]))
        stack.enter_context(patch.object(registry.access,'require_pair',side_effect=access_pair))
        projection=lambda value:deepcopy(value)
        stack.enter_context(patch.dict(sys.modules,{'own_record_comparison':SimpleNamespace(prior_protected_projection=projection)}))
        return stack,ctx,entry,events,calls,admitted,(legacy,native),before,manifest_bound

    def test_master_keeps_original_saved_science_then_exact_chain_and_access_body_paths(self):
        for original in actual_entries():
            with self.subTest(record=original['record_id']),tempfile.TemporaryDirectory()as tmp:
                root=Path(tmp).resolve();stack,ctx,entry,events,calls,admitted,actual,before,manifest_bound=self.master_fixture(root,original)
                ledger={'tree_root':str(root),'run_entities':[{'id':'Run-001','status':'CERTIFIED'}]}
                with stack:result=ctx.require_registration(root,entry['registration'],ledger)
                self.assertEqual(events[0],('saved',entry['registration'],ledger,{'views':None}))
                self.assertEqual([e[0]for e in events].count('owner'),2)
                self.assertEqual(calls[0][0],actual)
                self.assertEqual(calls[0][1],before if original['prior_chain']is not None else
                    (admitted['public_legacy'],admitted['public_native']))
                kwargs=calls[0][2]
                self.assertEqual(kwargs['manifest_bytes'],science.raw(admitted['manifest']))
                self.assertEqual(kwargs['archive_bytes'],b'exact synthetic original archive body')
                self.assertIs(kwargs['download'],ctx.download)
                self.assertEqual(result['public_legacy'],actual[0]);self.assertEqual(result['public_native'],actual[1])
                chain_calls=[e for e in events if e[0]=='chain-pair']
                if original['prior_chain']is not None:
                    self.assertEqual(len(chain_calls),1)
                    self.assertEqual(chain_calls[0][1:3],(before,(admitted['public_legacy'],admitted['public_native'])))
                    self.assertEqual(chain_calls[0][3],original['prior_chain'])
                else:self.assertEqual(chain_calls,[])
                self.assertEqual(entry['prior_chain'],original['prior_chain'])
                self.assertEqual(len(result['prior_processing_audit']['genuine_chain_audits']),len(chain_calls))

    def test_master_original_chain_failure_prevents_access_admission(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=Path(tmp).resolve();stack,ctx,entry,events,calls,*_=self.master_fixture(root,actual_entries()[0])
            def reject(*args):raise registry.registration.RegistrationHold('synthetic exact chain HOLD')
            ctx._chain_pair=reject
            with stack,self.assertRaisesRegex(registry.registration.RegistrationHold,'synthetic exact chain HOLD'):
                ctx.require_registration(root,entry['registration'],{})
            self.assertEqual(calls,[])

    def test_master_consumer_and_chain_body_remain_literal_frozen_v7(self):
        old=historical_bytes('v007', 'manuscript_access_registry.py');self.assertEqual(hashlib.sha256(old).hexdigest(),
            '167d82b849a750edf2b0cfa92188931c9170db1a59c50eff4ba88ba48a5af2b8')
        new=(HERE/'manuscript_access_registry.py').read_bytes()
        def methods(raw):
            cls=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef)and n.name=='RegistryContext')
            return {n.name:ast.get_source_segment(raw.decode(),n)for n in cls.body if isinstance(n,ast.FunctionDef)}
        before=methods(old);after=methods(new)
        for name in ('require_registration','_chain_inputs','_chain_pair','_authority'):
            self.assertEqual(before[name],after[name],name)


if __name__=='__main__':unittest.main()
