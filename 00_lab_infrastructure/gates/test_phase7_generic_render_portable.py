"""Isolated public source fixtures; no certification, API, or live admission."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
G=Path(__file__).resolve().parent
F=G/'tests/fixtures/phase7_generic_render_v001'
class GenericRenderPortableTests(unittest.TestCase):
 def test_frozen_render_source_fixtures(self):
  manifest=json.loads((F/'CI_SOURCE_MANIFEST.json').read_bytes())
  with tempfile.TemporaryDirectory(prefix='phase7-render-ci-')as temp:
   out=Path(temp).resolve(strict=True)/'gates';out.mkdir()
   for name,expected in manifest['production'].items():
    source=G/name;self.assertTrue(source.is_file());self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),expected);shutil.copyfile(source,out/name)
   for row in manifest['fixtures']:
    source=F/row['path'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);target=out/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
   for row in manifest['parent_sources']:
    source=F/row['path'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);shutil.copyfile(source,out.parent/row['target'])
   env=dict(os.environ);env.pop('PYTHONPATH',None);env['PYTHONDONTWRITEBYTECODE']='1';env['TMPDIR']=str(out.parent)
   result=subprocess.run([sys.executable,'-B','CI_ISOLATED_RUNNER.py',*manifest['test_modules']],cwd=out,env=env,capture_output=True,text=True,timeout=90)
   self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran '+str(manifest['expected_tests'])+' tests',result.stderr);self.assertIn('OK',result.stderr)
if __name__=='__main__':unittest.main()
