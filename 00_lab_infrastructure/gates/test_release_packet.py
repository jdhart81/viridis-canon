import unittest
import json
from pathlib import Path
from copy import deepcopy
from release_packet import LABEL, amendment, prepare_amendment, deposition_projection, digest


class ReleasePacketTests(unittest.TestCase):
    def fixture(self):
        return {'title':'Viridis Compiled Theorem Stack — Canon v5 (Dendritic Corridor Formation)',
                'doi':'10.5281/zenodo.20467431','description':'<p>Original historical claims.</p>',
                'keywords':['Lean 4','conjecture'],'license':{'id':'apache2.0'},
                'communities':[{'id':'viridis-canon'}],
                'resource_type':{'type':'software','title':'Software'},
                'relations':{'version':[{'index':4,'parent':{'pid_value':'19317982'}}]},
                'related_identifiers':[{'identifier':'10.5281/zenodo.20006414','relation':'isNewVersionOf','scheme':'doi'}]}

    def test_title_and_all_non_label_fields_survive(self):
        before=self.fixture();saved=deepcopy(before);after=amendment(before)
        self.assertEqual(before,saved)
        for field in before:
            if field not in ('description','keywords'):self.assertEqual(after[field],before[field])
        self.assertEqual(after['title'],before['title'])

    def test_one_label_and_historical_separator(self):
        result=amendment(self.fixture())
        self.assertEqual(result['description'].count(LABEL),1)
        self.assertEqual(result['description'].count('Historical description'),1)
        self.assertNotIn('not machine-verified',result['description'])
        self.assertNotIn('Machine-checked:',result['description'])
        self.assertIn('uncertified',result['keywords']);self.assertNotIn('conjecture',result['keywords'])
        self.assertEqual(amendment(result),result)

    def test_api_projection_and_expected_readback_are_distinct(self):
        r=prepare_amendment(self.fixture());p=r['api_payload']['metadata']
        self.assertEqual(p['doi'],self.fixture()['doi']);self.assertEqual(p['license'],'apache2.0')
        self.assertEqual(p['upload_type'],'software');self.assertNotIn('relations',p)
        self.assertEqual(p['communities'],[{'identifier':'viridis-canon'}])
        self.assertEqual(r['expected_after_metadata']['relations'],self.fixture()['relations'])
        self.assertEqual(r['payload_sha256'],digest(r['api_payload']))
        self.assertFalse(r['execution_authorized']);self.assertEqual(r['writes_executed'],0)

    def test_unknown_field_never_silently_cleared(self):
        b=self.fixture();b['custom']={'code:codeRepository':'https://example.org/repo'}
        r=prepare_amendment(b);self.assertEqual(r['status'],'HOLD')
        self.assertIn('HOLD_UNSUPPORTED_FIELD:custom',r['reasons'])
        self.assertEqual(r['expected_after_metadata']['custom'],b['custom'])

    def test_new_version_never_copies_old_doi(self):
        b=self.fixture();p,_,_=deposition_projection(b,new_version=True)
        self.assertNotIn('doi',p['metadata']);self.assertEqual(b['doi'],'10.5281/zenodo.20467431')

    def test_missing_input_is_hold(self):
        b=self.fixture();del b['title']
        with self.assertRaises(ValueError):prepare_amendment(b)

    def test_unsupported_license_and_resource_fail_closed(self):
        b=self.fixture();b['license']={'id':'x','unexplained':'y'}
        self.assertEqual(prepare_amendment(b)['status'],'HOLD')
        b=self.fixture();b['resource_type']={'type':'publication'}
        with self.assertRaises(ValueError):prepare_amendment(b)

    def test_every_real_amendment_title_and_field_are_preserved(self):
        source=Path(__file__).resolve().parents[2]/'reports/verification-coverage/2026-10-02/pr37-followup/ZENODO_WRITE_PLAN.json'
        rows=[r for r in json.loads(source.read_text())['records'] if r['operation']=='CONJECTURE_METADATA_AMENDMENT']
        self.assertEqual(len(rows),36)
        for row in rows:
            with self.subTest(doi=row['doi']):
                b=row['before_metadata'];r=prepare_amendment(b);a=r['expected_after_metadata']
                self.assertEqual(a['title'],b['title'])
                self.assertEqual(a.keys(),b.keys() | {'keywords'})
                for k in b:
                    if k not in ('description','keywords'):self.assertEqual(a[k],b[k])
                self.assertEqual(a['description'].count(LABEL),1)
                self.assertEqual(digest(r['api_payload']),r['payload_sha256'])
                table={f['field']:f for f in r['field_preservation']}
                for name in b:
                    self.assertEqual(table[name]['before_value'],b[name])
                    self.assertEqual(table[name]['expected_readback_value'],a[name])
                    self.assertEqual(table[name]['public_changed'],b[name]!=a[name])

    def test_entity_encoded_label_and_server_whitespace_are_idempotent(self):
        b=self.fixture()
        b['description']='<p><strong>'+LABEL.replace('—','&mdash;')+'</strong></p>\n\n'+"<p><strong>Historical description (verification assertions below are not current certification labels):</strong></p>\n<p>Historical content.</p>"
        a=amendment(b)
        import html
        self.assertEqual(html.unescape(a['description']).count(LABEL),1)
        self.assertEqual(a['description'].count('Historical description'),1)
        self.assertIn('<p>Historical content.</p>',a['description'])
        self.assertEqual(a['title'],b['title'])

    def test_repeated_exact_banners_removed_without_changing_historical_claims(self):
        b=self.fixture();a=amendment(b)
        b['description']=a['description'].replace('<hr/>','\n')
        b['description']=amendment(b)['description']
        self.assertEqual(amendment(b)['description'].count(LABEL),1)
        self.assertIn('Original historical claims.',amendment(b)['description'])
