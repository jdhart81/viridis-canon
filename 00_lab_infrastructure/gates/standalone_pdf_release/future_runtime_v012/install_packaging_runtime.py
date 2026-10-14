"""Additive exact-source installation after genuine merge and root review.

Default mode only checks the plan. --go copies already merged reviewed modules,
preserves the exact historical publisher and frozen v001-v008 installs, and
nominates the explicit default dispatcher. No policy snapshot, ledger, science
certificate, automation, account or Zenodo record is changed here.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import packaging_runtime as runtime

ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
ORIGINAL_PUBLISHER_SHA='4f099eaffb9a35fbd24e5c57ef34801391fabcd5c3272b58a379d7ac52b35e94'
PLAN_FIELDS={'standard','status','canonical_root','source_modules','source_origin','source_review',
             'user_authority','access_registry','historical_publisher','installed_at_utc','root_review','predecessor_installation','transient_rehydration','data_alias_observation','platform_timezone_observation'}
REVIEW_FIELDS=runtime.ROOT_REVIEW_FIELDS


def encoded(v):return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n'


def preflight(root,plan_binding):
    root=Path(root).resolve(strict=True);runtime.need(root==ROOT.resolve(strict=True),'INSTALL_CANONICAL_ROOT')
    _,raw,plan=runtime.object_at(root,plan_binding)
    runtime.need(set(plan)==PLAN_FIELDS and plan['standard']=='VRS-EXACT-ADDITIVE-PDF-RUNTIME-INSTALL-PLAN-12'
                 and plan['status']=='ROOT_REVIEWED_READY_NOT_INSTALLED'and plan['canonical_root']==str(root), 'CLOSED_INSTALL_PLAN')
    pins=runtime.module_table(root,plan['source_modules'])
    installers=[r for r in pins if r['name']=='install_packaging_runtime.py']
    runtime.need(len(installers)==1 and Path(installers[0]['path']).resolve(strict=True)==Path(__file__).resolve(strict=True)
                 and installers[0]['sha256']==runtime.sha(Path(__file__).read_bytes()),'EXACT_EXECUTED_INSTALLER_SOURCE')
    proof=runtime.source_proof(root,plan['source_origin'],plan['source_modules'])
    source_review=runtime.object_at(root,plan['source_review'])[2]
    hashes={r['name']:r['sha256']for r in plan['source_modules']}
    runtime.require_source_review(source_review, hashes, runtime.LEGACY_CLOSURE)
    review=runtime.object_at(root,plan['root_review'])[2]
    runtime.need(set(review)==REVIEW_FIELDS and review['standard']=='VRS-ROOT-EXACT-PDF-RUNTIME-INSTALL-REVIEW-12'
                 and review['status']=='EXACT_MERGED_SOURCE_AND_INSTALL_PLAN_REVIEW_PASS'
                 and isinstance(review['reviewer'],str)and review['reviewer']
                 and review['plan_projection_sha256']==runtime.sha(encoded({k:v for k,v in plan.items()if k!='root_review'})) and review['merged_source_commit']==proof['merge_commit']
                 and review['source_hashes']==hashes and review['historical_publisher_sha256']==ORIGINAL_PUBLISHER_SHA
                 and all(review.get(k) is v for k,v in runtime.SOURCE_REVIEW_CHANGE_FLAGS.items()),'ACTUAL_ROOT_INSTALL_REVIEW')
    runtime.need(plan['predecessor_installation']==runtime.PREDECESSOR_INSTALLATION
                 and plan['transient_rehydration']==runtime.TRANSIENT_REHYDRATION_POLICY,
                 'EXACT_PREDECESSOR_AND_TRANSIENT_POLICY')
    predecessor=runtime.predecessor_installation(root)
    runtime.require_data_alias_observation(root,plan['data_alias_observation'])
    runtime.require_platform_timezone_observation(root,plan['platform_timezone_observation'])
    preserved=plan['historical_publisher']
    runtime.need(runtime.same_binding(root,preserved,runtime.HISTORICAL_PUBLISHER),
                 'EXACT_PRESERVED_HISTORICAL_PUBLISHER')
    publisher,before=runtime.read(root,preserved)
    runtime.need(runtime.sha(before)==ORIGINAL_PUBLISHER_SHA,'KNOWN_EXACT_HISTORICAL_PUBLISHER')
    scope=runtime.object_at(root,runtime.LEGACY_SCOPE)[2]
    origin=scope['source_origin'];proof_rows=origin['source_rows']
    runtime.need(len(proof_rows)==130,'COMPLETE_ORIGINAL130_PREFLIGHT')
    old_origin={'pull_request':origin['merged_pr'],'merge_commit':origin['merged_commit'],'tree':origin['merged_tree']}
    runtime.source_proof(root,old_origin,proof_rows,
                        required_checks=runtime.REQUIRED_CHECKS-{'standalone-manuscript-pdf'})
    transients=runtime.legacy_transient_precheck(root,old_origin,require_present=False)
    # Preflight also proves original fixed anchors and authority inputs, without
    # loading executable legacy or new sources and without claiming live PASS.
    for anchor in (runtime.LEGACY_CLOSURE,runtime.LEGACY_CONSUMER,runtime.LEGACY_SCOPE,runtime.SESSION_CONSUMER):runtime.read(root,anchor)
    authority=runtime.object_at(root,plan['user_authority'])[2]
    installed=runtime.dt.datetime.fromisoformat(plan['installed_at_utc'].replace('Z','+00:00'))
    captured=runtime.dt.datetime.fromisoformat(authority['captured_at_utc'].replace('Z','+00:00'))
    runtime.need(installed.tzinfo is not None and captured.tzinfo is not None
                 and captured<=installed<=runtime.dt.datetime.now(runtime.dt.timezone.utc),'INSTALL_PREFLIGHT_TIME')
    runtime.need(set(authority)=={'standard','source','user_text','captured_at_utc','scientific_scope_changes','provider_instruction'}
                 and authority['standard']=='VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1'
                 and authority['source']=='Current user message in this Codex chat'
                 and authority.get('user_text')==runtime.USER_DIRECTIVE and authority.get('scientific_scope_changes')is False,'INSTALL_PACKAGING_AUTHORITY')
    provider=runtime.read(root,authority['provider_instruction'])[1]
    runtime.need(runtime.sha(provider)==runtime.PROVIDER_SHA,'INSTALL_ACTUAL_USER_PROVIDER')
    runtime.read(root,plan['access_registry'])
    target=root/runtime.PROFILE_PATH;runtime.need(not target.parent.exists(),'NO_REPLACE_OR_DUPLICATE_INSTALL')
    runtime.need(runtime.read(root,plan_binding)[1]==raw and publisher.read_bytes()==before,'INSTALL_PREFLIGHT_RACE')
    return plan,proof,pins,before,predecessor,transients


def exclusive(path,raw):
    path=Path(path);runtime.need(not path.exists()and not any(p.is_symlink()for p in (path,*path.parents)),'EXCLUSIVE_INSTALL_OUTPUT')
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    runtime.need(path.read_bytes()==raw,'INSTALL_BYTE_READBACK')


def install(root,plan_binding,*,go=False):
    plan,proof,pins,before,predecessor,transients=preflight(root,plan_binding)
    if not go:return {'status':'ACTUAL_MERGED_SOURCE_INSTALL_PREFLIGHT_PASS_NOT_INSTALLED','source_hashes':{r['name']:r['sha256']for r in pins},'certifies':False,'writes':0}
    root=Path(root).resolve(strict=True);target=root/runtime.PROFILE_PATH;target.parent.mkdir(exist_ok=False)
    exclusive(target.parent/'INSTALL_PLAN.json',runtime.read(root,plan_binding)[1])
    installed=[]
    try:
        for row in plan['source_modules']:
            data=runtime.read(root,{'path':row['path'],'sha256':row['sha256']})[1]
            dest=target.parent/row['name'];exclusive(dest,data)
            installed.append({**row,'path':str(dest)})
        publisher=root/'_ZENODO_DEPOSITS/publish_dated_bundles.py'
        runtime.need(publisher.read_bytes()==before,'HISTORICAL_PUBLISHER_FINAL_PRESERVATION')
        exclusive(target.parent/'PUBLISHER_UNCHANGED_BEFORE_INSTALL.py',before)
        scope=runtime.object_at(root,runtime.LEGACY_SCOPE)[2];origin=scope['source_origin']
        recovered=runtime.legacy_transient_precheck(root,
            {'pull_request':origin['merged_pr'],'merge_commit':origin['merged_commit'],'tree':origin['merged_tree']},
            restore=True)
        profile={'standard':runtime.STANDARD,'status':runtime.STATUS,'canonical_root':str(root),
                 'installed_at_utc':plan['installed_at_utc'],'user_authority':plan['user_authority'],
                 'legacy_closure':runtime.LEGACY_CLOSURE,'legacy_consumer':runtime.LEGACY_CONSUMER,
                 'legacy_scope':runtime.LEGACY_SCOPE,'source_session_consumer':runtime.SESSION_CONSUMER,
                 'modules':installed,'source_origin':plan['source_origin'],'source_review':plan['source_review'],
                 'access_registry':plan['access_registry'],'default_routes':runtime.DEFAULT_ROUTES,
                 'predecessor_installation':plan['predecessor_installation'],
                 'transient_rehydration':plan['transient_rehydration'],
                 'data_alias_observation':plan['data_alias_observation'],
                 'platform_timezone_observation':plan['platform_timezone_observation']}
        exclusive(target,encoded(profile));profile_binding={'path':str(target),'sha256':runtime.sha(target.read_bytes())}
        nomination={'standard':'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-12',
                    'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
                    'profile':profile_binding,'installer_source':{'path':str(Path(__file__).resolve()),'sha256':runtime.sha(Path(__file__).read_bytes())},
                    'merged_source_commit':proof['merge_commit'],'root_review_receipt':plan['root_review']}
        exclusive(root/runtime.NOMINATION_PATH,encoded(nomination))
        # Caller must enter the installed source scope, then freshly validate
        # scientific/registry/default dispatch readbacks. Installation alone is
        # not a scientific or production-readback verdict.
        result={'status':'EXACT_SOURCE_COPIED_AND_DEFAULT_NOMINATED_AWAITING_FRESH_RUNTIME_READBACK',
                'profile':profile_binding,'modules':installed,'historical_publisher_preserved_sha256':ORIGINAL_PUBLISHER_SHA,
                'predecessor_installation':predecessor,'transient_source_readback':recovered,
                'default_routes':runtime.DEFAULT_ROUTES,'merged_source_commit':proof['merge_commit'],
                'ssot_writes':0,'zenodo_writes':0,'certifies':False}
        runtime.need(publisher.read_bytes()==before,'HISTORICAL_PUBLISHER_EXIT_PRESERVATION')
        runtime.predecessor_installation(root)
        exclusive(target.parent/'INSTALL_RESULT_PENDING_READBACK.json',encoded(result));return result
    except Exception as exc:
        exclusive(target.parent/'INSTALL_HOLD.json',encoded({'status':'HOLD_PARTIAL_INSTALL_NOT_ADMISSION','error_type':type(exc).__name__,
                    'error':str(exc),'installed_modules':installed,'automatic_retry':False,'certifies':False}));raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--expected-plan-sha256',required=True);p.add_argument('--go',action='store_true');a=p.parse_args()
    result=install(ROOT,{'path':str(a.plan.resolve(strict=True)),'sha256':a.expected_plan_sha256},go=a.go)
    print(json.dumps(result,sort_keys=True,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
