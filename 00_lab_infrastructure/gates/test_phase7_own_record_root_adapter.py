"""Own-record root literal profile; source-only fixtures, no API/admission."""
from pathlib import Path
import ast,copy,hashlib,json,os,tempfile,types,unittest
G=Path(os.environ.get('VIRIDIS_ROOT_ADAPTER_GATES',Path(__file__).resolve().parent)).resolve(strict=True)
PUBLIC=Path(os.environ.get('VIRIDIS_ROOT_ADAPTER_PUBLIC_GATES',G)).resolve(strict=True)
PRODUCTION=Path(os.environ.get('VIRIDIS_ROOT_ADAPTER_PRODUCTION',G/'tests/fixtures/phase7_prior_content_historical_v001')).resolve(strict=True)
OLD=G/'production_snapshots/phase7-20261008-merge-evidence-rebinding/after'
NEW=PUBLIC/'production_snapshots/phase7-20261008-own-record-root-adapter/after'
PROFILE=json.loads((PUBLIC/'tests/fixtures/phase7_own_record_root_adapter_v001/EXPECTED_PROFILE.json').read_bytes())
def load(path,name):
    module=types.ModuleType(name);module.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__);return module
def assignment(text,name):
    return next(node for node in ast.parse(text).body if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in node.targets))
def substitute(text,name,value):
    node=assignment(text,name);rows=text.splitlines(keepends=True)
    rows[node.lineno-1:node.end_lineno]=[name+'='+repr(value)+'\n'];return ''.join(rows)
def exclude(tree,names):
    return [ast.dump(n,include_attributes=False)for n in tree.body if not(isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in names for t in n.targets))]
class LiteralProfileTests(unittest.TestCase):
    def setUp(self):
        self.m=load(NEW/'root_weekly_configuration.py','fixture_own_root_adapter')
        self.extra=load(NEW/'root_weekly_purpose_specs.py','fixture_own_root_purpose')
    def test_exact_two_source_hashes_and_profile(self):
        self.assertEqual(self.m.sha(self.m.__file__),PROFILE['adapter_sha256'])
        self.assertEqual(self.m.sha(self.extra.__file__),PROFILE['purpose_extension_sha256'])
        self.assertEqual(self.m.PRODUCTION,PROFILE['production']);self.assertEqual(len(self.m.PRODUCTION),19)
        self.assertEqual(self.m.CONFIG_SHA,PROFILE['config_sha256']);self.assertEqual(self.extra.ADOPTER_SHA,PROFILE['adapter_sha256'])
    def test_adapter_byte_reversal_preserves_every_other_byte(self):
        old=(OLD/'root_weekly_configuration.py').read_text();new=(NEW/'root_weekly_configuration.py').read_text()
        self.assertEqual(self.m.sha(OLD/'root_weekly_configuration.py'),PROFILE['predecessor_adapter_sha256'])
        for name in ('CONFIG_SHA','PRODUCTION'):new=substitute(new,name,ast.literal_eval(assignment(old,name).value))
        self.assertEqual(new,old)
    def test_extension_byte_reversal_preserves_every_other_byte(self):
        old=(OLD/'root_weekly_purpose_specs.py').read_text();new=(NEW/'root_weekly_purpose_specs.py').read_text()
        self.assertEqual(self.m.sha(OLD/'root_weekly_purpose_specs.py'),PROFILE['predecessor_extension_sha256'])
        self.assertEqual(substitute(new,'ADOPTER_SHA',PROFILE['predecessor_adapter_sha256']),old)
    def test_all_adapter_functions_other_globals_ast_exact(self):
        self.assertEqual(exclude(ast.parse((OLD/'root_weekly_configuration.py').read_bytes()),{'CONFIG_SHA','PRODUCTION'}),exclude(ast.parse((NEW/'root_weekly_configuration.py').read_bytes()),{'CONFIG_SHA','PRODUCTION'}))
        self.assertEqual(exclude(ast.parse((OLD/'root_weekly_purpose_specs.py').read_bytes()),{'ADOPTER_SHA'}),exclude(ast.parse((NEW/'root_weekly_purpose_specs.py').read_bytes()),{'ADOPTER_SHA'}))
    def test_exact_two_added_names_and_six_replacements(self):
        before=ast.literal_eval(assignment((OLD/'root_weekly_configuration.py').read_text(),'PRODUCTION').value)
        self.assertEqual(set(self.m.PRODUCTION)-set(before),{'owned_creation_recovery.py','own_prior_record.py'})
        self.assertEqual(set(before)-set(self.m.PRODUCTION),set())
        self.assertEqual({n for n in before if before[n]!=self.m.PRODUCTION[n]},{'weekly_digest_executor.py','weekly_digest_boundary.py','weekly_digest_runtime.py','weekly_checkpoint_replay.py','prepare_weekly_configuration.py','invoke_weekly_digest.py'})
        self.assertEqual(self.m.PRODUCTION['weekly_digest_executor.py'],PROFILE['recovery_executor_sha256'])
