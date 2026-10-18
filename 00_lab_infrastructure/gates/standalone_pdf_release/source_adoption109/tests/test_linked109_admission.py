"""Inert SOURCE controls, never genuine adoption or installed admission.

Only selected pure/closed-loader ASTs are executed on private synthetic files.
Actual source before/after/patch bytes are public; no private S4 archive/audit,
Core, credential, publisher callback, HTTP, Lean or native child is opened.
A clean positive precedes every assertion-only omission mutant oracle.
"""
from __future__ import annotations
import ast,contextlib,copy,hashlib,importlib.abc,importlib.util,json,os,re,sys,tempfile,types,unittest
from pathlib import Path

HERE=Path(__file__).absolute().parent
ROOT=HERE.parents[4]
RELEASE=HERE.parent.parent
RUNTIME=RELEASE/'runtime/packaging_runtime.py'
LEGACY=ROOT/'00_lab_infrastructure/gates/production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies'
PATCH=ROOT/'00_lab_infrastructure/gates/terminal_certification/EXISTING_SELECTION.patch'
def _deny_effect(event,args):
    if event in {'subprocess.Popen','os.fork','os.forkpty','os.posix_spawn','os.exec','socket.__new__','socket.connect'}:
        raise RuntimeError('INERT_LINKED109_EFFECT_DENIED:'+event)
    if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
        if 'Viridis Core docs' in os.fsdecode(args[0]):raise RuntimeError('INERT_LINKED109_CORE_DENIED')
sys.addaudithook(_deny_effect)


SELECTED={'need','sha','linked109_json','linked109_read','linked109_apply_patch','linked109_tables',
          'linked109_live_afterimages','Linked109Loader','Linked109Finder','linked109_source_scope'}


class FixtureHold(ValueError):pass


