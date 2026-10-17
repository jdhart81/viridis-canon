"""Real old-default validator controls over explicitly simulated trust DATA.

This is not a production renderer/provider/authority observation and does not
establish the complete packaging source-session predecessor chain.
"""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from w42_portable_fixture import PortableFixture,pdf,digest,encoded


class RealDefaultFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='w42-real-policy-')
        self.addCleanup(self.temporary.cleanup)
        self.fixture=PortableFixture(self.temporary.name)

    def require_default(self,note):
        f=self.fixture
        with f.context(),__import__('nightly_manuscript_access').frozen_sources(f.root) as load:
            return load('phase7_audit_policy').require_note_publication_bound(note,f.root,f.authority)

    def test_actual_source_then_later_old_default_reader_creates_and_rechecks_binding(self):
        f=self.fixture;note=f.base_note();value=self.require_default(note)
        self.assertEqual(value['status'],'PUBLICATION_BOUND')
        self.assertTrue(value['exact_publication_binding'])
        source=json.loads((note/'NIGHTLY_SCOPE_SOURCE.json').read_bytes())
        rule=json.loads((note/'PHASE7_RULE_EXECUTION.json').read_bytes())
        self.assertNotEqual(source['selection_invocation'],rule['scope_comparison']['current_invocation'])
        self.assertEqual(rule['scope_comparison']['new_historical_audit_row'],False)
        self.assertNotIn(f.run,[r['run_id'] for r in json.loads(f.read('synthetic-trust/PACKET.json'))['rows']])
        self.assertEqual(value['publication_binding']['sha256'],digest.sha(note/'PUBLICATION_BINDING.json'))

    def test_all_frozen_validator_bodies_and_provider_selection_bodies_are_unchanged(self):
        proof=self.fixture.structural_readback()
        self.assertGreater(len(proof['source_rows']),40)
        self.assertTrue(all(r['original_bytes_and_all_AST_nodes_preserved']for r in proof['source_rows']))
        self.assertFalse(proof['mocked_validator_or_PB_outputs'])
        self.assertEqual(proof['genuine_complete_packaging_session'],'NOT_ESTABLISHED')

    def test_rebound_simulated_provider_and_witness_fail_at_real_contract_causes(self):
        f=self.fixture;certificate=Path(f.certificate['path'])
        original_cert=certificate.read_bytes();base=json.loads(original_cert)
        cloud=Path(base['bindings']['independent_cloud_receipt']['path']);original_cloud=cloud.read_bytes()
        cases=[
            ('wrong_provider',lambda c:c.update(provider='UNTRUSTED_FIXTURE_PROVIDER'),'Comparator raw receipt contract failed'),
            ('missing_witness_export',lambda c:c['provider_response'].update(theoremNames=['bounded']),'missing a required theorem or nonvacuity witness export'),
            ('raw_failure_type',lambda c:c['provider_response'].update(type='verification-failed'),'does not establish dual-kernel acceptance'),
        ]
        try:
            for name,change,cause in cases:
                with self.subTest(name=name):
                    value=json.loads(original_cloud);change(value)
                    value['provider_response_sha256']=hashlib.sha256((json.dumps(value['provider_response'],sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
                    cloud.write_bytes(encoded(value))
                    cert=deepcopy(base);cert['bindings']['independent_cloud_receipt']['sha256']=digest.sha(cloud)
                    certificate.write_bytes(encoded(cert))
                    with f.context(),__import__('nightly_manuscript_access').frozen_sources(f.root)as load:
                        seen=load('certificate_inspection').inspect_certificate(certificate,f.root)
                    self.assertFalse(seen['valid'])
                    self.assertIn(cause,'; '.join(seen['reasons']))
                    self.assertNotIn('hash-mismatched binding','; '.join(seen['reasons']))
        finally:
            cloud.write_bytes(original_cloud);certificate.write_bytes(original_cert)

    def test_changed_frozen_source_never_uses_saved_publication_bound(self):
        f=self.fixture;note=f.base_note()
        (f.gates/'nightly_minimal_policy.py').write_bytes(f.read('RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_minimal_policy.py')+b'\n')
        with self.assertRaisesRegex(ValueError,'frozen source changed: nightly_minimal_policy.py'):
            self.require_default(note)

    def test_changed_execution_consumer_fails_actual_default_nomination(self):
        f=self.fixture;note=f.base_note();path=note/'PHASE7_RULE_EXECUTION.json'
        value=json.loads(path.read_bytes());value['execution_consumer_sha256']='f'*64;path.write_bytes(encoded(value))
        with self.assertRaisesRegex(ValueError,'exact nominated current nightly consumer required'):
            self.require_default(note)

    def test_simulated_account_pages_are_reconsumed_by_actual_complete_selector(self):
        f=self.fixture;bound=f.account_discovery();proof=json.loads(Path(bound['path']).read_bytes())
        with f.context(),__import__('nightly_manuscript_access').frozen_sources(f.root)as load:
            weekly=load('digest_weekly_state')
            self.assertEqual(weekly.require_account_discovery(proof,root=f.root)['status'],'NO_EXISTING_WEEKLY_RECORD')
            second=json.loads(Path(proof['passes'][1][0]['path']).read_bytes())
            Path(second['response_path']).write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'ACCOUNT_RAW_BINDING'):
                weekly.require_account_discovery(proof,root=f.root)

    def test_pdf_fixture_has_consistent_objects_xref_and_one_page(self):
        raw=pdf('SIMULATED fixture only')
        self.assertTrue(raw.startswith(b'%PDF-1.4\n'))
        offset=int(raw.split(b'startxref\n')[1].splitlines()[0])
        self.assertTrue(raw[offset:].startswith(b'xref\n0 6\n'))
        rows=raw[offset:].splitlines()[3:8]
        for index,row in enumerate(rows,1):
            object_offset=int(row.split()[0])
            self.assertTrue(raw[object_offset:].startswith(str(index).encode()+b' 0 obj\n'))
        self.assertIn(b'/Type /Pages /Kids [3 0 R] /Count 1',raw)
        self.assertTrue(raw.endswith(b'%%EOF\n'))


if __name__=='__main__':unittest.main()
