import hashlib,sys,tempfile,types,unittest
from pathlib import Path
import runtime_closure_view as scope
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.pins=[]
        for name in('runtime','purpose'):
            p=self.root/(name+'.py');p.write_text('value=1\n');self.pins.append({'name':p.name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});m=types.ModuleType('_fixture_'+name);m.__file__=str(p);sys.modules[m.__name__]=m
        self.original={n:sys.modules[n]for n in('_fixture_runtime','_fixture_purpose')}
    def tearDown(self):
        for n in('_fixture_runtime','_fixture_purpose','_fixture_foreign'):sys.modules.pop(n,None)
        self.tmp.cleanup()
    def test_exact_extras_temporarily_hidden_then_same_identity_restored(self):
        with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):
            self.assertNotIn('_fixture_purpose',sys.modules);self.assertIs(sys.modules['_fixture_runtime'],self.original['_fixture_runtime'])
        self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_exception_still_restores_approved_identity(self):
        with self.assertRaises(ValueError):
            with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):raise ValueError('original consumer failed')
        self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_foreign_cached_own_source_not_hidden(self):
        p=self.root/'foreign.py';p.write_text('foreign=1\n');m=types.ModuleType('_fixture_foreign');m.__file__=str(p);sys.modules[m.__name__]=m
        with self.assertRaises(scope.ScopeHold):
            with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):pass
        self.assertIs(sys.modules['_fixture_foreign'],m);self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_changed_source_fails_before_hiding(self):
        Path(self.pins[1]['path']).write_text('value=2\n')
        with self.assertRaises(scope.ScopeHold):
            with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):pass
        self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_runtime_not_subset_fails(self):
        wrong=dict(self.pins[0],sha256='a'*64)
        with self.assertRaises(scope.ScopeHold):
            with scope.exact_runtime_view(self.root,self.pins,[wrong]):pass
    def test_purpose_import_inside_runtime_scope_fails(self):
        with self.assertRaises(scope.ScopeHold):
            with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):sys.modules['_fixture_purpose']=self.original['_fixture_purpose']
    def test_typed_table_reader_precedes_full_independent_consumer(self):
        calls=[]
        def read(binding):
            self.assertIn('_fixture_purpose',sys.modules);calls.append('bound_table');return {'source_pins':self.pins[:1]}
        def require(binding):
            self.assertNotIn('_fixture_purpose',sys.modules);calls.append('actual_recompute');return {'source_pins':self.pins[:1]}
        consumer=types.SimpleNamespace(read_bound_closure=read,require_current_closure=require)
        result=scope.require_current(consumer,{'path':'relative.json','sha256':'a'*64},root=self.root,purpose_pins=self.pins)
        self.assertEqual(calls,['bound_table','actual_recompute']);self.assertEqual(result['source_pins'],self.pins[:1]);self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_table_marker_does_not_skip_full_consumer_failure(self):
        def require(binding):raise ValueError('actual activation failed')
        consumer=types.SimpleNamespace(read_bound_closure=lambda b:{'source_pins':self.pins[:1],'status':'PASS'},require_current_closure=require)
        with self.assertRaises(ValueError):scope.require_current(consumer,{},root=self.root,purpose_pins=self.pins)
        self.assertIs(sys.modules['_fixture_purpose'],self.original['_fixture_purpose'])
    def test_symbol_identity_not_replaced(self):
        with scope.exact_runtime_view(self.root,self.pins,self.pins[:1]):self.assertIs(sys.modules['_fixture_runtime'],self.original['_fixture_runtime'])
        self.assertIs(sys.modules['_fixture_runtime'],self.original['_fixture_runtime'])
if __name__=='__main__':unittest.main()
