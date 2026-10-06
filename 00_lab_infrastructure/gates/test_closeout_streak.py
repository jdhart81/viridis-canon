"""Offline fixtures only: recovery changes bookkeeping, never theorem acceptance."""
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import nightly_coverage as nc
import closeout_streak as cc
from test_activation_guard import ActivationFixture, write, relative_binding

PASS = {'status':'PASS','exact_publication_binding':True,'claim_gate':{'status':'PASS'},
        'premise_declaration_required':True,'premise_declaration':{'status':'PASS'}}

class DatedFailureRecovery(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.f=ActivationFixture(self,self.root)
        self.now=dt.datetime(2026,10,14,12,tzinfo=dt.timezone.utc)
        self.reports=[];self.failed=set()
        self.gate_patch=patch('publication_gate.evaluate_publication',side_effect=self.gate)
        self.gate_patch.start();self.addCleanup(self.gate_patch.stop)
    def gate(self,path,*args,**kwargs):
        if str(path).split('/')[-1] in self.failed:
            return {'status':'HOLD','reasons':['TEST_ONLY_MISSING_BINDING'],'exact_publication_binding':False}
        return dict(PASS)
    def change(self,p,fn):
        d=json.loads(p.read_text());fn(d);write(p,d)
    def add(self,day,*,failed=False,suffix='a',clean=None):
        clean=(not failed) if clean is None else clean
        rp,fp,sp=self.f.checkpoint(day,suffix,clean=clean)
        d=json.loads(rp.read_text());lp=self.root/d['coverage_ledger']['path']
        ledger=json.loads(lp.read_text());ledger['run_entities'][0]['path']='TEST_ONLY/'+day
        write(lp,ledger);d['coverage_ledger']=relative_binding(self.root,lp)
        if failed:
            self.failed.add(day);d['new_artifact_publication_gate'].update(status='HOLD',exact_publication_binding=False,claim_gate={'status':'HOLD'})
        finish=json.loads(fp.read_text());d['checkpoint_status']=finish['status'];d['incidents']=finish['incidents']
        write(rp,d);self.reports.append(rp);return rp,fp,sp
    def collect(self):return cc.collect_closeout_streak(self.root,self.reports,now=self.now)
    def seven(self):
        for day in range(7,14):self.add(f'2026-10-{day:02}')
    def test_C01_seven_passes_unchanged(self):
        self.seven();r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertEqual(r['status'],'SEVEN_CLEAN_NIGHTLY_WINDOWS')
    def test_C02_latest_failure_resets_to_zero(self):
        for day in range(7,13):self.add(f'2026-10-{day:02}')
        self.add('2026-10-13',failed=True);r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['anchored_failures']),1)
    def test_C03_failure_then_seven_recovers_without_deleting_failure(self):
        rp,_,_=self.add('2026-10-06',failed=True);before=rp.read_bytes();self.seven();r=self.collect()
        self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertEqual(r['status'],'SEVEN_CLEAN_NIGHTLY_WINDOWS');self.assertEqual(r['rejected'],[])
        self.assertEqual(rp.read_bytes(),before);self.assertEqual(r['windows']['2026-10-06'][0]['clean'],False);self.assertEqual(r['anchored_failures'][0]['window'],'2026-10-06')
    def test_C04_failure_then_one_only_counts_one(self):
        self.add('2026-10-12',failed=True);self.add('2026-10-13');self.assertEqual(self.collect()['consecutive_clean_closed_windows'],1)
    def test_C05_hold_never_credited(self):
        for day in range(7,14):self.add(f'2026-10-{day:02}',failed=True)
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertTrue(all(not row['clean'] for rows in r['windows'].values() for row in rows))
    def test_C06_same_day_hold_vetoes_clean(self):
        self.add('2026-10-13');self.add('2026-10-13',failed=True,suffix='b');self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C07_same_day_duplicates_count_once(self):
        for i in range(8):self.add('2026-10-13',suffix=str(i))
        self.reports+=self.reports;self.assertEqual(self.collect()['consecutive_clean_closed_windows'],1)
    def test_C08_unknown_json_still_globally_fail_closed(self):
        self.seven();p=self.root/'unknown.json';p.write_text('{');self.reports.append(p)
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['rejected']),1)
    def test_C09_hold_finish_tamper_still_global_rejection(self):
        _,fp,_=self.add('2026-10-06',failed=True);fp.write_text(fp.read_text()+' ');self.seven();r=self.collect()
        self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['rejected']),1);self.assertEqual(r['anchored_failures'],[])
    def test_C10_hold_start_tamper_still_global_rejection(self):
        _,_,sp=self.add('2026-10-06',failed=True);sp.write_text(sp.read_text()+' ');self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C11_hold_snapshot_tamper_still_global_rejection(self):
        rp,_,_=self.add('2026-10-06',failed=True);d=json.loads(rp.read_text());p=self.root/d['coverage_ledger']['path'];p.write_text(p.read_text()+' ')
        self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C12_empty_spoofed_hold_has_no_date_authority(self):
        self.seven();p=self.root/'fake.json';write(p,{'mode':'ENFORCING','enforcement':True,'status':'HOLD'});self.reports.append(p)
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['rejected']),1)
    def test_C13_spoofed_pass_with_missing_binding_does_not_get_failure_escape(self):
        rp,_,_=self.add('2026-10-06',failed=True);self.change(rp,lambda d:d.update(status='ENFORCING_PASS'));self.seven()
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['rejected']),1)
    def test_C14_wrong_window_bounds_cannot_anchor(self):
        rp,fp,_=self.add('2026-10-06',failed=True);self.change(fp,lambda d:d['generation']['window'].update(ends_at_utc='2026-10-08T05:00:00+00:00'))
        self.change(rp,lambda d:d.update(checkpoint=nc.binding(fp)));self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C15_preactivation_failure_ineligible_does_not_poison(self):
        self.add('2026-09-29',failed=True);self.seven();r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertEqual(len(r['ineligible']),1)
    def test_C16_open_window_never_credited(self):
        self.add('2026-10-14');self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C17_hold_with_generation_unsatisfied_is_dated_failure_not_pass(self):
        rp,fp,_=self.add('2026-10-06',failed=True);self.change(fp,lambda d:d['generation']['window'].update(satisfied=False))
        self.change(rp,lambda d:d.update(checkpoint=nc.binding(fp)));self.seven();r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertFalse(r['windows']['2026-10-06'][0]['clean'])
    def test_C18_hold_status_incident_contradiction_cannot_anchor(self):
        rp,fp,_=self.add('2026-10-06',failed=True);self.change(fp,lambda d:d.update(incidents=[]));self.change(rp,lambda d:d.update(checkpoint=nc.binding(fp),incidents=[]))
        self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C19_hold_future_timestamp_cannot_anchor(self):
        rp,_,_=self.add('2026-10-06',failed=True);self.change(rp,lambda d:d.update(observed_at_utc='2026-10-15T12:00:00+00:00'))
        self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C20_hold_outside_checkpoint_root_cannot_anchor(self):
        rp,fp,_=self.add('2026-10-06',failed=True);bad=self.root/'other/FINISH.json';bad.parent.mkdir();bad.write_bytes(fp.read_bytes());self.change(rp,lambda d:d.update(checkpoint=nc.binding(bad)))
        self.seven();self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C21_weekly_authentic_hold_persists_without_nightly_credit(self):
        rp,_,_=self.add('2026-10-13',failed=True);d=json.loads(rp.read_text());before=rp.read_bytes()
        with patch('corpus_ledger.render_markdown',return_value='TEST_ONLY ledger'):
            r=cc.weekly_report_for_checkpoint(self.root,d,now=self.now)
        self.assertEqual(r['status'],'REPORTED');self.assertEqual(r['checkpoint'],d['checkpoint']);self.assertFalse(r['proof_execution']);self.assertFalse(r['zenodo_writes'])
        self.assertEqual(rp.read_bytes(),before);self.assertEqual(self.collect()['consecutive_clean_closed_windows'],0)
    def test_C22_weekly_tampered_hold_does_not_write(self):
        rp,fp,_=self.add('2026-10-13',failed=True);fp.write_text(fp.read_text()+' ')
        with self.assertRaises(ValueError):cc.weekly_report_for_checkpoint(self.root,json.loads(rp.read_text()),now=self.now)
        self.assertFalse((self.root/'reports/verification-coverage/weekly').exists())
    def test_C23_weekly_replay_does_not_rewrite(self):
        rp,_,_=self.add('2026-10-13',failed=True);d=json.loads(rp.read_text())
        with patch('corpus_ledger.render_markdown',return_value='TEST_ONLY ledger'):
            first=cc.weekly_report_for_checkpoint(self.root,d,now=self.now);p=Path(first['ledger']['path']);before=p.read_bytes()
            second=cc.weekly_report_for_checkpoint(self.root,d,now=self.now+dt.timedelta(hours=1))
        self.assertEqual(first,second);self.assertEqual(p.read_bytes(),before)
    def test_C24_held_anchor_cannot_accept_a_pass_report(self):
        rp,_,_=self.add('2026-10-13')
        with self.assertRaisesRegex(ValueError,'explicit enforcing HOLD'):cc.held_checkpoint_window(self.root,json.loads(rp.read_text()),self.now)
    def test_C25_weekly_pass_still_uses_strict_fresh_gate(self):
        rp,_,_=self.add('2026-10-13');self.failed.add('2026-10-13')
        with self.assertRaisesRegex(ValueError,'fresh actual publication'):cc.weekly_report_for_checkpoint(self.root,json.loads(rp.read_text()),now=self.now)
        self.assertFalse((self.root/'reports/verification-coverage/weekly').exists())

    def test_C26_empty_object_unknown_not_silently_ignored(self):
        self.seven();p=self.root/'empty.json';write(p,{});self.reports.append(p)
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertEqual(len(r['rejected']),1)
    def test_C27_nonobject_unknown_not_silently_ignored(self):
        for content in ([],None,True):
            with self.subTest(content=content):
                self.seven();p=self.root/'nonobject.json';write(p,content);self.reports.append(p)
                r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],0);self.assertTrue(r['rejected'])
                self.reports=[]
                # Other subtests reuse the immutable journals with unique suffixes.
                self.seven=lambda: [self.add(f'2026-10-{d:02}',suffix=str(content)) for d in range(7,14)]
    def test_C28_known_report_only_history_remains_ineligible(self):
        rp,_,_=self.add('2026-10-06',failed=True);self.change(rp,lambda d:d.update(mode='REPORT_ONLY',enforcement=False));self.seven()
        r=self.collect();self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertEqual(r['anchored_failures'],[])
    def test_C29_clean_acceptance_delegates_to_installed_guard(self):
        self.seven()
        with patch.object(nc,'load_enforcement_activation',wraps=nc.load_enforcement_activation) as load, \
                patch.object(nc,'checkpoint_window',wraps=nc.checkpoint_window) as window, \
                patch.object(nc,'_clean',wraps=nc._clean) as clean:
            r=self.collect()
        self.assertEqual(r['consecutive_clean_closed_windows'],7);self.assertEqual(load.call_count,1)
        self.assertEqual(window.call_count,7);self.assertEqual(clean.call_count,7)
    def test_C30_negative_anchor_does_not_call_a_second_proof_gate(self):
        rp,_,_=self.add('2026-10-13',failed=True)
        with patch('publication_gate.evaluate_publication',side_effect=AssertionError('no additional verifier')):
            day,_=cc.held_checkpoint_window(self.root,json.loads(rp.read_text()),self.now)
        self.assertEqual(day,'2026-10-13')
    def test_C31_weekly_unknown_or_old_only_candidate_cannot_be_substituted(self):
        rp,_,_=self.add('2026-10-06',failed=True)
        r=cc._weekly_current_candidate(self.root,[rp],self.now)
        self.assertEqual(r['status'],'HOLD_NO_CURRENT_AUTHENTIC_WEEKLY_COVERAGE')
        self.assertFalse((self.root/'reports/verification-coverage/weekly').exists())

