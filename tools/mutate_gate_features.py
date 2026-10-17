"""Exercise twenty documented archive/readback feature mutations on current code.

This is a current-code port of the independent review's listed feature classes;
it does not claim possession of the reviewer's absent scratchpad script.
No syntax/import error is credited as a kill. All inputs remain disposable.
"""
import argparse,ast,hashlib,json,os,subprocess,sys,tempfile,time
from pathlib import Path
MUTANTS={
'N01 extra public files':('or set(names) != set(approved_names)','or not set(approved_names).issubset(set(names))'),
'N02 nested archives':('nested.extend(scan(content, name, depth + 1, prefix + name + "!"))','pass'),
'N03 swallowed parse errors':('raise ManuscriptPDFHold("invalid or uninspectable reproduction archive") from exc','return'),
'N04 depth limit':('if depth > MAX_ARCHIVE_DEPTH:','if False:'),
'N05 expansion bound':('if len(data) > limit:','if False:'),
'N06 shared total limit':('if self.expanded_bytes > MAX_ARCHIVE_BYTES:','if False:'),
'N07 magic bytes beyond suffix':('if _archive_kind(upload_bytes[path.name]) is None and not path.name.lower().endswith(ARCHIVE_SUFFIXES):','if not path.name.lower().endswith(ARCHIVE_SUFFIXES):'),
'N08 compressed PDF':('return [(prefix + name, decoded)] if _archived_manuscript(name) else []','return []'),
'N09 role JSON shape':('if not isinstance(roles, dict) or roles.get("standard") != STANDARD or not isinstance(roles.get("manuscripts"), list):','if False:'),
'N10 long Run identity':('re.fullmatch(r"Run-[0-9]{3,}", run)','re.fullmatch(r"Run-[0-9]{3}", run)'),
'N11 archive download hashes':('if _hashes(data) != {k: expected[k] for k in ("sha256", "md5", "bytes")}:','if False:'),
'N12 ZIP symlink type':('if stat.S_IFMT(mode) not in {0, stat.S_IFREG}:','if False:'),
'N13 duplicate public names':('or len(set(names)) != len(names):','or False:'),
'N14 ZIP preamble':('if zipfile.is_zipfile(BytesIO(raw)):','if False:'),
'N15 unsupported archive':('if kind is None or kind == "unsupported":','if kind == "unsupported":\n            return []\n        if kind is None:'),
'N16 V7 TAR':('if len(raw) >= 512 and re.fullmatch(rb"[0-7\\x00 ]{8}", raw[148:156]):','if False:'),
'N17 source render coverage':('if str(PurePosixPath(name.lower()).with_suffix(".pdf")) not in pdf_names:','if False:'),
'N18 decoded layer budget':('decoded = _decompress(data, kind)\n            budget.member(len(decoded))','decoded = _decompress(data, kind)\n            pass'),
'N19 digest JSON shape':('if not isinstance(manifest, dict):','if False:'),
'N20 declared size limit':('if not 0 <= size <= MAX_MEMBER_BYTES:','if False:'),
}
def classify_test_run(returncode, counts, *, baseline=False):
 """Use TestResult counts and exception types, never traceback word searches."""
 keys={'tests_run','failures','errors','infrastructure_errors'}
 if not isinstance(counts,dict)or set(counts)!=keys or any(type(v)is not int or v<0 for v in counts.values()):
  return {'result':'BASELINE_FAILURE'if baseline else'INVALID_TEST_ERROR'}
 tests,failures,errors,invalid=(counts[k]for k in('tests_run','failures','errors','infrastructure_errors'))
 if invalid>errors or not tests or (returncode==0 and failures+errors):return {'result':'BASELINE_FAILURE'if baseline else'INVALID_TEST_ERROR'}
 if baseline:result='PASS'if returncode==0 and tests else'BASELINE_FAILURE'
 elif returncode==0:result='SURVIVED'
 elif tests and failures+errors-invalid:result='KILLED'
 else:result='INVALID_TEST_ERROR'
 return {'result':result,**counts}

TEST_RUNNER='''import json,unittest
class Counts(unittest.TextTestResult):
 def __init__(self,*a,**k):super().__init__(*a,**k);self.infrastructure_errors=0
 def addError(self,test,error):
  if issubclass(error[0],(ImportError,SyntaxError)) or type(test).__name__=="_FailedTest":self.infrastructure_errors+=1
  super().addError(test,error)
result=unittest.TextTestRunner(resultclass=Counts).run(unittest.defaultTestLoader.discover("tests",pattern="test_gate_hardening.py"))
print("VRS_MUTATION_TEST_COUNTS:"+json.dumps(dict(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),infrastructure_errors=result.infrastructure_errors)))
raise SystemExit(not result.wasSuccessful())
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();source=a.source.resolve();original=(source/'manuscript_pdf_gate.py').read_text();tests=(source/'tests/test_gate_hardening.py').read_bytes();rows=[];started=time.monotonic();baseline=None
 for name,change in [('BASELINE',None),*MUTANTS.items()]:
  modified=original
  if change:
   old,new=change
   if original.count(old)!=1:rows.append({'mutant':name,'result':'INVALID_PATTERN','count':original.count(old)});continue
   modified=original.replace(old,new)
  ast.parse(modified)
  with tempfile.TemporaryDirectory(prefix='viridis-feature-mutant-')as temp:
   root=Path(temp);(root/'tests').mkdir();(root/'manuscript_pdf_gate.py').write_text(modified);(root/'tests/test_gate_hardening.py').write_bytes(tests)
   run=subprocess.run([sys.executable,'-c',TEST_RUNNER],cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=30)
  metrics=[line.removeprefix('VRS_MUTATION_TEST_COUNTS:')for line in run.stdout.splitlines()if line.startswith('VRS_MUTATION_TEST_COUNTS:')]
  try:counts=json.loads(metrics[0])if len(metrics)==1 else None
  except ValueError:counts=None
  classification=classify_test_run(run.returncode,counts,baseline=change is None)
  row={'mutant':name,**classification,'exit_code':run.returncode,'stderr_sha256':hashlib.sha256(run.stderr.encode()).hexdigest()}
  if change:rows.append(row)
  else:baseline=row
 receipt={'status':'PASS'if baseline['result']=='PASS'and sum(x['result']=='KILLED'for x in rows)>=19 and len(rows)==20 else'HOLD','baseline':baseline,'mutants':rows,'killed':sum(x['result']=='KILLED'for x in rows),'declared_mutants':20,'gate_sha256':hashlib.sha256(original.encode()).hexdigest(),'elapsed_seconds':round(time.monotonic()-started,3),'lineage':'current-code port of documented independent feature classes; original scratchpad script unavailable'}
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.open('x')as out:out.write(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:receipt[k]for k in ('status','killed','declared_mutants','elapsed_seconds')}));return int(receipt['status']!='PASS')
if __name__=='__main__':raise SystemExit(main())
