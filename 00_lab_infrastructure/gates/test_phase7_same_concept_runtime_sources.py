"""Closed immutable helper/archive bytes; no live receipt or publication action."""
import ast,hashlib,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
POLICY='91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e'
LEGACY='b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38'
CODEC='cbd6aa9034e8d2e775c3b2f3226c9c41dbb39ccce1d7a59150ca52414ca8dfb2'
NAMES={'phase7_audit_policy.py','PHASE7_SUPPLEMENTAL_SOURCE_CONTRACTS.json','phase7_claim_label_render.py','nonvacuity_tier0.py','probe_observations.py','inv9_dependency_scope.py','methods_digest.py','publication_gate.py'}

class RuntimeSources(unittest.TestCase):
    def test_exact_original_codec_not_reimplemented(self):
        self.assertEqual(hashlib.sha256((D/'first_digest_state.py').read_bytes()).hexdigest(),CODEC)
    def test_exact_historical_public_constructor(self):
        self.assertEqual(hashlib.sha256((D/'digest_public_state_legacy_b5545.py').read_bytes()).hexdigest(),LEGACY)
    def test_exact_fourth_archive_members(self):
        self.assertEqual({p.name for p in (D/'policy_versions'/POLICY).iterdir()},NAMES)
    def test_fourth_archive_current_bytes_match(self):
        for name in NAMES:
            self.assertEqual((D/'policy_versions'/POLICY/name).read_bytes(),(D/name).read_bytes())
        self.assertEqual(hashlib.sha256((D/'phase7_audit_policy.py').read_bytes()).hexdigest(),POLICY)
    def test_codec_dependencies_are_measured_named_modules(self):
        import phase7_runtime_update as runtime
        imports={n.module for n in ast.walk(ast.parse((D/'first_digest_state.py').read_bytes()))if isinstance(n,ast.ImportFrom)and n.module in{'digest_metadata','methods_digest_registration'}}
        self.assertEqual(imports,{'digest_metadata','methods_digest_registration'})
        self.assertTrue({n+'.py'for n in imports}|{'first_digest_state.py'}<=runtime.POLICY_MODULE_NAMES)
    def test_successor_keeps_genuine_measured_codec_imports(self):
        imported=[(n.module,{a.name for a in n.names})for n in ast.walk(ast.parse((D/'digest_successor_state.py').read_bytes()))if isinstance(n,ast.ImportFrom)and n.module=='first_digest_state']
        self.assertTrue(any('encode_api_communities'in names for module,names in imported))
        self.assertTrue(any('private_metadata_expected'in names for module,names in imported))
        self.assertNotIn('digest_private_codec_cbd6', (D/'digest_successor_state.py').read_text())

if __name__=='__main__':unittest.main()
