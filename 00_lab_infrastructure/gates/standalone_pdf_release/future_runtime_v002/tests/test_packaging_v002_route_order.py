"""Actual activation27/current92 ordering with synthetic science/time only."""
from pathlib import Path
from copy import deepcopy
import json,sys,tempfile,unittest,contextlib
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(HERE/'tests'))
import packaging_catalog as catalog
import packaging_nightly_coverage as coverage
import packaging_runtime as runtime
import test_packaging_default_routes as fixtures
import packaging_nightly_intake as intake

class ActualRegistrationOrderWithSlowSyntheticScan(unittest.TestCase):
    def exercise(self, registrations_first):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            integration = fixtures.DefaultRouteIntegration()
            previous, original, scoped, calls, labels, old, imports = integration.fixture(root)
            # Preserve the complete scientific-predecessor fixture and exercise
            # the original copied 27-identity checks, not an inferred count.
            more = [{**deepcopy(original[0]), 'id': 'publication:additional:' + str(i),
                     'path': 'additional/' + str(i)} for i in range(54)]
            previous['publication_entities'] = [*original, *more,
                                               *previous['publication_entities'][35:]]
            self.assertEqual(len(previous['publication_entities']), 92)
            canonical = root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
            canonical.parent.mkdir()
            canonical.write_text(json.dumps(previous))
            proof = root / 'slow-source.lean'
            proof.write_bytes(b'unchanged exact synthetic science input')
            observer = fixtures.ObservationReplayTests()
            stack, actual_context, transport_calls, clock, output = observer.setup_context(root, begin=False)
            events = []
            original_consume = scoped.require_registration

            def consume(*args, **kwargs):
                result = original_consume(*args, **kwargs)
                events.append(('registration-owner-read', clock[0]))
                actual_context.owner_getter('24000001', 'application/json')
                return result

            actual_context.require_registration = consume
            actual_context.public_label_read_record = scoped.public_label_read_record
            corpus = imports('corpus_ledger')
            original_build = corpus.build

            def slow_science(*args, **kwargs):
                events.append(('complete-scan-start', clock[0]))
                proof.read_bytes()
                # This is a fake clock, not a sleep or a real scientific scan.
                # The local phase is within the additive3000-child budget, but
                # greater than the separate900-public observation lifetime.
                clock[0] += 1001
                events.append(('complete-scan-finish', clock[0]))
                return original_build(*args, **kwargs)

            corpus.build = slow_science
            with stack, integration.scope(root, actual_context, old, imports):
                if registrations_first:
                    coverage._registrations(root, previous, {'publication_entities': original[:27]})
                fresh = catalog.build(root, root / 'certificates', previous, {'fixture_profile': True},
                                      registry_context=actual_context)
                if not registrations_first:
                    coverage._registrations(root, fresh, {'publication_entities': original[:27]})
                    self.assertEqual(actual_context.observation_timing()['observation_elapsed_seconds'], 0)
                    self.assertEqual(fresh['publication_entities'], previous['publication_entities'])
            return events, transport_calls

    def test_activation_registration_prime_finishes_science_before_first_owner_get(self):
        events,requests=self.exercise(registrations_first=True)
        self.assertEqual(sum(event[0]=='complete-scan-start'for event in events),1)
        scan_end=next(i for i,event in enumerate(events)if event[0]=='complete-scan-finish')
        first=next(i for i,event in enumerate(events)if event[0]=='registration-owner-read')
        self.assertLess(scan_end,first)
        self.assertEqual(len(requests),1)

    def test_science_first_then_the_same_original27_and_current92_checks_fits_the_context(self):
        events, requests = self.exercise(registrations_first=False)
        first_read = next(i for i, item in enumerate(events) if item[0] == 'registration-owner-read')
        scan_end = next(i for i, item in enumerate(events) if item[0] == 'complete-scan-finish')
        self.assertLess(scan_end, first_read)
        self.assertEqual(events[scan_end][1], 1001)
        self.assertEqual(len(requests), 1)


