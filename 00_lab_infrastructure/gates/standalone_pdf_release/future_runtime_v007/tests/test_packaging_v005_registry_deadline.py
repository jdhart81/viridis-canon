"""Scalar expiry before costly admission; every held original row is retained.

All source/archive/authority inputs are synthetic resolved temporary fixtures.
The portable original registrar's preserve/catch path is real. No Cowork
production modules or live scientific consumers are imported or invoked;
mocked science fixtures supply no production authority.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(HERE / 'tests'))
import test_manuscript_access_registry as fixture_module
import manuscript_access_registry as registry
import methods_digest_registration_v3 as registration
import methods_digest_registration as original_registrar


class ScalarClock:
    def __init__(self):
        self.first_get = None
        self.now = 0
        self.closed = False
        self.calls = 0

    def check(self):
        self.calls += 1
        if self.closed:
            raise registration.RegistrationHold('HOLD_FIXTURE_OBSERVATION_CLOSED')
        if self.first_get is not None and self.now > self.first_get + 900:
            raise registration.RegistrationHold('HOLD_FIXTURE_OBSERVATION_EXPIRED')


class RegistryDeadlineTests(unittest.TestCase):
    def fixture(self):
        f = fixture_module.AccessRegistryTests(methodName='runTest')
        f.setUp()
        self.addCleanup(f.doCleanups)
        return f

    def expired(self):
        clock = ScalarClock()
        clock.first_get = 1
        clock.now = 902
        return clock

    def test_expired_constructor_fails_before_any_registry_source_read(self):
        f = self.fixture()
        clock = self.expired()
        with patch.object(registry, '_object', side_effect=AssertionError('no registry IO')) as source:
            with self.assertRaisesRegex(registration.RegistrationHold, 'OBSERVATION_EXPIRED'):
                f.context(deadline_guard=clock.check)
        self.assertEqual(source.call_count, 0)
        self.assertEqual(clock.calls, 1)

    def test_invalid_deadline_callback_is_not_an_admission_verdict(self):
        f = self.fixture()
        with patch.object(registry, '_object', side_effect=AssertionError('no registry IO')):
            with self.assertRaisesRegex(registration.RegistrationHold, 'SCALAR_DEADLINE_GUARD'):
                f.context(deadline_guard='cached PASS')

    def test_pre_get_science_has_no_deadline_and_clock_is_never_started_or_reset_here(self):
        f = self.fixture()
        clock = ScalarClock()
        clock.now = 100000
        context = f.context(deadline_guard=clock.check)
        with f.fixture_authority(), patch.object(registration, 'require_registration', return_value=deepcopy(f.admitted)) as science:
            context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
        self.assertEqual(science.call_count, 1)
        self.assertIsNone(clock.first_get)
        self.assertEqual(clock.now, 100000)
        self.assertGreater(clock.calls, 2)

    def test_expired_reconsume_is_cheap_before_full_hashes_and_science(self):
        f = self.fixture()
        clock = ScalarClock()
        context = f.context(deadline_guard=clock.check)
        clock.first_get, clock.now = 1, 902
        with patch.object(context, '_registry', side_effect=AssertionError('no full registry hashes')) as hashes, \
             patch.object(registration, 'require_registration', side_effect=AssertionError('no science')) as science:
            with self.assertRaisesRegex(registration.RegistrationHold, 'OBSERVATION_EXPIRED'):
                context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
        self.assertEqual(hashes.call_count, 0)
        self.assertEqual(science.call_count, 0)

    def test_active_reconsume_keeps_all_global_source_hashes_and_fresh_science(self):
        f = self.fixture()
        other = deepcopy(f.entry)
        other['record_id'] = '99999'
        other['registration'] = f.write('other-registration.json', {'record_id': '99999', 'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2'})
        other['archive'] = f.write_bytes('other-archive.zip', Path(f.entry['archive']['path']).read_bytes())
        f.registry_value['entries'].append(other)
        f.registry_binding = f.write('registry.json', f.registry_value)
        clock = ScalarClock()
        clock.first_get, clock.now = 1, 500
        context = f.context(deadline_guard=clock.check)
        expected_global = {r['path'] for entry in f.registry_value['entries']
                           for field, r in entry.items()
                           if field not in {'record_id', 'prior_chain'} and r is not None}
        with f.fixture_authority(), patch.object(registry, 'bound', wraps=registry.bound) as hashes, \
             patch.object(registration, 'require_registration', return_value=deepcopy(f.admitted)) as science:
            for _ in range(2):
                actual = context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
                self.assertEqual(actual['strict_readback'], f.admitted['strict_readback'])
                self.assertEqual(actual['registered_public_views']['native'], f.admitted['public_native'])
                self.assertEqual(actual['public_native'], f.after_n)
        seen = [c.args[1]['path'] for c in hashes.call_args_list]
        for path in expected_global:
            self.assertGreaterEqual(seen.count(path), 2)
        self.assertEqual(science.call_count, 2)
        self.assertTrue(all(c.kwargs['views'] is None for c in science.call_args_list))
        self.assertEqual((clock.first_get, clock.now), (1, 500))
        # A changed unselected archive is still a global registry HASH hold;
        # an active scalar clock cannot skip it to admit the selected record.
        Path(other['archive']['path']).write_bytes(b'changed original input')
        with patch.object(registration, 'require_registration', side_effect=AssertionError('no scientific admission')) as science:
            with self.assertRaises(registration.d.DigestHold):
                context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
        self.assertEqual(science.call_count, 0)

    def test_expiry_immediately_before_saved_science_stops_it(self):
        f = self.fixture()
        clock = ScalarClock()
        clock.first_get, clock.now = 1, 500
        context = f.context(deadline_guard=clock.check)
        original_registry = context._registry
        def registry_then_expire():
            result = original_registry()
            clock.now = 902
            return result
        with patch.object(context, '_registry', registry_then_expire), \
             patch.object(registration, 'require_registration', side_effect=AssertionError('no science')) as science:
            with self.assertRaisesRegex(registration.RegistrationHold, 'OBSERVATION_EXPIRED'):
                context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
        self.assertEqual(science.call_count, 0)

    def test_successful_science_that_expires_stops_before_owner_and_access_reads(self):
        f = self.fixture()
        clock = ScalarClock()
        clock.first_get, clock.now = 1, 500
        def science_then_expire(*args, **kwargs):
            clock.now = 902
            return deepcopy(f.admitted)
        getter = unittest.mock.Mock(side_effect=AssertionError('no OWNER read'))
        context = f.context(deadline_guard=clock.check, owner_getter=getter)
        with patch.object(registration, 'require_registration', science_then_expire), \
             patch.object(registry.access, 'require_pair', side_effect=AssertionError('no access admission')) as access:
            with self.assertRaisesRegex(registration.RegistrationHold, 'OBSERVATION_EXPIRED'):
                context.require_registration(f.root, f.registration)
        self.assertEqual(getter.call_count, 0)
        self.assertEqual(access.call_count, 0)

    def test_original_scientific_exception_is_not_masked_by_later_deadline(self):
        f = self.fixture()
        clock = ScalarClock()
        clock.first_get, clock.now = 1, 500
        context = f.context(deadline_guard=clock.check)
        class OriginalScienceHold(ValueError):
            pass
        original_error = OriginalScienceHold('genuine original scientific mismatch')
        def failing_science(*args, **kwargs):
            clock.now = 902
            raise original_error
        with patch.object(registration, 'require_registration', failing_science):
            with self.assertRaises(OriginalScienceHold) as captured:
                context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))
        self.assertIs(captured.exception, original_error)

    def test_original_preserve_catch_retains_every_expired_group_note_and_ordinary_row(self):
        f = self.fixture()
        clock = ScalarClock()
        context = f.context(deadline_guard=clock.check)
        other_binding = f.write('second-registration.json', {'record_id': '99999', 'standard': 'VRS-METHODS-DIGEST-REGISTRATION-2'})
        rows = [{'id': 'ordinary', 'path': 'ordinary', 'status': 'SCOPED', 'enforcement_acceptable': True,
                 'publication_registration_status': 'PASS'}]
        for number, binding in ((1, f.registration), (2, other_binding)):
            group = 'group-' + str(number)
            common = {'registration_receipt': binding, 'enforcement_acceptable': True,
                      'registration_revalidated': True, 'publication_registration_status': 'PASS'}
            rows.extend([{**common, 'id': group, 'path': 'bundle-' + str(number),
                          'registration_route': original_registrar.GROUP_ROUTE,
                          'entity_type': 'METHODS_DIGEST_GROUP', 'status': 'SCOPED_DIGEST', 'certificate_valid': False},
                         {**common, 'id': 'note-' + str(number), 'path': 'note-' + str(number),
                          'group_id': group, 'registration_route': original_registrar.NOTE_ROUTE,
                          'entity_type': 'METHODS_DIGEST_NOTE', 'status': 'CERTIFIED', 'certificate_valid': True}])
        previous = {'tree_root': str(f.root), 'publication_entities': deepcopy(rows)}
        base = {'tree_root': str(f.root), 'publication_entities': [], 'file_entities': [],
                'run_entities': [], 'publication_holds': []}
        def unchanged_ordinary(ledger, ordinary):
            return {**deepcopy(ledger), 'publication_entities': deepcopy(ordinary['publication_entities'])}
        clock.first_get, clock.now = 1, 902
        with patch.object(context, '_registry', side_effect=AssertionError('no expired hashes')), \
             patch.object(registration, 'require_registration', side_effect=AssertionError('no expired science')):
            actual = original_registrar.preserve(base, previous, legacy=unchanged_ordinary,
                                                 consume=context.require_registration)
        self.assertEqual({r['id'] for r in actual['publication_entities']}, {r['id'] for r in rows})
        self.assertEqual(len(actual['publication_entities']), 5)
        self.assertEqual(next(r for r in actual['publication_entities'] if r['id'] == 'ordinary'), rows[0])
        held = [r for r in actual['publication_entities'] if r['id'] != 'ordinary']
        self.assertEqual(len(held), 4)
        self.assertTrue(all(r['status'] == 'DEBT' and r['certificate_valid'] is False
                            and r['enforcement_acceptable'] is False
                            and r['registration_revalidated'] is False
                            and 'OBSERVATION_EXPIRED' in r['reasons'][0] for r in held))
        self.assertFalse(actual['publication_registration_enforcement_acceptable'])
        self.assertEqual(len(actual['publication_registration_defects']), 4)
        self.assertEqual(previous['publication_entities'], rows)

    def test_closed_context_stops_before_registry_hashes(self):
        f = self.fixture()
        clock = ScalarClock()
        context = f.context(deadline_guard=clock.check)
        clock.closed = True
        with patch.object(context, '_registry', side_effect=AssertionError('no hashes')):
            with self.assertRaisesRegex(registration.RegistrationHold, 'OBSERVATION_CLOSED'):
                context.require_registration(f.root, f.registration, views=(f.after_l, f.after_n))


if __name__ == '__main__':
    unittest.main()
