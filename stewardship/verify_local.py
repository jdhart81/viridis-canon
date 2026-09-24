"""One-command local verification. New evidence directory, explicit commands/exit codes.
Does not verify the missing archive, push, publish, or invoke paid proof tools.
"""
import argparse,datetime,hashlib,json,os,platform,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
py=ROOT/'.venv-stewardship/bin/python'
commands=[]
def run(name,argv,cwd=ROOT):
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (out/(name+'.log')).open('w') as log:
        result=subprocess.run([str(v) for v in argv],cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
    commands.append({'name':name,'argv':[str(v) for v in argv],'cwd':str(cwd),'utc':started,'exit_code':result.returncode})
    print(name+': '+('PASS' if result.returncode==0 else 'FAIL'),flush=True)
    return result.returncode==0
if not py.exists():
    if not run('venv',[sys.executable,'-m','venv',ROOT/'.venv-stewardship']): raise SystemExit(1)
if not run('dependencies',[py,'-m','pip','install','-r','stewardship/requirements.txt']): raise SystemExit(1)
run('python-version',[py,'--version']); run('lean-version',['lake','--version'])
run('numerical-tests',[py,'-m','unittest','discover','-s','stewardship','-p','test_model.py','-v'])
run('benchmark',[py,'stewardship/run.py','--output',out/'benchmark'])
run('spine-hygiene',['bash','tools/check_spine_hygiene.sh','.'])
run('candidate-vacuity',[sys.executable,'tools/vacuity_lint.py','InformationWeightedStewardship.lean',*sorted(ROOT.glob('InformationWeightedStewardship/*.lean'))])
run('deposit-manifest',['bash','tools/check_deposit_manifest.sh','.'])
run('current-cache',['lake','exe','cache','get'])
run('current-build',['lake','build'])
run('candidate-build',['lake','build','InformationWeightedStewardship','InformationWeightedStewardshipAudit'])
run('deposit-build',['lake','build','DepositAudit'])
run('p0-version',['lake','--version'],ROOT/'compat/v4_24')
run('p0-cache',['lake','exe','cache','get'],ROOT/'compat/v4_24')
run('p0-build',['lake','build'],ROOT/'compat/v4_24')
run('repository-tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
run('catalog',[sys.executable,'tools/build_research_portal.py','--check'])
run('diff-whitespace',['git','diff','--check'])
# Compiler-level gate and positive audit receipts, also when Lake replays cached output.
checks={}
for name,receipt in [('current-build','Axiom audit PASSED'),('candidate-build','Information-weighted stewardship axiom audit PASSED'),('deposit-build','Deposit axiom audit PASSED'),('p0-build','P0 axiom audit PASSED')]:
    text=(out/(name+'.log')).read_text()
    checks[name]={'audit_receipt_present':receipt in text,'no_proof_hole_output':"declaration uses 'sorry'" not in text and 'sorryAx' not in text}
source_paths=[ROOT/'lakefile.toml',ROOT/'lake-manifest.json',ROOT/'lean-toolchain',ROOT/'StewardshipSetpoint.lean',ROOT/'ThermodynamicAttention.lean',ROOT/'InformationWeightedStewardship.lean',ROOT/'InformationWeightedStewardshipAudit.lean',ROOT/'compat/v4_24/lean-toolchain',ROOT/'compat/v4_24/lake-manifest.json',ROOT/'stewardship/requirements.txt',ROOT/'os/functions/stewardship-setpoint-direction/function.json',ROOT/'os/functions/thermodynamic-attention-waterfill/function.json',*ROOT.glob('InformationWeightedStewardship/*.lean'),*Path(__file__).parent.glob('*.py')]
summary={'evidence_class':'local compiled/symbolic/numerical checks; not independent peer review, empirical evidence or supplied-package reproduction','platform':platform.platform(),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'commands':commands,'audit_checks':checks,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source_paths},'supplied_package_status':'NOT_LOCATED; hash/manifest/spec and original reproduction pending','checks_passed':all(c['exit_code']==0 for c in commands) and all(all(v.values()) for v in checks.values()),'milestone_complete':False}
(out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
raise SystemExit(0 if summary['checks_passed'] else 1)
