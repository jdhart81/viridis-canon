"""Portable frozen caller snapshot; all original assertions run unchanged."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,unittest
GIT_SUBDIR="production_snapshots/phase7-20261008-prospective-catalog-close/after/production_execution_dependencies"
DRIVER_SUBDIR="production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/runtime_successor.py"
class ProspectiveCatalogSnapshotTests(unittest.TestCase):
 def gates(self):return Path(os.environ.get("PHASE7_TEST_GATES",Path(__file__).resolve().parent)).resolve(strict=True)
 def test_frozen_files_exact(self):
  folder=self.gates()/GIT_SUBDIR;v=json.loads((folder/"FREEZE.json").read_bytes())
  self.assertEqual(v["standard"],"VRS-PHASE7-PROSPECTIVE-CATALOG-CLOSE-FREEZE-1");self.assertEqual(v["status"],"FROZEN_REVIEWABLE_NOT_EXECUTED")
  for n,r in v["files"].items():
   b=(folder/n).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),r["sha256"]);self.assertEqual(len(b),r["bytes"])
 def test_all52_frozen_assertions_portable(self):
  gates=self.gates();folder=gates/GIT_SUBDIR;driver=gates/DRIVER_SUBDIR
  code="import sys,unittest;sys.path.insert(0,sys.argv[1]);import prospective_catalog_close as c;from pathlib import Path;c.DRIVER=Path(sys.argv[2]);import test_prospective_catalog_close as t;result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromModule(t));assert result.testsRun==52;sys.exit(0 if result.wasSuccessful() else 1)"
  p=subprocess.run([sys.executable,"-B","-c",code,str(folder),str(driver)],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)
if __name__=="__main__":unittest.main()
