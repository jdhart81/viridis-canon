"""Portable closed namespace/source-body tests; no runtime receipt issued."""
import ast, hashlib, importlib.util, unittest
from pathlib import Path

D=Path(__file__).resolve().parent
BEFORE=D/'testdata/phase7_same_concept_runtime_namespace/phase7_runtime_update_predecessor.py'
AFTER=D/'phase7_runtime_update.py'
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

if __name__=='__main__':unittest.main()
