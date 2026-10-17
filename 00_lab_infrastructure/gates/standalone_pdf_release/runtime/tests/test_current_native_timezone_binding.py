"""Current native DATA binding changes; historical/source/science predicates stay exact."""
import ast
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime
from test_packaging_v004_platform_timezone import native_fixture


class CurrentNativeBindingTests(unittest.TestCase):
    def test_historical_observation_is_preserved_for_frozen_predecessors(self):
        self.assertEqual(runtime.PLATFORM_TIMEZONE_OBSERVATION, {
            'path': 'reports/verification-coverage/2026-10-13/standalone-pdf-platform-timezone-v001/PLATFORM_NEW_YORK_TZIF_READBACK.json',
            'sha256': '3bde531e08f840dab3a55ce4f492d660f48597a7e2490e13ffda7e58875ea94e'})

    def test_current_observation_is_exact_root_captured_2026e_not_historical_alias(self):
        self.assertEqual(runtime.CURRENT_PLATFORM_TIMEZONE_OBSERVATION, {
            'path': 'reports/verification-coverage/2026-10-17/standalone-pdf-platform-timezone-2026e/PLATFORM_NEW_YORK_TZIF_READBACK.json',
            'sha256': '5012617020f643e80c4fad18ffdef9bf119d6687efaa53ba47585e8cf1696dc4'})
        self.assertNotEqual(runtime.CURRENT_PLATFORM_TIMEZONE_OBSERVATION,
                            runtime.PLATFORM_TIMEZONE_OBSERVATION)
        self.assertEqual(str(runtime.PLATFORM_TZ_PHYSICAL),
                         '/private/var/db/timezone/tz/2026e.1.0/zoneinfo/America/New_York')

    def test_all_exact_identity_predicate_bodies_are_byte_unchanged(self):
        source = (HERE / 'packaging_runtime.py').read_text()
        nodes = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
        expected = {
            'platform_timezone_frame': '71c09f7d693d226b9b1e44e1226883a4e42d4fdc80389c04b39a9337f3834207',
            'platform_file_identity': 'b1accf23e32bb0283e76cf5aa02df26403b9f7cc420d9e479fb7c49aa1ab3a03',
            'data_alias_identity': '07d3c09b416f3630012905de858740b1cc4804fcf7cc64bdc901ebc41a6fda14',
            'same_observed_identity': '0737336234ae04b7347b2a5d4bc47145be62ae83a19e83f2eeceb6d08b65c9e1',
            'read_stable_input': 'e20cc58bbb4fd353a9d7291ea7818e7ad3ee336fbb8ebe6b5263a69d94c7607e'}
        for name, digest in expected.items():
            with self.subTest(name=name):
                raw = ast.get_source_segment(source, nodes[name]).encode()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)

    def test_frozen_predecessors_never_consume_new_current_binding(self):
        source = (HERE / 'packaging_runtime.py').read_text()
        nodes = {n.name: n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)}
        names = ['v%03d_predecessor_installation' % version for version in range(4, 11)]
        names.append('predecessor_installation')
        for name in names:
            with self.subTest(name=name):
                references = {n.id for n in ast.walk(nodes[name]) if isinstance(n, ast.Name)}
                self.assertIn('PLATFORM_TIMEZONE_OBSERVATION', references)
                self.assertNotIn('CURRENT_PLATFORM_TIMEZONE_OBSERVATION', references)

    def test_current_admission_accepts_only_exact_current_descriptor_without_historical_fallback(self):
        with native_fixture() as fixture:
            historical = dict(runtime.PLATFORM_TIMEZONE_OBSERVATION)
            value = runtime.require_platform_timezone_observation(fixture.root, fixture.binding)
            self.assertEqual(value['after'], fixture.frame)
            self.assertEqual(runtime.PLATFORM_TIMEZONE_OBSERVATION, historical)
            # An explicit synthetic historical descriptor must exist before the
            # real same_binding reader can compare it; do not rely on missing I/O.
            historical_path = fixture.root / historical['path']
            historical_path.parent.mkdir(parents=True, exist_ok=True)
            historical_path.write_bytes(fixture.receipt.read_bytes())
            synthetic_historical = {'path': historical['path'],
                                    'sha256': runtime.sha(historical_path.read_bytes())}
            with self.assertRaisesRegex(runtime.PackagingHold, 'FIXED_NATIVE_PLATFORM_TIMEZONE_OBSERVATION'):
                runtime.require_platform_timezone_observation(fixture.root, synthetic_historical)

    def test_equal_current_frame_at_another_descriptor_path_is_refused(self):
        with native_fixture() as fixture:
            alternate = fixture.receipt.with_name('alternate_timezone.json')
            alternate.write_bytes(fixture.receipt.read_bytes())
            binding = {'path': str(alternate), 'sha256': runtime.sha(alternate.read_bytes())}
            with self.assertRaisesRegex(runtime.PackagingHold, 'FIXED_NATIVE_PLATFORM_TIMEZONE_OBSERVATION'):
                runtime.require_platform_timezone_observation(fixture.root, binding)

    def test_outer_guard_binds_changed_current_sources_and_still_excludes_successor(self):
        tree = ast.parse((HERE / 'guard_methods_digest_release.py').read_text())
        value = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'SOURCE_HASHES' for t in n.targets))
        self.assertEqual(len(value), 20)
        self.assertNotIn('publish_successor_wave_guarded.py', value)
        for name in ['packaging_runtime.py', 'packaging_catalog.py']:
            self.assertEqual(value[name], hashlib.sha256((HERE / name).read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
