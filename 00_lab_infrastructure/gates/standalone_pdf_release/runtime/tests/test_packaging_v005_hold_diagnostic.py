"""Genuine comparator HOLD retention; strict DATA holder and generic boundaries.

No production scanner, published metadata or network is consumed in these tests.
The integration fixture retains the unchanged comparator arguments and actual
copy/CAS routes; this file tests only the additive diagnostic/byte boundaries.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(1,str(HERE/'tests'))
import packaging_catalog as catalog
import packaging_runtime as runtime
import test_packaging_default_routes as fixtures


class GenuineHoldDiagnosticTests(unittest.TestCase):
    def context(self,root):
        out=root/'reports/verification-coverage/exact-owner';out.mkdir(parents=True)
        context=SimpleNamespace(owner_evidence_directory=out,
            credential_safe_diagnostic=lambda raw:runtime.need(b'fixture-only-secret'not in raw,'KNOWN_TOKEN_DIAGNOSTIC'),
            observation_timing=lambda:{'clock_start':'FIRST_ACTUAL_GET','limit_seconds':900,
                'observation_elapsed_seconds':901,'owner_api_views':4,'file_bodies':25})
        return context,out

    def failed(self,root,context,previous=None,result=None):
        previous=previous or{'publication_entities':[{'id':'group','enforcement_acceptable':True,'qualifier':'LISTED_NOTE_SCOPE_ONLY'}]}
        result=result or{'publication_entities':[{'id':'group','enforcement_acceptable':False,'qualifier':'LISTED_NOTE_SCOPE_ONLY','reasons':['expired genuine group']}],
            'publication_holds':[{'id':'group','reasons':['expired genuine group']}],
            'publication_registration_defects':['group'],'publication_registration_summary':{'DEBT':1},
            'publication_registration_enforcement_acceptable':False}
        original=runtime.PackagingHold('HOLD_RUNTIME_SUCCESSOR_FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY')
        catalog.retain_comparator_hold(previous,[{'id':'baseline-original'}],result,context,original,
            phase='FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY')
        return original,previous,result

    def test_retains_complete_actual_rows_reasons_qualifiers_timing_and_hash_without_replay(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();context,out=self.context(root)
            with patch.object(runtime,'load',side_effect=AssertionError('no scientific replay')):
                original,previous,result=self.failed(root,context)
            path=out/'COMPLETE_REGISTRATION_REPLAY_HOLD.json';raw=path.read_bytes();value=json.loads(raw)
            self.assertEqual(value['expected_publication_entities'],previous['publication_entities'])
            self.assertEqual(value['actual_publication_entities'],result['publication_entities'])
            self.assertEqual(value['publication_holds'],result['publication_holds'])
            self.assertEqual(value['publication_registration_defects'],['group'])
            self.assertEqual(value['observation_timing']['observation_elapsed_seconds'],901)
            self.assertFalse(value['certifies']);self.assertFalse(value['cached_admission'])
            self.assertTrue(value['status'].startswith('HOLD_'))
            self.assertEqual(context.comparator_hold_diagnostic,{'path':str(path),'sha256':runtime.sha(raw)})
            self.assertFalse(hasattr(original,'__notes__'))

    def test_original_exception_survives_missing_context_write_failure_or_unsafe_credentials(self):
        for failure in('missing-context','known-token','pattern','write','existing','symlink'):
            with self.subTest(failure=failure),tempfile.TemporaryDirectory()as temporary:
                root=Path(temporary).resolve();context,out=self.context(root);target=out/'COMPLETE_REGISTRATION_REPLAY_HOLD.json'
                previous={'publication_entities':[{'id':'ordinary'}]}
                if failure=='missing-context':context.credential_safe_diagnostic=None
                if failure=='known-token':previous['publication_entities'][0]['reason']='fixture-only-secret'
                if failure=='pattern':previous['publication_entities'][0]['reason']='Bearer hidden-token'
                if failure=='existing':target.write_bytes(b'exact earlier immutable receipt')
                if failure=='symlink':
                    elsewhere=root/'untouched';elsewhere.write_bytes(b'exact separate file');target.symlink_to(elsewhere)
                before=target.read_bytes()if target.exists()else None
                if failure=='write':
                    with patch.object(catalog.os,'open',side_effect=OSError('fixture failure')):
                        original,_,_=self.failed(root,context,previous)
                else:original,_,_=self.failed(root,context,previous)
                self.assertEqual(str(original),'HOLD_RUNTIME_SUCCESSOR_FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY')
                self.assertTrue(original.__notes__[0].startswith('HOLD diagnostic retention unavailable:'))
                self.assertFalse(hasattr(context,'comparator_hold_diagnostic'))
                if before is None:self.assertFalse(target.exists())
                else:self.assertEqual(target.read_bytes(),before)

    def test_actual_build_comparator_failure_keeps_exact_exception_and_retains_failed_proposal(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();integration=fixtures.DefaultRouteIntegration()
            previous,original,context,calls,labels,old,imports=integration.fixture(root)
            capture,out=self.context(root)
            context.owner_evidence_directory=out;context.credential_safe_diagnostic=capture.credential_safe_diagnostic
            context.observation_timing=capture.observation_timing
            error=runtime.PackagingHold('GENUINE_SCOPE_COMPARATOR_FAILURE');seen=[]
            def comparator(prior,baseline,actual):
                seen.append((deepcopy(prior),deepcopy(actual)))
                actual['publication_holds']=[{'id':'fixture','reasons':['genuine captured mismatch']}]
                raise error
            with self.assertRaises(runtime.PackagingHold)as caught:
                with integration.scope(root,context,old,imports),patch.object(runtime,'load',return_value=SimpleNamespace(
                        baseline_rows=lambda path:[],preserving_population=comparator)):
                    catalog.build(root,root/'certificates',previous,{'fixture':True},registry_context=context)
            self.assertIs(caught.exception,error);self.assertEqual(len(seen),1)
            value=json.loads((out/'COMPLETE_REGISTRATION_REPLAY_HOLD.json').read_bytes())
            self.assertEqual(value['expected_publication_entities'],seen[0][0]['publication_entities'])
            self.assertEqual(value['actual_publication_entities'],seen[0][1]['publication_entities'])
            self.assertEqual(value['publication_holds'],[{'id':'fixture','reasons':['genuine captured mismatch']}])
            self.assertTrue((out/'SCIENTIFIC_INPUT_DATA_HOLD.json').is_file())
            self.assertFalse((out/'SCIENTIFIC_INPUT_DATA_MANIFEST.json').exists())

    def test_successful_unchanged_comparator_emits_no_failed_comparator_receipt(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();integration=fixtures.DefaultRouteIntegration()
            previous,original,context,calls,labels,old,imports=integration.fixture(root)
            capture,out=self.context(root);context.owner_evidence_directory=out
            context.credential_safe_diagnostic=capture.credential_safe_diagnostic
            with integration.scope(root,context,old,imports):
                value=catalog.build(root,root/'certificates',previous,{'fixture':True},registry_context=context)
            self.assertEqual(value['publication_entities'],previous['publication_entities'])
            self.assertFalse((out/'COMPLETE_REGISTRATION_REPLAY_HOLD.json').exists())


class PureDataHolderAndGenericBoundaryTests(unittest.TestCase):
    def test_live_cache_holder_entry_replacement_and_declared_frame_injection_are_unavailable(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();path=root/'authority.json';raw=b'{"actual":true}';path.write_bytes(raw)
            binding={'path':str(path),'sha256':runtime.sha(raw)}
            with runtime.json_data_scope(root)as view:
                first=runtime.object_at(root,binding)[2]
                with self.assertRaises(TypeError):view['material']={str(path):(raw,'identity','forged')}
                holder=runtime._JSON_DATA.get()
                for field in('material','frames','root','_parse','view'):
                    with self.subTest(field=field),self.assertRaises(AttributeError):setattr(holder,field,{'forged':True})
                for field in('material','frames'):
                    with self.subTest(field=field),self.assertRaises(AttributeError):getattr(holder,field)
                self.assertFalse(hasattr(runtime,'checked_json_data_frame'))
                self.assertFalse(hasattr(runtime,'_record_fresh_parse_frame'))
                with self.assertRaisesRegex(runtime.PackagingHold,'FRESH_CHECKED_JSON_DATA_FRAME_REQUIRED'):
                    runtime.parse_json_data(root,path,raw)
                self.assertEqual(runtime.object_at(root,binding)[2],first)
                self.assertEqual(view['parses'],1);self.assertEqual(view['parse_reuses'],1)
            with self.assertRaisesRegex(runtime.PackagingHold,'ONE_ACTIVE_JSON_DATA_OPERATION_REQUIRED'):
                runtime.parse_json_data(root,path,raw)

    def test_generic_request_has_scalar_before_spacing_and_complete_owner_before_and_after_get(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();integration=fixtures.DefaultRouteIntegration()
            previous,original,context,calls,labels,old,imports=integration.fixture(root);events=[]
            context.deadline_guard=lambda:events.append('scalar')
            context.assert_observation_current=lambda:events.append('complete-owner')
            context.begin_public_get=lambda:events.append('begin-actual-get')
            context.public_label_read_record=lambda row,legacy:legacy(row)
            generic=SimpleNamespace(_read_record_legacy=lambda row:(events.append('actual-original-generic-get')or
                {'status':'READ','proposed_label_disagrees':False,'local_manuscript_public_checksum_matches':[]}))
            def route(name,*args,**kwargs):return generic if name=='public_metadata_readback'else imports(name,*args,**kwargs)
            with integration.scope(root,context,old,route):
                catalog.build(root,root/'certificates',previous,{'fixture':True},registry_context=context)
                events.clear()
                with patch.object(catalog.time,'sleep',side_effect=lambda duration:events.append('spacing')):
                    catalog.public_label_readback(root,{'published_records':[{'doi':'fixture'}]}, {'fixture':True},registry_context=context)
            start=events.index('scalar')
            self.assertEqual(events[start:start+6],['scalar','spacing','complete-owner','begin-actual-get','actual-original-generic-get','complete-owner'])
            self.assertEqual(events.count('actual-original-generic-get'),1)

    def test_expiry_before_generic_spacing_performs_no_sleep_or_request(self):
        with tempfile.TemporaryDirectory()as temporary:
            root=Path(temporary).resolve();integration=fixtures.DefaultRouteIntegration()
            previous,original,context,calls,labels,old,imports=integration.fixture(root)
            context.public_label_read_record=lambda row,legacy:legacy(row)
            with integration.scope(root,context,old,imports):
                catalog.build(root,root/'certificates',previous,{'fixture':True},registry_context=context)
                context.deadline_guard=lambda:runtime.need(False,'ACTUAL_SCALAR_DEADLINE_EXPIRED')
                with patch.object(catalog.time,'sleep',side_effect=AssertionError('expired spacing')):
                    with self.assertRaisesRegex(runtime.PackagingHold,'ACTUAL_SCALAR_DEADLINE_EXPIRED'):
                        catalog.public_label_readback(root,{'published_records':[{'doi':'fixture'}]}, {'fixture':True},registry_context=context)


if __name__=='__main__':unittest.main()
