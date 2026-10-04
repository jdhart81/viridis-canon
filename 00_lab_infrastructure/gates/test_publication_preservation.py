import unittest
from copy import deepcopy
from publication_preservation import *
class PreservationTests(unittest.TestCase):
 def test_only_proven_html_sanitization(self):
  require_public_metadata({'title':'Canon v5','description':'<p>A &mdash; B</p>\n<p>C</p>'},{'title':'Canon v5','description':'<p>A — B</p><hr/><p>C</p>'})
 def test_claim_number_and_attribute_changes_hold(self):
  for actual in ('<p>2 bits</p>','<p>1 byte</p>','<p class="changed">1 bit</p>'):
   with self.assertRaises(TransportHold):require_public_metadata({'description':actual},{'description':'<p>1 bit</p>'})
 def test_every_other_public_field_exact(self):
  for key in ('title','doi','relations','license','resource_type'):
   with self.assertRaises(TransportHold):require_public_metadata({key:'changed'},{key:'original'})
 def test_pid_repair_changes_no_other_fields(self):
  public={'pids':{'doi':{'identifier':'10.5281/zenodo.1','provider':'datacite'}}}
  draft={'pids':{'doi':{'identifier':'10.5281/zenodo.1','provider':'external'}},'metadata':{'title':'Canon'},'custom_fields':{},'access':{},'files':{}}
  result=managed_pid_payload(public,draft)
  self.assertEqual(result['pids'],public['pids'])
  for key in ('metadata','custom_fields','access','files'):self.assertEqual(result[key],draft[key])
  self.assertEqual(draft['pids']['doi']['provider'],'external')
 def test_changed_doi_never_repaired(self):
  with self.assertRaises(TransportHold):managed_pid_payload({'pids':{'doi':{'identifier':'original','provider':'datacite'}}},{'pids':{'doi':{'identifier':'changed','provider':'external'}}})
 def test_native_protected_changes_hold(self):
  before={'metadata':{'title':'original','description':'old','subjects':[]},'custom_fields':{},'access':{},'files':{}}
  after=deepcopy(before);after['metadata'].update(title='changed',description='new',subjects=[{'subject':'uncertified'}])
  with self.assertRaises(TransportHold):require_native_preservation(before,after,'new',['uncertified'])
