"""A derived ZIP affordance never replaces protected individual-file evidence."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

import own_record_comparison as c

FIXTURES = Path(__file__).parent / 'tests/fixtures/prior_archive_link_v001'
BEFORE = json.loads((FIXTURES / 'prior_native_before_create.json').read_bytes())
AFTER = json.loads((FIXTURES / 'prior_native_after_create.json').read_bytes())
ARCHIVE = 'https://zenodo.org/api/records/23226761/files-archive'


class PriorArchiveLinkTests(unittest.TestCase):
    def pair(self):
        return deepcopy(BEFORE), deepcopy(BEFORE)

    def require(self, before, after):
        return c.require_prior_semantics(after, before, representation='NATIVE')

    def reject(self, before, after):
        with self.assertRaises(c.OwnRecordHold):
            self.require(before, after)

    def test_canonical_present_in_both(self):
        before, after = self.pair()
        self.assertEqual(self.require(before, after)['status'], 'PRIOR_RECORD_PROTECTED_READBACK_PASS')

    def test_absent_in_both(self):
        before, after = self.pair()
        before['links'].pop('archive'); after['links'].pop('archive')
        self.require(before, after)

    def test_canonical_removed(self):
        before, after = self.pair(); after['links'].pop('archive')
        audit = self.require(before, after)
        self.assertEqual(audit['differences'][0]['path'], '$.links.archive')
        self.assertTrue(audit['differences'][0]['before_present'])
        self.assertFalse(audit['differences'][0]['after_present'])
        self.assertEqual(before['links']['archive'], ARCHIVE)
        self.assertNotIn('archive', after['links'])

    def test_canonical_restored(self):
        before, after = self.pair(); before['links'].pop('archive')
        self.require(before, after)

    def test_real_recovery_fixture_only_approved_differences(self):
        self.assertEqual(BEFORE['metadata'], AFTER['metadata'])
        self.assertEqual(BEFORE['files'], AFTER['files'])
        self.assertEqual(BEFORE['pids'], AFTER['pids'])
        self.assertEqual(BEFORE['parent'], AFTER['parent'])
        audit = c.require_prior_exact(AFTER, BEFORE, representation='NATIVE', boundary='CREATE')
        self.assertEqual(audit['status'], 'PRIOR_RECORD_PROTECTED_EXCEPT_APPROVED_VERSION_FLAGS_PASS')
        self.assertEqual(audit['changed_flags'], ['versions.is_latest_draft'])
        self.assertEqual({row['path'] for row in audit['differences']}, {
            '$.links.archive', '$.links.archive_media',
            '$.media_files.entries.paper.pdf.ptif.processor.status'})

    def test_foreign_host_id_path_query_fragment_trailing_slash_rejected(self):
        values = ['https://example.org/api/records/23226761/files-archive',
                  'https://zenodo.org/api/records/23246368/files-archive',
                  'https://zenodo.org/api/records/23226761/media-files-archive',
                  ARCHIVE + '?download=1', ARCHIVE + '#fragment', ARCHIVE + '/']
        for bad in values:
            with self.subTest(value=bad):
                before, after = self.pair(); after['links']['archive'] = bad
                self.reject(before, after)

    def test_null_and_non_string_rejected_even_if_unchanged(self):
        for bad in (None, False, 23226761, ['https://zenodo.org'], {'href': ARCHIVE}):
            with self.subTest(value=bad):
                before, after = self.pair()
                before['links']['archive'] = bad; after['links']['archive'] = bad
                self.reject(before, after)

    def test_missing_or_invalid_record_id_rejected(self):
        for bad in (None, '', '023226761', '23226761/other', True):
            with self.subTest(value=bad):
                before, after = self.pair()
                if bad is None:before.pop('id');after.pop('id')
                else:before['id'] = bad;after['id'] = bad
                self.reject(before, after)

    def test_parent_archive_link_remains_strict(self):
        before, after = self.pair()
        before['parent'].setdefault('links', {})['archive'] = ARCHIVE
        after['parent'].setdefault('links', {})['archive'] = ARCHIVE
        after['parent']['links'].pop('archive')
        self.reject(before, after)

    def test_file_archive_link_remains_strict(self):
        before, after = self.pair(); key = next(iter(before['files']['entries']))
        before['files']['entries'][key].setdefault('links', {})['archive'] = ARCHIVE
        after['files']['entries'][key].setdefault('links', {})['archive'] = ARCHIVE
        after['files']['entries'][key]['links'].pop('archive')
        self.reject(before, after)

    def test_unknown_root_link_remains_strict(self):
        before, after = self.pair(); before['links']['unknown_control'] = 'https://zenodo.org/records/23226761'
        self.reject(before, after)

    def test_self_and_doi_links_remain_strict(self):
        for name in ('self', 'doi', 'self_doi', 'parent_doi'):
            with self.subTest(link=name):
                before, after = self.pair(); after['links'][name] = 'https://zenodo.org/records/23246368'
                self.reject(before, after)

    def test_all_metadata_changes_remain_strict(self):
        for name in ('title', 'description', 'creators', 'publication_date', 'keywords', 'rights', 'resource_type', 'related_identifiers'):
            with self.subTest(field=name):
                before, after = self.pair(); after['metadata'][name] = 'CHANGED'
                self.reject(before, after)

    def test_main_file_name_size_checksum_count_changes_remain_strict(self):
        for field in ('key', 'size', 'checksum', 'count'):
            with self.subTest(field=field):
                before, after = self.pair(); key = next(iter(after['files']['entries']))
                if field == 'count':after['files']['entries'].pop(key)
                else:after['files']['entries'][key][field] = 'CHANGED'
                self.reject(before, after)

    def test_pid_and_concept_identity_remain_strict(self):
        for field in ('record_pid', 'concept_pid', 'record_id', 'concept_id'):
            with self.subTest(field=field):
                before, after = self.pair()
                if field == 'record_pid':after['pids']['doi']['identifier'] = '10.5281/zenodo.23246368'
                elif field == 'concept_pid':after['parent']['pids']['doi']['identifier'] = '10.5281/zenodo.23246368'
                elif field == 'record_id':after['id'] = '23246368'
                else:after['parent']['id'] = '23246368'
                self.reject(before, after)

    def test_version_identity_remains_strict(self):
        before, after = self.pair(); after['versions']['index'] += 1
        self.reject(before, after)

    def test_archive_exclusion_not_global_processing_link(self):
        self.assertNotIn('archive', c._PROCESSING_LINKS)
        self.assertEqual(c._prior_links({'archive': ARCHIVE}), {'archive': ARCHIVE})

    def test_no_observation_mutation(self):
        before, after = self.pair(); after['links'].pop('archive')
        originals = deepcopy((before, after)); self.require(before, after)
        self.assertEqual((before, after), originals)


if __name__ == '__main__':
    unittest.main(verbosity=2)
