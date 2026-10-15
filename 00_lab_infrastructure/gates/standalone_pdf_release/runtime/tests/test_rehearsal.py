"""Rehearsal keeps original source admission and transport, with no publication."""
from contextlib import contextmanager
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import urllib.error

HERE=Path(__file__).resolve().parents[1]
GATES=HERE.parents[1]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(GATES))
import digest_controller_v2 as c
spec=importlib.util.spec_from_file_location('_rehearsal_real_transport',GATES/'zenodo_transport.py')
transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
TOKEN='DUMMY_REHEARSAL_' + 'x' * 40


class RehearsalBoundaryTests(unittest.TestCase):
 def test_active_runtime_has_no_private_user_path_and_missing_root_holds(self):
  import subprocess
  for path in HERE.rglob('*'):
   if path.is_file() and path.suffix in {'.py', '.json', '.md'}:
    self.assertNotIn(b'/Users/' + b'justinhart',path.read_bytes(),str(path))
  environment={k:v for k,v in os.environ.items()if k!='VIRIDIS_CORE_ROOT'}
  result=subprocess.run([sys.executable,'-c','import packaging_runtime'],cwd=HERE,env=environment,capture_output=True,text=True)
  self.assertNotEqual(result.returncode,0);self.assertIn('HOLD_CORE_ROOT_REQUIRED',result.stderr)

 def test_publish_builder_raises_and_canonical_source_scope_stays_closed(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();core=root/'core';core.mkdir();engine=root/'engine';engine.mkdir()
   path=engine/'receipt.json';path.write_text('{}');binding=c.binding(path)
   scope=c._REHEARSAL_OUTPUT.set(engine)
   try:
    with self.assertRaises(c.Hold):c.publish_action_url('123')
    with self.assertRaises(c.Hold):c.obj(core,binding)
    self.assertEqual(c.receipt_obj(core,binding),{})
   finally:c._REHEARSAL_OUTPUT.reset(scope)
  self.assertTrue(c.publish_action_url('123').endswith('/123/actions/publish'))

 def test_actual_transport_deletes_draft_and_requires_404(self):
  for absence in (404,410,503):
   with self.subTest(absence=absence),tempfile.TemporaryDirectory()as folder:
    root=Path(folder).resolve();calls=[]
    class Response:
     status=200
     def __init__(self,body,status=200):self.body=body;self.status=status
     def read(self):return self.body
     def __enter__(self):return self
     def __exit__(self,*args):pass
    class Opener:
     deleted=False
     def open(self,request,timeout=120):
      calls.append((request.get_method(),request.full_url))
      if request.get_method()=='DELETE':self.deleted=True;return Response(b'',204)
      if self.deleted:raise urllib.error.HTTPError(request.full_url,absence,'expected absence',{},io.BytesIO(b'{}'))
      return Response(json.dumps({'id':123,'state':'unsubmitted','submitted':False}).encode())
    t=transport.ZenodoTransport('zenodo.org',TOKEN,root/'transport',opener=Opener())
    if absence==503:
     with self.assertRaises(c.Hold):c.discard_rehearsal(t,'123',save_receipt=lambda x:x)
    else:
     receipt=c.discard_rehearsal(t,'123',save_receipt=lambda x:x)
     self.assertEqual(receipt['http_status'],absence)
    self.assertEqual([method for method,url in calls],['GET','DELETE','GET'])
    self.assertFalse(any(url.endswith('/actions/publish')for method,url in calls))
    self.assertTrue(all(TOKEN.encode()not in path.read_bytes()for path in root.rglob('*')if path.is_file()))

 def test_draft_delete_refuses_published_record(self):
  client=mock.Mock();client.request.return_value={'id':'123','submitted':True,'state':'done'}
  with self.assertRaises(c.Hold):c.discard_rehearsal(client,'123',save_receipt=lambda x:x)
  client._send.assert_not_called()

 def test_journal_observes_original_budget_without_changing_live_index(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();index=root/'live/INDEX.json';index.parent.mkdir();index.write_text('{}')
   engine=root/'engine/rehearsals/now';engine.mkdir(parents=True);before=index.read_bytes()
   modules={'mutation_journal_writer':SimpleNamespace(JOURNAL='live/INDEX.json')}
   scope=c._REHEARSAL_OUTPUT.set(engine)
   try:
    with c.RehearsalJournal(root,engine/'reservations',modules)as journal,mock.patch.object(journal,'budget',return_value={'used':0})as budget:
     with self.assertRaises(c.Hold):journal.reserve('POST',c.BASE+'/api/deposit/depositions/123/actions/publish',b'{}',engine/'publish.json','2026-10-15T23:00:00Z','forbidden')
     binding=journal.reserve('POST',c.BASE+'/api/deposit/depositions',b'{}',engine/'create.json','2026-10-15T23:00:00Z','create')
     self.assertTrue(c.receipt_obj(root,binding)['rehearsal_only']);budget.assert_called_once()
   finally:c._REHEARSAL_OUTPUT.reset(scope)
   self.assertEqual(index.read_bytes(),before)

 def test_rehearse_keeps_original_source_session_checks_and_package_bytes(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();package=root/'package';package.mkdir();(package/'paper.pdf').write_bytes(b'%PDF-unchanged')
   engine=root/'engine';engine.mkdir();config={'package':str(package),'packaging_profile':{'pinned':True},'source_pins':[],'controller':c.binding(c.__file__)}
   p=root/'CONFIG.json';p.write_text(json.dumps(config));before=c.raw(package/'paper.pdf');events=[]
   @contextmanager
   def session(*args):
    events.append('enter');yield;events.append('exit')
   runtime=SimpleNamespace(session=session,validate=lambda *a,**k:events.append('validate'))
   def run(*args,**kwargs):
    self.assertTrue(kwargs['rehearse']);self.assertEqual(c._REHEARSAL_OUTPUT.get(),engine/'rehearsals/now');events.append('draft_discard');return {'status':'REHEARSED_DRAFT_DELETED','published':False,'draft_deleted_http_status':404}
   with mock.patch.object(c,'ROOT',root),mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=str(engine)),mock.patch.dict(sys.modules,packaging_runtime=runtime),mock.patch.object(c,'run',side_effect=run):
    result,binding=c.rehearse(c.binding(p),str(engine/'rehearsals/now'),TOKEN)
   self.assertEqual(events,['enter','validate','draft_discard','validate','exit'])
   self.assertTrue(result['source_session_exit_succeeded']);self.assertEqual(before,c.raw(package/'paper.pdf'))
   self.assertTrue(Path(binding['path']).is_relative_to(engine/'rehearsals/now'))


if __name__=='__main__':unittest.main()