def factory(mutant=None):
    raw=RUNTIME.read_bytes();tree=ast.parse(raw);nodes=[];constants={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            name=n.targets[0].id
            if name in {'LINKED109_PAIRS','LINKED109_PINS','LINKED109_HELPER_PATH','LINKED109_HELPER_SHA','LINKED109_CHECKERS'}:
                constants[name]=ast.literal_eval(n.value)
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in SELECTED:nodes.append(copy.deepcopy(n))
    if {n.name for n in nodes}!=SELECTED:raise AssertionError('EXACT_SELECTED_PURE_AST_SET')
    if mutant:
        reason=mutant
        class Omit(ast.NodeTransformer):
            hits=0
            def visit_Expr(self,node):
                if isinstance(node.value,ast.Call):
                    call=node.value
                    if isinstance(call.func,ast.Name) and call.func.id=='need' and len(call.args)==2 and isinstance(call.args[1],ast.Constant) and call.args[1].value==reason:
                        self.hits+=1;return ast.copy_location(ast.Pass(),node)
                    if reason=='HELPER_READ' and isinstance(call.func,ast.Name) and call.func.id=='linked109_read' and 'LINKED109_HELPER_PATH' in ast.unparse(call):
                        self.hits+=1;return ast.copy_location(ast.Pass(),node)
                return self.generic_visit(node)
        changer=Omit();nodes=[changer.visit(n)for n in nodes]
        if changer.hits!=1:raise AssertionError('EXACT_ONE_MUTANT_TARGET:'+str(changer.hits))
    # The independently pinned shared reader operates on synthetic roots only.
    shared=RELEASE/'common/stable_input_identity.py';source=shared.read_bytes()
    if hashlib.sha256(source).hexdigest()!='7e6c204993f0ba65650c58ad50a71073d803522d31fa08b93b7ce35054fa5eda':
        raise AssertionError('ACTUAL_SHARED_SOURCE_PIN')
    name='_linked109_inert_shared';module=types.ModuleType(name);module.__file__=str(shared)
    previous=sys.modules.get(name);sys.modules[name]=module
    try:exec(compile(source,str(shared),'exec'),module.__dict__)
    finally:
        if previous is None:sys.modules.pop(name,None)
        else:sys.modules[name]=previous
    def stable(path,**kw):
        try:return module.read_stable(path,**kw)
        except module.StableInputHold as exc:raise FixtureHold('fixture bounded read HOLD')from exc
    namespace=dict(constants,PackagingHold=FixtureHold,hashlib=hashlib,json=json,Path=Path,stat=__import__('stat'),
        importlib=__import__('importlib'),contextlib=contextlib,sys=sys,re=re,
        checked_root=lambda root:Path(root).resolve(strict=True),read_stable_input=stable)
    selected=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
    exec(compile(selected,'<selected-linked109-inert-AST>','exec'),namespace)
    return types.SimpleNamespace(**namespace)


def canonical(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def materials(m):
    before={p[0]:(LEGACY/p[0]).read_bytes()for p in m.LINKED109_PAIRS}
    after={p[0]:(HERE.parent/'after'/p[0]).read_bytes()for p in m.LINKED109_PAIRS}
    return before,after,PATCH.read_bytes()


def tables(m,root):
    rows=[{'name':n,'path':str(root/relative),'sha256':old}for n,relative,old,_ in m.LINKED109_PAIRS]
    rows += [{'name':n,'path':str(root/'checker'/n),'sha256':digest}for n,digest in m.LINKED109_CHECKERS.items()]
    for i in range(125):rows.append({'name':'fixture_%03d.py'%i,'path':str(root/'sources'/('%03d.py'%i)),'sha256':m.sha(b'pass\n')})
    return {'purpose_source_pins':copy.deepcopy(rows)},{'source_pins':copy.deepcopy(rows[:99])}


def write_live(m,root):
    _,after,_=materials(m)
    for n,relative,_,_ in m.LINKED109_PAIRS:
        p=root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after[n])
    h=root/m.LINKED109_HELPER_PATH;h.parent.mkdir(parents=True,exist_ok=True)
    h.write_bytes((ROOT/'00_lab_infrastructure/gates/terminal_certification/terminal_hold.py').read_bytes())
    return after,h


class Linked109Controls(unittest.TestCase):
    def test_canonical_positive(self):
        m=factory();self.assertEqual(m.linked109_json(canonical({'source_only':True}),canonical=True),{'source_only':True})
    def oracle_duplicate(self,m):
        self.assertEqual(m.linked109_json(b'{"x":1}'),{'x':1})
        with self.assertRaises(FixtureHold):m.linked109_json(b'{"x":1,"x":2}')
    def test_duplicate_rejected(self):self.oracle_duplicate(factory())
    def oracle_noncanonical(self,m):
        self.assertEqual(m.linked109_json(canonical({'x':1}),canonical=True),{'x':1})
        with self.assertRaises(FixtureHold):m.linked109_json(b'{"x":1}',canonical=True)
    def test_noncanonical_rejected(self):self.oracle_noncanonical(factory())
    def test_nonfinite_rejected(self):
        with self.assertRaises(FixtureHold):factory().linked109_json(b'{"x":NaN}')
    def test_oversized_rejected(self):
        with self.assertRaises(FixtureHold):factory().linked109_json(b' '*4_000_001)
    def test_patch_real_two_afterimages(self):
        m=factory();before,after,patch=materials(m);self.assertEqual(m.linked109_apply_patch(before,patch),after)
    def test_wrong_original_beforeimage_rejected(self):
        m=factory();before,_,patch=materials(m);before[next(iter(before))]+=b'\n'
        with self.assertRaises(FixtureHold):m.linked109_apply_patch(before,patch)
    def test_extra_third_patch_rejected(self):
        m=factory();before,_,patch=materials(m)
        with self.assertRaises(FixtureHold):m.linked109_apply_patch(before,patch+b'--- a/third.py\n')
    def test_missing_pair_rejected(self):
        m=factory();before,_,patch=materials(m);before.pop(next(iter(before)))
        with self.assertRaises(FixtureHold):m.linked109_apply_patch(before,patch)
    def oracle_closed_table(self,m):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();scope,closure=tables(m,root);_,after,_=materials(m)
            p,r=m.linked109_tables(root,scope,closure,after);self.assertEqual((len(p),len(r)),(131,100))
            scope['purpose_source_pins'].pop()
            with self.assertRaises(FixtureHold):m.linked109_tables(root,scope,closure,after)
    def test_exact131_and100_no130_fiction(self):self.oracle_closed_table(factory())
    def oracle_derived(self,m):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();scope,closure=tables(m,root);_,after,_=materials(m)
            self.assertEqual(len(m.linked109_tables(root,scope,closure,after)[0]),131)
            after[next(iter(after))]+=b'\n'
            with self.assertRaises(FixtureHold):m.linked109_tables(root,scope,closure,after)
    def test_changed_derived_bytes_rejected(self):self.oracle_derived(factory())
    def test_original99_not_subset_rejected(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();s,c=tables(m,root);_,a,_=materials(m);c['source_pins'][-1]['sha256']='0'*64
            with self.assertRaises(FixtureHold):m.linked109_tables(root,s,c,a)
    def test_checker_unchanged(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();s,c=tables(m,root);_,a,_=materials(m)
            s['purpose_source_pins'][2]['sha256']='0'*64;c['source_pins'][2]['sha256']='0'*64
            with self.assertRaises(FixtureHold):m.linked109_tables(root,s,c,a)
    def oracle_live(self,m):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();after,_=write_live(m,root);m.linked109_live_afterimages(root,after)
            (root/m.LINKED109_PAIRS[0][1]).write_bytes(b'foreign\n')
            with self.assertRaises(FixtureHold):m.linked109_live_afterimages(root,after)
    def test_live_afterimage_cas(self):self.oracle_live(factory())
    def oracle_helper(self,m):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();after,helper=write_live(m,root);m.linked109_live_afterimages(root,after);helper.unlink()
            with self.assertRaises(FixtureHold):m.linked109_live_afterimages(root,after)
    def test_missing_helper_rejected(self):self.oracle_helper(factory())
    def test_symlink_proof_rejected(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();(root/'real').write_bytes(b'x');(root/'link').symlink_to(root/'real')
            with self.assertRaises(FixtureHold):m.linked109_read(root,{'path':'link','sha256':m.sha(b'x')})
    def test_oversized_regular_proof_rejected(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();(root/'large').write_bytes(b'x'*17)
            with self.assertRaises(FixtureHold):m.linked109_read(root,{'path':'large','sha256':m.sha(b'x'*17)},limit=16)
    def test_no_path_escape(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            with self.assertRaises(FixtureHold):m.linked109_read(Path(temp).resolve(),{'path':'../escape','sha256':'0'*64})
    def test_no_extra_binding_override(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            with self.assertRaises(FixtureHold):m.linked109_read(Path(temp).resolve(),{'path':'x','sha256':'0'*64,'override':True})
    def oracle_foreign_qualified(self,m):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();_,helper=write_live(m,root)
            row={'name':'terminal_hold.py','path':str(helper),'sha256':m.LINKED109_HELPER_SHA};finder=m.Linked109Finder(root,[row]);finder.assert_current()
            name=finder.qualified;previous=sys.modules.get(name);foreign=types.ModuleType(name);foreign.__file__='/private/FOREIGN_NOT_OPENED.py';sys.modules[name]=foreign
            try:
                with self.assertRaises(FixtureHold):finder.assert_current()
            finally:
                if previous is None:sys.modules.pop(name,None)
                else:sys.modules[name]=previous
    def test_foreign_cached_qualified_rejected(self):self.oracle_foreign_qualified(factory())
    def test_no_flat_helper_alias(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();_,helper=write_live(m,root);f=m.Linked109Finder(root,[{'name':'terminal_hold.py','path':str(helper),'sha256':m.LINKED109_HELPER_SHA}])
            with self.assertRaises(FixtureHold):f.find_spec('terminal_hold')
    def test_qualified_map_exact_fixed_path(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();_,helper=write_live(m,root);f=m.Linked109Finder(root,[{'name':'terminal_hold.py','path':str(helper),'sha256':m.LINKED109_HELPER_SHA}])
            self.assertEqual(f.find_spec(f.qualified).origin,str(helper));self.assertIsNone(f.find_spec('json'))
    def test_direct_helper_alias_refused(self):
        m=factory()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();_,helper=write_live(m,root)
            row={'name':'terminal_hold.py','path':str(helper),'sha256':m.LINKED109_HELPER_SHA}
            with m.linked109_source_scope(root,[row]):
                spec=importlib.util.spec_from_file_location('verification_coverage_gates.terminal_certification.terminal_hold',helper)
                self.assertEqual(spec.origin,str(helper))
                with self.assertRaises(FixtureHold):importlib.util.spec_from_file_location('foreign_helper_alias',helper)
    def test_legacy_and_science_entry_remain(self):
        tree=ast.parse(RUNTIME.read_bytes());names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
        self.assertTrue({'_validate_legacy','_session_legacy','_validate_linked109','linked109_legacy_gate'}<=names)
        catalog=(RELEASE/'runtime/packaging_catalog.py').read_text()
        self.assertIn('original.preserving_population(previous,baseline,result)',catalog)
        self.assertIn('corpus.build(root,certificates,previous_ledger=ordinary)',catalog)
    def test_actual_old_collector_is_not_replaced_by_a_pin_table(self):
        source=RUNTIME.read_text()
        self.assertIn('original.pin_table(builder)',source)
        self.assertIn('LINKED109_ACTUAL_CLOSED_IMPORT_READBACK',source)
        self.assertIn("edges==saved['local_import_edges']",source)
    def test_worker_entry_exit_and_adoption_manifest_required(self):
        for name in ('owner_content_worker.py','scientific_registration_worker.py'):
            raw=(RELEASE/'runtime'/name).read_text();self.assertGreaterEqual(raw.count('runtime.verify_worker_source_manifest('),2)
            self.assertIn('linked109_adoption',raw);self.assertIn('linked109_outer_guard',raw)
        source=RUNTIME.read_text();self.assertIn('LINKED109_FINAL_CURRENT_FRAME_RACE',source)
        self.assertIn('WORKER_CURRENT_COMPLETE_SOURCE_MANIFEST_CHANGED',source)
    def test_seven_assertion_only_causal_mutants(self):
        families=[('LINKED109_DUPLICATE_JSON_KEY',self.oracle_duplicate),('LINKED109_CANONICAL_JSON',self.oracle_noncanonical),
          ('LINKED109_CLOSED_HISTORICAL_TABLE',self.oracle_closed_table),('LINKED109_EXACT_OLD_AND_DERIVED_CALLER',self.oracle_derived),
          ('LINKED109_CURRENT_AFTERIMAGE',self.oracle_live),('HELPER_READ',self.oracle_helper),
          ('LINKED109_FOREIGN_QUALIFIED_HELPER_CACHE',self.oracle_foreign_qualified)]
        # Seven independent omitter families. Unsupported/import/error is never
        # a kill: only the exact original assertion oracle's AssertionError.
        for name,oracle in families:
            oracle(factory())
            try:oracle(factory(name))
            except AssertionError:print('LINKED109_MUTANT_KILLED_ASSERTION:'+name)
            else:self.fail('SURVIVED:'+name)


if __name__=='__main__':unittest.main()