class PreparedIntakeGateOrder(unittest.TestCase):
    def test_original_apply_runs_activation_callback_after_scan_before_gate_and_exact_cas(self):
        for allowed in (False,True):
            with self.subTest(allowed=allowed),tempfile.TemporaryDirectory()as temporary:
                root=Path(temporary).resolve();artifact=root/'finalized';artifact.mkdir()
                for name in ('paper.pdf','paper.tex','claim_binding.json','POST_ARISTOTLE_REVIEW.json'):
                    (artifact/name).write_bytes(('explicit fixture '+name).encode())
                certificate=root/'certificate.json';certificate.write_text('{}')
                ledger=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger.parent.mkdir()
                old={'tree_root':str(root),'publication_entities':[]};ledger.write_text(json.dumps(old));before=ledger.read_bytes();expected=runtime.sha(before)
                assessment={'certificate':{'path':str(certificate),'sha256':runtime.sha(certificate.read_bytes())},
                    'sealed_manuscript':{'explicit_fixture':True},'final_manuscript':{'explicit_fixture':True},
                    'final_pdf_sha256':runtime.sha((artifact/'paper.pdf').read_bytes()),'final_tex_sha256':runtime.sha((artifact/'paper.tex').read_bytes()),
                    'allowed_diff_sha256':'a'*64,'diff_classification':'VERIFICATION_STATUS_ONLY'}
                plan={'status':'READY_FOR_AUTHORIZED_REGISTRATION','ledger_sha256':expected,'assessment':assessment,
                    'certificate':assessment['certificate'],'entry':{'id':'publication:fixture-new','path':'replaced-by-original-apply'},
                    'claim_map':{'sha256':runtime.sha((artifact/'claim_binding.json').read_bytes())},
                    'post_lean_review':{'sha256':runtime.sha((artifact/'POST_ARISTOTLE_REVIEW.json').read_bytes())},
                    'reviewer':{'explicit_fixture':True},'reviewed_at_utc':'2020-01-01T00:00:00Z'}
                output=root/'RESEARCH_PIPELINE_v2/publication_releases/Run-999/fixture';events=[]
                def scan(*args,**kwargs):
                    events.append('scan')
                    self.assertTrue((output/'registration_audit/corpus_ledger_before.json').is_file())
                    self.assertEqual(kwargs['inventory_publications']['publication_entities'][-1]['path'],str(output.relative_to(root)))
                    return old
                def activation():
                    events.append('activation27/window')
                    if not allowed:raise ValueError('explicit activation/window fixture HOLD')
                def preserve(*args,**kwargs):events.append('registration');return args[2]
                def gate(*args,**kwargs):events.append('publication-gate');return {'status':'PASS'}
                def cas(*args):events.append('exact-cas');return fixtures.real_cas()(*args)
                with contextlib.ExitStack()as stack:
                    for target,name,value in ((intake,'prepare',plan),(intake,'assessment',assessment),(intake,'operation',({},object())),
                                               (intake,'validate_publication_binding',None),(catalog,'observation_guard',None),
                                               (catalog,'authorize_canonical_write',None),(catalog,'finish_canonical_write',None)):
                        stack.enter_context(patch.object(target,name,return_value=value))
                    stack.enter_context(patch.object(intake,'inspect_certificate',return_value={'explicit_fixture':True}))
                    stack.enter_context(patch.object(catalog,'build',side_effect=scan))
                    stack.enter_context(patch.object(intake,'preserve_registered',side_effect=preserve))
                    stack.enter_context(patch.object(intake,'evaluate_publication',side_effect=gate))
                    import corpus_ledger
                    stack.enter_context(patch.object(corpus_ledger,'write_guarded_ledger',side_effect=cas))
                    if allowed:
                        result=intake.apply(root,'Run-999',artifact,output,expected_ledger_sha256=expected,before_registration=activation)
                        self.assertEqual(result['status'],'PUBLICATION_BOUND_REGISTERED')
                    else:
                        with self.assertRaisesRegex(ValueError,'activation/window fixture HOLD'):
                            intake.apply(root,'Run-999',artifact,output,expected_ledger_sha256=expected,before_registration=activation)
                self.assertEqual(events,['scan','activation27/window','registration','publication-gate','exact-cas']if allowed else['scan','activation27/window'])
                if not allowed:self.assertEqual(ledger.read_bytes(),before)
                else:self.assertEqual(json.loads(ledger.read_bytes())['publication_entities'][0]['id'],'publication:fixture-new')


if __name__ == '__main__':
    unittest.main()
