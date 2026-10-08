"""Flat-G root configuration fixture CI, clean subprocess and no R/API reads."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
G=Path(__file__).resolve().parent
F=G/'tests/fixtures/phase7_generic_root_configuration_v002'
class RootConfigurationPortableTests(unittest.TestCase):
 def test_repo_only_root_configuration_merge_reference_copy_27_source_fixture(self):
  manifest=json.loads((F/'CI_SOURCE_MANIFEST.json').read_bytes())
  with tempfile.TemporaryDirectory(prefix='phase7-root-config-ci-')as temp:
   out=Path(temp).resolve(strict=True)
   for row in manifest['source_rows']:
    source=G.parents[1]/row['from'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);p=out/row['to'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,p)
   for row in manifest['fixtures']:
    source=F/row['path'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);shutil.copyfile(source,out/row['path'])
   result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(out),'-p','test*.py'],cwd=out,capture_output=True,text=True,timeout=90)
   self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 32 tests',result.stderr);self.assertIn('OK',result.stderr)
if __name__=='__main__':unittest.main()
