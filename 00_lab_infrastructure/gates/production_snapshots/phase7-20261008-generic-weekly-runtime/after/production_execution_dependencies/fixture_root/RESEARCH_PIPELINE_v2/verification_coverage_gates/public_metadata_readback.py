#!/usr/bin/env python3
"""Anonymous GET-only public readback. No token, draft API, upload or publication."""

import methods_digest_registration
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request
import re


def _read_record_legacy(row):
    doi=row['doi']; result={'doi':doi,'status':'UNAVAILABLE','proposed_label':'CONJECTURE — not machine-verified',
        'observed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'local_manuscript_public_checksum_matches':[]}
    try:
        match=re.fullmatch(r'10\.5281/zenodo\.(\d+)',doi)
        if not match:raise ValueError('unsupported record identity')
        url='https://zenodo.org/api/records/'+match[1]
        req=urllib.request.Request(url,headers={'User-Agent':'Viridis report-only verification-coverage audit','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=30) as response: record=json.load(response)
        if record.get('doi') != doi:raise ValueError('public record DOI mismatch')
        meta=record['metadata'];files=record.get('files',[])
        public_files=[{'name':f.get('key',f.get('filename')),'checksum':f.get('checksum'),'size':f.get('size')} for f in files]
        for deposit in row['deposit_paths']:
            p=Path(deposit)
            for local in sorted(p.glob('*')):
                if local.suffix not in ('.tex','.pdf') or not local.is_file():continue
                data=local.read_bytes();md5=hashlib.md5(data).hexdigest()
                matches=[f for f in public_files if f['checksum']=='md5:'+md5]
                result['local_manuscript_public_checksum_matches'].append({'path':str(local),
                    'sha256':hashlib.sha256(data).hexdigest(),'matches_public_files':matches,'confirmed':bool(matches)})
        description=str(meta.get('description',''));verification_status=meta.get('verification_status')
        banner_present='CONJECTURE — not machine-verified' in description or 'CONJECTURE — not machine-verified' in str(meta.get('title'))
        result.update(status='READ',url=url,title=meta.get('title'),description=description,
                      public_verification_status=verification_status,files=public_files,
                      proposed_label_disagrees=not banner_present or verification_status=='CERTIFIED',
                      reason='Required conjecture banner absent from current public metadata' if not banner_present else 'Conjecture banner present')
    except Exception as exc:result['error']=type(exc).__name__+': '+str(exc)
    return result


def read_record(row):
    return methods_digest_registration.public_label_read_record(row, legacy=_read_record_legacy)


def _readback_legacy(audit):
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(read_record,audit['published_records']))
    return {'mode':'REPORT_ONLY','method':'Anonymous HTTPS GET /api/records/{id} only','zenodo_writes':False,
            'counts':{'records':len(rows),'read':sum(r['status']=='READ' for r in rows),
                      'unavailable':sum(r['status']!='READ' for r in rows),
                      'label_disagreements':sum(r.get('proposed_label_disagrees',False) for r in rows),
                      'locally_deposited_manuscripts_confirmed_public':sum(any(m['confirmed'] for m in r['local_manuscript_public_checksum_matches']) for r in rows)},'records':rows}


def readback(audit):
    return methods_digest_registration.public_label_readback(audit, legacy=_readback_legacy)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=readback(json.loads(a.audit.read_text()));a.out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n');print(json.dumps(report['counts']))

if __name__=='__main__':main()
