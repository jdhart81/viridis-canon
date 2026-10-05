#!/usr/bin/env python3
"""Restore an exact approved registration set through the preserving consumer.

This command cannot contact Zenodo, issue certificates, invent claim maps or
install runtime files. Applying is an explicit local SSOT write with a recorded
predecessor hash; the fresh scan revalidates every retained registration.
"""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil

from corpus_ledger import (build,preserve_publication_registrations,
                           render_markdown,write_guarded_ledger)
from mirror_parity import GENERATION_ROOT

APPROVED_PROPOSAL_SHA256='72044a08aba24d2c82d0b9fd68cb2198bc0075f6a456a0662a5e0554bed23b62'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recover(root,cert_root,proposal,expected_ledger_sha256,output,readbacks,*,apply=False):
    root=Path(root).resolve(strict=True)
    output=Path(output).resolve()
    canonical=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
    proposal=Path(proposal)
    if proposal.is_symlink() or digest(proposal)!=APPROVED_PROPOSAL_SHA256:
        raise ValueError('exact approved v002 proposal SHA-256 required')
    plan=json.loads(proposal.read_text())
    if Path(plan.get('tree_root','')).resolve()!=root:
        raise ValueError('approved proposal tree root differs')
    entries=plan.get('publication_entities')
    if not isinstance(entries,list) or len(entries)!=27 or any(not isinstance(e,dict) for e in entries):
        raise ValueError('exact 27-entry approved registration proposal required')
    ids=[e.get('id') for e in entries]
    if any(not isinstance(eid,str) or not eid for eid in ids) or len(set(ids))!=27:
        raise ValueError('27 unique explicit registration identities required')
    if canonical.is_symlink() or digest(canonical)!=expected_ledger_sha256:
        raise ValueError('concurrent authoritative ledger differs from recorded predecessor')
    before=canonical.read_bytes()
    current=json.loads(before)
    if Path(current.get('tree_root','')).resolve()!=root:
        raise ValueError('authoritative ledger tree root differs')
    if output.exists():
        raise ValueError('immutable recovery output already exists')
    output.mkdir(parents=True)
    (output/'before_corpus_ledger.json').write_bytes(before)
    shutil.copyfile(proposal,output/'APPROVED_REREGISTRATION_V002.json')
    readbacks=Path(readbacks)
    evidence=json.loads(readbacks.read_text())
    if evidence.get('standard')!='SSOT_PUBLIC_BANNER_READBACK_1' or evidence.get('authenticated_public_readback') is not True:
        raise ValueError('authenticated public banner collection required')
    records=evidence.get('records')
    if not isinstance(records,list) or any(not isinstance(e,dict) for e in records):
        raise ValueError('public banner readback table required')
    joins={e.get('id'):e for e in records}
    if len(joins)!=len(records):
        raise ValueError('duplicate public readback identity')
    releases=deepcopy(entries)
    for entity in releases:
        if not entity.get('doi'):continue
        record=joins.get(entity['id'])
        if not isinstance(record,dict) or record.get('authenticated') is not True or record.get('doi')!=entity['doi']:
            raise ValueError('authenticated exact DOI readback missing')
        source=Path(record['receipt_path'])
        if source.is_symlink() or digest(source)!=record.get('receipt_sha256'):
            raise ValueError('collected public receipt changed')
        dest=output/'public-readbacks'/record['record_id']/'001_GET.json'
        dest.parent.mkdir(parents=True)
        shutil.copyfile(source,dest)
        if not dest.is_relative_to(root):
            raise ValueError('recovery evidence must be saved inside the canonical tree')
        entity['public_uncertified_readback']={
            'authenticated':True,'record_id':record['record_id'],
            'receipt_path':str(dest.relative_to(root)),
            'receipt_sha256':record['receipt_sha256'],
            'response_sha256':record['response_sha256']}
    previous={**current,'publication_entities':releases}
    candidate=preserve_publication_registrations(deepcopy(current),previous)
    retained=candidate.get('publication_entities',[])
    if len(retained)!=27 or {e['id'] for e in retained}!=set(ids):
        raise ValueError('preserving consumer did not retain all 27 identities')
    if any(e.get('certificate_valid') is not True or e.get('publication_binding_status')!='PUBLICATION_BOUND' for e in retained):
        raise ValueError('fresh certificate/manuscript/review validation failed')
    summary=candidate['publication_registration_summary']
    if summary!={'HOLD_NO_CLAIM_MAP':25,'PASS':2}:
        raise ValueError('consumer does not resolve exactly 2 PASS and 25 HOLD_NO_CLAIM_MAP')
    (output/'prepared_corpus_ledger.json').write_text(json.dumps(candidate,sort_keys=True,indent=2,ensure_ascii=False)+'\n')
    result={'standard':'SSOT_REGISTRATION_RECOVERY_1','at_utc':datetime.now(timezone.utc).isoformat(),
            'tree_root':str(root),'proposal_sha256':APPROVED_PROPOSAL_SHA256,
            'before_sha256':expected_ledger_sha256,'registration_count':27,
            'registration_summary':summary,'banner_defects':candidate['publication_registration_defects'],
            'enforcement_acceptable':candidate['publication_registration_enforcement_acceptable'],
            'canonical_modified':False,'zenodo_mutations':False}
    if apply:
        result['after_sha256']=write_guarded_ledger(canonical,candidate,expected_ledger_sha256)
        result['canonical_modified']=True
        fresh=build(root,cert_root,GENERATION_ROOT)
        rows=fresh.get('publication_entities',[])
        result['fresh_scan_count']=len(rows)
        result['fresh_scan_summary']=fresh.get('publication_registration_summary')
        result['fresh_scan_retained_exact_identities']=len(rows)==27 and {e['id'] for e in rows}==set(ids)
        result['fresh_scan_all_manuscript_bindings_valid']=all(e.get('certificate_valid') is True and e.get('publication_binding_status')=='PUBLICATION_BOUND' for e in rows)
        result['fresh_scan_enforcement_acceptable']=fresh.get('publication_registration_enforcement_acceptable')
        (output/'fresh_scan_corpus_ledger.json').write_text(json.dumps(fresh,sort_keys=True,indent=2,ensure_ascii=False)+'\n')
        (output/'LEDGER.md').write_text(render_markdown(fresh))
        result['canonical_readback_sha256']=digest(canonical)
        result['canonical_readback_exact']=result['canonical_readback_sha256']==result['after_sha256']
        result['status']='RESTORED_RETAINED' if (result['fresh_scan_retained_exact_identities']
            and result['fresh_scan_all_manuscript_bindings_valid']
            and result['fresh_scan_summary']==summary and result['canonical_readback_exact']) else 'HOLD_READBACK'
    else:
        result['status']='PREPARED_REPORT_ONLY'
    (output/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--cert-root',type=Path,required=True)
    p.add_argument('--proposal',type=Path,required=True)
    p.add_argument('--expected-ledger-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--readbacks',type=Path,required=True)
    p.add_argument('--apply',action='store_true')
    a=p.parse_args()
    try:
        result=recover(a.root,a.cert_root,a.proposal,a.expected_ledger_sha256,a.output,a.readbacks,apply=a.apply)
    except Exception as exc:
        result={'status':'HOLD','canonical_write_not_assumed':True,'reasons':[type(exc).__name__+': '+str(exc)],'zenodo_mutations':False}
    print(json.dumps(result,sort_keys=True,indent=2))
    return 0 if result['status'] in ('RESTORED_RETAINED','PREPARED_REPORT_ONLY') else 1


if __name__=='__main__':raise SystemExit(main())
