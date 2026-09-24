"""Write a fresh evidence directory; never overwrite saved inputs or an earlier run."""
import argparse,datetime,hashlib,json,platform,subprocess,sys
from pathlib import Path
import numpy,scipy,sympy
from model import benchmark
p=argparse.ArgumentParser(); p.add_argument('--output',type=Path,required=True); args=p.parse_args()
args.output.mkdir(parents=True,exist_ok=False)
out=benchmark()
out['execution']={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'command':sys.argv,'python':sys.version,'platform':platform.platform(),
 'versions':{'numpy':numpy.__version__,'scipy':scipy.__version__,'sympy':sympy.__version__},
 'revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
 'dirty_state':subprocess.check_output(['git','status','--porcelain=v1'],text=True),
 'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}
(args.output/'results.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:out[k] for k in ['stationary','forcing','raw_target','ratio','crossover','schedules']},indent=2))