class ReportingConsumerBoundaries(unittest.TestCase):
    def test_C32_guard_source_stays_exact_approved_hash(self):
        self.assertEqual(hashlib.sha256(Path(nc.__file__).read_bytes()).hexdigest(),cc.INSTALLED_GUARD_SHA256)
    def test_C33_production_cli_refuses_other_tree(self):
        with self.assertRaisesRegex(ValueError,'exact canonical Cowork root'):
            cc.require_actual_installed_guard(Path('/Users/justinhart/Desktop/science '))
    def test_C34_production_cli_refuses_wrong_import(self):
        with patch.object(nc,'__file__','/private/tmp/fake/nightly_coverage.py'):
            with self.assertRaisesRegex(ValueError,'actual installed guard'):
                cc.require_actual_installed_guard(cc.CANONICAL_ROOT)
    def test_C35_production_cli_refuses_changed_guard_sha(self):
        expected=cc.CANONICAL_ROOT/'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
        with patch.object(nc,'__file__',str(expected)),patch.object(nc,'binding',return_value={'path':str(expected),'sha256':'0'*64}):
            with self.assertRaisesRegex(ValueError,'approved d25e closure'):
                cc.require_actual_installed_guard(cc.CANONICAL_ROOT)
    def test_C36_module_has_no_mutation_of_guard_or_science_execution_import(self):
        tree=ast.parse(Path(cc.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                targets=node.targets if isinstance(node,ast.Assign) else [node.target]
                for t in targets:
                    if isinstance(t,ast.Attribute):self.assertFalse(isinstance(t.value,ast.Name) and t.value.id=='nc')
            if isinstance(node,ast.Import):
                self.assertFalse(any(x.name.split('.')[0] in {'subprocess','requests','urllib','socket'} for x in node.names))
        self.assertNotIn('issue_lean_zero_sorry_certificate',Path(cc.__file__).read_text())

if __name__=='__main__':unittest.main()
