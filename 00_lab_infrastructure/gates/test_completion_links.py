import tempfile
import unittest
from pathlib import Path
import completion_links as gate


class CompletionLinks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'Cowork ' / 'Viridis Core docs 2.0'
        self.root.mkdir(parents=True)
        self.file = self.root / 'proof receipt.json'
        self.file.write_text('{}\n')
        self.outside = self.base / 'outside.json'
        self.outside.write_text('{}\n')
        self.report_dir = self.root / 'reports'
        self.report_dir.mkdir()

    def link(self, target): return '[evidence](<' + str(target) + '>)'
    def ok(self, text): return gate.validate(text, self.root, self.report_dir)
    def bad(self, text):
        with self.assertRaises(ValueError): self.ok(text)

    def test_absolute_literal_spaces_pass(self):
        r = self.ok(self.link(self.file))
        self.assertEqual(r['links'][0]['resolved'], str(self.file))
        self.assertEqual(r['canonical_writes'], 0)

    def test_relative_inside_pass(self): self.ok(self.link('../proof receipt.json'))
    def test_positive_line_suffix_pass(self): self.ok(self.link(str(self.file) + ':1'))
    def test_literal_colon_filename_pass(self):
        p = self.root / 'proof:1'; p.write_text('x'); self.ok(self.link(p))
    def test_traversal_inside_root_pass(self): self.ok(self.link(self.report_dir / '../proof receipt.json'))
    def test_symlink_inside_pass(self):
        p = self.root / 'inside'; p.symlink_to(self.file); self.ok(self.link(p))
    def test_repeated_link_counts_pass(self):
        r = self.ok(self.link(self.file) + '\n' + self.link(self.file))
        self.assertEqual((r['link_count'], r['distinct_resolved_files']), (2, 1))
    def test_plain_no_space_link_pass(self):
        p = self.root / 'simple.json'; p.write_text('{}'); self.ok('[e](../simple.json)')
    def test_link_in_code_does_not_count(self):
        r = self.ok('`[bad](https://example.com)`\n' + self.link(self.file))
        self.assertEqual(r['link_count'], 1)
    def test_fenced_example_does_not_count(self):
        r = self.ok('```\n[bad](https://example.com)\n```\n' + self.link(self.file))
        self.assertEqual(r['link_count'], 1)

    def test_tmp_outside_must_fail(self): self.bad(self.link(self.outside))
    def test_sibling_prefix_must_fail(self):
        sibling = Path(str(self.root) + '-other'); sibling.mkdir()
        p = sibling / 'e.json'; p.write_text('{}'); self.bad(self.link(p))
    def test_parent_traversal_outside_must_fail(self): self.bad(self.link('../../../../outside.json'))
    def test_symlink_escape_must_fail(self):
        p = self.root / 'escape'; p.symlink_to(self.outside); self.bad(self.link(p))
    def test_ancestor_symlink_escape_must_fail(self):
        p = self.root / 'escape'; p.symlink_to(self.base, target_is_directory=True)
        self.bad(self.link(p / 'outside.json'))
    def test_missing_must_fail(self): self.bad(self.link(self.root / 'missing'))
    def test_directory_must_fail(self): self.bad(self.link(self.report_dir))
    def test_directory_line_suffix_must_fail(self): self.bad(self.link(str(self.report_dir) + ':1'))
    def test_zero_line_must_fail(self): self.bad(self.link(str(self.file) + ':0'))
    def test_negative_line_must_fail(self): self.bad(self.link(str(self.file) + ':-1'))
    def test_encoded_path_must_fail(self): self.bad(self.link(str(self.file).replace(' ', '%20')))
    def test_url_must_fail(self): self.bad('[x](https://example.com/e.json)')
    def test_file_uri_must_fail(self): self.bad('[x](file://' + str(self.file) + ')')
    def test_network_relative_must_fail(self): self.bad('[x](//example.com/e.json)')
    def test_fragment_must_fail(self): self.bad(self.link(str(self.file) + '#1'))
    def test_query_must_fail(self): self.bad(self.link(str(self.file) + '?x=1'))
    def test_unwrapped_spaces_must_fail(self): self.bad('[x](' + str(self.file) + ')')
    def test_reference_link_must_fail(self): self.bad('[x][one]\n[one]: ' + str(self.file))
    def test_automatic_link_must_fail(self): self.bad(self.link(self.file) + '\n<https://example.com>')
    def test_bare_url_must_fail(self): self.bad(self.link(self.file) + '\nhttps://example.com')
    def test_bare_www_must_fail(self): self.bad(self.link(self.file) + '\nwww.example.com')
    def test_html_link_must_fail(self): self.bad(self.link(self.file) + '\n<a href="https://example.com">x</a>')
    def test_html_image_must_fail(self): self.bad(self.link(self.file) + '\n<img src="/private/tmp/outside.png">')
    def test_malformed_link_must_fail(self): self.bad(self.link(self.file) + '\n[x](<oops')
    def test_empty_links_must_fail(self): self.bad('No evidence supplied.')
    def test_blank_target_must_fail(self): self.bad('[x]()')
    def test_image_outside_must_fail(self): self.bad('![x](<' + str(self.outside) + '>)')
    def test_root_outside_report_dir_must_fail(self):
        with self.assertRaises(ValueError): gate.validate(self.link(self.file), self.root, self.base)
    def test_report_file_positive(self):
        p = self.report_dir / 'COMPLETION_REPORT.md'; p.write_text(self.link(self.file))
        self.assertEqual(gate.validate_file(p, self.root)['report_sha256'], gate.hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == '__main__': unittest.main()
