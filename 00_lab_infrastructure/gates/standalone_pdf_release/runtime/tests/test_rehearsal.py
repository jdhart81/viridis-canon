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

class ControllerHoldPathTests(unittest.TestCase):
 def test_run_api_override_holds_before_source_or_transport(self):
  with mock.patch.dict(os.environ,VIRIDIS_CORE_ROOT='/mock/core',VIRIDIS_ZENODO_API_BASE='https://sandbox.zenodo.org/api'),mock.patch.object(c,'loaded_sources')as loaded:
   with self.assertRaisesRegex(c.Hold,'API_BASE_OVERRIDE_FORBIDDEN'):
    c.run({},'/mock/output',TOKEN)
   loaded.assert_not_called()

 def test_owned_checkpoint_hold_deletes_draft_through_actual_controller_except(self):
  from contextlib import ExitStack
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();package=root/'package';package.mkdir();out=root/'engine/rehearsals/now';out.mkdir(parents=True)
   config={'package':str(package),'packaging_profile':{},'source_pins':[],
    'release_scope':'scope','source_legacy_receipt':'legacy','source_native_before_create':'native',
    'account_discovery':'account','predecessor_registration':'registration','access_registry':{}}
   (out/'CONFIG.json').write_bytes(c.encoded(config));checkpoints=out/'checkpoints';checkpoints.mkdir()
   state={'standard':c.STANDARD,'config':c.binding(out/'CONFIG.json'),'published':False,'record_id':'123','concept_id':'100',
    'ownership':None,'controlled':{},'pending':0,'operations':[{'step':'PUBLISH','outcome':'ACKNOWLEDGED_NOT_ADMITTED','transport':'badack'}]}
   (checkpoints/'00001.json').write_bytes(c.encoded(state));calls=[]
   class Response:
    status=200
    def __init__(self,data,status=200):self.data=data;self.status=status
    def read(self):return self.data
    def __enter__(self):return self
    def __exit__(self,*a):pass
   class Opener:
    deleted=False;deadline=0
    def open(self,request,timeout=120):
     calls.append((request.get_method(),request.full_url))
     if request.get_method()=='DELETE':self.deleted=True;return Response(b'',204)
     if self.deleted:raise urllib.error.HTTPError(request.full_url,410,'gone',{},io.BytesIO(b'{}'))
     return Response(json.dumps({'id':123,'submitted':False,'state':'unsubmitted'}).encode())
   sl={'id':100,'metadata':{'title':'same'}};sn={'id':100,'metadata':{'copyright':'retained'}}
   manifest={'release_week':'2026-W42','notes':[],'public_metadata':{'title':'same'}}
   registry=SimpleNamespace(require_registration=lambda *a,**k:{'receipt':{'record_id':'100'}},registered_relation_template=lambda *a,**k:{})
   mods={'methods_digest_v2':SimpleNamespace(require_publication_bound=lambda *a:(manifest,{})),
    'methods_digest_registration_v3':registry,'own_record_comparison':SimpleNamespace(),
    'own_prior_record':SimpleNamespace(),'digest_metadata':SimpleNamespace(closed_payload=lambda *a:{'metadata':{}},native_metadata=lambda *a:{}),
    'first_digest_state':SimpleNamespace(encode_api_communities=lambda x:x),'digest_weekly_state':SimpleNamespace(),
    'zenodo_transport':transport,'owned_weekly_discovery':SimpleNamespace(require_discovery=lambda *a,**k:{}),
    'manuscript_access_registry':SimpleNamespace(RegistryContext=lambda *a,**k:registry),
    'manuscript_pdf_gate':SimpleNamespace(require_local=lambda *a:{}),'publication_preservation':SimpleNamespace()}
   def obj(_root,binding):
    return {'scope':{'start_kind':'CREATE_WEEK','release_week':'2026-W42'},'legacy':{'response':sl},'native':{'response':sn},'account':{}}[binding]
   with ExitStack()as stack:
    stack.enter_context(mock.patch.dict(os.environ,VIRIDIS_CORE_ROOT=str(root)))
    stack.enter_context(mock.patch.object(c,'ROOT',root));stack.enter_context(mock.patch.dict(sys.modules,packaging_runtime=SimpleNamespace(validate=lambda *a,**k:{})))
    for name,value in {'config_value':lambda *a:package,'loaded_sources':lambda *a:mods,'obj':obj,
                       'require_cohort':lambda *a:None,'require_predecessor':lambda *a:None,
                       'inherited_inventory':lambda *a:{},'approved_inventory':lambda *a:{}}.items():
     stack.enter_context(mock.patch.object(c,name,side_effect=value))
    stack.enter_context(mock.patch.object(c,'RehearsalJournal'))
    original_receipt_obj=c.receipt_obj
    stack.enter_context(mock.patch.object(c,'receipt_obj',side_effect=lambda r,b:{}if b=='badack'else original_receipt_obj(r,b)))
    scope=c._REHEARSAL_OUTPUT.set(out)
    try:
     with self.assertRaisesRegex(c.Hold,'OWN_EXACT_ACK'):
      c.run(config,str(out),TOKEN,opener=Opener(),rehearse=True)
    finally:c._REHEARSAL_OUTPUT.reset(scope)
   self.assertEqual([method for method,url in calls],['GET','DELETE','GET'])
   deletion=json.loads((out/'attempt-0001/HOLD_DRAFT_DELETION.json').read_text())
   self.assertEqual((deletion['draft_id'],deletion['http_status']),('123',410))
   self.assertFalse(any(url.endswith('/actions/publish')for _,url in calls))