class SourceSpecsTests(unittest.TestCase):
    def setUp(self):
        self.m=load(NEW/'root_weekly_configuration.py','fixture_own_root_adapter')
        self.extra=load(NEW/'root_weekly_purpose_specs.py','fixture_own_root_purpose')
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve(strict=True)
        historical=json.loads((G/'tests/fixtures/phase7_generic_root_configuration_v002/CI_SOURCE_MANIFEST.json').read_bytes())
        original={Path(row['to']).name:G.parents[1]/row['from']for row in historical['source_rows']if row['to'].startswith('repo_sources/original/')}
        sources={name:PRODUCTION/name for name in self.m.PRODUCTION};sources.update(original)
        self.specs=[{'name':name,'source':str(path),'git_path':'00_lab_infrastructure/gates/'+name,'destination':name}for name,path in sources.items()]
        self.tree={'sha':'a'*40,'truncated':False,'tree':[{'path':row['git_path'],'type':'blob','mode':'100644','sha':self.m.blob(self.m.raw(row['source']))}for row in self.specs]}
    def tearDown(self):self.tmp.cleanup()
    def test_all_26_base_source_specs_with_genuine_bytes_pass(self):
        rows=self.m.exact_sources(self.tree,self.specs);self.assertEqual(len(rows),26)
        self.assertEqual({r['name']for r in rows},set(self.m.PRODUCTION)|set(self.m.ORIGINAL)|{'prepare_first_seven_plan.py','runtime_successor.py'})
        self.assertFalse((self.root/'reports').exists())
    def test_missing_either_new_source_must_fail(self):
        for name in ('owned_creation_recovery.py','own_prior_record.py'):
            with self.subTest(name=name):self.assertRaises(ValueError,self.m.exact_sources,self.tree,[r for r in self.specs if r['name']!=name])
    def test_altered_new_source_fails_even_with_matching_new_git_blob(self):
        for name in ('owned_creation_recovery.py','own_prior_record.py','weekly_digest_executor.py'):
            with self.subTest(name=name):
                changed=self.root/name;changed.write_bytes((PRODUCTION/name).read_bytes()+b'\n# altered fixture\n')
                specs=copy.deepcopy(self.specs);next(r for r in specs if r['name']==name)['source']=str(changed)
                tree=copy.deepcopy(self.tree);next(r for r in tree['tree']if Path(r['path']).name==name)['sha']=self.m.blob(changed.read_bytes())
                self.assertRaisesRegex(ValueError,'FROZEN_GENERIC_PRODUCTION',self.m.exact_sources,tree,specs)
    def test_wrong_config_recipe_source_fails_before_exec(self):
        changed=self.root/'fake_configuration.py';changed.write_bytes(b'raise AssertionError("must never execute")\n')
        self.assertRaisesRegex(ValueError,'EXACT_FROZEN_SOURCE',self.m.recipe,changed)
    def layout(self):
        checkout=self.root/'checkout';tree=copy.deepcopy(self.tree)
        for spec,node in zip(self.specs,tree['tree']):
            name=spec['name'];gp='00_lab_infrastructure/gates/'+name if name in self.m.PRODUCTION else '00_lab_infrastructure/gates/production_snapshots/fixture/after/'+name
            node['path']=gp;path=checkout/gp;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(self.m.raw(spec['source']))
        for name in self.extra.PINS:
            gp='00_lab_infrastructure/gates/'+name;path=checkout/gp;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((G/name).read_bytes());tree['tree'].append({'path':gp,'type':'blob','mode':'100644','sha':self.m.blob(path.read_bytes())})
        return checkout,tree
    def test_checkout_selector_and_three_purpose_sources_exact29(self):
        checkout,tree=self.layout();runtime=checkout/'00_lab_infrastructure/gates/production_snapshots/fixture/after/runtime_successor.py'
        base=self.m.source_specs(checkout,tree,runtime_consumer=runtime);combined=self.extra.add_purpose_specs(self.m,checkout,tree,base)
        self.assertEqual(len(base),26);self.assertEqual(len(combined),29);self.assertEqual({r['name']for r in combined}-{r['name']for r in base},set(self.extra.PINS))
        self.assertEqual(len(self.m.exact_sources(tree,combined)),29)
    def test_wrong_adopter_duplicate_purpose_or_changed_purpose_fails(self):
        checkout,tree=self.layout();runtime=checkout/'00_lab_infrastructure/gates/production_snapshots/fixture/after/runtime_successor.py'
        base=self.m.source_specs(checkout,tree,runtime_consumer=runtime);combined=self.extra.add_purpose_specs(self.m,checkout,tree,base)
        self.assertRaises(ValueError,self.extra.add_purpose_specs,self.m,checkout,tree,combined)
        path=checkout/'00_lab_infrastructure/gates/nightly_release_checkpoint.py';path.write_bytes(b'changed source\n')
        self.assertRaises(ValueError,self.extra.add_purpose_specs,self.m,checkout,tree,base)
        wrong=self.root/'wrong_adopter.py';wrong.write_bytes(b'pass\n');old=self.m.__file__;self.m.__file__=str(wrong)
        try:self.assertRaisesRegex(ValueError,'UNCHANGED_REVIEWED_ADOPTER',self.extra.add_purpose_specs,self.m,checkout,tree,base)
        finally:self.m.__file__=old
if __name__=='__main__':unittest.main()
