import unittest,json
from copy import deepcopy
from unittest.mock import patch
from test_scoped_release import Fixture,m,save,sha
try:import proposed_scoped_release as m
except ModuleNotFoundError:pass

class RuleCallbackTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.addCleanup(self.f.close)
 def consume(self,**kw):
  c=kw['claim'];return {'lean_theorem':c['lean_theorem'],'semantic_tier':'ROUTINE','nonvacuity':{'tier':'TIER1','status':'CERTIFIED_WITNESS','witness_theorem':c['nonvacuity_obligation'],'certificate':kw['certificate']}}
 def call(self,cb=None):return m.assess(self.f.bundle,self.f.root,inspector=self.f.inspector,claim_rule_consumer=cb or self.consume)
 def hold(self,r):self.assertEqual(r['status'],'HOLD')
 def test_explicit_existing_witness_pass_unchanged(self):self.assertEqual(self.call()['status'],'DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND')
 def test_callback_is_not_publication_binding(self):
  with self.assertRaises(ValueError):m.require_publication_bound(self.call())
 def test_wrong_callback_theorem_hold(self):
  def cb(**kw):r=self.consume(**kw);r['lean_theorem']='foreign';return r
  self.hold(self.call(cb))
 def test_unknown_callback_fields_hold(self):
  def cb(**kw):r=self.consume(**kw);r['approved']=True;return r
  self.hold(self.call(cb))
 def test_missing_domain_hold(self):
  def cb(**kw):r=self.consume(**kw);r['nonvacuity']={'tier':'TIER0','status':'NO_HYPOTHESES','domains':[]};return r
  self.hold(self.call(cb))
 def test_explicit_witness_cannot_be_reassigned(self):
  def cb(**kw):r=self.consume(**kw);r['nonvacuity']['witness_theorem']='foreign';return r
  self.hold(self.call(cb))
 def test_main_witness_cannot_point_other_certificate(self):
  def cb(**kw):r=self.consume(**kw);r['nonvacuity']['certificate']={'path':str(self.f.formal),'sha256':sha(self.f.formal)};return r
  self.hold(self.call(cb))
 def test_defs_only_probe_formal_hold(self):
  def cb(**kw):r=self.consume(**kw);r['semantic_tier']='DEFINITIONAL';return r
  self.hold(self.call(cb))
 def test_invalid_source_not_bypassed(self):
  self.f.manifest['statement_scope'][0]['exact_source_signature']='changed';self.f.commit();self.hold(self.call())
 def test_hypothesis_drop_not_bypassed(self):
  self.f.manifest['statement_scope'][0]['ambient_source_context']=[{'line':1,'source_text':'variable (h_hidden : False)'}];self.f.commit();self.hold(self.call())
 def test_missing_witness_default_still_hold(self):
  for row in self.f.manifest['statement_scope']:row['nonvacuity_obligation']=None
  self.f.commit();self.hold(m.assess(self.f.bundle,self.f.root,inspector=self.f.inspector))
 def test_inventory_witness_original_must_remain(self):
  self.f.inventory['declarations'][0]['nonvacuity_obligation']=None;save(self.f.inventory_path,self.f.inventory);self.f.rebind(self.f.inventory_path,'statement_inventory');self.hold(self.call())
 def test_unknown_semantics_hold(self):
  def cb(**kw):r=self.consume(**kw);r['semantic_tier']='UNKNOWN';return r
  self.hold(self.call(cb))
if __name__=='__main__':unittest.main()
