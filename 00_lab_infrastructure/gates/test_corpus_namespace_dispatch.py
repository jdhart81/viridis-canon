import ast,contextlib,hashlib,types,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
BASELINE=D/'production_snapshots/phase7-20261007-decoupled-policy/after/RESEARCH_PIPELINE_v2/verification_coverage_gates/corpus_ledger.py'
class CallerTests(unittest.TestCase):
 def test_every_current_corpus_body_and_signature_remains_exact(self):
  a=ast.parse((BASELINE).read_bytes());b=ast.parse((D/'corpus_ledger.py').read_bytes());before={n.name:n for n in a.body if isinstance(n,ast.FunctionDef)};after={n.name:n for n in b.body if isinstance(n,ast.FunctionDef)}
  for name,node in before.items():
   other=after['_preserve_publication_registrations_source_original'if name=='preserve_publication_registrations'else name];other.name=name;self.assertEqual(ast.dump(node),ast.dump(other))
 def test_module_is_same_plus_rename_and_one_wrapper(self):
  a=ast.parse((BASELINE).read_bytes());b=ast.parse((D/'corpus_ledger.py').read_bytes());self.assertEqual(len(b.body),len(a.body)+1)
  clean=[n for n in b.body if not(isinstance(n,ast.FunctionDef)and n.name=='preserve_publication_registrations')]
  for left,right in zip(a.body,clean):
   if isinstance(right,ast.FunctionDef)and right.name=='_preserve_publication_registrations_source_original':right.name='preserve_publication_registrations'
   self.assertEqual(ast.dump(left),ast.dump(right))
 def wrapper(self):
  tree=ast.parse((D/'corpus_ledger.py').read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='preserve_publication_registrations');source=ast.Module(body=[fn],type_ignores=[]);events=[]
  def original(ledger,previous):events.append(('original',ledger,previous));return 'UNCHANGED_ORIGINAL_RESULT'
  data={'Path':Path,'methods_digest_registration':types.SimpleNamespace(GROUP_ROUTE='GROUP',NOTE_ROUTE='NOTE'),'_preserve_publication_registrations_source_original':original};exec(compile(source,'proposed-corpus-wrapper','exec'),data);return data['preserve_publication_registrations'],events
 def test_no_digest_population_uses_original_without_helper_import(self):
  call,events=self.wrapper();self.assertEqual(call({},None),'UNCHANGED_ORIGINAL_RESULT');self.assertEqual(call({},{}),'UNCHANGED_ORIGINAL_RESULT');self.assertEqual(call({}, {'publication_entities':[{'registration_route':'LEGACY'}]}),'UNCHANGED_ORIGINAL_RESULT');self.assertEqual(len(events),3)
 def test_digests_delegate_all_original_inputs_in_source_session(self):
  import sys
  call,events=self.wrapper();ledger={'tree_root':str(D)};previous={'publication_entities':[{'registration_route':'GROUP'}]}
  module=types.ModuleType('registration_imports')
  @contextlib.contextmanager
  def session(root):events.append(('before',root));yield;events.append(('after',root))
  module.source_session=session;old=sys.modules.get('registration_imports');sys.modules['registration_imports']=module
  try:self.assertEqual(call(ledger,previous),'UNCHANGED_ORIGINAL_RESULT')
  finally:
   if old is None:sys.modules.pop('registration_imports',None)
   else:sys.modules['registration_imports']=old
  self.assertEqual(events,[('before',D),('original',ledger,previous),('after',D)])
 def test_namespace_hold_does_not_call_original(self):
  import sys
  call,events=self.wrapper();module=types.ModuleType('registration_imports')
  @contextlib.contextmanager
  def session(root):raise ValueError('hash mismatch');yield
  module.source_session=session;old=sys.modules.get('registration_imports');sys.modules['registration_imports']=module
  try:
   with self.assertRaisesRegex(ValueError,'hash mismatch'):call({'tree_root':str(D)}, {'publication_entities':[{'registration_route':'GROUP'}]})
  finally:
   if old is None:sys.modules.pop('registration_imports',None)
   else:sys.modules['registration_imports']=old
  self.assertEqual(events,[])
 def test_wrapper_defined_before_real_main_guard(self):
  tree=ast.parse((D/'corpus_ledger.py').read_bytes());wrapper=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='preserve_publication_registrations');guard=next(n for n in tree.body if isinstance(n,ast.If)and isinstance(n.test,ast.Compare)and ast.dump(n.test)==ast.dump(ast.parse("__name__ == '__main__'",mode='eval').body));self.assertLess(wrapper.lineno,guard.lineno)
 def test_actual_guard_compilation_calls_defined_wrapper(self):
  tree=ast.parse((D/'corpus_ledger.py').read_bytes());wrapper=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='preserve_publication_registrations');guard=next(n for n in tree.body if isinstance(n,ast.If)and isinstance(n.test,ast.Compare)and ast.dump(n.test)==ast.dump(ast.parse("__name__ == '__main__'",mode='eval').body));events=[]
  scope={'__name__':'__main__','Path':Path,'methods_digest_registration':types.SimpleNamespace(GROUP_ROUTE='GROUP',NOTE_ROUTE='NOTE'),'_preserve_publication_registrations_source_original':lambda ledger,previous:events.append('original')or'UNCHANGED'}
  def main():self.assertEqual(scope['preserve_publication_registrations']({},None),'UNCHANGED');return 0
  scope['main']=main
  with self.assertRaises(SystemExit)as stopped:exec(compile(ast.Module(body=[wrapper,guard],type_ignores=[]),'actual-corpus-main-guard','exec'),scope)
  self.assertEqual(stopped.exception.code,0);self.assertEqual(events,['original'])
if __name__=='__main__':unittest.main()
