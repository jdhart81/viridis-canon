"""Portable closed namespace/source-body tests; no runtime receipt issued."""
import ast, hashlib, importlib.util, unittest
from pathlib import Path

D=Path(__file__).resolve().parent
BEFORE=D/'testdata/phase7_same_concept_runtime_namespace/phase7_runtime_update_predecessor.py'
AFTER=D/'testdata/phase7_same_concept_runtime_namespace/phase7_runtime_update_historical_e37.py'
OLD_SHA='7aa7a7920f8be5bdb37e91a3efa56acda689c2a5dd7991953691ae56c9274f42'
NEW_SHA='e37ed3d0fe05aa4ecd178c9fb0c3bbec0c49eba203c89bdfa4d2e07ee851e121'
ADDED={'digest_public_state_legacy_b5545.py','digest_successor_state.py','first_digest_state.py'}

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class NamespaceTests(unittest.TestCase):
    def test_exact_old_and_new_source_bytes(self):
        self.assertEqual(hashlib.sha256(BEFORE.read_bytes()).hexdigest(),OLD_SHA)
        self.assertEqual(hashlib.sha256(AFTER.read_bytes()).hexdigest(),NEW_SHA)
    def test_closed_three_names_only(self):
        before=load(BEFORE,'old_namespace');after=load(AFTER,'new_namespace')
        self.assertEqual(len(before.POLICY_MODULE_NAMES),18)
        self.assertEqual(after.POLICY_MODULE_NAMES,before.POLICY_MODULE_NAMES|ADDED)
        self.assertNotIn('arbitrary_plugin.py',after.POLICY_MODULE_NAMES)
    def test_every_original_function_and_signature_identical(self):
        old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(BEFORE.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        new={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(AFTER.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
        self.assertEqual(old,new)
    def test_all_other_statements_identical(self):
        def body(path):
            return [ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='POLICY_MODULE_NAMES' for t in n.targets))]
        self.assertEqual(body(BEFORE),body(AFTER))
    def test_no_new_import_or_acceptance_predicate(self):
        old=load(BEFORE,'old_contract');new=load(AFTER,'new_contract')
        for name in ('PROFILES','REQUIRED_CHECKS','POLICY_VERSION_NAMES','APPROVED_AUDIT_APPENDICES'):
            self.assertEqual(getattr(old,name),getattr(new,name))
        self.assertEqual(new._bound.__code__.co_code,old._bound.__code__.co_code)
    def test_source_delta_is_exact_insert(self):
        needle=b"    'phase7_policy_versions.py', 'digest_public_state.py', 'registration_imports.py',\n"
        self.assertEqual(AFTER.read_bytes(),BEFORE.read_bytes().replace(needle,needle+b"    'digest_public_state_legacy_b5545.py', 'digest_successor_state.py', 'first_digest_state.py',\n",1))


class CurrentGenericNamespaceTests(unittest.TestCase):
    def split(self,data):
        tree=ast.parse(data);rows=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='POLICY_MODULE_NAMES'for t in n.targets)];self.assertEqual(len(rows),1);node=rows[0];self.assertIsInstance(node.value,ast.Call);self.assertEqual(node.value.func.id,'frozenset');self.assertEqual(len(node.value.args),1);self.assertEqual(node.value.keywords,[]);names=ast.literal_eval(node.value.args[0]);self.assertIsInstance(names,set);self.assertTrue(all(type(v)is str for v in names));lines=data.decode().splitlines(keepends=True);outside=''.join(s for i,s in enumerate(lines)if not node.lineno-1<=i<node.end_lineno);return names,outside
    def closed(self,data):
        oldnames,oldother=self.split(AFTER.read_bytes());names,other=self.split(data);self.assertEqual(names,oldnames|{'digest_weekly_state.py','nightly_minimal_policy.py'});self.assertEqual(other,oldother)
    def test_exact_current_hash_and_closed_two_names(self):
        data=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),'5c1bb16662c194f402ca60ec65b1cabcfa96811df553c4c3024f083177e769b1');self.closed(data)
    def test_every_other_function_global_and_signature_byte_exact(self):
        self.closed((D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes())
    def test_foreign_namespace_rejected(self):
        data=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes()
        for name in ('digest_weekly_state.py','nightly_minimal_policy.py'):
            with self.subTest(name=name),self.assertRaises(AssertionError):self.closed(data.replace(name.encode(),b'foreign_plugin.py',1))
    def test_removing_new_or_historical_names_rejected(self):
        data=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes()
        for name in ('digest_weekly_state.py','nightly_minimal_policy.py','digest_successor_state.py','first_digest_state.py'):
            with self.subTest(name=name),self.assertRaises(AssertionError):self.closed(data.replace(("'"+name+"', ").encode(),b'',1))
    def test_original_predicate_mutation_rejected(self):
        data=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes();needle=b'raw = normalize_authority_plan(raw)';self.assertIn(needle,data)
        with self.assertRaises(AssertionError):self.closed(data.replace(needle,b'raw = raw',1))
    def test_unknown_global_or_import_rejected(self):
        data=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes()
        for extra in (b'\nimport foreign_acceptance\n',b'\nUNREVIEWED_GLOBAL = True\n'):
            with self.subTest(extra=extra),self.assertRaises(AssertionError):self.closed(data+extra)


class CurrentOwnNamespaceTests(unittest.TestCase):
    split = CurrentGenericNamespaceTests.split
    def closed(self,data):
        original=(D/'production_snapshots/phase7-20261008-own-record-comparison/before/runtime/phase7_runtime_update.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),'5c1bb16662c194f402ca60ec65b1cabcfa96811df553c4c3024f083177e769b1')
        oldnames,oldother=self.split(original);names,other=self.split(data)
        self.assertEqual(names,oldnames|{'own_record_comparison.py','methods_digest_registration_legacy_0fc739.py'})
        self.assertEqual(other,oldother)
    def test_exact_flat_current_hash_and_closed_two_own_names(self):
        data=(D/'tests/fixtures/phase7_prior_content_historical_v001/phase7_runtime_update.py').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'517adb25a3073296b8aabd2267706beef602f7307bf390ebaa5d2db91ab89d6e')
        self.closed(data)
    def test_flat_current_all_other_function_global_and_signature_bytes_exact(self):
        self.closed((D/'tests/fixtures/phase7_prior_content_historical_v001/phase7_runtime_update.py').read_bytes())
    def test_each_own_namespace_row_removal_or_foreign_replacement_rejected(self):
        data=(D/'tests/fixtures/phase7_prior_content_historical_v001/phase7_runtime_update.py').read_bytes()
        for name in ('own_record_comparison.py','methods_digest_registration_legacy_0fc739.py'):
            for changed in (data.replace(name.encode(),b'foreign_plugin.py',1),data.replace(("'"+name+"', ").encode(),b'',1)):
                self.assertNotEqual(changed,data)
                with self.subTest(name=name),self.assertRaises(AssertionError):self.closed(changed)
    def test_flat_current_predicate_mutation_unknown_global_or_import_rejected(self):
        data=(D/'tests/fixtures/phase7_prior_content_historical_v001/phase7_runtime_update.py').read_bytes();needle=b'raw = normalize_authority_plan(raw)';self.assertIn(needle,data)
        for changed in (data.replace(needle,b'raw = raw',1),data+b'\nimport foreign_acceptance\n',data+b'\nUNREVIEWED_GLOBAL = True\n'):
            with self.assertRaises(AssertionError):self.closed(changed)

if __name__=='__main__':unittest.main()
