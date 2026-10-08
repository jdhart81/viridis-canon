"""Exact closed three-purpose extension over fixture own merged blobs."""
import copy,unittest
from pathlib import Path
import root_weekly_configuration as m
import root_weekly_purpose_specs as extra
import test_root_weekly_configuration as fixtures
class Tests(unittest.TestCase):
 def setUp(self):self.f=fixtures.Tests(methodName='runTest');self.f.setUp()
 def tearDown(self):self.f.tearDown()
 def layout(self):
  checkout,tree=self.f.checkout_fixture();sources=Path(__file__).parent/'repo_sources/purpose'
  for name in extra.PINS:
   gp='00_lab_infrastructure/gates/'+name;p=checkout/gp;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((sources/name).read_bytes());tree['tree'].append({'path':gp,'type':'blob','mode':'100644','sha':m.blob(p.read_bytes())})
  runtime=checkout/'00_lab_infrastructure/gates/production_snapshots/fixture/after/runtime_successor.py';return checkout,tree,m.source_specs(checkout,tree,runtime_consumer=runtime)
 def test_closed27_source_specs_pass_without_runtime_install(self):
  checkout,tree,base=self.layout();combined=extra.add_purpose_specs(m,checkout,tree,base);self.assertEqual(len(combined),27);self.assertEqual({r['name']for r in combined}-{r['name']for r in base},set(extra.PINS));self.assertEqual(len(m.exact_sources(tree,combined)),27);self.assertFalse((self.f.root/'reports').exists())
 def test_wrong_nightly_bytes_or_duplicate_spec_fails_before_copy(self):
  checkout,tree,base=self.layout();combined=extra.add_purpose_specs(m,checkout,tree,base);self.assertRaises(ValueError,extra.add_purpose_specs,m,checkout,tree,combined);(checkout/'00_lab_infrastructure/gates/nightly_release_checkpoint.py').write_bytes(b'changed nightly source');self.assertRaises(ValueError,extra.add_purpose_specs,m,checkout,tree,base);self.assertFalse((self.f.root/'reports').exists())
if __name__=='__main__':unittest.main()
