"""TEST-ONLY fixtures: approved activation guard A01..A36, no live execution evidence."""
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import corpus_ledger
import nightly_coverage as nc
import run_flow
from install_phase5_hooks import TARGETS
from mirror_parity import GENERATION_ROOT
from release_packet import LABEL

UTC = dt.timezone.utc
REAL_PRESERVE = corpus_ledger.preserve_publication_registrations


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    return path


def relative_binding(root, path):
    return {'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class ActivationFixture:
    def __init__(self, case, root, *, activated='2026-10-03T05:00:00+00:00'):
        self.case, self.root = case, root.resolve()
        self.now = dt.datetime(2026, 10, 11, 12, tzinfo=UTC)
        self.at = dt.datetime.fromisoformat(activated)
        self.base = self.root/'reports/verification-coverage/TEST_ONLY_ACTIVATION'
        self.canonical = self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        self.paths = {}
        entries=[]
        for i in range(27):
            entity={'id':'publication:TEST_ONLY-'+str(i), 'path':'TEST_ONLY/release/'+str(i),
                    'run_id':'Run-'+str(900+i) if i<2 else 'Run-'+str(120+i),
                    'certificate':'TEST_ONLY/cert/'+str(i)+'.json', 'certificate_sha256':'a'*64,
                    'approved_publication_binding_reviews':['b'*64], 'status':'CERTIFIED',
                    'certificate_valid':True, 'publication_binding_status':'PUBLICATION_BOUND',
                    'publication_registration_status':'PASS' if i<2 else 'HOLD_NO_CLAIM_MAP',
                    'enforcement_acceptable':True}
            if i>=2:
                rid=str(100000+i); entity['doi']='10.5281/zenodo.'+rid
                receipt={'method':'GET','environment':'zenodo.org','http_status':200,
                         'url':'https://zenodo.org/api/records/'+rid,
                         'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':'c'*64,
                         'response':{'id':int(rid),'is_published':True,'metadata':{'description':LABEL+'<hr>Historical description'}}}
                path=write(self.base/'banner'/rid/'GET.json',receipt)
                entity['public_uncertified_readback']={'authenticated':True,'record_id':rid,
                    'receipt_path':str(path.relative_to(self.root)), 'receipt_sha256':nc.binding(path)['sha256'],
                    'response_sha256':'c'*64}
            entries.append(entity)
        self.ledger={'tree_root':str(self.root), 'file_counts':{}, 'run_counts':{},
                     'receipt_era':{'total':71,'certified':71}, 'mirror_drift':[], 'errors':[],
                     'run_entities':[], 'file_entities':[], 'publication_entities':entries,
                     'premise_declaration_cutover_run':'Run-188', 'publication_registration_enforcement_acceptable':True,
                     'activation_snapshot_observed_at_utc':self.time(-4)}
        plan={'tree_root':str(self.root),'publication_entities':copy.deepcopy(entries)}
        self.put('registration_plan',plan)
        self.put('registration_ledger',self.ledger)
        plan_patch = patch('nightly_coverage.APPROVED_REGISTRATION_PLAN_SHA256',nc.binding(self.paths['registration_plan'])['sha256'])
        plan_patch.start(); self.case.addCleanup(plan_patch.stop)
        # Certificate/binding parsing is covered by existing preserving consumer
        # tests. This fixture supplies synthetic qualified entries, but exercises
        # the real banner consumer and every guard/identity comparison below.
        consumer_patch = patch('corpus_ledger.preserve_publication_registrations',side_effect=lambda ledger, previous: copy.deepcopy(ledger))
        consumer_patch.start(); self.case.addCleanup(consumer_patch.stop)
        gate_patch=patch('publication_gate.evaluate_publication',return_value={
            'status':'PASS','exact_publication_binding':True,'claim_gate':{'status':'PASS'},
            'premise_declaration_required':True,'premise_declaration':{'status':'PASS'}})
        gate_patch.start(); self.case.addCleanup(gate_patch.stop)
        parity_patch=patch('mirror_parity.run_parity',return_value={'status':'MATCH','errors':[],'differences':[]})
        parity_patch.start(); self.case.addCleanup(parity_patch.stop)
        snapshots=[]; installed=[]
        for relative in sorted(TARGETS):
            path=self.root/relative; path.parent.mkdir(parents=True,exist_ok=True); path.write_text('TEST_ONLY installed '+relative)
            digest=nc.binding(path)['sha256']
            snapshots.append({'relative_path':relative,'after_sha256':digest})
            installed.append({'path':relative,'after_sha256':digest})
        self.put('after_manifest',{'snapshots':snapshots})
        self.put('installation',{'standard':'VRS-PHASE5-HOOK-INSTALL-1','status':'INSTALLED_HASH_READBACK_PASS',
            'root':str(self.root),'manifest_sha256':nc.binding(self.paths['after_manifest'])['sha256'],
            'installed':installed,'release_commit':'d'*40,'started_at_utc':self.time(-8),'completed_at_utc':self.time(-7)})
        self.put('pr',{'number':50,'state':'MERGED','mergeCommit':{'oid':'d'*40}})
        self.put('checks',[{'name':'TEST_ONLY required','bucket':'pass'}])
        self.put('merge_review',{'standard':'VRS-PHASE5-MERGE-REVIEW-1','status':'MERGED_REQUIRED_CHECKS_PASS',
            'observed_at_utc':self.time(-9),'release_commit':'d'*40,
            'pull_request_readback':self.bound('pr'),'checks_readback':self.bound('checks')})
        baseline={'standard':'VRS-PROTECTED-IMPLEMENTATION-BASELINE-1',
            'canonical_pipeline_root':str(self.root/'RESEARCH_PIPELINE_v2'),
            'protected_implementation_sha256':{'client.py':'e'*64,'issuer.py':'f'*64},
            'unchanged_support_sha256':{'aligner.py':'1'*64},
            'deployed_pre_f2h_sha256':{'/TEST_ONLY/comparator.sh':'2'*64},
            'protected_remote_implementation_sha256':{'/TEST_ONLY/wrapper':'3'*64},
            'deployed_f2g_baseline_reconciliation':{'release_commit':'4'*40,'overlay_manifest_sha256':'5'*64,
                'changes':[{'path':'/TEST_ONLY/service','deployed_authority_sha256':'6'*64}]}}
        self.put('protected_baseline',baseline)
        checks=[{'surface':'DEPLOYED_DROPLET','path':path,'expected_sha256':digest,'actual_sha256':digest,'match':True}
                for path,digest in {'/TEST_ONLY/comparator.sh':'2'*64,'/TEST_ONLY/wrapper':'3'*64,'/TEST_ONLY/service':'6'*64}.items()]
        checks.extend({'surface':'CANONICAL_LOCAL','path':str(self.root/'RESEARCH_PIPELINE_v2'/name),
                       'expected_sha256':digest,'actual_sha256':digest,'match':True}
                      for name,digest in {**baseline['protected_implementation_sha256'],**baseline['unchanged_support_sha256']}.items())
        self.put('protected_readback',{'status':'LIVE_PROTECTED_HASH_READBACK_PASS','at_utc':self.time(-6),
            'baseline_sha256':nc.binding(self.paths['protected_baseline'])['sha256'],
            'approved_overlay_release':'4'*40,'approved_overlay_manifest_sha256':'5'*64,'checks':checks})
        for name,root_value in [('generation_state',str(GENERATION_ROOT)),('mirror_state',str(self.root))]:
            self.put(name,{'root':root_value,'run_ids':['Run-186','Run-187']})
        self.put('source_observation',{'standard':'VRS-PHASE5-CUTOVER-OBSERVATION-1','observed_at_utc':self.time(-3),
            'tree_root':str(self.root),'generation_root':str(GENERATION_ROOT),'latest_run':'Run-187',
            'next_run':'Run-188','next_run_sealed':False,
            'generation_state':self.bound('generation_state'),'mirror_state':self.bound('mirror_state')})
        automation={'id':'viridis-nightly-science-generator','status':'ACTIVE',
                    'cwds':[str(GENERATION_ROOT)],'rrule':'FREQ=DAILY;BYHOUR=1,7,13,19',
                    'model':'TEST_ONLY','reasoning_effort':'high','prompt':'TEST_ONLY previous no recurring publication authority'}
        self.put('scheduler_before_raw',automation)
        self.put('scheduler_before',{'standard':'VRS-PHASE5-SCHEDULER-READBACK-1','observed_at_utc':self.time(-10),
                                    'automation':automation,'raw_configuration':self.bound('scheduler_before_raw')})
        automation=copy.deepcopy(automation); automation['prompt']='\n'.join([
            'nightly_checkpoint.py --begin --enforce-new-artifacts',
            'nightly_checkpoint.py --finish --enforce-new-artifacts',
            'issuer --require-premise-declaration',
            'Seal explicit foundation_basis in SEALED_RUN_MANIFEST and SEALED_CLAIM_INVENTORY.',
            'TEST_ONLY no recurring publication authority'])
        self.put('scheduler_raw',automation)
        self.put('scheduler_readback',{'standard':'VRS-PHASE5-SCHEDULER-READBACK-1','observed_at_utc':self.time(-1),
            'automation':automation,'raw_configuration':self.bound('scheduler_raw')})
        self.receipt={'standard':nc.ACTIVATION_STANDARD,'status':'ENFORCEMENT_ACTIVATED','tree_root':str(self.root),
                      'generation_root':str(GENERATION_ROOT),'scheduler_id':'viridis-nightly-science-generator',
                      'timezone':'America/New_York','activated_at_utc':self.at.isoformat(),
                      'premise_declaration_cutover_run':'Run-188','first_eligible_window':nc.first_eligible_window(self.at),
                      'sources':{key:self.bound(key) for key in nc.ACTIVATION_SOURCES},
                      'proofs':{key:self.bound(key) for key in nc.ACTIVATION_PROOFS}}
        self.save_activation()

    def time(self, minutes):return (self.at+dt.timedelta(minutes=minutes)).isoformat()
    def put(self,name,obj):self.paths[name]=write(self.base/(name+'.json'),obj);return self.paths[name]
    def bound(self,name):return relative_binding(self.root,self.paths[name])
    def save_activation(self):
        self.put('activation',self.receipt)
        self.ledger['enforcement_activation']=self.bound('activation')
        write(self.canonical,self.ledger)
    def change(self,name,action,*,rebind=True):
        obj=json.loads(self.paths[name].read_text()); action(obj);write(self.paths[name],obj)
        if rebind:
            for table in ('sources','proofs'):
                if name in self.receipt[table]:self.receipt[table][name]=self.bound(name)
            self.save_activation()
    def attach(self,report,day,latest='Run-188'):
        ledger=copy.deepcopy(self.ledger)
        ledger['run_entities']=[{'id':latest,'kind':'PAPER','path':'TEST_ONLY/current'}]
        path=write(self.base/('cycle-'+day+'-'+str(len(list(self.base.glob('cycle-*'))))+'.json'),ledger)
        report['coverage_ledger']=relative_binding(self.root,path)
        report['enforcement_activation']=self.bound('activation')
        report['coverage']={k:ledger[k] for k in nc.COVERAGE_FIELDS}
        report['new_artifact_publication_gate'].update(entity_id=latest,premise_declaration_required=True,
                                                       premise_declaration={'status':'PASS'})
        return report
    def checkpoint(self,day,suffix='a',*,clean=True,latest='Run-188'):
        date=dt.date.fromisoformat(day);lower=dt.datetime.combine(date,dt.time(1),nc.TZ)
        upper=dt.datetime.combine(date+dt.timedelta(days=1),dt.time(1),nc.TZ)
        invocation=day+'-'+suffix;directory=self.root/'RESEARCH_PIPELINE_v2/nightly_checkpoints'/invocation
        start={'standard':'VRS-NIGHTLY-CHECKPOINT-1','invocation_id':invocation,'started_at_utc':(lower+dt.timedelta(minutes=1)).isoformat()}
        sp=write(directory/'START.json',start)
        finish={'standard':start['standard'],'invocation_id':invocation,'started_at_utc':start['started_at_utc'],
            'completed_at_utc':(lower+dt.timedelta(hours=1)).isoformat(),'start_receipt_sha256':nc.binding(sp)['sha256'],
            'status':'NIGHTLY_PROGRESS_PASS' if clean else 'HOLD_NIGHTLY_PROGRESS','incidents':[] if clean else ['TEST_ONLY_HOLD'],
            'generation':{'latest_run':latest,'generated_at_utc':(lower+dt.timedelta(minutes=5)).isoformat(),
                'window':{'standard':'VRS-NIGHTLY-WINDOW-1','window_id':day,'timezone':'America/New_York','satisfied':True,
                          'starts_at_utc':lower.isoformat(),'ends_at_utc':upper.isoformat()}}}
        fp=write(directory/'FINISH.json',finish)
        report={'mode':'ENFORCING','enforcement':True,'observed_at_utc':(lower+dt.timedelta(hours=2)).isoformat(),
                'status':'ENFORCING_PASS' if clean else 'HOLD','checkpoint':nc.binding(fp),
                'new_artifact_publication_gate':{'status':'PASS','exact_publication_binding':True,'claim_gate':{'status':'PASS'}}}
        self.attach(report,day,latest)
        rp=write(self.root/'reports/verification-coverage'/invocation/'NIGHTLY_CYCLE_REPORT.json',report)
        return rp,fp,sp


class ApprovedActivation36Cases(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.f=ActivationFixture(self,self.root);self.reports=[]
    def load(self):return nc.load_enforcement_activation(self.root,now=self.f.now)
    def collect(self):return nc.collect_streak(self.root,self.reports,now=self.f.now)
    def add(self,day,**kwargs):
        result=self.f.checkpoint(day,**kwargs);self.reports.append(result[0]);return result
    def hold(self):
        result=self.collect();self.assertEqual(result['status'],'HOLD_ENFORCEMENT_ACTIVATION');self.assertEqual(result['consecutive_clean_closed_windows'],0)
    def report_change(self,path,action):obj=json.loads(path.read_text());action(obj);write(path,obj)

    def test_A01_seven_genuine_full_future_windows(self):
        for day in range(4,11):self.add(f'2026-10-{day:02}')
        self.assertEqual(self.collect()['status'],'SEVEN_CLEAN_NIGHTLY_WINDOWS')
    def test_A02_historical_replays_cannot_count(self):
        for day in range(20,27):self.add(f'2026-09-{day}')
        result=self.collect();self.assertEqual(len(result['ineligible']),7);self.assertEqual(result['consecutive_clean_closed_windows'],0)
    def test_A03_historical_does_not_poison_genuine_seven(self):
        rp,fp,_=self.add('2026-09-28',clean=False)
        old=json.loads(fp.read_text());old['generation']['window']['satisfied']=False;write(fp,old)
        self.report_change(rp,lambda x:x.update(checkpoint=nc.binding(fp)))
        for day in range(4,11):self.add(f'2026-10-{day:02}')
        result=self.collect();self.assertEqual(result['status'],'SEVEN_CLEAN_NIGHTLY_WINDOWS');self.assertEqual(len(result['ineligible']),1)
    def test_A04_partial_activation_window_then_six(self):
        self.f=ActivationFixture(self,self.root,activated='2026-10-04T05:30:00+00:00')
        for day in range(4,11):self.add(f'2026-10-{day:02}')
        result=self.collect();self.assertEqual(result['consecutive_clean_closed_windows'],6);self.assertEqual(len(result['ineligible']),1)
    def test_A05_exact_boundary_can_count(self):
        self.f=ActivationFixture(self,self.root,activated='2026-10-04T05:00:00+00:00')
        for day in range(4,11):self.add(f'2026-10-{day:02}')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'],7)
    def test_A06_missing_authoritative_pointer(self):
        self.f.ledger.pop('enforcement_activation');write(self.f.canonical,self.f.ledger);self.hold()
    def test_A07_malformed_binding_and_boolean_alias(self):
        for bad in ({'path':self.f.bound('activation')['path']}, {'path':True,'sha256':'a'*64},
                    {'path':self.f.bound('activation')['path'],'sha256':True}, {'path':self.f.bound('activation')['path'],'sha256':'A'*64}):
            with self.subTest(bad=bad):self.f.ledger['enforcement_activation']=bad;write(self.f.canonical,self.f.ledger);self.hold()
    def test_A08_missing_symlink_external_traversal(self):
        original=self.f.bound('activation')
        for path in ('reports/verification-coverage/missing.json','../outside.json','/tmp/outside.json'):
            self.f.ledger['enforcement_activation']={**original,'path':path};write(self.f.canonical,self.f.ledger);self.hold()
        self.f.paths['activation'].rename(self.f.base/'real-activation.json');self.f.paths['activation'].symlink_to(self.f.base/'real-activation.json')
        self.f.ledger['enforcement_activation']=original;write(self.f.canonical,self.f.ledger);self.hold()
    def test_A09_mutated_activation_or_dependency(self):
        self.f.paths['activation'].write_text(self.f.paths['activation'].read_text()+' ');self.hold();self.f.save_activation()
        self.f.paths['checks'].write_text(self.f.paths['checks'].read_text()+' ');self.hold()
    def test_A10_future_naive_reversed_chronology(self):
        for value in ('2026-11-01T12:00:00+00:00','2026-10-03T05:00:00'):
            self.f.receipt['activated_at_utc']=value;self.f.save_activation();self.hold()
        self.f.receipt['activated_at_utc']=self.f.at.isoformat();self.f.change('installation',lambda x:x.update(completed_at_utc=self.f.time(-9)));self.hold()
    def test_A11_backdated_floor_or_wrong_timezone(self):
        self.f.receipt['first_eligible_window']='2026-10-02';self.f.save_activation();self.hold()
        self.f.receipt['first_eligible_window']='2026-10-03';self.f.receipt['timezone']='UTC';self.f.save_activation();self.hold()
    def test_A12_report_activation_missing_or_mismatched(self):
        rp,_,_=self.add('2026-10-10');original=json.loads(rp.read_text())
        for bad in (None,{'path':'reports/verification-coverage/foreign.json','sha256':'0'*64}):
            obj=copy.deepcopy(original)
            if bad is None:obj.pop('enforcement_activation')
            else:obj['enforcement_activation']=bad
            write(rp,obj);self.assertTrue(self.collect()['rejected']);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)

    def test_A13_cycle_snapshot_missing_mutated_external_symlink(self):
        rp,_,_=self.add('2026-10-10');report=json.loads(rp.read_text());path=self.root/report['coverage_ledger']['path'];original=path.read_bytes()
        for corrupt in ('missing','mutated','external','symlink'):
            with self.subTest(corrupt=corrupt):
                if path.is_symlink():path.unlink()
                path.write_bytes(original);record=copy.deepcopy(report)
                if corrupt=='missing':record.pop('coverage_ledger')
                elif corrupt=='mutated':path.write_bytes(original+b' ')
                elif corrupt=='external':record['coverage_ledger']['path']='/tmp/external'
                else:path.rename(path.with_suffix('.saved'));path.symlink_to(path.with_suffix('.saved'))
                write(rp,record);self.assertTrue(self.collect()['rejected'])
    def test_A14_report_coverage_different_from_snapshot(self):
        rp,_,_=self.add('2026-10-10');self.report_change(rp,lambda x:x['coverage']['receipt_era'].update(certified=72));self.assertTrue(self.collect()['rejected'])
    def test_A15_cutover_missing_zero_reserved_noncanonical_different(self):
        original=copy.deepcopy(self.f.ledger)
        for value in (None,'Run-000','Run-900','Run-0188','Run-189'):
            self.f.ledger['premise_declaration_cutover_run']=value;write(self.f.canonical,self.f.ledger);self.hold()
        self.f.ledger=original;write(self.f.canonical,original)
        rp,_,_=self.add('2026-10-10');report=json.loads(rp.read_text());path=self.root/report['coverage_ledger']['path']
        snapshot=json.loads(path.read_text());snapshot['premise_declaration_cutover_run']='Run-189';write(path,snapshot)
        report['coverage_ledger']=relative_binding(self.root,path);write(rp,report);self.assertTrue(self.collect()['rejected'])

    def test_A16_generated_run_below_reserved_wrong_join(self):
        for index,value in enumerate(('Run-187','Run-900')):
            self.add('2026-10-10',suffix=str(index),latest=value)
        self.assertTrue(self.collect()['rejected'])
        self.reports=[];rp,_,_=self.add('2026-10-10',suffix='join');self.report_change(rp,lambda x:x['new_artifact_publication_gate'].update(entity_id='Run-189'));self.assertTrue(self.collect()['rejected'])
    def test_A17_premise_gate_actual_required_pass(self):
        rp,_,_=self.add('2026-10-10');original=json.loads(rp.read_text())
        for status,required in [('EXEMPT',True),('HOLD',True),('PASS',False),('PASS',1),(None,True)]:
            report=copy.deepcopy(original);gate=report['new_artifact_publication_gate'];gate['premise_declaration_required']=required;gate['premise_declaration']={} if status is None else {'status':status};write(rp,report)
            self.assertTrue(self.collect()['rejected'])
    def test_A18_old_start_or_generation_never_counts(self):
        rp,fp,sp=self.add('2026-10-10');start=json.loads(sp.read_text());start['started_at_utc']='2026-10-02T05:00:00+00:00';write(sp,start)
        finish=json.loads(fp.read_text());finish['started_at_utc']=start['started_at_utc'];finish['start_receipt_sha256']=nc.binding(sp)['sha256'];write(fp,finish)
        self.report_change(rp,lambda x:x.update(checkpoint=nc.binding(fp)));self.assertEqual(len(self.collect()['ineligible']),1)
        self.reports=[];rp,fp,sp=self.add('2026-10-10',suffix='generation');finish=json.loads(fp.read_text());finish['generation']['generated_at_utc']='2026-10-02T05:00:00+00:00';write(fp,finish)
        self.report_change(rp,lambda x:x.update(checkpoint=nc.binding(fp)));self.assertTrue(self.collect()['rejected']);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)

    def test_A19_install_complete_manifest_merge_required(self):
        original=json.loads(self.f.paths['installation'].read_text())
        for action in (lambda x:x.update(status='READY'),lambda x:x['installed'].pop(),lambda x:x['installed'][0].update(after_sha256='0'*64),lambda x:x.update(release_commit='0'*40)):
            write(self.f.paths['installation'],original);self.f.change('installation',action);self.hold()
        write(self.f.paths['installation'],original);self.f.receipt['sources']['installation']=self.f.bound('installation');self.f.save_activation()
        self.f.change('pr',lambda x:x.update(state='OPEN'),rebind=False)
        self.f.change('merge_review',lambda x:x.update(pull_request_readback=self.f.bound('pr')));self.hold()
        self.f.change('pr',lambda x:x.update(state='MERGED'),rebind=False)
        self.f.change('checks',lambda x:x[0].update(bucket='fail'),rebind=False)
        self.f.change('merge_review',lambda x:x.update(pull_request_readback=self.f.bound('pr'),checks_readback=self.f.bound('checks')));self.hold()

    def test_A20_protected_omission_wrong_baseline_or_hash(self):
        original=json.loads(self.f.paths['protected_readback'].read_text())
        for action in (lambda x:x.update(status='READY'),lambda x:x['checks'].pop(),lambda x:x.update(baseline_sha256='0'*64),lambda x:x['checks'][0].update(actual_sha256='0'*64),lambda x:x.update(approved_overlay_release='0'*40)):
            write(self.f.paths['protected_readback'],original);self.f.change('protected_readback',action);self.hold()
    def test_A21_stale_source_or_wrong_root(self):
        self.f.change('source_observation',lambda x:x.update(next_run_sealed=True));self.hold()
        self.f.change('source_observation',lambda x:x.update(next_run_sealed=False,tree_root='/tmp/other'));self.hold()
        self.f.change('source_observation',lambda x:x.update(tree_root=str(self.root)))
        self.f.change('generation_state',lambda x:x['run_ids'].append('Run-188'),rebind=False)
        self.f.change('source_observation',lambda x:x.update(generation_state=self.f.bound('generation_state')));self.hold()

    def test_A22_scheduler_identity_flags_active_cadence(self):
        original=json.loads(self.f.paths['scheduler_readback'].read_text())
        prompt=original['automation']['prompt']
        for field,value in [('id','different'),('status','PAUSED'),('rrule','FREQ=DAILY;BYHOUR=2'),
                            ('model','changed'),('cwds',['/tmp/foreign']),
                            ('prompt',prompt.replace('--begin --enforce-new-artifacts','--begin')),
                            ('prompt',prompt.replace('--finish --enforce-new-artifacts','--finish')),
                            ('prompt',prompt.replace('--require-premise-declaration','')),
                            ('prompt',prompt.replace('SEALED_CLAIM_INVENTORY',''))]:
            wrapper=copy.deepcopy(original);wrapper['automation'][field]=value;write(self.f.paths['scheduler_raw'],wrapper['automation']);wrapper['raw_configuration']=self.f.bound('scheduler_raw');write(self.f.paths['scheduler_readback'],wrapper)
            self.f.receipt['sources']['scheduler_readback']=self.f.bound('scheduler_readback');self.f.save_activation();self.hold()
    def test_A23_original_identity_replaced_even_with_27(self):
        self.f.ledger['publication_entities'][0]['id']='replacement';write(self.f.canonical,self.f.ledger);self.hold()
    def test_A24_review_mutated_or_acceptability_not_boolean(self):
        original=copy.deepcopy(self.f.ledger)
        for action in (lambda e:e.pop('approved_publication_binding_reviews'),lambda e:e.update(approved_publication_binding_reviews=['0'*64]),lambda e:e.update(enforcement_acceptable=False),lambda e:e.update(enforcement_acceptable=1)):
            self.f.ledger=copy.deepcopy(original);action(self.f.ledger['publication_entities'][0]);write(self.f.canonical,self.f.ledger);self.hold()
    def test_A25_no_map_banner_proof_malformed_doi_unpublished_duplicate(self):
        baseline=copy.deepcopy(self.f.ledger)
        for mutation in (lambda e:e.pop('public_uncertified_readback'),lambda e:e.update(doi='10.5281/zenodo.999'),
                         lambda e:e['public_uncertified_readback'].update(receipt_sha256='0'*64)):
            self.f.ledger=copy.deepcopy(baseline);mutation(self.f.ledger['publication_entities'][2]);write(self.f.canonical,self.f.ledger);self.hold()
        self.f.ledger=baseline;write(self.f.canonical,self.f.ledger)
        entry=self.f.ledger['publication_entities'][2];proof=entry['public_uncertified_readback'];path=self.root/proof['receipt_path'];original=json.loads(path.read_text())
        for action in (lambda x:x['response'].update(id=999),lambda x:x['response'].update(is_published=False),lambda x:x['response']['metadata'].update(description='no banner'),lambda x:x['response']['metadata'].update(description=LABEL+LABEL)):
            receipt=copy.deepcopy(original);action(receipt);write(path,receipt);proof['receipt_sha256']=nc.binding(path)['sha256'];write(self.f.canonical,self.f.ledger)
            # Pin both copies so this case exercises semantic banner validation.
            snapshot=copy.deepcopy(self.f.ledger);snapshot.pop('enforcement_activation',None);write(self.f.paths['registration_ledger'],snapshot);self.f.receipt['sources']['registration_ledger']=self.f.bound('registration_ledger');self.f.save_activation();self.hold()
    def test_A26_25_hold_claims_exact_banners_do_not_upgrade(self):
        self.load();self.assertEqual(sum(e['publication_registration_status']=='HOLD_NO_CLAIM_MAP' for e in self.f.ledger['publication_entities']),25)
    def test_A27_extra_valid_registration_preserves_prior(self):
        extra=copy.deepcopy(self.f.ledger['publication_entities'][0]);extra.update(id='publication:extra',path='TEST_ONLY/extra');self.f.ledger['publication_entities'].append(extra);write(self.f.canonical,self.f.ledger);self.load()
    def test_A28_preserving_scan_keeps_exact_pointer_old_bytes(self):
        rp,fp,sp=self.add('2026-09-28');before=[p.read_bytes() for p in (rp,fp,sp)]
        previous=copy.deepcopy(self.f.ledger)
        # Call the unpatched function to exercise actual activation preservation.
        fresh=copy.deepcopy(previous);fresh['publication_entities']=[];fresh['run_entities']=[]
        with patch('corpus_ledger.inspect_certificate',return_value={'valid':False}):
            result=REAL_PRESERVE(fresh,previous)
        self.assertEqual(result['enforcement_activation'],previous['enforcement_activation'])
        self.assertEqual(result['premise_declaration_cutover_run'],'Run-188')
        self.assertEqual(len(result['publication_entities']),27)
        self.assertEqual(before,[p.read_bytes() for p in (rp,fp,sp)])
    def test_A29_invalid_pointer_cannot_silently_preserve(self):
        previous=copy.deepcopy(self.f.ledger);previous['enforcement_activation']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
            REAL_PRESERVE(copy.deepcopy(self.f.ledger),previous)
        previous['enforcement_activation']=self.f.bound('activation')
        self.f.paths['activation'].write_text(self.f.paths['activation'].read_text()+' ')
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
            REAL_PRESERVE(copy.deepcopy(self.f.ledger),previous)
    def test_A30_report_only_without_activation_is_not_counted(self):
        rp,_,_=self.add('2026-10-10');self.report_change(rp,lambda x:x.update(mode='REPORT_ONLY',enforcement=False));self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
        # Global activation is fail-closed even when inputs are report-only.
        self.f.ledger.pop('enforcement_activation');write(self.f.canonical,self.f.ledger);self.hold()

    def test_A31_open_duplicate_missing_last_and_hold(self):
        self.add('2026-10-11');self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
        self.add('2026-10-10');self.reports+=self.reports;self.assertEqual(self.collect()['consecutive_clean_closed_windows'],1)
        self.add('2026-10-10',suffix='hold',clean=False);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
        self.reports=[]
        for day in range(3,10):self.add(f'2026-10-{day:02}',suffix='stale')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)

    def test_A32_dst_calendar_boundaries(self):
        for activation,day,now in [('2026-11-01T05:00:00+00:00','2026-11-01','2026-11-02T12:00:00+00:00'),('2027-03-14T06:00:00+00:00','2027-03-14','2027-03-15T12:00:00+00:00')]:
            self.f=ActivationFixture(self,self.root,activated=activation);self.f.now=dt.datetime.fromisoformat(now);self.reports=[];self.add(day);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],1)
    def test_A33_checkpoint_hash_or_future_chronology_retained(self):
        rp,fp,sp=self.add('2026-10-10');sp.write_text(sp.read_text()+' ');self.assertTrue(self.collect()['rejected'])
        self.reports=[];rp,fp,sp=self.add('2026-10-10',suffix='future');self.report_change(rp,lambda x:x.update(observed_at_utc='2026-10-12T12:00:00+00:00'));self.assertTrue(self.collect()['rejected'])
        self.reports=[];rp,fp,sp=self.add('2026-10-10',suffix='reversed');finish=json.loads(fp.read_text());finish['completed_at_utc']='2026-10-10T04:00:00+00:00';write(fp,finish)
        self.report_change(rp,lambda x:x.update(checkpoint=nc.binding(fp)));self.assertTrue(self.collect()['rejected'])

    def test_A34_certificate_binding_claim_parity_holds(self):
        rp,_,_=self.add('2026-10-10');original=json.loads(rp.read_text())
        for action in (lambda x:x['new_artifact_publication_gate'].update(status='HOLD'),lambda x:x['new_artifact_publication_gate'].update(exact_publication_binding=False),lambda x:x['new_artifact_publication_gate']['claim_gate'].update(status='HOLD'),lambda x:x['coverage'].update(mirror_drift=['Run-188'])):
            obj=copy.deepcopy(original);action(obj);write(rp,obj);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
        write(rp,original)
        with patch('publication_gate.evaluate_publication',return_value={'status':'HOLD'}):
            self.assertTrue(self.collect()['rejected']);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
        with patch('mirror_parity.run_parity',return_value={'status':'MIRROR_DRIFT','errors':[],'differences':[{'path':'paper.tex'}]}):
            self.assertTrue(self.collect()['rejected']);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_A35_guarded_predecessor_mismatch_preserves_bytes(self):
        before=self.f.canonical.read_bytes();proposal=copy.deepcopy(self.f.ledger);proposal['enforcement_activation']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'concurrent authoritative ledger'):
            corpus_ledger.write_guarded_ledger(self.f.canonical,proposal,'0'*64)
        self.assertEqual(before,self.f.canonical.read_bytes())
    def test_A36_default_report_only_and_old_cutover_do_not_infer(self):
        # Compare complete default report-only outputs against the frozen
        # predecessor implementation at the same test-only time/output path.
        predecessor=Path(run_flow.__file__).parent/'production_snapshots/phase5-20261004/after/RESEARCH_PIPELINE_v2/verification_coverage_gates/run_flow.py'
        expected='89492b12622fc44ecae0c407a3937320dc0fd62454b209ca8b5d95fc54d56dca'
        self.assertEqual(nc.binding(predecessor)['sha256'],expected)
        spec=importlib.util.spec_from_file_location('TEST_ONLY_predecessor_run_flow',predecessor)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        ledger=copy.deepcopy(self.f.ledger)
        for field in ('enforcement_activation','premise_declaration_cutover_run','activation_snapshot_observed_at_utc'):
            ledger.pop(field)
        write(self.f.canonical,ledger)
        _,checkpoint,_=self.f.checkpoint('2026-10-04')
        output=self.root/'reports/verification-coverage/TEST_ONLY_DEFAULT_OUTPUT'
        fixed=dt.datetime(2026,10,5,20,tzinfo=UTC)
        class Clock(dt.datetime):
            @classmethod
            def now(cls,tz=None):return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
        patches=[patch('datetime.datetime',Clock),patch('corpus_ledger.build',return_value=ledger),
                 patch('corpus_ledger.render_markdown',return_value='TEST_ONLY ledger'),
                 patch('doi_audit.build_audit',return_value={'published_records':[]}),
                 patch('doi_audit.render_markdown',return_value='TEST_ONLY audit'),
                 patch('doi_triage.build_triage',return_value={'counts':{},'records':[]}),
                 patch('doi_triage.markdown',return_value='TEST_ONLY triage'),
                 patch('nightly_coverage.load_enforcement_activation')]
        for obj in patches:obj.start();self.addCleanup(obj.stop)
        before=old.cycle_report(self.root,checkpoint,output)
        before_bytes={str(p.relative_to(output)):p.read_bytes() for p in output.rglob('*') if p.is_file()}
        shutil.rmtree(output)
        after=run_flow.cycle_report(self.root,checkpoint,output)
        after_bytes={str(p.relative_to(output)):p.read_bytes() for p in output.rglob('*') if p.is_file()}
        self.assertEqual(before,after);self.assertEqual(before_bytes,after_bytes)
        self.assertFalse(after['enforcement']);self.assertEqual(after['mode'],'REPORT_ONLY')
        self.assertNotIn('foundation_basis',json.loads(self.f.canonical.read_text()))



if __name__=='__main__':unittest.main()
