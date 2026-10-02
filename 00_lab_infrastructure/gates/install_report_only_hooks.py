#!/usr/bin/env python3
"""Install the reviewed local report-only adapters; never invoke a publisher."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def install(root):
    root=Path(root).resolve();base=Path(__file__).resolve().parent
    snapshots=base/'production_snapshots';manifest=json.loads((snapshots/'MANIFEST.json').read_text())
    planned=[]
    for row in manifest['snapshots']:
        target=Path(row['production_path'])
        if not target.resolve().is_relative_to(root):raise ValueError('snapshot outside installation root')
        expected=row['sha256'];prepared=snapshots/row['installed_path']
        if sha(snapshots/row['before_path'])!=expected or sha(prepared)!=row['installed_sha256']:
            raise ValueError('reviewed snapshot hash changed')
        actual=sha(target)
        if actual not in (expected,row['installed_sha256'],row.get('previous_installed_sha256')):raise ValueError('production script changed since snapshot: '+str(target))
        planned.append((target,prepared.read_bytes(),actual,row['installed_sha256']))
    runtime=root/'RESEARCH_PIPELINE_v2/verification_coverage_gates'
    for source in sorted(base.glob('*.py')):
        if source.name.startswith('test') or source.name=='install_report_only_hooks.py':continue
        target=runtime/source.name
        if target.is_symlink():raise ValueError('runtime symlink refused')
        planned.append((target,source.read_bytes(),sha(target) if target.is_file() else None,sha(source)))
    for target,data,before,after in planned:
        target.parent.mkdir(parents=True,exist_ok=True)
        # Refuse concurrent edits between inventory and replacement.
        actual=sha(target) if target.is_file() else None
        if actual!=before:raise ValueError('concurrent installation drift: '+str(target))
        if actual==after:continue
        with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as stream:
            stream.write(data);temp=Path(stream.name)
        if target.is_file():os.chmod(temp,target.stat().st_mode & 0o777)
        os.replace(temp,target)
    receipt={'mode':'REPORT_ONLY','enforcement':False,'installed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
             'root':str(root),'zenodo_writes':False,'generation_root_changed':False,
             'files':[{'path':str(t),'before_sha256':b,'installed_sha256':a} for t,_,b,a in planned]}
    out=root/'reports/verification-coverage/HOOK_INSTALLATION.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--report-only',action='store_true',required=True);a=p.parse_args()
    receipt=install(a.root);print(json.dumps({'mode':receipt['mode'],'files':len(receipt['files']),'enforcement':False,'receipt':str(a.root/'reports/verification-coverage/HOOK_INSTALLATION.json')}))

if __name__=='__main__':main()
