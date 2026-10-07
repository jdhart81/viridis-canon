"""Platform-temp fixture regression; assertions and production gates stay intact."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from test_methods_digest import Fixture as DigestFixture
from test_phase7_runtime_update import Fixture as RuntimeFixture

class PortableFixtureTests(unittest.TestCase):
 def check_fixture(self,factory):
  # Linux need not provide macOS's /private/tmp. A controlled platform temp
  # root with spaces also proves fixture paths do not assume a fixed root.
  with tempfile.TemporaryDirectory()as parent:
   selected=Path(parent).resolve()/'portable temp root with spaces';selected.mkdir()
   with patch.object(tempfile,'tempdir',str(selected)):
    fixture=factory()
    try:
     self.assertTrue(fixture.root.is_relative_to(selected))
     self.assertTrue(fixture.root.is_dir())
     self.assertNotEqual(fixture.root,selected)
     if isinstance(fixture,DigestFixture):
      self.assertEqual(len(fixture.specs),2)
      self.assertEqual(fixture.prepare()['status'],'ASSEMBLED_NOT_PUBLICATION_BOUND')
     else:
      self.assertEqual(len(fixture.rows),22)
      self.assertEqual(fixture.validate()['profile'],'RUN187_SELECTOR')
    finally:fixture.close()
    self.assertFalse(fixture.root.exists())
 def test_digest_fixture_honors_platform_temp_root(self):self.check_fixture(DigestFixture)
 def test_runtime_fixture_honors_platform_temp_root(self):self.check_fixture(RuntimeFixture)

if __name__=='__main__':unittest.main()
