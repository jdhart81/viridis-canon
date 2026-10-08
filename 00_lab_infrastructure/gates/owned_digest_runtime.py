"""Actual source-purpose adapter; never accepts a prepared PASS marker.

The root calls this only inside the unchanged measured source-session loader.
It replays current activation, complete default SSOT consumers, package, Git
origin, private readback helper pins and actual preserving mutation budget.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib, importlib, json, re, sys, types, urllib.request
from pathlib import Path
import owned_digest_executor as e
import methods_digest as d
import phase7_audit_policy as policy
import phase7_mutation_baseline as mutations
import corpus_ledger as corpus
import methods_digest_registration as registrar
import zenodo_transport as transport
import server_managed_fields as sm
from first_digest_publisher import PacedOpener
from owned_digest_boundary import OwnedDigestBoundary
from runtime_closure_view import require_current
from owned_successor_archive_wait import OwnedSuccessorArchiveWait

UNCHANGED={'methods_digest.py':'5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5','methods_digest_registration.py':'0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9','zenodo_transport.py':'69bcfa0c7008f052a0c30d06d23e94a226c5b40707905550e41c40e16c379b65','server_managed_fields.py':'ce8ad2002a11938966201a44d2714ee866bb922649cd572e36f09e8cc0f062a1','publication_preservation.py':'4fb48f40fd76cae1f973dca66253813bfd1c8edcdffa07c02945d28ddf170e2b','file_byte_metadata.py':'4a21de5efd74531b135682f92ce4d49b1d8ad71d044795548ea9877756fa50ef','mutation_journal_writer.py':'a2a72c49b5bc67a5c7535320bab5b6513b8cbfac3cf6c19d39b2e0c3d5d5c4e8'}
CHECKS={'gitleaks','report-only-consumers','verify-catalog','verify','verify-functions','lean-build-current','lean-build-p0','deposit-verify'}
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def load_bound_module(root,binding,name):
    p,_=e.source(root,binding);m=types.ModuleType(name);m.__file__=str(p);exec(compile(e.raw(p),str(p),'exec'),m.__dict__);e.need(e.sha(p)==binding['sha256'],'REVIEWED_CONSUMER_RACE');return m
def require_origin(root,binding,pins):
    _,proof=e.bound(root,binding)
    e.need(set(proof)=={'standard','status','merged_pr','merged_commit','merged_tree','source_rows'}and proof['standard']=='VRS-OWNED-DIGEST-MERGED-PURPOSE-SOURCE-1'and proof['status']=='EXACT_MERGED_BLOBS_NOT_PUBLICATION_CLEARANCE','CLOSED_MERGED_SOURCE_PROOF')
    _,pr=e.bound(root,proof['merged_pr']);_,commit=e.bound(root,proof['merged_commit']);_,tree=e.bound(root,proof['merged_tree'])
    e.need(pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr.get('number'))and re.fullmatch('[0-9a-f]{40}',str(pr.get('headRefOid')))is not None and pr.get('mergeCommit',{}).get('oid')==commit.get('sha')and commit.get('tree',{}).get('sha')==tree.get('sha')and tree.get('truncated')is False,'OWN_REAL_MERGE_TREE')
    checks=pr.get('statusCheckRollup');e.need(isinstance(checks,list)and CHECKS<={x.get('name')for x in checks if x.get('status')=='COMPLETED'and x.get('conclusion')=='SUCCESS'}and all(x.get('status')=='COMPLETED'and x.get('conclusion')in{'SUCCESS','SKIPPED'}for x in checks),'REAL_EXACT_HEAD_CHECKS')
    nodes=tree.get('tree');e.need(isinstance(nodes,list)and all(isinstance(x,dict)for x in nodes),'COMPLETE_TREE');mapping={x['path']:x for x in nodes};e.need(len(mapping)==len(nodes),'UNIQUE_TREE_PATHS')
    rows=proof['source_rows'];e.need(isinstance(rows,list)and len(rows)==len(pins),'ALL_PURPOSE_SOURCES_HAVE_GIT_ORIGIN')
    by_name={x['name']:x for x in rows};e.need(len(by_name)==len(rows)and set(by_name)=={x['name']for x in pins},'EXACT_SOURCE_ORIGIN_TABLE')
    for pin in pins:
        row=by_name[pin['name']];e.need(set(row)=={'name','path','sha256','git_path','git_blob_sha'}and {k:row[k]for k in('name','path','sha256')}==pin,'EXACT_PURPOSE_ORIGIN_ROW');raw=e.raw(Path(row['path']));node=mapping.get(row['git_path'],{});e.need(hashlib.sha256(raw).hexdigest()==row['sha256']and blob(raw)==row['git_blob_sha']==node.get('sha')and node.get('type')=='blob'and node.get('mode')in{'100644','100755'},'OWN_MERGED_BLOB_BYTES')
    return proof

class ActualRuntime:
    def __init__(self,root,plan):
        self.root=Path(root).resolve(strict=True);self.plan=plan;self.d=d;self.opener=None;self.token=None
    def admission(self,plan,package):
        e.need(plan==self.plan,'ONE_ACTUAL_PLAN');e.require_plan(self.root,plan);require_origin(self.root,plan['source_origin'],plan['purpose_source_pins'])
        current=load_bound_module(self.root,plan['runtime_consumer'],'owned_current_runtime_consumer');closure=require_current(current,plan['current_runtime_closure'],root=self.root,purpose_pins=plan['purpose_source_pins'],bound=e.bound)
        table={p['name']:p for p in plan['purpose_source_pins']}
        e.need(all(table.get(p['name'])==p for p in closure['source_pins']),'ACTUAL_RUNTIME_SUBSET_OF_PURPOSE')
        builder=load_bound_module(self.root,plan['source_session_consumer'],'owned_unchanged_source_session');e.need(closure['source_session']['sha256']==plan['source_session_consumer']['sha256'],'EXACT_SOURCE_SESSION')
        builder.verify_loaded(plan['purpose_source_pins'],self.root)
        for name,expected in UNCHANGED.items():e.need(table.get(name,{}).get('sha256')==expected,'UNCHANGED_ACCEPTANCE_OR_TRANSPORT:'+name)
        ledger_path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before=e.raw(ledger_path);ledger=json.loads(before);e.need(ledger.get('enforcement_activation')==closure['activation'],'CURRENT_NOMINATION')
        # Fresh ordinary build delegates every registration to the unchanged
        # current preserving consumer; derived status dictionaries do not pass.
        scanned=corpus.build(self.root,self.root/'RESEARCH_PIPELINE_v2/lean_certificates',previous_ledger=ledger)
        rows=ledger.get('publication_entities');actual=scanned.get('publication_entities');e.need(isinstance(rows,list)and actual==rows and len({x.get('id')for x in rows})==len(rows)and all(x.get('enforcement_acceptable')is True for x in actual),'FRESH_COMPLETE_DEFAULT_SSOT_SCAN')
        predecessor=registrar.require_registration(self.root,plan['predecessor_registration'],ledger)
        e.need(predecessor['receipt']['record_id']==plan['predecessor_record_id']and (predecessor['receipt']['release_week']==plan['release_week']if plan['start_kind']=='NEW_VERSION'else predecessor['receipt']['release_week']!=plan['release_week'])and [x['run_id']for x in predecessor['receipt']['children']]==plan['prior_run_ids'],'ACTUAL_SAME_WEEK_PREDECESSOR_DEFAULT_READER')
        recovery_path,recovery=e.bound(self.root,plan['registration_recovery']);e.need(recovery.get('status')=='EXPLICIT_DEFAULT_READER8_FRESH35_CAS_READBACK_PASS'and recovery.get('unchanged_registrar_sha256')==UNCHANGED['methods_digest_registration.py']and recovery.get('all27_predecessor_rows_exact')is True and recovery.get('all8_actual_reader_rows')is True and recovery.get('all35_fresh_scan_and_replay_acceptable')is True and recovery.get('certifies')is False,'REAL_HISTORICAL35_RECOVERY')
        manifest,pub=d.require_publication_bound(package,self.root);e.need([x['run_id']for x in manifest['notes']]==plan['new_run_ids']and manifest['release_week']==plan['release_week'],'ACTUAL_CURRENT_MINIMAL_GATES')
        _,discovery=e.bound(self.root,plan['account_discovery']);e.need(discovery.get('standard')=='VRS-OWNED-WEEKLY-DISCOVERY-1'and discovery.get('release_week')==plan['release_week']and discovery.get('start_kind')==plan['start_kind']and discovery.get('concept_id')==plan['expected_concept_id']and discovery.get('record_id')==(plan['predecessor_record_id']if plan['start_kind']=='NEW_VERSION'else None),'ACTUAL_ACCOUNT_DISCOVERY_INPUT')
        # This routine is a real source-bound receipt consumer, not a caller's
        # complete=True/marker list. It recomputes the preserved weekly chain.
        import owned_weekly_discovery
        owned_weekly_discovery.require_discovery(discovery,root=self.root)
        require_current(current,plan['current_runtime_closure'],root=self.root,purpose_pins=plan['purpose_source_pins'],bound=e.bound);builder.verify_loaded(plan['purpose_source_pins'],self.root);e.need(e.raw(ledger_path)==before,'SSOT_CHANGED_DURING_ADMISSION')
        return manifest,pub
    def replay_checkpoint(self,plan,state):
        import owned_checkpoint_replay
        # Re-consume each actual transport/reservation/full-readback through
        # the separately reviewed context adapter; no summary grants a retry.
        owned_checkpoint_replay.require_checkpoint(plan,state,root=self.root)
    def require_events(self,root,at):return mutations.require_events(root,at)
    def require_budget(self,root,method,at):return policy.require_write_budget(root,method,at)
    def transport(self,token,out):
        self.token=token;self.opener=OwnedSuccessorArchiveWait(PacedOpener(urllib.request.build_opener(transport.NoRedirect())));return transport.ZenodoTransport('zenodo.org',token,out,opener=self.opener)
    def boundary(self,plan,package,t,out):return OwnedDigestBoundary(plan,package,t,out,self.opener,self.token)

def execute(plan_binding,output,token,*,checkpoint=None,reviewed_driver_sha256):
    # All canonical configuration comes from the root-bound actual plan. No
    # CLI credential or auto-running scheduler command is present.
    root=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0').resolve(strict=True);_,plan=e.bound(root,plan_binding);runtime=ActualRuntime(root,plan)
    return e.execute(root,plan_binding,output,token,runtime,checkpoint=checkpoint,reviewed_driver_sha256=reviewed_driver_sha256)
if __name__=='__main__':raise SystemExit('HOLD: explicit root call inside the current measured source session is required')
