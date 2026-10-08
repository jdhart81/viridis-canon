from copy import deepcopy
import hashlib
import json
import unittest
from canon_core import coverage_provenance as p


def raw(value): return p.encoded(value)


class DualProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.historical = '1' * 64
        self.before = {'records': [{'record_id': 'legacy-' + str(i), 'metadata': {'verification_coverage': {'ledger_sha256': self.historical, 'status': 'HOLD'}},
                                   'title': 'Original ' + str(i), 'revision': 1} for i in range(215)],
                       'publications': [{'entity_id': 'old-foundation'}, {'entity_id': 'old-bcan'}],
                       'stats': {'verified': 0, 'spine': 0, 'quarantined': 1}, 'methods_digests': [], 'catalog_digest': 'old'}
        self.notes = [{'entity_id': 'note-' + str(run), 'certifies': 'LISTED_NOTE_SCOPE_ONLY', 'run_id': 'Run-' + str(run)}
                      for run in (125, 126, 128, 129, 131, 134, 141)]
        self.after = deepcopy(self.before)
        self.after['methods_digests'] = [{'entity_id': 'group', 'certifies': False, 'notes': self.notes}]
        self.rows = [{'id': 'group', 'entity_type': 'METHODS_DIGEST_GROUP', 'status': 'SCOPED_DIGEST', 'certifies': False, 'certificate_valid': False}]
        self.rows += [{'id': row['entity_id'], 'entity_type': 'METHODS_DIGEST_NOTE', 'status': 'CERTIFIED',
                       'certifies': 'LISTED_NOTE_SCOPE_ONLY', 'certificate_valid': True} for row in self.notes]
        for row in self.rows:
            row.update(publication_registration_status='PASS', registration_revalidated=True,
                       publication_binding_status='PUBLICATION_BOUND', enforcement_acceptable=True,
                       reasons=[], publication_registration_reasons=[])
        self.ledger = raw({'publication_entities': self.rows})
        self.header = p.construct_provenance(self.after, self.ledger, historical_name='corpus-ledger-historical-20261005', current_name='corpus-ledger-current-20261008')
        self.after['coverage_provenance'] = deepcopy(self.header)

    def reject(self, document=None, header=None, ledger=None):
        with self.assertRaises(ValueError):
            p.validate_provenance(document or self.after, self.header if header is None else header,
                                  current_ledger_raw=self.ledger if ledger is None else ledger)

    def test_two_snapshots_and_complete_exact_membership(self):
        checked = p.validate_provenance(self.after, self.header, current_ledger_raw=self.ledger)
        self.assertEqual(checked['historical_snapshot']['sha256'], self.historical)
        self.assertEqual(checked['current_snapshots'][-1]['sha256'], hashlib.sha256(self.ledger).hexdigest())
        self.assertEqual(len(checked['historical_record_ids']), 215)
        self.assertEqual(len(checked['current_entities']), 8)
        self.assertIs(checked['certifies'], False)

    def test_public_validation_is_metadata_only_and_does_not_change_records(self):
        before = deepcopy(self.after)
        self.assertEqual(p.validate_provenance(self.after, self.header), self.header)
        self.assertEqual(self.after, before)
        self.assertIsNot(p.validate_provenance(self.after, self.header), self.header)

    def test_unknown_header_or_snapshot_field_fails(self):
        for where in ('header', 'historical_snapshot', 'current_snapshots'):
            h = deepcopy(self.header)
            target = h if where == 'header' else h[where] if where == 'historical_snapshot' else h[where][-1]
            target['ignored'] = 'never'
            with self.subTest(where=where): self.reject(header=h)

    def test_missing_header_field_fails(self):
        for field in self.header:
            h = deepcopy(self.header); del h[field]
            with self.subTest(field=field): self.reject(header=h)

    def test_false_aggregate_certification_fails(self):
        for value in (True, 0, None, 'false'):
            h = deepcopy(self.header); h['certifies'] = value
            with self.subTest(value=value): self.reject(header=h)

    def test_snapshot_malformed_hash_and_private_name_fail(self):
        for role in ('historical_snapshot', 'current_snapshots'):
            for value in ('A' * 64, 'g' * 64, '1' * 63, True):
                h = deepcopy(self.header); target = h[role] if role == 'historical_snapshot' else h[role][-1]
                target['sha256'] = value
                with self.subTest(role=role, value=value): self.reject(header=h)
            for name in ('', '/private/tmp/ledger.json', 'file:ledger', 'dir\\ledger'):
                h = deepcopy(self.header); target = h[role] if role == 'historical_snapshot' else h[role][-1]
                target['name'] = name
                with self.subTest(role=role, name=name): self.reject(header=h)

    def test_stale_current_snapshot_fails(self):
        ledger = raw({'publication_entities': self.rows, 'new_scan': 'current'})
        self.reject(ledger=ledger)

    def test_current_row_changed_even_with_rehashed_snapshot_fails(self):
        rows = deepcopy(self.rows); rows[-1]['scientific_scope'] = 'omitted premise'
        ledger = raw({'publication_entities': rows})
        h = deepcopy(self.header); h['current_snapshots'][-1]['sha256'] = hashlib.sha256(ledger).hexdigest()
        for row in h['current_entities']: row['snapshot_sha256'] = h['current_snapshots'][-1]['sha256']
        self.reject(header=h, ledger=ledger)

    def test_hold_current_rows_never_create_header(self):
        for key, value in (('publication_registration_status', 'HOLD'), ('registration_revalidated', False),
                           ('publication_binding_status', 'HOLD'), ('enforcement_acceptable', False),
                           ('reasons', ['module missing']), ('publication_registration_reasons', ['module missing'])):
            rows = deepcopy(self.rows); rows[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.construct_provenance(self.after, raw({'publication_entities': rows}), historical_name='old', current_name='current')

    def test_wrong_note_scope_or_invalid_certificate_fails(self):
        for key, value in (('status', 'DEBT'), ('certifies', True), ('certificate_valid', False)):
            rows = deepcopy(self.rows); rows[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                p.construct_provenance(self.after, raw({'publication_entities': rows}), historical_name='old', current_name='current')

    def test_duplicate_current_ledger_ids_fail(self):
        rows = deepcopy(self.rows); rows.append(rows[0])
        with self.assertRaises(ValueError):
            p.construct_provenance(self.after, raw({'publication_entities': rows}), historical_name='old', current_name='current')

    def test_wrong_or_missing_new_cohort_fails(self):
        for change in ('remove', 'duplicate', 'wrong_type', 'new_id'):
            h = deepcopy(self.header)
            if change == 'remove': h['current_entities'].pop()
            if change == 'duplicate': h['current_entities'].append(h['current_entities'][-1])
            if change == 'wrong_type': h['current_entities'][-1]['entity_type'] = 'METHODS_DIGEST_GROUP'
            if change == 'new_id': h['current_entities'][-1]['entity_id'] = 'foreign'
            with self.subTest(change=change): self.reject(header=h)

    def test_historical_membership_changed_fails(self):
        for key in ('historical_record_ids', 'historical_publication_entity_ids'):
            h = deepcopy(self.header); h[key][-1] = 'foreign'
            with self.subTest(key=key): self.reject(header=h)

    def test_historical_coverage_hash_changed_fails(self):
        doc = deepcopy(self.after); doc['records'][0]['metadata']['verification_coverage']['ledger_sha256'] = '2' * 64
        self.reject(document=doc)

    def test_source_prefix_cannot_be_changed(self):
        h = deepcopy(self.header); h['source_prefix'] = '../science'
        self.reject(header=h)

    def test_header_removal_only_is_visible_to_unchanged_whole_guard(self):
        called = []
        def whole(before, after, groups):
            called.append(deepcopy(after))
            self.assertNotIn('coverage_provenance', after)
            self.assertEqual(after['records'], before['records'])
            self.assertEqual(after['publications'], before['publications'])
            self.assertEqual(groups, self.after['methods_digests'])
            return 'original guard result'
        self.assertEqual(p.audit_additive_update(self.before, self.after, self.header, self.ledger, whole), 'original guard result')
        self.assertEqual(len(called), 1)

    def test_existing_title_delta_fails_before_whole_guard(self):
        doc = deepcopy(self.after); doc['records'][0]['title'] = 'Rewritten'
        with self.assertRaises(ValueError): p.audit_additive_update(self.before, doc, self.header, self.ledger, lambda *a: self.fail('guard should not be bypassed'))

    def test_existing_bool_int_delta_fails(self):
        doc = deepcopy(self.after); doc['records'][0]['revision'] = True
        with self.assertRaises(ValueError): p.audit_additive_update(self.before, doc, self.header, self.ledger, lambda *a: 'not called')

    def test_unlisted_catalog_field_remains_visible_and_fails(self):
        doc = deepcopy(self.after); doc['arbitrary_server_metadata'] = True
        with self.assertRaises(ValueError): p.audit_additive_update(self.before, doc, self.header, self.ledger, lambda *a: 'not called')

    def test_missing_header_fails_before_whole_guard(self):
        doc = deepcopy(self.after); del doc['coverage_provenance']
        with self.assertRaises(ValueError): p.audit_additive_update(self.before, doc, self.header, self.ledger, lambda *a: 'not called')

    def test_header_afterbody_is_not_an_expected_baseline(self):
        expected = deepcopy(self.header); expected['current_snapshots'][-1]['sha256'] = '3' * 64
        with self.assertRaises(ValueError): p.audit_additive_update(self.before, self.after, expected, self.ledger, lambda *a: 'not called')

    def test_disjoint_historical_new_publications(self):
        doc = deepcopy(self.after); doc['publications'][0]['entity_id'] = 'group'
        h = deepcopy(self.header); h['historical_publication_entity_ids'] = sorted(['group', 'old-bcan'])
        self.reject(document=doc, header=h)

    def test_groups_and_notes_never_gain_aggregate_claims(self):
        for target, value in (('group', True), ('note', 'FORMALLY_VERIFIED')):
            doc = deepcopy(self.after)
            (doc['methods_digests'][0] if target == 'group' else doc['methods_digests'][0]['notes'][0])['certifies'] = value
            with self.subTest(target=target): self.reject(document=doc)

    def successor_fixture(self):
        doc = deepcopy(self.after)
        second = deepcopy(doc['methods_digests'][0]); second['entity_id'] = 'second-group'
        for note in second['notes']: note['entity_id'] = 'second-' + note['entity_id']
        doc['methods_digests'].append(second)
        rows = deepcopy(self.rows)
        for row in deepcopy(self.rows):
            row['id'] = 'second-group' if row['id'] == 'group' else 'second-' + row['id']
            rows.append(row)
        ledger = raw({'publication_entities': rows})
        header = p.construct_provenance(doc, ledger, historical_name='corpus-ledger-historical-20261005',
                                        current_name='corpus-ledger-current-second', prior_header=self.header)
        doc['coverage_provenance'] = header
        return doc, ledger, header

    def test_second_cohort_appends_without_rebinding_first_eight(self):
        doc, ledger, header = self.successor_fixture()
        self.assertEqual(header['current_snapshots'][:1], self.header['current_snapshots'])
        self.assertEqual(header['current_entities'][:8], self.header['current_entities'])
        self.assertEqual(len(header['current_entities']), 16)
        self.assertEqual(len(header['current_snapshots']), 2)
        self.assertTrue(p.require_append_only(self.header, header))
        self.assertEqual(p.validate_provenance(doc, header, current_ledger_raw=ledger), header)

    def test_second_cohort_cannot_rewrite_old_snapshot_or_row(self):
        doc, ledger, header = self.successor_fixture()
        for table, field in (('current_snapshots', 'sha256'), ('current_entities', 'row_sha256'), ('current_entities', 'snapshot_sha256')):
            changed = deepcopy(header); changed[table][0][field] = 'a'*64
            with self.subTest(table=table, field=field), self.assertRaises(ValueError):
                p.require_append_only(self.header, changed)

    def test_second_cohort_prior_header_is_retained_for_whole_guard(self):
        doc, ledger, header = self.successor_fixture()
        def unchanged(before, projected, groups):
            self.assertEqual(projected['coverage_provenance'], self.header)
            self.assertEqual(projected['records'], self.after['records'])
            self.assertEqual(groups[:1], self.after['methods_digests'])
            return 'original whole-guard return'
        self.assertEqual(p.audit_additive_update(self.after, doc, header, ledger, unchanged), 'original whole-guard return')

    def test_second_cohort_cannot_rewrite_prior_digest_claim(self):
        doc, ledger, header = self.successor_fixture()
        doc['methods_digests'][0]['notes'][0]['scientific_claim'] = 'stronger statement'
        with self.assertRaises(ValueError):
            p.audit_additive_update(self.after, doc, header, ledger, lambda *a: 'not called')

    def test_second_cohort_cannot_use_stale_new_snapshot(self):
        doc, ledger, header = self.successor_fixture()
        with self.assertRaises(ValueError): p.validate_provenance(doc, header, current_ledger_raw=self.ledger)

    def test_current_entity_requires_existing_snapshot_hash(self):
        changed = deepcopy(self.header); changed['current_entities'][0]['snapshot_sha256'] = 'a'*64
        self.reject(header=changed)

    def test_duplicate_snapshot_or_name_fails(self):
        for change in ('duplicate_sha','duplicate_name'):
            h=deepcopy(self.header)
            h['current_snapshots'].append(dict(h['current_snapshots'][0]))
            if change=='duplicate_name': h['current_snapshots'][-1]['sha256']='a'*64
            with self.subTest(change=change): self.reject(header=h)



from pathlib import Path
import tempfile
ROOT = Path(__file__).resolve().parents[1]

class RendererIntegration(unittest.TestCase):
    def run_case(self, body):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root/'proof.lean').write_text('theorem fixture : True := by trivial\n')
            script = """from canon_core.catalog import build_catalog,validate_catalog,validate_catalog_sources
from canon_core.coverage_provenance import construct_provenance
ledger=root/'historical.json';ledger.write_text(json.dumps({'publication_entities':[]}))
config={'release':'fixture','concept_doi':'','repository':'','include':['*.lean']};c=root/'config.json';c.write_text(json.dumps(config))
doc=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
current=json.dumps({'publication_entities':[]}).encode()
header=construct_provenance(doc,current,historical_name='historical-fixture',current_name='current-fixture')
config['coverage_provenance']=header;c.write_text(json.dumps(config))
""" + body
            exec(script, {'root': root, 'json': json})

    def test_explicit_original_inputs_build_exact_header(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
assert actual['coverage_provenance']==header
assert actual['records']==doc['records']
assert validate_catalog(actual,root=root,config_path=c,ledger_path=ledger,source_prefix='viridis-canon')==[]
assert validate_catalog_sources(actual,root,c)==[]
''')

    def test_missing_private_ledger_is_not_mislabeled_historical(self):
        self.run_case('''actual=build_catalog(root,c)
assert 'coverage_provenance'not in actual
assert actual['records'][0]['metadata']['verification_coverage']['ledger_sha256']==''
assert 'MISSING_CORPUS_LEDGER'in actual['records'][0]['metadata']['verification_coverage']['reasons']
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
''')

    def test_ci_source_comparison_retains_header_without_private_ledger(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
ledger.unlink()
assert validate_catalog(actual,root=root,config_path=c)==[]
assert validate_catalog_sources(actual,root,c)==[]
''')

    def test_missing_checked_header_fails_current_source_contract(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
del actual['coverage_provenance']
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
''')

    def test_changed_config_current_snapshot_fails(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
config['coverage_provenance']['current_snapshots'][-1]['sha256']='a'*64;c.write_text(json.dumps(config))
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
assert any('coverage provenance'in e for e in validate_catalog(actual,root=root,config_path=c))
''')

    def test_unknown_header_field_fails(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
actual['coverage_provenance']['ignored']='never'
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
assert any('coverage provenance'in e for e in validate_catalog(actual,root=root,config_path=c))
''')

    def test_false_aggregate_header_fails(self):
        self.run_case('''actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
actual['coverage_provenance']['certifies']=True
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
assert any('coverage provenance'in e for e in validate_catalog(actual,root=root,config_path=c))
''')

    def test_changed_historical_coverage_fails_even_if_digest_recomputed(self):
        self.run_case('''from canon_core.canonical import canonical_digest
actual=build_catalog(root,c,ledger_path=ledger,source_prefix='viridis-canon')
actual['records'][0]['metadata']['verification_coverage']['ledger_sha256']='a'*64
actual['records'][0]['digest']=canonical_digest({k:v for k,v in actual['records'][0].items()if k!='digest'})
actual['catalog_digest']=canonical_digest({k:v for k,v in actual.items()if k!='catalog_digest'})
assert any('coverage provenance'in e for e in validate_catalog(actual,root=root,config_path=c))
assert any('coverage provenance'in e for e in validate_catalog_sources(actual,root,c))
''')

    def test_header_schema_is_closed_without_changing_group_or_note_contracts(self):
        from canon_core.methods_digests import GROUP_FIELDS, NOTE_FIELDS
        schema=json.loads((ROOT/'docs/schemas/research-catalog-v1.json').read_bytes())
        header=schema['properties']['coverage_provenance']
        self.assertIs(schema['additionalProperties'],False)
        self.assertIs(header['additionalProperties'],False)
        self.assertEqual(set(header['required']),set(header['properties']))
        self.assertIs(header['properties']['certifies']['const'],False)
        group=schema['properties']['methods_digests']['items']
        note=group['properties']['notes']['items']
        self.assertEqual(set(group['properties']),GROUP_FIELDS)
        self.assertEqual(set(note['properties']),NOTE_FIELDS)

if __name__ == '__main__': unittest.main()
