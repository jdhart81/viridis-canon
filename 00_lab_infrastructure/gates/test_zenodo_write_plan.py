import copy
import json
from pathlib import Path
import unittest
from zenodo_write_plan import amendment,validate_amendment,deposition_projection,UNCERTIFIED_STATEMENT

class WritePlanTests(unittest.TestCase):
    def test_all_amendments_and_reissue_identity_snapshots_preserve_exact_titles(self):
        base=Path(__file__).resolve().parents[2]/'reports/verification-coverage/2026-10-02/pr37-followup/write-plan'
        cases=list(base.glob('*/before_metadata.json'));self.assertEqual(len(cases),52)
        for p in cases:
            before=json.loads(p.read_text());after=amendment(before)
            self.assertEqual(after['title'],before['title'],p.parent.name)
            self.assertEqual(set(before)-set(after),set())
            for k in before:
                if k not in ('description','keywords'):self.assertEqual(after[k],before[k],(p.parent.name,k))
    def test_canon_v5_title_is_literal_and_label_once(self):
        before={'title':'Viridis Compiled Theorem Stack — Canon v5 (Dendritic Corridor Formation)','description':'Historical machine-checked assertion','keywords':['conjecture','Lean 4'],'doi':'10.5281/zenodo.20467431','relations':{'version':[{'index':4}]}}
        after=amendment(before)
        self.assertEqual(after['title'],before['title']);self.assertEqual(after['description'].count(UNCERTIFIED_STATEMENT),1)
        self.assertIn('Historical description:',after['description']);self.assertNotIn('conjecture',after['keywords']);self.assertIn('uncertified',after['keywords'])
        after['doi']='changed'
        with self.assertRaises(ValueError):validate_amendment(before,after)
    def test_wire_conversions_keep_expected_metadata_and_unknown_fields(self):
        before={'title':'T','description':'D','doi':'10.5281/x','license':{'id':'cc-by-4.0'},'resource_type':{'type':'publication','subtype':'preprint','title':'Preprint'},'communities':[{'id':'viridis-canon'}],'relations':{'version':[]},'custom':{'code:codeRepository':'https://example.org/repo'},'alternate_identifiers':[{'identifier':'10.1234/test'}]}
        original=copy.deepcopy(before);after=amendment(before);wire,changes,holds=deposition_projection(after)
        self.assertEqual(before,original);self.assertEqual(after['relations'],before['relations']);self.assertEqual(after['license'],before['license'])
        self.assertEqual(wire['metadata']['doi'],before['doi']);self.assertEqual(wire['metadata']['license'],'cc-by-4.0');self.assertEqual(wire['metadata']['publication_type'],'preprint')
        self.assertEqual(wire['metadata']['custom'],before['custom']);self.assertEqual(wire['metadata']['alternate_identifiers'],before['alternate_identifiers']);self.assertTrue(holds)
    def test_no_defaults_for_unknown_resource_or_missing_original_description(self):
        with self.assertRaises(ValueError):amendment({'title':'T'})
        with self.assertRaises(ValueError):deposition_projection({'resource_type':{'type':'invented'}})
    def test_generated_corrected_packet_has_title_invariance(self):
        base=Path(__file__).resolve().parents[2]/'reports/verification-coverage/2026-10-02/pr38-corrected-write-plan/write-plan'
        cases=list(base.glob('*/after_payload.json'));self.assertEqual(len(cases),52)
        for p in cases:
            before=json.loads((p.parent/'before_metadata.json').read_text());after=json.loads(p.read_text())['metadata']
            self.assertEqual(after['title'],before['title'],p.parent.name)
            operation=json.loads((p.parent/'PLAN.json').read_text())['operation']
            if operation=='UNCERTIFIED_METADATA_AMENDMENT':validate_amendment(before,after)
            else:self.assertEqual(after,before)

if __name__=='__main__':unittest.main()

class SandboxBoundaryTests(unittest.TestCase):
    def test_production_and_response_redirects_are_refused(self):
        from zenodo_sandbox_validation import checked_url,NoRedirect
        self.assertEqual(checked_url('https://sandbox.zenodo.org/api/deposit/depositions/12'),'https://sandbox.zenodo.org/api/deposit/depositions/12')
        for url in ('https://zenodo.org/api/deposit/depositions/12','http://sandbox.zenodo.org/api/records/12','https://sandbox.zenodo.org.evil.test/api/records/12','https://sandbox.zenodo.org/api/records/12?access_token=unsafe','https://sandbox.zenodo.org@evil.test/api/records/12'):
            with self.assertRaises(ValueError):checked_url(url)
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,None,None,None,None)
    def test_missing_sandbox_credential_is_hold_before_any_call(self):
        from zenodo_sandbox_validation import SandboxClient
        from unittest.mock import patch
        with patch.dict('os.environ',{},clear=True):
            with self.assertRaises(ValueError):SandboxClient()
